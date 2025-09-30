import asyncio
import asyncpg
from Sakura.Core.config import DATABASE_URL
from Sakura.Core.logging import logger
from Sakura import state

async def connect_database():
    """Initialize database connection and create tables"""
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return False

    try:
        state.db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=3,
            server_settings={'application_name': 'sakura_bot'}
        )
        logger.info("✅ Database connection pool created successfully")

        async with state.db_pool.acquire() as conn:
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
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS purchases (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    amount INTEGER NOT NULL,
                    telegram_payment_charge_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_groups_created_at ON groups(created_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON purchases(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_purchases_created_at ON purchases(created_at)")

        logger.info("✅ Database tables created/verified successfully")
        await load_data()
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def load_data():
    """Load user IDs and group IDs from database into memory"""
    if not state.db_pool:
        logger.warning("⚠️ Database pool not available for loading data")
        return

    try:
        async with state.db_pool.acquire() as conn:
            user_rows = await conn.fetch("SELECT user_id FROM users")
            state.user_ids.update(row['user_id'] for row in user_rows)
            group_rows = await conn.fetch("SELECT group_id FROM groups")
            state.group_ids.update(row['group_id'] for row in group_rows)
        logger.info(f"✅ Loaded {len(state.user_ids)} users and {len(state.group_ids)} groups from database")
    except Exception as e:
        logger.error(f"❌ Failed to load data from database: {e}")

def save_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Save user to database asynchronously (fire and forget)"""
    if not state.db_pool:
        return
    asyncio.create_task(_save_user(user_id, username, first_name, last_name))

async def _save_user(user_id: int, username: str, first_name: str, last_name: str):
    try:
        async with state.db_pool.acquire() as conn:
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

def save_group(group_id: int, title: str = None, username: str = None, chat_type: str = None):
    """Save group to database asynchronously (fire and forget)"""
    if not state.db_pool:
        return
    asyncio.create_task(_save_group(group_id, title, username, chat_type))

async def _save_group(group_id: int, title: str, username: str, chat_type: str):
    try:
        async with state.db_pool.acquire() as conn:
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

async def get_users():
    """Get all user IDs from database"""
    if not state.db_pool:
        return list(state.user_ids)
    try:
        async with state.db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM users")
            return [row['user_id'] for row in rows]
    except Exception as e:
        logger.error(f"❌ Failed to get users from database: {e}")
        return list(state.user_ids)

async def get_groups():
    """Get all group IDs from database"""
    if not state.db_pool:
        return list(state.group_ids)
    try:
        async with state.db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT group_id FROM groups")
            return [row['group_id'] for row in rows]
    except Exception as e:
        logger.error(f"❌ Failed to get groups from database: {e}")
        return list(state.group_ids)

def save_purchase(user_id: int, username: str = None, first_name: str = None, last_name: str = None, amount: int = 0, charge_id: str = None):
    """Save purchase to database asynchronously (fire and forget)"""
    if not state.db_pool:
        return
    asyncio.create_task(_save_purchase(user_id, username, first_name, last_name, amount, charge_id))

async def _save_purchase(user_id: int, username: str, first_name: str, last_name: str, amount: int, charge_id: str):
    try:
        async with state.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO purchases (user_id, username, first_name, last_name, amount, telegram_payment_charge_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (telegram_payment_charge_id) DO NOTHING
            """, user_id, username, first_name, last_name, amount, charge_id)
        logger.debug(f"💾 Purchase saved to database: user {user_id}, amount {amount}")
    except Exception as e:
        logger.error(f"❌ Failed to save purchase to database: {e}")

async def get_purchases():
    """Get all purchases from database ordered by amount descending"""
    if not state.db_pool:
        return []
    try:
        async with state.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, username, first_name, last_name, SUM(amount) as total_amount, COUNT(*) as purchase_count
                FROM purchases
                GROUP BY user_id, username, first_name, last_name
                ORDER BY total_amount DESC
            """)
            return rows
    except Exception as e:
        logger.error(f"❌ Failed to get purchases from database: {e}")
        return []

async def close_database():
    """Close database connection pool"""
    if state.db_pool:
        await state.db_pool.close()
        logger.info("✅ Database connection pool closed")

async def remove_user(user_id: int):
    """Remove a user from the database and memory."""
    if user_id in state.user_ids:
        state.user_ids.remove(user_id)
    if not state.db_pool:
        return
    try:
        async with state.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)
        logger.info(f"✅ User {user_id} removed from database.")
    except Exception as e:
        logger.error(f"❌ Failed to remove user {user_id} from database: {e}")

async def remove_group(group_id: int):
    """Remove a group from the database and memory."""
    if group_id in state.group_ids:
        state.group_ids.remove(group_id)
    if not state.db_pool:
        return
    try:
        async with state.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM groups WHERE group_id = $1", group_id)
        logger.info(f"✅ Group {group_id} removed from database.")
    except Exception as e:
        logger.error(f"❌ Failed to remove group {group_id} from database: {e}")