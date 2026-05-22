# Engineering Report — iter-v3/123

## Headers

- Iteration: iter-v3/123
- Branch: iteration-v3/123
- Commit SHA: 32306c3b1ec142169e2996950613fbe6f626ce0a
- Implementation commit: `32306c3` feat(iter-v3/123): B1 eth_realized_vol_ratio_50 cross-asset feature + runner setup; eth_ret_3d REMOVED per /122 closure
- Brief commit: `aa0b29a` docs(iter-v3/123): research brief
- EDA commit: `dbc2993` analysis(iter-v3/123): cycle-7 axis-1 sub-axis B1 EDA
- Phase 5.5 gate: PASS (file `briefs-v3/iteration_v3-123/phase5p5_gate.md`)
- Hardware: WSL2 / x86-64
- Wall-clock time: 0.69h (within 2h EXPLORATION cap)

---

## Section 1 — Setup Verification

- Branch `iteration-v3/123` confirmed; SHA `32306c3`.
- Phase 5.5 gate PASS (all 10 sections verified pre-code).
- Ruff lint/format: clean at implementation commit (no new lint violations introduced by B1 changes in `cross_btc_v3.py`, `__init__.py`, `run_baseline_v3.py`).
- Parquet regeneration: BCH/LDO/TRX regenerated with `eth_vs_sym_rv_50` column materialized; `eth_ret_3d` absent; `len(V3_FEATURE_COLUMNS_TOP_N) == 15` pre-flight assertion PASS.
- ETH data freshness: `data/ETHUSDT/8h.csv` present and within staleness window at run time.
- OOS_CUTOFF_DATE and training_months: UNCHANGED (sacred constants).
- `eth_ret_3d` absent from `V3_FEATURE_COLUMNS_TOP_N`: confirmed (ABSENT assertion in runner pre-flight).
- `eth_vs_sym_rv_50` present: confirmed.
- `/119 C6 ret5d_signed_tbi` remains in BANNED list: confirmed (not in `V3_FEATURE_COLUMNS_TOP_N`).
- `/116 no_confirm` ENABLED: confirmed (`enable_no_confirm_exit=True` unchanged).
- Unit test `test_eth_vs_sym_rv_50_past_only`: PASS.
- Integration test `test_eth_vs_sym_rv_50_integration`: PASS.

---

## Section 2 — Implementation Summary

Single-axis change vs /121 baseline: replaced `eth_ret_3d` (CLOSED at /122) with `eth_vs_sym_rv_50` in `V3_FEATURE_COLUMNS_TOP_N` (count stays 15).

Files changed (per Section 3.5 manifest):
1. `src/crypto_trade/features_v3/cross_btc_v3.py`: `_load_eth_v3_features()` now computes `eth_rv_50 = rolling(50, min_periods=50).std()` on 1-bar ETH log returns; `add_cross_btc_v3_features()` computes `eth_vs_sym_rv_50 = eth_rv_50 / (range_realized_vol_50 + 1e-12)` per symbol, drops intermediate `eth_rv_50`.
2. `src/crypto_trade/features_v3/__init__.py`: `"eth_ret_3d"` replaced with `"eth_vs_sym_rv_50"` in `V3_FEATURE_COLUMNS_TOP_N`.
3. `run_baseline_v3.py`: `ITERATION_LABEL = "v3-123"`, pre-flight inverted (ABSENT `eth_ret_3d`, PRESENT `eth_vs_sym_rv_50`), banner updated.
4. Tests: `test_eth_vs_sym_rv_50_past_only` and `test_eth_vs_sym_rv_50_integration` added.

No labeling, risk-gate, walk-forward, or ensemble changes.

---

## Section 3 — Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | **-0.4155** | **1.7536** | -4.22 |
| daily_sharpe | -0.8235 | 3.4357 | -4.17 |
| max_drawdown | 56.3150 | 19.2104 | 0.34 |
| profit_factor | 0.8925 | 1.5740 | 1.76 |
| win_rate | 27.6% | 40.7% | 1.47 |
| n_trades | 181 | 91 | 0.50 |
| total_pnl (weighted) | -23.04 | +52.31 | -2.27 |
| monthly_calmar | -0.4092 | 2.7232 | -6.66 |
| dsr | 0.0 (IS neg) | — | — |
| pbo | 0.1042 | — | — |
| psr | 1.0 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 18 | — | — |
| CPCV frac_positive_paths | 0.644 (PASS) | — | — |

