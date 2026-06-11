"""Big 4 sales brief generator — deterministic template injection, no external API."""

from typing import Optional


# ── Formatters ────────────────────────────────────────────────────────────────

def _fmt(v: Optional[float], prefix: str = "$") -> str:
    if v is None:
        return "N/A"
    a = abs(v)
    if a >= 1e9:
        return f"{prefix}{a/1e9:.1f}B"
    if a >= 1e6:
        return f"{prefix}{a/1e6:.0f}M"
    return f"{prefix}{a:,.0f}"

def _pct(v: Optional[float]) -> str:
    return f"{v:.1%}" if v is not None else "N/A"


# ── Per-issue opening lines ───────────────────────────────────────────────────
# Each receives (company_name, profile dict) and returns a single sentence.

_OPENINGS = {
    "obbba_r_e": lambda co, p:
        f"{co}'s {_fmt(p.get('rd_expense'))} R&D spend makes the OBBBA's retroactive §174 fix "
        f"the first number worth putting on the table.",
    "obbba_163j": lambda co, p:
        f"The OBBBA moved §163(j) back to an EBITDA base — {co}'s {_fmt(p.get('interest_expense'))} "
        f"in annual interest expense is why this conversation is timely.",
    "obbba_bonus_depreciation": lambda co, p:
        f"{co} is running a {_fmt(p.get('capex'))} capital program under rules that just "
        f"fundamentally changed — permanent 100% bonus depreciation rewrites the depreciation schedule.",
    "pillar_two": lambda co, p:
        f"The GIR filing deadline is June 30, and {co}'s international footprint puts them "
        f"squarely in scope — that's what makes this meeting timely.",
    "irs_enforcement": lambda co, p:
        f"{co}'s {_fmt(p.get('uncertain_tax_positions'))} in unrecognized tax benefits is a real "
        f"number, and the IRS is staffing up specifically to scrutinize companies at this scale.",
    "transfer_pricing": lambda co, p:
        f"The same intercompany prices {co} uses to minimize tax are now being reviewed by customs "
        f"to set duty values — {_fmt(p.get('foreign_income'))} in foreign income puts both sides in play.",
    "tariff_unicap": lambda co, p:
        f"{co}'s {_fmt(p.get('inventory'))} inventory position means every new tariff tranche "
        f"is a §263A capitalization event that most finance teams aren't measuring.",
    "camt": lambda co, p:
        f"{co}'s {_fmt(p.get('net_income'))} in book income puts them in CAMT territory — "
        f"and with final regs still pending, the exposure isn't fully quantified.",
    "payroll_compliance": lambda co, p:
        f"The no-tax-on-tips provision affects {co}'s workforce more directly than most — "
        f"the implementation gap between the statute and what payroll systems currently do is real.",
    "state_conformity": lambda co, p:
        f"{co}'s multistate footprint means the OBBBA creates a fresh set of diverging "
        f"federal-state treatments to manage simultaneously.",
    "rd_credit_documentation": lambda co, p:
        f"{co}'s {_fmt(p.get('rd_expense'))} R&D program sits above the threshold where the "
        f"IRS's new documentation standards create real exposure if records don't meet the bar.",
    "transferable_credits": lambda co, p:
        f"{co} is in the primary beneficiary category for IRA transferable credits — "
        f"the question is whether they're monetizing them or leaving value on the table.",
}

_DEFAULT_OPENING = lambda co, p: \
    f"{co} has several 2026 tax issues worth prioritising — here's where Your advisor can add the most immediate value."


# ── Per-issue "what to avoid" lines ──────────────────────────────────────────

_AVOID = {
    "obbba_r_e":
        "Don't claim the analysis is fast — §174 method changes require a formal IRS filing. "
        "Don't conflate domestic and foreign R&E; the 15-year amortization on foreign R&E is still live.",
    "obbba_163j":
        "Don't imply the EBITDA restoration eliminates all limits — §163(j) still applies. "
        "Frame it as expanding the deductible base and recovering carryforwards, not removing the cap.",
    "obbba_bonus_depreciation":
        "Don't imply this is a new planning opportunity — frame it as replanning under permanent rules "
        "vs. the phased-down rates they may have modelled last year.",
    "pillar_two":
        "Don't quote jurisdiction-specific effective tax rates off the cuff — GloBE calculations are "
        "fact-intensive. Stick to filing deadlines and data infrastructure as the entry point.",
    "irs_enforcement":
        "Don't imply they're under investigation — frame as getting ahead of a systematic IRS initiative, "
        "not responding to a specific audit signal.",
    "transfer_pricing":
        "Don't lead with audit risk. Lead with documentation and the tariff convergence angle — "
        "customs and tax are now reviewing the same prices for opposite reasons.",
    "tariff_unicap":
        "Don't conflate §263A with trade policy. This is a tax accounting issue — "
        "capitalising tariffs into inventory cost basis — not an argument about the tariffs themselves.",
    "camt":
        "Don't quote a specific CAMT liability figure — final regs are pending and interim guidance "
        "has changed. The pitch is modelling exposure and identifying optimisation levers.",
    "payroll_compliance":
        "Don't imply their current payroll is non-compliant — implementing guidance is still being "
        "written. Frame as proactive preparation before the W-2 code changes go live.",
    "state_conformity":
        "Don't cite specific non-conformity counts by state — these change frequently. "
        "Lead with the exposure framework, not the exact number.",
    "rd_credit_documentation":
        "Don't imply existing credits are at risk unless there is a specific signal. "
        "Frame as strengthening documentation proactively ahead of heightened IRS scrutiny.",
    "transferable_credits":
        "Don't promise a specific transfer price — the market rate varies. "
        "Lead with whether they have transferable credits and what the monetisation pathway looks like.",
}

