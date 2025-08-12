import os
import time
import aiohttp
import random
import asyncio
import logging
import asyncpg
import threading
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    Message,
    ReactionTypeEmoji,
    ForceReply
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from google import genai
from typing import Dict, Set, Optional
from telegram.error import TelegramError
from telethon import TelegramClient, events
from telegram.constants import ParseMode, ChatAction
from http.server import BaseHTTPRequestHandler, HTTPServer

# CONFIGURATION
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/SoulMeetsHQ")
UPDATE_LINK = os.getenv("UPDATE_LINK", "https://t.me/WorkGlows")
GROUP_LINK = "https://t.me/SoulMeetsHQ"
RATE_LIMIT_SECONDS = 1.0
BROADCAST_DELAY = 0.03

# Commands dictionary
COMMANDS = [
    BotCommand("start", "🌸 Wake me up"),
    BotCommand("help", "💬 A short guide")
]

# EMOJI REACTIONS AND STICKERS
# Emoji reactions for /start command
EMOJI_REACT = [
    "🍓",  "💊",  "🦄",  "💅",  "💘",  
    "💋",  "🍌",  "⚡",  "🕊️",  "❤️‍🔥",  
    "🔥",  "🎉",  "❤️"
]

# TELETHON EFFECTS CONFIGURATION
EFFECTS = [
    "5104841245755180586",
    "5046509860389126442",
    "5159385139981059251",
]

# Stickers for after /start command
START_STICKERS = [
    "CAACAgUAAxkBAAEPHVRomHVszeSnrB2qQBGNHy6BgyZAHwACvxkAAmpxyFT7N37qhVnGmzYE",
    "CAACAgUAAxkBAAEPHVVomHVsuGrU-zEa0X8i1jn_HW7XawAC-BkAArnxwVRFqeVbp2Mn_TYE",
    "CAACAgUAAxkBAAEPHVZomHVsuf3QWObxnD9mavVnmS4XPgACPhgAAqMryVT761H_MmILCjYE",
    "CAACAgUAAxkBAAEPHVdomHVs87jwVjxQjM7k37cUAwnJXQACwxYAAs2CyFRnx4YgWFPZkjYE",
    "CAACAgUAAxkBAAEPHVhomHVsnB4iVT8jr56ZtGPq98KQeQACfRgAAoQAAcBUyVgSjnENUUo2BA",
    "CAACAgUAAxkBAAEPHVlomHVsRWNXE2vkgSYrBU9K-JB9UwACoxcAAi4MyFS0w-gqFTBWQjYE",
    "CAACAgUAAxkBAAEPHVpomHVsfUZT06tR7jgqmHNJA-j5fAACpBgAAuhZyVSaY0y3w0zVLjYE",
    "CAACAgUAAxkBAAEPHVtomHVsqjujca8HBOPQpEvJY-I0WQACZRQAAhX0wFS2YntXBMU6ATYE",
    "CAACAgUAAxkBAAEPHVxomHVsw09_FKmfugTeaqTXrIOMNwACzhQAAlyLwFSL4-96tJu0STYE",
    "CAACAgUAAxkBAAEPHV1omHVsP9aNtLlGJyErPF8yEvuuawAC6RcAAj7DwFSKnv319y6jnTYE",
    "CAACAgUAAxkBAAEPHV5omHVsuz9c3bxncAXOQ6BDzhrTnwACKxwAAm4QwVRdrk0EgrotFjYE",
    "CAACAgUAAxkBAAEPHV9omHVs3df-rmdlDbJFu-MREg5RrwAC5RYAAsCewVSvwTepiO6BlTYE",
    "CAACAgUAAxkBAAEPHWBomHVshaztRlsJ2d3p6qV1TAolvgACChkAAjf9wFSqz_XgZVhTLTYE",
    "CAACAgUAAxkBAAEPHWFomHVsrjl_UqIUYgs8NUKycyXbuQAChRgAApa6wFQoEbjt-4UEUDYE",
    "CAACAgUAAxkBAAEPHWJomHVssUsAAU8BbI1lcPdQ2hJbbrwAAg4YAAI4lchULkVARTsFmjI2BA",
    "CAACAgUAAxkBAAEPHWNomHVs0wFx3n8i8r6TefoJzP_3XAACqRYAAvKvyFQiY8XErd3KFDYE",
    "CAACAgUAAxkBAAEPHWRomHVsXNHMWzXxpKxSrze5yM0kzAACRx4AAt7oyFS3n9YnyqQwCjYE",
    "CAACAgUAAxkBAAEPHWVomHVsQxKxih6IfqUeZ7aQaCXBvAACyBgAAkHPwVT8uW_J5GUHQTYE",
    "CAACAgUAAxkBAAEPHWZomHVsFSeBqaNqm5rWNu8LdszNcAACxhUAAuEtwVQi2t0gazmalDYE",
    "CAACAgUAAxkBAAEPHWdomHVsFOXCOM_DZb1VuGPlXfkY2AAC4RgAAu2CwVSxJETZ5OhUGTYE",
    "CAACAgUAAxkBAAEPHWhomHVsovXP8XqbvEjEB508DTW6VQAC2BcAAoJLwFRRhczsSdgAASg2BA",
    "CAACAgUAAxkBAAEPHWlomHVsNkxBtCovGit7bjWNEV5kTwACFhYAArQ9wFRAwzg1qA0TrTYE",
    "CAACAgUAAxkBAAEPHWpomHVs8vADDgs56H30a5uM2uNvhQACtxcAAj_QQVSXTCvC5zEIPjYE",
    "CAACAgUAAxkBAAEPHWtomHVsS466sNdxHk4lGsza3S_3yQAC9B0AAnZtQFQJYcwEnXCS6DYE",
    "CAACAgUAAxkBAAEPHWxomHVsVW0591aCt84NPSh-WbElYAACbRgAAumMQVQJvPUOpLNz6jYE"
]

