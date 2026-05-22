# iter-v3/125 Research Brief — Cycle-7 EXPLORATION #4 — WILD axis under LIFTED constraints

**Axis**: Wholesale V3_MODELS UNIVERSE REPLACEMENT — BCH/LDO/TRX → ATOM/RUNE/UNI at 8h cadence with all other /121 architecture identical (incl. /116 no_confirm RULE-layer primitive, 14-feature V3_FEATURE_COLUMNS_TOP_N stack, 7-gate RiskV2, +2/-1 ATR triple-barrier K=21).

**Lineage discipline**: This is the FIRST cycle-7 axis pivot under the LIFTED constraints per `feedback_v3_cycle7_constraints_lifted.md` (2026-05-20 user directive — symbol universe + candle frequency LIFTED; QR mandated to "create innovations, do not follow always the playbook, try something wild"). The chosen axis is universe (Critic Priority 4 from /124 closeout was Critic Priority 1 stateful drawdown brake — DEFERRED in favor of the WILD axis the user mandated). The chosen universe ATOM/RUNE/UNI is *structurally distinct* from all 7 prior v3 universe attempts (/021 HBAR+AVAX, /069 ADA, /078 BCH/ADA/TRX, /083 +FIL, /087 +GALA/MANA/SAND, /110-111 CRV/AAVE/GRT/ADA, /069 ADA-replace) because: (a) all 3 candidates have NEVER been in any prior V3_MODELS bundle, (b) the /121 baseline includes /116 no_confirm, which changes the trade-exit semantics that all prior universe attempts (which were /059-anchored without no_confirm) evaluated against, (c) the candidate selection is sector-diverse across L0/L1/DeFi-governance, orthogonal to the all-DeFi /110-111 attempt (CRV/AAVE/GRT all DeFi) and the all-gaming /087 attempt (GALA/MANA/SAND).

**Cycle**: 7 EXPLORATION slot **#4 of 10**. Cycle-7 catalog state at /124 closeout: /122 NEGATIVE-INERT (ETH OHLCV cross-asset), /123 NEGATIVE-catastrophic (ETH realized-vol ratio), /124 NEGATIVE-catastrophic (K=63 longer-cadence labels). /125 is the first axis under the LIFTED constraints. Cycle-7 axes 1 (cross-asset OHLCV) + 3 (labeling-DURATION) are CLOSED bilaterally; axis 2 (non-LightGBM model classes) is locked out (cycle-5 finding); axis 4 (NEW symbol universe) was constrained under the old BCH/LDO/TRX rules but is now FULLY OPEN under the LIFTED constraints.

**Anchor (EXPLORATION-mode comparison)**: iter-v3/121 multi-seed CONFIRMATION-MERGE BASELINE_V3.md numbers (IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682**) — the canonical anchor per `BASELINE_V3.md`. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode 3-seed results compress relative to CONFIRMATION-mode 10-seed; the /122 brief established the architectural-adjustment factor at ≈ −0.25 IS Sharpe. The /125 brief uses BOTH anchors per /122 Critic Rec 3 (PER-CRITERION ANCHOR ANNOTATION).

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. The sacred constants are immutable across all three tracks; no /125 modification touches them.

- **IS window**: data extent start (per-symbol earliest 8h candle close ≥ 2020-01-01 for ATOM, ≥ 2020-09-04 for RUNE, ≥ 2020-09-18 for UNI) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent (~2026-05-19 for ATOM/UNI, 2026-05-17 for RUNE).
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **Reporting layer**: `comparison.csv` and `in_sample/` / `out_of_sample/` directories split on `OOS_CUTOFF_DATE` exactly.
- **Bar interval**: 8h (LIFTED constraint permits any frequency; 8h chosen because (a) 24h cadence was TESTED at /117 NEGATIVE catastrophic on the incumbent universe, (b) 4h/12h cadence has NO data in the worktree, so fetch overhead would risk the 2h cap, (c) maintaining 8h enables direct architectural comparability with all prior v3 universe attempts).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

The /125 axis introduces **NO new tuned scalar parameter** — the only change is the V3_MODELS tuple membership. The 14 V3_FEATURE_COLUMNS_TOP_N, all 7 RiskV2 gates, the +2/-1 ATR triple-barrier (K=21), the no_confirm RULE-layer primitive (`enable_no_confirm_exit=True, no_confirm_trigger_atr=0.50, no_confirm_k_candles=4`), the Optuna search space, and the 10-seed unified ensemble lineage are bit-identical to /121.

| Parameter | Value | Provenance |
|---|---|---|
| V3_MODELS candidate 1 | **("v3-125-ATOM", "ATOMUSDT")** | SELECTED via EDA — ATOM has 37 IS months evaluable (LDO incumbent has 6 — candidate exceeds 6× LDO depth); ATOM appeared in /021/033/069/087 *candidate pools* but was NEVER bundled into V3_MODELS. Cosmos L0 ecosystem (vs BCH = Bitcoin-cash L1, TRX = independent L1, LDO = Lido DAO). |
| V3_MODELS candidate 2 | **("v3-125-RUNE", "RUNEUSDT")** | SELECTED via EDA — RUNE has 30 IS months evaluable; RUNE appeared in /083/087 candidate pools but NEVER bundled. THORChain cross-chain DeFi (slip-based pricing, asymmetric liquidity vs incumbent DEX/DAO). |
| V3_MODELS candidate 3 | **("v3-125-UNI", "UNIUSDT")** | SELECTED via EDA — UNI has 30 IS months evaluable; UNI NEVER appeared in any prior v3 candidate pool list. Uniswap governance token (DeFi DEX, distinct from CRV/AAVE/GRT DeFi-protocol cluster tested at /110-111). |
| Bar interval | **8h** | INHERITED from /121. LIFTED-constraints regime permits other choices; 8h chosen per Section 0 rationale (24h NEGATIVE at /117; 4h/12h require fetch). |
| V3_FEATURE_COLUMNS_TOP_N | **14 features (bit-identical to /121 anchor)** | INHERITED from /121 BASELINE_V3.md spec. |
| Triple-barrier K | **21 (=7 calendar days at 8h)** | INHERITED from /121 (labeling-DURATION axis CLOSED bilaterally at /068/124). |
| ATR multipliers | **(2.0, 1.0)** | INHERITED from /121. |
| ENSEMBLE_SIZE | **3 (EXPLORATION mode)** | INHERITED EXPLORATION default per `feedback_v3_outer_seed_cap_2_v3.md`. |
| n_trials | **35** | INHERITED EXPLORATION default per `feedback_v3_exploration_n_trials_35.md`. |

