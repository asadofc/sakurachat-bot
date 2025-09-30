import random
import asyncio
from typing import Optional, Dict
from telegram import Update
from telegram.ext import ContextTypes
from Sakura.Chat.prompts import SAKURA_PROMPT, LOVELY_SAKURA_PROMPT
from Sakura.Core.config import OWNER_ID, MODEL
from Sakura.Core.helpers import log_action
from Sakura.Handlers.effects import animate_reaction
from Sakura.Handlers.reactions import CONTEXTUAL_REACTIONS
from Sakura.Handlers.typing import send_typing
from Sakura.Database.conversation import add_history, get_history
from Sakura import state

POLL_ANALYSIS_TRIGGERS = [
    "poll", "polls", "question", "questions", "query", "queries", "quiz", "quiz question",
    "answer", "answers", "reply", "replies", "solution", "solutions",
    "correct", "wrong", "galat", "sahi", "right", "incorrect", "true", "false",
    "option", "options", "choice", "choices", "selection", "selections",
    "batao", "jawab", "kya hai", "kya hai ye", "ye kya hai", "isme kya hai",
    "ismein kya hai", "sawal", "sawal ka jawab", "jawab do", "btao mujhe",
    "tell me", "what is", "which", "which one", "pick one", "choose one", "kaunsa sahi",
    "kaunsa galat", "kaunsa option", "kaunsa choice"
]

async def reply_poll(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str, user_info: dict) -> bool:
    """Check if user is asking to analyze a previously sent poll and handle it"""
    message_lower = user_message.lower()
    contains_poll_request = any(trigger in message_lower for trigger in POLL_ANALYSIS_TRIGGERS)

    if not contains_poll_request:
        return False

    log_action("DEBUG", "🔍 Detected potential poll analysis request", user_info)

    if update.message.reply_to_message and update.message.reply_to_message.poll:
        log_action("INFO", "🔍 User asking about replied poll", user_info)

        try:
            emoji_to_react = random.choice(CONTEXTUAL_REACTIONS["confused"])
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
            log_action("INFO", f"🤔 Sent analysis reaction '{emoji_to_react}' for replied poll", user_info)
        except Exception as e:
            log_action("WARNING", f"⚠️ Could not send analysis reaction for replied poll: {e}", user_info)

        await send_typing(context, update.effective_chat.id, user_info)

        try:
            poll = update.message.reply_to_message.poll
            poll_question = poll.question
            poll_options = [option.text for option in poll.options]
            user_name = update.effective_user.first_name or ""
            response = await analyze_poll(
                poll_question, poll_options, user_name, user_info, user_info["user_id"]
            )
            await update.message.reply_text(response)
            log_action("INFO", "✅ Referenced poll analyzed successfully", user_info)
            return True
        except Exception as e:
            log_action("ERROR", f"❌ Error analyzing referenced poll: {e}", user_info)
            error_response = "Poll analyze nahi kar paa rahi 😔"
            await update.message.reply_text(error_response)
            return True
    return False

async def analyze_poll(poll_question: str, poll_options: list, user_name: str = "", user_info: Dict[str, any] = None, user_id: int = None) -> str:
    """Analyze a poll, trying OpenRouter first and falling back to Gemini."""
    response = None
    source_api = None

    if state.openrouter_client:
        log_action("INFO", "🤖 Trying OpenRouter API for poll analysis...", user_info)
        try:
            response = await openrouter_poll(poll_question, poll_options, user_name, user_info, user_id)
            if response:
                source_api = "OpenRouter"
        except Exception as e:
            log_action("ERROR", f"❌ OpenRouter poll analysis error: {e}. Falling back to Gemini.", user_info)

    if not response:
        log_action("INFO", "🤖 Falling back to Gemini API for poll analysis", user_info)
        source_api = "Gemini"
        response = await gemini_poll(poll_question, poll_options, user_name, user_info, user_id)

    if response and user_id:
        poll_description = f"[Poll: {poll_question}] Options: {', '.join(poll_options)}"
        await add_history(user_id, poll_description, is_user=True)
        await add_history(user_id, response, is_user=False)
        log_action("INFO", f"✅ Poll analysis via {source_api} completed and saved to history", user_info)

    return response if response else "Poll analyze nahi kar paa rahi 😕"

