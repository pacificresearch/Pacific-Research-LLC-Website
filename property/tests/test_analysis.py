import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import appreciation, rent_analysis, risk, scoring, tax_analysis  # noqa: E402
from src.config import load_config  # noqa: E402
from src.database import Cache  # noqa: E402
from src.market_screen import _pct_rank  # noqa: E402
from src.models import DataPoint, Listing, MarketProfile, PropertyRecord, RentComp  # noqa: E402
from src.rentcast import Budget, RentCast, normalize_listing  # noqa: E402


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_pct_rank_direction():
    r = _pct_rank({"a": 0.04, "b": 0.07, "c": 0.06}, higher_is_better=True)
    assert r["b"] == 1.0 and r["a"] == 0.0
    r = _pct_rank({"a": 3.0, "b": 7.0}, higher_is_better=False)
    assert r["a"] == 1.0 and r["b"] == 0.0


def test_tax_analysis_distinguishes_current_and_post_sale(cfg):
    rec = PropertyRecord(tax_assessments={"2025": {"value": 205000}}, property_taxes={"2025": {"total": 4100}})
    t = tax_analysis.analyze(rec, 289000, "AL", cfg)      # AL = HIGH risk (Class III -> II)
    assert t["current_tax_bill"].value == 4100
    assert t["effective_tax_rate_on_assessed"].value == pytest.approx(0.02, abs=1e-4)
    assert t["post_sale_tax_risk"] == "HIGH"
    assert t["post_sale_tax_estimate"].value == pytest.approx(4100 / 205000 * 289000, rel=0.01)
    t = tax_analysis.analyze(rec, 289000, "TN", cfg)      # LOW: no sale trigger, +5% cushion
    assert t["post_sale_tax_estimate"].value == pytest.approx(4100 * 1.05, rel=0.01)
    t = tax_analysis.analyze(rec, 289000, "ZZ", cfg)      # unknown state -> UNKNOWN risk, +25% cushion
    assert t["post_sale_tax_risk"] == "UNKNOWN"
    assert t["post_sale_tax_estimate"].value == pytest.approx(4100 * 1.25, rel=0.01)
    t = tax_analysis.analyze(None, 289000, "IN", cfg)
    assert not t["current_tax_bill"].known and not t["post_sale_tax_estimate"].known


def test_rent_analysis_uses_comps_never_avm_times_units_blindly(cfg):
    cache = Cache(cfg.cache_db)
    rc = RentCast(cache, cfg["run"]["cache_ttl_hours"], Budget(0))
    comps = [{"id": str(i), "address": f"{i} X St", "price": p, "bedrooms": 2, "square_footage": 850, "property_type": "Multi-Family", "distance_miles": 0.5, "days_old": 30, "source": "fixture"}
             for i, p in enumerate([800, 825, 850, 850, 875, 900, 925, 950])]
    l = normalize_listing({"id": "L", "formattedAddress": "1 Fixture St, Fort Wayne, IN", "city": "Fort Wayne", "state": "IN", "bedrooms": 8, "squareFootage": 3400, "price": 250000, "_fixture": True, "_fixture_comps": comps})
    out = rent_analysis.analyze(l, None, 4, rc, cfg)
    c = out["cases"]["conservative"]
    assert c.grade == "A" and c.n_comps == 8
    assert c.base == 862 and out["per_building"]["conservative"]["base"] == 862 * 4
    assert "ASSUMED similar layouts" in out["layout_note"]
    assert out["cases"]["contractual"].base is None
    # AVM path with unknown layout => grade D and widened range
    l2 = normalize_listing({"id": "L2", "formattedAddress": "2 Fixture St", "bedrooms": 7, "price": 250000, "_fixture": True})
    out2 = rent_analysis.analyze(l2, None, 4, rc, cfg, avm={"rent": 900, "rentRangeLow": 800, "rentRangeHigh": 1000})
    assert out2["cases"]["conservative"].grade == "D"
    assert out2["per_building"]["conservative"]["base"] < 900 * 4
    out3 = rent_analysis.analyze(l2, None, 4, rc, cfg)
    assert out3["per_building"]["conservative"]["base"] is None   # no comps, no AVM => UNKNOWN, never invented


def test_insurance_estimate_is_labelled_and_state_tiered(cfg):
    l_tx = Listing(id="a", formatted_address="x", state="TX", price=300000, square_footage=3000)
    l_in = Listing(id="b", formatted_address="y", state="IN", price=300000, square_footage=3000)
    tx, ind = risk.insurance_estimate(l_tx, 4, cfg), risk.insurance_estimate(l_in, 4, cfg)
    assert tx.status.value == "ESTIMATED" and tx.value > ind.value
    q = risk.insurance_estimate(l_in, 4, cfg, {"annual_premium": 3100, "source": "quote"})
    assert q.status.value == "VERIFIED" and q.value == 3100


def test_catalyst_score_penalizes_single_sector_and_credits_status():
    m = MarketProfile(cbsa="36220", name="Odessa, TX", state="TX")
    m.metrics["population_growth_4y"] = DataPoint.provider(0.03, "t")
    m.metrics["domestic_migration_per_1000"] = DataPoint.provider(5.0, "t")
    m.metrics["employment_level"] = DataPoint.provider(80000, "t")
    m.research["catalysts"] = [{"name": "Gas plant", "sector": "oil gas", "status": "under_construction", "jobs": 800, "investment_usd": 2e9}]
    a = appreciation.catalyst_score(m)
    m.research["catalysts"] = [{"name": "Gas plant", "sector": "oil gas", "status": "announced", "jobs": 800, "investment_usd": 2e9}]
    b = appreciation.catalyst_score(m)
    assert a["score"] > b["score"]            # under-construction earns more than announced
    assert a["penalty"] >= 0.10               # single energy sector
    assert a["energy_boom_watch"] is True


def test_confidence_deductions_are_auditable():
    pr = {"rent": {"per_building": {"contractual": {"base": None}, "conservative": {"base": 3000, "grade": "C"}}},
          "taxes": {"current_tax_bill": {"known": False}, "post_sale_tax_risk": "UNKNOWN", "post_sale_treatment": {"status": "UNKNOWN"}},
          "insurance": {"status": "ESTIMATED"}, "units_status": "UNKNOWN", "owner_pays_utilities": None, "listing_stale_days": 0, "fixture": False}
    c = scoring.confidence_score(pr)
    assert c["score"] == 100 - 10 - 12 - 10 - 15 - 10 - 15 - 8 - 10
    assert any("POST-SALE" in d["reason"] for d in c["deductions"])
