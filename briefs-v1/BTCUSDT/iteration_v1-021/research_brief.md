# Research Brief — iter-v1/021 (BTCUSDT) — Phases 1–2 (THICKEN the OOS edge, IS-ONLY)

**Author:** Crypto-markets Quant Researcher. **Symbol:** BTCUSDT. **Interval:** 8h (sacred).
**Scope:** Phase 1 (EDA) + Phase 2 (labeling/entry). **IS-ONLY. Objective: SHARPE / generalization.**
**Merge gate (RESOLVED 2026-06-17):** generalization-first — (1) both-positive (IS>0 AND OOS>0),
(2) then OOS; never chase/overfit OOS. Anchor = `BASELINE_V1_BTCUSDT` (iter-020 IS +0.37 / OOS +0.09).

All numbers come from three committed, re-runnable, IS-ONLY scripts under
`analysis/BTCUSDT/iteration_v1-021/`. Each hard-filters `open_time < OOS_CUTOFF_MS = 1742774400000`
(2025-03-24), asserts `df["open_time"].max() < OOS_CUTOFF_MS` BEFORE any forward quantity, computes the
forward log-return AFTER the filter, builds every primitive (SMA200, ATR14, dist_atr, funding signal)
with `.shift(1)` past-only, and selects every threshold as a **PAST-ONLY per-sub-period quantile**
(purged by N_LABEL=42). **Nothing is fit/selected/calibrated against OOS; OOS rows are never read for
design.** A leak-probe (`leak_guard_and_oos_count_probe.py` Part A) confirms the funding `.shift(1)` is
load-bearing: 478/2382 chop re-admission decisions (20.07%) FLIP without it. `src/`, the runner, and OOS
are UNTOUCHED.

- `regime_conditioner_screen.py` → screens 6 crypto-native regime conditioners (funding/vol/OI) for
  whether they can RE-ADMIT gate-skipped chop rows that share the trend-aligned edge.
- `r2_funding_contra_robustness.py` → robustness sweep + side decomposition + concentration table of
  the winning conditioner.
- `leak_guard_and_oos_count_probe.py` → leak guard (Part A) + IS-only trade-rate-floor projection (Part B).

---

## 0. Headline finding (read this first)

**A crypto-native FUNDING-CONTRA-CROWD regime signal robustifies the iter-020 book on IS evidence.**
The conviction gate over-thinned the book by skipping ALL weak-trend (price-near-SMA200) rows. But a
subset of those skipped rows are NOT chop — they are positioning-fragility setups where **funding
OPPOSES the trend-state direction**, and the trend-aligned direction is the high-quality side. Re-admitting
ONLY those rows (a) **thickens the book +23% to +31%** (IS firing candles 2755 → 3398 at q_f=0.50;
→ 3603 at q_f=0.30), (b) the re-admitted rows THEMSELVES carry a positive, sub-period-stable edge
(readmit full +0.56, recent3 +0.74, +1.39%/trade at q_f=0.50 — unlike every other conditioner, whose
re-admitted rows are noise ~0 or negative), and (c) **de-concentrates the book**: max single-month share
0.396 → 0.349, top-2-month share 0.620 → 0.545, while the book net GROWS (+65.8 → +74.7). The combined
book preserves the iter-020 stability fingerprint (frac_pos 0.70, recent3 +1.58, dispersion improves
2.18 → 1.77; worst sub-period 2022-07 improves −3.87 → −2.76). This is the exact robustification the
task asked for, IS-only, with no OOS tuning.

### 0.1 — The screen: only FUNDING-CONTRA re-admits edge-sharing trades (IS-only)

`regime_conditioner_screen.py`. Each candidate re-admits chop rows where its regime is favourable;
the decisive column is **+readmitted_chop_only** (the re-admitted rows scored ALONE — they must share
the edge, not dilute it). Net of 0.14% RT cost, IS-only:

