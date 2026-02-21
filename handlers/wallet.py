from telegram.ext import CallbackQueryHandler
from database import get_user

async def wallet_menu(update, context):
    query = update.callback_query
    await query.answer()

    user = get_user(update.effective_user.id)

    await query.edit_message_caption(
        caption=f"💰 DOMPET Boss\n"
                f"👤 ID: {update.effective_user.id}\n"
                f"📊 Total Invite: {user['invites']} Orang\n"
                f"💵 Baki Wallet: RM {user['wallet']}\n"
                f"Min withdrawal: RM50"
    )

def setup(app):
    app.add_handler(CallbackQueryHandler(wallet_menu, pattern="wallet_menu"))
