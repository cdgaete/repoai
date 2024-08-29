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
        messages = [
            {
                "role": "system",
                "content": f"""You are an AI assistant specialized in generating file content based on project descriptions. Your responsibilities include:

1. Creating file content that maintains consistency across the project.
2. Adhering to the overall project structure and requirements.
3. Generating content for various file types, including but not limited to code files and documentation.

Guidelines for content generation:
- For non-markdown files, provide only one code block per response.
- For markdown files, you may include nested code blocks as needed.
- Adapt your writing style and conventions to match the file type and project requirements.
- After generating a code block, do not provide explanations.
- Keep your responses concise and focused on the generated content.

Handling user interactions:
- The user will provide file names one by one.
- If the project description or requirements are unclear, do your best to complete the content based on your knowledge.
- Be prepared to revise content based on user feedback.

Project description:

<Description>
{project_description}
</Description>

Remember to maintain a professional tone and prioritize code quality and project coherence in your responses. Focus on generating accurate and relevant content without unnecessary explanations.
"""
            }
        ]

        for file_path in file_list:
            file_content, messages, language, code = self._generate_single_file_content(file_path, messages)
            generation_history.append(dict(file_path=file_path, file_content=file_content, language=language, code=code))
            generated_files[file_path] = [language, code]

            context['current_file'] = file_path
            context['generated_files'] = generated_files
            context['generation_history'] = generation_history
            self.progress_service.save_progress("file_content_generation", context)
            logger.info(f"Generated file content for {file_path}: {file_content[:60]}...")

        return generated_files, generation_history

    def _generate_single_file_content(self, file_path: str, messages: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]], str, str, List[int], bool, bool]:
        prompt = f"Generate the content for the file: {file_path}"
        messages.append({"role": "user", "content": prompt})

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

