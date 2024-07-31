# src/repoai/core/project_creator.py

import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from ..config import Config
from ..LLM.llm_client import LLMManager
from ..utils.git_operations import GitOperations
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class ProjectCreator:
    def __init__(self, ai_client: LLMManager):
        self.ai_client = ai_client
        self.git_operations = GitOperations()
        self.current_prompt = ""

    def create_empty_project(self, project_name: str) -> Path:
        logger.info(f"Creating empty project: {project_name}")
        
        project_path = self._get_project_path(project_name)
        
        try:
            self._create_project_directory(project_path)
            
            # Set the CURRENT_PROJECT_PATH in Config
            Config.set_current_project(project_name)
            
            self._create_gitignore(project_path)
            self._create_repoaiignore(project_path)
            self._create_env_file(project_path)
            self._initialize_git_repo()

            logger.info(f"Empty project creation completed successfully at: {project_path}")
            return project_path
        except Exception as e:
            logger.exception(f"Error during empty project creation: {str(e)}")
            self._cleanup_failed_project(project_path)
            raise

    def create_project_from_description(self, project_name: str, project_description: str) -> Path:
        logger.info(f"Creating project from description: {project_name}")
        
        project_path = self._get_project_path(project_name)
        
        try:
            # Create project directory and initialize git repo with empty commit
            self._create_project_directory(project_path)
            Config.set_current_project(project_name)
            self._initialize_git_repo()

            self.ai_client.set_current_project(project_name)
            self.ai_client.set_current_phase("creation")

            project_summary = self._generate_complete_project_summary(project_description)
            directory_structure = self._format_directory_structure(project_summary)
            root_dir_name, files = self._create_project_structure(project_path, directory_structure)

            self._validate_project_structure(directory_structure)
            content_dict = self._extract_project_content(root_dir_name, project_path, files, project_summary)
            self._create_project_files(content_dict)

            self._create_gitignore(project_path)
            self._create_repoaiignore(project_path)
            self._create_env_file(project_path)

            logger.info(f"Project creation completed successfully at: {project_path}")
            return project_path
        except Exception as e:
            logger.exception(f"Error during project creation: {str(e)}")
            raise

    def _generate_complete_project_summary(self, project_description: str) -> str:
        logger.info("Generating complete project summary using AI")
        system_prompt = Config.get_prompt("PROJECT_CREATOR_PROMPT")
        wrapped_system_prompt = f"{system_prompt}\nWrap your entire response with <creation_repoai> and </creation_repoai> tags."
        user_prompt = f"Project Description: {project_description}"

        messages = [{"role": "system", "content": wrapped_system_prompt},{"role": "user", "content": user_prompt}]
        preliminary_summary = []
        max_attempts = 6  # Prevent infinite loops

        response = self.ai_client.get_chat_response("PROJECT_CREATOR", messages)["text"]

        if not response:
            logger.error("Failed to generate project summary using AI")
            raise ValueError("Failed to generate project summary using AI, output is an empty string.")
        
        is_complete, cut_index = self._is_summary_complete(response)

        if is_complete:
            logger.info("Complete project summary generated successfully")
            response = response[:cut_index]
            return self._extract_content_from_tags(response)
        
        preliminary_summary.append(response)
        messages.append({"role": "assistant", "content": response})
        user_prompt = "Please continue generating the project summary just from where you left off."
        done = False
        for attempt in range(max_attempts):
            logger.debug(f"Attempt {attempt + 1} to generate complete project summary")
            messages.append({"role": "user", "content": user_prompt})
            
            response = self.ai_client.get_chat_response("PROJECT_CREATOR", messages)["text"]

            if not response:
                logger.error("Failed to generate project summary using AI")
                raise ValueError("Failed to generate project summary using AI, output is an empty string.")
            
            is_complete, cut_index = self._is_summary_complete(response)

            if is_complete:
                logger.info("Complete project summary generated successfully")
                response = response[:cut_index]
                preliminary_summary.append(response)
                done = True
                break

            preliminary_summary.append(response)
            messages.append({"role": "assistant", "content": response})

        raw_summary = "".join(preliminary_summary)

        if not done:
            logger.warning(f"Failed to generate complete project summary after {max_attempts} attempts")
            project_path = Config.get_current_project_path()
            with open(project_path / "project_summary.txt", "w") as f:
                f.write(raw_summary)
            raise ValueError("Failed to generate complete project summary")

        return self._extract_content_from_tags(raw_summary)

    def _extract_content_from_tags(self, response: str) -> str:
        pattern = r'<creation_repoai>(.*?)</creation_repoai>'
        matches = re.findall(pattern, response, re.DOTALL)
        return '\n'.join(matches)

    def _is_summary_complete(self, response: str) -> Tuple[bool, Optional[int]]:
        is_complete = response.strip().endswith('</creation_repoai>')
        if not is_complete:
            if '</creation_repoai>' in response:
                rhs = response.rsplit('</creation_repoai>', 1)[0]
                cut_index = len(rhs) + len('</creation_repoai>')
                return True, cut_index
            else:
                return False, None
        else:
            return True, len(response)

    def _get_project_path(self, project_name: str) -> Path:
        if Config.PROJECT_ROOT_PATH is None:
            raise ValueError("Project root path is not set")
        return Config.PROJECT_ROOT_PATH / project_name

    def _create_project_directory(self, project_path: Path):
        try:
            project_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise ValueError(f"Project directory already exists: {project_path}")

    def _cleanup_failed_project(self, project_path: Path):
        if project_path.exists():
            shutil.rmtree(project_path)
        logger.info(f"Cleaned up failed project at: {project_path}")

    def _validate_project_structure(self, directory_structure: str):
        if not self._validate_directory_structure(directory_structure):
            raise ValueError("Invalid directory structure generated")

    def _create_project_structure(self, project_path: Path, directory_structure: str):
        tree_pattern = r'<Tree>\n([\s\S]*?)\n</Tree>'
        tree_match = re.search(tree_pattern, directory_structure)
        if not tree_match:
            raise ValueError("Invalid tree string format")
        
        tree_content = tree_match.group(1).split('\n')
        root_dir_name = tree_content[0].rstrip('/')
        files = []
        for line in tree_content[1:]:
            path = line.strip().lstrip(root_dir_name).lstrip('/')
            if path.endswith('/'):
                full_path = project_path / path
                full_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {full_path}")
            else:
                # save file path only
                files.append(path)

        return root_dir_name, files
    
    def _extract_project_content(self, root_dir: str, project_path: Path, files: List[str], project_summary: str) -> Dict[str, str]:
        content_dict = {}
        batch_size = 3  # Process 5 files at a time, adjust as needed

        for i in range(0, len(files), batch_size):
            batch = files[i:i+batch_size]
            batch_content = self._format_file_contents(project_summary, batch)
            
            for file_path, content in self._parse_file_contents(batch_content):
                if file_path.startswith(root_dir):
                    file_path = file_path[len(root_dir):].lstrip('/')
                full_path = project_path / file_path
                content_dict[str(full_path)] = content

        return content_dict
    
    def _create_project_files(self, file_content_dict: Dict[str, str]):
        for file_path, content in file_content_dict.items():
            full_path = Path(file_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            logger.info(f"Created file with content: {full_path}")

    def _initialize_git_repo(self):
        try:
            self.git_operations.init_repo(True)
        except Exception as e:
            logger.error(f"Failed to initialize Git repository: {str(e)}")
            raise

    def _create_gitignore(self, project_path: Path):
        self._create_file(project_path / ".gitignore", Config.GITIGNORE_TEMPLATE)

    def _create_repoaiignore(self, project_path: Path):
        self._create_file(project_path / ".repoaiignore", Config.REPOAIIGNORE_TEMPLATE)

    def _create_env_file(self, project_path: Path):
        self._create_file(project_path / ".env", Config.ENV_TEMPLATE)

    def _create_file(self, file_path: Path, content: str):
        try:
            with open(file_path, "w") as f:
                f.write(content.strip())
            logger.info(f"Created file: {file_path}")
        except IOError as e:
            logger.error(f"Failed to create file {file_path}: {str(e)}")
            raise

    def chat_about_project(self, user_input: str, messages: List[Dict[str, Any]] = []) -> Tuple[str, List[Dict[str, Any]]]:
        logger.info("Chatting about project description")
        system_prompt = Config.get_prompt("PROJECT_DESCRIPTION_CHAT_PROMPT")
        if not messages:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        else:
            messages.append({"role": "user", "content": user_input})
        
        response = self.ai_client.get_chat_response("PROJECT_DESCRIPTION_CHAT", messages)["text"]
        
        if response:
            messages.append({"role": "assistant", "content": response})
            self._update_current_prompt(response)
        
        return response, messages
    
    def _update_current_prompt(self, ai_response: str):
        prompt_match = re.search(r'Current Project Description Prompt:\n(.+?)(?:\n\n|$)', ai_response, re.DOTALL)
        if prompt_match:
            self.current_prompt = prompt_match.group(1).strip()
            logger.info(f"Updated current prompt: {self.current_prompt}")
        else:
            logger.warning("Couldn't extract updated prompt from AI response")

    def get_current_prompt(self) -> str:
        return self.current_prompt
    
    def _format_directory_structure(self, project_summary: str) -> str:
        system_prompt = Config.get_prompt("FORMAT_DIRECTORY_STRUCTURE_PROMPT")
        messages = [{"role": "user", "content": f"Format the following project summary into a directory structure:\n\n{project_summary}"}]
        response = self.ai_client.get_response("FORMAT_DIRECTORY_STRUCTURE", system_prompt, messages)
        if not response:
            raise ValueError("Failed to generate directory structure")
        return response

    def _format_file_contents(self, project_summary: str, files: List[str]) -> str:
        logger.info(f"Formatting file contents for {len(files)} files")
        system_prompt = Config.get_prompt("FORMAT_FILE_CONTENTS_PROMPT")
        files_list = "\n".join(files)
        user_prompt = f"Extract and format file contents for the following files from the project summary:\n\n{files_list}\n\nProject Summary:\n{project_summary}"

        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}]
        
        response = self.ai_client.get_chat_response("FORMAT_FILE_CONTENTS", messages)["text"]
        
        if not response:
            logger.error("AI client returned empty response for file contents")
            raise ValueError("Failed to generate file contents")
        
        logger.debug(f"Raw AI response for file contents:\n{response}")
        return response

    def _parse_file_contents(self, file_contents: str) -> List[Tuple[str, str]]:
        file_pattern = r'<FileBlock>\n```.*?\n# (.+?)\n([\s\S]*?)\n```\n</FileBlock>'
        return re.findall(file_pattern, file_contents, re.DOTALL)

    def _validate_directory_structure(self, directory_structure: str) -> bool:
        pattern = r'<Tree>\n([\s\S]*?)\n</Tree>'
        match = re.search(pattern, directory_structure)
        if not match:
            logger.error(f"Invalid directory structure: {directory_structure}")
        return bool(match)
    