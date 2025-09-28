import random
import time
from typing import Dict
from telegram import Message, Update
from Sakura.Core.logging import logger
from Sakura.Interface.messages import RESPONSES, ERROR
from Sakura import state
from Sakura.Core.config import SESSION_TTL

def fetch_user(msg: Message) -> Dict[str, any]:
    """Extract user and chat information from message"""
    logger.debug("🔍 Extracting user information from message")
    u = msg.from_user
    c = msg.chat
    info = {
        "user_id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "chat_id": c.id,
        "chat_type": c.type,
        "chat_title": c.title or c.first_name or "",
        "chat_username": f"@{c.username}" if c.username else "No Username",
        "chat_link": f"https://t.me/{c.username}" if c.username else "No Link",
    }
    logger.info(
        f"📑 User info extracted: {info['full_name']} (@{info['username']}) "
        f"[ID: {info['user_id']}] in {info['chat_title']} [{info['chat_id']}] {info['chat_link']}"
    )
    return info

def log_action(level: str, message: str, user_info: Dict[str, any]) -> None:
    """Log message with user information"""
    user_detail = (
        f"👤 {user_info.get('full_name', 'N/A')} (@{user_info.get('username', 'N/A')}) "
        f"[ID: {user_info.get('user_id', 'N/A')}] | "
        f"💬 {user_info.get('chat_title', 'N/A')} [{user_info.get('chat_id', 'N/A')}] "
        f"({user_info.get('chat_type', 'N/A')}) {user_info.get('chat_link', 'N/A')}"
    )
    full_message = f"{message} | {user_detail}"

    if level.upper() == "INFO":
        logger.info(full_message)
    elif level.upper() == "DEBUG":
        logger.debug(full_message)
    elif level.upper() == "WARNING":
        logger.warning(full_message)
    elif level.upper() == "ERROR":
        logger.error(full_message)
    else:
        logger.info(full_message)

def should_reply(update: Update, bot_id: int) -> bool:
    """Determine if bot should respond in group chat"""
    user_message = update.message.text or update.message.caption or ""
    if "sakura" in user_message.lower():
        return True
    if (update.message.reply_to_message and
        update.message.reply_to_message.from_user.id == bot_id):
        return True
    return False

def get_mention(user) -> str:
    """Create user mention for HTML parsing using first name"""
    first_name = user.first_name or "Friend"
    return f'<a href="tg://user?id={user.id}">{first_name}</a>'

def get_fallback() -> str:
    """Get a random fallback response when API fails"""
    return random.choice(RESPONSES)

def get_error() -> str:
    """Get a random error response when something goes wrong"""
    return random.choice(ERROR)

async def log_response(user_id: int) -> None:
    """Update the last response time for user in Valkey"""
    if state.valkey_client:
        try:
            key = f"last_response:{user_id}"
            await state.valkey_client.setex(key, SESSION_TTL, int(time.time()))
            logger.debug(f"⏰ Updated response time in Valkey for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to update response time in Valkey for user {user_id}: {e}")
    state.user_last_response_time[user_id] = time.time()