# BASELINE_PORTFOLIO_V2 — rank-21–40 dollar-neutral cross-sectional momentum

**Established:** 2026-06-23 (iter-v2-001 → 009). **Branch:** `quant-portfolio`. **Status:** baseline
candidate, MERGE-WITH-RISK-LAYER confirmed by quant-critic; record items R1/R3 closed below.

> **⚠️ CORRECTION (2026-06-23, live deploy) — numbers below are the pre-correction figures.** The live
> testnet deploy revealed the universe was contaminated with NON-COIN perps (tokenized stocks INTC/CRCL/…,
> BTCDOM/DEFI indices). Fixed via `universe_v2.NON_COIN_PERPS` (exclude `underlyingType != COIN`).
> **Authoritative CRYPTO-ONLY figures (re-run):**
> - v2 ensemble baseline **OOS +1.16** (2025 +1.58, 2026 +0.62), 2× taker **+0.90**, pessimistic +1.10.
> - risk layer (tv=0.006/ml=2.0): **OOS DD ~−24% → ~−15% at zero Sharpe cost** (signal-agnostic de-lever).
> - statistics: **PSR(SR>0) = 0.90**, **DSR (XS-family N=9) = 0.765** (all-classes over-conservative 0.34) —
>   real, corroborated, MODERATE deflated significance (was 0.94/0.83 contaminated).
> - **combined v1+v2 (50/50) OOS +1.89** (corr +0.22, DD −18%) — diversification lift survives.
> The stock-perps were padding ~+0.21 OOS (mostly 2026, when they listed). See `LIVE_DEPLOY.md`.

## The strategy (fixed-parameter — NO monthly tuning, NO OOS tuning)
**Dollar-neutral cross-sectional momentum on the rank-21–40 mid-cap perp cohort, 8h rebalance.**
- **Signal:** equal-weight ensemble of the centered within-band return-rank at lookbacks
  L ∈ {42, 63, 84, 126, 168} (`_xsmom`, unit-L1 normalized, averaged). Winners long / losers short,
  Σw ≈ 0 within the band.
- **Universe:** rank 21–40 by trailing-90-candle $-volume, survivorship-safe PIT pool (delisting-
  inclusive, per-bar seasoning ≥168), ex-stable. `rank_lo=20, rank_hi=40, season=168`.
- **Construction:** `engine_v2.run_book_from_signal` — inverse-vol size → gross-norm → lag(1) →
  hysteresis band (δ=0.010) + eligibility-exit (k=2) → renorm → vol-target → net (taker 5bps + liquidity
  slippage + funding).
- **Risk layer (iter-007, IS-calibrated, frozen):** `TARGET_VOL=0.006, MAX_LEV=2.0, dd_brake=OFF`
  (a uniform de-lever — Sharpe-invariant, drawdown-shrinking).

## Performance (OOS_CUTOFF = 2025-03-24; net of taker + slippage + funding)
| | IS | LATE (24→cut) | **OOS** | OOS 2025 | OOS 2026 | OOS maxDD | turn |
|---|---|---|---|---|---|---|---|
| **v2 baseline (ensemble + risk layer)** | +0.41 | +1.46 | **+1.37** | +1.61 | +0.84 | **−16%** | 0.157 |
| cost: 2× taker | — | — | **+1.03** | — | — | −17% | — |
| cost: pessimistic slip | — | — | +1.29 | — | — | −16% | — |
| — anchor (ported top-20 trend+carry) | +1.53 | +1.16 | **−0.01** | — | — | — | 0.30 |
| — de-inflated v1 top-20 (reference, diff universe) | +1.24 | — | +1.49 | — | — | — | 0.28 |

The IS +0.41 is weak ONLY because of the dead 2021–23 alt-season (which a forward book never trades);
the deploy-regime years are strong (per-year 2024 +1.3, 2025 +1.78, 2026 +0.84).

## Statistical record (dsr_v2.py — critic R3)
- **PSR(SR>0) = 0.938** (T=16 OOS months, SR_ann +1.37, skew +0.14, near-normal tails).
- **DSR vs XS-mom-family trials (N=9) = 0.834**; **DSR vs all-classes (N=24) = 0.372** (over-conservative —
  mixes the unrelated dead ML/funding/routing classes, null E[max]=+1.66ann).
- **Honest verdict:** the edge is real and well-corroborated (positive PSR, BOTH OOS sub-windows positive,
  survives 2× taker at +1.03, lower turnover, crypto-native mechanism) but the heavy search means the
  deflated significance is **MODERATE, not bulletproof**. Treat as a strong candidate, not a certainty.

## Methodology guarantees
- **Leak-safe:** signal + `run_book_from_signal` pipeline traced past-only; certified by tests #6/#9/#13/#16
  (incl. a direct future-perturbation test on the deployed path — R1). parity_check 1.041e-16, 16/16 tests.
- **Fixed-parameter:** zero monthly/walk-forward optimization in the deployed path; all hyperparameters
  inherited from v1/pre-registered, never fit to the v2 OOS.
- **Survivorship-safe + honestly costed:** PIT delisting-inclusive universe; taker + liquidity slippage.

## Crypto-native mechanism
Retail rotation / relative-strength chasing in the flow-rich rank-21–40 band: capital persistently chases
recent relative winners on a multi-day-to-few-week horizon. Dollar-neutral rank harvests the spread
regardless of cohort direction — which is why it carries the 2024–26 regime where the directional trend
stack (anchor) is OOS-dead.

## Dead paths (logged — what does NOT work on this cohort)
- Fixed-γ trend+XS-mom blend (/002), L2 cross-sectional ML (/003), BTC-beta-residual momentum (/004),
  factor-momentum routing (/005), weekly/monthly rebalance of XS-mom (/006), cross-sectional funding-fade
  sleeve (/009). The "combine trend+XS-mom" axis family is closed; carry is regime-faded.

## Open items / caveats
- DSR moderate (0.83 family / 0.37 all-classes) — monitor live; the edge could fade (carry did).
- 2026 OOS sub-window is the noisiest (n≈518); the ensemble holds it positive but it's the falsifier to watch.
- Exact-weight-hold confirmation backtest still owed (the 8h path doesn't use resampling, so low-risk).
- R2 (live full-seasoning gate to bound the warmup non-neutrality) before real capital.

## Run
```
export PATH="$HOME/.local/bin:$PATH"
uv run pytest tests/test_portfolio_v2.py -q              # 16/16
uv run python analysis/portfolio_v2/parity_check.py      # 1.041e-16
uv run python analysis/portfolio_v2/iter_v2_008_ensemble.py   # the baseline signal
uv run python analysis/portfolio_v2/iter_v2_007_risklayer.py  # risk layer before/after
uv run python analysis/portfolio_v2/dsr_v2.py            # deflated-Sharpe record
```
