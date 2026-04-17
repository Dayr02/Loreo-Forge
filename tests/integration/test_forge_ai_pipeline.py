from ai.context_manager import ContextManager
from ai.model_router import ModelRouter
from ai.prompt_builder import PromptBuilder
from database import db_manager


def test_context_prompt_and_routing_pipeline(isolated_paths):
    assert db_manager.initialize_database(30) is True
    db_manager.create_entity("characters", 30, {"name": "Ari", "role": "hero"})
    db_manager.create_entity(
        "chapters",
        30,
        {"chapter_number": 1, "title": "Arrival", "content": "The city wakes.", "word_count": 3},
    )

    context = ContextManager().build_chapter_context(30, 2)
    prompt = PromptBuilder().build_prompt_from_string(
        "Story: {{ story_metadata.title }} | Characters: {{ active_characters|length }}",
        context,
    )
    model = ModelRouter().route("chapter_generation")

    assert "Characters: 1" in prompt
    assert model == "llama3.1:70b"
