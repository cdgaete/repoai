from git import Repo, InvalidGitRepositoryError
from pathlib import Path
from typing import List, Dict, Tuple
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GitService:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.repo = self._initialize_repo()
        self.pending_to_stage: List[Tuple[str, str]] = []  # List of (file_path, operation)
        logger.debug("Git service initialized")

    def _initialize_repo(self) -> Repo:
        try:
            return Repo(self.project_path)
        except InvalidGitRepositoryError:
            logger.debug("Project directory is not a valid Git repository. Initializing...")
            return Repo.init(self.project_path)
        


        return Repo(self.project_path)

    def stage_operation(self, file_path: str, operation: str):
        if operation in ['edit_file', 'delete_file', 'move_file']:
            if self._has_changes(file_path):
                self.pending_to_stage.append((file_path, operation))
                return True
        return False

    def _has_changes(self, file_path: str) -> bool:
        if file_path in self.repo.untracked_files:
            return True
        return False

    def commit_pending_operations(self, message: str):
        for file_path, operation in self.pending_to_stage:
            if operation in ['edit_file', 'delete_file', 'move_file']:
                self.repo.git.add(file_path)

        if self.pending_to_stage:
            self.repo.git.commit('-m', message)
            self.pending_to_stage.clear()
        else:
            logger.debug("No operations to commit.")

    def commit_all(self, message: str):
        # Check if there are any changes to commit
        if not self.repo.is_dirty(untracked_files=True):
            logger.debug("No changes to commit.")
            return "No changes to commit"

        self.repo.git.add(A=True)
        res = self.repo.git.commit('-m', f"{message}")
        logger.debug(f"Committed changes: {res}")
        return res

    def get_current_commit(self) -> str:
        return self.repo.head.commit.hexsha

    def get_commit_history(self, max_count: int = 10) -> List[Dict[str, str]]:
        commits = list(self.repo.iter_commits(max_count=max_count))
        return [
            {
                "hash": commit.hexsha,
                "author": commit.author.name,
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip()
            }
            for commit in commits
        ]