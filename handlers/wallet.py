from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import ensure_user, save

MIN_WITHDRAW = 50

async def wallet_menu(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)

    users = ensure_user(user_id)
    user = users[user_id]

    keyboard = [
        [InlineKeyboardButton("💸 Request Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("⬅ Kembali", callback_data="back_main")]
    ]

    text = (
        "💰 DOMPET Boss\n"
        f"👤 ID: {user_id}\n"
        f"📊 Total Invite: {user['invite']} Orang\n"
        f"💵 Baki Wallet: RM {user['wallet']}\n"
        "Min withdrawal: RM50"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def withdraw(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)

    users = ensure_user(user_id)
    user = users[user_id]

    if user["wallet"] < MIN_WITHDRAW:
        await query.answer("❌ Jumlah tidak mencukupi!", show_alert=True)
    else:
        await query.answer("✅ Request dihantar ke admin!", show_alert=True)
