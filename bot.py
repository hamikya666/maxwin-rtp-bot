import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ✅ 从 Railway 读取环境变量
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN 未设置，请去 Railway Variables 添加")

# ========================
# 语言选择
# ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_ms")],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_cn")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Please Select Language / Sila pilih bahasa / 请选择语言",
        reply_markup=reply_markup,
    )

# ========================
# 语言点击
# ========================

async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("CM8", callback_data="merchant_CM8")],
        [InlineKeyboardButton("A9PLAY", callback_data="merchant_A9PLAY")],
        [InlineKeyboardButton("ALD99", callback_data="merchant_ALD99")],
        [InlineKeyboardButton("U9PLAY", callback_data="merchant_U9PLAY")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🔥 Welcome to MAXWIN AI RTP\n\nPlease Select Platform",
        reply_markup=reply_markup,
    )

# ========================
# 商家点击
# ========================

async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.replace("merchant_", "")

    keyboard = [
        [InlineKeyboardButton("🎮 Scan RTP", callback_data=f"scan_{merchant}")],
        [InlineKeyboardButton("📝 Register", callback_data=f"register_{merchant}")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_main")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Platform: {merchant}\n\nSelect Option",
        reply_markup=reply_markup,
    )

# ========================
# 返回主菜单
# ========================

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await start(update, context)

# ========================
# 主程序
# ========================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="back_main"))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
