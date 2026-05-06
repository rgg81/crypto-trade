# Iteration v3-012 — Research Brief

**Type**: EXPLORATION (FIFTH EXPLORATION under the cadence discipline)
**Track**: v3 (rigor arm) — twelfth iteration
**Branch**: `iteration-v3/012` (off `iteration-v3/011` head; analysis commit `aadeb72` ships before this brief)
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

**Sacred constants UNCHANGED.** The `--exploration` flag (SHA `bce50c8`) does NOT touch `OOS_CUTOFF_DATE` or `training_months`. The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007/009/010/011 briefs / engineering reports / Critic / diaries; iter-v3/012 analysis script `analysis/iteration_v3-012/btc_trend_band_demo.py` outputs (committed at SHA `aadeb72` BEFORE this brief). The analysis script reads `data/BTCUSDT/8h.csv` which is public price data over the entire span — no IS/OOS split discipline at risk (no model trades read or computed).

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Wall-clock budget: < 30 min (2h hard cap)
Single-axis variation: BTC trend filter band (±20% → ±15%, stricter)
Cadence: EXPLORATION #5 of 10 needed
This iteration NEVER updates BASELINE_V3.md.
```

**Justification**: Per cadence discipline (skill SHA `d5c9f21`), CONFIRMATION cannot launch with fewer than 10 EXPLORATION rows since the last CONFIRMATION. The catalog at `briefs-v3/exploration_catalog.md` has 4 rows (iter-v3/007 PROMISING, iter-v3/009 NEGATIVE, iter-v3/010 PROMISING, iter-v3/011 PROMISING-w-caveats); iter-v3/012 is the fifth. Per Critic FINAL Recommendation 1 on iter-v3/011 review (SHA `b9ebbb2`), iter-v3/012 must vary along the BTC-TREND-FILTER axis to maximize catalog axis diversity (currently features×2, labeling×1, gate-zscore×1, gate-btc-trend×0). After iter-v3/012: features×2, labeling×1, gate-zscore×1, gate-btc-trend×1 — substantially diverse for the eventual CONFIRMATION bundle.

**Direction (stricter not looser)**: ±15% is selected over ±25% because the v3 strategy's IS sample carries the 2024-Q4 post-election BTC rally regime (BTC +48%/30d) where iter-v3/011's BTC filter at ±20% caught only the most extreme moves; ±15% stress-tests whether tightening this band — kills more alt trades during BTC moves between 15-20% — improves or degrades signal under the iter-v3/011 PROMISING z=2.0 stack. iter-v3/013 may test ±25% (looser direction) if needed for monotonicity verification.

---

## Section 1 — Hypothesis

Tightening BTC trend filter band from ±20% to ±15% over 14 days (kills more alt trades when BTC moves materially) on top of iter-v3/011's z=2.0 + iter-v3/010's ATR 2.0/1.0 + iter-v3/009's 13-feature stack will produce IS Sharpe maintained or improved (≥+0.40, vs iter-v3/011's +0.96) by filtering more aggressively against BTC-driven regime shifts; tests whether the prior PROMISING settings depend on the BTC band's relative permissiveness.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-012/btc_trend_band_demo.py` (committed at SHA `aadeb72` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (BTC public data, no IS/OOS contamination since BTC kline data is public over the entire span and no model trades are read or computed):
- `data/BTCUSDT/8h.csv` — BTC 8h klines, 6,953 rows, used for 14-day rolling absolute returns.

**Outputs** (committed alongside the script at SHA `aadeb72`):
- `analysis/iteration_v3-012/btc_band_kill_rate.csv` — full BTC 14d return distribution stats + per-band kill fractions, per-window-split (FULL / IS-only / OOS-only).
- `analysis/iteration_v3-012/synthesis.md` — 1-paragraph narrative.

### 2.1 BTC 14-day rolling absolute-return distribution

| Window | n_candles | median |14d| | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|
| FULL | 6,911 | 6.29% | 27.34% | 39.45% | 70.09% |
| IS (2022-09-24 → 2025-03-23) | 5,685 | 6.71% | 29.13% | 40.93% | 70.09% |
| OOS (2025-03-24 onwards) | 1,226 | 4.60% | 15.15% | 22.25% | 29.77% |

Note: `n_candles` here is the analysis-side count after the 42-bar warmup is dropped (raw CSV has ~6,953 8h candles). The OOS window is calmer than IS — p95 dropped from 29% to 15% — consistent with the 2024-Q4 post-election rally being IS-only and 2025+ being a more range-bound regime.

### 2.2 Per-band gross fire rate

The BTC trend filter fires when `|BTC 14d return| > threshold_pct` AND the alt's signal direction OPPOSES BTC's direction (`risk_v2.py:761-849`). The "gross fire rate" below counts candles where `|BTC 14d return| > threshold` regardless of signal direction — this is an UPPER BOUND on actual alt-trade kills since at any single bar only one of {long, short} is fightable; the realized kill rate at the trade level is roughly half the gross.

| Window | ±20% gross fire | ±15% gross fire | Δ (pp) |
|---|---:|---:|---:|
| FULL | 10.95% | 18.54% | +7.58pp |
| IS | 12.88% | 21.41% | +8.54pp |
| OOS | 2.04% | 5.22% | +3.18pp |

### 2.3 Expected realized kill-rate shift on iter-v3/011 IS trade base

iter-v3/011 reported empirical BTC-filter killed ~7-8% combined IS trades at ±20%. Per the linear scale-up:

| Quantity | Baseline (±20%) | Perturbation (±15%) | Δ |
|---|---:|---:|---:|
| Gross fire rate (FULL) | 10.95% | 18.54% | ratio 1.69× |
| Realized kill rate (IS estimate) | ~7.5% | **~12.7%** (linear) | +5.2pp |
| Realized kill rate (OOS estimate) | ~1.5% | **~3.8%** (linear) | +2.3pp |

The IS-OOS kill-rate ASYMMETRY (8.54pp gross delta IS vs 3.18pp OOS) is informational: the band tightening will affect IS trade-economics MORE than OOS, since IS contains the 2024-Q4 BTC rally whereas OOS post-March-2025 is calmer. This is a structural property of the data, not an iteration-specific artifact.

### 2.4 Setup integrity (verified at SHA `aadeb72`)

```
data/BTCUSDT/8h.csv extant + non-empty                 PASS (6953 rows)
n_candles after 42-bar warmup (FULL)                   = 6911    PASS
n_candles IS-only                                       = 5685    PASS
n_candles OOS-only                                      = 1226    PASS
btc_band_kill_rate.csv produced                         PASS
synthesis.md produced                                   PASS
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (full v3 universe)

| Symbol | Status | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Full v3 universe (iter-v3/007/009/010/011 baseline). |
| MKRUSDT | KEEP | Same. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED (inherits iter-v3/010 ATR(2.0/1.0))

| Parameter | iter-v3/011 (current) | iter-v3/012 (this iteration) |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | **2.0 (UNCHANGED)** |
| `atr_sl_multiplier` | 1.0 | **1.0 (UNCHANGED)** |
| Timeout | 21 candles (7d, 10080 min) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 88 (= (21+1)×4) | UNCHANGED |

### 3.3 Features — UNCHANGED (13 features, inherited from iter-v3/009)

```python
V3_FEATURE_COLUMNS = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)  # length = 13, vwap_dev_50 dropped (inherited from iter-v3/008/009/010/011)
```

NO feature changes. `_verify_feature_columns()` will continue to assert `len == 13` and `'vwap_dev_50' not in V3_FEATURE_COLUMNS`.

### 3.4 Risk gates — z-score gate UNCHANGED at iter-v3/011's z=2.0; BTC trend band CHANGED

| Parameter | iter-v3/011 (current) | iter-v3/012 (this iteration) |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | **2.0 (UNCHANGED, inherits iter-v3/011)** |
| `BTC_TREND_CONFIG.threshold_pct` | **20.0** | **15.0 (CHANGED)** |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| ADX threshold | 20 | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

The only change is `BTC_TREND_CONFIG.threshold_pct` 20.0 → 15.0 in `run_baseline_v3.py` line 121. The 7-primitive risk table structure preserved; only one knob tuned.

### 3.5 Sub-fix decomposition (single-axis: BTC trend filter band)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Update `BTC_TREND_CONFIG.threshold_pct` 20.0 → 15.0** in `run_baseline_v3.py` (line 121) | `threshold_pct=15.0` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 2 | **Update `ITERATION_LABEL` to `"v3-012"`** in `run_baseline_v3.py` (line 99) | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-012"' run_baseline_v3.py` exits 0 |
| 3 | **Optional cosmetic**: parametrize `_verify_feature_columns()` docstring like iter-v3/010 did so docstring/banner stale references don't recur (P3 mitigation) | Use `ITERATION_LABEL` in docstring | Engineer discretion |
| 4 | **Commit the runner with these changes** | `feat(iter-v3/012): BTC trend filter band 20.0→15.0 + ITERATION_LABEL=v3-012` | `git log --oneline iteration-v3/012 -- run_baseline_v3.py | head -1` shows the iter-v3/012 SHA |
| 5 | **Run `--exploration --seeds 1 --n-trials 10`** on full 4-symbol universe | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10` (no `--symbols` flag → all 4 V3_MODELS). Wall-clock target: < 30 min (hard cap 2h per cadence rule). | `test -f reports-v3/iteration_v3-012/comparison.csv` |

NO new src/ code changes (only `run_baseline_v3.py` line edits). NO test additions. NO labeling/universe/features/z-score-gate change.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | V3_FEATURE_COLUMNS unchanged at 13 features (inherited) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13, f'len={len(V3_FEATURE_COLUMNS)}'"` exits 0 |
| 2 | `atr_tp_multiplier=2.0` UNCHANGED (inherited from iter-v3/010) | `run_baseline_v3.py` line 862 | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 3 | `atr_sl_multiplier=1.0` UNCHANGED (inherited from iter-v3/010) | `run_baseline_v3.py` line 863 | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 4 | `zscore_threshold=2.0` UNCHANGED (inherited from iter-v3/011) | `run_baseline_v3.py` line 873 | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 5 | `BTC_TREND_CONFIG.threshold_pct=15.0` CHANGED (was 20.0 in iter-v3/011) | `run_baseline_v3.py` line 121 | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 6 | `ITERATION_LABEL` updated to `"v3-012"` | `run_baseline_v3.py` line 99 | `grep -E 'ITERATION_LABEL.*=.*"v3-012"' run_baseline_v3.py` exits 0 |
| 7 | Sub-fix #5 produces comparison.csv | runner | `test -f reports-v3/iteration_v3-012/comparison.csv` |
| 8 | **EXPLORATION sanity test**: IS monthly Sharpe != 0 (band change took effect) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-012/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert abs(float(ms)) > 1e-6, f'IS sharpe ~0 — band likely not taking effect: {ms}'"` exits 0 |
| 9 | All 35 adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 10 | Wall-clock ceiling: total Phase 6 runtime < 30 min target / 2h hard cap | engineering report | wall-clock minutes < 120 |
| 11 | Full v3 universe used (4 symbols, no --symbols filter) | runner invocation log | `grep -E "Active models: 4/4" reports-v3/iteration_v3-012/run.log` exits 0 |
| 12 | **Falsifier 2 monotonicity check**: IS trade count <= iter-v3/011 baseline (286) | comparison.csv | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-012/comparison.csv'); n = df.loc[df['metric']=='n_trades','in_sample'].iloc[0]; assert int(n) <= 286, f'IS trades > 286 — band did not tighten kill: {n}'"` exits 0 |

