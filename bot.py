import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN 未设置")

# =========================
# 临时数据存储
# =========================
user_data_store = {}
waiting_for_id = {}

# =========================
# /start
# =========================
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

# =========================
# 语言选择
# =========================
async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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

# =========================
# 商家点击
# =========================
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    merchant = query.data.replace("merchant_", "")

    if user_id not in user_data_store or merchant not in user_data_store[user_id]:

        # ❗ 未注册显示视频 + 提示
        keyboard = [
            [InlineKeyboardButton("📝 Daftar", callback_data=f"register_{merchant}")],
            [InlineKeyboardButton("⬅ Back", callback_data="back_main")],
        ]

        await query.edit_message_text(
            "🔥 Selamat datang ke MAXWIN AI RTP\n"
            "🤖 AI yang scan RTP tertinggi dalam slot\n"
            "📊 Sistem mengesan bahawa bossku masih belum mendaftar di platform ini.\n"
            "Boss boleh klik \"Daftar\" dalam direktori.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    else:
        # ✅ 已注册
        keyboard = [
            [InlineKeyboardButton("🎮 Scan RTP", callback_data=f"scan_{merchant}")],
            [InlineKeyboardButton("⬅ Back", callback_data="back_main")],
        ]

        await query.edit_message_text(
            f"Platform: {merchant}\n\nReady to Scan",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

# =========================
# 点击注册
# =========================
async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.replace("register_", "")
    user_id = query.from_user.id

    waiting_for_id[user_id] = merchant

    await query.edit_message_text(
        f"Please enter your {merchant} ID:"
    )

# =========================
# 接收ID
# =========================
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in waiting_for_id:
        merchant = waiting_for_id[user_id]
        player_id = update.message.text

        if user_id not in user_data_store:
            user_data_store[user_id] = {}

        user_data_store[user_id][merchant] = player_id
        del waiting_for_id[user_id]

        await update.message.reply_text(
            f"✅ ID saved for {merchant}!\nReturning to main menu..."
        )

        await start(update, context)

# =========================
# 返回
# =========================
async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

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

# =========================
# 主程序
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(register_handler, pattern="register_"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="back_main"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
