"""Phases 2-3: qualify (screen + score + rank) and prepare materials. Idempotent."""
from __future__ import annotations

import json
import logging

from . import application_tracker as db
from . import cover_letter_builder, eligibility, job_scoring, resume_builder, semantic
from .config import load_config, load_yaml
from .evidence import evidence_lines, lexicon, profile

log = logging.getLogger("jobbot.pipeline")


def _tiers() -> dict:
    return {e["name"]: e.get("tier", 3) for e in (load_yaml("employers.yaml", {}) or {}).get("employers", [])}


def qualify(rescore: bool = False, use_semantic: bool | None = None) -> dict:
    """Screen + score every DISCOVERED (or, with rescore, every pre-materials) application."""
    cfg = load_config()
    terms = load_yaml("search.yaml", {})
    pr = profile()
    facts, lex, tiers = pr["facts"], lexicon(pr), _tiers()
    statuses = ("DISCOVERED", "SCREENED", "QUALIFIED") if rescore else ("DISCOVERED",)
    rows = db.connect().execute(
        f"SELECT a.id app_id, a.status, j.* FROM applications a JOIN jobs j ON j.id=a.job_id "
        f"WHERE a.status IN ({','.join('?' * len(statuses))}) AND j.active=1", statuses).fetchall()
    stats = {"screened": 0, "qualified": 0, "failed_eligibility": 0, "below_threshold": 0, "semantic": 0}
    scored = []
    for r in rows:
        job = dict(r)
        el = eligibility.screen(job, facts)
        sc = job_scoring.score(job, el, cfg, terms, tiers, lex)
        scored.append((r["app_id"], r["status"], job, el, sc))
    # semantic refinement for the top N per category that passed deterministic screening
    use_semantic = cfg["semantic"]["enabled"] if use_semantic is None else use_semantic
    if use_semantic and semantic.available():
        # Review until every job that could make today's shortlist has been reviewed (review can lower a
        # score, which promotes unreviewed jobs; keep going until the top 2x quota is all reviewed).
        from concurrent.futures import ThreadPoolExecutor
        ev = evidence_lines(pr)
        cap = cfg["semantic"].get("max_calls_per_category", 60)
        prior = {r["job_id"]: json.loads(r["semantic"]) for r in db.connect().execute(
            "SELECT job_id, semantic FROM assessments WHERE semantic IS NOT NULL")}
        for cat in ("A", "B", "C"):
            need = 2 * cfg["quotas"].get(cat, 10)
            calls = 0
            while calls < cap:
                live = sorted([x for x in scored if x[4]["category"] == cat and x[3]["eligibility"] != "fail"
                               and x[4]["score"] >= cfg["min_score"] - 5], key=lambda x: -x[4]["score"])[:need]
                todo = [x for x in live if not x[4].get("semantic")]
                if not todo:
                    break
                todo = todo[: min(len(todo), cap - calls, 10)]
                cached = [x for x in todo if x[2]["id"] in prior]
                fresh = [x for x in todo if x[2]["id"] not in prior]
                with ThreadPoolExecutor(max_workers=cfg["semantic"].get("workers", 5)) as ex:
                    sems = list(ex.map(lambda x: semantic.assess(x[2], ev, cfg["semantic"]["timeout_seconds"]), fresh))
                calls += len(fresh)
                for item, sem in list(zip(fresh, sems)) + [(x, prior[x[2]["id"]]) for x in cached]:
                    aid, st, job, el, sc = item
                    if not sem:
                        sem = {"qualifications_fit": sc["subscores"]["fit"], "interview_likelihood":
                               sc["subscores"]["interview"], "mandatory_requirements": [], "emphasize": [],
                               "one_line_rationale": "semantic review unavailable", "failed": True}
                    sc2, el2 = semantic.blend(sc, sem, el) if not sem.get("failed") else (dict(sc), el)
                    sc2["semantic"] = sem
                    scored[scored.index(item)] = (aid, st, job, el2, sc2)
                    stats["semantic"] += 0 if sem.get("failed") else 1
    for aid, st, job, el, sc in scored:
        db.save_assessment(job["id"], {**sc, **el, "semantic": sc.get("semantic")})
        if st == "DISCOVERED":
            db.transition(aid, "SCREENED", "screened")
            st = "SCREENED"
        stats["screened"] += 1
        if el["eligibility"] == "fail":
            fails = "; ".join(r["detail"] for r in el["eligibility_reasons"] if r["outcome"] == "fail")
            db.transition(aid, "REJECTED", f"screen: {fails}"[:500])
            stats["failed_eligibility"] += 1
        elif sc["score"] < cfg["min_score"]:
            if st == "QUALIFIED":
                db.transition(aid, "SCREENED", f"rescored below threshold ({sc['score']})")
            stats["below_threshold"] += 1
        else:
            if st != "QUALIFIED":
                db.transition(aid, "QUALIFIED", f"score {sc['score']} ({el['eligibility']})")
            stats["qualified"] += 1
    return stats


