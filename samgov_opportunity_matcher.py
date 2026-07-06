#!/usr/bin/env python3
"""
SAM.gov API Capability Matcher & Screening Script
==================================================

Pulls active federal contract opportunities from the SAM.gov Opportunities API,
filters and evaluates them against the capabilities of Pacific Research Group LLC
(a Service-Disabled Veteran-Owned Small Business), and prints a Markdown
screening report to the console.

The report is organized into four tiers:
    1. Core-target opportunities  — deep capability match (primary NAICS).
    2. Actionable recommendations — top 3 core matches to pursue first.
    3. Low-barrier / "warm body" opportunities — staffing/administrative/support
       work under secondary NAICS that PRG can reasonably win without deep
       domain specialization (mainly needs eligible, qualified personnel).
    4. Subcontracting & teaming opportunities — awarded primes and large
       unrestricted solicitations where PRG's realistic path is teaming as a
       subcontractor rather than bidding as prime.

Usage:
    python3 samgov_opportunity_matcher.py

Optional command-line overrides:
    --days N        Look back N days for posted opportunities (default: 30)
    --limit N       Max opportunities to request per NAICS query (default: 100)
    --api-key KEY   Override the hardcoded API key (or set env SAM_API_KEY)

Notes:
    * The script is self-contained; only the standard library and `requests`
      are required (`pip install requests`).
    * SAM.gov requires date filters (postedFrom / postedTo) in MM/DD/YYYY
      format and caps ranges at one year. Results are paginated.
"""

import argparse
import datetime as dt
import os
import re
import sys
import textwrap
from collections import OrderedDict

try:
    import requests
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "ERROR: The 'requests' library is required. Install it with:\n"
        "    pip install requests\n"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# 1. INPUT DATA CONFIGURATION
# ---------------------------------------------------------------------------

# API access. Prefer the environment variable so the key is not committed to
# history, but fall back to the value provided for turnkey execution.
API_KEY = os.environ.get(
    "SAM_API_KEY", "SAM-a87c1f1f-af4a-4e49-b2cd-7e21b68022a2"
)

# SAM.gov Opportunities API (v2 is the current GA endpoint; v1 is deprecated).
API_URL = "https://api.sam.gov/opportunities/v2/search"

# Company profile ----------------------------------------------------------
COMPANY_NAME = "Pacific Research Group LLC"
COMPANY_WEBSITE = "https://pacificresearchllc.com/"
SOCIOECONOMIC_STATUS = "SDVOSB (Service-Disabled Veteran-Owned Small Business)"

# Core capabilities (used to build the keyword-matching corpus).
CORE_CAPABILITIES = [
    "Clinical trial operations, clinical research coordination, and site "
    "management (Phases II-IV).",
    "Decentralized and hybrid clinical trial models, eConsent, ePRO/eCOA, and "
    "telehealth workflows.",
    "Regulatory compliance (ICH GCP, 21 CFR, HIPAA, CITI GCP) and audit "
    "readiness.",
    "Data analytics, electronic data capture (EDC), REDCap, CTMS, OnCore, "
    "Medidata Rave management, and database optimization.",
    "Biomedical equipment management, diagnostics, maintenance, and technical "
    "operations (DoD/VA healthcare settings).",
    "Emergency and trauma medicine clinical workflows, training, and "
    "healthcare technology deployment.",
]

# Tier 1 — PRIMARY / CORE-TARGET NAICS codes (deep capability match).
TARGET_NAICS = OrderedDict(
    [
        ("541715", "R&D in the Physical, Engineering, and Life Sciences"),
        ("541611", "Administrative & General Management Consulting"),
        ("541990", "All Other Professional, Scientific & Technical Services"),
        ("811210", "Electronic & Precision Equipment Repair & Maintenance"),
    ]
)

# Tier 2 — LOW-BARRIER / "WARM BODY" NAICS codes.
# These are labor-, staffing-, and support-heavy service categories that PRG,
# as an eligible SDVOSB, can realistically win by fielding qualified personnel
# rather than by deep technical differentiation. They are adjacent to PRG's
# healthcare / veteran-services footprint but have a lower barrier to entry.
LOW_BARRIER_NAICS = OrderedDict(
    [
        ("561320", "Temporary Help Services (medical/admin staffing)"),
        ("561110", "Office Administrative Services"),
        ("561210", "Facilities Support Services"),
        ("561499", "All Other Business Support Services"),
        ("561410", "Document Preparation Services"),
        ("541618", "Other Management Consulting Services"),
        ("541519", "Other Computer Related Services (IT staff aug)"),
        ("611430", "Professional & Management Development Training"),
        ("621999", "All Other Misc. Ambulatory Health Care Services"),
        ("621399", "Offices of All Other Misc. Health Practitioners"),
        ("621512", "Diagnostic Imaging Centers (support staffing)"),
        ("561612", "Security Guards & Patrol Services"),
        ("561720", "Janitorial Services"),
        ("488190", "Other Support Activities for Air Transportation"),
        # Research / analysis / writing codes — rich in solo-doable knowledge work
        ("541720", "R&D in Social Sciences & Humanities"),
        ("541910", "Marketing Research & Public Opinion Polling"),
        ("611710", "Educational Support Services"),
    ]
)

# Every NAICS we actually query the API for (primary first, then low-barrier).
ALL_QUERY_NAICS = OrderedDict()
ALL_QUERY_NAICS.update(TARGET_NAICS)
ALL_QUERY_NAICS.update(LOW_BARRIER_NAICS)

