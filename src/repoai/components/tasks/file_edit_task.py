from typing import Dict, Any
from ...components.components_base import BaseTask
from ...services.llm_service import LLMService
from ...services.progress_service import ProgressService
from ...utils.common_utils import extract_outer_code_block
from ...utils.logger import get_logger

logger = get_logger(__name__)


class FileEditTask(BaseTask):
    def __init__(self, llm_service: LLMService, progress_service: ProgressService, model_config: Dict[str, Any]={}):
        super().__init__()
        self.llm_service = llm_service
        self.progress_service = progress_service
        self.model_config = model_config

    def execute(self, context: Dict[str, Any]) -> None:
        self._process_edit(context)

    def _process_edit(self, context: Dict[str, Any]):
        file_path = context['file_path']
        current_content = context['current_content']
        edit_message = context['edit_message']
        if current_content.strip() != edit_message.strip():
            prompt = self._create_edit_prompt(file_path, current_content, edit_message)
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with editing file contents based on user requests."},
                {"role": "user", "content": prompt}
            ]

            response = self.llm_service.get_completion(messages=messages, **self.model_config)
            new_content = response.content.strip()

            _, outer_content = extract_outer_code_block(new_content)
            context['new_content'] = outer_content if outer_content else new_content
        else:
            context['new_content'] = current_content

        logger.info(f"Edited content: {context['new_content'][:60]}...")

        # Save progress after the edit
        self.progress_service.save_progress("file_edit", context)

    def _create_edit_prompt(self, file_path: str, current_content: str, edit_message: str) -> str:
        return f"""
You are tasked with editing the following file: {file_path}

Current content of the file:
```
{current_content}
```

Edit request: 
```
{edit_message}
```

Please provide the full updated content of the file that reflects the requested changes.
Your response should only contain the updated file content, without any additional explanations or formatting.
Provide the updated file content in triple backticks. Ensure the resulting file content is valid and remove comments if necessary.
"""