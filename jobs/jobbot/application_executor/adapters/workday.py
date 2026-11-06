"""Workday (myworkdayjobs.com / myworkdaysite.com) multi-step application.

Flow: Apply Manually -> Create Account / Sign In -> My Information -> My Experience ->
Application Questions -> Voluntary Disclosures -> Self Identify -> Review -> Submit.

Built against live Workday markup (data-automation-id attributes are Workday's stable test hooks).
Account: one per tenant host, email = profile.account_email, Chrome-strength password from
credentials.py (saved before it is typed). The "I Accept" applicant-privacy box on account creation is
accepted under Andrew's standing instruction to create portal logins; its text is logged.

Every other field goes through the same policy as the other adapters: optional -> skipped; required
voluntary disclosure -> "I don't wish to answer"; anything else required that has no approved answer ->
Blocked (NEEDS_HUMAN_ACTION). Review mode stops on the Review step; submit mode clicks Submit there.
"""
from __future__ import annotations

import re
from datetime import date

from ... import credentials
from ..guards import attestation_id, classify, match_option, salary_answer
from .base import CORE_FIELDS, DECLINE_KEYS, DECLINE_RX, captcha_visible

A = lambda aid: f"[data-automation-id='{aid}']"  # noqa: E731

FIELDS_JS = r"""
() => [...document.querySelectorAll("[data-automation-id^='formField-']")].filter(e => e.offsetParent).map((e, i) => {
  e.setAttribute('data-jobbot-wd', String(i));
  const lab = e.querySelector('label, legend');
  const label = (lab ? lab.innerText : e.innerText.split('\n')[0] || '').replace(/\s+/g, ' ').trim();
  const radios = [...e.querySelectorAll("input[type=radio]")];
  const cb = e.querySelectorAll("input[type=checkbox]");
  const btn = e.querySelector("button[aria-haspopup='listbox']");
  const multi = e.querySelector("[data-automation-id='multiselectInputContainer']");
  const date = e.querySelector("[data-automation-id*='dateSection']");
  const ta = e.querySelector('textarea'); const inp = e.querySelector("input[type=text], input:not([type]), input[type=tel], input[type=email], input[type=number]");
  let type = radios.length ? 'radio' : cb.length ? 'checkbox' : btn ? 'select' : multi ? 'multiselect' : date ? 'date' : ta ? 'textarea' : inp ? 'text' : 'other';
  const opts = radios.map(r => { const l = document.querySelector(`label[for='${r.id}']`); return l ? l.innerText.trim() : r.value; });
  const sel = e.querySelector("[data-automation-id='selectedItem']");
  const value = btn ? btn.innerText.trim() : multi ? (sel ? sel.innerText.trim() : '') : (inp ? inp.value : ta ? ta.value : '');
  return {i, id: e.getAttribute('data-automation-id').slice(10), label, required: /\*\s*$/.test(label) || !!e.querySelector('[aria-required=true],[required]'),
          type, options: opts, value, checked: cb.length ? cb[0].checked : null};
})
"""


class WorkdayError(Exception):
    pass


def _step(page) -> str:
    loc = page.locator(A("progressBarActiveStep"))
    return re.sub(r"^current step \d+ of \d+\s*", "", loc.inner_text().strip()) if loc.count() else "?"


def _accept_cookies(page):
    for sel in (A("legalNoticeAcceptButton"),):
        if page.locator(sel).count():
            page.click(sel)


def sign_in_or_create(page, url, pr, log):
    email = pr.get("account_email") or pr["contact"]["email"]
    cred, new = credentials.get_or_create(url, email)
    if page.locator(A("createAccountSubmitButton")).count() and new:
        page.fill(A("email"), email)
        page.fill(A("password"), cred["password"])
        page.fill(A("verifyPassword"), cred["password"])
        box = page.locator(A("createAccountCheckbox"))
        if box.count():
            log.append({"label": "Create-account applicant privacy notice", "key": "account_terms",
                        "value": "accepted (standing instruction: create portal logins)", "ok": True})
            box.check()
        btn = A("click_filter") if page.locator(A("click_filter")).count() else A("createAccountSubmitButton")
        page.click(btn)
    else:
        if page.locator(A("signInLink")).count():
            page.click(A("signInLink"))
            page.wait_for_timeout(1500)
        page.fill(A("email"), email)
        page.fill(A("password"), cred["password"])
        btn = A("click_filter") if page.locator(A("click_filter")).count() else A("signInSubmitButton")
        page.click(btn)
    page.wait_for_timeout(6000)
    body = page.inner_text("body").lower()
    if "verify your account" in body or "verification email" in body:
        credentials.set_status(url, "needs_email_verification")
        raise WorkdayError("account created — Workday sent a verification email to "
                           f"{email}; click it (or let a Claude session read it) and re-run")
    if page.locator(A("errorMessage")).count() and _step(page).startswith("Create Account"):
        raise WorkdayError("sign-in failed: " + page.locator(A("errorMessage")).first.inner_text()[:200])
    credentials.set_status(url, "active")
    log.append({"label": "portal account", "key": "account", "value": f"{email} @ {credentials.site_key(url)}",
                "ok": True})


