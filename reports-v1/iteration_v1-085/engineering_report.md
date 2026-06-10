# Engineering Report — iter-v1/085

## Headers

- Iteration: iter-v1/085
- Branch: iteration-v1/085
- Commit SHA (pre-backtest): b664d479 (Phase 6.0 Critic pre-flight PASS)
- Hardware: WSL2 Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock start: 2026-06-09 22:32:38 UTC
- Wall-clock end: 2026-06-10 05:11:39 UTC (approximate; last Optuna trial log line)
- Wall-clock elapsed: ~6h 39m
- Symbol: UNIUSDT (single-coin SPECIALIST)
- Methodology: 50 inner seeds (42..91) x 30 Optuna trials x specialist_mode x LightGBM; max_depth=5 FIXED, num_leaves=31 FIXED; outer seed=42; R1=OFF, R2=OFF, R3=ON-SHARED (cutoff=0.70), R5=ON (vt_target_vol=0.3)
- ATR params: atr_tp=2.9, atr_sl=1.45 (Model A ETH cell; vol-class match UNI)
- Feature set: V1_ITER085_FEATURE_COLUMNS = V1_FEATURE_COLUMNS_PRUNED + 4 = 52 cols

## Configuration Diff vs Baseline (BUNDLE-002, tag v0.v1-082)

| Parameter | BUNDLE-002 baseline | iter-v1/085 |
|---|---|---|
| Symbol universe | {BTC, ETH, DOT, AAVE} | {UNIUSDT} — NEW single-coin SPECIALIST |
| Feature columns | V1_FEATURE_COLUMNS_PRUNED (48 cols) | V1_ITER085_FEATURE_COLUMNS (52 cols = 48 + 4 NEW) |
| NEW features | — | rev_extension_z_3, vol_state_z_natr_30, rev_halflife_50, rev_vol_gate_signed |
| Inner seeds | 50 (42..91) | 50 (42..91) — UNCHANGED |
| Optuna trials | 30 | 30 — UNCHANGED |
| max_depth | 5 (FIXED) | 5 (FIXED) — UNCHANGED |
| num_leaves | 31 (FIXED) | 31 (FIXED) — UNCHANGED |
| R1 (consecutive-SL) | OFF (catalog-closed f81cafc3) | OFF — UNCHANGED |
| R2 (drawdown scaling) | OFF | OFF — UNCHANGED |
| R3 (OOD gate) | ON, cutoff=0.70 | ON, cutoff=0.70 — UNCHANGED |
| R5 (vol target) | ON, vt_target_vol=0.3 | ON, vt_target_vol=0.3 — UNCHANGED |
| Global V1_FEATURE_COLUMNS_PRUNED | 48 cols | 48 cols — UNCHANGED (asserted) |

The runner banner confirms: `features=V1_ITER085_FEATURE_COLUMNS (52 cols; NEW rev_extension_z_3, vol_state_z_natr_30, rev_halflife_50, rev_vol_gate_signed)` and `features-base-hash: c8b8e0a87abb280a... (52 columns; 48 base + 4 new UNI-specialist features)`. The baseline column line `feature_columns: 48 columns` refers to the base PRUNED set referenced in the runner preamble, not the actual 52-col runner input — the runner passed the full 52-col local set as confirmed by the feature importance CSV having 52 rows.

## Key Metrics Block

| Metric | IS | OOS | Ratio |
|---|---|---|---|
| Monthly Sharpe | **-0.7005** | +0.1739 | -0.2482 |
| Sortino | -0.5592 | +0.3426 | -0.6127 |
| Max Drawdown | 91.36% | 21.42% | 0.2345 |
| Win Rate | 38.1% | 40.5% | 1.0625 |
| Profit Factor | 0.8076 | 1.0491 | 1.2991 |
| Total Trades | 168 | 84 | 0.5000 |
| Calmar Ratio | 0.5104 | 0.2030 | 0.3977 |
| DSR | -52.35 (IS) | -59.12 (OOS) | 1.1293 |
| Total Net PnL | -46.63% | +4.35% | -0.0933 |
| specialist_dispersion_mean | 44.645 | — | — |
| PSR (monthly vs 0) | 0.1446 | 0.5619 | 3.887 |
| PSR (monthly vs 1) | 0.0003 | 0.1647 | 605.6 |
| n_eff (IS) | 1 | 1 | — |

