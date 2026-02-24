"""
Power System Model
Represents magic systems, abilities, and supernatural forces in the story
"""

from typing import Dict, Any, Optional, List
from models.base import BaseModel
from database import db_manager


class PowerSystem(BaseModel):
    """
    Power System model - represents magic systems, abilities, and supernatural forces
    Includes rules, limitations, and user relationships
    """
    
    _table_name = 'power_systems'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        name = self._data.get('name', 'Unnamed System')
        system_name = self._data.get('system_name', 'power system')
        if self.id:
            return f"<PowerSystem: {name} ({system_name}, ID: {self.id})>"
        return f"<PowerSystem: {name} ({system_name}, unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def name(self) -> str:
        """Display name for the power system entry"""
        return self._data.get('name', '')
    
    @name.setter
    def name(self, value: str):
        self._data['name'] = value
        self._modified_fields.add('name')
    
    @property
    def system_name(self) -> Optional[str]:
        """Name of the overall power system (e.g., 'Magic', 'Cultivation', 'Chi')"""
        return self._data.get('system_name')
    
    @system_name.setter
    def system_name(self, value: str):
        self._data['system_name'] = value
        self._modified_fields.add('system_name')
    
    @property
    def type(self) -> Optional[str]:
        """Type of power (Magic, Technology, Divine, Psychic, etc.)"""
        return self._data.get('type')
    
    @type.setter
    def type(self, value: str):
        self._data['type'] = value
        self._modified_fields.add('type')
    
    @property
    def description(self) -> Optional[str]:
        """Overall description of the power system"""
        return self._data.get('description')
    
    @description.setter
    def description(self, value: str):
        self._data['description'] = value
        self._modified_fields.add('description')
    
    @property
    def source(self) -> Optional[str]:
        """Source of the power (innate, learned, granted, etc.)"""
        return self._data.get('source')
    
    @source.setter
    def source(self, value: str):
        self._data['source'] = value
        self._modified_fields.add('source')
    
    @property
    def rules(self) -> Optional[str]:
        """Rules and mechanics of how the power works"""
        return self._data.get('rules')
    
    @rules.setter
    def rules(self, value: str):
        self._data['rules'] = value
        self._modified_fields.add('rules')
    
    @property
    def limitations(self) -> Optional[str]:
        """Limitations and costs of using the power"""
        return self._data.get('limitations')
    
    @limitations.setter
    def limitations(self, value: str):
        self._data['limitations'] = value
        self._modified_fields.add('limitations')
    
    @property
    def tiers(self) -> Optional[str]:
        """Power tiers or progression levels"""
        return self._data.get('tiers')
    
    @tiers.setter
    def tiers(self, value: str):
        self._data['tiers'] = value
        self._modified_fields.add('tiers')
    
    @property
    def users(self) -> Optional[str]:
        """Description of who can use this power"""
        return self._data.get('users')
    
    @users.setter
    def users(self, value: str):
        self._data['users'] = value
        self._modified_fields.add('users')
    
    @property
    def cultural_significance(self) -> Optional[str]:
        """Cultural or societal significance of the power"""
        return self._data.get('cultural_significance')
    
    @cultural_significance.setter
    def cultural_significance(self, value: str):
        self._data['cultural_significance'] = value
        self._modified_fields.add('cultural_significance')
    
    @property
    def weaknesses(self) -> Optional[str]:
        """Weaknesses or counters to this power"""
        return self._data.get('weaknesses')
    
    @weaknesses.setter
    def weaknesses(self, value: str):
        self._data['weaknesses'] = value
        self._modified_fields.add('weaknesses')
    
    @property
    def manifestations(self) -> Optional[str]:
        """How the power manifests or appears"""
        return self._data.get('manifestations')
    
    @manifestations.setter
    def manifestations(self, value: str):
        self._data['manifestations'] = value
        self._modified_fields.add('manifestations')
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    
    def get_user_characters(self) -> List['Character']:
        """
        Get all Character instances who use this power system
        Searches for this system's name in character abilities
        
        Returns:
            List of Character instances
        """
        try:
            from models.character import Character
            all_characters = Character.get_all(self.story_id)
            user_characters = []
            
            # Search keywords for matching
            search_terms = [self.name.lower()]
            if self.system_name:
                search_terms.append(self.system_name.lower())
            
            for char in all_characters:
                # Check abilities field
                if char.abilities:
                    abilities_lower = char.abilities.lower()
                    if any(term in abilities_lower for term in search_terms):
                        user_characters.append(char)
                        continue
                
                # Check background for mentions
                if char.background:
                    background_lower = char.background.lower()
                    if any(term in background_lower for term in search_terms):
                        user_characters.append(char)
            
            return user_characters
            
        except Exception as e:
            self.logger.error(f"Failed to get user characters: {e}")
            return []
    
    def get_related_items(self) -> List['Item']:
        """
        Get all Item instances related to this power system
        Searches for this system's name in item powers/properties
        
        Returns:
            List of Item instances
        """
        try:
            from models.item import Item
            all_items = Item.get_all(self.story_id)
            related_items = []
            
            search_terms = [self.name.lower()]
            if self.system_name:
                search_terms.append(self.system_name.lower())
            
            for item in all_items:
                # Check powers field
                if item.powers:
                    powers_lower = item.powers.lower()
                    if any(term in powers_lower for term in search_terms):
                        related_items.append(item)
                        continue
                
                # Check properties field
                if item.properties:
                    properties_lower = item.properties.lower()
                    if any(term in properties_lower for term in search_terms):
                        related_items.append(item)
            
            return related_items
            
        except Exception as e:
            self.logger.error(f"Failed to get related items: {e}")
            return []
    
    def add_user(self, character_name: str) -> bool:
        """
        Add a user to the power system's users list
        
        Args:
            character_name: Name of character to add
            
        Returns:
            True if successful
        """
        current_users = self.users or ""
        
        # Check if already mentioned
        if character_name.lower() in current_users.lower():
            self.logger.info(f"{character_name} already in users list")
            return True
        
        # Add to list
        if current_users:
            self.users = f"{current_users}, {character_name}"
        else:
            self.users = character_name
        
        return self.save()
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate power system data
        
        Returns:
            True if valid, False otherwise
        """
        if not super().validate():
            return False
        
        # Name is required
        if not self.name or not self.name.strip():
            self.logger.error("Power system name is required")
            return False
        
        # Check for duplicate names
        if self._is_new or 'name' in self._modified_fields:
            has_duplicate = db_manager.check_duplicate_names(
                'power_systems',
                self.name,
                self.story_id,
                exclude_id=self.id
            )
            
            if has_duplicate:
                self.logger.error(f"Power system name '{self.name}' already exists in this story")
                return False
        
        return True
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_summary(self) -> str:
        """
        Get a brief power system summary
        
        Returns:
            Summary string
        """
        parts = [f"{self.name}"]
        
        if self.system_name:
            parts.append(f"System: {self.system_name}")
        
        if self.type:
            parts.append(f"Type: {self.type}")
        
        if self.source:
            parts.append(f"Source: {self.source}")
        
        if self.description:
            desc = self.description[:100]
            if len(self.description) > 100:
                desc += "..."
            parts.append(desc)
        
        return " | ".join(parts)
    
    def to_context_string(self) -> str:
        """
        Convert power system to string format suitable for AI context
        
        Returns:
            Formatted power system description
        """
        lines = [f"**{self.name}**"]
        
        if self.system_name:
            lines.append(f"System: {self.system_name}")
        
        if self.type:
            lines.append(f"Type: {self.type}")
        
        if self.description:
            lines.append(f"Description: {self.description}")
        
        if self.source:
            lines.append(f"Source: {self.source}")
        
        if self.rules:
            lines.append(f"Rules: {self.rules}")
        
        if self.limitations:
            lines.append(f"Limitations: {self.limitations}")
        
        if self.tiers:
            lines.append(f"Tiers: {self.tiers}")
        
        if self.users:
            lines.append(f"Users: {self.users}")
        
        if self.weaknesses:
            lines.append(f"Weaknesses: {self.weaknesses}")
        
        if self.manifestations:
            lines.append(f"Manifestations: {self.manifestations}")
        
        return "\n".join(lines)
    
    def get_power_level(self) -> str:
        """
        Estimate the power level/scale of this system
        
        Returns:
            Power level description
        """
        score = 0
        
        # Check description for power indicators
        if self.description:
            desc_lower = self.description.lower()
            high_power_words = [
                'god', 'divine', 'reality', 'universe', 'omnipotent',
                'limitless', 'infinite', 'cosmic', 'transcendent'
            ]
            if any(word in desc_lower for word in high_power_words):
                score += 3
        
        # Check type
        if self.type:
            type_lower = self.type.lower()
            if 'divine' in type_lower or 'cosmic' in type_lower:
                score += 2
        
        # Check limitations (fewer limitations = more powerful)
        if self.limitations:
            if len(self.limitations) < 50:
                score += 1
        else:
            score += 2  # No stated limitations
        
        # Check for tiers
        if self.tiers:
            tier_count = self.tiers.count('\n') + 1
            if tier_count >= 5:
                score += 1
        
        if score >= 5:
            return "Reality-Warping"
        elif score >= 3:
            return "High-Level"
        elif score >= 2:
            return "Mid-Level"
        else:
            return "Low-Level"
    
    def is_restricted(self) -> bool:
        """
        Determine if power system has significant restrictions
        
        Returns:
            True if power is heavily restricted
        """
        restricted_keywords = [
            'forbidden', 'banned', 'illegal', 'restricted', 'secret',
            'hidden', 'lost', 'rare', 'exclusive', 'elite'
        ]
        
        # Check description
        if self.description:
            if any(kw in self.description.lower() for kw in restricted_keywords):
                return True
        
        # Check cultural significance
        if self.cultural_significance:
            if any(kw in self.cultural_significance.lower() for kw in restricted_keywords):
                return True
        
        # Check users description
        if self.users:
            if any(kw in self.users.lower() for kw in restricted_keywords):
                return True
        
        return False