# Contingent Job Posting — template

Generate one file per position in the opportunity's `05_staffing/`.
Output BOTH the paste-ready posting and the structured fields (for
LinkedIn/Indeed/ATS forms). Every pre-award posting MUST carry the
contingency line. Do not name the solicitation number or agency office
beyond what's public on SAM.

---

## Structured fields
- **Title:** [from PWS position description]
- **Location:** [place of performance city/state; onsite/hybrid/remote]
- **Type:** [Full-time / Part-time / 1099] — **contingent upon contract award**
- **Anticipated start:** [PoP start]
- **Pay:** [WD rate or market range — post the range; several states require it]
- **Required credentials:** [certs/licenses verbatim from the solicitation]

## Posting text

**[Title] — [City, State] (Contingent Upon Contract Award)**

Pacific Research Group LLC, a Service-Disabled Veteran-Owned Small
Business, is recruiting a [title] in support of an anticipated federal
contract with [agency, public level only].

**This position is contingent upon contract award.**

**Responsibilities:** [3–6 bullets translated from PWS tasks — duties,
not contract language]

**Required:** [education, certs, clearance eligibility, years — exactly
the solicitation's minimums; don't inflate]

**Preferred:** [genuine differentiators for evaluation]

**Compensation:** [range] plus [H&W/benefits per SCA if applicable]

PRG is an equal opportunity employer. Veterans encouraged to apply.

---

## Careers-page snippet (generate alongside every posting)

Insert between the `<!-- JOBS:START -->` / `<!-- JOBS:END -->` markers in
`site/careers/index.html` (remove the empty-state block when the first
posting goes live; restore it when the last one closes). Two parts per
posting:

```html
<article class="job-card" id="[slug]">
  <h3>[Title]</h3>
  <div class="job-meta">
    <span class="badge badge-green">Contingent Upon Contract Award</span>
    <span class="tag">[City, State]</span>
    <span class="tag">[Full-time / Part-time / 1099]</span>
    <span class="tag">[$XX–$XX/hr or salary range]</span>
  </div>
  <p>[One-paragraph summary from the posting text.]</p>
  <ul>
    <li>[Top 3 responsibilities]</li>
  </ul>
  <p><strong>Required:</strong> [minimums, one line]</p>
  <div class="apply-row">
    <a class="btn btn-primary" data-icon="send"
       href="mailto:contact@pacificresearchllc.com?subject=Application%3A%20[Title%20URL-encoded]">Apply by Email</a>
    <span class="job-note">Attach resume + certifications. Posted [date].</span>
  </div>
</article>

<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "JobPosting",
  "title": "[Title]",
  "description": "<p>[Full posting text as escaped HTML — Google requires the complete description here, not a summary.]</p>",
  "datePosted": "[YYYY-MM-DD]",
  "validThrough": "[YYYY-MM-DDT00:00]",
  "employmentType": "[FULL_TIME / PART_TIME / CONTRACTOR]",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "Pacific Research Group LLC",
    "sameAs": "https://pacificresearchllc.com",
    "logo": "https://pacificresearchllc.com/assets/logo-primary-navy.png"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "[City]",
      "addressRegion": "[ST]",
      "addressCountry": "US"
    }
  },
  "baseSalary": {
    "@type": "MonetaryAmount",
    "currency": "USD",
    "value": {"@type": "QuantitativeValue",
      "minValue": [min], "maxValue": [max], "unitText": "[HOUR/YEAR]"}
  }
}
</script>
```

Google for Jobs indexes these automatically via the sitemap (careers URL
is listed at `weekly` change frequency). Keep `validThrough` honest —
expired postings with stale markup hurt indexing. The same source fields
fill the LinkedIn/Indeed manual paste below.

## Candidate tracking
| Candidate | Source | Resume on file | Screen | Contingent offer / LOI signed | Named in proposal? | Last contact |
|-----------|--------|----------------|--------|-------------------------------|--------------------|--------------|

Key personnel named in the proposal need a signed contingent offer or
letter of intent BEFORE submission. Re-touch all committed candidates
every 2 weeks until award decision.
