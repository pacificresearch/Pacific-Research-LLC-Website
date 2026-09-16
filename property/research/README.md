# Research files — the human/agent-verified layer

The code never invents catalysts, incentives, landlord rules or tax
treatment. Those come from `research/markets/<cbsa>.yaml`, filled by the
weekly Claude run (web search) or by Andrew, **with a source URL on every
item**. Absent file ⇒ the report says UNKNOWN / NOT RESEARCHED and the
catalyst score rests on fundamentals only.

`research/drafts/<cbsa>.json` holds Brave Search leads (when the key
exists). Leads are tiered by source quality and are NOT facts until moved
into the market YAML with `verified: true`.

Schema: see `TEMPLATE.yaml`. Statuses for catalysts:
`announced` (0.45 credit) · `under_construction` / `dirt_moving` (1.0) ·
`completed` (0.6) · `speculative` (0.15) · `cancelled` (0).
