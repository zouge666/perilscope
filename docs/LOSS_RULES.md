# Loss rules

All money is in DKK.

## Numbers

- Incurred loss of a claim:
  - settled: the paid amount.
  - open: the paid amount plus the reserve.
  - withdrawn or declined: 0.
  - A settled claim can still show a reserve. We ignore it.
- Earned premium: the full annual premium of the policy. No pro-rata.
- Loss ratio: incurred loss divided by earned premium. It is `null` when the premium is 0.
- Underwriting year: the year the policy starts. A claim gets the year of its policy.
- Policy count: the number of valid policies.
- Claim count: the number of settled and open claims. Withdrawn and declined claims are not counted.
- Largest claim: the biggest incurred loss of one claim. It is 0 when there are no claims.
- A claim belongs to the policy named in its `policy_id`. The policy gives the asset, and the asset gives the portfolio, region and asset type.

## Currency

- Each amount is converted with its own currency. A claim can be in a different currency than its policy.
- A premium uses the rate of the month the policy starts.
- A claim uses the rate of the month of its loss date.
- The rate table has EUR and DKK for every month from 2020-01 to 2026-12.
- EUR moves very little in this table (7.43 to 7.46). We tried one flat rate of 7.45. The loss ratio of the whole book is the same to four decimals.

## Bad data

Each row is kept, fixed or excluded. Every case is counted in `/data-quality`. The rows of a file always add up: rows = kept + excluded.

If a row fails more than one check, it is counted under the first one in the lists below.

Assets are excluded when:
- `duplicate_id`: the id was seen before. We keep the first row.

Policies are excluded when:
- `duplicate_id`: the id was seen before. We keep the first row.
- `asset_not_found`: the asset does not exist.
- `unknown_peril`: the peril is not fire, flood, hail, storm or subsidence (after the fix below).
- `bad_date`: a date cannot be read, or the end is not after the start.
- `bad_premium`: the premium is not a number above 0.
- `no_fx_rate`: there is no rate for the currency and month.

Claims are excluded when:
- `duplicate_id`: the id was seen before. We keep the first row.
- `policy_not_found`: the policy does not exist.
- `unknown_status`: the status is not settled, open, withdrawn or declined.
- `bad_date`: the loss date cannot be read.
- `bad_amount`: the paid or reserve amount is not a number.
- `negative_amount`: the paid or reserve amount is below 0.
- `no_fx_rate`: there is no rate for the currency and month.
- `loss_outside_policy_term`: the loss date is before the policy starts or after it ends.

Rate rows are excluded when:
- `bad_rate`: the rate is not a number above 0.
- `duplicate_rate`: the month and currency were seen before. We keep the first row.

Rows we fix and keep:
- `peril_spelling`: spaces and capital letters are removed from the peril, so " Fire" becomes "fire".
- `loss_date_format`: a loss date written as DD-MM-YYYY is read day first.
- `reserve_ignored_on_settled`: a settled claim with a reserve. The reserve is not used.

We do not look at the columns we do not use (`reported_date`, `construction_year`, `sum_insured_dkk`). No row is dropped because of them.

## Assumptions

- A claim dated before its policy starts cannot be covered by that policy. We exclude it. We do not move it to another policy, because policies of the same asset and peril often overlap.
- A claim with a negative amount is not a real payment. We exclude it. We do not flip the sign, because we cannot know that it is a sign error.
- A claim with no policy cannot be put in a portfolio. We exclude it.
- Excluded claims are still visible. `/data-quality` shows what each group of excluded claims would have added, in DKK.
- The portfolios are about the same size, so their loss ratios can be compared directly. The comparison puts the highest loss ratio first.
