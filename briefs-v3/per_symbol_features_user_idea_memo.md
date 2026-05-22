# Research Memo — User Idea: "Custom-Made Features Per Symbol"

**Author:** Quant Researcher (v3)
**Date:** 2026-05-18
**Status:** EVALUATION memo (not a Phase-5 brief). EDA-grounded. NOT git-committed (backtest running on `iteration-v3/092`).
**EDA script:** `analysis/iteration_v3-092/per_symbol_feature_eda.py` (scratch, untracked, read-only on `data/features_v3/`)
**Idea (verbatim intent):** "Instead of using the same features for all symbol models, why not have custom-made features for each symbol?" — i.e. per-symbol feature SETS, not one shared set.

---

## 0. Bottom line up front

The user's instinct — symbols are heterogeneous, so the model should attend to different signals per symbol — is a real and well-posed quant question. I engaged it with per-symbol IC and per-symbol LightGBM importance EDA on the IS bar panel, plus a noise-floor simulation.

**The verdict is NO for the literal idea, and a QUALIFIED YES for one reframe.**

The decisive number: **per-symbol LightGBM gain-importance rankings are highly concordant across BCH / LDO / TRX — mean pairwise Spearman rho = +0.839** (BCH-LDO +0.763, BCH-TRX +0.837, LDO-TRX +0.916). The multivariate signal the model *actually uses* is essentially the same ranking on all three symbols. The shared 14-feature set is already near-optimal per-symbol; there is little headroom for per-symbol feature selection, and the univariate "divergence" that superficially suggests headroom is fully explained by sample noise (Section 1.3). Routes (a) bar-IC-driven per-symbol selection is **not worth a slot**. The one route with genuine novelty and a non-noise rationale is (b) **symbol-conditional features inside the pooled cross-sectional ranker** (`cross_sectional.py`, the live /088+ research line) — and even that is LOW priority, sketched in Section 4 as a fast-fail probe, not a headline axis.

---

## 1. TASK 1 — Per-symbol IC / importance EDA (the empirical core)

### 1.1 Setup

IS bar panel only (`open_time < OOS_CUTOFF_MS = 1742774400000`, 2025-03-24). Panel sizes are data-rich — **5,727 / 2,741 / 5,669 IS bars** for BCH / LDO / TRX — three orders of magnitude larger than the 83 / 9 / 79-trade roster. This is the right surface for a feature-ranking question; the trade roster is not.

Two targets: (i) a continuous 3-bar (~1-day) forward return; (ii) a ternary triple-barrier label (ATR 2.0 TP / 1.0 SL, 21-bar timeout, ATR shifted 1 bar — past-only, no look-ahead), the /059-architecture label. Candidate pool: the 14 `V3_FEATURE_COLUMNS` plus 22 extra v3-implemented scale-invariant features (36 total).

### 1.2 Result A — LightGBM importance rankings barely differ across symbols

One LightGBM per symbol, fed the 14 shared features, fit to the ternary triple-barrier label. Gain-importance rank-correlation between every symbol pair:

| Pair | Spearman rho of the 14-feature importance ordering |
|---|---:|
| BCH vs LDO | **+0.763** |
| BCH vs TRX | **+0.837** |
| LDO vs TRX | **+0.916** |
| **Mean pairwise** | **+0.839** |

A mean rho of +0.84 means the three per-symbol models rank the 14 features in almost the same order. The top-5-for-one / bottom-half-for-another disagreement list has only **two** entries (`ret_kurt_50`, `vwap_dev_20`) and both are marginal (rank 4 vs 9-10 — neither a true top-vs-tail flip). Every symbol's top-5 is drawn from the same pool: `max_dd_window_50`, `ret_kurt_200`, `range_realized_vol_50`, `ret_skew_200`, `ema_spread_atr_20`. The weakest universal feature is `regime_momentum_signed_5d` for all three (BCH 0.035 / LDO 0.052 / TRX 0.041 share — and note it is the one /025-validated edge ingredient; importance share is not the same as marginal edge, which is why it stays in).

