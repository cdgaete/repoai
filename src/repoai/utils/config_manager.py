# src/repoai/utils/config_manager.py

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from appdirs import user_config_dir
from .config_constants import DEFAULT_CONFIG


class ConfigManager:

    DEFAULT_CONFIG = DEFAULT_CONFIG

    def __init__(self):
        self.config_dir = Path(user_config_dir("repoai", "repoai"))
        self.global_config_file = self.config_dir / "config.json"
        self.project_config_file = None
        self.config = self.load_config()
        print(f"Global config file: {self.global_config_file}")
        if self.project_config_file:
            print(f"Project config file: {self.project_config_file}")

    def load_config(self) -> Dict[str, Any]:
        global_config = self._load_json_file(self.global_config_file, self.DEFAULT_CONFIG)
        if self.project_config_file:
            project_config = self._load_json_file(self.project_config_file, {})
            return self._merge_configs(global_config, project_config)
        return global_config

    def _load_json_file(self, file_path: Path, default_value: Dict[str, Any]) -> Dict[str, Any]:
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return default_value

    def _merge_configs(self, global_config: Dict[str, Any], project_config: Dict[str, Any]) -> Dict[str, Any]:
        merged = global_config.copy()
        for key, value in project_config.items():
            if isinstance(value, dict) and key in merged:
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any, project_specific: bool = False) -> None:
        if project_specific and self.project_config_file:
            project_config = self._load_json_file(self.project_config_file, {})
            self._set_nested(project_config, key.split('.'), value)
            self._save_json_file(self.project_config_file, project_config)
            print(f"Project-specific configuration updated and saved: {key} = {value}")
        else:
            self._set_nested(self.config, key.split('.'), value)
            self._save_json_file(self.global_config_file, self.config)
            print(f"Global configuration updated and saved: {key} = {value}")
        
        # Reload the configuration after saving
        self.config = self.load_config()

    def set_project_config(self, project_config_file: Union[Path, str]) -> None:
        if isinstance(project_config_file, str):
            project_config_file = Path(project_config_file)
        self.project_config_file = project_config_file
        self.config = self.load_config()

    def _set_nested(self, config: Dict[str, Any], keys: list, value: Any) -> None:
        for key in keys[:-1]:
            config = config.setdefault(key, {})
        config[keys[-1]] = value

    def _save_json_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def reset_to_default(self) -> None:
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_json_file(self.global_config_file, self.config)
        if self.project_config_file:
            self._save_json_file(self.project_config_file, {})

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        return self.config['providers'].get(provider, {})

    def get_task_model(self, task: str) -> str:
        # First, check project-specific config
        if self.project_config_file:
            project_config = self._load_json_file(self.project_config_file, {})
            if 'task_model_mapping' in project_config and task in project_config['task_model_mapping']:
                return project_config['task_model_mapping'][task]
        
        # Then, check global config
        if 'task_model_mapping' in self.config and task in self.config['task_model_mapping']:
            return self.config['task_model_mapping'][task]
        
        # Finally, fall back to default config
        if task in self.DEFAULT_CONFIG['task_model_mapping']:
            return self.DEFAULT_CONFIG['task_model_mapping'][task]
        
        # If no mapping found, return a default model
        return self.DEFAULT_CONFIG['task_model_mapping'].get('default', 'claude-3-5-sonnet-20240620')


    def get_system_prompt(self, prompt_key: str) -> str:
        return self.config['system_prompts'].get(prompt_key, self.DEFAULT_CONFIG['system_prompts'].get(prompt_key))

    def load_json(self, file_path_or_object):
        if isinstance(file_path_or_object, (str, Path)):
            with open(file_path_or_object, 'r') as f:
                return json.load(f)
        elif hasattr(file_path_or_object, 'read'):
            return json.load(file_path_or_object)
        else:
            raise TypeError("Expected str, Path, or file-like object")


    def save_json(self, file_path: Union[str, Path], data: Dict[str, Any]) -> None:
        if not isinstance(file_path, (str, Path)):
            raise TypeError("file_path must be a string or Path object")
        file_path = Path(file_path)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with file_path.open('w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Successfully saved JSON data to {file_path}")
        except IOError as e:
            print(f"Error saving JSON data to {file_path}: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error while saving JSON data to {file_path}: {str(e)}")
            raise

config_manager = ConfigManager()