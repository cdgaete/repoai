# src/repoai/utils/context_managers.py

from contextlib import contextmanager
from threading import local

class FeatureContext:
    _thread_local = local()

    @classmethod
    def get_current(cls):
        if not hasattr(cls._thread_local, "stack"):
            cls._thread_local.stack = [{"use_tools": False}]
        return cls._thread_local.stack[-1]

    @classmethod
    @contextmanager
    def use_features(cls, use_tools=False):
        current = cls.get_current().copy()
        current.update({"use_tools": use_tools})
        cls._thread_local.stack.append(current)
        try:
            yield
        finally:
            cls._thread_local.stack.pop()

def use_tools():
    return FeatureContext.get_current()["use_tools"]
