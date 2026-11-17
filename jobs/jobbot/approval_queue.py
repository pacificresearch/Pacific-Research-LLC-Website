"""Approval queue: you approve/reject prepared applications; auto-submit is a separate, explicit grant."""
from __future__ import annotations

from . import application_tracker as db

MIN_REVIEWED_FOR_AUTO = 5


def pending() -> list:
    return db.pipeline_rows(status="AWAITING_APPROVAL")


def approve(app_id: int, note: str = "") -> None:
    a = db.app(app_id)
    if a["status"] not in ("AWAITING_APPROVAL", "NEEDS_HUMAN_ACTION"):
        raise ValueError(f"app {app_id} is {a['status']}, not awaiting approval")
    db.update_app(app_id, approved_at=db.now(), approved_note=note or "approved")
    if a["status"] == "NEEDS_HUMAN_ACTION":
        db.transition(app_id, "AWAITING_APPROVAL", "approved after human action")


def promote(app_id: int, note: str = "near-miss promoted for your decision") -> None:
    """Move a below-threshold (SCREENED) job into preparation. It stays below the auto-submit bar."""
    a = db.app(app_id)
    if a["status"] != "SCREENED":
        raise ValueError(f"app {app_id} is {a['status']}; only SCREENED (below threshold) jobs can be promoted")
    db.transition(app_id, "QUALIFIED", f"promoted: {note}")


def reject(app_id: int, reason: str = "rejected by you") -> None:
    db.transition(app_id, "REJECTED", f"you: {reason}")


def mark_submitted_manually(app_id: int, confirmation: str) -> None:
    """You applied yourself (Workday/USAJOBS/Inspira). Confirmation text/ID is required."""
    if not confirmation.strip():
        raise ValueError("a confirmation number, email subject, or screenshot path is required")
    a = db.app(app_id)
    if a["status"] in ("AWAITING_APPROVAL", "MATERIALS_READY"):
        db.transition(app_id, "NEEDS_HUMAN_ACTION", "applied manually")
    db.transition(app_id, "SUBMITTED", "applied manually by you", submitted_at=db.now(),
                  confirmation=confirmation.strip()[:500])


def authorize_auto_submit(confirm_text: str) -> str:
    """Enable Authorized Auto-Submit Mode — only after you reviewed real completed applications."""
    reviewed = db.connect().execute(
        "SELECT COUNT(*) FROM applications WHERE approved_at IS NOT NULL AND status IN ('SUBMITTED','INTERVIEW','OFFER')"
    ).fetchone()[0]
    if reviewed < MIN_REVIEWED_FOR_AUTO:
        raise PermissionError(f"auto-submit needs at least {MIN_REVIEWED_FOR_AUTO} applications you approved and that "
                              f"were confirmed submitted; you have {reviewed}")
    if confirm_text.strip() != "I authorize automatic submission of standard applications":
        raise PermissionError('type exactly: "I authorize automatic submission of standard applications"')
    db.set_setting("mode", "auto")
    db.set_setting("auto_submit_authorized", {"at": db.now(), "reviewed": reviewed})
    return "Authorized Auto-Submit Mode enabled. Attestations, unknown questions, CAPTCHAs and assessments still pause."


def revoke_auto_submit() -> None:
    db.set_setting("mode", "review")
    db.set_setting("auto_submit_authorized", None)


def auto_eligible(row) -> bool:
    """Standard application: strong score, clean eligibility, high confidence, automatable ATS."""
    from .application_executor import AUTOMATABLE, route
    return (row["score"] or 0) >= 80 and row["eligibility"] == "pass" and (row["confidence"] or 0) >= 0.75 \
        and route({"apply_url": row["apply_url"]}) in AUTOMATABLE
