"""
Unit tests for database layer
Tests schema creation, CRUD operations, and queries
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import db_manager, DatabaseSchema
from config.settings import settings


class TestDatabaseSchema(unittest.TestCase):
    """Test database schema creation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        # Override story database path for testing
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
    
    def tearDown(self):
        """Clean up test environment"""
        # Close connections
        db_manager.close_all_connections()
        
        # Remove test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        # Restore original path
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_schema_creation(self):
        """Test that database schema is created successfully"""
        result = db_manager.initialize_database(self.test_story_id)
        self.assertTrue(result)
        
        # Verify database file exists
        db_path = settings.get_story_db_path(self.test_story_id)
        self.assertTrue(db_path.exists())
    
    def test_schema_verification(self):
        """Test schema verification"""
        db_manager.initialize_database(self.test_story_id)
        conn = db_manager.get_connection(self.test_story_id)
        
        schema = DatabaseSchema()
        is_valid = schema.verify_schema(conn)
        self.assertTrue(is_valid)
    
    def test_schema_version(self):
        """Test schema version tracking"""
        db_manager.initialize_database(self.test_story_id)
        version = db_manager.get_schema_version(self.test_story_id)
        self.assertEqual(version, DatabaseSchema.SCHEMA_VERSION)


class TestDatabaseCRUD(unittest.TestCase):
    """Test CRUD operations"""
    
    def setUp(self):
        """Set up test database"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
        
        db_manager.initialize_database(self.test_story_id)
        
        # Create test story
        self.story_data = {
            'id': self.test_story_id,
            'title': 'Test Story',
            'genre': 'Fantasy',
            'synopsis': 'A test story for unit testing'
        }
        db_manager.create_record(self.test_story_id, 'stories', self.story_data)
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_create_character(self):
        """Test character creation"""
        character_data = {
            'name': 'Test Hero',
            'role': 'protagonist',
            'age': 25,
            'status': 'alive',
            'importance_weight': 1.0
        }
        
        character_id = db_manager.create_record(
            self.test_story_id, 
            'characters', 
            character_data
        )
        
        self.assertIsNotNone(character_id)
        self.assertGreater(character_id, 0)
    
    def test_get_character(self):
        """Test retrieving a character"""
        # Create character
        character_data = {
            'name': 'Test Hero',
            'role': 'protagonist'
        }
        character_id = db_manager.create_record(
            self.test_story_id, 
            'characters', 
            character_data
        )
        
        # Retrieve character
        character = db_manager.get_record(
            self.test_story_id, 
            'characters', 
            character_id
        )
        
        self.assertIsNotNone(character)
        self.assertEqual(character['name'], 'Test Hero')
        self.assertEqual(character['role'], 'protagonist')
    
    def test_update_character(self):
        """Test updating a character"""
        # Create character
        character_data = {'name': 'Test Hero', 'age': 25}
        character_id = db_manager.create_record(
            self.test_story_id, 
            'characters', 
            character_data
        )
        
        # Update character
        update_data = {'age': 26, 'status': 'alive'}
        result = db_manager.update_record(
            self.test_story_id, 
            'characters', 
            character_id, 
            update_data
        )
        
        self.assertTrue(result)
        
        # Verify update
        character = db_manager.get_record(
            self.test_story_id, 
            'characters', 
            character_id
        )
        self.assertEqual(character['age'], 26)
        self.assertEqual(character['status'], 'alive')
    
    def test_delete_character(self):
        """Test deleting a character"""
        # Create character
        character_data = {'name': 'Test Hero'}
        character_id = db_manager.create_record(
            self.test_story_id, 
            'characters', 
            character_data
        )
        
        # Delete character
        result = db_manager.delete_record(
            self.test_story_id, 
            'characters', 
            character_id
        )
        
        self.assertTrue(result)
        
        # Verify deletion
        character = db_manager.get_record(
            self.test_story_id, 
            'characters', 
            character_id
        )
        self.assertIsNone(character)
    
    def test_json_field_serialization(self):
        """Test JSON field serialization/deserialization"""
        character_data = {
            'name': 'Test Hero',
            'relationships': [
                {'character_id': 2, 'type': 'friend', 'description': 'Best friend'},
                {'character_id': 3, 'type': 'rival', 'description': 'Long-time rival'}
            ]
        }
        
        character_id = db_manager.create_record(
            self.test_story_id, 
            'characters', 
            character_data
        )
        
        # Retrieve and verify JSON deserialization
        character = db_manager.get_record(
            self.test_story_id, 
            'characters', 
            character_id
        )
        
        self.assertIsInstance(character['relationships'], list)
        self.assertEqual(len(character['relationships']), 2)
        self.assertEqual(character['relationships'][0]['type'], 'friend')
    
    def test_bulk_insert(self):
        """Test bulk insertion of records"""
        characters = [
            {'name': 'Hero 1', 'role': 'protagonist'},
            {'name': 'Hero 2', 'role': 'protagonist'},
            {'name': 'Villain 1', 'role': 'antagonist'}
        ]
        
        result = db_manager.bulk_insert(
            self.test_story_id, 
            'characters', 
            characters
        )
        
        self.assertTrue(result)
        
        # Verify all characters were inserted
        all_characters = db_manager.get_all_characters(self.test_story_id)
        self.assertEqual(len(all_characters), 3)


class TestDatabaseQueries(unittest.TestCase):
    """Test complex queries"""
    
    def setUp(self):
        """Set up test database with sample data"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_story_id = 999
        
        self.original_stories_dir = settings.STORIES_DIR
        settings.STORIES_DIR = self.test_dir
        
        db_manager.initialize_database(self.test_story_id)
        
        # Create story
        db_manager.create_record(self.test_story_id, 'stories', {
            'id': self.test_story_id,
            'title': 'Test Story',
            'genre': 'Fantasy'
        })
        
        # Create test characters
        self.char1_id = db_manager.create_record(self.test_story_id, 'characters', {
            'name': 'Main Hero',
            'role': 'protagonist',
            'importance_weight': 1.0
        })
        
        self.char2_id = db_manager.create_record(self.test_story_id, 'characters', {
            'name': 'Sidekick',
            'role': 'supporting',
            'importance_weight': 0.7
        })
        
        # Create test chapters
        for i in range(1, 4):
            db_manager.create_record(self.test_story_id, 'chapters', {
                'chapter_number': i,
                'title': f'Chapter {i}',
                'content': f'Content of chapter {i}',
                'word_count': 1000 * i,
                'pov_character_id': self.char1_id
            })
    
    def tearDown(self):
        """Clean up"""
        db_manager.close_all_connections()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        settings.STORIES_DIR = self.original_stories_dir
    
    def test_get_story_metadata(self):
        """Test retrieving story metadata with statistics"""
        metadata = db_manager.get_story_metadata(self.test_story_id)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['title'], 'Test Story')
        self.assertEqual(metadata['total_chapters'], 3)
        self.assertEqual(metadata['total_characters'], 2)
        self.assertEqual(metadata['total_word_count'], 6000)  # 1000 + 2000 + 3000
    
    def test_get_chapter_by_number(self):
        """Test retrieving chapter by number"""
        chapter = db_manager.get_chapter_by_number(self.test_story_id, 2)
        
        self.assertIsNotNone(chapter)
        self.assertEqual(chapter['title'], 'Chapter 2')
        self.assertEqual(chapter['word_count'], 2000)
    
    def test_get_chapters_range(self):
        """Test retrieving chapter range"""
        chapters = db_manager.get_chapters_range(self.test_story_id, 1, 2)
        
        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0]['chapter_number'], 1)
        self.assertEqual(chapters[1]['chapter_number'], 2)
    
    def test_get_recent_chapters(self):
        """Test retrieving recent chapters"""
        chapters = db_manager.get_recent_chapters(self.test_story_id, 2)
        
        self.assertEqual(len(chapters), 2)
        # Should be in reverse order (most recent first)
        self.assertEqual(chapters[0]['chapter_number'], 3)
        self.assertEqual(chapters[1]['chapter_number'], 2)
    
    def test_verify_chapter_sequence(self):
        """Test chapter sequence verification"""
        is_valid, missing = db_manager.verify_chapter_sequence(self.test_story_id)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)
        
        # Create gap by deleting chapter 2
        chapter = db_manager.get_chapter_by_number(self.test_story_id, 2)
        db_manager.delete_record(self.test_story_id, 'chapters', chapter['id'])
        
        is_valid, missing = db_manager.verify_chapter_sequence(self.test_story_id)
        self.assertFalse(is_valid)
        self.assertEqual(missing, [2])
    
    def test_check_duplicate_names(self):
        """Test duplicate name checking"""
        # Should find duplicate
        has_duplicate = db_manager.check_duplicate_names(
            'characters',
            'Main Hero',
            self.test_story_id
        )
        self.assertTrue(has_duplicate)
        
        # Should not find duplicate
        has_duplicate = db_manager.check_duplicate_names(
            'characters',
            'Nonexistent Hero',
            self.test_story_id
        )
        self.assertFalse(has_duplicate)


if __name__ == '__main__':
    unittest.main()