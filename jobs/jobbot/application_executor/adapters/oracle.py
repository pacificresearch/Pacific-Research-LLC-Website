"""Oracle Recruiting Cloud (HCM Candidate Experience) — Stanford, UCSF, Mayo, Providence, Cedars-Sinai,
Mount Sinai, Vanderbilt (Andrew 11/18: "we need ROI" — the academic medical centers were packets only).

Flow: /job/<id>/apply/email -> email (+ terms) -> section 1..N (contact/address, application questions,
education/documents/veteran, diversity, e-signature) -> Submit.

Email: Oracle asks a returning email for a one-time PIN that does not reach the Gmail connector, so each
application uses a Gmail plus-alias of the application inbox (local+<site><app>@gmail.com). Mail to the alias
lands in the same inbox; nothing about the candidate changes.

Answers follow the same policy as the Workday adapter: approved answers and Andrew's overrides first, then
evidence-only answers; optional voluntary disclosures skipped; required disclosures -> a decline option
(or the approved forced answer); anything required without an approved answer -> Blocked.
"""
from __future__ import annotations

import re

from ..guards import classify, match_option, salary_answer, scope_work_auth
from .base import DECLINE_KEYS, DECLINE_RX, captcha_visible
from .workday import _override, _value_for

ROWS_JS = r"""
() => { document.querySelectorAll('[data-jobbot-or]').forEach(e => e.removeAttribute('data-jobbot-or'));
  return [...document.querySelectorAll('.input-row')].filter(r => r.offsetParent).map((r, i) => {
  r.setAttribute('data-jobbot-or', String(i));
  const lab = r.querySelector('label.input-row__label, legend, .input-row__label');
  const label = lab ? lab.innerText.replace(/\s+/g, ' ').trim() : '';
  const required = !!(lab && lab.className.includes('--required')) || !!r.querySelector('[aria-required=true]');
  const pills = [...r.querySelectorAll('button[role=radio], button[role=checkbox]')];
  const combo = r.querySelector('input[role=combobox]');
  const cbs = [...r.querySelectorAll('input[type=checkbox]')];
  const ta = r.querySelector('textarea');
  const inp = r.querySelector('input[type=text]:not([role=combobox]), input[type=email], input[type=tel], input[type=url], input[type=number], input:not([type])');
  const date = r.querySelector('input[placeholder*="/"], .input-row--date, oj-input-date');
  let type = pills.length ? 'pills' : combo ? 'combo' : cbs.length ? 'checkbox' : ta ? 'textarea' : inp ? 'text' : 'other';
  const options = pills.length ? pills.map(b => b.innerText.trim()) : cbs.map(c => { const l = document.querySelector(`label[for='${c.id}']`); return l ? l.innerText.trim() : c.value; });
  const chosen = pills.filter(b => b.getAttribute('aria-checked') === 'true').map(b => b.innerText.trim());
  const value = combo ? combo.value : ta ? ta.value : inp ? inp.value : chosen.join('|');
  return {i, label, required, type, options, value, multi: !!r.querySelector('button[role=checkbox]'),
          contact: !!r.querySelector('input[type=tel], input[name=email], input[name=firstName], input[name=lastName]'),
          name: (combo || inp || ta || {}).name || ''};
}); }
"""

NUM = re.compile(r"^\d+\.\s*")


class OracleError(Exception):
    pass


def _row(page, f):
    return page.locator(f"[data-jobbot-or='{f['i']}']")


def _alias(pr: dict, job: dict, app_row) -> str:
    # Oracle folds Gmail "+" aliases into the base address (and its PIN mail never reaches the Gmail connector),
    # so applications use a plus-alias on the PRG domain, whose mailbox the session can read for PINs/replies.
    base = pr.get("oracle_email_base") or "andrew@pacificresearchllc.com"
    local, dom = base.split("@")
    site = re.sub(r"[^a-z]", "", (job.get("employer") or "x").lower())[:10]
    return f"{local}+{site}{job['id']}@{dom}"


def _wait_pin(seconds: int) -> str | None:
    """Same hand-off as the Greenhouse code: the session reads the PIN from the PRG mailbox and writes it."""
    import time
    from ...config import path
    want, got = path("waiting_for_code.txt"), path("verification_code.txt")
    got.unlink(missing_ok=True)
    want.write_text("oracle PIN\n")
    end = time.time() + max(seconds, 0)
    while time.time() < end:
        if got.exists() and got.read_text().strip():
            c = re.sub(r"\D", "", got.read_text())
            got.unlink(missing_ok=True)
            want.unlink(missing_ok=True)
            return c
        time.sleep(5)
    want.unlink(missing_ok=True)
    return None


