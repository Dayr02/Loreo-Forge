"""
Logging System for Loreo Forge
Provides structured logging with file and console output
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logger(name: str = "LoreoForge", log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    """
    Set up the application logger with file and console handlers
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler - with date in filename
    log_file = log_path / f"loreo_forge_{datetime.now().strftime('%Y%m%d')}.log"
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
    except OSError:
        file_handler = None
    if file_handler is not None:
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler - only INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Store global reference
    _logger = logger
    
    logger.info(f"Logger initialized: {name}")
    if file_handler is not None:
        logger.debug(f"Log file: {log_file}")
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the application logger or create one if it doesn't exist
    
    Args:
        name: Optional logger name (uses default if None)
        
    Returns:
        Logger instance
    """
    global _logger
    
    if _logger is None:
        _logger = setup_logger(name or "LoreoForge")
    
    if name and name != _logger.name:
        return logging.getLogger(name)
    
    return _logger


class LoggerMixin:
    """
    Mixin class that provides logging capabilities to any class
    
    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.log_info("This is an info message")
                self.log_error("This is an error")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)
    
    def log_info(self, message: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)
    
    def log_warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)
    
    def log_error(self, message: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)
    
    def log_critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)
    
    def log_exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)


# Convenience functions for module-level logging
def debug(message: str, *args, **kwargs):
    """Log debug message"""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Log info message"""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Log warning message"""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Log error message"""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Log critical message"""
    get_logger().critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """Log exception with traceback"""
    get_logger().exception(message, *args, **kwargs)
