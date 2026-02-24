"""
Organization Model
Represents story organizations - guilds, factions, governments, groups
"""

from typing import Dict, Any, Optional, List
from models.base import BaseModel
from database import db_manager


class Organization(BaseModel):
    """
    Organization model - represents guilds, factions, governments, groups
    Includes structure, goals, membership, and relationships
    """
    
    _table_name = 'organizations'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        name = self._data.get('name', 'Unnamed Organization')
        org_type = self._data.get('type', 'organization')
        if self.id:
            return f"<Organization: {name} ({org_type}, ID: {self.id})>"
        return f"<Organization: {name} ({org_type}, unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def name(self) -> str:
        """Organization name"""
        return self._data.get('name', '')
    
    @name.setter
    def name(self, value: str):
        self._data['name'] = value
        self._modified_fields.add('name')
    
    @property
    def type(self) -> Optional[str]:
        """Organization type (Guild, Government, Military, Religious, etc.)"""
        return self._data.get('type')
    
    @type.setter
    def type(self, value: str):
        self._data['type'] = value
        self._modified_fields.add('type')
    
    @property
    def member_count(self) -> Optional[int]:
        """Number of members"""
        return self._data.get('member_count')
    
    @member_count.setter
    def member_count(self, value: int):
        self._data['member_count'] = value
        self._modified_fields.add('member_count')
    
    @property
    def description(self) -> Optional[str]:
        """Organization description"""
        return self._data.get('description')
    
    @description.setter
    def description(self, value: str):
        self._data['description'] = value
        self._modified_fields.add('description')
    
    @property
    def history(self) -> Optional[str]:
        """Organization history and founding"""
        return self._data.get('history')
    
    @history.setter
    def history(self, value: str):
        self._data['history'] = value
        self._modified_fields.add('history')
    
    @property
    def goals(self) -> Optional[str]:
        """Organization goals and objectives"""
        return self._data.get('goals')
    
    @goals.setter
    def goals(self, value: str):
        self._data['goals'] = value
        self._modified_fields.add('goals')
    
    @property
    def structure(self) -> Optional[str]:
        """Organizational structure and hierarchy"""
        return self._data.get('structure')
    
    @structure.setter
    def structure(self, value: str):
        self._data['structure'] = value
        self._modified_fields.add('structure')
    
    @property
    def leadership(self) -> Optional[str]:
        """Current leadership"""
        return self._data.get('leadership')
    
    @leadership.setter
    def leadership(self, value: str):
        self._data['leadership'] = value
        self._modified_fields.add('leadership')
    
    @property
    def members(self) -> Optional[str]:
        """Notable members description"""
        return self._data.get('members')
    
    @members.setter
    def members(self, value: str):
        self._data['members'] = value
        self._modified_fields.add('members')
    
    @property
    def territory(self) -> Optional[str]:
        """Controlled territory or area of influence"""
        return self._data.get('territory')
    
    @territory.setter
    def territory(self, value: str):
        self._data['territory'] = value
        self._modified_fields.add('territory')
    
    @property
    def resources(self) -> Optional[str]:
        """Organization resources and assets"""
        return self._data.get('resources')
    
    @resources.setter
    def resources(self, value: str):
        self._data['resources'] = value
        self._modified_fields.add('resources')
    
    @property
    def allies(self) -> Optional[str]:
        """Allied organizations or groups"""
        return self._data.get('allies')
    
    @allies.setter
    def allies(self, value: str):
        self._data['allies'] = value
        self._modified_fields.add('allies')
    
    @property
    def rivals(self) -> Optional[str]:
        """Rival organizations or enemies"""
        return self._data.get('rivals')
    
    @rivals.setter
    def rivals(self, value: str):
        self._data['rivals'] = value
        self._modified_fields.add('rivals')
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    
    def get_member_characters(self) -> List['Character']:
        """
        Get all Character instances who are members
        Searches for this organization's name in character relationships or background
        
        Returns:
            List of Character instances
        """
        try:
            from models.character import Character
            all_characters = Character.get_all(self.story_id)
            member_characters = []
            
            org_name_lower = self.name.lower()
            
            for char in all_characters:
                # Check background for mentions
                if char.background and org_name_lower in char.background.lower():
                    member_characters.append(char)
                    continue
                
                # Check relationships JSON
                if char.relationships:
                    for rel in char.relationships:
                        if isinstance(rel, dict):
                            desc = rel.get('description', '')
                            if desc and org_name_lower in desc.lower():
                                member_characters.append(char)
                                break
            
            return member_characters
            
        except Exception as e:
            self.logger.error(f"Failed to get member characters: {e}")
            return []
    
    def get_territory_locations(self) -> List['Location']:
        """
        Get all Location instances in organization's territory
        Searches for this organization's name in location descriptions
        
        Returns:
            List of Location instances
        """
        try:
            from models.location import Location
            all_locations = Location.get_all(self.story_id)
            territory_locations = []
            
            org_name_lower = self.name.lower()
            
            for loc in all_locations:
                # Check description
                if loc.description and org_name_lower in loc.description.lower():
                    territory_locations.append(loc)
                    continue
                
                # Check history
                if loc.history and org_name_lower in loc.history.lower():
                    territory_locations.append(loc)
                    continue
                
                # Check inhabitants
                if loc.inhabitants and org_name_lower in loc.inhabitants.lower():
                    territory_locations.append(loc)
            
            return territory_locations
            
        except Exception as e:
            self.logger.error(f"Failed to get territory locations: {e}")
            return []
    
    def add_member(self, character_name: str) -> bool:
        """
        Add a member to the organization's members list
        
        Args:
            character_name: Name of character to add
            
        Returns:
            True if successful
        """
        current_members = self.members or ""
        
        # Check if already mentioned
        if character_name.lower() in current_members.lower():
            self.logger.info(f"{character_name} already in members list")
            return True
        
        # Add to list
        if current_members:
            self.members = f"{current_members}, {character_name}"
        else:
            self.members = character_name
        
        return self.save()
    
    def set_leader(self, character_name: str) -> bool:
        """
        Set the organization's leader
        
        Args:
            character_name: Name of leader character
            
        Returns:
            True if successful
        """
        self.leadership = character_name
        return self.save()
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate organization data
        
        Returns:
            True if valid, False otherwise
        """
        if not super().validate():
            return False
        
        # Name is required
        if not self.name or not self.name.strip():
            self.logger.error("Organization name is required")
            return False
        
        # Check for duplicate names
        if self._is_new or 'name' in self._modified_fields:
            has_duplicate = db_manager.check_duplicate_names(
                'organizations',
                self.name,
                self.story_id,
                exclude_id=self.id
            )
            
            if has_duplicate:
                self.logger.error(f"Organization name '{self.name}' already exists in this story")
                return False
        
        # Validate member_count if provided
        if self.member_count is not None and self.member_count < 0:
            self.logger.error("Member count cannot be negative")
            return False
        
        return True
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_summary(self) -> str:
        """
        Get a brief organization summary
        
        Returns:
            Summary string
        """
        parts = [f"{self.name}"]
        
        if self.type:
            parts.append(f"Type: {self.type}")
        
        if self.member_count is not None:
            parts.append(f"Members: {self.member_count}")
        
        if self.leadership:
            parts.append(f"Led by: {self.leadership}")
        
        if self.description:
            desc = self.description[:100]
            if len(self.description) > 100:
                desc += "..."
            parts.append(desc)
        
        return " | ".join(parts)
    
    def to_context_string(self) -> str:
        """
        Convert organization to string format suitable for AI context
        
        Returns:
            Formatted organization description
        """
        lines = [f"**{self.name}**"]
        
        if self.type:
            lines.append(f"Type: {self.type}")
        
        if self.member_count is not None:
            lines.append(f"Members: {self.member_count}")
        
        if self.description:
            lines.append(f"Description: {self.description}")
        
        if self.goals:
            lines.append(f"Goals: {self.goals}")
        
        if self.structure:
            lines.append(f"Structure: {self.structure}")
        
        if self.leadership:
            lines.append(f"Leadership: {self.leadership}")
        
        if self.territory:
            lines.append(f"Territory: {self.territory}")
        
        if self.resources:
            lines.append(f"Resources: {self.resources}")
        
        if self.allies:
            lines.append(f"Allies: {self.allies}")
        
        if self.rivals:
            lines.append(f"Rivals: {self.rivals}")
        
        if self.history:
            lines.append(f"History: {self.history[:150]}...")
        
        return "\n".join(lines)
    
    def get_power_level(self) -> str:
        """
        Estimate organization's power level based on various factors
        
        Returns:
            Power level description
        """
        score = 0
        
        # Member count
        if self.member_count:
            if self.member_count >= 1000:
                score += 3
            elif self.member_count >= 100:
                score += 2
            elif self.member_count >= 10:
                score += 1
        
        # Resources
        if self.resources:
            wealthy_keywords = ['vast', 'immense', 'unlimited', 'wealthy', 'rich']
            if any(kw in self.resources.lower() for kw in wealthy_keywords):
                score += 2
        
        # Territory
        if self.territory:
            large_keywords = ['empire', 'kingdom', 'continent', 'world', 'vast']
            if any(kw in self.territory.lower() for kw in large_keywords):
                score += 2
        
        # Leadership
        if self.leadership:
            powerful_titles = ['emperor', 'king', 'queen', 'archmage', 'supreme']
            if any(title in self.leadership.lower() for title in powerful_titles):
                score += 1
        
        if score >= 6:
            return "Major Power"
        elif score >= 4:
            return "Significant Influence"
        elif score >= 2:
            return "Moderate Power"
        else:
            return "Minor Organization"