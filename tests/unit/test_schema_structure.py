from database import db_manager
from database.schema import DatabaseSchema


def test_story_schema_initializes_current_version(isolated_paths):
    assert db_manager.initialize_database(10) is True
    conn = db_manager.get_connection(10)
    schema = DatabaseSchema()
    assert schema.verify_schema(conn) is True
    assert schema.get_schema_version(conn) == DatabaseSchema.SCHEMA_VERSION
