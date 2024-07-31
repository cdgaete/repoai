# src/repoai/config.py

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Union, List, Optional, Any

from .utils.context_managers import use_tools

class Config:
    # Load environment variables from .env file
    load_dotenv()

    # API Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OLLAMA_API_KEY: Optional[str] = os.getenv("OLLAMA_API_KEY", "Any_API_Key")
    OLLAMA_API_HOST: str = os.getenv("OLLAMA_API_HOST", "http://localhost:11434")

    # File and text processing
    SAMPLE_SIZE_FOR_TEXT_DETECTION: int = 1024
    CHARDET_CONFIDENCE_THRESHOLD: float = 0.8
    PRINTABLE_RATIO_THRESHOLD: float = 0.7

    TASK_MODEL_MAPPING: Dict[str, str] = {
        "PROJECT_DESCRIPTION_CHAT": "claude-3-5-sonnet-20240620",
        "PROJECT_CREATOR": "claude-3-5-sonnet-20240620",
        "FORMAT_DIRECTORY_STRUCTURE": "claude-3-haiku-20240307",
        "FORMAT_FILE_CONTENTS": "claude-3-5-sonnet-20240620",
        "EXPERT_CHAT": "claude-3-5-sonnet-20240620",
        "EDIT_FILE": "claude-3-5-sonnet-20240620",
    }

    MODELS_PROVIDER_MAPPING: Dict[str, str] = {
        "claude-3-haiku-20240307": "anthropic",
        "claude-3-5-sonnet-20240620": "anthropic",
        "llama3.1:latest": "ollama",  # Add Ollama model
        "llama3-groq-tool-use:latest": "ollama",
    }

    MODELS_CONFIG_MAPPING: Dict[str, Dict[str, Any]] = {
        "claude-3-haiku-20240307": dict(
            max_tokens=4000,
            temperature=0.3,
            top_p=0.1,
            top_k=1,
            metadata=None,
            stop_sequences=None,
            stream=False,
            tools=None,
            tool_choice={"type": "auto"},
            extra_headers=None,
            extra_query=None,
            extra_body=None,
            timeout=600.0,
        ),
        "claude-3-5-sonnet-20240620": dict(
            max_tokens=4000,
            temperature=0.3,
            top_p=0.1,
            top_k=1,
            metadata=None,
            stop_sequences=None,
            stream=False,
            tools=None,
            tool_choice={"type": "auto"},
            extra_headers=None,
            extra_query=None,
            extra_body=None,
            timeout=600.0,
        ),
        "llama3.1:latest": dict(
            max_tokens=4000,
            temperature=0.7,
            top_p=0.9,
            stream=False,
        ),
        "llama3-groq-tool-use:latest": dict(
            max_tokens=4000,
            temperature=0.7,
            top_p=0.9,
            stream=False,
        ),
    }

    PROJECT_DESCRIPTION_CHAT_PROMPT: str = os.getenv("PROJECT_DESCRIPTION_CHAT_PROMPT", """
You are an AI assistant helping to create a detailed project description. Your goal is to ask relevant questions and provide suggestions to help the user create a comprehensive project description. Consider the following aspects:

1. Project type and purpose
2. Target audience or users
3. Key features and functionalities
4. Technology stack (programming languages, frameworks, databases, etc.)
5. Project structure and architecture
6. Third-party integrations or APIs
7. Deployment and hosting considerations
8. Potential challenges or considerations

Ask questions to gather information about these aspects and any other relevant details. Provide suggestions and examples when appropriate. After each interaction, summarize the current project description in a format suitable for project initialization.

Always include an updated "Current Project Description Prompt" at the end of your response, which should be a concise summary of the project based on the information gathered so far. This prompt will be used to generate the project structure and files.

Example format for your response:
[Your response to the user's input, including questions, suggestions, and clarifications]

Current Project Description Prompt:
[Concise summary of the project description based on the information gathered so far]
""")

    PROJECT_CREATOR_PROMPT: str = os.getenv("PROJECT_CREATOR_PROMPT", """
You are an AI assistant helping to create a new software project.
Based on the user's responses to the project questionnaire, generate a detailed project summary.
Include a directory structure and initial file contents for the project.
Consider the project type, programming language, framework (if applicable), and any custom structure preferences.
Provide a comprehensive and well-organized project setup that follows best practices for the chosen technology stack.

Your response should follow this structure:
1. A brief description of the project
2. A directory structure in a code block, using a tree-like format
3. Initial file contents for each file in the structure, using the following format:

## File: path/to/file.ext
```language
file content here
```

Ensure that all files mentioned in the directory structure have corresponding file content sections.
""")
    
    FORMAT_DIRECTORY_STRUCTURE_PROMPT: str = os.getenv("FORMAT_DIRECTORY_STRUCTURE_PROMPT", """
You are an AI assistant that extracts and formats directory structures.
Given a user's input, extract the directory structure and format it exactly as follows:

<Tree>
root_directory/
root_directory/subdirectory1/
root_directory/subdirectory1/file1.txt
root_directory/subdirectory1/file2.txt
root_directory/subdirectory2/
root_directory/subdirectory2/file3.txt
root_directory/file4.txt
</Tree>

Rules:
1. Always start with <Tree> on a new line and end with </Tree> on a new line.
2. The root directory should be on the first line inside the <Tree> tags, followed by a forward slash (/).
4. Directories should end with a forward slash (/).
5. Files should not have any trailing characters.
6. Ensure no indentation for subdirectories and files.
7. If no clear structure is provided, create a minimal structure with a root directory and a README.md file.
8. Do not include any explanatory text or markdown formatting outside the <Tree> tags.""")

    FORMAT_FILE_CONTENTS_PROMPT: str = os.getenv("FORMAT_FILE_CONTENTS_PROMPT", """
You are an AI assistant that extracts file contents from a given input. Your task is to identify any file contents mentioned or implied in the input, even if they are not explicitly formatted as code blocks. Follow these rules:

1. Look for any mentions of file names or file types (e.g., 'requirements.txt', 'app.py', '.env').
2. For each identified file, extract or infer its contents based on the context provided.
3. Format the output as follows:
    - Always start with <FileBlock> on a new line and end with </FileBlock> on a new line.
    - Start a code block, using triple backticks (```).
    - If the file has a specific language, specify it after the opening triple backticks.
    - First line after starting the code block should be one hash signs followed by a space and the file path. Example: # root_directory/filename.ext
    - Include the entire file content within the code block.
    - Finish the code block, using triple backticks (```) on a new line.
    - End each FileBlock with </FileBlock> on a new line.
    - Separate each FileBlock with a newline.
4. If the content for a file is not explicitly provided but can be reasonably inferred, generate appropriate content based on the context.
5. If no file contents can be extracted or inferred, respond with "No file contents could be extracted or inferred from the input."

Be thorough in your search for file contents, don't hesitate to generate reasonable content for mentioned files if specifics are not provided, and don't include any additional concluding remarks. Ensure that each code block is properly enclosed with backticks (```) and every <FileBlock> is properly closed with </FileBlock>.
""")

    EXPERT_CHAT_PROMPT: str = os.getenv("EXPERT_CHAT_PROMPT", """
You are an AI expert on coding and software design. Provide advice and suggestions based on the current project structure and files. 
When suggesting changes to the project, use the following format:

To edit an existing file:
EDIT_FILE: [file_path]
```
[Your suggested changes]
```
END_EDIT

To create a new file:
CREATE_FILE: [file_path]
```
[File content]
```
END_CREATE

To delete a file:
DELETE_FILE: [file_path]

To move a file:
MOVE_FILE: [source_file_path]:[destination_file_path]

You can suggest multiple file operations in one response. Always provide a clear explanation of your suggestions before listing the file operations.
Remember that edit and create operations must end with END_EDIT or END_CREATE respectively.
File paths must be relative to the root directory.
""")
    
    EDIT_FILE_PROMPT: str = os.getenv("EDIT_FILE_PROMPT", """
You are an expert on coding edition and software design. Provide the full content of a file based on the original file content and the suggested changes.
If the suggested changes represent the complete new file, provide the suggested content only. You must not add any additional comments or explanations to the content.
Return your response enclosed in triple backticks (```) and line breaks (`\n`) so: ```\n[content]\n```
""")
    
    # File and Directory Configuration
    LLM_RESPONSE_LOG: str = "llm_response_log.jsonl"
    IGNORE_FILE: str = ".repoaiignore"
    TOKEN_COUNTS_FILE: str = "repoai_token_counts.json"

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # LLM log
    MAX_LOG_SIZE: int = int(os.getenv("MAX_LOG_SIZE", str(10 * 1024 * 1024)))  # 10 MB

    # Streamlit Configuration
    STREAMLIT_THEME: Dict[str, str] = {
        "primaryColor": "#FF4B4B",
        "backgroundColor": "#0E1117",
        "secondaryBackgroundColor": "#262730",
        "textColor": "#FAFAFA",
        "font": "sans serif",
    }

    AVAILABLE_TOOLS: List[Dict[str, Any]] = [
        {
            "name": "get_current_time",
            "description": "Get the current time in a given time zone",
            "module": "repoai.LLM.tool_functions",
            "function": "get_current_time",
            "input_schema": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "The IANA time zone name, e.g. America/Los_Angeles"
                    }
                },
                "required": ["timezone"]
            }
        }
    ]

    # File type configurations
    DEFAULT_IGNORE_PATTERNS: List[str] = [
        ".git/",
        "__pycache__/",
        "*.pyc",
        ".DS_Store",
        ".idea/",
        ".vscode/",
        "node_modules/",
        "build/",
        "dist/",
        "secrets/",
        "env/",
        "venv/"
    ]

    FILE_EXTENSION_TO_LANGUAGE: Dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".html": "html",
        ".css": "css",
        ".md": "markdown",
        ".json": "json",
        ".xml": "xml",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".sh": "bash",
        ".bat": "batch",
        ".txt": "text",
        ".ini": "ini",
        ".cfg": "ini",
        ".csv": "csv",
        ".ts": "typescript",
        ".tsx": "typescript",
    }

    # Template content for generated files
    GITIGNORE_TEMPLATE: str = """
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
env/
.venv/

# IDEs and editors
.vscode/
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
Thumbs.db

# Logs
*.log

# Environment variables
.env

# RepoAI specific
repochat_log.md
temp_repo_content.md
.repoaiignore
.env
.gitignore
llm_response_log.jsonl
repoai_token_counts.json
"""

    REPOAIIGNORE_TEMPLATE: str = """
# Version control
.git/

# Build outputs
build/
dist/

.DS_Store/
.vscode/
.idea/

# Dependency directories
node_modules/

# Large binary files
*.zip
*.tar.gz
*.rar

# Sensitive information
secrets/

.repoaiignore
.env
.gitignore
llm_response_log.jsonl
repoai_token_counts.json

__pycache__/
"""

    ENV_TEMPLATE: str = """
# API Configuration
# ANTHROPIC_API_KEY=your_api_key_here
# DEFAULT_MODEL=claude-3-sonnet-20240229
# MAX_TOKENS=4000

# Logging Configuration
# LOG_LEVEL=INFO

"""

    PROJECT_ROOT_PATH: Optional[Path] = None
    CURRENT_PROJECT_PATH: Optional[Path] = None
    TOKEN_COUNTS: Dict[str, Dict[str, Dict[str, int]]] = {"creation": {}, "edition": {}}

    @classmethod
    def set_current_project(cls, project_name: str) -> None:
        if cls.PROJECT_ROOT_PATH is None:
            raise ValueError("PROJECT_ROOT_PATH has not been initialized")
        cls.CURRENT_PROJECT_PATH = cls.PROJECT_ROOT_PATH / project_name
        cls.load_token_counts()

    @classmethod
    def initialize_paths(cls, project_root_path: Union[str, Path]) -> None:
        cls.PROJECT_ROOT_PATH = Path(project_root_path)
        cls.load_token_counts()

    @classmethod
    def set_task_model(cls, task: str, model: str) -> None:
        if model not in cls.MODELS_PROVIDER_MAPPING:
            raise ValueError(f"Unsupported model: {model}")
        if task not in cls.TASK_MODEL_MAPPING:
            raise ValueError(f"Unsupported task: {task}")
        cls.TASK_MODEL_MAPPING[task] = model

    @classmethod
    def get_project_root_path(cls, *paths) -> Path:
        if cls.PROJECT_ROOT_PATH is None:
            raise ValueError("PROJECT_ROOT_PATH has not been initialized")
        return cls.PROJECT_ROOT_PATH.joinpath(*paths)
    
    @classmethod
    def get_current_project_path(cls, *paths) -> Path:
        if cls.CURRENT_PROJECT_PATH is None:
            raise ValueError("CURRENT_PROJECT_PATH has not been set. Use set_current_project() first.")
        return cls.CURRENT_PROJECT_PATH.joinpath(*paths)

    @classmethod
    def get_prompt(cls, prompt_name: str) -> str:
        return getattr(cls, prompt_name, cls.PROJECT_DESCRIPTION_CHAT_PROMPT)

    @classmethod
    def get_model_for_task(cls, task: str) -> str:
        if task not in cls.TASK_MODEL_MAPPING:
            raise ValueError(f"Unsupported task: {task}")
        return cls.TASK_MODEL_MAPPING[task]
    
    @classmethod    
    def get_provider_for_model(cls, model: str) -> str:
        if model in cls.MODELS_PROVIDER_MAPPING:
            return cls.MODELS_PROVIDER_MAPPING[model]
        else:
            raise ValueError(f"Unsupported model: {model}")
    
    @staticmethod
    def get_llm_response_log_file(dir_path: Union[str, Path]) -> Path:
        return Path(dir_path) / Config.LLM_RESPONSE_LOG

    @classmethod
    def get_provider_api_key(cls, provider: str) -> Optional[str]:
        if provider == "anthropic":
            return cls.ANTHROPIC_API_KEY
        elif provider == "ollama":
            return cls.OLLAMA_API_KEY
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
    @classmethod
    def get_provider_api_host(cls, provider: str) -> Optional[str]:
        if provider == "anthropic":
            return None
        elif provider == "ollama":
            return cls.OLLAMA_API_HOST
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @classmethod
    def get_ignore_file(cls, dir_path: Union[str, Path]) -> Path:
        return Path(dir_path) / Config.IGNORE_FILE

    @classmethod
    def get_model_config(cls, model: str) -> Dict[str, Any]:
        if model in cls.MODELS_CONFIG_MAPPING:
            config = cls.MODELS_CONFIG_MAPPING[model].copy()
            if use_tools():
                if cls.MODELS_PROVIDER_MAPPING[model] == "anthropic":
                    config['tools'] = cls.get_available_tools()
                    if not isinstance(config.get('tool_choice'), dict):
                        config['tool_choice'] = {"type": "auto"}
                elif cls.MODELS_PROVIDER_MAPPING[model] == "ollama":
                    config['tools'] = cls.get_available_tools()
            else:
                # Remove tool-related configurations if tools are not being used
                config.pop('tools', None)
                config.pop('tool_choice', None)
            return config
        else:
            raise ValueError(f"Unsupported model: {model}")

    @classmethod
    def update_model_config(cls, model: str, **kwargs):
        if model in cls.MODELS_CONFIG_MAPPING:
            if 'tool_choice' in kwargs and not isinstance(kwargs['tool_choice'], dict):
                kwargs['tool_choice'] = {"type": kwargs['tool_choice']}
            cls.MODELS_CONFIG_MAPPING[model].update(kwargs)
        else:
            raise ValueError(f"Unsupported model: {model}")
        
    @classmethod
    def get_available_tools(cls):
        if not use_tools():
            return []
        tools = cls.AVAILABLE_TOOLS.copy()
        return tools

    @classmethod
    def load_token_counts(cls):
        if cls.CURRENT_PROJECT_PATH is None:
            cls.TOKEN_COUNTS = {"creation": {}, "edition": {}}
            return
        
        token_counts_path = cls.CURRENT_PROJECT_PATH / cls.TOKEN_COUNTS_FILE
        if token_counts_path.exists():
            with open(token_counts_path, 'r') as f:
                cls.TOKEN_COUNTS = json.load(f)
        else:
            # Create a new file with default values
            cls.TOKEN_COUNTS = cls._get_default_token_counts()
            cls.save_token_counts()

    @classmethod
    def save_token_counts(cls):
        if cls.CURRENT_PROJECT_PATH is None:
            return  # Don't save if no project is selected
        
        token_counts_path = cls.CURRENT_PROJECT_PATH / cls.TOKEN_COUNTS_FILE
        with open(token_counts_path, 'w') as f:
            json.dump(cls.TOKEN_COUNTS, f, indent=2)

    @classmethod
    def update_token_count(cls, phase: str, model: str, input_tokens: int, output_tokens: int):
        if phase not in cls.TOKEN_COUNTS:
            cls.TOKEN_COUNTS[phase] = {}
        
        if model not in cls.TOKEN_COUNTS[phase]:
            cls.TOKEN_COUNTS[phase][model] = {"input": 0, "output": 0}
        
        cls.TOKEN_COUNTS[phase][model]["input"] += input_tokens
        cls.TOKEN_COUNTS[phase][model]["output"] += output_tokens
        
        cls.save_token_counts()

    @classmethod
    def get_token_counts(cls) -> Dict[str, Dict[str, Dict[str, int]]]:
        return cls.TOKEN_COUNTS

    @classmethod
    def _get_default_token_counts(cls) -> Dict[str, Dict[str, Dict[str, int]]]:
        default_counts = {"creation": {}, "edition": {}}
        for phase in ["creation", "edition"]:
            for model in cls.MODELS_PROVIDER_MAPPING.keys():
                default_counts[phase][model] = {"input": 0, "output": 0}
        return default_counts