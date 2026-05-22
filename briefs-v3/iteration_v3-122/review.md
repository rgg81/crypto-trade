# Phase 7.5 Critic Review — iter-v3/122

OVERALL: EXPLORATION-NEGATIVE-INERT — F2/F3/F4 falsifiers all triggered; Section 8 criterion 3 (NEGATIVE-INERT) is first-match. Axis-CLOSE recommendation for eth_ret_3d primitive (IC-spanned by vwap_dev_20 0.56 + regime_momentum_signed_5d 0.53 incumbents); broader ETH-OHLCV cross-asset hypothesis not auto-CLOSED per QR's per-primitive interpretation.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-7 slot #1 of 10)

## QR Response Considered (Round 2 only)

N/A — Round 1 emitted ZERO clarifications. The evidence chain is unambiguous: every Section 8 first-match condition for criterion 3 (NEGATIVE-INERT) is independently verifiable from the engineering report tables + reports-v3/iteration_v3-122 artifacts; the dual-anchor protocol declared in brief Section 4 / Section 8 anchor block produces the same verdict regardless of which anchor is canonical for each falsifier.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`eth_ret_3d` at `src/crypto_trade/features_v3/cross_btc_v3.py:56-76` uses past-only array indexing: `df["eth_ret_3d"] = np.concatenate([np.full(9, np.nan), log_close[9:] - log_close[:-9]])`. At row t the value is `log(close[t]) - log(close[t-9])` with the first 9 bars NaN. ETH klines merge via `merged = merged.merge(eth, on="open_time", how="left")` at line 137 — the same convention as the existing `btc_ret_14d` BTC merge (line 100), already verified clean. The adversarial unit-test `test_eth_ret_3d_past_only` in `tests/features_v3/test_cross_btc_eth_v3.py` covers the future-bar mutation invariant. ETH OHLCV at the bar's close_time is "knowable" at the symbol's bar-decision time (same-frequency 8h bars). No look-ahead.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 unchanged from /121 baseline. Walk-forward fix `e149e9d` active. No labeling/universe change.

### Check 3 — Multiple-Testing Correction: PASS
PBO=0.1412 PASS, PSR=1.0 PASS, frac_positive_paths=0.6444 PASS, dsr_relative=0.9999 PASS. DSR=0.0 EXPLORATION-mode structural artifact (`feedback_v3_dsr_mode_artifact.md`).

### Check 4 — IC Correlation: PASS (with structural note)
Max |IC| for `eth_ret_3d` is 0.5613 with `vwap_dev_20`; secondary 0.5280 with `regime_momentum_signed_5d`; tertiary 0.4055 with `btc_ret_14d`. All < 0.70 strict threshold — mechanically PASSES. Structural implication: new feature's information is **substantially spanned by 2-3 incumbents** at the 0.50-0.56 |IC| range. This explains the F2 importance-INERT outcome at production (rank 14/15 portfolio, share 3.9%): trees at depth 3-5 cannot exploit marginal information when 2 incumbents already provide cross-asset momentum coverage at |IC| > 0.5. The QR's hypothesis is mechanically discredited by the same IC distribution that EDA T2 measured.

### Check 5 — ADF Stationarity: PASS
eth_ret_3d ADF at OOS-boundary IS month (2025-03): BCH adf_stat=-8.57 p=0.0; LDO adf_stat=-8.57 p=0.0; TRX adf_stat=-8.57 p=0.0. Stationary by log-return construction.

### Check 6 — Pareto Dominance: N/A
Single-seed EXPLORATION. CONFIRMATION-mode validation deferred to /132.

### Check 7 — Reproducibility: PASS
Commit chain: `ac0f891` (setup) + `f88415c` (pre-flight assertion fix len==14→15) verified. Runner uses explicit feature_columns. Inner ensemble seeds verbatim in ensemble_summary.json. Pre-flight assertions verify len=15, eth_ret_3d present, ret5d_signed_tbi absent, enable_no_confirm_exit=True, REQUIRED_GAP=66.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 3 6 changes all delivered (ETH loader, V3_FEATURE_COLUMNS 14→15, ITERATION_LABEL, parquet regen, unit test, integration test). No scope creep. Hypothesis "eth_ret_3d carries incremental directional signal beyond 14-feature stack" exactly tested; FALSIFIED outcome (Mode 2 INERT, F2 fired, IC-spanning explains mechanism) honestly registered.

