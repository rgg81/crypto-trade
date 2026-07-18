# Top-40 V3 frozen diagnostic rubric

This rubric is frozen before the first result-bearing lab command. It produces one deterministic
diagnostic score from 0 to 100. Diagnostics are disclosure-only evidence: they never change a hard
gate, readiness decision, public-core floor, robustness score or rank, comeback decision, private
gate, final-OOS eligibility, or final order.

Let `C(x) = min(1, max(0, x))`. All calculations use unrounded finite inputs; displayed values may
be rounded only after the exact score is stored. A component is zero if any input it requires is
missing, nonfinite, malformed, not preregistered, or not produced on its complete frozen schedule.
There is no renormalization of the remaining components.

## 1. Expected role and sign agreement — 15 points

Before testing, a team declares `N >= 1` atomic sign checks covering its signal components and the
long and short sleeves. For check `i`, `a_i=1` only when the organizer-computed after-cost estimate
has the declared strict sign; zero has no sign and gives `a_i=0`.

```text
A = sum(a_i for i=1..N) / N
S_role = 15 * C(A)
```

The declaration cannot be edited after its first bound train run. A missing declared check, an
undeclared post-result check, or `N=0` makes `S_role=0`.

## 2. Chronological fold and walk-forward consistency — 20 points

Use the `K >= 4` preregistered, nonoverlapping chronological test folds. Let `s_k` be each fold's
after-cost net Sharpe, `P = count(s_k > 0)/K`, and `M = median(s_1,...,s_K)`.

```text
S_folds = 20 * (0.60 * P + 0.40 * C((M + 0.25) / 0.75))
```

Folds remain in timestamp order and may not be pooled, dropped, relabelled, or replaced. Missing
or overlapping folds, fewer than four folds, or a fold without a finite result makes this whole
component zero.

## 3. Target/forward-return IC level, sign, and decay — 15 points

For each preregistered forward horizon `h_1 < ... < h_H`, with `H >= 2`, compute the timestamp-level
cross-sectional Spearman correlation between the frozen target and the later market-residual
return. Let `mu_j` be the mean finite IC at horizon `h_j`, using every scheduled timestamp. Define:

```text
L = C(mu_1 / 0.03)
G = count(all scheduled IC observations > 0) / count(all scheduled IC observations)
D = count(mu_j >= mu_(j+1) >= 0 for j=1..H-1) / (H-1)
S_ic = 15 * (0.50 * L + 0.30 * G + 0.20 * D)
```

Thus the declared target must have the positive predictive sign, and its mean IC should decay
rather than reverse as the forward horizon grows. A missing scheduled observation, horizon, target
hash, or forward-return definition makes `S_ic=0`.

## 4. Trial-adjusted block-bootstrap confidence — 20 points

Use the complete after-cost daily return series, exactly 2,000 stationary circular block-bootstrap
replicates, 10-day blocks, and seed `20260718`. Let `B` be the fraction of replicate arithmetic
means strictly above zero, and let `T >= 1` be the team's cumulative material-trial count from the
append-only journal at nomination time. Apply the preregistered Bonferroni adjustment:

```text
Q = C(1 - T * (1 - B))
S_confidence = 20 * C((Q - 0.50) / 0.45)
```

An incomplete journal, missing failures, a noncanonical trial count, changed seed/block rule, or
fewer than 2,000 completed replicates makes this component zero.

## 5. Preregistered local-neighborhood stability — 15 points

Evaluate every point in the finite local parameter neighborhood frozen before its center result.
The neighborhood must contain `J >= 5` distinct points and vary every material continuous parameter
both upward and downward where its domain permits. For point `j`, let `b_j=1` only when both its
after-cost annualized return and doubled-cost Sharpe are strictly positive. Let `P_n=sum(b_j)/J`
and let `M_n` be the median doubled-cost Sharpe across all `J` points.

```text
S_neighborhood = 15 * (0.70 * P_n + 0.30 * C(M_n / 0.75))
```

Missing points, duplicated points, a post-result neighborhood, or an unevaluated required direction
makes `S_neighborhood=0`.

## 6. Position, sleeve, sector, and return concentration — 15 points

Compute absolute, nonnegative contribution shares over the complete scored record. Let `W_symbol`
be the largest symbol share of absolute PnL, `W_days5` the share of absolute daily PnL contributed
by the five largest days, and `W_sector` the largest frozen native-crypto sector share of average
absolute exposure. Let `A_long` and `A_short` be the long and short sleeves' absolute PnL totals and
`R_sleeve=min(A_long,A_short)/max(A_long,A_short)`.

```text
P_symbol = C((0.20 - W_symbol) / 0.15)
P_days   = C((0.35 - W_days5) / 0.25)
P_sleeve = C(R_sleeve / 0.50)
P_sector = C((0.50 - W_sector) / 0.30)

S_concentration = 15 * (
    0.30 * P_symbol
  + 0.30 * P_days
  + 0.20 * P_sleeve
  + 0.20 * P_sector
)
```

If total absolute PnL is zero, either sleeve total is zero, sector attribution is missing, or any
share is outside `[0,1]`, this component is zero.

## Frozen total

```text
Diagnostic = S_role + S_folds + S_ic + S_confidence + S_neighborhood + S_concentration
```

The exact total lies in `[0,100]`. Every component, raw input hash, missing-input reason, and exact
unrounded calculation is disclosed with the public packet. No diagnostic threshold exists.
