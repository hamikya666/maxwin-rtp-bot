import json
import random
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8194393436:AAF-fVYwsGflkXyHU7nOg7vmOJV40fRiDIM"
ADMIN_ID = 5473935017  # 改成你的ID
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ
"

USERS_FILE = "users.json"

MERCHANT_LINKS = {
    "CM8": "https://bit.ly/MaxWinCM8",
    "A9PLAY": "http://a9play5.com/R=F7464F",
    "ALD99": "https://bit.ly/ALDMaxWin",
    "U9PLAY": "https://u9play99.com/R=C8BAAC"
}

PROVIDERS = ["PP", "JILI", "BNG"]

# =====================
# USER STORAGE
# =====================

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

USERS = load_users()

def generate_app_id():
    date = datetime.now().strftime("%Y%m%d")
    num = random.randint(1000, 9999)
    return f"MW-{date}-{num}"

# =====================
# START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)

    if user in USERS and USERS[user]["status"] == "WAIT":
        await update.message.reply_text(
            "⏳ Request sedang diproses.\nSila tunggu admin approve."
        )
        return

    if user in USERS and USERS[user]["status"] == "APPROVED":
        await send_main_menu(update, context)
        return

    USERS[user] = {
        "status": "NEW",
        "language": None,
        "phone": None,
        "game_id": None,
        "wallet": 0
    }
    save_users(USERS)

    keyboard = [
        [InlineKeyboardButton("🇲🇾 Malay", callback_data="lang_ms")],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_cn")]
    ]

    await update.message.reply_text(
        "🎰 Selamat Datang ke MAXWIN AI RTP BOT",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# LANGUAGE
# =====================

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = str(query.from_user.id)
    USERS[user]["language"] = query.data
    USERS[user]["status"] = "REGISTER"
    save_users(USERS)

    keyboard = [
        [InlineKeyboardButton(p, callback_data=f"reg_{p}")]
        for p in MERCHANT_LINKS.keys()
    ]

    await query.edit_message_text(
        "⚠ 请选择平台进行注册",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# REGISTER FLOW
# =====================

async def register_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    platform = query.data.split("_")[1]
    context.user_data["platform"] = platform
    link = MERCHANT_LINKS[platform]

    keyboard = [
        [InlineKeyboardButton("🌐 点击注册", url=link)],
        [InlineKeyboardButton("✅ 我已注册", callback_data="after_reg")],
        [InlineKeyboardButton("⬅ 返回", callback_data="back_lang")]
    ]

    await query.edit_message_text(
        f"🏢 平台：{platform}\n\n"
        "请使用上方官方链接注册账号。\n"
        "注册完成后点击【我已注册】",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def after_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎮 请输入您的游戏ID：",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅ 返回", callback_data="back_lang")]]
        )
    )

async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)

    if user not in USERS or USERS[user]["status"] != "REGISTER":
        return

    USERS[user]["game_id"] = update.message.text
    save_users(USERS)

    keyboard = [[KeyboardButton("📱 Share Phone", request_contact=True)]]

    await update.message.reply_text(
        "📱 请分享电话号码以完成注册",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)

    USERS[user]["phone"] = update.message.contact.phone_number
    USERS[user]["status"] = "WAIT"
    USERS[user]["application"] = generate_app_id()
    save_users(USERS)

    await update.message.reply_text(
        "⏳ 正在等待管理员审批...",
        reply_markup=ReplyKeyboardRemove()
    )

    text = (
        f"📥 NEW REGISTRATION REQUEST\n\n"
        f"🆔 Application: {USERS[user]['application']}\n"
        f"👤 Username: @{update.effective_user.username}\n"
        f"📞 Phone: {USERS[user]['phone']}\n"
        f"🏢 Merchant: {context.user_data.get('platform')}\n"
        f"🎮 Game ID: {USERS[user]['game_id']}\n"
        f"🌐 Language: {USERS[user]['language']}\n"
        f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user}")
        ]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# ADMIN
