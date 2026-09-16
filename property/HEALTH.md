# PRG Property System Health — heartbeat file
> Every weekly run appends its line via its artifact PR. Any session
> seeing the newest line older than 9 days must alert Andrew:
> "PROPERTY SYSTEM DEGRADED".

| Date (UTC) | Run | RentCast | Public data | Tests | Underwritten | Report landed on main | Notes |
|---|---|---|---|---|---|---|---|
| 2026-09-16 | build session (manual) | ❌ key missing | ✅ popest 387 / zillow 894 / fhfa 410 / laus 393 / permits 931 | ✅ 18 passed | 0 real (5 fixture) | property/reports/2026-09-16 | System built; Stage 1 live on public data; Stage 2 waits on RENTCAST_API_KEY; Census API now key-gated |
