from typing import Dict, Set, Optional, List
from telethon import TelegramClient
from valkey.asyncio import Valkey as AsyncValkey

# GLOBAL STATE & MEMORY SYSTEM
user_ids: Set[int] = set()
group_ids: Set[int] = set()
broadcast_mode: Dict[int, str] = {}
user_message_counts: Dict[str, List] = {}
rate_limited_users: Dict[str, float] = {}
user_last_response_time: Dict[int, float] = {}
conversation_history: Dict[int, list] = {}
db_pool = None
cleanup_task = None
valkey_client: Optional[AsyncValkey] = None
payment_storage: Dict[str, dict] = {}
effects_client: Optional[TelegramClient] = None
gemini_client = None
openrouter_client = None