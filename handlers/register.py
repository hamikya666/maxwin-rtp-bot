from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import MERCHANT_LINKS
from database import ensure_user, save

async def choose_merchant(update, context):
    query = update.callback_query

    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"reg_{m}")]
        for m in MERCHANT_LINKS
    ]
    keyboard.append([InlineKeyboardButton("⬅ Kembali", callback_data="back_main")])

    await query.edit_message_text(
        "⚠️Sila pilih salah satu platform berikut dan klik mendaftar\n⚠️Sila daftar melalui pautan rasmi 😘",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def register_link(update, context):
    query = update.callback_query
    merchant = query.data.split("_")[1]

    link = MERCHANT_LINKS[merchant]

    keyboard = [
        [InlineKeyboardButton("🌐 Klik Untuk Daftar", url=link)],
        [InlineKeyboardButton("⬅ Kembali", callback_data="back_main")]
    ]

    await query.edit_message_text(
        f"Platform: {merchant}\n\nSila daftar melalui link rasmi.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
