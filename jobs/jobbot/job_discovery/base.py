"""Shared HTTP session: polite rate limiting, exponential backoff, honest UA."""
from __future__ import annotations

import random
import re
import threading
import time

import requests

UA = "jobbot/0.1 (personal job search tool; low volume)"
_session = requests.Session()
_session.headers["User-Agent"] = UA
_last: dict[str, float] = {}
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()
# Workday rate-limits per shared cluster (wd1/wd3/wd5.myworkdayjobs.com), not per tenant: parallel workers on
# different tenants were tripping HTTP 429 on nearly every Workday source. Throttle the whole cluster as one host.
CLUSTER_MIN_INTERVAL = {"myworkdayjobs.com": 2.0}


def _key(host: str) -> tuple[str, float]:
    for dom, gap in CLUSTER_MIN_INTERVAL.items():
        if host.endswith(dom):
            return ".".join(host.split(".")[-3:]), gap
    return host, 0.0


def _lock(key: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


class SourceError(RuntimeError):
    pass


def http(method: str, url: str, *, min_interval: float = 1.0, retries: int = 4, **kw) -> requests.Response:
    host = url.split("/")[2]
    key, floor = _key(host)
    min_interval = max(min_interval, floor)
    kw.setdefault("timeout", 30)
    delay = 5.0 if floor else 2.0
    for attempt in range(retries + 1):
        with _lock(key):  # one request at a time per host/cluster, spaced by min_interval
            wait = _last.get(key, 0) + min_interval - time.time()
            if wait > 0:
                time.sleep(wait)
            _last[key] = time.time()
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
