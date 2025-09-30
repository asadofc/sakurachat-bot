from valkey.asyncio import Valkey as AsyncValkey
from Sakura.Core.config import VALKEY_URL
from Sakura.Core.logging import logger
from Sakura import state

async def connect_cache():
    """Initialize Valkey connection"""
    try:
        state.valkey_client = AsyncValkey.from_url(
            VALKEY_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        await state.valkey_client.ping()
        logger.info("✅ Valkey client initialized and connected successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Valkey client: {e}")
        state.valkey_client = None
        return False

async def close_cache():
    """Close Valkey connection"""
    if state.valkey_client:
        try:
            await state.valkey_client.aclose()
            logger.info("✅ Valkey connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing Valkey connection: {e}")