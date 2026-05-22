# Phase 7.5 Critic Review — iter-v3/124

OVERALL: EXPLORATION-NEGATIVE-catastrophic — IS Δ −0.870 / OOS Δ −0.943 vs /121 BASELINE_V3 (both legs > 2× the −0.40 NEGATIVE-catastrophic threshold); labeling-DURATION axis CLOSED bilaterally (K=42 /068 + K=63 /124).

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-7 slot #3 of 10; single-axis K=63 + Branch B sqrt(3) ATR scaling)

## QR Response Considered (Round 2 only)
N/A — single-round NEGATIVE-catastrophic; zero clarifications. First-match-wins gives Section 8 NEGATIVE-catastrophic before any other criterion can fire.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
K=63 horizon is TRAIN-TIME labeling parameter. Walk-forward post-fix at `walk_forward.py:113` (`train_end_ms = test_start_ms - embargo_ms`) intact: at K=63, embargo_ms = 64 × 480 × 60_000 = 1,843,200,000 ms ≈ 21.3 days. Branch B ATR multipliers applied at label-generation time using past-only natr_21. Trade arithmetic spot check clean.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP = 192 = (63+1)×3 (runner-local override per /068 precedent; validation_v3.py constant stays at 66). Per-cell embargo 64 candles (21.3 days). Symmetric application verified.

### Check 3 — Multiple-Testing Correction: SPLIT (informational for EXPLORATION)
DSR=0.0 informational, PSR=0.6068 (below 0.95), PBO=0.0649 PASS, frac_positive_paths=0.644 PASS. PBO axis (the only EXPLORATION-mode hard gate) passes. **The PSR collapse from /121's 1.0 → 0.6068 is itself a clean corroborating negative signal**: the /121 lift is GENUINELY LOST under K=63, not just deflated by architecture-mode compression.

### Check 4 — IC Correlation: PASS (by carry-forward)
No new features. V3_FEATURE_COLUMNS_TOP_N reverts /123's 15 → /121's 14. Engineered-feature carve-out cluster intact: regime_momentum_signed_5d / vwap_dev_20 = 0.7642 (Category-2 grandfathered). No new pair > 0.70.

### Check 5 — ADF Stationarity: PASS (by carry-forward)
14-feature stack identical to /121. ADF distribution matches /121.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS
Commit chain: setup `0efcd2d` + 2 pre-flight fix commits (ATR-assertion fix + config-accretion fix + feature-count fix). ITERATION_LABEL=v3-124. Explicit feature_columns. `_verify_timeout_consistency` asserts BacktestConfig.timeout_minutes == LightGbmStrategy.label_timeout_minutes == 30240. Trade arithmetic spot-checks clean.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis "K=21 → K=63 with PROPORTIONAL sqrt(K) ATR scaling carries incremental signal" implemented exactly: label_timeout_minutes 10080→30240, atr_tp 2.0→3.4641, atr_sl 1.0→1.7321. Single-axis discipline holds — coupled DURATION+MAGNITUDE is methodologically ONE axis per random-walk variance derivation.

## Substantive Verdict — NEGATIVE-catastrophic

Per Section 8 first-match-wins:
- IS Δ −0.870 << −0.40 threshold (2.2×); OOS Δ −0.943 << −0.40 threshold (2.4×)
- F1 IS regime-cost catastrophic TRIGGERED
- F6 OOS-collapse TRIGGERED

**Mechanism**: AFML sample-uniqueness loss at 67% (LDO 137→44, BCH 301→97, TRX 283→91). Branch B ATR scaling preserved per-step barrier semantics (IS timeout rate 4.4% comparable to K=21's 9.2%) but couldn't compensate for sample compression. Per-symbol attribution: BCH 77 IS / 27 OOS trades (huge IS-overfit signal); LDO IS net_pnl +31.9% with weighted_pnl −16.34 (low weights on winners); TRX marginally negative IS / positive OOS (frozen baseline pattern).

**Labeling-DURATION axis CLOSED bilaterally**: K=42 /068 (IS Δ −0.35 / OOS Δ −0.48, /060 anchor, retained ATR) + K=63 /124 (IS Δ −0.87 / OOS Δ −0.94, /121 anchor, Branch B ATR) both NEGATIVE-catastrophic at different scales and ATR configurations. Same second-order mechanism (sample-uniqueness collapse at large K) regardless of barrier semantics.

## Recommendations to QR for /125 Axis Selection

Cycle-7 axis menu state after /124:
- Axis 1 (cross-asset OHLCV): CLOSED (6 failures)
- Axis 3 (longer-cadence labels): CLOSED bilaterally
- Axes 2 (non-LightGBM) + 4 (new universe): LOCKED OUT per user constraints

Critic priority order for /125 under locked constraints:

1. **HIGHEST PRIORITY — Creative out-of-box: per-symbol drawdown brake at closed-loop simulator layer.** Per `feedback_v3_oracle_eda_validity.md`, STATEFUL gates require deadlock-impossibility proof in brief Section 2 (the /054 brake entered permanent deadlock). QR EDA must include closed-loop simulator showing brake transitions ON/OFF correctly through ≥2 hysteresis cycles in IS; brief pre-registers universe-cascade kill switch fallback. Highest priority because (a) /124 directly recommends this per closeout, (b) symbol-level concentration is structural drag since /121 (BCH 95.76% top-symbol share), (c) closed-loop discipline is auditable and not knob-tuning.

2. **MEDIUM PRIORITY — NEW engineered features at strict pairwise-IC gate (< 0.40 vs existing 14-feature stack).** Per `feedback_v3_structural_over_knob_exploration.md`. Restricted to FUNDING/OI/MICROSTRUCTURE/CROSS-ASSET-NON-OHLCV families (cross-asset OHLCV CLOSED). QR EDA pre-registers |IC| < 0.40 falsifier against ALL 14 existing features.

3. **LOW PRIORITY — Risk-management RiskV2 untested gate configurations.** Specific untested gate-threshold combinations (vol_scale_floor_per_symbol changes, per-symbol ADX overrides at LDO-only since LDO is dominant OOS loss carrier).

NOT RECOMMENDED for /125: (a) any DURATION axis (bilateral closure), (b) any cross-asset OHLCV (6-iteration streak), (c) /017-style meta-labeling revisits, (d) any axis whose EDA doesn't model AFML sample-uniqueness penalty.

## Clarifications Requested from QR — NONE
