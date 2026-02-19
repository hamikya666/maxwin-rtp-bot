import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import os

# ====== 配置 ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"

# ====== 初始化用户文件 ======
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

# ====== 商家链接 ======
MERCHANT_LINKS = {
    "CM8": "https://bit.ly/MaxWinCM8",
    "A9PLAY": "http://a9play5.com/R=F7464F",
    "ALD99": "https://bit.ly/ALDMaxWin",
    "U9PLAY": "https://u9play99.com/R=C8BAAC"
}

# ====== 平台 ======
PLATFORMS = ["PP", "BNG", "JILI", "PG"]

# ====== 游戏示例数据 ======
GAMES = {p: [f"{p}_Game_{i}" for i in range(1,36)] for p in PLATFORMS}

# ====== 临时存储 ======
pending_users = {}
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ====== 语言文本 ======
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🎰 Welcome to MaxWin Official RTP Bot",
        "choose_merchant": "Please select a merchant:",
        "register_prompt": "⚠️ Please register via official link:\n{link}\nThen enter your account ID:",
        "share_contact": "📱 Please share your phone number",
        "wait_admin": "Please wait for Admin to approve your access.",
        "approved": "✅ Your account has been approved.\nSelect merchant:",
        "select_platform": "{merchant} - Please select a platform:",
        "rtp_top": "{merchant} - {platform} RTP TOP 15\n\n"
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🎰 欢迎来到 MaxWin 官方 RTP 查询机器人",
        "choose_merchant": "请选择商家：",
        "register_prompt": "⚠️ 请通过以下链接注册：\n{link}\n注册后请输入账号ID：",
        "share_contact": "📱 请授权手机号",
        "wait_admin": "请等待 Admin 审核权限。",
        "approved": "✅ 审核通过 ✅\n请选择商家：",
        "select_platform": "{merchant} - 请选择游戏平台：",
        "rtp_top": "{merchant} - {platform} RTP TOP 15\n\n"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🎰 Selamat Datang ke MaxWin RTP Bot Rasmi",
        "choose_merchant": "Sila pilih merchant:",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi:\n{link}\nKemudian masukkan ID akaun:",
        "share_contact": "📱 Sila kongsi nombor telefon anda",
        "wait_admin": "Sila tunggu Admin meluluskan akses anda.",
        "approved": "✅ Akaun anda telah diluluskan.\nPilih merchant:",
        "select_platform": "{merchant} - Sila pilih platform:",
        "rtp_top": "{merchant} - {platform} RTP TOP 15\n\n"
    }
}

# ====== 保存用户 ======
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=reply_markup)

# ====== 语言选择 ======
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["choose_merchant"]
    await show_merchants(query, text)

# ====== 显示商家 ======
async def show_merchants(query, text):
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 商家选择 ======
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    merchant = query.data.split("_")[1]
    context.user_data["merchant"] = merchant
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        text = TEXTS[lang]["select_platform"].format(merchant=merchant)
        await show_platforms(query, merchant, lang, text)
    else:
        link = MERCHANT_LINKS[merchant]
        text = TEXTS[lang]["register_prompt"].format(link=link)
        await query.edit_message_text(text=text)

# ====== 接收注册ID ======
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    merchant = context.user_data.get("merchant")
    lang = user_language.get(user_id, "en")
    if not merchant:
        return
    account_id = update.message.text
    pending_users[user_id] = {"merchant": merchant, "account_id": account_id}
    contact_button = KeyboardButton(TEXTS[lang]["share_contact"], request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(TEXTS[lang]["share_contact"], reply_markup=reply_markup)

# ====== 接收手机号 ======
async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    lang = user_language.get(user.id, "en")
    contact = update.message.contact
    pending_users[user.id]["phone"] = contact.phone_number
    pending_users[user.id]["approved"] = False
    users_data[str(user.id)] = pending_users[user.id]
    save_users()
    if ADMIN_ID != 0:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"新用户申请\nTG: {user.full_name}\n商家: {pending_users[user.id]['merchant']}\nID: {pending_users[user.id]['account_id']}\n电话: {contact.phone_number}\n\n批准: /approve {user.id}"
        )
    await update.message.reply_text(TEXTS[lang]["wait_admin"])

# ====== Admin批准 ======
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) != 1:
        return
    user_id = int(context.args[0])
    if str(user_id) in users_data:
        users_data[str(user_id)]["approved"] = True
        save_users()
        lang = user_language.get(user_id, "en")
        await context.bot.send_message(chat_id=user_id, text=TEXTS[lang]["approved"])
        await update.message.reply_text(f"用户 {user_id} 已批准 ✅")

# ====== 平台显示 ======
async def show_platforms(query, merchant, lang, text):
    keyboard = [[InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")] for p in PLATFORMS]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 平台RTP显示 ======
async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    _, merchant, platform = query.data.split("_")
    games = GAMES[platform]
    rtp_list = [(game, round(random.uniform(88, 98),2)) for game in games]
    rtp_list.sort(key=lambda x: x[1], reverse=True)
    top15 = rtp_list[:15]
    message = TEXTS[lang]["rtp_top"].format(merchant=merchant, platform=platform)
    for game, rtp in top15:
        message += f"{game} - {rtp}%\n"
    await query.edit_message_text(message)

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(platform_handler, pattern="platform_"))
    app.add_handler(MessageHandler(filters.CONTACT, receive_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))
    app.add_handler(CommandHandler("approve", approve))
    print("Bot Running...")
    app.run_polling()  # ⚠️ 不要 asyncio.run()

if __name__ == "__main__":
    main()