# =====================

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_")

    if action == "approve":
        USERS[user_id]["status"] = "APPROVED"
        save_users(USERS)

        await context.bot.send_message(user_id, "✅ Akaun Boss telah diluluskan🔥")
        await context.bot.send_video(
            user_id,
            VIDEO_FILE_ID,
            caption="🔥欢迎使用 MAXWIN AI RTP\n请选择下方菜单开始",
            reply_markup=main_menu_keyboard()
        )

    else:
        USERS[user_id]["status"] = "NEW"
        save_users(USERS)
        await context.bot.send_message(user_id, "❌ 注册被拒绝")

    # 保留按钮
    await query.edit_message_reply_markup(reply_markup=query.message.reply_markup)

# =====================
# MAIN MENU
# =====================

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Scan RTP", callback_data="scan")],
        [InlineKeyboardButton("💰 Dompet", callback_data="wallet")],
        [InlineKeyboardButton("🔗 Share & Earn", callback_data="share")]
    ])

async def send_main_menu(update, context):
    await update.message.reply_video(
        VIDEO_FILE_ID,
        caption="🔥 MAXWIN AI RTP SYSTEM",
        reply_markup=main_menu_keyboard()
    )

# =====================
# SCAN FLOW
# =====================

async def scan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(p, callback_data=f"scan_platform_{p}")]
        for p in MERCHANT_LINKS.keys()
    ]
    keyboard.append([InlineKeyboardButton("⬅ 返回", callback_data="back")])

    await query.edit_message_caption(
        "🎮 请选择游戏平台",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def scan_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    platform = query.data.split("_")[2]
    context.user_data["scan_platform"] = platform

    keyboard = [
        [InlineKeyboardButton(p, callback_data=f"scan_game_{p}")]
        for p in PROVIDERS
    ]
    keyboard.append([InlineKeyboardButton("⬅ 返回", callback_data="scan")])

    await query.edit_message_caption(
        f"🏢 {platform}\n请选择游戏厂商",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def scan_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg = await query.edit_message_caption("🚀 AI ENGINE INITIALIZING...")

    for i in range(0, 101, 5):
        bar = "█"*(i//10) + "░"*(10 - i//10)
        await msg.edit_caption(
            f"⚡ AI RTP MATRIX SCANNING ⚡\n\n[{bar}] {i}%"
        )
        await asyncio.sleep(0.15)

    result = (
        f"🔍 SCAN RESULT\n"
        f"🏢 {context.user_data.get('scan_platform')}\n"
        f"🎮 {query.data.split('_')[2]}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🏆 Lucky Neko — 93%\n"
        "🔥 Sugar Rush — 88%\n"
        "💎 Mahjong Ways — 84%\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚠ 有效期 15 分钟"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 再次扫描", callback_data="scan")],
        [InlineKeyboardButton("⬅ 返回", callback_data="back")]
    ]

    await msg.edit_caption(result, reply_markup=InlineKeyboardMarkup(keyboard))

# =====================
# SHARE
# =====================

async def share_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = str(query.from_user.id)
    link = f"https://t.me/YOURBOT?start=REF{user}"

    keyboard = [
        [InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={link}")],
        [InlineKeyboardButton("⬅ 返回", callback_data="back")]
    ]

    await query.edit_message_caption(
        f"💰 SHARE AND EARN\n\n{link}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# BACK
# =====================

async def back_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_caption(
        "🔥 MAXWIN AI RTP SYSTEM",
        reply_markup=main_menu_keyboard()
    )

async def back_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(p, callback_data=f"reg_{p}")]
        for p in MERCHANT_LINKS.keys()
    ]

    await query.edit_message_text(
        "⚠ 请选择平台进行注册",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# HANDLERS
# =====================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose_language, pattern="lang_"))
app.add_handler(CallbackQueryHandler(register_platform, pattern="reg_"))
app.add_handler(CallbackQueryHandler(after_register, pattern="after_reg"))
app.add_handler(CallbackQueryHandler(admin_action, pattern="approve_|reject_"))
app.add_handler(CallbackQueryHandler(scan_menu, pattern="^scan$"))
app.add_handler(CallbackQueryHandler(scan_platform, pattern="scan_platform_"))
app.add_handler(CallbackQueryHandler(scan_result, pattern="scan_game_"))
app.add_handler(CallbackQueryHandler(share_link, pattern="share"))
app.add_handler(CallbackQueryHandler(back_menu, pattern="back"))
app.add_handler(CallbackQueryHandler(back_lang, pattern="back_lang"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id))
app.add_handler(MessageHandler(filters.CONTACT, receive_phone))

app.run_polling()
