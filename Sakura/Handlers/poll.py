import random
from telegram import Update
from telegram.ext import ContextTypes
from Sakura.Core.helpers import fetch_user, log_action, get_error
from Sakura.Interface.reactions import CONTEXTUAL_REACTIONS
from Sakura.Interface.effects import animate_reaction
from Sakura.Interface.typing import send_typing
from Sakura.AI.polls import analyze_poll

async def handle_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle poll messages with AI analysis"""
    user_info = fetch_user(update.message)
    log_action("INFO", "📊 Poll message received", user_info)

    try:
        emoji_to_react = random.choice(CONTEXTUAL_REACTIONS["confused"])
        await animate_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            emoji=emoji_to_react
        )
        log_action("INFO", f"🤔 Sent analysis reaction '{emoji_to_react}' for poll", user_info)
    except Exception as e:
        log_action("WARNING", f"⚠️ Could not send analysis reaction for poll: {e}", user_info)

    await send_typing(context, update.effective_chat.id, user_info)

    try:
        poll = update.message.poll
        poll_question = poll.question
        poll_options = [option.text for option in poll.options]
        log_action("DEBUG", f"📊 Poll question: '{poll_question}' with {len(poll_options)} options", user_info)

        user_name = update.effective_user.first_name or ""
        response = await analyze_poll(poll_question, poll_options, user_name, user_info, update.effective_user.id)

        log_action("DEBUG", f"📤 Sending poll analysis: '{response[:50]}...'", user_info)
        await update.message.reply_text(response)
        log_action("INFO", "✅ Poll analysis response sent successfully", user_info)

    except Exception as e:
        log_action("ERROR", f"❌ Error analyzing poll: {e}", user_info)
        await update.message.reply_text(get_error())