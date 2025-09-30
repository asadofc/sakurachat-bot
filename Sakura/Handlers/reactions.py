import random
from typing import Dict
from telegram import Update
from Sakura.Core.helpers import log_action
from Sakura.Interface.effects import animate_reaction

# EMOJI REACTIONS
EMOJI_REACT = [
    "🍓",  "💊",  "🦄",  "💅",  "💘",
    "💋",  "🍌",  "⚡",  "🕊️",  "❤️‍🔥",
    "🔥",  "❤️"
]

CONTEXTUAL_REACTIONS = {
    # Positive emotions
    "love": ["❤️", "🥰", "😍", "💘", "❤️‍🔥"],
    "happy": ["😁", "🤗", "🤩", "😘", "❤️"],
    "excited": ["🤗", "🔥", "🤩", "⚡", "💯", "❤️"],
    "funny": ["🤣", "😁", "❤️", "🤗"],
    "impressed": ["🤯", "😨", "👏", "😱", "👌", "❤️"],
    "cute": ["🥰", "😍", "❤️", "🍓", "💘"],
    "cool": ["❤️", "😎", "🤗", "👌", "👍"],

    # Negative emotions
    "sad": ["😢", "😭", "💔", "💘", "🤗"],
    "angry": ["😡", "🤬", "👎"],
    "confused": ["🤔", "🤨", "😐", "👍", "👀"],
    "tired": ["😴", "🥱"],
    "sick": ["💔", "😭", "❤️"],
    "shocked": ["😱", "🤯", "😨"],

    # Actions/Activities
    "food": ["🍓", "🍌", "🌭", "🍾", "❤️"],
    "study": ["👨‍💻", "✍️", "🤓", "❤️"],
    "celebration": ["🎉", "🏆", "🔥", "❤️"],
    "thanks": ["🥰", "👍", "❤️", "🤗", "❤️"],
    "agreement": ["👍", "💯", "👌", "❤️"],

    # Special cases
    "flirty": ["😘", "😍", "💋", "❤️", "👀"],
    "mysterious": ["🌚", "👀"],
    "playful": ["🤪", "👀", "🙈", "❤️"],
    "supportive": ["🤗", "👍", "💘", "❤️", "🥰"]
}

