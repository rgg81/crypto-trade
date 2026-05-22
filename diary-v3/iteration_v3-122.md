# iter-v3/122 — Cycle-7 EXPLORATION slot #1 — NEW cross-asset feature family (ETH OHLCV; A4 = `eth_ret_3d` = `log(close_eth[t]) − log(close_eth[t−9])`) — FILED **EXPLORATION-NEGATIVE-INERT**. The Critic FINAL (`9e0eeb6`) emitted ZERO clarifications and issued OVERALL=EXPLORATION-NEGATIVE-INERT on a single review pass. Section 8 first-match-wins decision tree returned criterion 3 (NEGATIVE-INERT) FIRST: (a) production importance rank ≥ 14/15 on > 1 symbol — BCH 14/15, TRX 15/15 (dead last) → YES; (b) POOLED lift < +0.005 — portfolio rank 14/15, share 3.9% out of 5291.7 total → YES; (c) IS Sharpe Δ vs the architecturally-adjusted EXPLORATION-mode anchor < +0.05 — IS Δ −0.089 → YES. ALL THREE CONDITIONS MET; criterion 3 first-matches; verdict ENGRAVED. The IC matrix on the production feature stack confirms the mechanism: `eth_ret_3d` has max |IC| = **0.5613 with `vwap_dev_20`** and secondary |IC| = **0.5280 with `regime_momentum_signed_5d`** — substantially spanned by 2-3 incumbents at the 0.50-0.56 |IC| range. Mechanically, trees at depth 3-5 cannot exploit marginal information when 2 incumbents already provide cross-asset momentum coverage at |IC| > 0.5. The QR hypothesis ("eth_ret_3d carries incremental directional signal beyond the 14-feature stack") is FALSIFIED by the same IC distribution that EDA T2 R²=0.44 only partially captured; the joint-R² screen is insufficient diagnostic for ETH-derived primitives and the pairwise ICs against `vwap_dev_20` + `regime_momentum_signed_5d` specifically are now the controlling gate. The headline OOS Δ +0.20 vs /121 multi-seed baseline (and OOS Δ +0.31 vs the architecturally-adjusted EXPLORATION anchor) is a single-seed 3-seed-mode TRX loss-surface reorganization artifact — the SAME mechanism that elevated /119's C6 composed feature to PROMISING-FEATURE-MECHANICAL status — but at /122 the diagnostic conjunction (a) is satisfied with INVERTED-CARRIER TRX importance rank 15/15 (dead last) while TRX IS PnL improved +32.45, exactly the dissociation pattern documented at /082/085/086/119 C6. F2 (importance INERT) TRIGGERED. F3 (suspicious-OOS-dominant) TRIGGERED. F4 (TRX-carrier SSC at PnL level) TRIGGERED with importance-rank INVERSION. The /119 C6 dissociation pattern (positive IS PnL change at the SSC carrier without importance allocation) is the canonical mechanism — /122 is the first cycle-7 RECURRENCE of this pattern in a non-engineered (off-the-shelf cross-asset primitive) class. No BASELINE update.

**Date**: 2026-05-20
**Type**: EXPLORATION (cycle-7 slot #1 of 10; `--exploration --seeds 3 --n-trials 35`, ENSEMBLE_SIZE=3, single-axis: ONE new feature appended to `V3_FEATURE_COLUMNS_TOP_N` 14 → 15)
**Verdict**: **EXPLORATION-NEGATIVE-INERT** — feature `eth_ret_3d` primitive CLOSED at /122; the broader ETH-OHLCV cross-asset hypothesis is NOT auto-closed per QR's per-primitive interpretation.
**Tag**: `v0.v3-122` (cycle-7 slot 1 NEGATIVE-INERT marker; does NOT supersede `v0.v3-121` as canonical).
**Anchor**: /121 multi-seed CONFIRMATION-MERGE BASELINE (IS +1.3108 / OOS +0.9682). UNCHANGED.

---

## 1. Setup — the iteration (brief reference)

**Brief**: `briefs-v3/iteration_v3-122/research_brief.md` (SHA `af157d0`).
**Iteration class**: cycle-7 EXPLORATION slot #1 of 10. /122 is the FIRST EXPLORATION post-/121 baseline update.
**Hypothesis**: adding `eth_ret_3d` as the 15th feature in `V3_FEATURE_COLUMNS_TOP_N` carries incremental directional signal beyond the /121 14-feature stack on the BCH/LDO/TRX 8h cohort, lifting EXPLORATION-mode IS monthly Sharpe by Δ ∈ [+0.05, +0.20] vs the architecturally-adjusted /121 EXPLORATION-mode reference AND OOS monthly Sharpe by Δ ∈ [+0.00, +0.15] vs /121 OOS +0.9682.

**Single substantive change vs /121 head state**: ONE new feature appended to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15: append `eth_ret_3d`). All other knobs (universe, label, gates, ensemble seeds, Optuna search space, /116 no_confirm primitive) are bit-identical to /121. ITERATION_LABEL "v3-122".

**Anchors**:
- /121 multi-seed CONFIRMATION baseline (IS +1.3108 / OOS +0.9682) — canonical public anchor for Section 8 NEGATIVE-catastrophic threshold.
- /121 architecturally-adjusted EXPLORATION-mode estimate (IS +1.06 / OOS +0.85) — falsifier band reference per `feedback_v3_dsr_mode_artifact.md` (3-seed-vs-10-seed proba-averaging compression factor: IS −0.25, OOS −0.12, from /077 vs /059 anchor-staleness work).

**Spec**:
- Runner invocation: `uv run python run_baseline_v3.py --exploration --n-trials 35`
- ENSEMBLE_SIZE=3 (per `feedback_v3_outer_seed_cap_2_v3.md` — first 3 seeds of the unified 10-seed lineage)
- Total Optuna trials: 35 × 3 symbols × 3 seeds = 315
- Hard cap: 2h. Actual wall-clock: **0.70h** (well within cap).

