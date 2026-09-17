"""FRED (optional). Absent key => skipped, fields UNKNOWN, no failure."""
from __future__ import annotations

import logging
from typing import Dict, Optional

from .config import api_keys
from .database import Cache
from .http_client import HttpError, get_json
from .models import DataPoint

log = logging.getLogger("prg.fred")
URL = "https://api.stlouisfed.org/fred/series/observations"


def available() -> bool:
    return bool(api_keys().get("FRED_API_KEY"))


def series_latest(cache: Cache, ttl: float, series_id: str) -> DataPoint:
    key = api_keys().get("FRED_API_KEY")
    if not key:
        return DataPoint.unknown("FRED_API_KEY not set")
    params = {"series_id": series_id, "file_type": "json", "sort_order": "desc", "limit": 13}

    def fetch():
        try:
            data = get_json(URL, {**params, "api_key": key})
        except HttpError as e:
            log.warning("FRED %s failed: %s", series_id, e)
            return None
        cache.log_call("fred", series_id, cached=False, status=200)
        return data

    data, _ = cache.cached("fred", URL, params, ttl, fetch, endpoint=series_id)
    obs = [o for o in (data or {}).get("observations", []) if o.get("value") not in (".", None)]
    if not obs:
        return DataPoint.unknown("no observations")
    return DataPoint.provider(float(obs[0]["value"]), f"FRED {series_id}", f"https://fred.stlouisfed.org/series/{series_id}", obs[0]["date"], 0.85)


def metro_series(cache: Cache, ttl: float, cbsa: str) -> Dict[str, DataPoint]:
    """Metro-level series that FRED keys by CBSA code (e.g., ACTLISCOU<cbsa> active listings, MEDDAYONMAR<cbsa>)."""
    if not available():
        return {"fred_active_listings": DataPoint.unknown("FRED_API_KEY not set"),
                "fred_median_days_on_market": DataPoint.unknown("FRED_API_KEY not set")}
    return {"fred_active_listings": series_latest(cache, ttl, f"ACTLISCOU{cbsa}"),
            "fred_median_days_on_market": series_latest(cache, ttl, f"MEDDAYONMAR{cbsa}")}
