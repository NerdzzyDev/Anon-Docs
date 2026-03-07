from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from app.core.config import RESULTS_DIR


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        backtrace=False,
        diagnose=False,
    )
    log_path = Path(RESULTS_DIR) / "app.log"
    logger.add(
        log_path,
        level="INFO",
        rotation="10 MB",
        retention=5,
        backtrace=False,
        diagnose=False,
    )
