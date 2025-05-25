import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.BACKEND_LOG_LEVEL,
        colorize=True
    )

    # Add file handler for development
    if settings.ENV == "development":
        logger.add(
            "logs/development.log",
            rotation="1 day",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.BACKEND_LOG_LEVEL
        )

    # Add file handler for production
    else:
        logger.add(
            "logs/production.log",
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.BACKEND_LOG_LEVEL,
            compression="zip"
        )

    # Add Elasticsearch handler for both environments
    logger.add(
        lambda msg: send_to_elasticsearch(msg),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.BACKEND_LOG_LEVEL,
        filter=lambda record: record["level"].no >= logger.level(settings.BACKEND_LOG_LEVEL).no
    )

def send_to_elasticsearch(record):
    """
    Send log record to Elasticsearch.
    This is a placeholder - implement actual Elasticsearch integration.
    """
    # TODO: Implement Elasticsearch integration
    pass 