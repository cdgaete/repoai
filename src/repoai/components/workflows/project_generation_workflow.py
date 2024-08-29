from typing import List, Dict, Any
from pathlib import Path
from ...components.components_base import BaseWorkflow
from ...core.project_manager import ProjectManager
from ...services.llm_service import LLMService
from ...services.progress_service import ProgressService
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ProjectGenerationWorkflow(BaseWorkflow):
    def __init__(self, project_manager: ProjectManager, progress_service: ProgressService, model_config: Dict[str, Any] = None):
        super().__init__()
        self.project_manager = project_manager
        self.progress_service = progress_service
        self.llm_service = LLMService(project_manager.project_path, project_manager.config)
        
        self.model_config = model_config or {}
        
        self.description_task = self.project_manager.get_task("project_description_chat_task")(
            self.llm_service, 
            self.progress_service,
            self.model_config.get("project_description_chat_task", {})
        )
        self.structure_task = self.project_manager.get_task("project_structure_chat_task")(
            self.llm_service, 
            self.progress_service,
            self.model_config.get("project_structure_chat_task", {})
        )
        self.paths_task = self.project_manager.get_task("structure_to_paths_task")(
            self.llm_service,
            self.model_config.get("structure_to_paths_task", {})
        )
        self.content_generation_task = self.project_manager.get_task("file_content_generation_task")(
            self.llm_service, 
            self.progress_service,
            self.model_config.get("file_content_generation_task", {})
        )

    def description_start(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = self.reset_chat_context(context)
        context['user_input'] = user_input
        return self.execute_description_task(context)
    
    def execute_description_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.description_task.execute(context)
        self.progress_service.save_progress("project_description", context)
        return context

    def execute_structure_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.structure_task.execute(context)
        self.progress_service.save_progress("project_structure", context)
        return context

    def finalize_project(self, context: Dict[str, Any]) -> Dict[str, Any]:
        project_prompt = context["description"]
        structure_and_explanation = context["structure_and_explanation"]
        context['report'] = context.get('report', f"{project_prompt}\n\n{structure_and_explanation}")
        
        if 'file_paths' not in context:
            self.paths_task.execute(context)
            self.progress_service.save_progress("paths_generation", context)
        
        self.content_generation_task.execute(context)
        self.progress_service.save_progress("file_content_generation", context)
        self._create_project_files(context['generated_files'])
        self._save_generation_history(context['generation_history'])
        self._save_report(context['report'])
        self.progress_service.clear_progress()
        return context


    def _create_project_files(self, generated_files: Dict[str, str], directories: List[str] = []):
        batch_operations = []
        for file_path, (language, code) in generated_files.items():
            batch_operations.append({'operation': 'create_file', 'file_path': file_path, 'content': code})
        for folder in directories:
            batch_operations.append({'operation': 'create_directory', 'file_path': folder})
        self.project_manager.batch_operations(batch_operations)

    def _save_generation_history(self, generation_history: List[Dict[str, Any]]):
        self.project_manager.file_manager.save_yaml(str(Path(self.project_manager.config.REPOAI_DIR) / "generation_history.yml"), generation_history)

    def _save_report(self, report: str):
        self.project_manager.file_manager.save_file(str(Path(self.project_manager.config.REPOAI_DIR) / "report.md"), report)

    @staticmethod
    def reset_chat_context(context: dict = None):
        if not context:
            return {
                "messages": [],
                "user_input": "",
            }
        else:
            context["messages"] = []
            context["user_input"] = ""
            return context