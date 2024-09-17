from ..defaults.default_llm_prompts import DEFAULT_LLM_PROMPTS
from ..defaults.default_interface_prompts import DEFAULT_INTERFACE_PROMPTS
from jinja2 import Environment, BaseLoader
from typing import Dict, Any
import yaml
from pathlib import Path

class PromptManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.default_llm_prompts = DEFAULT_LLM_PROMPTS
        self.custom_llm_prompts = self._load_custom_llm_prompts()
        self.interface_prompts = DEFAULT_INTERFACE_PROMPTS
        self.jinja_env = Environment(loader=BaseLoader())

    def _load_custom_llm_prompts(self) -> Dict[str, Any]:
        custom_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'custom_llm_prompts.yaml'
        if custom_prompts_path.exists():
            with open(custom_prompts_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def get_default_llm_prompts(self) -> Dict[str, Dict[str, str]]:
        return self.default_llm_prompts

    def get_llm_prompt(self, task_id: str, prompt_type: str = 'system', **kwargs) -> str:
        custom_prompt = self.custom_llm_prompts.get(task_id, {}).get(prompt_type)
        if custom_prompt:
            return custom_prompt
        
        prompt_template = self.default_llm_prompts.get(task_id, {}).get(prompt_type, '')
        template = self.jinja_env.from_string(prompt_template)
        return template.render(**kwargs)

    def get_interface_prompt(self, task_id: str, prompt_key: str, **kwargs) -> str:
        prompt_template = self.interface_prompts.get(task_id, {}).get(prompt_key, '')
        template = self.jinja_env.from_string(prompt_template)
        return template.render(**kwargs)

    def set_custom_llm_prompt(self, task_id: str, prompt: str, prompt_type: str = 'system'):
        if task_id not in self.custom_llm_prompts:
            self.custom_llm_prompts[task_id] = {}
        self.custom_llm_prompts[task_id][prompt_type] = prompt
        self._save_custom_llm_prompts()

    def set_interface_prompt(self, task_id: str, prompt: str, prompt_key: str):
        if task_id not in self.interface_prompts:
            self.interface_prompts[task_id] = {}
        self.interface_prompts[task_id][prompt_key] = prompt

    def _save_custom_llm_prompts(self):
        custom_prompts_path = Path(self.config_manager.project_path) / self.config_manager.REPOAI_DIR / 'custom_llm_prompts.yaml'
        with open(custom_prompts_path, 'w') as f:
            yaml.dump(self.custom_llm_prompts, f)

    def reset_llm_prompt(self, task_id: str, prompt_type: str = 'system'):
        if task_id in self.custom_llm_prompts and prompt_type in self.custom_llm_prompts[task_id]:
            del self.custom_llm_prompts[task_id][prompt_type]
            if not self.custom_llm_prompts[task_id]:
                del self.custom_llm_prompts[task_id]
            self._save_custom_llm_prompts()

    def reset_interface_prompt(self, task_id: str, prompt_key: str):
        if task_id in self.interface_prompts and prompt_key in self.interface_prompts[task_id]:
            del self.interface_prompts[task_id][prompt_key]

    def list_llm_prompts(self) -> Dict[str, Dict[str, Any]]:
        all_prompts = {}
        for task_id in set(list(self.default_llm_prompts.keys()) + list(self.custom_llm_prompts.keys())):
            all_prompts[task_id] = {
                'system': {
                    'default': self.default_llm_prompts.get(task_id, {}).get('system', ''),
                    'custom': self.custom_llm_prompts.get(task_id, {}).get('system', '')
                },
                'user': {
                    'default': self.default_llm_prompts.get(task_id, {}).get('user', ''),
                    'custom': self.custom_llm_prompts.get(task_id, {}).get('user', '')
                }
            }
        return all_prompts

    def list_interface_prompts(self) -> Dict[str, Dict[str, str]]:
        return self.interface_prompts