# PRG International — compliance rails

Nine rails. Each is a **compliance-matrix row** on every pursuit, with a
named owner and a CLOSED/OPEN state. Rails 1 and 2 gate the pursuit
itself: they close before a local partner is named in a proposal, not
before submission.

This file is an operating checklist, not legal advice. Where a rail says
"get a rated quote" or "confirm with counsel," that is the instruction.

---

## Rail 1 — Sanctions, OFAC, and exclusions (LEGAL KILL)

**Fires on:** every pursuit, every counterparty, every hire, every time.

**This list moves. Verify live on every pursuit — never from memory and
never from this file's snapshot.**

Screening procedure, all four steps, results saved to
`05_sourcing/sanctions_screen_<date>.md`:

1. **Program check** — https://ofac.treasury.gov/sanctions-programs-and-country-information
   for the country of performance and the country of every counterparty.
   Record the program name and the page's last-updated date.
2. **SDN / consolidated list search** — https://sanctionssearch.ofac.treas.gov/
   on: the buyer, every teaming partner and its principals, every local
   agent, every named expert, and the payee bank. Screenshot or save the
   "no match" result with the date.
3. **SAM.gov exclusions** — https://sam.gov/content/exclusions on every
   U.S. counterparty.
4. **UN consolidated list** — https://scsanctions.un.org/consolidated/
   when the buyer is in the UN system or a development bank.

**Snapshot as of 2026-08-18 — treat as a prompt to check, not an
answer.** Active OFAC country/region programs include: Afghanistan,
Balkans, Belarus, Burma, Central African Republic, China (military
companies), Cuba, DRC, Ethiopia, Hong Kong, Iraq, Lebanon, Libya, Mali,
Nicaragua, North Korea, Russia (several), Somalia, South Sudan,
Sudan/Darfur, Syria (now administered as PAARSS — Promoting
Accountability for Assad and Regional Stabilization Sanctions, materially
changed from the pre-2025 comprehensive embargo), Ukraine, Venezuela,
Yemen. **Program scope varies enormously** — some are comprehensive
embargoes, most are targeted at listed persons only. A country appearing
on that list is NOT automatically a kill; a *comprehensive* program or a
*listed counterparty* is.

**The kill:** comprehensive-embargo jurisdictions, any SDN/SSI/blocked
counterparty, any SAM-excluded party, or any structure routing value to
a blocked person. No override. No founder exception. No "the client
confirmed it's fine."

**The not-kill:** a targeted program in a country where PRG's actual
counterparties clear all four checks. Document the clearance and proceed
— with the general license / authorization question answered in writing
if any part of the scope touches a restricted activity.

## Rail 2 — FCPA and local anti-bribery (the #1 legal risk of this model)

**Fires on:** every agent, partner, local hire, fixer, expediter,
customs broker, and anyone else who touches a foreign official on PRG's
behalf.

PRG's model is *travel to post and hire local people.* That is precisely
the fact pattern the FCPA polices: a U.S. company acting through foreign
intermediaries. PRG is liable for what its agents do. The controls:

- **Vet before naming.** `intl/templates/fcpa_vetting_checklist.md`
  completed and filed before any partner or agent appears in a proposal.
- **Rep letter before paying.** `intl/templates/fcpa_rep_letter.md`
  signed before the first dollar moves.
- **Anti-bribery clause in every subcontract and teaming agreement**,
  with audit rights and a termination right for breach. In
  `intl/templates/local_partner_teaming.md`.
- **No cash. Ever.** Every payment by traceable bank transfer to the
  contracted entity's own account. Never to a third party, never to a
  personal account for a corporate payee, never to a jurisdiction other
  than the contract's.
- **Facilitation payments: PRG does not make them.** The FCPA has a
  narrow facilitating-payments exception; most local laws and the UK
  Bribery Act have none, and the exception is a trap. PRG's rule is a
  flat no, stated in the rep letter so the agent knows before they ask.
- **Government-official proximity check** — ask directly whether any
  owner, principal, or family member of a partner is a government
  official or state-enterprise employee, record the answer, and escalate
  to counsel if yes. This is the most common way the rule is broken
  without anyone intending to.
- **Gifts and hospitality** — logged, modest, never around a decision.
- **Red flags that stop a partner cold:** refuses to sign the rep
  letter; wants cash or an offshore account; commission tied to award
  rather than work; "I have a relationship with the ministry"; no
  verifiable business address or prior clients; resists audit rights.

Reference: DOJ/SEC *FCPA Resource Guide* —
https://www.justice.gov/criminal/criminal-fraud/foreign-corrupt-practices-act

## Rail 3 — Defense Base Act insurance

**Fires on:** U.S. government **service** contracts performed outside
the United States (42 U.S.C. §1651 et seq.). Look for FAR 52.228-3 /
52.228-4 in the solicitation, but assume it applies and check rather
than the reverse.

- DBA is workers' compensation for employees on overseas U.S.
  government contracts. It covers PRG's deployed personnel **and, in
  most configurations, local nationals hired to perform.** Confirm local-
  national coverage explicitly — it is the gap that bites.
- **Priced as a rate per $100 of payroll, and the rate is
  threat-dependent.** A war-risk post can be a multiple of a benign
  post's rate. Get a **rated quote for the actual country** before
  pricing. A CONUS placeholder is not a number.
- Some agencies (notably State and USAID-legacy programs) have used a
  single-source DBA program — check whether the solicitation directs a
  specific carrier before shopping.
- **Bind before anyone deploys**, not on award, not on arrival.
- Cost is an allowable direct cost. Price it as a line item; do not bury
  it in overhead.