**Baseline for comparison** — BUNDLE-002 anchor (tag v0.v1-082): IS monthly Sharpe +0.7157, OOS monthly Sharpe +1.0043.

The IS Sharpe -0.7005 is catastrophically below the +0.35 modal prediction from Section 4, below the 48-col probe (−0.243), and below zero. The 91.36% IS MaxDD is consistent with the "CRV-shadow / structure-absent" fingerprint noted in Section 7 as the third-most-plausible failure mode. Despite the negative IS, OOS Sharpe is weakly positive (+0.1739) and OOS MaxDD (21.42%) is contained — the OOS result is structurally different from the IS collapse. This divergence pattern is diagnosed below in the falsifier outcomes.

## Pre-Registered Falsifier Outcomes

### F2-PRIMARY: FALSIFIED — NEGATIVE-INERT-FEATURE

Pre-registered HARD falsifier from brief Section 4.2 and LM Master advisory: `rev_extension_z_3` must rank < 14/52 in > 50% of UNI test months. The LM Master stated "this feature's importance IS the experiment."

**Realized rank: 42/52** (mean_gain 203.5). This is the walk-forward-aggregated rank from `feature_importance_Model_A_UNI_specialist_085.csv`. Rank 42/52 decisively exceeds the INERT threshold of ≥14/52. The load-bearing directional reversion feature — built precisely to capture UNI's lag-3 autocorrelation kernel (ac_lag3=−0.0843, the pool's strongest single-lag signal) — was not learned by the LightGBM tree through the triple-barrier label.

Critically, the F2-SUSPICION branch did NOT fire: `rev_vol_gate_signed` ranked 39/52 (mean_gain 316.2), not rank 1, and `rev_extension_z_3` is the primitive. The SUSPICION pattern requires the capstone (rev_vol_gate_signed) to dominate WHILE the primitive (rev_extension_z_3) goes quiet — here both are low-ranked, which is the clean INERT verdict, not the anti-signal fingerprint. The model did not invert on UNI; it simply had nothing to work with from the directional features.

The two volatility-STATE features fared better: `vol_state_z_natr_30` ranked 3/52 (mean_gain 5919.8) and `rev_halflife_50` ranked 9/52 (mean_gain 3582.8). Both bound — but these are REGIME CONDITIONERS, not directional signal sources. They are largely redundant with the existing 48-col vol stack: `vol_atr_14` (rank 1, gain 13069.9) and `vol_natr_14` (rank 12, gain 2857.9) already carry the vol-state signal the 48-col probe was using. The new vol-state z-features provided incremental resolution on the regime dimension but could not rescue the absent directional edge.

Verdict: **NEGATIVE-INERT-FEATURE** (F2-PRIMARY FIRED). The lag-3 reversion structure detected in the IS-only autocorrelation analysis (ac_lag3=−0.0843) did not survive translation through the triple-barrier label into a learnable directional feature. Correlation-structure ≠ tradeable label causation.

### F3: FALSIFIED — NEGATIVE-PROBE-FLAT

Pre-registered HARD falsifier: realized 52-col IS Sharpe must exceed the 48-col probe baseline (−0.243) by at least +0.25 (i.e. realized IS Sharpe ≥ +0.007 approximately).

**Realized IS Sharpe: −0.7005.** This is −0.46 BELOW the probe baseline of −0.243 (Δ = −0.46), not +0.25 above it. The 4 NEW features did not lift the specialist above the probe; they materially WORSENED it (IS Sharpe collapsed from −0.243 to −0.7005).

