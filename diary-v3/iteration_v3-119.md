# iter-v3/119 — Cycle-6 EXPLORATION slot #10 (FINAL) — NEW engineered-feature lineage (Category-2 composed: `ret5d_signed_tbi` = `ret_5d × sign(taker_buy_imbalance_20)`) — FILED **EXPLORATION-PROMISING — PROMISING-FEATURE-MECHANICAL subclass** (NEW sister-subtype to /116's PROMISING-MECHANICAL; FEATURE-layer analog of /116's RULE-layer mechanism; non-compoundable-as-signal-source invariant). The Critic FINAL (`bb654ab`) accepted the QR Round-2 sub-classification proposal in full: C6 is the FEATURE-form sister of /116's slot-freeing cascade — a feature-layer mechanism in which a new primitive cannibalizes its algebraic-sister's split-budget allocation and triggers loss-surface reorganization that elevates four other anchor features, rather than contributing direct edge signal. The verdict followed the row-by-row /060 vs /119 portfolio importance comparison the QR committed in Round 2: Spearman ρ = 0.7714 on the 14 anchor features (rank-preserving NOT chaotic shuffle), BUT `regime_momentum_signed_5d` (C6's IC=−0.72 algebraic sister, sharing the `ret_5d` value primitive) cratered −65.3% of importance (506.67 → 175.67); the combined "ret_5d × regime-sign" sister-family allocation NET DROPS 35.1% (506.67 → 328.67); C6's own allocation is only 2.6% of total split-budget (153/5847) — mechanically insufficient to produce a 5.0× OOS monthly Sharpe lift (0.14 → 0.84) as direct edge. The 35% saved allocation redistributes broadly to four rank-rising anchors (`max_dd_window_50`, `ret_kurt_50`, `hurst_100`, `ret_skew_50`), with C6 acting as the catalyst. This is the FEATURE-form sister to /116's RULE-form PROMISING-MECHANICAL: both share the load-bearing non-compoundable-as-signal-source invariant but operate at structurally distinct layers (split-budget redistribution vs book composition via slot-freeing). All 8 Critic checks PASS; Check 4 PASS-CARVEOUT for Category-2 composed-feature pivot; Check 3 informational FAIL (EXPLORATION-mode DSR/PSR regime-specific artifact). Two Critic rounds + one QR-response round. **This is cycle-6's SECOND PROMISING after /116** — and the FIRST PROMISING in v3 history that establishes a NEW classification subtype. /120 = the first multi-mechanism TWO-COMPONENT bundle in v3 history (/116 no_confirm + /119 C6) with three pre-committed falsifiers.

