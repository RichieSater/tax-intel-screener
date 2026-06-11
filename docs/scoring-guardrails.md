# Scoring System Guardrails

**TL;DR: Do not modify `src/tax_issues.py` or `data/tax_issues_2026.json` during autonomous runs. Ever.**

## Why This File Exists

The scoring system in `src/tax_issues.py` was calibrated over three sessions of
batch testing against 30 real public companies. Every scoring rule, threshold,
and sector flag represents a deliberate decision made after observing a real
company produce a wrong result. None of these are arbitrary numbers.

## Validation Protocol

The only acceptable way to change scoring is:

1. Richie is actively in the session (not autonomous Hermes run)
2. A specific company produces a result that is verifiably wrong
3. The proposed fix is stated explicitly with reasoning
4. The fix is run against the company that was broken AND several previously-correct companies
5. 10/10 tests pass after the fix
6. The fix is committed with a message explaining which company it fixes and why

## What Each Scoring Decision Protects

### Sector flags

| Flag | What it prevents |
|------|-----------------|
| `is_financial` | 163(j) false positive for banks — $50B bank interest is deposit funding, not business interest |
| `is_hospitality` | Payroll underscoring for restaurants — franchised model hides COGS signal |
| `is_retail` | Payroll signal for large hourly retail workforces |
| `is_tech_or_internet` | R&D undisclosed flag for AMZN/tech that don't break out R&D separately |
| `is_utility_or_energy` | Transferable credits boost — utilities ARE the §6418 transferability candidate |
| `is_service_cogs` | Prevents healthcare claims (UNH) and logistics costs (FDX) from triggering import-COGS transfer pricing and tariff UNICAP proxies |

### IRS enforcement UTP tiers (added batch 3)

The old scoring gave every >$10B company a score of 85. This made IRS enforcement
always appear as a top-2 issue regardless of actual controversy exposure.

The current scoring uses UTP balance as the primary discriminating signal:
- $5B+ UTP → 85+ (tech, pharma, leveraged telecoms with huge controversy portfolios)
- $500M–$1B UTP → 65–75 (moderate exposure)  
- <$100M UTP + large assets → ~55 (large but tax-simple companies)

### Transfer pricing tiers and false positives (fixed batch 2 + 3)

- Required positive foreign income (negative FI was firing abs() check — UNH had -$196M)
- Added `is_service_cogs` exclusion from COGS-ratio proxy
- Tiered foreign income: >$5B → 85, >$1B → 55, >$500M → 35
- This made ABBV (Irish IP structure, $10B FI) correctly rank as top-3 TP candidate

### Tariff UNICAP mega-importer tier

- $50B+ COGS at 55%+ ratio → +70 (HD, WMT, COST)
- Without this tier, mega-importers scored 55 — below IRS/CAMT noise

### 163(j) leverage tiers

- Tiered interest: $5B+ → 65, $1B+ → 55, $200M+ → 35
- Mega-debt tier: $50B+ → +20 bonus
- Specifically fixed AT&T ($136B debt, $6.8B interest) which was scoring 65 and ranked 4th

## If You Think a Score Is Wrong

Write to `docs/scoring-review-queue.md`:

```
## [TICKER] — [Date]
**Issue:** [Which tax issue seems wrong]
**Observed score:** [Score]
**Expected:** [What you think it should be and why]
**Company profile:** [Key financials that are relevant]
**Do not change scoring until reviewed by Richie.**
```
