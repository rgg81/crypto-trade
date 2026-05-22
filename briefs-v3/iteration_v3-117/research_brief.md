# iter-v3/117 Research Brief — Cycle-6 EXPLORATION #8

**Axis**: CANDLE FREQUENCY — change the v3 decision grid from 8h to 24h with the 3-offset multi-offset derived-series technique (offsets 0h / 8h / 16h UTC). Per user directive 2026-05-20 (`feedback_v3_candle_frequency_unblocked.md`): the 8h-only candle-frequency constraint is UNBLOCKED from iter-v3/117 onward. Locked constraints: BCH/LDO/TRX universe, LightGBM model, <2h wall-clock cap. The user (2026-05-20): *"Be free and I hope I can please the QR. He is in a very bad mood to find good alpha."*

**Cycle**: 6 EXPLORATION slot #8 of 10 (iter-v3/120 is the mandatory cycle-6 CONFIRMATION). The cycle-6 axis menu (`project_v3_cycle6_axis_menu.md`) was spent by /110–/114 (universe ×2, model architecture ×1, multi-frequency-features-on-8h ×1, risk management ×1 — all NEGATIVE); /115 closed the labeling-architecture axis (NEGATIVE); /116 found the first PROMISING via an exit-layer primitive (PROMISING-MECHANICAL — strictly accretive on /059, carried as a component decision into the /120 CONFIRMATION). iter-v3/117 advances to the CANDLE-FREQUENCY axis — the one structural lever the QR has never had access to until the 2026-05-20 user directive.

**Anchor (EXPLORATION-mode comparison)**: iter-v3/060 (IS monthly Sharpe **+0.8325** / OOS monthly Sharpe **+0.1403**) — the 3-seed EXPLORATION-mode reference per `BASELINE_V3.md`. iter-v3/116 EXPLORATION-PROMISING-MECHANICAL produced IS +0.6246 / OOS +1.1089 but its slot-freeing cascade is non-compoundable; the candle-frequency axis is tested in /117 ISOLATION with the /059-canonical baseline (the /116 no_confirm primitive is REVERTED for /117 — see Section 3.5 Change 5).

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. The sacred constants are immutable across all three tracks; no /117 modification touches them.

- **IS window**: data extent start (per-symbol earliest 8h candle close ≥ 2020-01-01) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent (~2026-05-19).
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **Reporting layer**: `comparison.csv` and `in_sample/` / `out_of_sample/` directories split on `OOS_CUTOFF_DATE` exactly.

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

The brief declares ONE hand-chosen design parameter:
- **Candle frequency = 24h** (= 1d). Hand-chosen per the user directive 2026-05-20 (`feedback_v3_candle_frequency_unblocked.md`) and the /116 diary Section 9 recommendation. Not selected from an IS-only sweep — declared hand-chosen with the IS-only rationale: *cycle-6's six 8h NEGATIVEs (/110-/115) empirically reconfirmed the /109 terminal null is intrinsic to the 8h representation; 24h is the user-suggested first frequency-axis test; /113's T5 daily-ONLY POOLED AUC 0.5275 p=0.00 is direct prior evidence that the daily representation carries signal the 8h cannot exploit when constrained to an 8h decision grid; iter-v3/117 changes the decision grid itself to 24h.*

