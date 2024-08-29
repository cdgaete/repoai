from pathlib import Path
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TreeNode:
    def __init__(self, path, is_last=False):
        self.path = Path(path)
        self.is_last = is_last
        self.children = []

    @property
    def display_name(self):
        return self.path.name

class FileSystemTree:
    PREFIX_MIDDLE = '├── '
    PREFIX_LAST = '└── '
    PREFIX_VERTICAL = '│   '
    PREFIX_SPACE = '    '

    @classmethod
    def generate(cls, filtered_files):
        root = Path(".")
        root_node = TreeNode(root)

        for file_path in sorted(filtered_files):
            path = Path(file_path)
            relative_path = path.relative_to(root)
            cls._add_path_to_tree(root_node, relative_path)

        cls._set_last_flags(root_node)
        return root_node

    @classmethod
    def _add_path_to_tree(cls, root_node, relative_path):
        current_node = root_node
        parts = relative_path.parts

        for i, part in enumerate(parts):
            child_node = cls._find_or_create_child(current_node, part)
            current_node = child_node

    @classmethod
    def _find_or_create_child(cls, parent_node, child_name):
        for child in parent_node.children:
            if child.path.name == child_name:
                return child

        child_path = parent_node.path / child_name
        child_node = TreeNode(child_path)
        parent_node.children.append(child_node)
        return child_node

    @classmethod
    def _set_last_flags(cls, node):
        if node.children:
            for child in node.children[:-1]:
                child.is_last = False
                cls._set_last_flags(child)
            node.children[-1].is_last = True
            cls._set_last_flags(node.children[-1])

    @classmethod
    def display(cls, node, prefix=""):
        lines = [node.display_name]

        def _inner_display(node, prefix=""):
            for child in node.children[:-1]:
                lines.append(f"{prefix}{cls.PREFIX_MIDDLE}{child.display_name}")
                if child.children:
                    _inner_display(child, prefix + cls.PREFIX_VERTICAL)

            if node.children:
                last_child = node.children[-1]
                lines.append(f"{prefix}{cls.PREFIX_LAST}{last_child.display_name}")
                if last_child.children:
                    _inner_display(last_child, prefix + cls.PREFIX_SPACE)

        _inner_display(node)
        return lines