"""
Chapter Model
Represents a story chapter with content, metadata, and versioning
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from models.base import BaseModel
from database import db_manager
import re


class Chapter(BaseModel):
    """
    Chapter model - represents a story chapter
    Includes content, metadata, and version history
    """
    
    _table_name = 'chapters'
    
    def __str__(self) -> str:
        """Human-readable representation"""
        chapter_num = self._data.get('chapter_number', '?')
        title = self._data.get('title', 'Untitled')
        if self.id:
            return f"<Chapter {chapter_num}: {title} (ID: {self.id})>"
        return f"<Chapter {chapter_num}: {title} (unsaved)>"
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def chapter_number(self) -> int:
        """Chapter number in sequence"""
        return self._data.get('chapter_number', 0)
    
    @chapter_number.setter
    def chapter_number(self, value: int):
        self._data['chapter_number'] = value
        self._modified_fields.add('chapter_number')
    
    @property
    def title(self) -> Optional[str]:
        """Chapter title"""
        return self._data.get('title')
    
    @title.setter
    def title(self, value: str):
        self._data['title'] = value
        self._modified_fields.add('title')
    
    @property
    def content(self) -> Optional[str]:
        """Chapter content/text"""
        return self._data.get('content')
    
    @content.setter
    def content(self, value: str):
        self._data['content'] = value
        self._modified_fields.add('content')
        # Auto-update word count when content changes
        if value:
            self._data['word_count'] = self._calculate_word_count(value)
            self._modified_fields.add('word_count')
    
    @property
    def word_count(self) -> int:
        """Word count of chapter content"""
        return self._data.get('word_count', 0)
    
    @property
    def summary(self) -> Optional[str]:
        """Chapter summary"""
        return self._data.get('summary')
    
    @summary.setter
    def summary(self, value: str):
        self._data['summary'] = value
        self._modified_fields.add('summary')
    
    @property
    def arc_id(self) -> Optional[int]:
        """Associated arc ID"""
        return self._data.get('arc_id')
    
    @arc_id.setter
    def arc_id(self, value: int):
        self._data['arc_id'] = value
        self._modified_fields.add('arc_id')
    
    @property
    def pov_character_id(self) -> Optional[int]:
        """Point-of-view character ID"""
        return self._data.get('pov_character_id')
    
    @pov_character_id.setter
    def pov_character_id(self, value: int):
        self._data['pov_character_id'] = value
        self._modified_fields.add('pov_character_id')
    
    @property
    def featured_characters(self) -> List[int]:
        """List of featured character IDs (stored as JSON)"""
        return self._data.get('featured_characters', [])
    
    @featured_characters.setter
    def featured_characters(self, value: List[int]):
        self._data['featured_characters'] = value
        self._modified_fields.add('featured_characters')
    
    @property
    def featured_locations(self) -> List[int]:
        """List of featured location IDs (stored as JSON)"""
        return self._data.get('featured_locations', [])
    
    @featured_locations.setter
    def featured_locations(self, value: List[int]):
        self._data['featured_locations'] = value
        self._modified_fields.add('featured_locations')
    
    @property
    def mood(self) -> Optional[str]:
        """Chapter mood/tone"""
        return self._data.get('mood')
    
    @mood.setter
    def mood(self, value: str):
        self._data['mood'] = value
        self._modified_fields.add('mood')
    
    @property
    def status(self) -> str:
        """Chapter status (draft, review, final)"""
        return self._data.get('status', 'draft')
    
    @status.setter
    def status(self, value: str):
        self._data['status'] = value
        self._modified_fields.add('status')
    
    @property
    def model_used(self) -> Optional[str]:
        """AI model used for generation"""
        return self._data.get('model_used')
    
    @property
    def edited(self) -> bool:
        """Whether chapter has been manually edited"""
        return bool(self._data.get('edited', 0))
    
    @edited.setter
    def edited(self, value: bool):
        self._data['edited'] = 1 if value else 0
        self._modified_fields.add('edited')
    
    # ========================================================================
    # SELECTIVE EDITING - APPROVED SECTIONS
    # ========================================================================

    @property
    def approved_sections(self) -> List[Dict[str, Any]]:
        """
        List of approved text sections that should not be modified
        [
            {'start': 0, 'end': 500, 'text': '...', 'approved_at': '...'},
            {'start': 1000, 'end': 1500, 'text': '...', 'approved_at': '...'}
        ]
        """
        return self._data.get('approved_sections', [])

    @approved_sections.setter
    def approved_sections(self, value: List[Dict[str, Any]]):
        self._data['approved_sections'] = value
        self._modified_fields.add('approved_sections')

    def approve_section(self, start_index: int, end_index: int) -> bool:
        """
        Mark a text section as approved (cannot be AI-modified)

        Args:
            start_index: Start character index
            end_index: End character index

        Returns:
            True if approved
        """
        if not self.content:
            self.logger.error("Cannot approve section - no content")
            return False

        if start_index < 0 or end_index > len(self.content) or start_index >= end_index:
            self.logger.error(f"Invalid section range: {start_index}-{end_index}")
            return False

        sections = self.approved_sections.copy()

        sections.append({
            'start': start_index,
            'end': end_index,
            'text': self.content[start_index:end_index],
            'approved_at': datetime.now().isoformat()
        })

        # Merge overlapping sections
        sections = self._merge_sections(sections)
        self.approved_sections = sections

        self.logger.info(f"Approved section {start_index}-{end_index}")
        return True

    def unapprove_section(self, section_index: int) -> bool:
        """
        Remove approval from a section

        Args:
            section_index: Index in approved_sections list

        Returns:
            True if successful
        """
        sections = self.approved_sections.copy()

        if 0 <= section_index < len(sections):
            sections.pop(section_index)
            self.approved_sections = sections
            self.logger.info(f"Unapproved section at index {section_index}")
            return True

        return False

    def is_section_approved(self, start_index: int, end_index: int) -> bool:
        """
        Check if a text section is approved

        Args:
            start_index: Start character index
            end_index: End character index

        Returns:
            True if any part is approved
        """
        for section in self.approved_sections:
            # Check for overlap
            if not (end_index <= section['start'] or start_index >= section['end']):
                return True

        return False

    def get_editable_ranges(self) -> List[Tuple[int, int]]:
        """
        Get list of editable (non-approved) text ranges

        Returns:
            List of (start, end) tuples
        """
        if not self.content:
            return []

        if not self.approved_sections:
            return [(0, len(self.content))]

        editable = []
        last_end = 0

        # Sort sections by start position
        sorted_sections = sorted(self.approved_sections, key=lambda x: x['start'])

        for section in sorted_sections:
            if last_end < section['start']:
                editable.append((last_end, section['start']))
            last_end = section['end']

        # Add final section if exists
        if last_end < len(self.content):
            editable.append((last_end, len(self.content)))

        return editable

    @staticmethod
    def _merge_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping approved sections"""
        if not sections:
            return []

        sorted_sections = sorted(sections, key=lambda x: x['start'])
        merged = [sorted_sections[0]]

        for section in sorted_sections[1:]:
            last = merged[-1]

            if section['start'] <= last['end']:
                # Overlapping - merge
                last['end'] = max(last['end'], section['end'])
                # Extend text if needed
                if section['end'] > last['end']:
                    last['text'] = last['text'] + section['text'][len(last['text']):]
            else:
                merged.append(section)

        return merged

    # ========================================================================
    # NAVIGATION
    # ========================================================================
    
    def get_previous_chapter(self) -> Optional['Chapter']:
        """
        Get the previous chapter in sequence
        
        Returns:
            Previous Chapter instance or None
        """
        if self.chapter_number <= 1:
            return None
        
        chapter_data = db_manager.get_chapter_by_number(
            self.story_id,
            self.chapter_number - 1
        )
        
        if chapter_data:
            return Chapter(self.story_id, **chapter_data)
        
        return None
    
    def get_next_chapter(self) -> Optional['Chapter']:
        """
        Get the next chapter in sequence
        
        Returns:
            Next Chapter instance or None
        """
        chapter_data = db_manager.get_chapter_by_number(
            self.story_id,
            self.chapter_number + 1
        )
        
        if chapter_data:
            return Chapter(self.story_id, **chapter_data)
        
        return None
    
    # ========================================================================
    # VERSIONING
    # ========================================================================
    
    def create_version(self, notes: Optional[str] = None) -> bool:
        """
        Create a version snapshot of current chapter content
        
        Args:
            notes: Optional notes about this version
            
        Returns:
            True if successful
        """
        if self._is_new:
            self.logger.warning("Cannot create version for unsaved chapter")
            return False
        
        try:
            # Get current version count
            versions = self.get_versions()
            version_number = len(versions) + 1
            
            # Create version record
            version_data = {
                'chapter_id': self.id,
                'version_number': version_number,
                'content': self.content,
                'notes': notes or f'Version {version_number}'
            }
            
            version_id = db_manager.create_record(
                self.story_id,
                'chapter_versions',
                version_data
            )
            
            if version_id:
                self.logger.info(f"Created version {version_number} for chapter {self.id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to create chapter version: {e}")
            return False
    
    def get_versions(self) -> List[Dict[str, Any]]:
        """
        Retrieve all versions of this chapter
        
        Returns:
            List of version dictionaries
        """
        if self._is_new:
            return []
        
        return db_manager.get_all_records(
            self.story_id,
            'chapter_versions',
            filters={'chapter_id': self.id},
            sort_by='version_number',
            order='DESC'
        )
    
    def restore_version(self, version_number: int) -> bool:
        """
        Restore chapter content from a specific version
        
        Args:
            version_number: Version number to restore
            
        Returns:
            True if successful
        """
        try:
            versions = self.get_versions()
            
            for version in versions:
                if version['version_number'] == version_number:
                    # Save current as new version before restoring
                    self.create_version(notes=f'Before restoring to version {version_number}')
                    
                    # Restore content
                    self.content = version['content']
                    self.edited = True
                    
                    return self.save()
            
            self.logger.warning(f"Version {version_number} not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to restore version: {e}")
            return False
    
    # ========================================================================
    # METRICS & ANALYSIS
    # ========================================================================
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate various metrics for the chapter
        
        Returns:
            Dictionary containing metrics
        """
        metrics = {
            'word_count': self.word_count,
            'character_count': len(self.content or ''),
            'paragraph_count': 0,
            'dialogue_lines': 0,
            'average_sentence_length': 0
        }
        
        if not self.content:
            return metrics
        
        # Count paragraphs
        paragraphs = [p.strip() for p in self.content.split('\n\n') if p.strip()]
        metrics['paragraph_count'] = len(paragraphs)
        
        # Count dialogue lines (simple heuristic: lines with quotes)
        metrics['dialogue_lines'] = self.content.count('"') // 2
        
        # Average sentence length
        sentences = re.split(r'[.!?]+', self.content)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            total_words = sum(len(s.split()) for s in sentences)
            metrics['average_sentence_length'] = total_words / len(sentences)
        
        return metrics
    
    def extract_plot_points(self) -> List[str]:
        """
        Extract important plot points from chapter content
        (Simple implementation - can be enhanced with AI in future)
        
        Returns:
            List of plot point strings
        """
        if not self._data.get('plot_points'):
            return []
        
        # If plot_points is stored, split by newline or comma
        plot_points = self._data.get('plot_points', '')
        
        if '\n' in plot_points:
            return [p.strip() for p in plot_points.split('\n') if p.strip()]
        else:
            return [p.strip() for p in plot_points.split(',') if p.strip()]
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate chapter data
        
        Returns:
            True if valid, False otherwise
        """
        if not super().validate():
            return False
        
        # Chapter number is required
        if self.chapter_number <= 0:
            self.logger.error("Chapter number must be positive")
            return False
        
        # Check for duplicate chapter numbers
        if self._is_new or 'chapter_number' in self._modified_fields:
            existing = db_manager.get_chapter_by_number(
                self.story_id,
                self.chapter_number
            )
            
            if existing and existing['id'] != self.id:
                self.logger.error(f"Chapter {self.chapter_number} already exists")
                return False
        
        return True
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    @staticmethod
    def _calculate_word_count(text: str) -> int:
        """
        Calculate word count of text
        
        Args:
            text: Text to count
            
        Returns:
            Word count
        """
        if not text:
            return 0
        
        # Remove extra whitespace and split
        words = text.split()
        return len(words)
    
    def get_excerpt(self, max_words: int = 50) -> str:
        """
        Get an excerpt from the chapter content
        
        Args:
            max_words: Maximum words in excerpt
            
        Returns:
            Excerpt string
        """
        if not self.content:
            return ""
        
        words = self.content.split()
        
        if len(words) <= max_words:
            return self.content
        
        excerpt = ' '.join(words[:max_words])
        return excerpt + "..."
    
    def get_summary_or_excerpt(self, excerpt_words: int = 100) -> str:
        """
        Get summary if available, otherwise return excerpt
        
        Args:
            excerpt_words: Words in excerpt if no summary
            
        Returns:
            Summary or excerpt
        """
        if self.summary:
            return self.summary
        
        return self.get_excerpt(excerpt_words)
    
    def to_export_format(self) -> Dict[str, Any]:
        """
        Prepare chapter data for export
        
        Returns:
            Dictionary formatted for export
        """
        return {
            'chapter_number': self.chapter_number,
            'title': self.title or f'Chapter {self.chapter_number}',
            'content': self.content or '',
            'word_count': self.word_count,
            'summary': self.summary,
            'mood': self.mood
        }