---

## 2. Implementation — setup, engineering report, Critic cycle

### 2.1 Setup commit chain

| Commit | SHA | Description |
|---|---|---|
| EDA | `b875272` | 4-candidate cross-asset EDA (A1-A4); 13 files; T1-T9 result tables; synthesis.md |
| Research brief | `af157d0` | 10-section brief; 7 pre-registered failure modes; first-match-wins decision tree |
| Phase 5.5 gate | `e18b266` | PASS (all 10 sections present; bundle state verified; zero scope creep) |
| Setup commit | `ac0f891` | A4 `eth_ret_3d` cross-asset feature + runner setup; `V3_FEATURE_COLUMNS_TOP_N` 14 → 15; ITERATION_LABEL "v3-122" |
| Pre-flight fix | `f88415c` | Assertion guard `len == 14` → `len == 15` (residue from /121 setup) |
| Engineering report | `08022dd` | Backtest 0.70h wall-clock; all 12 sections + falsifier evaluation + SSC pattern check |
| Critic FINAL | `9e0eeb6` | OVERALL=EXPLORATION-NEGATIVE-INERT; single round; zero clarifications; 7 of 8 checks PASS + 1 N/A |

### 2.2 Code surfaces (THREE)

Three surfaces changed vs /121 head state.

1. **`src/crypto_trade/features_v3/cross_btc_v3.py` (extension)** — Added `_load_eth_v3_features()` function (ETH klines cache, `eth_ret_3d = log(close[t]) − log(close[t−9])` with 9-bar NaN warm-up) + extended `add_cross_btc_v3_features` to left-join ETH columns on `open_time`. The merge convention mirrors the existing `btc_ret_14d` BTC merge.

2. **`src/crypto_trade/features_v3/__init__.py`** — Appended `"eth_ret_3d"` to `V3_FEATURE_COLUMNS_TOP_N`. Length 14 → 15. Comment updated with /122 provenance.

3. **`run_baseline_v3.py`** — `ITERATION_LABEL = "v3-122"` (was "v3-121"); pre-flight assertion inversion `len(V3_FEATURE_COLUMNS_TOP_N) == 15` (was 14); pre-flight assertion `"eth_ret_3d" in V3_FEATURE_COLUMNS_TOP_N`.

### 2.3 Sacred constants — UNCHANGED

- `OOS_CUTOFF_DATE = 2025-03-24` — IMMUTABLE
- `training_months = 24` — IMMUTABLE
- `ENSEMBLE_SIZE = 3` (EXPLORATION mode, per `feedback_v3_outer_seed_cap_2_v3.md`)
- `ENSEMBLE_SEEDS` first 3 of the 10-tuple lineage — UNCHANGED
- 3-symbol universe BCHUSDT/LDOUSDT/TRXUSDT — UNCHANGED
- `(atr_tp=2.0, atr_sl=1.0)` triple-barrier; 21-candle timeout — UNCHANGED
- 7-primitive risk gate stack — UNCHANGED
- /116 no_confirm RULE-layer primitive (`enable_no_confirm_exit=True, no_confirm_trigger_atr=0.50, no_confirm_k_candles=4`) — UNCHANGED at canonical baseline

### 2.4 Critic Phase 7.5 review

Single round; **zero clarifications requested**. 7 of 8 mandatory checks PASS + 1 N/A:

| Check | Status | Highlight |
|---|---|---|
| 1 Look-Ahead | PASS | `eth_ret_3d` at `cross_btc_v3.py:56-76` uses past-only array indexing; ETH OHLCV at bar close_time is "knowable" at symbol's bar-decision time (same-frequency 8h bars); adversarial unit test PASS |
| 2 Embargo | PASS | REQUIRED_GAP=66 unchanged from /121; walk-forward POST-FIX at `e149e9d` active |
| 3 Multiple-testing | PASS | PBO 0.1412 < 0.40, PSR 1.0 > 0.95, frac_positive_paths 0.6444 ≥ 0.55; DSR_relative 0.9999. DSR=0.0 EXPLORATION-mode structural artifact per `feedback_v3_dsr_mode_artifact.md` |
| 4 IC Correlation | **PASS (structural note)** | Max |IC| = 0.5613 with `vwap_dev_20`; secondary 0.5280 with `regime_momentum_signed_5d`. < 0.70 strict threshold MECHANICALLY PASSES, but the structural implication (information substantially spanned by 2-3 incumbents at 0.50-0.56 range) explains F2 INERT outcome |
| 5 ADF Stationarity | PASS | `eth_ret_3d` ADF stat ≈ −8.57 (p=0) on all 3 symbols at OOS-boundary; stationary by log-return construction |
| 6 Pareto Dominance | N/A | Single-seed EXPLORATION; CONFIRMATION-mode validation deferred to /132 |
| 7 Reproducibility | PASS | Setup chain `ac0f891` + `f88415c` verified; explicit 15-feature tuple; pre-flight assertions verify `len=15`, `eth_ret_3d` present, ret5d_signed_tbi absent, enable_no_confirm_exit=True, REQUIRED_GAP=66 |
| 8 Hypothesis-Impl Alignment | PASS | Brief Section 3 six changes all delivered; no scope creep; hypothesis exactly tested; FALSIFIED outcome honestly registered |

---

## 3. Results — Phase 7 OOS evaluation (first look)

### 3.1 Headline metrics vs /121 multi-seed CONFIRMATION baseline (`reports-v3/iteration_v3-122/comparison.csv`)

