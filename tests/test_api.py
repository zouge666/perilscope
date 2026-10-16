from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from loss_experience.api import create_app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(FIXTURES))


def test_loss_experience_of_one_portfolio(client):
    response = client.get("/portfolios/PF-A/loss-experience")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio_id"] == "PF-A"
    assert body["currency"] == "DKK"
    assert len(body["perils"]) == 5
    assert body["perils"][0] == {
        "peril": "fire",
        "policy_count": 2,
        "earned_premium": 1750.0,
        "incurred_loss": 525.0,
        "loss_ratio": 0.3,
        "claim_count": 3,
        "largest_claim": 400.0,
    }


def test_unknown_portfolio_gives_404(client):
    response = client.get("/portfolios/PF-X/loss-experience")
    assert response.status_code == 404
    assert "PF-X" in response.json()["detail"]


def test_compare_portfolios(client):
    body = client.get("/portfolios/loss-experience").json()
    assert [p["portfolio_id"] for p in body["portfolios"]] == ["PF-A", "PF-B"]
    assert body["total"]["earned_premium"] == 7250.0


def test_data_quality_report(client):
    body = client.get("/data-quality").json()
    claims = body["files"]["claims"]
    assert claims["rows"] == 10
    assert claims["kept"] == 7
    assert claims["excluded"] == {
        "policy_not_found": 1,
        "negative_amount": 1,
        "loss_outside_policy_term": 1,
    }
    assert body["files"]["policies"]["fixed"] == {"peril_spelling": 2}
    assert body["excluded_incurred_dkk"]["policy_not_found"] == 999.0


def test_filter_by_underwriting_year(client):
    url = "/portfolios/PF-A/loss-experience"
    body = client.get(url, params={"underwriting_year": 2023}).json()
    assert body["total"]["earned_premium"] == 3000.0
    assert body["total"]["incurred_loss"] == 950.0
    assert body["total"]["loss_ratio"] == 0.3167
    assert body["filters"] == {"underwriting_year": 2023, "region": None, "asset_type": None}


def test_filter_by_region(client):
    url = "/portfolios/PF-A/loss-experience"
    body = client.get(url, params={"region": "Nordjylland"}).json()
    assert body["total"]["earned_premium"] == 750.0
    assert body["total"]["incurred_loss"] == 75.0


def test_filter_by_asset_type(client):
    url = "/portfolios/PF-A/loss-experience"
    body = client.get(url, params={"asset_type": "residential"}).json()
    assert body["total"]["earned_premium"] == 3000.0
    assert body["total"]["incurred_loss"] == 950.0


def test_filters_work_when_comparing_portfolios(client):
    body = client.get("/portfolios/loss-experience", params={"region": "Hovedstaden"}).json()
    assert body["total"]["earned_premium"] == 6500.0
    assert body["total"]["incurred_loss"] == 1110.0
    assert body["total"]["loss_ratio"] == 0.1708


def test_unknown_region_gives_400(client):
    response = client.get("/portfolios/PF-A/loss-experience", params={"region": "Mars"})
    assert response.status_code == 400
    assert "Mars" in response.json()["detail"]
