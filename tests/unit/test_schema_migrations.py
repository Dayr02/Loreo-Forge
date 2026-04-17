import sqlite3

from database.migrations import db_migrator
from database.schema import DatabaseSchema


def test_story_migration_adds_phase1_columns(isolated_paths):
    db_path = isolated_paths / "data" / "stories" / "story_1.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

    changed = db_migrator.migrate_story_database(1)
    assert changed is True

    conn = sqlite3.connect(str(db_path))
    columns = {row[1] for row in conn.execute("PRAGMA table_info(characters)").fetchall()}
    version = DatabaseSchema().get_schema_version(conn)
    conn.close()

    assert {"unique_key", "generation_rules", "card_data", "ascension_level"}.issubset(columns)
    assert version == DatabaseSchema.SCHEMA_VERSION
