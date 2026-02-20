import json
import random
import asyncio
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InputMediaVideo
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
)
import os

# ===== 配置 =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"

VIDEO_FILE_ID = "BAACAgUAAxkBAAJ682mYXMwrOUSatmP8ROjQJcx6vtw9AAI1HAACd5HBVPGdMpbcTHcZOgQ"

# ===== 初始化用户数据 =====
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

with open(USERS_FILE, "r") as f:
    users_data = json.load(f)

# ===== 商家链接 =====
MERCHANT_LINKS = {
    "CM8": "https://bit.ly/MaxWinCM8",
    "A9PLAY": "http://a9play5.com/R=F7464F",
    "ALD99": "https://bit.ly/ALDMaxWin",
    "U9PLAY": "https://u9play99.com/R=C8BAAC"
}

# ===== CM8 平台 & 游戏示例 =====
PLATFORMS_GAMES = {
    "VPOWER": ["DolphinReef","Mahjong Ways 2","Triple Supreme Olympic(new)","RAVE FEVER PARTY","Cash Machine","Starlight Princess","PIRATE BINGO","GOLDEN CENTURY","BAOZHUZHAOFU","Fortune Bowls","Battleground Royale","the crypt","FORTUNE OX","Fortune Mouse","King of Olympus","Super Golf Drive","Alchemy Gold","Fire Hot 5","Chin shi huang","The Knight King","Black-Myth: Wukong","BAOZHUZHAOCAI","Gold Pots","Lamp of Infinity","Fortune Tiger","Treasures of Aztec","ZhaoCaiJinBao","Eyes of Fortune","Magic Pearl","Alice","Joyful Lantern","Draon's Treasure","OCEAN PARTY","prosperous lions","PandaMagic","crown of fire","Crazy Restaurant","God Of Wealth","Best Bet","GreatBlue","Mystery of the Orient","Golden Rooste","Buffalo Gold","HighWay","BonusBears","SAFARI Heat","Thai","Water Margin","PantherMoon","JinQianWa","SeaWorld","BoyKing","ICELAND","Boxing","Golden Tour","Victory","Fairy Garden","Irish Luck","Dragon","Samurai","Top Gun","T-REX","India","Panda","Captain","JAPAN","Fruit","FengShen","FortunePanda","Fashion","FORTUNE","Rally","Easter","Wealth","Dragon Gold","GoldenTree","RobinHood","StoneAge","Prosperity","Three Kingdoms","Amazon","BigShot","PayDirt","SeaCaptain","AfricanWildlife","Seasons","Laura","Pirate","CookiePop","Circus","Tally Ho","Orient","Fame","Cleopatra","Twister","Girls","EmperorGate","WildFox","NvXia","Long Teng Hu Xiao","5 fortune dragon","Archer","Life of luxury II","Wild Elements","Peace&Long Life","Fire of rue royale","Fire of riverside","Mr.Fido","CHICKEN DINNER","PYRAMID ADVENTURE","WILD BUFFALO","LUCKY FORTUNE","HOT WHEELS","Runaway","TIS THE SEASON","Long Teng Hu Xiao 2","Wild Chuco","Mysterious Witch","Cash Spark","Indihn Dkehming","5 Kings","GOLD BONANZA","MAGIC TOTEM","DRAGON CITY","sea Realms","888888","Brothers Kingdom","FaFaFa 2","Fire Of Glacier Gold","Fire Of Route 66","Fire Of Villa Street","Glorious Rome","Mystery Reels","Sahara Gold","Silver Bullet","Sweet Bakery","Sweet Bonanza XMAS"] 
    # 其他平台可类似添加
}

MERCHANT_PLATFORMS = {
    "CM8": list(PLATFORMS_GAMES.keys()),
    "A9PLAY": list(PLATFORMS_GAMES.keys()),
    "ALD99": list(PLATFORMS_GAMES.keys()),
    "U9PLAY": list(PLATFORMS_GAMES.keys())
}

