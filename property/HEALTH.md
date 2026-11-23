# PRG Property System Health — heartbeat file
> Every weekly run appends its line via its artifact PR. Any session
> seeing the newest line older than 9 days must alert Andrew:
> "PROPERTY SYSTEM DEGRADED".

| Date (UTC) | Run | RentCast | Public data | Tests | Underwritten | Report landed on main | Notes |
|---|---|---|---|---|---|---|---|
| 2026-09-16 | build session (manual) | ❌ key missing | ✅ popest 387 / zillow 894 / fhfa 410 / laus 393 / permits 931 | ✅ 18 passed | 0 real (5 fixture) | property/reports/2026-09-16 | System built; Stage 1 live on public data; Stage 2 waits on RENTCAST_API_KEY; Census API now key-gated |
| 2026-11-18 | repair session (manual) | ❌ key missing (request declined on card) | ✅ popest / zillow / fhfa / laus / permits all live | ✅ 18 passed | 0 real | property/reports/2026-11-18 | Root cause of silent 11/16 run: fired session had no repo (`no-git-repo`) — Routine prompt now attaches+clones; main.py self-installs deps; key setup documented in README |
| 2026-11-18 | weekly (persistent session) | ❌ key missing | ✅ popest / zillow / fhfa / laus / permits live; BLS API daily quota exhausted | ✅ 18 passed | 0 real | property/reports/2026-11-18 | Push proven; Stage 1 ran; research fan-out (10 agents) hit the account 5-hour rate limit before any market file was written — no research landed, PR not opened; folded into the 2026-11-23 run |
| 2026-11-23 | weekly (persistent session) | ❌ key missing | ✅ popest / zillow / fhfa / laus / permits (cached, <7d); BLS API quota exhausted | ✅ 18 passed | 0 real | property/reports/2026-11-23 | First full research layer: 22 market YAMLs (8 top Stage 1 + 14 seeds), 97 catalysts / 73 primary-verified, 26 incentives, 22 tax rules; re-run uses them. Agents ran in waves of 3-4 after the 11/18 rate-limit failure. |