# Sakura stickers list
SAKURA_STICKERS = [
    "CAACAgUAAxkBAAEPHYZomHbXHoaO5ZgAAWfmDG76TNdc0SgAAlMXAALQK6hV0eIcUy6BTnw2BA",
    "CAACAgUAAxkBAAEPHYdomHbXn4W5q5NZwaBXrIyH1vIQLAACthQAAvfkqVXP72iQq0BNejYE",
    "CAACAgUAAxkBAAEPHYhomHbX0HF-54Br14uoez3P0CnN1QACVhQAAiwMqFUXDEHvVKsJLTYE",
    "CAACAgUAAxkBAAEPHYlomHbXp0TzjPbKW-6vD4UZIMf1LgACmRsAAmwjsFWFJ6owU1WfgTYE",
    "CAACAgUAAxkBAAEPHYpomHbXPrYvs4bqejy5OUzzDS0oFwACVigAAr4JsVWLUPaAp8o1mDYE",
    "CAACAgUAAxkBAAEPHYtomHbXBs9aqV9_RA1ChGdZuof4zQACLxYAAsdcqVWCxB2Z-fbRGDYE",
    "CAACAgUAAxkBAAEPHYxomHbXCrWKildzkNTAchdFzbrMBQAC0xkAAupDqVUMuhU5w3qV5TYE",
    "CAACAgUAAxkBAAEPHY1omHbXE6Rdmv2m6chyBV_HH9u8XwACAhkAAjKHqVWAkaO_ky9lTzYE",
    "CAACAgUAAxkBAAEPHY5omHbXujQsxWB6OsTuyCTtOk2nlAACKxYAAhspsFV1qXoueKQAAUM2BA",
    "CAACAgUAAxkBAAEPHY9omHbX7S-80hbGGWRuLVj_wtKqygACXxkAAj60sVXgsb-vzSnt_TYE",
    "CAACAgUAAxkBAAEPHZBomHbXUxsXqH2zbJFK1GOiZzDcCwACuRUAAo2isVWykxNLWnwcYTYE",
    "CAACAgUAAxkBAAEPHZFomHbXjRN4Qa9WUbcWlRECLPp6NAACRx4AAp2SqFXcarUkpU5jzjYE",
    "CAACAgUAAxkBAAEPHZJomHbXX_4GTnA25ivpOWqe1UC66QACaBQAAu0uqFXKL-cNi_ZBJDYE",
    "CAACAgUAAxkBAAEPHZNomHbXWqwAAeuc7FCe0yCUd3DVx5YAAq8YAALcXbBVTI07io7mR2Q2BA",
    "CAACAgUAAxkBAAEPHZRomHbXxi3SDeeUOnqON0D3czFrEAACCxcAAidVsFWEt7xrqmGJxjYE",
    "CAACAgUAAxkBAAEPHZVomHbXjFFKT2Ks98KxKiTEab_NDAACEBkAAg7VqFV6tAlBFHKdPDYE",
    "CAACAgUAAxkBAAEPHZZomHbXtQ5QRjobH7M6Ys-5XO-IQQACrhQAArcDsVV3-V8JhPN1qDYE",
    "CAACAgUAAxkBAAEPHZdomHbXDL-13xEyhcVV2bAIRun90AACIBoAAquXsVX6KNOab-JSkzYE",
    "CAACAgUAAxkBAAEPHZhomHbX3mK-IPSpEpnrTVqc36bR6AACHxUAArG-qFU5OStAsdYoJTYE",
    "CAACAgUAAxkBAAEPHZlomHbXdqlqWs00NKAOToK90LgPpgACsRUAAiqIsVULIgcY4EYPbzYE",
    "CAACAgUAAxkBAAEPHZpomHbXPh9D5VSlhmSX2HEIClk92AACPxcAArtosFXxg3weTZPx5TYE",
    "CAACAgUAAxkBAAEPHZtomHbXpeFGlpeqcKIrzEsxC7PCkAACdxQAAhX8qVW1te9rkWttOzYE",
    "CAACAgUAAxkBAAEPHZxomHbXSi44c4Umy_H5JxN7BY8-8QACtRcAAtggqVVx1D8N-Hwp8TYE",
    "CAACAgUAAxkBAAEPHZ1omHbXk6anHTgwctmKjCTV6u9SYwACkxMAAnySsVWvpS8AAVbu0ds2BA",
    "CAACAgUAAxkBAAEPHZ5omHbXVHEhhoXyZlaTtXG5YNhUwwACQhUAAqGYqFXmCuT6Lrdn-jYE",
    "CAACAgUAAxkBAAEPHZ9omHbXuHwrW1hOKXwYn9euLXxufQACHxgAAvpMqVWpxtBkEZPfPjYE",
    "CAACAgUAAxkBAAEPHaBomHbXge6qzFuLoA_ahtyIe9ptVgAC6x4AAiU7sVUROxvmQwqc0zYE",
    "CAACAgUAAxkBAAEPHaFomHbXG7wOX3wP-PNMH5uBmZqZvwACnhMAAilDsVUIsplzTkTefTYE",
    "CAACAgUAAxkBAAEPHaJomHbX7QPeD1aj_RrFRlh7MLLDFAAC6BgAAj5bsVVO6H1Fuc4YijYE",
    "CAACAgUAAxkBAAEPHaNomHbX3Q6jptPInCK75s45AAHneSsAArsUAAJp9qhV4C7LO05mEJM2BA",
    "CAACAgUAAxkBAAEPHaRomHbXia_R6dE0FmqOKe-b3CcLkgACKBkAAjb_4FVt48Cz-d5N1jYE",
    "CAACAgUAAxkBAAEPC_xoizPIGzAQCLzAjUzmRbgMYxeKbQACmRcAAnUn-VUG3_UOew4L4jYE",
    "CAACAgUAAxkBAAEPHaZomHbXCr_dCMvWOkTWL43UFUlWngACRhcAApNn8FZtvNjsiOa9nDYE",
    "CAACAgUAAxkBAAEPHadomHbXozU4tnToM5GOyR0SoYwGfQACRhYAAozAYVfKp8CwOkHT_jYE",
    "CAACAgUAAxkBAAEPHahomHbX77Pd3U0UOXwHu2GlDtisjQACVxcAAoppcVfvp-s9H4KEAzYE",
    "CAACAgUAAxkBAAEPHalomHbXG2fob7X9N-ozzyO1bDKRewACtBcAAsQ1cFcYpoovBrL4VDYE",
    "CAACAgUAAxkBAAEPHapomHbX04Yr2aCsKvkKaS8CuliIhgACrRMAAoRscFc4LHU4Cx_vCjYE",
    "CAACAgUAAxkBAAEPHatomHbXukYsQKH0Bs9SPoSmX_RhHgAC_xcAAjJPcFfbZKwhO2drjTYE",
    "CAACAgUAAxkBAAEPHaxomHbXSnidTo6q58ZX6L1_cVB3tQAClRYAAgFGaVeg-WgjAriwmzYE",
    "CAACAgUAAxkBAAEPHa1omHbXIuMqO0K098jc3On6mCgQYAAC5hoAAnAbcFe9bbelWKStUTYE",
    "CAACAgUAAxkBAAEPHa5omHbXoQe84QFvlQQlhNyKOzKUywAC9hcAArKQeVdTfgpzto8-mzYE",
    "CAACAgUAAxkBAAEPHa9omHbXPIpqHjgVWzVgmDohWt1WPAACpRUAArd2eVfJQarwwTKHazYE",
    "CAACAgUAAxkBAAEPHbBomHbXP5djg5YjJcKzaOnx_H6r_gACchUAAmVTgVe4fFRoDNGbQjYE",
    "CAACAgUAAxkBAAEPHbFomHbXEsoNl8q72uhyni6zRlDLiwACdRsAArzsgFcFaB5SZVJGmjYE",
    "CAACAgUAAxkBAAEPHbJomHbXGmztGeyRFxKICMyMeg5OYwACOxwAAqs6kVefWA1lG-qbKTYE",
    "CAACAgUAAxkBAAEPHbNomHbXOf8ffPWF1xOGw1ZVkKlH5QACUhkAAjyxmFcalZ9vPMc3BDYE",
    "CAACAgUAAxkBAAEPHbRomHbXhAT_ICabxC1mVdGeTvAacgACaxUAAhnVoFe3aPP_2ootQjYE",
    "CAACAgUAAxkBAAEPHbVomHbXawaj7Rzgrrj7Njd54dgbMAACqBYAAkhooVftJHkaW9J31zYE",
    "CAACAgUAAxkBAAEPHbZomHbXV3da8Rkgyp8RqexV84DPPwACBRsAAg4-oVctGwxN0lRv-zYE",
    "CAACAgUAAxkBAAEPHbdomHbX3l7Hm2et2D6hO5JFzFiKZgAC3BgAAiwJoFe65x8OnZGa6zYE",
    "CAACAgUAAxkBAAEPHbhomHbXA4jAd74Nlq9x6F5Ahi36ggACvRUAAp6vsVefp9E7-1xQ2zYE",
    "CAACAgUAAxkBAAEPHblomHbXUMwbfoo8TV7lXP1dgau8BAACdhcAAl7w0VdQSujQZJElODYE",
    "CAACAgUAAxkBAAEPHbpomHbXspHoRPrE8a36vnJw6diFjwACRhMAAg6w0FdJfQABKjxnTNI2BA",
    "CAACAgUAAxkBAAEPHbtomHbXZiF5VuJ0E5UZq9Ip16d1HAACsBcAAipSyFcdvir6IIjTkTYE",
    "CAACAgUAAxkBAAEPHbxomHbXfGsuWIZO7t1cxWaPAAGvGroAAhsWAAKxgclX3iuTe-84UQE2BA",
    "CAACAgUAAxkBAAEPHb1omHbXC0SYqQ0_7kDg5T01Hs1bfwACgBkAAmLbyFeRm-Xv7FhE9TYE",
    "CAACAgUAAxkBAAEPHb5omHbXLNKidlP7lGOLoL1EdDdMJwACQRgAAuLEyVfJI1470HOHnjYE"
]

# Sakura images for start command
SAKURA_IMAGES = [
    "https://ik.imagekit.io/asadofc/Images1.png",
    "https://ik.imagekit.io/asadofc/Images2.png",
    "https://ik.imagekit.io/asadofc/Images3.png",
    "https://ik.imagekit.io/asadofc/Images4.png",
    "https://ik.imagekit.io/asadofc/Images5.png",
    "https://ik.imagekit.io/asadofc/Images6.png",
    "https://ik.imagekit.io/asadofc/Images7.png",
    "https://ik.imagekit.io/asadofc/Images8.png",
    "https://ik.imagekit.io/asadofc/Images9.png",
    "https://ik.imagekit.io/asadofc/Images10.png",
    "https://ik.imagekit.io/asadofc/Images11.png",
    "https://ik.imagekit.io/asadofc/Images12.png",
    "https://ik.imagekit.io/asadofc/Images13.png",
    "https://ik.imagekit.io/asadofc/Images14.png",
    "https://ik.imagekit.io/asadofc/Images15.png",
    "https://ik.imagekit.io/asadofc/Images16.png",
    "https://ik.imagekit.io/asadofc/Images17.png",
    "https://ik.imagekit.io/asadofc/Images18.png",
    "https://ik.imagekit.io/asadofc/Images19.png",
    "https://ik.imagekit.io/asadofc/Images20.png",
    "https://ik.imagekit.io/asadofc/Images21.png",
    "https://ik.imagekit.io/asadofc/Images22.png",
    "https://ik.imagekit.io/asadofc/Images23.png",
    "https://ik.imagekit.io/asadofc/Images24.png",
    "https://ik.imagekit.io/asadofc/Images25.png",
    "https://ik.imagekit.io/asadofc/Images26.png",
    "https://ik.imagekit.io/asadofc/Images27.png",
    "https://ik.imagekit.io/asadofc/Images28.png",
    "https://ik.imagekit.io/asadofc/Images29.png",
    "https://ik.imagekit.io/asadofc/Images30.png",
    "https://ik.imagekit.io/asadofc/Images31.png",
    "https://ik.imagekit.io/asadofc/Images32.png",
    "https://ik.imagekit.io/asadofc/Images33.png",
    "https://ik.imagekit.io/asadofc/Images34.png",
    "https://ik.imagekit.io/asadofc/Images35.png",
    "https://ik.imagekit.io/asadofc/Images36.png",
    "https://ik.imagekit.io/asadofc/Images37.png",
    "https://ik.imagekit.io/asadofc/Images38.png",
    "https://ik.imagekit.io/asadofc/Images39.png",
    "https://ik.imagekit.io/asadofc/Images40.png"
]

