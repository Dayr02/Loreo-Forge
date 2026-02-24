"""
Prompt Template System for Loreo Forge
Constructs dynamic, context-aware prompts from templates
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from jinja2.exceptions import TemplateSyntaxError

from config.settings import settings
from ai.exceptions import InvalidPromptError
from utils.logger import LoggerMixin


class PromptBuilder(LoggerMixin):
    """
    Builds dynamic prompts from templates with context data
    Supports Jinja2 templating with custom filters and functions
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize prompt builder
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False
        )
        
        # Register custom filters
        self._register_filters()
        
        # In-memory template registry
        self._template_registry: Dict[str, str] = {}
        
        self.logger.info(f"PromptBuilder initialized with templates from {self.templates_dir}")
    
    def _register_filters(self):
        """Register custom Jinja2 filters"""
        
        def truncate_words(text: str, max_words: int) -> str:
            """Truncate text to max words"""
            words = text.split()
            if len(words) <= max_words:
                return text
            return ' '.join(words[:max_words]) + '...'
        
        def summarize(text: str, max_chars: int = 200) -> str:
            """Create a summary of text"""
            if len(text) <= max_chars:
                return text
            return text[:max_chars].rsplit(' ', 1)[0] + '...'
        
        def bullet_list(items: List[str]) -> str:
            """Format list as bullet points"""
            return '\n'.join(f"- {item}" for item in items)
        
        def numbered_list(items: List[str]) -> str:
            """Format list as numbered points"""
            return '\n'.join(f"{i+1}. {item}" for i, item in enumerate(items))
        
        # Register filters
        self.env.filters['truncate_words'] = truncate_words
        self.env.filters['summarize'] = summarize
        self.env.filters['bullet_list'] = bullet_list
        self.env.filters['numbered_list'] = numbered_list
    
    # ========================================================================
    # TEMPLATE MANAGEMENT
    # ========================================================================
    
    def load_template(self, template_name: str) -> Template:
        """
        Load template from file
        
        Args:
            template_name: Name of template file (without .txt extension)
            
        Returns:
            Jinja2 Template object
            
        Raises:
            InvalidPromptError: If template not found or invalid
        """
        try:
            # Add .txt extension if not present
            if not template_name.endswith('.txt'):
                template_name += '.txt'
            
            template = self.env.get_template(template_name)
            self.logger.debug(f"Loaded template: {template_name}")
            return template
            
        except TemplateNotFound:
            raise InvalidPromptError(f"Template '{template_name}' not found")
        except TemplateSyntaxError as e:
            raise InvalidPromptError(f"Template syntax error in '{template_name}': {e}")
    
    def register_template(self, name: str, template_string: str):
        """
        Register a template from string
        
        Args:
            name: Template name
            template_string: Template content
        """
        self._template_registry[name] = template_string
        self.logger.debug(f"Registered template: {name}")
    
    def list_templates(self) -> List[str]:
        """
        Get list of available templates
        
        Returns:
            List of template names (without .txt extension)
        """
        templates = []
        
        # File-based templates
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob('*.txt'):
                templates.append(template_file.stem)
        
        # Registered templates
        templates.extend(self._template_registry.keys())
        
        return sorted(list(set(templates)))
    
    def validate_template(self, template: str) -> bool:
        """
        Validate template syntax
        
        Args:
            template: Template string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.env.from_string(template)
            return True
        except TemplateSyntaxError as e:
            self.logger.warning(f"Template validation failed: {e}")
            return False
    
    # ========================================================================
    # PROMPT CONSTRUCTION
    # ========================================================================
    
    def build_prompt(
        self, 
        template_name: str, 
        context_data: Dict[str, Any]
    ) -> str:
        """
        Build prompt from template and context data
        
        Args:
            template_name: Name of template to use
            context_data: Dictionary of context variables
            
        Returns:
            Rendered prompt string
            
        Raises:
            InvalidPromptError: If template or rendering fails
        """
        try:
            # Try to load from registry first
            if template_name in self._template_registry:
                template = self.env.from_string(self._template_registry[template_name])
            else:
                # Load from file
                template = self.load_template(template_name)
            
            # Render template with context
            prompt = template.render(**context_data)
            
            self.logger.debug(
                f"Built prompt from '{template_name}' "
                f"({len(prompt)} chars, ~{len(prompt.split())} words)"
            )
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"Failed to build prompt: {e}")
            raise InvalidPromptError(f"Prompt building failed: {e}")
    
    def build_prompt_from_string(
        self, 
        template_string: str, 
        context_data: Dict[str, Any]
    ) -> str:
        """
        Build prompt from template string
        
        Args:
            template_string: Template content
            context_data: Context variables
            
        Returns:
            Rendered prompt
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context_data)
        except Exception as e:
            raise InvalidPromptError(f"Prompt rendering failed: {e}")
    
    def add_context_section(
        self, 
        prompt: str, 
        section_name: str, 
        content: str
    ) -> str:
        """
        Append a context section to existing prompt
        
        Args:
            prompt: Existing prompt text
            section_name: Name of section
            content: Section content
            
        Returns:
            Prompt with added section
        """
        section = f"\n\n{section_name.upper()}:\n{content}"
        return prompt + section
    
    def insert_few_shot_examples(
        self, 
        prompt: str, 
        examples: List[Dict[str, str]]
    ) -> str:
        """
        Add few-shot examples to prompt
        
        Args:
            prompt: Existing prompt
            examples: List of example dicts with 'input' and 'output' keys
            
        Returns:
            Prompt with examples
        """
        if not examples:
            return prompt
        
        examples_text = "\n\nEXAMPLES:\n\n"
        
        for i, example in enumerate(examples, 1):
            examples_text += f"Example {i}:\n"
            examples_text += f"Input: {example.get('input', '')}\n"
            examples_text += f"Output: {example.get('output', '')}\n\n"
        
        # Insert before final instruction
        return prompt + examples_text
    
    def apply_formatting_rules(self, text: str) -> str:
        """
        Apply consistent formatting to text
        
        Args:
            text: Text to format
            
        Returns:
            Formatted text
        """
        # Remove excessive blank lines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Ensure consistent spacing after punctuation
        text = re.sub(r'([.!?])\s+', r'\1 ', text)
        
        # Trim leading/trailing whitespace
        text = text.strip()
        
        return text
    
    # ========================================================================
    # CONTEXT OPTIMIZATION
    # ========================================================================
    
    def prioritize_context(
        self, 
        items: List[Dict[str, Any]], 
        max_length: int,
        key_field: str = 'content'
    ) -> List[Dict[str, Any]]:
        """
        Keep most important context within length limit
        
        Args:
            items: List of context items
            max_length: Maximum total character length
            key_field: Field to measure length
            
        Returns:
            Prioritized list of items
        """
        # Sort by importance (if field exists)
        if items and 'importance_weight' in items[0]:
            items = sorted(
                items, 
                key=lambda x: x.get('importance_weight', 0.5), 
                reverse=True
            )
        
        # Keep items until max length reached
        result = []
        current_length = 0
        
        for item in items:
            item_length = len(str(item.get(key_field, '')))
            
            if current_length + item_length <= max_length:
                result.append(item)
                current_length += item_length
            else:
                break
        
        self.logger.debug(
            f"Prioritized {len(result)}/{len(items)} items "
            f"(~{current_length} chars)"
        )
        
        return result
    
    def summarize_old_context(
        self, 
        text: str, 
        max_length: int = 500
    ) -> str:
        """
        Compress older context information
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summarized text
        """
        if len(text) <= max_length:
            return text
        
        # Extract key sentences (simple heuristic)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Keep first and last sentences, fill middle
        if len(sentences) <= 2:
            return text[:max_length] + '...'
        
        summary = sentences[0] + '. '
        remaining = max_length - len(summary) - len(sentences[-1]) - 10
        
        # Add middle content
        middle_text = ' '.join(sentences[1:-1])
        if len(middle_text) > remaining:
            summary += middle_text[:remaining] + '... '
        else:
            summary += middle_text + '. '
        
        summary += sentences[-1]
        
        return summary
    
    def balance_context_types(
        self, 
        context_dict: Dict[str, List[Any]]
    ) -> Dict[str, List[Any]]:
        """
        Ensure diverse representation of context types
        
        Args:
            context_dict: Dictionary of context type -> items
            
        Returns:
            Balanced context dictionary
        """
        # Calculate fair share for each type
        total_types = len(context_dict)
        
        if total_types == 0:
            return context_dict
        
        # Ensure each type has at least some representation
        min_items_per_type = 2
        
        balanced = {}
        for context_type, items in context_dict.items():
            if len(items) < min_items_per_type:
                balanced[context_type] = items
            else:
                # Take top items by importance if available
                if items and isinstance(items[0], dict) and 'importance_weight' in items[0]:
                    sorted_items = sorted(
                        items, 
                        key=lambda x: x.get('importance_weight', 0.5), 
                        reverse=True
                    )
                    balanced[context_type] = sorted_items[:max(min_items_per_type, len(items) // 2)]
                else:
                    balanced[context_type] = items[:max(min_items_per_type, len(items) // 2)]
        
        return balanced
    
    # ========================================================================
    # SPECIALIZED PROMPT BUILDERS
    # ========================================================================
    
    def build_chapter_prompt(
        self,
        story_title: str,
        genre: str,
        chapter_number: int,
        target_word_count: int,
        context: Dict[str, Any]
    ) -> str:
        """
        Build a chapter generation prompt
        
        Args:
            story_title: Title of story
            genre: Story genre
            chapter_number: Chapter number
            target_word_count: Target word count
            context: Additional context data
            
        Returns:
            Formatted prompt for chapter generation
        """
        context_data = {
            'story_title': story_title,
            'genre': genre,
            'chapter_number': chapter_number,
            'target_word_count': target_word_count,
            **context
        }
        
        return self.build_prompt('chapter_generation', context_data)
    
    def build_character_expansion_prompt(
        self,
        character_name: str,
        story_title: str,
        genre: str,
        existing_profile: str,
        expansion_aspects: List[str]
    ) -> str:
        """
        Build a character expansion prompt
        
        Args:
            character_name: Name of character
            story_title: Story title
            genre: Story genre
            existing_profile: Current character profile
            expansion_aspects: Aspects to expand
            
        Returns:
            Character expansion prompt
        """
        context_data = {
            'character_name': character_name,
            'story_title': story_title,
            'genre': genre,
            'existing_profile': existing_profile,
            'expansion_aspects': '\n'.join(f"- {aspect}" for aspect in expansion_aspects)
        }
        
        return self.build_prompt('character_expansion', context_data)
    
    def build_world_building_prompt(
        self,
        element_type: str,
        element_name: str,
        story_setting: str,
        existing_elements: List[str],
        requirements: str
    ) -> str:
        """
        Build a world-building prompt
        
        Args:
            element_type: Type of element (location, artifact, etc.)
            element_name: Name of element
            story_setting: Story setting description
            existing_elements: List of existing world elements
            requirements: Specific requirements
            
        Returns:
            World-building prompt
        """
        context_data = {
            'element_type': element_type,
            'element_name': element_name,
            'story_setting': story_setting,
            'existing_elements': '\n'.join(f"- {elem}" for elem in existing_elements),
            'requirements': requirements
        }
        
        return self.build_prompt('world_building', context_data)


# Global prompt builder instance
prompt_builder = PromptBuilder()