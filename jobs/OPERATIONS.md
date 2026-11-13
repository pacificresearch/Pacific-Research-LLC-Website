# jobbot operations manual

## 1. One-time setup (≈15 minutes)

1. **Install** (README quick start). Use Python 3.11+.
2. **Evidence library**: `jobs/data/profile.yaml`. Every bullet must come from your real CV.
   The builder selects, orders and picks among variants; it never writes new claims.
3. **Approved answers**: fill in `approved_answers` in `profile.yaml`. Anything left `null`
   makes the executor stop and ask you, and no application is ever sent with a guessed answer.
   You need to decide these:
   - work authorization, sponsorship, citizenship
   - veteran status and disability status: the exact option text to select, or "I do not wish to answer"
   - EEO (gender, race, Hispanic/Latino, orientation): your explicit preference
   - criminal history, security clearance (held? level? active?)
   - relocation willingness, salary rule (`advertised_midpoint` or a fixed figure), start date
   - SMS consent, travel %, referred-by-employee, education dates (not in the CV)
   - languages: the levels for Portuguese, Spanish and Mandarin. Until they are set, the system treats you as not holding them and rejects postings that require them.
4. **Attestations**: when a form asks you to certify something, the job lands in
   NEEDS_HUMAN_ACTION with an id like `[3fa9c2d1e0b4]`. If you agree with that exact text, add
   the id to `approved_attestations`. Approval is per wording, never a blanket yes.
5. **Browser sign-ins**: run `python -m jobbot review <id>` once. A visible Chromium opens with its
   own persistent profile (`jobs/data/browser/`). Sign in to Workday tenants, USAJOBS or
   LinkedIn there yourself if you want. Your passwords are never stored by jobbot.
6. **Optional integrations**
   - USAJOBS discovery: free key at developer.usajobs.gov → `export USAJOBS_API_KEY=… USAJOBS_EMAIL=…`
   - Email monitoring (read-only): `JOBBOT_IMAP_HOST/USER/PASSWORD` (app password), or let a
     Claude session export mail with the Gmail/Outlook connector and `python -m jobbot import-emails`.
   - Phone push: `export JOBBOT_NTFY_URL=https://ntfy.sh/<private-topic>`
   - Claude semantic review: install Claude Code and log in. `claude -p` uses your account
     (about $0.01 per posting reviewed, 25 per category per day by default).
7. **Schedule**: `python -m jobbot install-schedule` (macOS launchd, 06:17 daily; runs at
   wake if the Mac was asleep). Keep secrets in `~/.zshenv` or launchd `EnvironmentVariables`,
   never in the repo.

### Standing answer policy (Andrew, 11/4)
- **Optional questions are skipped.** Only required fields are filled, plus resume, cover letter and core contact fields.
- **Required voluntary disclosures** (veteran, disability, gender, race/ethnicity, orientation): the system
  selects the "I don't wish to answer / Decline to self-identify" option. If a form has no decline option,
  the application stops for you. On the Workday disability form (CC-305), jobbot types your name and
  today's date next to the decline answer.
- Configured as `answer_policy` in `profile.yaml`.

### Employer portal accounts
- Resumes and applications show your contact email (aodhan.o@outlook.com), and you watch that inbox for
  recruiter replies yourself. Portal accounts and verification links use `account_email`
  (pacificresearchglobal@gmail.com), the inbox jobbot can read through the Gmail connector, or IMAP on your Mac. Each portal gets a unique 16-character password, the same strength as
  Chrome's "suggest strong password".
- Passwords live in your Mac's Keychain (`pip install keyring`) or `data/credentials.json` (0600, gitignored).
- `python -m jobbot export-passwords` writes a Chrome import CSV. Import it at passwords.google.com →
  Settings → Import Passwords so every account syncs to Chrome, then delete the CSV.
- Creating an account accepts the portal's applicant-privacy box, under your instruction to create logins.
  Every other attestation still needs your per-text approval.
- Workday is automated (account → My Information → My Experience → Questions → Disclosures →
  Self-Identify → Review); it stops at Review until you approve.

### Web-search discovery
- On Mondays and Thursdays the daily run searches the web (through `claude -p` WebSearch) for employer job
  boards on Greenhouse, Lever, Ashby, Workday and SmartRecruiters, checks each board is relevant, and
  adds it to `data/employers_discovered.yaml`. From then on the board is read every day through its
  official feed. Aggregators that re-post other companies' jobs (Jobgether etc.) are excluded.
- Manual run: `python -m jobbot harvest --search`, or `python -m jobbot harvest urls.txt`.

## 2. Daily operation (≈10 minutes of your time)

The morning run does discovery (incremental, about 50 employer feeds, 12 in parallel), then
qualification, then the A/B/C shortlist, then tailored materials. Approved applications are
submitted, inbound email is read and the report is written. You get a notification with the counts.

Your part:
1. Open the dashboard and check **Awaiting approval**. Open the resume and cover letter links,
   then **Approve** or **Reject** each one with a reason (reasons feed tuning).
2. Check **Needs you**. Each row says exactly what is missing: an unapproved question, an
   attestation, a CAPTCHA, a Workday account, or a custom essay question. Fix it in the profile,
   or apply yourself with the prepared packet and click **I applied — record it** with the
   confirmation number.
