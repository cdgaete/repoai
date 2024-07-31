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
from ..config import Config
from ..utils.logger import setup_logger
from ..utils.context_managers import use_tools

dirs = AppDirs("repoai", "repoai")

logger = setup_logger(__name__)

class LLMManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.current_project = None
        self.current_phase = None
        self.tool_handler = ToolHandler()

    def set_current_project(self, project_name: str):
        self.current_project = project_name

    def set_current_phase(self, phase: str):
        self.current_phase = phase

    def _get_llm_provider(self, task: str) -> LLMProvider:
        model = Config.get_model_for_task(task)
        provider = Config.get_provider_for_model(model)
        api_key = Config.get_provider_api_key(provider)
        api_host = Config.get_provider_api_host(provider)
        if provider == "anthropic":
            return AnthropicProvider(api_key, api_host)
        elif provider == "ollama":
            return OllamaProvider(api_key, api_host)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
    def get_response(self, task: str, system_prompt: str, messages: List[MessageType], **kwargs) -> Optional[str]:
        model = Config.get_model_for_task(task)
        llm_provider = self._get_llm_provider(task)
        config = Config.get_model_config(model)
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
        model = Config.get_model_for_task(task)
        llm_provider = self._get_llm_provider(task)
        config = Config.get_model_config(model)
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
        return response["text"]
    
    def _log_response(self, task: str, model: str, messages: List[MessageType], response: Optional[str], system_prompt: str=None, input_tokens: int=0, output_tokens: int=0):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "provider": Config.get_provider_for_model(model),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "system_prompt": system_prompt,
            "messages": messages,
            "response": response,
        }

        os.makedirs(dirs.user_data_dir, exist_ok=True)
        log_file = Config.get_llm_response_log_file(dirs.user_data_dir)
        
        try:
            # Check if file size exceeds MAX_LOG_SIZE
            if os.path.exists(log_file) and os.path.getsize(log_file) > Config.MAX_LOG_SIZE:
                # Rename the current file
                backup_file = log_file.with_suffix(f".{datetime.now().strftime('%Y%m%d%H%M%S')}.jsonl")
                os.rename(log_file, backup_file)
                logger.info(f"Logging LLM file size exceeded {Config.MAX_LOG_SIZE} bytes. Rotated to {backup_file}")

            logger.info(f"Logging LLM response to: {log_file}")
            with open(log_file, "a") as f:
                f.write("\n<<REPOAI_LLM_LOG>>\n")
                json.dump(log_entry, f, indent=2)
                f.write("\n<</REPOAI_LLM_LOG>>\n")
        except IOError as e:
            logger.error(f"Error writing to log file {log_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while logging response: {str(e)}")