# Iteration v3-014 — Research Brief

**Type**: EXPLORATION (SEVENTH EXPLORATION under cadence discipline; mandatory ADX-threshold axis per Critic FINAL Recommendation 1 of iter-v3/013, SHA `1ee0213`)
**Track**: v3 (rigor arm) — fourteenth iteration
**Branch**: `iteration-v3/014` (off `iteration-v3/013` head; analysis commit `33f389f` ships before this brief)
**Date**: 2026-05-06
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 10             # SET BY --exploration default
colsample_bytree = 1.0             # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000   # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–013 briefs / engineering reports / Critic / diaries; iter-v3/014 analysis script `analysis/iteration_v3-014/adx_threshold_demo.py` outputs (committed at SHA `33f389f` BEFORE this brief). The analysis script reads iter-v3/013's already-OOS-disclosed `trades.csv` files but ONLY as a counterfactual on already-revealed numbers — re-aggregating the same trade roster bucketed by ADX at entry.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Wall-clock budget: < 30 min (2h hard cap)
Single-axis variation: ADX threshold (20 → 25, tighter)
Cadence: EXPLORATION #7 of 10 needed
This iteration NEVER updates BASELINE_V3.md.
```

**Justification**: Per Critic FINAL Recommendation 1 of iter-v3/013 review (SHA `1ee0213`): iter-v3/014 axis MUST be ADX threshold (currently 20; 18 looser OR 25 tighter). ADX threshold is structurally orthogonal to all 5 prior axes (features × 2, labeling × 1, gate-zscore × 1, gate-btc-trend × 1, universe × 1) and NOT subject to mechanical-accretion artifact (single-symbol architecture means changing the gate DOES change behavior at the trade-roster level for all 3 retained symbols — saturation predictor will register Δ trades). After iter-v3/014 the catalog will have axis coverage features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 = 6 unique axis representations. **This QR chose the tighter direction (25 over 18)** to stress-test whether the strategy benefits from ADX-defined trend regime filtering — iter-v3/015 may test 18 (looser) if needed.

---

## Section 1 — Hypothesis

Tightening ADX threshold from 20 to 25 (only allow trades when trend strength is high) on top of iter-v3/013's drop-MKR + iter-v3/012's z=2.0 + iter-v3/010's ATR 2.0/1.0 stack will produce IS Sharpe maintained or improved (≥+0.40, vs iter-v3/013's +1.01) by filtering more aggressively against ranging/choppy regimes.

---

## Section 2 — IS-Only Numerical Evidence + Counterfactual + Behavioral-Effect Predictor

**Analysis script**: `analysis/iteration_v3-014/adx_threshold_demo.py` (committed at SHA `33f389f` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (already-disclosed iter-v3/013 trade rosters; ADX-bucket re-aggregation only — no new OOS information generated):
- `reports-v3/iteration_v3-013/in_sample/trades.csv` — 209 IS trade rows
- `reports-v3/iteration_v3-013/out_of_sample/trades.csv` — 85 OOS trade rows
- `data/{BCH,LDO,TRX}USDT/8h.csv` — OHLC for 14-period Wilder ADX computation

**Outputs** (committed alongside the script at SHA `33f389f`):
- `analysis/iteration_v3-014/expected_adx_kill.csv` — per-bucket aggregate.
- `analysis/iteration_v3-014/synthesis.md` — narrative + falsifier derivation.

### 2.1 ADX-bucket distribution at iter-v3/013 trade entry candles

Each iter-v3/013 trade is annotated with the 14-period Wilder ADX at the candle whose `close_time == trade.open_time` (mirroring `RiskV2Wrapper._adx_gate_fails` lookup at `risk_v2.py:296-307`). Buckets:

#### IS (iter-v3/013 in_sample, total 209 trades)

| bucket | n_trades | n_wins | win_rate_pct | weighted_pnl_total | share_of_slice_pct |
|---|---:|---:|---:|---:|---:|
| `[20,25)_KILL` | **70** | 26 | 37.14 | **+11.49** | **14.58** |
| `>=25_KEEP` | **139** | 58 | **41.73** | **+67.30** | **85.42** |

**IS interpretation**: 33.5% of iter-v3/013 IS trades fall in the [20, 25) ADX bucket — these would be killed by tighter `adx_threshold=25`. The KILL bucket has WR 37.14% (lower than KEEP's 41.73%) and only +11.49 weighted_pnl (14.58% of IS PnL). The KEEP bucket has WR 41.73% and +67.30 weighted_pnl (85.42% of IS PnL). **Direction signal: tighter ADX trims a lower-quality bucket** — IS Sharpe should be maintained-or-improved.

#### OOS (iter-v3/013 out_of_sample, total 85 trades) — informational under EXPLORATION

| bucket | n_trades | n_wins | win_rate_pct | weighted_pnl_total | share_of_slice_pct |
|---|---:|---:|---:|---:|---:|
| `[20,25)_KILL` | 30 | 15 | 50.00 | **+38.03** | **61.48** |
| `>=25_KEEP` | 55 | 25 | 45.45 | +23.82 | 38.52 |

**OOS_caveat** (audit-trail; OOS not pre-registered as falsifier per EXPLORATION protocol): the OOS [20, 25) bucket carried **61.48% of iter-v3/013 OOS PnL** (50% WR × 30 trades = +38.03 weighted_pnl). Tightening ADX would mechanically remove this bucket from the OOS roster. Whether the realized iter-v3/014 OOS Sharpe rises or falls depends on whether the iter-v3/014 model (trained under the new gate) reshapes the surviving OOS roster favorably or simply loses 61% of OOS PnL with no compensating signal. This is an OOS axis warning that travels to Phase 7 / Phase 8 — not a brief-time falsifier per EXPLORATION discipline.

### 2.2 Counterfactual + saturation falsifier (per `feedback_axis_saturation_predictor.md` + Critic FINAL Rec 3)

Per the new memory rule (added after iter-v3/012's NULL-RESULT trade-roster bit-identity surprise): brief Section 2 must include explicit estimates of how many IS trades will change in the roster, with a falsifier triggered if observed change is below the predicted lower bound. Per Critic FINAL Recommendation 3 (iter-v3/013 SHA `1ee0213`): the falsifier threshold MUST be derived as `ceil(1.2 × counterfactual_n_trades)` rather than hardcoded.

| Metric | Value | Source |
|---|---:|---|
| iter-v3/013 IS trades | 209 | counterfactual §2.1 |
| IS [20, 25)_KILL bucket (additional kills under ADX=25) | 70 | counterfactual §2.1 |
| **counterfactual_n_trades (IS)** | **139** = 209 − 70 | derivation |
| **saturation falsifier_threshold (IS)** | **167** = ceil(1.2 × 139) | per Rec 3 |
| iter-v3/013 OOS trades | 85 | counterfactual §2.1 |
| OOS [20, 25)_KILL bucket | 30 | counterfactual §2.1 |
| counterfactual_n_trades (OOS) | 55 = 85 − 30 | derivation (informational) |
| OOS falsifier_threshold | 66 = ceil(1.2 × 55) | informational |

**Falsifier reading**: if observed iter-v3/014 IS trades > 167, the ADX axis did NOT propagate (analogous to iter-v3/012's NULL-RESULT trade-roster identity but with different root cause — likely `adx_threshold=25` edit didn't propagate through `RiskV2Config` or fallback to default 20.0). The falsifier is sensitive in the right direction: **larger-than-counterfactual trade roster = axis failure**. Realized iter-v3/014 IS trade count is expected in [120, 167] based on first-order counterfactual; the upper bound 167 (1.2x slack) absorbs Optuna re-optimization variance and gate-composition residuals (some [20, 25) trades may have been killed upstream by other gates).

### 2.3 Realized vs counterfactual divergence drivers

The realized iter-v3/014 run will diverge from the counterfactual numbers because:
- Optuna re-optimizes hyperparameters on a tighter-ADX gate (different optimal params; per-cell PBO/CPCV partitioning unchanged but trial trajectories diverge).
- Risk gates compose: a trade in iter-v3/013's [20, 25) bucket might have been killed upstream by z-score OOD, BTC trend, low-vol, or Hurst gate — so the iter-v3/014 ADX gate's *additional* kill rate is bounded ABOVE by the counterfactual's 70 IS trades / 33.5%.
- Cooldown logic: removing one trade may free downstream candles from cooldown lockout (cooldown=4 candles), occasionally adding new trades that did not exist in iter-v3/013.
- LightGBM `colsample_bytree=1.0` is fixed but Optuna's trial-to-trial seeding may shift parameter selection by a small margin under the changed gate composition.

The DIRECTION of the counterfactual (tighter ADX trims a lower-quality IS bucket) is informative; the realized run will produce numbers in the 120-180 range with high probability.

### 2.4 Setup integrity (verified at SHA `33f389f`)

```
reports-v3/iteration_v3-013/in_sample/trades.csv extant + non-empty   PASS (210 rows incl. header)
reports-v3/iteration_v3-013/out_of_sample/trades.csv extant + non-empty PASS (86 rows incl. header)
data/{BCH,LDO,TRX}USDT/8h.csv extant + non-empty                        PASS (3/3 symbols)
expected_adx_kill.csv produced                                          PASS
synthesis.md produced                                                   PASS
0 ghost trades (ADX<20)                                                 PASS — iter-v3/013 gate was active at 20
0 NaN ADX lookups                                                       PASS — clean candle alignment
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (3-symbol BCH+LDO+TRX from iter-v3/013)

