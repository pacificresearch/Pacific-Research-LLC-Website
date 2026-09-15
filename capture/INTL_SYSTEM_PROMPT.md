# PRG INTERNATIONAL — system-design kickoff prompt
> Paste everything below the line into a fresh Claude session to build
> the second capture system. Keep it in this repo so both systems share
> the library, the Outlook channel, and the daily-run infrastructure.

---

We need to design and build a SECOND automated contract-capture system
for Pacific Research Group LLC — **PRG International** — modeled on the
domestic system already running in this repo (`capture/WORKFLOW.md`,
`capture/DAILY_RUN.md`, `capture/PIPELINE.md`, the SAM.gov matcher, the
Outlook send channel, the careers page), but aimed **solely at
international opportunities. Not healthcare-specific — ANY international
contract**: U.S. embassy and consulate procurements, overseas DoD and
State Department requirements, UN system tenders, development-bank
projects, foreign-affairs support services, logistics, training,
research, facilities, advisory — anything with an overseas place of
performance or an international-affairs scope.

## The business model (read carefully — this is the lane)

I hold an MA in International Studies with field experience in Brazil,
Peru, and China, plus interagency refugee/evacuee operations experience
(Operation Allies Welcome, 25K+ evacuees, CDC/interagency compliance).
PRG International monetizes that expertise the same way the domestic
system monetizes aggregation: **PRG primes and owns the customer
relationship, contract management, QC, invoicing, and compliance; I
travel to post — embassies, missions, project sites — to source, vet,
hire, and manage LOCAL experts and local firms who execute the work.**
Founder travel is a feature, not a cost overrun: budget it into every
pricing model. Do NOT evaluate opportunities on whether I can personally
perform the work — the standard is the same credible path:
WIN → SOURCE (locally) → PERFORM → CONTROL → INVOICE → COLLECT → PROFIT.

## What to build (mirror the domestic system, adapted)

1. **`intl/WORKFLOW.md`** — SCREEN → PURSUE → SUBMIT → MONITOR →
   WIN/LOSS pipeline, opportunity folders under `intl/opportunities/`,
   shared reuse library at `capture/library/` (one library, two
   systems; file international variants alongside domestic ones).
2. **Opportunity sources + a daily matcher run** covering:
   - SAM.gov filtered to overseas place of performance and posting
     offices: State Dept regional procurement (A/LM/AQM), embassy/
     consulate local procurement, DoD overseas commands, USAID-legacy
     programs under State, DFC, USDA/FAS, Commerce/ITA.
   - **UN Global Marketplace (UNGM)** tender notices — UNDP, UNOPS,
     UNICEF, WFP, IOM, WHO — after registering PRG on UNGM (walk me
     through registration with exact click-paths).
   - World Bank, IDB, ADB procurement portals (borrower-executed
     tenders open to foreign firms) — monitor, screen, and tell me
     honestly which are realistic for a firm PRG's size.
   - Devex/development-sector pipelines as market intelligence only.
3. **An international screening gate** (`intl/` analog of the
   capture-v3 gate). Keep the domestic hard kills (bonded/large
   construction, firm licensure we don't hold, vehicles/FCL required at
   proposal, dead timeline, wrong scale >$10M early) and ADD:
   - OFAC-sanctioned countries/parties (legal kill — non-negotiable).
   - Conflict zones are NOT a kill (Andrew's standing decision 8/18:
     "conflict zones are fine" — he is a veteran with TCCC/austere-
     operations background and accepts the risk). Instead, every
     conflict/high-threat pursuit gets a mandatory RISK block in the
     screening doc: security and life-support costs priced in, DBA
     insurance rated for the threat level, medevac coverage, and
     duty-of-care plan for local hires. Higher margin bands apply —
     danger pricing is standard in this market, never bid it thin.
   - Requirements demanding an in-country registered legal entity or
     in-country bank account AT PROPOSAL TIME (monitor-preposition
     instead; note where a local partner cures it).
   - Local-national-only or host-country-firm-only set-asides.
   - NOTE the differences, don't assume domestic rules: SDVOSB
     preference generally does NOT apply overseas or in UN/multilateral
     procurement — mention the certification once as credibility, never
     as an entitlement. Veteran-owned status IS worth one line in UN
     vendor profiles.
4. **Compliance rails built into every pursuit** (make these compliance-
   matrix rows, not afterthoughts): FCPA/anti-bribery vetting of every
   local agent, partner, and hire (this is the #1 legal risk of the
   travel-and-hire-locally model — build a standard vetting checklist
   and rep letter); Defense Base Act insurance on U.S.-government
   overseas service contracts; export controls/ITAR screen on anything
   technical; local labor law + contractor-vs-employee classification
   per country; currency and payment terms (bill in USD wherever
   allowed; flag FX risk when not); visa/entry requirements for my
   travel; DSSR per-diem rates for travel pricing.
5. **Pricing** — same delegated authority as domestic (price
   independently from data, present the finished number with the
   package): local-market wage data for in-country experts, DSSR/State
   travel rates for my trips, margin bands adjusted for country risk,
   working-capital check including payment-lag realities of overseas
   invoicing (and UN/multilateral net-30-to-60).
6. **Sourcing engine** — the international analog of the careers page:
   a roster/database of vetted local experts by country and discipline
   (`intl/experts/` — CVs, rates, vetting status, NDAs), built from
   each pursuit and compounding like the library. Job postings stay on
   the existing careers page with location fields; add per-country
   channels (LinkedIn cross-border, local boards) as paste-ready text.
7. **Same operating rules as the domestic system**: every response
   cites the notice's own scope language; email from
   Andrew@pacificresearchllc.com via Outlook; daily run appends an
   INTERNATIONAL section to my morning report; PIPELINE-style board at
   `intl/PIPELINE.md`; honesty rules absolute (never claim experience
   or local presence PRG doesn't have — the MA, the field experience,
   and OAW are the true story; local partners supply the rest and are
   named as such).

## First actions once the design is approved
1. Build the folder skeleton + workflow + gate docs and commit.
2. UNGM vendor registration (with me, exact click-paths + hyperlinks).
3. Extend the SAM matcher with an `--intl` mode (overseas PoP filter,
   State/overseas-DoD posting offices) and run the first report.
4. Screen the first week of notices, pick ONE beachhead pursuit
   (bias: embassy/consulate services or a small advisory/support scope
   in a country where I have field experience — Brazil, Peru, China —
   or an easy-travel post), and run it through the full pipeline.

Ask me only the questions you genuinely need answered (languages I
speak, passport/visa status, travel availability windows, target
countries beyond Brazil/Peru/China, budget for the first BD trip);
default everything else and start building.
