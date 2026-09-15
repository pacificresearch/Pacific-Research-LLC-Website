# International daily run — addendum to `capture/DAILY_RUN.md`

The domestic daily run procedure is unchanged. This adds an
**INTERNATIONAL** section to the same scheduled session and the same
morning report. One run, one notification, two lanes — Andrew should
never get two separate morning messages.

Insert these steps into the domestic run at the points named.

---

## After domestic step 2 (generate the report)

```
python3 samgov_opportunity_matcher.py --intl --days 7 --limit 100 --narrow \
  --no-recompetes --no-grants --no-sbir --no-reliefweb --no-excel --no-report \
  > intl/reports/PRG_INTL_report_$(date +%F).md
```

`--narrow` is deliberate here: the domestic wide-net sweep pages through
every US small-business set-aside across all NAICS, and set-asides are
overwhelmingly domestic, so it costs many minutes for almost no
international yield. `--intl` adds the State/foreign-assistance posting
offices, which is where the volume actually is. The secondary pulls are
skipped because the domestic run already made them.

**Validated 2026-08-18:** 1,513 notices pulled → 86 kept by the `--intl`
filter → 54 passed the screen, 40 biddable. Runtime a few minutes.

`--intl` keeps only notices with an overseas place of performance or an
international/overseas buyer, drops the domestic international-buyer
score penalty (overseas IS the lane here), and applies the international
kills. Commit the report. Dedupe against notice IDs already in
`intl/reports/` and `intl/opportunities/`.

If `api.sam.gov` is unreachable, the domestic run's STOP rule applies —
notify, do not fabricate.

## After domestic step 3 (screen and select)

Apply `intl/GATE.md` to every notice in the international report.

- **Volume mode applies here too:** every pre-RFP notice (sources
  sought / RFI / presolicitation) with an overseas place of performance
  that survives the gate gets a tailored response drafted the same day.
  On U.S. overseas buys, the response **asks the CO to consider a FAR
  19.000(b)(1)(ii) set-aside** and notes that an SDVOSB award at post
  counts toward the agency's small-business goals (`intl/GATE.md` §A1).
  Cite the paragraph. This is the cheapest real edge in this lane.
- **REGISTER–PREPOSITION outcomes are the expected majority early on.**
  They are logged to `intl/PIPELINE.md`'s registration backlog, not
  drafted against. That is a productive outcome — say so plainly rather
  than reporting a dry day.
- Select **at most ONE** international pursuit as the current
  international contract under consideration, separate from the
  domestic selection.

## Weekly (Mondays) — sources the matcher cannot reach

SAM is the only international source with a clean API. The rest are
portals, so they are swept manually once a week rather than pretended
at daily. Do not let the report imply they were checked when they were
not.

1. **UNGM** tender notices for PRG's UNSPSC codes (once registered) —
   https://www.ungm.org/Public/Notice
2. **UNDP** procurement notices — https://procurement-notices.undp.org/
3. **World Bank eConsultant2**, **IDB**, **ADB CMS** — individual
   consultant assignments only until PRG has bank past performance
   (`intl/SOURCES.md` Tier 3)
4. **ReliefWeb** — already pulled by the full (non-`--fast`) matcher run
5. Implementing-partner career/consultant pages for surge calls

## Registration backlog check (every run, one line)

Report the top open registration and its blocker. Registrations gate
the entire lane; a week of "no international opportunities" while UNGM
sits unregistered is a self-inflicted result.

## Notification — one section appended to the domestic message

```
INTERNATIONAL
  Current intl pursuit: <title> (<buyer>, <country>) — deadline <local / ET>
    role · fulfillment model · margin band · registration held? Y/N
  Sources-sought responses drafted: N (⛔ awaiting send)
  REGISTER–PREPOSITION: N notices — blocked on <registration>
  Registration backlog: next up <X>, blocker <Y>
  PASS: N (top kill: <criterion>)
```

If there is nothing, say "INTERNATIONAL: nothing survived the gate;
registration backlog next up <X>." That is a valid, cheap outcome.

## Standing boundaries — same as domestic, plus

- ⛔ Never auto-send to a contracting officer, a UN procurement officer,
  or a local partner. Prepare and notify only.
- ⛔ Never submit a portal registration on Andrew's behalf without him
  present — UNGM and bank registrations make binding eligibility
  declarations.
- **Never name a local partner or expert in any drafted document before
  their Rail 2 vetting folder is closed.** This is the one boundary in
  the international lane with legal consequences, and drafting pressure
  is exactly when it gets skipped.
