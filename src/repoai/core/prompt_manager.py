import os
import yaml
from pathlib import Path
from typing import Dict, Any
from importlib import resources
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PromptManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.default_prompts = self._load_default_prompts()
        self.custom_prompts = self._load_custom_prompts()

    def _load_default_prompts(self) -> Dict[str, str]:
        with resources.open_text("repoai.core", "default_prompts.yaml") as f:
            return yaml.safe_load(f)

    def _load_custom_prompts(self) -> Dict[str, str]:
        custom_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'custom_prompts.yaml'
        if custom_prompts_path.exists():
            with open(custom_prompts_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def get_prompt(self, task_id: str) -> str:
        return self.custom_prompts.get(task_id, self.default_prompts.get(task_id, ''))

    def set_custom_prompt(self, task_id: str, prompt: str):
        self.custom_prompts[task_id] = prompt
        self._save_custom_prompts()

    def _save_custom_prompts(self):
        custom_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'custom_prompts.yaml'
        with open(custom_prompts_path, 'w') as f:
            yaml.dump(self.custom_prompts, f)

    def reset_prompt(self, task_id: str):
        if task_id in self.custom_prompts:
            del self.custom_prompts[task_id]
            self._save_custom_prompts()

    def list_prompts(self) -> Dict[str, Dict[str, str]]:
        all_prompts = {}
        for task_id in set(list(self.default_prompts.keys()) + list(self.custom_prompts.keys())):
            all_prompts[task_id] = {
                'default': self.default_prompts.get(task_id, ''),
                'custom': self.custom_prompts.get(task_id, '')
            }
        return all_prompts