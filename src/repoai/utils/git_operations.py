# src/repoai/utils/git_operations.py

import subprocess
from pathlib import Path
from ..config import Config
from .config_manager import config_manager
from .logger import setup_logger

logger = setup_logger(__name__)

class GitOperations:
    def __init__(self):
        pass

    def init_repo(self, allow_empty: bool = False) -> None:
        current_project_path = Config.PROJECT_PATH
        if current_project_path is None:
            logger.error("PROJECT_PATH is not set")
            raise ValueError("PROJECT_PATH is not set")
        
        logger.info(f"Initializing git repository at {current_project_path}")
        try:
            subprocess.run(["git", "init"], cwd=current_project_path, check=True, capture_output=True, text=True)
            self.commit_changes("Initial commit", allow_empty=allow_empty)
            logger.info("Git repository initialized and initial commit created")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize git repository: {e.stderr}")
            raise

    def commit_changes(self, message: str, allow_empty: bool = False) -> None:
        current_project_path = Config.PROJECT_PATH
        if current_project_path is None:
            logger.error("PROJECT_PATH is not set")
            raise ValueError("PROJECT_PATH is not set")
        
        logger.info(f"Committing changes with message: {message}")
        try:
            subprocess.run(["git", "add", "-A"], cwd=current_project_path, check=True, capture_output=True, text=True)
            if allow_empty:
                subprocess.run(["git", "commit", "-m", message, "--allow-empty"], cwd=current_project_path, check=True, capture_output=True, text=True)
            else:
                subprocess.run(["git", "commit", "-m", message], cwd=current_project_path, check=True, capture_output=True, text=True)
            logger.info("Changes committed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes: {e.stderr}")
            raise

    def commit_specific_files(self, files: list, message: str) -> None:
        current_project_path = Config.PROJECT_PATH
        if current_project_path is None:
            logger.error("PROJECT_PATH is not set")
            raise ValueError("PROJECT_PATH is not set")
        
        logger.info(f"Committing specific files with message: {message}")
        try:
            # First, check if there are any changes to commit
            status_output = subprocess.run(["git", "status", "--porcelain"] + files, 
                                           cwd=current_project_path, 
                                           check=True, capture_output=True, text=True).stdout.strip()
            
            if not status_output:
                logger.info("No changes to commit for the specified files")
                return  # Exit the method without raising an exception
            
            # If there are changes, proceed with the commit
            for file in files:
                subprocess.run(["git", "add", file], cwd=current_project_path, check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-m", message], cwd=current_project_path, check=True, capture_output=True, text=True)
            logger.info("Specific files committed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit specific files: {e.stderr}")
            # We're not raising an exception here, as we want the operation to continue even if the commit fails