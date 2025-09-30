import base64
import hashlib
from typing import Dict
from google import genai
from Sakura.Core.config import GEMINI_API_KEY, OWNER_ID, CACHE_TTL
from Sakura.Core.logging import logger
from Sakura.Core.helpers import log_action, get_fallback, get_error
from Sakura.Database.conversation import get_context
from Sakura.Database.cache import get_cache, set_cache
from Sakura.Chat.prompts import SAKURA_PROMPT, LOVELY_SAKURA_PROMPT
from Sakura import state

def init_gemini():
    """Initialize Gemini client"""
    try:
        state.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini client: {e}")

async def gemini_response(user_message: str, user_name: str = "", user_info: Dict[str, any] = None, user_id: int = None) -> str:
    """Get response from Gemini API with conversation context and caching"""
    if user_info:
        log_action("DEBUG", f"🤖 Getting Gemini response for message: '{user_message[:50]}...'", user_info)

    if not state.gemini_client:
        if user_info:
            log_action("WARNING", "❌ Gemini client not available, using fallback response", user_info)
        return get_fallback()

    try:
        context = ""
        if user_id:
            context = await get_context(user_id)
            if context:
                context = f"\n\nPrevious conversation:\n{context}\n"

        active_prompt = SAKURA_PROMPT
        if user_id == OWNER_ID:
            active_prompt = LOVELY_SAKURA_PROMPT

        prompt = f"{active_prompt}\n\nUser name: {user_name}{context}\nCurrent user message: {user_message}\n\nSakura's response:"

        cache_key = None
        if len(user_message) <= 50 and not context and user_id:
            cache_key = f"gemini_response:{user_id}:{hashlib.md5(user_message.lower().encode()).hexdigest()}"
            cached_response = await get_cache(cache_key)
            if cached_response:
                if user_info:
                    log_action("INFO", f"📦 Using cached response for message", user_info)
                return cached_response

        response = await state.gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        ai_response = response.text.strip() if response.text else get_fallback()

        if cache_key:
            await set_cache(cache_key, ai_response, CACHE_TTL)

        if user_info:
            log_action("INFO", f"✅ Gemini response generated: '{ai_response[:50]}...'", user_info)

        return ai_response

    except Exception as e:
        if user_info:
            log_action("ERROR", f"❌ Gemini API error: {e}", user_info)
        else:
            logger.error(f"Gemini API error: {e}")
        return get_error()

async def analyze_image(image_bytes: bytes, caption: str, user_name: str = "", user_info: Dict[str, any] = None, user_id: int = None) -> str:
    """Analyze image using Gemini 2.5 Flash with conversation context"""
    if user_info:
        log_action("DEBUG", f"🖼️ Analyzing image with Gemini: {len(image_bytes)} bytes", user_info)

    if not state.gemini_client:
        if user_info:
            log_action("WARNING", "❌ Gemini client not available for image analysis", user_info)
        return "Samjh nahi paa rahi image kya hai 😔"

    try:
        context = ""
        if user_id:
            context = await get_context(user_id)
            if context:
                context = f"\n\nPrevious conversation:\n{context}\n"

        active_prompt = SAKURA_PROMPT
        if user_id == OWNER_ID:
            active_prompt = LOVELY_SAKURA_PROMPT

        image_prompt = f"""{active_prompt}

User name: {user_name}{context}

User has sent an image. Caption: "{caption if caption else 'No caption'}"

Analyze this image and respond in Sakura's style about what you see. Be descriptive but keep it to one or two lines as per your character rules. Comment on what's in the image, colors, mood, or anything interesting you notice.

Sakura's response:"""

        image_data = base64.b64encode(image_bytes).decode('utf-8')

        response = await state.gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                image_prompt,
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_data
                    }
                }
            ]
        )

        ai_response = response.text.strip() if response.text else "Kya cute image hai! 😍"

        if user_info:
            log_action("INFO", f"✅ Image analysis completed: '{ai_response[:50]}...'", user_info)

        return ai_response

    except Exception as e:
        if user_info:
            log_action("ERROR", f"❌ Image analysis error: {e}", user_info)
        else:
            logger.error(f"Image analysis error: {e}")
        return "Image analyze nahi kar paa rahi 😕"