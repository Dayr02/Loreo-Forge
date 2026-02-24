"""
View Verification Script
Automatically checks all views for common initialization issues

Usage: python verify_views.py
"""

import os
import sys

print("=" * 70)
print("LOREO FORGE - VIEW VERIFICATION TOOL")
print("=" * 70)

# List of expected views
EXPECTED_VIEWS = [
    'dashboard_view.py',
    'story_view.py',
    'characters_view.py',
    'world_view.py',
    'bestiary_view.py',
    'lore_view.py',
    'powers_view.py',
    'chapter_generator_view.py',
    'chapters_list_view.py',
    'settings_view.py'
]

views_dir = 'ui/views'
issues_found = 0

# Check 1: Files exist
print("\n[CHECK 1] Verifying view files exist...")
all_exist = True
for view_file in EXPECTED_VIEWS:
    filepath = os.path.join(views_dir, view_file)
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"  {status} {view_file}")
    if not exists:
        all_exist = False
        issues_found += 1

if all_exist:
    print("  ✓ All view files found")
else:
    print("  ✗ Some view files are missing!")

# Check 2: Import test
print("\n[CHECK 2] Testing view imports...")
try:
    sys.path.insert(0, os.getcwd())
    from ui.views import (
        DashboardView, StoryView, CharactersView,
        WorldView, BestiaryView, LoreView, PowersView,
        ChapterGeneratorView, ChaptersListView, SettingsView
    )
    print("  ✓ All views imported successfully")
except ImportError as e:
    print(f"  ✗ Import failed: {e}")
    issues_found += 1

# Check 3: Initialization pattern
print("\n[CHECK 3] Checking initialization patterns...")
for view_file in EXPECTED_VIEWS:
    filepath = os.path.join(views_dir, view_file)
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for __init__ method
    if 'def __init__(self):' not in content:
        print(f"  ⚠ {view_file}: No __init__ method found")
        continue
    
    # Extract __init__ method
    init_start = content.find('def __init__(self):')
    if init_start == -1:
        continue
        
    # Find super().__init__() call
    super_start = content.find('super().__init__()', init_start)
    if super_start == -1:
        print(f"  ⚠ {view_file}: No super().__init__() call found")
        issues_found += 1
        continue
    
    # Check if there are attribute assignments before super()
    init_section = content[init_start:super_start]
    has_self_assignments = 'self.' in init_section and 'def __init__(self):' in init_section
    
    if has_self_assignments:
        print(f"  ✓ {view_file}: Attributes initialized before super()")
    else:
        print(f"  ✗ {view_file}: No attributes before super() - NEEDS FIX")
        issues_found += 1

# Check 4: BaseView inheritance
print("\n[CHECK 4] Verifying BaseView inheritance...")
for view_file in EXPECTED_VIEWS:
    filepath = os.path.join(views_dir, view_file)
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for BaseView import
    if 'from .base_view import BaseView' in content or 'from base_view import BaseView' in content:
        print(f"  ✓ {view_file}: Imports BaseView")
    else:
        print(f"  ⚠ {view_file}: Doesn't import BaseView")
    
    # Check for BaseView inheritance
    if '(BaseView)' in content:
        print(f"  ✓ {view_file}: Inherits from BaseView")
    else:
        print(f"  ✗ {view_file}: Doesn't inherit from BaseView")
        issues_found += 1

# Check 5: MainWindow integration
print("\n[CHECK 5] Checking MainWindow integration...")
main_window_file = 'ui/main_window.py'
if os.path.exists(main_window_file):
    with open(main_window_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for view imports
    views_to_check = [
        ('DashboardView', 'dashboard'),
        ('StoryView', 'story'),
        ('CharactersView', 'characters'),
        ('WorldView', 'world'),
        ('BestiaryView', 'bestiary'),
        ('LoreView', 'lore'),
        ('PowersView', 'powers'),
        ('ChapterGeneratorView', 'chapter_generator'),
        ('ChaptersListView', 'chapters_list'),
        ('SettingsView', 'settings')
    ]
    
    all_integrated = True
    for view_class, view_id in views_to_check:
        # Check import
        if view_class in content:
            # Check if added to views dict
            if f"self.views['{view_id}']" in content:
                print(f"  ✓ {view_class} integrated")
            else:
                print(f"  ✗ {view_class} not added to views dict")
                all_integrated = False
                issues_found += 1
        else:
            print(f"  ✗ {view_class} not imported")
            all_integrated = False
            issues_found += 1
    
    if all_integrated:
        print("  ✓ All views integrated in MainWindow")
else:
    print(f"  ✗ MainWindow file not found")
    issues_found += 1

# Check 6: Sidebar integration
print("\n[CHECK 6] Checking Sidebar integration...")
sidebar_file = 'ui/components/sidebar.py'
if os.path.exists(sidebar_file):
    with open(sidebar_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_nav_items = [
        'dashboard', 'story', 'characters', 'world', 'bestiary',
        'lore', 'powers', 'chapter_generator', 'chapters_list', 'settings'
    ]
    
    all_found = True
    for nav_id in required_nav_items:
        if f'"{nav_id}"' in content or f"'{nav_id}'" in content:
            print(f"  ✓ '{nav_id}' in sidebar")
        else:
            print(f"  ✗ '{nav_id}' missing from sidebar")
            all_found = False
            issues_found += 1
    
    if all_found:
        print("  ✓ All navigation items in Sidebar")
else:
    print(f"  ✗ Sidebar file not found")
    issues_found += 1

# Summary
print("\n" + "=" * 70)
if issues_found == 0:
    print("✓ ALL CHECKS PASSED - Views are properly configured!")
    print("  You can now run: python main.py")
else:
    print(f"✗ FOUND {issues_found} ISSUE(S) - Review and fix before running app")
    print("  See the detailed output above for specific issues")
print("=" * 70)

sys.exit(0 if issues_found == 0 else 1)