"""
Database Migration Script
Adds missing columns to chapters table for existing databases
Run this ONCE to update your existing story databases
"""

import sqlite3
from pathlib import Path
from config.settings import settings


def migrate_chapters_table(db_path: Path) -> bool:
    """
    Add missing columns to chapters table
    
    Args:
        db_path: Path to story database
        
    Returns:
        True if successful
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(chapters)")
        columns = [row[1] for row in cursor.fetchall()]
        
        migrations_applied = []
        
        # Add model_used column if missing
        if 'model_used' not in columns:
            cursor.execute("ALTER TABLE chapters ADD COLUMN model_used TEXT")
            migrations_applied.append('model_used')
        
        # Add edited column if missing
        if 'edited' not in columns:
            cursor.execute("ALTER TABLE chapters ADD COLUMN edited BOOLEAN DEFAULT 0")
            migrations_applied.append('edited')
        
        # Add generation_metadata column if missing
        if 'generation_metadata' not in columns:
            cursor.execute("ALTER TABLE chapters ADD COLUMN generation_metadata TEXT")
            migrations_applied.append('generation_metadata')
        
        conn.commit()
        conn.close()
        
        if migrations_applied:
            print(f"✓ Migrated {db_path.name}: Added columns {', '.join(migrations_applied)}")
        else:
            print(f"✓ {db_path.name} already up to date")
        
        return True
        
    except Exception as e:
        print(f"✗ Error migrating {db_path.name}: {e}")
        return False


def migrate_all_story_databases():
    """Migrate all existing story databases"""
    print("=" * 60)
    print("Database Migration - Adding Chapters Table Columns")
    print("=" * 60)
    print()
    
    stories_dir = settings.STORIES_DIR
    
    if not stories_dir.exists():
        print("No stories directory found. Nothing to migrate.")
        return
    
    # Find all story databases
    db_files = list(stories_dir.glob("story_*.db"))
    
    if not db_files:
        print("No story databases found. Nothing to migrate.")
        return
    
    print(f"Found {len(db_files)} story database(s) to migrate:")
    print()
    
    success_count = 0
    for db_file in db_files:
        if migrate_chapters_table(db_file):
            success_count += 1
    
    print()
    print("=" * 60)
    print(f"Migration complete: {success_count}/{len(db_files)} databases updated")
    print("=" * 60)


if __name__ == "__main__":
    migrate_all_story_databases()