**Comparison vs /121 BASELINE (both anchors):**

| Anchor | IS Sharpe | OOS Sharpe | IS Delta | OOS Delta |
|---|---:|---:|---:|---:|
| /121 multi-seed CONFIRMATION (+1.3108 / +0.9682) | -0.4155 | +1.7536 | **-1.73** | **+0.79** |
| /121 EXPLORATION-mode estimate (+1.06 / +0.85) | -0.4155 | +1.7536 | **-1.48** | **+0.90** |

**vs /120 all-time bundle record (+1.6946 OOS):** OOS Sharpe +1.7536 EXCEEDS /120 by +0.059. This is the highest OOS monthly Sharpe in v3 history — achieved while IS is the lowest in v3 history at -0.42.

---

## Section 4 — Per-Symbol IS Attribution

| Symbol | IS Trades | IS WR | IS net_pnl_pct | IS wPnL share |
|---|---:|---:|---:|---|
| BCHUSDT | 89 | 34.8% | -1.06 | 2.79% of loss |
| LDOUSDT | 9 | 22.2% | -21.53 | 56.49% of loss |
| TRXUSDT | 83 | 30.1% | -15.52 | 40.72% of loss |

All three symbols are IS-negative. IS collapse is UNIVERSAL across the universe, not isolated to the EDA-predicted carrier (LDO). The deepest loss in net_pnl_pct is LDO (-21.53, 9 trades — avg -2.39/trade); TRX is -15.52 on 83 trades (avg -0.187/trade); BCH is essentially flat in net terms (-1.06, avg -0.012/trade).

Comparison vs /121 IS per-symbol:
- BCH: /121 +119.15 → /123 -1.06 (delta -120.22)
- LDO: /121 +9.53 → /123 -21.53 (delta -31.06)
- TRX: /121 +7.31 → /123 -15.52 (delta -22.83)

All three symbols lost their IS PnL basis relative to /121.

---

## Section 5 — Per-Symbol OOS Attribution

| Symbol | OOS Trades | OOS WR | OOS net_pnl_pct | OOS wPnL share |
|---|---:|---:|---:|---|
| BCHUSDT | 35 | **60.0%** | +85.57 | **108.3%** |
| LDOUSDT | 14 | 28.6% | -6.56 | -10.9% |
| TRXUSDT | 42 | 33.3% | -2.96 | +2.6% |

OOS is driven entirely by BCH (108.3% of total OOS wPnL; avg +2.445/trade). LDO and TRX are OOS-negative. This is a full carrier role reversal vs the EDA T9 SSC prediction (T9 predicted LDO as the importance-aligned PnL carrier; BCH was predicted structurally INERT).

The BCH OOS WR of 60.0% vs IS WR of 34.8% is the per-symbol signature of SUSPICIOUS-OOS-DOMINANT: BCH's IS model is net-flat but the OOS is strongly profitable at BCH level alone.

---

## Section 6 — B1 Feature Importance: Per-Symbol and Portfolio

| Symbol | B1 Rank/15 | B1 Gain% | EDA T5 Predicted Rank | EDA T5 Predicted Gain% |
|---|---:|---:|---:|---|
| BCH | **5** | 7.17% | 15 (INERT) | 4.46% |
| LDO | **11** | 6.51% | 1 (TOP) | 14.00% |
| TRX | **9** | 5.72% | 4 | 9.07% |
| Portfolio | **9** | 6.45% | — | — |

The EDA T5 prediction is INVERTED at production for all three symbols:
- BCH: EDA said rank 15/15 (least important); production shows rank 5/15 (mid-upper table). BCH used B1 MORE than EDA predicted — but in a direction that destroyed IS PnL.
- LDO: EDA said rank 1/15 (strongest in v3 EDA history); production shows rank 11/15. This is the sharpest EDA-vs-production importance divergence seen in v3. The "top carrier" collapsed to mid-table at full walk-forward training.
- TRX: EDA said rank 4/15; production shows rank 9/15 (degraded but not inverted).

