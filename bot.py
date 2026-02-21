import json
import random
import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, InputMediaVideo
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import os

# ====== 配置 ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"

VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

# ====== 商家链接 ======
MERCHANT_LINKS = {
    "CM8": "https://bit.ly/MaxWinCM8",
    "A9PLAY": "http://a9play5.com/R=F7464F",
    "ALD99": "https://bit.ly/ALDMaxWin",
    "U9PLAY": "https://u9play99.com/R=C8BAAC"
}

# ====== 数据库初始化 ======
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

pending_users = {}  # 临时保存等待 admin 审核的用户
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ====== 游戏数据 ======
from data import cm8, a9play, ald99, u9play
GAMES = {
    "CM8": cm8.GAMES,
    "A9PLAY": a9play.GAMES,
    "ALD99": ald99.GAMES,
    "U9PLAY": u9play.GAMES
}

PLATFORMS = ["PP", "BNG", "JILI", "PG", "VPOWER"]

# ====== 文本 ======
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please select language",
        "welcome": "🎥 Welcome to MAXWIN AI RTP\n\nSelect merchant below:",
        "register_prompt": "⚠️ Please register via official link:\nThen enter your account ID:",
        "share_contact": "📱 Please share your phone number",
        "wait_admin": "⏳ Waiting for Admin approval...",
        "approved": "✅ Your account has been approved!",
        "rejected": "❌ Your registration was rejected. Please register again.",
        "unregistered_scan": "🔥 MAXWIN AI RTP\n🤖 AI scanning highest RTP for slots\n📊 You haven't registered for this merchant yet. Click 'Register' below."
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🎥 欢迎来到 MAXWIN AI RTP\n\n请选择商家：",
        "register_prompt": "⚠️ 请通过注册链接注册：\n注册后输入账户ID：",
        "share_contact": "📱 请分享您的手机号",
        "wait_admin": "⏳ 请等待管理员审核...",
        "approved": "✅ 审核通过！",
        "rejected": "❌ 注册被拒绝，请重新注册。",
        "unregistered_scan": "🔥 MAXWIN AI RTP\n🤖 AI 正在扫描最高 RTP\n📊 您尚未注册该商家，请点击下方 '注册'。"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🎥 Selamat Datang ke MAXWIN AI RTP\n\nPilih merchant di bawah:",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi:\nKemudian masukkan ID akaun:",
        "share_contact": "📱 Sila kongsi nombor telefon anda",
        "wait_admin": "⏳ Sila tunggu kelulusan Admin...",
        "approved": "✅ Akaun anda telah diluluskan!",
        "rejected": "❌ Pendaftaran ditolak. Sila daftar semula.",
        "unregistered_scan": "🔥 Selamat datang ke MAXWIN AI RTP\n🤖 AI yang scan RTP tertinggi dalam slot\n📊 Sistem mengesan bahawa anda belum mendaftar di platform ini. Klik 'Daftar' di bawah."
    }
}