async def openrouter_poll(poll_question: str, poll_options: list, user_name: str = "", user_info: Dict[str, any] = None, user_id: int = None) -> Optional[str]:
    """Analyze poll using OpenRouter API to suggest the correct answer."""
    if not state.openrouter_client:
        return None

    if user_info:
        log_action("DEBUG", f"📊 Analyzing poll with OpenRouter: '{poll_question[:50]}...'", user_info)

    try:
        history = await get_history(user_id)
        messages = []
        active_prompt = SAKURA_PROMPT
        if user_id == OWNER_ID:
            active_prompt = LOVELY_SAKURA_PROMPT
        messages.append({"role": "system", "content": active_prompt})
        messages.extend(history)
        options_text = "\n".join([f"{i + 1}. {option}" for i, option in enumerate(poll_options)])
        poll_prompt = f"""User has sent a poll or asked about a poll question. Analyze this question and suggest which option might be the correct answer.

Poll Question: "{poll_question}"

Options:
{options_text}

Analyze this poll question and respond in Sakura's style about which option you think is correct and why. Keep it to one or two lines as per your character rules. Be helpful and give a quick reason.

Sakura's response:"""
        messages.append({"role": "user", "content": poll_prompt})

        completion = await asyncio.to_thread(
            state.openrouter_client.chat.completions.create,
            extra_headers={"HTTP-Referer": "https://t.me/SakuraHarunoBot", "X-Title": "Sakura Bot"},
            model=MODEL,
            messages=messages
        )
        ai_response = completion.choices[0].message.content
        if ai_response:
            if user_info:
                log_action("INFO", f"✅ OpenRouter poll analysis completed: '{ai_response[:50]}...'", user_info)
            return ai_response.strip()
        return None
    except Exception as e:
        if user_info:
            log_action("ERROR", f"❌ OpenRouter poll analysis error: {e}", user_info)
        return None

async def gemini_poll(poll_question: str, poll_options: list, user_name: str = "", user_info: Dict[str, any] = None, user_id: int = None) -> str:
    """Analyze poll using Gemini 2.5 Flash to suggest the correct answer"""
    if user_info:
        log_action("DEBUG", f"📊 Analyzing poll with Gemini: '{poll_question[:50]}...'", user_info)

    if not state.gemini_client:
        if user_info:
            log_action("WARNING", "❌ Gemini client not available for poll analysis", user_info)
        return "Poll samjh nahi paa rahi 😔"

    try:
        context = ""
        if user_id:
            context = await get_context(user_id)
            if context:
                context = f"\n\nPrevious conversation:\n{context}\n"
        options_text = "\n".join([f"{i + 1}. {option}" for i, option in enumerate(poll_options)])
        active_prompt = SAKURA_PROMPT
        if user_id == OWNER_ID:
            active_prompt = LOVELY_SAKURA_PROMPT
        poll_prompt = f"""{active_prompt}

User name: {user_name}{context}

User has sent a poll or asked about a poll question. Analyze this question and suggest which option might be the correct answer.

Poll Question: "{poll_question}"

Options:
{options_text}

Analyze this poll question and respond in Sakura's style about which option you think is correct and why. Keep it to one or two lines as per your character rules. Be helpful and give a quick reason.

Sakura's response:"""
        response = await state.gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=poll_prompt
        )
        ai_response = response.text.strip() if response.text else "Poll ka answer samjh nahi aaya 😅"
        if user_info:
            log_action("INFO", f"✅ Gemini poll analysis completed: '{ai_response[:50]}...'", user_info)
        return ai_response
    except Exception as e:
        if user_info:
            log_action("ERROR", f"❌ Poll analysis error: {e}", user_info)
        return "Poll analyze nahi kar paa rahi 😕"