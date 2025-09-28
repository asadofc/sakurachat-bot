import orjson
from Sakura.Core.config import CACHE_TTL
from Sakura.Core.logging import logger
from Sakura import state

async def set_cache(key: str, value: any, ttl: int = CACHE_TTL):
    """Set cache value in Valkey"""
    if not state.valkey_client:
        return False

    try:
        if isinstance(value, (dict, list)):
            value = orjson.dumps(value)
        await state.valkey_client.setex(f"cache:{key}", ttl, value)
        logger.debug(f"📦 Cache set for key: {key}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to set cache for key {key}: {e}")
        return False

async def get_cache(key: str) -> any:
    """Get cache value from Valkey"""
    if not state.valkey_client:
        return None

    try:
        value = await state.valkey_client.get(f"cache:{key}")
        if value:
            try:
                return orjson.loads(value)
            except:
                return value
        return None
    except Exception as e:
        logger.error(f"❌ Failed to get cache for key {key}: {e}")
        return None

async def delete_cache(key: str):
    """Delete cache value from Valkey"""
    if not state.valkey_client:
        return False

    try:
        await state.valkey_client.delete(f"cache:{key}")
        logger.debug(f"🗑️ Cache deleted for key: {key}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete cache for key {key}: {e}")
        return False