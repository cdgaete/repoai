from typing import Dict, Any
from ...components.components_base import BaseTask
from ...services.llm_service import LLMService
from ...utils.common_utils import extract_paths
from ...utils.logger import get_logger

logger = get_logger(__name__)


class StructureToPathsTask(BaseTask):
    def __init__(self, llm_service: LLMService, model_config: Dict[str, Any] = {}):
        super().__init__()
        self.llm_service = llm_service
        self.model_config = model_config

    def execute(self, context: dict) -> None:
        raw_structure = context.get('structure', '')

        if not raw_structure:
            raise ValueError("No raw structure provided in the context")

        system_prompt = self.llm_service.config.get_llm_prompt(task_id='structure_to_paths_task', prompt_type='system')
        user_prompt = self.llm_service.config.get_llm_prompt(
            task_id='structure_to_paths_task', prompt_type='user', tree_structure=raw_structure)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.llm_service.get_completion(messages=messages, **self.model_config)

        context['raw_paths'] = response.content

        paths = extract_paths(response.content)
        files = []
        folders = []
        for path in paths:
            if path.endswith('/'):
                folders.append(path)
            else:
                files.append(path)
        context['file_paths'] = files
        context['folder_paths'] = folders
