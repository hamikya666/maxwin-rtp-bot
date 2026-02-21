import os
import json
import time
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from data import MERCHANTS

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

VIDEO_FILE_ID = "PUT_YOUR_VIDEO_FILE_ID_HERE"
USERS_FILE = "users.json"
SCAN_COOLDOWN = 900  # 15分钟

# ---------------- LOAD USERS ---------------- #

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users = json.load(f)

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in users:
        await show_language(update)
        return

    if not users[user_id]["approved"]:
        await update.message.reply_text("⏳ Waiting for Admin approval.")
        return

    await show_main_menu(update)

# ---------------- LANGUAGE ---------------- #

async def show_language(update):
    keyboard = [
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇾 Malay", callback_data="lang_my")]
    ]
    await update.message.reply_text(
        "🌐 Select Language",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    user_id = str(query.from_user.id)

    users[user_id] = {
        "language": lang,
        "approved": False,
        "merchants": {},
        "cooldowns": {}
    }

    save_users()
    await show_merchant_selection(query)

# ---------------- REGISTER ---------------- #

async def show_merchant_selection(query):
    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"register_{m}")]
        for m in MERCHANTS.keys()
    ]
    await query.edit_message_text(
        "Select Merchant to Register:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def register_merchant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    merchant = query.data.split("_")[1]
    context.user_data["registering"] = merchant

    await query.edit_message_text(
        f"Register via official link then send your Account ID for {merchant}:"
    )

async def receive_account_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if "registering" not in context.user_data:
        return

    merchant = context.user_data["registering"]
    account_id = update.message.text

    users[user_id]["merchants"][merchant] = account_id
    save_users()

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"NEW REGISTRATION\nUser: {user_id}\nMerchant: {merchant}\nID: {account_id}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("Reject", callback_data=f"reject_{user_id}")
            ]
        ])
    )

    await update.message.reply_text("✅ Registration submitted. Waiting approval.")
    context.user_data.pop("registering")

# ---------------- ADMIN ---------------- #

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_")

    if action == "approve":
        users[user_id]["approved"] = True
        save_users()
        await context.bot.send_message(chat_id=user_id, text="✅ Approved!")
        await query.edit_message_text("User approved.")

    if action == "reject":
        users.pop(user_id, None)
        save_users()
        await context.bot.send_message(chat_id=user_id, text="❌ Rejected.")
        await query.edit_message_text("User rejected.")

# ---------------- MAIN MENU ---------------- #

async def show_main_menu(update):
    await update.message.reply_video(VIDEO_FILE_ID)

    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"scan_{m}")]
        for m in MERCHANTS.keys()
    ]

    await update.message.reply_text(
        "🎰 Welcome to MAXWIN AI RTP",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- SCAN ---------------- #

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    merchant = query.data.split("_")[1]

    now = int(time.time())

    if merchant in users[user_id]["cooldowns"]:
        last = users[user_id]["cooldowns"][merchant]
        if now - last < SCAN_COOLDOWN:
            remain = SCAN_COOLDOWN - (now - last)
            await query.edit_message_text(
                f"⛔ Cooldown active\nRemaining: {remain//60}m {remain%60}s"
            )
            return

    users[user_id]["cooldowns"][merchant] = now
    save_users()

    result = generate_rtp(merchant)

    msg = await query.edit_message_text(result)
    await countdown(msg, user_id, merchant)

def generate_rtp(merchant):
    platform = list(MERCHANTS[merchant].keys())[0]
    games = MERCHANTS[merchant][platform][:7]

    text = f"🔍 SCAN RESULT — {merchant}\n\n"
    for g in games:
        r = random.randint(40, 99)
        text += f"{g} — {r}%\n"

    text += "\n⚠️ Valid 15 minutes"
    return text

async def countdown(message, user_id, merchant):
    end = users[user_id]["cooldowns"][merchant] + SCAN_COOLDOWN

    while True:
        remain = end - int(time.time())
        if remain <= 0:
            await message.edit_text(message.text + "\n\n🟢 Scan Ready Again")
            break

        await message.edit_text(
            message.text.split("⏳")[0] +
            f"\n\n⏳ Next Scan In: {remain//60}m {remain%60}s"
        )
        await asyncio.sleep(1)

# ---------------- RUN ---------------- #

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(register_merchant, pattern="register_"))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="approve_|reject_"))
    app.add_handler(CallbackQueryHandler(scan, pattern="scan_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_account_id))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
