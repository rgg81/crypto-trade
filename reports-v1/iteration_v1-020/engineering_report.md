# iter-v1/020 — Phase 7 Engineering Report (RETROSPECTIVE)

**Iteration**: iter-v1/020 (cycle-3 EXPLORATION #5 of 10; THIRD per-cohort EXPLORATION under USER STRATEGIC PIVOT; BTC IS-NEG / OOS-POS asymmetric-rotation structural prior cohort)
**Branch**: `iteration-v1/020` from `iter-v1/019` closeout (tag `v0.v1-019`)
**HEAD**: `ebdc4a6` (QR Phases 1-4 + LM Master Phase 4.5 `9c6c32f` → QE implementation + Phase 6 backtest → LM Master Phase 7.4 + Critic Phase 7.5 `ebdc4a6`)
**Wall-clock**: ~25 min (well inside 2h cap; identical scale to /018 and /019)
**Verdict**: **EXPLORATION-NEGATIVE — Catastrophic-NEGATIVE** per Section 8 Row 6 (F1 OOS Sharpe Δ -0.86 ≤ -0.55); **H_INTRINSIC REFUTED** at training-time granularity; BTC's OOS positive rotation was POOL-CONFERRED, NOT intrinsic.
**Reports**: `reports-v1/iteration_v1-020/{in_sample,out_of_sample}/`
**Critic review**: `briefs-v1/iteration_v1-020/review.md` (HEAD `ebdc4a6`)
**LM Master pre/post**: `briefs-v1/iteration_v1-020/lgbm_advisor.md` (Phase 4.5 advisory + Phase 7.4 post-mortem)

This report is written RETROSPECTIVELY at Phase 8 closeout per Critic Phase 7.5 Recommendation #1 — Phase 6 did not emit it inline. Zero backtest re-run; all numbers drawn from committed CSVs.

---

## 1. Headline Metrics

| Metric | IS | OOS | OOS / IS Ratio |
|---|---|---|---|
| **Sharpe (annualized daily)** | **−0.5914** | **−0.5566** | 0.9413 |
| Sortino | −0.3485 | −0.3251 | 0.9329 |
| Win rate | 41.0% | **45.3%** | 1.1049 |
| Profit factor | 0.7675 | 0.8146 | 1.0614 |
| Max drawdown | 38.29% | 18.21% | 0.4756 |
| Trades | 122 | 53 | 0.4344 |
| Total Net PnL (%) | **−28.93** | **−10.17** | 0.3517 |
| Calmar ratio | 0.7557 | 0.5588 | 0.7394 |
| **PSR_monthly_vs_0** | 0.168886 | **0.301056** | 1.7826 |
| PSR_monthly_vs_1 | 0.002386 | 0.037855 | 15.87 |
| PSR_daily_vs_0 | 0.160580 | 0.275884 | 1.7180 |
| DSR | −38.06 | −40.07 | informational only (EXPLORATION-mode artifact) |
| n_eff (global PCA) | 9 | 9 | — |
| n_eff_per_cell_median | 9 | 9 | matches /018 + /019 cohort-isolation reference; matches LM Master point estimate 9 |
| r5_fire_rate | 0.0 | 0.0 | R5 disabled |

**BTC-in-pool anchor (F1/F3 baseline per `feedback_v1_per_cohort_exploration_strategy.md` + brief Section 4)**:
- IS net_pnl_pct: **−37.28%** (113 IS trades) — from `reports-v1/iteration_v1-baseline/in_sample/per_symbol.csv` (BTC row)
- OOS net_pnl_pct: **+33.17%** (35 OOS trades) — from `reports-v1/iteration_v1-baseline/out_of_sample/per_symbol.csv` (BTC row)
- IS monthly Sharpe proxy: **≈ +0.30** (from brief Section 4)
- OOS monthly Sharpe proxy: **≈ +0.30** (from brief Section 4 baseline EDA)

Per anchor-frame audit at Critic Phase 7.5 (4 frames all land Catastrophic on net_pnl monthly-sum / annualized-daily-Sharpe; 3 of 4 Catastrophic on annualized-daily-Sharpe vs reconstructed proxy):

| Frame | /020 BTC-only | BTC-in-pool baseline | Δ | Band |
|---|---|---|---|---|
| **net_pnl trade-sum** | −23.25% | +9.93%* | −33.18 pp | NEGATIVE |
| **net_pnl monthly-sum** | −10.17% (OOS) | +33.17% | **−43.34 pp** | **Catastrophic** |
| **annualized-daily-Sharpe vs brief proxy +0.30** | −0.5566 | +0.30 | **−0.86** | **Catastrophic** |
| **annualized-daily-Sharpe vs reconstructed proxy +1.0** | −0.5566 | +1.00 | **−1.56** | **Catastrophic** |

*baseline BTC-in-pool OOS net_pnl trade-sum approximation from `analysis/iteration_v1-020/btc_oos_trajectory.csv`; difference from monthly-sum reflects within-month re-weighting.

→ **NEGATIVE-CATASTROPHIC** verdict-cell (Section 8 row 6). F1 OOS Sharpe Δ −0.86 ≤ −0.55 threshold fires. Robust across all 4 frames.

## 2. Per-Symbol PnL Attribution

### In-Sample (Model H — BTC-only dispatch)

| Symbol | Trades | Wins | WR | Net PnL % | Avg PnL % | % of Total IS PnL |
|---|---|---|---|---|---|---|
| **BTCUSDT** | **122** | **50** | **41.0%** | **−23.25** | **−0.19** | **100.00%** |

### Out-of-Sample (Model H — BTC-only dispatch)

| Symbol | Trades | Wins | WR | Net PnL % | Avg PnL % | % of Total OOS PnL |
|---|---|---|---|---|---|---|
| **BTCUSDT** | **53** | **24** | **45.3%** | **+0.99** | **+0.019** | **100.00%** |

**F-AXIS-MECHANISM #1 binary PASS**: per_symbol.csv contains 100% BTCUSDT both IS and OOS. Model H via `V1_ITER020_UNIVERSE = (BTCUSDT,)` and `set(symbols)==set(V1_ITER020_UNIVERSE)` guard. Zero spillover from other dispatch branches (Model A/C/D/E/F/G all DROPPED).

Despite OOS net_pnl_pct technically POSITIVE (+0.99%), the OOS Sharpe (−0.5566) is NEGATIVE because the OOS PnL distribution has high monthly variance with multiple large drawdown months (-11.65, -10.89, -4.26, -3.11) crowding the small wins. The net +0.99% is dwarfed by per-trade variance.

## 3. F-AXIS #3 IS_H1 Regime-Binding Computation (Critic INDETERMINATE → resolved here)

Per brief Section 0.4 + brief Section 4 F-AXIS #3 row: pre-registered band IS_H1 net_pnl ∈ [−45%, −15%] (baseline IS_H1 = −36.01% across 15 months 2022 to mid-2024, anchor ± 15pp).

Computed from `reports-v1/iteration_v1-020/in_sample/monthly_pnl.csv`, partitioned at month 15 per baseline-aligned definition (first 15 chronological IS months = 2022-01 through 2023-04):

### IS_H1 (15 months — 2022-01 to 2023-04)

| month | net_pnl_pct | trade_count |
|---|---|---|
| 2022-01 | +4.7664 | 2 |
| 2022-02 | −13.7351 | 3 |
| 2022-03 | +0.4681 | 3 |
| 2022-04 | +5.9319 | 1 |
| 2022-05 | −4.0107 | 1 |
| 2022-06 | +9.5648 | 3 |
| 2022-07 | −14.3258 | 3 |
| 2022-08 | −1.1432 | 4 |
| 2022-09 | +3.3630 | 4 |
| 2022-10 | +4.5581 | 6 |
| 2022-11 | −3.7034 | 3 |
| 2023-01 | −6.0922 | 5 |
| 2023-02 | −2.9626 | 4 |
| 2023-03 | −4.3895 | 4 |
| 2023-04 | −0.2430 | 4 |
| **IS_H1 total** | **−21.95%** | **50** |

Positive months 6/15 (40.0%); negative months 9/15 (60.0%); mean = **−1.46%/month**.

### IS_H2 (17 months — 2023-05 to 2025-02)

| month | net_pnl_pct | trade_count |
|---|---|---|
| 2023-05 | +2.5718 | 6 |
| 2023-06 | +6.2729 | 4 |
| 2023-07 | +0.3043 | 4 |
| 2023-08 | −1.0826 | 4 |
| 2023-09 | −3.4183 | 4 |
| 2023-10 | −0.0433 | 5 |
| 2023-11 | −1.7433 | 3 |
| 2023-12 | +0.8385 | 6 |
| 2024-01 | +4.6015 | 7 |
| 2024-02 | +0.0887 | 4 |
| 2024-04 | −13.1233 | 4 |
| 2024-05 | +0.8556 | 5 |
| 2024-06 | −0.5952 | 4 |
| 2024-07 | −3.5437 | 6 |
| 2024-08 | +2.1365 | 1 |
| 2024-09 | +4.9673 | 2 |
| 2025-02 | −6.0650 | 3 |
| **IS_H2 total** | **−6.98%** | **72** |

Positive months 9/17 (52.9%); negative months 8/17 (47.1%); mean = **−0.41%/month**.

### F-AXIS #3 verdict

| F-AXIS #3 band | Threshold | IS_H1 observed | Status |
|---|---|---|---|
| PASS (regime-preserved) | IS_H1 ∈ [−45%, −15%] | **−21.95%** | **PASS / BORDERLINE PASS** (inside band, near upper boundary −15%) |
| DISSOLVED (H_INTRINSIC partially false) | IS_H1 ≥ −10% | — | not triggered |
| AMPLIFIED (cohort isolation harmful) | IS_H1 ≤ −60% | — | not triggered |

**F-AXIS #3 status: BORDERLINE PASS** (observed −21.95% inside band but only −6.95pp from upper PASS boundary −15%). Critic's manual estimate (-19.4%) was within reading-noise of the true value (-21.95%) — both inside band.

**Mechanism interpretation**: BTC-only Optuna trajectory DID partially reduce IS_H1 catastrophic magnitude (from baseline −36.01% to BTC-only −21.95%, Δ +14.06pp) but did NOT dissolve it. IS_H1 catastrophic regime-bound character is preserved at single-cohort isolation. **The IS catastrophic regime-bound finding from Section 0.4 EDA holds** — but it is NOT the load-bearing constraint that drove /020's Catastrophic verdict. The Catastrophic verdict is driven by **OOS Sharpe collapse from +0.30 proxy to −0.5566** at F1 — a 0.86 standard-deviation drop **in the OPPOSITE direction** from F-AXIS #3.

This is the key structural finding (LM Master Phase 7.4 §3): F-AXIS #3 PASS + F1 Catastrophic-NEGATIVE = IS preserved its regime profile, but OOS LOST its positive rotation. The OOS positive rotation was POOL-CONFERRED, not intrinsic.

## 4. F-AXIS-MECHANISM Compound Verdict

| Sub-check | Status | Detail |
|---|---|---|
| **#1 Dispatch correctness** | **PASS** | per_symbol.csv 100% BTCUSDT IS+OOS; trades.csv 175 BTC rows / 0 other |
| **#2 Trade-count band** | **PASS** | IS 122 ∈ [70, 150] QR + ∈ [79, 147] LM tighter sub-band; OOS 53 ∈ [25, 55] QR + outside LM tighter [25, 46] **BREACH-HIGH +7 INFORMATIONAL** (LM Master Phase 7.4 §1 notes BREACH inside QR's blocking band → does NOT trigger F-AXIS #2 BREACH) |
| **#3 IS_H1 catastrophic preservation (regime-binding)** | **BORDERLINE PASS** | IS_H1 = −21.95% inside band [−45%, −15%] (near upper boundary); REGIME-BOUND character preserved but Δ +14.06pp vs baseline IS_H1 = −36.01% |
| **#4 n_eff_per_cell band (informational)** | **PASS** | observed 9 inside LM Master point estimate [7, 10]; matches /018 LINK-only (9); methodology calibration accurate |

**Compound: PASS on mechanism**. All load-bearing dispatch + trade-count + regime-preservation checks pass; F1 OOS Sharpe Δ at −0.86 fires Section 8 Row 6 Catastrophic verdict despite F-AXIS PASS.

## 5. Critic + LM Master Convergent Verdict

Both Critic Phase 7.5 (`review.md` HEAD `ebdc4a6`) and LM Master Phase 7.4 (`lgbm_advisor.md`) converge on **EXPLORATION-NEGATIVE Catastrophic-NEGATIVE** (Section 8 Row 6):

| Item | Critic | LM Master |
|---|---|---|
| Verdict cell | NEGATIVE-CATASTROPHIC (Section 8 Row 6; robust across 4 anchor frames) | NEGATIVE-CATASTROPHIC (2% tail materialized — modal INERT 60% REFUTED) |
| F1 OOS Δ | −0.86 ≤ −0.55 threshold | −0.86 observed; predicted modal [0, +0.10]; tail [−0.55, −0.20] negative; CATASTROPHIC ≤ −0.55 at 2% |
| Mechanism | LM Master Phase 7.4 §3 STRUCTURAL FINDING ADOPTED: H_INTRINSIC REFUTED — pool-conferred OOS positive rotation via 3 channels | 3 specific pool-conferred channels: (a) shared feature normalization (NATR distribution narrower BTC-alone), (b) label-timing co-location (joint Optuna IS loss surface), (c) `abs_pnl` sample weighting (BTC large-magnitude downweighted in pool, NOT in isolation) |
| Jaccard test | 0.084 combined → NEW signal source NOT PROMISING-MECHANICAL | 0.084 confirmed (IS 0.098 / OOS 0.048); REFUTES LM §4 [0.10, 0.25] prediction; basin relocation |
| /021 next-axis | Path Forward #1 (methodology pivot) preferred | LM Master §5 hybrid Option C + Option B preferred (matches Critic Path Forward #1) |
| /027 bundle role for BTC | enter via POOL (Model A), NOT BTC-only Model H | enter via POOL (Model A); BTC-only Model H unsuitable |

**Track records updated:**
- **Critic**: 8 of 9 mandatory checks PASS (Check 3 EXPLORATION-edge FAIL-informational does NOT trigger BLOCK per §5.1 rule). Verdict ROBUST across 4 anchor frames.
- **LM Master**: 0/3 directional Phase 4.5 calls (INERT-no-effect modal 40% REFUTED; Jaccard [0.10, 0.25] REFUTED; BTC-only DIVERSIFICATION role VINDICATED in direction but understated magnitude — actual NEGATIVE additive); 1/1 methodology call (n_eff = 9 PASS); 1/1 alternative-branch pre-registration utility (§4 Jaccard ≈ 0.04 alternative branch realized).

## 6. EDA Prediction Calibration — H_POOL_ANCHOR REFUTATION was MISLEADING

The Phase 2 EDA at `analysis/iteration_v1-020/btc_pool_anchor_summary.csv` projected:

| EDA prediction | Observed | Calibration |
|---|---|---|
| Pearson(BTC, ETH) monthly net_pnl = −0.0220 | (independent test confirmed) | TRUE at monthly aggregate — but MISLEADING at training-time granularity |
| Spearman(BTC, ETH) monthly net_pnl = +0.0227 | (independent test confirmed) | TRUE at monthly aggregate — but MISLEADING |
| Same-sign months 51.7% | (coin-flip rate confirmed) | TRUE — but at the WRONG resolution |
| H_POOL_ANCHOR REFUTED → modal INERT 60% | NEGATIVE-CATASTROPHIC (2% tail) | **EDA prediction REFUTED** at training-time |
| Modal verdict-class: INERT (small Δ, OOS preserved) | OOS Sharpe Δ = −0.86 | **REFUTED** by 0.86σ — modal MISSED, tail materialized |

**Critical structural finding (LM Master Phase 7.4 §3 ADOPTED)**: monthly aggregate ρ ≈ −0.022 was a **methodological false-negative** for training-time pool dependence. Three pool-conferred channels carry BTC's OOS positive rotation, none visible at monthly Pearson:

1. **Shared feature normalization at training time**: rolling 50-bar features compute per-symbol but Optuna trial selection on COMBINED IS labels picks splits favoring features whose value distribution is regular across all 5 cohorts. BTC-alone trains on BTC's narrower NATR distribution and Optuna lands in a different basin.
2. **Label-timing co-location**: training months containing BTC labels also contain ETH/LINK/LTC/DOT labels — Optuna's IS loss surface is integrated over all of them. Best-trial selection optimizes for JOINT loss; BTC-conditional optimum within that joint solution differs from BTC-alone optimum.
3. **Sample weighting (abs_pnl)**: weighted by |net_pnl_pct|, BTC's large-magnitude trades are downweighted RELATIVE to LINK/LTC vol-amplified trades — BTC-only retraining REMOVES this implicit downweighting and changes the implicit risk-distribution Optuna sees.

**Corrected mental model**: cohort isolation success requires either (a) **independent positive prior at pool level** (LINK case — /018, both IS and OOS positive in pool) OR (b) **ORTHOGONAL mechanism added** on top of isolation (ETH+counter-trend-gate case — /019, gate is the load-bearing mechanism not isolation). Pool-anchor refutation at monthly aggregate is NEITHER sufficient NOR necessary for isolation viability.

## 7. Jaccard Roster Comparison (computed in §2 of LM Master Phase 7.4)

Computed from `reports-v1/iteration_v1-020/{in,out_of}_sample/trades.csv` and `reports-v1/iteration_v1-baseline/{in,out_of}_sample/trades.csv` filtered `symbol==BTCUSDT`, keyed on `open_time`:

| Scope | /020 BTC-only | Baseline BTC-in-pool | Overlap | Union | **Jaccard** |
|---|---|---|---|---|---|
| IS only | 122 trades | 113 trades | 21 | 214 | **0.0981** |
| OOS only | 53 trades | 35 trades | 4 | 84 | **0.0476** |
| **IS+OOS combined** | **175** | **148** | **25** | **298** | **0.0839** |

**Verdict**: Jaccard 0.084 combined << 0.50 threshold → **NEW SIGNAL SOURCE (NOT PROMISING-MECHANICAL)** but with NEGATIVE Sharpe Δ — i.e., basin relocation took /020 into a worse region of feature space. /020 retained only 4 of baseline's 35 OOS BTC trades (containment 11.4%); the other 49 OOS trades are net-new from BTC-only Optuna basin. **The new basin produces NET-NEGATIVE OOS Sharpe (−0.5566) — the pool-trained basin's OOS positive (+33.17%) was a structurally adverse target for BTC-alone training.**

LM Master Phase 4.5 §4 had pre-registered the alternative branch interpretation: "If observed Jaccard ≈ 0.04 (matching /018+/019): pool independence claim is at higher-than-monthly granularity — within-month label timing IS coupling BTC+ETH. Surprise outcome." That pre-registration is the **only Phase 4.5 prediction that earned utility** at Phase 7.4.

## 8. BTC Structural Prior — Pre/Post Comparison

BTC IS/OOS PnL across baseline + /014/015/016/017 + /020 (from brief Section 0.3 + `reports-v1/iteration_v1-020/per_symbol.csv`):

| Iter | BTC IS trades | BTC IS WR | BTC IS net_pnl_pct | BTC OOS trades | BTC OOS WR | BTC OOS net_pnl_pct |
|---|---|---|---|---|---|---|
| baseline | 113 | 33.6% | **−37.28%** | 35 | 45.7% | **+33.17%** |
| /014 | 120 | 37.5% | −24.25% | 41 | 43.9% | +5.70% |
| /015 | 114 | 39.5% | −0.65% | 44 | 29.5% | **−7.18%** |
| /016 | 131 | 38.2% | −34.60% | 61 | 34.4% | −8.31% |
| /017 | 129 | 31.0% | **−93.81%** | 52 | 36.5% | +15.11% |
| **/020 (BTC-only)** | **122** | **41.0%** | **−23.25%** | **53** | **45.3%** | **+0.99%** |

**Structural finding**: BTC OOS positive (+33.17%) is **DISSOLVABLE** under cohort isolation alone — the pool-conferred positive rotation collapses (+33.17% → +0.99%, Δ −32.18 pp on net_pnl) at Model H BTC-only retraining. The IS catastrophic regime-bound finding from Section 0.4 is PARTIALLY relaxed (−37.28% → −23.25%, Δ +14.03pp) but the OOS collapse is the dominant effect.

**Contrast with LINK and ETH**:
- **LINK** (/018, structurally-positive prior cohort): isolation PRESERVED OOS positive (+52.16% baseline → +53.80% /018); pool was NOT load-bearing for LINK.
- **ETH** (/019, structurally-negative prior cohort + gate): isolation PLUS orthogonal mechanism (BTC-trend gate) DISSOLVED OOS negative (+2.75% baseline → +32.65% /019); the gate was the load-bearing mechanism.
- **BTC** (/020, asymmetric-rotation cohort, NO knob): isolation ALONE LOST pool-conferred OOS positive (+33.17% baseline → +0.99% /020). The pool WAS load-bearing for BTC.

This three-cohort comparison establishes the cohort-isolation viability principle: **isolation succeeds only when the pool was NOT the source of the positive prior**.

## 9. Monthly OOS PnL Distribution

| Month | n | net_pnl_pct |
|---|---|---|
| 2025-03 | 1 | +4.88% |
| 2025-04 | 3 | **−11.65%** |
| 2025-05 | 4 | −4.26% |
| 2025-06 | 2 | +0.64% |
| 2025-07 | 1 | +3.20% |
| 2025-08 | 7 | **+7.86%** |
| 2025-09 | 5 | −1.06% |
| 2025-10 | 5 | +3.58% |
| 2025-11 | 2 | +0.69% |
| 2025-12 | 4 | −3.11% |
| 2026-01 | 3 | +0.36% |
| 2026-02 | 4 | **−10.89%** |
| 2026-03 | 6 | −0.20% |
| 2026-04 | 1 | −1.06% |
| 2026-05 | 5 | +0.85% |

Positive months 8/15 (53%); negative months 7/15 (47%); mean monthly OOS PnL = **−0.68%**; std ≈ 5.1%. Three negative-double-digit months (2025-04 −11.65%, 2026-02 −10.89%) + multiple small-magnitude drag months dominate the Sharpe denominator. PSR_monthly_vs_0 = 0.301 (below PROMISING-INERT floor 0.40, above Catastrophic floor 0.10) reflects this mixed-distribution structure.

## 10. Critic Recommendations to QR (Phase 8 actions)

Verbatim from `briefs-v1/iteration_v1-020/review.md` §"Recommendations to QR":

1. **Engineering report timing contract VIOLATED** (process-level; NOT verdict change at /020 but mandatory fix for /021). `briefs-v1/iteration_v1-020/engineering_report.md` was MISSING at Phase 7.5 dispatch. Per brief Section 10.4 + /019 Critic Rec #1, QE was bound to publish engineering_report.md BEFORE Phase 7.5 dispatch. **Phase 8 closeout addresses retrospectively (THIS REPORT)**. /021 must either (a) re-enforce the timing contract at orchestrator dispatch OR (b) downgrade to "advisory" with documented justification.

2. **Anchor proxy formalization** (load-bearing for cycle-3 verdict-cell calibration). Brief Section 4 F1 uses a monthly Sharpe PROXY (+0.30) while comparison.csv reports annualized daily Sharpe. /018 and /019 implicitly used the same mixed-frame Δ rule. Recommend /027 CONFIRMATION brief pre-compute BTC-in-pool annualized-daily-Sharpe directly (single deterministic number, no proxy) and lock the anchor frame to comparison.csv "sharpe" semantics. Forward-looking; /020 verdict ROBUST under all frames.

3. **LM Master Phase 7.4 §3 structural finding adoption** (binding for /021 axis selection). H_INTRINSIC was REFUTED via 3 specific pool-conferred channels. Cycle-3 cohort-isolation evidence base: LINK (independent positive prior succeeds) + ETH (negative prior dissolved by GATE not isolation) + BTC (positive OOS rotation LOST at isolation — POOL-CONFERRED). Future per-cohort EXPLORATIONs without methodology pivot or orthogonal mechanism are predicted to repeat the BTC pattern. **/021 MUST EITHER add methodology diagnostic OR orthogonal mechanism on top of isolation.**

All three carry process implications. Items 1 and 2 carry forward as feedback rule updates (orchestrator Phase 6 contract; anchor proxy lock). Item 3 propagates to /021 brief design.

## 11. /027 Bundle Composition Update

Per LM Master Phase 7.4 §5 + Critic Phase 7.5 Path Forward + /019 closeout LESSON #4:

| Specialist | Status after /020 | Single-seed Δ | /027 multi-seed regression target |
|---|---|---|---|
| LINK-only /018 | PROMISING-INERT favorable (VALIDATED — LOAD-BEARING from /018 closeout) | +0.16 | **+0.80** |
| ETH-only + BTC-trend gate /019 | PROMISING (VALIDATED — LOAD-BEARING from /019 closeout) | +0.65 | **+0.50** |
| **BTC-only /020** | **NEGATIVE Catastrophic (THIS ITERATION; CLOSED for isolation-without-gate)** | **−0.86** | **EXCLUDED** |
| LTC-only /021+ | PENDING (depends on /021 methodology diagnostic outcome) | — | — |
| DOT-only /022+ | PENDING | — | — |
| Pooled cohorts /023-/026 | PENDING | — | — |

**Current /027 bundle composition**: **2/4-6 ingredients staged (LINK-only +0.80 + ETH+gate +0.50)** — UNCHANGED from /019 closeout. /020 NEGATIVE means BTC enters /027 **IN POOL via Model A** NOT in isolation. Projected portfolio Sharpe lift +0.85 to +1.05 with 2 specialists (LINK + ETH+gate) + BTC-IN-POOL anchor; cross-correlation < 0.40 still required (Critic /019 Rec #3 pre-validation).

## 12. USER STRATEGIC PIVOT — Continued Validation (REFINED Interpretation)

Cycle-3 verdict distribution after /020:

| Iter | Methodology | Verdict | OOS Δ vs anchor |
|---|---|---|---|
| /016 | global axis on pooled (sample-weighting uniform) | NEGATIVE catastrophic | −1.67 |
| /017 | global axis on pooled (universe +SOL) | NEGATIVE anti-direction-INERT | −0.09 |
| /018 | per-cohort specialization LINK-only | PROMISING favorable-INERT | +0.16 |
| /019 | per-cohort specialization ETH-only + BTC-trend gate | PROMISING | +0.65 |
| **/020** | **per-cohort specialization BTC-only (NO knob, pure isolation)** | **NEGATIVE Catastrophic** | **−0.86** |

**Per-cohort methodology has now produced**:
- 2 PROMISING (LINK with positive prior; ETH with negative prior + orthogonal gate)
- 1 NEGATIVE Catastrophic (BTC with asymmetric-rotation prior + NO knob)

Global-pooled axes: 2 NEGATIVE / 0 PROMISING.

**The refined view** (per LM Master Phase 7.4 §3): per-cohort isolation success is NOT methodology-class-universal. It depends on:
1. The cohort's structural prior independence from pool (LINK has it; BTC does NOT).
2. The presence of an orthogonal mechanism added when isolation alone is insufficient (ETH+gate).

USER STRATEGIC PIVOT is REFINED not REFUTED: per-cohort specialization is a viable methodology *with cohort-prior screening* and *orthogonal mechanism addition where required*. Future per-cohort EXPLORATIONs need a training-time pool-anchor diagnostic to predict isolation viability BEFORE wall-clock spend.

## 13. Phase 7 Closeout — Items for Phase 8

1. **Diary** (`diary-v1/iteration_v1-020.md`): frontmatter verdict `EXPLORATION-NEGATIVE` subtype `Catastrophic`, axis family `per-cohort-specialization-BTC` (NEW 11th catalog family), cohort identifier BTC, specialization dimension = NONE (pure isolation, NO gate, NO new feature, NO new labeling).

2. **Catalog row append** at `briefs-v1/exploration_catalog.md` Ledger as cycle-3 #5/10.

3. **Tag** `v0.v1-020` after Phase 8 closeout commit.

4. **/021 axis advances per Critic Phase 7.5 Path Forward #1 + LM Master Phase 7.4 §5 convergent hybrid Option C + B**: methodology pivot — (i) add `_write_feature_importance` per /019 §6 outstanding gap; (ii) add training-time pool-anchor diagnostic (per-fold Optuna best-trial parameter delta between BTC-in-pool Model A and BTC-only Model H at SAME seed=42).

5. **Brief Section 13 self-check addendum** with observed Phase 7+8 outcomes (pre-registered template self-check).

6. **Memory update — DURABLE LESSON**: per-cohort isolation success requires (a) independent positive prior at pool level OR (b) orthogonal mechanism added — NOT pool-anchor-refutation at monthly aggregate. Document at `feedback_v1_h_intrinsic_refuted_at_btc.md`.

## 14. Files & Commits on Branch

- Branch: `iteration-v1/020` from `iter-v1/019` closeout (tag `v0.v1-019`)
- HEAD at QR Phase 1-4 + LM Master Phase 4.5: `9c6c32f`
- HEAD at brief Section 3.4 LM Master responses + final brief: (intermediate commits between `9c6c32f` and Phase 6)
- HEAD at QE Phase 5.5 + dispatch implementation: (Phase 6 implementation commit)
- HEAD at Critic Phase 6.0 PASS: (Phase 6.0 pre-flight commit)
- HEAD at backtest dispatch: (Phase 6 backtest run commit — comparison.csv + reports artifacts in `reports-v1/iteration_v1-020/`)
- HEAD at LM Master Phase 7.4 post-mortem: (Phase 7.4 commit)
- HEAD at Critic Phase 7.5 review (EXPLORATION-NEGATIVE Catastrophic): `ebdc4a6`
- HEAD at engineering report (THIS COMMIT — retrospective at Phase 8 per Critic Rec #1): TBD
- HEAD at Phase 7 evaluation memo (next commit): TBD
- HEAD at Phase 8 diary closeout (subsequent commit): TBD
- Reports artifacts in `reports-v1/iteration_v1-020/`

**Trunk merge**: NONE. EXPLORATION-NEGATIVE Catastrophic does NOT update BASELINE_V1.md. BTC-only Model H specialist EXCLUDED from /027 substrate; BTC enters /027 IN POOL via Model A (no architectural change vs baseline for BTC). NO src/ trunk merge from this iteration.

**Tag**: `v0.v1-020` to be applied after Phase 8 diary commit.
