"""
Database Migrations for Loreo Forge
Adds chapter_parts, timeline_states, and items (and any other missing tables) to existing story databases.
Called automatically from main.py on startup.
"""

import sqlite3
from pathlib import Path
from typing import List
from config.settings import settings
from utils.logger import LoggerMixin


class DatabaseMigrator(LoggerMixin):
    """Migrates existing story databases to the current schema."""

    # Each entry: (table_name, CREATE SQL)
    REQUIRED_TABLES = [
        (
            'chapter_parts',
            """
            CREATE TABLE IF NOT EXISTS chapter_parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                chapter_number INTEGER NOT NULL,
                part_number INTEGER NOT NULL,
                title TEXT,
                content TEXT,
                word_count INTEGER DEFAULT 0,
                context_summary TEXT,
                story_progression_notes TEXT,
                generation_metadata TEXT,
                is_merged BOOLEAN DEFAULT 0,
                merged_into_chapter_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(story_id, chapter_number, part_number)
            )
            """
        ),
        (
            'timeline_states',
            """
            CREATE TABLE IF NOT EXISTS timeline_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                chapter_number INTEGER NOT NULL,
                story_time TEXT,
                character_states TEXT,
                active_conflicts TEXT,
                plot_threads TEXT,
                unresolved_events TEXT,
                world_changes TEXT,
                cause_effect_chains TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(story_id, chapter_number)
            )
            """
        ),
        (
            'items',
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                category TEXT,
                rarity TEXT,
                description TEXT,
                properties TEXT,
                powers TEXT,
                materials TEXT,
                creator TEXT,
                history TEXT,
                current_owner TEXT,
                current_location TEXT,
                value TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(story_id, name)
            )
            """
        ),
    ]

    REQUIRED_INDICES = [
        ('idx_chapter_parts_story',
         "CREATE INDEX IF NOT EXISTS idx_chapter_parts_story ON chapter_parts(story_id, chapter_number)"),
        ('idx_chapter_parts_merged',
         "CREATE INDEX IF NOT EXISTS idx_chapter_parts_merged ON chapter_parts(story_id, is_merged)"),
        ('idx_timeline_states_story',
         "CREATE INDEX IF NOT EXISTS idx_timeline_states_story ON timeline_states(story_id, chapter_number)"),
        ('idx_items_story',
         "CREATE INDEX IF NOT EXISTS idx_items_story ON items(story_id)"),
    ]

    def check_and_migrate_all_stories(self) -> dict:
        """
        Check every story_N.db file and apply missing tables.
        Returns a summary dict.
        """
        results = {'total': 0, 'migrated': 0, 'skipped': 0, 'errors': []}

        stories_dir: Path = settings.STORIES_DIR
        if not stories_dir.exists():
            self.log_warning("Stories directory not found — skipping migration.")
            return results

        db_files = sorted(stories_dir.glob("story_*.db"))
        results['total'] = len(db_files)

        for db_file in db_files:
            try:
                changed = self._migrate_single_db(db_file)
                if changed:
                    results['migrated'] += 1
                else:
                    results['skipped'] += 1
            except Exception as e:
                msg = f"{db_file.name}: {e}"
                self.log_error(f"Migration error — {msg}")
                results['errors'].append(msg)

        self.log_info(
            f"Migration done: {results['migrated']} updated, "
            f"{results['skipped']} already current, "
            f"{len(results['errors'])} errors."
        )
        return results

    def migrate_story_database(self, story_id: int) -> bool:
        """Migrate a single story by ID. Returns True if any change was made."""
        db_path = settings.get_story_db_path(story_id)
        if not db_path.exists():
            self.log_warning(f"DB not found for story {story_id}")
            return False
        return self._migrate_single_db(db_path)

    # ── internals ─────────────────────────────────────────────────────────────

    def _migrate_single_db(self, db_path: Path) -> bool:
        """Apply any missing tables/indices to a single .db file. Returns True if changed."""
        changed = False
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            existing = self._get_existing_tables(cursor)

            for table_name, create_sql in self.REQUIRED_TABLES:
                if table_name not in existing:
                    self.log_info(f"Adding '{table_name}' to {db_path.name}")
                    cursor.execute(create_sql)
                    changed = True

            # indices (idempotent CREATE INDEX IF NOT EXISTS)
            for _idx_name, idx_sql in self.REQUIRED_INDICES:
                try:
                    cursor.execute(idx_sql)
                except sqlite3.Error:
                    pass   # index may already exist under a different name

            if changed:
                conn.commit()

            conn.close()
            return changed

        except sqlite3.Error as e:
            raise RuntimeError(f"SQLite error migrating {db_path.name}: {e}") from e

    @staticmethod
    def _get_existing_tables(cursor: sqlite3.Cursor) -> set:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {row[0] for row in cursor.fetchall()}

    def get_table_list(self, story_id: int) -> List[str]:
        db_path = settings.get_story_db_path(story_id)
        if not db_path.exists():
            return []
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            tables = list(self._get_existing_tables(cursor))
            conn.close()
            return sorted(tables)
        except sqlite3.Error as e:
            self.log_error(f"Error listing tables for story {story_id}: {e}")
            return []


# Global instance
db_migrator = DatabaseMigrator()