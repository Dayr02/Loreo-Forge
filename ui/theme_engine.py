"""
Theme Engine for Loreo Forge
Provides flexible, game-like visual themes
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt

from config.settings import settings
from utils.logger import LoggerMixin


class Theme:
    """Represents a single theme with colors and styling"""
    
    def __init__(self, name: str, colors: Dict[str, str], description: str = ""):
        """
        Initialize theme
        
        Args:
            name: Theme name
            colors: Dictionary of color definitions
            description: Theme description
        """
        self.name = name
        self.colors = colors
        self.description = description
    
    def get_color(self, key: str, default: str = "#000000") -> str:
        """Get color value by key"""
        return self.colors.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'colors': self.colors,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """Create theme from dictionary"""
        return cls(
            name=data.get('name', 'Unnamed'),
            colors=data.get('colors', {}),
            description=data.get('description', '')
        )


class ThemeEngine(LoggerMixin):
    """
    Manages application themes and styling
    Provides multiple pre-defined themes and custom theme support
    """
    
    def __init__(self):
        """Initialize theme engine"""
        self.current_theme: Optional[Theme] = None
        self.themes: Dict[str, Theme] = {}
        
        # Register built-in themes
        self._register_builtin_themes()
        
        # Load custom themes
        self._load_custom_themes()
        
        self.logger.info("ThemeEngine initialized")
    
    def _register_builtin_themes(self):
        """Register built-in themes"""
        
        # Theme 1: Obsidian Night (Default Dark)
        self.themes['Obsidian Night'] = Theme(
            name='Obsidian Night',
            colors={
                'background': '#1a1a1a',
                'foreground': '#e0e0e0',
                'primary': '#ff8c00',
                'secondary': '#4ecdc4',
                'accent': '#ffd700',
                'text': '#e0e0e0',
                'text_secondary': '#a0a0a0',
                'border': '#333333',
                'hover': '#2a2a2a',
                'selected': '#3a3a3a',
                'disabled': '#555555',
                'error': '#ff4444',
                'success': '#44ff44',
                'warning': '#ffaa00'
            },
            description='Modern dark theme with amber accents. Easy on the eyes for long writing sessions.'
        )
        
        # Theme 2: Parchment Legacy (Light Fantasy)
        self.themes['Parchment Legacy'] = Theme(
            name='Parchment Legacy',
            colors={
                'background': '#f4e8d8',
                'foreground': '#1a1a1a',
                'primary': '#5c4033',
                'secondary': '#2d5016',
                'accent': '#800020',
                'text': '#1a1a1a',
                'text_secondary': '#4a4a4a',
                'border': '#c8b89a',
                'hover': '#ebe0d0',
                'selected': '#e2d5c0',
                'disabled': '#b8a898',
                'error': '#cc0000',
                'success': '#006600',
                'warning': '#cc8800'
            },
            description='Classic light theme with aged paper aesthetic. Perfect for a literary feel.'
        )
        
        # Theme 3: Cyber Neon (Futuristic)
        self.themes['Cyber Neon'] = Theme(
            name='Cyber Neon',
            colors={
                'background': '#0a0e27',
                'foreground': '#ffffff',
                'primary': '#00ffff',
                'secondary': '#ff00ff',
                'accent': '#00ff00',
                'text': '#ffffff',
                'text_secondary': '#cccccc',
                'border': '#1a1e37',
                'hover': '#1a1e47',
                'selected': '#2a2e57',
                'disabled': '#444466',
                'error': '#ff0066',
                'success': '#00ff66',
                'warning': '#ffff00'
            },
            description='High-tech theme with electric colors and glow effects.'
        )
        
        # Theme 4: Forest Haven (Nature)
        self.themes['Forest Haven'] = Theme(
            name='Forest Haven',
            colors={
                'background': '#1b3a26',
                'foreground': '#f5f5dc',
                'primary': '#7cb342',
                'secondary': '#8d6e63',
                'accent': '#87ceeb',
                'text': '#f5f5dc',
                'text_secondary': '#c5c5ac',
                'border': '#2b4a36',
                'hover': '#2b4a46',
                'selected': '#3b5a56',
                'disabled': '#4b6a66',
                'error': '#ff6b6b',
                'success': '#90ee90',
                'warning': '#ffd700'
            },
            description='Calm nature theme with earthy tones and forest greens.'
        )
        
        self.logger.info(f"Registered {len(self.themes)} built-in themes")

        # Theme 5: Arcane Twilight (Fantasy Focus)
        self.themes['Arcane Twilight'] = Theme(
            name='Arcane Twilight',
            colors={
                'background': '#14121a',
                'foreground': '#e6e1f0',
                'primary': '#9b5de5',
                'secondary': '#00bbf9',
                'accent': '#f15bb5',
                'text': '#e6e1f0',
                'text_secondary': '#b7aecf',
                'border': '#2a2636',
                'hover': '#1e1b28',
                'selected': '#2f2a40',
                'disabled': '#5c5870',
                'error': '#ff5c5c',
                'success': '#4fd1a1',
                'warning': '#f6c177'
            },
            description='Mystical dark theme with vibrant arcane accents, perfect for fantasy and magic-heavy worlds.'
        )

        # Theme 6: Steel Horizon (Neutral / Professional)
        self.themes['Steel Horizon'] = Theme(
            name='Steel Horizon',
            colors={
                'background': '#202428',
                'foreground': '#e4e7eb',
                'primary': '#4c8bf5',
                'secondary': '#6c757d',
                'accent': '#17c3b2',
                'text': '#e4e7eb',
                'text_secondary': '#b0b6bd',
                'border': '#343a40',
                'hover': '#2a2f34',
                'selected': '#3a4046',
                'disabled': '#6c6f73',
                'error': '#e5533d',
                'success': '#4caf50',
                'warning': '#f0ad4e'
            },
            description='Clean, modern theme with cool tones for focused planning and technical world-building.'
        )

        # Theme 7: Emberforge (Dark with Strong Contrast)
        self.themes['Emberforge'] = Theme(
            name='Emberforge',
            colors={
                'background': '#120d0b',
                'foreground': '#f2e6dc',
                'primary': '#e4572e',
                'secondary': '#f3a712',
                'accent': '#9cdb43',
                'text': '#f2e6dc',
                'text_secondary': '#cbb9a9',
                'border': '#2a1f1a',
                'hover': '#1d1512',
                'selected': '#33241f',
                'disabled': '#6a5a52',
                'error': '#ff3b3b',
                'success': '#7bd389',
                'warning': '#ffb000'
            },
            description='High-contrast molten tones inspired by fire and creation. Excellent for dramatic writing.'
        )

        # Theme 8: Verdant Chronicle (Nature / Worldbuilding)
        self.themes['Verdant Chronicle'] = Theme(
            name='Verdant Chronicle',
            colors={
                'background': '#18201a',
                'foreground': '#e8f0e8',
                'primary': '#6ab04c',
                'secondary': '#4d908e',
                'accent': '#f9c74f',
                'text': '#e8f0e8',
                'text_secondary': '#b7c7b7',
                'border': '#2b3a2e',
                'hover': '#223026',
                'selected': '#2f4234',
                'disabled': '#5f6f63',
                'error': '#d62828',
                'success': '#80ed99',
                'warning': '#f9844a'
            },
            description='Earthy greens and warm accents designed for immersive world and ecosystem design.'
        )

        # Theme 9: Void Ash
        self.themes['Void Ash'] = Theme(
            name='Void Ash',
            colors={
                'background': '#121212',
                'foreground': '#d8d8d8',
                'primary': '#9e9e9e',
                'secondary': '#6c757d',
                'accent': '#b388ff',
                'text': '#d8d8d8',
                'text_secondary': '#9a9a9a',
                'border': '#242424',
                'hover': '#1e1e1e',
                'selected': '#2c2c2c',
                'disabled': '#5a5a5a',
                'error': '#ff5252',
                'success': '#69f0ae',
                'warning': '#ffd740'
            },
            description='Ultra-dark minimalist theme with soft violet highlights. Ideal for distraction-free writing.'
        )

        # Theme 10: Blood Moon
        self.themes['Blood Moon'] = Theme(
            name='Blood Moon',
            colors={
                'background': '#160b0b',
                'foreground': '#f0dcdc',
                'primary': '#b11226',
                'secondary': '#6a040f',
                'accent': '#e85d04',
                'text': '#f0dcdc',
                'text_secondary': '#c7a1a1',
                'border': '#2a1414',
                'hover': '#201010',
                'selected': '#331818',
                'disabled': '#6b4b4b',
                'error': '#ff2e2e',
                'success': '#8fd694',
                'warning': '#ffba08'
            },
            description='Dark crimson theme inspired by eclipses and tragedy. Perfect for grim, dramatic narratives.'
        )

        # Theme 11: Arcane Obscura
        self.themes['Arcane Obscura'] = Theme(
            name='Arcane Obscura',
            colors={
                'background': '#0f0d16',
                'foreground': '#e6e1f0',
                'primary': '#7b5cff',
                'secondary': '#4ea8de',
                'accent': '#f72585',
                'text': '#e6e1f0',
                'text_secondary': '#b8b1d6',
                'border': '#221f33',
                'hover': '#181426',
                'selected': '#2a2440',
                'disabled': '#5c5773',
                'error': '#ff5c8a',
                'success': '#4fd1a1',
                'warning': '#ffd166'
            },
            description='Deep arcane purples and blues designed for magic-heavy and high-fantasy storytelling.'
        )

        # Theme 12: Iron Dusk
        self.themes['Iron Dusk'] = Theme(
            name='Iron Dusk',
            colors={
                'background': '#181a1f',
                'foreground': '#e4e7eb',
                'primary': '#5c7cfa',
                'secondary': '#868e96',
                'accent': '#51cf66',
                'text': '#e4e7eb',
                'text_secondary': '#b0b6bd',
                'border': '#2c2f36',
                'hover': '#22252b',
                'selected': '#343840',
                'disabled': '#6c7078',
                'error': '#fa5252',
                'success': '#69db7c',
                'warning': '#fcc419'
            },
            description='Cold industrial tones with clean contrast. Great for structured plotting and long sessions.'
        )

        # Theme 13: Abyssal Teal
        self.themes['Abyssal Teal'] = Theme(
            name='Abyssal Teal',
            colors={
                'background': '#0d1b1e',
                'foreground': '#e0f2f1',
                'primary': '#00b4d8',
                'secondary': '#0077b6',
                'accent': '#90dbf4',
                'text': '#e0f2f1',
                'text_secondary': '#a8cfcf',
                'border': '#1c2f33',
                'hover': '#132529',
                'selected': '#1f3a3f',
                'disabled': '#4f6b6f',
                'error': '#ef476f',
                'success': '#06d6a0',
                'warning': '#ffd166'
            },
            description='Deep oceanic blues and teals for calm, immersive world-building and lore writing.'
        )
    
    def _load_custom_themes(self):
        """Load custom themes from themes directory"""
        themes_dir = settings.ASSETS_DIR / "themes"
        
        if not themes_dir.exists():
            return
        
        for theme_file in themes_dir.glob("*.json"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    theme = Theme.from_dict(theme_data)
                    self.themes[theme.name] = theme
                    self.logger.debug(f"Loaded custom theme: {theme.name}")
            except Exception as e:
                self.logger.error(f"Failed to load theme from {theme_file}: {e}")
    
    # ========================================================================
    # THEME MANAGEMENT
    # ========================================================================
    
    def load_theme(self, theme_name: str) -> bool:
        """
        Apply theme to application
        
        Args:
            theme_name: Name of theme to load
            
        Returns:
            True if successful, False otherwise
        """
        if theme_name not in self.themes:
            self.logger.error(f"Theme '{theme_name}' not found")
            return False
        
        theme = self.themes[theme_name]
        self.current_theme = theme
        
        # Generate and apply stylesheet
        stylesheet = self._generate_stylesheet(theme)
        QApplication.instance().setStyleSheet(stylesheet)
        
        # Save preference
        settings.set('ui.theme', theme_name)
        
        self.logger.info(f"Applied theme: {theme_name}")
        return True
    
    def get_available_themes(self) -> list:
        """
        Get list of available theme names
        
        Returns:
            List of theme names
        """
        return list(self.themes.keys())
    
    def get_current_theme(self) -> Optional[Theme]:
        """Get currently active theme"""
        return self.current_theme
    
    def create_custom_theme(
        self, 
        name: str, 
        colors: Dict[str, str],
        description: str = ""
    ) -> bool:
        """
        Create a custom theme
        
        Args:
            name: Theme name
            colors: Color definitions
            description: Theme description
            
        Returns:
            True if successful
        """
        theme = Theme(name, colors, description)
        self.themes[name] = theme
        
        # Save to file
        try:
            themes_dir = settings.ASSETS_DIR / "themes"
            themes_dir.mkdir(parents=True, exist_ok=True)
            
            theme_file = themes_dir / f"{name.lower().replace(' ', '_')}.json"
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(theme.to_dict(), f, indent=2)
            
            self.logger.info(f"Created custom theme: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save custom theme: {e}")
            return False
    
    def export_theme(self, theme_name: str, filepath: Path) -> bool:
        """
        Export theme to file
        
        Args:
            theme_name: Name of theme to export
            filepath: Destination file path
            
        Returns:
            True if successful
        """
        if theme_name not in self.themes:
            return False
        
        try:
            theme = self.themes[theme_name]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(theme.to_dict(), f, indent=2)
            
            self.logger.info(f"Exported theme '{theme_name}' to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export theme: {e}")
            return False
    
    def import_theme(self, filepath: Path) -> bool:
        """
        Import theme from file
        
        Args:
            filepath: Path to theme file
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
                theme = Theme.from_dict(theme_data)
                self.themes[theme.name] = theme
            
            self.logger.info(f"Imported theme: {theme.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import theme: {e}")
            return False
    
    # ========================================================================
    # STYLESHEET GENERATION
    # ========================================================================
    
    def _generate_stylesheet(self, theme: Theme) -> str:
        """
        Generate QSS stylesheet from theme
        
        Args:
            theme: Theme to generate stylesheet for
            
        Returns:
            QSS stylesheet string
        """
        qss = f"""
        /* Global Styles */
        QWidget {{
            background-color: {theme.get_color('background')};
            color: {theme.get_color('text')};
            font-family: {settings.DEFAULT_FONT_FAMILY};
            font-size: {settings.DEFAULT_FONT_SIZE}pt;
        }}
        
        /* Main Window */
        QMainWindow {{
            background-color: {theme.get_color('background')};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {theme.get_color('primary')};
            color: {theme.get_color('background')};
            border: 2px solid {theme.get_color('primary')};
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {theme.get_color('accent')};
            border-color: {theme.get_color('accent')};
        }}
        
        QPushButton:pressed {{
            background-color: {theme.get_color('secondary')};
            border-color: {theme.get_color('secondary')};
        }}
        
        QPushButton:disabled {{
            background-color: {theme.get_color('disabled')};
            border-color: {theme.get_color('disabled')};
            color: {theme.get_color('text_secondary')};
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {theme.get_color('hover')};
            color: {theme.get_color('text')};
            border: 2px solid {theme.get_color('border')};
            border-radius: 4px;
            padding: 6px;
            selection-background-color: {theme.get_color('selected')};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {theme.get_color('primary')};
        }}
        
        /* Combo Boxes */
        QComboBox {{
            background-color: {theme.get_color('hover')};
            color: {theme.get_color('text')};
            border: 2px solid {theme.get_color('border')};
            border-radius: 4px;
            padding: 6px;
        }}
        
        QComboBox:hover {{
            border-color: {theme.get_color('primary')};
        }}
        
        QComboBox::drop-down {{
            border: none;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {theme.get_color('hover')};
            color: {theme.get_color('text')};
            selection-background-color: {theme.get_color('selected')};
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {theme.get_color('background')};
            width: 12px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {theme.get_color('border')};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {theme.get_color('primary')};
        }}
        
        QScrollBar:horizontal {{
            background-color: {theme.get_color('background')};
            height: 12px;
            margin: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {theme.get_color('border')};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {theme.get_color('primary')};
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {theme.get_color('background')};
            color: {theme.get_color('text')};
            border-bottom: 1px solid {theme.get_color('border')};
        }}
        
        QMenuBar::item:selected {{
            background-color: {theme.get_color('hover')};
        }}
        
        QMenu {{
            background-color: {theme.get_color('hover')};
            color: {theme.get_color('text')};
            border: 1px solid {theme.get_color('border')};
        }}
        
        QMenu::item:selected {{
            background-color: {theme.get_color('selected')};
        }}
        
        /* Tool Bar */
        QToolBar {{
            background-color: {theme.get_color('background')};
            border-bottom: 1px solid {theme.get_color('border')};
            padding: 4px;
        }}
        
        QToolButton {{
            background-color: transparent;
            color: {theme.get_color('text')};
            border: none;
            border-radius: 4px;
            padding: 6px;
        }}
        
        QToolButton:hover {{
            background-color: {theme.get_color('hover')};
        }}
        
        QToolButton:pressed {{
            background-color: {theme.get_color('selected')};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {theme.get_color('background')};
            color: {theme.get_color('text')};
            border-top: 1px solid {theme.get_color('border')};
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {theme.get_color('border')};
            border-radius: 4px;
        }}
        
        QTabBar::tab {{
            background-color: {theme.get_color('hover')};
            color: {theme.get_color('text')};
            border: 1px solid {theme.get_color('border')};
            padding: 8px 16px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {theme.get_color('primary')};
            color: {theme.get_color('background')};
        }}
        
        QTabBar::tab:hover {{
            background-color: {theme.get_color('selected')};
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {theme.get_color('hover')};
            border: 2px solid {theme.get_color('border')};
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {theme.get_color('primary')};
        }}
        
        /* List Widget */
        QListWidget {{
            background-color: {theme.get_color('hover')};
            color: {theme.get_color('text')};
            border: 2px solid {theme.get_color('border')};
            border-radius: 4px;
        }}
        
        QListWidget::item:selected {{
            background-color: {theme.get_color('selected')};
        }}
        
        QListWidget::item:hover {{
            background-color: {theme.get_color('hover')};
        }}
        
        /* Table Widget */
        QTableWidget {{
            background-color: {theme.get_color('hover')};
            color: {theme.get_color('text')};
            gridline-color: {theme.get_color('border')};
            border: 2px solid {theme.get_color('border')};
        }}
        
        QTableWidget::item:selected {{
            background-color: {theme.get_color('selected')};
        }}
        
        QHeaderView::section {{
            background-color: {theme.get_color('background')};
            color: {theme.get_color('text')};
            border: 1px solid {theme.get_color('border')};
            padding: 6px;
        }}
        
        /* Labels */
        QLabel {{
            color: {theme.get_color('text')};
            background-color: transparent;
        }}
        
        /* Group Box */
        QGroupBox {{
            border: 2px solid {theme.get_color('border')};
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        
        QGroupBox::title {{
            color: {theme.get_color('primary')};
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
        }}
        
        /* Slider */
        QSlider::groove:horizontal {{
            background: {theme.get_color('hover')};
            height: 8px;
            border-radius: 4px;
        }}
        
        QSlider::handle:horizontal {{
            background: {theme.get_color('primary')};
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {theme.get_color('accent')};
        }}
        
        /* Spin Box */
        QSpinBox {{
            background-color: {theme.get_color('hover')};
            color: {theme.get_color('text')};
            border: 2px solid {theme.get_color('border')};
            border-radius: 4px;
            padding: 6px;
        }}
        
        /* Check Box */
        QCheckBox {{
            color: {theme.get_color('text')};
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {theme.get_color('border')};
            border-radius: 4px;
            background-color: {theme.get_color('hover')};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {theme.get_color('primary')};
        }}
        
        /* Radio Button */
        QRadioButton {{
            color: {theme.get_color('text')};
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {theme.get_color('border')};
            border-radius: 9px;
            background-color: {theme.get_color('hover')};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {theme.get_color('primary')};
        }}
        """
        
        return qss
    
    def apply_stylesheet(self):
        """Apply current theme stylesheet"""
        if self.current_theme:
            stylesheet = self._generate_stylesheet(self.current_theme)
            QApplication.instance().setStyleSheet(stylesheet)
    
    def set_font_family(self, family: str):
        """
        Change application font family
        
        Args:
            family: Font family name
        """
        settings.set('ui.font_family', family)
        font = QApplication.font()
        font.setFamily(family)
        QApplication.setFont(font)
        self.apply_stylesheet()
    
    def set_font_size(self, size: int):
        """
        Adjust text size globally
        
        Args:
            size: Font size in points
        """
        settings.set('ui.font_size', size)
        font = QApplication.font()
        font.setPointSize(size)
        QApplication.setFont(font)
        self.apply_stylesheet()


# Global theme engine instance
theme_engine = ThemeEngine()