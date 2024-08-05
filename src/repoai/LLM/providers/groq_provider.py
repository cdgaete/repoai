# src/repoai/LLM/providers/groq_provider.py

from typing import Optional
from openai import OpenAI
from .openai_provider import OpenAIProvider
from ...utils.config_manager import config_manager

class GroqProvider(OpenAIProvider):
    def __init__(self, api_key: str, api_host: Optional[str] = None):
        super().__init__(api_key, api_host)
        self.provider = "groq"
        self.client = OpenAI(api_key=api_key, base_url=api_host or config_manager.get('GROQ_API_HOST', 'https://api.groq.com/openai/v1'))