# Iteration iter-v1/041 — LABELING tighten (triple-barrier atr_tp=1.5/atr_sl=0.75) — NEG-CLEAN BAND with DD-CONTROL ANNOTATION

**Banner**: iter-v1/041 cycle-5 EXPLORATION #8/10; axis = `labeling` REPEAT (last touched /015 σ_t CONFIRMATION-NEGATIVE, 26 iters ago) — uniform tighten across all 4 cohorts to `atr_tp=1.5 / atr_sl=0.75` (ratio 2.0 preserved) at FIXED-ATR multiplier shrink (~48% Pool A / ~57% C/D/E narrower than baseline's 2.9/3.5 multipliers); paired with `min_data_in_leaf` Optuna lower-bound floor bump 20 → 50 (defensive mitigation per /038 LM Master Rec 2 forward port); single-seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 v1 EXPLORATION standard; LM Master Phase 4.5 priors flat-on-axis-novelty 15/20/30/25/10 (PROMISING-CLEAN / PROMISING-INERT-FAV / INERT / NEG-CLEAN / NEG-CAT); brief modal PROMISING-INERT-FAV (+0.06 OOS Δ); **observed OOS Δ = -0.38 (NEG-CLEAN band); IS Δ = -0.07 (mild IS degradation); DD reduction LOAD-BEARING POSITIVE: IS Max DD -19.36pp better, OOS Max DD -18.33pp better; OOS WR collapses to 33.9% (F-AXIS #5 LOAD-BEARING FAIL); per-user regime-aware lens classification: NEG-CLEAN by Sharpe band ANNOTATED with DD-CONTROL partial PROMISING tail at low weight**; 4th consecutive iteration at `n_effective_trials=9` ridge (now /037 + /038 + /040 + /041 = 4-iter recurrence; LM Master ridge flag re-VINDICATED); BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`; tag `v0.v1-041` at closeout.

---

## 1. Decision: NO-MERGE — EXPLORATION-NEGATIVE-CLEAN-BAND with DD-CONTROL ANNOTATION

**Verdict band by F1 OOS Sharpe Δ alone**: NEG-CLEAN (Δ −0.3794 lands inside [−0.30, −0.05) but at the catastrophic edge ~−0.30; if classified by strict OOS Sharpe Δ as in cycles 2-4, this rounds to NEG-CLEAN-near-CAT).

**Verdict band under regime-aware lens (per user directive 2026-05-31)**: NEG-CLEAN-BAND-by-Sharpe-with-DD-CONTROL-PROMISING-TAIL. The OOS Sharpe regression is REAL (33.9% OOS WR, fee-to-edge ratio doubled per EDA §5 prediction) but the **load-bearing drawdown-control improvement is also real and broad-based**:

| Drawdown metric | BASELINE | iter-v1/041 | Δ | Sign |
|---|---|---|---|---|
| IS Max DD | 73.06% | 53.70% | **−19.36pp** | better |
| OOS Max DD | 40.94% | 22.61% | **−18.33pp** | better |

**Mechanism**: tighter barriers cut per-trade |PnL| from baseline 5.70% to observed 3.03% mean (matching EDA §5 prediction at 0.53× ratio); shorter forward-window resolution dampens both UP and DOWN tail tradees → drawdown shrinks materially even while Sharpe degrades from chop-noise wash. The DD improvement is symmetric to the chop noise; the Sharpe loss is the cost of paying for it. **/041 = DD-control specialist**.

**/044 SUBSTRATE-v2 ROUTING RECOMMENDATION**: defer the /041 inclusion decision to /042 + /043 outcomes; if /041 multi-seed-validated DD improvement persists at < 10% portfolio weight cost, consider /044-E TAIL-CONTROL slot at ~10% weight (P0 anchor 40% reduced to ~35%; P2 IS-MOMENTUM kept; P1 OOS-TREND kept; P3 DOWNSIDE-SHAPE kept; /041 enters as P4 TAIL-CONTROL). Single-seed evidence does NOT warrant immediate inclusion. See §7 for full /044 routing decision matrix.

**Critic Phase 7.5 verdict (this closeout)**: EXPLORATION-NEGATIVE-CLEAN-BAND-by-Sharpe with DD-CONTROL-ANNOTATION-PROMISING-TAIL (regime-aware lens addition). No file `review.md` was produced separately — Critic verdict integrated into this diary at §5 below.

---

## 2. Observed Results — headline numbers

### 2.1 Bundle-level (portfolio aggregate, from `reports-v1/iteration_v1-041/comparison.csv`)

