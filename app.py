"""Big 4 Tax Intelligence Screener — Streamlit app."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import json
from typing import Optional
from edgar import get_financial_profile
from tax_issues import score_profile
from analyzer import generate_recommendation_brief

# --- Pre-load company list for autocomplete ---
@st.cache_data
def load_companies() -> list[dict]:
    base = os.path.dirname(__file__)
    path = os.path.join(base, "data", "companies.json")
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []

# --- Demo fallback companies ---
DEMO_COMPANIES = {
    "DEMO-PHARMA": {
        "ticker": "DEMO-PHARMA",
        "company_name": "Acme Pharmaceutical Corp (Demo)",
        "cik": "demo",
        "revenue": 18_500_000_000,
        "net_income": 4_200_000_000,
        "rd_expense": 3_800_000_000,
        "capex": 1_200_000_000,
        "interest_expense": 380_000_000,
        "total_assets": 42_000_000_000,
        "total_debt": 8_500_000_000,
        "depreciation_amortization": 2_100_000_000,
        "inventory": 2_800_000_000,
        "cogs": 6_200_000_000,
        "income_tax_expense": 650_000_000,
        "deferred_tax_assets": 1_200_000_000,
        "uncertain_tax_positions": 480_000_000,
        "foreign_income": 2_900_000_000,
        "ebitda": 7_330_000_000,
        "effective_tax_rate": 0.134,
        "data_source": "Demo data (synthetic — pharma profile)",
    },
    "DEMO-MFG": {
        "ticker": "DEMO-MFG",
        "company_name": "Titan Manufacturing Inc (Demo)",
        "cik": "demo",
        "revenue": 12_000_000_000,
        "net_income": 980_000_000,
        "rd_expense": 420_000_000,
        "capex": 2_100_000_000,
        "interest_expense": 520_000_000,
        "total_assets": 28_000_000_000,
        "total_debt": 9_200_000_000,
        "depreciation_amortization": 1_800_000_000,
        "inventory": 3_400_000_000,
        "cogs": 8_400_000_000,
        "income_tax_expense": 280_000_000,
        "deferred_tax_assets": 800_000_000,
        "uncertain_tax_positions": 120_000_000,
        "foreign_income": 1_100_000_000,
        "ebitda": 3_580_000_000,
        "effective_tax_rate": 0.222,
        "data_source": "Demo data (synthetic — manufacturing profile)",
    },
}


# --- Demo suite handoffs: issues that the companion demos take from screening to delivery ---
DEMO_SUITE_HANDOFFS = {
    "pillar_two": (
        "**Suite handoff →** When Pillar Two screens material, the next step is the "
        "**Pillar Two Data-Gap Copilot** (companion demo): source-data readiness, gap register, "
        "safe-harbour triage, and a GIR readiness memo."
    ),
    "camt": (
        "**Suite handoff →** When CAMT screens material, the next step is the "
        "**Tax Regulation Change Impact Agent** (companion demo): models the IRS notice against "
        "the company's profile and drafts an impact memo and action list."
    ),
}

HANDOFF_NEXT_STEPS = {
    "pillar_two": "Pillar Two screens material — propose a GIR data-readiness assessment (Pillar Two Data-Gap Copilot).",
    "camt": "CAMT screens material — propose a regulation-change impact analysis of the current IRS notice (Tax Regulation Change Impact Agent).",
}


def is_demo_profile(profile: dict) -> bool:
    return str(profile.get("cik", "")).lower() == "demo" or str(profile.get("data_source", "")).startswith("Demo data")


def resolve_profile(ticker: str, cik: str = None, company_name: str = None, sector: str = None, industry: str = None, fetcher=get_financial_profile):
    """
    Resolve a ticker to a financial profile.
    Demo tickers return synthetic profiles instantly.
    CIK/name/sector/industry come from companies.json — no live metadata lookups.
    """
    ticker = ticker.strip().upper()
    if ticker in DEMO_COMPANIES:
        return dict(DEMO_COMPANIES[ticker]), "Demo mode: using synthetic company profile."

    profile = fetcher(ticker, cik=cik, company_name=company_name, sector=sector, industry=industry)
    return profile, None


def fmt_usd(v):
    if v is None:
        return "N/A"
    if abs(v) >= 1e9:
        return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"


DISPLAY_METRICS = [
    ("Revenue", "revenue"),
    ("Net Income", "net_income"),
    ("R&D Expense", "rd_expense"),
    ("CapEx", "capex"),
    ("Interest Expense", "interest_expense"),
    ("Total Assets", "total_assets"),
    ("Total Debt", "total_debt"),
    ("EBITDA", "ebitda"),
    ("Effective Tax Rate", "effective_tax_rate"),
    ("Foreign Income", "foreign_income"),
    ("UTP Balance", "uncertain_tax_positions"),
    ("Inventory", "inventory"),
]


def _format_metric_value(profile: dict, key: str) -> str:
    val = profile.get(key)
    if key == "effective_tax_rate":
        return f"{val:.1%}" if val is not None else "N/A"
    return fmt_usd(val)


def _metric_source(profile: dict, key: str) -> str:
    if is_demo_profile(profile):
        return "Synthetic demo metric"
    source = (profile.get("source_metadata") or {}).get(key) or {}
    concept = source.get("concept")
    period = source.get("period")
    if concept and period:
        return f"{concept} / {period}"
    if concept:
        return concept
    return "SEC EDGAR XBRL — concept unavailable"


def build_metric_rows(profile: dict) -> list[dict]:
    rows = []
    for label, key in DISPLAY_METRICS:
        rows.append({
            "Metric": label,
            "Value": _format_metric_value(profile, key),
            "Source": _metric_source(profile, key),
        })
    return rows


def _key_numbers(profile: dict) -> list[str]:
    preferred = [
        ("Revenue", "revenue"),
        ("R&D expense", "rd_expense"),
        ("Foreign income", "foreign_income"),
        ("CapEx", "capex"),
        ("Total assets", "total_assets"),
        ("Effective tax rate", "effective_tax_rate"),
    ]
    numbers = []
    for label, key in preferred:
        value = _format_metric_value(profile, key)
        if value != "N/A":
            numbers.append(f"- {label}: {value} ({_metric_source(profile, key)})")
        if len(numbers) == 3:
            break
    return numbers or ["- No reliable financial metric available; use the profile table before citing numbers."]


def build_meeting_brief_markdown(profile: dict, scored: list[dict], recommendation_brief: str) -> str:
    company = profile.get("company_name", profile.get("ticker", "Company"))
    ticker = profile.get("ticker", "")
    source = profile.get("data_source", "SEC EDGAR")
    top_issues = scored[:3]
    lines = [
        f"# Partner Meeting Brief — {company}",
        "",
        f"- Ticker: {ticker}",
        f"- Data source: {source}",
        f"- Data mode: {'Synthetic demo profile' if is_demo_profile(profile) else 'Live SEC EDGAR XBRL'}",
        "",
        "## Top 3 issues with talking points",
    ]
    for i, issue in enumerate(top_issues, 1):
        lines += [
            f"{i}. {issue['title']} — screening score {issue['score']}/100",
            f"   - Talking point: {issue['talking_point']}",
            f"   - Signals: {'; '.join(issue.get('matched_signals', []))}",
            f"   - Assumptions & missing data: {issue.get('assumptions_missing_data', 'Requires professional review.')}",
        ]
    next_steps = [
        f"- {HANDOFF_NEXT_STEPS[issue['id']]}"
        for issue in top_issues
        if issue.get("id") in HANDOFF_NEXT_STEPS and issue.get("score", 0) >= 30
    ]
    if next_steps:
        lines += ["", "## Recommended engagement next steps", *next_steps]
    lines += [
        "",
        "## 3 key numbers to cite",
        *_key_numbers(profile),
        "",
        "## Recommendation brief",
        recommendation_brief,
        "",
        "## Disclaimer",
        "This meeting brief is screening intelligence derived from public SEC filings or clearly labeled synthetic demo data. It is not tax advice, legal advice, or professional advisory work product. All conclusions require review by qualified tax professionals.",
    ]
    return "\n".join(lines)


# --- Page config ---
st.set_page_config(
    page_title="Big 4 Tax Intelligence Screener",
    page_icon="📊",
    layout="wide",
)

# --- Header ---
st.title("📊 Big 4 Tax Intelligence Screener")
st.caption(
    "Analyzes SEC EDGAR 10-K financial statements and ranks 2026 tax issues by materiality. "
    "Output is analytical intelligence — not tax advice."
)

with st.sidebar:
    st.markdown("### Demo suite: ticker → delivered engagement")
    st.markdown(
        "1. **Find** — this screener ranks which 2026 tax issues are material "
        "for a target company, from public SEC filings.\n"
        "2. **Quantify** — the *Tax Regulation Change Impact Agent* models a specific "
        "rule change (e.g. the CAMT notice) against the client's profile.\n"
        "3. **Deliver** — the *Pillar Two Data-Gap Copilot* turns the engagement into "
        "execution: data readiness, gaps, safe harbours, filing memo.\n"
    )
    st.caption(
        "Same design rule across all three: deterministic rules decide, "
        "AI drafts narrative, professionals review and sign off."
    )

st.markdown("---")

# --- Build company options for autocomplete ---
companies = load_companies()
_company_lookup = {c["ticker"]: c for c in companies}

# Options: blank placeholder + all real companies (sorted by name) + demo entries
_real_options = sorted(
    [f"{c['ticker']} — {c['name']}" for c in companies],
    key=lambda s: s.split(" — ", 1)[-1],
)
_demo_options = ["DEMO-PHARMA — Acme Pharmaceutical Corp (Demo)", "DEMO-MFG — Titan Manufacturing Inc (Demo)"]
ALL_OPTIONS = [""] + _real_options + _demo_options

# --- Input ---
col1, col2 = st.columns([2, 1])
with col1:
    selected_option = st.selectbox(
        "Select a company:",
        options=ALL_OPTIONS,
        index=0,
        placeholder="Type a ticker or company name to search...",
        help="Start typing to filter — works by ticker symbol or company name.",
    )

with col2:
    top_n = st.slider("Issues to highlight in brief", min_value=1, max_value=5, value=3)

# Parse selection
ticker_input = ""
selected_meta: dict = {}
if selected_option:
    ticker_input = selected_option.split(" — ")[0].strip().upper()
    selected_meta = _company_lookup.get(ticker_input, {})

run_btn = st.button("Analyze", type="primary", disabled=not ticker_input)

if run_btn and ticker_input:
    # --- Fetch ---
    with st.spinner(f"Fetching financial data for {ticker_input}..."):
        profile, fetch_warning = resolve_profile(
            ticker_input,
            cik=selected_meta.get("cik"),
            company_name=selected_meta.get("name"),
            sector=selected_meta.get("sector"),
            industry=selected_meta.get("industry"),
        )

    if fetch_warning:
        if is_demo_profile(profile):
            st.warning(fetch_warning)
        else:
            st.info(fetch_warning)

    # --- Score ---
    with st.spinner("Scoring tax issues..."):
        scored = score_profile(profile)

    # --- Brief ---
    with st.spinner("Generating advisory recommendation brief..."):
        brief = generate_recommendation_brief(profile, scored, top_n=top_n)

    # --- Display ---
    st.markdown("---")
    st.subheader(f"📋 {profile.get('company_name', ticker_input)}")
    st.caption(f"Data source: {profile.get('data_source', 'SEC EDGAR')}")

    with st.expander("Financial profile (from 10-K)", expanded=False):
        st.table(build_metric_rows(profile))

    st.subheader("Tax Issue Rankings")
    for issue in scored:
        score = issue["score"]
        color = "🔴" if score >= 60 else "🟡" if score >= 30 else "🟢"
        urgency_label = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM"}.get(issue.get("urgency", ""), "")
        with st.expander(f"{color} {issue['title']} — Score: {score}/100  {urgency_label}"):
            st.write(f"**Advisor framing:** {issue['advisor_framing']}")
            st.write(f"**Talking point:** _{issue['talking_point']}_")
            st.write(f"**Matched signals:**")
            for sig in issue.get("matched_signals", []):
                st.write(f"  - {sig}")
            st.write(f"**Assumptions & missing data:** {issue.get('assumptions_missing_data', 'Requires company-specific professional review.')}")
            if issue.get("id") in DEMO_SUITE_HANDOFFS and score >= 30:
                st.info(DEMO_SUITE_HANDOFFS[issue["id"]])

    st.markdown("---")
    st.subheader("Tax Advisory Brief")
    st.markdown(brief)

    export_brief = build_meeting_brief_markdown(profile, scored, brief)
    st.download_button(
        "Download partner meeting brief (Markdown)",
        data=export_brief,
        file_name=f"{profile.get('ticker', ticker_input).lower()}-tax-intel-brief.md",
        mime="text/markdown",
    )

    st.markdown("---")
    st.caption(
        "⚠️ This output is analytical intelligence derived from public SEC filings. "
        "It is not tax advice, legal advice, or a professional advisory work product. "
        "All conclusions require review by qualified tax professionals."
    )
