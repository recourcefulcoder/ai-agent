"""
Logging configuration using loguru.
"""

import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()


def setup_logger(level: str = "INFO", log_to_file: bool = True, log_file: str = "logs/agent.log"):
    """
    Setup logger with console and file handlers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to file
        log_file: Path to log file
    """
    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )
    
    # File handler if requested
    if log_to_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
        )


# Default setup
setup_logger()
