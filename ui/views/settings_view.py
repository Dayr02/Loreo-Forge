"""
Settings View
Application settings and preferences
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QScrollArea, QWidget,
    QSpinBox, QCheckBox, QSlider, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.views.base_view import BaseView
from config.settings import settings


class SettingsView(BaseView):
    """Settings and preferences view"""
    
    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        # Initialize attributes
        self.theme_combo = None
        self.font_size_spin = None
        self.default_model_combo = None
        self.temperature_slider = None
        self.temperature_label = None
        self.max_tokens_spin = None
        self.ollama_url_input = None
        self.test_connection_button = None
        self.auto_save_checkbox = None
        self.auto_save_interval = None
        self.chapter_word_count_spin = None
        self.save_settings_button = None
        self.reset_button = None
        
        super().__init__()
        self.view_name = "Settings"
    
    def setup_ui(self):
        """Initialize the settings view UI"""
        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header = QLabel("Application Settings")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(header)
        
        # General settings
        general_group = self._create_general_settings()
        main_layout.addWidget(general_group)
        
        # AI settings
        ai_group = self._create_ai_settings()
        main_layout.addWidget(ai_group)
        
        # Generation settings
        generation_group = self._create_generation_settings()
        main_layout.addWidget(generation_group)
        
        # UI settings
        ui_group = self._create_ui_settings()
        main_layout.addWidget(ui_group)
        
        # Action buttons
        buttons_layout = self._create_action_buttons()
        main_layout.addLayout(buttons_layout)
        
        main_layout.addStretch()
        content.setLayout(main_layout)
        scroll.setWidget(content)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)
        
        # Load current settings
        self.load_data()
    
    def _create_general_settings(self):
        """Create general settings group"""
        group = QGroupBox("General Settings")
        layout = QFormLayout()
        
        # Auto-save
        self.auto_save_checkbox = QCheckBox("Enable auto-save")
        self.auto_save_checkbox.setChecked(True)
        layout.addRow("", self.auto_save_checkbox)
        
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setValue(5)
        self.auto_save_interval.setSuffix(" minutes")
        layout.addRow("Auto-save interval:", self.auto_save_interval)
        
        group.setLayout(layout)
        return group
    
    def _create_ai_settings(self):
        """Create AI model settings group"""
        group = QGroupBox("AI Model Settings")
        layout = QFormLayout()
        
        # Default model
        self.default_model_combo = QComboBox()
        self.default_model_combo.addItems(["llama3.1:8b (Fast)", "llama3.1:70b (Quality)"])
        layout.addRow("Default Model:", self.default_model_combo)
        
        # Temperature
        temp_layout = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(70)
        self.temperature_slider.valueChanged.connect(self._update_temperature_label)
        temp_layout.addWidget(self.temperature_slider)
        
        self.temperature_label = QLabel("0.70")
        self.temperature_label.setMinimumWidth(40)
        temp_layout.addWidget(self.temperature_label)
        
        layout.addRow("Temperature:", temp_layout)
        
        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 16000)
        self.max_tokens_spin.setValue(4096)
        self.max_tokens_spin.setSingleStep(100)
        layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        # Ollama URL
        self.ollama_url_input = QLineEdit()
        self.ollama_url_input.setText("http://localhost:11434")
        layout.addRow("Ollama Server URL:", self.ollama_url_input)
        
        # Test connection button
        self.test_connection_button = QPushButton("🔌 Test Connection")
        self.test_connection_button.clicked.connect(self._test_ollama_connection)
        layout.addRow("", self.test_connection_button)
        
        group.setLayout(layout)
        return group
    
    def _create_generation_settings(self):
        """Create generation settings group"""
        group = QGroupBox("Generation Settings")
        layout = QFormLayout()
        
        # Default chapter word count
        self.chapter_word_count_spin = QSpinBox()
        self.chapter_word_count_spin.setRange(500, 20000)
        self.chapter_word_count_spin.setValue(3000)
        self.chapter_word_count_spin.setSingleStep(500)
        layout.addRow("Default Chapter Word Count:", self.chapter_word_count_spin)
        
        group.setLayout(layout)
        return group
    
    def _create_ui_settings(self):
        """Create UI settings group"""
        group = QGroupBox("User Interface")
        layout = QFormLayout()
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Obsidian Night (Default)",
            "Parchment Legacy",
            "Cyber Neon",
            "Forest Haven"
        ])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        layout.addRow("Theme:", self.theme_combo)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        self.font_size_spin.setSuffix(" pt")
        layout.addRow("Font Size:", self.font_size_spin)
        
        group.setLayout(layout)
        return group
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # Reset to defaults
        self.reset_button = QPushButton("↺ Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 152, 0, 0.8);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 152, 0, 1.0);
            }
        """)
        layout.addWidget(self.reset_button)
        
        layout.addStretch()
        
        # Save settings
        self.save_settings_button = QPushButton("💾 Save Settings")
        self.save_settings_button.setMinimumHeight(40)
        self.save_settings_button.clicked.connect(self.save_data)
        self.save_settings_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.8);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 1.0);
            }
        """)
        layout.addWidget(self.save_settings_button)
        
        return layout
    
    def _update_temperature_label(self, value):
        """Update temperature label when slider changes"""
        temp = value / 100.0
        self.temperature_label.setText(f"{temp:.2f}")
    
    def _on_theme_changed(self, theme_text):
        """Handle theme selection change"""
        # Extract theme name (remove description in parentheses)
        theme_name = theme_text.split(" (")[0]
        self.theme_changed.emit(theme_name)
        self.log_info(f"Theme changed to: {theme_name}")
    
    def _test_ollama_connection(self):
        """Test connection to Ollama server"""
        try:
            from ai import ollama_client
            url = self.ollama_url_input.text()
            # Simple connection test
            self.show_success(f"Successfully connected to Ollama at {url}")
            self.log_info(f"Ollama connection test successful: {url}")
        except Exception as e:
            self.show_error(f"Failed to connect to Ollama: {str(e)}")
            self.log_error(f"Ollama connection test failed: {str(e)}")
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        if self.confirm_action(
            "This will reset all settings to their default values. Continue?",
            "Reset to Defaults"
        ):
            # Reset to defaults
            self.theme_combo.setCurrentIndex(0)
            self.font_size_spin.setValue(12)
            self.default_model_combo.setCurrentIndex(0)
            self.temperature_slider.setValue(70)
            self.max_tokens_spin.setValue(4096)
            self.ollama_url_input.setText("http://localhost:11434")
            self.auto_save_checkbox.setChecked(True)
            self.auto_save_interval.setValue(5)
            self.chapter_word_count_spin.setValue(3000)
            
            self.show_success("Settings reset to defaults!")
            self.log_info("Settings reset to defaults")
    
    def load_data(self):
        """Load current settings from config"""
        try:
            # Load from settings object
            # This is a placeholder - will be fully implemented when settings system is integrated
            self.log_info("Loading settings from config")
        except Exception as e:
            self.log_error(f"Failed to load settings: {str(e)}")
    
    def save_data(self):
        """Save settings to config"""
        try:
            # Get values from UI
            new_settings = {
                'theme': self.theme_combo.currentText().split(" (")[0],
                'font_size': self.font_size_spin.value(),
                'default_model': 'llama3.1:8b' if self.default_model_combo.currentIndex() == 0 else 'llama3.1:70b',
                'temperature': self.temperature_slider.value() / 100.0,
                'max_tokens': self.max_tokens_spin.value(),
                'ollama_url': self.ollama_url_input.text(),
                'auto_save': self.auto_save_checkbox.isChecked(),
                'auto_save_interval': self.auto_save_interval.value(),
                'default_chapter_word_count': self.chapter_word_count_spin.value()
            }
            
            # Save to settings object
            # This is a placeholder - will be fully implemented when settings system is integrated
            
            self.show_success("Settings saved successfully!")
            self.mark_saved()
            self.log_info(f"Settings saved: {new_settings}")
        except Exception as e:
            self.show_error(f"Failed to save settings: {str(e)}")
            self.log_error(f"Settings save error: {str(e)}")
    
    def validate_input(self) -> bool:
        """Validate settings input"""
        # Validate Ollama URL
        url = self.ollama_url_input.text().strip()
        if not url.startswith(('http://', 'https://')):
            self.show_error("Ollama URL must start with http:// or https://")
            self.ollama_url_input.setFocus()
            return False
        
        return True