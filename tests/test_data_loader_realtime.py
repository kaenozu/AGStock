import pandas as pd
import pytest

from src import data_loader


def test_fetch_realtime_data_uses_cache(monkeypatch):
    calls = {"count": 0}

    def fake_download(ticker, period, interval, auto_adjust, progress):
        calls["count"] += 1
        return pd.DataFrame({"Close": [100, 101]})

    monkeypatch.setattr(data_loader.yf, "download", fake_download)

    # First call should hit downloader
    df1 = data_loader.fetch_realtime_data("TEST", ttl_seconds=30)
    # Second call should be served from cache (no additional download)
    df2 = data_loader.fetch_realtime_data("TEST", ttl_seconds=30)

    assert calls["count"] == 1
    assert not df1.empty and not df2.empty
