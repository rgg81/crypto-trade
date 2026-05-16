# iter-v3/086 — Cycle 3 #5 EXPLORATION — NEW crypto-native data feed: perp-spot BASIS family / INERT

**Date**: 2026-05-16
**Type**: EXPLORATION (cycle 3 slot #5 of 10). Single-axis: a NEW crypto-native DATA FEED — the perp-spot basis — fetched as spot 8h klines, with a 3-feature basis family (`basis_zscore_30`, `basis_momentum_3`, `basis_extreme_flag`) appended to `V3_FEATURE_COLUMNS_TOP_N` (14→17). EXPLORATION-mode 3-seed, `--n-trials 35`, 315 Optuna trials, wall-clock 0.72h.
**Axis**: Direction 1 — a NEW crypto-native data feed (the highest-value untried axis named by the /085 Critic Rec #4). QR-research-and-EDA-driven (brief Section 10: Ackerer/Hugonnier/Jermann "Perpetual Futures Pricing" *Mathematical Finance* 2024-25; AEA 2026 "Perpetual Futures and Basis Risk"; BitMEX 2025 Q3 derivatives report; EDA `c9bf818`).
**Verdict**: EXPLORATION-MERGE per Critic FINAL `a3297e1` — OVERALL=MERGE certifies the methodology of a clean EXPLORATION, including the highest-risk surface (the NEW spot-data feed, audited independently in `basis_v3.py` and `_cmd_fetch_spot`). The Critic gates methodology soundness, NOT advancement; the Section 8 classification is the QR's Phase-8 call.
**Classification**: **INERT** (brief Section 8.4). F1 INERT falsifier satisfied (the 3 basis features rank 15/16/17 of 17, portfolio-pooled, combined share ~4.3%); neither LOCKED SUSPICIOUS sub-channel fires (the Phase-8 roster-diff: F2 = +0.9630 candle, below the +1.0 LOCKED threshold; F3 = +0.3489 candle, below +1.0). SUSPICIOUS does NOT fire, so by the disjunctive precedence INERT is canonical.
**Advancement**: does NOT advance to the iter-v3/092 cycle-3 CONFIRMATION bundle — INERT axes carry no edge ingredient. The 3 basis feature columns are dropped at the /087 setup.
**BASELINE_V3.md**: **UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. An EXPLORATION cannot update the baseline regardless. The /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed) stays the cycle-3 intra-cycle anchor.
**Branch**: `iteration-v3/086`

---

## 1. What was done — the single axis

iter-v3/086 is the FIFTH EXPLORATION slot of v3 cycle 3. Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 3 runs 10 SEPARATE EXPLORATIONs (/082-/091) followed by 1 SEPARATE CONFIRMATION (/092); the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

The single axis: a **NEW crypto-native data feed** — the perp-spot basis. Every prior v3 feature is derived from OHLCV or the funding rate; the basis required acquiring a feed v3 has never fetched (spot 8h klines) and computing the perp-vs-spot premium `(perp_close − spot_close) / spot_close`. The /085 Critic Rec #4 explicitly named a NEW crypto-native data feed as the highest-value untried axis after the funding axis closed at 5 data points; iter-v3/086 executes that directive.

`V3_FEATURE_COLUMNS_TOP_N` grew 14 → 17 by appending three basis features:

- `basis_zscore_30` — 30-bar past-only z-score of the basis (crowding LEVEL)
- `basis_momentum_3` — 3-bar change of the lagged basis (crowding MOMENTUM)
- `basis_extreme_flag` — 9-bar rolling mean of `sign(basis)` (crowding DIRECTION + PERSISTENCE)

All three are computed on `basis.shift(1)` — one full candle lag, STRICTER than the funding convention (the basis needs both the perp and spot CLOSE, so it is knowable only at bar t close). Nothing else changed — no labeling change, no symbol change, no risk-gate change, no model-architecture change, no seed change. The 11-knob `_canonical_v059` config-accretion check confirmed all 11 RiskV3 knobs /059-canonical.

The QE Phase-6 build productionised the QR prototype: a new `crypto-trade fetch-spot` CLI subcommand (`data.binance.vision` monthly spot-kline archives + `/api/v3/klines` REST fallback, with mandatory 2025-01 microsecond→millisecond timestamp normalisation), a track-isolated `basis_v3.py` feature module (the `cross_btc_v3.py` external-CSV-merge pattern), a `GROUP_REGISTRY["basis_v3"]` entry, and the `data/spot/` cache (BCH 7037 / LDO 4358 / TRX 8642 rows). Two mandatory non-axis baseline-restore/cleanup actions accompanied the setup (Critic /085 Recs #1/#3): (a) `funding_regime_momentum_5d` dropped from `V3_FEATURE_COLUMNS_TOP_N` + added to the runner ABSENT-assertion list; (b) the stale `validation_v3.py:594` docstring (`88 4-symbol` → `66` 3-symbol) corrected.

## 2. Results — vs the cycle-3 EXPLORATION-MODE-REFERENCE (/084)

Per the MANDATORY two-anchor structure (Critic /084 Rec #2): the intra-cycle Δ is classified against **ANCHOR 1 — the /084 EXPLORATION-MODE-REFERENCE, IS +0.8325 / OOS +0.3322 (3-seed EXPLORATION-mode, current data)** — architecturally matched to /086's own 3-seed EXPLORATION run. **ANCHOR 2 — the /059 CONFIRMATION baseline, IS +1.0894 / OOS +0.5791 (10-seed)** — is RESERVED for the iter-v3/092 CONFIRMATION and is NOT the comparison point here.

| Metric | /084 EXPLORATION-MODE-REFERENCE | /086 (this run) | Δ /086 − /084 |
|---|---:|---:|---:|
| IS monthly Sharpe | **+0.8325** | **+0.8951** | **+0.0626** |
| OOS monthly Sharpe | **+0.3322** | **+1.0284** | **+0.6962** |
| OOS/IS monthly Sharpe ratio | 0.3990 | **1.1489** | — |
| IS daily Sharpe | 1.7115 | 1.7940 | — |
| OOS daily Sharpe | 0.8745 | 2.7100 | — |
| IS MaxDD | 31.87% | 23.77% | — |
| OOS MaxDD | 35.78% | 24.52% | — |
| IS n_trades | 159 | 187 | +28 |
| OOS n_trades | 104 | 91 | −13 |
| PBO (per-cell mean) | 0.1278 | **0.1343** | — |
| frac_positive_paths (CPCV) | 0.644 | **0.644** | 0 |
| PSR | 1.0000 | 1.0000 | — |
| DSR (legacy) | 0.0000 | 0.0000 | EXPLORATION-mode artifact |
| DSR_relative_B4 | 0.8154 | 1.0000 | EXPLORATION-mode artifact |
| n_trials (Optuna total) | 315 | 315 | — |
| n_eff | 19 | 19 | — |

CPCV path Sharpe distribution: q25 = −0.243, q50 = +0.335, q75 = +0.838. `frac_positive_paths = 0.644` clears the 0.55 Gate-10-CPCV threshold and PBO 0.1343 clears the 0.40 gate — the run is a clean, valid measurement, not a methodology failure.

**Per-symbol OOS attribution** (`comparison.csv` per_symbol block, `weighted_pnl`):

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +31.4846 | 34 | 44.1% | 78.15% |
| TRXUSDT | +23.4435 | 46 | 47.8% | 58.19% |
| LDOUSDT | −14.6395 | 11 | 27.3% | −36.34% |

**Per-symbol IS attribution** (`in_sample/per_symbol`, `net_pnl%`): BCH 90 trades / 40.0% WR / +22.08%; LDO 12 / 58.3% / +42.93%; TRX 85 / 31.8% / −17.03%. BCH OOS concentration at 78.15% persists as the known v3 fragility, not /086's scope. LDO OOS WR collapses to 27.3% with negative wpnl — LDO remains the persistent directionally-weak symbol.

**The 3 basis features' importance** (last-IS-month, portfolio-pooled, `conditional_orthogonality.csv`): rank **15/17 (`basis_zscore_30`, share 0.01871)**, **16/17 (`basis_momentum_3`, 0.01411)**, **17/17 (`basis_extreme_flag`, 0.00983)** — all three occupy the bottom-3 positions of 17, combined share **0.04265** (a 2.15× gap below the weakest anchor `regime_momentum_signed_5d` at 0.04034 — three features together carry roughly what one weakest anchor carries alone). Max |IC| vs the 14-anchor stack: `basis_zscore_30` 0.2689, `basis_momentum_3` 0.0601, `basis_extreme_flag` 0.3273 — all below the 0.50 strict target and the 0.70 hard gate (Critic Check 4 PASS). The basis family is orthogonal enough to pass the IC gate but is INERT-by-importance — the model declines to allocate ranked split capacity to it.

## 3. PATH classification — INERT — and the F2/F3 roster-diff adjudication

The brief Section 8 LOCKED taxonomy runs disjunctive precedence, first match canonical: **SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT.** Anchor for all Δ: ANCHOR 1 (/084, IS +0.8325 / OOS +0.3322).

### 3.1 SUSPICIOUS (8.3) — evaluated FIRST, and it does NOT fire

Section 8.3 fires on ANY of four sub-channels:

- **(a) OOS/IS monthly Sharpe ratio > 3.0** — /086 ratio = 1.0284 / 0.8951 = **1.1489** → does NOT fire.
- **(b) OOS-DOMINANT sub-mode — IS Δ < 0 AND OOS Δ ≥ +0.20** — /086 IS Δ = **+0.0626 ≥ 0** → mechanically foreclosed; does NOT fire. (The OOS Δ is +0.6962 ≥ +0.20, but the IS Δ < 0 leg fails — the strict OOS-DOMINANT sub-mode requires BOTH legs.)
- **(c) F2 — the /076 trade-selection sub-channel** — the added-vs-removed OOS-roster mean-duration gap > +1.0 candle.
- **(d) F3 — the full-OOS-roster mean-duration shift** > +1.0 candle vs /084.

**The Phase 7/8 roster-diff (the Critic-mandated check, `analysis/iteration_v3-086/roster_diff_oos.py`).** The /085 closeout's `roster_diff_oos.py` is the method precedent. Comparing the /086 and /084 OOS trade rosters by the trade-identity key `(symbol, direction, open_time, entry_price)` — /086 has 91 OOS trades, /084 has 104; **64 are identical**, /086 **ADDS 27** and **REMOVES 40**.

**F2 — sub-channel (c).** The added set mean duration = **6.9630 candles**; the removed set mean duration = **6.0000 candles**:

```
added-minus-removed OOS mean-duration gap  =  6.9630 − 6.0000  =  +0.9630 candles
```

**+0.9630 ≤ +1.0 — the LOCKED Section 8.3(c) F2 falsifier does NOT fire.** The result is robust: re-run under three distinct trade-identity keys (`sym+dir+open+entry`, `sym+open_time`, `sym+dir+open`) the gap is +0.9630 / +0.9630 / +0.9630 — identical across keys, not a key artifact.

**F3 — sub-channel (d).** The /086 full-OOS-roster mean duration = **6.7912 candles** (91 trades); /084's = **6.4423 candles** (104 trades):

```
full-OOS-roster mean-duration shift  =  6.7912 − 6.4423  =  +0.3489 candles
```

**+0.3489 ≤ +1.0 — the LOCKED Section 8.3(d) F3 falsifier does NOT fire.**

**Neither LOCKED SUSPICIOUS sub-channel fires; the ratio gate and the OOS-DOMINANT sub-mode also do not fire. SUSPICIOUS does NOT fire.** The F2 gap landed +0.0370 candle below the trigger — close, but a LOCKED numeric falsifier is honored exactly as written. The /085 discipline (`feedback_v3_per_symbol_target_axis_falsifier.md`: "predictions are estimates; falsifiers are gates") cuts both ways: the same rule that fired SUSPICIOUS at /085's +1.578 (no mechanism-downgrade) forbids rounding /086's +0.9630 UP across the +1.0 line. +0.9630 is below +1.0; F2 does not fire.

### 3.2 The substantive texture — for the record (consistent with the INERT call)

- **Per-symbol OOS dur-gap**: BCH **+1.08** (12 added / 15 removed), LDO **+8.25** (3 added / 4 removed — tiny-n), TRX **−0.45** (12 added / 21 removed). The aggregate +0.9630 is pulled UP by LDO's +8.25 on a 3-trade-vs-4-trade set; the dominant-volume symbols BCH (+1.08) and TRX (−0.45) average near the threshold. The LDO leg is the small-n noise that the /085 closeout already flagged as the texture caveat — but unlike /085, here even with LDO's pull the aggregate stays below +1.0.
- **The net OOS wpnl from the roster swap is +26.69** (added set vs removed set) — the roster swap is net OOS-PnL-accretive, but the exit-reason mix shows it is not a clean regime-loading signature: the added set is 8 TP / 18 SL / 1 timeout, the removed set is 30 SL / 10 TP. /086 removed 30 stop-loss trades and added back a mix — the OOS lift is the model picking a different (here favorable) roster, not a duration-extension toward riding an uptrend. This is consistent with the Optuna-perturbation mechanism (Section 3.4).

### 3.3 The other taxonomy branches (foreclosed, for completeness)

- **NEGATIVE (8.2)** does NOT fire: IS Δ +0.0626 ≥ −0.10 AND OOS Δ +0.6962 ≥ −0.20.
- **PROMISING (8.1)** is mechanically foreclosed: the binding importance leg requires at least one basis feature at rank ≤ 9/17 with last-IS-month absolute importance ≥ 30 on ≥ 1 symbol — the basis features are at portfolio-pooled ranks 15/16/17, so no member clears rank ≤ 9. (The PROMISING importance leg is the explicit F1-falsifier complement.)
- **INERT (8.4)** — **fires**, on the F1 feature-level signature: all 3 basis features rank ≥ 15/17 (bottom-3-of-17) by portfolio-pooled last-IS-month importance. The brief's F1 trigger is "all 3 rank ≥ 15/17 across ≥ 2 of 3 symbols"; the `conditional_orthogonality.csv` exports portfolio-pooled importance only, and the portfolio-pooled evidence satisfies the portfolio-level version of the condition (all 3 at ranks 15/16/17). INERT is fourth in the disjunctive precedence; since SUSPICIOUS and NEGATIVE do NOT fire and PROMISING is foreclosed, **INERT is the canonical classification.**
- **NULL-RESULT (8.5)** does NOT fire: the /086 OOS roster is NOT bit-identical to /084's (64 common of 91/104; 27 added, 40 removed).

### 3.4 The +0.696 OOS lift is an Optuna-search-perturbation artifact, NOT basis signal

The +0.6962 OOS monthly Sharpe lift vs the /084 anchor is materially larger than the +0.0626 IS lift. This IS/OOS asymmetry is **the exact /082 signature** — an INERT feature family that ranks bottom-of-stack yet moves OOS by perturbing the Optuna search. A 3-feature family ranked 15/16/17-of-17 by importance (combined share 4.3%, a 2.15× gap below the weakest anchor) cannot have *produced* +0.696 of OOS Sharpe as signal — effectively-unused columns have no path to the OOS objective except via the search-space-perturbation side channel. This is the documented `feedback_v3_inert_features_at_higher_budget.md` mechanism: adding 3 columns expands the Optuna hyperparameter search space, and at 3-seed single-lineage EXPLORATION resolution the perturbed search lands a different (here favorable) OOS hyperparameter draw. /082's INERT funding family did exactly this (IS Δ −0.012, OOS Δ +1.21); /086's basis family reproduces the pattern (IS Δ +0.063, OOS Δ +0.696). The +0.696 is an artifact of 3 INERT columns, not a perp-spot-basis edge discovery. The brief pre-registered this honestly (Section 7: INERT ≈ 50% as the single most-likely outcome; Section 2.4's incremental-information probe was already NEGATIVE on all 3 symbols).

The Critic's preliminary read (review.md Rec #1) reached the same conclusion — "the +0.6962 OOS lift ... is the exact /082 signature ... most plausibly *not* basis signal" — while explicitly delegating the F2/F3 adjudication to this Phase 8. This Phase 8 ran the delegated roster-diff: neither F2 nor F3 fires, so the INERT verdict stands as the canonical classification (the Critic's preliminary read was INERT-pending-roster-diff; the roster-diff confirms it).

## 4. Section 7 prediction check — INERT inside the pre-registered set, top of the distribution

The brief Section 7 pre-registered the failure-mode distribution: **≈50% INERT-by-importance, ≈25% SUSPICIOUS, ≈15% NEGATIVE, ≈10% PROMISING.** The realized classification is **INERT** — the single most-likely outcome, pre-registered at ≈50% and named in the Section 7 prose as "the single most-likely outcome." The calibration verdict is **clean**: the brief's central forecast was correct on both the mechanism (INERT-by-importance — the basis features rank bottom-3, exactly as predicted) and the texture (the +0.696 OOS lift is the documented Optuna-perturbation artifact, exactly the Section-7 caveat that an INERT family "*might* lift OOS if the LightGBM learns the LDO extreme-bucket interaction" — except the lift is search-perturbation, not the LDO interaction). The /085 closeout had flagged that the Section-7 prose must give the trade-selection SUSPICIOUS sub-channel a non-tail weight; the /086 brief honored that — SUSPICIOUS was weighted at ≈25% with both F2/F3 sub-channels pre-registered as LOCKED gates — and the roster-diff then showed SUSPICIOUS did not fire (F2 +0.963 below +1.0). The outcome landed at the top of the pre-registered distribution; the prediction set was correct.

## 5. The 7-feed structural verdict — v3's architecture does not allocate split capacity to crypto-native features

iter-v3/086 is the **7th non-OHLCV crypto-native feature family v3 has tried, and all 7 are INERT-by-importance:**

| Feed | Iterations | Construction | Importance verdict |
|---|---|---|---|
| Funding rate | /019, /023, /024 | Category-1 direct z-score (`funding_rate_zscore_30`, BTC cross-asset variant) | INERT — rank bottom-of-stack |
| Funding rate | /082 | Category-1 direct 4-channel family (sign-persist / momentum / accel / divergence) | INERT — rank 15/16/17/18 of 18 |
| Funding rate | /085 | Category-2 composed sign-switch (`funding_regime_momentum_5d`) | INERT — rank 13/14/15 of 15 |
| Microstructure | /015 | `tbr_zscore_30` (taker-buy-ratio z-score) | INERT — rank 14/14 |
| Perp-spot basis | /086 | Category-1 direct 3-feature family (zscore / momentum / extreme-flag) | INERT — rank 15/16/17 of 17 |

**Seven independent crypto-native data sources — funding (5 data points across two construction families), microstructure (1), basis (1) — every one ranks bottom-of-stack on the v3 LightGBM at the BCH/LDO/TRX 3-symbol per-symbol scale.** This has crossed from a per-feed result into a **structural verdict on the v3 architecture**: a depth-3-5 LightGBM trained per-symbol on ~2700-5700 IS rows (LDO only 2741) does not allocate ranked split capacity to crypto-native sentiment features regardless of the feed or the construction. The architecture's split budget is consumed by the price/return/volatility/regime features; crypto-native features — which encode positioning/crowding information genuinely orthogonal to OHLCV — are systematically declined.

**The /087+ axis selection MUST NOT be an 8th crypto-native feature family on the same architecture.** Per the Critic Rec #2, the remaining structural levers are **Direction 2 (universe expansion / breadth)** and **Direction 3 (a multi-symbol-pooled model)**. The basis feed itself is a sound engineering investment — the `fetch-spot` subcommand, `basis_v3.py`, and `data/spot/` cache are RETAINED as reusable infrastructure; only the 3 basis feature columns are dropped. This 7-feed structural verdict is recorded in BASELINE_V3.md Dead Ideas and `cycle3_plan.md`.

## 6. Critic integration — OVERALL=MERGE + 3 Recommendations

**Critic FINAL `a3297e1`** (`briefs-v3/iteration_v3-086/review.md`): a single-round full review, OVERALL=**MERGE**. The MERGE verdict CERTIFIES the methodology of a clean EXPLORATION — including the highest-risk surface, the NEW spot-data feed, audited independently in `basis_v3.py` and `main.py::_cmd_fetch_spot`. It is a methodology certification, NOT an advancement or an edge endorsement.

- **All 8 mandatory Checks + 4 optional Checks PASS.** Check 1 (look-ahead) PASS — four sub-surfaces audited independently: the spot→perp left-join on `open_time` (no forward-fill, NaN on miss), the microsecond/millisecond normalisation (`_to_ms` divides by 1000 when `val ≥ 1e15`; a missed normalisation fails-to-join conservatively rather than misaligning), forming-candle handling (REST path drops `ct ≥ now_ms`; archive path is structurally forming-candle-free), and the basis past-only construction (`basis.shift(1)` — stricter than funding; the committed spike-perturbation test + the EDA T4 audit both confirm bars < K bit-identical). Check 2 (embargo) PASS — `REQUIRED_GAP = (21+1)×3 = 66`, `PER_CELL_GAP = 22`. Check 3 (multiple-testing) — per-cell PBO 0.1343 < 0.40 PASS; `frac_positive_paths` 0.644 ≥ 0.55 PASS; DSR/PSR informational at EXPLORATION mode. Check 4 (IC) PASS — max |IC| 0.3273, below the 0.50 strict target. Check 5 (ADF) PASS — basis features stationary (`basis_extreme_flag` weakest at 76.4% but >70%). Check 6 (Gate-10-CPCV) PASS. Check 7 (reproducibility) PASS — explicit 17-element `feature_columns`, 3-tuple `ENSEMBLE_SEEDS` literal, 3-row OOS trade-PnL spot-check reconciles exactly. Check 8 (hypothesis-implementation alignment) PASS — exactly one axis, zero scope creep, `funding_regime_momentum_5d` asserted ABSENT. Checks 9-12 all PASS.
- **Critic preliminary result-read — INERT-by-importance, with the SUSPICIOUS sub-channels delegated to Phase 8.** The Critic's forensic input: the F1 INERT falsifier is satisfied at the portfolio-pooled level (ranks 15/16/17, combined share 0.04265, 2.15× gap below the weakest anchor); the PROMISING importance leg is mechanically foreclosed; the +0.6962 OOS lift is the exact /082 Optuna-perturbation signature. The Critic explicitly delegated F2/F3 (sub-channels c/d) to this Phase-8 roster-diff "with the explicit recommendation that the +0.696 OOS lift WARRANTS the full trade-selection-sub-channel scrutiny." **This Phase 8 ran the delegated roster-diff; neither F2 (+0.9630) nor F3 (+0.3489) fires; the FINAL classification is INERT** (Section 3 above) — consistent with the Critic's preliminary read.
- **Three Critic Recommendations — all integrated:**
  1. **The roster-diff (delegated F2/F3 adjudication).** DONE — `analysis/iteration_v3-086/roster_diff_oos.py` (committed). F2 added-minus-removed OOS mean-duration gap = +0.9630 candle ≤ +1.0 (does NOT fire; robust across 3 trade-identity keys); F3 full-roster mean-duration shift = +0.3489 candle ≤ +1.0 (does NOT fire). Neither LOCKED SUSPICIOUS sub-channel fires → INERT is canonical.
  2. **The 7-feed structural verdict.** RECORDED in BASELINE_V3.md Dead Ideas and `cycle3_plan.md` — the basis feed is the 7th non-OHLCV crypto-native feature family v3 has tried (funding /019/023/024/082/085, microstructure /015, basis /086), all 7 INERT-by-importance. This is a structural verdict on the v3 architecture; /087+ MUST NOT be an 8th crypto-native feature family. The `fetch-spot` subcommand + `basis_v3.py` + `data/spot/` cache are RETAINED as reusable infrastructure (only the 3 feature columns are dropped).
  3. **The /087-setup mandate.** RECORDED in `cycle3_plan.md` — the /087 setup must drop the 3 basis features (revert `V3_FEATURE_COLUMNS_TOP_N` to the 14-feature /059 anchor) and add `basis_zscore_30` / `basis_momentum_3` / `basis_extreme_flag` to the runner's ABSENT-assertion list (the `funding_regime_momentum_5d` pattern). Per `feedback_v3_inert_features_at_higher_budget.md` an INERT feature must NOT be carried forward and must NOT be retested at a higher Optuna budget — do NOT carry the basis family to /092.

## 7. Decision — NO-MERGE

**NO-MERGE. BASELINE_V3.md is UNCHANGED — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. The /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed) stays the cycle-3 intra-cycle anchor.**

iter-v3/086 classified **INERT** (brief Section 8.4 — the F1 feature-level signature; the 3 basis features rank 15/16/17 of 17 by portfolio-pooled importance; neither LOCKED SUSPICIOUS sub-channel fires). INERT axes carry no edge ingredient and do not advance to the CONFIRMATION bundle; an EXPLORATION cannot update the baseline regardless. The 3 basis feature columns are dropped at the /087 setup per Critic Rec #3. **No new git tag for a baseline update.** An EXPLORATION closeout marker tag `v0.v3-086` is issued (annotated; explicitly NOT a baseline update — the same pattern as `v0.v3-082` / `v0.v3-083` / `v0.v3-084` / `v0.v3-085`).

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched. `V3_MODELS` stays the 3-symbol BCH/LDO/TRX /059-canonical universe. `PER_CELL_GAP` stays 22.

## 8. Cycle-3 progress + Next Iteration

### Cycle 3 progress — 5/10 EXPLORATION slots done, 0 clean PROMISING

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | NEW crypto-native FEATURE FAMILY (funding-rate 4-channel, Direction 1) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /083 | symbol-universe EXPANSION 3→4 (+FILUSDT, Direction 2) | NEGATIVE |
| #3 | /084 | REFERENCE / METHODOLOGY — PER_CELL_GAP 43→22 fix + clean /059-config 3-symbol anchor re-run | REFERENCE-REANCHOR |
| #4 | /085 | NEW funding-regime-conditioned ENGINEERED feature (Category-2 composed, Direction 1) | SUSPICIOUS (trade-selection sub-channel) |
| #5 | /086 | NEW crypto-native DATA FEED — perp-spot basis 3-feature family (Direction 1) | **INERT** |
| #6-#10 | /087-/091 | TBD per QR research + EDA, Directions 2-3 | — |
| CONFIRMATION | /092 | best cycle-3 bundle (multi-seed validation) | pre-registered MERGE gates |

Cycle 3 has used 5 of its 10 EXPLORATION slots — outcome distribution: 1 SUSPICIOUS-OOS-DOMINANT, 1 NEGATIVE, 1 REFERENCE-REANCHOR, 1 SUSPICIOUS, 1 INERT — **0 clean PROMISING.** The pattern matches cycles 1 and 2 (each 0 clean PROMISING). The five cycle-3 EXPLORATIONs to date have closed the entire feature-construction-on-crypto-native-data axis: /082 (funding 4-channel), /085 (funding composed sign-switch), and /086 (perp-spot basis) jointly prove that NO feature family — funding, basis, or otherwise crypto-native — finds a v3 edge ingredient on the per-symbol depth-3-5 LightGBM architecture.

### iter-v3/087 — what it should be

**iter-v3/087 (cycle 3 #6) must be a genuinely bold STRUCTURAL axis in the Direction-2-or-Direction-3 space — NOT an 8th crypto-native feature family.** Per the Critic Rec #2, the 7-feed structural verdict is dispositive: the v3 per-symbol depth-3-5 LightGBM trained on ~2700-5700 IS rows does not allocate split capacity to crypto-native features regardless of the feed. The two remaining structural levers are:

- **Direction 2 — universe expansion / breadth, done WHOLESALE.** Not /083's single-weak-symbol-add (FILUSDT, which collapsed IS). A genuine breadth expansion — 5-8 liquid symbols added together — directly attacks the BCH ~78% OOS concentration and the 3-symbol single-bet fragility. The Fundamental Law (IR = IC × √breadth) says breadth is the lever v3 has never pulled at scale. The /087 QR must screen candidates on a genuine per-symbol IS-edge AND portfolio-aggregate-Sharpe-contribution screen (the /083/078 lesson: a per-symbol screen does not transfer to aggregate lift), and pre-register the holding-time predictor.
- **Direction 3 — a multi-symbol-pooled model, NON-NAIVE variant.** The naive pooled model was EDA-falsified at /085 (only 7/14 features sign-agree on feature→label IC across symbols; pooled+`symbol_id` breaks BCH). But a non-naive variant is untested — e.g. a pooled model with per-symbol calibration, a pooled model over a LARGER universe (Direction 2 + Direction 3 compound), or a pooled model with symbol-cluster grouping. Pooling shares statistical strength and is the natural architecture for the thin-data symbols (LDO at 2741 IS rows).

Per `feedback_v3_axis_selection_quant_discipline.md` + the cycle-3 research mandate, the /087 QR must do genuine WebSearch/WebFetch literature research, commit an `analysis/iteration_v3-087/*.py` IS-EDA script before the brief, and state BOTH anchors in brief Section 4.

**Hard constraints on /087** (carried from prior closeouts + the /086 Critic):
- /087 setup MUST drop the 3 basis features (`basis_zscore_30` / `basis_momentum_3` / `basis_extreme_flag`); revert `V3_FEATURE_COLUMNS_TOP_N` to the 14-feature /059 anchor stack; add the 3 names to the runner's pre-flight ABSENT-assertion list (the `funding_regime_momentum_5d` pattern) (Critic /086 Rec #3).
- Do NOT carry the basis family to /092 and do NOT retest it at a higher Optuna budget (`feedback_v3_inert_features_at_higher_budget.md`).
- The `fetch-spot` subcommand, `basis_v3.py`, and `data/spot/` cache are RETAINED as reusable infrastructure — they are NOT removed; only the 3 feature columns are dropped from `V3_FEATURE_COLUMNS_TOP_N`.
- Anchor intra-cycle Δ against the /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed); reserve the /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791, 10-seed) for /092. State BOTH anchors explicitly in brief Section 4.
- Pre-register the OOS/IS Sharpe ratio bound (> 3.0 → SUSPICIOUS), the OOS-DOMINANT sub-mode, AND the /076 trade-selection sub-channel (added-vs-removed OOS-roster mean-duration gap > +1.0 → SUSPICIOUS) in Section 4/8.
- Pre-register the holding-time / roster-composition predictor per `feedback_v3_is_oos_regime_divergence.md`; for a universe axis, pre-register the target-symbol-axis falsifier band per `feedback_v3_per_symbol_target_axis_falsifier.md`.
- Genuine WebSearch/WebFetch literature research in Phases 1-4, documented in brief Section 10.
- `V3_MODELS` is BCH/LDO/TRX at the /087 starting point; `PER_CELL_GAP` stays 22.
- CLOSED — do not re-propose: any 8th crypto-native feature family on the per-symbol architecture (the 7-feed structural verdict); the v3 funding axis (5 data points /019/023/024/082/085); the perp-spot basis feature family (/086); the microstructure feature family (/015); the Kaufman path-efficiency axis; the regime-conditional kill switch; the LDO→ADA universe swap; single-weak-symbol universe adds (FILUSDT /083); per-symbol PnL-share caps; the NAIVE multi-symbol-pooled model (EDA-falsified at /085); HBAR/AVAX (/021), ADA (/078), FILUSDT (/083) as universe-expansion candidates; gate-threshold knobs, ATR-multiplier tweaks, labeling tweaks on the same 14 features, instrumentation-only axes.

---

**Commit chain:**
- EDA SHA: `c9bf818` — `analysis/iteration_v3-086/{fetch_spot_klines,basis_feed_eda,basis_directional_probe}.py` + the t0/t1/t2/t3/t4/p1/p2/p3 CSVs
- Brief SHA: `8385398` (research brief); brief Section 10/11 EDA+setup-SHA backfill `152d035`
- Setup SHA: `47b9a35` (perp-spot basis feature family + funding-revert + docstring fix); `8fb2139` (fetch-spot production subcommand + 3-symbol v3 parquet regen)
- Phase 5.5 gate SHA: `98de6fc` (PASS — QR-driven basis-feed axis certified)
- Engineering report SHA: `ae9081e`
- Critic FINAL SHA: `a3297e1` (OVERALL=MERGE)
- Phase 8 roster-diff analysis SHA: `c0fbeab` — `analysis/iteration_v3-086/roster_diff_oos.py` (the Critic-mandated F2/F3 sub-channel adjudication)
- Diary + catalog + cycle3_plan + BASELINE_V3.md Dead-Ideas SHA: `51cefb6` (this closeout; SHA backfilled by the immediately-following commit)
**Reports**: `reports-v3/iteration_v3-086/`
**Tag**: `v0.v3-086` (EXPLORATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
