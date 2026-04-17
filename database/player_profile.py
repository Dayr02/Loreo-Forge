"""Player profile helpers for the master database."""

from __future__ import annotations

from typing import Optional

from database.master_db import master_db


def get_player_profile() -> Optional[dict]:
    row = master_db.fetch_one("SELECT * FROM player_profile ORDER BY id LIMIT 1")
    return dict(row) if row else None
