from Sakura.Core.config import OWNER_ID
from Sakura.Core.logging import logger
from Sakura.state import db_pool

def is_owner(user_id: int) -> bool:
    """Check if a user is the owner of the bot."""
    return user_id == OWNER_ID

async def find_user(identifier: str) -> tuple:
    """Get user info by user ID or username from database"""
    if not db_pool:
        return None, None

    try:
        async with db_pool.acquire() as conn:
            if identifier.isdigit():
                # Search by user ID
                row = await conn.fetchrow(
                    "SELECT user_id, username, first_name, last_name FROM users WHERE user_id = $1",
                    int(identifier)
                )
            else:
                # Search by username (remove @ if present)
                username = identifier.lstrip('@')
                row = await conn.fetchrow(
                    "SELECT user_id, username, first_name, last_name FROM users WHERE username = $1",
                    username
                )

            if row:
                display_name = row['first_name'] or row['username'] or f"User {row['user_id']}"
                return row['user_id'], display_name

        return None, None

    except Exception as e:
        logger.error(f"❌ Error looking up user {identifier}: {e}")
        return None, None