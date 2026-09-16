"""Conventional investment financing math. Never VA. Rates here are ASSUMPTIONS, not quotes."""
from __future__ import annotations

from typing import List


def monthly_payment(principal: float, annual_rate: float, years: int, interest_only_months: int = 0) -> float:
    if principal <= 0:
        return 0.0
    r = annual_rate / 12
    n = years * 12
    if interest_only_months:      # IO is disabled by default; supported for completeness
        return principal * r
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)


def loan_constant(annual_rate: float, years: int) -> float:
    """Annual debt service per $1 of loan — the yield earned by every marginal dollar of extra equity."""
    return monthly_payment(1.0, annual_rate, years) * 12


def feasible_down_payments(pcts: List[float], price: float, max_down: float) -> List[float]:
    return [p for p in pcts if p * price <= max_down + 1e-6]


def year1_principal_paydown(principal: float, annual_rate: float, years: int) -> float:
    pmt = monthly_payment(principal, annual_rate, years)
    bal = principal
    r = annual_rate / 12
    paid = 0.0
    for _ in range(12):
        interest = bal * r
        princ = pmt - interest
        bal -= princ
        paid += princ
    return paid
