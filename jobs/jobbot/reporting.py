"""Daily report + optimization analysis (every 100 verified submissions)."""
from __future__ import annotations

import csv
import io
import json
import math
from collections import Counter, defaultdict
from datetime import date

from . import application_tracker as db
from .config import load_config, path


def _fmt_salary(r) -> str:
    if r["salary_min"] or r["salary_max"]:
        cur = r["salary_currency"] or "USD"
        return f"{cur} {r['salary_min'] or 0:,.0f}-{r['salary_max'] or 0:,.0f} ({r['salary_label']})"
    sub = json.loads(r["subscores"] or "{}")
    return "unknown"


def metrics() -> dict:
    con = db.connect()
    by_status = dict(con.execute("SELECT status, COUNT(*) FROM applications GROUP BY status").fetchall())
    by_cat_sub = dict(con.execute("SELECT category, COUNT(*) FROM applications WHERE status IN "
                                  "('SUBMITTED','INTERVIEW','OFFER') GROUP BY category").fetchall())
    today = date.today().isoformat()
    disc_today = con.execute("SELECT COUNT(*) FROM jobs WHERE substr(first_seen,1,10)=?", (today,)).fetchone()[0]
    avg = con.execute("SELECT AVG(score) FROM assessments a JOIN applications p ON p.job_id=a.job_id "
                      "WHERE p.status NOT IN ('REJECTED','DISCOVERED','SCREENED')").fetchone()[0]
    return {"by_status": by_status, "submitted_by_category": by_cat_sub, "discovered_today": disc_today,
            "jobs_total": con.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
            "active_jobs": con.execute("SELECT COUNT(*) FROM jobs WHERE active=1").fetchone()[0],
            "avg_qualified_score": round(avg or 0, 1),
            "submitted_today": db.submitted_today(),
            "emails_attention": con.execute("SELECT COUNT(*) FROM emails WHERE needs_attention=1 AND handled=0").fetchone()[0]}


def daily_report(run_stats: dict | None = None) -> str:
    cfg = load_config()
    m = metrics()
    run_stats = dict(run_stats or {})
    if not run_stats:  # standalone report: use the most recent run that did discovery/qualification
        for r in db.connect().execute("SELECT stats FROM runs WHERE stats IS NOT NULL ORDER BY id DESC LIMIT 10"):
            st = json.loads(r["stats"])
            for k in ("discovery", "qualify"):
                if isinstance(st.get(k), dict) and (st[k].get("fetched") or st[k].get("screened")) and k not in run_stats:
                    run_stats[k] = st[k]
    run_stats = run_stats or {}
    q = cfg["quotas"]
    lines = [f"# Job application report — {date.today().isoformat()}", "",
             f"Mode: **{cfg['mode'].upper()}**{' (PAUSED)' if cfg.get('paused') else ''} · quotas A={q['A']} B={q['B']} "
             f"C={q['C']} · min score {cfg['min_score']}", ""]
    d = run_stats.get("discovery", {})
    ql = run_stats.get("qualify", {})
    lines += ["## Today", "",
              f"- Discovered: {d.get('relevant', m['discovered_today'])} relevant postings "
              f"({d.get('new', '?')} new, {d.get('dupes', '?')} already known) from {d.get('fetched', '?')} fetched",
              f"- Evaluated: {ql.get('screened', '?')} · qualified: {ql.get('qualified', '?')} · "
              f"failed mandatory requirements: {ql.get('failed_eligibility', '?')} · below threshold: "
              f"{ql.get('below_threshold', '?')} · Claude-reviewed: {ql.get('semantic', 0)}",
              f"- Applications **submitted (employer-confirmed)** today: **{m['submitted_today']}**",
              f"- Awaiting your approval: {m['by_status'].get('AWAITING_APPROVAL', 0)} · needs you: "
              f"{m['by_status'].get('NEEDS_HUMAN_ACTION', 0)} · confirmation pending: "
              f"{m['by_status'].get('CONFIRMATION_PENDING', 0)} · failed: {m['by_status'].get('FAILED', 0)}",
              f"- Average score of qualified pipeline: {m['avg_qualified_score']}", ""]
    if d.get("errors"):
        lines += ["### Source errors", ""] + [f"- `{k}`: {v}" for k, v in d["errors"].items()] + [""]
    lines += ["## Category breakdown", "", "| Cat | Quota | Submitted today | Ready for approval | Shortfall reason |",
              "|---|---|---|---|---|"]
    names = {"A": "Clinical research", "B": "Best overall fit", "C": "International"}
    for cat in ("A", "B", "C"):
        ready = len([r for r in db.pipeline_rows(status="AWAITING_APPROVAL", category=cat)])
        sub = db.submitted_today(cat)
        short = ""
        if sub < q[cat]:
            short = ("review mode — waiting on your approval" if ready else
                     "not enough qualified openings found today")
        lines.append(f"| {cat} {names[cat]} | {q[cat]} | {sub} | {ready} | {short} |")
    lines += ["", "## Highest-quality opportunities", ""]
    for cat in ("A", "B", "C"):
        rows = [r for r in db.pipeline_rows(category=cat, limit=400)
                if r["status"] in ("AWAITING_APPROVAL", "QUALIFIED", "MATERIALS_READY", "NEEDS_HUMAN_ACTION")][:10]
        lines += [f"### {cat} — {names[cat]}", "", "| # | Score | Conf | Employer | Title | Location | Salary | Status |",
                  "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r['id']} | {r['score']} | {r['confidence']} | {r['employer']} | "
                         f"[{r['title']}]({r['job_url'] or r['apply_url']}) | {r['location'][:40]} | {_fmt_salary(r)} | "
                         f"{r['status']} |")
        if not rows:
            lines.append("| — | | | none qualified | | | | |")
        lines.append("")
    na = db.pipeline_rows(status="NEEDS_HUMAN_ACTION", limit=50)
    if na:
        lines += ["## Follow-up tasks (needs you)", ""]
        for r in na[:25]:
            lines.append(f"- #{r['id']} {r['employer']} — {r['title']}: {r['status_reason'][:220]}")
        lines.append("")
    att = db.connect().execute("SELECT subject, classification, application_id FROM emails WHERE needs_attention=1 "
                               "AND handled=0 ORDER BY id DESC LIMIT 20").fetchall()
    if att:
        lines += ["## Email needing attention", ""] + [f"- [{e['classification']}] {e['subject']} (app "
                                                       f"{e['application_id']})" for e in att] + [""]
    text = "\n".join(lines)
    path("reports", f"{date.today().isoformat()}.md").write_text(text)
    return text