| Metric | /121 IS | /121 OOS | /122 IS | /122 OOS | IS Δ vs /121 | OOS Δ vs /121 |
|---|---:|---:|---:|---:|---:|---:|
| Monthly Sharpe | +1.3108 | +0.9682 | **+0.9710** | **+1.1642** | **−0.3398** | **+0.1960** |
| Daily Sharpe | 3.1180 | 2.3979 | 2.5243 | 2.3286 | −0.5937 | −0.0693 |
| Max Drawdown | 26.38% | 25.70% | 33.21% | 28.25% | +6.83pp | +2.55pp |
| Profit Factor | 1.6019 | 1.3869 | 1.511 | 1.356 | −0.091 | −0.031 |
| Win Rate (aggregate) | — | 39.8% | 40.2% | 43.1% | — | +3.3pp |
| n_trades | 173 | 98 | 179 | 102 | +6 | +4 |
| Total PnL (weighted) | 88.77 | 38.15 | 74.09 | 36.52 | −14.68 | −1.63 |
| OOS/IS Sharpe ratio | — | 0.7386 | — | **1.1989** | — | +0.460 |

### 3.2 Methodology metrics (`reports-v3/iteration_v3-122/dsr.json`)

| Metric | /121 (10-seed) | /122 (3-seed EXPLORATION) | Status |
|---|---:|---:|---|
| PBO mean | 0.1278 | **0.1412** | PASS (< 0.40) |
| PSR | 1.0 | **1.0** | PASS (> 0.95) |
| frac_positive_paths | 0.6444 | **0.6444** | PASS (≥ 0.55) |
| CPCV path Sharpe Q25 | −0.243 | −0.243 | substantial left tail; 35% paths Sharpe-negative |
| CPCV path Sharpe Q50 | +0.3351 | +0.335 | identical |
| DSR (legacy) | 0.0 | 0.0 | EXPLORATION-mode structural artifact |
| DSR_relative | 0.9999 | 0.9999 | architecture-invariant |
| n_trials | 1050 | 315 | EXPLORATION-mode |
| n_eff | 19 | 19 | architecture-independent |

### 3.3 Anchor-vs-observed band classification

The /122 brief Section 4 pre-registered TWO anchor references with the architecturally-adjusted EXPLORATION-mode estimate (IS +1.06 / OOS +0.85) used for the falsifier band classification per `feedback_v3_dsr_mode_artifact.md`. Section 8 NEGATIVE-catastrophic uses the public /121 multi-seed anchor directly.

| Reference | IS Sharpe | OOS Sharpe | Use |
|---|---:|---:|---|
| /121 CONFIRMATION (public canonical) | +1.3108 | +0.9682 | For NEGATIVE-catastrophic threshold; for headline reporting |
| /121 architecturally-adjusted EXPLORATION-mode estimate | +1.06 | +0.85 | For falsifier band classification |

| Observed vs | IS Δ | OOS Δ |
|---|---:|---:|
| /121 multi-seed CONFIRMATION (canonical) | **−0.3398** | **+0.1960** |
| /121 architecturally-adjusted EXPLORATION estimate | **−0.089** | **+0.314** |

### 3.4 Per-symbol IS attribution (load-bearing for F4 SSC TRX-carrier falsifier)

| Symbol | /121 IS trades | /122 IS trades | /121 IS PnL | /122 IS PnL | IS PnL Δ | /121 IS WR | /122 IS WR | WR Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCH | 85 | 85 | 119.15 | 54.53 | **−64.62** | 50.6% | 40.0% | −10.6pp |
| TRX | 79 | 82 | 7.31 | 39.76 | **+32.45** | 34.2% | 41.5% | +7.3pp |
| LDO | 9 | 12 | 9.53 | 1.48 | **−8.05** | 33.3% | 33.3% | 0.0pp |

IS aggregate: BCH IS WR collapsed −10.6pp (50.6% → 40.0%). TRX IS lifted substantially. LDO IS PnL fell with unchanged WR (roster shifted to lower-avg-PnL trades). Net IS Sharpe degraded −0.3398 vs /121 multi-seed.

### 3.5 Per-symbol OOS attribution

| Symbol | /121 OOS trades | /122 OOS trades | /121 OOS PnL | /122 OOS PnL | OOS PnL Δ | /121 OOS WR | /122 OOS WR | WR Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BCH | 35 | 41 | 52.48 | 47.67 | **−4.81** | 48.6% | 43.9% | −4.7pp |
| TRX | 51 | 49 | 13.09 | 28.77 | **+15.68** | 43.1% | 46.9% | +3.8pp |
| LDO | 12 | 12 | −10.77 | −28.02 | **−17.25** | 25.0% | 25.0% | 0.0pp |

OOS net: +0.1960 Sharpe vs /121 multi-seed, driven entirely by TRX OOS PnL +15.68. BCH OOS slightly negative (−4.81), LDO OOS deepened its loss (−17.25). The OOS-positive headline conceals a concerning LDO OOS deterioration (same WR, much worse total loss — roster-shift to larger-loss trades, not a WR change).

### 3.6 A4 feature importance (per-symbol production ranks, IS last month)

| Symbol | EDA T5 predicted rank | Production rank | Importance score | Share |
|---|---:|---:|---:|---:|
| BCH | **15/15 (INERT)** | **14/15** | 41.0 | 3.0% |
| LDO | 11/15 | **13/15** | 124.7 | 4.6% |
| TRX | 10/15 | **15/15 (dead last)** | 39.7 | 3.3% |

**Portfolio rank: 14/15**, share 3.9% (importance 205.3 out of 5291.7 total).

The TRX rank fell to 15/15 (dead last; INVERTED vs EDA T5 prediction of rank 10/15) while TRX IS PnL improved +32.45 — the canonical /119 C6 dissociation signature.

---

## 4. The /119 C6 dissociation pattern parallel — first cycle-7 RECURRENCE in non-engineered feature class

The /122 outcome RECURS the same loss-surface reorganization mechanism observed at /119 with `ret5d_signed_tbi` (PROMISING-FEATURE-MECHANICAL subclass) and at /082/085/086 with funding-rate features (PROMISING-INERT subclass). The parallel is structurally exact at the dissociation diagnostic level, but differs in the carrier mechanism class.

### 4.1 /119 C6 mechanism summary (canonical reference)

