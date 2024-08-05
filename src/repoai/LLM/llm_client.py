# src/repoai/LLM/llm_client.py

import json
import os
from typing import List, Dict, Optional, Any
from pathlib import Path
from appdirs import AppDirs
from datetime import datetime
from .tool_handler import ToolHandler
from .llm_provider import LLMProvider, MessageType
from .providers.anthropic_provider import AnthropicProvider
from .providers.ollama_provider import OllamaProvider
from .providers.openai_provider import OpenAIProvider
from .providers.fireworks_provider import FireworksProvider
from .providers.groq_provider import GroqProvider
from ..config import Config
from ..utils.logger import setup_logger
from ..utils.context_managers import use_tools
from ..utils.config_manager import config_manager

dirs = AppDirs("repoai", "repoai")

logger = setup_logger(__name__)

class LLMManager:
    def __init__(self):
        self.current_phase = None
        self.tool_handler = ToolHandler()
        self.runtime_overrides = {}

    def set_current_phase(self, phase: str):
        self.current_phase = phase

    def set_runtime_override(self, key: str, value: Any):
        self.runtime_overrides[key] = value

    def clear_runtime_overrides(self):
        self.runtime_overrides.clear()

    def get_config(self, key: str, default: Any = None):
        # First check in runtime_overrides
        value = self.runtime_overrides
        for part in key.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                break

        if value is None:
            # If not found in runtime_overrides, check in config_manager
            value = config_manager.config
            for part in key.split('.'):
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    break
        return value if value is not None else default
 

    def _get_llm_provider(self, task: str) -> LLMProvider:
        model = self.get_config(f"task_model_mapping.{task}")
        provider = self.get_config(f"MODELS_PROVIDER_MAPPING.{model}")
        api_key = self.get_config(f"providers.{provider}.api_key")
        api_host = self.get_config(f"providers.{provider}.api_host")
        if provider == "anthropic":
            return AnthropicProvider(api_key, api_host)
        elif provider == "ollama":
            return OllamaProvider(api_key, api_host)
        elif provider == "openai":
            return OpenAIProvider(api_key, api_host)
        elif provider == "fireworks":
            return FireworksProvider(api_key, api_host)
        elif provider == "groq":
            return GroqProvider(api_key, api_host)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
    def get_response(self, task: str, system_prompt: str, messages: List[MessageType], **kwargs) -> Optional[str]:
        model = self.get_config(f"task_model_mapping.{task}")
        llm_provider = self._get_llm_provider(task)
        config = self.get_config(f"providers.{llm_provider.provider}.default_params", {})
        config = {**config, **kwargs}

        # Remove tool-related configurations if tools are not being used
        if not use_tools():
            config.pop('tools', None)
            config.pop('tool_choice', None)
        
        response_dc = llm_provider.get_response(model, system_prompt, messages, **config)
        
        if use_tools() and response_dc and 'tool_calls' in response_dc:
            # Handle tool calls
            tool_messages = self._handle_tool_calls(response_dc['tool_calls'])
            messages.extend(tool_messages)
            
            # Get a new response with the tool results
            response_dc = llm_provider.get_response(model, system_prompt, messages, **config)
        
        return self._process_response(response_dc, model, messages, task, system_prompt)

    def get_chat_response(self, task: str, messages: List[MessageType], **kwargs) -> Optional[str]:
        model = self.get_config(f"task_model_mapping.{task}")
        llm_provider = self._get_llm_provider(task)
        config = self.get_config(f"providers.{llm_provider.provider}.default_params", {})
        config = {**config, **kwargs}
        
        # Remove tool-related configurations if tools are not being used
        if not use_tools():
            config.pop('tools', None)
            config.pop('tool_choice', None)
        
        response_dc = llm_provider.get_chat_response(model, messages, **config)
        
        if use_tools() and response_dc and 'tool_calls' in response_dc:
            # Handle tool calls
            tool_messages = self._handle_tool_calls(response_dc['tool_calls'])
            messages.extend(tool_messages)
            
            # Get a new response with the tool results
            response_dc = llm_provider.get_chat_response(model, messages, **config)
        
        return self._process_response(response_dc, model, messages, task)

    def _handle_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        if not use_tools() or not self.tool_handler:
            return []
        tool_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call['function']['name']
            tool_args = json.loads(tool_call['function']['arguments'])
            try:
                tool_result = self.tool_handler.execute_tool(tool_name, **tool_args)
                tool_messages.append({
                    "role": "function",
                    "name": tool_name,
                    "content": json.dumps(tool_result)
                })
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                tool_messages.append({
                    "role": "function",
                    "name": tool_name,
                    "content": json.dumps({"error": str(e)})
                })
        return tool_messages

    def _process_response(self, response: Dict[str, Any], model: str, messages: List[MessageType], task: str, system_prompt: str = None) -> Optional[str]:
        if response is None:
            self._log_response(task, model, messages, None, system_prompt)
            return None
        
        self._log_response(task, model, messages, response["text"], system_prompt, response["input_tokens"], response["output_tokens"])
        if self.current_phase:
            Config.update_token_count(self.current_phase, model, response["input_tokens"], response["output_tokens"])
        return response
    
    def _log_response(self, task: str, model: str, messages: List[MessageType], response: Optional[str], system_prompt: str=None, input_tokens: int=0, output_tokens: int=0):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "provider": self.get_config(f"MODELS_PROVIDER_MAPPING.{model}"),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "system_prompt": system_prompt,
            "messages": messages,
            "response": response,
        }
        print(system_prompt)
        print("===========================")
        print(messages[-1]["content"])
        print("===========================")
        print(response)
        print("===========================")

        os.makedirs(dirs.user_data_dir, exist_ok=True)
        log_file = Config.get_llm_response_log_file(Path(dirs.user_data_dir))
        
        try:
            # Check if file size exceeds MAX_LOG_SIZE
            max_log_size = config_manager.get('MAX_LOG_SIZE', 10 * 1024 * 1024)  # Default to 10 MB if not set
            if os.path.exists(log_file) and os.path.getsize(log_file) > max_log_size:
                # Rename the current file
                backup_file = log_file.with_suffix(f".{datetime.now().strftime('%Y%m%d%H%M%S')}.jsonl")
                os.rename(log_file, backup_file)
                logger.info(f"Logging LLM file size exceeded {max_log_size} bytes. Rotated to {backup_file}")

            logger.info(f"Logging LLM response to: {log_file}")
            with open(log_file, "a") as f:
                f.write("\n<<REPOAI_LLM_LOG>>\n")
                json.dump(log_entry, f, indent=2)
                f.write("\n<</REPOAI_LLM_LOG>>\n")
        except IOError as e:
            logger.error(f"Error writing to log file {log_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while logging response: {str(e)}")