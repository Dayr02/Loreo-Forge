"""
Chapters List View
Browse, search, and manage chapters with story-scoped persistence
"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QWidget, QSplitter, QGroupBox, QFormLayout, QScrollArea, QCheckBox,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem, QSpinBox
)
from PyQt5.QtCore import Qt
from ui.views.base_view import BaseView
from models import Chapter
from database import db_manager


class ChaptersListView(BaseView):
    """
    Chapters list and management view with story-scoped data
    """
    
    def __init__(self):
        # Initialize all instance attributes BEFORE calling super().__init__()
        self.current_chapter_id = None
        self.chapters_data = []
        
        # Filter/search widgets
        self.search_input = None
        self.arc_filter = None
        self.pov_filter = None
        self.status_filter = None
        self.sort_combo = None
        self.view_mode_btn = None
        
        # Views
        self.table_view = None
        self.grid_view = None
        self.view_container = None
        
        # Details panel
        self.details_panel = None
        self.chapter_content = None
        self.edit_mode = False
        
        # Form fields
        self.chapter_number_input = None
        self.title_input = None
        self.summary_input = None
        self.plot_points_input = None
        self.mood_input = None
        self.notes_input = None
        self.pov_character_input = None
        self.arc_input = None
        self.status_input = None
        
        # Action buttons
        self.save_btn = None
        self.edit_btn = None
        self.create_version_btn = None
        self.regenerate_btn = None
        self.version_history_btn = None
        self.export_btn = None
        self.delete_btn = None
        
        # Bulk action elements
        self.bulk_export_btn = None
        self.bulk_delete_btn = None
        
        # Current state
        self.current_view_mode = 'list'  # 'list' or 'grid'
        
        # Now call parent init which will call setup_ui()
        super().__init__()
        
        # Set view properties
        self.view_name = "Chapters List"
        
    def setup_ui(self):
        """Set up the chapters list view UI"""
        layout = QVBoxLayout()
        
        # Top toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Chapter list
        list_panel = self._create_list_panel()
        splitter.addWidget(list_panel)
        
        # Right: Chapter details
        details_panel = self._create_details_panel()
        splitter.addWidget(details_panel)
        
        # Set initial sizes (60% list, 40% details)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        # Bottom: Bulk actions
        bulk_actions = self._create_bulk_actions()
        layout.addWidget(bulk_actions)
        
        self.setLayout(layout)
        
    def _create_toolbar(self):
        """Create the top toolbar with search and filters"""
        toolbar = QWidget()
        layout = QHBoxLayout()
        
        # Search
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search chapters...")
        self.search_input.textChanged.connect(self.filter_chapters)
        layout.addWidget(search_label)
        layout.addWidget(self.search_input)
        
        # Arc filter
        layout.addWidget(QLabel("Arc:"))
        self.arc_filter = QComboBox()
        self.arc_filter.addItems(['All'])
        self.arc_filter.currentTextChanged.connect(self.filter_chapters)
        layout.addWidget(self.arc_filter)
        
        # POV filter
        layout.addWidget(QLabel("POV:"))
        self.pov_filter = QComboBox()
        self.pov_filter.addItems(['All'])
        self.pov_filter.currentTextChanged.connect(self.filter_chapters)
        layout.addWidget(self.pov_filter)
        
        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(['All', 'Draft', 'Review', 'Final'])
        self.status_filter.currentTextChanged.connect(self.filter_chapters)
        layout.addWidget(self.status_filter)
        
        # Sort
        layout.addWidget(QLabel("Sort:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Chapter Number', 'Date Created', 'Word Count', 'Last Edited'])
        self.sort_combo.currentTextChanged.connect(self.sort_chapters)
        layout.addWidget(self.sort_combo)
        
        # View mode toggle
        self.view_mode_btn = QPushButton("Grid View")
        self.view_mode_btn.clicked.connect(self.toggle_view_mode)
        layout.addWidget(self.view_mode_btn)
        
        layout.addStretch()
        toolbar.setLayout(layout)
        return toolbar
        
    def _create_list_panel(self):
        """Create the chapter list panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Create container for view switching
        self.view_container = QWidget()
        view_layout = QVBoxLayout()
        view_layout.setContentsMargins(0, 0, 0, 0)
        
        # Table view (default)
        self.table_view = self._create_table_view()
        view_layout.addWidget(self.table_view)
        
        self.view_container.setLayout(view_layout)
        layout.addWidget(self.view_container)
        
        # Add New Chapter button
        add_chapter_btn = QPushButton("➕ Add New Chapter")
        add_chapter_btn.clicked.connect(self._add_new_chapter)
        add_chapter_btn.setStyleSheet("""
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
        layout.addWidget(add_chapter_btn)
        
        panel.setLayout(layout)
        return panel
        
    def _create_table_view(self):
        """Create the table view for chapters"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            '☑', 'Ch#', 'Title', 'Arc', 'POV', 'Words', 'Status', 'Last Edit'
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        table.setColumnWidth(0, 30)
        table.setColumnWidth(1, 50)
        table.setColumnWidth(3, 100)
        table.setColumnWidth(4, 80)
        table.setColumnWidth(5, 80)
        table.setColumnWidth(6, 80)
        table.setColumnWidth(7, 100)
        
        # Style
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Connect selection
        table.itemClicked.connect(self.on_chapter_selected)
        
        return table
        
    def _populate_table(self):
        """Populate the table with chapter data"""
        if self.table_view is None:
            return
            
        chapters = self.get_filtered_chapters()
        self.table_view.setRowCount(len(chapters))
        
        for row, chapter in enumerate(chapters):
            # Checkbox
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table_view.setCellWidget(row, 0, checkbox_widget)
            
            # Chapter number
            num_item = QTableWidgetItem(str(chapter.get('chapter_number', 0)))
            num_item.setData(Qt.UserRole, chapter.get('id'))
            self.table_view.setItem(row, 1, num_item)
            
            # Title
            title_item = QTableWidgetItem(chapter.get('title', 'Untitled'))
            self.table_view.setItem(row, 2, title_item)
            
            # Arc
            arc_item = QTableWidgetItem(chapter.get('arc', ''))
            self.table_view.setItem(row, 3, arc_item)
            
            # POV
            pov_item = QTableWidgetItem(chapter.get('pov_character', ''))
            self.table_view.setItem(row, 4, pov_item)
            
            # Word count
            word_item = QTableWidgetItem(str(chapter.get('word_count', 0)))
            self.table_view.setItem(row, 5, word_item)
            
            # Status (with color coding)
            status = chapter.get('status', 'draft')
            status_item = QTableWidgetItem(status.capitalize())
            if status == 'final':
                status_item.setForeground(Qt.darkGreen)
            elif status == 'review':
                status_item.setForeground(Qt.darkYellow)
            else:
                status_item.setForeground(Qt.gray)
            self.table_view.setItem(row, 6, status_item)
            
            # Last edited
            updated = chapter.get('updated_at', '')
            if updated and ('T' in str(updated) or ' ' in str(updated)):
                updated = str(updated).split('T')[0].split(' ')[0]
            last_edit_item = QTableWidgetItem(str(updated))
            self.table_view.setItem(row, 7, last_edit_item)
    
    def _create_details_panel(self):
        """Create the chapter details panel"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Chapter Details")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Basic Info
        basic_group = QGroupBox("Basic Information")
        basic_form = QFormLayout()
        
        self.chapter_number_input = QSpinBox()
        self.chapter_number_input.setRange(1, 9999)
        self.chapter_number_input.valueChanged.connect(self.mark_modified)
        basic_form.addRow("Chapter #:", self.chapter_number_input)
        
        self.title_input = QLineEdit()
        self.title_input.textChanged.connect(self.mark_modified)
        basic_form.addRow("Title:", self.title_input)
        
        self.arc_input = QLineEdit()
        self.arc_input.textChanged.connect(self.mark_modified)
        basic_form.addRow("Arc:", self.arc_input)
        
        self.pov_character_input = QLineEdit()
        self.pov_character_input.textChanged.connect(self.mark_modified)
        basic_form.addRow("POV Character:", self.pov_character_input)
        
        self.status_input = QComboBox()
        self.status_input.addItems(['Draft', 'Review', 'Final'])
        self.status_input.currentTextChanged.connect(self.mark_modified)
        basic_form.addRow("Status:", self.status_input)
        
        self.mood_input = QLineEdit()
        self.mood_input.textChanged.connect(self.mark_modified)
        basic_form.addRow("Mood:", self.mood_input)
        
        basic_group.setLayout(basic_form)
        content_layout.addWidget(basic_group)
        
        # Chapter content
        content_group = QGroupBox("Content")
        content_form = QVBoxLayout()
        
        self.chapter_content = QTextEdit()
        self.chapter_content.setReadOnly(True)
        self.chapter_content.setMinimumHeight(250)
        self.chapter_content.textChanged.connect(self.mark_modified)
        content_form.addWidget(self.chapter_content)
        
        content_group.setLayout(content_form)
        content_layout.addWidget(content_group)
        
        # Metadata
        meta_group = QGroupBox("Metadata")
        meta_form = QVBoxLayout()
        
        self.summary_input = QTextEdit()
        self.summary_input.setPlaceholderText("Chapter summary...")
        self.summary_input.setMaximumHeight(80)
        self.summary_input.textChanged.connect(self.mark_modified)
        meta_form.addWidget(QLabel("Summary:"))
        meta_form.addWidget(self.summary_input)
        
        self.plot_points_input = QTextEdit()
        self.plot_points_input.setPlaceholderText("Key plot points...")
        self.plot_points_input.setMaximumHeight(60)
        self.plot_points_input.textChanged.connect(self.mark_modified)
        meta_form.addWidget(QLabel("Plot Points:"))
        meta_form.addWidget(self.plot_points_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional notes...")
        self.notes_input.setMaximumHeight(60)
        self.notes_input.textChanged.connect(self.mark_modified)
        meta_form.addWidget(QLabel("Notes:"))
        meta_form.addWidget(self.notes_input)
        
        meta_group.setLayout(meta_form)
        content_layout.addWidget(meta_group)
        
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Action buttons
        btn_layout = QVBoxLayout()
        
        self.edit_btn = QPushButton("✏️ Edit Mode")
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        btn_layout.addWidget(self.edit_btn)
        
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)
        
        self.create_version_btn = QPushButton("📋 Create Version")
        self.create_version_btn.clicked.connect(self.create_version)
        btn_layout.addWidget(self.create_version_btn)
        
        self.regenerate_btn = QPushButton("🔄 Regenerate")
        self.regenerate_btn.clicked.connect(self.regenerate_chapter)
        btn_layout.addWidget(self.regenerate_btn)
        
        self.version_history_btn = QPushButton("📜 Version History")
        self.version_history_btn.clicked.connect(self.show_version_history)
        btn_layout.addWidget(self.version_history_btn)
        
        self.export_btn = QPushButton("📤 Export Chapter")
        self.export_btn.clicked.connect(self.export_chapter)
        btn_layout.addWidget(self.export_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete Chapter")
        self.delete_btn.clicked.connect(self.delete_chapter)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.8);
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 1.0);
            }
        """)
        btn_layout.addWidget(self.delete_btn)
        
        layout.addLayout(btn_layout)
        
        # APPROVED SECTIONS BUTTONS (NEW)
        self.approve_selection_btn = QPushButton("✓ Approve Selected Text")
        self.approve_selection_btn.clicked.connect(self.approve_selected_text)
        self.approve_selection_btn.setToolTip("Mark selected text as approved (protected from AI edits)")
        btn_layout.addWidget(self.approve_selection_btn)

        self.show_approved_btn = QPushButton("🔒 Show Approved Sections")
        self.show_approved_btn.clicked.connect(self.show_approved_sections)
        self.show_approved_btn.setToolTip("View all protected text sections")
        btn_layout.addWidget(self.show_approved_btn)

        panel.setLayout(layout)
        self.details_panel = panel
        return panel
        
    def _create_bulk_actions(self):
        """Create bulk action buttons"""
        widget = QWidget()
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Bulk Actions:"))
        
        self.bulk_export_btn = QPushButton("📤 Export Selected")
        self.bulk_export_btn.clicked.connect(self.bulk_export)
        layout.addWidget(self.bulk_export_btn)
        
        self.bulk_delete_btn = QPushButton("🗑️ Delete Selected")
        self.bulk_delete_btn.clicked.connect(self.bulk_delete)
        layout.addWidget(self.bulk_delete_btn)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def _add_new_chapter(self):
        """Add a new chapter"""
        if not self.current_story_id:
            self.show_warning("Please select a story first")
            return
        
        # Get next chapter number
        next_num = db_manager.get_next_chapter_number(self.current_story_id)
        
        # Clear form
        self.current_chapter_id = None
        self.chapter_number_input.setValue(next_num)
        self.title_input.clear()
        self.arc_input.clear()
        self.pov_character_input.clear()
        self.status_input.setCurrentIndex(0)
        self.mood_input.clear()
        self.chapter_content.clear()
        self.summary_input.clear()
        self.plot_points_input.clear()
        self.notes_input.clear()
        
        self.edit_mode = True
        self._update_edit_mode_ui()
        
        self.title_input.setFocus()
        self.mark_saved()
        self.log_info(f"Creating new chapter {next_num}")
        
    def load_data(self):
        """Load chapters for the current story"""
        if not self.current_story_id:
            self.chapters_data = []
            if self.table_view:
                self.table_view.setRowCount(0)
            self.log_info("No active story - chapters cleared")
            return
        
        try:
            # Get all chapters for this story
            chapters = db_manager.get_chapters(self.current_story_id)
            self.chapters_data = chapters
            
            # Update filters with actual data
            self._update_filter_options()
            
            # Populate table
            self._populate_table()
            
            self.log_info(f"Loaded {len(chapters)} chapters for story {self.current_story_id}")
            
        except Exception as e:
            self.log_error(f"Error loading chapters: {e}")
            self.show_error(f"Failed to load chapters: {str(e)}")
    
    def _update_filter_options(self):
        """Update filter dropdowns with actual data from chapters"""
        # Get unique arcs
        arcs = set(['All'])
        povs = set(['All'])
        
        for chapter in self.chapters_data:
            if chapter.get('arc'):
                arcs.add(chapter['arc'])
            if chapter.get('pov_character'):
                povs.add(chapter['pov_character'])
        
        # Update arc filter
        current_arc = self.arc_filter.currentText()
        self.arc_filter.clear()
        self.arc_filter.addItems(sorted(arcs))
        if current_arc in arcs:
            self.arc_filter.setCurrentText(current_arc)
        
        # Update POV filter
        current_pov = self.pov_filter.currentText()
        self.pov_filter.clear()
        self.pov_filter.addItems(sorted(povs))
        if current_pov in povs:
            self.pov_filter.setCurrentText(current_pov)
        
    def get_filtered_chapters(self):
        """Get chapters based on current filters"""
        chapters = self.chapters_data.copy()
        
        # Search filter
        search_text = self.search_input.text().lower() if self.search_input else ""
        if search_text:
            chapters = [c for c in chapters if 
                       search_text in str(c.get('title', '')).lower() or 
                       search_text in str(c.get('content', '')).lower()]
        
        # Arc filter
        arc = self.arc_filter.currentText() if self.arc_filter else "All"
        if arc != 'All':
            chapters = [c for c in chapters if c.get('arc') == arc]
        
        # POV filter
        pov = self.pov_filter.currentText() if self.pov_filter else "All"
        if pov != 'All':
            chapters = [c for c in chapters if c.get('pov_character') == pov]
        
        # Status filter
        status = self.status_filter.currentText() if self.status_filter else "All"
        if status != 'All':
            chapters = [c for c in chapters if c.get('status', 'draft').lower() == status.lower()]
        
        return chapters
        
    def filter_chapters(self):
        """Apply filters to chapter list"""
        self._populate_table()
        
    def sort_chapters(self):
        """Sort chapters based on selected criteria"""
        sort_by = self.sort_combo.currentText() if self.sort_combo else "Chapter Number"
        
        if sort_by == 'Chapter Number':
            self.chapters_data.sort(key=lambda x: x.get('chapter_number', 0))
        elif sort_by == 'Word Count':
            self.chapters_data.sort(key=lambda x: x.get('word_count', 0), reverse=True)
        elif sort_by == 'Last Edited':
            self.chapters_data.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        elif sort_by == 'Date Created':
            self.chapters_data.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        self._populate_table()
        
    def toggle_view_mode(self):
        """Toggle between list and grid view"""
        if self.current_view_mode == 'list':
            self.current_view_mode = 'grid'
            self.view_mode_btn.setText("List View")
            self.show_info("Grid view not yet implemented")
        else:
            self.current_view_mode = 'list'
            self.view_mode_btn.setText("Grid View")
            
    def on_chapter_selected(self, item):
        """Handle chapter selection from table"""
        row = item.row()
        chapter_id = self.table_view.item(row, 1).data(Qt.UserRole)
        
        if chapter_id:
            self._load_chapter(chapter_id)
    
    def _load_chapter(self, chapter_id):
        """Load chapter data into details panel"""
        if not self.current_story_id:
            return
        
        try:
            chapter = Chapter.get_by_id(self.current_story_id, chapter_id)
            
            if not chapter:
                self.show_error("Chapter not found")
                return
            
            self.current_chapter_id = chapter_id
            
            # Populate form
            self.chapter_number_input.setValue(chapter.chapter_number or 1)
            self.title_input.setText(chapter.title or '')
            self.arc_input.setText(chapter._data.get('arc', ''))
            self.pov_character_input.setText(chapter._data.get('pov_character', ''))
            
            # Set status
            status = (chapter.status or 'draft').capitalize()
            status_index = self.status_input.findText(status)
            self.status_input.setCurrentIndex(status_index if status_index >= 0 else 0)
            
            self.mood_input.setText(chapter.mood or '')
            self.chapter_content.setPlainText(chapter.content or '')
            self.summary_input.setPlainText(chapter.summary or '')
            self.plot_points_input.setPlainText(chapter._data.get('plot_points', ''))
            self.notes_input.setPlainText(chapter._data.get('notes', ''))
            
            self.edit_mode = False
            self._update_edit_mode_ui()
            
            self.mark_saved()
            # Highlight approved sections if any
            self._highlight_approved_sections()

            self.log_info(f"Loaded chapter: {chapter.chapter_number} - {chapter.title}")
            
        except Exception as e:
            self.log_error(f"Error loading chapter: {e}")
            self.show_error(f"Failed to load chapter: {str(e)}")
            
    def toggle_edit_mode(self):
        """Toggle edit mode for chapter details"""
        self.edit_mode = not self.edit_mode
        self._update_edit_mode_ui()
    
    def _update_edit_mode_ui(self):
        """Update UI based on edit mode"""
        self.chapter_content.setReadOnly(not self.edit_mode)
        self.chapter_number_input.setEnabled(self.edit_mode)
        self.title_input.setEnabled(self.edit_mode)
        self.arc_input.setEnabled(self.edit_mode)
        self.pov_character_input.setEnabled(self.edit_mode)
        self.status_input.setEnabled(self.edit_mode)
        self.mood_input.setEnabled(self.edit_mode)
        self.summary_input.setEnabled(self.edit_mode)
        self.plot_points_input.setEnabled(self.edit_mode)
        self.notes_input.setEnabled(self.edit_mode)
        self.save_btn.setEnabled(self.edit_mode)
        
        if self.edit_mode:
            self.edit_btn.setText("👁️ View Mode")
        else:
            self.edit_btn.setText("✏️ Edit Mode")
            
    def save_data(self):
        """Save chapter changes"""
        if not self.current_story_id:
            self.show_warning("No active story selected")
            return
        
        if not self.validate_input():
            return
        
        try:
            # Gather form data
            chapter_num = self.chapter_number_input.value()
            title = self.title_input.text().strip()
            arc = self.arc_input.text().strip()
            pov = self.pov_character_input.text().strip()
            status = self.status_input.currentText().lower()
            mood = self.mood_input.text().strip()
            content = self.chapter_content.toPlainText().strip()
            summary = self.summary_input.toPlainText().strip()
            plot_points = self.plot_points_input.toPlainText().strip()
            notes = self.notes_input.toPlainText().strip()
            
            if self.current_chapter_id:
                # Update existing chapter
                chapter = Chapter.get_by_id(self.current_story_id, self.current_chapter_id)
                
                if chapter:
                    chapter.chapter_number = chapter_num
                    chapter.title = title
                    chapter._data['arc'] = arc
                    chapter._data['pov_character'] = pov
                    chapter.status = status
                    chapter.mood = mood
                    chapter.content = content
                    chapter.summary = summary
                    chapter._data['plot_points'] = plot_points
                    chapter._data['notes'] = notes
                    
                    if chapter.save():
                        self.show_success(f"Chapter {chapter_num} updated successfully!")
                        self.mark_saved()
                        self.load_data()
                        self.log_info(f"Chapter updated: {chapter_num}")
                    else:
                        self.show_error("Failed to update chapter")
                else:
                    self.show_error("Chapter not found")
            else:
                # Create new chapter
                chapter = Chapter(
                    self.current_story_id,
                    chapter_number=chapter_num,
                    title=title,
                    arc=arc,
                    pov_character=pov,
                    status=status,
                    mood=mood,
                    content=content,
                    summary=summary,
                    plot_points=plot_points,
                    notes=notes
                )
                
                if chapter.save():
                    self.show_success(f"Chapter {chapter_num} created successfully!")
                    self.mark_saved()
                    self.current_chapter_id = chapter.id
                    self.load_data()
                    self.log_info(f"Chapter created: {chapter_num}")
                else:
                    self.show_error("Failed to create chapter")
                    
        except Exception as e:
            self.log_error(f"Error saving chapter: {e}")
            self.show_error(f"Failed to save chapter: {str(e)}")
            
    def validate_input(self) -> bool:
        """Validate chapter input"""
        if self.chapter_number_input.value() <= 0:
            self.show_error("Chapter number must be positive!")
            return False
        return True
            
    def create_version(self):
        """Create a new version of the current chapter"""
        if not self.current_chapter_id:
            self.show_warning("No chapter selected")
            return
        
        try:
            chapter = Chapter.get_by_id(self.current_story_id, self.current_chapter_id)
            if chapter and chapter.create_version():
                self.show_success("Chapter version created successfully!")
            else:
                self.show_error("Failed to create version")
        except Exception as e:
            self.log_error(f"Error creating version: {e}")
            self.show_error(f"Failed to create version: {str(e)}")

    def regenerate_chapter(self):
        """Regenerate the current chapter with AI"""
        if not self.current_chapter_id:
            self.show_warning("No chapter selected")
            return

        self.show_info("Chapter regeneration will integrate with AI generator in Phase 5")

    def show_version_history(self):
        """Show version history dialog"""
        if not self.current_chapter_id:
            self.show_warning("No chapter selected")
            return

        try:
            chapter = Chapter.get_by_id(self.current_story_id, self.current_chapter_id)
            if not chapter:
                return

            versions = chapter.get_versions()

            dialog = QDialog(self)
            dialog.setWindowTitle("Version History")
            dialog.setMinimumSize(600, 400)

            layout = QVBoxLayout()

            # Version list
            version_list = QListWidget()

            if versions:
                for version in versions:
                    version_num = version.get('version_number', 0)
                    created = version.get('created_at', '')
                    notes = version.get('notes', '')

                    item_text = f"Version {version_num} - {created}"
                    if notes:
                        item_text += f" - {notes}"

                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, version_num)
                    version_list.addItem(item)
            else:
                version_list.addItem("No versions available")

            layout.addWidget(version_list)

            # Buttons
            btn_layout = QHBoxLayout()
            restore_btn = QPushButton("Restore Version")
            restore_btn.clicked.connect(lambda: self._restore_version(version_list, dialog))
            compare_btn = QPushButton("Compare Versions")
            compare_btn.clicked.connect(lambda: self.show_info("Version comparison coming soon"))
            delete_btn = QPushButton("Delete Version")
            delete_btn.clicked.connect(lambda: self.show_info("Version deletion coming soon"))
            btn_layout.addWidget(restore_btn)
            btn_layout.addWidget(compare_btn)
            btn_layout.addWidget(delete_btn)
            layout.addLayout(btn_layout)

            # Dialog buttons
            buttons = QDialogButtonBox(QDialogButtonBox.Close)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            dialog.setLayout(layout)
            dialog.exec_()

        except Exception as e:
            self.log_error(f"Error showing version history: {e}")
            self.show_error(f"Failed to show version history: {str(e)}")

    def _restore_version(self, version_list, dialog):
        """Restore a selected version"""
        current_item = version_list.currentItem()
        if not current_item:
            self.show_warning("Please select a version to restore")
            return

        version_num = current_item.data(Qt.UserRole)

        if self.confirm_action("Restore Version", 
                              f"Are you sure you want to restore version {version_num}?"):
            try:
                chapter = Chapter.get_by_id(self.current_story_id, self.current_chapter_id)
                if chapter and chapter.restore_version(version_num):
                    self.show_success(f"Version {version_num} restored successfully!")
                    self._load_chapter(self.current_chapter_id)
                    dialog.accept()
                else:
                    self.show_error("Failed to restore version")
            except Exception as e:
                self.log_error(f"Error restoring version: {e}")
                self.show_error(f"Failed to restore version: {str(e)}")

    def export_chapter(self):
        """Export the current chapter"""
        if not self.current_chapter_id:
            self.show_warning("No chapter selected")
            return

        self.show_info("Chapter export will be implemented with export utilities")

    def delete_chapter(self):
        """Delete the current chapter"""
        if not self.current_chapter_id:
            return

        try:
            chapter = Chapter.get_by_id(self.current_story_id, self.current_chapter_id)
            if not chapter:
                return

            chapter_title = f"Chapter {chapter.chapter_number}"
            if chapter.title:
                chapter_title += f": {chapter.title}"

            if self.confirm_action("Delete Chapter", 
                                  f"Are you sure you want to delete '{chapter_title}'?"):
                if chapter.delete():
                    self.show_success(f"'{chapter_title}' deleted successfully")
                    self.current_chapter_id = None
                    self.load_data()
                else:
                    self.show_error("Failed to delete chapter")

        except Exception as e:
            self.log_error(f"Error deleting chapter: {e}")
            self.show_error(f"Failed to delete chapter: {str(e)}")

    def bulk_export(self):
        """Export selected chapters"""
        selected = self._get_selected_chapters()
        if selected:
            self.show_info(f"Bulk export of {len(selected)} chapter(s) will be implemented with export utilities")
        else:
            self.show_warning("No chapters selected")

    def bulk_delete(self):
        """Delete selected chapters"""
        selected = self._get_selected_chapters()

        if not selected:
            self.show_warning("No chapters selected")
            return

        if self.confirm_action("Delete Chapters", 
                              f"Are you sure you want to delete {len(selected)} chapter(s)?"):
            try:
                deleted_count = 0
                for chapter_id in selected:
                    chapter = Chapter.get_by_id(self.current_story_id, chapter_id)
                    if chapter and chapter.delete():
                        deleted_count += 1

                self.show_success(f"Deleted {deleted_count} chapter(s)")
                self.current_chapter_id = None
                self.load_data()

            except Exception as e:
                self.log_error(f"Error in bulk delete: {e}")
                self.show_error(f"Failed to delete chapters: {str(e)}")

    def _get_selected_chapters(self):
        """Get list of selected chapter IDs"""
        selected = []
        for row in range(self.table_view.rowCount()):
            checkbox_widget = self.table_view.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    chapter_id = self.table_view.item(row, 1).data(Qt.UserRole)
                    if chapter_id:
                        selected.append(chapter_id)
        return selected

    def refresh(self):
        """Refresh the view"""
        self.load_data()

    # ========================================================================
    # SELECTIVE EDITING - APPROVED SECTIONS
    # ========================================================================

    def approve_selected_text(self):
        """Approve currently selected text"""
        if not self.current_chapter_id:
            self.show_warning("Please select a chapter first")
            return

        cursor = self.chapter_content.textCursor()
        if not cursor.hasSelection():
            self.show_warning("Please select text to approve")
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        try:
            from models.chapter import Chapter
            chapter = Chapter.get_by_id(self.current_story_id, self.current_chapter_id)

            if chapter:
                if chapter.approve_section(start, end):
                    if chapter.save():
                        self.show_success(f"Approved text from position {start} to {end}")
                        self._highlight_approved_sections()
                        self.log_info(f"Section approved: {start}-{end}")
                    else:
                        self.show_error("Failed to save approval")
                else:
                    self.show_error("Failed to approve section")
            else:
                self.show_error("Chapter not found")

        except Exception as e:
            self.log_error(f"Error approving section: {e}")
            self.show_error(f"Failed to approve: {str(e)}")

    def show_approved_sections(self):
        """Show dialog with all approved sections"""
        if not self.current_chapter_id:
            self.show_warning("Please select a chapter first")
            return

        try:
            from models.chapter import Chapter
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout

            chapter = Chapter.get_by_id(self.current_story_id, self.current_chapter_id)
            if not chapter:
                self.show_error("Chapter not found")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Approved Sections - Chapter {chapter.chapter_number}")
            dialog.setMinimumSize(700, 500)

            layout = QVBoxLayout()

            # Info text area
            info_text = QTextEdit()
            info_text.setReadOnly(True)

            if chapter.approved_sections:
                content = "APPROVED SECTIONS (Protected from AI modification):\n"
                content += "=" * 60 + "\n\n"

                for i, section in enumerate(chapter.approved_sections, 1):
                    content += f"Section {i}:\n"
                    content += f"Position: Characters {section['start']}-{section['end']}\n"
                    content += f"Approved: {section.get('approved_at', 'Unknown')}\n"
                    content += f"Text:\n{section['text']}\n"
                    content += "=" * 60 + "\n\n"

                editable = chapter.get_editable_ranges()
                content += f"\nEDITABLE RANGES: {len(editable)}\n"
                for start, end in editable:
                    content += f"  • Characters {start} to {end} ({end - start} chars)\n"

                info_text.setPlainText(content)
            else:
                info_text.setPlainText(
                    "No approved sections yet.\n\n"
                    "All content is editable by AI.\n\n"
                    "To approve a section:\n"
                    "1. Select the text you want to protect\n"
                    "2. Click '✓ Approve Selected Text'\n\n"
                    "Approved sections will be preserved during AI regeneration."
                )

            layout.addWidget(info_text)

            # Buttons
            btn_layout = QHBoxLayout()

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)

            clear_all_btn = QPushButton("Clear All Approvals")
            clear_all_btn.clicked.connect(lambda: self._clear_all_approvals(dialog, chapter))
            clear_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(244, 67, 54, 0.8);
                    color: white;
                }
            """)
            btn_layout.addWidget(clear_all_btn)

            layout.addLayout(btn_layout)

            dialog.setLayout(layout)
            dialog.exec_()

        except Exception as e:
            self.log_error(f"Error showing approved sections: {e}")
            self.show_error(f"Failed to show sections: {str(e)}")

    def _clear_all_approvals(self, dialog, chapter):
        """Clear all approved sections"""
        if self.confirm_action(
            "Clear All Approvals",
            "Are you sure you want to remove all approved sections? This cannot be undone."
        ):
            chapter.approved_sections = []
            if chapter.save():
                self.show_success("All approvals cleared")
                dialog.accept()
                self._highlight_approved_sections()
            else:
                self.show_error("Failed to clear approvals")

    def _highlight_approved_sections(self):
        """Highlight approved text sections in editor"""
        if not self.current_chapter_id or not self.chapter_content:
            return

        try:
            from models.chapter import Chapter
            from PyQt5.QtGui import QTextCharFormat, QColor

            chapter = Chapter.get_by_id(self.current_story_id, self.current_chapter_id)
            if not chapter:
                return

            # Clear existing highlights
            cursor = self.chapter_content.textCursor()
            cursor.select(cursor.Document)
            fmt = QTextCharFormat()
            cursor.setCharFormat(fmt)

            # Highlight approved sections with light green background
            for section in chapter.approved_sections:
                cursor = self.chapter_content.textCursor()
                cursor.setPosition(section['start'])
                cursor.setPosition(section['end'], cursor.KeepAnchor)

                fmt = QTextCharFormat()
                fmt.setBackground(QColor(100, 200, 100, 50))  # Light green with transparency
                cursor.setCharFormat(fmt)

            self.log_debug(f"Highlighted {len(chapter.approved_sections)} approved sections")

        except Exception as e:
            self.log_error(f"Error highlighting sections: {e}")

    