iter-v3/119 introduced `ret5d_signed_tbi` = `ret_5d × sign(taker_buy_imbalance_20)` — a Category-2 composed feature with IC=−0.72 against its algebraic sister `regime_momentum_signed_5d` (sharing the `ret_5d` value primitive). The diagnostic conjunction PROMISING-FEATURE-MECHANICAL fired:

1. **Sister-family redistribution > 30%**: `regime_momentum_signed_5d` lost 65.3% of importance (506.67 → 175.67); combined sister-family allocation NET DROPS 35.1%; C6 share 2.6% of total split-budget — mechanically insufficient to produce direct edge.
2. **Anchor-rank preservation Spearman > 0.50**: ρ = 0.7714 on 14 anchor features (rank-preserving not chaotic shuffle).
3. **Broad-based per-symbol IS positive Δ**: BCH +4.57 / LDO +18.75 / TRX +37.63 — 3/3 positive.

The mechanism: C6 acts as a CATALYST for loss-surface reorganization (redistributing split-budget from its algebraic sister to four rank-rising anchor features) without contributing direct edge. The OOS Sharpe lift (+0.7017 vs /060 anchor) is structurally interpretable as the entry-distribution reshape × Component A's RULE-layer exit overlay interaction.

### 4.2 /122 A4 mechanism summary (the cycle-7 RECURRENCE)

iter-v3/122 introduced `eth_ret_3d` — an OFF-THE-SHELF cross-asset PRIMITIVE (not a composed feature). The diagnostic conjunction PROMISING-FEATURE-MECHANICAL does NOT fully fire (condition c "broad-based per-symbol IS positive Δ" FAILS — BCH IS PnL −64.62 is materially negative; condition a fires only PARTIALLY because `eth_ret_3d` does not have a single IC=−0.72 algebraic sister but rather two |IC|≈0.55 incumbents in `vwap_dev_20` + `regime_momentum_signed_5d`). The mechanism instead matches the /082/085/086 INERT class:

1. **Importance INERT pattern (F2)**: BCH rank 14/15, TRX rank 15/15 (dead last), LDO rank 13/15. POOLED lift estimate < +0.005. Portfolio split-budget share 3.9% — structurally insufficient as direct edge.
2. **Loss-surface reorganization at TRX-only**: TRX IS PnL +32.45 with TRX importance rank 15/15 — the FOUNDING /119 dissociation signature (positive IS PnL change without importance allocation; the model uses other features at the TRX prediction boundary but the addition of `eth_ret_3d` to the feature matrix changed the Optuna hyperparameter search trajectory for TRX).
3. **NOT broad-based**: BCH IS PnL −64.62 + LDO IS PnL −8.05 + TRX +32.45 → net negative IS aggregate; the C6 condition (c) "all 3 symbols positive" FAILS at /122.

### 4.3 What the parallel finding establishes

The /122 outcome is the FIRST cycle-7 RECURRENCE of the loss-surface dissociation mechanism in a non-engineered (off-the-shelf cross-asset) feature class. The structural lesson:

- **At /119**: the dissociation mechanism produced PROMISING-FEATURE-MECHANICAL classification (3-condition diagnostic conjunction satisfied; broad-based per-symbol positive Δ → bundled into /120 multi-mechanism CONFIRMATION).
- **At /122**: the dissociation mechanism produces NEGATIVE-INERT classification (diagnostic conjunction NOT satisfied — single-symbol carrier TRX + non-broad-based IS Δ → Section 8 criterion 3 first-matches).

The two classifications are distinguished by the broad-based-per-symbol-IS-positive-Δ leg (condition c at /119; absent at /122). When the dissociation mechanism produces broad-based positive lift, the QR's interpretation moves to PROMISING-FEATURE-MECHANICAL (bundling pathway with F3 binding gate at multi-seed CONFIRMATION); when the dissociation mechanism produces single-symbol-carrier lift (the SSC pattern), the QR's interpretation moves to NEGATIVE-INERT (closure pathway at axis-CLOSE per F4 SSC realization).

### 4.4 IC-spanning mechanism — the controlling diagnostic

The /122 outcome adds a NEW diagnostic refinement to the loss-surface dissociation pattern catalog. The /122 mechanism is structurally distinct from /119's algebraic-sister cannibalization in one key respect: `eth_ret_3d` has NO single IC=−0.72 algebraic sister — instead, its information is **distributively spanned** by 2-3 incumbents at the 0.50-0.56 |IC| range (vwap_dev_20 at 0.561, regime_momentum_signed_5d at 0.528, btc_ret_14d at 0.405). This is the IC-SPANNING-BY-MULTIPLE-INCUMBENTS class — a softer redundancy pattern than /119's near-anti-correlated single-sister cannibalization.

The joint-R² screen at EDA (T2: R² = 0.44 against the full 14-feature set) measured the AGGREGATE residual signal capacity correctly, but it did NOT identify WHICH 2-3 incumbent features were doing the spanning. The pairwise IC matrix now provides the controlling diagnostic: a new feature with no |IC|>0.70 single algebraic sister but TWO |IC|>0.50 partial-spanning incumbents is structurally INERT at the importance-allocation level (trees at depth 3-5 cannot exploit marginal information when the partial-spanning incumbents already cover the variance contribution).

**Future EXPLORATION QR application**: Category-1 OFF-THE-SHELF primitives (especially cross-asset features) must pass pairwise |IC| < 0.40 with EACH high-importance incumbent (not just joint-R² against the full anchor set). The /122 outcome is the empirical justification for tightening the cross-asset feature gate.

### 4.5 Cross-references to dissociation precedents