# ====== 保存用户 ======
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = users_data.get(str(user_id))
    lang = user_language.get(user_id, "en")
    # 如果用户已注册并且approve
    if user and user.get("approved"):
        await show_main_menu(update, context, lang)
        return
    # 否则选择语言
    keyboard = [
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(TEXTS["en"]["choose_lang"], reply_markup=reply_markup)

# ====== 语言选择 ======
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    await show_merchants(query, lang)

# ====== 显示商家选择 ======
async def show_merchants(query, lang):
    text = TEXTS[lang]["welcome"]
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_lang")])
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 点击商家 ======
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    merchant = query.data.split("_")[1]
    context.user_data["merchant"] = merchant
    user = users_data.get(str(user_id))

    # 检查是否已注册该商家
    if user and merchant in user.get("merchants", []):
        await show_platforms(query, merchant, lang)
    else:
        # 未注册提示 + 注册按钮
        text = TEXTS[lang]["unregistered_scan"]
        keyboard = [
            [InlineKeyboardButton("Scan", callback_data=f"scan_{merchant}")],
            [InlineKeyboardButton("Register", callback_data="register")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_merchants")]
        ]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 注册流程 ======
async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    keyboard = [[InlineKeyboardButton(m, callback_data=f"reg_{m}")] for m in MERCHANT_LINKS.keys()]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_merchants")])
    await query.edit_message_text("Select merchant to register:", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 提供ID ======
async def provide_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    account_id = update.message.text
    merchant = context.user_data.get("merchant")
    lang = user_language.get(user_id, "en")
    pending_users[user_id] = {"merchant": merchant, "account_id": account_id, "approved": False, "timestamp": str(datetime.datetime.now())}
    users_data.setdefault(str(user_id), {"merchants": []})
    save_users()
    # 通知 admin
    if ADMIN_ID != 0:
        app = context.bot
        app.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 NEW REGISTRATION REQUEST\n\n🆔 Application: MW-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}\n👤 Username: @{update.message.from_user.username}\n🏢 Merchant: {merchant}\n🎮 Game ID: {account_id}\n🌐 Language: {lang}\n🕒 {datetime.datetime.now().strftime('%d %b %Y %H:%M')}"
        )
    await update.message.reply_text(TEXTS[lang]["wait_admin"])

# ====== Admin Approve / Reject ======
async def approve_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    args = context.args
    if len(args) != 2:
        return
    action, user_id = args
    user_id = int(user_id)
    if str(user_id) in users_data:
        if action == "approve":
            users_data[str(user_id)]["approved"] = True
            save_users()
            lang = user_language.get(user_id, "en")
            await context.bot.send_message(chat_id=user_id, text=TEXTS[lang]["approved"])
            await update.message.reply_text(f"User {user_id} approved ✅")
        elif action == "reject":
            lang = user_language.get(user_id, "en")
            await context.bot.send_message(chat_id=user_id, text=TEXTS[lang]["rejected"])
            await update.message.reply_text(f"User {user_id} rejected ❌")

# ====== 平台展示 + Scan ======
async def show_platforms(query, merchant, lang):
    keyboard = [[InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")] for p in PLATFORMS]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_merchants")])
    await query.edit_message_text(text=f"Select platform for {merchant}:", reply_markup=InlineKeyboardMarkup(keyboard))

async def platform_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, merchant, platform = query.data.split("_")
    games = GAMES[merchant][platform]
    # Loading 模拟
    loading_texts = [
        "Loading AI Engine...",
        "Calibrating volatility index...",
        "Syncing RTP Matrix..."
    ]
    message = await query.edit_message_text("Loading...\n[■□□□□□□□□] 20%")
    for i, text in enumerate(loading_texts, 1):
        await message.edit_text(f"{text}\n[{'■' * i}{'□' * (10-i)}] {i*33}%")
    # 显示 RTP
    rtp_list = [(g, round(random.uniform(30, 98), 2)) for g in games]
    rtp_text = f"🔍 SCAN RESULT — {platform}\n━━━━━━━━━━\n"
    for g, r in rtp_list:
        if r < 70:
            icon = "🛑"
        elif r < 80:
            icon = "✅"
        elif r < 90:
            icon = "🔥"
        else:
            icon = "🏆"
        rtp_text += f"{icon} {g} — {r}%\n"
    await query.edit_message_text(rtp_text)

# ====== 主菜单（视频 + 欢迎 + 商家 + 注册） ======
async def show_main_menu(update, context, lang):
    chat_id = update.message.chat_id
    # 发送视频
    await context.bot.send_video(chat_id=chat_id, video=VIDEO_FILE_ID)
    # 欢迎文本
    await context.bot.send_message(chat_id=chat_id, text=TEXTS[lang]["welcome"])
    # 商家按钮
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
    # 注册按钮
    keyboard.append([InlineKeyboardButton("Register", callback_data="register")])
    await context.bot.send_message(chat_id=chat_id, text="Select merchant or register:", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 返回键 ======
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    if query.data == "back_lang":
        keyboard = [
            [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
        ]
        await query.edit_message_text(TEXTS["en"]["choose_lang"], reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "back_merchants":
        await show_merchants(query, lang)

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(register_handler, pattern="register"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="back_"))
    app.add_handler(CallbackQueryHandler(platform_scan, pattern="platform_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, provide_id))
    app.add_handler(CommandHandler("approve", approve_reject))
    app.add_handler(CommandHandler("reject", approve_reject))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