**Interpretation:** the model does not "want" different features per symbol. Per-symbol feature *selection* — dropping a symbol's bottom-half and keeping its top-half — would converge to nearly the same subset for all three. The headroom the user idea is reaching for is, at the multivariate level, close to zero.

### 1.3 Result B — the univariate IC orderings *look* divergent, but it is noise

Univariate Spearman IC rankings tell a louder story — mean pairwise rho +0.306 (36-feature pool) / +0.411 (14-set) — and the disagreement list is long (e.g. `ret_skew_200` is BCH's #1 IC feature but #29/#27 for LDO/TRX). Taken at face value this *supports* the user idea.

It does not survive a noise check. The IC magnitudes are tiny — for the 14-set, almost every |IC| < 0.05; the largest single IC in the whole table is `ema_spread_atr_20` at LDO, −0.0875. At |IC| ~ 0.02-0.05 the sampling standard error of a Spearman correlation is ≈ 1/√n ≈ 0.013-0.019 per symbol — *comparable to the signal itself*. A Monte-Carlo simulation (in the EDA driver) drawing a **single common true-IC vector** for all symbols and adding only per-symbol sampling noise reproduces the observed numbers:

| Pair (panel sizes) | Simulated rank-rho if the true IC ranking is IDENTICAL | Observed |
|---|---:|---:|
| BCH-TRX (n ≈ 5700, 5700) | **+0.354 ± 0.162** | +0.242 (pool) |
| BCH-LDO (n ≈ 5700, 2700) | **+0.244 ± 0.161** | +0.159 (pool) |

The observed univariate IC rank-rho is **inside the band you would see even if the three symbols had a literally identical true feature ranking**. The univariate "per-symbol divergence" is a sample-noise artifact, not evidence of genuine per-symbol structure. This is precisely the iter-v3/070 lesson (`feedback`-recorded: univariate Spearman misleads — it ranked features that turned out INERT/HARMFUL). The trustworthy signal is Result B's multivariate importance ranking, and that says **concordant**.

**TASK 1 decisive answer: the per-symbol feature ranking does NOT materially differ. Multivariate importance rho = +0.839; the univariate IC divergence is noise. The shared 14-set is already near-optimal per symbol.**

---

## 2. TASK 2 — Engaging iter-v3/039 head-on

iter-v3/039 must not be the dismissal — but the record has to be stated precisely, because the user idea and /039 are *not* the same thing.

**What /039 actually did:** per-symbol feature **ADDITION**. `V3_FEATURES_PER_SYMBOL["BCHUSDT"] = V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)` — BCH got a **15th** feature that the other symbols did not. Plus a per-symbol label change (LDO ATR multipliers). Multi-seed CONFIRMATION result: OOS Sharpe +1.47 / IS Sharpe −0.08 — OOS lifted +0.96, **IS collapsed −0.59**. NO-MERGE. The pattern (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`) was then re-confirmed at iter-v3/050 and is a CLOSED axis at the system level: *per-symbol customizations bundled at CONFIRMATION lift OOS, break IS*.

**The distinction the user idea deserves.** There are two genuinely different operations:

- **Per-symbol ADDITION** (what /039 did, and /035-/038): GROW the feature count for some symbols. Net parameters fit to that symbol's small data INCREASE. Strictly more overfitting surface.
- **Per-symbol SELECTION** (the disciplined reading of the user idea): each symbol picks a controlled-size SUBSET of a common pool. Total feature count per symbol is NOT grown — e.g. every symbol uses exactly 14, but BCH's 14 ≠ LDO's 14, both drawn from a 20-feature superset.

Per-symbol SELECTION (fixed budget, different members) is **not** literally what /039 tested. The /030 record has one near-miss — `V3_FEATURES_PER_SYMBOL["LDOUSDT"]` was once a 7-feature *reduction* — but that was a single-symbol size cut, abandoned when LDO was dropped at /031, never run as a clean fixed-budget per-symbol-selection sweep at CONFIRMATION. **So: per-symbol feature SELECTION, as distinct from ADDITION, has not been cleanly tested in v3.** The user has, fairly, identified an untested variant.

That honest concession is exactly why I ran TASK 1 rather than waving /039. And TASK 1 answers it: the reason per-symbol SELECTION is not worth a slot is **not** "/039 failed" — it is that the importance rankings are concordant (rho +0.84), so a fixed-budget per-symbol selection would pick almost the same 14 features for every symbol. The idea is untested *and* the EDA shows it has no headroom. Both facts, stated.

---

## 3. TASK 3 — The data-honest reckoning and the pooled reframe

### 3.1 Route (a) — bar-IC-driven per-symbol selection — REJECT

The data-honest fix for "selection on 9 LDO trades overfits" is to drive selection from the bar panel (2,700-5,700 rows, data-rich) with a hard per-symbol-deviation cap and an IS-aggregate-preservation gate. The construction is sound. But TASK 1 kills the *premise*: bar-panel importance rankings are concordant (rho +0.84), so bar-IC-driven per-symbol selection converges to the shared set. You would spend a cycle-4 EXPLORATION slot to re-derive `V3_FEATURE_COLUMNS`. Route (a) is methodologically clean and **empirically pointless. REJECT.**

### 3.2 Route (b) — symbol-conditional features inside the POOLED cross-sectional model — the only viable reframe

This is the strong reframe and it must be read against where v3 *actually is*. As of /088+, v3 has pivoted off the per-symbol architecture entirely: the live research line is **one pooled `LGBMRanker` cross-sectional model** (`cross_sectional.py`) trained on a 22-symbol panel of ~47k IS rows. The /087 strategic assessment closed the per-symbol paradigm precisely because per-symbol depth-3-5 trees on 3-6k rows overfit. So the user idea, ported forward, is **not** "per-symbol feature sets" (there are no per-symbol models anymore) — it is: *should the pooled model be given symbol-conditional inputs so it can effectively use different features per symbol while still training on the full 47k-row dataset?*

That construction is real and it dissolves the data-scarcity objection by design:

- **Mechanism:** add the symbol identity as a LightGBM native categorical feature, and/or add a small number of `symbol_id × feature` interaction columns, to the pooled cross-sectional panel. The model can then split differently per symbol — *effectively* a per-symbol feature response — but every split is still estimated on all 47k pooled rows. No symbol is fit on its own thin slice. This is the standard "pooled panel with entity effects + interactions" approach (cf. fixed-effects panel regression; in a GBM it is just a categorical feature plus interactions).
- **Is it novel for v3?** Yes. Every prior per-symbol attempt (/030-/039) was N *separate* models. The pooled cross-sectional model (/088-/091) so far feeds 13 cross-sectionally rank-normalized features with **no symbol identity** — by deliberate design, since the label is cross-sectional rank and market-wide moves cancel. Symbol-conditional features inside the pooled ranker have **not been tried in v3**. Genuinely new.
- **Does TASK 1's IC divergence predict it would help?** This is the honest part. TASK 1 says the multivariate importance ranking is concordant (rho +0.84) — which argues the *marginal* value of symbol-conditioning is small. But two things keep route (b) from being a flat no: (1) the /088 panel was a *different* 22-symbol universe, and TASK 1 ran on the 3-symbol BCH/LDO/TRX set — a 22-symbol cross-section has more room for genuine symbol heterogeneity than 3 symbols; (2) symbol-conditioning costs the pooled model very little — it is one categorical column on a 47k-row panel, the data-scarcity penalty that sank /039 simply does not exist here. So route (b) is a **cheap, low-risk probe with a modest expected payoff** — not a headline axis, but a legitimate small bet IF the cross-sectional line is still being iterated and a slot is cheap.

---

## 4. TASK 4 — Verdict

**The literal user idea — per-symbol feature SETS for per-symbol models — is a NO.** Two independent reasons: (i) v3 no longer *has* per-symbol models (the /088+ pivot to the pooled cross-sectional ranker); (ii) even on the legacy 3-symbol set, TASK 1 shows the multivariate feature-importance rankings are concordant (rho +0.839), so per-symbol selection has near-zero headroom and per-symbol addition is the CLOSED `feedback_v3_per_symbol_lifts_oos_breaks_is` axis. This is a numerically-grounded no, not a lazy one.

**There is ONE disciplined, data-honest reframe worth keeping on the cycle-4 candidate list — LOW priority — route (b): symbol-conditional features inside the pooled cross-sectional ranker.** It is genuinely untested in v3 and it structurally avoids the data-scarcity failure mode. Concrete sketch, should a cheap slot open:

- **Construction.** In `cross_sectional.py`, add `symbol` to the pooled `LGBMRanker` feature matrix as a native categorical (`pd.Categorical`, passed via `categorical_feature`). Optionally add 2-3 `symbol × feature` interaction columns for the highest-importance cross-sectional features only (keep the count tiny — interactions are where overfitting re-enters). Hold the cross-sectional rank-normalization of the continuous features unchanged. Single-axis: symbol-conditioning ON vs OFF, same /089 cost-aware quintile construction, same 22-symbol `XS_UNIVERSE`, same H.
- **IS evidence already in hand.** TASK 1's 3-symbol importance rho +0.84 is the prior — it says expect a *small* effect. The brief must pre-register that and not over-claim. A pre-brief EDA must extend TASK 1's per-symbol importance computation to the full 22-symbol `XS_UNIVERSE`: if the 22-symbol importance rank-rho is also > ~0.7, route (b) should be **dropped before it consumes a slot**. That is the EDA-driven kill gate.
- **Failure mode it must guard against.** The `symbol` categorical lets the pooled tree split on symbol identity and silently rebuild per-symbol sub-models inside the pool — re-importing the /087 per-symbol overfitting through the back door. Guard: a HARD pre-registered cap on the gain-importance share allocated to the `symbol` column and the interaction columns combined (e.g. ≤ 10%); if the pooled model spends more than that on symbol identity, it has stopped being a cross-sectional model and the axis is FALSIFIED. Pair it with the standard IS-aggregate-preservation gate (`feedback_v3_per_symbol_lifts_oos_breaks_is`) and the existing XS turnover ceiling.
- **Priority.** LOW. Cycle 4's stated direction is derivatives-microstructure re-architecture, and the cross-sectional line's binding constraint (/088-/091) is a thin *gross* signal, not feature attribution — symbol-conditioning does not address that. Route (b) is a fast-fail probe to run *if* the cross-sectional architecture continues and a low-cost slot is free; it is not a reason to displace the microstructure work.

**Net:** the user identified a genuinely untested variant (per-symbol SELECTION ≠ /039's ADDITION) — that concession is owed and made. But the bar-panel EDA shows the variant has no headroom on the current symbols, and the only forward-compatible version (route b, pooled symbol-conditioning) is a low-priority, EDA-gated probe, not a headline cycle-4 axis. The honest answer to "why not custom features per symbol?" is: *the model, given the choice, ranks the features almost identically for every symbol — so it already, in effect, declined the offer.*

---

## Appendix — EDA reproducibility

- Script: `analysis/iteration_v3-092/per_symbol_feature_eda.py` (scratch; untracked).
- Inputs: `data/features_v3/{BCHUSDT,LDOUSDT,TRXUSDT}_8h_features.parquet`, read-only.
- IS filter: `open_time < 1742774400000`. No OOS data touched.
- Labels: 3-bar forward return; ternary triple-barrier (ATR 2.0/1.0, 21-bar timeout, ATR `.shift(1)` past-only).
- LightGBM: `n_estimators=300, num_leaves=15, lr=0.05, multiclass`, `random_state=42`.
- Noise-floor: Monte-Carlo (300 trials) drawing one common true-IC vector + per-symbol sampling noise; reproduces observed IC rank-rho — confirming the univariate IC divergence is a sampling artifact.