**ZERO tuned scalars in /125.** Every numeric design choice is either inherited from the /121 baseline or naturally bounded by the candidate symbol pool (the V3_MODELS membership is set-valued, not scalar-valued).

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-125/`, commit `a2bd2d6`) was committed in ONE atomic commit BEFORE this brief. The EDA loader (`analysis/iteration_v3-125/wild_universe_eda.py`) asserts `close_time < OOS_CUTOFF_MS = 1742774400000` at every IS-frame extraction. Verified at EDA: 0 OOS-leaked rows across all 6 symbols (3 candidate + 3 anchor for comparison).

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: V3_MODELS UNIVERSE REPLACEMENT BCH/LDO/TRX → ATOM/RUNE/UNI)
- **Cycle 7 slot**: **#4 of 10**. iter-v3/131 is the projected final EXPLORATION (cycle-7 ends with iter-v3/132 CONFIRMATION per the strict 10:1 cadence; `feedback_v3_strict_10_to_1_cadence.md`).
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35` (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per `feedback_v3_outer_seed_cap_2_v3.md`)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md`)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`). Recent EXPLORATIONs at 8h on BCH/LDO/TRX: /122 ~1.05h, /123 ~1.05h, /124 ~1.10h with 3-seed. /125 has different per-symbol Optuna trajectories but the same total per-(sym,month)-cell wall-clock structure; expect ≤ 1.5h with margin.
- **Single axis variation**: V3_MODELS tuple replacement — drop the 3 incumbents BCHUSDT/LDOUSDT/TRXUSDT, replace with 3 new ATOMUSDT/RUNEUSDT/UNIUSDT. Labels, features, gates, ensemble seeds, Optuna search space, /116 no_confirm primitive — ALL bit-identical to /121.

---

## Section 1 — Hypothesis

> Wholesale replacing V3_MODELS BCH/LDO/TRX with the structurally-distinct ATOM/RUNE/UNI universe at 8h cadence (anchored against /121 with /116 no_confirm enabled) carries differentiable directional signal beyond the saturated incumbent distribution, lifting EXPLORATION-mode IS monthly Sharpe by Δ ∈ [−0.30, +0.30] vs the architecturally-adjusted /121 EXPLORATION-mode reference (estimated IS ≈ +1.06) and OOS monthly Sharpe by Δ ∈ [−0.30, +0.40] vs /121 multi-seed OOS +0.9682; OR the WILD UNIVERSE hypothesis — that the /121 baseline's edge structurally generalizes to a never-tested sector-diverse universe — is FALSIFIED at production, narrowing cycle-7's remaining axis space to {NEW non-OHLCV cross-asset features at IC<0.40, RiskV2 untested gate configurations, stateful drawdown brake (deferred Critic Priority 1)}.

**Why a WIDE prediction band ([-0.30, +0.30] IS)**: The /125 axis substitutes 3 NEW symbols whose individual Optuna fit quality on the 14-feature stack is genuinely unknown (no per-symbol baseline exists for ATOM/RUNE/UNI under the /121 architecture). The width reflects honest prior uncertainty: ALL 7 prior universe-replacement attempts have NEGATIVE-or-NEUTRAL outcomes (/021/069/078/083/087/110/111), so the median expectation is around −0.10 IS / −0.10 OOS, BUT the lifted-constraint regime under /121 with no_confirm is a genuinely different prior than the 7 prior attempts (which were all /059-anchored). The band asymmetric upward to +0.30 OOS captures the "no_confirm transforms how alt-coin trades behave" lift-of-hope scenario. The brief explicitly DOES NOT claim PROMISING modal expectation.

---

## Section 2 — IS-Only Numerical Evidence

EDA (`analysis/iteration_v3-125/`, commit `a2bd2d6`): 3 pre-flight gates evaluated against the candidate universe + cross-reference vs anchor universe.

### Section 2.1 — T1 Data Depth Gate

See `analysis/iteration_v3-125/T1_data_depth.csv`:

| Symbol | n_is_bars | first_is_date | training_complete | is_months_evaluable | gate |
|---|---:|---|---|---:|---|
| ATOMUSDT | 5615 | 2020-02-07 | 2022-02-07 | **37** | PASS |
| RUNEUSDT | 4986 | 2020-09-04 | 2022-09-04 | **30** | PASS |
| UNIUSDT | 4944 | 2020-09-18 | 2022-09-18 | **30** | PASS |
| BCHUSDT (anchor) | 5727 | 2020-01-01 | 2022-01-01 | 38 | PASS |
| LDOUSDT (anchor) | 2741 | 2022-09-22 | 2024-09-22 | **6** | n/a |
| TRXUSDT (anchor) | 5669 | 2020-01-15 | 2022-01-15 | 38 | PASS |

**Key finding**: All 3 candidates have 30+ IS months evaluable — comparable to BCH/TRX anchors (38 months) and 5-6× the LDO anchor's mere 6 months. The candidate universe has MORE balanced data-depth across all 3 members than the incumbent universe (where LDO is a 6-month outlier). This supports the "no per-symbol data-poverty cell" prior for the new universe.

### Section 2.2 — T2 Per-Symbol Signal Stats

See `analysis/iteration_v3-125/T2_per_symbol_signal_stats.csv`:

