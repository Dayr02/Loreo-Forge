"""
Custom exception classes for Loreo Forge
"""

class LoreoForgeException(Exception):
    """Base exception for Loreo Forge"""
    pass

class DatabaseException(LoreoForgeException):
    """Database-related errors"""
    pass

class AIException(LoreoForgeException):
    """AI generation errors"""
    pass

class OllamaConnectionError(AIException):
    """Ollama server connection failed"""
    pass

class ConfigurationError(LoreoForgeException):
    """Configuration file issues"""
    pass

class ExportException(LoreoForgeException):
    """Export operation failures"""
    pass