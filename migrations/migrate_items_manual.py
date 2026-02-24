"""
Manual Migration and Verification Script
Run this to manually migrate databases and verify items table exists
"""

import sqlite3
from pathlib import Path
from config.settings import settings


def verify_and_migrate_single_story(story_id: int) -> dict:
    """
    Verify and migrate a single story database
    
    Returns dict with:
        - tables_before: list of tables before migration
        - tables_after: list of tables after migration
        - items_existed: bool
        - items_created: bool
        - success: bool
    """
    result = {
        'story_id': story_id,
        'tables_before': [],
        'tables_after': [],
        'items_existed': False,
        'items_created': False,
        'success': False,
        'error': None
    }
    
    db_path = settings.get_story_db_path(story_id)
    
    if not db_path.exists():
        result['error'] = f"Database not found: {db_path}"
        return result
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get tables before
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        result['tables_before'] = [row[0] for row in cursor.fetchall()]
        result['items_existed'] = 'items' in result['tables_before']
        
        # Create items table if it doesn't exist
        if not result['items_existed']:
            print(f"  Creating 'items' table in story_{story_id}.db...")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT,
                    category TEXT,
                    rarity TEXT,
                    description TEXT,
                    properties TEXT,
                    powers TEXT,
                    materials TEXT,
                    creator TEXT,
                    history TEXT,
                    current_owner TEXT,
                    current_location TEXT,
                    value TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(story_id, name)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_items_story ON items(story_id)
            """)
            
            conn.commit()
            result['items_created'] = True
        
        # Get tables after
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        result['tables_after'] = [row[0] for row in cursor.fetchall()]
        
        # Verify items table exists now
        if 'items' in result['tables_after']:
            result['success'] = True
            
            # Get item count
            cursor.execute("SELECT COUNT(*) FROM items WHERE story_id = ?", (story_id,))
            item_count = cursor.fetchone()[0]
            result['item_count'] = item_count
        
        conn.close()
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def main():
    """Main verification and migration"""
    print("=" * 70)
    print("📋 MANUAL DATABASE MIGRATION & VERIFICATION")
    print("=" * 70)
    print()
    
    stories_dir = settings.STORIES_DIR
    
    if not stories_dir.exists():
        print(f"❌ Stories directory not found: {stories_dir}")
        return
    
    db_files = list(stories_dir.glob("story_*.db"))
    
    if not db_files:
        print(f"No story databases found in {stories_dir}")
        return
    
    print(f"Found {len(db_files)} story database(s)")
    print()
    
    results = []
    
    for db_file in sorted(db_files):
        try:
            story_id = int(db_file.stem.split('_')[1])
        except (IndexError, ValueError):
            print(f"⚠ Could not parse story ID from {db_file.name}")
            continue
        
        print(f"Checking story_{story_id}.db:")
        
        result = verify_and_migrate_single_story(story_id)
        results.append(result)
        
        if result['error']:
            print(f"  ❌ Error: {result['error']}")
        elif result['success']:
            if result['items_existed']:
                print(f"  ✅ Items table already exists ({result.get('item_count', 0)} items)")
            else:
                print(f"  ✅ Items table created successfully")
                
            print(f"  📊 Total tables: {len(result['tables_after'])}")
            print(f"     Tables: {', '.join(result['tables_after'])}")
        else:
            print(f"  ⚠ Items table could not be verified")
        
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    already_had = sum(1 for r in results if r['items_existed'])
    created = sum(1 for r in results if r['items_created'])
    failed = sum(1 for r in results if r['error'])
    
    print(f"Total databases: {total}")
    print(f"  ✅ Successful: {successful}")
    print(f"  📋 Already had items table: {already_had}")
    print(f"  ➕ Created items table: {created}")
    print(f"  ❌ Failed: {failed}")
    print()
    
    if created > 0:
        print("🎉 Items table has been added to your story databases!")
        print("   You can now use the Items view in Loreo Forge.")
    elif already_had == total:
        print("✅ All databases already have the items table.")
        print("   If you're still seeing errors, try restarting Loreo Forge.")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()