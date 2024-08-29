import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PluginManager:
    def __init__(self, plugin_dir: str):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, Any] = {}
        self.tasks: Dict[str, Any] = {}
        self.workflows: Dict[str, Any] = {}
        self.interfaces: Dict[str, Any] = {}

    def discover_plugins(self):
        if not self.plugin_dir.exists():
            logger.debug(f"Creating plugin directory: {self.plugin_dir}")
            self.plugin_dir.mkdir(parents=True, exist_ok=True)

        if not list(self.plugin_dir.glob('*.py')):
            logger.debug(f"No plugins found in {self.plugin_dir}")
            return

        for file_path in self.plugin_dir.glob('*.py'):
            if file_path.name.startswith('__'):
                continue
            plugin_name = file_path.stem

            spec = importlib.util.spec_from_file_location(plugin_name, file_path)
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            if hasattr(plugin_module, 'register_plugin'):
                plugin_components = plugin_module.register_plugin()
                self.plugins[plugin_name] = plugin_components
                self._organize_plugin_components(plugin_name, plugin_components)
                logger.debug(f"Loaded plugin: {plugin_name}")

    def _organize_plugin_components(self, plugin_name: str, components: Dict[str, Any]):
        for component_type, items in components.items():
            if component_type in ['tasks', 'workflows', 'interfaces']:
                getattr(self, component_type).update({f"{plugin_name}.{name}": cls for name, cls in items.items()})


    def get_tasks(self) -> Dict[str, Any]:
        return self.tasks

    def get_workflows(self) -> Dict[str, Any]:
        return self.workflows

    def get_interfaces(self) -> Dict[str, Any]:
        return self.interfaces

    def get_plugin(self, plugin_name: str) -> Any:
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, Any]:
        return self.plugins