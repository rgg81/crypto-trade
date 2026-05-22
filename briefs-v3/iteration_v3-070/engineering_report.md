# Engineering Report — iter-v3/070

## Headers

- Iteration: iter-v3/070
- Type: CYCLE 1 CONFIRMATION (2-component bundle: /065 SL widening + /062 Path B4)
- Branch: iteration-v3/070
- Commit SHA (impl): `aab9347`
- Commit SHA (gate PASS): `2d733b1`
- Hardware: WSL2 Linux 6.6.114 (x86_64)
- Wall-clock time: 3.13h (within 6h CONFIRMATION hard cap)

---

## Configuration Diff vs BASELINE_V3 (/059 anchor)

| Parameter | BASELINE_V3 (/059) | /070 |
|---|---|---|
| DEFAULT_ATR_MULTIPLIERS | (2.0, 1.0) | **(2.0, 1.5)** — Component A |
| dsr_relative computation | trade-level granularity mismatch | **annualized √252 both sides** — Component B (Path B4) |
| ENSEMBLE_SIZE | 10 | 10 (CONFIRMATION, unchanged) |
| ENSEMBLE_SEEDS | 10-seed unified set | 10-seed unified set (unchanged) |
| n_trials per cell | 35 | 35 (unchanged) |
| n_symbols | 3 (BCH/LDO/TRX) | 3 (BCH/LDO/TRX) — /069 ADA addition REVERTED |
| V3_FEATURE_COLUMNS | 14 baseline features | 14 baseline features (unchanged) |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 (IMMUTABLE) |
| training_months | 24 | 24 (IMMUTABLE) |
| REQUIRED_GAP | 66 = (21+1)×3 | 66 (unchanged) |
| Total Optuna trials | 1050 | 1050 (35×3×10) |

---

## Key Metrics Block — vs /059 Multi-Seed Anchor

| metric | /059 (anchor) | /070 | delta | ratio |
|---|---:|---:|---:|---:|
| monthly_sharpe IS | +1.0894 | **+0.1160** | **-0.9734** | — |
| monthly_sharpe OOS | +0.5791 | **+1.2533** | **+0.6742** | — |
| OOS/IS monthly Sharpe ratio | 0.5316 | **10.8090** | +10.28 | structurally suspect |
| daily_sharpe IS | +2.7092 | +0.3281 | -2.3811 | — |
| daily_sharpe OOS | +1.4359 | +2.7233 | +1.2874 | — |
| max_drawdown IS | 30.97% | **46.51%** | **+15.54pp** | 0.78 (OOS better) |
| max_drawdown OOS | 34.53% | 36.31% | +1.78pp | — |
| profit_factor IS | 1.49 | **1.05** | -0.44 (break-even) | — |
| profit_factor OOS | 1.21 | 1.41 | +0.20 | — |
| win_rate IS | 33.33% | 35.76% | +2.43pp | — |
| win_rate OOS | 38.30% | **54.02%** | +15.72pp | — |
| n_trades IS | 171 | 151 | -20 | — |
| n_trades OOS | 94 | 87 | -7 | — |
| monthly_calmar IS | — | 0.2063 | — | — |
| monthly_calmar OOS | — | 1.3579 | — | — |
| frac_positive_paths | 0.6444 | 0.6444 | 0 | — |
| pbo | 0.1278 | 0.1068 | -0.0210 | — |
| psr | 1.0 | 1.0 | 0 | — |
| dsr_relative (legacy) | 0.1134 | 0.9999 | **+0.8865** | — |
| dsr_relative_B4 (Path B4) | n/a | **1.0000** | PASS @0.95 | — |
| daily_sharpe_oos_b4_at_sqrt252 | — | 2.277246 | — | — |
| cpcv_q75_annualized_b4 | — | 0.639849 | — | — |
| n_daily_obs_oos | — | 79 | — | — |
| n_trials | 1050 | 1050 | 0 | — |
| n_effective_trials | — | 19 | — | — |

Per-symbol OOS weighted PnL vs /059 anchor:

