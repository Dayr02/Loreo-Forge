# ============================================================================
# ai/__init__.py
# ============================================================================
"""AI integration layer"""
from .exceptions import (
    AIException,
    OllamaConnectionError,
    ModelNotFoundError,
    GenerationTimeoutError,
    ContextLengthExceededError,
    InvalidPromptError,
    GenerationError
)
from .ollama_client import OllamaClient, ollama_client
from .prompt_builder import PromptBuilder, prompt_builder
from .context_manager import ContextManager, context_manager

__all__ = [
    'AIException',
    'OllamaConnectionError',
    'ModelNotFoundError',
    'GenerationTimeoutError',
    'ContextLengthExceededError',
    'InvalidPromptError',
    'GenerationError',
    'OllamaClient',
    'ollama_client',
    'PromptBuilder',
    'prompt_builder',
    'ContextManager',
    'context_manager'
]