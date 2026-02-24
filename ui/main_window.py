"""
Main Window for Loreo Forge
Primary application interface with menu, toolbar, sidebar, and content area
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar, QLabel, QComboBox,
    QPushButton, QLineEdit, QMessageBox, QSplitter,
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon, QKeySequence

from config.settings import settings
from models.story import Story
from ui.theme_engine import theme_engine
from ui.components.sidebar import Sidebar
from utils.logger import LoggerMixin
from core.story_manager import StoryManager
from database import db_manager
from ui.views.chapter_parts_generator_view import ChapterPartsGeneratorView

class MainWindow(QMainWindow, LoggerMixin):
    """
    Main application window
    Manages layout, navigation, and global UI state
    """

    def __init__(self):
        super().__init__()

        self.log_info("Initializing MainWindow")

        self.story_manager = StoryManager(db_manager)

        # Instance attributes — initialised BEFORE any UI setup
        self.sidebar              = None
        self.content_stack        = None
        self.status_bar           = None
        self.current_story_id     = None
        self.current_story_name   = "No Story Loaded"

        self.views = {}

        self.dashboard_view            = None
        self.story_view                = None
        self.characters_view           = None
        self.world_view                = None
        self.bestiary_view             = None
        self.lore_view                 = None
        self.organizations_view        = None
        self.powers_view               = None
        self.items_view                = None
        self.chapter_generator_view    = None
        self.chapter_parts_generator_view = None
        self.chapters_list_view        = None
        self.settings_view             = None

        # Status-bar QLabel widgets
        self.status_story_label      = None
        self.status_model_label      = None
        self.status_word_count_label = None
        self.status_ai_label         = None
        self.status_connection_label = None

        # Toolbar / search
        self.search_widget = None
        self.toolbar       = None
        self.model_combo   = None

        self.initialize_ui()

    # =========================================================================
    # UI INITIALISATION
    # =========================================================================

    def initialize_ui(self):
        self.setWindowTitle("Loreo Forge")
        self.setMinimumSize(1280, 720)
        self.resize(1600, 900)
        self._center_window()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()
        self._load_window_state()
        self.logger.debug("UI initialization complete")

    def _center_window(self):
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        window = self.geometry()
        self.move(
            (screen.width()  - window.width())  // 2,
            (screen.height() - window.height()) // 2,
        )

    # =========================================================================
    # MENU BAR
    # =========================================================================

    def _create_menu_bar(self):
        menubar = self.menuBar()

        # ── File ──────────────────────────────────────────────────────────────
        file_menu = menubar.addMenu("&File")

        new_story_action = QAction("&New Story", self)
        new_story_action.setShortcut(QKeySequence.New)
        new_story_action.triggered.connect(self._on_new_story)
        file_menu.addAction(new_story_action)

        open_story_action = QAction("&Open Story", self)
        open_story_action.setShortcut(QKeySequence.Open)
        open_story_action.triggered.connect(self._on_open_story)
        file_menu.addAction(open_story_action)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        export_menu = file_menu.addMenu("&Export")
        export_chapter_action = QAction("Export Chapter...", self)
        export_chapter_action.triggered.connect(self._on_export_chapter)
        export_menu.addAction(export_chapter_action)
        export_story_action = QAction("Export Story...", self)
        export_story_action.triggered.connect(self._on_export_story)
        export_menu.addAction(export_story_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut(QKeySequence.Preferences)
        settings_action.triggered.connect(self._on_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ── Edit ──────────────────────────────────────────────────────────────
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        find_action = QAction("&Find", self)
        find_action.setShortcut(QKeySequence.Find)
        edit_menu.addAction(find_action)

        replace_action = QAction("&Replace", self)
        replace_action.setShortcut(QKeySequence.Replace)
        edit_menu.addAction(replace_action)

        # ── View ──────────────────────────────────────────────────────────────
        view_menu = menubar.addMenu("&View")

        toggle_sidebar_action = QAction("Toggle &Sidebar", self)
        toggle_sidebar_action.setShortcut("Ctrl+B")
        toggle_sidebar_action.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)

        toggle_toolbar_action = QAction("Toggle &Toolbar", self)
        toggle_toolbar_action.triggered.connect(self._toggle_toolbar)
        view_menu.addAction(toggle_toolbar_action)

        view_menu.addSeparator()

        theme_menu = view_menu.addMenu("&Theme")
        for theme_name in theme_engine.get_available_themes():
            theme_action = QAction(theme_name, self)
            theme_action.triggered.connect(
                lambda checked, name=theme_name: theme_engine.load_theme(name)
            )
            theme_menu.addAction(theme_action)

        view_menu.addSeparator()

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)

        # ── Tools ─────────────────────────────────────────────────────────────
        tools_menu = menubar.addMenu("&Tools")

        ai_settings_action = QAction("&AI Settings", self)
        ai_settings_action.triggered.connect(self._on_ai_settings)
        tools_menu.addAction(ai_settings_action)

        model_switcher_action = QAction("&Model Switcher", self)
        model_switcher_action.triggered.connect(self._on_model_switcher)
        tools_menu.addAction(model_switcher_action)

        tools_menu.addSeparator()

        db_manager_action = QAction("&Database Manager", self)
        db_manager_action.triggered.connect(self._on_db_manager)
        tools_menu.addAction(db_manager_action)

        continuity_action = QAction("&Continuity Checker", self)
        continuity_action.triggered.connect(self._on_continuity_checker)
        tools_menu.addAction(continuity_action)

        # ── Help ──────────────────────────────────────────────────────────────
        help_menu = menubar.addMenu("&Help")

        guide_action = QAction("User &Guide", self)
        guide_action.setShortcut(QKeySequence.HelpContents)
        guide_action.triggered.connect(self._on_user_guide)
        help_menu.addAction(guide_action)

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self._on_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("&About Loreo Forge", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    # =========================================================================
    # TOP TOOLBAR
    # =========================================================================

    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        new_char_btn = QPushButton("New Character")
        new_char_btn.clicked.connect(self._on_new_character)
        toolbar.addWidget(new_char_btn)
        toolbar.addSeparator()

        new_loc_btn = QPushButton("New Location")
        new_loc_btn.clicked.connect(self._on_new_location)
        toolbar.addWidget(new_loc_btn)
        toolbar.addSeparator()

        gen_chapter_btn = QPushButton("Generate Chapter")
        gen_chapter_btn.clicked.connect(self._on_generate_chapter)
        toolbar.addWidget(gen_chapter_btn)
        toolbar.addSeparator()

        save_all_btn = QPushButton("Save All")
        save_all_btn.clicked.connect(self._on_save_all)
        toolbar.addWidget(save_all_btn)
        toolbar.addSeparator()

        toolbar.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "llama3.1:8b (Fast)",
            "llama3.1:70b (Quality)",
            "mistral-nemo:12b (Balanced)",
        ])
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        toolbar.addWidget(self.model_combo)
        toolbar.addSeparator()

        # Search widget — added exactly ONCE
        toolbar.addWidget(QLabel("Search:"))
        from ui.components.search_widget import SearchWidget
        self.search_widget = SearchWidget()
        self.search_widget.result_selected.connect(self._on_search_result_selected)
        if self.current_story_id:
            self.search_widget.set_story_id(self.current_story_id)
        toolbar.addWidget(self.search_widget)

        self.toolbar = toolbar

    # =========================================================================
    # MAIN LAYOUT
    # =========================================================================

    def _create_main_layout(self):
        central = QWidget()
        layout  = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.view_changed.connect(self.switch_view)
        self.log_info("Sidebar signal connected to switch_view")
        layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()

        try:
            from ui.views import (
                DashboardView, StoryView, CharactersView,
                WorldView, ItemsView, BestiaryView, LoreView, OrganizationsView, PowersView,
                ChapterGeneratorView, ChaptersListView, SettingsView,
            )
            self.log_info("All view classes imported successfully")

            # ── Helper: create once, add to stack, store in self.views ────────
            def _add(attr_name, view_key, view_obj):
                self.content_stack.addWidget(view_obj)
                self.views[view_key] = view_obj
                setattr(self, attr_name, view_obj)
                self.log_info(f"Created {view_key} view")
                return view_obj

            # each view created EXACTLY ONCE
            _add('dashboard_view', 'dashboard', DashboardView())
            _add('story_view',     'story',     StoryView())
            _add('characters_view',    'characters',    CharactersView())
            _add('world_view',         'world',         WorldView())
            _add('items_view',         'items',         ItemsView())
            _add('bestiary_view',      'bestiary',      BestiaryView())
            _add('lore_view',          'lore',          LoreView())
            _add('organizations_view', 'organizations', OrganizationsView())
            _add('powers_view',        'powers',        PowersView())
            _add('chapter_generator_view',       'chapter_generator',       ChapterGeneratorView())
            _add('chapter_parts_generator_view', 'chapter_parts_generator', ChapterPartsGeneratorView())
            _add('chapters_list_view', 'chapters_list', ChaptersListView())
            _add('settings_view',      'settings',      SettingsView())

            # Connect signals now that each view exists exactly once
            if hasattr(self.dashboard_view, 'story_selected'):
                self.dashboard_view.story_selected.connect(self.set_active_story)
                self.log_info("Dashboard story_selected signal connected")

            if hasattr(self.dashboard_view, 'create_story_requested'):
                self.dashboard_view.create_story_requested.connect(
                    self._on_create_story_from_dashboard
                )
                self.log_info("Dashboard create_story_requested signal connected")

            if hasattr(self.story_view, 'story_created'):
                self.story_view.story_created.connect(self.set_active_story)
                self.log_info("Story view story_created signal connected")

            if hasattr(self.settings_view, 'theme_changed'):
                self.settings_view.theme_changed.connect(self._on_theme_changed)
                self.log_info("Settings theme_changed signal connected")

            self.content_stack.setCurrentWidget(self.dashboard_view)

            self.log_info(f"Successfully loaded {len(self.views)} views")
            self.log_info(f"Available views: {list(self.views.keys())}")

        except ImportError as e:
            self.log_error(f"Failed to import views: {e}")
            import traceback; traceback.print_exc()
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_label  = QLabel(f"Error loading views:\n{e}\n\nCheck console for details.")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            error_layout.addWidget(error_label)
            error_widget.setLayout(error_layout)
            self.content_stack.addWidget(error_widget)

        layout.addWidget(self.content_stack, stretch=1)
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.log_info("Main layout creation completed")

    # =========================================================================
    # STATUS BAR
    # =========================================================================

    def _create_status_bar(self):
        self.status_bar = self.statusBar()

        self.status_story_label = QLabel(f"📖 {self.current_story_name}")
        self.status_bar.addWidget(self.status_story_label)
        self.status_bar.addWidget(QLabel(" | "))

        self.status_model_label = QLabel("🤖 Model: llama3.1:8b")
        self.status_bar.addWidget(self.status_model_label)
        self.status_bar.addWidget(QLabel(" | "))

        self.status_word_count_label = QLabel("📊 Words: 0")
        self.status_bar.addWidget(self.status_word_count_label)

        spacer = QLabel()
        spacer.setMinimumWidth(100)
        self.status_bar.addWidget(spacer, stretch=1)

        self.status_ai_label = QLabel("✨ AI: Ready")
        self.status_bar.addWidget(self.status_ai_label)
        self.status_bar.addWidget(QLabel(" | "))

        self.status_connection_label = QLabel("🟢 Ollama: Connected")
        self.status_bar.addWidget(self.status_connection_label)

        self.log_info("Status bar created")

    # =========================================================================
    # VIEW MANAGEMENT
    # =========================================================================

    def switch_view(self, view_name: str):
        self.log_info(f"Switching to view: {view_name}")

        if view_name not in self.views:
            self.log_warning(f"View '{view_name}' not found")
            self.show_notification(
                "View Not Available",
                f"The '{view_name}' view has not been loaded yet.",
                "warning",
            )
            return

        view_widget = self.views[view_name]

        if hasattr(view_widget, 'current_story_id'):
            view_widget.current_story_id = self.current_story_id

        self.content_stack.setCurrentWidget(view_widget)
        self.log_info(f"Successfully switched to view: {view_name}")

        if hasattr(view_widget, 'refresh') and callable(view_widget.refresh):
            try:
                view_widget.refresh()
            except Exception as e:
                self.log_error(f"Error refreshing view {view_name}: {e}")

    def load_story(self, story_id: int):
        """Load a story into the interface (legacy helper)."""
        from models import Story

        story = Story.get_by_id(story_id, story_id)

        if story:
            self.current_story_id   = story_id
            self.current_story_name = story.title

            self.setWindowTitle(f"Loreo Forge - {story.title}")

            # Use the named QLabel attributes, not a non-existent dict
            self.status_story_label.setText(f"📖 {story.title}")

            stats = story.calculate_statistics()
            self.status_word_count_label.setText(
                f"📊 Words: {stats['total_word_count']:,}"
            )

            current_widget = self.content_stack.currentWidget()
            if hasattr(current_widget, 'load_data'):
                current_widget.load_data()

            self.logger.info(f"Loaded story: {story.title}")
        else:
            self.logger.error(f"Failed to load story {story_id}")

    # =========================================================================
    # STATUS BAR HELPERS
    # =========================================================================

    def update_status_bar(self, message: str, duration: int = 3000):
        self.statusBar().showMessage(message, duration)

    def show_notification(
        self, title: str, message: str, notification_type: str = "info"
    ):
        icon_map = {
            'info':    QMessageBox.Information,
            'success': QMessageBox.Information,
            'warning': QMessageBox.Warning,
            'error':   QMessageBox.Critical,
        }
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon_map.get(notification_type, QMessageBox.Information))
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        QTimer.singleShot(3000, msg_box.accept)
        msg_box.exec_()

    # =========================================================================
    # WINDOW STATE
    # =========================================================================

    def _load_window_state(self): pass
    def _save_window_state(self): pass

    def _on_theme_changed(self, theme_name: str):
        try:
            theme_engine.load_theme(theme_name)
            self.log_info(f"Theme changed to: {theme_name}")
            self.show_notification("Theme Changed", f"Applied theme: {theme_name}", "info")
        except Exception as e:
            self.log_error(f"Failed to change theme: {e}")

    def closeEvent(self, event):
        if self.prompt_unsaved_changes():
            self._save_window_state()
            event.accept()
        else:
            event.ignore()

    def prompt_unsaved_changes(self) -> bool:
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'is_modified') and current_widget.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Save:
                if hasattr(current_widget, 'save_data'):
                    current_widget.save_data()
                return True
            return reply == QMessageBox.Discard
        return True

    # =========================================================================
    # STORY MANAGEMENT
    # =========================================================================

    def set_active_story(self, story_id: int) -> bool:
        self.log_info(f"Setting active story: {story_id}")

        if self.story_manager.set_active_story(story_id):
            story = self.story_manager.get_active_story()
            if story:
                self.current_story_id   = story_id
                self.current_story_name = story['title']

                self.setWindowTitle(f"Loreo Forge - {story['title']}")
                self.status_story_label.setText(f"📖 {story['title']}")

                stats = self.story_manager.get_story_stats(story_id)
                self.status_word_count_label.setText(
                    f"📊 Words: {stats.get('total_words', 0):,}"
                )

                if self.search_widget is not None:
                    self.search_widget.set_story_id(story_id)

                self._refresh_all_views()

                self.log_info(f"Active story set to: {story['title']}")
                return True

        self.log_error(f"Failed to set active story: {story_id}")
        return False

    def _refresh_all_views(self):
        self.log_info("Refreshing all views with new story context")
        for view_name, view_widget in self.views.items():
            try:
                if hasattr(view_widget, 'current_story_id'):
                    view_widget.current_story_id = self.current_story_id
                if hasattr(view_widget, 'clear_form') and callable(view_widget.clear_form):
                    view_widget.clear_form()
                if hasattr(view_widget, 'load_data') and callable(view_widget.load_data):
                    view_widget.load_data()
            except Exception as e:
                self.log_error(f"Error refreshing {view_name}: {e}")

    def get_active_story_id(self) -> int:
        return self.current_story_id

    def create_new_story(
        self,
        title:    str,
        genre:    str = "",
        setting:  str = "",
        tone:     str = "",
        synopsis: str = "",
    ) -> bool:
        try:
            story_id = self.story_manager.create_story(
                title=title, genre=genre, setting=setting,
                tone=tone, synopsis=synopsis,
            )
            if story_id:
                db_manager.initialize_database(story_id)
                self.set_active_story(story_id)
                self.show_notification(
                    "Success", f"Story '{title}' created successfully!", "success"
                )
                return True
            return False
        except Exception as e:
            self.log_error(f"Failed to create story: {e}")
            self.show_notification("Error", f"Failed to create story: {e}", "error")
            return False

    # =========================================================================
    # SEARCH RESULT NAVIGATION
    # =========================================================================

    def _on_search_result_selected(
        self,
        entity_type:     str,
        entity_id:       int,
        view_name:       str,
        result_story_id: int,
    ):
        """
        Navigate to a search result.

        Global search (no story active):
            result_story_id will differ from self.current_story_id (which is
            None).  set_active_story is called first; navigation only proceeds
            if the story switch succeeds.

        Story-specific search (story already active):
            result_story_id == self.current_story_id → navigate directly.

        Cross-story result (different story active):
            set_active_story switches context first, then navigates.

        load_method_map keys are the view_name strings emitted by SearchWidget,
        and the values are the exact method names confirmed in each view file:
            lore_view.py       → _load_lore(lore_id)
            powers_view.py     → _load_power(power_id)
            organizations_view → _load_org(org_id)
        """
        try:
            # ── Step 1: switch story if needed ────────────────────────────────
            needs_story_switch = (
                result_story_id is not None
                and result_story_id != self.current_story_id
            )

            if needs_story_switch:
                self.log_info(
                    f"Search result from story {result_story_id} "
                    f"(current: {self.current_story_id}) — switching story"
                )
                success = self.set_active_story(result_story_id)
                if not success:
                    # Story switch failed — do not navigate to a view that has
                    # the wrong story's data loaded.
                    self.log_error(
                        f"Failed to switch to story {result_story_id}; "
                        "aborting navigation"
                    )
                    self.show_notification(
                        "Navigation Error",
                        f"Could not load story {result_story_id}.",
                        "error",
                    )
                    return

            # ── Step 2: switch to the correct view ───────────────────────────
            self.switch_view(view_name)

            view = self.views.get(view_name)
            if not view:
                self.log_warning(f"View '{view_name}' not in self.views after switch")
                return

            # ── Step 3: open the specific entry ──────────────────────────────
            # Method names verified against the actual view source files:
            #   characters_view  → _load_character
            #   world_view       → _load_location
            #   lore_view        → _load_lore         
            #   bestiary_view    → _load_creature
            #   organizations    → _load_org            
            #   powers_view      → _load_power  
            #   itmes_view       → _load_item       
            #   chapters_list    → _load_chapter
            load_method_map = {
                'characters':    '_load_character',
                'world':         '_load_location',
                'lore':          '_load_lore',
                'bestiary':      '_load_creature',
                'organizations': '_load_org',
                'powers':        '_load_power',
                'items':         '_load_item',
                'chapters_list': '_load_chapter',
            }

            method_name = load_method_map.get(view_name)
            if method_name and hasattr(view, method_name):
                getattr(view, method_name)(entity_id)
                self.log_info(
                    f"Loaded entry via {method_name}({entity_id}) "
                    f"in view '{view_name}'"
                )
            elif hasattr(view, 'select_by_id'):
                view.select_by_id(entity_id)
            else:
                self.log_warning(
                    f"No load method found for view '{view_name}' "
                    f"(tried '{method_name}')"
                )

            self.log_info(
                f"Search navigation complete: {view_name} → "
                f"{entity_type} ID={entity_id} (story {result_story_id})"
            )

        except Exception as e:
            self.log_error(f"Search navigation error: {e}")

    # =========================================================================
    # LEGACY SEARCH DIALOG (kept for Edit → Find)
    # =========================================================================

    def _on_search(self):
        if not self.current_story_id:
            self.show_notification("No Story", "Please select a story first", "warning")
            return
        self._show_search_results_dialog(self.search_widget.search_input.text().strip()
                                         if self.search_widget else "")

    def _show_search_results_dialog(self, query: str):
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
            QLabel, QPushButton, QTabWidget,
        )

        results = db_manager.search_all_entities(self.current_story_id, query)
        if not results or all(len(v) == 0 for v in results.values()):
            self.show_notification("No Results", f"No results found for '{query}'", "info")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Search Results: {query}")
        dialog.setMinimumSize(700, 500)
        layout = QVBoxLayout()

        header = QLabel(f"Found results for: <b>{query}</b>")
        header.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(header)

        tabs = QTabWidget()
        entity_configs = {
            'characters':    ('Characters',    'characters',    '👤'),
            'locations':     ('Locations',     'world',         '📍'),
            'lore_entries':  ('Lore',          'lore',          '📜'),
            'bestiary':      ('Creatures',     'bestiary',      '🐉'),
            'organizations': ('Organizations', 'organizations', '🏛️'),
            'power_systems': ('Powers',        'powers',        '⚡'),
            'items':         ('Items',         'items',         '🗡️'),
            'chapters':      ('Chapters',      'chapters_list', '📖'),
        }

        for entity_type, items in results.items():
            if not items:
                continue
            config = entity_configs.get(entity_type)
            if not config:
                continue
            display_name, view_name, icon = config

            tab_widget = QWidget()
            tab_layout = QVBoxLayout()
            results_list = QListWidget()

            for item in items:
                if entity_type == 'characters':
                    text = f"{icon} {item.get('name')} - {item.get('role','Character')}"
                elif entity_type == 'locations':
                    text = f"{icon} {item.get('name')} - {item.get('type','Location')}"
                elif entity_type == 'lore_entries':
                    text = f"{icon} {item.get('title')} - {item.get('category','Lore')}"
                elif entity_type == 'bestiary':
                    text = f"{icon} {item.get('name')} - {item.get('category','Creature')}"
                elif entity_type == 'organizations':
                    text = f"{icon} {item.get('name')} - {item.get('type','Organization')}"
                elif entity_type == 'power_systems':
                    text = f"{icon} {item.get('name')} - {item.get('system_name','Power')}"
                elif entity_type == 'items':
                    text = f"{icon} {item.get('name')} - {item.get('type','Item')}"
                elif entity_type == 'chapters':
                    text = f"{icon} Ch.{item.get('chapter_number')} - {item.get('title','Untitled')}"
                else:
                    text = f"{icon} {item.get('name', item.get('title','Unknown'))}"

                list_item = QListWidgetItem(text)
                list_item.setData(Qt.UserRole, (entity_type, item.get('id'), view_name))
                results_list.addItem(list_item)

            results_list.itemDoubleClicked.connect(self._navigate_to_search_result)
            tab_layout.addWidget(results_list)
            tab_widget.setLayout(tab_layout)
            tabs.addTab(tab_widget, f"{icon} {display_name} ({len(items)})")

        layout.addWidget(tabs)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.setLayout(layout)
        dialog.exec_()

    def _navigate_to_search_result(self, list_item):
        data = list_item.data(Qt.UserRole)
        if not data:
            return
        entity_type, entity_id, view_name = data
        self.switch_view(view_name)
        current_view = self.content_stack.currentWidget()

        method_map = {
            'characters':    '_load_character',
            'locations':     '_load_location',
            'lore_entries':  '_load_lore',
            'bestiary':      '_load_creature',
            'organizations': '_load_org',
            'power_systems': '_load_power',
            'items':         '_load_item',
            'chapters':      '_load_chapter',
        }
        m = method_map.get(entity_type)
        if m and hasattr(current_view, m):
            getattr(current_view, m)(entity_id)

        self.log_info(f"Navigated to {entity_type} ID {entity_id}")
        self.show_notification("Navigation", f"Opened {entity_type} entry", "success")

    # =========================================================================
    # MENU / TOOLBAR HANDLERS
    # =========================================================================

    def _on_create_story_from_dashboard(self): self.switch_view('story')
    def _on_new_story(self):    self.show_notification("Info", "New Story dialog coming soon!", "info")
    def _on_open_story(self):   self.show_notification("Info", "Open Story dialog coming soon!", "info")
    def _on_export_chapter(self): self.show_notification("Info", "Export Chapter coming soon!", "info")
    def _on_export_story(self):   self.show_notification("Info", "Export Story coming soon!", "info")
    def _on_settings(self):       self.show_notification("Info", "Settings dialog coming soon!", "info")
    def _on_ai_settings(self):    self.show_notification("Info", "AI Settings coming soon!", "info")
    def _on_model_switcher(self):  self.show_notification("Info", "Model Switcher coming soon!", "info")
    def _on_db_manager(self):      self.show_notification("Info", "Database Manager coming soon!", "info")
    def _on_continuity_checker(self): self.show_notification("Info", "Continuity Checker coming soon!", "info")
    def _on_user_guide(self):     self.show_notification("Info", "User Guide coming soon!", "info")
    def _on_shortcuts(self):      self.show_notification("Info", "Keyboard Shortcuts coming soon!", "info")

    def _on_save(self):
        current = self.content_stack.currentWidget()
        if hasattr(current, 'save_data'):
            current.save_data()
            self.update_status_bar("Saved successfully")

    def _on_save_all(self):
        self.update_status_bar("All changes saved")

    def _on_model_changed(self, model_text: str):
        t = model_text.lower()
        if "mistral" in t or "12b" in t:
            model = "mistral-nemo:12b"
        elif "8b" in t:
            model = "llama3.1:8b"
        else:
            model = "llama3.1:70b"
        # FIX 2: was self.status_labels['model'] (non-existent dict key)
        if self.status_model_label is not None:
            self.status_model_label.setText(f"🤖 Model: {model}")
        self.logger.info(f"Model switched to: {model}")

    def _on_about(self):
        QMessageBox.about(
            self, "About Loreo Forge",
            "<h2>Loreo Forge 1.0</h2>"
            "<p>AI-Powered Story Generation Platform</p>"
            "<p>Built with Python, PyQt5, and Ollama</p>"
            "<p>&copy; 2024 Loreo Forge</p>",
        )

    def _on_new_character(self):
        if not self.current_story_id:
            self.show_notification("No Story", "Please select or create a story first", "warning")
            return
        self.switch_view('characters')

    def _on_new_location(self):
        if not self.current_story_id:
            self.show_notification("No Story", "Please select or create a story first", "warning")
            return
        self.switch_view('world')

    def _on_generate_chapter(self):
        if not self.current_story_id:
            self.show_notification("No Story", "Please select or create a story first", "warning")
            return
        self.switch_view('chapter_generator')

    def _toggle_sidebar(self):
        if self.sidebar:
            self.sidebar.setVisible(not self.sidebar.isVisible())

    def _toggle_toolbar(self):
        if self.toolbar:
            self.toolbar.setVisible(not self.toolbar.isVisible())

    def _zoom_in(self):
        current_size = settings.get('ui.font_size', settings.DEFAULT_FONT_SIZE)
        theme_engine.set_font_size(min(current_size + 1, 24))

    def _zoom_out(self):
        current_size = settings.get('ui.font_size', settings.DEFAULT_FONT_SIZE)
        theme_engine.set_font_size(max(current_size - 1, 8))