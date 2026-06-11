"""Tests for the SEC EDGAR companyconcept client."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import json

import pytest

from edgar import get_financial_profile, edgar_cik, _CONCEPTS


def _cik_from_companies_json(ticker: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "companies.json")
    with open(path) as f:
        companies = json.load(f)
    for c in companies:
        if c.get("ticker", "").upper() == ticker:
            return str(c["cik"]).zfill(10)
    raise AssertionError(f"{ticker} missing from companies.json")


def test_unknown_ticker_raises():
    with pytest.raises(ValueError):
        get_financial_profile("ZZZZNOTREAL999")


def test_msft_returns_core_fields():
    profile = get_financial_profile("MSFT", cik=_cik_from_companies_json("MSFT"))
    assert profile["ticker"] == "MSFT"
    assert profile["company_name"]
    # Core income statement fields must be present and positive
    assert profile["revenue"] and profile["revenue"] > 1e9
    assert profile["net_income"] and profile["net_income"] > 0
    assert profile["total_assets"] and profile["total_assets"] > 1e9
    # Source metadata present for every scored field
    assert set(profile["source_metadata"]) == set(_CONCEPTS)
    assert profile["source_metadata"]["revenue"]["concept"]
    assert profile["source_metadata"]["revenue"]["source"] == "SEC EDGAR companyconcept"


def test_capex_is_positive():
    profile = get_financial_profile("CAT", cik=_cik_from_companies_json("CAT"))
    if profile.get("capex") is not None:
        assert profile["capex"] >= 0, "CapEx must be stored as a positive value"


def test_data_source_label():
    profile = get_financial_profile("AAPL", cik=_cik_from_companies_json("AAPL"))
    assert "edgar" in profile["data_source"].lower()


def test_edgar_cik_lookup():
    assert edgar_cik("AAPL") == "0000320193"