# ===== 临时存储 =====
pending_users = {}
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ===== 语言文本 =====
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🎰 Welcome to MAXWIN AI RTP",
        "merchant_info": "🤖 AI scans highest RTP in slots\n📊 Tap merchant below to start",
        "register_prompt": "⚠️ Please register via official link:\nThen enter your account ID:",
        "share_contact": "📱 Please share your phone number",
        "wait_admin": "Please wait for Admin to approve your access.",
        "approved": "✅ Your account has been approved!",
        "select_platform": "{merchant} - Please select a platform:",
        "scan_loading": ["Loading AI Engine...","Calibrating volatility index...","Syncing RTP Matrix...","Analyzing slot volatility...","Initializing RNG module..."],
        "scan_footer": "📊 Scanned: {scanned} | 🔥 Hot: {hot} | ⚡ Best: {best}%\n🕒 {time}\n⚠️ Valid 15 min only"
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🎰 欢迎来到 MAXWIN AI RTP",
        "merchant_info": "🤖 AI扫描最高RTP的老虎机\n📊 点击下面商家开始",
        "register_prompt": "⚠️ 请通过以下链接注册：\n注册后请输入账号ID：",
        "share_contact": "📱 请授权手机号",
        "wait_admin": "请等待 Admin 审核权限。",
        "approved": "✅ 审核通过！",
        "select_platform": "{merchant} - 请选择游戏平台：",
        "scan_loading": ["加载AI引擎...","校准波动指数...","同步RTP矩阵...","分析老虎机波动...","初始化随机模块..."],
        "scan_footer": "📊 已扫描: {scanned} | 🔥 Hot: {hot} | ⚡ Best: {best}%\n🕒 {time}\n⚠️ 仅15分钟有效"
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🎰 Selamat Datang ke MAXWIN AI RTP",
        "merchant_info": "🤖 AI scan RTP tertinggi dalam slot2\n📊 Tekan merchant di bawah untuk mula",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi:\nKemudian masukkan ID akaun:",
        "share_contact": "📱 Sila kongsi nombor telefon anda",
        "wait_admin": "Sila tunggu Admin meluluskan akses anda.",
        "approved": "✅ Akaun anda telah diluluskan!",
        "select_platform": "{merchant} - Sila pilih platform:",
        "scan_loading": ["Loading AI Engine...","Calibrating volatility index...","Syncing RTP Matrix...","Analyzing slot volatility...","Initializing RNG module..."],
        "scan_footer": "📊 Telah scan: {scanned} | 🔥 Hot: {hot} | ⚡ Best: {best}%\n🕒 {time}\n⚠️ Sah 15 min sahaja"
    }
}

