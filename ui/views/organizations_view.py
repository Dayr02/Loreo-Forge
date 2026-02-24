"""
Organizations View
Manage factions and organizations with story-scoped persistence

"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QGroupBox, QFormLayout, QScrollArea, QWidget, QSpinBox,
)
from PyQt5.QtCore import Qt

from ui.views.base_view import BaseView
from database import db_manager


class OrganizationsView(BaseView):
    """Organizations and factions management view with story-scoped data"""

    def __init__(self):
        self.current_org_id   = None
        self.orgs_list_data   = []

        # UI elements (set in setup_ui)
        self.org_list         = None
        self.search_input     = None
        self.add_button       = None
        self.delete_button    = None

        # Form fields (set in _create_details_form)
        self.name_input        = None
        self.type_input        = None
        self.member_count_input = None
        self.description_input = None
        self.history_input     = None
        self.goals_input       = None
        self.structure_input   = None
        self.leadership_input  = None
        self.members_input     = None
        self.territory_input   = None
        self.resources_input   = None
        self.allies_input      = None
        self.rivals_input      = None
        self.save_button       = None

        self.details_widget      = None
        self.no_selection_label  = None

        super().__init__()
        self.view_name = "Organizations"

    # =========================================================================
    # UI CONSTRUCTION
    # =========================================================================

    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._create_org_list_panel())
        splitter.addWidget(self._create_org_details_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def _create_org_list_panel(self):
        panel  = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel("Organizations & Factions")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search organizations...")
        self.search_input.textChanged.connect(self._filter_orgs)
        layout.addWidget(self.search_input)

        self.org_list = QListWidget()
        self.org_list.itemClicked.connect(self._on_org_selected)
        layout.addWidget(self.org_list)

        self.add_button = QPushButton("➕ Add New Organization")
        self.add_button.clicked.connect(self._add_org)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.8);
                color: white; border: none; border-radius: 5px;
                padding: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(76, 175, 80, 1.0); }
        """)
        layout.addWidget(self.add_button)

        panel.setLayout(layout)
        return panel

    def _create_org_details_panel(self):
        panel  = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.no_selection_label = QLabel(
            "Select an organization to view details\n"
            "or create a new organization to get started"
        )
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet(
            "font-size: 16px; color: rgba(255, 255, 255, 0.5);"
        )

        self.details_widget = self._create_details_form()
        self.details_widget.hide()

        layout.addWidget(self.no_selection_label)
        layout.addWidget(self.details_widget)
        panel.setLayout(layout)
        return panel

    def _create_details_form(self):
        widget  = QWidget()
        scroll  = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        layout  = QVBoxLayout()
        layout.setSpacing(15)

        # ── Header + Delete ──────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        header = QLabel("Organization Details")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self._delete_org)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.8);
                color: white; border: none; border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: rgba(244, 67, 54, 1.0); }
        """)
        header_layout.addWidget(self.delete_button)
        layout.addLayout(header_layout)

        # ── Basic Information ────────────────────────────────────────────────
        basic_group  = QGroupBox("Basic Information")
        basic_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Organization name")
        self.name_input.textChanged.connect(self.mark_modified)
        basic_layout.addRow("Name *:", self.name_input)

        self.type_input = QComboBox()
        self.type_input.setEditable(True)
        self.type_input.addItems([
            "Guild", "Kingdom", "Empire", "Military Order", "Religious Order",
            "Secret Society", "Trading Company", "Criminal Syndicate",
            "Rebel Group", "Academy", "Council", "Tribe", "Other",
        ])
        self.type_input.currentTextChanged.connect(self.mark_modified)
        basic_layout.addRow("Type:", self.type_input)

        self.member_count_input = QSpinBox()
        self.member_count_input.setRange(0, 999_999)
        self.member_count_input.setSpecialValueText("Unknown")
        self.member_count_input.valueChanged.connect(self.mark_modified)
        basic_layout.addRow("Member Count:", self.member_count_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # ── Remaining text fields (helper keeps DRY) ─────────────────────────
        def _text_group(title, placeholder, attr, max_h=100):
            grp = QGroupBox(title)
            vbl = QVBoxLayout()
            te  = QTextEdit()
            te.setPlaceholderText(placeholder)
            te.setMaximumHeight(max_h)
            te.textChanged.connect(self.mark_modified)
            vbl.addWidget(te)
            grp.setLayout(vbl)
            setattr(self, attr, te)
            return grp

        layout.addWidget(_text_group(
            "Description",
            "What is this organization? What do they do?",
            "description_input", 100,
        ))
        layout.addWidget(_text_group(
            "History & Origins",
            "How was this organization founded? What's its history?",
            "history_input", 100,
        ))
        layout.addWidget(_text_group(
            "Goals & Motivations",
            "What are this organization's goals and motivations?",
            "goals_input", 80,
        ))
        layout.addWidget(_text_group(
            "Structure & Hierarchy",
            "How is the organization structured? Ranks, hierarchy, etc.",
            "structure_input", 100,
        ))
        layout.addWidget(_text_group(
            "Leadership",
            "Who leads this organization? Key figures and their roles.",
            "leadership_input", 80,
        ))
        layout.addWidget(_text_group(
            "Notable Members",
            "Key members and their roles within the organization...",
            "members_input", 80,
        ))
        layout.addWidget(_text_group(
            "Territory & Influence",
            "What regions or areas does this organization control or influence?",
            "territory_input", 80,
        ))
        layout.addWidget(_text_group(
            "Resources & Assets",
            "What resources, wealth, or assets does the organization possess?",
            "resources_input", 80,
        ))
        layout.addWidget(_text_group(
            "Allies & Partnerships",
            "Who are this organization's allies and partners?",
            "allies_input", 60,
        ))
        layout.addWidget(_text_group(
            "Rivals & Enemies",
            "Who opposes this organization? Rivals and enemies.",
            "rivals_input", 60,
        ))

        # ── Save ─────────────────────────────────────────────────────────────
        self.save_button = QPushButton("💾 Save Organization")
        self.save_button.setMinimumHeight(40)
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.8);
                color: white; border: none; border-radius: 5px;
                font-size: 14px; font-weight: bold; padding: 10px;
            }
            QPushButton:hover { background-color: rgba(76, 175, 80, 1.0); }
        """)
        layout.addWidget(self.save_button)

        content.setLayout(layout)
        scroll.setWidget(content)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        widget.setLayout(main_layout)
        return widget

    # =========================================================================
    # FORM HELPERS
    # =========================================================================

    def _clear_form_fields(self):
        """
        Unconditionally reset every form field to its empty / default state.
        Called at the start of _load_org so that no previous org's values can
        bleed into the newly selected org's display.
        """
        self.name_input.clear()
        self.type_input.setCurrentIndex(0)
        self.member_count_input.setValue(0)
        self.description_input.clear()
        self.history_input.clear()
        self.goals_input.clear()
        self.structure_input.clear()
        self.leadership_input.clear()
        self.members_input.clear()
        self.territory_input.clear()
        self.resources_input.clear()
        self.allies_input.clear()
        self.rivals_input.clear()

    def clear_form(self):
        """Hide the details panel and reset state (called by main_window)."""
        if self.details_widget:
            self.details_widget.hide()
        if self.no_selection_label:
            self.no_selection_label.show()
        self.current_org_id = None
        self.mark_saved()
        self.log_info("Organizations view: Form cleared")

    # =========================================================================
    # LIST FILTERING
    # =========================================================================

    def _filter_orgs(self):
        search_term = self.search_input.text().lower()
        for i in range(self.org_list.count()):
            item = self.org_list.item(i)
            item.setHidden(search_term not in item.text().lower())

    # =========================================================================
    # LOAD
    # =========================================================================

    def _on_org_selected(self, item):
        self._load_org(item.data(Qt.UserRole))

    def _load_org(self, org_id):
        """Load a single organization into the form."""
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return

        try:
            org_data = db_manager.get_entity(
                'organizations', org_id, self.current_story_id
            )
            if not org_data:
                self.show_error("Organization not found")
                return

            self.current_org_id = org_id

            # ── Show panel ───────────────────────────────────────────────────
            self.no_selection_label.hide()
            self.details_widget.show()

            # ── FIX B: clear every widget BEFORE populating ──────────────────
            # Prevents values from the previously displayed org from remaining
            # visible in fields that the new org leaves empty.
            self._clear_form_fields()

            # ── Populate basic info ──────────────────────────────────────────
            self.name_input.setText(str(org_data.get('name') or ''))

            org_type  = str(org_data.get('type') or 'Guild')
            type_idx  = self.type_input.findText(org_type)
            if type_idx >= 0:
                self.type_input.setCurrentIndex(type_idx)
            else:
                self.type_input.setEditText(org_type)

            # ── FIX 2: guard against NULL member_count ───────────────────────
            # dict.get('member_count', 0) returns None (not 0) when the column
            # IS present in the row but its value is NULL.  'or 0' handles None.
            self.member_count_input.setValue(
                int(org_data.get('member_count') or 0)
            )

            # ── Populate text fields (FIX A: str() coercion) ─────────────────
            # db_manager previously treated members/allies/rivals as JSON and
            # could return Python lists here.  str(list or '') would still give
            # a readable string; but the real fix is in db_manager removing
            # those fields from the JSON list so they always arrive as str.
            # The str() + 'or ""' pattern is a belt-and-suspenders guard.
            def _s(val):
                """Return val as a plain string, '' for None/empty."""
                if val is None:
                    return ''
                if isinstance(val, list):
                    # Fallback: join list items if JSON deserialization sneaks through
                    return '\n'.join(str(v) for v in val)
                return str(val)

            self.description_input.setPlainText(_s(org_data.get('description')))
            self.history_input.setPlainText(_s(org_data.get('history')))
            self.goals_input.setPlainText(_s(org_data.get('goals')))
            self.structure_input.setPlainText(_s(org_data.get('structure')))
            self.leadership_input.setPlainText(_s(org_data.get('leadership')))
            self.members_input.setPlainText(_s(org_data.get('members')))
            self.territory_input.setPlainText(_s(org_data.get('territory')))
            self.resources_input.setPlainText(_s(org_data.get('resources')))
            self.allies_input.setPlainText(_s(org_data.get('allies')))
            self.rivals_input.setPlainText(_s(org_data.get('rivals')))

            self.mark_saved()
            self.log_info(f"Loaded organization: {org_data.get('name')}")

        except Exception as e:
            self.log_error(f"Error loading organization: {e}")
            self.show_error(f"Failed to load organization: {str(e)}")

    # =========================================================================
    # ADD / DELETE
    # =========================================================================

    def _add_org(self):
        if not self.current_story_id:
            self.show_warning("Please select a story first")
            return
        self.current_org_id = None
        self.no_selection_label.hide()
        self.details_widget.show()
        self._clear_form_fields()
        self.name_input.setFocus()
        self.mark_saved()
        self.log_info("Creating new organization")

    def _delete_org(self):
        if not self.current_org_id:
            return
        if not self.confirm_action(
            "Delete Organization",
            "Are you sure you want to delete this organization?",
        ):
            return
        try:
            if db_manager.delete_entity(
                'organizations', self.current_org_id, self.current_story_id
            ):
                self.show_success("Organization deleted successfully!")
                self.details_widget.hide()
                self.no_selection_label.show()
                self.current_org_id = None
                self.load_data()
            else:
                self.show_error("Failed to delete organization")
        except Exception as e:
            self.log_error(f"Error deleting organization: {e}")
            self.show_error(f"Failed to delete organization: {str(e)}")

    # =========================================================================
    # LOAD DATA (list)
    # =========================================================================

    def load_data(self):
        if not self.current_story_id:
            self.org_list.clear()
            return
        try:
            orgs = db_manager.get_entities_by_story(
                'organizations', self.current_story_id, 'name ASC'
            )
            self.org_list.clear()
            self.orgs_list_data = orgs
            for org in orgs:
                name     = org.get('name', 'Unnamed')
                org_type = org.get('type', 'Organization')
                item     = QListWidgetItem(f"{name} ({org_type})")
                item.setData(Qt.UserRole, org.get('id'))
                self.org_list.addItem(item)
            self.log_info(
                f"Loaded {len(orgs)} organizations for story {self.current_story_id}"
            )
        except Exception as e:
            self.log_error(f"Error loading organizations: {e}")
            self.show_error(f"Failed to load organizations: {str(e)}")

    # =========================================================================
    # SAVE
    # =========================================================================

    def save_data(self):
        if not self.validate_input():
            return
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        try:
            # member_count: store 0 as 0 (not None) so reload always gets an int
            data = {
                'name':         self.name_input.text().strip(),
                'type':         self.type_input.currentText(),
                'member_count': self.member_count_input.value(),
                'description':  self.description_input.toPlainText().strip(),
                'history':      self.history_input.toPlainText().strip(),
                'goals':        self.goals_input.toPlainText().strip(),
                'structure':    self.structure_input.toPlainText().strip(),
                'leadership':   self.leadership_input.toPlainText().strip(),
                'members':      self.members_input.toPlainText().strip(),
                'territory':    self.territory_input.toPlainText().strip(),
                'resources':    self.resources_input.toPlainText().strip(),
                'allies':       self.allies_input.toPlainText().strip(),
                'rivals':       self.rivals_input.toPlainText().strip(),
            }

            if self.current_org_id:
                if db_manager.update_entity(
                    'organizations', self.current_org_id,
                    self.current_story_id, data
                ):
                    self.show_success(f"Organization '{data['name']}' updated successfully!")
                    self.mark_saved()
                    self.load_data()
                    self.log_info(f"Organization updated: {data['name']}")
                else:
                    self.show_error("Failed to update organization")
            else:
                org_id = db_manager.create_entity(
                    'organizations', self.current_story_id, data
                )
                if org_id:
                    self.show_success(f"Organization '{data['name']}' created successfully!")
                    self.mark_saved()
                    self.current_org_id = org_id
                    self.load_data()
                    self.log_info(f"Organization created: {data['name']}")
                else:
                    self.show_error("Failed to create organization")

        except Exception as e:
            self.log_error(f"Error saving organization: {e}")
            self.show_error(f"Failed to save organization: {str(e)}")

    # =========================================================================
    # VALIDATION / REFRESH
    # =========================================================================

    def validate_input(self) -> bool:
        if not self.name_input.text().strip():
            self.show_error("Organization name is required!")
            self.name_input.setFocus()
            return False
        return True

    def refresh(self):
        self.load_data()