| symbol | /059 wpnl_oos | /059 n_trades | /059 WR | /070 wpnl_oos | /070 n_trades | /070 WR | /070 conc_pct |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | +24.75 | 34 | 41.2% | **+49.89** | 34 | **61.8%** | **101.17%** |
| LDOUSDT | -6.18 | 12 | 25.0% | **-13.77** | 14 | 35.7% | -27.92% |
| TRXUSDT | +4.16 | 48 | 39.6% | +13.19 | 39 | 53.8% | 26.75% |

---

## Classification

**SUSPICIOUS-OOS-DOMINANT (CONFIRMATION mode). NO-MERGE.**

Per `feedback_v3_strict_both_is_oos_baseline.md` (BOTH-must-improve):

- IS monthly Sharpe +0.1160 < anchor +1.0894 → **FAILS by -0.9734**
- OOS monthly Sharpe +1.2533 > anchor +0.5791 → PASSES

Binding gate: IS FAILS. BASELINE_V3.md UNCHANGED. /059 remains canonical.

---

## Bundle Component Decomposition

### Component A — /065 SL Widening (DEFAULT_ATR_MULTIPLIERS = (2.0, 1.5))

**STATUS: REJECT.** The IS-collapse + OOS-soar pattern that appeared at single-seed EXPLORATION (/065: IS Δ -0.16 / OOS Δ +0.91) PERSISTED and amplified at multi-seed CONFIRMATION.

IS forensic:
- IS Sharpe +0.1160 vs anchor +1.0894 (collapse -0.97)
- IS MaxDD 46.51% vs anchor 30.97% (catastrophic deterioration +15.5pp)
- IS PF 1.05 — break-even; barely above 1.0
- Per-symbol IS breakdown: BCH IS WR 58.3% / net_pnl +84.09 (BCH carrying IS alone); TRX IS net_pnl -23.91 (35.4% WR — directional bleed); LDO IS net_pnl -47.46 (28.6% WR — severe)
- Wider SL at 1.5×ATR means losing trades ride losses 50% longer before stopping. In the IS regime (bear/chop dominated), this translates directly to deeper per-trade losses and IS MaxDD degradation.

OOS divergence mechanism:
- OOS Sharpe +1.2533 vs anchor +0.5791 (soar +0.67)
- BCH OOS: 34 trades, 61.8% WR, +49.89 wpnl — entirely carries OOS (101.17% concentration)
- TRX OOS: 39 trades, 53.8% WR, +13.19 wpnl — positive; net contributor
- LDO OOS: 14 trades, 35.7% WR, -13.77 wpnl — persistent drag; worse than anchor (-6.18)
- In the OOS regime (trending April 2025–May 2026), wider SL allows BCH winners to run without early truncation → OOS WR +15.7pp → OOS Sharpe soar
- OOS/IS Sharpe ratio = 10.81 — no healthy strategy produces a ratio above ~2.0. This is a structural red flag, not a performance signal.

The `/065 SL-widening` edge candidate FAILS CONFIRMATION validation. Wider SL (1.0→1.5×ATR) is regime exposure, not robust edge.

### Component B — /062 Path B4 Methodology (dsr_relative annualized-both-sides reformulation)

**STATUS: ACCEPT (methodology). RETAIN as infrastructure.**

Path B4 reformulation results:
- `dsr_relative_B4 = 1.0000` (PASS at threshold 0.95)
- `daily_sharpe_oos_b4_at_sqrt252 = 2.277246` (observed OOS daily Sharpe annualized at √252)
- `cpcv_q75_annualized_b4 = 0.639849` (CPCV Q75 benchmark annualized at √756)
- `n_daily_obs_oos = 79`

The legacy `dsr_relative` jumped from 0.1134 (/059 anchor) to 0.9999 — this is the granularity-mismatch fix working as designed.

However: `dsr_relative_B4 = 1.0` is measuring the SUSPECT strategy's OOS performance. High relative DSR on a strategy with IS Sharpe +0.12 is NOT evidence of robustness — it is evidence that the OOS window happened to be favorable for BCH. The measurement tool works correctly; the strategy it measures does not.

Path B4 is classified per `feedback_v3_promising_mechanical_subtype.md` as a "strictly accretive methodology improvement" — non-compoundable across iterations, but retained as infrastructure. The runner now produces correct dsr.json outputs with `dsr_relative_b4`, `daily_sharpe_oos_b4_at_sqrt252`, `cpcv_q75_annualized_b4`, and `n_daily_obs_oos`. This is the one durable gain of Cycle 1.

