from typing import List, Dict, Tuple, Any
from repoai.components.components_base import BaseTask
from repoai.services.llm_service import LLMService
from repoai.services.progress_service import ProgressService
from repoai.utils.common_utils import extract_outer_code_block
from repoai.utils.logger import get_logger

logger = get_logger(__name__)


class FileContentGenerationTask(BaseTask):
    def __init__(self, llm_service: LLMService, progress_service: ProgressService, model_config: Dict[str, Any]={}):
        super().__init__()
        self.llm_service = llm_service
        self.progress_service = progress_service
        self.model_config = model_config

    def execute(self, context: dict) -> None:
        project_description = context['report']
        file_list = context['file_paths']

        last_state = self.progress_service.get_last_state()
        if last_state:
            generated_files = context.get('generated_files', {})
            generation_history = context.get('generation_history', [])
            last_processed_file = context.get('current_file')

            if last_processed_file in file_list:
                start_index = file_list.index(last_processed_file) + 1
            else:
                start_index = 0
            remaining_files = file_list[start_index:]
        else:
            generated_files = {}
            generation_history = []
            remaining_files = file_list

        if remaining_files:
            generated_files, generation_history = self._generate_file_contents(
                project_description, remaining_files, context, generated_files, generation_history
            )
        context['generated_files'] = generated_files
        context['generation_history'] = generation_history

    def _generate_file_contents(self, project_description: str,
                                file_list: List[str],
                                context: dict,
                                generated_files: Dict[str, Any],
                                generation_history: List[Dict[str, Any]]
                                ) -> Tuple[Dict[str, Any], List[Any], List[Dict[str, Any]]]:
        system_message = self.llm_service.config.get_llm_prompt(task_id='file_content_generation_task', prompt_type='system')
        messages = [
            {
                "role": "system",
                "content": system_message
            }
        ]

        for file_path in file_list:
            file_content, messages, language, code = self._generate_single_file_content(file_path, messages, project_description)
            generation_history.append(dict(file_path=file_path, file_content=file_content, language=language, code=code))
            generated_files[file_path] = [language, code]

            context['current_file'] = file_path
            context['generated_files'] = generated_files
            context['generation_history'] = generation_history
            self.progress_service.save_progress("file_content_generation", context)
            logger.info(f"Generated file content for {file_path}: {file_content[:60]}...")

        return generated_files, generation_history

    def _generate_single_file_content(self, file_path: str, messages: List[Dict[str, str]], project_description: str) -> Tuple[str, List[Dict[str, str]], str, str, List[int], bool, bool]:
        user_prompt = self.llm_service.config.get_llm_prompt(task_id='file_content_generation_task', prompt_type='user', file_path=file_path, project_description=project_description)
        messages.append({"role": "user", "content": user_prompt})

        response = self.llm_service.get_completion(messages=messages, **self.model_config)
        content = response.content
        messages.append({"role": "assistant", "content": content})

        if content:
            language, code = extract_outer_code_block(content)
            if not code:
                code = content
            if not language:
                language = "markdown"

        return content, messages, language, code