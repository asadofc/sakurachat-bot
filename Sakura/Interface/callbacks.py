from telegram import Update, ChatMember
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden
from Sakura.Core.helpers import fetch_user, log_action, get_mention
from Sakura.Interface.keyboards import info_menu, help_menu
from Sakura.Interface.messages import START_MESSAGES, HELP_MESSAGES, BROADCAST_MESSAGES
from Sakura.Interface.typing import send_typing
from Sakura.AI.response import get_response
from Sakura.Interface.effects import send_effect
from Sakura.Features.payments import send_invoice
from Sakura import state
from Sakura.Core.config import OWNER_ID

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle start command inline button callbacks"""
    query = update.callback_query
    if query.message.chat.type in ['group', 'supergroup']:
        try:
            chat_member = await context.bot.get_chat_member(query.message.chat.id, context.bot.id)
            if chat_member.status in [ChatMember.LEFT, ChatMember.BANNED]:
                await query.answer("Add me first, my soul might be here but my body not! 🌸", show_alert=True)
                return
        except (BadRequest, Forbidden):
            await query.answer("Add me first, my soul might be here but my body not! 🌸", show_alert=True)
            return

    try:
        user_info = fetch_user(query.message)
        log_action("INFO", f"🌸 Start callback received: {query.data}", user_info)
        user_mention = get_mention(update.effective_user)

        if query.data == "start_info":
            await query.answer(START_MESSAGES["callback_answers"]["info"], show_alert=False)
            keyboard = info_menu(context.bot.username)
            caption = START_MESSAGES["info_caption"].format(user_mention=user_mention)
            await query.edit_message_caption(caption=caption, parse_mode="HTML", reply_markup=keyboard)
            log_action("INFO", "✅ Start info buttons shown", user_info)

        elif query.data == "start_hi":
            await query.answer(START_MESSAGES["callback_answers"]["hi"], show_alert=False)
            await send_typing(context, update.effective_chat.id, user_info)
            user_name = update.effective_user.first_name or ""
            hi_response = await get_response("Hi sakura", user_name, user_info, update.effective_user.id)

            if update.effective_chat.type == "private":
                if not await send_effect(update.effective_chat.id, hi_response):
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=hi_response)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=hi_response)
            log_action("INFO", "✅ Hi message sent from Sakura", user_info)

    except Exception as e:
        user_info = fetch_user(query.message) if query.message else {}
        log_action("ERROR", f"❌ Error in start callback: {e}", user_info)
        try:
            await query.answer("Something went wrong 😔", show_alert=True)
        except:
            pass

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle help expand/minimize callbacks"""
    query = update.callback_query
    if query.message.chat.type in ['group', 'supergroup']:
        try:
            chat_member = await context.bot.get_chat_member(query.message.chat.id, context.bot.id)
            if chat_member.status in [ChatMember.LEFT, ChatMember.BANNED]:
                await query.answer("Add me first, my soul might be here but my body not! 🌸", show_alert=True)
                return
        except (BadRequest, Forbidden):
            await query.answer("Add me first, my soul might be here but my body not! 🌸", show_alert=True)
            return

    try:
        user_info = fetch_user(query.message)
        log_action("INFO", f"🔄 Help callback received: {query.data}", user_info)
        user_mention = get_mention(update.effective_user)

        expanded = query.data == "help_expand"
        answer_text = HELP_MESSAGES["callback_answers"]["expand" if expanded else "minimize"]
        await query.answer(answer_text, show_alert=False)

        keyboard = help_menu(expanded=expanded)
        caption = HELP_MESSAGES["expanded" if expanded else "minimal"].format(user_mention=user_mention)

        await query.edit_message_caption(caption=caption, parse_mode="HTML", reply_markup=keyboard)
        log_action("INFO", f"✅ Help message {'expanded' if expanded else 'minimized'}", user_info)

    except Exception as e:
        user_info = fetch_user(query.message) if query.message else {}
        log_action("ERROR", f"❌ Error editing help message: {e}", user_info)
        try:
            await query.answer("Something went wrong 😔", show_alert=True)
        except:
            pass

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle broadcast target selection and get flowers again button"""
    query = update.callback_query
    if query.message.chat.type in ['group', 'supergroup']:
        try:
            chat_member = await context.bot.get_chat_member(query.message.chat.id, context.bot.id)
            if chat_member.status in [ChatMember.LEFT, ChatMember.BANNED]:
                await query.answer("Add me first, my soul might be here but my body not! 🌸", show_alert=True)
                return
        except (BadRequest, Forbidden):
            await query.answer("Add me first, my soul might be here but my body not! 🌸", show_alert=True)
            return

    user_info = fetch_user(query.message)

    if query.data == "get_flowers_again":
        log_action("INFO", "🌸 'Buy flowers again' button clicked", user_info)
        await query.answer("🌸 Getting more flowers for you!", show_alert=False)
        await send_invoice(context, query.message.chat.id, user_info, 50)
        return

    if query.from_user.id != OWNER_ID:
        log_action("WARNING", "⚠️ Non-owner attempted broadcast callback", user_info)
        await query.answer("You're not authorized to use this 🚫", show_alert=True)
        return

    log_action("INFO", f"🎯 Broadcast target selected: {query.data}", user_info)

    if query.data == "bc_users":
        await query.answer(BROADCAST_MESSAGES["callback_answers"]["users"], show_alert=False)
        state.broadcast_mode[OWNER_ID] = "users"
        await query.edit_message_text(
            BROADCAST_MESSAGES["ready_users"].format(count=len(state.user_ids)),
            parse_mode="HTML"
        )
        log_action("INFO", f"✅ Ready to broadcast to {len(state.user_ids)} users", user_info)

    elif query.data == "bc_groups":
        await query.answer(BROADCAST_MESSAGES["callback_answers"]["groups"], show_alert=False)
        state.broadcast_mode[OWNER_ID] = "groups"
        await query.edit_message_text(
            BROADCAST_MESSAGES["ready_groups"].format(count=len(state.group_ids)),
            parse_mode="HTML"
        )
        log_action("INFO", f"✅ Ready to broadcast to {len(state.group_ids)} groups", user_info)

async def stats_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle stats refresh button callback"""
    query = update.callback_query
    if query.message.chat.type in ['group', 'supergroup']:
        try:
            chat_member = await context.bot.get_chat_member(query.message.chat.id, context.bot.id)
            if chat_member.status in [ChatMember.LEFT, ChatMember.BANNED]:
                await query.answer("Add me first, my soul might be here but my body not! 🌸", show_alert=True)
                return
        except (BadRequest, Forbidden):
            await query.answer("Add me first, my soul might be here but my body not! 🌸", show_alert=True)
            return

    try:
        user_info = fetch_user(query.message)
        if query.from_user.id != OWNER_ID:
            log_action("WARNING", "⚠️ Non-owner attempted stats refresh", user_info)
            await query.answer("You're not authorized to use this 🚫", show_alert=True)
            return

        log_action("INFO", "🔄 Stats refresh callback received from owner", user_info)
        await query.answer("🔄 Refreshing statistics...", show_alert=False)

        from Sakura.Features.stats import send_stats
        stats_message, reply_markup = await send_stats(query.message.chat.id, context, is_refresh=True)

        await query.edit_message_text(
            text=stats_message,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        log_action("INFO", "✅ Stats refreshed successfully", user_info)

    except Exception as e:
        user_info = fetch_user(query.message) if query.message else {}
        log_action("ERROR", f"❌ Error refreshing stats: {e}", user_info)
        try:
            await query.answer("❌ Error refreshing statistics!", show_alert=True)
        except:
            pass