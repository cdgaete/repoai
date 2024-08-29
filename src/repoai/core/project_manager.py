import os
from functools import partial
from pathlib import Path
from typing import Any, List, Tuple, Dict, Callable, Union
from ..services.git_service import GitService
from ..utils.common_utils import validate_project_path
from .config_manager import ConfigManager
from ..components.module_loader import ModuleLoader
from .file_manager import FileManager
from .plugin_manager import PluginManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProjectManager:
    def __init__(self, project_path: Union[Path,str], create_if_not_exists: bool = False, error_if_exists: bool = False):
        if isinstance(project_path, str):
            project_path = Path(project_path)
        assert isinstance(project_path, Path), f"Invalid project path: {project_path}"

        self.project_name = project_path.stem
        if not validate_project_path(self.project_name):
            raise ValueError(f"Invalid project name: {self.project_name}. Project names must start with a letter and contain only letters, numbers, hyphens, and underscores.")

        self.config = ConfigManager()
        self.project_path = project_path
        self.file_manager = FileManager(self.project_path, ignore_file=self.config.get('repoai_ignore_file'))

        if not self.project_path.exists():
            if create_if_not_exists:
                self._create_new_project()
            else:
                raise ValueError(f"Project '{self.project_name}' does not exist. Set create_if_not_exists=True to create a new project.")
        else:
            if error_if_exists:
                raise ValueError(f"Project '{self.project_name}' already exists.")
            else:
                self.git_service = GitService(self.project_path)

        self.config.load_project_config(project_path)
        logger.info(f"Project '{self.project_name}' loaded.")
        
        self.pending_operations: List[Tuple[str, bool, str, Any]] = []

        # Load dynamic modules
        self.tasks = ModuleLoader.load_tasks()
        self.workflows = ModuleLoader.load_workflows()

        # Initialize plugin manager
        plugin_dir = self.config.get('plugin_dir', os.path.join(self.config.user_dir, 'plugins'))
        self.plugin_manager = PluginManager(plugin_dir)
        self.plugin_manager.discover_plugins()

        # Merge built-in modules with plugins
        self.tasks.update(self.plugin_manager.get_tasks())
        self.workflows.update(self.plugin_manager.get_workflows())

        self.generate_repoaiignore()

    def _create_new_project(self):
        self.project_path.mkdir(parents=True, exist_ok=True)
        self.git_service = GitService(self.project_path)
        self.file_manager.create_directory(self.config.REPOAI_DIR)
        self.config.save_project_config(self.project_path)
        self.generate_initial_files()
        self.git_service.commit_all("Initial commit")

    def get_task(self, task_name: str):
        return self.tasks.get(task_name)

    def get_workflow(self, workflow_name: str) -> Callable[..., Any]:
        workflow_class = self.workflows.get(workflow_name)
        return partial(workflow_class, self)

    def list_tasks(self):
        return list(self.tasks.keys())

    def list_workflows(self):
        return list(self.workflows.keys())

    @classmethod
    def project_exists(cls, project_path: Path):
        project_name = project_path.stem
        assert validate_project_path(project_name)
        return project_path.exists()

    def file_exists(self, file_path: str) -> bool:
        return self.file_manager.file_exists(file_path)
    
    def directory_exists(self, directory_path: str) -> bool:
        return self.file_manager.directory_exists(directory_path)

    def read_file(self, file_path: str) -> str:
        return self.file_manager.read_file(file_path)

    def batch_operations(self, operations: List[Dict[str, Any]]):
        processed_files = set()
        files_other_than_create_directory = set()
        deleted_directories = set()

        for op in operations:

            operation = op['operation']
            file_path = op['file_path']
            content = op.get('content')

            if operation in ['create_file', 'edit_file', 'delete_file', 'move_file']:
                files_other_than_create_directory.add(file_path)
            elif operation == 'delete_directory':
                deleted_directories.add(file_path)

            if file_path in processed_files:
                self.execute_pending_operations(f"Automatic commit before {operation} {file_path}")
                processed_files.clear()
                files_other_than_create_directory.clear()

            if operation == 'create_file':
                self.create_file_in_batch(file_path, content)
            elif operation == 'edit_file':
                self.edit_file_in_batch(file_path, content)
            elif operation == 'delete_file':
                self.delete_file_in_batch(file_path)
            elif operation == 'move_file':
                self.move_file_in_batch(file_path, content)  # 'content' is the destination path in this case
            elif operation == 'create_directory':
                self.create_directory_in_batch(file_path)  # This does not need to be commited. Operation performs inmediately
            elif operation == 'delete_directory':
                files_in_dir = [f for f in files_other_than_create_directory if f.startswith(file_path)]  # Pending files are in the directory being deleted
                if files_in_dir:
                    self.execute_pending_operations(f"Automatic commit before deleting directory {file_path}")
                    processed_files.clear()
                    files_other_than_create_directory.clear()
                self.delete_directory_in_batch(file_path)
            else:
                raise ValueError(f"Invalid operation: {operation} for file: {file_path}")

            processed_files.add(file_path)

        # Handle any remaining operations
        if self.pending_operations:
            self.execute_pending_operations(f"""Operation commit before '{operations[0]["operation"]}' '{operations[0]['file_path']}'""")

    def create_directory_in_batch(self, directory_path: str):  # This does not need to be commited.
        self.file_manager.create_directory(directory_path)

    def create_file_in_batch(self, file_path: str, content: str):
        self.stage_file_operation('create_file', file_path, content)

    def edit_file_in_batch(self, file_path: str, content: str):
        self.stage_file_operation('edit_file', file_path, content)

    def delete_file_in_batch(self, file_path: str):
        self.stage_file_operation('delete_file', file_path)

    def move_file_in_batch(self, source_path: str, destination_path: str):
        self.stage_file_operation('move_file', source_path, destination_path)

    def delete_directory_in_batch(self, directory_path: str):
        self.stage_file_operation('delete_directory', directory_path)

    def stage_file_operation(self, operation: str, file_path: str, content: str = None):
        if operation == 'delete_directory':
            files = self.file_manager.get_files_in_directory(file_path)
            collect = []
            for file in files:
                staged = self.git_service.stage_operation(file, 'delete_file')
                if staged:
                    collect.append(file)
            if collect:
                self.pending_operations.append((operation, True, file_path, None))
            else:
                self.pending_operations.append((operation, False, file_path, None))
        elif self.git_service.stage_operation(file_path, operation):
            self.pending_operations.append((operation, True, file_path, content))
        else:
            self.pending_operations.append((operation, False, file_path, content))

    def execute_pending_operations(self, commit_message: str):
        if self.pending_operations:
            self.git_service.commit_pending_operations(commit_message)
        for operation, staged, file_path, content in self.pending_operations:
            logger.debug(f"Operation {operation} on File {file_path} staged {staged}")
            if operation == 'create_file':
                self.file_manager.create_file(file_path, content)
            elif operation == 'edit_file':
                self.file_manager.edit_file(file_path, content)
            elif operation == 'delete_file':
                self.file_manager.delete_file(file_path)
            elif operation == 'move_file':
                self.file_manager.move_file(file_path, content)  # In this case, 'content' is the destination path
            elif operation == 'delete_directory':
                self.file_manager.delete_directory(file_path)
            else:
                raise ValueError(f"Invalid operation: {operation}")
        self.pending_operations.clear()

    def git_create_file(self, file_path: str, content: str):
        self.batch_operations([{'operation': 'create_file', 'file_path': file_path, 'content': content}])

    def git_edit_file(self, file_path: str, content: str):
        self.batch_operations([{'operation': 'edit_file', 'file_path': file_path, 'content': content}])

    def git_delete_file(self, file_path: str):
        self.batch_operations([{'operation': 'delete_file', 'file_path': file_path}])

    def git_move_file(self, source_path: str, destination_path: str):
        self.batch_operations([{'operation': 'move_file', 'file_path': source_path, 'content': destination_path}])

    def git_delete_directory(self, directory_path: str):
        self.batch_operations([{'operation': 'delete_directory', 'file_path': directory_path}])

    def git_create_directory(self, directory_path: str):
        self.batch_operations([{'operation': 'create_directory', 'file_path': directory_path}])

    def generate_initial_files(self):
        self.generate_gitignore()
        self.generate_repoaiignore()

    def generate_gitignore(self):
        if self.file_exists('.gitignore'):
            logger.debug("Gitignore already exists. Skipping generation.")
        else:
            gitignore_content = self.config.get('templates', {}).get('gitignore', '').strip()
            self.file_manager.save_file('.gitignore', gitignore_content)

    def generate_repoaiignore(self):
        ignore_file = self.config.get('repoai_ignore_file')
        if self.file_exists(ignore_file):
            logger.debug("Repoaiignore already exists. Skipping generation.")
        else:
            repoaiignore_content = self.config.get('templates', {}).get('repoaiignore', '').strip()
            self.file_manager.save_file(ignore_file, repoaiignore_content)


