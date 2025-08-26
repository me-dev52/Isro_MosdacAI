"""
Logging utility module for MOSDAC AI Help Bot
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from config.config import get_config

class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru"""
    
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging(
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days"
) -> None:
    """
    Setup logging configuration
    
    Args:
        log_file: Path to log file
        log_level: Logging level
        rotation: Log rotation size
        retention: Log retention period
    """
    config = get_config()
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                   "{name}:{function}:{line} - {message}",
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("fastapi").handlers = [InterceptHandler()]
    logging.getLogger("neo4j").handlers = [InterceptHandler()]
    logging.getLogger("selenium").handlers = [InterceptHandler()]
    logging.getLogger("urllib3").handlers = [InterceptHandler()]

def get_logger(name: str) -> logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)

# Setup default logging
setup_logging(
    log_file=get_config().logs_dir / "mosdac_ai_bot.log",
    log_level=get_config().log_level
)
