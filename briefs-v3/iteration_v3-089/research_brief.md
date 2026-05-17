# iter-v3/089 — Research Brief — the CORRECTED cross-sectional iteration: sign fix + CPCV-proxy fix + cost-aware construction (cycle-3 EXPLORATION #8)

**Iteration**: iter-v3/089
**Type**: EXPLORATION (cycle-3 slot #8 of 10) — the CORRECTED next build on the RETAINED /088 cross-sectional architecture. NOT a fresh re-architecture.
**Branch**: `iteration-v3/089` (off the /088 closeout merge `5b9c8b1`)
**Date**: 2026-05-17
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **IMMUTABLE** (`src/crypto_trade/config.py`, `OOS_CUTOFF_MS = 1742774400000`).
- `training_months = 24` — **IMMUTABLE**.
- IS = every bar with `open_time < OOS_CUTOFF_MS`. OOS = every bar at/after it.
- The QR sees OOS for the FIRST time in Phase 7. Every design parameter in this brief — the sign mapping, the quantile cutoff, the holding period, the no-trade band, the turnover ceiling, the feature set — is selected on **IS data only** (the committed `analysis/iteration_v3-089/*.py` EDAs) or set **a-priori from cited research**. This is scrutinised in Section 10.3.

## Section 0.5 — Iteration Type Declaration

iter-v3/089 is a **CORRECTED-BUILD EXPLORATION** — cycle-3 slot #8 of 10, EXPLORATION mode (single-seed seed=42, `--n-trials 35`). Its axis is **not** a fresh re-architecture and **not** an incremental knob on the /059 per-symbol baseline. It is the corrected next build on the **RETAINED** /088 cross-sectional `LGBMRanker` architecture — the architecture the /088 closeout classified ARCHITECTURE-PARTIAL and recorded as **the active v3 research line** (diary-v3/iteration_v3-088.md Section 7: *"the cross-sectional architecture is RETAINED as a LIVE v3 research direction ... /089 is the corrected next build on it"*).

Per `feedback_v3_bold_research_mandate.md` (SHARPENED 2026-05-17): the cross-sectional architecture produced v3's FIRST genuine OOS signal transfer in ~27 EXPLORATIONs (OOS rank-IC +0.0430, t ≈ 4.6); /089's job is to convert that signal into a profitable book. This brief carries the two **mandatory corrections** (Critic /088 Recs #2 and #3 — bug/methodology fixes) and the **genuine /089 axis** — making the corrected architecture profitable by attacking the dominant turnover-drag failure mode structurally.

This brief **supersedes the cycle-3 incremental plan** (`briefs-v3/cycle3_plan.md`) for slots #8–#10, exactly as /088's brief did for #7: the cross-sectional architecture is the active line and /089–/091 iterate it.

---

## Section 1 — Hypothesis

### 1.1 — What /088 established, and what it leaves for /089

iter-v3/088 replaced the per-symbol absolute-barrier architecture with a pooled `LGBMRanker(lambdarank)` on a 22-symbol cross-section, traded as a dollar-neutral long-short book. The result (diary-v3/iteration_v3-088.md):

- **The cross-sectional MODEL works.** OOS rank-IC **+0.0430 ± 0.3317, n = 1255 OOS timestamps, t ≈ +4.59** — a statistically-significant POSITIVE out-of-sample signal transfer. The first time in three v3 cycles a new EXPLORATION axis produced a genuine OOS signal rather than an IS-overfit inversion.
- **The BOOK lost money** — IS monthly Sharpe −0.6403, OOS monthly Sharpe −0.5418 — for two diagnosed, fixable reasons (QE + Critic, concurring):
  1. **Sign inversion.** The /088 brief Section 3.4 specified LONGing the model's predicted *losers*. The brief mis-reasoned — it conflated the EDA's *past*-return reversal predictor with what an `LGBMRanker` trained on a *forward*-return-grade label learns. The model is trained on the forward grade, so high score = predicted future WINNER (the /088 pooled IS `Spearman(predicted_score, label_grade) = +0.0328`, p = 1.2e-12). The book longed the predicted losers.
  2. **Turnover drag — the dominant failure mode.** IS total fees 0.687 were **8.8× the IS gross PnL magnitude (0.078)**. The every-8h-bar rebalance of a tercile (~⅓-of-book turnover/bar) at 0.1%/side is incompatible with a +0.043-rank-IC signal. The /088 flipped-IS diagnostic settled this: sign-flipping the positions takes IS *gross* Sharpe to only ≈ +0.067 and IS *net* Sharpe to still −0.43 — the fee drag overwhelms even the correctly-oriented gross signal.

### 1.2 — The /089 hypothesis

> **The /088 architecture's cross-sectional model genuinely transfers OOS (rank-IC +0.043, t ≈ 4.6). The book lost money for two diagnosed reasons — a sign inversion and turnover drag. Correcting the sign and attacking turnover STRUCTURALLY — a tighter (quintile) quantile, overlapping multi-bar holds, and a no-trade band — will materially reduce the net loss and is the necessary path toward a profitable cross-sectional book. The committed IS-only EDA confirms each lever's direction and magnitude, AND honestly bounds what they can achieve: the corrected + cost-aware construction roughly HALVES the IS net loss, but does not by itself reach a positive IS net Sharpe — because the gross long-short spread is structurally thin (corrected-sign IS gross monthly Sharpe ≈ +0.05). /089 carries every IS-validated construction lever and pre-registers a hard turnover ceiling; the gross-signal feature expansion is scoped, IS-quantified, and deferred to /090 as its own dedicated EXPLORATION.**

This is the honest hypothesis the EDA supports. /089 is a genuine, well-researched attack on the dominant failure mode — not a minimal patch — and it is honest about the residual: the construction fixes are necessary and individually correct, the gross signal needs its own iteration, and /089 pre-registers exactly what would falsify the cost-aware-construction claim.

### 1.3 — Why this is not defeatism

The bold-research mandate (SHARPENED) forbids defeatism — and it equally forbids dishonesty. /089 does NOT conclude "the cross-sectional line is exhausted." It does the opposite: it executes every construction lever the cost-aware-portfolio literature supports, validates each on IS data, pre-registers a hard turnover gate, and lays out /090's gross-signal expansion as the next concrete axis with its own IS evidence. The cross-sectional architecture is the most promising structural result v3 has produced; /089 advances it on the construction axis and hands /090 a quantified gross-signal axis. That is relentless iteration, not a stopping point.

---

## Section 2 — IS-Only Numerical Evidence

Two committed EDA scripts, both IS-only (`open_time < OOS_CUTOFF_MS`), both run on the RETAINED `cross_sectional.py` infrastructure:

- `analysis/iteration_v3-089/turnover_construction_eda.py` — a TRUE IS-internal walk-forward of the `LGBMRanker` (trains the ranker on IS months, predicts the next IS month — NO OOS row read), measuring the corrected-sign net IS monthly Sharpe under each turnover-reduction lever. CSVs E1–E6.
- `analysis/iteration_v3-089/gross_signal_eda.py` — a model-free cross-sectional-predictor EDA quantifying the gross-spread levers (horizon, quantile, weighting, normalisation, feature expansion). CSVs G1–G4.

### 2.1 — E1: the sign fix restores a positive gross signal

`E1_baseline_replication.csv` — corrected-sign tercile, every-bar rebalance, the IS-internal walk-forward (37 monthly models, mean IS *train* rank-IC +0.21):

| Variant | IS gross monthly Sharpe | IS net monthly Sharpe | IS fee/\|gross\| | turnover/bar |
|---|---:|---:|---:|---:|
| E1 — corrected-sign tercile, every-bar | **+0.0485** | −0.6548 | 18.5× | 0.3252 |

The corrected sign produces a **positive IS gross monthly Sharpe (+0.049)** — confirming the /088 flipped-IS diagnostic (+0.067 gross) directionally on a full IS-internal walk-forward. The sign fix is necessary and verified. It is **not sufficient**: the net Sharpe is still −0.65 because IS fees are 18.5× the gross PnL on the every-bar tercile.

### 2.2 — E2: quantile concentration steepens the gross spread

`E2_quantile_concentration.csv` — tercile vs quartile vs quintile, every-bar:

| Quantile | per-leg frac | IS gross monthly Sharpe | IS net monthly Sharpe | IS fee/\|gross\| |
|---|---:|---:|---:|---:|
| tercile | 0.333 | +0.0485 | −0.6548 | 18.5× |
| quartile | 0.250 | **+0.0972** | −0.5912 | 8.6× |
| quintile | 0.200 | +0.0765 | −0.5744 | 10.0× |

Concentrating the legs lifts the gross signal — quartile +0.097 and quintile +0.077 both beat tercile +0.049. This is the Poh/Lim/Zohren effect (arXiv 2012.07149): an LTR model places assets in the correct quantile with greater precision, so a tighter quantile steepens the long-short spread. A tighter quantile also concentrates the gross PnL relative to the fee base — quintile net Sharpe −0.574 is the best of the three.

### 2.3 — E3: overlapping multi-bar holds cut turnover ~3–4× and lift net Sharpe

`E3_overlapping_holds.csv` — quintile, holding period in {1, 3, 6} bars (Jegadeesh-Titman 1993 overlapping-portfolio construction — at hold H, a new tranche sized 1/H is formed each bar and held H bars):

| Hold (bars) | IS gross monthly Sharpe | IS net monthly Sharpe | IS fee/\|gross\| | turnover/bar |
|---:|---:|---:|---:|---:|
| 1 | +0.0765 | −0.5744 | 10.0× | 0.3334 |
| **3** | −0.0743 | **−0.4154** | 5.4× | **0.1496** |
| 6 | −0.0805 | −0.3200 | 3.3× | 0.0882 |

The overlapping hold cuts turnover proportionally — hold=3 to 0.150/bar (a 2.2× cut vs hold=1), hold=6 to 0.088/bar (3.8×). Net IS Sharpe improves monotonically (−0.574 → −0.415 → −0.320). **Note honestly:** the IS-internal-walk-forward gross Sharpe goes slightly negative at hold ≥ 3 (the 3-bar tranche averaging slightly weakens the gross signal on this IS window — Jegadeesh-Titman find no significant return difference for equities, but the crypto short-horizon signal is faster). /089 selects **hold=3** — horizon-matched (the label predicts the 3-bar-forward cross-section), the largest net-Sharpe lift per unit of gross-signal sacrifice, and the J-T convention.

### 2.4 — E4: the no-trade band — the turnover/cost tradeoff curve

`E4_no_trade_band_scan.csv` — quintile, hold=3, no-trade band τ scanned (a symbol is re-traded only when its target book weight moves > τ vs the held weight):

| τ (no-trade band) | IS gross monthly Sharpe | IS net monthly Sharpe | turnover/bar | IS fee/\|gross\| |
|---:|---:|---:|---:|---:|
| 0.0000 | −0.0743 | −0.4154 | 0.1496 | 5.4× |
| 0.0050 | −0.0760 | −0.4085 | 0.1454 | 5.1× |
| 0.0100 | −0.0490 | −0.3630 | 0.1391 | 7.5× |
| 0.0150 | −0.0807 | −0.3765 | 0.1306 | 4.4× |
| **0.0200** | −0.0229 | **−0.3147** | **0.1199** | 15.0× |

The no-trade band monotonically reduces turnover (0.150 → 0.120 across the grid) and the IS net Sharpe is best at **τ = 0.020 (−0.315)** — the IS-best of the entire 17-variant grid. This is the Constantinides (1986) / Davis-Norman (1990) result: with a proportional cost, the optimal policy is a no-trade region; the optimal band width scales O(ε^1/3) in the cost ε and utility loss is O(ε^2/3), so when costs dominate (the /088 case) a non-trivial band is mandatory. /089 selects **τ = 0.020** — the IS-best.

### 2.5 — E5/E6: the combined /089 construction and the pre-registered turnover ceiling

`E5_combined_candidate.csv` — corrected sign + quintile + hold=3 + τ=0.020:

| Metric | E1 baseline | **E5 /089 candidate** |
|---|---:|---:|
| IS net monthly Sharpe | −0.6548 | **−0.3147** |
| IS gross monthly Sharpe | +0.0485 | −0.0229 |
| turnover/bar | 0.3252 | **0.1199** |
| IS fee/\|gross\| | 18.5× | 15.0× |
| max IS symbol concentration | 12.0% | 16.9% |

The combined /089 construction **halves the IS net loss** (−0.65 → −0.31) and **cuts turnover 2.7×** (0.325 → 0.120/bar). `E6_turnover_ceiling.csv` derives the **pre-registered hard turnover ceiling**: the IS-best construction runs at 0.120 gross turnover/bar; the ceiling is set at ×1.15 headroom = **0.138 gross turnover/bar**. A /089 build whose realised IS mean gross turnover/bar exceeds 0.138 is NO-MERGE (Section 4).

### 2.6 — G1–G4: the gross-signal levers — the honest read

`gross_signal_eda.py` (model-free, IS-only) quantifies whether the gross signal itself can be strengthened:

**G1 — `G1_horizon_quantile_spread.csv`** — the realised top-vs-bottom-quantile L-S spread Sharpe across forward horizon {3,6,9,12} × quantile {tercile, quartile, quintile, decile}, normalised per-bar-equivalent (÷√H for cross-H comparability):

| | tercile | quartile | quintile | decile |
|---|---:|---:|---:|---:|
| **per-bar-eq spread Sharpe, mean over H** | −0.040 | −0.041 | **−0.045** | −0.032 |

The realised spread Sharpe is **structurally flat across all (H, quantile)** — per-bar-equivalent magnitude only 0.030–0.046. A longer horizon does NOT lift the per-bar economic edge (the raw spread grows with H but so does its std). **Quintile is marginally the strongest quantile** (−0.045); **decile is WEAKER** (−0.032) — at N=22, a decile is ~2 names/leg, too thin and noisy. This is decisive evidence that **quintile is the quantile sweet spot** — confirming the E2/E3 choice and ruling out decile.

**G2 — `G2_score_weighting.csv`** — conviction-weighting (weight each name by rank-distance from the universe median) vs equal-weighting, quintile: equal −0.078 vs conviction −0.074. Conviction-weighting does **NOT** help. Equal-weight is retained; conviction-weighting is dropped.

**G3 — `G3_normalization.csv`** — cross-sectional rank vs z-score feature normalisation of the 13-feature composite: rank IC-IR 0.198 vs z-score 0.191. The /088 cross-sectional **rank** transform is correct; keep it.

**G4 — `G4_feature_set_headroom.csv` / `G4_xs_channel_ic.csv`** — the 13-feature composite IC-IR vs the same + 5 cross-sectional momentum/reversal channels (multi-lookback `close`-ratio channels the per-symbol architecture never carried as separate cross-sectional predictors): composite IC-IR 0.200 → 0.204 (+2%). The expansion gives a **real but marginal** lift; the per-channel ICs are all −0.03 to −0.04 (the same magnitude as the existing predictors).

### 2.7 — Summary of IS evidence — and the honest scoping call

1. The sign fix restores a positive IS gross monthly Sharpe (+0.049, E1).
2. Quantile concentration steepens the gross spread; **quintile is the sweet spot** (E2, G1) — decile is too thin at N=22.
3. Overlapping 3-bar holds cut turnover 2.2× and lift net Sharpe (E3).
4. A no-trade band τ=0.020 is the IS-best of the 17-variant grid (E4).
5. The combined /089 construction halves the IS net loss (−0.65 → −0.31) and cuts turnover 2.7× (E5).
6. **The honest residual**: no construction lever reaches a positive IS net Sharpe — because the realised gross L-S spread Sharpe is structurally ≈ −0.04 per bar (G1) and neither horizon, conviction-weighting, nor a marginal feature expansion lifts it materially (G2–G4).
7. **The scoping call**: /089 carries the corrections + the full IS-validated cost-aware construction. The gross-signal feature expansion (G4: +2% IC-IR, real but marginal) is **deferred to /090** as its own dedicated EXPLORATION — a feature expansion done properly needs its own axis (and per `feedback_v3_inert_features_at_higher_budget.md` / the iter-v3/070 dead path, stacking a marginally-correlated feature set onto another axis is a known failure mode).

---

## Section 3 — Proposed Changes (the /089 build spec — the QE Phase-6 build)

### 3.1 — Correction #1: the SIGN FIX (Critic /088 Rec #2) — from first principles

**First principles.** `label_cross_sectional_rank` assigns each (symbol, timestamp) row a grade in {0,1,2} by the **FORWARD-return** tercile rank within the cross-section: grade 2 = the top-third of the next-H-bar returns (future cross-section out-performers), grade 0 = the bottom-third (future under-performers). `LGBMRanker(objective="lambdarank")` is trained on this grade — `lambdarank` optimises a ranking metric so the model learns to assign **high score to high grade**, i.e. the **FORWARD mapping**: high predicted score → high future return → predicted future WINNER. There is no reversal for the model to invert — it is not trained on past returns; it is trained on the forward grade. The /088 brief's "reversal ... long the bottom tercile" reasoning was a non-sequitur (it imported the EDA's past-return-reversal predictor into a statement about a forward-grade-trained model). The /088 IS `Spearman(predicted_score, label_grade) = +0.0328`, p = 1.2e-12 confirms the forward mapping empirically.

**The corrected mapping**: at each timestamp `build_positions` **LONGs the TOP quantile (highest predicted scores = predicted future winners)** and **SHORTs the BOTTOM quantile (lowest predicted scores = predicted future losers)**.

**Code surfaces corrected** (`src/crypto_trade/strategies/ml/cross_sectional.py`):
- `build_positions` (lines ~599-606): `long_syms = sorted_syms[-n_leg:]` (top quantile, high score) and `short_syms = sorted_syms[:n_leg]` (bottom quantile, low score) — the inverse of /088's `sorted_syms[:n_leg]`-long.
- The `predict_ranking` docstring (lines ~511-525) — the wrong "reversal → SHORT high-score" text — is corrected to state the forward mapping from first principles.
- The `label_cross_sectional_rank` docstring grade-comment is corrected (it described grade-0 as the "predicted WINNERS given the reversal signal" — wrong).

### 3.2 — Correction #2: the CPCV-PROXY FIX (Critic /088 Rec #3)

The /088 `_compute_xs_cpcv` (`run_cross_sectional_v3.py`) computed each CPCV path "Sharpe" as `mean(sub_labels[long_idx]) − mean(sub_labels[short_idx])` — a **label-grade self-correlation**: grade-0 < grade-2 by construction of the tercile label, so it measures nothing about the model. `cpcv_paths.csv` collapsed to 45 rows of literally `sharpe = 0.0`, and the F4 `frac_positive_paths` gate carried no information at /088.

**The fix**: `_compute_xs_cpcv` now computes the **ACTUAL realised long-short NET return** of the trained model on each CPCV path's test fold. It does not re-fit the model per path — it reads the per-(timestamp, symbol) `net_pnl` from the already-computed walk-forward backtest `results` (which carries the trained, **corrected-sign** positions, gross PnL, turnover fee and net PnL), sums `net_pnl` into one book return per IS timestamp, and computes the Sharpe of each CPCV path's test-fold book-return series. This is the real model-driven long-short net P&L on the path — the informative F4 gate the Critic asked for. The `XS_REQUIRED_GAP = 88` `expected_gap` assertion is retained on the `combinatorial_purged_cv` call.

### 3.3 — The /089 axis: the cost-aware construction (the genuine research)

All three levers are IS-selected (Section 2) or a-priori from cited research. New constants in `cross_sectional.py`:

- **`XS_QUANTILE_FRAC = 0.20` — QUINTILE legs.** EDA E2 + G1: quintile maximises the realised per-bar spread Sharpe across the 22-symbol universe; decile (10%) is thinner and weaker (~2 names/leg at N=22 is too noisy); tercile dilutes the LTR precision. Poh/Lim/Zohren: an LTR model places assets in the right quantile with greater precision, so a tighter quantile steepens the spread — but not so tight the leg loses diversification. Quintile = ~4–5 names/leg.
- **`XS_HOLD_BARS = 3` — OVERLAPPING multi-bar holds.** At each bar a new tranche sized 1/3 of the target book is formed and held 3 bars; the book is the sum of the live tranches (Jegadeesh-Titman 1993 overlapping-portfolio construction). H=3 is horizon-matched (= `XS_HORIZON`; the label predicts the 3-bar-forward cross-section). EDA E3: hold=3 cuts turnover 2.2× and IS fee/|gross| 10.0× → 5.4×.
- **`XS_NO_TRADE_BAND = 0.020` — NO-TRADE BAND.** A symbol is re-traded to its book weight only when that weight moved > τ vs the held weight (Constantinides 1986; Davis-Norman 1990 — optimal band O(ε^1/3) in the proportional cost). EDA E4: τ=0.020 is the IS-best net Sharpe of the scanned grid.

**`build_positions`** produces the per-bar **target** book (corrected-sign, quintile, dollar-neutral, inverse-vol, vol-targeted). **`run_cross_sectional_backtest`** then (a) forms a 1/3-sized tranche each bar and maintains the live overlapping tranches → the **raw book**; (b) applies `apply_no_trade_band` → the **book**; (c) accrues PnL and the turnover-based fee on the **book** positions bar-to-bar.

### 3.4 — The pre-registered HARD turnover ceiling

`XS_TURNOVER_CEILING = 0.138` — the gross-turnover-per-bar HARD MERGE-BLOCKING gate. Derived (EDA E6): the IS-best /089 construction runs at 0.120 gross turnover/bar; the ceiling is ×1.15 headroom = 0.138. The runner computes `compute_turnover_per_bar(results, is_oos=False)` and writes `turnover_ceiling_gate_pass` to `comparison.csv` and `dsr.json`. Per `feedback_v3_per_symbol_target_axis_falsifier.md` (falsifiers are gates, not predictions): **any /089 build whose realised IS mean gross turnover/bar exceeds 0.138 is NO-MERGE** — the same fee drag that sank /088 cannot be rationalised post-hoc.

### 3.5 — The feature set, universe, label, embargo — UNCHANGED from /088

- **Features**: the 13-feature cross-sectional stack (14-feature /059 anchor minus `btc_ret_14d`), cross-sectionally rank-normalized. G3 confirms rank-normalization beats z-score. **No feature change in /089** — the G4 cross-sectional-momentum expansion is deferred to /090 (Section 2.7).
- **Universe**: the 22-symbol `XS_UNIVERSE` — unchanged (the T1 IS screen stands).
- **Label**: `label_cross_sectional_rank`, H=3 forward tercile grade — unchanged. G1 confirms a longer horizon does not lift the per-bar spread.
- **Embargo / CPCV**: `XS_REQUIRED_GAP = 88` — unchanged; the `expected_gap` assertion is retained.
- **Model**: `LGBMRanker(lambdarank)`, monthly walk-forward, `train_end_ms = test_start_ms − embargo_ms` (the e149e9d fix) — unchanged.

### 3.6 — Phase-6 build scope

This is a focused build on the RETAINED `cross_sectional.py` — NOT a re-architecture. The QE Phase-6 build:
1. Confirm the SIGN FIX in `build_positions` + the corrected docstrings (Section 3.1) — already wired at the /089 setup commit.
2. Confirm the CPCV-PROXY FIX in `_compute_xs_cpcv` (Section 3.2) — already wired.
3. Confirm the cost-aware construction (quintile + 3-bar overlapping holds + no-trade band) in `run_cross_sectional_backtest` (Section 3.3) — already wired; `XS_QUANTILE_FRAC`/`XS_HOLD_BARS`/`XS_NO_TRADE_BAND` passed explicitly at the runner call site.
4. Confirm the turnover-ceiling gate computation + report emission (Section 3.4) — already wired.
5. Run the full walk-forward cross-sectional backtest (`uv run python run_cross_sectional_v3.py --skip-features` if the 22 parquets are fresh; EXPLORATION mode, single-seed seed=42, `--n-trials 35`); emit `comparison.csv`, per-symbol attribution, the corrected `cpcv_paths.csv`, `rank_ic.csv`, `dsr.json`.

The /089 setup commit lands the code corrections + construction + tests; the QE Phase-6 step runs the backtest and writes the engineering report.

### 3.7 — Risk framework

Unchanged from /088 — the cross-sectional book is risk-managed structurally (dollar-neutral construction, inverse-vol + vol-targeting, quantile diversification). The /089 cost-aware construction **adds** two risk-relevant structural controls: the overlapping-hold tranching (smooths position changes, reduces single-bar exposure jumps) and the no-trade band (suppresses churn on noise). The legacy v3 7-gate stack stays deferred (re-introducing gates would still confound the construction measurement; the cross-sectional risk gate re-design remains a future-iteration axis).

---

## Section 4 — Expected OOS Impact + evaluation + the pre-registered falsifiers

### 4.1 — Evaluation

iter-v3/089 produces a cross-sectional long-short book; per the /088 brief Section 4.1 it is **not directly comparable** to the per-symbol-book Sharpes of the /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322) or the /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791) — a different return distribution, beta, turnover. The operative evaluation:

**(A) The standing absolute bar.** The mission bar is top-quant-firm-grade: the standing v3 merge floors are IS monthly Sharpe ≥ +1.0 AND OOS monthly Sharpe ≥ +1.0. /089 is measured against these.

**(B) The architecture-internal diagnostics + the /089-specific construction gate:**
- **OOS rank-IC > 0** — does the corrected-sign model's OOS prediction rank correlate with the realised forward cross-sectional rank? (Comparable across IS/OOS; the /088 architecture-validity signal.)
- **OOS/IS monthly Sharpe ratio ≥ 0.5** — the researcher-overfitting check.
- **The HARD turnover ceiling — IS mean gross turnover/bar ≤ 0.138** (Section 3.4). A breach is NO-MERGE regardless of Sharpe.
- **frac_positive_paths (CPCV)** — now computed on the ACTUAL long-short net return per path (the corrected proxy, Section 3.2), so it is finally an informative gate.
- **No single symbol > 30% of OOS book PnL** — the quintile dollar-neutral construction should keep this structural.

**The /089 anchor.** The honest internal anchor for /089 is the /088 cross-sectional book itself — IS monthly Sharpe **−0.6403** / OOS monthly Sharpe **−0.5418**, turnover/bar **~0.30**. /089's claim is that the corrected sign + cost-aware construction materially improves on the /088 book on the net Sharpe and the turnover axes. The two-anchor rule is satisfied: ANCHOR 1 (the /088 cross-sectional book, the like-for-like architecture predecessor); ANCHOR 2 (the /059 CONFIRMATION baseline, IS +1.0894 / OOS +0.5791, recorded with the comparability caveat — a per-symbol-book reference, not a like-for-like delta).

