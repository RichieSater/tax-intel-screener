"""Tests for tax issue scoring logic."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tax_issues import score_profile


def test_high_rd_scores_r_e_issue():
    profile = {"rd_expense": 2_000_000_000, "foreign_income": None}
    scored = score_profile(profile)
    r_e = next(i for i in scored if i["id"] == "obbba_r_e")
    assert r_e["score"] >= 60


def test_large_assets_scores_irs_enforcement():
    # Asset tier is the base qualifier; UTP is the key discriminating signal.
    # Large assets alone give the base score (~45); UTP adds the audit-intensity signal.
    profile = {"total_assets": 15_000_000_000}
    scored = score_profile(profile)
    irs = next(i for i in scored if i["id"] == "irs_enforcement")
    assert irs["score"] >= 40


def test_large_assets_with_utp_scores_irs_high():
    # A company with large assets AND a substantial UTP balance (real controversy exposure)
    # should score well above the asset-only base.
    profile = {"total_assets": 15_000_000_000, "uncertain_tax_positions": 2_000_000_000}
    scored = score_profile(profile)
    irs = next(i for i in scored if i["id"] == "irs_enforcement")
    assert irs["score"] >= 70


def test_high_book_income_scores_camt():
    profile = {"net_income": 2_000_000_000, "effective_tax_rate": 0.08}
    scored = score_profile(profile)
    camt = next(i for i in scored if i["id"] == "camt")
    assert camt["score"] >= 60


def test_foreign_income_scores_pillar_two():
    profile = {"foreign_income": 1_500_000_000, "effective_tax_rate": 0.11}
    scored = score_profile(profile)
    p2 = next(i for i in scored if i["id"] == "pillar_two")
    assert p2["score"] >= 60


def test_scores_sorted_descending():
    profile = {
        "rd_expense": 3_000_000_000,
        "total_assets": 50_000_000_000,
        "net_income": 5_000_000_000,
    }
    scored = score_profile(profile)
    scores = [i["score"] for i in scored]
    assert scores == sorted(scores, reverse=True)
