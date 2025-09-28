from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from Sakura.Interface.messages import START_MESSAGES, HELP_MESSAGES, BROADCAST_MESSAGES
from Sakura.Core.config import UPDATE_LINK, SUPPORT_LINK
from Sakura import state

def start_menu() -> InlineKeyboardMarkup:
    """Create initial start keyboard with Info and Hi buttons"""
    keyboard = [
        [
            InlineKeyboardButton(START_MESSAGES["button_texts"]["info"], callback_data="start_info"),
            InlineKeyboardButton(START_MESSAGES["button_texts"]["hi"], callback_data="start_hi")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def info_menu(bot_username: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for start info (original start buttons)"""
    keyboard = [
        [
            InlineKeyboardButton(START_MESSAGES["button_texts"]["updates"], url=UPDATE_LINK),
            InlineKeyboardButton(START_MESSAGES["button_texts"]["support"], url=SUPPORT_LINK)
        ],
        [
            InlineKeyboardButton(START_MESSAGES["button_texts"]["add_to_group"],
                               url=f"https://t.me/{bot_username}?startgroup=true")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def help_menu(expanded: bool = False) -> InlineKeyboardMarkup:
    """Create help command keyboard"""
    if expanded:
        button_text = HELP_MESSAGES["button_texts"]["minimize"]
        callback_data = "help_minimize"
    else:
        button_text = HELP_MESSAGES["button_texts"]["expand"]
        callback_data = "help_expand"

    keyboard = [[InlineKeyboardButton(button_text, callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)

def broadcast_menu() -> InlineKeyboardMarkup:
    """Create broadcast target selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                BROADCAST_MESSAGES["button_texts"]["users"].format(count=len(state.user_ids)),
                callback_data="bc_users"
            ),
            InlineKeyboardButton(
                BROADCAST_MESSAGES["button_texts"]["groups"].format(count=len(state.group_ids)),
                callback_data="bc_groups"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)