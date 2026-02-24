"""
Arc Model
Represents a story arc with chapters and thematic elements
"""

from typing import Dict, Any, Optional, List
from models.base import BaseModel
from database import db_manager


class Arc(BaseModel):
    """
    Arc model - represents a story arc or narrative segment
    Groups chapters together with thematic unity
    """
    
    _table_name = 'arcs'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        arc_num = self._data.get('arc_number', '?')
        title = self._data.get('title', 'Untitled Arc')
        if self.id:
            return f"<Arc {arc_num}: {title} (ID: {self.id})>"
        return f"<Arc {arc_num}: {title} (unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def arc_number(self) -> int:
        """Arc number in sequence"""
        return self._data.get('arc_number', 0)
    
    @arc_number.setter
    def arc_number(self, value: int):
        self._data['arc_number'] = value
        self._modified_fields.add('arc_number')
    
    @property
    def title(self) -> Optional[str]:
        """Arc title"""
        return self._data.get('title')
    
    @title.setter
    def title(self, value: str):
        self._data['title'] = value
        self._modified_fields.add('title')
    
    @property
    def description(self) -> Optional[str]:
        """Arc description"""
        return self._data.get('description')
    
    @description.setter
    def description(self, value: str):
        self._data['description'] = value
        self._modified_fields.add('description')
    
    @property
    def themes(self) -> Optional[str]:
        """Arc themes"""
        return self._data.get('themes')
    
    @themes.setter
    def themes(self, value: str):
        self._data['themes'] = value
        self._modified_fields.add('themes')
    
    @property
    def starting_chapter(self) -> Optional[int]:
        """Starting chapter number"""
        return self._data.get('starting_chapter')
    
    @starting_chapter.setter
    def starting_chapter(self, value: int):
        self._data['starting_chapter'] = value
        self._modified_fields.add('starting_chapter')
    
    @property
    def ending_chapter(self) -> Optional[int]:
        """Ending chapter number"""
        return self._data.get('ending_chapter')
    
    @ending_chapter.setter
    def ending_chapter(self, value: int):
        self._data['ending_chapter'] = value
        self._modified_fields.add('ending_chapter')
    
    @property
    def status(self) -> str:
        """Arc status (planned, in_progress, completed)"""
        return self._data.get('status', 'planned')
    
    @status.setter
    def status(self, value: str):
        self._data['status'] = value
        self._modified_fields.add('status')
    
    # ========================================================================
    # CHAPTERS
    # ========================================================================
    
    def get_chapters(self) -> List['Chapter']:
        """
        Get all chapters belonging to this arc
        
        Returns:
            List of Chapter instances
        """
        from models.chapter import Chapter
        
        chapters = Chapter.get_all(
            self.story_id,
            filters={'arc_id': self.id},
            sort_by='chapter_number',
            order='ASC'
        )
        
        return chapters
    
    def get_chapter_count(self) -> int:
        """
        Get number of chapters in this arc
        
        Returns:
            Chapter count
        """
        return len(self.get_chapters())
    
    def get_chapter_range(self) -> tuple[Optional[int], Optional[int]]:
        """
        Get the actual chapter range (min and max chapter numbers)
        
        Returns:
            Tuple of (min_chapter, max_chapter) or (None, None)
        """
        chapters = self.get_chapters()
        
        if not chapters:
            return (None, None)
        
        chapter_numbers = [ch.chapter_number for ch in chapters]
        return (min(chapter_numbers), max(chapter_numbers))
    
    # ========================================================================
    # PROGRESS TRACKING
    # ========================================================================
    
    def calculate_progress(self) -> float:
        """
        Calculate arc completion percentage
        
        Returns:
            Progress percentage (0.0 - 100.0)
        """
        if not self.starting_chapter or not self.ending_chapter:
            # If no range defined, use chapter count as heuristic
            chapters = self.get_chapters()
            if len(chapters) == 0:
                return 0.0
            
            # Assume some target (e.g., 10 chapters per arc)
            target = 10
            return min(100.0, (len(chapters) / target) * 100)
        
        # Calculate based on defined range
        total_chapters = self.ending_chapter - self.starting_chapter + 1
        
        # Count completed chapters
        chapters = self.get_chapters()
        completed = sum(1 for ch in chapters if ch.status == 'final')
        
        if total_chapters == 0:
            return 0.0
        
        return (completed / total_chapters) * 100
    
    def is_complete(self) -> bool:
        """
        Check if arc is complete
        
        Returns:
            True if status is 'completed'
        """
        return self.status == 'completed'
    
    def mark_as_complete(self) -> bool:
        """
        Mark arc as completed
        
        Returns:
            True if successful
        """
        self.status = 'completed'
        return self.save()
    
    def mark_as_in_progress(self) -> bool:
        """
        Mark arc as in progress
        
        Returns:
            True if successful
        """
        self.status = 'in_progress'
        return self.save()
    
    # ========================================================================
    # THEMES
    # ========================================================================
    
    def get_themes(self) -> List[str]:
        """
        Extract thematic elements from arc
        
        Returns:
            List of theme strings
        """
        if not self.themes:
            return []
        
        # Split themes by comma or newline
        if '\n' in self.themes:
            return [t.strip() for t in self.themes.split('\n') if t.strip()]
        else:
            return [t.strip() for t in self.themes.split(',') if t.strip()]
    
    def add_theme(self, theme: str) -> bool:
        """
        Add a theme to the arc
        
        Args:
            theme: Theme to add
            
        Returns:
            True if successful
        """
        themes = self.get_themes()
        
        if theme not in themes:
            themes.append(theme)
            self.themes = ', '.join(themes)
            return True
        
        return False
    
    def remove_theme(self, theme: str) -> bool:
        """
        Remove a theme from the arc
        
        Args:
            theme: Theme to remove
            
        Returns:
            True if theme was removed
        """
        themes = self.get_themes()
        
        if theme in themes:
            themes.remove(theme)
            self.themes = ', '.join(themes)
            return True
        
        return False
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive arc statistics
        
        Returns:
            Dictionary containing statistics
        """
        chapters = self.get_chapters()
        
        total_words = sum(ch.word_count for ch in chapters)
        
        stats = {
            'arc_number': self.arc_number,
            'title': self.title,
            'status': self.status,
            'total_chapters': len(chapters),
            'total_words': total_words,
            'progress_percentage': self.calculate_progress(),
            'starting_chapter': self.starting_chapter,
            'ending_chapter': self.ending_chapter,
            'themes': self.get_themes()
        }
        
        if chapters:
            stats['average_chapter_length'] = int(total_words / len(chapters))
            stats['first_chapter_number'] = chapters[0].chapter_number
            stats['last_chapter_number'] = chapters[-1].chapter_number
        else:
            stats['average_chapter_length'] = 0
            stats['first_chapter_number'] = None
            stats['last_chapter_number'] = None
        
        return stats
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate arc data
        
        Returns:
            True if valid, False otherwise
        """
        if not super().validate():
            return False
        
        # Arc number is required
        if self.arc_number <= 0:
            self.logger.error("Arc number must be positive")
            return False
        
        # Validate chapter range if provided
        if self.starting_chapter and self.ending_chapter:
            if self.starting_chapter > self.ending_chapter:
                self.logger.error("Starting chapter cannot be after ending chapter")
                return False
        
        # Validate status
        valid_statuses = ['planned', 'in_progress', 'completed']
        if self.status not in valid_statuses:
            self.logger.error(f"Invalid status: {self.status}")
            return False
        
        return True
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_summary(self) -> str:
        """
        Get a brief arc summary
        
        Returns:
            Summary string
        """
        parts = [f"Arc {self.arc_number}"]
        
        if self.title:
            parts.append(f"'{self.title}'")
        
        parts.append(f"Status: {self.status}")
        
        chapter_count = self.get_chapter_count()
        parts.append(f"{chapter_count} chapter(s)")
        
        if self.starting_chapter and self.ending_chapter:
            parts.append(f"Chapters {self.starting_chapter}-{self.ending_chapter}")
        
        return " | ".join(parts)
    
    def to_context_string(self) -> str:
        """
        Convert arc to string format suitable for AI context
        
        Returns:
            Formatted arc description
        """
        lines = [f"**Arc {self.arc_number}**"]
        
        if self.title:
            lines.append(f"Title: {self.title}")
        
        if self.description:
            lines.append(f"Description: {self.description}")
        
        if self.themes:
            lines.append(f"Themes: {self.themes}")
        
        lines.append(f"Status: {self.status}")
        
        if self.starting_chapter and self.ending_chapter:
            lines.append(f"Chapter Range: {self.starting_chapter}-{self.ending_chapter}")
        
        progress = self.calculate_progress()
        lines.append(f"Progress: {progress:.1f}%")
        
        return "\n".join(lines)