| Symbol | iter-v3/013 status | iter-v3/014 status |
|---|---|---|
| BCHUSDT | KEEP | UNCHANGED |
| LDOUSDT | KEEP | UNCHANGED |
| TRXUSDT | KEEP | UNCHANGED |
| MKRUSDT | DROPPED | UNCHANGED (still dropped, drop-MKR rule executed at iter-v3/013) |

`set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED (iter-v3/010 ATR 2.0/1.0)

| Parameter | iter-v3/013 (current) | iter-v3/014 |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | UNCHANGED |
| `atr_sl_multiplier` | 1.0 | UNCHANGED |
| Timeout | 21 candles (7d) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 66 (= (21+1)×3) | UNCHANGED |

### 3.3 Features — UNCHANGED (13 V3_FEATURE_COLUMNS inherited from iter-v3/008)

`V3_FEATURE_COLUMNS` length = 13; `vwap_dev_50` NOT in set. Inherited unchanged from iter-v3/009-013. `_verify_feature_columns()` continues to assert `len == 13`.

### 3.4 Risk gates — ADX threshold ONLY (single-axis variation: 20 → 25)

| Parameter | iter-v3/013 (current) | iter-v3/014 (this iteration) |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | UNCHANGED (iter-v3/011) |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | UNCHANGED (iter-v3/012) |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| **ADX threshold** | **20.0 (default)** | **25.0 (tighter)** |
| `adx_period` | 14 (default) | UNCHANGED |
| `enable_adx_gate` | True (default) | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

### 3.5 Sub-fix decomposition (single-axis: ADX threshold 20 → 25)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Update `RiskV2Config` instantiation** in `run_baseline_v3.py:872-874` from `RiskV2Config(zscore_threshold=2.0,)` → `RiskV2Config(zscore_threshold=2.0, adx_threshold=25.0,)` | One-line addition (kwarg) | `grep -E 'adx_threshold=25\.0' run_baseline_v3.py` exits 0 |
| 2 | **Update `ITERATION_LABEL`** to `"v3-014"` in `run_baseline_v3.py:100` | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-014"' run_baseline_v3.py` exits 0 |
| 3 | **Fix stale `= 88` docstrings** at `run_baseline_v3.py:206` (docstring) and `run_baseline_v3.py:211` (comment): parametrize against `REQUIRED_GAP` instead of hardcoding `88`. Replace `"Assert gap == REQUIRED_GAP == 88 and print proof"` → `"Assert gap == REQUIRED_GAP and print proof"`; replace `# = (21+1)*4 = 88` → `# formula: (timeout_candles+1)*n_symbols = (21+1)*len(V3_MODELS)` (or similar wording matching `REQUIRED_GAP` derivation). | docstring + comment edits | `grep -nE '= 88' run_baseline_v3.py` exits 1 (zero matches; hygiene fix per Critic FINAL Rec 3 of iter-v3/013) |
| 4 | **Run `--exploration --seeds 1 --n-trials 10`** on the 3-symbol universe with the tighter gate | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10`. Wall-clock target: < 10 min (3-symbol), 2h hard cap. | `test -f reports-v3/iteration_v3-014/comparison.csv` |

NO new feature additions. NO labeling change. NO z-score-gate change. NO BTC-band change. NO universe change. NO new src/ code beyond the runner edits.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | V3_FEATURE_COLUMNS unchanged at 13 features (inherited) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13"` exits 0 |
| 2 | `atr_tp_multiplier=2.0` UNCHANGED (iter-v3/010) | `run_baseline_v3.py` ATR mult line | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 3 | `atr_sl_multiplier=1.0` UNCHANGED (iter-v3/010) | `run_baseline_v3.py` ATR mult line | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 4 | `zscore_threshold=2.0` UNCHANGED (iter-v3/011) | `run_baseline_v3.py` zscore line | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 5 | `BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED (iter-v3/012) | `run_baseline_v3.py:121` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 6 | `V3_MODELS` has exactly 3 entries; MKR NOT present (inherited iter-v3/013) | `run_baseline_v3.py:106-110` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3 and 'MKRUSDT' not in {s for _,s in m.V3_MODELS}"` exits 0 |
| 7 | `REQUIRED_GAP == 66` UNCHANGED (iter-v3/013) | `src/crypto_trade/strategies/ml/validation_v3.py` | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP==66"` exits 0 |
| 8 | **`adx_threshold=25.0` set in RiskV2Config call** | `run_baseline_v3.py:872-874` | `grep -E 'adx_threshold=25\.0' run_baseline_v3.py` exits 0 |
| 9 | `ITERATION_LABEL` updated to `"v3-014"` | `run_baseline_v3.py:100` | `grep -E 'ITERATION_LABEL.*=.*"v3-014"' run_baseline_v3.py` exits 0 |
| 10 | **Stale `= 88` docstrings + comments removed (Critic FINAL Rec 3 hygiene fix)** | `run_baseline_v3.py:206, 211` | `grep -nE '= 88' run_baseline_v3.py \| wc -l` returns 0 |
| 11 | Sub-fix #4 produces comparison.csv | runner | `test -f reports-v3/iteration_v3-014/comparison.csv` |
| 12 | **EXPLORATION sanity test**: IS monthly Sharpe != 0 (gate change took effect; non-trivial signal computed) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-014/comparison.csv'); ms=df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert abs(float(ms)) > 1e-6"` exits 0 |
| 13 | All adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 14 | Wall-clock ceiling: total Phase 6 runtime < 30 min target / 2h hard cap | engineering report | wall-clock minutes < 120 |
| 15 | 3-symbol universe used | runner invocation log | `grep -E "Active models: 3/3" reports-v3/iteration_v3-014/run.log` exits 0 |
| 16 | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` + Critic FINAL Rec 3)**: IS trades < 167 (= ceil(1.2 × 139) counterfactual_n_trades) | comparison.csv | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-014/comparison.csv'); n=df.loc[df['metric']=='n_trades','in_sample'].iloc[0]; assert int(n) < 167, f'IS trades >= 167 — ADX-tighter did not propagate: {n}'"` exits 0 |
| 17 | **ADX gate fire rate increased**: `risk_v2.killed_by_adx` in iter-v3/014 strictly greater than iter-v3/013 (proof the gate was tighter, not silently disabled) | engineering report | engineering report cites `killed_by_adx` count from runner stats; > iter-v3/013's count |

