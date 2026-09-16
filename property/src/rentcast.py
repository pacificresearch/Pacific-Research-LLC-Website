"""RentCast API v1 client with hard call budget, caching and provenance. The primary property data source."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .config import api_keys
from .database import Cache
from .http_client import HttpError, get_json
from .models import Listing, PropertyRecord, RentComp

log = logging.getLogger("prg.rentcast")
BASE = "https://api.rentcast.io/v1"


class Budget:
    def __init__(self, max_calls: int):
        self.max = max_calls
        self.used = 0
        self.cached_hits = 0
        self.skipped = 0

    def ok(self) -> bool:
        return self.used < self.max


class RentCast:
    def __init__(self, cache: Cache, ttl: Dict[str, float], budget: Budget):
        self.cache = cache
        self.ttl = ttl
        self.budget = budget
        self.key = api_keys().get("RENTCAST_API_KEY")

    @property
    def available(self) -> bool:
        return bool(self.key)

    def _get(self, path: str, params: dict, ttl_key: str) -> Optional[Any]:
        url = f"{BASE}{path}"

        def fetch():
            if not self.key:
                return None
            if not self.budget.ok():
                self.budget.skipped += 1
                log.warning("RentCast budget exhausted (%d); skipping %s", self.budget.max, path)
                return None
            self.budget.used += 1
            try:
                data = get_json(url, params, headers={"X-Api-Key": self.key, "Accept": "application/json"})
            except HttpError as e:
                self.cache.log_call("rentcast", path, cached=False, status=e.status)
                if e.status == 404:      # RentCast returns 404 for "no results" on some endpoints
                    return []
                log.warning("RentCast %s failed: %s", path, e)
                return None
            self.cache.log_call("rentcast", path, cached=False, status=200)
            return data

        data, was_cached = self.cache.cached("rentcast", url, params, self.ttl[ttl_key], fetch, endpoint=path)
        if was_cached:
            self.budget.cached_hits += 1
        return data

    # ---- endpoints -------------------------------------------------------
    def sale_listings(self, city: str, state: str, max_price: float, limit: int = 500, offset: int = 0) -> List[Listing]:
        params = {"city": city, "state": state, "propertyType": "Multi-Family", "status": "Active", "limit": limit, "offset": offset}
        data = self._get("/listings/sale", params, "rentcast_listings")
        out = []
        for r in data or []:
            if r.get("price") is None or r["price"] > max_price:
                continue
            out.append(normalize_listing(r))
        return out

    def property_record(self, address: str) -> Optional[PropertyRecord]:
        data = self._get("/properties", {"address": address}, "rentcast_property")
        if not data:
            return None
        rec = data[0] if isinstance(data, list) else data
        return normalize_property(rec)

    def rent_avm(self, address: str, property_type: str = "Multi-Family", bedrooms: Optional[float] = None,
                 bathrooms: Optional[float] = None, sqft: Optional[float] = None, comp_count: int = 15) -> Optional[dict]:
        params = {"address": address, "propertyType": property_type, "compCount": comp_count}
        for k, v in [("bedrooms", bedrooms), ("bathrooms", bathrooms), ("squareFootage", sqft)]:
            if v:
                params[k] = v
        return self._get("/avm/rent/long-term", params, "rentcast_avm")

    def value_avm(self, address: str, property_type: str = "Multi-Family", comp_count: int = 10) -> Optional[dict]:
        return self._get("/avm/value", {"address": address, "propertyType": property_type, "compCount": comp_count}, "rentcast_avm")

    def rental_listings_near(self, lat: float, lon: float, radius_miles: float, days_old: int, limit: int = 100) -> List[RentComp]:
        params = {"latitude": lat, "longitude": lon, "radius": radius_miles, "status": "Active", "daysOld": days_old, "limit": limit}
        data = self._get("/listings/rental/long-term", params, "rentcast_comps")
        comps = []
        for r in data or []:
            if r.get("price") is None:
                continue
            comps.append(RentComp(id=str(r.get("id", "")), address=r.get("formattedAddress", ""), price=float(r["price"]),
                                  bedrooms=r.get("bedrooms"), bathrooms=r.get("bathrooms"), square_footage=r.get("squareFootage"),
                                  property_type=r.get("propertyType", ""), days_old=r.get("daysOnMarket"),
                                  listed_date=r.get("listedDate", ""), status=r.get("status", ""),
                                  distance_miles=_haversine(lat, lon, r.get("latitude"), r.get("longitude")),
                                  source="rentcast:/listings/rental/long-term"))
        return comps

    def market_stats(self, zip_code: str) -> Optional[dict]:
        return self._get("/markets", {"zipCode": zip_code}, "rentcast_avm")


def _haversine(lat1, lon1, lat2, lon2) -> Optional[float]:
    import math
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)), 2)


def normalize_listing(r: dict) -> Listing:
    return Listing(
        id=str(r.get("id") or r.get("formattedAddress")), formatted_address=r.get("formattedAddress", ""),
        address_line1=r.get("addressLine1", ""), city=r.get("city", ""), state=r.get("state", ""), zip_code=str(r.get("zipCode", "")),
        county=r.get("county", ""), latitude=r.get("latitude"), longitude=r.get("longitude"), property_type=r.get("propertyType", ""),
        bedrooms=r.get("bedrooms"), bathrooms=r.get("bathrooms"), square_footage=r.get("squareFootage"), lot_size=r.get("lotSize"),
        year_built=r.get("yearBuilt"), price=r.get("price"), status=r.get("status", ""), listed_date=r.get("listedDate", "") or "",
        last_seen_date=r.get("lastSeenDate", "") or "", days_on_market=r.get("daysOnMarket"), mls_name=r.get("mlsName", "") or "",
        mls_number=str(r.get("mlsNumber", "") or ""), listing_agent=r.get("listingAgent") or {}, listing_office=r.get("listingOffice") or {},
        hoa_fee=(r.get("hoa") or {}).get("fee"), history=r.get("history") or {}, unit_count_hint=r.get("unitCount"),
        fixture=bool(r.get("_fixture")), cbsa=str(r.get("_cbsa", "") or ""), raw=r)


def normalize_property(r: dict) -> PropertyRecord:
    feats = r.get("features") or {}
    return PropertyRecord(
        id=str(r.get("id", "")), unit_count=feats.get("unitCount") or r.get("unitCount"), year_built=r.get("yearBuilt"),
        square_footage=r.get("squareFootage"), assessor_id=str(r.get("assessorID", "") or ""), zoning=r.get("zoning", "") or "",
        owner_occupied=r.get("ownerOccupied"), last_sale_date=r.get("lastSaleDate", "") or "", last_sale_price=r.get("lastSalePrice"),
        tax_assessments=r.get("taxAssessments") or {}, property_taxes=r.get("propertyTaxes") or {},
        sale_history={k: v for k, v in (r.get("history") or {}).items()}, features=feats, hoa_fee=(r.get("hoa") or {}).get("fee"), raw=r)
