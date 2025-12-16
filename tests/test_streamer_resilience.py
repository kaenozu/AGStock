from datetime import datetime

import pandas as pd

from src.realtime.streamer import marketStreamer


def test_streamer_retries_and_recovers(monkeypatch):
    call_count = {"n": 0}

    def fake_download(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ValueError("rate limit")
        return pd.DataFrame({"Close": [10], "Volume": [5]})

    monkeypatch.setattr("src.realtime.streamer.time.sleep", lambda s: None)

    streamer = marketStreamer(["AAA"], max_retries=2, backoff_factor=1, downloader=fake_download)
    streamer._fetch_latest()

    assert streamer.failure_count == 0
    assert streamer.last_error is None
    assert "AAA" in streamer.latest_data
    assert streamer.latest_data["AAA"]["price"] == 10
    assert isinstance(streamer.last_update, datetime)


def test_streamer_records_failure(monkeypatch):
    def failing_download(*args, **kwargs):
        raise RuntimeError("hard fail")

    monkeypatch.setattr("src.realtime.streamer.time.sleep", lambda s: None)

    streamer = marketStreamer(["BBB"], max_retries=2, backoff_factor=1, downloader=failing_download)
    streamer._fetch_latest()

    assert streamer.failure_count == 2
    assert streamer.last_error == "hard fail"
    assert streamer.last_update is None

