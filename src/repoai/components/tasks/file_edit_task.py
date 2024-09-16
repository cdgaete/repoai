from typing import Dict, Any
from ...components.components_base import BaseTask
from ...services.llm_service import LLMService
from ...services.progress_service import ProgressService
from ...utils.common_utils import extract_outer_code_block
from ...utils.logger import get_logger

logger = get_logger(__name__)


class FileEditTask(BaseTask):
    def __init__(self, llm_service: LLMService, progress_service: ProgressService, model_config: Dict[str, Any] = {}):
        super().__init__()
        self.llm_service = llm_service
        self.progress_service = progress_service
        self.model_config = model_config

    def execute(self, context: Dict[str, Any]) -> None:
        file_path = context['file_path']
        current_content = context['current_content']
        edit_message = context['edit_message']
        if current_content.strip() != edit_message.strip():
            system_prompt = self.llm_service.config.get_llm_prompt(task_id='file_edit_task', prompt_type='system')
            user_prompt = self.llm_service.config.get_llm_prompt(
                task_id='file_edit_task', prompt_type='user', file_path=file_path, current_content=current_content, edit_message=edit_message)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = self.llm_service.get_completion(messages=messages, **self.model_config)
            new_content = response.content.strip()

            _, outer_content = extract_outer_code_block(new_content)
            context['new_content'] = outer_content if outer_content else new_content
        else:
            context['new_content'] = current_content

        logger.info(f"Edited content: {context['new_content'][:60]}...")

        self.progress_service.save_progress("file_edit", context)
