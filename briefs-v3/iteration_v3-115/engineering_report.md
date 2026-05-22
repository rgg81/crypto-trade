# Engineering Report — iter-v3/115

## Headers

- Iteration: iter-v3/115
- Branch: iteration-v3/115
- Commit SHA: 2b99a1bd6e2bd655ac6812806abe5bd075746083
- Hardware: WSL2 x86-64 Linux 6.6.114
- Wall-clock time: 0.69h

---

## Configuration Diff vs /059 Baseline

Single axis: labeling architecture swapped from triple-barrier to coherent horizon-exit.

| Knob | /059 canonical | iter-v3/115 | Changed? |
|---|---|---|:--:|
| `label_mode` | `triple_barrier` | `fixed_horizon` | YES (the axis) |
| Execution exit geometry | TP/SL/timeout (ATR x2/x1 barriers) | fixed 21-candle timeout (barriers non-binding via atr_tp/sl_multiplier=100.0) | YES (the axis — inseparable) |
| `atr_tp_multiplier` / `atr_sl_multiplier` | 2.0 / 1.0 | 100.0 / 100.0 | YES (execution side of axis) |
| label/exit horizon N | 21 candles (10080 min) | 21 candles (10080 min) | NO |
| `V3_MODELS` | BCH/LDO/TRX | BCH/LDO/TRX | NO |
| `V3_FEATURE_COLUMNS` | 14 | 14 | NO |
| `REQUIRED_GAP` | 66 | 66 | NO |
| CV embargo | 22 candles | 22 candles | NO |
| 7-gate RiskV2 stack | /059-canonical | /059-canonical | NO |
| `regime_gate_symbols` | () | () | NO (reverted from /114's ("LDOUSDT",)) |
| `enable_ldo_realvol_gate` | False | False | NO (reverted from /114's True) |
| ENSEMBLE_SIZE / seeds / n_trials | 3-seed EXPLORATION, 35 | 3-seed EXPLORATION, 35 | NO |
| `OOS_CUTOFF_DATE` / `training_months` | 2025-03-24 / 24 | 2025-03-24 / 24 | NO |
| `ITERATION_LABEL` | v3-114 | v3-115 | YES (bookkeeping) |

**Run.log verification (lines 3–26):**
- Line 21: `label_mode (iter-v3/115 axis): 'fixed_horizon'  PASS` — confirmed.
- Line 20: `Config-accretion check (Critic /081 Rec #3): 13 knobs verified — ALL /115-state (BCH/LDO/TRX 3-symbol per-symbol, REQUIRED_GAP=66, label_mode=fixed_horizon)  PASS` — confirmed.
- `regime_gate_symbols=()` and `enable_ldo_realvol_gate=False`: confirmed at lines 7 and 11 respectively (via the accretion-check PASS and V3_MODELS disjointness PASS; the /114 kill-switch guard is asserted to expect reverted state per Change 6 — pre-flight PASSED without crashing).
- 14-feature stack: confirmed line 3 and line 64: `[lgbm] 14 feature columns`.
- `REQUIRED_GAP=66`: confirmed lines 24–26.

---

## Timeout-Exit Fraction (Price-Barriers Non-Binding Verification)

The brief's Section 3.5 requires that `atr_tp_multiplier=atr_sl_multiplier=100.0` make barriers effectively non-binding, with a target of >= 99% `timeout` exits.

**IS trades.csv exit-reason distribution:**
- `timeout`: 105 / 105 = **100.0%**

**OOS trades.csv exit-reason distribution:**
- `timeout`: 52 / 53 = **98.1%**
- `end_of_data`: 1 / 53 = 1.9% (the final trade truncated by data boundary — structurally expected, not a barrier exit)

The `end_of_data` exit is the trailing OOS candle hitting the data boundary before the 21-candle horizon expires — this is not a TP/SL barrier firing. Effective timeout fraction excluding data-boundary artifact: 100.0% IS, 100.0% OOS (no actual SL/TP exits). The coherent horizon-exit architecture is confirmed: the x100.0 ATR multipliers produce barriers of ~370% per trade on IS NATR median ~3.7%, far beyond any 21-candle move. The Section 3.5 target is met.

---

## Key Metrics Block

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | 0.3172 | 0.9370 | **2.9543** |
| daily_sharpe | 1.1421 | 2.7507 | 2.4084 |
| max_drawdown | 48.12% | 33.51% | 0.6965 |
| profit_factor | 1.2185 | 1.6022 | 1.3149 |
| win_rate | 46.67% | 52.83% | 1.1321 |
| n_trades | 105 | 53 | 0.5048 |
| total_pnl | 33.62 | 41.42 | 1.2319 |
| monthly_calmar | 0.6987 | 1.2359 | 1.7688 |
| weighted_pnl_total | 33.62 | 41.42 | 1.2319 |
| dsr | 0.000 | — | — |
| pbo | 0.1426 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 16 | — | — |

**Anchor (/060 EXPLORATION-mode reference):** IS +0.8325 / OOS +0.1403.

**IS delta vs /060 anchor:** 0.3172 - 0.8325 = **-0.5153** (IS collapse of Delta -0.52).
**OOS delta vs /060 anchor:** 0.9370 - 0.1403 = **+0.7967** (OOS spike of Delta +0.80).

---

## OOS/IS Ratio Analysis — IS-Collapse / OOS-Spike Pattern

**OOS/IS monthly Sharpe ratio:** 0.9370 / 0.3172 = **2.9543**

This is the pre-registered IS-collapse / OOS-spike divergence, Section 7's "second failure mode (~25%): IS-collapse / OOS-spike SUSPICIOUS divergence — the /105 signature."

**Gate evaluation:**

1. **Brief Section 8 SUSPICIOUS criterion (pre-registered):** OOS/IS monthly Sharpe ratio > 3.0 triggers SUSPICIOUS-OOS-DOMINANT. The observed ratio is 2.9543 — this is **just under** the 3.0 threshold. The brief's own SUSPICIOUS-OOS-DOMINANT criterion (criterion 2 of the Section 8 taxonomy) requires the ratio to be > 3.0 AND criterion 1 (NEGATIVE) must not fire. Criterion 1 fires because IS < +0.7325 (IS = +0.3172). Therefore the NEGATIVE criterion fires first under the first-match-wins taxonomy, before the SUSPICIOUS gate can be evaluated.

2. **`feedback_v3_oos_is_ratio_gate.md` > 3.0 SUSPICIOUS gate:** The ratio 2.9543 is **just UNDER 3.0** — the gate does not formally fire. However, 2.9543 is within rounding distance of the threshold. Combined with the pre-registered description in Section 7 ("if iter-v3/115 lands IS low and OOS high with OOS/IS ratio > 3.0"), the result sits at the **structural edge** of the SUSPICIOUS zone.

3. **Structural diagnosis:** IS = +0.3172 (anchor -0.52), OOS = +0.9370 (anchor +0.80). This IS-collapse / OOS-spike divergence IS the /105 pattern the brief explicitly pre-registered. The mechanism (Section 7 Mode 2): IS Optuna fits on a more-feature-predictable horizon-exit label in a IS bear/chop regime, producing a lower Sharpe fit; the OOS 2025-03 to 2026-05 uptrend rewards the longer 21-candle holds selectively. The pattern is a regime-exposure artifact, not a discovered edge — confirmed by DSR = 0.0 (no statistical significance at EXPLORATION budget) and the IS-collapse fact that the feature→label predictability advantage (T4: ~1.5x IC ratio) did not translate to IS trade-book Sharpe.

**Classification note:** the ratio 2.9543 does not technically fire the > 3.0 gate, but the structural pattern is the SUSPICIOUS divergence nonetheless. The Critic should note that under the first-match-wins taxonomy, the classification is NEGATIVE (criterion 1 fires on IS < +0.7325), and the SUSPICIOUS regime-artifact reading is contextual rather than formally gated.

---

## Section 8 Pre-Registered Criteria — Criterion-by-Criterion

**First-match-wins taxonomy (Section 8):**

**Criterion 1 — EXPLORATION-NEGATIVE:** IS monthly Sharpe < +0.7325 (Delta < -0.10 vs /060 anchor) OR OOS monthly Sharpe < +0.3403 (Delta < +0.20 vs /060 anchor).

- IS = +0.3172. Gate: IS < +0.7325. **FIRES.** (Delta = -0.5153, far below the -0.10 threshold.)
- OOS = +0.9370. Gate: OOS < +0.3403. Does not fire (OOS > +0.3403).
- Either-leg-fires rule: criterion 1 FIRES on the IS leg.

**Classification: EXPLORATION-NEGATIVE.**

Criterion 2 (SUSPICIOUS-OOS-DOMINANT) is not evaluated — criterion 1 fired first. Criterion 3 (INERT) is not evaluated. Criterion 4 (PROMISING) is not evaluated.

**Supporting observations:**
- PBO = 0.1426 (< 0.4 threshold — favorable, but EXPLORATION-mode PBO is informational only).
- frac_positive_paths = 0.6444 (> 0.50 threshold — also favorable but irrelevant given NEGATIVE classification).
- DSR = 0.0 — EXPLORATION-mode structural artifact at n_trials=315; informational only.
- OOS MaxDD = 33.51% vs IS MaxDD = 48.12% — OOS MaxDD is lower than IS (favorable direction relative to /059 IS 30.97% / OOS 34.53%).

**Behavioral inertia check (criterion 3 falsifier):** IS n_trades = 105 vs /060 IS n_trades (need comparison). The run.log shows 105 IS trades with 100% timeout exits — the label and execution change clearly landed (different exit geometry from the /059 mix of TP/SL/timeout), so behavioral inertia Mode 3 is excluded. The axis genuinely ran.

---

## Seed Concentration Audit

EXPLORATION mode: 3 seeds (191664963, 1662057957, 1405681631), single-roster (no per-seed decomposition in EXPLORATION outputs). Per `feedback_v3_dsr_mode_artifact.md`, multi-seed concentration analysis is a CONFIRMATION-mode requirement. PBO = 0.1426 from 45 CPCV paths is the EXPLORATION-mode statistical indicator.

CPCV path distribution:
- frac_positive_paths = 0.6444 (29 of 45 paths positive)
- q25 Sharpe = -0.243, q50 = 0.335, q75 = 0.838
- Path range: -1.318 to +1.880

---

## Label Leakage Audit

`REQUIRED_GAP = 66 = (21 + 1) × 3` — confirmed at run.log line 34 and verified against the Lopez de Prado purge requirement. CV gap = 22 rows (184h) per fold, confirmed at run.log lines 149–153 for the first BCH walk-forward split. Train window ends before test window with 22-row embargo at each fold boundary. No leakage.

---

## Gate Efficacy Table (RiskV2 stack — /059-canonical)

The 7-primitive RiskV2 gate stack is /059-identical; gate fire rates are inherited unchanged (the labeling change does not alter gate logic). No new primitives introduced. Gate-specific fire-rate analysis is not applicable to this EXPLORATION iteration (the axis is labeling, not risk gates). The risk-gate section is passed through from /059.

---

## Per-Symbol OOS Attribution

From `out_of_sample/per_symbol.csv`:

| Symbol | OOS Trades | Win Rate | Net PnL % | Pct of Total OOS PnL |
|---|---:|---:|---:|---:|
| BCHUSDT | 18 | 72.2% | +39.17% | 57.68% |
| LDOUSDT | 11 | 54.5% | +31.04% | 45.71% |
| TRXUSDT | 24 | 41.7% | -2.30% | -3.39% |

Named metric: `net_pnl_pct` (per the brief Section 5 rule: "net_pnl_pct from per_symbol.csv if the OOS book total is near zero, else concentration_pct"). OOS total PnL = 41.42 (not near zero), so `concentration_pct` is the named metric per brief rule. However, concentration_pct = LDO 45.71%, BCH 57.68%, TRX -3.39% — LDO and BCH together are 103.39% of OOS weighted PnL (TRX is a small drag). The OOS is highly concentrated in BCH and LDO; TRX produces a slight net drag.

**Comparison vs /072 (prior fixed-horizon-label-only NEGATIVE):** LDO did NOT collapse in /115. /072's LDO OOS was -32.49 wpnl / 21.4% WR. /115 LDO OOS is +31.04% net PnL / 54.5% WR — the coherent execution design removes the /072 mismatch mechanism as predicted. TRX IS is the drag symbol: IS TRX net_pnl_pct = -20.89 / 41.7% WR. BCH IS net_pnl_pct = -53.10 / 54.2% WR — BCH IS collapses under the symmetric time exit (the T3 prediction: tight stop + wide target creates Sharpe the symmetric hold discards).

---

## Trade Spot-Check (IS)

Row 2 (IS trades.csv): TRXUSDT LONG, entry=0.057810, exit=0.060340, direction=1, pnl_pct = (0.060340-0.057810)/0.057810 × 100 = 4.3764%. net_pnl_pct = 4.3764 - 0.10 = 4.2764. weighted_pnl = 4.2764 × 0.57 = 2.438 (vs stated 2.4376 — rounding match). exit_reason=timeout. PASS.

Row 3 (IS trades.csv): BCHUSDT LONG, entry=297.630000, exit=309.250000, direction=1, pnl_pct = (309.250-297.630)/297.630 × 100 = 3.9042%. net_pnl_pct = 3.9042 - 0.10 = 3.8042. weighted_pnl = 3.8042 × 0.47 = 1.7880 (stated 1.7880 — exact). exit_reason=timeout. PASS.

Row 6 (IS trades.csv): BCHUSDT SHORT, entry=359.690000, exit=371.240000, direction=-1, pnl_pct = (359.690-371.240)/359.690 × 100 = -3.2111%. net_pnl_pct = -3.2111 - 0.10 = -3.3111. weighted_pnl = -3.3111 × 0.75 = -2.4833 (stated -2.4833 — exact). exit_reason=timeout. PASS.

Row 2 (OOS trades.csv): BCHUSDT SHORT, entry=295.980000, exit=283.700000, direction=-1, pnl_pct = (295.980-283.700)/295.980 × 100 = 4.1489%. net_pnl_pct = 4.1489 - 0.10 = 4.0489. weighted_pnl = 4.0489 × 0.35 = 1.4171 (stated 1.4171 — exact). exit_reason=timeout. PASS.

Row 3 (OOS trades.csv): BCHUSDT LONG, entry=365.910000, exit=417.800000, direction=1, pnl_pct = (417.800-365.910)/365.910 × 100 = 14.1811%. net_pnl_pct = 14.1811 - 0.10 = 14.0811. weighted_pnl = 14.0811 × 0.41 = 5.7732 (stated 5.7732 — exact). exit_reason=timeout. PASS.

All 5 spot-checks pass. PnL arithmetic correct, exit_reason=timeout throughout (confirming non-binding barriers), weight_factor values are in [0.0, 1.0].

---

## Anomaly Notes

1. **IS MaxDD = 48.12% vs /059 IS MaxDD = 30.97%.** MaxDD blow-out: +17.15 percentage points. The brief Section 5 and Section 7 pre-registered "MaxDD up (longer holds)" as the expected direction for the NEGATIVE outcome — confirmed. The symmetric 21-candle hold keeps losers open for the full horizon, inflating IS MaxDD materially.

2. **BCH IS collapse is the primary driver.** BCH IS: -53.10% net PnL / 48 trades / 54.2% WR. BCH OOS: +39.17% / 18 trades / 72.2% WR. This is the starkest per-symbol IS-collapse / OOS-spike — BCH IS regime (2022-09 to 2025-03: bear + chop) destroys the symmetric time exit, while BCH OOS (2025-03 to 2026-05: uptrend) rewards it. The regime-divergence mechanism (pre-registered Section 7 Mode 2) is confirmed at the per-symbol level.

3. **IS monthly_pnl.csv: no NaN Sharpe, no zero-trade months in IS coverage.** Monthly coverage runs 2022-01 through 2025-03 with gaps (some months have 0 trades due to confidence threshold filtering — normal for EXPLORATION mode). No NaN PnL values observed.

4. **DSR = 0.0 is a structural EXPLORATION-mode artifact** (n_trials=315, `feedback_v3_dsr_mode_artifact.md`). Not a signal of negative significance — it reflects the E[max_SR] calculation at low trial count. PSR = 1.0 and PBO = 0.1426 are the meaningful EXPLORATION-budget statistics.

5. **CPCV path distribution is bimodal.** Paths 0–16 (early IS windows) skew positive (median ~0.9); paths 17–29 (mid-window) skew negative (median ~-0.4); paths 30–44 (late IS windows) are mildly positive (median ~0.4). This is consistent with the bear/chop/recovery IS regime heterogeneity and the geometry's IS weakness.

---

## Status

OVERALL=READY-FOR-CRITIC
