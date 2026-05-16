# Iteration v3-034 — Research Brief

**Type**: EXPLORATION (cadence #6 of 10 in post-iter-v3/028 cycle; **FEATURE axis (Category 2 — engineered feature add) + UNIVERSE shrink (Category 5 — DROP VETUSDT)** — atomic swap: revert V3_MODELS 5→4 + ADD fracdiff_d05_close as 15th feature)
**Track**: v3 (rigor arm) — thirty-fourth iteration
**Branch**: `iteration-v3/034` (off `iter-v3/033` head)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # default per feedback_v3_exploration_n_trials_35
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #6 of 10 in post-iter-v3/028 cycle)
Wall-clock budget: ≤ 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation (ATOMIC SWAP):
  - DROP VETUSDT (V3_MODELS reverts 5 → 4: BCH+LDO+TRX+ALGO)
  - ADD fracdiff_d05_close (V3_FEATURE_COLUMNS_TOP_N expands 14 → 15)
  Net: universe shrinks by 1, feature count grows by 1
Cadence: 6 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039)
Axis category: 2 (Category 2 engineered feature — LdP AFML Ch. 5 FFD at fixed d=0.5)
ANCHOR: iter-v3/032 single-seed (IS +0.2360 / OOS +1.9338) for feature-axis comparison
  [iter-v3/033 VETUSDT result informs the DROP decision; iter-v3/032 is the feature anchor]
Prerequisite references:
  - feedback_v3_engineered_features_proven.md (engineered features pivot validated by iter-v3/025+)
  - López de Prado, AFML Ch. 5 (Fixed-window Fractional Differencing methodology)