def _dismiss_cookies(page):
    btn = page.locator(".cookie-consent-modal button:visible:has-text('Decline'), "
                       ".cookie-consent-modal button:visible:has-text('Reject')")
    if btn.count():
        btn.first.click()
        page.wait_for_timeout(800)


def _combo_pick(page, row, value: str) -> bool:
    inp = row.locator("input[role=combobox]").first
    inp.click()
    inp.fill("")
    inp.press_sequentially(value, delay=90)
    page.wait_for_timeout(2500)
    opts = row.locator("[role=gridcell], [role=option]")
    if not opts.count():
        page.wait_for_timeout(2500)
    texts = [t.strip() for t in opts.all_inner_texts()]
    if not texts:
        return False
    pick = match_option(value, texts)
    if pick is None:
        low = value.lower()
        pick = next((t for t in texts if t.lower().startswith(low)), None) or \
            next((t for t in texts if low in t.lower()), None)
    if pick is None:
        page.keyboard.press("Escape")
        return False
    opts.nth(texts.index(pick)).click()
    page.wait_for_timeout(1200)
    return True


def _combo_options(page, row) -> list[str]:
    tog = row.locator("button[id$='-toggle-button']:visible")
    if tog.count():
        tog.first.click(timeout=5000)
        page.wait_for_timeout(1500)
    else:
        inp = row.locator("input[role=combobox]:visible")
        if not inp.count():
            return []
        inp.first.click(timeout=5000)
        page.wait_for_timeout(1500)
    texts = [t.strip() for t in row.locator("[role=gridcell], [role=option]").all_inner_texts()]
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    return texts


def _combo_choose(page, row, option: str) -> bool:
    tog = row.locator("button[id$='-toggle-button']:visible")
    if tog.count():
        tog.first.click(timeout=5000)
        page.wait_for_timeout(1500)
    opts = row.locator("[role=gridcell], [role=option]")
    texts = [t.strip() for t in opts.all_inner_texts()]
    if option in texts:
        opts.nth(texts.index(option)).click()
        page.wait_for_timeout(1000)
        return True
    return _combo_pick(page, row, option)


def _answer(label: str, options: list[str], job: dict, pr: dict, kind: str):
    """Return (answer, source) or (None, reason)."""
    ans = pr.get("approved_answers", {}) or {}
    ov = _override(label)
    if ov is not None:
        return ov, "override"
    low = label.lower()
    if re.search(r"work permit.*under (the )?age (of )?18|under 18", low):
        na = next((o for o in options if re.match(r"not applicable", o, re.I)), None)
        return (na or "No"), "age"
    if re.search(r"salary.*negotiable|negotiable", low):
        return "Yes", "salary_negotiable"
    if re.search(r"desired (salary|pay)|salary (range|expectation)|expected (salary|compensation)", low):
        return salary_answer(ans.get("salary_expectation_rule"), job), "salary_rule"
    m = re.search(r"(?:current or former|former or current|previously (?:an? )?)\s*employee of (.+?)(\?|$| \()", low)
    if m or re.search(r"previously (worked|been employed)|ever (worked|been employed) (for|at|by)", low):
        org = (m.group(1) if m else job["employer"]).lower()
        prior = [p.lower() for p in pr.get("prior_employers", [])]
        # only the exact organization: Stanford University != Stanford Health Care
        hit = any(p in org and not re.search(r"health care|hospital|packard|\bshc\b|lpch", org) for p in prior)
        return ("Yes" if hit else "No"), "prior_employers"
    if re.search(r"sunet|email address ending in stanford\.edu", low):
        return ("Yes" if any("stanford" in p.lower() for p in pr.get("prior_employers", [])) else "No"), "prior_employers"
    _, key = classify(label)
    key = scope_work_auth(key, label, job) if key else key
    if key in DECLINE_KEYS:
        dec = next((o for o in options if DECLINE_RX.search(o)), None)
        return (dec, "decline") if dec else (None, f"disclosure:{key}")
    if key:
        val = _value_for(key, label, {"type": kind, "id": ""}, job, pr)
        if val not in (None, ""):
            return str(val), key
    from ...evidence_answers import answer as ev_answer
    val = ev_answer(label, options, job)
    if val:
        return val, "evidence"
    return None, f"no approved answer ({key or 'unclassified'})"


