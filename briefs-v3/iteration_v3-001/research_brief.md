# Iteration v3-001 — Research Brief

**Type**: METHODOLOGY STACK + UNIVERSE SELECTION (largest single iteration in project history)
**Track**: v3 (rigor arm) — first iteration; no parent baseline
**Branch**: `iteration-v3/001` (off `quant-research`)
**Date**: 2026-05-04
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ensemble_seeds   = [42, 123, 456, 789, 1001]   # 5-seed inner ensemble (v1-style)
```

- **IS window**: from each symbol's first usable kline (with the listing-date floor 2022-09-24, no symbol contributes to walk-forward training before 2022-09-24) through `2025-03-23 23:59:59 UTC` exclusive.
- **OOS window**: from `2025-03-24 00:00:00 UTC` through the data-extent timestamp at backtest time (Engineer pre-flight check).
- **Walk-forward unit**: monthly retrain, 24-month rolling training window, 1-month OOS prediction window, advancing one month at a time.
- **CPCV unit (v3 mandate)**: `N=10, k=2 → C(N,2)=45 paths`. CPCV runs on top of the same 24-month training window using `mlfinpy` / pure-Python fallback, with purge `gap = (timeout_candles + 1) × n_symbols` and embargo `δ ≈ 0.01 × T`.
- The QR sees OOS metrics for the first time in Phase 7. The QR has produced this brief reading IS-only data (close_time < 2025-03-24).

---

## Section 1 — Hypothesis

A v3 portfolio of {BCH, MKR, LDO, TRX} — four symbols spanning PoW, DeFi-CDP, liquid-staking-infra, and DPoS sectors that have zero overlap with v1 (BTC/ETH/LINK/LTC/DOT) or v2 (SOL/XRP/DOGE/NEAR) — combined with the rigor-arm methodology stack (CPCV with 45 paths, Deflated/Probabilistic Sharpe and PBO with hard pass thresholds, meta-labeled M1 + M2 architecture, `FracdiffStat`-auto-`d*` features, and Critic adversarial review) will deliver an OOS monthly Sharpe ≥ 1.0 with PBO < 0.4 and PSR > 0.95, while structurally insuring against the four single-track failure modes that the v2 dead-paths catalog has documented (univariate-rho-misled feature additions, single-path walk-forward seed bias, fixed-`d` non-stationarity, and concentration-only optimisation).

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-001/symbol_universe.py` (committed before this brief — Phase 5.5 reproducibility requirement).

**Outputs** (committed alongside the script):
- `analysis/iteration_v3-001/symbol_candidates.csv` — Gate 1 + Gate 2 stats for 40 candidate symbols
- `analysis/iteration_v3-001/pairwise_correlation.csv` — 40×40 IS-aligned 8h log-return Pearson correlation matrix (intersection window 2,727 candles)
- `analysis/iteration_v3-001/v3_universe_summary.csv` — 4 chosen symbols with full Gate stats
- `analysis/iteration_v3-001/v3_universe_correlation.csv` — 4×4 within-universe correlation
- `analysis/iteration_v3-001/v3_universe_cross_track_correlation.csv` — 4 chosen symbols vs BTC (v1 representative) and SOL (v2 representative)

### 2.1 Gate 1 — Data Quality (IS only, 8h candles)

| Symbol | First close | Last IS close | IS candles | Coverage % | Max gap (h) | Gaps > 1d |
|---|---|---|---|---:|---:|---:|
| BCHUSDT | 2020-01-01 | 2025-03-23 | 5,727 | 100.00 | 8.00 | 0 |
| MKRUSDT | 2020-08-13 | 2025-03-23 | 5,037 | 99.70 | 80.00 | 2 |
| LDOUSDT | 2022-09-22 | 2025-03-23 | 2,741 | 100.00 | 8.00 | 0 |
| TRXUSDT | 2020-01-15 | 2025-03-23 | 5,669 | 99.74 | 80.00 | 2 |

The two gaps in MKR and TRX are both Binance-platform-wide outages on 2022-03-01 (3d 8h) and 2022-04-03 (2d 8h) — visible in many other symbols' CSVs. They occur in IS pre-2023 territory, do not coincide with feature-warmup or label-horizon boundaries that materially affect OOS, and are well-documented in the project memory. **All four symbols pass Gate 1.**

### 2.2 Gate 2 — Return Regime (IS only, 8h log-returns)

