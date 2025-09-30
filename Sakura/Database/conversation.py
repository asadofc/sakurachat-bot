import orjson
from Sakura.Core.config import CHAT_LENGTH, SESSION_TTL
from Sakura.Core.logging import logger
from Sakura import state

async def add_history(user_id: int, message: str, is_user: bool = True):
    """Add message to user's conversation history (Valkey + memory fallback)"""
    role = "user" if is_user else "assistant"
    new_message = {"role": role, "content": message}

    if state.valkey_client:
        try:
            key = f"conversation:{user_id}"
            existing = await state.valkey_client.get(key)
            history = orjson.loads(existing) if existing else []
            history.append(new_message)
            if len(history) > CHAT_LENGTH:
                history = history[-CHAT_LENGTH:]
            await state.valkey_client.setex(key, SESSION_TTL, orjson.dumps(history))
            logger.debug(f"💬 Conversation updated in Valkey for user {user_id}")
            return
        except Exception as e:
            logger.error(f"❌ Failed to update conversation in Valkey for user {user_id}: {e}")

    if user_id not in state.conversation_history:
        state.conversation_history[user_id] = []
    state.conversation_history[user_id].append(new_message)
    if len(state.conversation_history[user_id]) > CHAT_LENGTH:
        state.conversation_history[user_id] = state.conversation_history[user_id][-CHAT_LENGTH:]

async def get_history(user_id: int) -> list:
    """Get conversation history as a list of dicts."""
    history = []
    if state.valkey_client:
        try:
            key = f"conversation:{user_id}"
            existing = await state.valkey_client.get(key)
            if existing:
                history = orjson.loads(existing)
        except Exception as e:
            logger.error(f"❌ Failed to get conversation from Valkey for user {user_id}: {e}")

    if not history and user_id in state.conversation_history:
        history = state.conversation_history[user_id]

    return history

async def get_context(user_id: int) -> str:
    """Get formatted conversation context for the user."""
    history = await get_history(user_id)
    if not history:
        return ""
    context_lines = [f"User: {msg['content']}" if msg["role"] == "user" else f"Sakura: {msg['content']}" for msg in history]
    return "\n".join(context_lines)