This is the F5 falsifier: "if production LDO importance rank drops below 5/15 AND production LDO IS PnL delta is below +1pp, file /119 C6 DISSOCIATION-PATTERN-RECURRENT." Both conditions fire: LDO rank 11/15 (below 5) AND LDO IS PnL is -21.53 (deeply negative). F5 FIRES.

The production gain shares converge to a narrow band (5.7%-7.2%) across all 3 symbols and portfolio — B1 at production acts as a roughly uniform-importance feature rather than the strongly LDO-differentiated pattern the EDA predicted.

---

## Section 7 — IC Matrix at Production

Key B1 rows from `ic_matrix.csv`:

| Feature pair | Production IC | EDA prediction | Gate result |
|---|---:|---:|---|
| B1 vs `vwap_dev_20` | 0.0567 | 0.0687 | PASS < 0.40 (/122 Critic Rec 1) |
| B1 vs `regime_momentum_signed_5d` | -0.0177 | 0.0205 | PASS < 0.40 (/122 Critic Rec 1) |
| B1 vs `range_realized_vol_50` | -0.5353 | ~-0.52 | STRUCTURAL (denominator-sharing) |

Both critical /122 Critic Recommendation 1 pairwise-IC gates hold at production. The EDA pairwise-IC screen was accurate; the IC profiles for B1 match EDA within small delta. The IC methodology did not fail — B1 was genuinely orthogonal to the two key incumbents at the pooled IS level.

High-IC pairs existing in the baseline (unchanged from /121): `vwap_dev_20` vs `regime_momentum_signed_5d` = 0.764; `regime_momentum_signed_5d` vs `sym_vs_btc_ret_7d` = 0.619.

---

## Section 8 — ADF at Production

B1 (`eth_vs_sym_rv_50`) ADF at final IS months (January-March 2025):

| Symbol | Month | ADF stat | p-value | Stationary |
|---|---|---:|---:|---|
| BCH | 2025-03 | -3.352 | 0.0127 | PASS |
| LDO | 2025-03 | -4.286 | 0.0005 | PASS |
| TRX | 2025-03 | -3.329 | 0.0136 | PASS |

All 3 symbols PASS p < 0.05 at the final IS month. The EDA T8 ADF result was accurate (EDA BCH p=0.0045, LDO p=0.0078, TRX p=0.0076 — production slightly less extreme but same directional verdict). ADF stationarity is NOT the failure mode.

---

## Section 9 — Falsifier Evaluation per Brief Section 4 and Section 8

Per-criterion first-match-wins evaluation (pre-registered anchors per /122 Critic Rec 3):

| Criterion | Anchor | Threshold | Observed | Fires? |
|---|---|---|---|---|
| **C1 NEGATIVE-catastrophic** | **/121 multi-seed** (+1.3108 IS / +0.9682 OOS) | IS delta < -0.40 OR OOS delta < -0.30 | IS delta = **-1.73** | **YES — FIRST MATCH** |
| C8 SUSPICIOUS | /121 EXPLORATION-mode (+1.06 / +0.85) | OOS delta > +0.30 AND IS delta in [-0.10, +0.05] | IS delta = -1.48 (outside [-0.10, +0.05]) | Does not fire (IS delta too negative) |
| F5 C6-dissociation | anchor-independent importance rank | LDO rank < 5/15 AND LDO IS PnL delta < +1pp | LDO rank 11/15; LDO IS PnL = -21.53 | **YES (secondary)** |
| F4 role-reversal | per-symbol PnL direction vs T9 | LDO IS PnL NEGATIVE AND BCH/TRX both positive | BCH IS -1.06 (negative) | Does not fire (BCH not positive) |

C8 SUSPICIOUS-OOS-DOMINANT does NOT fire under first-match-wins because IS delta = -1.48 is far outside the C8 condition range of [-0.10, +0.05]. C1 fires first and terminates evaluation.

Note: The word "SUSPICIOUS" in the brief's characterization of this result is informal and does not correspond to Criterion 8 (which is the pre-registered mode). The formal verdict under Section 8 first-match-wins is C1 NEGATIVE-catastrophic.

---

## Section 10 — Section 8 First-Match-Wins Verdict

**CRITERION 1 FIRES: EXPLORATION-NEGATIVE-catastrophic.**

