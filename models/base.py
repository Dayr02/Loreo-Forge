"""
Base Model Class for Loreo Forge
Provides ORM-style object-oriented interface to database
"""

from typing import Dict, Any, Optional, List, Type, TypeVar
from datetime import datetime
from database import db_manager
from utils.logger import LoggerMixin


T = TypeVar('T', bound='BaseModel')


class BaseModel(LoggerMixin):
    """
    Base class for all data models
    Provides common CRUD operations and validation
    """
    
    # Table name - must be overridden by subclasses
    _table_name: str = None
    
    # Fields that should not be included in to_dict() by default
    _exclude_fields: List[str] = []
    
    def __init__(self, story_id: int, **kwargs):
        """
        Initialize model instance

        Args:
            story_id: Story identifier
            **kwargs: Field values
        """
        self.story_id = story_id
        # Remove story_id from kwargs if present to avoid conflict
        kwargs.pop('story_id', None)
        self.id: Optional[int] = kwargs.get('id')
        self._data: Dict[str, Any] = kwargs
        # Add story_id to data for consistency
        self._data['story_id'] = story_id
        self._modified_fields: set = set()
        self._is_new = self.id is None
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        class_name = self.__class__.__name__
        if self.id:
            return f"<{class_name} id={self.id}>"
        return f"<{class_name} (unsaved)>"
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return self.__repr__()
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to data fields"""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return self._data.get(name)
    
    def __setattr__(self, name: str, value: Any):
        """Track modified fields for efficient updates"""
        if name.startswith('_') or name in ['story_id', 'id']:
            super().__setattr__(name, value)
        else:
            if name not in self._data or self._data[name] != value:
                self._data[name] = value
                self._modified_fields.add(name)
    
    @classmethod
    def get_table_name(cls) -> str:
        """Get the database table name for this model"""
        if cls._table_name is None:
            raise NotImplementedError(f"{cls.__name__} must define _table_name")
        return cls._table_name
    
    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================
    
    def save(self) -> bool:
        """
        Persist model to database (insert or update)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.validate():
            self.logger.error(f"Validation failed for {self.__class__.__name__}")
            return False
        
        try:
            if self._is_new:
                # Insert new record
                data = self._prepare_data_for_save()
                record_id = db_manager.create_record(
                    self.story_id,
                    self.get_table_name(),
                    data
                )
                
                if record_id:
                    self.id = record_id
                    self._data['id'] = record_id
                    self._is_new = False
                    self._modified_fields.clear()
                    self.logger.info(f"Created {self.__class__.__name__} with id={record_id}")
                    return True
                else:
                    return False
            else:
                # Update existing record
                if not self._modified_fields:
                    self.logger.debug(f"No changes to save for {self.__class__.__name__} id={self.id}")
                    return True
                
                update_data = {field: self._data[field] for field in self._modified_fields}
                result = db_manager.update_record(
                    self.story_id,
                    self.get_table_name(),
                    self.id,
                    update_data
                )
                
                if result:
                    self._modified_fields.clear()
                    self.logger.info(f"Updated {self.__class__.__name__} id={self.id}")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to save {self.__class__.__name__}: {e}")
            return False
    
    def delete(self) -> bool:
        """
        Remove model from database
        
        Returns:
            True if successful, False otherwise
        """
        if self._is_new:
            self.logger.warning(f"Cannot delete unsaved {self.__class__.__name__}")
            return False
        
        try:
            result = db_manager.delete_record(
                self.story_id,
                self.get_table_name(),
                self.id
            )
            
            if result:
                self.logger.info(f"Deleted {self.__class__.__name__} id={self.id}")
                self._is_new = True
                self.id = None
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to delete {self.__class__.__name__}: {e}")
            return False
    
    def refresh(self) -> bool:
        """
        Reload data from database
        
        Returns:
            True if successful, False otherwise
        """
        if self._is_new:
            self.logger.warning(f"Cannot refresh unsaved {self.__class__.__name__}")
            return False
        
        try:
            data = db_manager.get_record(
                self.story_id,
                self.get_table_name(),
                self.id
            )
            
            if data:
                self._data = data
                self._modified_fields.clear()
                self.logger.debug(f"Refreshed {self.__class__.__name__} id={self.id}")
                return True
            else:
                self.logger.warning(f"{self.__class__.__name__} id={self.id} not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to refresh {self.__class__.__name__}: {e}")
            return False
    
    @classmethod
    def get_by_id(cls: Type[T], story_id: int, record_id: int) -> Optional[T]:
        """
        Retrieve a model instance by ID
        
        Args:
            story_id: Story identifier
            record_id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        try:
            data = db_manager.get_record(story_id, cls.get_table_name(), record_id)
            if data:
                data_copy = data.copy()
                data_copy.pop('story_id', None)  # Remove story_id to avoid duplication
                return cls(story_id, **data_copy)
            return None
        except Exception as e:
            logger = LoggerMixin()
            logger.logger.error(f"Failed to get {cls.__name__} by id: {e}")
            return None
    
    @classmethod
    def get_all(
        cls: Type[T],
        story_id: int,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        order: str = 'ASC',
        limit: Optional[int] = None
    ) -> List[T]:
        """
        Retrieve multiple model instances
        
        Args:
            story_id: Story identifier
            filters: Optional filter criteria
            sort_by: Column to sort by
            order: Sort order ('ASC' or 'DESC')
            limit: Maximum number of records
            
        Returns:
            List of model instances
        """
        try:
            records = db_manager.get_all_records(
                story_id,
                cls.get_table_name(),
                filters=filters,
                sort_by=sort_by,
                order=order,
                limit=limit
            )
            # Remove story_id from record dict before passing
            # because we're already passing it as positional argument
            instances = []
            for record in records:
                # Make a copy and remove story_id to avoid duplicate
                record_copy = record.copy()
                record_copy.pop('story_id', None)
                instances.append(cls(story_id, **record_copy))
            return instances
        except Exception as e:
            logger = LoggerMixin()
            logger.logger.error(f"Failed to get all {cls.__name__}: {e}")
            return []
    
    # ========================================================================
    # DATA CONVERSION
    # ========================================================================
    
    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model to dictionary for JSON serialization
        
        Args:
            exclude_fields: Additional fields to exclude
            
        Returns:
            Dictionary of model data
        """
        exclude = set(self._exclude_fields)
        if exclude_fields:
            exclude.update(exclude_fields)
        
        result = {}
        for key, value in self._data.items():
            if key not in exclude:
                # Convert datetime objects to ISO format strings
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        
        return result
    
    @classmethod
    def from_dict(cls: Type[T], story_id: int, data: Dict[str, Any]) -> T:
        """
        Create model instance from dictionary
        
        Args:
            story_id: Story identifier
            data: Dictionary of field values
            
        Returns:
            Model instance
        """
        return cls(story_id, **data)
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> bool:
        """
        Validate model data before saving
        Override in subclasses for custom validation
        
        Returns:
            True if valid, False otherwise
        """
        # Base validation - ensure story_id is set
        if not self.story_id:
            self.logger.error("story_id is required")
            return False
        
        return True
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _prepare_data_for_save(self) -> Dict[str, Any]:
        """
        Prepare data dictionary for database insertion
        Excludes id and other non-saveable fields
        
        Returns:
            Dictionary ready for database insertion
        """
        data = self._data.copy()
        
        # Remove id if present (auto-generated)
        data.pop('id', None)
        
        # Ensure story_id is included
        data['story_id'] = self.story_id
        
        return data
    
    def is_new(self) -> bool:
        """Check if this is a new unsaved record"""
        return self._is_new
    
    def is_modified(self) -> bool:
        """Check if any fields have been modified"""
        return len(self._modified_fields) > 0
    
    def get_modified_fields(self) -> set:
        """Get set of modified field names"""
        return self._modified_fields.copy()
    
    def mark_as_saved(self):
        """Mark instance as saved (clear modified fields)"""
        self._modified_fields.clear()
        self._is_new = False