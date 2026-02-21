import os
import json
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

DATA_FILE = "users.json"

# =====================
# 数据存储
# =====================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data_store, f, indent=4)

user_data_store = load_data()

# =====================
# 编号生成
# =====================

def generate_application_no():
    today = datetime.now().strftime("%Y%m%d")
    count = sum(
        1
        for u in user_data_store.values()
        for a in u.get("applications", [])
        if a.startswith(f"MW-{today}")
    )
    return f"MW-{today}-{count+1:04d}"

# =====================
# /start
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = user_data_store.get(user_id)

    if user and user.get("pending", False):
        await update.message.reply_text(
            "⏳ Your registration is under review.\nPlease wait for admin approval."
        )
        return

    keyboard = [
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_ms")],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_cn")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]

    await update.message.reply_text(
        "Please Select Language",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# =====================
# 语言
# =====================

async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["language"] = query.data.replace("lang_", "")

    keyboard = [
        [InlineKeyboardButton("CM8", callback_data="merchant_CM8")],
        [InlineKeyboardButton("A9PLAY", callback_data="merchant_A9PLAY")],
        [InlineKeyboardButton("ALD99", callback_data="merchant_ALD99")],
        [InlineKeyboardButton("U9PLAY", callback_data="merchant_U9PLAY")],
    ]

    await query.edit_message_text(
        "🔥 Welcome to MAXWIN AI RTP\n\nPlease Select Platform",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# =====================
# 商家点击
# =====================

async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    merchant = query.data.replace("merchant_", "")
    user = user_data_store.get(user_id)

    # 完全新客户
    if not user:
        keyboard = [
            [InlineKeyboardButton("📝 Register", callback_data=f"newreg_{merchant}")],
            [InlineKeyboardButton("⬅ Back", callback_data="back_lang")],
        ]
        await query.edit_message_text(
            "🔥 Welcome to MAXWIN AI RTP\n\nPlease register to continue.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # 未批准用户
    if user.get("pending", False):
        await query.edit_message_text(
            "⏳ Your registration is under review.\nPlease wait for admin approval."
        )
        return

    # 已批准老客户
    registered = merchant in user.get("merchants", {})

    if VIDEO_FILE_ID:
    await context.bot.send_video(
        chat_id=query.message.chat_id,
        video=VIDEO_FILE_ID
    )

    keyboard = [
        [InlineKeyboardButton("🎮 Scan RTP", url="https://example.com/scan")],
        [InlineKeyboardButton("📝 Register", callback_data="additional_register")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_lang")],
    ]

    if not registered:
        text = (
            "🔥 Selamat datang ke MAXWIN AI RTP\n"
            "🤖 AI yang scan RTP tertinggi dalam slot\n"
            "📊 Sistem mengesan bahawa bossku masih belum mendaftar di platform ini.\n"
            "Boss boleh klik \"Daftar\" dalam direktori."
        )
    else:
        text = f"Platform: {merchant}\n\nReady to Scan"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# =====================
# 新客户注册
# =====================

async def new_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.replace("newreg_", "")
    context.user_data["registering"] = merchant
    context.user_data["new_user"] = True

    keyboard = [[InlineKeyboardButton("⬅ Back", callback_data="back_lang")]]

    await query.edit_message_text(
        f"Please enter your {merchant} Game ID:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# =====================
# 老客户追加注册
# =====================

async def additional_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("CM8", callback_data="add_CM8")],
        [InlineKeyboardButton("A9PLAY", callback_data="add_A9PLAY")],
        [InlineKeyboardButton("ALD99", callback_data="add_ALD99")],
        [InlineKeyboardButton("U9PLAY", callback_data="add_U9PLAY")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_lang")],
    ]

    await query.edit_message_text(
        "Select merchant to register:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# =====================
# 老客户选择追加商家
# =====================

async def add_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.replace("add_", "")
    context.user_data["registering"] = merchant
    context.user_data["new_user"] = False

    await query.edit_message_text(
        f"Please enter your {merchant} Game ID:"
    )

# =====================
# 接收ID
# =====================

async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    merchant = context.user_data.get("registering")

    if not merchant:
        return

    context.user_data["player_id"] = update.message.text

    if context.user_data.get("new_user", False):
        # 要求share phone
        button = KeyboardButton("Share Phone", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True)
        await update.message.reply_text(
            "Please share your phone number:",
            reply_markup=reply_markup,
        )
    else:
        await finalize_registration(update, context)

# =====================
# 接收电话
# =====================

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    contact = update.message.contact

    if not contact:
        return

    context.user_data["phone"] = contact.phone_number
    await finalize_registration(update, context)

# =====================
# 完成注册
# =====================

async def finalize_registration(update, context):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "NoUsername"
    merchant = context.user_data["registering"]
    player_id = context.user_data["player_id"]
    application_no = generate_application_no()

    new_user = context.user_data.get("new_user", False)

    if user_id not in user_data_store:
        user_data_store[user_id] = {
            "approved": False,
            "pending": True,
            "phone": context.user_data.get("phone"),
            "language": context.user_data.get("language"),
            "merchants": {},
            "applications": []
        }

    user = user_data_store[user_id]
    user["merchants"][merchant] = player_id
    user["applications"].append(application_no)

    total_merchants = len(user["merchants"])
    save_data()

    if new_user:
        text = (
            "📥 NEW REGISTRATION REQUEST\n\n"
            f"🆔 Application: {application_no}\n"
            f"👤 Username: @{username}\n"
            f"📞 Phone: {context.user_data.get('phone')}\n"
            f"🏢 Merchant: {merchant}\n"
            f"🎮 Game ID: {player_id}\n"
            f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
            ]
        ]

        await context.bot.send_message(
            ADMIN_ID,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        await update.message.reply_text(
            "⏳ Registration submitted.\nPlease wait for admin approval."
        )
    else:
        text = (
            "🔁 ADDITIONAL MERCHANT REGISTRATION\n\n"
            f"🆔 Ref No: {application_no}\n"
            f"👤 Username: @{username}\n"
            f"🏢 Merchant: {merchant}\n"
            f"🎮 Game ID: {player_id}\n"
            f"📊 Total Merchants: {total_merchants}\n"
            f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
            "ℹ️ Existing approved user"
        )

        await context.bot.send_message(ADMIN_ID, text)
        await update.message.reply_text("✅ Merchant registered successfully!")

    context.user_data.clear()

# =====================
# Approve / Reject
# =====================

async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.data.replace("approve_", "")
    user = user_data_store.get(user_id)

    if user:
        user["approved"] = True
        user["pending"] = False
        save_data()

        await context.bot.send_message(
            user_id,
            "✅ Your registration has been approved.\nYou may now use Scan."
        )

        await query.edit_message_reply_markup(reply_markup=None)

async def reject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.data.replace("reject_", "")
    if user_id in user_data_store:
        del user_data_store[user_id]
        save_data()

        await context.bot.send_message(
            user_id,
            "❌ Your registration was rejected.\nPlease register again."
        )

        await query.edit_message_reply_markup(reply_markup=None)

# =====================
# 返回语言
# =====================

async def back_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await language_handler(update, context)

# =====================
# 主程序
# =====================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(new_register, pattern="newreg_"))
    app.add_handler(CallbackQueryHandler(additional_register, pattern="additional_register"))
    app.add_handler(CallbackQueryHandler(add_select, pattern="add_"))
    app.add_handler(CallbackQueryHandler(approve_handler, pattern="approve_"))
    app.add_handler(CallbackQueryHandler(reject_handler, pattern="reject_"))
    app.add_handler(CallbackQueryHandler(back_lang, pattern="back_lang"))

    app.add_handler(MessageHandler(filters.CONTACT, receive_phone))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