### 3.7 NO new feature additions, NO universe change, NO labeling change, NO z-score-gate change

iter-v3/012 is a single-axis (BTC-trend-filter-band) EXPLORATION. The feature set, model architecture, ATR labeling multipliers, z-score OOD gate threshold, CPCV parameters, and walk-forward window are byte-for-byte unchanged from iter-v3/011. The only differences vs iter-v3/011: `BTC_TREND_CONFIG.threshold_pct` (single-axis) + `ITERATION_LABEL` (cosmetic) + optional docstring parametrization.

### 3.8 Inheritance from iter-v3/011

The `iteration-v3/012` branch was branched from `iteration-v3/011` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0) + ITERATION_LABEL=v3-010 + docstring parametrization`
- `17d01ab feat(iter-v3/011): z-score OOD threshold perturbation analysis`
- iter-v3/011's `zscore_threshold=2.0` change (sub-fix from iter-v3/011's brief Section 3.4)
- `aadeb72 feat(iter-v3/012): BTC trend filter band perturbation analysis` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'threshold_pct=20\.0' run_baseline_v3.py` exits 0 BEFORE the iter-v3/012 sub-fix #1 lands (then must transition to `threshold_pct=15\.0`)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with 35/35 PASS

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK` (process). iter-v3/012 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/011 (z=2.0, ATR(2.0/1.0), BTC ±20%) | iter-v3/012 prediction (BTC ±15%) |
|---|---:|---:|
| IS monthly Sharpe | +0.9566 | **predicted [+0.40, +1.20] with median +0.65** |
| IS trades | 286 | **predicted ~243-271 (5-15% reduction)** |
| Phase 6 wall-clock | 8 min | predicted 7-10 min (marginally fewer trades), hard cap 2h |

The prediction band [+0.40, +1.20] is intentionally **broad** — BTC-band sensitivity is high-variance because the band shifts trade-mix toward less-BTC-correlated regimes (a structural change, not just a sample-size trim). Median +0.65 reflects the realistic +5-15% IS trade reduction (per Section 2.3) on top of iter-v3/011's broad-based +0.96; tightening might preserve most of the IS edge IF the v3 strategy's lift is primarily intra-symbol momentum rather than BTC-correlated regime trades. Median is BELOW iter-v3/011's +0.96 because tighter filtering uniformly trims SOME directional edge (per López de Prado AFML Ch. 2 on signal/noise tradeoffs in filter selection); not above, despite "maintained or improved" framing, because the baseline ±20% band is already calibrated for the rare-tail (5-10×/year) BTC moves and tightening to ±15% catches more frequent but less-extreme moves where the alt's directional signal may still carry useful information.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.10 → tighter BTC band killed signal beyond noise reduction. The (±15%) band over-filters; tightening over-corrects. Verdict: EXPLORATION-NEGATIVE on BTC-band-axis tight direction. Catalog this finding; iter-v3/013 may try ±25% (looser direction) to verify the relationship is monotonic in the OPPOSITE direction.

**Falsifier 2**: IS trade count > 286 (i.e., MORE trades despite tighter band) → bug. The BTC trend filter logic should be monotonic-decreasing in threshold (lower threshold = more kills = fewer trades). If trade count rises, something is wrong in the runtime wiring. Verdict: BLOCK (process); engineer documents.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on full v3 universe at exploration config → BTC-band-perturbation slowdown reproduces; engineer documents the cause; future EXPLORATION iterations re-scope.

**Process falsifier**: pre-flight `len(V3_FEATURE_COLUMNS) == 13` returns False OR grep for `threshold_pct=15.0` returns empty → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation

| Critic verdict | Meaning | Next iteration |
|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe ≥ +0.40 — tighter BTC band validates iter-v3/011 robustness | iter-v3/013 EXPLORATION on a DIFFERENT axis (e.g., ADX threshold, low-vol filter floor, vol-scaling clip) |
| `EXPLORATION-NEGATIVE-soft` | IS Sharpe in [+0.10, +0.40) — tighter band filters useful information; signal dilutes but stays positive | iter-v3/013 may test ±25% (looser direction) to confirm BTC-band-axis sensitivity |
| `EXPLORATION-NEGATIVE` | IS Sharpe < +0.10 (Falsifier 1) — tighter band over-filters | iter-v3/013 EXPLORATION on a DIFFERENT axis OR test ±25% (looser) |
| `BLOCK` (process) | Methodology check FAILED unexpectedly | Diary documents, iter-v3/013 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards

iter-v3/012 inherits THREE structural safeguards from the cadence skill:

1. **2h wall-clock hard cap** (skill SHA `d5c9f21`): Engineer kills Phase 6 if elapsed > 2h, regardless of progress. Prevents the iter-v3/008 abort pattern from recurring.
2. **Single-axis variation rule** honored (only `BTC_TREND_CONFIG.threshold_pct` changed; features/symbols/labeling/z-score-gate/other gates byte-for-byte identical to iter-v3/011).
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / NEGATIVE / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-012.md`.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-011)

