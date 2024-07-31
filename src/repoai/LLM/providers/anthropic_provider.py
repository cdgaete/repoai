# src/repoai/LLM/providers/anthropic_provider.py

import anthropic
from typing import Optional, Iterable, List, Any, Dict
from ..llm_provider import LLMProvider
from ..llm_provider import MessageType
from ...utils.exceptions import OverloadedError
from ...utils.exceptions import ConnectionError
from ...utils.logger import setup_logger

logger = setup_logger(__name__)

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, api_host: Optional[str] = None):
        super().__init__("anthropic", api_key, api_host)
        self.client = anthropic.Client(api_key=api_key)

    def get_response(self, model: str, system_prompt: str, messages: List[MessageType], **kwargs) -> Optional[str]:
        try:
            anthropic_messages: Iterable[anthropic.types.MessageParam] = [
                {"role": msg["role"], "content": msg["content"]} for msg in messages if msg["role"] != "system"
            ]
            
            # Format tools if present
            if 'tools' in kwargs and kwargs['tools']:
                kwargs['tools'] = self._format_tools_for_anthropic(kwargs['tools'])
            elif 'tools' in kwargs:
                del kwargs['tools']
            
            response = self.client.messages.create(
                            messages=anthropic_messages,
                            model=model,
                            system=system_prompt,
                            **kwargs
                            )
            return self.formated_response(response)
        except anthropic.APIConnectionError as e:
            logger.error(f"Error connecting to Anthropic API: {str(e)}")
            raise ConnectionError("Unable to connect to the AI service. Please check your internet connection and try again.")
        except anthropic.APIStatusError as e:
            logger.error(f"API returned an error: {str(e)}")
            if e.status_code == 529:
                raise OverloadedError("The AI service is currently overloaded. Please try again in a few minutes.")
            else:
                raise RuntimeError(f"An error occurred while processing your request: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while getting AI response: {str(e)}")
            raise RuntimeError(f"An unexpected error occurred: {str(e)}")

    def get_chat_response(self, model: str, messages: List[MessageType], **kwargs) -> Optional[str]:
        try:
            system_prompt = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
            anthropic_messages: Iterable[anthropic.types.MessageParam] = [
                {"role": msg["role"], "content": msg["content"]} for msg in messages if msg["role"] != "system"
            ]
            
            # Format tools if present
            if 'tools' in kwargs and kwargs['tools']:
                kwargs['tools'] = self._format_tools_for_anthropic(kwargs['tools'])
            elif 'tools' in kwargs:
                del kwargs['tools']
            
            response = self.client.messages.create(
                            messages=anthropic_messages,
                            model=model,
                            system=system_prompt,
                            **kwargs
                            )
            return self.formated_response(response)
        except anthropic.APIConnectionError as e:
            logger.error(f"Error connecting to Anthropic API: {str(e)}")
            raise ConnectionError("Unable to connect to the AI service. Please check your internet connection and try again.")
        except anthropic.APIStatusError as e:
            logger.error(f"API returned an error: {str(e)}")
            if e.status_code == 529:
                raise OverloadedError("The AI service is currently overloaded. Please try again in a few minutes.")
            else:
                raise RuntimeError(f"An error occurred while processing your request: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while getting AI chat response: {str(e)}")
            raise RuntimeError(f"An unexpected error occurred: {str(e)}")
        
    def formated_response(self, response: Any) -> Optional[Dict[str, Any]]:
        if isinstance(response, anthropic.types.Message):
            result = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "tool_calls": []
            }
            
            for content in response.content:
                if isinstance(content, anthropic.types.TextBlock):
                    result["text"] = content.text
                elif isinstance(content, anthropic.types.ToolCallBlock):
                    result["tool_calls"].append({
                        "id": content.id,
                        "type": "function",
                        "function": {
                            "name": content.name,
                            "arguments": content.arguments
                        }
                    })
            
            return result
        else:
            logger.error("Unexpected response content type")
            return None

    def _format_tools_for_anthropic(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted_tools = []
        for tool in tools:
            formatted_tool = self.convert_schema(tool)
            formatted_tools.append(formatted_tool)
        return formatted_tools

    def convert_schema(self, input_schema):
        output_schema = {
            "name": input_schema["name"],
            "description": input_schema["description"],
            "input_schema": input_schema["input_schema"]
        }
        return output_schema