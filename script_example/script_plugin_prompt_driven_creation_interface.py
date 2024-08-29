from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.core.plugin_manager import PluginManager

# Define your model configuration
model_config = {
    "prompt_driven_project_creation_workflow": {
        "project_description_and_structure_task": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "temperature": 0.7,
            "max_tokens": 2000,
            "use_prompt_caching": True,
        },
        "structure_to_paths_task": {
            "model": "anthropic/claude-3-haiku-20240307",
            "temperature": 0.2,
            "max_tokens": 600,
            "use_prompt_caching": False,
        },
        "file_content_generation_task": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "temperature": 0.2,
            "max_tokens": 8000,
            "use_prompt_caching": True,
        }
    }
}

model_config = {}

config = initialize()
plugin_manager = PluginManager(config.get('plugin_dir'))
plugin_manager.discover_plugins()

print("Available plugin interfaces:")
for name in plugin_manager.get_interfaces().keys():
    print(f"  - {name}")

interface_name = "prompt_driven_project_creation_interface"
project_path = Path(input("Enter project path (exit to quit): "))
project_manager = ProjectManager(project_path, create_if_not_exists=True, error_if_exists=False)
interface_class = plugin_manager.get_interfaces().get(interface_name)

interface = interface_class(project_manager, model_config)
interface.run()