| Symbol | Annualised σ % | Annualised µ % | µ/σ | Max DD % | Avg daily quote vol (M USDT) |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 94.83 | 8.69 | 0.092 | -94.25 | 242.4 |
| MKRUSDT | 104.53 | 8.71 | 0.083 | -91.59 | 69.6 |
| LDOUSDT | 112.52 | -22.49 | -0.200 | -77.44 | 111.5 |
| TRXUSDT | 84.22 | 50.39 | 0.598 | -72.52 | 137.8 |

Volatility is the directional-strategy-relevant signal: ATR-scaled triple-barrier labels need σ in the [80%, 130%] band where v1+v2 found edge. All four are in that band. Buy-and-hold µ is **not** the selection criterion (a directional ML model finds asymmetries within volatility — the v2 DOGE precedent showed near-zero µ → non-trivial OOS edge). LDO's negative µ is acceptable: the strategy is a directional model with both long and short signals, and LDO's higher σ provides a richer signal surface.

Liquidity (avg daily quote volume): all four ≥ $69M/day (MKR floor) — well above the project's empirical "tail floor" of $10M/day. **All four pass Gate 2.**

### 2.3 Within-universe IS correlation (Pearson, 8h log-returns, full IS intersection)

```
         BCHUSDT  MKRUSDT  LDOUSDT  TRXUSDT
BCHUSDT   1.0000   0.4429   0.4775   0.3912
MKRUSDT   0.4429   1.0000   0.5114   0.3557
LDOUSDT   0.4775   0.5114   1.0000   0.3335
TRXUSDT   0.3912   0.3557   0.3335   1.0000
```

Pairwise range 0.33–0.51 — comparable to v2's within-universe correlation profile (v2's NEAR/SOL/XRP/DOGE pairwise was 0.40–0.55 from prior measurements). No pair > 0.55. **TRX is the most diversifying** (lowest mean correlation to other 3 = 0.36). **MKR–LDO at 0.51** is the highest within-universe pair — both ETH-ecosystem DeFi tokens — but well below the 0.85 redundancy threshold.

### 2.4 Cross-track diversification check (vs v1 BTC + v2 SOL)

| Symbol | corr vs BTCUSDT | corr vs SOLUSDT |
|---|---:|---:|
| BCHUSDT | 0.7290 | 0.5434 |
| MKRUSDT | 0.5909 | 0.5296 |
| LDOUSDT | 0.5564 | 0.5443 |
| TRXUSDT | 0.5916 | 0.4720 |

