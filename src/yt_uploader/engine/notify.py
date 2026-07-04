from __future__ import annotations

import sys

import requests

from yt_uploader.engine.settings import Settings


def alert(settings: Settings, message: str) -> None:
    """
    Sends a Telegram message if notify.enabled and TELEGRAM_TOKEN/TELEGRAM_CHAT_ID
    are set in .env. Silently does nothing otherwise - a missing/misconfigured
    notifier must never break an upload run.
    """
    if not settings.notify_enabled:
        return
    if not settings.telegram_token or not settings.telegram_chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage",
            json={"chat_id": settings.telegram_chat_id, "text": message},
            timeout=10,
        )
    except requests.RequestException as exc:
        print(f"[notify] failed to send telegram alert: {exc}", file=sys.stderr)
