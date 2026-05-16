# iter-v3/021 Symbol Candidate EDA — Synthesis

## Context

iter-v3/020 EXPLORATION (Critic FINAL `f913724`, diary commit `5287bd6`) closed
the per-symbol PnL share cap mechanism at the catalog level — concentration in
3-symbol BCH+LDO+TRX universe is lottery-REWARD source NOT lottery-RISK source.
Per `feedback_v3_concentration_is_signal.md` the orthogonal mechanism for the
concentration architecture axis is **universe expansion** (denominator
expansion — adds more symbols rather than scaling existing ones).

iter-v3/021 axis pre-commit per Critic FINAL Rec #1: HIGH-priority axis #2b =
universe expansion. This EDA evaluates 10 candidate NEW symbols against Gate 1
(data quality) + Gate 2 (liquidity) + structural complementarity to BCH+LDO+TRX.

## Method

Reads only IS-window data (2023-04-01 → 2025-03-24) for ranking; OOS coverage
reported informationally only. Composite score:

- 0.30 · complementarity (1 − mean_abs_corr_baseline)
- 0.30 · data_quality (gate1_pass × 0.7 + is_coverage_pct × 0.3)
- 0.25 · liquidity (log10(avg_daily_qvol) / log10(1e9), capped to 1)
- 0.15 · trade_rate_proxy (gate_retained_trades_per_month / 8, capped to 1)

Gate 1 thresholds: ≥24mo pre-IS history (for full TRAINING_MONTHS=24 walk-forward),
≥99% IS coverage, ≤5 gap candles in IS. Gate 2 thresholds: avg daily quote
volume > $20M AND P10 > $5M.

Candidate pool excludes V3_EXCLUDED_SYMBOLS (BTC/ETH/LINK/LTC/DOT/BNB/SOL/XRP/
DOGE/NEAR) + project_tried_symbols.md (DOGE/SOL/XRP/NEAR — already evaluated
2026-04-21) + MKR (dropped at iter-v3/013).

## Results — Ranking

| Rank | Symbol | Composite | Gate1 | Gate2 | IS cov% | Avg qvol $M | mean\|corr\| | NATR% |
|---:|---|---:|---|---|---:|---:|---:|---:|
| 1 | **HBARUSDT** | 0.756 | PASS | PASS | 100.0 | 126.4 | 0.410 | 4.27 |
| 2 | **AVAXUSDT** | 0.740 | PASS | PASS | 100.0 | 334.6 | 0.498 | 4.17 |
| 3 | ADAUSDT | 0.738 | PASS | PASS | 100.0 | 390.6 | 0.496 | 3.79 |
| 4 | FILUSDT | 0.724 | PASS | PASS | 100.0 | 220.6 | 0.534 | 4.15 |
| 5 | ALGOUSDT | 0.722 | PASS | PASS | 100.0 | 60.6 | 0.492 | 4.19 |
| 6 | ATOMUSDT | 0.709 | PASS | PASS | 100.0 | 105.8 | 0.531 | 3.54 |
| 7 | VETUSDT | 0.693 | PASS | PASS | 100.0 | 38.3 | 0.558 | 3.97 |
| 8 | OPUSDT | 0.532 | FAIL | PASS | 100.0 | 222.5 | 0.500 | 4.74 |
| 9 | ARBUSDT | 0.518 | FAIL | PASS | 100.0 | 290.9 | 0.540 | 4.32 |
| 10 | POLUSDT | 0.417 | FAIL | PASS | 26.5 | 57.7 | 0.595 | 4.46 |

OPUSDT, ARBUSDT, POLUSDT FAIL Gate 1 — insufficient pre-IS history for the
TRAINING_MONTHS=24 walk-forward window (OP listed 2022-06; ARB listed 2023-03;
POL listed 2024-09 after MATIC→POL rename). They are excluded from QR
recommendation.

## Top-2 Recommendation

### #1 — HBARUSDT (composite 0.756)

- **Lowest correlation to baseline universe**: mean |corr| = 0.410 (max with
  LDO 0.475, min with TRX 0.302). Strongest structural complementarity in pool.
- **Gate 1 PASS**: 100% IS coverage, 24.48mo pre-IS history (just enough for
  full 24mo training window), 0 gap candles.
- **Gate 2 PASS**: avg daily qvol $126M, p10 $12.5M — comfortably above
  thresholds. Min daily qvol $5.95M is the lowest in the pool but still above
  liquidity floor.
