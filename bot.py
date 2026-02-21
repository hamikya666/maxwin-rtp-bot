import json
import random
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ====== 配置 ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"

# ====== 数据导入 ======
from data import MERCHANTS  # data/__init__.py 管理所有商家和平台

# ====== 初始化用户文件 ======
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)
with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

# ====== 临时存储 ======
pending_users = {}
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ====== 视频 FileID ======
WELCOME_VIDEO_FILEID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

# ====== 语言文本 ======
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🎰 Welcome to MAXWIN AI RTP",
        "waiting_approval": "⏳ Please wait for Admin to approve your account.",
        "not_registered_scan": "📊 System detected you have not registered this merchant. Click 'Register' to proceed.",
        "approved": "✅ Your account has been approved!",
        "rejected": "❌ Your registration was rejected. Please register again."
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🎰 欢迎使用 MAXWIN AI RTP",
        "waiting_approval": "⏳ 请等待管理员批准您的账户。",
        "not_registered_scan": "📊 系统检测您尚未注册此商家，请点击“注册”进行注册。",
        "approved": "✅ 您的账户已通过审核！",
        "rejected": "❌ 您的注册被拒绝，请重新注册。"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🎰 Selamat datang ke MAXWIN AI RTP",
        "waiting_approval": "⏳ Sila tunggu Admin meluluskan akaun anda.",
        "not_registered_scan": "📊 Sistem mengesan anda belum mendaftar merchant ini. Tekan 'Daftar' untuk mendaftar.",
        "approved": "✅ Akaun anda telah diluluskan!",
        "rejected": "❌ Pendaftaran anda ditolak, sila daftar semula."
    }
}

# ====== 保存用户 ======
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_language.get(user_id)
    
    # 已注册但未审批
    if str(user_id) in users_data and not users_data[str(user_id)].get("approved"):
        await update.message.reply_text(TEXTS[lang]["waiting_approval"])
        return
    
    # 已注册并批准
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        # 发送欢迎视频 + 文本 + 商家按钮 + 注册按钮
        await update.message.reply_video(
            WELCOME_VIDEO_FILEID,
            caption=TEXTS[lang]["welcome"]
        )
        keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANTS.keys()]
        keyboard.append([InlineKeyboardButton("🔄 Register Another Merchant", callback_data="register")])
        await update.message.reply_text("Select merchant or register another:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # 未注册用户显示语言选择
    keyboard = [
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
    ]
    await update.message.reply_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 语言选择 ======
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    
    # 显示商家注册按钮
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANTS.keys()]
    await query.edit_message_text(TEXTS[lang]["welcome"], reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 商家点击处理 ======
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    merchant = query.data.split("_")[1]
    
    # 判断是否已经注册该商家
    user_data = users_data.get(str(user_id))
    if user_data and merchant in user_data.get("merchants", {}):
        # 已注册
        keyboard = [[InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")] for p in MERCHANTS[merchant].keys()]
        await query.edit_message_text(f"{merchant} - Select Platform", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # 未注册显示注册文本 + 注册按钮
        keyboard = [[InlineKeyboardButton("Register", callback_data=f"register_{merchant}")]]
        await query.edit_message_text(TEXTS[lang]["not_registered_scan"], reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 注册商家处理 ======
async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    merchant = query.data.split("_")[1]
    
    # 提示提供账户ID
    pending_users[user_id] = {"merchant": merchant}
    await query.edit_message_text(f"Please send your account ID for {merchant}:")

# ====== 接收账户ID ======
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    if user_id not in pending_users:
        return
    merchant = pending_users[user_id]["merchant"]
    
    # 保存账户ID并标记等待Admin
    pending_users[user_id]["account_id"] = text
    pending_users[user_id]["approved"] = False
    users_data.setdefault(str(user_id), {"merchants": {}})
    users_data[str(user_id)]["merchants"][merchant] = pending_users[user_id]
    save_users()
    
    # 发送给Admin
    if ADMIN_ID:
        timestamp = datetime.now().strftime("%d %b %Y %H:%M")
        app_no = f"MW-{datetime.now().strftime('%Y%m%d')}-{len(users_data):04d}"
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 NEW REGISTRATION REQUEST\n\n🆔 Application: {app_no}\n👤 Username: @{update.message.from_user.username}\n🏢 Merchant: {merchant}\n🎮 Game ID: {text}\n🌐 Language: {user_language.get(user_id)}\n🕒 {timestamp}\n\nApprove: /approve {user_id}\nReject: /reject {user_id}"
        )
    await update.message.reply_text(TEXTS[user_language[user_id]]["waiting_approval"])

# ====== Admin Approve / Reject ======
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    user_id = str(context.args[0])
    if user_id in users_data:
        for merchant in users_data[user_id]["merchants"]:
            users_data[user_id]["merchants"][merchant]["approved"] = True
        save_users()
        lang = user_language.get(int(user_id), "en")
        await context.bot.send_message(chat_id=user_id, text=TEXTS[lang]["approved"])
        await update.message.reply_text(f"User {user_id} approved ✅")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    user_id = str(context.args[0])
    if user_id in users_data:
        for merchant in users_data[user_id]["merchants"]:
            users_data[user_id]["merchants"][merchant]["approved"] = False
        save_users()
        lang = user_language.get(int(user_id), "en")
        await context.bot.send_message(chat_id=user_id, text=TEXTS[lang]["rejected"])
        await update.message.reply_text(f"User {user_id} rejected ❌")

# ====== 平台点击处理 (Scan) ======
async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    _, merchant, platform = query.data.split("_")
    
    # 模拟Loading
    loading_texts = ["Loading AI Engine...", "Calibrating volatility index...", "Syncing RTP Matrix..."]
    for i, text in enumerate(loading_texts, 1):
        await query.edit_message_text(f"{text} [■{'□'* (10*i//len(loading_texts))}]{i*33}%")
    
    # 随机生成RTP 25个游戏
    games = MERCHANTS[merchant][platform]
    rtp_list = [(g, round(random.uniform(30, 98), 2)) for g in games]
    message = f"🔍 SCAN RESULT — {platform}\n━━━━━━━━\n"
    for game, rtp in rtp_list:
        if rtp < 70:
            icon = "🛑"
        elif rtp < 80:
            icon = "✅"
        elif rtp < 90:
            icon = "🔥"
        else:
            icon = "🏆"
        message += f"{icon} {game} — {rtp}%\n"
    await query.edit_message_text(message)

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(register_handler, pattern="register_"))
    app.add_handler(CallbackQueryHandler(platform_handler, pattern="platform_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
