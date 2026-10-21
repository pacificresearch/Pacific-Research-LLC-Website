# PRG System Health — heartbeat file
> Every scheduled run appends its line via its artifact PR. Any session
> seeing the newest line older than 2 days must alert Andrew:
> "SYSTEM DEGRADED". Manual "run daily" clicks count as runs.

| Date (UTC) | Run | SAM | Outlook | Sent | Report landed on main | Notes |
|---|---|---|---|---|---|---|
| 2026-09-15 | manual repair session | ✅ | ❌ session-side | 0 | n/a | System repaired: PR #13+#37+#38 merged; matcher coverage fix; queue pruned; artifact rule + self-test added |
| 2026-10-21 | manual repair session | ❌ api.sam.gov blocked by egress policy (403 CONNECT) | n/a | 0 | n/a | ROOT CAUSE of no reports since 08-18: cloud environment network policy blocks api.sam.gov and sam.gov; every scheduled run stops at step 1 and reports SUCCEEDED in ~1 min. Fix is account-side: claude.ai Settings > Capabilities > allowed domains. Cadence changed to Mon/Thu (2x/week) for all four capture/send tasks; watchdog prompt updated. |
