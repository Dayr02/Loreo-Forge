"""Processes inbound events from the Godot bridge."""

from __future__ import annotations

import json
from typing import Any, Dict

from database.master_db import master_db
from utils.logger import LoggerMixin


class BridgeEventHandler(LoggerMixin):
    """Applies inbound bridge events to the Python data layer."""

    def handle_event(self, event: Dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        if event_type == "xp_earned":
            self._apply_xp(payload.get("amount", 0))
        elif event_type == "game_state_save":
            self.log_info("Received game state save event")
        elif event_type == "navigation_request":
            self.log_info(f"Navigation requested: {json.dumps(payload)}")

    def _apply_xp(self, amount: int) -> None:
        profile = master_db.fetch_one("SELECT id, xp FROM player_profile ORDER BY id LIMIT 1")
        if not profile:
            return
        new_xp = int(profile["xp"] or 0) + int(amount or 0)
        master_db.execute(
            "UPDATE player_profile SET xp = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_xp, profile["id"]),
        )
