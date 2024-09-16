from typing import Dict, Any
from ...components.components_base import BaseTask
from ...services.llm_service import LLMService
from ...services.progress_service import ProgressService
from ...utils.common_utils import extract_code_blocks
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ProjectDescriptionChatTask(BaseTask):
    def __init__(self, llm_service: LLMService, progress_service: ProgressService, model_config: Dict[str, Any] = None):
        super().__init__()
        self.llm_service = llm_service
        self.progress_service = progress_service
        self.model_config = model_config or {}

    def execute(self, context: dict) -> None:
        messages = context.get('messages', [])
        user_input = context.get('user_input')
        
        if not messages:
            system_prompt = self.llm_service.config.get_llm_prompt(task_id='project_description_chat_task', prompt_type='system')
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            context['messages'] = messages

        if user_input:
            user_prompt = self.llm_service.config.get_llm_prompt(
                task_id='project_description_chat_task', prompt_type='user', project_info=user_input)
            messages.append({"role": "user", "content": user_prompt})
        else:
            if messages[-1]['role'] == 'user':
                pass
            else:
                raise Exception("No user input provided")

        response = self.llm_service.get_completion(messages=messages, **self.model_config)

        prompt, found = self._extract_description_prompt(response.content)
        if not found:
            assistant_content = response.content + "\n\n **Description Not Found**"
        else:
            assistant_content = response.content
        assistant_message = {"role": "assistant", "content": assistant_content}
        messages.append(assistant_message)

        context['messages'] = messages
        context['user_input'] = ""
        context['description'] = prompt

        self.progress_service.save_progress("project_description", context)

    def _extract_description_prompt(self, content: str) -> str:
        assert isinstance(content, str), f"Content must be a string, but got {type(content)}"
        assert content, "Content cannot be empty"
        prompts = extract_code_blocks(content)
        if prompts:
            prompt = prompts[0][1].strip()
            assert isinstance(prompt, str)
            return prompt, True
        else:
            prompt = content
            logger.warning("No text found in triple backticks in the assistant's response. Using the entire response as the prompt.")
            return prompt, False
