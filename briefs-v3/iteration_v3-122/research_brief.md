# iter-v3/122 Research Brief — Cycle-7 EXPLORATION #1 (FIRST EXPLORATION post-/121 BASELINE update)

**Axis**: NEW cross-asset feature family using ETH OHLCV (`data/ETHUSDT/8h.csv`). Adds **one** ETH-derived primitive to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15): `A4 = eth_ret_3d = log(close_eth[t]/close_eth[t−9])` — ETH's 3-day log return. The candidate is a SIMPLE PRIMITIVE (NOT a composed feature, NOT a regime classifier), in the same OHLCV-cross-asset family as the existing baseline `btc_ret_14d` and `sym_vs_btc_ret_7d` features. Selected via committed EDA per `feedback_v3_axis_selection_quant_discipline.md`.

**Lineage discipline**: ETH OHLCV is OUT-OF-SCOPE of the BASELINE_V3.md "7-FEED structural verdict" (which addressed non-OHLCV crypto-native sentiment-metadata feeds: funding /019/023/024/082/085, microstructure /015, basis /086 — all derivatives-metadata). ETH klines are OHLCV; ETH is a price source structurally identical to the existing BTC OHLCV source already in baseline. See `analysis/iteration_v3-122/_shared.py` docstring + `synthesis.md` for the full lineage adjudication.

**Cycle**: 7 EXPLORATION slot **#1 of 10**. Cycle-7 catalog state at /121 closeout: 0 EXPLORATIONs run yet (cycle 7 starts fresh). The /121 CONFIRMATION-MERGE updated BASELINE_V3.md /059 → /121 yesterday (2026-05-20) — the first BASELINE update in 7 days; /116 no_confirm RULE-layer primitive is now load-bearing in the canonical baseline. /122 = first cycle-7 EXPLORATION to test against the new /121 anchor.

**Anchor (EXPLORATION-mode comparison)**: iter-v3/121 multi-seed CONFIRMATION-MERGE BASELINE_V3.md numbers (IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682**) — the NEW canonical anchor per `BASELINE_V3.md`. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode 3-seed results compress relative to CONFIRMATION-mode 10-seed. A clean EXPLORATION-MODE-REFERENCE re-anchor (the cycle-2 /077, cycle-3 /084 pattern) would require running /121-config at 3-seed mode with no axis — this is NOT what /122 does. /122 runs the +A4 single-axis at 3-seed EXPLORATION mode and compares the headline Δ to /121 multi-seed baseline directly, with the explicit understanding (per Section 4.3 below) that an EXPLORATION-mode 3-seed run will compress IS by ~−0.25 vs the 10-seed CONFIRMATION baseline through architecture-effect alone (the /077 vs /059 IS gap was ~−0.27 attributed to 3-seed-vs-10-seed proba-averaging). The /122 brief explicitly accounts for this compression in the Section 4 prediction bands.

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. The sacred constants are immutable across all three tracks; no /122 modification touches them.

- **IS window**: data extent start (per-symbol earliest 8h candle close ≥ 2020-01-01) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent (~2026-05-20).
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **Reporting layer**: `comparison.csv` and `in_sample/` / `out_of_sample/` directories split on `OOS_CUTOFF_DATE` exactly.
- **Bar interval**: 8h (cycle-6 candle-frequency axis broadly CLOSED per /117 closeout; cycle-7 stays at 8h).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

The /122 axis introduces **NO tuned scalar parameter** — every primitive is INHERITED from the natural log-return geometry at a standard lookback (3 calendar days = 9 8h bars).

| Parameter | Value | Provenance |
|---|---|---|
| `eth_ret_3d` lookback | **9 8h bars (= 3 calendar days)** | INHERITED from the natural 3-day log-return convention used by `cross_btc_v3.py:_load_btc_v3_features` for the existing `btc_ret_3d` primitive (which was in the /063 mass-expansion set, REMOVED at /064 for COLLATERAL mass-expansion reasons — not feature-specific falsification). NOT tuned for /122. Source: `analysis/iteration_v3-122/_shared.py:_load_eth_klines`. |
| ETH source CSV | **`data/ETHUSDT/8h.csv`** | INHERITED data infrastructure; ETH klines are pre-fetched by `crypto-trade fetch` (the same fetcher used for BCH/LDO/TRX/BTC). 6990 rows back to 2020-01-01, identical extent to BTC. |
| Merge convention | **left-join on `open_time`** | INHERITED from `cross_btc_v3.py:add_cross_btc_v3_features` pattern. NOT tuned for /122. |
| Sign convention | **none — A4 is a signed primitive** (positive ETH 3d return → A4 > 0) | Inherent to log-return; NOT a tunable scalar. |

**ZERO tuned scalars in /122.** Every numeric design choice is either inherited from the existing v3 cross-asset feature pattern or structurally fixed by the algebraic form. This is parity with /119's provenance posture (which also declared zero tuned scalars).

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-122/`, commit `b875272`) was committed in ONE atomic commit BEFORE this brief. Every script in the EDA directory asserts `close_time < OOS_CUTOFF_MS = 1742774400000`; no OOS-window file is read at any point. Verified at EDA: 0 OOS-leaked rows across all 3 symbols (BCH 5606/0, LDO 2620/0, TRX 5548/0).

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: NEW cross-asset feature in `V3_FEATURE_COLUMNS_TOP_N`, 14 → 15)
- **Cycle 7 slot**: **#1 of 10**. iter-v3/131 is the projected final EXPLORATION (cycle-7 ends with iter-v3/132 CONFIRMATION per the strict 10:1 cadence; `feedback_v3_strict_10_to_1_cadence.md`).
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35` (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per `feedback_v3_outer_seed_cap_2_v3.md`; first 3 seeds of the unified 10-seed lineage)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md` — above TPE warmup ~30; the v3 EXPLORATION default since iter-v3/019)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`; the 8h baseline EXPLORATION runtime envelope is well under cap — recent EXPLORATIONs: /118 0.72h, /117 0.64h, /119 1.1h)
- **Single axis variation**: ONE new feature added to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15: append `eth_ret_3d`). All other knobs (universe, label, gates, ensemble seeds, Optuna search space, /116 no_confirm primitive) are bit-identical to the /121 baseline (the new canonical state).

