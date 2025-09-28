import logging

# LOGGING SETUP
# Color codes for logging
class Colors:
    # ANSI color codes for colorful logging
    BLUE = '\033[94m'      # INFO/WARNING
    GREEN = '\033[92m'     # DEBUG
    YELLOW = '\033[93m'    # INFO
    RED = '\033[91m'       # ERROR
    RESET = '\033[0m'      # Reset color
    BOLD = '\033[1m'       # Bold text

# Custom formatter for colored logs
class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to entire log messages"""

    # Color mapping for log levels
    COLORS = {
        'DEBUG': Colors.GREEN,
        'INFO': Colors.YELLOW,
        'WARNING': Colors.BLUE,
        'ERROR': Colors.RED,
    }

    # Formats the log record with appropriate colors
    def format(self, record):
        # Get the original formatted message
        original_format = super().format(record)

        # Get color based on log level
        color = self.COLORS.get(record.levelname, Colors.RESET)

        # Apply color to the entire message
        colored_format = f"{color}{original_format}{Colors.RESET}"

        return colored_format

# Configure logging with colors
def setup_logging():
    # Sets up a colored logger for the bot
    """Setup colored logging configuration"""
    logger = logging.getLogger("SAKURA 🌸")
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

logger = setup_logging()