from fastapi import FastAPI, HTTPException

from loss_experience.cleaning import load_data
from loss_experience.loss import (
    asset_types,
    compare_portfolios,
    loss_experience,
    portfolio_ids,
    regions,
)
from loss_experience.quality import data_quality


def check_value(name, value, known):
    if value is not None and value not in known:
        raise HTTPException(400, f"Unknown {name} '{value}'. Use one of: {', '.join(known)}")


def create_app(data_dir):
    data = load_data(data_dir)
    app = FastAPI(title="Loss experience")

    @app.get("/portfolios/loss-experience")
    def compare(
        underwriting_year: int | None = None,
        region: str | None = None,
        asset_type: str | None = None,
    ):
        check_value("region", region, regions(data))
        check_value("asset_type", asset_type, asset_types(data))
        return compare_portfolios(data, underwriting_year, region, asset_type)

    @app.get("/portfolios/{portfolio_id}/loss-experience")
    def one_portfolio(
        portfolio_id: str,
        underwriting_year: int | None = None,
        region: str | None = None,
        asset_type: str | None = None,
    ):
        if portfolio_id not in portfolio_ids(data):
            raise HTTPException(404, f"Portfolio {portfolio_id} not found")
        check_value("region", region, regions(data))
        check_value("asset_type", asset_type, asset_types(data))
        return loss_experience(data, portfolio_id, underwriting_year, region, asset_type)

    @app.get("/data-quality")
    def quality():
        return data_quality(data)

    return app
