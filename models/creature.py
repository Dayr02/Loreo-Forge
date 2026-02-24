"""
Creature Model
Represents bestiary creatures with abilities, weaknesses, and ecology
"""

from typing import Dict, Any, Optional, List
from models.base import BaseModel
from database import db_manager


class Creature(BaseModel):
    """
    Creature model - represents bestiary entries
    Includes appearance, behavior, abilities, ecology
    """
    
    _table_name = 'bestiary'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        name = self._data.get('name', 'Unknown')
        category = self._data.get('category', 'creature')
        if self.id:
            return f"<Creature: {name} ({category}, ID: {self.id})>"
        return f"<Creature: {name} ({category}, unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def name(self) -> str:
        """Creature name"""
        return self._data.get('name', '')
    
    @name.setter
    def name(self, value: str):
        self._data['name'] = value
        self._modified_fields.add('name')
    
    @property
    def category(self) -> Optional[str]:
        """Category (Beast, Monster, Dragon, Undead, etc.)"""
        return self._data.get('category')
    
    @category.setter
    def category(self, value: str):
        self._data['category'] = value
        self._modified_fields.add('category')
    
    @property
    def appearance(self) -> Optional[str]:
        """Physical appearance description"""
        return self._data.get('appearance')
    
    @appearance.setter
    def appearance(self, value: str):
        self._data['appearance'] = value
        self._modified_fields.add('appearance')
    
    @property
    def behavior(self) -> Optional[str]:
        """Behavioral patterns"""
        return self._data.get('behavior')
    
    @behavior.setter
    def behavior(self, value: str):
        self._data['behavior'] = value
        self._modified_fields.add('behavior')
    
    @property
    def abilities(self) -> Optional[str]:
        """Special abilities and powers"""
        return self._data.get('abilities')
    
    @abilities.setter
    def abilities(self, value: str):
        self._data['abilities'] = value
        self._modified_fields.add('abilities')
    
    @property
    def weaknesses(self) -> Optional[str]:
        """Known weaknesses"""
        return self._data.get('weaknesses')
    
    @weaknesses.setter
    def weaknesses(self, value: str):
        self._data['weaknesses'] = value
        self._modified_fields.add('weaknesses')
    
    @property
    def habitat(self) -> Optional[str]:
        """Natural habitat"""
        return self._data.get('habitat')
    
    @habitat.setter
    def habitat(self, value: str):
        self._data['habitat'] = value
        self._modified_fields.add('habitat')
    
    @property
    def is_sentient(self) -> bool:
        """Whether creature is sentient"""
        return bool(self._data.get('is_sentient', False))
    
    @is_sentient.setter
    def is_sentient(self, value: bool):
        self._data['is_sentient'] = value
        self._modified_fields.add('is_sentient')
    
    @property
    def is_magical(self) -> bool:
        """Whether creature has magical properties"""
        return bool(self._data.get('is_magical', False))
    
    @is_magical.setter
    def is_magical(self, value: bool):
        self._data['is_magical'] = value
        self._modified_fields.add('is_magical')
    
    @property
    def is_hostile(self) -> bool:
        """Whether creature is hostile"""
        return bool(self._data.get('is_hostile', True))
    
    @is_hostile.setter
    def is_hostile(self, value: bool):
        self._data['is_hostile'] = value
        self._modified_fields.add('is_hostile')
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """Validate creature data"""
        if not super().validate():
            return False
        
        if not self.name or not self.name.strip():
            self.logger.error("Creature name is required")
            return False
        
        return True
    
    def to_context_string(self) -> str:
        """Convert to AI context format"""
        lines = [f"**{self.name}**"]
        
        if self.category:
            lines.append(f"Category: {self.category}")
        
        if self.appearance:
            lines.append(f"Appearance: {self.appearance[:200]}")
        
        if self.behavior:
            lines.append(f"Behavior: {self.behavior[:200]}")
        
        if self.abilities:
            lines.append(f"Abilities: {self.abilities}")
        
        if self.weaknesses:
            lines.append(f"Weaknesses: {self.weaknesses}")
        
        return "\n".join(lines)