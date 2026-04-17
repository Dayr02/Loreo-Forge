"""Human-readable unique key generation helpers."""

from __future__ import annotations

import re
from typing import Optional
from uuid import uuid4


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower())
    return value.strip("-") or "unnamed"


def generate_unique_key(prefix: str, story_slug: str, name: str, seed: Optional[object] = None) -> str:
    suffix_source = str(seed) if seed is not None else uuid4().hex
    suffix = re.sub(r"[^a-zA-Z0-9]", "", suffix_source.lower())[:4].ljust(4, "0")
    return f"{slugify(prefix)}_{slugify(story_slug)}_{slugify(name)}_{suffix}"
