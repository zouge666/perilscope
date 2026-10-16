import csv
from datetime import datetime
from pathlib import Path

from loss_experience.fx import to_dkk
from loss_experience.loss import PERILS, incurred
from loss_experience.models import Claim, Data, FileReport, Policy

STATUSES = ("settled", "open", "withdrawn", "declined")


def parse_date(text):
    for pattern in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text.strip(), pattern).date()
        except ValueError:
            pass
    return None


def parse_number(text):
    try:
        return float(text)
    except ValueError:
        return None


def read_csv(folder, name):
    path = Path(folder) / name
    if not path.exists():
        raise FileNotFoundError(
            f"Cannot find {path}. Unzip envira-loss-data.zip so that "
            "the csv files are in the data folder."
        )
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def add(counts, name):
    counts[name] = counts.get(name, 0) + 1


def clean_rates(rows, report):
    rates = {}
    for row in rows:
        report.rows += 1
        key = (row["month"], row["currency"])
        rate = parse_number(row["rate_dkk_per_unit"])
        if rate is None or rate <= 0:
            add(report.excluded, "bad_rate")
        elif key in rates:
            add(report.excluded, "duplicate_rate")
        else:
            rates[key] = rate
            report.kept += 1
    return rates


def clean_assets(rows, report):
    assets = {}
    for row in rows:
        report.rows += 1
        if row["asset_id"] in assets:
            add(report.excluded, "duplicate_id")
        else:
            assets[row["asset_id"]] = row
            report.kept += 1
    return assets


def clean_policies(rows, assets, rates, report):
    policies = {}
    seen = set()
    for row in rows:
        report.rows += 1
        peril = row["peril"].strip().lower()
        inception = parse_date(row["inception_date"])
        expiry = parse_date(row["expiry_date"])
        premium = parse_number(row["annual_premium"])
        reason = None
        if row["policy_id"] in seen:
            reason = "duplicate_id"
        elif row["asset_id"] not in assets:
            reason = "asset_not_found"
        elif peril not in PERILS:
            reason = "unknown_peril"
        elif inception is None or expiry is None or expiry <= inception:
            reason = "bad_date"
        elif premium is None or premium <= 0:
            reason = "bad_premium"
        premium_dkk = None
        if reason is None:
            premium_dkk = to_dkk(premium, row["currency"], inception, rates)
            if premium_dkk is None:
                reason = "no_fx_rate"
        seen.add(row["policy_id"])
        if reason:
            add(report.excluded, reason)
            continue
        if peril != row["peril"]:
            add(report.fixed, "peril_spelling")
        asset = assets[row["asset_id"]]
        policies[row["policy_id"]] = Policy(
            policy_id=row["policy_id"],
            portfolio_id=asset["portfolio_id"],
            region=asset["region"],
            asset_type=asset["asset_type"],
            peril=peril,
            underwriting_year=inception.year,
            inception=inception,
            expiry=expiry,
            premium_dkk=premium_dkk,
        )
        report.kept += 1
    return policies


def claim_value(row, loss_date, paid, reserve, rates):
    # The loss in DKK, or None when the row is too broken to work it out.
    if row["status"] not in STATUSES or loss_date is None or paid is None or reserve is None:
        return None
    return to_dkk(incurred(row["status"], paid, reserve), row["currency"], loss_date, rates)


def clean_claims(rows, policies, rates, report, excluded_amounts):
    claims = []
    seen = set()
    for row in rows:
        report.rows += 1
        policy = policies.get(row["policy_id"])
        loss_date = parse_date(row["loss_date"])
        paid = parse_number(row["paid_amount"])
        reserve = parse_number(row["reserve_amount"])
        value = claim_value(row, loss_date, paid, reserve, rates)
        reason = None
        if row["claim_id"] in seen:
            reason = "duplicate_id"
        elif policy is None:
            reason = "policy_not_found"
        elif row["status"] not in STATUSES:
            reason = "unknown_status"
        elif loss_date is None:
            reason = "bad_date"
        elif paid is None or reserve is None:
            reason = "bad_amount"
        elif paid < 0 or reserve < 0:
            reason = "negative_amount"
        elif value is None:
            reason = "no_fx_rate"
        elif loss_date < policy.inception or loss_date > policy.expiry:
            reason = "loss_outside_policy_term"
        seen.add(row["claim_id"])
        if reason:
            add(report.excluded, reason)
            if value is not None:
                excluded_amounts[reason] = excluded_amounts.get(reason, 0.0) + value
            continue
        if row["loss_date"].strip()[2:3] == "-":
            add(report.fixed, "loss_date_format")
        if row["status"] == "settled" and reserve > 0:
            add(report.fixed, "reserve_ignored_on_settled")
        claims.append(Claim(row["claim_id"], policy, row["status"], value))
        report.kept += 1
    return claims


def load_data(data_dir):
    reports = {name: FileReport() for name in ("assets", "policies", "claims", "fx_rates")}
    rates = clean_rates(read_csv(data_dir, "fx_rates.csv"), reports["fx_rates"])
    assets = clean_assets(read_csv(data_dir, "assets.csv"), reports["assets"])
    policies = clean_policies(
        read_csv(data_dir, "policies.csv"), assets, rates, reports["policies"]
    )
    excluded_amounts = {}
    claims = clean_claims(
        read_csv(data_dir, "claims.csv"), policies, rates, reports["claims"], excluded_amounts
    )
    return Data(
        policies=list(policies.values()),
        claims=claims,
        reports=reports,
        excluded_incurred_dkk=excluded_amounts,
    )