REACTION_KEYWORDS = {
    "love": [
        "love", "pyaar", "mohabbat", "ishq", "dil", "heart", "miss", "yaad", "romance",
        "lover", "sweetheart", "bf", "gf", "husband", "wife", "husbae", "hubby", "wifey",
        "crush", "dosti", "pyara", "pyari", "cute love", "romantic", "romantically", "affection"
    ],
    "happy": [
        "happy", "khushi", "khush", "joy", "joyful", "good", "accha", "amazing", "awesome",
        "great", "fantastic", "excellent", "wonderful", "yay", "hooray", "feeling good", "blessed"
    ],
    "excited": [
        "excited", "wow", "omg", "awesome", "incredible", "fantastic", "amazing",
        "can't wait", "looking forward", "pumped", "hyped", "stoked", "ecstatic", "thrilled"
    ],
    "funny": [
        "haha", "lol", "funny", "hasna", "mazak", "joke", "comedy", "laugh", "lmao", "rofl",
        "funniest", "humor", "hilarious", "prank", "memes"
    ],
    "impressed": [
        "impressive", "amazing", "wow", "incredible", "outstanding", "awesome", "brilliant",
        "fantastic", "marvelous", "astounding", "superb", "mind blown", "🤯"
    ],
    "cute": [
        "cute", "sweet", "adorable", "pyara", "meetha", "pyaara", "lovely", "charming",
        "kawaii", "baby", "innocent", "fluffy", "precious", "angel", "sweety"
    ],
    "cool": [
        "cool", "nice", "badiya", "mast", "solid", "awesome", "great", "amazing", "impressive",
        "dope", "lit", "chill", "awesome sauce", "fantastic", "stylish", "swag"
    ],
    "sad": [
        "sad", "dukh", "upset", "cry", "rona", "depression", "down", "lonely", "trouble",
        "heartbroken", "pain", "hurt", "miserable", "unhappy", "😭", "😢", "💔"
    ],
    "angry": [
        "angry", "gussa", "mad", "frustrated", "annoyed", "irritated", "furious", "rage",
        "hate", "🤬", "pissed", "grumpy", "upset", "boiling"
    ],
    "confused": [
        "confused", "confuse", "samajh", "understand", "kya", "what", "huh", "kaise", "how",
        "uncertain", "unsure", "puzzled", "baffled", "perplexed", "🤔", "thinking"
    ],
    "tired": [
        "tired", "thak", "sleepy", "neend", "rest", "sleep", "exhausted", "fatigue", "weary",
        "drowsy", "zzz", "nap", "burnt out", "drained"
    ],
    "sick": [
        "sick", "bimar", "ill", "fever", "headache", "pain", "unwell", "vomit", "dizzy",
        "ache", "cold", "flu", "🤒", "nausea", "sore", "cough", "infection"
    ],
    "shocked": [
        "shocked", "surprise", "omg", "what", "kya", "really", "no way", "unbelievable",
        "astonished", "😱", "🤯", "😨", "stunned", "speechless", "mind blown"
    ],
    "food": [
        "food", "khana", "eat", "hungry", "bhookh", "delicious", "tasty", "meal", "snack",
        "breakfast", "lunch", "dinner", "dinner time", "yum", "yummy", "🍔", "🍕", "🍗", "🍣", "🍩", "🥗"
    ],
    "study": [
        "study", "padhai", "exam", "test", "homework", "assignment", "learn", "revision",
        "quiz", "project", "prepare", "notes", "📚", "read", "educate", "lecture"
    ],
    "celebration": [
        "congrats", "congratulations", "celebrate", "party", "success", "win", "achievement",
        "cheers", "hooray", "yay", "🎉", "🏆", "🥳", "victory", "🥂", "clap", "👏"
    ],
    "thanks": [
        "thanks", "thank", "dhanyawad", "shukriya", "grateful", "thank you", "appreciate",
        "obliged", "🙏", "cheers", "merci", "arigato"
    ],
    "agreement": [
        "yes", "haan", "right", "correct", "sahi", "agree", "okay", "ok", "yep", "sure",
        "absolutely", "👍", "💯", "of course", "definitely"
    ],
    "flirty": [
        "beautiful", "handsome", "sexy", "hot", "gorgeous", "cute", "attractive", "desirable",
        "stunning", "bae", "babe", "lover", "hottie", "🔥", "😍", "😘", "💋"
    ],
    "mysterious": [
        "secret", "mystery", "hidden", "raaz", "chupana", "unknown", "enigmatic", "puzzle",
        "suspense", "cryptic", "🕵️", "dark", "hidden meaning"
    ],
    "playful": [
        "play", "fun", "enjoy", "masti", "timepass", "tease", "joke", "prank", "games",
        "funtime", "🙈", "😂", "🤣", "silly", "goofy", "playful banter", "😂"
    ],
    "supportive": [
        "support", "help", "sahayata", "madad", "care", "assistance", "backup", "encourage",
        "aid", "stand by", "💪", "🤗", "👍", "I got you", "here for you"
    ]
}

async def handle_reaction(update: Update, user_info: Dict[str, any]):
    """
    Analyzes the message text and sends a contextual, animated emoji reaction
    with a certain probability.
    """
    try:
        if random.random() > 0.3:
            return

        message_text = (update.message.text or "").lower()
        if not message_text:
            return

        log_action("DEBUG", f"🤔 Analyzing message for reaction: '{message_text[:50]}...'", user_info)

        found_context = None
        for context, keywords in REACTION_KEYWORDS.items():
            if any(keyword in message_text for keyword in keywords):
                found_context = context
                log_action("INFO", f"✅ Context found for reaction: '{found_context}'", user_info)
                break

        if found_context:
            emoji_to_react = random.choice(CONTEXTUAL_REACTIONS[found_context])
            log_action("INFO", f"🥰 Selected emoji for reaction: {emoji_to_react}", user_info)

            await animate_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                emoji=emoji_to_react
            )
            log_action("INFO", f"🚀 Sent animated reaction '{emoji_to_react}' successfully", user_info)

    except Exception as e:
        log_action("ERROR", f"❌ Failed to handle contextual reaction: {e}", user_info)