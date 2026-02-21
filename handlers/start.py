from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from config import VIDEO_FILE_ID
from database import get_user, create_user

async def start(update, context):
    user_id = update.effective_user.id
    if not get_user(user_id):
        create_user(user_id)

    keyboard = [
        [InlineKeyboardButton("🎮 Scan RTP", callback_data="scan_menu")],
        [InlineKeyboardButton("📝 Daftar", callback_data="register_menu")],
    ]

    await update.message.reply_video(
        video=VIDEO_FILE_ID,
        caption="🔥Selamat datang ke MAXWIN AI RTP\n"
                "🤖AI yang scan RTP tertinggi dalam slot2\n"
                "📊 Tekan game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def setup(app):
    app.add_handler(CommandHandler("start", start))
