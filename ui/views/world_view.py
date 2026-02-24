"""
World View
Manage story locations with story-scoped persistence
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QFormLayout, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt

from ui.views.base_view import BaseView
from models import Location
from database import db_manager


class WorldView(BaseView):
    """World and locations management view with story-scoped data"""
    
    def __init__(self):
        # Initialize attributes
        self.current_location_id = None
        self.locations_list_data = []
        
        # UI elements
        self.location_list = None
        self.search_input = None
        self.add_button = None
        self.delete_button = None
        
        # Location details form fields
        self.name_input = None
        self.type_input = None
        self.description_input = None
        self.history_input = None
        self.inhabitants_input = None
        self.atmosphere_input = None
        self.special_features_input = None
        self.save_button = None
        
        self.details_widget = None
        self.no_selection_label = None
        
        super().__init__()
        self.view_name = "World & Locations"
    
    def setup_ui(self):
        """Initialize the world view UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - location list
        left_panel = self._create_location_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - location details
        right_panel = self._create_location_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def _create_location_list_panel(self):
        """Create the location list panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("Locations")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search locations...")
        self.search_input.textChanged.connect(self._filter_locations)
        layout.addWidget(self.search_input)
        
        self.location_list = QListWidget()
        self.location_list.itemClicked.connect(self._on_location_selected)
        layout.addWidget(self.location_list)
        
        self.add_button = QPushButton("➕ Add New Location")
        self.add_button.clicked.connect(self._add_location)
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
    
    def _create_location_details_panel(self):
        """Create the location details panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.no_selection_label = QLabel("Select a location to view details\nor create a new location to get started")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 16px; color: rgba(255, 255, 255, 0.5);")
        
        self.details_widget = self._create_details_form()
        self.details_widget.hide()
        
        layout.addWidget(self.no_selection_label)
        layout.addWidget(self.details_widget)
        
        panel.setLayout(layout)
        return panel
    
    def _create_details_form(self):
        """Create location details form"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Location Details")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self._delete_location)
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
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Location name")
        self.name_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("Name *:", self.name_input)
        
        self.type_input = QComboBox()
        self.type_input.setEditable(True)
        self.type_input.addItems([
            "City", "Town", "Village", "Kingdom", "Empire",
            "Dungeon", "Cave", "Forest", "Mountain", "Desert",
            "Building", "Castle", "Temple", "Ruins", "Other"
        ])
        self.type_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Type:", self.type_input)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Visual description of the location...")
        self.description_input.setMaximumHeight(120)
        self.description_input.textChanged.connect(self.mark_modified)
        desc_layout.addWidget(self.description_input)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # Atmosphere
        atmosphere_group = QGroupBox("Atmosphere & Mood")
        atmosphere_layout = QVBoxLayout()
        self.atmosphere_input = QTextEdit()
        self.atmosphere_input.setPlaceholderText("How does this place feel? What's the mood?")
        self.atmosphere_input.setMaximumHeight(80)
        self.atmosphere_input.textChanged.connect(self.mark_modified)
        atmosphere_layout.addWidget(self.atmosphere_input)
        atmosphere_group.setLayout(atmosphere_layout)
        layout.addWidget(atmosphere_group)
        
        # History
        history_group = QGroupBox("History & Lore")
        history_layout = QVBoxLayout()
        self.history_input = QTextEdit()
        self.history_input.setPlaceholderText("Historical significance and background...")
        self.history_input.setMaximumHeight(100)
        self.history_input.textChanged.connect(self.mark_modified)
        history_layout.addWidget(self.history_input)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Inhabitants
        inhabitants_group = QGroupBox("Inhabitants")
        inhabitants_layout = QVBoxLayout()
        self.inhabitants_input = QTextEdit()
        self.inhabitants_input.setPlaceholderText("Who lives here? What creatures or people?")
        self.inhabitants_input.setMaximumHeight(80)
        self.inhabitants_input.textChanged.connect(self.mark_modified)
        inhabitants_layout.addWidget(self.inhabitants_input)
        inhabitants_group.setLayout(inhabitants_layout)
        layout.addWidget(inhabitants_group)
        
        # Special Features
        features_group = QGroupBox("Special Features")
        features_layout = QVBoxLayout()
        self.special_features_input = QTextEdit()
        self.special_features_input.setPlaceholderText("Unique characteristics, magical properties, points of interest...")
        self.special_features_input.setMaximumHeight(100)
        self.special_features_input.textChanged.connect(self.mark_modified)
        features_layout.addWidget(self.special_features_input)
        features_group.setLayout(features_layout)
        layout.addWidget(features_group)
        
        # Save button
        self.save_button = QPushButton("💾 Save Location")
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
        """Clear the location detail form and reset to initial state"""
        if self.details_widget:
            self.details_widget.hide()
        
        if self.no_selection_label:
            self.no_selection_label.show()
        
        self.current_location_id = None
        self.mark_saved()
        self.log_info("World view: Form cleared")

    def _filter_locations(self, text):
        """Filter location list based on search text"""
        search_term = text.lower()
        
        for i in range(self.location_list.count()):
            item = self.location_list.item(i)
            item_text = item.text().lower()
            item.setHidden(search_term not in item_text)
    
    def _on_location_selected(self, item):
        """Handle location selection"""
        location_id = item.data(Qt.UserRole)
        self._load_location(location_id)
    
    def _load_location(self, location_id):
        """Load location data into form"""
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            location = Location.get_by_id(self.current_story_id, location_id)
            
            if not location:
                self.show_error("Location not found")
                return
            
            self.current_location_id = location_id
            
            # Show details panel
            self.no_selection_label.hide()
            self.details_widget.show()
            
            # Populate form
            self.name_input.setText(location.name or "")
            
            # Set type
            type_text = location.type or "City"
            type_index = self.type_input.findText(type_text)
            if type_index >= 0:
                self.type_input.setCurrentIndex(type_index)
            else:
                self.type_input.setEditText(type_text)
            
            self.description_input.setPlainText(location.description or "")
            self.atmosphere_input.setPlainText(location.atmosphere or "")
            self.history_input.setPlainText(location.history or "")
            self.inhabitants_input.setPlainText(location.inhabitants or "")
            self.special_features_input.setPlainText(location.special_features or "")
            
            self.mark_saved()
            self.log_info(f"Loaded location: {location.name}")
            
        except Exception as e:
            self.log_error(f"Error loading location: {e}")
            self.show_error(f"Failed to load location: {str(e)}")
    
    def _add_location(self):
        """Add new location"""
        if not self.current_story_id:
            self.show_warning("Please select a story first")
            return
        
        # Clear form for new location
        self.current_location_id = None
        self.no_selection_label.hide()
        self.details_widget.show()
        
        self.name_input.clear()
        self.type_input.setCurrentIndex(0)
        self.description_input.clear()
        self.atmosphere_input.clear()
        self.history_input.clear()
        self.inhabitants_input.clear()
        self.special_features_input.clear()
        
        self.name_input.setFocus()
        self.mark_saved()
        self.log_info("Creating new location")
    
    def _delete_location(self):
        """Delete current location"""
        if not self.current_location_id:
            return
        
        if not self.confirm_action("Delete Location", "Are you sure you want to delete this location?"):
            return
        
        try:
            location = Location.get_by_id(self.current_story_id, self.current_location_id)
            
            if location and location.delete():
                self.show_success("Location deleted successfully!")
                self.details_widget.hide()
                self.no_selection_label.show()
                self.current_location_id = None
                self.load_data()  # Refresh list
                self.log_info("Location deleted")
            else:
                self.show_error("Failed to delete location")
                
        except Exception as e:
            self.log_error(f"Error deleting location: {e}")
            self.show_error(f"Failed to delete location: {str(e)}")
    
    def load_data(self):
        """Load locations for the current story"""
        if not self.current_story_id:
            self.location_list.clear()
            self.log_info("No active story - locations list cleared")
            return
        
        try:
            # Get all locations for this story
            locations = Location.get_all(self.current_story_id, sort_by='name', order='ASC')
            
            # Clear list
            self.location_list.clear()
            self.locations_list_data = locations
            
            # Populate list
            for location in locations:
                item = QListWidgetItem(f"{location.name} ({location.type or 'Location'})")
                item.setData(Qt.UserRole, location.id)
                self.location_list.addItem(item)
            
            self.log_info(f"Loaded {len(locations)} locations for story {self.current_story_id}")
            
        except Exception as e:
            self.log_error(f"Error loading locations: {e}")
            self.show_error(f"Failed to load locations: {str(e)}")
    
    def save_data(self):
        """Save current location"""
        if not self.validate_input():
            return
        
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            # Gather form data
            name = self.name_input.text().strip()
            loc_type = self.type_input.currentText()
            description = self.description_input.toPlainText().strip()
            atmosphere = self.atmosphere_input.toPlainText().strip()
            history = self.history_input.toPlainText().strip()
            inhabitants = self.inhabitants_input.toPlainText().strip()
            special_features = self.special_features_input.toPlainText().strip()
            
            if self.current_location_id:
                # Update existing location
                location = Location.get_by_id(self.current_story_id, self.current_location_id)
                
                if location:
                    location.name = name
                    location.type = loc_type
                    location.description = description
                    location.atmosphere = atmosphere
                    location.history = history
                    location.inhabitants = inhabitants
                    location.special_features = special_features
                    
                    if location.save():
                        self.show_success(f"Location '{name}' updated successfully!")
                        self.mark_saved()
                        self.load_data()  # Refresh list
                        self.log_info(f"Location updated: {name}")
                    else:
                        self.show_error("Failed to update location")
                else:
                    self.show_error("Location not found")
            else:
                # Create new location
                location = Location(
                    self.current_story_id,
                    name=name,
                    type=loc_type,
                    description=description,
                    atmosphere=atmosphere,
                    history=history,
                    inhabitants=inhabitants,
                    special_features=special_features
                )
                
                if location.save():
                    self.show_success(f"Location '{name}' created successfully!")
                    self.mark_saved()
                    self.current_location_id = location.id
                    self.load_data()  # Refresh list
                    self.log_info(f"Location created: {name}")
                else:
                    self.show_error("Failed to create location")
                    
        except Exception as e:
            self.log_error(f"Error saving location: {e}")
            self.show_error(f"Failed to save location: {str(e)}")
    
    def validate_input(self) -> bool:
        """Validate location input"""
        if not self.name_input.text().strip():
            self.show_error("Location name is required!")
            self.name_input.setFocus()
            return False
        return True
    
    def refresh(self):
        """Refresh locations list"""
        self.load_data()