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
VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

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

# ====== CM8 平台和游戏 ======
CM8_PLATFORMS = {
    "VPOWER": [
        "DolphinReef", "Mahjong Ways 2", "Triple Supreme Olympic", "RAVE FEVER PARTY", "Cash Machine",
        "Starlight Princess", "PIRATE BINGO", "GOLDEN CENTURY", "BAOZHUZHAOFU", "Fortune Bowls",
        "Battleground Royale", "The Crypt", "FORTUNE OX", "Fortune Mouse", "King of Olympus",
        "Super Golf Drive", "Alchemy Gold", "Fire Hot 5", "Chin shi huang", "The Knight King",
        "Black-Myth: Wukong", "BAOZHUZHAOCAI", "Gold Pots", "Lamp of Infinity", "Fortune Tiger",
        "Treasures of Aztec", "ZhaoCaiJinBao", "Eyes of Fortune", "Magic Pearl", "Alice"
    ],
    "HACKSAW": [
        "Stick'Em", "OmNom", "Miami Multiplier", "Cubes", "Cash Compass", "The Respinners",
        "Chaos Crew", "Mystery Motel", "Let It Snow", "Cubes 2", "Aztec Twist"
    ],
    # 继续填充其他 CM8 平台游戏
}

# ====== 新增大供应商示例 ======
NEW_SUPPLIERS = {
    "NOLIMITCITY": ["Game A", "Game B", "Game C"],
    "IN&OUT": ["Game D", "Game E"],
    "GFG": ["Game F", "Game G"],
    "JDB": ["Game H", "Game I"],
    "FASTSPIN": ["Game J", "Game K"],
    "BETSOFT": ["Game L", "Game M"],
    "PLAYTECH": ["Game N", "Game O"],
    "ADVANTPLAY": ["Game P", "Game Q"],
    "GAMZIX": ["Game R", "Game S"],
    "WOW GAMING": ["Game T", "Game U"],
    "SIMPLEPLAY": ["Game V", "Game W"],
    "RECTANGLE GAME": ["Game X", "Game Y"],
    "PEGASUS": ["Game Z"],
    "UU": ["Game AA"],
    "VPLUS": ["Game BB", "Game CC"]
}

# 合并所有平台
PLATFORMS_GAMES = {**CM8_PLATFORMS, **NEW_SUPPLIERS}

# ====== 临时存储 ======
pending_users = {}
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ====== 语言文本 ======
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🎰 Welcome to MAXWIN Official RTP Bot",
        "choose_merchant": "Please select a merchant:",
        "register_prompt": "⚠️ Please register via official link:\nThen enter your account ID:",
        "share_contact": "📱 Please share your phone number",
        "wait_admin": "Please wait for Admin to approve your access.",
        "approved": "✅ Your account has been approved.\nSelect merchant:",
        "select_platform": "{merchant} - Please select a platform:",
        "rtp_top": "{merchant} - {platform} RTP Scan Result:\n"
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🎰 欢迎来到 MAXWIN 官方 RTP 机器人",
        "choose_merchant": "请选择商家：",
        "register_prompt": "⚠️ 请通过以下链接注册：\n注册后请输入账号ID：",
        "share_contact": "📱 请授权手机号",
        "wait_admin": "请等待 Admin 审核权限。",
        "approved": "✅ 审核通过 ✅\n请选择商家：",
        "select_platform": "{merchant} - 请选择游戏平台：",
        "rtp_top": "{merchant} - {platform} RTP 扫描结果:\n"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🎰 Selamat Datang ke MAXWIN RTP Bot Rasmi",
        "choose_merchant": "Sila pilih merchant:",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi:\nKemudian masukkan ID akaun:",
        "share_contact": "📱 Sila kongsi nombor telefon anda",
        "wait_admin": "Sila tunggu Admin meluluskan akses anda.",
        "approved": "✅ Akaun anda telah diluluskan.\nPilih merchant:",
        "select_platform": "{merchant} - Sila pilih platform:",
        "rtp_top": "{merchant} - {platform} Hasil Scan RTP:\n"
    }
}

# ====== 保存用户 ======
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f)

# ====== /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_language.get(user_id, "en")
    
    # 如果已经approve过
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        # 发送视频
        await context.bot.send_video(chat_id=user_id, video=VIDEO_FILE_ID)
        # 显示 approve 欢迎信息 + 商家注册按钮
        text = ""
        if lang == "zh":
            text = "🔥 欢迎来到 MAXWIN AI RTP\n🤖 AI 扫描最高 RTP 的游戏\n📊 点击下方平台菜单开始"
        elif lang == "my":
            text = "🔥 Selamat datang ke MAXWIN AI RTP\n🤖 AI yang scan RTP tertinggi dalam slot2\n📊 Tekan platform game menu di bawah untuk mula"
        else:
            text = "🔥 Welcome to MAXWIN AI RTP\n🤖 AI scans the highest RTP games\n📊 Press platform menu below to start"

        await show_merchants_text(update, context, text)
        return

    # 第一次 start，选择语言
    keyboard = [
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # 发送视频
    await context.bot.send_video(chat_id=user_id, video=VIDEO_FILE_ID)
    await update.message.reply_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=reply_markup)

# ====== 语言选择 ======
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["choose_merchant"]
    await show_merchants_text(query, context, text)

