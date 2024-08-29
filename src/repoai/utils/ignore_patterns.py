import fnmatch
import os
from pathlib import Path
from typing import List
from ..core.config_manager import ConfigManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class IgnorePatternHandler:
    def __init__(self, ignore_file: Path):
        """
        Args:
            ignore_file: Absolute path to ignore file
        """
        self.ignore_file = ignore_file
        self.ignore_patterns = []
        self.reload_patterns()

    def reload_patterns(self):
        if self.ignore_file.exists():
            with open(self.ignore_file, 'r') as f:
                content = f.read()
            if content:
                splited_content = content.split('\n')
                self.ignore_patterns = [line.strip() for line in splited_content if line.strip() and not line.startswith('#')]
        else:
            self.ignore_patterns = []

    def add_pattern(self, pattern: str):
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
            self._save_patterns()

    def remove_pattern(self, pattern: str):
        if pattern in self.ignore_patterns:
            self.ignore_patterns.remove(pattern)
            self._save_patterns()

    def _save_patterns(self):
        with open(self.ignore_file, 'w') as f:
            f.write('\n'.join(self.ignore_patterns))

    def get_patterns(self) -> List[str]:
        return self.ignore_patterns.copy()

    def is_ignored(self, file_path: str) -> bool:
        self.reload_patterns()  # Reload patterns before checking
        return should_ignore(file_path, self.ignore_patterns)

def should_ignore(file: str, patterns: List[str]) -> bool:
    file = file.rstrip(os.sep)
    file_parts = file.split(os.sep)
    
    for pattern in patterns:
        pattern = pattern.rstrip(os.sep)
        pattern_parts = pattern.split(os.sep)
        
        if match_pattern_parts(file_parts, pattern_parts):
            return True
    
    return False

def match_pattern_parts(file_parts: List[str], pattern_parts: List[str]) -> bool:
    if not pattern_parts:
        return True
    if not file_parts:
        return False
    
    if pattern_parts[0] == '**':
        for i in range(len(file_parts)):
            if match_pattern_parts(file_parts[i:], pattern_parts[1:]):
                return True
        return False
    
    if fnmatch.fnmatch(file_parts[0], pattern_parts[0]):
        return match_pattern_parts(file_parts[1:], pattern_parts[1:])
    
    return False