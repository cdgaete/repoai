import importlib
import os
from typing import Dict, Any, Type
from .components_base import BaseTask, BaseWorkflow, BaseInterface
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ModuleLoader:

    @staticmethod
    def load_tasks() -> Dict[str, Type[BaseTask]]:
        return ModuleLoader._load_modules('tasks', BaseTask)

    @staticmethod
    def load_workflows() -> Dict[str, Type[BaseWorkflow]]:
        return ModuleLoader._load_modules('workflows', BaseWorkflow)
    
    @staticmethod
    def load_interfaces() -> Dict[str, Type[BaseInterface]]:
        return ModuleLoader._load_modules('interfaces', BaseInterface)

    @staticmethod
    def _load_modules(module_type: str, base_class: Type[Any]) -> Dict[str, Type[Any]]:
        modules = {}
        module_dir = os.path.join(os.path.dirname(__file__), '..', 'components', module_type)
        for filename in os.listdir(module_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                module = importlib.import_module(f'..components.{module_type}.{module_name}', package='repoai.components')
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if isinstance(item, type) and issubclass(item, base_class) and item != base_class:
                        modules[module_name] = item
        return modules