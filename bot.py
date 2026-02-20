import random
import asyncio
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

# ===== 导入商家数据 =====
from data import cm8, a9play, ald99, u9play

# ===== 你的BOT TOKEN =====
BOT_TOKEN = "你的BOT_TOKEN"

# ===== 商家数据整合 =====
MERCHANT_DATA = {
    "CM8": cm8.PLATFORMS,
    "A9PLAY": a9play.PLATFORMS,
    "ALD99": ald99.PLATFORMS,
    "U9PLAY": u9play.PLATFORMS
}

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("CM8", callback_data="merchant_CM8")],
        [InlineKeyboardButton("A9PLAY", callback_data="merchant_A9PLAY")],
        [InlineKeyboardButton("ALD99", callback_data="merchant_ALD99")],
        [InlineKeyboardButton("U9PLAY", callback_data="merchant_U9PLAY")]
    ]

    await update.message.reply_text(
        "🔥 Welcome to MAXWIN AI RTP\n\nSelect Merchant:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====== 点击商家 ======
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.split("_")[1]

    platforms = MERCHANT_DATA.get(merchant, {})

    keyboard = []
    for platform in platforms.keys():
        keyboard.append(
            [InlineKeyboardButton(platform, callback_data=f"platform_{merchant}_{platform}")]
        )

    keyboard.append(
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    )

    await query.edit_message_text(
        f"{merchant} - Select Platform:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====== 点击平台 ======
async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, merchant, platform = query.data.split("_")

    games = MERCHANT_DATA[merchant][platform]

    # ===== Loading 动画 =====
    loading_steps = [
        "Loading AI Engine...",
        "Calibrating Volatility Index...",
        "Syncing RTP Matrix...",
        "Analyzing Slot Probability...",
        "Finalizing Data..."
    ]

    for i, step in enumerate(loading_steps):
        percent = int((i+1) / len(loading_steps) * 100)
        bar = "■" * (percent // 10) + "□" * (10 - percent // 10)

        await query.edit_message_text(
            f"{step}\n[{bar}] {percent}%"
        )
        await asyncio.sleep(0.8)

    # ===== 生成 RTP =====
    result_text = f"🔍 SCAN RESULT — {platform}\n"
    result_text += "━━━━━━━━━━━━━━━━━━\n"

    best_rtp = 0
    hot_count = 0

    for game in games:
        rtp = round(random.uniform(30, 98), 2)

        if rtp < 70:
            icon = "🛑"
        elif rtp < 80:
            icon = "✅"
        elif rtp < 90:
            icon = "🔥"
            hot_count += 1
        else:
            icon = "🏆"
            hot_count += 1

        if rtp > best_rtp:
            best_rtp = rtp

        result_text += f"{icon} {game} — {rtp}%\n"

    result_text += "━━━━━━━━━━━━━━━━━━\n"
    result_text += f"📊 Total: {len(games)} | 🔥 Hot: {hot_count}\n"
    result_text += f"⚡ Best RTP: {best_rtp}%\n"
    result_text += f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}\n"
    result_text += "⚠️ Valid 15 minutes only"

    keyboard = [
        [InlineKeyboardButton("🔄 Scan Again", callback_data=f"platform_{merchant}_{platform}")],
        [InlineKeyboardButton("🔙 Back to Platforms", callback_data=f"merchant_{merchant}")]
    ]

    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====== 返回主菜单 ======
async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("CM8", callback_data="merchant_CM8")],
        [InlineKeyboardButton("A9PLAY", callback_data="merchant_A9PLAY")],
        [InlineKeyboardButton("ALD99", callback_data="merchant_ALD99")],
        [InlineKeyboardButton("U9PLAY", callback_data="merchant_U9PLAY")]
    ]

    await query.edit_message_text(
        "🔥 Welcome to MAXWIN AI RTP\n\nSelect Merchant:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(platform_handler, pattern="platform_"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="back_main"))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
