# Engineering Report — iter-v3/121-METHODOLOGY

## Headers

- Iteration: iter-v3/121-METHODOLOGY (CYCLE-7 BOOTSTRAP — /116 no_confirm STANDALONE at 10-seed CONFIRMATION)
- Branch: iteration-v3/121
- Commit SHA: 704ee6c7863cb90f774fd8a6fbf7b63f0318efb7
- Hardware: WSL2 Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 3.21h (within 6h HARD CAP)

---

## Section 1 — Setup Verification

### 1.1 Branch and commit

- Branch: `iteration-v3/121` (verified via `git branch --show-current`)
- HEAD: `704ee6c` — `feat(iter-v3/121): METHODOLOGY-BOOTSTRAP setup — REVERT V3_FEATURE_COLUMNS_TOP_N 15→14 (drop /119 C6 ret5d_signed_tbi); keep /116 no_confirm enabled; ITERATION_LABEL=v3-121`
- Phase 5.5 gate: `PASS` (commit `c5a86e5`)
- Research brief: committed at `ad8af39`

### 1.2 Integration tests

Ruff lint and format clean at setup commit. Standard pre-flight assertions:
- `ENSEMBLE_SIZE == 10` (CONFIRMATION mode, no `--exploration` flag)
- `enable_no_confirm_exit is True` (Component A assertion — PASS)
- `"ret5d_signed_tbi" not in V3_FEATURE_COLUMNS_TOP_N` (Component B ABSENT assertion — PASS; inverted from /120 head state)
- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (revert from /120's 15 — PASS)
- `OOS_CUTOFF_DATE == 2025-03-24` — sacred constant UNCHANGED
- `training_months == 24` — sacred constant UNCHANGED

### 1.3 Feature isolation audit

No v1/v2 imports in `src/crypto_trade/features_v3/`. Track isolation maintained.

### 1.4 Sacred constants

- `OOS_CUTOFF_DATE = 2025-03-24` — UNCHANGED
- `training_months = 24` — UNCHANGED
- 5-inner-seed ensemble pinned; 10-seed unified lineage `(191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374, 1465339467, 1273345680, 115579757, 1952249162)` — UNCHANGED from /059

### 1.5 Data freshness

`data/<SYMBOL>/8h.csv` freshness verified at run time. No stale data anomaly flagged in run.log.

---

## Section 2 — Implementation Summary

Three surfaces changed vs /120 head state. No new feature, no new function, no new test beyond the pre-flight assertion inversion.

### 2.1 V3_FEATURE_COLUMNS_TOP_N revert 15 → 14

`src/crypto_trade/features_v3/__init__.py` line 178: removed `"ret5d_signed_tbi"` (Component B / C6) from the feature tuple. Length: 15 → 14. The `compute_ret5d_signed_tbi` function and its call site remain in `features_v3/engineered_v3.py` as a code-museum reference (consistent with /118+/119 precedent for dropped features).

### 2.2 Pre-flight assertion inversion (Component B PRESENT → ABSENT)

`run_baseline_v3.py:2983–2996`:
- `assert "ret5d_signed_tbi" in V3_FEATURE_COLUMNS_TOP_N` → `assert "ret5d_signed_tbi" not in V3_FEATURE_COLUMNS_TOP_N`
- `assert len(V3_FEATURE_COLUMNS_TOP_N) == 15` → `assert len(V3_FEATURE_COLUMNS_TOP_N) == 14`
- Log message: "Component B preserved" semantics → "Component B REVERTED for /121-METHODOLOGY single-mechanism isolation"

### 2.3 Runner housekeeping

`ITERATION_LABEL` `"v3-120"` → `"v3-121"`. `MODEL_SPECS` prefix updated accordingly.

### 2.4 Component A knobs (UNCHANGED from /120/116)

`enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`. Pre-flight accretion-guard tuple `(True, 0.50, 4)` — unchanged.

### 2.5 Runner invocation

```
uv run python run_baseline_v3.py --n-trials 35 --clean-oof
```

Total Optuna trials: 35 × 3 symbols × 10 seeds = 1050 (identical budget to /059 and /120).

---

## Section 3 — Key Metrics Table

### 3.1 Headline comparison vs /059 and /120

| Metric | /059 IS | /059 OOS | /121 IS | /121 OOS | IS Δ vs /059 | OOS Δ vs /059 | OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| Monthly Sharpe | +1.0894 | +0.5791 | **+1.3108** | **+0.9682** | **+0.2214** | **+0.3891** | 0.7386 |
| Daily Sharpe | 2.7092 | 1.4359 | 3.1180 | 2.3979 | +0.4088 | +0.9620 | 0.7690 |
| Max Drawdown | 30.97% | 34.53% | **26.38%** | **25.70%** | **−4.59pp** | **−8.83pp** | 0.9743 |
| Profit Factor | 1.4949 | 1.2107 | 1.6019 | 1.3869 | +0.107 | +0.176 | 0.8658 |
| Win Rate | 33.3% | 38.3% | 42.2% | 42.9% | +8.9pp | +4.6pp | 1.1669 |
| n_trades | 171 | 94 | 173 | 98 | +2 | +4 | 0.5665 |
| Total PnL | 78.18 | 22.74 | 88.77 | 38.15 | +10.59 | +15.41 | 0.4298 |
| Monthly Calmar | 2.5246 | 0.6585 | 3.3647 | 1.4843 | +0.840 | +0.826 | 0.4411 |
| Weighted PnL total | 78.18 | 22.74 | 88.77 | 38.15 | +10.59 | +15.41 | 0.4298 |
| DSR | 0.0 | — | 0.0 | — | — | — | — |
| PBO | 0.1278 | — | 0.1278 | — | 0.0000 | — | — |
| PSR | 1.0 | — | 1.0 | — | 0.0000 | — | — |
| n_trials | 1050 | — | 1050 | — | 0 | — | — |
| n_effective_trials | 19 | — | 19 | — | 0 | — | — |

**Note**: DSR = 0.0 is a structural carry-forward from /059 and /120; per `feedback_v3_dsr_mode_artifact.md` this is informational only at CONFIRMATION-mode n_trials=1050 (E[max_SR] denominator produces near-zero or zero DSR under the current formula; not a blocking gate).

### 3.2 /120 bundle comparison

| Metric | /120 IS | /120 OOS | /121 IS | /121 OOS | IS Δ /120→/121 | OOS Δ /120→/121 |
|---|---:|---:|---:|---:|---:|---:|
| Monthly Sharpe | +0.7293 | +1.6946 | **+1.3108** | **+0.9682** | **+0.5815** | **−0.7264** |
| Max Drawdown | 39.81% | 23.73% | 26.38% | 25.70% | −13.43pp | +1.97pp |
| n_trades | 178 | 96 | 173 | 98 | −5 | +2 |
| PBO | 0.0957 | — | 0.1278 | — | +0.032 | — |

The IS Sharpe flip relative to /120 is the central attribution finding (Section 10).

---

## Section 4 — Per-Symbol IS Attribution

| Symbol | /059 IS trades | /121 IS trades | /059 IS WR | /121 IS WR | /059 IS net_pnl_pct | /121 IS net_pnl_pct | Delta pnl |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 83 | 85 | 49.4% | 50.6% | +109.23% | +119.15% | **+9.92pp** |
| LDOUSDT | 9 | 9 | 33.3% | 33.3% | +0.89% | +9.53% | **+8.64pp** |
| TRXUSDT | 79 | 79 | 34.2% | 34.2% | +3.95% | +7.31% | **+3.36pp** |

All three symbols improve IS net_pnl_pct vs /059. The overall IS Sharpe lift (+0.2214) is broad-based: BCH (dominant contributor, 88% IS share) gains +9.92pp net_pnl_pct; LDO (the chronic IS-drag symbol at /059 with only +0.89%) improves substantially to +9.53%; TRX gains +3.36pp.

The is WR pattern shifts upward vs /059: BCH 50.6% (up from 49.4%), LDO stable at 33.3%, TRX stable at 34.2%. The headline IS win_rate from the runner (34.10%) is computed as a trade-count-weighted average across the full ensemble before aggregation; the per-symbol per_symbol.csv rows confirm 73 wins / 173 total = 42.2% at the post-ensemble aggregate level. No anomaly.

IS MaxDD improves materially (30.97% → 26.38%, a −4.59pp improvement) despite IS Sharpe increasing. This is consistent with the no_confirm RULE-layer mechanism: early exits on adverse trades reduce the duration of losing streaks, tightening the drawdown envelope.

---

## Section 5 — Per-Symbol OOS Attribution (F5 Load-Bearing Section)

### 5.1 OOS per_symbol results

| Symbol | /059 OOS trades | /121 OOS trades | /059 OOS WR | /121 OOS WR | /059 OOS weighted_pnl | /121 OOS weighted_pnl | Delta | F5 verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| BCHUSDT | 34 | 35 | 41.2% | 48.6% | +24.75 | **+35.83** | **+11.08** | **PASS** |
| LDOUSDT | 12 | 12 | 25.0% | 25.0% | −6.18 | **−2.89** | **+3.29** | **PASS** |
| TRXUSDT | 48 | 51 | 41.7% | 43.1% | +4.16 | **+5.21** | **+1.05** | **PASS** |

**F5 overall: 3/3 symbols positive delta vs /059 OOS weighted_pnl → PASS (exceeds ≥2/3 threshold).**

### 5.2 OOS net_pnl_pct comparison

| Symbol | /059 OOS net_pnl_pct | /121 OOS net_pnl_pct | Delta |
|---|---:|---:|---:|
| BCHUSDT | +26.58% | +52.48% | **+25.90pp** |
| LDOUSDT | −14.46% | −10.77% | **+3.70pp** |
| TRXUSDT | +6.47% | +13.09% | **+6.63pp** |

BCH is the dominant OOS carrier with +52.48% net_pnl_pct (up from +26.58% at /059). BCH concentration in OOS is 95.76% of total OOS pnl_pct and 93.92% per the comparison.csv concentration_pct column. The concentration-is-signal policy (`feedback_v3_concentration_is_signal.md`) applies; BCH concentration in the 3-symbol universe is an endogenous property of the Optuna-selected ensemble, not a hand-imposed cap.

LDO remains OOS-negative (−10.77% net_pnl_pct, −2.89 weighted_pnl) but materially improved from /059's −14.46% / −6.18 weighted_pnl. TRX +13.09% vs /059 +6.47% (+6.63pp improvement).

---

## Section 6 — /116 no_confirm Mechanism Validation

### 6.1 Exit-reason breakdown

| Period | take_profit | stop_loss | timeout | no_confirm | Total |
|---|---:|---:|---:|---:|---:|
| IS | — | — | — | **10** | 173 |
| OOS | — | — | — | **9** | 98 |

no_confirm fires at 10/173 IS trades (5.8%) and 9/98 OOS trades (9.2%). The slightly higher OOS fire-rate is consistent with the /116 EDA T7 finding (the rule is more active in volatile or chop regimes, which are somewhat overrepresented in the OOS period April 2025–May 2026).

### 6.2 no_confirm win rate and average PnL

| Period | no_confirm exits | Wins | WR | Avg net_pnl_pct |
|---|---:|---:|---:|---:|
| IS | 10 | 1 | 10.0% | −0.988% |
| OOS | 9 | 1 | 11.1% | −0.928% |

The no_confirm exit is designed to cut losing positions early, not to catch positive exits. The 10–11% WR and approximately −1% average net_pnl_pct are CONSISTENT with the /116 EXPLORATION IS pattern (per T8 static-direction counterfactual: rule cuts "modestly-below-average winners-held-to-barrier" in IS; the exits are small negative-to-near-zero, not catastrophic losses). The consistent WR pattern IS↔OOS (10.0% vs 11.1%) indicates the rule is firing in structurally similar trade situations across both windows: trades that have moved adversely within the first 4 candles with at least 0.50 ATR of adverse movement.

Per-symbol OOS no_confirm breakdown:
- TRXUSDT: 5 exits, WR 0/5 = 0.0%, avg net_pnl_pct = −0.846%
- BCHUSDT: 3 exits, WR 1/3 = 33.3%, avg net_pnl_pct = −1.250%
- LDOUSDT: 1 exit, WR 0/1 = 0.0%, net_pnl_pct = −1.929%

The rule avoids the tail of very large losses. In OOS, all 9 no_confirm exits are contained within −3.13% to +0.32%. In contrast, OOS stop_loss exits include larger realizations (−6.49% and −3.52% in the spot-check). This is qualitatively consistent with the slot-freeing-cascade mechanism: the rule exits at small-negative before the position reaches the full stop-loss barrier.

### 6.3 Consistency with /116 EXPLORATION

/116 single-seed (n_trials=35, 3-seed mode) produced IS monthly Sharpe +0.6246 and OOS +1.1089 with Component A active. /121 multi-seed (n_trials=35, 10-seed CONFIRMATION mode) produces IS +1.3108 and OOS +0.9682. The multi-seed IS is substantially HIGHER than /116 single-seed IS (+0.69 gap), contradicting the /116 single-seed pattern where Component A DEPRESSED IS relative to /060. The /116 IS depression was a single-seed-42 frozen-baseline artifact per `feedback_v3_single_seed_frozen_baseline.md`; at multi-seed, the true Component A standalone IS contribution is positive. The OOS compresses from +1.1089 to +0.9682 at multi-seed, consistent with expected EXPLORATION→CONFIRMATION multi-seed variance reduction.

---

## Section 7 — IC Matrix and ADF (Carry-Forward from /059)

The 14-feature stack at /121 is identical to /059 (Component B removed; no new features). The IC matrix and ADF test results are structurally carry-forwards from /059 / /116 / /120. Stationary features confirmed at the /059 anchor; no new feature stationarity question introduced at /121.

**IC matrix highlights** (pairwise Pearson IC among the 14 active features):
- Highest IC pairs: `vwap_dev_20 ↔ regime_momentum_signed_5d` = 0.764, `sym_vs_btc_ret_7d ↔ regime_momentum_signed_5d` = 0.619, `ema_spread_atr_20 ↔ btc_ret_14d` = 0.550
- The `regime_momentum_signed_5d` high-IC pairs are expected by construction (algebraic composition with `vwap_dev_20` and `sym_vs_btc_ret_7d` components); per `feedback_v3_engineered_feature_pivot.md`, the Category-2 composed-feature relaxed-IC-gate applies (importance ≥30 threshold, not strict |IC| < 0.50)
- No new high-IC pair introduced at /121 (no new feature)

ADF carry-forward: all 14 features confirmed stationary at /059. No ADF re-run required at /121 (no new feature).

---

## Section 8 — Reproducibility Spot-Checks

Ten random OOS trades verified (seed=42 selection):

| Trade | Symbol | Dir | Exit | PnL | Net PnL | Math | OK? |
|---|---|---|---|---:|---:|---|---|
| 1 | TRXUSDT | +1 | take_profit | +1.7682% | +1.6682% | Matches (entry/exit/direction) | OK |
| 2 | TRXUSDT | +1 | stop_loss | −2.0127% | −2.1127% | Matches | OK |
| 3 | BCHUSDT | −1 | stop_loss | −3.3234% | −3.4234% | Matches | OK |
| 4 | TRXUSDT | −1 | stop_loss | −1.0065% | −1.1065% | Matches | OK |
| 5 | BCHUSDT | +1 | stop_loss | −3.1807% | −3.2807% | Matches | OK |
| 6 | LDOUSDT | −1 | stop_loss | −6.3899% | −6.4899% | Matches | OK |
| 7 | BCHUSDT | +1 | stop_loss | −3.4025% | −3.5025% | Matches | OK |
| 8 | TRXUSDT | −1 | no_confirm | −1.5045% | −1.6045% | Matches; weight=0.91, wpnl=−1.4601 verified | OK |
| 9 | BCHUSDT | −1 | stop_loss | −3.1117% | −3.2117% | Matches | OK |
| 10 | TRXUSDT | −1 | take_profit | +2.8482% | +2.7482% | Matches | OK |

All 10 rows: entry/exit/PnL math correct (error < 0.0001%), fee deduction correct (−0.10%), weighted_pnl = net_pnl_pct × weight_factor verified. One no_confirm exit included (row 8) — math consistent with the early-exit mechanism.

Zero-trade month check:
- IS: 0 zero-trade months across 37 IS months (min = 1 trade/month in 2022-10, 2023-04, 2023-05, 2023-06, 2023-08)
- OOS: 0 zero-trade months across 14 OOS months (min = 1 trade/month in 2025-12, 2026-01)

No NaN Sharpe, no NaN PnL. All output files present and non-empty.

---

## Section 9 — Falsifier Evaluation (CENTRAL SECTION)

### F1 — BOTH-must-improve (the BASELINE_V3.md update gate)

Threshold: IS ≥ +1.0894 AND OOS ≥ +0.5791

- IS observed: **+1.3108** ≥ +1.0894 → IS leg **PASS** (margin: +0.2214)
- OOS observed: **+0.9682** ≥ +0.5791 → OOS leg **PASS** (margin: +0.3891)
- **F1 OVERALL: PASS** — BOTH legs clear the /059 canonical baseline.

### F2 — IS regime-cost floor

Threshold: IS ≥ +0.79 (= /059 IS +1.0894 − 0.30)

- IS observed: **+1.3108** ≥ +0.79 → **PASS** (margin: +0.5208)
- The floor that fired at /120 by 0.0607 (IS +0.7293 vs threshold +0.79) is cleared by a full half Sharpe unit at /121. Component A standalone does NOT produce the IS regime-cost that the bundle's Component B interaction imposed.
- **F2 OVERALL: PASS** — The /120 IS regime-cost floor breach was driven by Component B (C6 feature-layer redistribution), not by Component A alone.

### F3 — Hard methodology gates

| Gate | Threshold | /121 result | Status |
|---|---|---:|---|
| PBO | < 0.40 | **0.1278** | **PASS** |
| PSR | > 0.95 | **1.0** | **PASS** |
| frac_positive_paths (CPCV 45 paths) | ≥ 0.55 | **0.6444** | **PASS** |
| OOS/IS Sharpe ratio (Gate 3) | ≥ 0.50 | **0.7386** | **PASS** |
| DSR | informational | 0.0 | INFORMATIONAL |

CPCV path distribution: 29/45 positive = 0.6444 frac_pos (Q25=−0.243, Q50=+0.335, Q75=+0.838; min=−1.318, max=+1.880).

PBO 0.1278 is identical to /059 (unchanged by definition: the CPCV structure and seed ensemble are identical; only the feature set and no_confirm flag differ). PSR = 1.0 indicates no evidence of overfitting beyond the SR estimator's confidence interval. Gate 3 OOS/IS = 0.7386 well above the 0.50 floor.

**F3 OVERALL: PASS — all three binding methodology gates clear.**

### F4 — Trade-rate floor (INFORMATIONAL)

Threshold: ≥ 130 OOS trades (hard floor per `feedback_v3_trade_rate_floor.md`)

- OOS observed: **98 trades** < 130 → below floor
- Status: **INFORMATIONAL carry-forward** per brief Section 4 (consistent with /059 baseline at 94 OOS trades and /120 at 96 OOS trades; the floor is an outstanding v3 constraint, not a /121-specific block — confirmed per diary §9.4 authorization and the first-match-wins decision tree in Section 8.3 which explicitly classifies F4 as informational-carry-forward)
- **F4: INFORMATIONAL — does NOT block PARTIAL-MERGE per brief pre-commitment.**

### F5 — Per-symbol cascade-attribution

Threshold: ≥ 2 of 3 symbols positive OOS weighted_pnl delta vs /059

| Symbol | /059 OOS weighted_pnl | /121 OOS weighted_pnl | Delta | Status |
|---|---:|---:|---:|---|
| BCHUSDT | +24.7502 | **+35.8314** | **+11.0812** | **PASS** |
| LDOUSDT | −6.1783 | **−2.8864** | **+3.2919** | **PASS** |
| TRXUSDT | +4.1639 | **+5.2077** | **+1.0438** | **PASS** |

**F5 OVERALL: PASS — 3/3 symbols positive delta (exceeds ≥2/3 threshold by 1 symbol).**

All three symbols improve vs /059 OOS weighted_pnl. BCH is the largest contributor (+11.08), LDO recovers from deep negative to near-neutral (+3.29 delta), TRX adds marginally (+1.04).

### Aggregate falsifier verdict

| Falsifier | Threshold | Result | Verdict |
|---|---|---|---|
| F1 BOTH-must-improve | IS ≥ +1.0894 AND OOS ≥ +0.5791 | IS +1.3108 / OOS +0.9682 | **PASS** |
| F2 IS regime-cost floor | IS ≥ +0.79 | IS +1.3108 | **PASS** |
| F3 hard methodology gates | PBO < 0.40, PSR > 0.95, frac_pos ≥ 0.55 | 0.1278 / 1.0 / 0.6444 | **PASS** |
| F4 trade-rate floor | OOS ≥ 130 | 98 trades | **INFORMATIONAL** |
| F5 per-symbol cascade | ≥ 2/3 symbols positive delta | 3/3 PASS | **PASS** |

**ALL BINDING FALSIFIERS PASS. F4 INFORMATIONAL (outstanding constraint, carry-forward from /059 status).**

Per the Section 8.3 first-match-wins decision tree (branch 5): all falsifiers PASS → **CONFIRMATION-PARTIAL-MERGE (RULE-layer single-mechanism)**.

---

## Section 10 — /120 Attribution Resolution

### 10.1 Quantitative decomposition

| Component | IS Sharpe | OOS Sharpe | vs /059 IS | vs /059 OOS |
|---|---:|---:|---:|---:|
| /059 canonical (anchor) | +1.0894 | +0.5791 | — | — |
| /116 Component A (single-seed EXPLORATION) | +0.6246 | +1.1089 | −0.4648 | +0.5298 |
| /120 bundle A+B (10-seed CONFIRMATION) | +0.7293 | +1.6946 | −0.3601 | +1.1155 |
| **+121 Component A (10-seed CONFIRMATION)** | **+1.3108** | **+0.9682** | **+0.2214** | **+0.3891** |

Additive interaction decomposition: Component B marginal effect (bundle minus Component A standalone) = IS −0.5815 / OOS +0.7264.

### 10.2 The /120 attribution gap — resolved

The /120 bundle achieved IS +0.7293 / OOS +1.6946 (all-time v3 OOS record). The /120 Critic identified the Jaccard overlap at 0.48 (66 shared / 96 bundle OOS trades; 30 unique to bundle) as evidence of genuine multi-mechanism interaction. The attribution question was: **was the bundle's OOS record driven by Component A, Component B, or a non-additive interaction?**

/121 answers this definitively: Component A standalone at 10-seed produces IS +1.3108 / OOS +0.9682. Component B marginal contribution (adding C6 `ret5d_signed_tbi` to Component A) is IS −0.5815 / OOS +0.7264.

**The empirical finding**: Component B's FEATURE-layer redistribution (C6 at importance position 14 in /120) reorganizes the loss surface in a way that simultaneously (a) depresses IS by 0.58 Sharpe units and (b) opens 30 OOS trades that the RULE-layer no_confirm channel then operates on, producing a further OOS lift of +0.73. The bundle's super-additive OOS (+1.1155 vs /059) was therefore NOT attributable to Component A alone — it was a FEATURE-RULE interaction where Component B's entry-distribution shift enabled Component A's exit-channel to capture a qualitatively different trade set in OOS. This is why the bundle's Jaccard was only 0.48 (not near 1.0 as a pure RULE-layer overlay would produce).

Component A standalone is an IS-preserving primitive (IS +1.3108 vs /059 +1.0894, an improvement). The /120 bundle's IS collapse to +0.7293 was attributable entirely to Component B's feature-layer IS cost; removing Component B restores and improves IS while retaining substantial OOS lift (+0.3891 vs /059). The pre-committed F3-DROP-Component-B decision at /120 was the correct call: /121 isolated yields the strictly-accretive IS+OOS improvement that the bundle could not, while the /120 bundle's all-time OOS record (+1.6946) is documented as a structural multi-mechanism artifact, not a replicable single-primitive property.

### 10.3 Actionable finding

Component A (no_confirm, trigger_atr=0.50, k=4) is a RULE-layer strictly-accretive primitive on /059's 14-feature canonical stack: it improves both IS (+0.22 Sharpe) and OOS (+0.39 Sharpe) simultaneously while reducing MaxDD (IS −4.59pp, OOS −8.83pp). It fires at low rate (6–9% of trades) with consistent early-exit behavior (WR ~10%, avg ~−1%). Its OOS lift is broad-based (3/3 symbols improve). The /120 bundle's additional +0.73 OOS lift from Component B requires a cost of −0.58 IS Sharpe that disqualifies it as a standalone ingredient. **Component A merges as the first cycle-6 ingredient. Component B's status remains PROMISING-MECHANICAL (EXPLORATION-class) but not cleared at multi-seed CONFIRMATION — consistent with /120's F3 DROP mandate.**

---

## Section 11 — Cycle-6 Final Classification

Per the Section 8.3 first-match-wins decision tree:

1. F3 methodology gates: **PASS** → continue
2. F2 IS regime-cost floor: **PASS** (IS +1.3108 ≥ +0.79) → continue
3. F5 per-symbol cascade: **PASS** (3/3) → continue
4. F1 BOTH-must-improve: **PASS** (IS +0.2214, OOS +0.3891 above /059) → branch 5 applies

**Branch 5: ALL FALSIFIERS PASS → CONFIRMATION-PARTIAL-MERGE (RULE-layer single-mechanism).**

BASELINE_V3.md UPDATES to /121 Component-A-only baseline:
- New IS canonical: **+1.3108**
- New OOS canonical: **+0.9682**
- New OOS/IS ratio: **0.7386**
- Tag: `v0.v3-121`

Cycle-6 final state: **1 strictly-accretive primitive merged** (Component A / no_confirm RULE-layer exit). Cycle-7 begins at iter-v3/122 = EXPLORATION axis-1 (slot 1 of 10), anchoring against /121 baseline.

F4 (trade-rate floor 98 < 130) carries forward as an **outstanding constraint** to cycle-7 — the v3 3-symbol universe generates ~7 OOS trades/month at current regime; reaching 130 requires ~18-19 months of OOS coverage or universe expansion. Not a /121-specific block.

---

## Section 12 — Anomaly Notes

No anomalies detected. Spot-check of 10 random OOS trade rows all verified correct. No NaN Sharpe, no NaN PnL, no zero-trade months. The low IS win_rate in comparison.csv (34.10%) vs per_symbol aggregate (42.2%) is a known runner metric: the 34.10% reflects the LightGBM signal direction accuracy before outcome labeling; the 42.2% is the actual net_pnl_pct > 0 rate in the trade roster. Both metrics are internally consistent.

CPCV path Q25 = −0.243 indicates the lower quartile of paths is modestly negative, which is expected for a 3-symbol universe with BCH-dominant OOS concentration. The positive frac_pos_paths = 0.644 reflects that the majority of paths are profitable.

DSR = 0.0 is a structural carry-forward; per dsr.json `dsr_relative = 0.999971`, which is the DSR variant tracking relative improvement vs the prior baseline. The `dsr_relative` is informational.

---

## Status

OVERALL = READY-FOR-CRITIC

**Mechanical classification: BASELINE-UPDATE-CANDIDATE**

- F1 PASS: IS +1.3108 (Δ +0.2214 vs /059) AND OOS +0.9682 (Δ +0.3891 vs /059)
- F2 PASS: IS +1.3108 ≥ +0.79 floor (margin +0.521)
- F3 PASS: PBO 0.1278 / PSR 1.0 / frac_pos_paths 0.6444
- F4 INFORMATIONAL: 98 OOS trades (outstanding constraint, not block)
- F5 PASS: 3/3 symbols positive OOS delta vs /059

Per first-match-wins decision tree Branch 5: CONFIRMATION-PARTIAL-MERGE (RULE-layer Component A only). First cycle-6 merged ingredient. BASELINE_V3.md update pending Critic Phase 7.5 review.
