import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import Forbidden, BadRequest
from Sakura.Core.helpers import log_action
from Sakura.Database.database import get_users, get_groups, remove_user, remove_group
from Sakura.Interface.messages import BROADCAST_MESSAGES
from Sakura.Core.config import BROADCAST_DELAY

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, target_type: str, user_info: dict) -> None:
    """Execute broadcast with the current message"""
    try:
        if target_type == "users":
            target_list = await get_users()
            target_list = [uid for uid in target_list if uid != user_info["user_id"]]
            target_name = "users"
        elif target_type == "groups":
            target_list = await get_groups()
            target_name = "groups"
        else:
            return

        log_action("INFO", f"🚀 Starting broadcast to {len(target_list)} {target_name}", user_info)

        if not target_list:
            await update.message.reply_text(
                BROADCAST_MESSAGES["no_targets"].format(target_type=target_name)
            )
            log_action("WARNING", f"⚠️ No {target_name} found for broadcast", user_info)
            return

        is_forwarded = update.message.forward_origin is not None
        broadcast_method = "forward" if is_forwarded else "copy"
        log_action("INFO", f"📤 Using {broadcast_method} method for broadcast", user_info)

        status_msg = await update.message.reply_text(
            BROADCAST_MESSAGES["progress"].format(count=len(target_list), target_type=target_name)
        )

        broadcast_count = 0
        failed_count = 0

        for i, target_id in enumerate(target_list, 1):
            try:
                if is_forwarded:
                    await context.bot.forward_message(
                        chat_id=target_id,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.message_id
                    )
                else:
                    await context.bot.copy_message(
                        chat_id=target_id,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.message_id
                    )
                broadcast_count += 1
                if i % 10 == 0:
                    log_action("DEBUG", f"📡 Broadcast progress: {i}/{len(target_list)} using {broadcast_method}", user_info)
                await asyncio.sleep(BROADCAST_DELAY)

            except Forbidden:
                failed_count += 1
                if target_name == "users":
                    await remove_user(target_id)
                elif target_name == "groups":
                    await remove_group(target_id)
            except BadRequest as e:
                failed_count += 1
                if "chat not found" in str(e).lower():
                    if target_name == "users":
                        await remove_user(target_id)
                    else:
                        await remove_group(target_id)
                else:
                    log_action("ERROR", f"❌ Broadcast failed for {target_id}: {e}", user_info)
            except Exception as e:
                failed_count += 1
                log_action("ERROR", f"❌ Unhandled broadcast error for {target_id}: {e}", user_info)

        await status_msg.edit_text(
            BROADCAST_MESSAGES["completed"].format(
                success_count=broadcast_count,
                total_count=len(target_list),
                target_type=target_name,
                failed_count=failed_count
            ) + f"\n<i>Method used: {broadcast_method}</i>",
            parse_mode=ParseMode.HTML
        )
        log_action("INFO", f"✅ Broadcast completed using {broadcast_method}: {broadcast_count}/{len(target_list)} successful, {failed_count} failed", user_info)

    except Exception as e:
        log_action("ERROR", f"❌ Broadcast error: {e}", user_info)
        await update.message.reply_text(
            BROADCAST_MESSAGES["failed"].format(error=str(e))
        )