def _fill_contact(page, pr, job, alias, log):
    c, addr = pr["contact"], pr.get("address") or {}
    first, last = c["name"].split()[0], c["name"].split()[-1]
    vals = {"firstName": first, "lastName": last, "addressLine1": addr.get("line1"),
            "email": alias}
    for name, v in vals.items():
        box = page.locator(f"input[name={name}]:visible")
        if box.count() and v and not box.first.input_value() and box.first.is_editable():
            box.first.fill(v)
            log.append({"field": name, "value": v})
    tel = page.locator("input[type=tel]:visible")
    if tel.count() and not tel.first.input_value():
        tel.first.fill(re.sub(r"\D", "", c["phone"]))
        log.append({"field": "phone", "value": "(on file)"})
    z = page.locator("input[name=postalCode]:visible")
    if z.count() and not z.first.input_value() and addr.get("postal_code"):
        row = z.first.locator("xpath=ancestor::div[contains(@class,'input-row')][1]")
        _combo_pick(page, row, addr["postal_code"])
    for name, v in (("city", addr.get("city")), ("region2", addr.get("state")), ("region1", addr.get("county"))):
        box = page.locator(f"input[name={name}]:visible")
        if box.count() and v and not box.first.input_value():
            row = box.first.locator("xpath=ancestor::div[contains(@class,'input-row')][1]")
            if box.first.get_attribute("role") == "combobox":
                _combo_pick(page, row, v)
            else:
                box.first.fill(v)


def _upload(page, app_row, log):
    for lab, path in (("resume", app_row["resume_path"]), ("cover letter", app_row["cover_path"])):
        if not path:
            continue
        inp = page.locator(f"input[type=file][aria-label*='{lab.title()}' i], "
                           f"input[type=file][id^=attachment-upload]")
        # pick the input whose label mentions this document
        for k in range(inp.count()):
            el = inp.nth(k)
            lid = el.get_attribute("id") or ""
            ltxt = page.locator(f"label[for='{lid}']").all_inner_texts() if lid else []
            name = " ".join(ltxt + [el.get_attribute("aria-label") or ""]).lower()
            if lab in name:
                already = page.locator(f"button:has-text('REMOVE {lab.upper()}')").count()
                if not already:
                    el.set_input_files(path)
                    page.wait_for_timeout(4000)
                    log.append({"field": f"upload {lab}", "value": path.split("/")[-1]})
                break


def _do_section(page, job, pr, log) -> list[str]:
    blocked = []
    fields = page.evaluate(ROWS_JS)
    for f in fields:
        label = NUM.sub("", f["label"])
        if not label or f["name"] in ("firstName", "lastName", "middleNames", "email", "addressLine1", "addressLine2",
                                      "addressLine3", "city", "postalCode", "region1", "region2", "country",
                                      "phoneNumber", "addlAddressAttribute4") or f["type"] == "other" or \
                re.search(r"^(phone|country code|address|city|state|zip|county|email|first name|last name|middle name|"
                          r"title|suffix|preferred name|known as)\b", label, re.I) or f.get("contact"):
            continue
        if re.search(r"full name", label, re.I) and f["type"] == "text":
            if not f["value"]:
                _row(page, f).locator("input").first.fill(pr["contact"]["name"])
                log.append({"field": label, "value": pr["contact"]["name"], "source": "e-signature"})
            continue
        if f["value"] and f["type"] != "checkbox":
            continue
        _, key = classify(label)
        if not f["required"] and (key in DECLINE_KEYS or f["type"] == "checkbox" or
                                  re.search(r"ethnic|race|legal sex|gender|veteran|disab|link \d|website", label, re.I)):
            continue  # optional voluntary disclosure / optional extras: skip
        row = _row(page, f)
        opts = f["options"]
        if f["type"] == "combo":
            opts = _combo_options(page, row)
        val, src = _answer(label, opts, job, pr, f["type"])
        if val is None and key == "gender" and f["required"]:
            val, src = (pr.get("approved_answers") or {}).get("gender_forced"), "gender_forced"
        if val is None:
            if f["required"]:
                blocked.append(f"[Oracle] required question needs your answer: '{label[:200]}' {opts[:6]}")
            continue
        if f["type"] == "pills":
            pick = match_option(str(val), opts) or next((o for o in opts if o.lower().startswith(str(val).lower())), None)
            if pick is None:
                blocked.append(f"[Oracle] answer '{val}' not among options for '{label[:150]}' {opts[:6]}")
                continue
            row.locator("button[role=radio], button[role=checkbox]").nth(opts.index(pick)).click()
            val = pick
        elif f["type"] == "combo":
            pick = match_option(str(val), opts) if opts else None
            if not _combo_choose(page, row, pick or str(val)):
                if f["required"]:
                    blocked.append(f"[Oracle] could not select '{val}' for '{label[:150]}'")
                continue
        elif f["type"] in ("text", "textarea"):
            row.locator("textarea, input").first.fill(str(val))
        elif f["type"] == "checkbox":
            if str(val).lower().startswith(("yes", "i agree", "agree", "true")):
                row.locator("input[type=checkbox]").first.check(force=True)
        log.append({"field": label[:200], "value": str(val)[:200], "source": src})
        page.wait_for_timeout(400)
    return blocked


