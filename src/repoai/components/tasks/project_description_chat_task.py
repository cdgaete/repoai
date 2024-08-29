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
        self._process_chat(context)

    def _process_chat(self, context: dict):
        messages = context.get('messages', [])
        if not messages:
            system_message = (
                "You are an AI assistant helping to create a detailed project description called 'project prompt'. "
                "This project prompt must be written in an instructive style. "
                "The project prompt must be enclosed with triple backticks. "
                "After each interaction, update the project prompt to reflect the latest information. "
                "Ask questions to gather information and provide suggestions. "
                "The prompt should be a comprehensive description of the project, including its purpose, "
                "main features, and any technical requirements. "
            )
            messages = [
                {"role": "system", "content": system_message},
            ]
            context['messages'] = messages

        user_input = context.get('user_input')
        if user_input:
            messages.append({"role": "user", "content": user_input})
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

        # Save progress after each interaction
        self.progress_service.save_progress("project_description", context)

    def _extract_description_prompt(self, content: str) -> str:
        assert isinstance(content, str), f"Content must be a string, but got {type(content)}"
        assert content, "Content cannot be empty"
        prompts = extract_code_blocks(content)
        if prompts:
            prompt = prompts[0][1].strip()  # Assume the first code block is the prompt
            assert isinstance(prompt, str)
            return prompt, True
        else:
            # No prompt found
            prompt = content
            logger.warning("No text found in triple backticks in the assistant's response. Using the entire response as the prompt.")
            return prompt, False