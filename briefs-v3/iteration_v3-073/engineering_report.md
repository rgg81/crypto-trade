# Engineering Report — iter-v3/073

## Headers

- Iteration: iter-v3/073
- Branch: iteration-v3/073
- Commit SHA (impl + gate fix): `d5d53a0` (fix: update 4 stale assertions for per-symbol ATR axis + label_mode revert)
- Gate SHA (original BLOCK): `da92d0d` (docs: Phase 5.5 gate OVERALL=BLOCK)
- Gate SHA (fixed): `d5d53a0` (gate BLOCK resolved; Phase 6 proceeded after fix)
- Hardware: CPU (WSL2, linux 6.6.114.1)
- Wall-clock time: 0.70h (vs brief estimate 0.6–1.0h — within estimate)

## Configuration Diff vs Baseline (BASELINE_V3.md, /059)

| Parameter | BASELINE_V3.md (/059) | iter-v3/073 | Change |
|---|---|---|---|
| V3_ATR_MULTIPLIERS_PER_SYMBOL | `{}` (empty; global default) | `{"BCHUSDT": (2.0, 1.25), "LDOUSDT": (1.5, 1.25)}` | AXIS VARIABLE |
| DEFAULT_ATR_MULTIPLIERS | `(2.0, 1.0)` | `(2.0, 1.0)` (UNCHANGED; TRX falls back here) | none |
| label_mode | `"triple_barrier"` | `"triple_barrier"` (UNCHANGED; /072 revert applied) | none |
| ITERATION_LABEL | `"v3-071"` | `"v3-073"` | bumped |
| vol_scale_floor_per_symbol | `{"TRXUSDT": 0.5}` | `{"TRXUSDT": 0.5}` (UNCHANGED; cycle-2 baseline state) | none |
| V3_FEATURE_COLUMNS | 14 features | 14 features (UNCHANGED) | none |
| V3_MODELS | BCH, LDO, TRX | BCH, LDO, TRX (UNCHANGED) | none |
| EXPLORATION_ENSEMBLE_SIZE | 3 | 3 (UNCHANGED) | none |
| ENSEMBLE_SEEDS (outer=42 lineage) | [191664963, 1662057957, 1405681631] | [191664963, 1662057957, 1405681631] | none |
| n_trials | 35 | 35 (UNCHANGED) | none |
| label_timeout_minutes | 10080 | 10080 (UNCHANGED) | none |
| compute_embargo_candles | 22 | 22 (UNCHANGED) | none |
| REQUIRED_GAP | 66 | 66 (UNCHANGED) | none |
| Risk gates (7 primitives) | as at /059 | UNCHANGED | none |
| block_long_for / block_short_for | `()` / `()` | `()` / `()` (UNCHANGED) | none |
| enable_per_symbol_drawdown_brake | False | False (UNCHANGED) | none |
| enable_per_symbol_cap | False | False (UNCHANGED) | none |
| enable_regime_gate | False | False (UNCHANGED) | none |

Single-axis discipline: confirmed. The only intentional change vs the /071/072 cycle-2 baseline is `V3_ATR_MULTIPLIERS_PER_SYMBOL` (Edit 1 per brief Section 3.1). The `label_mode="triple_barrier"` (Edit 2) is the mandatory revert of the /072 axis — without it the ATR multipliers would not fire (they only take effect under the triple-barrier path). Total Optuna trials = 35 × 3 symbols × 3 seeds = 315.

## Phase 5.5 Gate Outcome

Original gate (`da92d0d`) = BLOCK (4 hard blocks: stale pre-flight assertion on `V3_ATR_MULTIPLIERS_PER_SYMBOL` count, stale per-symbol ATR loop, stale `label_mode` expected `"fixed_horizon"`, existing test `test_atr_multipliers_for_symbol.py` asserting the pre-/073 default). All 4 resolved at `d5d53a0`. Phase 6 proceeded from `d5d53a0` as the implementation commit.

## Key Metrics Block

### Headline (vs /060 EXPLORATION-mode anchor)