def _choose_listbox(page, field, option_text):
    field.locator("button[aria-haspopup='listbox']").click()
    page.wait_for_timeout(600)
    opts = page.locator("[role='option']")
    texts = [opts.nth(k).inner_text().strip() for k in range(opts.count())]
    pick = option_text if option_text in texts else match_option(option_text, texts)
    if not pick:
        page.keyboard.press("Escape")
        return None, texts
    exact = page.get_by_role("option", name=pick, exact=True)
    (exact.first if exact.count() else page.locator("[role='option']", has_text=pick).first).click()
    page.wait_for_timeout(400)
    return pick, texts


OPT = "[data-automation-id='activeListContainer'] [data-automation-id='promptOption']"


def _open_options(page):
    loc = page.locator(OPT)
    seen, texts = set(), []
    for k in range(min(loc.count(), 80)):
        t = loc.nth(k).inner_text().strip()
        if t and t not in seen and loc.nth(k).is_visible():
            seen.add(t)
            texts.append(t)
    return texts


def _choose_multiselect(page, field, text):
    inp = field.locator("input").first
    inp.click()
    page.wait_for_timeout(1200)
    texts = _open_options(page)  # options shown for THIS field only (scoped to the active popup)
    pick = match_option(text, texts) or (texts[0] if len(texts) == 1 else None)
    if not pick and re.search(r"website|career", text, re.I):  # "How did you hear": company site wording varies
        pick = next((t for t in texts if re.search(r"(company|corporate|career).*(site|website|page)|careers? (site|page|website)|"
                                                    r"^website$|company website", t, re.I)), None)
    if not pick:
        page.keyboard.press("Escape")
        return None, texts
    exact = page.locator(OPT).filter(has_text=re.compile(rf"^\s*{re.escape(pick)}\s*$"))
    (exact.first if exact.count() else page.locator(OPT, has_text=pick).first).click()
    page.wait_for_timeout(1500)
    now = _open_options(page)
    selected = field.locator("[data-automation-id='selectedItem']").count() > 0
    sub = [t for t in now if t != pick] if (now and set(now) != set(texts)) else []  # sub-menu only if the list CHANGED
    if sub and not selected:
        # hierarchical prompt (e.g. Website -> specific site): take the employer's own careers site
        nxt = next((t for t in sub if re.search(r"career|company|corporate|website", t, re.I)), sub[0] if len(sub) == 1 else None)
        if not nxt:
            page.keyboard.press("Escape")
            return None, sub
        page.locator(OPT, has_text=nxt).first.click()
        page.wait_for_timeout(800)
        pick = f"{pick} > {nxt}"
    page.keyboard.press("Escape")
    return pick, texts


def _value_for(key, label, f, job, pr):
    c, ans = pr["contact"], pr.get("approved_answers", {}) or {}
    addr = pr.get("address") or {}
    first, last = c["name"].split()[0], c["name"].split()[-1]
    by_id = {"legalName--firstName": first, "legalName--lastName": last, "addressLine1": addr.get("line1"),
             "city": addr.get("city"), "postalCode": addr.get("postal_code"), "countryRegion": addr.get("state"),
             "phoneNumber": re.sub(r"\D", "", c["phone"]), "phoneType": "Mobile", "email": pr.get("account_email"),
             "source": "Website" if re.search(r"website|career", str(ans.get("how_did_you_hear")), re.I)
             else ans.get("how_did_you_hear"), "country": "United States of America",
             "countryPhoneCode": "United States of America (+1)"}
    if f["id"] in by_id:
        return by_id[f["id"]]
    if key in ("first_name", "last_name", "full_name", "email", "phone"):
        return {"first_name": first, "last_name": last, "full_name": c["name"], "email": pr.get("account_email"),
                "phone": c["phone"]}[key]
    if key == "salary_expectation":
        return salary_answer(ans.get("salary_expectation_rule"), job)
    if key == "licensed_hcp" and f["type"] == "select":
        hcp = pr.get("hcp_option_letter")  # employer-coded A/B/C answer sets, mapped once from the question text
        if hcp:
            return hcp
    if key == "previously_employed_here" or re.search(r"previously (worked|been employed)|worked for .* before", label, re.I):
        prior = [p.lower() for p in pr.get("prior_employers", [])]
        return "Yes" if any(p in job["employer"].lower() for p in prior) else ans.get("previously_employed_here")
    return ans.get(key)


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                      "dec"], 1)}


