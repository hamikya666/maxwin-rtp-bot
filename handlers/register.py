from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from config import MERCHANT_LINKS
from database import get_user

async def register_menu(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(m, url=link)]
        for m, link in MERCHANT_LINKS.items()
    ]

    await query.edit_message_caption(
        caption="⚠️Sila pilih salah satu platform berikut dan klik mendaftar\n"
                "⚠️Sila daftar melalui pautan rasmi 😘",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def setup(app):
    app.add_handler(CallbackQueryHandler(register_menu, pattern="register_menu"))
