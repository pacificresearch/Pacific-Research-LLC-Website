#!/usr/bin/env python3
"""
PRG SBIR/STTR opportunity pipeline (sbir-v1).

Companion to samgov_opportunity_matcher.py. Same house rules — cheapest
gate first, stop at the first fail, name the gate that fired — applied to
the small-business R&D lane instead of the contract lane.

What this is NOT: a parent-announcement finder. PA-27-100 (SBIR R43/R44)
and PA-27-102 (STTR R41/R42) are omnibus and always open; locating them is
not the task. The discovery targets are the things that carry a *signal*:
Notices of Special Interest, institute-specific PAs/PARs, RFAs with
dedicated set-aside money, and contract-based topics competed against a
stated need. See sbir/GATE.md.

Two rules run through every line of this file:

  1. Never invent an announcement number, a deadline, or a budget cap.
     Every one of those three is copied out of a primary source that this
     program fetched in this run, and the URL it came from is printed next
     to it in the digest. The IC budget caps in particular are parsed from
     the NOFO's own table, not from a constant in this file.

  2. When a source fails, the digest says so. A source that 403s is
     reported as a hole in the sweep, never silently dropped. Three of the
     six documented sources are expected to be unreachable without
     credentials; that is a finding, not an error to swallow.

Usage:
    python3 sbir_sttr_pipeline.py                     # full run, write digest
    python3 sbir_sttr_pipeline.py --dry-run           # print, do not persist
    python3 sbir_sttr_pipeline.py --all               # ignore the seen-list
    python3 sbir_sttr_pipeline.py --ic-table          # print verified IC caps
    python3 sbir_sttr_pipeline.py --explain PA-27-102 # gate trace for one FON

Andrew O'Donnell / Pacific Research Group LLC.
"""

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
from collections import Counter, OrderedDict

try:
    import requests
except ImportError:                                        # pragma: no cover
    sys.stderr.write("FATAL: pip install requests\n")
    raise SystemExit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
SBIR_DIR = os.path.join(HERE, "sbir")
STATE_DIR = os.path.join(SBIR_DIR, "state")
REPORT_DIR = os.path.join(SBIR_DIR, "reports")
SEEN_PATH = os.path.join(STATE_DIR, "seen.json")
CACHE_PATH = os.path.join(STATE_DIR, "nofo_cache.json")

TODAY = dt.date.today()
UA = ("PRG-SBIR-Pipeline/1.0 (Pacific Research Group LLC; UEI J585TLDV1CH1; "
      "SEEDinfo-compatible contact: andrew@pacificresearchgroup.com)")
TIMEOUT = 60
DIGEST_CAP = 10

# ---------------------------------------------------------------------------
# COMPANY + OPERATOR PROFILE — the thing every fit judgment is scored against
# ---------------------------------------------------------------------------

COMPANY = {
    "name": "Pacific Research Group LLC",
    "short": "PRG",
    "city": "Orange, CA",
    "uei": "J585TLDV1CH1",
    "cage": "1Z9B6",
    "naics": "541714",
    "certs": ["SDVOSB", "VOSB"],
    "formed": "2026-03",
    "headcount": 1,
    # The three facilities questions that kill an application on contact.
    "has_wet_lab": False,
    "has_animal_facility": False,
    "has_gmp": False,
    "has_clinical_site": False,
    "has_facility_clearance": False,
    "has_existing_ip": False,
}

OPERATOR = {
    "name": "Andrew O'Donnell",
    "role": "Managing Director",
    # Hard constraint, and the single most consequential fact in this file:
    # concurrently job searching for a full-time role, so the SBIR
    # primarily-employed rule (>= 51% employment at the SBC at time of award
    # and through the project) cannot be satisfied. STTR lets the PD/PI sit
    # at the partnering research institution. Default STTR. See Gate 2.
    "primarily_employable_at_sbc": False,
}

# Fit vocabulary. Tier A is "this asks for someone who has actually run
# trial operations at a site" — the thing almost no other applicant has.
# Tier B is real adjacent capability. Tier C is credible but thin.
# "Adjacent to healthcare" is not a fit and lives nowhere in this table.
FIT_TIER_A = {
    "clinical trial operation": 2.0, "trial operation": 2.0,
    "site-level": 1.6, "study coordinator": 2.0, "research coordinator": 2.0,
    "clinical research coordinator": 2.2, "protocol deviation": 2.2,
    "participant recruitment": 1.8, "participant retention": 1.8,
    "subject recruitment": 1.6, "trial recruitment": 1.8,
    "enrollment barrier": 1.8, "accrual": 1.6,
    "redcap": 2.2, "oncore": 2.4, "medidata": 2.2, "rave": 1.4,
    "electronic data capture": 2.0, "edc": 1.4,
    "econsent": 1.8, "electronic consent": 1.8, "informed consent process": 1.8,
    "decentralized trial": 2.2, "decentralized clinical trial": 2.4,
    "remote monitoring of trial": 2.0, "risk-based monitoring": 2.2,
    "source data verification": 2.4, "query resolution": 1.8,
    "data quality in clinical": 2.0, "clinical data management": 2.0,
    "good clinical practice": 2.0, "gcp": 1.4, "21 cfr part 11": 2.2,
    "regulatory binder": 2.4, "essential document": 1.6,
    "irb": 1.2, "institutional review board": 1.4,
    "clinical trial management system": 2.4, "ctms": 2.2,
    "protocol complexity": 2.0, "protocol feasibility": 2.2,
    "trial site": 1.8, "study startup": 2.2, "site activation": 2.4,
    "clinical operations": 1.8, "monitoring visit": 2.0,
    "adverse event reporting": 1.4, "case report form": 2.0,
}
FIT_TIER_B = {
    "biomedical equipment": 1.2, "medical device servicing": 1.2,
    "healthcare technology management": 1.4, "clinical engineering": 1.2,
    "device integration": 1.0, "interoperability": 0.9,
    "clinical workflow": 1.0, "electronic health record": 1.0, "ehr": 0.9,
    "digital health": 0.8, "health informatics": 1.0, "informatics": 0.7,
    "real-world evidence": 1.0, "real-world data": 1.0,
    "patient registry": 1.0, "registry": 0.6,
    "biostatistic": 0.8, "data harmoniz": 0.8, "data standard": 0.7,
    "cdisc": 1.2, "fhir": 0.9, "omop": 0.9,
    "workflow automation": 0.7, "quality improvement": 0.8,
    "human factors": 0.7, "usability": 0.6,
    "telehealth": 0.8, "remote patient monitoring": 0.9,
    "wearable": 0.6, "digital endpoint": 1.0,
    "medical equipment maintenance": 1.2, "equipment lifecycle": 1.0,
}
FIT_TIER_C = {
    "implementation science": 0.5, "dissemination": 0.4,
    "health disparities": 0.5, "underrepresented": 0.5,
    "community engagement": 0.4, "rural health": 0.4,
    "workforce training": 0.5, "training curriculum": 0.4,
    "global health": 0.4, "low- and middle-income": 0.4,
    "spanish": 0.3, "portuguese": 0.5, "multilingual": 0.4,
    "veteran": 0.4, "military health": 0.5,
    "emergency medical": 0.5, "prehospital": 0.5, "point-of-care testing": 0.5,
}
# Eligibility niches that RESTRICT THE FIELD in PRG's favour. This is not
# capability and does not pretend to be — it is the cheapest real edge a
# first-time applicant can get, and it is invisible to topic vocabulary. An
# announcement that carries one is never killed on fit alone; it is surfaced
# as MONITOR-PREPOSITION with the niche named, the way the domestic gate
# treats a set-aside.
ELIGIBILITY_NICHE = {
    "never been an independent pd/pi": ("PD/PI must never have led an NIH "
                                        "research grant — Andrew qualifies, "
                                        "and it removes every established "
                                        "small-business PI from the field"),
    "never been a pd/pi": ("PD/PI must never have led an NIH research grant "
                           "— Andrew qualifies"),
    "new entrepreneur": ("explicitly aimed at first-time small-business "
                         "entrepreneurs, which is exactly PRG's position"),
    "transition grant": ("transition-to-entrepreneurship mechanism; the field "
                         "is first-timers, not incumbents"),
    "have not previously received": ("excludes prior awardees, thinning the "
                                     "repeat-winner field this gate exists to "
                                     "detect"),
    "first-time applicant": ("field restricted to first-time applicants"),
    "new investigator": ("new-investigator status is an evaluation factor"),
    "early-stage investigator": ("early-stage investigator status is an "
                                 "evaluation factor"),
}

# Signals that the work is bench/discovery science PRG cannot do. These do
# not kill on their own (Gate 1 handles the hard facility kills); they pull
# the fit score down so "adjacent to healthcare" cannot float to a 3.
FIT_NEGATIVE = {
    "small molecule": -1.4, "drug candidate": -1.4, "lead optimization": -1.4,
    "medicinal chemistry": -1.6, "compound librar": -1.4,
    "gene therapy": -1.4, "gene editing": -1.4, "crispr": -1.4,
    "nanoparticle": -1.4, "biomaterial": -1.0, "tissue engineering": -1.2,
    "monoclonal antibod": -1.4, "vaccine candidate": -1.2,
    "assay development": -1.0, "biomarker discovery": -1.0,
    "protein engineering": -1.4, "cell line": -1.2, "organoid": -1.4,
    "microfluidic": -1.0, "fabricat": -0.8, "prototype device": -0.6,
    "synthesi": -0.8, "in vitro": -0.9, "preclinical model": -1.2,
    "pharmacokinetic": -1.0, "formulation": -1.0,
}

# --- Gate 1 kill vocabulary: capability PRG cannot buy its way into inside a
# Phase I period of performance. Wet-bench, animals, GMP, cleared facilities,
# and owning a clinical site are all hard stops for a 1-person shop with no
# lab. An STTR partner can hold a lab, so these fire only when the SMALL
# BUSINESS is the one that must hold it (see _gate1_eligibility).
KILL_WET_LAB = (
    "wet lab", "wet-bench", "bench science", "laboratory bench",
    "cell culture", "tissue culture", "in vitro assay", "western blot",
    "mass spectrometry", "flow cytometry", "pcr assay", "sequencing library",
    "histolog", "immunohistochem", "biosafety level", "bsl-2", "bsl-3",
    "select agent", "chemical synthesis", "organic synthesis",
)
KILL_ANIMAL = (
    "animal model", "animal stud", "vertebrate animal", "murine", "mouse model",
    "rodent", "non-human primate", "nonhuman primate", "in vivo efficacy",
    "vivarium", "iacuc", "glp toxicolog", "animal facilit",
)
KILL_GMP = (
    "cgmp", "gmp manufactur", "good manufacturing practice", "clean room",
    "cleanroom", "fill-finish", "lot release", "scale-up manufactur",
    "ind-enabling", "ide submission", "pilot production line",
)
KILL_CLEARANCE = (
    "facility clearance", "facility security clearance", "cleared facility",
    "top secret", "ts/sci", "secret-level facility", "classified space",
    "dd254",
)
KILL_OWN_SITE = (
    "applicant must operate a clinical site", "must own a clinical site",
    "applicant-operated clinic", "own patient population",
    "must have an existing patient cohort", "cliaertified laboratory",
    "clia-certified laboratory", "clia certified laboratory",
)
# Announcements that only a company already inside the program can enter.
# PRG has no prior Phase I or Phase II, so these are eligibility kills, not
# fit judgments.
PRIOR_AWARD_GATED = (
    "phase iib", "phase ii b", "commercialization readiness",
    "crp) program", "phase ii bridge", "sb1", "phase iia",
)
KILL_INELIGIBLE = (
    "8(a) set-aside", "hubzone set-aside", "wosb set-aside", "edwosb",
    "women-owned small business set-aside", "phase i awardee only",
    "prior phase i required", "must hold a phase i award",
    "gsa schedule holder", "idiq holders only",
)

# --- Gate 4 partner map: topic domain -> the academic home that would
# plausibly host the PD/PI, plus whether Stanford Dept of Medicine is a
# credible home for it. PRG's real asset is relationships at Stanford
# Department of Medicine; anything that needs an engineering fab, a vet
# school, or a chem department is a partner type with no path.
PARTNER_MAP = OrderedDict([
    ("clinical trial operations", {
        "match": ("trial operation", "site activation", "study startup",
                  "recruitment", "retention", "accrual", "protocol deviation",
                  "monitoring", "source data verification", "ctms",
                  "clinical research coordinator", "decentralized"),
        "dept": ("Stanford Department of Medicine — Quantitative Sciences Unit "
                 "/ Spectrum Clinical & Translational Research Unit (CTSA)"),
        "stanford_credible": True,
        "why": ("This is the department Andrew worked in; the CTSA hub is "
                "chartered to host exactly this kind of trial-operations "
                "methods work and routinely signs STTR partner letters."),
    }),
    ("clinical data / informatics", {
        "match": ("data capture", "redcap", "data quality", "data management",
                  "informatics", "fhir", "omop", "cdisc", "interoperability",
                  "real-world data", "registry", "electronic health record"),
        "dept": ("Stanford Department of Medicine — Center for Biomedical "
                 "Informatics Research (BMIR) / Division of Biomedical "
                 "Informatics"),
        "stanford_credible": True,
        "why": ("Sits inside the Department of Medicine, so the existing "
                "relationship carries; BMIR has prior STTR subaward history."),
    }),
    ("health services / implementation", {
        "match": ("implementation science", "dissemination", "health service",
                  "care delivery", "quality improvement", "disparities",
                  "access to care", "workflow"),
        "dept": ("Stanford Department of Medicine — Division of Primary Care "
                 "and Population Health / Stanford Center for Population "
                 "Health Sciences"),
        "stanford_credible": True,
        "why": ("Department of Medicine division; population-health STTR "
                "partnering is routine and needs no lab."),
    }),
    ("device / clinical engineering", {
        "match": ("biomedical equipment", "medical device", "clinical "
                  "engineering", "healthcare technology management",
                  "equipment maintenance", "device integration",
                  "human factors", "usability"),
        "dept": ("Stanford Department of Bioengineering / Byers Center for "
                 "Biodesign (NOT Department of Medicine)"),
        "stanford_credible": False,
        "why": ("Outside the department where PRG has relationships; a "
                "Biodesign or Bioengineering partnership would have to be "
                "built cold, which is a real but unfunded 60-90 day task."),
    }),
    ("bench / discovery", {
        "match": ("small molecule", "gene", "protein", "assay", "biomarker",
                  "nanoparticle", "cell line", "organoid", "vaccine",
                  "antibody", "compound"),
        "dept": None,
        "stanford_credible": False,
        "why": ("Requires a wet-lab PI whose science PRG cannot evaluate, "
                "manage, or contribute 40% of the effort to. No path."),
    }),
])