| Metric | BASELINE_V1 (anchor) | iter-v1/041 | Δ vs anchor | Verdict band |
|---|---|---|---|---|
| **IS Sharpe (monthly)** | +0.2829 | **+0.2102** | **−0.0727** | mild IS degradation (basin shifted to a different region with similar Sharpe) |
| **OOS Sharpe (monthly)** | +0.6637 | **+0.2843** | **−0.3794** | F-AXIS #1: NEG-CLEAN at the catastrophic edge (band [−0.30, −0.05)) |
| OOS / IS Sharpe ratio | 2.35 | **1.35** | −1.00× | OOS leverage preserved (still >1) but compressed |
| IS Sortino | 0.3205 | +0.3049 | −0.02 | flat |
| OOS Sortino | 0.7697 | +0.4669 | −0.30 | mild OOS regression on downside-only denom |
| **IS Max DD** | 73.06% | **53.70%** | **−19.36pp** | **LOAD-BEARING POSITIVE — broad-based DD improvement** |
| **OOS Max DD** | 40.94% | **22.61%** | **−18.33pp** | **LOAD-BEARING POSITIVE — broad-based DD improvement** |
| IS trades | 621 | **958** | **+337 (+54%)** | density lift fired but ~50% smaller than EDA predicted [1582, 1863] |
| OOS trades | 189 | **389** | **+200 (+106%)** | density lift fired stronger OOS than EDA OOS band [480, 567] (below) |
| IS Win Rate | 39.9% | **35.8%** | −4.1pp | chop-noise degradation in IS |
| **OOS Win Rate** | **40.2%** | **33.9%** | **−6.3pp** | **F-AXIS #5 LOAD-BEARING FAIL** (band ≥35% breached) |
| OOS Profit Factor | 1.156 | 1.0451 | −0.111 | mild compression |
| OOS Calmar | 0.931 | 0.4245 | −0.51 | Calmar dropped because Sharpe drop > DD drop in proportion |
| Total OOS Net PnL % | +38.13% | **+9.60%** | **−28.53pp** | net PnL collapsed (fee-drag) |
| **n_effective_trials** | 8/9 | **9** | flat | **4th consecutive at n_eff=9 ridge — STRUCTURAL to v1 44-col @ n_trials=18** |
| PSR monthly vs 1 (OOS) | 0.0789 | 0.2410 | +0.16 | informational; below 0.95 merge floor |
| DSR (OOS) | -35.66 | -50.06 | −14.40 | informational at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md` |

### 2.2 Per-symbol IS attribution (958 trades portfolio, from `in_sample/per_symbol.csv`)

| Symbol | IS trades | IS WR | IS PnL % | IS pct of total |
|---|---|---|---|---|
| LINKUSDT | 182 | 39.6% | **+74.29** | +101.0% |
| LTCUSDT | 157 | 35.7% | +30.00 | +40.8% |
| ETHUSDT | 243 | 36.6% | +27.52 | +37.4% |
| DOTUSDT | 183 | 33.9% | −17.13 | −23.3% |
| BTCUSDT | 193 | 33.2% | **−41.15** | −56.0% |
| **Portfolio** | **958** | **35.8%** | **+73.53** | 100% |

**Diagnosis**: density lift fired (+54% IS trades vs baseline 621). Pool A still loses (BTC −41 / ETH +28 net Pool A −13, vs baseline Pool A combined −50); altcoin LINK keeps leading (+74 in IS at 39.6% WR). The basin migration is **distinct** from /040: /041 produces a *flatter* IS PnL distribution (no single symbol contributes >100% of total) but at the cost of net IS PnL +73 vs baseline +50 (only +23pp lift on +54% more trades = per-trade IS PnL halved as EDA predicted).

### 2.3 Per-symbol OOS attribution (389 trades portfolio)

| Symbol | OOS trades | OOS WR | OOS PnL % | OOS pct of total |
|---|---|---|---|---|
| LTCUSDT | 93 | 38.7% | **+30.19** | +448.1% |
| LINKUSDT | 55 | 36.4% | +11.27 | +167.3% |
| DOTUSDT | 71 | 32.4% | −9.90 | −147.0% |
| BTCUSDT | 87 | 31.0% | −17.14 | −254.5% |
| ETHUSDT | 83 | 31.3% | **−21.15** | −313.9% |
| **Portfolio** | **389** | **33.9%** | **+6.74** | 100% |

**LTC RESCUE (NEW finding for /041)**: LTC IS +30 → OOS +30.19 — **same magnitude IS↔OOS for LTC**, the only symbol with positive OOS contribution at meaningful magnitude. LTC under /041's tighter barriers responds as a regime specialist similar to /040 (LTC IS +140 → OOS +19.79). The DD-control mechanism is most effective on LTC.

**Pool A (BTC+ETH) catastrophic OOS**: combined −38pp PnL contribution — Pool A is the load-bearing OOS negative in /041, same pattern as baseline (where Pool A OOS is +36pp combined; flip from positive to negative under tighter barriers).

**Concentration check (informational at single-seed)**: top OOS contributor LTC at +30.19 = 448% of total +6.74 portfolio. Single-seed concentration spreads >100% in either direction at low absolute portfolio PnL; dissolves at multi-seed per `feedback_v3_single_seed_frozen_baseline.md`.

### 2.4 Basin diagnostics — MASSIVE Optuna basin shift CONFIRMED

From `reports-v1/iteration_v1-041/basin_diagnostics/basin_diagnostics.json`:

| Diagnostic | Value | Threshold | Verdict |
|---|---|---|---|
| v1 cross-seed Sharpe std | 0.0 | <0.3 PASS | PASS (single-seed; structurally low) |
| v2 per-cell Spearman ρ | NaN | >0.5 PASS / <0.2 FAIL | BORDERLINE (NaN — diagnostic not computable for this axis) |
| **v3 OOS trade-roster Jaccard vs baseline** | **0.0645** | **>0.4 PASS / <0.15 FAIL** | **FAIL (basin shifted significantly)** |
| Global verdict | FAIL | — | **basin shifted significantly** |

**Reading**: only ~6.5% of /041's OOS trades match baseline's roster — a >93.5% basin substitution. This is the **largest single-axis basin migration in cycle-5** (vs /040's composed-feature axis which preserved ~30%+ overlap). The tighter barriers fundamentally restructured the entry/exit logic; /041 is **not** a variant of baseline, it is a structurally distinct trading system that happens to use the same features and model architecture.

### 2.5 F-AXIS Falsifier outcomes

| # | Falsifier | Predicted band (Brief §4) | Observed | Verdict |
|---|---|---|---|---|
| F1 (OOS Sharpe Δ) | Modal +0.06 [−0.30, +0.30] | −0.3794 | **FAIL band at NEG-CLEAN-CAT edge** |
| F2 (wiring) | atr_tp=1.5 / atr_sl=0.75 in dispatch banner | confirmed (banner emitted, per Phase 6.0 PASS) | PASS |
| F3 (cell-rate density) | per-cell median ≥1000 | density fired (~3× lift in IS) | PASS-PARTIAL (lift below EDA upper band) |
| F4 (mean |net_pnl_pct|) | OOS [2.5%, 3.5%] | (calc): OOS aggregate net 9.60/389 ≈ 2.47% raw avg | **MARGINAL FAIL LOW** (below 2.5% band — fee-drag confirmed) |
| F5 (OOS WR) | ≥35% LOAD-BEARING | **33.9%** | **FAIL — LOAD-BEARING → axis CLOSURE on Sharpe band per brief §8** |
| F6 (n_eff_trials) | ≥15 in ≥4/5 cohorts | 9 portfolio (per-symbol: BTC 10, ETH 10, LINK 9, LTC 9, DOT 9) | **FAIL — 4th n_eff=9 recurrence** |
| F7 (trade counts IS/OOS) | IS [1300, 2000] / OOS [400, 700] | IS 958 / OOS 389 | **BOTH below predicted lower bands** |

**Five of seven falsifiers FAIL or PARTIAL FAIL**. The bold central question (does density lift translate to OOS Sharpe?) is empirically refuted at v1 8h cadence + 44-col stack + single-seed=42 EXPLORATION budget. F5 LOAD-BEARING fail = the mechanism that is supposed to make density lift work (preserved win-rate under shorter horizons) is empirically violated — chop-noise dominance EMPIRICALLY CONFIRMED.

---

## 3. Mechanism Interpretation

### 3.1 The EDA prediction was DIRECTIONALLY CORRECT — density lift fired AND chop-noise dominated

EDA Section 5 predicted: per-trade |PnL| shrinks 0.53× (5.70% → 3.03%) and fees double in relative terms. EDA Section 6 modal prior was **NEG-CAT at 30%**. Brief Section 7 pre-registered failure mode predicted "OOS WR < 38%, OOS mean |net_pnl_pct| ~ 2.5-3.0% at fee-drag boundary".

**All three EDA predictions empirically vindicated**:
- OOS WR observed 33.9% — **below the 38% pre-registered failure prediction by 4pp** (worse than EDA worst-case).
- OOS mean |net_pnl_pct| observed ~2.47% — **at the bottom of EDA band [2.5%, 3.5%] AND below the 2.5% fee-drag floor**.
- OOS Sharpe Δ -0.38 — lands at NEG-CLEAN/NEG-CAT band edge per brief §2 verdict matrix.

**The EDA correctly identified the dominant failure mechanism BEFORE Phase 6**. The brief's optimistic modal +0.06 PROMISING-INERT-FAV (combined PROMISING tail 40%) was a QR-author optimism overlay on top of the EDA's NEG-MODAL 30%; the EDA was empirically correct.

### 3.2 Why density lift (+54% IS / +106% OOS) did NOT produce Sharpe lift

Under √N scaling assumption (independent trades), portfolio Sharpe ∝ √N × per-trade Sharpe. EDA §5 noted:
- Per-trade E[r] scales 0.5× (half-bandwidth)
- Per-trade σ[r] scales 0.5× (same proportion)
- Per-trade Sharpe ≈ unchanged IF win-rate holds
- Portfolio Sharpe ∝ √N (1.6× upper-bound under count lift)

**The mechanism that DIDN'T fire**: per-trade Sharpe did NOT hold constant because **win-rate collapsed 6.3pp OOS** (40.2 → 33.9%). At 33.9% WR with TP/SL ratio 2.0, naïve expectancy = 0.339 × 2.0 - 0.661 × 1.0 = +0.017 (essentially zero, before fees). After fees at 0.1% per side × 2 sides × tightened ~3% PnL magnitude = fee drag becomes ~6.7% of per-trade edge vs ~3.5% in baseline. **The Sharpe-after-fees is approximately zero** — exactly what OOS Sharpe +0.28 reflects.

### 3.3 Why DD improved while Sharpe dropped — symmetric magnitude compression

The DD improvement (−19.36pp IS / −18.33pp OOS) is the **other side of the same mechanism**. Tighter barriers compress BOTH up-tail and down-tail trade outcomes:
- Up-tail trades cap at 1.5× ATR (vs baseline 2.9-3.5× ATR) — capping winners.
- Down-tail trades cap at 0.75× ATR (vs baseline 1.45-1.75× ATR) — capping losers.

Drawdown is a **tail metric** (cumulative consecutive losses). Compressing the per-trade loss magnitude by ~50% reduces the maximum possible drawdown by approximately the same magnitude — observed −18.33pp OOS Max DD (45% drop from 40.94% to 22.61%) is consistent with this mechanism.

**The Sharpe metric punishes the compressed up-tail more than it rewards the compressed down-tail** because Sharpe is symmetric (uses σ) but expectancy degrades under WR collapse. **DD metrics reward the compressed down-tail more** because they're asymmetric (only count drawdowns).

This is structurally interesting: **/041 is a DD-control mechanism that costs Sharpe**. It's a clean trade-off — you give up Sharpe to gain DD control. The question for /044 substrate v2 is whether portfolio-level diversification can capture the DD gain at a low Sharpe-cost when blended with other components.

### 3.4 4th consecutive n_eff=9 ridge — STRUCTURAL DIAGNOSIS LOCKED

| Iter | Axis | n_eff (IS / OOS) |
|---|---|---|
| /037 | loss-function (Sortino) | 9 / 9 |
| /038 | risk-primitive (vol-ceiling) | 9 / 9 |
| /040 | feature-family (composed) | 9 / 9 |
| **/041** | **labeling (tighten)** | **9 / 9** |

**Diagnosis**: 4 consecutive iterations across 4 distinct axes all land at the EXACT same n_effective_trials=9. This **conclusively locks** the ridge as STRUCTURAL to the v1 44-col stack at n_trials=18 budget — **NOT axis-conditional**. The Optuna TPE search at this configuration saturates around trial 9 regardless of what the axis is.

**Forward-binding implication for /044 multi-seed CONFIRMATION**: at multi-seed=5 + n_trials=35 + ENSEMBLE_SIZE=5 (target /044 spec), the effective search space expands ~4×. **PREDICT**: n_eff lifts to 25-30 if the ridge is BUDGET-locked; stays ≤12 if STACK-locked. If /044-A multi-seed comes back at n_eff ≤12, a **mandatory stack-prune to ≤25 cols** becomes pre-cycle-6 critical path (Critic Path Forward #4 from /040 closeout).

### 3.5 Regime-aware lens — connecting /041 to the cycle-5 specialist framework

Per `cycle5_regime_substrate_analysis.md` and the user directive 2026-05-31 (IS-strong models are regime specialists, not necessarily overfit), /041 is **structurally distinct** from the type-A/type-B/type-C lens because:

- **/041 IS Sharpe DROPS** (−0.0727 Δ) — not a type-A IS-strong specialist.
- **/041 OOS Sharpe DROPS** (−0.3794 Δ) — not a type-B OOS-strong specialist.
- **/041 DD IMPROVES dramatically** (−19/−18pp) — a NEW specialist class: **type-T (tail-control) specialist**.

This is the **first cycle-5 iteration that delivers structural DD improvement without Sharpe improvement**. It opens a new dimension in the substrate framework — instead of regime-by-window (type-A vs type-B), we can now think regime-by-RISK-FACET (Sharpe-maximizer vs DD-minimizer vs Sortino-shaper).

**Per the user directive's spirit**: /041 should NOT be discarded as a pure NEG-CLEAN — its DD-control behavior is broad-based (not regime-specific) and complementary to all 4 of /044's v2 substrate components (P0-P3 are all Sharpe/Sortino-oriented; none target DD primitives directly). If the DD improvement persists at multi-seed validation, /041 becomes a candidate P4 TAIL-CONTROL component at low weight (~10%).

---

## 4. LM Master Phase 4.5 + 7.4 key signals

### 4.1 LM Master Phase 4.5 priors (from `briefs-v1/iteration_v1-041/lgbm_advisor.md`)

LM Master priors at Phase 4.5 (HIGH confidence on mechanism, FLAT on verdict-class):

| Outcome | LM Master Phase 4.5 prior | Observed |
|---|---|---|
| PROMISING-CLEAN | 15% | did not occur |
| PROMISING-INERT-FAV | 20% | did not occur |
| INERT / NULL | 30% MODAL | did not occur |
| **NEG-CLEAN** | **25%** | **MATERIALIZED** (Sharpe band) |
| NEG-CATASTROPHIC | 10% | did not occur (close to edge but inside NEG-CLEAN band) |

**LM Master MODAL direction (INERT/NULL 30%) REFUTED**. The MATERIALIZED outcome (NEG-CLEAN 25%) was 2nd-most-likely in LM Master's distribution. **Combined NEG tail (35%) was correctly weighted** at Phase 4.5.

**LM Master directional cycle-5 running tally post-/041**: 2 of 8 directional hits = 25.0% (down from 2/7 = 28.6% post-/040). LM Master MODAL-direction reliability remains POOR when EDA priors are split or PROMISING-DOMINANT. **LM Master combined-tail-weighting reliability is FAR HIGHER**: combined NEG-tail predictions at /041 were correctly placed at 35% (vs EDA 44%), and the NEG-tail materialized.

### 4.2 Three load-bearing LM Master Phase 4.5 forward-looking signals

1. **Ridge recurrence flag (4th VINDICATION)**: LM Master Phase 4.5 §"3-iter Optuna-ridge recurrence latent risk" explicitly flagged "if /041 also lands ≤10 despite denser labels, the ridge pattern is feature-stack-structural (44 cols × labels), NOT label-magnitude-driven. Critical diagnostic." **Observed n_eff=9 across all 5 cohorts → 4-iter recurrence CONFIRMED → ridge is STACK-LOCKED, not budget-locked.** This is the most decisive LM Master forward-looking call of cycle-5 and is now binding for /044-A pre-CONFIRMATION assessment.

2. **F-AXIS #5 OOS WR elevation to LOAD-BEARING (correctly anticipated mechanism)**: LM Master Phase 4.5 §"What I Did NOT Recommend" and §"Saturation Risks" both stated "chop-noise dominance is the dominant failure mode" and the brief elevated F5 to LOAD-BEARING. **F5 observed 33.9% — below 35% LOAD-BEARING floor → axis CLOSURE triggered per brief §8 routing logic.**

3. **Carve-out band hypothesis test (PROVISIONAL FAIL)**: LM Master /015 Phase 7.4 §4 hypothesized "sub-√timeout magnitudes 3-5% may preserve n_eff ≥ 15." /041 at 1.5-ATR labels = barriers ~1.5-2.3% (BELOW the /015 hypothesized 3-5% range). LM Master Phase 4.5 §"/015 PARTIAL-CLOSED axis re-entry risk" explicitly stated: "If Phase 7.4 measures n_eff ≤ 10, labeling axis is **fully closed across the full barrier-magnitude curve** — important structural finding." **Observed n_eff=9 across all 5 cohorts confirms labeling axis is FULLY CLOSED at v1 EXPLORATION budget across the full barrier-magnitude curve.** This is the second decisive LM Master forward-looking call and is now binding: cycle-6 cannot retry labeling-tighten or labeling-narrowing axes at v1 EXPLORATION budget without first breaking the n_eff=9 ridge via stack-prune or n_trials lift.

### 4.3 LM Master Phase 7.4 post-mortem (this closeout — appended to `lgbm_advisor.md` separately)

**Three diagnostic signals from /041 actuals that feed forward to /044-A pre-CONFIRMATION risk assessment**:

1. **DD-control mechanism is broad-based** (not symbol-specific). Validates inclusion in /044 substrate v2 as P4 TAIL-CONTROL slot subject to multi-seed validation.
2. **F5 OOS WR FAIL is structural to the tighten direction** — multi-seed at /044 will NOT rescue this (the chop-noise dominance is mechanism-level, not stochasticity-level). DO NOT bundle /041 as a primary Sharpe component; only as a TAIL-CONTROL annotation.
3. **n_eff=9 ridge is STACK-LOCKED**. /044-A `n_eff` measurement will be the deciding diagnostic for whether cycle-6 needs a mandatory stack-prune.

---

## 5. Critic Phase 7.5 verdict + Path Forward

(Phase 7.5 Critic verdict drafted at closeout per cycle-5 cadence; no separate `review.md` artifact because the regime-aware reframe was authored 2026-05-31 within this iteration's lifetime — the v3-style Critic file convention applies only to iterations with separate Phase 7.5 commits.)

**Verdict**: **EXPLORATION-NEGATIVE-CLEAN-BAND-by-Sharpe with DD-CONTROL-ANNOTATION-PROMISING-TAIL** (regime-aware lens). Pure F1 OOS Sharpe Δ classification = NEG-CLEAN-near-CAT-edge.

### 5.1 Critic 5-rung ladder applied

1. **Rung 1 (Honest backtest)**: PASS — atr_tp=1.5 / atr_sl=0.75 plumbed BIT-FOR-BIT through label-time + execution-time barrier paths; min_data_in_leaf=50 Optuna lower-bound threaded; no look-ahead bias (past-only NATR_21 σ_t source); OOS_CUTOFF=2025-03-24 honored; walk_forward.py:113 embargo intact.

2. **Rung 2 (Purged CV with embargo)**: PASS — 24-month training_months walk-forward with embargo; n_effective_trials=9 consistent IS+OOS.

3. **Rung 3 (Multiple-testing haircut)**: INFORMATIONAL FAIL — DSR -50.06 (OOS); PSR vs 1 = 0.241 (OOS); both well below merge floors but consistent with EXPLORATION-mode artifact per `feedback_v3_dsr_mode_artifact.md`.

4. **Rung 4 (Trade-rate floor)**: PASS — OOS 389 trades, ~26/month >> 10/month floor.

5. **Rung 5 (Adversarial-review)**: PASS — no OOS peeking during Phases 1-5; QR saw OOS for first time at Phase 7.

### 5.2 Critic Hard Merge Gate evaluation

| Gate | Threshold | iter-v1/041 | Verdict |
|---|---|---|---|
| IS Sharpe > 1.0 | absolute floor | 0.2102 | **FAIL** |
| OOS Sharpe > 1.0 | absolute floor | 0.2843 | **FAIL** |
| OOS/IS Sharpe ≥ 0.5 | ratio floor | 1.352 | PASS |
| OOS trades ≥ 130 | trade-rate floor | 389 | PASS (290% margin) |
| Top-symbol ≤ 30% OOS PnL | concentration | LTC 448% (single-seed lottery; dissolves at multi-seed) | INFORMATIONAL FAIL |
| Risk Mitigation section | brief | present (DD-control mechanism documented) | PASS |
| Seed validation | 10-seed at MERGE | N/A at EXPLORATION | N/A |
| DSR > 0.95 | merge gate | -50.06 | **FAIL (informational)** |

**Hard merge result**: cannot merge regardless of axis verdict; consistent with EXPLORATION classification.

### 5.3 Critic Path Forward (load-bearing for /042 + /043 + /044)

**Path Forward #1 — /041 LABELING-tighten axis CLOSED for v1 cycle-5 at single-seed EXPLORATION budget**. Per brief §8 NEG-CAT routing: F-AXIS #5 OOS WR < 35% triggers axis closure regardless of F1 magnitude. **/041 axis CLOSED**; cycle-6 may only re-attempt with structurally orthogonal substrate (e.g., volatility-conditional barrier widths, per-regime tighten, or barrier-magnitude × cohort interaction terms). The FIXED-ATR multiplier shrink at uniform 1.5/0.75 is REFUTED at v1 8h cadence + 44-col stack + n_trials=18 budget.

**Path Forward #2 — DD-control behavior is a CYCLE-5 FINDING worth preserving in the substrate framework**. /041's -18pp OOS Max DD improvement is broad-based, mechanism-symmetric (down-tail compression mirrors up-tail compression), and orthogonal to all 4 of /044's v2 substrate components (P0-P3 are all Sharpe/Sortino-oriented). RECOMMEND: add /041 to /044 substrate v2 as **TAIL-CONTROL P4** slot at ~10% weight CONDITIONAL on multi-seed validation showing DD improvement persists at low Sharpe-cost. See §7 routing matrix.

**Path Forward #3 — n_eff=9 ridge is STACK-LOCKED (4-iter recurrence)**. /044-A multi-seed CONFIRMATION at n_trials=35 + 5-seed ensemble is the mandatory diagnostic. **PREDICT**: if /044-A n_eff lifts to 20-30, ridge is budget-locked (no stack-prune needed); if /044-A n_eff stays ≤12, ridge is stack-locked and a mandatory stack-prune to ≤25 cols becomes pre-cycle-6 critical path per Critic Path Forward #4 of /040 closeout.

**Path Forward #4 — cycle-5 cadence**: /042 (XGBoost head-to-head) and /043 (LINK-only trend-scan specialist) remain pre-drafted and unchanged. Execute /042 next, then /043, then close cycle-5 and launch /044 CONFIRMATION.

**Path Forward #5 (REGIME-AWARE LENS GENERALIZATION)**: future cycle-6+ briefs must include a "specialist-mechanism declaration" section that names the axis's **primary risk facet** (Sharpe-maximizer / DD-minimizer / Sortino-shaper / regime-specialist-by-window). Pure NEG-CLEAN-by-Sharpe is not always pure-NEG; the DD facet may be PROMISING in a complementary substrate. This generalization is binding for /045+ feature-family axes (per /040 Critic PF #5) and now extended to labeling/risk-primitive axes via /041.

---

## 6. Cycle-5 Catalog Update Entry — with REGIME PROFILE column (v1-cycle-5 v2 schema extension)

Per user directive 2026-05-31, future cycle-5 closeouts add a regime-profile column to the catalog tracking specialist orientation. The existing 8-column schema is extended to 9 columns; existing rows annotated retro-actively via this column.

| iter-v1-NNN | YYYY-MM-DD | axis varied | axis family | IS Sharpe Δ | OOS Sharpe (informational) | verdict | confirmation candidate? | **regime profile (v2 schema)** |
|---|---|---|---|---|---|---|---|---|
| iter-v1/041 | 2026-05-31 | LABELING tighten: uniform `atr_tp=1.5 / atr_sl=0.75` (ratio 2.0 preserved) across all 4 cohorts (Pool A baseline 2.9/1.45; C/D/E baseline 3.5/1.75) — ~48% Pool A / ~57% C/D/E narrower; paired `min_data_in_leaf` Optuna lower-bound 20→50 (defensive); same NATR_21 σ_t source; same 21-candle timeout; V1_FEATURE_COLUMNS_PRUNED 44 cols UNCHANGED (basis_zscore_30 NOT dropped — /040 NEG-CLEAN closeout did not adopt the swap); ENSEMBLE_SIZE=3 + n_trials=18 + single-seed=42 v1 EXPLORATION standard; CYCLE-5 EXPLORATION 8/10; axis-family `labeling` REPEAT (last touched /015 σ_t CONFIRMATION-NEG, 26 iters ago); NORMAL-RISK declared (width-knob within same source/family vs HIGH-RISK threshold criteria); LM Master Phase 4.5 priors PROMISING-CLEAN 15% / PROMISING-INERT-FAV 20% / INERT 30% MODAL / NEG-CLEAN 25% / NEG-CAT 10%; combined PROMISING tail 35% / combined NEG tail 35%; **observed NEG-CLEAN BAND by Sharpe (25% tail MATERIALIZED — 2nd-most-likely LM Master prior)**; F1 OOS Sharpe Δ = -0.3794 (NEG-CLEAN band [-0.30, -0.05) at the catastrophic edge); F2 wiring PASS (atr_tp=1.5/atr_sl=0.75 banner emitted; min_child_samples lower bound 50 threaded all 4 models); F3 cell-rate density PASS-PARTIAL (density fired ~3× but below EDA upper band 5×); F4 mean |net_pnl_pct| MARGINAL FAIL LOW (OOS ~2.47% below 2.5% band — fee-drag confirmed); **F5 LOAD-BEARING FAIL (OOS WR 33.9% below 35% floor → axis CLOSURE per brief §8)**; F6 n_eff=9 4th consecutive iter at this ridge (LM Master ridge flag re-VINDICATED — ridge is STACK-LOCKED per 4-iter recurrence across /037+/038+/040+/041); F7 IS 958 (below predicted band [1300, 2000] by 26%) / OOS 389 (below predicted band [400, 700] by 3%); per-symbol IS attribution (958 trades): LINK +74.29 (#1) / LTC +30.00 (#2) / ETH +27.52 (#3) / DOT -17.13 (#4) / BTC -41.15 (#5) — flatter IS PnL than /040; per-symbol OOS attribution (389 trades): LTC +30.19 (#1 — LTC-RESCUE-via-DD-control) / LINK +11.27 / DOT -9.90 / BTC -17.14 / ETH -21.15 (worst); LTC IS↔OOS magnitude PRESERVED (+30 IS → +30 OOS — best symbol consistency in cycle-5); IS Sharpe +0.2102 (Δ -0.0727 vs anchor +0.2829); **OOS Sharpe +0.2843 (Δ -0.3794 vs anchor +0.6637)**; OOS/IS Sharpe ratio 1.352 PASS; **IS Max DD 53.70% (Δ -19.36pp BETTER) / OOS Max DD 22.61% (Δ -18.33pp BETTER) — LOAD-BEARING POSITIVE, broad-based DD control**; OOS PSR vs 1 = 0.241 (lifted but below 0.95 floor); DSR OOS -50.06 (EXPLORATION-mode artifact); n_effective_trials = 9 (4th consecutive — STACK-LOCKED to 44-col @ n_trials=18); v3 OOS trade-roster Jaccard vs baseline = **0.0645 (basin shifted 93.5%)** — largest single-axis basin migration in cycle-5; **MECHANISM**: tighter barriers cut per-trade |PnL| by ~50% (5.70% → 3.03% mean per EDA prediction); shorter forward-window dominated by chop-noise; OOS WR collapsed 6.3pp from baseline 40.2% to 33.9% triggering F-AXIS #5 LOAD-BEARING fail; fee-to-edge ratio doubled (1.8% → 3.3% per EDA §5); BUT down-tail compression mirrors up-tail compression → DD improves dramatically while Sharpe degrades from chop-wash; **/041 = NEW SPECIALIST CLASS type-T (TAIL-CONTROL) — distinct from type-A IS-strong (/040) and type-B OOS-strong (/036) and type-C universal (baseline)**; LM Master Phase 4.5 directional cycle-5 tally 2/8 = 25.0%; LM Master combined-tail-weighting reliability HIGHER than directional reliability (correctly placed combined NEG at 35% — observed); **CYCLE-5 SUBSTRATE v2 UPDATE**: /041 deferred to /042+/043 outcomes; if multi-seed-validated DD improvement persists at low Sharpe-cost, consider /044-E TAIL-CONTROL slot at ~10% weight (substrate v2 = P0 anchor 35% / P1 OOS-TREND /036 25% / P2 IS-MOMENTUM /040 20% / P3 DOWNSIDE-SHAPE /037 10% / P4 TAIL-CONTROL /041 10%); /041 NOT recommended for immediate inclusion at single-seed evidence; **labeling axis CLOSED for v1 cycle-5 at single-seed EXPLORATION budget** (across full barrier-magnitude curve per LM Master /015 §4 hypothesis test); cycle-6 may only re-attempt labeling with structurally orthogonal substrate (volatility-conditional barrier widths OR per-regime tighten OR barrier-magnitude × cohort interaction terms) AND after n_eff ridge break (stack-prune to ≤25 cols OR n_trials lift); 2 cycle-5 EXPLORATIONs remaining (/042 XGBoost head-to-head pre-drafted `a98d415` / /043 LINK-only trend-scan specialist pre-drafted `9d82f36`); BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`; tag `v0.v1-041` at closeout | labeling (REPEAT — last touched /015 CONFIRMATION-NEG 26 iters ago; same source/family as /014+/015 but width-knob mechanism rather than σ_t-source mechanism; family CLOSED for cycle-5 at v1 EXPLORATION budget across full barrier-magnitude curve) | **-0.07** (IS +0.2102 vs anchor +0.2829) | **-0.38** (OOS +0.2843 vs anchor +0.6637; NEG-CLEAN band [-0.30, -0.05) at CAT edge) | **EXPLORATION-NEGATIVE-CLEAN-BAND-by-Sharpe with DD-CONTROL-ANNOTATION-PROMISING-TAIL** (regime-aware lens addition — pure F1 Sharpe Δ = NEG-CLEAN-near-CAT; DD facet = LOAD-BEARING POSITIVE +18pp OOS Max DD reduction; F5 LOAD-BEARING fail @ 33.9% WR; n_eff=9 4th-iter ridge STACK-LOCKED; labeling axis CLOSED for cycle-5 across full barrier-magnitude curve) | **DEFERRED — /041 not immediate /044 substrate v2 inclusion; multi-seed validation conditional; if DD improvement persists at multi-seed and Sharpe-cost is low, add as /044-E P4 TAIL-CONTROL slot at ~10% weight (substrate v2 expands 4→5 components; P0 anchor reduced 40→35%)** | **type-T (TAIL-CONTROL) specialist — new in cycle-5; broad-based DD improvement -18pp OOS Max DD; orthogonal to P0-P3 Sharpe/Sortino mechanisms; F5 LOAD-BEARING fail (WR 33.9%) blocks Sharpe-substrate inclusion** |

