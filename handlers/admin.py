from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import load, save

async def approve_handler(update, context):
    query = update.callback_query
    user_id = query.data.split("_")[1]

    users = load()
    users[user_id]["status"] = "APPROVED"
    save(users)

    await context.bot.send_message(user_id, "✅ Akaun Boss telah diluluskan🔥")

    await context.bot.send_video(
        user_id,
        context.bot_data["VIDEO"],
        caption="🔥Selamat datang ke MAXWIN AI RTP\n🤖AI yang scan RTP tertinggi dalam slot2\n📊 Tekan game menu di bawah untuk mula"
    )

    await query.edit_message_reply_markup(reply_markup=query.message.reply_markup)