3. Run `python -m jobbot submit`. A visible browser fills and submits each approved application;
   if a CAPTCHA appears it waits 120 s for you to solve it. It never solves one itself.

Only an employer confirmation page or confirmation email counts as **submitted**. Anything else is
CONFIRMATION_PENDING until email or you confirm it.

### Modes
- **Review Mode** (default): nothing is submitted without your approval.
- **Authorized Auto-Submit**: available after 5 applications you approved were confirmed submitted.
  Enable with `python -m jobbot authorize-auto-submit "I authorize automatic submission of standard applications"`
  or from the dashboard. Only standard applications qualify: score ≥ 80, eligibility pass, confidence ≥ 0.75,
  a supported ATS, and every answer pre-approved. Attestations, unknown questions,
  assessments, fees and CAPTCHAs still pause. Revoke with `revoke-auto-submit`.

### Finding jobs elsewhere
- **LinkedIn**: browse it yourself (its terms prohibit automated scraping), then
  `python -m jobbot add-url <url> --employer "X" --title "Y"`. jobbot applies via the employer ATS when it can.
- **Indeed**: in a Claude session, say "Run Job System". Claude searches through the Indeed
  connector and runs `python -m jobbot import data/imports/indeed_<date>.json`.

## 3. What is automated vs. manual (honest status)

| Channel | Discovery | Submission |
|---|---|---|
| Greenhouse / Lever / Ashby boards | automated (official public APIs) | **automated**, with guards |
| Workday (IQVIA, ICON, Parexel, Syneos, Fortrea, PPD, pharma, medtech, Leidos, Booz Allen, GDIT, CACI, FHI 360, PATH) | automated | **automated**: creates the account, signs in, works through each step and stops at Review. Email-verification tenants pause until the link is clicked. |
| Boards found by web search | automated (Mon/Thu) | per their ATS (above) |
| USAJOBS | automated with free API key | manual (Login.gov); packet prepared |
| UN Careers / Inspira | adapter (CDN may block datacenter IPs; home networks usually fine) | manual (PHP form) |
| Indeed | via Claude connector import | manual (Indeed prohibits automation) |
| LinkedIn | you paste URLs | via employer ATS, or manual |
| Stanford, UCSF, UCLA, UCSD, USC, City of Hope, Hoag, WHO, UNICEF, UNDP, IOM, ICRC, IFRC, IRC | not public feeds | manual; add an ATS slug to `employers.yaml` if you find one |

Because much of the clinical market runs on Workday, the 25/day target counts **all**
confirmed submissions, including the ones you file manually from prepared packets and record in
the dashboard.

## 4. Troubleshooting

| Symptom | Fix |
|---|---|
| `health` shows a failing source | Board slug changed or the site blocked us. Check `source_health`, update `employers.yaml`. A 403 is respected and never retried around. |
| Everything lands in NEEDS_HUMAN_ACTION | Approved answers are still `null`. Fill them in (see 1.3). |
| "no option matches" | The approved wording differs from the form's options. Use the exact option text. |
| Resume rejected by fact guard | A variant contains a number or credential not in the evidence. Fix `profile.yaml`. |
| Semantic layer silent | `claude` not on PATH for launchd. Add its folder to the plist PATH, or set `semantic.enabled: false`. |
| Run didn't happen | `python -m jobbot health` → `last_run`; `launchctl list | grep jobbot`; logs in `jobs/data/logs/`. |

## 5. Recovery and guarantees

- **Crash or closed browser**: on the next start `recover()` resolves anything left in SUBMITTING.
  If the submit click was recorded, the application goes to CONFIRMATION_PENDING and is **never
  clicked again**. If no click was recorded, it goes back to AWAITING_APPROVAL.
- The click intent is committed to the database *before* the click (idempotency barrier).
- One application per job (`UNIQUE job_id`). The same opening on two boards is one job (fingerprint dedupe).
- Concurrent runs are prevented by a file lock. SIGTERM finishes the current step, then stops.
- Manual recovery: `python -m jobbot recover`, `python -m jobbot status --status SUBMITTING`.
- Backup: copy `jobs/data/` (the database is SQLite WAL; copy while no run is active).

## 6. Security and privacy

- Personal data (profile, database, materials, browser profile, reports) lives in `jobs/data/`,
  which is gitignored. Only code, `employers.yaml`, `search.yaml` and fictional examples are committed.
- Credentials come only from environment variables. The browser profile holds your sessions;
  protect it like a password manager (FileVault on).
- The dashboard binds to 127.0.0.1 only, and actions need a per-install token (`data/.dashboard_token`).
- Email access is read-only (`BODY.PEEK`, `readonly=True`). jobbot never sends, replies, accepts,
  declines or withdraws.
- No CAPTCHA solving, no anti-bot evasion, no fake identities, no scraping of sites whose terms prohibit it.

## 7. Scaling past 25 per day

Quotas live in the dashboard. Raise them only when the optimization report (generated every 100
verified submissions, with Wilson intervals and a minimum of 20 per group) shows quality holding.
The architecture (parallel discovery, per-host rate limits, an idempotent queue) handles 100+ per day.
