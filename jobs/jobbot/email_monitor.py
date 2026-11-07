"""Email follow-up: classify ATS/recruiter mail and match it to applications.

Read-only by design: never sends, replies, accepts, declines, or withdraws. Follow-up
drafts are written as .eml files under data/drafts/ for you to send yourself.

Inputs (choose one):
  * IMAP with an app password: JOBBOT_IMAP_HOST, JOBBOT_IMAP_USER, JOBBOT_IMAP_PASSWORD
    (Gmail: imap.gmail.com; Outlook.com: outlook.office365.com — Microsoft may require OAuth)
  * `jobbot import-emails file.json` with [{message_id, received, sender, subject, body}],
    e.g. exported by a Claude session through the Gmail/Outlook connector.
"""
from __future__ import annotations

import email
import imaplib
import json
import os
import re
from email.header import decode_header, make_header
from email.message import EmailMessage

from . import application_tracker as db
from .config import path

RULES = [
    ("interview", r"\binterview\b|schedule (a )?(call|time|chat)|phone screen|availability for|meet with|next steps? in (the|our) process"),
    ("rejection", r"not (be )?(moving|proceed)\w* forward|other candidates|unfortunately|position has been filled|"
                  r"no longer (being )?considered|decided not to|regret to inform"),
    ("offer", r"\boffer letter\b|pleased to offer|extend (an|the) offer"),
    ("assessment", r"assessment|questionnaire|complete (the|this) (test|survey)|hirevue|codility|video interview"),
    ("confirmation", r"thank you for (applying|your application|your interest)|application (was |has been )?received|"
                     r"we('ve| have) received your application|application submitted"),
    ("recruiter", r"recruit|talent acquisition|came across your (profile|resume)|opportunity that"),
]


def classify(subject: str, body: str) -> str:
    t = f"{subject}\n{body}".lower()
    for label, rx in RULES:
        if re.search(rx, t):
            return label
    return "other"


def match_application(sender: str, subject: str, body: str) -> int | None:
    t = f"{sender} {subject} {body[:4000]}".lower()
    best, best_score = None, 0
    for r in db.connect().execute(
            """SELECT a.id, j.employer, j.title FROM applications a JOIN jobs j ON j.id=a.job_id
               WHERE a.status IN ('SUBMITTED','CONFIRMATION_PENDING','INTERVIEW','NEEDS_HUMAN_ACTION','SUBMITTING')"""):
        emp = re.sub(r"\(.*?\)|\b(inc|llc|plc|corp|corporation|systems|sciences|health)\b", "", r["employer"].lower()).strip()
        emp_tokens = [w for w in re.findall(r"[a-z0-9]{3,}", emp)]
        s = sum(2 for w in emp_tokens if w in t)
        s += sum(1 for w in re.findall(r"[a-z]{4,}", r["title"].lower()) if w in t)
        if s > best_score:
            best, best_score = r["id"], s
    return best if best_score >= 3 else None


def ingest(msg: dict) -> dict:
    cls = classify(msg.get("subject", ""), msg.get("body", ""))
    app_id = match_application(msg.get("sender", ""), msg.get("subject", ""), msg.get("body", ""))
    attention = cls in ("interview", "offer", "assessment", "recruiter")
    with db.tx() as con:
        cur = con.execute("""INSERT OR IGNORE INTO emails(message_id,received,sender,subject,classification,application_id,
                             snippet,needs_attention) VALUES(?,?,?,?,?,?,?,?)""",
                          (msg["message_id"], msg.get("received"), msg.get("sender"), msg.get("subject"), cls, app_id,
                           (msg.get("body") or "")[:400], int(attention)))
        if cur.rowcount == 0:
            return {"duplicate": True}
    if app_id:
        a = db.app(app_id)
        try:
            if cls == "confirmation" and a["status"] in ("CONFIRMATION_PENDING", "NEEDS_HUMAN_ACTION"):
                db.transition(app_id, "SUBMITTED", "confirmation email", submitted_at=a["submitted_at"] or db.now(),
                              confirmation=f"email: {msg.get('subject', '')[:200]}",
                              confirmation_evidence=f"email {msg['message_id']}")
            elif cls == "rejection" and a["status"] in ("SUBMITTED", "CONFIRMATION_PENDING", "INTERVIEW"):
                db.transition(app_id, "REJECTED", f"employer: {msg.get('subject', '')[:200]}")
            elif cls == "interview" and a["status"] in ("SUBMITTED", "CONFIRMATION_PENDING"):
                db.transition(app_id, "INTERVIEW", f"interview request: {msg.get('subject', '')[:200]}")
            elif cls == "offer" and a["status"] in ("SUBMITTED", "INTERVIEW"):
                db.transition(app_id, "OFFER", f"offer: {msg.get('subject', '')[:200]}")
        except db.TransitionError:
            pass
    return {"classification": cls, "application_id": app_id, "needs_attention": attention}


