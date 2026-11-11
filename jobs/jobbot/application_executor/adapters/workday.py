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
from ..guards import attestation_id, classify, is_plain_consent, match_option, salary_answer, scope_work_auth
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


def _all_listbox_texts(page) -> list[str]:
    """Workday listboxes are virtualized: scroll the open list to collect every option."""
    seen: list[str] = []
    lb = page.locator("[role='listbox']:visible").last
    for _ in range(25):
        for t in page.locator("[role='option']:visible").all_inner_texts():
            t = t.strip()
            if t and t not in seen:
                seen.append(t)
        try:
            at_end = lb.evaluate("e => { const b = e.scrollTop; e.scrollTop += Math.max(200, e.clientHeight); "
                                 "return e.scrollTop === b; }")
        except Exception:
            break
        page.wait_for_timeout(200)
        if at_end:
            break
    try:
        lb.evaluate("e => e.scrollTop = 0")
    except Exception:
        pass
    return seen


def _choose_listbox(page, field, option_text):
    field.locator("button[aria-haspopup='listbox']").click()
    page.wait_for_timeout(600)
    texts = _all_listbox_texts(page)
    pick = option_text if option_text in texts else match_option(option_text, texts)
    if pick:  # bring it into view in the virtualized list before clicking
        lb = page.locator("[role='listbox']:visible").last
        for _ in range(25):
            o = page.get_by_role("option", name=pick, exact=True)
            if o.count() and o.first.is_visible():
                break
            try:
                lb.evaluate("e => e.scrollTop += Math.max(200, e.clientHeight)")
            except Exception:
                break
            page.wait_for_timeout(150)
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


# acceptable field-of-study picks for an MA in International Studies
FOS_OK = re.compile(r"^\s*(international|global)\b.*(stud|relation|affair)|^\s*other\s*$", re.I)


def _unselect(page, field, text):
    chips = field.locator("[data-automation-id='selectedItem']", has_text=text)
    for i in range(chips.count() - 1, -1, -1):
        x = chips.nth(i).locator("[data-automation-id='DELETE_charm'], [aria-label*='elete' i], [aria-label*='emove' i]")
        if x.count():
            x.first.click(force=True)
            page.wait_for_timeout(600)


def _fill_full_date(page, loc, d) -> bool:
    """Workday MM/DD/YYYY widget: click the month display layer, type MMDDYYYY (auto-advances), verify."""
    mi = loc.locator("[data-automation-id='dateSectionMonth-input']")
    want = (str(d.month), str(d.day), str(d.year))

    def cur():
        try:
            return tuple(str(int(loc.locator(f"[data-automation-id='dateSection{p}-input']").first.input_value() or 0))
                         for p in ("Month", "Day", "Year"))
        except Exception:
            return ()
    for _ in range(3):
        if not mi.count() or cur() == want:
            break
        disp = loc.locator("[data-automation-id='dateSectionMonth-display']")
        try:
            (disp.first if disp.count() else mi.first).scroll_into_view_if_needed(timeout=5000)
            (disp.first if disp.count() else mi.first).click(timeout=5000)
        except Exception:
            mi.first.evaluate("e => { e.scrollIntoView({block: 'center'}); e.focus(); }")
        page.keyboard.type(f"{d.month:02d}{d.day:02d}{d.year}", delay=80)
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
    return cur() == want


def _tick(page, loc) -> None:
    """Tick a Workday checkbox: native input, a styled role=checkbox, or the clickable label/row."""
    for sel in ("input[type=checkbox]", "[role=checkbox]", "[data-automation-id*='checkbox' i]", "label"):
        el = loc.locator(sel)
        if el.count():
            el = el.first
            try:
                if sel == "input[type=checkbox]":
                    el.check(force=True, timeout=5000)
                else:
                    if (el.get_attribute("aria-checked") or "") != "true":
                        el.click(force=True, timeout=5000)
                return
            except Exception:
                continue
    raise RuntimeError("could not tick the checkbox")


