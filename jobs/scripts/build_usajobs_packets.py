"""Rebuild data/packets/USAJOBS/ (one numbered folder per pending federal application + INDEX.md) and
data/reports/USAJOBS_packets.zip. Andrew 11/24: keep every USAJOBS packet in one place."""
import os, re, shutil, sqlite3, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from jobbot.config import path

def main():
    db = str(path("jobbot.sqlite"))
    base = str(path("packets", "USAJOBS", "x").parent)
    c = sqlite3.connect(db)
    rows = c.execute("""select a.id,j.employer,j.title,j.location,j.apply_url,j.salary_min,j.salary_max,a.resume_path,a.cover_path
        from applications a join jobs j on j.id=a.job_id where j.ats='usajobs' and j.active=1
        and a.status in ('AWAITING_APPROVAL','MATERIALS_READY','NEEDS_HUMAN_ACTION') and a.resume_path is not null order by a.id""").fetchall()
    shutil.rmtree(base, ignore_errors=True); os.makedirs(base)
    lines = ["# USAJOBS applications to submit (login.gov)\n", "Upload your DD-214 (Member 4) on each for veterans' preference.\n",
             "| # | Agency | Title | Location | Pay | Apply | Folder |", "|---|---|---|---|---|---|---|"]
    for k, (i, e, t, loc, u, lo, hi, rp, cp) in enumerate(rows, 1):
        fol = f"{k:02d}_{re.sub(r'[^A-Za-z0-9]+', '_', t)[:40]}_{i}"
        os.makedirs(os.path.join(base, fol))
        for p in (rp, cp):
            if p and os.path.exists(p):
                shutil.copy(p, os.path.join(base, fol))
        lines.append(f"| {k} | {e[:34]} | {t[:55]} | {(loc or '')[:22]} | ${int(lo or 0)//1000}K–${int(hi or 0)//1000}K | "
                     f"{(u or '').replace(':443', '')} | {fol} |")
    open(os.path.join(base, "INDEX.md"), "w").write("\n".join(lines) + "\n")
    shutil.make_archive(str(path("reports", "x").parent / "USAJOBS_packets"), "zip", base)
    print(f"{len(rows)} federal packets -> {base}")

if __name__ == "__main__":
    main()
