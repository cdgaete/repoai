DEFAULT_CONFIG = {
    "default_model": "anthropic/claude-3-5-sonnet-20240620",
    "log_level": "INFO",
    "log_file": "repoai.log",
    "max_log_file_size": 10485760,  # 10 MB
    "log_backup_count": 5,
    "max_commit_history": 10,
    "docker_compose_file": "docker-compose.yml",
    "global_token_usage_file": "global_token_usage.yaml",
    "project_token_usage_file": ".repoai/token_usage.yaml",
    "repoai_ignore_file": ".repoai/.repoaiignore",
    "prompt_cache_threshold": 20000,
    "plugin_dir": "plugins",
}