# 2026 reauthorization expanded foreign-affiliation review. Flag, never kill —
# PRG is clean on all of it, but the disclosure burden changes the workplan.
FOREIGN_FLAGS = (
    "foreign risk", "malign foreign", "foreign influence", "due diligence "
    "program", "covered individual", "foreign country of concern",
    "foreign talent", "foreign ownership", "foreign affiliation",
    "foreign component", "foreign subaward", "foreign subcontract",
    "non-domestic", "foreign entity",
)

# NIH IC abbreviation <-> full name. Used to join the NOFO budget table
# (full names) to RePORTER (abbreviations). Names are copied from the
# NOFO's own participating-components list, never typed from memory.
IC_ABBREV = OrderedDict([
    ("National Cancer Institute", "NCI"),
    ("National Eye Institute", "NEI"),
    ("National Heart, Lung, and Blood Institute", "NHLBI"),
    ("National Human Genome Research Institute", "NHGRI"),
    ("National Institute on Aging", "NIA"),
    ("National Institute on Alcohol Abuse and Alcoholism", "NIAAA"),
    ("National Institute of Allergy and Infectious Diseases", "NIAID"),
    ("National Institute of Arthritis and Musculoskeletal and Skin Diseases",
     "NIAMS"),
    ("National Institute of Biomedical Imaging and Bioengineering", "NIBIB"),
    ("Eunice Kennedy Shriver National Institute of Child Health and Human "
     "Development", "NICHD"),
    ("National Institute on Deafness and Other Communication Disorders",
     "NIDCD"),
    ("National Institute of Dental and Craniofacial Research", "NIDCR"),
    ("National Institute of Diabetes and Digestive and Kidney Diseases",
     "NIDDK"),
    ("National Institute on Drug Abuse", "NIDA"),
    ("National Institute of Environmental Health Sciences", "NIEHS"),
    ("National Institute of General Medical Sciences", "NIGMS"),
    ("National Institute of Mental Health", "NIMH"),
    ("National Institute of Neurological Disorders and Stroke", "NINDS"),
    ("National Institute of Nursing Research", "NINR"),
    ("National Institute on Minority Health and Health Disparities", "NIMHD"),
    ("National Library of Medicine", "NLM"),
    ("National Center for Complementary and Integrative Health", "NCCIH"),
    ("National Center for Advancing Translational Sciences", "NCATS"),
    ("Division of Program Coordination, Planning and Strategic Initiatives, "
     "Office of Research Infrastructure Programs", "ORIP"),
    ("Office of Research on Women's Health", "ORWH"),
])

# Eight of the 25 participating components publish no dollar figure at all —
# their cap row reads "SBA Guideline". That is a real number, it just lives
# somewhere else, and leaving it unresolved makes a third of the table
# unusable for budgeting.
#
# The pipeline tries to read it live each run. sbir.gov blocks this network
# (see sbir/SOURCES.md), so the fallback is a DATED, CITED figure that the
# digest labels as needing re-verification rather than presenting as fresh.
# Two independent NIH/SBA sources were checked on the verification date.
SBA_GUIDELINE = {
    "phase1": "$323,090",
    "phase2": "$2,153,927",
    "verified_on": "2026-08-25",
    "sources": ("https://www.sbir.gov/about",
                "https://seed.nih.gov/small-business-funding/"
                "small-business-program-basics/understanding-sbir-sttr"),
}
SBA_URL = "https://www.sbir.gov/about"


def sba_guideline():
    """Try live, fall back to the dated constant. Returns (p1, p2, note)."""
    try:
        txt = _text(_http("GET", SBA_URL).text)
        m1 = re.search(r"Phase\s*I\b[^$]{0,120}(\$\s?[\d,]{6,})", txt, re.I)
        m2 = re.search(r"Phase\s*II\b[^$]{0,120}(\$\s?[\d,]{6,})", txt, re.I)
        if m1 and m2:
            p1 = m1.group(1).replace(" ", "")
            p2 = m2.group(1).replace(" ", "")
            LOG.ok("SBA budgetary guideline", 1, SBA_URL,
                   "read live: %s Phase I / %s Phase II" % (p1, p2))
            return p1, p2, "read live from %s this run" % SBA_URL
    except (requests.RequestException, ValueError) as exc:
        LOG.record("SBA budgetary guideline", "STALE",
                   "could not read live (%s) — falling back to the figure "
                   "verified %s against %s. The guideline is adjusted for "
                   "inflation periodically; RE-VERIFY before budgeting."
                   % (_detail(exc), SBA_GUIDELINE["verified_on"],
                      " and ".join(SBA_GUIDELINE["sources"])), SBA_URL)
    return (SBA_GUIDELINE["phase1"], SBA_GUIDELINE["phase2"],
            "NOT read live this run; verified %s against %s — re-verify "
            "before budgeting" % (SBA_GUIDELINE["verified_on"],
                                  SBA_GUIDELINE["sources"][0]))


def expand_cap(cap, p1, p2, which):
    """Turn the literal string 'SBA Guideline' into the figure it stands for,
    while keeping the announcement's own wording visible."""
    if "sba guideline" in (cap or "").lower():
        return "SBA guideline (%s)" % (p1 if which == 1 else p2)
    return cap


STTR_CODES = ("R41", "R42")
SBIR_CODES = ("R43", "R44")

# ---------------------------------------------------------------------------
# SOURCE REGISTRY — every source reports OK / EMPTY / FAILED / NO-CREDENTIAL,
# and every one of those states is printed in the digest. A source that 403s
# is a hole in the sweep and gets named as one.
# ---------------------------------------------------------------------------

GRANTS_SEARCH = "https://api.grants.gov/v1/api/search2"
GRANTS_FETCH = "https://api.grants.gov/v1/api/fetchOpportunity"
GRANTS_ATT = "https://grants.gov/grantsws/rest/opportunity/att/download/{}"
GRANTS_DETAIL = "https://grants.gov/search-results-detail/{}"
NIH_GUIDE_API = "https://search.grants.nih.gov/guide/api/data"
NIH_GUIDE_RSS = "https://grants.nih.gov/grants/guide/newsfeed/fundingopps.xml"
NIH_NOTICE = "https://grants.nih.gov/grants/guide/notice-files/{}.html"
REPORTER = "https://api.reporter.nih.gov/v2/projects/search"
SBIR_TOPICS = "https://api.www.sbir.gov/public/api/topics"
DSIP_TOPICS = "https://www.dodsbirsttr.mil/topics-app/api/topics/search"
SIMPLER = "https://api.simpler.grants.gov/v1/opportunities/search"
SAM_SEARCH = "https://api.sam.gov/opportunities/v2/search"


class SourceLog(object):
    """Holds one line per source per run. Rendered verbatim into the digest
    so a run with three dead sources cannot read as a complete sweep."""

    def __init__(self):
        self.rows = OrderedDict()

    def record(self, key, status, detail, url="", count=None):
        self.rows[key] = {"status": status, "detail": detail, "url": url,
                          "count": count}

    def ok(self, key, count, url, note=""):
        state = "OK" if count else "EMPTY"
        detail = "%d record(s)%s" % (count, (" — " + note) if note else "")
        if not count:
            detail = "reachable but returned zero records%s" % (
                (" — " + note) if note else "")
        self.record(key, state, detail, url, count)

    def fail(self, key, detail, url=""):
        self.record(key, "FAILED", detail, url, 0)

    def nocred(self, key, detail, url=""):
        self.record(key, "NO-CREDENTIAL", detail, url, 0)

    def holes(self):
        return [k for k, v in self.rows.items()
                if v["status"] in ("FAILED", "NO-CREDENTIAL")]


