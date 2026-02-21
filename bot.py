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
ADMIN_ID = 5473935017  # 改成你的Telegram ID
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

USERS_FILE = "users.json"

MERCHANT_LINKS = {
    "CM8": "https://bit.ly/MaxWinCM8",
    "A9PLAY": "http://a9play5.com/R=F7464F",
    "ALD99": "https://bit.ly/ALDMaxWin",
    "U9PLAY": "https://u9play99.com/R=C8BAAC"
}

# =============================
# USER DATA
# =============================

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

# =============================
# START
# =============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)

    if user in USERS and USERS[user]["status"] == "WAIT_APPROVAL":
        await update.message.reply_text(
            "⏳ Request bossku sedang diproses.\nSila tunggu admin approve ya 😘"
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
        "merchants": [],
        "wallet": 0
    }
    save_users(USERS)

    keyboard = [
        [InlineKeyboardButton("🇲🇾 Malay", callback_data="lang_ms")],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_cn")]
    ]

    await update.message.reply_text(
        "🎰 Selamat Datang ke MaxWin RTP Bot Rasmi",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# LANGUAGE
# =============================

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = str(query.from_user.id)
    USERS[user]["language"] = query.data
    USERS[user]["status"] = "REGISTERING"
    save_users(USERS)

    keyboard = [
        [InlineKeyboardButton("CM8", callback_data="reg_CM8")],
        [InlineKeyboardButton("A9PLAY", callback_data="reg_A9PLAY")],
        [InlineKeyboardButton("ALD99", callback_data="reg_ALD99")],
        [InlineKeyboardButton("U9PLAY", callback_data="reg_U9PLAY")]
    ]

    await query.edit_message_text(
        "⚠️Sila pilih salah satu platform berikut dan klik mendaftar\n"
        "⚠️Sila daftar melalui pautan rasmi 😘",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# REGISTER FLOW
# =============================

async def register_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = str(query.from_user.id)
    platform = query.data.split("_")[1]

    context.user_data["register_platform"] = platform

    await query.edit_message_text(
        f"➡️ Kemudian masukkan ID akaun untuk {platform}:"
    )

async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)

    if USERS[user]["status"] != "REGISTERING":
        return

    USERS[user]["game_id"] = update.message.text
    save_users(USERS)

    keyboard = [[KeyboardButton("📱 Share Phone", request_contact=True)]]

    await update.message.reply_text(
        "📱 Sila kongsi nombor telefon boss untuk AI daftar",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.effective_user.id)

    if USERS[user]["status"] != "REGISTERING":
        return

    USERS[user]["phone"] = update.message.contact.phone_number
    USERS[user]["status"] = "WAIT_APPROVAL"
    USERS[user]["application_id"] = generate_app_id()
    save_users(USERS)

    await update.message.reply_text(
        "⏳ Permohonan sedang diproses oleh AI Verification System.\n"
        "Sila tunggu admin approve ya 😘",
        reply_markup=ReplyKeyboardRemove()
    )

    # Send to admin
    app_id = USERS[user]["application_id"]

    text = (
        f"📥 NEW REGISTRATION REQUEST\n\n"
        f"🆔 Application: {app_id}\n"
        f"👤 Username: @{update.effective_user.username}\n"
        f"📞 Phone: {USERS[user]['phone']}\n"
        f"🏢 Merchant: {context.user_data.get('register_platform')}\n"
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

# =============================
# ADMIN ACTION
# =============================

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_")

    if action == "approve":
        USERS[user_id]["status"] = "APPROVED"
        save_users(USERS)

        await context.bot.send_message(
            int(user_id),
            "✅ Akaun Boss telah diluluskan🔥"
        )

        await context.bot.send_video(
            int(user_id),
            VIDEO_FILE_ID,
            caption="🔥Selamat datang ke MAXWIN AI RTP\n"
                    "🤖AI yang scan RTP tertinggi dalam slot2\n"
                    "📊 Tekan game menu di bawah untuk mula",
            reply_markup=main_menu_keyboard()
        )

        await query.edit_message_text("✅ Approved")

    else:
        USERS[user_id]["status"] = "NEW"
        save_users(USERS)

        await context.bot.send_message(
            int(user_id),
            "❌ Permohonan ditolak.\nSila daftar semula."
        )

        await query.edit_message_text("❌ Rejected")

# =============================
# MAIN MENU
# =============================

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Scan RTP", callback_data="scan")],
        [InlineKeyboardButton("💰 Dompet", callback_data="wallet")],
        [InlineKeyboardButton("🔗 Share & Earn", callback_data="share")]
    ])

async def send_main_menu(update, context):
    await update.message.reply_video(
        VIDEO_FILE_ID,
        caption="🔥Selamat datang ke MAXWIN AI RTP\n"
                "🤖AI yang scan RTP tertinggi dalam slot2\n"
                "📊 Tekan game menu di bawah untuk mula",
        reply_markup=main_menu_keyboard()
    )

# =============================
# SCAN
# =============================

async def scan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(x, callback_data=f"scan_{x}")]
        for x in MERCHANT_LINKS.keys()
    ]
    keyboard.append([InlineKeyboardButton("⬅ Kembali", callback_data="back")])

    await query.edit_message_caption(
        "🔥Selamat datang ke MAXWIN AI RTP\n"
        "🤖AI yang scan RTP tertinggi dalam slot2\n"
        "📊 Tekan platform game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def scan_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    msg = await query.edit_message_caption("🔄 Initializing AI ENGINE...")

    for i in range(0, 101, 10):
        bar = "█"*(i//10) + "□"*(10 - i//10)
        await msg.edit_caption(f"🔄 AI RTP MATRIX SCANNING...\n[{bar}] {i}%")
        await asyncio.sleep(0.4)

    expire = datetime.now() + timedelta(minutes=15)

    result = (
        f"🔍 SCAN RESULT — {query.data.split('_')[1]}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 ID: {USERS[str(query.from_user.id)]['game_id']}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🏆 Goddess of Egypt — 92%\n"
        "🔥 Coin Express — 80%\n"
        "✅ Lady Fortune — 75%\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}\n"
        "⚠️ Valid 15 minit sahaja\n"
        f"⏳ Expire at: {expire.strftime('%H:%M')}"
    )

    await msg.edit_caption(result)

# =============================
# SHARE
# =============================

async def share_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = str(query.from_user.id)
    link = f"https://t.me/YourBot?start=REF{user}"

    keyboard = [
        [InlineKeyboardButton("📤 Share Link",
                              url=f"https://t.me/share/url?url={link}")]
    ]

    await query.edit_message_caption(
        f"💰SHARE AND EARN💰\n\n{link}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================
# BACK
# =============================

async def back_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_caption(
        "🔥Selamat datang ke MAXWIN AI RTP\n"
        "🤖AI yang scan RTP tertinggi dalam slot2\n"
        "📊 Tekan game menu di bawah untuk mula",
        reply_markup=main_menu_keyboard()
    )

# =============================
# MAIN
# =============================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose_language, pattern="lang_"))
app.add_handler(CallbackQueryHandler(register_platform, pattern="reg_"))
app.add_handler(CallbackQueryHandler(admin_action, pattern="approve_|reject_"))
app.add_handler(CallbackQueryHandler(scan_menu, pattern="^scan$"))
app.add_handler(CallbackQueryHandler(scan_result, pattern="scan_"))
app.add_handler(CallbackQueryHandler(share_link, pattern="share"))
app.add_handler(CallbackQueryHandler(back_menu, pattern="back"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id))
app.add_handler(MessageHandler(filters.CONTACT, receive_phone))

app.run_polling()
