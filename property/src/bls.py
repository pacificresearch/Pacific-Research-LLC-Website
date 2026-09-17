"""BLS public API v2: LAUS metro unemployment/employment, QCEW average weekly wage. Key optional."""
from __future__ import annotations

import logging
from datetime import date
from typing import Dict, List, Optional

from .config import api_keys
from .database import Cache
from .http_client import HttpError, post_json
from .models import DataPoint

log = logging.getLogger("prg.bls")
URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

STATE_FIPS = {"AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10", "DC": "11",
              "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
              "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30",
              "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
              "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
              "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56", "PR": "72"}


def laus_series(state: str, cbsa: str, measure: str) -> str:
    # LAU + MT + state FIPS(2) + CBSA(5) + 00000 + measure (03 unemployment rate, 05 employment, 06 labor force)
    return f"LAUMT{STATE_FIPS[state]}{cbsa}00000{measure}"


def qcew_wage_series(cbsa: str) -> str:
    # ENU + C + first 4 digits of CBSA + datatype 4 (avg weekly wage) + size 0 + ownership 0 + industry 10 (total)
    return f"ENUC{cbsa[:4]}40010"


def fetch_series(cache: Cache, ttl: float, series_ids: List[str], budget: dict) -> Dict[str, list]:
    """Fetch up to 25 series per query (unregistered limit). Returns {series_id: [{year, period, value}]}."""
    out: Dict[str, list] = {}
    key = api_keys().get("BLS_API_KEY")
    end = date.today().year
    start = end - 3
    for i in range(0, len(series_ids), 25):
        chunk = series_ids[i:i + 25]
        body = {"seriesid": chunk, "startyear": str(start), "endyear": str(end)}
        if key:
            body["registrationkey"] = key

        def fetch(body=body):
            if budget["used"] >= budget["max"]:
                log.warning("BLS query budget exhausted; skipping %d series", len(body["seriesid"]))
                return None
            budget["used"] += 1
            try:
                data = post_json(URL, body)
            except HttpError as e:
                log.warning("BLS failed: %s", e)
                return None
            cache.log_call("bls", "timeseries", cached=False, status=200)
            if data.get("status") != "REQUEST_SUCCEEDED":
                log.warning("BLS status %s: %s", data.get("status"), data.get("message"))
            return data

        data, _ = cache.cached("bls", URL, {"seriesid": chunk, "start": start, "end": end}, ttl, fetch, endpoint="timeseries")
        if not data:
            continue
        for s in data.get("Results", {}).get("series", []):
            rows = [{"year": int(d["year"]), "period": d["period"], "value": float(d["value"])}
                    for d in s.get("data", []) if d.get("value") not in (None, "-", "")]
            out[s["seriesID"]] = rows
    return out


def latest_and_yoy(rows: list) -> tuple[Optional[dict], Optional[float]]:
    """Latest observation and the value one year earlier (same period)."""
    if not rows:
        return None, None
    rows = sorted(rows, key=lambda r: (r["year"], r["period"]), reverse=True)
    latest = rows[0]
    prior = next((r for r in rows if r["year"] == latest["year"] - 1 and r["period"] == latest["period"]), None)
    return latest, (prior["value"] if prior else None)


def metro_labor(cache: Cache, ttl: float, markets: List[dict], budget: dict) -> Dict[str, Dict[str, DataPoint]]:
    """markets: [{cbsa, state}] -> {cbsa: {unemployment_rate, unemployment_rate_yoy_change, employment_growth_1y, avg_weekly_wage, wage_growth_1y}}"""
    ids = []
    for m in markets:
        if m["state"] not in STATE_FIPS:
            continue
        ids += [laus_series(m["state"], m["cbsa"], "03"), laus_series(m["state"], m["cbsa"], "05"), qcew_wage_series(m["cbsa"])]
    series = fetch_series(cache, ttl, ids, budget)
    out: Dict[str, Dict[str, DataPoint]] = {}
    src = "BLS LAUS (metro) / QCEW"
    for m in markets:
        cbsa, st = m["cbsa"], m["state"]
        d: Dict[str, DataPoint] = {}
        if st not in STATE_FIPS:
            out[cbsa] = {k: DataPoint.unknown("no state FIPS") for k in ["unemployment_rate", "employment_growth_1y", "avg_weekly_wage", "wage_growth_1y"]}
            continue
        ur = series.get(laus_series(st, cbsa, "03"), [])
        latest, prior = latest_and_yoy(ur)
        if latest:
            d["unemployment_rate"] = DataPoint.provider(latest["value"], src, URL, f"{latest['year']}-{latest['period']}", 0.85)
            d["unemployment_rate_yoy_change"] = DataPoint.provider(round(latest["value"] - prior, 2), src, URL, f"{latest['year']}-{latest['period']}", 0.85) if prior is not None else DataPoint.unknown()
        else:
            d["unemployment_rate"] = DataPoint.unknown("LAUS metro series not returned (New England NECTA or budget)")
            d["unemployment_rate_yoy_change"] = DataPoint.unknown()
        emp = series.get(laus_series(st, cbsa, "05"), [])
        latest, prior = latest_and_yoy(emp)
        d["employment_growth_1y"] = DataPoint.provider(round(latest["value"] / prior - 1, 4), src, URL, f"{latest['year']}-{latest['period']}", 0.85) if latest and prior else DataPoint.unknown()
        d["employment_level"] = DataPoint.provider(latest["value"], src, URL, f"{latest['year']}-{latest['period']}", 0.85) if latest else DataPoint.unknown()
        w = series.get(qcew_wage_series(cbsa), [])
        latest, prior = latest_and_yoy(w)
        d["avg_weekly_wage"] = DataPoint.provider(latest["value"], "BLS QCEW avg weekly wage, all industries", URL, f"{latest['year']}-{latest['period']}", 0.85) if latest else DataPoint.unknown()
        d["wage_growth_1y"] = DataPoint.provider(round(latest["value"] / prior - 1, 4), "BLS QCEW", URL, f"{latest['year']}-{latest['period']}", 0.8) if latest and prior else DataPoint.unknown()
        out[cbsa] = d
    return out


def metro_wages(cache: Cache, ttl: float, cbsas: List[str], budget: dict) -> Dict[str, Dict[str, DataPoint]]:
    """QCEW average weekly wage (all industries, total covered) + 1y growth for a list of CBSAs."""
    ids = [qcew_wage_series(c) for c in cbsas]
    series = fetch_series(cache, ttl, ids, budget)
    out: Dict[str, Dict[str, DataPoint]] = {}
    for c in cbsas:
        w = series.get(qcew_wage_series(c), [])
        latest, prior = latest_and_yoy(w)
        d: Dict[str, DataPoint] = {}
        d["avg_weekly_wage"] = DataPoint.provider(latest["value"], "BLS QCEW avg weekly wage, all industries", URL, f"{latest['year']}-{latest['period']}", 0.85) if latest else DataPoint.unknown("QCEW metro series not returned")
        d["wage_growth_1y"] = DataPoint.provider(round(latest["value"] / prior - 1, 4), "BLS QCEW", URL, f"{latest['year']}-{latest['period']}", 0.8) if latest and prior else DataPoint.unknown()
        out[c] = d
    return out
