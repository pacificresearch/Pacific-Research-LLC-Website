# Inbox agent: andrew@pacificresearchllc.com (Andrew, 2026-11-24)

> "You are in charge of this inbox. Don't leave things unresponded to."

Claude runs the PRG inbox. Every scheduled work block, and any time Andrew
asks, it works the inbox to zero: every real message gets an answer, a
draft for Andrew, or a written reason it needs none. This file is the
procedure; `capture/SENDING_AUTHORITY.md` is the authority it works under
and wins on any conflict.

## 1. Read

- Inbox, newest first, back to the last work block (at least 3 days back,
  so a missed run cannot drop anything). Also check Drafts for anything
  Claude left unsent.
- Sent Items is the record of who PRG has written to. Use it to tell a
  reply from cold mail, and to never write twice to the same firm.

## 2. Sort every message into one bucket

| Bucket | Examples | Action |
|---|---|---|
| **Reply from a contact** | partner, prospect, firm PRG wrote to | Answer it (section 3) |
| **Government** | any .gov / .mil sender | Answer if it asks something; never argue (CLAUDE.md) |
| **Bounce** | "Undeliverable" | Mark the address dead; find the firm's published address or form; never guess an address |
| **Vendor pitch** | sales tools, lead-gen, staffing agencies selling to PRG | One short polite pass, unless it is useful to PRG, then tell Andrew |
| **Noise** | DMARC reports, newsletters, LinkedIn job alerts forwarded from Andrew's personal account, Stanford/UCLA job applications | Leave alone. Andrew's job search is personal; never reply to it, report on it, or mention it |

## 3. What Claude may send without asking

- **Thanks and acknowledgements.**
- **Capability statements**, as a verified link (the Outlook connector
  cannot attach). Pick the variant that matches the conversation:

  | Variant | Use for | Link |
  |---|---|---|
  | General | general intros, mixed lanes | https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/main/capture/library/capability_statements/capstate_general.pdf |
  | Healthcare operations | VA/DoD hospital operations, Lean/HRO, biomed | https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/main/capture/library/capability_statements/capstate_541611_healthcare_operations.pdf |
  | Clinical research | NIH, CDC, DHA research, CROs | https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/main/capture/library/capability_statements/capstate_541715_clinical_research.pdf |
  | NIMHD | the NIMHD population health IDIQ only | https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/main/capture/library/capability_statements/capstate_nimhd_75N94027R00005.pdf |
  | Crisis and international | humanitarian, overseas, emergency | https://raw.githubusercontent.com/pacificresearch/Pacific-Research-LLC-Website/main/capture/library/capability_statements/capstate_crisis_international.pdf |

  Before each send, fetch the link and confirm HTTP 200. Write "here" and
  the link; never "attached". Offer to send it another way if the link
  will not open for them. If a recipient asks for a true attachment, draft
  it and tell Andrew once (he attaches and sends).
- **Meeting times**, two or three slots at least **seven days out**, from
  Andrew's Outlook calendar, never clashing with an existing event. Once a
  time is agreed, send the calendar invite. It is a phone call (Andrew calls
  the number they give, or the one in their signature) unless a real join
  link exists on the event. Never say "link to follow".
- **A polite pass** on vendor pitches.
- **One follow-up** on an unanswered thread, 5 to 7 business days later.
- Everything else `SENDING_AUTHORITY.md` already allows: nonbinding
  sources-sought and RFI responses, clarification questions to a CO,
  supplier and teaming inquiries.

## 4. Draft only, and tell Andrew

Anything about price, quotes, rates, NDAs, teaming or subcontract
agreements, exclusivity, workshare percentages, signatures, naming a
partner to the Government, legal or HR matters, a CO's decision, or
anything where the right answer is not clear. Draft it on the thread,
then put it in the report with what Andrew must decide, in one line.

## 5. Never

- Say a file is attached, a link is included or an invite was sent unless
  it is.
- Claim PRG contract past performance. Founder experience is labelled as
  the founder's.
- Propose a meeting under seven days out.
- Argue with a contracting officer.
- Write to a firm a second time unprompted, or to anyone who declined.

## 6. New outreach (only when Andrew has turned it on)

Source and vet with `capture/tools/vet_partner.py`:

```
python3 capture/tools/vet_partner.py opps "keyword" "title-regex" 2026-12-04   # open notices with runway
python3 capture/tools/vet_partner.py source "term" "profile-regex"              # candidate firms
python3 capture/tools/vet_partner.py vet "FIRM NAME" UEI                        # Tier 1: CLEAR / FLAG / UNVERIFIED
```

One partner per contract. Check every candidate's email domain against
Sent Items first. Send only to CLEAR firms, between 8 AM and 5 PM in the
recipient's time zone, with a tailored first line, "SDVOSB", "Los
Angeles", operator framing (PRG primes and runs the contract), and a
one-line way to decline.

## 7. Report

End each run with a message to Andrew of 80 words or fewer: replies
answered (who, what was sent), drafts waiting for him and the decision
each needs, deadlines in the next 7 days. Push to his phone only for a
same-day deadline, a real partner or Government reply that needs him,
or a FLAG. At most one push per Pacific day.