def shortlist(quotas: dict | None = None) -> dict[str, list]:
    """Ranked per-category shortlist of QUALIFIED/ready applications, honoring employer caps."""
    cfg = load_config()
    quotas = quotas or cfg["quotas"]
    out = {}
    for cat, n in quotas.items():
        from datetime import datetime, timedelta, timezone
        recent = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        # prepared work still in flight counts against today's quota (incl. manual Workday packets you
        # haven't filed yet), so parking an application never makes the system prepare more behind it
        rows = [r for r in db.pipeline_rows(category=cat, limit=2000)
                if r["status"] in ("QUALIFIED", "MATERIALS_READY", "AWAITING_APPROVAL")
                or (r["status"] == "NEEDS_HUMAN_ACTION" and r["updated_at"] >= recent)
                or (r["status"] in ("SUBMITTED", "CONFIRMATION_PENDING") and (r["submitted_at"] or r["updated_at"]) >= db.today())]
        picked, per_emp = [], {}
        for r in rows:
            if per_emp.get(r["employer"], 0) >= cfg["max_per_employer_per_day"]:
                continue
            per_emp[r["employer"]] = per_emp.get(r["employer"], 0) + 1
            picked.append(r)
            if len(picked) >= n:
                break
        out[cat] = picked
    return out


def prepare(app_ids: list[int], polish: bool = False, regenerate: bool = False) -> dict:
    """Phase 3: build tailored resume (+ cover letter when warranted) -> MATERIALS_READY -> AWAITING_APPROVAL."""
    stats = {"prepared": 0, "errors": {}}
    for aid in app_ids:
        a = db.app(aid)
        ok = ("QUALIFIED", "MATERIALS_READY") + (("AWAITING_APPROVAL", "NEEDS_HUMAN_ACTION") if regenerate else ())
        if a["status"] not in ok or (regenerate and a["approved_at"]):
            continue  # never swap materials under an approval you already gave
        job = dict(db.job(a["job_id"]))
        s = db.connect().execute("SELECT * FROM assessments WHERE job_id=?", (job["id"],)).fetchone()
        from .job_scoring import family_for
        fam = family_for(job, a["category"])
        sem = json.loads(s["semantic"]) if s["semantic"] else {}
        emph = sem.get("emphasize", [])
        try:
            res = resume_builder.build(aid, job, fam, emph)
            need, why = cover_letter_builder.needed(job, a["category"], s["score"] or 0)
            cov = cover_letter_builder.build(aid, job, fam, emph, polish=polish) if need else None
        except Exception as ex:
            stats["errors"][aid] = str(ex)
            db.transition(aid, "NEEDS_HUMAN_ACTION", f"materials failed: {ex}"[:400])
            continue
        fields = {"resume_path": res["pdf"], "resume_sha": res["sha256"], "resume_family": fam}
        if cov:
            fields.update(cover_path=cov["pdf"], cover_sha=cov["sha256"])
        db.update_app(aid, **fields, notes=f"cover letter: {why}" + (f" ({cov['words']} words, {cov['method']})" if cov else ""))
        if a["status"] in ("AWAITING_APPROVAL", "NEEDS_HUMAN_ACTION"):
            stats["prepared"] += 1  # regenerated in place; status unchanged
            continue
        if a["status"] == "QUALIFIED":
            db.transition(aid, "MATERIALS_READY", f"resume family={fam}; cover={'yes' if cov else 'no'}")
        db.transition(aid, "AWAITING_APPROVAL", "review mode: materials ready for your approval")
        stats["prepared"] += 1
    return stats