def open_and_fill(page, url, job, pr, app_row, evid, wait_human_seconds=0):
    from .. import Blocked
    base = re.sub(r"(/job/\d+).*$", r"\1", url)
    page.goto(base + "/apply/email", wait_until="networkidle", timeout=90000)
    page.wait_for_timeout(3000)
    body = page.inner_text("body")
    if re.search(r"no longer (available|accepting)|job (has been )?(closed|filled)|not found", body, re.I) and \
            not page.locator("input[type=email]").count():
        raise Blocked(["POSTING CLOSED: Oracle page says the job is unavailable"])
    _dismiss_cookies(page)
    alias = _alias(pr, job, app_row)
    page.get_by_label(re.compile("Email", re.I)).first.fill(alias)
    terms = page.locator("label[for=legal-disclaimer-checkbox]")
    if terms.count():
        terms.first.click(position={"x": 5, "y": 5})
        page.wait_for_timeout(1200)
        agree = page.locator("button:visible:has-text('Agree')")
        if agree.count():
            agree.first.click()
            page.wait_for_timeout(800)
    page.locator("button:visible:has-text('Next')").first.click()
    page.wait_for_timeout(9000)
    if page.locator("#pin-code-1:visible").count():
        code = _wait_pin(wait_human_seconds)
        if not code:
            raise OracleError(f"Oracle emailed a PIN to {alias}; no code provided in time")
        for k, ch in enumerate(code[:6]):
            page.fill(f"#pin-code-{k + 1}", ch)
        page.locator("button:visible:has-text('Verify')").first.click()
        page.wait_for_timeout(9000)
    if captcha_visible(page):
        raise Blocked(["human verification on the Oracle sign-in page — not bypassed"])
    log: list[dict] = [{"field": "email (alias of application inbox)", "value": alias}]
    blocked: list[str] = []
    for step in range(8):
        _dismiss_cookies(page)
        if step == 0 or page.locator("input[name=postalCode]:visible").count():
            _fill_contact(page, pr, job, alias, log)
            for nm in ("city", "region2", "postalCode", "addressLine1", "lastName", "firstName"):
                box = page.locator(f"input[name={nm}]:visible")
                if box.count() and not box.first.input_value().strip():
                    raise Blocked([f"[Oracle] contact field '{nm}' did not fill — not submitting"])
        _upload(page, app_row, log)
        blocked += _do_section(page, job, pr, log)
        if blocked:
            raise Blocked(blocked)
        if page.locator("button:visible:has-text('Submit')").count():
            errs = page.locator(".input-row--invalid:visible")
            if errs.count():
                raise Blocked([f"[Oracle] field still invalid before submit: "
                               f"{errs.first.inner_text()[:200]}"])
            return log
        page.locator("button:visible:has-text('Next')").first.click()
        page.wait_for_timeout(6000)
        inval = page.locator(".input-row--invalid:visible")
        if inval.count() and "section" in page.url and step > 0:
            # Next did not advance: report what is invalid
            msgs = [t.replace("\n", " ")[:160] for t in inval.all_inner_texts()[:5]]
            raise Blocked([f"[Oracle] could not advance — invalid: {msgs}"])
    raise OracleError("Oracle flow did not reach the Submit step")


def submit(page):
    page.locator("button:visible:has-text('Submit')").last.click()
    page.wait_for_timeout(8000)
