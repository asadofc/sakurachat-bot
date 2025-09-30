from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from Sakura.Core.helpers import log_action

async def send_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_info: dict) -> None:
    """Send typing action to show bot is processing"""
    log_action("DEBUG", "⌨️ Sending typing action", user_info)
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

async def photo_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_info: dict) -> None:
    """Send upload photo action"""
    log_action("DEBUG", "📷 Sending photo upload action", user_info)
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

async def sticker_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_info: dict) -> None:
    """Send choosing sticker action"""
    log_action("DEBUG", "🎭 Sending sticker choosing action", user_info)
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.CHOOSE_STICKER)