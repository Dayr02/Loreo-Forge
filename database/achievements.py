"""Achievement helpers for the master database."""

from __future__ import annotations

from typing import List

from database.master_db import master_db


def list_achievement_definitions() -> List[dict]:
    return [dict(row) for row in master_db.fetch_all("SELECT * FROM achievements_definitions")]