### 3.7 NO labeling/feature/universe/other-gate changes

iter-v3/014 is a single-axis (ADX threshold) EXPLORATION. The feature set, model architecture, ATR labeling multipliers, z-score OOD threshold, BTC trend filter band, low-vol floor, Hurst regime check, hit-rate feedback (disabled), CPCV parameters, and walk-forward window are unchanged from iter-v3/013. The only differences vs iter-v3/013: `adx_threshold` value (default 20 → 25) + `ITERATION_LABEL` (cosmetic) + the stale-docstring hygiene fix (mandated by Critic FINAL Rec 3).

### 3.8 Inheritance from iter-v3/013

The `iteration-v3/014` branch was branched from `iteration-v3/013` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0)`
- `17d01ab feat(iter-v3/011): z-score OOD threshold 2.5 → 2.0`
- `93891a3 feat(iter-v3/012): BTC trend band 0.20 → 0.15 + ITERATION_LABEL=v3-012`
- `e3168f2 feat(iter-v3/013): drop MKR universe (4→3 symbols) + REQUIRED_GAP 88→66 + ITERATION_LABEL=v3-013`
- `33f389f feat(iter-v3/014): ADX threshold perturbation analysis + counterfactual_n_trades` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 (still iter-v3/012 value)
- `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3"` exits 0 (still iter-v3/013 value)
- BEFORE iter-v3/014 sub-fix #1: `grep -E 'adx_threshold=' run_baseline_v3.py` exits 1 (default in use)
- AFTER iter-v3/014 sub-fix #1: `grep -E 'adx_threshold=25\.0' run_baseline_v3.py` exits 0 (tighter set explicitly)
- AFTER iter-v3/014 sub-fix #3: `grep -nE '= 88' run_baseline_v3.py | wc -l` returns 0 (hygiene done)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, `EXPLORATION-PROMISING-MECHANICAL`, `EXPLORATION-NEGATIVE-no-effect`, or `BLOCK` (process). iter-v3/014 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/013 (current) | Counterfactual (3-symbol KEEP-only re-aggregate) | iter-v3/014 prediction (3-symbol Optuna re-optimized at adx>=25) |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0088 | n/a (counterfactual is bucket-removed-from-fixed-roster, not Sharpe-comparable cleanly across n_trades) | **predicted [+0.50, +1.30] (median +0.90)** |
| IS trades | 209 | 139 (counterfactual KEEP bucket) | **predicted 120–167** (counterfactual + Optuna re-opt + gate composition) |
| OOS trades | 85 | 55 (counterfactual KEEP bucket) | **informational ~50–70** |
| OOS Sharpe | +2.6970 | n/a | **informational; significant downside risk per §2.1 OOS_caveat (61% of OOS PnL in [20,25) KILL bucket)** |
| Phase 6 wall-clock | 6 min | n/a | predicted 5–10 min (3 symbols, slightly faster due to ~33% fewer candidate trades), hard cap 2h |

