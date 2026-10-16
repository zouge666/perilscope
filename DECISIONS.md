Started: 2026-10-16 19:15 CEST
Stopped: 2026-10-16 20:36 CEST

I started from the same small setup I use for other Python projects: uv, pytest, ruff and hatchling. I did not use another template.

## What I built

A FastAPI service. It reads the four csv files once when it starts and keeps them in memory.
- `GET /portfolios/{id}/loss-experience`: for each peril, the policy count, earned premium, incurred loss, loss ratio, claim count and largest claim, in DKK.
- `GET /portfolios/loss-experience`: all portfolios, highest loss ratio first, so the worst ones are on top.
- `GET /data-quality`: for each file, the rows kept, fixed and excluded, with the reason. It also shows what the excluded claims would have added in DKK.
- Filters for underwriting year, region and asset type. A simple page at `/` to pick a portfolio and a year. A Dockerfile, a compose file and a CI workflow.
- Tests on a small data set that I checked by hand. One more test uses the real data and compares the totals with a separate SQL calculation.

The data has real problems. I fixed 1,321 perils written in other ways ("Fire ", "STORM"). I excluded and counted 260 claims with no policy, 262 with a negative amount and 293 dated before their policy starts. The rules for each number are in `docs/LOSS_RULES.md`.

I used Claude Code (Claude Sonnet 5.5) to write most of the code and tests. I checked the numbers myself: the Python rules and a separate SQL query give the same totals, to the cent. A test run also showed a problem in my first test data (a loss date with no exchange rate), and I fixed the data, not the test.

## What I deliberately did not build, and why

- No database. The data is small and memory is enough. A database is one more thing to keep right.
- No cache, login or paging. The data is small and the brief did not ask for them.
- The page has no automated browser test. I checked it by hand.
- I did not guess that negative amounts are sign errors, and I did not move claims to other policies. I exclude them and show how much they are worth.
- No expenses and no pro-rata premium, as the brief says. So the loss ratio is not a profit number.

## What I would do first with another day

- Ask the underwriters about the excluded claims. The claims with no policy are 11.7 million DKK, about a fifth of the loss I count.
- Look at fire. Its loss ratio is 1.58 and all other perils are below 0.75. I do not know yet if it is the pricing or a few big fires.
- Put the data in SQLite or Postgres and keep the SQL check as a test.
