# Big 4 Tax Intelligence Screener — Demo Story

**Demo label:** TAX-INTEL DEMO  
**Updated:** 2026-06-08

## The One-Sentence Pitch

> Big 4 engagement leads enter any public company ticker and get a ranked list of which 2026 tax issues are most material for that client — based on their actual SEC filings — plus a ready-to-use conversation opener for the first meeting.

## The Problem It Solves

A Big 4 partner walking into a first meeting with a Fortune 500 CFO has 30 seconds to establish credibility before the conversation becomes generic. The difference between "we help companies with tax issues" and "your $3.8B R&D expense creates a specific retroactive Section 174 recovery opportunity that needs to be filed this quarter" is the difference between a follow-up and an engagement.

This tool gives the partner the second version of that sentence, derived from the company's own public filings.

## Five-Minute Demo Arc

### 0:00–0:30 — Set the scene

> "Before a first client meeting, a Big 4 engagement lead needs to know which of the twelve major 2026 tax issues is actually relevant for this specific company — not in general, but based on their numbers. That used to take a day of research. This does it in sixty seconds."

### 0:30–1:30 — Enter a real ticker

Type `PFE` or `MSFT` or `CAT`. Watch the EDGAR fetch complete.

Say:
> "This is pulling their actual 10-K data from SEC EDGAR — the same source their auditors use. Revenue, R&D, CapEx, interest expense, book income, foreign income. No synthetic data for a real company."

### 1:30–2:30 — Show the rankings

Point to the top three issues with red/yellow/green scores.

Say:
> "The scoring maps their financial profile to the twelve biggest 2026 tax issues. A pharmaceutical company with $3.8B in R&D scores very differently than a manufacturer with $2B in CapEx and heavy imports. The rankings are driven by their actual numbers."

### 2:30–3:30 — Drill into the top issue

Click the top-ranked issue. Show matched signals.

Say:
> "Here's why this issue ranks first: [read the matched signal]. That's not a general tax tip — that's a specific reason why this issue matters for this company at this scale."

### 3:30–4:30 — Show the brief

Scroll to the Advisory Recommendation Brief.

Say:
> "This is the output a partner prints before the meeting. Opening line, primary issue, two supporting issues, the specific numbers to reference, and what not to overclaim. It's grounded in their SEC filings."

### 4:30–5:00 — Close

> "The value isn't the rankings — it's the specificity. A generic tax pitch loses to one that starts with the company's own numbers. Your advisor can deliver that at scale with this kind of screening layer in the engagement development workflow."

## Audience Beliefs This Demo Must Create

1. The output is grounded in real public data — not opinions or generic lists.
2. The ranking logic reflects actual financial materiality, not marketing priority.
3. A Big 4 partner could walk into a meeting with this brief and sound immediately credible.
4. This is an engagement development tool, not final tax advice.
5. Richie understands both the tax issues and the sales/advisory context well enough to build this.

## Objections and Responses

**"Is this tax advice?"**  
No. It's intelligence derived from public filings — the same kind of analysis a partner would do manually before a meeting. The brief explicitly says professional review is required.

**"What if the EDGAR data is incomplete?"**  
EDGAR has full XBRL financials for all 10-K filers. The scoring is conservative — it only flags issues where the financial signal is clearly material. Missing data shows as N/A, not a false score.

**"Why would a Big 4 partner need this?"**  
They wouldn't for clients they know well. The use case is prospect development and cross-sell: quickly screening a new company or a client's subsidiary before a first call.

**"Does Big 4 have something like this already?"**  
This demo shows Richie understands the workflow well enough to build it. The conversation is about whether a Big 4 firm wants to build it properly with their data, their issue frameworks, and their brand.

## What to Avoid

- Do not suggest this replaces Big 4 tax judgment — it augments pre-meeting prep.
- Do not claim the AI-generated brief is a Big 4 deliverable.
- Do not demo on a company with a bad EDGAR data year — use demo companies if needed.
- Do not linger on the EDGAR fetch — it can be slow. Have DEMO-PHARMA or DEMO-MFG ready.

## Where This Fits: The Three-Demo Arc

The three demos follow one client's journey through the tax engagement lifecycle:

1. **Find (this app).** A partner screens a target company from public SEC data and walks into the first
   meeting knowing which 2026 issues are material. Pillar Two and CAMT are two of the twelve issues scored.
2. **Quantify (`tax-impact`).** The screener flagged CAMT — the Tax Regulation Change Impact Agent models the
   IRS notice against the client's profile and produces an impact matrix, draft memo, and action list.
3. **Deliver (`beps-pillar-two-data-gap-copilot`).** The screener flagged Pillar Two — the Data-Gap Copilot
   takes the signed engagement into execution: source-data intake, gap register, safe-harbour triage,
   and a gated GIR readiness memo.

The connective line to say out loud:

> "Act 1 finds the opportunity from public data. Act 2 quantifies it against the client's numbers.
> Act 3 delivers it with audit-ready controls. Same design rule throughout: deterministic rules decide,
> AI drafts the narrative, professionals review and sign off."

When Pillar Two or CAMT lands in the top issues during this demo, the app shows the suite handoff inline —
use that moment to bridge to the next demo.

A related fourth prototype, `tax-provision-agent`, applies the same controlled-AI pattern to recurring
provision close work (the recurring-revenue side of the same story).
