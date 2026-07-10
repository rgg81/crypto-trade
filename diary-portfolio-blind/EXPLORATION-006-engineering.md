# EXPLORATION-006 — Engineering Report (mania-aware risk-overlay stack, 9-run frozen matrix)

- **Track:** baseline-BLIND top-20 L/S portfolio (worktree `quant-portfolio-blind`)
- **Branch:** `quant-portfolio-blind`
- **What ran:** the FROZEN 9-run variant matrix pre-registered in
  `briefs-portfolio-blind/EXPLORATION-006.md`, implemented EXACTLY — no parameter adjustments,
  no extra variants, no post-hoc re-runs. One frozen pass.
- **IS-only. OOS sealed at `OOS_CUTOFF = 2025-03-24`.** Panel hard-sliced with `slice_is()` at the
  top of the script; every number below is on candles `open_time < 2025-03-24`. Verified at runtime:
  `panel.grid_ms.max() < OOS_CUTOFF_MS`. `CONFIRMATION-005.md` not read; no baseline artifact read.
- **Artifacts:**
  - `analysis/portfolio/blind_exploration_006.py` (new — runs all 9 variants + 9 at 2×-cost + tables)
  - `tests/test_blind_engine.py` (+2 indicator leak positive-controls; 46 total)
- **No engine code changes.** Controls are the existing opt-in engine hooks; byte-identical when off.
- **No commits (per task instruction).**
- **ENGINEER SCOPE:** observed values only. Gate PASS/FAIL, the §5.2 decision-tree resolution, the
  §5.4 verdict paragraphs, and the SUCCESS/PARTIAL/FAIL tier are the QR's / Critic's Phase-7 calls.
  Every gate-relevant number below is shown with its frozen threshold ALONGSIDE; the verdict column
  is deferred.

---

## 1. Test suite: 46/46 green

`uv run pytest tests/test_blind_engine.py -q` → **46 passed in 8.72s**. Lint clean
(`ruff check` → "All checks passed"; `ruff format` applied).

- Existing 44 tests untouched (no engine edits; controls opt-in & byte-identical when off — already
  covered by `test_short_leg_plumbing_byte_identical_when_off`, `test_regime_plumbing_*`, and the
  gross_scalar / dd_brake positive-controls).
- **NEW `test_mania_gate_series_no_future_leak`** — builds the C1 `short_scalar_series` from the
  committed `mania_gate` on the real IS panel, then on a panel whose `close` AND `funding` are
  corrupted (×10 / +0.5) from `cutoff = T//2` forward. Asserts `short_scalar_series[:cutoff]` and
  `gate[:cutoff]` are bit-identical (`assert_array_equal`); non-vacuous guard confirms the gate
  changes post-cutoff (the ×10 pump forces `btc_up` and the +0.5 funding forces the funding-z high).
  **PASS** — no forward read in the 63c BTC momentum, trailing-21c dispersion, trailing-21c funding
  mean, or the 365c rolling z.
- **NEW `test_parabolic_exclude_series_no_future_leak`** — imports the SAME `build_parabolic_exclude`
  the matrix uses (no drift), builds the C2 `short_exclude` (T,C) mask on a synthetic panel and on a
  `close`-corrupted (×10) twin. Asserts `short_exclude[:cutoff]` bit-identical + non-vacuous flip
  post-cutoff. **PASS** — `rK[t] = close[t]/close[t-21]-1` reaches back only 21 candles.

---

## 2. Parity guard (brief §8 #1 — ABORT on drift) — PASS

V0 (/005 base, no controls), post-warmup=63:

| metric | observed | target | tol | result |
|---|---|---|---|---|
| Sharpe | **+0.9134** | +0.913 | ±0.005 | PASS |
| maxDD | **−32.99%** | −33% | ±1pp | PASS |
| turnover | **55.36x** | 55.4x | ±2 | PASS |

Additional construction cross-checks (all exact):

