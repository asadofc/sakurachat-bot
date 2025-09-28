import os

# CONFIGURATION
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
VALKEY_URL = os.getenv("VALKEY_URL", "valkey://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL = os.getenv("MODEL", "x-ai/grok-4-fast:free")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/SoulMeetsHQ")
UPDATE_LINK = os.getenv("UPDATE_LINK", "https://t.me/WorkGlows")
PING_LINK = os.getenv("PING_LINK", "https://t.me/WorkGlows")
SESSION_TTL = 3600
CACHE_TTL = 300
RATE_LIMIT_TTL = 60
RATE_LIMIT_COUNT = 5
MESSAGE_LIMIT = 1.0
BROADCAST_DELAY = 0.03
CHAT_LENGTH = 20
CHAT_CLEANUP = 1800
OLD_CHAT = 3600