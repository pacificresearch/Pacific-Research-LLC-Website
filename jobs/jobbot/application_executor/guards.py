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
    # follow-up shown only for an "Other" choice we did not make (e.g. "If you selected 'Other,' specify the visa")
    ("conditional_other", r"^if (you (selected|chose|answered|picked) .{0,3}other|other)\b"),
    ("offer_factors", r"factors .{0,40}should consider|anything (else )?we should (know|consider) (about|regarding) (an )?offer"),
    ("debarment", r"debarred|debarment|excluded.*federal|ineligible to participate in federal|oig exclusion|"
                  r"sanctioned by (the )?(fda|oig|hhs)|list of excluded|\boig\b|disqualified or restricted by the (fda|hhs)|"
                  r"receiving investigational (drugs|products)"),
    ("contact_method", r"preferred (method|mode|way) of (communication|contact)|how (should|would you like) (we|us to) contact"),
    ("future_opportunities", r"(interested in|like to) (hear|be contacted|be considered|learn) (about|for) (other|future|contract|additional)|"
                             r"if not selected.*(interested|consider)|talent (community|pool)"),
    ("visa_status_na", r"optional practical training|\bopt\b|stem extension|h-?1b (transfer|cap)|f-?1 student|tn status|e-?3"),
    ("conflict_of_interest", r"conflicts? of interest"),
    ("noncompete", r"non[- ]?compet|non[- ]?solicit|restrictive covenant"),
    ("work_auth_type", r"what (type|kind) of (valid )?(work )?authori[sz]ation|^(current )?(work authori[sz]ation|immigration) (type|status)\b"),
    ("e_signature", r"applicant.?s statement|statement (&|and) acknowledg|type your (full )?(legal )?name (above |below )?to (agree|acknowledge|sign)|"
                    r"electronic (name|signature)|e-?signature|sign(ature)? by typing"),
    ("relatives_here", r"relatives?|(family|household) members?.{0,40}(work|employ)"),
    ("licensed_hcp", r"health ?care professionals?|\bhcps?\b|physician licensed|licensed (physician|to practice|medic)|"
                     r"sunshine act|general medical council|\bgmc\b"),
    ("undisclosed_employment", r"employment (that is )?not listed|not listed on your (cv|resume)|other employment"),
    ("electronic_offer", r"(submitted|sent|delivered) to you electronic|electronic(ally)? (delivery|offer)"),
    ("truth_certification", r"certify .{0,40}(truthful|true|accurate|correct|complete)|(truthful|true and (correct|complete)).{0,30}certif"),
    ("sms_consent", r"consent to (receiv|be contacted)|text messag|\bsms\b"),
    ("requires_sponsorship", r"sponsorship|\bvisa\b|h-?1b|immigration status|sponsor (you|your|an? (employment|work))"),
    ("legally_authorized_us", r"(legally )?(authori[sz]ed|eligible|permitted) to work|work authori[sz]ation|right to work|"
                              r"(legal )?(authori[sz]ation|eligibility|permission) to (work|be employed)"),
    ("us_citizen", r"\bcitizen(ship)?\b|\bnationality\b"),
    ("ever_held_clearance", r"(ever|previously|have you) (held|had|been granted).*clearance|clearance.*(ever|previous|history)"),
    ("security_clearance", r"clearance"),
    ("veteran_status", r"veteran|military (service|spouse)|armed forces|uniformed service"),
    ("disability_status", r"disabilit"),
    ("hispanic_latino", r"hispanic|latin[oax]"),
    ("race_ethnicity", r"\brace\b|ethnic"),
    ("sexual_orientation", r"sexual orientation|transgender|lgbt"),
    ("gender", r"\bgender\b|\bsex\b|pronoun"),
    ("criminal_history", r"criminal|convict|felony|misdemeanor|offen[cs]e|background check"),
    ("age_under_18", r"under (the age of )?18|younger than 18|less than 18"),
    ("age_18_or_over", r"18 years|age of 18|\bover 18\b|date of birth|\bbirth\b|minimum age"),
    ("willing_to_relocate", r"relocat"),
    ("willing_onsite", r"willing to (be|work) (on-?site|in (the )?office)|not a remote position|commute to"),
    ("years_clinical_research", r"years of (\w+ )?experience .*(clinical (research|trials?)|crc\b)"),
    ("salary_expectation", r"salary|compensation|pay (expectation|requirement)|desired pay|expected pay"),
    ("education_dates", r"(start|end) date (month|year)|graduation (date|year)|dates? attended"),
    ("start_date", r"start date|available to start|availability|notice period|when can you start"),
    ("previously_interviewed_here", r"(ever|previously) interviewed (with|at|for)"),
    ("previously_employed_here", r"(been|were) (an? )?(contingent worker|contractor|consultant|temp\w*) (at|for|with)|previously (been )?(an? )?(employee|employed|worked|contingent)|former (employee|worker|contractor)|worked (for|at) .* (before|previously)|ever been employed|(are|were) you (currently or )?(previously )?(an? )?(employee|contingent worker) (of|for|at)|have you (ever )?worked (for|at)"),
    ("can_travel_percent", r"\btravel\b"),
    ("license", r"licen[cs]e|licensure|certified in"),
    ("attestation", r"attest|certify|i (hereby )?(confirm|acknowledge|agree|consent|understand|authori[sz]e)|terms|privacy (policy|notice)|"
                    r"signature|e-?sign|declar|accurate and complete|true and correct"),
]