| Iteration | Class | Feature | Mechanism | Classification |
|---|---|---|---|---|
| /082 | crypto-native sentiment | funding_rate_zscore_30 | INERT-by-importance + OOS-spike artifact | PROMISING-INERT |
| /085 | crypto-native sentiment | funding_rate_zscore_30 (retry at higher budget) | INERT-by-importance + OOS-spike artifact | PROMISING-INERT |
| /086 | crypto-native sentiment | basis_zscore_30 (cross-exchange) | INERT-by-importance + OOS-spike artifact | PROMISING-INERT |
| **/119** | engineered Category-2 composed | ret5d_signed_tbi | Algebraic-sister cannibalization + broad-based positive lift | PROMISING-FEATURE-MECHANICAL |
| **/122** | off-the-shelf cross-asset primitive | eth_ret_3d | IC-spanning by 2-3 incumbents + single-symbol-carrier TRX lift | **NEGATIVE-INERT** |

The /122 entry establishes the OFF-THE-SHELF CROSS-ASSET PRIMITIVE class as the NEW context where IC-spanning dissociation produces NEGATIVE rather than PROMISING outcomes — the SSC + non-broad-based-IS-Δ legs are the controlling diagnostic that distinguishes the two pathways.

---

## 5. Falsifier evaluation (the load-bearing finding)

### 5.1 The 4 pre-registered falsifiers

| F# | Status | Observed | Threshold |
|---|---|---:|---:|
| **F1 NEGATIVE-catastrophic** | NOT TRIGGERED | IS Δ −0.3398 (> −0.40); OOS Δ +0.1960 (> −0.30) | IS Δ < −0.40 OR OOS Δ < −0.30 |
| **F2 importance INERT at production** | **TRIGGERED** | BCH rank 14/15, TRX rank 15/15 → 2 symbols at ≥ 14/15; portfolio rank 14/15 share 3.9% | rank ≥ 14/15 on > 1 symbol AND POOLED lift < +0.005 |
| **F3 suspicious-OOS-dominant** | **TRIGGERED** | OOS Δ +0.1960 > +0.15; IS Δ −0.3398 < +0.00 | OOS Δ > +0.15 AND IS Δ < +0.00 |
| **F4 TRX-carrier SSC realized** | **TRIGGERED** | TRX IS PnL Δ +32.45 > +5pp; BCH IS PnL Δ −64.62 < −1pp; LDO IS PnL Δ −8.05 < +1pp | TRX +5pp AND BCH < −1pp AND LDO < +1pp |

**3 of 4 falsifiers TRIGGERED.** F1 NOT triggered (IS and OOS deltas within band). F2 + F3 + F4 all FIRED — the 3-conjunction is the canonical signature of the loss-surface dissociation mechanism.

### 5.2 Section 8 first-match-wins decision tree walk

Walking through Section 8 criteria in order:

1. **NEGATIVE-catastrophic**: IS Δ −0.3398 not below −0.40; OOS Δ +0.1960 not below −0.30. NOT TRIGGERED.
2. **NEGATIVE-no-effect**: IS Δ −0.3398 not in [−0.05, +0.05]. NOT TRIGGERED.
3. **NEGATIVE-INERT**: (a) production importance rank ≥ 14/15 on > 1 symbol [BCH 14/15, TRX 15/15: YES]; (b) POOLED lift < +0.005 [portfolio rank 14/15, share 3.9%: YES]; (c) IS Δ vs EXPLORATION-mode anchor < +0.05 [−0.089 < 0.05: YES]. **ALL THREE CONDITIONS MET. FIRST MATCH. VERDICT: EXPLORATION-NEGATIVE-INERT.**

Note: Section 8 criterion 8 (SUSPICIOUS-OOS-DOMINANT) is ALSO met (OOS Δ +0.314 > +0.30; IS Δ −0.089 ∈ [−0.10, +0.05]) but criterion 3 first-matches per the listed order. F3 falsifier (Section 4) is also triggered independently. Both classifications point to the same root cause.

### 5.3 Why the OOS Δ +0.20 is NOT a robust signal

The OOS Sharpe headline (+1.1642 absolute, +0.20 vs /121 multi-seed, +0.31 vs architecturally-adjusted EXPLORATION anchor) is a single-seed 3-seed-mode loss-surface-reorganization artifact, not a robust signal. The evidence chain:

1. **TRX importance rank 15/15 (dead last)** — `eth_ret_3d` is NOT being used by LightGBM at the TRX prediction boundary at all. The TRX IS PnL gain (+32.45) and TRX OOS PnL gain (+15.68) are loss-surface-reorganization artifacts, not direct signal.
2. **CPCV path distribution shows substantial left tail** (q25 = −0.243; 35% paths Sharpe-negative). Robust signal would show a tighter positive distribution.
3. **LDO OOS deepened from −10.77 to −28.02 despite unchanged WR and trade count** — the worsening is in avg_pnl_pct (−0.90 → −2.34 per trade) — the LDO OOS roster shifted to worse-average-outcome trades, likely because `eth_ret_3d` changed the threshold at which LDO signals fire.
4. **F3 + F4 + F2 triple-trigger** — the canonical signature of loss-surface dissociation rather than direct edge.
5. **IC matrix shows information spanned by incumbents** — `eth_ret_3d` has no signal that the 14-feature stack doesn't already cover via `vwap_dev_20` + `regime_momentum_signed_5d`.

The OOS lift would NOT survive multi-seed CONFIRMATION because the underlying mechanism (single-seed TRX loss-surface reorganization) is not robust to seed averaging. The /119 multi-seed validation at /120 confirmed this for a different feature class (PROMISING-FEATURE-MECHANICAL) — the corresponding multi-seed projection for a NEGATIVE-INERT case is even more degrading.

---

## 6. Axis CLOSURE — what /122 closes and what stays open

### 6.1 What CLOSES at /122

- **The `eth_ret_3d` primitive specifically**: this feature is INERT due to IC-spanning by `vwap_dev_20` + `regime_momentum_signed_5d`. Do NOT retry at higher Optuna budget or at multi-seed CONFIRMATION (per `feedback_v3_inert_features_at_higher_budget.md` — INERT features at higher Optuna budget actively HARM OOS).
- **The "OFF-THE-SHELF cross-asset PRIMITIVE without joint-R²-PLUS-pairwise-IC vetting" axis**: the joint-R² screen at EDA (T2: 0.44) was insufficient diagnostic. The pairwise IC matrix is the controlling gate. Future cross-asset primitives must pass pairwise |IC| < 0.40 with each of `vwap_dev_20` AND `regime_momentum_signed_5d` AND any other importance-top-5 incumbent.

