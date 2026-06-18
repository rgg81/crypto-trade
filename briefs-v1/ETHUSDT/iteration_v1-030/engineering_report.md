# iter-v1/030 Engineering Report — AGREE_SCALE conviction modulator (ETHUSDT)

**Phase 6 SETUP-ONLY** (no backtest run — iter-029 K=20 confirmation owned the compute).
Implemented by the Quant Engineer (opus). All edits purely additive (+286 lines, 0 deletions) →
byte-identity preserved for every prior iter-016→029 run.

## Design implemented = AGREE_SCALE (QR brief §3.2), NOT the FE direction-replacement
The conviction-gate quantity `conv = |close[t-1]−SMA200[t-1]| / ATR14[t-1]` is multiplied by a
deterministic past-only **agreement fraction** = fraction of the 3-signal panel **P3**
{`ma_cross(50,200)`, `donchian(55)`, `tsmom(42)`} that points the SAME way as the **unchanged**
SMA-200 anchor direction. Direction sign stays byte-identical to iter-027; only the conviction
quantity is modulated, so low-agreement (chop) rows fall below the q=0.40 gate and stand aside.
This is the Pareto-dominant design the QR selected after testing-and-rejecting direction
replacement (which trades away the recent-regime edge +1.31→+0.54).

## Files changed
- **src/crypto_trade/strategies/ml/lgbm.py** (+79): constructor flag `enable_agreement_scale: bool
  = False` (default-off byte-identity); in the trend-strength index-build block, when the flag is
  on, compute P3 panel signs + anchor + `agreement = mean(panel==anchor, axis=0)` and set
  `_abs_dist = _abs_dist * agreement` BEFORE storing `_trend_strength_idx`. Modulating the series at
  build time makes BOTH the per-month q=0.40 threshold AND the per-candle value consistent (the
  trick). `_abs_dist` NaN at warmup stays NaN → gate fallback preserved. decision_log gains
  `"agreement_scale"` for attribution.
- **run_baseline_v1.py** (+201, includes the iter-029 confirmation branch): module constant
  `V1_ITER030_AGREE_PANEL`; `_spec_enable_agreement_scale` default False; new keyed branch
  `elif iteration_label == "v1-030" and len(symbols)==1 and symbols[0]=="ETHUSDT":` cloning the
  iter-027 ETH M1 stack + `_spec_enable_agreement_scale=True` (M2 OFF); pass-through threaded into
  `run_model`/`run_meta_model` and the universal single-symbol guard. The new branch is gated on
  single-symbol ETH so it cannot collide with the pre-existing (inert) 5-symbol v1-030 M2 branch.
- **src/crypto_trade/strategies/ml/metalabeling.py** (+6): `enable_agreement_scale` forwarded to
  M1 (symmetry; default off, not exercised by iter-030).
- **tests/test_agreement_scale_lookahead.py** (new): 9 look-ahead + byte-identity tests.

## Verification (no backtest)
- `tests/test_agreement_scale_lookahead.py`: **9 passed** (future-candle leak, agreement-matches-
  manual, decision-candle-own-bar, uses-close[t-1], default-off byte-identity, off-vs-on differ,
  valid-range, threshold-past-only).
- Existing look-ahead suites (trend_state + trend_strength + metalabel): **33 passed** (no
  regression). Combined **42 passed**.
- **Default-off byte-identity PROVEN on the real ETH parquet**: with the flag off,
  `_trend_strength_idx[1]` is bit-identical to the raw `|dist_atr|` production formula (6873 finite
  of 7073 rows). With the flag on, 2916 finite rows are modulated, ON ≤ OFF everywhere (agreement
  ≤ 1), NaN positions identical.
- `ruff check` + `py_compile`: clean on edited files (the 43 pre-existing E501 in run_baseline_v1.py
  are untouched legacy debt; 0 new long lines introduced).

## Launch command (orchestrator, AFTER iter-029 completes)
```
PYTHONUNBUFFERED=1 uv run python run_baseline_v1.py --exploration --iteration 30 \
  --symbols ETHUSDT --n-trials 35 --slippage-bps 2
```
**n_trials=35** (NOT 18) — matches the iter-026/027/028 ETH lineage so the ONLY difference vs
iter-027 is the agreement modulator (single-axis cleanliness; 18 would confound the axis with a
trial-budget change). `--exploration` → K=5 bagging.

## Pre-registered falsifiers (from brief §4 — measured IS-only on the EXPLORATION)
CONFIRM (→ K=20) requires ALL: F1 IS top-2 trade share strictly below iter-027's; F2 IS Sharpe ≥
+0.6336 − 0.05; F3 recent-IS-subperiod book stays strong (proxy ≥ +1.10); F4 IS trade count ≥
0.85× iter-027. KILL if any of K1 (no de-concentration), K2 (IS Sharpe regresses >0.05), K3 (recent
edge gutted <+1.00), K4 (trade count drops >25% → collapsed to hard veto).
