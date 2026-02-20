from game_data import PLATFORM_GAMES
import json
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import os

# ====== 配置 ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

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

# ====== 商家的游戏平台及游戏 ======
PLATFORM_GAMES = {
    "CM8": {
        "VPOWER": ["DolphinReef","Mahjong Ways 2","Triple Supreme Olympic","RAVE FEVER PARTY","Cash Machine"],
        "BAOZHUZHAOFU": ["Starlight Princess","PIRATE BINGO","GOLDEN CENTURY","BAOZHUZHAOCAI","Fortune Bowls"],
        "HACKSAW": ["Stick'Em","OmNom","Miami Multiplier","Cubes","Cash Compass"]
        # 这里根据你发的列表继续添加每个平台下的游戏
    },
    "A9PLAY": {
        "PP": ["SuperAce Plus","Wisdom Athena 1000","Sweet Bonanza 1000"],
        "PG": ["Fortune Panda","Fortune Tiger","Starlight Princess 1000"]
    },
    "ALD99": {
        "PG": ["Egypt Queen","MonkeyKing","MonkeyKing3","Aztec"]
    },
    "U9PLAY": {
        "JILI": ["Dragon Palace","Golden Lotus","God Of Wealth2"]
    }
}

# ====== 临时存储 ======
pending_users = {}  # TG_ID: {merchant, account_id, approved}
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ====== 语言文本 ======
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🎰 Welcome to MAXWIN AI RTP",
        "choose_merchant": "Please select a merchant:",
        "register_prompt": "⚠️ Please register via official link:\nThen enter your account ID:",
        "share_contact": "📱 Please share your phone number",
        "wait_admin": "Please wait for Admin to approve your access.",
        "approved": "✅ Your account has been approved.",
        "select_platform": "{merchant} - Please select a platform:",
        "scan_loading": [
            "Loading AI Engine...",
            "Calibrating volatility index...",
            "Syncing RTP Matrix..."
        ],
        "scan_result_header": "🔍 SCAN RESULT — {platform}\n━━━━━━━━━━━━━━━━━━\n👤 {merchant} | 🆔 {account_id}\n━━━━━━━━━━━━━━━━━━",
        "scan_result_footer": "━━━━━━━━━━━━━━━━━━\n📊 Scanned: {scanned} | 🔥 Hot: {hot} | ⚡ Best: {best}\n🕒 {time}\n⚠️ Valid 15 min only",
        "not_registered": "🔥 Welcome to MAXWIN AI RTP\n🤖 AI scans highest RTP in slots\n📊 Our system detects you haven't registered on this platform. Click 'Register' in the directory."
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🎰 欢迎来到 MAXWIN AI RTP",
        "choose_merchant": "请选择商家：",
        "register_prompt": "⚠️ 请通过以下链接注册：\n注册后请输入账号ID：",
        "share_contact": "📱 请授权手机号",
        "wait_admin": "请等待 Admin 审核权限。",
        "approved": "✅ 审核通过",
        "select_platform": "{merchant} - 请选择游戏平台：",
        "scan_loading": [
            "加载 AI 引擎...",
            "校准波动指数...",
            "同步 RTP 矩阵..."
        ],
        "scan_result_header": "🔍 SCAN 结果 — {platform}\n━━━━━━━━━━━━━━━━━━\n👤 {merchant} | 🆔 {account_id}\n━━━━━━━━━━━━━━━━━━",
        "scan_result_footer": "━━━━━━━━━━━━━━━━━━\n📊 已扫描: {scanned} | 🔥 高: {hot} | ⚡ 最佳: {best}\n🕒 {time}\n⚠️ 有效 15 分钟",
        "not_registered": "🔥 欢迎来到 MAXWIN AI RTP\n🤖 AI 扫描老虎机最高 RTP\n📊 系统检测您尚未在此平台注册，请点击目录中的“注册”。"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🎰 Selamat Datang ke MAXWIN AI RTP",
        "choose_merchant": "Sila pilih merchant:",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi:\nKemudian masukkan ID akaun:",
        "share_contact": "📱 Sila kongsi nombor telefon anda",
        "wait_admin": "Sila tunggu Admin meluluskan akses anda.",
        "approved": "✅ Akaun anda telah diluluskan.",
        "select_platform": "{merchant} - Sila pilih platform:",
        "scan_loading": [
            "Loading AI Engine...",
            "Calibrating volatility index...",
            "Syncing RTP Matrix..."
        ],
        "scan_result_header": "🔍 SCAN RESULT — {platform}\n━━━━━━━━━━━━━━━━━━\n👤 {merchant} | 🆔 {account_id}\n━━━━━━━━━━━━━━━━━━",
        "scan_result_footer": "━━━━━━━━━━━━━━━━━━\n📊 Scanned: {scanned} | 🔥 Hot: {hot} | ⚡ Best: {best}\n🕒 {time}\n⚠️ Valid 15 minit sahaja",
        "not_registered": "🔥 Selamat datang ke MAXWIN AI RTP\n🤖 AI yang scan RTP tertinggi dalam slot\n📊 Sistem mengesan bahawa bossku masih belum mendaftar di platform ini. Boss boleh klik \"Daftar\" dalam direktori."
    }
}

