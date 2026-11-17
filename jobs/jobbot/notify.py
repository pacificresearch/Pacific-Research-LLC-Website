"""Notifications: always logged; optionally pushed to your phone via ntfy and shown on the desktop."""
from __future__ import annotations

import os
import platform
import subprocess

import requests

from .config import load_config, path
from .application_tracker import now


def send(message: str, title: str = "jobbot") -> None:
    with open(path("logs", "notifications.log"), "a") as f:
        f.write(f"{now()} {message}\n")
    url = os.environ.get("JOBBOT_NTFY_URL") or load_config()["notify"].get("ntfy_url")
    if url:
        try:
            requests.post(url, data=message.encode(), headers={"Title": title}, timeout=10)
        except requests.RequestException:
            pass
    try:
        if platform.system() == "Darwin":
            subprocess.run(["osascript", "-e", f'display notification "{message[:200]}" with title "{title}"'],
                           timeout=5, capture_output=True)
    except Exception:
        pass
