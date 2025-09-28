from telegram import Update
from Sakura.Core.helpers import log_action
from Sakura.Storage.database import save_user, save_group
from Sakura import state

def track_user(update: Update, user_info: dict) -> None:
    """Track user and chat IDs for broadcasting (fast memory + async database)"""
    user_id = user_info["user_id"]
    chat_id = user_info["chat_id"]
    chat_type = user_info["chat_type"]

    if chat_type == "private":
        is_new_user = user_id not in state.user_ids
        state.user_ids.add(user_id)
        save_user(
            user_id,
            user_info.get("username"),
            user_info.get("first_name"),
            user_info.get("last_name")
        )
        if is_new_user:
            log_action("INFO", f"👤 New user tracked for broadcasting", user_info)

    elif chat_type in ['group', 'supergroup']:
        is_new_group = chat_id not in state.group_ids
        state.group_ids.add(chat_id)
        save_group(
            chat_id,
            user_info.get("chat_title"),
            user_info.get("username"),
            chat_type
        )
        if is_new_group:
            log_action("INFO", f"📢 New group tracked for broadcasting", user_info)