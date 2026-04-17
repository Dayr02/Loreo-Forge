"""Database schema definitions for Loreo Forge V2.0."""

from __future__ import annotations

import sqlite3

from utils.logger import LoggerMixin


ENTITY_TABLES = (
    "characters",
    "locations",
    "bestiary",
    "lore_entries",
    "organizations",
    "items",
    "power_systems",
    "arcs",
    "chapters",
    "chapter_parts",
)

ENTITY_METADATA_COLUMNS = """
            unique_key TEXT,
            generation_rules TEXT,
            card_data TEXT,
            ascension_level INTEGER DEFAULT 0,
"""


class DatabaseSchema(LoggerMixin):
    """Handles schema creation for master and story databases."""

    SCHEMA_VERSION = 2

    def create_master_schema(self, conn: sqlite3.Connection) -> bool:
        try:
            cursor = conn.cursor()
            for create_sql in MASTER_SCHEMA.values():
                cursor.execute(create_sql)
            self._write_schema_version(cursor)
            conn.commit()
            return True
        except sqlite3.Error as exc:
            self.log_error(f"Master schema creation failed: {exc}")
            conn.rollback()
            return False

    def create_story_schema(self, conn: sqlite3.Connection) -> bool:
        try:
            cursor = conn.cursor()
            for create_sql in STORY_SCHEMA.values():
                cursor.execute(create_sql)
            self._write_schema_version(cursor)
            conn.commit()
            return True
        except sqlite3.Error as exc:
            self.log_error(f"Story schema creation failed: {exc}")
            conn.rollback()
            return False

    def verify_schema(self, conn: sqlite3.Connection, schema_type: str = "story") -> bool:
        expected = MASTER_SCHEMA if schema_type == "master" else STORY_SCHEMA
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {row[0] for row in cursor.fetchall()}
        required = {name for name, sql in expected.items() if "CREATE TABLE" in sql}
        return required.issubset(existing)

    def get_schema_version(self, conn: sqlite3.Connection) -> int:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        if not cursor.fetchone():
            return 0
        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return int(result[0] or 0)

    def _write_schema_version(self, cursor: sqlite3.Cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (self.SCHEMA_VERSION,),
        )


