# iter-v1/039 — EDA Findings: Per-cohort Sortino × Specialist Hybrid

**Run date**: 2026-05-31
**Axis**: Apply /037's Sortino Optuna objective to /036's LINK+DOT 2-cohort trend-scanning specialist substrate. REPEAT-COMBO of loss-function × per-cohort-specialization.
**Data source**:
- `reports-v1/iteration_v1-036/{in_sample,out_of_sample}/trades.csv` (281 IS / 105 OOS; LINK+DOT trend-scan specialist; Sharpe Optuna)
- `reports-v1/iteration_v1-037/{in_sample,out_of_sample}/trades.csv` (688 IS / 243 OOS; 5-cohort; Sortino Optuna)
- `BASELINE_V1.md` IS +0.2829 / OOS +0.6637

**Script**: `analysis/iteration_v1-039/eda.py`
**CSV outputs**: `analysis/iteration_v1-039/{jaccard_overlap,per_symbol_sortino_sharpe,delta_037_link_dot_only,prediction_signals,prediction_band,summary}.csv|json`

**NOTE**: this directory previously held a REJECTED axis EDA (drawdown-brake binary kill). That EDA has been moved to `analysis/iteration_v1-039/rejected_drawdown_brake/`; the rejection rationale lives in `briefs-v1/iteration_v1-039/axis_rejected.md`. The /039 axis pivoted to Per-cohort Sortino × specialist hybrid per the axis_rejected.md "Path Forward — option 1".

---

## Load-bearing purpose

Resolves /044 CONFIRMATION stacking decision. Per /037 closeout's 3-way convergent finding (LM Master + Critic + QR):