def parse_dates(dates: str) -> tuple[tuple[int, int] | None, tuple[int, int] | None, bool]:
    """'Nov 2021 - Feb 2026' -> ((11, 2021), (2, 2026), False); '... - Present' -> current=True."""
    parts = re.split(r"\s*[-–]\s*", dates.strip())

    def one(x):
        m = re.match(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{4})", x.strip())
        return (MONTHS[m.group(1).lower()], int(m.group(2))) if m else None
    start = one(parts[0]) if parts else None
    current = len(parts) > 1 and parts[1].lower().startswith("present")
    end = None if current or len(parts) < 2 else one(parts[1])
    return start, end, current


def _date_value(sec) -> tuple[str, str]:
    mi = sec.locator("[data-automation-id='dateSectionMonth-input']")
    yi = sec.locator("[data-automation-id='dateSectionYear-input']")
    return (mi.first.get_attribute("aria-valuenow") or mi.first.input_value() if mi.count() else "",
            yi.first.get_attribute("aria-valuenow") or yi.first.input_value() if yi.count() else "")


def _fill_date(sec, mm_yy):
    """Workday MM/YYYY widget: focus the month and type MMYYYY (it auto-advances); retype if a wrong value is saved."""
    if not mm_yy or not sec.count():
        return
    m, y = mm_yy
    cur_m, cur_y = _date_value(sec)
    if cur_m and cur_y and int(cur_m) == m and int(cur_y) == y:
        return
    mi = sec.locator("[data-automation-id='dateSectionMonth-input']")
    target = mi.first if mi.count() else sec.locator("input").first
    disp = sec.locator("[data-automation-id='dateSectionMonth-display']")
    try:
        (disp.first if disp.count() else target).scroll_into_view_if_needed(timeout=5000)
        (disp.first if disp.count() else target).click(timeout=5000)
    except Exception:
        target.evaluate("e => { e.scrollIntoView({block: 'center'}); e.focus(); }")
    target.page.keyboard.type(f"{m:02d}{y}", delay=60)


def fill_work_experience(page, pr, log) -> list[str]:
    """Enter every role from the evidence library (title, employer, location, dates) — CV facts only.

    Live layout (Workday 2026): 'Work Experience [Add]', 'Education [Add]', 'Websites [Add]' in that order;
    the first add-button belongs to Work Experience. Each entry panel holds formField-jobTitle / companyName /
    location / currentlyWorkHere / startDate / endDate (endDate disappears when 'currently work here' is
    checked), so every field is located INSIDE its own entry panel, never by page-wide index.
    """
    roles = pr["experience"]
    titles = page.locator("[data-automation-id='formField-jobTitle']")
    for k, role in enumerate(roles):
        if titles.count() <= k:
            page.locator("[data-automation-id='add-button']").first.click()
            page.wait_for_timeout(1500)
            if titles.count() <= k:
                return [f"could not add work-experience entry for {role['org']}"]
        entry = titles.nth(k).locator("xpath=ancestor::div[.//*[@data-automation-id='formField-startDate']][1]")
        f = lambda fid: entry.locator(f"[data-automation-id='formField-{fid}']").first  # noqa: E731
        start, end, current = parse_dates(role["dates"])
        for fid, val in (("jobTitle", role["title"]), ("companyName", role["org"]), ("location", role.get("location", ""))):
            box = f(fid).locator("input")
            if box.count() and val and box.first.input_value() != val:
                box.first.fill(val)
        cw = f("currentlyWorkHere").locator("input[type=checkbox]")
        if cw.count() and cw.first.is_checked() != current:
            cw.first.set_checked(current, force=True)
            page.wait_for_timeout(500)
        _fill_date(f("startDate"), start)
        if not current:
            _fill_date(f("endDate"), end)
        log.append({"label": "Work experience", "key": "experience",
                    "value": f"{role['title']} @ {role['org']} ({role['dates']})", "ok": True})
    return []


def _settle(page, max_s: int = 25) -> None:
    """Workday renders grey skeleton placeholders first; wait until the field list stops changing."""
    stable, last = 0, -1
    for _ in range(max_s):
        n = page.locator("[data-automation-id^='formField-']").count()
        loading = page.locator("[data-automation-id*='loading'], [class*='skeleton' i], [data-automation-id='loadingSpinner']").count()
        stable = stable + 1 if (n == last and not loading) else 0
        if stable >= 2:
            return
        last = n
        page.wait_for_timeout(1000)