- **Volatility regime**: NATR_21 = 4.27% IS (slightly above BCH 3.5%, below
  LDO 6.8%, similar to TRX 3.0% scale).
- **Cap band**: MID (Hedera; layer-1 altcoin).
- **Trade rate proxy**: 2.88 trades/month (informational; below the 5+/month
  proxy of bigger-volume symbols, but the proxy is rough).

### #2 — AVAXUSDT (composite 0.740)

- **Mean |corr| = 0.498**: second-lowest in pool. Highest liquidity of all
  PASSING candidates (avg qvol $334.6M, p10 $93M).
- **Gate 1 PASS**: 100% IS coverage, 30.23mo pre-IS history, 0 gap candles.
- **Gate 2 PASS**: liquidity well above thresholds; 23.3% weekend share normal.
- **Volatility regime**: NATR_21 = 4.17% IS.
- **Cap band**: LARGE (Avalanche; layer-1 smart-contract platform).
- **Trade rate proxy**: 2.81 trades/month.

## Why HBAR + AVAX over Other Top-Scored Candidates

- **HBAR > ADAUSDT** despite ADA's bigger qvol: mean |corr| 0.410 (HBAR) vs
  0.496 (ADA) — HBAR is materially less correlated to baseline. Concentration
  reduction is the iter-v3/021 OBJECTIVE, not just liquidity addition.
- **AVAX > FILUSDT/ALGOUSDT/ATOMUSDT**: similar correlation profile to ADA but
  larger liquidity (AVAX $334M vs FIL $220M, ALG $60M, ATOM $105M); AVAX is
  the highest-liquidity Gate-1-passing candidate.
- **Both candidates use already-cached 8h klines** in `data/{SYM}/8h.csv` — no
  fetch required for backtest.

## Caveats

- **Trade-rate proxy is a rough heuristic** (NATR-based, gate retention assumed
  0.30 from iter-v3/018 anchor calibration). Real trade emission depends on
  the 7-gate risk stack which dominates. The proxy is informational only and
  not load-bearing for ranking.
- **Correlation is single-window IS-only**. The structural complementarity
  could regime-shift in OOS — but per single-axis discipline this EDA cannot
  examine OOS without contamination. Brief Section 2 may layer per-month or
  per-regime correlation diagnostics on top of this baseline.
- **Single-axis discipline at iter-v3/021**: the brief commits to ONE axis only
  — adding HBAR + AVAX as 2 NEW symbols (universe 3 → 5). NOT changing
  features, labeling, gates, ATR multipliers, ensemble, n_trials, or seed
  count. The cap mechanism is DISABLED in the iter-v3/021 first commit per
  diary `5287bd6` pre-commit.
- **"Adding 2 symbols" is technically two structural changes**, not one. The
  brief must justify the 2-symbol bundle as a single coherent axis (universe
  expansion to 5 symbols) rather than 2 independent variations.

## QR Inputs for Brief Authoring (Phase 5 — separate dispatch)

The brief author should:

1. Cite this synthesis + ranking CSV in Section 2 (IS-only numerical evidence)
2. Decide on 1-symbol vs 2-symbol expansion (ranking suggests both top-2;
   single-symbol may be cleaner attribution)
3. Predict IS Sharpe Δ band + OOS Sharpe Δ band per `feedback_axis_saturation_predictor`
4. Pre-register Falsifier 1 (PATH C indicator), Falsifier 4 (importance rank),
   Falsifier 5 (concentration shift)
5. Specify Risk Mitigation: per-symbol cap REMAINS DISABLED; the universe
   expansion is the orthogonal-mechanism attempt at the concentration gate
6. Behavioral-effect predictor per `feedback_axis_saturation_predictor`:
   estimate IS trade volume change (ranking proxy: +5.7 trades/month if both
   added at gate-retained rate ~ 2.85 each). Saturation falsifier: <80%
   predicted IS trade increase = saturated axis.

## Outputs (committed)

- `analysis/iteration_v3-021/symbol_candidate_eda.py` — this EDA script
- `analysis/iteration_v3-021/symbol_candidate_ranking.csv` — composite ranking
- `analysis/iteration_v3-021/per_candidate_data_quality.csv` — Gate 1 details
- `analysis/iteration_v3-021/per_candidate_liquidity.csv` — Gate 2 details
- `analysis/iteration_v3-021/per_candidate_correlations.csv` — corr matrix
- `analysis/iteration_v3-021/per_candidate_volatility.csv` — vol regime
