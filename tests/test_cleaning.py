from pathlib import Path

import pytest

from loss_experience.cleaning import load_data

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def data():
    return load_data(FIXTURES)


def test_peril_spelling_is_fixed(data):
    perils = {p.policy_id: p.peril for p in data.policies}
    assert perils["POL-2"] == "storm"
    assert perils["POL-3"] == "fire"


def test_underwriting_year_is_the_start_year(data):
    years = {p.policy_id: p.underwriting_year for p in data.policies}
    assert years["POL-1"] == 2023
    assert years["POL-3"] == 2024


def test_money_is_in_dkk(data):
    premium = {p.policy_id: p.premium_dkk for p in data.policies}
    assert premium["POL-1"] == 1000.0
    assert premium["POL-3"] == 750.0  # 100 EUR at 7.5


def test_duplicate_policy_keeps_the_first_row(data):
    premium = {p.policy_id: p.premium_dkk for p in data.policies}
    assert premium["POL-5"] == 500.0
    assert data.reports["policies"].excluded["duplicate_id"] == 1


def test_loss_date_written_day_first_is_read(data):
    ids = [c.claim_id for c in data.claims]
    assert "CLM-2" in ids


def test_claim_without_policy_is_excluded(data):
    ids = [c.claim_id for c in data.claims]
    assert "CLM-8" not in ids
    assert data.reports["claims"].excluded["policy_not_found"] == 1


def test_negative_amount_is_excluded(data):
    ids = [c.claim_id for c in data.claims]
    assert "CLM-9" not in ids
    assert data.reports["claims"].excluded["negative_amount"] == 1


def test_claim_before_the_policy_starts_is_excluded(data):
    ids = [c.claim_id for c in data.claims]
    assert "CLM-10" not in ids
    assert data.reports["claims"].excluded["loss_outside_policy_term"] == 1


def test_incurred_loss_follows_the_status(data):
    incurred = {c.claim_id: c.incurred_dkk for c in data.claims}
    assert incurred["CLM-1"] == 400.0  # settled
    assert incurred["CLM-2"] == 50.0  # settled, the reserve of 70 is ignored
    assert incurred["CLM-3"] == 500.0  # open: 300 paid + 200 reserve
    assert incurred["CLM-4"] == 75.0  # 10 EUR at 7.5
    assert incurred["CLM-5"] == 160.0  # 20 EUR at 8.0, the rate of 2023-07
    assert incurred["CLM-6"] == 0.0  # declined
    assert incurred["CLM-7"] == 0.0  # withdrawn


def test_excluded_claims_are_valued(data):
    assert data.excluded_incurred_dkk == {
        "policy_not_found": 999.0,
        "negative_amount": -30.0,
        "loss_outside_policy_term": 60.0,
    }


def test_every_row_is_counted(data):
    expected = {
        "assets": (3, 3),
        "policies": (6, 5),
        "claims": (10, 7),
        "fx_rates": (48, 48),
    }
    for name, (rows, kept) in expected.items():
        report = data.reports[name]
        assert report.rows == rows
        assert report.kept == kept
        assert report.rows == report.kept + sum(report.excluded.values())


def test_fixed_rows_are_counted(data):
    assert data.reports["policies"].fixed == {"peril_spelling": 2}
    assert data.reports["claims"].fixed == {
        "loss_date_format": 1,
        "reserve_ignored_on_settled": 1,
    }


def test_missing_data_folder_gives_a_clear_error():
    with pytest.raises(FileNotFoundError):
        load_data("no/such/folder")
