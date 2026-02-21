from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import BOT_USERNAME

async def referral_menu(update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)

    link = f"https://t.me/{BOT_USERNAME}?start=REF{user_id}"

    keyboard = [
        [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={link}")],
        [InlineKeyboardButton("⬅ Kembali", callback_data="back_main")]
    ]

    text = (
        "💰SHARE AND EARN💰\n\n"
        f"{link}\n\n"
        "Share link dapatkan RM1 setiap invite!"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
