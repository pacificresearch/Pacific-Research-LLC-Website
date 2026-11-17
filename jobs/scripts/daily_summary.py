"""End-of-day job report (Andrew 11/13: due 8 pm Pacific).

Usage: python3 scripts/daily_summary.py [YYYY-MM-DD]   (default: today, Pacific time)
Writes data/reports/daily_<date>.md (gitignored with the rest of jobs/data) and prints it.
Counts only employer-confirmed submissions.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jobbot import application_tracker as db  # noqa: E402
from jobbot.config import home  # noqa: E402

PT = timezone(timedelta(hours=-8))
LANES = {"A": "Clinical research", "B": "Program / operations", "C": "International",
         "D": "Big tech", "E": "Startups", "F": "UN / WHO / global health"}
TARGET = {"A": 8, "B": 3, "C": 4, "D": 5, "E": 5, "F": 7}


def pt_day(ts: str | None) -> str | None:
    return datetime.fromisoformat(ts).astimezone(PT).date().isoformat() if ts else None


def main(day: str) -> str:
    c = db.connect()
    rows = c.execute("""SELECT p.id, p.category, p.status, p.status_reason, p.submitted_at, p.updated_at,
                               p.confirmation, j.employer, j.title, j.location, j.ats
                        FROM applications p JOIN jobs j ON j.id = p.job_id""").fetchall()
    confirmed = [r for r in rows if r["confirmation"] and pt_day(r["submitted_at"]) == day]
    total_all = sum(1 for r in rows if r["confirmation"])
    target = sum(TARGET.values())
    lines = [f"# Job applications — {day}", "",
             f"**{len(confirmed)} confirmed today** (target {target}) · **{total_all} confirmed all-time**", "",
             "## Breakdown by lane", "", "| Lane | Today | % of today | Target % |", "|---|---|---|---|"]
    for k, name in LANES.items():
        n = sum(1 for r in confirmed if r["category"] == k)
        pct = f"{100 * n / len(confirmed):.0f}%" if confirmed else "—"
        lines.append(f"| {name} | {n} | {pct} | {100 * TARGET[k] / target:.0f}% |")
    brazil = sum(1 for r in confirmed if any(x in (r["location"] or "").lower()
                                             for x in ("brazil", "são paulo", "sao paulo", "rio de janeiro", "bra-")))
    lines += ["", f"Brazil (Rio / São Paulo): {brazil} ({100 * brazil / len(confirmed):.0f}% of today; target ~5%)"
              if confirmed else "Brazil (Rio / São Paulo): 0", "", "## Applied today (employer-confirmed)", ""]
    for r in sorted(confirmed, key=lambda r: (r["category"] or "", r["employer"])):
        lines.append(f"- [{LANES.get(r['category'], r['category'])}] **{r['employer']}** — {r['title']} ({r['location'] or 'n/a'})")
    if not confirmed:
        lines.append("- none")
    touched = [r for r in rows if pt_day(r["updated_at"]) == day and not r["confirmation"]]
    need = [r for r in touched if r["status"] == "NEEDS_HUMAN_ACTION"]
    pending = [r for r in touched if r["status"] in ("APPROVED", "SUBMITTING", "CONFIRMATION_PENDING")]
    lines += ["", f"## Pending ({len(pending)})", ""]
    lines += [f"- {r['employer']} — {r['title']}: {r['status']}" for r in pending] or ["- none"]
    lines += ["", f"## Needs you ({len(need)})", ""]
    lines += [f"- {r['employer']} — {r['title']}: {(r['status_reason'] or '')[:140]}" for r in need] or ["- nothing"]
    # --- Outcomes / hit rate (Andrew 11/17: litmus guide for where he can win) ---
    sub = [r for r in rows if r["confirmation"]]
    def fam(t):
        t = (t or "").lower()
        for k, rx in (("Clinical research coordinator/specialist", r"coordinator|specialist|associate"),
                      ("Clinical research / trial manager", r"clinical (research|trial|operations)|cra\b|study"),
                      ("Program / project manager", r"program|project|portfolio|operations"),):
            if __import__("re").search(rx, t):
                return k
        return "Other"
    ivw = [r for r in sub if r["status"] in ("INTERVIEW", "OFFER")]
    rej = [r for r in sub if r["status"] == "REJECTED"]
    aged = [r for r in sub if r["submitted_at"] and
            (datetime.now(timezone.utc) - datetime.fromisoformat(r["submitted_at"])).days >= 14]
    lines += ["", "## Outcomes (hit rate)", "",
              f"All-time: {len(sub)} applications · {len(ivw)} interview(s) · {len(rej)} rejection(s) · "
              f"{len(sub) - len(ivw) - len(rej)} no answer yet",
              f"Interview rate: {100 * len(ivw) / len(sub):.1f}% of all; "
              f"{(100 * sum(1 for r in aged if r in ivw) / len(aged)) if aged else 0:.1f}% of {len(aged)} apps aged 14+ days "
              "(benchmark for cold online applications: ~2-5%; strong-fit targeted: 5-10%)", "",
              "| Title family | Applied | Interviews | Rejections |", "|---|---|---|---|"]
    groups = {}
    for r in sub:
        g = groups.setdefault(fam(r["title"]), [0, 0, 0])
        g[0] += 1; g[1] += r in ivw; g[2] += r in rej
    for k, (a, i, j) in sorted(groups.items(), key=lambda x: -x[1][0]):
        lines.append(f"| {k} | {a} | {i} | {j} |")
    if ivw:
        lines += ["", "Interviews:"] + [f"- **{r['employer']}** — {r['title']}" for r in ivw]
    text = "\n".join(lines) + "\n"
    out = home() / "reports" / f"daily_{day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return text


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else datetime.now(PT).date().isoformat()
    print(main(d))
