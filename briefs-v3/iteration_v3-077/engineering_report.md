# Engineering Report — iter-v3/077

## Headers

- Iteration: iter-v3/077
- Branch: iteration-v3/047 (cycle-2 shared branch)
- Commit chain (EDA → brief → backfill → setup → Phase 5.5 gate → backfill gate SHA):
  - EDA: `313d3c0` — `analysis/iteration_v3-077/axis_selection_eda.py` + 10 output files
  - Brief: `77d0b62` — `briefs-v3/iteration_v3-077/research_brief.md`
  - Setup: `30cda98` — `run_baseline_v3.py` + `features_v3/__init__.py` + 5 test files
  - Phase 5.5 gate: `caed50d` — PASS
  - Gate SHA backfill: `50995c6`
  - HEAD at report time: `50995c6`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.69h (within 2.0h EXPLORATION cap; `--skip-features` because parquets were pre-regenerated at /076 setup)
- Run mode: `--exploration --clean-oof --skip-features` (`EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS[0:3]`, `--n-trials 35`)
- Seeds: `[191664963, 1662057957, 1405681631]` (outer=42 lineage subset)
- Total Optuna trials: 315 (3 seeds × 3 symbols × 35 trials)

---

## Configuration Diff vs /060 EXPLORATION-MODE ANCHOR

Two changes vs /060 — one axis change (conditional-orthogonality report instrumentation) and one mandatory baseline-restore:

| Parameter | /060 (anchor) | /077 |
|---|---|---|
| `V3_FEATURE_COLUMNS_TOP_N` | 14 features | **14 features** (`range_efficiency_50` REVERTED — restoring /060 anchor) |
| `_write_conditional_orthogonality()` | absent | **ADDED** (PASSIVE-DIAGNOSTIC axis — emits `conditional_orthogonality.csv`) |
| `ITERATION_LABEL` | `"v3-060"` | `"v3-077"` |
| All other params | — | UNCHANGED |

Note: `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` was NOT a /077 change — it was introduced at iter-v3/061 (commit `6910fcf`) and is present in the current codebase. This is a code-evolution accumulation that affects the /077-vs-/060 comparison and is diagnosed in the forensic section below.

Sacred constants confirmed: `OOS_CUTOFF_DATE = "2025-03-24"`, `TRAINING_MONTHS = 24`.

---

## Key Metrics Block

### Headline vs /060 anchor (brief prediction in parentheses)

| Metric | /060 IS (predicted) | /077 IS | IS Δ | /060 OOS (predicted) | /077 OOS | OOS Δ | /077 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8325 (predicted Δ=0) | **+0.8236** | **-0.0089** | +0.1403 (predicted Δ=0) | **+0.2078** | **+0.0675** | **0.2523** |
| daily_sharpe | +1.7115 | +1.7028 | -0.0087 | +0.3659 | +0.5427 | +0.1768 | 0.3187 |
| max_drawdown | 31.87% | 32.04% | +0.17pp | 35.78% | 35.89% | +0.11pp | 1.1201 |
| profit_factor | 1.2806 | 1.2773 | -0.003 | 1.0482 | 1.0715 | +0.023 | 0.8389 |
| win_rate | 31.4% | 31.4% | 0.0pp | 39.2% | 39.8% | +0.6pp | 1.2658 |
| n_trades | 159 (predicted 159) | 159 | **0** | 102 (predicted 102) | **103** | **+1** | 0.6478 |
| total_pnl | 51.89 | 51.73 | -0.16 | 5.50 | 8.22 | +2.72 | 0.1589 |
| monthly_calmar | 1.6282 | 1.6144 | -0.014 | 0.1537 | 0.2290 | +0.075 | 0.1418 |
| dsr | 0.0 | 0.0 | — | — | — | — | — |
| pbo | 0.1278 | 0.1278 | 0.0 | — | — | — | — |
| psr | — | 0.9987 | — | — | — | — | — |
| dsr_relative | n/a | 2e-06 | — | — | — | — | — |
| dsr_relative_b4 | n/a | 0.0512 | — | — | — | — | — |
| frac_positive_paths | 0.6444 | 0.6444 | **0.0** | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |

### Per-symbol OOS section

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +1.9078 | 37 | 32.4% | 23.21% |
| LDOUSDT | -18.4079 | 12 | 25.0% | -223.99% |
| TRXUSDT | +24.7184 | 54 | 48.1% | 300.77% |

