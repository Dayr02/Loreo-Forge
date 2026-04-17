from database import db_manager


def test_story_crud_and_sequence_validation(isolated_paths):
    assert db_manager.initialize_database(21) is True

    char_id = db_manager.create_entity("characters", 21, {"name": "Kade", "role": "lead"})
    assert char_id is not None

    chapter_1 = db_manager.create_entity(
        "chapters",
        21,
        {"chapter_number": 1, "title": "Start", "content": "Alpha", "word_count": 1},
    )
    chapter_2 = db_manager.create_entity(
        "chapters",
        21,
        {"chapter_number": 2, "title": "Next", "content": "Beta", "word_count": 1},
    )

    record = db_manager.get_entity("characters", char_id, 21)
    assert record["name"] == "Kade"
    assert db_manager.update_entity("characters", char_id, 21, {"status": "active"}) is True
    assert db_manager.get_entity("characters", char_id, 21)["status"] == "active"
    assert db_manager.delete_entity("chapters", chapter_2, 21) is True

    valid, missing = db_manager.verify_chapter_sequence(21)
    assert valid is False
    assert missing == [2]
    assert chapter_1 is not None