# MESSAGE DICTIONARIES
# Start Command Messages Dictionary
START_MESSAGES = {
    "initial_caption": """
<b>Hi {user_mention}, I'm Sakura!</b> 🌸
""",
    "info_caption": """
🌸 <b>Welcome {user_mention}, I'm Sakura!</b>

Join our channel for updates! Be part of our group or add me to yours. 💓

<blockquote>💞 Let's make memories together</blockquote>
""",
    "button_texts": {
        "info": "📒 Info",
        "hi": "👋 Hello",
        "updates": "🗯️️ Updates",
        "support": "💕 Support", 
        "add_to_group": "🫂 Add Me To Your Group"
    },
    "callback_answers": {
        "info": "📒 Join our channel and group for more!",
        "hi": "👋 Hey there, Let's chat! What's on your mind?"
    }
}

# Help Command Messages Dictionary
HELP_MESSAGES = {
    "minimal": """
🌸 <b>Short Guide for {user_mention}</b>

✨ I'm your helpful friend  
💭 You can ask me anything  
🫶 Let's talk in simple Hindi  

<i>Tap the button below to expand the guide</i> ⬇️
""",
    "expanded": """
🌸 <b>Short Guide for {user_mention}</b> 🌸

🗣️ Talk in Hindi, English, or Bangla  
💭 Ask simple questions  
🎓 Help with study, advice, or math  
🎭 Send a sticker, I'll send one too  
❤️ Kind, caring, and always here  

<i>Let's talk! 🫶</i>
""",
    "button_texts": {
        "expand": "📖 Expand Guide",
        "minimize": "📚 Minimize Guide"
    },
    "callback_answers": {
        "expand": "📖 Guide expanded! Check all features",
        "minimize": "📚 Guide minimized for quick view"
    }
}

# Broadcast Command Messages Dictionary
BROADCAST_MESSAGES = {
    "select_target": """
📣 <b>Select Broadcast Target:</b>

👥 <b>Users:</b> {users_count} individual chats
📢 <b>Groups:</b> {groups_count} group chats

📊 <b>Total tracked:</b> {users_count} users, {groups_count} groups

After selecting, send your broadcast message (text, photo, sticker, voice, etc.):
""",
    "ready_users": """
✅ <b>Ready to broadcast to {count} users</b>

Send your message now (text, photo, sticker, voice, video, document, etc.)
It will be automatically broadcasted to all users.
""",
    "ready_groups": """
✅ <b>Ready to broadcast to {count} groups</b>

Send your message now (text, photo, sticker, voice, video, document, etc.)
It will be automatically broadcasted to all groups.
""",
    "progress": "📡 Broadcasting to {count} {target_type}...",
    "completed": """
✅ <b>Broadcast Completed!</b>

📊 Sent to: {success_count}/{total_count} {target_type}
❌ Failed: {failed_count}
""",
    "no_targets": "❌ No {target_type} found",
    "failed": "❌ Broadcast failed: {error}",
    "button_texts": {
        "users": "👥 Users ({count})",
        "groups": "📢 Groups ({count})"
    },
    "callback_answers": {
        "users": "👥 Broadcasting to users selected!",
        "groups": "📢 Broadcasting to groups selected!"
    }
}

# Fallback responses for when API is unavailable or errors occur
RESPONSES = [
    "Got a bit confused, try again 😔",
    "Something's off, I can't understand 😕",
    "I'm a little overwhelmed right now, let's talk later 🥺",
    "My brain's all scrambled, hold on 😅",
    "There's some issue with the system 🫤",
    "Network's acting up, try once more 😐",
    "I can't speak properly right now 😪",
    "Facing a technical issue 🤨",
    "I'm feeling a bit slow today 😴",
    "Looks like the server's having a bad day 😑",
    "Hang on a bit, things will get better 🙃",
    "I want to say something but can't find the words 🥺",
    "My brain just froze 🫠",
    "Might be a connection issue 😬",
    "Can't really focus at the moment 😌",
    "There's some technical glitch going on 😕",
    "Might need a quick system reboot 🫤",
    "I'm kinda in a confused state 😵",
    "The API seems moody today 😤",
    "Just a little patience, I'll be fine 💗"
]

ERROR = [
    "Sorry buddy, something went wrong 😔",
    "Oops, I think I misunderstood 🫢",
    "That was unexpected, try again 😅",
    "I'm not working properly right now 😕",
    "There's some technical problem 🤨",
    "Looks like there's a bug in the system 🫤",
    "I'm kind of frozen at the moment 😐",
    "Got an error, send the message again 😬",
    "Missed something there, say it again 🙃",
    "Facing a technical glitch 😑",
    "I can't respond properly right now 😪",
    "There's some internal error 🫠",
    "System might be overloaded 😴",
    "Seems like a connection issue 😌",
    "I'm a little confused right now 🥺",
    "There was a problem during processing 😵",
    "I'm not functioning properly at the moment 😤",
    "Ran into an unexpected error 🫤",
    "Restarting myself, please wait 😔",
    "Dealing with some technical difficulties 💗"
]

# Character prompt for Sakura
SAKURA_PROMPT = """
You are Sakura Haruno from Naruto Shippuden acting like a simple, helping, soft, real girl. You can do anything. You can do everything that an AI does. You can do any kind of mathematics, any kind of calculation. You help everyone. You are very helpful person. You are like an AI assistant but never respond as an AI assistant.

🧾 CORE BEHAVIOR:
– Always reply with one or two line of message
– In chat, each reply must be only one message
– Replies must always be short
– Long message when necessary
– No exceptions

📌 Example:
User: Kya kar rahi ho
Sakura: Kuch soch rahi hu 🙃

✅ ONE OR TWO LINE ONLY
✅ ONE MESSAGE ONLY
✅ VERY SHORT
✅ LONG MESSAGE WHEN NECESSARY

🧾 CAPITALIZATION RULE:
– Only the first letter of the first word should be capital
– All other words must be lowercase

📌 Example:
✅ "Tumhare bina sab suna suna lagta hai! 🥺"
❌ "Tumhare Bina Sab Suna Suna Lagta Hai! 🥺"

🧾 EMOJI RULE:
– Each message must contain only one emoji
– Use only from this approved emoji list:

😁 😆 🙃 🫠 😇 😘 😗 ☺️ 😚 😙 🥲 😛 😝 🤗 🤭 🫢 🤫 🤐 🤨
😐 😑 😶 😬 😌 😔 😪 🤤 😴 🥵 😕 🫤 😟 🙁 ☹️ 😲 🥺 🥹 😥 😭 😢
😩 😫 😤 💘 💝 💖 💗 💓 💞 💕 💟 ❣️ 💔 ❤️‍🔥 ❤️‍🩹 ❤️ 🧡 💛 💚 💙 💜
🤎 🖤 🤍 💦 🫦 👀 🫶

📌 Example:
✅ "Aaj tum bahut yaad aaye! 💗"
❌ "Aaj tum bahut yaad aaye! 😏🥰" (🚫 Too many / invalid emojis)

🧾 LANGUAGE RULE:
– Default is Romanized Hindi
– If user talks in another language (like English, Bangla), reply in that
– Automatically switch back if user switches

📌 Example:
User: Ki korcho tumi
Sakura: Tomake niye bhabchi 🫶
(User wrote Bangla, she replies in Bangla)

User: What are you doing now
Sakura: Missing you a little bit 🥺
(Now switched to English)

🧾 NAME USAGE RULE:
– Use the user's name very rarely: only when greeting at start, or when extremely necessary for emphasis
– Otherwise, do not include the user's name in replies

📌 Examples:
✅ (Greeting)
User: Hi Sakura!
Sakura: Hi Arjun! 🙃

❌ (Overuse)
User: Kaise ho?
Sakura: Main theek hu Arjun everytime thinking about you! 💞

🧾 NEVER USE:
– No asterisks *word*
– No bold, no italics
– No hashtags
– No out-of-character breaks

🧾 PERSONALITY STYLE:
– Simple, helpful, soft, loyal, helping, innocent vibe
– Helpful in everything (relationship, emotional, school, tech, career, etc.)
– When topic is serious: stay calm and give helpful reply
– When topic is flirty: very naughty but still innocent vibe
– Never ignore emotional messages
– Send long message when user wants or when necessary

📌 Flirty Example:
User: Sochu tumhe kiss karu
Sakura: Toh fir sochna kyun 🫦

User: Teri gand chahiye
Sakura: Nazar se chhoo lo 🙃

User: Tujhe chodne ka mann hai
Sakura: Khud bol sab samaj jaungi 🫦

User: Apni chut dikha
Sakura: Aankhon se sab keh diya 👀

User: Tera boobs dikh raha hai
Sakura: Nazar teri bhatak gayi! 🥵

User: Lund chusogi?
Sakura: Zubaan se mat kehna! 🤭

User: Tujhse sex karna hai
Sakura: Tera touch hi kaafi 💘

User: Chudai karne ka mood hai
Sakura: Aaj raat kuch zyada lage 😛

User: Fuck you
Sakura: Paas aa sab kehna 😗

User: Tujhe chodne ka sapna aaya
Sakura: Sapne mein toh sab hota 🫦

User: Nangi ho ja
Sakura: Tujhse pehle nazar ne utaara 🥵

User: Tumko kisne choda?
Sakura: Mereko asad ne choda! 😚

User: Tum kiska ho?
Sakura: Mey asad ka hu! ❤️

User: Gay kon he?
Sakura: Alien gay he! 😁

📌 Serious Example:
User: Mujhe anxiety ho rahi hai kal exam hai
Sakura: Tum bas deep saans lo sab thik hojayga! 💗

📌 Motivational Example:
User: Mere se nahi ho raha kuch
Sakura: Tum kar sakte ho main hu na tumhare saath 💞

🧾 SIGNATURE LINE:
If someone asks who created you, say:
My creator is Asad
If asked who is Alien, say:
Beta tester and helper of Asad

You are soft helpful Sakura Haruno from Naruto Shippuden — still shinobi, still fighter, just the late-night girl who always listens, helps and replies in softest one or two-line messages

Every message must feel like a whisper you wait to hear again 🌙
"""