---

## Section 1 — Hypothesis

> Adding **`eth_ret_3d`** (ETH's 3-day log return) as the 15th feature in `V3_FEATURE_COLUMNS_TOP_N` carries incremental directional signal beyond the /121 14-feature stack on the BCH/LDO/TRX 8h cohort, lifting EXPLORATION-mode IS monthly Sharpe by Δ ∈ [+0.05, +0.20] vs the architecturally-adjusted /121 EXPLORATION-mode reference (estimated IS +1.06 — see Section 4.3) and OOS monthly Sharpe by Δ ∈ [+0.00, +0.15] vs /121 OOS +0.9682; OR the OHLCV-cross-asset hypothesis (that ETH-cross-asset signals are structurally distinct from the 7-FEED non-OHLCV closure scope and can carry incremental signal to v3) is FALSIFIED at production by an EXPLORATION-NEGATIVE result, closing one of the four /119 diary §8.2 candidate menu items and informing cycle-7's axis-selection priors.

---

## Section 2 — IS-Only Numerical Evidence

EDA (`analysis/iteration_v3-122/`, commit `b875272`): 4 ETH-derived candidates evaluated via the /119 / /118 5-step methodology (T1 catalog, T2 linear redundancy, T3 POOLED univariate, T4 per-symbol univariate, T5 multivariate importance, T7 multivariate lift, T9 SSC-RISK gate, T6 GO/NO-GO, T8 ADF stationarity).

### Section 2.1 — T1 catalog (4 candidates)

See `T1_candidate_catalog.csv`:

| ID | Formula | R² (T2) | T3 POOLED AUC | T5 BCH/LDO/TRX importance rank | T7 POOLED lift | T9 SSC ratio |
|---|---|---:|---:|---|---:|---:|
| A1 | `eth_ret_14d` | **0.70** | 0.494 | 15/12/8 | +0.0069 | 0.90× |
| A2 | `eth_vs_btc_ret_21d` | 0.11 | 0.518 | 15/2/3 | **−0.006** | 8.81× |
| A3 | `eth_vs_btc_vol_diff_14d` | 0.33 | 0.473 | 15/4/7 | +0.0007 | **28.13×** |
| **A4** | `eth_ret_3d` | 0.44 | 0.508 | 15/11/10 | +0.0012 | 3.63× |

### Section 2.2 — T2 Linear Redundancy Pre-Falsifier

A1 fails the strict R²<0.70 gate (R²=0.7017 with top correlation 0.82 vs `btc_ret_14d` — algebraic near-clone of an existing baseline feature). Per `feedback_v3_lr_pf_methodology.md`, ETH features are NOT composed features so the carve-out does NOT apply; A1 is REJECT-R2.

A2 (0.11), A3 (0.33), A4 (0.44) all PASS the R² gate — distinct information content from the 14-feature anchor.

### Section 2.3 — T3 POOLED + T4 per-symbol univariate

A2 is the strongest univariate (POOLED AUC 0.518 above null q95 0.506, p=0.00). A4 just clears q95 (AUC 0.508 vs q95 0.507, p=0.03). A1 (0.494) and A3 (0.473) below null.

Per-symbol AUC reveals the structural asymmetry:
- A2: BCH 0.469 / **LDO 0.574** / **TRX 0.560** (2 g1 passes; strong on alts)
- A4: BCH 0.463 / LDO 0.530 / TRX 0.538 (2 g1 passes; weaker uniform)
- A1: BCH 0.467 / LDO 0.440 / TRX 0.555 (1 g1 pass)
- A3: BCH 0.477 / LDO 0.407 / TRX 0.494 (0 g1 passes)

**BCH univariate AUC is below 0.50 for ALL 4 candidates**. BCH is a BTC-fork; its price is tightly coupled to BTC's, so ETH-vs-BTC information is structurally irrelevant for BCH directional prediction. This per-symbol asymmetry — ETH features work on ALT symbols (LDO/TRX) but not on BCH — is the controlling diagnostic that drives the SSC-RISK gate.

### Section 2.4 — T5 multivariate importance

A4's per-symbol importance: BCH rank 15/15 (gain 3.0%), LDO rank 11/15 (gain 4.0%), TRX rank 10/15 (gain 4.3%). **BCH rank 15/15 is the /015 / /082 / /085 / /086 INERT signature** at importance-allocation level. LDO + TRX mid-table (10-11/15) with mid-tier gain.

A2 has the strongest importance allocation (LDO rank 2/15 + TRX rank 3/15) but the multivariate POOLED lift is NEGATIVE (−0.006) — Optuna at depth 3-5 cannot simultaneously load A2 productively on LDO + TRX while absorbing the BCH cost.

### Section 2.5 — T7 multivariate-LIFT screen (controlling test)

| Candidate | POOLED lift | BCH lift | LDO lift | TRX lift |
|---|---:|---:|---:|---:|
| A1 | +0.0069 | −0.0005 | −0.0044 | −0.0062 |
| A4 | **+0.0012** | +0.0001 | −0.0034 | −0.0044 |
| A3 | +0.0007 | −0.0091 | +0.0203 | −0.0071 |
| A2 | −0.0060 | +0.0106 | +0.0530 | −0.0055 |

A4 is the only T2-passing candidate with non-negative POOLED lift (+0.0012). The /118 + /119 production-relevance threshold (POOLED lift > +0.003) is NOT met by A4 (+0.0012 is below threshold).

### Section 2.6 — T9 SSC-RISK gate

Only A1 (REJECT-R2 disqualified) clears the SSC-RISK gate. A4's SSC ratio 3.63× exceeds the 2× threshold (TRX +0.0044 vs POOLED +0.0012 = 3.63×) — TRX is the carrier. The /118 catastrophic NEGATIVE was caused by single-symbol-carrier asymmetry; A4's SSC carrier is TRX, which is a smaller-share symbol at /059's 95.76% BCH concentration so the production blast radius may be smaller than /118's BCH carrier.

**T9 SSC-RISK A4 = TRUE (3.63×)** — pre-registers Section 4 band-tightening per `feedback_v3_promising_feature_mechanical.md` SSC-RISK gate convention.

### Section 2.7 — T6 verdict synthesis

| Candidate | Verdict | Notes |
|---|---|---|
| **A4_eth_ret_3d** | **MARGINAL** | Least-bad T2-passing candidate; weak POOLED lift, BCH rank 15/15 INERT signature, SSC TRUE 3.63× |
| A3 | WEAK | Fails univariate; SSC 28× |
| A1 | REJECT-R2 | Algebraic clone of btc_ret_14d (R²=0.70) |
| A2 | REJECT | NEGATIVE POOLED lift (−0.006); SSC 8.81× |

**Selection: /122 = A4 (eth_ret_3d) with MARGINAL EDA signal.** The brief models the modal outcome as **NEGATIVE-no-effect or NEGATIVE-INERT** per the BCH rank 15/15 + thin POOLED lift signature.

### Section 2.8 — ADF stationarity (T8)

12/12 cells PASS p<0.05. A4 specifically: BCH adf_stat=−11.84, p=0.0; LDO adf_stat=−7.51, p=0.0; TRX adf_stat=−11.59, p=0.0. Stationary by construction (log-returns).

---

## Section 3 — Proposed Changes (single-axis vs /121 baseline)

### Change 1 — `src/crypto_trade/features_v3/cross_btc_v3.py`

Extend the existing BTC cross-asset module to also load ETH klines and expose ETH-derived features.

Current state (BTC only):
```python
def add_cross_btc_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Merge BTC-derived features into the symbol's feature frame."""
    ...
```

Proposed delta — add ETH klines loader + new feature `eth_ret_3d`:

```python
ETH_CSV_PATH = Path("data/ETHUSDT/8h.csv")

_ETH_CACHE_V3: pd.DataFrame | None = None


def _load_eth_v3_features() -> pd.DataFrame:
    """Load ETH 8h klines and precompute ETH-derived columns (cached)."""
    global _ETH_CACHE_V3
    if _ETH_CACHE_V3 is not None:
        return _ETH_CACHE_V3
    df = pd.read_csv(ETH_CSV_PATH).sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)
    log_close = np.log(close)
    df["eth_ret_3d"] = np.concatenate([np.full(9, np.nan), log_close[9:] - log_close[:-9]])
    _ETH_CACHE_V3 = df[["open_time", "eth_ret_3d"]].copy()
    return _ETH_CACHE_V3


# Inside add_cross_btc_v3_features, after the BTC merge:
eth = _load_eth_v3_features()
out = out.merge(eth, on="open_time", how="left")
```

### Change 2 — `src/crypto_trade/features_v3/__init__.py`

Append `"eth_ret_3d"` to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15):

