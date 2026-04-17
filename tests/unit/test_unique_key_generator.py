from utils.unique_key import generate_unique_key


def test_unique_key_format():
    key = generate_unique_key("char", "my-story", "Aerin Vale", seed="123456")
    assert key == "char_my-story_aerin-vale_1234"


def test_unique_key_changes_with_seed():
    assert generate_unique_key("char", "story", "hero", seed="aaaa") != generate_unique_key(
        "char", "story", "hero", seed="bbbb"
    )
