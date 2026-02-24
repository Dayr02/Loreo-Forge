"""
Chapter by Parts Generator View
Dedicated multi-part chapter generation with:
  - Dismissible notification banner
  - Part Settings above Context Selection
  - POV / Mood / Style fields
  - Generation log + Cancel button
  - Save / Edit / Regenerate / View controls per part
  - Resizable panels via QSplitter
  - Fully functional context merging and DB persistence
"""

from logging import root
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QGroupBox, QFormLayout, QScrollArea,
    QWidget, QSpinBox, QSlider, QCheckBox, QListWidget, QSplitter,
    QListWidgetItem, QToolButton, QProgressBar, QFrame, QTabWidget,
    QSizePolicy, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from ui.views.base_view import BaseView
from database import db_manager
from controllers.ai_controller import ai_controller


# ─────────────────────────────────────────────────────────────────────────────
# Small collapsible checkbox section
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
        self.expand_btn.setStyleSheet("border:none; background:transparent; font-size:10px;")
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
            "background:rgba(0,0,0,0.25); border:1px solid rgba(255,255,255,0.1); font-size:11px;"
        )
        self.list_widget.hide()
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

        # wiring
        self.expand_btn.toggled.connect(
            lambda c: (self.list_widget.setVisible(c), self.expand_btn.setText("▼" if c else "▶"))
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
            w = self.list_widget.itemWidget(item)
            if w and w.isChecked():
                ids.append(item.data(Qt.UserRole))
        return ids

    def populate(self, items, name_field: str):
        self.list_widget.clear()
        for it in items:
            name = getattr(it, name_field, None) or it.get(name_field, 'Unknown')
            iid  = getattr(it, 'id', None) or it.get('id')
            cb   = QCheckBox(name)
            cb.setChecked(True)
            li   = QListWidgetItem()
            li.setData(Qt.UserRole, iid)
            self.list_widget.addItem(li)
            self.list_widget.setItemWidget(li, cb)


# ─────────────────────────────────────────────────────────────────────────────
# Part card (right panel)
# ─────────────────────────────────────────────────────────────────────────────

class PartCard(QFrame):
    """Compact card for one generated part with action buttons."""

    edit_requested       = pyqtSignal(int)   # part_id
    regenerate_requested = pyqtSignal(int)
    delete_requested     = pyqtSignal(int)
    view_requested       = pyqtSignal(int)

    def __init__(self, part_data: dict):
        super().__init__()
        self.part_id     = part_data.get('id', 0)
        self.part_number = part_data.get('part_number', 0)
        self._full_content = part_data.get('content', '')

        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            PartCard {
                background: rgba(76,175,80,0.10);
                border: 1px solid rgba(76,175,80,0.45);
                border-radius: 7px;
                margin: 3px 0;
            }
        """)
        self._build(part_data)

    def _build(self, d: dict):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # ── header row ───────────────────────────────────────────────────
        hdr = QHBoxLayout()

        num_lbl = QLabel(f"📝 Part {d.get('part_number', '?')}")
        f = QFont(); f.setBold(True); f.setPointSize(11)
        num_lbl.setFont(f)
        hdr.addWidget(num_lbl)

        hdr.addStretch()

        wc = d.get('word_count', 0)
        hdr.addWidget(QLabel(f"{wc} words"))

        for icon, sig in [("👁", self.view_requested), ("✏️", self.edit_requested),
                          ("🔄", self.regenerate_requested), ("🗑", self.delete_requested)]:
            b = QPushButton(icon)
            b.setFixedSize(26, 26)
            b.setToolTip({"👁":"View","✏️":"Edit","🔄":"Regenerate","🗑":"Delete"}[icon])
            if icon == "🗑":
                b.setStyleSheet("background:rgba(244,67,54,0.5); border-radius:4px;")
            else:
                b.setStyleSheet("background:rgba(255,255,255,0.08); border-radius:4px;")
            b.clicked.connect(lambda _, s=sig: s.emit(self.part_id))
            hdr.addWidget(b)

        layout.addLayout(hdr)

        # ── title ────────────────────────────────────────────────────────
        title = d.get('title', '')
        if title and title != f"Part {d.get('part_number')}":
            tl = QLabel(title)
            tl.setStyleSheet("font-size:11px; color:rgba(255,255,255,0.75);")
            layout.addWidget(tl)

        # ── preview ──────────────────────────────────────────────────────
        preview_text = self._full_content[:120].replace('\n', ' ')
        if len(self._full_content) > 120:
            preview_text += "…"
        preview = QLabel(preview_text)
        preview.setWordWrap(True)
        preview.setStyleSheet("font-size:10px; color:rgba(255,255,255,0.5);")
        layout.addWidget(preview)

        self.setLayout(layout)


# ─────────────────────────────────────────────────────────────────────────────
# Main view
# ─────────────────────────────────────────────────────────────────────────────

class ChapterPartsGeneratorView(BaseView):
    """Chapter by Parts Generator — clean, resizable, fully functional."""

    def __init__(self):
        # attributes before super().__init__()
        self.chapter_number_input     = None
        self.chapter_title_input      = None
        self.pov_combo                = None
        self.mood_combo               = None
        self.part_word_count_slider   = None
        self.part_word_count_label    = None
        self.part_progression_input   = None
        self.part_plot_points_input   = None
        self.style_input              = None
        self.model_combo              = None
        self.temperature_slider       = None
        self.temperature_label        = None

        # context sections
        self.ctx_characters    = None
        self.ctx_locations     = None
        self.ctx_organizations = None
        self.ctx_powers        = None
        self.ctx_bestiary      = None
        self.ctx_lore          = None
        self.ctx_items         = None

        # generation controls
        self.generate_btn     = None
        self.cancel_btn       = None
        self.progress_bar     = None
        self.status_label     = None

        # log tab
        self.log_text         = None

        # right panel
        self.parts_layout     = None
        self.parts_stats      = None
        self.merge_btn        = None

        # state
        self.current_part_number = 1
        self.generated_parts     = []   # list of part_data dicts
        self._part_group_box     = None

        super().__init__()
        self.view_name = "Chapter Parts Generator"

    # ------------------------ UI --------------------------------------------

    def setup_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 14)
        root.setSpacing(0)

        # --- page header ---
        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(16, 8, 16, 0)

        self.back_btn = QPushButton("← Chapter Generator")
        self.back_btn.setMaximumWidth(200)
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100,100,100,0.3);
                color: white;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(120,120,120,0.4);
            }
        """)
        hdr_row.addWidget(self.back_btn)
        hdr_row.addStretch()

        hdr = QLabel("📝 Chapter Parts Generator")
        hdr.setStyleSheet("font-size:20px; font-weight:bold; color: white;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()

        root.addLayout(hdr_row)

        # ── dismissible notification banner (separate row, minimal space) ────
        self._banner = self._make_banner()
        root.addWidget(self._banner)

        # ── main horizontal splitter ──────────────────────────────────────────
        main_split = QSplitter(Qt.Horizontal)
        main_split.setChildrenCollapsible(False)

        # LEFT: config + generation
        left = self._build_left_panel()
        main_split.addWidget(left)

        # RIGHT: generated parts + merge
        right = self._build_right_panel()
        main_split.addWidget(right)

        main_split.setSizes([550, 450])
        root.addWidget(main_split, 1)  # stretch factor of 1

        self.setLayout(root)

    def _make_banner(self) -> QWidget:
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background: rgba(33,150,243,0.15);
                border-left: 3px solid rgba(33,150,243,0.8);
                border-radius: 4px;
                padding: 3px 8px;
            }
        """)
        banner.setMaximumHeight(32)  # Keep it compact
        row = QHBoxLayout()
        row.setContentsMargins(6, 2, 6, 2)

        msg = QLabel(
            "ℹ  Generate a chapter in multiple parts — each part uses previous parts as context "
            "for seamless flow. Merge all parts into a final chapter when ready."
        )
        msg.setStyleSheet("font-size:10px; color:rgba(255,255,255,0.80);")
        msg.setWordWrap(False)  # Single line to save space
        row.addWidget(msg, 1)

        close = QPushButton("✕")
        close.setFixedSize(20, 20)
        close.setStyleSheet("background:transparent; border:none; color:rgba(255,255,255,0.5); font-size:11px;")
        close.setToolTip("Dismiss")
        close.clicked.connect(lambda: banner.hide())
        row.addWidget(close)

        banner.setLayout(row)
        return banner

    # ── left panel ───────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 6, 0)
        vl.setSpacing(0)

        # scrollable config area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        inner = QWidget()
        il = QVBoxLayout()
        il.setSpacing(10)

        # 1. chapter info
        il.addWidget(self._make_chapter_info())

        # 2. part settings  (ABOVE context, per request)
        self._part_group_box = self._make_part_settings()
        il.addWidget(self._part_group_box)

        # 3. model settings
        il.addWidget(self._make_model_settings())

        # 4. context selection
        il.addWidget(self._make_context_group())

        il.addStretch()
        inner.setLayout(il)
        scroll.setWidget(inner)
        vl.addWidget(scroll)

        # generation controls (fixed at bottom)
        vl.addWidget(self._make_gen_controls())

        w.setLayout(vl)
        return w

    # ── right panel ──────────────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout()
        vl.setContentsMargins(6, 0, 0, 0)
        vl.setSpacing(6)

        # tab widget: parts list  |  generation log
        self.right_tabs = QTabWidget()

        # --- Parts tab ---
        parts_tab = QWidget()
        pt_layout = QVBoxLayout()
        pt_layout.setContentsMargins(4, 4, 4, 4)

        self.parts_stats = QLabel("0 parts | 0 total words")
        self.parts_stats.setStyleSheet("color:rgba(255,255,255,0.6); font-size:11px;")
        pt_layout.addWidget(self.parts_stats)

        parts_scroll = QScrollArea()
        parts_scroll.setWidgetResizable(True)
        parts_scroll.setFrameShape(QScrollArea.NoFrame)

        parts_container = QWidget()
        self.parts_layout = QVBoxLayout()
        self.parts_layout.setSpacing(6)
        self.parts_layout.addStretch()
        parts_container.setLayout(self.parts_layout)
        parts_scroll.setWidget(parts_container)
        pt_layout.addWidget(parts_scroll)

        self.merge_btn = QPushButton("🔗  MERGE ALL PARTS INTO FINAL CHAPTER")
        self.merge_btn.setMinimumHeight(50)
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self._merge_all)
        self.merge_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,152,0,0.80); color:white;
                border:none; border-radius:6px;
                font-size:15px; font-weight:bold;
            }
            QPushButton:hover  { background: rgba(255,152,0,1.0); }
            QPushButton:disabled { background: rgba(80,80,80,0.5); }
        """)
        pt_layout.addWidget(self.merge_btn)

        parts_tab.setLayout(pt_layout)
        self.right_tabs.addTab(parts_tab, "📚 Generated Parts")

        # --- Log tab ---
        log_tab = QWidget()
        ll = QVBoxLayout()
        ll.setContentsMargins(4, 4, 4, 4)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family:'Courier New', monospace; font-size:11px;")
        self.log_text.setPlaceholderText("Generation log appears here…")
        ll.addWidget(self.log_text)
        log_tab.setLayout(ll)
        self.right_tabs.addTab(log_tab, "📋 Generation Log")

        vl.addWidget(self.right_tabs)
        w.setLayout(vl)
        return w

    # ── group boxes ──────────────────────────────────────────────────────────

    def _make_chapter_info(self) -> QGroupBox:
        g = QGroupBox("Chapter Information")
        f = QFormLayout()

        self.chapter_number_input = QSpinBox()
        self.chapter_number_input.setRange(1, 9999)
        self.chapter_number_input.setValue(1)
        f.addRow("Chapter Number:", self.chapter_number_input)

        self.chapter_title_input = QLineEdit()
        self.chapter_title_input.setPlaceholderText("Final chapter title…")
        f.addRow("Chapter Title:", self.chapter_title_input)

        g.setLayout(f)
        return g

    def _make_part_settings(self) -> QGroupBox:
        """Part-specific settings — placed ABOVE context by request."""
        g = QGroupBox(f"Part {self.current_part_number} Settings")
        g.setStyleSheet("QGroupBox { border:2px solid rgba(76,175,80,0.5); }")
        vl = QVBoxLayout()
        vl.setSpacing(8)

        # part number label
        self.part_num_label = QLabel(f"▶  Generating: Part {self.current_part_number}")
        self.part_num_label.setStyleSheet("font-weight:bold; color:rgba(76,175,80,1.0);")
        vl.addWidget(self.part_num_label)

        f = QFormLayout()

        # word count
        wc_row = QHBoxLayout()
        self.part_word_count_slider = QSlider(Qt.Horizontal)
        self.part_word_count_slider.setRange(300, 4000)
        self.part_word_count_slider.setValue(1500)
        self.part_word_count_slider.valueChanged.connect(
            lambda v: self.part_word_count_label.setText(f"{v} words")
        )
        wc_row.addWidget(self.part_word_count_slider)
        self.part_word_count_label = QLabel("1500 words")
        self.part_word_count_label.setMinimumWidth(72)
        wc_row.addWidget(self.part_word_count_label)
        f.addRow("Word Count:", wc_row)

        # POV character (requested addition)
        self.pov_combo = QComboBox()
        self.pov_combo.setEditable(True)
        self.pov_combo.addItems(["Auto-select", "Third-person omniscient", "Third-person limited",
                                  "First-person"])
        f.addRow("POV Character:", self.pov_combo)

        # Mood/Tone (requested addition)
        self.mood_combo = QComboBox()
        self.mood_combo.setEditable(True)
        self.mood_combo.addItems([
            "Dramatic", "Tense", "Action-packed", "Mysterious",
            "Emotional", "Lighthearted", "Suspenseful", "Dark", "Hopeful"
        ])
        f.addRow("Mood / Tone:", self.mood_combo)

        vl.addLayout(f)

        # story progression (main prompt)
        pg_lbl = QLabel("What happens in this part: *")
        pg_lbl.setStyleSheet("font-weight:bold; color:rgba(76,175,80,1.0);")
        vl.addWidget(pg_lbl)

        self.part_progression_input = QTextEdit()
        self.part_progression_input.setPlaceholderText(
            f"Describe what should happen in Part {self.current_part_number}…\n"
            "e.g. The hero enters the ruins and discovers the sealed chamber."
        )
        self.part_progression_input.setMaximumHeight(75)
        self.part_progression_input.setStyleSheet("border:2px solid rgba(76,175,80,0.5);")
        vl.addWidget(self.part_progression_input)

        # plot points
        pp_lbl = QLabel("Specific plot points (optional):")
        pp_lbl.setStyleSheet("font-weight:bold;")
        vl.addWidget(pp_lbl)

        self.part_plot_points_input = QTextEdit()
        self.part_plot_points_input.setPlaceholderText("Key moments, dialogue beats, reveals…")
        self.part_plot_points_input.setMaximumHeight(55)
        vl.addWidget(self.part_plot_points_input)

        # style instructions (requested addition)
        st_lbl = QLabel("Style Instructions (optional):")
        st_lbl.setStyleSheet("font-weight:bold;")
        vl.addWidget(st_lbl)

        self.style_input = QTextEdit()
        self.style_input.setPlaceholderText("Writing style, pacing, tone preferences…")
        self.style_input.setMaximumHeight(45)
        vl.addWidget(self.style_input)

        g.setLayout(vl)
        return g

    def _make_model_settings(self) -> QGroupBox:
        g = QGroupBox("AI Model Settings")
        f = QFormLayout()

        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama3.1:8b (Fast)", "llama3.1:70b (Quality)"])
        f.addRow("Model:", self.model_combo)

        t_row = QHBoxLayout()
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(10, 100)
        self.temperature_slider.setValue(70)
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v/100:.2f}")
        )
        t_row.addWidget(self.temperature_slider)
        self.temperature_label = QLabel("0.70")
        self.temperature_label.setMinimumWidth(38)
        t_row.addWidget(self.temperature_label)
        f.addRow("Temperature:", t_row)

        g.setLayout(f)
        return g

    def _make_context_group(self) -> QGroupBox:
        g = QGroupBox("Context Selection  (applied to ALL parts)")
    
        # Add collapse button to title
        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
    
        # Header with collapse toggle
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
    
        # Resize handle hint
        resize_hint = QLabel("⇕ Drag to resize")
        resize_hint.setStyleSheet("font-size:9px; color:rgba(255,255,255,0.4);")
        header_row.addWidget(resize_hint)
    
        main_layout.addLayout(header_row)
    
        # Collapsible content with resizable scroll area
        self.ctx_content = QWidget()
        ctx_layout = QVBoxLayout()
        ctx_layout.setContentsMargins(0, 0, 0, 0)
        ctx_layout.setSpacing(0)
    
        # Create resizable scroll area
        self.ctx_scroll = QScrollArea()
        self.ctx_scroll.setWidgetResizable(True)
        self.ctx_scroll.setFrameShape(QScrollArea.NoFrame)
        self.ctx_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set initial height (can be adjusted by user)
        self.ctx_scroll.setMinimumHeight(150)
        self.ctx_scroll.setMaximumHeight(16777215)  # Remove max constraint for full resize
    
        inner = QWidget()
        il = QVBoxLayout()
        il.setSpacing(4)
    
        self.ctx_characters    = CheckboxSection("👤 Characters")
        self.ctx_locations     = CheckboxSection("📍 Locations")
        self.ctx_organizations = CheckboxSection("🏛️  Organizations")
        self.ctx_powers        = CheckboxSection("⚡ Power Systems")
        self.ctx_bestiary      = CheckboxSection("🐉 Creatures")
        self.ctx_lore          = CheckboxSection("📜 Lore")
        self.ctx_items         = CheckboxSection("🗡️ Items")
    
        for s in [self.ctx_characters, self.ctx_locations, self.ctx_organizations,
                  self.ctx_powers, self.ctx_bestiary, self.ctx_lore, self.ctx_items]:
            il.addWidget(s)
    
        il.addStretch()
        inner.setLayout(il)
        self.ctx_scroll.setWidget(inner)
        
        # Add resize handle at the bottom
        ctx_layout.addWidget(self.ctx_scroll, 1)  # Stretch factor 1 to allow growth
        
        # Add a visual resize handle
        resize_handle = QFrame()
        resize_handle.setFrameShape(QFrame.HLine)
        resize_handle.setFrameShadow(QFrame.Sunken)
        resize_handle.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.2);
                max-height: 3px;
                min-height: 3px;
            }
            QFrame:hover {
                background: rgba(33,150,243,0.6);
            }
        """)
        resize_handle.setCursor(Qt.SizeVerCursor)
        resize_handle.setMouseTracking(True)
        
        # Install event filter for resize functionality
        resize_handle.installEventFilter(self)
        resize_handle.setProperty('resize_target', 'ctx_scroll')
        
        ctx_layout.addWidget(resize_handle)
        
        self.ctx_content.setLayout(ctx_layout)
        main_layout.addWidget(self.ctx_content, 1)  # Allow this to expand
    
        # Connect collapse toggle
        self.ctx_collapse_btn.toggled.connect(self._toggle_context_section)
    
        g.setLayout(main_layout)
        return g
    
    def _toggle_context_section(self, expanded: bool):
        """Toggle context section visibility."""
        self.ctx_content.setVisible(expanded)
        self.ctx_collapse_btn.setText("▼" if expanded else "▶")
    
    def eventFilter(self, obj, event):
        """Handle resize dragging for context scroll area."""
        if hasattr(obj, 'property') and obj.property('resize_target') == 'ctx_scroll':
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._resize_start_y = event.globalY()
                    self._resize_start_height = self.ctx_scroll.height()
                    return True
            elif event.type() == event.MouseMove:
                if hasattr(self, '_resize_start_y'):
                    delta = event.globalY() - self._resize_start_y
                    new_height = max(150, self._resize_start_height + delta)
                    self.ctx_scroll.setMinimumHeight(new_height)
                    self.ctx_scroll.setMaximumHeight(new_height)
                    return True
            elif event.type() == event.MouseButtonRelease:
                if hasattr(self, '_resize_start_y'):
                    delattr(self, '_resize_start_y')
                    # After resize, allow it to expand further if needed
                    self.ctx_scroll.setMaximumHeight(16777215)
                    return True
        
        return super().eventFilter(obj, event)

    def _make_gen_controls(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout()
        vl.setContentsMargins(0, 6, 0, 0)
        vl.setSpacing(4)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        vl.addWidget(self.progress_bar)

        self.status_label = QLabel(f"Ready to generate Part {self.current_part_number}")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color:rgba(255,255,255,0.65); font-size:11px;")
        vl.addWidget(self.status_label)

        btn_row = QHBoxLayout()

        # Cancel button (ABOVE generate, requested)
        self.cancel_btn = QPushButton("⛔  Cancel Generation")
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_generation)
        self.cancel_btn.setStyleSheet("""
            QPushButton { background:rgba(244,67,54,0.75); color:white;
                          border:none; border-radius:5px; font-weight:bold; }
            QPushButton:hover { background:rgba(244,67,54,1.0); }
        """)
        btn_row.addWidget(self.cancel_btn)

        self.generate_btn = QPushButton(f"✨  Generate Part {self.current_part_number}")
        self.generate_btn.setMinimumHeight(46)
        self.generate_btn.clicked.connect(self._generate_part)
        self.generate_btn.setStyleSheet("""
            QPushButton { background:rgba(76,175,80,0.80); color:white;
                          border:none; border-radius:5px;
                          font-size:15px; font-weight:bold; }
            QPushButton:hover    { background:rgba(76,175,80,1.0); }
            QPushButton:disabled { background:rgba(80,80,80,0.5); }
        """)
        btn_row.addWidget(self.generate_btn)

        vl.addLayout(btn_row)
        w.setLayout(vl)
        return w

    # ---------------------------------------------------------------- LOGIC --

    def load_data(self):
        if not self.current_story_id:
            return
        next_ch = db_manager.get_next_chapter_number(self.current_story_id)
        self.chapter_number_input.setValue(next_ch)
        self._populate_pov_combo()
        self._populate_context_lists()
        self._load_existing_parts()

    def _populate_pov_combo(self):
        """Populate POV combo from saved characters."""
        if not self.current_story_id:
            return
        try:
            chars = db_manager.get_characters(self.current_story_id)
            self.pov_combo.clear()
            self.pov_combo.addItem("Auto-select")
            self.pov_combo.addItem("Third-person omniscient")
            self.pov_combo.addItem("Third-person limited")
            self.pov_combo.addItem("First-person")
            for c in chars:
                self.pov_combo.addItem(c.get('name', ''))
        except Exception as e:
            self.log_error(f"POV combo populate error: {e}")

    def _populate_context_lists(self):
        if not self.current_story_id:
            return
        try:
            from models.character import Character
            from models.location import Location
            from models.creature import Creature

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
            self.log_error(f"Context populate error: {e}")

    def _load_existing_parts(self):
        """Load any parts already saved for the current chapter."""
        if not self.current_story_id:
            return
        ch = self.chapter_number_input.value()
        parts = db_manager.get_chapter_parts(self.current_story_id, ch)
        for p in parts:
            if not any(x.get('id') == p.get('id') for x in self.generated_parts):
                self.generated_parts.append(p)
                self._add_part_card(p)
        if self.generated_parts:
            self.current_part_number = max(p.get('part_number', 0) for p in self.generated_parts) + 1
            self._update_part_ui()
        self._update_stats()

    def _get_selected_context(self) -> dict:
        return {
            'characters':    self.ctx_characters.get_selected_ids(),
            'locations':     self.ctx_locations.get_selected_ids(),
            'organizations': self.ctx_organizations.get_selected_ids(),
            'power_systems': self.ctx_powers.get_selected_ids(),
            'creatures':     self.ctx_bestiary.get_selected_ids(),
            'lore':          self.ctx_lore.get_selected_ids(),
            'items':         self.ctx_items.get_selected_ids(),
        }

    # ── generation ────────────────────────────────────────────────────────────

    def _generate_part(self):
        if not self.current_story_id:
            self.show_error("No story selected.")
            return

        progression = self.part_progression_input.toPlainText().strip()
        if not progression:
            self.show_warning("Please describe what should happen in this part.")
            return

        ch_num  = self.chapter_number_input.value()
        wc      = self.part_word_count_slider.value()
        model   = 'llama3.1:8b' if self.model_combo.currentIndex() == 0 else 'llama3.1:70b'
        temp    = self.temperature_slider.value() / 100.0
        context = self._get_selected_context()

        # build an augmented progression string with POV/Mood
        pov   = self.pov_combo.currentText()
        mood  = self.mood_combo.currentText()
        style = self.style_input.toPlainText().strip()
        extra = f"\nPOV: {pov}\nMood/Tone: {mood}"
        if style:
            extra += f"\nStyle: {style}"
        plot_points = self.part_plot_points_input.toPlainText().strip()

        # UI → generating state
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Generating Part {self.current_part_number}…")
        self.right_tabs.setCurrentIndex(1)  # show log tab
        self._append_log(f"▶ Starting Part {self.current_part_number} generation…")

        # wire signals
        try:
            ai_controller.generation_progress.disconnect()
            ai_controller.generation_complete.disconnect()
            ai_controller.generation_failed.disconnect()
            ai_controller.log_updated.disconnect()
        except Exception:
            pass

        ai_controller.generation_progress.connect(self.progress_bar.setValue)
        ai_controller.generation_complete.connect(self._on_part_complete)
        ai_controller.generation_failed.connect(self._on_generation_error)
        ai_controller.log_updated.connect(self._append_log)

        ok = ai_controller.generate_chapter_part(
            story_id=self.current_story_id,
            chapter_number=ch_num,
            part_number=self.current_part_number,
            title=f"Part {self.current_part_number}",
            target_word_count=wc,
            story_progression_prompt=progression + extra + ("\n\nPlot points:\n" + plot_points if plot_points else ""),
            model=model,
            temperature=temp,
            selected_context=context,
        )

        if not ok:
            self.show_error("Failed to start generation.")
            self._reset_gen_ui()

    def _cancel_generation(self):
        ai_controller.cancel_generation()
        self._append_log("⛔ Generation cancelled by user.")
        self.status_label.setText("Cancelled.")
        self._reset_gen_ui()

    def _on_part_complete(self, signal_id: int):
        """
        ai_controller emits -part_id for parts.
        We resolve the actual part from the DB.
        """
        try:
            part_id = abs(signal_id)
            part_data = db_manager.get_entity('chapter_parts', part_id, self.current_story_id)

            if not part_data:
                # Fallback: fetch latest part for the current chapter
                parts = db_manager.get_chapter_parts(
                    self.current_story_id,
                    self.chapter_number_input.value()
                )
                if parts:
                    part_data = parts[-1]

            if part_data:
                self.generated_parts.append(part_data)
                self._add_part_card(part_data)
                self._update_stats()
                self.current_part_number += 1
                self._update_part_ui()
                self._reset_gen_ui()
                self.part_progression_input.clear()
                self.part_plot_points_input.clear()
                wc = part_data.get('word_count', 0)
                self._append_log(f"✅ Part {part_data.get('part_number')} saved — {wc} words.")
                self.right_tabs.setCurrentIndex(0)   # switch to parts tab
                self.show_success(f"Part {part_data.get('part_number')} generated & saved!")
            else:
                self._on_generation_error("Part saved but could not be retrieved.")

        except Exception as e:
            self.log_error(f"on_part_complete error: {e}")
            self._on_generation_error(str(e))

    def _on_generation_error(self, msg: str):
        self.show_error(f"Generation failed: {msg}")
        self._append_log(f"✗ Error: {msg}")
        self.status_label.setText("Generation failed.")
        self._reset_gen_ui()

    def _reset_gen_ui(self):
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def _update_part_ui(self):
        self._part_group_box.setTitle(f"Part {self.current_part_number} Settings")
        self.part_num_label.setText(f"▶  Generating: Part {self.current_part_number}")
        self.part_progression_input.setPlaceholderText(
            f"Describe what should happen in Part {self.current_part_number}…"
        )
        self.generate_btn.setText(f"✨  Generate Part {self.current_part_number}")
        self.status_label.setText(f"Ready to generate Part {self.current_part_number}")

    def _append_log(self, msg: str):
        if self.log_text:
            self.log_text.append(msg)

    # ── part card management ──────────────────────────────────────────────────

    def _add_part_card(self, part_data: dict):
        card = PartCard(part_data)
        card.view_requested.connect(self._view_part)
        card.edit_requested.connect(self._edit_part)
        card.regenerate_requested.connect(self._regenerate_part)
        card.delete_requested.connect(self._delete_part)
        # insert before stretch
        count = self.parts_layout.count()
        self.parts_layout.insertWidget(count - 1, card)

    def _update_stats(self):
        n = len(self.generated_parts)
        total_wc = sum(p.get('word_count', 0) for p in self.generated_parts)
        self.parts_stats.setText(f"{n} part{'s' if n!=1 else ''} | {total_wc} total words")
        self.merge_btn.setEnabled(n > 0)

    def _find_part(self, part_id: int) -> dict | None:
        return next((p for p in self.generated_parts if p.get('id') == part_id), None)

    def _view_part(self, part_id: int):
        part = self._find_part(part_id)
        if not part:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Part {part.get('part_number')} — {part.get('title','')}")
        dlg.setMinimumSize(680, 480)
        vl = QVBoxLayout()
        viewer = QTextEdit()
        viewer.setPlainText(part.get('content', ''))
        viewer.setReadOnly(True)
        vl.addWidget(viewer)
        vl.addWidget(QLabel(f"Words: {part.get('word_count',0)}  |  Created: {part.get('created_at','')}"))
        close = QPushButton("Close")
        close.clicked.connect(dlg.accept)
        vl.addWidget(close)
        dlg.setLayout(vl)
        dlg.exec_()

    def _edit_part(self, part_id: int):
        part = self._find_part(part_id)
        if not part:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edit Part {part.get('part_number')}")
        dlg.setMinimumSize(680, 480)
        vl = QVBoxLayout()
        editor = QTextEdit()
        editor.setPlainText(part.get('content', ''))
        vl.addWidget(editor)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        vl.addWidget(btns)
        dlg.setLayout(vl)
        if dlg.exec_() == QDialog.Accepted:
            new_content = editor.toPlainText()
            part['content'] = new_content
            part['word_count'] = len(new_content.split())
            db_manager.update_entity('chapter_parts', part_id, self.current_story_id,
                                     {'content': new_content, 'word_count': part['word_count']})
            self._refresh_cards()
            self._update_stats()
            self.show_success("Part updated.")

    def _regenerate_part(self, part_id: int):
        part = self._find_part(part_id)
        if not part:
            return
        if not self.confirm_action("Regenerate Part",
                                   f"Delete and regenerate Part {part.get('part_number')}?"):
            return
        # delete existing
        db_manager.delete_chapter_part(self.current_story_id, part_id)
        self.generated_parts = [p for p in self.generated_parts if p.get('id') != part_id]
        self.current_part_number = part.get('part_number', self.current_part_number)
        self._refresh_cards()
        self._update_stats()
        self._update_part_ui()
        self.show_info(f"Part {self.current_part_number} removed. Adjust settings and generate again.")

    def _delete_part(self, part_id: int):
        part = self._find_part(part_id)
        if not part:
            return
        if not self.confirm_action("Delete Part",
                                   f"Permanently delete Part {part.get('part_number')}?"):
            return
        db_manager.delete_chapter_part(self.current_story_id, part_id)
        self.generated_parts = [p for p in self.generated_parts if p.get('id') != part_id]
        self._refresh_cards()
        self._update_stats()
        self.show_success("Part deleted.")

    def _refresh_cards(self):
        """Rebuild all part cards from self.generated_parts."""
        while self.parts_layout.count() > 1:
            item = self.parts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for p in sorted(self.generated_parts, key=lambda x: x.get('part_number', 0)):
            self._add_part_card(p)

    # ── merge ─────────────────────────────────────────────────────────────────

    def _merge_all(self):
        if not self.generated_parts:
            return
        ch_num  = self.chapter_number_input.value()
        ch_title = self.chapter_title_input.text().strip() or f"Chapter {ch_num}"
        n = len(self.generated_parts)
        total_wc = sum(p.get('word_count', 0) for p in self.generated_parts)
        if not self.confirm_action("Merge Parts",
                                   f"Merge {n} parts ({total_wc} words) into '{ch_title}'?"):
            return
        part_ids = [p.get('id') for p in self.generated_parts]
        ch_id = db_manager.merge_chapter_parts(
            self.current_story_id, ch_num, part_ids, ch_title
        )
        if ch_id:
            self.show_success(f"Merged into {ch_title}  ({total_wc} words)!")
            self.generated_parts.clear()
            self._refresh_cards()
            self._update_stats()
            self.current_part_number = 1
            self._update_part_ui()
            try:
                self.window().switch_view('chapters_list')
            except Exception:
                pass
        else:
            self.show_error("Merge failed — check logs.")

    # ── navigation ────────────────────────────────────────────────────────────

    def _go_back(self):
        try:
            self.window().switch_view('chapter_generator')
        except Exception:
            pass

    # ── base overrides ────────────────────────────────────────────────────────

    def save_data(self):
        pass   # Parts are saved immediately on generation

    def validate_input(self) -> bool:
        return self.current_story_id is not None

    def clear_form(self):
        pass