import os
import json
import yaml
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..utils.ignore_patterns import IgnorePatternHandler
from ..utils.common_utils import is_text_file, yaml_multiline_string_presenter
from ..utils.logger import get_logger

logger = get_logger(__name__)

yaml.add_representer(str, yaml_multiline_string_presenter)
yaml.representer.SafeRepresenter.add_representer(str, yaml_multiline_string_presenter)

class FileManager:
    def __init__(self, project_path: Path, ignore_file: str):
        """
        Args:
            project_path (str): Absolute path to the project directory
            ignore_file (str): Relative path to the ignore file (.repoai/.repoaiignore by default)
        """
        self.project_path = project_path
        self.ignore_patterns = IgnorePatternHandler(self.project_path / ignore_file)
        logger.debug("File manager initialized")

    def create_file(self, file_path: str, content: str):
        if self.file_exists(file_path):
            logger.warn(f"File {file_path} already exists. Use edit_file to modify existing files. No operation was performed.")
        else:
            self.save_file(file_path, content)
            self.ignore_patterns.reload_patterns()

    def edit_file(self, file_path: str, content: str):
        if not self.file_exists(file_path):
            logger.warn(f"File {file_path} does not exist. Use create_file to create new files. No operation was performed.")
        else:
            self.save_file(file_path, content)
            self.ignore_patterns.reload_patterns()

    def save_file(self, file_path: str, content: str):
        full_path = self.project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.ignore_patterns.reload_patterns()
        logger.debug(f"File {file_path} created successfully.")

    def save_json(self, file_path: str, content: Dict[str, Any]):
        full_path = self.project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2)
        self.ignore_patterns.reload_patterns()
        logger.debug(f"File {file_path} created successfully.")

    def save_yaml(self, file_path: str, content: Dict[str, Any]):
        full_path = self.project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
        self.ignore_patterns.reload_patterns()
        logger.debug(f"File {file_path} created successfully.")

    def read_file(self, file_path: str) -> Optional[str]:
        full_path = self.project_path / file_path
        if full_path.exists():
            if not is_text_file(str(full_path)):
                logger.warning(f"File {file_path} is not a text file and cannot be displayed.")
                return "This file is not a text file and cannot be displayed."
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        logger.warning(f"File {file_path} not found or couldn't be read.")
        return "File not found or couldn't be read."

    def read_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        full_path = self.project_path / file_path
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        logger.warning(f"File {file_path} not found or couldn't be read.")
        return "File not found or couldn't be read."

    def read_yaml(self, file_path: str) -> Optional[Dict[str, Any]]:
        full_path = self.project_path / file_path
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        logger.warning(f"File {file_path} not found or couldn't be read.")
        return "File not found or couldn't be read."

    def delete_file(self, file_path: str):
        full_path = self.project_path / file_path
        if full_path.exists():
            os.remove(full_path)

    def move_file(self, source_path: str, destination_path: str):
        full_source_path = self.project_path / source_path
        full_destination_path = self.project_path / destination_path
        full_destination_path.parent.mkdir(parents=True, exist_ok=True)
        os.rename(str(full_source_path), str(full_destination_path))

    def list_files_not_ignored(self) -> List[str]:
        all_files = [str(f.relative_to(self.project_path)) for f in self.project_path.rglob('*') if f.is_file()]
        return [f for f in all_files if not self.ignore_patterns.is_ignored(f)]

    def list_directories_not_ignored(self) -> List[str]:
        all_dirs = [str(d.relative_to(self.project_path)) for d in self.project_path.rglob('*') if d.is_dir()]
        return [d for d in all_dirs if not self.ignore_patterns.is_ignored(d)]

    def get_files_in_directory(self, directory_path: str) -> List[str]:
        full_dir_path = self.project_path / directory_path
        return [str(f.relative_to(self.project_path)) for f in full_dir_path.rglob('*') if f.is_file()]

    def file_exists(self, file_path: str) -> bool:
        return (self.project_path / file_path).exists()

    def create_project_directory(self):
        self.project_path.mkdir(parents=True, exist_ok=True)

    def create_directory(self, directory_path: str):
        (self.project_path / directory_path).mkdir(parents=True, exist_ok=True)

    def delete_directory(self, directory_path: str):
        full_path = self.project_path / directory_path
        if full_path.exists():
            shutil.rmtree(full_path)

    def list_directories(self) -> List[str]:
        return [str(d.relative_to(self.project_path)) for d in self.project_path.rglob('*') if d.is_dir()]

    def directory_exists(self, directory_path: str) -> bool:
        return (self.project_path / directory_path).is_dir()

    def generate_repo_content(self) -> Dict[str, Any]:
        files = self.list_files_not_ignored()
        directories = self.list_directories_not_ignored()

        repo_content = {
            "files": files,
            "directories": directories,
            "content": {},
        }

        for file_path in files:
            repo_content["content"][file_path] = self.read_file(file_path)

        return repo_content

    def add_ignore_pattern(self, pattern: str):
        self.ignore_patterns.add_pattern(pattern)

    def remove_ignore_pattern(self, pattern: str):
        self.ignore_patterns.remove_pattern(pattern)

    def get_ignore_patterns(self) -> List[str]:
        return self.ignore_patterns.get_patterns()