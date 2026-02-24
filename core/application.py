"""
Application Core
Main QApplication wrapper with theme and initialization
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from config.settings import settings
from ui.theme_engine import theme_engine
from utils.logger import LoggerMixin


class LoreoForgeApp(QApplication, LoggerMixin):
    """
    Main application class
    Handles initialization, theming, and global state
    """
    
    def __init__(self, argv):
        super().__init__(argv)
        
        self.main_window = None
        
        # Set application metadata
        self.setApplicationName(settings.APP_NAME)
        self.setApplicationVersion(settings.APP_VERSION)
        self.setOrganizationName("Loreo Forge")
        
        # Initialize application
        self._initialize()
        
        self.log_info("LoreoForgeApp initialized")
    
    def _initialize(self):
        """Initialize application settings and theme"""
        # Set default font
        font = QFont(settings.font_family, settings.font_size)
        self.setFont(font)
        
        # CRITICAL: Load Obsidian Night theme by default
        theme_name = settings.get('ui.theme', 'Obsidian Night')
        
        # Force Obsidian Night if not set
        if not theme_name or theme_name not in theme_engine.get_available_themes():
            theme_name = 'Obsidian Night'
            settings.set('ui.theme', theme_name)
        
        # Apply theme
        success = theme_engine.load_theme(theme_name)
        
        if success:
            self.log_info(f"Applied theme: {theme_name}")
        else:
            self.log_warning(f"Failed to load theme '{theme_name}', using default")
            theme_engine.load_theme('Obsidian Night')
        
        # Enable high DPI scaling
        self.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        self.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    def _setup_fonts(self):
        """Setup application fonts"""
        font_family = settings.get('ui.font_family', settings.DEFAULT_FONT_FAMILY)
        font_size = settings.get('ui.font_size', settings.DEFAULT_FONT_SIZE)
        
        app_font = QFont(font_family, font_size)
        self.setFont(app_font)
        
        self.logger.debug(f"Application font set to {font_family} {font_size}pt")

    def set_main_window(self, window):
        """Set the main application window"""
        self.main_window = window
        self.log_info("Main window set")
    
    def get_main_window(self):
        """Get the main application window"""
        return self.main_window
    

    