# ====== 显示商家 ======
async def show_merchants_text(query, context, text):
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
    keyboard.append([InlineKeyboardButton("🔙 返回语言选择", callback_data="back_lang")])
    if isinstance(query, Update):  # 来自 /start
        await query.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:  # callback query
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 商家选择 ======
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    merchant = query.data.split("_")[1]
    context.user_data["merchant"] = merchant
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        text = TEXTS[lang]["select_platform"].format(merchant=merchant)
        await show_platforms(query, merchant, lang, text)
    else:
        text = TEXTS[lang]["register_prompt"]
        register_button = InlineKeyboardButton("点击注册", url=MERCHANT_LINKS[merchant])
        keyboard = [[register_button], [InlineKeyboardButton("🔙 返回商家选择", callback_data="back_merchant")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

# ====== 接收注册ID ======
async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    merchant = context.user_data.get("merchant")
    lang = user_language.get(user_id, "en")
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
    contact = update.message.contact
    pending_users[user.id]["phone"] = contact.phone_number
    pending_users[user.id]["approved"] = False
    users_data[str(user.id)] = pending_users[user.id]
    save_users()
    if ADMIN_ID != 0:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 NEW REGISTRATION REQUEST\n\n🆔 Application: MW-{datetime.now().strftime('%Y%m%d-%H%M')}\n"
                 f"👤 Username: @{user.username}\n📞 Phone: {contact.phone_number}\n🏢 Merchant: {pending_users[user.id]['merchant']}\n"
                 f"🎮 Game ID: {pending_users[user.id]['account_id']}\n🌐 Language: {lang}\n🕒 {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
                 f"Approve: /approve {user.id}"
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
        # 发送欢迎 + 商家选择
        text = ""
        if lang == "zh":
            text = "🔥 欢迎来到 MAXWIN AI RTP\n🤖 AI 扫描最高 RTP 的游戏\n📊 点击下方平台菜单开始"
        elif lang == "my":
            text = "🔥 Selamat datang ke MAXWIN AI RTP\n🤖 AI yang scan RTP tertinggi dalam slot2\n📊 Tekan platform game menu di bawah untuk mula"
        else:
            text = "🔥 Welcome to MAXWIN AI RTP\n🤖 AI scans the highest RTP games\n📊 Press platform menu below to start"
        await context.bot.send_video(chat_id=user_id, video=VIDEO_FILE_ID)
        # 显示商家选择
        await show_merchants_text(update, context, text)
        await update.message.reply_text(f"用户 {user_id} 已批准 ✅")

# ====== 平台显示 ======
async def show_platforms(query, merchant, lang, text):
    keyboard = [[InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")] for p in PLATFORMS_GAMES.keys()]
    keyboard.append([InlineKeyboardButton("🔙 返回商家选择", callback_data="back_merchant")])
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 游戏RTP显示 ======
async def platform_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id, "en")
    _, merchant, platform = query.data.split("_")
    games = PLATFORMS_GAMES.get(platform, [])

    # 发送 loading 动画
    loading_steps = [
        "Loading AI Engine...",
        "Calibrating volatility index...",
        "Syncing RTP Matrix...",
        "Optimizing slot RNG...",
        "Finalizing RTP data..."
    ]
    msg = await query.edit_message_text("Starting scan...")
    for i, step in enumerate(loading_steps, 1):
        percent = int(i / len(loading_steps) * 100)
        bar = "■" * (percent // 10) + "□" * (10 - percent // 10)
        await msg.edit_text(f"{step} [{bar}] {percent}%")
        await asyncio.sleep(2)  # 模拟加载

    # 生成每个游戏随机25个RTP
    game_rtp_text = f"🔍 SCAN RESULT — {platform}\n━━━━━━━━━━━━━━━━━━\n"
    game_rtp_text += f"👤 {merchant} | 🆔 账户ID\n━━━━━━━━━━━━━━━━━━\n"
    for game in games:
        rtp = round(random.uniform(30, 98), 2)
        if 40 <= rtp <= 69:
            icon = "🛑"
        elif 70 <= rtp <= 79:
            icon = "✅"
        elif 80 <= rtp <= 89:
            icon = "🔥"
        else:
            icon = "🏆"
        game_rtp_text += f"{icon} {game} — {rtp}%\n"

    # 扫描统计
    total_scanned = len(games)
    hot_count = sum(1 for game in games if 80 <= round(random.uniform(30,98),2) <= 89)
    best_rtp = max(round(random.uniform(30, 98),2) for _ in games)
    game_rtp_text += "━━━━━━━━━━━━━━━━━━\n"
    game_rtp_text += f"📊 Scanned: {total_scanned} | 🔥 Hot: {hot_count} | ⚡ Best: {best_rtp}%\n"
    game_rtp_text += f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}\n⚠️ Valid 15 minit sahaja"

    # 返回按钮
    keyboard = [[InlineKeyboardButton("🔙 返回平台选择", callback_data=f"merchant_{merchant}")]]
    await msg.edit_text(game_rtp_text, reply_markup=InlineKeyboardMarkup(keyboard))

# ====== 返回按钮 ======
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
        await query.edit_message_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "back_merchant":
        text = TEXTS[lang]["choose_merchant"]
        keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
        keyboard.append([InlineKeyboardButton("🔙 返回语言选择", callback_data="back_lang")])
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

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
