import json
import random
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import os

# ====== 配置 ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"

VIDEO_FILEID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

# ====== 初始化用户文件 ======
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

# ====== 商家链接 ======
MERCHANT_LINKS = {
    "CM8": "https://bit.ly/MaxWinCM8",
    "A9PLAY": "http://a9play5.com/R=F7464F",
    "ALD99": "https://bit.ly/ALDMaxWin",
    "U9PLAY": "https://u9play99.com/R=C8BAAC"
}

# ====== CM8游戏平台示例 ======
CM8_PLATFORMS = {
    "VPOWER": ["DolphinReef","Mahjong Ways 2","Triple Supreme Olympic","RAVE FEVER PARTY","Cash Machine","Starlight Princess","PIRATE BINGO","GOLDEN CENTURY","BAOZHUZHAOFU","Fortune Bowls","Battleground Royale","the crypt","FORTUNE OX","Fortune Mouse","King of Olympus","Super Golf Drive","Alchemy Gold","Fire Hot 5","Chin shi huang","The Knight King","Black-Myth: Wukong","BAOZHUZHAOCAI","Gold Pots","Lamp of Infinity","Fortune Tiger","Treasures of Aztec"],
    "HACKSAW": ["Stick'Em","OmNom","Miami Multiplier","Cubes","Cash Compass","The Respinners","Chaos Crew","Mystery Motel","Let It Snow","Cubes 2"],
    "LUCKY365": ["SuperAce Plus","Wisdom Athena 1000","Sweet Bonanza 1000","Ganesha Fortune","Wild Ape","Pinata Wins"],
    "ACE333": ["Luxury Cruise","Robin Hood","Gates Of Olympus","Twin Dragon Treasure","Eggs Of Gold","Buffalo Rush"],
    "CROCO GAMING": ["Super Waldo","Tim & Larry","Deadliest Sea","Wizard's Academy","Dragon Quest","John Wild"],
    "918Kiss": ["Pokémon","KingDerby","Motorbike","CarRacing","MonkeyStoryPlus"],
    "MEGA888": ["THUNDER BOLT","KING DERBY","MENMAID JEWELS","ANCIENT EGYPT","MOTORBIKE"],
    "MONKEY KING": ["ICELAND","GOD OF WEALTH","INDIAN MYTH","GREAT BLUE","THAI PARADISE"]
}

# ====== 临时存储 ======
pending_users = {}
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ====== 多语言文本 ======
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🔥 Welcome to MAXWIN AI RTP\n🤖 AI scans the highest RTP slot games\n📊 Click platform menu below to start",
        "choose_merchant": "Please select a merchant:",
        "register_prompt": "⚠️ Please register via official link:\nThen enter your account ID:",
        "share_contact": "📱 Please share your phone number",
        "wait_admin": "Please wait for Admin to approve your access.",
        "approved": "✅ Your account has been approved.\nSelect merchant:",
        "select_platform": "{merchant} - Please select a platform:",
        "scan_loading": ["Loading AI Engine...", "Calibrating volatility index...", "Syncing RTP Matrix...", "Analyzing slot volatility...", "Initializing RNG module..."],
        "back_text": "🔙 Back",
        "new_registration": "📥 NEW REGISTRATION REQUEST"
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🔥 欢迎来到 MAXWIN AI RTP\n🤖 AI 扫描 RTP 最高的 slot 游戏\n📊 点击平台菜单开始",
        "choose_merchant": "请选择商家：",
        "register_prompt": "⚠️ 请通过以下链接注册：\n注册后请输入账号ID：",
        "share_contact": "📱 请授权手机号",
        "wait_admin": "请等待 Admin 审核权限。",
        "approved": "✅ 审核通过 ✅\n请选择商家：",
        "select_platform": "{merchant} - 请选择游戏平台：",
        "scan_loading": ["加载 AI 引擎...","校准波动指数...","同步 RTP 矩阵...","分析老虎机波动率...","初始化随机模块..."],
        "back_text": "🔙 返回",
        "new_registration": "📥 新注册申请"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🔥 Selamat datang ke MAXWIN AI RTP\n🤖 AI yang scan RTP tertinggi dalam slot2\n📊 Tekan platform game menu di bawah untuk mula",
        "choose_merchant": "Sila pilih merchant:",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi:\nKemudian masukkan ID akaun:",
        "share_contact": "📱 Sila kongsi nombor telefon anda",
        "wait_admin": "Sila tunggu Admin meluluskan akses anda.",
        "approved": "✅ Akaun anda telah diluluskan.\nPilih merchant:",
        "select_platform": "{merchant} - Sila pilih platform:",
        "scan_loading": ["Loading AI Engine...","Kalibrasi indeks volatiliti...","Menyelaraskan RTP Matrix...","Menganalisis slot volatility...","Memulakan modul RNG..."],
        "back_text": "🔙 Kembali",
        "new_registration": "📥 NEW REGISTRATION REQUEST"
    }
}

