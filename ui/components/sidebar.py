"""
Sidebar Component
Navigation sidebar with view switching.
UPDATED: Added 'Chapter by Parts Generator' entry under Generate.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from utils.logger import LoggerMixin


class Sidebar(QWidget, LoggerMixin):
    """Sidebar navigation — emits view_changed(str) on click."""

    view_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.active_button = None
        self.buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(200)
        self.setObjectName("sidebar")

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)

        nav_items = [
            ("dashboard",               "📊 Dashboard"),
            ("story",                   "📖 Story"),
            ("characters",              "👥 Characters"),
            ("world",                   "🗺️  World"),
            ("items",                   "🗡️  Items"),
            ("bestiary",               "🐉 Bestiary"),
            ("lore",                    "📜 Lore"),
            ("organizations",           "🏛️  Organizations"),
            ("powers",                  "⚡ Powers"),
            ("chapter_generator",       "✍️  Generate"),
            ("chapter_parts_generator", "📝 Parts Generator"),   
            ("chapters_list",           "📚 Chapters"),
            ("settings",                "⚙️  Settings"),
        ]

        for view_id, label in nav_items:
            btn = QPushButton(label)
            btn.setObjectName(f"nav_button_{view_id}")
            btn.setMinimumHeight(40)
            btn.setCursor(Qt.PointingHandCursor)

            # Indent the Parts Generator button slightly to show it's related
            if view_id == "chapter_parts_generator":
                btn.setStyleSheet("padding-left: 20px; font-size: 11px;")

            btn.clicked.connect(lambda checked, v=view_id: self._on_button_clicked(v))
            self.buttons[view_id] = btn
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)
        self.set_active_button("dashboard")

    def _on_button_clicked(self, view_id: str):
        self.log_info(f"Sidebar: {view_id}")
        self.set_active_button(view_id)
        self.view_changed.emit(view_id)

    def set_active_button(self, view_id: str):
        if self.active_button:
            self.active_button.setProperty("active", False)
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)

        if view_id in self.buttons:
            self.active_button = self.buttons[view_id]
            self.active_button.setProperty("active", True)
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)