ROUTINE = [
    ("first_name", r"first name|given name|preferred (first )?name|nickname"),
    ("last_name", r"last name|surname|family name"),
    ("full_name", r"^\s*(full )?name\s*$|your name|legal name"),
    ("country", r"^\s*country\s*$|country of residence|address\W+country\s*$"),
    ("school", r"^\s*(school|university|institution)( name)?\s*$"),
    ("degree", r"^\s*degree( type| level)?\s*$"),
    ("discipline", r"^\s*(discipline|field of study|major)\s*$"),
    ("referred_by_employee", r"referred by|referral from an? (current )?employee"),
    ("email", r"e-?mail"),
    ("phone", r"phone|mobile|telephone"),
    ("location", r"^\s*(current )?location\b|where are you (located|based)"),
    ("addr_zip", r"zip|postal"),
    ("addr_state", r"\bstate\b|province|territory"),
    ("addr_city", r"\bcity\b|\btown\b"),
    ("addr_line2", r"address (line )?2|\bapt\b|\bsuite\b|\bunit\b"),
    ("home_address", r"(home|street|mailing) address|^address( line 1)?$|address 1"),
    ("linkedin", r"linkedin"),
    ("website", r"website|portfolio|personal site|github"),
    ("current_employer", r"current (company|employer)|^company$|most recent employer"),
    ("current_title", r"current (job )?title|most recent title"),
    ("how_did_you_hear", r"how did you (hear|learn|find)|\bsource\b|referr?al source|where did you (hear|find|learn)"),
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
    k = _classify(stem)
    if k[0] != "unknown":
        return k
    k = _classify(full)
    # help text alone must never turn an authorization question into a sponsorship one (or vice versa):
    # if the stem talks about authorization/sponsorship but did not classify, ask the human
    if k[1] in ("requires_sponsorship", "legally_authorized_us", "us_citizen", "visa_status_na", "work_auth_type") \
            and re.search(r"authori[sz]|sponsor|eligib|permit|right to work", stem):
        return "sensitive", "unclear_work_auth"
    return k


def _classify(l: str) -> tuple[str, str]:
    l = re.sub(r"[\s*✱:]+$", "", l)  # required-field markers
    for key, rx in SENSITIVE:
        if re.search(rx, l):
            return "sensitive", key
    for key, rx in ROUTINE:
        if re.search(rx, l):
            return "routine", key
    return "unknown", ""


WORK_AUTH_KEYS = ("legally_authorized_us", "requires_sponsorship", "us_citizen", "visa_status_na", "work_auth_type")
US_RX = re.compile(r"\b(united states|u\.?s\.?a?\.?|america)\b", re.I)
COUNTRY_RX = re.compile(r"\b(canada|mexico|brazil|argentina|chile|peru|colombia|united kingdom|\buk\b|england|ireland|"
                        r"germany|france|spain|italy|netherlands|belgium|switzerland|poland|india|china|japan|"
                        r"singapore|australia|new zealand|philippines|south africa|israel|eu\b|european union|"
                        r"europe|kenya|nigeria|uae|saudi)", re.I)
JOB_COUNTRY_RX = re.compile(r"(country|location) (in )?(which|where) (this|the) (position|role|job) (is|will be) "
                            r"(located|posted|based)|this country|the country of (employment|the position)", re.I)
US_STATES = ("alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|"
             "illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|"
             "mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york|"
             "north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|"
             "south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming|"
             r"\b(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|"
             r"nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy|dc)\b|\busa?\b|united states|remote,? us")


def job_in_us(job: dict | None) -> bool | None:
    """True/False when the posting's country is known, None when it is not."""
    job = job or {}
    country = (job.get("country") or "").strip().lower()
    if country:
        return country in ("united states", "us", "usa", "united states of america")
    loc = (job.get("location") or "").lower()
    if COUNTRY_RX.search(loc) or COUNTRY_RX.search(job.get("title") or ""):
        return False
    if re.search(US_STATES, loc):
        return True
    return None


def scope_work_auth(key: str, label: str, job: dict | None) -> str:
    """The approved work-authorization answers are about the UNITED STATES. Use them only when the question is
    about the US; a question about another country (named, or 'the country where this position is located' for a
    non-US / unknown-location job) gets its own key with no approved answer, so it stops for a human."""
    if key not in WORK_AUTH_KEYS:
        return key
    text = " ".join((label or "").split())
    stem = re.sub(r"\([^)]*\)?", " ", text)
    if COUNTRY_RX.search(stem):
        return key + "_foreign"
    if US_RX.search(stem):
        return key
    if JOB_COUNTRY_RX.search(stem) or not re.search(r"\bu\.?s\b", text, re.I):
        in_us = job_in_us(job)
        if in_us is True:
            return key
        return key + ("_foreign" if in_us is False else "_unknown_country")
    return key


def attestation_id(label: str) -> str:
    return hashlib.sha1(" ".join(label.lower().split()).encode()).hexdigest()[:12]


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def match_option(answer: str, options: list[str]) -> str | None:
    """Pick the option matching an approved answer; None if not unambiguous."""
    if norm(answer) in ("not applicable", "n a", "na"):
        na = [o for o in options if re.search(r"not applicable|\bn/?a\b|does not apply|u\.?s\.? citizen", o, re.I)]
        if na:
            return na[0]
        answer = "No"
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
    m = re.fullmatch(r"advertised_midpoint_min:(\d+)", rule)
    if m:  # midpoint of the posted range, never below the floor; floor when no range is posted
        floor = int(m.group(1))
        lo, hi = job.get("salary_min"), job.get("salary_max")
        mid = (lo + hi) / 2 if lo and hi and job.get("salary_label") == "advertised" else 0
        return f"{max(round(mid, -3), floor):,.0f}"
    if rule == "advertised_midpoint":
        lo, hi = job.get("salary_min"), job.get("salary_max")
        if lo and hi and job.get("salary_label") == "advertised":
            return f"{round((lo + hi) / 2, -3):,.0f}"
        return None  # no advertised range -> ask the human
    return rule