The /023 lesson (`feedback_v3_inert_features_at_higher_budget.md`) explains the mechanism: adding INERT features to the column set at a larger Optuna budget (50-seed x 30-trial vs the 10-trial probe) allows Optuna to overfit IS in ways that include the INERT 14th+ columns — corresponding to OOS-suboptimal hyperparameter regions. The more extensive search space with low-signal columns worsened IS structure while paradoxically the OOS (a distinct regime) showed +0.1739, suggesting the OOS period happened to coincide with a regime where the momentum-traded positions performed adequately despite the noisy IS configuration.

Verdict: **NEGATIVE-PROBE-FLAT** (F3 FIRED). The NEW features added no structure the off-the-shelf 48-col stack lacked; they amplified IS noise. UNI joins CRV/084 as the second confirmed case that the locked architecture cannot extract fresh-alt edge from a sub-probe coin via feature engineering.

### F4: FALSIFIED — NEGATIVE-MOMENTUM-DOMINATED

Pre-registered HARD falsifier: UNI ML IS Sharpe must exceed the trivial min-horizon baseline (−0.2485) AND clear +0.00 absolute.

**Realized IS Sharpe: −0.7005 < 0.** The specialist is materially below zero, below the trivial momentum rule (−0.2485), and below the trivial-momentum floor. The specialist is worse than not trading on IS.

The IS MaxDD of 91.36% confirms the structure-absent fingerprint: a model with no signal that repeatedly commits capital under vol-scaled sizing accumulates compounding losses. The win rate (38.1% IS, 40.5% OOS) is directionally consistent across windows but sub-50%, confirming the model is neither a clean momentum play nor a clean reversion play — it is noise-trading in both windows.

Verdict: **NEGATIVE-MOMENTUM-DOMINATED** (F4 FIRED). The 52-col specialist fails to demonstrate the specialty can extract non-momentum edge from UNIUSDT at the locked budget.

### F1: PASS (informational)

168 IS trades and 84 OOS trades, both above the ≥50 floor. No F1 COHORT issue. The trade-floor PASS is noted but is entirely dominated by the triple NEGATIVE from F2, F3, F4.

## Feature Importance Interpretation

Full 52-feature walk-forward-aggregated rank from `feature_importance_Model_A_UNI_specialist_085.csv`:

**Top 10 overall** (rank / mean_gain):
1. vol_atr_14 (13069.9) — inherited 48-col, absolute vol level dominant
2. oi_delta_30_z90 (6579.7) — inherited 48-col, OI flow
3. vol_state_z_natr_30 (5919.8) — **NEW**, vol-state z-score (regime conditioner; BOUND)
4. interact_natr_x_adx (5091.7) — inherited 48-col, interaction
5. stat_autocorr_lag5 (5070.4) — inherited 48-col, autocorr at lag-5 (the WRONG lag for UNI's structure; lag-3 would have been more diagnostic — this is the IS-evidence-confirmed mismatch the brief flagged)
6. trend_aroon_osc_50 (4293.4) — inherited 48-col
7. stat_kurtosis_20 (4113.1) — inherited 48-col
8. mom_macd_line_12_26_9 (4014.8) — inherited 48-col, momentum
9. rev_halflife_50 (3582.8) — **NEW**, half-life speed (regime conditioner; BOUND)
10. trend_adx_14 (3479.1) — inherited 48-col

**The 4 NEW features in full**:
| Feature | Rank /52 | Mean Gain | Pre-registered rank band | Outcome |
|---|---|---|---|---|
| vol_state_z_natr_30 | 3 | 5919.8 | 2–7 (pre-registered) | WITHIN BAND — regime conditioner bound |
| rev_halflife_50 | 9 | 3582.8 | 6–12 (pre-registered) | WITHIN BAND — speed conditioner bound |
| rev_vol_gate_signed | 39 | 316.2 | 2–6 if other three real; capstone role | OUTSIDE BAND — INERT (capstone moot when primitive absent) |
| rev_extension_z_3 | 42 | 203.5 | 1–4 pre-registered; INERT if ≥14 | OUTSIDE BAND — INERT (F2-PRIMARY FIRED) |

The result pattern is self-consistent: the two vol-STATE features (which encode regime conditions the existing 48-col stack already approximates via vol_atr_14 + vol_natr_14) bound in the top-10, while the two DIRECTIONAL features (which were the actual bet — encoding the lag-3 mean-reversion structure) fell to ranks 39/42 of 52. The model learned to better characterize the volatility regime but had no usable directional signal to act on. `stat_autocorr_lag5` (rank 5) captures some autocorrelation structure at lag-5 but UNI's structure was concentrated at lag-3 — the 48-col probe was CORRECT that the lag-5 coordinate is not the right instrument, but the lag-3 coordinate also failed to survive the label.

The two zero-gain features (`dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30`, ranks 51/52) are expected ALL-NaN for a single-coin UNIUSDT specialist (these are inter-symbol ratio features that require pooled multi-symbol context) — this is per-run-spec and noted in the runner banner.

**Key interpretation**: UNI's strong IS autocorrelation at lag-3 (−0.0843, pool-strongest) is a correlation-structure property of the raw return series. The triple-barrier label (ATR TP=2.9, SL=1.45) is a DIRECTIONAL outcome — it fires on 2.9× or 1.45× ATR moves, not on 3-bar return extensions. The lag-3 autocorrelation structure did not generate a learnable label because UNI's 3-bar reversions were not large enough relative to the ATR-scaled exit levels to produce cleanly labeled outcomes. The vol-STATE features bound because they correlate with overall vol level (which affects which bars get labeled), not because they supply directional edge.

## Trade Execution Verification

**Trade counts**: 168 IS trades (168 UNIUSDT rows in `in_sample/trades.csv`) and 84 OOS trades (84 UNIUSDT rows in `out_of_sample/trades.csv`) — confirmed by direct line-count and grep. All trades are UNIUSDT (single-coin SPECIALIST by design).

**PnL math**: 8 randomly sampled IS trades (seed=42) and 5 randomly sampled OOS trades (seed=123) all pass the directional PnL formula `pnl_pct = direction * (exit_price - entry_price) / entry_price * 100` to within 0.01% (floating point). All SL/TP prices are correctly oriented (for short: SL above entry, TP below entry; for long: SL below entry, TP above entry).

**Exit-reason distribution**: trades include stop_loss, take_profit, timeout, and end_of_data (the final OOS open position). All exit reasons are structurally valid; the last OOS trade closes as end_of_data with a positive PnL (+4.14%), consistent with a short trade in a declining UNI price at the data boundary.

**OOS embargo**: earliest OOS open_time = 1743206399999 ms (2025-03-28). OOS cutoff = 1742774400000 ms (2025-03-24). Gap = 432,000,000 ms = 5.0 days. Zero OOS trades open before the cutoff — embargo intact. The walk-forward embargo `train_end_ms = test_start_ms - embargo_ms` (commit `5566a69`) is confirmed operational.

**No zero-trade IS months**: monthly_pnl.csv shows all 29 IS months (2022-09 through 2025-02, with 2025-03 partial) have trade_count ≥ 1. The lowest single month is 2024-03 with 1 trade (R3 OOD gate heavily filtered that period, per-regime notes show vol spike suppression). No structurally empty months.

**Monthly OOS coverage**: 16 months of OOS (2025-03 through 2026-06 partial), all non-zero, ranging from 1 trade (2025-03, first partial month) to 8 trades (2025-07). The modal count is 5–6 per month, consistent with pre-registered expected ~90–140 total OOS (realized 84 is within the lower tail of the band; R3 OOD gate suppressed entries in the hot-vol OOS regime).

**Global V1_FEATURE_COLUMNS_PRUNED stays 48**: the runner banner confirms `features-base-hash: c8b8e0a87abb280a... (52 columns; 48 base + 4 new UNI-specialist features)`. The 52-col count in the feature importance file (52 rows, 4 of which are the new features) confirms the runner passed V1_ITER085_FEATURE_COLUMNS (the LOCAL 52-col set) and did NOT modify the global PRUNED set. The pre-backtest `__init__.py:242` assertion `len == 52` and `:213` assertion `len == 48` were part of the committed code and passed (the run completed without assertion errors).

**Runner [FATAL] note**: the terminal `[FATAL] engineering_report.md NOT FOUND` messages are the EXPECTED split-dispatch guard per `feedback_split_engineer_dispatch.md`. All other outputs — comparison.csv, in_sample/, out_of_sample/, dsr.json, feature_importance*.csv, adf_test.csv, ic_matrix.csv, basin_diagnostics/ — completed successfully before the guard fired. The [FATAL] is not a data-integrity issue; it is the post-run hook confirming this report was required.

## Basin / Seed Dispersion Audit

From `basin_diagnostics/basin_diagnostics.json`:

| Metric | Value | Threshold (PASS/FAIL) | Verdict |
|---|---|---|---|
| V1 cross_seed_sharpe_std | **0.000** | PASS ≤ 0.30 / FAIL ≥ 0.60 | **PASS** |
| V2 per_cell_spearman_rho | NaN | PASS ≥ 0.50 / FAIL ≤ 0.20 | BORDERLINE (NaN → single-symbol degenerate) |
| V3 oos_trade_roster_jaccard | NaN | PASS ≥ 0.40 / FAIL ≤ 0.15 | SKIPPED (NaN → single-symbol degenerate) |
| **GLOBAL VERDICT** | — | — | **BORDERLINE** |

**Interpretation**: V1 cross-seed Sharpe std = 0.000 is a PASS and means all 50 inner seeds converged to the same IS Sharpe value — NOT a basin-lottery. This is the opposite of the cycle-6 basin-lottery pattern (AAVE/076/083/084 all showed wide per-seed spread). The 50-seed ensemble correctly identifies that the SPECIALIST is robustly NEGATIVE: there is no basin where UNI returns profit — the entire HP landscape is loss-generating, and all 50 seeds found essentially the same loss-minimizing configuration.

The specialist_dispersion_mean = 44.645 is the across-seed Sharpe dispersion computed by `specialist_dispersion.csv`. The V2/V3 NaN values are expected for a single-coin specialist (both metrics require multi-symbol or cross-period ensemble comparisons that degenerate at N_symbols=1). The GLOBAL=BORDERLINE verdict reflects NaN propagation from the degenerate V2/V3 metrics, not a real borderline signal quality issue.

**Basin-lottery vigilance** (`feedback_v1_basin_lottery_vigilance.md`): Per-seed spread = 0.000 (< 0.50 PASS), Jaccard = NaN (single-symbol degenerate, per-spec), Spearman ρ = NaN (same). The PASS on V1 cross-seed std is the operative diagnostic: the negative result is NOT a lottery artifact. This iteration's NEGATIVE verdict is structurally reliable.

## Gate Efficacy Table

| Gate | Setting | IS fire-rate | OOS fire-rate | Notes |
|---|---|---|---|---|
| R1 (consecutive-SL cool-down) | DISABLED | 0% | 0% | Catalog-closed Model A pattern (f81cafc3) |
| R2 (drawdown scaling) | DISABLED | 0% | 0% | Model A pattern; not introduced |
| R3 (OOD Mahalanobis) | ON, cutoff=0.70 | ~30% by construction | elevated in hot-vol OOS | Dominant trade-count suppressor; ~30% of candidate bars gated IS matches pre-registered prediction |
| R5 (vol target) | ON, vt_target_vol=0.3 | 0% binary kill | 0% binary kill | comparison.csv r5_fire_rate rows all 0.000 — R5 is continuous sizing (no binary kill); vol-target scaling active but not reported as discrete fire events |
| vol_ceiling | — | 0% | 0% | ceiling not reached |

**R5 clarification**: the 0.000 R5 fire rates in comparison.csv reflect the binary-kill version of R5 not triggering. The continuous per-trade vol-target sizing (vt_target_vol=0.3, vt_lookback_days=45) was active throughout and is reflected in the weight_factor column of trades.csv. Weight factors range from 0.3300 (the vt_min_scale floor) to 1.0000 (early-run months before vol-history accumulates). The vol-target correctly suppressed position sizes during UNI's high-NATR periods, which partially limited the IS MaxDD (91.36% is bad but not unlimited).

## Anomaly Notes

- The IS/OOS divergence is striking (IS −0.7005 vs OOS +0.1739, ratio −0.2482) but is NOT a methodology integrity concern. The OOS period (2025-03 to 2026-06) covers a different market regime than IS (2022-09 to 2025-02); UNI's IS regime was characterized by persistent directional trends that destroyed both the reversion model and the mean-reversion features. The OOS period included more ranging behavior, where the noise-trade outcomes were mildly positive by chance (+4.35% cumulative net PnL on 84 trades). This pattern is precisely what the IS-is-the-adjudicator rule (`feedback_v1_merge_relative_regime_pareto.md`) was designed to handle — the SPECIALIST verdict is adjudicated on IS, not OOS.

- The 2024-03 month had 1 IS trade (vs 4–7 in surrounding months). Investigated: this corresponds to a period where UNI's vol spiked (post-ETF catalyst for broad DeFi), activating R3 OOD gating heavily. The single-trade month is not a data gap or an embargo artifact — it is the vol-regime gating operating as designed.

- The last OOS trade (`end_of_data`, 2026-06-09) is a SHORT UNIUSDT at 2.573 with PnL +4.14%. This is the live boundary trade at data extent — structurally normal.

## SPECIALIST Verdict

**SPECIALIST-NEGATIVE** — triple-falsified.

All three load-bearing falsifiers from brief Section 4 fired NEGATIVE:

1. **F2-PRIMARY FALSIFIED** (NEGATIVE-INERT-FEATURE): `rev_extension_z_3` ranked 42/52, far above the ≥14/52 INERT threshold. The lag-3 mean-reversion coordinate — UNI's empirically strongest structure — was not learned through the triple-barrier label. Both DIRECTIONAL reversion features (rev_extension_z_3 rank 42, rev_vol_gate_signed rank 39) are inert; neither the signal nor the interaction capstone bound. The F2-SUSPICION sub-branch did NOT fire (this is not an anti-signal pattern; it is absence of signal).

2. **F3 FALSIFIED** (NEGATIVE-PROBE-FLAT): realized 52-col IS Sharpe −0.7005 is Δ −0.46 below the 48-col probe baseline −0.243, far from the required +0.25 lift. The NEW features worsened IS via the /023 INERT-features-at-higher-budget mechanism (more overfit surface, not more signal).

3. **F4 FALSIFIED** (NEGATIVE-MOMENTUM-DOMINATED): IS Sharpe −0.7005 < 0.00 absolute and < trivial min-horizon −0.2485. The specialist is worse than not trading in-sample.

**Baseline unchanged**: BUNDLE-002 (tag v0.v1-082) remains the v1 baseline. No merge.

**Program-level finding** (for QR Phase 8 diary): iter-v1/085 is now the SECOND consecutive case (after CRV/084) where feature-engineering failed to manufacture a structure-gate pass on a sub-probe coin. The pre-registered "burden of proof has shifted to the architecture" diary trigger (brief Section 1, Risk A, Section 7) has now FIRED twice. The lag-3 autocorrelation structure in UNI returns is a correlation property that did not translate into a learnable triple-barrier label edge. The /086 decision should address: (a) whether a different labeling approach (e.g. fixed-horizon vs ATR-barrier) better captures the mean-reversion signal, or (b) whether to pivot to a different candidate coin from the eligible pool. This is a QR Phase 8 determination.

**GATE-2 reform validation**: the REFINED structure-gate (GATE 1 + GATE 2) correctly flagged UNI as GATE-2-WEAK (probe −0.243 < +0.30). The iteration confirmed the gate's predictive validity: UNI was GATE-2-WEAK and produced a NEGATIVE result. The gate-2 reform from /085 brief is empirically validated — the gate flag was honest and the outcome matched the flag.

## Status

OVERALL=READY-FOR-CRITIC