| Metric | /060 (anchor) | /073 | Δ | Ratio |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.8325 | **+0.2779** | **-0.5546** | — |
| OOS monthly Sharpe | +0.1403 | **+1.9025** | **+1.7622** | — |
| IS daily Sharpe | +1.7115 | +0.6080 | -1.1035 | — |
| OOS daily Sharpe | +0.3659 | +3.8067 | +3.4408 | — |
| OOS/IS monthly Sharpe ratio | 0.169 | **6.847** | — | SUSPICIOUS fires (>3.0) |
| OOS/IS daily Sharpe ratio | 0.214 | **6.262** | — | — |
| IS profit_factor | 1.2806 | 1.0891 | -0.191 | — |
| OOS profit_factor | 1.0482 | 1.5912 | +0.509 | — |
| IS win_rate | 31.45% | 34.09% | +2.64pp | — |
| OOS win_rate | 39.22% | 49.06% | +9.84pp | — |
| IS MaxDD | 30.97% | 29.07% | -1.90pp | — |
| OOS MaxDD | 34.53% | **15.79%** | **-18.74pp** | — |
| IS monthly Calmar | — | 0.7059 | — | — |
| OOS monthly Calmar | — | 4.1115 | — | — |
| IS n_trades | 159 | 176 | +17 | — |
| OOS n_trades | 102 | 106 | +4 | — |
| IS total_pnl | — | +20.52 | — | — |
| OOS total_pnl | — | +64.93 | — | — |
| DSR | 0.0 | 0.0 | — | structural at v3 volume |
| DSR_relative_B4 | n/a | **1.0000** | — | PASS |
| PBO | 0.1278 | 0.1541 | +0.026 | — |
| PSR | 0.9763 | 1.0000 | +0.024 | PASS |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | 0.000 | architecture-invariant |
| n_trials | 315 | 315 | 0 | — |
| n_eff | — | 19 | — | — |

### Comparison.csv values (byte-exact from `reports-v3/iteration_v3-073/comparison.csv`)

```
metric,in_sample,out_of_sample,ratio
monthly_sharpe,0.2779,1.9025,6.8468
daily_sharpe,0.6080,3.8067,6.2615
max_drawdown,29.0715,15.7930,0.5432
profit_factor,1.0891,1.5912,1.4610
win_rate,34.0909,49.0566,1.4390
n_trades,176,106,0.6023
total_pnl,20.5203,64.9329,3.1643
monthly_calmar,0.7059,4.1115,5.8248
weighted_pnl_total,20.5203,64.9329,3.1643
dsr,0.000000,—,—
pbo,0.1541,—,—
psr,1.0000,—,—
n_trials,315,—,—
n_effective_trials,19,—,—

# per_symbol,weighted_pnl,n_trades,win_rate,concentration_pct
BCHUSDT,21.9872,37,48.6,33.86
LDOUSDT,18.2273,15,53.3,28.07
TRXUSDT,24.7184,54,48.1,38.07
```

OOS wpnl cross-check: 21.9872 + 18.2273 + 24.7184 = 64.9329 — matches `weighted_pnl_total`. PASS.
IS trade count: BCH 83 + LDO 18 + TRX 75 = 176 — matches `n_trades`. PASS.
OOS trade count: BCH 37 + LDO 15 + TRX 54 = 106 — matches `n_trades`. PASS.

## Classification — SUSPICIOUS-OOS-DOMINANT

Per brief Section 8.4 (disjunctive SUSPICIOUS gate — evaluated first per precedence rules):

**OOS/IS monthly Sharpe ratio = 6.847 > 3.0 — FIRES.**

The ratio 6.847 is the most extreme OOS/IS ratio in v3 history across all EXPLORATION and CONFIRMATION iterations. The pre-registered SUSPICIOUS classifier fires unconditionally on the ratio gate; per Section 8.4 precedence, SUSPICIOUS takes classification precedence over NEGATIVE when both fire concurrently (IS Δ = -0.5546 < -0.10 would independently fire the Section 8.2 NEGATIVE gate, but SUSPICIOUS supersedes NEGATIVE per established /071 precedent).

The SUSPICIOUS-OOS-DOMINANT sub-mode criterion is also met independently: OOS shift ≥ +0.20 (observed +1.7622) AND IS shift < +0.10 (observed -0.5546).

**Classification: SUSPICIOUS-OOS-DOMINANT.** Axis does NOT advance to cycle-2 CONFIRMATION.

## SUSPICIOUS-OOS-DOMINANT Pattern — Third Occurrence in Cycle 2

This is the third consecutive SUSPICIOUS-OOS-DOMINANT result in cycle 2:

| Iteration | Axis | IS Δ | OOS Δ | OOS/IS ratio | Disposition |
|---|---|---:|---:|---:|---|
| /065 | Universal SL widening (2.0→1.5) | -0.28 | +0.71 | 2.87 (below gate) | SUSPICIOUS (OOS-dominant sub-mode); rejected |
| /070 | CONFIRMATION of /065 bundle | -0.97 | — | — | IS collapsed worse at multi-seed; full REJECT |
| /071 | Meta-labeling | -0.12 | +0.63 | 4.51 | SUSPICIOUS-OOS-DOMINANT; FAILS ratio gate |
| **/073** | **Per-symbol barrier asymmetry** | **-0.55** | **+1.76** | **6.85** | **SUSPICIOUS-OOS-DOMINANT; most extreme ratio** |

The common mechanism across /065, /071, and /073: any axis that widens the SL or filters the trade roster — making individual trades survive longer before stopping out — produces an IS-collapse + OOS-soar pattern. The IS window (2022-09 through 2025-03) contains the 2022 bear market, 2023 chop, and 2024-Q4/2025-Q1 deceleration, where wider SL trades bleed longer. The OOS window (2025-03 through 2026-05) contains a persistent uptrend on BCH/TRX/LDO that rewards wider barriers. The structural IS/OOS regime difference — rather than a genuine edge — is generating the apparent OOS improvement.

The /065→/070 precedent is the controlling evidence. At single-seed EXPLORATION, /065's SL widening showed OOS Δ +0.71, IS Δ -0.28. At multi-seed CONFIRMATION, the IS collapse worsened to -0.97 (the frozen-baseline artifact dissolved and the underlying IS weakness became fully visible). There is strong prior evidence that /073's multi-seed CONFIRMATION would follow the same trajectory.

## The LDO OOS-Positive Result — Genuine Fix or Regime Artifact?

LDO OOS wpnl at /073 = +18.23 (53.3% WR, 15 trades). This is the FIRST positive LDO OOS result across all of cycle 1 and cycle 2. The /060 anchor had LDO OOS at -25.08 wpnl (18.2% WR, 11 trades).

However, the IS picture tells the opposite story:

| Window | /060 LDO | /073 LDO | Δ |
|---|---|---|---|
| IS net_pnl | -11.44% | -9.997% | +1.4pp (slight improve) |
| IS win_rate | 27.3% | 44.4% | +17.1pp |
| IS n_trades | 11 | 18 | +7 |

LDO IS WR improved substantially (27.3% → 44.4%, +17.1pp). IS net_pnl improved marginally. These are positive IS signals for LDO specifically. But the IS HEADLINE collapsed to +0.28 because BCH and TRX IS deteriorated severely (see IS collapse forensic below). LDO IS improvement was offset by BCH IS and TRX IS regression.

Is the LDO OOS-positive result a genuine edge? Two competing explanations:

1. **Genuine fix hypothesis**: the LDO (1.5, 1.25) multiplier corrects the 69% SL-saturation pathology (EDA Section 2.2). The shorter TP (1.5× vs 2.0×) means LDO LONG trades reach TP more often (per EDA Section 2.3: `exec_consistency` 0.65→0.90 IS). The IS WR improvement (+17.1pp) supports this — the model is learning a better-calibrated LDO signal, consistent with the EDA's IS-only prediction.

2. **Regime exposure hypothesis**: the OOS period happens to favor LDO LONG trades with a wider SL (OOS is a bull period for many alts). The IS LDO improvement (+1.4pp net_pnl) is too small to distinguish genuine signal from the regime effect; the OOS surge (+18.23 wpnl from -25.08) is disproportionately large relative to any IS signal.

The 6.85 OOS/IS headline ratio is not attributable solely to LDO — BCH OOS +21.99 and TRX OOS +24.72 both outperform their IS counterparts heavily (BCH IS +74.97% IS net_pnl but TRX IS is -23.04%). The OOS/IS inflation is portfolio-wide, consistent with the regime-exposure hypothesis being the dominant factor.

The /065→/070 precedent is directly applicable to LDO as well: at single-seed EXPLORATION, /065 showed a similar (though less extreme) OOS surge, but the underlying IS weakness was regime-masked at single seed and fully visible at multi-seed. The LDO OOS-positive result is more likely regime exposure than a genuine LDO edge.

