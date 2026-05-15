# Phase 7.5 Critic Review — iter-v3/073

OVERALL: MERGE

OVERALL=MERGE certifies the SUSPICIOUS-OOS-DOMINANT classification clean: no methodology violation, single-axis discipline intact, Foundation Audit PASS, no look-ahead. Per the pre-registered Section 8.4 gate, iter-v3/073 does NOT auto-advance to cycle 2 CONFIRMATION — the axis is regime-exposed and closed at catalog level.

## Iteration Type
TYPE: EXPLORATION (cycle 2 #3 of 10). Check 3 (DSR/PSR/PBO) informational for EXPLORATION.

## Foundation Audit (Boot Steps 9-11)

- **Boot 9 — Walk-Forward Lookahead Fix: PASS.** `walk_forward.py:113` `train_end_ms = test_start_ms - embargo_ms`. `compute_embargo_candles(10080,480)=22` strictly covers the 21-candle triple-barrier horizon. Fix `e149e9d` intact, untouched.
- **Boot 10 — Regression Tests: PASS.** New `test_per_symbol_atr_v3_073.py` (6 assertions). Phase 5.5 BLOCK 4 (stale test) resolved at `d5d53a0`. 53-test v1/v2 suite passes.
- **Boot 11 — §11 Anti-Pattern Scan: PASS.** `labeling.py` clean — no labeling-window sigma, no shift omission, no future-fill. ATR `natr_21_raw` is past-inclusive EWMA.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Single axis = label-geometry change. Barrier distances consume `atr_values[idx]` at the entry index (causal). 22-candle embargo guarantees no training label's forward scan reaches the test month. Per-symbol multiplier change only rescales an already-causal ATR.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66=(21+1)×3. Embargo=22, symmetric. Axis changes barrier GEOMETRY not the label HORIZON — embargo arithmetic invariant.

### Check 3 — Multiple-Testing Correction: PASS (informational for EXPLORATION)
DSR=0.0 (legacy structural), dsr_relative_b4=1.0 (PASS), PBO=0.1541 (PASS<0.4), PSR=1.0. n_trials=315=35×3×3 (EXPLORATION budget). EXPLORATION-mode DSR/PSR informational per `feedback_v3_dsr_mode_artifact.md`.

### Check 4 — IC Correlation: PASS
No new feature — 14-feature set inherited UNCHANGED from /059. Highest pair `vwap_dev_20 × regime_momentum_signed_5d = 0.764` is the established Category-2 composed-feature carve-out. /073 introduces no new pair.

### Check 5 — ADF Stationarity: PASS
13/14 features stationary in recent training windows; `ret_kurt_200` marginal (p≈0.078) — inherited /028 property. No new price-derived feature.

### Check 6 — Pareto Dominance: PASS (N/A under unified architecture)
pareto_front.csv retired at Phase B-3. Gate 10-CPCV: frac_positive_paths=0.6444 ≥ 0.55 PASS. EXPLORATION = single 3-seed pass (outer=42 lineage).

### Check 7 — Reproducibility: PASS
Commit `d5d53a0` stamped. Explicit 14-feature feature_columns. Ensemble seeds literal in ensemble_summary.json. Trade-row PnL spot-checks (2 rows) match to float precision. Per-symbol sums reconcile (OOS 106, IS 176, OOS wpnl 64.9329).

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis implemented exactly: V3_ATR_MULTIPLIERS_PER_SYMBOL={BCH:(2.0,1.25), LDO:(1.5,1.25)}. Edit 2 revert present (label_mode="triple_barrier"). 4 Phase 5.5 BLOCKs resolved at `d5d53a0`. Single-axis discipline confirmed — every adjacent surface (features, models, 7 risk primitives, embargo, timeout) verified unchanged. TRX IS byte-identical to /060 = positive control that the axis fired ONLY on BCH+LDO.

## Adversarial Questions — Findings

**Q1 — /073 distinct from /065's rejected universal SL widening?** Mechanically /073 IS in the SL-widening family (BCH/LDO SL 1.0→1.25). The QR does NOT hide this — brief Section 4.4 pre-registers the SUSPICIOUS gate BECAUSE it is SL-widening; Section 7 weights NEGATIVE 35% citing /065 precedent. Honest disclosure posture — the QR called the failure mode before the run, the run produced it, the gate fired. The /070 CONFIRMATION precedent (/065 single-seed OOS surge → IS −0.97 at multi-seed) is the controlling evidence against advancing /073. Concur.

**Q2 — LDO OOS-positive genuine edge or regime exposure?** LDO IS DID genuinely improve (WR 27.3%→44.4%, net_pnl −11.44%→−9.997%, +1.4pp) — so the aggregate IS collapse is NOT a hidden LDO failure. BUT: a +1.4pp IS net_pnl improvement cannot underwrite a +43pp OOS swing (−25.08→+18.23 wpnl). The EDA itself is decisive: LDO `directional_spread` is NEGATIVE across all 9 grid cells; the axis "corrects the barrier pathology, does NOT manufacture a positive LDO label spread." The +1.4pp-IS / +43pp-OOS split is the regime-exposure signature. The LDO OOS-positive result is dominantly regime exposure; it does NOT survive as edge evidence.

**Q3 — 3-consecutive SUSPICIOUS-OOS-DOMINANT (2.87→4.51→6.85) a structural regime signal?** YES — the most important finding of the iteration. /065 (universal SL widening), /071 (meta-labeling), /073 (per-symbol SL widening) share ONE mechanism: each extends effective trade holding time. The IS window (2022-09→2025-03: bear+recovery+2024 bull+chop) penalizes longer-held trades; the OOS window (2025-03→2026-05: persistent uptrend) rewards them. Three independent axes all loading the same regime factor with escalating leverage. Research-level finding exceeding any per-iteration verdict.

**Q4 — OOS/IS 6.85 + OOS Sharpe +1.90 a leakage artifact?** NO. Walk-forward fix intact, 22-candle embargo covers 21-candle horizon, ATR is past-inclusive EWMA, §11 scan clean, TRX byte-identical IS = positive control. OOS +1.90 is a GENUINE property of the wider-SL config on a trending OOS window (PSR=1.0, dsr_relative_b4=1.0 confirm OOS Sharpe is statistically real). The SUSPICIOUS classification is orthogonal — it flags the IS/OOS DIVERGENCE as regime exposure, not the OOS number as fabricated.

## Recommendations to QR

1. **Cycle 2 #4 (/074) must NOT be another holding-time-extension axis.** Three consecutive SUSPICIOUS-OOS-DOMINANT (/065, /071, /073) with escalating ratios is a saturated signal — any axis lengthening effective holding time (wider SL, meta-labeling filtration, per-symbol barrier rebalancing) loads the v3 IS/OOS regime factor and trips the ratio gate. Per `feedback_v3_axis_saturation_predictor.md`, this family is saturated. /074's QR EDA must select a holding-time-orthogonal axis OR a dedicated IS/OOS regime-diagnostic axis (regime-stratified IS sub-period analysis: bull 2024-01→2025-03 vs bear/chop 2022-09→2023-12).

2. **The 3-consecutive-SUSPICIOUS pattern warrants a pre-registered entry in `briefs-v3/exploration_catalog.md`** (and a memory rule), not just a diary line. The finding — v3's IS (2023-2025) and OOS (2025-2026) regimes are structurally divergent; holding-time-extension axes mechanically exploit this — is cycle-level and should constrain the remaining cycle 2 agenda so it is not re-discovered a fourth time.

3. **QR Phase 8 diary should record the SUSPICIOUS-precedence-over-NEGATIVE application explicitly.** IS Δ −0.5546 independently fires the Section 8.2 NEGATIVE gate; SUSPICIOUS supersedes per the /071 precedent (no magnitude qualifier). Both classifications converge on "do not advance"; the per-symbol SL-widening axis is closed at catalog level either way.
