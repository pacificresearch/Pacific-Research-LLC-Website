# Sources-sought / RFI response — template

**Standing rule (Andrew, 8/19): only include what the notice asks for.**
A CO reads dozens of these. Everything that does not answer their notice
is noise, and noise is what gets a firm remembered as unserious.

## Length

**Under 200 words of body.** If it runs longer, the extra is almost
always credentials the notice never asked about.

## What goes in

1. **The notice's own questions, in its order, in its words.** Most
   sources sought ask specific things — capability, business size,
   NAICS concurrence, prior similar work, ability to meet a schedule.
   Answer those. Nothing else is "responsive."
2. **Only the capability that maps to THIS scope.** One or two facts
   that a CO could verify and that bear on this requirement. Not the
   credential stack.
3. **A compact identity line** — name, UEI, CAGE, size/socioeconomic
   status. One line, at the end.
4. **Contact.**

## What stays out — unless the notice asks

- ❌ FAR 9.104-1 responsibility recital
- ❌ "PRG confirms current, active SAM.gov registration" — the CO can
  see SAM; saying it wastes a sentence
- ❌ Credentials unrelated to the scope (CBET on a software buy, ACRP on
  a paving buy, the $2M portfolio on anything that isn't equipment)
- ❌ Headline metrics as decoration
- ❌ Set-aside advocacy **as a reflex**

**On set-aside advocacy — the one nuance.** When the notice states its
purpose is market research to determine whether a set-aside is
appropriate, saying PRG is an SDVOSB small business under the notice's
NAICS **is** the responsive answer and belongs. Bolting it onto a notice
that isn't asking is the error.

## Shape

```
Re: <notice number> — <notice title>

<One sentence: PRG is responding, and can perform the scope, named in
the notice's own words.>

<One short paragraph OR the notice's numbered questions answered in
order. Only capability that bears on this scope.>

Pacific Research Group LLC · UEI J585TLDV1CH1 · CAGE 1Z9B6 ·
SBA-certified SDVOSB small business under NAICS <the notice's NAICS>.

Andrew O'Donnell, Managing Director
Andrew@pacificresearchllc.com · (650) 213-2381
pacificresearchllc.com
```

## Worked example — the rewrite that prompted this rule

**Before** (sent 8/17, 118 words of boilerplate on every notice):

> Pacific Research Group LLC (UEI J585TLDV1CH1, CAGE 1Z9B6), an
> SBA-certified SDVOSB, responds to the subject notice and affirms its
> interest and capability to perform this requirement. PRG's leadership
> is a U.S. military veteran and AAMI Certified Biomedical Equipment
> Technician (CBET) with USAF biomedical equipment training who has
> managed over $2M in medical equipment infrastructure at a greater than
> 98% preventive-maintenance and compliance rate aligned to Joint
> Commission and DoD standards. PRG provides equipment maintenance,
> monitoring, and support services in VA and federal healthcare settings
> with credential-verified technicians under prime-level management and
> quality control. PRG confirms current, active SAM.gov registration and
> responsibility in accordance with FAR 9.104-1, and respectfully
> encourages consideration of a set-aside for which PRG qualifies.

Identical text went to a loading-dock concrete notice, a bat-removal
notice, a ServiceNow staffing notice, and a proprietary-software
subscription. The biomedical credentials were irrelevant on all four.

**After** — e.g. for a biomedical equipment maintenance sources sought:

> Re: <notice> — <title>
>
> Pacific Research Group LLC responds to the subject notice and can
> perform the scheduled and corrective maintenance described in the
> notice.
>
> Our Managing Director is an AAMI Certified Biomedical Equipment
> Technician (USAF 4A2X5) who has sustained a $2M+ medical equipment
> portfolio at a >98% preventive-maintenance and compliance rate to
> Joint Commission and DoD accreditation standards. PRG performs as
> prime with credential-verified technicians under its own QC.
>
> Pacific Research Group LLC · UEI J585TLDV1CH1 · CAGE 1Z9B6 ·
> SBA-certified SDVOSB small business under NAICS 811219.

Same firm, half the words, every sentence earning its place — and the
credentials only appear because this notice is about equipment
maintenance.

## Email mechanics
- Send from **Andrew@pacificresearchllc.com** (Outlook).
- **First contact on a notice** → `outlook_send_mail`.
- **Replying to a CO** → reply on their thread
  (`capture/WORKFLOW.md` Stage 2). Never `send_mail` with "RE:".
- Signature block: `capture/library/boilerplate/company_data_block.md`.
  Logo comes from Andrew's configured Outlook signature — it cannot be
  injected into the body (see that file).
