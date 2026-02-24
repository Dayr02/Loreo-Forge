"""
Location Model
Represents a story location with descriptions and connections
"""

from typing import Dict, Any, Optional, List
from models.base import BaseModel
from database import db_manager
from models.chapter import Chapter


class Location(BaseModel):
    """
    Location model - represents a place in the story world
    Includes descriptions, history, and connections to other locations
    """
    
    _table_name = 'locations'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        name = self._data.get('name', 'Unnamed')
        loc_type = self._data.get('type', 'location')
        if self.id:
            return f"<Location: {name} ({loc_type}, ID: {self.id})>"
        return f"<Location: {name} ({loc_type}, unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def name(self) -> str:
        """Location name"""
        return self._data.get('name', '')
    
    @name.setter
    def name(self, value: str):
        self._data['name'] = value
        self._modified_fields.add('name')
    
    @property
    def type(self) -> Optional[str]:
        """Location type (city, dungeon, realm, building, etc.)"""
        return self._data.get('type')
    
    @type.setter
    def type(self, value: str):
        self._data['type'] = value
        self._modified_fields.add('type')
    
    @property
    def description(self) -> Optional[str]:
        """Location description"""
        return self._data.get('description')
    
    @description.setter
    def description(self, value: str):
        self._data['description'] = value
        self._modified_fields.add('description')
    
    @property
    def history(self) -> Optional[str]:
        """Location history and background"""
        return self._data.get('history')
    
    @history.setter
    def history(self, value: str):
        self._data['history'] = value
        self._modified_fields.add('history')
    
    @property
    def inhabitants(self) -> Optional[str]:
        """Description of location inhabitants"""
        return self._data.get('inhabitants')
    
    @inhabitants.setter
    def inhabitants(self, value: str):
        self._data['inhabitants'] = value
        self._modified_fields.add('inhabitants')
    
    @property
    def special_features(self) -> Optional[str]:
        """Special features or points of interest"""
        return self._data.get('special_features')
    
    @special_features.setter
    def special_features(self, value: str):
        self._data['special_features'] = value
        self._modified_fields.add('special_features')
    
    @property
    def atmosphere(self) -> Optional[str]:
        """Atmospheric description and mood"""
        return self._data.get('atmosphere')
    
    @atmosphere.setter
    def atmosphere(self, value: str):
        self._data['atmosphere'] = value
        self._modified_fields.add('atmosphere')
    
    @property
    def connected_locations(self) -> List[int]:
        """List of connected location IDs (stored as JSON)"""
        return self._data.get('connected_locations', [])
    
    @connected_locations.setter
    def connected_locations(self, value: List[int]):
        self._data['connected_locations'] = value
        self._modified_fields.add('connected_locations')
    
    @property
    def map_data(self) -> Optional[str]:
        """Map data for future visual mapping"""
        return self._data.get('map_data')
    
    @map_data.setter
    def map_data(self, value: str):
        self._data['map_data'] = value
        self._modified_fields.add('map_data')
    
    # ========================================================================
    # CONNECTIONS
    # ========================================================================
    
    def add_connection(self, location_id: int) -> bool:
        """
        Add connection to another location
        
        Args:
            location_id: ID of location to connect
            
        Returns:
            True if successful
        """
        connections = self.connected_locations.copy()
        
        if location_id not in connections:
            connections.append(location_id)
            self.connected_locations = connections
            return True
        
        return False
    
    def remove_connection(self, location_id: int) -> bool:
        """
        Remove connection to another location
        
        Args:
            location_id: ID of location to disconnect
            
        Returns:
            True if connection was removed
        """
        connections = self.connected_locations.copy()
        
        if location_id in connections:
            connections.remove(location_id)
            self.connected_locations = connections
            return True
        
        return False
    
    def get_connected_locations(self) -> List['Location']:
        """
        Get all connected Location instances
        
        Returns:
            List of connected Location objects
        """
        connected = []
        
        for location_id in self.connected_locations:
            location = Location.get_by_id(self.story_id, location_id)
            if location:
                connected.append(location)
        
        return connected
    
    def get_location_details(self, include_connections: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive location details including connections
        
        Args:
            include_connections: Whether to include connected location details
            
        Returns:
            Dictionary with location and connection data
        """
        return db_manager.get_location_details(
            self.id,
            self.story_id,
            include_connections=include_connections
        )
    
    # ========================================================================
    # SCENE HISTORY
    # ========================================================================
    
    def get_scene_history(self) -> List['Chapter']:
        """
        Get all chapters that take place in this location
        
        Returns:
            List of Chapter instances
        """
        
        try:
            conn = db_manager.get_connection(self.story_id)
            cursor = conn.cursor()
            
            # Search in featured_locations JSON
            query = """
                SELECT * FROM chapters 
                WHERE story_id = ? AND featured_locations LIKE ?
                ORDER BY chapter_number ASC
            """
            
            search_pattern = f'%{self.id}%'
            cursor.execute(query, (self.story_id, search_pattern))
            
            rows = cursor.fetchall()
            chapters = []
            for row in rows:
                chapter_data = dict(row)
                chapter_data = db_manager._deserialize_json_fields('chapters', chapter_data)
                chapters.append(Chapter(self.story_id, **chapter_data))
            
            return chapters
            
        except Exception as e:
            self.logger.error(f"Failed to get scene history: {e}")
            return []
    
    def get_scene_count(self) -> int:
        """
        Get number of chapters set in this location
        
        Returns:
            Chapter count
        """
        return len(self.get_scene_history())
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate location data
        
        Returns:
            True if valid, False otherwise
        """
        if not super().validate():
            return False
        
        # Name is required
        if not self.name or not self.name.strip():
            self.logger.error("Location name is required")
            return False
        
        # Check for duplicate names
        if self._is_new or 'name' in self._modified_fields:
            has_duplicate = db_manager.check_duplicate_names(
                'locations',
                self.name,
                self.story_id,
                exclude_id=self.id
            )
            
            if has_duplicate:
                self.logger.error(f"Location name '{self.name}' already exists")
                return False
        
        return True
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_summary(self) -> str:
        """
        Get a brief location summary
        
        Returns:
            Summary string
        """
        parts = [f"{self.name}"]
        
        if self.type:
            parts.append(f"Type: {self.type}")
        
        if self.description:
            desc = self.description[:100]
            if len(self.description) > 100:
                desc += "..."
            parts.append(desc)
        
        if self.atmosphere:
            parts.append(f"Atmosphere: {self.atmosphere[:50]}")
        
        connection_count = len(self.connected_locations)
        if connection_count > 0:
            parts.append(f"Connected to {connection_count} location(s)")
        
        return " | ".join(parts)
    
    def to_context_string(self) -> str:
        """
        Convert location to string format suitable for AI context
        
        Returns:
            Formatted location description
        """
        lines = [f"**{self.name}**"]
        
        if self.type:
            lines.append(f"Type: {self.type}")
        
        if self.description:
            lines.append(f"Description: {self.description}")
        
        if self.atmosphere:
            lines.append(f"Atmosphere: {self.atmosphere}")
        
        if self.history:
            lines.append(f"History: {self.history}")
        
        if self.inhabitants:
            lines.append(f"Inhabitants: {self.inhabitants}")
        
        if self.special_features:
            lines.append(f"Special Features: {self.special_features}")
        
        if self.connected_locations:
            connected_names = []
            for location_id in self.connected_locations:
                location = Location.get_by_id(self.story_id, location_id)
                if location:
                    connected_names.append(location.name)
            
            if connected_names:
                lines.append(f"Connected to: {', '.join(connected_names)}")
        
        return "\n".join(lines)