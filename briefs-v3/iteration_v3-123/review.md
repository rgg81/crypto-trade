# Phase 7.5 Critic Review — iter-v3/123

OVERALL: EXPLORATION-NEGATIVE-catastrophic — IS Sharpe Δ -1.73 vs /121 multi-seed (threshold < -0.40); F5 C6-DISSOCIATION-PATTERN-RECURRENT secondary fire (LDO EDA rank 1/15 → production rank 11/15)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-7 slot #2 of 10; single-axis: replace eth_ret_3d with eth_vs_sym_rv_50 as 15th feature)

## QR Response Considered (Round 2 only)
No clarifications raised — catastrophic verdict unambiguous. Round 2 emitted directly per zero-clarification short-circuit.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
B1 at `cross_btc_v3.py:57-88` past-only by construction. ETH 1-bar log returns via `np.concatenate([[np.nan], np.diff(log_close)])`, then `eth_rv_50 = pd.Series(log_ret_1bar).rolling(50, min_periods=50).std()` — canonical past-only rolling. Merge `on="open_time", how="left"` — no future bars. The ratio against the panel's own `range_realized_vol_50` uses the same past-only convention. OOS BCH WR 60% spike is NOT look-ahead artifact — it is vol-regime classification artifact where IS/OOS partitions invert.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 unchanged. Walk-forward POST-FIX `e149e9d` intact.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (EXPLORATION mode)
PBO=0.1042 PASS, PSR=1.0 PASS, frac_pos=0.6444 PASS. DSR=0.0 degenerate because IS Sharpe negative (mathematically correct, not defect). CPCV path statistics bit-identical to /121 (frozen-baseline pattern per `feedback_v3_single_seed_frozen_baseline.md`).

### Check 4 — IC Correlation: PASS
Production IC matrix confirms /122 Critic Rec 1 strict pairwise gate: B1 vs `vwap_dev_20` = 0.0567 (PASS by 7.1× margin); B1 vs `regime_momentum_signed_5d` = -0.0177 (PASS by 22.6× margin). EDA predictions (0.0687, 0.0205) match production. Joint R²=0.39 < 0.70. The B1 vs `range_realized_vol_50` = -0.5353 is structural by denominator-sharing (carve-out adjudicated in brief Section 2.2).

### Check 5 — ADF Stationarity: PASS
B1 ADF at final IS month (2025-03): BCH -3.352 p=0.0127, LDO -4.286 p=0.00047, TRX -3.329 p=0.0136. All p<0.05.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
Setup `32306c3`, engineering `89a1acf`, brief `aa0b29a`, EDA `dbc2993`. ITERATION_LABEL=v3-123 verified. Explicit `feature_columns=_feature_columns` (no None). Pre-flight assertions: eth_vs_sym_rv_50 PRESENT, eth_ret_3d ABSENT, len==15. V3_EXCLUDED_SYMBOLS disjointness OK. Trade-level spot checks (2 OOS trades) reproduce math exactly.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 3.5 5-file manifest exactly implemented. No scope creep. /116 no_confirm STAYS enabled. /119 C6 STAYS BANNED. Catastrophic OOS-IS dissociation is TRUE NEGATIVE on registered hypothesis, not implementation artifact.

## Recommendations to QR

1. **Cycle-7 cross-asset axis broadly CLOSED at OHLCV-derived primitive class**. Six consecutive cross-asset failures: /082 (funding), /085 (funding-z), /086 (basis), /119-C6 (ret5d_signed), /122 (eth_ret_3d), /123 (eth_vs_sym_rv_50). Mechanism: in BCH/LDO/TRX 8h universe, cross-asset OHLCV-derived features either become INERT or become harmful regime classifiers with diverging IS/OOS distributions. **Next cross-asset axis (if any) MUST use structurally different primitive class** — on-chain (Glassnode), liquidations, non-Binance basis — with external-feed access decision adjudicated upfront. Pure OHLCV-derived ETH/BTC primitives at any window or transform CONSIDERED EXHAUSTED.

2. **EDA single-window importance NOT reliable for cross-asset**. /122 + /123 demonstrate EDA T5 on fixed single window does NOT generalize across rolling walk-forward distribution. **For future cross-asset axes, EDA Section 2 MUST include rolling-window T5 importance test across at least 3 IS endpoint slices** (e.g., 2023-Q1, 2024-Q1, 2025-Q1) and report rank stability range. Feature predicted top-1 at one window and bottom-third at another must trigger F-falsifier on rank instability.

3. **Pivot /124 axis AWAY from cross-asset entirely**. Per cycle-7 menu and established cross-asset exhaustion, /124 should select from: **longer-cadence labels axis-3** (1d or 3d horizon-extended triple-barrier — currently 21-bar 8h ≈ 7-day horizon; doubling to 14d most-deferred high-priority axis in cycle 7), OR creative out-of-box (per-symbol drawdown brake at closed-loop simulator layer with deadlock-impossibility proof per `feedback_v3_oracle_eda_validity.md`). The OOS +1.75 headline should NOT seduce QR into cross-asset retry — engineering report Section 11 explicit it's regime-classifier artifact, not signal. Cycle-7 has 8 EXPLORATION slots remaining; trajectory should diversify away from 6th-consecutive cross-asset failure.

## Clarifications Requested from QR — NONE
