"""
AI Controller
Orchestrates AI operations - bridges UI, Context, Prompts, and Ollama
"""

from typing import Dict, Any, Optional, List, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from ai.ollama_client import ollama_client
from ai.context_manager import context_manager
from ai.prompt_builder import prompt_builder
from ai.exceptions import (
    OllamaConnectionError,
    ModelNotFoundError,
    GenerationError,
    GenerationTimeoutError
)
from database import db_manager
from models.chapter import Chapter
from utils.logger import LoggerMixin


class GenerationWorkerThread(QThread):
    """Background thread for AI generation to keep UI responsive"""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage
    generation_complete = pyqtSignal(str)  # Generated content
    generation_error = pyqtSignal(str)  # Error message
    log_message = pyqtSignal(str)  # Log messages
    
    def __init__(self, prompt: str, model: str, temperature: float, max_tokens: int):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.is_cancelled = False
    
    def run(self):
        """Execute generation in background"""
        try:
            self.log_message.emit("🤖 Connecting to AI model...")
            self.progress_updated.emit(10)
            
            # Generate with Ollama
            self.log_message.emit(f"📝 Generating with {self.model}...")
            self.progress_updated.emit(30)
            
            generated_text = ollama_client.generate(
                prompt=self.prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if self.is_cancelled:
                self.log_message.emit("❌ Generation cancelled")
                return
            
            self.progress_updated.emit(100)
            self.log_message.emit(f"✅ Generated ~{len(generated_text.split())} words")
            self.generation_complete.emit(generated_text)
            
        except Exception as e:
            self.log_message.emit(f"❌ Error: {str(e)}")
            self.generation_error.emit(str(e))
    
    def cancel(self):
        """Cancel the generation"""
        self.is_cancelled = True


class AIController(QObject, LoggerMixin):
    """
    AI Controller - Phase 0-2 Implementation with Fixes
    """
    
    # Signals
    generation_started = pyqtSignal()
    generation_progress = pyqtSignal(int)  # Progress percentage
    generation_complete = pyqtSignal(int)  # Chapter ID
    generation_failed = pyqtSignal(str)  # Error message
    log_updated = pyqtSignal(str)  # Log message
    
    def __init__(self):
        QObject.__init__(self)
        LoggerMixin.__init__(self)
        
        self.worker_thread: Optional[GenerationWorkerThread] = None
        self.log_info("AIController initialized with Phase 0-2 safety measures")
    
    # ========================================================================
    # PHASE 0: CONTEXT SAFETY
    # ========================================================================
    
    def _validate_story_scope(self, story_id: int) -> bool:
        """PHASE 0: Ensure story ID is valid and active"""
        if not story_id or story_id <= 0:
            self.log_error("Invalid story ID - cannot generate")
            return False
        
        story_data = db_manager.get_story_metadata(story_id)
        if not story_data:
            self.log_error(f"Story {story_id} not found")
            return False
        
        self.log_info(f"✓ Story scope validated: {story_id}")
        return True
    
    def _create_readonly_context_snapshot(
        self,
        story_id: int,
        chapter_number: int,
        selected_context: Optional[Dict[str, List[int]]] = None
    ) -> Dict[str, Any]:
        """
        PHASE 0/1: Create immutable context snapshot
        
        FIXED: Now checks if any entity lists are non-empty before using
        selective context. If selected_context is an all-empty dict
        (e.g., {'characters': [], 'locations': [], ...}), falls back to
        automatic context selection instead of generating with zero entities.
        """
        self.log_info(f"Creating context snapshot for story {story_id}, chapter {chapter_number}")

        # Use selective context if provided AND at least one entity type is selected
        if selected_context and any(selected_context.values()):
            self.log_info("Using user-selected context (Phase 1)")
            context = context_manager.build_selective_context(
                story_id,
                chapter_number,
                selected_context
            )
        else:
            # Auto mode: None, empty dict, or all lists empty
            if selected_context:
                self.log_info("No entities selected — using automatic context selection")
            else:
                self.log_info("Using automatic context selection")
            context = context_manager.build_chapter_context(
                story_id,
                chapter_number
            )

        # PHASE 0: Validate context
        assert isinstance(context, dict), "Context must be a dictionary"

        self.log_info("✓ Context snapshot created (read-only, story-scoped)")
        return context
    
    # ========================================================================
    # DETERMINISTIC CONTEXT CONTRACT
    # ========================================================================
    
    def get_context_preview(
        self,
        story_id: int,
        chapter_number: int,
        selected_context: Optional[Dict[str, List[int]]] = None
    ) -> Dict[str, Any]:
        """PHASE 1: Preview context before generation"""
        if not self._validate_story_scope(story_id):
            return {}
        
        summary = context_manager.get_context_summary(
            story_id,
            chapter_number,
            selected_context
        )
        
        from database.master_db import master_db
        story_data = master_db.fetch_one(
            "SELECT title FROM stories WHERE id = ?",
            (story_id,)
        )
        
        preview = {
            'story_title': story_data['title'] if story_data else 'Unknown',
            'mode': summary.get('mode', 'automatic'),
            'character_count': summary.get('characters', 0),
            'location_count': summary.get('locations', 0),
            'lore_count': summary.get('lore', 0),
            'creature_count': summary.get('creatures', 0),
            'organization_count': summary.get('organizations', 0),
            'power_systems_count': summary.get('power_systems', 0),
            'total_context_items': summary.get('total_entities', 0),
            'estimated_tokens': summary.get('estimated_tokens', 0)
        }
        
        self.log_info(
            f"Context preview ({preview['mode']}): "
            f"{preview['total_context_items']} items, "
            f"~{preview['estimated_tokens']} tokens"
        )
        
        return preview
    
    # ========================================================================
    # PHASE 2: CHAPTER GENERATION WITH STORY PROGRESSION
    # ========================================================================
    
    def generate_chapter(
        self,
        story_id: int,
        chapter_number: int,
        title: Optional[str] = None,
        target_word_count: int = 3000,
        pov_character: Optional[str] = None,
        mood: Optional[str] = None,
        plot_points: Optional[str] = None,
        style_instructions: Optional[str] = None,
        story_progression_prompt: Optional[str] = None,  # NEW: Story progression
        generation_type: str = "full_chapter",  # NEW: full_chapter, chapter_parts, short_story
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        selected_context: Optional[Dict[str, List[int]]] = None
    ) -> bool:
        """
        PHASE 2: Generate chapter with full safety and context
        ENHANCED: Added story progression prompt and generation type
        """
        try:
            # PHASE 0: Validate story scope
            if not self._validate_story_scope(story_id):
                self.generation_failed.emit("Invalid story scope")
                return False
            
            self.log_info(f"Starting {generation_type} generation for chapter {chapter_number}")
            
            # PHASE 0: Create read-only context snapshot (FIXED)
            context = self._create_readonly_context_snapshot(
                story_id,
                chapter_number,
                selected_context
            )
            
            # PHASE 1: Build prompt using deterministic context
            prompt = self._build_chapter_prompt(
                context=context,
                chapter_number=chapter_number,
                title=title,
                target_word_count=target_word_count,
                pov_character=pov_character,
                mood=mood,
                plot_points=plot_points,
                style_instructions=style_instructions,
                story_progression_prompt=story_progression_prompt,
                generation_type=generation_type
            )
            
            self.log_info(f"Prompt built: {len(prompt)} chars")
            
            # PHASE 2: Start generation in background thread
            model = model or 'llama3.1:8b'
            temperature = temperature if temperature is not None else 0.7
            
            self.worker_thread = GenerationWorkerThread(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=target_word_count * 2
            )
            
            # Connect signals
            self.worker_thread.progress_updated.connect(self.generation_progress.emit)
            self.worker_thread.log_message.connect(self.log_updated.emit)
            self.worker_thread.generation_complete.connect(
                lambda content: self._on_generation_complete(
                    story_id, chapter_number, title, content, mood, plot_points
                )
            )
            self.worker_thread.generation_error.connect(self._on_generation_error)
            
            # Start generation
            self.worker_thread.start()
            self.generation_started.emit()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to start generation: {e}")
            self.generation_failed.emit(str(e))
            return False
    
    def _build_chapter_prompt(
        self,
        context: Dict[str, Any],
        chapter_number: int,
        title: Optional[str],
        target_word_count: int,
        pov_character: Optional[str],
        mood: Optional[str],
        plot_points: Optional[str],
        style_instructions: Optional[str],
        story_progression_prompt: Optional[str],
        generation_type: str
    ) -> str:
        """
        Build chapter generation prompt
        ENHANCED: Added story progression and generation type
        """
        # Prepare template data
        template_data = {
            'chapter_number': chapter_number,
            'story_title': context.get('story_metadata', {}).get('title', 'Untitled'),
            'genre': context.get('story_metadata', {}).get('genre', 'Fiction'),
            'story_synopsis': context.get('story_metadata', {}).get('synopsis', ''),
            'target_word_count': target_word_count,
            'pov_character': pov_character or 'Third-person omniscient',
            'mood': mood or 'Dramatic',
            'required_plot_points': plot_points or '',
            'style_guidelines': style_instructions or '',
            'story_progression': story_progression_prompt or '',
            'generation_type': generation_type
        }
        
        # Add generation type specific instructions
        if generation_type == "chapter_parts":
            template_data['generation_instruction'] = "Generate this as a complete scene or section that can stand alone but connects to the larger chapter."
        elif generation_type == "short_story":
            template_data['generation_instruction'] = "Generate this as a complete, self-contained short story with beginning, middle, and end."
        else:  # full_chapter
            template_data['generation_instruction'] = "Generate a complete chapter with full narrative arc."
        
        # Add arc context
        if context.get('current_arc'):
            template_data['arc_description'] = context['current_arc'].get('description', '')
        
        # Add recent chapters
        recent_chapters = context.get('recent_chapters', [])
        if recent_chapters:
            summaries = []
            for ch in recent_chapters:
                summaries.append(f"Chapter {ch['chapter_number']}: {ch['summary']}")
            template_data['recent_chapters_summary'] = '\n'.join(summaries)
        
        # Add character details
        characters = context.get('active_characters', []) or context.get('selected_characters', [])
        if characters:
            char_details = []
            for char in characters[:5]:
                char_details.append(
                    f"- {char['name']} ({char.get('role', 'character')}): {char.get('personality', 'No description')}"
                )
            template_data['character_details'] = '\n'.join(char_details)
        
        # Add power systems
        power_systems = context.get('power_systems', []) or context.get('selected_power_systems', [])
        if power_systems:
            rules = []
            for ps in power_systems:
                rules.append(f"- {ps.get('system_name', 'Unknown')}: {ps.get('rules', 'No rules defined')}")
            template_data['power_system_rules'] = '\n'.join(rules)
        
        # Add items (weapons, artifacts, equipment)
        items = context.get('items', []) or context.get('selected_items', [])
        if items:
            item_details = []
            for item in items[:5]:  # Limit to top 5 items
                # Build item entry with all relevant details
                item_entry = f"- {item.get('name')} ({item.get('rarity', 'Unknown')} {item.get('type', 'Item')})"
                
                if item.get('description'):
                    item_entry += f"\n  Description: {item.get('description')[:150]}"
                
                if item.get('properties'):
                    item_entry += f"\n  Properties: {item.get('properties')}"
                
                if item.get('powers'):
                    item_entry += f"\n  Powers: {item.get('powers')}"
                
                if item.get('current_owner'):
                    item_entry += f"\n  Current Owner: {item.get('current_owner')}"
                
                if item.get('current_location'):
                    item_entry += f"\n  Current Location: {item.get('current_location')}"
                
                item_details.append(item_entry)
            
            template_data['item_details'] = '\n\n'.join(item_details)

        # Add previous chapter ending
        if context.get('previous_chapter_ending'):
            template_data['previous_chapter_ending'] = context['previous_chapter_ending']
        
        # Build prompt from template
        try:
            prompt = prompt_builder.build_prompt('chapter_generation', template_data)
            return prompt
        except Exception as e:
            self.log_error(f"Failed to build prompt from template: {e}")
            return self._build_fallback_prompt(template_data)
    
    def _build_fallback_prompt(self, data: Dict[str, Any]) -> str:
        """Simple fallback if template fails"""
        prompt = f"""Write chapter {data['chapter_number']} of "{data['story_title']}", a {data['genre']} story.

Target word count: {data['target_word_count']} words
Mood: {data['mood']}
POV: {data['pov_character']}
Type: {data.get('generation_instruction', 'Full chapter')}

{data.get('story_progression', '')}

{data.get('required_plot_points', '')}

Begin the chapter now:"""
        return prompt
    
    def _on_generation_complete(
        self,
        story_id: int,
        chapter_number: int,
        title: Optional[str],
        content: str,
        mood: Optional[str],
        plot_points: Optional[str]
    ):
        """Handle successful generation and save to database"""
        try:
            self.log_info("Generation complete - saving to database")
            
            chapter = Chapter(
                story_id,
                chapter_number=chapter_number,
                title=title or f"Chapter {chapter_number}",
                content=content,
                mood=mood,
                status='draft',
                model_used=self.worker_thread.model if self.worker_thread else 'unknown',
                edited=False
            )
            
            if plot_points:
                chapter._data['plot_points'] = plot_points
            
            if chapter.save():
                self.log_info(f"Chapter {chapter_number} saved successfully (ID: {chapter.id})")
                self.generation_complete.emit(chapter.id)
            else:
                self.log_error("Failed to save chapter to database")
                self.generation_failed.emit("Failed to save chapter")
                
        except Exception as e:
            self.log_error(f"Error saving generated chapter: {e}")
            self.generation_failed.emit(f"Save error: {str(e)}")
    
    def _on_generation_error(self, error_message: str):
        """Handle generation errors"""
        self.log_error(f"Generation error: {error_message}")
        self.generation_failed.emit(error_message)
    
    def cancel_generation(self):
        """Cancel ongoing generation"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.log_info("Cancelling generation...")
            self.worker_thread.cancel()
            self.worker_thread.wait()
            self.log_info("Generation cancelled")
    
    # ========================================================================
    # CHAPTER PARTS GENERATION
    # ========================================================================
    
    def generate_chapter_part(
        self,
        story_id: int,
        chapter_number: int,
        part_number: int,
        title: Optional[str] = None,
        target_word_count: int = 2000,
        story_progression_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        selected_context: Optional[Dict[str, List[int]]] = None
    ) -> bool:
        """
        Generate a chapter part with context from previous parts
        
        Args:
            story_id: Story identifier
            chapter_number: Chapter number
            part_number: Part number within chapter
            title: Optional part title
            target_word_count: Target word count for this part
            story_progression_prompt: What should happen in this part
            model: AI model to use
            temperature: Generation temperature
            selected_context: User-selected context entities
            
        Returns:
            True if generation started successfully
        """
        try:
            # Validate story scope
            if not self._validate_story_scope(story_id):
                self.generation_failed.emit("Invalid story scope")
                return False
            
            self.log_info(
                f"Starting part {part_number} generation for chapter {chapter_number}"
            )
            
            # Get context including previous parts
            context = self._create_context_with_previous_parts(
                story_id,
                chapter_number,
                part_number,
                selected_context
            )
            
            # Build prompt for chapter part
            prompt = self._build_chapter_part_prompt(
                context=context,
                chapter_number=chapter_number,
                part_number=part_number,
                title=title,
                target_word_count=target_word_count,
                story_progression_prompt=story_progression_prompt
            )
            
            self.log_info(f"Part prompt built: {len(prompt)} chars")
            
            # Start generation
            model = model or 'llama3.1:8b'
            temperature = temperature if temperature is not None else 0.7
            
            self.worker_thread = GenerationWorkerThread(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=target_word_count * 2
            )
            
            # Connect signals - save as part instead of chapter
            self.worker_thread.progress_updated.connect(self.generation_progress.emit)
            self.worker_thread.log_message.connect(self.log_updated.emit)
            self.worker_thread.generation_complete.connect(
                lambda content: self._on_part_generation_complete(
                    story_id, chapter_number, part_number, title, content, 
                    story_progression_prompt
                )
            )
            self.worker_thread.generation_error.connect(self._on_generation_error)
            
            # Start generation
            self.worker_thread.start()
            self.generation_started.emit()
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to start part generation: {e}")
            self.generation_failed.emit(str(e))
            return False
    
    def _create_context_with_previous_parts(
        self,
        story_id: int,
        chapter_number: int,
        current_part_number: int,
        selected_context: Optional[Dict[str, List[int]]] = None
    ) -> Dict[str, Any]:
        """
        Create context including previous chapter parts for continuity
        
        FIXED: Uses same selected_context logic as _create_readonly_context_snapshot
        """
        # Get base context with fixed logic
        if selected_context and any(selected_context.values()):
            context = context_manager.build_selective_context(
                story_id,
                chapter_number,
                selected_context
            )
        else:
            context = context_manager.build_chapter_context(
                story_id,
                chapter_number
            )
        
        # Add previous parts from this chapter
        previous_parts = db_manager.get_chapter_parts(story_id, chapter_number)
        
        # Filter to only parts before current part
        previous_parts = [
            p for p in previous_parts 
            if p.get('part_number', 0) < current_part_number
        ]
        
        if previous_parts:
            # Sort by part number
            previous_parts.sort(key=lambda x: x.get('part_number', 0))
            
            # Create summary of previous parts
            parts_summary = []
            for part in previous_parts:
                part_num = part.get('part_number', 0)
                content = part.get('content', '')
                words = part.get('word_count', 0)
                
                # Get first 200 chars as summary
                summary = content[:200] + '...' if len(content) > 200 else content
                
                parts_summary.append({
                    'part_number': part_num,
                    'summary': summary,
                    'word_count': words,
                    'story_progression': part.get('story_progression_notes', '')
                })
            
            context['previous_parts'] = parts_summary
            
            # Get the ending of the last part for smooth continuation
            last_part = previous_parts[-1]
            last_content = last_part.get('content', '')
            if last_content:
                # Get last 300 characters
                context['previous_part_ending'] = last_content[-300:]
        
        return context
    
    def _build_chapter_part_prompt(
        self,
        context: Dict[str, Any],
        chapter_number: int,
        part_number: int,
        title: Optional[str],
        target_word_count: int,
        story_progression_prompt: Optional[str]
    ) -> str:
        """
        Build prompt for chapter part generation
        
        Args:
            context: Context dictionary
            chapter_number: Chapter number
            part_number: Part number
            title: Part title
            target_word_count: Target word count
            story_progression_prompt: Story progression instructions
            
        Returns:
            Generated prompt string
        """
        # Build base template data
        template_data = {
            'chapter_number': chapter_number,
            'part_number': part_number,
            'story_title': context.get('story_metadata', {}).get('title', 'Untitled'),
            'genre': context.get('story_metadata', {}).get('genre', 'Fiction'),
            'story_synopsis': context.get('story_metadata', {}).get('synopsis', ''),
            'target_word_count': target_word_count,
            'generation_instruction': f"Generate Part {part_number} of Chapter {chapter_number} as a complete scene.",
            'story_progression': story_progression_prompt or ''
        }
        
        # Add previous parts context
        if context.get('previous_parts'):
            parts_text = []
            for part in context['previous_parts']:
                parts_text.append(
                    f"Part {part['part_number']} ({part['word_count']} words):\n"
                    f"{part['summary']}\n"
                    f"Progression: {part.get('story_progression', 'N/A')}"
                )
            
            template_data['previous_parts_summary'] = '\n\n'.join(parts_text)
            
            if context.get('previous_part_ending'):
                template_data['previous_part_ending'] = context['previous_part_ending']
        
        # Add arc context
        if context.get('current_arc'):
            template_data['arc_description'] = context['current_arc'].get('description', '')
        
        # Add character details
        characters = context.get('active_characters', []) or context.get('selected_characters', [])
        if characters:
            char_details = []
            for char in characters[:5]:
                char_details.append(
                    f"- {char['name']} ({char.get('role', 'character')}): {char.get('personality', 'No description')}"
                )
            template_data['character_details'] = '\n'.join(char_details)
        
        # Build custom prompt for part generation
        prompt = f"""You are a skilled novelist writing Part {part_number} of Chapter {chapter_number} of "{template_data['story_title']}", a {template_data['genre']} story.
    
    STORY CONTEXT:
    {template_data.get('story_synopsis', 'No synopsis provided.')}
    
    """
        
        if template_data.get('arc_description'):
            prompt += f"""CURRENT ARC:
    {template_data['arc_description']}
    
    """
        
        if template_data.get('previous_parts_summary'):
            prompt += f"""PREVIOUS PARTS OF THIS CHAPTER:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {template_data['previous_parts_summary']}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    """
        
        if template_data.get('previous_part_ending'):
            prompt += f"""PREVIOUS PART ENDED WITH:
    {template_data['previous_part_ending']}
    
    """
        
        if template_data.get('character_details'):
            prompt += f"""ACTIVE CHARACTERS:
    {template_data['character_details']}
    
    """
        
        if story_progression_prompt:
            prompt += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    STORY PROGRESSION FOR THIS PART:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {story_progression_prompt}
    
    This is your PRIMARY DIRECTIVE for this part. Follow this progression closely.
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    """
        
        prompt += f"""PART REQUIREMENTS:
    - This is Part {part_number} of Chapter {chapter_number}
    - Target word count: {target_word_count} words
    - Continue smoothly from the previous part
    - This part should feel complete but leave room for continuation
    - Maintain consistency with all previous parts
    
    Write Part {part_number} now. Create vivid, immersive prose with strong character voices and narrative momentum. Ensure smooth continuation from the previous part. Write approximately {target_word_count} words.
    
    Begin Part {part_number}:"""
        
        return prompt
    
    def _on_part_generation_complete(
        self,
        story_id: int,
        chapter_number: int,
        part_number: int,
        title: Optional[str],
        content: str,
        story_progression_notes: Optional[str]
    ):
        """Handle successful part generation"""
        try:
            self.log_info(f"Part {part_number} generation complete - saving to database")
            
            # Save as chapter part
            part_id = db_manager.create_chapter_part(
                story_id,
                chapter_number,
                content,
                title or f'Part {part_number}',
                context_summary=f"Generated {len(content.split())} words",
                story_progression_notes=story_progression_notes
            )
            
            if part_id:
                self.log_info(f"Chapter part {part_number} saved successfully (ID: {part_id})")
                # Emit with negative ID to signal it's a part, not a chapter
                self.generation_complete.emit(-part_id)
            else:
                self.log_error("Failed to save chapter part to database")
                self.generation_failed.emit("Failed to save chapter part")
                
        except Exception as e:
            self.log_error(f"Error saving generated part: {e}")
            self.generation_failed.emit(f"Save error: {str(e)}")
            
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    def test_ollama_connection(self) -> bool:
        """Test if Ollama is accessible"""
        try:
            return ollama_client.test_connection()
        except Exception as e:
            self.log_error(f"Ollama connection test failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models"""
        try:
            models = ollama_client.list_available_models()
            return [m['name'] for m in models]
        except Exception as e:
            self.log_error(f"Failed to list models: {e}")
            return []


# Global AI controller instance
ai_controller = AIController()