| Symbol | median_rv50_annual | median_kurt50 | median_skew50 | median_abs_ret_1bar_bps |
|---|---:|---:|---:|---:|
| ATOMUSDT | 0.919 | 1.298 | -0.081 | 150.4 |
| RUNEUSDT | 1.210 | 0.990 | 0.028 | 195.2 |
| UNIUSDT | 0.980 | 1.364 | 0.045 | 157.3 |
| BCHUSDT (anchor) | 0.767 | 1.827 | -0.060 | 117.3 |
| LDOUSDT (anchor) | 1.019 | 1.089 | 0.173 | 167.6 |
| TRXUSDT (anchor) | 0.588 | 1.716 | -0.335 | 85.1 |

**Volatility profile**: Candidate universe spans 0.92-1.21 RV50 annualized — slightly HIGHER vol than incumbent universe (0.59-1.02), but well within the same order of magnitude. Higher per-bar return magnitudes (150-195 bps vs incumbent 85-168 bps) imply the +2/-1 ATR triple-barrier will trigger at comparable rates (verified at T6).

**Skewness/kurtosis**: Lower median kurtosis on candidates (0.99-1.36 vs incumbent 1.09-1.83) suggests less fat-tailed distribution — POTENTIALLY favorable for the /121 model's calibration assumptions, though the inverse direction (less tail-event signal) is also possible. The EDA does NOT make a directional claim from these moments.

### Section 2.3 — T3 Pairwise Signal Correlation

See `analysis/iteration_v3-125/T3_pairwise_feature_corr.csv`:

Within-candidate-universe return correlations:
| Pair | ret_corr | rv_corr |
|---|---:|---:|
| ATOM-RUNE | 0.596 | 0.748 |
| ATOM-UNI | 0.631 | 0.737 |
| RUNE-UNI | 0.608 | 0.695 |

**Max within-candidate return correlation = 0.631** (ATOM-UNI). All pairs PASS the G2 gate (< 0.85). Cross-universe correlations (each candidate vs each anchor) span 0.48-0.63 — comparable to within-anchor (BCH-LDO 0.48, BCH-TRX 0.60, LDO-TRX 0.33). The candidate universe is NEITHER more correlated NOR less correlated than the incumbent universe — signal-diversity comparable.

**T3 lesson from /087 brief**: "Price-return correlation is the WRONG metric for signal diversity" (the diversification of per-symbol strategy monthly-PnL streams is what matters). The /125 brief acknowledges this but uses T3 as a pre-flight FIRST-ORDER PROXY — the multivariate per-symbol-strategy correlation cannot be measured pre-backtest. The 0.631 max within-candidate correlation is INFORMATIONAL, not load-bearing for the GO decision.

### Section 2.4 — T4 ADF Stationarity of Incumbent Features

See `analysis/iteration_v3-125/T4_adf_stationarity.csv`:

All 9 incumbent-feature × candidate-symbol pairs PASS ADF (p < 1e-6):

| Symbol | range_realized_vol_50_proxy | ret_kurt_50 | vwap_dev_20_proxy |
|---|---:|---:|---:|
| ATOMUSDT | 1.57e-06 | 2.18e-13 | 2.67e-30 |
| RUNEUSDT | 5.32e-06 | 3.18e-13 | 1.54e-29 |
| UNIUSDT | 9.51e-07 | 1.75e-13 | 5.87e-29 |

**Stationarity gate PASS** — all 3 anchor-feature proxies (3 of the 14 V3_FEATURE_COLUMNS_TOP_N) demonstrate strong stationarity on the candidate symbols. The remaining 11 features will be computed by the same v3 feature pipeline (`process_symbol_v3`) and inherit the same stationarity properties as they exhibited on the incumbents (verified at every prior baseline ADF report).

### Section 2.5 — T5 Volatility-Tier Diversity (universe-level)

See `analysis/iteration_v3-125/T5_vol_regime_diversity.csv`:

Vol-rank across all 6 symbols (1 = highest vol):
| Rank | Symbol | universe | median_rv50_annual |
|---:|---|---|---:|
| 1 | RUNEUSDT | CANDIDATE | 1.210 |
| 2 | LDOUSDT | ANCHOR | 1.019 |
| 3 | UNIUSDT | CANDIDATE | 0.980 |
| 4 | ATOMUSDT | CANDIDATE | 0.919 |
| 5 | BCHUSDT | ANCHOR | 0.767 |
| 6 | TRXUSDT | ANCHOR | 0.588 |

**Candidate universe vol-tier compactness**: RUNE/UNI/ATOM span rv50 ∈ [0.92, 1.21] (range 0.29), while anchor universe spans [0.59, 1.02] (range 0.43). Candidate is MORE vol-clustered (less vol-tier diversity), which means diversification works through sector/microstructure rather than vol regime. The /121 universe's bimodal vol (TRX low, BCH-LDO higher) is REPLACED by a uniform mid-vol universe.

### Section 2.6 — T6 Triple-Barrier Label Distribution Counterfactual

See `analysis/iteration_v3-125/T6_label_distribution_predict.csv`. Past-only +2/-1 ATR K=21 triple-barrier label distribution evaluated on full IS data per symbol:

| Symbol | n_labels | tp_rate | sl_rate | timeout_rate | tp_minus_sl |
|---|---:|---:|---:|---:|---:|
| ATOMUSDT | 5543 | 29.7% | 66.3% | **4.1%** | -36.6% |
| RUNEUSDT | 4914 | 32.0% | 65.2% | **2.8%** | -33.3% |
| UNIUSDT | 4872 | 29.9% | 65.5% | **4.6%** | -35.6% |
| BCHUSDT (anchor) | 5655 | 29.5% | 63.6% | 6.9% | -34.1% |
| LDOUSDT (anchor) | 2669 | 27.5% | 68.8% | 3.8% | -41.3% |
| TRXUSDT (anchor) | 5597 | 34.9% | 58.2% | 6.9% | -23.3% |

