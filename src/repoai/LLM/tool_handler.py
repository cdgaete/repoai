# src/repoai/LLM/tool_handler.py

import importlib
import json
from typing import Dict, Any, Callable, List
from ..utils.config_manager import config_manager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class ToolHandler:
    def __init__(self):
        self.tools = {}

    def _load_tools(self):
        self.tools = {}  # Clear existing tools
        for tool in config_manager.get('AVAILABLE_TOOLS', []):
            try:
                module = importlib.import_module(tool['module'])
                function = getattr(module, tool['function'])
                self.tools[tool['name']] = {
                    'function': function,
                    'description': tool['description'],
                    'input_schema': tool['input_schema'],
                    'validate': getattr(module, f"validate_{tool['function']}", None)
                }
                logger.info(f"Loaded tool: {tool['name']}")
            except Exception as e:
                logger.error(f"Failed to load tool {tool['name']}: {str(e)}")

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        self._load_tools()  # Ensure tools are up-to-date before execution
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        try:
            result = self.tools[tool_name]['function'](**kwargs)
            if isinstance(result, dict) and "error" in result:
                logger.error(f"Error executing tool {tool_name}: {result['error']}")
                raise Exception(result['error'])
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            raise

    def get_tool_descriptions(self) -> Dict[str, Dict[str, Any]]:
        return {name: {'description': tool['description'], 'input_schema': tool['input_schema']}
                for name, tool in self.tools.items()}

    def validate_tools(self) -> bool:
        """Validate that all tools defined in Config are properly loaded and can be validated."""
        for tool_name, tool in self.tools.items():
            if tool['validate'] is None:
                logger.warning(f"No validation method found for tool: {tool_name}")
                continue
            
            try:
                is_valid, message = tool['validate']()
                if not is_valid:
                    logger.error(f"Tool validation failed for {tool_name}: {message}")
                    return False
                logger.info(f"Tool validation passed for {tool_name}")
            except Exception as e:
                logger.error(f"Exception during validation of tool {tool_name}: {str(e)}")
                return False
        return True