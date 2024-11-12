from pathlib import Path
from typing import Dict, Any, Optional
from ..utils.markdown_generator import MarkdownGenerator
from ..core.file_manager import FileManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownService:
    def __init__(self, project_path: Path, ignore_file: str):
        self.project_name = project_path.stem
        self.project_path = project_path
        self.file_manager = FileManager(project_path, ignore_file=ignore_file)
        self.repo_content = {}
        logger.debug("Markdown service initialized")

    def generate_repo_content(self, files: Optional[list[str]] = None) -> None:
        """
        Generate the repo content for the project.
        """
        logger.debug(f"Generating repo content for project: {self.project_name}")
        self.repo_content = self.file_manager.generate_repo_content(files)
    
    def add_file_content(self, file_path: str, content: Dict[str, Any]):
        """
        Add file content to the repo content for the project.
        """
        logger.debug(f"Adding file content for project: {self.project_name}")
        self.repo_content[file_path] = content

    def generate_markdown_report(self, project_description: str, include_line_numbers: bool = False) -> str:
        """
        Generate the markdown report for the project.
        """
        logger.debug(f"Generating markdown report for project: {self.project_name}")
        return MarkdownGenerator.generate_project_compilation(project_description, self.repo_content, include_line_numbers)

    def generate_markdown_compilation(self, project_description: str, files: Optional[list[str]] = None, include_line_numbers: bool = False) -> str:
        """
        Generate the markdown compilation for the project.
        """
        logger.debug(f"Generating markdown compilation for project: {self.project_name}")
        self.generate_repo_content(files)
        return MarkdownGenerator.generate_project_compilation(project_description, self.repo_content, include_line_numbers)