**Mechanistic translation**: Triple-barrier label distributions are CONSISTENT across candidate vs incumbent — TP rate 29.7-32.0% (candidate) vs 27.5-34.9% (incumbent); timeout rates 2.8-4.6% (candidate) vs 3.8-6.9% (incumbent). The /121 label-generation mechanism (asymmetric barriers favoring TP-direction trades the model can find) operates in the SAME regime on the candidate universe — the model doesn't need a fundamentally different label statistic to find edge. This is the LOAD-BEARING positive evidence for the WILD universe axis: the triple-barrier mechanism stays calibrated.

**Counter-evidence acknowledgement**: lower timeout rates on candidates (2.8-4.6% vs anchor 3.8-6.9%) may indicate FASTER label resolution — which interacts unpredictably with the /116 no_confirm primitive (K=4 candle exit acceleration). Faster intrinsic label resolution could make no_confirm LESS load-bearing on the candidate universe than on the incumbent. This is a known unknown the production backtest will resolve.

### Section 2.7 — Pre-flight Gate Summary

| Gate | Threshold | Observed | Result |
|---|---|---|---|
| G1 data depth | ≥ 24 IS months per candidate | ATOM 37 / RUNE 30 / UNI 30 | PASS |
| G2 signal diversity | within-candidate max ret_corr < 0.85 | 0.6312 | PASS |
| G3 ADF stationarity | 9/9 feature-symbol pairs p < 0.05 | 9/9 p < 1e-6 | PASS |

**All 3 pre-flight gates PASS** — the axis is QR-cleared for production backtest.

---

## Section 3 — Proposed Changes (single-axis vs /121 baseline)

The /125 EXPLORATION makes ONE production code change:

### Change 1 — V3_MODELS tuple replacement in `run_baseline_v3.py`

Replace (at lines 191-201 of `run_baseline_v3.py`):

```python
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("v3-123-BCH", "BCHUSDT"),
    ("v3-123-LDO", "LDOUSDT"),
    ("v3-123-TRX", "TRXUSDT"),
)
```

With:

```python
V3_MODELS: tuple[tuple[str, str], ...] = (
    # iter-v3/125 WILD CYCLE-7 axis-4: V3_MODELS WHOLESALE REPLACEMENT
    # BCH/LDO/TRX → ATOM/RUNE/UNI under lifted constraints per
    # feedback_v3_cycle7_constraints_lifted.md (2026-05-20 user directive).
    # All other /121 architecture identical — features (14 V3_FEATURE_COLUMNS_TOP_N),
    # labels (+2/-1 ATR K=21), gates (7-gate RiskV2), no_confirm primitive,
    # ensemble (3-seed EXPLORATION), Optuna search space, REQUIRED_GAP=66 — all
    # bit-identical to /121. EDA at analysis/iteration_v3-125/ (commit a2bd2d6).
    # Three DISTINCT model labels so _is_pooled = (len(set(labels)) == 1) is False;
    # three separate LightGbmStrategy instances are built, one per symbol.
    ("v3-125-ATOM", "ATOMUSDT"),
    ("v3-125-RUNE", "RUNEUSDT"),
    ("v3-125-UNI", "UNIUSDT"),
)
```

### Change 2 — ITERATION_LABEL in `run_baseline_v3.py`

Replace `ITERATION_LABEL = "v3-124"` with `ITERATION_LABEL = "v3-125"`.

### Change 3 — pre-flight assertion guard in `run_baseline_v3.py`

The runner has a per-symbol features parquet existence check (around line 1463). If the test framework runs first and detects missing parquets, the runner regenerates them via `process_symbol_v3(sym, "8h", ...)`. The EDA confirms all 3 candidates have raw 8h klines at `data/{ATOM,RUNE,UNI}USDT/8h.csv` — feature parquets at `data/features_v3/{ATOM,RUNE,UNI}USDT_8h_features.parquet` may need first-time generation by the QE.

### Change 4 — V3_FEATURE_COLUMNS_TOP_N count unchanged

Verify at runtime: `len(V3_FEATURE_COLUMNS_TOP_N) == 14`. The pre-flight assertion at runner startup must continue to pass; no feature-column edits are made by /125.

### Change 5 — assertions/tests

No new unit tests required — the /125 axis tests the runner's existing V3_MODELS-loop logic on the new symbol membership. The existing tests in `tests/strategies/ml/test_v3_*.py` are V3_MODELS-membership-agnostic.

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

ZERO `src/` changes. The /125 axis lives ENTIRELY in `run_baseline_v3.py` (Changes 1 + 2 above) and at feature-parquet generation time. The feature pipeline `process_symbol_v3` in `src/crypto_trade/features_v3/__init__.py` is INVARIANT under symbol substitution — it computes the same 14 features regardless of symbol.

QE Phase 6 sequence:
1. Apply Changes 1 + 2 to `run_baseline_v3.py`
2. Generate ATOM/RUNE/UNI feature parquets via `uv run crypto-trade features --symbols ATOMUSDT,RUNEUSDT,UNIUSDT --interval 8h --track v3 --format parquet --workers 3` (1-time generation; ≤ 5min)
3. Run `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof`
4. Verify outputs:
   - `reports-v3/iteration_v3-125/comparison.csv` exists with monthly_sharpe rows
   - `reports-v3/iteration_v3-125/per_symbol` table shows 3 rows (ATOMUSDT, RUNEUSDT, UNIUSDT)
   - No row for BCH/LDO/TRX (confirms full universe replacement, not addition)
   - `ensemble_summary.json` confirms 3-seed EXPLORATION ENSEMBLE_SIZE
5. Write `briefs-v3/iteration_v3-125/engineering_report.md` with the standard sections

---

## Section 4 — Expected OOS Impact (predicted bands) — PER-CRITERION ANCHOR ANNOTATION

Per /122 Critic Rec 3 (PER-CRITERION ANCHOR ANNOTATION), every prediction band declares which anchor it references.

