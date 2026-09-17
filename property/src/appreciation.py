"""APPRECIATION CATALYST SCORE (0-100) — separate from cash flow. Quantitative fundamentals + verified project catalysts with status tiers."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import MarketProfile

STATUS_CREDIT = {"completed": 0.6, "under_construction": 1.0, "dirt_moving": 1.0, "announced": 0.45, "speculative": 0.15, "cancelled": 0.0}
ENERGY_TERMS = ["oil", "gas", "lng", "energy", "refinery", "permian", "pipeline", "petrochemical"]


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _lin(v: Optional[float], lo: float, hi: float) -> Optional[float]:
    return None if v is None else _clamp((v - lo) / (hi - lo))


def catalyst_score(p: MarketProfile) -> Dict[str, Any]:
    m = p.metrics
    comps: Dict[str, Optional[float]] = {}
    # fundamentals (each 0..1). HPI is CONTEXT: strong past appreciation gets modest credit; lagging HPI vs strong fundamentals = re-rating potential.
    comps["population_growth"] = _lin(m.get("population_growth_4y") and m["population_growth_4y"].v(), -0.02, 0.08)
    comps["net_migration"] = _lin(m.get("domestic_migration_per_1000") and m["domestic_migration_per_1000"].v(), -5, 15)
    comps["employment_growth"] = _lin(m.get("employment_growth_1y") and m["employment_growth_1y"].v(), -0.01, 0.03)
    ur_chg = m.get("unemployment_rate_yoy_change") and m["unemployment_rate_yoy_change"].v()
    comps["unemployment_trend"] = _lin(-ur_chg, -0.5, 0.5) if ur_chg is not None else None
    comps["wage_growth"] = _lin(m.get("wage_growth_1y") and m["wage_growth_1y"].v(), 0.0, 0.06)
    comps["income_growth"] = _lin(m.get("median_hh_income_growth_5y") and m["median_hh_income_growth_5y"].v(), 0.10, 0.35)
    comps["rent_growth"] = _lin(m.get("rent_growth_1y") and m["rent_growth_1y"].v(), -0.02, 0.06)
    pv = m.get("permits_vs_pop_growth") and m["permits_vs_pop_growth"].v()
    comps["supply_constraint"] = (1 - _lin(pv, 0.2, 1.5)) if pv is not None else None   # fewer permits per new resident = tighter supply
    h3 = m.get("hpi_3y_cagr") and m["hpi_3y_cagr"].v()
    comps["hpi_context"] = _lin(h3, -0.02, 0.08) if h3 is not None else None
    # re-rating: fundamentals strong but HPI lagging
    fund = [comps[k] for k in ("population_growth", "net_migration", "employment_growth") if comps.get(k) is not None]
    if fund and h3 is not None:
        comps["re_rating_gap"] = _clamp((sum(fund) / len(fund)) - _lin(h3, 0.0, 0.10) + 0.5)
    # verified project catalysts from research file
    projects: List[dict] = (p.research.get("catalysts") or [])
    proj_score, energy_share, proj_detail = 0.0, 0.0, []
    emp = m.get("employment_level") and m["employment_level"].v()
    total_jobs = 0.0
    for pr in projects:
        credit = STATUS_CREDIT.get(str(pr.get("status", "announced")).lower().replace(" ", "_").replace("/", "_"), 0.45)
        jobs = float(pr.get("jobs") or 0)
        inv = float(pr.get("investment_usd") or 0)
        size = _clamp(jobs / (emp * 0.01) if emp else 0, 0, 1) * 0.6 + _clamp(inv / 1e9, 0, 1) * 0.4
        contrib = credit * size
        proj_score += contrib
        total_jobs += jobs * credit
        if any(t in (pr.get("sector", "") + pr.get("name", "")).lower() for t in ENERGY_TERMS):
            energy_share += contrib
        proj_detail.append({**pr, "credit": credit, "contribution": round(contrib, 3)})
    comps["project_catalysts"] = _clamp(proj_score) if projects else None
    # concentration penalty: industry HHI (ACS) and/or single-sector dominance among catalysts, and explicit research flag
    hhi = m.get("industry_hhi") and m["industry_hhi"].v()
    penalty = 0.0
    if hhi is not None and hhi > 0.14:
        penalty += _clamp((hhi - 0.14) / 0.10) * 0.15
    if proj_score and energy_share / proj_score > 0.7:
        penalty += 0.10
    if p.research.get("single_employer_dependence"):
        penalty += 0.10
    weights = {"population_growth": 0.12, "net_migration": 0.12, "employment_growth": 0.10, "unemployment_trend": 0.05, "wage_growth": 0.08,
               "income_growth": 0.05, "rent_growth": 0.08, "supply_constraint": 0.10, "hpi_context": 0.05, "re_rating_gap": 0.05, "project_catalysts": 0.20}
    active = {k: w for k, w in weights.items() if comps.get(k) is not None}
    if not active:
        return {"score": None, "components": comps, "penalty": penalty, "coverage": "no data", "projects": proj_detail}
    raw = sum(active[k] * comps[k] for k in active) / sum(active.values())
    coverage = sum(active.values())
    score = round(_clamp(raw - penalty) * 100, 1)
    return {"score": score, "components": {k: (round(v, 3) if v is not None else None) for k, v in comps.items()}, "penalty": round(penalty, 3),
            "coverage": f"{coverage:.0%} of catalyst weight has data" + ("" if projects else "; NO verified project catalysts on file — research pending"),
            "confidence": round(coverage * (1.0 if projects else 0.7), 2), "projects": proj_detail,
            "energy_boom_watch": bool(energy_share and proj_score and energy_share / proj_score > 0.5) or bool(p.research.get("energy_boom_watch")),
            "supply_mismatch_signal": (comps.get("supply_constraint") or 0) > 0.6 and (comps.get("net_migration") or 0) > 0.6}
