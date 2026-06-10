# Phase 7.5 Critic Review — iter-v1/085

OVERALL: SPECIALIST-NEGATIVE — triple-falsified (F2-PRIMARY INERT + F3 probe-flat + F4 momentum-dominated); structureless single-seed-convergent loss model; +0.17 OOS is noise, not edge; foundation + no-cheating audit clean.

## Iteration Type (from Brief Section 0.5)
TYPE: SPECIALIST — UNIUSDT single-coin cohort; NEW 4-feature mean-reversion set; fresh-alt MINE under the REFINED structure-gated selector. Check 3 edge axes (DSR/PSR) are INFORMATIONAL for a SPECIALIST and cannot trigger BLOCK; verdict adjudicated on methodology + falsifier axes (Checks 1, 2, 6, 8, 14) and pre-registered F1-F4.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Foundation re-audited (Boot Step 11). `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms` — UNCHANGED by QE's commits; embargo from centralized `compute_embargo_candles`. 4 regression tests present in `tests/test_lookahead_embargo.py`. The 4 NEW features re-confirmed causal (`.shift(1)`, trailing rolling windows, backward-looking AR(1) half-life). **Empirical**: OOS first trade `1743206399999` (2025-03-28), 5.0 days AFTER cutoff `1742774400000` (2025-03-24) — zero OOS trades open before cutoff.

### Check 2 — Embargo Width: PASS
Centralized embargo subtraction at the train/test boundary; bit-exact inherited /063→/084 config. 5.0-day realized IS→OOS gap consistent with multi-bar triple-barrier embargo on 8h candles.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (SPECIALIST layer)
Two DSR figures exist + scrutinized: comparison.csv raw `[report]` DSR (−52.35/−59.12) vs dsr.json N_eff-corrected DSR (+0.0936 IS / +0.591 OOS). Pre-existing dual-metric in the reporting pipeline, NOT iteration-specific manipulation — both flow from the same run, both agree IS edge is absent. Corrected IS DSR 0.0936 (~9% prob true Sharpe > 0); PSR_monthly_vs_0 = 0.000272 IS. n_eff=1 = degenerate single-symbol value, expected.

### Check 4 — IC Correlation: INFORMATIONAL
ic_matrix.csv present. Capstone-vs-primitive correlation is feature-vs-feature (Category-2 carve-out), does not gate. Empirically moot: both directional features INERT (rank 42/39), tree used neither.

### Check 5 — ADF Stationarity: INFORMATIONAL
adf_test.csv present. Does not gate per 2026-06-01 revision.

### Check 6 — Pareto Dominance: PASS (degenerate, single-seed by directive)
Single-outer-seed=42 SPECIALIST with 50-INNER-seed ensemble (multi-seed CONFIRMATION permanently dropped per 2026-06-09 directive). `basin_diagnostics.json`: V1 cross_seed_sharpe_std = 0.000 (PASS); v1_cross_seed_variance.csv std_sharpe = 0.0 across all 50 seeds. OPPOSITE of a basin-lottery — all 50 seeds converged → NEGATIVE is structurally reliable. GLOBAL=BORDERLINE is NaN-propagation from V2/V3 single-symbol-degenerate metrics, not a signal concern. Basin-lottery vigilance satisfied (spread 0.000 < 0.50).

### Check 7 — Reproducibility: PASS
Commit b664d479 stamped. Explicit feature_columns (52 cols, asserted len==52). 50 inner seeds = literal range(42,92). PnL spot-check first IS trade: −1×(6.451562−6.037)/6.037×100 = −6.867%, matches pnl_pct −6.8670. The `[FATAL] engineering_report.md NOT FOUND` lines = expected split-dispatch guard, not data-integrity failure.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 1 hypothesis maps exactly to src/: V1_ITER085_UNIVERSE=("UNIUSDT",), 4 named features, LOCAL 52-col override gated to UNI dispatch only, NO new risk primitive (Section 3.3 honored). Every code change traces to a brief sentence.

**Critical Check-8 adjudication — the +0.17 OOS must NOT be spun as positive: CONFIRMED.**
- Both merge floors fail: IS −0.7005 < 1.0, OOS +0.1739 < 1.0.
- OOS significance absent: DSR_corrected OOS 0.591 (59% prob > 0), PSR_monthly_vs_0 0.5619 (≈coin-flip), PSR_monthly_vs_1 0.1647.
- OOS monthly_pnl 7 pos / 9 negative months — +0.1739 carried by a few large positives (2025-05 +8.2%, 2025-11 +14.4%) vs large negatives (2025-07 −15.3%); slightly negative on month-count. NOT a persistent edge.
- OOS WR 40.5% / PF 1.05 = sub-50% noise-trading. Structureless in BOTH windows; OOS landed mildly positive by regime luck. Does NOT rescue/soften/re-tag.

### Check 14 — Axis Family Validation: PASS
Section 0.6 declares per-cohort-specialization-UNI (NEW mean-reversion feature-family + NEW single-coin universe + NO risk-primitive change). src/ matches; declared family honest. Rotation VALID (UNIUSDT distinct from prior 5: /064 ETH, /065 BTC, /078 AAVE, /083 FIL, /084 CRV; ∉ BUNDLE-002 ∉ failed-set ∉ EXCLUDED). **Global invariant verified**: V1_FEATURE_COLUMNS_PRUNED == 48 (asserted __init__.py:213); 4 features LOCAL-only in V1_ITER085_FEATURE_COLUMNS == 52 (asserted :242); PRUNED did NOT grow — recurring /083+/084 leak-bug absent.

