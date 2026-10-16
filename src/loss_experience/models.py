from dataclasses import dataclass, field
from datetime import date


@dataclass
class Policy:
    policy_id: str
    portfolio_id: str
    region: str
    asset_type: str
    peril: str
    underwriting_year: int
    inception: date
    expiry: date
    premium_dkk: float


@dataclass
class Claim:
    claim_id: str
    policy: Policy
    status: str
    incurred_dkk: float


@dataclass
class FileReport:
    rows: int = 0
    kept: int = 0
    excluded: dict = field(default_factory=dict)
    fixed: dict = field(default_factory=dict)


@dataclass
class Data:
    policies: list
    claims: list
    reports: dict
    excluded_incurred_dkk: dict