1. **35 adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 12 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len + name check** on `V3_FEATURE_COLUMNS`: catches the case where inherited setup was silently lost during a rebase.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 NO new model-level risks introduced

The iter-v3/012 changes:
- ZERO new code (only one-line `BTC_TREND_CONFIG.threshold_pct` arg edit + ITERATION_LABEL).
- ZERO new features.
- ZERO new dropped features.
- ZERO labeling changes.
- ZERO z-score-gate changes.
- ZERO CPCV / walk-forward window changes.
- ZERO test changes.

The only model-level effect is the new BTC-trend-filter kill-rate distribution. Mitigated by:
- BTC public-data IS+OOS frequency baseline + projected reduction (§2.3) provides Falsifier-2 reference.
- Critic two-round flow surfaces any unexpected interaction.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — SAME 7 PRIMITIVES as iter-v3/006-011, only #7 threshold tuned

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 (iter-v3/011 inherited) | ≈ 25–35% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d **±15% (tightened from ±20%)** | **≈ 12–13% killed (vs 7–8% baseline)** | Macro flips — TIGHTER |

Combined kill rate target: **80–90%** (vs 75–88% at ±20%) — the tightening adds ~5pp to the combined kill rate via primitive #7.

**Gate orthogonality**: BTC trend filter fires at trade-entry time on the candle's BTC 14d return computed in `apply_btc_trend_filter` (`risk_v2.py:806-849`), INDEPENDENT of the LightGBM model's `V3_FEATURE_COLUMNS` (13 features) AND independent of the z-score OOD gate's `V2_FEATURE_COLUMNS` (34 features). Verifier: the threshold change at `BTC_TREND_CONFIG.threshold_pct` propagates to the post-hoc `apply_btc_trend_filter` call (`run_baseline_v3.py:1209-1215`) but does NOT affect the model's feature ingestion, labeling logic, or z-score-gate firing.

