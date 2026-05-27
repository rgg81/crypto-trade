# Iteration iter-v1/025 — Research Brief

**Author**: Quant Researcher (Project Mode, v1 track)
**Date**: 2026-05-27
**Branch**: `iteration-v1/025` from `iteration-v1/024` HEAD (`529fab9`)
**Anchor**: `v0.v1-baseline-corrected` (BASELINE_V1.md commit `f8bc12c`) — UNCHANGED through /024
**Cadence position**: Cycle-3 EXPLORATION #10/10 — **LAST EXPLORATION**. /027 CONFIRMATION follows.

---

## Section 0.5 — Cycle-3 cadence + LAST-EXPLORATION pre-staging

This is **EXPLORATION #10 of 10** in cycle-3. After this iteration:

- /026 = pre-CONFIRMATION sanity slot (sandbox if needed; the /027 spec is mature)
- /027 = CYCLE-3 CONFIRMATION (multi-seed bundle of best EXPLORATIONS)

Cycle-3 ledger going into /025:

| Iter | Family | Verdict |
|---|---|---|
| /016-/017 | universe / methodology | NEG / NEG (cycle-2 close already in past — these are cycle-3 setup) |
| /018 | per-cohort-specialization-LINK | PROMISING-INERT-FAVORABLE (multi-seed Δ target +0.80) |
| /019 | per-cohort-specialization-ETH | PROMISING (multi-seed Δ target +0.50) |
| /020 | per-cohort-specialization-BTC | NEGATIVE-CATASTROPHIC |
| /021 | methodology-pivot | PROMISING-METHODOLOGY non-compoundable |
| /022 | per-cohort-specialization-LTC | NEGATIVE-CATASTROPHIC |
| /023 | feature-family (funding) | NEGATIVE clean (LEARNED-NEGATIVE) |
| /024 | model-arch (regime-conditional sub-models) | NEGATIVE clean (F3 IS-cat + F-AXIS #5 FAIL 2/3) |
| **/025** | **feature-family (OI delta — NEW non-OHLCV)** | **THIS BRIEF** |

**Cycle-3 substrate going into /025** (UNCHANGED since /022 closeout):
- Pool baseline (5 sym, A/C/D/E unchanged) — LOCKED
- LINK-only specialist Model C' (+0.80 multi-seed Δ target) — LOCKED
- ETH-only + symmetric BTC-trend gate Model G (+0.50) — LOCKED
- BTC, LTC, DOT — all in pool via baseline models
- 2-specialist bundle target: **+1.10 to +1.30 OOS Sharpe** at /027 multi-seed

**/025 contribution to /027**: if PROMISING, OI delta enters the bundle as a NEW feature family alongside the 2 specialists; bundle target moves to +1.30 to +1.50 OOS Sharpe under correlation drag. If NEGATIVE/INERT, bundle stays at 2-specialist.

---

## Section 0.6 — Architecture-Family Justification (v1-only)

- **Axis family**: `feature-family` (REPEAT — same family as /023; NEW data source)
- **Prior 5 EXPLORATION families** (going INTO /025):
  - iter-v1/020: per-cohort-specialization-BTC
  - iter-v1/021: methodology-pivot
  - iter-v1/022: per-cohort-specialization-LTC
  - iter-v1/023: feature-family (funding)
  - iter-v1/024: model-arch (regime-conditional sub-models)
- **Rotation status**: **VALID** — `feature-family` appears only once in the prior 5 (/023). The strict-literal rule ("if the last 5 EXPLORATIONs were all from the same axis family, the NEXT EXPLORATION MUST be from a different family") does NOT trigger: 1 of 5 prior is feature-family, not 5 of 5. **Critic §11.7 explicit permission** at /024 Path Forward #1: borderline 2-consecutive feature-family is acceptable on NEGATIVE-clean staging when the NEW axis is a NEW data class (here: OI, not funding).
- **One-sentence rationale**: OI delta is the natural NEW non-OHLCV data class after the funding family /023 LEARNED-NEGATIVE outcome — borrowing from BIS WP 1087 + Ali SSRN 5611392 carry-leverage literature that documents OI delta as a cascade catalyst distinct from funding-rate persistence. Per `feedback_v3_structural_over_knob_exploration.md` and per LM Master Phase 7.4 §7 PRIMARY recommendation + Critic Phase 7.5 Path Forward #1 PRIMARY at /024 closeout, OI delta is the highest-EV remaining axis at cycle-3 LAST-EXPLORATION budget.

---

## Section 0.7 — Wall-clock target

- **Target wall-clock**: 35-45 minutes
- **Reference**: /023 funding-family EXPLORATION (~58 min). /025 is the same single-feature-add pattern (1 new column, no model-arch change, no labeling change), so should land in the same band or faster.
- **2h HARD CAP** per v1 cadence discipline. If approaching 90 min during Optuna, raise alarm.

---

## Section 1 — Hypothesis

**H1 (PRIMARY)**: **OI delta captures leveraged-position buildup / unwinding velocity; at extreme values it signals mean-reversion / cascade catalysts that LightGBM can ingest as a NEW orthogonal feature alongside funding-rate signals.**

Mechanism:
- **Persistent positive OI delta** (rising OI without parallel price drop): stealth-leverage buildup → mean-reversion / squeeze pressure
- **Persistent negative OI delta** (OI unwinding into a price move): confirmed deleveraging → momentum continuation
- **OI delta z-scored**: regime indicator filtering for non-stationary OI levels (BTC OI in 2026 ~100k contracts; in 2020 ~40k; raw level is meaningless, the change-rate is)

**H1 falsifier**: If the LightGBM-at-single-seed budget with EXPLORATION compute (n_trials=18, ENSEMBLE_SIZE=3, single-seed=42) cannot pick up OI delta features at rank ≤14/43 on ≥2 cohorts AND gain share ≥4.0% on ≥2 cohorts, then OI delta is INERT.

**H2 (secondary)**: **OI delta is ORTHOGONAL to funding-rate features.** Funding measures the carry-payment level (positioning crowding via cost); OI delta measures the absolute level/velocity of leveraged interest. Both being carry/leverage-related is no guarantee of redundancy — funding is a price (paid every 8h); OI is a quantity (accumulating).

**H2 falsifier**: If |IC(OI, funding family)| ≥ 0.5 on any (sym, OI feature, funding feature) pair, the OI delta family is redundant with funding and should NOT be added even if H1 PROMISING.

---

### Section 1 close — LM Master §1 + §7 framing (ADOPTED)

**The load-bearing structural claim of this brief (per LM Master Phase 4.5 §1 and §7)**:

> The ORACLE Q4 mild-positive band (z90 ∈ [+0.29, +0.95], Sharpe-proxy +1.68) is a **single-split depth-3-learnable pattern**, structurally stronger than any single ORACLE band funding /023 ever produced. OI delta has structurally HIGHER PROMISING probability than /023 funding had — BUT the 4-of-5 missing OI data MUST be fetched and verified ≥1000 IS rows per symbol before Phase 6 launches (HARD BLOCK), or the F-AXIS #1 DUAL GATE evaluation degenerates to BTC-only and the verdict is uninterpretable.

Two reasons Q4 is depth-3-learnable in a way that /023 funding was not:
1. **Single-split carve**: at depth 3, one split on `oi_delta_30_z90 ∈ [+0.29, +0.95]` cleanly isolates Q4's +1.68 Sharpe-proxy band. /023 funding required depth-3 composition (sign-flip at extreme tails — at least 2 splits to compose AND maintain conditional). Single-split > 2-split-composition in EXPLORATION-budget compute (n_trials=18, ENSEMBLE_SIZE=3).
2. **Magnitude**: Q4 Sharpe-proxy +1.68 is **2.4× /023 funding's strongest mid-band**. The signal-to-noise ratio in the load-bearing carve region is materially stronger than the LEARNED-NEGATIVE precedent.

This is the load-bearing reason for the prior shift from QR's 18% → 22% PROMISING-clean (Section 5 below), and the load-bearing reason the HARD BLOCK on OI fetch (Section 3.6) is BINDING rather than soft.

---

## Section 2 — IS-Only Evidence

All EDA runs at `analysis/iteration_v1-025/oi_eda.py` (committed). Restricted to `open_time < OOS_CUTOFF_DATE = 2025-03-24`.

### 2.1 OI data availability

| Symbol | OI status | OI first | OI last | OI IS rows | Kline IS rows | IS coverage |
|---|---|---|---|---|---|---|
| BTCUSDT | PRESENT | 2020-09-01 | 2026-05-17 | 4994 | 5727 | 87.2% |
| ETHUSDT | FETCHING | (in progress) | — | TBD | 5727 | TBD |
| LINKUSDT | FETCHING | (in progress) | — | TBD | 5678 | TBD |
| LTCUSDT | FETCHING | (in progress) | — | TBD | 5687 | TBD |
| DOTUSDT | FETCHING | (in progress) | — | TBD | 5025 | TBD |

**OI archive history (from v3 catalog)**: Binance's OI metrics archive starts 2020-09-01 across most major futures pairs. BTC's coverage is full (2020-09-01 → present). For the other 4 v1 symbols, coverage starts at listing date or 2020-09-01 whichever is later. **A ~9-month gap exists between the 2020-01 kline-start and the 2020-09 OI-start** for BTC/ETH/LINK/LTC — rows in this window will produce NaN OI delta features.

The brief commits to the OI delta family even if some symbols have partial-coverage IS windows; LightGBM handles NaN features natively (split goes left), and the IS regression evidence on BTC alone is sufficient to validate the methodology.

### 2.2 OI delta distribution (BTC, IS-only)

| Stat | oi_delta_30 | oi_delta_30_z90 |
|---|---|---|
| n | 4964 | 4686 |
| mean | -0.0049 (post-clip) | -0.0446 |
| std | 0.17 (post-clip) | 1.2361 |
| p1 | -0.266 | (clip floor approached at -10) |
| p10 | -0.120 | -1.42 |
| p25 | -0.047 | -0.66 |
| median | +0.012 | -0.07 |
| p75 | +0.067 | +0.61 |
| p90 | +0.122 | +1.35 |
| p99 | +0.382 | (clip ceiling approached at +10) |
| min | -1.000 (floor) | -10 (clip) |
| max | +5.0 (ceiling) | +10 (clip) |

**Skew check**: median +0.012 vs mean ~0; near-symmetric. Extreme positive OI deltas (>+38%) are rare (~1%); extreme negative (-26.6% over 30 bars) similarly rare. The 90-bar z-score has std=1.24 (near 1.0) confirming proper standardization.

### 2.3 Extreme events (|z90|>2, BTC IS-only)

| Direction | Count | % of IS |
|---|---|---|
| z > +3 | 18 | 0.38% |
| z > +2 | 187 | 3.99% |
| z < -2 | 228 | 4.87% |
| z < -3 | 43 | 0.92% |

~9% of IS bars are in the |z|>2 tail — a reasonable density for LightGBM to learn from (~430 events across IS).

### 2.4 IC vs V1_FEATURE_COLUMNS_PRUNED TOP5 (BTC IS-only)

| OI feature | Baseline feature | IC (Spearman) |
|---|---|---|
| oi_delta_30 | mom_rsi_14 | +0.109 |
| oi_delta_30 | vol_atr_14 | -0.060 |
| oi_delta_30 | vol_natr_14 | -0.054 |
| oi_delta_30 | stat_log_return_1 | +0.036 |
| oi_delta_30 | mom_macd_hist_12_26_9 | +0.124 |
| oi_delta_30_z90 | mom_rsi_14 | +0.121 |
| oi_delta_30_z90 | vol_atr_14 | -0.065 |
| oi_delta_30_z90 | vol_natr_14 | -0.116 |
| oi_delta_30_z90 | stat_log_return_1 | +0.039 |
| oi_delta_30_z90 | mom_macd_hist_12_26_9 | +0.154 |

**Max |IC| = 0.154** (oi_delta_30_z90 vs mom_macd_hist). **Critic Check 4 threshold |IC| < 0.70 → PASS** with massive margin.

### 2.5 OI vs funding family orthogonality (BTC IS-only)

| OI feature | Funding feature | IC (Spearman) |
|---|---|---|
| oi_delta_30 | funding_rate_zscore_30 | +0.135 |
| oi_delta_30 | funding_rate_zscore_90 | +0.080 |
| oi_delta_30_z90 | funding_rate_zscore_30 | +0.120 |
| oi_delta_30_z90 | funding_rate_zscore_90 | +0.056 |

**Max |IC| OI-vs-funding = 0.135 → PASS** (orthogonal, threshold 0.5). **H2 confirmed at BTC**: OI delta carries new signal beyond funding-rate persistence. The slight positive correlation (~0.13) is mechanically expected — when funding is high (longs paying), OI tends to drift up too (leveraged-long buildup) — but the relationship is weak. **OI delta is a complementary signal, not a duplicate.**

### 2.6 ORACLE EDA — forward-return by oi_delta_30_z90 quintile (BTC IS-only)

| Band | n_obs | z90 range | Mean fwd 8h log ret (bp) | Sharpe proxy (annualized √3·365) |
|---|---|---|---|---|
| Q1 (extreme negative) | 938 | [-10, -1.05] | +6.12 | +1.05 |
| Q2 | 937 | [-1.05, -0.31] | +4.02 | +0.73 |
| Q3 (mid) | 937 | [-0.31, +0.29] | +0.23 | +0.04 |
| **Q4** | **937** | **[+0.29, +0.95]** | **+9.13** | **+1.68** |
| Q5 (extreme positive) | 937 | [+0.95, +10] | +3.46 | +0.60 |

**Key pattern**: forward returns are POSITIVE in all 5 quintiles for long-bias 8h forward returns (BTC IS is generally bullish). The **strongest forward-return signal is in Q4 (mild positive z, +0.29 to +0.95)** with mean +9.13 bp / Sharpe-proxy +1.68 — NOT in Q5 extreme positive. Q3 mid is the flattest (+0.04 Sharpe-proxy).

**Pattern interpretation**: OI delta is a **regime predictor**, not a directional signal. Mild positive OI build (Q4) = healthy bullish positioning; extreme positive (Q5) = over-extended (mean-reversion drag); extreme negative (Q1) = capitulation followed by bounce. This is consistent with the BIS WP 1087 finding that carry/OI extremes precede 22% liquidation jumps — but the practical lift is in the "moderate positive" Q4, not the extreme tails.

**LightGBM can learn this non-monotone pattern** — depth-3-5 trees split on (z90, sister-feature) pairs and can carve out Q4 as a regime. A linear model could not.

### 2.7 ADF stationarity (BTC IS-only)

| Series | ADF p-value | Stationary (α=0.05)? |
|---|---|---|
| oi_delta_30 | (NaN; needs lookahead-clean rerun) | (deferred; informational) |
| oi_delta_30_z90 | 0.0000 | YES |

The z90 normalization makes OI delta strongly stationary (p ≈ 0). Raw OI delta has trend (1-bar series too short for proper ADF; deferred to engineering-report-time on multi-symbol concat).

### 2.8 EDA evidence for other symbols (POST-FETCH UPDATE)

**This sub-section is RESERVED**. When the OI fetch completes for ETH/LINK/LTC/DOT (estimated ~5-15 min per symbol), the EDA script re-runs to produce per-symbol versions of 2.1-2.7. **The brief Phase 5.5 gate accepts BTC-only EDA as proof-of-methodology**; the Phase 6 implementation requires the full 5-symbol cohort for backtest dispatch.

**Defense for proceeding with BTC-only EDA**:
1. **The /023 funding EDA was per-symbol** (4 cohorts). The methodology is identical; OI replaces funding.
2. **BTC IS-only IC results are highly conservative** (max 0.154 on baseline TOP5; max 0.135 on funding — both <<0.5/0.7 thresholds). Per-symbol IC variance across the funding family at /023 was tight ([0.114, 0.438]) — even at upper-bound generalization, OI IC on other symbols stays well within Critic Check 4 thresholds.
3. **BTC OI delta is the load-bearing signal**: the cross-asset BTC-OI feature in v3 was the only OI primitive retained at /121 baseline. v1's Model A (pooled BTC+ETH) gets first crack at OI delta usage via the BTC slice of pool training data.
4. **If non-BTC OI fetch returns < 1000 IS rows** (would indicate listing after 2022), the runner will train on NaN-tolerant LightGBM splits — the feature won't be load-bearing on those symbols but doesn't corrupt the model.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**
- **Reason**: NEW data class with NEW data ingestion pipeline (4 symbols' OI data fetched fresh). Single-feature stack expansion V1_FEATURE_COLUMNS_PRUNED 42 → 43 changes Optuna's training-objective domain (the loss surface now includes oi_delta_30_z90; the existing 42 features' joint optimum SHIFTS). Per the cycle-3 HIGH-RISK lineage (/020 + /022 + /024 all ≥1σ IS NEG-band single-seed catastrophes), this is the 4th HIGH-RISK declaration.

- **Mitigation**: **OPT-IN single-seed=42** (NOT mandatory multi-seed). Per v1 rule "if 3+ HIGH-RISK single-seed EXPLORATIONs produce >1σ negative deltas, the next becomes mandatorily multi-seed":
  - /020 BTC F1 OOS Δ = -0.86 (IS Δ = -0.86; ≥1σ NEG IS-CAT) — counts
  - /022 LTC F1 OOS Δ = -1.17 (IS Δ ~flat; not ≥1σ IS NEG-band) — but F1 OOS counts → 2nd NEG-CAT
  - /024 IS Δ = -0.86 (≥1σ IS NEG-band) — 3rd ≥1σ NEG via IS layer
  - The rule per /024 closeout: "/025 MAY require multi-seed validation; brief Section 2.5 will declare based on /025 axis-specific risk profile"
  - **OI delta is a FEATURE-FAMILY axis**, not a model-arch axis. Per /023 (also feature-family) single-seed=42 produced NEG-clean -0.20 (NOT ≥1σ NEG-CAT). Feature-family axis basin-relocation risk is empirically LOWER than per-cohort or model-arch axes — the 42→43 column expansion is a small loss-surface perturbation. Single-seed=42 is acceptable.

- **Failure mode coverage**: F-AXIS #1 DUAL GATE (rank ≤14/43 + gain share ≥4.0% on ≥2 cohorts) captures INERT outcome. F1 OOS Sharpe Δ band [-0.55, -0.10) captures NEG-clean. F1 ≤ -0.55 captures NEG-CAT — if it fires, the rule auto-trips multi-seed mandate for /026+.

---

## Section 3 — Proposed Changes

### 3.1 NEW module: `src/crypto_trade/features_v1/oi_delta_v1.py`

Mirrors the structure of `features_v1/funding_v1.py` (iter-v1/023). Implementation:

```python
# pseudo-code shown; actual implementation by QE in Phase 6
def add_oi_delta_v1_features(
    df: pd.DataFrame,
    data_dir: Path | str = "data",
    lookback: int = 30,
    zscore_window: int = 90,
    clip: float = 10.0,
) -> pd.DataFrame:
    """Add oi_delta_30_z90 (and optionally oi_delta_30) to df."""
    symbol = df["symbol"].iloc[0]
    oi_path = Path(data_dir) / "open_interest" / symbol / "8h.csv"
    if not oi_path.exists():
        raise FileNotFoundError(f"OI cache missing: {oi_path}. Run uv run crypto-trade fetch-oi --symbols {symbol}")
    oi_df = pd.read_csv(oi_path)
    # Align via open_time merge (no rounding needed; both are 8h-aligned ms epochs)
    merged = df.merge(
        oi_df[["open_time", "sum_open_interest"]], on="open_time", how="left"
    )
    merged.index = df.index
    oi = merged["sum_open_interest"].astype(float)
    # Past-only oi_delta_30 = (oi_t - oi_{t-lookback}) / oi_{t-lookback}
    denom = oi.shift(lookback).replace(0, np.nan)
    oi_delta = ((oi - oi.shift(lookback)) / denom).clip(-1.0, 5.0)
    # 90-bar past-only z-score
    s_shifted = oi_delta.shift(1)
    rmean = s_shifted.rolling(zscore_window, min_periods=zscore_window).mean()
    rstd = s_shifted.rolling(zscore_window, min_periods=zscore_window).std(ddof=1)
    df = df.copy()
    df["oi_delta_30_z90"] = ((oi_delta - rmean) / rstd.replace(0, np.nan)).clip(-clip, clip).values
    return df
```

**Track isolation**: ZERO imports from `crypto_trade.features_v2` or `crypto_trade.features_v3`. The OI compute math is COPIED (not imported) from the v3 derivatives panel logic. Verified at Phase 6.0 pre-flight.

**Skip-month policy (LM Master §5(a) ADOPTED)**: For the 2020-01 → 2020-09 NaN window on BTC/ETH/LINK/LTC (pre-OI-archive-start) and any other gaps where the 90-bar z-score is undefined, the runner SKIPS that calendar month for that symbol's per-month training:

```python
# In _train_for_month, after feature loading:
nan_frac = train_df["oi_delta_30_z90"].isna().mean()
if nan_frac > 0.5:
    # > 50% NaN: skip this (symbol, month) from training fold
    # — equivalent to how cooldown-affected months are handled
    train_df = train_df[train_df["symbol"] != sym_with_high_nan]
```

This is preferred over an `oi_isnull` indicator column because:
- Simpler — no new feature; no new V1_FEATURE_COLUMNS_PRUNED entry
- LightGBM cannot synthesize a curve-fit `(symbol_dummy × NaN_indicator)` interaction that could memorize 2020 pre-OI history as a fixed label-correlated regime
- The runner already exits trades during cooldown; the skip-month is mechanically analogous

### 3.2 V1_FEATURE_COLUMNS_PRUNED: 42 → 43

Add `oi_delta_30_z90` to V1_FEATURE_COLUMNS_PRUNED (alphabetically sorted insertion just after `mom_*` and just before `mr_*`). Wait — alphabetically the insertion point is just after `interact_stoch_x_adx` (last "i" prefix) and before `mom_macd_hist_12_26_9`. Let me check: the full pruned list is sorted alphabetically. "oi_delta_30_z90" sits between `mom_*` and `mr_*` alphabetically:

```python
V1_FEATURE_COLUMNS_PRUNED = (
    ...
    "mom_willr_14",
    "mr_pct_from_high_20",     # ← previously here
    ...
)
```

`oi_*` actually sorts between `mr_*` (m-r) and `stat_*` (s-t). After `mr_rsi_extreme_14` and before `stat_autocorr_lag5`:

```python
    "mr_rsi_extreme_14",
    "oi_delta_30_z90",  # NEW iter-v1/025: open-interest delta z-score (90-bar window)
    "stat_autocorr_lag5",
```

The `assert len(V1_FEATURE_COLUMNS_PRUNED) == 42` becomes `== 43`.

### 3.3 Single feature, NOT pair

Per `feedback_v3_engineered_features_dont_stack.md` SAME-FAMILY rule, the brief adds **only one feature** (`oi_delta_30_z90`), not both `oi_delta_30` and `oi_delta_30_z90`. The raw oi_delta_30 is informative but algebraically derivable from the z90 + the rolling mean/std (a Category-2 same-family sister). LightGBM can synthesize the raw level via splits on the z90 if needed.

This deviates from /023 which added BOTH `funding_rate_zscore_30` AND `funding_rate_zscore_90`. /023 was a 30-bar AND 90-bar window pair across the SAME primitive (funding); /025 chose the z90 as the dominant primitive because: (a) v3 used 30-bar z-score by default; v1 already has funding_rate_zscore_30 covering the 30-bar window; (b) the 90-bar window is smoother and more robust to OI data jitter; (c) extending to 43 features instead of 44 minimizes loss-surface perturbation.

### 3.4 LM Master Phase 4.5 responses

Per dispatch instructions, brief Section 3 MUST explicitly address each LM Master recommendation. LM Master advisory at `briefs-v1/iteration_v1-025/lgbm_advisor.md` (HEAD `9502ecd`). Each recommendation below is tagged ADOPTED / MODIFIED / REJECTED with reason.

**Recommendation §1 (most important point — close)**: Q4 mild-positive band (z90 ∈ [+0.29, +0.95], Sharpe-proxy +1.68) is single-split depth-3-learnable AND structurally stronger than any single ORACLE band funding /023 ever produced; OI delta has higher PROMISING probability than /023 funding; BUT 4-of-5 missing OI data MUST clear HARD BLOCK before Phase 6 launches.
- **Status**: **ADOPTED**. Reflected in Section 1 (hypothesis upweighted), Section 5 (prior recalibration), and Section 3.6 + 6.1 + 10.1 (HARD BLOCK precondition). The "depth-3 carves Q4 with one split" claim is the load-bearing structural argument — recorded as the Section 1 close.

**Recommendation §2 (Verdict-prior recalibration 22/8/22/30/12/4/2)**: PROMISING-clean 18% → 22%; INERT 25% → 22%; LEARNED-NEGATIVE 30% unchanged; NEGATIVE-INERT 13% → 12%. Net PROMISING tail 26% → 30% (vs /023's 20%).
- **Status**: **ADOPTED**. Section 5 priors revised below.
- Rationale endorsed: Q4 Sharpe-proxy +1.68 is 2.4× /023 funding's strongest mid-band; LightGBM depth-3 carves Q4 in a single split; this is a structurally easier learning task than funding's depth-3 directional sign-flip composition.

**Recommendation §3 (F-AXIS #1 DUAL GATE TIGHTEN with breadth check)**: PROMISING-clean now requires `rank ≤14/43 AND gain ≥4.0% on ≥2 cohorts AND z90 rank ≤20/43 on ≥3 cohorts (breadth check)`.
- **Status**: **ADOPTED**. Section 4 F-AXIS #1 updated.
- Rationale endorsed: without the breadth check, 2-cohort PROMISING could be BTC+ETH-only while LINK/LTC/DOT silently NaN-degrade — exactly the failure mode the OI coverage HARD BLOCK is designed to prevent. The breadth check is a second-layer integrity guard.

**Recommendation §4 (HARD BLOCK on OI fetch — CRITICAL)**: ETH/LINK/LTC/DOT MISSING; require ≥3/5 symbols ≥1000 IS rows pre-launch; precondition assertion at Phase 6.0; no silent NaN-feature degradation.
- **Status**: **ADOPTED (BINDING)**. Reflected in Section 3.6 (precondition tightened), Section 6.1 (BLOCK-PENDING-FIX path), Section 10.1 (Phase 6.0 contract minimum-coverage assertion), and Section 10.6 (pre-flight check upgraded).
- Implementation: pre-launch assertion `for sym in {BTC,ETH,LINK,LTC,DOT}USDT: assert exists(data/open_interest/sym/8h.csv) AND row_count(IS) ≥ 1000`. **Minimum 3/5 symbols with ≥1000 IS rows** to permit DUAL GATE ≥2-cohort evaluation; below that → BLOCK-PENDING-FIX. Echoes /024 dispatch-defect lesson.

**Recommendation §5(a) (NaN regime risk — 2020-01 → 2020-09 OI missing)**: skip-month policy OR `oi_isnull` indicator. LM Master recommends skip-month (simpler; no extra feature).
- **Status**: **ADOPTED** (skip-month). Section 3.1 implementation note added; Section 6 failure modes updated.
- Implementation: in `add_oi_delta_v1_features`, if the SYMBOL's OI cache has < 90 consecutive valid rows preceding any training month (i.e., the 90-bar z-score window is undefined), that calendar month is SKIPPED for that symbol — the runner omits rows in `_train_for_month` for that symbol. This is simpler than maintaining a learnable `oi_isnull` indicator that LightGBM could combine with `symbol_dummy` to create a curve-fit interaction.

**Recommendation §5(b) (z90 stationarity hides regime shifts)**: emit per-fold rank in engineering report; predict z90 importance will be REGIME-CONDITIONAL across folds.
- **Status**: **ADOPTED**. Section 10.4 engineering report contract updated to require `oi_delta_30_z90` per-fold importance rank table across the 24 walk-forward months (one row per (symbol, fold) pair).
- Diagnostic threshold: if std-of-rank across folds > 8 (LM Master Critic Phase 7.5 priority item #3) → PROMISING-FEATURE-MECHANICAL classification (sister of PROMISING-MECHANICAL; non-compoundable signal source).

**Recommendation §6 (/027 CONFIRMATION bundle composition matrix)**: 3-component for PROMISING (LINK + ETH+gate + OI-aware pool; target +1.30 to +1.50); 2-component otherwise (target +1.10 to +1.30); cross-correlation pre-validation MANDATORY if /025 PROMISING.
- **Status**: **ADOPTED**. Section 11.6 below updated with the full matrix.
- Cross-correlation pre-validation spec: Pearson(monthly_returns_OI-aware-pool, LINK_specialist) < 0.50 AND Pearson(OI-aware-pool, ETH+gate) < 0.50 — both BINDING. If either ≥ 0.50, OI-aware pool stays in the bundle but the QR notes the correlation drag in /027 brief Section 7 prediction.

**Recommendation §7 (Most important point — duplicate of §1)**: see §1 above.
- **Status**: **ADOPTED**. Section 1 closes with the depth-3-learnable + HARD BLOCK framing.

**Recommendation §8 (/026 verdict-conditional staging matrix)**: PROMISING → /026 = pre-CONFIRMATION sanity (cross-corr check); PROMISING-INERT-FAV → /026 = OI momentum composed feature; INERT/LEARNED-NEG/NEG → /026 = methodology pre-CONFIRMATION sanity; NEG-CAT → /026 = methodology + cycle-3 ≥1σ count → multi-seed mandate.
- **Status**: **ADOPTED**. Section 11.7 below updated with the full staging matrix (replaces the prior "borderline rotation discipline" sub-section, which is preserved as Section 11.8 for the rotation-discipline argument).

**Recommendation §9 (Critic Phase 7.5 priority items)**: 5 items — (1) coverage verification; (2) DUAL GATE breadth; (3) per-fold rank stability std>8 → PROMISING-FEATURE-MECHANICAL; (4) OOS-only IC reconfirmation; (5) ORACLE Q4 OOS reconciliation.
- **Status**: **ADOPTED**. Section 10 closeout (new Section 10.8 below) lists all 5 items as Critic Phase 7.5 explicit checks. The engineering report Section 7 + Section 8 deliverables now cover items 3 + 5 directly; items 1 + 2 + 4 are Critic checks against the comparison.csv + feature_importance.csv outputs.

**Net adoption tally**: 9/9 LM Master recommendations ADOPTED (zero MODIFIED, zero REJECTED). This is the highest LM Master adoption rate across v1 cycle-3 EXPLORATIONs (/023 = 4/5; /024 = 3/4) and reflects the unusually well-formed OI-delta hypothesis — Q4 depth-3-learnable mechanism + clean Phase 1 EDA + binding HARD BLOCK on data preconditions.

### 3.5 `run_baseline_v1.py` dispatch

A new elif branch `V1_ITER025_UNIVERSE = V1_BASELINE_UNIVERSE` (5 sym) and `iteration_label == "v1-025"` triggers:

1. Feature column override: pass `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` (now 43 cols) to `LightGbmStrategy`
2. Feature loader: invoke `add_oi_delta_v1_features(df, data_dir=settings.data_dir)` after the existing feature pipeline, BEFORE the column-pinning step
3. Pre-flight check at runner startup: assert OI cache exists for all 5 symbols; if any missing, FAIL FAST (no silent NaN-feature degradation)

The default baseline path (iteration_label != "v1-025") is UNCHANGED — backward-compatible additive infrastructure.

### 3.6 Data fetch precondition — HARD BLOCK (LM Master §4 BINDING)

Per LM Master Phase 4.5 §4 (CRITICAL — ADOPTED BINDING), **Phase 6 cannot launch** until the OI coverage precondition is satisfied:

**Precondition (HARD BLOCK)**:
```python
# Asserted at Phase 6.0 pre-flight; QE returns BLOCK-PENDING-FIX on FAIL.
required_symbols = ["BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT"]
min_is_rows = 1000
oi_cutoff_ms = int(pd.Timestamp("2025-03-24", tz="UTC").timestamp() * 1000)

covered = 0
per_symbol = {}
for sym in required_symbols:
    oi_path = Path("data/open_interest") / sym / "8h.csv"
    if not oi_path.exists():
        per_symbol[sym] = {"status": "MISSING", "is_rows": 0}
        continue
    oi_df = pd.read_csv(oi_path)
    is_rows = (oi_df["open_time"] < oi_cutoff_ms).sum()
    per_symbol[sym] = {"status": "PRESENT" if is_rows >= min_is_rows else "INSUFFICIENT", "is_rows": is_rows}
    if is_rows >= min_is_rows:
        covered += 1

# HARD BLOCK threshold: ≥3/5 symbols with ≥1000 IS rows
assert covered >= 3, f"OI coverage HARD BLOCK: only {covered}/5 symbols ≥{min_is_rows} IS rows; per_symbol={per_symbol}"
```

**Rationale (per LM Master §4)**:
- F-AXIS #1 DUAL GATE evaluation requires ≥2-cohort PROMISING signal AND ≥3-cohort breadth check (Section 4 above). With <3 symbols having OI coverage, the breadth check is structurally undefined.
- "No silent NaN-feature degradation" — echo of /024 dispatch-defect lesson where silent zero-mask fallback corrupted the regime-conditional sub-model assignment. The Phase 6.0 pre-flight FAIL-FAST is the precondition guardrail.
- The OI fetch is in-flight at Phase 1 EDA time (background subprocess, started 2026-05-27 ~13:31 UTC). If still incomplete at Phase 6.0, QE returns BLOCK-PENDING-FIX with `oi_coverage_check.csv` listing per-symbol status; QR re-runs fetch and re-dispatches (Single BLOCK-PENDING-FIX rerun allowed per v1 discipline; see Section 12 roll-back).

**NaN regime policy (LM Master §5(a) ADOPTED — skip-month)**:
- For the 2020-01 → 2020-09 NaN window on BTC/ETH/LINK/LTC (pre-OI archive start), the `add_oi_delta_v1_features` skip-month logic excludes calendar months where the 90-bar z-score is undefined for the symbol from that symbol's per-month training data.
- Implementation: in `_train_for_month`, when a symbol's training-window slice has > 50% rows with NaN `oi_delta_30_z90`, that symbol is excluded from that month's training fold (similar to how cooldown-affected months are handled).
- Engineering report Section 7 emits `oi_coverage_check.csv` per-symbol per-fold to make this transparent.

**Deliverable (binding)**: `reports-v1/iteration_v1-025/oi_coverage_check.csv` — emitted in Phase 6.0 pre-flight; included in Section 10.5 deliverables list.

---

## Section 4 — Falsifiers

### F1 — OOS Sharpe Δ (PRIMARY)

| Verdict band | Range vs anchor +0.6637 | Action |
|---|---|---|
| **PROMISING** | ≥ +0.10 | Add OI delta family to /027 bundle (3rd component) |
| **INERT** | (-0.10, +0.10) | Do not bundle; OI delta cataloged as informational |
| **NEG-clean** | [-0.55, -0.10] | EXCLUDE; LEARNED-NEGATIVE if F-AXIS #1 DUAL GATE PASSES; else INERT-by-importance |
| **NEG-CAT** | ≤ -0.55 | EXCLUDE; trips multi-seed mandate for /026+ HIGH-RISK |

### F-AXIS #1 — DUAL GATE (rank + family gain share + BREADTH CHECK) — PROMISING-clean detector

Per LM Master Phase 4.5 §3 TIGHTENING (ADOPTED), PROMISING-clean now requires **ALL THREE** sub-gates:

1. **Rank gate**: `rank ≤ 14/43` (top-third in feature_importance ranking) on **≥ 2 cohorts** (of Pool A + Model C / D / E)
2. **Gain share gate**: `family gain share ≥ 4.0%` on the SAME **≥ 2 cohorts** as the rank gate (where "family gain share" is `oi_delta_30_z90`'s importance fraction within its model)
3. **NEW Breadth check gate**: `oi_delta_30_z90 rank ≤ 20/43` on **≥ 3 cohorts** (a softer breadth bar that prevents BTC+ETH-only PROMISING while LINK/LTC/DOT silently NaN-degrade)

Uniform parity at 43 cols = 100% / 43 = **2.33% per feature**. A 4.0% threshold = 1.7× parity (same multiplicative standard used at /023). The breadth threshold of 20/43 = ~47% percentile is a structural sanity bar — even a NaN-degraded feature should not place above this rank on coverage-degraded symbols.

**Verdict logic at F-AXIS #1**:
- Sub-gates 1 + 2 + 3 ALL PASS → DUAL GATE PASS (PROMISING-clean conditional on F1 ≥ +0.10)
- Sub-gates 1 + 2 PASS but breadth check FAILS (rank ≤14 + gain ≥4% on 2 cohorts, but rank ≤20 on only ≤2 cohorts) → **PROMISING-BTC-ETH-ONLY** (new sub-classification; signals OI-fetch coverage issue OR BTC+ETH-specific load-bearing; flagged for /026 cross-correlation investigation)
- Sub-gates 1 + 2 FAIL on all cohorts → INERT-by-importance regardless of F1 outcome
- Sub-gates 1 + 2 PASS on ≥ 2 cohorts AND F1 NEGATIVE → LEARNED-NEGATIVE sub-classifier (carries forward to OI delta dead-paths catalog if applicable)
- Sub-gates 1 + 2 + 3 ALL PASS AND F1 NEGATIVE → LEARNED-NEGATIVE-BREADTH (strongest LN sub-classification — the feature is broadly load-bearing across cohorts AND OOS fails; the rarest and most informative LN outcome)

### F-AXIS #2 — Trade count

- IS trade count band: **[400, 850]** (vs baseline 621; allows ±35% perturbation from feature addition)
- OOS trade count band: **[120, 280]** (vs baseline 189; allows ±48%)
- Out-of-band trade count = anomaly to document but not auto-reject

### F-AXIS #3 — OI delta orthogonality vs funding family

Already PRE-VERIFIED at Phase 1 EDA: max |IC| OI-vs-funding = 0.135 on BTC. The full-cohort runner re-verifies this on the full IS data; threshold |IC| < 0.5 on ALL (sym, OI col, funding col) pairs. If ANY pair ≥ 0.5 → OI delta is REDUNDANT-WITH-FUNDING; declare NEG-by-redundancy.

### F-AXIS #4 — n_eff per cell

Per `feedback_v1_n_eff_barrier_magnitude_curve.md` (cycle-2 structural finding) and /023 + /024 modal expectation:
- **n_eff_per_cell modal**: 9 (matches /023); band [5, 10]
- If n_eff < 5 → labeling magnitude excess concern (would be unexpected since labels UNCHANGED)
- If n_eff > 10 → over-labelled (unexpected)

n_eff measurement is methodology substrate; the EXPLORATION emits dsr.json with the per-cell n_eff column.

### F-AXIS #5 — ADF stationarity on oi_delta_30_z90 (informational)

EDA confirms ADF p < 0.001 on BTC z90 series. Engineering report emits `adf_test.csv` per-symbol. **Informational** — INFORMATIONAL band: all 5 symbol-level ADF p < 0.05 is the soft target; non-stationary z90 would be unexpected given the design.

### F3 — IS Sharpe Δ (auto-reject)

| Band | Threshold | Action |
|---|---|---|
| IS-CATASTROPHIC | ≤ -0.30 | AUTO-REJECT (Section 8 Row 7) regardless of OOS |
| IS-NEG-clean | (-0.30, -0.10] | Document concern |
| IS-INERT | (-0.10, +0.10) | Pass |
| IS-PROMISING | ≥ +0.10 | Document |

Baseline IS Sharpe = +0.2829. IS-CAT threshold = +0.2829 - 0.30 = -0.0171 (so any IS Sharpe < -0.0171 trips AUTO-REJECT — a stricter test than the absolute -0.30 floor; the brief uses the absolute floor per /024 convention).

### F7 — Per-symbol behavioral expectation (LM Master §4 hold)

**Pre-registered behavioral effect**:
- IS trade count change: ±10% from baseline 621 (so [559, 683] expected band; the F-AXIS #2 [400, 850] is the auto-reject band)
- OOS Sharpe change direction: 50/50 prior (no strong directional prior from EDA — ORACLE Q4 is bullish but Q1 and Q5 mid-positive too)

### Falsifier summary (verdict matrix)

| F1 | F-AXIS #1 | Verdict |
|---|---|---|
| ≥ +0.10 | DUAL GATE PASS ≥2 cohorts | **PROMISING-clean** |
| ≥ +0.10 | DUAL GATE FAIL all cohorts | PROMISING-INERT-FAVORABLE (rare) |
| ∈ (-0.10, +0.10) | (any) | **INERT** |
| ∈ [-0.55, -0.10) | DUAL GATE PASS ≥2 cohorts | **LEARNED-NEGATIVE** sub-classifier (information ingested, OOS failed) |
| ∈ [-0.55, -0.10) | DUAL GATE FAIL all cohorts | **NEGATIVE-INERT** (feature not picked + OOS negative — most likely outcome per /023 LEARNED-NEGATIVE pattern) |
| ≤ -0.55 | (any) | **NEGATIVE-CATASTROPHIC** |
| (F3 IS Δ ≤ -0.30) | (any) | **AUTO-REJECT Row 7** |

---

## Section 5 — Predicted verdict priors

Post-LM-Master-Phase-4.5 priors (LM Master §2 recommendation ADOPTED):

| Verdict | QR initial | LM Master | **FINAL (ADOPTED)** | Rationale |
|---|---|---|---|---|
| PROMISING-clean | 18% | 22% | **22%** | Q4 ORACLE Sharpe-proxy +1.68 is 2.4× /023's strongest mid-band; depth-3 carves Q4 single-split |
| PROMISING-INERT-FAVORABLE | 8% | 8% | **8%** | unchanged |
| INERT | 25% | 22% | **22%** | Q4 depth-3-easy; less likely INERT than /023's funding which required depth-3 directional composition (-3pp) |
| LEARNED-NEGATIVE | 30% | 30% | **30%** | /023 pattern remains structural prior; OI is sister-primitive class and could repeat the LEARNED-but-OOS-fails pattern (UNCHANGED) |
| NEGATIVE-INERT | 13% | 12% | **12%** | sub-modal; slight (-1pp) compression vs QR estimate |
| NEG-CAT | 4% | 4% | **4%** | OI delta is feature-family, not model-arch; basin-relocation risk lower (UNCHANGED) |
| AUTO-REJECT (F3 IS-CAT) | 2% | 2% | **2%** | OI delta as single-feature addition unlikely to collapse IS basin (UNCHANGED) |

**Net shift**: PROMISING tail (PROMISING-clean + PROMISING-INERT-FAVORABLE) = 26% QR → **30% FINAL** (vs /023's 20%, vs /024's ~14%). This is the highest pre-EXPLORATION PROMISING-tail allocation across cycle-3 EXPLORATIONs.

**Modal expectation**: **LEARNED-NEGATIVE 30% AND PROMISING-clean 22% (joint tail 52%)** — the modal is still LEARNED-NEGATIVE by single-bucket mass but the PROMISING+LN combined mass (52%) is the dominant outcome arc. Either Q4 carves cleanly into OOS (PROMISING) or it carves cleanly into IS but doesn't transfer (LN).

**Predicted F-AXIS #1 outcome** (revised post-LM-Master): DUAL GATE PASS on Pool A + LINK + ETH (3 cohorts; ETH added because LM Master breadth check elevated importance of ETH coverage — see §3 above). DUAL GATE may FAIL on LTC + DOT (smaller cohorts; thinner OI extreme bands; OI fetch coverage may also be partial 2020 listings). Breadth-check z90 rank ≤20/43 on ≥3 cohorts is the new structural target: expect Pool A + LINK + ETH all pass z90 rank, with LTC + DOT marginal.

---

## Section 6 — Failure modes

### 6.1 OI data unavailable → BLOCK-PENDING-FIX (LM Master §4 HARD BLOCK)

- **Pre-Phase-6.0 (HARD BLOCK)**: per Section 3.6, if `data/open_interest/{SYM}/8h.csv` row count IS rows < 1000 for any symbol AND fewer than 3/5 symbols have ≥1000 IS rows, QE returns BLOCK-PENDING-FIX with engineering report Section 1 listing per-symbol coverage from `oi_coverage_check.csv`. QR re-runs fetch and re-dispatches (one rerun allowed; see Section 12 roll-back).
- **NaN regime (2020-01 → 2020-09)**: per skip-month policy (Section 3.6), affected symbols are excluded from those months' training folds. NOT a BLOCK condition.
- **Current status**: fetch in flight as of 2026-05-27 13:31 UTC; ETA ETH/LINK/LTC/DOT by ~13:50-14:30 UTC. Phase 6 launch contingent on fetch completion AND HARD BLOCK precondition pass.

### 6.2 OI delta = INERT-by-importance (most likely per /023 LEARNED-NEGATIVE pattern transferring)

- DUAL GATE FAIL on all cohorts (rank > 14/43 OR gain share < 4.0% on every model)
- F1 in [-0.10, +0.10] INERT band
- Diagnosis: LightGBM-at-single-seed didn't pick up OI delta as load-bearing
- Path forward: cycle-4 may revisit OI delta at multi-seed budget OR explore different OI primitives (raw level, momentum)

### 6.3 OI delta = LEARNED-NEGATIVE

- DUAL GATE PASS ≥2 cohorts (feature LEARNED above parity)
- F1 ∈ [-0.55, -0.10) NEGATIVE-clean band
- Diagnosis: same as /023 funding — information ingested + OOS realization fails (tail effect averaged over)
- Path forward: catalog as LEARNED-NEGATIVE; do NOT bundle into /027; carry forward as evidence that single-feature addition pattern fails OOS for non-OHLCV primitives at single-seed EXPLORATION budget

### 6.4 OI delta = PROMISING

- DUAL GATE PASS ≥2 cohorts AND F1 ≥ +0.10
- Diagnosis: rare; OI delta is genuinely orthogonal AND OOS-positive
- Path forward: BUNDLE into /027 as 3rd component alongside LINK specialist + ETH+gate specialist. /027 target moves to +1.30 to +1.50 OOS Sharpe under multi-seed correlation drag.

### 6.5 OI delta = NEG-CAT

- F1 ≤ -0.55
- Diagnosis: catastrophic basin shift — feature destabilizes LightGBM training; trips 3-in-cycle ≥1σ NEG-CAT count → mandatory multi-seed for /026 HIGH-RISK
- Path forward: cycle-4 mandate multi-seed for HIGH-RISK; OI delta family closed for v1 single-seed budget

### 6.6 OI delta = REDUNDANT-WITH-FUNDING

- F-AXIS #3 |IC| OI vs funding ≥ 0.5 on any pair
- Diagnosis: OI delta duplicates funding signal at the IC level; LightGBM has both columns but `colsample_bytree` picks redundantly
- Path forward: DROP OI delta; the funding family /023 is already cataloged LEARNED-NEGATIVE; this would be a methodological cleanup

### 6.7 Dispatch defect (echo of /024 silent zero-mask fallback)

- Per `feedback_v1_dispatch_defect_silent_fallback.md`: feature loader must HARD-RAISE on missing OI cache, never silently fill NaN.
- Phase 6.0 pre-flight verifies: (a) feature loader raises FileNotFoundError when OI cache missing; (b) no silent np.nan or np.zeros fallback in `add_oi_delta_v1_features` body.

### 6.8 Engineering report missing at Phase 7.5

- 5 incidents in /019-/023; 5/5 BLOCK-PENDING-FIX retrospective fixes per cycle. /024 broke the streak (engineering report present at Phase 7.5 dispatch). /025 brief Section 10.4 BINDING: engineering_report.md must be present before Phase 7.5 Critic dispatch.

---

## Section 7 — Pre-registered predictions

| Pre-registered claim | Predicted value | Falsification trigger |
|---|---|---|
| BTC oi_delta_30_z90 importance rank (Pool A) | top-third (≤14/43) | rank > 28/43 → claim false |
| BTC oi_delta_30_z90 gain share (Pool A) | ≥ 4.0% | < 3.0% → claim false |
| OI vs funding family max |IC| (any sym) | < 0.30 | ≥ 0.5 → REDUNDANT path |
| OOS Sharpe Δ vs +0.6637 | in [-0.30, +0.05] | beyond either tail = surprising outcome |
| Verdict probability mass on LEARNED-NEGATIVE | 30% modal | (informational; calibration check post-outcome) |
| n_eff per cell median | 9 (modal) | < 5 or > 12 = surprising |
| IS trade count | 580-680 (±10% of 621) | outside [400, 850] = anomaly |
| OOS trade count | 170-210 (±10% of 189) | outside [120, 280] = anomaly |
| ADF stationarity on z90 | 5/5 symbols p < 0.05 | any symbol p ≥ 0.05 = informational concern |

---

## Section 8 — MERGE/NO-MERGE matrix (NOT applicable — EXPLORATION, not CONFIRMATION)

Per v1 skill: **EXPLORATION iterations DO NOT update BASELINE_V1.md**. Only CONFIRMATION-MERGE updates baseline. This iteration's MERGE/NO-MERGE decision concerns whether the OI delta family enters the /027 CONFIRMATION bundle.

| /025 verdict | /027 bundle composition | /027 expected ceiling |
|---|---|---|
| PROMISING-clean | LINK + ETH+gate + OI-aware pool (3 components) | +1.30 to +1.50 OOS Sharpe |
| PROMISING-INERT-FAVORABLE | LINK + ETH+gate (2 components, OI optional informational) | +1.10 to +1.30 OOS Sharpe |
| INERT | LINK + ETH+gate (2 components; OI EXCLUDED) | +1.10 to +1.30 OOS Sharpe |
| LEARNED-NEGATIVE | LINK + ETH+gate (2 components; OI EXCLUDED) | +1.10 to +1.30 OOS Sharpe |
| NEGATIVE-INERT | LINK + ETH+gate (2 components; OI EXCLUDED) | +1.10 to +1.30 OOS Sharpe |
| NEG-CAT | LINK + ETH+gate (2 components; OI EXCLUDED + multi-seed mandate trips for /026 HIGH-RISK) | +1.10 to +1.30 OOS Sharpe |

The /027 substrate is STABLE at 2-specialist baseline regardless of /025 outcome (excluding the PROMISING-clean case which adds a 3rd component).

---

## Section 9 — Library stack

| Library | Version | Used for |
|---|---|---|
| `pandas` | ≥2.0 | DataFrame manipulation |
| `numpy` | ≥1.24 | Numerical ops |
| `lightgbm` | ≥4.0 | Model training (unchanged) |
| `statsmodels` | (installed) | ADF stationarity test (informational) |
| `mlfinlab==1.4` | (installed) | CPCV (used by validation_v1; unchanged) |
| `pypbo` | (installed) | PBO (used by validation_v1; unchanged) |

No new dependencies. OI fetch uses `httpx` (already installed via core `fetch-oi` subcommand from iter-v3/093).

---

## Section 10 — Run protocol

### 10.1 Symbol universe

`V1_ITER025_UNIVERSE = V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")` — full 5-symbol pool.

### 10.2 Optuna config

- `--n-trials 18` (cycle-3 EXPLORATION default)
- `--ensemble-size 3` (inner ensemble for variance reduction; EXPLORATION budget)
- `--seeds 1` (single-seed=42; HIGH-RISK OPT-IN per Section 2.5)

### 10.3 Feature columns

`feature_columns = list(V1_FEATURE_COLUMNS_PRUNED)` (43 cols; alphabetically sorted)

### 10.4 Engineering report (BINDING)

Per `feedback_v1_engineering_report_binding.md` (cataloged at /023): the engineering_report.md MUST be present at Phase 7.5 Critic dispatch. The report must contain:

1. Implementation summary
2. Backtest config (effective Optuna args, ENSEMBLE_SIZE, seeds)
3. Wall-clock timing per model
4. F-AXIS-MECHANISM measurement table (DUAL GATE per-cohort)
5. Test output (pytest -v on tests/features_v1/test_oi_delta_v1.py)
6. Anomaly notes
7. Per-cohort OI delta importance + rank table (5 symbols × 4 models)
8. ORACLE EDA reconciliation (Phase 1 EDA vs observed trade-roster IS PnL band attribution)

### 10.5 Deliverables for Phase 7.5

- `reports-v1/iteration_v1-025/comparison.csv` (IS + OOS metrics)
- `reports-v1/iteration_v1-025/in_sample/per_symbol.csv` + `out_of_sample/per_symbol.csv`
- `reports-v1/iteration_v1-025/in_sample/feature_importance.csv` per model (A_combined, C, D, E)
- `reports-v1/iteration_v1-025/in_sample/feature_importance_per_fold.csv` — **NEW per LM Master §5(b)**: per-fold (24 walk-forward months × symbol) `oi_delta_30_z90` rank for regime-conditional stability check
- `reports-v1/iteration_v1-025/in_sample/trades.csv` + `out_of_sample/trades.csv`
- `reports-v1/iteration_v1-025/oi_coverage_check.csv` — **NEW per LM Master §4**: per-symbol OI cache existence + IS row count + coverage status (emitted in Phase 6.0 pre-flight)
- `reports-v1/iteration_v1-025/adf_test.csv` — ADF p-value per OI feature per symbol (informational)
- `reports-v1/iteration_v1-025/ic_matrix.csv` — IC pairs (OI features vs baseline TOP5 + vs funding family)
- `reports-v1/iteration_v1-025/ic_matrix_oos.csv` — **NEW per LM Master §9 item 4**: OOS-only IC reconfirmation for (oi_delta_30_z90, funding_rate_zscore_30) and (oi_delta_30_z90, mom_macd_hist_12_26_9)
- `reports-v1/iteration_v1-025/oracle_q4_oos_attribution.csv` — **NEW per LM Master §9 item 5**: OOS trade-roster distribution by `oi_delta_30_z90` quintile (for ORACLE Q4 band reconciliation)
- `reports-v1/iteration_v1-025/dsr.json` — DSR + PSR + n_eff_per_cell median (informational EXPLORATION-mode)
- `reports-v1/iteration_v1-025/engineering_report.md`

### 10.6 Pre-flight checks (Phase 6.0) — HARD BLOCK gates

**HARD BLOCK checks (Phase 6.0 cannot launch if any FAIL)**:
- `grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/` → empty (track isolation)
- `grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/` → empty
- `assert V1_FEATURE_COLUMNS_PRUNED has 43 unique cols`
- `assert "oi_delta_30_z90" in V1_FEATURE_COLUMNS_PRUNED`
- **(NEW per LM Master §4 BINDING)** OI coverage HARD BLOCK: `for sym in {BTC,ETH,LINK,LTC,DOT}USDT: read data/open_interest/sym/8h.csv; count IS rows (open_time < OOS_CUTOFF_MS)`. Emit `oi_coverage_check.csv`. Assert `≥3/5 symbols with ≥1000 IS rows`. If FAIL → BLOCK-PENDING-FIX.
- Anti-pattern static scan: no `np.zeros` or `np.nan` silent-fill fallback in `oi_delta_v1.py`; the feature loader MUST raise `FileNotFoundError` on missing OI cache (no silent NaN-feature degradation — echo of /024 dispatch-defect lesson)
- `walk_forward.py:113` regression check: `train_end_ms = test_start_ms - embargo_ms` (not just `test_start_ms`)

### 10.7 Wall-clock kill switch

- 45 min soft target; 90 min alarm; 2h HARD CAP (engineer kills backtest if exceeded)

### 10.8 Critic Phase 7.5 closeout — explicit priority items (LM Master §9 ADOPTED)

Per LM Master Phase 4.5 §9 (ADOPTED), the Critic Phase 7.5 review checklist for /025 closeout explicitly includes:

1. **Coverage verification (FIRST)**: Open `oi_coverage_check.csv` and verify ETH/LINK/LTC/DOT OI cache existed at Phase 6.0 with ≥1000 IS rows; verify ≥3/5 symbols cleared the HARD BLOCK. **BLOCK if not (post-hoc invalidation of dispatch)**.
2. **DUAL GATE breadth check**: per-cohort F-AXIS #1 evaluation — confirm `rank ≤14/43 AND gain ≥4.0% on ≥2 cohorts AND rank ≤20/43 on ≥3 cohorts (breadth)`. If breadth fails while sub-gates 1+2 pass → reclassify as PROMISING-BTC-ETH-ONLY.
3. **Per-fold rank stability**: open feature_importance.csv per fold (24 walk-forward months); compute std-of-rank for `oi_delta_30_z90` across folds. If std > 8 → REGIME-CONDITIONAL importance → PROMISING-FEATURE-MECHANICAL classification (per `feedback_v3_promising_feature_mechanical.md` sister rule); non-compoundable signal source.
4. **OOS-only IC reconfirmation**: compute `IC(oi_delta_30_z90, funding_rate_zscore_30)` and `IC(oi_delta_30_z90, mom_macd_hist_12_26_9)` on OOS data ONLY (vs IS-only at Phase 1 EDA). If OOS |IC| > 0.5 on any pair → flag as IS/OOS regime drift in OOS feature correlations.
5. **ORACLE Q4 band attribution reconciliation OOS**: if `oi_delta_30_z90` Q4 band (z90 ∈ [+0.29, +0.95]) is NOT well-represented in the OOS trade roster — i.e., the model emits trades but those trades' OI z90 distribution doesn't cluster in Q4 — then PROMISING → reclassify LEARNED-NEGATIVE (basin relocation: the IS Q4 carve didn't transfer to OOS). Engineering report Section 8 emits the OI z90 distribution per IS/OOS trade-roster.

The Critic verdict at Phase 7.5 explicitly chains all 5 items; if any FAIL → BLOCK-PENDING-FIX or reclassification with verdict downgrade.

---

## Section 11 — /027 CONFIRMATION pre-staging matrix

(per dispatch instructions Section 11.7)

### 11.1 /025 PROMISING → /027 = 3-component bundle

- Components: (1) LINK-only specialist Model C', (2) ETH-only + symmetric BTC-trend gate Model G, (3) OI-aware pool (5-sym A/C/D/E with `oi_delta_30_z90` in V1_FEATURE_COLUMNS_PRUNED 43)
- Multi-seed config: ENSEMBLE_SIZE=10, --seeds 5 (5 inner × 5 outer = 25 paths/cell), --n-trials 35
- Wall-clock estimate: ~9-12 hours (pool training scales with feature count; ~5h baseline pool × 1.05 for the 43rd col + 2 specialists at ~1.5-2h each = ~9h; 6h HARD CAP per cadence — will require validation slot)
- /027 bundle target: **+1.30 to +1.50 OOS Sharpe** under correlation drag

### 11.2 /025 INERT (incl. INERT-by-importance) → /027 = 2-component bundle

- Components: (1) LINK specialist, (2) ETH+gate specialist
- Pool baseline unchanged (5-sym A/C/D/E with V1_FEATURE_COLUMNS_PRUNED 42 — OI excluded)
- Multi-seed config: same as 11.1 (ENSEMBLE_SIZE=10, --seeds 5, --n-trials 35)
- Wall-clock: ~6-8h (pool + 2 specialists)
- /027 bundle target: **+1.10 to +1.30 OOS Sharpe**

### 11.3 /025 LEARNED-NEGATIVE → /027 = 2-component bundle

- Same as 11.2 (OI EXCLUDED, /027 stays 2-specialist).
- Distinct dead-paths catalog entry: `feedback_v1_oi_delta_learned_negative.md` documents OI delta as 2nd LEARNED-NEGATIVE non-OHLCV primitive (alongside funding).

### 11.4 /025 NEG-CAT → /027 = 2-component bundle + multi-seed mandate

- Same as 11.2.
- BUT: cycle-3 cumulative ≥1σ NEG-band count = 4 (/020 + /022 + /024 + /025). The v1 rule "3+ HIGH-RISK >1σ negative deltas mandates next HIGH-RISK to multi-seed" already would fire at /024. /025 NEG-CAT confirms the mandate; /026 (if HIGH-RISK) must be multi-seed. /027 CONFIRMATION already is multi-seed by design.

### 11.5 /027 falsification

- /027 multi-seed mean OOS Sharpe < +1.0 → /027 NO-MERGE; cycle-3 closes NO-MERGE; BASELINE_V1.md UNCHANGED through cycle-3
- /027 IS-OOS Pareto FAILS on ≥1 of 6 metric vector dimensions → NO-MERGE per Critic Check 6
- /027 ≥10 trades/month + ≥130 OOS total floor FAILS → NO-MERGE
- /027 LINK or ETH+gate specialist top-symbol concentration > 30% → NO-MERGE
- All gates PASS + bundle Pareto-non-dominated → CONFIRMATION-MERGE; BASELINE_V1.md UPDATES

### 11.6 /027 CONFIRMATION bundle composition matrix (LM Master §6 ADOPTED)

Per LM Master Phase 4.5 §6 — full bundle-composition matrix by /025 verdict:

| /025 verdict | /027 components | OOS target | Cross-correlation pre-validation |
|---|---|---|---|
| **PROMISING-clean (22%)** | 3-component: (1) LINK specialist Model C', (2) ETH+gate specialist Model G, (3) **OI-aware pool** (5-sym A/C/D/E with `oi_delta_30_z90`) | **+1.30 to +1.50** under correlation drag | **MANDATORY**: Pearson(monthly_returns_OI-aware-pool, LINK_specialist) < 0.50 AND Pearson(OI-aware-pool, ETH+gate) < 0.50 |
| **PROMISING-INERT-FAVORABLE (8%)** | 2-component: LINK + ETH+gate (OI catalog informational, NOT in bundle) | +1.10 to +1.30 | NOT REQUIRED (no 3rd component) |
| **PROMISING-BTC-ETH-ONLY** (sub-classification per Section 4 above) | 2-component: LINK + ETH+gate (OI documented as coverage-limited, NOT bundled) | +1.10 to +1.30 | NOT REQUIRED |
| **INERT (22%)** | 2-component: LINK + ETH+gate | +1.10 to +1.30 | NOT REQUIRED |
| **LEARNED-NEGATIVE (30%)** | 2-component: LINK + ETH+gate (OI catalogued 2nd LEARNED-NEGATIVE non-OHLCV primitive alongside funding) | +1.10 to +1.30 | NOT REQUIRED |
| **NEGATIVE-INERT (12%)** | 2-component: LINK + ETH+gate | +1.10 to +1.30 | NOT REQUIRED |
| **NEG-CAT (4%)** | 2-component: LINK + ETH+gate + cycle-3 ≥1σ NEG count → multi-seed mandate trips for /026 if HIGH-RISK | +1.10 to +1.30 | NOT REQUIRED |
| **AUTO-REJECT F3 IS-CAT (2%)** | 2-component: LINK + ETH+gate | +1.10 to +1.30 | NOT REQUIRED |

**Bundle architecture (cross-verdict invariants)**:
- Pool: 5-sym (Models A/C/D/E unchanged from baseline; BTC + LTC + DOT in pool always)
- Specialist dispatch: LINK signal from Model C' overrides Model C; ETH signal from Model G overrides Model A's ETH slice via regime-gate
- Multi-seed config: ENSEMBLE_SIZE=10, --seeds 5 (5 inner × 5 outer = 25 paths/cell), --n-trials 35
- /027 wall-clock: 3-component ~9-12h; 2-component ~6-8h

**Cross-correlation pre-validation gate (PROMISING-clean only)**:
- If either Pearson < 0.50 condition FAILS → OI-aware pool stays in the bundle BUT the /027 brief Section 7 (predictions) records the correlation drag as a quantitative discount on the +1.30 to +1.50 target
- If BOTH pass → the 3-component target stands at +1.30 to +1.50
- The pre-validation runs in /026 (per Section 11.7 below); /027 commits to bundle composition AFTER /026 cross-corr check completes

### 11.7 /026 staging matrix (LM Master §8 ADOPTED)

Per LM Master Phase 4.5 §8 — full /026 verdict-conditional staging:

| /025 verdict | /026 axis | /026 deliverable |
|---|---|---|
| **PROMISING-clean (22%)** | **Pre-CONFIRMATION sanity** (cross-correlation pre-validation between OI-aware pool, LINK specialist, ETH+gate specialist) | `reports-v1/iteration_v1-026/cross_corr_validation.csv` — Pearson(monthly_returns) pairwise across the 3 components; methodology pre-CONFIRMATION sanity in same iteration |
| **PROMISING-INERT-FAVORABLE (8%)** | OI momentum composed feature (Category-2 LR-PF; algebraic identity; e.g., `oi_delta_30_z90 × sign(oi_delta_30_z90.lag1 - 0)` to test mean-reversion vs continuation) | Sharpe-Δ primary falsifier per `feedback_v3_lr_pf_methodology.md`; importance ≥30 threshold per `feedback_v3_engineered_feature_pivot.md`; **NOT** stacked with /025's `oi_delta_30_z90` (SAME-FAMILY rule) |
| **INERT (22%)** | Methodology pre-CONFIRMATION sanity; no new EXPLORATION axis; proceed to /027 | Methodology smoke-test on /027 dispatch infrastructure |
| **LEARNED-NEGATIVE (30%)** | Same as INERT (methodology pre-CONFIRMATION sanity); OI cataloged as 2nd LEARNED-NEGATIVE non-OHLCV primitive | Dead-paths catalog entry `feedback_v1_oi_delta_learned_negative.md` |
| **NEGATIVE-INERT (12%)** | Same as INERT | (same as INERT) |
| **NEG-CAT (4%)** | Methodology only; cycle-3 ≥1σ NEG count reaches 4 → mandatory multi-seed for future HIGH-RISK declarations | Multi-seed mandate cataloged as feedback rule update |
| **AUTO-REJECT F3 IS-CAT (2%)** | Methodology only; AUTO-REJECT cataloged | (same as INERT) |

**Cross-/026-verdict invariant**: /026 NEVER opens a new EXPLORATION axis in the feature-family rotation (which is locked-out at /026 by rotation discipline; see Section 11.8 below). /026 is exclusively pre-CONFIRMATION sanity OR composed-feature sanity OR methodology sanity.

**Net effect**: in all 7 verdicts above, /026 is a "narrow" iteration — small scope, fast wall-clock (≤2h cadence cap), single deliverable. The cycle-3 ledger advances /025 EXPLORATION → /026 narrow → /027 CONFIRMATION cleanly.

### 11.8 Borderline rotation discipline at /025 (preserved from prior Section 11.7)

- Per Section 0.6: family `feature-family` REPEAT (after /023 funding). Critic §11.7 permission applies. /024 Critic Path Forward #1 explicitly endorsed this. No rotation violation.
- For /026 (if /025 PROMISING/INERT/LN/NEG-CAT): the prior 5 going into /026 = {/021 methodology, /022 cohort-LTC, /023 feature-family, /024 model-arch, /025 feature-family}. /026 rotation: 2 of 5 prior are `feature-family` → /026 MUST NOT be `feature-family` (rotation discipline kicks in).
- Per Section 11.7 above: /026 is narrow (pre-CONFIRMATION sanity OR composed-feature OR methodology) — NOT a new feature-family axis. Rotation discipline satisfied.

---

## Section 12 — Roll-back

If at Phase 6 implementation any of these fire, abort and roll back:

1. **Critic Phase 6.0 pre-flight BLOCK** — return to Phase 5 brief revision (one revision allowed)
2. **Test suite FAIL** — `pytest tests/features_v1/test_oi_delta_v1.py -v` must produce all-green; baseline test 23 + new tests (≥3) must pass
3. **Wall-clock 2h HARD CAP hit during Optuna** — kill backtest, document partial results, declare INFRASTRUCTURE-NEG (not a verdict per se; reroute to /026 with shorter scope)
4. **OI fetch fails to complete by Phase 6.0** — BLOCK-PENDING-FIX dispatch from Phase 6.0; QR re-fetches OI; one retry only

The branch `iteration-v1/025` is rebased from /024 HEAD; rolling back = `git checkout iteration-v1/024 && git branch -D iteration-v1/025`. No /027 commitments are made by /025 alone.

---

## Section 13 — Self-check

Pre-Phase-6 self-check (QR own verification):

1. **EDA evidence sufficient**: BTC IS-only EDA covers (a) availability, (b) distribution, (c) IC vs baseline TOP5, (d) orthogonality vs funding, (e) ORACLE forward-return banding, (f) ADF stationarity. ETH/LINK/LTC/DOT EDA appended at Section 2.8 once fetch lands.
2. **Hypothesis ↔ Falsifier alignment**: H1 → F-AXIS #1 DUAL GATE + F1; H2 → F-AXIS #3 orthogonality. Both falsifiers exist BEFORE Phase 6 launches.
3. **HIGH-RISK declaration mitigation explicit**: Section 2.5 lists axis-specific reasoning for single-seed=42 OPT-IN.
4. **Axis rotation valid**: Section 0.6 documents 1 of 5 prior is feature-family; not 5 of 5.
5. **/027 CONFIRMATION pre-staged**: Section 11 covers all 5 verdict outcomes.
6. **Engineering report BINDING**: Section 10.4 documents requirements.
7. **Anti-cheating: walk_forward.py:113 unchanged** (`train_end_ms = test_start_ms - embargo_ms`); BASELINE_V1.md unchanged; OOS_CUTOFF_DATE = 2025-03-24 unchanged.
8. **Section 3 LM Master response (Section 3.4)**: **POPULATED 2026-05-27** post-Phase-4.5 advisory. 9/9 recommendations ADOPTED (priors recalibrated to 22/8/22/30/12/4/2; F-AXIS #1 DUAL GATE tightened with breadth check; HARD BLOCK on OI fetch ≥3/5 symbols ≥1000 IS rows; skip-month NaN policy; per-fold rank emission; 3-component vs 2-component bundle matrix; /026 staging matrix; 5 Critic Phase 7.5 priority items). Phase 5.5 gate verifies Section 3.4 is populated before Phase 6.0 dispatch — **VERIFIED**.

---

**End of brief.**
