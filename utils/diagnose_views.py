"""
Diagnostic Script for Loreo Forge Views
Run this script to identify issues with view imports and setup

Usage: python diagnose_views.py
"""

import sys
import os

print("=" * 60)
print("Loreo Forge View Diagnostics")
print("=" * 60)

# Test 1: Check if all view files exist
print("\n[TEST 1] Checking view files...")
view_files = [
    'ui/views/base_view.py',
    'ui/views/dashboard_view.py',
    'ui/views/story_view.py',
    'ui/views/characters_view.py',
    'ui/views/world_view.py',
    'ui/views/bestiary_view.py',
    'ui/views/lore_view.py',
    'ui/views/powers_view.py',
    'ui/views/chapter_generator_view.py',
    'ui/views/chapters_list_view.py',
    'ui/views/settings_view.py',
]

all_exist = True
for file in view_files:
    exists = os.path.exists(file)
    status = "✓" if exists else "✗"
    print(f"  {status} {file}")
    if not exists:
        all_exist = False

if not all_exist:
    print("\n⚠️  Some view files are missing!")
    print("   Create missing files before proceeding.")
else:
    print("\n✓ All view files exist")

# Test 2: Check if views can be imported
print("\n[TEST 2] Testing view imports...")
try:
    from ui.views import (
        BaseView,
        DashboardView,
        StoryView,
        CharactersView,
        WorldView,
        BestiaryView,
        LoreView,
        PowersView,
        ChapterGeneratorView,
        ChaptersListView,
        SettingsView
    )
    print("✓ All views imported successfully")
    
    # List what was imported
    views = {
        'BaseView': BaseView,
        'DashboardView': DashboardView,
        'StoryView': StoryView,
        'CharactersView': CharactersView,
        'WorldView': WorldView,
        'BestiaryView': BestiaryView,
        'LoreView': LoreView,
        'PowersView': PowersView,
        'ChapterGeneratorView': ChapterGeneratorView,
        'ChaptersListView': ChaptersListView,
        'SettingsView': SettingsView,
    }
    
    print("\n[TEST 3] Instantiating views...")
    for name, ViewClass in views.items():
        if name == 'BaseView':
            continue  # Skip base class
        try:
            view = ViewClass()
            print(f"  ✓ {name} instantiated successfully")
        except Exception as e:
            print(f"  ✗ {name} failed: {e}")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check sidebar
print("\n[TEST 4] Testing sidebar...")
try:
    from ui.components.sidebar import Sidebar
    sidebar = Sidebar()
    print(f"✓ Sidebar created successfully")
    print(f"  Buttons: {list(sidebar.buttons.keys())}")
except Exception as e:
    print(f"✗ Sidebar failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check if ui/__init__.py exists and is correct
print("\n[TEST 5] Checking ui/views/__init__.py...")
init_file = 'ui/views/__init__.py'
if os.path.exists(init_file):
    print(f"✓ {init_file} exists")
    with open(init_file, 'r') as f:
        content = f.read()
        required_imports = [
            'BaseView',
            'DashboardView',
            'StoryView',
            'CharactersView',
            'WorldView',
            'BestiaryView',
            'LoreView',
            'PowersView',
            'ChapterGeneratorView',
            'ChaptersListView',
            'SettingsView'
        ]
        for imp in required_imports:
            if imp in content:
                print(f"  ✓ {imp} found in __init__.py")
            else:
                print(f"  ✗ {imp} MISSING from __init__.py")
else:
    print(f"✗ {init_file} does not exist")

# Test 5: Check main_window.py for switch_view method
print("\n[TEST 6] Checking MainWindow.switch_view method...")
main_window_file = 'ui/main_window.py'
if os.path.exists(main_window_file):
    with open(main_window_file, 'r') as f:
        content = f.read()
        if 'def switch_view(self' in content:
            print("✓ switch_view method found")
        else:
            print("✗ switch_view method NOT FOUND")
            print("  You need to add the switch_view method to MainWindow")
        
        if 'self.sidebar.view_changed.connect' in content:
            print("✓ Sidebar signal connection found")
        else:
            print("✗ Sidebar signal connection NOT FOUND")
            print("  Add: self.sidebar.view_changed.connect(self.switch_view)")
        
        if "self.views = {}" in content:
            print("✓ self.views dictionary initialization found")
        else:
            print("✗ self.views dictionary initialization NOT FOUND")
            print("  Add: self.views = {} in __init__ method")

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)