### 6.2 Regime coverage — UNCHANGED

Full v3 universe IS data spans 2022-09-24 → 2025-03-23. Regime coverage includes 2022 LUNA/FTX, 2023 banking (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC -25%/14d), 2025 January correction. The ±15% band catches the 2023-03 SVB rally and the 2024-08 yen-carry crash (which crossed ±20% only briefly), in addition to the 2024-Q4 rally that the baseline ±20% already caught.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/011 OOS showed 86% LDO concentration (lottery-flag). Concentration is NOT a gate for iter-v3/012 per TYPE=EXPLORATION; informational only. The BTC-band tightening may shift concentration in either direction (BTC moves correlate differently with each alt's signal direction); diary captures the actual shift.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Prediction P1 (process, P=5%)**: the `BTC_TREND_CONFIG.threshold_pct` change in `run_baseline_v3.py` line 121 doesn't propagate to the runtime `apply_btc_trend_filter` call (e.g., a stale config object is cached, or the Engineer accidentally edits a different `threshold_pct` reference). **Detection signal**: pre-flight check via grep + Phase 6 run.log BTC-filter stats showing IS kill counts identical to iter-v3/011 (impossible if threshold actually changed). **Mitigation**: pre-flight grep verifies `threshold_pct=15.0` (sub-fix #1 verifier); engineer reports observed BTC trend filter kill counts in engineering report.

**Prediction P2 (process, P=5%)**: wall-clock overshoots 30 min on full v3 universe at exploration config. iter-v3/011 ran in 8 min on the same config + same 4 symbols; tightening is expected to produce FEWER trades (5-15% reduction), which marginally DECREASES run time. **Detection signal**: total Phase 6 wall-clock > 30 min on full universe. **Mitigation**: 2h hard cap (cadence rule). Engineer kills if exceeded; iter-v3/013 EXPLORATION re-scopes.

**Prediction P3 (process, P=5%)**: docstring/banner stale references (recurring drift across iter-v3/008, iter-v3/009, iter-v3/010). **Detection signal**: grep for stale "iter-v3/011" or "z=2.5" / "z=2.0" or "BTC ±20%" strings in `run_baseline_v3.py` after sub-fix lands. **Mitigation**: parametrize docstring like iter-v3/010's `_verify_feature_columns` did (sub-fix #3 cosmetic option); Engineer's discretion.

**Prediction P4 (model, P=50%)**: IS Sharpe lands in [+0.50, +1.20] band (predicted band; tighter BTC band validates iter-v3/011 signal robustness). EXPLORATION-PROMISING. The strategy's edge survives the stricter BTC filter because the underlying signal is broad-based intra-symbol momentum rather than driven by trades during BTC moves between 15-20%. The realistic +5-15% trade reduction compresses sample size moderately while preserving most directional edge.

**Prediction P5 (model, P=30%)**: IS Sharpe lands in [+0.10, +0.50) band — tighter BTC band filters useful information; signal dilutes but stays positive. EXPLORATION-NEGATIVE-soft. The (±15%) band over-filters by removing trades where alt's directional signal carried information even during 15-20% BTC moves — iter-v3/011's edge was partly carried by these "BTC-correlated but still profitable" trades. Catalog this finding; iter-v3/013 may test looser direction (±25%).

**Prediction P6 (model, P=15%)**: IS Sharpe drops below +0.10 (Falsifier 1 activates). Tighter BTC band over-filters severely — the strategy's edge sat substantially on trades during BTC moves between 15-20% (e.g., banking-stress / yen-carry-rally regimes where alts' signals had specific edge). EXPLORATION-NEGATIVE. Catalog this finding; iter-v3/013 pivots back to a different axis (e.g., features-axis or labeling-axis).

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline
- 3 model-level (P4, P5, P6) covering predicted-band, soft-undershoot, hard-undershoot
- Per the iter-v3/010 calibration overshoot AND iter-v3/011 calibration overshoot (both labeling-axis and gate-axis priors had been too narrow): for BTC-band-axis here, priors are widened to reflect higher BTC-band-sensitivity variance: 50/30/15 (PROMISING / soft-NEGATIVE / hard-NEGATIVE) with broad PROMISING band ([+0.50, +1.20] vs iter-v3/011's [+0.40, +0.70]).

Summary: **EXPLORATION-PROMISING pathway probability ≈ 50%** (P4); EXPLORATION-NEGATIVE ≈ 45% (P5+P6); process abort ≈ 15% (P1+P2+P3 ≈ 15% but each individually triggers a remediation, not a verdict change).

If any prediction fails to materialize, the iter-v3/012 diary documents the calibration miss.

---

## Section 8 — Pre-Registered EXPLORATION Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/012 is an **EXPLORATION iteration** per Section 0.5. Headline-metric criteria from CONFIRMATION iterations (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0) are NOT in scope. Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, or `BLOCK`.

### EXPLORATION-PROMISING iff ALL 10 of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE | §0.5 |
| 2 | Single-axis variation only (BTC trend filter band) | TRUE | §3.7 |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | §3.6 row 10 |
| 4 | `--exploration --seeds 1 --n-trials 10` used | TRUE | §3.5 sub-fix #5 |
| 5 | 35/35 adversarial tests pass | TRUE | §3.6 row 9 |
| 6 | `BTC_TREND_CONFIG.threshold_pct=15.0` confirmed at runtime | TRUE | §3.6 row 5 |
| 7 | `comparison.csv` produced (basic headline metrics) | TRUE | §3.6 row 7 |
| 8 | Critic OVERALL = `EXPLORATION-PROMISING` (NOT NEGATIVE, NOT BLOCK) | enum | Phase 7.5 |
| 9 | NO 5-seed or CONFIRMATION-style runs | TRUE (vacuous; --seeds 1) | §3.7 |
| 10 | Catalog updated post-Phase-8 with iter-v3/012 row | TRUE | post-iteration mechanic |

### EXPLORATION-NEGATIVE iff:

- Criteria 1-7, 9, 10 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE` (because IS Sharpe < +0.40, falsifier 1 region, OR IS trades > 286 unexpectedly indicating monotonicity bug)

### BLOCK (process) iff ANY of:

- Criteria 1-7, 9 fail (process-level)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 2h hard cap
- IS trade count > 286 (Falsifier 2: monotonicity violation)

### Discretionary judgment — EXPLORATION pathway

iter-v3/012 has NO MERGE pathway because the iteration TYPE is EXPLORATION. The "MERGE pathway" is `EXPLORATION-PROMISING`, which is a forward-pointer: it adds one row to the catalog and counts toward the 10 EXPLORATION quota. **iter-v3/012 NEVER updates BASELINE_V3.md.**

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds`; column-array math | n/a |
| `scipy` | (already installed) | BSD-3 | (no use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | 35 adversarial tests | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O + analysis script CSV/BTC kline loading | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, fastparquet |

**No new external deps.** Same stack as iter-v3/007-011. The iteration's NEW code is:
- 1 analysis script + 2 outputs (committed at SHA `aadeb72`)
- 1 cosmetic `run_baseline_v3.py` line edit (Engineer ships in Phase 6): `BTC_TREND_CONFIG.threshold_pct`
- 1 cosmetic `run_baseline_v3.py` line edit (Engineer ships in Phase 6): `ITERATION_LABEL`
- Optional: docstring parametrization (sub-fix #3, P3 mitigation)
- 0 new pytest test files
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-012/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `aadeb72` analysis + the new sub-fix SHA)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The full 13-feature list as actually trained on (sanity check against §3.3)
- The runtime `BTC_TREND_CONFIG.threshold_pct` (sanity check against §3.5 sub-fix #1)
- Observed IS BTC trend filter kill counts (P1 detection signal): `n_killed/n_total` per seed from `run_baseline_v3.py:1217-1219` log output
- The `comparison.csv` IS / OOS monthly Sharpe values
- The total IS trade count (Falsifier 2 reference, must be ≤ 286)
- The wall-clock minutes total (must be < 120; target < 30)
- The 35-test outcome (PASS expected)
- The `--exploration` activation banner from `run.log`
- The runner invocation literal (proof of `--exploration --seeds 1 --n-trials 10`)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 11 mandatory sections plus the Phase 5.5 inputs:

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ENSEMBLE_SIZE=1 / colsample=1.0 / n_trials=10 SET BY --exploration |
| 0.5 — Iteration Type Declaration | PASS — TYPE: EXPLORATION declared; cadence catalog reference; explicit "NEVER updates BASELINE_V3.md"; BTC-trend-band axis chosen per Critic FINAL Rec 1 of iter-v3/011 |
| 1 — Hypothesis | PASS — one sentence; testable target IS Sharpe ≥ +0.40 (Falsifier 1 at +0.10); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-012/btc_trend_band_demo.py` committed at SHA `aadeb72` BEFORE this brief; per-window-split fire-rate stats + linear-extrapolation kill-rate projection |
| 3 — Proposed Changes | PASS — symbols UNCHANGED; labeling UNCHANGED; features UNCHANGED; z-score-gate UNCHANGED; BTC trend band CHANGED (single-axis); sub-fix decomposition with reconciliation table 12 verifiers; inheritance plan §3.8 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [+0.40, +1.20]; 4 falsifiers in §4.3; EXPLORATION pathway in §4.4 |
| 5 — Risk Mitigation | PASS — 3 cadence-discipline structural safeguards in §5.1 + 4 methodology-pipeline safeguards in §5.2 |
| 6 — Risk Management Design | PASS — 7-primitive table with primitive #7 threshold tightened; gate orthogonality verified |
| 7 — Pre-Registered Failure-Mode | PASS — 6 predictions with **3 process-level (P1, P2, P3)**; calibrated PROMISING prior at ~50% (reflecting iter-v3/010 + iter-v3/011 overshoot lessons + BTC-band-axis variance) |
| 8 — Pre-Registered EXPLORATION Criteria | PASS — 10 EXPLORATION criteria; EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / BLOCK pathways; explicit "NEVER updates BASELINE_V3.md" |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/006-011 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8.
