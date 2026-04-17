"""Serializable game card model for V2.0 entities."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class GameCard:
    unique_key: str
    title: str
    card_type: str
    ascension_level: int = 0
    stats: Dict[str, int] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)
