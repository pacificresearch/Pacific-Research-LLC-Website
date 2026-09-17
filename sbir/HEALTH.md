# PRG SBIR/STTR System Health — heartbeat file
> Every weekly run appends its line via its artifact push. Any session
> seeing the newest line older than 9 days must alert Andrew:
> "SBIR SYSTEM DEGRADED".
>
> Nine days, not two: this lane sweeps weekly (Mondays 13:12 UTC), so a
> 2-day alarm — right for the daily capture runs — would cry wolf every
> week. One missed Monday is the real signal.

| Date (UTC) | Run | Sources | Self-test | Survivors | Report landed on main | Notes |
|---|---|---|---|---|---|---|
| 2026-08-25 | build session (manual) | ⚠️ partial — 4 of 9 unavailable (SBIR.gov 403, DoD DSIP 403, Simpler.Grants.gov and SAM.gov uncredentialed) | ✅ 18 passed | 1 (PAR-27-040, forecast) | sbir/reports/PRG_SBIR_digest_2026-08-25.md | Lane built; first pass across all 24 PA-27-102 institutes filed |