MASTER_SCHEMA = {
    "stories": """
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            genre TEXT,
            setting TEXT,
            tone TEXT,
            target_audience TEXT,
            synopsis TEXT,
            notes TEXT,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "stories_idx": "CREATE INDEX IF NOT EXISTS idx_stories_active ON stories(is_active)",
    "player_profile": """
        CREATE TABLE IF NOT EXISTS player_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL DEFAULT 'Player',
            level INTEGER NOT NULL DEFAULT 1,
            xp INTEGER NOT NULL DEFAULT 0,
            ink_currency INTEGER NOT NULL DEFAULT 0,
            lifetime_statistics TEXT,
            streak_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "achievements_definitions": """
        CREATE TABLE IF NOT EXISTS achievements_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_key TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            reward_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "player_achievements": """
        CREATE TABLE IF NOT EXISTS player_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_profile_id INTEGER NOT NULL,
            achievement_definition_id INTEGER NOT NULL,
            progress REAL DEFAULT 0,
            unlocked_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "quests": """
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quest_key TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            cadence TEXT DEFAULT 'daily',
            reward_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "player_quests": """
        CREATE TABLE IF NOT EXISTS player_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_profile_id INTEGER NOT NULL,
            quest_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            progress REAL DEFAULT 0,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "templates": """
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            template_type TEXT NOT NULL,
            content TEXT NOT NULL,
            is_system BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}


STORY_SCHEMA = {
    "characters": f"""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
{ENTITY_METADATA_COLUMNS}
            role TEXT,
            age INTEGER,
            status TEXT,
            first_appearance INTEGER,
            appearance TEXT,
            personality TEXT,
            goals TEXT,
            fears TEXT,
            voice_pattern TEXT,
            background TEXT,
            arc_notes TEXT,
            abilities TEXT,
            linked_power_system INTEGER,
            importance_weight REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, name)
        )
    """,
    "characters_idx": "CREATE INDEX IF NOT EXISTS idx_characters_story ON characters(story_id)",
    "locations": f"""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
{ENTITY_METADATA_COLUMNS}
            type TEXT,
            parent_location INTEGER,
            description TEXT,
            atmosphere TEXT,
            special_features TEXT,
            history TEXT,
            inhabitants TEXT,
            cultural_notes TEXT,
            map_x REAL,
            map_y REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, name)
        )
    """,
    "locations_idx": "CREATE INDEX IF NOT EXISTS idx_locations_story ON locations(story_id)",
    "bestiary": f"""
        CREATE TABLE IF NOT EXISTS bestiary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
{ENTITY_METADATA_COLUMNS}
            category TEXT NOT NULL,
            type TEXT,
            threat_level TEXT,
            rarity TEXT,
            size TEXT,
            habitat TEXT,
            lifespan TEXT,
            appearance TEXT,
            behavior TEXT,
            abilities TEXT,
            weaknesses TEXT,
            lore TEXT,
            is_sentient BOOLEAN DEFAULT 0,
            is_magical BOOLEAN DEFAULT 0,
            is_hostile BOOLEAN DEFAULT 0,
            first_appearance_chapter INTEGER,
            appearances_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, name)
        )
    """,
    "bestiary_idx": "CREATE INDEX IF NOT EXISTS idx_bestiary_story ON bestiary(story_id)",
    "lore_entries": f"""
        CREATE TABLE IF NOT EXISTS lore_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            title TEXT NOT NULL,
{ENTITY_METADATA_COLUMNS}
            category TEXT,
            content TEXT,
            importance INTEGER DEFAULT 5,
            is_secret BOOLEAN DEFAULT 0,
            is_revelation BOOLEAN DEFAULT 0,
            related_chapters TEXT,
            tags TEXT,
            related_characters TEXT,
            related_locations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, title)
        )
    """,
    "lore_entries_idx": "CREATE INDEX IF NOT EXISTS idx_lore_story ON lore_entries(story_id)",
    "organizations": f"""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
{ENTITY_METADATA_COLUMNS}
            type TEXT,
            member_count INTEGER,
            description TEXT,
            history TEXT,
            goals TEXT,
            structure TEXT,
            leadership TEXT,
            members TEXT,
            territory TEXT,
            resources TEXT,
            allies TEXT,
            rivals TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, name)
        )
    """,
    "organizations_idx": "CREATE INDEX IF NOT EXISTS idx_organizations_story ON organizations(story_id)",
    "items": f"""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
{ENTITY_METADATA_COLUMNS}
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
    """,
    "items_idx": "CREATE INDEX IF NOT EXISTS idx_items_story ON items(story_id)",
    "power_systems": f"""
        CREATE TABLE IF NOT EXISTS power_systems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
{ENTITY_METADATA_COLUMNS}
            system_name TEXT,
            description TEXT,
            rules TEXT,
            limitations TEXT,
            progression_system TEXT,
            rare_abilities TEXT,
            cost_system TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, name)
        )
    """,
    "power_systems_idx": "CREATE INDEX IF NOT EXISTS idx_power_systems_story ON power_systems(story_id)",
    "arcs": f"""
        CREATE TABLE IF NOT EXISTS arcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
{ENTITY_METADATA_COLUMNS}
            arc_number INTEGER NOT NULL,
            title TEXT,
            description TEXT,
            themes TEXT,
            status TEXT DEFAULT 'planned',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, arc_number)
        )
    """,
    "arcs_idx": "CREATE INDEX IF NOT EXISTS idx_arcs_story ON arcs(story_id)",
    "chapters": f"""
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
{ENTITY_METADATA_COLUMNS}
            chapter_number INTEGER NOT NULL,
            title TEXT,
            arc TEXT,
            arc_id INTEGER,
            pov_character TEXT,
            pov_character_id INTEGER,
            content TEXT,
            summary TEXT,
            plot_points TEXT,
            mood TEXT,
            notes TEXT,
            word_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            model_used TEXT,
            edited BOOLEAN DEFAULT 0,
            generation_metadata TEXT,
            approved_sections TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, chapter_number)
        )
    """,
    "chapters_idx": "CREATE INDEX IF NOT EXISTS idx_chapters_story ON chapters(story_id, chapter_number)",
    "chapter_parts": f"""
        CREATE TABLE IF NOT EXISTS chapter_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
{ENTITY_METADATA_COLUMNS}
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
    """,
    "chapter_parts_idx": "CREATE INDEX IF NOT EXISTS idx_chapter_parts_story ON chapter_parts(story_id, chapter_number)",
    "chapter_parts_merged_idx": "CREATE INDEX IF NOT EXISTS idx_chapter_parts_merged ON chapter_parts(story_id, is_merged)",
    "timeline_states": """
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
    """,
    "timeline_states_idx": "CREATE INDEX IF NOT EXISTS idx_timeline_states_story ON timeline_states(story_id, chapter_number)",
    "chapter_versions": """
        CREATE TABLE IF NOT EXISTS chapter_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            chapter_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            content TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(chapter_id, version_number)
        )
    """,
    "chapter_versions_idx": "CREATE INDEX IF NOT EXISTS idx_chapter_versions_story ON chapter_versions(story_id)",
    "generation_history": """
        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            chapter_id INTEGER,
            settings_json TEXT,
            output_text TEXT,
            model_used TEXT,
            prompt TEXT,
            context_used TEXT,
            tokens_consumed INTEGER,
            generation_time REAL,
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "generation_history_idx": "CREATE INDEX IF NOT EXISTS idx_generation_history_story ON generation_history(story_id)",
    "generation_preferences": """
        CREATE TABLE IF NOT EXISTS generation_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL UNIQUE,
            preferences_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "game_sessions": """
        CREATE TABLE IF NOT EXISTS game_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            mode_name TEXT NOT NULL,
            session_state TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "reader_books": """
        CREATE TABLE IF NOT EXISTS reader_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            book_type TEXT DEFAULT 'encyclopedia',
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}
