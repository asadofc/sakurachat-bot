import os
import random
import aiohttp
import orjson
from telethon import TelegramClient
from telegram import ReactionTypeEmoji
from Sakura.Core.config import BOT_TOKEN, API_ID, API_HASH
from Sakura.Core.logging import logger
from Sakura import state

EFFECTS = [
    "5104841245755180586",
    "5159385139981059251"
]

def init_effects():
    """Initialize Telethon client for effects"""
    if os.path.exists('sakura_effects.session'):
        os.remove('sakura_effects.session')
    try:
        state.effects_client = TelegramClient('sakura_effects', API_ID, API_HASH)
        logger.info("✅ Telethon effects client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Telethon effects client: {e}")

async def send_effect(chat_id: int, text: str, reply_markup=None) -> bool:
    """Send message with random effect using Telethon"""
    if not state.effects_client:
        logger.warning("⚠️ Telethon effects client not available")
        return False

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'message_effect_id': random.choice(EFFECTS),
            'parse_mode': 'HTML'
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup.to_dict()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=orjson.dumps(payload),
                headers={'Content-Type': 'application/json'}
            ) as response:
                result = await response.json(loads=orjson.loads)
                return result.get('ok', False)
    except Exception as e:
        logger.error(f"❌ Effect error for {chat_id}: {e}")
        return False

async def animate_reaction(chat_id: int, message_id: int, emoji: str) -> bool:
    """Send animated emoji reaction using direct API call"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction"
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'reaction': [{'type': 'emoji', 'emoji': emoji}],
            'is_big': True
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=orjson.dumps(payload),
                headers={'Content-Type': 'application/json'}
            ) as response:
                result = await response.json(loads=orjson.loads)
                return result.get('ok', False)
    except Exception as e:
        logger.error(f"❌ Animated reaction error for {chat_id}: {e}")
        return False

async def add_reaction(context, update, emoji: str, user_info: dict):
    """Fallback PTB reaction without animation"""
    try:
        reaction = [ReactionTypeEmoji(emoji=emoji)]
        await context.bot.set_message_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            reaction=reaction
        )
    except Exception as e:
        from Sakura.Core.helpers import log_action
        log_action("WARNING", f"⚠️ PTB reaction fallback failed: {e}", user_info)

async def photo_effect(chat_id: int, photo_url: str, caption: str, reply_markup=None) -> bool:
    """Send photo message with random effect using direct API"""
    if not state.effects_client:
        logger.warning("⚠️ Telethon effects client not available")
        return False

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': caption,
            'message_effect_id': random.choice(EFFECTS),
            'parse_mode': 'HTML'
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup.to_dict()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=orjson.dumps(payload),
                headers={'Content-Type': 'application/json'}
            ) as response:
                result = await response.json(loads=orjson.loads)
                return result.get('ok', False)
    except Exception as e:
        logger.error(f"❌ Photo effect error for {chat_id}: {e}")
        return False

async def start_effects():
    """Start Telethon effects client"""
    if state.effects_client:
        try:
            await state.effects_client.start(bot_token=BOT_TOKEN)
            logger.info("✅ Telethon effects client started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start Telethon effects client: {e}")
            state.effects_client = None

async def stop_effects():
    """Stop Telethon effects client"""
    if state.effects_client:
        try:
            await state.effects_client.disconnect()
            logger.info("✅ Telethon effects client stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping Telethon effects client: {e}")