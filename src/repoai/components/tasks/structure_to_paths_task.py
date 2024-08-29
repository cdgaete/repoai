from typing import Dict, Any
from ...components.components_base import BaseTask
from ...services.llm_service import LLMService
from ...utils.common_utils import extract_paths
from ...utils.logger import get_logger

logger = get_logger(__name__)


class StructureToPathsTask(BaseTask):
    def __init__(self, llm_service: LLMService, model_config: Dict[str, Any]={}):
        super().__init__()
        self.llm_service = llm_service
        self.model_config = model_config

    def execute(self, context: dict) -> None:
        raw_structure = context.get('structure', '')
        if not raw_structure:
            raise ValueError("No raw structure provided in the context")
        paths = self._convert_structure_to_paths(raw_structure)
        files = []
        folders = []
        for path in paths:
            if path.endswith('/'):
                folders.append(path)
            else:
                files.append(path)
        context['file_paths'] = files
        context['folder_paths'] = folders

    def _convert_structure_to_paths(self, raw_structure: str) -> list:
        prompt = self._create_conversion_prompt(raw_structure)
        messages = [
            {"role": "system", "content": "You are an AI assistant that converts tree-like file structures into lists of root-relative file paths."},
            {"role": "user", "content": prompt}
        ]

        response = self.llm_service.get_completion(messages=messages, **self.model_config)
        paths = self._parse_llm_response(response.content)
        return paths

    def _create_conversion_prompt(self, raw_structure: str) -> str:
        return f"""
Convert the following tree-like structure into a list of root-relative file paths. The paths should start without '/'.

Here is the structure:

{raw_structure}

Please provide the list of paths, one per line, without any additional explanation or commentary.
"""

    def _parse_llm_response(self, response: str) -> list:
        paths = extract_paths(response)
        return paths
