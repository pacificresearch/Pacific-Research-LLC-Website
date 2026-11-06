"""Browser application executor (Playwright).

Runs on YOUR computer in a persistent, visible browser profile (jobs/data/browser) so
sign-ins are yours and a human can step in. Never bypasses CAPTCHAs or bot checks:
if one appears, the application pauses (headed: waits for you; unattended:
NEEDS_HUMAN_ACTION).

Modes:
  review   fill every field, screenshot, DO NOT submit -> stays AWAITING_APPROVAL
           (or NEEDS_HUMAN_ACTION listing exactly which questions need you)
  submit   only for approved applications (or auto-submit-eligible once authorized):
           re-fill, verify, record intent, click submit, verify confirmation
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from .. import application_tracker as db
from ..config import load_config, path
from ..evidence import profile
from . import adapters
from .guards import CONFIRM_RX, VALIDATION_RX

log = logging.getLogger("jobbot.executor")

AUTOMATABLE = {"greenhouse", "lever", "ashby", "workday"}
MANUAL_REASONS = {
    "usajobs": "USAJOBS applications are filed through Login.gov/USAJOBS — use the prepared federal packet",
    "inspira": "UN Inspira requires your account and Personal History Profile — use the prepared cover letter",
    "smartrecruiters": "SmartRecruiters forms vary by employer and often require an account — assisted mode",
    "indeed": "Indeed prohibits automated applications — apply via the employer site or manually",
    "linkedin": "LinkedIn prohibits automated applications — apply via the employer site or manually",
}


class Blocked(Exception):
    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def route(job: dict) -> str:
    url = (job.get("apply_url") or "").lower()
    if "greenhouse.io" in url or "gh_jid=" in url:
        return "greenhouse"
    if "lever.co" in url:
        return "lever"
    if "ashbyhq.com" in url:
        return "ashby"
    if "myworkdayjobs.com" in url or "myworkdaysite.com" in url:
        return "workday"
    if "usajobs.gov" in url:
        return "usajobs"
    if "careers.un.org" in url:
        return "inspira"
    if "smartrecruiters.com" in url:
        return "smartrecruiters"
    if "indeed.com" in url:
        return "indeed"
    if "linkedin.com" in url:
        return "linkedin"
    return "unsupported"


def _launch(headless: bool):
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    kw = {"headless": headless, "viewport": {"width": 1280, "height": 1600}, "accept_downloads": False}
    exe = Path("/opt/pw-browsers/chromium")
    try:
        ctx = pw.chromium.launch_persistent_context(str(path("browser", "x").parent), **kw)
    except Exception:
        import glob
        cands = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")
        if not cands:
            raise
        ctx = pw.chromium.launch_persistent_context(str(path("browser", "x").parent), executable_path=cands[0], **kw)
    return pw, ctx


def execute(app_id: int, mode: str = "review", headless: bool = False, wait_human_seconds: int = 0,
            url_override: str | None = None) -> dict:
    """Run one application. Returns a result dict; all state changes go through the tracker."""
    cfg = load_config()
    a = db.app(app_id)
    job = dict(db.job(a["job_id"]))
    pr = profile()
    kind = route({"apply_url": url_override or job["apply_url"]})
    if cfg.get("paused"):
        return {"app": app_id, "outcome": "paused"}
    if a["status"] not in ("AWAITING_APPROVAL", "MATERIALS_READY", "NEEDS_HUMAN_ACTION"):
        return {"app": app_id, "outcome": f"skipped: status {a['status']}"}
    if mode == "submit":
        if db.ever_clicked_submit(app_id):
            return {"app": app_id, "outcome": "refused: submit already clicked once — verify, never resubmit"}
        auto_ok = cfg.get("mode") == "auto" and db.get_settings().get("auto_submit_authorized")
        if not a["approved_at"] and not auto_ok:
            return {"app": app_id, "outcome": "refused: not approved (review mode)"}
        if db.employer_submissions_today(job["employer"]) >= cfg["max_per_employer_per_day"]:
            return {"app": app_id, "outcome": "deferred: employer daily cap"}
    if kind not in AUTOMATABLE:
        reason = MANUAL_REASONS.get(kind, "unsupported application system — manual with prepared packet")
        if a["status"] != "NEEDS_HUMAN_ACTION":
            db.transition(app_id, "NEEDS_HUMAN_ACTION", f"manual: {reason}",
                          needs_action=json.dumps({"type": "manual_ats", "ats": kind, "url": job["apply_url"],
                                                   "resume": a["resume_path"], "cover": a["cover_path"]}))
        return {"app": app_id, "outcome": "needs_human", "reason": reason}

    attempt = db.start_attempt(app_id, mode)
    evid = path("materials", f"app_{app_id:05d}", f"attempt_{attempt}", "x").parent
    pw = ctx = None
    try:
        if mode == "submit":
            db.transition(app_id, "SUBMITTING", "executor started (approved)")
        pw, ctx = _launch(headless)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        adapter = adapters.get(kind)
        log_fields = adapter.open_and_fill(page, url_override or job["apply_url"], job, pr, a, evid,
                                           wait_human_seconds=wait_human_seconds)
        page.screenshot(path=str(evid / "filled.png"), full_page=True)
        (evid / "field_log.json").write_text(json.dumps(log_fields, indent=2))
        if mode == "review":
            db.finish_attempt(attempt, "prefilled", evidence_dir=str(evid), field_log=log_fields)
            note = f"prefilled OK — screenshot {evid / 'filled.png'}"
            if a["status"] == "NEEDS_HUMAN_ACTION":
                db.transition(app_id, "AWAITING_APPROVAL", note)
            else:
                db.update_app(app_id, notes=note)
            return {"app": app_id, "outcome": "prefilled", "evidence": str(evid)}
        # ---- submit
        db.mark_submit_clicked(attempt)  # durable BEFORE the click
        adapter.submit(page)
        result = verify(page, evid, wait_human_seconds)
        db.finish_attempt(attempt, result["state"], evidence_dir=str(evid), field_log=log_fields)
        if result["state"] == "confirmed":
            db.transition(app_id, "SUBMITTED", "employer confirmation page",
                          submitted_at=db.now(), confirmation=result["text"][:500],
                          confirmation_evidence=str(evid / "confirmation.png"))
        elif result["state"] == "validation_error":
            db.transition(app_id, "NEEDS_HUMAN_ACTION", f"form rejected the submission: {result['text'][:300]}",
                          needs_action=json.dumps({"type": "validation", "detail": result["text"][:500],
                                                   "url": page.url}))
        elif result["state"] == "email_code":
            db.transition(app_id, "NEEDS_HUMAN_ACTION", "employer emailed a security code to the application email; "
                          "not submitted — retry when the code can be read",
                          needs_action=json.dumps({"type": "email_code", "url": page.url}))
        elif result["state"] == "captcha":
            db.transition(app_id, "NEEDS_HUMAN_ACTION", "human verification appeared at submit — not bypassed",
                          needs_action=json.dumps({"type": "captcha", "url": page.url}))
        else:
            db.transition(app_id, "CONFIRMATION_PENDING", "submit clicked; no confirmation page — check email")
        return {"app": app_id, "outcome": result["state"], "evidence": str(evid)}
    except Blocked as b:
        db.finish_attempt(attempt, "blocked", error="; ".join(b.reasons), evidence_dir=str(evid))
        if any(r.startswith("POSTING CLOSED") for r in b.reasons):
            with db.tx() as con:
                con.execute("UPDATE jobs SET active=0 WHERE id=?", (job["id"],))
            cur = db.app(app_id)["status"]
            if cur == "SUBMITTING":
                db.transition(app_id, "FAILED", "posting closed")
                cur = "FAILED"
            db.transition(app_id, "REJECTED", "posting closed by employer")
            return {"app": app_id, "outcome": "posting_closed"}
        cur = db.app(app_id)["status"]
        target = "NEEDS_HUMAN_ACTION"
        if cur != target:
            db.transition(app_id, target, "needs you: " + "; ".join(b.reasons)[:400],
                          needs_action=json.dumps({"type": "questions", "items": b.reasons}))
        else:
            db.update_app(app_id, needs_action=json.dumps({"type": "questions", "items": b.reasons}),
                          status_reason="needs you: " + "; ".join(b.reasons)[:400])
        return {"app": app_id, "outcome": "needs_human", "reasons": b.reasons}
    except Exception as ex:
        log.exception("executor error app %s", app_id)
        db.finish_attempt(attempt, "error", error=str(ex)[:1000], evidence_dir=str(evid))
        cur = db.app(app_id)["status"]
        if cur == "SUBMITTING":
            db.transition(app_id, "CONFIRMATION_PENDING" if db.ever_clicked_submit(app_id) else "FAILED",
                          f"executor error: {ex}"[:400])
        return {"app": app_id, "outcome": "error", "error": str(ex)}
    finally:
        try:
            if ctx:
                ctx.close()
            if pw:
                pw.stop()
        except Exception:
            pass


def _wait_for_code(page, evid: Path, wait_seconds: int):
    """Greenhouse-style emailed security code. The code is read from the inbox by IMAP (on your Mac) or
    written to $JOBBOT_HOME/verification_code.txt by a Claude session that read it through the Gmail
    connector. Typed into the form, then the form is re-submitted. Never guessed."""
    import time
    from ..email_monitor import fetch_security_code
    f = path("verification_code.txt")
    deadline = time.time() + max(wait_seconds, 0)
    while True:
        code = fetch_security_code() or (f.read_text().strip() if f.exists() else None)
        if code:
            f.unlink(missing_ok=True)
            boxes = page.locator("input[maxlength='1']")
            if boxes.count() >= len(code):
                for k, ch in enumerate(code):
                    boxes.nth(k).fill(ch)
            else:
                page.locator("input[name*='code'], input[id*='code']").first.fill(code)
            page.locator("button[type=submit], button:has-text('Submit')").first.click()
            return code
        if time.time() >= deadline:
            return None
        time.sleep(10)


def verify(page, evid: Path, wait_human_seconds: int = 0) -> dict:
    from .adapters.base import captcha_visible
    deadline_ms = 25000 + wait_human_seconds * 1000
    waited = 0
    while waited < deadline_ms:
        page.wait_for_timeout(1500)
        waited += 1500
        body = page.inner_text("body")[:20000]
        if CONFIRM_RX.search(body) or re.search(r"confirm|thank", page.url, re.I):
            page.screenshot(path=str(evid / "confirmation.png"), full_page=True)
            m = CONFIRM_RX.search(body)
            return {"state": "confirmed", "text": (m.group(0) if m else page.url) + f" | url={page.url}"}
        if re.search(r"verification code was sent|enter the \d+-character code|security code", body, re.I):
            code = _wait_for_code(page, evid, wait_human_seconds)
            if code is None:
                page.screenshot(path=str(evid / "email_code.png"), full_page=True)
                return {"state": "email_code", "text": "employer emailed a security code; not submitted"}
            continue
        if captcha_visible(page):
            if wait_human_seconds and waited < deadline_ms:
                continue  # a person at the keyboard may solve it; we never do
            page.screenshot(path=str(evid / "captcha.png"), full_page=True)
            return {"state": "captcha", "text": ""}
        inval = page.locator("[aria-invalid='true']").count()
        if inval and waited >= 6000:
            page.screenshot(path=str(evid / "validation.png"), full_page=True)
            m = VALIDATION_RX.search(body)
            return {"state": "validation_error", "text": m.group(0) if m else f"{inval} invalid fields"}
    page.screenshot(path=str(evid / "after_submit.png"), full_page=True)
    return {"state": "unconfirmed", "text": ""}
