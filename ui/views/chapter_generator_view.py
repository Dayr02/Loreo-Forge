"""
Chapter Generator View
AI-powered chapter generation interface

"""

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QGroupBox, QFormLayout, QScrollArea,
    QWidget, QSpinBox, QSlider, QCheckBox, QTabWidget, QProgressBar,
    QListWidget, QSplitter, QListWidgetItem, QToolButton, QButtonGroup,
    QRadioButton, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt
from datetime import datetime

from ui.views.base_view import BaseView
from database import db_manager
from controllers.ai_controller import ai_controller


# ─────────────────────────────────────────────────────────────────────────────
# CheckboxSection — identical to the one in ChapterPartsGeneratorView.
# Inlined here to avoid a circular import.
# ─────────────────────────────────────────────────────────────────────────────

class CheckboxSection(QWidget):
    """Collapsible list of checkboxes for one entity type."""

    def __init__(self, title: str):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 2)
        layout.setSpacing(2)

        header = QHBoxLayout()

        self.expand_btn = QToolButton()
        self.expand_btn.setText("▶")
        self.expand_btn.setCheckable(True)
        self.expand_btn.setStyleSheet(
            "border:none; background:transparent; font-size:10px;"
        )
        header.addWidget(self.expand_btn)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight:bold; font-size:11px;")
        header.addWidget(lbl)
        header.addStretch()

        sel_btn = QPushButton("All")
        sel_btn.setMaximumWidth(32)
        sel_btn.setStyleSheet("padding:1px; font-size:9px;")
        header.addWidget(sel_btn)

        none_btn = QPushButton("None")
        none_btn.setMaximumWidth(36)
        none_btn.setStyleSheet("padding:1px; font-size:9px;")
        header.addWidget(none_btn)

        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(90)
        self.list_widget.setStyleSheet(
            "background:rgba(0,0,0,0.25);"
            "border:1px solid rgba(255,255,255,0.1);"
            "font-size:11px;"
        )
        self.list_widget.hide()
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

        self.expand_btn.toggled.connect(
            lambda c: (
                self.list_widget.setVisible(c),
                self.expand_btn.setText("▼" if c else "▶"),
            )
        )
        sel_btn.clicked.connect(self._select_all)
        none_btn.clicked.connect(self._select_none)

    def _select_all(self):
        for i in range(self.list_widget.count()):
            w = self.list_widget.itemWidget(self.list_widget.item(i))
            if w:
                w.setChecked(True)

    def _select_none(self):
        for i in range(self.list_widget.count()):
            w = self.list_widget.itemWidget(self.list_widget.item(i))
            if w:
                w.setChecked(False)

    def get_selected_ids(self):
        ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            w    = self.list_widget.itemWidget(item)
            if w and w.isChecked():
                ids.append(item.data(Qt.UserRole))
        return ids

    def populate(self, items, name_field: str):
        self.list_widget.clear()
        for it in items:
            name = getattr(it, name_field, None) or it.get(name_field, 'Unknown')
            iid  = getattr(it, 'id', None)       or it.get('id')
            cb   = QCheckBox(name)
            cb.setChecked(True)
            li   = QListWidgetItem()
            li.setData(Qt.UserRole, iid)
            self.list_widget.addItem(li)
            self.list_widget.setItemWidget(li, cb)


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class ChapterGeneratorView(BaseView):
    """Chapter generation interface with AI controls."""

    def __init__(self):
        # ── basic form fields ────────────────────────────────────────────────
        self.chapter_number_input  = None
        self.title_input           = None
        self.word_count_slider     = None
        self.word_count_label      = None
        self.pov_character_combo   = None
        self.mood_combo            = None
        self.model_combo           = None
        self.temperature_slider    = None
        self.temperature_label     = None
        self.plot_points_input     = None
        self.style_input           = None
        self.story_progression_input = None
        self.generation_type_group   = None

        # ── generation controls ──────────────────────────────────────────────
        self.generate_button    = None
        self.cancel_button      = None
        self.progress_bar       = None
        self.status_label       = None

        # ── preview tabs ─────────────────────────────────────────────────────
        self.preview_tabs       = None
        self.content_preview    = None
        self.log_preview        = None

        # ── action buttons ───────────────────────────────────────────────────
        self.save_button        = None
        self.regenerate_button  = None
        self.edit_button        = None
        self.discard_button     = None

        # ── context panel (CheckboxSection-based, matching Parts generator) ──
        self.ctx_characters    = None
        self.ctx_locations     = None
        self.ctx_organizations = None
        self.ctx_powers        = None
        self.ctx_bestiary      = None
        self.ctx_lore          = None
        self.ctx_items         = None
        self.ctx_content       = None   # collapsible wrapper
        self.ctx_collapse_btn  = None
        self.ctx_scroll        = None   # resizable scroll area

        # ── generated content tracking ───────────────────────────────────────
        self.generated_chapter_id = None
        self.generated_content    = ""

        super().__init__()
        self.view_name = "Chapter Generator"

    # =========================================================================
    # SETUP UI
    # =========================================================================

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ── Header ────────────────────────────────────────────────────────────
        header_layout = QHBoxLayout()

        header = QLabel("🖊️ AI Chapter Generator")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        # "Chapter by Parts Generator →" navigation button (kept)
        parts_generator_btn = QPushButton("📝 Chapter by Parts Generator →")
        parts_generator_btn.setMaximumWidth(250)
        parts_generator_btn.clicked.connect(self._open_parts_generator)
        parts_generator_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.7);
                color: white; border: none; border-radius: 5px;
                font-weight: bold; padding: 8px 15px;
            }
            QPushButton:hover { background-color: rgba(76, 175, 80, 0.9); }
        """)
        header_layout.addWidget(parts_generator_btn)

        # NOTE: "Show Chapter Parts Manager" button REMOVED (along with its
        # duplicate declaration, stylesheet, and all associated panel code).

        main_layout.addLayout(header_layout)

        # ── Vertical splitter: settings / controls / preview ─────────────────
        # generation_splitter is added directly to main_layout now that the
        # horizontal main_splitter (which held the parts panel) is removed.
        generation_splitter = QSplitter(Qt.Vertical)

        # Top: Generation settings (scrollable)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QScrollArea.NoFrame)
        settings_scroll.setMaximumHeight(450)

        settings_widget = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(15)

        settings_layout.addWidget(self._create_chapter_info_group())
        settings_layout.addWidget(self._create_generation_type_group())
        settings_layout.addWidget(self._create_model_settings_group())
        settings_layout.addWidget(self._create_context_group())

        settings_widget.setLayout(settings_layout)
        settings_scroll.setWidget(settings_widget)
        generation_splitter.addWidget(settings_scroll)

        # Middle: Generation controls
        generation_splitter.addWidget(self._create_generation_controls())

        # Bottom: Preview panel
        generation_splitter.addWidget(self._create_preview_panel())

        generation_splitter.setStretchFactor(0, 2)
        generation_splitter.setStretchFactor(1, 1)
        generation_splitter.setStretchFactor(2, 4)

        main_layout.addWidget(generation_splitter)
        self.setLayout(main_layout)

    # =========================================================================
    # CHAPTER INFO GROUP
    # =========================================================================

    def _create_chapter_info_group(self):
        group  = QGroupBox("Chapter Information")
        layout = QFormLayout()

        self.chapter_number_input = QSpinBox()
        self.chapter_number_input.setRange(1, 9999)
        self.chapter_number_input.setValue(1)
        layout.addRow("Chapter Number:", self.chapter_number_input)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Optional - can be AI-generated")
        layout.addRow("Chapter Title:", self.title_input)

        wc_row = QHBoxLayout()
        self.word_count_slider = QSlider(Qt.Horizontal)
        self.word_count_slider.setRange(500, 10000)
        self.word_count_slider.setValue(3000)
        self.word_count_slider.setSingleStep(100)
        self.word_count_slider.valueChanged.connect(self._update_word_count_label)
        wc_row.addWidget(self.word_count_slider)
        self.word_count_label = QLabel("3000 words")
        self.word_count_label.setMinimumWidth(80)
        wc_row.addWidget(self.word_count_label)
        layout.addRow("Target Word Count:", wc_row)

        self.pov_character_combo = QComboBox()
        self.pov_character_combo.addItems([
            "Auto-select", "Hero", "Villain", "Sidekick",
        ])
        layout.addRow("POV Character:", self.pov_character_combo)

        self.mood_combo = QComboBox()
        self.mood_combo.setEditable(True)
        self.mood_combo.addItems([
            "Dramatic", "Lighthearted", "Tense", "Mysterious",
            "Action-packed", "Emotional", "Suspenseful", "Peaceful",
        ])
        layout.addRow("Mood/Tone:", self.mood_combo)

        group.setLayout(layout)
        return group

    # =========================================================================
    # GENERATION TYPE GROUP
    # =========================================================================

    def _create_generation_type_group(self):
        group  = QGroupBox("Generation Type")
        layout = QVBoxLayout()

        self.generation_type_group = QButtonGroup(self)

        full_chapter_radio = QRadioButton("Full Chapter")
        full_chapter_radio.setToolTip("Generate a complete chapter with full narrative arc")
        full_chapter_radio.setChecked(True)
        self.generation_type_group.addButton(full_chapter_radio, 0)
        layout.addWidget(full_chapter_radio)

        chapter_parts_radio = QRadioButton("Section/Scene")
        chapter_parts_radio.setToolTip(
            "Generate a scene or section that's part of a larger chapter"
        )
        self.generation_type_group.addButton(chapter_parts_radio, 1)
        layout.addWidget(chapter_parts_radio)

        short_story_radio = QRadioButton("Short Story")
        short_story_radio.setToolTip("Generate a complete, self-contained short story")
        self.generation_type_group.addButton(short_story_radio, 2)
        layout.addWidget(short_story_radio)

        group.setLayout(layout)
        return group

    # =========================================================================
    # MODEL SETTINGS GROUP
    # =========================================================================

    def _create_model_settings_group(self):
        group  = QGroupBox("AI Model Settings")
        layout = QFormLayout()

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "llama3.1:8b (Fast Draft)",
            "llama3.1:70b (High Quality)",
        ])
        layout.addRow("Model:", self.model_combo)

        temp_row = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(10, 100)
        self.temperature_slider.setValue(70)
        self.temperature_slider.valueChanged.connect(self._update_temperature_label)
        temp_row.addWidget(self.temperature_slider)
        self.temperature_label = QLabel("0.70")
        self.temperature_label.setMinimumWidth(40)
        temp_row.addWidget(self.temperature_label)
        layout.addRow("Temperature:", temp_row)

        group.setLayout(layout)
        return group

    # =========================================================================
    # CONTEXT GROUP  — identical panel to ChapterPartsGeneratorView
    # =========================================================================

    def _create_context_group(self):
        """
        Context & Prompts group.

        Builds all ctx_ CheckboxSection widgets (stored on self) so that
        _create_preview_panel() can embed self.ctx_content into the
        '📚 Context Selection' tab.  The ctx_content widget is NOT added to
        this group's own layout — it lives in the preview tab.

        This group contains only the generation prompts:
          - Story Progression Prompt
          - Specific Plot Points
          - Style Instructions
        """
        group  = QGroupBox("Context & Prompts")
        layout = QVBoxLayout()

        # ── Context selection panel (widgets built here, displayed in preview tab) ──
        # Identical structure to ChapterPartsGeneratorView._make_context_group().
        self.ctx_content = QWidget()
        ctx_outer = QVBoxLayout()
        ctx_outer.setContentsMargins(0, 4, 0, 4)
        ctx_outer.setSpacing(4)

        # header row: collapse button + note + resize hint
        header_row = QHBoxLayout()

        self.ctx_collapse_btn = QToolButton()
        self.ctx_collapse_btn.setText("▼")
        self.ctx_collapse_btn.setCheckable(True)
        self.ctx_collapse_btn.setChecked(True)
        self.ctx_collapse_btn.setStyleSheet(
            "border:none; background:transparent; font-size:12px; font-weight:bold;"
        )
        header_row.addWidget(self.ctx_collapse_btn)

        note = QLabel("Select which story entries to include as AI context:")
        note.setStyleSheet("font-size:10px; color:rgba(255,255,255,0.6);")
        header_row.addWidget(note)
        header_row.addStretch()

        resize_hint = QLabel("⇕ Drag bottom edge to resize")
        resize_hint.setStyleSheet("font-size:9px; color:rgba(255,255,255,0.4);")
        header_row.addWidget(resize_hint)

        ctx_outer.addLayout(header_row)

        # inner collapsible area
        self._ctx_inner = QWidget()
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)

        # resizable scroll area
        self.ctx_scroll = QScrollArea()
        self.ctx_scroll.setWidgetResizable(True)
        self.ctx_scroll.setFrameShape(QScrollArea.NoFrame)
        self.ctx_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ctx_scroll.setMinimumHeight(150)
        self.ctx_scroll.setMaximumHeight(16777215)   # no upper limit initially

        scroll_inner = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(4)

        self.ctx_characters    = CheckboxSection("👤 Characters")
        self.ctx_locations     = CheckboxSection("📍 Locations")
        self.ctx_organizations = CheckboxSection("🏛️  Organizations")
        self.ctx_powers        = CheckboxSection("⚡ Power Systems")
        self.ctx_bestiary      = CheckboxSection("🐉 Creatures")
        self.ctx_lore          = CheckboxSection("📜 Lore")
        self.ctx_items         = CheckboxSection("🗡️ Items")

        for section in [
            self.ctx_characters, self.ctx_locations, self.ctx_organizations,
            self.ctx_powers, self.ctx_bestiary, self.ctx_lore, self.ctx_items,
        ]:
            scroll_layout.addWidget(section)

        scroll_layout.addStretch()
        scroll_inner.setLayout(scroll_layout)
        self.ctx_scroll.setWidget(scroll_inner)

        inner_layout.addWidget(self.ctx_scroll, 1)

        # drag-to-resize handle (identical to Parts generator)
        resize_handle = QFrame()
        resize_handle.setFrameShape(QFrame.HLine)
        resize_handle.setFrameShadow(QFrame.Sunken)
        resize_handle.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.2);
                max-height: 4px;
                min-height: 4px;
            }
            QFrame:hover {
                background: rgba(33,150,243,0.6);
            }
        """)
        resize_handle.setCursor(Qt.SizeVerCursor)
        resize_handle.setMouseTracking(True)
        resize_handle.installEventFilter(self)
        resize_handle.setProperty('resize_target', 'ctx_scroll')
        inner_layout.addWidget(resize_handle)

        self._ctx_inner.setLayout(inner_layout)
        ctx_outer.addWidget(self._ctx_inner, 1)

        self.ctx_content.setLayout(ctx_outer)
        # NOTE: ctx_content is NOT added to this layout — it is inserted into
        # the '📚 Context Selection' preview tab by _create_preview_panel().

        # connect collapse toggle
        self.ctx_collapse_btn.toggled.connect(self._toggle_context_section)

        # ── Story Progression Prompt ──────────────────────────────────────────
        progression_label = QLabel("Story Progression Prompt:")
        progression_label.setStyleSheet(
            "font-weight: bold; margin-top: 10px; color: rgba(76, 175, 80, 1.0);"
        )
        progression_label.setToolTip(
            "Tell the AI how the story should progress in this chapter"
        )
        layout.addWidget(progression_label)

        self.story_progression_input = QTextEdit()
        self.story_progression_input.setPlaceholderText(
            "Describe how you want the story to progress...\n\n"
            "Examples:\n"
            "- The hero should discover the ancient artifact in the temple ruins\n"
            "- Reveal the villain's true identity through a dramatic confrontation\n"
            "- Build romantic tension between the two main characters\n"
            "- The team should face their greatest challenge yet"
        )
        self.story_progression_input.setMaximumHeight(80)
        self.story_progression_input.setStyleSheet(
            "border: 2px solid rgba(76, 175, 80, 0.5);"
        )
        layout.addWidget(self.story_progression_input)

        # ── Plot Points ───────────────────────────────────────────────────────
        plot_label = QLabel("Specific Plot Points:")
        plot_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(plot_label)

        self.plot_points_input = QTextEdit()
        self.plot_points_input.setPlaceholderText(
            "Specific events or moments to include (optional)..."
        )
        self.plot_points_input.setMaximumHeight(60)
        layout.addWidget(self.plot_points_input)

        # ── Style Instructions ────────────────────────────────────────────────
        style_label = QLabel("Style Instructions:")
        style_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(style_label)

        self.style_input = QTextEdit()
        self.style_input.setPlaceholderText("Writing style preferences (optional)...")
        self.style_input.setMaximumHeight(60)
        layout.addWidget(self.style_input)

        group.setLayout(layout)
        return group

    # ── context panel helpers ─────────────────────────────────────────────────

    def _toggle_context_section(self, expanded: bool):
        """Collapse/expand the CheckboxSection scroll area."""
        self._ctx_inner.setVisible(expanded)
        self.ctx_collapse_btn.setText("▼" if expanded else "▶")

    def eventFilter(self, obj, event):
        """Drag-to-resize for ctx_scroll — same logic as ChapterPartsGeneratorView."""
        if (hasattr(obj, 'property')
                and obj.property('resize_target') == 'ctx_scroll'):
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._resize_start_y      = event.globalY()
                    self._resize_start_height = self.ctx_scroll.height()
                    return True
            elif event.type() == event.MouseMove:
                if hasattr(self, '_resize_start_y'):
                    delta      = event.globalY() - self._resize_start_y
                    new_height = max(150, self._resize_start_height + delta)
                    self.ctx_scroll.setMinimumHeight(new_height)
                    self.ctx_scroll.setMaximumHeight(new_height)
                    return True
            elif event.type() == event.MouseButtonRelease:
                if hasattr(self, '_resize_start_y'):
                    delattr(self, '_resize_start_y')
                    self.ctx_scroll.setMaximumHeight(16777215)   # re-enable free growth
                    return True
        return super().eventFilter(obj, event)

    def _populate_context_lists(self):
        """Populate all six CheckboxSections from the active story's DB."""
        if not self.current_story_id:
            return
        try:
            from models.character import Character
            from models.location  import Location
            from models.creature  import Creature

            self.ctx_characters.populate(
                Character.get_all(self.current_story_id, sort_by='name'), 'name')
            self.ctx_locations.populate(
                Location.get_all(self.current_story_id, sort_by='name'), 'name')
            self.ctx_organizations.populate(
                db_manager.get_organizations(self.current_story_id), 'name')
            self.ctx_powers.populate(
                db_manager.get_power_systems(self.current_story_id), 'name')
            self.ctx_bestiary.populate(
                Creature.get_all(self.current_story_id, sort_by='name'), 'name')
            self.ctx_lore.populate(
                db_manager.get_lore_entries(self.current_story_id), 'title')
            self.ctx_items.populate(
                db_manager.get_all_records(self.current_story_id, 'items', sort_by='name'), 'name')
        except Exception as e:
            self.log_error(f"Error populating context lists: {e}")

    def _get_selected_context(self):
        """Return dict of selected entity IDs from the Context Selection tab."""
        return {
            'characters':    self.ctx_characters.get_selected_ids(),
            'locations':     self.ctx_locations.get_selected_ids(),
            'organizations': self.ctx_organizations.get_selected_ids(),
            'power_systems': self.ctx_powers.get_selected_ids(),
            'creatures':     self.ctx_bestiary.get_selected_ids(),
            'lore':          self.ctx_lore.get_selected_ids(),
            'items':         self.ctx_items.get_selected_ids(),
        }

    # =========================================================================
    # GENERATION CONTROLS
    # =========================================================================

    def _create_generation_controls(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to generate")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()

        self.generate_button = QPushButton("✨ Generate Chapter")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.clicked.connect(self._start_generation)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.8);
                color: white; border: none; border-radius: 5px;
                font-size: 16px; font-weight: bold; padding: 10px;
            }
            QPushButton:hover    { background-color: rgba(76, 175, 80, 1.0); }
            QPushButton:pressed  { background-color: rgba(56, 142, 60, 1.0); }
            QPushButton:disabled { background-color: rgba(100, 100, 100, 0.5); }
        """)
        button_layout.addWidget(self.generate_button)

        self.cancel_button = QPushButton("⛔ Cancel")
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.clicked.connect(self._cancel_generation)
        self.cancel_button.setVisible(False)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.8);
                color: white; border: none; border-radius: 5px;
                font-size: 16px; font-weight: bold; padding: 10px;
            }
            QPushButton:hover { background-color: rgba(244, 67, 54, 1.0); }
        """)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        widget.setLayout(layout)
        return widget

    # =========================================================================
    # PREVIEW PANEL
    # =========================================================================

    def _create_preview_panel(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.preview_tabs = QTabWidget()

        # Tab 1: Generated Content
        cc = QWidget(); cl = QVBoxLayout(); cl.setContentsMargins(5, 5, 5, 5)
        self.content_preview = QTextEdit()
        self.content_preview.setPlaceholderText("Generated chapter will appear here...")
        self.content_preview.setReadOnly(True)
        cl.addWidget(self.content_preview); cc.setLayout(cl)
        self.preview_tabs.addTab(cc, "📝 Generated Content")

        # Tab 2: Context Selection (interactive CheckboxSection panel)
        # ctx_content is built in _create_context_group() which runs before
        # this method in setup_ui(), so self.ctx_content is always ready here.
        xc = QWidget(); xl = QVBoxLayout(); xl.setContentsMargins(5, 5, 5, 5)
        xl.addWidget(self.ctx_content)
        xc.setLayout(xl)
        self.preview_tabs.addTab(xc, "📚 Context Selection")

        # Tab 3: Generation Log
        lc = QWidget(); ll = QVBoxLayout(); ll.setContentsMargins(5, 5, 5, 5)
        self.log_preview = QTextEdit()
        self.log_preview.setPlaceholderText("Generation logs will appear here...")
        self.log_preview.setReadOnly(True)
        self.log_preview.setStyleSheet("font-family: 'Courier New', monospace;")
        ll.addWidget(self.log_preview); lc.setLayout(ll)
        self.preview_tabs.addTab(lc, "📋 Generation Log")

        layout.addWidget(self.preview_tabs)

        # Action buttons
        actions_layout = QHBoxLayout()

        self.save_button = QPushButton("💾 Accept & Save")
        self.save_button.clicked.connect(self._save_chapter)
        self.save_button.setVisible(False)
        self.save_button.setMinimumHeight(40)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.8);
                color: white; border: none; border-radius: 5px;
                font-weight: bold; padding: 10px 20px;
            }
            QPushButton:hover { background-color: rgba(76, 175, 80, 1.0); }
        """)
        actions_layout.addWidget(self.save_button)

        self.regenerate_button = QPushButton("🔄 Regenerate")
        self.regenerate_button.clicked.connect(self._start_generation)
        self.regenerate_button.setVisible(False)
        self.regenerate_button.setMinimumHeight(40)
        self.regenerate_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 152, 0, 0.8);
                color: white; border: none; border-radius: 5px;
                font-weight: bold; padding: 10px 20px;
            }
            QPushButton:hover { background-color: rgba(255, 152, 0, 1.0); }
        """)
        actions_layout.addWidget(self.regenerate_button)

        self.edit_button = QPushButton("✏️ Edit Before Saving")
        self.edit_button.clicked.connect(self._enable_editing)
        self.edit_button.setVisible(False)
        self.edit_button.setMinimumHeight(40)
        actions_layout.addWidget(self.edit_button)

        self.discard_button = QPushButton("🗑️ Discard")
        self.discard_button.clicked.connect(self._discard_chapter)
        self.discard_button.setVisible(False)
        self.discard_button.setMinimumHeight(40)
        self.discard_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.8);
                color: white; border: none; border-radius: 5px;
                font-weight: bold; padding: 10px 20px;
            }
            QPushButton:hover { background-color: rgba(244, 67, 54, 1.0); }
        """)
        actions_layout.addWidget(self.discard_button)

        layout.addLayout(actions_layout)
        widget.setLayout(layout)
        return widget

    # =========================================================================
    # NAVIGATION
    # =========================================================================

    def _open_parts_generator(self):
        try:
            main_window = self.window()
            if hasattr(main_window, 'switch_view'):
                main_window.switch_view('chapter_parts_generator')
        except Exception as e:
            self.log_error(f"Error navigating to parts generator: {e}")

    # =========================================================================
    # GENERATION LOGIC  (unchanged)
    # =========================================================================

    def _update_word_count_label(self, value):
        self.word_count_label.setText(f"{value} words")

    def _update_temperature_label(self, value):
        self.temperature_label.setText(f"{value / 100.0:.2f}")

    def _start_generation(self):
        if not self.current_story_id:
            self.show_error("Please select a story first!")
            return

        chapter_num      = self.chapter_number_input.value()
        title            = self.title_input.text() or None
        word_count       = self.word_count_slider.value()
        pov              = self.pov_character_combo.currentText()
        mood             = self.mood_combo.currentText()
        model            = ('llama3.1:8b'
                            if self.model_combo.currentIndex() == 0
                            else 'llama3.1:70b')
        temp             = self.temperature_slider.value() / 100.0
        plot_points      = self.plot_points_input.toPlainText()
        style            = self.style_input.toPlainText()
        story_progression = self.story_progression_input.toPlainText()

        gen_type_id = self.generation_type_group.checkedId()
        generation_type = (
            "full_chapter"   if gen_type_id == 0 else
            "chapter_parts"  if gen_type_id == 1 else
            "short_story"
        )

        selected_context = self._get_selected_context()

        # UI → generating state
        self.generate_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generating...")
        self._hide_action_buttons()
        self.content_preview.clear()
        self.log_preview.clear()

        try:
            ai_controller.generation_progress.disconnect()
            ai_controller.generation_complete.disconnect()
            ai_controller.generation_failed.disconnect()
            ai_controller.log_updated.disconnect()
        except Exception:
            pass

        ai_controller.generation_progress.connect(self._on_progress_updated)
        ai_controller.generation_complete.connect(self._on_ai_generation_complete)
        ai_controller.generation_failed.connect(self._on_ai_generation_error)
        ai_controller.log_updated.connect(self._on_log_message)

        success = ai_controller.generate_chapter(
            story_id=self.current_story_id,
            chapter_number=chapter_num,
            title=title,
            target_word_count=word_count,
            pov_character=pov,
            mood=mood,
            plot_points=plot_points,
            style_instructions=style,
            story_progression_prompt=story_progression,
            generation_type=generation_type,
            model=model,
            temperature=temp,
            selected_context=selected_context,
        )

        if not success:
            self.show_error("Failed to start generation")
            self._reset_ui()
        else:
            self.log_info(f"Started {generation_type} generation for chapter {chapter_num}")

    def _on_ai_generation_complete(self, chapter_id: int):
        try:
            from models.chapter import Chapter
            chapter = Chapter.get_by_id(self.current_story_id, chapter_id)
            if chapter:
                self.generated_chapter_id = chapter_id
                self.generated_content    = chapter.content
                self.content_preview.setPlainText(chapter.content)
                word_count = chapter.word_count
                self.status_label.setText(f"✓ Generation complete ({word_count} words)")
                self._reset_ui()
                self._show_action_buttons()
                self.preview_tabs.setCurrentIndex(0)
                self.show_success(f"Chapter {chapter.chapter_number} generated successfully!")
                self.log_info(f"AI generation completed: {word_count} words")
            else:
                self._on_ai_generation_error(
                    "Chapter was generated but could not be loaded"
                )
        except Exception as e:
            self.log_error(f"Error handling generation completion: {e}")
            self._on_ai_generation_error(str(e))

    def _on_ai_generation_error(self, error_message: str):
        self.show_error(f"Generation failed: {error_message}")
        self.status_label.setText("✗ Generation failed")
        self._reset_ui()
        self.log_error(f"AI generation error: {error_message}")

    def _cancel_generation(self):
        ai_controller.cancel_generation()
        self.status_label.setText("Generation cancelled")
        self._reset_ui()
        self.log_info("Generation cancelled by user")

    def _on_progress_updated(self, value):
        self.progress_bar.setValue(value)

    def _on_log_message(self, message):
        self.log_preview.append(message)

    def _reset_ui(self):
        self.generate_button.setVisible(True)
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def _show_action_buttons(self):
        self.save_button.setVisible(True)
        self.regenerate_button.setVisible(True)
        self.edit_button.setVisible(True)
        self.discard_button.setVisible(True)

    def _hide_action_buttons(self):
        self.save_button.setVisible(False)
        self.regenerate_button.setVisible(False)
        self.edit_button.setVisible(False)
        self.discard_button.setVisible(False)

    # =========================================================================
    # CHAPTER SAVE / EDIT / DISCARD
    # =========================================================================

    def _save_chapter(self):
        if not self.generated_chapter_id:
            self.show_warning("No chapter to save!")
            return
        try:
            from models.chapter import Chapter
            chapter = Chapter.get_by_id(self.current_story_id, self.generated_chapter_id)
            if chapter:
                chapter.status = 'final'
                if chapter.save():
                    self.show_success(
                        f"Chapter {chapter.chapter_number} accepted and saved!"
                    )
                    self.log_info(f"Chapter {chapter.chapter_number} marked as final")
                    self._discard_chapter()
                else:
                    self.show_error("Failed to update chapter status")
            else:
                self.show_error("Chapter not found")
        except Exception as e:
            self.log_error(f"Error saving chapter: {e}")
            self.show_error(f"Save failed: {str(e)}")

    def _enable_editing(self):
        self.content_preview.setReadOnly(False)
        self.content_preview.setFocus()
        self.edit_button.setText("✏️ Editing Enabled")
        self.edit_button.setEnabled(False)
        self.show_success(
            "You can now edit the chapter. Click 'Accept & Save' when done."
        )
        self.log_info("Edit mode enabled")

    def _discard_chapter(self):
        if self.generated_content and not self.confirm_action(
            "Are you sure you want to discard this chapter?",
            "Discard Chapter",
        ):
            return
        self.generated_content    = ""
        self.generated_chapter_id = None
        self.content_preview.clear()
        self.content_preview.setReadOnly(True)
        self.log_preview.clear()
        self._hide_action_buttons()
        self.edit_button.setText("✏️ Edit Before Saving")
        self.edit_button.setEnabled(True)
        self.status_label.setText("Ready to generate")
        self.log_info("Chapter discarded")

    def clear_form(self):
        self.generated_content    = ""
        self.generated_chapter_id = None
        self.content_preview.clear()
        self.log_preview.clear()
        self._hide_action_buttons()
        self.status_label.setText("Ready to generate")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.log_info("Chapter generator form cleared")

    # =========================================================================
    # DATA LOAD / SAVE
    # =========================================================================

    def load_data(self):
        if self.current_story_id:
            next_chapter = db_manager.get_next_chapter_number(self.current_story_id)
            self.chapter_number_input.setValue(next_chapter)
            # Populate context selection lists with current story's entries
            self._populate_context_lists()

    def save_data(self):
        pass

    def validate_input(self) -> bool:
        if not self.current_story_id:
            self.show_error("No story selected")
            return False
        return True