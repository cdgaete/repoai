from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple


class BaseInterface(ABC):
    def __init__(self, project_manager: 'ProjectManager', model_config: Dict[str, Any]):
        self.project_manager = project_manager
        self.model_config = model_config

    @abstractmethod
    def run(self):
        """Main entry point for the application interface."""
        pass

    @abstractmethod
    def handle_input(self):
        """Handle user input."""
        pass

    @abstractmethod
    def display_output(self, output):
        """Display output to the user."""
        pass

    @abstractmethod
    def manage_context(self):
        """Manage the context for the application."""
        pass


class BaseTask(ABC):
    @abstractmethod
    def execute(self, context: Dict[str, Any]):
        pass
  

class BaseWorkflow(ABC):
    pass

