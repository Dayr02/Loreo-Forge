"""
Unit tests for model classes
Tests ORM functionality, relationships, and business logic
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import db_manager
from models import Story, Character, Location, Chapter, Arc
from config.settings import settings


class TestBaseModel(unittest.TestCase):
    """Test base model functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
        
        # Initialize database and create story
        db_manager.initialize_database(self.test_story_id)
        db_manager.create_record(self.test_story_id, 'stories', {
            'id': self.test_story_id,
            'title': 'Test Story'
        })
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_model_creation(self):
        """Test creating a new model instance"""
        character = Character(self.test_story_id, name='Test Hero', role='protagonist')
        
        self.assertTrue(character.is_new())
        self.assertIsNone(character.id)
        self.assertEqual(character.name, 'Test Hero')
    
    def test_model_save_new(self):
        """Test saving a new model"""
        character = Character(self.test_story_id, name='Test Hero', role='protagonist')
        result = character.save()
        
        self.assertTrue(result)
        self.assertFalse(character.is_new())
        self.assertIsNotNone(character.id)
    
    def test_model_update(self):
        """Test updating an existing model"""
        character = Character(self.test_story_id, name='Test Hero', role='protagonist')
        character.save()
        
        # Modify and save
        character.age = 25
        result = character.save()
        
        self.assertTrue(result)
        
        # Verify update
        reloaded = Character.get_by_id(self.test_story_id, character.id)
        self.assertEqual(reloaded.age, 25)
    
    def test_model_delete(self):
        """Test deleting a model"""
        character = Character(self.test_story_id, name='Test Hero')
        character.save()
        character_id = character.id
        
        result = character.delete()
        self.assertTrue(result)
        
        # Verify deletion
        reloaded = Character.get_by_id(self.test_story_id, character_id)
        self.assertIsNone(reloaded)
    
    def test_model_refresh(self):
        """Test refreshing model from database"""
        character = Character(self.test_story_id, name='Test Hero')
        character.save()
        
        # Modify in database directly
        db_manager.update_record(
            self.test_story_id,
            'characters',
            character.id,
            {'age': 30}
        )
        
        # Refresh model
        character.refresh()
        self.assertEqual(character.age, 30)
    
    def test_to_dict(self):
        """Test converting model to dictionary"""
        character = Character(self.test_story_id, name='Test Hero', age=25)
        data = character.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data['name'], 'Test Hero')
        self.assertEqual(data['age'], 25)


class TestStoryModel(unittest.TestCase):
    """Test Story model"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_create_new_story(self):
        """Test creating a new story project"""
        story = Story.create_new(
            title='Test Story',
            genre='Fantasy',
            synopsis='A test story'
        )
        
        self.assertIsNotNone(story)
        self.assertIsNotNone(story.id)
        self.assertEqual(story.title, 'Test Story')
        self.assertEqual(story.genre, 'Fantasy')
    
    def test_story_statistics(self):
        """Test story statistics calculation"""
        story = Story.create_new(title='Test Story')
        
        # Add some test data
        char = Character(story.story_id, name='Hero')
        char.save()
        
        chapter = Chapter(story.story_id, chapter_number=1, content='Test content')
        chapter.save()
        
        stats = story.calculate_statistics()
        
        self.assertEqual(stats['total_characters'], 1)
        self.assertEqual(stats['total_chapters'], 1)
        self.assertGreater(stats['total_word_count'], 0)
    
    def test_get_characters(self):
        """Test retrieving story characters"""
        story = Story.create_new(title='Test Story')
        
        # Create characters
        char1 = Character(story.story_id, name='Hero 1')
        char1.save()
        char2 = Character(story.story_id, name='Hero 2')
        char2.save()
        
        characters = story.get_characters()
        self.assertEqual(len(characters), 2)


class TestCharacterModel(unittest.TestCase):
    """Test Character model"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
        
        db_manager.initialize_database(self.test_story_id)
        db_manager.create_record(self.test_story_id, 'stories', {
            'id': self.test_story_id,
            'title': 'Test Story'
        })
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_character_relationships(self):
        """Test character relationship management"""
        char1 = Character(self.test_story_id, name='Hero')
        char1.save()
        
        char2 = Character(self.test_story_id, name='Villain')
        char2.save()
        
        # Add relationship
        char1.add_relationship(char2.id, 'enemy', 'Arch nemesis')
        char1.save()
        
        # Verify relationship
        relationships = char1.relationships
        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0]['character_id'], char2.id)
        self.assertEqual(relationships[0]['type'], 'enemy')
    
    def test_duplicate_name_validation(self):
        """Test that duplicate character names are prevented"""
        char1 = Character(self.test_story_id, name='Hero')
        char1.save()
        
        char2 = Character(self.test_story_id, name='Hero')
        result = char2.save()
        
        self.assertFalse(result)
    
    def test_to_context_string(self):
        """Test converting character to context format"""
        char = Character(
            self.test_story_id,
            name='Test Hero',
            role='protagonist',
            age=25,
            personality='Brave and determined'
        )
        
        context = char.to_context_string()
        
        self.assertIn('Test Hero', context)
        self.assertIn('protagonist', context)
        self.assertIn('25', context)
        self.assertIn('Brave', context)