# Keywords that signal a technical-competency match. Kept lowercase for
# case-insensitive substring matching against title + description.
CAPABILITY_KEYWORDS = [
    "clinical research", "clinical trial", "clinical trials", "clinical study",
    "clinical studies", "clinical operations", "clinical site", "site management",
    "clinical coordinator", "research coordination", "research operations",
    "decentralized trial", "hybrid trial", "econsent", "epro", "ecoa",
    "telehealth", "telemedicine", "good clinical practice", "gcp", "ich gcp",
    "21 cfr", "hipaa", "audit readiness", "regulatory compliance",
    "data analytics", "electronic data capture", "edc", "redcap", "ctms",
    "oncore", "medidata", "rave", "database", "data management",
    "biomedical equipment", "biomedical", "medical equipment",
    "diagnostic", "diagnostics", "equipment maintenance", "equipment repair",
    "precision equipment", "healthcare technology", "health technology",
    "emergency medicine", "trauma", "trauma medicine", "medical research",
    "research and development", "life sciences", "pharmaceutical",
    "protocol", "irb", "institutional review board", "patient recruitment",
    "healthcare", "health care", "medical", "laboratory", "lab equipment",
]

# Keywords that signal a "warm body" / low-barrier staffing or support need —
# work where fielding eligible, credentialed personnel is the main requirement.
LOW_BARRIER_KEYWORDS = [
    "staffing", "staff augmentation", "temporary staffing", "personnel",
    "administrative support", "admin support", "office support", "clerical",
    "data entry", "records management", "medical records", "scheduling",
    "front desk", "reception", "call center", "help desk",
    "facilities support", "custodial", "janitorial", "housekeeping",
    "grounds", "security guard", "security services", "logistics support",
    "warehouse", "supply", "courier", "transcription", "coding",
    "credentialing", "training support", "instructor", "program support",
    "technician", "phlebotom", "medical assistant", "nursing", "cna",
    "patient transport", "escort", "labor", "operations support",
]

# Keywords that indicate a subcontracting / teaming angle.
SUBCONTRACT_KEYWORDS = [
    "subcontract", "subcontracting plan", "subcontractor", "teaming",
    "small business subcontracting", "sub-award", "subaward", "joint venture",
]

# --- "Solo-friendly" detection ------------------------------------------------
# Knowledge/office work that one capable person (with an AI assistant) can
# deliver: research, analysis, writing, data, reviews, small advisory tasks.
SOLO_FRIENDLY_KEYWORDS = [
    "research", "study", "studies", "analysis", "analytical", "report",
    "white paper", "assessment", "evaluation", "survey", "market research",
    "literature review", "systematic review", "data analysis", "data entry",
    "data management", "transcription", "translation", "editing", "proofreading",
    "technical writing", "writing", "documentation", "curriculum",
    "training material", "instructional design", "consulting", "advisory",
    "subject matter expert", "sme", "abstract", "records review", "chart review",
    "medical coding", "coding", "audit support", "program support",
    "administrative support", "grant writing", "proposal support",
    "policy analysis", "feasibility", "needs assessment", "sbir", "sttr",
    "phase i", "spreadsheet", "database design", "analyst", "review of",
]

# Signals that a task needs a crew, physical presence, or a large team —
# these push an opportunity OUT of "solo-friendly".
SOLO_EXCLUDE_KEYWORDS = [
    "construction", "renovation", "janitorial", "custodial", "security guard",
    "guard services", "landscaping", "grounds maintenance", "hvac", "plumbing",
    "roofing", "food service", "warehouse", "fleet", "installation",
    "manufacture", "manufacturing", "onsite staffing", "full-time equivalents",
    "ftes", "24/7", "around the clock", "nationwide", "multiple locations",
    "guards", "custodians", "shift work", "call center", "help desk",
]

# Firm-Fixed-Price small-buy thresholds (FAR): micro-purchase and the
# Simplified Acquisition Threshold — smaller usually means solo-doable.
MICRO_PURCHASE = 10_000
SIMPLIFIED_ACQ_THRESHOLD = 250_000

_FTE_RE = re.compile(
    r"(\d{1,3})\s*(?:\+\s*)?(?:full[-\s]?time|fte'?s?|full time equivalents?)",
    re.IGNORECASE,
)

# Set-aside codes/labels that this company is eligible for. SAM.gov returns a
# `typeOfSetAside` code and a `typeOfSetAsideDescription`. We map the codes.
# See: https://open.gsa.gov/api/opportunities-api/  (set-aside code table)
SDVOSB_SETASIDE_CODES = {"SDVOSBC", "SDVOSBS"}          # SDVOSB set-aside / sole source
SMALL_BUSINESS_SETASIDE_CODES = {"SBA", "SBP"}          # Total Small Business
# Codes that are eligible but broader (8a, HUBZone, WOSB, etc.) -- treated as
# "restricted" but flagged separately because they may exclude us.
OTHER_SETASIDE_CODES = {
    "8A", "8AN", "HZC", "HZS", "WOSB", "WOSBSS", "EDWOSB", "EDWOSBSS",
    "VSA", "VSS",  # VOSB (not necessarily SDVOSB)
}

# Notice types that represent a completed award (a prime now exists to sub under).
AWARD_NOTICE_MARKERS = ("award",)


# ---------------------------------------------------------------------------
# 2. API QUERY CONSTRUCTION
# ---------------------------------------------------------------------------