def _choose_exact(page, inp, text):
    for attempt in (None, text):
        if attempt:
            inp.fill(attempt)
            inp.press("Enter")
            page.wait_for_timeout(1500)
        texts = _open_options(page)
        pick = next((t for t in texts if t.strip().lower() == text.lower()), None)
        if pick:
            page.locator(OPT).filter(has_text=re.compile(rf"^\s*{re.escape(pick)}\s*$")).first.click()
            page.wait_for_timeout(1200)
            page.keyboard.press("Escape")
            return pick, texts
    page.keyboard.press("Escape")
    return None, texts


def _choose_multiselect(page, field, text, exact=False):
    inp = field.locator("input").first
    try:
        inp.click(timeout=5000)
    except Exception:  # a leftover search popup from a previous try can cover the input
        page.keyboard.press("Escape")
        inp.click(force=True, timeout=5000)
    if inp.input_value():
        inp.fill("")  # clear a previous search term so the full list comes back
    page.wait_for_timeout(1200)
    texts = _open_options(page)  # options shown for THIS field only (scoped to the active popup)
    if exact:  # e.g. "Other": never let it match "Mgmt & Business Admin - Other"
        return _choose_exact(page, inp, text)
    pick = match_option(text, texts) or (texts[0] if len(texts) == 1 else None)
    if not pick and not re.search(r"website|career", text, re.I):  # long lists (field of study, skills): type to filter
        inp.fill(text)
        inp.press("Enter")
        page.wait_for_timeout(1500)
        more = _open_options(page)
        if more:
            texts = more
            pick = match_option(text, texts) or next((t for t in texts if text.lower() in t.lower()), None) \
                or (texts[0] if len(texts) == 1 else None)
    if not pick and re.search(r"website|career", text, re.I) and not any(
            re.search(r"(company|corporate|career).*(site|website|page)|careers? (site|page|website)|website", t, re.I)
            for t in texts):
        for term in ("website", "career"):  # long, virtualized lists: filter by typing
            inp.fill(term)
            inp.press("Enter")
            page.wait_for_timeout(1500)
            more = _open_options(page)
            if more:
                texts = more
                break
    if not pick and re.search(r"website|career", text, re.I):
        # Andrew 11/6: source "can be anything — click whatever is easiest". Prefer site/job-board wording; never an
        # option that asserts something untrue (referral, recruiter contact, current worker) or needs follow-ups.
        unsafe = re.compile(r"referr|employee|recruiter|contingent|worker|agency|campus|university|fair|event|"
                            r"intern|former|current|other \(please|specify", re.I)
        prefs = [r"(company|corporate|career).*(site|website|page)|careers? (site|page|website)|website",
                 r"job board|indeed|linkedin|internet|online|search engine|glassdoor|social"]
        for rx in prefs:
            pick = next((t for t in texts if re.search(rx, t, re.I) and not unsafe.search(t)), None)
            if pick:
                break
        if not pick:
            pick = next((t for t in texts if not unsafe.search(t)), None)
    if False:  # legacy branch kept for readability
        pass
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
    for _ in range(3):  # nested prompts: a category opens a sub-list, sometimes with a same-named leaf
        if selected or not now or set(now) == set(texts):
            break
        leaf = next((t for t in now if t == pick), None) or (now[0] if len(now) == 1 else None)
        if not leaf:
            break
        page.locator(OPT).filter(has_text=re.compile(rf"^\s*{re.escape(leaf)}\s*$")).first.click()
        page.wait_for_timeout(1200)
        texts, now = now, _open_options(page)
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
    edu = (pr.get("education_structured") or [{}])[0]
    by_id.update({"school": edu.get("school"), "schoolName": edu.get("school"), "degree": edu.get("degree"),
                  "fieldOfStudy": edu.get("discipline"), "fieldsOfStudy": edu.get("discipline")})
    if f["id"] in by_id:
        return by_id[f["id"]]
    if key == "education_level":
        return edu.get("degree")
    if key in ("school", "degree", "discipline"):
        return {"school": edu.get("school"), "degree": edu.get("degree"), "discipline": edu.get("discipline")}[key]
    if key in ("first_name", "last_name", "full_name", "email", "phone"):
        return {"first_name": first, "last_name": last, "full_name": c["name"], "email": pr.get("account_email"),
                "phone": c["phone"]}[key]
    if key == "addr_county":
        return addr.get("county") or ("Orange" if (addr.get("city") or "").lower() == "orange" else None)
    if key == "citizenship_country" and str(ans.get("us_citizen", "")).lower().startswith("yes"):
        return "United States of America"
    if key == "salary_expectation":
        return salary_answer(ans.get("salary_expectation_rule"), job)
    if key == "licensed_hcp" and f["type"] == "select" and re.search(r"\(\s*[ABC]\s*\)", label):
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
        rd = f("roleDescription")
        if rd.count() and "*" in (rd.inner_text() or ""):  # required on some tenants (Merck): CV bullets, verbatim
            box = rd.locator("textarea").first
            text = "\n".join("- " + b["text"] for b in role.get("bullets", []) if b.get("text"))[:1900]
            if box.count() and text and not box.input_value().strip():
                box.fill(text)
        log.append({"label": "Work experience", "key": "experience",
                    "value": f"{role['title']} @ {role['org']} ({role['dates']})", "ok": True})
    # the resume parse can leave extra entries; an EMPTY one has required fields and blocks the step -> delete it
    for k in range(titles.count() - 1, len(roles) - 1, -1):
        entry = titles.nth(k).locator("xpath=ancestor::div[.//*[@data-automation-id='formField-startDate']][1]")
        box = entry.locator("[data-automation-id='formField-jobTitle'] input")
        if box.count() and not box.first.input_value().strip():
            panel = titles.nth(k).locator("xpath=ancestor::div[.//button[contains(normalize-space(.), 'Delete')]][1]")
            btn = panel.get_by_role("button", name=re.compile(r"^delete", re.I))
            if btn.count():
                btn.last.click()
                page.wait_for_timeout(1000)
                log.append({"label": "Work experience", "key": "experience", "value": f"removed empty entry {k + 1}",
                            "ok": True})
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
        key = scope_work_auth(key, label, job)
        req = f["required"]
        loc = page.locator(f"[data-jobbot-wd='{f['i']}']")
        is_fos = f["id"] in ("fieldOfStudy", "fieldsOfStudy") or key == "discipline"
        if is_fos and f["type"] == "multiselect" and f["value"] not in ("", "0 items selected"):
            chips = loc.locator("[data-automation-id='selectedItem']")
            bad = [chips.nth(i) for i in range(chips.count()) if not FOS_OK.search(chips.nth(i).inner_text())]
            for chip in reversed(bad):  # a wrong field (parse or earlier mistake) is never left in place
                x = chip.locator("[data-automation-id='DELETE_charm'], [aria-label*='elete' i], [aria-label*='emove' i]")
                if x.count():
                    x.first.click(force=True)
                    page.wait_for_timeout(600)
            if bad:
                f["value"] = "" if not loc.locator("[data-automation-id='selectedItem']").count() else f["value"]
        if f["value"] and f["type"] in ("select", "text", "multiselect") and f["value"] not in ("Select One",
                                                                                               "0 items selected") \
                and kind != "sensitive" and not re.search(r"authori|sponsor|citizen|visa|eligib", label, re.I):
            continue  # Workday prefilled it (from the account or resume parse)
        # sensitive answers are NEVER trusted from a saved draft or resume parse: always re-answered from the
        # approved profile (or blocked) - a stale 'Yes' to foreign work authorization went out this way (11/6)
        # voluntary disclosures -> decline when required
        if f["type"] == "checkbox" and ("Self Identify" in step or "Disclosure" in step):
            # disability / veteran self-ID as a checkbox group: tick the "I do not want to answer" box
            boxes = loc.locator("input[type=checkbox]")
            dec = None
            for b_i in range(boxes.count()):
                bid = boxes.nth(b_i).get_attribute("id") or ""
                lab = page.locator(f"label[for='{bid}']").first.inner_text().strip() if bid else ""
                if DECLINE_RX.search(lab):
                    dec = (boxes.nth(b_i), lab)
                    break
            if dec:
                if not dec[0].is_checked():
                    dec[0].check(force=True)
                log.append({"label": label, "key": "self_identify", "value": dec[1], "ok": True})
                continue
        if key in DECLINE_KEYS or re.search(r"disabilit|veteran|gender|ethnic|race", label, re.I):
            if not req:
                continue
            if f["type"] == "select":
                loc.locator("button[aria-haspopup='listbox']").click()
                page.wait_for_timeout(600)
                opts = _all_listbox_texts(page)
                page.keyboard.press("Escape")
                pick = next((o for o in opts if DECLINE_RX.search(o)), None)
                if not pick and re.search(r"veteran", label, re.I) and pr.get("veteran_fallback"):
                    # required, no decline option: answer truthfully (service-disabled veteran -> protected veteran)
                    pick = next((o for o in opts if re.search(r"identify as (a |one or more )?.*protected veteran|^i am a protected veteran", o, re.I)), None)
                if pick:
                    p2, _ = _choose_listbox(page, loc, pick)
                    log.append({"label": label, "key": key or "disclosure", "value": p2 or pick, "ok": bool(p2)})
                    if not p2:
                        blockers.append(f"could not select '{pick}' for '{label[:80]}'")
                else:
                    blockers.append(f"required disclosure without a decline option: '{label[:80]}' {opts[:6]}")
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
        if key == "truth_certification" and pr.get("answer_policy", {}).get("e_sign_when_all_answers_from_profile"):
            if f["type"] in ("checkbox",):
                _tick(page, loc)
            elif f["type"] == "select":
                _choose_listbox(page, loc, "Yes")
            elif f["type"] in ("text", "textarea"):
                loc.locator("input, textarea").first.fill(pr["contact"]["name"])
            log.append({"label": label, "key": "truth_certification", "value": "<certified (approved 11/4)>", "ok": True})
            continue
        if f["type"] == "checkbox" and key in ("us_citizen", "citizenship_country") and str((pr.get("approved_answers") or {}).get("us_citizen")).lower().startswith("yes"):
            # "Indicate which, if any, where you are a citizen" -> a country checklist: tick United States only
            boxes = loc.locator("input[type=checkbox]")
            us = None
            for b_i in range(boxes.count()):
                bid = boxes.nth(b_i).get_attribute("id") or ""
                lab = page.locator(f"label[for='{bid}']").first.inner_text().strip() if bid else ""
                lab = lab or (boxes.nth(b_i).get_attribute("aria-label") or "")
                if re.fullmatch(r"(the )?united states( of america)?|usa?|u\.s\.(a\.)?", lab.strip(), re.I):
                    us = boxes.nth(b_i)
                    break
            if us is None and str((pr.get("approved_answers") or {}).get("other_citizenships", "")).lower() == "none":
                # country checklist without the US (export-control screens: Cuba/Iran/...): "None of these" is true
                # only for a US-only citizen -> needs the approved other_citizenships: none
                for b_i in range(boxes.count()):
                    bid = boxes.nth(b_i).get_attribute("id") or ""
                    lab = page.locator(f"label[for='{bid}']").first.inner_text().strip() if bid else ""
                    if re.fullmatch(r"none( of (these|the above))?|not applicable|n/?a", lab.strip(), re.I):
                        boxes.nth(b_i).check(force=True)
                        log.append({"label": label, "key": "us_citizen", "value": lab, "ok": True})
                        us = False
                        break
            if us is False:
                pass
            elif us is not None:
                us.check(force=True)
                log.append({"label": label, "key": "us_citizen", "value": "United States", "ok": True})
            else:
                blockers.append(f"citizenship checklist has no 'United States' box: '{label[:120]}'")
            continue
        if kind == "sensitive" and key == "attestation" or f["type"] == "checkbox":
            aid = attestation_id(label)
            pol = pr.get("answer_policy") or {}
            if aid in approved_att or (req and pol.get("accept_consents") and is_plain_consent(label)):
                try:
                    if f["type"] == "select":  # consent rendered as a Yes/No dropdown (BD)
                        pick = None
                        for cand in ("Yes", "I consent", "I agree", "Agree", "Accept"):
                            pick, _o = _choose_listbox(page, loc, cand)
                            if pick:
                                break
                        if not pick:
                            raise RuntimeError("no affirmative option")
                    else:
                        _tick(page, loc)
                    log.append({"label": label, "key": "attestation", "value": f"<consented {aid}>", "ok": True})
                except Exception:
                    blockers.append(f"could not tick approved box [{aid}]: '{label[:120]}'")
            else:
                blockers.append(f"attestation needs your explicit approval [{aid}]: '{label[:200]}'")
            continue
        # self-identification form signature (CC-305): name + today's date, only alongside a decline answer
        if re.search(r"^name$|your name|full name|signature|sign here|signed", label, re.I) and \
                ("Self Identify" in step or "Disclosure" in step) and f["type"] in ("text", "textarea", "other"):
            loc.locator("input").first.fill(pr["contact"]["name"])
            continue
        if f["type"] == "date" and ("Self Identify" in step or "Disclosure" in step):
            _fill_full_date(page, loc, date.today())  # signature date = today
            continue
        if f["type"] == "date" and key == "start_date" and \
                re.search(r"two weeks|2 weeks", str((pr.get("approved_answers") or {}).get("start_date", "")), re.I):
            from datetime import timedelta
            _fill_full_date(page, loc, date.today() + timedelta(days=14))  # approved: within two weeks of offer
            log.append({"label": label, "key": "start_date", "value": str(date.today() + timedelta(days=14)), "ok": True})
            continue
        if f["id"] == "skills" or re.search(r"type to add skills|^skills$", label, re.I):
            if loc.locator("[data-automation-id='selectedItem']").count() >= 1:
                continue  # already has skills (earlier pass or saved draft)
            added = 0
            for sk in ["Clinical Trials", "Project Management", "Good Clinical Practice", "REDCap", "Clinical Research"]:
                try:
                    before = loc.locator("[data-automation-id='selectedItem']").count()
                    inp = loc.locator("input").first
                    inp.click()
                    inp.fill(sk)
                    inp.press("Enter")
                    page.wait_for_timeout(1800)
                    cands = _open_options(page)
                    pick = next((t for t in cands if t.lower() == sk.lower()), None) or \
                        next((t for t in cands if sk.lower() in t.lower()), None) or (cands[0] if cands else None)
                    if pick:
                        page.locator(OPT).filter(has_text=re.compile(rf"^\s*{re.escape(pick)}\s*$")).first.click()
                        page.wait_for_timeout(900)
                    page.keyboard.press("Escape")
                    if loc.locator("[data-automation-id='selectedItem']").count() > before:
                        added += 1
                        log.append({"label": "Skills", "key": "skills", "value": pick, "ok": True})
                except Exception:
                    page.keyboard.press("Escape")
                if added >= 3:
                    break
            if not added and req:
                blockers.append("skills field: could not add any skill")
            continue
        val = _value_for(key, label, f, job, pr)
        if key == "salary_expectation" and val and re.search(r"currency", label, re.I) and "USD" not in str(val):
            val = f"{val} USD"
        if val in (None, "") and kind == "unknown":
            from ...evidence_answers import answer as evidence_answer
            opts_for_q = f.get("options", [])
            if f["type"] == "select" and not opts_for_q:  # read the listbox so choice questions get a listed option
                try:
                    loc.locator("button[aria-haspopup='listbox']").click()
                    page.wait_for_timeout(500)
                    opts_for_q = [t for t in _all_listbox_texts(page) if t != "Select One"]
                    page.keyboard.press("Escape")
                except Exception:
                    opts_for_q = []
            val = evidence_answer(label, opts_for_q, job)
        if val in (None, ""):
            blockers.append(f"{'custom question' if kind == 'unknown' else (key or 'field').replace('_', ' ')} "
                            f"needs your answer: '{label[:160]}'")
            continue
        try:
            if f["type"] == "select":
                cands = [str(val)]
                if f["id"] == "degree" or key in ("degree", "education_level"):
                    cands = ["Master of Arts", "Master's Degree", "Masters Degree", "Master Degree", "Masters", "Master's",
                             "Master", "MA", "M.A.", "Graduate Degree", str(val)]
                elif f["id"] in ("fieldOfStudy", "fieldsOfStudy") or key == "discipline":
                    # closest truthful entries for an MA in International Studies; "Other" is always true
                    cands = [str(val), "International Relations", "International Affairs", "Global Studies", "Other"]
                pick = opts = None
                for cand in cands:
                    pick, opts = _choose_listbox(page, loc, cand)
                    if pick:
                        break
                if not pick and (key == "how_did_you_hear" or f["id"] == "source") and opts:
                    from .base import neutral_source_option
                    alt = neutral_source_option([o for o in opts if "(+" not in o])
                    if alt:
                        pick, opts = _choose_listbox(page, loc, alt)
                if not pick:  # virtualized list: type-ahead with the keyboard, then confirm what it landed on
                    btn = loc.locator("button[aria-haspopup='listbox']").first
                    for cand in cands:
                        try:
                            page.keyboard.press("Escape")
                            btn.click()
                            page.wait_for_timeout(400)
                            page.keyboard.type(cand.split()[0][:6], delay=90)
                            page.wait_for_timeout(500)
                            page.keyboard.press("Enter")
                            page.wait_for_timeout(600)
                            shown = btn.inner_text().strip()
                            if shown and shown != "Select One" and match_option(cand, [shown]):
                                pick = shown
                                break
                        except Exception:
                            continue
                if pick:  # verify the widget now shows the choice; Workday occasionally drops a click
                    ok_shown = False
                    for _ in range(3):
                        shown = loc.locator("button[aria-haspopup='listbox']").first.inner_text().strip()
                        if shown == pick or pick in shown:
                            ok_shown = True
                            break
                        page.wait_for_timeout(600)
                        btn = loc.locator("button[aria-haspopup='listbox']").first
                        btn.focus()
                        page.keyboard.press("Enter")  # keyboard path: open, type-ahead, confirm
                        page.wait_for_timeout(400)
                        page.keyboard.type(pick[:3], delay=80)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(500)
                    if not ok_shown:
                        blockers.append(f"selection did not stick for '{label[:80]}' (wanted '{pick}')")
                        continue
                if not pick:
                    full = loc.inner_text()[:1500].replace("\n", " ")
                    blockers.append(f"'{val}' matches no option for '{label[:80]}': {opts[:6]}"
                                    + (f" || FULL QUESTION: {full}" if all(len(o) <= 2 for o in opts if o != 'Select One') else ""))
                    continue
            elif f["type"] == "multiselect":
                pick, opts = _choose_multiselect(page, loc, str(val))
                if pick and is_fos and not FOS_OK.search(pick):
                    _unselect(page, loc, pick)
                    pick = None
                if not pick and is_fos:
                    for alt in ("International Relations", "International Affairs", "Global Studies", "Other"):
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)
                        try:
                            pick, _ = _choose_multiselect(page, loc, alt, exact=(alt == "Other"))
                            if pick and not FOS_OK.search(pick):
                                _unselect(page, loc, pick)
                                pick = None
                        except Exception:
                            pick = None
                        if pick:
                            break
                if not pick:
                    blockers.append(f"'{val}' matches no option for '{label[:80]}': {opts[:6]}")
                    continue
            elif f["type"] == "radio":
                pick = match_option(str(val), f["options"])
                if not pick:
                    blockers.append(f"'{val}' matches no option for '{label[:80]}': {f['options'][:6]}")
                    continue
                try:
                    loc.get_by_label(pick, exact=True).check(force=True, timeout=5000)
                except Exception:  # Workday radios: the label is the clickable element
                    loc.locator("label").filter(has_text=re.compile(rf"^\s*{re.escape(pick)}\s*$")).first.click()
                    page.wait_for_timeout(400)
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
    # some tenants first show "Sign in with Google / Sign in with email"
    em = page.get_by_role("button", name=re.compile(r"sign in with email", re.I))
    if em.count() and not page.locator(A("password")).count():
        em.first.click()
        page.wait_for_timeout(2500)
        if not credentials.get(url) and page.locator(A("createAccountLink")).count():
            page.click(A("createAccountLink"))
            page.wait_for_timeout(2500)
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
        if step.startswith("Create Account") or step.startswith("Sign In"):
            try:
                page.wait_for_selector(A("password"), timeout=30000)
                sign_in_or_create(page, url, pr, log)
            except WorkdayError as ex:
                raise Blocked([str(ex)])
            except Exception:
                pass
            if _step(page).startswith(("Create Account", "Sign In")):
                raise Blocked(["could not get past Workday sign-in (see screenshot)"])
            continue
        import os
        if os.environ.get("JOBBOT_WD_DUMP"):
            dump = page.evaluate("()=>[...document.querySelectorAll('[data-automation-id]')].filter(e=>e.offsetParent||e.type==='file')"
                                 ".map(e=>e.getAttribute('data-automation-id')+'|'+e.tagName+'|'+(e.type||'')+'|'"
                                 "+(e.innerText||e.value||'').trim().slice(0,50).replace(/\\n/g,' '))")
            (evid / f"dump_{re.sub(r'[^A-Za-z]+', '_', step)}.txt").write_text("\n".join(dump))
        blockers = fill_step(page, job, pr, app_row, log)
        if not blockers:  # answers can reveal follow-up questions (e.g. "If yes, please specify"): second pass
            page.wait_for_timeout(800)
            blockers = fill_step(page, job, pr, app_row, log)
        page.screenshot(path=str(evid / f"wd_{re.sub(r'[^A-Za-z]+', '_', step)}.png"), full_page=True)
        if blockers:
            raise Blocked([f"[{step}] {b}" for b in blockers])
        if "something went wrong" in page.inner_text("body").lower():
            continue  # loop top reloads (once) or stops cleanly
        page.locator(A("pageFooterNextButton")).click(timeout=60000)
        page.wait_for_timeout(6000)
        errs = page.locator(A("errorMessage")).all_inner_texts()
        if not errs and "errors found" in page.inner_text("body").lower():
            errs = [e for e in page.locator("[data-automation-id='errorBanner'], [role='alert']").all_inner_texts() if e.strip()] \
                or ["Workday reported 'Errors Found' on this step"]
        errs = [e for e in errs if not re.search(r"successfully (uploaded|saved)", e, re.I)]
        if not errs and "errors found" in page.inner_text("body").lower():
            errs = ["Workday reported 'Errors Found' on this step (see screenshot)"]
        if errs and _step(page) == step:
            raise Blocked([f"[{step}] Workday validation: {e[:160]}" for e in errs[:6]])
    raise Blocked(["Workday flow did not reach Review within 10 steps"])


def submit(page):
    page.click(A("pageFooterNextButton"))  # on Review, the footer button is "Submit"