### 4.2 — Predicted OOS impact (honest)

The EDA IS-internal walk-forward is the basis for the prediction. The /089 construction halves the IS net loss (E1 −0.65 → E5 −0.31). Honest prediction for the OOS run:

- **OOS rank-IC stays positive** — the sign fix does not touch the model, and the /088 OOS rank-IC was +0.043 at t ≈ 4.6; the corrected book reads the SAME model's scores with the correct sign. Predicted OOS rank-IC ≈ +0.03 to +0.05.
- **OOS monthly Sharpe materially improves on the /088 book's −0.5418, but most likely remains sub-floor** — the EDA says the cost-aware construction roughly halves the IS net loss; applying the same proportional improvement to the /088 OOS book's −0.54 predicts an OOS monthly Sharpe in roughly **[−0.30, +0.10]** — a large improvement, very likely still below the +1.0 floor, plausibly still slightly negative. **This is the honest modal prediction.** A positive OOS monthly Sharpe is achievable but not the modal outcome; clearing the +1.0 floor on this iteration is not expected — the gross signal needs /090's expansion first.
- **IS mean gross turnover/bar ≈ 0.12** — within the 0.138 ceiling (the EDA E5 figure).

### 4.3 — The LOCKED falsifier band (pre-registered — gates, not predictions)