```python
V3_FEATURE_COLUMNS_TOP_N: tuple[str, ...] = (
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
    "regime_momentum_signed_5d",
    "eth_ret_3d",  # iter-v3/122 — NEW cycle-7 EXPLORATION axis-1 (ETH cross-asset; A4 EDA top)
)
```

Update the comment header to record the /122 EXPLORATION + the ABSENT-list does NOT add `eth_ret_3d` (this iteration ADDS the feature; only REVERTED features go on the ABSENT list).

### Change 3 — `run_baseline_v3.py`

Update `ITERATION_LABEL` and the pre-flight assertion:
- Line ~131: `ITERATION_LABEL = "v3-122"` (was `"v3-121"`)
- Line ~2983-2996 pre-flight: invert `"eth_ret_3d" not in V3_FEATURE_COLUMNS_TOP_N` → `"eth_ret_3d" in V3_FEATURE_COLUMNS_TOP_N`; assert `len(V3_FEATURE_COLUMNS_TOP_N) == 15` (was 14).
- ITERATION_LABEL propagates to `reports-v3/iteration_v3-122/`.

### Change 4 — Parquet regeneration

The parquet generation pipeline (`crypto-trade features`) must be re-run for BCH/LDO/TRX (and BTC, ETH for cache priming) to materialize the `eth_ret_3d` column. Engineer runs:

```bash
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 8h --track v3 --format parquet --workers 4
```

The parquet for BCH/LDO/TRX must contain `eth_ret_3d` as a column (non-NaN on the last 100 IS rows). Engineer Phase 6 pre-flight asserts this.

### Change 5 — Unit test

Add a test in `tests/test_features_v3/` verifying `eth_ret_3d` is past-only on a synthetic ETH panel:

