import uvloop
from Sakura.Core.logging import logger
from Sakura.application import run_bot
from Sakura.Core.server import start_server_thread

def main() -> None:
    """Main function"""
    try:
        try:
            uvloop.install()
            logger.info("🚀 uvloop installed successfully")
        except ImportError:
            logger.warning("⚠️ uvloop not available")
        except Exception as e:
            logger.warning(f"⚠️ uvloop setup failed: {e}")

        logger.info("🌸 Sakura Bot starting up...")
        start_server_thread()
        run_bot()

    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    main()