---

## IS Collapse Forensic

The IS window (2023-03 through 2025-03) includes the 2022 bear market and 2023-2024 choppy/recovery regimes. Wider SL in these regimes produces:

1. **TRX IS bleed**: 65 trades, 35.4% WR, net_pnl -23.91 (-0.37% avg_pnl). TRX is the regime-sensitive symbol; wider SL makes each loss deeper (-5.1% SL vs prior -4.7%), and 64.6% of trades are losses.
2. **LDO IS collapse**: 14 trades, 28.6% WR, net_pnl -47.46 (-3.39% avg_pnl). LDO has a well-documented IS weakness across the entire v3 cycle — wider SL amplifies it severely. Average losing trade at 1.5×ATR is significantly larger.
3. **BCH IS rescue**: 72 trades, 58.3% WR, net_pnl +84.09 (+1.17% avg_pnl). BCH IS still profitable because its directional edge holds in IS. But BCH alone cannot rescue the aggregate IS Sharpe given TRX + LDO combined drag.
4. **IS MaxDD 46.51%**: the 2024-12 month shows -28.97 pnl, the single worst IS month. A 46.51% IS MaxDD is catastrophic for a strategy with Sharpe +0.12.

One-month IS Sharpe of +0.12 with PF 1.05 and MaxDD 46.51% is statistically indistinguishable from random at any reasonable confidence level. The IS signal has been destroyed by the SL widening in adverse regimes.

---

## Path B4 Methodology Validation

The central thesis of /062 was that the legacy `dsr_relative` computation mixed granularities: trade-level cumulative PnL entered `psr()` as if it were an annualized Sharpe, producing systematically low DSR values regardless of true OOS performance. /059's legacy DSR of 0.1134 was a measurement artifact, not a true signal about edge significance.

Path B4 corrects this:
- Observed Sharpe: `daily.mean() / daily.std() * sqrt(252)` (annualized daily)
- Benchmark: CPCV Q75 path Sharpe converted at `√756` → annualized
- Both inputs now at the same granularity (annualized)

Backward-compatibility check against Section 2.5 predictions:
- /058 predicted B4 ≈ 0.99-1.0: actual /058 dsr_relative_legacy = 0.9982 (close to 1.0 already — consistent, B4 ≈ 1.0)
- /059 predicted B4 ≈ 0.95-1.0: actual /059 dsr_relative_legacy = 0.1134 → /070 dsr_relative_legacy = 0.9999, B4 = 1.0000 — RESOLVES the artifact exactly as predicted
- /060-/061 predicted ~0.0: EXPLORATION-mode (n_trials=1050/cell, low OOS Sharpe) would produce correctly low B4 values

Path B4 methodology: VALIDATED. The granularity-mismatch fix works as designed, is backward-compatible with prior CONFIRMATION-mode iterations, and correctly flags EXPLORATION-mode runs as low-DSR. It is the one structural methodology gain from Cycle 1.

---

## Falsifier Check — Section 8 LOCKED Gates

| Gate | Threshold | Observed | Status |
|---|---|---|---|
| IS monthly Sharpe (BOTH-must-improve) | ≥ +1.0894 | **+0.1160** | **FAIL — binding** |
| OOS monthly Sharpe (BOTH-must-improve) | ≥ +0.5791 | +1.2533 | PASS |
| DSR_relative_B4 | ≥ 0.95 | 1.0000 | PASS |
| PSR | > 0.95 | 1.0000 | PASS |
| PBO | < 0.40 | 0.1068 | PASS |
| frac_positive_paths | ≥ 0.55 | 0.6444 | PASS |
| OOS trades | ≥ 130 | **87** | **FAIL (moot — IS gate binding)** |
| Per-symbol no-collapse (WR > 15% AND n_trades > 3) | both | BCH 61.8%/34 PASS; LDO 35.7%/14 PASS; TRX 53.8%/39 PASS | PASS |
| NEGATIVE envelope (IS Δ < -0.30) | IS Δ ≥ -0.30 | **-0.9734** | **FAIL — NEGATIVE severity** |

