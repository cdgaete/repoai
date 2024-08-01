# src/repoai/LLM/providers/openai_provider.py

from openai import OpenAI
from openai import APIError, APITimeoutError, APIConnectionError, RateLimitError
from typing import Optional, List, Any, Dict
from ..llm_provider import LLMProvider
from ..llm_provider import MessageType
from ...utils.exceptions import OverloadedError, ConnectionError
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, api_host: Optional[str] = None):
        super().__init__("openai", api_key, api_host)
        self.client = OpenAI(api_key=api_key, base_url=api_host)

    def get_response(self, model: str, system_prompt: str, messages: List[MessageType], **kwargs) -> Optional[Dict[str, Any]]:
        try:
            openai_messages = [{"role": "system", "content": system_prompt}] + messages
            
            # Format tools if present
            if 'tools' in kwargs and kwargs['tools']:
                kwargs['tools'] = self._format_tools_for_openai(kwargs['tools'])
            elif 'tools' in kwargs:
                del kwargs['tools']
            
            response = self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                **kwargs
            )
            return self.formated_response(response)
        except Exception as e:
            self._handle_exception(e)

    def get_chat_response(self, model: str, messages: List[MessageType], **kwargs) -> Optional[Dict[str, Any]]:
        try:
            # Format tools if present
            if 'tools' in kwargs and kwargs['tools']:
                kwargs['tools'] = self._format_tools_for_openai(kwargs['tools'])
            elif 'tools' in kwargs:
                del kwargs['tools']
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return self.formated_response(response)
        except Exception as e:
            self._handle_exception(e)

    def _handle_exception(self, e: Exception) -> None:
        if isinstance(e, APITimeoutError):
            logger.error(f"OpenAI API request timed out: {str(e)}")
            raise ConnectionError("The request to the OpenAI API timed out. Please try again later.")
        elif isinstance(e, APIConnectionError):
            logger.error(f"Error connecting to OpenAI API: {str(e)}")
            raise ConnectionError("Unable to connect to the OpenAI service. Please check your internet connection and try again.")
        elif isinstance(e, RateLimitError):
            logger.error(f"OpenAI API rate limit exceeded: {str(e)}")
            raise OverloadedError("The OpenAI service is currently overloaded. Please try again in a few minutes.")
        elif isinstance(e, APIError):
            logger.error(f"OpenAI API returned an error: {str(e)}")
            raise RuntimeError(f"An error occurred while processing your request: {str(e)}")
        else:
            logger.error(f"Unexpected error while getting OpenAI response: {str(e)}")
            raise RuntimeError(f"An unexpected error occurred: {str(e)}")

    def formated_response(self, response: Any) -> Optional[Dict[str, Any]]:
        if hasattr(response, 'choices') and len(response.choices) > 0:
            result = {
                "text": response.choices[0].message.content,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "tool_calls": []
            }
            
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
            
            return result
        else:
            logger.error("Unexpected response content type")
            return None

    def _format_tools_for_openai(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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