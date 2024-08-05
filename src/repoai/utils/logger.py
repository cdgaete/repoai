# src/repoai/utils/logger.py

import logging
from .config_manager import config_manager

def setup_logger(name, log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config_manager.get('LOG_LEVEL', 'INFO')))

    formatter = logging.Formatter(
        config_manager.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        datefmt=config_manager.get('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S')
        )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger