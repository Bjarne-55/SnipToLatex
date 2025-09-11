"""Custom exceptions used by AI request backends.

These exceptions allow the caller (capture pipeline) to present precise
error toasts to the user without parsing strings.
"""

class AiError(Exception):
    """Base class for AI-related errors."""


class ApiKeyMissing(AiError):
    """Raised when the required API key is not configured."""


class SdkMissing(AiError):
    """Raised when the SDK/library for a model is not installed."""


class EmptyResponse(AiError):
    """Raised when a model responds without any text content."""

class InvalidApiKey(AiError):
    """Raised when api key is invalid."""

