#!/usr/bin/env python3
"""
SAM.gov API Capability Matcher & Screening Script
==================================================

Pulls active federal contract opportunities from the SAM.gov Opportunities API,
filters and evaluates them against the capabilities of Pacific Research Group LLC
(a Service-Disabled Veteran-Owned Small Business), and prints a Markdown
screening report to the console.

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

# Primary target NAICS codes -> human-readable description.
TARGET_NAICS = OrderedDict(
    [
        ("541715", "R&D in the Physical, Engineering, and Life Sciences"),
        ("541611", "Administrative & General Management Consulting"),
        ("541990", "All Other Professional, Scientific & Technical Services"),
        ("811210", "Electronic & Precision Equipment Repair & Maintenance"),
    ]
)

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
        "ptype": "o,p,k,r",           # solicitation, presol, combined, sources sought
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


def match_capabilities(opp):
    """Return (is_match, matched_keywords) for technical-competency scoring."""
    haystack_parts = [
        opp.get("title", ""),
        opp.get("description", ""),
        opp.get("naicsCode", ""),
        opp.get("classificationCode", ""),
    ]
    # `description` may be a URL to the full text; include whatever is present.
    haystack = " ".join(str(p) for p in haystack_parts).lower()

    matched = []
    for kw in CAPABILITY_KEYWORDS:
        if kw in haystack and kw not in matched:
            matched.append(kw)
    return (len(matched) > 0, matched)


def evaluate(opp):
    """Evaluate a single opportunity and return a structured result dict."""
    setaside_label, setaside_eligible, is_sdvosb = classify_setaside(opp)
    tech_match, matched_kw = match_capabilities(opp)

    naics = (opp.get("naicsCode") or "").strip()
    naics_targeted = naics in TARGET_NAICS

    # Eligibility = allowed to bid AND technically relevant.
    eligible = setaside_eligible and tech_match

    # Build a concise reason / gap-analysis string.
    reason = _build_reason(
        eligible, setaside_label, setaside_eligible, is_sdvosb,
        tech_match, matched_kw, naics, naics_targeted,
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

    return {
        "solicitation": (
            opp.get("solicitationNumber")
            or opp.get("noticeId")
            or "N/A"
        ),
        "title": _clean(opp.get("title", "Untitled")),
        "agency": _extract_agency(opp),
        "naics": naics or "N/A",
        "setaside": setaside_label,
        "eligible": eligible,
        "reason": reason,
        "matched_keywords": matched_kw,
        "is_sdvosb": is_sdvosb,
        "naics_targeted": naics_targeted,
        "tech_match": tech_match,
        "score": score,
        "link": opp.get("uiLink", ""),
        "response_deadline": opp.get("responseDeadLine", "N/A"),
        "raw_setaside_eligible": setaside_eligible,
    }


def _build_reason(eligible, setaside_label, setaside_eligible, is_sdvosb,
                  tech_match, matched_kw, naics, naics_targeted):
    """Compose a short reason / gap-analysis sentence for the report."""
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


def _date_range(days_back):
    """Return (postedFrom, postedTo) as MM/DD/YYYY strings."""
    today = dt.date.today()
    start = today - dt.timedelta(days=days_back)
    fmt = "%m/%d/%Y"
    return start.strftime(fmt), today.strftime(fmt)


# ---------------------------------------------------------------------------
# 4. OUTPUT GENERATION
# ---------------------------------------------------------------------------

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

    # --- Section 1: complete list ----------------------------------------
    lines.append("### 1. Complete List of Reviewed Opportunities")
    lines.append("")
    if not results:
        lines.append(
            "_No opportunities were returned for the target NAICS codes in the "
            "selected date window. Widen the `--days` window or verify the API "
            "key, then re-run._"
        )
        lines.append("")
    else:
        header = (
            "| Solicitation # | Title | Agency | NAICS | Set-Aside "
            "| Eligible? (Yes/No) | Short Reason / Gap Analysis |"
        )
        divider = "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        lines.append(header)
        lines.append(divider)
        for r in results:
            elig = "**YES**" if r["eligible"] else "**NO**"
            lines.append(
                f"| {r['solicitation']} | {r['title']} | {r['agency']} "
                f"| {r['naics']} | {r['setaside']} | {elig} | {r['reason']} |"
            )
        lines.append("")

    # --- Section 2: recommendations --------------------------------------
    lines.append("### 2. Actionable Recommendations")
    lines.append("")

    eligible_sorted = sorted(
        [r for r in results if r["eligible"]],
        key=lambda r: r["score"],
        reverse=True,
    )
    top3 = eligible_sorted[:3]

    if not top3:
        lines.append(
            "*   No eligible, on-target opportunities were identified in this "
            "run. Recommended actions:"
        )
        lines.append(
            "    *   Broaden the search window (`--days 60` or `--days 90`) to "
            "capture recently posted notices."
        )
        lines.append(
            "    *   Register for Sources Sought / RFI notices under the target "
            "NAICS to shape upcoming set-asides toward SDVOSB."
        )
        lines.append(
            "    *   Confirm the SAM.gov API key is active and the entity's "
            "SDVOSB certification is current in SAM.gov and VetCert."
        )
    else:
        lines.append(
            f"Top {len(top3)} best-matching opportunit"
            f"{'y' if len(top3) == 1 else 'ies'} for {COMPANY_NAME}:"
        )
        lines.append("")
        for i, r in enumerate(top3, start=1):
            naics_desc = TARGET_NAICS.get(r["naics"], "")
            kw = ", ".join(r["matched_keywords"][:5]) or "n/a"
            deadline = r.get("response_deadline", "N/A")
            lines.append(
                f"*   **#{i}. {r['title']}** "
                f"(Solicitation `{r['solicitation']}`)"
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
            lines.append(f"    *   **Why it fits:** capability signals → {kw}.")
            lines.append(f"    *   **Response Deadline:** {deadline}")
            if r.get("link"):
                lines.append(f"    *   **Link:** {r['link']}")
            lines.append("")

    # --- Summary footer ---------------------------------------------------
    total = len(results)
    n_elig = sum(1 for r in results if r["eligible"])
    n_sdvosb = sum(1 for r in results if r["is_sdvosb"])
    lines.append("---")
    lines.append(
        f"*Screened **{total}** opportunit"
        f"{'y' if total == 1 else 'ies'} across target NAICS "
        f"{', '.join(TARGET_NAICS)} — "
        f"**{n_elig}** eligible, **{n_sdvosb}** SDVOSB set-asides.*"
    )

    print("\n".join(lines))


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
        f"{len(TARGET_NAICS)} target NAICS codes...\n"
    )

    # Pull opportunities per NAICS and de-duplicate by notice id.
    seen = set()
    all_opps = []
    for naics in TARGET_NAICS:
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

    render_report(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
