import json
import random
import asyncio
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InputMediaVideo
)
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
        "welcome_approved": "🔥 Welcome to MAXWIN AI RTP\n🤖 AI scans highest RTP in slots\n📊 Press platform game menu below to start",
        "choose_merchant": "Please select a merchant:",
        "register_prompt": "⚠️ Please register via official link:\nThen enter your account ID:",
        "share_contact": "📱 Please share your phone number",
        "wait_admin": "Please wait for Admin to approve your access.",
        "approved": "✅ Your account has been approved.\nSelect merchant:",
        "select_platform": "{merchant} - Please select a platform:",
        "rtp_scan_header": "🔍 SCAN RESULT — {platform} \n━━━━━━━━━━━━━━━━━━\n👤 {merchant} | 🆔 {account_id}\n━━━━━━━━━━━━━━━━━━",
        "scan_stats": "━━━━━━━━━━━━━━━━━━\n📊 Scanned: {total} | \n🔥 Hot: {hot}\n⚡ Best: {best}%\n🕒 {time}\n⚠️ Valid 15 min only"
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome_approved": "🔥 欢迎来到 MAXWIN AI RTP\n🤖 AI 扫描最高 RTP 游戏\n📊 点击下方游戏平台菜单开始",
        "choose_merchant": "请选择商家：",
        "register_prompt": "⚠️ 请通过以下链接注册：\n注册后请输入账号ID：",
        "share_contact": "📱 请授权手机号",
        "wait_admin": "请等待 Admin 审核权限。",
        "approved": "✅ 审核通过 ✅\n请选择商家：",
        "select_platform": "{merchant} - 请选择游戏平台：",
        "rtp_scan_header": "🔍 SCAN RESULT — {platform} \n━━━━━━━━━━━━━━━━━━\n👤 {merchant} | 🆔 {account_id}\n━━━━━━━━━━━━━━━━━━",
        "scan_stats": "━━━━━━━━━━━━━━━━━━\n📊 扫描总数: {total} | \n🔥 热度: {hot}\n⚡ 最高: {best}%\n🕒 {time}\n⚠️ 有效期 15 分钟"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome_approved": "🔥 Selamat datang ke MAXWIN AI RTP\n🤖 AI yang scan RTP tertinggi dalam slot2\n📊 Tekan platform game menu di bawah untuk mula",
        "choose_merchant": "Sila pilih merchant:",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi:\nKemudian masukkan ID akaun:",
        "share_contact": "📱 Sila kongsi nombor telefon anda",
        "wait_admin": "Sila tunggu Admin meluluskan akses anda.",
        "approved": "✅ Akaun anda telah diluluskan.\nPilih merchant:",
        "select_platform": "{merchant} - Sila pilih platform:",
        "rtp_scan_header": "🔍 SCAN RESULT — {platform} \n━━━━━━━━━━━━━━━━━━\n👤 {merchant} | 🆔 {account_id}\n━━━━━━━━━━━━━━━━━━",
        "scan_stats": "━━━━━━━━━━━━━━━━━━\n📊 Total scan: {total} | \n🔥 Hot: {hot}\n⚡ Best: {best}%\n🕒 {time}\n⚠️ Sah selama 15 minit sahaja"
    }
}

# ====== 保存用户 ======
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        # 已批准用户，直接显示视频+欢迎
        lang = user_language.get(user_id, "en")
        # 视频 URL，可替换为实际视频文件或链接
        video_url = "https://www.example.com/demo.mp4"
        await context.bot.send_video(chat_id=user_id, video=video_url)
        await update.message.reply_text(TEXTS[lang]["welcome_approved"])
        await show_merchants_message(update, context, lang)
    else:
        # 未批准用户，语言选择
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
    user_id = query.from_user.id
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        # 已批准用户，直接显示视频+欢迎
        video_url = "https://www.example.com/demo.mp4"
        await context.bot.send_video(chat_id=user_id, video=video_url)
        await query.edit_message_text(TEXTS[lang]["welcome_approved"])
        await show_merchants(query, lang)
    else:
        text = TEXTS[lang]["choose_lang"]
        await show_merchants(query, lang, initial=True)

# ====== 显示商家 ======
async def show_merchants(query_or_update, lang, initial=False):
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
    if initial:
        # 返回语言选择按钮
        keyboard.append([InlineKeyboardButton("🔙 返回语言选择", callback_data="back_lang")])
    await query_or_update.edit_message_text(TEXTS[lang]["choose_merchant"], reply_markup=InlineKeyboardMarkup(keyboard))