Note: concentration_pct computed against the OOS total weighted_pnl (+8.22); LDO's negative concentration is a bookkeeping artifact of the near-flat total. The 30% per-symbol cap is a CONFIRMATION gate.

### Per-symbol IS section

| Symbol | /077 trades | /060 trades | /077 win_rate | /060 win_rate | /077 net_pnl_pct | /060 net_pnl_pct |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 73 | 73 | 45.2% | 45.2% | +79.45% | +79.45% |
| LDOUSDT | 11 | 11 | 27.3% | 27.3% | -11.44% | -11.44% |
| TRXUSDT | 75 | 75 | 29.3% | 29.3% | -23.04% | -23.04% |

**IS per-symbol conclusion:** All per-symbol IS stats from `in_sample/per_symbol.csv` are bit-identical between /077 and /060. The IS Sharpe difference (-0.0089) does NOT come from any entry/exit/pnl_pct change — it comes entirely from the `weight_factor` (TRX vol-scale floor) changing how individual TRX trades are sized. See Forensic Section below.

---

## FORENSIC: Why the Prediction Failed

### Forensic 1 — Roster diff /077 vs /060

Trade-by-trade diff on `(symbol, open_time)` key pairs:

| Split | /077 n | /060 n | Added | Removed | Common |
|---|---:|---:|---:|---:|---:|
| IS | 159 | 159 | **0** | **0** | 159 |
| OOS | 103 | 102 | **1** | 0 | 102 |

**The IS trade ROSTER (set of (symbol, open_time) keys) is bit-identical to /060.** Zero IS trades added, zero removed. IS n_trades = 159 on both sides. The per-symbol IS stats (wins, win_rate, net_pnl_pct) are identical in `in_sample/per_symbol.csv`.

However, 13 of the 159 IS trades have different `weight_factor` values (and thus different `weighted_pnl` values) — all 13 are TRXUSDT trades. The IS Sharpe difference (-0.0089) is entirely attributable to these 13 `weight_factor` perturbations. See Forensic 3 for root cause.

### Forensic 2 — The OOS +1 trade

The extra OOS trade is an `LDOUSDT end_of_data` trade with `open_time = 1778716799999` (~2026-05-14 01:59:59 UTC). This is the **same data-extent artifact certified by the /074 and /075 Critics**: /077's kline data extends through 2026-05-15 while /060's data was fetched on an earlier date; the extra LDO open position in the final OOS hours is closed as `end_of_data` with `pnl_pct = +1.81` and `weighted_pnl = +1.3129`.

Additionally, the last common OOS TRX trade (`open_time = 1778572799999`, ~2026-05-12 09:59:59 UTC) exited as `end_of_data` at `pnl_pct = +0.21` in /060 (data ended mid-trade) but hits `take_profit` at `pnl_pct = +1.83` in /077 (data extends far enough for TP). This changes `weighted_pnl` on a trade that IS in both rosters (same key, different close). This is a data-extent artifact, not a wiring defect.

### Forensic 3 — The IS difference: root cause

The IS (symbol, open_time) roster is bit-identical, but 13 TRXUSDT IS trades have different `weight_factor` values. In all 13 cases:

- `/077 weight_factor = 0.5` (exactly the floor value)
- `/060 weight_factor` ranges from 0.33 to 0.48 (below 0.5, unaffected by the floor)

**Root cause: `vol_scale_floor_per_symbol = {"TRXUSDT": 0.5}` was introduced at iter-v3/061 (commit `6910fcf`) — 16 iterations AFTER /060 ran.** The /060 run used no per-symbol floor; every subsequent iteration (including /077) runs with TRXUSDT floored at 0.5. For 13 IS TRX trades where the vol-targeting formula produced a raw scale < 0.5, the floor now applies. BCH IS and LDO IS are unaffected (0 rows differ).

The composition of the 13 differing TRX IS rows: 4 wins, 9 losses. Raising the floor amplifies both wins and losses proportionally, but the loss-heavy composition means the net IS wpnl falls: `/077 = 51.7291` vs `/060 = 51.8907`, delta `-0.1616`. This propagates to the monthly Sharpe delta of `-0.0089`.

