from __future__ import annotations

from pathlib import Path

import requests

from yt_uploader.engine.notify import alert
from yt_uploader.engine.settings import Defaults, Settings


def _settings(
    *,
    token: str = "123:ABC",
    chat_id: str = "-100123",
    prefix: str = "test",
) -> Settings:
    return Settings(
        uploader_binary=Path("./youtubeuploader"),
        meta_dir=Path("./meta"),
        sleep_between_uploads=0,
        uploaded_dir_name="old_videos",
        defaults=Defaults(),
        telegram_token=token,
        telegram_chat_id=chat_id,
        telegram_prefix=prefix,
        ledger_path=Path("./ledger.sqlite"),
        accounts={},
    )


def test_sends_to_telegram_api(monkeypatch):
    calls = []

    def fake_post(url, **kw):
        calls.append({"url": url, "json": kw.get("json")})
        return type("R", (), {"ok": True})()

    monkeypatch.setattr("yt_uploader.engine.notify.requests.post", fake_post)
    alert("hello", _settings())
    assert len(calls) == 1
    assert "api.telegram.org/bot123:ABC/sendMessage" in calls[0]["url"]
    assert "[test] hello" in calls[0]["json"]["text"]


def test_missing_token_skips(monkeypatch):
    calls = []

    def fake_post(url, **kw):
        calls.append(1)

    monkeypatch.setattr("yt_uploader.engine.notify.requests.post", fake_post)
    alert("hi", _settings(token=""))
    assert calls == []


def test_missing_chat_id_skips(monkeypatch):
    calls = []

    def fake_post(url, **kw):
        calls.append(1)

    monkeypatch.setattr("yt_uploader.engine.notify.requests.post", fake_post)
    alert("hi", _settings(chat_id=""))
    assert calls == []


def test_exception_is_swallowed(monkeypatch):
    def boom(*a, **kw):
        raise requests.ConnectionError("down")

    monkeypatch.setattr("yt_uploader.engine.notify.requests.post", boom)
    alert("hi", _settings())  # Does not raise


# ponytail: reused Settings structure already has all required fields
