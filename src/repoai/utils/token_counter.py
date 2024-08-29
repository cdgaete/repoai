import json
from typing import Dict, List, Any
from pathlib import Path
from litellm import token_counter, cost_per_token
from ..core.config_manager import ConfigManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TokenCounter:
    def __init__(self, project_path: Path, config: ConfigManager):
        self.project_path = project_path
        self.config = config
        self.global_usage = self._load_global_usage()
        self.project_usage = self._load_project_usage()
        self.interaction_usage = self._initialize_interaction_usage()

    def _load_global_usage(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        global_usage_file = Path(self.config.get('global_token_usage_file'))
        if global_usage_file.exists():
            with open(global_usage_file, 'r') as f:
                return json.load(f)
        return {}

    def _load_project_usage(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        project_usage_file = self.project_path / self.config.get('project_token_usage_file')
        if project_usage_file.exists():
            with open(project_usage_file, 'r') as f:
                return json.load(f)
        return {}

    def _initialize_interaction_usage(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {}

    def _save_global_usage(self):
        global_usage_file = Path(self.config.get('global_token_usage_file'))
        with open(global_usage_file, 'w') as f:
            json.dump(self.global_usage, f, indent=2)

    def _save_project_usage(self):
        project_usage_file = self.project_path / self.config.get('project_token_usage_file')
        with open(project_usage_file, 'w') as f:
            json.dump(self.project_usage, f, indent=2)

    def count_tokens(self, model: str, messages: List[Dict[str, str]]) -> int:
        return token_counter(model=model, messages=messages)

    def update_token_usage(self, model: str, provider: str, input_tokens: int, output_tokens: int):
        total_tokens = input_tokens + output_tokens

        for usage in [self.global_usage, self.project_usage, self.interaction_usage]:
            if provider not in usage:
                usage[provider] = {}
            if model not in usage[provider]:
                usage[provider][model] = {
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0
                }
            usage[provider][model]['input_tokens'] += input_tokens
            usage[provider][model]['output_tokens'] += output_tokens
            usage[provider][model]['total_tokens'] += total_tokens

        # Update global usage
        try:
            prompt_cost, completion_cost = cost_per_token(model, input_tokens, output_tokens)
        except Exception as e:
            logger.debug(f"Error in cost calculation: {str(e)}", exc_info=True)
            prompt_cost = 0.0
            completion_cost = 0.0
        total_cost = prompt_cost + completion_cost
        
        for usage in [self.global_usage, self.project_usage, self.interaction_usage]:
            usage[provider][model]['total_cost'] += total_cost

        self._save_global_usage()
        self._save_project_usage()

    def get_global_token_usage(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return self.global_usage

    def get_project_token_usage(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return self.project_usage

    def get_interaction_token_usage(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return self.interaction_usage

    def reset_interaction_usage(self):
        self.interaction_usage = self._initialize_interaction_usage()