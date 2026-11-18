# PRG Property System Health — heartbeat file
> Every weekly run appends its line via its artifact PR. Any session
> seeing the newest line older than 9 days must alert Andrew:
> "PROPERTY SYSTEM DEGRADED".

| Date (UTC) | Run | RentCast | Public data | Tests | Underwritten | Report landed on main | Notes |
|---|---|---|---|---|---|---|---|
| 2026-09-16 | build session (manual) | ❌ key missing | ✅ popest 387 / zillow 894 / fhfa 410 / laus 393 / permits 931 | ✅ 18 passed | 0 real (5 fixture) | property/reports/2026-09-16 | System built; Stage 1 live on public data; Stage 2 waits on RENTCAST_API_KEY; Census API now key-gated |
| 2026-11-18 | repair session (manual) | ❌ key missing (request declined on card) | ✅ popest / zillow / fhfa / laus / permits all live | ✅ 18 passed | 0 real | property/reports/2026-11-18 | Root cause of silent 11/16 run: fired session had no repo (`no-git-repo`) — Routine prompt now attaches+clones; main.py self-installs deps; key setup documented in README |
| 2026-11-18 | persistent-session validation | started 11:57 UTC |
