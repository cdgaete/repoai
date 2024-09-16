import re
from typing import Dict, Any
from ...components.components_base import BaseTask
from ...services.llm_service import LLMService
from ...services.progress_service import ProgressService
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ProjectStructureChatTask(BaseTask):
    def __init__(self, llm_service: LLMService, progress_service: ProgressService, model_config: Dict[str, Any]={}):
        super().__init__()
        self.llm_service = llm_service
        self.progress_service = progress_service
        self.model_config = model_config

    def execute(self, context: dict) -> None:
        self._process_chat(context)

    def _process_chat(self, context: dict):
        messages = context.get('messages', [])
        if not messages:
            system_message = self.llm_service.config.get_prompt('project_structure_chat_task')
            messages = [{"role": "system", "content": system_message}]
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
        assistant_message = {"role": "assistant", "content": response.content}
        messages.append(assistant_message)

        context['messages'] = messages
        context['user_input'] = ""
        context['structure_and_explanation'] = response.content
        context['structure'] = self._extract_structure(response.content)

        self.progress_service.save_progress("project_structure", context)

    def _extract_structure(self, content):
        code_blocks = re.findall(r'```(?:[\w]*\n)?(.*?)```', content, re.DOTALL)
        if code_blocks:
            for block in code_blocks:
                if '/' in block and ('\n' in block or '│' in block):
                    return block.strip()
        lines = content.split('\n')
        structure_lines = []
        for line in lines:
            if ('/' in line or '│' in line or '├' in line or '└' in line) and not line.startswith('```'):
                structure_lines.append(line)
            elif structure_lines and line.strip() == '':
                break
        if structure_lines:
            return '\n'.join(structure_lines).strip()
        return ""