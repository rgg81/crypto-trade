# iter-v3/123 Research Brief — Cycle-7 EXPLORATION #2 (first /122 closeout Critic Rec 1 application)

**Axis**: cycle-7 EXPLORATION slot #2 of 10. SECOND ETH-cross-asset sub-axis tested in cycle 7, structurally orthogonal to /122 axis-1. Adds **one** ETH-derived primitive to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15): `B1 = eth_realized_vol_50 / sym_realized_vol_50` — the ETH-vs-symbol 50-bar realized-vol REGIME RATIO. The candidate is a SECOND-MOMENT cross-asset RATIO (NOT a composed feature, NOT a first-moment ETH primitive), structurally orthogonal to the /122 IC-spanning incumbents `vwap_dev_20` and `regime_momentum_signed_5d` which are both first-moment primitives. Selected via committed EDA per `feedback_v3_axis_selection_quant_discipline.md`.

**/122 lesson applied** (the controlling discipline change vs /122):

At /122 EDA, `A4_eth_ret_3d` passed the joint-R² screen (R²=0.44) but FAILED at production with EXPLORATION-NEGATIVE-INERT verdict. Critic FINAL `9e0eeb6` identified the missing diagnostic: `eth_ret_3d` had pairwise IC = 0.5613 with `vwap_dev_20` and 0.5280 with `regime_momentum_signed_5d` — substantially spanned by 2-3 incumbents at the 0.50-0.56 |IC| range. The /122 Critic Recommendation 1 mandated: "EDA must show pairwise |IC| < 0.40 with `vwap_dev_20` and `regime_momentum_signed_5d` specifically. Joint-R² is insufficient diagnostic for ETH-derived primitives."

