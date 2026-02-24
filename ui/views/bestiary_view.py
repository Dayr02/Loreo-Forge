"""
Bestiary View
Manage creatures and monsters with story-scoped persistence
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QFormLayout, QScrollArea, QWidget, QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt

from ui.views.base_view import BaseView
from database import db_manager


class BestiaryView(BaseView):
    """Bestiary management view with story-scoped data"""
    
    def __init__(self):
        # Initialize attributes
        self.current_creature_id = None
        self.creatures_list_data = []
        
        # UI elements
        self.creature_list = None
        self.search_input = None
        self.category_filter = None
        self.add_button = None
        self.delete_button = None
        
        # Creature details form fields
        self.name_input = None
        self.category_input = None
        self.type_input = None
        self.threat_level_input = None
        self.rarity_input = None
        self.size_input = None
        self.habitat_input = None
        self.lifespan_input = None
        self.appearance_input = None
        self.behavior_input = None
        self.abilities_input = None
        self.weaknesses_input = None
        self.lore_input = None
        self.is_sentient_check = None
        self.is_magical_check = None
        self.is_hostile_check = None
        self.first_appearance_input = None
        self.save_button = None
        
        self.details_widget = None
        self.no_selection_label = None
        
        super().__init__()
        self.view_name = "Bestiary"
    
    def setup_ui(self):
        """Initialize the bestiary view UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - creature list
        left_panel = self._create_creature_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - creature details
        right_panel = self._create_creature_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def _create_creature_list_panel(self):
        """Create the creature list panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("Bestiary")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search creatures...")
        self.search_input.textChanged.connect(self._filter_creatures)
        layout.addWidget(self.search_input)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All", "Beast", "Monster", "Dragon", "Undead", "Elemental",
            "Demon", "Celestial", "Construct", "Aberration", "Other"
        ])
        self.category_filter.currentTextChanged.connect(self._filter_creatures)
        filter_layout.addWidget(self.category_filter)
        layout.addLayout(filter_layout)
        
        # Creature list
        self.creature_list = QListWidget()
        self.creature_list.itemClicked.connect(self._on_creature_selected)
        layout.addWidget(self.creature_list)
        
        # Add button
        self.add_button = QPushButton("➕ Add New Creature")
        self.add_button.clicked.connect(self._add_creature)
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
    
    def _create_creature_details_panel(self):
        """Create the creature details panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.no_selection_label = QLabel("Select a creature to view details\nor create a new creature to get started")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 16px; color: rgba(255, 255, 255, 0.5);")
        
        self.details_widget = self._create_details_form()
        self.details_widget.hide()
        
        layout.addWidget(self.no_selection_label)
        layout.addWidget(self.details_widget)
        
        panel.setLayout(layout)
        return panel
    
    def _create_details_form(self):
        """Create creature details form"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Creature Details")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self._delete_creature)
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
        self.name_input.setPlaceholderText("Creature name")
        self.name_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("Name *:", self.name_input)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems([
            "Beast", "Monster", "Dragon", "Undead", "Elemental",
            "Demon", "Celestial", "Construct", "Aberration", "Other"
        ])
        self.category_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Category *:", self.category_input)
        
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("e.g., Fire Dragon, Shadow Wolf")
        self.type_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("Type:", self.type_input)
        
        self.threat_level_input = QComboBox()
        self.threat_level_input.addItems([
            "Harmless", "Low", "Moderate", "High", "Extreme", "Legendary"
        ])
        self.threat_level_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Threat Level:", self.threat_level_input)
        
        self.rarity_input = QComboBox()
        self.rarity_input.addItems([
            "Common", "Uncommon", "Rare", "Very Rare", "Legendary", "Unique"
        ])
        self.rarity_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Rarity:", self.rarity_input)
        
        self.size_input = QComboBox()
        self.size_input.addItems([
            "Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"
        ])
        self.size_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Size:", self.size_input)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Habitat & Lifespan
        environment_group = QGroupBox("Environment")
        environment_layout = QFormLayout()
        
        self.habitat_input = QLineEdit()
        self.habitat_input.setPlaceholderText("Forests, mountains, caves...")
        self.habitat_input.textChanged.connect(self.mark_modified)
        environment_layout.addRow("Habitat:", self.habitat_input)
        
        self.lifespan_input = QLineEdit()
        self.lifespan_input.setPlaceholderText("e.g., 50 years, immortal")
        self.lifespan_input.textChanged.connect(self.mark_modified)
        environment_layout.addRow("Lifespan:", self.lifespan_input)
        
        environment_group.setLayout(environment_layout)
        layout.addWidget(environment_group)
        
        # Characteristics
        characteristics_layout = QHBoxLayout()
        
        self.is_sentient_check = QCheckBox("Sentient")
        self.is_sentient_check.toggled.connect(self.mark_modified)
        characteristics_layout.addWidget(self.is_sentient_check)
        
        self.is_magical_check = QCheckBox("Magical")
        self.is_magical_check.toggled.connect(self.mark_modified)
        characteristics_layout.addWidget(self.is_magical_check)
        
        self.is_hostile_check = QCheckBox("Hostile")
        self.is_hostile_check.toggled.connect(self.mark_modified)
        characteristics_layout.addWidget(self.is_hostile_check)
        
        characteristics_layout.addStretch()
        layout.addLayout(characteristics_layout)
        
        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        self.appearance_input = QTextEdit()
        self.appearance_input.setPlaceholderText("Physical description of the creature...")
        self.appearance_input.setMaximumHeight(100)
        self.appearance_input.textChanged.connect(self.mark_modified)
        appearance_layout.addWidget(self.appearance_input)
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Behavior
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        self.behavior_input = QTextEdit()
        self.behavior_input.setPlaceholderText("How does this creature act? Temperament, instincts...")
        self.behavior_input.setMaximumHeight(100)
        self.behavior_input.textChanged.connect(self.mark_modified)
        behavior_layout.addWidget(self.behavior_input)
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        # Abilities
        abilities_group = QGroupBox("Abilities & Powers")
        abilities_layout = QVBoxLayout()
        self.abilities_input = QTextEdit()
        self.abilities_input.setPlaceholderText("Special abilities, magical powers, natural weapons...")
        self.abilities_input.setMaximumHeight(100)
        self.abilities_input.textChanged.connect(self.mark_modified)
        abilities_layout.addWidget(self.abilities_input)
        abilities_group.setLayout(abilities_layout)
        layout.addWidget(abilities_group)
        
        # Weaknesses
        weaknesses_group = QGroupBox("Weaknesses")
        weaknesses_layout = QVBoxLayout()
        self.weaknesses_input = QTextEdit()
        self.weaknesses_input.setPlaceholderText("Vulnerabilities, weaknesses, how to defeat...")
        self.weaknesses_input.setMaximumHeight(80)
        self.weaknesses_input.textChanged.connect(self.mark_modified)
        weaknesses_layout.addWidget(self.weaknesses_input)
        weaknesses_group.setLayout(weaknesses_layout)
        layout.addWidget(weaknesses_group)
        
        # Lore
        lore_group = QGroupBox("Lore & Background")
        lore_layout = QVBoxLayout()
        self.lore_input = QTextEdit()
        self.lore_input.setPlaceholderText("Origin, mythology, cultural significance...")
        self.lore_input.setMaximumHeight(100)
        self.lore_input.textChanged.connect(self.mark_modified)
        lore_layout.addWidget(self.lore_input)
        lore_group.setLayout(lore_layout)
        layout.addWidget(lore_group)
        
        # Story Integration
        story_group = QGroupBox("Story Integration")
        story_layout = QFormLayout()
        
        self.first_appearance_input = QSpinBox()
        self.first_appearance_input.setRange(0, 9999)
        self.first_appearance_input.setSpecialValueText("Not yet appeared")
        self.first_appearance_input.valueChanged.connect(self.mark_modified)
        story_layout.addRow("First Appearance (Chapter):", self.first_appearance_input)
        
        story_group.setLayout(story_layout)
        layout.addWidget(story_group)
        
        # Save button
        self.save_button = QPushButton("💾 Save Creature")
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
        """Clear the creature detail form and reset to initial state"""
        if self.details_widget:
            self.details_widget.hide()
        
        if self.no_selection_label:
            self.no_selection_label.show()
        
        self.current_creature_id = None
        self.mark_saved()
        self.log_info("Bestiary view: Form cleared")

    def _filter_creatures(self):
        """Filter creature list based on search and category"""
        search_term = self.search_input.text().lower()
        category = self.category_filter.currentText()
        
        for i in range(self.creature_list.count()):
            item = self.creature_list.item(i)
            item_data = item.data(Qt.UserRole + 1)
            
            # Check search term
            name_match = search_term in item.text().lower()
            
            # Check category
            category_match = (category == "All" or 
                            (item_data and item_data.get('category') == category))
            
            item.setHidden(not (name_match and category_match))
    
    def _on_creature_selected(self, item):
        """Handle creature selection"""
        creature_id = item.data(Qt.UserRole)
        self._load_creature(creature_id)
    
    def _load_creature(self, creature_id):
            """Load creature data into form"""
            if not self.current_story_id:
                self.show_warning("No active story selected")
                return
            
            try:
                # Use Creature model instead of db_manager
                from models.creature import Creature
                
                creature = Creature.get_by_id(self.current_story_id, creature_id)
                
                if not creature:
                    self.show_error("Creature not found")
                    return
                
                self.current_creature_id = creature_id
                
                # Show details panel
                self.no_selection_label.hide()
                self.details_widget.show()
                
                # Populate form with safe defaults
                self.name_input.setText(creature.name or "")
                
                # Set category
                category = creature.category or 'Beast'
                cat_index = self.category_input.findText(category)
                if cat_index >= 0:
                    self.category_input.setCurrentIndex(cat_index)
                else:
                    self.category_input.setEditText(category)
                
                self.type_input.setText(creature.type or "")
                
                # Set threat level with safe default
                threat = creature.threat_level or 'Moderate'
                threat_index = self.threat_level_input.findText(threat)
                if threat_index >= 0:
                    self.threat_level_input.setCurrentIndex(threat_index)
                else:
                    self.threat_level_input.setCurrentIndex(2)  # Default to Moderate
                
                # Set rarity with safe default
                rarity = creature.rarity or 'Common'
                rarity_index = self.rarity_input.findText(rarity)
                if rarity_index >= 0:
                    self.rarity_input.setCurrentIndex(rarity_index)
                else:
                    self.rarity_input.setCurrentIndex(0)  # Default to Common
                
                # Set size with safe default
                size = creature.size or 'Medium'
                size_index = self.size_input.findText(size)
                if size_index >= 0:
                    self.size_input.setCurrentIndex(size_index)
                else:
                    self.size_input.setCurrentIndex(2)  # Default to Medium
                
                self.habitat_input.setText(creature.habitat or "")
                self.lifespan_input.setText(creature.lifespan or "")
                
                self.is_sentient_check.setChecked(creature.is_sentient)
                self.is_magical_check.setChecked(creature.is_magical)
                self.is_hostile_check.setChecked(creature.is_hostile)
                
                self.appearance_input.setPlainText(creature.appearance or "")
                self.behavior_input.setPlainText(creature.behavior or "")
                self.abilities_input.setPlainText(creature.abilities or "")
                self.weaknesses_input.setPlainText(creature.weaknesses or "")
                self.lore_input.setPlainText(creature.lore or "")
                
                # Handle None for first_appearance_chapter safely
                first_appearance = creature.first_appearance_chapter
                if first_appearance is not None:
                    self.first_appearance_input.setValue(int(first_appearance))
                else:
                    self.first_appearance_input.setValue(0)
                
                self.mark_saved()
                self.log_info(f"Loaded creature: {creature.name}")
                
            except Exception as e:
                self.log_error(f"Error loading creature: {e}")
                self.show_error(f"Failed to load creature: {str(e)}")
                
            except Exception as e:
                self.log_error(f"Error loading creature: {e}")
                self.show_error(f"Failed to load creature: {str(e)}")
    
    def _add_creature(self):
        """Add new creature"""
        if not self.current_story_id:
            self.show_warning("Please select a story first")
            return
        
        # Clear form
        self.current_creature_id = None
        self.no_selection_label.hide()
        self.details_widget.show()
        
        self.name_input.clear()
        self.category_input.setCurrentIndex(0)
        self.type_input.clear()
        self.threat_level_input.setCurrentIndex(2)
        self.rarity_input.setCurrentIndex(0)
        self.size_input.setCurrentIndex(2)
        self.habitat_input.clear()
        self.lifespan_input.clear()
        self.is_sentient_check.setChecked(False)
        self.is_magical_check.setChecked(False)
        self.is_hostile_check.setChecked(False)
        self.appearance_input.clear()
        self.behavior_input.clear()
        self.abilities_input.clear()
        self.weaknesses_input.clear()
        self.lore_input.clear()
        self.first_appearance_input.setValue(0)
        
        self.name_input.setFocus()
        self.mark_saved()
        self.log_info("Creating new creature")
    
    def _delete_creature(self):
        """Delete current creature"""
        if not self.current_creature_id:
            return
        
        if not self.confirm_action("Delete Creature", "Are you sure you want to delete this creature?"):
            return
        
        try:
            if db_manager.delete_entity('bestiary', self.current_creature_id, self.current_story_id):
                self.show_success("Creature deleted successfully!")
                self.details_widget.hide()
                self.no_selection_label.show()
                self.current_creature_id = None
                self.load_data()
                self.log_info("Creature deleted")
            else:
                self.show_error("Failed to delete creature")
                
        except Exception as e:
            self.log_error(f"Error deleting creature: {e}")
            self.show_error(f"Failed to delete creature: {str(e)}")
    
    def load_data(self):
        """Load creatures for the current story"""
        if not self.current_story_id:
            self.creature_list.clear()
            self.log_info("No active story - bestiary cleared")
            return
        
        try:
            from models.creature import Creature
            
            # Get all creatures for this story
            creatures = Creature.get_all(self.current_story_id, sort_by='name', order='ASC')
            
            # Clear list
            self.creature_list.clear()
            self.creatures_list_data = creatures
            
            # Populate list
            for creature in creatures:
                name = creature.name
                category = creature.category or 'Unknown'
                item = QListWidgetItem(f"{name} ({category})")
                item.setData(Qt.UserRole, creature.id)
                self.creature_list.addItem(item)
            
            self.log_info(f"Loaded {len(creatures)} creatures for story {self.current_story_id}")
            
        except Exception as e:
            self.log_error(f"Error loading creatures: {e}")
            self.show_error(f"Failed to load creatures: {str(e)}")
    
    def save_data(self):
        """Save current creature"""
        if not self.validate_input():
            return
        
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            from models.creature import Creature
            
            # Gather form data
            name = self.name_input.text().strip()
            category = self.category_input.currentText()
            creature_type = self.type_input.text().strip()
            threat_level = self.threat_level_input.currentText()
            rarity = self.rarity_input.currentText()
            size = self.size_input.currentText()
            habitat = self.habitat_input.text().strip()
            lifespan = self.lifespan_input.text().strip()
            appearance = self.appearance_input.toPlainText().strip()
            behavior = self.behavior_input.toPlainText().strip()
            abilities = self.abilities_input.toPlainText().strip()
            weaknesses = self.weaknesses_input.toPlainText().strip()
            lore = self.lore_input.toPlainText().strip()
            is_sentient = self.is_sentient_check.isChecked()
            is_magical = self.is_magical_check.isChecked()
            is_hostile = self.is_hostile_check.isChecked()
            first_appearance = self.first_appearance_input.value() if self.first_appearance_input.value() > 0 else None
            
            if self.current_creature_id:
                # Update existing creature
                creature = Creature.get_by_id(self.current_story_id, self.current_creature_id)
                
                if creature:
                    creature.name = name
                    creature.category = category
                    creature.type = creature_type
                    creature.threat_level = threat_level
                    creature.rarity = rarity
                    creature.size = size
                    creature.habitat = habitat
                    creature.lifespan = lifespan
                    creature.appearance = appearance
                    creature.behavior = behavior
                    creature.abilities = abilities
                    creature.weaknesses = weaknesses
                    creature.lore = lore
                    creature.is_sentient = is_sentient
                    creature.is_magical = is_magical
                    creature.is_hostile = is_hostile
                    creature.first_appearance_chapter = first_appearance
                    
                    if creature.save():
                        self.show_success(f"Creature '{name}' updated successfully!")
                        self.mark_saved()
                        self.load_data()
                        self.log_info(f"Creature updated: {name}")
                    else:
                        self.show_error("Failed to update creature")
                else:
                    self.show_error("Creature not found")
            else:
                # Create new creature
                creature = Creature(
                    self.current_story_id,
                    name=name,
                    category=category,
                    type=creature_type,
                    threat_level=threat_level,
                    rarity=rarity,
                    size=size,
                    habitat=habitat,
                    lifespan=lifespan,
                    appearance=appearance,
                    behavior=behavior,
                    abilities=abilities,
                    weaknesses=weaknesses,
                    lore=lore,
                    is_sentient=is_sentient,
                    is_magical=is_magical,
                    is_hostile=is_hostile,
                    first_appearance_chapter=first_appearance
                )
                
                if creature.save():
                    self.show_success(f"Creature '{name}' created successfully!")
                    self.mark_saved()
                    self.current_creature_id = creature.id
                    self.load_data()
                    self.log_info(f"Creature created: {name}")
                else:
                    self.show_error("Failed to create creature")
                    
        except Exception as e:
            self.log_error(f"Error saving creature: {e}")
            self.show_error(f"Failed to save creature: {str(e)}")
    
    def _delete_creature(self):
        """Delete current creature"""
        if not self.current_creature_id:
            return
        
        if not self.confirm_action("Delete Creature", "Are you sure you want to delete this creature?"):
            return
        
        try:
            from models.creature import Creature
            
            creature = Creature.get_by_id(self.current_story_id, self.current_creature_id)
            
            if creature and creature.delete():
                self.show_success("Creature deleted successfully!")
                self.details_widget.hide()
                self.no_selection_label.show()
                self.current_creature_id = None
                self.load_data()
                self.log_info("Creature deleted")
            else:
                self.show_error("Failed to delete creature")
                
        except Exception as e:
            self.log_error(f"Error deleting creature: {e}")
            self.show_error(f"Failed to delete creature: {str(e)}")
    
    def validate_input(self) -> bool:
        """Validate creature input"""
        if not self.name_input.text().strip():
            self.show_error("Creature name is required!")
            self.name_input.setFocus()
            return False
        return True
    
    def refresh(self):
        """Refresh creatures list"""
        self.load_data()