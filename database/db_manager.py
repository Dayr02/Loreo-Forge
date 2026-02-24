"""
Database Manager for Loreo Forge
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime

from config.settings import settings
from database.schema import DatabaseSchema
from utils.logger import LoggerMixin


class DatabaseError(Exception):
    pass

class ConnectionError(DatabaseError):
    pass

class ValidationError(DatabaseError):
    pass

class IntegrityError(DatabaseError):
    pass


class DatabaseManager(LoggerMixin):
    def __init__(self):
        self._connections: Dict[int, sqlite3.Connection] = {}
        self._schema = DatabaseSchema()
        self.log_info("DatabaseManager initialized")

    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================

    def initialize_database(self, story_id: int) -> bool:
        db_path = settings.get_story_db_path(story_id)
        self.log_info(f"Initializing database for story {story_id} at {db_path}")
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_path), timeout=settings.DB_TIMEOUT,
                                   isolation_level=settings.DB_ISOLATION_LEVEL)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            if not self._schema.create_story_schema(conn):
                raise DatabaseError("Failed to create database schema")
            self._connections[story_id] = conn
            self.log_info(f"Database initialized successfully for story {story_id}")
            return True
        except sqlite3.Error as e:
            self.log_error(f"Failed to initialize database for story {story_id}: {e}")
            raise ConnectionError(f"Database initialization failed: {e}")

    def get_connection(self, story_id: int) -> sqlite3.Connection:
        if story_id in self._connections:
            return self._connections[story_id]
        db_path = settings.get_story_db_path(story_id)
        if not db_path.exists():
            raise ConnectionError(f"Database does not exist for story {story_id}")
        try:
            conn = sqlite3.connect(str(db_path), timeout=settings.DB_TIMEOUT,
                                   isolation_level=settings.DB_ISOLATION_LEVEL)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            self._connections[story_id] = conn
            self.log_debug(f"Connection established for story {story_id}")
            return conn
        except sqlite3.Error as e:
            self.log_error(f"Failed to connect to database for story {story_id}: {e}")
            raise ConnectionError(f"Connection failed: {e}")

    def close_connection(self, story_id: int) -> bool:
        if story_id not in self._connections:
            return True
        try:
            self._connections[story_id].close()
            del self._connections[story_id]
            self.log_debug(f"Connection closed for story {story_id}")
            return True
        except sqlite3.Error as e:
            self.log_error(f"Error closing connection for story {story_id}: {e}")
            return False

    def close_all_connections(self):
        story_ids = list(self._connections.keys())
        for story_id in story_ids:
            self.close_connection(story_id)
        self.log_info("All database connections closed")

    @contextmanager
    def transaction(self, story_id: int):
        conn = self.get_connection(story_id)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.log_error(f"Transaction rolled back: {e}")
            raise

    def vacuum_database(self, story_id: int) -> bool:
        try:
            conn = self.get_connection(story_id)
            conn.execute("VACUUM")
            self.log_info(f"Database vacuumed for story {story_id}")
            return True
        except sqlite3.Error as e:
            self.log_error(f"Failed to vacuum database for story {story_id}: {e}")
            return False

    # ========================================================================
    # STORY-SCOPED CRUD OPERATIONS
    # ========================================================================

    def create_entity(self, table: str, story_id: int, data: Dict[str, Any]) -> Optional[int]:
        if not self._is_valid_table(table):
            raise ValidationError(f"Invalid table name: {table}")
        data['story_id'] = story_id
        data = self._serialize_json_fields(table, data)
        if not self.validate_foreign_keys(table, data):
            raise IntegrityError("Foreign key validation failed")
        try:
            with self.transaction(story_id) as cursor:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                cursor.execute(query, tuple(data.values()))
                entity_id = cursor.lastrowid
                self.log_info(f"Created {table} entity (ID: {entity_id}) for story {story_id}")
                return entity_id
        except sqlite3.Error as e:
            self.log_error(f"Failed to create entity in {table}: {e}")
            return None

    def get_entity(self, table: str, entity_id: int, story_id: int) -> Optional[Dict[str, Any]]:
        if not self._is_valid_table(table):
            raise ValidationError(f"Invalid table name: {table}")
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            query = f"SELECT * FROM {table} WHERE id = ? AND story_id = ?"
            cursor.execute(query, (entity_id, story_id))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result = self._deserialize_json_fields(table, result)
                return result
            return None
        except sqlite3.Error as e:
            self.log_error(f"Failed to get entity from {table}: {e}")
            return None

    def get_entities_by_story(self, table: str, story_id: int,
                              order_by: str = "created_at DESC",
                              filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self._is_valid_table(table):
            raise ValidationError(f"Invalid table name: {table}")
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            query = f"SELECT * FROM {table} WHERE story_id = ?"
            params: List[Any] = [story_id]
            if filters:
                for key, value in filters.items():
                    query += f" AND {key} = ?"
                    params.append(value)
            query += f" ORDER BY {order_by}"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            results = [self._deserialize_json_fields(table, r) for r in results]
            return results
        except sqlite3.Error as e:
            self.log_error(f"Failed to get entities from {table}: {e}")
            return []

    def update_entity(self, table: str, entity_id: int, story_id: int,
                      data: Dict[str, Any]) -> bool:
        if not self._is_valid_table(table):
            raise ValidationError(f"Invalid table name: {table}")
        existing = self.get_entity(table, entity_id, story_id)
        if not existing:
            self.log_error(f"Entity {entity_id} not found in {table} for story {story_id}")
            return False
        data.pop('story_id', None)
        data.pop('id', None)
        if not data:
            return True
        data = self._serialize_json_fields(table, data)
        data['updated_at'] = datetime.now().isoformat()
        try:
            with self.transaction(story_id) as cursor:
                set_clauses = ', '.join([f"{key} = ?" for key in data.keys()])
                query = f"UPDATE {table} SET {set_clauses} WHERE id = ? AND story_id = ?"
                params = list(data.values()) + [entity_id, story_id]
                cursor.execute(query, params)
                if cursor.rowcount == 0:
                    self.log_warning(f"No entity found with ID {entity_id} in {table}")
                    return False
                self.log_info(f"Updated {table} entity {entity_id} for story {story_id}")
                return True
        except sqlite3.Error as e:
            self.log_error(f"Failed to update entity in {table}: {e}")
            return False

    def delete_entity(self, table: str, entity_id: int, story_id: int) -> bool:
        if not self._is_valid_table(table):
            raise ValidationError(f"Invalid table name: {table}")
        existing = self.get_entity(table, entity_id, story_id)
        if not existing:
            self.log_error(f"Entity {entity_id} not found in {table} for story {story_id}")
            return False
        try:
            with self.transaction(story_id) as cursor:
                query = f"DELETE FROM {table} WHERE id = ? AND story_id = ?"
                cursor.execute(query, (entity_id, story_id))
                if cursor.rowcount == 0:
                    return False
                self.log_info(f"Deleted {table} entity {entity_id} from story {story_id}")
                return True
        except sqlite3.Error as e:
            self.log_error(f"Failed to delete entity from {table}: {e}")
            return False

    def count_entities(self, table: str, story_id: int) -> int:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM {table} WHERE story_id = ?", (story_id,))
            result = cursor.fetchone()
            return result['count'] if result else 0
        except sqlite3.Error as e:
            self.log_error(f"Failed to count entities in {table}: {e}")
            return 0

    # ========================================================================
    # LEGACY CRUD (backward compatibility)
    # ========================================================================

    def create_record(self, story_id: int, table: str, data: Dict[str, Any]) -> Optional[int]:
        return self.create_entity(table, story_id, data)

    def get_record(self, story_id: int, table: str, record_id: int) -> Optional[Dict[str, Any]]:
        return self.get_entity(table, record_id, story_id)

    def get_all_records(self, story_id: int, table: str, filters=None,
                        sort_by=None, order='ASC', limit=None) -> List[Dict[str, Any]]:
        order_clause = f"{sort_by} {order}" if sort_by else "created_at DESC"
        results = self.get_entities_by_story(table, story_id, order_clause, filters)
        if limit:
            results = results[:limit]
        return results

    def update_record(self, story_id: int, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        return self.update_entity(table, record_id, story_id, data)

    def delete_record(self, story_id: int, table: str, record_id: int) -> bool:
        return self.delete_entity(table, record_id, story_id)

    # ========================================================================
    # SPECIALIZED ENTITY OPERATIONS
    # ========================================================================

    def get_characters(self, story_id: int) -> List[Dict[str, Any]]:
        return self.get_entities_by_story('characters', story_id, 'name ASC')

    def get_locations(self, story_id: int) -> List[Dict[str, Any]]:
        return self.get_entities_by_story('locations', story_id, 'name ASC')

    def get_bestiary(self, story_id: int) -> List[Dict[str, Any]]:
        return self.get_entities_by_story('bestiary', story_id, 'name ASC')

    def get_lore_entries(self, story_id: int) -> List[Dict[str, Any]]:
        return self.get_entities_by_story('lore_entries', story_id, 'title ASC')

    def get_organizations(self, story_id: int) -> List[Dict[str, Any]]:
        return self.get_entities_by_story('organizations', story_id, 'name ASC')

    def get_power_systems(self, story_id: int) -> List[Dict[str, Any]]:
        return self.get_entities_by_story('power_systems', story_id, 'name ASC')

    def get_chapters(self, story_id: int) -> List[Dict[str, Any]]:
        return self.get_entities_by_story('chapters', story_id, 'chapter_number ASC')

    def get_next_chapter_number(self, story_id: int) -> int:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(chapter_number) as max_num FROM chapters WHERE story_id = ?", (story_id,))
            result = cursor.fetchone()
            if result and result['max_num'] is not None:
                return result['max_num'] + 1
            return 1
        except sqlite3.Error as e:
            self.log_error(f"Failed to get next chapter number: {e}")
            return 1

    def get_all_characters(self, story_id: int) -> List[Dict[str, Any]]:
        return self.get_entities_by_story('characters', story_id, 'name ASC')

    # ========================================================================
    # STORY-SPECIFIC QUERIES
    # ========================================================================

    def get_story_metadata(self, story_id: int) -> Optional[Dict[str, Any]]:
        try:
            from database.master_db import master_db
            story_data = master_db.fetch_one("SELECT * FROM stories WHERE id = ?", (story_id,))
            if not story_data:
                return None
            story_dict = dict(story_data)
            story_dict['total_chapters']     = self.count_entities('chapters',     story_id)
            story_dict['total_characters']   = self.count_entities('characters',   story_id)
            story_dict['total_locations']    = self.count_entities('locations',    story_id)
            story_dict['total_bestiary']     = self.count_entities('bestiary',     story_id)
            story_dict['total_lore_entries'] = self.count_entities('lore_entries', story_id)
            story_dict['total_power_systems']= self.count_entities('power_systems',story_id)
            story_dict['total_organizations']= self.count_entities('organizations',story_id)
            story_dict['total_word_count']   = self._get_total_word_count(story_id)
            return story_dict
        except Exception as e:
            self.log_error(f"Failed to get story metadata for story {story_id}: {e}")
            return None

    def get_chapter_by_number(self, story_id: int, chapter_num: int) -> Optional[Dict[str, Any]]:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chapters WHERE story_id = ? AND chapter_number = ?", (story_id, chapter_num))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                return self._deserialize_json_fields('chapters', result)
            return None
        except sqlite3.Error as e:
            self.log_error(f"Failed to get chapter {chapter_num}: {e}")
            return None

    def get_recent_chapters(self, story_id: int, count: int = 3) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chapters WHERE story_id = ? ORDER BY chapter_number DESC LIMIT ?",
                (story_id, count)
            )
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            return [self._deserialize_json_fields('chapters', r) for r in results]
        except sqlite3.Error as e:
            self.log_error(f"Failed to get recent chapters: {e}")
            return []

    def get_chapter_context(self, story_id: int, chapter_num: int) -> Dict[str, Any]:
        context = {'story': None, 'recent_chapters': [], 'characters': [],
                   'locations': [], 'power_systems': [], 'lore': [], 'bestiary': []}
        try:
            context['story']           = self.get_story_metadata(story_id)
            if chapter_num > 1:
                context['recent_chapters'] = self.get_recent_chapters(story_id, 3)
            context['characters']      = self.get_characters(story_id)
            context['locations']       = self.get_locations(story_id)
            context['power_systems']   = self.get_power_systems(story_id)
            context['lore']            = self.get_lore_entries(story_id)
            context['bestiary']        = self.get_bestiary(story_id)
            return context
        except Exception as e:
            self.log_error(f"Failed to build chapter context: {e}")
            return context

    def search_lore(self, story_id: int, keywords: str) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            search_pattern = f"%{keywords}%"
            cursor.execute(
                "SELECT * FROM lore_entries WHERE story_id = ? AND (title LIKE ? OR content LIKE ? OR category LIKE ?) ORDER BY importance DESC",
                (story_id, search_pattern, search_pattern, search_pattern)
            )
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            return [self._deserialize_json_fields('lore_entries', r) for r in results]
        except sqlite3.Error as e:
            self.log_error(f"Failed to search lore: {e}")
            return []

    def get_active_arc(self, story_id: int) -> Optional[Dict[str, Any]]:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM arcs WHERE story_id = ? AND status = 'active' ORDER BY arc_number DESC LIMIT 1",
                (story_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            self.log_error(f"Failed to get active arc: {e}")
            return None

    def get_chapters_range(self, story_id: int, start_chapter: int, end_chapter: int) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chapters WHERE story_id = ? AND chapter_number BETWEEN ? AND ? ORDER BY chapter_number ASC",
                (story_id, start_chapter, end_chapter)
            )
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            return [self._deserialize_json_fields('chapters', r) for r in results]
        except sqlite3.Error as e:
            self.log_error(f"Failed to get chapters range: {e}")
            return []

    # ========================================================================
    # CHAPTER PARTS OPERATIONS
    # ========================================================================

    def create_chapter_part(self, story_id: int, chapter_number: int, content: str,
                            title: Optional[str] = None, context_summary: Optional[str] = None,
                            story_progression_notes: Optional[str] = None) -> Optional[int]:
        try:
            part_number = self.get_next_part_number(story_id, chapter_number)
            data = {
                'chapter_number': chapter_number,
                'part_number': part_number,
                'title': title or f'Part {part_number}',
                'content': content,
                'word_count': len(content.split()),
                'context_summary': context_summary,
                'story_progression_notes': story_progression_notes,
                'is_merged': 0
            }
            part_id = self.create_entity('chapter_parts', story_id, data)
            if part_id:
                self.log_info(f"Created chapter part {part_number} for chapter {chapter_number} ({data['word_count']} words)")
            return part_id
        except Exception as e:
            self.log_error(f"Failed to create chapter part: {e}")
            return None

    def get_chapter_parts(self, story_id: int, chapter_number: int,
                          include_merged: bool = False) -> List[Dict[str, Any]]:
        try:
            filters: Dict[str, Any] = {'chapter_number': chapter_number}
            if not include_merged:
                filters['is_merged'] = 0
            return self.get_entities_by_story('chapter_parts', story_id, 'part_number ASC', filters)
        except Exception as e:
            self.log_error(f"Failed to get chapter parts: {e}")
            return []

    def get_next_part_number(self, story_id: int, chapter_number: int) -> int:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(part_number) as max_num FROM chapter_parts WHERE story_id = ? AND chapter_number = ?",
                (story_id, chapter_number)
            )
            result = cursor.fetchone()
            if result and result['max_num'] is not None:
                return result['max_num'] + 1
            return 1
        except sqlite3.Error as e:
            self.log_error(f"Failed to get next part number: {e}")
            return 1

    def merge_chapter_parts(self, story_id: int, chapter_number: int,
                            part_ids: List[int], merged_title: Optional[str] = None) -> Optional[int]:
        try:
            parts = []
            for part_id in part_ids:
                part = self.get_entity('chapter_parts', part_id, story_id)
                if part:
                    parts.append(part)
            if not parts:
                self.log_error("No valid parts to merge")
                return None
            parts.sort(key=lambda x: x['part_number'])
            merged_content = '\n\n'.join(part['content'] for part in parts)
            total_words = sum(part['word_count'] for part in parts)
            from models.chapter import Chapter
            chapter = Chapter(story_id, chapter_number=chapter_number,
                              title=merged_title or f"Chapter {chapter_number}",
                              content=merged_content, word_count=total_words, status='draft')
            if chapter.save():
                with self.transaction(story_id) as cursor:
                    for part_id in part_ids:
                        cursor.execute(
                            "UPDATE chapter_parts SET is_merged = 1, merged_into_chapter_id = ? WHERE id = ? AND story_id = ?",
                            (chapter.id, part_id, story_id)
                        )
                self.log_info(f"Merged {len(parts)} parts into chapter {chapter.id} ({total_words} words)")
                return chapter.id
            return None
        except Exception as e:
            self.log_error(f"Failed to merge chapter parts: {e}")
            return None

    def delete_chapter_part(self, story_id: int, part_id: int) -> bool:
        return self.delete_entity('chapter_parts', part_id, story_id)

    # ========================================================================
    # SEARCH — NAME / TITLE ONLY  (used by SearchWidget)
    # ========================================================================

    def search_by_name_title(
        self,
        story_id: int,
        query: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search each entity table by its primary display column ONLY
        (name or title).  This prevents false positives from body-text
        fields like personality, background, content, etc.

        Returns {entity_type: [rows]} for tables that have matches.
        """
        if not query or not query.strip():
            return {}

        pattern = f"%{query.strip()}%"
        results: Dict[str, List[Dict[str, Any]]] = {}

        try:
            conn   = self.get_connection(story_id)
            cursor = conn.cursor()

            # characters — search by name only
            cursor.execute(
                "SELECT * FROM characters WHERE story_id = ? AND name LIKE ? ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cursor.fetchall()
            if rows:
                results['characters'] = [dict(r) for r in rows]

            # locations — search by name only
            cursor.execute(
                "SELECT * FROM locations WHERE story_id = ? AND name LIKE ? ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cursor.fetchall()
            if rows:
                results['locations'] = [dict(r) for r in rows]

            # lore_entries — search by title only
            cursor.execute(
                "SELECT * FROM lore_entries WHERE story_id = ? AND title LIKE ? ORDER BY importance DESC, title ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cursor.fetchall()
            if rows:
                results['lore_entries'] = [
                    self._deserialize_json_fields('lore_entries', dict(r)) for r in rows
                ]

            # bestiary — search by name only
            cursor.execute(
                "SELECT * FROM bestiary WHERE story_id = ? AND name LIKE ? ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cursor.fetchall()
            if rows:
                results['bestiary'] = [dict(r) for r in rows]

            # organizations — search by name only
            cursor.execute(
                "SELECT * FROM organizations WHERE story_id = ? AND name LIKE ? ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cursor.fetchall()
            if rows:
                results['organizations'] = [
                    self._deserialize_json_fields('organizations', dict(r)) for r in rows
                ]

            # power_systems — search by name only
            cursor.execute(
                "SELECT * FROM power_systems WHERE story_id = ? AND name LIKE ? ORDER BY name ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cursor.fetchall()
            if rows:
                results['power_systems'] = [dict(r) for r in rows]

            # chapters — search by title only (chapter_number not a name match)
            cursor.execute(
                "SELECT * FROM chapters WHERE story_id = ? AND title LIKE ? ORDER BY chapter_number ASC LIMIT 20",
                (story_id, pattern),
            )
            rows = cursor.fetchall()
            if rows:
                results['chapters'] = [dict(r) for r in rows]

            total = sum(len(v) for v in results.values())
            self.log_debug(f"search_by_name_title '{query}' → {total} results for story {story_id}")
            return results

        except Exception as e:
            self.log_error(f"search_by_name_title failed: {e}")
            return {}

    # ========================================================================
    # FULL-TEXT SEARCH  (kept for other callers such as the legacy dialog)
    # ========================================================================

    def search_all_entities(self, story_id: int, query: str,
                            entity_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        if not query or not query.strip():
            return {}

        search_pattern = f"%{query.strip()}%"

        default_types = [
            'characters', 'locations', 'lore_entries',
            'bestiary', 'organizations', 'power_systems', 'chapters'
        ]
        if not entity_types:
            entity_types = default_types
        safe_types = [t for t in entity_types if t != 'chapter_parts']

        results: Dict[str, List[Dict[str, Any]]] = {}

        try:
            conn   = self.get_connection(story_id)
            cursor = conn.cursor()

            if 'characters' in safe_types:
                cursor.execute(
                    "SELECT * FROM characters WHERE story_id = ? AND (name LIKE ? OR personality LIKE ? OR background LIKE ?) ORDER BY name ASC LIMIT 20",
                    (story_id, search_pattern, search_pattern, search_pattern)
                )
                results['characters'] = [dict(r) for r in cursor.fetchall()]

            if 'locations' in safe_types:
                cursor.execute(
                    "SELECT * FROM locations WHERE story_id = ? AND (name LIKE ? OR description LIKE ?) ORDER BY name ASC LIMIT 20",
                    (story_id, search_pattern, search_pattern)
                )
                results['locations'] = [dict(r) for r in cursor.fetchall()]

            if 'lore_entries' in safe_types:
                cursor.execute(
                    "SELECT * FROM lore_entries WHERE story_id = ? AND (title LIKE ? OR content LIKE ? OR category LIKE ?) ORDER BY importance DESC LIMIT 20",
                    (story_id, search_pattern, search_pattern, search_pattern)
                )
                results['lore_entries'] = [dict(r) for r in cursor.fetchall()]

            if 'bestiary' in safe_types:
                cursor.execute(
                    "SELECT * FROM bestiary WHERE story_id = ? AND (name LIKE ? OR category LIKE ? OR behavior LIKE ?) ORDER BY name ASC LIMIT 20",
                    (story_id, search_pattern, search_pattern, search_pattern)
                )
                results['bestiary'] = [dict(r) for r in cursor.fetchall()]

            if 'organizations' in safe_types:
                cursor.execute(
                    "SELECT * FROM organizations WHERE story_id = ? AND (name LIKE ? OR description LIKE ? OR goals LIKE ?) ORDER BY name ASC LIMIT 20",
                    (story_id, search_pattern, search_pattern, search_pattern)
                )
                results['organizations'] = [dict(r) for r in cursor.fetchall()]

            if 'power_systems' in safe_types:
                cursor.execute(
                    "SELECT * FROM power_systems WHERE story_id = ? AND (name LIKE ? OR system_name LIKE ? OR description LIKE ?) ORDER BY name ASC LIMIT 20",
                    (story_id, search_pattern, search_pattern, search_pattern)
                )
                results['power_systems'] = [dict(r) for r in cursor.fetchall()]

            if 'chapters' in safe_types:
                cursor.execute(
                    "SELECT * FROM chapters WHERE story_id = ? AND (title LIKE ? OR content LIKE ? OR summary LIKE ?) ORDER BY chapter_number ASC LIMIT 20",
                    (story_id, search_pattern, search_pattern, search_pattern)
                )
                results['chapters'] = [dict(r) for r in cursor.fetchall()]

            if 'chapter_parts' in entity_types:
                try:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chapter_parts'")
                    if cursor.fetchone():
                        cursor.execute(
                            "SELECT * FROM chapter_parts WHERE story_id = ? AND (title LIKE ? OR content LIKE ?) AND is_merged = 0 ORDER BY chapter_number ASC, part_number ASC LIMIT 20",
                            (story_id, search_pattern, search_pattern)
                        )
                        results['chapter_parts'] = [dict(r) for r in cursor.fetchall()]
                except sqlite3.Error:
                    pass

            total = sum(len(v) for v in results.values())
            self.log_info(f"search_all_entities '{query}' → {total} results")
            return results

        except Exception as e:
            self.log_error(f"search_all_entities failed: {e}")
            return {}

    # ========================================================================
    # VALIDATION & INTEGRITY
    # ========================================================================

    def validate_foreign_keys(self, table: str, data: Dict[str, Any]) -> bool:
        return True

    def check_duplicate_names(self, table: str, name: str, story_id: int,
                               exclude_id: Optional[int] = None) -> bool:
        if table not in ['characters', 'locations', 'bestiary', 'power_systems']:
            return False
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE story_id = ? AND name = ? AND id != ?", (story_id, name, exclude_id))
            else:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE story_id = ? AND name = ?", (story_id, name))
            return cursor.fetchone()[0] > 0
        except sqlite3.Error as e:
            self.log_error(f"Error checking duplicate names: {e}")
            return False

    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================

    def bulk_insert(self, story_id: int, table: str, data_list: List[Dict[str, Any]]) -> bool:
        if not self._is_valid_table(table):
            raise ValidationError(f"Invalid table name: {table}")
        if not data_list:
            return True
        for data in data_list:
            data['story_id'] = story_id
        columns = list(data_list[0].keys())
        try:
            with self.transaction(story_id) as cursor:
                placeholders = ', '.join(['?' for _ in columns])
                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                serialized = [
                    tuple(self._serialize_json_fields(table, r).get(c) for c in columns)
                    for r in data_list
                ]
                cursor.executemany(query, serialized)
                self.log_info(f"Bulk inserted {len(data_list)} records into {table}")
                return True
        except sqlite3.Error as e:
            self.log_error(f"Failed to bulk insert into {table}: {e}")
            return False

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _is_valid_table(self, table: str) -> bool:
        valid_tables = {
            'stories', 'characters', 'locations', 'power_systems', 'bestiary',
            'lore_entries', 'organizations', 'arcs', 'chapters',
            'chapter_parts',
            'chapter_versions',
            'timeline_states',
            'generation_history',
            'media_gallery',
            'character_relationships',
            'location_connections',
            'items',
        }
        return table in valid_tables

    def _get_json_fields(self, table: str) -> List[str]:
        json_fields_map = {
            'characters':    ['relationships'],
            'locations':     ['connected_locations'],
            'bestiary':      ['behavior', 'weaknesses', 'relationships'],
            'lore_entries':  ['related_characters', 'related_locations'],
            'powers':         ['related_characters', 'related_locations'],
            'organizations':  ['members', 'goals', 'relationships'],
            'items':          ['properties', 'powers'],
            'chapters':      ['featured_characters', 'featured_locations', 'approved_sections'],
            'timeline_states': [
                'character_states', 'active_conflicts', 'plot_threads',
                'unresolved_events', 'world_changes', 'cause_effect_chains',
            ],
        }
        return json_fields_map.get(table, [])

    def _serialize_json_fields(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        json_fields = self._get_json_fields(table)
        result = data.copy()
        for field in json_fields:
            if field in result and result[field] is not None:
                if not isinstance(result[field], str):
                    result[field] = json.dumps(result[field])
        return result

    def _deserialize_json_fields(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        json_fields = self._get_json_fields(table)
        result = data.copy()
        for field in json_fields:
            if field in result and result[field] is not None:
                if isinstance(result[field], str):
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, ValueError):
                        # Leave as plain string — do NOT null it out.
                        pass
        return result

    def _get_total_word_count(self, story_id: int) -> int:
        try:
            conn = self.get_connection(story_id)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(word_count) FROM chapters WHERE story_id = ?", (story_id,))
            result = cursor.fetchone()[0]
            return result if result else 0
        except sqlite3.Error:
            return 0


# Global instance
db_manager = DatabaseManager()