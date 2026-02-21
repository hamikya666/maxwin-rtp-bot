import json
import os
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ===== 配置 =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

MERCHANTS = ["CM8", "A9PLAY", "ALD99", "U9PLAY"]

# ===== 初始化 =====
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

user_language = {}  # user_id -> 'en'/'zh'/'my'
pending_users = {}  # 临时存储新注册信息

# ===== 文本 =====
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🔥 Welcome to MAXWIN AI RTP\n🤖 AI scans highest RTP in slots",
        "pending_approval": "⏳ Waiting for Admin to approve your registration...",
        "not_registered": "📊 System detected you have not registered on this merchant.\nClick 'Register' below.",
        "register_prompt": "⚠️ Please provide your Account ID to register:",
        "reject_msg": "❌ Your registration has been rejected. Please re-register.",
        "new_request": "📥 NEW REGISTRATION REQUEST"
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🔥 欢迎使用 MAXWIN AI RTP\n🤖 AI 扫描最高 RTP 老虎机",
        "pending_approval": "⏳ 等待 Admin 审核您的注册...",
        "not_registered": "📊 系统检测您尚未在此商家注册。\n点击下方“注册”",
        "register_prompt": "⚠️ 请输入您的账户ID进行注册：",
        "reject_msg": "❌ 您的注册被拒绝，请重新注册。",
        "new_request": "📥 新用户注册申请"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🔥 Selamat datang ke MAXWIN AI RTP\n🤖 AI yang scan RTP tertinggi dalam slot",
        "pending_approval": "⏳ Menunggu Admin meluluskan pendaftaran anda...",
        "not_registered": "📊 Sistem mengesan bahawa bossku masih belum mendaftar di platform ini.\nBoss boleh klik 'Daftar' dalam direktori.",
        "register_prompt": "⚠️ Sila masukkan ID akaun anda untuk daftar:",
        "reject_msg": "❌ Pendaftaran anda telah ditolak. Sila daftar semula.",
        "new_request": "📥 PERMOHONAN PENDAFTARAN BARU"
    }
}

# ===== 保存 =====
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

# ===== 生成 MW 编号 =====
def generate_mw_id():
    today = datetime.now().strftime("%Y%m%d")
    count = sum(1 for u in users_data.values() if "mw_id" in u and u["mw_id"].startswith(today)) + 1
    return f"MW-{today}-{str(count).zfill(4)}"

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        lang = user_language.get(user_id, "en")
        await show_welcome_page(update, context, lang)
    else:
        keyboard = [
            [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
        ]
        await update.message.reply_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa",
                                        reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 语言选择 =====
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    await show_welcome_page(query, context, lang)

# ===== 欢迎页面 =====
async def show_welcome_page(update_or_query, context, lang):
    if isinstance(update_or_query, Update):
        chat_id = update_or_query.message.chat_id
    else:
        chat_id = update_or_query.message.chat_id
        await update_or_query.answer()
    user_id = update_or_query.from_user.id if isinstance(update_or_query, Update) else update_or_query.from_user.id

    # 视频
    if VIDEO_FILE_ID:
        await context.bot.send_video(chat_id=chat_id, video=VIDEO_FILE_ID)

    # 文本
    msg = TEXTS[lang]["welcome"]
    await context.bot.send_message(chat_id=chat_id, text=msg)

    # 商家按钮
    merchant_buttons = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANTS]
    merchant_buttons.append([InlineKeyboardButton("Register", callback_data="register")])
    reply_markup = InlineKeyboardMarkup(merchant_buttons)
    await context.bot.send_message(chat_id=chat_id, text="Select Merchant / Pilih Merchant",
                                   reply_markup=reply_markup)

# ===== 点击商家 =====
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    merchant = query.data.split("_")[1]
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    user_info = users_data.get(str(user_id), {})

    # 是否已注册当前商家
    if user_info.get("approved") and merchant in user_info.get("merchants", []):
        msg = f"✅ You are registered on {merchant}.\nYou can use Scan."
    elif user_info.get("approved") and merchant not in user_info.get("merchants", []):
        msg = TEXTS[lang]["not_registered"]
    else:
        msg = TEXTS[lang]["register_prompt"]

    keyboard = [[InlineKeyboardButton("Scan", callback_data=f"scan_{merchant}")]]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_welcome")])
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 注册 =====
async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    buttons = [[InlineKeyboardButton(m, callback_data=f"register_{m}")] for m in MERCHANTS]
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_welcome")])
    await query.edit_message_text("Select merchant to register:", reply_markup=InlineKeyboardMarkup(buttons))

# ===== 提供 ID =====
async def provide_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    merchant = context.user_data.get("register_merchant")
    if not merchant:
        return

    mw_id = generate_mw_id()
    pending_users[user_id] = {
        "username": update.message.from_user.username or update.message.from_user.full_name,
        "merchant": merchant,
        "account_id": text,
        "time": datetime.now().strftime("%d %b %Y %H:%M"),
        "mw_id": mw_id,
        "language": user_language.get(user_id, "en")
    }

    # 通知 Admin
    if ADMIN_ID != 0:
        msg = (
            f"📥 NEW REGISTRATION REQUEST\n\n"
            f"🆔 Application: {mw_id}\n"
            f"👤 Username: @{pending_users[user_id]['username']}\n"
            f"🏢 Merchant: {merchant}\n"
            f"🎮 Game ID: {text}\n"
            f"🌐 Language: {pending_users[user_id]['language']}\n"
            f"🕒 {pending_users[user_id]['time']}\n\n"
            f"Approve: /approve {user_id}\n"
            f"Reject: /reject {user_id}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    await update.message.reply_text(TEXTS[user_language.get(user_id, "en")]["pending_approval"])

# ===== Admin approve =====
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) != 1:
        return
    user_id = int(context.args[0])
    if user_id in pending_users:
        user_info = users_data.get(str(user_id), {"merchants": []})
        merchant = pending_users[user_id]["merchant"]
        user_info["merchants"].append(merchant)
        user_info["approved"] = True
        user_info["mw_id"] = pending_users[user_id]["mw_id"]
        users_data[str(user_id)] = user_info
        save_users()
        lang = user_language.get(user_id, "en")
        await context.bot.send_message(chat_id=user_id,
                                       text=f"✅ Approved! You can now use Scan on {merchant}.")
        await update.message.reply_text(f"User {user_id} approved ✅")
        del pending_users[user_id]

# ===== Admin reject =====
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) != 1:
        return
    user_id = int(context.args[0])
    if user_id in pending_users:
        lang = user_language.get(user_id, "en")
        await context.bot.send_message(chat_id=user_id, text=TEXTS[lang]["reject_msg"])
        await update.message.reply_text(f"User {user_id} rejected ❌")
        del pending_users[user_id]

# ===== 返回键 =====
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = user_language.get(query.from_user.id, "en")
    await show_welcome_page(query, context, lang)

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(register_handler, pattern="register$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, provide_id))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="back_"))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
