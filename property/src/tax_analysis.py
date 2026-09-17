"""Property taxes: actual parcel bill, assessed value, effective rate, and the post-sale estimate — always distinguished."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .config import Config
from .models import DataPoint, PropertyRecord, Status

log = logging.getLogger("prg.tax")


def _latest(d: Dict[str, Dict[str, Any]], field: str) -> tuple[Optional[int], Optional[float]]:
    best = None
    for yr, rec in (d or {}).items():
        try:
            y, v = int(yr), rec.get(field)
        except (TypeError, ValueError):
            continue
        if v is None:
            continue
        if best is None or y > best[0]:
            best = (y, float(v))
    return best if best else (None, None)


def analyze(record: Optional[PropertyRecord], price: float, state: str, cfg: Config, research: Optional[dict] = None) -> Dict[str, Any]:
    """Returns current bill, assessed value, history, effective rate, post-sale estimate, risk, assessor source."""
    out: Dict[str, Any] = {}
    research = research or {}
    src = "RentCast property record (county assessor data via provider)"
    url = "https://api.rentcast.io/v1/properties"
    if record and record.property_taxes:
        y, bill = _latest(record.property_taxes, "total")
        out["current_tax_bill"] = DataPoint.provider(bill, src, url, str(y), 0.8, "current OWNER's bill — not the post-purchase bill") if bill else DataPoint.unknown()
    else:
        out["current_tax_bill"] = DataPoint.unknown("no parcel tax bill in property record — pull from county treasurer")
    if record and record.tax_assessments:
        y, av = _latest(record.tax_assessments, "value")
        out["assessed_value"] = DataPoint.provider(av, src, url, str(y), 0.8) if av else DataPoint.unknown()
        out["assessment_history"] = {yr: rec for yr, rec in sorted(record.tax_assessments.items())}
    else:
        out["assessed_value"] = DataPoint.unknown()
        out["assessment_history"] = {}
    out["tax_history"] = {yr: rec for yr, rec in sorted((record.property_taxes if record else {}).items())}
    bill, av = out["current_tax_bill"].v(), out["assessed_value"].v()
    if bill and av:
        out["effective_tax_rate_on_assessed"] = DataPoint.estimated(round(bill / av, 5), src, "latest bill / latest assessed value (parcel-specific)", url, 0.8)
        out["effective_tax_rate_on_price"] = DataPoint.estimated(round(bill / price, 5), src, "latest bill / asking price", url, 0.7)
    else:
        out["effective_tax_rate_on_assessed"] = DataPoint.unknown()
        out["effective_tax_rate_on_price"] = DataPoint.unknown()

    # post-sale treatment: verified research file > state reference note > UNKNOWN
    rules = cfg["property_taxes"]["post_sale_reassessment_notes"]
    tr = research.get("tax_rules") or {}
    if tr.get("post_sale_treatment"):
        risk = tr.get("risk", "UNKNOWN").upper()
        out["post_sale_treatment"] = DataPoint(value=tr["post_sale_treatment"], status=Status.VERIFIED if tr.get("verified") else Status.ESTIMATED,
                                               source=tr.get("source", "research/markets"), url=tr.get("source_url", ""), confidence=0.85 if tr.get("verified") else 0.6)
        out["assessor_url"] = tr.get("assessor_url", "")
        out["treasurer_url"] = tr.get("treasurer_url", "")
    elif state in rules:
        r = rules[state]
        risk = r["risk"].upper()
        out["post_sale_treatment"] = DataPoint(value=r["treatment"], status=Status.ESTIMATED, source="config reference note (state-level) — VERIFY with county", url=r["source"], confidence=0.5)
        out["assessor_url"] = ""
        out["treasurer_url"] = ""
    else:
        risk = "UNKNOWN"
        out["post_sale_treatment"] = DataPoint.unknown("reassessment-after-sale treatment not determined for this state")
        out["assessor_url"] = ""
        out["treasurer_url"] = ""
    out["post_sale_tax_risk"] = risk

    # post-sale estimate. Rule: never assume the current bill survives the sale.
    eff_assessed = out["effective_tax_rate_on_assessed"].v()
    if tr.get("post_sale_estimate_annual"):
        out["post_sale_tax_estimate"] = DataPoint(value=float(tr["post_sale_estimate_annual"]), status=Status.VERIFIED if tr.get("verified") else Status.ESTIMATED,
                                                  source=tr.get("source", "research"), url=tr.get("source_url", ""), note="from research file")
    elif bill and av and risk in ("HIGH", "MEDIUM") and price > av:
        # reassessment toward price at the parcel's own effective rate on assessed value (scales with price for the negotiation solver)
        est = bill / av * price if eff_assessed else None
        if risk == "MEDIUM":
            est = (bill + est) / 2   # partial step-up
        out["post_sale_tax_estimate"] = DataPoint.estimated(round(est), src, f"current bill re-based toward asking price at the parcel's effective rate; risk={risk}; scales with price", url, 0.5 if risk == "HIGH" else 0.45)
    elif bill and risk == "LOW":
        out["post_sale_tax_estimate"] = DataPoint.estimated(round(bill * 1.05), src, "sale does not trigger reassessment in this state; +5% cushion; VERIFY county cycle", url, 0.6)
    elif bill:
        out["post_sale_tax_estimate"] = DataPoint.estimated(round(bill * 1.25), src, "POST-SALE TAX RISK = UNKNOWN; +25% cushion applied, confidence reduced", url, 0.3)
    else:
        out["post_sale_tax_estimate"] = DataPoint.unknown("no bill; cannot estimate without fabricating — must be pulled from county")
    return out