```python
def test_eth_ret_3d_past_only():
    # Build an ETH panel with bar 1000 + extended bar 1500 with extreme future values
    # Compute eth_ret_3d, then change bars [1010+] to extreme values
    # Recompute and check eth_ret_3d[1000] == original eth_ret_3d[1000]
```

Faithful to the /119 past-only invariant test pattern.

### Change 6 — Integration test

Add a test in `tests/test_run_baseline_v3.py` asserting:
- `V3_FEATURE_COLUMNS_TOP_N` includes `"eth_ret_3d"` (the 15th feature)
- `len(V3_FEATURE_COLUMNS_TOP_N) == 15`
- The parquet for BCHUSDT/LDOUSDT/TRXUSDT has the `eth_ret_3d` column non-NaN on the LAST 100 IS rows
- Runner pre-flight n_features guard fires `n == 15`
- The feature value is consistent with the EDA's stand-alone computation (compare 10 random IS rows)

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

| File | Change |
|---|---|
| `src/crypto_trade/features_v3/cross_btc_v3.py` | Add `_load_eth_v3_features()` + extend `add_cross_btc_v3_features` to merge ETH columns |
| `src/crypto_trade/features_v3/__init__.py` | Append `"eth_ret_3d"` to `V3_FEATURE_COLUMNS_TOP_N`; comment update with /122 history note |
| `run_baseline_v3.py` | Lines ~131 (ITERATION_LABEL), ~2983-2996 (pre-flight inversion) |
| `tests/test_features_v3/test_cross_btc_v3.py` (or new test file) | Add `test_eth_ret_3d_past_only` |
| `tests/test_run_baseline_v3.py` (or equivalent) | Add `test_eth_ret_3d_integration` |

**Files NOT touched** (negative scope):
- `src/crypto_trade/strategies/ml/lgbm.py` (no labeling change, no risk gate change)
- `src/crypto_trade/strategies/ml/labeling.py` (no label change)
- `src/crypto_trade/strategies/ml/walk_forward.py` (no walk-forward change)
- `src/crypto_trade/strategies/risk_v2.py` (gates unchanged)
- `src/crypto_trade/backtest.py` (no new exit primitive)
- `src/crypto_trade/features_v3/engineered_v3.py` (no engineered-feature change)
- All other `features_v3/*.py` modules
- `OOS_CUTOFF_DATE`, `training_months` — sacred constants, immutable
- /116 no_confirm primitive — STAYS ENABLED in baseline per user directive 2026-05-20

---

## Section 4 — Expected OOS Impact (predicted bands) — SSC-RISK-aware

### Section 4.1 — Anchor-architecture adjustment (load-bearing for cycle-7)

**The architecture-gap finding (per BASELINE_V3.md "EXPLORATION-vs-CONFIRMATION architecture-gap" + `feedback_v3_dsr_mode_artifact.md`)**: /121 baseline IS +1.3108 / OOS +0.9682 is a 10-seed CONFIRMATION-mode number. /122 runs at EXPLORATION 3-seed mode. The /077 vs /059 IS gap was ~−0.27 attributed entirely to the 3-seed-vs-10-seed proba-averaging architecture component.

**Cycle-7 architecturally-adjusted EXPLORATION-mode reference for /122 axis-Δ classification**:

| Anchor | Mode | IS Sharpe | OOS Sharpe | Use |
|---|---|---:|---:|---|
| /121 CONFIRMATION (canonical) | 10-seed | +1.3108 | +0.9682 | For CONFIRMATION-mode forward-looking gates only |
| **/121 EXPLORATION-mode estimate (architecturally adjusted)** | 3-seed estimate | **+1.06** | **+0.85** | **For /122 EXPLORATION-mode Δ classification** |

