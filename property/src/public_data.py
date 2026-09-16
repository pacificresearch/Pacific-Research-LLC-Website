"""Keyless public datasets that carry Stage 1 when the Census API key is absent:
Zillow Research ZHVI/ZORI (metro), Census Population Estimates (CBSA, incl. net migration), BLS LAUS flat file."""
from __future__ import annotations

import csv
import io
import logging
import re
from datetime import date
from typing import Dict, Optional

from .database import Cache
from .http_client import HttpError, get_text
from .models import DataPoint

log = logging.getLogger("prg.public")
ZHVI_URL = "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"
ZORI_URL = "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv"
POPEST_URL = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/metro/totals/cbsa-est2024-alldata.csv"
LAUS_URL = "https://download.bls.gov/pub/time.series/la/la.data.60.Metro"


def _fetch(cache: Cache, source: str, url: str, ttl: float, parse, endpoint: str):
    def fetch():
        try:
            text = get_text(url, timeout=300)
        except HttpError as e:
            log.warning("%s download failed: %s", source, e)
            return None
        cache.log_call(source, endpoint, cached=False, status=200)
        return parse(text)
    data, _ = cache.cached(source, url, None, ttl, fetch, endpoint=endpoint)
    return data or {}


def _last_numeric(row: list, header: list, n_back: int = 0) -> tuple[Optional[float], str]:
    """Value n_back months before the latest non-empty month."""
    idx = [i for i, h in enumerate(header) if re.match(r"\d{4}-\d{2}-\d{2}", h)]
    vals = [(header[i], row[i]) for i in idx if i < len(row) and row[i] not in ("", None)]
    if len(vals) <= n_back:
        return None, ""
    d, v = vals[-1 - n_back]
    try:
        return float(v), d
    except ValueError:
        return None, d


def zillow_metros(cache: Cache, ttl: float) -> Dict[str, dict]:
    """{'City, ST': {zhvi, zhvi_date, zhvi_1y, zhvi_3y_cagr, zhvi_5y_cagr, zori, zori_date, zori_1y, size_rank}} keyed by Zillow RegionName."""
    def parse_zhvi(text):
        rows = list(csv.reader(io.StringIO(text)))
        h = rows[0]
        out = {}
        for r in rows[1:]:
            if r[3] != "msa":
                continue
            v, d = _last_numeric(r, h)
            v12, _ = _last_numeric(r, h, 12)
            v36, _ = _last_numeric(r, h, 36)
            v60, _ = _last_numeric(r, h, 60)
            out[r[2]] = {"zhvi": v, "zhvi_date": d, "size_rank": int(r[1]) if r[1].isdigit() else None,
                         "zhvi_1y": (v / v12 - 1) if v and v12 else None,
                         "zhvi_3y_cagr": ((v / v36) ** (1 / 3) - 1) if v and v36 else None,
                         "zhvi_5y_cagr": ((v / v60) ** (1 / 5) - 1) if v and v60 else None}
        return out

    def parse_zori(text):
        rows = list(csv.reader(io.StringIO(text)))
        h = rows[0]
        out = {}
        for r in rows[1:]:
            if r[3] != "msa":
                continue
            v, d = _last_numeric(r, h)
            v12, _ = _last_numeric(r, h, 12)
            out[r[2]] = {"zori": v, "zori_date": d, "zori_1y": (v / v12 - 1) if v and v12 else None}
        return out

    zhvi = _fetch(cache, "zillow", ZHVI_URL, ttl, parse_zhvi, "Metro_zhvi.csv")
    zori = _fetch(cache, "zillow", ZORI_URL, ttl, parse_zori, "Metro_zori.csv")
    out = {}
    for name, rec in zhvi.items():
        out[name] = {**rec, **zori.get(name, {})}
    return out


def popest_metros(cache: Cache, ttl: float) -> Dict[str, dict]:
    """{cbsa: {name, pop_2020, pop_2024, growth_4y, dom_mig_per_1000, net_mig_per_1000}} for Metropolitan Statistical Areas."""
    def parse(text):
        rows = list(csv.reader(io.StringIO(text)))
        h = rows[0]
        ix = {c: i for i, c in enumerate(h)}
        out = {}
        for r in rows[1:]:
            if r[ix["LSAD"]] != "Metropolitan Statistical Area":
                continue
            try:
                p20, p24 = float(r[ix["POPESTIMATE2020"]]), float(r[ix["POPESTIMATE2024"]])
                dom = sum(float(r[ix[f"DOMESTICMIG{y}"]]) for y in (2022, 2023, 2024)) / 3
                net = sum(float(r[ix[f"NETMIG{y}"]]) for y in (2022, 2023, 2024)) / 3
            except (ValueError, KeyError):
                continue
            out[r[ix["CBSA"]].zfill(5)] = {"name": r[ix["NAME"]], "pop_2020": p20, "pop_2024": p24,
                                          "growth_4y": p24 / p20 - 1 if p20 else None,
                                          "dom_mig_per_1000": dom / p24 * 1000 if p24 else None,
                                          "net_mig_per_1000": net / p24 * 1000 if p24 else None}
        return out
    return _fetch(cache, "census_popest", POPEST_URL, ttl, lambda t: parse(t), "cbsa-est2024-alldata.csv")


def laus_metros(cache: Cache, ttl: float) -> Dict[str, dict]:
    """{cbsa: {unemployment_rate, period, unemployment_rate_yoy_change, employment_growth_1y}} from the LAUS Metro flat file (~40MB, cached)."""
    def parse(text):
        yr_min = date.today().year - 2
        series: Dict[str, Dict[str, float]] = {}
        for line in io.StringIO(text):
            if not line.startswith("LAUMT"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            sid, yr, per, val = parts[0], parts[1], parts[2], parts[3]
            if per == "M13" or int(yr) < yr_min:
                continue
            meas = sid[-2:]
            if meas not in ("03", "05"):
                continue
            try:
                series.setdefault(sid, {})[f"{yr}-{per}"] = float(val)
            except ValueError:
                continue
        out: Dict[str, dict] = {}
        for sid, obs in series.items():
            cbsa = sid[7:12]
            keys = sorted(obs)
            latest = keys[-1]
            prior = f"{int(latest[:4]) - 1}{latest[4:]}"
            rec = out.setdefault(cbsa, {})
            if sid.endswith("03"):
                rec.update({"unemployment_rate": obs[latest], "period": latest,
                            "unemployment_rate_yoy_change": (obs[latest] - obs[prior]) if prior in obs else None})
            else:
                rec["employment_growth_1y"] = (obs[latest] / obs[prior] - 1) if prior in obs and obs[prior] else None
                rec["employment_level"] = obs[latest]
        return out
    return _fetch(cache, "bls_laus_file", LAUS_URL, ttl, parse, "la.data.60.Metro")


def zillow_key_for(cbsa_name: str) -> str:
    """'Fayetteville-Springdale-Rogers, AR' -> 'Fayetteville, AR' (Zillow's short metro name)."""
    head, _, st = cbsa_name.partition(",")
    city = head.split("-")[0].split("/")[0].strip()
    st2 = st.strip().split("-")[0].strip()[:2]
    return f"{city}, {st2}"
