from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from config import MERCHANT_LINKS, ADMIN_ID
from database import load, save
from datetime import datetime
import random

def generate_ref():
    return f"MW-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

async def show_register(update, context):
    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"reg_{m}")]
        for m in MERCHANT_LINKS
    ]
    keyboard.append([InlineKeyboardButton("⬅ Kembali", callback_data="back_main")])

    await update.callback_query.edit_message_caption(
        caption="⚠️Sila pilih salah satu platform berikut dan klik mendaftar\n⚠️Sila daftar melalui pautan rasmi 😘",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def register_merchant(update, context):
    query = update.callback_query
    merchant = query.data.split("_")[1]
    context.user_data["merchant"] = merchant

    link = MERCHANT_LINKS[merchant]

    keyboard = [
        [InlineKeyboardButton("🌐 点击注册", url=link)],
        [InlineKeyboardButton("✅ 我已注册", callback_data="input_id")]
    ]

    await query.edit_message_caption(
        caption=f"Platform: {merchant}\n\nKlik link untuk daftar.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
