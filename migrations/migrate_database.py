"""Apply Loreo Forge schema migrations to master and story databases."""

from database.migrations import db_migrator


def migrate_all_databases() -> dict:
    results = db_migrator.check_and_migrate_all_stories()
    db_migrator.migrate_master_database()
    return results


if __name__ == "__main__":
    print(migrate_all_databases())
