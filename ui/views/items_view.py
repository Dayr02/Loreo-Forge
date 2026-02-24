"""
Items View
Manage story items, weapons, artifacts, and equipment with story-scoped persistence
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QFormLayout, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt

from ui.views.base_view import BaseView
from database import db_manager


class ItemsView(BaseView):
    """Items and artifacts management view with story-scoped data"""
    
    def __init__(self):
        # Initialize attributes
        self.current_item_id = None
        self.items_list_data = []
        
        # UI elements
        self.item_list = None
        self.search_input = None
        self.add_button = None
        self.delete_button = None
        
        # Item details form fields
        self.name_input = None
        self.type_input = None
        self.category_input = None
        self.rarity_input = None
        self.description_input = None
        self.properties_input = None
        self.powers_input = None
        self.materials_input = None
        self.creator_input = None
        self.history_input = None
        self.current_owner_input = None
        self.current_location_input = None
        self.value_input = None
        self.notes_input = None
        self.save_button = None
        
        self.details_widget = None
        self.no_selection_label = None
        
        super().__init__()
        self.view_name = "Items & Artifacts"
    
    def setup_ui(self):
        """Initialize the items view UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - item list
        left_panel = self._create_item_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - item details
        right_panel = self._create_item_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def _create_item_list_panel(self):
        """Create the item list panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("Items & Artifacts")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search items...")
        self.search_input.textChanged.connect(self._filter_items)
        layout.addWidget(self.search_input)
        
        self.item_list = QListWidget()
        self.item_list.itemClicked.connect(self._on_item_selected)
        layout.addWidget(self.item_list)
        
        self.add_button = QPushButton("➕ Add New Item")
        self.add_button.clicked.connect(self._add_item)
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
    
    def _create_item_details_panel(self):
        """Create the item details panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.no_selection_label = QLabel("Select an item to view details\nor create a new item to get started")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 16px; color: rgba(255, 255, 255, 0.5);")
        
        self.details_widget = self._create_details_form()
        self.details_widget.hide()
        
        layout.addWidget(self.no_selection_label)
        layout.addWidget(self.details_widget)
        
        panel.setLayout(layout)
        return panel
    
    def _create_details_form(self):
        """Create item details form"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Item Details")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self._delete_item)
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
        self.name_input.setPlaceholderText("Item name")
        self.name_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("Name *:", self.name_input)
        
        self.type_input = QComboBox()
        self.type_input.setEditable(True)
        self.type_input.addItems([
            "Weapon", "Armor", "Artifact", "Tool", "Consumable",
            "Quest Item", "Currency", "Jewelry", "Book", "Other"
        ])
        self.type_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Type:", self.type_input)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems([
            "Melee", "Ranged", "Magical", "Mundane", "Legendary",
            "Cursed", "Divine", "Ancient", "Technological", "Other"
        ])
        self.category_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Category:", self.category_input)
        
        self.rarity_input = QComboBox()
        self.rarity_input.addItems([
            "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical", "Unique"
        ])
        self.rarity_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Rarity:", self.rarity_input)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Physical description and appearance...")
        self.description_input.setMaximumHeight(120)
        self.description_input.textChanged.connect(self.mark_modified)
        desc_layout.addWidget(self.description_input)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # Properties & Powers
        props_group = QGroupBox("Properties & Powers")
        props_layout = QVBoxLayout()
        
        props_label = QLabel("Special Properties:")
        props_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        props_layout.addWidget(props_label)
        
        self.properties_input = QTextEdit()
        self.properties_input.setPlaceholderText("Magical or special properties...")
        self.properties_input.setMaximumHeight(100)
        self.properties_input.textChanged.connect(self.mark_modified)
        props_layout.addWidget(self.properties_input)
        
        powers_label = QLabel("Granted Powers/Abilities:")
        powers_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        props_layout.addWidget(powers_label)
        
        self.powers_input = QTextEdit()
        self.powers_input.setPlaceholderText("Abilities or powers this item grants...")
        self.powers_input.setMaximumHeight(100)
        self.powers_input.textChanged.connect(self.mark_modified)
        props_layout.addWidget(self.powers_input)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        # Materials & Crafting
        materials_group = QGroupBox("Materials & Crafting")
        materials_layout = QVBoxLayout()
        
        mat_label = QLabel("Materials:")
        mat_label.setStyleSheet("font-weight: bold;")
        materials_layout.addWidget(mat_label)
        
        self.materials_input = QTextEdit()
        self.materials_input.setPlaceholderText("What is this item made of?")
        self.materials_input.setMaximumHeight(80)
        self.materials_input.textChanged.connect(self.mark_modified)
        materials_layout.addWidget(self.materials_input)
        
        creator_form = QFormLayout()
        self.creator_input = QLineEdit()
        self.creator_input.setPlaceholderText("Craftsman, smith, wizard...")
        self.creator_input.textChanged.connect(self.mark_modified)
        creator_form.addRow("Creator:", self.creator_input)
        materials_layout.addLayout(creator_form)
        
        materials_group.setLayout(materials_layout)
        layout.addWidget(materials_group)
        
        # History & Lore
        history_group = QGroupBox("History & Lore")
        history_layout = QVBoxLayout()
        self.history_input = QTextEdit()
        self.history_input.setPlaceholderText("Origin story, previous owners, legends...")
        self.history_input.setMaximumHeight(100)
        self.history_input.textChanged.connect(self.mark_modified)
        history_layout.addWidget(self.history_input)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Ownership & Location
        ownership_group = QGroupBox("Ownership & Location")
        ownership_layout = QFormLayout()
        
        self.current_owner_input = QLineEdit()
        self.current_owner_input.setPlaceholderText("Who currently possesses this item")
        self.current_owner_input.textChanged.connect(self.mark_modified)
        ownership_layout.addRow("Current Owner:", self.current_owner_input)
        
        self.current_location_input = QLineEdit()
        self.current_location_input.setPlaceholderText("Where the item is now")
        self.current_location_input.textChanged.connect(self.mark_modified)
        ownership_layout.addRow("Current Location:", self.current_location_input)
        
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Worth or price")
        self.value_input.textChanged.connect(self.mark_modified)
        ownership_layout.addRow("Value:", self.value_input)
        
        ownership_group.setLayout(ownership_layout)
        layout.addWidget(ownership_group)
        
        # Additional Notes
        notes_group = QGroupBox("Additional Notes")
        notes_layout = QVBoxLayout()
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any other relevant information...")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.textChanged.connect(self.mark_modified)
        notes_layout.addWidget(self.notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # Save button
        self.save_button = QPushButton("💾 Save Item")
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
        """Clear the item detail form and reset to initial state"""
        if self.details_widget:
            self.details_widget.hide()
        
        if self.no_selection_label:
            self.no_selection_label.show()
        
        self.current_item_id = None
        self.mark_saved()
        self.log_info("Items view: Form cleared")

    def _filter_items(self, text):
        """Filter item list based on search text"""
        search_term = text.lower()
        
        for i in range(self.item_list.count()):
            item = self.item_list.item(i)
            item_text = item.text().lower()
            item.setHidden(search_term not in item_text)
    
    def _on_item_selected(self, item):
        """Handle item selection"""
        item_id = item.data(Qt.UserRole)
        self._load_item(item_id)
    
    def _load_item(self, item_id):
        """Load item data into form"""
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            item_data = db_manager.get_entity('items', item_id, self.current_story_id)
            
            if not item_data:
                self.show_error("Item not found")
                return
            
            self.current_item_id = item_id
            
            # Show details panel
            self.no_selection_label.hide()
            self.details_widget.show()
            
            # Populate form
            self.name_input.setText(item_data.get('name') or "")
            
            # Set type
            item_type = item_data.get('type') or "Weapon"
            type_index = self.type_input.findText(item_type)
            if type_index >= 0:
                self.type_input.setCurrentIndex(type_index)
            else:
                self.type_input.setEditText(item_type)
            
            # Set category
            category = item_data.get('category') or "Magical"
            category_index = self.category_input.findText(category)
            if category_index >= 0:
                self.category_input.setCurrentIndex(category_index)
            else:
                self.category_input.setEditText(category)
            
            # Set rarity
            rarity = item_data.get('rarity') or "Common"
            rarity_index = self.rarity_input.findText(rarity)
            self.rarity_input.setCurrentIndex(rarity_index if rarity_index >= 0 else 0)
            
            self.description_input.setPlainText(item_data.get('description') or "")
            self.properties_input.setPlainText(item_data.get('properties') or "")
            self.powers_input.setPlainText(item_data.get('powers') or "")
            self.materials_input.setPlainText(item_data.get('materials') or "")
            self.creator_input.setText(item_data.get('creator') or "")
            self.history_input.setPlainText(item_data.get('history') or "")
            self.current_owner_input.setText(item_data.get('current_owner') or "")
            self.current_location_input.setText(item_data.get('current_location') or "")
            self.value_input.setText(item_data.get('value') or "")
            self.notes_input.setPlainText(item_data.get('notes') or "")
            
            self.mark_saved()
            self.log_info(f"Loaded item: {item_data.get('name')}")
            
        except Exception as e:
            self.log_error(f"Error loading item: {e}")
            self.show_error(f"Failed to load item: {str(e)}")
    
    def _add_item(self):
        """Add new item"""
        if not self.current_story_id:
            self.show_warning("Please select a story first")
            return
        
        # Clear form for new item
        self.current_item_id = None
        self.no_selection_label.hide()
        self.details_widget.show()
        
        self.name_input.clear()
        self.type_input.setCurrentIndex(0)
        self.category_input.setCurrentIndex(0)
        self.rarity_input.setCurrentIndex(0)
        self.description_input.clear()
        self.properties_input.clear()
        self.powers_input.clear()
        self.materials_input.clear()
        self.creator_input.clear()
        self.history_input.clear()
        self.current_owner_input.clear()
        self.current_location_input.clear()
        self.value_input.clear()
        self.notes_input.clear()
        
        self.name_input.setFocus()
        self.mark_saved()
        self.log_info("Creating new item")
    
    def _delete_item(self):
        """Delete current item"""
        if not self.current_item_id:
            return
        
        if not self.confirm_action("Delete Item", "Are you sure you want to delete this item?"):
            return
        
        try:
            if db_manager.delete_entity('items', self.current_item_id, self.current_story_id):
                self.show_success("Item deleted successfully!")
                self.details_widget.hide()
                self.no_selection_label.show()
                self.current_item_id = None
                self.load_data()
                self.log_info("Item deleted")
            else:
                self.show_error("Failed to delete item")
                
        except Exception as e:
            self.log_error(f"Error deleting item: {e}")
            self.show_error(f"Failed to delete item: {str(e)}")
    
    def load_data(self):
        """Load items for the current story"""
        if not self.current_story_id:
            self.item_list.clear()
            self.log_info("No active story - items list cleared")
            return
        
        try:
            # Get all items for this story
            items = db_manager.get_all_records(
                self.current_story_id, 'items', sort_by='name', order='ASC'
            )
            
            # Clear list
            self.item_list.clear()
            self.items_list_data = items
            
            # Populate list
            for item_data in items:
                item_type = item_data.get('type') or 'Item'
                item_rarity = item_data.get('rarity') or ''
                rarity_emoji = self._get_rarity_emoji(item_rarity)
                
                list_item = QListWidgetItem(
                    f"{rarity_emoji}{item_data.get('name')} ({item_type})"
                )
                list_item.setData(Qt.UserRole, item_data.get('id'))
                self.item_list.addItem(list_item)
            
            self.log_info(f"Loaded {len(items)} items for story {self.current_story_id}")
            
        except Exception as e:
            self.log_error(f"Error loading items: {e}")
            self.show_error(f"Failed to load items: {str(e)}")
    
    def _get_rarity_emoji(self, rarity: str) -> str:
        """Get emoji prefix for item rarity"""
        rarity_map = {
            'Legendary': '🌟',
            'Mythical': '✨',
            'Unique': '💎',
            'Epic': '🔮',
            'Rare': '⭐',
            'Uncommon': '🗡️',
            'Common': '⚔️',
        }
        return rarity_map.get(rarity, '🗡️') + ' '
    
    def save_data(self):
        """Save current item"""
        if not self.validate_input():
            return
        
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            # Gather form data
            item_data = {
                'story_id': self.current_story_id,
                'name': self.name_input.text().strip(),
                'type': self.type_input.currentText(),
                'category': self.category_input.currentText(),
                'rarity': self.rarity_input.currentText(),
                'description': self.description_input.toPlainText().strip(),
                'properties': self.properties_input.toPlainText().strip(),
                'powers': self.powers_input.toPlainText().strip(),
                'materials': self.materials_input.toPlainText().strip(),
                'creator': self.creator_input.text().strip(),
                'history': self.history_input.toPlainText().strip(),
                'current_owner': self.current_owner_input.text().strip(),
                'current_location': self.current_location_input.text().strip(),
                'value': self.value_input.text().strip(),
                'notes': self.notes_input.toPlainText().strip(),
            }
            
            if self.current_item_id:
                # Update existing item
                if db_manager.update_entity('items', self.current_item_id, self.current_story_id, item_data):
                    self.show_success(f"Item '{item_data['name']}' updated successfully!")
                    self.mark_saved()
                    self.load_data()
                    self.log_info(f"Item updated: {item_data['name']}")
                else:
                    self.show_error("Failed to update item")
            else:
                # Create new item
                item_id = db_manager.create_entity('items', self.current_story_id, item_data)
                
                if item_id:
                    self.show_success(f"Item '{item_data['name']}' created successfully!")
                    self.mark_saved()
                    self.current_item_id = item_id
                    self.load_data()
                    self.log_info(f"Item created: {item_data['name']}")
                else:
                    self.show_error("Failed to create item")
                    
        except Exception as e:
            self.log_error(f"Error saving item: {e}")
            self.show_error(f"Failed to save item: {str(e)}")
    
    def validate_input(self) -> bool:
        """Validate item input"""
        if not self.name_input.text().strip():
            self.show_error("Item name is required!")
            self.name_input.setFocus()
            return False
        return True
    
    def refresh(self):
        """Refresh items list"""
        self.load_data()