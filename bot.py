import json
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from data import MERCHANTS

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

pending_users = {}
user_language = {}

TEXTS = {
    "en": {"choose_lang": "🌐 Please Select Language", "welcome": "🎰 Welcome to MaxWin AI RTP", "wait_admin": "Please wait for Admin approval."},
    "zh": {"choose_lang": "请选择语言", "welcome": "🎰 欢迎来到 MaxWin AI RTP", "wait_admin": "请等待 Admin 审核权限。"},
    "my": {"choose_lang": "Sila Pilih Bahasa", "welcome": "🎰 Selamat Datang ke MaxWin AI RTP", "wait_admin": "Sila tunggu Admin meluluskan akses anda."}
}

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_language.get(user_id)
    
    if str(user_id) in users_data:
        if users_data[str(user_id)].get("approved"):
            # 已注册且已Approve
            await send_main_menu(update, lang)
            return
        else:
            # 已注册但未Approve
            lang = users_data[str(user_id)].get("language", "en")
            await update.message.reply_text(TEXTS[lang]["wait_admin"])
            return
    
    # 新用户，选择语言
    keyboard = [
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=reply_markup)

# ====== 语言选择 ======
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    await show_merchants(query, lang)

async def show_merchants(query, lang):
    keyboard = [[InlineKeyboardButton(m, callback_data=f"register_{m}")] for m in MERCHANTS.keys()]
    await query.edit_message_text(TEXTS[lang]["choose_lang"], reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 注册流程 ======
async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    merchant = query.data.split("_")[1]
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    
    # 显示注册链接
    url_button = InlineKeyboardButton("点击注册", url=f"https://example.com/{merchant}")
    back_button = InlineKeyboardButton("🔙 返回商家选择", callback_data="back_merchants")
    keyboard = [[url_button], [back_button]]
    await query.edit_message_text(f"请通过以下链接注册 {merchant}", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # 标记用户待提交ID
    pending_users[user_id] = {"merchant": merchant, "lang": lang}

async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in pending_users:
        return
    account_id = update.message.text
    pending_users[user_id]["account_id"] = account_id
    pending_users[user_id]["phone"] = None  # 如果需要 share phone 可以加
    pending_users[user_id]["approved"] = False
    users_data[str(user_id)] = pending_users[user_id]
    save_users()
    
    # 发给Admin
    if ADMIN_ID != 0:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 NEW REGISTRATION REQUEST\n\n"
                 f"🆔 Application: MW-20260221-0001\n"
                 f"👤 Username: @{update.message.from_user.username}\n"
                 f"🏢 Merchant: {pending_users[user_id]['merchant']}\n"
                 f"🎮 Game ID: {pending_users[user_id]['account_id']}\n"
                 f"🌐 Language: {pending_users[user_id]['lang']}"
        )
    await update.message.reply_text(TEXTS[pending_users[user_id]['lang']]["wait_admin"])

# ====== 主菜单 ======
async def send_main_menu(update, lang=None):
    if lang is None:
        lang = "en"
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
    # 发送视频
    await update.message.reply_video(VIDEO_FILE_ID)
    # 发送欢迎文本
    await update.message.reply_text(TEXTS[lang]["welcome"])
    # 商家按钮
    keyboard = [[InlineKeyboardButton(m, callback_data=f"scan_{m}")] for m in MERCHANTS.keys()]
    await update.message.reply_text("请选择商家", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 回调返回键 ======
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    await show_merchants(query, lang)

# ====== 主 ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(register_handler, pattern="register_"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="back_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))
    
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