### 6.2 What does NOT close at /122

- **The broader ETH-OHLCV cross-asset hypothesis**: per the Critic FINAL recommendation 1, the criterion-3 (NEGATIVE-INERT) verdict closes `eth_ret_3d` specifically but does NOT auto-close all ETH-OHLCV derivatives. ETH-derived primitives that are NOT spanned by `vwap_dev_20` + `regime_momentum_signed_5d` (e.g., ETH realized-volatility regime classifier, ETH cross-sectional rank vs alt cohort, ETH OI-weighted direction, ETH funding-rate divergence) remain testable in subsequent cycle-7 EXPLORATION slots if the EDA passes the pairwise-IC gate.
- **The cycle-7 cross-asset axis-1 menu item**: cross-asset feeds remain among the 4 candidate axes for cycle-7 EXPLORATION (per `project_v3_cycle7_setup.md`). Only the eth_ret_3d primitive is closed.

### 6.3 Cycle-7 cadence

Per `feedback_v3_strict_10_to_1_cadence.md`: 10 EXPLORATIONs (iter-v3/122–/131) + 1 CONFIRMATION (iter-v3/132). /122 is slot 1/10. **9 EXPLORATIONs remain + /132 CONFIRMATION**.

Cycle-7 cadence accounting at /122 closeout:
- Slot 1: /122 — NEGATIVE-INERT (this iteration)
- Slot 2: /123 — NEXT (axis recommendation in Section 8 below)
- Slots 3-10: /124-/131 — open
- CONFIRMATION: /132

---

## 7. Honest accounting — what worked, what failed

### 7.1 What worked

- **EDA discipline**: the EDA correctly identified A4 as MARGINAL (POOLED lift +0.0012 below threshold; BCH rank 15/15 INERT signature; SSC TRUE 3.63×). The pre-registered Mode 2 (Importance INERT at production) modal probability of 35% and Mode 5 (Null at production) modal probability of 30% captured the realized outcome (criterion 3 NEGATIVE-INERT) — combined 65% probability assigned to INERT-class outcomes, which is exactly what fired.
- **Falsifier discipline**: 3 of 4 pre-registered falsifiers TRIGGERED with quantitative match to the predicted patterns. F2 (importance INERT) + F3 (suspicious-OOS-dominant) + F4 (TRX-carrier SSC) firing simultaneously is the canonical /082/085/086/119 dissociation signature.
- **Process discipline**: zero scope creep; single substantive change (ONE new feature appended); single Critic round; zero clarifications; clean Phase 5.5 gate PASS; integration test + unit test both PASS; pre-flight assertion fix committed before backtest.
- **Honest pre-registration**: the brief Section 7 assigned only 10% probability to PROMISING outcomes — the EDA signal was genuinely WEAK and the brief modeled this honestly. The outcome matched the modal prediction, not the optimistic tail.

### 7.2 What failed

- **The hypothesis "eth_ret_3d carries incremental directional signal beyond the 14-feature stack"** is FALSIFIED. The feature's information is substantially spanned by `vwap_dev_20` + `regime_momentum_signed_5d` (|IC| 0.561 + 0.528). Trees at depth 3-5 cannot exploit marginal information at this redundancy level.
- **The EDA T2 joint-R² screen was insufficient diagnostic**: R² = 0.44 against the full 14-feature set passed the < 0.70 strict gate, but the pairwise IC matrix would have shown the 2-incumbent partial-spanning at 0.50-0.56 range. The lesson: for OFF-THE-SHELF cross-asset primitives, pairwise IC against each high-importance incumbent is a stricter diagnostic than joint-R².
- **The TRX-carrier SSC prediction realized at PnL level but INVERTED at importance level**: EDA T9 predicted TRX as the carrier (TRX lift-to-POOLED ratio = 3.63×). Production shows TRX as the carrier at the IS PnL level (+32.45) but with importance rank 15/15 (dead last). The carrier is real at the PnL-roster level but absent at the split-gain level — the canonical /119 C6 dissociation signature recurring in a non-engineered feature class.

### 7.3 Lessons generalizable

1. **Pairwise IC > joint-R² for OFF-THE-SHELF cross-asset primitives**: future cross-asset feature EDAs must include the pairwise IC matrix as a controlling diagnostic. The /122 outcome formalizes the gate at |IC| < 0.40 with each of `vwap_dev_20` AND `regime_momentum_signed_5d`.
2. **The loss-surface dissociation mechanism RECURS across feature classes**: /082/085/086 (crypto-native sentiment) → /119 (engineered Category-2 composed) → /122 (off-the-shelf cross-asset primitive). The mechanism is structurally the same (importance INERT + single-seed loss-surface reorganization producing roster shifts that change Sharpe without changing model decisions). The classification (PROMISING-FEATURE-MECHANICAL vs NEGATIVE-INERT) depends on the SSC/broad-based-IS-Δ diagnostic conjunction.
3. **EXPLORATION-mode OOS Δ +0.20 vs CONFIRMATION-mode anchor is NOT a reliable PROMISING signal**: when F2 + F3 + F4 fire simultaneously, the OOS lift is structurally interpretable as single-seed loss-surface artifact, not robust signal. The OOS would degrade or invert at multi-seed CONFIRMATION.

---

## 8. /123 axis recommendation — what to test next

### 8.1 Two admissible axes per Critic FINAL recommendation

Per the Critic FINAL recommendations (2) and the cycle-7 axis menu in `project_v3_cycle7_setup.md`:

