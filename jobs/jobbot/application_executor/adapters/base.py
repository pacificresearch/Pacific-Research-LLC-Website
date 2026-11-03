"""Label-driven form scanning and filling shared by every ATS adapter.

scan() tags each visible control with data-jobbot-idx and returns its label, type,
required flag and options. plan() decides a value for each control from the profile and
approved answers — or records a blocker. fill() applies the plan. Nothing is ever
guessed: unknown required questions and unapproved sensitive ones become blockers.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..guards import CAPTCHA_SELECTORS, attestation_id, classify, match_option, salary_answer

SCAN_JS = r"""
() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    if (el.type !== 'file' && (el.getAttribute('aria-hidden') === 'true' || parseFloat(s.opacity) === 0 || el.tabIndex === -1 && r.width < 3)) return false;
    return (r.width > 0 || r.height > 0 || el.type === 'file') && s.visibility !== 'hidden' && s.display !== 'none'; };
  const questionOf = el => {  // walk up to the element that holds the question text, excluding option labels
    let n = el.parentElement;
    for (let k = 0; k < 7 && n; k++, n = n.parentElement) {
      const q = n.querySelector(':scope > legend, :scope > .application-label, :scope > label:not(:has(input)), :scope > [class*="label"]:not(:has(input)), :scope > [class*="question"]:not(:has(input)), :scope > p, :scope > span:not(:has(input))');
      if (q && txt(q) && !n.matches('label')) return txt(q);
    }
    return '';
  };
  const txt = el => (el ? (el.innerText || el.textContent || '') : '').replace(/\s+/g, ' ').trim();
  const labelOf = el => {
    if (el.id) { const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l && txt(l)) return txt(l); }
    if (el.getAttribute('aria-labelledby')) {
      const t = el.getAttribute('aria-labelledby').split(/\s+/).map(i => txt(document.getElementById(i))).join(' ');
      if (t.trim()) return t; }
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
    const wrap = el.closest('label'); if (wrap && txt(wrap)) return txt(wrap);
    const fs = el.closest('fieldset'); if (fs && fs.querySelector('legend')) return txt(fs.querySelector('legend'));
    const grp = el.closest('[class*="question"], [class*="field"], [class*="application-question"], li, .form-group');
    if (grp) { const l = grp.querySelector('label, .label, .application-label, [class*="label"]'); if (l && txt(l)) return txt(l); }
    return el.getAttribute('placeholder') || el.name || '';
  };
  const out = []; let i = 0; const radios = {};
  for (const el of document.querySelectorAll('input, select, textarea')) {
    const type = (el.type || el.tagName).toLowerCase();
    if (['hidden', 'submit', 'button', 'image', 'reset', 'search'].includes(type)) continue;
    if (!vis(el) && type !== 'file') continue;
    if (type === 'radio' || type === 'checkbox') {
      const key = el.name || el.id;
      const optLabel = labelOf(el);
      const q = questionOf(el) || optLabel;
      if (type === 'radio') {
        if (!radios[key]) { radios[key] = {idx: i++, type: 'radio', name: key, label: q, required: el.required, options: []}; out.push(radios[key]); }
        el.setAttribute('data-jobbot-idx', `${radios[key].idx}:${radios[key].options.length}`);
        radios[key].options.push(optLabel); continue;
      }
      el.setAttribute('data-jobbot-idx', String(i));
      const single = !q || q === optLabel ? optLabel : (optLabel && optLabel.length > 25 ? optLabel : q + ' — ' + optLabel);
      out.push({idx: i++, type, name: el.name, label: single, required: el.required, options: []}); continue;
    }
    el.setAttribute('data-jobbot-idx', String(i));
    const f = {idx: i++, type, name: el.name || el.id, label: labelOf(el),
               required: el.required || el.getAttribute('aria-required') === 'true' || /\*\s*$/.test(labelOf(el)),
               options: type.startsWith('select') ? [...el.options].map(o => o.text.trim()) : [],
               value: type === 'file' ? '' : (el.value || '')};
    out.push(f);
  }
  return out;
}
"""


def captcha_visible(page) -> bool:
    for sel in CAPTCHA_SELECTORS:
        for el in page.locator(sel).all():
            try:
                box = el.bounding_box()
                if box and box["width"] > 40 and box["height"] > 40 and el.is_visible():
                    return True
            except Exception:
                continue
    return False


def scan(page) -> list[dict]:
    return page.evaluate(SCAN_JS)


def plan(fields: list[dict], job: dict, pr: dict, app_row, evid: Path) -> tuple[list[dict], list[str]]:
    c, ans = pr["contact"], pr.get("approved_answers", {}) or {}
    approved_att = set(pr.get("approved_attestations", []) or [])
    first, last = c["name"].split()[0], c["name"].split()[-1]
    routine = {"first_name": first, "last_name": last, "full_name": c["name"], "email": c["email"],
               "phone": c["phone"], "location": c["location"],
               "linkedin": c["linkedin"] if c["linkedin"].startswith("http") else "https://www." + c["linkedin"].removeprefix("www."),
               "website": ans.get("website"), "current_employer": ans.get("current_employer"),
               "current_title": ans.get("current_title"), "how_did_you_hear": ans.get("how_did_you_hear"),
               "country": ans.get("country") or "United States", "school": None, "degree": None, "discipline": None,
               "referred_by_employee": ans.get("referred_by_employee")}
    edu = (pr.get("education_structured") or [{}])[0]
    routine.update({k: edu.get(k) for k in ("school", "degree", "discipline") if edu.get(k)})
    routine["education_level"] = edu.get("degree")
    actions, blockers = [], []
    cover_txt = None
    if app_row["cover_path"]:
        p = Path(app_row["cover_path"]).with_name("cover_letter.txt")
        cover_txt = p.read_text() if p.exists() else None
    for f in fields:
        label = (f.get("label") or "").strip()
        if f.get("options") and f["type"].startswith("select"):
            for o in f["options"]:  # wrapping <label> also contains every option's text
                if o:
                    label = label.replace(o, " ")
            label = " ".join(label.split())
        kind, key = classify(label)
        req = bool(f.get("required"))
        act = {"idx": f["idx"], "type": f["type"], "label": label[:160], "kind": kind, "key": key}
        if f["type"] == "file":
            nm = (f.get("name") or "").lower()
            if kind == "unknown" and "cover" in nm:
                key = "cover_letter"
            if key == "cover_letter":
                if app_row["cover_path"]:
                    actions.append({**act, "file": app_row["cover_path"]})
                elif req:
                    blockers.append(f"required cover letter upload but none prepared: '{label[:80]}'")
            elif key == "resume" or re.search(r"resume|\bcv\b", (f.get("name") or "").lower()) or \
                    (not label and sum(1 for x in fields if x["type"] == "file") == 1):
                actions.append({**act, "file": app_row["resume_path"]})
            elif req:
                blockers.append(f"required upload not recognized: '{label[:80]}'")
            continue
        if kind == "routine":
            if key == "cover_letter" and f["type"] == "textarea":
                if cover_txt:
                    actions.append({**act, "value": cover_txt})
                elif req:
                    blockers.append(f"required cover letter text but none prepared: '{label[:80]}'")
                continue
            if key == "resume":
                continue
            val = routine.get(key)
            if val:
                if f["type"] in ("select-one", "radio"):
                    opt = match_option(val, f.get("options", []))
                    if opt:
                        actions.append({**act, "option": opt})
                    elif req:
                        blockers.append(f"no option matches '{val}' for '{label[:80]}'")
                elif f["type"] == "checkbox":
                    continue
                else:
                    actions.append({**act, "value": val})
            elif req:
                blockers.append(f"required field has no approved value: '{label[:100]}'")
            continue
        if kind == "sensitive":
            if key == "attestation":
                aid = attestation_id(label)
                if aid in approved_att:
                    actions.append({**act, "check": True, "attestation_id": aid})
                elif req:
                    blockers.append(f"attestation needs your explicit approval [{aid}]: '{label[:200]}'")
                # optional consent/marketing boxes are left unchecked
                continue
            if key == "license":
                if req:
                    blockers.append(f"licensing question: '{label[:120]}'")
                continue
            val = salary_answer(ans.get("salary_expectation_rule"), job) if key == "salary_expectation" else ans.get(key)
            if val is None:
                if req or f["type"] in ("select-one", "radio"):
                    blockers.append(f"{key.replace('_', ' ')} not approved: '{label[:120]}'")
                continue
            if f["type"] in ("select-one", "radio"):
                opt = match_option(str(val), f.get("options", []))
                if opt:
                    actions.append({**act, "option": opt})
                else:
                    blockers.append(f"approved {key} '{val}' matches no option {f.get('options', [])[:6]} for '{label[:80]}'")
            elif f["type"] == "checkbox":
                blockers.append(f"checkbox for {key} needs review: '{label[:100]}'")
            else:
                actions.append({**act, "value": str(val)})
            continue
        # unknown question
        if req:
            blockers.append(f"custom question needs your answer: '{label[:200]}'")
    if not any(a.get("file") == app_row["resume_path"] for a in actions):
        blockers.append("no resume upload field found")
    return actions, blockers


def fill(page, actions: list[dict]) -> list[dict]:
    log = []
    for a in actions:
        sel = f"[data-jobbot-idx='{a['idx']}']" if a["type"] != "radio" else None
        try:
            if a.get("file"):
                page.locator(sel).set_input_files(a["file"])
                page.wait_for_timeout(1200)
            elif a["type"] == "radio":
                loc = page.locator(f"[data-jobbot-idx^='{a['idx']}:']")
                for k in range(loc.count()):
                    el = loc.nth(k)
                    lab = el.evaluate("e => (document.querySelector(`label[for='${e.id}']`)||e.closest('label')||{}).innerText||''")
                    if lab.strip() == a["option"].strip():
                        el.check(force=True)
                        break
            elif a["type"].startswith("select"):
                page.locator(sel).select_option(label=a["option"])
            elif a.get("check"):
                page.locator(sel).check(force=True)
            elif "value" in a:
                el = page.locator(sel)
                el.fill(a["value"])
                if el.get_attribute("role") == "combobox" or el.get_attribute("aria-autocomplete"):
                    page.wait_for_timeout(700)
                    page.keyboard.press("ArrowDown")
                    page.keyboard.press("Enter")
            log.append({"label": a["label"], "key": a["key"], "kind": a["kind"],
                        "value": "<file:" + Path(a["file"]).name + ">" if a.get("file") else
                        a.get("option") or ("<checked>" if a.get("check") else
                                            (a.get("value", "")[:60] + ("…" if len(a.get("value", "")) > 60 else ""))),
                        "ok": True})
        except Exception as ex:
            log.append({"label": a["label"], "key": a["key"], "ok": False, "error": str(ex)[:200]})
    return log


def run_form(page, job, pr, app_row, evid, wait_human_seconds=0):
    from .. import Blocked
    if captcha_visible(page):
        if wait_human_seconds:
            page.wait_for_timeout(wait_human_seconds * 1000)
        if captcha_visible(page):
            raise Blocked(["human verification (CAPTCHA) shown before the form — not bypassed"])
    fields = scan(page)
    if not fields:
        raise Blocked(["no application form found on the page (posting may be closed or require sign-in)"])
    actions, blockers = plan(fields, job, pr, app_row, evid)
    if blockers:
        raise Blocked(blockers)
    log = fill(page, actions)
    bad = [l for l in log if not l["ok"]]
    if bad:
        raise Blocked([f"could not fill '{b['label'][:80]}': {b.get('error', '')[:80]}" for b in bad])
    return log