QR Phase 8 should adjudicate this question. The engineering report cannot resolve it — both mechanisms are consistent with the observed numbers.

## IS Collapse Forensic

IS monthly Sharpe collapsed from +0.8325 (/060) to +0.2779 (/073), a Δ of -0.5546. IS profit_factor = 1.0891 (barely break-even). The IS window is clearly adverse for the /073 configuration.

### Per-symbol IS decomposition

| Symbol | /060 IS trades | /073 IS trades | /060 IS WR | /073 IS WR | /060 IS net_pnl | /073 IS net_pnl | Δ net_pnl |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCH | 73 | 83 | 45.2% | 50.6% | +79.45% | +74.97% | -4.5pp |
| LDO | 11 | 18 | 27.3% | 44.4% | -11.44% | -9.997% | +1.4pp |
| TRX | 75 | 75 | 29.3% | 29.3% | -23.04% | -23.04% | 0pp |

IS net_pnl cross-check: +74.97 + (-9.997) + (-23.04) = +41.93pp. This does not directly reconcile to the IS Sharpe because Sharpe accounts for volatility across the monthly series, not cumulative pnl. The headline IS Sharpe collapse (-0.55) is driven by the monthly volatility pattern and the low IS PF (1.09).

Key observation: TRX IS is IDENTICAL between /060 and /073 (75 trades, 29.3% WR, -23.04% net_pnl) — TRX uses DEFAULT_ATR_MULTIPLIERS `(2.0, 1.0)` (unchanged), confirming the axis is wired correctly. The per-symbol ATR dict change for BCH and LDO did not contaminate TRX's trade roster.

The IS Sharpe collapse from +0.8325 to +0.2779 is not dominated by a single symbol catastrophic failure (unlike /072 where LDO OOS -32.49 dominated). BCH IS improved slightly (WR +5.4pp, net_pnl -4.5pp — likely a different monthly distribution). The IS Sharpe collapse reflects the monthly PnL volatility structure: IS monthly_pnl.csv shows 35 IS months with a mix of positive and negative months; the 2024-Q1 cluster (Jan +29.05, Feb -2.40, Mar -7.28, Apr -11.92) is the dominant IS volatility driver in both /060 and /073.

