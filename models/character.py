"""
Character Model
Represents a story character with full attributes and relationships
"""

from typing import Dict, Any, Optional, List
from models.base import BaseModel
from database import db_manager
from models.chapter import Chapter


class Character(BaseModel):
    """
    Character model - represents a story character
    Includes personality, background, relationships, and abilities
    """
    
    _table_name = 'characters'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        name = self._data.get('name', 'Unnamed')
        role = self._data.get('role', 'unknown')
        if self.id:
            return f"<Character: {name} ({role}, ID: {self.id})>"
        return f"<Character: {name} ({role}, unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def name(self) -> str:
        """Character name"""
        return self._data.get('name', '')
    
    @name.setter
    def name(self, value: str):
        self._data['name'] = value
        self._modified_fields.add('name')
    
    @property
    def role(self) -> Optional[str]:
        """Character role (protagonist, antagonist, supporting, etc.)"""
        return self._data.get('role')
    
    @role.setter
    def role(self, value: str):
        self._data['role'] = value
        self._modified_fields.add('role')
    
    @property
    def age(self) -> Optional[int]:
        """Character age"""
        return self._data.get('age')
    
    @age.setter
    def age(self, value: int):
        self._data['age'] = value
        self._modified_fields.add('age')
    
    @property
    def status(self) -> str:
        """Character status (alive, deceased, unknown)"""
        return self._data.get('status', 'alive')
    
    @status.setter
    def status(self, value: str):
        self._data['status'] = value
        self._modified_fields.add('status')
    
    @property
    def importance_weight(self) -> float:
        """Importance weight for context prioritization (0.0 - 1.0)"""
        return self._data.get('importance_weight', 0.5)
    
    @importance_weight.setter
    def importance_weight(self, value: float):
        self._data['importance_weight'] = max(0.0, min(1.0, value))
        self._modified_fields.add('importance_weight')
    
    @property
    def appearance(self) -> Optional[str]:
        """Physical appearance description"""
        return self._data.get('appearance')
    
    @appearance.setter
    def appearance(self, value: str):
        self._data['appearance'] = value
        self._modified_fields.add('appearance')
    
    @property
    def personality(self) -> Optional[str]:
        """Personality traits and characteristics"""
        return self._data.get('personality')
    
    @personality.setter
    def personality(self, value: str):
        self._data['personality'] = value
        self._modified_fields.add('personality')
    
    @property
    def background(self) -> Optional[str]:
        """Character background and history"""
        return self._data.get('background')
    
    @background.setter
    def background(self, value: str):
        self._data['background'] = value
        self._modified_fields.add('background')
    
    @property
    def goals(self) -> Optional[str]:
        """Character goals and motivations"""
        return self._data.get('goals')
    
    @goals.setter
    def goals(self, value: str):
        self._data['goals'] = value
        self._modified_fields.add('goals')
    
    @property
    def fears(self) -> Optional[str]:
        """Character fears and weaknesses"""
        return self._data.get('fears')
    
    @fears.setter
    def fears(self, value: str):
        self._data['fears'] = value
        self._modified_fields.add('fears')
    
    @property
    def abilities(self) -> Optional[str]:
        """Character abilities and powers"""
        return self._data.get('abilities')
    
    @abilities.setter
    def abilities(self, value: str):
        self._data['abilities'] = value
        self._modified_fields.add('abilities')
    
    @property
    def relationships(self) -> List[Dict[str, Any]]:
        """Character relationships (stored as JSON)"""
        return self._data.get('relationships', [])
    
    @relationships.setter
    def relationships(self, value: List[Dict[str, Any]]):
        self._data['relationships'] = value
        self._modified_fields.add('relationships')
    
    @property
    def voice_pattern(self) -> Optional[str]:
        """Character voice pattern for dialogue consistency"""
        return self._data.get('voice_pattern')
    
    @voice_pattern.setter
    def voice_pattern(self, value: str):
        self._data['voice_pattern'] = value
        self._modified_fields.add('voice_pattern')
    
    # ========================================================================
    # APPEARANCES & CHAPTERS
    # ========================================================================
    
    def get_appearances(self) -> List['Chapter']:
        """
        Get all chapters where this character appears
        
        Returns:
            List of Chapter instances
        """
        
        try:
            conn = db_manager.get_connection(self.story_id)
            cursor = conn.cursor()
            
            # Search in pov_character_id and featured_characters JSON
            query = """
                SELECT * FROM chapters 
                WHERE story_id = ? AND (
                    pov_character_id = ? OR
                    featured_characters LIKE ?
                )
                ORDER BY chapter_number ASC
            """
            
            search_pattern = f'%{self.id}%'
            cursor.execute(query, (self.story_id, self.id, search_pattern))
            
            rows = cursor.fetchall()
            chapters = []
            for row in rows:
                chapter_data = dict(row)
                # Deserialize JSON fields
                chapter_data = db_manager._deserialize_json_fields('chapters', chapter_data)
                chapters.append(Chapter(self.story_id, **chapter_data))
            
            return chapters
            
        except Exception as e:
            self.logger.error(f"Failed to get character appearances: {e}")
            return []
    
    def get_appearance_count(self) -> int:
        """
        Get number of chapters where character appears
        
        Returns:
            Chapter count
        """
        return len(self.get_appearances())
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    
    def add_relationship(
        self,
        character_id: int,
        relationship_type: str,
        description: Optional[str] = None
    ) -> bool:
        """
        Add a relationship to another character
        
        Args:
            character_id: ID of related character
            relationship_type: Type of relationship (friend, enemy, family, etc.)
            description: Optional description of the relationship
            
        Returns:
            True if successful
        """
        relationships = self.relationships.copy()
        
        # Check if relationship already exists
        for rel in relationships:
            if rel.get('character_id') == character_id:
                # Update existing relationship
                rel['type'] = relationship_type
                if description:
                    rel['description'] = description
                self.relationships = relationships
                return True
        
        # Add new relationship
        relationships.append({
            'character_id': character_id,
            'type': relationship_type,
            'description': description or ''
        })
        
        self.relationships = relationships
        return True
    
    def remove_relationship(self, character_id: int) -> bool:
        """
        Remove a relationship with another character
        
        Args:
            character_id: ID of related character
            
        Returns:
            True if relationship was removed
        """
        relationships = self.relationships.copy()
        original_count = len(relationships)
        
        relationships = [
            rel for rel in relationships 
            if rel.get('character_id') != character_id
        ]
        
        if len(relationships) < original_count:
            self.relationships = relationships
            return True
        
        return False
    
    def get_relationship_details(self) -> Dict[str, Any]:
        """
        Get detailed information about character relationships
        
        Returns:
            Dictionary with relationship data and related character info
        """
        return db_manager.get_character_relationships(self.id, self.story_id)
    
    # ========================================================================
    # CHARACTER DEVELOPMENT
    # ========================================================================
    
    def update_character_arc(self, arc_stage: str) -> bool:
        """
        Update character arc development stage
        
        Args:
            arc_stage: Description of current arc stage
            
        Returns:
            True if successful
        """
        self._data['character_arc'] = arc_stage
        self._modified_fields.add('character_arc')
        return self.save()
    
    def generate_voice_print(self) -> str:
        """
        Generate a voice pattern signature for dialogue consistency
        Based on personality and existing voice_pattern
        
        Returns:
            Voice print string
        """
        voice_elements = []
        
        if self.personality:
            voice_elements.append(f"Personality: {self.personality[:100]}")
        
        if self.voice_pattern:
            voice_elements.append(f"Pattern: {self.voice_pattern}")
        
        if self.background:
            voice_elements.append(f"Background influences: {self.background[:50]}")
        
        return " | ".join(voice_elements)
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate character data
        
        Returns:
            True if valid, False otherwise
        """
        if not super().validate():
            return False
        
        # Name is required
        if not self.name or not self.name.strip():
            self.logger.error("Character name is required")
            return False
        
        # Check for duplicate names
        if self._is_new or 'name' in self._modified_fields:
            has_duplicate = db_manager.check_duplicate_names(
                'characters',
                self.name,
                self.story_id,
                exclude_id=self.id
            )
            
            if has_duplicate:
                self.logger.error(f"Character name '{self.name}' already exists")
                return False
        
        # Validate importance_weight range
        if self.importance_weight < 0.0 or self.importance_weight > 1.0:
            self.logger.error("Importance weight must be between 0.0 and 1.0")
            return False
        
        return True
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_summary(self) -> str:
        """
        Get a brief character summary
        
        Returns:
            Summary string
        """
        parts = [f"{self.name} ({self.role or 'character'})"]
        
        if self.age:
            parts.append(f"Age: {self.age}")
        
        if self.status and self.status != 'alive':
            parts.append(f"Status: {self.status}")
        
        if self.personality:
            parts.append(f"Personality: {self.personality[:50]}...")
        
        return " | ".join(parts)
    
    def to_context_string(self) -> str:
        """
        Convert character to string format suitable for AI context
        
        Returns:
            Formatted character description
        """
        lines = [f"**{self.name}**"]
        
        if self.role:
            lines.append(f"Role: {self.role}")
        
        if self.age:
            lines.append(f"Age: {self.age}")
        
        if self.appearance:
            lines.append(f"Appearance: {self.appearance}")
        
        if self.personality:
            lines.append(f"Personality: {self.personality}")
        
        if self.background:
            lines.append(f"Background: {self.background}")
        
        if self.goals:
            lines.append(f"Goals: {self.goals}")
        
        if self.abilities:
            lines.append(f"Abilities: {self.abilities}")
        
        if self.relationships:
            rel_summary = ", ".join([
                f"{rel.get('type', 'related')} with character {rel.get('character_id')}"
                for rel in self.relationships
            ])
            lines.append(f"Relationships: {rel_summary}")
        
        return "\n".join(lines)