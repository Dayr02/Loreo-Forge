"""
Item Model
Represents story items - weapons, artifacts, equipment, magical objects
"""

from typing import Dict, Any, Optional, List
from models.base import BaseModel
from database import db_manager
from models.location import Location
from models.character import Character


class Item(BaseModel):
    """
    Item model - represents weapons, artifacts, equipment, magical objects
    Includes properties, powers, ownership, and history
    """
    
    _table_name = 'items'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        name = self._data.get('name', 'Unnamed Item')
        item_type = self._data.get('type', 'item')
        rarity = self._data.get('rarity', '')
        if self.id:
            return f"<Item: {name} ({item_type}, {rarity}, ID: {self.id})>"
        return f"<Item: {name} ({item_type}, unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def name(self) -> str:
        """Item name"""
        return self._data.get('name', '')
    
    @name.setter
    def name(self, value: str):
        self._data['name'] = value
        self._modified_fields.add('name')
    
    @property
    def type(self) -> Optional[str]:
        """Item type (Weapon, Armor, Artifact, Tool, etc.)"""
        return self._data.get('type')
    
    @type.setter
    def type(self, value: str):
        self._data['type'] = value
        self._modified_fields.add('type')
    
    @property
    def category(self) -> Optional[str]:
        """Item category (Melee, Ranged, Magical, Mundane, etc.)"""
        return self._data.get('category')
    
    @category.setter
    def category(self, value: str):
        self._data['category'] = value
        self._modified_fields.add('category')
    
    @property
    def rarity(self) -> Optional[str]:
        """Item rarity (Common, Uncommon, Rare, Epic, Legendary, etc.)"""
        return self._data.get('rarity')
    
    @rarity.setter
    def rarity(self, value: str):
        self._data['rarity'] = value
        self._modified_fields.add('rarity')
    
    @property
    def description(self) -> Optional[str]:
        """Physical description and appearance"""
        return self._data.get('description')
    
    @description.setter
    def description(self, value: str):
        self._data['description'] = value
        self._modified_fields.add('description')
    
    @property
    def properties(self) -> Optional[str]:
        """Special properties (magical or otherwise)"""
        return self._data.get('properties')
    
    @properties.setter
    def properties(self, value: str):
        self._data['properties'] = value
        self._modified_fields.add('properties')
    
    @property
    def powers(self) -> Optional[str]:
        """Powers or abilities granted by the item"""
        return self._data.get('powers')
    
    @powers.setter
    def powers(self, value: str):
        self._data['powers'] = value
        self._modified_fields.add('powers')
    
    @property
    def materials(self) -> Optional[str]:
        """Materials the item is made from"""
        return self._data.get('materials')
    
    @materials.setter
    def materials(self, value: str):
        self._data['materials'] = value
        self._modified_fields.add('materials')
    
    @property
    def creator(self) -> Optional[str]:
        """Name of the item's creator/craftsman"""
        return self._data.get('creator')
    
    @creator.setter
    def creator(self, value: str):
        self._data['creator'] = value
        self._modified_fields.add('creator')
    
    @property
    def history(self) -> Optional[str]:
        """Item's history and lore"""
        return self._data.get('history')
    
    @history.setter
    def history(self, value: str):
        self._data['history'] = value
        self._modified_fields.add('history')
    
    @property
    def current_owner(self) -> Optional[str]:
        """Current owner (character name or description)"""
        return self._data.get('current_owner')
    
    @current_owner.setter
    def current_owner(self, value: str):
        self._data['current_owner'] = value
        self._modified_fields.add('current_owner')
    
    @property
    def current_location(self) -> Optional[str]:
        """Current location (location name or description)"""
        return self._data.get('current_location')
    
    @current_location.setter
    def current_location(self, value: str):
        self._data['current_location'] = value
        self._modified_fields.add('current_location')
    
    @property
    def value(self) -> Optional[str]:
        """Item's monetary or trade value"""
        return self._data.get('value')
    
    @value.setter
    def value(self, value: str):
        self._data['value'] = value
        self._modified_fields.add('value')
    
    @property
    def notes(self) -> Optional[str]:
        """Additional notes about the item"""
        return self._data.get('notes')
    
    @notes.setter
    def notes(self, value: str):
        self._data['notes'] = value
        self._modified_fields.add('notes')
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    
    def get_owner_character(self) -> Optional['Character']:
        """
        Get the Character who currently owns this item
        Attempts to match current_owner string to character names
        
        Returns:
            Character instance or None
        """
        if not self.current_owner:
            return None
        
        try:
            characters = Character.get_all(self.story_id)
            
            # Try exact match first
            for char in characters:
                if char.name.lower() == self.current_owner.lower():
                    return char
            
            # Try partial match
            for char in characters:
                if char.name.lower() in self.current_owner.lower():
                    return char
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get owner character: {e}")
            return None
    
    def get_creator_character(self) -> Optional['Character']:
        """
        Get the Character who created this item
        Attempts to match creator string to character names
        
        Returns:
            Character instance or None
        """
        if not self.creator:
            return None
        
        try:
            from models.character import Character
            characters = Character.get_all(self.story_id)
            
            # Try exact match first
            for char in characters:
                if char.name.lower() == self.creator.lower():
                    return char
            
            # Try partial match
            for char in characters:
                if char.name.lower() in self.creator.lower():
                    return char
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get creator character: {e}")
            return None
    
    def get_location_object(self) -> Optional['Location']:
        """
        Get the Location where this item currently is
        Attempts to match current_location string to location names
        
        Returns:
            Location instance or None
        """
        if not self.current_location:
            return None
        
        try:
            locations = Location.get_all(self.story_id)
            
            # Try exact match first
            for loc in locations:
                if loc.name.lower() == self.current_location.lower():
                    return loc
            
            # Try partial match
            for loc in locations:
                if loc.name.lower() in self.current_location.lower():
                    return loc
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get location: {e}")
            return None
    
    def set_owner(self, character_name: str) -> bool:
        """
        Set the current owner of the item
        
        Args:
            character_name: Name of the character who owns this item
            
        Returns:
            True if successful
        """
        self.current_owner = character_name
        return self.save()
    
    def set_location(self, location_name: str) -> bool:
        """
        Set the current location of the item
        
        Args:
            location_name: Name of the location where item is
            
        Returns:
            True if successful
        """
        self.current_location = location_name
        return self.save()
    
    def transfer_ownership(self, new_owner: str, new_location: Optional[str] = None) -> bool:
        """
        Transfer ownership of the item to a new character
        
        Args:
            new_owner: Name of new owner
            new_location: Optional new location
            
        Returns:
            True if successful
        """
        self.current_owner = new_owner
        if new_location:
            self.current_location = new_location
        
        return self.save()
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate item data
        
        Returns:
            True if valid, False otherwise
        """
        if not super().validate():
            return False
        
        # Name is required
        if not self.name or not self.name.strip():
            self.logger.error("Item name is required")
            return False
        
        # Check for duplicate names
        if self._is_new or 'name' in self._modified_fields:
            has_duplicate = db_manager.check_duplicate_names(
                'items',
                self.name,
                self.story_id,
                exclude_id=self.id
            )
            
            if has_duplicate:
                self.logger.error(f"Item name '{self.name}' already exists in this story")
                return False
        
        # Validate rarity if provided
        valid_rarities = [
            'Common', 'Uncommon', 'Rare', 'Epic', 
            'Legendary', 'Mythical', 'Unique', None
        ]
        if self.rarity and self.rarity not in valid_rarities:
            self.logger.warning(
                f"Rarity '{self.rarity}' is not standard. "
                f"Standard values: {', '.join([r for r in valid_rarities if r])}"
            )
        
        return True
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_summary(self) -> str:
        """
        Get a brief item summary
        
        Returns:
            Summary string
        """
        parts = [f"{self.name}"]
        
        if self.type:
            parts.append(f"Type: {self.type}")
        
        if self.rarity:
            parts.append(f"Rarity: {self.rarity}")
        
        if self.current_owner:
            parts.append(f"Owner: {self.current_owner}")
        
        if self.current_location:
            parts.append(f"Location: {self.current_location}")
        
        if self.description:
            desc = self.description[:80]
            if len(self.description) > 80:
                desc += "..."
            parts.append(desc)
        
        return " | ".join(parts)
    
    def to_context_string(self) -> str:
        """
        Convert item to string format suitable for AI context
        
        Returns:
            Formatted item description
        """
        lines = [f"**{self.name}**"]
        
        if self.type:
            lines.append(f"Type: {self.type}")
        
        if self.category:
            lines.append(f"Category: {self.category}")
        
        if self.rarity:
            lines.append(f"Rarity: {self.rarity}")
        
        if self.description:
            lines.append(f"Description: {self.description}")
        
        if self.properties:
            lines.append(f"Properties: {self.properties}")
        
        if self.powers:
            lines.append(f"Powers: {self.powers}")
        
        if self.materials:
            lines.append(f"Materials: {self.materials}")
        
        if self.creator:
            lines.append(f"Created by: {self.creator}")
        
        if self.history:
            lines.append(f"History: {self.history[:150]}...")
        
        if self.current_owner:
            lines.append(f"Current Owner: {self.current_owner}")
        
        if self.current_location:
            lines.append(f"Current Location: {self.current_location}")
        
        if self.value:
            lines.append(f"Value: {self.value}")
        
        return "\n".join(lines)
    
    def get_rarity_emoji(self) -> str:
        """
        Get emoji representing item rarity
        
        Returns:
            Emoji string
        """
        rarity_map = {
            'Legendary': '🌟',
            'Mythical': '✨',
            'Unique': '💎',
            'Epic': '🔮',
            'Rare': '⭐',
            'Uncommon': '🗡️',
            'Common': '⚔️',
        }
        return rarity_map.get(self.rarity, '🗡️')
    
    def is_magical(self) -> bool:
        """
        Determine if item has magical properties
        
        Returns:
            True if item has magical properties or powers
        """
        magical_indicators = ['magical', 'enchanted', 'cursed', 'blessed', 'divine']
        
        # Check category
        if self.category and any(word in self.category.lower() for word in magical_indicators):
            return True
        
        # Check if it has powers
        if self.powers and self.powers.strip():
            return True
        
        # Check properties for magical keywords
        if self.properties:
            if any(word in self.properties.lower() for word in magical_indicators):
                return True
        
        return False
    
    def is_weapon(self) -> bool:
        """
        Determine if item is a weapon
        
        Returns:
            True if item is classified as a weapon
        """
        weapon_types = ['weapon', 'sword', 'axe', 'bow', 'staff', 'dagger', 'spear']
        
        if self.type:
            if any(wtype in self.type.lower() for wtype in weapon_types):
                return True
        
        if self.category:
            if 'melee' in self.category.lower() or 'ranged' in self.category.lower():
                return True
        
        return False
    
    def is_armor(self) -> bool:
        """
        Determine if item is armor
        
        Returns:
            True if item is classified as armor
        """
        armor_types = ['armor', 'shield', 'helmet', 'gauntlet', 'boots', 'chest', 'plate']
        
        if self.type:
            return any(atype in self.type.lower() for atype in armor_types)
        
        return False