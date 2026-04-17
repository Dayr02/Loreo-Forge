"""Persists session lifecycle events between Godot and SQLite."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from database import db_manager
from utils.logger import LoggerMixin


class GameSessionManager(LoggerMixin):
    """Reads and writes session payloads for story-linked game modes."""

    def create_session(
        self,
        story_id: int,
        mode_name: str,
        state: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        return db_manager.create_entity(
            "game_sessions",
            story_id,
            {
                "mode_name": mode_name,
                "session_state": json.dumps(state or {}),
                "status": "active",
            },
        )

    def save_session_state(self, story_id: int, session_id: int, state: Dict[str, Any]) -> bool:
        return db_manager.update_entity(
            "game_sessions",
            session_id,
            story_id,
            {"session_state": json.dumps(state), "status": "saved"},
        )
