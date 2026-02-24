"""
Unit tests for AI components (Ollama, Prompt Builder, Context Manager)
Tests connection, generation, templating, and context gathering
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai import (
    OllamaClient, 
    OllamaConnectionError, 
    ModelNotFoundError, 
    GenerationError,
    PromptBuilder,
    InvalidPromptError,
    ContextManager
)
from config.settings import settings
from database import db_manager
from models import Story, Character, Chapter


class TestOllamaClient(unittest.TestCase):
    """Test Ollama client functionality"""
    
    def setUp(self):
        """Set up test client"""
        self.client = OllamaClient()
    
    @patch('ai.ollama_client.requests.get')
    def test_connection_success(self, mock_get):
        """Test successful connection to Ollama"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'models': []}
        mock_get.return_value = mock_response
        
        result = self.client.test_connection()
        self.assertTrue(result)
    
    @patch('ai.ollama_client.requests.get')
    def test_connection_failure(self, mock_get):
        """Test failed connection to Ollama"""
        mock_get.side_effect = Exception("Connection refused")
        
        with self.assertRaises(OllamaConnectionError):
            self.client.test_connection()
    
    @patch('ai.ollama_client.requests.get')
    def test_list_models(self, mock_get):
        """Test listing available models"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3.1:8b'},
                {'name': 'llama3.1:70b'}
            ]
        }
        mock_get.return_value = mock_response
        
        models = self.client.list_available_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]['name'], 'llama3.1:8b')
    
    @patch('ai.ollama_client.requests.get')
    def test_verify_model_exists(self, mock_get):
        """Test verifying model existence"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [{'name': 'llama3.1:8b'}]
        }
        mock_get.return_value = mock_response
        
        exists = self.client.verify_model('llama3.1:8b')
        self.assertTrue(exists)
        
        not_exists = self.client.verify_model('nonexistent:model')
        self.assertFalse(not_exists)
    
    @patch('ai.ollama_client.requests.post')
    @patch('ai.ollama_client.requests.get')
    def test_generate_basic(self, mock_get, mock_post):
        """Test basic text generation"""
        # Mock model verification
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            'models': [{'name': 'llama3.1:8b'}]
        }
        mock_get.return_value = mock_get_response
        
        # Mock generation
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            'response': 'Generated text here',
            'done': True
        }
        mock_post.return_value = mock_post_response
        
        result = self.client.generate(
            "Test prompt",
            model='llama3.1:8b'
        )
        
        self.assertEqual(result, 'Generated text here')
        mock_post.assert_called_once()
    
    def test_token_estimation(self):
        """Test token count estimation"""
        text = "This is a test sentence with several words."
        tokens = self.client.estimate_token_count(text)
        
        # Should be roughly len(text) / 4
        expected = len(text) // 4
        self.assertAlmostEqual(tokens, expected, delta=5)
    
    def test_context_trimming(self):
        """Test context trimming to token limit"""
        long_text = "word " * 10000  # 10000 words
        
        trimmed = self.client.trim_to_context_limit(
            long_text,
            max_tokens=1000
        )
        
        # Should be significantly shorter
        self.assertLess(len(trimmed), len(long_text))
        
        # Should be roughly 4000 characters (1000 tokens * 4)
        self.assertLess(len(trimmed), 5000)


class TestPromptBuilder(unittest.TestCase):
    """Test prompt builder functionality"""
    
    def setUp(self):
        """Set up test prompt builder"""
        self.builder = PromptBuilder()
    
    def test_template_validation(self):
        """Test template syntax validation"""
        valid_template = "Hello {{ name }}, welcome!"
        self.assertTrue(self.builder.validate_template(valid_template))
        
        invalid_template = "Hello {{ name, welcome!"
        self.assertFalse(self.builder.validate_template(invalid_template))
    
    def test_register_template(self):
        """Test registering template from string"""
        template_name = "test_template"
        template_string = "Hello {{ name }}!"
        
        self.builder.register_template(template_name, template_string)
        
        # Should be in registry
        templates = self.builder.list_templates()
        self.assertIn(template_name, templates)
    
    def test_build_prompt_from_string(self):
        """Test building prompt from template string"""
        template = "Hello {{ name }}, you are {{ age }} years old."
        context = {'name': 'John', 'age': 25}
        
        result = self.builder.build_prompt_from_string(template, context)
        self.assertEqual(result, "Hello John, you are 25 years old.")
    
    def test_conditional_blocks(self):
        """Test Jinja2 conditional blocks"""
        template = "{% if show_greeting %}Hello!{% endif %}"
        
        # With greeting
        result1 = self.builder.build_prompt_from_string(
            template, 
            {'show_greeting': True}
        )
        self.assertEqual(result1, "Hello!")
        
        # Without greeting
        result2 = self.builder.build_prompt_from_string(
            template, 
            {'show_greeting': False}
        )
        self.assertEqual(result2, "")
    
    def test_loop_constructs(self):
        """Test Jinja2 loops"""
        template = "{% for item in items %}{{ item }}, {% endfor %}"
        context = {'items': ['apple', 'banana', 'orange']}
        
        result = self.builder.build_prompt_from_string(template, context)
        self.assertEqual(result, "apple, banana, orange, ")
    
    def test_custom_filters(self):
        """Test custom Jinja2 filters"""
        # Test truncate_words filter
        template = "{{ text | truncate_words(5) }}"
        context = {'text': 'one two three four five six seven eight'}
        
        result = self.builder.build_prompt_from_string(template, context)
        self.assertIn('one two three four five', result)
        self.assertIn('...', result)
    
    def test_add_context_section(self):
        """Test adding context section to prompt"""
        base_prompt = "Write a story."
        section_name = "Characters"
        content = "John: protagonist, Mary: antagonist"
        
        result = self.builder.add_context_section(
            base_prompt,
            section_name,
            content
        )
        
        self.assertIn("CHARACTERS:", result)
        self.assertIn(content, result)
    
    def test_formatting_rules(self):
        """Test text formatting"""
        messy_text = "Hello.\n\n\n\nWorld.  \n  Test."
        
        formatted = self.builder.apply_formatting_rules(messy_text)
        
        # Should have normalized spacing
        self.assertNotIn('\n\n\n', formatted)
        self.assertEqual(formatted.strip(), formatted)
    
    def test_prioritize_context(self):
        """Test context prioritization"""
        items = [
            {'content': 'a' * 100, 'importance_weight': 0.3},
            {'content': 'b' * 100, 'importance_weight': 0.9},
            {'content': 'c' * 100, 'importance_weight': 0.5},
        ]
        
        prioritized = self.builder.prioritize_context(items, max_length=250)
        
        # Should keep highest importance items
        self.assertLessEqual(len(prioritized), 3)
        if prioritized:
            # First item should have highest importance
            self.assertEqual(prioritized[0]['importance_weight'], 0.9)


