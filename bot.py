import json
import random
import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import os

# ====== 配置 ======
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
USERS_FILE = "users.json"

# ====== 初始化 ======
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

# ====== 平台 ======
PLATFORMS = ["PP", "BNG", "JILI", "PG"]

# ====== 游戏示例数据 ======
GAMES = {
    "PP": [f"PP_Game_{i}" for i in range(1,36)],
    "BNG": [f"BNG_Game_{i}" for i in range(1,36)],
    "JILI": [f"JILI_Game_{i}" for i in range(1,36)],
    "PG": [f"PG_Game_{i}" for i in range(1,36)]
}

# ====== 临时存储 ======
pending_users = {}
user_language = {}  # TG_ID: 'en'/'zh'/'my'

# ====== 语言文本 ======
TEXTS = {
    "en": {
        "choose_lang": "🌐 Please Select Language",
        "welcome": "🎰 Welcome to MaxWin Official RTP Bot",
        "choose_merchant": "Please select a merchant:",
        "register_prompt": "⚠️ Please register via official link:\n{link}\nThen enter your account ID:",
        "share_contact": "📱 Please share your phone number:",
        "wait_admin": "Please wait for Admin to approve your access.",
        "approved": "✅ Your account has been approved.\nSelect merchant:",
        "select_platform": "{merchant} - Please select a platform:",
        "rtp_top": "{merchant} - {platform} RTP TOP 15\n\n",
    },
    "zh": {
        "choose_lang": "请选择语言",
        "welcome": "🎰 欢迎来到 MaxWin 官方 RTP 查询机器人",
        "choose_merchant": "请选择商家：",
        "register_prompt": "⚠️ 请通过以下链接注册：\n{link}\n注册后请输入账号ID：",
        "share_contact": "📱 请授权手机号：",
        "wait_admin": "请等待 Admin 审核权限。",
        "approved": "✅ 审核通过 ✅\n请选择商家：",
        "select_platform": "{merchant} - 请选择游戏平台：",
        "rtp_top": "{merchant} - {platform} RTP TOP 15\n\n",
    },
    "my": {
        "choose_lang": "Sila Pilih Bahasa",
        "welcome": "🎰 Selamat Datang ke MaxWin RTP Bot Rasmi",
        "choose_merchant": "Sila pilih merchant:",
        "register_prompt": "⚠️ Sila daftar melalui pautan rasmi:\n{link}\nKemudian masukkan ID akaun:",
        "sh