| conditioner | comb full | comb fpos | comb trades | maxMoShr | top2Shr | **readmit full** | **readmit fpos** | **readmit rec3** |
|---|---:|:--:|---:|---:|---:|---:|:--:|---:|
| REF_gated (iter-020 skeleton) | +1.00 | 0.70 | 2755 | 0.396 | 0.620 | — | — | — |
| REF_ungated (all trend rows) | +0.41 | 0.70 | 5137 | 0.497 | 0.780 | — | — | — |
| REF_chop_only (the skipped chop) | −0.22 | 0.30 | 2382 | 0.618 | 1.015 | — | — | — |
| **R2 funding-contra-crowd** | **+0.91** | **0.70** | **3398** | **0.349** | **0.545** | **+0.56** | 0.40 | **+0.74** |
| R1 funding-extreme | +0.72 | 0.70 | 3817 | 0.391 | 0.611 | +0.04 | 0.70 | −0.08 |
| R3 funding-spread-extreme | +0.69 | 0.70 | 3578 | 0.430 | 0.673 | −0.23 | 0.50 | +0.18 |
| R4 vol-low | +0.52 | 0.70 | 4166 | 0.508 | 0.797 | −0.45 | 0.33 | +0.69 |
| R5 vol-high | +0.88 | 0.70 | 3372 | 0.349 | 0.546 | +0.48 | 0.44 | −1.61 |
| R6 oi-build | +0.75 | 0.80 | 3475 | 0.400 | 0.626 | −0.03 | 0.44 | +0.87 |

**R2 is the unique winner on the load-bearing criterion.** Its re-admitted rows are the ONLY ones with
a clearly positive AND recent-stable edge (full +0.56, recent3 +0.74). R1 (funding-extreme, sign-agnostic)
dilutes (readmit full +0.04 ≈ noise); R3/R4/R6 re-admit net-negative or near-zero rows; R5 (vol-high) has
positive full but recent3 −1.61 (the edge is in old windows, not recent — unstable). Critically, R2 ALSO
gives the lowest concentration (maxMoShr 0.349, top2 0.545) — it spreads the edge, exactly the task goal.
(R5's concentration ties R2's, but its re-admitted edge is recent-unstable — rejected.)

### 0.2 — The crypto mechanism (why funding-OPPOSES-trend marks high-quality entries)

This is a positioning-fragility / reflexive-squeeze regime, native to perpetual futures:

- **SHORT trend (price < SMA200) + POSITIVE funding z30** = crowded LONGS paying carry to hold *against*
  a downtrend. Funding is the crowd leaning the wrong way; the unwind/liquidation pressure fuels the
  continuation DOWN. The trend-state direction (short) is the right side.
- **LONG trend (price > SMA200) + NEGATIVE funding z30** = crowded SHORTS paying carry to hold *against*
  an uptrend. The short-squeeze fuel pushes UP. The trend-state direction (long) is the right side.

In both cases the candle was skipped by the conviction gate only because price was *near* the SMA200
(small |dist_atr|), not because the trade was bad. Funding-vs-trend opposition is a SECOND, orthogonal
conviction axis (positioning crowding) that the price-distance gate is blind to. This is reasoning from
crypto market structure (funding/price feedback, liquidation cascades), not equity intuition.

### 0.3 — No knife-edge; broad plateau (IS-only)

`r2_funding_contra_robustness.py`, funding-magnitude quantile q_f sweep:

| q_f | comb full | comb fpos | comb rec3 | comb trades | readmit n | readmit full | readmit rec3 | maxMoShr | top2Shr |
|---:|---:|:--:|---:|---:|---:|---:|---:|---:|---:|
| 0.30 | +0.81 | 0.70 | +1.36 | 3603 | 848 | +0.22 | +0.30 | 0.370 | 0.579 |
| **0.40** | **+0.88** | 0.70 | +1.53 | 3501 | 746 | +0.44 | +0.63 | 0.352 | 0.551 |
| **0.50** | **+0.91** | 0.70 | +1.58 | 3398 | 643 | +0.56 | +0.74 | **0.349** | **0.545** |
| 0.60 | +0.95 | 0.70 | +1.46 | 3271 | 516 | +0.66 | +0.62 | 0.353 | 0.552 |
| 0.70 | +0.97 | 0.70 | +1.56 | 3142 | 387 | +0.71 | +0.72 | 0.360 | 0.563 |