# ====== 保存用户 ======
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_language.get(user_id, None)
    # 如果已approve直接欢迎页面
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        lang = lang or 'en'
        user_language[user_id] = lang
        await show_welcome_page(update.message, lang, user_id)
        return

    keyboard = [
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=reply_markup)

# ====== 显示欢迎页面（视频+商家+注册按钮） ======
async def show_welcome_page(message, lang, user_id):
    # 视频
    await message.reply_video(video=VIDEO_FILE_ID)
    text = TEXTS[lang]["welcome"]
    # 商家按钮
    keyboard = []
    for m in MERCHANT_LINKS.keys():
        keyboard.append([InlineKeyboardButton(m, callback_data=f"merchant_{m}")])
    # 注册按钮
    keyboard.append([InlineKeyboardButton("Daftar / Register", callback_data="register_button")])
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 语言选择 ======
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    # 视频 + 欢迎文本 + 商家按钮
    await show_welcome_page(query, lang, query.from_user.id)

# ====== 点击商家 ======
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    merchant = query.data.split("_")[1]

    # 如果用户未注册该商家
    user_merchants = [users_data[str(user_id)]["merchant"]] if str(user_id) in users_data else []
    if merchant not in user_merchants:
        await query.edit_message_text(TEXTS[lang]["not_registered"])
        return

    # 已注册 → 显示游戏平台
    platforms = PLATFORM_GAMES.get(merchant, {})
    keyboard = [[InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")] for p in platforms.keys()]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"back_welcome")])
    await query.edit_message_text(TEXTS[lang]["select_platform"].format(merchant=merchant), reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 点击平台 Scan ======
async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    _, merchant, platform = query.data.split("_")
    games = PLATFORM_GAMES.get(merchant, {}).get(platform, [])

    # 显示 loading
    for i, step in enumerate(TEXTS[lang]["scan_loading"], start=1):
        progress = int(i/len(TEXTS[lang]["scan_loading"])*100)
        bar = "■"*progress + "□"*(100-progress)
        await query.edit_message_text(f"{step}\n[{bar}] {progress}%")
        await asyncio.sleep(1)

    # 随机生成25个RTP
    rtp_list = {game: [round(random.uniform(30, 98),2) for _ in range(25)] for game in games}
    # 构造显示
    message = TEXTS[lang]["scan_result_header"].format(platform=platform, merchant=merchant, account_id=users_data[str(user_id)]["account_id"])
    scanned = len(games)
    hot = sum(1 for vals in rtp_list.values() for v in vals if 80 <= v < 90)
    best = max(max(vals) for vals in rtp_list.values()) if rtp_list else 0
    for game, vals in rtp_list.items():
        rtp_display = random.choice(vals)
        if rtp_display < 70: emoji = "🛑"
        elif rtp_display < 80: emoji = "✅"
        elif rtp_display < 90: emoji = "🔥"
        else: emoji = "🏆"
        message += f"{emoji} {game} — {rtp_display}%\n"
    message += TEXTS[lang]["scan_result_footer"].format(scanned=scanned, hot=hot, best=best, time=datetime.now().strftime("%d %b %Y %H:%M"))
    # 返回平台选择按钮
    keyboard = [[InlineKeyboardButton("🔙 Back to Platforms", callback_data=f"merchant_{merchant}")]]
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 注册按钮 ======
async def register_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    # 显示可注册商家
    keyboard = [[InlineKeyboardButton(m, callback_data=f"register_{m}")] for m in MERCHANT_LINKS.keys()]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_welcome")])
    await query.edit_message_text("Select merchant to register:", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 注册商家提交ID ======
async def register_merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    merchant = query.data.split("_")[1]
    user_id = query.from_user.id
    context.user_data["register_merchant"] = merchant
    contact_button = KeyboardButton("Enter your Account ID")
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await query.edit_message_text(f"Please enter your Account ID for {merchant}:", reply_markup=reply_markup)

# ====== 接收注册ID ======
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    merchant = context.user_data.get("register_merchant")
    lang = user_language.get(user_id, "en")
    if not merchant:
        return
    account_id = update.message.text
    users_data[str(user_id)] = {"merchant": merchant, "account_id": account_id, "approved": True}
    save_users()
    # 返回欢迎页面
    await show_welcome_page(update.message, lang, user_id)

# ====== 返回处理 ======
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    if query.data == "back_welcome":
        await show_welcome_page(query, lang, user_id)

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

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(platform_handler, pattern="platform_"))
    app.add_handler(CallbackQueryHandler(register_button_handler, pattern="register_button"))
    app.add_handler(CallbackQueryHandler(register_merchant_handler, pattern="register_"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="back_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))
    app.add_handler(CommandHandler("approve", approve))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