- **V0 CRASH bucket (20 mo):** mean **+2.586%/mo** ≡ DIAGNOSTIC-003 +2.586%; leg split
  long_px **−0.892** / short_px **+1.531** / net_fund **−0.035** — reproduces DIAG-003 to the digit
  (short leg carries the crash alpha).
- **V0 MANIA bucket (13 mo, `MANIA_MONTHS_FROZEN`):** mean **+2.524%/mo** ≡ brief +2.52%; win 61.5%;
  worst **−16.35% @ 2024-11** (also the overall worst calendar month) ≡ brief.
- **MANIA-rule regeneration self-check:** `mania_months(gate, grid_ms, warmup=63, thr=0.40) ==
  MANIA_MONTHS_FROZEN` → OK.
- **C1 gate IS coverage** (post-warmup) = **19.3%** ≡ RISK-006 19.3% (1091 candles at 0.5, 4636 at 1.0).
- **Per-candle leg-attribution reconciliation** `long_px + short_px + net_fund − tcost ≡ ret`: max
  error **≤ 2.8e-17** across ALL nine variants (assert < 1e-10). Panel: 5727 IS candles, 712 coins,
  2020-01-01 .. 2025-03-23.

**Consumption-lag guard:** all indicator series (`short_scalar_series`, `short_exclude`,
`gross_scalar_series`) are passed indexed by `t`; the engine consumes them at `[k-1]`
(`blind_engine.py:490/509`). NO pre-shift is applied (a pre-shift would double-lag).

**Metric protocol (brief §2.6):** every comparative metric EXCEPT turnover is computed on the common
frozen post-warmup slice starting at candle index 63 via `_metrics(res, cost, warmup=63)` — so C3's
`vol_lookback=45` does not shift the warmup and all nine runs share one denominator. **Turnover**
reads `res.metrics['turnover_ann_one_way']` (full array; warmup-independent; §2.6 F4 exception).

---

## 3. TABLE 1 — 9-variant comparison (frozen warmup=63 slice)

| run | stack | Sharpe | 2×-cost | maxDD | ann | turn/yr | wins% | worst-mo | top10% | min-PY |
|---|---|---|---|---|---|---|---|---|---|---|
| **V0** | base | **+0.913** | +0.771 | −32.99% | +25.46% | 55.4x | 53.5% | −16.35% | 98.8% | +0.35 |
| **V1** | C1 | **+1.005** | +0.865 | −28.56% | +27.37% | 51.7x | 53.5% | −13.07% | 90.2% | +0.27 |
| **V2** | C2 | **+1.200** | +1.058 | −31.11% | +35.26% | 53.3x | 53.9% | −12.72% | 82.7% | +0.33 |
| **V3** | C3 | +0.791 | +0.642 | −33.33% | +19.16% | 52.0x | 53.5% | −14.31% | 119.0% | +0.11 |
| **V4** | C4 | +0.768 | +0.714 | −32.48% | +17.59% | 48.1x | 53.5% | −14.46% | 115.2% | +0.12 |
| **V5** | C5 (falsify) | +0.842 | +0.716 | −32.73% | +21.18% | 45.1x | 53.5% | −16.35% | 112.9% | +0.34 |
| **L1** | C1+C2 | **+1.164** | +1.028 | −28.58% | +33.20% | 50.1x | 53.8% | −12.72% | 83.0% | +0.10 |
| **L2** | C1+C2+C3 | +0.983 | +0.840 | −28.45% | +24.53% | 48.0x | 53.8% | −13.50% | 98.6% | −0.10 |
| **L3** | C1+C2+C3+C4 | +0.736 | +0.600 | −25.67% | +15.01% | 40.8x | 53.8% | −15.96% | 132.3% | −0.25 |

### Per-year Sharpe by variant (2025 = 2025Q1; IS ends 2025-03-24)

