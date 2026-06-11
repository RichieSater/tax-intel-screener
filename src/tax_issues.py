"""Tax issue scoring — maps financial profile metrics to 2026 Big 4 tax issue relevance scores."""

import json
import os
from typing import Optional

_ISSUES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tax_issues_2026.json")


def load_issues() -> list[dict]:
    with open(_ISSUES_PATH) as f:
        return json.load(f)["issues"]


def score_profile(profile: dict) -> list[dict]:
    """
    Score a financial profile against all tax issues.
    Returns list of issues sorted by score descending, each with a score and matched signals.
    """
    issues = load_issues()
    results = []

    sector   = (profile.get("sector")   or "").lower()
    industry = (profile.get("industry") or "").lower()
    is_financial = any(x in sector + " " + industry for x in
        ["financial", "bank", "insurance", "credit services", "asset management", "capital markets"])
    is_hospitality = any(x in sector + " " + industry for x in
        ["restaurant", "hospitality", "hotel", "lodging", "food service",
         "quick service", "casual dining", "fast food"])
    is_retail = any(x in sector + " " + industry for x in
        ["retail", "apparel", "department", "grocery", "discount"])
    is_tech_or_internet = any(x in sector + " " + industry for x in
        ["technology", "internet", "software", "semiconductor", "electronic"])
    is_utility_or_energy = any(x in sector + " " + industry for x in
        ["utilities", "regulated electric", "regulated gas", "independent power",
         "renewable", "solar", "wind"])
    is_service_cogs = any(x in sector + " " + industry for x in
        ["healthcare plans", "managed care", "health insurance",
         "freight", "logistics", "courier", "air delivery",
         "financial services", "bank", "insurance", "capital markets"])
    rev = profile.get("revenue") or 0
    rd = profile.get("rd_expense") or 0
    capex = profile.get("capex") or 0
    interest = profile.get("interest_expense") or 0
    assets = profile.get("total_assets") or 0
    debt = profile.get("total_debt") or 0
    net_income = profile.get("net_income") or 0
    ebitda = profile.get("ebitda") or 0
    foreign_income = profile.get("foreign_income") or 0
    utp = profile.get("uncertain_tax_positions") or 0
    etr = profile.get("effective_tax_rate")
    inventory = profile.get("inventory") or 0
    cogs = profile.get("cogs") or 0
    da = profile.get("depreciation_amortization") or 0

    for issue in issues:
        score = 0
        matched = []

        iid = issue["id"]

        if iid == "obbba_r_e":
            if rd > 1_000_000_000:
                score += 70; matched.append(f"R&D >${rd/1e9:.1f}B")
            elif rd > 500_000_000:
                score += 50; matched.append(f"R&D >${rd/1e6:.0f}M")
            elif rd > 100_000_000:
                score += 30; matched.append(f"R&D >${rd/1e6:.0f}M")
            if foreign_income and rd > 50_000_000:
                score += 20; matched.append("Foreign income (foreign R&E 15-yr amortization still applies)")
            elif rd > 5_000_000_000 and not foreign_income:
                score += 15; matched.append("Large global R&D program — foreign R&E likely material (15-yr amortization still applies; verify in 10-K)")
            if rd == 0 and is_tech_or_internet:
                score += 40
                matched.append(
                    "R&D expense not separately disclosed in standard financials "
                    "(company may report as Technology and Infrastructure or similar); "
                    "Section 174 exposure likely material — verify in 10-K.")

        elif iid == "obbba_bonus_depreciation":
            if capex > 1_000_000_000:
                score += 60; matched.append(f"CapEx >${capex/1e9:.1f}B")
            elif capex > 500_000_000:
                score += 45; matched.append(f"CapEx >${capex/1e6:.0f}M")
            elif capex > 100_000_000:
                score += 25; matched.append(f"CapEx >${capex/1e6:.0f}M")
            if da and da > 500_000_000:
                score += 15; matched.append(f"D&A >${da/1e6:.0f}M (asset-heavy)")

        elif iid == "obbba_163j":
            if is_financial:
                matched.append("Financial institution — §163(j) EBITDA limitation does not apply"
                               " to bank deposit funding costs; skip this issue.")
                score = 0
                results.append({**issue, "score": 0, "matched_signals": matched,
                                "assumptions_missing_data": _assumptions_missing_data(iid, matched)})
                continue
            if interest > 5_000_000_000:
                score += 65; matched.append(f"Interest expense >${interest/1e9:.1f}B — highly leveraged capital structure")
            elif interest > 1_000_000_000:
                score += 55; matched.append(f"Interest expense >${interest/1e6:.0f}M")
            elif interest > 200_000_000:
                score += 35; matched.append(f"Interest expense >${interest/1e6:.0f}M")
            elif interest > 50_000_000:
                score += 15; matched.append(f"Interest expense >${interest/1e6:.0f}M")
            if ebitda and interest and ebitda > 0:
                ratio = interest / ebitda
                if ratio > 0.3:
                    score += 30; matched.append(f"Interest/EBITDA ratio {ratio:.0%} — high leverage")
            if debt > 50_000_000_000:
                score += 20; matched.append(f"Mega-leveraged ({debt/1e9:.0f}B debt) — review prior-year disallowed interest carryforwards")
            elif debt > 1_000_000_000:
                score += 15; matched.append(f"Long-term debt >${debt/1e9:.1f}B")

        elif iid == "state_conformity":
            # Proxy: large US revenue with no dominant foreign exposure
            us_revenue_proxy = rev - abs(foreign_income) if foreign_income else rev
            if assets > 5_000_000_000:
                score += 40; matched.append(f"Total assets >${assets/1e9:.1f}B (multistate exposure)")
            elif assets > 1_000_000_000:
                score += 20; matched.append(f"Total assets >${assets/1e9:.1f}B")
            if rd > 100_000_000:
                score += 15; matched.append("R&D spend — OBBBA conformity gap creates state divergence")
            if capex > 200_000_000:
                score += 15; matched.append("CapEx — bonus depreciation state conformity gap")

        elif iid == "pillar_two":
            # Foreign income or large revenue is the key signal
            if foreign_income and abs(foreign_income) > 750_000_000:
                score += 80; matched.append(f"Foreign income >${abs(foreign_income)/1e9:.1f}B (above GloBE threshold)")
            elif foreign_income and abs(foreign_income) > 200_000_000:
                score += 50; matched.append(f"Foreign income >${abs(foreign_income)/1e6:.0f}M")
            elif rev > 2_000_000_000:
                score += 30; matched.append(f"Revenue >${rev/1e9:.1f}B (likely above GloBE threshold — verify foreign split)")
            if etr is not None and etr < 0.15:
                score += 25; matched.append(f"Effective tax rate {etr:.1%} — below 15% GloBE minimum")

        elif iid == "irs_enforcement":
            # Base: asset tier tells us IRS jurisdiction, not audit intensity
            if assets > 10_000_000_000:
                score += 45; matched.append(f"Total assets >${assets/1e9:.0f}B (IRS Large Business & International territory)")
            elif assets > 1_000_000_000:
                score += 30; matched.append(f"Total assets >${assets/1e9:.1f}B (IRS large business threshold)")
            elif assets > 250_000_000:
                score += 15; matched.append(f"Total assets >${assets/1e6:.0f}M (IRS audit rate surge applies)")
            # UTP is the key discriminating signal — size of unsettled tax controversy
            if utp > 5_000_000_000:
                score += 40; matched.append(f"UTP ${utp/1e9:.1f}B — substantial unresolved tax controversy portfolio")
            elif utp > 1_000_000_000:
                score += 30; matched.append(f"UTP ${utp/1e9:.1f}B — significant uncertain tax positions under IRS scrutiny")
            elif utp > 500_000_000:
                score += 20; matched.append(f"UTP ${utp/1e6:.0f}M — material uncertain tax positions")
            elif utp > 50_000_000:
                score += 10; matched.append(f"UTP ${utp/1e6:.0f}M")
            # Low ETR signals aggressive planning = higher audit scrutiny
            if etr is not None and 0 < etr < 0.10:
                score += 10; matched.append(f"ETR {etr:.1%} — below-market rate signals scrutinized positions")

        elif iid == "transfer_pricing":
            if foreign_income and foreign_income > 5_000_000_000:
                score += 85; matched.append(f"Foreign income >${foreign_income/1e9:.1f}B — multinational IP/operational structure")
            elif foreign_income and foreign_income > 1_000_000_000:
                score += 55; matched.append(f"Foreign income >${foreign_income/1e9:.1f}B")
            elif foreign_income and foreign_income > 500_000_000:
                score += 35; matched.append(f"Foreign income >${foreign_income/1e6:.0f}M")
            if not is_service_cogs and cogs and rev and (cogs / rev) > 0.5 and cogs > 5_000_000_000:
                score += 25; matched.append(f"COGS ratio {cogs/rev:.0%} — import-heavy operations likely")
            if not is_service_cogs and foreign_income and foreign_income > 0 and cogs and (cogs / rev if rev else 0) > 0.4:
                score += 25; matched.append("High COGS + foreign income → likely intercompany transactions")

        elif iid == "tariff_unicap":
            if not is_service_cogs and cogs and rev and (cogs / rev) > 0.55 and cogs > 50_000_000_000:
                score += 70; matched.append(f"Mega-importer — COGS ${cogs/1e9:.0f}B ({cogs/rev:.0%} of revenue); §263A tariff capitalization is material")
            elif not is_service_cogs and cogs and rev and (cogs / rev) > 0.5 and cogs > 500_000_000:
                score += 40; matched.append(f"COGS >${cogs/1e6:.0f}M ({cogs/rev:.0%} of revenue) — import exposure likely")
            if inventory > 10_000_000_000:
                score += 20; matched.append(f"Inventory >${inventory/1e9:.1f}B — substantial §263A tariff capitalization impact")
            elif inventory > 500_000_000:
                score += 15; matched.append(f"Inventory >${inventory/1e6:.0f}M — tariff capitalization under §263A")

        elif iid == "camt":
            # CAMT applies to companies with >$1B average annual book income
            if net_income and net_income > 5_000_000_000:
                score += 80; matched.append(f"Net income >${net_income/1e9:.1f}B — clearly in CAMT territory")
            elif net_income and net_income > 1_000_000_000:
                score += 60; matched.append(f"Net income >${net_income/1e9:.1f}B — likely in CAMT territory")
            elif net_income and net_income > 300_000_000:
                score += 30; matched.append(f"Net income >${net_income/1e6:.0f}M — CAMT analysis warranted")
            if etr is not None and etr < 0.10 and net_income and net_income > 500_000_000:
                score += 25; matched.append(f"Low ETR {etr:.1%} with high book income — CAMT gap risk")

        elif iid == "payroll_compliance":
            # Score based on sector first; fall back to COGS proxy only when sector is unknown
            if is_hospitality:
                score += 70; matched.append(f"Hospitality/restaurant sector — large tipped and hourly workforce")
            elif is_retail:
                score += 50; matched.append(f"Retail sector — large hourly workforce, tip/overtime reporting required")
            elif rev and cogs and rev > 500_000_000 and (cogs / rev) > 0.5:
                score += 30; matched.append("High revenue, high COGS ratio — likely large hourly workforce")

        elif iid == "rd_credit_documentation":
            if rd > 200_000_000:
                score += 35; matched.append(f"R&D >${rd/1e6:.0f}M — R&D credit documentation risk")
            elif rd > 50_000_000:
                score += 20; matched.append(f"R&D >${rd/1e6:.0f}M")

        elif iid == "transferable_credits":
            if is_utility_or_energy and capex > 1_000_000_000:
                score += 65; matched.append(f"Utility/clean energy sector with CapEx >${capex/1e9:.1f}B — primary ITC/PTC transferability candidate under IRA §6418")
            elif is_utility_or_energy:
                score += 40; matched.append("Utility/clean energy sector — likely ITC/PTC transferability candidate")
            if etr is not None and etr < 0.05 and net_income and net_income > 100_000_000:
                score += 25; matched.append(f"ETR {etr:.1%} — generating excess credits for transfer monetization")
            elif etr is not None and etr < 0.10 and net_income and net_income > 100_000_000:
                score += 15; matched.append(f"Low ETR {etr:.1%} — potential excess clean energy credits")

        if not matched:
            matched.append("General applicability — requires company-specific review")

        results.append({
            **issue,
            "score": min(score, 100),
            "matched_signals": matched,
            "assumptions_missing_data": _assumptions_missing_data(iid, matched),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def _assumptions_missing_data(issue_id: str, matched_signals: list[str]) -> str:
    """Label proxy signals and EDGAR data gaps without changing scoring."""
    no_direct_signal = any("General applicability" in signal for signal in matched_signals)
    notes = {
        "obbba_r_e": (
            "Screening uses SEC R&D expense and foreign income as proxies; EDGAR does not identify "
            "domestic vs. foreign Section 174 spend, method-change history, or claimed R&D credits."
        ),
        "obbba_bonus_depreciation": (
            "Screening uses CapEx and D&A as asset-intensity proxies; EDGAR does not show eligible "
            "property classes, placed-in-service dates, or election posture."
        ),
        "obbba_163j": (
            "Screening uses interest expense, debt, and EBITDA-style metrics as proxies; EDGAR does not "
            "provide tax ATI, disallowed-interest carryforwards, or consolidated limitation details."
        ),
        "state_conformity": (
            "Proxy-driven: assets, R&D, and CapEx suggest possible multistate complexity; SEC EDGAR does "
            "not provide state footprint, apportionment, nexus, or state conformity positions."
        ),
        "pillar_two": (
            "Proxy-driven: foreign income, revenue, and ETR approximate possible GloBE relevance; EDGAR "
            "does not provide jurisdictional GloBE revenue, covered taxes, entity data, or safe-harbor status."
        ),
        "irs_enforcement": (
            "Screening uses total assets and UTP balance as public proxies; EDGAR does not show actual "
            "IRS exam history, entity classification, campaign selection, or documentation quality."
        ),
        "transfer_pricing": (
            "Proxy-driven: foreign income and COGS ratio suggest possible import/intercompany activity; "
            "EDGAR does not identify controlled transactions, transfer-pricing policies, customs values, or APAs."
        ),
        "tariff_unicap": (
            "Proxy-driven: COGS and inventory suggest possible import/tariff exposure; EDGAR does not show "
            "HTS codes, customs entries, tariff payments, vendor origin, or UNICAP calculations."
        ),
        "camt": (
            "Proxy-driven: current net income and ETR approximate CAMT relevance; SEC EDGAR does not provide "
            "three-year average AFSI, CAMT adjustments, applicable corporation status, or safe-harbor analysis."
        ),
        "payroll_compliance": (
            "Proxy-driven: revenue and COGS ratio weakly suggest workforce scale; EDGAR does not provide "
            "employee wage categories, tip/overtime populations, payroll systems, or state withholding setup."
        ),
        "rd_credit_documentation": (
            "Screening uses R&D expense as a proxy; EDGAR does not show actual credit claims, project-level "
            "qualified research activities, contemporaneous documentation, or refund claim posture."
        ),
        "transferable_credits": (
            "Proxy-driven: low ETR can suggest credit activity but is not conclusive; EDGAR does not show "
            "IRA credit generation, transfer elections, buyer/seller status, or project eligibility."
        ),
    }
    if no_direct_signal:
        return (
            notes.get(issue_id, "SEC EDGAR did not provide direct issue-specific signals for this item.")
            + " No direct public-filing signal was matched; treat this as a low-confidence prompt for professional review."
        )
    return notes.get(issue_id, "Screening score is heuristic and requires company-specific professional review.")
