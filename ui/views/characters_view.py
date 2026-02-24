"""
Characters View
Manage story characters with story-scoped persistence
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QFormLayout, QScrollArea, QWidget, QSpinBox
)
from PyQt5.QtCore import Qt

from ui.views.base_view import BaseView
from models import Character
from database import db_manager


class CharactersView(BaseView):
    """Character management view with story-scoped data"""
    
    def __init__(self):
        # Initialize attributes
        self.current_character_id = None
        self.characters_list_data = []
        
        # UI elements
        self.character_list = None
        self.search_input = None
        self.add_button = None
        self.delete_button = None
        
        # Character details form fields
        self.name_input = None
        self.role_input = None
        self.age_input = None
        self.status_input = None
        self.appearance_input = None
        self.personality_input = None
        self.background_input = None
        self.goals_input = None
        self.fears_input = None
        self.abilities_input = None
        self.save_button = None
        
        self.details_widget = None
        self.no_selection_label = None
        
        super().__init__()
        self.view_name = "Characters"
    
    def setup_ui(self):
        """Initialize the characters view UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - character list
        left_panel = self._create_character_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - character details
        right_panel = self._create_character_details_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% list, 70% details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def _create_character_list_panel(self):
        """Create the character list panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("Characters")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search characters...")
        self.search_input.textChanged.connect(self._filter_characters)
        layout.addWidget(self.search_input)
        
        # Character list
        self.character_list = QListWidget()
        self.character_list.itemClicked.connect(self._on_character_selected)
        layout.addWidget(self.character_list)
        
        # Add button
        self.add_button = QPushButton("➕ Add New Character")
        self.add_button.clicked.connect(self._add_character)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.8);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 1.0);
            }
        """)
        layout.addWidget(self.add_button)
        
        panel.setLayout(layout)
        return panel
    
    def _create_character_details_panel(self):
        """Create the character details panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # No selection message
        self.no_selection_label = QLabel("Select a character to view details\nor create a new character to get started")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 16px; color: rgba(255, 255, 255, 0.5);")
        
        # Details form (initially hidden)
        self.details_widget = self._create_details_form()
        self.details_widget.hide()
        
        layout.addWidget(self.no_selection_label)
        layout.addWidget(self.details_widget)
        
        panel.setLayout(layout)
        return panel
    
    def _create_details_form(self):
        """Create character details form"""
        widget = QWidget()
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header with delete button
        header_layout = QHBoxLayout()
        header = QLabel("Character Details")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self._delete_character)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.8);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 1.0);
            }
        """)
        header_layout.addWidget(self.delete_button)
        layout.addLayout(header_layout)
        
        # Basic info group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Character name")
        self.name_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("Name *:", self.name_input)
        
        self.role_input = QComboBox()
        self.role_input.addItems(["Protagonist", "Antagonist", "Supporting", "Minor"])
        self.role_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Role:", self.role_input)
        
        self.age_input = QSpinBox()
        self.age_input.setRange(0, 9999)
        self.age_input.valueChanged.connect(self.mark_modified)
        basic_layout.addRow("Age:", self.age_input)
        
        self.status_input = QComboBox()
        self.status_input.addItems(["Alive", "Deceased", "Unknown"])
        self.status_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Status:", self.status_input)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        self.appearance_input = QTextEdit()
        self.appearance_input.setPlaceholderText("Describe physical appearance...")
        self.appearance_input.setMaximumHeight(100)
        self.appearance_input.textChanged.connect(self.mark_modified)
        appearance_layout.addWidget(self.appearance_input)
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Personality
        personality_group = QGroupBox("Personality")
        personality_layout = QVBoxLayout()
        self.personality_input = QTextEdit()
        self.personality_input.setPlaceholderText("Describe personality traits...")
        self.personality_input.setMaximumHeight(100)
        self.personality_input.textChanged.connect(self.mark_modified)
        personality_layout.addWidget(self.personality_input)
        personality_group.setLayout(personality_layout)
        layout.addWidget(personality_group)
        
        # Background
        background_group = QGroupBox("Background")
        background_layout = QVBoxLayout()
        self.background_input = QTextEdit()
        self.background_input.setPlaceholderText("Character history and background...")
        self.background_input.setMaximumHeight(100)
        self.background_input.textChanged.connect(self.mark_modified)
        background_layout.addWidget(self.background_input)
        background_group.setLayout(background_layout)
        layout.addWidget(background_group)
        
        # Goals
        goals_group = QGroupBox("Goals & Motivations")
        goals_layout = QVBoxLayout()
        self.goals_input = QTextEdit()
        self.goals_input.setPlaceholderText("What does this character want?")
        self.goals_input.setMaximumHeight(80)
        self.goals_input.textChanged.connect(self.mark_modified)
        goals_layout.addWidget(self.goals_input)
        goals_group.setLayout(goals_layout)
        layout.addWidget(goals_group)
        
        # Fears
        fears_group = QGroupBox("Fears & Weaknesses")
        fears_layout = QVBoxLayout()
        self.fears_input = QTextEdit()
        self.fears_input.setPlaceholderText("What does this character fear?")
        self.fears_input.setMaximumHeight(80)
        self.fears_input.textChanged.connect(self.mark_modified)
        fears_layout.addWidget(self.fears_input)
        fears_group.setLayout(fears_layout)
        layout.addWidget(fears_group)
        
        # Abilities
        abilities_group = QGroupBox("Abilities & Skills")
        abilities_layout = QVBoxLayout()
        self.abilities_input = QTextEdit()
        self.abilities_input.setPlaceholderText("Special powers, skills, combat abilities...")
        self.abilities_input.setMaximumHeight(100)
        self.abilities_input.textChanged.connect(self.mark_modified)
        abilities_layout.addWidget(self.abilities_input)
        abilities_group.setLayout(abilities_layout)
        layout.addWidget(abilities_group)
        
        # Save button
        self.save_button = QPushButton("💾 Save Character")
        self.save_button.setMinimumHeight(40)
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.8);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 1.0);
            }
        """)
        layout.addWidget(self.save_button)
        
        content.setLayout(layout)
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        widget.setLayout(main_layout)
        
        return widget
    
    def clear_form(self):
        """Clear the character detail form and reset to initial state"""
        # Hide detail panel
        if self.details_widget:
            self.details_widget.hide()
        
        # Show no selection message  
        if self.no_selection_label:
            self.no_selection_label.show()
        
        # Clear current selection
        self.current_character_id = None
        
        # Mark as saved
        self.mark_saved()
        
        self.log_info("Characters view: Form cleared")

    def _filter_characters(self, text):
        """Filter character list based on search text"""
        search_term = text.lower()
        
        for i in range(self.character_list.count()):
            item = self.character_list.item(i)
            item_text = item.text().lower()
            item.setHidden(search_term not in item_text)
    
    def _on_character_selected(self, item):
        """Handle character selection"""
        character_id = item.data(Qt.UserRole)
        self._load_character(character_id)
    
    def _load_character(self, character_id):
        """Load character data into form"""
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            character = Character.get_by_id(self.current_story_id, character_id)
            
            if not character:
                self.show_error("Character not found")
                return
            
            self.current_character_id = character_id
            
            # Show details panel
            self.no_selection_label.hide()
            self.details_widget.show()
            
            # Populate form
            self.name_input.setText(character.name or "")
            
            # Set role
            role_index = self.role_input.findText(character.role or "Protagonist")
            self.role_input.setCurrentIndex(role_index if role_index >= 0 else 0)
            
            self.age_input.setValue(character.age or 0)
            
            # Set status
            status_index = self.status_input.findText(character.status or "Alive")
            self.status_input.setCurrentIndex(status_index if status_index >= 0 else 0)
            
            self.appearance_input.setPlainText(character.appearance or "")
            self.personality_input.setPlainText(character.personality or "")
            self.background_input.setPlainText(character.background or "")
            self.goals_input.setPlainText(character.goals or "")
            self.fears_input.setPlainText(character.fears or "")
            self.abilities_input.setPlainText(character.abilities or "")
            
            self.mark_saved()
            self.log_info(f"Loaded character: {character.name}")
            
        except Exception as e:
            self.log_error(f"Error loading character: {e}")
            self.show_error(f"Failed to load character: {str(e)}")
    
    def _add_character(self):
        """Add new character"""
        if not self.current_story_id:
            self.show_warning("Please select a story first")
            return
        
        # Clear form for new character
        self.current_character_id = None
        self.no_selection_label.hide()
        self.details_widget.show()
        
        self.name_input.clear()
        self.role_input.setCurrentIndex(0)
        self.age_input.setValue(0)
        self.status_input.setCurrentIndex(0)
        self.appearance_input.clear()
        self.personality_input.clear()
        self.background_input.clear()
        self.goals_input.clear()
        self.fears_input.clear()
        self.abilities_input.clear()
        
        self.name_input.setFocus()
        self.mark_saved()
        self.log_info("Creating new character")
    
    def _delete_character(self):
        """Delete current character"""
        if not self.current_character_id:
            return
        
        if not self.confirm_action("Delete Character", "Are you sure you want to delete this character?"):
            return
        
        try:
            character = Character.get_by_id(self.current_story_id, self.current_character_id)
            
            if character and character.delete():
                self.show_success("Character deleted successfully!")
                self.details_widget.hide()
                self.no_selection_label.show()
                self.current_character_id = None
                self.load_data()  # Refresh list
                self.log_info("Character deleted")
            else:
                self.show_error("Failed to delete character")
                
        except Exception as e:
            self.log_error(f"Error deleting character: {e}")
            self.show_error(f"Failed to delete character: {str(e)}")
    
    def load_data(self):
        """Load characters for the current story"""
        if not self.current_story_id:
            self.character_list.clear()
            self.log_info("No active story - characters list cleared")
            return
        
        try:
            # Get all characters for this story
            characters = Character.get_all(self.current_story_id, sort_by='name', order='ASC')
            
            # Clear list
            self.character_list.clear()
            self.characters_list_data = characters
            
            # Populate list
            for character in characters:
                item = QListWidgetItem(f"{character.name} ({character.role or 'Character'})")
                item.setData(Qt.UserRole, character.id)
                self.character_list.addItem(item)
            
            self.log_info(f"Loaded {len(characters)} characters for story {self.current_story_id}")
            
        except Exception as e:
            self.log_error(f"Error loading characters: {e}")
            self.show_error(f"Failed to load characters: {str(e)}")
    
    def save_data(self):
        """Save current character"""
        if not self.validate_input():
            return
        
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            # Gather form data
            name = self.name_input.text().strip()
            role = self.role_input.currentText()
            age = self.age_input.value() if self.age_input.value() > 0 else None
            status = self.status_input.currentText()
            appearance = self.appearance_input.toPlainText().strip()
            personality = self.personality_input.toPlainText().strip()
            background = self.background_input.toPlainText().strip()
            goals = self.goals_input.toPlainText().strip()
            fears = self.fears_input.toPlainText().strip()
            abilities = self.abilities_input.toPlainText().strip()
            
            if self.current_character_id:
                # Update existing character
                character = Character.get_by_id(self.current_story_id, self.current_character_id)
                
                if character:
                    character.name = name
                    character.role = role
                    character.age = age
                    character.status = status
                    character.appearance = appearance
                    character.personality = personality
                    character.background = background
                    character.goals = goals
                    character.fears = fears
                    character.abilities = abilities
                    
                    if character.save():
                        self.show_success(f"Character '{name}' updated successfully!")
                        self.mark_saved()
                        self.load_data()  # Refresh list
                        self.log_info(f"Character updated: {name}")
                    else:
                        self.show_error("Failed to update character")
                else:
                    self.show_error("Character not found")
            else:
                # Create new character
                character = Character(
                    self.current_story_id,
                    name=name,
                    role=role,
                    age=age,
                    status=status,
                    appearance=appearance,
                    personality=personality,
                    background=background,
                    goals=goals,
                    fears=fears,
                    abilities=abilities
                )
                
                if character.save():
                    self.show_success(f"Character '{name}' created successfully!")
                    self.mark_saved()
                    self.current_character_id = character.id
                    self.load_data()  # Refresh list
                    self.log_info(f"Character created: {name}")
                else:
                    self.show_error("Failed to create character")
                    
        except Exception as e:
            self.log_error(f"Error saving character: {e}")
            self.show_error(f"Failed to save character: {str(e)}")
    
    def validate_input(self) -> bool:
        """Validate character input"""
        if not self.name_input.text().strip():
            self.show_error("Character name is required!")
            self.name_input.setFocus()
            return False
        return True
    
    def refresh(self):
        """Refresh characters list"""
        self.load_data()