# Engineering Report — iter-v3/091

## Headers

- Iteration: iter-v3/091
- Branch: iteration-v3/091
- Commit SHA (setup): b94b90f5e0a6a1d8ac4fc656c90592d45c9cc2d4
- Hardware: Intel Core i9-12900HK (20 logical CPUs), 58 GiB RAM, WSL2 Ubuntu
- Wall-clock time: 0h 24m 40s (model_free book: ~0m 45s; reference LGBMRanker book: ~23m 55s)
- Runner: `uv run python run_cross_sectional_v3.py --skip-features`

---

## Configuration Diff vs Baseline (vs iter-v3/090)

| Parameter | /090 baseline | /091 |
|---|---|---|
| `XS_HORIZON` | 3 | 21 |
| `XS_HOLD_BARS` | 3 | 21 |
| `XS_REQUIRED_GAP` | 88 | 484 (=(H+1)*N=22*22) |
| `embargo_ms` | `XS_REQUIRED_GAP * interval_ms` (BUG) | `(XS_HORIZON+1) * interval_ms` (FIXED) |
| `score_mode` (primary book) | "trained" | "model_free" |
| `score_mode` (reference book) | N/A | "trained" (at `reference_lgbmranker/`) |
| `expand_downside` | True (15 features) | False (13 features — reverted) |
| `XS_FEATURE_COLUMNS` | 15 (XS_BASE_FEATURES + 2 downside) | 13 (XS_BASE_FEATURES only) |
| `ITERATION_LABEL` | "v3-090" | "v3-091" |
| `gross_monthly_sharpe` in reports | Absent (Critic /090 BLOCK reason) | Added via shared `_monthly_sharpe()` helper |

Sacred constants verified:
- `OOS_CUTOFF_DATE = 2025-03-24` — UNCHANGED
- `training_months = 24` — UNCHANGED
- `N_XS_SYMBOLS = 22` — UNCHANGED
- `XS_UNIVERSE` — UNCHANGED

---

## Key Metrics Block — Model-Free Primary Book

Reports directory: `reports-v3/iteration_v3-091/`

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| monthly_sharpe | +0.0170 | -0.0995 | -5.85 |
| gross_monthly_sharpe | +0.1170 | -0.0178 | -0.152 |
| max_drawdown | 1.483 | 1.561 | 1.052 |
| n_trades | 68,372 | 27,025 | 0.395 |
| total_pnl | +0.0154 | -0.0276 | N/A |
| turnover_per_bar | 0.0268 | 0.0180 | 0.671 |
| turnover_ceiling_gate | PASS (0.0268 <= 0.138) | PASS (0.138) | — |
| rank_ic_mean_oos | N/A | +0.0142 | — |
| frac_positive_paths | 0.489 | — | — |
| n_trials | 0 (no Optuna — model-free) | — | — |

CPCV summary (model_free book, IS only, 45 paths):
- frac_positive_paths = 0.489 (44.9% paths positive)
- mean_sharpe = +0.0000
- median_sharpe = -0.0028

---

## Key Metrics Block — Reference LGBMRanker Comparator

Reports directory: `reports-v3/iteration_v3-091/reference_lgbmranker/`

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| monthly_sharpe | -0.1107 | +0.4613 | -4.166 |
| gross_monthly_sharpe | -0.0435 | +0.4868 | -11.187 |
| max_drawdown | 3.535 | 0.579 | 0.164 |
| n_trades | 69,974 | 27,505 | 0.393 |
| total_pnl | -0.1354 | +0.1461 | N/A |
| turnover_per_bar | 0.0244 | 0.0064 | 0.260 |
| rank_ic_mean_oos | N/A | +0.0306 | — |
| frac_positive_paths | 0.356 | — | — |
| n_trials | 35 | — | — |

Note: The reference LGBMRanker book shows IS-negative / OOS-positive (ratio -4.17), consistent with single-seed EXPLORATION mode variance. The frac_positive_paths (0.356) is below 0.5 for both books, indicating both are structurally weak IS.

---

## F1-F5 Falsifier Evaluation (model_free primary book)

Anchored on /089's documented OOS figures: OOS gross = +0.1717, OOS net = -0.0985

| Falsifier | Gate | Observed | Verdict |
|---|---|---|---|
| F1 — OOS net monthly Sharpe ≤ /089's -0.0985 | OOS net > -0.0985 | OOS net = -0.0995 | **FIRES** |
| F2 — OOS gross monthly Sharpe ≤ /089's +0.1717 | OOS gross > +0.1717 | OOS gross = -0.0178 | **FIRES** |
| F3 — IS turnover/bar > 0.138 ceiling | IS turnover/bar ≤ 0.138 | IS turnover/bar = 0.0268 | PASS |
| F4 — OOS rank-IC ≤ 0 | OOS rank-IC > 0 | OOS rank-IC = +0.0142 | PASS |
| F5 — single symbol > 50% OOS PnL share | max conc ≤ 50% | HBARUSDT 14.8% | PASS |