def fill_step(page, job, pr, app_row, log) -> list[str]:
    """Fill the current Workday step. Returns blockers (empty = step complete)."""
    _settle(page)
    blockers = []
    approved_att = set(pr.get("approved_attestations", []) or [])
    step = _step(page)
    # resume upload + work history live on My Experience
    if "Experience" in step:
        up = page.locator("input[type=file]")
        if up.count() and not page.locator(A("file-upload-successful")).count():
            up.first.set_input_files(app_row["resume_path"])
            page.wait_for_timeout(6000)  # Workday parses the resume and may prefill work history
            log.append({"label": "Resume upload", "key": "resume", "value": "<file:resume.pdf>", "ok": True})
        blockers += fill_work_experience(page, pr, log)
    fields = page.evaluate(FIELDS_JS)
    for f in fields:
        label = f["label"].rstrip("*").strip()
        if "Experience" in step and (f["id"] in ("jobTitle", "companyName", "location", "startDate", "endDate",
                                                 "currentlyWorkHere", "roleDescription")
                                     or f["type"] == "other" and "upload" in label.lower()):
            continue  # handled by fill_work_experience / resume upload above
        kind, key = classify(label)
        req = f["required"]
        loc = page.locator(f"[data-jobbot-wd='{f['i']}']")
        if f["value"] and f["type"] in ("select", "text", "multiselect") and f["value"] not in ("Select One",
                                                                                               "0 items selected"):
            continue  # Workday prefilled it (from the account or resume parse)
        # voluntary disclosures -> decline when required
        if key in DECLINE_KEYS or re.search(r"disabilit|veteran|gender|ethnic|race", label, re.I):
            if not req:
                continue
            if f["type"] == "select":
                loc.locator("button[aria-haspopup='listbox']").click()
                page.wait_for_timeout(500)
                opts = [o.strip() for o in page.locator("[role='option']").all_inner_texts()]
                pick = next((o for o in opts if DECLINE_RX.search(o)), None)
                if pick:
                    page.locator("[role='option']", has_text=pick).first.click()
                    log.append({"label": label, "key": key or "disclosure", "value": pick, "ok": True})
                else:
                    page.keyboard.press("Escape")
                    blockers.append(f"required disclosure without a decline option: '{label[:80]}' {opts[:5]}")
            elif f["type"] in ("radio", "checkbox"):
                pick = next((o for o in f["options"] if DECLINE_RX.search(o)), None)
                if pick:
                    loc.get_by_label(pick).check(force=True)
                    log.append({"label": label, "key": key or "disclosure", "value": pick, "ok": True})
                else:
                    blockers.append(f"required disclosure without a decline option: '{label[:80]}'")
            continue
        if not req:
            continue  # policy: optional -> blank (Workday marks required fields reliably)
        if kind == "sensitive" and key == "attestation" or f["type"] == "checkbox":
            aid = attestation_id(label)
            if aid in approved_att:
                loc.locator("input[type=checkbox]").first.check(force=True)
                log.append({"label": label, "key": "attestation", "value": f"<checked {aid}>", "ok": True})
            else:
                blockers.append(f"attestation needs your explicit approval [{aid}]: '{label[:200]}'")
            continue
        # self-identification form signature (CC-305): name + today's date, only alongside a decline answer
        if re.search(r"^name$|your name", label, re.I) and "Self Identify" in step:
            loc.locator("input").first.fill(pr["contact"]["name"])
            continue
        if f["type"] == "date" and "Self Identify" in step:
            t = date.today()
            for part, val in (("Month", t.month), ("Day", t.day), ("Year", t.year)):
                sec = loc.locator(f"[data-automation-id='dateSection{part}-input']")
                if sec.count():
                    sec.fill(str(val))
            continue
        val = _value_for(key, label, f, job, pr)
        if val in (None, "") and kind == "unknown":
            from ...evidence_answers import answer as evidence_answer
            val = evidence_answer(label, f.get("options", []), job)
        if val in (None, ""):
            blockers.append(f"{'custom question' if kind == 'unknown' else (key or 'field').replace('_', ' ')} "
                            f"needs your answer: '{label[:160]}'")
            continue
        try:
            if f["type"] == "select":
                pick, opts = _choose_listbox(page, loc, str(val))
                if not pick:
                    full = loc.inner_text()[:1500].replace("\n", " ")
                    blockers.append(f"'{val}' matches no option for '{label[:80]}': {opts[:6]}"
                                    + (f" || FULL QUESTION: {full}" if all(len(o) <= 2 for o in opts if o != 'Select One') else ""))
                    continue
            elif f["type"] == "multiselect":
                pick, opts = _choose_multiselect(page, loc, str(val))
                if not pick:
                    blockers.append(f"'{val}' matches no option for '{label[:80]}': {opts[:6]}")
                    continue
            elif f["type"] == "radio":
                pick = match_option(str(val), f["options"])
                if not pick:
                    blockers.append(f"'{val}' matches no option for '{label[:80]}': {f['options'][:6]}")
                    continue
                loc.get_by_label(pick, exact=True).check(force=True)
            elif f["type"] in ("text", "textarea"):
                loc.locator("input, textarea").first.fill(str(val))
            else:
                blockers.append(f"unsupported Workday widget for '{label[:80]}'")
                continue
            log.append({"label": label, "key": key or f["id"], "value": str(val)[:60], "ok": True})
        except Exception as ex:
            blockers.append(f"could not fill '{label[:80]}': {str(ex)[:100]}")
    return blockers