LOG = SourceLog()
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": UA, "Accept": "*/*"})


def _http(method, url, **kw):
    """One retry with backoff. Raises for status so callers can log the code."""
    kw.setdefault("timeout", TIMEOUT)
    last = None
    for attempt in range(3):
        try:
            resp = _SESSION.request(method, url, **kw)
            if resp.status_code >= 500 and attempt < 2:
                last = requests.HTTPError("HTTP %d" % resp.status_code)
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise last


def _detail(exc):
    resp = getattr(exc, "response", None)
    if resp is not None:
        return "HTTP %d %s" % (resp.status_code, resp.reason or "")
    return type(exc).__name__ + ": " + str(exc)[:160]


def _json_or_die(resp):
    """A blocked endpoint often answers 200 with an HTML error page, which
    surfaces as a bare JSONDecodeError and reads like a bug in this program.
    Say what actually happened instead."""
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "json" not in ctype:
        raise ValueError("expected JSON, got %s (%d bytes) — the endpoint "
                         "answered with %s, which is what a block or "
                         "a WAF challenge looks like"
                         % (ctype or "no content-type", len(resp.content),
                            "an HTML page" if "html" in ctype
                            else "a non-JSON body"))
    return resp.json()


def _text(raw):
    """HTML -> flat text. Used on NOFOs and NIH notices."""
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"[ \t ]+", " ", raw)


# --- 1. Grants.gov Search2 (keyless) ---------------------------------------

def fetch_grants_gov(queries, rows=100, max_pages=4):
    """Discovery + the authoritative record for FON, title, and close date.
    Returns raw oppHits keyed by grants.gov opportunity id."""
    found, pages = OrderedDict(), 0
    try:
        for kw in queries:
            for page in range(max_pages):
                body = {"keyword": kw, "rows": rows,
                        "startRecordNum": page * rows,
                        "oppStatuses": "posted|forecasted"}
                data = (_http("POST", GRANTS_SEARCH, json=body).json()
                        or {}).get("data") or {}
                pages += 1
                hits = data.get("oppHits") or []
                for h in hits:
                    found.setdefault(str(h.get("id")), h)
                if len(hits) < rows:
                    break
    except requests.RequestException as exc:
        LOG.fail("grants.gov Search2", _detail(exc), GRANTS_SEARCH)
        return found
    except ValueError as exc:
        LOG.fail("grants.gov Search2", "JSON decode: %s" % exc, GRANTS_SEARCH)
        return found
    LOG.ok("grants.gov Search2", len(found), GRANTS_SEARCH,
           "%d keyword page(s)" % pages)
    return found


def fetch_grants_detail(opp_id):
    """Full synopsis: eligibility text, response date, contacts, attachments.
    Returns None on failure — callers must treat that as unverified."""
    try:
        return (_http("POST", GRANTS_FETCH,
                      json={"opportunityId": int(opp_id)}).json()
                or {}).get("data")
    except (requests.RequestException, ValueError, TypeError):
        return None


def fetch_nofo_text(detail):
    """Pull the announcement's own Full Announcement attachment. This is where
    the IC budget table lives, so this fetch is what makes it possible to
    print a budget cap without inventing one. Returns (text, url) or (None, "")."""
    for folder in (detail.get("synopsisAttachmentFolders") or []):
        for att in (folder.get("synopsisAttachments") or []):
            name = (att.get("fileName") or "").lower()
            if not name.endswith((".html", ".htm")):
                continue
            url = GRANTS_ATT.format(att.get("id"))
            try:
                return _text(_http("GET", url).text), url
            except requests.RequestException:
                continue
    return None, ""


# --- 2. NIH Guide search API (keyless) — the NOSI / PA / PAR / RFA channel --

GUIDE_PAGE = 25          # server-enforced; asking for more still returns 25
GUIDE_MAX_PAGES = 16     # 400 records/query, newest first
GUIDE_LOOKBACK_DAYS = 900


def fetch_nih_guide(queries, size=GUIDE_PAGE, label="NIH Guide search API",
                    lookback=GUIDE_LOOKBACK_DAYS):
    """The real discovery surface for NOSIs, PAs, PARs and RFAs.

    Three server behaviours this has to work around, all found by probing:
      * page size is capped at 25 no matter what `size` asks for;
      * `from` paging works, so the cap is a paging problem, not a wall;
      * the only filter that actually applies is `doctype` — activity code,
        IC and date are ignored server-side, so they are applied here.
    Sorted newest-first, so paging stops as soon as it walks past the
    lookback window rather than draining the whole index."""
    found = OrderedDict()
    cutoff = (TODAY - dt.timedelta(days=lookback)).isoformat()
    pages = 0
    try:
        for kw in queries:
            for page in range(GUIDE_MAX_PAGES):
                params = {"query": kw, "from": page * GUIDE_PAGE,
                          "size": GUIDE_PAGE, "sort": "reldate:desc"}
                hits = (((_http("GET", NIH_GUIDE_API, params=params).json()
                          or {}).get("data") or {}).get("hits") or {}).get("hits") or []
                pages += 1
                if not hits:
                    break
                oldest = "9999"
                for h in hits:
                    src = h.get("_source") or {}
                    if src.get("docnum"):
                        found.setdefault(src["docnum"], src)
                    oldest = min(oldest, (src.get("reldate") or "9999")[:10])
                if len(hits) < GUIDE_PAGE or oldest < cutoff:
                    break
    except requests.RequestException as exc:
        LOG.fail(label, _detail(exc), NIH_GUIDE_API)
        return found
    except ValueError as exc:
        LOG.fail(label, "JSON decode: %s" % exc, NIH_GUIDE_API)
        return found
    LOG.ok(label, len(found), NIH_GUIDE_API,
           "%d quer(ies) over %d page(s), released within %d days"
           % (len(queries), pages, lookback))
    return found


def fetch_nih_rss():
    """This week's new notices. Catches a NOSI the day it posts, before the
    search index necessarily surfaces it against our keywords."""
    items = []
    try:
        raw = _http("GET", NIH_GUIDE_RSS).text
        for block in re.findall(r"<item>(.*?)</item>", raw, re.S | re.I):
            def grab(tag):
                m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), block, re.S | re.I)
                return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""
            items.append({"title": grab("title"), "link": grab("link"),
                          "pubDate": grab("pubDate")})
    except requests.RequestException as exc:
        LOG.fail("NIH Guide weekly RSS", _detail(exc), NIH_GUIDE_RSS)
        return items
    LOG.ok("NIH Guide weekly RSS", len(items), NIH_GUIDE_RSS)
    return items


def fetch_notice_text(docnum):
    try:
        return _text(_http("GET", NIH_NOTICE.format(docnum)).text)
    except requests.RequestException:
        return ""


# --- 3. NIH RePORTER v2 — award intelligence, NOT opportunity discovery -----

def fetch_reporter(terms, activity_codes, years, limit=500, ic=None):
    """Gate 6's engine. Answers: how crowded is this topic, who keeps winning
    it, and who is the program officer. Returns (results, error_or_None)."""
    crit = {"fiscal_years": list(years), "activity_codes": list(activity_codes)}
    if terms:
        crit["advanced_text_search"] = {
            "operator": "and", "search_field": "projecttitle,abstracttext,terms",
            "search_text": " ".join(terms)}
    if ic:
        crit["agencies"] = [ic]
    body = {"criteria": crit, "include_fields": [
        "ProjectNum", "ProjectTitle", "AgencyIcAdmin", "AwardAmount",
        "Organization", "PrincipalInvestigators", "ProgramOfficers",
        "FiscalYear", "ActivityCode"], "limit": min(limit, 500), "offset": 0}
    try:
        payload = _http("POST", REPORTER, json=body).json() or {}
        return payload.get("results") or [], None
    except requests.RequestException as exc:
        return [], _detail(exc)
    except ValueError as exc:
        return [], "JSON decode: %s" % exc


# --- 4-6. The three sources expected to be unreachable. Probed every run so
# the digest reports today's truth, not a stale assumption. ------------------

def probe_sbir_gov():
    """The user flagged this returns 403. Confirm it each run rather than
    hardcoding the assumption — and if it ever comes back, use it."""
    try:
        payload = _json_or_die(
            _http("GET", SBIR_TOPICS, params={"rows": 100, "open": 1}))
        items = payload if isinstance(payload, list) else (payload.get("data") or [])
        LOG.ok("SBIR.gov cross-agency topics", len(items), SBIR_TOPICS)
        return items
    except requests.RequestException as exc:
        LOG.fail("SBIR.gov cross-agency topics",
                 "%s — cross-agency topic search UNAVAILABLE this run; any "
                 "non-NIH topic that exists only on sbir.gov was not swept"
                 % _detail(exc), SBIR_TOPICS)
    except ValueError as exc:
        LOG.fail("SBIR.gov cross-agency topics", "JSON decode: %s" % exc,
                 SBIR_TOPICS)
    return []


def probe_dsip():
    body = {"searchText": None, "components": None, "programYear": None,
            "solicitationCycleNames": ["openTopics"], "releaseNumbers": [],
            "topicReleaseStatus": [591], "modernizationPriorities": [],
            "sortBy": "finalTopicCode,asc", "technologyAreaIds": [],
            "component": None, "program": None, "rowsPerPage": 100}
    try:
        payload = _json_or_die(_http("POST", DSIP_TOPICS, json=body)) or {}
        items = payload.get("data") or []
        LOG.ok("DoD DSIP open topics", len(items), DSIP_TOPICS)
        return items
    except requests.RequestException as exc:
        LOG.fail("DoD DSIP open topics",
                 "%s — DoD SBIR/STTR topics NOT swept this run; check "
                 "https://www.defensesbirsttr.mil/SBIR-STTR/Opportunities/ "
                 "by hand before treating the digest as cross-agency"
                 % _detail(exc), DSIP_TOPICS)
    except ValueError as exc:
        LOG.fail("DoD DSIP open topics", "JSON decode: %s" % exc, DSIP_TOPICS)
    return []


def probe_simpler(queries):
    key = os.environ.get("SIMPLER_GRANTS_API_KEY")
    if not key:
        LOG.nocred("Simpler.Grants.gov API",
                   "no SIMPLER_GRANTS_API_KEY in env — this source returns 401 "
                   "without one. Request a key at "
                   "https://wiki.simpler.grants.gov/product/api . Not fatal: "
                   "it indexes the same opportunities as Search2, which ran.",
                   SIMPLER)
        return []
    found = []
    try:
        for kw in queries:
            body = {"query": kw, "pagination": {
                "page_offset": 1, "page_size": 100, "sort_order": [
                    {"order_by": "post_date", "sort_direction": "descending"}]}}
            payload = _http("POST", SIMPLER, json=body,
                            headers={"X-Auth": key}).json() or {}
            found.extend(payload.get("data") or [])
        LOG.ok("Simpler.Grants.gov API", len(found), SIMPLER)
    except requests.RequestException as exc:
        LOG.fail("Simpler.Grants.gov API", _detail(exc), SIMPLER)
    except ValueError as exc:
        LOG.fail("Simpler.Grants.gov API", "JSON decode: %s" % exc, SIMPLER)
    return found


def probe_sam():
    """Contract-based SBIR topics (PHS solicitations, some DoD components).
    Reuses the key the SAM matcher already uses."""
    key = os.environ.get("SAM_API_KEY")
    if not key:
        LOG.nocred("SAM.gov Opportunities v2",
                   "no SAM_API_KEY in env — contract-based SBIR topics (PHS "
                   "solicitations, DoD component buys) were NOT swept. Grant-"
                   "based NIH coverage is unaffected.", SAM_SEARCH)
        return []
    frm = (TODAY - dt.timedelta(days=45)).strftime("%m/%d/%Y")
    out = []
    try:
        for kw in ("SBIR", "STTR"):
            params = {"api_key": key, "postedFrom": frm,
                      "postedTo": TODAY.strftime("%m/%d/%Y"),
                      "limit": 200, "title": kw}
            payload = _http("GET", SAM_SEARCH, params=params).json() or {}
            out.extend(payload.get("opportunitiesData") or [])
        LOG.ok("SAM.gov Opportunities v2", len(out), SAM_SEARCH,
               "contract-based topics, last 45 days")
    except requests.RequestException as exc:
        LOG.fail("SAM.gov Opportunities v2", _detail(exc), SAM_SEARCH)
    except ValueError as exc:
        LOG.fail("SAM.gov Opportunities v2", "JSON decode: %s" % exc, SAM_SEARCH)
    return out


# ---------------------------------------------------------------------------
# NOFO PARSING — budget caps, due dates, and PI rules come out of the
# announcement's own text. Nothing in this section falls back to a constant.
# ---------------------------------------------------------------------------

MONEY = re.compile(r"\$[\d,]+(?:\.\d{2})?")


def as_ic_table(cached):
    """The cache round-trips through JSON with sort_keys=True, which silently
    re-alphabetises a dict and loses the announcement's own ordering. Tables
    are therefore cached as ordered pairs and rebuilt here."""
    if isinstance(cached, list):
        return OrderedDict((k, tuple(v)) for k, v in cached)
    return OrderedDict(cached or {})


def parse_ic_budget_table(nofo_html):
    """Extract the 'NIH Participating Component / Phase I Budget / Phase II
    Budget' table. Returns OrderedDict[full IC name] = (phase1, phase2) with
    the strings EXACTLY as the NOFO prints them, 'SBA Guideline' included."""
    table = OrderedDict()
    for tb in re.findall(r"<table.*?</table>", nofo_html, re.S | re.I):
        flat = re.sub(r"<[^>]+>", " ", tb)
        if "Phase I Budget" not in flat:
            continue
        for row in re.findall(r"<tr.*?</tr>", tb, re.S | re.I):
            cells = [html.unescape(re.sub(r"\s+", " ",
                     re.sub(r"<[^>]+>", "", c))).strip()
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row,
                                         re.S | re.I)]
            if len(cells) == 3 and cells[0] and "Participating Component" not in cells[0]:
                table[cells[0]] = (cells[1], cells[2])
    return table


def parse_due_dates(nofo_text):
    """Application due dates as printed in the NOFO's Key Dates table."""
    m = re.search(r"Application Due Dates(.{0,2500}?)All applications are due",
                  nofo_text, re.S | re.I)
    chunk = m.group(1) if m else nofo_text[:4000]
    seen, out = set(), []
    for raw in re.findall(
            r"(January|February|March|April|May|June|July|August|September|"
            r"October|November|December)\s+(\d{1,2}),\s*(\d{4})", chunk):
        iso = _to_iso(" ".join(raw))
        if iso and iso not in seen and iso >= TODAY.isoformat():
            seen.add(iso)
            out.append(iso)
    return sorted(out)


def _to_iso(text):
    text = re.sub(r"[*,]", " ", text or "").strip()
    for fmt in ("%B %d %Y", "%b %d %Y", "%m/%d/%Y", "%Y-%m-%d",
                "%b %d %Y %H:%M:%S", "%B %d %Y %H:%M:%S"):
        try:
            return dt.datetime.strptime(re.sub(r"\s+", " ", text)[:len(
                dt.datetime(2000, 1, 1).strftime(fmt))], fmt).date().isoformat()
        except ValueError:
            continue
    m = re.search(r"([A-Z][a-z]{2,8})\s+(\d{1,2})\s+(\d{4})", text)
    if m:
        for fmt in ("%B %d %Y", "%b %d %Y"):
            try:
                return dt.datetime.strptime(" ".join(m.groups()), fmt).date().isoformat()
            except ValueError:
                continue
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    return m.group(0) if m else None


# ---------------------------------------------------------------------------
# GATES — applied in order, cheapest first, STOP at the first fail. Every
# opportunity carries the name of the gate that killed it. sbir/GATE.md is
# the prose version of this section; keep the two aligned.
# ---------------------------------------------------------------------------

_TERM_RE = {}


def _term_re(term):
    """Match a vocabulary term on word boundaries. Short tokens (gcp, edc,
    irb, ehr, rave) are the reason this exists: substring matching scored
    'rave' as a Medidata Rave hit inside the word 'grave'. Terms ending in a
    deliberate stem ('histolog', 'immunohistochem') keep an open right edge."""
    rx = _TERM_RE.get(term)
    if rx is None:
        stem = term.rstrip()
        right = "" if re.search(r"[a-z]$", stem) and stem in _OPEN_STEMS else r"\b"
        rx = re.compile(r"\b" + re.escape(stem).replace(r"\ ", r"[\s\-]+")
                        + right)
        _TERM_RE[term] = rx
    return rx


# Vocabulary entries that are deliberately truncated stems, so they must
# still match the words they were written to catch.
_OPEN_STEMS = frozenset([
    "histolog", "immunohistochem", "glp toxicolog", "animal facilit",
    "gmp manufactur", "scale-up manufactur", "crp) program",
    "monoclonal antibod", "compound librar", "biomarker discovery",
    "data harmoniz", "synthesi", "fabricat", "pharmacokinetic",
    "medicinal chemistry", "animal stud", "cliaertified laboratory",
])


def _hits(text, vocab):
    low = (text or "").lower()
    return [t for t in vocab if _term_re(t).search(low)]


def gate1_eligibility(opp):
    """US-owned for-profit small business, <500 employees, US performance.
    Kill anything requiring a facility PRG does not have.

    The nuance that matters: under STTR the partnering research institution
    may hold the lab. So wet-lab and animal language kills only when the
    SMALL BUSINESS must hold the capability, or when the science is so
    bench-centric that PRG cannot supply its mandatory 40% of the effort."""
    text = opp.get("scope") or opp["text"]
    low = text.lower()

    title_low = (opp["title"] or "").lower()
    if opp["docnum"].upper() in OMNIBUS:
        return False, "G1", ("omnibus parent announcement — always open, no "
                             "stated need to compete against. Finding it is "
                             "not the task (see sbir/GATE.md)")
    for term in PRIOR_AWARD_GATED:
        if _term_re(term).search(title_low):
            return False, "G1", ("gated on a prior SBIR/STTR award PRG does "
                                 "not hold (\"%s\")" % term)

    for term in KILL_CLEARANCE:
        if _term_re(term).search(low):
            return False, "G1", ("requires a facility clearance PRG does not "
                                 "hold at proposal time (\"%s\")" % term)
    for term in KILL_INELIGIBLE:
        if _term_re(term).search(low):
            return False, "G1", ("restricted to an eligibility PRG lacks "
                                 "(\"%s\")" % term)
    for term in KILL_GMP:
        if _term_re(term).search(low):
            return False, "G1", ("needs GMP/manufacturing capability PRG has "
                                 "no path to (\"%s\")" % term)
    for term in KILL_OWN_SITE:
        if _term_re(term).search(low):
            return False, "G1", ("requires the applicant to operate a clinical "
                                 "site or CLIA lab; PRG has neither (\"%s\")"
                                 % term)

    animal = _hits(low, KILL_ANIMAL)
    wet = _hits(low, KILL_WET_LAB)
    if opp["mechanism"] == "SBIR" and (animal or wet):
        # No STTR partner to hold the lab, and PRG has none.
        return False, "G1", ("SBIR with wet-lab/animal work and no partner "
                             "institution to hold it (%s)"
                             % ", ".join((animal + wet)[:3]))
    if len(animal) + len(wet) >= 4:
        # Bench-dominant even for an STTR: PRG cannot supply 40% of effort.
        return False, "G1", ("bench/animal-dominant (%s) — PRG cannot supply "
                             "the STTR-mandatory 40%% of research effort"
                             % ", ".join((animal + wet)[:4]))

    if "non-domestic" in low and "not eligible" in low:
        pass                     # standard NIH boilerplate, PRG is domestic
    opp["lab_notes"] = sorted(set(animal + wet))
    return True, "G1", "US small business, no facility PRG lacks is mandatory"


def gate2_mechanism(opp):
    """STTR passes. SBIR passes only if Andrew could plausibly be PI himself
    under the primarily-employed rule — which, while he is job searching, he
    cannot. So an SBIR survives only when the work is solo-operator-shaped
    AND it is flagged loudly for what it would cost him."""
    mech = opp["mechanism"]
    if sttr_eligible(mech):
        opp["pi_note"] = ("STTR: PD/PI may be employed by the partnering "
                          "non-profit research institution, so long as the PI "
                          "holds a formal appointment with or commitment to "
                          "PRG (no salary required) and commits >=10% effort. "
                          "Compatible with Andrew taking a full-time role.")
        return True, "G2", ("%s — the STTR path (R41/R42) lets the PI sit at "
                            "the institution" % mech)
    if mech == "SBIR":
        if OPERATOR["primarily_employable_at_sbc"]:
            return True, "G2", "SBIR and PI employment is available"
        solo = _hits(opp.get("scope") or opp["text"], list(FIT_TIER_A) + [
            "software", "algorithm", "dashboard", "analytic", "curriculum",
            "toolkit", "guideline", "framework", "training module"])
        bench = _hits(opp.get("scope") or opp["text"],
                      KILL_WET_LAB + KILL_ANIMAL)
        if solo and not bench:
            opp["pi_note"] = ("SBIR: requires the PD/PI to be PRIMARILY "
                              "EMPLOYED (>50%) by PRG at award and through the "
                              "project. Andrew is job searching, so this is a "
                              "conflict, not a formality. Surfaced only "
                              "because the work is solo-operator-shaped.")
            return True, "G2", ("SBIR (R43/R44) — SURFACED WITH CONFLICT: "
                                "primarily-employed rule versus the job search")
        return False, "G2", ("SBIR requires Andrew to be primarily employed by "
                             "PRG, which the concurrent job search rules out, "
                             "and the work is not solo-operator-shaped")
    return False, "G2", "not an SBIR/STTR mechanism"


def gate3_capability(opp):
    """Score 0-5 against the operator profile. <=2 dies. Honest, not generous:
    'adjacent to healthcare' scores nothing, 'needs someone who has run trial
    operations at a site' scores high."""
    low = (opp.get("scope") or opp["text"] or "").lower()
    raw, evidence = 0.0, []
    for vocab, label in ((FIT_TIER_A, "A"), (FIT_TIER_B, "B"),
                         (FIT_TIER_C, "C")):
        tier_total = 0.0
        for term, weight in vocab.items():
            if _term_re(term).search(low):
                tier_total += weight
                if len(evidence) < 8:
                    evidence.append("%s:%s" % (label, term))
        raw += min(tier_total, {"A": 3.6, "B": 1.6, "C": 0.8}[label])
    penalty = 0.0
    for term, weight in FIT_NEGATIVE.items():
        if _term_re(term).search(low):
            penalty += weight
    raw += max(penalty, -2.5)
    score = max(0.0, min(5.0, round(raw, 1)))
    opp["fit_score"] = score
    opp["fit_evidence"] = evidence

    niches = [(t, why) for t, why in ELIGIBILITY_NICHE.items()
              if _term_re(t).search(low)]
    opp["niches"] = niches
    if score <= 2.0:
        if niches:
            # The fit score stays honest — this is NOT scored up to look like
            # capability. It survives because a restricted field is worth
            # pursuing on its own terms, and the digest says which it is.
            opp["niche_only"] = True
            return True, "G3", ("capability fit %.1f/5 (low) but the "
                                "eligibility field is restricted in PRG's "
                                "favour: %s" % (score, niches[0][1]))
        return False, "G3", ("capability fit %.1f/5 — no site-level trial-"
                             "operations demand in the text%s" % (
                                 score,
                                 "; bench-science signals pull it down"
                                 if penalty < 0 else ""))
    return True, "G3", ("capability fit %.1f/5%s"
                        % (score, " + restricted eligibility field"
                           if niches else ""))


def gate4_partner(opp):
    """Name the specific academic home that would host the PI, and say
    whether Stanford Department of Medicine is credible for it."""
    low = (opp.get("scope") or opp["text"] or "").lower()
    best, best_hits = None, 0
    for name, spec in PARTNER_MAP.items():
        n = sum(1 for t in spec["match"] if _term_re(t).search(low))
        if n > best_hits:
            best, best_hits = name, n
    if best is None or best_hits == 0:
        if opp.get("niche_only"):
            spec = PARTNER_MAP["clinical trial operations"]
            opp["partner_domain"] = "clinical trial operations"
            opp["partner_dept"] = spec["dept"]
            opp["partner_stanford"] = True
            opp["partner_why"] = (
                "the announcement is not yet topic-specific, so this is the "
                "default home PRG would pitch: %s" % spec["why"])
            return True, "G4", ("no topic yet — default partner is Stanford "
                                "Dept of Medicine (CTSA)")
        return False, "G4", ("no identifiable academic partner type — cannot "
                             "name a department that would host the PI")
    spec = PARTNER_MAP[best]
    if spec["dept"] is None:
        return False, "G4", ("needs a wet-lab discovery PI (%s); PRG has no "
                             "path to that partner type and could not manage "
                             "the science" % best)
    opp["partner_domain"] = best
    opp["partner_dept"] = spec["dept"]
    opp["partner_stanford"] = spec["stanford_credible"]
    opp["partner_why"] = spec["why"]
    return True, "G4", ("partner: %s%s" % (
        spec["dept"],
        "" if spec["stanford_credible"] else " (cold relationship)"))


def gate5_deadline(opp):
    """A first-time STTR with an institutional partner and an IP allocation
    agreement to negotiate needs 90+ days. Under that is 'next cycle', not
    'actionable' — and never silently dropped."""
    dues = opp.get("due_dates") or []
    if not dues:
        opp["days_left"] = None
        opp["deadline_class"] = "UNDATED"
        opp["feasibility"] = 0.5
        return True, "G5", ("no due date published on a primary source — "
                            "treat as rolling; VERIFY before committing")
    nxt = dues[0]
    days = (dt.date.fromisoformat(nxt) - TODAY).days
    opp["next_due"] = nxt
    opp["days_left"] = days
    later = [d for d in dues if (dt.date.fromisoformat(d) - TODAY).days >= 90]
    if days >= 90:
        opp["deadline_class"] = "ACTIONABLE"
        opp["feasibility"] = 1.0
    elif later:
        opp["deadline_class"] = "NEXT CYCLE"
        opp["feasibility"] = 0.4
        opp["cycle_target"] = later[0]
    else:
        opp["deadline_class"] = "NEXT CYCLE"
        opp["feasibility"] = 0.25
    if days < 0:
        return False, "G5", "closed %d day(s) ago" % (-days)
    return True, "G5", "%d day(s) to %s (%s)" % (days, nxt,
                                                 opp["deadline_class"])


def gate6_competition(opp, years):
    """Crowding, repeat winners, and the named program officer. A topic with
    40 prior awards to the same three firms is a different bet than one with
    four, and this gate is what tells them apart."""
    terms = opp.get("topic_terms") or []
    if opp["mechanism"] == "STTR":
        codes = list(STTR_CODES)
    elif opp["mechanism"] == "SBIR":
        codes = list(SBIR_CODES)
    else:                        # dual SBIR/STTR notice — count both families
        codes = list(STTR_CODES) + list(SBIR_CODES)
    raw, err = fetch_reporter(terms, codes, years, ic=opp.get("ic_abbrev"))
    results = dedupe_projects(raw)
    if err:
        opp["competition"] = {"error": err}
        return True, "G6", ("RePORTER unavailable (%s) — crowding UNKNOWN, "
                            "do not read the go/no-go as competition-tested"
                            % err)
    orgs = Counter()
    pos = Counter()
    amounts = []
    for r in results:
        org = ((r.get("organization") or {}).get("org_name") or "").title()
        if org:
            orgs[org] += 1
        for po in (r.get("program_officers") or []):
            full = re.sub(r"\s+", " ", (po.get("full_name") or "")).strip().title()
            if full:
                pos[full] += 1
        if r.get("award_amount"):
            amounts.append(r["award_amount"])
    top = orgs.most_common(3)
    concentration = (sum(n for _, n in top) / float(len(results))) if results else 0.0
    opp["competition"] = {
        "n_awards": len(results),
        "n_rows": len(raw),
        "years": "FY%d-FY%d" % (min(years), max(years)),
        "top_firms": top,
        "concentration": round(concentration, 2),
        "program_officers": pos.most_common(3),
        "median_award": (sorted(amounts)[len(amounts) // 2] if amounts else None),
        "query_terms": terms,
        "reporter_url": ("https://reporter.nih.gov/search — criteria: "
                         "activity %s, FY%d-%d, text \"%s\"%s"
                         % ("/".join(codes), min(years), max(years),
                            " ".join(terms),
                            (", IC " + opp["ic_abbrev"]) if opp.get("ic_abbrev") else "")),
    }
    if len(results) >= 25 and concentration >= 0.45:
        opp["crowding"] = "CROWDED-CAPTURED"
    elif len(results) >= 25:
        opp["crowding"] = "CROWDED-OPEN"
    elif len(results) >= 6:
        opp["crowding"] = "CONTESTED"
    elif len(results) >= 1:
        opp["crowding"] = "THIN"
    else:
        opp["crowding"] = "UNPROVEN"
    return True, "G6", "%d prior award(s), %s" % (len(results), opp["crowding"])


GATES = (gate1_eligibility, gate2_mechanism, gate3_capability,
         gate4_partner, gate5_deadline)


# ---------------------------------------------------------------------------
# CANDIDATE SPECIFIC AIMS — skeletons, not prose. Each is anchored to
# something Andrew can defend in a phone call with a program officer, which
# is the only test that matters at this stage.
# ---------------------------------------------------------------------------

AIM_LIBRARY = {
    "clinical trial operations": [
        ("Aim 1. Characterize the site-level failure modes the topic targets "
         "by structured retrospective review of {n} trials at the partner "
         "institution, coding deviations, screen failures, and startup delays "
         "against a taxonomy Andrew built from Stanford Dept of Medicine "
         "operations."),
        ("Aim 2. Build and instrument the {thing} against that taxonomy, "
         "using REDCap/OnCore as the system of record so the intervention "
         "rides existing site infrastructure rather than asking coordinators "
         "to adopt a parallel tool."),
        ("Aim 3. Test feasibility in a single-arm pilot at 2-3 partner-"
         "institution study teams, with predefined thresholds on coordinator "
         "burden (time-on-task), data-quality (query rate, SDV findings), and "
         "cycle time to site activation."),
    ],
    "clinical data / informatics": [
        ("Aim 1. Map the data path end to end for {topic} at the partner "
         "institution — source, EDC, and downstream — and quantify where "
         "quality is actually lost, using query and SDV records rather than "
         "self-report."),
        ("Aim 2. Specify and implement the {thing} to a published standard "
         "(CDISC/OMOP/FHIR as the topic dictates), with 21 CFR Part 11 audit "
         "and provenance requirements designed in rather than retrofitted."),
        ("Aim 3. Validate against a gold-standard manually-abstracted subset, "
         "reporting agreement, time saved per record, and the residual error "
         "classes that still require human adjudication."),
    ],
    "health services / implementation": [
        ("Aim 1. Quantify the delivery gap the topic names within the partner "
         "institution's population, stratified by the subgroups the funding "
         "IC cares about, using existing EHR and registry data."),
        ("Aim 2. Co-design the {thing} with the clinicians and coordinators "
         "who would run it, and specify implementation strategies and "
         "fidelity measures explicitly (not as an afterthought)."),
        ("Aim 3. Pilot in 2-3 clinics with feasibility, acceptability, and "
         "fidelity endpoints prespecified, plus a costed pathway to the "
         "Phase II hybrid effectiveness-implementation design."),
    ],
    "device / clinical engineering": [
        ("Aim 1. Establish the maintenance/failure baseline for the device "
         "class in scope using partner-institution HTM records, framed to "
         "Joint Commission and manufacturer service requirements."),
        ("Aim 2. Build the {thing} and integrate it with the CMMS and clinical "
         "workflow, with human-factors requirements derived from observed "
         "technician and clinician tasks."),
        ("Aim 3. Bench-and-field feasibility test against the baseline, "
         "reporting uptime, mean-time-to-repair, and technician burden."),
    ],
}


def draft_aims(opp):
    dom = opp.get("partner_domain") or "clinical trial operations"
    lib = AIM_LIBRARY.get(dom) or AIM_LIBRARY["clinical trial operations"]
    thing = "intervention"
    for cand in ("toolkit", "platform", "dashboard", "instrument", "workflow",
                 "algorithm", "curriculum", "registry", "software"):
        if _term_re(cand).search(
                (opp.get("scope") or opp["text"] or "").lower()):
            thing = cand
            break
    topic = (opp.get("topic_terms") or ["the topic"])[0]
    n = "20-30"
    return [a.format(thing=thing, topic=topic, n=n) for a in lib]


def foreign_screening(opp):
    hits = _hits(opp["text"], FOREIGN_FLAGS)
    opp["foreign_flags"] = hits
    return hits


# ---------------------------------------------------------------------------
# OPPORTUNITY ASSEMBLY
# ---------------------------------------------------------------------------

STOP = set("""a an the and or of for to in on with by from at as is are be this
that these those using use used new nih national institute institutes center
centers notice notices special interest program announcement research small
business innovation technology transfer sbir sttr phase grant grants award
awards application applications clinical trial trials optional required not
allowed development r41 r42 r43 r44 parent omnibus""".split())


# Everything from "Section II. Award Information" onward in an NIH NOFO is
# boilerplate that is byte-identical across every announcement NIH publishes.
# Scoring capability fit against it makes every NOFO score 5.0/5, and makes
# "Select Agent Research" (a review-criteria heading) look like a wet-lab
# requirement. So gates 1, 3, and 4 read the scope, not the document.
SCOPE_START = re.compile(
    r"(Purpose\s|Research Objectives|Background\s|Specific Areas of "
    r"Research Interest|Scientific/Research Contact|Funding Opportunity "
    r"Purpose|Notice of Special Interest)", re.I)
SCOPE_END = re.compile(
    r"(Section II\.|Award Information|Section III\.|Eligibility "
    r"Information|Funding Instrument|Application and Submission)", re.I)


def scope_of(title, text):
    """Return the part of the announcement that says what it actually wants.
    Falls back to the whole text for short documents (NOSIs are short and are
    all signal), and to the head of the document if no section marker hits."""
    text = text or ""
    if len(text) < 12000:
        return (title or "") + " " + text
    start = SCOPE_START.search(text)
    head = text[start.start():] if start else text
    end = SCOPE_END.search(head, 400)
    body = head[:end.start()] if end else head[:20000]
    if len(body) < 600:
        body = text[:20000]
    return (title or "") + " " + body


def topic_terms(title, k=3):
    words = re.findall(r"[a-z][a-z\-]{3,}", (title or "").lower())
    keep = [w for w in words if w not in STOP]
    seen, out = set(), []
    for w in keep:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:k]


def detect_mechanism(title, docnum="", activity=""):
    """Mechanism comes from the TITLE, the doc number, and the indexed activity
    code — never from the announcement body. Every NIH small-business NOFO
    mentions both programs somewhere in 90KB of boilerplate, so scanning the
    body classifies an R44-only announcement as STTR. That bug shipped once."""
    blob = " ".join([title or "", docnum or "", activity or ""]).upper()
    has_sttr = "STTR" in blob or re.search(r"\bR4[12]\b", blob)
    has_sbir = "SBIR" in blob or re.search(r"\bR4[34]\b", blob)
    if has_sttr and has_sbir:
        return "SBIR/STTR"       # dual notice; STTR path is the one PRG runs
    if has_sttr:
        return "STTR"
    if has_sbir:
        return "SBIR"
    return "OTHER"


def sttr_eligible(mech):
    return mech in ("STTR", "SBIR/STTR")


# NIH serial numbers embed a two-letter IC code (NOT-DK-27-402 -> NIDDK).
# That mapping is NOT typed from memory here: it is harvested each run from
# the NIH Guide index itself, by pairing every indexed docnum against the
# primaryIC the index assigns it, and accumulated in sbir/state/nofo_cache.json.
# A code the index has never shown us stays unresolved, and the digest then
# prints a cap RANGE with its source rather than picking an institute.
IC_CODE_RE = re.compile(r"^(?:NOT|PA|PAR|RFA|RFP|NOSI)-([A-Z]{2})-\d")


def harvest_ic_codes(guide_records, prior=None):
    votes = {}
    for src in guide_records:
        m = IC_CODE_RE.match((src.get("docnum") or "").upper())
        ic = (src.get("primaryIC") or "").upper()
        if not m or ic not in IC_ABBREV.values():
            continue
        votes.setdefault(m.group(1), Counter())[ic] += 1
    out = dict(prior or {})
    for code, c in votes.items():
        out[code] = c.most_common(1)[0][0]
    return out


def detect_ic(docnum, primary_ic="", code_map=None):
    """Resolve to ONE institute or to nothing. Never to a plausible guess:
    an announcement's participating-components list names every IC at NIH, so
    matching institute names in the body would 'resolve' every notice to NCI."""
    if primary_ic and primary_ic.upper() in IC_ABBREV.values():
        return primary_ic.upper()
    m = IC_CODE_RE.match((docnum or "").upper())
    if m and code_map:
        return code_map.get(m.group(1))
    return None


def resolve_caps(opp, ic_table, table_url):
    """Budget caps, verified or explicitly absent. Order of preference:
      1. a cap the opportunity itself prints,
      2. the parent NOFO's IC budget table for this opportunity's IC,
      3. "NOT VERIFIED" — never a guess."""
    own = re.search(r"(?:Phase\s*I|budget)[^.]{0,120}?(\$[\d,]{6,})",
                    opp.get("scope") or "", re.I)
    ab = opp.get("ic_abbrev")
    full = None
    for name, code in IC_ABBREV.items():
        if code == ab:
            full = name
            break
    if full and full in ic_table:
        p1, p2 = ic_table[full]
        g1, g2, gnote = sba_guideline()
        opp["cap_phase1"] = expand_cap(p1, g1, g2, 1)
        opp["cap_phase2"] = expand_cap(p2, g1, g2, 2)
        opp["cap_source"] = table_url
        opp["cap_basis"] = ("%s row of the IC budget table in the parent "
                            "announcement%s" % (
                                ab,
                                ("; SBA guideline figure %s" % gnote)
                                if "sba guideline" in (p1 + p2).lower()
                                else ""))
        return
    if own:
        opp["cap_phase1"] = own.group(1)
        opp["cap_phase2"] = "see announcement"
        opp["cap_source"] = opp["url"]
        opp["cap_basis"] = "figure printed in the announcement text"
        return
    if ic_table:
        # Report the verified spread across participating ICs. Every figure
        # here is still copied from the table; none is chosen for this notice.
        p1s = sorted({v[0] for v in ic_table.values()})
        p2s = sorted({v[1] for v in ic_table.values()})
        opp["cap_phase1"] = "IC-dependent: " + " / ".join(p1s)
        opp["cap_phase2"] = "IC-dependent: " + " / ".join(p2s)
        opp["cap_source"] = table_url
        opp["cap_basis"] = (
            "institute could not be resolved for this notice, so the full "
            "verified spread across all %d participating components is shown "
            "instead of picking one. Confirm the assignment with the program "
            "officer before budgeting." % len(ic_table))
        return
    opp["cap_phase1"] = "NOT VERIFIED"
    opp["cap_phase2"] = "NOT VERIFIED"
    opp["cap_source"] = ""
    opp["cap_basis"] = (
        "the parent announcement's budget table could not be fetched this "
        "run, so no cap was copied from a primary source. Nothing is being "
        "guessed in its place — re-run, or read the cap off the NOFO by hand.")


def read_detail(detail, fallback_url):
    """Return (text, dues, due_source, stage) from a grants.gov detail record,
    whether it is a posted synopsis or a forecast."""
    nofo, nofo_url = fetch_nofo_text(detail)
    syn = detail.get("synopsis") or {}
    if syn:
        text = nofo or _text(syn.get("synopsisDesc") or "")
        text += " " + _text(syn.get("applicantEligibilityDesc") or "")
        dues, src = _dues_from(nofo, syn, nofo_url, fallback_url)
        return text, dues, src, "POSTED", (nofo_url or fallback_url)
    fc = detail.get("forecast") or {}
    if fc:
        text = " ".join(_text(fc.get(k) or "") for k in
                        ("forecastDesc", "applicantEligibilityDesc"))
        iso = _to_iso(fc.get("estApplicationResponseDate") or "")
        return (text, [iso] if iso else [], fallback_url, "FORECAST",
                fallback_url)
    return "", [], "", "UNKNOWN", fallback_url


def _dues_from(nofo_text, syn, nofo_url, fallback_url):
    """grants.gov publishes ONE responseDate per opportunity. For an NIH
    announcement with a standing cycle that field holds the LAST due date —
    Apr 5 2029 on a notice whose next deadline is Sep 5 2026. So the NOFO's
    own Key Dates table wins whenever it can be parsed, and responseDate is
    only the fallback for opportunities with a single real deadline."""
    if nofo_text:
        dues = parse_due_dates(nofo_text)
        if dues:
            return dues, (nofo_url or fallback_url)
    iso = _to_iso((syn or {}).get("responseDate") or "")
    return ([iso] if iso else []), fallback_url


def make_opp(docnum, title, url, text, source, mechanism=None,
             ic_abbrev=None, due_dates=None, parent=None, reldate=None,
             activity=""):
    return {
        "docnum": docnum, "title": title, "url": url, "text": text or "",
        "scope": scope_of(title, text),
        "source": source, "parent": parent, "reldate": reldate,
        "mechanism": mechanism or detect_mechanism(title, docnum, activity),
        "ic_abbrev": ic_abbrev,
        "due_dates": due_dates or [],
        "topic_terms": topic_terms(title),
        "gate_trace": [],
    }


def run_gates(opp, years):
    for gate in GATES:
        ok, name, reason = gate(opp)
        opp["gate_trace"].append((name, "PASS" if ok else "KILL", reason))
        if not ok:
            opp["killed_by"] = name
            opp["kill_reason"] = reason
            return False
    ok, name, reason = gate6_competition(opp, years)
    opp["gate_trace"].append((name, "PASS", reason))
    foreign_screening(opp)
    opp["aims"] = draft_aims(opp)
    # Rank by fit x deadline feasibility, plus a bounded credit for a
    # restricted eligibility field. The credit is additive and small so it can
    # lift a niche row onto the page without ever outranking a real fit.
    niche_credit = 1.5 if opp.get("niches") else 0.0
    opp["rank_score"] = round(
        (opp["fit_score"] + niche_credit) * opp.get("feasibility", 1.0), 2)
    return True


def decide(opp):
    """One go/no-go, one reason. The reason is the single most binding fact,
    not a summary of everything above it."""
    if opp.get("stage") == "FORECAST":
        return "MONITOR-PREPOSITION", (
            "forecast only — NIH has announced its intent but not published "
            "the NOFO, so there is nothing to write against yet. %s Watch for "
            "the NOFO and start the partner conversation now."
            % ((opp["niches"][0][1] + ".") if opp.get("niches")
               else "Track it because the mechanism fits."))
    if opp["deadline_class"] == "NEXT CYCLE":
        return "NO-GO (this cycle)", (
            "only %s days to the next due date; a first STTR needs 90+ to "
            "close an IP allocation agreement with the institution — target "
            "%s instead" % (opp.get("days_left"),
                            opp.get("cycle_target", "the following cycle")))
    if opp["mechanism"] == "SBIR":
        return "NO-GO unless the job search resolves", (
            "SBIR requires Andrew primarily employed by PRG at award; the "
            "work fits but the employment rule does not")
    if opp.get("crowding") == "CROWDED-CAPTURED":
        top = ", ".join(n for n, _ in opp["competition"]["top_firms"])
        return "NO-GO", (
            "%d prior awards with %d%% concentrated in %s — this topic is "
            "captured and a first-time applicant is buying a lottery ticket"
            % (opp["competition"]["n_awards"],
               int(opp["competition"]["concentration"] * 100), top))
    if opp["fit_score"] >= 3.5 and not opp.get("partner_stanford", True):
        return "GO, conditional", (
            "fit is real but the partner department is outside Dept of "
            "Medicine — GO only once %s confirms a PI in writing"
            % (opp.get("partner_dept") or "the host department"))
    if opp["fit_score"] >= 3.5:
        return "GO", (
            "fit %.1f/5 on site-level trial operations, %s prior-award field, "
            "and a Dept of Medicine PI is a warm ask"
            % (opp["fit_score"], opp.get("crowding", "unknown").lower()))
    if opp.get("niche_only"):
        return "GO on eligibility, not on fit", (
            "capability fit is only %.1f/5, but %s — a thin field is worth "
            "more to a first-time applicant than a strong topic in a crowded "
            "one" % (opp["fit_score"], opp["niches"][0][1]))
    return "GO, low priority", (
        "fit %.1f/5 clears the gate but does not lead with the one thing PRG "
        "has that others do not" % opp["fit_score"])


# ---------------------------------------------------------------------------
# SEEN-LIST — repeat runs surface only what is NEW or CHANGED. Changed means
# the primary source changed, not that our scoring drifted, so the hash
# covers title + due dates + the announcement text.
# ---------------------------------------------------------------------------

def load_json(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (IOError, ValueError):
        return default


def save_json(path, obj):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
    os.rename(tmp, path)


def content_hash(opp):
    blob = "|".join([opp["title"] or "", ",".join(opp.get("due_dates") or []),
                     hashlib.sha256((opp["text"] or "").encode(
                         "utf-8", "replace")).hexdigest()])
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()[:16]


def classify_novelty(opp, seen):
    prior = seen.get(opp["docnum"])
    h = content_hash(opp)
    if prior is None:
        opp["novelty"] = "NEW"
    elif prior.get("hash") != h:
        opp["novelty"] = "CHANGED"
        opp["prior_seen"] = prior.get("first_seen")
    else:
        opp["novelty"] = "UNCHANGED"
        opp["prior_seen"] = prior.get("first_seen")
    opp["hash"] = h
    return opp["novelty"]


def update_seen(seen, opps):
    stamp = TODAY.isoformat()
    for o in opps:
        prior = seen.get(o["docnum"]) or {}
        seen[o["docnum"]] = {
            "hash": o["hash"],
            "title": o["title"][:200],
            "first_seen": prior.get("first_seen", stamp),
            "last_seen": stamp,
            "last_verdict": o.get("verdict", ""),
            "killed_by": o.get("killed_by", ""),
            "fit_score": o.get("fit_score"),
        }
    return seen


# ---------------------------------------------------------------------------
# DIGEST
# ---------------------------------------------------------------------------

def money(s):
    return s if s else "NOT VERIFIED"


def render_digest(survivors, killed, weekly, run_meta):
    L = []
    A = L.append
    A("# PRG SBIR/STTR digest — %s" % TODAY.isoformat())
    A("")
    A("Pipeline `sbir_sttr_pipeline.py` (sbir-v1). Gate doc: `sbir/GATE.md`.")
    A("Default mechanism is **STTR** — Andrew is job searching, so the SBIR")
    A("primarily-employed rule cannot be satisfied. SBIR appears only where")
    A("the work is solo-operator-shaped, and always flagged as a conflict.")
    A("")

    # --- Source health FIRST. A hole in the sweep is a headline, not a footnote.
    A("## Source health — read this before the ranking")
    A("")
    A("| Source | Status | Detail |")
    A("| --- | --- | --- |")
    for key, row in LOG.rows.items():
        A("| %s | **%s** | %s |" % (key, row["status"],
                                    row["detail"].replace("|", "/")))
    A("")
    holes = LOG.holes()
    if holes:
        A("> **This sweep is incomplete.** %d source(s) did not return data: "
          "%s. Anything that exists only there was not screened. Do not read "
          "the ranking below as cross-agency coverage."
          % (len(holes), ", ".join(holes)))
    else:
        A("> All documented sources returned data this run.")
    A("")

    A("## Ranked shortlist — %d of %d survivor(s)"
      % (min(len(survivors), DIGEST_CAP), len(survivors)))
    A("")
    if not survivors:
        A("Nothing cleared all six gates this run. The kill ledger below says")
        A("which gate fired on each candidate — that is the finding, not an")
        A("empty result.")
        A("")
    for i, o in enumerate(survivors[:DIGEST_CAP], 1):
        A("### %d. %s — %s" % (i, o["docnum"], o["title"]))
        A("")
        A("- **Verified against**: %s" % (o["url"] or "n/a"))
        A("- **Mechanism**: %s | **Agency**: NIH | **Institute**: %s | "
          "**Stage**: %s"
          % (o["mechanism"], o.get("ic_abbrev") or "not resolved",
             o.get("stage", "POSTED")))
        if o.get("stage") == "FORECAST":
            A("  - forecast: NIH has stated intent to publish; the NOFO does "
              "not exist yet, so the date below is NIH's estimate, not a "
              "published deadline")
        for term, why in (o.get("niches") or []):
            A("- **Restricted eligibility field** (\"%s\"): %s" % (term, why))
        if o.get("parent"):
            A("- **Parent announcement**: %s" % o["parent"])
        A("- **Next due date**: %s (%s day(s) out) — %s"
          % (o.get("next_due", "none published"),
             o.get("days_left", "n/a"), o["deadline_class"]))
        if o.get("due_source"):
            A("  - due date read from: %s" % o["due_source"])
        if len(o.get("due_dates") or []) > 1:
            A("  - full published cycle: %s"
              % ", ".join((o.get("due_dates") or [])[:4]))
        A("- **Phase I cap**: %s | **Phase II cap**: %s"
          % (money(o.get("cap_phase1")), money(o.get("cap_phase2"))))
        A("  - source: %s" % (o.get("cap_source") or o.get("cap_basis")))
        if o.get("cap_source"):
            A("  - basis: %s" % o.get("cap_basis"))
        A("- **Fit**: %.1f/5 — %s" % (o["fit_score"], o.get("fit_line", "")))
        A("- **Partner**: %s" % o.get("partner_dept"))
        A("  - Stanford Dept of Medicine credible: **%s** — %s"
          % ("YES" if o.get("partner_stanford") else "NO", o.get("partner_why")))
        A("- **PI rule**: %s" % o.get("pi_note", ""))
        A("")
        A("**Three candidate specific aims:**")
        A("")
        for j, aim in enumerate(o.get("aims") or [], 1):
            A("%d. %s" % (j, aim))
        A("")
        comp = o.get("competition") or {}
        if comp.get("error"):
            A("- **Prior-award landscape**: UNAVAILABLE — RePORTER returned "
              "%s. Crowding untested." % comp["error"])
        else:
            firms = ", ".join("%s (%d)" % (n, c) for n, c in comp.get("top_firms") or []) or "none"
            pos = ", ".join("%s (%d)" % (n, c) for n, c in comp.get("program_officers") or []) or "none named"
            A("- **Prior-award landscape**: %d distinct %s project(s) %s "
              "(%d project-year rows), %s. Top firms: %s. "
              "Top-3 concentration %d%%."
              % (comp.get("n_awards", 0), o["mechanism"], comp.get("years", ""),
                 comp.get("n_rows", 0),
                 o.get("crowding", ""), firms,
                 int(comp.get("concentration", 0) * 100)))
            A("- **Program officer(s)**: %s" % pos)
            A("  - reproduce: %s" % comp.get("reporter_url", ""))
        if o.get("foreign_flags"):
            A("- **FOREIGN-AFFILIATION SCREENING**: this announcement carries "
              "foreign-review language (%s). The 2026 reauthorization expanded "
              "that review; budget disclosure time even though PRG is clean."
              % ", ".join(o["foreign_flags"][:4]))
        A("- **Novelty**: %s%s" % (o["novelty"],
                                   (" (first seen %s)" % o["prior_seen"])
                                   if o.get("prior_seen") else ""))
        A("")
        A("> **%s** — %s" % (o["verdict"], o["verdict_reason"]))
        A("")

    A("## Kill ledger — %d candidate(s) screened out" % len(killed))
    A("")
    A("| Doc | Gate | Reason |")
    A("| --- | --- | --- |")
    for o in killed[:60]:
        A("| %s | %s | %s |" % (o["docnum"], o.get("killed_by", "?"),
                                (o.get("kill_reason") or "").replace("|", "/")[:150]))
    if len(killed) > 60:
        A("")
        A("_%d further kills omitted from the table; all are in "
          "`sbir/state/seen.json`._" % (len(killed) - 60))
    A("")

    if weekly:
        A("## NIH Guide — posted this week (unfiltered, for eyeball)")
        A("")
        for w in weekly[:12]:
            A("- [%s](%s)" % (w["title"][:130], w["link"]))
        A("")

    A("## Run metadata")
    A("")
    for k, v in run_meta.items():
        A("- **%s**: %s" % (k, v))
    A("")
    A("---")
    A("")
    A("_Every announcement number, due date, and budget cap above was copied "
      "from a primary source fetched during this run, and the URL it came "
      "from is printed beside it. Anything the run could not verify says "
      "NOT VERIFIED rather than carrying a guess._")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# DISCOVERY
# ---------------------------------------------------------------------------

# Queries are aimed at PRG's lane, not at "SBIR". Finding the omnibus parents
# is not the task; finding what an institute actually wants to fund is.
GUIDE_QUERIES = [
    "STTR clinical trial", "SBIR clinical trial operations",
    "small business decentralized clinical trial",
    "small business clinical research recruitment retention",
    "small business clinical data quality",
    "small business health informatics interoperability",
    "small business digital health implementation",
    "small business medical device clinical workflow",
]
GRANTS_QUERIES = ["STTR", "SBIR clinical", "small business technology transfer"]
# Broad, deliberately un-targeted queries whose only job is to give the
# IC-code harvester a wide sample of docnum/primaryIC pairs to learn from.
HARVEST_QUERIES = ["notice of special interest", "small business",
                   "clinical trial"]
PARENTS = ("PA-27-102", "PA-27-100")
CACHE_TTL_DAYS = 7

# Populated at runtime by derive_omnibus() from the parents' own "Companion
# Funding Opportunity" block. Starts as the two parents so a failed fetch
# degrades to "kill less", never to "kill the wrong thing".
OMNIBUS = set(PARENTS)


def derive_omnibus(parents):
    """Read the companion FONs out of the parent announcements themselves.
    On PA-27-102 that block names PA-27-100, PA-27-101 and PAR-27-098 — the
    four documents that together ARE the omnibus. Everything else with a
    small-business activity code is a real, competed opportunity."""
    found = set(PARENTS)
    for fon, p in (parents or {}).items():
        found.add(fon.upper())
        m = re.search(r"Companion Funding Opportunit(?:y|ies)(.{0,600})",
                      p.get("text") or "", re.S | re.I)
        if not m:
            continue
        for num in re.findall(r"\b(?:PA|PAR|RFA)-\d{2}-\d{3,4}\b", m.group(1)):
            found.add(num.upper())
    return found


def load_parent_context(force=False):
    """Fetch the two omnibus parents, parse their IC budget tables and due
    dates. This is what lets every downstream cap cite a URL."""
    cache = load_json(CACHE_PATH, {})
    fresh = cache.get("fetched")
    if fresh and not force:
        age = (TODAY - dt.date.fromisoformat(fresh)).days
        if age <= CACHE_TTL_DAYS and cache.get("parents"):
            LOG.record("Parent NOFO cache", "OK",
                       "IC budget table reused from cache fetched %s (%d day(s) "
                       "old, TTL %d)" % (fresh, age, CACHE_TTL_DAYS),
                       cache.get("parents", {}).get(PARENTS[0], {}).get("nofo_url", ""))
            return cache["parents"]

    parents = {}
    for fon in PARENTS:
        try:
            data = (_http("POST", GRANTS_SEARCH,
                          json={"oppNum": fon, "rows": 5,
                                "oppStatuses": "posted|forecasted"}).json()
                    or {}).get("data") or {}
        except (requests.RequestException, ValueError) as exc:
            LOG.fail("Parent NOFO %s" % fon, _detail(exc), GRANTS_SEARCH)
            continue
        hits = [h for h in (data.get("oppHits") or [])
                if (h.get("number") or "").upper() == fon]
        if not hits:
            LOG.fail("Parent NOFO %s" % fon,
                     "not found on grants.gov — the FON may have been reissued; "
                     "budget caps CANNOT be verified this run", GRANTS_SEARCH)
            continue
        hit = hits[0]
        detail = fetch_grants_detail(hit["id"])
        if not detail:
            LOG.fail("Parent NOFO %s" % fon, "fetchOpportunity failed",
                     GRANTS_FETCH)
            continue
        nofo_text, nofo_url = fetch_nofo_text(detail)
        if not nofo_text:
            LOG.fail("Parent NOFO %s" % fon,
                     "full-announcement attachment unavailable — IC budget "
                     "caps CANNOT be verified this run", GRANTS_DETAIL.format(hit["id"]))
            continue
        raw_html = ""
        for folder in (detail.get("synopsisAttachmentFolders") or []):
            for att in (folder.get("synopsisAttachments") or []):
                if (att.get("fileName") or "").lower().endswith((".html", ".htm")):
                    try:
                        raw_html = _http("GET", GRANTS_ATT.format(att["id"])).text
                    except requests.RequestException:
                        raw_html = ""
        table = parse_ic_budget_table(raw_html) if raw_html else {}
        dues = parse_due_dates(nofo_text)
        parents[fon] = {
            "title": hit.get("title") or "",
            "grants_id": hit.get("id"),
            "grants_url": GRANTS_DETAIL.format(hit["id"]),
            "nofo_url": nofo_url,
            "close_date": hit.get("closeDate") or "",
            "due_dates": dues,
            "ic_table": [[k, list(v)] for k, v in table.items()],
            # Only the head is kept: it carries the Companion Funding
            # Opportunity block that derive_omnibus() reads. Caching the whole
            # 400KB announcement made the state file 200KB for no benefit.
            "text": nofo_text[:8000],
        }
        LOG.ok("Parent NOFO %s" % fon, 1, nofo_url,
               "%d IC budget row(s), %d future due date(s) parsed from the "
               "announcement itself" % (len(table), len(dues)))
    if parents:
        cache["fetched"] = TODAY.isoformat()
        cache["parents"] = parents
        save_json(CACHE_PATH, cache)
    return parents


# Administrative notices are not opportunities. NIH publishes far more
# rescissions, corrections, participation changes and webinar announcements
# than actual small-business topics, and gating them wastes a fetch and puts
# noise in the ledger. A literal list kept missing variants ("Notice of
# Change:" vs "Notice of Change to"), so this matches the shape instead.
ADMIN_NOTICE_RE = re.compile(
    r"^\s*(?:rescinded\b"
    r"|notice\s+(?:of|to)\s+(?:rescind|change|correction|clarification"
    r"|information|intent\s+to\s+publish|participation|removal|withdrawal"
    r"|expiration|early\s+expiration|availability|legacy|extend|correct"
    r"|pre-?application\s+webinar|informational\s+webinar"
    r"|technical\s+assistance\s+webinar)"
    r"|request\s+for\s+(?:comment|information)\b)", re.I)


def is_admin_notice(title):
    title = (title or "").strip()
    if ADMIN_NOTICE_RE.match(title):
        return True
    # "Notice of ... Webinar" in any word order is still an announcement about
    # an announcement.
    return bool(re.match(r"^\s*notice\b", title, re.I)
                and re.search(r"\bwebinar\b", title, re.I))


def _guide_relevant(src):
    blob = " ".join(str(src.get(k) or "") for k in
                    ("title", "ac", "docnum", "parentFOA"))
    if not re.search(r"\b(R4[1234])\b|SBIR|STTR|small business", blob, re.I):
        return False
    exp = src.get("expdate")
    if exp and exp[:10] < TODAY.isoformat():
        return False
    rel = (src.get("reldate") or "")[:10]
    if rel and rel < (TODAY - dt.timedelta(days=900)).isoformat():
        return False
    return True


def discover(parents, code_map):
    """Assemble candidates from every reachable source."""
    global OMNIBUS
    OMNIBUS = derive_omnibus(parents)
    LOG.record("Omnibus exclusion set", "OK",
               "%s — derived from the parents' own Companion Funding "
               "Opportunity block, not from titles" % ", ".join(sorted(OMNIBUS)),
               (parents.get("PA-27-102") or {}).get("nofo_url", ""))
    cands = OrderedDict()

    harvest = fetch_nih_guide(HARVEST_QUERIES, label="IC-code harvest")
    code_map = harvest_ic_codes(list(harvest.values()), code_map)
    LOG.record("IC-code map", "OK",
               "%d two-letter IC code(s) resolved from the NIH Guide index "
               "itself (accumulated across runs); unresolved codes yield a "
               "cap RANGE, never a guessed institute" % len(code_map),
               NIH_GUIDE_API)

    guide = fetch_nih_guide(GUIDE_QUERIES)
    for docnum, src in harvest.items():
        guide.setdefault(docnum, src)
    admin = []
    for docnum, src in guide.items():
        if not _guide_relevant(src):
            continue
        if docnum.upper() in OMNIBUS:
            continue                       # omnibus parents are not the task
        if is_admin_notice(src.get("title")):
            admin.append("%s (%s)" % (docnum, (src.get("title") or "")[:60]))
            continue
        cands[docnum] = {"kind": "nih-guide", "src": src}
    if admin:
        LOG.record("Administrative notices", "OK",
                   "%d SBIR/STTR notice(s) were policy, rescission, "
                   "correction or webinar announcements rather than funding "
                   "opportunities, and were not gated: %s"
                   % (len(admin), "; ".join(admin[:5])), NIH_GUIDE_API)

    gg = fetch_grants_gov(GRANTS_QUERIES)
    for oid, hit in gg.items():
        num = (hit.get("number") or "").upper()
        if not num or num in OMNIBUS or num in cands:
            continue
        if not re.search(r"SBIR|STTR|small business", 
                         "%s %s" % (hit.get("title"), num), re.I):
            continue
        cands[num] = {"kind": "grants.gov", "src": hit, "grants_id": oid}

    weekly = fetch_nih_rss()
    for item in weekly:
        m = re.search(r"(NOT|PA|PAR|RFA)-[A-Z]{2}-\d{2}-\d{3,4}", item["link"],
                      re.I)
        if not m:
            continue
        num = m.group(0).upper()
        if num in cands or num in OMNIBUS:
            continue
        if not re.search(r"SBIR|STTR|small business", item["title"], re.I):
            continue
        cands[num] = {"kind": "nih-rss", "src": item}

    probe_sbir_gov()
    probe_dsip()
    probe_simpler(GRANTS_QUERIES)
    probe_sam()
    return cands, weekly, code_map


def hydrate(docnum, entry, parents, code_map=None):
    """Pull the candidate's own text from a primary source and build the opp.
    An opportunity whose text cannot be fetched is NOT scored — it is reported
    as unverifiable, because scoring it would mean guessing."""
    kind = entry["kind"]
    src = entry["src"]
    text, url, title, dues, ic, parent = "", "", "", [], None, None
    due_src, stage = "", "POSTED"

    if kind == "nih-guide":
        title = src.get("title") or ""
        ic = detect_ic(docnum, src.get("primaryIC") or "", code_map)
        parent = src.get("parentFOA") or None
        url = NIH_NOTICE.format(docnum) if docnum.upper().startswith("NOT") else ""
        if url:
            text = fetch_notice_text(docnum)
    elif kind == "nih-rss":
        title = src.get("title") or ""
        url = (src.get("link") or "").replace("http://", "https://")
        text = fetch_notice_text(docnum)
    else:
        title = src.get("title") or ""
        url = GRANTS_DETAIL.format(entry["grants_id"])
        detail = fetch_grants_detail(entry["grants_id"])
        if detail:
            text, dues, due_src, stage, url = read_detail(detail, url)

    if not text:
        # Fall back to grants.gov by announcement number before giving up.
        try:
            data = (_http("POST", GRANTS_SEARCH,
                          json={"oppNum": docnum, "rows": 3,
                                "oppStatuses": "posted|forecasted"}).json()
                    or {}).get("data") or {}
            for h in (data.get("oppHits") or []):
                detail = fetch_grants_detail(h["id"])
                if not detail:
                    continue
                text, dues, due_src, stage, url = read_detail(
                    detail, GRANTS_DETAIL.format(h["id"]))
                break
        except (requests.RequestException, ValueError):
            pass

    if not text:
        return None

    blob = title + " " + text
    opp = make_opp(docnum, title, url, blob, kind,
                   mechanism=detect_mechanism(blob, docnum),
                   ic_abbrev=ic or detect_ic(docnum, "", code_map),
                   due_dates=dues, parent=parent, activity=(
                       src.get("ac") if isinstance(src, dict) else ""),
                   reldate=(src.get("reldate") or "")[:10] if isinstance(src, dict) else "")
    opp["due_source"] = due_src
    opp["stage"] = stage

    # A NOSI has no due dates of its own; it inherits the parent's cycle.
    if not opp["due_dates"]:
        pfon = (parent or "").upper()
        pdata = parents.get(pfon) or parents.get(
            "PA-27-102" if opp["mechanism"] == "STTR" else "PA-27-100")
        if pdata:
            opp["due_dates"] = pdata.get("due_dates") or []
            opp["parent"] = opp["parent"] or (
                pfon or ("PA-27-102" if opp["mechanism"] == "STTR"
                         else "PA-27-100"))
            opp["due_source"] = pdata.get("nofo_url")
    return opp


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def fit_line(opp):
    ev = opp.get("fit_evidence") or []
    a = [e[2:] for e in ev if e.startswith("A:")]
    if a:
        return ("asks for site-level trial-operations knowledge (%s), which is "
                "exactly the five years at Stanford Dept of Medicine"
                % ", ".join(a[:3]))
    b = [e[2:] for e in ev if e.startswith("B:")]
    if b:
        return ("adjacent capability (%s) — real, but not the thing PRG has "
                "that others do not" % ", ".join(b[:3]))
    return "clears the bar on general health-research literacy only"


def cmd_ic_table(args):
    parents = load_parent_context(force=args.refresh)
    for fon in PARENTS:
        p = parents.get(fon)
        print("\n=== %s — %s" % (fon, (p or {}).get("title", "NOT FETCHED")))
        if not p:
            print("    NOT VERIFIED this run; see source health above.")
            continue
        print("    verified from: %s" % p["nofo_url"])
        print("    due dates parsed from the NOFO: %s"
              % (", ".join(p["due_dates"]) or "none"))
        g1, g2, gnote = sba_guideline()
        print("    SBA budgetary guideline: %s Phase I / %s Phase II (%s)"
              % (g1, g2, gnote))
        print("    %-72s %-24s %s" % ("IC", "Phase I", "Phase II"))
        for name, (p1, p2) in as_ic_table(p["ic_table"]).items():
            print("    %-72s %-24s %s" % (name[:72],
                                          expand_cap(p1, g1, g2, 1),
                                          expand_cap(p2, g1, g2, 2)))
    for key, row in LOG.rows.items():
        print("[%s] %s — %s" % (row["status"], key, row["detail"]))
    return 0


def cmd_explain(args):
    parents = load_parent_context()
    code_map = (load_json(CACHE_PATH, {}) or {}).get("ic_codes") or {}
    cands, _, code_map = discover(parents, code_map)
    OMNIBUS.discard(args.explain.upper())   # --explain overrides the exclusion
    target = args.explain.upper()
    entry = cands.get(target)
    if entry is None:
        entry = {"kind": "grants.gov-lookup", "src": {"title": target},
                 "grants_id": None}
        opp = hydrate(target, {"kind": "nih-guide", "src": {"title": target}},
                      parents, code_map)
    else:
        opp = hydrate(target, entry, parents, code_map)
    if opp is None:
        print("Could not fetch a primary source for %s. Not scored." % target)
        return 1
    ic_table, table_url = _table_for(opp, parents)
    resolve_caps(opp, ic_table, table_url)
    survived = run_gates(opp, _years())
    print("%s — %s" % (opp["docnum"], opp["title"]))
    print("source: %s" % opp["url"])
    print("mechanism: %s | IC: %s | caps: %s / %s (%s)"
          % (opp["mechanism"], opp.get("ic_abbrev"), opp.get("cap_phase1"),
             opp.get("cap_phase2"), opp.get("cap_basis")))
    for name, state, reason in opp["gate_trace"]:
        print("  %-3s %-4s %s" % (name, state, reason))
    if survived:
        v, r = decide(opp)
        print("  => %s — %s" % (v, r))
    return 0


SELFTESTS = [
    # (label, callable) -> raises AssertionError on failure
    ("word-boundary matching does not fire inside longer words",
     lambda: _hits("a grave and lasting concern", FIT_TIER_A) == []),
    ("word-boundary matching still catches real short tokens",
     lambda: set(_hits("we ran Medidata Rave as the EDC", FIT_TIER_A))
     >= {"rave", "edc", "medidata"}),
    ("deliberately truncated stems still match",
     lambda: _hits("immunohistochemistry panels", KILL_WET_LAB)
     == ["immunohistochem"]),
    ("mechanism reads the title, never the body",
     lambda: detect_mechanism(
         "NIH SBIR Phase IIB (R44)", "PA-27-101",
         "") == "SBIR"),
    ("a dual notice is classified dual, not silently STTR",
     lambda: detect_mechanism("SBIR/STTR Commercialization", "PAR-27-098")
     == "SBIR/STTR"),
    ("administrative notices are not opportunities",
     lambda: is_admin_notice("Notice of Change: NINDS Participation")
     and is_admin_notice("Notice of Pre-Application Webinar for X")
     and not is_admin_notice("Notice of Special Interest (NOSI): Trials")),
    ("SBIR dies at gate 2 while the job search is live",
     lambda: gate2_mechanism({"mechanism": "SBIR", "text": "gene therapy "
                              "manufacturing", "scope": "gene therapy "
                              "manufacturing", "title": ""})[0] is False),
    ("STTR passes gate 2 because the PI may sit at the institution",
     lambda: gate2_mechanism({"mechanism": "STTR", "text": "", "scope": "",
                              "title": ""})[0] is True),
    ("a bench-dominant scope dies at gate 1",
     lambda: gate1_eligibility(_probe(
         "murine model organoid cell culture in vitro assay animal study"))[0]
     is False),
    ("an eligibility niche survives a low fit score",
     lambda: gate3_capability(_probe(
         "applicants whose PD/PI has never been an independent PD/PI"))[0]
     is True),
    ("a plain low-fit scope still dies at gate 3",
     lambda: gate3_capability(_probe("advanced polymer coating chemistry"))[0]
     is False),
    ("the parent's own companion block defines the omnibus set",
     lambda: derive_omnibus({"PA-27-102": {"text":
         "Companion Funding Opportunity PA-27-100 , R43 / R44 ... "
         "PA-27-101 , R44 ... PAR-27-098 , SB1 Commercialization"}})
     == {"PA-27-100", "PA-27-101", "PA-27-102", "PAR-27-098"}),
    ("grants.gov responseDate never overrides the NOFO's own cycle table",
     lambda: _dues_from(
         "Application Due Dates September 05, 2026 * January 05, 2027 * "
         "All applications are due by 5:00 PM",
         {"responseDate": "Apr 05, 2029 12:00:00 AM EDT"}, "N", "F")[0][0]
     == "2026-09-05"),
    ("responseDate is still the fallback when there is no cycle table",
     lambda: _dues_from("", {"responseDate": "Jan 05, 2027 12:00:00 AM EST"},
                        "", "F")[0] == ["2027-01-05"]),
    ("an unresolved IC yields a verified range, never a guessed institute",
     lambda: _capless()),
]


def _probe(scope):
    return {"docnum": "NOT-XX-99-999", "title": "probe", "text": scope,
            "scope": scope, "mechanism": "STTR"}


def _capless():
    o = _probe("x")
    o["ic_abbrev"] = None
    resolve_caps(o, {"National Cancer Institute": ("$700,000.00", "$2,500,000.00"),
                     "National Eye Institute": ("$400,000.00", "SBA Guideline")},
                 "http://example/table")
    return ("IC-dependent" in o["cap_phase1"]
            and o["cap_source"] == "http://example/table")


# ---------------------------------------------------------------------------
# INSTITUTE SCAN — "which institute should PRG aim at?" Ranks every
# participating component of a parent announcement by verified budget cap and
# by how crowded and how PRG-shaped its actual STTR portfolio is.
# ---------------------------------------------------------------------------

# "PRG's lane" is not defined twice. The scan classifies each award with the
# SAME fit vocabulary Gate 3 scores against, so the two can never drift apart
# — if a term is added to FIT_TIER_A, the institute scan starts counting it.
#
# RePORTER's advanced_text_search is not used for this. operator="and" on a
# six-word phrase matches nothing (0 of NCI's 250 STTR awards); operator="or"
# matches almost everything (240 of 250). Neither number means anything. So
# the portfolio is pulled once per IC and classified here.
LANE_TIERS = OrderedDict([
    ("trial-ops", FIT_TIER_A),
    ("data/informatics", FIT_TIER_B),
    ("care-delivery", FIT_TIER_C),
])


# RePORTER returns one row per project-YEAR: a Phase I, its Phase II, and each
# non-competing continuation are separate rows with the same core number
# (1R42AG094389-01, 5R42AG094389-02, ...). Counting those as separate awards
# inflates a 40-project institute into 180 and makes every crowding read wrong.
CORE_NUM = re.compile(r"[A-Z]?\d?([A-Z]\d{2}[A-Z]{2}\d{6})")


def core_project(num):
    m = CORE_NUM.search((num or "").upper())
    return m.group(1) if m else (num or "")


def dedupe_projects(results):
    """One row per distinct project, keeping the largest award seen."""
    best = OrderedDict()
    for r in results:
        key = core_project(r.get("project_num"))
        cur = best.get(key)
        if cur is None or (r.get("award_amount") or 0) > (cur.get("award_amount") or 0):
            best[key] = r
    return list(best.values())


def classify_lane(title):
    """Return the highest-tier lane this award title falls in, or None."""
    low = (title or "").lower()
    for lane, vocab in LANE_TIERS.items():
        if any(_term_re(t).search(low) for t in vocab):
            return lane
    return None


def _reporter_all(terms, codes, years, ic, cap=2000):
    """Page RePORTER past its 500-record response limit."""
    out, offset = [], 0
    while offset < cap:
        crit = {"fiscal_years": list(years), "activity_codes": list(codes),
                "agencies": [ic]}
        if terms:
            crit["advanced_text_search"] = {
                "operator": "and",
                "search_field": "projecttitle,abstracttext,terms",
                "search_text": terms}
        body = {"criteria": crit, "include_fields": [
            "ProjectNum", "ProjectTitle", "AwardAmount", "Organization",
            "ProgramOfficers", "FiscalYear"], "limit": 500, "offset": offset}
        try:
            batch = (_http("POST", REPORTER, json=body).json()
                     or {}).get("results") or []
        except (requests.RequestException, ValueError) as exc:
            return out, _detail(exc)
        out.extend(batch)
        if len(batch) < 500:
            break
        offset += 500
        time.sleep(0.4)
    return out, None


def cmd_institute_scan(args):
    parents = load_parent_context(force=args.refresh)
    fon = (args.institute_scan or "PA-27-102").upper()
    p = parents.get(fon)
    if not p or not p.get("ic_table"):
        print("Could not verify %s or its IC budget table this run. Nothing "
              "is being estimated in its place." % fon)
        for key, row in LOG.rows.items():
            print("  [%s] %s — %s" % (row["status"], key, row["detail"]))
        return 1
    codes = list(STTR_CODES) if "102" in fon else list(SBIR_CODES)
    years = list(range(TODAY.year - 5, TODAY.year + 1))
    g1, g2, gnote = sba_guideline()
    rows = []
    for full, (raw_p1, raw_p2) in as_ic_table(p["ic_table"]).items():
        p1 = expand_cap(raw_p1, g1, g2, 1)
        p2 = expand_cap(raw_p2, g1, g2, 2)
        ab = IC_ABBREV.get(full)
        if not ab:
            continue
        raw, err = _reporter_all("", codes, years, ab)
        awards = dedupe_projects(raw)
        if err:
            rows.append({"ic": ab, "full": full, "p1": p1, "p2": p2,
                         "error": err})
            continue
        orgs, lanes, lane_pos, lane_firms = Counter(), Counter(), Counter(), Counter()
        for r in awards:
            nm = ((r.get("organization") or {}).get("org_name") or "").title()
            if nm:
                orgs[nm] += 1
            lane = classify_lane(r.get("project_title"))
            if not lane:
                continue
            lanes[lane] += 1
            if nm:
                lane_firms[nm] += 1
            for po in (r.get("program_officers") or []):
                who = re.sub(r"\s+", " ",
                             (po.get("full_name") or "")).strip().title()
                if who:
                    lane_pos[who] += 1
        top = orgs.most_common(3)
        conc = (sum(n for _, n in top) / float(len(awards))) if awards else 0.0
        lane_total = sum(lanes.values())
        rows.append({
            "ic": ab, "full": full, "p1": p1, "p2": p2, "n": len(awards),
            "n_rows": len(raw),
            "top": top, "conc": conc, "lanes": lanes, "lane_total": lane_total,
            "lane_share": (lane_total / float(len(awards))) if awards else 0.0,
            "pos": lane_pos.most_common(3),
            "lane_firms": lane_firms.most_common(3),
            "unique_firms": len(orgs),
            "cap1_num": _cap_num(p1),
        })
        time.sleep(0.25)

    print("# Institute scan — %s" % fon)
    print("# %s" % p["title"])
    print("# Caps verified from the announcement's own budget table: %s"
          % p["nofo_url"])
    print("# Portfolio: NIH RePORTER v2, activity %s, FY%d-FY%d, one query "
          "per participating component." % ("/".join(codes), min(years),
                                            max(years)))
    print("# Lane = the award title matches the same capability vocabulary "
          "Gate 3 scores against.")
    print("# SBA budgetary guideline: %s Phase I / %s Phase II (%s)"
          % (g1, g2, gnote))
    print()
    hdr = ("%-7s %-26s %-26s %7s %6s %6s %6s %7s  %s"
           % ("IC", "Phase I", "Phase II", "projs", "firms", "top3%",
              "lane", "lane%", "ops/data/care"))
    print(hdr)
    print("-" * len(hdr))
    ranked = sorted(rows, key=lambda x: (-(x.get("lane_total") or 0),
                                         -(x.get("cap1_num") or 0)))
    for r in ranked:
        if r.get("error"):
            print("%-7s %-26s %-26s   RePORTER FAILED: %s"
                  % (r["ic"], r["p1"], r["p2"], r["error"]))
            continue
        L = r["lanes"]
        print("%-7s %-26s %-26s %7d %6d %5d%% %6d %6d%%  %d/%d/%d"
              % (r["ic"], r["p1"], r["p2"], r["n"], r["unique_firms"],
                 int(r["conc"] * 100), r["lane_total"],
                 int(r["lane_share"] * 100), L["trial-ops"],
                 L["data/informatics"], L["care-delivery"]))
    print()
    print("Top of the ranking, in detail:")
    for r in ranked[:6]:
        if r.get("error") or not r.get("lane_total"):
            continue
        print()
        print("%s (%s) — Phase I %s / Phase II %s" % (r["ic"], r["full"],
                                                      r["p1"], r["p2"]))
        print("   portfolio : %d distinct STTR project(s) (%d RePORTER "
              "project-year rows) across %d firm(s); top three hold %d%%"
              % (r["n"], r["n_rows"], r["unique_firms"], int(r["conc"] * 100)))
        print("   in lane   : %d (%d%% of the portfolio) — %s"
              % (r["lane_total"], int(r["lane_share"] * 100),
                 ", ".join("%s %d" % (k, v) for k, v in r["lanes"].items())))
        print("   lane firms: %s" % (", ".join("%s (%d)" % (n, c)
                                     for n, c in r["lane_firms"]) or "none"))
        print("   lane PO(s): %s" % (", ".join("%s (%d)" % (n, c)
                                     for n, c in r["pos"]) or "none named"))
    print()
    for key, row in LOG.rows.items():
        if row["status"] != "OK":
            print("[%s] %s — %s" % (row["status"], key, row["detail"]))
    return 0


def _cap_num(cap):
    m = re.search(r"[\d,]{6,}", cap or "")
    return int(m.group(0).replace(",", "")) if m else 0


def cmd_selftest():
    bad = 0
    for label, fn in SELFTESTS:
        try:
            ok = bool(fn())
        except Exception as exc:                       # noqa: BLE001
            ok, label = False, "%s [raised %s]" % (label, exc)
        print("%-5s %s" % ("ok" if ok else "FAIL", label))
        bad += 0 if ok else 1
    print("\n%d/%d passed" % (len(SELFTESTS) - bad, len(SELFTESTS)))
    return 1 if bad else 0


def _years():
    y = TODAY.year
    return list(range(y - 5, y + 1))


def _table_for(opp, parents):
    fon = "PA-27-102" if opp["mechanism"] == "STTR" else "PA-27-100"
    p = parents.get(fon) or {}
    return as_ic_table(p.get("ic_table")), p.get("nofo_url", "")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the digest, do not write it or the seen-list")
    ap.add_argument("--all", action="store_true",
                    help="ignore the seen-list; surface unchanged items too")
    ap.add_argument("--ic-table", action="store_true",
                    help="print the verified IC budget caps and exit")
    ap.add_argument("--explain", metavar="FON",
                    help="print the full gate trace for one announcement")
    ap.add_argument("--refresh", action="store_true",
                    help="bypass the parent-NOFO cache")
    ap.add_argument("--out", help="digest path (default sbir/reports/)")
    ap.add_argument("--institute-scan", nargs="?", const="PA-27-102",
                    metavar="FON",
                    help="rank a parent announcement's participating "
                         "institutes by verified cap and prior-award crowding")
    ap.add_argument("--selftest", action="store_true",
                    help="run the offline gate assertions and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return cmd_selftest()
    if args.institute_scan:
        return cmd_institute_scan(args)
    if args.ic_table:
        return cmd_ic_table(args)
    if args.explain:
        return cmd_explain(args)

    started = dt.datetime.now()
    parents = load_parent_context(force=args.refresh)
    cache = load_json(CACHE_PATH, {})
    cands, weekly, code_map = discover(parents, cache.get("ic_codes") or {})
    cache["ic_codes"] = code_map
    save_json(CACHE_PATH, cache)
    seen = load_json(SEEN_PATH, {})
    years = _years()

    survivors, killed, unverifiable = [], [], []
    for docnum, entry in cands.items():
        opp = hydrate(docnum, entry, parents, code_map)
        if opp is None:
            unverifiable.append(docnum)
            continue
        ic_table, table_url = _table_for(opp, parents)
        resolve_caps(opp, ic_table, table_url)
        classify_novelty(opp, seen)
        if run_gates(opp, years):
            opp["fit_line"] = fit_line(opp)
            opp["verdict"], opp["verdict_reason"] = decide(opp)
            survivors.append(opp)
        else:
            killed.append(opp)

    if unverifiable:
        LOG.record("Candidate hydration", "PARTIAL",
                   "%d candidate(s) had no fetchable primary source and were "
                   "NOT scored: %s" % (len(unverifiable),
                                       ", ".join(unverifiable[:8])), "")

    if not args.all:
        fresh = [o for o in survivors if o["novelty"] != "UNCHANGED"]
        if fresh:
            survivors = fresh
        else:
            LOG.record("Seen-list", "OK",
                       "no NEW or CHANGED survivor this run — showing the "
                       "standing shortlist unchanged so the digest is never "
                       "silently empty", SEEN_PATH)

    survivors.sort(key=lambda o: (-o["rank_score"], o.get("days_left") or 999))

    run_meta = OrderedDict([
        ("run date", TODAY.isoformat()),
        ("elapsed", "%.1fs" % (dt.datetime.now() - started).total_seconds()),
        ("candidates discovered", len(cands)),
        ("scored", len(survivors) + len(killed)),
        ("unverifiable (no primary source)", len(unverifiable)),
        ("survivors", len(survivors)),
        ("killed", len(killed)),
        ("RePORTER window", "FY%d-FY%d" % (min(years), max(years))),
        ("seen-list", SEEN_PATH),
    ])
    digest = render_digest(survivors, killed, weekly, run_meta)

    if args.dry_run:
        print(digest)
        return 0

    out = args.out or os.path.join(
        REPORT_DIR, "PRG_SBIR_digest_%s.md" % TODAY.isoformat())
    d = os.path.dirname(out)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(out, "w") as fh:
        fh.write(digest + "\n")
    save_json(SEEN_PATH, update_seen(seen, survivors + killed))
    sys.stderr.write("wrote %s (%d survivor(s), %d kill(s), %d source hole(s))\n"
                     % (out, len(survivors), len(killed), len(LOG.holes())))
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
