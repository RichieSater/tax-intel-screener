## Project Overview
* **Project name:** big4-sec-financial-screener
* **Demo label:** TAX-INTEL DEMO — SEC Financial Intelligence Screener
* **What it does:** Scrapes SEC EDGAR financial statements (10-K filings) for publicly traded companies, analyzes which 2026 tax issues are most material based on the company's actual financials, and generates ranked sales recommendations for advisory engagement leads.
* **Tech stack:** Python 3.9+, Streamlit, SEC EDGAR API (data.sec.gov), Anthropic Claude API, pandas.
* **Main language:** Python.

## Product Goals
* Pull real 10-K financial data from SEC EDGAR for any US public company by ticker.
* Score each of the 12 priority 2026 tax issues against the company's financials.
* Rank issues by materiality and generate a Big 4 sales recommendation brief.
* Present as a controlled demo: analysis is intelligence, not tax advice.
* Demo-ready with fallback synthetic data when EDGAR is slow or unavailable.

## Project Structure
* `app.py` — Streamlit main app: ticker input, financial fetch, issue scoring, recommendation output.
* `src/edgar.py` — SEC EDGAR API client: fetch CIK by ticker, pull latest 10-K XBRL facts, extract key financial metrics.
* `src/tax_issues.py` — 2026 tax issue definitions, financial signal rules, and scoring logic.
* `src/analyzer.py` — Claude API call: takes financial profile and issue scores, generates ranked sales recommendation brief.
* `src/report.py` — Report formatting: structured output, PDF-ready export, presenter-mode display.
* `data/tax_issues_2026.json` — Canonical issue list with descriptions, signals, Big 4 framing, and talking points.
* `data/demo_companies.json` — Synthetic fallback profiles for demo mode when EDGAR is unavailable.
* `docs/demo-story.md` — Demo arc, presenter notes, audience beliefs, objection handling.
* `tests/test_edgar.py` — EDGAR client unit tests.
* `tests/test_scoring.py` — Tax issue scoring logic tests.

## Key Commands
* **Install dependencies:** `pip install -r requirements.txt`
* **Run dev server:** `streamlit run app.py`
* **Run tests:** `python -m pytest tests/ -v`

## Rules - Always Do
1. Always read `data/tax_issues_2026.json` as the source of truth for issue definitions.
2. Always label AI-generated recommendations as intelligence and analytical output, not tax advice.
3. Always show the data source (EDGAR filing reference) for each financial metric used.
4. Always fall back to synthetic demo data if EDGAR is unavailable; never leave the demo broken.
5. Always run tests after code changes.
6. Always treat the demo path as primary: ticker → fetch → score → recommend → export.

## Rules - Never Do
1. Never store real client data or API keys in the repo.
2. Never imply the publisher has approved, reviewed, or endorsed the output.
3. Never remove the "intelligence not advice" disclaimer from report outputs.
4. Never hardcode a single company — the app must work for any ticker.
5. Never install new packages without noting the reason in requirements.txt.
6. **NEVER modify `src/tax_issues.py` or `data/tax_issues_2026.json` autonomously.**
   The scoring system was calibrated across 30+ real companies through step-by-step
   human-in-the-loop review. Every scoring rule exists because a real company produced
   a wrong result and the fix was verified against multiple companies before committing.
   If you change a threshold, a sector flag, or a signal weight autonomously, you will
   silently break other companies that were already correct. Scoring changes ONLY happen
   when Richie is actively in the session reviewing outputs step by step — not during
   autonomous runs. If you believe a score is wrong, write a note to
   `docs/scoring-review-queue.md` describing the company, the issue, and what you
   observed. Do not touch the scoring code itself. See `docs/scoring-guardrails.md`.

## Scoring System — Read Before Touching Anything
The scoring in `src/tax_issues.py` is not simple rule logic. It is the result of
iterative calibration across three batches of 10 real public companies each. Key
design decisions encoded in the current scoring:

- **Sector flags** (`is_financial`, `is_hospitality`, `is_retail`, `is_tech_or_internet`,
  `is_utility_or_energy`, `is_service_cogs`) exist because generic COGS/interest/ETR
  proxies fire incorrectly for service industries. Do not remove or broaden them.
- **163(j) financial institution exclusion** — banks' $50B+ interest expense is deposit
  funding cost, not business interest. Removing this makes every bank a false 163(j) lead.
- **Transfer pricing `is_service_cogs` exclusion** — UNH's 81% COGS is medical claims,
  not imports. FedEx's COGS is fuel and labor, not goods. These are NOT transfer pricing.
- **IRS enforcement UTP tiers** — the old flat +65/+20 made every large company score 85.
  UTP size is the discriminating signal; asset size is only the base.
- **Tariff UNICAP mega-importer tier** — designed for HD/WMT/COST scale ($50B+ COGS).
  Lower-tier signals still fire for mid-size importers.
- **Transferable credits utility boost** — NextEra Energy and similar clean energy
  utilities are the PRIMARY IRA §6418 transferability candidates. The sector flag is
  intentional; do not remove it thinking "this should apply to all companies."

If a scoring result looks wrong, READ THIS FILE and `docs/scoring-guardrails.md`
before drawing conclusions about what to change.