Per `feedback_v3_per_symbol_target_axis_falsifier.md` — falsifiers are gates. Evaluated in Phase 7:

- **F1 — OOS rank-IC ≤ 0**: the corrected-sign model's OOS prediction rank does NOT correlate with the realised forward cross-sectional rank. Since /089 reuses the /088 model unchanged and /088 had OOS rank-IC +0.043 (t ≈ 4.6), an OOS rank-IC ≤ 0 at /089 would indicate a build defect (e.g. the sign fix mis-wired the score→position map, or a panel/feature regression) — a hard investigate-and-block signal.
- **F2 — IS mean gross turnover/bar > 0.138** (`XS_TURNOVER_CEILING`): the pre-registered HARD turnover gate. A breach means the cost-aware construction did not actually contain turnover → NO-MERGE regardless of any other metric. **This is the /089-defining falsifier** — it makes the "attack turnover" claim a gate, not a footnote.
- **F3 — OOS monthly Sharpe ≤ the /088 cross-sectional book's −0.5418**: the corrected + cost-aware construction did NOT improve the OOS book at all vs the /088 predecessor → the construction levers did not transfer OOS → the cost-aware-construction hypothesis is falsified.
- **F4 — OOS/IS monthly Sharpe ratio < 0.5** (evaluated only when both are positive; if both are negative, F4 is N/A and F3 governs): if /089 reaches a positive IS Sharpe, the OOS must generalise.
- **F5 — a single symbol > 50% of OOS book PnL**: the quintile dollar-neutral construction failed to diversify (a structural-construction failure distinct from a signal failure).

