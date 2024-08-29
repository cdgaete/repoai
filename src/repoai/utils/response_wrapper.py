from typing import Dict, Any, List, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ResponseRepoAI:
    def __init__(self, raw_response: Dict[str, Any]):
        self._raw_response = raw_response
        self._choices = raw_response.get('choices', [])
        self._first_choice = self._choices[0] if self._choices else {}

    @property
    def raw(self) -> Dict[str, Any]:
        """Return the raw response from the LLM."""
        return self._raw_response

    @property
    def content(self) -> str:
        """Extract the content from the LLM response."""
        return self._first_choice.get('message', {}).get('content', '')

    @property
    def role(self) -> str:
        """Extract the role from the LLM response."""
        return self._first_choice.get('message', {}).get('role', '')

    @property
    def finish_reason(self) -> str:
        """Get the finish reason of the response."""
        return self._first_choice.get('finish_reason', '')

    @property
    def model(self) -> str:
        """Get the model used for the response."""
        return self._raw_response.get('model', '')

    @property
    def usage(self) -> Dict[str, int]:
        """Get the token usage information."""
        return self._raw_response.get('usage', {})

    @property
    def id(self) -> str:
        """Get the response ID."""
        return self._raw_response.get('id', '')

    @property
    def created(self) -> int:
        """Get the creation timestamp."""
        return self._raw_response.get('created', 0)

    def get_content_by_index(self, index: int) -> Optional[str]:
        """Get content from a specific choice by index."""
        if 0 <= index < len(self._choices):
            return self._choices[index].get('message', {}).get('content')
        return None

    def get_role_by_index(self, index: int) -> Optional[str]:
        """Get role from a specific choice by index."""
        if 0 <= index < len(self._choices):
            return self._choices[index].get('message', {}).get('role')
        return None

    @property
    def all_contents(self) -> List[str]:
        """Get a list of all contents from all choices."""
        return [choice.get('message', {}).get('content', '') for choice in self._choices]

    @property
    def all_roles(self) -> List[str]:
        """Get a list of all roles from all choices."""
        return [choice.get('message', {}).get('role', '') for choice in self._choices]

    def __str__(self) -> str:
        """String representation of the response."""
        return f"ResponseRepoAI(model={self.model}, content_length={len(self.content)}, role={self.role})"

    def __repr__(self) -> str:
        """Detailed string representation of the response."""
        return f"ResponseRepoAI(id={self.id}, model={self.model}, choices={len(self._choices)}, usage={self.usage})"