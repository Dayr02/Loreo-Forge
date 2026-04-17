from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from config.settings import settings
from database import db_manager


@pytest.fixture()
def isolated_paths():
    root = Path(tempfile.mkdtemp())
    original = {
        "DATA_DIR": settings.DATA_DIR,
        "STORIES_DIR": settings.STORIES_DIR,
        "LOGS_DIR": settings.LOGS_DIR,
        "BRIDGE_DIR": settings.BRIDGE_DIR,
        "BRIDGE_OUTBOUND_DIR": settings.BRIDGE_OUTBOUND_DIR,
        "BRIDGE_INBOUND_DIR": settings.BRIDGE_INBOUND_DIR,
        "GAME_STATE_DIR": settings.GAME_STATE_DIR,
        "BACKUPS_DIR": settings.BACKUPS_DIR,
    }
    settings.DATA_DIR = root / "data"
    settings.STORIES_DIR = settings.DATA_DIR / "stories"
    settings.LOGS_DIR = root / "logs"
    settings.BRIDGE_DIR = settings.DATA_DIR / "bridge"
    settings.BRIDGE_OUTBOUND_DIR = settings.BRIDGE_DIR / "outbound"
    settings.BRIDGE_INBOUND_DIR = settings.BRIDGE_DIR / "inbound"
    settings.GAME_STATE_DIR = settings.DATA_DIR / "game_state"
    settings.BACKUPS_DIR = settings.DATA_DIR / "backups"
    settings.ensure_directories()
    yield root
    db_manager.close_all_connections()
    for key, value in original.items():
        setattr(settings, key, value)
    shutil.rmtree(root, ignore_errors=True)
