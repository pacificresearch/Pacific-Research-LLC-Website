---
name: run-jobs
description: Run Andrew's personal job application system (jobs/jobbot) end to end — Indeed-connector search + import, ATS discovery, eligibility screen, scoring with Claude review, A/B/C shortlist (10 clinical research / 10 best fit / 5 international), tailored resumes and cover letters, report, and a summary of what awaits approval. Use when Andrew says "run job system", "run jobs", "/run-jobs", "find me jobs", "apply to jobs", or asks for today's job applications.
---

# Run Job System

**DISCOVER → IMPORT → QUALIFY → PREPARE → REPORT → (SUBMIT only what Andrew approved)**

Work from `jobs/`. Personal data is in `jobs/data/` (gitignored); never commit it, and never
paste his phone, email or registry numbers into PRs or commits.

1. `python3 -m jobbot health`. Note unapproved answers and failing sources for the summary.
2. `python3 -m jobbot discover`. These are public ATS feeds, 12 in parallel, about 10 minutes.
3. Indeed: run `search_jobs` for the category titles in `jobs/search.yaml` and the locations
   SoCal, San Diego, Bay Area and remote, plus international ones. Call `get_job_details` for
   promising hits, write `jobs/data/imports/indeed_<date>.json` ([{employer,title,location,
   description,salary_min,salary_max,posted_date,job_url,apply_url,source_job_id}]), then
   `python3 -m jobbot import <file> --source indeed`.
3b. LinkedIn (discovery only, Andrew 11/6): search engines do not index LinkedIn job pages, so
   read LinkedIn job-alert emails (Gmail: `from:jobalerts-noreply@linkedin.com newer_than:2d`).
   For each promising posting, find the same job on the employer's own site (search "<company> careers <title>").
   If that site is a supported ATS board, add it with `harvest` (new boards) or `add-url` (one
   posting); the system then applies there. LinkedIn-only (Easy Apply) postings go on a short list
   in the report for Andrew to apply himself — never automate LinkedIn itself.
4. `python3 -m jobbot qualify`. Claude review runs automatically through `claude -p`.
5. `python3 -m jobbot shortlist`, then `python3 -m jobbot prepare`.
6. `python3 -m jobbot report`. Send Andrew the report plus a zip of `data/materials/app_*`.
7. Submitting: only for applications Andrew approved (`approve <ids>`), via `submit` on **his**
   machine (Playwright needs his browser sessions). In a cloud session, prepare and report only.

Gates that never open on their own: no unapproved submission, no guessed answer to a
sensitive question (work authorization, sponsorship, veteran/disability, EEO, criminal,
clearance, salary, relocation, attestations), no CAPTCHA solving, no automated LinkedIn or
Indeed applications, no messages sent to recruiters.