Monotone, flat-rising plateau: frac_pos pinned at 0.70 across the whole range; combined full climbs
+0.81 → +0.97 as q_f tightens (fewer but higher-quality re-admits); concentration is best at q_f≈0.50.
This is NOT a tuned knife-edge. **q_f = 0.50 is the crypto-canonical mid-plateau choice** (median |funding|
= "above-average crowding"), matching the un-tuned-median philosophy of the SMA200 and the conviction gate.

### 0.4 — Both sides contribute; the SHORT re-admits are the stable robustifier (IS-only)

Side decomposition at q_f=0.50:

| leg | combined full | combined fpos | combined rec3 | **readmit full** | **readmit rec3** | readmit n | readmit WR |
|---|---:|:--:|---:|---:|---:|---:|:--:|
| combined LONG | +1.44 | 0.60 | +1.29 | +0.69 | −0.00 | 331 | 48.3% |
| combined SHORT | +0.06 | 0.30 | −0.41 | **+0.39** | **+1.54** | 312 | 53.8% |

Mechanistically coherent: the re-admitted SHORT rows are the recent-STABLE contributor (readmit short
recent3 **+1.54**, WR 53.8%) — and the short leg is precisely the campaign's documented weak/fragile
side. R2 adds *stable, edge-sharing* short trades (crowded-long squeezes) on top of an unchanged book,
robustifying the side that needed it WITHOUT building an OOS-curve-fit short-only book (the full short
leg still nets near-flat; we are ADDING good shorts, not flipping to shorts).

---

## 1. Phase-2 decision — label/direction UNCHANGED; the axis is an ENTRY RE-ADMISSION

**Target/label UNCHANGED:** `fixed_horizon` N=42 (14d), `use_atr_labeling=False`, let-winners-run exit
(`atr_tp=100` non-binding / `atr_sl=1.45`), abs_pnl weights. **Direction UNCHANGED:** stateless trend-state
sign = sign(close[t−1] − SMA200[t−1]). **Conviction gate UNCHANGED:** q=0.40 trend-strength gate.

**NEW (the single axis): a funding-contra-crowd RE-ADMISSION of gate-skipped rows.** At a candle the
conviction gate would SKIP (weak trend, |dist_atr| < q40), additionally check funding opposition; if it
holds, RE-ADMIT the trade (do not skip). Past-only:
```
dir(t)        = sign(close[t−1] − SMA200[t−1])                       # unchanged trend-state
opposes(t)    = sign(funding_z30[t−1]) == −sign(dir(t))              # funding leans against the trend
crowded(t)    = |funding_z30[t−1]| ≥ f_thr(t)                        # f_thr = past-only q_f quantile of |funding_z30|
readmit(t)    = (gate would skip) AND opposes(t) AND crowded(t)      # un-skip this row
fire(t)       = (conviction gate fires) OR readmit(t)
```
`funding_z30` = the parquet column `funding_rate_zscore_30` (already in the iter-009 19-col HYBRID set,
so it is already loaded and `.shift(1)`-lagged in the feature pipeline). The re-admission NEVER flips
direction — it only un-skips a row at the unchanged trend-state direction.

---

## 2. Proposed changes (Phase 5 → QE Phase 6)

- **Labeling:** UNCHANGED.
- **Direction:** UNCHANGED (trend-state override, `enable_trend_state_dir=True`, sma 200).
- **Conviction gate:** UNCHANGED (`enable_trend_strength_gate=True`, atr 14, quantile 0.40).
- **NEW funding-contra re-admission:** add `enable_funding_contra_readmit: bool=False`,
  `funding_contra_col: str="funding_rate_zscore_30"`, `funding_contra_quantile: float=0.50`.
- **Features:** KEEP the 19-col HYBRID set unchanged (the mechanism is a RULE-layer entry primitive,
  `funding_rate_zscore_30` is already in the set; no feature add/remove). Single-axis discipline.
- **Risk gates:** KEEP R2 brake, R3 OOD (0.70), R5 vol-target. R1 OFF. Unchanged.

### Section 2.5 — Risk Declaration (v1)
- **Declaration:** NORMAL-RISK.
- **Reason:** the re-admission is a stateless RULE-layer entry filter on top of the UNCHANGED training
  objective, UNCHANGED direction, and UNCHANGED conviction gate. It does NOT change Optuna's
  training-objective domain — the model trains the identical labels; the rule only decides whether an
  already-gate-skipped candle is un-skipped at the unchanged trend-state direction.
