import os
import yaml
from pathlib import Path
from typing import Dict, Any
from importlib import resources
from jinja2 import Environment, FileSystemLoader
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PromptManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.default_prompts = self._load_default_prompts()
        self.custom_prompts = self._load_custom_prompts()
        self.interface_prompts = self._load_interface_prompts()
        self.jinja_env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / 'resources' / 'prompts')))

    def _load_default_prompts(self) -> Dict[str, Any]:
        with resources.open_text("repoai.resources.prompts", "default_prompts.yaml") as f:
            return yaml.safe_load(f)

    def _load_custom_prompts(self) -> Dict[str, Any]:
        custom_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'custom_prompts.yaml'
        if custom_prompts_path.exists():
            with open(custom_prompts_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def _load_interface_prompts(self) -> Dict[str, Any]:
        with resources.open_text("repoai.resources.prompts", "interface_prompts.yaml") as f:
            return yaml.safe_load(f)

    def get_default_prompts(self) -> Dict[str, Dict[str, str]]:
        default_prompts = {}
        for task_id in self.default_prompts.keys():
            default_prompts[task_id] = {
                'system': self.get_llm_prompt(task_id, 'system'),
                'user': self.get_llm_prompt(task_id, 'user')
            }
        return default_prompts

    def get_llm_prompt(self, task_id: str, prompt_type: str = 'system', **kwargs) -> str:
        custom_prompt = self.custom_prompts.get(task_id, {}).get(prompt_type)
        if custom_prompt:
            return custom_prompt
        
        prompt_template = self.default_prompts.get(task_id, {}).get(prompt_type, '')
        template = self.jinja_env.from_string(prompt_template)
        return template.render(**kwargs)

    def get_interface_prompt(self, task_id: str, prompt_key: str, **kwargs) -> str:
        prompt_template = self.interface_prompts.get(task_id, {}).get(prompt_key, '')
        template = self.jinja_env.from_string(prompt_template)
        return template.render(**kwargs)

    def set_custom_llm_prompt(self, task_id: str, prompt: str, prompt_type: str = 'system'):
        if task_id not in self.custom_prompts:
            self.custom_prompts[task_id] = {}
        self.custom_prompts[task_id][prompt_type] = prompt
        self._save_custom_prompts()

    def set_interface_prompt(self, task_id: str, prompt_key: str, prompt: str):
        if task_id not in self.interface_prompts:
            self.interface_prompts[task_id] = {}
        self.interface_prompts[task_id][prompt_key] = prompt
        self._save_interface_prompts()

    def _save_custom_prompts(self):
        custom_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'custom_prompts.yaml'
        with open(custom_prompts_path, 'w') as f:
            yaml.dump(self.custom_prompts, f)

    def _save_interface_prompts(self):
        interface_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'interface_prompts.yaml'
        with open(interface_prompts_path, 'w') as f:
            yaml.dump(self.interface_prompts, f)

    def reset_llm_prompt(self, task_id: str, prompt_type: str = 'system'):
        if task_id in self.custom_prompts and prompt_type in self.custom_prompts[task_id]:
            del self.custom_prompts[task_id][prompt_type]
            if not self.custom_prompts[task_id]:
                del self.custom_prompts[task_id]
            self._save_custom_prompts()

    def reset_interface_prompt(self, task_id: str, prompt_key: str):
        if task_id in self.interface_prompts and prompt_key in self.interface_prompts[task_id]:
            del self.interface_prompts[task_id][prompt_key]
            if not self.interface_prompts[task_id]:
                del self.interface_prompts[task_id]
            self._save_interface_prompts()

    def list_prompts(self) -> Dict[str, Dict[str, Any]]:
        all_prompts = {}
        for task_id in set(list(self.default_prompts.keys()) + list(self.custom_prompts.keys())):
            all_prompts[task_id] = {
                'system': {
                    'default': self.default_prompts.get(task_id, {}).get('system', ''),
                    'custom': self.custom_prompts.get(task_id, {}).get('system', '')
                },
                'user': {
                    'default': self.default_prompts.get(task_id, {}).get('user', ''),
                    'custom': self.custom_prompts.get(task_id, {}).get('user', '')
                }
            }
        return all_prompts

    def list_interface_prompts(self) -> Dict[str, Dict[str, str]]:
        return self.interface_prompts