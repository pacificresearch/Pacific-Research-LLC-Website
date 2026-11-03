"""Question classification and the never-guess rules.

Every form control is classified by its label. Sensitive categories are answered ONLY
from approved_answers in profile.yaml; a null/missing approved answer blocks the
application (NEEDS_HUMAN_ACTION) instead of guessing. Attestations require that the
exact attestation text was approved (approved_attestations), never a blanket yes.
"""
from __future__ import annotations

import hashlib
import re

# order matters: first match wins
SENSITIVE = [
    ("sms_consent", r"consent to (receiv|be contacted)|text messag|\bsms\b"),
    ("requires_sponsorship", r"sponsorship|\bvisa\b|h-?1b|immigration status|sponsor (you|your|an? (employment|work))"),
    ("legally_authorized_us", r"(legally )?(authori[sz]ed|eligible|permitted) to work|work authori[sz]ation|right to work"),
    ("us_citizen", r"\bcitizen(ship)?\b|\bnationality\b"),
    ("security_clearance", r"clearance"),
    ("veteran_status", r"veteran|military (service|spouse)|armed forces|uniformed service"),
    ("disability_status", r"disabilit"),
    ("hispanic_latino", r"hispanic|latin[oax]"),
    ("race_ethnicity", r"\brace\b|ethnic"),
    ("sexual_orientation", r"sexual orientation|transgender|lgbt"),
    ("gender", r"\bgender\b|\bsex\b|pronoun"),
    ("criminal_history", r"criminal|convict|felony|misdemeanor|offen[cs]e|background check"),
    ("age_18_or_over", r"18 years|age of 18|\bover 18\b|date of birth|\bbirth\b"),
    ("willing_to_relocate", r"relocat"),
    ("willing_onsite", r"willing to (be|work) (on-?site|in (the )?office)|not a remote position|commute to"),
    ("years_clinical_research", r"years of (\w+ )?experience .*(clinical (research|trials?)|crc\b)"),
    ("salary_expectation", r"salary|compensation|pay (expectation|requirement)|desired pay|expected pay"),
    ("education_dates", r"(start|end) date (month|year)|graduation (date|year)|dates? attended"),
    ("start_date", r"start date|available to start|availability|notice period|when can you start"),
    ("previously_employed_here", r"previously (been )?(employed|worked)|former employee|worked (for|at) .* before|ever been employed"),
    ("can_travel_percent", r"\btravel\b"),
    ("license", r"licen[cs]e|licensure|certified in"),
    ("attestation", r"attest|certify|i (hereby )?(confirm|acknowledge|agree|consent|understand)|terms|privacy (policy|notice)|"
                    r"signature|e-?sign|declar|accurate and complete|true and correct"),
]

ROUTINE = [
    ("first_name", r"first name|given name|preferred first"),
    ("last_name", r"last name|surname|family name"),
    ("full_name", r"^\s*(full )?name\s*$|your name|legal name"),
    ("country", r"^\s*country\s*$|country of residence"),
    ("school", r"^\s*(school|university|institution)( name)?\s*$"),
    ("degree", r"^\s*degree( type| level)?\s*$"),
    ("discipline", r"^\s*(discipline|field of study|major)\s*$"),
    ("referred_by_employee", r"referred by|referral from an? (current )?employee"),
    ("email", r"e-?mail"),
    ("phone", r"phone|mobile|telephone"),
    ("location", r"^\s*(current )?(location|city)\b|where are you (located|based)|address"),
    ("linkedin", r"linkedin"),
    ("website", r"website|portfolio|personal site|github"),
    ("current_employer", r"current (company|employer)|^company$|most recent employer"),
    ("current_title", r"current (job )?title|most recent title"),
    ("how_did_you_hear", r"how did you (hear|learn|find)|source|referr?al source|where did you"),
    ("education_level", r"highest (level of )?(education|degree)"),
    ("resume", r"resume|\bcv\b|curriculum"),
    ("cover_letter", r"cover letter|motivation letter|letter of interest"),
]

CAPTCHA_SELECTORS = [
    "iframe[src*='hcaptcha.com']", "iframe[title*='challenge']", "iframe[src*='recaptcha/api2/bframe']",
    "iframe[src*='recaptcha/api2/anchor']", "iframe[src*='challenges.cloudflare.com']", ".cf-turnstile",
    "#px-captcha", "[data-sitekey]:not(.grecaptcha-badge)",
]
CONFIRM_RX = re.compile(r"thank(s| you) for (applying|your (application|interest|submission))|application (has been |was )?"
                        r"(received|submitted|complete)|we('ve| have) received your application|successfully submitted|"
                        r"submission (received|confirmed)", re.I)
VALIDATION_RX = re.compile(r"(is|are) required|this field is required|please (enter|select|complete|provide)|invalid", re.I)


def classify(label: str) -> tuple[str, str]:
    """-> (kind, key): kind in {'sensitive','routine','unknown'}

    The question stem decides; parenthetical help text ("Answer Yes if your visa...") only breaks ties.
    """
    full = " ".join((label or "").lower().split())
    stem = re.sub(r"\([^)]*\)?", " ", full)
    stem = re.split(r"(?<=\?)\s", stem)[0]
    for cand in (stem, full):
        k = _classify(cand)
        if k[0] != "unknown":
            return k
    return "unknown", ""


def _classify(l: str) -> tuple[str, str]:
    l = re.sub(r"[\s*✱:]+$", "", l)  # required-field markers
    for key, rx in SENSITIVE:
        if re.search(rx, l):
            return "sensitive", key
    for key, rx in ROUTINE:
        if re.search(rx, l):
            return "routine", key
    return "unknown", ""


def attestation_id(label: str) -> str:
    return hashlib.sha1(" ".join(label.lower().split()).encode()).hexdigest()[:12]


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def match_option(answer: str, options: list[str]) -> str | None:
    """Pick the option matching an approved answer; None if not unambiguous."""
    a = norm(answer)
    opts = [(o, norm(o)) for o in options if norm(o) and norm(o) not in ("select", "select one", "please select", "")]
    for o, n in opts:
        if n == a:
            return o
    starts = [o for o, n in opts if n.startswith(a) or a.startswith(n)]
    if len(starts) == 1:
        return starts[0]
    if a in ("yes", "no"):
        yn = [o for o, n in opts if n.split()[:1] == [a]]
        if len(yn) == 1:
            return yn[0]
    contains = [o for o, n in opts if a and a in n]
    return contains[0] if len(contains) == 1 else None


def salary_answer(rule: str | None, job: dict) -> str | None:
    if not rule:
        return None
    if rule == "advertised_midpoint":
        lo, hi = job.get("salary_min"), job.get("salary_max")
        if lo and hi and job.get("salary_label") == "advertised":
            return f"{round((lo + hi) / 2, -3):,.0f}"
        return None  # no advertised range -> ask the human
    return rule
