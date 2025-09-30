import random
import time
from telegram import Update, BotCommand
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from Sakura.Core.helpers import fetch_user, log_action, get_mention, get_error
from Sakura.Services.tracking import track_user
from Sakura.Handlers.reactions import EMOJI_REACT
from Sakura.Handlers.effects import animate_reaction, add_reaction, photo_effect
from Sakura.Handlers.typing import sticker_action, photo_action
from Sakura.Database.constants import START_STICKERS, SAKURA_IMAGES
from Sakura.Database.database import get_users, get_groups
from Sakura.Core.config import PING_LINK, OWNER_ID
from Sakura.Storage.database import get_users, get_groups
from Sakura.Handlers.messages import (
    START_MESSAGES,
    HELP_MESSAGES,
)
from Sakura import state

COMMANDS = [
    BotCommand("start", "👋 Wake me up"),
    BotCommand("buy", "🌸 Get flowers"),
    BotCommand("buyers", "💝 Flower buyers"),
    BotCommand("help", "💬 A short guide")
]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with two-step inline buttons and effects in private chat"""
    try:
        user_info = fetch_user(update.message)
        log_action("INFO", "🌸 /start command received", user_info)
        track_user(update, user_info)

        if EMOJI_REACT:
            try:
                random_emoji = random.choice(EMOJI_REACT)
                if state.effects_client and update.effective_chat.type == "private":
                    if not await animate_reaction(update.effective_chat.id, update.message.message_id, random_emoji):
                        await add_reaction(context, update, random_emoji, user_info)
                else:
                    await add_reaction(context, update, random_emoji, user_info)
            except Exception as e:
                log_action("WARNING", f"⚠️ Failed to add emoji reaction: {e}", user_info)

        if update.effective_chat.type == "private" and START_STICKERS:
            await sticker_action(context, update.effective_chat.id, user_info)
            random_sticker = random.choice(START_STICKERS)
            await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=random_sticker)
            log_action("INFO", "✅ Start sticker sent successfully", user_info)

        await photo_action(context, update.effective_chat.id, user_info)
        random_image = random.choice(SAKURA_IMAGES)
        keyboard = start_menu()
        user_mention = get_mention(update.effective_user)
        caption = START_MESSAGES["initial_caption"].format(user_mention=user_mention)

        if update.effective_chat.type == "private":
            if not await photo_effect(update.effective_chat.id, random_image, caption, keyboard):
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=random_image,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=random_image,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        log_action("INFO", "✅ Start command completed successfully", user_info)

    except Exception as e:
        user_info = fetch_user(update.message)
        log_action("ERROR", f"❌ Error in start command: {e}", user_info)
        await update.message.reply_text(get_error())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command with random image and effects in private chat"""
    try:
        user_info = fetch_user(update.message)
        log_action("INFO", "ℹ️ /help command received", user_info)
        track_user(update, user_info)

        if EMOJI_REACT:
            try:
                random_emoji = random.choice(EMOJI_REACT)
                if state.effects_client and update.effective_chat.type == "private":
                    if not await animate_reaction(update.effective_chat.id, update.message.message_id, random_emoji):
                        await add_reaction(context, update, random_emoji, user_info)
                else:
                    await add_reaction(context, update, random_emoji, user_info)
            except Exception as e:
                log_action("WARNING", f"⚠️ Failed to add emoji reaction: {e}", user_info)

        await photo_action(context, update.effective_chat.id, user_info)
        keyboard = help_menu(expanded=False)
        user_mention = get_mention(update.effective_user)
        caption = HELP_MESSAGES["minimal"].format(user_mention=user_mention)
        random_image = random.choice(SAKURA_IMAGES)

        if update.effective_chat.type == "private":
            if not await photo_effect(update.effective_chat.id, random_image, caption, keyboard):
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=random_image,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=random_image,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        log_action("INFO", "✅ Help command completed successfully", user_info)

    except Exception as e:
        user_info = fetch_user(update.message)
        log_action("ERROR", f"❌ Error in help command: {e}", user_info)
        await update.message.reply_text(get_error())

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle broadcast command (owner only)"""
    user_info = fetch_user(update.message)
    if update.effective_user.id != OWNER_ID:
        log_action("WARNING", "⚠️ Non-owner attempted broadcast command", user_info)
        return

    log_action("INFO", "📢 Broadcast command received from owner", user_info)
    state.user_ids.update(await get_users())
    state.group_ids.update(await get_groups())

    from Sakura.Handlers.keyboards import broadcast_menu
    from Sakura.Handlers.messages import BROADCAST_MESSAGES

    keyboard = broadcast_menu()
    text = BROADCAST_MESSAGES["select_target"].format(
        users_count=len(state.user_ids),
        groups_count=len(state.group_ids)
    )
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    log_action("INFO", "✅ Broadcast selection menu sent", user_info)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ping command for everyone"""
    user_info = fetch_user(update.message)
    log_action("INFO", "🏓 Ping command received", user_info)
    start_time = time.time()
    msg = await update.message.reply_text("🛰️ Pinging...")
    response_time = round((time.time() - start_time) * 1000, 2)
    await msg.edit_text(
        f"🏓 <a href='{PING_LINK}'>Pong!</a> {response_time}ms",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    log_action("INFO", "✅ Ping completed", user_info)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hidden owner command to show bot statistics"""
    try:
        user_info = fetch_user(update.message)
        if update.effective_user.id != OWNER_ID:
            log_action("WARNING", "⚠️ Non-owner attempted /stats command", user_info)
            return
        log_action("INFO", "📊 /stats command received from owner", user_info)
        from Sakura.Services.stats import send_stats
        await send_stats(update.message.chat.id, context, is_refresh=False)
        log_action("INFO", "✅ Bot statistics sent to owner", user_info)
    except Exception as e:
        user_info = fetch_user(update.message)
        log_action("ERROR", f"❌ Error in /stats command: {e}", user_info)
        await update.message.reply_text("❌ Something went wrong getting bot statistics!")