def fetch_opportunities(api_key, naics_code, posted_from, posted_to, limit):
    """Query the SAM.gov Opportunities API for a single NAICS code.

    Returns a list of opportunity dicts (possibly empty). Network / API
    errors are caught and surfaced as an empty list plus a stderr warning so
    that one bad request does not abort the whole run.
    """
    params = {
        "api_key": api_key,
        "ncode": naics_code,          # filter by NAICS code
        "postedFrom": posted_from,    # MM/DD/YYYY (required)
        "postedTo": posted_to,        # MM/DD/YYYY (required)
        "limit": min(limit, 1000),    # API max page size is 1000
        "offset": 0,
        # Notice types: solicitation, presol, combined, sources sought, special,
        # and award notices ('a') so we can surface subcontracting/teaming targets.
        "ptype": "o,p,k,r,s,a",
    }

    collected = []
    try:
        while True:
            resp = requests.get(API_URL, params=params, timeout=30)
            if resp.status_code == 429:
                sys.stderr.write(
                    "WARNING: Rate limited by SAM.gov (HTTP 429). "
                    "Try again later or reduce --limit.\n"
                )
                break
            resp.raise_for_status()
            payload = resp.json()

            batch = payload.get("opportunitiesData") or []
            collected.extend(batch)

            total = payload.get("totalRecords", len(collected))
            params["offset"] += len(batch)
            if not batch or params["offset"] >= total or params["offset"] >= limit:
                break
    except requests.exceptions.HTTPError as exc:
        sys.stderr.write(
            f"WARNING: HTTP error querying NAICS {naics_code}: {exc}\n"
            f"         Response: {getattr(exc.response, 'text', '')[:300]}\n"
        )
    except requests.exceptions.RequestException as exc:
        sys.stderr.write(
            f"WARNING: Network error querying NAICS {naics_code}: {exc}\n"
        )
    except ValueError as exc:  # JSON decode error
        sys.stderr.write(
            f"WARNING: Could not decode JSON for NAICS {naics_code}: {exc}\n"
        )

    return collected


# ---------------------------------------------------------------------------
# 3. EVALUATION LOGIC
# ---------------------------------------------------------------------------

def naics_tier(code):
    """Classify a NAICS code into 'primary', 'low_barrier', or 'other'."""
    code = (code or "").strip()
    if code in TARGET_NAICS:
        return "primary"
    if code in LOW_BARRIER_NAICS:
        return "low_barrier"
    return "other"


def classify_setaside(opp):
    """Return (flag_label, eligible_bool, is_sdvosb_bool).

    flag_label   -> short human-readable set-aside label for the report.
    eligible     -> True if PRG (an SDVOSB small business) can bid.
    is_sdvosb    -> True if it is specifically an SDVOSB set-aside (best fit).
    """
    code = (opp.get("typeOfSetAside") or "").strip().upper()
    desc = (opp.get("typeOfSetAsideDescription") or "").strip()

    if code in SDVOSB_SETASIDE_CODES:
        return ("SDVOSB", True, True)
    if code in SMALL_BUSINESS_SETASIDE_CODES:
        return ("Total SB", True, False)
    if code in OTHER_SETASIDE_CODES:
        # Small-business program but not one PRG necessarily qualifies for.
        label = desc or code
        # VOSB set-asides are open to SDVOSBs; treat as eligible.
        if code in {"VSA", "VSS"}:
            return ("VOSB", True, False)
        return (label, False, False)
    if not code:
        return ("None", True, False)  # Unrestricted -> anyone (incl. SB) may bid
    # Unknown / other restricted set-aside.
    return (desc or code, False, False)


def _keyword_hits(haystack, keywords):
    """Return the list of keywords (in order) that appear in haystack."""
    matched = []
    for kw in keywords:
        if kw in haystack and kw not in matched:
            matched.append(kw)
    return matched


def _haystack(opp):
    """Lowercased title + description + codes for keyword matching."""
    parts = [
        opp.get("title", ""),
        opp.get("description", ""),
        opp.get("naicsCode", ""),
        opp.get("classificationCode", ""),
    ]
    return " ".join(str(p) for p in parts).lower()


def match_capabilities(opp):
    """Return (is_match, matched_keywords) for technical-competency scoring."""
    matched = _keyword_hits(_haystack(opp), CAPABILITY_KEYWORDS)
    return (len(matched) > 0, matched)


def match_low_barrier(opp):
    """Return (is_match, matched_keywords) for warm-body / staffing signals."""
    matched = _keyword_hits(_haystack(opp), LOW_BARRIER_KEYWORDS)
    return (len(matched) > 0, matched)


def classify_subcontracting(opp, setaside_label, tier, tech_match):
    """Decide whether an opportunity is a realistic subcontracting/teaming target.

    Returns (is_subcontracting, notice_type, angle_reason).

    The realistic sub/teaming paths for a small SDVOSB are:
      * Award Notices  -> a prime has been selected; approach them to sub.
      * Large UNRESTRICTED solicitations -> the prime must meet FAR 52.219-9
        small-business subcontracting goals, so an SDVOSB is an attractive sub.
      * Any notice whose text explicitly mentions subcontracting/teaming.
    We only flag notices with some NAICS relevance so the list stays focused.
    """
    notice_type = (opp.get("type") or opp.get("baseType") or "").strip()
    nt_lower = notice_type.lower()
    text = _haystack(opp)

    is_award = any(m in nt_lower for m in AWARD_NOTICE_MARKERS)
    sub_kw = _keyword_hits(text, SUBCONTRACT_KEYWORDS)
    mentions_sub = len(sub_kw) > 0
    unrestricted_prime = setaside_label == "None"
    relevant = tier in ("primary", "low_barrier") or tech_match

    is_sub = relevant and (is_award or mentions_sub or unrestricted_prime)

    if not is_sub:
        return (False, notice_type, "")

    angle_bits = []
    if is_award:
        awardee = _extract_awardee(opp)
        angle_bits.append(
            f"awarded prime{f' ({awardee})' if awardee else ''} — pursue as sub"
        )
    if mentions_sub:
        angle_bits.append(f"notice cites subcontracting/teaming ({sub_kw[0]})")
    if unrestricted_prime and not is_award:
        angle_bits.append(
            "unrestricted prime must meet SB subcontracting goals (FAR 52.219-9)"
        )
    return (True, notice_type or "N/A", "; ".join(angle_bits) + ".")


