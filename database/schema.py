"""
Database Schema for Loreo Forge
"""

import sqlite3
from typing import Optional
from utils.logger import LoggerMixin


class DatabaseSchema(LoggerMixin):
    """
    Database schema manager
    Handles schema creation for both master and story databases
    """
    
    SCHEMA_VERSION = 1
    
    def __init__(self):
        """Initialize schema manager"""
        pass
    
    def create_master_schema(self, conn: sqlite3.Connection) -> bool:
        """
        Create MASTER database schema (stories registry only)
        
        Args:
            conn: SQLite connection to MASTER database
            
        Returns:
            True if successful
        """
        try:
            cursor = conn.cursor()
            
            # ONLY the stories table goes in master DB
            cursor.execute(MASTER_SCHEMA['stories'])
            cursor.execute(MASTER_SCHEMA['stories_idx'])
            
            # Schema version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (self.SCHEMA_VERSION,)
            )
            
            conn.commit()
            self.log_info("Master database schema created successfully")
            return True
            
        except sqlite3.Error as e:
            self.log_error(f"Master schema creation failed: {e}")
            conn.rollback()
            return False
    
    def create_story_schema(self, conn: sqlite3.Connection) -> bool:
        """
        Create STORY database schema (all entity tables)
        
        Args:
            conn: SQLite connection to story-specific database
            
        Returns:
            True if successful
        """
        try:
            cursor = conn.cursor()
            
            # Create all story-specific tables
            for table_name, create_sql in STORY_SCHEMA.items():
                try:
                    cursor.execute(create_sql)
                    self.log_debug(f"Created/verified table/index: {table_name}")
                except sqlite3.Error as e:
                    self.log_error(f"Error creating {table_name}: {e}")
                    return False
            
            # Schema version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (self.SCHEMA_VERSION,)
            )
            
            conn.commit()
            self.log_info("Story database schema created successfully")
            return True
            
        except sqlite3.Error as e:
            self.log_error(f"Story schema creation failed: {e}")
            conn.rollback()
            return False


# ============================================================================
# MASTER DATABASE SCHEMA (loreo_master.db)
# ============================================================================

MASTER_SCHEMA = {
    'stories': """
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
    
    'stories_idx': """
        CREATE INDEX IF NOT EXISTS idx_stories_active 
        ON stories(is_active)
    """,
}


# ============================================================================
# STORY DATABASE SCHEMA (story_N.db)
# All entities with story_id for data isolation
# ============================================================================

STORY_SCHEMA = {
    # ========================================
    # CHARACTERS
    # ========================================
    'characters': """
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
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
    
    'characters_idx': """
        CREATE INDEX IF NOT EXISTS idx_characters_story 
        ON characters(story_id)
    """,
    
    # ========================================
    # LOCATIONS
    # ========================================
    'locations': """
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
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
    
    'locations_idx': """
        CREATE INDEX IF NOT EXISTS idx_locations_story 
        ON locations(story_id)
    """,
    
    # ========================================
    # BESTIARY
    # ========================================
    'bestiary': """
        CREATE TABLE IF NOT EXISTS bestiary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
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
    
    'bestiary_idx': """
        CREATE INDEX IF NOT EXISTS idx_bestiary_story 
        ON bestiary(story_id)
    """,
    
    # ========================================
    # LORE ENTRIES
    # ========================================
    'lore_entries': """
        CREATE TABLE IF NOT EXISTS lore_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            title TEXT NOT NULL,
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
    
    'lore_entries_idx': """
        CREATE INDEX IF NOT EXISTS idx_lore_story 
        ON lore_entries(story_id)
    """,
    
        # ========================================
    # ORGANIZATIONS
    # ========================================
    'organizations': """
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
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
    
    'organizations_idx': """
        CREATE INDEX IF NOT EXISTS idx_organizations_story 
        ON organizations(story_id)
    """,

    # ========================================
    # ITEMS (WEAPONS, ARTIFACTS, EQUIPMENT)
    # ========================================
    'items': """
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
    """,
    
    'items_idx': """
        CREATE INDEX IF NOT EXISTS idx_items_story 
        ON items(story_id)
    """,
    
    # ========================================
    # POWER SYSTEMS
    # ========================================
    'power_systems': """
        CREATE TABLE IF NOT EXISTS power_systems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            name TEXT NOT NULL,
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
    
    'power_systems_idx': """
        CREATE INDEX IF NOT EXISTS idx_power_systems_story 
        ON power_systems(story_id)
    """,
    
    # ========================================
    # ARCS
    # ========================================
    'arcs': """
        CREATE TABLE IF NOT EXISTS arcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
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
    
    'arcs_idx': """
        CREATE INDEX IF NOT EXISTS idx_arcs_story 
        ON arcs(story_id)
    """,
    
    # ========================================
    # CHAPTERS (WITH APPROVED_SECTIONS)
    # ========================================
    'chapters': """
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
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
    
    'chapters_idx': """
        CREATE INDEX IF NOT EXISTS idx_chapters_story 
        ON chapters(story_id, chapter_number)
    """,
    
    # ========================================
    # CHAPTER PARTS (for multi-part generation)
    # ========================================
    'chapter_parts': """
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
    """,
    
    'chapter_parts_idx': """
        CREATE INDEX IF NOT EXISTS idx_chapter_parts_story 
        ON chapter_parts(story_id, chapter_number)
    """,
    
    'chapter_parts_merged_idx': """
        CREATE INDEX IF NOT EXISTS idx_chapter_parts_merged 
        ON chapter_parts(story_id, is_merged)
    """,

    # ========================================
    # TIMELINE STATES 
    # ========================================
    'timeline_states': """
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
    
    'timeline_states_idx': """
        CREATE INDEX IF NOT EXISTS idx_timeline_states_story 
        ON timeline_states(story_id, chapter_number)
    """,
    
    # ========================================
    # CHAPTER VERSIONS
    # ========================================
    'chapter_versions': """
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
    
    'chapter_versions_idx': """
        CREATE INDEX IF NOT EXISTS idx_chapter_versions_story 
        ON chapter_versions(story_id)
    """,
    
    # ========================================
    # GENERATION HISTORY
    # ========================================
    'generation_history': """
        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            chapter_id INTEGER,
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
    
    'generation_history_idx': """
        CREATE INDEX IF NOT EXISTS idx_generation_history_story 
        ON generation_history(story_id)
    """,
    
}
