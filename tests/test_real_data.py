import csv
import sqlite3
from pathlib import Path

import pytest

from loss_experience.cleaning import load_data
from loss_experience.loss import compare_portfolios

DATA = Path(__file__).parent.parent / "data"

pytestmark = pytest.mark.skipif(not (DATA / "assets.csv").exists(), reason="no data folder")


@pytest.fixture(scope="module")
def data():
    return load_data(DATA)


def read(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sql_totals():
    # A second way to get the numbers, with SQL. It does not use the code under src.
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE assets(asset_id TEXT PRIMARY KEY, portfolio_id TEXT)")
    db.execute(
        "CREATE TABLE policies(policy_id TEXT PRIMARY KEY, asset_id TEXT, inception_date TEXT,"
        " expiry_date TEXT, annual_premium REAL, currency TEXT)"
    )
    db.execute(
        "CREATE TABLE claims(claim_id TEXT PRIMARY KEY, policy_id TEXT, loss_date TEXT,"
        " paid REAL, reserve REAL, currency TEXT, status TEXT)"
    )
    db.execute(
        "CREATE TABLE fx(month TEXT, currency TEXT, rate REAL, PRIMARY KEY (month, currency))"
    )
    db.executemany(
        "INSERT OR IGNORE INTO assets VALUES (?, ?)",
        [(r["asset_id"], r["portfolio_id"]) for r in read("assets.csv")],
    )
    db.executemany(
        "INSERT OR IGNORE INTO policies VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                r["policy_id"],
                r["asset_id"],
                r["inception_date"],
                r["expiry_date"],
                r["annual_premium"],
                r["currency"],
            )
            for r in read("policies.csv")
        ],
    )
    db.executemany(
        "INSERT OR IGNORE INTO claims VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                r["claim_id"],
                r["policy_id"],
                r["loss_date"],
                r["paid_amount"],
                r["reserve_amount"],
                r["currency"],
                r["status"],
            )
            for r in read("claims.csv")
        ],
    )
    db.executemany(
        "INSERT OR IGNORE INTO fx VALUES (?, ?, ?)",
        [(r["month"], r["currency"], r["rate_dkk_per_unit"]) for r in read("fx_rates.csv")],
    )
    db.execute(
        """CREATE VIEW p AS
        SELECT po.policy_id, a.portfolio_id, po.inception_date, po.expiry_date,
               po.annual_premium * f.rate AS premium_dkk
        FROM policies po
        JOIN assets a ON a.asset_id = po.asset_id
        JOIN fx f ON f.month = substr(po.inception_date, 1, 7) AND f.currency = po.currency"""
    )
    # Some loss dates are written DD-MM-YYYY. This turns them into YYYY-MM-DD.
    db.execute(
        """CREATE VIEW c AS
        SELECT claim_id, policy_id, paid, reserve, currency, status,
               CASE WHEN substr(loss_date, 5, 1) = '-' THEN loss_date
                    ELSE substr(loss_date, 7, 4) || '-' || substr(loss_date, 4, 2) || '-'
                         || substr(loss_date, 1, 2) END AS loss_iso
        FROM claims"""
    )
    premium = dict(db.execute("SELECT portfolio_id, SUM(premium_dkk) FROM p GROUP BY portfolio_id"))
    rows = db.execute(
        """SELECT p.portfolio_id,
                  SUM(CASE c.status WHEN 'settled' THEN c.paid WHEN 'open' THEN c.paid + c.reserve
                      ELSE 0 END * f.rate),
                  SUM(CASE WHEN c.status IN ('settled', 'open') THEN 1 ELSE 0 END)
        FROM c
        JOIN p ON p.policy_id = c.policy_id
        JOIN fx f ON f.month = substr(c.loss_iso, 1, 7) AND f.currency = c.currency
        WHERE c.paid >= 0 AND c.reserve >= 0
          AND c.loss_iso >= p.inception_date AND c.loss_iso <= p.expiry_date
        GROUP BY p.portfolio_id"""
    ).fetchall()
    return {pf: (premium[pf], loss, count) for pf, loss, count in rows}


def test_every_row_is_accounted_for(data):
    for report in data.reports.values():
        assert report.rows == report.kept + sum(report.excluded.values())


def test_the_known_problems_are_found(data):
    assert data.reports["claims"].excluded == {
        "policy_not_found": 260,
        "negative_amount": 262,
        "loss_outside_policy_term": 293,
    }
    assert data.reports["claims"].kept == 3694
    assert data.reports["policies"].fixed["peril_spelling"] == 1321
    assert data.reports["claims"].fixed["reserve_ignored_on_settled"] == 667


def test_totals_match_a_separate_sql_calculation(data):
    expected = sql_totals()
    rows = compare_portfolios(data)["portfolios"]
    assert len(rows) == len(expected) == 12
    for row in rows:
        premium, loss, count = expected[row["portfolio_id"]]
        assert row["earned_premium"] == pytest.approx(premium, abs=0.01)
        assert row["incurred_loss"] == pytest.approx(loss, abs=0.01)
        assert row["claim_count"] == count


def test_the_numbers_are_plausible(data):
    result = compare_portfolios(data)
    assert 0.3 < result["total"]["loss_ratio"] < 1.5
    for row in result["portfolios"]:
        assert 0 < row["loss_ratio"] < 2
