import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from Sakura.Core.helpers import fetch_user, log_action, should_reply, get_error, log_response
from Sakura.Services.limiter import check_limit
from Sakura.Handlers.reactions import handle_reaction
from Sakura.Chat.images import reply_image
from Sakura.Chat.polls import reply_poll
from Sakura.Handlers.typing import send_typing
from Sakura.Chat.response import get_response
from Sakura.Services.broadcast import execute_broadcast
from Sakura import state
from Sakura.Core.config import OWNER_ID
from Sakura.Handlers.commands import ping_command
from Sakura.Handlers.stickers import handle_sticker
from Sakura.Handlers.image import handle_image
from Sakura.Handlers.poll import handle_poll
from Sakura.Services.tracking import track_user

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text and media messages with AI response"""
    user_info = fetch_user(update.message)
    user_message = update.message.text or update.message.caption or "Media message"
    log_action("INFO", f"💬 Text/media message received: '{user_message[:100]}...'", user_info)

    if await reply_image(update, context, user_message, user_info):
        return
    if await reply_poll(update, context, user_message, user_info):
        return

    await send_typing(context, update.effective_chat.id, user_info)
    user_name = update.effective_user.first_name or ""
    response = await get_response(user_message, user_name, user_info, update.effective_user.id)
    log_action("DEBUG", f"📤 Sending response: '{response[:50]}...'", user_info)
    await update.message.reply_text(response)
    log_action("INFO", "✅ Text message response sent successfully", user_info)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all types of messages"""
    try:
        user_info = fetch_user(update.message)
        user_id = update.effective_user.id
        chat_type = update.effective_chat.type
        log_action("DEBUG", f"📨 Processing message in {chat_type}", user_info)

        track_user(update, user_info)

        if user_id == OWNER_ID and user_id in state.broadcast_mode:
            log_action("INFO", f"📢 Executing broadcast to {state.broadcast_mode[user_id]}", user_info)
            await execute_broadcast(update, context, state.broadcast_mode[user_id], user_info)
            del state.broadcast_mode[user_id]
            return

        user_message = update.message.text or update.message.caption or ""
        if any(user_message.lower().startswith(prefix) for prefix in ['?ping', '!ping', '*ping', '#ping']):
            log_action("INFO", f"🏓 Ping command detected with prefix: {user_message}", user_info)
            await ping_command(update, context)
            return

        if chat_type in ['group', 'supergroup'] and not should_reply(update, context.bot.id):
            log_action("DEBUG", "🚫 Not responding to group message (no mention/reply)", user_info)
            return

        log_action("INFO", "✅ Responding to group message (mentioned/replied)", user_info)

        if await check_limit(user_id, user_info["chat_id"]):
            log_action("WARNING", "⏱️ Rate limited - ignoring message", user_info)
            return

        asyncio.create_task(handle_reaction(update, user_info))

        if update.message.sticker:
            await handle_sticker(update, context)
        elif update.message.photo:
            await handle_image(update, context)
        elif update.message.poll:
            await handle_poll(update, context)
        else:
            await handle_text(update, context)

        await log_response(user_id)
        log_action("DEBUG", "⏰ Updated user response time", user_info)

    except Exception as e:
        user_info = fetch_user(update.message)
        log_action("ERROR", f"❌ Error handling message: {e}", user_info)
        if update.message.text:
            await update.message.reply_text(get_error())