| run | stack | 2020 | 2021 | 2022 | 2023 | 2024 | 2025Q1 |
|---|---|---|---|---|---|---|---|
| V0 | base | +1.51 | +1.10 | +1.07 | +0.35 | +0.46 | +2.15 |
| V1 | C1 | +1.63 | +1.63 | +0.64 | +0.27 | +0.57 | +2.15 |
| V2 | C2 | +1.68 | +2.07 | +0.95 | +0.33 | +0.86 | +1.79 |
| V3 | C3 | +1.12 | +0.93 | +1.01 | +0.11 | +0.66 | +1.84 |
| V4 | C4 | +0.99 | +1.06 | +1.07 | +0.12 | +0.46 | +2.10 |
| V5 | C5 | +1.64 | +1.05 | +0.75 | +0.34 | +0.47 | +2.14 |
| L1 | C1+C2 | +1.70 | +2.13 | +0.62 | +0.10 | +0.93 | +1.79 |
| L2 | C1+C2+C3 | +1.33 | +1.95 | +0.55 | **−0.10** | +0.97 | +1.46 |
| L3 | C1+C2+C3+C4 | +0.95 | +1.87 | +0.30 | **−0.25** | +0.37 | +1.74 |

Observation only: L2 and L3 carry a negative 2023 part-year (−0.10 / −0.25); every other variant has
all six part-years ≥ 0. Verdict (G-years) is Phase 7.

---

## 4. TABLE 2 — CRASH bucket (20 market-defined months) with leg P&L split

Frozen threshold alongside: **G-crash mean ≥ +1.55%/mo AND > 0 (HARD)**. Verdict → Phase 7.

| run | stack | mean_ret | win% | worst | wm | long_px | short_px | net_fund |
|---|---|---|---|---|---|---|---|---|
| V0 | base | **+2.586%** | 70% | −8.83% | 2022-06 | −0.892 | +1.531 | −0.035 |
| V1 | C1 | +2.268% | 70% | −8.83% | 2022-06 | −0.893 | +1.468 | −0.039 |
| V2 | C2 | +1.956% | 70% | −8.83% | 2022-06 | −0.892 | +1.413 | −0.039 |
| V3 | C3 | +2.278% | 70% | −8.45% | 2022-06 | −0.781 | +1.356 | −0.033 |
| V4 | C4 | +2.449% | 70% | −8.83% | 2022-06 | −0.811 | +1.416 | −0.032 |
| V5 | C5 (falsify) | **+1.492%** | 70% | −3.15% | 2022-01 | −0.615 | +0.974 | −0.020 |
| L1 | C1+C2 | +1.754% | 70% | −8.83% | 2022-06 | −0.894 | +1.373 | −0.042 |
| L2 | C1+C2+C3 | +1.607% | 70% | −8.45% | 2022-06 | −0.800 | +1.244 | −0.040 |
| L3 | C1+C2+C3+C4 | +1.164% | 70% | −8.45% | 2022-06 | −0.658 | +0.990 | −0.029 |

