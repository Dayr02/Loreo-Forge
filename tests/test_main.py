import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import LoreoForgeLauncher

class TestMainLauncher(unittest.TestCase):
    
    def setUp(self):
        self.launcher = LoreoForgeLauncher()
    
    def test_python_version_check(self):
        """Test Python version validation"""
        result = self.launcher.check_python_version()
        self.assertTrue(result)
    
    def test_directory_creation(self):
        """Test directory structure creation"""
        self.launcher.create_directories()
        
        required_dirs = [
            'data/stories',
            'data/backups',
            'logs',
            'config'
        ]
        
        for dir_path in required_dirs:
            self.assertTrue(Path(dir_path).exists())
    
    def test_logging_setup(self):
        """Test logging initialization"""
        self.launcher.setup_logging()
        self.assertIsNotNone(self.launcher.logger)

if __name__ == '__main__':
    unittest.main()