import logging
from app.core.config import settings  # Импортируем настройки


def setup_logger(name=__name__, level=None):
    if level is None:
        level_str = getattr(settings, 'LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, level_str, logging.INFO)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=level,
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger(name)
    return logger