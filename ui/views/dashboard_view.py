"""
Dashboard View
Main overview with story listing and selection
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QGridLayout, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.views.base_view import BaseView
from core.story_manager import StoryManager
from database import db_manager


class StoryCard(QFrame):
    """Individual story card widget"""
    
    clicked = pyqtSignal(int)  # Emits story_id when clicked
    delete_requested = pyqtSignal(int)  # Emits story_id for deletion
    
    def __init__(self, story_data, is_active=False, parent=None):
        super().__init__(parent)
        self.story_id = story_data['id']
        self.story_data = story_data
        self.is_active = is_active
        
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        
        self._setup_ui()
    
    def _update_style(self):
        """Update card style based on active state"""
        if self.is_active:
            self.setStyleSheet("""
                StoryCard {
                    background-color: rgba(255, 140, 0, 0.2);
                    border: 2px solid rgba(255, 140, 0, 0.8);
                    border-radius: 8px;
                    padding: 15px;
                }
                StoryCard:hover {
                    background-color: rgba(255, 140, 0, 0.3);
                    border: 2px solid rgba(255, 140, 0, 1.0);
                }
            """)
        else:
            self.setStyleSheet("""
                StoryCard {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 2px solid transparent;
                    border-radius: 8px;
                    padding: 15px;
                }
                StoryCard:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 2px solid rgba(255, 140, 0, 0.5);
                }
            """)
    
    def set_active(self, active: bool):
        """Set the active state of this card"""
        self.is_active = active
        self._update_style()
    
    def _setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Header: Title with active indicator and delete button
        header_layout = QHBoxLayout()
        
        if self.is_active:
            active_icon = QLabel("⭐")
            active_icon.setStyleSheet("font-size: 16px; color: rgb(255, 140, 0);")
            active_icon.setToolTip("Active Story")
            header_layout.addWidget(active_icon)
        
        title = QLabel(self.story_data.get('title', 'Untitled'))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setMaximumWidth(30)
        delete_btn.setMaximumHeight(30)
        delete_btn.setToolTip("Delete this story")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.6);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 0.9);
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.story_id))
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Metadata row
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(10)
        
        genre = self.story_data.get('genre', 'Unknown')
        if genre:
            genre_label = QLabel(f"📚 {genre}")
            genre_label.setStyleSheet("background-color: rgba(100, 100, 255, 0.2); padding: 4px 8px; border-radius: 3px;")
            meta_layout.addWidget(genre_label)
        
        tone = self.story_data.get('tone', '')
        if tone:
            tone_label = QLabel(f"🎭 {tone}")
            tone_label.setStyleSheet("background-color: rgba(255, 100, 100, 0.2); padding: 4px 8px; border-radius: 3px;")
            meta_layout.addWidget(tone_label)
        
        meta_layout.addStretch()
        layout.addLayout(meta_layout)
        
        # Synopsis (truncated)
        synopsis = self.story_data.get('synopsis', 'No synopsis')
        if len(synopsis) > 150:
            synopsis = synopsis[:150] + "..."
        
        synopsis_label = QLabel(synopsis)
        synopsis_label.setWordWrap(True)
        synopsis_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); margin: 5px 0;")
        synopsis_label.setMaximumHeight(60)
        layout.addWidget(synopsis_label)
        
        # Stats
        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)
        
        # Chapters
        chapters = self.story_data.get('total_chapters', 0)
        chapters_label = QLabel(f"📝 {chapters} chapters")
        stats_layout.addWidget(chapters_label, 0, 0)
        
        # Words
        words = self.story_data.get('total_word_count', 0)
        words_label = QLabel(f"📊 {words:,} words")
        stats_layout.addWidget(words_label, 0, 1)
        
        # Characters
        characters = self.story_data.get('total_characters', 0)
        char_label = QLabel(f"👤 {characters} characters")
        stats_layout.addWidget(char_label, 1, 0)
        
        # Locations
        locations = self.story_data.get('total_locations', 0)
        loc_label = QLabel(f"📍 {locations} locations")
        stats_layout.addWidget(loc_label, 1, 1)
        
        layout.addLayout(stats_layout)
        
        # Last updated
        updated = self.story_data.get('updated_at', 'Unknown')
        if updated and updated != 'Unknown':
            if 'T' in str(updated) or ' ' in str(updated):
                updated = str(updated).split('T')[0].split(' ')[0]
        
        updated_label = QLabel(f"Last updated: {updated}")
        updated_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 10px; margin-top: 5px;")
        layout.addWidget(updated_label)
        
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.story_id)
        super().mousePressEvent(event)


class DashboardView(BaseView):
    """Main dashboard view with story listing and selection"""
    
    # Signals
    story_selected = pyqtSignal(int)  # Emits story_id
    create_story_requested = pyqtSignal()
    
    def __init__(self):
        # Initialize instance attributes BEFORE calling super().__init__()
        self.story_manager = None
        self.stories_container = None
        self.no_stories_widget = None
        self.stories_scroll = None
        self.create_story_btn = None
        
        # Now call parent init which will call setup_ui()
        super().__init__()
        
        # Set view properties
        self.view_name = "Dashboard"
        
        # Initialize story manager
        self.story_manager = StoryManager(db_manager)
    
    def setup_ui(self):
        """Initialize the dashboard UI"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📚 Your Stories")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Create New Story button
        self.create_story_btn = QPushButton("➕ Create New Story")
        self.create_story_btn.setMinimumHeight(40)
        self.create_story_btn.clicked.connect(self._on_create_story)
        self.create_story_btn.setStyleSheet("""
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
        header_layout.addWidget(self.create_story_btn)
        
        main_layout.addLayout(header_layout)
        
        # Stories scroll area
        self.stories_scroll = QScrollArea()
        self.stories_scroll.setWidgetResizable(True)
        self.stories_scroll.setFrameShape(QScrollArea.NoFrame)
        
        # Container for story cards
        self.stories_container = QWidget()
        self.stories_layout = QVBoxLayout()
        self.stories_layout.setSpacing(15)
        self.stories_container.setLayout(self.stories_layout)
        
        self.stories_scroll.setWidget(self.stories_container)
        main_layout.addWidget(self.stories_scroll)
        
        # No stories widget (shown when empty)
        self.no_stories_widget = self._create_no_stories_widget()
        self.no_stories_widget.hide()
        main_layout.addWidget(self.no_stories_widget)
        
        self.setLayout(main_layout)
    
    def _create_no_stories_widget(self):
        """Create widget shown when no stories exist"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel("📖")
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon.setFont(icon_font)
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        message = QLabel("No stories yet")
        message_font = QFont()
        message_font.setPointSize(18)
        message_font.setBold(True)
        message.setFont(message_font)
        message.setAlignment(Qt.AlignCenter)
        layout.addWidget(message)
        
        submessage = QLabel("Create your first story to get started!")
        submessage.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px;")
        submessage.setAlignment(Qt.AlignCenter)
        layout.addWidget(submessage)
        
        create_btn = QPushButton("➕ Create Your First Story")
        create_btn.setMinimumHeight(50)
        create_btn.setMinimumWidth(250)
        create_btn.clicked.connect(self._on_create_story)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.8);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(56, 142, 60, 1.0);
            }
        """)
        layout.addWidget(create_btn, alignment=Qt.AlignCenter)
        
        widget.setLayout(layout)
        return widget
    
    def load_data(self):
        """Load and display all stories"""
        try:
            # Clear existing story cards
            while self.stories_layout.count():
                item = self.stories_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Get all stories
            stories = self.story_manager.get_all_stories()
            
            if not stories:
                # Show no stories message
                self.stories_scroll.hide()
                self.no_stories_widget.show()
                self.log_info("No stories found")
                return
            
            # Hide no stories message
            self.no_stories_widget.hide()
            self.stories_scroll.show()
            
            # Get active story ID
            active_story = self.story_manager.get_active_story()
            active_story_id = active_story['id'] if active_story else None
            
            # Create story cards
            for story in stories:
                # Get statistics for the story
                stats = self.story_manager.get_story_stats(story['id'])
                
                # Merge stats into story data
                story_data = story.copy()
                story_data.update(stats)
                
                # Check if this is the active story
                is_active = (story['id'] == active_story_id)
                
                # Create card with active state
                card = StoryCard(story_data, is_active=is_active)
                card.clicked.connect(self._on_story_selected)
                card.delete_requested.connect(self._on_delete_story)
                
                self.stories_layout.addWidget(card)
            
            # Add stretch at the end
            self.stories_layout.addStretch()
            
            self.log_info(f"Loaded {len(stories)} stories (active: {active_story_id})")
            
        except Exception as e:
            self.log_error(f"Error loading stories: {e}")
            self.show_error(f"Failed to load stories: {str(e)}")
    
    def _on_story_selected(self, story_id: int):
        """Handle story card click"""
        self.log_info(f"Story selected: {story_id}")
        
        # Set as active story
        if self.story_manager.set_active_story(story_id):
            self.story_selected.emit(story_id)
            # Refresh to update highlighting
            self.load_data()
        else:
            self.show_error("Failed to activate story")
    
    def _on_delete_story(self, story_id: int):
        """Handle story deletion request"""
        story = self.story_manager.get_story(story_id)
        if not story:
            return
        
        # Confirm deletion
        is_active = (story_id == self.story_manager.get_active_story_id())
        
        warning_msg = f"Are you sure you want to delete '{story['title']}'?\n\n"
        warning_msg += "This will permanently delete:\n"
        warning_msg += "• All chapters and content\n"
        warning_msg += "• All characters and locations\n"
        warning_msg += "• All lore and world-building\n"
        warning_msg += "• Everything associated with this story\n\n"
        
        if is_active:
            warning_msg += "⚠️ This is your currently active story!\n"
        
        warning_msg += "This action CANNOT be undone!"
        
        if not self.confirm_action("Delete Story", warning_msg):
            return
        
        # Delete the story
        try:
            if self.story_manager.delete_story(story_id, force=True):
                self.show_success(f"Story '{story['title']}' deleted successfully!")
                self.load_data()  # Refresh the list
                
                # If we deleted the active story, emit signal to update UI
                if is_active:
                    new_active = self.story_manager.get_active_story()
                    if new_active:
                        self.story_selected.emit(new_active['id'])
            else:
                self.show_error("Failed to delete story")
                
        except Exception as e:
            self.log_error(f"Error deleting story: {e}")
            self.show_error(f"Failed to delete story: {str(e)}")
    
    def _on_create_story(self):
        """Handle create story button"""
        self.log_info("Create story requested")
        self.create_story_requested.emit()
    
    def refresh(self):
        """Refresh the dashboard"""
        self.load_data()
    
    def save_data(self):
        """Dashboard is read-only, nothing to save"""
        pass
    
    def validate_input(self) -> bool:
        """Dashboard has no input to validate"""
        return True