Crash-bucket monthly win rate is **70% for every variant** (no control fires often enough in the
capitulation bucket to flip a month's sign). The short leg stays the crash friend everywhere
(short_px > 0). C5 cuts the crash short leg the hardest (+1.531 → +0.974, −36%).

---

## 5. TABLE 3 — MANIA bucket (13 committed market-only months) with leg P&L split

Frozen threshold alongside: **G-mania mean ≥ V0_mania + 2.0pp = +4.52%/mo (HARD)**. Verdict → Phase 7.

| run | stack | mean_ret | win% | worst | wm | long_px | short_px | net_fund |
|---|---|---|---|---|---|---|---|---|
| V0 | base | +2.524% | 62% | −16.35% | 2024-11 | +2.269 | −1.912 | +0.033 |
| V1 | C1 | +3.955% | 69% | −13.07% | 2024-11 | +2.273 | −1.665 | −0.044 |
| V2 | C2 | +5.097% | 69% | −11.52% | 2024-11 | +2.261 | −1.528 | −0.030 |
| V3 | C3 | +1.522% | 62% | −14.31% | 2020-11 | +1.885 | −1.685 | +0.031 |
| V4 | C4 | +0.912% | 62% | −14.46% | 2023-12 | +1.763 | −1.618 | +0.021 |
| V5 | C5 (falsify) | +2.232% | 62% | −16.35% | 2024-11 | +2.056 | −1.740 | +0.033 |
| L1 | C1+C2 | **+5.829%** | 69% | −10.63% | 2024-11 | +2.263 | −1.384 | −0.084 |
| L2 | C1+C2+C3 | +3.922% | 77% | −13.50% | 2020-11 | +1.895 | −1.309 | −0.061 |
| L3 | C1+C2+C3+C4 | +2.547% | 69% | −15.96% | 2020-11 | +1.433 | −1.035 | −0.053 |

The short-leg mania squeeze is the axis the controls attack: V0 short_px −1.912 → L1 (C1+C2) −1.384
(the short leg is cut where it was being squeezed), lifting the long-leg-carried mania return. C1/C2
cut short_px surgically; C3/C4 shrink the whole book (both legs), which is why L2/L3 pull the mania
mean back down.

---

## 6. TABLE 4 — Ladder marginals (§5.1)

Observed deltas; drop-rule verdicts → Phase 7.

| marginal | definition | ΔSharpe | ΔMania (pp) | ΔCrash (pp) |
|---|---|---|---|---|
| m_C1 | Sharpe(V1) − Sharpe(V0) | **+0.0918** | **+1.431** | −0.318 |
| m_C2 | Sharpe(L1) − Sharpe(V1) | **+0.1586** | **+1.874** | −0.515 |
| m_C3 | Sharpe(L2) − Sharpe(L1) | **−0.1805** | −1.906 | −0.147 |
| m_C4 | Sharpe(L3) − Sharpe(L2) | **−0.2472** | −1.375 | −0.442 |

Observed inputs to the frozen §5.2 drop rules (RESOLUTION is a Phase-7 call):

- **R1 (drop C4):** `m_C4 = −0.2472` (< −0.05) ; `maxDD(L3) = −25.67%` vs `maxDD(L2) − 0.01 =
  −29.45%` → maxDD(L3) ≥ maxDD(L2) − 0.01 is TRUE (C4 tightens maxDD by 2.78pp). Both clauses feed R1.
- **R2 (drop C3):** `m_C3 = −0.1805` (< −0.05) AND `ΔMania_C3 = −1.906pp` (≤ 0) → first bracket true;
  also `crash(L2) = +1.607%` which is ≥ +1.55% (crash clause not triggered).
- **R3 (drop C2):** `m_C2 = +0.1586` (≥ −0.05) → R3 not triggered.
- **R4:** C1 never dropped. `ΔMania_C1 = +1.431pp` (> 0) → C1-anchor observation is positive
  (see §10).

The lean end of the ladder (C1, C1+C2) lifts Sharpe and mania; the C3/C4 rungs subtract Sharpe and
mania while tightening maxDD/turnover. The exact surviving prefix is resolved by the QR in Phase 7.

---

## 7. TABLE 5 — C1 flag coverage per crash month, split by sub-regime (brief §3.3 F2)

`cov` = fraction of the month's post-warmup candles flagged by C1; `short_px` = V0 short-leg P&L.

### (i) BTC-DOWN capitulation (14 mo) — C1 should read ≈ 0 (short crash alpha preserved)

| month | cov | V0 short_px | V0 ret | month | cov | V0 short_px | V0 ret |
|---|---|---|---|---|---|---|---|
| 2020-03 | 0% | +0.154 | +0.35% | 2022-05 | 0% | +0.290 | +8.95% |
| 2021-05 | 0% | +0.109 | +10.39% | 2022-06 | 0% | +0.137 | −8.83% |
| 2021-06 | 0% | +0.087 | −0.43% | 2022-08 | **30%** | +0.065 | −1.64% |
| 2021-09 | 10% | +0.103 | +5.39% | 2022-09 | 0% | +0.046 | +1.11% |
| 2021-12 | 0% | +0.051 | −4.96% | 2022-11 | 7% | +0.158 | +9.71% |
| 2022-01 | 0% | +0.109 | −5.36% | 2022-12 | 0% | +0.098 | +0.15% |
| 2022-04 | 11% | +0.191 | +4.92% | 2025-02 | 0% | +0.226 | +5.46% |

→ mean cov **4%**, max 30%, min 0%. In this sub-regime the short leg is the crash friend everywhere
(short_px > 0); C1 fires ≈ 0, so the capitulation crash alpha is structurally preserved — with one
watch-item (see §9).

### (ii) BTC-UP bear-rally (6 mo) — C1 MAY fire; where it does the short leg was being squeezed

| month | cov | V0 short_px | V0 ret |
|---|---|---|---|
| 2021-07 | 9% | +0.002 | +3.14% |
| 2021-08 | 43% | **−0.142** | +8.68% |
| 2022-02 | 0% | +0.018 | +5.92% |
| 2022-03 | 17% | **−0.046** | +4.78% |
| 2022-07 | 38% | **−0.146** | −1.18% |
| 2022-10 | 0% | +0.022 | +5.18% |

→ mean cov **18%**, max 43%. Where C1 fires most in this sub-regime (2021-08, 2022-07) the V0 short
leg was NEGATIVE (being squeezed) — so C1 firing there cuts a losing short (mechanism-consistent).

### (iii) MANIA bucket (13 mo) — the target regime

mean cov **60%**, max **92% (2024-11)**, min 42% (2020-12). 2024-11 (V0 short_px −0.391, ret −16.35%)
is flagged 92% — the primary C1+C2 target. Note the bucket also holds C1-flagged WINNER months where
the short leg won (2020-12 short_px +0.143, cov 42%) or the month was a strong strategy winner
(2024-02 ret +14.82%, cov 45%) — so C1's floor-0.5 clip HURTS there, keeping G-mania non-tautological.

**n_braked_rebal:** V4 = **76**, L3 = **93** braked rebal-STEPS (see §9 anomaly note — this counts
braked rebal steps, not distinct engagement episodes).

---

## 8. TABLE 6 — Pre-registered predictions (§6) vs observed singleton deltas (Vx − V0)

Hit/miss column deliberately BLANK — scored in Phase 7.

| ctrl | predicted (crash / mania / sharpe / maxDD) | obs ΔSharpe | obs ΔCrash | obs ΔMania | obs ΔMaxDD |
|---|---|---|---|---|---|
| C1 | ~0 (inert down / + up-rally) / improves / + (tail) / tightens | +0.0918 | −0.318pp | +1.431pp | +4.430pp |
| C2 | ~0 / improves / + / tightens | +0.2864 | −0.630pp | +2.573pp | +1.874pp |
| C3 | − (~12% shave) / − to ~0 / ~neutral / tightens | −0.1225 | −0.308pp | −1.002pp | −0.340pp |
| C4 | ~0 / small + / ~neutral-to-− / tightens | −0.1457 | −0.138pp | −1.612pp | +0.506pp |
| C5 | − (worse) / ~0 / − NEGATIVE / ~0-slightly tighter | −0.0717 | −1.094pp | −0.292pp | +0.259pp |

(ΔMaxDD sign convention: + = maxDD less negative = tighter.) Directional readings deferred to Phase 7;
two observations that diverge from the pre-registered direction are flagged in §9 for the Critic.

---

## 9. Anomaly / forensic notes

1. **`n_braked_rebal` is much larger than RISK-006's "4 engagements" — but it is a different
   quantity (NOT a contradiction).** V4 = 76, L3 = 93. RISK-006 §4.2's "4 engagements over 5.25 IS
   years" counts distinct engagement EPISODES simulated on the UN-braked /005 equity; `n_braked_rebal`
   counts the number of rebal STEPS spent in the braked state on the ACTUALLY-braked equity. Because
   C4 halves gross while braked, the book recovers from the −20% trigger toward the −10% release at
   HALF participation, so it sits below the release level ~2× longer → the brake is "stickier" than
   the descriptive un-braked simulation implied (76/273 ≈ 28% of rebal steps vs the 16%-of-candles
   RISK-006 estimate). This is expected own-equity feedback, not a bug — but it means C4 de-grosses
   more of the book than the calibration anticipated, which is visible in C4's mania/Sharpe drag.
   Flagged for the Critic.

2. **C4 as a SINGLETON HURTS the mania bucket (−1.612pp) — opposite the §6 "small +" prediction.**
   The DD brake, acting on its own equity, engages after a drawdown and stays braked into the
   RECOVERY/winner month, halving mania winners (V4 mania worst month is 2023-12; V4 mania mean
   +0.912% vs V0 +2.524%). This is exactly the "locks out the rebound" caveat RISK-006 §4.1 gave as
   the reason scale=0.5 (not 0.0) — here it is materialized. In the ladder, C4's marginal m_C4 is
   also negative (−0.247 Sharpe, −1.375pp mania) but it IS the only rung that tightens maxDD
   (−28.45% → −25.67%, −2.78pp) and cuts turnover (48.0x → 40.8x). Its cost/benefit is a Phase-7 call.

3. **C4 is NOT perfectly crash-inert on the actually-braked path.** Brief §3.3 states "none of C4's 4
   engagements is in the crash bucket" — true on the UN-braked equity. On the braked path (76
   engagements) some braked rebals fall inside/adjacent to 2022 crash months, so V4's crash bucket
   shrinks slightly (long_px −0.892 → −0.811, short_px +1.531 → +1.416, mean +2.586% → +2.449%,
   −0.138pp). Small, but the "crash-inert" assumption is looser than the calibration implied.

