"""
Master Database Manager
Handles the central stories registry (separate from per-story databases)
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.settings import settings
from database import schema
from utils.logger import LoggerMixin


class MasterDatabase(LoggerMixin):
    """
    Central database for managing the stories registry
    Separate from individual story databases
    """
    
    def __init__(self):
        """Initialize master database connection"""
        self.db_path = settings.DATA_DIR / "loreo_master.db"
        self._connection = None
        self._initialize_database()
        self.log_info("MasterDatabase initialized")
    
    def _initialize_database(self):
        """Create master database and stories table"""
        try:
            # Ensure data directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create connection
            self._connection = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            
            # Create stories table
            self._create_schema()
            
            self.log_info(f"Master database initialized at {self.db_path}")
            
        except sqlite3.Error as e:
            self.log_error(f"Failed to initialize master database: {e}")
            raise
    
    def _create_schema(self):
        """Create the stories registry schema"""
        from database.schema import DatabaseSchema

        # CREATE THE SCHEMA OBJECT
        schema = DatabaseSchema()

        if schema.create_master_schema(self._connection):
            self.log_debug("Master database schema created")
        else:
            self.log_warning("Master database schema could not be updated; continuing with existing database state")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get the master database connection"""
        return self._connection
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Execute a query and fetch one result
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Single row or None
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            self.log_error(f"fetch_one error: {e}")
            return None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute a query and fetch all results
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of rows
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            self.log_error(f"fetch_all error: {e}")
            return []
    
    def execute(self, query: str, params: tuple = ()) -> int:
        """
        Execute a query and return the last row ID
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Last inserted row ID
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            self._connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            self.log_error(f"execute error: {e}")
            self._connection.rollback()
            raise
    
    def close(self):
        """Close the master database connection"""
        if self._connection:
            self._connection.close()
            self.log_info("Master database connection closed")


# Global master database instance
master_db = MasterDatabase()
