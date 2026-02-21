import os
import json
import random
import time
import asyncio
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

SCAN_VALIDITY = 900  # 15分钟
REFERRAL_REWARD = 1
MIN_WITHDRAWAL = 50

MERCHANT_LINKS = {
    "CM8": "https://bit.ly/MaxWinCM8",
    "A9PLAY": "http://a9play5.com/R=F7464F",
    "ALD99": "https://bit.ly/ALDMaxWin",
    "U9PLAY": "https://u9play99.com/R=C8BAAC",
}

# ================= DATA =================

USERS_FILE = "users.json"

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    USERS = json.load(f)


def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f, indent=2)


# ================= UTIL =================

def generate_ref_code(user_id):
    return f"REF{str(user_id)[-5:]}"


def now_str():
    return datetime.now().strftime("%d %b %Y %H:%M")


def generate_rtp():
    r = random.randint(40, 99)
    if r < 70:
        icon = "🛑"
    elif r < 80:
        icon = "✅"
    elif r < 90:
        icon = "🔥"
    else:
        icon = "🏆"
    return icon, r


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    ref = None
    if context.args:
        ref = context.args[0]

    if user_id not in USERS:
        USERS[user_id] = {
            "approved": False,
            "language": None,
            "phone": None,
            "merchants": {},
            "cooldowns": {},
            "wallet": {
                "balance": 0,
                "total_referrals": 0
            },
            "referral_code": generate_ref_code(user_id),
            "referred_by": ref
        }
        save_users()

    # referral reward
    if ref and user_id != ref:
        for uid, data in USERS.items():
            if data.get("referral_code") == ref:
                USERS[uid]["wallet"]["balance"] += REFERRAL_REWARD
                USERS[uid]["wallet"]["total_referrals"] += 1
                save_users()

    if not USERS[user_id]["approved"]:
        await language_menu(update)
    else:
        await main_menu(update)


# ================= LANGUAGE =================

async def language_menu(update):
    keyboard = [
        [InlineKeyboardButton("🇲🇾 Malay", callback_data="lang_my")]
    ]
    await update.message.reply_text(
        "🎰 Selamat Datang ke MaxWin RTP Bot Rasmi",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    USERS[user_id]["language"] = "MY"
    save_users()

    await register_menu(query)


# ================= REGISTER =================

async def register_menu(query):
    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"register_{m}")]
        for m in MERCHANT_LINKS.keys()
    ]
    await query.edit_message_text(
        "⚠️Sila pilih salah satu platform berikut dan klik mendaftar\n"
        "⚠️Sila daftar melalui pautan rasmi 😘",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def register_merchant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.split("_")[1]
    context.user_data["registering"] = merchant

    keyboard = [
        [InlineKeyboardButton("📝 Daftar", url=MERCHANT_LINKS[merchant])],
        [InlineKeyboardButton("⬅ Kembali", callback_data="back_register")]
    ]

    await query.edit_message_text(
        f"➡️Kemudian masukkan ID akaun:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if "registering" not in context.user_data:
        return

    merchant = context.user_data["registering"]
    account_id = update.message.text

    USERS[user_id]["merchants"][merchant] = {
        "account_id": account_id,
        "approved": False
    }

    save_users()

    button = KeyboardButton("📱 Share Phone", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True)

    await update.message.reply_text(
        "📱 Sila kongsi nombor telefon boss untuk AI daftar",
        reply_markup=keyboard
    )


async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    contact = update.message.contact.phone_number
    USERS[user_id]["phone"] = contact
    save_users()

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 NEW REGISTRATION REQUEST\n\n"
             f"👤 {update.effective_user.username}\n"
             f"📞 {contact}\n"
             f"🕒 {now_str()}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("Reject", callback_data=f"reject_{user_id}")
            ]
        ])
    )

    await update.message.reply_text(
        "⏳ Request bossku dah masuk. Sila tunggu admin approve dulu ya 😘"
    )


# ================= ADMIN =================

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_")

    if action == "approve":
        USERS[user_id]["approved"] = True
        save_users()
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Akaun Boss telah diluluskan🔥"
        )
        await query.edit_message_text("User Approved")

    if action == "reject":
        USERS[user_id]["approved"] = False
        save_users()
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Rejected. Sila daftar semula."
        )
        await query.edit_message_text("User Rejected")


# ================= MAIN MENU =================

async def main_menu(update):
    keyboard = [
        [InlineKeyboardButton("🎮 Scan RTP", callback_data="scan_menu")],
        [InlineKeyboardButton("📝 Daftar", callback_data="register_menu")],
        [InlineKeyboardButton("💰 DOMPET Boss", callback_data="wallet")],
        [InlineKeyboardButton("🔗 SHARE AND EARN", callback_data="share")]
    ]

    await update.message.reply_video(VIDEO_FILE_ID)
    await update.message.reply_text(
        "🔥Selamat datang ke MAXWIN AI RTP\n"
        "🤖AI yang scan RTP tertinggi dalam slot2\n"
        "📊 Tekan game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= SCAN =================

async def scan_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"scan_{m}")]
        for m in MERCHANT_LINKS.keys()
    ]

    await query.edit_message_text(
        "🔥Selamat datang ke MAXWIN AI RTP\n"
        "📊 Tekan platform game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def scan_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    merchant = query.data.split("_")[1]

    now = int(time.time())

    last = USERS[user_id]["cooldowns"].get(merchant)

    if last and now - last < SCAN_VALIDITY:
        remain = SCAN_VALIDITY - (now - last)
        await query.edit_message_text(
            f"⏳ Next Scan Available In: {remain//60}m {remain%60}s"
        )
        return

    USERS[user_id]["cooldowns"][merchant] = now
    save_users()

    msg = await query.edit_message_text(
        "Scanning probability layers...\n"
        "Initializing AI ENGINE...\n"
        "Syncing RTP MATRIX...\n"
        "[■■■■■■■■□□] 80%"
    )

    await asyncio.sleep(3)

    icon, rtp = generate_rtp()

    result = (
        f"🔍 SCAN RESULT — {merchant}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{icon} RTP — {rtp}%\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {now_str()}\n"
        f"⚠️ Valid 15 minit sahaja"
    )

    await msg.edit_text(result)


# ================= WALLET =================

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = USERS[user_id]["wallet"]

    await query.edit_message_text(
        f"💰 DOMPET Boss\n"
        f"👤 ID: {user_id}\n"
        f"📊 Total Invite: {data['total_referrals']} Orang\n"
        f"💵 Baki Wallet: RM {data['balance']}\n"
        f"Min withdrawal: RM{MIN_WITHDRAWAL}"
    )


# ================= SHARE =================

async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    code = USERS[user_id]["referral_code"]

    link = f"https://t.me/{context.bot.username}?start={code}"

    await query.edit_message_text(
        f"💰SHARE AND EARN💰\n\n{link}"
    )


# ================= RUN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(register_merchant, pattern="register_"))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="approve_|reject_"))
    app.add_handler(CallbackQueryHandler(scan_menu, pattern="scan_menu"))
    app.add_handler(CallbackQueryHandler(scan_engine, pattern="scan_"))
    app.add_handler(CallbackQueryHandler(wallet, pattern="wallet"))
    app.add_handler(CallbackQueryHandler(share, pattern="share"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))
    app.add_handler(MessageHandler(filters.CONTACT, receive_contact))

    print("BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()
