"""Daily orchestration, locking, crash recovery, graceful shutdown, OS schedule install, health.

Claude Code sessions do not keep running in the background; the OS scheduler runs
`python -m jobbot run-daily` on your computer every morning instead.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import signal
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from . import application_tracker as db
from . import email_monitor, job_discovery, notify, pipeline, reporting
from .config import JOBS_DIR, home, load_config, path

log = logging.getLogger("jobbot.scheduler")
STOP = {"flag": False}


def _sigterm(*_):
    STOP["flag"] = True
    log.warning("shutdown requested — finishing the current step, then stopping")


class RunLock:
    def __init__(self):
        self.f = open(path("run.lock"), "w")

    def __enter__(self):
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            raise SystemExit("another jobbot run is in progress")
        self.f.write(str(os.getpid()))
        self.f.flush()
        return self

    def __exit__(self, *a):
        self.f.close()  # closing the handle releases the lock on every platform


def run_daily(submit: bool = True, headless: bool = True, use_semantic: bool | None = None,
              discover: bool = True) -> dict:
    signal.signal(signal.SIGTERM, _sigterm)
    signal.signal(signal.SIGINT, _sigterm)
    with RunLock():
        notes = db.recover()
        cfg = load_config()
        with db.tx() as con:
            run_id = con.execute("INSERT INTO runs(started_at,phase,status) VALUES(?,?,?)",
                                 (db.now(), "start", "running")).lastrowid
        stats: dict = {"recovered": notes}

        def phase(name, fn):
            if STOP["flag"]:
                return None
            with db.tx() as con:
                con.execute("UPDATE runs SET phase=? WHERE id=?", (name, run_id))
            try:
                stats[name] = fn()
            except Exception as ex:
                stats[name] = {"error": str(ex)}
                log.error("phase %s failed: %s", name, traceback.format_exc())
            return stats[name]

        try:
            if cfg.get("paused"):
                stats["paused"] = True
            else:
                if discover:
                    phase("discovery", job_discovery.run)
                phase("qualify", lambda: pipeline.qualify(use_semantic=use_semantic))
                sl = pipeline.shortlist()
                todo = [r["id"] for rows in sl.values() for r in rows if r["status"] == "QUALIFIED"]
                phase("prepare", lambda: pipeline.prepare(todo))
                if submit:
                    phase("apply", lambda: apply_approved(headless=headless))
                phase("email", email_monitor.poll_imap)
                phase("followups", lambda: {"drafts": email_monitor.followup_drafts()})
            report = reporting.daily_report(stats)
            opt = reporting.optimization_report()
            stats["report"] = str(path("reports", f"{datetime.now().date().isoformat()}.md"))
            status = "stopped" if STOP["flag"] else "ok"
            errs = [k for k, v in stats.items() if isinstance(v, dict) and v.get("error")]
            if errs:
                status = "partial"
            m = reporting.metrics()
            notify.send(f"jobbot {status}: {m['submitted_today']} submitted · "
                        f"{m['by_status'].get('AWAITING_APPROVAL', 0)} awaiting approval · "
                        f"{m['by_status'].get('NEEDS_HUMAN_ACTION', 0)} need you"
                        + (f" · errors in {', '.join(errs)}" if errs else "") + (" · optimization report ready" if opt else ""))
        except Exception as ex:
            status = "error"
            stats["fatal"] = str(ex)
            notify.send(f"jobbot run FAILED: {ex}")
            raise
        finally:
            with db.tx() as con:
                con.execute("UPDATE runs SET finished_at=?, status=?, stats=? WHERE id=?",
                            (db.now(), status, json.dumps(stats, default=str)[:20000], run_id))
        return stats


def apply_approved(headless: bool = True) -> dict:
    """Submit approved applications (and auto-eligible ones once auto-submit is authorized), within quotas."""
    from . import approval_queue
    from .application_executor import execute
    cfg = load_config()
    auto = cfg.get("mode") == "auto" and db.get_settings().get("auto_submit_authorized")
    out = {"attempted": 0, "results": []}
    for cat, quota in cfg["quotas"].items():
        room = quota - db.submitted_today(cat)
        for r in db.pipeline_rows(status="AWAITING_APPROVAL", category=cat):
            if room <= 0 or STOP["flag"]:
                break
            if not (r["approved_at"] or (auto and approval_queue.auto_eligible(r))):
                continue
            res = execute(r["id"], mode="submit", headless=headless)
            out["attempted"] += 1
            out["results"].append(res)
            if res.get("outcome") == "confirmed":
                room -= 1
    return out


# ------------------------------------------------------------------ OS scheduling
def install_schedule(hour: int = 6, minute: int = 17) -> str:
    py = sys.executable
    env_home = str(home())
    workdir = str(JOBS_DIR)
    system = platform.system()
    if system == "Darwin":
        plist = Path.home() / "Library/LaunchAgents/com.prg.jobbot.plist"
        plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.prg.jobbot</string>
  <key>ProgramArguments</key><array><string>{py}</string><string>-m</string><string>jobbot</string><string>run-daily</string></array>
  <key>WorkingDirectory</key><string>{workdir}</string>
  <key>EnvironmentVariables</key><dict><key>JOBBOT_HOME</key><string>{env_home}</string>
    <key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string></dict>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>{hour}</integer><key>Minute</key><integer>{minute}</integer></dict>
  <key>StandardOutPath</key><string>{env_home}/logs/launchd.out</string>
  <key>StandardErrorPath</key><string>{env_home}/logs/launchd.err</string>
</dict></plist>""")
        path("logs", "x")
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist)], check=False)
        return f"launchd job installed: {plist} (daily {hour:02d}:{minute:02d}; runs at next wake if asleep)"
    if system == "Linux" and shutil.which("systemctl"):
        d = Path.home() / ".config/systemd/user"
        d.mkdir(parents=True, exist_ok=True)
        (d / "jobbot.service").write_text(f"""[Unit]
Description=jobbot daily job application run
[Service]
Type=oneshot
WorkingDirectory={workdir}
Environment=JOBBOT_HOME={env_home}
ExecStart={py} -m jobbot run-daily
TimeoutStopSec=120
""")
        (d / "jobbot.timer").write_text(f"""[Unit]
Description=jobbot daily
[Timer]
OnCalendar=*-*-* {hour:02d}:{minute:02d}:00
Persistent=true
[Install]
WantedBy=timers.target
""")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        subprocess.run(["systemctl", "--user", "enable", "--now", "jobbot.timer"], check=False)
        return f"systemd user timer installed (daily {hour:02d}:{minute:02d}, Persistent=true catches missed runs)"
    if system == "Windows":
        cmd = f'schtasks /Create /SC DAILY /TN jobbot /ST {hour:02d}:{minute:02d} /TR "{py} -m jobbot run-daily" /F'
        subprocess.run(cmd, shell=True, check=False, cwd=workdir)
        return f"Windows Task Scheduler task 'jobbot' created ({hour:02d}:{minute:02d})"
    line = f"{minute} {hour} * * * cd {workdir} && JOBBOT_HOME={env_home} {py} -m jobbot run-daily >> {env_home}/logs/cron.log 2>&1"
    return "No supported scheduler found. Add this line with `crontab -e`:\n" + line