async def show_merchants_message(update, context, lang):
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
    await update.message.reply_text(TEXTS[lang]["choose_merchant"], reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 商家选择 ======
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    merchant = query.data.split("_")[1]
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    context.user_data["merchant"] = merchant
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        # 已批准用户直接显示平台选择
        text = TEXTS[lang]["select_platform"].format(merchant=merchant)
        await show_platforms(query, merchant, lang, text)
    else:
        # 未批准用户提示注册
        text = TEXTS[lang]["register_prompt"]
        register_button = InlineKeyboardButton("点击注册", url=MERCHANT_LINKS[merchant])
        keyboard = [[register_button], [InlineKeyboardButton("🔙 返回商家选择", callback_data="back_merchant")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

# ====== 接收注册ID ======
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    merchant = context.user_data.get("merchant")
    lang = user_language.get(user_id, "en")
    if not merchant or (str(user_id) in users_data and users_data[str(user_id)].get("approved")):
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
    pending_users[user.id]["phone"] = update.message.contact.phone_number
    pending_users[user.id]["approved"] = False
    users_data[str(user.id)] = pending_users[user.id]
    save_users()
    if ADMIN_ID != 0:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 NEW REGISTRATION REQUEST\n\n🆔 Application: MW-{datetime.now().strftime('%Y%m%d-%H%M')}\n"
                 f"👤 Username: @{user.username}\n📞 Phone: {pending_users[user.id]['phone']}\n"
                 f"🏢 Merchant: {pending_users[user.id]['merchant']}\n🎮 Game ID: {pending_users[user.id]['account_id']}\n"
                 f"🌐 Language: {lang}\n🕒 {datetime.now().strftime('%d %b %Y %H:%M')}\n\nApprove: /approve {user.id}"
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
        video_url = "https://www.example.com/demo.mp4"
        await context.bot.send_video(chat_id=user_id, video=video_url)
        await context.bot.send_message(chat_id=user_id, text=TEXTS[lang]["welcome_approved"])
        await show_merchants_message(update, context, lang)
        await update.message.reply_text(f"用户 {user_id} 已批准 ✅")

# ====== 平台显示 ======
async def show_platforms(query, merchant, lang, text):
    keyboard = [[InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")] for p in PLATFORMS]
    keyboard.append([InlineKeyboardButton("🔙 返回商家选择", callback_data="back_merchant")])
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== RTP 扫描显示 ======
async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    _, merchant, platform = query.data.split("_")
    account_id = users_data.get(str(user_id), {}).get("account_id", "N/A")
    
    header = TEXTS[lang]["rtp_scan_header"].format(platform=platform, merchant=merchant, account_id=account_id)
    msg = await query.edit_message_text(f"{header}\n\nLoading RTP...\n[□□□□□□□□□□] 0%")
    
    # 模拟加载动画
    bar_total = 10
    for i in range(1, 11):
        await asyncio.sleep(1)  # 每秒更新
        progress_bar = "■" * i + "□" * (bar_total - i)
        percent = i * 10
        await msg.edit_text(f"{header}\n\nLoading RTP...\n[{progress_bar}] {percent}%")
    
    # 生成每个游戏 25 个随机 RTP
    games = GAMES[platform]
    game_rtp_results = {}
    for game in games:
        rtp_values = [random.randint(30, 98) for _ in range(25)]
        game_rtp_results[game] = rtp_values
    
    # 只显示示例 scan 结果（标记和统计）
    scan_games = random.sample(list(game_rtp_results.keys()), 8)
    scan_text = header + "\n"
    hot_count = 0
    best = 0
    for g in scan_games:
        r = random.choice(game_rtp_results[g])
        best = max(best, r)
        if r < 70:
            prefix = "🛑"
        elif r < 80:
            prefix = "✅"
        elif r < 90:
            prefix = "🔥"
            hot_count += 1
        else:
            prefix = "🏆"
        scan_text += f"{prefix} {g} — {r}%\n"
    
    scan_text += TEXTS[lang]["scan_stats"].format(
        total=len(scan_games),
        hot=hot_count,
        best=best,
        time=datetime.now().strftime("%d %b %Y %H:%M")
    )
    # 添加返回平台按钮
    keyboard = [[InlineKeyboardButton("🔙 返回平台选择", callback_data=f"merchant_{merchant}")]]
    await msg.edit_text(scan_text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 返回按钮处理 ======
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
        await query.edit_message_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "back_merchant":
        await show_merchants(query, lang)

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(platform_handler, pattern="platform_"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="back_"))
    app.add_handler(MessageHandler(filters.CONTACT, receive_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))
    app.add_handler(CommandHandler("approve", approve))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
