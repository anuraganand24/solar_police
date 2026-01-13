# src/utils/logger.py

from loguru import logger
from src.config import LOG_DIR, LOG_LEVEL

LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.add(
    LOG_DIR / "pipeline.log",
    level=LOG_LEVEL,
    format="{time} | {level} | {message}",
    rotation="10 MB",
)

def get_logger():
    return logger