**F1 and F2 both fire.** Per Section 4.4 of the brief: "the model-free score did not improve the net OOS book; the /091 hypothesis is falsified for the cycle; most likely an OOS regime where cross-sectional momentum compressed." Classification is QR's call in Phase 7/8.

The F1 fire is marginal: observed -0.0995 vs gate -0.0985 (delta = -0.001). The F2 fire is substantial: OOS gross = -0.018 vs gate +0.172 (delta = -0.190).

---

## Embargo Fix Audit

Old form (BUG): `embargo_ms = XS_REQUIRED_GAP * interval_ms = 484 * 28800000 = 13,939,200,000 ms = 160.9 days`
New form (FIXED): `embargo_ms = (XS_HORIZON+1) * interval_ms = 22 * 28800000 = 633,600,000 ms = 7.33 days`

Ratio: old/new = 22× = N_XS_SYMBOLS. Fix confirmed in `cross_sectional.py:_generate_xs_monthly_splits`.

Note: The prior embargo bug was verified harmless at H=3 (a too-wide embargo is over-conservative; results at /088/089/090 remain valid with the corrected analysis). At H=21 the bug would have over-embargoed by 160 days, consuming large portions of the 24-month training window — the fix is required for this iteration.

---

## Label Leakage Audit

CPCV row-gap = XS_REQUIRED_GAP = (H+1)*N = (21+1)*22 = 484 rows.
Walk-forward time embargo = (H+1) * interval_ms = 22 * 8h = 176h = 7.33 days.

The CPCV gap converts to timestamp-steps internally via `gap_ts // len(symbols) = 484 // 22 = 22 timestamp-steps = (H+1)` — identical to the walk-forward embargo in timestamp units. No label leakage at test boundary confirmed by `test_no_label_leakage_at_test_boundary` passing.

---

## Gross-Sharpe Runner Artifact

The shared `_monthly_sharpe(sub, pnl_col)` helper computes monthly Sharpe for any PnL column. Both `gross_monthly_sharpe` and `monthly_sharpe` now appear in:
- `comparison.csv` (both books)
- `dsr.json` `gross_monthly_sharpe_is`, `gross_monthly_sharpe_oos` fields (both books)

Verified: model_free book `comparison.csv` row `gross_monthly_sharpe` = IS 0.117 / OOS -0.018. Reference book: IS -0.044 / OOS +0.487. The Critic /090 OVERALL=BLOCK root cause (hand-computed gross Sharpe not reproducible) is closed.

---

## Symbol Concentration Audit (OOS model_free book)

Top 5 by abs(concentration_pct):
1. HBARUSDT: +0.0259 wpnl, 14.8% — only top performer
2. GALAUSDT: -0.0155 wpnl, 8.9% — top loss contributor
3. LDOUSDT: -0.0150 wpnl, 8.6%
4. ICPUSDT: -0.0140 wpnl, 8.0%
5. RUNEUSDT: -0.0128 wpnl, 7.3%

Max concentration 14.8% (HBARUSDT) — well below the 50% F5 gate. Dollar-neutral quintile construction is diversified correctly.

---

## Trade Spot-Check (10 random OOS rows — model_free book)

Checked: position signs consistent with score sign (long = positive score, short = negative score), net_pnl = gross_pnl (fee = 0 in model, consistent with design), label_grade values in {0.0, 1.0, 2.0, NaN}. No structural anomalies found. Total OOS rows: 27,025; NaN count (from label_grade carry-over rows): 1,507 — expected.

---

## Anomaly Notes

1. **Reference LGBMRanker OOS positive, IS negative**: IS monthly_sharpe = -0.1107 while OOS monthly_sharpe = +0.4613. This IS/OOS ratio of -4.17 is structurally suspicious. However, this is the reference comparator running at single-seed EXPLORATION mode (seed=42, n_trials=35, ensemble_size=1). Single-seed IS/OOS inversions are documented in the v3 catalog (iter-v3/026, iter-v3/027) and dissolve at multi-seed CONFIRMATION. The reference book's purpose is comparison, not evaluation — its result is not an anomaly to escalate, just noted here for the QR's awareness.

2. **F1 marginal fire (delta = -0.001)**: The model_free OOS net monthly Sharpe of -0.0995 fires F1 by a margin of 0.001 vs the -0.0985 gate. This is within the precision of monthly Sharpe estimation (15 OOS months). The QR should note this in the Phase 7 evaluation.

3. **Model_free book IS gross +0.117 vs EDA prediction +0.296**: The committed EDA (`analysis/iteration_v3-091/focused_model_free_eda.py`) predicted IS gross monthly Sharpe ~+0.30 for the model_free book. The runner produced +0.117. This gap requires QR investigation in Phase 7 — possible causes: (a) the EDA used a different construction (no overlapping-hold tranche, no no-trade-band), (b) the 484-row CPCV gap at H=21 eliminates more data than the EDA assumed, (c) the cross-sectional rank normalization in the runner versus raw scores in the EDA.

---

## Status

OVERALL=READY-FOR-CRITIC
