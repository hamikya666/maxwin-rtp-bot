async def referral_handler(update, context):
    user_id = str(update.effective_user.id)
    link = f"https://t.me/YOURBOT?start=REF{user_id}"

    text = (
        "🔗 LINK REFERRAL BOSS\n"
        "Share link dapatkan RM1 setiap invite!\n"
        f"{link}"
    )

    await update.callback_query.edit_message_caption(caption=text)
