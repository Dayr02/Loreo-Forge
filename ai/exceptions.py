"""
Custom exception classes for AI operations
"""


class AIException(Exception):
    """Base exception for AI-related errors"""
    pass


class OllamaConnectionError(AIException):
    """Raised when connection to Ollama server fails"""
    pass


class ModelNotFoundError(AIException):
    """Raised when requested model is not available"""
    pass


class GenerationTimeoutError(AIException):
    """Raised when generation exceeds timeout limit"""
    pass


class ContextLengthExceededError(AIException):
    """Raised when context exceeds model's maximum token limit"""
    pass


class InvalidPromptError(AIException):
    """Raised when prompt validation fails"""
    pass


class GenerationError(AIException):
    """Raised when generation fails for unknown reasons"""
    pass