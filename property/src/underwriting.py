"""Line-item underwriting: expenses, standard/economic NOI, all required metrics, stress scenarios, negotiation solver."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import Config
from .financing import feasible_down_payments, loan_constant, monthly_payment
from .models import DataPoint, Status


@dataclass
class DealInputs:
    price: float
    units: Optional[int]                     # None => unknown (underwritten on the listing hint, flagged)
    units_status: Status
    sqft: Optional[float]
    year_built: Optional[int]
    state: str
    cbsa: str
    # per-BUILDING monthly rent by case; each a dict {low, base, high, status, grade, note}
    rent_cases: Dict[str, Dict[str, Any]]
    tax_current_annual: DataPoint            # current owner's bill
    tax_post_sale_annual: DataPoint          # estimated post-purchase bill (may be UNKNOWN)
    post_sale_tax_risk: str                  # LOW/MEDIUM/HIGH/UNKNOWN
    insurance_annual: DataPoint              # ESTIMATED unless a quote
    hoa_monthly: Optional[float] = None
    owner_pays_utilities: Optional[bool] = None   # None = unknown => assume owner pays water/sewer/trash (disclosed)
    master_metered: Optional[bool] = None
    vacant_units: int = 0
    immediate_rehab: DataPoint = field(default_factory=lambda: DataPoint.unknown())
    rental_license_annual: DataPoint = field(default_factory=lambda: DataPoint.unknown())
    inspection_fees_annual: DataPoint = field(default_factory=lambda: DataPoint.unknown())
    other_income_annual: float = 0.0
    contractual_rent_source: str = ""


def _mkt(cfg: Config, cbsa: str, key: str, default):
    return (cfg["market_overrides"].get(cbsa) or {}).get(key, cfg["expenses"].get(key, default))


def units_for_underwriting(d: DealInputs) -> int:
    return int(d.units or 2)


def expense_lines(d: DealInputs, cfg: Config, rent_case: str = "conservative", *, tax_mult=1.0, ins_mult=1.0, maint_mult=1.0,
                  vacancy_pct=None, rent_mult=1.0, rent_point="base", units_vacant_12mo=0) -> Dict[str, Any]:
    """Annual line items with provenance labels. Returns dict with 'lines' (name -> {amount, status, note}) and totals."""
    ex, inc = cfg["expenses"], cfg["income"]
    n = units_for_underwriting(d)
    rc = d.rent_cases[rent_case]
    per_building_monthly = rc.get(rent_point)
    if per_building_monthly is None:
        return {"gsr": None, "lines": {}, "note": f"rent case {rent_case}/{rent_point} unavailable"}
    gsr = per_building_monthly * 12 * rent_mult
    if units_vacant_12mo:
        gsr *= (n - units_vacant_12mo) / n
    vac = inc["vacancy_pct"] if vacancy_pct is None else vacancy_pct
    vacancy = gsr * vac
    credit = gsr * inc["credit_loss_pct"]
    egi = gsr - vacancy - credit + d.other_income_annual
    yb = d.year_built or 0
    capex_pct = ex["capex_pct_of_gsr"]
    capex_note = "ASSUMED baseline"
    if yb and yb < 1940:
        capex_pct, capex_note = ex["capex_pct_of_gsr_pre_1940"], "ASSUMED, raised for pre-1940 stock"
    elif yb and yb < 1960:
        capex_pct, capex_note = ex["capex_pct_of_gsr_pre_1960"], "ASSUMED, raised for pre-1960 stock"
    mgmt_pct = _mkt(cfg, d.cbsa, "management_pct_of_collected", 0.08)
    lines: Dict[str, Dict[str, Any]] = {}

    def add(name, amount, status, note=""):
        lines[name] = {"amount": round(amount, 2), "status": status.value if isinstance(status, Status) else status, "note": note}

    # taxes: post-sale estimate when known, else current bill uplifted with an explicit risk note
    if d.tax_post_sale_annual.known:
        add("property_taxes", d.tax_post_sale_annual.value * tax_mult, d.tax_post_sale_annual.status, d.tax_post_sale_annual.note)
    elif d.tax_current_annual.known:
        add("property_taxes", d.tax_current_annual.value * tax_mult, d.tax_current_annual.status,
            f"CURRENT OWNER'S bill; POST-SALE TAX RISK = {d.post_sale_tax_risk}. " + d.tax_current_annual.note)
    else:
        add("property_taxes", 0.0, Status.UNKNOWN, "no parcel tax bill available — NOI overstated until verified")
    if d.insurance_annual.known:
        add("insurance", d.insurance_annual.value * ins_mult, d.insurance_annual.status, d.insurance_annual.note)
    else:
        add("insurance", 0.0, Status.UNKNOWN, "no estimate")
    add("vacancy", vacancy, Status.ASSUMED, f"{vac:.0%} of GSR")
    add("credit_loss", credit, Status.ASSUMED, f"{inc['credit_loss_pct']:.0%} of GSR")
    add("management", egi * mgmt_pct, Status.ASSUMED, f"{mgmt_pct:.0%} of collected (EGI)")
    add("repairs_maintenance", gsr * ex["repairs_pct_of_gsr"] * maint_mult, Status.ASSUMED, f"{ex['repairs_pct_of_gsr']:.0%} of GSR")
    add("capex_reserve", gsr * capex_pct, Status.ASSUMED, f"{capex_pct:.0%} of GSR — {capex_note} (below-the-line for standard NOI)")
    upm = ex["utilities_per_unit_month"]
    owner_pays = True if d.owner_pays_utilities is None else d.owner_pays_utilities
    util_note = "utility responsibility UNKNOWN — owner-paid water/sewer/trash ASSUMED" if d.owner_pays_utilities is None else ("owner-paid per listing/record" if owner_pays else "tenant-paid per listing/record")
    for u in ["water", "sewer", "trash"]:
        add(u, (upm[u] * n * 12 if owner_pays else 0.0), Status.ASSUMED, util_note)
    elec = ex["common_area_electric_month"] * 12 + (upm["electric"] * n * 12)
    if d.master_metered:
        elec += 90 * n * 12
        add("electric", elec, Status.ASSUMED, "MASTER-METERED flag: owner pays tenant electric (ASSUMED $90/unit/mo)")
    else:
        add("electric", elec, Status.ASSUMED, "common-area only; tenant-paid units ASSUMED" if d.master_metered is None else "common-area only")
    add("gas", upm["gas"] * n * 12 * (1 if d.master_metered else 0), Status.ASSUMED, "tenant-paid ASSUMED unless master-metered")
    add("landscaping", ex["landscaping_month"] * 12, Status.ASSUMED, "ASSUMED")
    add("snow_removal", ex["snow_removal_month_where_relevant"] * 5 if d.state in ex["snow_states"] else 0.0, Status.ASSUMED, "5 winter months ASSUMED" if d.state in ex["snow_states"] else "not a snow state")
    add("pest_control", ex["pest_control_month"] * 12, Status.ASSUMED, "ASSUMED")
    if d.rental_license_annual.known:
        add("rental_licensing", d.rental_license_annual.value, d.rental_license_annual.status, d.rental_license_annual.note)
    else:
        add("rental_licensing", ex["rental_licensing_annual_default"], Status.ASSUMED, "city fee not yet researched")
    if d.inspection_fees_annual.known:
        add("inspection_fees", d.inspection_fees_annual.value, d.inspection_fees_annual.status, d.inspection_fees_annual.note)
    else:
        add("inspection_fees", ex["inspection_fees_annual_default"], Status.ASSUMED, "not researched")
    add("lead_compliance", ex["lead_compliance_annual_pre_1978"] if (yb and yb < 1978) else 0.0, Status.ASSUMED, "pre-1978 disclosure/inspection amortized" if (yb and yb < 1978) else "post-1978 or year built unknown")
    add("hoa", (d.hoa_monthly or 0) * 12, Status.PROVIDER if d.hoa_monthly else Status.ASSUMED, "listing HOA" if d.hoa_monthly else "none reported")
    add("other_recurring", ex["other_recurring_annual"], Status.ASSUMED, "")
    opex_names = [k for k in lines if k not in ("vacancy", "credit_loss", "capex_reserve")]
    opex = sum(lines[k]["amount"] for k in opex_names)
    std_noi = egi - opex
    econ_noi = std_noi - lines["capex_reserve"]["amount"]
    return {"gsr": round(gsr, 2), "egi": round(egi, 2), "opex": round(opex, 2), "standard_noi": round(std_noi, 2),
            "economic_noi": round(econ_noi, 2), "capex_reserve": lines["capex_reserve"]["amount"], "lines": lines,
            "utilities_total": round(sum(lines[u]["amount"] for u in ["water", "sewer", "trash", "electric", "gas"]), 2),
            "units": n, "vacancy_pct": vac}


def metrics(d: DealInputs, cfg: Config, dp_pct: float, rate: float, ex: Dict[str, Any], price: Optional[float] = None) -> Dict[str, Any]:
    """All required property metrics for one equity/rate structure on a computed expense set."""
    price = price if price is not None else d.price
    fin, acq = cfg.financing, cfg["acquisition_costs"]
    n = ex["units"]
    down = price * dp_pct
    loan = price - down
    pmt = monthly_payment(loan, rate, fin.amortization_years, fin.interest_only_months)
    ads = pmt * 12
    closing = price * acq["closing_cost_pct_of_price"]
    rehab = d.immediate_rehab.value if d.immediate_rehab.known else 0.0
    lease_up = acq["lease_up_cost_per_vacant_unit"] * d.vacant_units
    taxes_ins_m = (ex["lines"]["property_taxes"]["amount"] + ex["lines"]["insurance"]["amount"]) / 12
    lender_reserves = (pmt + taxes_ins_m) * fin.lender_reserve_months_piti
    op_reserve = ex["opex"] / 12 * acq["operating_reserve_months_opex"]
    coc_denominator = down + closing + rehab + lease_up
    total_cash = coc_denominator + lender_reserves + op_reserve
    std_noi, econ_noi, gsr = ex["standard_noi"], ex["economic_noi"], ex["gsr"]
    cf_econ = econ_noi - ads
    cf_std = std_noi - ads
    return {
        "price": price, "down_payment_pct": dp_pct, "down_payment": round(down, 2), "loan_amount": round(loan, 2),
        "interest_rate_assumed": rate, "monthly_debt_service": round(pmt, 2), "annual_debt_service": round(ads, 2),
        "price_per_unit": round(price / n, 2), "price_per_sqft": round(price / d.sqft, 2) if d.sqft else None,
        "gross_monthly_rent": round(gsr / 12, 2), "gross_annual_rent": round(gsr, 2),
        "rent_to_price": round(gsr / 12 / price, 4), "grm": round(price / gsr, 2) if gsr else None,
        "standard_noi": std_noi, "economic_noi": econ_noi,
        "standard_cap_rate": round(std_noi / price, 4), "economic_cap_rate": round(econ_noi / price, 4),
        "monthly_cash_flow_standard": round(cf_std / 12, 2), "monthly_cash_flow": round(cf_econ / 12, 2),
        "annual_cash_flow": round(cf_econ, 2),
        "cash_on_cash": round(cf_econ / coc_denominator, 4) if coc_denominator else None,
        "standard_dscr": round(std_noi / ads, 3) if ads else None, "economic_dscr": round(econ_noi / ads, 3) if ads else None,
        "debt_yield": round(std_noi / loan, 4) if loan else None,
        "operating_expense_ratio": round(ex["opex"] / ex["egi"], 4) if ex["egi"] else None,
        "break_even_occupancy": round((ex["opex"] + ads + ex["capex_reserve"]) / gsr, 4) if gsr else None,
        "closing_costs": round(closing, 2), "immediate_rehab": rehab, "lease_up_costs": lease_up,
        "lender_reserves": round(lender_reserves, 2), "operating_reserve": round(op_reserve, 2),
        "coc_denominator": round(coc_denominator, 2), "total_cash_required": round(total_cash, 2),
        "return_on_total_cash": round(cf_econ / total_cash, 4) if total_cash else None,
        "remaining_capital_vs_max": round(cfg.capital.max_down_payment - down, 2),
        "exceeds_max_down": down > cfg.capital.max_down_payment,
    }


def scenarios(d: DealInputs, cfg: Config, dp_pct: float, rate: float) -> Dict[str, Dict[str, Any]]:
    """BASE / DOWNSIDE / SEVERE / UPSIDE — each with monthly cash flow and DSCR."""
    s = cfg["stress"]
    out = {}
    base_ex = expense_lines(d, cfg, "conservative")
    if base_ex.get("gsr") is None:
        return {}
    out["base"] = metrics(d, cfg, dp_pct, rate, base_ex)
    dn = s["downside"]
    out["downside"] = metrics(d, cfg, dp_pct, rate, expense_lines(d, cfg, "conservative", rent_mult=dn["rent_mult"], vacancy_pct=dn["vacancy_pct"],
                                                                  ins_mult=dn["insurance_mult"], maint_mult=dn["maintenance_mult"], tax_mult=dn["tax_mult"]))
    sv = s["severe"]
    out["severe"] = metrics(d, cfg, dp_pct, rate, expense_lines(d, cfg, "conservative", units_vacant_12mo=1, ins_mult=sv["insurance_mult"],
                                                                maint_mult=sv["maintenance_mult"], tax_mult=sv["tax_mult"]))
    up_case = "market_upside" if d.rent_cases.get("market_upside", {}).get("base") else "conservative"
    out["upside"] = metrics(d, cfg, dp_pct, rate, expense_lines(d, cfg, up_case, vacancy_pct=s["upside"]["vacancy_pct"]))
    return out


def equity_structures(d: DealInputs, cfg: Config, rate: Optional[float] = None) -> Dict[str, Any]:
    """Model every feasible down payment; identify max-cash-flow and max-CoC structures; recommend with liquidity bias."""
    rate = rate or cfg.financing.interest_rate
    base_ex = expense_lines(d, cfg, "conservative")
    if base_ex.get("gsr") is None:
        return {"structures": [], "recommended": None}
    pcts = feasible_down_payments(cfg.capital.down_payment_pcts, d.price, cfg.capital.max_down_payment)
    rows = []
    for p in pcts:
        m = metrics(d, cfg, p, rate, base_ex)
        m["severe_monthly_cash_flow"] = metrics(d, cfg, p, rate, expense_lines(d, cfg, "conservative", units_vacant_12mo=1,
                                                ins_mult=cfg["stress"]["severe"]["insurance_mult"], maint_mult=cfg["stress"]["severe"]["maintenance_mult"],
                                                tax_mult=cfg["stress"]["severe"]["tax_mult"]))["monthly_cash_flow"]
        rows.append(m)
    if not rows:
        return {"structures": [], "recommended": None, "note": "no down payment within the $200K maximum at this price"}
    max_cf = max(rows, key=lambda r: r["monthly_cash_flow"])
    max_coc = max(rows, key=lambda r: (r["cash_on_cash"] or -9))
    t = cfg["targets"]
    # liquidity rule: the smallest equity that clears preferred DSCR and keeps severe-case CF >= -$300/mo; else the smallest equity
    # that clears DSCR alone; else the baseline. Marginal equity earns exactly the loan constant, so more equity never "improves" CoC.
    rec = next((r for r in rows if (r["economic_dscr"] or 0) >= t["economic_dscr"]["prefer"] and r["severe_monthly_cash_flow"] >= -300), None) \
        or next((r for r in rows if (r["economic_dscr"] or 0) >= t["economic_dscr"]["prefer"]), None) or rows[0]
    return {"structures": rows, "max_cash_flow_structure": max_cf["down_payment_pct"], "max_coc_structure": max_coc["down_payment_pct"],
            "recommended_structure": rec["down_payment_pct"], "marginal_equity_yield": round(loan_constant(rate, cfg.financing.amortization_years), 4),
            "recommendation_note": f"Every extra equity dollar earns the loan constant ({loan_constant(rate, cfg.financing.amortization_years):.2%}), so larger down payments trade liquidity for a fixed, mortgage-rate return. Recommended = smallest equity clearing DSCR {t['economic_dscr']['prefer']} with severe-case tolerance."}


def rate_sensitivity(d: DealInputs, cfg: Config, dp_pct: float) -> List[Dict[str, Any]]:
    base_ex = expense_lines(d, cfg, "conservative")
    if base_ex.get("gsr") is None:
        return []
    out = []
    for r in cfg.financing.rate_sensitivity:
        m = metrics(d, cfg, dp_pct, r, base_ex)
        out.append({"rate": r, "monthly_debt_service": m["monthly_debt_service"], "monthly_cash_flow": m["monthly_cash_flow"],
                    "cash_on_cash": m["cash_on_cash"], "economic_dscr": m["economic_dscr"]})
    return out


def insurance_sensitivity(d: DealInputs, cfg: Config, dp_pct: float, rate: float) -> List[Dict[str, Any]]:
    out = []
    for mult in cfg["insurance"]["sensitivity"]:
        ex = expense_lines(d, cfg, "conservative", ins_mult=mult)
        if ex.get("gsr") is None:
            continue
        m = metrics(d, cfg, dp_pct, rate, ex)
        out.append({"multiplier": mult, "insurance_annual": ex["lines"]["insurance"]["amount"], "monthly_cash_flow": m["monthly_cash_flow"], "economic_dscr": m["economic_dscr"]})
    return out


def _at_price(d: DealInputs, cfg: Config, dp_pct: float, rate: float, price: float) -> Dict[str, Any]:
    """Re-underwrite at a hypothetical price. Insurance and post-sale tax estimates that scale with price are rescaled."""
    dd = copy.deepcopy(d)
    ratio = price / d.price
    dd.price = price
    if dd.tax_post_sale_annual.known and "scales with price" in dd.tax_post_sale_annual.note:
        dd.tax_post_sale_annual.value = dd.tax_post_sale_annual.value * ratio
    ex = expense_lines(dd, cfg, "conservative")
    return metrics(dd, cfg, dp_pct, rate, ex, price=price)


def negotiation(d: DealInputs, cfg: Config, dp_pct: float, rate: float) -> Dict[str, Any]:
    """Price at which each target is met (bisection on price). Underwriting ceiling = min of the preferred-target prices, capped at ask."""
    t = cfg["targets"]
    targets = {"econ_cap_9": ("economic_cap_rate", t["economic_cap_rate"]["prefer"]), "econ_cap_10": ("economic_cap_rate", t["economic_cap_rate"]["strong"]),
               "coc_12": ("cash_on_cash", t["cash_on_cash"]["prefer"]), "coc_15": ("cash_on_cash", t["cash_on_cash"]["strong"]),
               "dscr_1_25": ("economic_dscr", t["economic_dscr"]["prefer"]), "dscr_1_40": ("economic_dscr", t["economic_dscr"]["strong"])}
    out: Dict[str, Any] = {"asking_price": d.price}
    if expense_lines(d, cfg, "conservative").get("gsr") is None:
        return out
    for name, (metric, goal) in targets.items():
        lo, hi = d.price * 0.25, d.price * 1.5
        if (_at_price(d, cfg, dp_pct, rate, lo)[metric] or -9) < goal:
            out[name] = None       # unattainable even at 25% of ask
            continue
        for _ in range(40):
            mid = (lo + hi) / 2
            if (_at_price(d, cfg, dp_pct, rate, mid)[metric] or -9) >= goal:
                lo = mid
            else:
                hi = mid
        out[name] = round(lo, -2)
    prefer_prices = [out[k] for k in ("econ_cap_9", "coc_12", "dscr_1_25") if out.get(k)]
    out["underwriting_ceiling_price"] = round(min(prefer_prices + [d.price]), -2) if prefer_prices else None
    out["ceiling_vs_ask_pct"] = round(out["underwriting_ceiling_price"] / d.price - 1, 4) if out.get("underwriting_ceiling_price") else None
    out["note"] = "Underwriting ceiling = lowest price among the 9% economic cap / 12% CoC / 1.25 DSCR targets, capped at ask. This is NOT an offer recommendation."
    return out
