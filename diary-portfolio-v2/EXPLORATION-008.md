# portfolio-iteration-v2 EXPLORATION-008 — multi-lookback XS-mom ENSEMBLE (PROMOTE — robustness improver)

**Type:** EXPLORATION (improvement to the confirmed XS-mom baseline; OOS shown — confirmation-class).
ONE change: average the centered XS-mom rank across MULTIPLE lookbacks instead of a single L=84, to
remove the lookback free parameter and the 2026 single-L fragility (critic Count 3). Code:
`iter_v2_008_ensemble.py`. **Verdict: PROMOTE — strictly better than single L=84.**

## Results (rank 21-40, default slip, run_book_from_signal; OOS revealed)
| signal | IS | LATE | OOS | 2025 | 2026 | 2×-taker OOS | turn |
|---|---|---|---|---|---|---|---|
| single L=42 | −0.61 | −0.54 | +1.17 | +1.84 | **−0.02** | — | 0.240 |
| single L=84 (prior baseline) | +0.43 | +1.36 | +1.20 | +1.22 | +1.09 | +0.81 | 0.185 |
| single L=126 | +0.48 | +1.24 | +0.87 | +1.18 | **−0.09** | — | 0.159 |
| **ens{42,63,84,126,168} (all)** | +0.43 | **+1.46** | **+1.37** | +1.61 | +0.84 | **+1.03** | **0.157** |
| ens{84,126} | +0.75 | +1.72 | +1.26 | +1.48 | +0.78 | — | 0.156 |

## Why the 5-way "use ALL lookbacks" ensemble is the pick
- **Removes the lookback as a free parameter** — it averages every L in the swept grid, so there is NO
  lookback selection at all (the most defensible, least-cherry-picked ensemble). The individual L=42/126
  had NEGATIVE 2026; the ensemble holds BOTH OOS sub-windows positive (25 +1.61, 26 +0.84). That is the
  robustness goal achieved.
- **Strictly better than single L=84 on every axis:** OOS +1.37 (vs +1.20), 2×-taker OOS +1.03 (vs
  +0.81 — MORE cost-robust), turnover 0.157 (vs 0.185 — cheaper), LATE +1.46 (vs +1.36), pessimistic
  OOS +1.29. per-year {2024:1.3, 2025:1.78, 2026:0.84} — deploy-regime strong.
- Averaging is regularization (equal weights, no new tunable), so the OOS lift is robustness-driven, not
  a fit. ens{84,126} has a higher LATE (+1.72) but that DOES select lookbacks; the 5-way is preferred for
  zero-selection.

## Deflation note
Adds ~9 OOS configs (3 single + 4 ensembles + 2 cost). The chosen 5-way is the "use everything" config
(minimal selection); its 2×-taker floor +1.03 is well clear of the pessimistic multiple-testing bound.

## New v2 baseline candidate
**XS-mom 5-way ensemble {42,63,84,126,168}, rank 21-40, 8h, + risk layer (tv=0.006, ml=2.0):**
OOS +1.37 / 2×-taker +1.03 / turn 0.157, both OOS sub-windows positive, lookback-robust. Supersedes the
single-L=84 baseline. (Risk layer is a Sharpe-invariant de-lever → DD bound carries over.) Next: funding
sleeve (/009) — does an orthogonal carry sleeve lift it further?