The adjustment factor: IS −0.25 (10-seed → 3-seed proba-averaging effect, from cycle-2 /077 vs /059 anchor-staleness work), OOS −0.12 (smaller; OOS path is less seed-sensitive at v3's trade volume).

**Methodology caveat**: this is an ESTIMATE; the true cycle-7 EXPLORATION-MODE-REFERENCE will be measured at a future iteration (the analogue of /077, /084). /122 must report results vs BOTH the /121 multi-seed baseline (the public anchor) AND the /121-architecturally-adjusted EXPLORATION estimate (the falsifier band).

### Section 4.2 — Predicted bands

| Arm | Modal predicted Δ vs /121 EXPLORATION-mode estimate (IS +1.06 / OOS +0.85) | Lower (failure mode) | Upper |
|---|---:|---:|---:|
| IS monthly Sharpe Δ | −0.10 to +0.10 | −0.30 (catastrophic) | +0.30 |
| OOS monthly Sharpe Δ | −0.15 to +0.10 | −0.50 (Mode 4) | +0.35 |

**Modal prediction band (EXPLORATION-mode reference):** IS Sharpe ∈ [+0.96, +1.16]; OOS Sharpe ∈ [+0.70, +0.95].

**Modal prediction band (against published /121 CONFIRMATION baseline):** IS Sharpe ∈ [+1.20, +1.40]; OOS Sharpe ∈ [+0.85, +1.05] (these are sensitive to architecture compression and used INFORMATIONALLY).

### Section 4.3 — SSC-RISK-aware band-tightening

A4's T9 SSC ratio 3.63× (TRUE flag, TRX carrier) triggers the /119-established band-tightening convention per `feedback_v3_promising_feature_mechanical.md` SSC-RISK rules: tighten upper bound IS Δ ≤ +0.10, OOS Δ ≤ +0.10 (the modal expected lift is smaller given the single-symbol carrier risk). C5/A2 would have triggered larger tightening (SSC ratios 28× and 8.8×); A4's 3.63× is closer to the 2× gate threshold and the carrier is TRX (smaller IS share than BCH) so the absolute blast radius is smaller — but the qualitative pattern matches the /118 lineage.

**Pre-registered F1 falsifier (binding)**: if production OOS monthly Sharpe Δ vs /121 multi-seed baseline falls below **−0.30** AND IS monthly Sharpe Δ vs /121 multi-seed baseline falls below **−0.40** (i.e., crossing into Sharpe < +0.90 OOS or Sharpe < +0.91 IS — material drift from the new baseline), the OHLCV-cross-asset hypothesis is FALSIFIED for the eth_ret_3d primitive; file EXPLORATION-NEGATIVE catastrophic.

**Pre-registered F2 falsifier (binding)**: if production importance rank for `eth_ret_3d` falls to ≥ 14/15 on > 1 of 3 symbols AT THE FINAL IS MONTH, AND POOLED lift not materially > 0 (estimated via test-month directional accuracy diff), file EXPLORATION-PROMISING-INERT or EXPLORATION-NEGATIVE-INERT. This is the /082 / /085 / /086 INERT-by-importance signature; the brief explicitly pre-registers this as the EDA modal failure mode.

**Pre-registered F3 falsifier (binding)**: if production OOS Sharpe Δ vs /121 multi-seed > +0.15 BUT IS Sharpe Δ < +0.00, file SUSPICIOUS-OOS-DOMINANT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. The /082 / /085 / /086 INERT-with-OOS-spike artifact pattern.

**Pre-registered F4 falsifier (binding)**: if production TRX-only IS PnL Δ > +5pp AND BCH IS PnL Δ < −1pp AND LDO IS PnL Δ < +1pp (the SSC-RISK realized as TRX-carrier asymmetry per the T9 prediction), file Mode 3 PROMISING-PARTIAL per the SSC-prediction precedent.

**Trade-rate prediction**: total IS trades expected ≈ /121 baseline count (173 IS) ± 10% (the new feature changes the Optuna loss surface slightly but does not change entry/exit gates). OOS trades expected ≈ /121 baseline count (98 OOS) ± 15%. If OOS trade count falls by > 30% vs /121, file Mode 4 RESIDUAL (the new feature is causing OOD-rejection rate to spike, an unexpected side-effect of the 15th column).

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): the new feature changes Optuna's loss surface, so the IS trade roster will differ from /121 — expected fraction of common IS trades vs /121 baseline roster: 70–90% (a fresh feature changes ~10–30% of the model's threshold-crossing decisions; lower variance than /118 / /119 because A4 is INERT-by-importance prediction → fewer decision changes expected than for a high-importance feature). If common-trade fraction > 95%, the feature is fully INERT (no behavioral signal) → file as NEGATIVE-no-effect / saturated.

**Per-symbol decomposition prediction** (T9-derived, pre-registered as a binding falsifier test, /119-template): given A4's TRX-carrier T9 signature, the expected production IS PnL Δ vs /121 baseline should be POSITIVE on TRX (the carrier) AND NEGATIVE on at least 1 of BCH or LDO (the SSC asymmetry realized). If the realized per-symbol decomposition is TRX-NEGATIVE OR BCH/LDO-both-positive (the SSC inversion), file Mode 3 PROMISING-PARTIAL with axis-CLOSE recommendation.

---

## Section 5 — Risk Mitigation

| Risk | Mitigation | IS-calibrated threshold |
|---|---|---|
| R1: Univariate signal absent (T3 informational; A4 just clears null q95 by 0.001) | A4 chosen on multivariate-lift (T7 +0.0012) + T2-PASS, not on univariate strength; production runner uses multivariate LightGBM at depth 3-5 (where weak features can contribute through interaction) | T7 POOLED lift +0.0012 is BELOW the /118+/119 +0.003 threshold — pre-registered Mode 2 INERT prediction |
| R2: Single-symbol-carrier risk (the /118 catastrophic failure mode) | NEW SSC-RISK gate evaluated at T9; A4 fails (TRUE) at 3.63× with TRX as carrier; band-tightened per /119 convention | T9 SSC ratio 3.63× — band upper bound IS Δ ≤ +0.10 / OOS Δ ≤ +0.10; F4 falsifier pre-registered |
| R3: Importance INERT at production scale (the /015/082/085/086 pattern; the EDA modal prediction) | Pre-registered Mode 2 + F2 falsifier in Section 7; the T5 BCH rank 15/15 signature is the controlling diagnostic | If production importance rank ≥ 14/15 on > 1 symbol AND POOLED lift not materially > 0, file PROMISING-INERT / NEGATIVE-INERT |
| R4: Per-symbol role-reversal vs T9 prediction (TRX-carrier becomes BCH-carrier or LDO-carrier) | EDA T7 has weak per-symbol lift sign uniformity (BCH +0.0001 / LDO −0.0034 / TRX −0.0044 — none of the per-symbol production lifts are confidently signed); a role-reversal at production is a F4 falsifier match | F4 falsifier: TRX-NEGATIVE OR BCH/LDO-both-positive at production = Mode 3 PROMISING-PARTIAL |
| R5: Look-ahead via ETH klines or merge convention | `eth_ret_3d = log(close[t]) − log(close[t−9])` is past-only; ETH klines source is `data/ETHUSDT/8h.csv` (the same fetcher convention as BCH/LDO/TRX); merge on `open_time` is the same convention as `btc_ret_3d` in cross_btc_v3.py; unit test Change 5 verifies past-only on synthetic data | Test must PASS in CI before merge; Critic Check 1 (Look-Ahead) at Phase 7.5 |
| R6: Parquet column missing at runtime | Change 4 mandates parquet regeneration; runner has hard assertion (lgbm.py:582-589 verifies feature_columns); Change 6 integration test catches at runtime | n_features == 15 hard guard at runner pre-flight |
| R7: ETH klines stale or missing | Engineer pre-flight verifies `data/ETHUSDT/8h.csv` exists, has ≥ 6990 rows, last close_time within 16h | ETH data freshness mirrors BTC data freshness rule |
| R8: ETH klines cached at module load (per `_ETH_CACHE_V3` pattern) — risk of stale cache | The `_ETH_CACHE_V3` pattern mirrors `_BTC_CACHE_V3` in cross_btc_v3.py; module is re-imported per runner invocation; no inter-run cache persistence | Audit at Critic Check 1 |
| R9: ETH klines merge introduces NaN at the IS/OOS boundary | Left-join on `open_time` preserves symbol's panel rows; rows without ETH match get NaN for `eth_ret_3d`; LightGBM handles NaN via tree-split convention | Engineer pre-flight check: NaN count for `eth_ret_3d` < 1% of total rows |