def health() -> dict:
    from . import semantic
    out = {"home": str(home()), "checks": {}}
    c = out["checks"]
    try:
        db.connect().execute("SELECT 1")
        c["database"] = "ok"
    except Exception as ex:
        c["database"] = f"FAIL {ex}"
    c["profile"] = "ok" if (home() / "profile.yaml").exists() else "MISSING — copy profile.example.yaml"
    try:
        from .evidence import profile
        aa = profile().get("approved_answers", {}) or {}
        missing = [k for k, v in aa.items() if v is None]
        c["approved_answers"] = "all set" if not missing else f"{len(missing)} not approved: {', '.join(missing)}"
    except Exception as ex:
        c["approved_answers"] = f"error {ex}"
    try:
        import playwright  # noqa
        c["playwright"] = "ok"
    except ImportError:
        c["playwright"] = "MISSING — pip install playwright && python -m playwright install chromium"
    c["claude_cli"] = "ok (semantic layer on)" if semantic.available() else "not found (deterministic scoring only)"
    last = db.connect().execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    if last:
        age_h = (datetime.now(timezone.utc) - datetime.fromisoformat(last["started_at"])).total_seconds() / 3600
        c["last_run"] = f"{last['status']} {age_h:.1f}h ago (phase {last['phase']})" + (
            " — STALE (>26h)" if age_h > 26 else "")
    else:
        c["last_run"] = "never"
    bad = db.connect().execute("SELECT source, last_error FROM source_health WHERE last_error_at > COALESCE(last_ok,'')"
                               ).fetchall()
    c["sources"] = "ok" if not bad else f"{len(bad)} failing: " + "; ".join(f"{b['source']}" for b in bad[:8])
    c["mode"] = load_config()["mode"]
    return out