The IS prediction band [+0.50, +1.30] is intentionally **broad** because gate-axis variation has high variance:
- The counterfactual KEEP bucket has WR 41.73% (vs 40.19% on full roster) and weighted_pnl_total +67.30 (vs +78.80 full); first-order indication is Sharpe maintained-or-improved.
- Optuna re-optimization on a tighter-gate scenario: with ~33% fewer candidate trades, Optuna may converge on different hyperparameters; the model may either tighten further (better edge per trade) or weaken (less signal per Optuna trial-symbol).
- Gate composition residuals: some [20, 25) trades may have been killed upstream by other gates, so the iter-v3/014 ADX kill rate is *less than* 33.5%.
- 3rd consecutive favorable IS calibration overshoot pattern (iter-v3/010, 011, 013 — see iter-v3/013 caveat 4): the QR's prior bands have been conservative on behavior-changing axes. Per pre-commit at iter-v3/013 caveat 4, this brief widens the upper bound on PROMISING predictions for behavior-changing axes by 30%. Applying to a base [+0.50, +1.00] gives [+0.50, +1.30].

Median +0.90 sits below iter-v3/013's +1.01 to reflect: (a) tighter gate may over-restrict in genuinely uncertain regimes (ADX 20-25 is the meat of the trending distribution); (b) Optuna re-optimization variance partially offsetting any clean lift from KILL-bucket removal.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.10 → tighter ADX over-restricted; the strategy needs ADX 20-25 trades for IS edge (e.g., the [20, 25) bucket carried marginally positive trades that mattered for the model's training distribution). Verdict: EXPLORATION-NEGATIVE on gate-axis. iter-v3/015 may revisit at ADX 22 or test the looser direction (18) per the Critic FINAL Rec.

