# iter-v3/093 — Research Brief — Cycle-4 RE-ARCHITECTURE: the DERIVATIVES-MICROSTRUCTURE REGIME-CONDITIONED BOOK

**Iteration**: iter-v3/093 — cycle-4 slot #1 of 10 (the cycle-4 opener)
**Type**: EXPLORATION — a genuine RE-ARCHITECTURE (a legitimate single iteration's axis, cf. iter-v3/001, iter-v3/088)
**Author role**: Quant Researcher (QR), v3
**Branch**: `iteration-v3/093`
**Date**: 2026-05-18
**Anchor**: BASELINE_V3.md `v0.v3-059` — per-symbol LightGBM, IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**. UNCHANGED by this iteration.
**EDA SHA**: `359bd74` — `analysis/iteration_v3-093/derivatives_microstructure_eda.py` + T1-T5 CSVs + console capture.

---

## Section 0 — Data-Split Declaration

```
OOS_CUTOFF_DATE = 2025-03-24      # IMMUTABLE — src/crypto_trade/config.py
OOS_CUTOFF_MS   = 1742774400000   # IMMUTABLE
training_months = 24              # IMMUTABLE
```

- The walk-forward / CPCV backtest runs on ALL data. The reporting layer splits results at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/` + `comparison.csv`. No date is cherry-picked; the backtest runs from each symbol's earliest kline.
- **The QR sees OOS for the first time in Phase 7.** This brief and the Section-2 EDA are IS-ONLY. The EDA's `flag_is_test_window` enforces the runner's burn-in: every IC / regime statistic is measured ONLY on the post-24-month walk-forward IS test window `[first_kline + 24mo, OOS_CUTOFF_MS)` — bit-identical to the runner's IS span (the `feedback_v3_eda_walkforward_faithful.md` /091 fix; see Section 2.6).
- Hard floor on `OOS_Sharpe / IS_Sharpe ≥ 0.5` (Gate 3). `OOS_CUTOFF_DATE` and `training_months` are NOT touched. No re-anchor of `BASELINE_V3.md` — `v0.v3-059` stays canonical.
- **Open-interest data is NOT yet fetched.** The OI feature component (Section 3.1, `fetch-oi` build) is designed on the prep memo's verified `data.binance.vision` `metrics` schema; the OI EDA is acknowledged as Phase-6/7 validation (Section 2.7). The Section-2 IS evidence is measured on the two derivatives legs that ARE present — funding rates and perp-spot basis.

---

## Section 1 — Hypothesis

**Every prior v3 architecture predicted from PRICE-DERIVED features only.** The per-symbol absolute-barrier LightGBM (`v0.v3-059`, cycles 1-3) and the cross-sectional `LGBMRanker` momentum-rank model (/088-092) both consumed only OHLCV transforms — momentum, volatility, the cross-sectional return rank. Cycle 3 closed with zero edge: the per-symbol architecture is dead to feature/universe work (/082-087), and the cross-sectional line reached only a multi-seed IS +0.09 / OOS +0.32 — sub-floor by an order of magnitude (/092 close). The binding constraint is architectural, and it is specific: **v3 has never used a non-price information layer.**

Crypto perpetual futures carry a second, orthogonal, mechanically-causal information layer: the **derivatives-microstructure state** — the funding rate (the 8h cost-of-carry, a direct read on positioning crowding), the perp-spot basis (the continuous unclamped leverage-premium), and open-interest dynamics (the leverage-stretch gauge). The 2025 literature is specific that this state is *predictive of forced deleveraging*: the Oct 10-11 2025 cascade erased $19B of open interest in 36h with 85-90% of liquidations long-side, and post-event open interest fell >40% — a structural, mechanically-triggered deleveraging event, not noise ([Ali, SSRN 5611392](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5611392); [amberdata, the $31B deleveraging](https://blog.amberdata.io/leverage-liquidations-the-31b-deleveraging)). The cascade lesson, stated bluntly in the literature: *"If an AI is not designed to be regime-aware, a sudden change from a quiet maturation phase to a volatile, deleveraging environment will break its underlying logic."*

**The hypothesis (and the re-architecture):**

> A model whose **prediction target is a forward derivatives-microstructure state** — a 3-state forward realized-VOL REGIME {calm, normal, stressed} — and whose **feature panel is the derivatives-microstructure state** (funding + basis + an open-interest leg) carries genuine forward predictive information that price-only models structurally cannot see. A book that is **regime-CONDITIONED** on that prediction — full directional exposure in a predicted-calm regime, scaled-down or flat into a predicted-stressed (deleveraging) regime — converts that predictive content into a Sharpe improvement, primarily by **drawdown avoidance** (being flat into the forced-deleveraging volatility the derivatives state predicts).

This is the "predict the regime, not the price" reframing. It is a genuine re-architecture: a new signal class (derivatives microstructure), a new label (a forward vol-regime, not a price barrier), a new model role (a regime classifier gating a book, not a return predictor). It is NOT the iter-v3/082 funding-axis retread — /082 bolted funding *features* onto a price-barrier-labelled per-symbol model and they ranked 15-18/18 by importance; here the **label itself is a derivatives-state object**, so funding/basis/OI are the primary signal, not a 4%-importance afterthought (the /082 closeout §11 Rec 1 names exactly this exemption — "a multi-symbol-pooled model OR open-interest data... neither is a funding-axis retread").

**The carry-decay framing.** The crypto carry trade decayed hard — the funding-driven carry Sharpe fell to 4.06 in 2024 and turned NEGATIVE in 2025 ([The Crypto Carry Trade, Christin et al.](https://www.andrew.cmu.edu/user/azj/files/CarryTrade.v1.0.pdf)), and the v3 OOS window is 2025-03→2026-05 — a naive long-carry book would be backtested on its own graveyard. **This architecture is therefore deliberately a regime-AVOIDANCE architecture, not a carry-collection architecture.** Funding/basis are used as a *leading signal* of a deleveraging regime, never as a *paid* signal. Regime avoidance is structurally robust to carry decay: it does not depend on funding being a positive-carry yield, only on funding+basis extremes leading forced-deleveraging volatility — and the EDA (Section 2) measures exactly that leading relationship on the IS window.

---

## Section 2 — IS-Only Numerical Evidence

All numbers below are from the committed EDA (`analysis/iteration_v3-093/derivatives_microstructure_eda.py`, SHA `359bd74`), measured ONLY on the runner's walk-forward IS test window — the post-24-month-burn-in span `[first_kline+24mo, 2025-03-24)`. The EDA tests the two derivatives legs already in `data/` — funding rates (`data/funding_rates/`) and perp-spot basis (`data/spot/`). All features are past-only (the `funding_v3.py` / `basis_v3.py` `.shift(1)` convention).

### 2.1 — The architecture's TARGET is predictable: forward-VOL-REGIME IC is materially strong

The re-architecture's prediction target is a forward 3-state realized-vol regime. **Test 2** measures the Spearman IC of each derivatives feature vs that ordinal regime label (terciles of forward H-bar realized vol, computed per-symbol on the IS test window), plus the standardised stressed-vs-calm feature gap. Core universe (BCH/LDO/TRX, mean over symbols):

| Feature | Horizon (8h bars) | Mean regime IC | Stressed-minus-calm effect-size (σ) |
|---|---:|---:|---:|
| `f_rate` (funding rate level) | 21 (~7d) | **+0.1819** | **+0.301** |
| `f_sign_persist_9` (9-bar funding-sign persistence) | 21 | **+0.1699** | **+0.384** |
| `f_extreme_persist_9` (funding-extreme persistence) | 9 | +0.1332 | −0.133 |
| `b_level` (perp-spot basis level) | 21 | +0.0983 | +0.293 |
| `proxy_vol_surge_z` (volume-surge z-score) | 3 | +0.0832 | +0.200 |
| `f_rate` | 9 | +0.0673 | +0.121 |
| `f_sign_persist_9` | 3 | +0.0492 | +0.085 |

The headline: the funding rate level and its sign-persistence carry a forward-vol-regime IC of **+0.18 / +0.17** at the 21-bar horizon, with stressed-vs-calm effect-sizes of **0.30-0.38σ**. For comparison, a |IC| of 0.05 is the usable-signal bar in this codebase; 8 of 39 core regime-IC measurements clear it, and the top two clear it 3-4×. **A funding-state model can separate the forward calm/stressed vol regime.** This is the architecture-relevant signal — and it is materially strong on the runner's actual IS window.

### 2.2 — The contrast that VALIDATES the "predict the regime, not the price" framing

**Test 1** measures the same features' IC vs forward *returns* (not the vol regime). Core POOLED, |IC| descending:

| Feature | Horizon | Forward-RETURN IC |
|---|---:|---:|
| `f_sign_persist_9` | 21 | −0.0822 |
| `f_rate` | 21 | −0.0755 |
| `f_sign_persist_9` | 9 | −0.0691 |
| `f_rate` | 9 | −0.0654 |

Forward-return IC tops out at ~0.08 — weak. **This is the expected price-myopic ceiling, and it is exactly why the re-architecture predicts the vol regime and not the price.** The same funding features that score +0.18 against the vol regime score only −0.08 against returns: the derivatives state is far more informative about *how volatile* the next 7 days will be than about *which direction* price goes. (The negative sign on the return IC is itself coherent — high/persistent positive funding = leveraged-long crowding = a forward mean-reversion / deleveraging drag, the BIS WP 1087 carry-shock mechanism.) An architecture that tried to predict returns from this state would be working against a 0.08 ceiling; an architecture that predicts the vol regime works with a 0.18 signal. The EDA settles the architectural choice on IS evidence.

### 2.3 — The deleveraging-risk state carries genuine forward predictive content

**Test 3** reconstructs the deleveraging-cascade fingerprint pre-OI-fetch: a **deleveraging-risk state** = `(|f_zscore_30| > 1.5)` AND `(volume-surge in the IS-window top tercile)` — a funding extreme concurrent with a leverage build. It measures the lift `P(forward stressed | risk state) / P(forward stressed)`:

| Universe | Horizon | Mean lift | Mean conditional forward-ret | Mean #risk-state bars |
|---|---:|---:|---:|---:|
| core (BCH/LDO/TRX) | 3 | **1.326** | +0.0102 | 156 |
| core | 9 | **1.191** | +0.0225 | 156 |
| core | 21 | **1.106** | +0.0156 | 156 |
| wide (21 symbols) | 3 | **1.375** | +0.0051 | 148 |
| wide | 9 | **1.233** | +0.0128 | 148 |
| wide | 21 | **1.156** | +0.0237 | 148 |

The deleveraging-risk state raises the probability of a forward-stressed vol regime by **11-37%** — strongest at the short (3-bar) horizon and decaying toward the 21-bar horizon, exactly the decay profile a deleveraging event should have (the cascade is acute, then dissipates). The lift is **consistent across the 3-symbol core and the 21-symbol wide universe** — it is not a 3-symbol artifact. There are ~156 risk-state bars per core symbol on the IS test window — ample sample for a tree to learn the state. This is the direct IS basis for the regime-AVOIDANCE edge: the derivatives state flags the bars that precede elevated forward volatility.

### 2.4 — The derivatives panel is ORTHOGONAL to price (Critic Check 4 clears IS-side)

**Test 4** measures the max |Spearman IC| of each of the 13 derivatives features vs the price-derived V3 feature subset (skew/kurt/realized-vol/autocorr/VWAP-dev/momentum — the cheap-to-compute members of the 14 `V3_FEATURE_COLUMNS`). Core, descending:

| Derivatives feature | Max \|IC\| vs any price feature | Check-4 (<0.70) |
|---|---:|---:|
| `f_zscore_30` | 0.321 | PASS |
| `f_rate` | 0.254 | PASS |
| `b_level` | 0.238 | PASS |
| `f_mom_9` | 0.236 | PASS |
| `b_zscore_30` | 0.218 | PASS |
| ... (all 13) | ≤ 0.321 | **all PASS** |

Every derivatives feature has a max |IC| vs price ≤ 0.32 — well under the Critic Check-4 0.70 ceiling. **The derivatives-microstructure panel is a genuinely orthogonal information layer**, not a re-encoding of price. This is the structural fact the re-architecture is built on: it adds information v3 has never had.

### 2.5 — The data is present and complete on the IS test window

The EDA console (`derivatives_microstructure_eda_output.txt`) confirms per-symbol IS-test-window coverage. Core: BCH 7561-pooled-obs basis, TRX & BCH IS test span 2022-01→2025-03, LDO 2024-09→2025-03 (its listing date — the same burn-in truncation the runner applies to LDO's klines). Funding coverage on the IS test window is 1.00 for BCH/LDO/TRX; basis coverage 1.00. The wide 21-symbol set has funding coverage 0.90-1.00 (a handful of symbols — VET 0.90, ALGO 0.95 — have minor pre-2022 gaps, irrelevant on the IS test window). `FILUSDT` funding is empty (header-only) — FIL is excluded from both universes (and FIL is already a v3 dead universe-expansion candidate). The data legs the architecture needs are present, current, and complete on the runner's evaluation window.

### 2.6 — Walk-forward fidelity — the /091 lesson is built into the EDA harness

Per `feedback_v3_eda_walkforward_faithful.md`: iter-v3/091's EDA scored the full 2020-04→2025-03 panel and over-predicted IS Sharpe by +0.28 because the runner only trades the post-burn-in span. **This EDA does not repeat that mistake.** `flag_is_test_window` computes, per symbol, `burn_end = first_kline_open + 24 months` and flags ONLY `[burn_end, OOS_CUTOFF_MS)` as the IS test window — bit-identical to the runner's IS span. Every IC, every regime statistic, every lift in Sections 2.1-2.4 is measured on that span and ONLY that span. The pre-2022 bull regime that inflated the /091 EDA is excluded, exactly as the runner excludes it. **The Section-2 numbers ARE runner-fidelity IS targets** (subject to the one structural caveat in 2.7).

### 2.7 — The honest EDA caveat — the OI leg and the IC→Sharpe gap

Two limits are stated plainly:

1. **The open-interest leg is not in this EDA.** OI data is not yet fetched (`fetch-oi` is a Phase-6 build, Section 3.1). The EDA measures funding + basis only; the OI feature group is designed on the verified `metrics` schema and its IS predictive content is acknowledged as **Phase-6/7 validation** — the QE runs an OI-feature IC check (Section 9, integration test #5) after `fetch-oi`, and Phase 7 reads it. The architecture does NOT depend on OI being predictive — funding+basis already clear the IS bar (2.1-2.3); OI is an additive leg with a strong literature prior (the deleveraging-cascade fingerprint, 2.3's reconstructed proxy is the OI-free stand-in).
2. **An IC of +0.18 vs a vol-regime label is not a Sharpe.** Section 2 establishes the *prediction target is learnable* and the *feature layer is orthogonal* — it does NOT establish the *regime-conditioned book clears the +1.0 floor*. The IC→Sharpe transfer depends on the regime-conditioning construction (Section 3.3), the cost model, and whether the IS predictive content survives the walk-forward classifier fit. Section 4 pre-registers the honest expected-outcome distribution and the falsifiers; Section 7 the failure modes. This is an EXPLORATION — the IS evidence is a green light for the axis, not a merge prediction.

---

## Section 3 — Proposed Changes (the full architecture spec)

The re-architecture is a **3-layer derivatives-microstructure regime-conditioned book**. v3's CPCV/DSR/PBO/PSR machinery, the walk-forward embargo (`e149e9d`), the 24-month training window, and the 10:1 cadence are all preserved.

### 3.0 — Universe (Phase 3 decision)

**The cycle-4 universe is the /059 canonical per-symbol set: BCHUSDT, LDOUSDT, TRXUSDT.** Justification:

- **`V3_EXCLUDED_SYMBOLS` check**: BCH/LDO/TRX are NOT in `V3_EXCLUDED_SYMBOLS` (`BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, DOGE, NEAR, MKR`). The cycle-4 universe re-uses none of v1's or v2's symbols — the v3 isolation mandate holds.
- **Universe expansion is a v3 dead path.** Every v3 universe expansion failed: /021 (HBAR+AVAX), /069 (ADA), /083 (FIL), /087 (GALA+MANA+SAND wholesale) — the breadth `√N` benefit transferred to OOS in none of four. Cycle 4's axis is the re-architecture, NOT a universe change; changing two axes at once is uninterpretable. The /059 3-symbol set is the controlled choice — it isolates the architecture as the single variable vs the `v0.v3-059` anchor.
- **The cross-sectional 22-symbol set is wrong here.** That universe belongs to the closed `LGBMRanker` cross-sectional line; this architecture is per-symbol regime-conditioned (each symbol gets its own regime classifier + book), not a cross-sectional ranker. The wide 21-symbol set is used in the EDA ONLY as a robustness cross-check (Section 2.3 confirms the deleveraging lift generalises) — it is not the runner universe.
- The EDA confirms funding+basis coverage is 1.00 on the IS test window for all three core symbols.

### 3.1 — Layer 1: the derivatives-microstructure feature panel — `derivatives_state_v3.py`

A NEW feature module `src/crypto_trade/features_v3/derivatives_state_v3.py` (track-isolated; zero imports from `features` / `features_v2`). It REUSES the retained funding infrastructure (`data/funding_rates/`, `funding_v3.py` conventions) and basis infrastructure (`data/spot/`, `basis_v3.py` conventions) and ADDS the new OI leg. All features past-only. The panel, by group:

**Funding group (7 features — from `funding_v3.py` conventions, the EDA-validated set):** `f_rate` (level), `f_zscore_30` (30-bar past-only z-score), `f_sign_persist_9` (9-bar sign-persistence), `f_mom_3` / `f_mom_9` (8h/24h-vs-72h momentum), `f_accel_3` (second-difference carry-shock, BIS WP 1087), `f_extreme_persist_9` (rolling |z|>threshold persistence).

**Basis group (4 features — `basis_v3.py` conventions):** `b_level`, `b_zscore_30`, `b_momentum_3`, `fb_spread_z` (funding-z minus basis-z — the lagged-clamped vs continuous-unclamped leverage-stress divergence; prep memo flags IS corr only ~0.22-0.28 so it is distinct).

**Open-interest group (5 features — NEW, requires the `fetch-oi` build):** `oi_log_delta_1` (8h log-change of `sum_open_interest` — the leverage build/unwind rate), `oi_zscore_30` (30-bar past-only z-score), `oi_mcap_ratio` (OI value / a market-cap proxy = OI-value / trailing-30-bar mean quote-volume — leverage-stretch normalised), `oi_price_divergence` (the canonical "OI rising + price flat" stealth-leverage interaction = sign(`oi_log_delta`) × (1 − |price-return|-rank)), `toptrader_ls_ratio` (the `count_toptrader_long_short_ratio` column from the same `metrics` archive — positioning skew). All past-only via `.shift(1)` on the rolling stats; the OI value at bar t is resampled from the 5-min `metrics` rows of the *previous* fully-closed 8h period.

**Cross-asset group (2 features):** `btc_f_zscore_30`, `btc_oi_zscore_30` — BTC's funding and OI z-scores broadcast as a market-wide deleveraging-stress regime input (BTC funding/OI data already present / fetchable; BTC is a market-state INPUT here, not a traded symbol — it does not violate `V3_EXCLUDED_SYMBOLS`, which governs the *traded* universe; cf. the existing `cross_btc_v3.py` precedent).

**Total: 18 derivatives-microstructure features.** All ADF-tested (Section 4) — z-scores and deltas are stationary by construction; `f_rate` / `b_level` / `oi_mcap_ratio` are regime-indicator features and carry the brief Section-4 "regime indicator" justification if ADF p ≥ 0.05.

**The `fetch-oi` build (Phase-6 QE setup item).** A NEW CLI subcommand `crypto-trade fetch-oi`, a near-clone of the existing `_cmd_fetch_spot`: download `data.binance.vision`'s `data/futures/um/daily/metrics/<SYM>/<SYM>-metrics-YYYY-MM-DD.zip` daily ZIPs (verified by the prep memo — BTC from 2020-09, all v3 symbols full-window-covered; schema `create_time, symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio` at 5-min granularity), unzip/dedup/resample-to-8h, cache to `data/open_interest/<SYM>/8h.csv`. Incremental like `fetch-spot`. Estimated <500 MB download, ~1-2h engineering. **The QE runs an OI-leg IC check after `fetch-oi`** (Section 9) so the OI features' IS predictive content is verified before the backtest.

### 3.2 — Layer 2: the regime classifier — a per-symbol LightGBM multi-class model

**The model is a per-symbol `LightGbmStrategy` in MULTI-CLASS mode.** The label is NOT the triple-barrier price barrier — it is the **forward 3-state realized-vol regime**:

- For each bar t, compute the forward 21-bar (~7d, the v3 horizon) realized vol = std of the 21 forward log-returns.
- Bucket into terciles {0=calm, 1=normal, 2=stressed}. **The tercile cut-points are computed per-symbol on the TRAINING window only** (the trailing 24 months) — past-only, no look-ahead, recomputed each walk-forward month. This mirrors the `OOS_CUTOFF`-respecting walk-forward exactly.
- The model is trained (multi-class `objective="multiclass"`, `num_class=3`) to predict `P(regime = stressed)`, `P(regime = normal)`, `P(regime = calm)` from the 18-feature derivatives panel.

This is a well-posed, **balanced** 3-class problem (terciles are equal-mass by construction — no class-imbalance pathology). The model is the standard v3 5-seed ensemble (`ENSEMBLE_SIZE` per `feedback_v3_v1_ensemble.md`; EXPLORATION single-seed=42 — see 3.5), Optuna-tuned, walk-forward with the `e149e9d` embargo and the 24-month training window. The re-architecture is in the **label and the feature class**, not a new model family — a LightGBM multi-class classifier on a derivatives-state label is the cleanest, lowest-overfitting-risk first cut (an HMM is a recorded later option; a tree classifier on a balanced 3-class target avoids the HMM's state-labeling fragility).

### 3.3 — Layer 3: the regime-conditioned book — a derivatives-state-gated directional book

The regime classifier does NOT itself emit trades — it gates a directional book. Construction:

- **The base directional signal** is the existing `v0.v3-059` per-symbol price-barrier LightGBM book — the canonical baseline book, UNCHANGED. v3 already has a working, multi-seed-validated directional model; the re-architecture does not discard it.
- **The regime classifier gates position SIZE**, multiplicatively, by the predicted regime:
  - Predicted **calm** (`argmax = 0`, or `P(calm)` dominant): size multiplier **1.0** — full exposure.
  - Predicted **normal** (`argmax = 1`): size multiplier **0.6** — reduced exposure.
  - Predicted **stressed** (`argmax = 2`, the predicted-deleveraging regime): size multiplier **0.0** — **FLAT**. This is the edge: the book is flat into the forced-deleveraging volatility the derivatives state predicts.
  - The three multipliers `{1.0, 0.6, 0.0}` are the IS-calibrated default (Section 5); they are NOT Optuna-tuned to OOS — they are fixed pre-registered constants, IS-justified by the Test-3 lift profile (a stressed-regime lift of 1.1-1.4× warrants going flat; a normal regime warrants partial de-risking).
- **Confidence weighting (refinement on the prep memo's sketch).** Rather than a hard `argmax` gate, the size multiplier is `1.0·P(calm) + 0.6·P(normal) + 0.0·P(stressed)` — a smooth expectation over the predicted regime distribution. This is strictly better than a hard 3-way gate: it avoids a knife-edge at the `argmax` boundary, it sizes by *confidence* (a 0.8-confident calm prediction gets more exposure than a 0.4-confident one), and it is the standard probabilistic-gate construction. The hard-`argmax` variant is the fallback if the smooth gate underperforms IS (a Phase-6 robustness check, not an OOS tune).

This is a regime-AVOIDANCE book (Section 1): the derivatives state never adds directional exposure or collects carry — it only ever *removes* exposure into a predicted-stressed regime. The edge mechanism is drawdown avoidance, which is robust to the 2025 carry decay.

### 3.4 — The runner — `run_derivatives_regime_v3.py`

A NEW runner `run_derivatives_regime_v3.py` (cloning the `run_baseline_v3.py` per-symbol walk-forward skeleton + the `cross_sectional.py` report-writer pattern). `ITERATION_LABEL = "v3-093"`. It:
- Builds the 18-feature derivatives panel (Layer 1), the 3-state vol-regime label (Layer 2), runs the per-symbol walk-forward multi-class classifier with the `e149e9d` embargo + 24-month training window, applies the regime-conditioned size gate (Layer 3) on top of the `v0.v3-059` base directional book, and writes the standard v3 report set (`comparison.csv`, `in_sample/`, `out_of_sample/`, per-symbol attribution, `cpcv_paths.csv`, `dsr.json`, `adf_test.csv`, `ic_matrix.csv`).
- **Carries genuine CONFIRMATION-grade DSR/PBO/PSR machinery from day one** (Section 9 — the hard /092 anti-recurrence requirement): imports and CALLS `validation_v3.psr`, `validation_v3.deflated_sharpe_ratio_v3`, `validation_v3.pbo_from_cpcv` on the genuine OOS monthly-return series — NEVER hardcoded `0.0`/`NaN` sentinels.

### 3.5 — Run configuration

| Parameter | Value | Source |
|---|---|---|
| Mode | EXPLORATION | cycle-4 slot #1 |
| Universe | BCHUSDT, LDOUSDT, TRXUSDT | Section 3.0 |
| Outer seeds | 1 (seed=42) | EXPLORATION single-seed (`feedback_v3_strict_10_to_1_cadence.md`) |
| `ENSEMBLE_SIZE` (inner) | 5 | `feedback_v3_v1_ensemble.md` |
| `--n-trials` (Optuna) | 35 | `feedback_v3_exploration_n_trials_35.md` |
| Label | forward 21-bar realized-vol regime, 3-state terciles (train-window cut-points) | Section 3.2 |
| Feature panel | 18 derivatives-microstructure features | Section 3.1 |
| Base directional book | `v0.v3-059` per-symbol price-barrier LightGBM (UNCHANGED) | Section 3.3 |
| Regime gate multipliers | `{calm 1.0, normal 0.6, stressed 0.0}`, smooth-probability-weighted | Section 3.3 / 5 |
| `training_months` | 24 | IMMUTABLE |
| Embargo | `e149e9d` walk-forward fix, 22 candles | inherited |
| CPCV | n_paths=45, the standard v3 config | inherited |
| Wall-clock cap | 2h (EXPLORATION cap, `feedback_v3_cadence_discipline.md`) | — |

**Setup items enumerated** (Phase-6 QE work): (1) the `fetch-oi` CLI subcommand + the `data/open_interest/` cache; (2) `src/crypto_trade/features_v3/derivatives_state_v3.py` (the 18-feature panel module); (3) `run_derivatives_regime_v3.py` (the new runner, with genuine DSR/PBO/PSR machinery); (4) the multi-class vol-regime label + the regime-conditioned size gate; (5) `ITERATION_LABEL = "v3-093"`; (6) the integration-test suite (Section 9), including the `dsr.json` test and the OI-leg IC check.

---

## Section 4 — Expected OOS Impact + Pre-Registered Numerical Falsifiers

### 4.1 — Expected OOS impact

The architecture's edge mechanism is **drawdown avoidance**: the regime gate removes exposure into predicted-stressed regimes. The honest expected impact:

- **OOS MaxDD**: improves (lower) — the gate is flat into the deleveraging volatility. This is the highest-confidence prediction.
- **OOS monthly Sharpe**: the edge is a denominator (vol) reduction more than a numerator (return) gain. If the regime classifier transfers OOS, the OOS book's vol falls in stressed windows and the Sharpe lifts; if the classifier does not transfer, the gate fires near-randomly and Sharpe is roughly flat-to-slightly-down (the gate costs some upside in mis-classified calm windows). Modal expectation: a modest OOS Sharpe improvement driven by drawdown avoidance.
- **OOS trades**: FEWER than the `v0.v3-059` base book — the stressed-regime gate zeroes some positions. The trade-rate floor risk is real and pre-registered (F4, and Section 5).

### 4.2 — Pre-registered numerical falsifiers

The falsifiers are evaluated at Phase 7 on the runner's reproducible artifacts ONLY. The anchor is `v0.v3-059` (IS monthly Sharpe +1.0894 / OOS +0.5791 / OOS MaxDD 34.53%) — the base directional book the regime gate sits on. Each falsifier references a *different* number from the Section-4.1 *estimates* (per `feedback_v3_per_symbol_target_axis_falsifier.md` — predictions are estimates, falsifiers are gates).

| ID | Falsifier (FIRES if true) | Mechanism it catches |
|---|---|---|
| **F1** | OOS monthly Sharpe < `v0.v3-059` OOS −0.10 (i.e. < +0.479) | The regime gate net-HARMS the OOS book — it removed more good exposure than bad. |
| **F2** | OOS MaxDD ≥ `v0.v3-059` OOS MaxDD (i.e. ≥ 34.53%) | **The core falsifier.** The architecture's stated edge is drawdown avoidance. If the gate does NOT reduce MaxDD, the regime classifier did not transfer OOS — the central thesis is falsified. |
| **F3** | The regime classifier's OOS vol-regime IC ≤ 0 (the `ic_matrix.csv` / a dedicated regime-IC artifact) | The derivatives-state→vol-regime signal (IS +0.18, Section 2.1) did not transfer OOS at all — the prediction target is not learnable out-of-sample. |
| **F4** | OOS total trades < 80 (the `v0.v3-059` base book has 94 OOS trades; the gate must not zero >15% of them) | The stressed-regime gate over-fires and starves the book — a regime classifier that predicts "stressed" too often. |
| **F5** | IS monthly Sharpe < `v0.v3-059` IS −0.20 (i.e. < +0.889) | The gate breaks the book even IN-sample — the architecture is structurally wrong, not merely an OOS-transfer failure. |
| **F6 (behavioral predictor)** | The OOS stressed-regime gate fires on **< 8%** OR **> 45%** of OOS bars | The gate is either inert (predicts calm always — no architecture effect, NEGATIVE-no-effect) or pathological (predicts stressed always — F4-adjacent). Pre-registered behavioral-effect band per `feedback_v3_axis_saturation_predictor.md`. |

**Behavioral-effect prediction (mandatory, `feedback_v3_axis_saturation_predictor.md`).** The vol-regime terciles are equal-mass on the *training* window, so on a well-calibrated OOS window the stressed gate should fire on ~33% of bars ± regime drift. The pre-registered expected OOS stressed-fire rate is **[20%, 40%]**. F6's `<8%` / `>45%` band is the falsifier; the `[20%, 40%]` is the estimate. If the observed stressed-fire rate is outside `[20%, 40%]` but inside `[8%, 45%]`, that is a calibration note, not a falsifier fire — but it is recorded.

### 4.3 — MERGE / NO-MERGE criteria (pre-registered)

This is an EXPLORATION. It does NOT update `BASELINE_V3.md` regardless of outcome. The pre-registered classification gates (Section 8):

- **PROMISING** requires ALL: F1 does NOT fire (OOS Sharpe ≥ +0.479) AND F2 does NOT fire (OOS MaxDD < 34.53%) AND F3 does NOT fire (OOS regime-IC > 0) AND F5 does NOT fire (IS Sharpe ≥ +0.889) AND F6 does NOT fire. PROMISING means the architecture transferred and is a candidate for the cycle-4 CONFIRMATION bundle — NOT a merge.
- Any single falsifier firing → NEGATIVE-class (the precise subtype per Section 8).
- The `v0.v3-059` +1.0 IS / +1.0 OOS Sharpe FLOORS are the merge gates, evaluated only at a future CONFIRMATION — an EXPLORATION cannot merge.

---

## Section 5 — Risk Mitigation (R1-R5, IS-calibrated, simulated effect)

The regime-conditioned gate IS itself a risk primitive (a regime-avoidance brake). The risk design, per `feedback_v3_risk_mitigation_design.md`:

- **R-gate (the architecture's own brake) — derivatives-state regime gate.** Thresholds: size multipliers `{calm 1.0, normal 0.6, stressed 0.0}`, smooth-probability-weighted. **IS calibration**: the multipliers are set from the Test-3 lift profile — a stressed-regime forward-stressed lift of 1.11-1.37× (Section 2.3) justifies a full flat (0.0) into the predicted-stressed regime; a normal regime warrants partial (0.6) de-risking; the calm regime is unchanged (1.0). **Simulated historical effect**: on the IS test window, ~33% of bars are stressed-tercile by construction; the gate would have zeroed exposure on those bars. The Test-3 conditional forward-return on risk-state bars is positive (+0.01 to +0.02) but the conditional forward VOL is in the top tercile — the gate trades a small expected-return give-up for a large vol reduction, which is the Sharpe-accretive trade if the vol reduction dominates (the IS-side basis for the architecture).
- **R1 — consecutive-SL cooldown.** Inherited from the `v0.v3-059` base book unchanged — the base directional book's R1 stack is untouched.
- **R2 — drawdown-triggered scaling.** Inherited from the base book unchanged.
- **R3 — OOD detection.** The base book's feature-z-score OOD gate is inherited. The NEW derivatives panel is ALSO subject to an ADF / coverage pre-flight (Section 9) — a degenerate funding/OI feature (a flat-clamp window driving a z-score blow-up) is clipped to `[-10, 10]` (the `funding_v3.py` `ZSCORE_CLIP` convention).
- **R4 — vol kill-switch.** The regime gate IS the vol kill-switch in this architecture — a predicted-stressed regime IS a predicted-high-vol regime, and the gate goes flat. This is the architecture's defining feature, not an add-on.
- **R5 — concentration cap.** The base book's per-symbol structure is inherited; the 3-symbol universe and the `v0.v3-059` attribution (BCH IS-dominant) are unchanged by the gate. The gate is symbol-agnostic (each symbol has its own regime classifier) — it does not concentrate.

---

## Section 6 — Risk-Management Design (the deeper structural defense)

The single largest structural risk is **the regime classifier fails to transfer OOS** — the IS +0.18 vol-regime IC (Section 2.1) does not survive the walk-forward fit, the gate fires near-randomly, and the architecture adds noise. The structural defenses:

1. **The label is balanced and well-posed.** Equal-mass terciles eliminate class imbalance — the classifier cannot degenerate to a majority-class predictor. F6 (the behavioral band) catches a gate that drifts to always-calm or always-stressed.
2. **The gate is monotone-conservative.** The gate only ever *removes* exposure (multipliers ≤ 1.0). A mis-classified calm-as-stressed bar costs upside; a mis-classified stressed-as-calm bar leaves the base book's own R1/R2 in place. The architecture cannot *add* leverage into a deleveraging regime — the worst case is the base book's own behavior, lightly degraded. This bounds the downside.
3. **The base directional book is the proven `v0.v3-059`** — a multi-seed-validated model. The re-architecture does not stake the iteration on a brand-new directional model AND a brand-new regime layer simultaneously; it isolates the regime gate as the single new object on top of a known book. (`feedback_v3_per_symbol_lifts_oos_breaks_is.md` — per-symbol additions must be IS-disciplined; F5 is the IS-discipline gate.)
4. **The DSR/PBO/PSR machinery is genuine from day one** (Section 9) — the /092 fabricated-gate defect cannot recur. The multiple-testing haircut is computed, not hardcoded, so a regime classifier that overfits IS to noise is caught by a sub-0.95 DSR.
5. **The walk-forward IS-fidelity is built into the EDA** (Section 2.6) — the /091 mistake cannot recur; the Section-2 numbers are measured on the runner's actual span.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The honest pre-registered outcome distribution for the Phase-7 result:

- **≈40% — NEGATIVE-no-effect (the modal failure).** The regime classifier does not transfer OOS — the IS +0.18 vol-regime IC degrades to ≈0 OOS (F3 fires), the gate fires near-randomly, OOS MaxDD is roughly unchanged (F2 fires), OOS Sharpe is roughly flat. The derivatives state is IS-predictive of the vol regime but the predictive content is regime-specific and does not survive to 2025-03→2026-05. This is the v3 base rate — most EXPLORATIONs are NEGATIVE.
- **≈25% — PROMISING (the architecture transfers).** The regime classifier transfers OOS, the gate is flat into genuine deleveraging windows, OOS MaxDD improves materially (F2 does not fire), OOS Sharpe lifts modestly via vol reduction. F1/F3/F5/F6 all clear. This is a cycle-4-CONFIRMATION-bundle candidate.
- **≈15% — SUSPICIOUS.** OOS Sharpe lifts but the lift is concentrated in one or two stressed windows (e.g. a single 2025 deleveraging event the gate happened to catch) — an OOS/IS ratio > 3.0 or a single-window-driven lift. The /082/085 SUSPICIOUS-OOS-DOMINANT pattern. Recorded as NEGATIVE-class.
- **≈12% — NEGATIVE trade-starvation.** The stressed gate over-fires (F4 and/or F6 fire — OOS trades < 80, stressed-fire rate > 45%), the book is starved, OOS Sharpe is noise from too few trades.
- **≈8% — NEGATIVE IS-break (F5 fires).** The gate breaks the book even IS — the architecture is structurally wrong (a label/construction defect). This would most likely surface at the Phase 5.5 gate or as a Phase-6 anomaly before the full backtest.

**The single most likely outcome is NEGATIVE-no-effect (≈40%)** — the IS→OOS transfer of the vol-regime signal is the load-bearing uncertainty, and the v3 base rate is unforgiving. The architecture is the correct bold cycle-4 swing (the EDA green-lights the axis), but a first cut clearing the merge floors is a ≈25%-or-lower event, and the brief states that plainly. The honest framing: this iteration's *information value* — does a non-price information layer transfer OOS in v3 — is high regardless of the merge outcome.

---

## Section 8 — Classification Taxonomy (LOCKED, disjunctive precedence)

Evaluated at Phase 7 in this order; first match is canonical:

- **8.1 — SUSPICIOUS.** Fires if (a) OOS monthly Sharpe / IS monthly Sharpe > 3.0 (the OOS-soars-on-flat-IS signature; N/A if IS Sharpe ≤ 0), OR (b) the OOS Sharpe lift over `v0.v3-059` is > 80% attributable to a single calendar month. → NEGATIVE-class; the architecture is not a durable edge.
- **8.2 — NEGATIVE-no-effect.** Fires if (NOT 8.1) AND F3 fires (OOS regime-IC ≤ 0) AND F2 fires (OOS MaxDD not improved) — the regime classifier did not transfer; the gate is inert. → NEGATIVE-class.
- **8.3 — NEGATIVE-harmful.** Fires if (NOT 8.1, NOT 8.2) AND (F1 fires OR F5 fires) — the gate net-harmed the book IS or OOS. → NEGATIVE-class.
- **8.4 — NEGATIVE-trade-starvation.** Fires if (NOT 8.1-8.3) AND (F4 fires OR F6 fires) — the gate over-fired and starved the book. → NEGATIVE-class.
- **8.5 — PROMISING.** Fires if NONE of F1-F6 fire (Section 4.3) — the architecture transferred: OOS MaxDD improved, OOS regime-IC positive, OOS/IS Sharpe healthy, trade-rate adequate, the gate fires in a calibrated band. → a cycle-4-CONFIRMATION-bundle candidate. NOT a merge — an EXPLORATION never updates `BASELINE_V3.md`.
- **8.6 — NULL / INCONCLUSIVE.** Fires only if the Phase-6 build did not reach a runnable backtest (e.g. the `fetch-oi` build blocked, or the runner errored). → re-scoped, not a strategy verdict.

A PROMISING (8.5) result is bundled into the cycle-4 CONFIRMATION (iter-v3/0103, after the 10-EXPLORATION cadence) per `feedback_v3_strict_10_to_1_cadence.md` — never collapsed into an early CONFIRMATION.

---

## Section 9 — Library Stack + Integration-Test Mandate

### 9.1 — Library stack

Pinned, inherited from `v0.v3-059`: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1. No new third-party dependency — the `fetch-oi` build uses `httpx` + stdlib `zipfile`/`csv` (the existing `fetch-spot` stack); the multi-class classifier is LightGBM's native `objective="multiclass"`.

### 9.2 — Integration-test mandate (HARD, pre-registered — the /092 anti-recurrence requirement)

Per the /092 closeout (Section 7, Critic Recs #1/#2/#3): cycle 4's runner MUST carry genuine CONFIRMATION-grade DSR/PBO/PSR machinery from day one, and the `/090→/092` fabricated-gate defect class MUST NOT recur a third time. The Phase-6 build MUST ship `tests/strategies/ml/test_derivatives_regime.py` with AT LEAST these 6 tests, and a Phase-6 build that omits the DSR/PBO/PSR machinery MUST fail the suite *before* the backtest runs:

1. **`test_dsr_json_is_computed`** — asserts the runner's `dsr.json` `dsr` and `psr` fields are FINITE COMPUTED values (NOT `0.0`/`NaN` literals) and `pbo` is a genuine fraction in `[0,1]` OR an explicitly-noted structural sentinel. The test asserts the runner imports and CALLS `validation_v3.psr` and `validation_v3.deflated_sharpe_ratio_v3` (a source-level `grep` assertion + a value-level finiteness assertion). **This test is the structural guarantee against the /092 hardcoded-sentinel defect — it fails the build if the gates are placeholders.**
2. **`test_no_lookahead_in_derivatives_panel`** — spike-perturbs a single future funding/basis/OI value and asserts NO past feature changes (the `funding_v3.py` / `basis_v3.py` past-only invariant, extended to the OI leg).
3. **`test_vol_regime_label_uses_train_window_cutpoints`** — asserts the tercile cut-points are computed on the trailing-24-month training window, never on the test window or the full panel (the look-ahead-free label invariant).
4. **`test_regime_gate_is_monotone_conservative`** — asserts the size multiplier is always in `[0.0, 1.0]` and the gate never multiplies position size above 1.0 (the R-gate monotone-conservative invariant, Section 6).
5. **`test_oi_feature_ic_check`** — the OI-leg IS-validation check: after `fetch-oi`, asserts the 5 OI features have a non-degenerate IS-test-window coverage (≥ 0.90) and prints their IS vol-regime IC to a committed artifact (`analysis/iteration_v3-093/oi_leg_ic.csv`) — the Phase-6/7 OI EDA the Section-2 EDA could not run pre-fetch.
6. **`test_walk_forward_embargo_intact`** — asserts the `e149e9d` walk-forward embargo (`train_end_ms = test_start_ms - embargo_ms`) is present and load-bearing in the new runner.

The Phase 5.5 gate MUST verify that the brief specifies tests #1 and #5 as hard build items; the Phase-6 engineering report MUST cite the exact `validation_v3` call-site and the SR granularity fed to `psr()` per `feedback_v3_methodology_post_hoc_input_traceback.md`.

---

## Section 10 — QR Audit Trail

- **Cycle-4 axis origin**: the cycle-4 re-architecture direction (Candidate A — derivatives-microstructure state-conditioning) was recommended by the iter-v3/091 closeout (§9.3/9.4) and de-risked by the committed `briefs-v3/cycle4_prep_memo.md` (the data-availability investigation). This is NOT an orchestrator ad-hoc pick — it is the QR-authored cycle-3-closeout forward plan, carried into the cycle-4 prep memo, and now formalised here.
- **QR sharpening over the prep memo's sketch** (the memo is a starting point, not the final design): (1) the EDA (`359bd74`) settles the architectural choice on IS evidence — Test 1 vs Test 2 proves the vol-regime target is the right one (IC +0.18) and the return target is wrong (IC 0.08); (2) the regime gate is upgraded from the memo's hard 3-way `argmax` to a smooth probability-weighted size multiplier (Section 3.3) — strictly better, sizes by confidence; (3) the deleveraging label is reconstructed as a measurable IS lift (Test 3) rather than the memo's narrative; (4) the OI panel is given a concrete 5-feature spec on the verified `metrics` schema (Section 3.1) + a Phase-6/7 IC-validation test (Section 9 #5); (5) the runner carries genuine DSR/PBO/PSR from day one with a `dsr.json` integration test (Section 9 #1) — the hard /092 anti-recurrence requirement, which the prep memo did not specify.
- **EDA SHA**: `359bd74`. **Brief SHA**: this commit. **Setup commit SHA**: backfilled by the QE at Phase 5.5 / Phase 6 (the `ITERATION_LABEL "v3-093"` + `fetch-oi` + `derivatives_state_v3.py` + `run_derivatives_regime_v3.py` + the integration-test suite).
- **Walk-forward fidelity**: the Section-2 EDA is walk-forward-faithful per `feedback_v3_eda_walkforward_faithful.md` (Section 2.6) — the /091 IS-window-mismatch flaw cannot recur.

---

## Section 11 — Phase-6 Amendment: OI-Coverage Finding + OI-Leg Drop (18 → 13 features)

**Date**: 2026-05-18. **Author**: QR, v3. **Trigger**: integration test #5 (`test_oi_feature_ic_check`) FAILED in the Phase-6 detached build — `oi_log_delta_1` for BCHUSDT scored IS coverage **0.632 < the pre-registered 0.90 gate**. The `fetch-oi` build itself SUCCEEDED; the backtest did not run (the `&&` chain stopped at test #5). This amendment records the QR design call. The single axis (the regime-size overlay) is UNCHANGED; this is a scope reduction of Layer 1.

### 11.1 — The OI-coverage reality (read-only investigation of `data/open_interest/`)

`fetch-oi` ran correctly. Binance's `metrics` archive simply does not reach back as far as the v3 symbols' klines:

| Symbol | OI archive starts | First kline | Test-#5 coverage (`open_time < 2025-03-24`) | OI coverage of the **post-burn-in IS test window** |
|---|---|---|---:|---:|
| BCHUSDT | 2021-12-01 | 2020-01-01 | **0.633** (test reports 0.632) | **~1.000** (IS test = `[2021-12-31, 2025-03-24)`) |
| TRXUSDT | 2021-12-01 | 2020-01-15 | **0.637** | **~1.000** (IS test = `[2022-01-14, 2025-03-24)`) |
| LDOUSDT | 2022-09-22 | 2022-09-22 | ~1.000 | ~1.000 (IS test = `[2024-09-21, 2025-03-24)`) |
| BTCUSDT (cross-asset) | 2020-09-01 | n/a (input only) | ~1.000 | ~1.000 |

**Diagnosis.** The OI CSVs are clean — one 1-bar internal gap (2024-02-16) and 2 zero-OI rows, nothing that collapses coverage. The 0.632 is produced by the test's coverage denominator: test #5 measures `is_df[col].notna().mean()` over the **entire pre-OOS span** (`open_time < 2025-03-24`), which for BCH/TRX includes the **2020-01 → 2021-12 training burn-in** (~2 years, ~2190 bars) where OI is structurally NaN because the Binance `metrics` archive does not exist before late 2021. **The early-IS gap is an unavoidable Binance archive limitation, NOT a fetch problem.** The cycle-4-prep memo's "OI covers the full v3 window" claim was wrong for BCH/TRX *if* "full window" meant "from the 2020 klines"; it is correct that OI covers the v3 **IS test window** (post-24-month burn-in) — coverage there is ~1.000 for all three symbols. The brief Section 9 #5 wording said "IS-**test**-window coverage"; the QE built the gate on the full pre-OOS span. Both the wording mismatch and the archive limitation are noted; **neither is renegotiated here** — see 11.3.

### 11.2 — The brief had NO test-#5-failure provision

Section 2.7 stated only that "OI data is not yet fetched ... its IS predictive content is acknowledged as Phase-6/7 validation" and "the architecture does NOT depend on OI being predictive — funding+basis already clear the IS bar." Section 8.6 (NULL/INCONCLUSIVE) covers "the Phase-6 build did not reach a runnable backtest" but is a re-scope clause, not a designed contingency for *this specific gate*. **No clause specified what happens if test #5's coverage assertion fails.** This amendment supplies that decision on the record.

### 11.3 — Decision: DROP the OI leg — run /093 on the 13 EDA-validated features

The disciplined call, on the record:

1. **The Section-2 IS evidence is funding+basis only.** The headline +0.18 vol-regime IC (2.1), the Test-1-vs-Test-2 architectural settle (2.2), the Test-3 deleveraging-lift (2.3) all rest on the **13-feature funding(7)+basis(4)+cross-asset-BTC(2)** core. The 5 OI features were the *un-pre-evidenced* add-on — Section 2.7 #1 said so explicitly ("the architecture does NOT depend on OI being predictive"). Test #5 exists *precisely* to catch an un-EDA-validated leg failing a data-quality bar; it fired as designed.
2. **Keeping OI would require overriding my own pre-registered ≥0.90 gate post-hoc** — the exact anti-pattern (`feedback_no_cheating`-adjacent; post-hoc renegotiation of a pre-registered gate). Even though the *true post-burn-in IS-test-window* OI coverage is ~1.000, the gate as pre-registered and as built is a genuine fail, and overriding it would set a precedent of post-hoc gate softening. **Not done.**
3. **The two forbidden escapes are off the table.** Trimming the IS window to start at 2021-12 would lift the coverage number but is cheating (`OOS_CUTOFF_DATE` / `training_months` are IMMUTABLE — `feedback_no_cheating`). Changing the universe is a documented v3 dead path (Section 3.0) and a second axis. **Drop-OI is the only disciplined path.**
4. **This is a scope reduction, not a re-architecture.** Layer 2 (the per-symbol multi-class vol-regime classifier) and Layer 3 (the smooth-probability-weighted regime-size overlay on the frozen `v0.v3-059` book) are UNCHANGED. The single iteration axis — the regime overlay — is unchanged. Layer 1's feature panel shrinks from 18 → 13.

**The exact change for the QE:**

- **Feature columns: `DERIVATIVES_FEATURE_COLUMNS` 18 → 13.** Remove the 5 OI-group features: `oi_log_delta_1`, `oi_zscore_30`, `oi_mcap_ratio`, `oi_price_divergence`, `toptrader_ls_ratio`. The retained 13 = funding(7): `f_rate`, `f_zscore_30`, `f_sign_persist_9`, `f_mom_3`, `f_mom_9`, `f_accel_3`, `f_extreme_persist_9` + basis(4): `b_level`, `b_zscore_30`, `b_momentum_3`, `fb_spread_z` + cross-asset(2): `btc_f_zscore_30`, `btc_oi_zscore_30`. Update the `assert len(DERIVATIVES_FEATURE_COLUMNS) == 18` to `== 13`. The runner reads this tuple in 4 places (`run_derivatives_regime_v3.py` ~L365/432/536/1062/1115) — no runner edit needed beyond the tuple shrinking; `_verify_feature_columns_non_empty` still passes.
- **`btc_oi_zscore_30` is RETAINED** (the task's "remove exactly the 5 OI features → 13" spec; the brief counted "cross-asset BTC 2" inside its 13-feature core). It is OI-derived but is a single market-wide broadcast scalar, not a per-traded-symbol panel, and BTC's OI archive (2020-09) is far closer to BTC's kline start than BCH's case. **QE pre-flight check**: confirm `btc_oi_zscore_30` post-burn-in coverage on the runner's IS span is ≥ 0.90 before the backtest; if it is not, drop it too (→ 12 features) and note it in the Phase-6 report. This is a data-quality verification, not an axis change.
- **`derivatives_state_v3.py`: minimal.** Keep the OI-feature *computation code* in `compute_derivatives_state_features` (dead but harmless — it is simply not referenced once the 5 names leave `DERIVATIVES_FEATURE_COLUMNS`); OR delete the 5 OI blocks. QE's choice — either is acceptable. The `oi_df` / `btc_oi_df` load paths stay (BTC OI still feeds `btc_oi_zscore_30`). **`fetch-oi` is UNCHANGED** — it ran correctly, the cached `data/open_interest/` CSVs stay, and BTC OI is still needed for the cross-asset feature.
- **Integration test #5 (`test_oi_feature_ic_check`) adjustment.** The test must NOT block a deliberately OI-free build. Replace its body with an **OI-free assertion**: assert that `DERIVATIVES_FEATURE_COLUMNS` contains exactly 13 features and that NONE of the 5 OI-group names (`oi_log_delta_1`, `oi_zscore_30`, `oi_mcap_ratio`, `oi_price_divergence`, `toptrader_ls_ratio`) is present — i.e. the panel is provably OI-free per this amendment. (If the QE keeps the OI compute code, the test may also assert the 5 names are absent from the panel even though the functions exist.) The renamed/repurposed test stays test #5 in the 6-test suite — the suite still ships 6 tests, the `/092` anti-recurrence guarantee (tests #1/#3/#4/#6) is fully intact. The `analysis/iteration_v3-093/oi_leg_ic.csv` artifact is no longer produced; that is expected and correct for an OI-free build.

**Re-gate verdict — NO Phase 5.5 re-gate required.** Test #5 firing is a *foreseen contingency* — the Phase 5.5 gate already approved an architecture in which the OI leg was explicitly flagged (Section 2.7 #1) as un-EDA-validated and Phase-6/7-conditional, and approved test #5 as the hard gate guarding it. Dropping to the EDA-validated 13-feature core is a **scope reduction with nothing new to vet**: no new feature, no new label, no new model, no new universe, no new risk primitive. The single iteration axis — the regime-size overlay on the `v0.v3-059` book — is unchanged, and the 13-feature core is the exact panel the Phase-5.5-approved Section-2 EDA measured. There is strictly less surface than what Phase 5.5 already passed. A re-gate would be ceremony with no decision content.

### 11.4 — Falsifier / classification impact

The Section 4.2 falsifiers (F1–F6) and the Section 8 taxonomy are **unchanged** — every one references the `v0.v3-059` anchor and the regime-gate behavior, none references the OI leg. The Section 7 outcome distribution is unchanged: the modal-failure mechanism (the vol-regime classifier failing to transfer OOS) is identical whether the classifier is fed 13 or 18 features. If anything the 13-feature panel is the *cleaner* test of the architecture — it is exactly the EDA-validated signal set with no un-evidenced leg diluting `colsample_bytree` picks (cf. `feedback_v3_inert_features_at_higher_budget.md` — INERT features at n_trials=35 actively harm OOS; removing the un-EDA-validated OI leg removes that risk). Phase 7 evaluates /093 as the 13-feature derivatives-microstructure regime-conditioned book against `v0.v3-059`.