def evaluate(opp):
    """Evaluate a single opportunity and return a structured result dict."""
    setaside_label, setaside_eligible, is_sdvosb = classify_setaside(opp)
    tech_match, matched_kw = match_capabilities(opp)
    lb_match, lb_kw = match_low_barrier(opp)

    naics = (opp.get("naicsCode") or "").strip()
    tier = naics_tier(naics)
    naics_targeted = tier == "primary"

    is_sub, notice_type, sub_angle = classify_subcontracting(
        opp, setaside_label, tier, tech_match
    )

    # Prime eligibility for the CORE table = allowed to bid AND technically relevant.
    eligible = setaside_eligible and tech_match

    # Warm-body eligibility = allowed to bid; deep tech match NOT required.
    low_barrier_eligible = setaside_eligible

    reason = _build_reason(
        eligible, setaside_label, setaside_eligible, is_sdvosb,
        tech_match, matched_kw, naics, naics_targeted,
    )
    lb_reason = _build_low_barrier_reason(
        setaside_eligible, setaside_label, is_sdvosb, tier,
        lb_match, lb_kw, tech_match, matched_kw, naics,
    )

    # Score used for ranking recommendations (higher = better fit).
    score = 0
    if is_sdvosb:
        score += 5
    elif setaside_eligible and setaside_label != "None":
        score += 3
    elif setaside_eligible:
        score += 1
    if naics_targeted:
        score += 3
    score += min(len(matched_kw), 6)  # cap keyword contribution

    # Separate score for ranking low-barrier plays (staffing signal + eligibility).
    lb_score = 0
    if is_sdvosb:
        lb_score += 4
    elif setaside_eligible and setaside_label != "None":
        lb_score += 3
    elif setaside_eligible:
        lb_score += 1
    lb_score += min(len(lb_kw), 5)
    if tech_match:
        lb_score += 1  # bonus if it also brushes core capability

    value_display, value_num = _extract_value(opp)
    is_solo, solo_score, solo_reason = classify_solo(
        opp, setaside_eligible, value_num
    )

    return {
        "solicitation": (
            opp.get("solicitationNumber")
            or opp.get("noticeId")
            or "N/A"
        ),
        "title": _clean(opp.get("title", "Untitled")),
        "agency": _extract_agency(opp),
        "naics": naics or "N/A",
        "naics_tier": tier,
        "setaside": setaside_label,
        "value_display": value_display,
        "value_num": value_num,
        "eligible": eligible,
        "low_barrier_eligible": low_barrier_eligible,
        "reason": reason,
        "lb_reason": lb_reason,
        "matched_keywords": matched_kw,
        "lb_keywords": lb_kw,
        "is_sdvosb": is_sdvosb,
        "naics_targeted": naics_targeted,
        "tech_match": tech_match,
        "lb_match": lb_match,
        "is_subcontracting": is_sub,
        "notice_type": notice_type or "N/A",
        "sub_angle": sub_angle,
        "is_solo": is_solo,
        "solo_score": solo_score,
        "solo_reason": solo_reason,
        "score": score,
        "lb_score": lb_score,
        "link": opp.get("uiLink", ""),
        "response_deadline": opp.get("responseDeadLine", "N/A"),
        "raw_setaside_eligible": setaside_eligible,
    }


def _build_reason(eligible, setaside_label, setaside_eligible, is_sdvosb,
                  tech_match, matched_kw, naics, naics_targeted):
    """Compose a short reason / gap-analysis sentence for the core table."""
    if eligible:
        bits = []
        if is_sdvosb:
            bits.append("SDVOSB set-aside aligns with veteran status")
        elif setaside_label == "None":
            bits.append("unrestricted (SB may compete)")
        else:
            bits.append(f"{setaside_label} set-aside is open to PRG")
        if naics_targeted:
            bits.append(f"NAICS {naics} is a primary target")
        if matched_kw:
            top = ", ".join(matched_kw[:3])
            bits.append(f"matches capabilities ({top})")
        return "Core match: " + "; ".join(bits) + "."

    # Not eligible -> explain the gap.
    gaps = []
    if not setaside_eligible:
        gaps.append(
            f"set-aside '{setaside_label}' excludes PRG (not SDVOSB/SB-eligible)"
        )
    if not tech_match:
        gaps.append("description does not overlap core clinical/biomedical scope")
    if not gaps:
        gaps.append("outside core capabilities")
    return "Gap: " + "; ".join(gaps) + "."


def _build_low_barrier_reason(setaside_eligible, setaside_label, is_sdvosb, tier,
                              lb_match, lb_kw, tech_match, matched_kw, naics):
    """Compose the reason string for the low-barrier / warm-body table."""
    if not setaside_eligible:
        return (
            f"Gap: set-aside '{setaside_label}' excludes PRG — not open to bid."
        )
    bits = []
    if is_sdvosb:
        bits.append("SDVOSB set-aside")
    elif setaside_label == "None":
        bits.append("unrestricted — SB may compete")
    else:
        bits.append(f"{setaside_label} set-aside open to PRG")
    if tier == "low_barrier":
        bits.append(f"low-barrier NAICS {naics}")
    if lb_kw:
        bits.append(f"staffing/support signals ({', '.join(lb_kw[:3])})")
    elif not lb_match:
        bits.append("standard service scope — win with qualified personnel")
    if tech_match:
        bits.append(f"bonus capability overlap ({matched_kw[0]})")
    return "Warm-body play: " + "; ".join(bits) + "."


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _clean(text, max_len=70):
    """Collapse whitespace and truncate long strings for table cells."""
    text = " ".join(str(text).split())
    text = text.replace("|", "\\|")  # escape pipes so Markdown tables don't break
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text or "N/A"


def _extract_agency(opp):
    """Pull the best available agency / department name."""
    for key in ("fullParentPathName", "organizationName", "departmentName"):
        val = opp.get(key)
        if val:
            # fullParentPathName is a dotted hierarchy; take the top department.
            return _clean(str(val).split(".")[0], max_len=40)
    return "N/A"


def _extract_awardee(opp):
    """Return the awardee company name for an award notice, if present."""
    award = opp.get("award") or {}
    awardee = award.get("awardee") or {}
    name = awardee.get("name") if isinstance(awardee, dict) else None
    return _clean(name, max_len=30) if name else ""