def export_csv() -> str:
    rows = db.pipeline_rows(limit=100000)
    buf = io.StringIO()
    cols = ["id", "status", "category", "score", "confidence", "eligibility", "employer", "title", "location",
            "salary_min", "salary_max", "salary_label", "source", "ats", "posted_date", "apply_url", "resume_family",
            "resume_path", "cover_path", "approved_at", "submitted_at", "confirmation", "follow_up_date",
            "status_reason", "attempts"]
    w = csv.writer(buf)
    w.writerow(cols)
    for r in rows:
        w.writerow([r[c] for c in cols])
    return buf.getvalue()


def _wilson(k: int, n: int) -> str:
    if n == 0:
        return "n/a"
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{p:.0%} (95% CI {max(0, c - h):.0%}–{min(1, c + h):.0%}, n={n})"


def optimization_report(force: bool = False) -> str | None:
    con = db.connect()
    sub = con.execute("SELECT COUNT(*) FROM applications WHERE status IN ('SUBMITTED','INTERVIEW','OFFER','REJECTED') "
                      "AND submitted_at IS NOT NULL").fetchone()[0]
    last = (db.get_settings().get("last_optimization_at_n") or 0)
    if not force and sub // 100 <= last // 100:
        return None
    rows = con.execute("""SELECT a.category, a.resume_family, j.ats, j.employer, a.status,
                          EXISTS(SELECT 1 FROM emails e WHERE e.application_id=a.id AND
                                 e.classification IN ('interview','recruiter','offer','assessment')) AS responded
                          FROM applications a JOIN jobs j ON j.id=a.job_id WHERE a.submitted_at IS NOT NULL""").fetchall()
    lines = [f"# Optimization analysis — {sub} verified submissions", "",
             "Rates with Wilson 95% intervals. Groups under 20 are listed but not used for recommendations; "
             "these are associations, not causal effects.", ""]
    recs = []
    for dim in ("category", "resume_family", "ats"):
        g = defaultdict(lambda: [0, 0, 0])
        for r in rows:
            k = r[dim] or "?"
            g[k][0] += 1
            g[k][1] += int(r["responded"] or r["status"] in ("INTERVIEW", "OFFER"))
            g[k][2] += int(r["status"] in ("INTERVIEW", "OFFER"))
        lines += [f"## By {dim}", "", "| Group | Response rate | Interview rate |", "|---|---|---|"]
        for k, (n, resp, iv) in sorted(g.items(), key=lambda x: -x[1][0]):
            lines.append(f"| {k} | {_wilson(resp, n)} | {_wilson(iv, n)} |")
        big = {k: v for k, v in g.items() if v[0] >= 20}
        if len(big) >= 2:
            best = max(big.items(), key=lambda x: x[1][1] / x[1][0])
            worst = min(big.items(), key=lambda x: x[1][1] / x[1][0])
            if best[1][1] / best[1][0] - worst[1][1] / worst[1][0] > 0.10:
                recs.append(f"{dim}: '{best[0]}' responds better than '{worst[0]}' "
                            f"({best[1][1]}/{best[1][0]} vs {worst[1][1]}/{worst[1][0]}) — consider shifting volume, "
                            f"re-check after the next 100.")
        lines.append("")
    lines += ["## Proposals", ""] + ([f"- {r}" for r in recs] or ["- Not enough data for a supported recommendation yet."])
    text = "\n".join(lines)
    path("reports", f"optimization_{sub:05d}.md").write_text(text)
    db.set_setting("last_optimization_at_n", sub)
    return text
