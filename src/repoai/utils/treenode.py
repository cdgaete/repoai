from pathlib import Path
import re
import fnmatch

class TreeNode:
    def __init__(self, path, parent=None, is_last=False):
        self.path = Path(str(path))
        self.parent = parent
        self.is_last = is_last
        self.depth = self.parent.depth + 1 if self.parent else 0

    @property
    def display_name(self):
        return f"{self.path.name}/" if self.path.is_dir() else self.path.name

class FileSystemTree:
    PREFIX_MIDDLE = '├──'
    PREFIX_LAST = '└──'
    PREFIX_PARENT_MIDDLE = '│   '
    PREFIX_PARENT_LAST = '    '

    @classmethod
    def generate(cls, root, criteria=None, ignore_file=None):
        root = Path(str(root))
        criteria = criteria or cls._default_criteria
        ignore_patterns = cls._load_ignore_patterns(ignore_file)

        def _generate_tree(path, parent=None, is_last=False):
            node = TreeNode(path, parent, is_last)
            yield node

            if path.is_dir():
                children = sorted(
                    [child for child in path.iterdir()
                     if criteria(child) and not cls._is_ignored(child, ignore_patterns, root)],
                    key=lambda s: str(s).lower()
                )

                last_index = len(children) - 1
                for index, child in enumerate(children):
                    yield from _generate_tree(child, node, index == last_index)

        return _generate_tree(root)

    @staticmethod
    def _default_criteria(path):
        return True

    @staticmethod
    def _load_ignore_patterns(ignore_file):
        if ignore_file:
            ignore_path = Path(ignore_file)
            if ignore_path.exists():
                with ignore_path.open('r') as f:
                    return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return []

    @staticmethod
    def _is_ignored(path, ignore_patterns, root):
        path_str = str(path.relative_to(root))
        return any(FileSystemTree._match_pattern(path_str, pattern) for pattern in ignore_patterns)

    @staticmethod
    def _match_pattern(path, pattern):
        # Convert .gitignore pattern to regex
        regex = fnmatch.translate(pattern)
        return re.match(regex, path) is not None

    @classmethod
    def display(cls, node):
        if node.parent is None:
            return node.display_name

        prefix = cls.PREFIX_LAST if node.is_last else cls.PREFIX_MIDDLE
        parts = [f"{prefix} {node.display_name}"]

        parent = node.parent
        while parent and parent.parent is not None:
            parts.append(
                cls.PREFIX_PARENT_LAST if parent.is_last else cls.PREFIX_PARENT_MIDDLE
            )
            parent = parent.parent

        return ''.join(reversed(parts))