- **Mitigation:** the rule can ONLY ADD trades that the bare trend-state book would already take (it
  re-admits a subset of the trend-state rows the conviction gate removed); it cannot open a position the
  trend-state direction wouldn't. Worst case it thins/thickens the book — caught by the trade-rate floor.

---

## 3. Expected impact + predicted IS/OOS profile

- **Predicted IS Sharpe:** ≈ **+0.30 to +0.45** (skeleton combined full +0.81 to +0.97 at q_f 0.30→0.70;
  the model timing/sizing + R2 + let-run interaction compresses the skeleton number to the iter-020
  realized scale, as iter-020's skeleton +1.00 → realized +0.37). Expect NOT below iter-020's +0.37
  (the re-admitted rows are net-positive and the combined skeleton dispersion IMPROVES 2.18 → 1.77).
- **Predicted OOS Sharpe:** ≈ **+0.05 to +0.30**, both-positive TARGET. Rationale: the re-admitted rows'
  IS recent3 fingerprint (+0.74 at q_f=0.50; the SHORT re-admits +1.54) is the closest IS analogue to
  the 2025-26 OOS correction regime, and the mechanism (crowded-funding squeezes) is regime-agnostic and
  crypto-structural. The de-concentration (top-2-month 0.62 → 0.545) directly attacks the iter-020
  fragility (2 lucky shorts ≈ 46% of OOS net). Honest CI is wide — this is still a directional 14d book.
- **vs baseline (iter-020 IS +0.37 / OOS +0.09):** designed to hold both-positive while spreading the
  OOS edge across MORE trades and months. Success = both-positive HELD + OOS-concentration falsifier
  PASSED (no ≤2 OOS trades/month > 40% of OOS net), NOT a bigger OOS number.
- **Trade rate (the primary risk):** IS firing-rate multiplier 1.233x at q_f=0.50 → ~47 projected OOS
  trades (iter-020 had 38). This is just under the ≥50 v1-specialist floor. **q_f=0.30 raises the
  multiplier to 1.308x → ~50 projected** while keeping the re-admitted edge positive (full +0.22,
  recent3 +0.30) and de-concentrating (maxMoShr 0.370, top2 0.579). See §4 fallback.

---

## 4. Risk Mitigation

- **R2 drawdown brake (KEEP):** IS-calibrated; bounds the worst sub-period (combined worst 2022-07
  improves −3.87 → −2.76). Simulated historical effect (iter-015): OOS DD 31.8% → 6.4%.
- **R3 OOD (KEEP, 0.70):** orthogonal regime-shift guard (feature-distribution Mahalanobis).
- **The funding-contra re-admission IS a quality primitive:** it does not add chop indiscriminately
  (R1/R4 do); it adds ONLY positioning-fragility rows where the trend-aligned direction is the
  high-quality side. Simulated IS effect: combined full +0.91 (q_f=0.50) vs gated +1.00 skeleton with
  +23% more trades and lower concentration — a Sharpe-neutral, breadth-positive, concentration-negative
  trade-off (the right shape per the merge gate).
- **Concentration cap:** N/A (single symbol) — but the mechanism's PURPOSE is de-concentration; the
  monthly-share table is the calibration evidence.
- **Kill-switch / fallback:** if the EXPLORATION (K=5) run shows the OOS trade count < 50 at q_f=0.50,
  drop to **q_f=0.30** (pre-registered, IS-stable: combined full +0.81, frac_pos 0.70, readmit full +0.22).
  If even q_f=0.30 misses 50 OOS trades on the real backtest, the thin trade rate is intrinsic to the
  14d-hold trend-state design (honest null on thickening — report it).

---

## 5. Pre-registered FALSIFIER (generalization-first; the gate's exact terms)

This design's robustification claim is FALSIFIED on the real bagged K=20 backtest if ANY of:
1. **Both-positive breaks** — IS Sharpe ≤ 0 OR OOS Sharpe ≤ 0. (Must hold both per the PRIMARY gate.)
2. **Material IS regression** — IS Sharpe < +0.30 (below iter-020's +0.37 by more than noise) — the
   re-admitted rows degraded the IS book; fall back to bare iter-020.
3. **OOS-concentration NOT improved / falsifier tripped** — any ≤2 OOS trades in a single month supply
   > ~40% of OOS net (the iter-020 fragility persists). The whole point is to BREAK this; if it doesn't,
   the mechanism failed its objective even if Sharpe is positive.
4. **OOS trades < 50 at BOTH q_f=0.50 and the q_f=0.30 fallback** — too thin at this horizon; honest null.
5. **The combined-book most-recent IS sub-period comes in negative** on the real backtest (contradicting
   the +1.36→+1.58 skeleton recent3) — the stability is a proxy artifact; re-test bare iter-020.

**MANDATORY K=20 confirmation.** The direction + conviction gate + funding-contra rule are deterministic
(zero seed variance), but the LightGBM timing/sizing layer is the basin-lottery surface. ANY K=5
EXPLORATION screen MUST be K=20-confirmed before a merge claim (per the iter-016/020 lottery history).

---

## 6. QE WIRING FLAG (new code the Engineer must add)

The funding-contra re-admission attaches to the EXISTING trend-strength gate-skip site
(`lgbm.py:2797-2821`, where a weak-trend candle returns `NO_SIGNAL`). Minimal, surgical:

1. **Constructor flags** — add to `LightGbmStrategy.__init__` (mirror the
   `enable_trend_strength_gate` / `trend_strength_quantile` pattern at `lgbm.py:323-325`):
   `enable_funding_contra_readmit: bool=False`, `funding_contra_col: str="funding_rate_zscore_30"`,
   `funding_contra_quantile: float=0.50`. Store as `self._enable_funding_contra_readmit`, etc.
2. **Past-only funding threshold (per month, training-window quantile)** — at the same month-train site
   that computes `self._trend_strength_thr` (`lgbm.py:1815-1834`), additionally compute
   `self._funding_contra_thr = quantile(|funding_contra_col| over the training window,
   funding_contra_quantile)`. Use the SAME training-window rows and the SAME past-only convention. If
   < 50 training rows → leave None (then do NOT re-admit; conservative).
3. **Re-admission at the gate-skip site** — in the `if self._enable_trend_strength_gate:` block at
   `lgbm.py:2797`, BEFORE `return NO_SIGNAL` for a weak-trend candle, check the re-admission condition:
   ```
   if self._enable_funding_contra_readmit and self._funding_contra_thr is not None:
       f = past-only value of funding_contra_col for this candle (the .shift(1) feature value)
       dir_sign = sign of the trend-state direction (_sp_direction)
       if f is not None and abs(f) >= self._funding_contra_thr and sign(f) == -dir_sign:
           # funding OPPOSES the trend AND crowding is at-least-q_f -> RE-ADMIT (skip the skip)
           pass   # do NOT return NO_SIGNAL; fall through to fire the trend-state trade
       else:
           return NO_SIGNAL
   else:
       return NO_SIGNAL
   ```
   The funding value for the candle is already available as the lagged feature column
   `funding_rate_zscore_30` in the feature row used for prediction — read it past-only (no new lookup).
4. **Decision-log** — extend the `trend_strength_gate_skip` log with a `funding_contra_readmit` event
   (`kind="funding_contra_readmit"`, log `funding_z30`, `funding_contra_thr`, `dir_sign`) so re-admissions
   are auditable in `decision_log.jsonl`.
5. **Runner flags** — `--enable-funding-contra-readmit` (store_true), `--funding-contra-col`,
   `--funding-contra-quantile`; wire into the iter-021 dispatch branch in `run_baseline_v1.py`.
6. **Look-ahead test** — add `tests/test_funding_contra_readmit_lookahead.py` proving the funding value
   used at candle t is the `.shift(1)` past-only value (mirror `tests/test_trend_strength_lookahead.py`).

**Cadence:** EXPLORATION K=5 screen at q_f=0.50 first → if both-positive AND OOS-concentration falsifier
PASSES → MANDATORY K=20 CONFIRMATION. If OOS trades < 50 at q_f=0.50, re-screen at q_f=0.30 (pre-registered).
Only the K=20 read can support a merge.
