# portfolio-iteration-v2 EXPLORATION-003 — cross-sectional LightGBM predictor (NEGATIVE)

**Type:** EXPLORATION (OOS HIDDEN). ONE change: replace the hand-crafted trend+carry+xs blend with a
**fast cross-sectional LightGBM** predicting each coin's BTC-undemeaned… no — cross-sectionally-demeaned
forward return within the band, leak-safe monthly walk-forward, dollar-neutral via centered rank.
**Verdict:** **NEGATIVE — clean.** Methodology sound (G5 PASS); the model fails G1–G4 decisively and is
notably WORSE than its own ingredients. Brief: `BRIEF_iter003_xsml.md`.

## What was built (infra is reusable + validated)
- `engine_v2.run_book_from_signal(coins, signal_panel, ...)` — NEW signal-driven path (no walk-forward
  λ); reuses the SAME band/eligexit/vol-target/slippage pipeline. Validated: `run_book` untouched,
  parity_check UNCHANGED 1.041e-16; unit tests `test_run_book_from_signal_handcomputed_net` (bit-for-bit
  <1e-12), `_degenerate_constant`, plus ML leak guards `test_ml_walkforward_train_window_bound` (embargo)
  and `test_ml_walkforward_future_perturbation_invariance` (pre-cutoff ML signal max|Δ|==0). 15/15 green.
- `ml_v2.py` (features + demeaned-forward label + leak-safe walk-forward LightGBM ~200 trees) +
  `iter_v2_003_xsml.py`. No `src/` or v1 changes.

## Results (IS + EARLY[21–23]/LATE[24→cutoff], OOS hidden; default slip)
| signal | IS | EARLY | LATE | turn | aPos |
|---|---|---|---|---|---|
| anchor (trend+carry λ) | +1.53 | +2.17 | +1.16 | 0.297 | 18.8 |
| **ML xs-predictor** | **+0.02** | **−0.13** | **+0.12** | 0.614 | 17.6 |
| TREND-only (via hook) | +1.46 | +2.10 | +0.77 | 0.281 | 14.2 |
| XS-mom-only (via hook) | +0.43 | +0.19 | +1.36 | 0.185 | 17.6 |
ML per-year `{2021:0.85, 2022:0.80, 2023:−1.90, 2024:−0.56, 2025:0.48, 2026:−0.65}`. Feature importance
well-distributed (top-1 `ret_7` 10.9%; `regime_trend_sharpe` 7.5%; rvol/carry/ret_42…). Cold-start 4.2%
of months. Cost: 2×-taker ML LATE −1.56 (ΔLATE −2.25); pessimistic LATE −0.27. Turnover 0.614 (~2.1×).

## Gate read (IS + LATE only; OOS not consulted)
- **G1 (IS ≥ +1.43): FAIL** (+0.02 — dilutes the IS-strong trend years to flat; 2023 collapse −1.90).
- **G2 (ΔLATE ≥ +0.20) [load-bearing]: FAIL** — ML LATE +0.12 vs anchor +1.16, ΔLATE **−1.04** (destroys
  the LATE era).
- **G3 (cost): FAIL** — cost-fatal at 2× taker (turnover 0.614 — the rank-churn risk iter-002 flagged).
- **G4 (beats its own ingredients on LATE): FAIL** — ML LATE +0.12 < TREND-only +0.77 AND < XS-mom-only
  +1.36. The pooled regression is WORSE than either hand-set ingredient → it adds nothing.
- **G5 (methodology): PASS** — dollar-neutral (signal max|Σ|=4.4e-16), leak test green, parity unchanged,
  embargo-gap enforced (window-bound test), cold-start reported.

## Why it failed (lesson)
A pooled **L2/MSE** LightGBM on a 20-name, regime-shifting, noisy cross-section overfits to noise and
churns (turnover 2.1×). The MSE objective optimizes return-prediction error, not the Sharpe/rank we
actually deploy; and combining trend (EARLY-alive) + XS-mom (LATE-alive) into one regression LOST to
each ingredient alone. **Simple, interpretable factors beat the kitchen-sink ML here.** The constructive
takeaway: the ingredients DO carry the era-split (TREND-only EARLY +2.10, XS-mom-only LATE +1.36) — the
problem is the L2 combination, not the signals. This points to (a) residual/beta-neutralized momentum
(iter-v2-004, literature lead) and (b) explicit regime-routing rather than a learned MSE blend.

DEAD PATH LOGGED: pooled L2 cross-sectional LightGBM on rank-21–40 (this feature set, this objective).
NOT closed for all of ML — a rank/Sharpe objective, or ML *on top of* residual momentum, remains open.