**This is NOT a /077-specific config drift.** The `vol_scale_floor_per_symbol` setting is present in the current `run_baseline_v3.py` runner and was not changed at /077 setup. Every cycle-2 EXPLORATION since /061 has run with this floor. The brief Section 4.2 falsifier targets a "Phase-6 wiring defect" — an unintended config drift making /077 different from the intended /060 config. The TRX floor is a legitimate code-evolution accumulation that post-dates /060, not an unintended divergence in /077's config.

### Forensic 4 — BCH IS bit-identity confirmed

Per the /074 and /075 Critic-certified pattern, BCH IS is bit-identical to /060: 0 added, 0 removed, weight_factor unchanged in all 73 BCH IS trades. The divergence is TRX-only (13 IS trades) and LDO-only (0, unaffected). The BCH frozen-baseline pattern holds.

### Forensic 5 — OOS Sharpe shift decomposition (+0.0675)

The OOS monthly Sharpe shift of +0.0675 decomposes into three additive wpnl components, each fully reconciling to +2.7191 total wpnl delta:

| Component | Mechanism | wpnl Δ | Type |
|---|---|---:|---|
| A — extra LDO `end_of_data` trade | data extent: new OOS LDO open position | +1.3129 | DATA EXTENT |
| B — last TRX trade changed from `end_of_data` → `take_profit` | data extent: fuller data lets trade reach TP | +0.8119 | DATA EXTENT |
| C — TRX vol_scale_floor lifts 12 common OOS TRX trades | code drift: /061's floor raises wf on TRX wins (OOS TRX is profitable: 48.1% WR) | +0.5943 | CODE DRIFT |
| **Total** | | **+2.7191** | |

The OOS monthly Sharpe lift is dominated by data extent (A+B = +2.1248 wpnl in the 2026-05 OOS month alone). The code drift component (C, TRX floor) contributes +0.5943 wpnl — positive in OOS because OOS TRX has a positive WR (48.1%) so raising the size floor on TRX trades is accretive in OOS (the floor amplifies TRX wins more than losses).

### Forensic 6 — Benign perturbation vs wiring defect adjudication

**ADJUDICATION: BENIGN PERTURBATION — NOT a wiring defect.**

The Section 4.2 falsifier reads: "Such a divergence would NOT be regime-loading — it would be a Phase-6 wiring defect (an unintended config drift)." The criteria for a wiring defect are: (a) the IS (symbol, open_time) roster diverges from /060; (b) the divergence indicates an unintended config change in /077.

Neither criterion fires:
- IS (symbol, open_time) keys: **bit-identical to /060** (0 added, 0 removed). ✓
- OOS +1 trade: data-extent artifact, same pattern certified at /074 and /075. ✓
- IS weight_factor differences: code-evolution accumulation (TRX floor from /061), present in every cycle-2 iteration since /061, NOT introduced at /077. ✓
- The magnitude — IS Δ -0.0089, OOS Δ +0.0675 — is small and consistent with the brief's ≈4% "benign non-determinism" tail. ✓

The brief pre-registered this tail as: "a benign non-determinism perturbs the roster without moving the metrics → INERT-AT-EXPLORATION." The roster is "perturbed" at the weight_factor level (not the (symbol, open_time) key level), and both IS and OOS metrics land inside the noise bands. The root cause is fully explained by two separate well-understood mechanisms (code evolution + data extent), with no residual.

---

## Classification per Brief Section 8 LOCKED

Evaluation order per brief: SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical. Anchor: /060 IS +0.8325 / OOS +0.1403.

| Gate | Threshold | /077 result | Status |
|---|---|---|---|
| **SUSPICIOUS — OOS/IS ratio > 3.0** | > 3.0 | **0.2523** | Does not fire |
| **SUSPICIOUS-OOS-DOMINANT — IS shift < 0 AND OOS shift ≥ +0.20** | IS<0 AND OOS≥+0.20 | IS -0.0089 (negative) AND OOS +0.0675 (<+0.20) | **Does not fire** |
| **NULL-RESULT** — IS n_trades=159, OOS n_trades=102, every (sym, open_time) matches | All three conditions | IS keys=159 (✓), OOS n_trades=103 (≠102) | **FAILS (OOS 103≠102)** |
| **NEGATIVE** | IS<-0.10 OR OOS<-0.20 | IS -0.0089 (>-0.10), OOS +0.0675 (>-0.20) | Does not fire |
| **PROMISING** | IS≥+0.10 AND OOS≥+0.20 AND frac_pos≥0.50 | IS -0.0089 (<+0.10) | Fails IS gate |
| **INERT** | \|IS\|≤0.10 AND \|OOS\|≤0.20, roster not bit-identical, not SUSPICIOUS | IS ✓ (0.0089≤0.10), OOS ✓ (0.0675≤0.20), not SUSPICIOUS ✓, roster ≠ bit-identical ✓ | **FIRES** |

