"""Hand-checked underwriting math. Run: python3 -m pytest property/tests -q"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import underwriting as uw  # noqa: E402
from src.config import load_config  # noqa: E402
from src.financing import feasible_down_payments, loan_constant, monthly_payment  # noqa: E402
from src.models import DataPoint, Status  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def deal(price=300000, units=4, rent_unit=850, tax=4100, post_sale=None, ins=2500, state="IN", yb=1925, risk="MEDIUM"):
    rc = {"contractual": {"low": None, "base": None, "high": None, "status": "UNKNOWN", "grade": "D", "note": ""},
          "conservative": {"low": rent_unit * units * 0.94, "base": rent_unit * units, "high": rent_unit * units * 1.06, "status": "ESTIMATED", "grade": "A", "note": ""},
          "market_upside": {"low": rent_unit * units, "base": rent_unit * units * 1.08, "high": rent_unit * units * 1.12, "status": "ESTIMATED", "grade": "A", "note": ""}}
    return uw.DealInputs(price=price, units=units, units_status=Status.PROVIDER, sqft=3600, year_built=yb, state=state, cbsa="23060", rent_cases=rc,
                         tax_current_annual=DataPoint.provider(tax, "t"), tax_post_sale_annual=(DataPoint.estimated(post_sale, "t", "x") if post_sale else DataPoint.unknown()),
                         post_sale_tax_risk=risk, insurance_annual=DataPoint.estimated(ins, "i", "table"), owner_pays_utilities=True)


def test_monthly_payment_matches_standard_amortization():
    # $225,000 at 7.5%/30y = $1,573.23 (standard mortgage tables)
    assert monthly_payment(225000, 0.075, 30) == pytest.approx(1573.23, abs=0.01)
    assert monthly_payment(0, 0.075, 30) == 0
    assert monthly_payment(120000, 0.0, 30) == pytest.approx(333.33, abs=0.01)


def test_loan_constant_is_annual_payment_per_dollar():
    assert loan_constant(0.075, 30) == pytest.approx(1573.23 * 12 / 225000, rel=1e-4)


def test_feasible_down_payments_respect_200k_cap(cfg):
    assert feasible_down_payments(cfg.capital.down_payment_pcts, 400000, 200000) == [0.25, 0.30, 0.35, 0.40, 0.50]
    assert feasible_down_payments(cfg.capital.down_payment_pcts, 390000, 150000) == [0.25, 0.30, 0.35]


def test_noi_definitions(cfg):
    d = deal()
    ex = uw.expense_lines(d, cfg, "conservative")
    gsr = 850 * 4 * 12
    assert ex["gsr"] == pytest.approx(gsr)
    assert ex["lines"]["vacancy"]["amount"] == pytest.approx(gsr * 0.05)
    assert ex["lines"]["credit_loss"]["amount"] == pytest.approx(gsr * 0.01)
    egi = gsr * 0.94
    assert ex["egi"] == pytest.approx(egi)
    assert ex["lines"]["management"]["amount"] == pytest.approx(egi * 0.08)
    assert ex["lines"]["repairs_maintenance"]["amount"] == pytest.approx(gsr * 0.05)
    # pre-1940 building -> 8% capex, and capex is NOT in standard NOI
    assert ex["lines"]["capex_reserve"]["amount"] == pytest.approx(gsr * 0.08)
    opex_names = [k for k in ex["lines"] if k not in ("vacancy", "credit_loss", "capex_reserve")]
    assert ex["standard_noi"] == pytest.approx(egi - sum(ex["lines"][k]["amount"] for k in opex_names))
    assert ex["economic_noi"] == pytest.approx(ex["standard_noi"] - gsr * 0.08)
    # taxes: no post-sale estimate -> current bill used but note carries the risk
    assert ex["lines"]["property_taxes"]["amount"] == 4100
    assert "POST-SALE TAX RISK = MEDIUM" in ex["lines"]["property_taxes"]["note"]
    assert ex["lines"]["snow_removal"]["amount"] > 0  # IN is a snow state


def test_metrics_consistency(cfg):
    d = deal()
    ex = uw.expense_lines(d, cfg, "conservative")
    m = uw.metrics(d, cfg, 0.25, 0.075, ex)
    assert m["down_payment"] == 75000 and m["loan_amount"] == 225000
    assert m["monthly_debt_service"] == pytest.approx(1573.23, abs=0.01)
    assert m["standard_cap_rate"] == pytest.approx(ex["standard_noi"] / 300000, abs=1e-4)
    assert m["economic_cap_rate"] == pytest.approx(ex["economic_noi"] / 300000, abs=1e-4)
    assert m["monthly_cash_flow"] == pytest.approx((ex["economic_noi"] - m["annual_debt_service"]) / 12, abs=0.01)
    assert m["coc_denominator"] == pytest.approx(75000 + 9000 + 0 + 0)   # down + 3% closing + rehab + lease-up
    assert m["cash_on_cash"] == pytest.approx(m["annual_cash_flow"] / 84000, abs=1e-4)
    assert m["economic_dscr"] == pytest.approx(ex["economic_noi"] / m["annual_debt_service"], rel=1e-3)
    assert m["debt_yield"] == pytest.approx(ex["standard_noi"] / 225000, rel=1e-3)
    assert m["break_even_occupancy"] == pytest.approx((ex["opex"] + m["annual_debt_service"] + ex["capex_reserve"]) / ex["gsr"], rel=1e-3)
    assert m["total_cash_required"] > m["coc_denominator"]   # reserves shown separately, on top
    assert m["rent_to_price"] == pytest.approx(3400 / 300000, abs=1e-4)
    assert m["grm"] == pytest.approx(300000 / 40800, abs=0.01)
    assert m["price_per_unit"] == 75000


def test_post_sale_tax_estimate_overrides_current_bill(cfg):
    d = deal(post_sale=6200)
    ex = uw.expense_lines(d, cfg, "conservative")
    assert ex["lines"]["property_taxes"]["amount"] == 6200


def test_stress_scenarios_move_in_the_right_direction(cfg):
    d = deal()
    s = uw.scenarios(d, cfg, 0.25, 0.075)
    assert set(s) == {"base", "downside", "severe", "upside"}
    assert s["upside"]["monthly_cash_flow"] > s["base"]["monthly_cash_flow"] > s["downside"]["monthly_cash_flow"] > s["severe"]["monthly_cash_flow"]
    # severe: one of four units vacant for 12 months => GSR x 0.75 before normal vacancy
    sev_ex = uw.expense_lines(d, cfg, "conservative", units_vacant_12mo=1)
    assert sev_ex["gsr"] == pytest.approx(850 * 4 * 12 * 0.75)
    dn = uw.expense_lines(d, cfg, "conservative", rent_mult=0.9, vacancy_pct=0.10, ins_mult=1.25, maint_mult=1.25, tax_mult=1.10)
    assert dn["lines"]["insurance"]["amount"] == pytest.approx(2500 * 1.25)
    assert dn["lines"]["property_taxes"]["amount"] == pytest.approx(4100 * 1.10)
    assert dn["gsr"] == pytest.approx(850 * 4 * 12 * 0.9)


def test_equity_structures_and_liquidity_bias(cfg):
    d = deal()
    es = uw.equity_structures(d, cfg)
    pcts = [s["down_payment_pct"] for s in es["structures"]]
    assert pcts == [0.25, 0.30, 0.35, 0.40, 0.50]
    cfs = [s["monthly_cash_flow"] for s in es["structures"]]
    assert cfs == sorted(cfs)                      # more equity => more cash flow
    assert es["max_cash_flow_structure"] == 0.50
    # positive leverage (econ cap > loan constant) => least equity maximizes CoC; negative leverage => most equity does
    base = es["structures"][0]
    expected = 0.25 if base["economic_cap_rate"] > es["marginal_equity_yield"] else 0.50
    assert es["max_coc_structure"] == expected
    assert es["recommended_structure"] in pcts
    # marginal dollars of equity earn exactly the loan constant
    a, b = es["structures"][0], es["structures"][1]
    assert (b["annual_cash_flow"] - a["annual_cash_flow"]) / (b["down_payment"] - a["down_payment"]) == pytest.approx(es["marginal_equity_yield"], rel=1e-3)


def test_price_cap_excludes_structures_over_200k(cfg):
    d = deal(price=400000)
    es = uw.equity_structures(d, cfg)
    assert [s["down_payment_pct"] for s in es["structures"]] == [0.25, 0.30, 0.35, 0.40, 0.50]
    d = deal(price=410000)
    es = uw.equity_structures(d, cfg)
    assert 0.50 not in [s["down_payment_pct"] for s in es["structures"]]  # 0.5*410000 > 200000


def test_negotiation_solver_hits_targets(cfg):
    d = deal(rent_unit=700)   # a mediocre deal so targets bind below ask
    neg = uw.negotiation(d, cfg, 0.25, 0.075)
    assert neg["underwriting_ceiling_price"] is not None and neg["underwriting_ceiling_price"] <= d.price
    p9 = neg["econ_cap_9"]
    if p9:
        m = uw._at_price(d, cfg, 0.25, 0.075, p9)
        assert m["economic_cap_rate"] == pytest.approx(0.09, abs=0.002)
    if neg["dscr_1_25"]:
        m = uw._at_price(d, cfg, 0.25, 0.075, neg["dscr_1_25"])
        assert m["economic_dscr"] == pytest.approx(1.25, abs=0.01)
    assert (neg["econ_cap_10"] or 0) <= (neg["econ_cap_9"] or 1e9)


def test_rate_sensitivity_monotonic(cfg):
    d = deal()
    rs = uw.rate_sensitivity(d, cfg, 0.25)
    assert [r["rate"] for r in rs] == [0.065, 0.07, 0.075, 0.08, 0.085]
    cfs = [r["monthly_cash_flow"] for r in rs]
    assert cfs == sorted(cfs, reverse=True)


def test_unknown_rent_yields_no_metrics(cfg):
    d = deal()
    d.rent_cases["conservative"] = {"low": None, "base": None, "high": None, "status": "UNKNOWN", "grade": "D", "note": "none"}
    assert uw.expense_lines(d, cfg, "conservative")["gsr"] is None
    assert uw.scenarios(d, cfg, 0.25, 0.075) == {}
    assert uw.equity_structures(d, cfg)["structures"] == []
