from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.core.interface_manager import InterfaceManager

# Define your model configuration
model_config = {
    "project_generation_workflow": {
        "project_description_chat_task": {
            "model": "gpt-4-turbo",
            "temperature": 0.7
        },
        "project_structure_chat_task": {
            "model": "gpt-4-turbo",
            "temperature": 0.5
        },
        "structure_to_paths_task": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.2
        },
        "file_content_generation_task": {
            "model": "gpt-4-turbo",
            "temperature": 0.8
        }
    }
}

model_config = {
    "project_generation_workflow": {
        "project_description_chat_task": {
            "model": "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct",
            "temperature": 0.7
        },
        "project_structure_chat_task": {
            "model": "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct",
            "temperature": 0.5
        },
        "structure_to_paths_task": {
            "model": "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct",
            "temperature": 0.2
        },
        "file_content_generation_task": {
            "model": "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct",
            "temperature": 0.8
        }
    }
}


model_config = {
    "project_generation_workflow": {
        "project_description_chat_task": {
            "model": "gpt-4o-mini-2024-07-18",
            "temperature": 0.7
        },
        "project_structure_chat_task": {
            "model": "gpt-4o-mini-2024-07-18",
            "temperature": 0.5
        },
        "structure_to_paths_task": {
            "model": "gpt-4o-mini-2024-07-18",
            "temperature": 0.2
        },
        "file_content_generation_task": {
            "model": "gpt-4o-mini-2024-07-18",
            "temperature": 0.8
        }
    }
}

model_config = {
    "project_generation_workflow": {
        "project_description_chat_task": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "max_tokens": 4000,
            "use_prompt_caching": True,
        },
        "project_structure_chat_task": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "max_tokens": 4000,
            "use_prompt_caching": True,
        },
        "structure_to_paths_task": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "max_tokens": 1000,
            "use_prompt_caching": False,
        },
        "file_content_generation_task": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "max_tokens": 8000,
            "use_prompt_caching": True,
        }
    }
}

model_config = {}

initialize()

project_path = Path(input("Enter project path: "))

pm = ProjectManager(project_path, create_if_not_exists=True, error_if_exists=False)
im = InterfaceManager(pm.config)
GenInt = im.get_interface("project_generation_interface")(pm, model_config)
GenInt.run()