# ===== 保存用户 =====
def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) in users_data and users_data[str(user_id)].get("approved"):
        # 已批准用户直接显示视频 + 欢迎文本 + 商家按钮 + 注册按钮
        lang = user_language.get(user_id,"en")
        await show_welcome_page(update, context, lang)
    else:
        # 未注册/未批准用户
        keyboard = [
            [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇲🇾 Bahasa Melayu", callback_data="lang_my")]
        ]
        await update.message.reply_text("🌐 Please select language / 请选择语言 / Sila Pilih Bahasa", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 欢迎页面 =====
async def show_welcome_page(update: Update, context: ContextTypes.DEFAULT_TYPE, lang):
    # 视频
    if update.message:
        await update.message.reply_video(VIDEO_FILE_ID)
    elif update.callback_query:
        await update.callback_query.message.reply_video(VIDEO_FILE_ID)

    text = f"{TEXTS[lang]['welcome']}\n{TEXTS[lang]['merchant_info']}"
    # 显示商家 + 注册按钮
    keyboard = []
    for m in MERCHANT_LINKS.keys():
        keyboard.append([InlineKeyboardButton(m, callback_data=f"merchant_{m}")])
    keyboard.append([InlineKeyboardButton("📌 Register Other Merchant", callback_data="register_other")])
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 语言选择 =====
async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    text = TEXTS[lang]["welcome"] + "\n\n" + TEXTS[lang]["choose_lang"]
    # 显示商家选择
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 商家处理 =====
async def merchant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id,"en")
    merchant = query.data.split("_")[1]
    # 判断是否已注册该商家
    registered = str(user_id) in users_data and merchant in users_data[str(user_id)].get("merchants",[])
    if registered:
        # 已注册 → 显示平台
        text = TEXTS[lang]["select_platform"].format(merchant=merchant)
        await show_platforms(query, merchant, lang)
    else:
        # 未注册 → 显示注册按钮
        register_button = InlineKeyboardButton("Click to Register", url=MERCHANT_LINKS[merchant])
        keyboard = [[register_button],[InlineKeyboardButton("🔙 Back", callback_data="back_welcome")]]
        await query.edit_message_text(TEXTS[lang]["register_prompt"], reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

# ===== 显示平台 =====
async def show_platforms(query, merchant, lang):
    platforms = MERCHANT_PLATFORMS.get(merchant,[])
    keyboard = [[InlineKeyboardButton(p, callback_data=f"platform_{merchant}_{p}")] for p in platforms]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="merchant_back")])
    await query.edit_message_text(TEXTS[lang]["select_platform"].format(merchant=merchant), reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 平台扫描 =====
async def platform_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id,"en")
    _, merchant, platform = query.data.split("_")
    games = PLATFORMS_GAMES.get(platform,[])
    
    # 显示Loading
    loading_messages = TEXTS[lang]["scan_loading"]
    progress_bar = "[□□□□□□□□□□]"
    loading_msg = await query.edit_message_text(f"{loading_messages[0]}\n{progress_bar} 0%")
    
    for i, msg in enumerate(loading_messages,1):
        progress = int(i/len(loading_messages)*100)
        bar_len = int(progress/10)
        bar = "■"*bar_len + "□"*(10-bar_len)
        await loading_msg.edit_text(f"{msg}\n[{bar}] {progress}%")
        await asyncio.sleep(2)
    
    # 生成随机RTP 25个
    rtp_results = {}
    for g in games:
        rtp_results[g] = [round(random.uniform(30,98),2) for _ in range(25)]
    
    # 构建消息
    msg = f"🔍 SCAN RESULT — {platform}\n━━━━━━━━━━━━━━━━━━\n👤 {merchant} | 🆔 AccountID\n━━━━━━━━━━━━━━━━━━\n"
    hot_count = 0
    best = 0
    for g,r_list in rtp_results.items():
        r = r_list[0]  # 取第一个示例显示
        if r<70:
            icon = "🛑"
        elif r<80:
            icon = "✅"
        elif r<90:
            icon = "🔥"
            hot_count += 1
        else:
            icon = "🏆"
        if r>best:
            best = r
        msg += f"{icon} {g} — {r}%\n"
    
    time_str = datetime.now().strftime("%d %b %Y %H:%M")
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += TEXTS[lang]["scan_footer"].format(scanned=len(games), hot=hot_count, best=best, time=time_str)
    
    # 添加返回按钮
    keyboard = [[InlineKeyboardButton("🔙 Back to Platform", callback_data=f"merchant_{merchant}")]]
    await loading_msg.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 注册其他商家 =====
async def register_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id,"en")
    keyboard = [[InlineKeyboardButton(m, callback_data=f"merchant_{m}")] for m in MERCHANT_LINKS.keys()]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_welcome")])
    await query.edit_message_text("Select merchant to register:", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== 返回处理 =====
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_language.get(user_id,"en")
    
    if query.data=="back_welcome":
        await show_welcome_page(update, context, lang)
    elif query.data=="merchant_back":
        await show_welcome_page(update, context, lang)

# ===== Admin Approve =====
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args)<2:
        await update.message.reply_text("Usage: /approve TG_ID Merchant")
        return
    user_id = context.args[0]
    merchant = context.args[1]
    if user_id not in users_data:
        users_data[user_id] = {"approved":True,"merchants":[merchant]}
    else:
        users_data[user_id]["approved"]=True
        if "merchants" not in users_data[user_id]:
            users_data[user_id]["merchants"]=[]
        if merchant not in users_data[user_id]["merchants"]:
            users_data[user_id]["merchants"].append(merchant)
    save_users()
    lang = user_language.get(int(user_id),"en")
    await context.bot.send_message(chat_id=int(user_id), text=TEXTS[lang]["approved"])
    await update.message.reply_text(f"User {user_id} approved for {merchant} ✅")

# ====== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(merchant_handler, pattern="merchant_"))
    app.add_handler(CallbackQueryHandler(platform_scan, pattern="platform_"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="back_"))
    app.add_handler(CallbackQueryHandler(register_other, pattern="register_other"))
    app.add_handler(CommandHandler("approve", approve))
    
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
