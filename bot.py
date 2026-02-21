import os
import json
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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
VIDEO_URL = os.environ.get("VIDEO_URL")

DATA_FILE = "users.json"

# ======================
# 数据读写
# ======================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data_store, f, indent=4)

user_data_store = load_data()

# ======================
# 生成编号
# ======================

def generate_application_no():
    today = datetime.now().strftime("%Y%m%d")
    count = sum(1 for u in user_data_store.values()
                for m in u.get("applications", [])
                if m.startswith(f"MW-{today}"))
    return f"MW-{today}-{count+1:04d}"

# ======================
# /start
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_ms")],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_cn")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]
    await update.message.reply_text(
        "Please Select Language",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ======================
# 语言选择
# ======================

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

# ======================
# 商家点击
# ======================

async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    merchant = query.data.replace("merchant_", "")

    user = user_data_store.get(user_id)

    # 新客户
    if not user or not user.get("approved", False):
        await query.edit_message_text(
            "注册好了请提供账户ID让Admin给您最高Scan的权限\n\n"
            "Please enter your Game ID:"
        )
        context.user_data["registering"] = merchant
        return

    # 老客户
    registered = merchant in user.get("merchants", {})

    if VIDEO_URL:
        await context.bot.send_video(chat_id=query.message.chat_id, video=VIDEO_URL)

    keyboard = [
        [InlineKeyboardButton("🎮 Scan RTP", url="https://example.com/scan")],
        [InlineKeyboardButton("📝 Register", callback_data=f"register_{merchant}")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_main")],
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

# ======================
# 注册按钮（老客户追加）
# ======================

async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.replace("register_", "")
    context.user_data["registering"] = merchant

    await query.edit_message_text(
        f"Please enter your {merchant} Game ID:"
    )

# ======================
# 接收ID
# ======================

async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "NoUsername"
    merchant = context.user_data.get("registering")

    if not merchant:
        return

    player_id = update.message.text
    application_no = generate_application_no()

    is_new = user_id not in user_data_store

    if is_new:
        user_data_store[user_id] = {
            "approved": False,
            "phone": None,
            "language": context.user_data.get("language"),
            "merchants": {},
            "applications": []
        }

    user = user_data_store[user_id]
    user["merchants"][merchant] = player_id
    user["applications"].append(application_no)

    total_merchants = len(user["merchants"])

    save_data()

    # 新客户
    if is_new:
        admin_text = (
            "📥 NEW REGISTRATION REQUEST\n\n"
            f"🆔 Application: {application_no}\n"
            f"👤 Username: @{username}\n"
            f"🏢 Merchant: {merchant}\n"
            f"🎮 Game ID: {player_id}\n"
            f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}"
        )

        keyboard = [
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")]
        ]

        await context.bot.send_message(
            ADMIN_ID,
            admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        await update.message.reply_text("Registration submitted. Waiting for admin approval.")

    # 老客户追加
    else:
        admin_text = (
            "🔁 ADDITIONAL MERCHANT REGISTRATION\n\n"
            f"🆔 Ref No: {application_no}\n"
            f"👤 Username: @{username}\n"
            f"🏢 Merchant: {merchant}\n"
            f"🎮 Game ID: {player_id}\n"
            f"📊 Total Merchants: {total_merchants}\n"
            f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
            "ℹ️ Existing approved user"
        )

        await context.bot.send_message(ADMIN_ID, admin_text)
        await update.message.reply_text("Merchant registered successfully!")

    context.user_data["registering"] = None

# ======================
# Approve
# ======================

async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.data.replace("approve_", "")
    if user_id in user_data_store:
        user_data_store[user_id]["approved"] = True
        save_data()

        await context.bot.send_message(user_id, "✅ Your account has been approved. You can now use Scan.")
        await query.edit_message_text("User approved.")

# ======================
# 返回
# ======================

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await language_handler(update, context)

# ======================
# 主程序
# ======================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(register_handler, pattern="register_"))
    app.add_handler(CallbackQueryHandler(approve_handler, pattern="approve_"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="back_main"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