# ====== 保存用户 ======
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_language.get(user_id, "en")
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        # 已批准用户直接显示欢迎 + 视频 + 商家
        await update.message.reply_video(
            video=VIDEO_FILEID,
            caption=TEXTS[lang]["welcome"],
            parse_mode="HTML"
        )
        await show_merchants(update, lang)
    else:
        # 未批准用户选择语言
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
    text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["choose_merchant"]
    await show_merchants(query, lang)

# ====== 显示商家 ======
async def show_merchants(obj, lang):
    keyboard = []
    for m in MERCHANT_LINKS.keys():
        keyboard.append([InlineKeyboardButton(m, callback_data=f"merchant_{m}")])
    # 可以注册按钮总在最底下
    keyboard.append([InlineKeyboardButton(TEXTS[lang]["back_text"], callback_data="back_lang")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if isinstance(obj, Update):
        await obj.message.reply_text(TEXTS[lang]["choose_merchant"], reply_markup=reply_markup)
    else:
        await obj.edit_message_text(TEXTS[lang]["choose_merchant"], reply_markup=reply_markup)

# ====== 商家选择 ======
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    merchant = query.data.split("_")[1]
    context.user_data["merchant"] = merchant

    # 如果用户未注册这个商家，显示注册按钮
    if str(user_id) not in users_data or merchant not in users_data[str(user_id)].get("registered_merchants", []):
        text = TEXTS[lang]["register_prompt"]
        register_button = InlineKeyboardButton("点击注册", url=MERCHANT_LINKS[merchant])
        keyboard = [[register_button], [InlineKeyboardButton(TEXTS[lang]["back_text"], callback_data="back_merchant")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    else:
        # 已注册商家直接显示平台
        await show_platforms(query, merchant, lang)

# ====== 平台显示 ======
async def show_platforms(query, merchant, lang):
    keyboard = []
    if merchant == "CM8":
        for p in CM8_PLATFORMS.keys():
            keyboard.append([InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")])
    else:
        # 默认PP/BNG/JILI/PG
        for p in ["PP","BNG","JILI","PG"]:
            keyboard.append([InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")])
    keyboard.append([InlineKeyboardButton(TEXTS[lang]["back_text"], callback_data=f"back_merchant")])
    text = TEXTS[lang]["select_platform"].format(merchant=merchant)
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== SCAN 游戏处理 ======
async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    _, merchant, platform = query.data.split("_")

    # 获取该平台的游戏
    if merchant == "CM8":
        games = CM8_PLATFORMS.get(platform, [])
    else:
        # 默认生成20个游戏
        games = [f"{platform}_Game_{i}" for i in range(1,21)]

    # 显示 loading 过程
    loading_messages = TEXTS[lang]["scan_loading"]
    msg = await query.edit_message_text("Initializing scan...")
    for i in range(1, 101, 20):
        loading_text = random.choice(loading_messages)
        bar = f"[{'■'* (i//10)}{'□'* (10 - i//10)}] {i}%"
        await msg.edit_text(f"{loading_text}\n{bar}")
        await asyncio.sleep(2)  # 每次2秒，总共10秒

    # 生成每个游戏25个随机RTP，展示部分信息
    result_lines = []
    hot_count = 0
    best_rtp = 0
    for game in games:
        rtp = round(random.uniform(30,98),2)
        if rtp < 70:
            icon = "🛑"
        elif rtp < 80:
            icon = "✅"
        elif rtp < 90:
            icon = "🔥"
            hot_count += 1
        else:
            icon = "🏆"
        best_rtp = max(best_rtp, rtp)
        result_lines.append(f"{icon} {game} — {rtp}%")

    scanned_count = len(games)
    now = datetime.now().strftime("%d %b %Y %H:%M")
    footer = f"━━━━━━━━━━━━━━━━━━\n📊 Scanned: {scanned_count}\n🔥 Hot: {hot_count}\n⚡ Best: {best_rtp}%\n🕒 {now}\n⚠️ Valid 15 minit sahaja"
    message = f"🔍 SCAN RESULT — {platform}\n━━━━━━━━━━━━━━━━━━\n" + "\n".join(result_lines) + "\n" + footer

    # 返回按钮
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back_text"], callback_data=f"merchant_{merchant}")]]
    await msg.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 返回键 ======
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")

    if query.data == "back_lang":
        keyboard = [
            [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
        ]
        await query.edit_message_text(TEXTS[lang]["choose_lang"], reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "back_merchant":
        await show_merchants(query, lang)
    elif query.data.startswith("merchant_"):
        merchant = query.data.split("_")[1]
        await show_platforms(query, merchant, lang)

# ====== 接收注册ID ======
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_language.get(user_id, "en")
    merchant = context.user_data.get("merchant")
    if not merchant:
        return
    account_id = update.message.text
    pending_users[user_id] = {"merchant": merchant, "account_id": account_id}
    contact_button = KeyboardButton(TEXTS[lang]["share_contact"], request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(TEXTS[lang]["share_contact"], reply_markup=reply_markup)

# ====== 接收手机号 ======
async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    lang = user_language.get(user.id, "en")
    pending_users[user.id]["phone"] = update.message.contact.phone_number
    pending_users[user.id]["approved"] = False
    users_data[str(user.id)] = pending_users[user.id]
    users_data[str(user.id)]["registered_merchants"] = [pending_users[user.id]["merchant"]]
    save_users()
    if ADMIN_ID != 0:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"{TEXTS[lang]['new_registration']}\n\n🆔 Application: MW-{datetime.now().strftime('%Y%m%d')}-xxxx\n👤 Username: @{user.username}\n📞 Phone: {pending_users[user.id]['phone']}\n🏢 Merchant: {pending_users[user.id]['merchant']}\n🎮 Game ID: {pending_users[user.id]['account_id']}\n🌐 Language: {lang}\n🕒 {datetime.now().strftime('%d %b %Y %H:%M')}\n\nApprove: /approve {user.id}"
        )
    await update.message.reply_text(TEXTS[lang]["wait_admin"])

# ====== Admin批准 ======
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) != 1:
        return
    user_id = int(context.args[0])
    if str(user_id) in users_data:
        users_data[str(user_id)]["approved"] = True
        save_users()
        lang = user_language.get(user_id, "en")
        await context.bot.send_message(chat_id=user_id, text=TEXTS[lang]["approved"])
        await update.message.reply_text(f"用户 {user_id} 已批准 ✅")

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(platform_handler, pattern="platform_"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="back_"))
    app.add_handler(MessageHandler(filters.CONTACT, receive_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id))
    app.add_handler(CommandHandler("approve", approve))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
