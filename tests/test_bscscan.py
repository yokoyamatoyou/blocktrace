import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import bscscan


def test_fetch_all_paginates(monkeypatch):
    """fetch_all should request subsequent pages until an empty page is returned."""
    calls = []

    class FakeResp:
        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    def fake_get(url, timeout=10):
        calls.append(url)
        if "startblock=0" in url:
            data = {"result": [{"blockNumber": "1", "hash": "h1"}]}
        elif "startblock=2" in url:
            data = {"result": []}
        else:
            raise AssertionError(f"Unexpected URL {url}")
        return FakeResp(data)

    monkeypatch.setattr(bscscan.requests, "get", fake_get)
    monkeypatch.setattr(bscscan.time, "sleep", lambda _: None)

    df = bscscan.fetch_all("txlist", "0xabc")
    assert len(df) == 1
    assert any("startblock=2" in url for url in calls)


def test_fetch_all_handles_api_error(monkeypatch):
    """An API error should result in an empty DataFrame."""

    class FakeResp:
        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

    def fake_get(url, timeout=10):
        return FakeResp({"status": "0", "message": "NOTOK", "result": "error"})

    monkeypatch.setattr(bscscan.requests, "get", fake_get)
    monkeypatch.setattr(bscscan.time, "sleep", lambda _: None)

    df = bscscan.fetch_all("txlist", "0xabc")
    assert df.empty
