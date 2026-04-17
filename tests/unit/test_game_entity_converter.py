from core.game_entity_converter import GameEntityConverter


def test_converter_builds_stat_block():
    converter = GameEntityConverter()
    payload = converter.convert(
        "characters",
        "starfall",
        {"id": 7, "name": "Nyra", "importance_weight": 0.8, "ascension_level": 1},
    )
    assert payload["name"] == "Nyra"
    assert payload["entity_type"] == "characters"
    assert payload["level"] >= 1
    assert payload["unique_key"].startswith("cha_starfall_nyra_")
