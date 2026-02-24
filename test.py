"""
Context Selection Verification Script - Final Test
Run this AFTER applying the ai_controller fix to verify items work
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import db_manager
from ai.context_manager import context_manager
from models import Item


def test_item_in_prompt():
    """Critical test: Verify item details actually appear in AI prompt"""
    print("\n" + "=" * 70)
    print("CRITICAL TEST: Item Details in AI Prompt")
    print("=" * 70)
    
    story_id = 1
    
    # Create test item
    test_item = Item(
        story_id,
        name="Flamebrand Sword",
        type="Weapon",
        rarity="Legendary",
        description="A sword wreathed in eternal flames",
        properties="Burns with magical fire, cannot be extinguished",
        powers="Deals fire damage, immune to ice attacks",
        current_owner="Hero",
        current_location="Castle Armory"
    )
    
    if not test_item.save():
        print("❌ Failed to create test item")
        return False
    
    print(f"✓ Created test item: {test_item.name} (ID: {test_item.id})")
    
    try:
        from controllers.ai_controller import ai_controller
        
        # Build context with this item
        selected_ids = {
            'items': [test_item.id],
            'characters': [],
            'locations': [],
            'lore': [],
            'power_systems': [],
            'bestiary': [],
            'organizations': []
        }
        
        context = ai_controller._create_readonly_context_snapshot(
            story_id,
            chapter_number=1,
            selected_context=selected_ids
        )
        
        # Build prompt
        prompt = ai_controller._build_chapter_prompt(
            context=context,
            chapter_number=1,
            title="Test Chapter",
            target_word_count=3000,
            pov_character="Third-person",
            mood="Epic",
            plot_points=f"The hero wields the {test_item.name}",
            style_instructions="",
            story_progression_prompt=f"Introduce the legendary {test_item.name}",
            generation_type="full_chapter"
        )
        
        print(f"\n✓ Prompt generated: {len(prompt)} characters")
        
        # Check for item details
        checks = {
            'Item name': test_item.name in prompt,
            'Item properties': 'Burns with magical fire' in prompt,
            'Item powers': 'Deals fire damage' in prompt or 'fire damage' in prompt.lower(),
            'Item owner': test_item.current_owner in prompt,
            'Item description': 'flames' in prompt.lower() or 'fire' in prompt.lower()
        }
        
        print("\nItem Detail Checks:")
        print("─" * 70)
        
        all_passed = True
        for check_name, passed in checks.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {check_name}")
            all_passed = all_passed and passed
        
        # Show prompt excerpt
        if any(checks.values()):
            print("\n📜 Prompt excerpt showing item details:")
            print("─" * 70)
            lines = prompt.split('\n')
            for i, line in enumerate(lines):
                if test_item.name in line or 'flame' in line.lower():
                    start = max(0, i - 1)
                    end = min(len(lines), i + 4)
                    for j in range(start, end):
                        prefix = "→ " if j == i else "  "
                        print(f"{prefix}{lines[j][:80]}")
                    print("─" * 70)
                    break
        
        # Cleanup
        test_item.delete()
        print(f"\n✓ Test item deleted")
        
        if all_passed:
            print("\n" + "🎉" * 35)
            print("✅ ALL CHECKS PASSED!")
            print("Items are correctly included in AI prompts")
            print("AI will receive full item details and use them correctly")
            print("🎉" * 35)
        else:
            print("\n" + "⚠️" * 35)
            print("❌ SOME CHECKS FAILED")
            print("Item details may not be fully included in prompts")
            print("⚠️" * 35)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        try:
            test_item.delete()
        except:
            pass
        return False


def main():
    """Run the critical test"""
    print("\n" + "🔥" * 35)
    print("FINAL VERIFICATION TEST")
    print("Testing if items are included in AI prompts")
    print("🔥" * 35)
    
    success = test_item_in_prompt()
    
    if success:
        print("\n✅ VERIFICATION COMPLETE - System is working correctly!")
        print("\nYou can now:")
        print("  1. Select items in Chapter Generator Context Selection")
        print("  2. Generate chapters with those items")
        print("  3. AI will use item details and not contradict them")
    else:
        print("\n❌ VERIFICATION FAILED")
        print("\nPlease ensure you applied the fix to ai_controller.py:")
        print("  - Added item_details section after power_systems")
        print("  - Restart application and try again")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()