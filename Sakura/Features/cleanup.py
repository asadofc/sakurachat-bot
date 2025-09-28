import asyncio
import time
from Sakura.Core.logging import logger
from Sakura.Core.config import OLD_CHAT, CHAT_CLEANUP
from Sakura import state

async def cleanup_conversations():
    """Clean up old conversation histories and response times periodically"""
    logger.info("🧹 Conversation cleanup task started")

    while True:
        try:
            current_time = time.time()
            conversations_cleaned = 0

            expired_users = [
                user_id for user_id, last_response_time in state.user_last_response_time.items()
                if current_time - last_response_time > OLD_CHAT
            ]

            for user_id in expired_users:
                if user_id in state.conversation_history:
                    del state.conversation_history[user_id]
                    conversations_cleaned += 1
                if user_id in state.user_last_response_time:
                    del state.user_last_response_time[user_id]

            if conversations_cleaned > 0:
                logger.info(f"🧹 Cleaned {conversations_cleaned} old conversations")

            logger.debug(f"📊 Active conversations: {len(state.conversation_history)}")

        except asyncio.CancelledError:
            logger.info("🧹 Cleanup task cancelled - shutting down gracefully")
            break
        except Exception as e:
            logger.error(f"❌ Error in conversation cleanup: {e}")

        try:
            await asyncio.sleep(CHAT_CLEANUP)
        except asyncio.CancelledError:
            logger.info("🧹 Cleanup task sleep cancelled - shutting down")
            break