import json
from pathlib import Path
import appdirs
from jinja2 import Environment, FileSystemLoader
from importlib import resources
import yaml
from .prompt_manager import PromptManager

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
        self.jinja_env = Environment(loader=FileSystemLoader(str(Path(__file__).parent)))
    
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
        with resources.open_text("repoai.core", "default_config.yaml") as f:
            self.global_config = yaml.safe_load(f)
        self.save_global_config()

    def get_prompt(self, task_id: str) -> str:
        if self.prompt_manager:
            return self.prompt_manager.get_prompt(task_id)
        return ''

    def set_custom_prompt(self, task_id: str, prompt: str):
        if self.prompt_manager:
            self.prompt_manager.set_custom_prompt(task_id, prompt)

    def reset_prompt(self, task_id: str):
        if self.prompt_manager:
            self.prompt_manager.reset_prompt(task_id)

    def list_prompts(self):
        if self.prompt_manager:
            return self.prompt_manager.list_prompts()
        return {}

    def render_template(self, template_name: str, **kwargs):
        template = self.jinja_env.get_template(f"{template_name}.j2")
        return template.render(**kwargs)