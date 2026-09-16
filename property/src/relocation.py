"""Relocation incentives + job/living overlay for finalist markets. One-time money is YEAR-1 PERSONAL BENEFIT, never NOI."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import MarketProfile

NO_INCOME_TAX_STATES = {"TX", "FL", "TN", "NV", "WA", "WY", "SD", "AK", "NH"}
INCENTIVE_FIELDS = ["program", "dollar_value", "cash_or_noncash", "eligibility", "minimum_income", "employment_requirement",
                    "home_purchase_requirement", "residency_requirement", "minimum_stay", "application_deadline", "funding_availability", "source_url"]


def incentives(p: MarketProfile) -> Dict[str, Any]:
    items: List[dict] = p.research.get("incentives") or []
    rows = []
    cash_total = 0.0
    for it in items:
        row = {f: it.get(f, "UNKNOWN") for f in INCENTIVE_FIELDS}
        row["status"] = "VERIFIED" if it.get("verified") else "RESEARCH LEAD — verify"
        rows.append(row)
        if str(it.get("cash_or_noncash", "")).lower().startswith("cash"):
            try:
                cash_total += float(it.get("dollar_value") or 0)
            except (TypeError, ValueError):
                pass
    return {"programs": rows, "year1_personal_economic_benefit_cash": cash_total if items else None,
            "status": "researched" if items else "NOT RESEARCHED — no incentive data on file; leads queued", "note": "Never added to NOI."}


def living_overlay(p: MarketProfile) -> Dict[str, Any]:
    m = p.metrics
    v = lambda k: (m[k].v() if k in m else None)
    return {"metro_unemployment": v("unemployment_rate"), "employment_growth_1y": v("employment_growth_1y"),
            "avg_weekly_wage": v("avg_weekly_wage"), "wage_growth_1y": v("wage_growth_1y"), "median_hh_income": v("median_hh_income"),
            "major_employers": p.research.get("major_employers") or "UNKNOWN — not researched",
            "economic_diversity_hhi": v("industry_hhi"), "cost_of_living": p.research.get("cost_of_living") or "UNKNOWN (no reliable free source wired)",
            "state_income_tax": ("none" if p.state in NO_INCOME_TAX_STATES else (p.research.get("state_income_tax") or "state income tax applies — rate not researched")),
            "relocation_benefit_cash": incentives(p)["year1_personal_economic_benefit_cash"]}


def living_score(p: MarketProfile) -> float:
    """0..1 for Ranking E's 5% relocation/living component. Only from data present."""
    o = living_overlay(p)
    parts = []
    if o["metro_unemployment"] is not None:
        parts.append(max(0.0, min(1.0, (7.0 - o["metro_unemployment"]) / 4.0)))
    if o["employment_growth_1y"] is not None:
        parts.append(max(0.0, min(1.0, (o["employment_growth_1y"] + 0.01) / 0.04)))
    parts.append(1.0 if o["state_income_tax"] == "none" else 0.5)
    if o["relocation_benefit_cash"]:
        parts.append(min(1.0, o["relocation_benefit_cash"] / 10000))
    return round(sum(parts) / len(parts), 3)
