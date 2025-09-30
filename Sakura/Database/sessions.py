import orjson
from Sakura.Core.config import SESSION_TTL
from Sakura.Core.logging import logger
from Sakura import state

async def save_session(user_id: int, session_data: dict):
    """Save user session data to Valkey"""
    if not state.valkey_client:
        return False

    try:
        key = f"session:{user_id}"
        await state.valkey_client.setex(
            key,
            SESSION_TTL,
            orjson.dumps(session_data)
        )
        logger.debug(f"💾 Session saved for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save session for user {user_id}: {e}")
        return False

async def get_session(user_id: int) -> dict:
    """Get user session data from Valkey"""
    if not state.valkey_client:
        return {}

    try:
        key = f"session:{user_id}"
        data = await state.valkey_client.get(key)
        if data:
            return orjson.loads(data)
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to get session for user {user_id}: {e}")
        return {}

async def delete_session(user_id: int):
    """Delete user session from Valkey"""
    if not state.valkey_client:
        return False

    try:
        key = f"session:{user_id}"
        await state.valkey_client.delete(key)
        logger.debug(f"🗑️ Session deleted for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete session for user {user_id}: {e}")
        return False