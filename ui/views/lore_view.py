"""
Lore View
Manage lore entries and world-building with story-scoped persistence
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QFormLayout, QScrollArea, QWidget, QCheckBox, QSlider
)
from PyQt5.QtCore import Qt

from ui.views.base_view import BaseView
from database import db_manager


class LoreView(BaseView):
    """Lore management view with story-scoped data"""
    
    def __init__(self):
        # Initialize attributes
        self.current_lore_id = None
        self.lore_list_data = []
        
        # UI elements
        self.lore_list = None
        self.search_input = None
        self.category_filter = None
        self.add_button = None
        self.delete_button = None
        
        # Lore details form fields
        self.title_input = None
        self.category_input = None
        self.content_input = None
        self.importance_slider = None
        self.importance_label = None
        self.is_secret_check = None
        self.is_revelation_check = None
        self.tags_input = None
        self.save_button = None
        
        self.details_widget = None
        self.no_selection_label = None
        
        super().__init__()
        self.view_name = "Lore"
    
    def setup_ui(self):
        """Initialize the lore view UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - lore list
        left_panel = self._create_lore_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - lore details
        right_panel = self._create_lore_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def _create_lore_list_panel(self):
        """Create the lore list panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("Lore Entries")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search lore...")
        self.search_input.textChanged.connect(self._filter_lore)
        layout.addWidget(self.search_input)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All", "History", "Mythology", "Culture", "Religion",
            "Magic System", "Technology", "Geography", "Prophecy", "Other"
        ])
        self.category_filter.currentTextChanged.connect(self._filter_lore)
        filter_layout.addWidget(self.category_filter)
        layout.addLayout(filter_layout)
        
        # Lore list
        self.lore_list = QListWidget()
        self.lore_list.itemClicked.connect(self._on_lore_selected)
        layout.addWidget(self.lore_list)
        
        # Add button
        self.add_button = QPushButton("➕ Add New Lore Entry")
        self.add_button.clicked.connect(self._add_lore)
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
    
    def _create_lore_details_panel(self):
        """Create the lore details panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.no_selection_label = QLabel("Select a lore entry to view details\nor create a new entry to get started")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 16px; color: rgba(255, 255, 255, 0.5);")
        
        self.details_widget = self._create_details_form()
        self.details_widget.hide()
        
        layout.addWidget(self.no_selection_label)
        layout.addWidget(self.details_widget)
        
        panel.setLayout(layout)
        return panel
    
    def _create_details_form(self):
        """Create lore details form"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Lore Entry Details")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self._delete_lore)
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
        
        # Basic info
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Lore entry title")
        self.title_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("Title *:", self.title_input)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems([
            "History", "Mythology", "Culture", "Religion",
            "Magic System", "Technology", "Geography", "Prophecy", "Other"
        ])
        self.category_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Category:", self.category_input)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Content
        content_group = QGroupBox("Content")
        content_layout = QVBoxLayout()
        
        help_text = QLabel("Detailed information about this lore entry. This will be used as context for AI generation.")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: rgba(255, 255, 255, 0.7); margin-bottom: 5px; font-size: 11px;")
        content_layout.addWidget(help_text)
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Enter detailed lore information...")
        self.content_input.setMinimumHeight(200)
        self.content_input.textChanged.connect(self.mark_modified)
        content_layout.addWidget(self.content_input)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Importance
        importance_group = QGroupBox("Importance & Relevance")
        importance_layout = QVBoxLayout()
        
        importance_info = QLabel("How important is this lore for the story? Higher importance means it will be prioritized in AI context.")
        importance_info.setWordWrap(True)
        importance_info.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 5px;")
        importance_layout.addWidget(importance_info)
        
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Low"))
        
        self.importance_slider = QSlider(Qt.Horizontal)
        self.importance_slider.setRange(1, 10)
        self.importance_slider.setValue(5)
        self.importance_slider.setTickPosition(QSlider.TicksBelow)
        self.importance_slider.setTickInterval(1)
        self.importance_slider.valueChanged.connect(self._on_importance_changed)
        slider_layout.addWidget(self.importance_slider)
        
        slider_layout.addWidget(QLabel("High"))
        
        self.importance_label = QLabel("Importance: 5/10")
        self.importance_label.setStyleSheet("font-weight: bold;")
        slider_layout.addWidget(self.importance_label)
        
        importance_layout.addLayout(slider_layout)
        importance_group.setLayout(importance_layout)
        layout.addWidget(importance_group)
        
        # Flags
        flags_layout = QHBoxLayout()
        
        self.is_secret_check = QCheckBox("Secret (Not widely known)")
        self.is_secret_check.toggled.connect(self.mark_modified)
        flags_layout.addWidget(self.is_secret_check)
        
        self.is_revelation_check = QCheckBox("Major Revelation")
        self.is_revelation_check.toggled.connect(self.mark_modified)
        flags_layout.addWidget(self.is_revelation_check)
        
        flags_layout.addStretch()
        layout.addLayout(flags_layout)
        
        # Tags
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout()
        
        tags_help = QLabel("Comma-separated tags for easy searching and organization")
        tags_help.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px;")
        tags_layout.addWidget(tags_help)
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g., ancient, magical, forbidden, prophecy")
        self.tags_input.textChanged.connect(self.mark_modified)
        tags_layout.addWidget(self.tags_input)
        
        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)
        
        # Save button
        self.save_button = QPushButton("💾 Save Lore Entry")
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
        """Clear the lore detail form and reset to initial state"""
        if self.details_widget:
            self.details_widget.hide()
        
        if self.no_selection_label:
            self.no_selection_label.show()
        
        self.current_lore_id = None
        self.mark_saved()
        self.log_info("Lore view: Form cleared")

    def _on_importance_changed(self, value):
        """Update importance label"""
        self.importance_label.setText(f"Importance: {value}/10")
        self.mark_modified()
    
    def _filter_lore(self):
        """Filter lore list based on search and category"""
        search_term = self.search_input.text().lower()
        category = self.category_filter.currentText()
        
        for i in range(self.lore_list.count()):
            item = self.lore_list.item(i)
            item_data = item.data(Qt.UserRole + 1)
            
            # Check search term
            name_match = search_term in item.text().lower()
            
            # Check category
            category_match = (category == "All" or 
                            (item_data and item_data.get('category') == category))
            
            item.setHidden(not (name_match and category_match))
    
    def _on_lore_selected(self, item):
        """Handle lore selection"""
        lore_id = item.data(Qt.UserRole)
        self._load_lore(lore_id)
    
    def _load_lore(self, lore_id):
        """Load lore data into form"""
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            lore_data = db_manager.get_entity('lore_entries', lore_id, self.current_story_id)
            
            if not lore_data:
                self.show_error("Lore entry not found")
                return
            
            self.current_lore_id = lore_id
            
            # Show details panel
            self.no_selection_label.hide()
            self.details_widget.show()
            
            # Populate form
            self.title_input.setText(lore_data.get('title', ''))
            
            # Set category
            category = lore_data.get('category', 'Other')
            cat_index = self.category_input.findText(category)
            if cat_index >= 0:
                self.category_input.setCurrentIndex(cat_index)
            else:
                self.category_input.setEditText(category)
            
            self.content_input.setPlainText(lore_data.get('content', ''))
            
            importance = lore_data.get('importance', 5)
            self.importance_slider.setValue(importance)
            
            self.is_secret_check.setChecked(bool(lore_data.get('is_secret', 0)))
            self.is_revelation_check.setChecked(bool(lore_data.get('is_revelation', 0)))
            
            self.tags_input.setText(lore_data.get('tags', ''))
            
            self.mark_saved()
            self.log_info(f"Loaded lore: {lore_data.get('title')}")
            
        except Exception as e:
            self.log_error(f"Error loading lore: {e}")
            self.show_error(f"Failed to load lore entry: {str(e)}")
    
    def _add_lore(self):
        """Add new lore entry"""
        if not self.current_story_id:
            self.show_warning("Please select a story first")
            return
        
        # Clear form
        self.current_lore_id = None
        self.no_selection_label.hide()
        self.details_widget.show()
        
        self.title_input.clear()
        self.category_input.setCurrentIndex(0)
        self.content_input.clear()
        self.importance_slider.setValue(5)
        self.is_secret_check.setChecked(False)
        self.is_revelation_check.setChecked(False)
        self.tags_input.clear()
        
        self.title_input.setFocus()
        self.mark_saved()
        self.log_info("Creating new lore entry")
    
    def _delete_lore(self):
        """Delete current lore entry"""
        if not self.current_lore_id:
            return
        
        if not self.confirm_action("Delete Lore Entry", "Are you sure you want to delete this lore entry?"):
            return
        
        try:
            if db_manager.delete_entity('lore_entries', self.current_lore_id, self.current_story_id):
                self.show_success("Lore entry deleted successfully!")
                self.details_widget.hide()
                self.no_selection_label.show()
                self.current_lore_id = None
                self.load_data()
                self.log_info("Lore entry deleted")
            else:
                self.show_error("Failed to delete lore entry")
                
        except Exception as e:
            self.log_error(f"Error deleting lore: {e}")
            self.show_error(f"Failed to delete lore entry: {str(e)}")
    
    def load_data(self):
        """Load lore entries for the current story"""
        if not self.current_story_id:
            self.lore_list.clear()
            self.log_info("No active story - lore cleared")
            return
        
        try:
            # Get all lore entries for this story
            lore_entries = db_manager.get_entities_by_story('lore_entries', self.current_story_id, 'importance DESC, title ASC')
            
            # Clear list
            self.lore_list.clear()
            self.lore_list_data = lore_entries
            
            # Populate list
            for lore in lore_entries:
                title = lore.get('title', 'Untitled')
                category = lore.get('category', 'Other')
                importance = lore.get('importance', 5)
                
                # Add importance indicator
                stars = '⭐' * min(importance, 5)
                item_text = f"{title} ({category}) {stars}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, lore.get('id'))
                item.setData(Qt.UserRole + 1, lore)
                self.lore_list.addItem(item)
            
            self.log_info(f"Loaded {len(lore_entries)} lore entries for story {self.current_story_id}")
            
        except Exception as e:
            self.log_error(f"Error loading lore: {e}")
            self.show_error(f"Failed to load lore entries: {str(e)}")
    
    def save_data(self):
        """Save current lore entry"""
        if not self.validate_input():
            return
        
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            # Gather form data
            data = {
                'title': self.title_input.text().strip(),
                'category': self.category_input.currentText(),
                'content': self.content_input.toPlainText().strip(),
                'importance': self.importance_slider.value(),
                'is_secret': 1 if self.is_secret_check.isChecked() else 0,
                'is_revelation': 1 if self.is_revelation_check.isChecked() else 0,
                'tags': self.tags_input.text().strip()
            }
            
            if self.current_lore_id:
                # Update existing lore
                if db_manager.update_entity('lore_entries', self.current_lore_id, self.current_story_id, data):
                    self.show_success(f"Lore entry '{data['title']}' updated successfully!")
                    self.mark_saved()
                    self.load_data()
                    self.log_info(f"Lore updated: {data['title']}")
                else:
                    self.show_error("Failed to update lore entry")
            else:
                # Create new lore
                lore_id = db_manager.create_entity('lore_entries', self.current_story_id, data)
                
                if lore_id:
                    self.show_success(f"Lore entry '{data['title']}' created successfully!")
                    self.mark_saved()
                    self.current_lore_id = lore_id
                    self.load_data()
                    self.log_info(f"Lore created: {data['title']}")
                else:
                    self.show_error("Failed to create lore entry")
                    
        except Exception as e:
            self.log_error(f"Error saving lore: {e}")
            self.show_error(f"Failed to save lore entry: {str(e)}")
    
    def validate_input(self) -> bool:
        """Validate lore input"""
        if not self.title_input.text().strip():
            self.show_error("Lore entry title is required!")
            self.title_input.setFocus()
            return False
        return True
    
    def refresh(self):
        """Refresh lore list"""
        self.load_data()