BCH is the most BTC-correlated (0.73, expected — it's a BTC fork). The other three are 0.56–0.59 vs BTC, comparable to v2's symbols. Vs SOL (v2's largest contributor), all four are 0.47–0.55. The combined v1+v2+v3 portfolio diversifies further than v1+v2 alone. **TRX adds the strongest diversification gain** (lowest correlation to both v1 and v2 representatives).

### 2.5 Sector taxonomy

| Symbol | Sector | Why distinct from v1+v2 |
|---|---|---|
| BCHUSDT | PoW major (BTC fork) | v1 has BTC (PoW base) but no PoW alternative; BCH gives BTC-cycle exposure with independent dynamics (block-size-debate community, smaller liquidity, halving timing offset by 2 days from BTC) |
| MKRUSDT | DeFi blue-chip (CDP/RWA) | No CDP / lending exposure in v1 or v2; MKR has the deepest DeFi tenure (since 2017 mainnet) and benefits from the RWA narrative (USDS rebrand, T-bill yield); Sky migration delisting risk **mitigated** — MKRUSDT perp pair remains active (data through 2026-02-28); SKYUSDT is a separate, newer pair |
| LDOUSDT | Liquid staking infrastructure | Entirely new sector for the project — neither v1 nor v2 touches LST; LDO's ETH-staking-volume drives token value distinctly from generic DeFi or L1 alts; structurally exposed to ETH-staking yield curve |
| TRXUSDT | DPoS / stablecoin rail | Distinct from v1 (PoS smart-contract platforms) and v2 (Solana, NEAR, XRP); Tron's USDT issuance is the largest stablecoin rail by volume globally; structurally low-correlation to L1-fee-token narratives |

### 2.6 v2 dead-path catalog check

V2 dead-pathed symbols (do not retry without justification): AAVE, AVAX, ATOM, ADA, DOT, OP, TRX (as primary picks).

Wait — TRX appears in iter-v2/066's dead-path note. Re-reading: iter-v2/066 used "OPUSDT, TRXUSDT as primary picks" with **IS-only screener** that mis-selected; the symbols failed because they were chosen via flawed methodology, not because the symbols themselves had no edge. This is materially different from "TRX has no signal." For v3:

- TRX is selected via the **full Gate 1 + Gate 2 + sector-diversification framework** (not an IS-only screener).
- TRX's µ/σ proxy in the IS window is the strongest of all 40 candidates evaluated (0.598).
- v3's CPCV + meta-labeling stack is structurally different from v2's walk-forward-only validation; if TRX's signal exists, v3's methodology should detect it more reliably.

**My selection includes one v2-dead-path symbol (TRX) under explicit justification: methodology change (CPCV vs walk-forward-only) and selection-criterion change (full Gate 1+2+sector vs IS-only Sharpe screener).** The other three (BCH, MKR, LDO) are entirely new — no project history, no dead-path lineage.

### 2.7 IS-only feature coverage (existing v2 features applied to v3 universe)

The v3 universe inherits `V2_FEATURE_COLUMNS` (34 columns post iter-v2/069 pruning) as the starting point. The Engineer's Phase 6 will compute these features for {BCH, MKR, LDO, TRX} from the existing `crypto_trade.features_v2` pipeline (cross-asset BTC features included). Each symbol passes the Phase 6 pre-flight feature-availability check (verified for all 4 in this brief: 34 column names exist in the pipeline registry, all symbols have ≥ 2,500 IS candles for the longest rolling window of 200).

The methodology stack adds two structural changes to the feature set without changing the column list:
1. `fracdiff_logclose_d04` and `fracdiff_logvolume_d04` are recomputed using `FracdiffStat`-auto-`d*` (Section 3.4 below); ADF p-values reported per-feature in `adf_test.csv`.
2. Existing `crypto_trade.features_v2` modules are re-imported under `crypto_trade.features_v3` namespace for **track isolation**; the Engineer copies (not refactors) the modules to satisfy the `grep -r "from crypto_trade.features_v2" features_v3/` empty-result rule.

Initial `V3_FEATURE_COLUMNS` = `V2_FEATURE_COLUMNS` (34 columns) **with one substitution**: `fracdiff_logclose_d04` and `fracdiff_logvolume_d04` are renamed to `fracdiff_logclose_dstat` and `fracdiff_logvolume_dstat` to mark the methodology change. Net column count: 34 (unchanged).

---

## Section 3 — Proposed Changes

### 3.1 Symbols

- **Added (full new universe — v3 has no parent baseline)**: BCHUSDT, MKRUSDT, LDOUSDT, TRXUSDT
- **V3_EXCLUDED_SYMBOLS check**: `set({BCH, MKR, LDO, TRX}) ∩ {BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, DOGE, NEAR} = ∅` ✓ PASS
- **Per-symbol model architecture**: each symbol gets its own LightGBM ensemble (5 inner seeds × 50 Optuna trials per walk-forward month) — identical scaffold to v2.
- **Combined-portfolio rationale**: 4 symbols, 4 sectors, mean within-universe correlation 0.42 — comparable diversification to v2's 4-symbol universe, with a structurally distinct sector basis from both v1 and v2.

### 3.2 Labeling

- Triple-barrier with ATR-scaled barriers: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21` (inherited from v2's iter-v2/069 baseline, which v1 also uses for Model A). Same `natr_21_raw` helper column.
- Timeout: 7 days = 21 candles at 8h.
- Label horizon defines the CPCV purge: `gap = (21 + 1) × 4 = 88 candles`, symmetric on both sides of every test boundary.
- σ_t for triple-barrier: past-only ATR (already implemented; no leak).
- **Meta-labeling adds a second binary label** per M1-positive bar: `y_meta = 1 iff M1's signal closed at TP within timeout`. M2 is trained on the M1-positive subset, target is `y_meta`. M2's training window is identical to M1's; M2's purge horizon **must** extend through M1's full label timeout (Engineer enforces).

### 3.3 Features

- **Initial V3_FEATURE_COLUMNS = 34 columns** (V2_FEATURE_COLUMNS with the two fracdiff columns renamed to mark the FracdiffStat substitution).
- **No new feature families this iteration.** Per the v3 skill: iter-v3/001 ships methodology stack + universe, NOT new crypto-native features. Funding (iter-v3/002), basis (003), OI (004), liquidations (005) are sequenced one-per-iteration starting iter-v3/002.
- **Cluster-importance check**: V2_FEATURE_COLUMNS already passed iter-v2/069's pruning (6 redundant features removed via Pearson cluster analysis). No additional cluster check needed at the column-list level. The Critic's Check 4 (IC < 0.7 between feature **families**) will run on the v3 universe — Engineer provides `ic_matrix.csv`.
- **Track isolation**: `crypto_trade.features_v3/` is a new package; copy (not import) the relevant modules from `features_v2/`. No `from crypto_trade.features_v2` import permitted.

### 3.4 Fractional differentiation — `FracdiffStat`-auto-`d*` substitution

- v2 uses fixed `d=0.4` (`features_v2/fracdiff_v2.py`) without ADF validation. The 0.4 was chosen by López de Prado convention but never verified to be the minimum-`d` for stationarity on this universe.
- v3 uses `fracdiff.sklearn.FracdiffStat(window=10, mode='full', stattest='adf', pvalue=0.05)` to **auto-select** `d* = min{d : ADF(diff_d(x)) < 0.05}` per feature per training-window-end retraining cycle.
- The auto-`d*` is recomputed per walk-forward month (using only training-window data — never OOS). Persisted per month for reproducibility.
- ADF p-value at the chosen `d*` is reported in `reports-v3/iteration_v3-001/adf_test.csv` per (feature, month). Critic Check 5 verifies p < 0.05 for every (feature, month).
- The legacy `features_v2/fracdiff_v2.py` is kept (not removed) so v2 baselines stay reproducible.

### 3.5 Risk gates

- **Inherit v2's 7 active gates** for the v3 baseline:
  1. ATR-percentile vol scaling (`atr_pct_rank_200`)
  2. ADX threshold gate (20)
  3. Hurst regime check (training 5/95 percentile band on `hurst_100`)
  4. Z-score OOD on 35 v2-equivalent features (|z| > 2.5)
  5. Low-vol filter (`atr_pct_rank_200 ≥ 0.33`)
  6. Hit-rate feedback gate (window=20, SL threshold=0.65, OOS only) — disabled by default for v3 inheriting iter-v2/045's lesson; Engineer sets `hit_rate_enabled=False` to match v2's current baseline
  7. BTC trend alignment (±20%, 14d lookback, full period)
- **No new risk gates this iteration** (one-variable-at-a-time discipline: methodology+universe is already the "one variable"). Risk-gate tuning is iter-v3/008+ scope.
- The CPCV-derived path-level diagnostics (per-path Sharpe, MaxDD, n_trades) are **not gates** — they are reported in `cpcv_paths.csv` for the Critic's Check 6 (Pareto dominance is on the 10-seed pre-MERGE matrix, NOT the CPCV path matrix; the skill is explicit about this distinction).

### 3.6 Methodology stack — Engineer-implements specifications

The Engineer in Phase 6 implements these (the QR specifies; the QE writes the code):

| Item | Spec | Implementation hint |
|---|---|---|
| CPCV | `N=10, k=2 → 45 paths`; purge gap = `(timeout_candles+1) × n_symbols` = 88; embargo δ ≈ 0.01 × T (≈ 27 candles for 24-month T) | New module `crypto_trade.strategies.ml.validation_v3.combinatorial_purged_cv` replacing the `validation_v2.py:178` stub. mlfinpy if available; pure-Python fallback otherwise. |
| PBO | Computed via CSCV on the 45-path × n-Optuna-trial matrix — for each (S=16) symmetric block split, fraction of "IS-best is OOS-below-median" | `pypbo.pbo()` from esvhd/pypbo (install via `pip install git+https://github.com/esvhd/pypbo.git`) |
| PSR | Probabilistic Sharpe Ratio on the chosen-seed observed Sharpe vs benchmark Sharpe = 0 over T months | Direct formula from Bailey-LdP 2014; no library dependency strictly needed; `mlfinpy.statistics.psr` if available |
| DSR | Existing `validation_v2.py` DSR; pass `n_eff_trials` via PCA-95% on the trial-return matrix | Existing — no change |
| Meta-labeling (M1 + M2) | M1 = LightGBM direction classifier (existing v2 architecture); M2 = LightGBM binary classifier on M1-positive bars; target `y_meta = 1 iff M1 → TP within timeout` | New `crypto_trade.strategies.ml.meta_label.MetaLabelStrategy` wrapping two LGBM models per symbol per month. Position sizing in iter-v3/001: vol-targeted only (no Kelly yet — that is iter-v3/002 scope). |
| Fractional differentiation | `FracdiffStat`-auto-`d*` per feature per month | `fracdiff.sklearn.FracdiffStat`; persist `d*` per (symbol, feature, month) |
| ADF stationarity test | At every retraining cycle, compute `adfuller` p-value per feature on training-window-tail data | `statsmodels.tsa.stattools.adfuller`; persist in `adf_test.csv` |
| IC matrix | Pairwise Pearson IC between feature families on IS data | New script in Engineer's pipeline; output `ic_matrix.csv` |
| `V3_FEATURE_COLUMNS` pinning | `feature_columns=list(V3_FEATURE_COLUMNS)` passed to `LightGbmStrategy`. Never None, never sorted, never reordered. | Same pattern as v2 — Engineer adds the constant in `crypto_trade/features_v3/__init__.py` |
| `V3_EXCLUDED_SYMBOLS` runtime assertion | At runner startup: `assert set(cfg.symbols).isdisjoint(V3_EXCLUDED_SYMBOLS)` | New `run_baseline_v3.py` |

---

## Section 4 — Expected OOS Impact

### 4.1 Baseline projection (point estimate)

This iteration has **no parent v3 baseline** to delta against. The closest reference is v2's iter-v2/069 (single-track baseline OOS monthly Sharpe +2.108, OOS MaxDD 18.80%, 55 trades) and v1's iter-186 (+1.735 OOS daily Sharpe, MaxDD 29.31%, 210 trades).

**Predicted v3 iter-v3/001 OOS monthly Sharpe**: **+1.2 (95% CI: [+0.6, +1.8])**.

This is intentionally below v2's +2.108 because:
1. v3 has zero IS overfitting headroom — the universe was selected on Gate 1+2 evidence, not on IS Sharpe screening (v2 had implicitly selected universe via 35+ iterations of feedback).
2. Meta-labeling reduces signal headcount (M1-positive bars × M2-confirmed subset is a strict subset of M1-positive bars). Trade count drops first, Sharpe steady-state recovers later.
3. CPCV penalises iterations with high IS variance — the chosen seed's reported Sharpe is the median of 45 paths, not the maximum. Single-path walk-forward Sharpe is typically 10–20% higher than CPCV median Sharpe (López de Prado convention).
4. New universe has zero learned hyperparameter priors; first-iteration models are likely under-tuned vs v2's matured tuning.

### 4.2 Confidence interval reasoning

- **Lower bound (+0.6)**: If meta-labeling overfits M1's CV folds, M2's filter rejects too many signals, and the universe has no genuine edge under v3's stricter validation, the OOS monthly Sharpe could fall to +0.6. This is below the 1.0 floor — would NO-MERGE.
- **Upper bound (+1.8)**: If the universe carries genuine alpha and CPCV/PBO confirm it generalises, the OOS Sharpe could approach v2's level. Above +1.8 would suggest the universe has stronger alpha than v2's, which is plausible but unverified.

### 4.3 Falsifier

**If OOS monthly Sharpe < +0.5, the hypothesis is rejected** (the universe + methodology stack does not produce edge after the rigor-arm gates). NO-MERGE; QR Phase 8 documents the failure mode in the diary; iter-v3/002 starts from the methodology-stack-validated CPCV/PBO numbers but reconsiders the universe.

**If PBO ≥ 0.4, the hypothesis is rejected regardless of headline Sharpe** (the strategy is over-fit to IS — the rigor arm's primary defense triggered as designed).

---

## Section 5 — Risk Mitigation

This is the first v3 baseline; the iteration's risk profile is "all of v2's gates + structural CPCV protection."

### 5.1 R1 — Per-symbol consecutive-SL cooldown
**Spec**: K=3 consecutive SLs → pause symbol for C=27 candles (≈9 days at 8h). Inherited from v1 Models C/D/E, applied to all 4 v3 symbols.
**IS-calibrated threshold**: K=3 came from v1's iter-186 IS analysis (`backtest.py:R1ConsecutiveSlCooldown`). For v3, Engineer's Phase 6 verifies K=3 fires no more than 5% of bars on each v3 symbol's IS data; if it fires more, the gate is too aggressive and is tuned in iter-v3/008+.
**Simulated effect**: in v1's iter-186, R1 reduced IS PnL by ≈6% but improved OOS PnL by ≈14% (positive contribution to OOS/IS ratio).

### 5.2 R2 — Per-model drawdown-triggered position scaling
**Spec**: When per-model cumulative PnL drawdown hits 7%, scale position size to `min(1.0, floor + (anchor − current_dd) / (anchor − trigger))` with floor=0.33, anchor=15%.
**Applied to**: all 4 v3 symbols (v1 applied only to Model E; v2 disabled it; v3 enables it for all symbols as a structural defense — IS-data-justified by the observation that all four v3 symbols have IS MaxDD > 70%).
**Simulated effect**: in v1's iter-186, R2 cut Model E's MaxDD from 41% to 32% with negligible PnL impact.

### 5.3 R3 — OOD Mahalanobis gate
**Spec**: cutoff 0.70 percentile, 16 scale-invariant features (same set as v1).
**Applied to**: all 4 v3 symbols.
**Simulated effect**: in v1's iter-186, R3 fired on ≈30% of OOS bars, killing predictions in 70th-percentile-distant regimes; lifted OOS Sharpe from 1.41 → 1.73.

### 5.4 RiskV2Wrapper z-score OOD gate
**Spec**: |z| > 2.5 on any of 35 v2-equivalent features kills the trade. Inherited from v2.
**Applied to**: all 4 v3 symbols.
**IS-calibrated**: 2.5 came from v2's iter-v2/059 (the v2 local optimum). v3 inherits.

### 5.5 BTC trend alignment filter
**Spec**: kill alt trade when direction fights BTC 14d return exceeding ±20% in opposing direction. Inherited from v2's iter-v2/019.
**Applied to**: all 4 v3 symbols.
**Simulated effect**: in v2's iter-v2/019 baseline, the gate caught the 2024-11 post-election rally shorts (15 kills, −33 wpnl saved). Same gate is structurally relevant for the v3 universe.

### 5.6 Concentration cap (per-symbol weighted PnL share)
**Hard rule**: top symbol ≤ 30% of OOS PnL; > 30% requires explicit exception with justification.
**v3 expectation**: with 4 symbols, the structural floor is 25% (equal contribution). Realistic baseline expectation: top symbol ≤ 35%, two strongest ≤ 60%. Exact threshold for MERGE is in Section 8.

### 5.7 Vol kill-switch
**Not implemented in iter-v3/001.** Reserved for iter-v3/008+ if observed OOS MaxDD exceeds 30% on the 4-symbol portfolio.

---

## Section 6 — Risk Management Design

### 6.1 8-primitive table (Engineer Phase 6 reference)

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling (atr_pct_rank_200) | scale = clip(atr_pct_rank_200, 0.3, 1.0) | Always on; mean scale ≈ 0.6 | High-vol environments scale down; low-vol environments scale up |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending regimes only (filters chop) |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 (training quantile band) | ≈ 90% of bars pass | Filters stationary-bond regimes (rare on 8h crypto) |
| 4 | Feature z-score OOD | kill if any feature \|z\| > 2.5 | ≈ 5–8% of bars killed | Catches distributional drift (October 2025 / liquidation cascades) |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback (OFF in v2 baseline) | DISABLED for v3 baseline | 0% (off) | (Reserved for tuning; iter-v2/045's lesson: disabling the gate gained +37% OOS Sharpe) |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 8% of bars killed | Catches macro flips (LUNA, FTX, 2024-11 rally) |
| 8 | R3 OOD Mahalanobis | kill if Mahalanobis > 70th-percentile | ≈ 30% of bars killed | Higher-dimensional regime change detection |

### 6.2 Regime coverage analysis

The v3 universe's IS data spans 2020-01 (BCH/TRX) → 2025-03-23, including:
- 2020 March COVID crash (BCH, TRX have data)
- 2021 bull market (all 4)
- 2022 LUNA collapse (May), FTX collapse (Nov) — BCH, MKR, TRX have data; LDO began 2022-09 and missed LUNA but caught FTX
- 2023 banking crisis (March) — all 4
- 2024 Bitcoin halving (April), Trump election rally (Nov) — all 4
- 2025 January correction — all 4

LDO is the youngest and missed LUNA — the brief disclaim is that LDO's IS regime coverage is narrower. Mitigation: LDO's first OOS-eligible model trains on 2023-03 → 2025-02 (24 months) — a regime-rich period. The Engineer's Phase 6 verifies LDO's `n_trials × n_walk_forward_months` cell count is ≥ 24,000 / 4 = 6,000 (i.e., ≥ 24 walk-forward months × 50 trials × 5 seeds — same as the other 3 symbols).

### 6.3 Concentration trajectory

The four symbols' expected weighted-PnL share at MERGE-time, given equal model architecture:
- Most-volatile (LDO) and most-trended (TRX): expected to be the largest contributors
- Most-stable (BCH) and lowest-µ (MKR): expected to be moderate-to-low contributors

Top-symbol concentration estimate at MERGE-time: **≤ 38%** (with TRX or LDO leading). The 30% rule is the strict bar; ≤ 35% qualifies under the diversification-exception clause if all 4 symbols are profitable OOS.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The most plausible failure mode for iter-v3/001 is **meta-labeling overfit on the M2 step**. Specifically: M2 is trained on the M1-positive subset, which is by definition a smaller and more biased sample than M1's full training set. With LightGBM's standard 50 Optuna trials per (seed × month × symbol), M2 will likely exhibit higher CV variance than M1, and PBO is the structural defense. I predict:

1. **Single-path walk-forward will report OOS monthly Sharpe in the +1.5 to +1.8 range** — comparable to v2.
2. **CPCV's median path Sharpe will be 15–25% lower** — i.e. +1.1 to +1.5 — exposing the headline-vs-honest gap that v2's single-path methodology hid.
3. **PBO will land in the 0.30–0.45 range**. If PBO < 0.40, the iteration MERGEs (after all other gates pass). If PBO ≥ 0.40, the Critic OVERALL=BLOCK with Check 3 = FAIL — and the failure is *exactly the rigor-arm's primary defense*.

The second-most-plausible failure is **LDO's narrower IS regime coverage** producing seed-unstable OOS predictions on the 2025-Q1 → 2025-Q4 OOS window. Mitigation: meta-labeling's M2 + the existing 5-seed inner ensemble. If LDO is the worst symbol on OOS PnL (negative), the diversification-cap rule still allows MERGE provided the other 3 are positive and concentration is acceptable.

The third-most-plausible failure is **TRX retreading its v2-iter-v2/066 dead-path failure**. The v2 failure was caused by IS-only screening selecting TRX with 99 break-even OOS trades. v3's selection criterion is different (full Gate 1+2+sector framework, not Sharpe screening), and v3's CPCV will catch break-even-in-disguise IS predictions before MERGE.

If iter-v3/001 fails OOS, the diary's "Pre-Registered Failure-Mode vs Reality" section will compare these three predictions to the actual failure mechanism — meta-research that compounds across iterations.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

### MERGE iff ALL of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | IS monthly Sharpe | > 1.0 | Project hard floor (memory) |
| 2 | OOS monthly Sharpe | > 1.0 | Project hard floor (memory) |
| 3 | OOS / IS Sharpe ratio | ≥ 0.5 | Project hard floor (memory) |
| 4 | OOS total trades | ≥ 130 | Trade-rate floor (memory) |
| 5 | Trades / month OOS | ≥ 10 | Trade-rate floor (memory) |
| 6 | Top-symbol OOS PnL share | ≤ 35% | Concentration cap with diversification exception (4-symbol structural floor 25%; 35% is +10pp) |
| 7 | DSR | > 0.95 | v3 hard threshold |
| 8 | PBO | < 0.40 | v3 hard threshold |
| 9 | PSR | > 0.95 | v3 hard threshold |
| 10 | Worst-symbol OOS wpnl | > -15% of total OOS wpnl | Concentration-floor tail check (no single symbol kills the portfolio) |
| 11 | OOS MaxDD | ≤ 30% | Project soft cap, hard for first v3 baseline |
| 12 | All 4 symbols have ≥ 1 OOS trade | True | Universe activity check |
| 13 | ADF p < 0.05 on every feature at every retraining month | True | v3 hard threshold (Critic Check 5) |
| 14 | IC < 0.7 between feature families | True (after methodology-stack code change, the only families are existing v2 ones; check is degenerate but enforced) | v3 hard threshold (Critic Check 4) |
| 15 | 10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable | True | Project hard floor (memory) — note iter-v2/069 finding that the 10-seed sweep is structurally vacuous with fixed `ensemble_seeds`; Engineer documents and proceeds with single-seed validation |
| 16 | Critic OVERALL | = MERGE | v3 mandatory |

### NO-MERGE iff ANY of:

- Any of the 16 criteria fails
- The Engineer's Phase 6 cannot install `pypbo` or `fracdiff` and the fallback (pure Python) cannot be implemented within the iteration's wall-clock budget
- The Engineer's Phase 6 cannot complete the CPCV backtest within 24 wall-clock hours

### Discretionary judgment

The QR retains discretion on **only one** axis: if criterion 15 (10-seed sweep) is structurally vacuous (the iter-v2/069 finding repeats), the QR may MERGE on single-seed validation alone, with explicit diary documentation. All other 15 criteria are mechanical pass/fail.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback if install fails |
|---|---|---|---|---|
| `mlfinpy` | `==0.1.2` | MIT | Optional source for `CombinatorialPurgedKFold`, meta-labeling utilities, PSR formula | Pure-Python implementation by Engineer (see fallback note) |
| `pypbo` | git `main` (esvhd/pypbo, install: `pip install git+https://github.com/esvhd/pypbo.git`) | MIT | `pbo()` for PBO computation via CSCV | Pure-Python implementation per López de Prado AFML Ch. 12 (≈100 LOC) |
| `fracdiff` | `>=0.10` (PyPI; latest 0.8.0 at time of brief — Engineer pins exact version after install) | BSD-3 | `fracdiff.sklearn.FracdiffStat` for auto-`d*` selection | n/a — the package is on PyPI and stable; if install fails, escalate |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` for ADF stationarity testing | n/a — already installed |
| `scikit-learn` | (already installed) | BSD-3 | CV scaffolding, PCA for `n_eff_trials` | n/a |
| `lightgbm` | (already installed) | MIT | M1 + M2 binary classifiers | n/a |

### Fallback rationale (mlfinlab → mlfinpy)

`mlfinlab` (Hudson & Thames) is no longer installable from public PyPI as of 2024 — the package is fully commercial and requires a subscription hash key for pip install. The v3 skill's Section 9 anticipates this. **mlfinpy is the primary library used.** If mlfinpy lacks `CombinatorialPurgedKFold` (the package is alpha and feature-incomplete per its PyPI page), the Engineer implements CPCV in pure Python directly from López de Prado AFML Ch. 12 — the algorithm is ~80 LOC plus tests.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-001/engineering_report.md` with the EXACT installed versions (output of `uv pip list | grep -E "(mlfinpy|pypbo|fracdiff|statsmodels|scikit-learn|lightgbm)"`) plus the git commit SHA. The Critic's Check 7 verifies the SHA exists and the trade-row PnL spot-check matches.

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections before submitting:

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants unchanged; IS/OOS windows in absolute dates |
| 1 — Hypothesis | PASS — one sentence, specific (universe + methodology stack), testable (OOS Sharpe ≥ 1.0, PBO < 0.4, PSR > 0.95) |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-001/symbol_universe.py` committed; 5 CSV outputs committed; tables inline |
| 3 — Proposed Changes | PASS — symbols enumerated with V3_EXCLUDED_SYMBOLS check; labeling specified; features specified (initial V3_FEATURE_COLUMNS = V2 + fracdiff rename); risk gates inherited from v2 |
| 4 — Expected OOS Impact | PASS — predicted +1.2 monthly Sharpe with [+0.6, +1.8] CI; falsifier OOS Sharpe < +0.5 OR PBO ≥ 0.4 |
| 5 — Risk Mitigation | PASS — R1/R2/R3/v2-7-gate inherited; per-gate IS-calibrated thresholds; simulated effect from v1/v2 prior iterations |
| 6 — Risk Management Design | PASS — 8-primitive table; fire-rate predictions; regime coverage analysis acknowledging LDO's narrower IS |
| 7 — Pre-Registered Failure-Mode | PASS — three explicit failure-mode predictions (M2 overfit, LDO regime gap, TRX dead-path repeat); CPCV/PBO catches enumerated |
| 8 — Pre-Registered MERGE/NO-MERGE | PASS — 16 mechanical criteria with absolute thresholds |
| 9 — Library Stack | PASS — mlfinpy primary (mlfinlab unavailable); pypbo from GitHub; fracdiff from PyPI; ADF via statsmodels |

Engineer: please run Phase 5.5 gate verification.
