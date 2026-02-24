"""
Timeline State Model
Tracks story continuity, character states, and unresolved events across chapters
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from models.base import BaseModel
from database import db_manager


class TimelineState(BaseModel):
    """
    Timeline state model - maintains story continuity
    Tracks character states, conflicts, plot threads, and cause-effect chains
    """
    
    _table_name = 'timeline_states'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        chapter_num = self._data.get('chapter_number', '?')
        if self.id:
            return f"<TimelineState for Chapter {chapter_num} (ID: {self.id})>"
        return f"<TimelineState for Chapter {chapter_num} (unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def chapter_number(self) -> int:
        """Chapter number this timeline state belongs to"""
        return self._data.get('chapter_number', 0)
    
    @chapter_number.setter
    def chapter_number(self, value: int):
        self._data['chapter_number'] = value
        self._modified_fields.add('chapter_number')
    
    @property
    def story_time(self) -> Optional[str]:
        """Current story time (e.g., "Day 5, Evening")"""
        return self._data.get('story_time')
    
    @story_time.setter
    def story_time(self, value: str):
        self._data['story_time'] = value
        self._modified_fields.add('story_time')
    
    @property
    def character_states(self) -> Dict[str, Any]:
        """
        Dictionary tracking character states:
        {
            character_id: {
                'injuries': [],
                'location': '',
                'emotional_state': '',
                'possessions': []
            }
        }
        """
        return self._data.get('character_states', {})
    
    @character_states.setter
    def character_states(self, value: Dict[str, Any]):
        self._data['character_states'] = value
        self._modified_fields.add('character_states')
    
    @property
    def active_conflicts(self) -> List[Dict[str, Any]]:
        """
        List of active conflicts:
        [
            {
                'type': 'character_vs_character',
                'parties': [],
                'description': '',
                'stakes': ''
            }
        ]
        """
        return self._data.get('active_conflicts', [])
    
    @active_conflicts.setter
    def active_conflicts(self, value: List[Dict[str, Any]]):
        self._data['active_conflicts'] = value
        self._modified_fields.add('active_conflicts')
    
    @property
    def plot_threads(self) -> List[Dict[str, Any]]:
        """
        List of ongoing plot threads:
        [
            {
                'thread_id': '',
                'description': '',
                'status': 'active/resolved/suspended',
                'related_characters': []
            }
        ]
        """
        return self._data.get('plot_threads', [])
    
    @plot_threads.setter
    def plot_threads(self, value: List[Dict[str, Any]]):
        self._data['plot_threads'] = value
        self._modified_fields.add('plot_threads')
    
    @property
    def unresolved_events(self) -> List[str]:
        """List of unresolved events that need addressing"""
        return self._data.get('unresolved_events', [])
    
    @unresolved_events.setter
    def unresolved_events(self, value: List[str]):
        self._data['unresolved_events'] = value
        self._modified_fields.add('unresolved_events')
    
    @property
    def world_changes(self) -> List[str]:
        """List of changes to the world state"""
        return self._data.get('world_changes', [])
    
    @world_changes.setter
    def world_changes(self, value: List[str]):
        self._data['world_changes'] = value
        self._modified_fields.add('world_changes')
    
    @property
    def cause_effect_chains(self) -> List[Dict[str, str]]:
        """
        List of cause-effect relationships:
        [
            {
                'cause': 'Character A stole the artifact',
                'effect': 'Guards are searching the city',
                'chapter': 5
            }
        ]
        """
        return self._data.get('cause_effect_chains', [])
    
    @cause_effect_chains.setter
    def cause_effect_chains(self, value: List[Dict[str, str]]):
        self._data['cause_effect_chains'] = value
        self._modified_fields.add('cause_effect_chains')
    
    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================
    
    def update_character_state(
        self,
        character_id: int,
        state_updates: Dict[str, Any]
    ) -> bool:
        """
        Update the state of a specific character
        
        Args:
            character_id: Character ID
            state_updates: Dictionary with state fields to update
            
        Returns:
            True if successful
        """
        states = self.character_states.copy()
        
        if str(character_id) not in states:
            states[str(character_id)] = {}
        
        states[str(character_id)].update(state_updates)
        self.character_states = states
        
        return True
    
    def add_conflict(
        self,
        conflict_type: str,
        parties: List[int],
        description: str,
        stakes: Optional[str] = None
    ) -> bool:
        """
        Add a new active conflict
        
        Args:
            conflict_type: Type of conflict
            parties: List of character IDs involved
            description: Conflict description
            stakes: What's at stake
            
        Returns:
            True if successful
        """
        conflicts = self.active_conflicts.copy()
        
        conflicts.append({
            'type': conflict_type,
            'parties': parties,
            'description': description,
            'stakes': stakes or ''
        })
        
        self.active_conflicts = conflicts
        return True
    
    def resolve_conflict(self, conflict_index: int) -> bool:
        """
        Mark a conflict as resolved
        
        Args:
            conflict_index: Index of conflict in active_conflicts list
            
        Returns:
            True if successful
        """
        conflicts = self.active_conflicts.copy()
        
        if 0 <= conflict_index < len(conflicts):
            conflicts.pop(conflict_index)
            self.active_conflicts = conflicts
            return True
        
        return False
    
    def add_plot_thread(
        self,
        thread_id: str,
        description: str,
        related_characters: Optional[List[int]] = None
    ) -> bool:
        """
        Add a new plot thread
        
        Args:
            thread_id: Unique identifier for thread
            description: Thread description
            related_characters: List of involved character IDs
            
        Returns:
            True if successful
        """
        threads = self.plot_threads.copy()
        
        threads.append({
            'thread_id': thread_id,
            'description': description,
            'status': 'active',
            'related_characters': related_characters or []
        })
        
        self.plot_threads = threads
        return True
    
    def update_plot_thread_status(
        self,
        thread_id: str,
        status: str
    ) -> bool:
        """
        Update plot thread status
        
        Args:
            thread_id: Thread identifier
            status: New status (active/resolved/suspended)
            
        Returns:
            True if found and updated
        """
        threads = self.plot_threads.copy()
        
        for thread in threads:
            if thread.get('thread_id') == thread_id:
                thread['status'] = status
                self.plot_threads = threads
                return True
        
        return False
    
    def add_cause_effect(
        self,
        cause: str,
        effect: str,
        chapter: int
    ) -> bool:
        """
        Add a cause-effect relationship
        
        Args:
            cause: What happened
            effect: The result
            chapter: Chapter where cause occurred
            
        Returns:
            True if successful
        """
        chains = self.cause_effect_chains.copy()
        
        chains.append({
            'cause': cause,
            'effect': effect,
            'chapter': chapter
        })
        
        self.cause_effect_chains = chains
        return True
    
    # ========================================================================
    # CONTINUITY CHECKING
    # ========================================================================
    
    def get_continuity_warnings(self) -> List[str]:
        """
        Generate continuity warnings for unresolved items
        
        Returns:
            List of warning strings
        """
        warnings = []
        
        # Check for injured characters
        for char_id, state in self.character_states.items():
            if state.get('injuries'):
                warnings.append(
                    f"Character {char_id} has unresolved injuries: "
                    f"{', '.join(state['injuries'])}"
                )
        
        # Check for active conflicts
        if self.active_conflicts:
            warnings.append(
                f"{len(self.active_conflicts)} active conflict(s) still unresolved"
            )
        
        # Check for unresolved events
        if self.unresolved_events:
            warnings.append(
                f"Unresolved events: {', '.join(self.unresolved_events[:3])}"
            )
        
        # Check for suspended plot threads
        suspended = [
            t for t in self.plot_threads 
            if t.get('status') == 'suspended'
        ]
        if suspended:
            warnings.append(
                f"{len(suspended)} plot thread(s) suspended and need resolution"
            )
        
        return warnings
    
    def to_ai_context_string(self) -> str:
        """
        Convert timeline state to string for AI context
        
        Returns:
            Formatted string for prompt
        """
        lines = []
        
        if self.story_time:
            lines.append(f"Story Time: {self.story_time}")
        
        if self.character_states:
            lines.append("\nCharacter States:")
            for char_id, state in self.character_states.items():
                lines.append(f"  Character {char_id}:")
                if state.get('location'):
                    lines.append(f"    Location: {state['location']}")
                if state.get('injuries'):
                    lines.append(f"    Injuries: {', '.join(state['injuries'])}")
                if state.get('emotional_state'):
                    lines.append(f"    Emotional: {state['emotional_state']}")
        
        if self.active_conflicts:
            lines.append("\nActive Conflicts:")
            for conflict in self.active_conflicts:
                lines.append(f"  - {conflict.get('description')}")
                if conflict.get('stakes'):
                    lines.append(f"    Stakes: {conflict['stakes']}")
        
        if self.plot_threads:
            active_threads = [
                t for t in self.plot_threads 
                if t.get('status') == 'active'
            ]
            if active_threads:
                lines.append("\nActive Plot Threads:")
                for thread in active_threads:
                    lines.append(f"  - {thread.get('description')}")
        
        if self.unresolved_events:
            lines.append("\nUnresolved Events:")
            for event in self.unresolved_events:
                lines.append(f"  - {event}")
        
        if self.world_changes:
            lines.append("\nWorld Changes:")
            for change in self.world_changes:
                lines.append(f"  - {change}")
        
        return "\n".join(lines) if lines else "No timeline data"
    
    # ========================================================================
    # QUERY METHODS
    # ========================================================================
    
    @classmethod
    def get_previous_state(
        cls,
        story_id: int,
        chapter_number: int
    ) -> Optional['TimelineState']:
        """
        Get timeline state from previous chapter
        
        Args:
            story_id: Story ID
            chapter_number: Current chapter number
            
        Returns:
            Previous timeline state or None
        """
        if chapter_number <= 1:
            return None
        
        try:
            conn = db_manager.get_connection(story_id)
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM timeline_states 
                WHERE story_id = ? AND chapter_number = ?
            """
            
            cursor.execute(query, (story_id, chapter_number - 1))
            row = cursor.fetchone()
            
            if row:
                data = dict(row)
                # Deserialize JSON fields
                data = db_manager._deserialize_json_fields('timeline_states', data)
                return cls(story_id, **data)
            
            return None
            
        except Exception as e:
            from utils.logger import LoggerMixin
            logger = LoggerMixin()
            logger.logger.error(f"Failed to get previous timeline state: {e}")
            return None
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """Validate timeline state data"""
        if not super().validate():
            return False
        
        if self.chapter_number <= 0:
            self.logger.error("Chapter number must be positive")
            return False
        
        return True