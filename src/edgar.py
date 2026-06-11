"""
Financial data client — SEC EDGAR XBRL companyconcept API.

No Yahoo Finance / yfinance dependency.
Works from any server IP including Streamlit Cloud.

Per-field fetches run in parallel (ThreadPoolExecutor) so total latency
is ~2-4 seconds rather than the sum of all individual calls.
"""

import concurrent.futures
import urllib.request
import json
from typing import Optional

EDGAR_BASE = "https://data.sec.gov"
_HEADERS = {"User-Agent": "Tax-Intel-Screener richiesater@gmail.com"}

# Ordered lists of GAAP concept names per field — first non-None 10-K value wins.
# Lists ordered by how commonly each concept appears across Fortune 1000 filers.
_CONCEPTS: dict[str, list[str]] = {
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueGoodsNet",
    ],
    "net_income": [
        "NetIncomeLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
        "ProfitLoss",
    ],
    "rd_expense": [
        "ResearchAndDevelopmentExpense",
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "CapitalExpendituresIncurringObligation",
    ],
    "interest_expense": [
        "InterestExpenseDebt",
        "InterestExpense",
        "InterestAndDebtExpense",
    ],
    "total_assets": [
        "Assets",
    ],
    "long_term_debt": [
        "LongTermDebt",
        "LongTermDebtNoncurrent",
        "LongTermNotesPayable",
    ],
    "current_debt": [
        "LongTermDebtCurrent",
        "DebtCurrent",
        "ShortTermBorrowings",
        "NotesPayableCurrent",
    ],
    "inventory": [
        "InventoryNet",
        "InventoryFinishedGoodsAndWorkInProcess",
        "InventoryFinishedGoods",
    ],
    "cogs": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
        "CostOfGoodsSoldAndServicesSold",
    ],
    "income_tax_expense": [
        "IncomeTaxExpenseBenefit",
    ],
    "da": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "Depreciation",
    ],
    "foreign_income": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesForeign",
    ],
    "uncertain_tax_positions": [
        "UnrecognizedTaxBenefits",
    ],
    "deferred_tax_assets": [
        "DeferredTaxAssetsGross",
        "DeferredTaxAssetsNet",
    ],
}


def edgar_cik(ticker: str) -> Optional[str]:
    """Return zero-padded 10-digit CIK via EDGAR company_tickers.json.
    Callers should pre-supply cik from companies.json to avoid this lookup."""
    try:
        req = urllib.request.Request(
            "https://www.sec.gov/files/company_tickers.json",
            headers=_HEADERS,
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.load(r)
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                return str(entry["cik_str"]).zfill(10)
    except Exception:
        pass
    return None


def _concept_value(cik: str, concept: str) -> Optional[float]:
    """Fetch the most recent 10-K annual value for one XBRL concept."""
    url = f"{EDGAR_BASE}/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status != 200:
                return None
            data = json.load(r)
        units = data.get("units", {})
        for unit_key in ("USD", "pure"):
            entries = [
                e for e in units.get(unit_key, [])
                if e.get("form") == "10-K" and e.get("val") is not None
            ]
            if entries:
                best = sorted(entries, key=lambda x: x.get("end", ""), reverse=True)[0]
                return float(best["val"])
    except Exception:
        pass
    return None


def _fetch_field(cik: str, field: str) -> tuple:
    """Try each concept for the field in order; return first non-None value."""
    for concept in _CONCEPTS.get(field, []):
        val = _concept_value(cik, concept)
        if val is not None:
            return field, val, concept
    return field, None, None


def get_financial_profile(
    ticker: str,
    cik: str = None,
    company_name: str = None,
    sector: str = None,
    industry: str = None,
) -> dict:
    """
    Fetch financial profile from SEC EDGAR companyconcept XBRL API.

    Pass cik from the pre-enriched companies.json to skip the tickers.json
    lookup. Pass company_name/sector/industry from the same source.
    """
    if not cik:
        cik = edgar_cik(ticker)
    if not cik:
        raise ValueError(
            f"Could not find CIK for '{ticker}'. "
            "Verify the ticker symbol or select a company from the dropdown."
        )

    company_name = company_name or ticker.upper()
    sector       = sector   or ""
    industry     = industry or ""

    # Fetch all fields in parallel — total latency ≈ slowest single concept (~1-2s)
    fields = list(_CONCEPTS.keys())
    results: dict[str, Optional[float]] = {}
    concept_used: dict[str, Optional[str]] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(fields)) as pool:
        future_map = {pool.submit(_fetch_field, cik, f): f for f in fields}
        for future in concurrent.futures.as_completed(future_map):
            field, val, concept = future.result()
            results[field]      = val
            concept_used[field] = concept

    revenue               = results.get("revenue")
    net_income            = results.get("net_income")
    rd_expense            = results.get("rd_expense")
    capex                 = results.get("capex")
    interest_expense      = results.get("interest_expense")
    total_assets          = results.get("total_assets")
    long_term_debt        = results.get("long_term_debt") or 0
    current_debt          = results.get("current_debt")  or 0
    inventory             = results.get("inventory")
    cogs                  = results.get("cogs")
    income_tax_expense    = results.get("income_tax_expense")
    da                    = results.get("da")
    foreign_income        = results.get("foreign_income")
    uncertain_tax_positions = results.get("uncertain_tax_positions")
    deferred_tax_assets   = results.get("deferred_tax_assets")

    total_debt = long_term_debt + current_debt

    ebitda = None
    if all(v is not None for v in [net_income, income_tax_expense, interest_expense, da]):
        ebitda = net_income + income_tax_expense + interest_expense + da

    pretax = (net_income or 0) + (income_tax_expense or 0)
    effective_tax_rate = (
        income_tax_expense / pretax
        if pretax and income_tax_expense is not None and pretax != 0
        else None
    )

    def lineage(field: str) -> dict:
        return {
            "concept": concept_used.get(field) or "Not found in EDGAR XBRL",
            "period":  "Most recent 10-K",
            "source":  "SEC EDGAR companyconcept",
        }

    source_metadata = {f: lineage(f) for f in _CONCEPTS}

    return {
        "ticker":                    ticker.upper(),
        "company_name":              company_name,
        "cik":                       cik,
        "revenue":                   revenue,
        "net_income":                net_income,
        "rd_expense":                rd_expense,
        "capex":                     capex,
        "interest_expense":          interest_expense,
        "total_assets":              total_assets,
        "total_debt":                total_debt,
        "depreciation_amortization": da,
        "inventory":                 inventory,
        "cogs":                      cogs,
        "income_tax_expense":        income_tax_expense,
        "deferred_tax_assets":       deferred_tax_assets,
        "uncertain_tax_positions":   uncertain_tax_positions,
        "foreign_income":            foreign_income,
        "ebitda":                    ebitda,
        "effective_tax_rate":        effective_tax_rate,
        "sector":                    sector,
        "industry":                  industry,
        "data_source":               f"SEC EDGAR XBRL (CIK {cik})",
        "source_metadata":           source_metadata,
    }