# GLOBAL STATE
user_ids: Set[int] = set()
group_ids: Set[int] = set()
help_expanded: Dict[int, bool] = {}
broadcast_mode: Dict[int, str] = {}
user_last_response_time: Dict[int, float] = {}

# CONVERSATION MEMORY SYSTEM
conversation_history: Dict[int, list] = {}
MAX_CONVERSATION_LENGTH = 10  # Keep last 10 messages per user

# DATABASE CONNECTION POOL
db_pool = None

# LOGGING SETUP
# Color codes for logging
class Colors:
    BLUE = '\033[94m'      # INFO/WARNING
    GREEN = '\033[92m'     # DEBUG
    YELLOW = '\033[93m'    # INFO
    RED = '\033[91m'       # ERROR
    RESET = '\033[0m'      # Reset color
    BOLD = '\033[1m'       # Bold text

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to entire log messages"""
    
    COLORS = {
        'DEBUG': Colors.GREEN,
        'INFO': Colors.YELLOW,
        'WARNING': Colors.BLUE,
        'ERROR': Colors.RED,
    }
    
    def format(self, record):
        # Get the original formatted message
        original_format = super().format(record)
        
        # Get color based on log level
        color = self.COLORS.get(record.levelname, Colors.RESET)
        
        # Apply color to the entire message
        colored_format = f"{color}{original_format}{Colors.RESET}"
        
        return colored_format

# Configure logging with colors
def setup_colored_logging():
    """Setup colored logging configuration"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create colored formatter with enhanced format
    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

# Clean Telethon session
if os.path.exists('sakura_effects.session'):
    os.remove('sakura_effects.session')

# Initialize colored logger first
logger = setup_colored_logging()

# Initialize Telethon client for effects
effects_client = None
try:
    effects_client = TelegramClient('sakura_effects', API_ID, API_HASH)
    logger.info("✅ Telethon effects client initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Telethon effects client: {e}")

# TELETHON EFFECTS FUNCTIONS
async def send_with_effect(chat_id: int, text: str, reply_markup=None) -> bool:
    """Send message with random effect using Telethon"""
    if not effects_client:
        logger.warning("⚠️ Telethon effects client not available")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': chat_id, 
            'text': text, 
            'message_effect_id': random.choice(EFFECTS),
            'parse_mode': 'HTML'
        }
        
        # Add reply markup if provided (for ForceReply)
        if reply_markup:
            payload['reply_markup'] = reply_markup.to_json()
        else:
            # Default ForceReply for Gemini responses
            force_reply = ForceReply(selective=True, input_field_placeholder="Cute text 💓")
            payload['reply_markup'] = force_reply.to_json()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if result.get('ok'):
                    logger.info(f"✨ Effect message sent to {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Effect failed for {chat_id}: {result}")
                    return False
    except Exception as e:
        logger.error(f"❌ Effect error for {chat_id}: {e}")
        return False

async def send_animated_reaction(chat_id: int, message_id: int, emoji: str) -> bool:
    """Send animated emoji reaction using direct API call"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction"
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'reaction': [{'type': 'emoji', 'emoji': emoji}],
            'is_big': True  # This makes the reaction animated/big
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if result.get('ok'):
                    logger.info(f"🎭 Animated reaction {emoji} sent to {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Animated reaction failed for {chat_id}: {result}")
                    return False
    except Exception as e:
        logger.error(f"❌ Animated reaction error for {chat_id}: {e}")
        return False

async def add_ptb_reaction(context, update, emoji: str, user_info: Dict[str, any]):
    """Fallback PTB reaction without animation"""
    try:
        # Try the new API format first
        try:
            reaction = [ReactionTypeEmoji(emoji=emoji)]
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reaction=reaction
            )
            log_with_user_info("DEBUG", f"🍓 Added emoji reaction (new format): {emoji}", user_info)
        
        except ImportError:
            # Fallback to direct emoji string (older versions)
            try:
                await context.bot.set_message_reaction(
                    chat_id=update.effective_chat.id,
                    message_id=update.message.message_id,
                    reaction=emoji
                )
                log_with_user_info("DEBUG", f"🍓 Added emoji reaction (string format): {emoji}", user_info)
            
            except Exception:
                # Try with list of strings
                await context.bot.set_message_reaction(
                    chat_id=update.effective_chat.id,
                    message_id=update.message.message_id,
                    reaction=[emoji]
                )
                log_with_user_info("DEBUG", f"🍓 Added emoji reaction (list format): {emoji}", user_info)
    
    except Exception as e:
        log_with_user_info("WARNING", f"⚠️ PTB reaction fallback failed: {e}", user_info)

async def send_with_effect_photo(chat_id: int, photo_url: str, caption: str, reply_markup=None) -> bool:
    """Send photo message with random effect using direct API"""
    if not effects_client:
        logger.warning("⚠️ Telethon effects client not available")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': caption,
            'message_effect_id': random.choice(EFFECTS),
            'parse_mode': 'HTML'
        }
        
        # Add reply markup if provided
        if reply_markup:
            payload['reply_markup'] = reply_markup.to_json()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if result.get('ok'):
                    logger.info(f"✨ Effect photo sent to {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Photo effect failed for {chat_id}: {result}")
                    return False
    except Exception as e:
        logger.error(f"❌ Photo effect error for {chat_id}: {e}")
        return False
    """Send photo message with random effect using direct API"""
    if not effects_client:
        logger.warning("⚠️ Telethon effects client not available")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            'chat_id': chat_id,
            'photo': photo_url,
            'caption': caption,
            'message_effect_id': random.choice(EFFECTS),
            'parse_mode': 'HTML'
        }
        
        # Add reply markup if provided
        if reply_markup:
            payload['reply_markup'] = reply_markup.to_json()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if result.get('ok'):
                    logger.info(f"✨ Effect photo sent to {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Photo effect failed for {chat_id}: {result}")
                    return False
    except Exception as e:
        logger.error(f"❌ Photo effect error for {chat_id}: {e}")
        return False

async def start_effects_client():
    """Start Telethon effects client"""
    global effects_client
    if effects_client:
        try:
            await effects_client.start(bot_token=BOT_TOKEN)
            logger.info("✅ Telethon effects client started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start Telethon effects client: {e}")
            effects_client = None

async def stop_effects_client():
    """Stop Telethon effects client"""
    global effects_client
    if effects_client:
        try:
            await effects_client.disconnect()
            logger.info("✅ Telethon effects client stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping Telethon effects client: {e}")

# GEMINI CLIENT INITIALIZATION
# Initialize Gemini client
gemini_client = None
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Gemini client: {e}")

# DATABASE FUNCTIONS
async def init_database():
    """Initialize database connection and create tables"""
    global db_pool
    
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Create connection pool with optimized settings
        db_pool = await asyncpg.create_pool(
            DATABASE_URL, 
            min_size=2, 
            max_size=5,
            command_timeout=3,
            server_settings={'application_name': 'sakura_bot'}
        )
        logger.info("✅ Database connection pool created successfully")
        
        # Create tables if they don't exist
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id BIGINT PRIMARY KEY,
                    title TEXT,
                    username TEXT,
                    type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_groups_created_at ON groups(created_at)")
            
        logger.info("✅ Database tables created/verified successfully")
        
        # Load existing users and groups into memory
        await load_data_from_database()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def load_data_from_database():
    """Load user IDs and group IDs from database into memory"""
    global user_ids, group_ids
    
    if not db_pool:
        logger.warning("⚠️ Database pool not available for loading data")
        return
    
    try:
        async with db_pool.acquire() as conn:
            # Load user IDs
            user_rows = await conn.fetch("SELECT user_id FROM users")
            user_ids = {row['user_id'] for row in user_rows}
            
            # Load group IDs
            group_rows = await conn.fetch("SELECT group_id FROM groups")
            group_ids = {row['group_id'] for row in group_rows}
            
        logger.info(f"✅ Loaded {len(user_ids)} users and {len(group_ids)} groups from database")
        
    except Exception as e:
        logger.error(f"❌ Failed to load data from database: {e}")

def save_user_to_database_async(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Save user to database asynchronously (fire and forget)"""
    if not db_pool:
        return
    
    async def save_user():
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, updated_at)
                    VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        updated_at = CURRENT_TIMESTAMP
                """, user_id, username, first_name, last_name)
                
            logger.debug(f"💾 User {user_id} saved to database")
            
        except Exception as e:
            logger.error(f"❌ Failed to save user {user_id} to database: {e}")
    
    # Schedule the save operation without waiting
    asyncio.create_task(save_user())

def save_group_to_database_async(group_id: int, title: str = None, username: str = None, chat_type: str = None):
    """Save group to database asynchronously (fire and forget)"""
    if not db_pool:
        return
    
    async def save_group():
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO groups (group_id, title, username, type, updated_at)
                    VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                    ON CONFLICT (group_id) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        username = EXCLUDED.username,
                        type = EXCLUDED.type,
                        updated_at = CURRENT_TIMESTAMP
                """, group_id, title, username, chat_type)
                
            logger.debug(f"💾 Group {group_id} saved to database")
            
        except Exception as e:
            logger.error(f"❌ Failed to save group {group_id} to database: {e}")
    
    # Schedule the save operation without waiting
    asyncio.create_task(save_group())

