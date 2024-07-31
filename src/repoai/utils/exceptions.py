# src/repoai/utils/exceptions.py

class OverloadedError(Exception):
    """Exception raised when the AI service is overloaded."""
    pass

class ConnectionError(Exception):
    """Exception raised when there's a connection error to the AI service."""
    pass

class FileOperationError(Exception):
    """Base exception for file operations."""
    pass

class FileEditError(FileOperationError):
    """Exception raised when there's an error editing a file."""
    pass

class FileCreateError(FileOperationError):
    """Exception raised when there's an error creating a file."""
    pass

class FileDeleteError(FileOperationError):
    """Exception raised when there's an error deleting a file."""
    pass
