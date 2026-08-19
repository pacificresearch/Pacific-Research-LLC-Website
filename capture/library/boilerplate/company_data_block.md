# Company data block — paste-ready identity fields

Pulled from `capture/library/company_profile.md`, which is the single
source of truth. **Never retype these from memory.** If anything here
disagrees with company_profile.md, company_profile.md wins and this file
gets corrected.

## Short block (email signatures, cover pages, form headers)

```
Pacific Research Group LLC
Service-Disabled Veteran-Owned Small Business (SBA-certified)
UEI J585TLDV1CH1 · CAGE 1Z9B6
Orange, CA 92867 · (650) 213-2381
Andrew@pacificresearchllc.com · pacificresearchllc.com
```

## Signature block (CO correspondence)

```
Andrew O'Donnell
Managing Director
Pacific Research Group LLC
UEI J585TLDV1CH1 · CAGE 1Z9B6
(650) 213-2381
Andrew@pacificresearchllc.com
pacificresearchllc.com
```

**Style rule (standing):** state SDVOSB **once** per document. Do not
spell it out in the signature block as well as the body — it reads as
padding to a CO who sees it fifty times a week.

## Logo in email — how it actually has to work

**Claude cannot put the logo in an email body.** The Outlook connector
sanitises HTML against a narrow allowlist and **strips `<img>`** (along
with `<style>` and `<span>`) before sending. Embedding, hotlinking, or
base64-inlining the mark all fail the same way — the tag is removed and
the recipient sees nothing.

**The logo belongs in Andrew's Outlook signature**, configured once, and
then it rides on every message automatically:

> Outlook (web): Settings ⚙ → Mail → Compose and reply → Email
> signature → insert the image (the paperclip/picture icon in the
> signature editor) → set it to apply to new messages **and** replies →
> Save.
> Outlook (desktop): File → Options → Mail → Signatures → New →
> insert picture → set for New messages and Replies/forwards.

Use `site/assets/logo-primary-navy.png`, resized to roughly 120–160 px
wide. Keep the text lines above as the signature text beneath it.

**Once the Outlook signature is set, do NOT repeat the signature block
in the message body** — it is applied at send time and you would get it
twice. Draft bodies end at "Respectfully, / Andrew O'Donnell" and let
the signature carry the identity lines.

## Full block (registrations, forms, reps & certs)

| Field | Value |
|---|---|
| Legal name | Pacific Research Group LLC |
| Entity type | Single-member LLC |
| UEI | J585TLDV1CH1 |
| CAGE | 1Z9B6 |
| Certifications | SBA-Certified SDVOSB · VOSB |
| SAM status | Active |
| Primary NAICS | 541714 — R&D in Biotechnology |
| Address | Orange, CA 92867 |
| Phone | (650) 213-2381 |
| CO correspondence | Andrew@pacificresearchllc.com |
| Public inquiries | contact@pacificresearchllc.com |
| Website | pacificresearchllc.com |

## Not held — state plainly if asked, never imply otherwise
No bonding capacity · no facility clearance (FCL) · no GSA schedule ·
not 8(a) / HUBZone / WOSB.