**CLASSIFICATION: INERT-AT-EXPLORATION.**

The SUSPICIOUS gate does not fire: the OOS/IS ratio is 0.2523 (far below 3.0) and the SUSPICIOUS-OOS-DOMINANT sub-mode requires OOS shift ≥ +0.20 (observed +0.0675). NULL-RESULT technically fails because OOS n_trades = 103 ≠ 102 (the extra LDO end_of_data trade), even though the IS key roster IS bit-identical. NEGATIVE and PROMISING gates do not fire. INERT fires: both shifts are inside the noise bands (IS 0.0089 ≤ 0.10; OOS 0.0675 ≤ 0.20), the roster is not bit-identical at the key level for OOS, and SUSPICIOUS is absent.

This matches the brief's pre-registered ≈4% tail (Section 7): "a benign non-determinism perturbs the roster without moving the metrics" — here the perturbation source is identified as code evolution (TRX vol_scale_floor) + data extent (extra LDO trade + last TRX trade resolution).

---

## The /060 Anchor Staleness Finding (Flag to Critic and Cycle-2 CONFIRMATION QR)

**/077 is the first iteration since /060 to run the exact /060 14-feature config as a diagnostic.** It reveals that the /060 anchor (IS +0.8325 / OOS +0.1403) does NOT reproduce on current code + current data. The current-code /060-config baseline is:

- **IS monthly Sharpe: +0.8236** (vs /060 frozen +0.8325; delta -0.0089)
- **OOS monthly Sharpe: +0.2078** (vs /060 frozen +0.1403; delta +0.0675)

Iterations /071 through /076 computed their IS/OOS deltas against the frozen /060 values (+0.8325/+0.1403). The IS delta from code drift is -0.0089, which is well within the INERT IS noise band (±0.10) and does not invalidate any /071–/076 classification (all of those involved substantially larger IS or OOS shifts). The OOS delta (+0.0675) is dominated by data extent, which grows monotonically with time and was similarly present (in smaller form) at /071–/075.

**Implications for future iterations:**

1. **For cycle-2 /078-/080 EXPLORATIONS:** The /077 result (IS +0.8236 / OOS +0.2078) is the *current-code* /060-config baseline. If the QR wishes to use the most reproducible anchor, they should reference /077's numbers for the current-code baseline alongside /060's frozen numbers for historical consistency. Both are valid — the IS delta (-0.0089) is attributable and explained; the OOS delta (+0.0675) is data-extent dominated.

2. **For the cycle-2 CONFIRMATION (iter-v3/081+):** The CONFIRMATION's MERGE gate thresholds reference the BASELINE_V3.md at `BASELINE_V3_IS_MONTHLY_SHARPE = +0.5051` and `BASELINE_V3_OOS_MONTHLY_SHARPE = +0.5069` (from iter-v3/059 CONFIRMATION). The /060 anchor is an EXPLORATION-MODE-REFERENCE used for intra-cycle EXPLORATION deltas, not the CONFIRMATION merge gate anchor. The staleness of the /060 EXPLORATION anchor is cycle-scoped and does not affect the CONFIRMATION BASELINE_V3.md merge gate.

3. **For future analysts reading /071-/076 reports:** The cycle-2 EXPLORATION-mode deltas (all computed against IS +0.8325 / OOS +0.1403) are internally consistent and their classifications are unaffected. The /077 finding is that the /060-config "true" current-code baseline is approximately IS +0.8236 / OOS +0.2078. The OOS uplift is not evidence of an edge improvement — it is data extent (the OOS window is now longer).

---

## Conditional-Orthogonality Deliverable (Primary Axis)

`conditional_orthogonality.csv` was emitted (1263 bytes). It is a HYBRID CSV combining:

