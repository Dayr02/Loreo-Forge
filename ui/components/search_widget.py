"""
Search Widget
Live search with a background QThread worker (no UI freeze), name/title-only
matching (no false positives), glow highlighting for in-story results, and
auto-navigation including correct entry-level opening for every view.

"""

from typing import Dict, List, Optional, Any

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QApplication,
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QEvent, QPoint, QThread,
)
from PyQt5.QtGui import QFont, QColor

from utils.logger import LoggerMixin


# ── entity type → (display label, view_name, icon) ───────────────────────────
ENTITY_CONFIG: Dict[str, tuple] = {
    'characters':    ('Characters',    'characters',    '👤'),
    'locations':     ('Locations',     'world',         '📍'),
    'lore_entries':  ('Lore',          'lore',          '📜'),
    'bestiary':      ('Creatures',     'bestiary',      '🐉'),
    'organizations': ('Organizations', 'organizations', '🏛️'),
    'power_systems': ('Powers',        'powers',        '⚡'),
    'items':         ('Items',         'items',         '🗡️'),
    'chapters':      ('Chapters',      'chapters_list', '📖'),
}


# ─────────────────────────────────────────────────────────────────────────────
# Background worker
# ─────────────────────────────────────────────────────────────────────────────

class _SearchWorker(QThread):
    """
    Runs all DB queries in a background thread.
    Sets _cancelled=True to abort mid-loop when a newer search is requested.
    Only emits results_ready when it completes without being cancelled.
    """

    results_ready = pyqtSignal(dict, dict)

    def __init__(
        self,
        query: str,
        current_story_id: Optional[int],
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._query           = query
        self._current_story_id = current_story_id
        self._cancelled       = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        in_story: Dict[str, List[Dict[str, Any]]] = {}
        other:    Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
        try:
            if self._current_story_id is not None:
                in_story = self._search_story(self._current_story_id)
                if not self._cancelled:
                    other = self._global_search(exclude=self._current_story_id)
            else:
                other = self._global_search(exclude=None)
        except Exception:
            pass
        if not self._cancelled:
            self.results_ready.emit(in_story, other)

    # ── thread-local story search ─────────────────────────────────────────────

    def _search_story(self, story_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Open a FRESH sqlite3 connection for this thread, run name/title-only
        queries, close the connection.  Never touches db_manager._connections
        (which were created on the main thread and cannot be shared).
        """
        import sqlite3
        from config.settings import settings

        db_path = settings.get_story_db_path(story_id)
        if not db_path.exists():
            return {}

        pattern = f"%{self._query.strip()}%"
        results: Dict[str, List[Dict[str, Any]]] = {}

        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.row_factory = sqlite3.Row
            cur  = conn.cursor()

            # characters — name only
            cur.execute(
                "SELECT * FROM characters WHERE story_id=? AND name LIKE ?"
                " ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cur.fetchall()
            if rows:
                results['characters'] = [dict(r) for r in rows]
            if self._cancelled:
                return results

            # locations — name only
            cur.execute(
                "SELECT * FROM locations WHERE story_id=? AND name LIKE ?"
                " ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cur.fetchall()
            if rows:
                results['locations'] = [dict(r) for r in rows]
            if self._cancelled:
                return results

            # lore_entries — title only
            cur.execute(
                "SELECT * FROM lore_entries WHERE story_id=? AND title LIKE ?"
                " ORDER BY importance DESC, title ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cur.fetchall()
            if rows:
                results['lore_entries'] = [dict(r) for r in rows]
            if self._cancelled:
                return results

            # bestiary — name only
            cur.execute(
                "SELECT * FROM bestiary WHERE story_id=? AND name LIKE ?"
                " ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cur.fetchall()
            if rows:
                results['bestiary'] = [dict(r) for r in rows]
            if self._cancelled:
                return results

            # organizations — name only
            cur.execute(
                "SELECT * FROM organizations WHERE story_id=? AND name LIKE ?"
                " ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cur.fetchall()
            if rows:
                results['organizations'] = [dict(r) for r in rows]
            if self._cancelled:
                return results

            # power_systems — name only
            cur.execute(
                "SELECT * FROM power_systems WHERE story_id=? AND name LIKE ?"
                " ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cur.fetchall()
            if rows:
                results['power_systems'] = [dict(r) for r in rows]
            if self._cancelled:
                return results

            # items — name only
            cur.execute(
                "SELECT * FROM items WHERE story_id=? AND name LIKE ?"
                " ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cur.fetchall()
            if rows:
                results['items'] = [dict(r) for r in rows]
            if self._cancelled:
                return results

            # chapters — title only
            cur.execute(
                "SELECT * FROM chapters WHERE story_id=? AND title LIKE ?"
                " ORDER BY chapter_number ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cur.fetchall()
            if rows:
                results['chapters'] = [dict(r) for r in rows]

        except Exception as e:
            pass  # DB may not have all tables yet; return partial results
        finally:
            try:
                conn.close()
            except Exception:
                pass

        return results

    # ── cross-story search ────────────────────────────────────────────────────

    def _global_search(
        self, exclude: Optional[int]
    ) -> Dict[int, Dict[str, List[Dict[str, Any]]]]:
        """
        master_db was created with check_same_thread=False so its single
        persistent connection IS safe to call from this worker thread.
        """
        from database.master_db import master_db
        try:
            rows = master_db.fetch_all("SELECT id FROM stories")
        except Exception:
            return {}

        combined: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
        for row in rows:
            if self._cancelled:
                break
            sid = row['id']
            if exclude is not None and sid == exclude:
                continue
            story_results = self._search_story(sid)
            if story_results:
                combined[sid] = story_results
        return combined


# ─────────────────────────────────────────────────────────────────────────────
# Keyboard event filter
# ─────────────────────────────────────────────────────────────────────────────

class _InputEventFilter(QObject):
    def __init__(self, search_widget: 'SearchWidget'):
        super().__init__(search_widget)
        self._sw = search_widget

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # type: ignore[override]
        if event.type() != QEvent.KeyPress:
            return False
        key = event.key()
        lst = self._sw.results_list
        if not lst.isVisible():
            return False
        if key == Qt.Key_Down:
            lst.setCurrentRow(min(lst.currentRow() + 1, lst.count() - 1))
            return True
        if key == Qt.Key_Up:
            lst.setCurrentRow(max(lst.currentRow() - 1, 0))
            return True
        if key in (Qt.Key_Return, Qt.Key_Enter):
            item = lst.currentItem()
            if item:
                self._sw._on_item_clicked(item)
            return True
        if key == Qt.Key_Escape:
            lst.hide()
            return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
# SearchWidget
# ─────────────────────────────────────────────────────────────────────────────

class SearchWidget(QWidget, LoggerMixin):
    """
    Top-bar search widget.

    * Runs all DB work in a QThread — typing never freezes the UI.
    * Searches only name / title columns — no false positives from body text.
    * In-story results glow amber; other-story results are muted grey.

    Emits
    ─────
    result_selected(entity_type: str, entity_id: int,
                    view_name: str,   story_id: int)
    """

    result_selected = pyqtSignal(str, int, str, int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_story_id: Optional[int] = None

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._start_search)

        self._worker: Optional[_SearchWorker] = None

        self._setup_ui()

    # ─────────────────────────────────────────── UI setup ─────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("🔍  Search characters, lore, chapters…")
        self.search_input.setMinimumWidth(280)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: rgba(255,140,0,0.7);
                background-color: rgba(255,255,255,0.12);
            }
        """)
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._start_search)
        layout.addWidget(self.search_input)

        self.results_list = QListWidget()
        self.results_list.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.results_list.setFocusPolicy(Qt.NoFocus)
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                border: 1px solid rgba(255,140,0,0.55);
                border-radius: 6px;
                padding: 4px;
                color: white;
                font-size: 12px;
            }
            QListWidget::item { padding: 5px 8px; border-radius: 4px; }
            QListWidget::item:hover    { background-color: rgba(255,140,0,0.15); }
            QListWidget::item:selected { background-color: rgba(255,140,0,0.30); }
        """)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        self.results_list.hide()

        self._key_filter = _InputEventFilter(self)
        self.search_input.installEventFilter(self._key_filter)

        self.setLayout(layout)

    # ─────────────────────────────────────────── public API ───────────────────

    def set_story_id(self, story_id: Optional[int]) -> None:
        self.current_story_id = story_id

    # ─────────────────────────────────────────── text change ──────────────────

    def _on_text_changed(self, text: str) -> None:
        self._cancel_worker()
        self.results_list.hide()
        if len(text.strip()) >= 2:
            self._debounce_timer.start(300)
        else:
            self._debounce_timer.stop()

    # ─────────────────────────────────────────── search launch ────────────────

    def _start_search(self) -> None:
        query = self.search_input.text().strip()
        if not query or len(query) < 2:
            return
        self._cancel_worker()
        self._worker = _SearchWorker(query, self.current_story_id, self)
        self._worker.results_ready.connect(self._on_results_ready)
        self._worker.start()

    def _cancel_worker(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            try:
                self._worker.results_ready.disconnect()
            except TypeError:
                pass
            self._worker = None

    # ─────────────────────────────────────────── result rendering ─────────────

    def _on_results_ready(
        self,
        in_story:  Dict[str, List[Dict[str, Any]]],
        all_other: Dict[int, Dict[str, List[Dict[str, Any]]]],
    ) -> None:
        self.results_list.clear()

        total = (sum(len(v) for v in in_story.values()) +
                 sum(len(v) for sid_d in all_other.values()
                     for v in sid_d.values()))

        if total == 0:
            ph = QListWidgetItem("  No results found")
            ph.setFlags(Qt.NoItemFlags)
            ph.setForeground(QColor("gray"))
            self.results_list.addItem(ph)
        else:
            if in_story:
                self._add_section_header("✦ Current Story", glow=True)
                self._add_grouped_results(in_story, self.current_story_id, glow=True)
            if all_other:
                self._add_section_header("◌ Other Stories", glow=False)
                for story_id, story_results in all_other.items():
                    self._add_grouped_results(story_results, story_id, glow=False)

        self._show_dropdown()

    def _add_section_header(self, label: str, glow: bool) -> None:
        h = QListWidgetItem(f"  {label}")
        h.setFlags(Qt.NoItemFlags)
        f = QFont()
        f.setBold(True)
        f.setPointSize(9)
        h.setFont(f)
        h.setForeground(QColor("#ff8c00" if glow else "#888888"))
        self.results_list.addItem(h)

    def _add_grouped_results(
        self,
        results: Dict[str, List[Dict[str, Any]]],
        story_id: Optional[int],
        glow: bool,
    ) -> None:
        for entity_type, items in results.items():
            if not items:
                continue
            config = ENTITY_CONFIG.get(entity_type)
            if not config:
                continue
            display_name, view_name, icon = config

            sub = QListWidgetItem(f"    {icon} {display_name}  ({len(items)})")
            sub.setFlags(Qt.NoItemFlags)
            sub.setForeground(QColor("#cccccc" if glow else "#666666"))
            self.results_list.addItem(sub)

            for raw in items[:8]:
                name = (raw.get('name') or raw.get('title')
                        or f"#{raw.get('id', '?')}")
                subtitle = self._make_subtitle(entity_type, raw)
                item = QListWidgetItem(f"        {name}  {subtitle}")
                item.setData(Qt.UserRole, {
                    'entity_type': entity_type,
                    'entity_id':   raw.get('id'),
                    'view_name':   view_name,
                    'story_id':    story_id,
                    'glow':        glow,
                })
                if glow:
                    item.setForeground(QColor("#ffd700"))
                    f = QFont()
                    f.setBold(True)
                    item.setFont(f)
                    item.setBackground(QColor(255, 140, 0, 28))
                else:
                    item.setForeground(QColor("#909090"))
                self.results_list.addItem(item)

    @staticmethod
    def _make_subtitle(entity_type: str, raw: Dict[str, Any]) -> str:
        if entity_type == 'characters':
            role = raw.get('role', '')
            return f"— {role}" if role else ""
        if entity_type == 'chapters':
            n = raw.get('chapter_number', '')
            return f"— Ch.{n}" if n else ""
        if entity_type == 'lore_entries':
            cat = raw.get('category', '')
            return f"— {cat}" if cat else ""
        if entity_type == 'bestiary':
            cat = raw.get('category', '')
            return f"— {cat}" if cat else ""
        return ""

    def _show_dropdown(self) -> None:
        if self.results_list.count() == 0:
            return
        top_window = self.window()
        if top_window is None or not top_window.isVisible():
            return
        global_pos: QPoint = self.search_input.mapToGlobal(
            self.search_input.rect().bottomLeft()
        )
        screen_w = QApplication.desktop().screenGeometry().width()
        popup_w  = max(self.search_input.width(), 360)
        if global_pos.x() + popup_w > screen_w:
            global_pos.setX(screen_w - popup_w - 8)
        rows    = min(self.results_list.count(), 14)
        popup_h = rows * 28 + 10
        self.results_list.setFixedWidth(popup_w)
        self.results_list.setFixedHeight(popup_h)
        self.results_list.move(global_pos)
        self.results_list.show()
        self.results_list.raise_()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.UserRole)
        if not data:
            return
        self.results_list.hide()
        self.search_input.clear()
        self.result_selected.emit(
            data['entity_type'],
            int(data['entity_id']),
            data['view_name'],
            int(data['story_id']),
        )

    def focusOutEvent(self, event: QEvent) -> None:  # type: ignore[override]
        QTimer.singleShot(200, self.results_list.hide)
        super().focusOutEvent(event)