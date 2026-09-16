"""Configuration: config.yaml (assumptions) + environment (secrets). Never hardcode keys."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

try:  # optional: .env support
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("prg.config")

KEY_NAMES = ["RENTCAST_API_KEY", "BRAVE_SEARCH_API_KEY", "CENSUS_API_KEY",
             "FRED_API_KEY", "BLS_API_KEY", "ATTOM_API_KEY"]


class Capital(BaseModel):
    price_ceiling: float
    preferred_down_payment: float
    max_down_payment: float
    down_payment_pcts: List[float]
    baseline_down_payment_pct: float

    @field_validator("down_payment_pcts")
    @classmethod
    def _pcts(cls, v):
        assert all(0 < p < 1 for p in v), "down payment pcts must be fractions"
        return v


class Financing(BaseModel):
    amortization_years: int = 30
    interest_rate: float = 0.075
    interest_only_months: int = 0
    va_loan: bool = False
    rate_sensitivity: List[float]
    lender_reserve_months_piti: int = 6

    @field_validator("va_loan")
    @classmethod
    def _no_va(cls, v):
        assert v is False, "VA financing is never modelled for this acquisition (entitlement preserved)"
        return v


class Config:
    """Thin wrapper: validated core sections + raw dict access for the rest."""

    def __init__(self, raw: Dict[str, Any]):
        self.raw = raw
        self.capital = Capital(**raw["capital"])
        self.financing = Financing(**raw["financing"])
        for section in ["run", "acquisition_costs", "income", "expenses", "insurance",
                        "hazards_by_state", "property_taxes", "rent_analysis", "targets",
                        "stress", "ranking_e_weights", "api_budget", "seed_markets",
                        "market_screen_weights"]:
            if section not in raw:
                raise ValueError(f"config.yaml missing section: {section}")
        w = raw["ranking_e_weights"]
        if abs(sum(w.values()) - 1.0) > 1e-6:
            raise ValueError("ranking_e_weights must sum to 1.0")

    def __getitem__(self, k):
        return self.raw[k]

    def get(self, k, default=None):
        return self.raw.get(k, default)

    @property
    def cache_db(self) -> Path:
        return ROOT / self.raw["run"].get("cache_db", "cache/prg_property.sqlite").replace("property/", "", 1)

    @property
    def output_dir(self) -> Path:
        return ROOT / "output"

    @property
    def research_dir(self) -> Path:
        return ROOT / "research" / "markets"


def load_config(path: Optional[Path] = None) -> Config:
    if load_dotenv:
        load_dotenv(ROOT / ".env")
    path = path or ROOT / "config.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)
    return Config(raw)


def api_keys() -> Dict[str, Optional[str]]:
    return {k: (os.environ.get(k) or None) for k in KEY_NAMES}


def redact(s: str) -> str:
    """Redact any configured key value that appears in a string (for logs)."""
    for v in api_keys().values():
        if v and len(v) > 6 and v in s:
            s = s.replace(v, v[:3] + "…" + v[-2:])
    return s
