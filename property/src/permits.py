"""Census Building Permits Survey — annual metro totals (public flat file)."""
from __future__ import annotations

import csv
import io
import logging
from datetime import date
from typing import Dict, Optional

from .database import Cache
from .http_client import HttpError, get_text
from .models import DataPoint

log = logging.getLogger("prg.permits")
BASE = "https://www2.census.gov/econ/bps/CBSA%20(beginning%20Jan%202024)/"


def load_permits(cache: Cache, ttl: float) -> Dict[str, dict]:
    """{cbsa: {year, total_units, units_1, units_2_4, units_5plus}} for the latest available annual file."""
    year = date.today().year - 1
    for y in (year, year - 1):
        url = f"{BASE}cbsa{y}a.txt"

        def fetch(url=url):
            try:
                text = get_text(url)
            except HttpError as e:
                log.info("permits %s not available: %s", url, e)
                return None
            cache.log_call("census_bps", url.rsplit("/", 1)[-1], cached=False, status=200)
            return text

        text, _ = cache.cached("census_bps", url, None, ttl, fetch, endpoint=url.rsplit("/", 1)[-1])
        if not text:
            continue
        out: Dict[str, dict] = {}
        rows = list(csv.reader(io.StringIO(text)))
        for row in rows[2:]:
            if len(row) < 17:
                continue
            try:
                cbsa = row[2].strip().zfill(5)
                # cols: 0 date,1 CSA,2 CBSA,3 hdr,4 name, then (bldgs,units,value) x 1-unit,2-unit,3-4,5+
                u1, u2, u34, u5 = (float(row[6]), float(row[9]), float(row[12]), float(row[15]))
            except ValueError:
                continue
            out[cbsa] = {"year": y, "total_units": u1 + u2 + u34 + u5, "units_1": u1, "units_2_4": u2 + u34, "units_5plus": u5, "url": url}
        if out:
            return out
    return {}


def permits_metrics(permits: Dict[str, dict], cbsa: str, population: Optional[float]) -> Dict[str, DataPoint]:
    rec = permits.get(cbsa)
    if not rec:
        return {"permits_total_units": DataPoint.unknown("BPS metro file unavailable or CBSA not listed"),
                "permits_per_1000_pop": DataPoint.unknown()}
    src = f"Census Building Permits Survey {rec['year']} (metro annual)"
    out = {"permits_total_units": DataPoint.provider(rec["total_units"], src, rec["url"], str(rec["year"]), 0.85)}
    out["permits_per_1000_pop"] = DataPoint.provider(round(rec["total_units"] / population * 1000, 2), src, rec["url"], str(rec["year"]), 0.8) if population else DataPoint.unknown()
    return out
