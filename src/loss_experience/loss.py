PERILS = ["fire", "flood", "hail", "storm", "subsidence"]
COUNTED_STATUSES = ("settled", "open")


def incurred(status, paid, reserve):
    # A settled claim can still show a reserve. We ignore it.
    if status == "settled":
        return paid
    if status == "open":
        return paid + reserve
    return 0.0


def portfolio_ids(data):
    return sorted({p.portfolio_id for p in data.policies})


def regions(data):
    return sorted({p.region for p in data.policies})


def asset_types(data):
    return sorted({p.asset_type for p in data.policies})


def summarize(policies, claims):
    premium = sum(p.premium_dkk for p in policies)
    loss = sum(c.incurred_dkk for c in claims)
    counted = [c for c in claims if c.status in COUNTED_STATUSES]
    ratio = None
    if premium > 0:
        ratio = round(loss / premium, 4)
    largest = max((c.incurred_dkk for c in counted), default=0.0)
    return {
        "policy_count": len(policies),
        "earned_premium": round(premium, 2),
        "incurred_loss": round(loss, 2),
        "loss_ratio": ratio,
        "claim_count": len(counted),
        "largest_claim": round(largest, 2),
    }


def keep(policy, underwriting_year, region, asset_type):
    return (
        (underwriting_year is None or policy.underwriting_year == underwriting_year)
        and (region is None or policy.region == region)
        and (asset_type is None or policy.asset_type == asset_type)
    )


def select(data, portfolio_id=None, underwriting_year=None, region=None, asset_type=None):
    policies = [
        p
        for p in data.policies
        if (portfolio_id is None or p.portfolio_id == portfolio_id)
        and keep(p, underwriting_year, region, asset_type)
    ]
    ids = {p.policy_id for p in policies}
    claims = [c for c in data.claims if c.policy.policy_id in ids]
    return policies, claims


def loss_experience(data, portfolio_id, underwriting_year=None, region=None, asset_type=None):
    policies, claims = select(data, portfolio_id, underwriting_year, region, asset_type)
    perils = []
    for name in PERILS:
        peril_policies = [p for p in policies if p.peril == name]
        peril_claims = [c for c in claims if c.policy.peril == name]
        perils.append({"peril": name, **summarize(peril_policies, peril_claims)})
    return {
        "portfolio_id": portfolio_id,
        "currency": "DKK",
        "filters": {
            "underwriting_year": underwriting_year,
            "region": region,
            "asset_type": asset_type,
        },
        "perils": perils,
        "total": summarize(policies, claims),
    }


def compare_portfolios(data, underwriting_year=None, region=None, asset_type=None):
    rows = []
    for portfolio_id in portfolio_ids(data):
        policies, claims = select(data, portfolio_id, underwriting_year, region, asset_type)
        rows.append({"portfolio_id": portfolio_id, **summarize(policies, claims)})
    # The worst portfolio comes first. A portfolio without premium has no ratio, so it goes last.
    rows.sort(key=lambda r: (r["loss_ratio"] is None, -(r["loss_ratio"] or 0), r["portfolio_id"]))
    for number, row in enumerate(rows, start=1):
        row["rank"] = number
    policies, claims = select(data, None, underwriting_year, region, asset_type)
    return {
        "currency": "DKK",
        "filters": {
            "underwriting_year": underwriting_year,
            "region": region,
            "asset_type": asset_type,
        },
        "ordered_by": "loss_ratio, highest first",
        "portfolios": rows,
        "total": summarize(policies, claims),
    }