## Independent Verification of the Triple-NEGATIVE
- **F2-PRIMARY (NEGATIVE-INERT-FEATURE) — CONFIRMED.** rev_extension_z_3 rank 42/52 (gain 203.5) ≫ 14/52 threshold; rev_vol_gate_signed rank 39/52. Both directional features inert. F2-SUSPICION did NOT fire (capstone didn't dominate while primitive went quiet — clean signal-absence, not /084 anti-signal). Vol-state features bound (rank 3/9) but as REDUNDANCY with vol_atr_14 (rank 1) / vol_natr_14 (rank 12). LM 7.4 labeling-horizon-mismatch diagnosis sound: 3-bar sub-1% reversion completes inside 1.45×ATR stop → label never sees the kernel; corroborated by interact_ret1_x_ret3 (lag-3 proxy) near-dead at rank 49. Correlation-in-raw-returns ≠ tradeable label causation.
- **F3 (NEGATIVE-PROBE-FLAT) — CONFIRMED.** IS −0.7005 is Δ−0.46 BELOW the −0.243 probe, not +0.25 above. NEW features WORSENED IS (inert-features-amplify-noise at higher Optuna budget). UNI = 2nd confirmed case after CRV that the locked architecture can't manufacture a structure-gate pass on a sub-probe coin.
- **F4 (NEGATIVE-MOMENTUM-DOMINATED) — CONFIRMED.** IS −0.7005 < 0 and < trivial −0.2485. Worse than not trading.

**Magnitude attribution — CONFIRMED and correctly bounded.** monthly_pnl: 2022-09 = −43.87% of −46.63% IS total = 94.1% of all IS loss. trades.csv: first 5 UNI trades at weight_factor 1.0, 4/5 stop-losses ~−6/−7%; R5 vol-target floor (0.33) engages only from trade ~10. R5 cold-start hazard: full-size into UNI's 2022-09 listing-shock with no accumulated vol-damp. Does NOT rescue (IS-ex-2022-09 still negative ~−2.8%, 38% WR / 168 trades). SIGNAL verdict = structureless coin-flip (F2/F3/F4); −0.70/91%-MaxDD MAGNITUDE = R5 cold-start amplifier, not over-attributed to features.

## No-Cheating Audit — CLEAN
- Ran from earliest UNI data (IS obs 0 = 2022-09-01); 2022-09 listing-shock INCLUDED not trimmed. Runner uses only OOS_CUTOFF_MS + training_months=24 (no start_time/iloc/trim).
- OOS untouched in design; embargo intact.
- Global PRUNED stayed 48; 4 features LOCAL-only.
- EDA scripts committed (b67fdefa) with open_time < OOS_CUTOFF_MS leak assertions.

## Recommendations to QR (process-level)
1. **Adopt LM 7.4 Rec 5a — make GATE-2 PRIMARY (probe ≥ +0.30 on REAL label) a HARD REJECT.** CRV/084 + UNI/085 = two consecutive correct GATE-2-WEAK predictions → NEGATIVE. Zero v1 wins from rescuing a probe-reject. Stop spending ~6.6h on coins the real-label probe already rejects.
2. **Reconcile the dual-DSR reporting** (comparison.csv raw vs dsr.json N_eff-corrected). Both NEGATIVE here so /085 verdict unaffected, but a future BUNDLE where they diverge in sign could create Check-3 ambiguity. Standardize the gate metric.
3. **Do NOT carry the 4 features into /086** (LM 7.4 Rec 5c). Directional pair (39/42) INERT-and-harmful; vol-state pair (3/9) redundant with vol_atr_14/vol_natr_14. Retaining any = Check-13-worthy regression.

## Path Forward (MANDATORY — NEGATIVE-class verdict)
Multi-seed confirmation NOT proposed (standing directive). Prior 5 SPECIALISTs were all per-cohort-specialization cohort-mines on the locked ATR-barrier label + stock stack. /084+/085 lesson: the bottleneck is now the LABEL and ARCHITECTURE, not the symbol. Three axes from families NOT exercised in the prior 5:

1. **Short-horizon fixed-bar reversion LABEL — validated on an ALREADY-STRUCTURED coin first** (*labeling family*). UNI's real lag-3 kernel didn't survive the 1.45×ATR triple-barrier (3-bar reversion completes inside the stop). Replace with sign-of-3-bar-forward-return or ±k-bp barrier at reversion magnitude; run as ISOLATED labeling EXPLORATION on a coin that ALREADY clears the stock probe (DOT/ETH) — validate the label captures a known kernel BEFORE applying to any sub-probe alt. NEW family (no /064-/084 touched the label).

2. **R5 vol-target cold-start primitive — warmup-aware initial sizing** (*risk-primitive family*). 94% of IS-loss magnitude came from full-weight (1.0) sizing in the first ~45 days before R5's vol history accumulates — SYSTEMIC across every new/volatile cohort. Cold-start sizing floor (cap weight_factor at vt_min_scale until ≥N days vol history, or seed vol-target with a cross-symbol prior). NEW risk primitive; de-risks every future fresh-alt mine's early-IS magnitude.

3. **Model-architecture axis — quantile / asymmetric-objective head** (*model-arch family*). All v1 specialists use depth-5 LightGBM directional triple-barrier classification. /085's Optuna trace shows a flat/noisy loss surface (best-trial IS-objective +0.116 vs walk-forward −0.70 = pure overfit gap). A quantile-loss reversion-magnitude head or asymmetric stop-out-tail-penalizing objective on an ALREADY-STRUCTURED coin tests whether the model class is the binding constraint. Untested dimension in the cohort-mine campaign.

OVERALL=SPECIALIST-NEGATIVE