def open_and_fill(page, url, job, pr, app_row, evid, wait_human_seconds=0):
    from .. import Blocked
    log: list[dict] = []
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    try:  # Workday keeps background requests open; wait for the apply/sign-in UI instead of network idle
        page.wait_for_selector(f"{A('applyManually')}, {A('adventureButton')}, {A('email')}, {A('progressBar')}",
                               timeout=60000)
    except Exception:
        pass
    page.wait_for_timeout(2000)
    body = page.inner_text("body").lower()
    if re.search(r"page you are looking for doesn.t exist|no longer (available|accepting)|position has been filled|"
                 r"job (posting )?(is )?(closed|expired)|this job is no longer", body):
        raise Blocked(["POSTING CLOSED: the employer page says this job no longer exists"])
    _accept_cookies(page)
    if not page.locator(A("applyManually")).count() and page.locator(A("adventureButton")).count():
        page.locator(A("adventureButton")).first.click()  # job page -> "Apply" -> start-your-application page
        page.wait_for_timeout(3000)
    if page.locator(A("applyManually")).count():
        page.click(A("applyManually"))
        page.wait_for_timeout(3500)
    if captcha_visible(page):
        raise Blocked(["human verification (CAPTCHA) on the Workday sign-in — not bypassed"])
    if page.locator(A("email")).count() and page.locator(A("password")).count():
        try:
            sign_in_or_create(page, url, pr, log)
        except WorkdayError as ex:
            raise Blocked([str(ex)])
    retries = 0
    for _ in range(12):
        if "something went wrong" in page.inner_text("body").lower():
            if retries >= 1:
                raise Blocked(["Workday returned 'Something went wrong' twice — paused to protect the account; "
                               "retry later from your Mac (home connection)"])
            retries += 1
            page.wait_for_timeout(15000)
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(4000)
            continue
        step = _step(page)
        if step.startswith("Review"):
            return log
        import os
        if os.environ.get("JOBBOT_WD_DUMP"):
            dump = page.evaluate("()=>[...document.querySelectorAll('[data-automation-id]')].filter(e=>e.offsetParent||e.type==='file')"
                                 ".map(e=>e.getAttribute('data-automation-id')+'|'+e.tagName+'|'+(e.type||'')+'|'"
                                 "+(e.innerText||e.value||'').trim().slice(0,50).replace(/\\n/g,' '))")
            (evid / f"dump_{re.sub(r'[^A-Za-z]+', '_', step)}.txt").write_text("\n".join(dump))
        blockers = fill_step(page, job, pr, app_row, log)
        page.screenshot(path=str(evid / f"wd_{re.sub(r'[^A-Za-z]+', '_', step)}.png"), full_page=True)
        if blockers:
            raise Blocked([f"[{step}] {b}" for b in blockers])
        page.locator(A("pageFooterNextButton")).click(timeout=60000)
        page.wait_for_timeout(6000)
        errs = page.locator(A("errorMessage")).all_inner_texts()
        if not errs and "errors found" in page.inner_text("body").lower():
            errs = [e for e in page.locator("[data-automation-id='errorBanner'], [role='alert']").all_inner_texts() if e.strip()] \
                or ["Workday reported 'Errors Found' on this step"]
        if errs and _step(page) == step:
            raise Blocked([f"[{step}] Workday validation: {e[:160]}" for e in errs[:6]])
    raise Blocked(["Workday flow did not reach Review within 10 steps"])


def submit(page):
    page.click(A("pageFooterNextButton"))  # on Review, the footer button is "Submit"