## Mechanical Classification & Verdict Notes

Per Section 8 first-match-wins on the dual-anchor classification:

1. **NEGATIVE-catastrophic (criterion 1)**: IS Δ vs /121 multi-seed = −0.34 (NOT < −0.40); OOS Δ vs /121 multi-seed = +0.20 (NOT < −0.30). **NOT TRIGGERED.**
2. **NEGATIVE-no-effect (criterion 2)**: IS Δ vs EXPLORATION-mode anchor = −0.089 (NOT in [−0.05, +0.05]). **NOT TRIGGERED.**
3. **NEGATIVE-INERT (criterion 3)**: (a) production importance rank ≥ 14/15 on > 1 symbol — BCH 14/15, TRX 15/15 → YES; (b) POOLED lift estimate < +0.005 — portfolio rank 14/15 share 3.9% → YES; (c) IS Sharpe Δ < +0.05 — IS Δ vs EXPLORATION-mode anchor = −0.089 < +0.05 → YES. **FIRST MATCH. VERDICT EXPLORATION-NEGATIVE-INERT.**

Section 8 criterion 8 (SUSPICIOUS-OOS-DOMINANT) would also fire vs EXPLORATION-mode anchor but criterion 3 first-matches. F3 falsifier (suspicious-OOS-dominant) TRIGGERED at /121 multi-seed anchor as confirming secondary signal — same root cause (loss-surface reorganization at TRX without importance allocation; the /082/085/086/119 C6 dissociation pattern).

F2 (importance INERT) TRIGGERED. F3 (suspicious-OOS-dominant) TRIGGERED. F4 (TRX-carrier SSC at PnL level) TRIGGERED: TRX IS PnL Δ +32.45, BCH IS PnL Δ −64.62, LDO IS PnL Δ −8.05. Importance-allocation level shows TRX-carrier INVERSION (TRX rank 15/15, dead last). The PnL-level carrier is real but unrelated to direct signal; it is Optuna-loss-surface reorganization at TRX (/119 C6 dissociation mechanism).

OOS Sharpe headline (+1.1642 absolute, +0.20 vs /121 multi-seed, +0.31 vs EXPLORATION-mode anchor) is a single-seed loss-surface-reorganization artifact, not robust signal. CPCV path distribution (q25=−0.243 substantial left tail; q50=+0.335; 35% paths Sharpe-negative) consistent with INERT-by-importance pattern.

## Recommendations to QR (for /123 axis selection)

1. **eth_ret_3d primitive CLOSED at /122**; the broader ETH-OHLCV-cross-asset hypothesis is NOT auto-closed. /123 may test an ETH-derived primitive that is NOT spanned by `vwap_dev_20` or `regime_momentum_signed_5d` (e.g., ETH realized-volatility regime classifier, ETH cross-sectional rank vs alt cohort) — but EDA T2 R² against the FULL 15-feature anchor must clear the gate **AND** EDA must show pairwise |IC| < 0.40 with `vwap_dev_20` and `regime_momentum_signed_5d` specifically. Joint-R² is insufficient diagnostic for ETH-derived primitives.

2. **Cycle-7 axis menu pivot consideration**: given /122's INERT outcome on cross-asset axis-1, the QR should either (a) continue cross-asset with a non-IC-spanned primitive per recommendation 1, OR (b) pivot to axis-3 longer-cadence labels with a coherent label+execution structural redesign (label horizon AND barrier AND REQUIRED_GAP scaled together to avoid /068's failure mode). Both admissible.

3. **Pre-register dual-anchor disambiguation explicitly in /123 brief Section 8**: the /122 brief's anchor block declared dual-anchor but Section 8 criteria 2-8 did NOT explicitly specify which anchor applies to each. The /122 outcome is unambiguous, but a future EXPLORATION where IS Δ falls in the [−0.05, +0.05] EXPLORATION-anchor band but outside the /121-multi-seed band could produce verdict ambiguity.

## Clarifications Requested from QR — NONE
