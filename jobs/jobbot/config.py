"""Configuration and paths.

Everything personal lives under JOBBOT_HOME (default: jobs/data/, gitignored):
  config.yaml      operating config (quotas, salary, geography, mode)
  profile.yaml     evidence library + approved answers (PII — never committed)
  jobbot.sqlite    tracking database
  materials/       exact resume/cover letter versions per application
  reports/         daily reports + optimization analyses
  browser/         persistent Playwright profile (your own logins)
"""
from __future__ import annotations

import copy
import os
from pathlib import Path

import yaml

PKG_DIR = Path(__file__).resolve().parent
JOBS_DIR = PKG_DIR.parent


def home() -> Path:
    p = Path(os.environ.get("JOBBOT_HOME", JOBS_DIR / "data")).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p


def path(*parts: str) -> Path:
    p = home().joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


DEFAULTS: dict = {
    "mode": "review",              # review | auto  (auto requires `jobbot authorize-auto-submit`)
    "paused": False,
    "quotas": {"A": 10, "B": 10, "C": 5},
    "min_score": 70,               # below this: never auto-apply
    "approval_score": 80,          # strong match threshold surfaced first
    "max_per_employer_per_day": 3,
    "discovery_target": 150,
    "salary": {"floor_usd": 100000, "target_min": 120000, "target_max": 180000,
               "international_floor_usd": 60000},
    "geography": {
        "tiers": [
            {"name": "SoCal (OC/LA)", "score": 100, "match": ["orange county", "irvine", "santa ana", "costa mesa",
             "newport beach", "anaheim", "los angeles", "pasadena", "duarte", "long beach", "torrance",
             "santa monica", "culver city", "el segundo", "thousand oaks", "carlsbad", "tustin", "huntington beach",
             "lake forest", "aliso viejo", "mission viejo", "fullerton", "burbank", "glendale", "ventura"]},
            {"name": "San Diego", "score": 95, "match": ["san diego", "la jolla", "carlsbad", "oceanside"]},
            {"name": "Bay Area", "score": 90, "match": ["san francisco", "palo alto", "stanford", "menlo park",
             "south san francisco", "redwood city", "san mateo", "oakland", "berkeley", "emeryville", "san jose",
             "mountain view", "sunnyvale", "foster city", "fremont", "brisbane", "hayward", "alameda"]},
            {"name": "Remote US", "score": 85, "match": ["remote"]},
        ],
        "other_us_score": 55,
        "international": {"default": 70,
                          "preferred": {"brazil": 90, "portugal": 85, "spain": 85, "italy": 80, "france": 80,
                                        "switzerland": 85, "geneva": 85, "netherlands": 80, "germany": 75,
                                        "united kingdom": 80, "ireland": 80, "denmark": 80, "austria": 80,
                                        "japan": 80, "singapore": 80, "korea": 75, "australia": 80,
                                        "new zealand": 80, "canada": 80, "mexico": 75, "chile": 75, "peru": 75,
                                        "colombia": 70, "costa rica": 75, "argentina": 70, "kenya": 65,
                                        "thailand": 70, "vietnam": 65, "philippines": 65, "uruguay": 75}},
    },
    "employers": {"include": [], "exclude": []},
    "rate_limit_seconds": 1.5,
    "semantic": {"enabled": True, "top_n_per_category": 25, "max_calls_per_category": 60, "workers": 5,
                 "timeout_seconds": 180},
    "notify": {"ntfy_url": None},
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config() -> dict:
    """File config merged over defaults, then DB runtime settings (dashboard) over that."""
    cfg = copy.deepcopy(DEFAULTS)
    f = home() / "config.yaml"
    if f.exists():
        cfg = _deep_merge(cfg, yaml.safe_load(f.read_text()) or {})
    try:
        from . import application_tracker as db
        cfg = _deep_merge(cfg, db.get_settings())
    except Exception:
        pass
    return cfg


def load_yaml(name: str, default=None):
    """Load a YAML file: JOBBOT_HOME first, then the committed package copy."""
    for base in (home(), JOBS_DIR):
        f = base / name
        if f.exists():
            return yaml.safe_load(f.read_text())
    return default