_DEFAULT_AVOID = (
    "Don't overclaim certainty on exposure amounts — these are signals from public financials, "
    "not a completed analysis. Frame everything as 'worth quantifying', not 'you owe X'."
)


# ── Key financial facts ───────────────────────────────────────────────────────

def _key_facts(top_issues: list[dict], profile: dict) -> list[str]:
    """Pull the 3 most citation-worthy numbers given the top issues."""
    seen: list[str] = []
    iids = {x["id"] for x in top_issues}

    candidates = [
        ("rd_expense",              "R&D expense",                "obbba_r_e", "rd_credit_documentation"),
        ("interest_expense",        "annual interest expense",     "obbba_163j"),
        ("capex",                   "capital expenditure",         "obbba_bonus_depreciation"),
        ("foreign_income",          "foreign income",              "pillar_two", "transfer_pricing"),
        ("uncertain_tax_positions", "unrecognized tax benefits",   "irs_enforcement"),
        ("inventory",               "inventory on hand",           "tariff_unicap"),
        ("net_income",              "book net income",             "camt"),
        ("total_debt",              "long-term debt",              "obbba_163j"),
        ("revenue",                 "total revenue",               None),
        ("effective_tax_rate",      "effective tax rate",          "pillar_two", "camt"),
    ]

    for row in candidates:
        key, label = row[0], row[1]
        relevant_ids = set(row[2:])
        v = profile.get(key)
        if v is None:
            continue
        if relevant_ids and not (relevant_ids & iids):
            # Skip non-relevant metrics unless we still need facts
            if len(seen) >= 2:
                continue
        if key == "effective_tax_rate":
            fact = f"Effective tax rate: {_pct(v)}"
        else:
            fact = f"{label.capitalize()}: {_fmt(v)}"
        seen.append(fact)
        if len(seen) == 3:
            break

    # Pad if we somehow have fewer than 3
    if len(seen) < 3 and profile.get("total_assets"):
        seen.append(f"Total assets: {_fmt(profile.get('total_assets'))}")

    return seen[:3]


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_recommendation_brief(
    profile: dict,
    scored_issues: list[dict],
    top_n: int = 3,
) -> str:
    company = profile.get("company_name") or profile.get("ticker", "this company")
    ticker  = profile.get("ticker", "")
    top     = [x for x in scored_issues if x["score"] > 0][:top_n]

    if not top:
        return f"### Pre-Meeting Tax Intelligence — {company}\n\nInsufficient public financial data to generate a ranked brief."

    primary = top[0]
    iid     = primary["id"]

    opening_fn = _OPENINGS.get(iid, _DEFAULT_OPENING)
    opening    = opening_fn(company, profile)

    # Primary paragraph: talking point + framing from issue JSON
    primary_talking = primary.get("talking_point", "")
    primary_framing = primary.get("advisor_framing", "")
    primary_signals = "; ".join(primary.get("matched_signals", [])[:2])
    primary_para    = (
        f"{primary_talking} "
        f"{primary_framing}"
    ).strip()

    # Supporting issues: one sentence each from talking_point
    supporting = []
    for iss in top[1:top_n]:
        supporting.append(
            f"**{iss['title']}** (score {iss['score']}/100) — {iss.get('talking_point','')}"
        )

    facts = _key_facts(top, profile)
    avoid = _AVOID.get(iid, _DEFAULT_AVOID)

    source = profile.get("data_source", "SEC public filings")

    lines = [
        f"### Pre-Meeting Tax Intelligence — {company} ({ticker})",
        "",
        f"**Opening:** {opening}",
        "",
        f"**Primary Entry Point — {primary['title']}** _{primary_signals}_",
        "",
        primary_para,
        "",
        "**Supporting Issues**",
        "",
    ]
    for s in supporting:
        lines.append(f"- {s}")
    lines += [
        "",
        "**Key Financial Facts to Reference**",
        "",
    ]
    for f in facts:
        lines.append(f"- {f}")
    lines += [
        "",
        f"**What to Avoid:** {avoid}",
        "",
        f"_Source: {source}_",
    ]

    return "\n".join(lines)