### Section 4.1 — Headline Sharpe Δ bands

| Metric | Anchor A: /121 multi-seed (PUBLIC) | Anchor B: /121 architecturally-adjusted EXPLORATION-mode | Δ band | Mode |
|---|---:|---:|---|---|
| IS monthly Sharpe | +1.3108 | ≈ +1.06 (per /122 brief Section 4.3) | [+1.06 − 0.30, +1.06 + 0.30] = [+0.76, +1.36] | falsifier band |
| OOS monthly Sharpe | +0.9682 | ≈ +0.95 (1-seed compression less material per /122 §4.3) | [+0.95 − 0.30, +0.95 + 0.40] = [+0.65, +1.35] | falsifier band |

Falsifier band classification: anchor B (architecturally-adjusted EXPLORATION-mode estimate).
NEGATIVE-catastrophic classification: anchor A (public /121 multi-seed) — IS Δ < −0.40 or OOS Δ < −0.30 vs /121 multi-seed.

### Section 4.2 — Per-symbol predicted weighted_pnl distribution

Anchor: /121 multi-seed `comparison.csv` per-symbol PnL.

| Symbol (candidate) | Predicted OOS wpnl band | Predicted concentration share | Rationale |
|---|---|---:|---|
| ATOMUSDT | [−15, +25] | 20-45% | NEW symbol; widest band; no prior production data |
| RUNEUSDT | [−15, +25] | 20-45% | Same |
| UNIUSDT | [−15, +25] | 20-45% | Same |

Anchor /121 OOS per-symbol: BCH +35.83 (94%), LDO −2.89 (−8%), TRX +5.21 (14%). NONE of the candidates have prior production benchmark data on the /121 architecture, so per-symbol bands are necessarily WIDE. The brief explicitly DOES NOT predict any single candidate to carry the universe.

### Section 4.3 — EXPLORATION-vs-CONFIRMATION architectural compression note

Per `feedback_v3_dsr_mode_artifact.md` + /122 brief Section 4.3: the EXPLORATION-mode 3-seed run will compress IS Sharpe by ~−0.25 relative to the 10-seed CONFIRMATION baseline through proba-averaging effect alone. The OOS compression is typically less material (~−0.02 per /122 §4.3). The /125 IS band median (centered on +1.06) accounts for this compression; the OOS band median (centered on +0.95) reflects minimal compression.

### Section 4.4 — Pre-registered modal expectation

Per the 7 prior universe-replacement attempts (all NEGATIVE-or-NEUTRAL), the modal expectation for /125 is **NEGATIVE-clean or NEGATIVE-INERT** (IS Δ < +0.05 vs anchor B, OOS Δ < +0.05). The /125 brief acknowledges this prior. The CASE FOR PROMISING is the /121-anchor-with-no_confirm distributional shift: if the no_confirm RULE-layer primitive transforms alt-coin trade exits favorably, the 7-prior-failures prior may NOT generalize to the /125 setup.

**Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)**: the V3_MODELS replacement causes a **100% IS trade-roster substitution** vs /121 — zero trades carry over (the trade-roster is generated by per-symbol model strategies; replacing the 3 symbols replaces every trade). This is the OPPOSITE of a saturated axis (which would show ≈ 0% trade-roster change). Falsifier: if production OOS trade-roster overlap with /121 OOS trade-roster is ≥ 5% by trade-id, the V3_MODELS substitution was incomplete (engineering defect — diagnose at Phase-8 roster diff).

---

## Section 5 — Risk Mitigation

The /125 axis introduces NO new risk mitigation primitive — the 7-gate RiskV2 stack (vol scaling, ADX, Hurst, z-score OOD, low-vol filter, hit-rate OOS, BTC trend) + the /116 no_confirm RULE-layer primitive are bit-identical to /121.

**Risk-of-risk-mitigation-incompatibility**: each RiskV2 gate was IS-calibrated on incumbent BCH/LDO/TRX distributions. Whether the same gate thresholds (e.g., ADX-25, Hurst-band, z-score-2.5) are properly calibrated for ATOM/RUNE/UNI distributions is UNKNOWN. The /125 EXPLORATION may surface miscalibration symptoms:
- If gates trigger LESS frequently on candidates → lower trade rate, higher per-trade edge potentially
- If gates trigger MORE frequently on candidates → fewer trades, lower trade-rate-floor compliance risk

**No new mitigation gate is introduced because** the wild-axis hypothesis is "universe substitution alone is the structural change worth testing"; introducing a 2nd axis (gate recalibration) would violate single-axis discipline. If /125 produces NEGATIVE on per-symbol gate-trigger asymmetry, /126 would be the recalibration follow-up.

---

## Section 6 — Risk Management Design

### Section 6.1 — Drawdown caps

The /121 multi-seed baseline IS MaxDD = 26.4%, OOS MaxDD = 25.7%. The /125 universe is vol-tier-comparable; expected MaxDD band [20%, 50%] — wide because new symbols' drawdown distributions are unknown. NEGATIVE-catastrophic threshold: OOS MaxDD > 50% AND OOS Sharpe < +0.50 = filed CATASTROPHIC.

### Section 6.2 — Concentration caps

Anchor /121 OOS concentration: BCH 93.92% (extreme single-symbol dominance). Predicted /125 concentration band [20%, 60%] per symbol (uncertain). NEGATIVE-catastrophic concentration threshold: any single candidate symbol > 80% OOS concentration AND OOS Sharpe < +0.50 = filed CONCENTRATION-RISK-MATERIALIZED.

### Section 6.3 — Trade-rate floor

Anchor /121 OOS trades = 98. Predicted /125 OOS trades band [50, 200]. Per `feedback_v3_trade_rate_floor_bundle_level.md` carry-forward from /121 brief Section 4: trade-rate floor (≥ 130 OOS) is INFORMATIONAL at EXPLORATION; falsifier-triggered only at CONFIRMATION-spec.