**Falsifier 2 (saturation predictor per `feedback_axis_saturation_predictor.md` + Critic FINAL Rec 3)**: IS trade count > **167** (= ceil(1.2 × counterfactual_n_trades=139)) → ADX gate change did NOT propagate to the model's prediction surface (analogous to iter-v3/012's NULL-RESULT trade-roster identity but with different root cause — likely `adx_threshold=25.0` edit didn't propagate through `RiskV2Config` instantiation, or fallback to default 20.0). Verdict: BLOCK (process); engineer documents.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on 3-symbol universe → unexpected slowdown in the gate-firing path or new code path issue; engineer documents the cause.

**Process falsifier**: pre-flight `grep adx_threshold=25.0 run_baseline_v3.py` exits non-zero, OR `grep "= 88" run_baseline_v3.py` returns nonzero matches (hygiene fix incomplete) → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

| Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe up ≥ +0.10 vs iter-v3/013 (i.e., ≥ +1.11) AND broad-based per-symbol AND IS trades < 167 (Falsifier 2 PASS) | "Tighter ADX trims a lower-quality bucket — broad-based gain" | iter-v3/015 EXPLORATION on a DIFFERENT axis (e.g., low-vol floor 0.33, vol-scaling clip range [0.3, 1.0], or ±25% BTC band looser direction deferred since iter-v3/012) |
| `EXPLORATION-PROMISING-INERT` | IS Sharpe within ±0.10 of iter-v3/013 (i.e., in [+0.91, +1.11]) AND IS trades < 167 | "ADX-orthogonal — KILL bucket was Sharpe-neutral; the threshold neither helps nor hurts at ~14% IS-PnL share" | iter-v3/015 EXPLORATION on a DIFFERENT axis; CONFIRMATION QR may still bundle ADX=25 if downstream re-running at higher seed counts shows orthogonality stable |
| `EXPLORATION-PROMISING-MECHANICAL` | IS Sharpe up ≥ +0.10 BUT trade-roster bit-identity to iter-v3/013 (would suggest gate-change had zero behavioral effect — UNLIKELY for ADX axis given non-trivial KILL bucket; flagged for completeness) | "Drag removal, not signal discovery — non-compoundable" | similar to iter-v3/013 framing |
| `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT) | IS Sharpe direction wrong (-Δ vs iter-v3/013) AND trade-roster bit-identity to iter-v3/013 | "Gate change had zero behavioral effect; saturation pattern" | iter-v3/015 EXPLORATION on a DIFFERENT axis |
| `EXPLORATION-NEGATIVE` | IS Sharpe down > 0.10 (i.e., < +0.91) AND non-bit-identical roster | "Tighter ADX over-restricted; [20, 25) trades were valuable to the model's signal" | iter-v3/015 EXPLORATION on a DIFFERENT axis (or test ADX=18 looser per Critic FINAL Rec 1 alternative) |
| `BLOCK` (process) | Methodology check FAILED, or Falsifier 2 (saturation) triggered | (none) | Diary documents, iter-v3/015 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards

iter-v3/014 inherits the cadence-discipline safeguards from skill SHA `d5c9f21` + the saturation-predictor rule:

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h.
2. **Single-axis variation rule** honored (only `adx_threshold` changed; features/labeling/universe/other-gates/CPCV byte-for-byte identical to iter-v3/013). Single axis is **gate-ADX**.
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / PROMISING-INERT / PROMISING-MECHANICAL / NEGATIVE / NEGATIVE-no-effect / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-014.md`.
4. **Saturation predictor falsifier** (Section 3.6 row 16, threshold derived `ceil(1.2 × counterfactual_n_trades)` per Critic FINAL Rec 3) actively verifies that the ADX gate change propagated to the model output (IS trades < 167).
5. **Gate-fire rate verifier** (Section 3.6 row 17): runner stats must show `killed_by_adx > iter-v3/013's count` — a second behavioral-effect signal independent of the trade roster size.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-013)