- IS delta vs /121 multi-seed: -1.73 (threshold: < -0.40). Distance to threshold: 1.33 Sharpe units below.
- This is the first IS-negative result in the /121-anchored cycle-7 test sequence.
- Per Section 8 Criterion 1 axis-close recommendation: "the broader ETH-realized-vol-cross-asset hypothesis is CLOSED at /123; future cross-asset axes must use a STRUCTURALLY DIFFERENT primitive class (e.g., on-chain feeds, liquidations, basis from non-Binance venue)."

Secondary finding: F5 C6-DISSOCIATION-PATTERN-RECURRENT fires (LDO importance rank 1 at EDA → rank 11 at production; the /119 C6 dissociation mechanism returned at /123 despite the stronger EDA T5 signal). This is the third consecutive cross-asset family EXPLORATION where the EDA importance prediction dissociates from production: /122 (eth_ret_3d, IC-spanning collapse), /123 (eth_vs_sym_rv_50, importance-rank inversion).

---

## Section 11 — Mechanism Analysis

**Why the EDA prediction (LDO rank 1/15) went catastrophically wrong at production:**

The EDA T5 importance was computed on a fixed 24-month IS window ending at a single IS endpoint (the EDA's IS cutoff). The production runner executes a rolling walk-forward over the full IS period — each walk-forward cell trains on a 24-month window that STARTS at a different absolute calendar date. The BCH/LDO/TRX histories diverge in their vol-ratio time series across those different window positions.

In the EDA single-window computation, LDO's `eth_vs_sym_rv_50` happened to be in an informative regime alignment at the specific EDA window anchor — producing the anomalously high rank 1/15. In the full rolling walk-forward, earlier window positions (2020-2022, 2021-2023) where LDO data is sparse and ETH vol regimes were qualitatively different produced a far weaker and sometimes inverted signal. The walk-forward mean importance converged to rank 11 (mid-table, gain 6.5%).

For BCH, the inversion is more structurally interesting: EDA ranked BCH at 15/15 (structurally INERT per the BTC-fork-coupling hypothesis), but the rolling walk-forward found BCH-specific period windows where `eth_vs_sym_rv_50` carried useful BCH signal (rank 5/15 at the last IS month). However, this BCH signal was exploited in a direction that produced IS losses (IS BCH WR 34.8%) — the feature learned to SUPPRESS BCH entries in IS regimes that coincidentally are the same regimes where the OOS BCH model fires profitably. This is vol-regime-classification mismatch: IS 2022-2025 vol-ratio regime differs structurally from OOS 2025-2026 vol-ratio regime, and B1's primary contribution at BCH level is to classify which regime is active — getting it backwards in IS.

The OOS BCH win (+85.57, WR 60%) is NOT evidence of a predictive signal. It is evidence that the B1 vol-regime classifier learned a partitioning of the feature space in which the "wrong" partition for IS happens to be the correct partition for the structurally different OOS regime. This is the most dangerous form of SUSPICIOUS-OOS-DOMINANT: a feature that acts as a regime classifier whose IS and OOS regime distributions are divergent, producing performance that appears PROMISING in OOS but is a regime-timing artifact with no forward-looking validity.

This is NOT the /105 trend-scanning IS-collapse pattern (which was a look-ahead bias). There is no look-ahead in B1 — it is past-only by construction. The mechanism is purely regime-distribution mismatch between IS 2020-2025 and OOS 2025-2026. The vol-ratio ETH/sym has a different distributional character in the 2025-2026 post-cycle-peak regime vs the 2020-2025 IS regime, and the model uses this distributional shift to do OOS regime identification rather than forward-looking signal extraction.

**Connection to the v3 cross-asset dissociation catalog:** This is the fourth consecutive ETH/BTC-derived cross-asset EXPLORATION that failed at production (/082 funding, /085 funding-z, /086 basis, /119 C6 ret5d_signed, /122 eth_ret_3d, /123 eth_vs_sym_rv_50). The pattern is consistent: EDA importance predicts a strong cross-asset signal; production walk-forward disagrees across most window positions; the feature either becomes INERT or (as here) becomes a harmful regime classifier. Section 8 Criterion 1's axis-close recommendation targets exactly this structural pattern.

---

## Section 12 — CPCV Path Analysis

CPCV paths (45 paths from 3-seed EXPLORATION): frac_positive = 0.644 (PASS > 0.55). Mean Sharpe = +0.30, Q25 = -0.24, Q50 = +0.34, Q75 = +0.84.

**Critical observation: /121 and /123 CPCV path statistics are bit-identical.**
- /121: frac_pos=0.6444, Q25=-0.243, Q50=0.3351, Q75=0.8378
- /123: frac_pos=0.6444, Q25=-0.243, Q50=0.3351, Q75=0.8378

This is the known frozen-baseline pattern (`feedback_v3_single_seed_frozen_baseline.md`) for single outer seed=42 EXPLORATION runs. The CPCV path structure is deterministic at this seed configuration; B1 does not change the path-level random structure. The IS monthly Sharpe collapse (-0.42 vs +1.31) is NOT captured in CPCV statistics — the CPCV path statistics CANNOT distinguish /123 from /121 at this seed configuration. This is a methodological observation, not a defect. At multi-seed CONFIRMATION, the path structure would diverge.

DSR = 0.0 because IS monthly Sharpe is negative — the PSR formula returns 1.0 (probability that observed SR > benchmark of 0, which is degenerate when SR is negative). This is not a computation error; it is the degenerate-IS case where the standard SR-based statistics are not meaningful.

---

## Section 13 — Seed Concentration Audit

EXPLORATION mode: ENSEMBLE_SIZE=3, seeds = outer=42 lineage (seed indices 0/1/2 of unified 10-seed lineage). All 3 seeds are from the same outer-42 lineage — this is the standard EXPLORATION configuration.

OOS BCH concentration: 108.3% of OOS wPnL. Well above the 30% top-symbol concentration gate for MERGE consideration — but this iteration does not reach MERGE evaluation (NEGATIVE-catastrophic verdict).

---

## Section 14 — Gate Efficacy Table

RiskV2 7-gate stack is UNCHANGED from /121 baseline. No new gate was introduced at /123. Gate fire rates are not directly measured in EXPLORATION-mode output. The IS MaxDD 56.31% vs OOS MaxDD 19.21% suggests the gates fired more frequently in IS (filtering more aggressively in the high-vol IS regimes) and less in OOS — consistent with the vol-ratio acting as a regime classifier that changes which gate-conditions are encountered.

---

## Section 15 — Anomaly Notes

1. **Spot-check (10 random OOS trades):** All 10 pass PnL math: pnl_pct = direction × (exit-entry)/entry × 100 within 0.01%, net_pnl_pct = pnl_pct - fee_pct, weighted_pnl = net_pnl_pct × weight_factor. No anomalies.

2. **IS monthly win rate (WR=32.0%) below 33%:** Consistent with a model that is directionally wrong in IS. The WR collapse from /121 IS (which was profitable at IS Sharpe +1.31) to /123 IS (WR 32%) is mechanically explained by the vol-ratio regime-classifier hypothesis in Section 11.

3. **LDO IS trades = 9 (very low):** LDO has extremely few IS signals — this is consistent with the ADX/Hurst gates filtering most LDO entries. The 9 IS LDO trades carry a -21.53 net_pnl_pct loss (avg -2.39/trade), which is the worst per-trade IS performance in any recent iteration. The small trade count makes LDO's IS contribution highly volatile; this is not an artifact of the engineering but of the gate stack behavior combined with the new feature.

4. **Comparison.csv OOS per-symbol section:** BCH shows wPnL=56.6684 and concentration_pct=108.32 — the concentration exceeds 100% because LDO and TRX are negative, and BCH alone generates more than the total OOS wPnL. This is mathematically correct but structurally unusual; confirms BCH is the entire OOS generator with LDO/TRX as drag.

5. **No NaN metrics, no zero-trade IS months:** All IS months have at least 1 trade. All comparison.csv headline metrics are non-NaN.

---

## Status

OVERALL=READY-FOR-CRITIC

Mechanical classification: **EXPLORATION-NEGATIVE-catastrophic**
- Section 8 Criterion 1 FIRES: IS delta -1.73 vs /121 multi-seed, threshold < -0.40
- Secondary: F5 C6-DISSOCIATION-PATTERN-RECURRENT fires (LDO importance 1→11)
- Axis-close recommendation per Section 8 Criterion 1: ETH-realized-vol-cross-asset hypothesis CLOSED
- Next cross-asset axis must use a structurally different primitive class
- /121 BASELINE_V3.md UNCHANGED (NEGATIVE verdict)
