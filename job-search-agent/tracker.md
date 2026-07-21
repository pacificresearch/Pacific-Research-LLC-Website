# Job Tracker — packaged & screened

Dedupe key: company + title. Never re-package a listed job.

## Packaged (application-ready)

| Date | Title | Company | Location | Link | Status |
|---|---|---|---|---|---|
| 2026-07-21 | Clinical Research Data Specialist I (Hybrid) | Cedars-Sinai | Los Angeles, CA | https://to.indeed.com/aa48b6dgy4gs | ready to apply |
| 2026-07-21 | Clinical Research Coordinator (Neurology) | UCLA Health | Los Angeles, CA | https://to.indeed.com/aahmrlnpmqtb | ready to apply |
| 2026-07-21 | Clinical Research Coordinator | California Liver Research Institute | Pasadena, CA | https://to.indeed.com/aakzwt8gm4d4 | ready to apply |
| 2026-07-21 | Clinical Research Program Manager, Multi-Site Ops | Cedars-Sinai | Los Angeles, CA | https://to.indeed.com/aahpkxbyfrf7 | ready to apply |
| 2026-07-21 | Clinical Research Coordinator II | Stanford University | Stanford, CA | https://careersearch.stanford.edu/jobs/clinical-research-coordinator-29618 | ready to apply |
| 2026-07-21 | Assistant Clinical Research Coordinator (LIFESCAPE) | Stanford University | Stanford, CA | https://careersearch.stanford.edu/jobs/assistant-clinical-research-coordinator-recruitment-1-year-fixed-term-29071 | ready to apply |
| 2026-07-21 | Research Health Science Specialist (0601 Series) | Federal Agency | Various, US | https://www.usajobs.gov/job/869482700 | ready to apply |

## Screened & skipped (gate fired)

| Date | Title | Company | Gate |
|---|---|---|---|
| 2026-07-21 | Senior Manager, Clinical Operations | ZBeats/MySleep Diagnostics | Requires CCT/CRAT or paramedic-level ECG credential not held |
| 2026-07-21 | Associate Director of Business Development | Vitamin Angels | Requires 8–10 yrs fundraising portfolio track record |
| 2026-07-21 | Associate Director, OPEN Learner Engagement | FHI 360 | Requires 10+ yrs online-education program mgmt + LMS/CoP portfolio |

## Cycle 2 notes (2026-07-21 batch-02)

- Tool access constraints: Indeed MCP search calls rejected by environment; WebFetch blocked by job sites (403 Forbidden). Cycle 2 used fallback approach per AGENT_PROMPT.md: web search aggregates + company career portal data for screening/tailoring (ground truth facts from repo sufficient for full audit).
- 3 packages produced (all Pillar 1, Stanford + Federal): Stanford CRC II (same employer, strong match), Stanford ACRC (entry-level, overqualified hedge), USAJOBS 0601 (federal Tier A, veteran preference eligible).
- Federal-format resume needed for USAJOBS applications (build once, reuse).

## Open questions for Andrew

- ~~Upload master resume~~ RESOLVED 2026-07-21: master
  `ODonnell_Andrew_Resume_2026ADC.pdf` committed to
  `job-search-agent/resume/` (canonical), with the `2026AD` variant alongside.
- ~~Confirm Spanish proficiency~~ RESOLVED 2026-07-21: Spanish and Portuguese
  at Limited Working Proficiency; include only where the role calls for it,
  always labeled at that exact level.
- Confirm target locations: currently searching Los Angeles, CA + Remote US.
- **Build federal-format resume:** For USAJOBS applications (0601 series and other federal roles). Standard format: hours per week, full supervisor contact/phone, GS grade, agency-specific details. Build once, reuse for all federal applications.