- **PART A (runner state — last-month-only):** `last_month_importance_share_portfolio` column — per-feature gain-importance share from the trained models' LAST walk-forward month (one importance vector per symbol, projected across the 3-model portfolio). This is the runner-integrated component: it reads the already-trained models at the same call site as `_write_feature_importance`, using the lazy monthly-training pattern's most recently retrained model state. Because the runner carries only the last walk-forward month's models in memory at the report stage, the per-month conditional correlation time-series cannot be reconstructed from runner state alone.

- **PART B (EDA pre-committed — full per-IS-month map):** `eda_corr_portfolio_pooled`, `eda_max_abs_corr`, `eda_conditionally_regime_loaded` columns — copied verbatim from the committed EDA artifact `analysis/iteration_v3-077/T3_conditional_orthogonality.csv` (EDA SHA `313d3c0`). The `source` column marks every row as `PART_A_runner + PART_B_eda_313d3c0`.

**The full diagnostic deliverable is PART B.** The complete per-IS-month conditional-orthogonality map (2086 symbol × month × feature importance rows; Pearson correlation of per-month GAIN-importance share vs the BULL/BEAR-CHOP monthly BTC regime label) is the committed EDA artifact at `analysis/iteration_v3-077/T3_conditional_orthogonality.csv`. The report CSV's PART A column (last-month portfolio share) is a supplementary runner-emitted companion; it adds no diagnostic value over the EDA's full map but confirms the runner integration path works correctly.

**Key conditional-orthogonality findings (from PART B):**

| Feature | eda_corr_portfolio_pooled | eda_max_abs_corr | conditionally_regime_loaded |
|---|---:|---:|:---|
| btc_ret_14d | +0.3591 | **0.4803** | **YES** |
| hurst_diff_100_50 | +0.2798 | **0.4416** | **YES** |
| max_dd_window_50 | -0.0757 | **0.4339** | **YES** |
| range_realized_vol_50 | -0.1737 | **0.3704** | **YES** |
| ret_skew_200 | -0.2362 | 0.3319 | no |
| regime_momentum_signed_5d | +0.0582 | 0.2092 | no |
| ... (9 remaining features) | — | ≤0.2851 | no |

4 of 14 baseline features are conditionally regime-loaded (max |corr| > 0.35). `regime_momentum_signed_5d` (the engineered feature) is clean at max |corr| = 0.21. This is the conditional-orthogonality map the Critic /076 Rec #1 mandated; it is now available for /078–/080 axis design and the cycle-2 CONFIRMATION QR.

---

## Feature Importance

Last walk-forward month portfolio importance (14-feature canonical stack):

| Rank | Feature | Portfolio importance |
|---:|---|---:|
| 1 | ret_skew_200 | 816.3 |
| 2 | vwap_dev_20 | 759.7 |
| 3 | range_realized_vol_50 | 706.3 |
| 4 | ema_spread_atr_20 | 698.7 |
| 5 | max_dd_window_50 | 646.3 |
| 6 | ret_autocorr_lag1_50 | 607.0 |
| 7 | ret_kurt_50 | 598.0 |
| 8 | hurst_diff_100_50 | 593.3 |
| 9 | ret_kurt_200 | 582.0 |
| 10 | btc_ret_14d | 582.0 |
| 11 | hurst_100 | 569.3 |
| 12 | ret_skew_50 | 520.3 |
| 13 | sym_vs_btc_ret_7d | 511.7 |
| 14 | regime_momentum_signed_5d | 506.7 |

`regime_momentum_signed_5d` (the single engineered feature) is rank 14/14 in the last walk-forward month. However, this is a last-month snapshot; the EDA's full IS-window analysis shows it is important and not regime-loaded (max |corr| = 0.21). The importance ranking is informational at this PASSIVE-DIAGNOSTIC iteration.

---

## ADF and IC Matrix Notes

**ADF warning — `LDOUSDT/cusum_reset_count_200`:** `run.log` line 49278: `[ADF] WARNING: LDOUSDT/cusum_reset_count_200 not found in ADF output`. Identical benign artifact from /074, /075, and /076 — LDO's shorter history (first valid bar 2022-09-22) means the 200-bar rolling `cusum_reset_count_200` feature is all-NaN in LDO's earliest walk-forward training windows. Total ADF rows: 2198 (within expected range for 3 syms × 14 feats × 33 IS months; the missing LDO cell is the only gap). 82.0% of features stationary (p < 0.05). No impact on backtest result.