4. **C1 mildly erodes crash alpha via a capitulation bear-rally (the flagged §3.3 stress case).**
   2022-08 is a BTC-DOWN capitulation month yet C1 fires **30%** there (a bear rally within the month
   pushed btc_mom_63 > +9%), cutting a WINNING short (V0 short_px +0.065). Combined with a few other
   low-coverage capitulation months (2022-04 11%, 2021-09 10%), C1's net crash effect is −0.318pp —
   this is the "2022-07→08 turn" that RISK-006's tail scenario (which only examined 2021-04→05) did
   NOT cover. crash(V1) = +2.268% remains well above the +1.55% floor; the erosion is small but real.

5. **C2 lowers the crash bucket more than the §6 "~0" prediction (−0.630pp).** C2 fires on ~0.98% of
   (t,coin) cells; in a few bear-rally crash months some alts print +30%/7d and get excluded,
   trimming short_px (+1.531 → +1.413). crash(V2) = +1.956% still clears +1.55%.

6. **top-10-month concentration exceeds 100% for the de-grossing variants** (V3 119%, V4 115%, V5
   113%, L3 132%). This is a valid ratio, not a bug: when C3/C4/C5 shrink total log-growth while the
   top-10 winner months stay relatively intact, the aggregate of the non-top-10 months is net-negative,
   so top10/total > 1. It signals these variants concentrate growth MORE than V0 (98.8%), not less —
   a texture the Critic may want for the fat-tail-fragility read.

