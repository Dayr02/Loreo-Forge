"""
Story Manager - Story Registry System
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.logger import LoggerMixin


class StoryManager(LoggerMixin):
    """
    Central registry for managing multiple stories
    Ensures only one story is active at a time
    ENHANCED: Complete story deletion including physical files
    """
    
    def __init__(self, db_manager):
        """
        Initialize Story Manager
        
        Args:
            db_manager: Database manager instance (for per-story databases)
        """
        from database.master_db import master_db
        
        self.db = master_db  # Use master database for stories table
        self.story_db = db_manager  # Keep reference for per-story operations
        self._active_story_id: Optional[int] = None
        self._active_story_cache: Optional[Dict[str, Any]] = None
        
        # Initialize on first run
        self._ensure_story_exists()
        
    def _ensure_story_exists(self):
        """Ensure at least one story exists, create default if needed"""
        stories = self.get_all_stories()
        
        if not stories:
            self.log_info("No stories found, creating default story")
            story_id = self.create_story(
                title="My First Story",
                genre="Fantasy",
                synopsis="A new adventure begins..."
            )
            self.set_active_story(story_id)
        else:
            # Set first story as active if none is active
            active = self.get_active_story()
            if not active:
                self.set_active_story(stories[0]['id'])
    
    # ========================================
    # Story CRUD Operations
    # ========================================
    
    def create_story(self, title: str, genre: str = "", 
                    setting: str = "", tone: str = "",
                    target_audience: str = "", synopsis: str = "",
                    notes: str = "") -> int:
        """
        Create a new story
        
        Args:
            title: Story title (must be unique)
            genre: Story genre
            setting: Story setting
            tone: Story tone
            target_audience: Target audience
            synopsis: Story synopsis
            notes: Additional notes
            
        Returns:
            int: New story ID
            
        Raises:
            ValueError: If story with title already exists
        """
        # Check for duplicate title
        existing = self.db.fetch_one(
            "SELECT id FROM stories WHERE title = ?",
            (title,)
        )
        
        if existing:
            raise ValueError(f"Story with title '{title}' already exists")
        
        # Create story
        query = """
            INSERT INTO stories (
                title, genre, setting, tone, target_audience, 
                synopsis, notes, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """
        
        story_id = self.db.execute(
            query,
            (title, genre, setting, tone, target_audience, synopsis, notes)
        )
        
        self.log_info(f"Created story: {title} (ID: {story_id})")
        return story_id
    
    def get_story(self, story_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a story by ID
        
        Args:
            story_id: Story ID
            
        Returns:
            Dict with story data or None if not found
        """
        story = self.db.fetch_one(
            "SELECT * FROM stories WHERE id = ?",
            (story_id,)
        )
        
        if story:
            return dict(story)
        return None
    
    def get_all_stories(self) -> List[Dict[str, Any]]:
        """
        Get all stories
        
        Returns:
            List of story dictionaries
        """
        stories = self.db.fetch_all(
            "SELECT * FROM stories ORDER BY updated_at DESC"
        )
        
        return [dict(story) for story in stories]
    
    def update_story(self, story_id: int, **kwargs) -> bool:
        """
        Update a story
        
        Args:
            story_id: Story ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if updated, False if not found
        """
        story = self.get_story(story_id)
        if not story:
            self.log_error(f"Story {story_id} not found")
            return False
        
        # Build update query
        allowed_fields = [
            'title', 'genre', 'setting', 'tone', 'target_audience',
            'synopsis', 'notes'
        ]
        
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return True
        
        # Add updated_at
        updates.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"UPDATE stories SET {', '.join(updates)} WHERE id = ?"
        values.append(story_id)
        
        self.db.execute(query, tuple(values))
        
        # Clear cache if this is the active story
        if story_id == self._active_story_id:
            self._active_story_cache = None
        
        self.log_info(f"Updated story {story_id}")
        return True
    
    def delete_story(self, story_id: int, force: bool = False) -> bool:
        """
        Delete a story and all its entities - COMPLETE DELETION
        
        Args:
            story_id: Story ID
            force: If True, allows deleting active story
            
        Returns:
            bool: True if deleted, False if not found or is active
            
        Note:
            This PERMANENTLY deletes:
            1. The story entry from master database
            2. The physical story_N.db file from disk
            3. ALL associated data (chapters, characters, locations, etc.)
        """
        story = self.get_story(story_id)
        if not story:
            self.log_error(f"Story {story_id} not found")
            return False
        
        # Prevent deleting active story unless forced
        if story_id == self._active_story_id and not force:
            self.log_error("Cannot delete active story")
            return False
        
        story_title = story['title']
        
        try:
            # STEP 1: Close any open database connections to this story
            self.log_info(f"Closing database connection for story {story_id}...")
            self.story_db.close_connection(story_id)
            
            # STEP 2: Delete the physical database file from disk
            from config.settings import settings
            db_path = settings.get_story_db_path(story_id)
            
            if db_path.exists():
                self.log_info(f"Deleting physical database file: {db_path}")
                db_path.unlink()  # Delete the file
                self.log_info(f"✓ Deleted database file: {db_path.name}")
            else:
                self.log_warning(f"Database file not found: {db_path}")
            
            # STEP 3: If deleting active story, switch to another
            if story_id == self._active_story_id:
                other_stories = [s for s in self.get_all_stories() if s['id'] != story_id]
                if other_stories:
                    self.set_active_story(other_stories[0]['id'])
                    self.log_info(f"Switched active story to: {other_stories[0]['title']}")
                else:
                    self._active_story_id = None
                    self._active_story_cache = None
                    self.log_info("No remaining stories - cleared active story")
            
            # STEP 4: Delete story entry from master database
            self.db.execute("DELETE FROM stories WHERE id = ?", (story_id,))
            self.log_info(f"✓ Deleted story entry from master database")
            
            self.log_info(f"✅ COMPLETE DELETION: Story '{story_title}' (ID: {story_id}) and all associated data")
            return True
            
        except Exception as e:
            self.log_error(f"Error during story deletion: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def rename_story(self, story_id: int, new_title: str) -> bool:
        """
        Rename a story
        
        Args:
            story_id: Story ID
            new_title: New title
            
        Returns:
            bool: True if renamed, False if failed
        """
        # Check for duplicate
        existing = self.db.fetch_one(
            "SELECT id FROM stories WHERE title = ? AND id != ?",
            (new_title, story_id)
        )
        
        if existing:
            self.log_error(f"Story with title '{new_title}' already exists")
            return False
        
        return self.update_story(story_id, title=new_title)
    
    # ========================================
    # Active Story Management
    # ========================================
    
    def get_active_story_id(self) -> Optional[int]:
        """
        Get the active story ID
        
        Returns:
            int: Active story ID or None
        """
        return self._active_story_id
    
    def get_active_story(self) -> Optional[Dict[str, Any]]:
        """
        Get the active story
        
        Returns:
            Dict with active story data or None
        """
        if self._active_story_cache:
            return self._active_story_cache
        
        if not self._active_story_id:
            # Try to get from database
            story = self.db.fetch_one(
                "SELECT * FROM stories WHERE is_active = 1 LIMIT 1"
            )
            if story:
                self._active_story_id = story['id']
                self._active_story_cache = dict(story)
                return self._active_story_cache
            return None
        
        story = self.get_story(self._active_story_id)
        if story:
            self._active_story_cache = story
        return story
    
    def set_active_story(self, story_id: int) -> bool:
        """
        Set the active story
        
        Args:
            story_id: Story ID to activate
            
        Returns:
            bool: True if set, False if not found
        """
        story = self.get_story(story_id)
        if not story:
            self.log_error(f"Story {story_id} not found")
            return False
        
        # Deactivate all stories
        self.db.execute("UPDATE stories SET is_active = 0")
        
        # Activate selected story
        self.db.execute(
            "UPDATE stories SET is_active = 1 WHERE id = ?",
            (story_id,)
        )
        
        # Update cache
        self._active_story_id = story_id
        self._active_story_cache = story
        
        self.log_info(f"Set active story: {story['title']} (ID: {story_id})")
        return True
    
    def require_active_story(self) -> int:
        """
        Require that an active story exists
        
        Returns:
            int: Active story ID
            
        Raises:
            RuntimeError: If no active story
        """
        if not self._active_story_id:
            active = self.get_active_story()
            if not active:
                raise RuntimeError("No active story. Please create or select a story.")
        
        return self._active_story_id
    
    # ========================================
    # Story Statistics
    # ========================================
    
    def get_story_stats(self, story_id: int) -> Dict[str, int]:
        stats = {
            'total_chapters': 0,
            'total_characters': 0,
            'total_locations': 0,
            'total_lore_entries': 0,
            'total_power_systems': 0,
            'total_bestiary': 0,
            'total_word_count': 0
        }
        
        try:
            # Use story_db to query entity tables in story-specific database
            stats['total_chapters'] = self.story_db.count_entities('chapters', story_id)
            stats['total_characters'] = self.story_db.count_entities('characters', story_id)
            stats['total_locations'] = self.story_db.count_entities('locations', story_id)
            stats['total_lore_entries'] = self.story_db.count_entities('lore_entries', story_id)
            stats['total_power_systems'] = self.story_db.count_entities('power_systems', story_id)
            stats['total_bestiary'] = self.story_db.count_entities('bestiary', story_id)
            
            # Get total word count
            try:
                conn = self.story_db.get_connection(story_id)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT SUM(word_count) as total FROM chapters WHERE story_id = ?",
                    (story_id,)
                )
                result = cursor.fetchone()
                stats['total_word_count'] = result['total'] if result and result['total'] else 0
            except Exception as e:
                self.log_error(f"Error getting word count: {e}")
                stats['total_word_count'] = 0
                
        except Exception as e:
            self.log_error(f"Error getting story stats for story {story_id}: {e}")
        
        return stats
    
    # ========================================
    # Validation
    # ========================================
    
    def validate_story_id(self, story_id: int) -> bool:
        """
        Validate that a story ID exists
        
        Args:
            story_id: Story ID to validate
            
        Returns:
            bool: True if exists, False otherwise
        """
        story = self.get_story(story_id)
        return story is not None