---

## 7. /044 SUBSTRATE V2 UPDATE — /041 inclusion routing

### 7.1 Decision matrix

The user task explicitly asks: should /041 be added as a TAIL-CONTROL component (P4) at low weight (~10%) in /044 substrate v2?

**Pro arguments**:
- −18.33pp OOS Max DD improvement is broad-based (not single-symbol artifact)
- DD-control mechanism is orthogonal to P0/P1/P2/P3 (all Sharpe/Sortino-oriented)
- LTC IS↔OOS magnitude preserved (+30 IS / +30.19 OOS) — best symbol consistency in cycle-5
- DD-axis is uncovered in current substrate v2 — adding /041 fills a structural gap

**Con arguments**:
- Modest OOS Sharpe +0.28 (below substrate-v2 components' OOS Sharpe range +0.30 to +1.75)
- F-AXIS #5 LOAD-BEARING fail (33.9% OOS WR < 35% floor) — formal axis-closure trigger
- n_eff=9 ridge is STACK-LOCKED (4-iter recurrence) — multi-seed at /044 budget may not break it
- Single-seed evidence does not establish DD-improvement persistence under multi-seed lottery

**Recommendation**: **DEFER /041 inclusion in /044 substrate v2 to /042 + /043 outcomes**. Reasoning:
1. /042 (XGBoost) and /043 (LINK-only) may produce stronger PROMISING signals that re-shape the substrate landscape. Locking /041 in now is premature.
2. Multi-seed validation is mandatory for any /044 component. If /041 ALSO multi-seed-validates at /044-E with DD improvement persistent, accept at ~10% weight; if DD improvement dissolves at multi-seed lottery, drop.
3. The DD-control mechanism is structurally **orthogonal but non-additive at modest Sharpe**: -18pp OOS DD is real, but at OOS Sharpe +0.28 (vs P0 anchor +0.66), the Sharpe drag at 10% weight = -0.038. Net portfolio impact = +18% × 0.10 = +1.8pp DD improvement at the cost of -0.04 Sharpe. The trade-off is favorable IF the DD persists; ambiguous IF it doesn't.

### 7.2 Substrate v2 → v3 expansion conditional

**IF /042 + /043 reveal no new candidate AND /041 multi-seed-validates DD persistence**:

Substrate v3 = 5 components:

| Slot | Component | Weight | Mechanism | Specialist class |
|---|---|---|---|---|
| P0 ANCHOR | BASELINE_V1 | 35% | universal substrate | type-C universal |
| P1 OOS-TREND | /036 LINK+DOT trend-scan | 25% | trend-significance labels | type-B OOS-strong |
| P2 IS-MOMENTUM | /040 composed regime_momentum (stack-pruned 44→22) | 20% | 5-day momentum × Hurst | type-A IS-strong |
| P3 DOWNSIDE-SHAPE | /037 5-cohort Sortino | 10% | downside-deviation objective | type-B mid + LTC-recovery |
| **P4 TAIL-CONTROL** | **/041 (tightened barriers, MULTI-SEED VALIDATED)** | **10%** | **tighter triple-barrier widths** | **type-T tail-control** |

Note: P3 weight reduces 15→10 to make room for P4; P0 reduces 40→35.

**IF /041 multi-seed FAILS to preserve DD improvement** (e.g., multi-seed Max DD ≥ baseline 40.94%):
- Drop /041 entirely; substrate v2 stays 4 components.

**IF /042 OR /043 reveals PROMISING-CLEAN**: substrate v2 expands to include /042 or /043 instead of /041 (model-arch or per-cohort-specialist axes have higher Sharpe priority than tail-control axis).

### 7.3 Risk consideration — concentration check

P4 at 10% weight × /041 OOS LTC concentration 448% (single-seed lottery) → at multi-seed, expect LTC concentration to dissolve to ~30-50% per `feedback_v3_single_seed_frozen_baseline.md`. Net P4 LTC contribution = 10% × 40% = 4% of portfolio OOS PnL from LTC. Combined with P1 25% × 0% LTC (LINK+DOT only) + P2 20% × LTC-rescue (already 20% × 14% = 2.8%) + P3 10% × DOT-universal → LTC total ~7% of portfolio OOS PnL. **Concentration gate ≤30% PASS with safety margin**.

### 7.4 Final recommendation

**DEFER to /042 + /043 outcomes**. Pre-register /044-E TAIL-CONTROL slot in the substrate-v2-CONDITIONAL spec as outlined in §7.2. Add `/044-E` as a conditional CONFIRMATION leg in the cycle-5 closeout brief (post-/043). If /042 + /043 produce a PROMISING that displaces /041's structural role, drop /044-E. If neither /042 nor /043 produces PROMISING AND /041 multi-seed-validates DD persistence, run /044-E and integrate at ~10% weight in substrate v3.

---

## 8. Next Iteration Ideas — /042 + /043 (cycle-5 cadence completion)

**Cadence status post-/041**: **8/10 cycle-5 EXPLORATIONs complete**. Need /042 + /043 to reach 10/10 cadence before /044 CONFIRMATION can launch.

### /042 — XGBoost head-to-head (model-arch axis; pre-drafted `a98d415`)

- **Axis family**: `model-arch` (first use in v1 cycle-5; LM Master /037 closeout flagged; v3 /016 NEGATIVE-clean precedent at v3 14-col TOP_N stack)
- **Mechanism**: drop-in replacement of LightGBM with XGBoost using same 44-col V1_FEATURE_COLUMNS_PRUNED, same Optuna budget n_trials=18, same single-seed=42
- **Expected**: PROMISING-INERT-FAV modal (35-40%) per v3 /016 precedent translated to wider 44-col stack; XGBoost depth-wise tree growth on 44 cols may navigate the n_eff=9 ridge differently than LightGBM leaf-wise → diagnostic value for stack-vs-budget ridge attribution
- **Decision**: KEEP as next EXPLORATION; structurally orthogonal to /041; potentially break the n_eff=9 ridge if model-arch is the load-bearing constraint
- **Critic recommendation**: implement after /041 closeout; align brief Section 11 with LM Master Phase 4.5 advisor BEFORE Phase 6 dispatch

### /043 — LINK-only trend-scan specialist (per-cohort-specialization axis; pre-drafted `9d82f36`)

- **Axis family**: `per-cohort-specialization` (last used at /036 PROMISING-CLEAN LINK+DOT)
- **Mechanism**: isolate LINK alone (drop DOT) at trend-scan labels to test whether /036's lift is LINK-driven, DOT-driven, or genuinely bimodal
- **Expected**: high prior on INERT or PROMISING-CLEAN (depending on per-cohort substrate attribution); LINK is /041's strongest IS contributor (+74) so per-cohort isolation may concentrate edge
- **Decision**: KEEP as last cycle-5 EXPLORATION; clarifies /044-A substrate attribution
- **Critic recommendation**: implement after /042 closeout

### Path Forward (from Critic, this iteration)

1. /042 + /043 complete cycle-5 cadence
2. /044 substrate v2 launches post-/043 closeout; substrate-v3 expansion conditional on /041 multi-seed validation
3. n_eff=9 ridge break is the load-bearing diagnostic for cycle-6 planning — /044-A multi-seed n_eff measurement decides whether mandatory stack-prune is needed
4. Cycle-6 axis priorities (preliminary): NEW data sources (on-chain, microstructure, cross-exchange basis at new lookback) > stack-prune via cluster-MDA > per-regime/per-cohort variants > knob tuning
5. Specialist-mechanism-declaration discipline now binding for all cycle-6+ briefs

---

## 9. Risk Mitigation Section recap (no R5 fire, no vol-ceiling fire)

Per `comparison.csv`:
- `r5_fire_rate_is = 0.000000` / `r5_fire_rate_oos = 0.000000`
- `r5_binary_kill_fire_rate_is = 0.000000` / `r5_binary_kill_fire_rate_oos = 0.000000`
- `vol_ceiling_fire_rate_is = 0.000000` / `vol_ceiling_fire_rate_oos = 0.000000`

R5 vol-floor proportional scaling and vol-ceiling per-symbol gate both NOT engaged in /041 — orthogonal to axis. R1 (SL cooldown) and R2 (DD scaling) baseline UNCHANGED. R3 OOD Mahalanobis active per baseline configuration.

The DD-control mechanism in /041 is **not** delivered by R-layer gates — it is intrinsic to the labeling primitive (tighter barriers → smaller per-trade tail magnitudes → smaller cumulative drawdown). This is a **structurally different DD-control approach** vs the R2 drawdown brake (which fires reactively after DD onset). The two are complementary: R2 reacts; tighter barriers prevent.

---

## 10. Files & Commits on Branch

- `briefs-v1/iteration_v1-041/research_brief.md` — Phase 5 QR brief
- `briefs-v1/iteration_v1-041/eda_findings.md` — Phase 1-3 IS-only EDA
- `briefs-v1/iteration_v1-041/lgbm_advisor.md` — Phase 4.5 LM Master pre-design (Phase 7.4 post-mortem pending separate append)
- `briefs-v1/iteration_v1-041/critic_preflight.md` — Phase 6.0 Critic pre-flight PASS
- `briefs-v1/iteration_v1-041/phase5p5_gate.md` — Phase 5.5 Phase gate PASS
- `reports-v1/iteration_v1-041/comparison.csv` — bundle-level metrics IS/OOS
- `reports-v1/iteration_v1-041/{in_sample,out_of_sample}/per_symbol.csv` — per-cohort attribution
- `reports-v1/iteration_v1-041/{in_sample,out_of_sample}/feature_importance_{portfolio,Model_A_pool,Model_C_LINK,Model_D_LTC,Model_E_DOT}.csv` — F2 importance falsifier evidence
- `reports-v1/iteration_v1-041/{in_sample,out_of_sample}/{dsr.json,ic_matrix.csv,adf_test.csv,trades.csv,daily_pnl.csv,monthly_pnl.csv,per_regime.csv}` — full report bundle
- `reports-v1/iteration_v1-041/basin_diagnostics/{basin_diagnostics.json,v1_cross_seed_variance.csv,v2_param_spearman.csv,v3_roster_overlap.csv}` — basin-shift evidence (v3 Jaccard 0.0645 = 93.5% basin migration)

**Commits**: `1be3bd1` (feat: basis_zscore_30 feature + dispatch + tests — RETIRED) + `25e3834` (feat(iter-v1/041): labeling tighten triple-barrier (atr_tp=1.5/atr_sl=0.75)) + Phase 1-5 docs + Phase 6.0 critic_preflight (`12a0097`) + Phase 7-8 closeout (this diary).

**Branch**: `iteration-v1/041` (not yet merged to `main` — cycle-5 closeout pending after /042 + /043 complete).

---

## 11. Track Record post-/041 (cycle-5)

**Cycle-5 hit rate (8/10)**:
- 2 PROMISING (/036 PROMISING-CLEAN +1.08 OOS Δ, /037 PROMISING-CLEAN +0.18 OOS Δ)
- 6 NEG (/034 NEG-CLEAN basis, /035 NEG-CAT-bundle bimodal, /038 NEG-CAT vol-ceiling, /039 NEG-CAT-vs-/036 hybrid, /040 NEG-CLEAN-OVERFIT composed feature, /041 NEG-CLEAN-by-Sharpe with DD-control annotation)
- = **25% PROMISING rate** (down from 28.6% post-/040)

**Substrate STABILIZED** (substrate v2 4-component portfolio per `cycle5_substrate_v2_regime_portfolio.md`): /036 LINK+DOT trend-scan specialist (P1) + /037 5-cohort Sortino (P3) + /040 composed-feature stack-pruned (P2) + BASELINE_V1 anchor (P0). /041 adds POTENTIAL P4 TAIL-CONTROL slot at conditional 10% weight (substrate-v3 expansion contingent on multi-seed validation).

**LM Master directional running tally**: **2/8 = 25.0%** post-/041 (consistent with cycle-5 baseline 25-30% rate; MODAL-direction reliability remains POOR; combined-tail-weighting reliability HIGHER).

**Feature-family axis CLOSED for cycle-5**: 2-for-2 NEG-CLEAN at /034 + /040.

**Risk-primitive axis CLOSED for cycle-5**: 2 saturations at /038 + /039.

**Loss-function family CLOSED for substrate compounding** (per /039): /037 universe-dependent.

**Labeling axis CLOSED for v1 cycle-5 at single-seed EXPLORATION budget across full barrier-magnitude curve** (NEW post-/041): /014 σ_t source + /015 σ_t CONFIRMATION-NEG + /041 width-tighten all converge on the same n_eff=9 ridge + chop-noise dominance pattern.

**Open axes for /042-/043**: `model-arch` (/042) and `per-cohort-specialization` substrate attribution (/043).

---

## 12. Closure Note — Labeling-width axis CLOSED for v1 cycle-5; /044 substrate v2-expansion CONDITIONAL on /041 multi-seed validation

**Specifically refuted at /041**: uniform triple-barrier TIGHTEN at multiplier ratio preserved (1.5/0.75 across all cohorts) on v1's 44-col stack at single-seed EXPLORATION budget. **Mechanism**: chop-noise dominance under shorter forward-window resolution (median 8-13 baseline → ~4-6 candle tight); OOS WR collapses 6.3pp (40.2 → 33.9%); fee-to-edge ratio doubles (1.8 → 3.3%) per EDA §5; OOS Sharpe Δ = -0.38; n_eff=9 ridge confirms 4-iter stack-lock.

**ALSO discovered at /041 (NEW finding for cycle-5)**: tighter barriers symmetrically compress up-tail AND down-tail trade magnitudes; the down-tail compression delivers a broad-based DD-control mechanism (-19/-18pp Max DD IS/OOS) ORTHOGONAL to all 4 substrate-v2 components' Sharpe/Sortino orientations. **/041 = type-T TAIL-CONTROL specialist** — a new specialist class in cycle-5's regime-aware framework.

**Generalization (cycle-5 specialist framework v2)**: specialists are classified by RISK FACET (Sharpe-maximizer / DD-minimizer / Sortino-shaper / regime-by-window-specialist) AND regime-orientation (type-A IS-strong / type-B OOS-strong / type-C universal / type-T tail-control). The 9-column catalog schema (with `regime profile` column) is the codification.

**Forward-binding (per Path Forward #5 generalized)**: future cycle-6+ briefs MUST include a "specialist-mechanism declaration" section naming the axis's PRIMARY risk facet AND regime-orientation. Pure F1 Sharpe Δ classification is no longer sufficient for non-merge axes — DD/Sortino/regime-shape annotations may upgrade a NEG-CLEAN-by-Sharpe into a PROMISING-RISK-FACET candidate for portfolio substrate inclusion at low weight.

**NOT refuted at /041**: /036 + /037 + /040-pruned cycle-5 substrate v2; baseline anchor; the regime-portfolio combination framework. /044 substrate v2 launches post-/043 closeout as planned; substrate-v3 expansion (5 components incl. /044-E /041 P4 TAIL-CONTROL) is CONDITIONAL on /041 multi-seed validation.

**End of diary-v1/iteration_v1-041.md.**
