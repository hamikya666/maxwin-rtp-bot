import asyncio
import random
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from database import get_user, update_user

async def scan_menu(update, context):
    query = update.callback_query
    await query.answer()

    msg = await query.edit_message_caption(
        caption="Scanning probability layers...\n[□□□□□□□□□□] 0%"
    )

    for i in range(1, 11):
        bar = "■" * i + "□" * (10 - i)
        await asyncio.sleep(0.8)
        await msg.edit_caption(
            caption=f"Scanning probability layers...\n[{bar}] {i*10}%"
        )

    rtp = random.randint(40, 99)
    now = datetime.now().strftime("%d %b %Y %H:%M")

    await msg.edit_caption(
        caption=f"🔍 SCAN RESULT\n\nRTP: {rtp}%\n🕒 {now}\n⚠️ Valid 15 minit sahaja"
    )

def setup(app):
    app.add_handler(CallbackQueryHandler(scan_menu, pattern="scan_menu"))
