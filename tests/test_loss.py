from pathlib import Path

import pytest

from loss_experience.cleaning import load_data
from loss_experience.loss import (
    asset_types,
    compare_portfolios,
    loss_experience,
    portfolio_ids,
    regions,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def data():
    return load_data(FIXTURES)


def peril(result, name):
    return next(p for p in result["perils"] if p["peril"] == name)


def test_portfolio_ids(data):
    assert portfolio_ids(data) == ["PF-A", "PF-B"]


def test_fire_in_portfolio_a(data):
    fire = peril(loss_experience(data, "PF-A"), "fire")
    assert fire == {
        "peril": "fire",
        "policy_count": 2,
        "earned_premium": 1750.0,  # 1000 + 100 EUR at 7.5
        "incurred_loss": 525.0,  # 400 + 50 + 75
        "loss_ratio": 0.3,
        "claim_count": 3,
        "largest_claim": 400.0,
    }


def test_storm_in_portfolio_a(data):
    storm = peril(loss_experience(data, "PF-A"), "storm")
    assert storm["policy_count"] == 1
    assert storm["earned_premium"] == 2000.0
    assert storm["incurred_loss"] == 500.0
    assert storm["loss_ratio"] == 0.25
    assert storm["claim_count"] == 1
    assert storm["largest_claim"] == 500.0


def test_peril_without_policies_has_no_loss_ratio(data):
    hail = peril(loss_experience(data, "PF-A"), "hail")
    assert hail == {
        "peril": "hail",
        "policy_count": 0,
        "earned_premium": 0.0,
        "incurred_loss": 0.0,
        "loss_ratio": None,
        "claim_count": 0,
        "largest_claim": 0.0,
    }


def test_all_five_perils_come_in_the_same_order(data):
    result = loss_experience(data, "PF-B")
    names = [p["peril"] for p in result["perils"]]
    assert names == ["fire", "flood", "hail", "storm", "subsidence"]


def test_total_of_portfolio_a(data):
    total = loss_experience(data, "PF-A")["total"]
    assert total["policy_count"] == 3
    assert total["earned_premium"] == 3750.0
    assert total["incurred_loss"] == 1025.0
    assert total["loss_ratio"] == 0.2733
    assert total["claim_count"] == 4
    assert total["largest_claim"] == 500.0


def test_declined_and_withdrawn_claims_are_not_counted(data):
    result = loss_experience(data, "PF-B")
    assert peril(result, "fire")["claim_count"] == 0  # one withdrawn claim
    assert peril(result, "flood")["claim_count"] == 1  # one declined, one settled
    assert peril(result, "flood")["incurred_loss"] == 160.0


def test_currency_is_dkk(data):
    assert loss_experience(data, "PF-A")["currency"] == "DKK"
    assert compare_portfolios(data)["currency"] == "DKK"


def test_portfolios_are_ordered_by_loss_ratio_highest_first(data):
    rows = compare_portfolios(data)["portfolios"]
    assert [r["portfolio_id"] for r in rows] == ["PF-A", "PF-B"]
    assert [r["rank"] for r in rows] == [1, 2]
    assert rows[0]["loss_ratio"] == 0.2733
    assert rows[1]["loss_ratio"] == 0.0457


def test_portfolios_add_up_to_the_book(data):
    result = compare_portfolios(data)
    assert result["total"]["earned_premium"] == 7250.0
    assert result["total"]["incurred_loss"] == 1185.0
    assert result["total"]["policy_count"] == 5
    assert result["total"]["loss_ratio"] == 0.1634
    assert sum(r["earned_premium"] for r in result["portfolios"]) == 7250.0
    assert sum(r["incurred_loss"] for r in result["portfolios"]) == 1185.0


def test_filter_by_underwriting_year(data):
    total = loss_experience(data, "PF-A", underwriting_year=2023)["total"]
    assert total["earned_premium"] == 3000.0
    assert total["incurred_loss"] == 950.0
    assert total["loss_ratio"] == 0.3167


def test_filter_by_region(data):
    total = loss_experience(data, "PF-A", region="Nordjylland")["total"]
    assert total["earned_premium"] == 750.0
    assert total["incurred_loss"] == 75.0


def test_filter_by_asset_type(data):
    total = loss_experience(data, "PF-A", asset_type="residential")["total"]
    assert total["earned_premium"] == 3000.0
    assert total["incurred_loss"] == 950.0


def test_filters_work_when_comparing_portfolios(data):
    result = compare_portfolios(data, region="Hovedstaden")
    assert result["total"]["earned_premium"] == 6500.0
    assert result["total"]["incurred_loss"] == 1110.0
    assert result["total"]["loss_ratio"] == 0.1708


def test_filters_are_part_of_the_answer(data):
    result = loss_experience(data, "PF-A", underwriting_year=2024, region="Nordjylland")
    assert result["filters"] == {
        "underwriting_year": 2024,
        "region": "Nordjylland",
        "asset_type": None,
    }
    assert result["total"]["earned_premium"] == 750.0


def test_known_values_for_the_filters(data):
    assert regions(data) == ["Hovedstaden", "Nordjylland"]
    assert asset_types(data) == ["commercial", "residential"]
