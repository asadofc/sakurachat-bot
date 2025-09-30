import random
from telegram import Update
from telegram.ext import ContextTypes
from Sakura.Core.helpers import fetch_user, log_action, get_error
from Sakura.Interface.reactions import CONTEXTUAL_REACTIONS
from Sakura.Interface.effects import animate_reaction
from Sakura.Interface.typing import send_typing
from Sakura.AI.response import get_response

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle image messages with AI analysis"""
    user_info = fetch_user(update.message)
    log_action("INFO", "📷 Image message received", user_info)

    try:
        emoji_to_react = random.choice(CONTEXTUAL_REACTIONS["love"])
        await animate_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            emoji=emoji_to_react
        )
        log_action("INFO", f"🤔 Sent analysis reaction '{emoji_to_react}' for image", user_info)
    except Exception as e:
        log_action("WARNING", f"⚠️ Could not send analysis reaction for image: {e}", user_info)

    await send_typing(context, update.effective_chat.id, user_info)

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        log_action("DEBUG", f"📥 Image downloaded: {len(image_bytes)} bytes", user_info)

        user_name = update.effective_user.first_name or ""
        caption = update.message.caption or ""

        response = await get_response(caption, user_name, user_info, update.effective_user.id, image_bytes=image_bytes)

        log_action("DEBUG", f"📤 Sending image analysis: '{response[:50]}...'", user_info)
        await update.message.reply_text(response)
        log_action("INFO", "✅ Image analysis response sent successfully", user_info)

    except Exception as e:
        log_action("ERROR", f"❌ Error analyzing image: {e}", user_info)
        await update.message.reply_text(get_error())