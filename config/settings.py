"""
Configuration Settings for Loreo Forge
Handles application settings, paths, and environment configuration

"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class Settings:
    """
    Application settings manager
    Loads from YAML files and environment variables
    """
    
    # Application metadata
    APP_NAME = "Loreo Forge"
    APP_VERSION = "1.0.0"
    
    # Default settings
    DEFAULT_FONT_FAMILY = "Segoe UI"  # Default system font
    DEFAULT_FONT_SIZE = 12
    DEFAULT_THEME = "Obsidian Night"
    DEFAULT_MODEL = "llama3.1:8b"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 8192  # INCREASED from 4096
    DEFAULT_CHAPTER_WORD_COUNT = 3000
    
    # Database settings
    DB_TIMEOUT = 30.0
    DB_ISOLATION_LEVEL = None  # Autocommit mode
    
    # AI settings - Ollama specific
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    # CRITICAL FIX: Dramatically increased timeouts
    # For 3000 words at ~20 tokens/sec = 150 seconds minimum
    # Added generous buffer for slower hardware and context processing
    OLLAMA_TIMEOUT = 1800  # 30 minutes (was 300s / 5 min)
    OLLAMA_CONNECTION_TIMEOUT = 10  # Connection timeout
    OLLAMA_READ_TIMEOUT = 1800  # Read timeout for long generations
    
    # Generation-specific timeouts (in seconds)
    SHORT_STORY_TIMEOUT = 900  # 15 minutes for short stories (500-1500 words)
    CHAPTER_TIMEOUT = 1800  # 30 minutes for chapters (1500-5000 words)
    LONG_CHAPTER_TIMEOUT = 3600  # 60 minutes for long chapters (5000+ words)
    
    MAX_RETRIES = 3  # Number of retry attempts for failed generations
    RETRY_BACKOFF = 2.0  # Exponential backoff multiplier
    
    # Streaming settings (NEW)
    ENABLE_STREAMING = True  # Use streaming for real-time feedback
    STREAM_CHUNK_SIZE = 1  # Process tokens as they arrive
    
    def __init__(self):
        """Initialize settings"""
        # Determine base directory
        self.BASE_DIR = Path(__file__).parent.parent.resolve()
        
        # Data directories
        self.DATA_DIR = self.BASE_DIR / "data"
        self.STORIES_DIR = self.DATA_DIR / "stories"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.ASSETS_DIR = self.BASE_DIR / "assets"
        
        # AI templates directory
        self.TEMPLATES_DIR = self.BASE_DIR / "ai" / "templates"
        
        # Ensure directories exist
        self._create_directories()
        
        # Load user settings
        self.user_settings = self._load_user_settings()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.DATA_DIR, self.STORIES_DIR, self.LOGS_DIR, self.TEMPLATES_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def ensure_directories(self):
        """
        Public method to ensure all directories exist
        Can be called by main.py or other modules
        """
        self._create_directories()
    
    def _load_user_settings(self) -> Dict[str, Any]:
        """Load user settings from YAML file"""
        settings_file = self.BASE_DIR / "config" / "user_settings.yaml"
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading user settings: {e}")
                return {}
        
        return {}
    
    def save_user_settings(self, settings_dict: Dict[str, Any]) -> bool:
        """Save user settings to YAML file"""
        settings_file = self.BASE_DIR / "config" / "user_settings.yaml"
        
        try:
            # Ensure config directory exists
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_file, 'w') as f:
                yaml.dump(settings_dict, f, default_flow_style=False)
            self.user_settings = settings_dict
            return True
        except Exception as e:
            print(f"Error saving user settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value with fallback to default
        
        Args:
            key: Setting key (can use dot notation, e.g., 'ui.theme')
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        # Check environment variable first
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        # Check user settings
        keys = key.split('.')
        value = self.user_settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a setting value
        
        Args:
            key: Setting key (can use dot notation)
            value: Value to set
            
        Returns:
            True if successful
        """
        keys = key.split('.')
        current = self.user_settings
        
        # Navigate to the nested location
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save to file
        return self.save_user_settings(self.user_settings)
    
    def get_timeout_for_word_count(self, word_count: int) -> int:
        """
        Calculate appropriate timeout based on target word count
        
        Args:
            word_count: Target word count
            
        Returns:
            Timeout in seconds
        """
        if word_count <= 1500:
            return self.SHORT_STORY_TIMEOUT
        elif word_count <= 5000:
            return self.CHAPTER_TIMEOUT
        else:
            return self.LONG_CHAPTER_TIMEOUT
    
    def get_story_db_path(self, story_id: int) -> Path:
        """
        Get the database path for a specific story
        
        Args:
            story_id: Story identifier
            
        Returns:
            Path to story database
        """
        return self.STORIES_DIR / f"story_{story_id}.db"
    
    def get_master_db_path(self) -> Path:
        """Get the master database path"""
        return self.DATA_DIR / "loreo_master.db"
    
    def get_log_path(self, log_name: str = "loreo_forge.log") -> Path:
        """Get log file path"""
        return self.LOGS_DIR / log_name
    
    # Convenience properties
    @property
    def theme(self) -> str:
        """Current theme"""
        return self.get('ui.theme', self.DEFAULT_THEME)
    
    @property
    def font_family(self) -> str:
        """Current font family"""
        return self.get('ui.font_family', self.DEFAULT_FONT_FAMILY)
    
    @property
    def font_size(self) -> int:
        """Current font size"""
        return self.get('ui.font_size', self.DEFAULT_FONT_SIZE)
    
    @property
    def default_model(self) -> str:
        """Default AI model"""
        return self.get('ai.default_model', self.DEFAULT_MODEL)
    
    @property
    def temperature(self) -> float:
        """AI temperature"""
        return self.get('ai.temperature', self.DEFAULT_TEMPERATURE)
    
    @property
    def max_tokens(self) -> int:
        """Max tokens for generation"""
        return self.get('ai.max_tokens', self.DEFAULT_MAX_TOKENS)
    
    @property
    def ollama_url(self) -> str:
        """Ollama server URL"""
        return self.get('ai.ollama_url', self.OLLAMA_BASE_URL)
    
    @property
    def auto_save(self) -> bool:
        """Auto-save enabled"""
        return self.get('general.auto_save', True)
    
    @property
    def auto_save_interval(self) -> int:
        """Auto-save interval in minutes"""
        return self.get('general.auto_save_interval', 5)


# Global settings instance
settings = Settings()