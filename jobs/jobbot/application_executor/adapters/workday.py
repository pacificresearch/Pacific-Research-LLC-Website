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
    page.locator("[role='option']", has_text=pick).first.click()
    page.wait_for_timeout(400)
    return pick, texts


def _choose_multiselect(page, field, text):
    inp = field.locator("input").first
    inp.fill(text)
    inp.press("Enter")
    page.wait_for_timeout(1200)
    opts = page.locator("[data-automation-id='promptOption'], [role='option']")
    texts = [opts.nth(k).inner_text().strip() for k in range(min(opts.count(), 40))]
    pick = match_option(text, texts) or (texts[0] if len(texts) == 1 else None)
    if not pick and re.search(r"website|career", text, re.I):  # "How did you hear": company site wording varies
        pick = next((t for t in texts if re.search(r"(company|corporate|career).*(site|website|page)|careers? (site|page|website)|"
                                                    r"^website$|company website", t, re.I)), None)
    if not pick:
        page.keyboard.press("Escape")
        return None, texts
    page.locator("[data-automation-id='promptOption'], [role='option']", has_text=pick).first.click()
    page.wait_for_timeout(600)
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
    if key == "previously_employed_here" or re.search(r"previously (worked|been employed)|worked for .* before", label, re.I):
        return ans.get("previously_employed_here")
    return ans.get(key)


def fill_step(page, job, pr, app_row, log) -> list[str]:
    """Fill the current Workday step. Returns blockers (empty = step complete)."""
    blockers = []
    approved_att = set(pr.get("approved_attestations", []) or [])
    step = _step(page)
    # resume upload lives on My Experience
    up = page.locator(A("file-upload-input-ref"))
    if up.count() and not page.locator(A("file-upload-successful")).count():
        up.first.set_input_files(app_row["resume_path"])
        page.wait_for_timeout(5000)
        log.append({"label": "Resume upload", "key": "resume", "value": "<file:resume.pdf>", "ok": True})
    fields = page.evaluate(FIELDS_JS)
    for f in fields:
        label = f["label"].rstrip("*").strip()
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
        if val in (None, ""):
            blockers.append(f"{'custom question' if kind == 'unknown' else (key or 'field').replace('_', ' ')} "
                            f"needs your answer: '{label[:160]}'")
            continue
        try:
            if f["type"] == "select":
                pick, opts = _choose_listbox(page, loc, str(val))
                if not pick:
                    blockers.append(f"'{val}' matches no option for '{label[:80]}': {opts[:6]}")
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
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2500)
    _accept_cookies(page)
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
    for _ in range(10):
        step = _step(page)
        if step.startswith("Review"):
            return log
        blockers = fill_step(page, job, pr, app_row, log)
        page.screenshot(path=str(evid / f"wd_{re.sub(r'[^A-Za-z]+', '_', step)}.png"), full_page=True)
        if blockers:
            raise Blocked([f"[{step}] {b}" for b in blockers])
        page.click(A("pageFooterNextButton"))
        page.wait_for_timeout(4500)
        errs = page.locator(A("errorMessage")).all_inner_texts()
        if errs and _step(page) == step:
            raise Blocked([f"[{step}] Workday validation: {e[:160]}" for e in errs[:6]])
    raise Blocked(["Workday flow did not reach Review within 10 steps"])


def submit(page):
    page.click(A("pageFooterNextButton"))  # on Review, the footer button is "Submit"
