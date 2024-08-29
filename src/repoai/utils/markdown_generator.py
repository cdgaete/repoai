from typing import Dict, Any, List
from .treenode import FileSystemTree
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownGenerator:
    @staticmethod
    def generate_project_compilation(project_description: str, repo_content: Dict[str, Any], include_line_numbers: bool = False) -> str:
        markdown = "# Project Compilation\n\n"
        markdown += f"{project_description}\n\n"
        markdown += "## Project Structure\n\n"
        markdown += MarkdownGenerator._generate_tree_structure(repo_content)
        markdown += "\n## Repository Contents\n\n"
        markdown += MarkdownGenerator._generate_file_contents(repo_content, include_line_numbers)
        return markdown

    @staticmethod
    def _generate_tree_structure(repo_content: Dict[str, Any]) -> str:
        filtered_files = repo_content.get('files', []) + repo_content.get('directories', [])
        tree = FileSystemTree.generate(filtered_files)
        tree_lines = FileSystemTree.display(tree)
        
        return "```\n" + "\n".join(tree_lines) + "\n```\n"

    @staticmethod
    def _generate_file_contents(repo_content: Dict[str, Any], include_line_numbers: bool) -> str:
        markdown = ""
        for file_path, content in repo_content.get('content', {}).items():
            markdown += f"### {file_path}\n\n"
            markdown += "```\n"
            if include_line_numbers:
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    markdown += f"{i:4d} | {line}\n"
            else:
                markdown += f"{content}\n"
            markdown += "```\n\n"
        return markdown