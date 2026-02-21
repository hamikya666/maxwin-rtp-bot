import importlib
import random
import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import MERCHANT_MODULES
from database import load, save

async def scan_menu(update, context):
    user_id = str(update.effective_user.id)
from database import ensure_user

users = ensure_user(user_id)

    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"scan_{m}")]
        for m in users[user_id]["merchants"]
    ]

    await update.callback_query.edit_message_caption(
        caption="🎮 Scan RTP",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def scan_platform(update, context):
    query = update.callback_query
    merchant = query.data.split("_")[1]
    context.user_data["merchant"] = merchant

    module = importlib.import_module(MERCHANT_MODULES[merchant])
    platforms = module.PLATFORMS.keys()

    keyboard = [
        [InlineKeyboardButton(p, callback_data=f"platform_{p}")]
        for p in platforms
    ]

    await query.edit_message_caption(
        caption="📊 Tekan platform game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
