# src/repoai/utils/logger.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(config):
    logger = logging.getLogger('repoai')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        log_file = config.get('log_file')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.get('max_log_file_size'),
            backupCount=config.get('log_backup_count')
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

def get_logger(name):
    return logging.getLogger(f'repoai.{name}')