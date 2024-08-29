__version__ = "0.0.2"

from .core.project_manager import ProjectManager
from .core.config_manager import ConfigManager
from typing import Optional
from .utils.logger import setup_logger


def initialize(config: Optional[ConfigManager] = None):
    if config is None:
        config = ConfigManager()
    setup_logger(config)
    return config

__all__ = ['ProjectManager', 'ConfigManager', 'initialize']