# File: src/repoai/services/progress_service.py

import json
import yaml
from pathlib import Path
from typing import Dict, Any
from ..core.config_manager import ConfigManager
from ..core.file_manager import FileManager
from ..utils.common_utils import get_formated_datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ProgressService:
    def __init__(self, project_path: str, config: ConfigManager):
        self.project_name = project_path.stem
        self.project_path = project_path
        self.config = config
        self.file_manager = FileManager(self.project_path, ignore_file=self.config.get('repoai_ignore_file'))
        self.base_path = Path(self.config.REPOAI_DIR)
        self.base_file_name = f"{self.project_name}_workflow_progress.yml"
        logger.debug("Progress service initialized")

    def save_progress(self, step_name: str, context: Dict[str, Any]):
        formated_time = get_formated_datetime()
        progress_data = self.load_progress()
        progress_data['last_step'] = step_name
        progress_data['context'] = context
        progress_data['datetime'] = formated_time
        
        self.file_manager.save_yaml(str(self.base_path / self.base_file_name), progress_data)
        self.file_manager.save_yaml(str(self.base_path / f"{formated_time}_{step_name}_{self.base_file_name}"), progress_data)
        logger.debug(f"Progress saved for step: {step_name}")

    def load_progress(self) -> Dict[str, Any]:
        if self.file_manager.file_exists(str(self.base_path / self.base_file_name)):
            content = self.file_manager.read_file(str(self.base_path / self.base_file_name))
            return yaml.safe_load(content)
        return {}

    def get_last_state(self) -> Dict[str, Any]:
        return self.load_progress()

    def clear_progress(self):
        self.file_manager.delete_file(str(self.base_path / self.base_file_name))
        logger.debug(f"Progress cleared for project: {self.project_path}")

    def get_last_step(self) -> str:
        progress = self.load_progress()
        return progress.get('last_step')

    def resume_from_last_step(self) -> Dict[str, Any]:
        progress = self.load_progress()
        return progress.get('context', {})