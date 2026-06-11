# Big 4 Tax Intelligence Screener

**Demo label:** TAX-INTEL DEMO  
**Status:** Active development  
**Location:** `mini-richie:/Users/richiesater/dev/big4-sec-screener`

## What This Is

A Streamlit app that pulls SEC EDGAR financial statements for any publicly traded company and generates a ranked Big 4 tax issue analysis: which of the 12 priority 2026 tax issues is most material for this client, and how a Big 4 engagement lead should open the conversation.

## Why It Exists

Big 4 engagement leads need a fast way to prioritize their entry angle when approaching a prospect. A company with $2B in R&D spend has a very different opening than one with heavy import costs or $1.5B in book income. This tool reads their public 10-K and surfaces the highest-leverage issue in 60 seconds.

## The 12 Tax Issues Scored

1. OBBBA R&E expensing (Section 174 retroactive to 2025)
2. OBBBA bonus depreciation (permanent 100%)
3. OBBBA 163(j) EBITDA interest deduction
4. State tax conformity gaps
5. Pillar Two / GloBE (first GIR filings due June 2026)
6. IRS enforcement / audit risk surge
7. Transfer pricing + tariff convergence
8. Tariff UNICAP capitalization exposure
9. Corporate Alternative Minimum Tax (CAMT $1B threshold)
10. Payroll compliance — no tax on tips/overtime
11. R&D tax credit documentation crackdown
12. Transferable clean energy credits opportunity

## How It Works

1. User picks a company from a 900+ Fortune 1000 autocomplete (or a demo profile)
2. App fetches their latest 10-K XBRL facts from SEC EDGAR (free public API, parallel per-concept fetches)
3. Extracts key financial signals: R&D, CapEx, interest expense, book income, foreign income, asset size, inventory/COGS
4. Scores each of the 12 tax issues against those signals with guardrailed, deterministic rules
5. Generates a ranked recommendation brief with advisor framing, talking points, and assumptions/missing data
6. Output is downloadable as a partner meeting brief (Markdown)

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

No API keys required — all data comes from the public SEC EDGAR API.

## Demo Mode

`DEMO-PHARMA` and `DEMO-MFG` are synthetic company profiles built into the app for use when EDGAR is slow or offline. Demo mode is clearly labeled in the output.

## The Demo Suite: Ticker → Delivered Engagement

This screener is Act 1 of a three-part demo suite that follows the tax client lifecycle:

| Act | App | Question it answers |
| --- | --- | --- |
| 1. **Find** | `big4-sec-screener` (this app) | Which tax issues are material for this company, from public data? |
| 2. **Quantify** | `tax-impact` — Tax Regulation Change Impact Agent | What does a specific rule change (e.g. the CAMT notice) do to this client's numbers? |
| 3. **Deliver** | `beps-pillar-two-data-gap-copilot` | Is the client's data ready to comply and file — and if not, exactly what's missing? |

Two of the twelve issues this screener scores — Pillar Two and CAMT — hand off directly to Acts 2 and 3. A related fourth prototype, `tax-provision-agent`, shows the same controlled-AI pattern applied to recurring provision close work.

All apps share one design rule: **deterministic rules decide, AI drafts narrative, professionals review and sign off.**
