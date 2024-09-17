import json
from pathlib import Path
import appdirs
from jinja2 import Environment, FileSystemLoader
from importlib import resources
import yaml
from typing import Dict, Any
from .prompt_manager import PromptManager
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ConfigManager:
    CONFIG_FILE = 'repoai_config.json'
    REPOAI_DIR = ".repoai"

    def __init__(self):
        self.global_config = {}
        self.project_config = {}
        self.config_dir = Path(appdirs.user_config_dir("repoai"))
        self.user_dir = Path(appdirs.user_data_dir("repoai"))
        self.load_global_config()
        self.prompt_manager = None
        self.jinja_env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / 'resources' / 'templates')))
    
    def load_global_config(self):
        config_file = self.config_dir / self.CONFIG_FILE

        if config_file.exists():
            with open(config_file, 'r') as f:
                self.global_config = json.load(f)
        else:
            self.set_default_global_config()
    
    def save_global_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / self.CONFIG_FILE
        with open(config_file, 'w') as f:
            json.dump(self.global_config, f, indent=2)

    def get(self, key, default=None):
        return self.project_config.get(key, self.global_config.get(key, default))

    def set(self, key, value, is_global=False):
        if is_global:
            self.global_config[key] = value
            self.save_global_config()
        else:
            self.project_config[key] = value

    def load_project_config(self, project_path:Path):
        self.project_path = project_path
        config_file_path = project_path / self.REPOAI_DIR / self.CONFIG_FILE
        if config_file_path.exists():
            with open(config_file_path, 'r') as f:
                self.project_config = json.load(f)
        else:
            self.project_config = {}
        self.prompt_manager = PromptManager(self)

    def save_project_config(self, project_path:Path):
        config_content = json.dumps(self.project_config, indent=2)
        config_file_path = project_path / self.REPOAI_DIR / self.CONFIG_FILE

        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w') as f:
            f.write(config_content)

    def set_default_global_config(self):
        try:
            logger.debug("Attempting to load default_config.yaml")
            with resources.open_text("repoai.resources.config", "default_config.yaml") as f:
                self.global_config = yaml.safe_load(f)
            logger.debug("Successfully loaded default_config.yaml")
        except FileNotFoundError as e:
            logger.error(f"Error loading default_config.yaml: {e}")
            logger.warning("Using built-in defaults.")
            self.global_config = self._get_default_config()
        self.save_global_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "default_model": "anthropic/claude-3-5-sonnet-20240620",
            "log_level": "INFO",
            "log_file": str(self.user_dir / "repoai.log"),
            "max_log_file_size": 10485760,  # 10 MB
            "log_backup_count": 5,
            "max_commit_history": 10,
            "docker_compose_file": "docker-compose.yml",
            "global_token_usage_file": str(self.user_dir / "global_token_usage.json"),
            "project_token_usage_file": ".repoai/token_usage.json",
            "repoai_ignore_file": ".repoai/.repoaiignore",
            "prompt_cache_threshold": 20000,
            "plugin_dir": str(self.user_dir / "plugins"),
        }

    def render_template(self, template_name: str, **kwargs):
        template = self.jinja_env.get_template(f"{template_name}.j2")
        return template.render(**kwargs)

    def get_llm_prompt(self, task_id: str, prompt_type: str = 'system', **kwargs) -> str:
        if self.prompt_manager:
            return self.prompt_manager.get_llm_prompt(task_id=task_id, prompt_type=prompt_type, **kwargs)
        return ''

    def get_interface_prompt(self, task_id: str, prompt_key: str, **kwargs) -> str:
        if self.prompt_manager:
            return self.prompt_manager.get_interface_prompt(task_id=task_id, prompt_key=prompt_key, **kwargs)
        return ''

    def set_custom_llm_prompt(self, task_id: str, prompt: str, prompt_type: str = 'system'):
        if self.prompt_manager:
            self.prompt_manager.set_custom_llm_prompt(task_id, prompt, prompt_type)

    def set_interface_prompt(self, task_id: str, prompt_key: str, prompt: str):
        if self.prompt_manager:
            self.prompt_manager.set_interface_prompt(task_id, prompt_key, prompt)

    def reset_llm_prompt(self, task_id: str, prompt_type: str = 'system'):
        if self.prompt_manager:
            self.prompt_manager.reset_llm_prompt(task_id, prompt_type)

    def reset_interface_prompt(self, task_id: str, prompt_key: str):
        if self.prompt_manager:
            self.prompt_manager.reset_interface_prompt(task_id, prompt_key)

    def list_llm_prompts(self):
        if self.prompt_manager:
            return self.prompt_manager.list_prompts()
        return {}

    def list_interface_prompts(self):
        if self.prompt_manager:
            return self.prompt_manager.list_interface_prompts()
        return {}

    def get_model_config(self) -> Dict[str, Any]:
        return self.project_config.get('model_config', {})

    def update_model_config(self, config: Dict[str, Any]):
        self.project_config['model_config'] = config
        self.save_project_config(self.project_path)

    def get_default_prompts(self) -> Dict[str, Dict[str, str]]:
        return self.prompt_manager.get_default_prompts()

    def update_custom_prompts(self, prompts: Dict[str, Dict[str, str]]):
        for task_id, prompt_data in prompts.items():
            self.prompt_manager.set_custom_llm_prompt(task_id, prompt_data['system'], 'system')
            self.prompt_manager.set_custom_llm_prompt(task_id, prompt_data['user'], 'user')
        self.save_project_config(self.project_path)