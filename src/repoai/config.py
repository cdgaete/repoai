# src/repoai/config.py

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from .utils.config_manager import config_manager
from .utils.logger import setup_logger

logger = setup_logger(__name__)

class Config:
    PROJECT_PATH: Optional[Path] = None
    PROJECT_REPOAI_PATH: Optional[Path] = None

    @classmethod
    def set_current_project(cls, project_path: str | Path) -> None:
        if isinstance(project_path, str):
            cls.PROJECT_PATH = Path(project_path)
        else:
            cls.PROJECT_PATH = project_path

        cls.PROJECT_REPOAI_PATH = cls.PROJECT_PATH / ".repoai"
        cls.PROJECT_REPOAI_PATH.mkdir(parents=True, exist_ok=True)
        config_file = cls.PROJECT_REPOAI_PATH / "config.json"
        cls.ensure_project_config_exists(config_file)
        config_manager.set_project_config(config_file)

    @classmethod
    def ensure_project_config_exists(cls, config_file: Path) -> None:
        if not config_file.exists():
            logger.info(f"Creating initial config.json for project: {cls.PROJECT_PATH.name}")
            initial_config = {
                "task_model_mapping": {}
            }
            config_manager.save_json(config_file, initial_config)
        
    @classmethod
    def get_provider_api_key(cls, provider: str) -> Optional[str]:
        return config_manager.get_provider_config(provider).get('api_key')

    @classmethod
    def get_provider_api_host(cls, provider: str) -> Optional[str]:
        return config_manager.get_provider_config(provider).get('api_host')

    @classmethod
    def get_model_for_task(cls, task: str) -> str:
        return config_manager.get_task_model(task)

    @classmethod
    def get_prompt(cls, prompt_name: str) -> str:
        return config_manager.get_system_prompt(prompt_name)

    @classmethod
    def get_provider_for_model(cls, model: str) -> str:
        models_provider_mapping = config_manager.get('MODELS_PROVIDER_MAPPING', {})
        if model in models_provider_mapping:
            return models_provider_mapping[model]
        else:
            raise ValueError(f"Unsupported model: {model}")
    
    @classmethod
    def get_current_project_path(cls, *paths) -> Path:
        if cls.PROJECT_PATH is None:
            raise ValueError("PROJECT_PATH has not been set. Use set_current_project() first.")
        return cls.PROJECT_PATH.joinpath(*paths)

    @classmethod
    def set_task_model(cls, task: str, model: str) -> None:
        models_provider_mapping = config_manager.get('MODELS_PROVIDER_MAPPING', {})
        task_model_mapping = config_manager.get('task_model_mapping', {})
        if model not in models_provider_mapping:
            raise ValueError(f"Unsupported model: {model}")
        if task not in task_model_mapping:
            raise ValueError(f"Unsupported task: {task}")
        config_manager.set(f'task_model_mapping.{task}', model)

    @classmethod
    def get_ignore_file_path(cls, dir_path: Path) -> Path:
        return dir_path / ".repoai" / config_manager.get('IGNORE_FILE', '.repoaiignore')

    @classmethod
    def get_available_tools(cls):
        return config_manager.get('AVAILABLE_TOOLS', [])

    @classmethod
    def load_token_counts(cls):
        if cls.PROJECT_PATH is None:
            return {"creation": {}, "edition": {}}
        
        token_counts_path = cls.PROJECT_REPOAI_PATH / config_manager.get('TOKEN_COUNTS_FILE', 'token_counts.json')
        if token_counts_path.exists():
            return config_manager.load_json(token_counts_path)
        else:
            # Create a new file with default values
            default_counts = cls._get_default_token_counts()
            cls.save_token_counts(default_counts)
            return default_counts
        
    @classmethod
    def save_token_counts(cls, token_counts: Dict[str, Dict[str, Dict[str, int]]]):
        if cls.PROJECT_PATH is None:
            logger.warning("Cannot save token counts: No current project path set")
            return
        
        token_counts_path = cls.PROJECT_REPOAI_PATH / config_manager.get('TOKEN_COUNTS_FILE', 'token_counts.json')
        config_manager.save_json(token_counts_path, token_counts)
        logger.info(f"Token counts saved to {token_counts_path}")

    @classmethod
    def update_token_count(cls, phase: str, model: str, input_tokens: int, output_tokens: int):
        token_counts = cls.load_token_counts()
        if phase not in token_counts:
            token_counts[phase] = {}
        
        if model not in token_counts[phase]:
            token_counts[phase][model] = {"input": 0, "output": 0}
        
        token_counts[phase][model]["input"] += input_tokens
        token_counts[phase][model]["output"] += output_tokens
        
        cls.save_token_counts(token_counts)

    @classmethod
    def get_token_counts(cls) -> Dict[str, Dict[str, Dict[str, int]]]:
        return cls.load_token_counts()

    @classmethod
    def _get_default_token_counts(cls) -> Dict[str, Dict[str, Dict[str, int]]]:
        default_counts = {"creation": {}, "edition": {}}
        models_provider_mapping = config_manager.get('MODELS_PROVIDER_MAPPING', {})
        for phase in ["creation", "edition"]:
            for model in models_provider_mapping.keys():
                default_counts[phase][model] = {"input": 0, "output": 0}
        return default_counts

    @classmethod
    def get_llm_response_log_file(cls, dir_path: Path) -> Path:
        return Path(dir_path) / config_manager.get('LLM_RESPONSE_LOG', 'llm_response_log.jsonl')

Config = Config()