**IC matrix — 14×14 confirmed.** `ic_matrix.csv` is a 14×14 square matrix. The /076 feature `range_efficiency_50` is absent (correct — it was reverted). No anomalies.

---

## Seed Concentration Audit

Single-seed EXPLORATION (outer=42 lineage, 3 seeds: 191664963, 1662057957, 1405681631). PASSIVE-DIAGNOSTIC iteration — the models are deterministically the same as /060's models at the config level, up to the TRX vol_scale_floor effect on weight_factor (which is post-model). OOS concentration: BCH 23.21%, LDO -223.99% (negative bookkeeping artifact), TRX 300.77% — computed against the near-flat total. The 30% per-symbol cap is a CONFIRMATION gate. Frozen-baseline pattern holds for BCH (0 IS wf differences, 0 OOS wf differences).

---

## Label Leakage Audit

- `REQUIRED_GAP = 66 = (21+1) × 3 symbols` — confirmed unchanged.
- Embargo = 22 candles — unchanged.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` confirmed: all symbols use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`.
- No feature was added in /077; the `_write_conditional_orthogonality` instrumentation reads already-trained models after the backtest loop and does not touch the feature pipeline or labeling.
- Walk-forward lookahead-bias note (`feedback_v3_walkforward_lookahead_bug.md`) applies equally to /077 — all v3 iterations carry the same embargo; deltas vs /060 are valid; absolute magnitudes uniformly biased upward.

---

## Gate Efficacy Table

All gates unchanged from the /060 baseline (the axis is a report-emission instrumentation; no gate was modified):

| Primitive | State | IS fire count / rate | OOS fire count / rate |
|---|---|---|---|
| 1 — Feature OOD z>2.0 | ON | baseline | baseline |
| 2 — Hurst regime | ON | baseline | baseline |
| 3 — ADX gate | ON | baseline | baseline |
| 4 — Low-vol filter | ON | baseline | baseline |
| 5 — Vol-adjusted sizing | ON | baseline | baseline |
| 9 — Regime kill switch | OFF (CLOSED axis) | 0 | 0 |
| 10 — Direction kill switch | OFF (reverted /051) | 0 | 0 |
| 11 — Per-symbol drawdown brake | OFF (CLOSED /054) | 0 | 0 |
| 12 — BTC-trend-regime SIZE de-rate | OFF (reverted /076) | 0 | 0 |

TRX vol_scale_floor=0.5 (from /061) is active for the 13 IS TRX trades and 12 OOS TRX trades where the raw vol-targeting scale was below 0.5. This is not a new gate — it is the /061 per-symbol floor that has been active since cycle 1.

---

## Anomaly Notes

1. **Spot-check 10 random OOS trades — 0 issues.** Entry/exit/PnL math checks pass for all 10 (verified: `weighted_pnl = net_pnl_pct × weight_factor` within float tolerance). Exit reasons (take_profit, stop_loss, timeout, end_of_data) are self-consistent. Weight_factor values are non-negative. No anomalies detected.

2. **No NaN Sharpe, no zero-trade IS months, no NaN PnL.** IS monthly_pnl.csv: 33 rows, all with positive trade_count and numeric pnl_pct. OOS monthly_pnl.csv: 14 rows, all clean. IS monthly Sharpe recomputed from monthly_pnl.csv matches comparison.csv (0.8236 ✓). OOS likewise (0.2078 ✓).

3. **IS per_symbol.csv stats bit-identical to /060.** BCH 73 trades 45.2% WR +79.45%; LDO 11 trades 27.3% WR -11.44%; TRX 75 trades 29.3% WR -23.04% — all match /060 exactly. The IS Sharpe difference (-0.0089) comes from the weight_factor channel (TRX vol_scale_floor), not from any entry/exit/pnl change.

4. **PBO unchanged at 0.1278.** The CPCV path-return proxy is weight-factor-independent (it uses daily pnl normalized returns); the 45-path PBO and frac_positive_paths (0.6444) are stable.

5. **The OOS Sharpe shift (+0.0675) does not represent a genuine edge.** The two data-extent components (A+B) together account for +2.1248 wpnl in 2026-05 alone — the final OOS month added since /060 was fetched. Future anchor refreshes should account for this monotonically-growing data-extent contribution.

