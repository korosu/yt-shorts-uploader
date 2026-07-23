"""notify.py — Telegram alerts for yt-shorts-uploader."""

from __future__ import annotations

import requests

from yt_uploader.engine.settings import Settings


def alert(msg: str, settings: Settings) -> None:
    if not settings.telegram_token or not settings.telegram_chat_id:
        return
    text = f"[{settings.telegram_prefix}] {msg}" if settings.telegram_prefix else msg
    url = f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": settings.telegram_chat_id, "text": text},
            timeout=10,
        )
        if not r.ok:
            print(
                f"[{settings.telegram_prefix}] Telegram returned {r.status_code}: "
                f"{r.text.strip()[:200]}"
            )
    except Exception as exc:
        print(f"[{settings.telegram_prefix}] Telegram send failed: {exc}")
