"""
Migration Script: Add Timeline and Selective Editing Support
Run this ONCE on existing Loreo Forge installations

Adds:
- timeline_states table
- approved_sections column to chapters table
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def migrate_story_database(story_id: int, db_path: Path) -> bool:
    """Migrate a single story database"""
    
    if not db_path.exists():
        print(f"  ✗ Story {story_id} database not found at {db_path}")
        return False
    
    try:
        # Create backup first
        backup_path = db_path.parent / f"{db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"  ✓ Backup created: {backup_path.name}")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        changes_made = []
        
        # 1. Add timeline_states table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                chapter_number INTEGER NOT NULL,
                story_time TEXT,
                character_states TEXT,
                active_conflicts TEXT,
                plot_threads TEXT,
                unresolved_events TEXT,
                world_changes TEXT,
                cause_effect_chains TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(story_id, chapter_number)
            )
        """)
        changes_made.append("timeline_states table")
        
        # 2. Add timeline_states index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timeline_states_story 
            ON timeline_states(story_id, chapter_number)
        """)
        
        # 3. Check if approved_sections column exists in chapters
        cursor.execute("PRAGMA table_info(chapters)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'approved_sections' not in columns:
            cursor.execute("ALTER TABLE chapters ADD COLUMN approved_sections TEXT")
            changes_made.append("approved_sections column to chapters")
            print(f"  ✓ Added approved_sections column to chapters table")
        else:
            print(f"  • approved_sections column already exists")
        
        # 4. Ensure lore_entries has JSON columns
        cursor.execute("PRAGMA table_info(lore_entries)")
        lore_columns = [col[1] for col in cursor.fetchall()]
        
        if 'related_characters' not in lore_columns:
            cursor.execute("ALTER TABLE lore_entries ADD COLUMN related_characters TEXT")
            changes_made.append("related_characters to lore_entries")
        
        if 'related_locations' not in lore_columns:
            cursor.execute("ALTER TABLE lore_entries ADD COLUMN related_locations TEXT")
            changes_made.append("related_locations to lore_entries")
        
        conn.commit()
        conn.close()
        
        if changes_made:
            print(f"  ✓ Migrated story {story_id}: {', '.join(changes_made)}")
        else:
            print(f"  • Story {story_id} already up to date")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Migration failed for story {story_id}: {e}")
        return False


def migrate_all_stories():
    """Migrate all story databases"""
    
    print("=" * 70)
    print("Loreo Forge Migration: Timeline & Selective Editing")
    print("=" * 70)
    print()
    
    # Find data directory
    from pathlib import Path
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data" / "stories"
    
    if not data_dir.exists():
        print(f"✗ Data directory not found: {data_dir}")
        return
    
    # Find all story databases
    story_dbs = list(data_dir.glob("story_*.db"))
    
    if not story_dbs:
        print(f"No story databases found in {data_dir}")
        return
    
    print(f"Found {len(story_dbs)} story database(s)\n")
    
    success_count = 0
    
    for db_path in sorted(story_dbs):
        # Extract story ID from filename
        try:
            story_id = int(db_path.stem.split('_')[1])
        except (IndexError, ValueError):
            print(f"  ✗ Could not parse story ID from {db_path.name}")
            continue
        
        print(f"Migrating story_{story_id}.db:")
        
        if migrate_story_database(story_id, db_path):
            success_count += 1
        
        print()
    
    print("=" * 70)
    print(f"Migration complete: {success_count}/{len(story_dbs)} successful")
    print("=" * 70)
    
    if success_count < len(story_dbs):
        print("\n⚠️  Some migrations failed. Check error messages above.")
        print("    Backups were created for all databases before migration.")
    else:
        print("\n✅ All story databases successfully migrated!")
        print("    Backups were created in the stories directory.")


if __name__ == "__main__":
    print("\n⚠️  This will modify your story databases.")
    print("    Backups will be created automatically.")
    print()
    
    response = input("Continue with migration? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print()
        migrate_all_stories()
    else:
        print("\nMigration cancelled.")