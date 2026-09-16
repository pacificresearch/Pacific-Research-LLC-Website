"""FHFA House Price Index (all-transactions, MSA, quarterly). One public CSV download covers every metro."""
from __future__ import annotations

import csv
import io
import logging
import math
from typing import Dict, Optional

from .database import Cache
from .http_client import HttpError, get_text
from .models import DataPoint

log = logging.getLogger("prg.fhfa")
URL = "https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv"


def load_hpi(cache: Cache, ttl: float) -> Dict[str, list]:
    """{place_id: [(year, quarter, index_nsa)] sorted ascending} for MSA all-transactions traditional index."""
    def fetch():
        try:
            text = get_text(URL)
        except HttpError as e:
            log.warning("FHFA download failed: %s", e)
            return None
        cache.log_call("fhfa", "hpi_master.csv", cached=False, status=200)
        out: Dict[str, list] = {}
        names: Dict[str, str] = {}
        for row in csv.DictReader(io.StringIO(text)):
            if row.get("hpi_type") != "traditional" or row.get("hpi_flavor") != "all-transactions" or row.get("level") != "MSA":
                continue
            try:
                out.setdefault(row["place_id"], []).append((int(row["yr"]), int(row["period"]), float(row["index_nsa"])))
                names[row["place_id"]] = row["place_name"]
            except (ValueError, KeyError):
                continue
        return {"series": out, "names": names}

    data, _ = cache.cached("fhfa", URL, None, ttl, fetch, endpoint="hpi_master.csv")
    if not data:
        return {}
    series = {k: sorted([tuple(x) for x in v]) for k, v in data["series"].items()}
    series["__names__"] = data["names"]
    return series


def hpi_metrics(hpi: Dict[str, list], cbsa: str, name_hint: str = "") -> Dict[str, DataPoint]:
    """1y change, 3y CAGR, 5y CAGR for a CBSA (falls back to a metro-division name match)."""
    rows = hpi.get(cbsa)
    used = cbsa
    if not rows and name_hint and hpi:
        city = name_hint.split(",")[0].split("-")[0].strip().lower()
        for pid, nm in hpi.get("__names__", {}).items():
            if nm.lower().startswith(city):
                rows, used = hpi[pid], pid
                break
    keys = ["hpi_1y", "hpi_3y_cagr", "hpi_5y_cagr", "hpi_latest_period"]
    if not rows:
        return {k: DataPoint.unknown("FHFA MSA series not found") for k in keys}
    latest = rows[-1]
    out: Dict[str, DataPoint] = {}
    src = f"FHFA HPI all-transactions, MSA {used}"

    def back(n_quarters: int) -> Optional[float]:
        idx = len(rows) - 1 - n_quarters
        return rows[idx][2] if idx >= 0 else None

    out["hpi_latest_period"] = DataPoint.provider(f"{latest[0]}Q{latest[1]}", src, URL, f"{latest[0]}Q{latest[1]}", 0.9)
    for key, q, yrs in [("hpi_1y", 4, 1), ("hpi_3y_cagr", 12, 3), ("hpi_5y_cagr", 20, 5)]:
        b = back(q)
        if b:
            out[key] = DataPoint.provider(round((latest[2] / b) ** (1 / yrs) - 1, 4), src, URL, f"{latest[0]}Q{latest[1]}", 0.9)
        else:
            out[key] = DataPoint.unknown("insufficient history")
    return out
