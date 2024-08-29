from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.core.interface_manager import InterfaceManager

# Define your model configuration
model_config = {
    "project_modification_workflow": {
        "project_modification_task": {
            "model": "gpt-4o-mini-2024-07-18",
            "temperature": 0.7
        },
        "file_edit_task": {
            "model": "gpt-4o-mini-2024-07-18",
            "temperature": 0.2
        }
    }
}

model_config = {
    "project_modification_workflow": {
        "project_modification_task": {
            "model": "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct",
            "temperature": 0.7
        },
        "file_edit_task": {
            "model": "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct",
            "temperature": 0.2
        }
    }
}

model_config = {
    "project_modification_workflow": {
        "project_modification_task": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "temperature": 0.7
        },
        "file_edit_task": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "temperature": 0.2
        }
    }
}

# model_config = {}


initialize()

project_path = Path(input("Enter project path: "))

# Create a ProjectManager instance
pm = ProjectManager(project_path, create_if_not_exists=False, error_if_exists=False)

# Create an InterfaceManager instance
im = InterfaceManager(pm.config)

# Get the project modification interface and run it
ModIn = im.get_interface("project_modification_interface")(pm, model_config)
ModIn.run()