def poll_imap(since_days: int = 14, folder: str = "INBOX") -> dict:
    host, user, pw = (os.environ.get(k) for k in ("JOBBOT_IMAP_HOST", "JOBBOT_IMAP_USER", "JOBBOT_IMAP_PASSWORD"))
    if not (host and user and pw):
        return {"skipped": "IMAP not configured (JOBBOT_IMAP_HOST/USER/PASSWORD)"}
    from datetime import date, timedelta
    stats = {"read": 0, "matched": 0, "attention": 0}
    with imaplib.IMAP4_SSL(host) as M:
        M.login(user, pw)
        M.select(folder, readonly=True)  # read-only: never marks, moves or deletes
        since = (date.today() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        _, ids = M.search(None, f'(SINCE "{since}")')
        for num in ids[0].split()[-500:]:
            _, data = M.fetch(num, "(BODY.PEEK[])")
            m = email.message_from_bytes(data[0][1])
            body = ""
            for part in m.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
                    break
            res = ingest({"message_id": m.get("Message-ID") or f"imap-{num.decode()}",
                          "received": m.get("Date"), "sender": str(make_header(decode_header(m.get("From", "")))),
                          "subject": str(make_header(decode_header(m.get("Subject", "")))), "body": body})
            if not res.get("duplicate"):
                stats["read"] += 1
                stats["matched"] += bool(res.get("application_id"))
                stats["attention"] += bool(res.get("needs_attention"))
    return stats


def import_file(fp: str) -> dict:
    stats = {"read": 0, "matched": 0, "attention": 0}
    for msg in json.load(open(fp)):
        res = ingest(msg)
        if not res.get("duplicate"):
            stats["read"] += 1
            stats["matched"] += bool(res.get("application_id"))
            stats["attention"] += bool(res.get("needs_attention"))
    return stats


def followup_drafts(days_after: int = 10) -> list[str]:
    """Polite check-in drafts for applications with no response after N days. Never sent automatically."""
    from datetime import datetime, timedelta, timezone
    from .evidence import profile
    pr = profile()
    out = []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_after)).isoformat()
    for r in db.connect().execute(
            """SELECT a.id, a.submitted_at, j.employer, j.title FROM applications a JOIN jobs j ON j.id=a.job_id
               WHERE a.status='SUBMITTED' AND a.submitted_at < ? AND
               NOT EXISTS (SELECT 1 FROM emails e WHERE e.application_id=a.id AND e.classification!='confirmation')""",
            (cutoff,)):
        m = EmailMessage()
        m["From"] = pr["contact"]["email"]
        m["To"] = ""
        m["Subject"] = f"Following up: {r['title']} application"
        m.set_content(f"Hello,\n\nI applied for the {r['title']} role at {r['employer']} on {r['submitted_at'][:10]} and "
                      f"wanted to confirm my application was received. I remain very interested and would be glad to "
                      f"share anything further that would be helpful.\n\nThank you,\n{pr['contact']['name']}\n")
        f = path("drafts", f"followup_app_{r['id']:05d}.eml")
        if not f.exists():
            f.write_bytes(bytes(m))
            db.update_app(r["id"], follow_up_date=db.today())
            out.append(str(f))
    return out


def fetch_security_code(max_age_minutes: int = 15) -> str | None:
    """Latest ATS security code (Greenhouse etc.) from the IMAP inbox, if IMAP is configured."""
    host, user, pw = (os.environ.get(k) for k in ("JOBBOT_IMAP_HOST", "JOBBOT_IMAP_USER", "JOBBOT_IMAP_PASSWORD"))
    if not (host and user and pw):
        return None
    try:
        with imaplib.IMAP4_SSL(host) as M:
            M.login(user, pw)
            M.select("INBOX", readonly=True)
            _, ids = M.search(None, '(SUBJECT "security code")')
            for num in reversed(ids[0].split()[-5:]):
                _, data = M.fetch(num, "(BODY.PEEK[])")
                m = email.message_from_bytes(data[0][1])
                from email.utils import parsedate_to_datetime
                from datetime import datetime, timezone
                if (datetime.now(timezone.utc) - parsedate_to_datetime(m["Date"])).total_seconds() > max_age_minutes * 60:
                    continue
                body = ""
                for part in m.walk():
                    if part.get_content_type() in ("text/plain", "text/html"):
                        body += part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
                c = re.search(r"\b([A-Za-z0-9]{8})\b(?=[^A-Za-z0-9]*(?:</|\n|$))", body)
                if c:
                    return c.group(1)
    except Exception:
        return None
    return None