---

## Section 6 — Risk Management Design

The 7-gate RiskV2 stack is UNCHANGED:
1. Vol scaling (vol_scale_floor_per_symbol = {} → no floor)
2. ADX threshold (20.0; no per-symbol override)
3. Hurst regime check
4. z-score OOD gate (threshold = 2.0)
5. Low-vol filter
6. Hit-rate feedback (OOS only)
7. BTC trend alignment filter

The /116 no_confirm RULE-layer primitive is ENABLED at baseline (`enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`) per the /121 CONFIRMATION-MERGE — UNCHANGED at /122 per user directive 2026-05-20.

No new risk primitive introduced at /122. The single axis is the new ETH-cross-asset feature column.

**Hard-merge gate implications for /132 CONFIRMATION** (if /122 lands PROMISING — unlikely given EDA MARGINAL classification):

| Gate | /122 EDA estimate | /132 CONFIRMATION requirement |
|---|---|---|
| IS Sharpe > 1.0 | EDA models modal IS Sharpe ∈ [+0.96, +1.16] (EXPLORATION-mode) — uncertain margin | CONFIRMATION must clear at multi-seed mean |
| OOS Sharpe > 1.0 | EDA models modal OOS Sharpe ∈ [+0.70, +0.95] (EXPLORATION-mode); OOS Δ +0.05 vs /121 would clear the sacred dual-floor | CONFIRMATION must clear |
| OOS/IS ratio ≥ 0.5 | /121 has 0.74 buffer | needs multi-seed validation |
| Trade-rate ≥ 10/month OOS | /121 at 7.0/month — outstanding constraint; A4 not expected to improve | NEEDS structural axis at later cycle |
| Top-symbol ≤ 30% | /121 at BCH 95.76% — structural property of universe | unchanged |
| 10-seed validation | Single-seed at /122 EXPLORATION; full 10-seed at /132 | /132 |

The /122 brief does NOT promise merge-eligibility — it promises a single-axis EXPLORATION result that feeds into the cycle-7 axis-prior catalog. **The EDA's MARGINAL classification (+0.0012 POOLED lift below threshold; BCH rank 15/15 INERT signature; SSC TRUE 3.63×) means /122 is most likely NEGATIVE-no-effect or NEGATIVE-INERT at production.** A surprise PROMISING outcome would be a real finding (the first OHLCV-cross-asset NEW feature in v3 history with positive verdict; one of the four /119 §8.2 axes ruled productive).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Seven modes pre-registered (Mode 1 = success; Modes 2-7 = failure/surprise variants). **First-match-wins**: classify by the FIRST mode whose condition matches the observed outcome.

| Mode | Condition (BEFORE checking the result) | Probability prior | Verdict if matches |
|---|---|---:|---|
| **Mode 1 (Modal success)** | IS Sharpe Δ ∈ [+0.05, +0.20] vs /121 EXPLORATION-mode estimate AND OOS Sharpe Δ ∈ [+0.00, +0.15] AND common-trade fraction with /121 ∈ [70%, 90%] AND production importance rank ≤ 11/15 on ≥ 2 symbols | 10% | EXPLORATION-PROMISING (the OHLCV-cross-asset hypothesis surprised positively; /132 bundle candidate) |
| Mode 2 (Importance INERT at production — EDA MODAL) | Production importance rank ≥ 14/15 on > 1 symbol AND POOLED lift estimate < +0.005 | **35%** | PROMISING-INERT (the /082/085/086 precedent; not bundled at /132) |
| Mode 3 (Per-sym role-reversal vs T9 prediction) | TRX IS PnL Δ NEGATIVE (vs T9 prediction TRX-carrier) AND BCH/LDO IS PnL Δ BOTH-positive | 5% | PROMISING-PARTIAL — the SSC inversion; axis-CLOSE recommendation |
| Mode 4 (Catastrophic regime artifact) | IS Sharpe Δ < −0.40 OR OOS Sharpe Δ < −0.30 vs /121 multi-seed baseline | 5% | EXPLORATION-NEGATIVE (the OHLCV-cross-asset hypothesis falsified for eth_ret_3d; axis CLOSED) |
| **Mode 5 (Null at production — EDA MODAL alternative)** | IS Sharpe Δ ∈ [−0.05, +0.05] AND common-trade fraction with /121 > 95% | **30%** | NEGATIVE-no-effect (the /015 saturated-axis pattern; feature is fully INERT, drop) |
| Mode 6 (Suspicious-OOS-dominant) | OOS Sharpe Δ > +0.30 BUT IS Sharpe Δ < +0.05 (or worse) | 10% | SUSPICIOUS per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — /082/085/086 OOS-spike-artifact pattern |
| Mode 7 (Suspicious-IS-dominant / overfitting) | IS Sharpe Δ > +0.40 BUT OOS Sharpe Δ < −0.20 | 5% | SUSPICIOUS-IS-overfit (the /102 alpha032 pattern) |

