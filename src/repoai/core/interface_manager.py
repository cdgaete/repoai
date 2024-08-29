from ..components.module_loader import ModuleLoader
from .plugin_manager import PluginManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class InterfaceManager:
    def __init__(self, config):
        self.config = config
        self.interfaces = ModuleLoader.load_interfaces()
        
        # Initialize plugin manager
        plugin_dir = self.config.get('plugin_dir')
        self.plugin_manager = PluginManager(plugin_dir)
        self.plugin_manager.discover_plugins()
        
        # Merge built-in interfaces with plugin interfaces
        self.interfaces.update(self.plugin_manager.get_interfaces())

    def get_interface(self, interface_name: str):
        interface_class = self.interfaces.get(interface_name)
        if interface_class:
            return interface_class
        return None

    def list_interfaces(self):
        return list(self.interfaces.keys())