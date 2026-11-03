# jobbot: personal job application system

Finds, screens, ranks and tailors job applications every day, then submits the ones you
approve through the employer's own application system. Persistent (SQLite), resumable,
idempotent, and measured. It never fabricates a qualification and never claims a
submission the employer didn't confirm.

```
DISCOVER ─► NORMALIZE/DEDUPE ─► SCREEN (mandatory reqs) ─► SCORE 0-100 (+ Claude review)
   ─► SHORTLIST (A10 / B10 / C5) ─► TAILOR resume + cover letter ─► AWAITING_APPROVAL
   ─► you approve ─► SUBMIT (Playwright, your browser) ─► VERIFY confirmation ─► REPORT
                                   └─► NEEDS_HUMAN_ACTION when anything can't be answered honestly
```

## Quick start (on your Mac)

```bash
cd Pacific-Research-LLC-Website/jobs
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python -m playwright install chromium
python -m jobbot init            # creates jobs/data/ (gitignored), config, baseline resumes
# put your evidence in jobs/data/profile.yaml (see profile.example.yaml), then:
python -m jobbot health
python -m jobbot run-daily --no-submit   # discover → qualify → prepare (nothing is sent)
python -m jobbot dashboard               # http://127.0.0.1:8765 — review, approve, settings
python -m jobbot submit                  # submits only what you approved, in a visible browser
python -m jobbot install-schedule        # launchd job, every morning at 06:17
```

The full manual (daily operation, approvals, troubleshooting, security, recovery) is in
[OPERATIONS.md](OPERATIONS.md).

## Layout

| Module | Role |
|---|---|
| `job_discovery/` | Greenhouse, Lever, Ashby, SmartRecruiters public APIs; Workday career-site JSON; USAJOBS API; UN Careers; `import` for Indeed-connector / LinkedIn finds |
| `job_normalization.py` | one schema, salary parsing (advertised / estimated / unknown), location, cross-source fingerprint |
| `eligibility.py` | mandatory requirements: clearance, citizenship / work authorization, language, licensure, degree, years, CRA/CTM specialized-experience traps |
| `job_scoring.py` | 30/20/15/15/10/10 weighted score, category A/B/C, resume family |
| `semantic.py` | optional Claude review through headless `claude -p` (no API key needed; it can only lower eligibility, never raise a fail) |
| `evidence.py` | evidence library loader + **fact guard** (rejects any number, credential or language claim not in your record) |
| `resume_builder.py` | 3 families (clinical, program, international) + per-job derivative; PDF + DOCX; exact version + SHA-256 saved |
| `cover_letter_builder.py` | 200–350-word employer-specific letters from documented achievements only |
| `application_executor/` | Playwright adapters (Greenhouse, Lever, Ashby) with never-guess question guards, CAPTCHA stop, confirmation verification |
| `approval_queue.py` | Review Mode by default; Authorized Auto-Submit only after 5 approved and confirmed submissions plus an explicit typed grant |
| `application_tracker.py` | SQLite schema, state machine, idempotency barrier, crash recovery |
| `email_monitor.py` | read-only IMAP / import; confirmations, rejections, interviews, recruiters; follow-up drafts (never sent) |
| `dashboard.py` | local web UI: progress, queues, materials, approve/reject, quotas, salary, employers, geography, auto-submit, CSV |
| `scheduler.py` | `run-daily`, lock, graceful shutdown, health, launchd / systemd / Task Scheduler install |
| `reporting.py` | daily report, CSV export, optimization analysis every 100 verified submissions |

`employers.yaml` (employer registry with verified ATS slugs) and `search.yaml` (title
vocabulary) are committed. **Everything personal is in `jobs/data/` and gitignored.**