### Section 6.4 — Stateful state for /116 no_confirm

The no_confirm primitive operates per-symbol-trade — substituting the universe does NOT create stateful state issues. Each per-symbol LightGbmStrategy instance carries its own no_confirm state machine.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Modal failure modes the /125 axis can produce, with falsifier-triggered classifications:

1. **F1: Universe-substitution NEGATIVE-clean** (IS Δ ∈ [-0.05, +0.05] AND OOS Δ ∈ [-0.05, +0.05])
   - Mechanism: new universe doesn't carry more edge than incumbent at this architectural stack
   - Diagnosis at Phase 8: per-symbol edge attribution comparable to /121's BCH-dominant structure but with different carrier symbol; close axis as "wild universe didn't change the binding constraint"

2. **F2: Single-symbol-carrier replication** (1 of 3 candidates carries > 80% concentration; other 2 contribute < 10% each)
   - Mechanism: same structural pattern as /121 (1-symbol-carrier; 2-symbol-drag) but with different carrier
   - Diagnosis at Phase 8: classify by which symbol carries; lesson "the binding constraint is the SHAPE not the SYMBOLS" → /126 should explore architectural changes rather than universe

3. **F3: Sector cross-contamination NEGATIVE-catastrophic** (IS Δ < −0.40)
   - Mechanism: cross-correlation between candidates is HIGHER under production than the 0.60-0.63 ret_corr EDA estimate suggested; all 3 trade together against the model
   - Diagnosis: cross-sectional Spearman rank of per-symbol PnL vs incumbent; if all 3 candidates' monthly PnL stream correlation > 0.8, sector-cross-contamination confirmed

4. **F4: OOS-spike SUSPICIOUS** (IS Δ < 0 AND OOS Δ > +0.30)
   - Mechanism: the /082/085/086 pattern in a NEW class — universe substitution creates OOS lottery without IS confirmation
   - Diagnosis: per /082 closeout convention, sub-channel diagnosis at Phase-8 roster-diff

5. **F5: Single-candidate breakthrough PROMISING-PARTIAL** (1 of 3 candidates IS+OOS > +0.20)
   - Mechanism: ONE candidate (e.g., ATOM) has structural edge on the 14-feature stack the others don't
   - Diagnosis: classify per /122 PROMISING-PARTIAL convention; the single-symbol-carrier could be promoted to /126 single-symbol-V3_MODELS axis

6. **F6: Universe-substitution PROMISING-strong** (IS Δ > +0.10 AND OOS Δ > +0.10)
   - Mechanism: /121-anchor-with-no_confirm distributional shift transforms alt-coin trades favorably; the 7-prior-universe-NEG prior is BROKEN
   - Bundle candidate for /132 CONFIRMATION

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria — PER-CRITERION ANCHOR ANNOTATION

Per /122 Critic Rec 3, every criterion declares its anchor explicitly (PUBLIC = /121 multi-seed; ADJUSTED = /121 architecturally-adjusted EXPLORATION-mode reference).

### NEGATIVE criteria (any-of-the-below; first-match wins)

1. **NEGATIVE-catastrophic** — Anchor: PUBLIC. IS Sharpe Δ < −0.40 vs /121 multi-seed +1.3108 (i.e., IS < +0.91) OR OOS Sharpe Δ < −0.30 vs /121 multi-seed +0.9682 (i.e., OOS < +0.67). File EXPLORATION-NEGATIVE-catastrophic. Axis-CLOSE recommendation: V3_MODELS universe-replacement axis CLOSED for ATOM/RUNE/UNI combination.

2. **NEGATIVE-no-effect** — Anchor: PUBLIC. IS Sharpe Δ ∈ [−0.05, +0.05] vs /121 multi-seed AND production OOS trade-roster overlap with /121 OOS > 95% (per Section 4.4 falsifier; this should be 0% under correct universe substitution) → ENGINEERING DEFECT, not signal verdict; restart Phase 6.