## Rail 4 — Export controls: ITAR / EAR / OFAC

**Fires on:** anything technical, any hardware crossing a border, any
technical data or software shared with a foreign national — including a
foreign national PRG hires, **including in the United States** (deemed
export).

- Classify first: is anything in scope on the USML (ITAR, 22 CFR
  120–130, State/DDTC) or the CCL (EAR, 15 CFR 730–774, Commerce/BIS)?
  Most of PRG's likely scopes (advisory, research, program support,
  facilities) are not — but medical/lab equipment, comms gear,
  encryption, and anything with a defense end-use can be.
- **Deemed exports:** giving a foreign local hire access to controlled
  technical data is an export to their country of nationality. This
  applies to the hire-locally model directly.
- Registration with DDTC is required to *export* defense articles — if
  a scope requires it and PRG is not registered, that is a
  REGISTER–PREPOSITION, and possibly a kill on the bid clock.
- Screen every foreign party against BIS Entity List / Denied Persons
  as part of Rail 1's search.
- If in doubt on classification, ask for a written determination rather
  than assuming.

## Rail 5 — Local labor law and worker classification

**Fires on:** every local hire, per country. There is no global answer;
this is researched per country and recorded in the country brief.

- **Contractor vs. employee is decided by that country's law, not by
  what the contract says.** Many jurisdictions (much of Latin America
  and Europe especially) reclassify aggressively and attach severance,
  social contributions, and back-tax liability retroactively.
- Questions the country brief must answer: mandatory written contract?
  minimum wage and mandatory bonuses (13th-month pay is common)?
  employer social contributions? notice and severance on termination?
  working-time limits? union/CBA coverage? penalties for
  misclassification?
- **Three structures, in order of PRG preference:**
  1. **Subcontract to a local firm** — the local firm employs; PRG
     manages. Cleanest, and it fits the aggregation model.
  2. **Employer of record (EOR)** — a licensed local provider employs
     the person for PRG. Costs 10–20% on top of salary; buys compliance.
  3. **Direct engagement of an individual as a contractor** — highest
     reclassification risk; use only for genuinely independent,
     short-term, deliverable-based work, and never for someone working
     PRG-directed full-time hours.
- Price the structure. An EOR fee or a local firm's employer burden is
  a real cost and belongs in the build-up.

## Rail 6 — Currency, payment terms, and FX

- **Bill in USD wherever the buyer allows it.** State it in the bid.
- Where USD is not allowed, flag FX exposure explicitly in
  `04_pricing.md`: contract currency, tenor, and what a 10% adverse move
  does to the margin. If the answer is "wipes it out," the margin band
  is wrong.
- **Capital controls and non-convertible currencies** — check whether
  funds can actually leave the country. A receivable that cannot be
  repatriated is not revenue.
- Match currencies where possible: local costs paid in local currency
  from local-currency receipts is a natural hedge.
- Confirm who pays wire and correspondent-bank fees. On a small
  contract these are not trivial.
- **Payment lag is the real number, not the stated one.** UN and
  multilateral terms are nominally net-30 to net-60; practice runs
  longer. Build the working-capital float from the practical figure.

## Rail 7 — Visas, work authorization, and entry

**Fires on:** founder travel and every deployed person.

- Visa category for the actual activity — a business-visitor visa
  usually does **not** cover performing paid work. Getting this wrong
  risks the person and the contract.
- Lead time for the visa, and whether it can be obtained on the
  proposal-to-start timeline. If not, say so before promising a start
  date.
- Passport validity (six months beyond entry is the common rule) and
  blank pages.
- Vaccination and health entry requirements.
- **Country clearance** — travel to a post in an official capacity may
  require country clearance through the embassy (eCC). Ask the CO/COR.
- Invitation or sponsorship letter from the buyer where required.
- Record all of it in the country brief so the second trip is cheap.

## Rail 8 — DSSR travel rates

**Fires on:** every pursuit — founder travel is in all of them.

- Per-diem (lodging + M&IE) by post from the **Department of State
  Standardized Regulations**, Office of Allowances:
  https://aoprals.state.gov/content.asp?content_id=184&menu_id=78
- Rates are **post-specific and change monthly** — pull the rate for the
  actual post on the actual pricing date and cite the effective date in
  `04_pricing.md`.
- Also from the same source where applicable: post hardship
  differential, danger pay, and cost-of-living allowances — these are
  the government's own quantification of how hard a post is, and they
  are useful evidence when justifying a higher price.
- Airfare priced from real fares on the real dates, with a change
  allowance. Add ground transport, visa fees, vaccinations, and
  security-driven transport as separate lines.

## Rail 9 — Tax presence and permanent establishment

**Fires on:** any pursuit with sustained in-country presence.

- Sustained activity in a country can create a **permanent
  establishment** and a local corporate tax filing obligation. Thresholds
  vary by country and by treaty.
- Check whether a **U.S. income tax treaty** with the country exists and
  what its PE article says — https://www.irs.gov/businesses/international-businesses/united-states-income-tax-treaties-a-to-z
- Local withholding tax on payments to a foreign contractor is common
  and can be 5–20% off the top. **If the buyer withholds, the bid price
  must account for it** — this is a frequent, expensive surprise.
- VAT/GST: is PRG's service taxable locally, is the buyer exempt (UN
  agencies and diplomatic missions usually are), and can PRG recover?
- Subcontracting to a local firm rather than operating directly is often
  the cleanest PE answer as well as the cleanest labor answer.
- **Escalate to a cross-border tax advisor before the first contract
  with sustained presence.** Do not improvise this one.
