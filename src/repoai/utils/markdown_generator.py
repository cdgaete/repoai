# src/repoai/utils/markdown_generator.py

import streamlit as st
import fnmatch
import mimetypes
import os
from pathlib import Path
from typing import List
from .treenode import FileSystemTree
from ..config import Config
from .config_manager import config_manager
from .text_file import is_text_file

class MarkdownGenerator:
    @staticmethod
    @st.cache_data(ttl=0)
    def generate_repo_content(project_path: Path, include_line_numbers: bool = True, ignore_patterns: List[str] = None):
        if not project_path:
            return "# No project selected\n\nPlease create or select a project to view its contents."
        
        if ignore_patterns is None:
            ignore_patterns = MarkdownGenerator._read_ignore_file(project_path)
        
        files = MarkdownGenerator._get_files(project_path, ignore_patterns)
        
        content = "# Repository Contents\n\n"
        content += "# Tree-like Structure\n\n"
        content += MarkdownGenerator._generate_folder_tree(project_path, ignore_patterns)
        content += "\n\n"
        content += MarkdownGenerator._generate_file_contents(project_path, files, include_line_numbers)
        return content
    
    @staticmethod
    @st.cache_data(ttl=0)
    def generate_repo_container(project_path: Path, include_line_numbers: bool = False, ignore_patterns: List[str] = None):
        if not project_path:
            return {}
        container = {}
        if ignore_patterns is None:
            ignore_patterns = MarkdownGenerator._read_ignore_file(project_path)
        files = MarkdownGenerator._get_files(project_path, ignore_patterns)
        tree = MarkdownGenerator._generate_folder_tree(project_path, ignore_patterns)
        container["__tree__"] = {"content":tree, "language": "markdown"}

        for file_path in files:
            full_path = project_path / file_path
            if full_path.is_file():  # Ensure it's a file before processing
                mime_type, _ = mimetypes.guess_type(str(full_path))
                if MarkdownGenerator._is_text_type(mime_type, full_path):
                    content = MarkdownGenerator._read_file_content(full_path, include_line_numbers)
                    container[str(file_path)] = {"content":content, "language": MarkdownGenerator._get_language_identifier(file_path)}
                else:
                    content = f"\n\n# Content not displayed: {mime_type or 'Unknown'} file\n\n"
                    container[str(file_path)] = {"content":content, "language": "python"}
        return container
                    
    @staticmethod
    def _is_text_type(mime_type: str, full_path: Path):
        return (mime_type and mime_type.startswith('text/')) or (mime_type in ['application/json', 'application/xml', 'image/svg+xml']) or is_text_file(full_path)

    @staticmethod
    def _read_ignore_file(project_path: Path):
        ignore_file = Config.get_ignore_file_path(project_path)
        if not ignore_file.exists():
            return config_manager.get('DEFAULT_IGNORE_PATTERNS', [])
        with open(ignore_file, "r") as f:
            patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        return patterns

    @staticmethod
    def _get_files(project_path: Path, ignore_patterns: list):
        all_files = []
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not MarkdownGenerator._should_ignore(Path(root) / d, project_path, ignore_patterns)]
            for file in files:
                file_path = Path(root) / file
                if not MarkdownGenerator._should_ignore(file_path, project_path, ignore_patterns):
                    all_files.append(file_path.relative_to(project_path))
        return all_files

    @staticmethod
    def _generate_folder_tree(project_path: Path, ignore_patterns: list):
        tree = "```\n /\n"

        def custom_criteria(path):
            return not MarkdownGenerator._should_ignore(path, project_path, ignore_patterns)

        file_system_tree = FileSystemTree.generate(
            project_path,
            criteria=custom_criteria,
            ignore_file=project_path / '.repoai' / config_manager.get('IGNORE_FILE', '.repoaiignore')
        )

        for node in file_system_tree:
            if node.path != project_path:  # Skip the root node
                tree += FileSystemTree.display(node) + "\n"

        tree += "```\n"
        return tree

    @staticmethod
    def _generate_file_contents(project_path: Path, files: list, include_line_numbers: bool):
        content = "## File Contents\n\n"
        for file_path in files:
            full_path = project_path / file_path
            if full_path.is_file():  # Ensure it's a file before processing
                content += f"### File: {file_path}\n"
                mime_type, _ = mimetypes.guess_type(str(full_path))
                if MarkdownGenerator._is_text_type(mime_type, full_path):
                    content += "```" + MarkdownGenerator._get_language_identifier(file_path) + "\n"
                    content += MarkdownGenerator._read_file_content(full_path, include_line_numbers)
                    content += "\n```\n\n"
                else:
                    content += f"```\n\n# Content not displayed: {mime_type or 'Unknown'} file\n\n```\n\n"

        return content

    @staticmethod
    @st.cache_data(ttl=0)
    def _read_file_content(file_path: Path, include_line_numbers: bool):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if include_line_numbers:
                return "".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
            else:
                return "".join(lines)
        except Exception as e:
            return f"Error reading file: {str(e)}\n"

    @staticmethod
    def _get_language_identifier(file_path: Path):
        extension = file_path.suffix.lower()
        return config_manager.get('FILE_EXTENSION_TO_LANGUAGE', {}).get(extension, "")

    @staticmethod
    def _should_ignore(path: Path, project_path: Path, ignore_patterns: list):
        relative_path = path.relative_to(project_path)
        return any(MarkdownGenerator._match_pattern(relative_path, pattern) for pattern in ignore_patterns)

    @staticmethod
    def _match_pattern(path: Path, pattern: str):
        if pattern.endswith('/'):
            return fnmatch.fnmatch(str(path) + '/', pattern) or \
                   any(fnmatch.fnmatch(str(parent) + '/', pattern) for parent in path.parents)
        return fnmatch.fnmatch(str(path), pattern)