# Rules for AI helpers

This is a small web service. It shows the loss ratio of insurance portfolios, by peril, in DKK.
Read `docs/LOSS_RULES.md` before you change any number.

## Commands

- Install: `uv sync`
- Test: `uv run pytest`
- Lint: `uv run ruff check .` and `uv run ruff format --check .`
- Run: `uv run uvicorn loss_experience.main:app --port 8000`

The real data is in `data/`. It is not in git. The tests use the small files in `tests/fixtures/`, so they run without it. `tests/test_real_data.py` runs only when `data/` exists.

## Layout

- `src/loss_experience/models.py` has the small data classes.
- `src/loss_experience/cleaning.py` reads the csv files, fixes or drops bad rows, and counts them.
- `src/loss_experience/fx.py` turns money into DKK.
- `src/loss_experience/loss.py` has the loss rules and the sums.
- `src/loss_experience/quality.py` builds the data quality report.
- `src/loss_experience/static/index.html` is the simple page. The api serves it at `/`.
- `src/loss_experience/api.py` has the web routes. `main.py` starts the app.
- `docs/LOSS_RULES.md` says how each number is made and how bad data is handled.

## Rules

- Keep the code simple. Plain functions. Standard library first. No pandas.
- Write the test first. Then write the code.
- Never drop or change a row without counting it. The data quality report must add up: rows = kept + excluded.
- Money is in DKK. Convert each amount with its own currency and the rate of its own month.
- Do not commit `data/`, the zip file, or any real data rows.
- Use short, plain English in comments and docs. A comment says why, not what.
- If you change a rule, change `docs/LOSS_RULES.md` and the tests in the same commit.
