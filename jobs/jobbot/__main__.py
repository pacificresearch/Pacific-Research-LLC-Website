"""CLI:  python -m jobbot <command>   (run from the jobs/ directory)"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from . import application_tracker as db


def main(argv=None):
    ap = argparse.ArgumentParser(prog="jobbot")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create data dir, config, and baseline resumes")
    d = sub.add_parser("discover"); d.add_argument("--only", nargs="*")
    q = sub.add_parser("qualify"); q.add_argument("--rescore", action="store_true"); q.add_argument("--no-semantic", action="store_true")
    sub.add_parser("shortlist")
    p = sub.add_parser("prepare"); p.add_argument("ids", nargs="*", type=int); p.add_argument("--polish", action="store_true"); p.add_argument("--regenerate", action="store_true")
    r = sub.add_parser("review", help="prefill (no submit) in a visible browser"); r.add_argument("ids", nargs="+", type=int)
    r.add_argument("--headless", action="store_true"); r.add_argument("--wait-human", type=int, default=0)
    a = sub.add_parser("approve"); a.add_argument("ids", nargs="+", type=int)
    pm = sub.add_parser("promote", help="prepare a below-threshold job you want to consider"); pm.add_argument("ids", nargs="+", type=int)
    rj = sub.add_parser("reject"); rj.add_argument("ids", nargs="+", type=int); rj.add_argument("--reason", default="not a fit")
    s = sub.add_parser("submit", help="submit APPROVED applications"); s.add_argument("ids", nargs="*", type=int)
    s.add_argument("--headless", action="store_true"); s.add_argument("--wait-human", type=int, default=120)
    m = sub.add_parser("mark-submitted"); m.add_argument("id", type=int); m.add_argument("confirmation")
    rd = sub.add_parser("run-daily"); rd.add_argument("--no-submit", action="store_true"); rd.add_argument("--no-semantic", action="store_true")
    rd.add_argument("--headed", action="store_true"); rd.add_argument("--no-discover", action="store_true")
    im = sub.add_parser("import", help="import jobs JSON [{employer,title,location,description,job_url,apply_url}]"); im.add_argument("file"); im.add_argument("--source", default="import")
    au = sub.add_parser("add-url", help="add one posting you found (e.g. on LinkedIn)"); au.add_argument("url"); au.add_argument("--employer", required=True); au.add_argument("--title", required=True); au.add_argument("--location", default="")
    ie = sub.add_parser("import-emails"); ie.add_argument("file")
    sub.add_parser("poll-email")
    sub.add_parser("report")
    sub.add_parser("optimize")
    sub.add_parser("export")
    sub.add_parser("health")
    sub.add_parser("recover")
    dash = sub.add_parser("dashboard"); dash.add_argument("--port", type=int, default=8765)
    sc = sub.add_parser("install-schedule"); sc.add_argument("--hour", type=int, default=6); sc.add_argument("--minute", type=int, default=17)
    aa = sub.add_parser("authorize-auto-submit"); aa.add_argument("confirm")
    sub.add_parser("revoke-auto-submit")
    st = sub.add_parser("status"); st.add_argument("--status"); st.add_argument("--limit", type=int, default=40)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    def out(x):
        print(json.dumps(x, indent=2, default=str) if not isinstance(x, str) else x)

    if args.cmd == "init":
        import shutil
        from .config import JOBS_DIR, home
        h = home()
        if not (h / "config.yaml").exists():
            shutil.copy(JOBS_DIR / "config.example.yaml", h / "config.yaml")
        if not (h / "profile.yaml").exists():
            shutil.copy(JOBS_DIR / "profile.example.yaml", h / "profile.yaml")
            out(f"Created {h/'profile.yaml'} from the example — replace it with your evidence before generating resumes.")
        db.connect()
        from .resume_builder import build_baselines
        out({"home": str(h), "baselines": build_baselines()})
    elif args.cmd == "discover":
        from . import job_discovery
        out(job_discovery.run(only=args.only))
    elif args.cmd == "qualify":
        from . import pipeline
        out(pipeline.qualify(rescore=args.rescore, use_semantic=False if args.no_semantic else None))
    elif args.cmd == "shortlist":
        from . import pipeline
        for cat, rows in pipeline.shortlist().items():
            print(f"== {cat}")
            for r in rows:
                print(f"  #{r['id']:<5} {r['score']:>5} {r['status']:<18} {r['employer']} — {r['title']} [{r['location'][:40]}]")
    elif args.cmd == "prepare":
        from . import pipeline
        ids = args.ids or [r["id"] for rows in pipeline.shortlist().values() for r in rows if r["status"] == "QUALIFIED"]
        out(pipeline.prepare(ids, polish=args.polish, regenerate=args.regenerate))
    elif args.cmd == "review":
        from .application_executor import execute
        out([execute(i, "review", headless=args.headless, wait_human_seconds=args.wait_human) for i in args.ids])
    elif args.cmd == "approve":
        from . import approval_queue
        for i in args.ids:
            approval_queue.approve(i)
        out(f"approved {args.ids}")
    elif args.cmd == "promote":
        from . import approval_queue
        for i in args.ids:
            approval_queue.promote(i)
        out(f"promoted {args.ids} — run `prepare {' '.join(map(str, args.ids))}`")
    elif args.cmd == "reject":
        from . import approval_queue
        for i in args.ids:
            approval_queue.reject(i, args.reason)
        out(f"rejected {args.ids}")
    elif args.cmd == "submit":
        from .application_executor import execute
        from .scheduler import apply_approved
        if args.ids:
            out([execute(i, "submit", headless=args.headless, wait_human_seconds=args.wait_human) for i in args.ids])
        else:
            out(apply_approved(headless=args.headless))
    elif args.cmd == "mark-submitted":
        from . import approval_queue
        approval_queue.mark_submitted_manually(args.id, args.confirmation)
        out("recorded")
    elif args.cmd == "run-daily":
        from .scheduler import run_daily
        out(run_daily(submit=not args.no_submit, headless=not args.headed,
                      use_semantic=False if args.no_semantic else None, discover=not args.no_discover))
    elif args.cmd == "import":
        from . import job_discovery
        out(job_discovery.import_records(json.load(open(args.file)), source=args.source))
    elif args.cmd == "add-url":
        from . import job_discovery
        out(job_discovery.import_records([{"employer": args.employer, "title": args.title, "location": args.location,
                                            "job_url": args.url, "apply_url": args.url}], source="manual"))
    elif args.cmd == "import-emails":
        from . import email_monitor
        out(email_monitor.import_file(args.file))
    elif args.cmd == "poll-email":
        from . import email_monitor
        out(email_monitor.poll_imap())
    elif args.cmd == "report":
        from . import reporting
        out(reporting.daily_report())
    elif args.cmd == "optimize":
        from . import reporting
        out(reporting.optimization_report(force=True))
    elif args.cmd == "export":
        from . import reporting
        sys.stdout.write(reporting.export_csv())
    elif args.cmd == "health":
        from .scheduler import health
        out(health())
    elif args.cmd == "recover":
        out(db.recover())
    elif args.cmd == "dashboard":
        from .dashboard import serve
        serve(args.port)
    elif args.cmd == "install-schedule":
        from .scheduler import install_schedule
        out(install_schedule(args.hour, args.minute))
    elif args.cmd == "authorize-auto-submit":
        from . import approval_queue
        out(approval_queue.authorize_auto_submit(args.confirm))
    elif args.cmd == "revoke-auto-submit":
        from . import approval_queue
        approval_queue.revoke_auto_submit()
        out("auto-submit revoked; review mode")
    elif args.cmd == "status":
        for r in db.pipeline_rows(status=args.status, limit=args.limit):
            print(f"#{r['id']:<5} {r['score'] or 0:>5} {r['category'] or '-'} {r['status']:<20} {r['employer']} — {r['title']}")


if __name__ == "__main__":
    main()
