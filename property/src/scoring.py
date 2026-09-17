"""Underwriting confidence (0-100), the five separate rankings, and the auditable Ranking E composite."""
from __future__ import annotations

from typing import Any, Dict, List

from .config import Config


def confidence_score(pr: Dict[str, Any]) -> Dict[str, Any]:
    """pr = the assembled property result dict. Deductions are listed so the score is auditable."""
    score, deductions = 100, []

    def ded(pts, why):
        nonlocal score
        score -= pts
        deductions.append({"points": pts, "reason": why})

    rent = pr["rent"]["per_building"]
    if rent["contractual"]["base"] is None:
        ded(10, "actual contractual rents unknown")
    g = rent["conservative"].get("grade", "D")
    ded({"A": 0, "B": 5, "C": 12, "D": 20}[g], f"rental comp grade {g}")
    if rent["conservative"]["base"] is None:
        ded(15, "no market rent estimate")
    t = pr["taxes"]
    if not t["current_tax_bill"]["known"]:
        ded(10, "no parcel tax bill")
    if t["post_sale_tax_risk"] == "UNKNOWN":
        ded(15, "POST-SALE TAX RISK = UNKNOWN")
    elif t["post_sale_treatment"]["status"] != "VERIFIED":
        ded(5, "post-sale tax treatment from state reference note, not county-verified")
    if pr["insurance"]["status"] != "VERIFIED":
        ded(10, "insurance ESTIMATED, no quote")
    if pr["units_status"] != "PROVIDER DATA" and pr["units_status"] != "VERIFIED":
        ded(15, "unit count unverified")
    ded(8, "legal unit status unverified") if not pr.get("legal_units_verified") else None
    ded(10, "utility responsibilities unverified") if pr.get("owner_pays_utilities") is None else None
    if pr.get("listing_stale_days", 0) > 7:
        ded(5, f"listing last seen {pr['listing_stale_days']} days ago")
    if pr.get("fixture"):
        ded(30, "FIXTURE / SYNTHETIC LISTING — not a real property")
    return {"score": max(0, score), "deductions": deductions}


def _norm(vals: List[float], v: float, lo: float, hi: float) -> float:
    return max(0.0, min(1.0, (v - lo) / (hi - lo))) if hi > lo else 0.5


def rankings(results: List[Dict[str, Any]], cfg: Config) -> Dict[str, List[Dict[str, Any]]]:
    """A: conservative monthly CF. B: CoC. C: CF + appreciation asymmetry. D: downside-protected. E: composite for the stated strategy."""
    t = cfg["targets"]
    live = [r for r in results if r.get("base") and r["base"].get("monthly_cash_flow") is not None]
    out: Dict[str, List[Dict[str, Any]]] = {}

    def key(r):
        return {"id": r["listing"]["id"], "address": r["listing"]["formatted_address"], "units": r["units"], "price": r["listing"]["price"], "confidence": r["confidence"]["score"]}

    A = sorted(live, key=lambda r: r["base"]["monthly_cash_flow"], reverse=True)
    out["A_conservative_cash_flow"] = [{**key(r), "monthly_cash_flow": r["base"]["monthly_cash_flow"], "economic_dscr": r["base"]["economic_dscr"]} for r in A]
    B = sorted(live, key=lambda r: r["base"]["cash_on_cash"] or -9, reverse=True)
    out["B_cash_on_cash"] = [{**key(r), "cash_on_cash": r["base"]["cash_on_cash"], "coc_denominator": r["base"]["coc_denominator"]} for r in B]
    for r in live:
        cf = _norm([], r["base"]["monthly_cash_flow"], 0, t["monthly_cash_flow"]["exceptional"])
        cat = (r["market"]["catalyst_score"] or 0) / 100
        r["_asym"] = round(0.5 * cf + 0.5 * cat, 3)
        sev = r["scenarios"].get("severe", {}).get("monthly_cash_flow")
        dn = r["scenarios"].get("downside", {}).get("monthly_cash_flow")
        r["_downside"] = round(0.4 * _norm([], sev if sev is not None else -2000, -1500, 500) + 0.3 * _norm([], dn if dn is not None else -2000, -500, 1000)
                               + 0.2 * _norm([], r["base"]["economic_dscr"] or 0, 1.0, 1.6) + 0.1 * (1 - (r["hazards"]["hazard_score"] / 100)), 3)
    C = sorted(live, key=lambda r: r["_asym"], reverse=True)
    out["C_cash_flow_plus_appreciation"] = [{**key(r), "asymmetry_score": r["_asym"], "monthly_cash_flow": r["base"]["monthly_cash_flow"], "catalyst_score": r["market"]["catalyst_score"]} for r in C]
    D = sorted(live, key=lambda r: r["_downside"], reverse=True)
    out["D_downside_protected"] = [{**key(r), "downside_score": r["_downside"], "severe_cf": r["scenarios"].get("severe", {}).get("monthly_cash_flow"), "downside_cf": r["scenarios"].get("downside", {}).get("monthly_cash_flow"), "economic_dscr": r["base"]["economic_dscr"]} for r in D]
    w = cfg["ranking_e_weights"]
    for r in live:
        b = r["base"]
        comp = {
            "cash_flow_economics": round(0.5 * _norm([], b["monthly_cash_flow"], 0, t["monthly_cash_flow"]["exceptional"]) + 0.5 * _norm([], b["economic_cap_rate"], 0.05, 0.12), 3),
            "capital_efficiency": round(_norm([], b["cash_on_cash"] or 0, 0.0, t["cash_on_cash"]["strong"] + 0.05), 3),
            "appreciation_catalysts": round((r["market"]["catalyst_score"] or 0) / 100, 3),
            "downside_property_risk": r["_downside"],
            "rent_employment_fundamentals": round(0.5 * _norm([], r["market"].get("rent_to_value_metro") or 0, 0.04, 0.09) + 0.5 * _norm([], r["market"].get("employment_growth_1y") or 0, -0.01, 0.03), 3),
            "relocation_living_economics": r["market"].get("living_score", 0.5),
        }
        raw = sum(w[k] * comp[k] for k in w)
        r["ranking_e"] = {"components": comp, "weights": w, "raw_score": round(raw * 100, 1),
                          "confidence_adjusted": round(raw * 100 * (0.6 + 0.4 * r["confidence"]["score"] / 100), 1)}
    E = sorted(live, key=lambda r: r["ranking_e"]["confidence_adjusted"], reverse=True)
    out["E_overall_strategy"] = [{**key(r), "score": r["ranking_e"]["confidence_adjusted"], "raw_score": r["ranking_e"]["raw_score"], **{f"c_{k}": v for k, v in r["ranking_e"]["components"].items()}} for r in E]
    return out
