from typing import Dict, List, Literal, Optional

MessageType = Dict[Literal["role", "content"], str]

class LLMProvider:
    def __init__(self, provider: str, api_key: Optional[str] = None, api_host: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self.api_host = api_host

    def get_response(self, model: str, system_prompt: str, messages: List[MessageType]) -> Optional[str]:
        raise NotImplementedError

    def get_chat_response(self, model: str, messages: List[MessageType]) -> Optional[str]:
        raise NotImplementedError
