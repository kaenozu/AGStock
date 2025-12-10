import sqlite3
import time
from datetime import datetime, timedelta

import pytest

from src.persistent_cache import PersistentCache


def test_persistent_cache_uses_custom_path_and_respects_ttl(tmp_path):
    db_path = tmp_path / "custom_cache.db"
    cache = PersistentCache(ttl_hours=0.0001, db_path=str(db_path))

    cache.set("key", {"value": 1})
    assert cache.get("key") == {"value": 1}

    time.sleep(0.5)
    assert cache.get("key") is None
    assert cache.get_stats()["total_entries"] == 0


def test_clear_expired_removes_entries(tmp_path):
    db_path = tmp_path / "cache.db"
    cache = PersistentCache(ttl_hours=1, db_path=str(db_path))

    cache.set("soon_expired", "value")
    expired_time = (datetime.now() - timedelta(seconds=1)).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE cache SET expires_at = ?", (expired_time,))
        conn.commit()

    deleted = cache.clear_expired()

    assert deleted == 1
    assert cache.get_stats() == {
        "total_entries": 0,
        "valid_entries": 0,
        "expired_entries": 0,
    }
