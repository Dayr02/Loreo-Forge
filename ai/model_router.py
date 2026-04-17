"""Simple task-to-model routing for Loreo Forge."""

from __future__ import annotations

from typing import Dict

from config.settings import settings


class ModelRouter:
    """Chooses a preferred local model for a task family."""

    DEFAULT_ROUTES: Dict[str, str] = {
        "chapter_generation": "llama3.1:70b",
        "chat": "llama3.1:8b",
        "brainstorming": "mistral-nemo:12b",
        "summarization": "llama3.1:8b",
    }

    def route(self, task_type: str) -> str:
        return self.DEFAULT_ROUTES.get(task_type, settings.default_model)