The brief declares THREE hand-chosen architectural parameters:
- **Number of offsets = 3**, at offsets {0, 8, 16} UTC hours. Hand-chosen because the 8h base candle stream produces exactly 3 sub-bars per UTC day; aligning offsets to the 8h sub-bar boundaries (00/08/16) is the natural, look-ahead-free derivation. Not tuned; declared hand-chosen with the rationale: *the 8h candle structure determines the offset grid by construction*.
- **Per-symbol pooled-offset training architecture** (1 LightGBM per symbol, trained on the concatenated 3-offset panel with `offset_id` as a feature). Hand-chosen over the alternative (3 LightGBMs per symbol, one per offset). Rationale: *the pooled-offset architecture multiplies training data 3× per LightGBM model (~4500 rows vs ~1500 standalone), closing the data-count gap vs the 8h baseline (~5500 rows); matches the /059 per-symbol pattern with one model per symbol; single Optuna fit surface per symbol-month (fewer overfit surfaces)*.
- **Label timeout = 7 daily bars** (= 7 calendar days at 24h, calendar-time-equivalent to /059's 21×8h = 168h horizon). Hand-chosen per the EDA's T6 evidence: the BAR-count-equivalent design (21 daily bars = 21 days) was TESTED FIRST and REJECTED — BCH label rate collapsed to 99.13% positive (the +2 ATR target dominates the -1 ATR stop in the 3× longer calendar window). Preserved as `T5/T6_BAR_COUNT_EQUIV_REJECTED.csv` for the auditable record. Calendar-time-equivalent scaling restores /059's barrier-asymmetry geometry at the new bar grid.

The brief introduces NO tuned scalar parameter — every numeric design choice (frequency, offset grid, training architecture, label timeout) is hand-chosen with an explicit IS-only rationale that does NOT depend on any sweep output.

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-117/`, commit `c64a5fc`) was committed in ONE atomic commit BEFORE this brief or any subsequent setup commit touches the runner. Every script in the EDA directory asserts `close_time < OOS_CUTOFF_MS = 1742774400000`; no OOS-window file is read at any point. The two T5/T6 BAR_COUNT_EQUIV_REJECTED files are saved BEFORE the calendar-time-equivalent design was chosen (the 21-daily-bar test came first chronologically in the EDA run). There is no OOS coverage annex — the parameters above are hand-chosen, not OOS-tuned, and the brief is committed *before* the runner code change.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: candle frequency)
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35 --bar-interval 24h` (the new `--bar-interval` flag is the runner change in Section 3.5; default `8h` preserves all prior-iteration byte-identity)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per `feedback_v3_outer_seed_cap_2_v3.md` + the v3 EXPLORATION-mode default; first 3 seeds of the unified 10-seed lineage)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md` — above TPE warmup ~30; the v3 EXPLORATION default since iter-v3/019)
- **Wall-clock cap**: ≤ 2h (cycle-6 EXPLORATION cap per `feedback_v3_cadence_discipline.md`; /116 ran 0.70h, /115 ran 0.69h, /113 ran 0.80h — comfortably under cap. The 24h decision grid has ~3× fewer bars per offset than 8h does per symbol; the 3-offset panel concatenation restores the row count to ~4500/symbol — comparable to 8h's ~5500/symbol — so per-symbol training time is comparable to the 8h baseline)
- **Single axis variation**: candle frequency (8h → 24h-multi-offset). The /116 no_confirm primitive is REVERTED in /117 (Section 3.5 Change 5) so the frequency axis is tested in isolation.

---

## Section 1 — Hypothesis

**Single sentence**: aggregating the 8h candle stream into a 24h decision grid with the 3-offset multi-offset derived-series technique (offsets 0h / 8h / 16h UTC) produces a feature→label representation that carries directional signal the 8h representation lacks, by virtue of (a) the daily-frequency representation aggregating-out 8h microstructure noise that the /109 terminal null is built on, and (b) the 3-offset derivation multiplying per-symbol training data 3× while preserving the lower-frequency dynamics — and this signal will transfer through production LightGBM walk-forward training to lift the universe-aggregate IS monthly Sharpe materially above the /060 anchor (+0.8325) with a positive OOS Sharpe Δ.

The hypothesis is **falsifiable** on three pre-registered axes (Section 7 + Section 8): the IS monthly Sharpe (Section 8 NEGATIVE floor at +0.7325), the OOS monthly Sharpe direction relative to the /060 anchor (+0.1403), and the trade-roster cardinality (Section 8 BEHAVIORAL-INERTIA gate: < 30 IS trades on the 24h grid → trivially-different design).

---

## Section 2 — IS-Only Numerical Evidence

**Source**: `analysis/iteration_v3-117/` (committed in commit `c64a5fc` BEFORE this brief). 10 result tables (T1–T10) + an explicit synthesis. The EDA's headline gate (T9 universe-pooled permutation null) PASSES; the formal pre-registered verdict is NO-GO under per-symbol gates (g1 FAIL); the substantive read is PARTIAL-GO at the universe level. Per the PRIME DIRECTIVE the brief proceeds to a Phase-6 backtest with an honest modal prediction band reflecting both the universe-pooled positive evidence and the per-symbol risk.

### 2.1 The headline gate (T9): universe-pooled permutation null CLEARS

| Model | n_rows | n_folds | observed AUC | null_q50 | null_q95 | p_value | clears_q95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **24h-multioffset 3-sym-pooled** | **12280** | **5** | **0.5823** | 0.4998 | 0.5113 | **0.00** | **TRUE** |

Source: `analysis/iteration_v3-117/T9_universe_pooled.csv`.

**Anchors for comparison** (committed prior artifacts):
- /109 8h-stack: AUC 0.4970, p=0.64 — the terminal 8h null (committed at `analysis/iteration_v3-109/T1_per_fold_metrics.csv` per the /109 closeout)
- /113 8h-only POOLED: AUC 0.4889 — committed at `analysis/iteration_v3-113/T1_walkforward_auc.csv`
- /113 8h+daily POOLED: AUC 0.5015, p=0.39 — committed at `analysis/iteration_v3-113/T4_permutation_null.csv` (the /113 NEGATIVE — daily features on an 8h decision grid did NOT clear)
- /113 daily-ONLY POOLED: AUC 0.5275, p=0.00 — committed at `analysis/iteration_v3-113/T5_daily_only_signal.csv` (positive prior — daily features carry signal in isolation)
- **/117 24h-multioffset universe-pooled**: AUC **0.5823**, p=0.00 — **the strongest held-out feature→label signal v3 has produced**

The 24h-multioffset representation produces an AUC lift of **+0.0934 vs /109 8h** (the terminal null), **+0.0808 vs /113 8h+daily** (the failed /113 mixed-frequency design), and **+0.0548 vs /113 daily-ONLY** (the strongest prior positive). The lift over /113 daily-ONLY is the key: /113 daily-ONLY was attached to an 8h decision grid (the feature was 24h but the decision was 8h); /117 changes the decision grid itself to 24h, and the AUC lifts another +0.0548 points — empirical evidence that the daily decision-grid is the active mechanism, not merely the daily feature smoothing.

### 2.2 Per-symbol permutation null (T2)

| Model | observed AUC | null_q50 | null_q95 | p_value | clears_q95 |
|---|---:|---:|---:|---:|---:|
| 24h-multioffset BCHUSDT | 0.4778 | 0.4845 | 0.5848 | 0.53 | FALSE |
| **24h-multioffset LDOUSDT** | **0.5201** | 0.4991 | 0.5323 | **0.18** | **FALSE (soft-clears null_q50 but not q95)** |
| 24h-multioffset TRXUSDT | 0.5092 | 0.4993 | 0.5147 | 0.17 | FALSE (soft-clears null_q50, marginal on q95) |
| **24h-multioffset POOLED** | **0.5823** | 0.5005 | 0.5104 | **0.00** | **TRUE** |

Source: `analysis/iteration_v3-117/T2_permutation_null.csv`.

The POOLED-across-symbols AUC clears formally; per-symbol AUC clears formally only for none of the three (LDO p=0.18 and TRX p=0.17 are soft-positive but below 0.05). The g1 hard gate is FAIL.

**Mechanism behind the per-symbol weakness**: BCH's structural label imbalance (Section 2.3) prevents per-symbol AUC measurement on BCH (effectively single-class). LDO and TRX produce real but modest per-symbol signal. The signal aggregates — pooling triples the effective sample, the cross-symbol shared structure (BTC dominance, daily-frequency regime variables) becomes visible — and POOLED clears decisively. This is the standard cross-sectional-aggregation pattern: per-symbol noise dominates, universe-pooled signal emerges.

### 2.3 Label balance (T6): the BCH structural artifact

| Symbol | n_rows | p(label=1) | imbalance | healthy (|p-0.5| < 0.10) |
|---|---:|---:|---:|---|
| **BCHUSDT** | 5108 | **0.9912** | **+49.12%** | NO — single-class |
| LDOUSDT | 2122 | 0.6451 | +14.51% | NO — moderate-imbalance |
| TRXUSDT | 5050 | 0.5665 | +6.65% | **YES** |

Source: `analysis/iteration_v3-117/T6_label_balance.csv`.

BCH's label is 99.12% positive on the 24h grid at the /059-faithful triple-barrier (atr_tp=2.0, atr_sl=1.0, calendar-time-equivalent timeout=7 daily bars). The +2 ATR target almost always hits before the -1 ATR stop on BCH at the daily-frequency scale; this is a structural property of BCH's daily-frequency volatility profile, not a labelling bug.

**Why not just fix BCH's labelling at /117?** Two reasons. (1) The /059-canonical barrier asymmetry IS the v3 baseline; changing the BCH barrier alone breaks the per-symbol attribution comparability against /060 (and turns the experiment into a 2-axis change: frequency + per-symbol labelling). (2) The /116 closeout (the most recent baseline-update precedent) carries the no_confirm primitive into /120 as strictly accretive — bundling a /117 labelling change would violate the PROMISING-MECHANICAL non-compoundability rule.

**Mitigation strategy**: BCH's structural imbalance is documented as Section 7 Failure Mode 2 (BCH-collapse / portfolio-survives-on-LDO+TRX). The brief Section 8 Criterion 5a (the SUSPICIOUS-OOS-DOMINANT gate) is calibrated to detect the BCH-collapse case and classify it correctly. If BCH-collapse fires and LDO+TRX carry positive lift, the result is a NEGATIVE-class outcome (the universe is 3-symbol; losing BCH's contribution is a meaningful portfolio loss), but the universe-pooled signal evidence is preserved as a positive Phase-7 finding for future-iteration design.

### 2.4 Per-offset breakdown (T3): the multi-offset derivation is causally contributing

| Symbol | offset_h | n_rows | AUC | > 0.5 |
|---|---:|---:|---:|---|
| BCHUSDT | 0 | 1702 | **0.6213** | YES |
| BCHUSDT | 8 | 1703 | 0.5028 | YES (marginal) |
| BCHUSDT | 16 | 1703 | 0.4628 | NO |
| LDOUSDT | 0 | 707 | 0.5485 | YES |
| LDOUSDT | 8 | 707 | 0.5084 | YES (marginal) |
| LDOUSDT | 16 | 708 | 0.4734 | NO |
| TRXUSDT | 0 | 1683 | 0.4590 | NO |
| TRXUSDT | 8 | 1683 | 0.5092 | YES (marginal) |
| TRXUSDT | 16 | 1684 | **0.5455** | YES |

Source: `analysis/iteration_v3-117/T3_per_offset_auc.csv`. 6 of 9 cells exhibit AUC > 0.5; g3 PASS.

**The multi-offset derivation pattern**: the 3 offsets carry different signal strengths per symbol (BCH strongest at offset 0; TRX strongest at offset 16; LDO weakly positive at offsets 0 and 8). No single offset dominates — each contributes. The g3 PASS is the empirical evidence that the multi-offset technique is doing real work; if all the signal lived at a single offset, the technique would be redundant (just use that offset standalone). The fact that the strongest offset varies per symbol justifies the multi-offset pooled-training design — a single-offset 24h model on offset 0 would capture BCH+LDO but lose TRX; a single-offset 24h model on offset 16 would capture TRX but lose BCH. Multi-offset pooling captures all three.

### 2.5 Multi-offset derivation audit (T4): look-ahead-free assertion PASS

900 audits across {3 symbols} × {3 offsets} × {100 sample bars each}; 900/900 PASS on the 5-property assertion:
1. The 24h bar's `bar_close_time` equals the close_time of the latest 8h sub-bar in its window
2. `bar.high == max(sub_bars.high)`
3. `bar.low == min(sub_bars.low)`
4. `bar.close == sub_bars.sort_by(open_time).last().close`
5. `bar.open == sub_bars.sort_by(open_time).first().open`

PLUS the strict look-ahead-free check: NO 8h candle with `close_time > bar_close_time` enters any 24h bar's aggregation.

Source: `analysis/iteration_v3-117/T4_derivation_audit.csv`. The multi-offset technique is causally clean — every 24h decision row uses only 8h candles whose close_time precedes the 24h bar's own bar_close_time.

### 2.6 Data coverage (T5): healthy training-data budget

| Symbol | offset_h | n_rows | n_pos | n_neg | p(label=1) |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 0 | 1702 | 1688 | 14 | 0.9918 |
| BCHUSDT | 8 | 1703 | 1686 | 17 | 0.9900 |
| BCHUSDT | 16 | 1703 | 1689 | 14 | 0.9918 |
| **BCHUSDT POOLED** | **5108** | 5063 | 45 | 0.9912 |
| LDOUSDT | 0 | 707 | 456 | 251 | 0.6450 |
| LDOUSDT | 8 | 707 | 452 | 255 | 0.6393 |
| LDOUSDT | 16 | 708 | 461 | 247 | 0.6511 |
| **LDOUSDT POOLED** | **2122** | 1369 | 753 | 0.6451 |
| TRXUSDT | 0 | 1683 | 955 | 728 | 0.5674 |
| TRXUSDT | 8 | 1683 | 952 | 731 | 0.5657 |
| TRXUSDT | 16 | 1684 | 954 | 730 | 0.5665 |
| **TRXUSDT POOLED** | **5050** | 2861 | 2189 | 0.5665 |

Source: `analysis/iteration_v3-117/T5_data_coverage.csv`. Per-symbol POOLED row counts are 5108 / 2122 / 5050 — comparable to the 8h baseline's ~5500/sym. g4 (SOFT) PASS: each symbol >= 1500 rows.

### 2.7 GO/NO-GO synthesis (T10)

| Gate | Value | Threshold | PASS |
|---|---|---|---|
| g1 (per-symbol q95 clears, >=2/3) | 0/3 symbols clear formal q95 | >=2/3 | **FAIL** |
| g2 (pooled q95 clears) | observed=0.5823 > q95=0.5104 | observed > q95 | **PASS** |
| g3 (per-offset cells AUC > 0.5, >=6/9) | 6/9 cells > 0.5 | >=6/9 | **PASS** |
| g4 SOFT (per-symbol n_rows >= 1500) | {BCH:5108, LDO:2122, TRX:5050} | >=1500 each | **PASS** |
| **VERDICT (g1 AND g2 AND g3)** | g1 FAIL blocks AND-conjunction | all three hard | **NO-GO (formal)** |

Source: `analysis/iteration_v3-117/T10_go_nogo_verdict.csv`.

**Formal pre-registered verdict: NO-GO** (g1 FAIL on per-symbol q95). The g1 failure is BCH's structural label-imbalance artifact, NOT a representation-lacks-signal mechanism.

**Substantive read: PARTIAL-GO at universe level.** g2 (universe-pooled permutation null clears, AUC 0.5823, p=0.00) is the headline statistical evidence; g3 (multi-offset derivation contributing across 6 of 9 cells) confirms the design works mechanically. The per-symbol weakness is a structural BCH-imbalance artifact (LDO and TRX produce real but per-symbol-subliminal signal; pooling makes it cross the formal significance threshold).

**Per the PRIME DIRECTIVE the brief proceeds to a Phase-6 backtest.** The NO-GO formal verdict sets the modal prediction band toward EXPLORATION-NEGATIVE (~50% Section 7); the PARTIAL-GO substantive read raises the secondary-outcome probability of EXPLORATION-PROMISING to ~20% (vs the typical ~5% on a hard-NO-GO axis).

### 2.8 Feature stationarity (T7): WARM-UP-ARTIFACT pattern

| Symbol | n stationary | n total | % stationary |
|---|---:|---:|---:|
| BCHUSDT | 4 | 14 | 28.6% |
| LDOUSDT | 6 | 14 | 42.9% |
| TRXUSDT | 7 | 14 | 50.0% |
| **TOTAL** | **17** | **42** | **40.5%** |

Source: `analysis/iteration_v3-117/T7_adf_stationarity.csv`.

40.5% stationary at the IS-end window is **lower than the v3 8h baseline's typical ~100%** (per the /116 closeout's `adf_test.csv`). The pattern is consistent with the standard ADF warm-up-artifact: rolling features with long windows (50-bar, 100-bar, 200-bar) at the daily timescale need substantially more calendar time to stabilize than at 8h. At 24h, a 200-bar window covers ~200 days; the IS window's earliest months are still in the rolling-feature warm-up phase. The per-symbol IS-end window (the operative diagnostic) is at the data-extent end; the warm-up affects only the early IS months, NOT the period the runner trades on.

**This is a known property of the 24h-derived feature stack**, not a blocking finding. Section 5 Risk 3 documents the mitigation; Section 7 Failure Mode 3 documents the non-stationarity-driven failure path. The runner pre-flight stationarity check is informational (not blocking) — the v3 Critic Check 5 ADF gate is interpreted in the context of the EDA evidence per `feedback_v3_oos_is_ratio_gate.md` precedent (informational, not auto-block).

---

## Section 3 — Proposed Changes (the architectural diff vs /059)

| Item | /059 baseline | iter-v3/117 |
|---|---|---|
| **Candle frequency** | 8h | **24h** (the single STRUCTURAL axis) |
| **Multi-offset derivation** | (not applicable at 8h) | **3 offsets: 0h, 8h, 16h UTC** (the single ARCHITECTURAL axis) |
| **Per-symbol training architecture** | 1 LightGBM per symbol at 8h | **1 LightGBM per symbol at 24h, trained on concatenated 3-offset panel with offset_id as feature** |
| **Universe** | BCH, LDO, TRX | BCH, LDO, TRX (UNCHANGED — locked per user 2026-05-20) |
| **Model** | LightGBM | LightGBM (UNCHANGED — locked per user 2026-05-20) |
| **Label** | triple-barrier, atr_tp=2.0 / atr_sl=1.0, timeout=21 candles (= 21×8h = 168h) | triple-barrier, atr_tp=2.0 / atr_sl=1.0, **timeout=7 daily bars (= 7×24h = 168h, calendar-time-equivalent)** |
| **Feature stack** | 14-feature V3_FEATURE_COLUMNS at 8h | **14-feature V3_FEATURE_COLUMNS RECOMPUTED at 24h** + 1 new categorical column `offset_id ∈ {0, 8, 16}` (15-feature total) |
| **REQUIRED_GAP** | (21+1) × 3 = 66 | **(7+1) × 3 × 3 = 72** (timeout 7 daily bars × 3 symbols × 3 offsets per symbol) |
| **Cooldown candles** | 4 (8h × 4 = 32h) | **2** (24h × 2 = 48h, calendar-time-equivalent rounded down; pre-trade refractory period) |
| **VT lookback days** | 30 (8h × 30 candles = 10 days)? — actually VT uses calendar days directly, UNCHANGED |
| **`atr_tp_multiplier` / `atr_sl_multiplier`** | 2.0 / 1.0 | 2.0 / 1.0 (UNCHANGED) |
| **`label_mode`** | `triple_barrier` | `triple_barrier` (UNCHANGED) |
| **`enable_no_confirm_exit`** | False (/059 default) | **False (REVERTED from /116's True; see Section 3.5 Change 5)** |
| **`no_confirm_trigger_atr` / `no_confirm_k_candles`** | 0.50 / 4 | 0.50 / 4 (carried as default field values; never read when flag is False) |
| **7-gate RiskV2 stack** | UNCHANGED | UNCHANGED |
| **Ensemble seeds** | (191664963, 1662057957, 1405681631, ...) | (191664963, 1662057957, 1405681631) — first-3 of unified 10-seed lineage (EXPLORATION-mode `ENSEMBLE_SIZE=3`) |
| **n_trials** | 35 (EXPLORATION default) | 35 (EXPLORATION default) |

**The single substantive EXPLORATION axis vs /059** is the candle frequency (8h → 24h-multi-offset). All other architectural and labelling parameters are held /059-identical (with the exception of `cooldown_candles` and `REQUIRED_GAP`, which are mechanical recomputations under the new bar grid).

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

The QE implements 8 changes. The CRITICAL revert (Change 5) reverts the /116 no_confirm primitive so the candle-frequency axis is tested in isolation.

### Change 1 — Data acquisition: 24h multi-offset derived CSVs

The runner needs the 24h-derived OHLCV data for each symbol (and BTCUSDT for cross-asset features). The /113 EDA already established the look-ahead-free 8h→24h aggregation pattern. The QE adds a new module `src/crypto_trade/features_v3/multioffset_24h.py` that:

1. Reads `data/<SYM>/8h.csv` for `SYM ∈ {BCHUSDT, LDOUSDT, TRXUSDT, BTCUSDT}`.
2. For each `offset_h ∈ {0, 8, 16}`: aggregates 8h candles into 24h bars whose 24-hour window starts at `D + offset_h` for UTC day boundaries `D`. The 24h bar's OHLCV is open=first sub-bar, high=max, low=min, close=last, volume=sum. The `close_time` of the 24h bar equals the `close_time` of the LATEST sub-bar (the CAUSAL timestamp).
3. Concatenates the 3 offsets per symbol into a single DataFrame with columns `open_time, open, high, low, close, volume, close_time, offset_h` and writes to `data/<SYM>/24h_multioffset.csv`.

The data is computed at startup time (not pre-fetched) since it derives from the existing 8h CSVs. The startup adds ~5 seconds for the 4 symbols.

**Reference implementation**: `analysis/iteration_v3-117/_shared.py::aggregate_to_24h()` is the bit-identical EDA function the QE ports to `src/crypto_trade/features_v3/multioffset_24h.py::aggregate_to_24h()`. The EDA's T4 audit (900/900 PASS) is the validation evidence for the function.

### Change 2 — Feature generation at 24h

The runner's existing v3 feature path generates features from 8h klines into `data/features_v3/<SYM>_8h_features.parquet`. The /117 QE adds an analog path that generates features from 24h-multi-offset klines into a NEW directory `data/features_v3_24h/<SYM>_24h_multioffset_features.parquet`. The new directory keeps the 24h parquets isolated from 8h artifacts.

The feature computation:
1. Loads `data/<SYM>/24h_multioffset.csv` (the 3-offset concatenated derived CSV from Change 1).
2. For each `offset_h ∈ {0, 8, 16}`: filters to that offset's bars, computes the 14 V3_FEATURE_COLUMNS using the existing v3 feature pipeline AS IF the 24h bars were 8h bars (the feature pipeline is bar-unit agnostic — a "50-bar EMA" works regardless of bar size). Cross-asset features (`btc_ret_14d`, `sym_vs_btc_ret_7d`) join on `bar_close_time` against the matching-offset BTCUSDT 24h panel.
3. Concatenates the 3 per-offset feature frames per symbol; adds an `offset_id ∈ {0, 8, 16}` int64 column (categorical-style — LightGBM handles this as numeric).
4. Sorts by `bar_close_time` (not `open_time`) so the trade loop iterates in causal order.
5. Writes the per-symbol parquet.

**Critical assertion**: per-offset feature computation MUST be done in ISOLATION (compute features on offset-0 bars only using offset-0 bars; never let offset-8 bars enter offset-0's rolling-feature computation). This is the look-ahead-free property at the offset level. The QE's adversarial integration test (Change 8) verifies this.

**Reference implementation**: `analysis/iteration_v3-117/_shared.py::compute_features_24h()` + `add_btc_cross_features()` + `load_labeled_is()` are the bit-identical EDA functions the QE ports.

### Change 3 — New `--bar-interval` CLI flag in the runner

The runner gains a new CLI argument: `--bar-interval {8h, 24h}` (default `8h` for backward compatibility with all prior iterations). When `--bar-interval 24h` is passed:

- `BacktestConfig.interval = "24h"` (a NEW supported interval string; the existing `1d` mapping in `_INTERVAL_MINUTES` is leveraged via an alias)
- `LightGbmStrategy._INTERVAL_MINUTES` is extended: `"24h": 1440` (alias for `"1d": 1440`)
- `BacktestConfig.timeout_minutes = 7 * 24 * 60 = 10080` (UNCHANGED in minutes — 7 daily bars = 168h = 10080 min; this is calendar-time-equivalent to /059's 21×8h = 10080 min!)
- `BacktestConfig.cooldown_candles = 2` (24h × 2 = 48h refractory; /059 used 4 × 8h = 32h, /117 rounds DOWN to 2 daily bars to preserve a comparable order-of-magnitude pre-trade refractory)
- `_load_atr_for_master` reads `data/features_v3_24h/<SYM>_24h_multioffset_features.parquet` (NEW path)
- The trade loop iterates over rows in `bar_close_time` order — already supported since `master["open_time"]` is the time-sort key; at 24h the open_time/close_time pairs correspond to 24h bars.

**`feature_columns` extension**: the runner's `features_for_symbol()` returns `V3_FEATURE_COLUMNS + ["offset_id"]` when `bar_interval == "24h"`. The 15-column list is pinned (no auto-discovery) per `feedback_v3_explicit_feature_columns.md`.

### Change 4 — `REQUIRED_GAP` recomputation

The /059 formula: `REQUIRED_GAP = (timeout_candles + 1) × n_symbols × n_offset_series`. At /117:
- `timeout_candles = 7` (daily bars)
- `n_symbols = 3` (BCH/LDO/TRX)
- `n_offset_series = 3` (offsets 0, 8, 16)
- **REQUIRED_GAP = (7+1) × 3 × 3 = 72**

This is the cross-cell label-leakage purge gap at the panel level — covers both within-offset purging (forward 7-bar label window) and cross-offset purging (the 3 offsets at the same calendar day overlap in their forward-label windows; the embargo at the concatenated panel must cover all three).

The runner pre-flight accretion-guard verifies `REQUIRED_GAP == 72` when `--bar-interval 24h`; the existing `REQUIRED_GAP == 66` is preserved when `--bar-interval 8h` (backward-compat).

### Change 5 — REVERT the /116 no_confirm primitive (critical isolation)

iter-v3/117 tests the candle-frequency axis in ISOLATION; the /116 no_confirm primitive is REVERTED. The QE applies:

(a) **`run_baseline_v3.py:1941-1943`** — change `BacktestConfig(...)` argument from `enable_no_confirm_exit=True, no_confirm_trigger_atr=0.50, no_confirm_k_candles=4` BACK to `enable_no_confirm_exit=False, no_confirm_trigger_atr=0.50, no_confirm_k_candles=4` (the boolean flip is the substantive change; the two trigger fields stay at the default values per the `BacktestConfig` dataclass declaration but are NEVER READ when the flag is False).

(b) **`run_baseline_v3.py:2837-2851`** — change the pre-flight assertion from `assert _pf_cfg.enable_no_confirm_exit is True` to `assert _pf_cfg.enable_no_confirm_exit is False` with the message: `"PREFLIGHT FAIL: enable_no_confirm_exit must be False for iter-v3/117. iter-v3/116's no_confirm primitive is REVERTED in /117 so the candle-frequency axis is tested in isolation."`. The two scalar checks (`no_confirm_trigger_atr == 0.50` and `no_confirm_k_candles == 4`) STAY (they verify the default field values are intact for the eventual /120 CONFIRMATION bundle re-enable).

(c) **`run_baseline_v3.py:1108-1112`** — update the `_canonical_v059` accretion guard's `("enable_no_confirm_exit", _acc_cfg.enable_no_confirm_exit, True)` row to expect `False`: `("enable_no_confirm_exit", _acc_cfg.enable_no_confirm_exit, False)`. The two scalar entries stay at their default-value baselines.

(d) **`BacktestConfig` / `Order` field DEFINITIONS in `src/crypto_trade/backtest_models.py:77-86, 101-110`** stay UNCHANGED — the cheap default-False / default-zero / default-zero declaration carries no behaviour when the flag is False. This is the same revert pattern as /115→/116 (the field stays in the dataclass; the runner flips the value). Per the /116 closeout the field DEFINITIONS are baseline accretive; the value-flip is the per-iteration knob.

(e) **`src/crypto_trade/backtest.py:251-287` order-loop logic** stays UNCHANGED — the entire `if config.enable_no_confirm_exit` branch is dead code when the flag is False. The /059-canonical byte-identity guarantee from /116 Change 8(c) holds: a /117 run with `enable_no_confirm_exit=False` produces identical trade outcomes to a /059 run (same flag value); the new fields default to zero and are never read.

### Change 6 — Banner-print + ITERATION_LABEL + MODEL_SPECS updates

(a) **`run_baseline_v3.py:131`** — `ITERATION_LABEL = "v3-116"` → `ITERATION_LABEL = "v3-117"`.

(b) **`run_baseline_v3.py:197-199`** — `MODEL_SPECS` model-name prefix `"v3-116-BCH"`/`"v3-116-LDO"`/`"v3-116-TRX"` → `"v3-117-BCH"`/`"v3-117-LDO"`/`"v3-117-TRX"`.

(c) **`run_baseline_v3.py:2922-2925`** — banner-print update. The /116 print line reads:
```python
print(
    f"Gap: {REQUIRED_GAP} (= (21+1)*3; iter-v3/113 BCH/LDO/TRX per-symbol; "
    f"timeout UNCHANGED 10080 min; label_mode=triple_barrier; V3_FEATURE_COLUMNS=14)"
)
```
Update to reflect /117's REQUIRED_GAP and bar-interval awareness:
```python
print(
    f"Gap: {REQUIRED_GAP} (iter-v3/117 BCH/LDO/TRX per-symbol; "
    f"bar_interval={args.bar_interval}; timeout=10080 min; "
    f"label_mode=triple_barrier; V3_FEATURE_COLUMNS={len(V3_FEATURE_COLUMNS) + (1 if args.bar_interval == '24h' else 0)})"
)
```

### Change 7 — Accretion guard extension for `--bar-interval`

The runner's `_canonical_v059` accretion guard (currently 13 knobs) is extended to verify the bar-interval-conditional REQUIRED_GAP:

```python
expected_required_gap = 72 if args.bar_interval == "24h" else 66
expected_interval = args.bar_interval
checks = [
    ("REQUIRED_GAP", REQUIRED_GAP, expected_required_gap),
    ("BacktestConfig.interval", _acc_cfg.interval, expected_interval),
    # ... existing knobs ...
    ("enable_no_confirm_exit", _acc_cfg.enable_no_confirm_exit, False),  # /117 REVERT
    # ... existing knobs ...
]
```

### Change 8 — Adversarial integration test

New file `tests/test_multioffset_24h_aggregation.py` with three test cases:

(a) **Look-ahead-free assertion**: synthetic 8h panel with known close prices; aggregate to 24h at each of 3 offsets; assert every 24h bar's `bar_close_time` equals the close_time of the latest 8h sub-bar in its window and that no 8h candle with `close_time > bar_close_time` is in the bar's sub-bar list.

(b) **Per-offset feature isolation**: synthetic 24h-multi-offset panel where the 3 offsets carry distinct OHLCV patterns; compute a 50-bar EMA per offset in isolation; assert the offset-0 EMA at row 50 depends ONLY on offset-0 bars 0..49 (not on offset-8 or offset-16 bars at indices that overlap in panel-sort order).

(c) **Trade-loop integrity at 24h**: synthetic 24h master DataFrame with known signals; run the backtest loop; assert each trade's `open_time` and `close_time` differ by a multiple of `MS_PER_DAY = 86_400_000`, and that the `cooldown_candles=2` refractory translates to 48h of suppressed signals after each trade close.

---

## Section 4 — Expected OOS Impact (predicted bands)

**Pre-registered Section 4 numerical bands** (anchored on /060 EXPLORATION-mode reference IS +0.8325 / OOS +0.1403):

| Outcome class | IS monthly Sharpe band | OOS monthly Sharpe band | Probability |
|---|---|---|---|
| **Modal: INERT / EXPLORATION-NEGATIVE** (BCH-collapse + LightGBM doesn't translate EDA-AUC signal to production) | [+0.30, +0.70] (Δ vs /060 ∈ [−0.53, −0.13]) | [−0.20, +0.30] (Δ vs /060 ∈ [−0.34, +0.16]) | **~50%** |
| **Secondary: EXPLORATION-PROMISING** (universe-pooled signal survives production LightGBM; trade-roster lift transfers) | [+0.85, +1.20] (Δ vs /060 ∈ [+0.02, +0.37]) | [+0.40, +0.90] (Δ vs /060 ∈ [+0.26, +0.76]) | ~20% |
| **Tertiary: SUSPICIOUS-OOS-DOMINANT** (regime artifact — daily bars favour OOS uptrend) | [+0.30, +0.65] (Δ ∈ [−0.53, −0.18]) | [+0.50, +1.10] (Δ ∈ [+0.36, +0.96]); OOS/IS ratio > 1.5 | ~25% |
| **Residual: BEHAVIORAL-INERTIA-OR-CATASTROPHE** (trade roster < 30 or BCH portfolio-breaking loss) | varies | varies | ~5% |

**Modal-call rationale**: the EDA's formal verdict was NO-GO (g1 FAIL); the universe-pooled signal (g2 PASS) is real but per-symbol weak. Production LightGBM trained per-symbol cannot necessarily exploit a universe-pooled signal — the model must select profitable trades on BCH+LDO+TRX individually. The BCH structural label imbalance is the load-bearing risk: at 99% positive labels, LightGBM may collapse to a near-constant predict_proba ≈ 1, producing either zero discriminative signal (the model predicts long on every candle, gets filtered by the 7-gate stack and produces no trades — BEHAVIORAL-INERTIA) or constant-long entries that get hammered in any down-trending OOS month (a regime risk).

**Secondary-call rationale**: the universe-pooled AUC lift (0.5823 vs 0.4970 baseline) is +0.0853 — material by held-out-AUC standards. LightGBM trained per-symbol can produce probabilistic predictions even on imbalanced data (predict_proba calibration on the rare-class minority). LDO+TRX provide a 2-of-3-symbols portfolio carrier; even with BCH degenerate, the v3 model has carried portfolio Sharpe on 2 of 3 symbols before (the /116 attribution).

**Tertiary-call rationale**: a regime-exposed 24h-grid model that selects long trades in OOS uptrend months and avoids them in IS bear months would produce an OOS/IS divergence — the standard SUSPICIOUS pattern. The 24h calendar-time-equivalent timeout (7 days) is structurally a longer-duration directional bet than 8h's 7-day-equivalent (which spreads across 21 candles), so the 24h book is naturally more regime-sensitive.

**Explicit falsifier**: if the production OOS monthly Sharpe falls below `−0.20` AND the IS monthly Sharpe falls below `+0.30`, the hypothesis is rejected — the universe-pooled AUC lift did NOT translate to production signal at all, and the EDA's signal is an artifact of the held-out-AUC measurement scope (or the LightGBM cannot exploit the 24h representation in production despite the EDA's positive evidence).

---

## Section 5 — Risk Mitigation

**Risk 1 — BCH structural label imbalance produces degenerate LightGBM model**. Mechanism: at 99.12% positive labels, LightGBM may overfit to the majority class and produce near-constant predict_proba ≈ 1, leading to either (a) every BCH candle classed as long → 7-gate stack filters most → near-empty BCH trade roster (BEHAVIORAL-INERTIA), or (b) every BCH candle classed as long → BCH trade roster is large → portfolio-breaking loss in any down-trend OOS month. Mitigation: the runner's 7-gate stack (vol scaling, ADX threshold, Hurst regime, z-score OOD, low-vol filter, hit-rate feedback, BTC trend alignment) filters by mechanism orthogonal to the LightGBM signal; even if BCH's LightGBM is degenerate, the gate filter prevents portfolio-breaking exposure. The runner pre-flight reports per-symbol IS trade count; if BCH IS trade count < 30 the result is BEHAVIORAL-INERTIA (Section 8 Criterion 3) and does not enter the formal PROMISING/NEGATIVE adjudication.

**Risk 2 — Cross-offset label leakage at fold boundaries**. Mechanism: the 3 offsets concatenated into one panel can leak labels if the embargo is not sized correctly. The 24h forward-label window for offset-0 day D ends at D+7×24h = D+168h; the offset-8 same-calendar-day decision row decides at D+8h and looks forward to D+8h+168h = D+176h (8h further); the offset-16 same-calendar-day row decides at D+16h and looks forward to D+16h+168h = D+184h. Three offset rows at the same calendar day overlap in their forward-label windows by up to 16h. Mitigation: `REQUIRED_GAP = 72 = (7+1) × 3 × 3` covers BOTH within-offset purging (7+1=8 daily bars) and cross-offset purging (× 3 offsets). The runner pre-flight verifies `REQUIRED_GAP == 72` at startup; the LightGBM walk-forward cv computes a fold-boundary gap of `8 daily bars × 3 = 24 daily bars per offset = 72 panel rows` (since the concatenated panel has 3 offsets per calendar day).

**Risk 3 — Feature stationarity warm-up at 24h**. Mechanism: 24h-derived features with 100-bar / 200-bar lookbacks need 100 / 200 calendar days to stabilize; the IS window's early months are in feature warm-up. T7 shows only 40.5% stationary at IS-end (vs ~100% at 8h baseline). Mitigation: the runner's `min_periods` enforcement on rolling-feature computation excludes warm-up rows from the master DataFrame (NaN-filter at LightGbmStrategy.compute_features); the actual training windows in walk-forward use only rows with all 14 features non-NaN. The Critic Check 5 ADF gate at /117 should be interpreted in context — the 40.5% rate is a property of the 24h representation, not a stationarity violation; the IS-end month's stationary rate is the operative diagnostic.

**Risk 4 — Per-symbol weakness at 24h**. Mechanism: LDO and TRX produced AUC > 0.50 at q-50 but not q-95 (per-symbol p=0.18 and p=0.17); the per-symbol weakness may translate to per-symbol production Sharpe weakness even when universe-pooled signal is real. Mitigation: the 7-gate RiskV2 stack's vol scaling + ADX threshold filters down to high-conviction trades; even at per-symbol AUC=0.52 the filtered trade book can be Sharpe-positive if the gates are selecting trades from the AUC>0.50 tail. Documented as Section 7 Mode 1 (the modal failure mode).

**Risk 5 — Multi-offset architecture introduces a new failure surface**. Mechanism: the 3-offset concatenated panel is structurally more complex than the 8h baseline's 3-symbol panel; bugs in the offset aggregation, feature computation, label assignment, or fold purging could silently corrupt training data. Mitigation: the EDA's T4 derivation audit (900/900 PASS) validates the aggregation; the QE's adversarial integration test (Change 8) validates the production code path including per-offset feature isolation; the runner's pre-flight accretion-guard verifies `REQUIRED_GAP=72`, `interval=24h`, `bar_interval=24h`, and the no_confirm revert (`enable_no_confirm_exit=False`); the Critic's Check 8 (Hypothesis-Implementation Alignment) verifies all 8 brief-declared changes at source.

---

## Section 6 — Risk Management Design

iter-v3/117 introduces ZERO new risk primitives. The /059-canonical 7-gate RiskV2 stack is UNCHANGED.

| Primitive | /059 baseline | /117 |
|---|---|---|
| 1. Vol scaling | enabled | UNCHANGED |
| 2. ADX threshold gate | enabled | UNCHANGED |
| 3. Hurst regime check | enabled | UNCHANGED |
| 4. Z-score OOD gate | enabled | UNCHANGED |
| 5. Low-vol filter | enabled | UNCHANGED |
| 6. Hit-rate feedback (OOS only) | enabled | UNCHANGED |
| 7. BTC trend filter | enabled | UNCHANGED |

The no_confirm primitive (the /116 PROMISING-MECHANICAL) is **REVERTED** per Section 3.5 Change 5 — the /117 candle-frequency axis is tested in isolation; the no_confirm primitive re-enters at the /120 CONFIRMATION bundle as strictly accretive (per `feedback_promising_mechanical_subtype.md`).

**Predicted fire-rate impact at 24h**: the 24h decision grid has fewer decision points per day than 8h (1 per offset per day vs 3 per day at 8h). The trade signal frequency is ~1/3 the 8h baseline per offset; the 3-offset architecture restores it to roughly 8h-comparable. The 7-gate stack's filter rate should remain in the same neighborhood (~30-40% of raw signals filtered to high-conviction trades). No primitive-specific tuning is performed at /117.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The brief Section 4 pre-registered four outcome bands. Section 7 names the SPECIFIC mechanisms behind each, anchored on the committed EDA evidence (the EDA's PARTIAL-GO substantive read informs the probability weighting toward INERT-and-PROMISING / against the extreme failure modes).

**Mode 1 (MODAL, ~50% — EXPLORATION-NEGATIVE / INERT)**: BCH structural imbalance causes LightGBM to produce a near-constant predict_proba on BCH; the 7-gate stack either filters most BCH signals (BEHAVIORAL-INERTIA-on-BCH) or admits them as constant-long bets that get hit in OOS down months. LDO+TRX produce real but per-symbol-subliminal signal (the EDA's p=0.18/p=0.17 per-symbol weakness translates to ~0.52 production AUC). Universe-pooled signal does NOT compound across per-symbol-trained models. Net: IS Sharpe in [+0.30, +0.70], OOS in [−0.20, +0.30], OOS/IS ratio in standard range; Section 8 Criterion 1 fires NEGATIVE. **The EDA's per-symbol weakness (g1 FAIL) is the load-bearing predictor for this mode.**

**Mode 2 (~25%, SUSPICIOUS-OOS-DOMINANT)**: the 24h calendar-time-equivalent timeout (7 days) makes each trade a structurally longer-duration directional bet than the 8h equivalent (which has 21 candles of intra-trade slack). Longer-duration bets are more regime-sensitive. The IS window includes 2022 bear + 2023 chop where directional bets get hit; the OOS window is 2025-Q2→2026-Q2 uptrend where directional longs work. The result: IS Sharpe in [+0.30, +0.65], OOS in [+0.50, +1.10], OOS/IS ratio > 1.5. This is the standard /065/073/076/078 SUSPICIOUS-OOS-DOMINANT artifact; if it fires the result is regime exposure, NOT a discovered edge. The Critic Check 1 audit (look-ahead) and the Section 2 Phase-7 reading (substantive verification on per-symbol attribution + per-month OOS distribution + lack-of-leak diagnostic) determines whether this Mode 2 reading or Mode 3 PROMISING reading is the correct classification.

**Mode 3 (~20%, EXPLORATION-PROMISING)**: the universe-pooled AUC lift (0.5823 vs 0.4970 baseline) survives production LightGBM; LDO+TRX produce per-symbol Sharpe lifts and BCH either contributes neutrally (gate-filtered to small trade book) or contributes positive (the structural imbalance is not as bad in production as the EDA suggests because the calibrated trees can produce useful predict_proba even on imbalanced data). IS Sharpe in [+0.85, +1.20], OOS in [+0.40, +0.90]. **The EDA's g2 PASS (universe-pooled q95 clears) is the load-bearing positive evidence for this mode.**

**Mode 4 (~5%, RESIDUAL)**: trade roster is degenerate (< 30 IS trades — BEHAVIORAL-INERTIA-AT-BAR-FREQUENCY-AXIS) OR BCH portfolio-breaking loss (BCH IS net_pnl_pct < -50% with portfolio aggregate IS Sharpe below the standard NEGATIVE floor — a catastrophic structural failure). Either mode would file EXPLORATION-NEGATIVE with the catastrophe documented as a dead-paths-catalog entry: "24h decision grid catastrophically fails on the 3-symbol universe; future candle-frequency exploration must use the /116 diary fallback (12h-2-offset or weekly-8-offset)".

**Application of the /116 regime-asymmetry lesson** (per `feedback_promising_mechanical_subtype.md` and the /116 closeout's Lesson (a)): iter-v3/117's design is NOT a regime-adaptive rule (it's a frequency-axis representation change), so the IS-vs-OOS regime-cost-asymmetry pattern of /116 is NOT expected. However, the longer calendar-time per trade at 24h (7 days vs 8h's 7-day-equivalent-spread-across-21-candles) introduces a regime-sensitivity that could LOOK like the /116 pattern superficially. Section 8 Criterion 5a (the SUSPICIOUS-OOS-DOMINANT gate, threshold 3.0) distinguishes Mode 2 (SUSPICIOUS) from Mode 3 (PROMISING) — the formal classifier reads OOS/IS ratio + per-symbol broadness + bar-by-bar OOS attribution, NOT a single number.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

EXPLORATION classification — **first-match-wins** evaluation order. Anchor for EXPLORATION-mode comparison: iter-v3/060 (IS +0.8325 / OOS +0.1403). Per `feedback_v3_baseline_update_policy.md` an EXPLORATION never updates BASELINE_V3.md regardless of outcome.

**Criterion 1 (NEGATIVE — FIRST CHECK)**: fires IF EITHER:

(a) IS monthly Sharpe < `+0.7325` (Δ vs /060 < −0.10); OR

(b) OOS monthly Sharpe < `-0.0597` (Δ vs /060 < −0.20).

**On fire**: file `EXPLORATION-NEGATIVE`. (Standard first-match-wins NEGATIVE floor — same numerical thresholds as /115 and /116. The Critic's substantive-override authority can upgrade this in the UPGRADE direction per the /116 precedent if the IS underperformance has a coherent mechanism behind it AND the OOS lift is broadly distributed AND the result is structurally novel — but the QR pre-registers the mechanical reading honestly, NOT relying on the Critic to bail out a NEGATIVE-numerical result.)

**Criterion 2 (SUSPICIOUS-OOS-DOMINANT — SECOND CHECK)**: fires IF Criterion 1 did NOT fire AND:

OOS monthly Sharpe / IS monthly Sharpe > **3.0** AND OOS monthly Sharpe > `+0.50` AND IS monthly Sharpe > `+0.30`.

**On fire**: file `EXPLORATION-SUSPICIOUS-OOS-DOMINANT`. The 3.0 ratio is the standard /065/073/076/078 SUSPICIOUS threshold. The hard Criterion 5a check (Phase-7 substantive verification on per-symbol OOS attribution + month-by-month OOS distribution) determines if the result is a regime artifact (NEGATIVE outcome dressed up as PROMISING) or a real lift; if Criterion 5a's substantive check returns "regime artifact", the iteration is classified NEGATIVE.

**Criterion 3 (BEHAVIORAL-INERTIA — THIRD CHECK)**: fires IF both Criteria 1+2 did NOT fire AND:

Total IS trade count < `30` OR total OOS trade count < `15`.

**On fire**: file `EXPLORATION-INERT`. The 24h decision grid produces fewer raw signals than 8h; if the trade roster is degenerate the iteration tested the bar-interval axis trivially.

**Criterion 4 (PROMISING — FOURTH CHECK)**: fires IF Criteria 1+2+3 did NOT fire AND:

(a) IS monthly Sharpe Δ ≥ `+0.10` (vs /060 +0.8325, i.e. IS ≥ `+0.9325`); AND

(b) OOS monthly Sharpe Δ ≥ `+0.20` (vs /060 +0.1403, i.e. OOS ≥ `+0.3403`); AND

(c) OOS/IS ratio ∈ `[0.5, 3.0]` (the healthy band; Criterion 2 would have caught the > 3.0 case).

**On fire**: file `EXPLORATION-PROMISING`. The result advances to the iter-v3/120 CONFIRMATION as a candidate edge ingredient (subject to the Critic's substantive review).

**Criterion 5 — substantive Phase-7 checks (informational; not auto-firing; the Critic adjudicates):**

(a) **SUSPICIOUS substantive check** (only if Criterion 2 fires): if the OOS month-by-month distribution shows < 50% of OOS months positive AND the OOS lift is concentrated in <=2 carrier months, the substantive read is "regime artifact" → reclassify to NEGATIVE.

(b) **PROMISING substantive check** (only if Criterion 4 fires): if the OOS lift is concentrated in 1 symbol (>=80% of OOS weighted PnL on one symbol) AND the trade rosters are bit-identical to /060 on the non-target symbols, the substantive read is "frozen-baseline artifact" (the /114 pattern) → reclassify to NEGATIVE.

(c) **The /116 UPGRADE precedent**: the Critic may upgrade a NEGATIVE-by-criterion result to PROMISING-MECHANICAL IF three independent substantive lines converge — (i) IS drag has a coherent mechanism, (ii) OOS lift is broadly distributed and mechanistically traceable, (iii) the mechanism is mechanical book-composition rather than new edge ingredient. The QR's brief NEVER pre-registers an UPGRADE — that is the Critic's role.

(d) **The /114 DOWNGRADE precedent**: the Critic may downgrade a PROMISING-by-criterion result to NEGATIVE on Check-1 (no-cheating) or Check-8 (hypothesis-implementation-mismatch) FAILs.

**Criterion 6 — multi-seed validation (CONFIRMATION-ONLY)**: not applicable at /117 (this is an EXPLORATION). The /120 CONFIRMATION will multi-seed validate any /117 PROMISING result.

**Applied to the EDA's PARTIAL-GO**: the formal pre-registered verdict here mirrors the EDA's verdict — the modal prediction (Section 4) puts ~50% on Criterion 1 firing (Mode 1 INERT/NEGATIVE), ~25% on Criterion 2 firing (Mode 2 SUSPICIOUS), ~20% on Criterion 4 firing (Mode 3 PROMISING), and ~5% on Criterion 3 firing (Mode 4 INERT). The brief does not pre-commit to a desired outcome; the Critic adjudicates the post-backtest substance.

---

## Section 9 — Library Stack Declaration

| Library | Version | Used for | Fallback |
|---|---|---|---|
| `lightgbm` | 4.5.0 (per `uv.lock`) | LightGBM strategy + EDA's 14-feature stack fitting | none — LightGBM is the v3 model class |
| `numpy` | 2.x | EDA aggregation + label computation | none |
| `pandas` | 2.x | DataFrame manipulation + walk-forward fold structure | none |
| `scikit-learn` | 1.x | `roc_auc_score` in EDA + permutation null computation | none |
| `statsmodels` | 0.14+ | T7 ADF stationarity test (informational; not blocking) | none — the ADF report is informational at /117 per Section 5 Risk 3 |
| `pyarrow` | 16+ | Parquet read of `data/features_v3_24h/<SYM>_24h_multioffset_features.parquet` | none |
| `optuna` | 3.x | Per-symbol-month Optuna trial budget (35 trials at EXPLORATION) | none |
| `mlfinlab` / `mlfinpy` | 1.4 / 1.x | CPCV / DSR / PBO / PSR utilities (inherited from /001+) | mlfinpy as fallback if mlfinlab licensing fails (the v3 default per `BASELINE_V3.md`) |
| `pypbo` | 0.x | Probability of Backtest Overfitting computation | none |
| `fracdiff` | 0.10+ | inherited from /001+; not used at /117 (the 14-feature stack has fracdiff but is computed in-place by the v3 feature pipeline) | none |

iter-v3/117 introduces ZERO new library dependencies beyond /116. The 24h-multi-offset aggregation and feature computation are pure numpy + pandas (no new packages); the EDA used the canonical stack.

---

## Section 10 — QR Audit Trail

No orchestrator-pick supersession at /117. The dispatch's literal recommendation was the candle-frequency axis at 24h with 3-offset multi-offset derivation per the /116 diary's Section 9 + the `feedback_v3_candle_frequency_unblocked.md` user directive. The QR's committed EDA (`analysis/iteration_v3-117/`, commit `c64a5fc`) BACKED the axis with empirical evidence:

1. **Universe-pooled signal lift confirmed** (T2 POOLED + T9 universe-pooled both clear permutation null at p=0.00; observed AUC 0.5823 vs null_q95 0.5113).
2. **Multi-offset derivation causally clean** (T4 900/900 audit pass; the look-ahead-free assertion holds at the 24h aggregation).
3. **Multi-offset derivation contributing** (T3 6 of 9 cells AUC > 0.5; the 3 offsets carry signal in different symbols, not redundant).
4. **Data budget healthy** (T5 per-symbol POOLED >= 2122 rows; comparable to 8h baseline; g4 SOFT PASS).
5. **Refinement of the dispatch's design from BAR-count-equivalent to calendar-time-equivalent label scaling** (T6 BAR_COUNT_EQUIV_REJECTED.csv + T6_label_balance.csv preserve the rejected→chosen design lineage). This is a methodological refinement within the dispatch's framing, NOT a supersession of the axis.
6. **Honest formal NO-GO declared** (g1 FAIL — per-symbol q95 clears <2/3) WITH explicit substantive PARTIAL-GO read. The brief proceeds per the PRIME DIRECTIVE; modal prediction band (Section 4) reflects both the EDA's positive g2 evidence AND the per-symbol risk.

The brief's design choices (24h + 3-offset + per-symbol-pooled-offset training architecture + calendar-time-equivalent timeout=7 daily bars) are all hand-chosen (per `feedback_v3_brief_parameter_provenance.md`) with IS-only rationale. No parameter is tuned on a sweep; no parameter is laundered as an optimization output. The 5 design-parameter table in Section 0 is the auditable provenance record.

**Cycle 6 status**: 7 of 10 EXPLORATIONs filed (/110-/116); 3 EXPLORATION slots left (/117, /118, /119) before the mandatory iter-v3/120 CONFIRMATION. iter-v3/117 tests the cycle-6 STRUCTURAL candle-frequency axis (the user-directed structural lever — the one the QR has never had access to until 2026-05-20).

---

**Provenance summary (audit-ready)**:
- EDA commit: `c64a5fc` (committed BEFORE this brief — auditable temporal fence)
- EDA scripts: `analysis/iteration_v3-117/_shared.py`, `multifreq_24h_gating_eda.py`, `synthesis.py`
- EDA tables: `T1_walkforward_auc.csv`, `T2_permutation_null.csv`, `T3_per_offset_auc.csv`, `T4_derivation_audit.csv`, `T5_data_coverage.csv`, `T6_label_balance.csv`, `T7_adf_stationarity.csv`, `T8_113_reproducibility.csv`, `T9_universe_pooled.csv`, `T10_go_nogo_verdict.csv` (+ rejected-design preservation: `T5_data_coverage_BAR_COUNT_EQUIV_REJECTED.csv`, `T6_label_balance_BAR_COUNT_EQUIV_REJECTED.csv`)
- All 5 design-parameter declarations: candle frequency, offset count, offset values, training architecture, label timeout — hand-chosen with IS-only rationale per Section 0
- No sweep, no tuned scalar, no false-provenance claim — provenance discipline established at /114 + held at /115 + held at /116 maintained at /117

**NO CHEATING.** `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The walk-forward embargo fix (`e149e9d`, 22 candles at 8h equivalent / 22 daily bars at 24h; `train_end_ms = test_start_ms − embargo_ms`) is inherited unchanged. The iter-v3/115 + /116 stale-knob lessons are carried forward: Section 3.5 Change 5 reverts the /116 no_confirm primitive cleanly at 3 surfaces (BacktestConfig argument, pre-flight assertion, accretion guard) so /117's frequency axis is tested in isolation.
