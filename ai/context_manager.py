"""
Context Manager for AI Generation
Intelligently gathers and organizes story context for AI prompts
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from database import db_manager
from models import Story, Character, Location, Chapter, Arc
from config.settings import settings
from utils.logger import LoggerMixin


class ContextManager(LoggerMixin):
    """
    Manages context gathering and optimization for AI generation
    Integrates with database to build comprehensive story context
    """
    
    def __init__(self):
        """Initialize context manager"""
        self.logger.info("ContextManager initialized")
    
    # ========================================================================
    # CONTEXT GATHERING
    # ========================================================================
    
    def build_chapter_context(
        self,
        story_id: int,
        chapter_number: int,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build complete context for chapter generation
        
        Args:
            story_id: Story identifier
            chapter_number: Chapter number being generated
            custom_settings: Override default context settings
            
        Returns:
            Comprehensive context dictionary
        """
        self.logger.info(f"Building context for story {story_id}, chapter {chapter_number}")
        
        settings_dict = custom_settings or {}
        
        context = {
            'story_metadata': self._get_story_context(story_id),
            'current_arc': self._get_arc_context(story_id),
            'recent_chapters': self._get_recent_chapters_context(
                story_id, 
                chapter_number,
                count=settings_dict.get('recent_chapters_count', 3)
            ),
            'active_characters': self._get_character_context(
                story_id,
                chapter_number,
                limit=settings_dict.get('max_characters', 10)
            ),
            'current_location': None,  # Will be set if specified
            'relevant_lore': self._get_lore_context(
                story_id,
                relevance_threshold=settings_dict.get('lore_threshold', 7)
            ),
            'power_systems': self._get_power_system_context(story_id),
            'items': self._get_items_context(story_id),
            'previous_chapter_ending': None,
            'context_stats': {}
        }
        
        # Get previous chapter ending if exists
        if chapter_number > 1:
            prev_chapter = Chapter.get_by_id(story_id, chapter_number - 1)
            if prev_chapter and prev_chapter.content:
                # Get last 500 characters
                context['previous_chapter_ending'] = prev_chapter.content[-500:]
        
        # Calculate context statistics
        context['context_stats'] = self._calculate_context_stats(context)
        
        self.logger.info(
            f"Context built: {context['context_stats']['total_items']} items, "
            f"~{context['context_stats']['estimated_tokens']} tokens"
        )
        
        return context
    
    def _get_story_context(self, story_id: int) -> Dict[str, Any]:
        """Get story metadata and overview"""
        story_data = db_manager.get_story_metadata(story_id)
        
        if story_data:
            return {
                'title': story_data.get('title', 'Untitled'),
                'genre': story_data.get('genre', 'Fiction'),
                'setting': story_data.get('setting', ''),
                'tone': story_data.get('tone', ''),
                'synopsis': story_data.get('synopsis', ''),
                'total_chapters': story_data.get('total_chapters', 0),
                'total_word_count': story_data.get('total_word_count', 0)
            }
        
        return {}
    
    def _get_arc_context(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Get current story arc information"""
        arc_data = db_manager.get_active_arc(story_id)
        
        if arc_data:
            return {
                'arc_number': arc_data.get('arc_number'),
                'title': arc_data.get('title'),
                'description': arc_data.get('description'),
                'themes': arc_data.get('themes'),
                'status': arc_data.get('status')
            }
        
        return None
    
    def _get_recent_chapters_context(
        self,
        story_id: int,
        current_chapter: int,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """Get recent chapters for context"""
        if current_chapter <= 1:
            return []
        
        start = max(1, current_chapter - count)
        end = current_chapter - 1
        
        chapters = db_manager.get_chapters_range(story_id, start, end)
        
        return [
            {
                'chapter_number': ch.get('chapter_number'),
                'title': ch.get('title'),
                'summary': ch.get('summary') or self._extract_summary(ch.get('content', '')),
                'plot_points': ch.get('plot_points'),
                'word_count': ch.get('word_count', 0)
            }
            for ch in chapters
        ]
    
    def _get_character_context(
        self,
        story_id: int,
        chapter_number: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get active character information"""
        characters = db_manager.get_all_characters(story_id)
        
        # Score characters by relevance
        scored_characters = []
        for char in characters:
            score = self._calculate_character_relevance(char, chapter_number)
            scored_characters.append((score, char))
        
        # Sort by score and take top characters
        scored_characters.sort(key=lambda x: x[0], reverse=True)
        top_characters = [char for score, char in scored_characters[:limit]]
        
        return [
            {
                'name': char.get('name'),
                'role': char.get('role'),
                'personality': char.get('personality'),
                'background': char.get('background', '')[:200],  # Truncate
                'goals': char.get('goals'),
                'abilities': char.get('abilities'),
                'status': char.get('status'),
                'importance_weight': char.get('importance_weight', 0.5)
            }
            for char in top_characters
        ]
    
    def _get_lore_context(
        self,
        story_id: int,
        relevance_threshold: int = 7
    ) -> List[Dict[str, Any]]:
        """Get relevant lore entries"""
        lore_entries = db_manager.get_all_records(
            story_id,
            'lore_entries',
            sort_by='importance',
            order='DESC',
            limit=10
        )
        
        # Filter by importance threshold
        relevant_lore = [
            entry for entry in lore_entries
            if entry.get('importance', 5) >= relevance_threshold
        ]
        
        return [
            {
                'title': entry.get('title'),
                'category': entry.get('category'),
                'content': entry.get('content', '')[:300],  # Truncate
                'importance': entry.get('importance')
            }
            for entry in relevant_lore
        ]
    
    def _get_power_system_context(self, story_id: int) -> List[Dict[str, Any]]:
        """Get power system information"""
        power_systems = db_manager.get_all_records(
            story_id,
            'power_systems'
        )
        
        return [
            {
                'system_name': ps.get('system_name'),
                'description': ps.get('description', '')[:200],
                'rules': ps.get('rules'),
                'limitations': ps.get('limitations')
            }
            for ps in power_systems
        ]
    
    def _get_items_context(self, story_id: int) -> List[Dict[str, Any]]:
        """Get important items and artifacts"""
        items = db_manager.get_all_records(
            story_id,
            'items',
            sort_by='name',
            order='ASC',
            limit=15
        )

        return [
            {
                'name': item.get('name'),
                'type': item.get('type'),
                'rarity': item.get('rarity'),
                'description': item.get('description', '')[:200],
                'properties': item.get('properties'),
                'powers': item.get('powers'),
                'current_owner': item.get('current_owner'),
                'current_location': item.get('current_location')
            }
            for item in items
        ]
    
    def get_character_context(
        self,
        character_ids: List[int],
        story_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get detailed context for specific characters
        
        Args:
            character_ids: List of character IDs
            story_id: Story identifier
            
        Returns:
            List of character context dictionaries
        """
        characters = []
        
        for char_id in character_ids:
            char = Character.get_by_id(story_id, char_id)
            if char:
                characters.append({
                    'name': char.name,
                    'role': char.role,
                    'appearance': char.appearance,
                    'personality': char.personality,
                    'background': char.background,
                    'goals': char.goals,
                    'fears': char.fears,
                    'abilities': char.abilities,
                    'relationships': char.relationships
                })
        
        return characters
    
    def get_location_context(
        self,
        location_ids: List[int],
        story_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get detailed context for specific locations
        
        Args:
            location_ids: List of location IDs
            story_id: Story identifier
            
        Returns:
            List of location context dictionaries
        """
        locations = []
        
        for loc_id in location_ids:
            location = Location.get_by_id(story_id, loc_id)
            if location:
                locations.append({
                    'name': location.name,
                    'type': location.type,
                    'description': location.description,
                    'atmosphere': location.atmosphere,
                    'history': location.history,
                    'special_features': location.special_features
                })
        
        return locations
    
    def get_recent_plot_context(
        self,
        story_id: int,
        chapter_count: int = 5
    ) -> str:
        """
        Get summary of recent plot events
        
        Args:
            story_id: Story identifier
            chapter_count: Number of recent chapters
            
        Returns:
            Formatted plot summary
        """
        recent_chapters = db_manager.get_recent_chapters(story_id, chapter_count)
        
        if not recent_chapters:
            return "No recent chapters available."
        
        plot_summary = []
        
        for chapter in reversed(recent_chapters):  # Chronological order
            summary = chapter.get('summary') or self._extract_summary(
                chapter.get('content', '')
            )
            plot_summary.append(
                f"Chapter {chapter.get('chapter_number')}: {summary}"
            )
        
        return '\n'.join(plot_summary)
    
    # ========================================================================
    # USER-DRIVEN CONTEXT SELECTION
    # ========================================================================

    def build_selective_context(
        self,
        story_id: int,
        chapter_number: int,
        selected_ids: Dict[str, List[int]]
    ) -> Dict[str, Any]:
        """
        PHASE 1: Build context from user-selected entities only

        Args:
            story_id: Story identifier
            chapter_number: Chapter number
            selected_ids: Dict mapping entity type to list of selected IDs
                {
                    'characters': [1, 2, 3],
                    'locations': [1],
                    'lore': [2, 5],
                    'creatures': [1],
                    'organizations': [1],
                    'power_systems': [1]
                }

        Returns:
            Context dictionary with only selected entities
        """
        self.logger.info(f"Building selective context for chapter {chapter_number}")

        context = {
            'story_metadata': self._get_story_context(story_id),
            'current_arc': self._get_arc_context(story_id),
            'selected_characters': [],
            'selected_locations': [],
            'selected_lore': [],
            'selected_creatures': [],
            'selected_organizations': [],
            'selected_power_systems': [],
            'selected_items': [],
            'previous_chapter_ending': None,
            'context_stats': {}
        }

        # Get only selected entities
        if selected_ids.get('characters'):
            context['selected_characters'] = self.get_character_context(
                selected_ids['characters'],
                story_id
            )

        if selected_ids.get('locations'):
            context['selected_locations'] = self.get_location_context(
                selected_ids['locations'],
                story_id
            )

        if selected_ids.get('lore'):
            context['selected_lore'] = self._get_selected_lore(
                selected_ids['lore'],
                story_id
            )

        if selected_ids.get('creatures'):
            context['selected_creatures'] = self._get_selected_creatures(
                selected_ids['creatures'],
                story_id
            )

        if selected_ids.get('organizations'):
            context['selected_organizations'] = self._get_selected_organizations(
                selected_ids['organizations'],
                story_id
            )

        if selected_ids.get('power_systems'):
            context['selected_power_systems'] = self._get_selected_power_systems(
                selected_ids['power_systems'],
                story_id
            )

        if selected_ids.get('items'):
            context['selected_items'] = self._get_selected_items(
                selected_ids['items'],
                story_id
            )

        # Previous chapter ending
        if chapter_number > 1:
            from models.chapter import Chapter
            prev_chapter = Chapter.get_by_id(story_id, chapter_number - 1)
            if prev_chapter and prev_chapter.content:
                context['previous_chapter_ending'] = prev_chapter.content[-500:]

        # Calculate stats
        context['context_stats'] = self._calculate_context_stats(context)

        self.logger.info(
            f"Selective context built: {context['context_stats']['total_items']} items"
        )

        return context

    def build_chapter_context_with_timeline(
        self,
        story_id: int,
        chapter_number: int,
        selected_context: Optional[Dict[str, List[int]]] = None
    ) -> Dict[str, Any]:
        """
        Build context INCLUDING timeline state
        
        Args:
            story_id: Story identifier
            chapter_number: Chapter number
            selected_context: Optional manual context selection
            
        Returns:
            Context with timeline continuity data
        """
        from models.timeline_state import TimelineState
        
        # Get base context (selective or automatic)
        if selected_context:
            context = self.build_selective_context(
                story_id,
                chapter_number,
                selected_context
            )
        else:
            context = self.build_chapter_context(
                story_id,
                chapter_number
            )
        
        # Add timeline state from previous chapter
        timeline = TimelineState.get_previous_state(story_id, chapter_number)
        if timeline:
            context['timeline_state'] = timeline.to_ai_context_string()
            context['continuity_warnings'] = timeline.get_continuity_warnings()
        else:
            context['timeline_state'] = None
            context['continuity_warnings'] = []
        
        self.logger.info(
            f"Built context with timeline for chapter {chapter_number}: "
            f"{len(context.get('continuity_warnings', []))} warnings"
        )
        
        return context
    
    def _get_selected_lore(
        self,
        lore_ids: List[int],
        story_id: int
    ) -> List[Dict[str, Any]]:
        """Get specific lore entries by IDs"""
        lore_entries = []

        for lore_id in lore_ids:
            lore = db_manager.get_entity('lore_entries', lore_id, story_id)
            if lore:
                lore_entries.append({
                    'title': lore.get('title'),
                    'category': lore.get('category'),
                    'content': lore.get('content', '')[:300],
                    'importance': lore.get('importance')
                })

        return lore_entries


    def _get_selected_creatures(
        self,
        creature_ids: List[int],
        story_id: int
    ) -> List[Dict[str, Any]]:
        """Get specific creatures by IDs"""
        from models.creature import Creature

        creatures = []
        for creature_id in creature_ids:
            creature = Creature.get_by_id(story_id, creature_id)
            if creature:
                creatures.append({
                    'name': creature.name,
                    'category': creature.category,
                    'appearance': creature.appearance,
                    'behavior': creature.behavior,
                    'abilities': creature.abilities,
                    'weaknesses': creature.weaknesses
                })

        return creatures


    def _get_selected_organizations(
        self,
        org_ids: List[int],
        story_id: int
    ) -> List[Dict[str, Any]]:
        """Get specific organizations by IDs"""
        organizations = []

        for org_id in org_ids:
            org = db_manager.get_entity('organizations', org_id, story_id)
            if org:
                organizations.append({
                    'name': org.get('name'),
                    'type': org.get('type'),
                    'description': org.get('description', '')[:200],
                    'goals': org.get('goals'),
                    'leadership': org.get('leadership')
                })

        return organizations


    def _get_selected_power_systems(
        self,
        power_ids: List[int],
        story_id: int
    ) -> List[Dict[str, Any]]:
        """Get specific power systems by IDs"""
        power_systems = []

        for power_id in power_ids:
            power = db_manager.get_entity('power_systems', power_id, story_id)
            if power:
                power_systems.append({
                    'name': power.get('name'),
                    'system_name': power.get('system_name'),
                    'description': power.get('description', '')[:200],
                    'rules': power.get('rules'),
                    'limitations': power.get('limitations')
                })

        return power_systems

    def _get_selected_items(
        self,
        item_ids: List[int],
        story_id: int
    ) -> List[Dict[str, Any]]:
        """Get specific items by IDs"""
        items = []
    
        for item_id in item_ids:
            item = db_manager.get_entity('items', item_id, story_id)
            if item:
                items.append({
                    'name': item.get('name'),
                    'type': item.get('type'),
                    'rarity': item.get('rarity'),
                    'description': item.get('description', '')[:200],
                    'properties': item.get('properties'),
                    'powers': item.get('powers'),
                    'current_owner': item.get('current_owner'),
                    'current_location': item.get('current_location')
                })
    
        return items

    def get_context_summary(
        self,
        story_id: int,
        chapter_number: int,
        selected_ids: Optional[Dict[str, List[int]]] = None
    ) -> Dict[str, Any]:
        """
        PHASE 1: Get context summary for preview

        Returns entity counts and token estimates without building full context
        """
        if selected_ids:
            # Count selected entities
            summary = {
                'mode': 'selective',
                'characters': len(selected_ids.get('characters', [])),
                'locations': len(selected_ids.get('locations', [])),
                'lore': len(selected_ids.get('lore', [])),
                'creatures': len(selected_ids.get('creatures', [])),
                'organizations': len(selected_ids.get('organizations', [])),
                'power_systems': len(selected_ids.get('power_systems', [])),
                'items': len(selected_ids.get('items', []))
            }
        else:
            # Count all available entities (auto mode)
            summary = {
                'mode': 'automatic',
                'characters': db_manager.count_entities('characters', story_id),
                'locations': db_manager.count_entities('locations', story_id),
                'lore': db_manager.count_entities('lore_entries', story_id),
                'creatures': db_manager.count_entities('bestiary', story_id),
                'organizations': db_manager.count_entities('organizations', story_id),
                'power_systems': db_manager.count_entities('power_systems', story_id),
                'items': db_manager.count_entities('items', story_id)
            }

        # Calculate totals
        summary['total_entities'] = sum(v for k, v in summary.items() if k != 'mode')
        summary['estimated_tokens'] = summary['total_entities'] * 100  # Rough estimate

        return summary

    # ========================================================================
    # CONTEXT PRIORITIZATION
    # ========================================================================
    
    def calculate_relevance_scores(
        self,
        context_items: List[Dict[str, Any]],
        current_chapter: int
    ) -> List[float]:
        """
        Calculate relevance score for each context item
        
        Args:
            context_items: List of context items
            current_chapter: Current chapter number
            
        Returns:
            List of relevance scores (0.0-1.0)
        """
        scores = []
        
        for item in context_items:
            score = 0.5  # Base score
            
            # Importance weight if available
            if 'importance_weight' in item:
                score = item['importance_weight']
            
            # Boost for recent appearances
            if 'first_appearance_chapter' in item:
                chapters_ago = current_chapter - item['first_appearance_chapter']
                recency_factor = max(0, 1.0 - (chapters_ago / 100))
                score = score * 0.7 + recency_factor * 0.3
            
            scores.append(min(1.0, max(0.0, score)))
        
        return scores
    
    def prioritize_by_recency(
        self,
        items: List[Dict[str, Any]],
        decay_factor: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Weight recent content higher
        
        Args:
            items: List of items (must have ordering)
            decay_factor: Decay multiplier per item (0.0-1.0)
            
        Returns:
            Reweighted items
        """
        weighted_items = []
        
        for i, item in enumerate(items):
            weight = decay_factor ** i
            weighted_item = item.copy()
            weighted_item['_recency_weight'] = weight
            weighted_items.append(weighted_item)
        
        return weighted_items
    
    def prioritize_by_importance(
        self,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sort items by importance weight
        
        Args:
            items: List of items with importance_weight
            
        Returns:
            Sorted items
        """
        return sorted(
            items,
            key=lambda x: x.get('importance_weight', 0.5),
            reverse=True
        )
    
    def filter_by_relevance(
        self,
        items: List[Dict[str, Any]],
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Remove low-relevance items
        
        Args:
            items: Items with relevance scores
            threshold: Minimum relevance to keep
            
        Returns:
            Filtered items
        """
        return [
            item for item in items
            if item.get('importance_weight', 0.5) >= threshold
        ]
    
    # ========================================================================
    # CONTEXT OPTIMIZATION
    # ========================================================================
    
    def compress_context(
        self,
        context: Dict[str, Any],
        target_size: int = 3000
    ) -> Dict[str, Any]:
        """
        Reduce context to fit size limits
        
        Args:
            context: Full context dictionary
            target_size: Target character count
            
        Returns:
            Compressed context
        """
        current_size = self._estimate_context_size(context)
        
        if current_size <= target_size:
            return context
        
        self.logger.info(f"Compressing context from ~{current_size} to ~{target_size} chars")
        
        compressed = context.copy()
        
        # Compress in order of priority (least important first)
        compression_order = [
            ('recent_chapters', self._compress_chapters),
            ('active_characters', self._compress_characters),
            ('relevant_lore', self._compress_lore)
        ]
        
        for key, compress_func in compression_order:
            if current_size <= target_size:
                break
            
            if key in compressed and compressed[key]:
                compressed[key] = compress_func(compressed[key], target_size - current_size)
                current_size = self._estimate_context_size(compressed)
        
        return compressed
    
    def _compress_chapters(
        self,
        chapters: List[Dict[str, Any]],
        space_available: int
    ) -> List[Dict[str, Any]]:
        """Compress chapter summaries"""
        compressed = []
        
        for chapter in chapters:
            compressed_chapter = chapter.copy()
            if 'summary' in compressed_chapter:
                summary = compressed_chapter['summary']
                if len(summary) > 100:
                    compressed_chapter['summary'] = summary[:100] + '...'
            compressed.append(compressed_chapter)
        
        return compressed
    
    def _compress_characters(
        self,
        characters: List[Dict[str, Any]],
        space_available: int
    ) -> List[Dict[str, Any]]:
        """Compress character details"""
        # Take only most important characters if needed
        if len(characters) > 5:
            return sorted(
                characters,
                key=lambda x: x.get('importance_weight', 0.5),
                reverse=True
            )[:5]
        
        return characters
    
    def _compress_lore(
        self,
        lore: List[Dict[str, Any]],
        space_available: int
    ) -> List[Dict[str, Any]]:
        """Compress lore entries"""
        # Keep only highest importance lore
        return sorted(
            lore,
            key=lambda x: x.get('importance', 5),
            reverse=True
        )[:5]
    
    def summarize_old_chapters(
        self,
        chapters: List[Dict[str, Any]]
    ) -> str:
        """
        Condense older chapter information
        
        Args:
            chapters: List of chapter dictionaries
            
        Returns:
            Summarized string
        """
        if not chapters:
            return ""
        
        summaries = []
        for chapter in chapters:
            summary = chapter.get('summary') or "No summary available."
            summaries.append(
                f"Ch{chapter.get('chapter_number', '?')}: {summary[:100]}"
            )
        
        return ' | '.join(summaries)
    
    def extract_key_facts(self, text: str, max_facts: int = 5) -> List[str]:
        """
        Extract essential information from text
        
        Args:
            text: Text to extract from
            max_facts: Maximum facts to extract
            
        Returns:
            List of key facts
        """
        # Simple sentence-based extraction
        import re
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Take first N sentences as key facts
        return sentences[:max_facts]
    
    def deduplicate_information(
        self,
        context_sections: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Remove redundant data from context
        
        Args:
            context_sections: Context dictionary
            
        Returns:
            Deduplicated context
        """
        # Simple deduplication: remove None/empty values
        deduplicated = {}
        
        for key, value in context_sections.items():
            if value is not None:
                if isinstance(value, list) and len(value) == 0:
                    continue
                if isinstance(value, str) and not value.strip():
                    continue
                deduplicated[key] = value
        
        return deduplicated
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_character_relevance(
        self,
        character: Dict[str, Any],
        chapter_number: int
    ) -> float:
        """Calculate how relevant a character is for current chapter"""
        score = character.get('importance_weight', 0.5)
        
        # Boost for protagonists
        if character.get('role') == 'protagonist':
            score += 0.3
        
        # Boost for recent appearances
        first_appearance = character.get('first_appearance_chapter', 1)
        if first_appearance and first_appearance < chapter_number:
            chapters_ago = chapter_number - first_appearance
            recency_boost = max(0, 0.2 - (chapters_ago * 0.01))
            score += recency_boost
        
        return min(1.0, score)
    
    def _extract_summary(self, content: str, max_length: int = 200) -> str:
        """Extract a summary from chapter content"""
        if not content or len(content) <= max_length:
            return content
        
        # Take first few sentences
        import re
        sentences = re.split(r'[.!?]+', content)
        summary = ""
        
        for sentence in sentences:
            if len(summary) + len(sentence) < max_length:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip()
    
    def _calculate_context_stats(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics about context"""
        total_items = 0
        estimated_chars = 0
        
        for key, value in context.items():
            if key == 'context_stats':
                continue
            
            if isinstance(value, list):
                total_items += len(value)
                estimated_chars += sum(len(str(item)) for item in value)
            elif isinstance(value, dict):
                total_items += 1
                estimated_chars += len(str(value))
            elif value:
                estimated_chars += len(str(value))
        
        return {
            'total_items': total_items,
            'estimated_chars': estimated_chars,
            'estimated_tokens': estimated_chars // 4  # Rough estimate
        }
    
    def _estimate_context_size(self, context: Dict[str, Any]) -> int:
        """Estimate total character count of context"""
        return sum(
            len(str(value)) for value in context.values()
            if value is not None
        )


# Global context manager instance
context_manager = ContextManager()