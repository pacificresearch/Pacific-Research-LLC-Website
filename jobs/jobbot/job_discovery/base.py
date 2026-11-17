"""Shared HTTP session: polite rate limiting, exponential backoff, honest UA."""
from __future__ import annotations

import random
import re
import time

import requests

UA = "jobbot/0.1 (personal job search tool; low volume)"
_session = requests.Session()
_session.headers["User-Agent"] = UA
_last: dict[str, float] = {}


class SourceError(RuntimeError):
    pass


def http(method: str, url: str, *, min_interval: float = 1.0, retries: int = 4, **kw) -> requests.Response:
    host = url.split("/")[2]
    wait = _last.get(host, 0) + min_interval - time.time()
    if wait > 0:
        time.sleep(wait)
    kw.setdefault("timeout", 30)
    delay = 2.0
    for attempt in range(retries + 1):
        _last[host] = time.time()
        try:
            r = _session.request(method, url, **kw)
        except requests.RequestException as e:
            if attempt == retries:
                raise SourceError(f"{host}: {e}") from e
        else:
            if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                ra = r.headers.get("Retry-After")
                time.sleep(float(ra) if ra and ra.isdigit() else delay + random.random())
                delay *= 2
                continue
            if r.status_code in (401, 403):
                # access control: respect it, do not try to get around it
                raise SourceError(f"{host}: HTTP {r.status_code} (access denied — not retried)")
            r.raise_for_status()
            return r
        time.sleep(delay + random.random())
        delay *= 2
    raise SourceError(f"{host}: retries exhausted")


def relevant_title(title: str, terms: dict) -> bool:
    t = title.lower()
    if any(re.search(p, t) for p in terms.get("exclude_title_patterns", [])):
        return False
    return any(re.search(p, t) for p in terms.get("include_title_patterns", []))