**Option A: NON-IC-SPANNED ETH-derived primitive** (continue cycle-7 axis-1 cross-asset with a structurally different sub-axis)
- Candidates: ETH realized-volatility regime classifier (e.g., 50-bar realized vol ratio ETH-vs-symbol), ETH cross-sectional rank vs alt cohort (ETH percentile rank in BTC+SOL+ETH+LDO+TRX cross-section), ETH funding-rate divergence from BTC funding (cross-asset positioning), ETH OI-weighted direction
- Required EDA gate: pairwise |IC| < 0.40 with EACH of `vwap_dev_20` AND `regime_momentum_signed_5d` AND any other importance-top-5 incumbent
- Joint-R² gate (< 0.70 strict) remains in force as a coarse first filter
- Risk: any ETH-derived primitive may still be partially spanned by the existing cross-asset incumbents; the pairwise-IC gate must be enforced strictly
- Pros: continues cycle-7 axis-1 cross-asset menu item; the broader ETH hypothesis is NOT closed and a structurally different ETH derivative could surface incremental signal
- Cons: the IC-spanning risk is structural to ETH-derived features (ETH and BTC are highly correlated in crypto bull/bear cycles)

**Option B: LONGER-CADENCE LABELS axis-3** (pivot to a structurally different cycle-7 axis with a coherent label+execution redesign)
- Specifically: 42-candle (14-day) or 63-candle (21-day) horizon labels with proportionally scaled barriers (e.g., ATR_TP=3.0, ATR_SL=1.5 at 42-candle horizon) and REQUIRED_GAP scaled to (42+1) × 3 = 129 or (63+1) × 3 = 192
- Risk: the 21-candle baseline is the empirical optimum identified at /072→/105→/115; longer-cadence labels are structurally adjacent to /068's failure mode (NEGATIVE-catastrophic at 42-candle timeout). A coherent label+barrier+REQUIRED_GAP scaling is the genuinely-new variant.
- Pros: opens a structurally different EDGE source than cross-asset features; the longer-cadence label may surface a different signal structure (multi-day regime persistence rather than 8h directional)
- Cons: triples REQUIRED_GAP from 66 → 129+ with substantial walk-forward impact; the /068 NEGATIVE-catastrophic precedent must be carefully avoided via the coherent execution geometry redesign

### 8.2 Recommendation: OPTION A — NON-IC-SPANNED ETH-derived primitive

**Reasoning**:

1. **/122 has NOT auto-closed the cross-asset axis-1 menu item** — the Critic FINAL is explicit that only `eth_ret_3d` specifically is closed; the broader ETH-OHLCV hypothesis stays open subject to the tightened pairwise-IC gate.
2. **Option A keeps cycle-7 axis-1 cross-asset coverage**: slots /124-/131 (8 remaining EXPLORATIONs) can include both more cross-asset variants AND axis-3 longer-cadence labels — Option A at /123 does not preclude axis-3 at /124.
3. **The IC-spanning diagnostic refinement from /122 is testable**: a non-IC-spanned ETH derivative (e.g., ETH realized-volatility regime classifier with pairwise |IC| < 0.40 against the 2 critical incumbents) is the cleanest follow-up to /122 — it directly tests whether the BROAD ETH-OHLCV hypothesis is FALSIFIED (in which case both /122 and /123 NEGATIVE close the axis cleanly) or whether the /122 outcome was specific to the eth_ret_3d primitive (in which case /123 surfaces incremental signal).
4. **Option B (longer-cadence labels) is structurally heavier**: requires REQUIRED_GAP retuning, walk-forward recomputation, label-barrier-scaling coherent redesign — a higher-risk axis that should be deferred to a slot where the cycle-7 axis-1 narrative is fully adjudicated. If /123 (Option A) also NEGATIVE, the cross-asset axis-1 closes definitively and Option B becomes the natural /124 axis.

### 8.3 /123 EDA seed (preliminary candidates pre-screened from theory)

To accelerate the QR EDA at /123, three pre-theoretical candidates that score well against the tightened pairwise-IC gate:

| ID | Formula | Hypothesis | Predicted |IC| with vwap_dev_20 | Predicted |IC| with regime_momentum_signed_5d |
|---|---|---|---:|---:|
| **B1** | `eth_realized_vol_50 / sym_realized_vol_50` | ETH-vs-symbol vol regime ratio; expected to capture cross-asset volatility-regime divergence (a structurally DIFFERENT signal than directional cross-asset return) | ≤ 0.25 (vol is structurally orthogonal to directional momentum) | ≤ 0.30 |
| **B2** | `rank(eth_ret_3d, [BTC, SOL, BCH, LDO, TRX])` (ETH percentile rank in 5-asset cross-section) | ETH's cross-sectional dominance regime; rank is a non-linear transformation of `eth_ret_3d` that decorrelates the absolute level | ≤ 0.40 (rank-monotone transformation of eth_ret_3d preserves SOME correlation) | ≤ 0.45 |
| **B3** | `eth_funding_z30 − btc_funding_z30` (ETH-vs-BTC funding-rate divergence) | Cross-asset positioning regime; funding rates are derivative-metadata (NOT OHLCV) so the 7-FEED structural verdict applies — REQUIRES re-evaluation of whether the 7-FEED verdict closes cross-asset funding-rate DIFFERENCES specifically (vs absolute funding rates which are closed) | ≤ 0.15 (funding is orthogonal to spot momentum) | ≤ 0.20 |

**Top-priority candidate**: **B1 (ETH-vs-symbol vol regime ratio)**. It is the cleanest non-IC-spanned candidate, structurally orthogonal to the directional momentum signal that /122 found INERT, and tests a NEW hypothesis (cross-asset volatility-regime divergence as a directional signal) rather than re-walking the /122 hypothesis. B1's information content is structurally distinct from any of the 15 features in `V3_FEATURE_COLUMNS_TOP_N`.

**B2 deferred**: rank features carry partial residual correlation with the base primitive; the predicted |IC| with `regime_momentum_signed_5d` is at the gate boundary (~0.45) which is risky.

