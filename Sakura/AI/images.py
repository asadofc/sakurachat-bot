import random
from telegram import Update
from telegram.ext import ContextTypes
from Sakura.Core.helpers import log_action
from Sakura.Interface.reactions import CONTEXTUAL_REACTIONS
from Sakura.Interface.effects import animate_reaction
from Sakura.Interface.typing import send_typing
from Sakura.AI.response import get_response
from Sakura import state

IMAGE_ANALYSIS_TRIGGERS = [
    "photo", "photos", "picture", "pictures", "image", "images", "pic", "pics", "foto", "fotos",
    "tasveer", "tasveeren", "photo ka matlab", "isme kya hai", "yeh kya hai", "ye kya hai",
    "image analysis", "photo analysis", "identify", "identify this", "analyze", "analyze this",
    "batao", "dekho", "kya hai", "what is", "tell me", "isme", "ismein", "yeh", "ye", "is", "mein",
    "kaun si cheez", "kaun sa object", "ye object kya hai", "isme kya object hai", "yeh cheez kya hai"
]

async def reply_image(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str, user_info: dict) -> bool:
    """Check if user is asking to analyze a previously sent image and handle it"""
    message_lower = user_message.lower()
    contains_image_request = any(trigger in message_lower for trigger in IMAGE_ANALYSIS_TRIGGERS)

    if not contains_image_request:
        return False

    log_action("DEBUG", "🔍 Detected potential image analysis request", user_info)

    if update.message.reply_to_message and update.message.reply_to_message.photo:
        log_action("INFO", "🔍 User asking about replied image", user_info)

        try:
            emoji_to_react = random.choice(CONTEXTUAL_REACTIONS["love"])
            await animate_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                emoji=emoji_to_react
            )
            await animate_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.reply_to_message.message_id,
                emoji=emoji_to_react
            )
            log_action("INFO", f"🤔 Sent analysis reaction '{emoji_to_react}' for replied image", user_info)
        except Exception as e:
            log_action("WARNING", f"⚠️ Could not send analysis reaction for replied image: {e}", user_info)

        await send_typing(context, update.effective_chat.id, user_info)

        try:
            photo = update.message.reply_to_message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()

            user_name = update.effective_user.first_name or ""
            caption = update.message.reply_to_message.caption or ""

            response = await get_response(
                caption, user_name, user_info, user_info["user_id"], image_bytes=image_bytes
            )

            await update.message.reply_text(response)

            log_action("INFO", "✅ Referenced image analyzed successfully", user_info)
            return True

        except Exception as e:
            log_action("ERROR", f"❌ Error analyzing referenced image: {e}", user_info)
            error_response = "Image analyze nahi kar paa rahi 😔"
            await update.message.reply_text(error_response)
            return True

    if user_info["user_id"] in state.conversation_history:
        history = state.conversation_history[user_info["user_id"]]
        for message in reversed(history):
            if message["role"] == "user" and "[Image:" in message["content"]:
                log_action("INFO", "🔍 User asking about previously sent image from history", user_info)
                no_image_response = "Koi recent image nahi mil rahi analyze karne ke liye 😔"
                await update.message.reply_text(no_image_response)
                return True

    return False