- /037 (Sortino on 5-cohort universe): DOT-concentrated +39.30pp OOS lift but **HURT LINK by −42.9pp** (LINK OOS −8.64% vs baseline's +34.23%).
- /036 (LINK+DOT trend-scan specialist with Sharpe Optuna): **OOS Sharpe +1.7465**, LINK +108.9% / DOT +113.6%, bit-identical +75/+112pp LINK+DOT OOS lift.

**Question /039 resolves**: does Sortino's mechanism survive on /036's substrate?
- If YES → universe-independent → /044 CAN BUNDLE both axes.
- If NO  → universe-dependent → /044 STAYS SEPARATE (Sortino is contingent on which cohorts co-train).

---

## 1. Trade-roster overlap on LINK+DOT (Jaccard)

`analysis/iteration_v1-039/jaccard_overlap.csv`

| Sample | Cohort | n(036) | n(037) | ∩ | ∪ | **Jaccard** |
|---|---|---|---|---|---|---|
| IS  | LINK     | 155 | 160 | 54 | 261 | **0.2069** |
| IS  | DOT      | 126 | 127 | 31 | 222 | **0.1396** |
| IS  | LINK+DOT | 281 | 287 | 85 | 483 | **0.1760** |
| OOS | LINK     |  52 |  48 |  6 |  94 | **0.0638** |
| OOS | DOT      |  53 |  53 | 19 |  87 | **0.2184** |
| OOS | **LINK+DOT** | **105** | **101** | **25** | **181** | **0.1381** |

**Finding**: Jaccard 0.14 OOS LINK+DOT is **deeply LOW** (< 0.30 threshold). The two iterations pick **substantially different trades** on the same nominal cohorts.

Mechanism: /036 trains on trend-scanning labels (4σ adaptive bar threshold, 21-day max horizon, gap-purge mandatory); /037 trains on standard triple-barrier labels with the Sortino objective. The combined effect of (label change × Optuna objective change) produces near-disjoint trade rosters. **The two axes are NOT picking the same edge** — they're picking different opportunities in the same cohort.

Implication for /039: stacking will land Optuna in a basin that competes with /036's specialist policy. **Basin competition is NOT orthogonality.**

---

## 2. Per-symbol Sortino vs Sharpe on /036 substrate

`analysis/iteration_v1-039/per_symbol_sortino_sharpe.csv`

| Sample | Symbol | n | mean% | trade-Sharpe | trade-Sortino | **Sortino/Sharpe** | skew | exc-kurt |
|---|---|---|---|---|---|---|---|---|
| IS  | DOT  | 126 | -0.150 | -0.075 | -0.077 | **1.029** | -0.722 | +7.05 |
| IS  | LINK | 155 | +0.184 | +0.038 | +0.054 | **1.402** | +1.342 | +3.51 |
| OOS | DOT  |  53 | +0.213 | +0.126 | +0.146 | **1.158** | +0.288 | -0.94 |
| OOS | LINK |  52 | +0.776 | +0.226 | +0.278 | **1.229** | +0.318 | +0.88 |

**Finding**: Sortino/Sharpe ratios on /036 substrate average **1.22 IS, 1.19 OOS** — **MODERATE differentiation, well below the 1.5+ "strong" threshold**.

Compared to /037's diagnostic (Sharpe & Sortino baseline IS, where ratios were 3.0-4.0× pre-Sortino-Optuna run), **/036's substrate already exhibits much lower Sortino/Sharpe spread**. The trend-scanning labels + 2-cohort universe produced symmetric-tail PnL distributions (LINK IS skew +1.34 is right-skewed, but the OOS shapes are nearly Gaussian: skew 0.29-0.32, exc-kurt -0.94 to +0.88).

**Mechanism**: trend-scanning labels already select clean trend persistences → tails are less left-heavy than triple-barrier → Sortino's downside-only deviation is **already approximated by Sharpe**. The Sortino objective has less room to reorganize the loss surface than it did on baseline.

Implication: /037-mechanism magnitude on /036 substrate is **predicted small in absolute terms** even if directionally favorable.

---

## 3. /037 LINK+DOT-subset OOS performance vs /036 specialist

`analysis/iteration_v1-039/delta_037_link_dot_only.csv`

Strip /037's 5-cohort output to LINK+DOT trades only and compare to /036's full 2-cohort output:

| Sample | Iter | n | net_PnL% | trade-Sharpe | trade-Sortino | mean% | WR |
|---|---|---|---|---|---|---|---|
| OOS | /036 LINK+DOT specialist | 105 | **+51.62** | **+0.182** | **+0.223** | +0.492 | **0.543** |
| OOS | /037 LINK+DOT subset of 5-cohort | 101 | +13.07 | +0.038 | +0.049 | +0.129 | 0.436 |
| OOS | **delta(037 − 036)** | **−4** | **−38.55** | **−0.144** | **−0.175** | **−0.362** | **−0.107** |

**Killer finding**: when /037 was applied to the 5-cohort universe, its LINK+DOT-subset OOS output was **already −38.55pp below /036**, with trade-Sharpe −0.144 lower. This is BEFORE we even consider whether restricting to LINK+DOT helps recover.

The trend-scanning label substrate produced the OOS gain in /036, not the Sortino objective. Replacing trend-scanning labels with standard labels (which is what /037 used) destroyed the LINK+DOT signal. **Sortino did NOT compensate.**

The /039 hypothesis is: combine BOTH — use /036's labels AND /037's objective. **But the EDA shows /037's mechanism collides with /036's basin (Jaccard 0.14), and the Sortino/Sharpe ratio is small on /036's substrate (1.22 avg).** The probability that Sortino's basin draw on a 2-cohort × trend-scan substrate lands on a STRICTLY BETTER policy than /036's existing optimum is structurally low.

---

## 4. Predicted F1 modal OOS Sharpe Δ band

`analysis/iteration_v1-039/prediction_band.csv`

Integration of three signals (Jaccard + Sortino/Sharpe ratio + /037 LINK+DOT-subset OOS delta):

| Band | Weight | Notes |
|---|---|---|
| PROMISING-CLEAN ≥+0.20 | **0%** | Ruled out — Jaccard LOW + /037 LINK+DOT-subset already underperformed /036. |
| PROMISING-INERT-FAV [0, +0.20) | 17% | Possible if Sortino's basin happens to land near /036's optimum AND trend-scanning labels still dominate. |
| INERT [-0.20, 0) | 23% | Likely if mechanisms cancel — /037 contribution swamped by /036's already-large gain. |
| **NEG-CLEAN [-0.45, -0.20)** | **40%** | **MODAL** — basin migration competes; /037 mechanism collides with /036's specialist policy. |
| NEG-CAT < -0.45 | 20% | Catastrophic interference if Sortino's basin draw is far from /036's, similar to /037's LINK regression in 5-cohort. |

**Modal band**: **NEG-CLEAN [-0.45, -0.20)** at 40% weight.

**Combined NEG mass**: 60% (40% NEG-CLEAN + 20% NEG-CAT).
**Combined POS mass**: 17%.
**Neutral mass**: 23%.

---

## 5. Will Sortino survive on /036's substrate?

**Cleanest answer (1 sentence)**: **NO — Sortino is universe-dependent**: /036's substrate already exhibits a moderate Sortino/Sharpe ratio (1.22 IS) and near-Gaussian OOS PnL distributions (skew 0.3, kurt < 1), giving the Sortino objective little to reorganize, while the Jaccard 0.14 OOS overlap between /036 and /037 confirms that the Sortino objective reroutes Optuna into a basin that **competes** with /036's already-optimal specialist policy rather than reinforcing it.

**Recommended verdict for the brief**: declare HIGH-RISK (REPEAT-COMBO axis with predicted-NEG modal), run anyway under PRIME DIRECTIVE (the experiment resolves the /044 stacking decision regardless of outcome), and pre-commit /044 to **SEPARATE** baseline-stacking rather than BUNDLE if the EDA prior holds.

---

## 6. Falsifier conditions for the brief Section 7

- **PROMISING-CLEAN trigger**: OOS bundle Sharpe Δ ≥ +0.20 AND LINK OOS Δ ≥ 0 AND DOT OOS Δ ≥ 0. Probability per band weights: **3%** (folded into PROMISING-INERT-FAV tail).
- **PROMISING-INERT-FAV trigger**: OOS bundle Sharpe Δ ∈ [0, +0.20).  Probability: **17%**.
- **INERT trigger**: OOS bundle Sharpe Δ ∈ [-0.20, 0). Probability: **23%**.
- **NEG-CLEAN trigger**: OOS bundle Sharpe Δ ∈ [-0.45, -0.20). Probability: **40%** (modal).
- **NEG-CAT trigger**: OOS bundle Sharpe Δ < -0.45. Probability: **20%**.

**/044 stacking decision pre-commit**: if Sharpe Δ < +0.05 → /044 STAYS SEPARATE.

---

## 7. Wall-clock & implementation cost

NO NEW SRC/ CODE per AXIS specification. All three mechanisms exist:
- `--symbols LINKUSDT DOTUSDT` (`run_baseline_v1.py` already accepts)
- `--label-mode trend_scanning` (added at /035)
- `--optuna-objective sortino` (added at /037)

Only need: `run_baseline_v1.py` dispatch elif (model selection for LINK+DOT-only path) + catch-all-cohort exclusion + 1 integration test.

**Wall-clock target**: ~50 min modal at v1 EXPLORATION standard (n_trials=18, ENSEMBLE_SIZE=3, single outer seed=42). Cost-positive even at predicted-NEG: resolves /044 stacking decision in one cheap experiment.
