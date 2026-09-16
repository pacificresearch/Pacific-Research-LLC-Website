"""Data models. Every factual number carries provenance (DataPoint)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Status(str, Enum):
    VERIFIED = "VERIFIED"        # official record / seen by a human against the primary source
    PROVIDER = "PROVIDER DATA"   # returned by an API provider (RentCast, Census, BLS, FHFA)
    ESTIMATED = "ESTIMATED"      # derived by the model from provider data (comps, insurance table)
    ASSUMED = "ASSUMED"          # config.yaml baseline assumption
    UNKNOWN = "UNKNOWN"          # not available — never filled


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DataPoint(BaseModel):
    """A value with its provenance. value=None + status=UNKNOWN is legitimate and preferred to a guess."""
    value: Optional[Any] = None
    status: Status = Status.UNKNOWN
    source: str = ""
    url: str = ""
    retrieved_at: str = Field(default_factory=now_iso)
    data_date: str = ""
    confidence: float = 0.0     # 0..1
    note: str = ""

    @classmethod
    def unknown(cls, note: str = "") -> "DataPoint":
        return cls(value=None, status=Status.UNKNOWN, note=note, confidence=0.0)

    @classmethod
    def assumed(cls, value, note: str, source: str = "config.yaml") -> "DataPoint":
        return cls(value=value, status=Status.ASSUMED, source=source, note=note, confidence=0.4)

    @classmethod
    def provider(cls, value, source: str, url: str = "", data_date: str = "", confidence: float = 0.8, note: str = "") -> "DataPoint":
        return cls(value=value, status=Status.PROVIDER, source=source, url=url, data_date=data_date, confidence=confidence, note=note)

    @classmethod
    def estimated(cls, value, source: str, note: str, url: str = "", confidence: float = 0.5, data_date: str = "") -> "DataPoint":
        return cls(value=value, status=Status.ESTIMATED, source=source, url=url, note=note, confidence=confidence, data_date=data_date)

    @property
    def known(self) -> bool:
        return self.value is not None and self.status != Status.UNKNOWN

    def v(self, default=None):
        return self.value if self.known else default

    def label(self) -> str:
        if not self.known:
            return "UNKNOWN"
        return f"{self.value} [{self.status.value}]"


class Listing(BaseModel):
    """Active sale listing (RentCast /listings/sale shape, normalized)."""
    id: str
    formatted_address: str
    address_line1: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    county: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: str = ""
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[float] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    price: Optional[float] = None
    status: str = ""
    listed_date: str = ""
    last_seen_date: str = ""
    days_on_market: Optional[int] = None
    mls_name: str = ""
    mls_number: str = ""
    listing_agent: Dict[str, Any] = Field(default_factory=dict)
    listing_office: Dict[str, Any] = Field(default_factory=dict)
    hoa_fee: Optional[float] = None
    history: Dict[str, Any] = Field(default_factory=dict)
    unit_count_hint: Optional[int] = None   # from listing, if provided — NOT verified
    cbsa: str = ""
    market_name: str = ""
    source: str = "rentcast:/listings/sale"
    fixture: bool = False
    raw: Dict[str, Any] = Field(default_factory=dict)


class PropertyRecord(BaseModel):
    """RentCast /properties record, normalized."""
    id: str = ""
    unit_count: Optional[int] = None
    year_built: Optional[int] = None
    square_footage: Optional[float] = None
    assessor_id: str = ""
    zoning: str = ""
    owner_occupied: Optional[bool] = None
    last_sale_date: str = ""
    last_sale_price: Optional[float] = None
    tax_assessments: Dict[str, Dict[str, Any]] = Field(default_factory=dict)   # year -> {value, land, improvements}
    property_taxes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)    # year -> {total}
    sale_history: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    features: Dict[str, Any] = Field(default_factory=dict)
    hoa_fee: Optional[float] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class RentComp(BaseModel):
    id: str = ""
    address: str = ""
    price: float
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[float] = None
    property_type: str = ""
    distance_miles: Optional[float] = None
    days_old: Optional[int] = None
    listed_date: str = ""
    status: str = ""
    source: str = ""


class RentEstimate(BaseModel):
    """Per-UNIT monthly rent estimate. Never a manufactured exact gross."""
    case: str                       # contractual | conservative | market_upside
    low: Optional[float] = None
    base: Optional[float] = None
    high: Optional[float] = None
    n_comps: int = 0
    median_comp_distance: Optional[float] = None
    median_comp_age_days: Optional[float] = None
    grade: str = "D"                # A/B/C/D
    status: Status = Status.UNKNOWN
    method: str = ""
    comps: List[RentComp] = Field(default_factory=list)
    layout_assumption: str = ""     # disclosed when units assumed similar


class MarketProfile(BaseModel):
    cbsa: str
    name: str
    state: str = ""
    seed: bool = False
    metrics: Dict[str, DataPoint] = Field(default_factory=dict)
    stage1_score: Optional[float] = None
    stage1_rank: Optional[int] = None
    stage1_components: Dict[str, Any] = Field(default_factory=dict)
    catalyst_score: Optional[float] = None
    catalyst_components: Dict[str, Any] = Field(default_factory=dict)
    research: Dict[str, Any] = Field(default_factory=dict)   # from research/markets/<cbsa>.yaml
    notes: List[str] = Field(default_factory=list)
