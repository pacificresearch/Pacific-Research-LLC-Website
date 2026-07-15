# Pacific Research Group LLC — Claude Instructions

## OPPORTUNITY SCREENING RULE — RUN BEFORE ANY ANALYSIS

When given a solicitation, RFQ, RFI, or sources sought, apply this gate
FIRST and lead with the verdict (BID / NO-BID / CONDITIONAL) in the first
sentence. Do not produce a full analysis of a NO-BID unless asked.

Kill criteria (any one = NO-BID, state which and stop):

1. **NAICS outside PRG capability**: PRG performs knowledge-work services
   (541611, 541715, 541720, 541714, 541618, 541990, 541910, 541512,
   611xxx). Construction (23xxxx), trades, manufacturing, physical field
   work, and Y/Z PSC codes are automatic kills.
2. **Self-performance PRG cannot meet**: SDVOSB set-asides carry limitations
   on subcontracting (50% services, 25% special trade, 15% general
   construction). If PRG cannot self-perform the required share with
   actual labor, kill it. No pass-through structures.
3. **Physical delivery requirements**: crews, equipment, licenses, site
   presence, trade certifications, bonding. PRG has none.
4. **Dead timeline**: deadline passed, mandatory site visit missed, or
   insufficient days to responsibly respond.
5. **Wrong scale**: contract value or size standard incompatible with a
   single-member LLC.

**PRG capability envelope**: clinical research (ACRP-PM/CP, JAMA-published),
program evaluation, longitudinal studies, international/STTA (Spanish,
evacuation ops), biomedical technology ADVISORY (not repair crews),
technical writing, training development. Labor = Andrew + Claude drafting
+ 1099 specialists.

**Format**: verdict first, one-line reason per kill criterion triggered,
total under 100 words for NO-BIDs.

## Repository context

- The SAM.gov opportunity screening tool lives on branch
  `claude/samgov-opportunity-matcher-0a3c2f` (`samgov_opportunity_matcher.py`,
  PR #1). Its go/no-go verdict layer implements screening logic consistent
  with the rule above; keep the two aligned when either changes.
