# Loss experience service

A small web service. It shows the loss ratio of insurance portfolios, by peril, in DKK.

## Data

Unzip `envira-loss-data.zip` in this folder. It makes a `data` folder with the csv files.

## Run

    uv sync
    uv run uvicorn loss_experience.main:app --port 8000

Open http://localhost:8000/ for the page, or http://localhost:8000/docs to try the API.
With Docker:

    docker compose up --build

## Test

    uv run pytest

## Endpoints

- `GET /`: a simple page to pick a portfolio. A button shows the curl command for what you see
- `GET /portfolios/{portfolio_id}/loss-experience`: one portfolio, by peril
- `GET /portfolios/loss-experience`: all portfolios, highest loss ratio first
- `GET /data-quality`: what was fixed or excluded in the csv files, and why

The two portfolio endpoints take `underwriting_year`, `region` and `asset_type` as filters.
The rules for each number are in `docs/LOSS_RULES.md`. The choices are in `DECISIONS.md`.