# Dollar-amount parsing for the estimated-value column. Matches figures like
# "$1,200,000", "$1.2M", "$500K", "$3 million".
_DOLLAR_RE = re.compile(
    r"\$\s?([\d,]+(?:\.\d+)?)\s?(billion|million|thousand|bn|mil|b|m|k)?\b",
    re.IGNORECASE,
)
_DOLLAR_MULTIPLIER = {
    "billion": 1e9, "bn": 1e9, "b": 1e9,
    "million": 1e6, "mil": 1e6, "m": 1e6,
    "thousand": 1e3, "k": 1e3,
}


def _format_currency(amount):
    """Human-friendly currency formatting: $1.2M, $500K, $12,000."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "Not stated"
    if amount >= 1e9:
        return f"${amount / 1e9:.1f}B"
    if amount >= 1e6:
        return f"${amount / 1e6:.1f}M"
    if amount >= 1e3:
        return f"${amount / 1e3:.0f}K"
    return f"${amount:,.0f}"


def _parse_dollar_amounts(text):
    """Return a list of dollar figures (floats) found in free text."""
    amounts = []
    for num, unit in _DOLLAR_RE.findall(text or ""):
        try:
            value = float(num.replace(",", ""))
        except ValueError:
            continue
        value *= _DOLLAR_MULTIPLIER.get((unit or "").lower(), 1)
        if value >= 1000:  # ignore trivial figures / page refs
            amounts.append(value)
    return amounts


def _extract_value(opp):
    """Estimate the contract's dollar value (i.e. the revenue it would generate).

    Priority:
      1. Award amount, when the notice is an award (the real contract value).
      2. The largest dollar figure mentioned in the notice title/description.
      3. "Not stated" — SAM rarely publishes a value for open solicitations.

    Returns (display_string, numeric_value_or_None).
    """
    award = opp.get("award") or {}
    raw = award.get("amount") if isinstance(award, dict) else None
    if raw not in (None, "", 0, "0"):
        try:
            amt = float(str(raw).replace("$", "").replace(",", "").strip())
            if amt > 0:
                return (_format_currency(amt), amt)
        except ValueError:
            pass

    candidates = _parse_dollar_amounts(_haystack(opp))
    if candidates:
        amt = max(candidates)
        return (f"~{_format_currency(amt)} (from notice text)", amt)

    return ("Not stated", None)


def _estimate_fte(text):
    """Largest full-time-equivalent headcount mentioned in the text, or None."""
    counts = []
    for m in _FTE_RE.findall(text or ""):
        try:
            counts.append(int(m))
        except ValueError:
            continue
    return max(counts) if counts else None


def classify_solo(opp, setaside_eligible, value_num):
    """Assess whether one person (with an AI assistant) could realistically
    deliver this contract. Returns (is_solo, solo_score, reason).

    Heuristic — favors small-dollar knowledge work (research, analysis,
    writing, data, review) and penalizes crew/physical/large-team signals.
    """
    text = _haystack(opp)
    hits = _keyword_hits(text, SOLO_FRIENDLY_KEYWORDS)
    excludes = _keyword_hits(text, SOLO_EXCLUDE_KEYWORDS)
    fte = _estimate_fte(text)

    score = 0
    score += min(len(hits), 5)                 # knowledge-work signals
    score -= 2 * min(len(excludes), 4)         # crew / physical / big-team signals

    # Dollar size: smaller = more solo-doable.
    if value_num is None:
        score += 1                             # unstated (often small buys)
    elif value_num <= MICRO_PURCHASE:
        score += 3
    elif value_num <= SIMPLIFIED_ACQ_THRESHOLD:
        score += 2
    elif value_num > 1_000_000:
        score -= 3

    # Headcount: a solo shop can't field a big team.
    if fte is None:
        score += 1
    elif fte <= 1:
        score += 2
    elif fte <= 2:
        score += 1
    else:
        score -= 4

    is_solo = (
        setaside_eligible
        and score >= 3
        and len(hits) >= 1
        and (fte is None or fte <= 2)
        and (value_num is None or value_num <= SIMPLIFIED_ACQ_THRESHOLD * 2)
    )

    # Compose a short "why it's solo-doable" note.
    bits = []
    if hits:
        bits.append(f"knowledge work ({', '.join(hits[:3])})")
    if value_num is not None and value_num <= SIMPLIFIED_ACQ_THRESHOLD:
        bits.append(f"small dollar value ({_format_currency(value_num)})")
    elif value_num is None:
        bits.append("small/unstated value")
    if fte is not None and fte <= 2:
        bits.append(f"~{fte} person")
    if excludes:
        bits.append(f"⚠ check for crew work ({excludes[0]})")
    reason = "; ".join(bits) + "." if bits else "Light-scope knowledge task."
    return (is_solo, score, "One-person doable: " + reason)


def _date_range(days_back):
    """Return (postedFrom, postedTo) as MM/DD/YYYY strings."""
    today = dt.date.today()
    start = today - dt.timedelta(days=days_back)
    fmt = "%m/%d/%Y"
    return start.strftime(fmt), today.strftime(fmt)


# ---------------------------------------------------------------------------
# 4. OUTPUT GENERATION
# ---------------------------------------------------------------------------

def _opportunity_table(rows, eligible_key, reason_key):
    """Render a standard reviewed-opportunity Markdown table from result rows."""
    lines = [
        "| Solicitation # | Title | Agency | NAICS | Set-Aside | Est. Value "
        "| Eligible? (Yes/No) | Short Reason / Gap Analysis |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in rows:
        elig = "**YES**" if r[eligible_key] else "**NO**"
        lines.append(
            f"| {r['solicitation']} | {r['title']} | {r['agency']} "
            f"| {r['naics']} | {r['setaside']} | {r['value_display']} "
            f"| {elig} | {r[reason_key]} |"
        )
    return lines


def render_report(results):
    """Print the full Markdown screening report to stdout."""
    lines = []
    lines.append(f"## SAM.gov Contract Screening Report for {COMPANY_NAME}")
    lines.append("")
    lines.append(
        f"*Profile:* {SOCIOECONOMIC_STATUS} • "
        f"[{COMPANY_WEBSITE}]({COMPANY_WEBSITE}) • "
        f"Generated {dt.date.today().isoformat()}"
    )
    lines.append("")

    primary = [r for r in results if r["naics_tier"] == "primary"]
    low_barrier = [r for r in results if r["naics_tier"] == "low_barrier"]
    subcontract = [r for r in results if r["is_subcontracting"]]
    solo = sorted([r for r in results if r["is_solo"]],
                  key=lambda r: r["solo_score"], reverse=True)

    # --- Section 1: complete list (core-target NAICS) --------------------
    lines.append("### 1. Complete List of Reviewed Opportunities (Core-Target NAICS)")
    lines.append("")
    if not primary:
        lines.append(
            "_No opportunities were returned for the primary target NAICS codes "
            "in the selected date window. Widen the `--days` window or verify "
            "the API key, then re-run._"
        )
        lines.append("")
    else:
        lines.extend(_opportunity_table(primary, "eligible", "reason"))
        lines.append("")

    # --- Section 2: recommendations --------------------------------------
    lines.append("### 2. Actionable Recommendations")
    lines.append("")

    top3 = sorted(
        [r for r in primary if r["eligible"]],
        key=lambda r: r["score"],
        reverse=True,
    )[:3]

    if not top3:
        lines.append(
            "*   No eligible, on-target prime opportunities were identified in "
            "this run. Recommended actions:"
        )
        lines.append(
            "    *   Broaden the search window (`--days 60` or `--days 90`) to "
            "capture recently posted notices."
        )
        lines.append(
            "    *   Review the low-barrier and subcontracting lists below for "
            "near-term, winnable work."
        )
        lines.append(
            "    *   Confirm the SAM.gov API key is active and the entity's "
            "SDVOSB certification is current in SAM.gov and VetCert."
        )
    else:
        lines.append(
            f"Top {len(top3)} best-matching prime opportunit"
            f"{'y' if len(top3) == 1 else 'ies'} for {COMPANY_NAME}:"
        )
        lines.append("")
        for i, r in enumerate(top3, start=1):
            _render_recommendation(lines, i, r)
    lines.append("")

    # --- Section 3: low-barrier / warm-body ------------------------------
    lines.append('### 3. Low-Barrier / "Warm Body" Opportunities')
    lines.append("")
    lines.append(
        "_Adjacent staffing, administrative, and support work under secondary "
        "NAICS codes that PRG can reasonably win by fielding eligible, "
        "qualified personnel — lower barrier to entry, less domain "
        "specialization required._"
    )
    lines.append("")
    lb_eligible = sorted(
        [r for r in low_barrier if r["low_barrier_eligible"]],
        key=lambda r: r["lb_score"],
        reverse=True,
    )
    if not lb_eligible:
        lines.append(
            "_No eligible low-barrier opportunities were returned in this window. "
            "Widen `--days`, or register for Sources Sought under the secondary "
            "NAICS codes to shape upcoming staffing/support set-asides._"
        )
    else:
        lines.extend(
            _opportunity_table(lb_eligible, "low_barrier_eligible", "lb_reason")
        )
    lines.append("")

    # --- Section 4: subcontracting / teaming -----------------------------
    lines.append("### 4. Subcontracting & Teaming Opportunities")
    lines.append("")
    lines.append(
        "_Awarded primes and large unrestricted solicitations where PRG's "
        "realistic path is teaming as a subcontractor rather than bidding as "
        "prime. Unrestricted primes must meet FAR 52.219-9 small-business "
        "subcontracting goals, making an SDVOSB an attractive teammate._"
    )
    lines.append("")
    subs_sorted = sorted(subcontract, key=lambda r: r["score"], reverse=True)
    if not subs_sorted:
        lines.append(
            "_No subcontracting/teaming targets were identified in this window._"
        )
    else:
        lines.append(
            "| Solicitation # | Title | Agency | NAICS | Set-Aside | Est. Value "
            "| Notice Type | Subcontracting Angle |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in subs_sorted:
            lines.append(
                f"| {r['solicitation']} | {r['title']} | {r['agency']} "
                f"| {r['naics']} | {r['setaside']} | {r['value_display']} "
                f"| {r['notice_type']} | {r['sub_angle']} |"
            )
    lines.append("")

    # --- Section 5: solo-friendly (one-person) ---------------------------
    lines.append("### 5. Solo-Friendly Opportunities (You + an AI Assistant)")
    lines.append("")
    lines.append(
        "_Small-scale knowledge work — research, analysis, writing, data, and "
        "reviews — that one capable person could realistically deliver without "
        "a team. Ranked by fit; verify scope in the full notice before bidding._"
    )
    lines.append("")
    if not solo:
        lines.append(
            "_No clearly solo-doable opportunities surfaced in this window. "
            "Widen `--days`, or add research/analysis NAICS (e.g. 541720, "
            "541990, 611710) and re-run._"
        )
    else:
        lines.append(
            "| Solicitation # | Title | Agency | NAICS | Set-Aside | Est. Value "
            "| Why One-Person Doable |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in solo:
            lines.append(
                f"| {r['solicitation']} | {r['title']} | {r['agency']} "
                f"| {r['naics']} | {r['setaside']} | {r['value_display']} "
                f"| {r['solo_reason']} |"
            )
        if len(solo) < 10:
            lines.append("")
            lines.append(
                f"_Only {len(solo)} solo-friendly match"
                f"{'' if len(solo) == 1 else 'es'} this window — widen "
                f"`--days` to 120 or 180 to surface more._"
            )
    lines.append("")

    # --- Summary footer ---------------------------------------------------
    total = len(results)
    n_elig = sum(1 for r in primary if r["eligible"])
    n_sdvosb = sum(1 for r in results if r["is_sdvosb"])

    # Total stated value across everything PRG could pursue (prime-eligible core
    # + low-barrier plays), where a dollar figure was actually published.
    pursuable = {id(r): r for r in
                 [x for x in primary if x["eligible"]] + lb_eligible}.values()
    valued = [r["value_num"] for r in pursuable if r["value_num"]]
    pipeline_total = sum(valued)

    lines.append("---")
    lines.append(
        f"*Screened **{total}** opportunit"
        f"{'y' if total == 1 else 'ies'} across "
        f"{len(TARGET_NAICS)} core + {len(LOW_BARRIER_NAICS)} low-barrier NAICS "
        f"codes — **{n_elig}** core-eligible, "
        f"**{len(lb_eligible)}** low-barrier plays, "
        f"**{len(subs_sorted)}** subcontracting/teaming targets, "
        f"**{n_sdvosb}** SDVOSB set-asides.*"
    )
    if valued:
        lines.append("")
        lines.append(
            f"*Estimated pipeline value (where a dollar figure was published): "
            f"**{_format_currency(pipeline_total)}** across {len(valued)} "
            f"opportunit{'y' if len(valued) == 1 else 'ies'}. Most open "
            f"solicitations do not publish a value, so this is a floor, not a "
            f"total — treat all figures as rough estimates.*"
        )

    print("\n".join(lines))


def _render_recommendation(lines, i, r):
    """Append one formatted top-pick recommendation to `lines`."""
    naics_desc = TARGET_NAICS.get(r["naics"], "")
    kw = ", ".join(r["matched_keywords"][:5]) or "n/a"
    deadline = r.get("response_deadline", "N/A")
    lines.append(
        f"*   **#{i}. {r['title']}** (Solicitation `{r['solicitation']}`)"
    )
    lines.append(f"    *   **Agency:** {r['agency']}")
    lines.append(
        f"    *   **NAICS:** {r['naics']}"
        + (f" — {naics_desc}" if naics_desc else "")
    )
    lines.append(
        f"    *   **Set-Aside:** {r['setaside']}"
        + ("  ✅ SDVOSB direct fit" if r["is_sdvosb"] else "")
    )
    lines.append(f"    *   **Est. Contract Value (revenue):** {r['value_display']}")
    lines.append(f"    *   **Why it fits:** capability signals → {kw}.")
    lines.append(f"    *   **Response Deadline:** {deadline}")
    if r.get("link"):
        lines.append(f"    *   **Link:** {r['link']}")
    lines.append("")


# ---------------------------------------------------------------------------
# 5. SPREADSHEET EXPORT (Excel / CSV)
# ---------------------------------------------------------------------------

# Column layouts for each worksheet: (header, result-key-or-callable).
_CORE_COLS = [
    ("Solicitation #", "solicitation"),
    ("Title", "title"),
    ("Agency", "agency"),
    ("NAICS", "naics"),
    ("Set-Aside", "setaside"),
    ("Est. Value (Revenue)", "value_display"),
    ("Eligible?", lambda r: "YES" if r["eligible"] else "NO"),
    ("Reason / Gap Analysis", "reason"),
    ("Response Deadline", "response_deadline"),
    ("Link", "link"),
]
_LOWBAR_COLS = [
    ("Solicitation #", "solicitation"),
    ("Title", "title"),
    ("Agency", "agency"),
    ("NAICS", "naics"),
    ("Set-Aside", "setaside"),
    ("Est. Value (Revenue)", "value_display"),
    ("Eligible?", lambda r: "YES" if r["low_barrier_eligible"] else "NO"),
    ("Why It's Winnable", "lb_reason"),
    ("Response Deadline", "response_deadline"),
    ("Link", "link"),
]
_SUB_COLS = [
    ("Solicitation #", "solicitation"),
    ("Title", "title"),
    ("Agency", "agency"),
    ("NAICS", "naics"),
    ("Set-Aside", "setaside"),
    ("Est. Value (Revenue)", "value_display"),
    ("Notice Type", "notice_type"),
    ("Subcontracting Angle", "sub_angle"),
    ("Link", "link"),
]
_SOLO_COLS = [
    ("Solicitation #", "solicitation"),
    ("Title", "title"),
    ("Agency", "agency"),
    ("NAICS", "naics"),
    ("Set-Aside", "setaside"),
    ("Est. Value (Revenue)", "value_display"),
    ("Why One-Person Doable", "solo_reason"),
    ("Response Deadline", "response_deadline"),
    ("Link", "link"),
]


def _cell(row, spec):
    """Resolve a column spec (key or callable) against a result row."""
    value = spec(row) if callable(spec) else row.get(spec, "")
    # Un-escape the Markdown pipe-escaping for spreadsheet cells.
    return str(value).replace("\\|", "|")


def _split_sections(results):
    """Return the (core, low_barrier, subcontracting, solo) row groups."""
    primary = [r for r in results if r["naics_tier"] == "primary"]
    low_barrier = sorted(
        [r for r in results
         if r["naics_tier"] == "low_barrier" and r["low_barrier_eligible"]],
        key=lambda r: r["lb_score"], reverse=True,
    )
    subs = sorted(
        [r for r in results if r["is_subcontracting"]],
        key=lambda r: r["score"], reverse=True,
    )
    solo = sorted(
        [r for r in results if r["is_solo"]],
        key=lambda r: r["solo_score"], reverse=True,
    )
    return primary, low_barrier, subs, solo


def export_spreadsheet(results, path):
    """Write results to an Excel workbook (.xlsx) if openpyxl is available,
    otherwise fall back to a set of CSV files. Returns the path actually written.
    """
    primary, low_barrier, subs, solo = _split_sections(results)
    sheets = [
        ("Solo-Friendly (1-Person)", _SOLO_COLS, solo),
        ("Core Opportunities", _CORE_COLS, primary),
        ("Low-Barrier (Warm Body)", _LOWBAR_COLS, low_barrier),
        ("Subcontracting", _SUB_COLS, subs),
    ]

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        return _export_csv(sheets, path)

    wb = Workbook()
    wb.remove(wb.active)  # drop the default empty sheet

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E78")
    wrap = Alignment(vertical="top", wrap_text=True)

    for sheet_name, cols, rows in sheets:
        ws = wb.create_sheet(title=sheet_name[:31])  # Excel caps sheet names at 31
        ws.append([h for h, _ in cols])
        for c in range(1, len(cols) + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = wrap
        for r in rows:
            ws.append([_cell(r, spec) for _, spec in cols])
        # Column widths + wrapping.
        widths = {
            "Title": 45, "Agency": 28, "Reason / Gap Analysis": 60,
            "Why It's Winnable": 55, "Subcontracting Angle": 55, "Link": 35,
            "Est. Value (Revenue)": 22, "Why One-Person Doable": 60,
        }
        for idx, (h, _) in enumerate(cols, start=1):
            ws.column_dimensions[get_column_letter(idx)].width = widths.get(h, 16)
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = wrap
        ws.freeze_panes = "A2"
        if ws.max_row >= 1:
            ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"

    if not path.lower().endswith(".xlsx"):
        path = path + ".xlsx"
    wb.save(path)
    return path


def _export_csv(sheets, path):
    """Fallback: write one CSV per section next to `path`."""
    import csv
    base = path[:-5] if path.lower().endswith(".xlsx") else path
    base = base[:-4] if base.lower().endswith(".csv") else base
    written = []
    for sheet_name, cols, rows in sheets:
        slug = sheet_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        fname = f"{base}_{slug}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow([h for h, _ in cols])
            for r in rows:
                writer.writerow([_cell(r, spec) for _, spec in cols])
        written.append(fname)
    return ", ".join(written)


def _default_output_path():
    """Best-guess path for the output workbook: PRG_Contracts.xlsx on the
    user's Desktop (handles OneDrive-redirected Desktops), falling back to the
    home directory if no Desktop folder is found.
    """
    home = os.path.expanduser("~")
    profile = os.environ.get("USERPROFILE", home)
    candidates = [
        os.path.join(profile, "Desktop"),
        os.path.join(profile, "OneDrive", "Desktop"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "OneDrive", "Desktop"),
    ]
    for folder in candidates:
        if os.path.isdir(folder):
            return os.path.join(folder, "PRG_Contracts.xlsx")
    return os.path.join(home, "PRG_Contracts.xlsx")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="SAM.gov capability matcher for Pacific Research Group LLC.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              python3 samgov_opportunity_matcher.py
              python3 samgov_opportunity_matcher.py --days 60 --limit 200
            """
        ),
    )
    parser.add_argument("--days", type=int, default=30,
                        help="Look-back window in days (default: 30).")
    parser.add_argument("--limit", type=int, default=100,
                        help="Max opportunities per NAICS query (default: 100).")
    parser.add_argument("--api-key", default=None,
                        help="Override the SAM.gov API key.")
    parser.add_argument("--excel", default=None, metavar="FILE",
                        help="Path for the Excel workbook. By default it is "
                             "saved as PRG_Contracts.xlsx on your Desktop. "
                             "Falls back to CSV files if openpyxl is missing.")
    parser.add_argument("--no-excel", action="store_true",
                        help="Skip writing the spreadsheet (console output only).")
    parser.add_argument("--no-print", action="store_true",
                        help="Suppress the console Markdown report.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    api_key = args.api_key or API_KEY

    if not api_key or api_key.startswith("SAM-") is False:
        sys.stderr.write(
            "WARNING: API key looks malformed. Set --api-key or SAM_API_KEY.\n"
        )

    posted_from, posted_to = _date_range(args.days)
    sys.stderr.write(
        f"Querying SAM.gov for active opportunities "
        f"({posted_from} – {posted_to}) across "
        f"{len(TARGET_NAICS)} core + {len(LOW_BARRIER_NAICS)} low-barrier "
        f"NAICS codes...\n"
    )

    # Pull opportunities per NAICS (core + low-barrier) and de-dupe by notice id.
    seen = set()
    all_opps = []
    for naics in ALL_QUERY_NAICS:
        batch = fetch_opportunities(
            api_key, naics, posted_from, posted_to, args.limit
        )
        sys.stderr.write(f"  NAICS {naics}: {len(batch)} record(s)\n")
        for opp in batch:
            key = opp.get("noticeId") or opp.get("solicitationNumber") or id(opp)
            if key in seen:
                continue
            seen.add(key)
            all_opps.append(opp)

    # Evaluate every opportunity.
    results = [evaluate(opp) for opp in all_opps]

    # Sort: eligible first, then by score, then SDVOSB set-asides on top.
    results.sort(
        key=lambda r: (r["eligible"], r["score"], r["is_sdvosb"]),
        reverse=True,
    )

    if not args.no_print:
        render_report(results)

    # Always save a spreadsheet by default (to the Desktop) unless opted out.
    if not args.no_excel:
        out_path = args.excel or _default_output_path()
        written = export_spreadsheet(results, out_path)
        sys.stderr.write(
            "\n============================================================\n"
            f"  SPREADSHEET SAVED:\n  {written}\n"
            "============================================================\n"
        )

    # Keep the window open when run interactively (e.g. double-clicked on
    # Windows) so the output and saved-file path don't vanish instantly.
    try:
        if sys.stdout.isatty():
            input("\nDone. Press Enter to close this window...")
    except (EOFError, KeyboardInterrupt):
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