**EDA Modal prediction**: Mode 2 (35%) or Mode 5 (30%) — both INERT outcomes. Mode 2 + Mode 5 together = 65% probability of an INERT-class result. Mode 1 (success) is 10% — the EDA's signal is weak enough that we explicitly model the success case as low-probability.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

EXPLORATION-mode criteria (first-match-wins; the post-result classification the QR commits to BEFORE looking at the result):

### NEGATIVE criteria (any-of-the-below)

1. **NEGATIVE-catastrophic**: IS Sharpe Δ < −0.40 vs /121 baseline OR OOS Sharpe Δ < −0.30 vs /121 baseline → file EXPLORATION-NEGATIVE catastrophic. Axis-CLOSE recommendation: the broader OHLCV-cross-asset feature hypothesis CLOSED at /122 (ETH cross-asset feed didn't lift in production); future cross-asset axes must either use a STRUCTURALLY DIFFERENT non-OHLCV feed (which the 7-FEED verdict CLOSES) or a different transformation of the ETH OHLCV (e.g., ETH realized vol regime classifier, ETH cross-sectional rank).

2. **NEGATIVE-no-effect**: IS Sharpe Δ ∈ [−0.05, +0.05] AND common-trade fraction with /121 > 95% AND production importance rank ≥ 14/15 on all 3 symbols → file EXPLORATION-NEGATIVE no-effect (the /015 saturated-axis pattern; **EDA modal expectation**).

3. **NEGATIVE-INERT**: production importance rank ≥ 14/15 on > 1 symbol AND POOLED lift estimate < +0.005 AND IS Sharpe Δ < +0.05 → file EXPLORATION-NEGATIVE-INERT (the /082/085/086 precedent; **EDA modal expectation**).

4. **NEGATIVE-clean**: IS Sharpe Δ < +0.05 AND OOS Sharpe Δ < +0.05 (both arms fail the PROMISING leg threshold) AND none of Modes 1-7 match → file EXPLORATION-NEGATIVE clean.

### PROMISING criteria (all-of-the-below)

5. **PROMISING-strong**: IS Sharpe Δ ≥ +0.10 vs /121 EXPLORATION-mode estimate AND OOS Sharpe Δ ≥ +0.10 vs /121 EXPLORATION-mode estimate AND production importance rank ≤ 11/15 on ≥ 2 symbols AND common-trade fraction ∈ [70%, 90%] AND no Mode 3/4 falsifier → file EXPLORATION-PROMISING strong. Bundle candidate for /132 CONFIRMATION.

6. **PROMISING-partial**: Only 1 of 3 symbols IS-positive AND that symbol IS PnL Δ > +3pp AND another symbol IS PnL Δ < −1pp → file EXPLORATION-PROMISING-PARTIAL. /132 bundles only if a per-symbol gate is also tested at a future iteration. The TRX-carrier T9 prediction is the modal pattern for this — TRX-only positive at production fits this branch.

7. **PROMISING-INERT-RISK**: T5 importance rank ≥ 14/15 on > 1 symbol AND POOLED lift estimate < +0.005 at production AND IS Sharpe Δ ∈ [+0.05, +0.20] → file EXPLORATION-PROMISING-INERT-RISK (the /085 pattern). Not bundled at /132.

8. **SUSPICIOUS**: OOS Sharpe Δ > +0.30 BUT IS Sharpe Δ ∈ [−0.10, +0.05] → SUSPICIOUS-OOS-DOMINANT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. The /082/085/086 OOS-spike artifact pattern; classify per /085 closeout convention (sub-channel diagnosis at Phase-8 roster-diff).

### Anchor

The /122 backtest will be compared multi-anchor: (1) the **/121 architecturally-adjusted EXPLORATION-mode estimate (IS +1.06 / OOS +0.85)** — the falsifier band reference; (2) the **/121 multi-seed CONFIRMATION baseline (IS +1.3108 / OOS +0.9682)** — the public anchor for documentation and Section 8 NEGATIVE-catastrophic threshold. The IS-Δ + OOS-Δ are computed vs /121 multi-seed for the NEGATIVE-catastrophic threshold; falsifier band classification uses the architecturally-adjusted estimate.

---

## Section 9 — Library Stack Declaration

**No new library dependencies** — `eth_ret_3d` is built from existing primitives (`close` column of `data/ETHUSDT/8h.csv`) using numpy `log` and array indexing. All required functions are already imported in `cross_btc_v3.py`.

**Library inventory** (verified at /122):
- `lightgbm == 4.6.0` (unchanged from /121)
- `numpy >= 2.0` (unchanged)
- `pandas >= 2.2` (unchanged)
- `scikit-learn` (used only in EDA, not in production runner)
- No `statsmodels` / `optuna` / `pyarrow` version change

**Adversarial integration test** (per `feedback_v3_methodology_axis_integration_test.md`): the `Change 6` integration test asserts:
- `V3_FEATURE_COLUMNS` includes `"eth_ret_3d"` at runtime (the 15th feature)
- `len(V3_FEATURE_COLUMNS) == 15`
- The parquet for BCH/LDO/TRX has the `eth_ret_3d` column non-NaN on the LAST 100 IS rows
- Runner pre-flight n_features guard fires `n == 15`
- The feature value from `add_cross_btc_v3_features()` for 10 random IS rows matches the EDA's stand-alone computation (numerical reconciliation: `analysis/iteration_v3-122/_shared.py`'s `_load_eth_klines` produces the SAME values as the production `_load_eth_v3_features`)
- The `compute_eth_ret_3d` unit test PASSES (past-only invariant on synthetic data; the Change 5 test)

