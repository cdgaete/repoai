from git import Repo, InvalidGitRepositoryError
from pathlib import Path
from typing import List, Dict, Tuple, Optional
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
        if file_path in self.get_untracked_and_changed_files():
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
    
    def get_file_versions(self, file_path: str) -> Dict[str, Optional[str]]:
        if file_path.startswith('/') or file_path.startswith('./'):
            return {"current": "", "previous": "", "message": "File path should be relative to project root and not contain './' or '/' at the beginning of the path"}
        abs_file_path = self.project_path / file_path
        if not abs_file_path.exists():
            return {"current": "", "previous": "", "message": "File not found"}
        result = {
            'current': "",
            'previous': "",
            'message': ""
        }
        with open(abs_file_path, 'r', encoding='utf-8') as f:
            result['current'] = f.read()

        try:
            commits = list(self.repo.iter_commits(paths=file_path, max_count=1))
            if len(commits) > 0:
                previous_commit = commits[0]
                result['previous'] = self.repo.git.show(f'{previous_commit.hexsha}:{file_path}')
                result['message'] = "Previous version found"
                logger.debug(f"Previous version of file {file_path} found: {previous_commit.hexsha}")
                return result
            else:
                result['previous'] = ""
                result['message'] = "No previous version found or the file is not tracked with git"
                logger.debug(f"No previous version found for file: {file_path}")
                return result

        except Exception as e:
            logger.error(f"Error retrieving previous version of file {file_path}: {str(e)}")
    
    def get_untracked_and_changed_files(self):
        changed = [item.a_path for item in self.repo.index.diff(None)]
        untracked = self.repo.untracked_files
        return changed + untracked
    
    def get_status(self) -> Dict[str, List[str]]:
        """Get the current Git status of the repository"""
        try:
            status = {
                'untracked': [],
                'modified': [],
                'deleted': [],
                'staged': []
            }
            
            if not self.repo:
                return status

            # Get repository status
            repo_status = self.repo.git.status('--porcelain').split('\n')
            
            for item in repo_status:
                if not item:
                    continue
                    
                status_code = item[:2]
                file_path = item[3:]
                
                if status_code.startswith('??'):
                    status['untracked'].append(file_path)
                elif status_code.startswith(' M'):
                    status['modified'].append(file_path)
                elif status_code.startswith(' D'):
                    status['deleted'].append(file_path)
                elif status_code.startswith('A ') or status_code.startswith('M '):
                    status['staged'].append(file_path)
                    
            return status
        except Exception as e:
            logger.error(f"Error getting git status: {str(e)}")
            raise

    def get_uncommitted_changes(self) -> List[Dict[str, str]]:
        """Get list of files with uncommitted changes"""
        try:
            changes = []
            if not self.repo:
                return changes

            # Get diff of working tree
            diff_index = self.repo.index.diff(None)
            
            # Add modified files
            for diff in diff_index:
                change_type = diff.change_type
                if change_type in ['M', 'A', 'D']:
                    changes.append({
                        'path': diff.a_path,
                        'type': change_type
                    })

            # Add untracked files
            for untracked_file in self.repo.untracked_files:
                changes.append({
                    'path': untracked_file,
                    'type': 'U'  # Untracked
                })

            return changes
        except Exception as e:
            logger.error(f"Error getting uncommitted changes: {str(e)}")
            raise

    def commit(self, message: str):
        """Commit changes with the given message"""
        try:
            self.commit_all(message)
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            raise

    def pull(self):
        """Pull changes from remote repository"""
        try:
            if not self.repo:
                raise ValueError("Git repository not initialized")
                
            self.repo.remotes.origin.pull()
        except Exception as e:
            logger.error(f"Error pulling changes: {str(e)}")
            raise

    def push(self):
        """Push changes to remote repository"""
        try:
            if not self.repo:
                raise ValueError("Git repository not initialized")
                
            self.repo.remotes.origin.push()
        except Exception as e:
            logger.error(f"Error pushing changes: {str(e)}")
            raise
