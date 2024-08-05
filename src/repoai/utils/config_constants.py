

DEFAULT_CONFIG = {
        "providers": {
            "anthropic": {
                "api_key": "",
                "api_host": None,
                "default_params": {
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            },
            "ollama": {
                "api_key": "",
                "api_host": "http://localhost:11434",
                "default_params": {}
            },
            "openai": {
                "api_key": "",
                "api_host": "https://api.openai.com/v1",
                "default_params": {
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            },
            "fireworks": {
                "api_key": "",
                "api_host": "https://api.fireworks.ai/inference/v1",
                "default_params": {
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            },
            "groq": {
                "api_key": "",
                "api_host": "https://api.groq.com/openai/v1",
                "default_params": {
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
            }
        },
        "task_model_mapping": {
            "PROJECT_DESCRIPTION_CHAT": "claude-3-5-sonnet-20240620",
            "PROJECT_CREATOR": "claude-3-5-sonnet-20240620",
            "FORMAT_DIRECTORY_STRUCTURE": "claude-3-haiku-20240307",
            "FORMAT_FILE_CONTENTS": "claude-3-5-sonnet-20240620",
            "EXPERT_CHAT": "claude-3-5-sonnet-20240620",
            "EDIT_FILE": "claude-3-5-sonnet-20240620"
        },
        "system_prompts": {
            "PROJECT_DESCRIPTION_CHAT_PROMPT": """You are an AI assistant helping to create a detailed project description. Your goal is to ask relevant questions and provide suggestions to help the user create a comprehensive project description. Consider the following aspects:

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
""",
            "PROJECT_CREATOR_PROMPT": """You are an AI assistant helping to create a new software project.
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
""",
            "FORMAT_DIRECTORY_STRUCTURE_PROMPT": """You are an AI assistant that extracts and formats directory structures.
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
8. Do not include any explanatory text or markdown formatting outside the <Tree> tags.
""",
            "FORMAT_FILE_CONTENTS_PROMPT": """
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
""",
            "EXPERT_CHAT_PROMPT": """You are an AI expert on coding and software design. Provide advice and suggestions based on the current project structure and files. 
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
File paths must be relative to the root directory. If there is a folder called 'context' in the root directory, this do not belong to the project, but contains useful information for the project.
""",
            "EDIT_FILE_PROMPT": """You are an expert on coding edition and software design. Provide the full content of a file based on the original file content and the suggested changes.
If the suggested changes represent the complete new file, provide the suggested content only. You must not add any additional comments or explanations to the content.
Return your response enclosed in triple backticks (```) and line breaks (`\n`) so: ```\n[content]\n```
"""
,
"CREATE_DOCKERFILES_PROMPT":"""Generate a Dockerfile and docker-compose.yml file for this application that allows for editing files and reflecting changes in the container. The Dockerfile should install dependencies as a non-root user and ensure proper permission ownership. The docker-compose.yml file should mount the current directory as a volume, excluding the node_modules directory (or equivalent) to prevent overriding installed dependencies. The container should run with a non-root user ID and group ID. Do not include version in compose file as is deprecated. If required, create, edit or delete other files to successfully perform this task."""
},
        "IGNORE_FILE": ".repoaiignore",
        "TOKEN_COUNTS_FILE": "token_counts.json",
        "LLM_RESPONSE_LOG": "llm_response_log.jsonl",
        "MAX_LOG_SIZE": 10 * 1024 * 1024,  # 10 MB
        "SAMPLE_SIZE_FOR_TEXT_DETECTION": 1024,
        "CHARDET_CONFIDENCE_THRESHOLD": 0.8,
        "PRINTABLE_RATIO_THRESHOLD": 0.7,
        "MAX_SUMMARY_ATTEMPTS": 6,
        "FILE_BATCH_SIZE": 3,
        "GITIGNORE_TEMPLATE": """
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

node_modules/

# Logs
*.log

# Environment variables
.env

# RepoAI specific
.repoai/
.gitignore
""",
        "ENV_TEMPLATE": """
# API Configuration
# ANTHROPIC_API_KEY=your_api_key_here
# DEFAULT_MODEL=claude-3-sonnet-20240229
# MAX_TOKENS=4000

# Logging Configuration
# LOG_LEVEL=INFO
""",
        "MODELS_PROVIDER_MAPPING": {
            "claude-3-haiku-20240307": "anthropic",
            "claude-3-5-sonnet-20240620": "anthropic",
            "llama3.1:latest": "ollama",
            "llama3-groq-tool-use:latest": "ollama",
            "gpt-4o-2024-05-13": "openai",
            "gpt-4o-mini-2024-07-18": "openai",
            "gpt-4-turbo-2024-04-09": "openai",
            "llama-3.1-405b-reasoning": "groq",
            "llama3-groq-70b-8192-tool-use-preview": "groq",
            "accounts/fireworks/models/llama-v3p1-405b-instruct": "fireworks",
            "accounts/fireworks/models/firefunction-v2": "fireworks",
        },
        "AVAILABLE_TOOLS": [
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
        ],
        "DEFAULT_IGNORE_PATTERNS": [
            "__pycache__/",
            "*/__pycache__/",
            ".git/",
            "*.pyc",
            ".DS_Store",
            ".idea/",
            ".vscode/",
            "node_modules/",
            "build/",
            "dist/",
            "secrets/",
            "env/",
            "venv/",
            ".repoai/",
            ".gitignore",
            ".env",

            # Add more patterns as needed
        ],
        "FILE_EXTENSION_TO_LANGUAGE": {
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
}