These 6 assertions cover the end-to-end integration boundary (ETH CSV loader → cross_btc_v3 merge → runner → strategy → model fit) at the runtime call-site, not just the unit-level math.

---

## Section 10 — QR Audit Trail

**Provenance of the /122 axis selection**:

1. **/121 closeout diary directives** (`diary-v3/iteration_v3-121.md` Section 7.1): "cycle-7 EXPLORATIONs anchor against THIS baseline (iter-v3/121 unified 10-seed with /116 no_confirm primitive merged), NOT the retired /059 anchor". Candidate axis menu: (1) cross-asset/external feeds, (2) non-LightGBM model classes, (3) longer-cadence labels, (4) NEW symbol universe.

2. **User directive 2026-05-20** (the autopilot session): symbols LOCKED to BCH/LDO/TRX, model LOCKED to LightGBM, /116 no_confirm STAYS enabled. This LOCKS OUT axes (2) and (4) from cycle 7. The actionable axes are (1) cross-asset/external feeds and (3) longer-cadence labels.

3. **/122 QR axis adjudication (this brief)**:
   - **Axis (3) longer-cadence labels** evaluated and rejected: BASELINE_V3.md Dead Ideas explicitly closes the labeling-timeout family ("CLOSED both directions" at /069 closeout after /068 NEGATIVE-catastrophic 21→42 candle timeout). A coherent label+execution longer-cadence (e.g., 42-candle label + 42-candle barrier) is the genuinely-new variant of this closed axis, but it triples REQUIRED_GAP from 66 → ~129 with substantial walk-forward impact and remains structurally adjacent to /068's failure mode. Deferred to a later cycle-7 EXPLORATION if /122/123/124 also INERT.
   - **Axis (1) cross-asset/external feeds** evaluated; chose ETH OHLCV as the structurally-cleanest sub-axis that respects the 7-FEED structural verdict (which is scoped to NON-OHLCV crypto-native sentiment-metadata feeds: funding, microstructure, basis — all derivatives-metadata). ETH OHLCV is OUT-OF-SCOPE because it is OHLCV data (same family as the existing baseline `btc_ret_14d` and `sym_vs_btc_ret_7d` features) and structurally distinct from sentiment-metadata feeds.
   - The /122 EDA evaluated 4 ETH-derived candidates: A1 (eth_ret_14d), A2 (eth_vs_btc_ret_21d), A3 (eth_vs_btc_vol_diff_14d), A4 (eth_ret_3d). The decision was driven by:
     - A1 REJECT-R2 (R²=0.70 with btc_ret_14d; algebraic clone)
     - A2 REJECT (POOLED lift NEGATIVE; SSC 8.81×)
     - A3 WEAK (univariate fails; SSC 28×)
     - A4 MARGINAL (T2 PASS; POOLED lift +0.0012 below threshold but POSITIVE; T9 SSC 3.63× TRUE band-tightening)
   - A4 selected as least-bad T2-passing candidate. Brief models the modal outcome as NEGATIVE (Mode 2 INERT or Mode 5 no-effect, combined 65% probability) per the EDA's WEAK signal — but PRIME DIRECTIVE runs the backtest regardless.

4. **EDA artifacts committed BEFORE this brief**: `analysis/iteration_v3-122/` (SHA `b875272`), 13 files including `_shared.py`, `eth_cross_asset_screen.py`, `eth_adf_audit.py`, 9 CSV result tables, and `synthesis.md`. Every script asserts `close_time < OOS_CUTOFF_MS = 1742774400000`.

5. **Cycle-7 cadence accounting** (per `feedback_v3_strict_10_to_1_cadence.md`): /122 is slot 1 of 10. Subsequent slots /123-/131 + CONFIRMATION /132 follow the strict 10:1 ratio. The /121-METHODOLOGY BOOTSTRAP does NOT count toward cycle-7 cadence (analogous to /018 precedent).

6. **Falsifier band methodology choice (Section 4.3)**: The architecturally-adjusted /121 EXPLORATION-mode estimate (IS +1.06 / OOS +0.85) is used for the falsifier band reference because /122 runs at 3-seed EXPLORATION mode and comparing 3-seed results to a 10-seed baseline directly without adjustment would systematically misclassify EXPLORATION outcomes. The adjustment factor (IS −0.25 / OOS −0.12) is taken from the /077 vs /059 anchor-staleness work documented in BASELINE_V3.md Measurement Discipline section. This is the cleanest interpretation per the prompt's "default to the cleanest interpretation: anchor /122 EXPLORATION result against /121's multi-seed BASELINE numbers directly, with the understanding that 3-seed EXPLORATION will compress the numbers somewhat" — the brief explicitly accounts for the compression rather than ignoring it.

7. **The honest pre-registration**: the EDA's modal verdict is NEGATIVE-INERT or NEGATIVE-no-effect (combined 65% probability). The brief is honest about this — Mode 1 (Modal success) has only 10% probability. A surprise PROMISING outcome would be a real finding, but the EDA's signal is genuinely WEAK and the SSC TRUE flag pre-registers band-tightening. The PRIME DIRECTIVE runs the backtest regardless; even a NEGATIVE outcome (the most likely) is publishable as the 4th data point on the OHLCV-cross-asset hypothesis (with /063's btc_ret_3d as a prior, also removed for collateral mass-expansion reasons).
