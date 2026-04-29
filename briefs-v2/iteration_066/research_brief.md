# iter-v2/066 Research Brief — IS-only universe re-screening

**Type**: EXPLORATION (new symbol selection from scratch)
**Parent baseline**: iter-v2/059-clean
**User directive**: generic solution, not NEAR-specific overfit. Fail fast.

## Section 0 — Data Split

`OOS_CUTOFF_DATE = 2025-03-24` — immutable. All screening in this iteration
uses IS-only (before 2025-03-24).

## 1. Problem & hypothesis

The current DOGE/SOL/XRP/NEAR universe was chosen via iterative
evolution (iter-v2/001 → v2/059) with implicit peeking at concentrations,
Sharpe, per-symbol behaviour. The per-symbol cap fixes in iter-v2/064-065
were themselves NEAR-specific — user flagged as data snooping.

Hypothesis: a **principled IS-only ranking** of candidate symbols, with
forbidden list respected, should produce a portfolio whose concentration
is not artefacts of OOS cherry-picking.

## 2. Method — Fail-fast two-stage screen

### Stage 1 — Quick LGBM ranker (<30s/symbol)

For every eligible candidate:
- Load v2 features, IS-only (before 2025-03-24)
- 80/20 train/test split on IS
- Train LightGBM with n_trials=5, single-seed
- Predict on test holdout
- Compute trade-Sharpe using the same triple-barrier ATR labels as
  production

Rank by test-Sharpe. Estimated total: ~26 candidates × ~30s = 13 min.

### Fail-fast gate

If **top-5 test-Sharpe of candidates < top-5 test-Sharpe of current
universe (DOGE/SOL/XRP/NEAR)**, ABORT. Don't waste time running a full
baseline on a portfolio that's no better than the current one.

### Stage 2 — Full baseline (only if Stage 1 passes)

Pick top 4-5 candidates by Stage-1 rank. Update `V2_MODELS`, run full
baseline (~2.5h single-seed). Evaluate against iter-v2/059-clean.

## 3. Candidate universe

All symbols in `data/features_v2/` with ≥1,500 IS candles (>~1.3 yrs),
excluding:
- v1: BTCUSDT, ETHUSDT, LINKUSDT, BNBUSDT
- user-forbidden: DOTUSDT, LTCUSDT
- delisted (last kline >3mo before OOS cutoff): MATICUSDT

Estimated ~23 candidates including current {DOGE, SOL, XRP, NEAR}.

## Section 6 — Risk Management Design

Unchanged. The 6 active gates (vol-scaling, ADX, Hurst, z-score OOD,
low-vol, BTC trend) stay at iter-v2/059-clean settings. This iteration
is about symbol universe, not risk layer tuning.

### 6.3 Pre-registered failure modes

**Most likely failure**: Stage-1 single-split Sharpe is a weak predictor
of walk-forward Sharpe (fewer data points, no retraining). Top
candidates by Stage-1 may underperform in Stage-2 walk-forward. If so,
we waste one 2.5h baseline run.

**Mitigation**: Stage-1 fail-fast gate requires top-5 Stage-1 Sharpe to
BEAT current universe, not just match. If current universe is close to
the best, we won't bother running Stage 2.

**Secondary failure**: IS screening selects symbols that overfit to IS
regime (say, 2022-2024). Stage 2 walk-forward will reveal this. If OOS
monthly Sharpe < 0.85 × baseline, NO-MERGE.

## 4. Success criteria

MERGE iff Stage 2 passes:
- Combined IS+OOS monthly Sharpe > baseline (+2.70)
- Concentration: max seed share ≤ 45% (relaxed from 40% for 4-symbol, to allow some flexibility)
- OOS monthly Sharpe ≥ 0.85 × baseline (+1.41)
- IS monthly Sharpe ≥ 0.85 × baseline (+0.88)
- OOS MaxDD ≤ 1.2 × baseline (27.1%)

NO-MERGE if Stage 1 fails (candidates not better than current) — cherry-pick
docs only.

## 5. Deliverables

- `screen_v2_candidates.py` — Stage-1 screener
- `reports-v2/iteration_v2-066/candidate_sharpe.csv` — Stage-1 ranking
- (If Stage 2 runs) `reports-v2/iteration_v2-066/` — full reports