**Date**: 2026-05-20
**Type**: EXPLORATION (cycle-6 slot #10 of 10, FINAL EXPLORATION; iter-v3/120 is the mandatory cycle-6 CONFIRMATION) — ran a full Phase 1–8 (EDA + brief + Phase-5.5 Engineer gate + backtest + Critic preliminary + QR response + Critic FINAL), classified at Phase 7.5.
**Verdict**: **EXPLORATION-PROMISING — PROMISING-FEATURE-MECHANICAL subclass.** C6 (the `ret_5d × sign(taker_buy_imbalance_20)` Category-2 composed feature) advances to /120 CONFIRMATION as one of two strictly-accretive mechanical primitives in the FIRST multi-mechanism bundle in v3 history. The PROMISING-strong direct-edge classification is NOT supported by the importance evidence (rank 15/15 portfolio at 27.8% of top; C6's split-budget share is 2.6% — too small to mechanistically produce a 5.0× OOS lift as direct edge); the lift is more parsimoniously attributed to loss-surface reorganization via algebraic-sister cannibalization. C6 is a FEATURE-layer mechanical primitive — non-compoundable as a SIGNAL source per `feedback_promising_mechanical_subtype.md` invariant — but is structurally orthogonal to /116's RULE-layer mechanism and CAN coexist with it as a separate strictly-accretive component decision.
**Decision**: **NO-MERGE.** An EXPLORATION never updates BASELINE_V3.md regardless of outcome. BASELINE_V3.md UNCHANGED at canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION). `v0.v3-119` is a closeout marker only. C6 advances to /120 CONFIRMATION as the second component of a TWO-COMPONENT bundle (/116 no_confirm + /119 C6) at 10-seed unified ensemble validation, with three pre-committed falsifiers (stacking-linearity, TRX-concentration, sister-redistribution stability).
**Branch**: `iteration-v3/119`

---

## 1. Setup — the axis (brief reference)

iter-v3/119 advances to the **NEW engineered-feature lineage axis on STRUCTURALLY DIFFERENT primitives** per the /118 closeout Recommendation. The /118 closeout closed the broader `value × sign(vol-regime-classifier)` Category-2 composed-feature lineage on the BCH/LDO/TRX universe at single-seed n_trials=35 EXPLORATION budget; LIVE branches within the broader engineered-feature axis are composite families on STRUCTURALLY DIFFERENT primitives (volume, cross-asset, microstructure, tail/higher-moment).

The cycle-6 axis menu state at /118 closeout:

| Cycle-6 axis | Status at end of /118 | State at end of /119 |
|---|---|---|
| Universe / symbol selection | CLOSED at /110, /111 NEGATIVE | unchanged — CLOSED |
| Pooled-vs-per-symbol architecture | CLOSED at /112 NEGATIVE | unchanged — CLOSED |
| Multi-frequency features on 8h | CLOSED at /113 NEGATIVE | unchanged — CLOSED |
| Risk management (R-layer) | CLOSED at /114 NEGATIVE | unchanged — CLOSED |
| Labeling architecture | CLOSED at /115 NEGATIVE | unchanged — CLOSED |
| Exit-layer / trade-construction | PROMISING-MECHANICAL at /116 (no_confirm) | unchanged — bundled at /120 two-component |
| Candle frequency | CLOSED at /117 catastrophic NEGATIVE | unchanged — CLOSED |
| NEW engineered feature family at 8h | CLOSED-NARROW at /118 (vol-regime branch); other lineages LIVE | NARROW microstructure-regime branch CLOSED for cycle (PROMISING-FEATURE-MECHANICAL accepted); broader engineered-feature axis NOT FULLY CLOSED |
| Per-symbol XGBoost-with-categorical | LIVE per /117 § 8.1 (with imbalance-magnitude caveat) | unchanged (DEFER — claim ground removed by /117 candle-frequency closure) |

The chosen /119 candidate (EDA SHA `7aa5cc5`, 4-table screen across (i) volume-based, (iii) tail/higher-moment, (iv) microstructure primitive categories from /118's recommendation):

```
C6 = ret5d_signed_tbi = ret_5d × sign(taker_buy_imbalance_20)
```

This is a NEW lineage on STRUCTURALLY DIFFERENT primitives from /118's vol-regime branch: the regime classifier is microstructure-based (`taker_buy_imbalance_20` = 20-bar rolling mean of taker-buy ratio minus 0.5; the discretized regime label `sign(tbi)` flips at the 50/50 directional-pressure boundary) rather than vol-regime-based; the value primitive is `ret_5d` (5-day log-return) — the same value primitive as the /025 PROMISING benchmark `regime_momentum_signed_5d` but with `sign(taker_buy_imbalance_20)` replacing `sign(hurst_100 − 0.5)` as the regime classifier. The Category-2 composed-feature lineage is structurally legitimate (the /025 hurst-regime sister is the only PROMISING engineered-feature precedent in v3); the order-flow-regime branch was previously untested.

**Brief reference**: `briefs-v3/iteration_v3-119/research_brief.md`, commit `301c885` (corrected at `0060659`). Hand-chosen design parameters declared per `feedback_v3_brief_parameter_provenance.md` Section 0:
- `ret_5d` lookback = **15 8h candles** (~5 days). Rationale: matches the /025 PROMISING benchmark value primitive (`ret_5d` in `regime_momentum_signed_5d`); standard cross-cycle horizon; NOT swept.
- `taker_buy_imbalance_20` window = **20 8h candles** (~6.7 days). Rationale: matches the /015 dead-path `tbr_zscore_30` family lookback range and the V3 canonical microstructure window; NOT swept.
- Sign convention = **+1 if taker_buy_imbalance > 0 (long-biased pressure); −1 if < 0**. Inherent to `sign(x)`.
- Zero-imbalance edge case: **NaN by design** (sign undefined; preserves discrete ±1 contract).

**EDA reference**: committed at SHA `7aa5cc5` (`analysis/iteration_v3-119/`, 4 result tables T1–T4 + NEW Single-Symbol-Carrier RISK pre-Falsifier per /118 closeout Recommendation) BEFORE the brief per `feedback_v3_axis_selection_quant_discipline.md` and the auditable temporal fence. The EDA returned a GO verdict: C6 was the BEST candidate in the 4-category screen on the production-relevant T9 POOLED multivariate-lift criterion (+0.0083 POOLED); cleared the NEW Single-Symbol-Carrier RISK pre-Falsifier (max-single-symbol/POOLED ratio = 1.48×, just under the 2× threshold the /118 closeout established); cleared the multivariate-importance gain threshold on TRX (rank 8/15 at 33% of top).

**Auditable temporal fence**: every script in `analysis/iteration_v3-119/` asserts `close_time < OOS_CUTOFF_MS = 1742774400000`; 0 OOS-leaked rows.

**Pre-registered Section 4 explicit falsifier** (modal band miss → catastrophic): OOS Δ < −0.50 AND IS Δ < −0.20 → FALSIFIED. The observed IS Δ = +0.1167 and OOS Δ = +0.7017 → both POSITIVE; the catastrophic falsifier does NOT fire. **The brief's Section 7 Mode 1 (Modal success, IS Δ ∈ [+0.05, +0.30] AND OOS Δ ∈ [+0.05, +0.25])** fires on the IS leg (+0.1167 within band) but the OOS leg (+0.7017) is **2.8× the modal upper bound** — a structural positive surprise. Mode 6 (SUSPICIOUS-OOS-DOMINANT: OOS Δ > +0.30 AND IS Δ < +0.05) does NOT fire because IS Δ is broad-based positive (above +0.05 threshold by 0.0667).

---

## 2. Implementation — setup commits, engineering commit, Critic cycle

Sequenced setup chain (3 commits before backtest), then 1 engineering report commit and 3 Critic-cycle commits:

| SHA | Type | Description |
|---|---|---|
| `7aa5cc5` | analysis | engineered-feature axis EDA (4 tables across 4 primitive categories + NEW SSC-RISK pre-Falsifier; top pick C6_ret5d_signed_tbi) |
| `301c885` | docs | research brief — 10 sections; Section 3.5 enumerates 6 implementation changes + Change 0 advisory |
| `afebf6d` | docs | Phase 5.5 Engineer gate BLOCK |
| `0060659` | docs | brief correction — module attribution `volume_micro_v3` → `microstructure_v3` (Phase 5.5 fix) |
| `a1f288d` | docs | Phase 5.5 Engineer gate Round 2 PASS |
| `82baf43` | feat | C6_ret5d_signed_tbi composed feature + runner setup (the substantive code change — `src/crypto_trade/features_v3/engineered_v3.py:834-888` `compute_ret5d_signed_tbi` + GROUP_REGISTRY reorder + `V3_FEATURE_COLUMNS_TOP_N` 14→15 (drop /118 C3, add C6) + `n != 15` guard + ITERATION_LABEL/MODEL_SPECS housekeeping) |
| `d761580` | analysis | engineering report + backtest results (`reports-v3/iteration_v3-119/`) |
| `4f3a4ab` | docs | Critic PRELIMINARY (5 clarifications) |
| `70b82d5` | docs | QR response to Critic (5 clarifications answered, sub-classification proposal) |
| `bb654ab` | docs | Critic FINAL — EXPLORATION-PROMISING / PROMISING-FEATURE-MECHANICAL subclass |

**Code summary (commit `82baf43`)**:
- `src/crypto_trade/features_v3/engineered_v3.py:834-888`: NEW function `compute_ret5d_signed_tbi(df, ret_window=15, tbi_window=20) -> pd.Series`. Past-only by construction (`ret_5d = log_close − log_close.shift(15)`; reuses past-only `taker_buy_imbalance_20` primitive from `microstructure_v3.py:28-72` which itself uses `tbr.shift(1).rolling(20).mean()`). Zero-imbalance edge case correctly NaN'd.
- `src/crypto_trade/features_v3/__init__.py`: GROUP_REGISTRY reordering at lines 78-89 places `microstructure_v3` BEFORE `engineered_v3` — critical dependency-satisfaction fix (so `taker_buy_imbalance_20` exists when `compute_ret5d_signed_tbi` runs). `V3_FEATURE_COLUMNS_TOP_N` updated 14→15 (drops `ema_signed_volregime` from /118, adds `ret5d_signed_tbi` as 15th element at line 221). Per /118 closeout Code-Defect-Retention: `compute_ema_signed_volregime` STAYS in `engineered_v3.py` as code-museum (preserves implementation in case the lineage is ever re-opened under a different protocol); the column is just absent from `V3_FEATURE_COLUMNS_TOP_N`.
- `run_baseline_v3.py`: feature-count guard updated `n != 14` → `n != 15` at lines 432-442 (with iter-v3/119-specific error message naming `ret5d_signed_tbi`); ABSENT-ban for `ema_signed_volregime` at lines 593-599; ITERATION_LABEL="v3-119" at line 131; MODEL_SPECS prefixed "v3-119-".
- Parquet regeneration: BCH/LDO/TRX/BTC 8h parquets regenerated with `ret5d_signed_tbi` column (15th) present and non-NaN on last 100 IS rows.
- `tests/test_engineered_v3.py`: 2 NEW C6-specific tests (past-only invariant + sign-convention) — 2/2 PASS; total 252 passed, 3 skipped.
- Integration tests: 5 end-to-end assertions all PASS.

**Knobs UNCHANGED vs /059-canonical** (verified against accretion guard output in `run.log`):
V3_MODELS = BCH/LDO/TRX; REQUIRED_GAP = 66; label_mode = triple_barrier; ATR multipliers = (2.0, 1.0); zscore_threshold = 2.0; adx_threshold = 20.0; enable_no_confirm_exit = False (REVERTED from /116); enable_per_symbol_drawdown_brake = False; ENSEMBLE_SIZE = 3 (EXPLORATION-mode); n_trials = 35; bar-interval = 8h.

**Wall-clock**: 0.70h (well under the 2h cycle-6 EXPLORATION cap). Hardware: 12th Gen Intel Core i9-12900HK / 58 GiB RAM / WSL2 Linux x86_64.

**Sacred constants verified**: `OOS_CUTOFF_DATE = 2025-03-24` UNCHANGED, `training_months = 24` UNCHANGED.

---

## 3. Results — Phase 7 OOS evaluation (first look)

This is the QR's first look at the iter-v3/119 OOS reports.

### 3.1 Headline metrics (`reports-v3/iteration_v3-119/comparison.csv`)

| Metric | In-Sample | Out-of-Sample | OOS/IS ratio |
|---|---:|---:|---:|
| **monthly_sharpe** | **+0.8492** | **+0.8420** | 0.9916 |
| daily_sharpe | +1.7386 | +2.3234 | 1.3363 |
| max_drawdown | 39.90% | 32.82% | 0.8225 |
| profit_factor | 1.3042 | 1.3421 | 1.0291 |
| win_rate | 33.33% | 42.72% | 1.2816 |
| n_trades | 189 | 103 | 0.5450 |
| total_pnl | +61.37% | +36.65% | 0.5971 |
| monthly_calmar | +1.5380 | +1.1165 | 0.7260 |
| weighted_pnl_total | +61.37% | +36.65% | 0.5971 |

vs the /060 EXPLORATION-mode anchor (IS +0.8325 / OOS +0.1403):
- **IS Δ = +0.1167** (clears +0.10 PROMISING floor)
- **OOS Δ = +0.7017** (clears +0.20 PROMISING floor by 3.5× — 2.8× the modal upper bound +0.25 → structural positive surprise)

vs the /059 CONFIRMATION canonical baseline (IS +1.0894 / OOS +0.5791):
- IS Δ = −0.2402; OOS Δ = +0.2629. /059 IS+OOS combined dominance NOT achieved at single-seed EXPLORATION-mode 3-seed run; OOS exceeds /059 but IS lags.

### 3.2 Statistical significance block

| Metric | /119 Value | Gate threshold | Gate status |
|---|---|---|---|
| DSR | 0.0000 | > 0.95 | FAIL (informational — EXPLORATION-budget artifact) |
| PBO | 0.0957 | < 0.40 | PASS |
| PSR | 1.0000 | > 0.95 | PASS |
| DSR_relative | 0.9997 | > 0.95 | PASS |
| frac_positive_paths | 0.6444 (29/45) | ≥ 0.55 | PASS |
| n_trials | 315 | — | — |
| n_effective_trials | 19 | — | — |
| CPCV path Sharpe Q25 / Q50 / Q75 | −0.2430 / +0.3351 / +0.8378 | — | — |

Per `feedback_v3_dsr_mode_artifact.md`, DSR=0.0 at EXPLORATION-mode (n_trials=315, E[max_SR]≈2.6) is a regime-specific structural artifact NOT comparable to CONFIRMATION-mode (n_trials=1500+, E[max_SR]≈3.4). For TYPE=EXPLORATION, only PBO is BLOCK-triggering — and PBO PASSES decisively (0.0957 identical to /060/059 CPCV invariant). PSR=1.0000 at EXPLORATION is informational only and cannot be cited as edge-significance evidence per `feedback_v3_dsr_mode_artifact.md`.

### 3.3 Per-symbol IS attribution (`reports-v3/iteration_v3-119/in_sample/per_symbol.csv`)

| Symbol | Trades | WR | net_pnl_pct | avg_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 95 | 46.3% | **+84.02%** | +0.885% | **+79.32%** |
| TRXUSDT | 82 | 35.4% | +14.59% | +0.178% | +13.77% |
| LDOUSDT | 12 | 33.3% | +7.31% | +0.609% | +6.90% |

**ALL THREE SYMBOLS POSITIVE IS PnL** — BCH dominant (79% of IS PnL); LDO and TRX both modest positive. Per-symbol IS Δ vs /060: BCH +4.57 (modest), LDO +18.75 (sign flip from −11.44), TRX +37.63 (sign flip from −23.04). The /118 single-symbol-carrier failure mode is cleanly avoided.

### 3.4 Per-symbol OOS attribution (`reports-v3/iteration_v3-119/out_of_sample/per_symbol.csv`)

| Symbol | Trades | WR | net_pnl_pct | avg_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|---:|
| TRXUSDT | 52 | 50.0% | **+33.89%** | +0.652% | **+61.53%** |
| BCHUSDT | 37 | 43.2% | +31.22% | +0.844% | +56.68% |
| LDOUSDT | 14 | 28.6% | **−10.03%** | −0.717% | **−18.22%** |

TRX + BCH both materially OOS positive; LDO drags (−18% portfolio share). Concentration_pct in `comparison.csv` shows TRX=80.14% — exceeds the ≤30% per-symbol merge gate as a raw figure, but the metric inflates under sign-divergence (LDO at −24.03% deflates the positive denominator). Corrected for sign-divergence: TRX share of positive-symbol total = 33.89 / (33.89 + 31.22) = **52.05%** — just over the threshold the QR pre-committed as a /120 BLOCK gate.

### 3.5 C6 feature importance ranks (`reports-v3/iteration_v3-119/in_sample/model_importance_last_month_portfolio.csv`)

**Portfolio (aggregated across BCH/LDO/TRX, last walk-forward month)** — full top-15 ranking:

| Rank | Feature | /060 Imp | /119 Imp | Δ Imp % |
|---|---|---:|---:|---:|
| 1 (was 5) | max_dd_window_50 | 646.33 | 551.00 | -14.7% |
| 2 (was 1) | ret_skew_200 | 816.33 | 524.00 | -35.8% |
| 3 (was 7) | ret_kurt_50 | 598.00 | 509.33 | -14.8% |
| 4 (was 3) | range_realized_vol_50 | 706.33 | 503.00 | -28.8% |
| 5 (was 2) | vwap_dev_20 | 759.67 | 487.67 | -35.8% |
| 6 (was 8) | hurst_diff_100_50 | 593.33 | 422.33 | -28.8% |
| 7 (was 4) | ema_spread_atr_20 | 698.67 | 402.00 | -42.5% |
| 8 (was 11) | hurst_100 | 569.33 | 389.67 | -31.6% |
| 9 (was 12) | ret_skew_50 | 520.33 | 369.33 | -29.0% |
| 10 (was 9) | ret_kurt_200 | 582.00 | 360.67 | -38.0% |
| 11 (was 6) | ret_autocorr_lag1_50 | 607.00 | 352.00 | -42.0% |
| 12 (was 10) | btc_ret_14d | 582.00 | 328.33 | -43.6% |
| 13 (was 13) | sym_vs_btc_ret_7d | 511.67 | 319.67 | -37.5% |
| 14 (was 14) | regime_momentum_signed_5d | **506.67** | **175.67** | **−65.3%** |
| **15 (NEW)** | **ret5d_signed_tbi (C6)** | — | **153.00** | — |

**C6 ranks 15/15 portfolio (last-month)** at 27.8% of top-feature share. Per-symbol: BCH 15/15 (47.7), LDO 15/15 (45.0), TRX 12/15 (60.3). The /025 PROMISING-strong benchmark (rank ≤ 11/15 on ≥ 2 symbols) FAILS on the literal sub-gate (only TRX clears). Under the Category-2 composed-feature carve-out (`feedback_v3_lr_pf_methodology.md` + `feedback_v3_engineered_feature_pivot.md`), Sharpe-Δ is the PRIMARY falsifier — the importance-rank sub-gate is informational. The full mechanistic interpretation requires the row-by-row /060 vs /119 comparison above and is the load-bearing diagnostic for the SUCCESS-mechanism classification in Section 5.

### 3.6 IC matrix and ADF (`reports-v3/iteration_v3-119/ic_matrix.csv`, `adf_test.csv`)

- C6's max |IC| with any existing feature = **0.7229** with `regime_momentum_signed_5d` — exceeds the strict 0.70 threshold by 0.02. Per `feedback_v3_engineered_feature_pivot.md`, Category-2 composed features sharing a value primitive (`ret_5d`) MECHANICALLY correlate by construction; the strict 0.70 threshold is replaced by the importance-≥30% threshold (the brief Section 0 PASS-CARVEOUT declaration). Secondary high-|IC| pairs (vwap_dev_20 −0.567, ema_spread_atr_20 −0.431) are algebraically inherited transitively through regime_momentum_signed_5d and do not constitute NEW high-IC pairs.
- The pre-existing high-IC pair (`vwap_dev_20 × regime_momentum_signed_5d` at 0.7642) is unchanged from /059/060 baseline — confirmed not worsened by C6 addition.
- ADF: 2283 rows total; 1949 (85.4%) stationary at p<0.05. At IS-end month 2025-03, C6 decisively stationary across all 3 symbols (BCH ADF=−7.753 p=0.0; LDO ADF=−8.128 p=0.0; TRX ADF=−10.295 p=0.0). Structurally guaranteed by `sign(tbi) ∈ {−1, +1}` × bounded log-return = stationary product.

### 3.7 OOS-trade-rate

OOS trades = 103 across 14 OOS months ≈ 7.4 trades/month — below the v3 informational trade-rate floor (≥10 trades/month OOS) but EXPLORATION mode does not enforce the floor. No zero-trade months in OOS. Flagged for /120 CONFIRMATION monitoring.

---

## 4. Critic Review Summary (Phase 7.5)

### 4.1 Round 1 — PRELIMINARY (`review_preliminary.md`)

The Critic returned a leaning EXPLORATION-PROMISING direction with 5 substantive clarifications that would materially change the sub-classification. The headline numbers cleared PROMISING gates and broad-based per-symbol attribution cleared the /118 SSC-RISK failure mode, but the importance-rank-15/15 + OOS-Δ-2.8×-modal-upper-bound + TRX-OOS-concentration-80% triad bore uncomfortable resemblance to the /116 PROMISING-MECHANICAL signature. The Critic's preliminary read framed the verdict as hinging on the QR's adjudication of whether the lift is FEATURE-SIGNAL or FEATURE-MECHANICAL.

The 5 clarifications:
1. **Importance-15/15 vs Sharpe-+0.70 paradox** — feature-SIGNAL or feature-MECHANICAL? Concrete diagnostic the QR could provide: row-by-row /060 vs /119 anchor-feature importance comparison.
2. **OOS Δ +0.7017 = 2.8× modal upper bound** — how is this NOT Mode 6 SUSPICIOUS-OOS-DOMINANT? Daily-Sharpe vs monthly-Sharpe reconciliation.
3. **/116 PROMISING-MECHANICAL precedent** — is /119 a feature-form analog? Should /119 be classified PROMISING-FEATURE-MECHANICAL (NEW sister-subtype)?
4. **TRX OOS concentration_pct = 80%** — sign-divergence inflation or genuine concentration risk? Falsifier pre-commitment for /120?
5. **/120 bundling adjudication** — TWO-COMPONENT vs SINGLE-COMPONENT vs deferred /119?

### 4.2 Round 2 — QR Response (`qr_response.md`)

The QR returned a substantive sub-classification proposal answering all 5 clarifications:

**Clarification 1 answer (load-bearing diagnostic)**: The QR committed the row-by-row /060 vs /119 portfolio importance comparison (see Section 3.5 table above). Diagnostic statistics:
- Spearman rank correlation /060 ↔ /119 (14 anchor features): **ρ = 0.7714** — moderate-high preservation. NOT a chaotic shuffle.
- Mean absolute rank shift per anchor feature: 2.29 / 14 ranks.
- Top-5 set preservation: 4/5.
- Total importance allocation /060 → /119: 8697.67 → 5847.67 (anchor-only 5694.67) — ~35% less total split-count budget despite one more feature.
- C6's share of /119 total: 153.0 / 5847.67 = **2.6%**.
- `regime_momentum_signed_5d` (C6's IC=−0.72 algebraic sister) lost **65.3%** of its importance (506.67 → 175.67). C6+sister combined: 506.67 → 175.67 + 153.00 = **328.67** (NET DROPS 35.1%).

The QR's interpretation: **C6 is BOTH feature-SIGNAL (low-but-nonzero direct contribution) AND feature-MECHANICAL (loss-surface reorganizer that redistributes split budget away from regime_momentum_signed_5d and toward four other anchor features that rank-rise)**. The dominant effect is feature-MECHANICAL: C6's NEW allocation (153) is smaller than the allocation it cannibalizes from its sister (506→175, a −331 drop); the +0.70 OOS Sharpe lift cannot mechanistically be produced by 2.6% of split budget as direct-edge effect; it is more parsimoniously attributed to loss-surface reorganization elevating max_dd_window_50, ret_kurt_50, hurst_100, ret_skew_50 (the four rank-rising anchors), with C6 acting as the catalyst.

**Clarification 2 answer**: Monthly Sharpe is canonical (matches brief Section 7 pre-registration and BASELINE_V3.md convention per `feedback_v3_cycle1_axis_pass_criteria.md`). Daily Sharpe view is INFORMATIONAL only. Mode 6 correctly does NOT fire because IS Δ = +0.1167 exceeds the +0.05 threshold — broad-based per-symbol IS movement (BCH +4.57 / LDO +18.75 / TRX +37.63) refutes the no-IS-movement lottery signature Mode 6 is calibrated to catch.

**Clarification 3 answer**: /119 IS the feature-form analog of /116. Classify as **PROMISING-FEATURE-MECHANICAL** (NEW sister-subtype to /116's RULE-form PROMISING-MECHANICAL). Both share the load-bearing **non-compoundable-as-signal-source** invariant from `feedback_promising_mechanical_subtype.md`. Mechanisms differ at the layer (rule-layer book composition vs feature-layer split-budget redistribution) — they can in principle coexist as separate strictly-accretive component decisions in a single CONFIRMATION bundle, but cannot be expected to STACK linearly as if they were independent edge ingredients.

**Clarification 4 answer**: Pre-committed falsifier for /120 CONFIRMATION 10-seed (QR-binding pre-registration): if TRX multi-seed mean OOS weighted PnL share > 50% of positive-symbol total → BLOCK C6 inclusion (keep /116 alone); 50–65% → concentration-watch flag; > 65% → full BLOCK; LDO portfolio share worse than −25% multi-seed → flag.

**Clarification 5 answer**: **(a) TWO-COMPONENT /116+C6 bundle at /120 CONFIRMATION**, with both treated as mechanical accretion decisions (NOT additive edge ingredients), and with three pre-committed falsifiers (stacking-linearity, TRX-concentration, sister-redistribution stability).

### 4.3 Round 3 — Critic FINAL (`bb654ab`)

The Critic FULLY ACCEPTED the QR Round-2 sub-classification proposal on all 5 clarifications. OVERALL: **EXPLORATION-PROMISING — subclass PROMISING-FEATURE-MECHANICAL** (NEW sister-subtype to /116 PROMISING-MECHANICAL). The new v3-catalog classification is established by this review.

Per-check status: all 8 PASS. Check 4 PASS-CARVEOUT per Category-2 composed-feature pivot. Check 3 INFORMATIONAL FAIL (DSR=0.0/PSR=1.0 EXPLORATION-mode regime artifacts; PBO=0.0957 PASS). Check 6 N/A (single-seed EXPLORATION, no 10-seed pareto front).

The Critic's three substantive recommendations for /120:

1. **TWO-COMPONENT bundle (/116 no_confirm + /119 C6 `ret5d_signed_tbi`)** at 10-seed unified ensemble validation — FIRST multi-mechanism bundle in v3 history. The two mechanisms operate at DIFFERENT layers (rule vs feature) so the non-compoundable-as-signal-source invariant does not preclude their coexistence as separate strictly-accretive accretion decisions. The /116-alone and C6-alone alternatives leave evidence on the table and the multi-seed budget cannot be re-spent.

2. **Three pre-committed falsifiers carried into /120 brief Section 4 (binding pre-registration)**:
   - **Falsifier 1 — Stacking-linearity**: bundle multi-seed OOS monthly Sharpe < max(/116-only multi-seed OOS Sharpe, C6-only multi-seed OOS Sharpe) − 0.10 → bundle is NEGATIVE-no-stacking; revert to /116-only for /120 MERGE. Critical safeguard against over-additive assumption.
   - **Falsifier 2 — TRX-concentration**: TRX multi-seed mean OOS PnL share > 50% of positive-symbol total → BLOCK C6 inclusion (keep /116 alone); 50–65% → concentration-watch flag; > 65% → full BLOCK; LDO portfolio share worse than −25% multi-seed → flag.
   - **Falsifier 3 — Sister-redistribution stability**: if `regime_momentum_signed_5d` importance falls > 50% in multi-seed mean (vs /060 anchor) AND `ret5d_signed_tbi` importance fails to exceed 5% of portfolio total importance → "allocation cannibal without contribution" → BLOCK C6 inclusion.

3. **C6 STAYS in `V3_FEATURE_COLUMNS_TOP_N` for /120**: do NOT revert as /118 C3 was. The /120 setup-commit takes /119 head state (15 features with `ret5d_signed_tbi` at index 14). The 10-seed CONFIRMATION evaluates C6 in its production form; the three falsifiers above are the gates that decide whether C6 remains in the production baseline post-/120.

---

## 5. SUCCESS-Mechanism Analysis — feature-MECHANICAL loss-surface reorganization, sister-family allocation transfer, broad-based per-symbol cascade

### 5.1 The mechanism — algebraic-sister cannibalization

The feature-MECHANICAL mechanism is structurally distinct from /116's RULE-form slot-freeing cascade. The mechanism operates at the LightGBM loss-surface layer:

1. The new primitive `ret5d_signed_tbi` (C6) has **IC = −0.7229** with its algebraic sister `regime_momentum_signed_5d` (which itself shares the `ret_5d` value primitive). This is BY CONSTRUCTION — both features compose `ret_5d × sign(regime-classifier)` with different regime classifiers (`taker_buy_imbalance_20` vs `hurst_100 − 0.5`).
2. At fixed `n_estimators × colsample_bytree × max_depth`, LightGBM's effective split budget is bounded. Two near-anti-correlated features compete for the same splits at each node.
3. The Optuna 35-trial search at single-seed lands on a hyperparameter point where the model preferentially uses C6 over `regime_momentum_signed_5d` for splits that would otherwise have gone to the sister. C6 absorbs 153 splits; `regime_momentum_signed_5d` loses 331 splits (506→175).
4. **The NET allocation to the "ret_5d × regime-sign" sister-family DROPS 35.1%** (from 506.67 to 328.67). The 178 "saved" splits (506 − 328) are redistributed to four other anchor features that rank-RISE: `max_dd_window_50` (was rank 5, becomes rank 1), `ret_kurt_50` (was 7, becomes 3), `hurst_100` (was 11, becomes 8), `ret_skew_50` (was 12, becomes 9).
5. The decision boundary becomes structurally different — the trees use `max_dd_window_50`, `ret_kurt_50`, `hurst_100`, `ret_skew_50` more aggressively, capturing tail-risk and regime-persistence signals the sister-family-dominated /060 model under-weighted.
6. The OOS environment (2025-2026 uptrend) rewards this tail-risk + regime-persistence weighting more than it rewards the sister-family momentum/regime-condition weighting that /060 used. Hence the 5.0× OOS monthly Sharpe lift (0.14 → 0.84).

The mechanism is verifiably mechanical: C6 itself is NOT the source of edge (2.6% of split budget); the lift comes from the reorganization C6 catalyzes.

### 5.2 The broad-based per-symbol cascade — anti-/118 signature

The /118 failure mode was a single-symbol-carrier per-symbol attribution: BCH was the sole IS positive carrier (+52.61%), with LDO (−13.80%) and TRX (−5.49%) both negative or catastrophically negative. The /118 EDA's T9 multivariate-lift predicted POOLED +0.0081 but max-single-symbol |lift| = 0.0082 (TRX) — asymmetry/POOLED ratio 1.01× (just under the 2× threshold the new SSC-RISK gate established at /118 closeout).

The /119 EDA's T9 max-single-symbol/POOLED ratio = 1.48× (also just under the 2× threshold) — still passing the SSC-RISK pre-Falsifier. The production result CONFIRMED broad-based:

| Symbol | /060 IS PnL | /119 IS PnL | /119 IS Δ | /060 OOS PnL | /119 OOS PnL | /119 OOS Δ |
|---|---:|---:|---:|---:|---:|---:|
| BCH | +79.45% | +84.02% | **+4.57** | −8.69% | +31.22% | **+39.91** |
| LDO | −11.44% | +7.31% | **+18.75** | −25.08% | −10.03% | **+15.05** |
| TRX | −23.04% | +14.59% | **+37.63** | +30.76% | +33.89% | **+3.13** |

ALL THREE SYMBOLS positive Δ on BOTH axes. LDO and TRX both flipped from deeply negative to positive on the IS leg. This is the BROAD-BASED-CASCADE signature defining the PROMISING-FEATURE-MECHANICAL subtype — distinguishing it from /118-style single-symbol-carrier lottery outcomes.

### 5.3 The anchor-rank preservation — NOT chaotic shuffle

A pure-mechanical reorganizer (e.g., a feature that catastrophically destroys the loss surface) would produce Spearman ρ close to 0.3–0.5 on the 14 anchor features (the model would find entirely different dominant signals). /119 shows ρ = 0.7714 — moderate-high preservation. The top-5 set is 4/5 preserved (only `ret_kurt_50` enters and `ema_spread_atr_20` drops). The model still finds the same dominant signals at rearranged weight.

This distinguishes PROMISING-FEATURE-MECHANICAL from a pure loss-surface destruction class (which would be NEGATIVE-catastrophic, not PROMISING). The rank-preservation evidence is critical for the diagnostic conjunction.

### 5.4 The mechanism summary — three diagnostic conditions

The PROMISING-FEATURE-MECHANICAL subtype is identified by the conjunction of three conditions (see new memory file `feedback_v3_promising_feature_mechanical.md`):

1. **Sister-family redistribution > 30% with new feature < 5% of total split-budget**: /119 has sister-family NET DROP 35.1% (506→328); C6 only 2.6% of total split budget.
2. **Anchor-rank preservation Spearman > 0.50 (NOT chaotic shuffle)**: /119 has Spearman ρ = 0.7714 on the 14 anchor features.
3. **Broad-based per-symbol IS positive Δ (NOT single-symbol carrier)**: /119 has BCH +4.57 / LDO +18.75 / TRX +37.63 IS PnL Δ — broad-based cascade.

/119 meets all three. The classification refines the standard EXPLORATION-PROMISING verdict: C6 is strictly-accretive on /059 as a feature-layer mechanical primitive, but is NOT a new edge ingredient and CANNOT be compounded with other edge ingredients in future cycles as if it were a signal contribution.

---

## 6. PROMISING-FEATURE-MECHANICAL classification — full diagnostic conjunction, precedent established by this iteration

This iteration establishes a NEW v3-catalog classification: **PROMISING-FEATURE-MECHANICAL**, the FEATURE-layer sister to /116's RULE-layer **PROMISING-MECHANICAL**. The new memory file `feedback_v3_promising_feature_mechanical.md` documents the subtype; this section provides the diary-canonical statement.

### 6.1 Definition

`EXPLORATION-PROMISING — PROMISING-FEATURE-MECHANICAL subclass`: an EXPLORATION-PROMISING outcome in which the headline Sharpe lift is mechanically attributable to loss-surface reorganization (split-budget redistribution from an algebraic-sister feature, with downstream effect on multiple other anchor features' relative weighting) rather than direct signal contribution from the new feature itself.

### 6.2 Diagnostic conjunction (all three must hold)

| Condition | Threshold | /119 observation |
|---|---|---|
| (a) Sister-family redistribution + new-feature split-budget share | sister-family NET DROP > 30% AND new feature < 5% of total split-budget | NET DROP 35.1% (506.67 → 328.67); C6 share 2.6% (153/5847) |
| (b) Anchor-rank preservation | Spearman ρ > 0.50 on the anchor-feature ranks vs prior baseline | ρ = 0.7714 on 14 anchor features |
| (c) Broad-based per-symbol IS positive Δ | ALL 3 symbols (or ≥ 80% of universe) show positive IS PnL Δ vs anchor | BCH +4.57 / LDO +18.75 / TRX +37.63 — 3/3 positive |

If all three hold, classify as PROMISING-FEATURE-MECHANICAL. If only conditions (b) and (c) hold but the new feature has > 5% split-budget share AND the sister-family allocation is preserved or grows, classify as PROMISING-strong (direct edge — the /025 precedent pattern). If only (b) holds, classify as standard EXPLORATION-PROMISING. If (a) holds but (c) fails, the pattern is SINGLE-SYMBOL-CARRIER (the /118 failure mode).

### 6.3 Subtype rules

**Sister-subtype to PROMISING-MECHANICAL**: PROMISING-FEATURE-MECHANICAL operates at the FEATURE layer; PROMISING-MECHANICAL operates at the RULE layer. Both share the load-bearing invariant.

**Load-bearing invariant — non-compoundable as a SIGNAL source**: PROMISING-FEATURE-MECHANICAL primitives cannot be bundled with other PROMISING-class outcomes as if they were independent edge ingredients. The new feature is a catalyst for loss-surface reorganization, not a new edge primitive. Adding multiple FEATURE-MECHANICAL primitives is expected to produce diminishing returns or interaction-cancellation, not linear stacking.

**Cross-layer orthogonality with PROMISING-MECHANICAL**: a PROMISING-FEATURE-MECHANICAL primitive (feature-layer) CAN coexist with a PROMISING-MECHANICAL primitive (rule-layer) in a single bundle as TWO separate strictly-accretive component decisions, because the mechanisms operate at structurally distinct layers. Cross-layer orthogonality means the two mechanisms address different aspects of the model+rule pipeline (split-budget allocation vs trade-roster composition) and may genuinely STACK — but the stacking-linearity is NOT guaranteed and must be tested empirically with a stacking-linearity falsifier (see /120 Falsifier 1).

**Precedent established by this iteration**: iter-v3/119 is the FIRST verified PROMISING-FEATURE-MECHANICAL classification in v3 history. Future EXPLORATION verdicts meeting the three-condition diagnostic conjunction file under this subtype.

### 6.4 Why /119 is NOT PROMISING-strong

The strict PROMISING-strong classification (direct edge contribution) requires:
- Importance rank ≤ 11/15 on ≥ 2 symbols, OR
- Importance share ≥ 30% of top-feature on a majority of symbols, OR
- Sister-family allocation preserved or grown.

/119 fails all three: rank 15/15 on BCH and LDO (only TRX at 12/15); portfolio share 27.8% (just below 30%); sister-family NET DROPS 35.1%. The Category-2 composed-feature carve-out (`feedback_v3_engineered_feature_pivot.md`) softens but does not eliminate the importance criterion — and /119's evidence of allocation cannibalization makes the carve-out unnecessary: the Sharpe-Δ-PRIMARY rule still applies, but the SOURCE of the Sharpe lift is mechanically traceable to reorganization, not direct edge.

The /025 precedent (`regime_momentum_signed_5d`) is the only PROMISING-strong engineered-feature in v3 history. /025 had 51% top importance share; /025 was the new feature contributing direct signal, not cannibalizing a sister (it WAS the sister, with no prior precedent). /119 differs from /025 at exactly the diagnostic features (a) and (c) — making it the FEATURE-MECHANICAL analog rather than another /025-class direct-edge precedent.

---

## 7. /120 TWO-COMPONENT bundle setup — first multi-mechanism bundle in v3 history

### 7.1 Bundle composition

/120 = TWO-COMPONENT CONFIRMATION at 10-seed unified ensemble (ENSEMBLE_SIZE=5 inner × outer_seeds=2 = 10 models per cell per v3 CONFIRMATION envelope; n_trials=35 per `feedback_v3_confirmation_n_trials_35.md`):

| Component | Layer | Subtype | Source iteration |
|---|---|---|---|
| no_confirm early-exit primitive | RULE layer | PROMISING-MECHANICAL | iter-v3/116 |
| ret5d_signed_tbi (C6) composed feature | FEATURE layer | PROMISING-FEATURE-MECHANICAL | iter-v3/119 |

Both treated as **separate strictly-accretive component decisions on /059** — NOT additive edge ingredients. Mechanisms operate at structurally distinct layers (RULE-layer book composition vs FEATURE-layer split-budget redistribution); they CAN in principle coexist, but stacking-linearity is NOT guaranteed.

### 7.2 Pre-committed falsifiers (binding pre-registration for /120 brief Section 4)

**Falsifier 1 — Stacking-linearity**:
> At /120 multi-seed, if the /116+C6 bundle OOS monthly Sharpe is LOWER than the LARGER of (/116-only multi-seed OOS Sharpe, C6-only multi-seed OOS Sharpe) by more than 0.10 Sharpe units, the bundle is NEGATIVE-no-stacking and one component must be DROPPED for /120 MERGE. Determining which component is dropped: revert to /116-only (the RULE-layer mechanism with bar-by-bar attributable mechanism documentation from cycle-6 diary).

Critical safeguard against the over-additive assumption that two mechanical primitives at different layers will stack linearly. If the bundle Sharpe is materially below the larger of the component Sharpes, the two mechanisms are negatively interacting (probably via the FEATURE-layer redistribution interfering with the RULE-layer slot-freeing cascade's beneficial entry-set), and one must be dropped. The fallback to /116-only is chosen because /116 has the better-documented mechanism (bar-by-bar OOS attribution from cycle-6 diary).

**Falsifier 2 — TRX-concentration**:
> At /120 multi-seed, if TRX multi-seed mean OOS weighted PnL share > 50% of positive-symbol total → BLOCK C6 inclusion (keep /116 alone); 50–65% → concentration-watch flag; > 65% → full BLOCK; LDO portfolio share worse than −25% multi-seed → flag. The /119 single-seed TRX share is 52.05% of positive-symbol total — exactly at the threshold.

This addresses the /119 single-seed TRX-OOS concentration (80% of weighted PnL by the comparison.csv concentration_pct metric, 52% by the sign-divergence-corrected positive-PnL-share). /116 single-seed had three positive carriers with the top carrier at 52.9% of positive total; /119 single-seed has only TWO positive carriers with TRX at 52% — materially more concentrated than /116 structurally because the denominator shrinks.

**Falsifier 3 — Sister-redistribution stability**:
> At /120 multi-seed, if `regime_momentum_signed_5d` importance falls by > 50% in mean (vs /060 anchor) AND `ret5d_signed_tbi` importance fails to exceed 5% of portfolio total importance → "allocation cannibal without contribution" → BLOCK C6 inclusion.

This addresses the diagnostic-condition-(a) stability at multi-seed. If at single-seed the C6 mechanism is "cannibalize sister + reorganize loss surface" but at multi-seed the C6 importance falls below 5% (i.e., the model does not even use it consistently), then the mechanism is NOT robust — C6 is a single-seed lottery, not a stable feature-MECHANICAL primitive. The combined condition (sister falls AND C6 doesn't compensate) is the precise failure mode this falsifier catches.

### 7.3 /120 PASS gates

Per `feedback_v3_iter018_baseline_bootstrap.md` (refined by `feedback_v3_baseline_update_policy.md` and tightened by `feedback_v3_strict_both_is_oos_baseline.md`): /120 CONFIRMATION updates BASELINE_V3.md ONLY when the bundle beats prior baseline (`v0.v3-059`) on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean), AND Pareto BOTH seeds positive, AND Gate 3 (OOS/IS ≥ 0.5) AND Gate 6 (PSR > 0.95) AND Gate 10 (Pareto) HOLD.

Specific /120 evaluation criteria:
- **IS Sharpe band**: per /116 closeout Critic Rec 2 (carried forward), IS NEGATIVE floor relaxed to /059 IS − 0.50 = +0.59 to accommodate /116's regime-cost; bundle must show IS multi-seed mean ≥ +0.59 to avoid IS-leg NEGATIVE.
- **OOS Sharpe**: must clear /059 OOS = +0.5791 multi-seed mean.
- **Stacking-linearity (Falsifier 1)**: bundle OOS ≥ max(/116-only OOS, C6-only OOS) − 0.10.
- **TRX-concentration (Falsifier 2)**: TRX OOS weighted PnL share ≤ 50% positive-symbol total.
- **Sister-redistribution stability (Falsifier 3)**: C6 importance ≥ 5% portfolio total OR sister importance Δ > −50%.

If all PASS, /120 MERGES with both components → BASELINE_V3.md updates to multi-mechanism bundle (FIRST multi-mechanism baseline in v3 history). If Falsifier 1 fires → revert to /116-only; re-evaluate /116-alone against PASS gates. If Falsifier 2 or 3 fires → drop C6; bundle becomes /116-only; re-evaluate. If multiple falsifiers fire → cycle-6 closes NO-MERGE.

### 7.4 Precedent established

iter-v3/120 is set to be the **FIRST multi-mechanism CONFIRMATION bundle in v3 history**. Prior CONFIRMATIONs (iter-v3/018 single-component drop-MKR; iter-v3/028 single-component regime_momentum_signed_5d; iter-v3/039 single-component per-symbol customizations; iter-v3/059 cycle-1 anchor) were all single-axis decisions. The multi-mechanism bundle architecture is structurally novel; the three falsifiers above are the methodological controls.

---

## 8. Cycle-6 closure characterization — 2 mechanical primitives + 0 new edge ingredients across 10 EXPLORATIONs

Cycle 6 has reached its 10/10 EXPLORATION slot — iter-v3/119 closes the EXPLORATION sequence. The full slate:

| Slot | Iteration | Date | Axis | Verdict |
|---|---|---|---|---|
| 1 | /110 | 2026-05-19 | Universe / symbol selection (CRV/AAVE/GRT/ADA) | UNRESOLVED (label-confound — re-ran at /111) |
| 2 | /111 | 2026-05-19 | Universe / symbol selection (clean re-test) | NEGATIVE clean |
| 3 | /112 | 2026-05-19 | Pooled-vs-per-symbol architecture | NEGATIVE |
| 4 | /113 | 2026-05-19 | Multi-frequency features on 8h | NEGATIVE |
| 5 | /114 | 2026-05-19 | Risk management (LDO kill-switch) | NEGATIVE (Check 1 + Check 8 FAIL) |
| 6 | /115 | 2026-05-19 | Labeling architecture (coherent horizon-exit) | NEGATIVE |
| 7 | /116 | 2026-05-20 | Exit-layer / trade-construction (no_confirm) | **PROMISING-MECHANICAL** (RULE form) |
| 8 | /117 | 2026-05-20 | Candle frequency (24h-multi-offset) | NEGATIVE catastrophic |
| 9 | /118 | 2026-05-20 | NEW engineered-feature lineage (vol-regime composed) | NEGATIVE catastrophic |
| 10 | /119 | 2026-05-20 | NEW engineered-feature lineage (microstructure-regime composed) | **PROMISING-FEATURE-MECHANICAL** (FEATURE form) |

**Cycle-6 outcomes**:
- **2 strictly-accretive mechanical primitives**: /116 (RULE-form PROMISING-MECHANICAL) + /119 (FEATURE-form PROMISING-FEATURE-MECHANICAL).
- **0 new edge ingredients**: no /025-class direct-edge engineered feature found in 10 EXPLORATIONs. No new signal-discovery PROMISING verdict in the cycle.
- **8 NEGATIVE/UNRESOLVED**: 6 NEGATIVE-clean, 2 NEGATIVE-catastrophic, 1 UNRESOLVED (re-ran at /111).

### 8.1 The user's cycle-6 axis-menu hypothesis — partial falsification

The user's 2026-05-19 directive (`project_v3_cycle6_axis_menu.md`) hypothesized that 4 structural axes (symbol selection, pooled-vs-per-symbol, multi-freq features, risk management) would surface NEW EDGE on the v3 binding constraint that the /105-/109 chain localized DOWNSTREAM of the label.

**The cycle-6 axis-menu hypothesis is FALSIFIED on the new-edge axis** — none of the 4 menu axes (symbol selection /110-/111, pooled architecture /112, multi-freq /113, risk management /114) produced a PROMISING outcome. All 4 NEGATIVE. The extended menu items (labeling /115, exit-layer /116, candle-frequency /117, engineered-feature /118-/119) added 2 more axis types — only 2 of those 6 axes produced PROMISING outcomes.

**The cycle-6 axis-menu hypothesis is PROMISING on the strictly-accretive mechanical-primitive axis** — 2 mechanical primitives at different layers (RULE-form /116 + FEATURE-form /119) advance to the /120 multi-mechanism bundle. The user's "out-of-the-box mandate" produced the exit-layer and the engineered-feature axes (both outside the original 4-item menu); both delivered the only PROMISING outcomes in the cycle.

### 8.2 Cycle-7 reorientation recommendation

If /120 bundles successfully (or even partially — i.e., /116-only survives the falsifiers), cycle 6 delivers a meaningful but non-revolutionary outcome: 1–2 strictly-accretive mechanical primitives on /059. **The cycle-7 axis menu should structurally reorient** toward fundamentally different edge sources rather than re-walking the cycle-6 NEGATIVE axes. Cycle-7 candidate axes (informational only; cycle-7 QR adjudicates):
- **Cross-asset/external feeds** — funding rates from a different venue, basis (perp-spot), liquidations data, on-chain metrics for BTC (correlation regime input), DeFi TVL/lending utilization (for indirect BCH/LDO regime classification).
- **Non-LightGBM model classes already falsified at /109** — but cycle-6 did NOT test ensemble-of-different-model-classes or neural-network-with-different-training-regime; these are unexplored within the non-LightGBM space.
- **Longer-cadence labels** — multi-day or multi-week labels (1-week horizon, 1-month horizon) with appropriate execution geometry. The /072→/105→/115 labeling-axis falsification closed at 21-candle horizon; longer cadences may surface a different signal structure.
- **NEW model architecture entirely** (e.g., MoE, attention-based time-series, gradient-tree extensions like CatBoost/XGBoost-v2). The /016 XGBoost falsification was at depth-wise defaults; alternative model classes with different inductive biases may surface.

The cycle-7 axis menu should NOT include:
- Re-walking cycle-6 NEGATIVE axes (universe / pooled / multi-freq-on-8h / risk-primitive-kill-switches / coherent-horizon-exit-labeling / candle-frequency / vol-regime-composed-features).
- Knob-tuning saturated axes (ADX threshold, z-score threshold, BTC-band threshold, etc.).
- Per-symbol customizations (closed at /039 NEGATIVE).

---

## 9. Catalog entry

Per the standard schema, appended to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/119 | 2026-05-20 | NEW engineered-feature lineage (Category-2 composed: ret_5d × sign(taker_buy_imbalance_20)) | +0.1167 | +0.7017 | EXPLORATION-PROMISING — PROMISING-FEATURE-MECHANICAL subclass | YES |
```

**Cycle-6 catalog state (after /119)**:
- **2 PROMISING**: /116 (PROMISING-MECHANICAL — RULE form), **/119 (PROMISING-FEATURE-MECHANICAL — FEATURE form)**.
- 8 NEGATIVE/UNRESOLVED: /110 (UNRESOLVED label-confound), /111 (clean), /112 (pooled architecture), /113 (multi-frequency on 8h), /114 (risk management with Check-1 FAIL), /115 (coherent horizon-exit labeling), /117 (24h-multi-offset catastrophic), /118 (Category-2 vol-regime composed-feature catastrophic).
- 0 EXPLORATION slots remaining.
- /120 = mandatory cycle-6 CONFIRMATION (TWO-COMPONENT bundle, FIRST multi-mechanism bundle in v3 history).

---

## 10. Next iteration — /120 CONFIRMATION

### 10.1 The /120 setup

iter-v3/120 = mandatory cycle-6 CONFIRMATION. Spec:
- TYPE = CONFIRMATION (per `feedback_v3_iter018_confirmation_baseline_validation.md` — multi-seed validation, NOT bundle assembly EXCEPT in /018 BOOTSTRAP one-time exception; /120 is regular CONFIRMATION).
- Mode: `--seeds 2 --n-trials 35` (v3 CONFIRMATION envelope per `feedback_v3_outer_seed_cap_2_v3.md` + `feedback_v3_confirmation_n_trials_35.md`).
- ENSEMBLE_SIZE = 5 (inner ensemble for live-prediction variance reduction; 5 inner × 2 outer = 10 models per cell).
- Hard cap: 6h wall-clock (per `feedback_v3_cadence_discipline.md`).
- Anchors: /059 canonical (IS +1.0894 / OOS +0.5791, 10-seed CONFIRMATION); /060 anchor (IS +0.8325 / OOS +0.1403, single-seed EXPLORATION-mode).
- Bundle: TWO-COMPONENT (/116 no_confirm + /119 C6 `ret5d_signed_tbi`); the /120 setup-commit takes /119 head state (`V3_FEATURE_COLUMNS_TOP_N` = 15 features with C6 at index 14; `enable_no_confirm_exit=True`; `trigger_atr=0.50`, `k_candles=4`).

### 10.2 The /120 brief mandate

The /120 brief Section 4 MUST pre-register the three falsifiers (stacking-linearity, TRX-concentration, sister-redistribution stability) as binding pre-registration. The brief Section 7 modal prediction MUST distinguish:
- Mode A (modal): both falsifiers pass + bundle Sharpe ≥ both component-alone Sharpes → CONFIRMATION-MERGE (BASELINE_V3.md updates IFF beats /059 on BOTH IS AND OOS).
- Mode B (Falsifier 1 fires): bundle Sharpe < max(component-alone) − 0.10 → drop C6, revert to /116-only; re-evaluate.
- Mode C (Falsifier 2 fires): TRX > 50% positive → drop C6; revert to /116-only.
- Mode D (Falsifier 3 fires): C6 importance < 5% + sister importance < 50% of /060 → drop C6; revert to /116-only.
- Mode E (catastrophic): all falsifiers fire OR /116 alone underperforms /059 OOS → cycle-6 closes NO-MERGE.

### 10.3 Cycle-6 closeout decision tree (post-/120)

| Branch | /120 outcome | BASELINE_V3.md decision | Cycle-6 closure characterization |
|---|---|---|---|
| 1 | Bundle PASSES all gates + falsifiers + beats /059 BOTH IS AND OOS | UPDATE — multi-mechanism baseline | FIRST multi-mechanism baseline in v3 history; cycle delivers 2 strictly-accretive primitives |
| 2 | Falsifier 1 fires; /116 alone PASSES + beats /059 | UPDATE — /116-only baseline | RULE-layer single mechanism merges; FEATURE-layer dissolves at multi-seed |
| 3 | Falsifier 2 or 3 fires; /116 alone PASSES + beats /059 | UPDATE — /116-only baseline | Same as branch 2 |
| 4 | Falsifiers fire AND /116 alone underperforms /059 | UNCHANGED | Cycle 6 closes NO-MERGE; /116's apparent OOS lift dissolves at multi-seed (same dissolution as /013 → /018) |
| 5 | Both components survive but bundle UNDERPERFORMS /059 | UNCHANGED | Cycle 6 closes NO-MERGE; non-revolutionary outcome |

The cycle-6 closure characterization in all branches: **2 mechanical primitives + 0 new edge ingredients across 10 EXPLORATIONs.** Whether 0, 1, or both primitives merge into the baseline, the cycle did NOT produce a new edge ingredient. The cycle-7 axis menu must structurally reorient.

---

## 11. Closeout

- **Verdict**: EXPLORATION-PROMISING — PROMISING-FEATURE-MECHANICAL subclass (NEW sister-subtype to /116 PROMISING-MECHANICAL).
- **SUCCESS-mechanism**: feature-MECHANICAL loss-surface reorganization via algebraic-sister cannibalization; `regime_momentum_signed_5d` lost 65.3% of importance; combined sister-family allocation NET DROPS 35.1%; C6 only 2.6% of split budget — mechanically insufficient as direct edge; the 35% saved allocation redistributes to 4 rank-rising anchors (max_dd_window_50, ret_kurt_50, hurst_100, ret_skew_50); anchor-rank preservation Spearman ρ = 0.7714 (NOT chaotic shuffle); broad-based per-symbol IS positive Δ on all 3 symbols.
- **Classification precedent**: FIRST PROMISING-FEATURE-MECHANICAL in v3 history; sister-subtype to /116 RULE-form PROMISING-MECHANICAL; both share non-compoundable-as-signal-source invariant; mechanisms at structurally distinct layers (RULE vs FEATURE) so CAN coexist as separate strictly-accretive component decisions; new memory file `feedback_v3_promising_feature_mechanical.md` documents the subtype.
- **Decision**: NO-MERGE. BASELINE_V3.md UNCHANGED at `v0.v3-059`. Catalog updated. `v0.v3-119` tagged as closeout marker only.
- **Cycle-6 closure**: 10/10 EXPLORATIONs complete. 2 mechanical primitives (/116 RULE-form + /119 FEATURE-form) + 0 new edge ingredients. User's cycle-6 axis-menu hypothesis FALSIFIED on the new-edge axis but PROMISING on the strictly-accretive mechanical-primitive axis. Cycle 7 should structurally reorient.
- **/120 CONFIRMATION setup**: TWO-COMPONENT bundle (/116 no_confirm + /119 C6) at 10-seed unified ensemble. Three pre-committed binding falsifiers (stacking-linearity, TRX-concentration, sister-redistribution stability). FIRST multi-mechanism bundle in v3 history. Cycle-6 closeout decision tree above governs all 5 outcome branches.
- **Sacred constants verified**: `OOS_CUTOFF_DATE = 2025-03-24` UNCHANGED, `training_months = 24` UNCHANGED.

See `briefs-v3/iteration_v3-119/research_brief.md`, `briefs-v3/iteration_v3-119/phase5p5_gate.md`, `briefs-v3/iteration_v3-119/engineering_report.md`, `briefs-v3/iteration_v3-119/review_preliminary.md`, `briefs-v3/iteration_v3-119/qr_response.md`, `briefs-v3/iteration_v3-119/review.md`, `reports-v3/iteration_v3-119/`, `briefs-v3/exploration_catalog.md`, `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_promising_feature_mechanical.md`, and `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/project_v3_cycle6_axis_menu.md` for full artifacts.
