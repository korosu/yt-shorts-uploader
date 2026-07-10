"""
notify.py — Notifier Protocol with Telegram and Discord implementations.
"""

from __future__ import annotations

import sys
from typing import Protocol, runtime_checkable

import requests

from yt_uploader.engine.settings import Settings


@runtime_checkable
class Notifier(Protocol):
    def alert(self, message: str) -> None: ...


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self._token = token
        self._chat_id = chat_id

    def alert(self, message: str) -> None:
        if not self._token or not self._chat_id:
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self._token}/sendMessage",
                json={"chat_id": self._chat_id, "text": message},
                timeout=10,
            )
        except requests.RequestException as exc:
            print(f"[notify] telegram failed: {exc}", file=sys.stderr)


class DiscordNotifier:
    def __init__(self, webhook_url: str) -> None:
        self._url = webhook_url

    def alert(self, message: str) -> None:
        if not self._url:
            return
        try:
            requests.post(self._url, json={"content": message}, timeout=10)
        except requests.RequestException as exc:
            print(f"[notify] discord failed: {exc}", file=sys.stderr)


def build_notifiers(settings: Settings) -> list[Notifier]:
    if not settings.notify_enabled:
        return []
    return [
        TelegramNotifier(settings.telegram_token, settings.telegram_chat_id),
        DiscordNotifier(settings.discord_webhook_url),
    ]


def notify_all(notifiers: list[Notifier], message: str) -> None:
    for n in notifiers:
        n.alert(message)


def alert(settings: Settings, message: str) -> None:
    """
    Sends a Telegram message if notify.enabled and TELEGRAM_TOKEN/TELEGRAM_CHAT_ID
    are set in .env. Silently does nothing otherwise - a missing/misconfigured
    notifier must never break an upload run.

    This function is maintained for backward compatibility; it delegates to
    build_notifiers and notify_all.
    """
    notify_all(build_notifiers(settings), message)
