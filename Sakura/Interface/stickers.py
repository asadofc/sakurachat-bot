import random
from telegram import Update
from telegram.ext import ContextTypes
from Sakura.Core.helpers import fetch_user, log_action
from Sakura.Interface.typing import sticker_action
from Sakura.Storage.storage import SAKURA_STICKERS

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sticker messages"""
    user_info = fetch_user(update.message)
    log_action("INFO", "🎭 Sticker message received", user_info)

    await sticker_action(context, update.effective_chat.id, user_info)

    random_sticker = random.choice(SAKURA_STICKERS)
    chat_type = update.effective_chat.type

    log_action("DEBUG", f"📤 Sending random sticker: {random_sticker}", user_info)

    if (chat_type in ['group', 'supergroup'] and
        update.message.reply_to_message and
        update.message.reply_to_message.from_user.id == context.bot.id):
        await update.message.reply_sticker(sticker=random_sticker)
        log_action("INFO", "✅ Replied to user's sticker in group", user_info)
    else:
        await context.bot.send_sticker(
            chat_id=update.effective_chat.id,
            sticker=random_sticker
        )
        log_action("INFO", "✅ Sent sticker response", user_info)