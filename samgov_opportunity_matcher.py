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
from collections import Counter, OrderedDict

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

    # Richer decision fields.
    fte = _estimate_fte(_haystack(opp))
    personnel = str(fte) if fte else "Not stated"
    location_display, country_code, is_international = _extract_location(opp)
    location_type = "International" if is_international else "CONUS / US"
    staffing = _staffing_type(opp)
    incumbent = ("inherit" in staffing.lower()) or ("take over" in staffing.lower())
    timeframe = _timeframe_note(opp)
    fit = _fit_label(tier, tech_match, matched_kw)
    if setaside_eligible:
        llc_note = "Yes — LLC may bid" + (" (SDVOSB cert req'd)" if is_sdvosb else "")
    else:
        llc_note = "No — set-aside excludes PRG"
    win_score, win_band, win_emoji, win_note = _win_assessment(
        setaside_label, setaside_eligible, is_sdvosb, tier,
        tech_match, matched_kw, is_solo, fte, value_num, incumbent,
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
        "personnel": personnel,
        "fte_num": fte,
        "location": location_display,
        "location_type": location_type,
        "is_international": is_international,
        "staffing_type": staffing,
        "timeframe": timeframe,
        "fit": fit,
        "llc_eligible": llc_note,
        "win_score": win_score,
        "win_band": win_band,
        "win_emoji": win_emoji,
        "win_note": win_note,
        "poc": _extract_poc(opp),
        "psc": (opp.get("classificationCode") or "").strip(),
        "posted": (opp.get("postedDate") or "").split("T")[0],
        "deadline_days": _deadline_days(opp),
        "naics_desc": TARGET_NAICS.get(naics) or LOW_BARRIER_NAICS.get(naics) or "",
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


def _extract_poc(opp):
    """Return government points of contact as a list of {name,email,phone,type}."""
    out = []
    for p in (opp.get("pointOfContact") or []):
        if not isinstance(p, dict):
            continue
        out.append({
            "name": (p.get("fullName") or p.get("name") or "").strip(),
            "email": (p.get("email") or "").strip(),
            "phone": (p.get("phone") or "").strip(),
            "type": (p.get("type") or "").strip(),
        })
    return out


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


# --- Location, staffing, timeframe, fit, and win-likelihood --------------------

_DOMESTIC_COUNTRY = {"USA", "US", "UNITED STATES", "USA ", ""}

# Signals that an incumbent already performs the work (you'd take over / may
# inherit staff) vs. a brand-new requirement (you hire from scratch).
_INCUMBENT_SIGNALS = [
    "incumbent", "currently being performed", "current contractor",
    "predecessor", "transition-in", "transition in", "phase-in", "phase in",
    "seamless transition", "right of first refusal", "currently performed",
    "existing contract", "follow-on", "recompete",
]
_NEW_REQ_SIGNALS = [
    "new requirement", "new contract", "stand up", "stand-up", "no incumbent",
    "newly established", "first time",
]


def _extract_location(opp):
    """Return (display, country_code, is_international)."""
    pop = opp.get("placeOfPerformance") or {}
    if not isinstance(pop, dict):
        return ("Not stated", "", False)

    def _name(key):
        v = pop.get(key)
        if isinstance(v, dict):
            return v.get("name") or v.get("code") or ""
        return v or ""

    city = _name("city")
    state = pop.get("state") or {}
    state_code = state.get("code") or state.get("name") if isinstance(state, dict) else state
    country = pop.get("country") or {}
    country_code = ""
    country_name = ""
    if isinstance(country, dict):
        country_code = (country.get("code") or "").upper()
        country_name = country.get("name") or ""
    else:
        country_code = str(country).upper()

    is_intl = bool(country_code) and country_code not in _DOMESTIC_COUNTRY \
        and "UNITED STATES" not in country_name.upper()

    parts = [p for p in [city, state_code] if p]
    display = ", ".join(parts)
    if is_intl:
        display = (display + " · " if display else "") + (country_name or country_code)
    if not display:
        display = country_name or country_code or "Not stated"
    return (_clean(display, 34), country_code, is_intl)


def _staffing_type(opp):
    """Guess whether you'd hire new staff or take over existing personnel."""
    text = _haystack(opp)
    if _keyword_hits(text, _INCUMBENT_SIGNALS):
        return "Take over / may inherit incumbent staff"
    if _keyword_hits(text, _NEW_REQ_SIGNALS):
        return "New requirement — hire fresh"
    return "Unclear — verify in notice"


def _timeframe_note(opp):
    """Actionable timeframe: response deadline + any period-of-performance hint."""
    deadline = opp.get("responseDeadLine") or "Not stated"
    text = _haystack(opp)
    options = len(re.findall(r"option\s+(?:year|period)", text))
    has_base = "base period" in text or "base year" in text
    pop = ""
    if has_base and options:
        pop = f"1 base + {options} option yr(s)"
    elif options:
        pop = f"{options} option period(s) referenced"
    elif has_base:
        pop = "base period (see notice)"
    resp = str(deadline).split("T")[0] if deadline else "Not stated"
    return f"Respond by {resp}" + (f"; POP: {pop}" if pop else "")


def _deadline_days(opp):
    """Days from today until the response deadline, or None if unparseable."""
    raw = opp.get("responseDeadLine") or ""
    if not raw:
        return None
    try:
        d = dt.date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None
    return (d - dt.date.today()).days


def _fit_label(tier, tech_match, matched_kw):
    """Plain-English fit rating for PRG's capabilities."""
    if tier == "primary" and len(matched_kw) >= 3:
        return "Strong"
    if tech_match:
        return "Moderate"
    if tier == "low_barrier":
        return "Adjacent"
    return "Weak / off-target"


def _win_assessment(setaside_label, setaside_eligible, is_sdvosb, tier,
                    tech_match, matched_kw, is_solo, fte, value_num, incumbent):
    """Composite win-likelihood score (0-100) with a RAG band.

    Blends: can PRG even bid (set-aside), capability fit, how executable it is
    for a small/solo shop, value sanity, and incumbent headwind. Heuristic —
    a planning aid, not a guarantee.
    """
    # Hard gate: if PRG can't bid, it's Red regardless of everything else.
    if not setaside_eligible:
        return (12, "Red", "🔴", "Ineligible — set-aside excludes PRG")

    score = 0
    # 1. Set-aside advantage (less competition in PRG's lane) — up to 35
    if is_sdvosb:
        score += 35
    elif setaside_label == "VOSB":
        score += 28
    elif setaside_label == "Total SB":
        score += 22
    elif setaside_label == "None":
        score += 10          # unrestricted = open competition, harder
    else:
        score += 14

    # 2. Capability fit — up to 30
    score += min(len(matched_kw) * 5, 22)
    if tier == "primary":
        score += 8
    elif tier == "low_barrier":
        score += 4

    # 3. Executability for a small/solo shop — up to 25
    if is_solo:
        score += 25
    elif fte is None:
        score += 12
    elif fte <= 3:
        score += 16
    elif fte <= 10:
        score += 8
    else:
        score += 3          # big team is hard for a new small co

    # 4. Value sanity — up to 10
    if value_num is None:
        score += 5
    elif value_num <= SIMPLIFIED_ACQ_THRESHOLD:
        score += 10
    elif value_num <= 2_000_000:
        score += 6
    elif value_num > 10_000_000:
        score += 2

    # 5. Incumbent headwind
    if incumbent:
        score -= 12

    score = max(0, min(100, score))
    if score >= 80:
        band, emoji, note = "Green", "🟢", "Strong — pursue"
    elif score >= 60:
        band, emoji, note = "Yellow", "🟡", "Good — worth pursuing"
    elif score >= 40:
        band, emoji, note = "Orange", "🟠", "Stretch — needs partner/effort"
    else:
        band, emoji, note = "Red", "🔴", "Low odds — likely skip"
    return (score, band, emoji, note)


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
    """Render a standard reviewed-opportunity Markdown table from result rows.

    Rows are ordered by win score (best first) so the strongest bets sit on top.
    """
    lines = [
        "| Win | Rating | Solicitation # | Title | Agency | Set-Aside "
        "| Est. Value | Personnel | Solo? | Location | Short Reason |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in sorted(rows, key=lambda x: x["win_score"], reverse=True):
        solo = "Yes" if r["is_solo"] else "No"
        lines.append(
            f"| {r['win_score']} | {r['win_emoji']} {r['win_band']} "
            f"| {r['solicitation']} | {r['title']} | {r['agency']} "
            f"| {r['setaside']} | {r['value_display']} | {r['personnel']} "
            f"| {solo} | {r['location']} | {r[reason_key]} |"
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
            "| Win | Rating | Solicitation # | Title | Agency | Set-Aside "
            "| Est. Value | Timeframe | Location | Why One-Person Doable |"
        )
        lines.append(
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        )
        for r in sorted(solo, key=lambda x: x["win_score"], reverse=True):
            lines.append(
                f"| {r['win_score']} | {r['win_emoji']} {r['win_band']} "
                f"| {r['solicitation']} | {r['title']} | {r['agency']} "
                f"| {r['setaside']} | {r['value_display']} | {r['timeframe']} "
                f"| {r['location']} | {r['solo_reason']} |"
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
# Full decision-dashboard columns, ordered for go/no-go review.
_RICH_COLS = [
    ("Win Score", "win_score"),
    ("Rating", lambda r: f"{r['win_emoji']} {r['win_band']}"),
    ("Verdict", "win_note"),
    ("Title", "title"),
    ("Agency", "agency"),
    ("Fit for PRG", "fit"),
    ("Set-Aside", "setaside"),
    ("Eligible as LLC?", "llc_eligible"),
    ("Est. Value (Revenue)", "value_display"),
    ("Personnel (FTE)", "personnel"),
    ("Hire New or Take Over?", "staffing_type"),
    ("Solo-Doable?", lambda r: "Yes" if r["is_solo"] else "No"),
    ("Timeframe", "timeframe"),
    ("Location", "location"),
    ("Intl / CONUS", "location_type"),
    ("NAICS", "naics"),
    ("Solicitation #", "solicitation"),
    ("Link", "link"),
]
_CORE_COLS = _RICH_COLS
_LOWBAR_COLS = _RICH_COLS + [("Why It's Winnable", "lb_reason")]
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
_SOLO_COLS = _RICH_COLS + [("Why One-Person Doable", "solo_reason")]


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
    band_fill = {
        "Green": PatternFill("solid", fgColor="C6E7D0"),
        "Yellow": PatternFill("solid", fgColor="FBEBB0"),
        "Orange": PatternFill("solid", fgColor="F6D3A6"),
        "Red": PatternFill("solid", fgColor="F3C2BC"),
    }

    for sheet_name, cols, rows in sheets:
        ws = wb.create_sheet(title=sheet_name[:31])  # Excel caps sheet names at 31
        headers = [h for h, _ in cols]
        ws.append(headers)
        for c in range(1, len(cols) + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = wrap
        # Best bets first.
        rows = sorted(rows, key=lambda r: r.get("win_score", 0), reverse=True)
        rag_cols = [i for i, h in enumerate(headers, start=1)
                    if h in ("Win Score", "Rating")]
        for r in rows:
            ws.append([_cell(r, spec) for _, spec in cols])
            fill = band_fill.get(r.get("win_band"))
            if fill:
                for ci in rag_cols:
                    ws.cell(row=ws.max_row, column=ci).fill = fill
        # Column widths + wrapping.
        widths = {
            "Title": 45, "Agency": 26, "Reason / Gap Analysis": 60,
            "Why It's Winnable": 50, "Subcontracting Angle": 50, "Link": 32,
            "Est. Value (Revenue)": 20, "Why One-Person Doable": 55,
            "Win Score": 10, "Rating": 12, "Verdict": 26, "Fit for PRG": 14,
            "Set-Aside": 14, "Eligible as LLC?": 24, "Personnel (FTE)": 13,
            "Hire New or Take Over?": 34, "Solo-Doable?": 12, "Timeframe": 30,
            "Location": 26, "Intl / CONUS": 13, "Solicitation #": 20,
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
    try:
        wb.save(path)
    except PermissionError:
        # File is open in Excel (locked). Save under a timestamped name instead
        # so a long scan is never lost.
        alt = _timestamped_alt(path)
        wb.save(alt)
        sys.stderr.write(
            f"NOTE: '{os.path.basename(path)}' was open/locked — saved as "
            f"'{os.path.basename(alt)}' instead.\n"
        )
        return alt
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
    # Prefer the OneDrive Desktop first: when OneDrive "Known Folder" redirection
    # is on (very common on Windows), that is the desktop the user actually sees;
    # the plain %USERPROFILE%\Desktop still physically exists but is hidden.
    candidates = [
        os.path.join(profile, "OneDrive", "Desktop"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(profile, "Desktop"),
        os.path.join(home, "Desktop"),
    ]
    existing = [f for f in candidates if os.path.isdir(f)]
    if existing:
        # Among existing desktops, pick the one most recently modified — that is
        # the one the user is actively using.
        best = max(existing, key=lambda f: os.path.getmtime(f))
        return os.path.join(best, "PRG_Contracts.xlsx")
    return os.path.join(home, "PRG_Contracts.xlsx")


def _desktop_path(filename):
    """Return `filename` on the user's Desktop (or home dir fallback)."""
    base = _default_output_path()
    return os.path.join(os.path.dirname(base), filename)


def _timestamped_alt(path):
    """Insert a HH-MM-SS stamp before the extension, e.g. for locked files."""
    root, ext = os.path.splitext(path)
    stamp = dt.datetime.now().strftime("%H-%M-%S")
    return f"{root}_{stamp}{ext}"


# ---------------------------------------------------------------------------
# 6. EXECUTIVE HTML REPORT
# ---------------------------------------------------------------------------

def _html_escape(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _svg_hbars(items, value_fmt, default_color="#1E3A5F", width=680):
    """Horizontal bar chart as inline SVG. `items` = list of (label, value)
    or (label, value, color). Returns an SVG string."""
    items = [it for it in items if (it[1] or 0) > 0]
    if not items:
        return '<p class="empty">No published values to chart yet.</p>'
    maxv = max(it[1] for it in items) or 1
    row_h, pad, label_w = 34, 10, 200
    bar_max = width - label_w - 96
    height = pad * 2 + row_h * len(items)
    out = [f'<svg viewBox="0 0 {width} {height}" class="chart" '
           f'preserveAspectRatio="xMinYMin meet" role="img">']
    y = pad
    for it in items:
        label, val = it[0], it[1]
        color = it[2] if len(it) > 2 else default_color
        bw = max(2.0, (val / maxv) * bar_max)
        yc = y + row_h / 2
        out.append(f'<text x="0" y="{yc + 4:.0f}" class="c-lab">'
                   f'{_html_escape(_clean(label, 26))}</text>')
        out.append(f'<rect x="{label_w}" y="{y + 6:.0f}" width="{bw:.1f}" '
                   f'height="{row_h - 14}" rx="3" fill="{color}"/>')
        out.append(f'<text x="{label_w + bw + 8:.1f}" y="{yc + 4:.0f}" '
                   f'class="c-val">{_html_escape(value_fmt(val))}</text>')
        y += row_h
    out.append("</svg>")
    return "".join(out)


_RAG_HEX = {"Green": "#2E7D4F", "Yellow": "#D9A62A",
            "Orange": "#DB7A2B", "Red": "#C0392B"}


def _key_findings_html(ranked, eligible):
    """Build the 'Key Findings & Things to Keep in Mind' review callout."""
    if not eligible:
        return ('<section class="findings"><h2>Key Findings</h2>'
                '<p class="empty">No eligible opportunities this run — widen the '
                'search window and check again.</p></section>')

    closing = sorted(
        [r for r in eligible
         if r["deadline_days"] is not None and 0 <= r["deadline_days"] <= 14],
        key=lambda r: r["deadline_days"],
    )
    solos = [r for r in ranked if r["is_solo"]]
    valued = [r for r in eligible if r["value_num"]]
    top_value = max(valued, key=lambda r: r["value_num"]) if valued else None
    green_yellow = [r for r in ranked if r["win_band"] in ("Green", "Yellow")]

    items = []

    # Urgent deadlines first.
    if closing:
        names = "; ".join(
            f'{_html_escape(_clean(r["title"], 40))} '
            f'(<b>{r["deadline_days"]}d</b>, {_html_escape(r["solicitation"])})'
            for r in closing[:4])
        items.append(('🔴', 'Closing soon — act now',
                      f'{len(closing)} eligible opportunit'
                      f'{"y" if len(closing) == 1 else "ies"} close within 14 days: '
                      f'{names}.'))

    # Best bets.
    if green_yellow:
        names = "; ".join(
            f'{_html_escape(_clean(r["title"], 40))} '
            f'({r["win_emoji"]} {r["win_score"]})' for r in green_yellow[:3])
        items.append(('⭐', 'Strongest fits to pursue',
                      f'{names}.'))

    # Best solo play.
    if solos:
        r = solos[0]
        items.append(('🧑‍💻', 'Best solo (you + AI) play',
                      f'{_html_escape(_clean(r["title"], 50))} '
                      f'({_html_escape(r["solicitation"])}) — {r["win_emoji"]} '
                      f'{r["win_score"]}, {_html_escape(r["value_display"])}.'))

    # Biggest opportunity.
    if top_value:
        items.append(('💰', 'Largest published value',
                      f'{_html_escape(_clean(top_value["title"], 50))} — '
                      f'{_html_escape(top_value["value_display"])} '
                      f'({_html_escape(top_value["agency"])}).'))

    # Standing reminders.
    items.append(('✅', 'Keep in mind',
                  'Respond same-day where you can; keep SDVOSB certification '
                  'active through award; SDVOSB set-asides require ≥50% '
                  'self-performance (FAR 52.219-14); a Sources Sought response '
                  'is cheap and can shape the eventual solicitation.'))

    rows = "".join(
        f'<div class="find"><span class="find-i">{ic}</span>'
        f'<div><b>{_html_escape(t)}</b> — {body}</div></div>'
        for ic, t, body in items)
    return (f'<section class="findings"><h2>Key Findings &amp; Things to Keep '
            f'in Mind</h2>{rows}</section>')


def export_html_report(results, path, days):
    """Write a self-contained executive HTML report of the opportunity pipeline."""
    eligible = [r for r in results if r["raw_setaside_eligible"]]
    ranked = sorted(eligible, key=lambda r: r["win_score"], reverse=True)

    # --- KPIs ---
    total_value = sum(r["value_num"] for r in eligible if r["value_num"])
    n_active = len(eligible)
    n_solo = sum(1 for r in eligible if r["is_solo"])
    n_sdvosb = sum(1 for r in eligible if r["is_sdvosb"])
    n_green = sum(1 for r in eligible if r["win_band"] == "Green")
    agency_counts = Counter(r["agency"] for r in eligible if r["agency"] != "N/A")
    top_agency, top_agency_n = (agency_counts.most_common(1)[0]
                                if agency_counts else ("—", 0))

    # --- Chart data ---
    agency_value = Counter()
    for r in eligible:
        if r["value_num"]:
            agency_value[r["agency"]] += r["value_num"]
    chart_agency = [(a, v) for a, v in agency_value.most_common(8)]
    rag_counts = Counter(r["win_band"] for r in eligible)
    chart_rag = [(b, rag_counts.get(b, 0), _RAG_HEX[b])
                 for b in ("Green", "Yellow", "Orange", "Red")]

    kpis = [
        ("Total Pipeline Value", _format_currency(total_value) if total_value else "N/A",
         "sum of published values"),
        ("Eligible Opportunities", str(n_active), "PRG can bid"),
        ("Solo-Friendly", str(n_solo), "one-person doable"),
        ("SDVOSB Set-Asides", str(n_sdvosb), "your direct lane"),
        ("Top Agency", _clean(top_agency, 22), f"{top_agency_n} opportunities"),
    ]

    # --- Assemble HTML ---
    p = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         f'<title>PRG Pipeline Executive Report — {dt.date.today().isoformat()}</title>',
         "<style>", _REPORT_CSS, "</style></head><body>"]
    p.append('<div class="wrap">')

    # Header
    p.append('<header><p class="eyebrow">Executive Pipeline Report</p>'
             f'<h1>{COMPANY_NAME} — Federal Opportunity Pipeline</h1>'
             f'<p class="sub">{SOCIOECONOMIC_STATUS} · generated '
             f'{dt.date.today().isoformat()} · last {days} days · '
             f'{len(results)} notices screened</p></header>')

    # KPI cards
    p.append('<section class="kpis">')
    for label, val, sub in kpis:
        p.append(f'<div class="kpi"><div class="kpi-v">{_html_escape(val)}</div>'
                 f'<div class="kpi-l">{_html_escape(label)}</div>'
                 f'<div class="kpi-s">{_html_escape(sub)}</div></div>')
    p.append('</section>')

    # Key findings / review
    p.append(_key_findings_html(ranked, eligible))

    # Charts
    p.append('<section class="charts">')
    p.append('<div class="card"><h3>Pipeline Value by Agency</h3>'
             + _svg_hbars(chart_agency, _format_currency, "#1E3A5F") + '</div>')
    p.append('<div class="card"><h3>Opportunities by Win Rating</h3>'
             + _svg_hbars(chart_rag, lambda v: str(int(v))) + '</div>')
    p.append('</section>')

    # Contract matrix
    p.append('<section><h2>Contract / Opportunity Matrix</h2>'
             '<div class="scroll"><table><thead><tr>'
             '<th>Rating</th><th>Win</th><th>Solicitation #</th><th>Agency</th>'
             '<th>Est. Value</th><th>Set-Aside</th><th>NAICS / PSC</th>'
             '<th>Personnel</th><th>Solo</th><th>Location</th><th>Respond By</th>'
             '</tr></thead><tbody>')
    for r in ranked:
        chip = (f'<span class="chip" style="background:{_RAG_HEX[r["win_band"]]}">'
                f'{r["win_band"]}</span>')
        deadline = str(r["response_deadline"]).split("T")[0]
        dd = r["deadline_days"]
        if dd is not None and 0 <= dd <= 7:
            deadline = f'<b class="urgent">{deadline} · {dd}d 🔴</b>'
        elif dd is not None and 0 <= dd <= 14:
            deadline = f'{deadline} · {dd}d 🟠'
        naics_psc = r["naics"] + (f" / {r['psc']}" if r["psc"] else "")
        p.append("<tr>"
                 f"<td>{chip}</td><td class='num'>{r['win_score']}</td>"
                 f"<td>{_html_escape(r['solicitation'])}</td>"
                 f"<td>{_html_escape(r['agency'])}</td>"
                 f"<td class='num'>{_html_escape(r['value_display'])}</td>"
                 f"<td>{_html_escape(r['setaside'])}</td>"
                 f"<td>{_html_escape(naics_psc)}</td>"
                 f"<td>{_html_escape(r['personnel'])}</td>"
                 f"<td>{'Yes' if r['is_solo'] else '—'}</td>"
                 f"<td>{_html_escape(r['location'])}</td>"
                 f"<td>{deadline}</td></tr>")
    if not ranked:
        p.append('<tr><td colspan="11" class="empty">No eligible '
                 'opportunities in this window.</td></tr>')
    p.append('</tbody></table></div></section>')

    # Deep dive (top opportunities)
    p.append('<section><h2>Deep Dive — Top Opportunities</h2>')
    for r in ranked[:8]:
        p.append('<div class="dive">')
        p.append(f'<div class="dive-h"><span class="chip" '
                 f'style="background:{_RAG_HEX[r["win_band"]]}">{r["win_band"]} '
                 f'· {r["win_score"]}</span> <strong>{_html_escape(r["title"])}</strong>'
                 f' <span class="muted">({_html_escape(r["solicitation"])})</span></div>')
        scope = r["naics_desc"] or "professional services"
        p.append(f'<p><b>Scope:</b> {_html_escape(r["title"])} — '
                 f'{_html_escape(r["agency"])} ({_html_escape(scope)}).</p>')
        # Personnel roster
        if r["poc"]:
            roster = []
            for c in r["poc"][:3]:
                bits = [b for b in [c["name"], c["email"], c["phone"]] if b]
                if bits:
                    role = f'{c["type"]}: ' if c["type"] else ""
                    roster.append(role + " · ".join(_html_escape(b) for b in bits))
            if roster:
                p.append('<p><b>Gov. Contacts:</b> ' + " &nbsp;|&nbsp; ".join(roster)
                         + '</p>')
        else:
            p.append('<p><b>Gov. Contacts:</b> <span class="muted">not listed in '
                     'notice — check the SAM.gov posting.</span></p>')
        # Risk / action
        risks = [f"Respond by {str(r['response_deadline']).split('T')[0]}"]
        if r["is_sdvosb"]:
            risks.append("keep SDVOSB certification active through award")
        if r["fte_num"] and r["fte_num"] >= 1:
            risks.append("50% self-performance applies (FAR 52.219-14)")
        if "inherit" in r["staffing_type"].lower():
            risks.append("incumbent present — differentiate to unseat")
        p.append('<p><b>Risk / Action:</b> ' + "; ".join(_html_escape(x) for x in risks)
                 + '.</p>')
        p.append('</div>')
    if not ranked:
        p.append('<p class="empty">Nothing to deep-dive this run.</p>')
    p.append('</section>')

    # Pipeline insights
    p.append('<section><h2>Growth &amp; Pipeline Insights</h2><div class="card">')
    if agency_counts:
        foot = ", ".join(f"{_html_escape(a)} ({n})"
                         for a, n in agency_counts.most_common(3))
        p.append(f'<p><b>Strongest agency footprints:</b> {foot}.</p>')
        targets = [a for a, _ in agency_counts.most_common(3)]
        p.append('<p><b>Recommended target agencies for future bids:</b> '
                 + _html_escape(", ".join(targets)) + '. Concentrate capability '
                 'statements and Sources Sought responses here to build past '
                 'performance where PRG already sees demand.</p>')
        naics_counts = Counter(r["naics"] for r in eligible)
        strong_naics = ", ".join(f"{n} ({c})" for n, c in naics_counts.most_common(3))
        p.append(f'<p><b>Strongest NAICS demand:</b> {_html_escape(strong_naics)}.</p>')
    else:
        p.append('<p class="empty">Not enough eligible data yet — widen the '
                 'search window and re-run.</p>')
    p.append('</div></section>')

    p.append('<footer>Heuristic planning report generated from live SAM.gov '
             'data. Win scores and estimates are decision aids, not guarantees. '
             'Verify scope, value, and contacts in each official notice before '
             f'bidding. · {COMPANY_NAME} · {dt.date.today().isoformat()}</footer>')
    p.append('</div></body></html>')

    if not path.lower().endswith(".html"):
        path += ".html"
    html = "".join(p)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
    except PermissionError:
        alt = _timestamped_alt(path)
        with open(alt, "w", encoding="utf-8") as fh:
            fh.write(html)
        sys.stderr.write(
            f"NOTE: '{os.path.basename(path)}' was open/locked — saved as "
            f"'{os.path.basename(alt)}' instead.\n"
        )
        return alt
    return path


_REPORT_CSS = """
:root{--paper:#F4F6F9;--surface:#fff;--ink:#14263C;--muted:#5A6B7E;
--line:#DCE1E8;--primary:#1E3A5F;--accent:#9A6B1C;}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:36px 22px 70px}
header{border-bottom:3px solid var(--accent);padding-bottom:18px;margin-bottom:24px}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;
color:var(--accent);font-weight:700;margin:0 0 8px}
h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(24px,4vw,34px);
margin:0 0 8px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:13.5px;margin:0}
h2{font-family:Georgia,serif;font-size:21px;margin:34px 0 12px;
border-bottom:1px solid var(--line);padding-bottom:6px}
h3{font-size:14px;margin:0 0 10px;color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:26px}
@media(max-width:820px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--primary);
border-radius:10px;padding:14px 16px}
.kpi-v{font-family:Georgia,serif;font-size:24px;font-weight:700;color:var(--primary);
font-variant-numeric:tabular-nums;line-height:1.1}
.kpi-l{font-size:12px;font-weight:700;margin-top:4px}
.kpi-s{font-size:11px;color:var(--muted)}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:8px}
@media(max-width:820px){.charts{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.chart{width:100%;height:auto}
.c-lab{fill:var(--ink);font-size:12px}
.c-val{fill:var(--muted);font-size:12px;font-weight:700}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;min-width:820px;font-size:12.5px}
thead th{background:#EEF1F5;text-align:left;padding:9px 11px;font-size:10.5px;
letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--line);white-space:nowrap}
tbody td{padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:last-child td{border-bottom:none}
.num{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
.chip{display:inline-block;color:#fff;font-size:10.5px;font-weight:700;
padding:2px 8px;border-radius:20px;white-space:nowrap}
.dive{background:var(--surface);border:1px solid var(--line);border-radius:10px;
padding:14px 18px;margin-bottom:12px}
.dive-h{margin-bottom:6px;font-size:15px}
.dive p{margin:4px 0;font-size:13px}
.muted{color:var(--muted)}
.urgent{color:#C0392B}
.findings{background:#FBF6EC;border:1px solid var(--accent);border-radius:12px;
padding:8px 20px 16px;margin:8px 0 26px}
.findings h2{border:none;margin:14px 0 8px;font-size:19px}
.find{display:flex;gap:10px;padding:7px 0;border-top:1px solid #EADFC6;font-size:13px}
.find:first-of-type{border-top:none}
.find-i{font-size:16px;flex:none;width:22px;text-align:center}
.empty{color:var(--muted);font-style:italic;padding:14px}
footer{margin-top:34px;padding-top:16px;border-top:1px solid var(--line);
font-size:11.5px;color:var(--muted)}
@media print{body{background:#fff}.wrap{max-width:100%;padding:0}
.card,.dive,.kpi{break-inside:avoid}}
"""


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
    parser.add_argument("--report", default=None, metavar="FILE",
                        help="Path for the executive HTML report. By default it "
                             "is saved as PRG_Executive_Report.html on your Desktop.")
    parser.add_argument("--no-report", action="store_true",
                        help="Skip writing the executive HTML report.")
    parser.add_argument("--outdir", default=None, metavar="FOLDER",
                        help="Save date-stamped Excel + HTML into this folder "
                             "(creates it if needed). Used by the scheduled "
                             "weekly/monthly automation to keep a history.")
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

    # Resolve output paths. --outdir writes date-stamped files into a folder
    # (for the scheduled automation history); otherwise write to the Desktop.
    stamp = dt.date.today().isoformat()
    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
        xlsx_path = os.path.join(args.outdir, f"PRG_Contracts_{stamp}.xlsx")
        report_path = os.path.join(args.outdir, f"PRG_Executive_Report_{stamp}.html")
    else:
        xlsx_path = args.excel or _default_output_path()
        report_path = args.report or _desktop_path("PRG_Executive_Report.html")

    saved = []
    if not args.no_excel:
        try:
            saved.append(export_spreadsheet(results, xlsx_path))
        except Exception as exc:  # never let one save abort the other
            sys.stderr.write(f"WARNING: could not save spreadsheet: {exc}\n")
    if not args.no_report:
        try:
            saved.append(export_html_report(results, report_path, args.days))
        except Exception as exc:
            sys.stderr.write(f"WARNING: could not save HTML report: {exc}\n")

    if saved:
        sys.stderr.write(
            "\n============================================================\n"
            "  FILES SAVED:\n" + "".join(f"  {s}\n" for s in saved)
            + "  (Open the .html report in your browser; the .xlsx in Excel.)\n"
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