**B3 deferred**: requires re-evaluation of the 7-FEED structural verdict scope (whether cross-asset DIFFERENCES of derivative-metadata fall under the closure or whether only absolute derivative-metadata features are closed). This adjudication is a separate methodology question that should not be entangled with a cross-asset feature EXPLORATION.

### 8.4 /123 brief Section 8 pre-registration mandate (carried forward from /122 Critic FINAL recommendation 3)

The /122 Critic FINAL recommendation 3 is binding for /123:

> **Pre-register dual-anchor disambiguation explicitly in /123 brief Section 8**: the /122 brief's anchor block declared dual-anchor but Section 8 criteria 2-8 did NOT explicitly specify which anchor applies to each. The /122 outcome is unambiguous, but a future EXPLORATION where IS Δ falls in the [−0.05, +0.05] EXPLORATION-anchor band but outside the /121-multi-seed band could produce verdict ambiguity.

/123 brief Section 8 MUST explicitly specify for each criterion which anchor (multi-seed /121 vs architecturally-adjusted EXPLORATION estimate) is the falsifier band reference.

---

## 9. Cycle-7 status

**Cadence**: slot 1/10 EXPLORATION done (this iteration). 9 EXPLORATIONs remain + /132 CONFIRMATION.

**Outstanding constraints carried into cycle 7** (from `project_v3_cycle7_setup.md`; UNCHANGED at /122):

| # | Constraint | Threshold | /121 Observed (anchor) | /122 Observed |
|---|---|---:|---:|---:|
| 1 | OOS Sharpe ≥ +1.0 | ≥ 1.0 | +0.9682 | +1.1642 (above floor — but classified NEGATIVE-INERT, not bundled) |
| 2 | OOS trades ≥ 130 | ≥ 130 | 98 | 102 |
| 3 | OOS trades/month ≥ 10 | ≥ 10 | 7.0 | 7.3 |
| 4 | Top-symbol concentration ≤ 30% | ≤ 30% | BCH 95.76% | BCH 95.46% (structural property of universe) |
| 5 | Legacy DSR > 0.95 | > 0.95 | 0.0 | 0.0 (structural) |
| 6 | DSR_relative > 0.95 (Path B4) | > 0.95 | 1.0 | 0.9999 |

**No constraint material change at /122**. The OOS Sharpe ≥ +1.0 nominal observation (+1.1642) is NOT a clearance because the headline is classified NEGATIVE-INERT — the OOS lift is a single-seed loss-surface artifact, not bundleable.

---

## 10. Memory updates

1. **APPEND to `feedback_v3_promising_feature_mechanical.md`** — /122 RECURRENCE note: the loss-surface dissociation mechanism (canonical at /119 C6) RECURS in a non-engineered OFF-THE-SHELF cross-asset primitive class at /122. The classification differs (NEGATIVE-INERT at /122 vs PROMISING-FEATURE-MECHANICAL at /119) because the broad-based-per-symbol-IS-positive-Δ leg (condition c) fails at /122 (single-symbol-carrier TRX with BCH+LDO IS negative). The diagnostic refinement: pairwise IC matrix with each of `vwap_dev_20` + `regime_momentum_signed_5d` is the controlling gate (< 0.40 strict for OFF-THE-SHELF cross-asset primitives), tighter than the joint-R² < 0.70 EDA T2 screen.

2. **UPDATE `project_v3_cycle7_setup.md`** — /122 EXPLORATION slot 1 of 10 COMPLETED with NEGATIVE-INERT verdict. eth_ret_3d primitive CLOSED. /123 advances to NEXT EXPLORATION slot (slot 2/10). Recommended axis: NON-IC-SPANNED ETH-derived primitive (Option A) with top candidate B1 (ETH-vs-symbol vol regime ratio); axis-3 longer-cadence labels deferred to /124 if /123 also NEGATIVE.

3. **MEMORY.md index** — no new feedback file at /122 (the lesson is captured as an APPEND to existing `feedback_v3_promising_feature_mechanical.md`). Index unchanged.

---

## 11. Catalog entry

Per the standard schema, appended to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/122 | 2026-05-20 | cycle-7 axis-1 cross-asset (ETH OHLCV) | -0.3398 | +0.1960 | EXPLORATION-NEGATIVE-INERT — IC-spanned by vwap_dev_20 + regime_momentum_signed_5d | NO |
```

---

## 12. Closeout

iter-v3/122 closes the cycle-7 axis-1 slot 1 narrative with an EXPLORATION-NEGATIVE-INERT verdict. The eth_ret_3d primitive is CLOSED at /122; the broader ETH-OHLCV cross-asset hypothesis stays open subject to the tightened pairwise-IC gate (< 0.40 with each of `vwap_dev_20` AND `regime_momentum_signed_5d` for OFF-THE-SHELF cross-asset primitives). The /122 outcome is the FIRST cycle-7 RECURRENCE of the loss-surface dissociation mechanism (canonical at /119 C6) in a non-engineered feature class — the diagnostic conjunction yields NEGATIVE-INERT rather than PROMISING-FEATURE-MECHANICAL because the broad-based-per-symbol-IS-positive-Δ leg fails (single-symbol-carrier TRX + BCH+LDO IS aggregate negative). The IC-spanning-by-multiple-incumbents diagnostic refinement is now formalized: a new feature with no |IC|>0.70 single algebraic sister but TWO |IC|>0.50 partial-spanning incumbents is structurally INERT at the importance-allocation level, and the pairwise IC matrix is a tighter gate than the joint-R² T2 screen.

**/123 advances to NEXT EXPLORATION slot 2/10 with axis recommendation: NON-IC-SPANNED ETH-derived primitive (Option A), top candidate B1 (`eth_realized_vol_50 / sym_realized_vol_50`).** The /123 brief Section 8 MUST explicitly specify per-criterion anchor disambiguation (multi-seed /121 vs architecturally-adjusted EXPLORATION estimate) per the /122 Critic FINAL recommendation 3 binding mandate. No BASELINE update at /122.
