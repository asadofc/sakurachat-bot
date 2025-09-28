import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
    ChatMemberHandler,
)
from Sakura.Core.config import BOT_TOKEN
from Sakura.Core.logging import logger
from Sakura.Core.utils import validate_config
from Sakura.Core.errors import handle_error
from Sakura.Storage.database import connect_database, close_database
from Sakura.Storage.valkey import connect_cache, close_cache
from Sakura.Interface.effects import start_effects, stop_effects, initialize_effects_client
from Sakura.Features.cleanup import cleanup_conversations
from Sakura.Interface.commands import (
    start_command,
    help_command,
    broadcast_command,
    ping_command,
    stats_command,
    COMMANDS,
)
from Sakura.Interface.callbacks import (
    start_callback,
    help_callback,
    broadcast_callback,
    stats_refresh,
)
from Sakura.Features.payments import (
    precheckout_query,
    successful_payment,
    buy_command,
    buyers_command,
)
from Sakura.Interface.handlers import handle_messages
from Sakura.Interface.updates import handle_member
from Sakura.AI.gemini import initialize_gemini_client
from Sakura.AI.openrouter import initialize_openrouter_client
from Sakura import state

async def setup_commands(application: Application) -> None:
    """Setup bot commands menu"""
    try:
        await application.bot.set_my_commands(COMMANDS)
        logger.info("✅ Bot commands menu set successfully")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")

def setup_handlers(application: Application) -> None:
    """Setup all command and message handlers"""
    logger.info("🔧 Setting up bot handlers...")

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("buyers", buyers_command))
    application.add_handler(CommandHandler("stats", stats_command))

    application.add_handler(CallbackQueryHandler(start_callback, pattern="^start_"))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
    application.add_handler(CallbackQueryHandler(broadcast_callback, pattern="^bc_|^get_flowers_again$"))
    application.add_handler(CallbackQueryHandler(stats_refresh, pattern="^refresh_stats$"))

    application.add_handler(PreCheckoutQueryHandler(precheckout_query))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    application.add_handler(MessageHandler(
        (filters.TEXT | filters.Sticker.ALL | filters.VOICE | filters.VIDEO_NOTE |
        filters.PHOTO | filters.Document.ALL | filters.POLL) & ~filters.COMMAND,
        handle_messages
    ))

    application.add_handler(ChatMemberHandler(handle_member, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_error_handler(handle_error)

    logger.info("✅ All handlers setup completed")

def run_bot() -> None:
    """Run the bot"""
    if not validate_config():
        return

    logger.info("🚀 Initializing Sakura Bot...")

    initialize_effects_client()
    initialize_gemini_client()
    initialize_openrouter_client()

    application = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()

    setup_handlers(application)

    async def post_init(app):
        valkey_success = await connect_cache()
        if not valkey_success:
            logger.warning("⚠️ Valkey initialization failed. Bot will continue with memory fallback.")
        db_success = await connect_database()
        if not db_success:
            logger.error("❌ Database initialization failed. Bot will continue without persistence.")
        await start_effects()
        await setup_commands(app)
        state.cleanup_task = asyncio.create_task(cleanup_conversations())
        logger.info("🌸 Sakura Bot initialization completed!")

    async def post_shutdown(app):
        if state.cleanup_task and not state.cleanup_task.done():
            logger.info("🛑 Cancelling cleanup task...")
            state.cleanup_task.cancel()
            try:
                await state.cleanup_task
            except asyncio.CancelledError:
                logger.info("✅ Cleanup task cancelled successfully")
        await close_database()
        await close_cache()
        await stop_effects()
        logger.info("🌸 Sakura Bot shutdown completed!")

    application.post_init = post_init
    application.post_shutdown = post_shutdown

    logger.info("🌸 Sakura Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)