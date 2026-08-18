# PRG International — opportunity sources

Ordered by realistic near-term value to PRG, not by size of the market.
Each entry says what it is, whether PRG can bid it **today**, and the
registration that gates it.

Registration status is tracked in `intl/PIPELINE.md`. A source PRG is not
registered for produces REGISTER–PREPOSITION outcomes, not bids.

---

## Tier 1 — bid today, no new registration

### SAM.gov, filtered to overseas place of performance
PRG's existing SAM registration covers all of this. This is the fastest
path to first international past performance, and it is the only lane
where the SDVOSB certification can still do work (FAR 19.000(b)(1)(ii)
— see `intl/GATE.md` §A1).

Run: `python3 samgov_opportunity_matcher.py --intl --days 7 --limit 100`

Target buyers:
- **State Dept — A/LM/AQM** (Office of Acquisitions Management), the
  regional procurement support offices, and **embassy/consulate local
  procurement** posting to SAM. Small services buys at post are the
  beachhead target.
- **Overseas DoD commands** — EUCOM, AFRICOM, INDOPACOM, CENTCOM,
  SOUTHCOM components; USACE overseas districts; the Army/Navy/Air Force
  contracting offices at OCONUS installations. DoD applies FAR Part 19
  overseas more readily than most.
- **USAID-legacy foreign-assistance programs now administered under
  State** — verify the current administering office on each notice
  rather than assuming, this moved recently.
- **DFC** (U.S. International Development Finance Corporation),
  **USDA/FAS**, **Commerce/ITA**, **Peace Corps**, **State/INL**,
  **State/PRM** (population, refugees, migration — closest fit to the
  Operation Allies Welcome past performance).

### Grants.gov
State Department global-health and foreign-assistance APS/NOFOs that
never touch SAM. Already pulled by the matcher.

---

## Tier 2 — register now, bid within weeks

### UNGM — UN Global Marketplace · https://www.ungm.org/
**The single highest-leverage registration in this lane.** One
registration reaches UNDP, UNOPS, UNICEF, WFP, WHO, IOM, UNHCR and
dozens more. Registration walkthrough: `intl/UNGM_REGISTRATION.md`.

**Know the ceiling before investing time.** UNGM registration levels
gate the contract size PRG may be considered for:

| Level | Contract value | PRG eligible? |
|-------|----------------|---------------|
| Basic | up to US $40,000 | **Yes — today** |
| Level 1 | US $40,000 – $500,000 | **Yes** — needs certificate of incorporation, 3 independent non-affiliated references, owners/principals |
| Level 2 | above US $500,000 | **NO — requires the company to have been established a minimum of 3 years**, plus 3 client reference letters and financial statements |

So PRG's UN lane is **capped at US $500,000 until PRG turns three.**
That is a hard eligibility fact, not a judgment call — it is kill #11 in
`intl/GATE.md`. It also happens to align with the domestic
"first-contract scale" rule, so it costs PRG little in practice.

**Action gating Level 1: line up three independent, non-affiliated
references.** Start now; this is the long pole.

### ReliefWeb · https://reliefweb.int/jobs
UN and NGO short-term consultancies and tenders. Already pulled live by
the matcher (`fetch_reliefweb`) and rendered as its own tab. Market
intelligence plus real individual-consultant gigs.

### WHO consultant rosters · https://www.who.int/careers
Expert rosters and short-term consultancies. The ACRP-PM/CP clinical-
research credentials are a direct fit here and this is one of the few
places the founder's clinical background is the product rather than the
credibility signal.

---

## Tier 3 — development banks: register, monitor, be honest about fit

Borrower-executed tenders are usually won by firms with in-country
presence and prior bank experience. **Individual-consultant assignments
are the realistic entry point** — 20 to 60 days, one person, bank-paid,
and they build the bank past performance that later makes firm-level
bids credible. Treat firm-level ICB tenders as MONITOR until PRG has
either a bank assignment or a local partner prime.

- **World Bank — eConsultant2** · https://wbgeconsult2.worldbank.org/
  Individual and firm consultant selection. Register the firm; also
  create an individual-consultant profile for Andrew.
- **IDB — Inter-American Development Bank** ·
  https://www.iadb.org/en/how-we-can-work-together/consultants
  Latin America and Caribbean. Brazil and Peru field experience is real
  and usable. **PRG does not hold Spanish or Portuguese** (Andrew,
  8/18) — language capability comes from named local partners, never
  claimed for PRG. Do not write a bid that implies otherwise.
- **ADB — Consultant Management System** · https://cms.adb.org/
  Asia-Pacific. Fits the China field experience.
- **UNDP procurement** · https://procurement-notices.undp.org/
  Country-office notices, many small, posted outside UNGM as well.

**Honest assessment for a firm PRG's size:** bank *firm* tenders are
not realistic in year one — they weight prior bank contracts and
in-country offices heavily, and the evaluation math is unforgiving of a
first-time bidder. Bank *individual consultant* assignments are
realistic now. Do not spend proposal hours on the former until the
latter has produced a reference.

---

## Tier 4 — market intelligence and roster plays (not bids)

Register once, get called. These are how surge work finds PRG without a
proposal.

- **Devex** · https://www.devex.com/ — the development sector's
  aggregator. Membership is a real cost; wait until roster flow proves
  out.
- **DevelopmentAid** · https://www.developmentaid.org/ — cheaper
  alternative, same shape.
- **Implementing-partner consultant databases** — register once in each:
  Chemonics, DAI, Tetra Tech International Development, Abt Global,
  FHI 360, Palladium, RTI International, Jhpiego, MSH. These primes hold
  the large State/foreign-assistance contracts and staff surge work from
  their rosters. This is also the **PURSUE AS SUBCONTRACTOR** lane
  overseas — the international analog of SBA SUBNet.
- **OSAC** · https://www.osac.gov/ — State Dept overseas security
  advisory council. Free, and the source for the RISK block's threat
  picture.
- **State Dept Travel Advisories** · https://travel.state.gov/ — the
  advisory level and date go in every RISK block.

---

## Sources deliberately NOT pursued in v1

- **EU / TED tenders** — EU procurement generally requires an EU
  establishment or reciprocal-access basis; not a fit for a U.S.
  micro-firm without an EU partner. Revisit only with a partner.
- **NATO / NSPA** — requires sponsorship by a member nation's delegation
  and NSPA source qualification. Real, but a multi-month registration
  project with no near-term payoff. Backlog it.
- **Host-government direct tenders** — local-firm preference plus local
  entity requirements make most of these kill #10. Only via a local
  partner prime.
