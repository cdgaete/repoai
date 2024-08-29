# RepoAI: Empowering AI-Assisted Repository Content Creation and Editing

[![To Our Website](https://img.shields.io/badge/WWW-Access%20Our%20Website-orange?style=for-the-badge&logo=WWW&logoColor=white)](https://repoai.dev) [![Join our Discord](https://img.shields.io/badge/Discord-Join%20our%20server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/ee88tmwHmR)  [![Follow on GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/cdgaete/repoai)

RepoAI is an innovative, AI-powered framework designed for repository content creation and editing. By leveraging the power of AI, RepoAI aims to streamline development processes and boost productivity.

## Key Features

1. **AI-Assisted Repository Management**
   - Intelligent project structure generation
   - Automated file content creation and editing
   - Smart version control integration with Git

2. **Flexible LLM Integration with LiteLLM**
   - Support for various AI models
   - Seamless integration with popular providers like OpenAI, Anthropic, and more

3. **Plugin Architecture**
   - Easy integration of custom workflows and tasks
   - Extensible framework for adding new functionalities

4. **Project-Aware Conversations**
   - Context-aware AI interactions based on your project structure
   - Intelligent code suggestions and explanations

5. **Markdown-Based Documentation**
   - Automated generation of project documentation
   - Easy-to-read project overviews and file contents

## Getting Started

1. **Installation**
   Create and activate a conda environment:
```bash
conda create -n repoai python=3.9
conda activate repoai
```

   Install RepoAI:
```bash
pip install repoai
```

2. **Configuration**
   Set up your API keys according to the LiteLLM documentation:
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
# Add other API keys as needed, e.g.:
# export OPENAI_API_KEY="your-openai-api-key-here"
```

3. **Model Configuration**

   RepoAI uses LiteLLM for model integration. It's crucial to use the correct model names as specified by LiteLLM. You can find the list of supported models and their correct names in the [LiteLLM documentation](https://docs.litellm.ai/docs/providers).

   There are several ways to configure the models:

   a. **Using model_config in scripts**

   You can specify the model configuration when creating an interface:

```python
model_config = {
    "project_generation_workflow": {
        "project_description_chat_task": {
            "model": "anthropic/claude-3-sonnet-20240229",
            "max_tokens": 4000,
            "use_prompt_caching": True,
        },
        "file_content_generation_task": {
            "model": "anthropic/claude-3-opus-20240229",
            "max_tokens": 4000,
            "use_prompt_caching": True,
        }
    }
}

GenInt = im.get_interface("project_generation_interface")(pm, model_config)
```

   b. **Using config.set()**

   You can set the default model globally:

```python
from repoai import initialize

config = initialize()
config.set('default_model', 'anthropic/claude-3-sonnet-20240229', is_global=True)
```

   c. **Editing config.json**

   You can also edit the global configuration file directly. The file is typically located at:
   - Windows: `C:\Users\YourUsername\AppData\Local\repoai\repoai_config.json`
   - macOS: `/Users/YourUsername/Library/Application Support/repoai/repoai_config.json`
   - Linux: `/home/YourUsername/.local/share/repoai/repoai_config.json`

   Edit the `default_model` field in this file:

```json
{
  "default_model": "anthropic/claude-3-sonnet-20240229",
  // other configuration options...
}
```

   Remember to use the correct model names as specified by LiteLLM to ensure compatibility and proper functionality.

4. **Caching for Anthropic Models**

   RepoAI implements caching for Anthropic models to improve performance and reduce API calls. To enable caching, you can use the `use_prompt_caching` parameter in your model configuration.

   Example of enabling caching in a model configuration file:

```json
{
  "project_generation_workflow": {
    "project_description_chat_task": {
      "model": "anthropic/claude-3-sonnet-20240229",
      "max_tokens": 4000,
      "use_prompt_caching": true
    },
    "project_structure_chat_task": {
      "model": "anthropic/claude-3-sonnet-20240229",
      "max_tokens": 4000,
      "use_prompt_caching": true
    },
    "structure_to_paths_task": {
      "model": "anthropic/claude-3-haiku-20240307",
      "max_tokens": 1000,
      "use_prompt_caching": false
    },
    "file_content_generation_task": {
      "model": "anthropic/claude-3-opus-20240229",
      "max_tokens": 8000,
      "use_prompt_caching": true
    }
  },
  "project_modification_workflow": {
    "project_modification_task": {
      "model": "anthropic/claude-3-sonnet-20240229",
      "max_tokens": 4000,
      "use_prompt_caching": true
    },
    "file_edit_task": {
      "model": "anthropic/claude-3-sonnet-20240229",
      "max_tokens": 4000,
      "use_prompt_caching": true
    }
  }
}
```

   In this example, caching is enabled for most tasks using Anthropic models. The `structure_to_paths_task` uses a different model and has caching disabled.

   When caching is enabled, RepoAI will automatically handle the caching of prompts for Anthropic models, which can significantly improve performance for repetitive tasks or when working with large projects.

5. **Usage Examples**

   a. **Project Generation**

   Create a Python script `generate_project.py`:
```python
from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.core.interface_manager import InterfaceManager

initialize()

project_path = Path("/path/to/your/new/project")

pm = ProjectManager(project_path, create_if_not_exists=True, error_if_exists=False)
im = InterfaceManager(pm.config)
GenInt = im.get_interface("project_generation_interface")(pm)
GenInt.run()
```

   Run the script:
```bash
python generate_project.py
```

   b. **Project Modification**

   Create a Python script `modify_project.py`:
```python
from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.core.interface_manager import InterfaceManager

initialize()

project_path = Path("/path/to/your/existing/project")

pm = ProjectManager(project_path, create_if_not_exists=False, error_if_exists=False)
im = InterfaceManager(pm.config)
ModInt = im.get_interface("project_modification_interface")(pm)
ModInt.run()
```

   Run the script:
```bash
python modify_project.py
```

   c. **Using Plugins**

   Create a Python script `use_plugin.py`:
```python
from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.core.plugin_manager import PluginManager

config = initialize()
plugin_manager = PluginManager(config.get('plugin_dir'))
plugin_manager.discover_plugins()

interface_name = "prompt_driven_project_creation_interface"
project_path = Path("/path/to/your/project")
project_manager = ProjectManager(project_path, create_if_not_exists=True, error_if_exists=False)
interface_class = plugin_manager.get_interfaces().get(interface_name)

interface = interface_class(project_manager)
interface.run()
```

   Run the script:
```bash
python use_plugin.py
```

6. **Command-Line Interface**

   RepoAI supports command-line usage with the following options:

```bash
# Create a new project
repoai create --project_path /path/to/new/project [--model_config /path/to/model_config.json]

# Edit an existing project
repoai edit --project_path /path/to/existing/project [--model_config /path/to/model_config.json]

# Generate a report for a project
repoai report --project_path /path/to/project

# Use a plugin
repoai plugin --project_path /path/to/project --interface plugin_interface_name [--model_config /path/to/model_config.json]

# List available plugins
repoai plugin
```

   The `--model_config` option allows you to specify a JSON file containing model configurations for different tasks. For example:

```json
{
  "project_generation_workflow": {
    "project_description_chat_task": {
      "model": "anthropic/claude-3-sonnet-20240229",
      "max_tokens": 4000
    },
    "file_content_generation_task": {
      "model": "anthropic/claude-3-opus-20240229",
      "max_tokens": 4000
    }
  }
}
```

7. **Custom Plugins**

   RepoAI looks for custom plugins in the following default location:
   - Windows: `C:\Users\YourUsername\AppData\Local\repoai\plugins`
   - macOS: `/Users/YourUsername/Library/Application Support/repoai/plugins`
   - Linux: `/home/YourUsername/.local/share/repoai/plugins`

   To change the default plugin directory, you can use the `config.set()` method:

```python
from repoai import initialize

config = initialize()
config.set('plugin_dir', '/path/to/your/custom/plugin/directory', is_global=True)
```

   Alternatively, you can edit the `repoai_config.json` file directly and modify the `plugin_dir` field:

```json
{
  "plugin_dir": "/path/to/your/custom/plugin/directory",
  // other configuration options...
}
```

   To create a custom plugin:

   1. Create a new Python file in the plugin directory.
   2. Define your custom tasks, workflows, or interfaces in the file.
   3. Implement a `register_plugin()` function that returns a dictionary of your custom components.

   Example plugin structure:

```python
# my_custom_plugin.py

from repoai.components.components_base import BaseTask, BaseWorkflow, BaseInterface

class MyCustomTask(BaseTask):
    # ... task implementation ...

class MyCustomWorkflow(BaseWorkflow):
    # ... workflow implementation ...

class MyCustomInterface(BaseInterface):
    # ... interface implementation ...

def register_plugin():
    return {
        "tasks": {"my_custom_task": MyCustomTask},
        "workflows": {"my_custom_workflow": MyCustomWorkflow},
        "interfaces": {"my_custom_interface": MyCustomInterface}
    }
```

   RepoAI will automatically discover and load your custom plugins when it's initialized.

## Community and Collaboration

- **Contribute**: [GitHub Repository](https://github.com/cdgaete/repoai)
- **Discord Community**: [Join our server](https://discord.gg/ee88tmwHmR)

## Customization and Extension

RepoAI is designed to be highly customizable and extensible through its plugin architecture. You can create custom plugins to add new functionalities, workflows, or tasks.

1. **Creating Plugins**: Develop new plugins in the `plugins` directory.
2. **Custom Interfaces**: Implement custom interfaces in your plugins to create new ways of interacting with RepoAI.
3. **Task Development**: Create custom tasks within your plugins to extend RepoAI's capabilities.

## Project Structure

The main components of RepoAI are organized as follows:

- `src/repoai/`: Core RepoAI package
  - `components/`: Base classes and implementations for tasks, workflows, and interfaces
  - `core/`: Core functionality including project management, configuration, and plugin handling
  - `services/`: Various services like Git, LLM, and Docker integration
  - `utils/`: Utility functions and helper classes

- `plugins_example/`: Example plugins demonstrating how to extend RepoAI
- `script_example/`: Example scripts showing how to use RepoAI programmatically

## Best Practices and Considerations

1. **Model Selection**: Choose appropriate models for your tasks. RepoAI supports various models through LiteLLM.
2. **Security**: Always review AI-generated code before execution, especially when using custom plugins.
3. **Version Control**: Regularly commit your changes and use branching strategies to maintain a clean project history.
4. **Documentation**: Encourage the AI to generate inline comments and documentation for better code maintainability.

## Disclaimer

RepoAI is a powerful tool that can significantly enhance your development workflow. However, it's important to remember that AI-generated code should always be reviewed and tested thoroughly before deployment. While we strive for accuracy and reliability, the responsibility for the final code quality and functionality lies with the developer.

Join us in revolutionizing the way we manage repositories and write code. With RepoAI, the future of AI-assisted development is here today!

---

We're excited to see what you'll build with RepoAI. Happy coding!