The IS PF of 1.09 (vs /060's IS PF from comparison.csv at approximately 1.28) means the wider SL on BCH+LDO lets losses run deeper in the adverse IS regime even when overall trade count and WR improve. The EDA predicted this: BCH's chosen cell still has SL-hit > TP-hit (57% vs 34% per brief Section 7 failure-mode analysis), and widening the SL from 1.0× to 1.25× means each of the majority-losing BCH trades books a deeper loss.

## Behavioral-Effect Audit (Section 4.5 confirmation)

Brief Section 4.5 predicted IS trade count change of +10 to +35 and OOS change of +5 to +25. Observed:

| Window | /060 trades | /073 trades | Delta | Within predicted band? |
|---|---:|---:|---:|---|
| IS total | 159 | 176 | +17 | YES (+17 within [+10, +35]) |
| OOS total | 102 | 106 | +4 | NEAR-MISS (+4 vs predicted [+5, +25]; 1 trade below lower bound) |

IS saturation falsifier: total IS delta = +17, per-symbol deltas — BCH +10 (> ±3), LDO +7 (> ±3), TRX 0 (as expected — unchanged multiplier). The axis moved the trade roster; saturation falsifier does NOT fire.

## Section 4.4/4.6 Falsifier Check (per brief)

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe shift | ≥ -0.10 (NEGATIVE floor) | -0.5546 | FAILS — IS regression |
| OOS Sharpe shift | ≥ +0.20 (PROMISING floor) | +1.7622 | EXCEEDS — far above PROMISING |
| OOS/IS monthly Sharpe ratio | ≤ 3.0 | **6.847** | **FIRES — SUSPICIOUS gate** |
| frac_positive_paths | ≥ 0.50 | 0.6444 | PASS |
| DSR_relative_B4 | ≥ 0.95 | 1.0000 | PASS |
| PSR | ≥ 0.95 | 1.0000 | PASS |
| BCH IS share ≥ 80% one-sided | IS share flag | BCH IS = 178.8% (concentration artifact) | Within expected range |
| BCH OOS wpnl | ≥ -15 (pre-registered; not collapse) | +21.99 | PASS |
| LDO OOS wpnl | ≥ -35 (pre-registered) | +18.23 | PASS |
| TRX OOS wpnl shift | < ±15 (cross-symbol contamination check) | +24.72 vs /060's +30.76 (Δ -6.0) | PASS (within ±15) |

Pre-registered PROMISING conditions: IS ≥ +0.9325 AND OOS ≥ +0.3403. Observed IS = +0.2779 (below +0.9325) and OOS = +1.9025 (above +0.3403). IS gate FAILS; PROMISING does not fire. SUSPICIOUS fires via ratio gate (Section 8.4). SUSPICIOUS takes classification precedence.

## CPCV / PBO / PSR Summary

| Metric | Value | Gate | Status |
|---|---|---|---|
| frac_positive_paths | 0.6444 | ≥ 0.55 | PASS |
| PBO | 0.1541 | — | informational |
| PSR | 1.0000 | ≥ 0.95 | PASS |
| DSR_relative_B4 | 1.0000 | ≥ 0.95 | PASS |
| CPCV path Sharpe q25 | -0.243 | — | — |
| CPCV path Sharpe q50 | +0.335 | — | — |
| CPCV path Sharpe q75 | +0.838 | — | — |
| n_eff | 19 | — | — |

CPCV paths: 45 paths, 29 positive = 64.4% positive (consistent with frac_positive_paths = 0.6444). The CPCV distribution is right-skewed: q25 = -0.243, q50 = +0.335, q75 = +0.838. The high PSR=1.000 and DSR_relative_B4=1.000 are driven by the extreme OOS Sharpe (+1.9025 monthly) against a low n_trials benchmark (315 trials, n_eff=19). These do NOT contradict the SUSPICIOUS classification — PSR/DSR measure whether the observed Sharpe is significant given the trial count, not whether the OOS/IS divergence is a regime artifact. The two concerns are orthogonal.

## Per-Symbol OOS — All Three Positive (First Time in Cycle 1+2)

| Symbol | OOS wpnl | OOS trades | OOS WR | OOS concentration |
|---|---:|---:|---:|---:|
| BCH | +21.99 | 37 | 48.6% | 33.86% |
| LDO | +18.23 | 15 | 53.3% | 28.07% |
| TRX | +24.72 | 54 | 48.1% | 38.07% |

This is the first iteration in cycle 1 and cycle 2 where ALL three symbols post positive OOS weighted PnL. LDO going from -25.08 (/060 raw OOS wpnl) to +14.14 (LDO IS `net_pnl_pct` from `out_of_sample/per_symbol.csv` = +14.1359%) is the most notable per-symbol move. No symbol exceeds the 40% concentration flag.

## Feature Importance

Portfolio-level importance (last month, IS, from `model_importance_last_month_portfolio.csv`):

| Rank | Feature | Importance |
|---|---|---:|
| 1 | max_dd_window_50 | 747.7 |
| 2 | ret_skew_200 | 690.3 |
| 3 | ema_spread_atr_20 | 687.0 |
| 4 | range_realized_vol_50 | 608.7 |
| 5 | vwap_dev_20 | 596.0 |
| 6 | ret_autocorr_lag1_50 | 534.0 |
| 7 | ret_kurt_50 | 518.7 |
| 8 | ret_kurt_200 | 507.7 |
| 9 | hurst_100 | 493.0 |
| 10 | regime_momentum_signed_5d | 449.3 |
| 11 | ret_skew_50 | 449.0 |
| 12 | hurst_diff_100_50 | 436.7 |
| 13 | sym_vs_btc_ret_7d | 435.3 |
| 14 | btc_ret_14d | 398.0 |

All 14 features have non-zero importance. No feature is INERT. The importance distribution is reasonable (top feature 747.7 vs min 398.0; ratio ~1.88, well within healthy bounds). The axis change is a label-geometry change — importance rankings may shift as different training labels are applied, but no feature was added or removed.

IC matrix note: highest off-diagonal IC pairs are `vwap_dev_20` vs `regime_momentum_signed_5d` = 0.764 and `sym_vs_btc_ret_7d` vs `regime_momentum_signed_5d` = 0.619. These are the same high-IC pairs observed in prior iterations; the composed feature `regime_momentum_signed_5d` = ret_5d × sign(hurst_100 - 0.5) mechanically correlates with its constituent primitives. No new high-IC pairs introduced by the /073 axis change.

## IS Monthly PnL — Zero-Trade Month Check

IS monthly_pnl.csv: 35 months (2022-02 through 2025-03). Zero zero-trade months (minimum per month = 1 trade). PASS.

## Label Leakage Audit

Walk-forward embargo = 22 candles (`compute_embargo_candles(10080, 480)`). Triple-barrier label timeout = 10080 minutes = 21 candles. The 22-candle embargo strictly covers the 21-candle label horizon for all three symbols. `REQUIRED_GAP = (21+1) × 3 = 66`. No label leakage risk. The per-symbol ATR multiplier change is a label GEOMETRY change (barrier widths), not a label HORIZON change; it does not affect the embargo calculation. PASS.

## Ensemble Configuration

`ensemble_summary.json` confirms: mode=`exploration`, ensemble_size=3, seeds `[191664963, 1662057957, 1405681631]` (outer=42 lineage), matching the brief's specified run mode. n_trials = 315 = 35 × 3 symbols × 3 seeds. PASS.

## Seed Concentration Audit

EXPLORATION mode: 3 seeds (ensemble_size=3), single outer run. Multi-seed dispersion audit applies at CONFIRMATION-mode only. Trade roster and metrics above are from the single 3-seed EXPLORATION pass. The frozen-baseline pattern (`feedback_v3_single_seed_frozen_baseline.md`) is noted: TRX IS is byte-identical to /060 TRX IS (75 trades, 29.3% WR, -23.04% net_pnl) because TRX's multipliers are unchanged. BCH and LDO IS trade rosters changed materially (+10 and +7 trades respectively), confirming the axis fired correctly on the targeted symbols.

## Gate Efficacy Table

All 7 risk primitives are UNCHANGED from /060 (no primitive threshold changes; regime gate DISABLED; per-symbol cap DISABLED; per-symbol drawdown brake DISABLED; block_long_for/block_short_for both empty). Per-primitive fire rates are not separately tabulated here — the axis is a labeling-geometry change that retrains models under different label targets; fire rates shift with model confidence outputs but gate configurations are unchanged.

`per_regime.csv` summary: IS window — regime "unknown" (176 trades, 40.9% WR, +41.93% net_pnl); OOS window — regime "unknown" (106 trades, 49.1% WR — inferred from WR 49.0566 in comparison.csv). The Hurst regime gate is ACTIVE but all trades are classified as "unknown" regime, consistent with prior iterations where the classifier defaults to "unknown" in EXPLORATION mode without the formal regime gate enabled.

## Anomaly Notes

1. OOS MaxDD = 15.79% vs IS MaxDD = 29.07%. An OOS MaxDD substantially LOWER than IS MaxDD is the mirror image of the usual overfitting concern and is expected in a SUSPICIOUS-OOS-DOMINANT regime-exposure pattern: the OOS bull period produces a smooth upward equity curve with shallow drawdowns.

2. OOS monthly_pnl.csv: 2025-10 is the worst OOS month at -13.84% (13 trades). All other OOS months range from -3.12% to +21.87%. No single month dominates the OOS result.

3. IS win_rate improved from /060's 31.45% to 34.09% (+2.64pp) despite IS Sharpe collapsing -0.55. This is consistent with the wider-SL mechanism: more trades survive to hit TP (higher WR) but the stops that do fire are deeper (lower PF = 1.09). The WR improvement does not compensate for the PF deterioration.

4. Trade spot-check: OOS trades.csv has 106 rows. Per-symbol sum (37+15+54=106) matches. No NaN PnL fields, no obvious entry/exit math anomalies. IS per_symbol.csv cross-check: 83+18+75=176 (matches IS n_trades). Cross-checks PASS.

## Methodological Significance — 3 Consecutive SUSPICIOUS-OOS-DOMINANT

Three consecutive SUSPICIOUS-OOS-DOMINANT results (/065, /071, /073) with escalating OOS/IS ratios (2.87, 4.51, 6.85) constitute a finding beyond any individual iteration. The pattern indicates v3's IS and OOS regimes are structurally different:

- IS (2022-09 through 2025-03): bear + recovery + 2024 bull + 2024-Q4/2025-Q1 chop. SL-widening axes bleed in the chop/bear phases.
- OOS (2025-03 through 2026-05): persistent uptrend on BCH/LDO/TRX. Wider SL lets winners run during this period.

Any axis that extends trade holding time (wider SL, meta-labeling that filters to fewer/higher-confidence trades, per-symbol asymmetry that reduces SL saturation) will mechanically reward the OOS regime and penalize the IS regime. This is regime exposure, not signal discovery.

This 3-consecutive-SUSPICIOUS-OOS-DOMINANT finding is a research-level signal that the QR Phase 8 should address. Possible diagnostic directions: (a) regime-stratified IS analysis (how does the axis perform in the IS bull sub-period 2024-01 through 2025-03 vs the IS bear/chop sub-period 2022-09 through 2023-12?); (b) whether a regime-conditional mechanism could apply the wider SL only in trending IS months; (c) whether the v3 14-feature set has a systematic trend/momentum bias that amplifies this IS/OOS regime split. These are QR domain questions — not recommendations, observations for Phase 8 diary.

## Recommendations to QR (informational — QR Phase 8 domain)

The engineering report does not make QR decisions. The following are observations for QR adjudication:

1. SUSPICIOUS-OOS-DOMINANT classification is correct per the pre-registered Section 8.4 gate. The axis does NOT auto-advance to cycle-2 CONFIRMATION.

2. The /065→/070 precedent (SUSPICIOUS-OOS-DOMINANT at single-seed EXPLORATION → IS collapse worsened at multi-seed CONFIRMATION) is the strongest prior evidence against advancing /073 to CONFIRMATION despite the LDO OOS-positive result.

3. The LDO OOS-positive result (+18.23 wpnl at 53.3% WR, 15 trades) is the first positive LDO OOS in v3 history. The LDO IS WR improved substantially (+17.1pp). Whether this reflects a genuine label correction or regime exposure is the key QR Phase 8 question.

4. The 3-consecutive-SUSPICIOUS-OOS-DOMINANT pattern (/065, /071, /073) with escalating ratios (2.87, 4.51, 6.85) is itself a finding that warrants diary documentation. The QR's cycle-2 EXPLORATION agenda should evaluate whether a dedicated IS/OOS regime-diagnostic axis is warranted.

5. Cycle 2 #4 (/074): axis selection is QR domain per `feedback_v3_axis_selection_quant_discipline.md`. The next axis should address the structural IS/OOS regime gap rather than continuing to test holding-time extension mechanisms.

## Critic Alert

The Critic should adjudicate:

(a) Whether the SUSPICIOUS-OOS-DOMINANT classification under Section 8.4 is correctly applied — specifically whether the OOS/IS ratio 6.847 unambiguously fires the >3.0 gate and whether the SUSPICIOUS precedence over NEGATIVE (Section 8.4 last paragraph) is correctly applied.

(b) Whether the per-symbol barrier asymmetry (/073) is meaningfully different from the rejected /065 universal SL widening as an axis family, or whether both belong to the same "SL extension" family that the /070 CONFIRMATION evidence has already closed.

(c) Whether the LDO OOS-positive result (+18.23 wpnl, 53.3% WR) constitutes sufficient evidence of a genuine signal to warrant any classification nuance (e.g., a NEGATIVE-IS sub-classification noting the LDO component), or whether the 6.85 ratio fully subsumes it into regime exposure.

(d) The methodological significance of 3 consecutive SUSPICIOUS-OOS-DOMINANT results — whether this warrants a pre-registered cycle-level finding in the exploration catalog (`briefs-v3/exploration_catalog.md`) beyond the per-iteration diary entry.

## Classification

**SUSPICIOUS-OOS-DOMINANT**

OOS/IS monthly Sharpe ratio = 6.847 > 3.0 — fires the pre-registered Section 8.4 gate. SUSPICIOUS takes classification precedence over NEGATIVE (IS Δ -0.5546 < -0.10 fires Section 8.2 NEGATIVE independently, but SUSPICIOUS supersedes per Section 8.4 precedence rules established at /071). The axis is regime-exposed and NOT eligible to advance to cycle-2 CONFIRMATION as an edge ingredient.

This is the THIRD consecutive SUSPICIOUS-OOS-DOMINANT in cycle 2 (/065, /071, /073) and the most extreme OOS/IS ratio in v3 history.

## Status

OVERALL=READY-FOR-CRITIC
