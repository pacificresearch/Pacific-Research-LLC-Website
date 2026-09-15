# Local expert roster — the international analog of the careers page

This is the sourcing engine. It compounds exactly like
`capture/library/`: every pursuit adds vetted people whether or not PRG
wins, and by the third pursuit in a region PRG can staff a bid in days
instead of weeks. **A lost bid that leaves behind three vetted local
experts was not a loss.**

## Structure

```
intl/experts/
  ROSTER.md                        # the index — everyone, at a glance
  <country>/
    <lastname_firstname>/
      cv.pdf
      profile.md                   # rates, availability, languages, scope
      vetting/                     # FCPA checklist, sanctions screen
      nda_signed.pdf
      rep_letter_signed.pdf
  firms/
    <country>_<firm>/              # local firms, same shape
```

## Rules

1. **Nobody goes in a proposal before their vetting folder is complete.**
   `intl/templates/fcpa_vetting_checklist.md` closed, sanctions screen
   saved with its date, rep letter signed. This is Rail 2 and it is not
   negotiable.
2. **Rates are recorded with their source and date.** A rate without a
   date is worthless in twelve months.
3. **Availability is refreshed every 60 days** for anyone PRG intends to
   name. Overseas commitments go stale fast — local experts take other
   work and stop answering.
4. **Rejections are recorded too**, with the reason. A party rejected
   for a Rail 2 red flag stays rejected across pursuits; check here
   before vetting anyone new.
5. **Consent before naming.** Written permission before a CV goes into a
   proposal, and a letter of intent or contingent commitment for anyone
   named as key personnel.
6. **Never describe roster members as PRG staff.** They are named
   partners, subcontractors, or contingent hires. See the honesty rules
   in `intl/WORKFLOW.md`.

## How people get here

- Every pursuit's sourcing track (`intl/WORKFLOW.md` §1d)
- Founder BD travel — the main reason the trips pay for themselves
- Referrals from vetted partners (still fully vetted; a referral is not
  a clearance)
- Careers-page applicants with the post as the location field
- Implementing-partner and UN roster networks
