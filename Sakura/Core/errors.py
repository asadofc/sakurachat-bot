from telegram.ext import ContextTypes
from Sakura.Core.logging import logger
from Sakura.Core.helpers import fetch_user, log_action

async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")

    # Try to extract user info if update has a message
    if hasattr(update, 'message') and update.message:
        try:
            user_info = fetch_user(update.message)
            log_action("ERROR", f"💥 Exception occurred: {context.error}", user_info)
        except:
            logger.error(f"Could not extract user info for error: {context.error}")
    elif hasattr(update, 'callback_query') and update.callback_query and update.callback_query.message:
        try:
            user_info = fetch_user(update.callback_query.message)
            log_action("ERROR", f"💥 Callback query exception: {context.error}", user_info)
        except:
            logger.error(f"Could not extract user info for callback error: {context.error}")
