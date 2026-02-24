"""
Story Model
Represents a complete story project with metadata and statistics
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from models.base import BaseModel
from database import db_manager


class Story(BaseModel):
    """
    Story model - represents a story project
    Contains metadata, genre, synopsis, and computed statistics
    """
    
    _table_name = 'stories'
    
    def __init__(self, story_id: int, **kwargs):
        """
        Initialize Story instance
        
        Args:
            story_id: Story identifier (same as id for stories table)
            **kwargs: Field values
        """
        # For stories, story_id equals id
        if 'id' in kwargs:
            story_id = kwargs['id']
        super().__init__(story_id, **kwargs)
    
    def __str__(self) -> str:
        """Human-readable representation"""
        title = self._data.get('title', 'Untitled')
        if self.id:
            return f"<Story: {title} (ID: {self.id})>"
        return f"<Story: {title} (unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def title(self) -> str:
        """Story title"""
        return self._data.get('title', '')
    
    @title.setter
    def title(self, value: str):
        self._data['title'] = value
        self._modified_fields.add('title')
    
    @property
    def genre(self) -> Optional[str]:
        """Story genre"""
        return self._data.get('genre')
    
    @genre.setter
    def genre(self, value: str):
        self._data['genre'] = value
        self._modified_fields.add('genre')
    
    @property
    def setting(self) -> Optional[str]:
        """Story setting description"""
        return self._data.get('setting')
    
    @setting.setter
    def setting(self, value: str):
        self._data['setting'] = value
        self._modified_fields.add('setting')
    
    @property
    def tone(self) -> Optional[str]:
        """Story tone"""
        return self._data.get('tone')
    
    @tone.setter
    def tone(self, value: str):
        self._data['tone'] = value
        self._modified_fields.add('tone')
    
    @property
    def synopsis(self) -> Optional[str]:
        """Story synopsis"""
        return self._data.get('synopsis')
    
    @synopsis.setter
    def synopsis(self, value: str):
        self._data['synopsis'] = value
        self._modified_fields.add('synopsis')
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    
    def get_characters(self, filters: Optional[Dict[str, Any]] = None) -> List['Character']:
        """
        Load all characters associated with this story
        
        Args:
            filters: Optional filtering criteria
            
        Returns:
            List of Character instances
        """
        from models.character import Character
        return Character.get_all(self.story_id, filters=filters)
    
    def get_chapters(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = 'chapter_number'
    ) -> List['Chapter']:
        """
        Load all chapters for this story
        
        Args:
            filters: Optional filtering criteria
            sort_by: Field to sort by
            
        Returns:
            List of Chapter instances
        """
        from models.chapter import Chapter
        return Chapter.get_all(self.story_id, filters=filters, sort_by=sort_by)
    
    def get_locations(self) -> List['Location']:
        """
        Load all locations for this story
        
        Returns:
            List of Location instances
        """
        from models.location import Location
        return Location.get_all(self.story_id)
    
    def get_arcs(self, sort_by: str = 'arc_number') -> List['Arc']:
        """
        Load all story arcs
        
        Args:
            sort_by: Field to sort by
            
        Returns:
            List of Arc instances
        """
        from models.arc import Arc
        return Arc.get_all(self.story_id, sort_by=sort_by)
    
    def get_current_arc(self) -> Optional['Arc']:
        """
        Get the currently active story arc
        
        Returns:
            Active Arc instance or None
        """
        from models.arc import Arc
        arc_data = db_manager.get_active_arc(self.story_id)
        if arc_data:
            return Arc(self.story_id, **arc_data)
        return None
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive story statistics
        
        Returns:
            Dictionary containing statistics
        """
        metadata = db_manager.get_story_metadata(self.story_id)
        
        if not metadata:
            return {
                'total_chapters': 0,
                'total_characters': 0,
                'total_locations': 0,
                'total_lore_entries': 0,
                'total_word_count': 0,
                'average_chapter_length': 0
            }
        
        stats = {
            'total_chapters': metadata.get('total_chapters', 0),
            'total_characters': metadata.get('total_characters', 0),
            'total_locations': metadata.get('total_locations', 0),
            'total_lore_entries': metadata.get('total_lore_entries', 0),
            'total_word_count': metadata.get('total_word_count', 0),
        }
        
        # Calculate average chapter length
        if stats['total_chapters'] > 0:
            stats['average_chapter_length'] = int(
                stats['total_word_count'] / stats['total_chapters']
            )
        else:
            stats['average_chapter_length'] = 0
        
        return stats
    
    def get_word_count(self) -> int:
        """
        Get total word count across all chapters
        
        Returns:
            Total word count
        """
        stats = self.calculate_statistics()
        return stats.get('total_word_count', 0)
    
    def get_chapter_count(self) -> int:
        """
        Get total number of chapters
        
        Returns:
            Chapter count
        """
        stats = self.calculate_statistics()
        return stats.get('total_chapters', 0)
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate story data
        
        Returns:
            True if valid, False otherwise
        """
        if not super().validate():
            return False
        
        # Title is required
        if not self.title or not self.title.strip():
            self.logger.error("Story title is required")
            return False
        
        return True
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the story with key information
        
        Returns:
            Dictionary with story summary
        """
        stats = self.calculate_statistics()
        
        return {
            'id': self.id,
            'title': self.title,
            'genre': self.genre,
            'synopsis': self.synopsis[:200] + '...' if self.synopsis and len(self.synopsis) > 200 else self.synopsis,
            'created_at': self._data.get('created_at'),
            'updated_at': self._data.get('updated_at'),
            'statistics': stats
        }
    
    @classmethod
    def create_new(
        cls,
        title: str,
        genre: Optional[str] = None,
        setting: Optional[str] = None,
        synopsis: Optional[str] = None
    ) -> Optional['Story']:
        """
        Create and initialize a new story project
        
        Args:
            title: Story title
            genre: Story genre
            setting: Story setting
            synopsis: Story synopsis
            
        Returns:
            Story instance or None if creation failed
        """
        # Note: story_id will be assigned after save
        story = cls(
            story_id=0,  # Temporary, will be set after save
            title=title,
            genre=genre,
            setting=setting,
            synopsis=synopsis
        )
        
        if story.save():
            # Update story_id to match the saved id
            story.story_id = story.id
            return story
        
        return None