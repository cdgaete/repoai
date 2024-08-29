from typing import Literal
import json
from pathlib import Path
import appdirs


class ConfigManager:
    CONFIG_FILE = 'repoai_config.json'
    REPOAI_DIR = ".repoai"

    def __init__(self):
        self.global_config = {}
        self.project_config = {}
        self.config_dir = Path(appdirs.user_config_dir("repoai"))
        self.user_dir = Path(appdirs.user_data_dir("repoai"))
        self.load_global_config()
    
    def load_global_config(self):
        config_file = self.config_dir / self.CONFIG_FILE

        if config_file.exists():
            with open(config_file, 'r') as f:
                self.global_config = json.load(f)
        else:
            self.set_default_global_config()
    
    def save_global_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / self.CONFIG_FILE
        with open(config_file, 'w') as f:
            json.dump(self.global_config, f, indent=2)

    def get(self, key, default=None):
        return self.project_config.get(key, self.global_config.get(key, default))

    def set(self, key, value, is_global=False):
        if is_global:
            self.global_config[key] = value
            self.save_global_config()
        else:
            self.project_config[key] = value

    def load_project_config(self, project_path:Path):
        config_file_path = project_path / self.REPOAI_DIR / self.CONFIG_FILE
        if config_file_path.exists():
            with open(config_file_path, 'r') as f:
                self.project_config = json.load(f)
        else:
            self.project_config = {}

    def save_project_config(self, project_path:Path):
        config_content = json.dumps(self.project_config, indent=2)
        config_file_path = project_path / self.REPOAI_DIR / self.CONFIG_FILE

        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w') as f:
            f.write(config_content)

    def set_default_global_config(self):
        self.global_config = {
            'default_model': 'ollama/llama3.1',
            'log_level': 'INFO',
            'log_file': str(self.user_dir / 'repoai.log'),
            'max_log_file_size': 10 * 1024 * 1024,  # 10 MB
            'log_backup_count': 5,
            'max_commit_history': 10,
            'docker_compose_file': 'docker-compose.yml',
            'global_token_usage_file': str(self.user_dir / 'global_token_usage.json'),
            'project_token_usage_file': str(Path(self.REPOAI_DIR) /'token_usage.json'),
            'repoai_ignore_file': str(Path(self.REPOAI_DIR) / '.repoaiignore'),
            'prompt_cache_threshold': 20000,
            'plugin_dir': str(self.user_dir / 'plugins'),
            'templates': {
                    'gitignore': """
# RepoAI
.repoai/

# Environments
.env
.venv
env/
ENV/
env.bak/
venv.bak/

# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.venv/
.pytest_cache/

# node
node_modules/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
""",
                    'repoaiignore': """
.repoai/

# Ignore version control directories
.git/
**/.git/
.svn/
.hg/
.gitignore

# Ignore build outputs
build/
**/build/
dist/
**/dist/
*.egg-info/
*/*.egg-info/

# Ignore log files
*.log

# Ignore environment files
.env
env/

# Python
__pycache__/
**/__pycache__/
.pytest_cache/
**/.pytest_cache/
.cache/
*.py[cod]
*$py.class
venv/
**/venv/
.venv/
**/.venv/

# node
node_modules/
**/node_modules/
package-lock.json
**/package-lock.json

# Ignore IDE specific files
.vscode/
.idea/
*.swp
*.swo

# Ignore OS generated files
.DS_Store
Thumbs.db
"""
}
        }
        self.save_global_config()