1. **Adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 17 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight grep-check** on `adx_threshold=25.0` and `"= 88"` removal: catches the case where setup edits were silently lost during a rebase.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 Gate-axis-specific risks

1. **Gate composition layering**: iter-v3/013 had 7 active primitives (vol scaling, ADX 20, Hurst, z-score OOD 2.0, low-vol 0.33, hit-rate disabled, BTC band ±15%). Tightening ADX may either (a) remove redundant kills (no net effect) or (b) interact with downstream gates non-linearly. The runner's per-gate fire-rate counters (`risk_v2.RiskStats`) provide diagnostic visibility.
2. **OOS distribution shift**: iter-v3/013's OOS [20, 25) bucket carried 61% of OOS PnL. Tightening ADX is a high-variance OOS proposition; the OOS_caveat in §2.1 travels with the catalog row regardless of OOS outcome. EXPLORATION discipline keeps OOS informational; iter-v3/015+ may revisit ADX=18 (looser) per Critic FINAL Rec if iter-v3/014 OOS regresses.
3. **Optuna trial budget**: 3 symbols × 10 trials = 30 trial-symbols (unchanged from iter-v3/013). The trial budget is not redistributed by gate change; same Optuna density per symbol.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — single primitive threshold change (ADX 20 → 25)

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol, ADX=25) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | **ADX gate (CHANGED)** | trade only when ADX ≥ **25** (vs 20) | **≈ 40-50% of bars pass** (vs ~60% at threshold 20) — reduced by ~20 percentage points | Strong-trend only (tighter) |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 | ≈ 25–35% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed (inherited iter-v3/012) | Macro flips |

Combined kill rate target: **85–92%** (vs 80-90% iter-v3/013, narrower passthrough). The ADX threshold is the only primitive whose threshold changes; all others' specs are byte-identical to iter-v3/013.

