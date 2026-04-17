"""Database migrations for Loreo Forge V2.0."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List

from config.settings import settings
from database.schema import DatabaseSchema, ENTITY_TABLES, MASTER_SCHEMA, STORY_SCHEMA
from utils.logger import LoggerMixin


PHASE_1_ENTITY_COLUMNS = {
    "unique_key": "TEXT",
    "generation_rules": "TEXT",
    "card_data": "TEXT",
    "ascension_level": "INTEGER DEFAULT 0",
}


class DatabaseMigrator(LoggerMixin):
    """Migrates existing databases to the current schema version."""

    TARGET_VERSION = DatabaseSchema.SCHEMA_VERSION

    def check_and_migrate_all_stories(self) -> dict:
        results = {"total": 0, "migrated": 0, "skipped": 0, "errors": []}
        stories_dir: Path = settings.STORIES_DIR
        if not stories_dir.exists():
            self.log_warning("Stories directory not found, skipping migration.")
            return results

        db_files = sorted(stories_dir.glob("story_*.db"))
        results["total"] = len(db_files)

        for db_file in db_files:
            try:
                changed = self._migrate_single_db(db_file)
                if changed:
                    results["migrated"] += 1
                else:
                    results["skipped"] += 1
            except Exception as exc:
                message = f"{db_file.name}: {exc}"
                self.log_error(message)
                results["errors"].append(message)
        return results

    def migrate_story_database(self, story_id: int) -> bool:
        db_path = settings.get_story_db_path(story_id)
        if not db_path.exists():
            self.log_warning(f"DB not found for story {story_id}")
            return False
        return self._migrate_single_db(db_path)

    def migrate_master_database(self) -> bool:
        db_path = settings.get_master_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        try:
            changed = self._ensure_schema(conn, MASTER_SCHEMA, schema_type="master")
            self._seed_master_records(conn)
            return changed
        finally:
            conn.close()

    def _migrate_single_db(self, db_path: Path) -> bool:
        conn = sqlite3.connect(str(db_path))
        try:
            conn.row_factory = sqlite3.Row
            return self._ensure_schema(conn, STORY_SCHEMA, schema_type="story")
        finally:
            conn.close()

    def _ensure_schema(
        self,
        conn: sqlite3.Connection,
        schema_definitions: Dict[str, str],
        schema_type: str,
    ) -> bool:
        cursor = conn.cursor()
        changed = False
        existing_tables = self._get_existing_tables(cursor)

        for object_name, create_sql in schema_definitions.items():
            cursor.execute(create_sql)
            if "CREATE TABLE" in create_sql and object_name not in existing_tables:
                changed = True

        if schema_type == "story":
            for table_name in ENTITY_TABLES:
                if table_name not in self._get_existing_tables(cursor):
                    continue
                existing_columns = self._get_existing_columns(cursor, table_name)
                for column_name, column_sql in PHASE_1_ENTITY_COLUMNS.items():
                    if column_name not in existing_columns:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
                        )
                        changed = True

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("SELECT MAX(version) FROM schema_version")
        current_version = int(cursor.fetchone()[0] or 0)
        if current_version != self.TARGET_VERSION:
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (self.TARGET_VERSION,),
            )
            changed = True

        conn.commit()
        return changed

    @staticmethod
    def _get_existing_tables(cursor: sqlite3.Cursor) -> set:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {row[0] for row in cursor.fetchall()}

    @staticmethod
    def _get_existing_columns(cursor: sqlite3.Cursor, table_name: str) -> set:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}

    def _seed_master_records(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM player_profile")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO player_profile (username) VALUES ('Player')")
        cursor.execute("SELECT COUNT(*) FROM achievements_definitions")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO achievements_definitions (achievement_key, title, description)
                VALUES
                ('first_story', 'First Story', 'Create your first story.'),
                ('first_session', 'First Session', 'Complete your first game session.')
                """
            )
        cursor.execute("SELECT COUNT(*) FROM quests")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO quests (quest_key, title, description, cadence)
                VALUES
                ('daily_write', 'Daily Writing', 'Write or generate new story content today.', 'daily'),
                ('weekly_worldbuild', 'Weekly Worldbuilding', 'Expand your lore this week.', 'weekly')
                """
            )
        conn.commit()

    def get_table_list(self, story_id: int) -> List[str]:
        db_path = settings.get_story_db_path(story_id)
        if not db_path.exists():
            return []
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()
            return sorted(self._get_existing_tables(cursor))
        finally:
            conn.close()


db_migrator = DatabaseMigrator()