7. **C5 (falsification) behaved as pre-registered in all three axes.** Sharpe −0.072 (NEGATIVE),
   crash −1.094pp (worse; short_px +1.531 → +0.974, the whole-book cut eats the crash short leg),
   mania −0.292pp (≈ 0, as BTC-up mania sees little BTC drawdown). The observed directions match the
   §5.3 prediction that BTC-crash de-risking attacks the WRONG regime. (Verdict is Phase 7, but no
   observation indicts the diagnostic thesis.)

8. **Reconciliation & determinism.** Leg attribution reconciles to `res.rets` at ≤ 2.8e-17 for all
   nine variants; V0 reproduces /005 (Sharpe, maxDD, turnover) and the DIAG-003 crash split to the
   digit. No NaN Sharpe, no NaN P&L, no zero-trade months. The matrix is a single frozen pass.

---

## 10. §5.4 observation inputs (values only; verdict = Phase 7)

- **C5 falsification (pre-registered NEGATIVE):** Sharpe(V5) **+0.8416** vs Sharpe(V0) **+0.9134**
  (ΔSharpe **−0.0717**); crash(V5) **+1.492%** vs crash(V0) **+2.586%**. Both moved in the
  pre-registered direction (worse). No observation shows C5 improving Sharpe or the crash bucket.
