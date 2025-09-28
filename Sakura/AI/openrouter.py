import asyncio
import base64
from typing import Optional, Dict
from openai import OpenAI
from Sakura.Core.config import OPENROUTER_API_KEY, MODEL, OWNER_ID
from Sakura.Core.logging import logger
from Sakura.Storage.conversation import get_history
from Sakura.AI.prompts import SAKURA_PROMPT, LOVELY_SAKURA_PROMPT
from Sakura import state

def initialize_openrouter_client():
    """Initialize OpenRouter client"""
    if OPENROUTER_API_KEY:
        try:
            state.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
            )
            logger.info("✅ OpenRouter client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenRouter client: {e}")

async def openrouter_response(user_message: str, user_name: str = "", user_info: Dict[str, any] = None, user_id: int = None, image_bytes: Optional[bytes] = None) -> Optional[str]:
    """Get response from OpenRouter API."""
    if not state.openrouter_client:
        return None

    history = await get_history(user_id)

    messages = []

    active_prompt = SAKURA_PROMPT
    if user_id == OWNER_ID:
        active_prompt = LOVELY_SAKURA_PROMPT

    messages.append({"role": "system", "content": active_prompt})
    messages.extend(history)

    current_message_content = []
    current_message_content.append({"type": "text", "text": user_message})

    if image_bytes:
        image_data = base64.b64encode(image_bytes).decode('utf-8')
        current_message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_data}"
            }
        })

    messages.append({"role": "user", "content": current_message_content})

    completion = await asyncio.to_thread(
        state.openrouter_client.chat.completions.create,
        extra_headers={
            "HTTP-Referer": "https://t.me/SakuraHarunoBot",
            "X-Title": "Sakura Bot",
        },
        model=MODEL,
        messages=messages
    )

    ai_response = completion.choices[0].message.content
    if ai_response:
        return ai_response.strip()
    else:
        return None