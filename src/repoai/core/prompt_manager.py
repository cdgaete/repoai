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

    def _load_default_prompts(self) -> Dict[str, Any]:
        with resources.open_text("repoai.core", "default_prompts.yaml") as f:
            return yaml.safe_load(f)

    def _load_custom_prompts(self) -> Dict[str, Any]:
        custom_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'custom_prompts.yaml'
        if custom_prompts_path.exists():
            with open(custom_prompts_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def get_prompt(self, task_id: str, prompt_type: str = 'system') -> str:
        custom_prompt = self.custom_prompts.get(task_id, {}).get(prompt_type)
        if custom_prompt:
            return custom_prompt
        return self.default_prompts.get(task_id, {}).get(prompt_type, '')

    def get_user_prompt(self, task_id: str, prompt_key: str) -> str:
        custom_prompt = self.custom_prompts.get(task_id, {}).get('user', {}).get(prompt_key)
        if custom_prompt:
            return custom_prompt
        return self.default_prompts.get(task_id, {}).get('user', {}).get(prompt_key, '')

    def set_custom_prompt(self, task_id: str, prompt: str, prompt_type: str = 'system'):
        if task_id not in self.custom_prompts:
            self.custom_prompts[task_id] = {}
        self.custom_prompts[task_id][prompt_type] = prompt
        self._save_custom_prompts()

    def set_custom_user_prompt(self, task_id: str, prompt_key: str, prompt: str):
        if task_id not in self.custom_prompts:
            self.custom_prompts[task_id] = {'user': {}}
        elif 'user' not in self.custom_prompts[task_id]:
            self.custom_prompts[task_id]['user'] = {}
        self.custom_prompts[task_id]['user'][prompt_key] = prompt
        self._save_custom_prompts()

    def _save_custom_prompts(self):
        custom_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'custom_prompts.yaml'
        with open(custom_prompts_path, 'w') as f:
            yaml.dump(self.custom_prompts, f)

    def reset_prompt(self, task_id: str, prompt_type: str = 'system'):
        if task_id in self.custom_prompts and prompt_type in self.custom_prompts[task_id]:
            del self.custom_prompts[task_id][prompt_type]
            if not self.custom_prompts[task_id]:
                del self.custom_prompts[task_id]
            self._save_custom_prompts()

    def reset_user_prompt(self, task_id: str, prompt_key: str):
        if task_id in self.custom_prompts and 'user' in self.custom_prompts[task_id] and prompt_key in self.custom_prompts[task_id]['user']:
            del self.custom_prompts[task_id]['user'][prompt_key]
            if not self.custom_prompts[task_id]['user']:
                del self.custom_prompts[task_id]['user']
            if not self.custom_prompts[task_id]:
                del self.custom_prompts[task_id]
            self._save_custom_prompts()

    def list_prompts(self) -> Dict[str, Dict[str, Any]]:
        all_prompts = {}
        for task_id in set(list(self.default_prompts.keys()) + list(self.custom_prompts.keys())):
            all_prompts[task_id] = {
                'system': {
                    'default': self.default_prompts.get(task_id, {}).get('system', ''),
                    'custom': self.custom_prompts.get(task_id, {}).get('system', '')
                },
                'user': {
                    'default': self.default_prompts.get(task_id, {}).get('user', {}),
                    'custom': self.custom_prompts.get(task_id, {}).get('user', {})
                }
            }
        return all_prompts