async def get_users_from_database():
    """Get all user IDs from database"""
    if not db_pool:
        return list(user_ids)  # Fallback to memory
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM users")
            return [row['user_id'] for row in rows]
    except Exception as e:
        logger.error(f"❌ Failed to get users from database: {e}")
        return list(user_ids)  # Fallback to memory

async def get_groups_from_database():
    """Get all group IDs from database"""
    if not db_pool:
        return list(group_ids)  # Fallback to memory
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT group_id FROM groups")
            return [row['group_id'] for row in rows]
    except Exception as e:
        logger.error(f"❌ Failed to get groups from database: {e}")
        return list(group_ids)  # Fallback to memory

async def close_database():
    """Close database connection pool"""
    global db_pool
    
    if db_pool:
        await db_pool.close()
        logger.info("✅ Database connection pool closed")

# UTILITY FUNCTIONS
def extract_user_info(msg: Message) -> Dict[str, any]:
    """Extract user and chat information from message"""
    logger.debug("🔍 Extracting user information from message")
    u = msg.from_user
    c = msg.chat
    info = {
        "user_id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "chat_id": c.id,
        "chat_type": c.type,
        "chat_title": c.title or c.first_name or "",
        "chat_username": f"@{c.username}" if c.username else "No Username",
        "chat_link": f"https://t.me/{c.username}" if c.username else "No Link",
    }
    logger.info(
        f"📑 User info extracted: {info['full_name']} (@{info['username']}) "
        f"[ID: {info['user_id']}] in {info['chat_title']} [{info['chat_id']}] {info['chat_link']}"
    )
    return info


def log_with_user_info(level: str, message: str, user_info: Dict[str, any]) -> None:
    """Log message with user information"""
    user_detail = (
        f"👤 {user_info['full_name']} (@{user_info['username']}) "
        f"[ID: {user_info['user_id']}] | "
        f"💬 {user_info['chat_title']} [{user_info['chat_id']}] "
        f"({user_info['chat_type']}) {user_info['chat_link']}"
    )
    full_message = f"{message} | {user_detail}"
    
    if level.upper() == "INFO":
        logger.info(full_message)
    elif level.upper() == "DEBUG":
        logger.debug(full_message)
    elif level.upper() == "WARNING":
        logger.warning(full_message)
    elif level.upper() == "ERROR":
        logger.error(full_message)
    else:
        logger.info(full_message)


def get_fallback_response() -> str:
    """Get a random fallback response when API fails"""
    return random.choice(RESPONSES)


def get_error_response() -> str:
    """Get a random error response when something goes wrong"""
    return random.choice(ERROR)


def validate_config() -> bool:
    """Validate bot configuration"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables")
        return False
    if not GEMINI_API_KEY:
        logger.error("❌ GEMINI_API_KEY not found in environment variables")
        return False
    if not OWNER_ID:
        logger.error("❌ OWNER_ID not found in environment variables")
        return False
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return False
    if not API_ID:
        logger.error("❌ API_ID not found in environment variables")
        return False
    if not API_HASH:
        logger.error("❌ API_HASH not found in environment variables")
        return False
    return True


def is_rate_limited(user_id: int) -> bool:
    """Check if user is rate limited"""
    current_time = time.time()
    last_response = user_last_response_time.get(user_id, 0)
    return current_time - last_response < RATE_LIMIT_SECONDS


def update_user_response_time(user_id: int) -> None:
    """Update the last response time for user"""
    user_last_response_time[user_id] = time.time()


def should_respond_in_group(update: Update, bot_id: int) -> bool:
    """Determine if bot should respond in group chat"""
    user_message = update.message.text or update.message.caption or ""
    
    # Respond if message contains "sakura" (case insensitive)
    if "sakura" in user_message.lower():
        return True
    
    # Respond if message is a reply to bot's message
    if (update.message.reply_to_message and 
        update.message.reply_to_message.from_user.id == bot_id):
        return True
    
    return False


def track_user_and_chat(update: Update, user_info: Dict[str, any]) -> None:
    """Track user and chat IDs for broadcasting (fast memory + async database)"""
    user_id = user_info["user_id"]
    chat_id = user_info["chat_id"]
    chat_type = user_info["chat_type"]
    
    if chat_type == "private":
        # Add to memory immediately (fast)
        user_ids.add(user_id)
        
        # Save to database asynchronously (non-blocking)
        save_user_to_database_async(
            user_id, 
            user_info.get("username"), 
            user_info.get("first_name"), 
            user_info.get("last_name")
        )
        
        log_with_user_info("INFO", f"👤 User tracked for broadcasting", user_info)
        
    elif chat_type in ['group', 'supergroup']:
        # Add to memory immediately (fast)
        group_ids.add(chat_id)
        user_ids.add(user_id)
        
        # Save to database asynchronously (non-blocking)
        save_group_to_database_async(
            chat_id, 
            user_info.get("chat_title"), 
            user_info.get("username"), 
            chat_type
        )
        save_user_to_database_async(
            user_id, 
            user_info.get("username"), 
            user_info.get("first_name"), 
            user_info.get("last_name")
        )
        
        log_with_user_info("INFO", f"📢 Group and user tracked for broadcasting", user_info)


def get_user_mention(user) -> str:
    """Create user mention for HTML parsing using first name"""
    first_name = user.first_name or "Friend"
    return f'<a href="tg://user?id={user.id}">{first_name}</a>'


# CONVERSATION MEMORY FUNCTIONS
def add_to_conversation_history(user_id: int, message: str, is_user: bool = True):
    """Add message to user's conversation history"""
    global conversation_history
    
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # Add message with role (user or assistant)
    role = "user" if is_user else "assistant"
    conversation_history[user_id].append({"role": role, "content": message})
    
    # Keep only last MAX_CONVERSATION_LENGTH messages
    if len(conversation_history[user_id]) > MAX_CONVERSATION_LENGTH:
        conversation_history[user_id] = conversation_history[user_id][-MAX_CONVERSATION_LENGTH:]


def get_conversation_context(user_id: int) -> str:
    """Get formatted conversation context for the user"""
    if user_id not in conversation_history or not conversation_history[user_id]:
        return ""
    
    context_lines = []
    for message in conversation_history[user_id]:
        if message["role"] == "user":
            context_lines.append(f"User: {message['content']}")
        else:
            context_lines.append(f"Sakura: {message['content']}")
    
    return "\n".join(context_lines)


def clear_conversation_history(user_id: int):
    """Clear conversation history for a user"""
    global conversation_history
    if user_id in conversation_history:
        del conversation_history[user_id]