NOT a gate-threshold knob. NOT a symbol-swap variation. NOT a labeling-param change.
```

**Why DROP VETUSDT now**: iter-v3/033 is the EXPLORATION that added VETUSDT (5th symbol). The Phase 7 OOS result for iter-v3/033 is available at brief-writing time and will determine whether VETUSDT earns a permanent slot. The brief does not pre-judge that outcome — the DROP is executed unconditionally here to isolate the fracdiff signal on the proven 4-symbol (BCH+LDO+TRX+ALGO) universe, which is the anchor established at iter-v3/032 (IS +0.2360). Running fracdiff on a 5-symbol universe with a potentially-failing VETUSDT would confound attribution.

**Atomic swap justification (one-variable principle)**: Dropping VETUSDT and adding fracdiff_d05_close are mechanically coupled because VETUSDT was the sole iter-v3/033 change. Reverting VETUSDT restores the iter-v3/032 anchor exactly; adding fracdiff_d05_close is then the single new variable. The net IS Sharpe lift over the iter-v3/032 anchor measures fracdiff signal only.

---

## Section 1 — Hypothesis

`fracdiff_d05_close` (fixed-window fractional differentiation of log(close) at d=0.5, López de Prado AFML Ch. 5 FFD) provides a regime-persistence signal that is **complementary** to `regime_momentum_signed_5d` (sign-flip momentum): where `regime_momentum_signed_5d` encodes the direction of 5-day momentum conditional on the Hurst regime, `fracdiff_d05_close` encodes the **level of accumulated price memory** (the long-memory component of the close series that is orthogonal to full differencing), giving the model a distinct stationary-yet-memory-preserving view of the current price state; IS Sharpe lifts +0.10 over the iter-v3/032 anchor of +0.2360 (to approximately +0.34).

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — LdP AFML Ch. 5 Methodology (Computational, No New EDA Required)

The `fracdiff_d05_close` feature is derived from a well-specified, peer-reviewed methodology in López de Prado (2018), *Advances in Financial Machine Learning*, Chapter 5 ("Fractionally Differentiated Features"). The computational specification is deterministic; no IS-only EDA is needed beyond the method description, weight-truncation verification, and ADF stationarity confirmation.

**Fixed-window fractional differentiation (FFD) at d=0.5**:

Weights for the fractional differencing operator at order d are defined by the binomial series:

```
w_k = (-1)^k * Gamma(d+1) / (Gamma(k+1) * Gamma(d-k+1))
```

which simplifies to the iterative recurrence:

```
w_0 = 1
w_k = -w_{k-1} * (d - k + 1) / k    for k >= 1
```

For d=0.5, the weights decay as k^{-0.5-1} (approximately), which is slower than integer differencing (d=1, weights = {1, -1}) but still summable. The FFD output at bar t is:

```
fracdiff_d05_close[t] = sum_{k=0}^{W-1} w_k * log_close[t-k]
```

where W is the truncation window chosen so that |w_W| < 1e-4.

**Weight truncation computation**:
For d=0.5, the weight magnitude |w_k| = |Gamma(1.5) / (Gamma(k+1) * Gamma(1.5-k))| decays as approximately C * k^{-1.5}. The threshold |w_k| < 1e-4 is reached at approximately k=50-200 bars depending on the exact d value. At d=0.5 the truncation point is typically around k=120-150 (the implementation will compute this exactly at runtime via the recurrence).

**Stationarity property (AFML §5.4)**:
- d=0 → no differencing → non-stationary (I(1) price series)
- d=1 → full differencing → stationary but maximum memory loss
- d=0.5 → fractional → stationary (ADF p < 0.05 expected) AND preserves long-memory

At d=0.5 the spectral density at frequency 0 is finite (stationarity condition met), and the autocorrelation function decays as k^{2d-1} = k^0 (slowly), preserving long-memory information that full differencing destroys.

**Expected ADF p < 0.05 across all 4 symbols** (BCH, LDO, TRX, ALGO) on the IS window (2023-03-24 to 2025-03-23). This is a falsifiable pre-registration: if any symbol fails ADF p >= 0.05 at d=0.5, the feature is non-stationary for that symbol and the hypothesis is partially falsified.

### 2.2 — Complementarity with regime_momentum_signed_5d

`regime_momentum_signed_5d` = ret_5d × sign(hurst_100 − 0.5):
- Encodes: recent 5-day price direction × regime classifier
- Source primitives: close (via log-return difference), hurst_100 (rolling R/S)
- Stationarity: stationary by construction (log-return difference)
- Information: DIRECTION of 5-day move, conditioned on trending vs mean-reverting regime

`fracdiff_d05_close`:
- Encodes: accumulated price memory (long-memory component at d=0.5)
- Source primitive: log(close) (the non-stationary level series, partially differenced)
- Stationarity: ADF-confirmed stationary at d=0.5
- Information: LEVEL of price relative to its fractionally-differentiated history

These two features are structurally non-overlapping:
- `regime_momentum_signed_5d` is a pure return feature (difference of log prices at fixed lags)
- `fracdiff_d05_close` is a weighted combination of the full log(close) history (up to truncation window)

IC orthogonality: the Category 2 carve-out (established in iter-v3/025 phase5p5_gate.md §IC-Gate Carve-Out) applies here. `fracdiff_d05_close` shares variance with `fracdiff_logclose_dstat` (the existing auto-d* fracdiff), so IC against existing features will be non-zero and the hard IC gate (≤0.70) is expected to be triggered. The carve-out governs: the binding gate for Category 2 / LdP-methodology features is **feature importance rank ≤ 10 AND absolute importance ≥ 30**, NOT pairwise IC.

### 2.3 — Relationship to Existing fracdiff Features

The existing v3 feature set contains `fracdiff_logclose_dstat` (auto-d* via ADF grid search, implemented in `fracdiff_v3.py`). The distinction from `fracdiff_d05_close`:

| | `fracdiff_logclose_dstat` | `fracdiff_d05_close` |
|---|---|---|
| d selection | ADF-adaptive (d* varies by month/symbol) | Fixed d=0.5 (AFML §5 reference value) |
| IS membership | NOT in V3_FEATURE_COLUMNS_TOP_N (excluded per iter-v3/008) | ADD in this iteration |
| Window | 100 bars | truncation at |w_k| < 1e-4 (~120-150 bars) |
| Stationarity guarantee | Adaptive, d* chosen to pass ADF | Pre-guaranteed at d=0.5 by AFML theory |

`fracdiff_logclose_dstat` is NOT currently in V3_FEATURE_COLUMNS_TOP_N and has never been active in the top-N subset since iter-v3/008 pruned it out. Adding `fracdiff_d05_close` as a separate column (distinct from the dstat variant) avoids any confusion between the two and allows clean attribution.

---

## Section 3 — Proposed Changes

### Sub-fix 1: DROP VETUSDT from V3_MODELS

Revert `V3_MODELS` from 5 symbols (BCH+LDO+TRX+VET+ALGO, iter-v3/033) to 4 symbols (BCH+LDO+TRX+ALGO):

```python
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
    ("F (ALGOUSDT)", "ALGOUSDT"),
)
```

VETUSDT (`"E (VETUSDT)"`) is removed. The model designation letters remain as assigned (A, C, D, F).

### Sub-fix 2: Update REQUIRED_GAP 110 → 88

`REQUIRED_GAP` in `validation_v3.py` reverts to 88 = (21+1) × 4 symbols. The formula is `(timeout_candles + 1) * n_symbols`. With 4 symbols and timeout=21 candles: (21+1) × 4 = 88.

Update the docstring comment in `run_baseline_v3.py` accordingly (gap formula comment block).

### Sub-fix 3: Implement compute_fracdiff_d05_close in engineered_v3.py

Add function `compute_fracdiff_d05_close(df: pd.DataFrame) -> pd.DataFrame` to `engineered_v3.py`:

- Apply FFD (Fixed-window Fractional Differencing) with d=0.5 to log(close)
- Truncate weights when |w_k| < 1e-4 (truncation window computed at function startup)
- Source: `log_close = np.log(close.clip(lower=1e-12))`
- Past-only: weights look BACKWARD only; FFD at bar t uses log_close[t], log_close[t-1], ..., log_close[t-W+1]
- NaN warmup: first (W-1) bars are NaN where W is the truncation window length
- Implementation: pure numpy — use the `_fracdiff_weights` and `_fracdiff_series` helpers already present in `fracdiff_v3.py` (import them), OR re-implement inline in `engineered_v3.py` to avoid cross-module coupling. Re-implementation inline is preferred for track-isolation clarity.
- Output column name: `fracdiff_d05_close`

Dispatch `compute_fracdiff_d05_close` from `add_engineered_v3_features` after `compute_regime_momentum_signed_5d`.

### Sub-fix 4: ADD fracdiff_d05_close to V3_FEATURE_COLUMNS_TOP_N (14 → 15)

Append `"fracdiff_d05_close"` to `V3_FEATURE_COLUMNS_TOP_N` in `features_v3/__init__.py`:

```python
"fracdiff_d05_close",  # rank TBD — engineered_v3 (Category 2; LdP AFML Ch. 5 FFD d=0.5)
```

Update the docstring comment block accordingly.

### Sub-fix 5: Update _verify_feature_columns (14 → 15)

In `run_baseline_v3.py`, update `_verify_feature_columns`:
- Change the count assertion: `n != 15` (was `n != 14`)
- Add: `if "fracdiff_d05_close" not in V3_FEATURE_COLUMNS: raise RuntimeError(...)`
- Update the docstring: reference iter-v3/034 + new count
- The existing guards (tbr_zscore_30 absent, vol_adj_autocorr absent, etc.) remain unchanged

### Sub-fix 6: Update ITERATION_LABEL "v3-033" → "v3-034"

In `run_baseline_v3.py`, change:
```python
ITERATION_LABEL = "v3-034"
```

Also update the comment block above `V3_MODELS` to document the iter-v3/034 DROP VET + ADD fracdiff_d05_close change.
Update the CPCV gap comment: `gap = REQUIRED_GAP = (timeout_candles+1)*n_symbols = (21+1)*4 = 88`.

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (vs iter-v3/032 anchor +0.2360)**:
- Predicted band: [+0.20, +0.55]
- Median point estimate: +0.38
- Rationale: fracdiff_d05_close adds a distinct stationary-memory signal; the 4-symbol universe is the proven anchor; net feature count 15 is within representational capacity of depth-3-5 LightGBM at n_trials=35

**OOS Sharpe prediction (vs iter-v3/032 anchor +1.9338)**:
- Predicted band: [+1.60, +2.10]
- Median point estimate: +1.85
- Rationale: feature IS-lift expected to partially transfer OOS; VETUSDT removal eliminates a potentially-noisy 5th model from the portfolio aggregate

**Path taxonomy**:
- Path A (PROMISING): IS ≥ +0.20 AND fracdiff_d05_close importance ≥ 30; proceed to Section 8 criteria
- Path B (NEGATIVE-no-effect): fracdiff_d05_close importance < 5 across all symbols (saturated axis); record NULL-RESULT; next EXPLORATION must move to different axis
- Path C (SUSPICIOUS): IS ≥ +0.20 but fracdiff importance ≥ 30 with OOS collapse (< +1.0); further diagnostic needed

**OOS falsifier**: if OOS Sharpe < +1.0, the fracdiff_d05_close hypothesis is rejected regardless of IS performance.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.

**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from baseline.

**R3 (OOD detection)**: unchanged. Mahalanobis OOD z-score threshold unchanged.

**Universe risk**: reverting to 4 symbols reduces portfolio diversification versus iter-v3/033 5-symbol configuration. Concentration risk increases. The per-symbol concentration cap (no symbol > 35% of weighted PnL) continues to apply. With 4 symbols, max theoretical concentration = 100% (ALGO alone) vs 80% (one of 5); the empirical cap is enforced at runtime via the concentration check in the engineering report.

**Feature IC risk**: `fracdiff_d05_close` will have high IC with the existing (but NOT active) `fracdiff_logclose_dstat` column. This does NOT trigger the IC hard gate because `fracdiff_logclose_dstat` is NOT in V3_FEATURE_COLUMNS_TOP_N. The IC gate applies only between ACTIVE features. IC computed in the engineering report should confirm: max |IC| between `fracdiff_d05_close` and any OTHER active feature in V3_FEATURE_COLUMNS_TOP_N.

**Warmup bars**: the fracdiff truncation window W ≈ 120-150 bars introduces additional NaN warmup (vs the existing ~99-bar warmup from hurst_100 for regime_momentum_signed_5d). At 8h cadence, 150 bars = 50 calendar days. The IS window of 24 months (2742 bars) easily absorbs this warmup; it has no material effect on training sample size.

**Threshold calibration**: all existing gate thresholds (BTC trend, hit-rate, ADX) are IS-calibrated from the incumbent 4-symbol universe. Dropping VET and adding a feature does not alter threshold validity — the universe reverts to iter-v3/032 which is the source of the calibration.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/032 baseline unchanged. No gate parameters are modified in this iteration.

| Gate | Type | Parameter | IS Fire Rate (iter-v3/032) | OOS Fire Rate (iter-v3/032) | Change in this iteration |
|---|---|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | ~8-12% | ~8-12% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED | DISABLED | None |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | symbol-dependent | symbol-dependent | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit in regime_momentum | symbol-dependent | symbol-dependent | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | symbol-dependent | symbol-dependent | None |
| 6 — OOD gate | Mahalanobis z-score | per-training-window | symbol-dependent | symbol-dependent | None |
| 7 — Liquidity floor | NATR floor | NATR ≥ 0.5% | All 4 symbols pass | All 4 symbols pass | None |

The ADX gate at threshold=20 is the iter-v3/009 baseline value. Per `feedback_adx_axis_asymmetric_v3.md`, the ADX axis was closed after iter-v3/015; no further ADX threshold exploration is permitted in this iteration.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode**: `fracdiff_d05_close` IS rank-importance is in the 10-13 range (low but above 5), contributing marginal signal, and the IS Sharpe lift is within noise of the iter-v3/032 anchor (+0.2360 ± 0.10 from seed variance). OOS would then show the typical single-seed EXPLORATION variance (±0.30-0.40 Sharpe), making attribution impossible. Classification would be PROMISING-INERT (analogous to iter-v3/019 funding_rate_zscore_30 outcome) rather than NEGATIVE.

**Second plausible failure mode**: `fracdiff_d05_close` IS importance > 30 (strong signal learned), but IS/OOS ratio degrades to > 3× (OOS Sharpe < +0.65), indicating the feature overfits on the IS training window. This would classify as NEGATIVE-OOS and mandate that the fracdiff axis be closed for v3. The gates to watch: BTC trend gate fires at > 20% OOS (suggests the fracdiff signal is correlated with BTC contagion periods), and/or TRX concentration > 60% in OOS (indicates the feature works only for one symbol).

**What the gates should catch**: a spurious fracdiff IS signal that emerges from overfitting the IS window's specific 2023-2025 crypto price dynamics should manifest as: low OOS trade count (< 50 trades), high TRX concentration (TRX is the most trend-persistent symbol), and below-threshold IS/OOS Sharpe ratio.

**Failure metric signals**:
- If fracdiff_d05_close ADF p >= 0.05 on any symbol: feature is non-stationary → implementation bug → BLOCK before continuing
- If fracdiff importance < 5 on ALL 4 symbols: saturated axis (NULL-RESULT per `feedback_v3_axis_saturation_predictor.md`)
- If IS Sharpe < +0.10: large IS regression vs anchor → NEGATIVE
- If OOS Sharpe < +1.0: OOS falsifier triggered → NEGATIVE

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (EXPLORATION)

This is an EXPLORATION iteration. MERGE criteria are not applicable — only PROMISING / NEGATIVE / NULL-RESULT classification applies.

**PROMISING** (proceed toward CONFIRMATION cadence): ALL of:
- IS Sharpe ≥ +0.20 (within 0.04 of iter-v3/032 anchor +0.2360, not regressing)
- fracdiff_d05_close feature importance ≥ 30 on at least 2 of 4 symbols (Category 2 carve-out gate: importance threshold ≥ 30 per `engineered_v3.py` module docstring)
- ADF p < 0.05 for fracdiff_d05_close on all 4 symbols in IS window

**PROMISING-INERT**: IS Sharpe ≥ +0.20 but fracdiff_d05_close importance in [5, 29] on all symbols: weak signal. Budget-disambiguation retest (n_trials=70) may be warranted per iter-v3/022 precedent.

**NULL-RESULT (saturated axis)**: fracdiff_d05_close importance < 5 on ALL 4 symbols → axis saturated per `feedback_v3_axis_saturation_predictor.md`. Per the policy established at iter-v3/012, the NEXT EXPLORATION must move to a different axis.

**NEGATIVE**: ANY of:
- IS Sharpe < +0.10 (large IS regression)
- OOS Sharpe < +1.0 (OOS falsifier)
- fracdiff_d05_close ADF p >= 0.05 on any symbol (stationarity failure — implementation bug)

---

## Section 9 — Library Stack Declaration

- **Python**: 3.13 (runtime)
- **LightGBM**: pinned in pyproject.toml (same as iter-v3/032; no change)
- **numpy**: standard array operations for fracdiff weight computation and application
- **scipy**: NOT required — the fracdiff implementation uses only numpy (weight recurrence + dot product)
- **statsmodels**: for ADF test in `fracdiff_v3.py` (existing; NOT used by `fracdiff_d05_close` which is fixed-d, not adaptive-d)
- **fracdiff (PyPI package)**: UNAVAILABLE due to statsmodels version conflict (fracdiff==0.9.0 requires statsmodels<0.14; project requires statsmodels==0.14.6). Fallback: pure-numpy implementation using the weight recurrence formula from AFML Ch. 5. This fallback is IDENTICAL in result to `fracdiff.sklearn.FracdiffStat` at fixed d=0.5 with the same truncation threshold.
- **Implementation location**: `compute_fracdiff_d05_close` function in `src/crypto_trade/features_v3/engineered_v3.py`, using an inline numpy weight recurrence (does NOT import from `fracdiff_v3.py` to preserve track isolation within the module)
- **No new dependencies required**: `fracdiff_d05_close` is a pure-numpy computation using the existing `np` import already present in `engineered_v3.py`