class TestContextManager(unittest.TestCase):
    """Test context manager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
        
        # Initialize database and create test story
        db_manager.initialize_database(self.test_story_id)
        db_manager.create_record(self.test_story_id, 'stories', {
            'id': self.test_story_id,
            'title': 'Test Story',
            'genre': 'Fantasy',
            'synopsis': 'A test story for context gathering'
        })
        
        self.context_manager = ContextManager()
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_build_chapter_context(self):
        """Test building complete chapter context"""
        # Create some test data
        char = Character(self.test_story_id, name='Hero', role='protagonist')
        char.save()
        
        context = self.context_manager.build_chapter_context(
            self.test_story_id,
            chapter_number=1
        )
        
        # Should have all required sections
        self.assertIn('story_metadata', context)
        self.assertIn('active_characters', context)
        self.assertIn('context_stats', context)
        
        # Story metadata should be populated
        self.assertEqual(context['story_metadata']['title'], 'Test Story')
    
    def test_get_character_context(self):
        """Test getting character context"""
        # Create test characters
        char1 = Character(self.test_story_id, name='Hero', role='protagonist')
        char1.save()
        
        char2 = Character(self.test_story_id, name='Villain', role='antagonist')
        char2.save()
        
        context = self.context_manager.get_character_context(
            [char1.id, char2.id],
            self.test_story_id
        )
        
        self.assertEqual(len(context), 2)
        self.assertEqual(context[0]['name'], 'Hero')
        self.assertEqual(context[1]['name'], 'Villain')
    
    def test_compress_context(self):
        """Test context compression"""
        # Create large context
        large_context = {
            'story_metadata': {'title': 'Test' * 1000},
            'active_characters': [
                {'name': f'Character{i}', 'background': 'x' * 500}
                for i in range(10)
            ],
            'relevant_lore': [
                {'content': 'y' * 500}
                for _ in range(10)
            ]
        }
        
        compressed = self.context_manager.compress_context(
            large_context,
            target_size=1000
        )
        
        # Should be smaller than original
        original_size = self.context_manager._estimate_context_size(large_context)
        compressed_size = self.context_manager._estimate_context_size(compressed)
        
        self.assertLess(compressed_size, original_size)
    
    def test_calculate_relevance_scores(self):
        """Test relevance scoring"""
        items = [
            {'importance_weight': 0.9},
            {'importance_weight': 0.3},
            {'importance_weight': 0.6}
        ]
        
        scores = self.context_manager.calculate_relevance_scores(items, current_chapter=5)
        
        self.assertEqual(len(scores), 3)
        # Scores should match importance weights
        self.assertEqual(scores[0], 0.9)
        self.assertEqual(scores[1], 0.3)
        self.assertEqual(scores[2], 0.6)


class TestIntegration(unittest.TestCase):
    """Integration tests for AI components"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
        
        # Initialize database
        db_manager.initialize_database(self.test_story_id)
        
        # Create test story
        db_manager.create_record(self.test_story_id, 'stories', {
            'id': self.test_story_id,
            'title': 'Integration Test Story',
            'genre': 'Fantasy',
            'synopsis': 'A story for testing full integration'
        })
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_full_prompt_generation_workflow(self):
        """Test complete workflow from context to prompt"""
        from ai import context_manager, prompt_builder
        
        # Create test data
        char = Character(
            self.test_story_id,
            name='TestHero',
            role='protagonist',
            personality='Brave and determined'
        )
        char.save()
        
        # Build context
        context = context_manager.build_chapter_context(
            self.test_story_id,
            chapter_number=1
        )
        
        # Build prompt
        prompt_data = {
            'story_title': context['story_metadata']['title'],
            'genre': context['story_metadata']['genre'],
            'chapter_number': 1,
            'target_word_count': 3000,
            'story_synopsis': context['story_metadata']['synopsis'],
            'character_details': '\n'.join([
                f"{ch['name']}: {ch['personality']}"
                for ch in context['active_characters']
            ]) if context['active_characters'] else 'No characters yet'
        }
        
        # Register a simple test template
        prompt_builder.register_template(
            'test_chapter',
            "Write chapter {{ chapter_number }} of {{ story_title }}. "
            "Genre: {{ genre }}. Characters: {{ character_details }}"
        )
        
        prompt = prompt_builder.build_prompt('test_chapter', prompt_data)
        
        # Verify prompt was built
        self.assertIn('Integration Test Story', prompt)
        self.assertIn('TestHero', prompt)
        self.assertIn('Fantasy', prompt)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)