from telegram.ext import ApplicationBuilder
from config import TOKEN
from handlers import start, register, scan, admin, wallet, referral

app = ApplicationBuilder().token(TOKEN).build()

start.setup(app)
register.setup(app)
scan.setup(app)
admin.setup(app)
wallet.setup(app)
referral.setup(app)

print("Bot Running...")
app.run_polling()
