import ollama
from typing import Optional, List, Any, Dict
from ..llm_provider import LLMProvider
from ..llm_provider import MessageType
from ...config import Config
from ...utils.exceptions import OverloadedError, ConnectionError
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

class OllamaProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, api_host: str = "http://localhost:11434") -> None:
        super().__init__("ollama", api_key, api_host)
        self.client = ollama.Client(host=api_host)

    def get_response(self, model: str, system_prompt: str, messages: List[MessageType], **kwargs) -> Optional[str]:
        try:
            # Ollama doesn't have a separate system prompt, so we'll add it as a system message
            ollama_messages = [{"role": "system", "content": system_prompt}] + messages
            
            return self._make_ollama_request(model, ollama_messages, **kwargs)
        except Exception as e:
            return self._handle_exception(e)

    def get_chat_response(self, model: str, messages: List[MessageType], **kwargs) -> Optional[str]:
        try:
            return self._make_ollama_request(model, messages, **kwargs)
        except Exception as e:
            return self._handle_exception(e)
        
    def _make_ollama_request(self, model: str, messages: List[MessageType], **kwargs) -> Optional[str]:
        # Convert tools to Ollama format if present
        tools = kwargs.pop('tools', None)
        if tools:
            tools = self._format_tools_for_ollama(tools)
        
        response = self.client.chat(model=model, messages=messages, tools=tools, **kwargs)
        return self.formated_response(response)
    
    def _handle_exception(self, e: Exception) -> None:
        if isinstance(e, ollama.ResponseError):
            if e.status_code == 429:
                raise OverloadedError("Ollama service is currently overloaded. Please try again in a few minutes.")
            elif e.status_code in (500, 502, 503, 504):
                raise ConnectionError("Unable to connect to the Ollama service. Please check your internet connection and try again.")
            else:
                raise RuntimeError(f"An error occurred while processing your request: {str(e)}")
        else:
            raise RuntimeError(f"An unexpected error occurred: {str(e)}")
        
    def formated_response(self, response: Any) -> Optional[Dict[str, Any]]:
        if isinstance(response, dict):
            input_tokens = len(response.get('prompt', '')) // 4  # Rough estimate
            output_tokens = len(response.get('message', {}).get('content', '')) // 4  # Rough estimate
            
            formatted_response = {
                "text": response['message']['content'],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "tool_calls": response['message'].get('tool_calls', [])
            }
            
            return formatted_response
        else:
            logger.error("Unexpected response content type")
            return None

    def _format_tools_for_ollama(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted_tools = []
        for tool in tools:
            formatted_tool = self.convert_schema(tool)
            formatted_tools.append(formatted_tool)
        return formatted_tools
    
    def convert_schema(self, input_schema):
        output_schema = {
                "type": "function",
                "function": {
                    "name": input_schema['name'],
                    "description": input_schema['description'],
                    "parameters": input_schema['input_schema']
                }
            }
        return output_schema