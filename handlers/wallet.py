from database import load

async def wallet_handler(update, context):
    user_id = str(update.effective_user.id)
from database import ensure_user

users = ensure_user(user_id)
user = users[user_id]

    text = (
        "💰 DOMPET Boss\n"
        f"👤 ID: {user_id}\n"
        f"📊 Total Invite: {user['invite']} Orang\n"
        f"💵 Baki Wallet: RM {user['wallet']}\n"
        "Min withdrawal: RM50"
    )

    await update.callback_query.edit_message_caption(caption=text)
