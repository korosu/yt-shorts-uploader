from __future__ import annotations

from pathlib import Path

import pytest
import requests

from yt_uploader.engine.notify import (
    DiscordNotifier,
    Notifier,
    TelegramNotifier,
    alert,
    build_notifiers,
    notify_all,
)
from yt_uploader.engine.settings import Defaults, Settings


def _notify_settings(
    *,
    enabled: bool = True,
    token: str = "123:ABCtoken",
    chat_id: str = "-1001234567890",
    discord_url: str = "https://discord.com/api/webhooks/test",
) -> Settings:
    return Settings(
        uploader_binary=Path("./youtubeuploader"),
        meta_dir=Path("./meta"),
        sleep_between_uploads=0,
        uploaded_dir_name="old_videos",
        defaults=Defaults(),
        notify_enabled=enabled,
        telegram_token=token,
        telegram_chat_id=chat_id,
        discord_webhook_url=discord_url,
        ledger_path=Path("./ledger.sqlite"),
        accounts={},
    )


def _record(monkeypatch, url_match: str | None = None) -> list[dict]:
    calls: list[dict] = []

    def fake_post(url, **kwargs):
        if url_match is None or url_match in url:
            calls.append({"url": url, "json": kwargs.get("json"), "timeout": kwargs.get("timeout")})
        return None

    monkeypatch.setattr("yt_uploader.engine.notify.requests.post", fake_post)
    return calls


def test_disabled_does_not_send(monkeypatch):
    calls = _record(monkeypatch)
    alert(_notify_settings(enabled=False), "hi")
    assert calls == []


def test_missing_token_does_not_send(monkeypatch):
    calls = _record(monkeypatch)
    # Also disable Discord to test Telegram-specific missing credential
    alert(_notify_settings(token="", discord_url=""), "hi")
    assert calls == []


def test_missing_chat_id_does_not_send(monkeypatch):
    calls = _record(monkeypatch)
    # Also disable Discord to test Telegram-specific missing credential
    alert(_notify_settings(chat_id="", discord_url=""), "hi")
    assert calls == []


def test_build_notifiers_empty_when_disabled():
    assert build_notifiers(_notify_settings(enabled=False)) == []


def test_build_notifiers_both_channels():
    notifiers = build_notifiers(_notify_settings())
    assert len(notifiers) == 2
    assert isinstance(notifiers[0], TelegramNotifier)
    assert isinstance(notifiers[1], DiscordNotifier)


def test_notify_all_calls_each(monkeypatch):
    calls = _record(monkeypatch)
    notify_all(build_notifiers(_notify_settings()), "hi")
    assert len(calls) == 2


def test_telegram_notifier_swallows_requestexception(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr("yt_uploader.engine.notify.requests.post", boom)
    assert alert(_notify_settings(), "hi") is None


def test_telegram_posts_to_correct_url(monkeypatch):
    calls = _record(monkeypatch, "telegram")
    alert(_notify_settings(token="123:ABC"), "hi")
    assert len(calls) >= 1
    assert "api.telegram.org/bot123:ABC/sendMessage" in calls[0]["url"]


def test_discord_notifier_posts_webhook(monkeypatch):
    calls = _record(monkeypatch, "discord")
    notifiers = build_notifiers(_notify_settings())
    notify_all(notifiers, "test message")
    assert len(calls) >= 1
    assert "discord.com/api/webhooks/test" in calls[0]["url"]
    assert calls[0]["json"] == {"content": "test message"}
    assert calls[0]["timeout"] == 10


def test_non_requests_exception_propagates(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("bug, not a requests exception")

    monkeypatch.setattr("yt_uploader.engine.notify.requests.post", boom)
    with pytest.raises(RuntimeError):
        alert(_notify_settings(), "hi")


def test_notifier_protocol_runtime_check():
    # Verify Notifier is a Protocol that works at runtime (structural typing)
    class BadNotifier:
        pass  # no alert method

    # Structural check: BadNotifier lacks alert() -> not a Notifier
    assert not isinstance(BadNotifier(), Notifier)

    # Structural check: good implementations pass
    assert isinstance(
        TelegramNotifier("token", "chat_id"), Notifier
    )
    assert isinstance(DiscordNotifier("https://example.com/webhook"), Notifier)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
