"""HTTP with retries, timeouts, rate-limit handling and key redaction in logs."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import redact

log = logging.getLogger("prg.http")
DEFAULT_TIMEOUT = 30


class Transient(Exception):
    pass


class RateLimited(Exception):
    pass


class HttpError(Exception):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body[:200]}")
        self.status = status


_session = requests.Session()
_session.headers["User-Agent"] = "PRG-PropertyScreener/0.1 (andrew@pacificresearchllc.com)"  # BLS requires a contact address in the UA


@retry(reraise=True, stop=stop_after_attempt(4),
       wait=wait_exponential(multiplier=1.5, min=2, max=20),
       retry=retry_if_exception_type((Transient, RateLimited)))
def _request(method: str, url: str, params: Optional[Dict[str, Any]], headers: Optional[Dict[str, str]],
             json_body: Optional[Any], timeout: int) -> requests.Response:
    try:
        r = _session.request(method, url, params=params, headers=headers, json=json_body, timeout=timeout)
    except (requests.ConnectionError, requests.Timeout) as e:
        log.warning("transient error %s %s", redact(url), type(e).__name__)
        raise Transient(str(e)) from e
    if r.status_code == 429:
        wait = float(r.headers.get("Retry-After", "5") or 5)
        log.warning("rate limited by %s; sleeping %.0fs", redact(url), wait)
        time.sleep(min(wait, 30))
        raise RateLimited(url)
    if 500 <= r.status_code < 600:
        raise Transient(f"HTTP {r.status_code}")
    return r


def get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
             timeout: int = DEFAULT_TIMEOUT) -> Any:
    r = _request("GET", url, params, headers, None, timeout)
    if r.status_code >= 400:
        raise HttpError(r.status_code, redact(r.text))
    try:
        return r.json()
    except ValueError as e:
        raise HttpError(r.status_code, f"non-JSON body: {redact(r.text[:100])}") from e


def post_json(url: str, body: Any, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_TIMEOUT) -> Any:
    r = _request("POST", url, None, headers or {"Content-Type": "application/json"}, body, timeout)
    if r.status_code >= 400:
        raise HttpError(r.status_code, redact(r.text))
    return r.json()


def get_text(url: str, timeout: int = 120) -> str:
    r = _request("GET", url, None, None, None, timeout)
    if r.status_code >= 400:
        raise HttpError(r.status_code, r.text)
    return r.text
