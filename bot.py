import json
import random
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import os

# ===== 配置 =====
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "YOUR_BOT_TOKEN"
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"  # 替换你的file_id
USERS_FILE = "users.json"

# ===== 导入商家和游戏平台 =====
from data import MERCHANTS  # data/__init__.py管理所有商家和平台

# ===== 初始化用户数据 =====
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

pending_users = {}  # 临时存储ID注册信息
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ===== 文本 =====
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🎰 Welcome to MAXWIN AI RTP",
        "select_merchant": "Please select a merchant:",
        "wait_admin": "⏳ Waiting for Admin approval...",
        "register_prompt": "⚠️ Please register via official link and provide your account ID:",
        "unregistered_scan": "🔥 Welcome to MAXWIN AI RTP\n🤖 AI scanning top RTP slots\n📊 You have not registered this merchant yet. Click 'Register' to proceed."
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🎰 欢迎来到 MAXWIN AI RTP",
        "select_merchant": "请选择商家：",
        "wait_admin": "⏳ 请等待 Admin 审核权限...",
        "register_prompt": "⚠️ 请通过以下链接注册并提供账号ID：",
        "unregistered_scan": "🔥 欢迎来到MAXWIN AI RTP\n🤖 AI扫描最高RTP老虎机\n📊 您尚未注册该商家，请点击“注册”。"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🎰 Selamat Datang ke MAXWIN AI RTP",
        "select_merchant": "Sila pilih merchant:",
        "wait_admin": "⏳ Sila tunggu Admin meluluskan akses anda.",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi dan masukkan ID akaun anda:",
        "unregistered_scan": "🔥 Selamat datang ke MAXWIN AI RTP\n🤖 AI yang scan RTP tertinggi dalam slot\n📊 Sistem mengesan bahawa bossku masih belum mendaftar di platform ini. Klik 'Daftar' untuk mendaftar."
    }
}

# ===== 保存 =====
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=2)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        lang = user_language.get(user_id, "en")
        await show_main_menu(update, lang)
        return

    # 新用户或未注册用户
    keyboard = [
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=reply_markup)

# ===== 语言选择 =====
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["select_merchant"]
    await show_merchants(query, text, lang)

# ===== 显示商家按钮 =====
async def show_merchants(query, text, lang):
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANTS.keys()]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 商家注册 =====
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    merchant = query.data.split("_")[1]
    context.user_data["merchant"] = merchant
    lang = user_language.get(user_id, "en")

    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        # 已注册过任何商家
        await show_scan_page(query, merchant, lang)
    else:
        # 未注册
        register_button = InlineKeyboardButton("Register", callback_data=f"register_{merchant}")
        keyboard = [[register_button]]
        await query.edit_message_text(TEXTS[lang]["register_prompt"], reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 注册流程 =====
async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    merchant = query.data.split("_")[1]
    user_id = query.from_user.id
    context.user_data["merchant"] = merchant
    await query.edit_message_text(f"Please provide your account ID for {merchant}")

# ===== 接收账户ID =====
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    merchant = context.user_data.get("merchant")
    if not merchant:
        return
    account_id = update.message.text
    pending_users[user_id] = {"merchant": merchant, "account_id": account_id, "approved": False, "time": datetime.datetime.now().isoformat()}
    users_data[str(user_id)] = pending_users[user_id]
    save_users()
    # 发给admin
    if ADMIN_ID:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 NEW REGISTRATION REQUEST\n\n🆔 Application: MW-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}\n👤 Username: @{update.message.from_user.username}\n🏢 Merchant: {merchant}\n🎮 Game ID: {account_id}\n🕒 {datetime.datetime.now().strftime('%d %b %Y %H:%M')}\n\nApprove: /approve {user_id}  Reject: /reject {user_id}"
        )
    lang = user_language.get(user_id, "en")
    await update.message.reply_text(TEXTS[lang]["wait_admin"])

# ===== Admin approve =====
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    user_id = context.args[0]
    if str(user_id) in users_data:
        users_data[str(user_id)]["approved"] = True
        save_users()
        lang = user_language.get(int(user_id), "en")
        await context.bot.send_message(chat_id=int(user_id), text="✅ Your registration has been approved!")
        await update.message.reply_text(f"User {user_id} approved ✅")

# ===== Admin reject =====
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    user_id = context.args[0]
    if str(user_id) in users_data:
        users_data.pop(str(user_id))
        save_users()
        await context.bot.send_message(chat_id=int(user_id), text="❌ Your registration was rejected. Please register again.")
        await update.message.reply_text(f"User {user_id} rejected ❌")

# ===== 显示 scan 页面 =====
async def show_scan_page(query, merchant, lang):
    text = TEXTS[lang]["unregistered_scan"]
    # 发送视频
    await query.message.reply_video(VIDEO_FILE_ID)
    scan_button = InlineKeyboardButton("Scan", callback_data=f"scan_{merchant}")
    register_button = InlineKeyboardButton("Register", callback_data="show_register")
    keyboard = [[scan_button], [register_button]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== MAIN MENU 显示给已注册用户 =====
async def show_main_menu(update, lang):
    text = TEXTS[lang]["welcome"]
    keyboard = [
        [InlineKeyboardButton(m, callback_data=f"merchant_{m}") for m in MERCHANTS.keys()],
        [InlineKeyboardButton("Scan", callback_data="scan_main"), InlineKeyboardButton("Register", callback_data="show_register")]
    ]
    await update.message.reply_video(VIDEO_FILE_ID)
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 主 =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(register_handler, pattern="register_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