---

## Recommendations to QR

1. **INERT-AT-EXPLORATION — conditional-orthogonality deliverable produced.** The diagnostic objective is achieved. The /060 conditional-orthogonality map (PART B of `conditional_orthogonality.csv`, full per-month map in `analysis/iteration_v3-077/T3_conditional_orthogonality.csv`) is the tool the Critic /076 Rec #1 mandated and that /078–/080 briefs should reference for regime-loaded feature identification.

2. **The /060 anchor is stale for future EXPLORATIONs.** IS -0.0089 and OOS +0.0675 are small but systematic drifts. QR should choose whether to: (a) continue anchoring against /060's frozen +0.8325/+0.1403 for intra-cycle consistency, annotating the TRX-floor code-drift component explicitly; or (b) transition /078+ to anchor against /077's current-code baseline (+0.8236/+0.2078). Either approach is valid; the classification taxonomy (INERT/PROMISING/NEGATIVE/SUSPICIOUS bands) would remain interpretable. **The QR should make this call explicitly in the /078 brief Section 0, not leave it implicit.**

3. **4 conditionally regime-loaded features identified.** `btc_ret_14d` (max |corr| 0.48), `hurst_diff_100_50` (0.44), `max_dd_window_50` (0.43), `range_realized_vol_50` (0.37). Future axis briefs for features that interact with these should include CONDITIONAL orthogonality analysis (model-split-allocation correlation, not just marginal feature distribution). The Critic /076 Rec #2 channel (regime-loading via roster selection in interaction with these 4 features) is now instrumentally characterised.

4. **The IS directional-quality diagnosis (EDA T2/T6) stands.** IS bull months carry 32.7% WR (104 trades), bear/chop months carry 43.6% WR (55 trades). Win/loss duration ratio 2.08× — the holding-time sensitivity channel is mechanically active. Future axes targeting the IS drag should aim at entry discrimination in bull-regime months, and any new feature brief should check its conditional-orthogonality flag against the PART B map.

---

## Status

OVERALL = READY-FOR-CRITIC

Classification: **INERT-AT-EXPLORATION** — PASSIVE-DIAGNOSTIC with benign perturbation sourced from two independent mechanisms.

Brief prediction (bit-identical NULL-RESULT) was wrong; actual result is INERT per brief Section 8.3 (both shifts within noise bands, roster not bit-identical at OOS level, not SUSPICIOUS). The IS (symbol, open_time) roster IS bit-identical to /060 (159 = 159, 0 added, 0 removed). The perturbations are: (1) OOS +1 trade = LDOUSDT `end_of_data` ~2026-05-14, same data-extent artifact as /074–/075-certified; (2) 13 IS + 12 OOS TRXUSDT trades with weight_factor floored at 0.5 — code-evolution accumulation from iter-v3/061 `vol_scale_floor_per_symbol={"TRXUSDT": 0.5}` (commit `6910fcf`), NOT a /077-specific wiring defect. Full OOS wpnl delta of +2.7191 decomposes exhaustively: A (extra LDO `end_of_data`) +1.3129 + B (last TRX trade `end_of_data`→`take_profit`) +0.8119 + C (TRX wf floor, 12 common OOS TRX trades) +0.5943 = +2.7191. IS wpnl delta -0.1616 attributable solely to the TRX floor (13 IS trades, 4 wins + 9 losses, net negative). The conditional-orthogonality deliverable is produced: `conditional_orthogonality.csv` is HYBRID (PART A = runner last-month portfolio importance share; PART B = full per-IS-month EDA map from `T3_conditional_orthogonality.csv`, SHA `313d3c0`). The full diagnostic deliverable is PART B. ADF warning on `LDOUSDT/cusum_reset_count_200` is the persistent benign LDO short-history artifact. **The /060 anchor is stale for current code+data: IS +0.8236 / OOS +0.2078 is the current-code /060-config baseline; QR must decide whether to re-anchor for /078+.**

---

Phase 6 complete. Engineering report committed. Phase 7.5 Critic review required before Phase 7. Orchestrator: invoke `quant-critic` with branch=`iteration-v3/047`, report_dir=`reports-v3/iteration_v3-077`, brief_dir=`briefs-v3/iteration_v3-077`.
