from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import TOKEN, VIDEO_FILE_ID

import handlers.register as register
import handlers.scan as scan
import handlers.admin as admin
import handlers.wallet as wallet
import handlers.referral as referral

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🎮 Scan RTP", callback_data="scan_menu")],
        [InlineKeyboardButton("📝 Daftar", callback_data="register")],
        [InlineKeyboardButton("💰 DOMPET Boss", callback_data="wallet")],
        [InlineKeyboardButton("🔗 SHARE AND EARN", callback_data="ref")]
    ]

    await update.message.reply_video(
        VIDEO_FILE_ID,
        caption="🔥Selamat datang ke MAXWIN AI RTP\n🤖AI yang scan RTP tertinggi dalam slot2\n📊 Tekan game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(register.show_register, pattern="register"))
app.add_handler(CallbackQueryHandler(scan.scan_menu, pattern="scan_menu"))
app.add_handler(CallbackQueryHandler(wallet.wallet_handler, pattern="wallet"))
app.add_handler(CallbackQueryHandler(referral.referral_handler, pattern="ref"))

print("BOT RUNNING...")
app.run_polling()