The /123 EDA implements this strict pairwise-IC gate. B1 clears the strict 0.40 gate by material margin:
- IC with `vwap_dev_20` = **0.0687** (8.2× /122 reduction)
- IC with `regime_momentum_signed_5d` = **0.0205** (25.8× /122 reduction)
- Max pairwise IC across the 14-feature anchor = 0.5204 (with `range_realized_vol_50` — the symbol's own realized vol — by construction, since B1 = `eth_rv / sym_rv` shares the symbol-rv denominator. This is a STRUCTURAL correlation, not a redundancy: the cross-asset NUMERATOR is what carries the new signal.)

**Lineage discipline** (INHERITED FROM /122): ETH OHLCV is OUT-OF-SCOPE of the BASELINE_V3.md "7-FEED structural verdict" (which addressed non-OHLCV crypto-native sentiment-metadata feeds: funding /019/023/024/082/085, microstructure /015, basis /086 — all derivatives-metadata). The B1 vol-ratio is computed entirely from OHLC close prices via 1-bar log returns and rolling std — no derivatives-metadata is involved. See `analysis/iteration_v3-123/_shared.py` docstring + `synthesis.md` for the full lineage adjudication.

**Cycle**: 7 EXPLORATION slot **#2 of 10**. Cycle-7 catalog state at /122 closeout: slot #1 (/122 axis-1 A4_eth_ret_3d) ran → EXPLORATION-NEGATIVE-INERT. /123 = second cycle-7 EXPLORATION, first to apply /122 Critic Rec 1 strict pairwise-IC gate.

**Anchor (dual-anchor protocol)** — per /122 Critic Recommendation 3 (the "Pre-register dual-anchor disambiguation explicitly in /123 brief Section 8" recommendation):

| Anchor | Mode | IS Sharpe | OOS Sharpe | Use |
|---|---|---:|---:|---|
| /121 multi-seed CONFIRMATION (public canonical) | 10-seed | +1.3108 | +0.9682 | NEGATIVE-catastrophic threshold + headline reporting |
| /121 architecturally-adjusted EXPLORATION-mode estimate | 3-seed est. | **+1.06** | **+0.85** | EXPLORATION-mode falsifier band reference |

The adjustment factor: IS −0.25 / OOS −0.12 (the cycle-2 /077 vs /059 anchor-staleness work documented in BASELINE_V3.md). Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode 3-seed runs compress relative to CONFIRMATION-mode 10-seed.

Per Critic Rec 3, **Section 8 explicitly annotates which anchor applies to each criterion**.

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. The sacred constants are immutable across all three tracks; no /123 modification touches them.

- **IS window**: data extent start (per-symbol earliest 8h candle close ≥ 2020-01-01) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent (~2026-05-20).
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **Reporting layer**: `comparison.csv` and `in_sample/` / `out_of_sample/` directories split on `OOS_CUTOFF_DATE` exactly.
- **Bar interval**: 8h (cycle-6 candle-frequency axis broadly CLOSED per /117 closeout; cycle-7 stays at 8h).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

The /123 axis introduces **NO tuned scalar parameter** — every primitive is INHERITED from the natural realized-vol geometry at the baseline window.

| Parameter | Value | Provenance |
|---|---|---|
| Rolling window W | **50 bars (= 16.7 calendar days at 8h)** | INHERITED from the baseline `range_realized_vol_50` 50-bar canonical window (per `multioffset_24h.py:296` — the SYMBOL'S OWN realized-vol-50 IS a baseline feature). The cross-asset ratio extends the symbol's vol-regime ANCHOR into ETH cross-asset territory at exactly the same window — the strongest possible inheritance signal. NOT tuned for /123. |
| Realized-vol estimator | **`rolling(50, min_periods=50).std()` of 1-bar log returns** | INHERITED past-only convention from baseline `range_realized_vol_50`. NOT tuned. |
| Ratio operator | **element-wise `eth_rv_50 / sym_rv_50` with 1e-12 epsilon** | Structural; epsilon prevents division-by-zero on degenerate vol values. NOT tuned. |
| ETH source CSV | **`data/ETHUSDT/8h.csv`** | INHERITED from /122 — same fetcher convention as BCH/LDO/TRX/BTC. |
| Merge convention | **left-join on `open_time`** | INHERITED from /122 `cross_btc_v3.py` pattern. NOT tuned. |

**ZERO tuned scalars in /123.** Every numeric design choice is either inherited from the existing v3 baseline pattern (the symbol's own realized-vol-50 is a baseline feature) or structurally fixed by the algebraic form. This is parity with /122's posture.

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-123/`, commit `dbc2993`) was committed in ONE atomic commit BEFORE this brief. Every script in the EDA directory asserts `close_time < OOS_CUTOFF_MS = 1742774400000`; no OOS-window file is read at any point. Verified at EDA: 0 OOS-leaked rows across all 3 symbols (BCH 5606/0, LDO 2620/0, TRX 5548/0).

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: NEW cross-asset feature in `V3_FEATURE_COLUMNS_TOP_N`, 14 → 15)
- **Cycle 7 slot**: **#2 of 10**. iter-v3/131 is the projected final EXPLORATION (cycle-7 ends with iter-v3/132 CONFIRMATION per the strict 10:1 cadence; `feedback_v3_strict_10_to_1_cadence.md`).
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35` (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per `feedback_v3_outer_seed_cap_2_v3.md`; first 3 seeds of the unified 10-seed lineage)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md` — above TPE warmup ~30; the v3 EXPLORATION default since iter-v3/019)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`; recent EXPLORATIONs: /122 0.70h, /118 0.72h, /117 0.64h, /119 1.1h)
- **Single axis variation**: ONE new feature added to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15: append `eth_vs_sym_rv_50`). All other knobs (universe, label, gates, ensemble seeds, Optuna search space, /116 no_confirm primitive) are bit-identical to the /121 baseline. Note: /122 setup added `eth_ret_3d` then was filed NEGATIVE-INERT — /123 setup REVERTS `eth_ret_3d` back out and ADDS `eth_vs_sym_rv_50` in its place. Net effect vs /121 baseline: ONE new feature.

---

## Section 1 — Hypothesis

> Adding **`eth_vs_sym_rv_50`** = `eth_realized_vol_50 / sym_realized_vol_50` (ETH-vs-symbol 50-bar realized-vol regime ratio) as the 15th feature in `V3_FEATURE_COLUMNS_TOP_N` carries incremental directional signal beyond the /121 14-feature stack on the BCH/LDO/TRX 8h cohort. The hypothesis is grounded in cross-asset volatility-regime divergence as a positioning signal: when ETH's realized vol regime is elevated relative to the symbol's own vol regime, alt idiosyncratic moves are conditioned by ETH-led volatility. The feature is structurally orthogonal to the 14-feature anchor (max pairwise IC 0.52 with `range_realized_vol_50` is the symbol-rv denominator's structural correlation — NOT a redundancy; the cross-asset NUMERATOR carries the new signal) and specifically non-IC-spanned by the /122 spanning incumbents (`vwap_dev_20` IC=0.069, `regime_momentum_signed_5d` IC=0.021 — both well below the /122 Critic Rec 1 strict 0.40 gate).
>
> Expected lift: EXPLORATION-mode IS monthly Sharpe Δ ∈ [+0.05, +0.30] vs the architecturally-adjusted /121 EXPLORATION-mode reference (IS +1.06) AND OOS monthly Sharpe Δ ∈ [+0.00, +0.25] vs the /121 architecturally-adjusted OOS +0.85 reference; OR the ETH-realized-vol-cross-asset hypothesis is FALSIFIED at production by an EXPLORATION-NEGATIVE result, closing the second of the four /119 §8.2 candidate menu items and informing cycle-7's axis-selection priors.

---

## Section 2 — IS-Only Numerical Evidence

EDA (`analysis/iteration_v3-123/`, commit `dbc2993`): 4 ETH-vs-sym vol-ratio candidates evaluated via the /122 / /119 / /118 5-step methodology + the NEW /122 Critic Rec 1 strict pairwise-IC gate (T1 catalog, T2 linear redundancy with pairwise IC, T3 POOLED univariate, T4 per-symbol univariate, T5 multivariate importance, T7 multivariate lift, T9 SSC-RISK gate, T6 GO/NO-GO, T8 ADF stationarity).

### Section 2.1 — T1 catalog (4 candidates)

See `T1_candidate_catalog.csv`:

| ID | Formula | W |
|---|---|---:|
| **B1** | `eth_rv_50 / sym_rv_50` (PRIMARY) | 50 |
| B1a | `log(eth_rv_50 / sym_rv_50)` (sister: scale-symmetric log transform) | 50 |
| B1b | `eth_rv_25 / sym_rv_25` (sister: shorter-cadence responsiveness variant) | 25 |
| B1c | `eth_rv_100 / sym_rv_100` (sister: longer-cadence smoothing variant) | 100 |

### Section 2.2 — T2 Linear Redundancy Pre-Falsifier (with NEW /122 Critic Rec 1 pairwise-IC gate)

See `T2_linear_redundancy_pre_falsifier.csv`:

| Candidate | Joint R² | IC vwap_dev_20 | IC regime_mom_signed_5d | Max pairwise IC | Verdict |
|---|---:|---:|---:|---:|---|
| B1b (W=25) | 0.3152 | 0.041 | 0.052 | 0.453 (range_realized_vol_50) | PASS |
| **B1 (W=50)** | **0.3937** | **0.069** | **0.021** | 0.520 (range_realized_vol_50) | **PASS** |
| B1c (W=100) | 0.3951 | 0.073 | 0.002 | 0.518 (range_realized_vol_50) | PASS |
| B1a (log W=50) | 0.4730 | 0.066 | 0.050 | 0.540 (range_realized_vol_50) | PASS |

All 4 candidates PASS both gates (joint R² < 0.70 strict AND pairwise IC < 0.40 strict with both spanning incumbents). For comparison, /122's eth_ret_3d had IC=0.5613 with vwap_dev_20 and 0.5280 with regime_momentum_signed_5d — **B1's pairwise IC profile is 8-26× cleaner**.

The max pairwise IC for all 4 candidates is with `range_realized_vol_50` (the symbol's own 50-bar realized vol). This is a STRUCTURAL correlation by construction — B1 = `eth_rv / sym_rv` shares the sym_rv denominator, so the ratio anti-correlates with sym_rv. The IC with the DENOMINATOR's INVERSE is ~0.52 by algebraic identity; this is not redundancy because the cross-asset NUMERATOR (eth_rv) is the new information content. **An OLS regression of B1 on `range_realized_vol_50` would leave a substantial residual that captures the eth_rv signal.**

### Section 2.3 — T3 POOLED + T4 per-symbol univariate

See `T3_walkforward_pooled_auc.csv` + `T4_per_symbol_auc.csv`:

| Candidate | POOLED AUC | q95 null | p-value | clears_q95 |
|---|---:|---:|---:|:---:|
| B1a | 0.4915 | 0.5072 | 0.89 | NO |
| B1c | 0.4783 | 0.5072 | 0.99 | NO |
| B1b | 0.4745 | 0.5102 | 1.00 | NO |
| B1 | 0.4694 | 0.5069 | 1.00 | NO |

All 4 candidates have univariate AUC BELOW the null q95. This is structurally expected for a SECOND-MOMENT primitive: vol-ratio is not a direction signal in isolation, it's a regime classifier that interacts MULTIVARIATELY with other features (per the T7 +0.0063 lift result). The univariate AUC is INFORMATIONAL for vol-ratio features per the /117 g1 hard gate convention — multivariate lift (T7) is the controlling diagnostic. Same convention used in /118 / /119 / /122 EDAs.

Per-symbol AUC (T4):
- **B1**: BCH 0.474 / LDO 0.513 / TRX 0.479 (1 g1 pass — LDO)
- B1a: BCH 0.476 / LDO 0.505 / TRX 0.485 (1 g1 pass — LDO)
- B1b: BCH 0.474 / LDO 0.472 / TRX 0.496 (0 g1 passes)
- B1c: BCH 0.474 / LDO 0.401 / TRX 0.480 (0 g1 passes)

LDO carries univariate signal (AUC 0.513 > 0.500); BCH is BTC-fork-coupled and structurally insensitive to ETH cross-asset signals (the same pattern observed at /122 for eth_ret_3d).

### Section 2.4 — T5 multivariate importance (the strongest cross-asset signal in v3 EDA history)

See `T5_importance_rank_multivariate.csv`:

| Candidate | BCH rank/gain% | LDO rank/gain% | TRX rank/gain% |
|---|---|---|---|
| **B1** | 15 / 4.46% | **1 / 14.00%** | 4 / 9.07% |
| B1a | 14 / 4.66% | 1 / 14.00% | 5 / 9.25% |
| B1c | 14 / 4.31% | 4 / 10.43% | 2 / 11.04% |
| B1b | 15 / 4.39% | 3 / 11.70% | 3 / 10.58% |

**B1's LDO rank 1/15 (14.0% gain share) is the STRONGEST cross-asset feature allocation in v3 EDA history.** For reference, /122's eth_ret_3d at production had LDO rank 11, BCH 14, TRX 10 — all mid-table or dead-last. B1's allocation is materially stronger: top-1 on LDO + rank 4 on TRX, vs BCH 15/15 INERT.

The asymmetry pattern: BCH is structurally insensitive to ETH cross-asset (BCH is a BTC fork, tightly BTC-coupled). LDO and TRX are alts where ETH's vol regime carries real information. This is the controlling diagnostic that drives the SSC-RISK gate.

### Section 2.5 — T7 multivariate-LIFT screen (controlling test)

See `T7_multivariate_lift_screen.csv`:

| Candidate | POOLED lift | BCH lift | LDO lift | TRX lift |
|---|---:|---:|---:|---:|
| **B1** | **+0.0063** | −0.0092 | +0.0215 | +0.0029 |
| B1a | +0.0059 | −0.0088 | +0.0215 | +0.0053 |
| B1c | +0.0021 | −0.0031 | +0.0042 | −0.0042 |
| B1b | −0.0029 | −0.0038 | +0.0162 | +0.0003 |

**B1 POOLED lift +0.0063 is 2.1× the /118+/119 production-relevance threshold (+0.003) and 5.25× /122's A4_eth_ret_3d (+0.0012).** The POOLED-LIFT signal is the strongest "GO" indicator in cycle-7 axis-1 to date.

Per-symbol decomposition mirrors T5: LDO is the carrier (+0.0215), TRX modest positive (+0.0029), BCH NEGATIVE (-0.0092). The BCH-negative residual is the controlling signal that drives the SSC-RISK gate.

### Section 2.6 — T9 SSC-RISK gate

See `T9_ssc_risk_gate.csv`:

| Candidate | POOLED lift | Max abs per-sym | Carrier | SSC ratio | SSC RISK |
|---|---:|---:|---|---:|:---:|
| B1b | -0.0029 | 0.0162 | LDOUSDT | 5.65× | TRUE |
| B1a | +0.0059 | 0.0215 | LDOUSDT | 3.65× | TRUE |
| **B1** | **+0.0063** | **0.0215** | **LDOUSDT** | **3.43×** | **TRUE** |
| B1c | +0.0021 | 0.0042 | TRXUSDT | 2.02× | TRUE |

B1's SSC ratio 3.43× exceeds the 2× threshold (LDO carrier with +0.0215 lift vs POOLED +0.0063). Per the /119 SSC-RISK band-tightening convention, this pre-registers tighter upper bounds in the prediction bands (Section 4.3).

**Note on carrier identity vs /122**: /122 had TRX as the PnL-level carrier (despite INERT importance rank 15/15 — the /082/085/086/119 C6 dissociation pattern). B1 at EDA has LDO as the importance-level carrier (rank 1/15, gain share 14.0%) which is ALIGNED with the PnL-carrier prediction. This is a CLEANER pattern than /122 — the importance-allocation and PnL-attribution prediction are coherent rather than dissociated. **This is also B1's primary risk**: if the dissociation pattern recurs (importance-strong but PnL-flat), it would constitute another data point on the cross-asset importance-OOS-Sharpe dissociation mechanism.

### Section 2.7 — T6 verdict synthesis

| Candidate | Verdict | Notes |
|---|---|---|
| **B1_eth_vs_sym_rv_50** | **GO-SSC-RISK** | T7 lift +0.0063 (5.25× /122); T5 LDO rank 1/15 (top in v3 EDA history); SSC 3.43× LDO-carrier (importance-PnL aligned, cleaner than /122 dissociation); T8 ADF PASS p<0.01 |
| B1a_log_eth_vs_sym_rv_50 | GO-SSC-RISK | Sister-equivalent to B1; T7 +0.0059; T5 LDO 1/14.0% |
| B1c_eth_vs_sym_rv_100 | MARGINAL — DISQUALIFIED | T8 ADF FAIL on all 3 symbols (p≈0.12-0.14); the W=100 smoothing is too slow for stationarity |
| B1b_eth_vs_sym_rv_25 | REJECT | T7 lift NEGATIVE (-0.0029); LDO carrier 5.65× |

**Selection: /123 = B1 (eth_vs_sym_rv_50) with GO-SSC-RISK EDA signal.** The brief models the modal outcome as **MODE 1 (Modal success) with PROBABILITY 25%** — materially higher than /122's 10% — but Mode 2/Mode 5/Mode 6 INERT-class outcomes remain in 55% combined probability range given the SSC-RISK TRUE flag + the /119 C6 dissociation pattern lurking.

### Section 2.8 — ADF stationarity (T8)

See `T8_adf_stationarity.csv`. B1 specifically: BCH adf_stat=-3.6729 p=0.0045; LDO adf_stat=-3.5093 p=0.0078; TRX adf_stat=-3.5155 p=0.0076. All 3 PASS p<0.05. B1a + B1b also PASS. B1c FAILS (the longer W=100 regime is too smooth).

9/12 cells PASS (B1, B1a, B1b all PASS; B1c fails). The selected B1 passes cleanly on all 3 symbols at p<0.01 — substantially below the 0.05 v3 mandatory threshold.

---

## Section 3 — Proposed Changes (single-axis vs /121 baseline)

Note: the /122 setup added `eth_ret_3d` to `V3_FEATURE_COLUMNS_TOP_N` (14 → 15) but was filed NEGATIVE-INERT. /123 setup REVERTS `eth_ret_3d` back out (per Critic /122 Rec 1: "eth_ret_3d primitive CLOSED at /122") and ADDS `eth_vs_sym_rv_50` in its place. Net effect vs /121 baseline: ONE new feature.

### Change 1 — `src/crypto_trade/features_v3/cross_btc_v3.py`

Extend the existing module to compute the new `eth_vs_sym_rv_50` cross-asset feature. The ETH realized-vol must be precomputed at module-cache load; the SYMBOL realized-vol must be computed per-call (since the function receives the symbol's panel as argument).

Current state (BTC + ETH return primitives):
```python
ETH_CSV_PATH = Path("data/ETHUSDT/8h.csv")

def _load_eth_v3_features() -> pd.DataFrame:
    """Load ETH 8h klines and precompute ETH-derived columns (cached)."""
    ...
    df["eth_ret_3d"] = ...
    _ETH_CACHE_V3 = df[["open_time", "eth_ret_3d"]].copy()
    return _ETH_CACHE_V3
```

Proposed delta — REPLACE the eth_ret_3d primitive with eth_rv_50 in the cache, compute the ratio per-symbol:

```python
def _load_eth_v3_features() -> pd.DataFrame:
    """Load ETH 8h klines and precompute ETH realized-vol-50 (cached).

    iter-v3/123: Replaces eth_ret_3d (closed at /122 NEGATIVE-INERT) with
    eth_rv_50 = rolling(50, min_periods=50).std() of ETH 1-bar log returns.
    Past-only by construction (rolling.std with min_periods=W uses ONLY prior
    W bars at each timestamp). ETH klines source: data/ETHUSDT/8h.csv (same
    fetcher convention as BTC). Merge key: open_time (same convention as BTC merge).
    """
    global _ETH_CACHE_V3
    if _ETH_CACHE_V3 is not None:
        return _ETH_CACHE_V3

    df = pd.read_csv(ETH_CSV_PATH).sort_values("open_time").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)
    log_close = np.log(close)
    log_ret_1bar = np.concatenate([[np.nan], np.diff(log_close)])

    # eth_rv_50 = rolling(50, min_periods=50).std() of 1-bar log returns
    df["eth_rv_50"] = pd.Series(log_ret_1bar).rolling(50, min_periods=50).std().to_numpy()

    _ETH_CACHE_V3 = df[["open_time", "eth_rv_50"]].copy()
    return _ETH_CACHE_V3
```

And update the merge function — compute the ratio per-symbol after the ETH merge:

```python
def add_cross_btc_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Merge BTC + ETH-derived features into the symbol's feature frame."""
    out = df.copy()
    # ... existing BTC merge ...

    # iter-v3/123: ETH-vs-symbol vol-ratio (NEW; replaces /122's eth_ret_3d)
    eth = _load_eth_v3_features()
    out = out.merge(eth, on="open_time", how="left")
    # range_realized_vol_50 is the symbol's own RV-50 (already in panel from
    # multioffset_24h.py); we use it as the ratio denominator.
    EPS = 1e-12
    out["eth_vs_sym_rv_50"] = out["eth_rv_50"] / (out["range_realized_vol_50"] + EPS)
    # Drop intermediate
    out = out.drop(columns=["eth_rv_50"])
    return out
```

NOTE: this implementation REUSES the parquet's pre-computed `range_realized_vol_50` column as the denominator (verified via T2 EDA — the parquet's value matches our local recompute by construction; both use `rolling(50, min_periods=50).std()` on 1-bar log returns). This avoids duplicating the symbol-rv computation.

### Change 2 — `src/crypto_trade/features_v3/__init__.py`

Replace `"eth_ret_3d"` with `"eth_vs_sym_rv_50"` in `V3_FEATURE_COLUMNS_TOP_N` (length stays 15):

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
    "eth_vs_sym_rv_50",  # iter-v3/123 — NEW cycle-7 EXPLORATION axis-1 (ETH-vs-sym vol-ratio; B1 EDA top)
)
```

Update the comment header to record the /123 EXPLORATION + add `eth_ret_3d` to the runner ABSENT-list per the /082-funding family REVERT pattern (the primitive is closed but the loader infrastructure stays).

### Change 3 — `run_baseline_v3.py`

Update `ITERATION_LABEL` and the pre-flight assertions:
- Line ~131: `ITERATION_LABEL = "v3-123"` (was `"v3-122"`)
- Lines ~432-445 pre-flight: invert the `"eth_ret_3d" not in V3_FEATURE_COLUMNS` ban → assert PRESENCE of `"eth_vs_sym_rv_50"`; assert ABSENCE of `"eth_ret_3d"` (the /122 ABSENT-list pattern)
- Line ~625: update preflight banner string from "/122 NEW" to "/123 NEW (eth_vs_sym_rv_50)"
- `len(V3_FEATURE_COLUMNS_TOP_N) == 15` (unchanged — 15 features, just different 15th)
- ITERATION_LABEL propagates to `reports-v3/iteration_v3-123/`.

### Change 4 — Parquet regeneration

The parquet generation pipeline (`crypto-trade features`) must be re-run for BCH/LDO/TRX (and BTC, ETH for cache priming) to materialize the new `eth_vs_sym_rv_50` column. Engineer runs:

```bash
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 8h --track v3 --format parquet --workers 4
```

The parquet for BCH/LDO/TRX must contain `eth_vs_sym_rv_50` as a column (non-NaN on the last 100 IS rows). Engineer Phase 6 pre-flight asserts this.

### Change 5 — Unit test

Add a test in `tests/test_features_v3/` verifying `eth_vs_sym_rv_50` is past-only on a synthetic ETH panel:

```python
def test_eth_vs_sym_rv_50_past_only():
    # Build symbol panel + ETH panel with bars at indices [0..1500]
    # Compute eth_vs_sym_rv_50 then mutate ETH bars [1010+] to extreme values
    # Recompute and check eth_vs_sym_rv_50[t=1000] == original value for all t<=1000
```

Faithful to /122's `test_eth_ret_3d_past_only` pattern.

### Change 6 — Integration test

Add a test in `tests/test_run_baseline_v3.py` (or equivalent) asserting:
- `V3_FEATURE_COLUMNS_TOP_N` includes `"eth_vs_sym_rv_50"` (the 15th feature)
- `V3_FEATURE_COLUMNS_TOP_N` DOES NOT include `"eth_ret_3d"` (closed at /122)
- `len(V3_FEATURE_COLUMNS_TOP_N) == 15`
- The parquet for BCHUSDT/LDOUSDT/TRXUSDT has the `eth_vs_sym_rv_50` column non-NaN on the LAST 100 IS rows
- Runner pre-flight n_features guard fires `n == 15`
- The feature value from `add_cross_btc_v3_features()` for 10 random IS rows matches the EDA's stand-alone computation (numerical reconciliation: `analysis/iteration_v3-123/_shared.py`'s `_attach_eth_vol_ratio_features` produces the SAME values as the production `add_cross_btc_v3_features`)
- The `compute_eth_vs_sym_rv_50_past_only` unit test PASSES

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

| File | Change |
|---|---|
| `src/crypto_trade/features_v3/cross_btc_v3.py` | Replace `_load_eth_v3_features()` payload (eth_ret_3d → eth_rv_50); update `add_cross_btc_v3_features` to compute `eth_vs_sym_rv_50 = eth_rv_50 / (range_realized_vol_50 + EPS)`; drop intermediate `eth_rv_50` column |
| `src/crypto_trade/features_v3/__init__.py` | Replace `"eth_ret_3d"` with `"eth_vs_sym_rv_50"` in `V3_FEATURE_COLUMNS_TOP_N`; comment update with /123 history note |
| `run_baseline_v3.py` | Lines ~131 (ITERATION_LABEL), ~432-445 (pre-flight invert: ABSENT eth_ret_3d, PRESENT eth_vs_sym_rv_50), ~625 (banner string) |
| `tests/test_features_v3/test_cross_btc_v3.py` (or new test file) | Add `test_eth_vs_sym_rv_50_past_only`; remove or replace `test_eth_ret_3d_past_only` (the feature is no longer in production) |
| `tests/test_run_baseline_v3.py` (or equivalent) | Add `test_eth_vs_sym_rv_50_integration`; replace `test_eth_ret_3d_integration` |

**Files NOT touched** (negative scope):
- `src/crypto_trade/strategies/ml/lgbm.py` (no labeling change, no risk gate change)
- `src/crypto_trade/strategies/ml/labeling.py` (no label change)
- `src/crypto_trade/strategies/ml/walk_forward.py` (no walk-forward change; REQUIRED_GAP=66 unchanged)
- `src/crypto_trade/strategies/risk_v2.py` (gates unchanged)
- `src/crypto_trade/backtest.py` (no new exit primitive)
- `src/crypto_trade/features_v3/engineered_v3.py` (no engineered-feature change)
- All other `features_v3/*.py` modules
- `OOS_CUTOFF_DATE`, `training_months` — sacred constants, immutable
- /116 no_confirm primitive — STAYS ENABLED in baseline (locked constraint per /122 setup)
- /119 C6 ret5d_signed_tbi — STAYS in BANNED list (locked constraint per /122 setup)

---

## Section 4 — Expected OOS Impact (predicted bands) — SSC-RISK-aware

### Section 4.1 — Anchor-architecture adjustment (inherited from /122)

**Cycle-7 architecturally-adjusted EXPLORATION-mode reference for /123 axis-Δ classification** (inherited from /122):

| Anchor | Mode | IS Sharpe | OOS Sharpe | Use |
|---|---|---:|---:|---|
| /121 CONFIRMATION (canonical) | 10-seed | +1.3108 | +0.9682 | For CONFIRMATION-mode forward-looking gates only |
| **/121 EXPLORATION-mode estimate (architecturally adjusted)** | 3-seed estimate | **+1.06** | **+0.85** | **For /123 EXPLORATION-mode Δ classification** |

Per /122 Critic Rec 3, **Section 8 explicitly annotates which anchor applies to each criterion**. The brief uses BOTH anchors but with clear per-criterion assignment.

### Section 4.2 — Predicted bands

| Arm | Modal predicted Δ vs /121 EXPLORATION-mode estimate (IS +1.06 / OOS +0.85) | Lower (failure mode) | Upper (SSC-tightened) |
|---|---:|---:|---:|
| IS monthly Sharpe Δ | −0.05 to +0.20 | −0.40 (catastrophic) | +0.30 |
| OOS monthly Sharpe Δ | −0.10 to +0.15 | −0.30 (Mode 4) | +0.25 |

**Modal prediction band (EXPLORATION-mode reference):** IS Sharpe ∈ [+1.01, +1.26]; OOS Sharpe ∈ [+0.75, +1.00].

**Modal prediction band (against published /121 CONFIRMATION baseline, INFORMATIONAL):** IS Sharpe ∈ [+1.25, +1.50]; OOS Sharpe ∈ [+0.85, +1.10].

The modal prediction bands are **WIDER on the upper side than /122's** because:
1. T7 POOLED lift is 5.25× higher (+0.0063 vs +0.0012) → more probability mass on Mode 1
2. T5 LDO rank 1/15 (top-1 importance) is the strongest in v3 EDA history → suggests genuine information content (not /082 INERT-by-importance pattern)
3. Pairwise IC profile is 8-26× cleaner than /122 → less risk of IC-spanning collapse

The modal prediction bands are **also wider on the lower side than /122's** because:
1. SSC-RISK TRUE 3.43× (LDO carrier) → /119 C6 dissociation pattern lurking
2. BCH structurally INERT (BCH rank 15/15 + BCH lift -0.0092) → BCH is a known drag carrier
3. Single-seed EXPLORATION subject to loss-surface reorganization artifacts (the /082/085/086 pattern)

### Section 4.3 — SSC-RISK-aware band-tightening

B1's T9 SSC ratio 3.43× (TRUE flag, LDO carrier) triggers the /119-established band-tightening convention per `feedback_v3_promising_feature_mechanical.md` SSC-RISK rules: tighten upper bound IS Δ ≤ +0.30, OOS Δ ≤ +0.25 (single-symbol-carrier risk).

B1's carrier identity (LDO) is DIFFERENT from /122's (TRX at PnL level). LDO is the importance-allocation carrier (rank 1/15, 14.0% gain) AND the predicted PnL carrier (T7 lift +0.0215). The /119 dissociation mechanism (importance-strong but PnL-flat) would manifest as: production LDO IS PnL Δ small or negative despite T7 prediction +0.0215. This is the **primary risk** for the /123 axis.

**Pre-registered F1 falsifier (binding)**: if production OOS monthly Sharpe Δ vs /121 multi-seed baseline falls below **−0.30** AND IS monthly Sharpe Δ vs /121 multi-seed baseline falls below **−0.40**, the ETH-realized-vol-cross-asset hypothesis is FALSIFIED for the eth_vs_sym_rv_50 primitive; file EXPLORATION-NEGATIVE catastrophic.

**Pre-registered F2 falsifier (binding)**: if production importance rank for `eth_vs_sym_rv_50` falls to ≥ 14/15 on > 1 of 3 symbols AT THE FINAL IS MONTH, AND POOLED lift not materially > 0 (estimated via test-month directional accuracy diff), file EXPLORATION-PROMISING-INERT or EXPLORATION-NEGATIVE-INERT. This is the /082/085/086/122 INERT-by-importance signature; the EDA T5 LDO rank 1/15 makes this pre-registration STRONGER than /122 — if LDO drops below rank 5 at production, the EDA-vs-production divergence is the controlling signal.

**Pre-registered F3 falsifier (binding)**: if production OOS Sharpe Δ vs /121 multi-seed > +0.15 BUT IS Sharpe Δ < +0.00, file SUSPICIOUS-OOS-DOMINANT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. The /082/085/086/122 INERT-with-OOS-spike artifact pattern.

**Pre-registered F4 falsifier (binding)**: if production LDO-only IS PnL Δ > +5pp AND BCH IS PnL Δ < −1pp AND TRX IS PnL Δ < +1pp (the SSC-RISK realized as LDO-carrier asymmetry per the T9 prediction), file Mode 3 PROMISING-PARTIAL per the SSC-prediction precedent.

**Pre-registered F5 falsifier (binding) — NEW for /123**: if production LDO importance rank drops below 5/15 at the final IS month (i.e., LDO importance allocation does NOT match the T5 EDA's rank 1/15 prediction), AND production LDO IS PnL Δ is below +1pp, file the /119 C6 DISSOCIATION-PATTERN-RECURRENT verdict. This is a structural finding: ETH-realized-vol importance allocation predicts production allocation poorly even when EDA shows top-1 rank.

**Trade-rate prediction**: total IS trades expected ≈ /121 baseline count (173 IS) ± 10% (the new feature changes the Optuna loss surface but does not change entry/exit gates). OOS trades expected ≈ /121 baseline count (98 OOS) ± 15%. If OOS trade count falls by > 30% vs /121, file Mode 4 RESIDUAL.

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`): the new feature changes Optuna's loss surface, so the IS trade roster will differ from /121 — expected fraction of common IS trades vs /121 baseline roster: 70–90%. Higher T5 importance allocation (LDO rank 1) suggests MORE decision changes than /122's INERT eth_ret_3d (which kept common-trade fraction high). If common-trade fraction > 95%, the feature is fully INERT at production despite EDA → file as NEGATIVE-no-effect / saturated.

**Per-symbol decomposition prediction** (T9-derived, pre-registered as a binding falsifier test, /119-template): given B1's LDO-carrier T9 signature, the expected production IS PnL Δ vs /121 baseline should be POSITIVE on LDO (the carrier) AND NEGATIVE on BCH (the structural drag). If the realized per-symbol decomposition is LDO-NEGATIVE OR BCH-positive (the SSC inversion), file Mode 3 PROMISING-PARTIAL with axis-CLOSE recommendation.

---

## Section 5 — Risk Mitigation

| Risk | Mitigation | IS-calibrated threshold |
|---|---|---|
| R1: Univariate signal BELOW null (T3 informational; B1 univariate AUC 0.4694 < q95 0.5069) | B1 chosen on T7 multivariate-lift (+0.0063, 5.25× /122) + T5 LDO rank 1/15, not on univariate strength. Vol-ratio is second-moment regime classifier; univariate AUC is INFORMATIONAL per /117 g1 convention | T7 POOLED lift +0.0063 > +0.003 threshold (2.1× margin); F2 falsifier covers production INERT outcome |
| R2: Single-symbol-carrier risk (LDO 3.43× SSC ratio) | SSC-RISK gate evaluated at T9; B1 fails (TRUE) at 3.43× with LDO as carrier; band-tightened per /119 convention; LDO importance-PnL alignment cleaner than /122 dissociation | T9 SSC ratio 3.43× — band upper bound IS Δ ≤ +0.30 / OOS Δ ≤ +0.25; F4 falsifier pre-registered |
| R3: /119 C6 dissociation pattern recurrence (importance-strong + PnL-flat) | EDA T5 LDO rank 1/15 is the STRONGEST signal — if production LDO importance drops < 5/15, dissociation pattern triggers; F5 falsifier pre-registered (NEW for /123) | If production LDO rank < 5/15 AT FINAL IS MONTH AND LDO IS PnL Δ < +1pp, file DISSOCIATION-RECURRENT |
| R4: BCH structural drag (T7 BCH lift -0.0092) | BCH is BTC-fork-coupled, structurally insensitive to ETH cross-asset; this is the /122 controlling diagnostic at importance level + now confirmed at multivariate lift level; absorbed as portfolio cost | T7 BCH lift -0.0092 vs POOLED +0.0063 = drag absorbed by LDO/TRX positive contributions |
| R5: Per-symbol role-reversal vs T9 prediction (LDO-carrier becomes BCH-carrier or TRX-carrier) | EDA T7 per-symbol decomposition shows LDO +0.0215 clear winner; a role-reversal at production is a F4 falsifier match | F4 falsifier: LDO-NEGATIVE OR BCH-positive at production = Mode 3 PROMISING-PARTIAL |
| R6: Look-ahead via ETH klines or merge convention | `eth_rv_50 = rolling(50, min_periods=50).std()` of log returns is past-only by canonical pandas convention; ETH klines source `data/ETHUSDT/8h.csv` (the same fetcher convention as BCH/LDO/TRX); merge on `open_time` is the same convention as /122; unit test Change 5 verifies past-only on synthetic data | Test must PASS in CI before merge; Critic Check 1 (Look-Ahead) at Phase 7.5 |
| R7: Parquet column missing at runtime | Change 4 mandates parquet regeneration; runner has hard assertion (lgbm.py:582-589 verifies feature_columns); Change 6 integration test catches at runtime | n_features == 15 hard guard at runner pre-flight; eth_vs_sym_rv_50 PRESENT + eth_ret_3d ABSENT both asserted |
| R8: ETH klines stale or missing | Engineer pre-flight verifies `data/ETHUSDT/8h.csv` exists, has ≥ 6990 rows, last close_time within 16h | ETH data freshness mirrors BTC data freshness rule |
| R9: ETH klines cached at module load (per `_ETH_CACHE_V3` pattern) — risk of stale cache | The `_ETH_CACHE_V3` pattern mirrors `_BTC_CACHE_V3` in cross_btc_v3.py; module is re-imported per runner invocation; no inter-run cache persistence | Audit at Critic Check 1 |
| R10: Division-by-zero on degenerate sym_rv_50 | `eth_rv_50 / (range_realized_vol_50 + EPS)` with EPS=1e-12 guards | Engineer pre-flight: 0 inf/NaN values in `eth_vs_sym_rv_50` across all 3 symbol panels |
| R11: Algebraic correlation with `range_realized_vol_50` denominator (max pairwise IC 0.52) | This is STRUCTURAL by construction (B1 shares the sym_rv denominator); the EDA T2 confirms the joint R²=0.39 < 0.70 strict gate — the cross-asset NUMERATOR (eth_rv) is the new signal | T2 joint R² + pairwise IC matrix shows the cross-asset signal is captured by the ratio, not redundant with the denominator |

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

The /116 no_confirm RULE-layer primitive is ENABLED at baseline (`enable_no_confirm_exit=True`, `no_confirm_trigger_atr=0.50`, `no_confirm_k_candles=4`) per the /121 CONFIRMATION-MERGE — UNCHANGED at /123 per locked constraint.

No new risk primitive introduced at /123. The single axis is the new ETH-vs-sym vol-ratio feature column.

**Hard-merge gate implications for /132 CONFIRMATION** (if /123 lands PROMISING — modal probability 25% given GO-SSC-RISK EDA):

| Gate | /123 EDA estimate | /132 CONFIRMATION requirement |
|---|---|---|
| IS Sharpe > 1.0 | EDA models modal IS Sharpe ∈ [+1.01, +1.26] (EXPLORATION-mode) — at the floor | CONFIRMATION must clear at multi-seed mean |
| OOS Sharpe > 1.0 | EDA models modal OOS Sharpe ∈ [+0.75, +1.00] (EXPLORATION-mode); OOS Δ +0.05 vs /121 would clear the sacred dual-floor | CONFIRMATION must clear |
| OOS/IS ratio ≥ 0.5 | /121 has 0.74 buffer | needs multi-seed validation |
| Trade-rate ≥ 10/month OOS | /121 at 7.0/month — outstanding constraint; B1 not expected to improve | NEEDS structural axis at later cycle |
| Top-symbol ≤ 30% | /121 at BCH 95.76% — structural property of universe | unchanged |
| 10-seed validation | Single-seed at /123 EXPLORATION; full 10-seed at /132 | /132 |

The /123 brief does NOT promise merge-eligibility — it promises a single-axis EXPLORATION result that feeds into the cycle-7 axis-prior catalog. **The EDA's GO-SSC-RISK classification (+0.0063 POOLED lift above threshold; LDO rank 1/15 top in v3 EDA history; SSC TRUE 3.43×) means /123 is more likely than /122 to land PROMISING.** A NEGATIVE outcome would close the second of the four /119 §8.2 cross-asset axis candidates.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Seven modes pre-registered (Mode 1 = success; Modes 2-7 = failure/surprise variants). **First-match-wins**: classify by the FIRST mode whose condition matches the observed outcome.

| Mode | Condition (BEFORE checking the result) | Probability prior | Verdict if matches |
|---|---|---:|---|
| **Mode 1 (Modal success — EDA STRONG)** | IS Sharpe Δ ∈ [+0.05, +0.30] vs /121 EXPLORATION-mode estimate AND OOS Sharpe Δ ∈ [+0.00, +0.25] AND common-trade fraction with /121 ∈ [70%, 90%] AND production importance rank ≤ 8/15 on ≥ 2 symbols | **25%** | EXPLORATION-PROMISING (the ETH-realized-vol-cross-asset hypothesis surprised positively; /132 bundle candidate) |
| Mode 2 (Importance INERT at production — /082/122 pattern) | Production importance rank ≥ 14/15 on > 1 symbol AND POOLED lift estimate < +0.005 | **25%** | PROMISING-INERT or NEGATIVE-INERT (the /082/085/086/122 precedent; not bundled at /132) |
| Mode 3 (Per-sym role-reversal vs T9 prediction) | LDO IS PnL Δ NEGATIVE (vs T9 prediction LDO-carrier) AND BCH/TRX IS PnL Δ BOTH-positive | 10% | PROMISING-PARTIAL — the SSC inversion; axis-CLOSE recommendation |
| Mode 4 (Catastrophic regime artifact) | IS Sharpe Δ < −0.40 OR OOS Sharpe Δ < −0.30 vs /121 multi-seed baseline | 5% | EXPLORATION-NEGATIVE (the ETH-vol-cross-asset hypothesis falsified for eth_vs_sym_rv_50; axis CLOSED) |
| Mode 5 (Null at production — saturated pattern) | IS Sharpe Δ ∈ [−0.05, +0.05] AND common-trade fraction with /121 > 95% | 15% | NEGATIVE-no-effect (the /015 saturated-axis pattern; feature is fully INERT, drop) |
| Mode 6 (Suspicious-OOS-dominant) | OOS Sharpe Δ > +0.30 BUT IS Sharpe Δ < +0.05 (or worse) | 15% | SUSPICIOUS per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — /082/085/086/122 OOS-spike-artifact pattern |
| Mode 7 (Suspicious-IS-dominant / overfitting) | IS Sharpe Δ > +0.40 BUT OOS Sharpe Δ < −0.20 | 5% | SUSPICIOUS-IS-overfit (the /102 alpha032 pattern) |

**EDA Modal prediction**: Mode 1 (25%) — STRONGER than /122's 10% due to T7 5.25× higher + T5 LDO rank 1/15 + pairwise IC 8-26× cleaner. Mode 2 + Mode 5 + Mode 6 combined = 55% (the INERT-class / SUSPICIOUS-class outcomes still dominate the distribution given SSC-RISK TRUE and the /119 C6 dissociation pattern lurking). Mode 4 catastrophic at 5% — small but non-zero given the BCH structural drag.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

EXPLORATION-mode criteria (first-match-wins; the post-result classification the QR commits to BEFORE looking at the result).

**PER-CRITERION ANCHOR ANNOTATION** (per /122 Critic Rec 3 — the explicit anchor specification mandate):

### NEGATIVE criteria (any-of-the-below)

1. **NEGATIVE-catastrophic** (anchor: **/121 multi-seed CONFIRMATION public baseline**): IS Sharpe Δ < −0.40 vs /121 multi-seed (+1.3108) OR OOS Sharpe Δ < −0.30 vs /121 multi-seed (+0.9682). → file EXPLORATION-NEGATIVE catastrophic. Axis-CLOSE recommendation: the broader ETH-realized-vol-cross-asset hypothesis CLOSED at /123 (ETH-vol-cross-asset didn't lift in production); future cross-asset axes must use a STRUCTURALLY DIFFERENT primitive class (e.g., on-chain feeds, liquidations, basis from non-Binance venue).

2. **NEGATIVE-no-effect** (anchor: **/121 architecturally-adjusted EXPLORATION-mode estimate** for IS Δ band; **/121 multi-seed baseline** for common-trade fraction): IS Sharpe Δ ∈ [−0.05, +0.05] vs EXPLORATION estimate (+1.06) AND common-trade fraction with /121 baseline trades > 95% AND production importance rank ≥ 14/15 on all 3 symbols → file EXPLORATION-NEGATIVE no-effect (the /015 saturated-axis pattern).

3. **NEGATIVE-INERT** (anchor: **/121 architecturally-adjusted EXPLORATION-mode estimate**): production importance rank ≥ 14/15 on > 1 symbol AND POOLED lift estimate < +0.005 AND IS Sharpe Δ < +0.05 vs EXPLORATION estimate (+1.06) → file EXPLORATION-NEGATIVE-INERT (the /082/085/086/122 precedent).

4. **NEGATIVE-clean** (anchor: **/121 architecturally-adjusted EXPLORATION-mode estimate**): IS Sharpe Δ < +0.05 AND OOS Sharpe Δ < +0.05 (both vs EXPLORATION estimate IS +1.06 / OOS +0.85) AND none of Modes 1-7 match → file EXPLORATION-NEGATIVE clean.

### PROMISING criteria (all-of-the-below)

5. **PROMISING-strong** (anchor: **/121 architecturally-adjusted EXPLORATION-mode estimate**): IS Sharpe Δ ≥ +0.10 vs EXPLORATION estimate (+1.06) AND OOS Sharpe Δ ≥ +0.10 vs EXPLORATION estimate (+0.85) AND production importance rank ≤ 8/15 on ≥ 2 symbols AND common-trade fraction ∈ [70%, 90%] AND no Mode 3/4 falsifier → file EXPLORATION-PROMISING strong. Bundle candidate for /132 CONFIRMATION.

6. **PROMISING-partial** (anchor: **/121 multi-seed baseline** for per-symbol PnL Δ — uses absolute PnL deltas not relative): Only 1 of 3 symbols IS-positive AND that symbol IS PnL Δ > +3pp vs /121 multi-seed baseline AND another symbol IS PnL Δ < −1pp → file EXPLORATION-PROMISING-PARTIAL. /132 bundles only if a per-symbol gate is also tested at a future iteration. The LDO-carrier T9 prediction is the modal pattern for this — LDO-only positive at production fits this branch.

7. **PROMISING-INERT-RISK** (anchor: **/121 architecturally-adjusted EXPLORATION-mode estimate** for IS Δ; T5 importance rank is anchor-independent): T5 importance rank ≥ 14/15 on > 1 symbol AND POOLED lift estimate < +0.005 at production AND IS Sharpe Δ ∈ [+0.05, +0.20] vs EXPLORATION estimate (+1.06) → file EXPLORATION-PROMISING-INERT-RISK (the /085 pattern). Not bundled at /132.

8. **SUSPICIOUS** (anchor: **/121 architecturally-adjusted EXPLORATION-mode estimate**): OOS Sharpe Δ > +0.30 vs EXPLORATION estimate (+0.85) BUT IS Sharpe Δ ∈ [−0.10, +0.05] vs EXPLORATION estimate (+1.06) → SUSPICIOUS-OOS-DOMINANT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. The /082/085/086/122 OOS-spike artifact pattern.

### Anchor disambiguation summary table

| Criterion | IS Δ anchor | OOS Δ anchor | Other anchor inputs |
|---|---|---|---|
| 1 NEGATIVE-catastrophic | **/121 multi-seed** | **/121 multi-seed** | — |
| 2 NEGATIVE-no-effect | /121 EXPLORATION est. | n/a | /121 multi-seed for trade-roster diff |
| 3 NEGATIVE-INERT | /121 EXPLORATION est. | n/a | T5 importance rank (anchor-independent) |
| 4 NEGATIVE-clean | /121 EXPLORATION est. | /121 EXPLORATION est. | — |
| 5 PROMISING-strong | /121 EXPLORATION est. | /121 EXPLORATION est. | T5 importance rank, common-trade fraction |
| 6 PROMISING-partial | **/121 multi-seed** (PnL Δ) | n/a | per-symbol PnL absolute |
| 7 PROMISING-INERT-RISK | /121 EXPLORATION est. | n/a | T5 importance rank |
| 8 SUSPICIOUS | /121 EXPLORATION est. | /121 EXPLORATION est. | — |

The anchor specification is COMPLETE per /122 Critic Rec 3.

---

## Section 9 — Library Stack Declaration

**No new library dependencies** — `eth_vs_sym_rv_50` is built from existing primitives (`close` column of `data/ETHUSDT/8h.csv` + the panel's existing `range_realized_vol_50` column) using numpy `log`, pandas `rolling`, and element-wise division. All required functions are already imported in `cross_btc_v3.py`.

**Library inventory** (verified at /123):
- `lightgbm == 4.6.0` (unchanged from /122)
- `numpy >= 2.0` (unchanged)
- `pandas >= 2.2` (unchanged)
- `scikit-learn` (used only in EDA, not in production runner)
- `statsmodels` (used only in EDA for ADF audit)
- No version change to any production library

**Adversarial integration test** (per `feedback_v3_methodology_axis_integration_test.md`): the `Change 6` integration test asserts:
- `V3_FEATURE_COLUMNS_TOP_N` includes `"eth_vs_sym_rv_50"` at runtime (the 15th feature)
- `V3_FEATURE_COLUMNS_TOP_N` DOES NOT include `"eth_ret_3d"` (closed at /122)
- `len(V3_FEATURE_COLUMNS) == 15`
- The parquet for BCH/LDO/TRX has the `eth_vs_sym_rv_50` column non-NaN on the LAST 100 IS rows
- Runner pre-flight n_features guard fires `n == 15`
- The feature value from `add_cross_btc_v3_features()` for 10 random IS rows matches the EDA's stand-alone computation (numerical reconciliation: `analysis/iteration_v3-123/_shared.py`'s `_attach_eth_vol_ratio_features` produces the SAME values as the production `add_cross_btc_v3_features`)
- The `compute_eth_vs_sym_rv_50_past_only` unit test PASSES (past-only invariant on synthetic data; the Change 5 test)

These 7 assertions cover the end-to-end integration boundary (ETH CSV loader → cross_btc_v3 merge → runner → strategy → model fit) at the runtime call-site, not just the unit-level math.

---

## Section 10 — QR Audit Trail

**Provenance of the /123 axis selection**:

1. **/122 closeout Critic FINAL Recommendation 1** (`briefs-v3/iteration_v3-122/review.md` Recommendation 1): "eth_ret_3d primitive CLOSED at /122; the broader ETH-OHLCV-cross-asset hypothesis is NOT auto-closed. /123 may test an ETH-derived primitive that is NOT spanned by `vwap_dev_20` or `regime_momentum_signed_5d` (e.g., ETH realized-volatility regime classifier, ETH cross-sectional rank vs alt cohort) — but EDA T2 R² against the FULL 15-feature anchor must clear the gate **AND** EDA must show pairwise |IC| < 0.40 with `vwap_dev_20` and `regime_momentum_signed_5d` specifically. Joint-R² is insufficient diagnostic for ETH-derived primitives." → /123 implements exactly this: ETH realized-vol-regime ratio + pairwise IC strict gate.

2. **/122 closeout Critic FINAL Recommendation 3** ("Pre-register dual-anchor disambiguation explicitly in /123 brief Section 8"): The /122 brief declared dual-anchor but Section 8 criteria 2-8 did NOT explicitly specify which anchor applies to each. /123 Section 8 has the FULL anchor disambiguation table.

3. **User directive 2026-05-20 in /123 prompt**: pre-selected axis B1 = `eth_realized_vol_50 / sym_realized_vol_50`. QR honors with EDA-validated sister catalog (B1a, B1b, B1c) per the QR mandate to evaluate sister candidates before committing to the primary.

4. **/123 QR axis adjudication (this brief)**:
   - **/122 axis-1 first-moment ETH primitive** CLOSED per Critic Rec 1.
   - **Cross-asset/external feeds axis (BASELINE_V3 priority #1)** stays available with the non-IC-spanned + pairwise-IC < 0.40 discipline.
   - **Sub-axis B1** (eth_realized_vol_50 / sym_realized_vol_50) selected per the QR prompt's pre-selection + EDA validation.
   - 4 sister candidates evaluated; the EDA decision was driven by:
     - B1 (PRIMARY): GO-SSC-RISK — T7 +0.0063 (5.25× /122); T5 LDO rank 1/15; pairwise IC 0.069 / 0.021 (8-26× /122 reduction)
     - B1a (log W=50): GO-SSC-RISK — sister-equivalent (T7 +0.0059)
     - B1c (W=100): MARGINAL but DISQUALIFIED (T8 ADF FAIL on all 3 symbols, p≈0.12-0.14)
     - B1b (W=25): REJECT (T7 NEGATIVE lift -0.0029)
   - B1 selected as PRIMARY per the user's pre-selection AND the EDA confirms it as the strongest signal (top-1 importance on LDO + 2.1× threshold POOLED lift + cleanest pairwise IC).

5. **EDA artifacts committed BEFORE this brief**: `analysis/iteration_v3-123/` (SHA `dbc2993`), 13 files including `_shared.py`, `eth_vol_ratio_screen.py`, `eth_adf_audit.py`, 9 CSV result tables, and `synthesis.md`. Every script asserts `close_time < OOS_CUTOFF_MS = 1742774400000`.

6. **Cycle-7 cadence accounting** (per `feedback_v3_strict_10_to_1_cadence.md`): /123 is slot 2 of 10. Subsequent slots /124-/131 + CONFIRMATION /132 follow the strict 10:1 ratio.

7. **Dual-anchor methodology** (Section 4.1 + Section 8): the architecturally-adjusted /121 EXPLORATION-mode estimate (IS +1.06 / OOS +0.85) is used for the falsifier band reference because /123 runs at 3-seed EXPLORATION mode. The /121 multi-seed CONFIRMATION baseline (IS +1.3108 / OOS +0.9682) is the public anchor for NEGATIVE-catastrophic threshold and headline reporting. Section 8's per-criterion anchor annotation table makes the assignment EXPLICIT per /122 Critic Rec 3.

8. **The honest pre-registration**: the EDA's modal verdict is **Mode 1 (Modal success) at 25% probability** — STRONGER than /122's 10% — but Mode 2/Mode 5/Mode 6 INERT-class / SUSPICIOUS-class outcomes combined at 55% still dominate the distribution. The PRIME DIRECTIVE runs the backtest regardless; the EDA's GO-SSC-RISK classification (vs /122's MARGINAL) reflects a structurally STRONGER signal but not a guarantee of production lift. A NEGATIVE outcome would close the second of the four /119 §8.2 cross-asset axis candidates.

9. **The /122 SSC-RISK convention applied**: B1's SSC ratio 3.43× (LDO carrier) triggers band-tightening per /119 convention — upper bound IS Δ ≤ +0.30, OOS Δ ≤ +0.25. The LDO carrier identity is DIFFERENT from /122 (TRX) — and the importance-PnL alignment (LDO is top-1 in T5 importance AND T7 carrier) is CLEANER than /122's dissociation. F5 falsifier pre-registered for the /119 C6 dissociation pattern recurrence.