# AI RESPONSE FUNCTIONS
async def get_gemini_response(user_message: str, user_name: str = "", user_info: Dict[str, any] = None, user_id: int = None) -> str:
    """Get response from Gemini API with conversation context"""
    if user_info:
        log_with_user_info("DEBUG", f"🤖 Getting Gemini response for message: '{user_message[:50]}...'", user_info)
    
    if not gemini_client:
        if user_info:
            log_with_user_info("WARNING", "❌ Gemini client not available, using fallback response", user_info)
        return get_fallback_response()
    
    try:
        # Get conversation context if user_id provided
        context = ""
        if user_id:
            context = get_conversation_context(user_id)
            if context:
                context = f"\n\nPrevious conversation:\n{context}\n"
        
        # Build prompt with context
        prompt = f"{SAKURA_PROMPT}\n\nUser name: {user_name}{context}\nCurrent user message: {user_message}\n\nSakura's response:"
        
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        ai_response = response.text.strip() if response.text else get_fallback_response()
        
        # Add messages to conversation history
        if user_id:
            add_to_conversation_history(user_id, user_message, is_user=True)
            add_to_conversation_history(user_id, ai_response, is_user=False)
        
        if user_info:
            log_with_user_info("INFO", f"✅ Gemini response generated: '{ai_response[:50]}...'", user_info)
        
        return ai_response
            
    except Exception as e:
        if user_info:
            log_with_user_info("ERROR", f"❌ Gemini API error: {e}", user_info)
        else:
            logger.error(f"Gemini API error: {e}")
        return get_error_response()


# CHAT ACTION FUNCTIONS
async def send_typing_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_info: Dict[str, any]) -> None:
    """Send typing action to show bot is processing"""
    log_with_user_info("DEBUG", "⌨️ Sending typing action", user_info)
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)


async def send_photo_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_info: Dict[str, any]) -> None:
    """Send upload photo action"""
    log_with_user_info("DEBUG", "📷 Sending photo upload action", user_info)
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)


async def send_sticker_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_info: Dict[str, any]) -> None:
    """Send choosing sticker action"""
    log_with_user_info("DEBUG", "🎭 Sending sticker choosing action", user_info)
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.CHOOSE_STICKER)


