import sys

required = ['yaml', 'PyQt5', 'requests', 'jinja2']
missing = []

for module in required:
    try:
        __import__(module)
        print(f"✓ {module} is installed")
    except ImportError:
        print(f"✗ {module} is MISSING")
        missing.append(module)

if missing:
    print(f"\nMissing packages: {', '.join(missing)}")
    print(f"Run: pip install {' '.join(missing)}")
else:
    print("\n✓ All critical dependencies are installed!")