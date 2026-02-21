import json, random, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from data import CM8, A9PLAY, ALD99, U9PLAY, WELCOME_VIDEO_FILEID
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

pending_users = {}  # 临时存储注册ID等
user_language = {}  # TG_ID: 'en'/'zh'/'my'
pending_requests = {}  # app_id: user info

MERCHANT_LINKS = {
    "CM8": "https://bit.ly/MaxWinCM8",
    "A9PLAY": "http://a9play5.com/R=F7464F",
    "ALD99": "https://bit.ly/ALDMaxWin",
    "U9PLAY": "https://u9play99.com/R=C8BAAC"
}

PLATFORMS = ["PP","BNG","JILI","PG","VPOWER","MG","PT"]

TEXTS = {
    "en": {"choose_lang":"🌐 Please Select Language","welcome":"🎰 Welcome to MAXWIN AI RTP",
           "wait_admin":"⏳ Please wait for admin approval.","register_prompt":"⚠️ Register via official link & send ID:",
           "approved":"✅ Approved! Select merchant:","unregistered":"📊 Not registered on this merchant yet."},
    "zh": {"choose_lang":"请选择语言","welcome":"🎰 欢迎来到 MAXWIN AI RTP",
           "wait_admin":"⏳ 请等待管理员审批","register_prompt":"⚠️ 请通过商家注册链接注册并发送账号ID：",
           "approved":"✅ 审核通过！请选择商家：","unregistered":"📊 您尚未注册此商家，请点击“注册”继续。"},
    "my": {"choose_lang":"Sila Pilih Bahasa","welcome":"🎰 Selamat Datang ke MAXWIN AI RTP",
           "wait_admin":"⏳ Sila tunggu admin luluskan","register_prompt":"⚠️ Sila daftar melalui pautan rasmi dan hantar ID akaun:",
           "approved":"✅ Lulus! Pilih merchant:","unregistered":"📊 Boss masih belum mendaftar di platform ini. Klik 'Daftar' untuk meneruskan."}
}

def save_users():
    with open(USERS_FILE,"w") as f:
        json.dump(users_data,f)

def generate_app_id():
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    count = sum(1 for uid in users_data) + 1
    return f"MW-{date_str}-{count:04d}"

def get_merchant_games(merchant_name):
    mapping = {"CM8": CM8, "A9PLAY": A9PLAY, "ALD99": ALD99, "U9PLAY": U9PLAY}
    return mapping.get(merchant_name, {})

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) in users_data and not users_data[str(user_id)].get("approved"):
        lang = user_language.get(user_id,"en")
        await update.message.reply_text(TEXTS[lang]["wait_admin"])
        return
    lang = user_language.get(user_id,"en")
    keyboard = [[InlineKeyboardButton(m,callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS]
    keyboard.append([InlineKeyboardButton("🔘 Register New Merchant",callback_data="register_new")])
    await context.bot.send_video(chat_id=user_id, video=WELCOME_VIDEO_FILEID)
    await update.message.reply_text(TEXTS[lang]["welcome"],reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 语言选择 ======
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["approved"]
    keyboard = [[InlineKeyboardButton(m,callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 注册新商家 ======
async def register_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id,"en")
    keyboard = [[InlineKeyboardButton(m, callback_data=f"register_{m}")] for m in MERCHANT_LINKS]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_lang")])
    await query.edit_message_text("Select merchant to register:", reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 提交ID ======
async def register_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    merchant = query.data.split("_")[1]
    user_id = query.from_user.id
    lang = user_language.get(user_id,"en")
    pending_users[user_id] = {"merchant": merchant}
    contact_button = KeyboardButton("Share Phone", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await query.edit_message_text(TEXTS[lang]["register_prompt"], reply_markup=reply_markup)

# ====== 接收号码 ======
async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    contact = update.message.contact
    lang = user_language.get(user_id,"en")
    pending_users[user_id]["phone"] = contact.phone_number
    pending_users[user_id]["approved"] = False
    pending_users[user_id]["merchants"] = [pending_users[user_id]["merchant"]]
    users_data[str(user_id)] = pending_users[user_id]
    save_users()
    # 生成申请ID
    app_id = generate_app_id()
    pending_requests[app_id] = {"user_id": user_id, **pending_users[user_id]}
    # 发送给 Admin
    if ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{app_id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"reject_{app_id}")]
        ]
        msg_text = f"📥 NEW REGISTRATION REQUEST\n\n🆔 Application: {app_id}\n👤 Username: @{update.message.from_user.username}\n📞 Phone: {contact.phone_number}\n🏢 Merchant: {pending_users[user_id]['merchant']}\n🕒 {datetime.datetime.now().strftime('%d %b %Y %H:%M')}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg_text, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text(TEXTS[lang]["wait_admin"])

# ====== Admin Approve/Reject ======
async def admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, app_id = query.data.split("_")
    if app_id not in pending_requests:
        await query.edit_message_text("❌ Request expired or invalid.")
        return
    req = pending_requests[app_id]
    user_id = req["user_id"]
    lang = user_language.get(user_id,"en")
    if action == "approve":
        users_data[str(user_id)]["approved"] = True
        save_users()
        await context.bot.send_message(chat_id=user_id, text="✅ Your registration is approved!")
        await query.edit_message_text(query.message.text + "\n✅ Approved")
    else:
        users_data.pop(str(user_id), None)
        save_users()
        await context.bot.send_message(chat_id=user_id, text="❌ Your registration was rejected, please re-register.")
        await query.edit_message_text(query.message.text + "\n❌ Rejected")
    del pending_requests[app_id]

# ====== 返回 ======
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(register_new, pattern="register_new"))
    app.add_handler(CallbackQueryHandler(register_id, pattern="register_"))
    app.add_handler(MessageHandler(filters.CONTACT, receive_contact))
    app.add_handler(CallbackQueryHandler(admin_response, pattern="^(approve_|reject_).+"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="back_"))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
