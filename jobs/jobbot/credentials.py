"""Employer-portal credentials (Workday, iCIMS, Taleo, SuccessFactors, Inspira...).

* Passwords are Chrome-strength: 16 random characters from upper, lower, digits and symbols
  (each class guaranteed), generated with `secrets`. Unique per site; never reused.
* Stored in the OS keychain when `keyring` is installed (macOS Keychain on your Mac), otherwise in
  $JOBBOT_HOME/credentials.json with 0600 permissions (gitignored). Never logged, never in a report.
* `export_chrome_csv()` writes Chrome's password-import format (name,url,username,password,note) so you
  can import every account into Google Password Manager: passwords.google.com -> Settings -> Import.
  Delete the CSV after importing.
"""
from __future__ import annotations

import csv
import json
import os
import secrets
import string
import re
from urllib.parse import urlparse

from .config import home

SERVICE = "jobbot"
SYMBOLS = "!#$%&*+-=?@^_"  # accepted by Workday/iCIMS/Taleo; avoids quotes, backslash, spaces, <>
ALPHABET = string.ascii_letters + string.digits + SYMBOLS


def generate_password(length: int = 16) -> str:
    while True:
        pw = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw)
                and any(c in SYMBOLS for c in pw) and not pw[0] in SYMBOLS):
            return pw


def site_key(url: str) -> str:
    """One account per employer portal: the host (Workday tenants are per-host), plus the tenant on shared
    hosts like wd5.myworkdaysite.com/recruiting/<tenant>/ (one host, many employers, separate accounts)."""
    u = urlparse(url)
    host = u.netloc.lower()
    m = re.match(r"/recruiting/([^/]+)/", u.path or "")
    if host.endswith("myworkdaysite.com") and m:
        return f"{host}/{m.group(1).lower()}"
    return host or url.lower()


def _file():
    return home() / "credentials.json"


def _keyring():
    try:
        import keyring  # noqa
        keyring.get_keyring()
        return keyring
    except Exception:
        return None


def _load() -> dict:
    f = _file()
    return json.loads(f.read_text()) if f.exists() else {}


def _save(d: dict) -> None:
    f = _file()
    f.write_text(json.dumps(d, indent=1))
    os.chmod(f, 0o600)


def get(url: str) -> dict | None:
    key = site_key(url)
    meta = _load().get(key)
    if not meta:
        return None
    kr = _keyring()
    pw = kr.get_password(SERVICE, f"{key}|{meta['username']}") if kr and meta.get("in_keychain") else meta.get("password")
    return {"site": key, "username": meta["username"], "password": pw, "url": meta.get("url"),
            "status": meta.get("status", "created")} if pw else None


def get_or_create(url: str, username: str) -> tuple[dict, bool]:
    """Returns (credential, is_new). A new credential is saved BEFORE it is typed anywhere."""
    cur = get(url)
    if cur:
        return cur, False
    key, pw = site_key(url), generate_password()
    d = _load()
    kr = _keyring()
    meta = {"username": username, "url": f"https://{key}/", "status": "pending_signup"}
    if kr:
        kr.set_password(SERVICE, f"{key}|{username}", pw)
        meta["in_keychain"] = True
    else:
        meta["password"] = pw
    d[key] = meta
    _save(d)
    return {"site": key, "username": username, "password": pw, "url": meta["url"], "status": "pending_signup"}, True


def set_status(url: str, status: str) -> None:
    d = _load()
    k = site_key(url)
    if k in d:
        d[k]["status"] = status
        _save(d)


def list_sites() -> list[dict]:
    return [{"site": k, "username": v["username"], "status": v.get("status")} for k, v in _load().items()]


def export_chrome_csv(path: str | None = None) -> str:
    out = path or str(home() / "chrome_passwords_import.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "url", "username", "password", "note"])
        for k in _load():
            c = get(f"https://{k}/")
            if c:
                w.writerow([k, c["url"], c["username"], c["password"], "created by jobbot for job applications"])
    os.chmod(out, 0o600)
    return out
