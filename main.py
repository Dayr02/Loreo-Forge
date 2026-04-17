"""
Loreo Forge - AI-Powered Story Generation Platform
Main application entry point
"""

import sys
import os
from pathlib import Path

from database import db_manager
from utils import logger

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from utils.logger import setup_logger
from ai import ollama_client


def check_dependencies():
    """Verify that all required dependencies are available"""
    missing = []
    
    try:
        import PyQt5
    except ImportError:
        missing.append("PyQt5")
    
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    try:
        import yaml
    except ImportError:
        missing.append("PyYAML")
    
    if missing:
        print("ERROR: Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nPlease run: pip install -r requirements.txt")
        return False
    
    return True


def check_ollama_connection():
    """Check if Ollama is running and accessible"""
    try:
        import requests
        response = requests.get(
            f"{settings.OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            print(f"✓ Ollama is running at {settings.OLLAMA_BASE_URL}")
            print(f"  Available models: {', '.join(models) if models else 'None'}")
            
            # Check for required models
            # (Future development will include more local models.)
            required = ['llama3.1:8b', 'llama3.1:70b']
            missing = [m for m in required if m not in models]
            
            if missing:
                print(f"\n⚠ Missing recommended models:")
                for model in missing:
                    print(f"  - {model}")
                print(f"\nTo install: ollama pull <model_name>")
            
            return True
        else:
            return False
    except Exception as e:
        print(f"⚠ Could not connect to Ollama at {settings.OLLAMA_BASE_URL}")
        print(f"  Error: {e}")
        print("\nOllama is required for AI generation features.")
        print("Please ensure Ollama is running and try again.")
        return False


def main():
    """Main application entry point"""
    print("=" * 60)
    print("🔥 Loreo Forge - AI-Powered Story Generation Platform")
    print("=" * 60)
    print()
    
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Loreo Forge application")
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✓ All dependencies found")
    
    # Check Ollama connection
    print("\nChecking Ollama connection...")
    ollama_available = check_ollama_connection()
    if not ollama_available:
        print("\n⚠ Warning: Continuing without Ollama connection")
        print("  AI features will not be available until Ollama is running")
    
    # Ensure directories exist
    print("\nInitializing directories...")
    settings.ensure_directories()
    print("✓ Directory structure created")
    
    # Test database connection
    print("\nTesting database system...")
    try:
        from database import db_manager
        # Try to initialize a test database
        test_story_id = 1
        if not settings.get_story_db_path(test_story_id).exists():
            db_manager.initialize_database(test_story_id)
        print("✓ Database system operational")
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        print(f"✗ Database error: {e}")
    
    from database.migrations import db_migrator

    # Auto-migrate existing databases
    print("\nChecking for database updates...")
    try:
        migration_results = db_migrator.check_and_migrate_all_stories()
        db_migrator.migrate_master_database()

        if migration_results['migrated'] > 0:
            print(f"✓ Updated {migration_results['migrated']} story database(s)")

        # FIX: Changed 'already_updated' to 'skipped' (correct dict key)
        if migration_results['skipped'] > 0:
            print(f"  {migration_results['skipped']} database(s) already current")

        if migration_results['errors']:
            print(f"⚠ {len(migration_results['errors'])} migration error(s)")
            for error in migration_results['errors']:
                print(f"  - {error}")
        
        # Show total processed
        if migration_results['total'] > 0:
            print(f"  Processed {migration_results['total']} database(s) total")
        else:
            print("  No story databases found to migrate")
            
    except Exception as e:
        logger.error(f"Migration check failed: {e}")
        print(f"⚠ Migration check failed: {e}")
        import traceback
        traceback.print_exc()

    from core.story_manager import StoryManager

    # Initialize story manager
    print("\nInitializing story manager...")
    try:
        story_manager = StoryManager(db_manager)
        print("✓ Story manager initialized")
        
        # Get active story
        active_story = story_manager.get_active_story()
        if active_story:
            print(f"  Active story: {active_story['title']}")
        else:
            print("  No active story")
    except Exception as e:
        logger.error(f"Story manager initialization failed: {e}")
        print(f"✗ Story manager error: {e}")

    # Test AI client 
    if ollama_available:
        print("\nTesting AI client...")
        try:
            test_result = ollama_client.test_connection()
            if test_result:
                print("✓ AI client operational")
                
                # Show current model
                current_model = ollama_client.get_current_model()
                print(f"  Current model: {current_model}")
        except Exception as e:
            logger.error(f"AI client test failed: {e}")
            print(f"✗ AI client error: {e}")
    
    # Try to initialize UI application 
    print("\nInitializing application...")
    try:
        from core.application import LoreoForgeApp
        from ui import MainWindow
        
        # Create and run application
        app = LoreoForgeApp(sys.argv)
        logger.info("Application initialized successfully")
        
        # Create main window
        main_window = MainWindow()
        app.set_main_window(main_window)
        
        # Show window
        main_window.show()
        
        print("✓ Application ready")
        print("\n🎉 Loreo Forge is now running!")
        print("=" * 60)
        
        # Start the event loop
        sys.exit(app.exec_())
        
    except ImportError as e:
        # Not yet fully implemented
        print(f"\n⚠ UI component not available: {e}")
        print("\nPhase Status:")
        print("  ✓ Phase 0: Foundation complete")
        print("  ✓ Phase 1: Database layer complete")
        print("  ✓ Phase 2: AI engine core complete")
        print("  ⧗ Phase 3: UI framework - in progress")
        print("\nCurrent capabilities:")
        print("  • Database operations (CRUD)")
        print("  • Model classes (Story, Character, etc.)")
        print("  • Ollama AI client")
        print("  • Prompt builder & context manager")
        print("  • Theme engine ready")
        logger.info("Phase 3 in progress - some UI components pending")


if __name__ == "__main__":
    main()