### 4.4 — What each falsifier implies

- **If F2 fires** — NO-MERGE, unconditionally. The turnover ceiling is the hard gate; a breach means /089's central construction claim failed and the build must be diagnosed before any cross-sectional iteration continues.
- **If F1 fires** — a build defect (the model itself transferred OOS at /088); investigate the sign-fix wiring / the panel before any classification.
- **If F3 fires (and F1/F2 do not)** — the construction levers did not improve the OOS book; the cost-aware-construction hypothesis is falsified for this cycle; /090 must rethink the construction, not just expand features.
- **If no falsifier fires** — /089 improved the OOS book, contained turnover, and the signal transferred; /089 is a genuine, methodologically-clean advance on the cross-sectional construction axis (the Phase-8 classification is the QR's call — Section 8).

---

## Section 5 — Risk Mitigation

Per `feedback_v3_risk_mitigation_design.md`, every merge-candidate iteration carries a Risk Mitigation section. /089's controls are structural — intrinsic to the cost-aware cross-sectional construction:

| Risk | Mitigation | IS-calibrated / a-priori | Simulated historical effect |
|---|---|---|---|
| **Turnover / fee drag** (the /088 failure mode) | Overlapping 3-bar holds + no-trade band τ=0.020 + the HARD turnover ceiling 0.138 | IS-selected (EDA E3/E4/E6) | IS-internal walk-forward: turnover/bar 0.325 → 0.120 (2.7× cut); IS fee/\|gross\| 18.5× → 15.0×; IS net Sharpe −0.65 → −0.31 |
| Directional market drawdown | Dollar-neutral long-short construction | a-priori (construction) | /088: market beta removed by design |
| Single-symbol concentration | Quintile long-short — ~4–5 names/leg, no symbol > 1/(quintile size) of a leg | a-priori (construction) | EDA E5: max IS symbol concentration 16.9% — structurally < 30% |
| High-vol-symbol domination | Inverse-vol weighting within each leg + portfolio vol-targeting | a-priori (standard cross-sectional construction) | /088: per-symbol concentration capped |
| Position-change shock | Overlapping-hold tranching smooths the per-bar position change (max 1/3 of the book turns per bar by construction) | a-priori (Jegadeesh-Titman) | EDA E3: turnover/bar capped at 0.150 by the hold mechanism |
| Listing non-stationarity | 60-day (180-bar) listing burn-in per symbol | a-priori (crypto pitfall) | /088: applied; signal measured with it active |
| Label look-ahead | `XS_REQUIRED_GAP = 88` pooled-CPCV purge; walk-forward `train_end = test_start − embargo` | a-priori (formula) | /088 Critic Check 1/2 PASS; unchanged |

The turnover controls are the /089-specific risk addition and their effect is simulated in the committed IS-internal-walk-forward EDA (E1→E5).

## Section 6 — Risk Management Design

The cross-sectional book is risk-managed by construction (Section 5). The legacy v3 7-gate stack stays **deferred** — re-introducing it onto the cost-aware cross-sectional book in the same iteration would confound the construction measurement (the same honest scoping call /088 made). The cross-sectional gate re-design (which v3 gates transfer to a market-neutral cross-sectional book) remains a future-iteration axis. /089's risk apparatus is: dollar-neutral construction + inverse-vol + vol-targeting + quintile diversification + the overlapping-hold tranching + the no-trade band + the HARD turnover ceiling.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (honest)

The /088 closeout's calibration lesson is recorded and applied: *"when a signal's rank-IC magnitude is ~0.04 and the rebalance cadence is every-bar, the turnover-cost-dominated outcome is not a 5% tail — it is the modal risk."* /089's distribution reflects that the gross signal is thin and the construction fixes are necessary-but-likely-insufficient:

- **≈45% — the modal outcome: the corrected + cost-aware construction MATERIALLY improves the OOS book vs /088 (OOS monthly Sharpe lifts from −0.54 toward [−0.30, +0.05]), turnover stays within the 0.138 ceiling, OOS rank-IC stays positive — but the OOS monthly Sharpe remains sub-floor (below +1.0, plausibly still slightly negative).** The construction fixes work and transfer, the turnover gate passes, but the thin gross signal keeps the net book below the floor. This is a genuine advance on the construction axis and the expected result; /090's gross-signal expansion is the next required lever.
- **≈20% — the construction fixes work AND the OOS book turns net-positive** (OOS monthly Sharpe in (0, +1.0)) — the corrected sign + turnover reduction is enough to flip the OOS book positive but still sub-floor. A good outcome; sets up /090/091 cleanly.
- **≈20% — F3 fires: the construction levers do NOT improve the OOS book** (OOS monthly Sharpe ≤ −0.54). The IS-internal walk-forward improvement did not transfer OOS — most likely the hold/band that helps on IS does not help on the OOS regime. The cost-aware-construction hypothesis is falsified for the cycle.
- **≈10% — F2 fires: the realised IS turnover breaches the 0.138 ceiling** — a build/measurement defect (the overlapping-hold or no-trade-band wiring did not actually contain turnover). NO-MERGE; investigate.
- **≈5% — full success: OOS monthly Sharpe ≥ +1.0.** The corrected construction clears the floor on the first corrected pass. The IS evidence (E5 net Sharpe still −0.31) makes this the tail — named honestly, not expected.

The single most-likely outcome is the **≈45% "construction works and transfers, OOS book materially improved but sub-floor"** — named here, honestly, as the expected result of a construction-fix iteration on a thin-gross-signal architecture, and a genuine advance that hands /090 a quantified gross-signal axis.

---

## Section 8 — Pre-Registered Classification Taxonomy (LOCKED)

iter-v3/089 is a corrected-build EXPLORATION on the RETAINED cross-sectional architecture. The taxonomy, evaluated in disjunctive precedence (first match canonical):

### 8.1 — SUSPICIOUS (evaluated FIRST)
Fires on EITHER (a) OOS monthly Sharpe / IS monthly Sharpe **> 3.0** (the OOS-soars-on-flat-IS signature — N/A if both are negative), OR (b) OOS rank-IC ≥ 2× the IS rank-IC magnitude (an implausible OOS-better-than-IS divergence).

### 8.2 — CONSTRUCTION-FALSIFIED
Fires if (NOT SUSPICIOUS) AND **F2 fires (IS turnover > 0.138 ceiling) OR F3 fires (OOS monthly Sharpe ≤ the /088 book's −0.5418)**. The cost-aware construction did not contain turnover, or did not improve the OOS book vs the /088 predecessor → the /089 cost-aware-construction hypothesis is falsified for the cycle. NO-MERGE. The cross-sectional architecture and `cross_sectional.py` infrastructure are RETAINED (the architecture is not falsified — the /088 OOS rank-IC stands; only the /089 construction levers are).

### 8.3 — CONSTRUCTION-VALIDATED-PROMISING
Fires if (NOT SUSPICIOUS, NOT 8.2) AND **OOS rank-IC > 0 AND IS turnover ≤ 0.138 AND OOS monthly Sharpe > the /088 book's −0.5418 AND OOS monthly Sharpe > 0**. The corrected construction works, contains turnover, transfers OOS, and produces a net-positive OOS book. Sub-case **8.3-FULL**: additionally OOS monthly Sharpe ≥ +1.0 AND IS monthly Sharpe ≥ +1.0 — clears the absolute floors; a /092 CONFIRMATION-bundle candidate. Sub-case **8.3-FOUNDATION**: OOS monthly Sharpe ∈ (0, +1.0) — validated and generalising but sub-floor; advances as the cross-sectional construction baseline for /090/091.

### 8.4 — CONSTRUCTION-PARTIAL (the honest modal outcome)
Fires if (NOT SUSPICIOUS, NOT 8.2, NOT 8.3) AND **OOS rank-IC > 0 AND IS turnover ≤ 0.138 AND OOS monthly Sharpe > the /088 book's −0.5418** but the OOS monthly Sharpe is **≤ 0** (so 8.3 does not fire — the book improved materially but is not yet net-positive). The corrected construction works, contains turnover, transfers OOS, and **materially improves the OOS book** — but the thin gross signal keeps it sub-zero. NO-MERGE; the cross-sectional construction axis is advanced and /090's gross-signal expansion is the next required lever. **This is the Section-7 ≈45% modal prediction.**

### 8.5 — NULL / INCONCLUSIVE
The Phase-6 build did not reach a runnable cross-sectional backtest. Recorded for completeness; the build is a focused change on the RETAINED runnable /088 infrastructure, so this is not expected.

**An EXPLORATION cannot update BASELINE_V3.md regardless of classification.** BASELINE_V3.md stays `v0.v3-059` (IS +1.0894 / OOS +0.5791).

---

## Section 9 — Library Stack Declaration

- **LightGBM** — `LGBMRanker` with `objective="lambdarank"` (the RETAINED /088 model; unchanged). Already a v3 dependency.
- **Optuna** — hyperparameter search (existing v3 dependency); CV objective = IS rank-IC.
- **pandas / numpy** — pooled-panel construction, the overlapping-tranche book, the no-trade band, the turnover diagnostic, the CPCV path net-return computation.
- **No new third-party dependency.** Every /089 change — the sign fix, the CPCV-proxy fix, the quintile/overlapping-hold/no-trade-band construction, the turnover-ceiling gate — is pure pandas/numpy on the existing LightGBM ranking model.

## Section 10 — QR Audit Trail

### 10.1 — The orchestrator's lead steer and the QR call

The orchestrator's dispatch LOCKED the **scope** of /089 — the two mandatory corrections (Critic /088 Recs #2/#3) plus the genuine axis (make the corrected cross-sectional architecture profitable by attacking turnover structurally), per the /088 closeout. Per `feedback_v3_axis_selection_quant_discipline.md`, the QR owns every *design* decision within that scope, EDA-grounded. The QR's calls in this brief, all IS/research-grounded: the quintile quantile (EDA E2 + G1); the 3-bar overlapping hold (EDA E3 + Jegadeesh-Titman); the no-trade band τ=0.020 (EDA E4 + Constantinides/Davis-Norman); the 0.138 turnover ceiling (EDA E6); the decision to DEFER the gross-signal feature expansion to /090 (EDA G4 — a +2% IC-IR lift that needs its own dedicated EXPLORATION). The QR also confronted the open strategic question the /088 closeout posed — whether the gross signal needs strengthening — and answered it honestly with the committed gross-signal EDA (G1–G4): yes, it does, and /090 is the axis for it.

### 10.2 — Literature-research path (genuine WebSearch/WebFetch, Phases 1–4)

Cost-aware cross-sectional portfolio construction — turnover control, no-trade bands, holding-period optimisation, quantile concentration:

1. **Poh, Lim, Zohren & Roberts (2021), "Building Cross-Sectional Systematic Strategies By Learning to Rank"** — arXiv 2012.07149 / *J. Financial Data Science* 3(2):70 / SSRN 3751012. The /088 methodology paper, re-consulted for the QUANTILE-CONCENTRATION result: *"there is a general trend of returns and Sharpe ratios increasing from decile 1 to decile 10 ... with a steeper rise for the LTR models stemming from their ability to place assets in their appropriate deciles with greater precision — leading to a greater difference in returns between the decile 1 and decile 10 portfolios."* This grounds the /089 quintile choice — concentrate the legs to exploit the LTR's tail precision. (The paper uses deciles for a large equity universe; /089's EDA G1 shows decile is too thin at N=22 and quintile is the sweet spot.)
2. **Constantinides (1986), "Capital Market Equilibrium with Transaction Costs"** / **Davis & Norman (1990), "Portfolio Selection with Transaction Costs"** (*Mathematics of Operations Research* 15(4):676) — the no-trade-region theory. Proportional transaction costs create a **no-trade region**; when a holding leaves the region it is rebalanced to the (target) boundary. The optimal no-trade band width is **O(ε^1/3)** in the proportional cost ε, and the utility loss is **O(ε^2/3)**. This grounds the /089 no-trade band: when costs dominate the gross signal (the /088 case, fees 8.8× gross PnL), a non-trivial no-trade band is mandatory and a small band is catastrophically suboptimal. The EDA E4 scan selects τ=0.020 on IS data.
3. **Jegadeesh & Titman (1993), "Returns to Buying Winners and Selling Losers"** (*Journal of Finance* 48(1)) + the 30-years-after review (*Financial Markets and Portfolio Management* 2023, 37:95) — the **overlapping-portfolio construction**. At a K-bar holding period, a new tranche is formed each bar and the tranche from K bars ago is closed; the book is the sum of the live tranches. The review confirms: *"no significant difference in returns between overlapping and non-overlapping portfolios ... overlapping portfolios provide the added benefit of diversification."* This grounds the /089 3-bar overlapping hold — cut turnover ~H-fold with the signal largely preserved.
4. **"Rebalancing with transaction costs: theory, simulations, and actual data"** (*Financial Markets and Portfolio Management* 2022, 36) + **Federico Baldi-Lanfranchi, "Transaction-cost-aware Factors" (2024)** — the practitioner cost-aware-rebalancing literature. Findings adopted: *"keeping the weights closer to target requires more frequent rebalancing and higher costs; allowing less frequent rebalancing results in greater disparity between portfolio and target weights"* (the turnover/tracking-error tradeoff the /089 no-trade band navigates); *"when transaction costs are nonzero, factors rebalance too aggressively, and suboptimal construction compresses net risk-premia, biasing results against high-turnover factors"* — exactly the /088 failure, and the reason /089 pre-registers a hard turnover ceiling.
5. **Cross-sectional crypto reversal net of costs** — "New behaviorally-based cross-sectional reversal portfolios in the cryptocurrency market" (*International Review of Financial Analysis* 2025) and the cryptocurrency-anomalies-and-economic-constraints literature (*IRFA* 2024): crypto cross-sectional reversal *"retains profitability after incorporating conservative transaction costs"* but *"trade size can substantially reduce portfolio returns"* and tradable-anomaly protocols must *"account for transaction costs, consider hard-to-trade coins, and emphasize recent years."* This confirms the /089 thesis — the crypto cross-sectional edge survives costs only with cost-aware construction — and the honest residual: the edge is thin, so cost-awareness alone is necessary but not sufficient.

The research path: paper 1 supplied the quantile-concentration result; paper 2 supplied the no-trade-band theory and the O(ε^1/3) sizing rationale; paper 3 supplied the overlapping-hold construction; paper 4 supplied the practitioner turnover/cost framework and the "pre-register a turnover budget" discipline; reference 5 supplied the crypto-specific net-of-cost evidence and the honest "thin edge" caveat.

### 10.3 — No-cheating audit

Per `feedback_no_cheating.md` — every design parameter selected on IS data only or a-priori:

- **OOS_CUTOFF_DATE / training_months** — IMMUTABLE, untouched.
- **The SIGN FIX** — a first-principles correction of what `lambdarank` on a forward-return-grade label learns; no data involved.
- **The CPCV-PROXY FIX** — a methodology correction (run the model, compute the actual net return); no parameter tuned.
- **Quantile = quintile (0.20)** — `E2_quantile_concentration.csv` (IS-internal walk-forward net Sharpe) + `G1_horizon_quantile_spread.csv` (IS realised spread Sharpe). Both IS-only; OOS never read. Cross-checked against the Poh/Lim/Zohren quantile-concentration result.
- **Hold = 3 bars** — `E3_overlapping_holds.csv` (IS-internal walk-forward); also horizon-matched (= `XS_HORIZON`) and the Jegadeesh-Titman convention.
- **No-trade band τ = 0.020** — `E4_no_trade_band_scan.csv`: τ scanned on IS data, τ=0.020 the IS-best net Sharpe of the grid. OOS never read.
- **Turnover ceiling = 0.138** — `E6_turnover_ceiling.csv`: the IS-best /089 construction's IS turnover/bar (0.120) × 1.15 headroom. An IS-derived a-priori gate.
- **The 13-feature set, the universe, the H=3 label, the embargo** — UNCHANGED from /088 (all /088-IS-grounded). The G4 feature-expansion candidate is **deferred to /090**, explicitly NOT carried in /089.
- The IS-internal walk-forward in `turnover_construction_eda.py` trains the ranker ONLY on IS months and predicts the NEXT IS month — never an OOS row. The gross-signal EDA `gross_signal_eda.py` reads only IS rows.
- The QR sees OOS for the first time in Phase 7. Every Section 4 OOS gate is a pre-registered evaluation gate, not a tuned parameter.

### 10.4 — The honest senior read

iter-v3/089 is a genuine, well-researched advance on the cross-sectional construction axis — and it is honest about its limits. The two mandatory corrections (sign, CPCV-proxy) are real bug/methodology fixes. The cost-aware construction (quintile + overlapping holds + no-trade band) is fully IS-validated and grounded in the canonical cost-aware-portfolio literature, and it halves the IS net loss. The pre-registered hard turnover ceiling makes the "attack turnover" claim a gate, not a footnote. But the committed gross-signal EDA delivers the hard truth the /088 closeout anticipated: the realised cross-sectional gross spread is structurally thin (≈ −0.04 per-bar spread Sharpe), and no construction lever — nor a marginal feature expansion — lifts it to a positive net Sharpe on IS data. So /089's honest modal outcome is CONSTRUCTION-PARTIAL: the construction works and transfers, the OOS book is materially improved, but it is still sub-floor — and /090's gross-signal feature expansion is the next required lever, scoped and IS-quantified here (G4). This is not defeatism; it is the relentless, honest execution the mission demands — /089 advances the architecture on the construction axis and hands /090 a concrete, IS-grounded gross-signal axis.

## Section 11 — Reproducibility Stamp

- **EDA SHA**: `c172a12` — `analysis/iteration_v3-089/turnover_construction_eda.py` (E1–E6 CSVs) + `analysis/iteration_v3-089/gross_signal_eda.py` (G1–G4 CSVs).
- **Brief SHA**: `<BRIEF_SHA>` (this research brief); the Section-11 SHA backfill in the immediately-following commit.
- **Setup SHA**: `<SETUP_SHA>` — the sign fix + CPCV-proxy fix + cost-aware construction + turnover ceiling wired into `cross_sectional.py` / `run_cross_sectional_v3.py`; ITERATION_LABEL "v3-089"; the 6 new /089 tests in `tests/strategies/ml/test_cross_sectional.py`.
- **Reports**: `reports-v3/iteration_v3-089/` (Phase 6).
- **Run mode**: EXPLORATION — single-seed (seed=42), `--n-trials 35` (the cross-sectional-path runner spec).
- **Future-iteration axes** (deferred from /089, recorded for the cycle plan): (i) /090 — the cross-sectional gross-signal feature expansion (EDA G4: cross-sectional momentum/reversal multi-lookback channels, +2% IC-IR on IS — a dedicated EXPLORATION with its own EDA, multivariate-contribution tested per the iter-v3/070 dead-path discipline); (ii) the cross-sectional risk-gate re-design (which v3 gates transfer to a market-neutral book); (iii) a long-only top-quantile variant (Cakici et al.: crypto abnormal returns concentrate in the long leg); (iv) a dedicated cross-sectional CONFIRMATION if /089/090/091 reach a CONSTRUCTION-VALIDATED-PROMISING result.
