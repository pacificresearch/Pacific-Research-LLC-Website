# PRG Reuse Library

Every proposal is assembled from here, and every bid (win or lose) files
improved content back. If the library isn't growing, the system isn't
compounding.

```
library/
  capability_statements/   # tailored variants, named by NAICS/lane:
                           #   capstate_561720_janitorial.md
                           #   capstate_541714_clinical_research.md
  past_performance/        # one file per performance record, CPARS-style:
                           #   customer, contract #, value, period, POC,
                           #   scope, outcome/metrics. Includes founder
                           #   pre-PRG record (OAW, Stanford trials, USAF).
  resumes/                 # founder + committed key personnel, tailored
                           #   variants by labor category
  boilerplate/             # QC plan skeleton, management approach,
                           #   company data block, EEO/vet statements,
                           #   pricing assumptions & actuals by NAICS
  partners/                # warm list: subs, staffing firms, candidates
                           #   who committed on past bids — NAICS tags,
                           #   quotes received, responsiveness notes
```

Naming: lowercase, underscores, NAICS code where applicable. Date-stamp
superseded versions into an `archive/` subfolder rather than deleting.

## Capability statements

`capability_statements/build_capstate.py` builds every variant (one-page
PDF plus a Markdown copy) from one source, so identity facts cannot
drift between them. Current variants: `capstate_general`,
`capstate_541715_clinical_research`, `capstate_541611_healthcare_operations`.
To tailor for a notice, copy the closest variant in the script, reorder
the competencies to the notice's own nouns, and rebuild. Every experience
line is the Managing Director's individual record and says so.