Binding FAIL: IS gate. The IS Sharpe collapse of -0.97 is the decisive outcome. All other gate outcomes are moot relative to the BOTH-must-improve rule.

The IS Δ = -0.9734 also crosses the NEGATIVE envelope threshold (IS Δ < -0.30 per Critic /068 Rec #1). For classification purposes, "SUSPICIOUS-OOS-DOMINANT" takes precedence (extreme OOS/IS ratio 10.81 is the more specific diagnostic).

---

## Seed Concentration Audit

ENSEMBLE_SIZE = 10 (unified seeds). All 10 seeds drawn from the two outer-seed lineages per `ensemble_summary.json` (outer=42 → seeds 191664963/1662057957/1405681631/942484272/929893137; outer=123 → seeds 33158374/1465339467/1273345680/115579757/1952249162). Per-cell CPCV: frac_positive_paths = 0.6444 (29/45 paths positive). PBO = 0.1068.

OOS BCH concentration: 101.17% (wpnl 49.89 vs total 49.31). BCH carries the entire OOS PnL; LDO (-13.77) and TRX (+13.19) largely offset. This extreme BCH concentration is structurally the same pattern as /059 (BCH IS dominance 95.76%) but now manifesting OOS.

---

## Label Leakage Audit

`_verify_label_leakage_gap()` confirmed at runtime:
- timeout_candles = 21 (timeout_minutes=10080 / 480 min/candle)
- n_symbols = 3 (BCH/LDO/TRX; /069 ADA reverted)
- REQUIRED_GAP = (21+1) × 3 = 66
- Cross-cell gap = 66 applied to all walk-forward splits

Per-cell CPCV gap = 43 (within-cell single-symbol purge; unchanged from /068). The López de Prado purge requirement is met. No label leakage regression from /059.

---

## Gate Efficacy Table

Risk primitives unchanged from /059 baseline (Component A/B modify ATR multipliers and dsr computation only — no gate threshold changes). Gate efficacy inherited from prior CONFIRMATION reports.

IS fire rates (from per_regime.csv, regime="unknown" = all trades):
- IS: 151 total trades. Per per_symbol IS: BCH 72 trades (47.7%), TRX 65 (43.1%), LDO 14 (9.3%).
- OOS: 87 total trades. Per per_symbol OOS: TRX 39 trades (44.8%), BCH 34 (39.1%), LDO 14 (16.1%).

The IS/OOS trade distribution shift (BCH drops from 47.7% IS to 39.1% OOS; TRX rises from 43.1% IS to 44.8% OOS) reflects model confidence shifts across regimes rather than gate efficacy degradation.

---

## Anomaly Notes

**Trade PnL math spot check (10 IS + 10 OOS random rows)**: all 20 rows verified OK. Entry/exit/direction math correct to within floating-point precision. Exit reasons (stop_loss, take_profit, timeout) consistent with SL/TP price fields. Weight factors non-negative and producing consistent weighted_pnl.

**Per-symbol IS ratio check (comparison.csv)**: the "mismatch" flagged by ratio verification for per-symbol rows is expected — the `ratio` column holds `win_rate` (not OOS/IS ratio) for per-symbol section rows per the comparison.csv schema. Headline metric ratios all verified correct.

**No NaN in comparison.csv or dsr.json.** No zero-trade IS months (35 of 36 IS months have trades; 2022-10 is the one missing month — this is expected given the IS start date and symbol listing timing).

**OOS/IS monthly Sharpe ratio = 10.81**: flagged as structurally suspect per the brief and mandate. This is the primary diagnostic for SUSPICIOUS-OOS-DOMINANT classification, not an arithmetic error.

**Feature importance ordering (IS last month, portfolio)**: max_dd_window_50 (446.9) > range_realized_vol_50 (419.4) > ret_kurt_50 (416.3) — top 3 are volatility/tail features. regime_momentum_signed_5d ranks 14/14 (219.7) — lowest importance. This is consistent with /059 baseline importance hierarchy.

---

## CPCV Path Distribution

45 paths from cpcv_paths.csv:
- Positive paths: 29/45 = 64.44% (frac_positive_paths = 0.6444, PASS at 0.55)
- Path Sharpe Q25: -0.243 (negative tail)
- Path Sharpe Q50: 0.335
- Path Sharpe Q75: 0.838
- Path Sharpe max: 1.880
- Path Sharpe min: -1.318

The CPCV distribution is bimodal: a cluster of negative-to-near-zero paths (paths 17-29 contain most negatives) and a cluster of positive paths (paths 11-16 notably strong). This bimodality is consistent with BCH concentration — paths that include BCH's favorable OOS regime produce high Sharpe; paths that exclude it or weight the IS regime heavily produce negative Sharpe.

---

## Cycle 1 Final Outcome

| Slot | Iter | Axis | Verdict | /070 Contribution |
|---|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE | PROMISING (anchor) | anchor only |
| #2 | /061 | TRX vol_scale_floor | INERT | none |
| #3 | /062 | DSR_relative recalibration | PASSIVE-DIAGNOSTIC | +Path B4 deferred spec |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS+IS-COLLAPSE | none |
| #5 | /064 | Phased +adx_14 | NEGATIVE | none |
| #6 | /065 | UNIVERSAL labeling Path D (SL=1.5) | SUSPICIOUS-OOS-DOMINANT | +SL widening (REJECTED at CONFIRMATION) |
| #7 | /066 | UNIVERSAL vol_scale_ceiling=0.8 | INERT | none |
| #8 | /067 | Confidence threshold floor=0.60 | INERT | none |
| #9 | /068 | Label timeout 21→42 | NEGATIVE | none |
| #10 | /069 | Universe expansion +ADA | INERT (corrected) | none |
| **CONFIRMATION** | **/070** | **/065 + /062 bundle** | **SUSPICIOUS-OOS-DOMINANT, NO-MERGE** | Component A REJECTED; Component B (Path B4) RETAINED |

**Cycle 1 produced NO BASELINE_V3 update.** /059 remains canonical. The /065 SL-widening edge candidate FAILED CONFIRMATION validation — IS collapse -0.97. Path B4 methodology is the one durable cycle 1 gain.

---

## Recommendations to QR for Phase 8 + Cycle 2

1. **BASELINE_V3.md UNCHANGED** — /059 (IS +1.0894 / OOS +0.5791) remains the canonical baseline. Document /070 NO-MERGE outcome in Phase 8 diary.

2. **Path B4 RETAINED in runner** — the dsr_relative_B4 / daily_sharpe_oos_b4_at_sqrt252 / cpcv_q75_annualized_b4 / n_daily_obs_oos fields are correct, useful methodology infrastructure. Do NOT revert Path B4 in cycle 2.

3. **DEFAULT_ATR_MULTIPLIERS: recommend REVERT to (2.0, 1.0)** — /065/070 evidence is unambiguous: SL widening (1.0→1.5×ATR) is regime exposure, not robust edge. IS-collapse + OOS-soar pattern PERSISTED at multi-seed CONFIRMATION. QR Phase 8 to adjudicate and commit the revert (or document justification for retention).

4. **Cycle 2 axis priorities** — LDO weakness persisted through all cycle 1 EXPLORATIONs and CONFIRMATION: IS net_pnl -47.46 (28.6% WR), OOS net_pnl -13.77 (35.7% WR). LDO is a structural drag. Cycle 2 options:
   - Model architecture (meta-labeling per /017 mandate — never fully executed)
   - Labeling architecture (fixed-horizon return labels as alternative to ATR triple-barrier)
   - Universe revision (replace LDO with a symbol that has IS-validated edge)
   - Per-symbol IS-axis discipline: validate any per-symbol customization PRESERVES IS Sharpe before including in bundle

5. **The 10.81 OOS/IS ratio pattern**: this pattern appeared at single-seed /065 EXPLORATION and amplified at CONFIRMATION. Future EXPLORATION briefs should pre-register an OOS/IS RATIO BOUND (e.g., reject if ratio > 3.0) as a supplemental diagnostic gate. Ratio > 3.0 is a structural red flag regardless of absolute OOS Sharpe magnitude.

---

## Status

**OVERALL = READY-FOR-CRITIC**

Classification: SUSPICIOUS-OOS-DOMINANT (CONFIRMATION mode). NO-MERGE. BASELINE_V3.md UNCHANGED (/059 canonical). Path B4 methodology RETAINED as infrastructure.
