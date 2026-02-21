from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import TOKEN, VIDEO_FILE_ID, MERCHANT_LINKS
from database import ensure_user, save
import handlers.register as register
import handlers.wallet as wallet
import handlers.referral as referral

async def start(update, context):
    user_id = str(update.effective_user.id)
    users = ensure_user(user_id)
    user = users[user_id]

    # 语言选择
    if user["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_cn")],
            [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
        ]
        await update.message.reply_text(
            "Please choose language:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 未审核
    if user["status"] != "APPROVED":
        await update.message.reply_text(
            "⏳ Request bossku dah masuk.\nSila tunggu admin approve dulu ya 😘"
        )
        return

    # 主菜单
    keyboard = [
        [InlineKeyboardButton("🎮 Scan RTP", callback_data="scan")],
        [InlineKeyboardButton("📝 Daftar", callback_data="register")],
        [InlineKeyboardButton("💰 DOMPET Boss", callback_data="wallet")],
        [InlineKeyboardButton("🔗 SHARE AND EARN", callback_data="ref")]
    ]

    await update.message.reply_video(
        VIDEO_FILE_ID,
        caption="🔥Selamat datang ke MAXWIN AI RTP\n🤖AI yang scan RTP tertinggi dalam slot2\n📊 Tekan game menu di bawah untuk mula",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_language(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)

    users = ensure_user(user_id)

    if query.data == "lang_cn":
        users[user_id]["language"] = "CN"
    else:
        users[user_id]["language"] = "MY"

    save(users)

    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"reg_{m}")]
        for m in MERCHANT_LINKS
    ]

    await query.edit_message_text(
        "⚠️Sila pilih salah satu platform berikut dan klik mendaftar\n⚠️Sila daftar melalui pautan rasmi 😘",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_main(update, context):
    await start(update, context)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(set_language, pattern="lang_"))
app.add_handler(CallbackQueryHandler(register.choose_merchant, pattern="register"))
app.add_handler(CallbackQueryHandler(register.register_link, pattern="reg_"))
app.add_handler(CallbackQueryHandler(wallet.wallet_menu, pattern="wallet"))
app.add_handler(CallbackQueryHandler(wallet.withdraw, pattern="withdraw"))
app.add_handler(CallbackQueryHandler(referral.referral_menu, pattern="ref"))
app.add_handler(CallbackQueryHandler(back_main, pattern="back_main"))

print("BOT RUNNING...")
app.run_polling()
