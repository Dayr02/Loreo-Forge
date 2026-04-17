"""Converts story entities into lightweight game-facing stat blocks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

from utils.unique_key import generate_unique_key


@dataclass
class GameStatBlock:
    name: str
    unique_key: str
    entity_type: str
    level: int
    power: int
    vitality: int
    tags: list[str]


class GameEntityConverter:
    """Maps story records to portable card/game data."""

    def convert(self, entity_type: str, story_slug: str, entity: Dict[str, Any]) -> Dict[str, Any]:
        name = entity.get("name") or entity.get("title") or "unnamed"
        importance = float(entity.get("importance_weight", 0.5) or 0.5)
        ascension = int(entity.get("ascension_level", 0) or 0)
        level = max(1, round(importance * 10) + ascension)
        stat_block = GameStatBlock(
            name=name,
            unique_key=entity.get("unique_key")
            or generate_unique_key(entity_type[:3], story_slug, name, entity.get("id")),
            entity_type=entity_type,
            level=level,
            power=max(1, level * 2),
            vitality=max(1, 10 + level * 3),
            tags=[entity_type, entity.get("role") or entity.get("category") or "general"],
        )
        return asdict(stat_block)