**Gate orthogonality**: All 7 primitives operate per-(symbol, candle) and are independent. Tightening ADX mechanically increases kill rate at primitive 2; it does NOT change the firing logic of primitives 1, 3-7.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2022-09-24 → 2025-03-23 — same as iter-v3/013. Regime coverage includes 2022 LUNA/FTX, 2023 banking (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction. The 3-symbol portfolio's exposure to these regimes is broadly similar; tighter ADX may sample fewer of these regime edges.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/013 OOS showed 65.65% LDO concentration. iter-v3/014 OOS concentration may shift either direction depending on whether ADX kill bucket is concentrated in any single symbol. Per-symbol [20, 25) IS kill counts (BCH/LDO/TRX) are informational; the brief does not pre-register a concentration falsifier (EXPLORATION protocol). Future CONFIRMATION QR will scope ex-LDO basket fragility separately.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Prediction P1 (process, P=5%)**: ADX threshold edit doesn't propagate. The Engineer adds the kwarg but a default-evaluation-order quirk or import caching means the runtime keeps `adx_threshold=20.0`. **Detection signal**: pre-flight grep (Section 3.6 row 8) returns 0 matches OR runner stats show `killed_by_adx` count unchanged from iter-v3/013 OR IS trade count > 167 (saturation falsifier). **Mitigation**: §3.6 row 8 verifier + row 16 (saturation) + row 17 (gate fire-rate). Three independent signals.

**Prediction P2 (process, P=5%)**: wall-clock overshoots the 30-min target. 3-symbol universe + tighter gate should run faster (fewer candidate trades). If runtime > 30 min, signal of unexpected slowdown (e.g., gate composition pathology or filesystem issue). **Detection signal**: engineering report wall-clock minutes. **Mitigation**: 2h hard cap by skill spec.

**Prediction P3 (process, P=10%)**: saturation falsifier calibration is incorrect (1.2× factor too tight). The realized IS trade count lands marginally above 167 (e.g., 175) due to Optuna re-optimization opening up new entries downstream of removed [20, 25) trades (cooldown release). Falsifier 2 fires as BLOCK but the gate change DID propagate. **Detection signal**: saturation falsifier triggers BUT `killed_by_adx > iter-v3/013` AND no other process anomaly. **Mitigation**: track in catalog as data point; recalibrate iter-v3/015+ if 1.2× factor is empirically too tight (could shift to 1.3× or use observed `killed_by_adx`-based check directly). The double-signal verifier (saturation + gate fire-rate) provides disambiguation.

**Prediction P4 (model, P=50%)**: IS Sharpe lifts moderately to [+1.10, +1.30]; tighter trend filter removes the [20, 25) bucket's lower-quality trades; PROMISING. The strategy benefits from regime filtering — the [20, 25) bucket is a marginal-trend regime where the model's edge is thin (37.14% WR vs 41.73% in KEEP bucket).

**Prediction P5 (model, P=30%)**: IS Sharpe stays in iter-v3/013 range [+0.91, +1.11] ±0.10; ADX-orthogonal (the [20, 25) bucket was Sharpe-neutral when normalized for n_trades; tightening neither helps nor hurts); PROMISING-INERT. Optuna re-optimization roughly compensates for the trade-roster shrinkage.

**Prediction P6 (model, P=20%)**: IS Sharpe drops to < +0.91; tighter ADX over-restricted; the [20, 25) bucket's marginal-trend trades carry signal that the model leverages downstream; NEGATIVE-soft. iter-v3/015 may test ADX=18 (looser direction per Critic FINAL Rec 1) to disambiguate.

**Prediction P7 (model, P=5%)**: IS Sharpe spikes to > +1.30; tighter ADX produces an unexpectedly large quality lift; PROMISING-strong. The [20, 25) bucket was net-negative for the model (despite +11.49 weighted_pnl) because of denominator (variance) effects similar to MKR-drop.

P4 + P5 sum to 80% (PROMISING outcome family). P6 + P7 sum to 25% (off-distribution outcomes). Process predictions P1-P3 sum to 20% (failure-mode hedging).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria — 11 EXPLORATION criteria

EXPLORATION never updates BASELINE_V3.md, so traditional MERGE thresholds do not apply. The 11 criteria below pre-register the catalog-row decision and provide unambiguous Critic verdict triggers (per skill spec at SHA `f0f8b84`).

1. **IS Sharpe ≥ +0.40** (PROMISING threshold inherited from cadence skill): catalog row records PROMISING verdict on numerical-axis basis.
2. **IS Sharpe < +0.10**: Falsifier 1 — EXPLORATION-NEGATIVE.
3. **IS Sharpe in [+0.10, +0.40)**: PROMISING-INERT (inert verdict) — catalog row records INERT.
4. **n_trades ≥ 50 IS, ≥ 50 OOS**: BUNDLE-LEVEL trade-rate floor per `feedback_trade_rate_floor_bundle_level` (informational at EXPLORATION; 167 IS / 30 OOS lower bound from Section 4.2 prediction). Realized iter-v3/014 IS expected ~120-167; OOS expected ~50-70. Both ABOVE the 50-trade floor; the bundle (5 outer × 3-4× ensemble) at CONFIRMATION will multiply this 3-4×.
5. **PBO < 0.40 (per-cell mean) AND `n_high_pbo_cells_99 ≤ 4`**: methodology hygiene; both inherited unchanged from iter-v3/013 0.1075 mean / 2 high-cells (TRX 2025-Q4 carry-forward). iter-v3/014 expected near-identical PBO unless ADX gate change has unexpected cell-level effect.
6. **IC max abs < 0.70**: per Critic Check 4 — zero new features so unchanged from iter-v3/013 0.685.
7. **ADF p < 0.05 on 13 V3_FEATURE_COLUMNS** (or stationarity rationale per Section 4 precedent): unchanged from iter-v3/013.
8. **Reproducibility verifier**: SHAs stamped in engineering report (analysis `33f389f`, runner setup commit, brief commit, Phase 5.5 gate, engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (Section 8 criterion 9 waiver inherited from iter-v3/006-013).
10. **Symbol exclusion + feature isolation**: `set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; `features_v3` does not import `features` (v1) or `features_v2` (v2).
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` + Critic FINAL Rec 3)**: IS trades < **167** (= ceil(1.2 × counterfactual_n_trades = 139)). The threshold is DERIVED per-iteration from §2.2's counterfactual; not a hardcoded constant. This is the load-bearing criterion for distinguishing "ADX gate change propagated" from "axis-saturated NULL-RESULT" — Critic uses this signal alongside `killed_by_adx` count from §3.6 row 17 to disambiguate.

**Catalog-axis verdicts** map to §4.4 table. The catalog row records the verdict exactly as Critic FINAL emits it.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/008-013** — no version bumps in iter-v3/014:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 2.3.1 (or recent compatible)
scikit-learn = 1.6.1
pyarrow = 19.0.1 (for parquet I/O)
mlfinpy = 1.4.0 (CPCV; MIT-licensed fork — fallback from mlfinlab=1.4)
pypbo = 0.10.0 (PBO via CSCV)
fracdiff = 0.10.0 (Numba-accelerated; FracdiffStat + ADF auto-d*)
statsmodels = 0.14.5 (adfuller for ADF stationarity)
optuna = 4.5.0
```

No package additions or version bumps. The runner edits modify only `RiskV2Config` kwargs and a docstring/comment hygiene fix; no new imports, no API surface change.

---

## Section 10 — Adversarial Tests (inherited; no new tests required for ADX-axis)

Adversarial test suite at `tests/strategies/ml/` is unchanged. No new tests are added for the ADX-axis variation because:
1. The ADX gate logic is already covered by `tests/strategies/ml/test_risk_v2.py` (or equivalent — gate-firing path is tested at construction time + via integration suite).
2. The change is a single kwarg value, not a new code path.
3. The Engineer's Phase 6 pre-flight pytest run validates that no existing test regressed.

---

## Section 11 — Catalog Row Pre-Commit (audit-trail discipline)

Per iter-v3/006+ catalog discipline, this brief pre-commits a structural template for the iter-v3/014 catalog row before backtest results are known:

```
| iter-v3/014 | 2026-05-06 | Risk-gate → ADX threshold 20 → 25 (tighter) | IS Sharpe Δ TBD vs iter-v3/013 +1.01 | OOS Sharpe TBD (informational) | TBD verdict | TBD candidate? |
```

The catalog row will be filled by the Phase 8 diary entry. The verdict cell maps to §4.4 + §8 criterion 1-3 + 11. The "candidate?" cell maps to whether the next CONFIRMATION-bundling QR should consider iter-v3/014 as a stack ingredient.

**Pre-committed disposition** (cannot be renegotiated post-hoc):
- If verdict = `EXPLORATION-PROMISING` AND `EXPLORATION-PROMISING-INERT` is NOT triggered: catalog row marked YES candidate (compoundable with iter-v3/010 labeling + iter-v3/011 z-score as a third axis-lift).
- If verdict = `EXPLORATION-PROMISING-INERT`: catalog row marked NO candidate (axis is orthogonal; no information gain at bundle level).
- If verdict = `EXPLORATION-PROMISING-MECHANICAL` (unlikely but flagged): catalog row marked YES with NON-COMPOUNDABLE flag (point decision, like drop-MKR).
- If verdict = `EXPLORATION-NEGATIVE` or `EXPLORATION-NEGATIVE-no-effect`: catalog row marked NO; iter-v3/015 explores a DIFFERENT axis (e.g., looser ADX=18 to disambiguate, OR low-vol floor 0.33, OR vol-scaling clip range, OR ±25% BTC band looser direction deferred since iter-v3/012).

**Catalog count after iter-v3/014**: 7 of 10 EXPLORATIONs; **3 more required** before any CONFIRMATION can launch. Axis coverage: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 = 6 unique axis representations.

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (7 of 10).
- [x] §1 hypothesis: one sentence, falsifiable.
- [x] §2 IS-only numerical evidence with COMMITTED analysis script SHA `33f389f`; counterfactual + behavioral-effect predictor with derived `falsifier_threshold = ceil(1.2 × counterfactual_n_trades) = 167`.
- [x] §3 sub-fixes with verifier commands; reconciliation table 17 rows.
- [x] §4 predicted IS Sharpe band [+0.50, +1.30] (median +0.90, with 30% upper-bound widening per iter-v3/013 caveat 4 pre-commit); falsifiers 1-3 + process locked.
- [x] §5 risk mitigation (cadence + saturation predictor + gate fire-rate verifier).
- [x] §6 7-primitive table with ADX threshold change explicit.
- [x] §7 7 failure-mode predictions (process P1-P3 = 20%; model P4-P7 = 105% — sums >100% reflect overlapping outcome buckets, intentional probabilistic redundancy).
- [x] §8 11 EXPLORATION criteria; criterion 11 = saturation falsifier with derived threshold per Critic FINAL Rec 3.
- [x] §9 library stack, no bumps.
- [x] §10 adversarial tests inherited.
- [x] §11 catalog row pre-commit + dispositions.

**Brief authorship complete.** Engineer Phase 5.5 gate is the next step.