- **C1 anchor (pre-registered ΔMania_C1 > 0):** mania(V1) **+3.955%** vs mania(V0) **+2.524%**
  (ΔMania_C1 **+1.431pp**, positive). C1 improved the mania bucket as its lead mechanism predicted.

(The QR writes the two mandatory verdict paragraphs in Phase 7; this section supplies their numeric
inputs only.)

---

## 11. Gate-relevant observations with frozen §4 thresholds (verdict → Phase 7)

Applied to ALL nine variants (the primary candidate is resolved by the §5.2 tree in Phase 7). Frozen
thresholds shown; NO PASS/FAIL stamped here (engineer scope).

Frozen HARD thresholds: G-years all ≥ 0 · G-crash ≥ +1.55%/mo & > 0 · G-mania ≥ +4.52%/mo ·
G-sharpe-floor Sharpe ≥ +0.45 AND 2× ≥ +0.35 · G-dd-floor maxDD ≥ −35% · G-turnover ≤ 100x ·
G-worst-month ≥ −15.0%.

| run | stack | min-PY | crashMean | maniaMean | Sharpe | 2× | maxDD | turn | worstMo |
|---|---|---|---|---|---|---|---|---|---|
| V0 | base | +0.35 | +2.586% | +2.524% | +0.913 | +0.771 | −32.99% | 55.4x | −16.35% |
| V1 | C1 | +0.27 | +2.268% | +3.955% | +1.005 | +0.865 | −28.56% | 51.7x | −13.07% |
| V2 | C2 | +0.33 | +1.956% | +5.097% | +1.200 | +1.058 | −31.11% | 53.3x | −12.72% |
| V3 | C3 | +0.11 | +2.278% | +1.522% | +0.791 | +0.642 | −33.33% | 52.0x | −14.31% |
| V4 | C4 | +0.12 | +2.449% | +0.912% | +0.768 | +0.714 | −32.48% | 48.1x | −14.46% |
| V5 | C5 | +0.34 | +1.492% | +2.232% | +0.842 | +0.716 | −32.73% | 45.1x | −16.35% |
| L1 | C1+C2 | +0.10 | +1.754% | +5.829% | +1.164 | +1.028 | −28.58% | 50.1x | −12.72% |
| L2 | C1+C2+C3 | −0.10 | +1.607% | +3.922% | +0.983 | +0.840 | −28.45% | 48.0x | −13.50% |
| L3 | C1+C2+C3+C4 | −0.25 | +1.164% | +2.547% | +0.736 | +0.600 | −25.67% | 40.8x | −15.96% |

---

## 12. Status

**OVERALL = READY-FOR-PHASE-7**

IS-only frozen matrix complete. OOS sealed (no OOS candle touched). Parity + DIAG-003/brief
cross-checks reproduce to the digit. 46/46 tests green (2 new indicator leak positive-controls).
Leg attribution reconciles ≤ 2.8e-17 across all nine variants. Observed values only — gate PASS/FAIL,
the §5.2 decision-tree resolution, the §5.4 verdict paragraphs, and the SUCCESS/PARTIAL/FAIL tier are
the QR's Phase-7 and the Critic's calls.
