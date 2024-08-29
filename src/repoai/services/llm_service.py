import base64
from typing import Dict, List, Any, Union, AsyncGenerator
from litellm import completion, supports_vision, acompletion
from litellm.utils import get_llm_provider
from ..core.config_manager import ConfigManager
from ..utils.response_wrapper import ResponseRepoAI
from ..utils.token_counter import TokenCounter
from ..utils.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    def __init__(self, project_path: str, config: ConfigManager):
        self.project_path = project_path
        self.config = config
        self.token_counter = TokenCounter(self.project_path, self.config)
        self.cache_threshold = self.config.get('prompt_cache_threshold', 5000)

    def get_completion(self, messages: List[Dict[str, Any]], **kwargs) -> ResponseRepoAI:
        kwargs, provider = self.input_validation(**kwargs)
        model = kwargs["model"]

        if supports_vision(model):
            messages = self._process_vision_inputs(messages)

        if provider == "anthropic":
            kwargs = self._handle_anthropic_specific_features(kwargs, messages)
        else:
            kwargs['messages'] = messages

        input_tokens = self.token_counter.count_tokens(model, messages)

        response = completion(**kwargs)

        llm_response = ResponseRepoAI(response)

        output_tokens = self.token_counter.count_tokens(model, [{"role": "assistant", "content": llm_response.content}])

        self.token_counter.update_token_usage(model, provider, input_tokens, output_tokens)

        return llm_response

    async def get_acompletion(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[str, None]:
        kwargs, provider = self.input_validation(**kwargs)
        model = kwargs["model"]

        if supports_vision(model):
            messages = self._process_vision_inputs(messages)

        if provider == "anthropic":
            kwargs = self._handle_anthropic_specific_features(kwargs, messages)
        else:
            kwargs['messages'] = messages

        kwargs['stream'] = True

        async for chunk in await acompletion(**kwargs):
            yield chunk["choices"][0]["delta"].get("content", "")

    def _process_vision_inputs(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for message in messages:
            if message['role'] == 'user' and isinstance(message['content'], list):
                for item in message['content']:
                    if item['type'] == 'image_url':
                        item['image_url'] = self._process_image_url(item['image_url'])
                        logger.debug(f"Processed image URL: {item['image_url']}")
        return messages

    def _process_image_url(self, image_url: Union[str, Dict[str, str]]) -> Dict[str, str]:
        if isinstance(image_url, str):
            if image_url.startswith(('http://', 'https://')):
                return {'url': image_url}
            else:
                return {'url': f"data:image/jpeg;base64,{self._encode_image(image_url)}"}
        return image_url

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _handle_anthropic_specific_features(self, kwargs: Dict[str, Any], messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        use_prompt_caching = kwargs.pop('use_prompt_caching', False)
        if use_prompt_caching:
            messages = self._apply_prompt_caching(messages)
            kwargs = self._add_caching_headers(kwargs)

        if 'max_tokens' in kwargs:
            max_tokens = kwargs['max_tokens']
            if max_tokens > 8192:
                kwargs['max_tokens'] = 8192
                logger.debug(f"Changed max_tokens from {max_tokens} to {kwargs['max_tokens']} due to model limits")

        kwargs['messages'] = messages
        return kwargs

    def _apply_prompt_caching(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for message in messages:
            if message['role'] in ['system', 'user']:
                if isinstance(message['content'], list):
                    for item in message['content']:
                        if item['type'] == 'text' and len(item['text']) > self.cache_threshold:
                            item['cache_control'] = {"type": "ephemeral"}
                            logger.debug(f"Caching prompt of role '{message['role']}': {item['text'][:300]}...")
                elif isinstance(message['content'], str) and len(message['content']) > self.cache_threshold:
                    message['content'] = [
                        {
                            "type": "text",
                            "text": message['content'],
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                    logger.debug(f"Caching prompt of role '{message['role']}': {message['content'][0]['text'][:300]}...")
        return messages

    def _add_caching_headers(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        extra_headers = kwargs.get('extra_headers', {})
        extra_headers.update({
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-caching-2024-07-31",
        })
        kwargs['extra_headers'] = extra_headers
        logger.debug(f"Adding caching headers: {extra_headers}")
        return kwargs

    def input_validation(self, **kwargs) -> Dict[str, Any]:
        from_config = False
        if "model" not in kwargs:
            model = self.config.get('default_model')
            kwargs["model"] = model
            from_config = True
        if "api_base" not in kwargs:
            if from_config:
                api_base = self.config.get('api_base', None)
                kwargs["api_base"] = api_base
        _, provider, _, _ = get_llm_provider(model=kwargs["model"])
        return kwargs, provider

    def supports_vision(self, model: str) -> bool:
        return supports_vision(model)

    def get_global_token_usage(self) -> Dict[str, Dict[str, Any]]:
        return self.token_counter.get_global_token_usage()

    def get_project_token_usage(self) -> Dict[str, Dict[str, Any]]:
        return self.token_counter.get_project_token_usage()

    def get_interaction_token_usage(self) -> Dict[str, Any]:
        return self.token_counter.get_interaction_token_usage()