from telegram import Update, ChatMember
from telegram.ext import ContextTypes
from Sakura.Core.logging import logger
from Sakura.Database.database import remove_user, remove_group

async def handle_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when a user blocks the bot or the bot is removed from a group."""
    result = update.my_chat_member
    if not result:
        return

    chat = result.chat
    new_status = result.new_chat_member.status

    if new_status in [ChatMember.BANNED, ChatMember.LEFT]:
        if chat.type == 'private':
            logger.info(f"User {chat.id} blocked the bot. Removing from database.")
            await remove_user(chat.id)
        elif chat.type in ['group', 'supergroup']:
            logger.info(f"Bot was removed from group {chat.id}. Removing from database.")
            await remove_group(chat.id)