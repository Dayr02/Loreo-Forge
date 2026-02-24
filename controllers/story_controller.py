"""
Story Controller
Handles story operations and coordinates between UI and business logic
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal

from core.story_manager import StoryManager
from database import db_manager
from utils.logger import LoggerMixin


class StoryController(QObject, LoggerMixin):
    """
    Controller for story operations
    Bridges between UI and story management logic
    """
    
    # Signals
    story_created = pyqtSignal(int)  # story_id
    story_updated = pyqtSignal(int)  # story_id
    story_deleted = pyqtSignal(int)  # story_id
    story_activated = pyqtSignal(int)  # story_id
    error_occurred = pyqtSignal(str)  # error_message
    
    def __init__(self, parent=None):
        """Initialize story controller"""
        QObject.__init__(self, parent)
        LoggerMixin.__init__(self)
        
        self.story_manager = StoryManager(db_manager)
        self.log_info("StoryController initialized")
    
    def create_story(
        self,
        title: str,
        genre: str = "",
        setting: str = "",
        tone: str = "",
        target_audience: str = "",
        synopsis: str = "",
        notes: str = ""
    ) -> Optional[int]:
        """
        Create a new story
        
        Args:
            title: Story title
            genre: Story genre
            setting: Story setting
            tone: Story tone
            target_audience: Target audience
            synopsis: Story synopsis
            notes: Additional notes
            
        Returns:
            Story ID if successful, None otherwise
        """
        try:
            # Create story in master database
            story_id = self.story_manager.create_story(
                title=title,
                genre=genre,
                setting=setting,
                tone=tone,
                target_audience=target_audience,
                synopsis=synopsis,
                notes=notes
            )
            
            if story_id:
                # Initialize story-specific database
                if db_manager.initialize_database(story_id):
                    self.log_info(f"Story created successfully: {title} (ID: {story_id})")
                    self.story_created.emit(story_id)
                    return story_id
                else:
                    self.log_error(f"Failed to initialize database for story {story_id}")
                    # Rollback story creation
                    self.story_manager.delete_story(story_id, force=True)
                    self.error_occurred.emit("Failed to initialize story database")
                    return None
            
            return None
            
        except ValueError as e:
            # Duplicate title or validation error
            self.log_error(f"Story creation failed: {e}")
            self.error_occurred.emit(str(e))
            return None
        except Exception as e:
            self.log_error(f"Unexpected error creating story: {e}")
            self.error_occurred.emit(f"Failed to create story: {str(e)}")
            return None
    
    def update_story(
        self,
        story_id: int,
        **kwargs
    ) -> bool:
        """
        Update story metadata
        
        Args:
            story_id: Story ID
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        try:
            success = self.story_manager.update_story(story_id, **kwargs)
            
            if success:
                self.log_info(f"Story {story_id} updated successfully")
                self.story_updated.emit(story_id)
                return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Error updating story {story_id}: {e}")
            self.error_occurred.emit(f"Failed to update story: {str(e)}")
            return False
    
    def delete_story(self, story_id: int, force: bool = False) -> bool:
        """
        Delete a story and its database
        
        Args:
            story_id: Story ID
            force: Force deletion even if active
            
        Returns:
            True if successful
        """
        try:
            # Delete from master database
            if self.story_manager.delete_story(story_id, force=force):
                # Close database connection
                db_manager.close_connection(story_id)
                
                # Delete story database file
                db_path = db_manager.settings.get_story_db_path(story_id)
                if db_path.exists():
                    try:
                        db_path.unlink()
                        self.log_info(f"Deleted story database: {db_path}")
                    except Exception as e:
                        self.log_warning(f"Could not delete database file: {e}")
                
                self.log_info(f"Story {story_id} deleted successfully")
                self.story_deleted.emit(story_id)
                return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Error deleting story {story_id}: {e}")
            self.error_occurred.emit(f"Failed to delete story: {str(e)}")
            return False
    
    def activate_story(self, story_id: int) -> bool:
        """
        Set a story as the active story
        
        Args:
            story_id: Story ID to activate
            
        Returns:
            True if successful
        """
        try:
            if self.story_manager.set_active_story(story_id):
                self.log_info(f"Story {story_id} activated")
                self.story_activated.emit(story_id)
                return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Error activating story {story_id}: {e}")
            self.error_occurred.emit(f"Failed to activate story: {str(e)}")
            return False
    
    def get_story(self, story_id: int) -> Optional[Dict[str, Any]]:
        """
        Get story data
        
        Args:
            story_id: Story ID
            
        Returns:
            Story data dictionary or None
        """
        try:
            return self.story_manager.get_story(story_id)
        except Exception as e:
            self.log_error(f"Error getting story {story_id}: {e}")
            return None
    
    def get_all_stories(self) -> List[Dict[str, Any]]:
        """
        Get all stories
        
        Returns:
            List of story dictionaries
        """
        try:
            return self.story_manager.get_all_stories()
        except Exception as e:
            self.log_error(f"Error getting all stories: {e}")
            return []
    
    def get_active_story(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active story
        
        Returns:
            Active story data or None
        """
        try:
            return self.story_manager.get_active_story()
        except Exception as e:
            self.log_error(f"Error getting active story: {e}")
            return None
    
    def get_active_story_id(self) -> Optional[int]:
        """
        Get the active story ID
        
        Returns:
            Active story ID or None
        """
        try:
            return self.story_manager.get_active_story_id()
        except Exception as e:
            self.log_error(f"Error getting active story ID: {e}")
            return None
    
    def get_story_stats(self, story_id: int) -> Dict[str, Any]:
        """
        Get story statistics
        
        Args:
            story_id: Story ID
            
        Returns:
            Statistics dictionary
        """
        try:
            return self.story_manager.get_story_stats(story_id)
        except Exception as e:
            self.log_error(f"Error getting story stats: {e}")
            return {}
    
    def rename_story(self, story_id: int, new_title: str) -> bool:
        """
        Rename a story
        
        Args:
            story_id: Story ID
            new_title: New title
            
        Returns:
            True if successful
        """
        try:
            if self.story_manager.rename_story(story_id, new_title):
                self.log_info(f"Story {story_id} renamed to: {new_title}")
                self.story_updated.emit(story_id)
                return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Error renaming story {story_id}: {e}")
            self.error_occurred.emit(f"Failed to rename story: {str(e)}")
            return False