class TestChapterModel(unittest.TestCase):
    """Test Chapter model"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
        
        db_manager.initialize_database(self.test_story_id)
        db_manager.create_record(self.test_story_id, 'stories', {
            'id': self.test_story_id,
            'title': 'Test Story'
        })
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_word_count_auto_calculation(self):
        """Test automatic word count calculation"""
        chapter = Chapter(
            self.test_story_id,
            chapter_number=1,
            content='This is a test chapter with exactly ten words here.'
        )
        
        self.assertEqual(chapter.word_count, 10)
    
    def test_chapter_navigation(self):
        """Test previous/next chapter navigation"""
        ch1 = Chapter(self.test_story_id, chapter_number=1, content='Chapter 1')
        ch1.save()
        
        ch2 = Chapter(self.test_story_id, chapter_number=2, content='Chapter 2')
        ch2.save()
        
        # Test navigation
        prev = ch2.get_previous_chapter()
        self.assertIsNotNone(prev)
        self.assertEqual(prev.chapter_number, 1)
        
        next_ch = ch1.get_next_chapter()
        self.assertIsNotNone(next_ch)
        self.assertEqual(next_ch.chapter_number, 2)
    
    def test_chapter_versioning(self):
        """Test chapter version creation"""
        chapter = Chapter(
            self.test_story_id,
            chapter_number=1,
            content='Original content'
        )
        chapter.save()
        
        # Create version
        result = chapter.create_version(notes='First version')
        self.assertTrue(result)
        
        # Modify and create another version
        chapter.content = 'Modified content'
        chapter.save()
        chapter.create_version(notes='Second version')
        
        versions = chapter.get_versions()
        self.assertEqual(len(versions), 2)
    
    def test_duplicate_chapter_number(self):
        """Test that duplicate chapter numbers are prevented"""
        ch1 = Chapter(self.test_story_id, chapter_number=1, content='First')
        ch1.save()
        
        ch2 = Chapter(self.test_story_id, chapter_number=1, content='Second')
        result = ch2.save()
        
        self.assertFalse(result)


class TestArcModel(unittest.TestCase):
    """Test Arc model"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
        
        db_manager.initialize_database(self.test_story_id)
        db_manager.create_record(self.test_story_id, 'stories', {
            'id': self.test_story_id,
            'title': 'Test Story'
        })
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_arc_progress_calculation(self):
        """Test arc progress calculation"""
        arc = Arc(
            self.test_story_id,
            arc_number=1,
            title='Test Arc',
            starting_chapter=1,
            ending_chapter=5
        )
        arc.save()
        
        # Create some chapters
        for i in range(1, 4):
            ch = Chapter(
                self.test_story_id,
                chapter_number=i,
                arc_id=arc.id,
                content=f'Chapter {i}',
                status='final'
            )
            ch.save()
        
        progress = arc.calculate_progress()
        self.assertEqual(progress, 60.0)  # 3 out of 5 chapters
    
    def test_arc_themes(self):
        """Test arc theme management"""
        arc = Arc(self.test_story_id, arc_number=1)
        arc.save()
        
        # Add themes
        arc.add_theme('Redemption')
        arc.add_theme('Betrayal')
        
        themes = arc.get_themes()
        self.assertEqual(len(themes), 2)
        self.assertIn('Redemption', themes)
        
        # Remove theme
        arc.remove_theme('Betrayal')
        themes = arc.get_themes()
        self.assertEqual(len(themes), 1)


if __name__ == '__main__':
    unittest.main()