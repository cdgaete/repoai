# src/repoai/core/llm_expert_chat.py

import os
import re
import json
import shutil
from typing import List, Dict, Optional, Tuple
from ..config import Config
from ..LLM.llm_client import LLMManager
from ..LLM.tool_handler import ToolHandler
from ..utils.markdown_generator import MarkdownGenerator
from ..utils.git_operations import GitOperations
from ..utils.exceptions import OverloadedError, ConnectionError, FileOperationError, FileCreateError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMExpertChat:
    def __init__(self, ai_client: LLMManager, markdown_generator: MarkdownGenerator):
        self.ai_client = ai_client
        self.markdown_generator = markdown_generator
        self.git_operations = GitOperations()
        self.messages: List[Dict[str, str]] = []
        self.file_suggestions: List[Dict[str, str]] = []
        self.tool_handler = ToolHandler()

    def chat(self, user_input: str, project_name: str) -> str:
        self.ai_client.set_current_project(project_name)
        self.ai_client.set_current_phase("edition")

        project_summary = self.get_project_summary()
        
        if not self.messages:
            system_message = Config.get_prompt("EXPERT_CHAT_PROMPT")
            self.messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Current project structure:\n\n{project_summary}\n\nUser question: {user_input}"}
            ]
        else:
            self.messages.append({"role": "user", "content": user_input})

        response = self.ai_client.get_chat_response("EXPERT_CHAT", self.messages)
        
        if response:
            if 'tool_calls' in response:
                for tool_call in response['tool_calls']:
                    tool_name = tool_call['function']['name']
                    tool_args = json.loads(tool_call['function']['arguments'])
                    tool_result = self.tool_handler.execute_tool(tool_name, **tool_args)
                    self.messages.append({
                        "role": "function",
                        "name": tool_name,
                        "content": json.dumps(tool_result)
                    })
                response = self.ai_client.get_chat_response("EXPERT_CHAT", self.messages)

            self.messages.append({"role": "assistant", "content": response})
            self.file_suggestions = self._parse_file_suggestions(response)
        
        return response

    def get_project_summary(self) -> str:
        return self.markdown_generator.generate_repo_content(Config.get_current_project_path(), False)

    def _parse_file_suggestions(self, response: str) -> List[Dict[str, str]]:
        suggestions = []
        lines = response.split('\n')
        current_suggestion = None

        for line in lines:
            if line.startswith("EDIT_FILE:"):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {"operation": "edit", "file": line.split(":")[1].strip(), "content": ""}
            elif line.startswith("DELETE_FILE:"):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                suggestions.append({"operation": "delete", "file": line.split(":")[1].strip(), "content": ""})
                current_suggestion = None
            elif line.startswith("MOVE_FILE:"):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                parts = line.split(":", 2)
                if len(parts) == 3:
                    source, destination = parts[1].strip(), parts[2].strip()
                    suggestions.append({"operation": "move", "file": source, "content": destination})
                current_suggestion = None
            elif line.startswith("CREATE_FILE:"):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {"operation": "create", "file": line.split(":")[1].strip(), "content": ""}
            elif line.startswith("END_CREATE"):
                if current_suggestion:
                    if not current_suggestion["content"].strip():
                        logger.warning(f"Empty content for file: {current_suggestion['file']}")
                    suggestions.append(current_suggestion)
                    current_suggestion = None
            elif line.startswith("END_EDIT"):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                    current_suggestion = None
            elif current_suggestion:
                current_suggestion["content"] += line + "\n"

        if current_suggestion:
            suggestions.append(current_suggestion)

        for suggestion in suggestions:
            if "content" in suggestion and not isinstance(suggestion["content"], str):
                logger.error(f"Invalid content type for suggestion: {suggestion}")
                raise ValueError(f"Invalid content type for suggestion: {suggestion}")

            if "content" in suggestion:
                language, content = self.extract_main_code_block(suggestion["content"])
                if content:
                    suggestion["content"] = content
        return suggestions

    def apply_file_operations(self, selected_operations: List[str]) -> None:
        for operation in selected_operations:
            suggestion = next((s for s in self.file_suggestions if self._get_operation_key(s) == operation), None)
            if suggestion:
                if suggestion['operation'] == 'edit':
                    self.apply_file_edit(suggestion['file'], suggestion['content'])
                elif suggestion['operation'] == 'delete':
                    self.apply_file_delete(suggestion['file'])
                elif suggestion['operation'] == 'move':
                    self.apply_file_move(suggestion['file'], suggestion['content'])
                elif suggestion['operation'] == 'create':
                    logger.info(f"Attempting to create file: {suggestion['file']}")
                    logger.debug(f"File content: {suggestion['content']}")
                    if suggestion['content'] is None:
                        logger.error(f"File content is None for file: {suggestion['file']}")
                        continue  # Skip this file creation
                    self.apply_file_create(suggestion['file'], suggestion['content'])

    def apply_file_edit(self, file_path: str, new_content: str) -> None:
        full_path = Config.get_current_project_path() / file_path
        logger.info(f"Attempting to apply edit to file: {full_path}")

        try:
            read_content = open(full_path, 'r').read()
        except FileNotFoundError:
            logger.error(f"File does not exist: {full_path}")
            raise FileNotFoundError(f"The file '{file_path}' does not exist. Please check the file path and try again.")
        
        system_prompt = Config.get_prompt("EDIT_FILE_PROMPT")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current file content:\n\n```{read_content}```\n\nSuggested changes:\n\n```{new_content}```"},
        ]
        
        try:
            response = self.ai_client.get_chat_response("EDIT_FILE", messages)
        except ConnectionError as e:
            logger.error(f"Connection error while applying edit to file {full_path}: {str(e)}")
            raise ConnectionError(f"Unable to connect to the AI service. Please check your internet connection and try again.")
        except OverloadedError as e:
            logger.error(f"AI service overloaded while applying edit to file {full_path}: {str(e)}")
            raise OverloadedError(f"The AI service is currently overloaded. Please try again in a few minutes.")
        except Exception as e:
            logger.error(f"Unexpected error while applying edit to file {full_path}: {str(e)}")
            raise RuntimeError(f"An unexpected error occurred while processing your request: {str(e)}")

        if not response:
            logger.error(f"Failed to apply edit to file {full_path}")
            raise RuntimeError(f"Failed to generate new content for file '{file_path}'. Please try again.")

        language, parsed_response = self.extract_main_code_block(response)

        logger.info(f"Applying edit to file: {full_path} in {language}")

        if not parsed_response:
            parsed_response = response

        try:
            if not os.path.exists(full_path):
                logger.error(f"File does not exist: {full_path}")
                raise FileNotFoundError(f"The file '{file_path}' does not exist. Please check the file path and try again.")

            if not os.access(full_path, os.W_OK):
                logger.error(f"No write permission for file: {full_path}")
                raise PermissionError(f"You don't have permission to edit the file '{file_path}'. Please check your file permissions and try again.")

            self.git_operations.commit_specific_files([file_path], f"Commit before editing {file_path}")

            with open(full_path, 'w') as f:
                f.write(parsed_response)
            logger.info(f"Successfully applied edit to file: {full_path}")
        except Exception as e:
            logger.error(f"Failed to apply edit to file {full_path}: {str(e)}")
            raise RuntimeError(f"An error occurred while editing the file '{file_path}': {str(e)}")

    def apply_file_create(self, file_path: str, new_content: str) -> None:
        if new_content is None:
            logger.error(f"Received None content for file: {file_path}")
            return  # Early return to prevent the error

        full_path = Config.get_current_project_path() / file_path

        logger.info(f"Attempting to create file: {full_path}")
        
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"Successfully created file: {full_path}")

        except IOError as e:
            logger.error(f"IOError while creating file {full_path}: {str(e)}")
            raise FileCreateError(f"Failed to create file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while creating file {full_path}: {str(e)}")
            raise FileCreateError(f"Unexpected error while creating file {file_path}: {str(e)}")

    def apply_file_delete(self, file_path: str) -> None:
        full_path = Config.get_current_project_path() / file_path
        logger.info(f"Attempting to delete file: {full_path}")
        
        try:
            if not os.path.exists(full_path):
                logger.error(f"File does not exist: {full_path}")
                raise FileNotFoundError(f"File does not exist: {full_path}")

            if not os.access(full_path, os.W_OK):
                logger.error(f"No write permission for file: {full_path}")
                raise PermissionError(f"No write permission for file: {full_path}")

            self.git_operations.commit_specific_files([file_path], f"Commit before deleting {file_path}")

            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            elif os.path.isfile(full_path):
                os.remove(full_path)
            logger.info(f"Successfully deleted file: {full_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {full_path}: {str(e)}")
            raise

    def apply_file_move(self, source_path: str, destination_path: str) -> None:
        full_source_path = Config.get_current_project_path() / source_path
        full_destination_path = Config.get_current_project_path() / destination_path
        logger.info(f"Attempting to move file from {full_source_path} to {full_destination_path}")
        
        try:
            if not os.path.exists(full_source_path):
                logger.error(f"Source file does not exist: {full_source_path}")
                raise FileNotFoundError(f"Source file does not exist: {full_source_path}")

            if os.path.exists(full_destination_path):
                logger.error(f"Destination file already exists: {full_destination_path}")
                raise FileExistsError(f"Destination file already exists: {full_destination_path}")

            if not os.access(full_source_path, os.R_OK) or not os.access(os.path.dirname(full_destination_path), os.W_OK):
                logger.error(f"Insufficient permissions to move file from {full_source_path} to {full_destination_path}")
                raise PermissionError(f"Insufficient permissions to move file")

            self.git_operations.commit_specific_files([source_path], f"Commit before moving {source_path}")

            os.makedirs(os.path.dirname(full_destination_path), exist_ok=True)
            shutil.move(full_source_path, full_destination_path)
            logger.info(f"Successfully moved file from {full_source_path} to {full_destination_path}")
        except Exception as e:
            logger.error(f"Failed to move file from {full_source_path} to {full_destination_path}: {str(e)}")
            raise FileOperationError(f"Failed to move file: {str(e)}")

    def get_file_suggestions(self) -> List[Tuple[str, str]]:
        return [(self._get_operation_key(s), self._get_operation_description(s)) for s in self.file_suggestions]

    def _get_operation_key(self, suggestion: Dict[str, str]) -> str:
        if suggestion['operation'] == 'move':
            return f"move:{suggestion['file']}:{suggestion['content']}"
        else:
            return f"{suggestion['operation']}:{suggestion['file']}"

    def _get_operation_description(self, suggestion: Dict[str, str]) -> str:
        if suggestion['operation'] == 'move':
            return f"Move {suggestion['file']} to {suggestion['content']}"
        else:
            return f"{suggestion['operation'].capitalize()} {suggestion['file']}"
    
    def extract_main_code_block(self, content):
        pattern = r'```(\w*)\n((?:(?!```).|\n)*(?:```(?!```)(?:(?!```).|\n)*)*?\n)```'
        
        match = re.search(pattern, content, re.DOTALL)
        if match:
            language = match.group(1) or "unspecified"
            block_content = match.group(2).rstrip()
            return language, block_content
        else:
            return None, None