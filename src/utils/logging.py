"""Custom logging configuration with colored output."""

import logging
from typing import Any

# ANSI color codes
COLORS = {
    'DEBUG': '\033[36m',  # Cyan
    'INFO': '\033[32m',   # Green
    'WARNING': '\033[33m', # Yellow
    'ERROR': '\033[31m',   # Red
    'CRITICAL': '\033[35m', # Magenta
    'RESET': '\033[0m'    # Reset
}

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        # Add color to the level name
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        
        # Format the message
        return super().format(record)

def setup_logging(level: str = "INFO") -> None:
    """Set up logging with colored output.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    root_logger.addHandler(console_handler) 