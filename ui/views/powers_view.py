"""
Powers View
Manage magic and power systems with story-scoped persistence
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QFormLayout, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt

from ui.views.base_view import BaseView
from database import db_manager


class PowersView(BaseView):
    """Power systems management view with story-scoped data"""
    
    def __init__(self):
        # Initialize attributes
        self.current_power_id = None
        self.powers_list_data = []
        
        # UI elements
        self.power_list = None
        self.search_input = None
        self.add_button = None
        self.delete_button = None
        
        # Power details form fields
        self.name_input = None
        self.system_name_input = None
        self.description_input = None
        self.rules_input = None
        self.limitations_input = None
        self.progression_input = None
        self.rare_abilities_input = None
        self.cost_system_input = None
        self.save_button = None
        
        self.details_widget = None
        self.no_selection_label = None
        
        super().__init__()
        self.view_name = "Power Systems"
    
    def setup_ui(self):
        """Initialize the powers view UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - power list
        left_panel = self._create_power_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - power details
        right_panel = self._create_power_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def _create_power_list_panel(self):
        """Create the power list panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("Power Systems")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search power systems...")
        self.search_input.textChanged.connect(self._filter_powers)
        layout.addWidget(self.search_input)
        
        # Power list
        self.power_list = QListWidget()
        self.power_list.itemClicked.connect(self._on_power_selected)
        layout.addWidget(self.power_list)
        
        # Add button
        self.add_button = QPushButton("➕ Add New Power System")
        self.add_button.clicked.connect(self._add_power)
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
    
    def _create_power_details_panel(self):
        """Create the power details panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.no_selection_label = QLabel("Select a power system to view details\nor create a new system to get started")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 16px; color: rgba(255, 255, 255, 0.5);")
        
        self.details_widget = self._create_details_form()
        self.details_widget.hide()
        
        layout.addWidget(self.no_selection_label)
        layout.addWidget(self.details_widget)
        
        panel.setLayout(layout)
        return panel
    
    def _create_details_form(self):
        """Create power details form"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Power System Details")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self._delete_power)
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
        self.name_input.setPlaceholderText("Power/ability name")
        self.name_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("Name *:", self.name_input)
        
        self.system_name_input = QLineEdit()
        self.system_name_input.setPlaceholderText("e.g., Elemental Magic, Psychic Powers")
        self.system_name_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("System Name:", self.system_name_input)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        
        desc_help = QLabel("Explain what this power system is and how it works in your world.")
        desc_help.setWordWrap(True)
        desc_help.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 5px;")
        desc_layout.addWidget(desc_help)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Describe the power system...")
        self.description_input.setMinimumHeight(120)
        self.description_input.textChanged.connect(self.mark_modified)
        desc_layout.addWidget(self.description_input)
        
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # Rules & Mechanics
        rules_group = QGroupBox("Rules & Mechanics")
        rules_layout = QVBoxLayout()
        
        rules_help = QLabel("How does this power system work? What are the core rules and mechanics?")
        rules_help.setWordWrap(True)
        rules_help.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 5px;")
        rules_layout.addWidget(rules_help)
        
        self.rules_input = QTextEdit()
        self.rules_input.setPlaceholderText("Define the rules and mechanics of this power system...")
        self.rules_input.setMinimumHeight(120)
        self.rules_input.textChanged.connect(self.mark_modified)
        rules_layout.addWidget(self.rules_input)
        
        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)
        
        # Limitations
        limitations_group = QGroupBox("Limitations & Weaknesses")
        limitations_layout = QVBoxLayout()
        
        limitations_help = QLabel("What are the limits? What can't this power do? What are its weaknesses?")
        limitations_help.setWordWrap(True)
        limitations_help.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 5px;")
        limitations_layout.addWidget(limitations_help)
        
        self.limitations_input = QTextEdit()
        self.limitations_input.setPlaceholderText("Describe limitations and weaknesses...")
        self.limitations_input.setMaximumHeight(100)
        self.limitations_input.textChanged.connect(self.mark_modified)
        limitations_layout.addWidget(self.limitations_input)
        
        limitations_group.setLayout(limitations_layout)
        layout.addWidget(limitations_group)
        
        # Progression System
        progression_group = QGroupBox("Progression System")
        progression_layout = QVBoxLayout()
        
        progression_help = QLabel("How do users of this power grow stronger? Levels, training, tiers?")
        progression_help.setWordWrap(True)
        progression_help.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 5px;")
        progression_layout.addWidget(progression_help)
        
        self.progression_input = QTextEdit()
        self.progression_input.setPlaceholderText("Describe how power users progress and grow...")
        self.progression_input.setMaximumHeight(100)
        self.progression_input.textChanged.connect(self.mark_modified)
        progression_layout.addWidget(self.progression_input)
        
        progression_group.setLayout(progression_layout)
        layout.addWidget(progression_group)
        
        # Rare/Advanced Abilities
        rare_group = QGroupBox("Rare & Advanced Abilities")
        rare_layout = QVBoxLayout()
        
        rare_help = QLabel("What are the most powerful or rare abilities in this system?")
        rare_help.setWordWrap(True)
        rare_help.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 5px;")
        rare_layout.addWidget(rare_help)
        
        self.rare_abilities_input = QTextEdit()
        self.rare_abilities_input.setPlaceholderText("List rare or advanced abilities...")
        self.rare_abilities_input.setMaximumHeight(100)
        self.rare_abilities_input.textChanged.connect(self.mark_modified)
        rare_layout.addWidget(self.rare_abilities_input)
        
        rare_group.setLayout(rare_layout)
        layout.addWidget(rare_group)
        
        # Cost System
        cost_group = QGroupBox("Cost & Resource System")
        cost_layout = QVBoxLayout()
        
        cost_help = QLabel("What does it cost to use these powers? Mana, stamina, life force, etc.?")
        cost_help.setWordWrap(True)
        cost_help.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 5px;")
        cost_layout.addWidget(cost_help)
        
        self.cost_system_input = QTextEdit()
        self.cost_system_input.setPlaceholderText("Describe the cost or resource system...")
        self.cost_system_input.setMaximumHeight(100)
        self.cost_system_input.textChanged.connect(self.mark_modified)
        cost_layout.addWidget(self.cost_system_input)
        
        cost_group.setLayout(cost_layout)
        layout.addWidget(cost_group)
        
        # Save button
        self.save_button = QPushButton("💾 Save Power System")
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
        """Clear the power system detail form and reset to initial state"""
        if self.details_widget:
            self.details_widget.hide()
        
        if self.no_selection_label:
            self.no_selection_label.show()
        
        self.current_power_id = None
        self.mark_saved()
        self.log_info("Powers view: Form cleared")

    def _filter_powers(self):
        """Filter power list based on search"""
        search_term = self.search_input.text().lower()
        
        for i in range(self.power_list.count()):
            item = self.power_list.item(i)
            item_text = item.text().lower()
            item.setHidden(search_term not in item_text)
    
    def _on_power_selected(self, item):
        """Handle power selection"""
        power_id = item.data(Qt.UserRole)
        self._load_power(power_id)
    
    def _load_power(self, power_id):
        """Load power data into form"""
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            power_data = db_manager.get_entity('power_systems', power_id, self.current_story_id)
            
            if not power_data:
                self.show_error("Power system not found")
                return
            
            self.current_power_id = power_id
            
            # Show details panel
            self.no_selection_label.hide()
            self.details_widget.show()
            
            # Populate form
            self.name_input.setText(power_data.get('name', ''))
            self.system_name_input.setText(power_data.get('system_name', ''))
            self.description_input.setPlainText(power_data.get('description', ''))
            self.rules_input.setPlainText(power_data.get('rules', ''))
            self.limitations_input.setPlainText(power_data.get('limitations', ''))
            self.progression_input.setPlainText(power_data.get('progression_system', ''))
            self.rare_abilities_input.setPlainText(power_data.get('rare_abilities', ''))
            self.cost_system_input.setPlainText(power_data.get('cost_system', ''))
            
            self.mark_saved()
            self.log_info(f"Loaded power system: {power_data.get('name')}")
            
        except Exception as e:
            self.log_error(f"Error loading power system: {e}")
            self.show_error(f"Failed to load power system: {str(e)}")
    
    def _add_power(self):
        """Add new power system"""
        if not self.current_story_id:
            self.show_warning("Please select a story first")
            return
        
        # Clear form
        self.current_power_id = None
        self.no_selection_label.hide()
        self.details_widget.show()
        
        self.name_input.clear()
        self.system_name_input.clear()
        self.description_input.clear()
        self.rules_input.clear()
        self.limitations_input.clear()
        self.progression_input.clear()
        self.rare_abilities_input.clear()
        self.cost_system_input.clear()
        
        self.name_input.setFocus()
        self.mark_saved()
        self.log_info("Creating new power system")
    
    def _delete_power(self):
        """Delete current power system"""
        if not self.current_power_id:
            return
        
        if not self.confirm_action("Delete Power System", "Are you sure you want to delete this power system?"):
            return
        
        try:
            if db_manager.delete_entity('power_systems', self.current_power_id, self.current_story_id):
                self.show_success("Power system deleted successfully!")
                self.details_widget.hide()
                self.no_selection_label.show()
                self.current_power_id = None
                self.load_data()
                self.log_info("Power system deleted")
            else:
                self.show_error("Failed to delete power system")
                
        except Exception as e:
            self.log_error(f"Error deleting power system: {e}")
            self.show_error(f"Failed to delete power system: {str(e)}")
    
    def load_data(self):
        """Load power systems for the current story"""
        if not self.current_story_id:
            self.power_list.clear()
            self.log_info("No active story - powers cleared")
            return
        
        try:
            # Get all power systems for this story
            powers = db_manager.get_entities_by_story('power_systems', self.current_story_id, 'name ASC')
            
            # Clear list
            self.power_list.clear()
            self.powers_list_data = powers
            
            # Populate list
            for power in powers:
                name = power.get('name', 'Unnamed')
                system = power.get('system_name', '')
                
                if system:
                    item_text = f"{name} - {system}"
                else:
                    item_text = name
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, power.get('id'))
                self.power_list.addItem(item)
            
            self.log_info(f"Loaded {len(powers)} power systems for story {self.current_story_id}")
            
        except Exception as e:
            self.log_error(f"Error loading power systems: {e}")
            self.show_error(f"Failed to load power systems: {str(e)}")
    
    def save_data(self):
        """Save current power system"""
        if not self.validate_input():
            return
        
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        try:
            # Gather form data
            data = {
                'name': self.name_input.text().strip(),
                'system_name': self.system_name_input.text().strip(),
                'description': self.description_input.toPlainText().strip(),
                'rules': self.rules_input.toPlainText().strip(),
                'limitations': self.limitations_input.toPlainText().strip(),
                'progression_system': self.progression_input.toPlainText().strip(),
                'rare_abilities': self.rare_abilities_input.toPlainText().strip(),
                'cost_system': self.cost_system_input.toPlainText().strip()
            }
            
            if self.current_power_id:
                # Update existing power system
                if db_manager.update_entity('power_systems', self.current_power_id, self.current_story_id, data):
                    self.show_success(f"Power system '{data['name']}' updated successfully!")
                    self.mark_saved()
                    self.load_data()
                    self.log_info(f"Power system updated: {data['name']}")
                else:
                    self.show_error("Failed to update power system")
            else:
                # Create new power system
                power_id = db_manager.create_entity('power_systems', self.current_story_id, data)
                
                if power_id:
                    self.show_success(f"Power system '{data['name']}' created successfully!")
                    self.mark_saved()
                    self.current_power_id = power_id
                    self.load_data()
                    self.log_info(f"Power system created: {data['name']}")
                else:
                    self.show_error("Failed to create power system")
                    
        except Exception as e:
            self.log_error(f"Error saving power system: {e}")
            self.show_error(f"Failed to save power system: {str(e)}")
    
    def validate_input(self) -> bool:
        """Validate power system input"""
        if not self.name_input.text().strip():
            self.show_error("Power system name is required!")
            self.name_input.setFocus()
            return False
        return True
    
    def refresh(self):
        """Refresh power systems list"""
        self.load_data()