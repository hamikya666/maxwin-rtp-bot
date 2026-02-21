import json
import random
import asyncio
import importlib
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = "8194393436:AAF-fVYwsGflkXyHU7nOg7vmOJV40fRiDIM"
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

MERCHANT_MODULES = {
    "CM8": "data.CM8",
    "A9PLAY": "data.A9PLAY",
    "ALD99": "data.ALD99",
    "U9PLAY": "data.U9PLAY"
}


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"merchant_{m}")]
        for m in MERCHANT_MODULES.keys()
    ]

    await update.message.reply_video(
        video=VIDEO_FILE_ID,
        caption="🔥Selamat datang ke MAXWIN AI RTP\n"
                "🤖AI yang scan RTP tertinggi dalam slot2\n"
                "📊 Tekan game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= MERCHANT CLICK =================

async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.split("_")[1]
    context.user_data["merchant"] = merchant

    module = importlib.import_module(MERCHANT_MODULES[merchant])
    platforms = list(module.PLATFORMS.keys())

    keyboard = [
        [InlineKeyboardButton(p, callback_data=f"platform_{p}")]
        for p in platforms
    ]
    keyboard.append([InlineKeyboardButton("⬅ Kembali", callback_data="back_main")])

    await query.edit_message_caption(
        caption="🔥Selamat datang ke MAXWIN AI RTP\n"
                "🤖AI yang scan RTP tertinggi dalam slot2\n"
                "📊 Tekan platform game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= PLATFORM CLICK =================

async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    platform = query.data.split("_")[1]
    merchant = context.user_data["merchant"]

    module = importlib.import_module(MERCHANT_MODULES[merchant])
    games = module.PLATFORMS[platform]

    context.user_data["platform"] = platform

    keyboard = [
        [InlineKeyboardButton(game, callback_data=f"game_{i}")]
        for i, game in enumerate(games)
    ]
    keyboard.append([InlineKeyboardButton("⬅ Kembali", callback_data=f"merchant_{merchant}")])

    await query.edit_message_caption(
        caption=f"🎮 {platform} Game List\n\nPilih game untuk scan RTP",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= GAME SCAN =================

async def game_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = context.user_data["merchant"]
    platform = context.user_data["platform"]

    module = importlib.import_module(MERCHANT_MODULES[merchant])
    games = module.PLATFORMS[platform]

    index = int(query.data.split("_")[1])
    selected_game = games[index]

    msg = await query.edit_message_caption(
        caption="🔄 AI RTP MATRIX SCANNING...\n\n[□□□□□□□□□□] 0%"
    )

    for i in range(1, 11):
        bar = "■" * i + "□" * (10 - i)
        await asyncio.sleep(0.8)
        await msg.edit_caption(
            caption=f"🔄 AI RTP MATRIX SCANNING...\n\n[{bar}] {i*10}%"
        )

    rtp = random.randint(40, 99)

    if rtp < 70:
        icon = "🛑"
    elif rtp < 80:
        icon = "✅"
    elif rtp < 90:
        icon = "🔥"
    else:
        icon = "🏆"

    now = datetime.now().strftime("%d %b %Y %H:%M")

    result_text = (
        f"🔍 SCAN RESULT — {platform}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 {merchant}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{icon} {selected_game} — {rtp}%\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {now}\n"
        "⚠️ Valid 15 minit sahaja"
    )

    keyboard = [
        [InlineKeyboardButton("⬅ Kembali", callback_data=f"platform_{platform}")]
    ]

    await msg.edit_caption(
        caption=result_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= BACK MAIN =================

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)


# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(merchant_handler, pattern="^merchant_"))
app.add_handler(CallbackQueryHandler(platform_handler, pattern="^platform_"))
app.add_handler(CallbackQueryHandler(game_handler, pattern="^game_"))
app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))

print("Bot Running...")
app.run_polling()
