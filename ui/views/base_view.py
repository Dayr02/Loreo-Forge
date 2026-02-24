"""
Base View Class
Shared functionality for all views
"""

from PyQt5.QtWidgets import QWidget, QMessageBox
from utils.logger import LoggerMixin


class BaseView(QWidget, LoggerMixin):
    """
    Base class for all application views
    Provides common functionality for CRUD operations and UI management
    """
    
    def __init__(self):
        """
        Initialize the base view
        Child classes should initialize their attributes BEFORE calling super().__init__()
        """
        super().__init__()
        
        # Base properties
        self._is_modified = False
        self._current_story_id = None
        self._view_name = "Base View"
        
        # Only call setup_ui if the child class hasn't already done so
        if not hasattr(self, '_ui_setup_complete'):
            self.setup_ui()
            self._ui_setup_complete = True
        
    def setup_ui(self):
        """
        Set up the view's user interface
        Should be overridden by child classes
        """
        pass
        
    def load_data(self):
        """
        Load data into the view
        Should be overridden by child classes
        """
        pass
        
    def save_data(self):
        """
        Save current view data
        Should be overridden by child classes
        """
        pass
    
    def clear_form(self):
        """
        Clear the detail form and hide it
        Should be overridden by child classes to clear their specific forms
        """
        # Default implementation - child classes should override
        pass
        
    def refresh(self):
        """
        Refresh the view's data
        Default: clears form, then loads data
        """
        self.clear_form()  # Clear form first
        self.load_data()   # Then load data
        
    def validate_input(self):
        """
        Validate user input before saving
        Should be overridden by child classes
        
        Returns:
            bool: True if valid, False otherwise
        """
        return True
        
    # Dialog helpers
    def show_error(self, message, title="Error"):
        """Show an error message dialog"""
        QMessageBox.critical(self, title, message)
        self.log_error(f"{title}: {message}")
        
    def show_warning(self, message, title="Warning"):
        """Show a warning message dialog"""
        QMessageBox.warning(self, title, message)
        self.log_warning(f"{title}: {message}")
        
    def show_success(self, message, title="Success"):
        """Show a success message dialog"""
        QMessageBox.information(self, title, message)
        self.log_info(f"{title}: {message}")
        
    def show_info(self, message, title="Information"):
        """Show an information message dialog"""
        QMessageBox.information(self, title, message)
        self.log_info(f"{title}: {message}")
        
    def confirm_action(self, title, message):
        """
        Show a confirmation dialog
        
        Returns:
            bool: True if user confirmed, False otherwise
        """
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes
        
    # Properties
    @property
    def is_modified(self):
        """Check if view has unsaved changes"""
        return self._is_modified
        
    def mark_modified(self):
        """Mark view as having unsaved changes"""
        self._is_modified = True
        
    def mark_saved(self):
        """Mark view as having no unsaved changes"""
        self._is_modified = False
        
    @property
    def current_story_id(self):
        """Get the current story ID"""
        return self._current_story_id
        
    @current_story_id.setter
    def current_story_id(self, value):
        """Set the current story ID and trigger refresh"""
        old_value = self._current_story_id
        self._current_story_id = value
        
        # If story ID changed, clear the form
        if old_value != value:
            self.clear_form()
        
    @property
    def view_name(self):
        """Get the view name"""
        return self._view_name
        
    @view_name.setter
    def view_name(self, value):
        """Set the view name"""
        self._view_name = value
        
    def prompt_save_changes(self):
        """
        Prompt user to save changes if modified
        
        Returns:
            bool: True if should continue (saved or discarded), False if cancelled
        """
        if self._is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_data()
                return True
            elif reply == QMessageBox.Discard:
                return True
            else:  # Cancel
                return False
        return True