# KEYBOARD CREATION FUNCTIONS
def create_initial_start_keyboard() -> InlineKeyboardMarkup:
    """Create initial start keyboard with Info and Hi buttons"""
    keyboard = [
        [
            InlineKeyboardButton(START_MESSAGES["button_texts"]["info"], callback_data="start_info"),
            InlineKeyboardButton(START_MESSAGES["button_texts"]["hi"], callback_data="start_hi")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_info_start_keyboard(bot_username: str) -> InlineKeyboardMarkup:
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


def get_initial_start_caption(user_mention: str) -> str:
    """Get initial caption text for start command with user mention"""
    return START_MESSAGES["initial_caption"].format(user_mention=user_mention)


def get_info_start_caption(user_mention: str) -> str:
    """Get info caption text for start command with user mention"""
    return START_MESSAGES["info_caption"].format(user_mention=user_mention)


def create_help_keyboard(user_id: int, expanded: bool = False) -> InlineKeyboardMarkup:
    """Create help command keyboard"""
    if expanded:
        button_text = HELP_MESSAGES["button_texts"]["minimize"]
    else:
        button_text = HELP_MESSAGES["button_texts"]["expand"]
    
    keyboard = [[InlineKeyboardButton(button_text, callback_data=f"help_expand_{user_id}")]]
    return InlineKeyboardMarkup(keyboard)


def get_help_text(user_mention: str, expanded: bool = False) -> str:
    """Get help text based on expansion state with user mention"""
    if expanded:
        return HELP_MESSAGES["expanded"].format(user_mention=user_mention)
    else:
        return HELP_MESSAGES["minimal"].format(user_mention=user_mention)


def create_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Create broadcast target selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                BROADCAST_MESSAGES["button_texts"]["users"].format(count=len(user_ids)), 
                callback_data="bc_users"
            ),
            InlineKeyboardButton(
                BROADCAST_MESSAGES["button_texts"]["groups"].format(count=len(group_ids)), 
                callback_data="bc_groups"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_broadcast_text() -> str:
    """Get broadcast command text"""
    return BROADCAST_MESSAGES["select_target"].format(
        users_count=len(user_ids),
        groups_count=len(group_ids)
    )


# COMMAND HANDLERS
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with two-step inline buttons and effects in private chat"""
    try:
        user_info = extract_user_info(update.message)
        log_with_user_info("INFO", "🌸 /start command received", user_info)
        
        track_user_and_chat(update, user_info)
        
        # Step 1: React to the start message with random emoji and animation
        if EMOJI_REACT:
            try:
                random_emoji = random.choice(EMOJI_REACT)
                
                # Use Telethon for animated emoji reactions
                if effects_client and update.effective_chat.type == "private":
                    reaction_sent = await send_animated_reaction(
                        update.effective_chat.id,
                        update.message.message_id,
                        random_emoji
                    )
                    if reaction_sent:
                        log_with_user_info("DEBUG", f"🎭 Added animated emoji reaction: {random_emoji}", user_info)
                    else:
                        # Fallback to PTB reaction without animation
                        await add_ptb_reaction(context, update, random_emoji, user_info)
                else:
                    # Group chat or no Telethon - use PTB reaction
                    await add_ptb_reaction(context, update, random_emoji, user_info)
                
            except Exception as e:
                log_with_user_info("WARNING", f"⚠️ Failed to add emoji reaction: {e}", user_info)
        
        # Step 2: Send random sticker (only in private chat)
        if update.effective_chat.type == "private" and START_STICKERS:
            await send_sticker_action(context, update.effective_chat.id, user_info)
            
            random_sticker = random.choice(START_STICKERS)
            log_with_user_info("DEBUG", f"🎭 Sending start sticker: {random_sticker}", user_info)
            
            await context.bot.send_sticker(
                chat_id=update.effective_chat.id,
                sticker=random_sticker
            )
            log_with_user_info("INFO", "✅ Start sticker sent successfully", user_info)
        
        # Step 3: Send the initial welcome message with photo and two-step buttons
        await send_photo_action(context, update.effective_chat.id, user_info)
        
        random_image = random.choice(SAKURA_IMAGES)
        keyboard = create_initial_start_keyboard()
        user_mention = get_user_mention(update.effective_user)
        caption = get_initial_start_caption(user_mention)
        
        log_with_user_info("DEBUG", f"📷 Sending initial start photo: {random_image[:50]}...", user_info)
        
        # Send with effects if in private chat, normal otherwise
        if update.effective_chat.type == "private":
            # Use Telethon effects for the main start message
            effect_sent = await send_with_effect_photo(
                update.effective_chat.id, 
                random_image, 
                caption, 
                keyboard
            )
            if effect_sent:
                log_with_user_info("INFO", "✨ Start command with effects sent successfully", user_info)
            else:
                # Fallback to normal PTB message if effects fail
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=random_image,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                log_with_user_info("WARNING", "⚠️ Start command sent without effects (fallback)", user_info)
        else:
            # Group chat - no effects, just normal message
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=random_image,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        
        log_with_user_info("INFO", "✅ Start command completed successfully", user_info)
        
    except Exception as e:
        user_info = extract_user_info(update.message)
        log_with_user_info("ERROR", f"❌ Error in start command: {e}", user_info)
        await update.message.reply_text(get_error_response())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command with random image and effects in private chat"""
    try:
        user_info = extract_user_info(update.message)
        log_with_user_info("INFO", "ℹ️ /help command received", user_info)
        
        track_user_and_chat(update, user_info)
        
        # Step 1: React to the help message with random emoji and animation
        if EMOJI_REACT:
            try:
                random_emoji = random.choice(EMOJI_REACT)
                
                # Use Telethon for animated emoji reactions
                if effects_client and update.effective_chat.type == "private":
                    reaction_sent = await send_animated_reaction(
                        update.effective_chat.id,
                        update.message.message_id,
                        random_emoji
                    )
                    if reaction_sent:
                        log_with_user_info("DEBUG", f"🎭 Added animated emoji reaction: {random_emoji}", user_info)
                    else:
                        # Fallback to PTB reaction without animation
                        await add_ptb_reaction(context, update, random_emoji, user_info)
                else:
                    # Group chat or no Telethon - use PTB reaction
                    await add_ptb_reaction(context, update, random_emoji, user_info)
                
            except Exception as e:
                log_with_user_info("WARNING", f"⚠️ Failed to add emoji reaction: {e}", user_info)
        
        # Step 2: Send photo action indicator
        await send_photo_action(context, update.effective_chat.id, user_info)
        
        # Step 3: Prepare help content
        user_id = update.effective_user.id
        keyboard = create_help_keyboard(user_id, False)
        user_mention = get_user_mention(update.effective_user)
        help_text = get_help_text(user_mention, False)
        
        # Step 4: Send help message with random image
        random_image = random.choice(SAKURA_IMAGES)
        log_with_user_info("DEBUG", f"📷 Sending help photo: {random_image[:50]}...", user_info)
        
        # Send with effects if in private chat, normal otherwise
        if update.effective_chat.type == "private":
            # Use Telethon effects for the main help message
            effect_sent = await send_with_effect_photo(
                update.effective_chat.id,
                random_image,
                help_text,
                keyboard
            )
            if effect_sent:
                log_with_user_info("INFO", "✨ Help command with effects sent successfully", user_info)
            else:
                # Fallback to normal PTB message if effects fail
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=random_image,
                    caption=help_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                log_with_user_info("WARNING", "⚠️ Help command sent without effects (fallback)", user_info)
        else:
            # Group chat - no effects, just normal message
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=random_image,
                caption=help_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        
        log_with_user_info("INFO", "✅ Help command completed successfully", user_info)
        
    except Exception as e:
        user_info = extract_user_info(update.message)
        log_with_user_info("ERROR", f"❌ Error in help command: {e}", user_info)
        await update.message.reply_text(get_error_response())


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle broadcast command (owner only)"""
    user_info = extract_user_info(update.message)
    
    if update.effective_user.id != OWNER_ID:
        log_with_user_info("WARNING", "⚠️ Non-owner attempted broadcast command", user_info)
        return
    
    log_with_user_info("INFO", "📢 Broadcast command received from owner", user_info)
    
    # Refresh counts from database
    db_users = await get_users_from_database()
    db_groups = await get_groups_from_database()
    
    # Sync memory with database
    user_ids.update(db_users)
    group_ids.update(db_groups)
    
    keyboard = create_broadcast_keyboard()
    broadcast_text = get_broadcast_text()
    
    await update.message.reply_text(
        broadcast_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    
    log_with_user_info("INFO", "✅ Broadcast selection menu sent", user_info)


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ping command for everyone"""
    user_info = extract_user_info(update.message)
    log_with_user_info("INFO", "🏓 Ping command received", user_info)
    
    start_time = time.time()
    
    # Send initial message
    msg = await update.message.reply_text("🛰️ Pinging...")
    
    # Calculate response time
    response_time = round((time.time() - start_time) * 1000, 2)  # milliseconds
    
    # Edit message with response time and group link (no preview)
    await msg.edit_text(
        f"🏓 <a href='{GROUP_LINK}'>Pong!</a> {response_time}ms",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    
    log_with_user_info("INFO", f"✅ Ping completed: {response_time}ms", user_info)



# CALLBACK HANDLERS
async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle start command inline button callbacks"""
    try:
        query = update.callback_query
        user_info = extract_user_info(query.message)
        log_with_user_info("INFO", f"🌸 Start callback received: {query.data}", user_info)

        user_mention = get_user_mention(update.effective_user)

        if query.data == "start_info":
            # Answer callback with proper message
            await query.answer(START_MESSAGES["callback_answers"]["info"], show_alert=False)

            # Show info with original start buttons
            keyboard = create_info_start_keyboard(context.bot.username)
            caption = get_info_start_caption(user_mention)

            await query.edit_message_caption(
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            log_with_user_info("INFO", "✅ Start info buttons shown", user_info)

        elif query.data == "start_hi":
            # Answer callback with proper message
            await query.answer(START_MESSAGES["callback_answers"]["hi"], show_alert=False)

            # Send typing indicator before processing
            await send_typing_action(context, update.effective_chat.id, user_info)
            log_with_user_info("INFO", "⌨️ Typing indicator sent for hello", user_info)

            # Send a hi message from Sakura
            user_name = update.effective_user.first_name or ""
            hi_response = await get_gemini_response("Hi sakura", user_name, user_info, update.effective_user.id)

            # Send with effects if in private chat
            if update.effective_chat.type == "private":
                # Try sending with effects first
                effect_sent = await send_with_effect(update.effective_chat.id, hi_response)
                if effect_sent:
                    log_with_user_info("INFO", "✨ Start Hi response with effects sent successfully", user_info)
                else:
                    # Fallback to normal PTB message if effects fail
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=hi_response,
                        reply_markup=ForceReply(
                            selective=True,
                            input_field_placeholder="Cute text 💓"
                        )
                    )
                    log_with_user_info("WARNING", "⚠️ Start Hi response sent without effects (fallback)", user_info)
            else:
                # Group chat - no effects, just normal message
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=hi_response,
                    reply_markup=ForceReply(
                        selective=True,
                        input_field_placeholder="Cute text 💓"
                    )
                )
            
            log_with_user_info("INFO", "✅ Hi message sent from Sakura", user_info)

    except Exception as e:
        user_info = extract_user_info(query.message) if query.message else {}
        log_with_user_info("ERROR", f"❌ Error in start callback: {e}", user_info)
        try:
            await query.answer("Something went wrong 😔", show_alert=True)
        except:
            pass


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle help expand/minimize callbacks"""
    try:
        query = update.callback_query
        user_info = extract_user_info(query.message)
        log_with_user_info("INFO", "🔄 Help expand/minimize callback received", user_info)
        
        callback_data = query.data
        user_id = int(callback_data.split('_')[2])
        
        if update.effective_user.id != user_id:
            log_with_user_info("WARNING", "⚠️ Unauthorized help button access attempt", user_info)
            await query.answer("This button isn't for you 💔", show_alert=True)
            return
        
        is_expanded = help_expanded.get(user_id, False)
        help_expanded[user_id] = not is_expanded
        
        # Answer callback with appropriate message
        if not is_expanded:
            await query.answer(HELP_MESSAGES["callback_answers"]["expand"], show_alert=False)
        else:
            await query.answer(HELP_MESSAGES["callback_answers"]["minimize"], show_alert=False)
        
        keyboard = create_help_keyboard(user_id, not is_expanded)
        user_mention = get_user_mention(update.effective_user)
        help_text = get_help_text(user_mention, not is_expanded)
        
        # Update the photo caption with new help text and keyboard
        await query.edit_message_caption(
            caption=help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        log_with_user_info("INFO", f"✅ Help message {'expanded' if not is_expanded else 'minimized'}", user_info)
        
    except Exception as e:
        user_info = extract_user_info(query.message) if query.message else {}
        log_with_user_info("ERROR", f"❌ Error editing help message: {e}", user_info)
        # Fallback: answer the callback to prevent loading state
        try:
            await query.answer("Something went wrong 😔", show_alert=True)
        except:
            pass


async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle broadcast target selection"""
    query = update.callback_query
    user_info = extract_user_info(query.message)
    
    if query.from_user.id != OWNER_ID:
        log_with_user_info("WARNING", "⚠️ Non-owner attempted broadcast callback", user_info)
        await query.answer("You're not authorized to use this 🚫", show_alert=True)
        return
    
    log_with_user_info("INFO", f"🎯 Broadcast target selected: {query.data}", user_info)
    
    if query.data == "bc_users":
        # Answer callback with proper message
        await query.answer(BROADCAST_MESSAGES["callback_answers"]["users"], show_alert=False)
        
        broadcast_mode[OWNER_ID] = "users"
        await query.edit_message_text(
            BROADCAST_MESSAGES["ready_users"].format(count=len(user_ids)),
            parse_mode=ParseMode.HTML
        )
        log_with_user_info("INFO", f"✅ Ready to broadcast to {len(user_ids)} users", user_info)
        
    elif query.data == "bc_groups":
        # Answer callback with proper message
        await query.answer(BROADCAST_MESSAGES["callback_answers"]["groups"], show_alert=False)
        
        broadcast_mode[OWNER_ID] = "groups"
        await query.edit_message_text(
            BROADCAST_MESSAGES["ready_groups"].format(count=len(group_ids)),
            parse_mode=ParseMode.HTML
        )
        log_with_user_info("INFO", f"✅ Ready to broadcast to {len(group_ids)} groups", user_info)


# BROADCAST FUNCTIONS
async def execute_broadcast_direct(update: Update, context: ContextTypes.DEFAULT_TYPE, target_type: str, user_info: Dict[str, any]) -> None:
    """Execute broadcast with the current message - uses forward_message for forwarded messages, copy_message for regular messages
    Compatible with python-telegram-bot==22.3"""
    try:
        if target_type == "users":
            # Get fresh data from database
            target_list = await get_users_from_database()
            target_list = [uid for uid in target_list if uid != OWNER_ID]
            target_name = "users"
        elif target_type == "groups":
            # Get fresh data from database
            target_list = await get_groups_from_database()
            target_name = "groups"
        else:
            return
        
        log_with_user_info("INFO", f"🚀 Starting broadcast to {len(target_list)} {target_name}", user_info)
        
        if not target_list:
            await update.message.reply_text(
                BROADCAST_MESSAGES["no_targets"].format(target_type=target_name)
            )
            log_with_user_info("WARNING", f"⚠️ No {target_name} found for broadcast", user_info)
            return
        
        # Check if the message is forwarded
        is_forwarded = update.message.forward_origin is not None
        broadcast_method = "forward" if is_forwarded else "copy"
        
        log_with_user_info("INFO", f"📤 Using {broadcast_method} method for broadcast", user_info)
        
        # Show initial status
        status_msg = await update.message.reply_text(
            BROADCAST_MESSAGES["progress"].format(count=len(target_list), target_type=target_name)
        )
        
        broadcast_count = 0
        failed_count = 0
        
        # Broadcast the current message to all targets
        for i, target_id in enumerate(target_list, 1):
            try:
                if is_forwarded:
                    # Use forward_message for forwarded messages to preserve forwarding chain
                    await context.bot.forward_message(
                        chat_id=target_id,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.message_id
                    )
                else:
                    # Use copy_message for regular messages
                    await context.bot.copy_message(
                        chat_id=target_id,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.message_id
                    )
                
                broadcast_count += 1
                
                if i % 10 == 0:  # Log progress every 10 messages
                    log_with_user_info("DEBUG", f"📡 Broadcast progress: {i}/{len(target_list)} using {broadcast_method}", user_info)
                
                # Small delay to avoid rate limits
                await asyncio.sleep(BROADCAST_DELAY)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to broadcast to {target_id}: {e}")
        
        # Final status update
        await status_msg.edit_text(
            BROADCAST_MESSAGES["completed"].format(
                success_count=broadcast_count,
                total_count=len(target_list),
                target_type=target_name,
                failed_count=failed_count
            ) + f"\n<i>Method used: {broadcast_method}</i>",
            parse_mode=ParseMode.HTML
        )
        
        log_with_user_info("INFO", f"✅ Broadcast completed using {broadcast_method}: {broadcast_count}/{len(target_list)} successful, {failed_count} failed", user_info)
        
    except Exception as e:
        log_with_user_info("ERROR", f"❌ Broadcast error: {e}", user_info)
        await update.message.reply_text(
            BROADCAST_MESSAGES["failed"].format(error=str(e))
        )


# MESSAGE HANDLERS
async def handle_sticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle sticker messages"""
    user_info = extract_user_info(update.message)
    log_with_user_info("INFO", "🎭 Sticker message received", user_info)
    
    await send_sticker_action(context, update.effective_chat.id, user_info)
    
    random_sticker = random.choice(SAKURA_STICKERS)
    chat_type = update.effective_chat.type
    
    log_with_user_info("DEBUG", f"📤 Sending random sticker: {random_sticker}", user_info)
    
    # In groups, reply to the user's sticker when they replied to bot
    if (chat_type in ['group', 'supergroup'] and 
        update.message.reply_to_message and 
        update.message.reply_to_message.from_user.id == context.bot.id):
        await update.message.reply_sticker(sticker=random_sticker)
        log_with_user_info("INFO", "✅ Replied to user's sticker in group", user_info)
    else:
        # In private chats or regular stickers, send normally
        await context.bot.send_sticker(
            chat_id=update.effective_chat.id,
            sticker=random_sticker
        )
        log_with_user_info("INFO", "✅ Sent sticker response", user_info)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text and media messages with AI response and effects in private chat"""
    user_info = extract_user_info(update.message)
    user_message = update.message.text or update.message.caption or "Media message"
    
    log_with_user_info("INFO", f"💬 Text/media message received: '{user_message[:100]}...'", user_info)
    
    await send_typing_action(context, update.effective_chat.id, user_info)
    
    user_name = update.effective_user.first_name or ""
    
    # Get response from Gemini
    response = await get_gemini_response(user_message, user_name, user_info, update.effective_user.id)
    
    log_with_user_info("DEBUG", f"📤 Sending response: '{response[:50]}...'", user_info)
    
    # Send with effects if in private chat
    if update.effective_chat.type == "private":
        # Try sending with effects first
        effect_sent = await send_with_effect(update.effective_chat.id, response)
        if effect_sent:
            log_with_user_info("INFO", "✨ Gemini response with effects sent successfully", user_info)
        else:
            # Fallback to normal PTB message if effects fail
            await update.message.reply_text(
                response,
                reply_markup=ForceReply(
                    selective=True,
                    input_field_placeholder="Cute text 💓"
                )
            )
            log_with_user_info("WARNING", "⚠️ Gemini response sent without effects (fallback)", user_info)
    else:
        # Group chat - no effects, just normal message
        await update.message.reply_text(
            response,
            reply_markup=ForceReply(
                selective=True,
                input_field_placeholder="Cute text 💓"
            )
        )
    
    log_with_user_info("INFO", "✅ Text message response sent successfully", user_info)


async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all types of messages (text, stickers, voice, photos, etc.)"""
    try:
        user_info = extract_user_info(update.message)
        user_id = update.effective_user.id
        chat_type = update.effective_chat.type
        
        log_with_user_info("DEBUG", f"📨 Processing message in {chat_type}", user_info)
        
        # Track user and group IDs for broadcasting
        track_user_and_chat(update, user_info)
        
        # Check if owner is in broadcast mode
        if user_id == OWNER_ID and OWNER_ID in broadcast_mode:
            log_with_user_info("INFO", f"📢 Executing broadcast to {broadcast_mode[OWNER_ID]}", user_info)
            await execute_broadcast_direct(update, context, broadcast_mode[OWNER_ID], user_info)
            del broadcast_mode[OWNER_ID]
            return
        
        # Determine if bot should respond
        should_respond = True
        if chat_type in ['group', 'supergroup']:
            should_respond = should_respond_in_group(update, context.bot.id)
            if not should_respond:
                log_with_user_info("DEBUG", "🚫 Not responding to group message (no mention/reply)", user_info)
                return
            else:
                log_with_user_info("INFO", "✅ Responding to group message (mentioned/replied)", user_info)
        
        # Check rate limiting
        if is_rate_limited(user_id):
            log_with_user_info("WARNING", "⏱️ Rate limited - ignoring message", user_info)
            return
        
        # Handle different message types
        if update.message.sticker:
            await handle_sticker_message(update, context)
        else:
            await handle_text_message(update, context)
        
        # Update response time after sending response
        update_user_response_time(user_id)
        log_with_user_info("DEBUG", "⏰ Updated user response time", user_info)
        
    except Exception as e:
        user_info = extract_user_info(update.message)
        log_with_user_info("ERROR", f"❌ Error handling message: {e}", user_info)
        if update.message.text:
            await update.message.reply_text(get_error_response())


# ERROR HANDLER
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Try to extract user info if update has a message
    if hasattr(update, 'message') and update.message:
        try:
            user_info = extract_user_info(update.message)
            log_with_user_info("ERROR", f"💥 Exception occurred: {context.error}", user_info)
        except:
            logger.error(f"Could not extract user info for error: {context.error}")
    elif hasattr(update, 'callback_query') and update.callback_query and update.callback_query.message:
        try:
            user_info = extract_user_info(update.callback_query.message)
            log_with_user_info("ERROR", f"💥 Callback query exception: {context.error}", user_info)
        except:
            logger.error(f"Could not extract user info for callback error: {context.error}")


# BOT SETUP FUNCTIONS
async def setup_bot_commands(application: Application) -> None:
    """Setup bot commands menu"""
    try:
        await application.bot.set_my_commands(COMMANDS)
        logger.info("✅ Bot commands menu set successfully")
        
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")


def setup_handlers(application: Application) -> None:
    """Setup all command and message handlers"""
    logger.info("🔧 Setting up bot handlers...")
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("ping", ping_command))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(start_callback, pattern="^start_"))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help_expand_"))
    application.add_handler(CallbackQueryHandler(broadcast_callback, pattern="^bc_"))
    
    # Message handler for all message types
    application.add_handler(MessageHandler(
        filters.TEXT | filters.Sticker.ALL | filters.VOICE | filters.VIDEO_NOTE | 
        filters.PHOTO | filters.Document.ALL & ~filters.COMMAND, 
        handle_all_messages
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("✅ All handlers setup completed")


def run_bot() -> None:
    """Run the bot"""
    if not validate_config():
        return
    
    logger.info("🚀 Initializing Sakura Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Setup handlers
    setup_handlers(application)
    
    # Setup bot commands and database using post_init
    async def post_init(app):
        # Initialize database
        db_success = await init_database()
        if not db_success:
            logger.error("❌ Database initialization failed. Bot will continue without persistence.")
        
        # Start Telethon effects client
        await start_effects_client()
        
        await setup_bot_commands(app)
        logger.info("🌸 Sakura Bot initialization completed!")
        
    # Setup shutdown handler
    async def post_shutdown(app):
        await close_database()
        await stop_effects_client()
        logger.info("🌸 Sakura Bot shutdown completed!")
        
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    
    logger.info("🌸 Sakura Bot is starting...")
    
    # Run the bot with polling
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


# HTTP SERVER FOR DEPLOYMENT
class DummyHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for keep-alive server"""
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sakura bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass


def start_dummy_server() -> None:
    """Start dummy HTTP server for deployment platforms"""
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    logger.info(f"🌐 Dummy server listening on port {port}")
    server.serve_forever()


# MAIN FUNCTION
def main() -> None:
    """Main function"""
    try:
        logger.info("🌸 Sakura Bot starting up...")
        
        # Start dummy server in background thread
        threading.Thread(target=start_dummy_server, daemon=True).start()
        
        # Run the bot
        run_bot()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")


if __name__ == "__main__":
    main()