3. **NEGATIVE-INERT** — Anchor: ADJUSTED. IS Sharpe Δ ∈ [−0.20, +0.05] vs /121 architecturally-adjusted estimate +1.06 (i.e., IS ∈ [+0.86, +1.11]) AND OOS Sharpe Δ < +0.05 vs /121 multi-seed +0.9682 (i.e., OOS < +1.02). File EXPLORATION-NEGATIVE-INERT (the wild universe didn't substantively change the binding constraint).

4. **NEGATIVE-clean** — Anchor: ADJUSTED. IS Sharpe Δ ∈ [+0.05, +0.10] vs /121 ADJUSTED AND OOS Sharpe Δ ∈ [−0.20, +0.05] vs /121 PUBLIC (NEGATIVE on either leg). File EXPLORATION-NEGATIVE-clean.

5. **SUSPICIOUS-OOS-DOMINANT** — Anchor: PUBLIC. OOS Sharpe Δ > +0.30 vs /121 multi-seed (i.e., OOS > +1.27) AND IS Sharpe Δ ∈ [−0.10, +0.05] vs /121 PUBLIC (IS ∈ [+1.21, +1.36]). File SUSPICIOUS-OOS-DOMINANT per /082/085/086 closeout convention.

### PROMISING criteria (all-of-the-below)

6. **PROMISING-strong** — Anchor: PUBLIC. IS Sharpe Δ ≥ +0.10 vs /121 ADJUSTED estimate +1.06 (i.e., IS ≥ +1.16) AND OOS Sharpe Δ ≥ +0.10 vs /121 PUBLIC +0.9682 (i.e., OOS ≥ +1.07) AND OOS trade-roster overlap with /121 < 5% (correct universe substitution; per Section 4.4) AND no candidate symbol > 80% concentration → file EXPLORATION-PROMISING-strong. Bundle candidate for /132 CONFIRMATION.

7. **PROMISING-PARTIAL** — Anchor: PUBLIC. Only 1 of 3 candidates carries IS PnL Δ > +5pp AND OOS PnL Δ > +3pp; the other 2 individually have wpnl ∈ [−5, +5] → file EXPLORATION-PROMISING-PARTIAL. The carrier candidate may be promoted to /126 single-symbol-V3_MODELS axis.

8. **PROMISING-MECHANICAL (universe variant)** — Anchor: PUBLIC. IS Sharpe Δ ≥ +0.10 vs /121 ADJUSTED AND OOS Sharpe Δ ≥ +0.10 vs /121 PUBLIC AND ALL 3 candidates IS+OOS positive (broad-based lift) AND trade-rate Δ vs /121 ∈ [+50%, +200%] (mechanical trade-rate-driven, not signal-driven). File PROMISING-MECHANICAL per `feedback_v3_promising_feature_mechanical.md`. Non-compoundable; non-bundle.

### Anchor restatement

- **Anchor A = PUBLIC** = /121 multi-seed CONFIRMATION-MERGE baseline (IS +1.3108 / OOS +0.9682). Public BASELINE_V3.md numbers.
- **Anchor B = ADJUSTED** = /121 architecturally-adjusted EXPLORATION-mode estimate (IS ≈ +1.06 / OOS ≈ +0.95). Per /122 brief §4.3 architectural-compression adjustment factor −0.25 IS / −0.02 OOS for EXPLORATION-mode 3-seed vs CONFIRMATION-mode 10-seed.
- NEGATIVE-catastrophic and SUSPICIOUS-OOS-DOMINANT use PUBLIC anchor (production-facing).
- NEGATIVE-INERT, NEGATIVE-clean, PROMISING-strong, PROMISING-MECHANICAL use ADJUSTED anchor for IS leg (architectural correction) and PUBLIC anchor for OOS leg (minimal architectural compression).

---

## Section 9 — Library Stack Declaration

**No new library dependencies** — V3_MODELS tuple substitution requires zero new imports. The `process_symbol_v3` pipeline + 14-feature `V3_FEATURE_COLUMNS_TOP_N` are V3_MODELS-membership-agnostic.

**Library inventory** (verified at /125):
- `lightgbm == 4.6.0` (unchanged from /121)
- `numpy >= 2.0` (unchanged)
- `pandas >= 2.2` (unchanged)
- `scikit-learn` (used only in EDA, not in production runner)
- No `statsmodels` / `optuna` / `pyarrow` version change
- `statsmodels` used in EDA for ADF test (already installed; ADF infrastructure in `analysis/iteration_v3-125/wild_universe_eda.py`)

**Adversarial integration test** (per `feedback_v3_methodology_axis_integration_test.md`): the Change 1 edit + Change 2 ITERATION_LABEL change + Change 3 feature-parquet generation must satisfy the following:
- `V3_MODELS == (("v3-125-ATOM", "ATOMUSDT"), ("v3-125-RUNE", "RUNEUSDT"), ("v3-125-UNI", "UNIUSDT"))` (3-tuple, byte-identical)
- `set(sym for _, sym in V3_MODELS) ∩ set(V3_EXCLUDED_SYMBOLS) == ∅` (disjointness assertion; existing assertion in `features_v3/__init__.py` lines 706-716 must continue to pass)
- `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (no inadvertent feature additions)
- Feature parquets exist at `data/features_v3/ATOMUSDT_8h_features.parquet`, `data/features_v3/RUNEUSDT_8h_features.parquet`, `data/features_v3/UNIUSDT_8h_features.parquet` after Phase 6 step 2
- Each candidate parquet contains all 14 V3_FEATURE_COLUMNS_TOP_N columns + non-NaN values on the last 100 IS rows
- `run.log` shows 3 per-symbol model training blocks labeled `v3-125-ATOM`, `v3-125-RUNE`, `v3-125-UNI` (no `[POOLED]` marker; 3 distinct labels enforce per-symbol path)
- `comparison.csv` `# per_symbol` rows = 3, with symbols ATOMUSDT/RUNEUSDT/UNIUSDT

---

## Section 10 — QR Audit Trail

### Section 10.1 — Wild-axis brainstorming

The user's 2026-05-20 directive: "Make the QR create innovations. Do not follow always the playbook. Try something wild." The QR brainstormed 7 distinct WILD axis classes:

1. **NEW universe at 8h** (selected) — see Section 10.2 rationale
2. **NEW universe at 24h** — REJECTED: /117 NEGATIVE catastrophic precedent on BCH/LDO/TRX; risk that 24h cadence is structurally adverse regardless of universe
3. **NEW universe at 4h or 12h** — REJECTED: data NOT in worktree; fetch risk exceeds 2h cap
4. **Memecoin / sentiment-coin universe at any cadence** — REJECTED: WIF/JTO/1000PEPE/1000BONK all have < 24 IS months evaluable (first data dates 2023-12 to 2024-03)
5. **Multi-frequency feature stack** (4h base + 24h aggregated features) — REJECTED: requires architectural changes beyond single-axis discipline; risk of axis-conflation
6. **Single-symbol intensive V3_MODELS** (e.g., BCH-alone at 4h with K=11 labels) — REJECTED: violates v3 mandate (BASELINE_V3.md trade-rate-floor + concentration cap heuristic); 1-symbol universe = 100% concentration by construction
7. **Concentration-resistant universe selected by negative BTC correlation** — DEFERRED: the per-symbol negative-BTC-correlation screen is itself a 1-axis variation that may interact with the universe-substitution axis (cycle-2 lesson at /087 brief)

### Section 10.2 — Why ATOM + RUNE + UNI specifically

| Symbol | Sector | First IS date | IS months | OOS months | Prior v3 status |
|---|---|---|---:|---:|---|
| ATOMUSDT | Cosmos L0 hub | 2020-02-07 | 37 | 14 | NEVER in V3_MODELS (only in /021/033/069/087 candidate pools) |
| RUNEUSDT | THORChain cross-chain DeFi | 2020-09-04 | 30 | 14 | NEVER in V3_MODELS (only in /083/087 candidate pools) |
| UNIUSDT | Uniswap governance | 2020-09-18 | 30 | 14 (data ends 2026-02-28) | NEVER in any v3 candidate pool list |

Selection criteria applied (in order):
1. **Data depth ≥ 24 IS months AND ≥ 10 OOS months**: filters out memecoins (WIF/JTO/etc. all < 24 IS mo) and recent alts (ARB has 0 IS mo, FET 2, APT 5).
2. **Disjoint from V3_EXCLUDED_SYMBOLS**: BTC/ETH/LINK/LTC/DOT/BNB/SOL/XRP/DOGE/NEAR/MKR all excluded; candidates pass.
3. **NEVER in prior V3_MODELS bundle**: filters out BCH/LDO/TRX (incumbents), HBAR/AVAX (/021), ADA (/069/078), FIL (/083), GALA/MANA/SAND (/087), CRV/AAVE/GRT (/110-111).
4. **Sector diversity**: avoid all-same-class clusters (e.g., all DeFi /110-111 attempt with 4 DeFi tokens FAILED). Choose 1 from each of L0/cross-chain-DeFi/DeFi-governance sectors.
5. **Highest data depth among remaining candidates**: ATOM (37), RUNE (30), UNI (30) are the top-3 by IS depth from the surviving pool. Honorable mentions UNI 30 vs HBAR 24 — HBAR rejected per criterion 3 (closed at /021).

### Section 10.3 — What this WILD axis taps that prior universe axes didn't

| Prior universe axis | Anchor baseline | Sector class | Wild-axis-distinct? |
|---|---|---|---|
| /021 HBAR+AVAX add | /018 BOOTSTRAP | L1 (both) | NO — sector-monoculture, /059-anchored |
| /069 ADA add | /068 (CLOSED) | DeFi/L1 hybrid | NO — single add, /059-anchored |
| /078 BCH/ADA/TRX | /059 | Mixed | NO — partial swap, /059-anchored |
| /083 +FIL | /059 | Storage | NO — single add, /059-anchored |
| /087 +GALA/MANA/SAND | /059 | Gaming (all 3) | NO — sector-monoculture, /059-anchored |
| /110-111 CRV/AAVE/GRT/ADA | /059 | DeFi-DEX/lending/indexing (3 DeFi) | NO — sector-monoculture, /059-anchored |
| **/125 ATOM/RUNE/UNI** | **/121 (no_confirm enabled)** | **L0+cross-chain+DEX-gov (3 sectors)** | **YES — sector-diverse, /121-anchored with no_confirm** |

The PRIOR-NOT-YET-TESTED distribution: **P(wild universe edge | /121 no_confirm baseline AND never-V3_MODELS-bundled symbols AND sector-diverse pick)**. All 7 prior universe attempts violated at least 2 of these 3 conditions; /125 is the first to satisfy all 3.

### Section 10.4 — Why this beats Critic Priority 1 (drawdown brake) for cycle-7 slot 4

The /124 closeout designated Critic Priority 1 = stateful drawdown brake. Why /125 elects WILD universe instead:

1. **User directive explicit**: 2026-05-20 directive overrides Critic Priorities — "BE WILD, INVENT INNOVATION".
2. **Drawdown brake risk**: /054 precedent of permanent deadlock; closed-loop simulator is high-cost EDA artifact; the deadlock-impossibility-proof methodological gate is itself an uncertain pre-flight requirement.
3. **Universe axis lower methodological risk under LIFTED constraints**: substituting V3_MODELS is a 2-line code change in the runner; no new methodology, no new gate.
4. **Drawdown brake addresses BCH 95.76% concentration**, but if the WILD universe RESOLVES the concentration through sector-diversity, the drawdown brake becomes redundant; /125 is a structurally prior question (does sector diversity solve concentration?) than the drawdown brake (how to clamp concentration when it materializes?).
5. **/124 Critic Priority 1 not displaced**: if /125 produces NEGATIVE on concentration grounds (F2 or F3 from Section 7), /126 can pivot to drawdown brake. Sequential exploration of orthogonal axes.

### Section 10.5 — Pre-registered prior probability statement

The QR pre-registers the prior probability mass for the outcome classes (Section 8):

| Outcome class | Prior probability (subjective) | Rationale |
|---|---:|---|
| NEGATIVE-catastrophic (F1 IS Δ < −0.40 OR OOS Δ < −0.30) | 25% | 7 prior universe attempts: 0 PROMISING, mix of catastrophic + clean |
| NEGATIVE-clean / NEGATIVE-INERT | 50% | Modal expectation; matches prior-7 universe distribution |
| SUSPICIOUS-OOS-DOMINANT | 10% | /082/085/086 pattern can recur in any class |
| PROMISING-PARTIAL (single-candidate carrier) | 8% | Plausible if 1 candidate has unique structural edge |
| PROMISING-MECHANICAL (mechanical-trade-rate) | 4% | Plausible if no_confirm transforms alt-coin trades |
| PROMISING-strong (broad-based IS + OOS lift) | 3% | Low prior given 7 prior universe failures, but non-zero |

The MODAL prediction is NEGATIVE-clean/INERT. The CASE for proceeding despite low PROMISING prior: (a) cycle-7 axis menu severely constrained after /122/123/124 closures, (b) the user mandate to "BE WILD" carries epistemic value beyond expected SR lift, (c) the /125 outcome — even if NEGATIVE — narrows the cycle-7 axis space and informs /126-/131 axis selection.

---

**End of brief**.

**EDA SHA**: `a2bd2d6` (analysis/iteration_v3-125/)
**Brief SHA**: (set by commit)
**Anchor**: /121 BASELINE_V3.md (IS +1.3108 / OOS +0.9682)
**Cycle-7 cadence**: EXPLORATION #4 of 10 → /132 CONFIRMATION pending
