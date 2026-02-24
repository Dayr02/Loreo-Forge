"""
Lore Entry Model
Represents world-building lore entries with categorization
"""

from typing import Dict, Any, Optional, List
from models.base import BaseModel
from database import db_manager


class Lore(BaseModel):
    """
    Lore model - represents world-building entries
    Includes history, mythology, culture, technology
    """
    
    _table_name = 'lore_entries'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        title = self._data.get('title', 'Untitled')
        category = self._data.get('category', 'general')
        if self.id:
            return f"<Lore: {title} ({category}, ID: {self.id})>"
        return f"<Lore: {title} ({category}, unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def title(self) -> str:
        """Lore entry title"""
        return self._data.get('title', '')
    
    @title.setter
    def title(self, value: str):
        self._data['title'] = value
        self._modified_fields.add('title')
    
    @property
    def category(self) -> Optional[str]:
        """Category (history, mythology, culture, technology, custom)"""
        return self._data.get('category')
    
    @category.setter
    def category(self, value: str):
        self._data['category'] = value
        self._modified_fields.add('category')
    
    @property
    def content(self) -> Optional[str]:
        """Lore entry content"""
        return self._data.get('content')
    
    @content.setter
    def content(self, value: str):
        self._data['content'] = value
        self._modified_fields.add('content')
    
    @property
    def importance(self) -> int:
        """Importance rating (1-10)"""
        return self._data.get('importance', 5)
    
    @importance.setter
    def importance(self, value: int):
        self._data['importance'] = max(1, min(10, value))
        self._modified_fields.add('importance')
    
    @property
    def is_secret(self) -> bool:
        """Whether this is secret knowledge"""
        return bool(self._data.get('is_secret', False))
    
    @is_secret.setter
    def is_secret(self, value: bool):
        self._data['is_secret'] = value
        self._modified_fields.add('is_secret')
    
    @property
    def related_characters(self) -> List[int]:
        """List of related character IDs (JSON)"""
        return self._data.get('related_characters', [])
    
    @related_characters.setter
    def related_characters(self, value: List[int]):
        self._data['related_characters'] = value
        self._modified_fields.add('related_characters')
    
    @property
    def related_locations(self) -> List[int]:
        """List of related location IDs (JSON)"""
        return self._data.get('related_locations', [])
    
    @related_locations.setter
    def related_locations(self, value: List[int]):
        self._data['related_locations'] = value
        self._modified_fields.add('related_locations')
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """Validate lore entry data"""
        if not super().validate():
            return False
        
        if not self.title or not self.title.strip():
            self.logger.error("Lore title is required")
            return False
        
        return True
    
    def to_context_string(self) -> str:
        """Convert to AI context format"""
        lines = [f"**{self.title}**"]
        
        if self.category:
            lines.append(f"Category: {self.category}")
        
        if self.content:
            lines.append(f"Content: {self.content[:300]}...")
        
        return "\n".join(lines)