"""
Story View
Manage story metadata and overview
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QGroupBox, QFormLayout, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.views.base_view import BaseView
from core.story_manager import StoryManager
from database import db_manager


class StoryView(BaseView):
    """Story metadata and overview management"""
    
    # Signal emitted when a new story is created
    story_created = pyqtSignal(int)  # Emits story_id
    
    def __init__(self):
        # Initialize attributes first
        self.story_manager = None
        self.current_story_data = None
        self.is_editing = False
        
        # Form fields
        self.title_input = None
        self.genre_input = None
        self.setting_input = None
        self.tone_input = None
        self.target_audience_input = None
        self.synopsis_input = None
        self.notes_input = None
        
        # Buttons
        self.save_button = None
        self.new_story_button = None
        self.cancel_button = None
        
        super().__init__()
        self.view_name = "Story Overview"
        
        # Initialize story manager
        self.story_manager = StoryManager(db_manager)
    
    def setup_ui(self):
        """Initialize the story view UI"""
        # Main scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        # Content widget
        content = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header with buttons
        header_layout = QHBoxLayout()
        
        header = QLabel("Story Information")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # New Story button
        self.new_story_button = QPushButton("➕ New Story")
        self.new_story_button.clicked.connect(self._on_new_story)
        self.new_story_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(33, 150, 243, 0.8);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(33, 150, 243, 1.0);
            }
        """)
        header_layout.addWidget(self.new_story_button)
        
        main_layout.addLayout(header_layout)
        
        # Story metadata form
        metadata_group = self._create_metadata_form()
        main_layout.addWidget(metadata_group)
        
        # Synopsis section
        synopsis_group = self._create_synopsis_section()
        main_layout.addWidget(synopsis_group)
        
        # Notes section
        notes_group = self._create_notes_section()
        main_layout.addWidget(notes_group)
        
        # Action buttons
        button_layout = self._create_action_buttons()
        main_layout.addLayout(button_layout)
        
        main_layout.addStretch()
        content.setLayout(main_layout)
        scroll.setWidget(content)
        
        # Set main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)
    
    def _create_metadata_form(self):
        """Create story metadata input form"""
        group = QGroupBox("Basic Information")
        layout = QFormLayout()
        layout.setSpacing(10)
        
        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter story title...")
        self.title_input.textChanged.connect(self.mark_modified)
        layout.addRow("Title *:", self.title_input)
        
        # Genre
        self.genre_input = QComboBox()
        self.genre_input.setEditable(True)
        self.genre_input.addItems([
            "Fantasy", "Science Fiction", "Mystery", "Thriller",
            "Romance", "Horror", "Adventure", "Historical Fiction",
            "Urban Fantasy", "Cyberpunk", "Steampunk", "Other"
        ])
        self.genre_input.currentTextChanged.connect(self.mark_modified)
        layout.addRow("Genre:", self.genre_input)
        
        # Setting
        self.setting_input = QLineEdit()
        self.setting_input.setPlaceholderText("e.g., Medieval fantasy world, Future Earth...")
        self.setting_input.textChanged.connect(self.mark_modified)
        layout.addRow("Setting:", self.setting_input)
        
        # Tone
        self.tone_input = QComboBox()
        self.tone_input.setEditable(True)
        self.tone_input.addItems([
            "Dark", "Light-hearted", "Dramatic", "Humorous",
            "Serious", "Whimsical", "Gritty", "Epic", "Mysterious"
        ])
        self.tone_input.currentTextChanged.connect(self.mark_modified)
        layout.addRow("Tone:", self.tone_input)
        
        # Target Audience
        self.target_audience_input = QComboBox()
        self.target_audience_input.setEditable(True)
        self.target_audience_input.addItems([
            "Young Adult", "Adult", "Middle Grade", "New Adult", "General"
        ])
        self.target_audience_input.currentTextChanged.connect(self.mark_modified)
        layout.addRow("Target Audience:", self.target_audience_input)
        
        group.setLayout(layout)
        return group
    
    def _create_synopsis_section(self):
        """Create synopsis text area"""
        group = QGroupBox("Synopsis")
        layout = QVBoxLayout()
        
        help_text = QLabel("Describe your story's plot, themes, and main conflicts. This will be used as context for AI generation.")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: rgba(255, 255, 255, 0.7); margin-bottom: 10px;")
        layout.addWidget(help_text)
        
        self.synopsis_input = QTextEdit()
        self.synopsis_input.setPlaceholderText("Enter a detailed synopsis of your story...")
        self.synopsis_input.setMinimumHeight(150)
        self.synopsis_input.textChanged.connect(self.mark_modified)
        layout.addWidget(self.synopsis_input)
        
        group.setLayout(layout)
        return group
    
    def _create_notes_section(self):
        """Create notes text area"""
        group = QGroupBox("Additional Notes")
        layout = QVBoxLayout()
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any additional notes, ideas, or reminders about your story...")
        self.notes_input.setMinimumHeight(100)
        self.notes_input.textChanged.connect(self.mark_modified)
        layout.addWidget(self.notes_input)
        
        group.setLayout(layout)
        return group
    
    def _create_action_buttons(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self._on_cancel)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(158, 158, 158, 0.5);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: rgba(158, 158, 158, 0.7);
            }
        """)
        layout.addWidget(self.cancel_button)
        
        layout.addStretch()
        
        # Save button
        self.save_button = QPushButton("💾 Save Story")
        self.save_button.setMinimumHeight(40)
        self.save_button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: rgba(56, 142, 60, 1.0);
            }
        """)
        self.save_button.clicked.connect(self.save_data)
        layout.addWidget(self.save_button)
        
        return layout
    
    def _on_new_story(self):
        """Handle new story button click"""
        if self.is_modified:
            if not self.confirm_action("Discard Changes", "You have unsaved changes. Start a new story anyway?"):
                return
        
        self._clear_form()
        self.is_editing = False
        self.current_story_data = None
        self.mark_saved()
        self.log_info("Starting new story")
    
    def _on_cancel(self):
        """Handle cancel button click"""
        if self.is_modified:
            if not self.confirm_action("Discard Changes", "You have unsaved changes. Discard them?"):
                return
        
        if self.current_story_id:
            # Reload current story
            self.load_data()
        else:
            # Clear form
            self._clear_form()
        
        self.mark_saved()
    
    def _clear_form(self):
        """Clear all form fields"""
        self.title_input.clear()
        self.genre_input.setCurrentIndex(0)
        self.setting_input.clear()
        self.tone_input.setCurrentIndex(0)
        self.target_audience_input.setCurrentIndex(0)
        self.synopsis_input.clear()
        self.notes_input.clear()
    
    def load_data(self):
        """Load story data for the current story"""
        if not self.current_story_id:
            self.log_info("No active story - form cleared")
            self._clear_form()
            self.is_editing = False
            self.mark_saved()
            return
        
        try:
            # Get story data
            story = self.story_manager.get_story(self.current_story_id)
            
            if not story:
                self.log_warning(f"Story {self.current_story_id} not found")
                self._clear_form()
                return
            
            # Store story data
            self.current_story_data = story
            self.is_editing = True
            
            # Populate form
            self.title_input.setText(story.get('title', ''))
            
            # Set genre (handle both index and custom text)
            genre = story.get('genre', '')
            index = self.genre_input.findText(genre)
            if index >= 0:
                self.genre_input.setCurrentIndex(index)
            else:
                self.genre_input.setEditText(genre)
            
            self.setting_input.setText(story.get('setting', ''))
            
            # Set tone
            tone = story.get('tone', '')
            index = self.tone_input.findText(tone)
            if index >= 0:
                self.tone_input.setCurrentIndex(index)
            else:
                self.tone_input.setEditText(tone)
            
            # Set target audience
            audience = story.get('target_audience', '')
            index = self.target_audience_input.findText(audience)
            if index >= 0:
                self.target_audience_input.setCurrentIndex(index)
            else:
                self.target_audience_input.setEditText(audience)
            
            self.synopsis_input.setPlainText(story.get('synopsis', ''))
            self.notes_input.setPlainText(story.get('notes', ''))
            
            self.mark_saved()
            self.log_info(f"Loaded story: {story.get('title')}")
            
        except Exception as e:
            self.log_error(f"Error loading story data: {e}")
            self.show_error(f"Failed to load story: {str(e)}")
    
    def save_data(self):
        """Save story data"""
        if not self.validate_input():
            return
        
        try:
            # Gather form data
            title = self.title_input.text().strip()
            genre = self.genre_input.currentText().strip()
            setting = self.setting_input.text().strip()
            tone = self.tone_input.currentText().strip()
            target_audience = self.target_audience_input.currentText().strip()
            synopsis = self.synopsis_input.toPlainText().strip()
            notes = self.notes_input.toPlainText().strip()
            
            if self.is_editing and self.current_story_id:
                # Update existing story
                success = self.story_manager.update_story(
                    self.current_story_id,
                    title=title,
                    genre=genre,
                    setting=setting,
                    tone=tone,
                    target_audience=target_audience,
                    synopsis=synopsis,
                    notes=notes
                )
                
                if success:
                    self.show_success(f"Story '{title}' updated successfully!")
                    self.mark_saved()
                    self.log_info(f"Story updated: {title}")
                else:
                    self.show_error("Failed to update story")
                    
            else:
                # Create new story
                story_id = self.story_manager.create_story(
                    title=title,
                    genre=genre,
                    setting=setting,
                    tone=tone,
                    target_audience=target_audience,
                    synopsis=synopsis,
                    notes=notes
                )
                
                if story_id:
                    # Initialize database for new story
                    db_manager.initialize_database(story_id)
                    
                    self.show_success(f"Story '{title}' created successfully!")
                    self.mark_saved()
                    
                    # Update internal state
                    self.current_story_id = story_id
                    self.is_editing = True
                    
                    # Emit signal that story was created
                    self.story_created.emit(story_id)
                    
                    self.log_info(f"Story created: {title} (ID: {story_id})")
                else:
                    self.show_error("Failed to create story")
                    
        except ValueError as e:
            # Handle duplicate title error
            self.show_error(str(e))
            self.log_error(f"Story save error: {e}")
        except Exception as e:
            self.show_error(f"Failed to save story: {str(e)}")
            self.log_error(f"Story save error: {e}")
    
    def validate_input(self) -> bool:
        """Validate story input"""
        if not self.title_input.text().strip():
            self.show_error("Story title is required!")
            self.title_input.setFocus()
            return False
        
        return True
    
    def refresh(self):
        """Refresh story data"""
        self.load_data()