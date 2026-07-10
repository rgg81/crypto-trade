# EXPLORATION-007 — Engineering Report (all-21-phase equal-weight ENSEMBLE of the frozen L1)

- **Track:** baseline-BLIND top-20 L/S portfolio (worktree `quant-portfolio-blind`)
- **Branch:** `quant-portfolio-blind`
- **What ran:** the SINGLE frozen ensemble pass pre-registered in
  `briefs-portfolio-blind/EXPLORATION-007.md` — equal-weight (1/21) over ALL 21 weekly-rebal phase
  offsets of the byte-frozen L1. No phase selected, no parameter tuned, no post-hoc re-run.
- **IS-only. OOS sealed at `OOS_CUTOFF = 2025-03-24`.** Panel hard-sliced with `slice_is()` at the top
  of the script; every number below is on candles `open_time < 2025-03-24`. Verified at runtime:
  `pis.grid_ms.max() < OOS_CUTOFF_MS`. `CONFIRMATION-005.md` not read; no baseline / `PROTOCOL-L1-
  FORWARD` / `paper-l1` forward artifact read.
- **Single source of truth:** `run_l1` / `run_v0` / `trim_panel` (+ frozen L1 params) from
  `blind_paper_l1`; `leg_attribution` / `bucket_agg` / `top10_concentration` / `worst_calendar_month`
  / `CRASH_MONTHS` / `fmt_years` from `blind_exploration_006`; `MANIA_MONTHS_FROZEN` from
  `blind_mania_rule`; `slice_is` from `blind_sanity_lowvol`; `_metrics` / `run_backtest` from
  `blind_engine`. No engine code changed.
- **Artifacts:**
  - `analysis/portfolio/blind_exploration_007.py` (new — 84-backtest ensemble matrix + tables)
  - `tests/test_blind_engine.py` (+2 tests: ensemble alignment/common-mask; analytic-2x drift; 53 total)
- **No commits (per task instruction).**
- **ENGINEER SCOPE:** observed values only. Gate PASS/FAIL, the §5.1 SUCCESS/PARTIAL/FAIL tier, and the
  §5.3 forward-switch recommendation are the QR's / Critic's Phase-7 calls. Every gate-relevant number
  below is shown with its frozen threshold ALONGSIDE; the verdict column is deferred.

---

## 1. Test suite: 53/53 green

`uv run pytest tests/test_blind_engine.py -q` → **53 passed in 15.55s**. Lint + format clean
(`ruff check` → "All checks passed"; `ruff format` applied). 51 pre-existing tests untouched.

- **NEW `test_exploration_007_ensemble_alignment_and_common_mask`** — pure-logic (no backtest): pins
  that `map_to_grid` places tranche-index `j` on ORIGINAL index `p+j` (aligned by `grid_ms`, pre-`p`
  NaN) and that `common_metric_mask`'s first-True equals `warmup + max_p` (the generalized index-83
  arithmetic). **PASS.**
