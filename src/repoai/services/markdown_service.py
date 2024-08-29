from pathlib import Path
from typing import Dict, Any
from ..utils.markdown_generator import MarkdownGenerator
from ..core.file_manager import FileManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownService:
    def __init__(self, project_path: Path, ignore_file: str):
        self.project_name = project_path.stem
        self.project_path = project_path
        self.file_manager = FileManager(project_path, ignore_file=ignore_file)
        logger.debug("Markdown service initialized")

    def generate_markdown_compilation(self, project_description: str, include_line_numbers: bool = False) -> str:
        logger.debug(f"Generating markdown compilation for project: {self.project_name}")
        repo_content = self.file_manager.generate_repo_content()
        return MarkdownGenerator.generate_project_compilation(project_description, repo_content, include_line_numbers)
