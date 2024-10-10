import re
from typing import Dict, Any, List
from ...components.components_base import BaseTask
from ...services.llm_service import LLMService
from ...services.progress_service import ProgressService
from ...utils.common_utils import extract_outer_code_block, extract_code_blocks
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ProjectModificationTask(BaseTask):
    def __init__(self, llm_service: LLMService, progress_service: ProgressService, model_config: Dict[str, Any]={}):
        super().__init__()
        self.llm_service = llm_service
        self.progress_service = progress_service
        self.model_config = model_config

    def execute(self, context: Dict[str, Any]) -> None:
        self._process_chat(context)

    def _process_chat(self, context: Dict[str, Any]):
        messages = context.get('messages', [])
        user_input = context.get('user_input', '')
        file_contexts = context.get('file_contexts', [])
        image_contexts = context.get('image_contexts', [])

        if not messages:
            system_message = self.llm_service.config.get_llm_prompt(task_id='project_modification_task', prompt_type='system')
            messages = [{"role": "system", "content": system_message}]
            project_report = context.get('project_report', '')
            text_message = f"\nContext:\n\n{project_report}\n\nRequest:\n\n{user_input}\n\n"
            if file_contexts:
                text_message += "Additional information for context:\n"
                for file_context in file_contexts:
                    text_message += f"File: {file_context['file_path']}\nContent:\n```\n{file_context['content']}\n```\n\n"
            user_message_content = [{"type": "text", "text": text_message}]
            if image_contexts:
                for image_context in image_contexts:
                    user_message_content.append({"type": "image_url", "image_url": image_context['image_url']})
            messages.append({"role": "user", "content": user_message_content})
        else:
            text_message = f"{user_input}\n\n"
            if file_contexts:
                text_message += "Additional information for context:\n"
                for file_context in file_contexts:
                    text_message += f"File: {file_context['file_path']}\nContent:\n```\n{file_context['content']}\n```\n\n"
            user_message_content = [{"type": "text", "text": text_message}]
            if image_contexts:
                for image_context in image_contexts:
                    user_message_content.append({"type": "image_url", "image_url": image_context['image_url']})
            messages.append({"role": "user", "content": user_message_content})

        response = self.llm_service.get_completion(messages=messages, **self.model_config)
        assistant_message = {"role": "assistant", "content": response.content}
        messages.append(assistant_message)

        context['messages'] = messages
        context['user_input'] = ""
        context['file_contexts'] = []
        context['image_contexts'] = []

        context['modifications'] = self._extract_modifications(response.content)

        self.progress_service.save_progress("project_modification", context)

    def _extract_modifications(self, content: str) -> List[Dict[str, Any]]:
        modifications = []
        lines = content.split('\n')
        current_modification = None
        content_lines = []

        operation_pattern = r'^<::(CREATE|EDIT|DELETE|MOVE)::>\s+(.+)$'

        for line in lines:
            stripped_line = line.strip()
            
            if current_modification is None:
                match = re.match(operation_pattern, stripped_line)
                if match:
                    if content_lines and modifications:
                        self._finalize_modification(modifications[-1], '\n'.join(content_lines))
                        content_lines = []
                    
                    operation, file_path = match.groups()
                    current_modification = {'operation': operation.lower(), 'file_path': file_path}

                    if operation == 'MOVE':
                        move_parts = file_path.split(' TO ')
                        if len(move_parts) == 2:
                            current_modification['file_path'] = move_parts[0]
                            current_modification['new_path'] = move_parts[1]
                        else:
                            raise Exception(f"Invalid MOVE operation format: {line}")
                    
                    modifications.append(current_modification)
                    
                    if operation in ['DELETE', 'MOVE']:
                        current_modification = None
                else:
                    content_lines.append(line)
            else:
                match = re.match(operation_pattern, stripped_line)
                if match:
                    self._finalize_modification(current_modification, '\n'.join(content_lines))
                    content_lines = []
                    current_modification = None
                    
                    operation, file_path = match.groups()
                    current_modification = {'operation': operation.lower(), 'file_path': file_path}

                    if operation == 'MOVE':
                        move_parts = file_path.split(' TO ')
                        if len(move_parts) == 2:
                            current_modification['file_path'] = move_parts[0]
                            current_modification['new_path'] = move_parts[1]
                        else:
                            raise Exception(f"Invalid MOVE operation format: {line}")
                    
                    modifications.append(current_modification)
                    
                    if operation in ['DELETE', 'MOVE']:
                        current_modification = None
                else:
                    content_lines.append(line)

        if current_modification and content_lines:
            self._finalize_modification(current_modification, '\n'.join(content_lines))

        return modifications

    def _finalize_modification(self, modification: Dict[str, Any], content: str):
        if modification['operation'] in ['create', 'edit']:
            blocks = extract_code_blocks(content)
            if len(blocks) > 1:
                if "markdown" == blocks[0][0].lower():
                    capture_first_block = False
                else:
                    capture_first_block = True
            elif len(blocks) == 1:
                capture_first_block = False
            else:
                capture_first_block = False

            if capture_first_block:
                modification['language'] = blocks[0][0].lower()
                modification['content'] = blocks[0][1].strip()
            else:
                lang, extracted_content = extract_outer_code_block(content)
                if extracted_content:
                    modification['content'] = extracted_content.strip()
                else:
                    modification['content'] = content.strip()
                if lang:
                    modification['language'] = lang
                else:
                    modification['language'] = 'unknown'
                    
        elif modification['operation'] == 'delete':
            pass
        elif modification['operation'] == 'move':
            if 'new_path' not in modification:
                raise Exception(f"New path missing for move operation: {modification}")

    def _validate_modifications(self, modifications: List[Dict[str, Any]]):
        valid_operations = {'create', 'edit', 'delete', 'move'}
        for mod in modifications:
            if 'operation' not in mod or 'file_path' not in mod:
                raise Exception(f"Invalid modification structure: {mod}")
            if mod['operation'] not in valid_operations:
                raise Exception(f"Invalid operation: {mod['operation']}")
            if mod['operation'] in {'create', 'edit'} and 'content' not in mod:
                raise Exception(f"Content missing for {mod['operation']} operation: {mod}")
            if mod['operation'] == 'move' and 'new_path' not in mod:
                raise Exception(f"New path missing for move operation: {mod}")