- **NEW `test_exploration_007_analytic_2x_twin_fixed_share_drift`** — on a REAL L1 tranche: the
  analytic 2x twin is bit-exact at the first cost-bearing rebal candle, drifts non-vacuously (≤ 5e-4)
  thereafter, and moves Sharpe ≤ 5e-3. Pins the true behavior (see §9 anomaly #1). **PASS.**

---

## 2. Parity guards (brief §7 — ABORT on drift) — PASS

Tranche `p=0` (Wed@00h, native phase) reproduces the frozen candidate; full sweep ties row-for-row.

| check | observed | target | tol | result |
|---|---|---|---|---|
| L1 Sharpe (p0) | **+1.1638** | +1.1638 | ±0.005 | PASS |
| V0 Sharpe (p0) | **+0.9134** | +0.9134 | ±0.005 | PASS |
| L1 maxDD (p0) | **−28.58%** | −28.58% | ±1pp | PASS |
| L1 turnover (p0) | **50.14x** | 50.10 | ±2 | PASS |

- **Full 21-row sweep reproduction** (all tranches' warmup=63 L1/V0 Sharpe + maxDD vs committed
  `paper-l1/phase_sweep_is.csv`): **max err 1.28e-15 (≤1e-6)** — ties the ensemble script to the sweep.
- **Per-tranche leg reconciliation** `long_px + short_px + net_fund − tcost ≡ rets`: **max 2.78e-17**
  across all 42 tranche runs (≤1e-12). Ensemble leg recon (by linearity): L1 3.12e-17, V0 2.78e-17.
- Panel: **5727 IS candles, 747 coins, 2020-01-01 .. 2025-03-23.**

**Common warmup=63 slice.** Each tranche `p` is warm+finite at ORIGINAL index `t` iff `(t−p) ≥ 63` and
`mapped_rets_p[t]` finite. Common region first-True index = **83** (= `max_p(p+63) = 20+63`) — matches
the pre-verified arithmetic exactly. Contiguous slice **[83, 5725], n = 5643 candles, 2020-01-28 ..
2025-03-23.** L1 and V0 common masks identical.

---

## 3. TABLE 1 — ENSEMBLE-L1 headline (common warmup=63 slice, PPY=1095; thresholds alongside)

| metric | observed | frozen threshold (verdict → Phase 7) |
|---|---|---|
| **Sharpe (headline)** | **+1.2826** | G-sharpe-floor ≥ +0.60 (H); target ≥ +0.90 (S) |
| **Sharpe (2×-cost)** | **+1.0921** | G-2xcost ≥ +0.45 (H); target ≥ +0.75 (S) |
| ann vol | 0.1987 | (context) |
| ann return | +26.54% | (context) |
| **maxDD** | **−18.59%** | G-dd-floor ≥ −35% (H); target ≥ −30% (S) |
| **turnover (ann 1-way)** | **50.3x** | G-turnover ≤ 100x (H) |
| **worst calendar month** | **−8.17% @ 2021-11** | G-worst-month ≥ −15.0% (H) |
| monthly win rate | 69.8% | (context) |
| candle win rate | 53.2% | (context) |
| top-10-month concentration | 83.9% | (context) |
| **min per-year Sharpe** | **+0.709** | G-years every year ≥ 0 (H) |

2×-cost Sharpe is from the **ground-truth re-run matrix** (21 L1@2x + 21 V0@2x, CostModel(10,5)); the
analytic twin agrees to −0.00009 Sharpe (see §9 anomaly #1). Turnover cross-check (common-slice
mean×PPY) = 50.5x, consistent with the §4‖ derivation 50.34x.

### Per-year ensemble Sharpe (2025 = 2025Q1; IS ends 2025-03-24)

| book | 2020 | 2021 | 2022 | 2023 | 2024 | 2025Q1 |
|---|---|---|---|---|---|---|
| **ENSEMBLE-L1** | +2.09 | +1.41 | +0.71 | +0.89 | +1.19 | +1.95 |
| **V0-ENSEMBLE** | +1.12 | **−0.35** | +1.10 | **+0.01** | +0.29 | +2.36 |

Observation only: ENSEMBLE-L1's six part-years are all ≥ 0 (min +0.709 @ 2022); V0-ENSEMBLE has a
negative 2021 (−0.35). G-years verdict is Phase 7.

---

## 4. TABLE 2 — V0-ENSEMBLE reference (equal-weight 21-phase ensemble of the /005 base)

Apples-to-apples reference for G-mania / G-crash context (both books are 21-phase ensembles).

| metric | V0-ENSEMBLE |
|---|---|
| Sharpe | +0.4504 |
| Sharpe (2×-cost) | +0.2571 |
| ann vol | 0.2156 |
| maxDD | −21.95% |
| ann return | +7.69% |
| turnover (ann 1-way) | 55.4x |
| worst calendar month | −10.32% @ 2023-09 |
| min per-year Sharpe | −0.348 |

---

## 5. TABLE 3 — CRASH (20 mo) + MANIA (13 mo) buckets, ENSEMBLE-L1 & V0-ENSEMBLE + leg split

Legs averaged across tranches then bucketed. Frozen thresholds alongside; verdict → Phase 7.

- **G-crash:** ENSEMBLE-L1 crash mean ≥ +1.55%/mo AND > 0 (HARD).
- **G-mania:** ENSEMBLE-L1 mania mean ≥ V0-ENSEMBLE mania + 2.0pp = **−1.242 + 2.0 = +0.758%/mo** (HARD).

| book | bucket | mean_ret | win% | worst | wm | long_px | short_px | net_fund |
|---|---|---|---|---|---|---|---|---|
| **ENSEMBLE-L1** | crash (20) | **+0.933%** | 70% | −5.94% | 2022-06 | −0.910 | +1.204 | −0.036 |
| **ENSEMBLE-L1** | mania (13) | **+4.535%** | 77% | −4.25% | 2023-01 | +2.184 | −1.462 | −0.087 |
| V0-ENSEMBLE | crash (20) | +0.935% | 70% | −5.41% | 2021-05 | −0.910 | +1.203 | −0.029 |
| V0-ENSEMBLE | mania (13) | −1.242% | 38% | −10.23% | 2023-01 | +2.200 | −2.313 | +0.019 |

Observations (numeric facts; gate resolution → Phase 7):
- **Crash bucket:** ENSEMBLE-L1 crash mean **+0.933%** is below the frozen +1.55%/mo floor and above
  0. The overlay barely moves crash at the ensemble level (V0-ENS +0.935% → ENS-L1 +0.933%); the short
  leg stays the crash friend (short_px +1.204 > 0). The +1.55% floor was calibrated on single-phase V0
  crash (+2.586% × 0.6); **BOTH** ensembles' crash means (~+0.93%) land below it — staggering averages
  the crash P&L down from the favorable single-phase draw (see §9 anomaly #3).
- **Mania bucket:** ENSEMBLE-L1 mania **+4.535%** clears the (relative) +0.758% threshold by a wide
  margin. Note the threshold came in far below the brief's predicted ≈+4.5% because V0-ENSEMBLE mania
  is **negative** (−1.242%), not the brief-predicted ≈+2.5% (see §9 anomaly #4). The C1+C2 overlay cuts
  the mania short-squeeze at the ensemble level exactly as designed: short_px −2.313 (V0-ENS) → −1.462
  (ENS-L1), lifting mania from −1.242% to +4.535% and win-rate 38% → 77%.

---

## 6. TABLE 4 — ENSEMBLE-L1 worst-10 calendar months (leg split)

Full 63-month table is in the run log; the worst-10 (by compounded monthly return):

| month | ret | long_px | short_px | net_fund |
|---|---|---|---|---|
| 2021-11 | −8.17% | −0.0045 | −0.0752 | −0.0010 |
| 2023-09 | −7.72% | +0.0215 | −0.0554 | −0.0412 |
| 2024-05 | −6.41% | +0.1150 | −0.1759 | −0.0003 |
| 2022-06 | −5.94% | −0.2065 | +0.1532 | −0.0027 |
| 2022-09 | −4.86% | −0.0352 | −0.0089 | −0.0009 |
| 2023-01 | −4.25% | +0.1694 | −0.2046 | −0.0038 |
| 2021-12 | −4.16% | −0.0922 | +0.0537 | +0.0007 |
| 2020-05 | −3.73% | +0.0243 | −0.0606 | +0.0023 |
| 2020-01 | −3.48% | +0.0159 | −0.0498 | −0.0010 |
| 2025-02 | −3.43% | −0.1543 | +0.1311 | −0.0068 |

Worst month −8.17% (2021-11) clears the −15.0% G-worst-month floor with margin. No month is worse than
the single-phase L1 worst (−12.72%, /006). The two deepest months are short-leg-driven
(2021-11 short_px −0.0752; 2023-09 short_px −0.0554 + a −0.0412 funding drag).

---

## 7. TABLE 5 — tranche correlation → rho_bar (the mechanism driver)

- **rho_bar (mean off-diagonal pairwise Pearson, common slice) = +0.5245** — §3 prediction was **+0.88
  [+0.80, +0.94]**; observed is **far below the band.**
- min pairwise +0.3847 · max pairwise +0.8396.
- diversification factor `sqrt(21/(1+20·rho_bar))` = **1.3519** (brief assumed ≈1.03–1.06).
- vol factor `sqrt((1+20·rho_bar)/21)` = 0.7397 (ensemble vol / typical tranche vol = 0.1987/0.2698 =
  0.737×, matching).

This is the load-bearing observation: the 21 rebal-phase tranches are **much less correlated than the
brief assumed** (0.52 vs 0.88), so time-diversification of entry timing is far stronger than predicted.
The consequence propagates to Sharpe (§8) and maxDD (§8-forensics).

---

## 8. TABLE 6 — turnover verification (§4 ‖) + TABLE 7 predictions + TABLE 9 Sharpe check

**Turnover (§4 ‖ derivation).** ensemble 1-way turnover = `(1/21)·Σ_p T_p^ann` = **50.34x/yr**
(per-tranche T_p^ann mean 50.3x, min 49.1x, max 51.3x). The staggered book trades the SAME ~50x/yr as
a single phase; the "÷21 then ×21" cancels. **Disclosed biases:** (i) no-netting = COST-CONSERVATIVE
(a real book nets internal cross-tranche crossings → real turnover ≤ ~50x, so all cost-bearing metrics
are a pessimistic lower bound); (ii) constant equal 1/21 weights assume costless cross-tranche weight
maintenance = a small OPTIMISTIC idealization. Both tiny; net direction likely conservative.

**TABLE 7 — §3 pre-registered predictions vs observed** (hit/miss BLANK — scored in Phase 7):

| quantity | point | band | observed | hit? |
|---|---|---|---|---|
| rho_bar | +0.88 | [+0.80,+0.94] | **+0.5245** | [ ] |
| Ensemble Sharpe | +0.98 | [+0.90,+1.08] | **+1.2826** | [ ] |
| Ensemble vol (÷ single-phase typ.) | 0.94× | [0.88×,0.98×] | **0.737×** | [ ] |
| Ensemble maxDD | −28% | [−22%,−36%] | **−18.59%** | [ ] |
| Ensemble 2×-cost Sharpe | +0.86 | [+0.76,+0.96] | **+1.0921** | [ ] |
| Ensemble turnover (ann 1-way) | +50x | [+48x,+55x] | **50.3x** | [ ] |
| Ensemble crash-bucket mean (20mo) | +1.7%/mo | [+1.3%,+2.1%] | **+0.933%** | [ ] |
| Ensemble mania-bucket mean (13mo) | +4.8%/mo | [+3.8%,+5.8%] | **+4.535%** | [ ] |
| Ensemble worst single month | −11% | [−8%,−14%] | **−8.17%** | [ ] |
| Min per-year Sharpe | +0.2 | all years ≥ 0 | **+0.709** | [ ] |

Mechanically: turnover, mania mean, worst-month, and min-PY land inside their bands; **rho_bar,
Ensemble Sharpe, vol, maxDD, 2×-cost Sharpe, and crash mean land OUTSIDE their bands** — and (except
crash) in the **favorable** direction. The single root cause is rho_bar (0.52 not 0.88): the low
correlation makes the diversification factor 1.35 not ~1.05, which lifts Sharpe well above the band and
clips maxDD below the band. Scoring is Phase 7.

**TABLE 9 — analytic ensemble-Sharpe confirmation (§2a arithmetic).**
phase-mean Sharpe (sweep, warmup=63) +0.9474 × div-factor 1.3519 = **+1.2807**; phase-mean on the
common slice +0.9528 × 1.3519 = **+1.2881**; **observed +1.2826** (Δ = −0.0056 vs common-slice
analytic). The observed Sharpe IS the phase-mean scaled by the diversification factor — arithmetic, per
§2a — but the factor is 1.35, not ~1.05, so the ensemble Sharpe (+1.28) exceeds BOTH the phase mean
(+0.947) AND the single-phase Wed@00h lucky draw (+1.164). (Level interpretation → Phase 7.)

---

## 9. maxDD FORENSICS — the crux (F7 resolved): TAIL CLIPPED, not synchronized

| quantity | value |
|---|---|
| **ENSEMBLE-L1 maxDD** | **−18.59%** (trough 2022-02-06, peak 2021-11-09) |
| 21 single-phase tranche maxDD (common slice) | mean −37.30% · min −70.42% · max −21.31% · median −32.21% |
| tranche DD AT the ensemble trough (2022-02) | mean −22.80% · min −43.52% · max −0.66% |
| tranches whose OWN maxDD trough is in 2022-02 | **0 / 21** |
| ensemble maxDD − mean tranche maxDD | **+18.71pp** |

**Reading (observation, not a verdict): the phase-tail is TIME-DIVERSIFIABLE.**
- The ensemble maxDD (−18.59%) is **shallower than every single tranche's maxDD** (best single phase
  −21.31%), and +18.71pp shallower than the phase-mean tranche maxDD (−37.3%). A large positive gap ⇒
  averaging clipped the tail; a near-zero gap would have meant a synchronized regime loss.
- **The ensemble's worst episode is a different episode than the single-phase worst episodes.** The
  deep-DD phases (p13–p16: maxDD −57% to −70%) all trough in **2024-10 / 2024-08**; at the ensemble's
  2022-02 trough those same phases are only −19% to −43% down, and the shallow phases are near flat.
  Conversely, in 2024-10 the phases that crater are offset by phases that don't, so the ensemble is
  fine there. **0/21 tranche troughs coincide with the ensemble trough** — textbook staggered-entry
  time-diversification. The 2024-10 squeeze that individually kills phases p9–p15 is almost entirely
  diversified away in the ensemble.

Per-tranche maxDD trough months (phase → month): p0 2023-12, p1 2020-11, p2 2020-07, p3 2021-04,
p4 2022-04, p5 2024-10, p6 2022-01, p7 2022-09, p8 2023-02, p9 2024-10, p10 2024-10, p11 2023-02,
p12 2023-03, p13 2024-10, p14 2024-10, p15 2024-10, p16 2024-08, p17 2022-04, p18 2023-12, p19 2022-09,
p20 2022-09 — scattered across 2020–2024, no clustering at the ensemble trough.

---

## 10. Anomaly / forensic notes

1. **The analytic 2×-cost twin is NOT exact to 1e-15 (brief §7 / REVIEW-007-preflight point 5(ii)
   premise does not hold).** The preflight verified `rets_2x = rets_1x − turnover·cost_side` as EXACT
   elementwise. On this engine it is exact ONLY at cost-bearing rebal candles (tranche-0 error there =
   0.0e+00); **between rebals it drifts** because the carried fixed shares are re-normalized by the
   (cost-dependent) running equity — the drifted weight `w_eff = shares·price/E` scales by the equity
   ratio `E_rebal/E[k−1]`, which differs once cost diverges. Tranche-0 elementwise MAX deviation
   **7.13e-05** (mean 3.9e-6); ensemble 2×-cost Sharpe deviation analytic vs re-run **−0.00009**
   (~2e-4 at tranche level). **Resolution:** I report the GROUND-TRUTH re-run matrix (21 L1@2x + 21
   V0@2x, the brief's explicitly-permitted equivalent path) as the authoritative 2×-cost number
   (+1.0921); the analytic twin is carried only as a cross-check. Sharpe impact is negligible; the
   G-2xcost read is unaffected. Flagged for the Critic — the "exact analytic twin" claim should be
   corrected in any future brief for this fixed-share engine.
2. **rho_bar came in at +0.52, not the predicted +0.88** (§7). The QR's "near-identical holdings
   shifted ≤6.7d ⇒ high correlation" reasoning over-estimated the correlation of the *8h return
   streams*: the fixed-share drift + staggered rebal timing means two distant-phase books rarely hold
   the same freshly-rebalanced portfolio simultaneously (max pairwise only +0.84, for adjacent phases).
   This single miss cascades into the favorable Sharpe/vol/maxDD misses. Scored in Phase 7.
3. **Both ensembles' crash-bucket means (~+0.93%) fall below the +1.55% G-crash floor.** The floor was
   calibrated on single-phase V0 crash (+2.586% × 0.6 ≈ +1.55%). The ENSEMBLE V0 crash is only +0.935%
   — i.e. staggering averages the crash P&L down from the favorable single-phase draw, so the floor
   (calibrated single-phase) sits above even the V0-ENSEMBLE reference. ENSEMBLE-L1 crash +0.933% is
   essentially unchanged vs V0-ENSEMBLE (+0.935%) and remains > 0 with the short leg still the crash
   friend (short_px +1.204). This is a floor-vs-construction mismatch, not a crash-alpha collapse in
   the overlay — but the observed number is below the frozen HARD floor. Localization → Phase 7.
4. **V0-ENSEMBLE mania is negative (−1.242%), vs the brief's predicted ≈+2.5%/mo.** Single-phase
   Wed@00h V0 mania was +2.524% (/006); the 21-phase V0 ensemble mania is −1.242% (win 38%, worst
   −10.23%). Because G-mania is *relative* (V0-ENS + 2.0pp), the actual threshold is +0.758%/mo, far
   below the brief's predicted +4.5%. ENSEMBLE-L1 mania (+4.535%) clears it comfortably; the mechanism
   (C1+C2 cutting the mania short squeeze) is clearly visible at the ensemble level (V0-ENS short_px
   −2.313 → ENS-L1 −1.462). The gate self-adjusted correctly; the brief's *point-prediction* for the
   reference was off.
5. **Determinism & reconciliation.** Two full runs produced bit-identical numbers. Sweep reproduction
   ≤1.28e-15; per-tranche + ensemble leg attribution reconciles ≤3.12e-17; parity ties the frozen
   candidate to the digit. No NaN Sharpe, no NaN P&L, no zero-trade months. Single frozen pass.
6. **top-10-month concentration 83.9%** (below single-phase L1's 83.0%? essentially the same;
   comfortably < 100%, so no de-grossing artifact). monthly win rate 69.8%, candle win 53.2%.

---

## 11. Status

**OVERALL = READY-FOR-PHASE-7**

IS-only frozen ensemble pass complete. OOS sealed (no OOS candle touched; runtime assert `pis.grid_ms
.max() < OOS_CUTOFF_MS`). Parity + sweep reproduction tie to ≤1.28e-15; leg attribution reconciles
≤3.12e-17; common-slice first-True = 83 exactly. 53/53 tests green (2 new). Observed values only — the
gate PASS/FAIL scorecard, the §5.1 SUCCESS/PARTIAL/FAIL tier, the §3 prediction hit/miss scoring, and
the §5.3 forward-switch recommendation are the QR's Phase-7 and the Critic's calls. Two premise
corrections are flagged for the Critic (§10 #1 analytic-2x non-exactness; §10 #2/#3/#4 prediction
misses driven by rho_bar).
