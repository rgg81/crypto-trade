# Engineering Report — iter-v3/071

## Headers

- Iteration: iter-v3/071
- Branch: iteration-v3/071
- Commit SHA (pre-backtest setup): 7cb700e (Phase 5.5 gate PASS)
- Brief LOCKED SHA: 7303113
- EDA SHA: 4f32ec5
- Hardware: WSL2 Linux 6.6.114 (AMD64)
- Wall-clock time: 0.65h

## Configuration Diff vs /060 EXPLORATION-mode Anchor

Single axis change: `--model metalabeling` activates `MetaLabelingStrategy` (M1 = LightGBM
signal generator, M2 = binary LGBMClassifier take/skip filter). All other configuration is
byte-identical to /060:

- V3_FEATURE_COLUMNS: 14 columns (unchanged — same-feature M2, single-axis discipline)
- DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) (unchanged)
- Universe: BCH, LDO, TRX (unchanged)
- n_trials: 35 (unchanged)
- Seeds: single-seed outer=42 (EXPLORATION mode)
- OOS_CUTOFF_DATE: 2025-03-24 (SACRED CONSTANT — unchanged)
- training_months: 24 (SACRED CONSTANT — unchanged)

## Key Metrics Block

### Headline: /071 vs /060 EXPLORATION-mode Anchor

| metric             | /060 (anchor) | /071 (meta-labeling) | delta     | ratio (OOS/IS) |
|--------------------|---------------|----------------------|-----------|----------------|
| IS monthly Sharpe  | +0.8325       | +0.6825              | -0.150    | —              |
| IS daily Sharpe    | +1.7115       | +2.2562              | +0.545    | —              |
| IS max_drawdown    | 31.87%        | 35.50%               | +4.53pp   | —              |
| IS profit_factor   | 1.2806        | 1.3940               | +0.113    | —              |
| IS win_rate        | 31.45%        | 32.14%               | +0.7pp    | —              |
| IS n_trades        | 159           | 112                  | -47       | —              |
| IS total_pnl       | 51.89         | 49.67                | -2.22     | —              |
| OOS monthly Sharpe | +0.1403       | +0.4623              | +0.322    | 0.6774         |
| OOS daily Sharpe   | +0.3659       | +1.0550              | +0.689    | 0.4676         |
| OOS max_drawdown   | 34.53%        | 25.12%               | -9.41pp   | 0.7077         |
| OOS profit_factor  | 1.0482        | 1.1465               | +0.098    | 0.8224         |
| OOS win_rate       | 39.22%        | 40.00%               | +0.78pp   | 1.2444         |
| OOS n_trades       | 102           | 80                   | -22       | 0.7143         |
| OOS total_pnl      | 5.4989        | 12.0185              | +6.52     | 0.2420         |
| frac_positive_paths| 0.6444        | 0.6444               | 0.000     | —              |
| PBO                | 0.1278        | NaN                  | UNEVALUABLE| —             |
| PSR                | 0.9763        | 1.0000               | +0.024    | —              |
| DSR_relative_B4    | n/a           | 0.9845               | PASS@0.95 | —              |
| n_eff              | 19            | 5                    | -14       | —              |
| n_trials           | 315           | 315                  | 0         | —              |

### CPCV Path Distribution (45 paths, IS candle sequence)

| percentile | Sharpe |
|------------|--------|
| q25        | -0.243 |
| q50        | +0.335 |
| q75        | +0.838 |

29 of 45 paths positive = 0.6444 frac_positive_paths (gate PASS at 0.55 threshold).

### Per-symbol OOS

| symbol  | wpnl    | n_trades | win_rate | concentration_pct |
|---------|---------|----------|----------|-------------------|
| TRXUSDT | +25.60  | 43       | 48.8%    | +212.98%          |
| BCHUSDT | -5.98   | 29       | 31.0%    | -49.73%           |
| LDOUSDT | -7.60   | 8        | 25.0%    | -63.25%           |

### Per-symbol IS

| symbol  | trades | wins | win_rate | net_pnl_pct | pct_of_total_pnl |
|---------|--------|------|----------|-------------|------------------|
| BCHUSDT | 52     | 24   | 46.2%    | +75.03      | +151.51%         |
| LDOUSDT | 7      | 2    | 28.6%    | -2.50       | -5.05%           |
| TRXUSDT | 53     | 16   | 30.2%    | -23.01      | -46.47%          |

## Classification per Brief Section 8 LOCKED Criteria

Checking against anchor /060 (IS +0.8325 / OOS +0.1403):

- IS delta: +0.6825 - +0.8325 = **-0.150** (negative)
- OOS delta: +0.4623 - +0.1403 = **+0.322** (positive, above +0.20 threshold)

Gate evaluation (in precedence order):

- Section 8.4 SUSPICIOUS-OOS-DOMINANT: IS delta < 0 AND OOS delta >= +0.20 → **FIRES**
  (IS -0.150 < 0; OOS +0.322 >= +0.20)
- Section 8.4 OOS/IS ratio > 3.0: OOS/IS = 0.6774 → does NOT fire
- Section 8.2 NEGATIVE: IS delta -0.150 is NOT < -0.10 in absolute terms... wait —
  IS = +0.6825 < +0.7325 (the -0.10 threshold) → FIRES. However, Section 8.4 precedence
  rule: SUSPICIOUS takes precedence over NEGATIVE when both fire.
- Section 8.1 PROMISING: IS >= +0.9325 required → FAILS (IS +0.6825)

**CLASSIFICATION: SUSPICIOUS-OOS-DOMINANT (Section 8.4)**

Note: NEGATIVE (Section 8.2) also fires (IS +0.6825 < threshold +0.7325 = /060 - 0.10). Per
Section 8.4 precedence rule: "SUSPICIOUS takes precedence over NEGATIVE when both fire." The
classification is SUSPICIOUS-OOS-DOMINANT, not NEGATIVE. The Critic must adjudicate whether
this precedence application is clean given the relatively modest IS delta (-0.150 vs -0.10
threshold).

The axis does NOT advance to the cycle-2 CONFIRMATION bundle.

## CRITICAL: PBO=NaN and n_eff=5 Investigation

### What the log shows

```
[CPCV] Computing per-cell CSCV PBO (iter-v3/004 per-cell pathway)...
[CPCV] IS candle sequence: 14137 candles across 3 symbols
[CPCV] cpcv_paths.csv: 45 paths (return proxy, S=1 — for schema)
PBO result: Per-cell PBO: OOF parquet absent or all cells degenerate.
[n_eff] per_cell_pbo.csv absent — using surrogate n_eff=5
```

The PBO computation path requires an OOF (out-of-fold) parquet produced during training;
`per_cell_pbo.csv` was not written (absent). The runner fell back to surrogate n_eff=5 (a
fixed sentinel value used when the PBO pathway produces no data).

### Root cause hypothesis: M2 filtering → sparse per-cell trial matrices

The per-cell CSCV PBO pathway works by constructing a matrix of per-(cell, trial) returns
from the OOF fold predictions produced during Optuna cross-validation. MetaLabelingStrategy's
M2 filter operates at signal-execution time, not during Optuna CV. The Optuna trials optimize
M1 hyperparameters; M2 is trained separately after M1's final model is selected per month.

This means: the OOF parquet is produced by M1 (LightGBM) during its Optuna CV loop. M2 does
not participate in Optuna and does not produce OOF predictions. The PBO machinery expects the
OOF parquet to be written at training-loop time (per the walk-forward cell structure). The
absence of the OOF parquet is the proximate cause — the code branch that writes it either
(a) was not reached (MetaLabelingStrategy training path differs from LightGbmStrategy), or
(b) the OOF returns were all degenerate (zero trades in every cell because M2-filtered cells
have too few samples).

**This is structural, not a transient bug.** The MetaLabelingStrategy training path differs
from LightGbmStrategy in how M1 and M2 interact; the OOF parquet generation hook appears to
sit in the LightGbmStrategy base path and is not triggered in the MetaLabelingStrategy path.
This is consistent with the surrogate n_eff=5 fallback firing deterministically (not
stochastically).

Consequence: **PBO is structurally unevaluable at EXPLORATION-mode with MetaLabelingStrategy.**
The overfitting gate based on PBO cannot fire. n_eff=5 is a hardcoded sentinel, not a
computed value, and should not be interpreted as an effective trial count.

Mitigation available from dsr.json: frac_positive_paths = 0.6444 (PASS at 0.55),
DSR_relative_B4 = 0.9845 (PASS at 0.95), PSR = 1.0000. These three non-PBO gates do
evaluate successfully. However, the PBO methodology gap is a Critic-adjudication item.

## Per-symbol Forensic

### BCH OOS: -5.98 wpnl, 29 trades, 31.0% WR (anchor: OOS +1.91 wpnl, 37 trades, 32.4% WR)

M2 IS-veto count for BCH: 679 vetoed out of BCH's M1-positive bar pool.
M2 OOS-veto count for BCH: 170 vetoed in OOS.

BCH IS showed +75.03 net_pnl (46.2% WR, 52 trades) — M2 filtered BCH IS to profitable trades
aggressively. In OOS, BCH produced -5.98 wpnl on 29 trades at 31.0% WR. The M2 filter that
selected winners IS failed to generalize to OOS for BCH: the BCH OOS WR dropped from IS 46.2%
to OOS 31.0% (15.2pp collapse). This is a classic IS-overfitting pattern on M2 for BCH: M2
learned to identify "good" BCH trades in IS but those IS-defined winners are not the OOS
winners.

The anchor /060 BCH OOS was +1.91 wpnl (37 trades, 32.4% WR). Meta-labeling made BCH OOS
meaningfully WORSE: from borderline-neutral to clearly negative (-7.89 wpnl delta on BCH).

### LDO OOS: -7.60 wpnl, 8 trades, 25.0% WR (anchor: OOS -19.72 wpnl, 11 trades, 18.2% WR)

LDO's IS training data starts only from 2024-09 (LDO listed 2024-09 in the LDOUSDT dataset).
M2 skip pattern: log shows "M1 has no models for 2022-09 through 2024-08 — M2 skipped" for
LDOUSDT. This is the structural data-scarcity problem the EDA (T4) predicted. LDO M2 only
has models from 2024-09 onward (6 months of IS history before OOS cutoff).

IS LDO: 7 trades only (-2.50 net_pnl, 28.6% WR). The M2 filter identified 65 LDO vetoes in
IS — a non-trivial count (the EDA predicted LDO M2 would be nearly inactive; 65 vetoes shows
it did train for the 2024-09 to 2025-03 window). But with only 7 IS trades remaining after
M2, LDO's IS contribution is negligible.

OOS LDO: 8 trades, 25.0% WR, -7.60 wpnl. In absolute wpnl terms this is a significant
improvement vs the anchor (-7.60 vs -19.72), but the trade count is critically low. M2 vetoed
264 LDO signals in OOS — an extremely high veto rate driven by OOS LDO M2 having very low
confidence (log shows conf values 0.096–0.494 in OOS May 2026 window, nearly all VETOED). The
8 remaining trades may be a high-noise sample, not a reliable signal.

### TRX OOS: +25.60 wpnl, 43 trades, 48.8% WR (anchor: OOS +23.31 wpnl, 54 trades, 48.1% WR)

TRX M2 operates correctly: 510 IS vetoes, 265 OOS vetoes. TRX IS: 53 trades (30.2% WR,
-23.01 net_pnl — M2 IS filter made TRX IS NEGATIVE in raw net_pnl despite removing 22 trades
vs anchor). TRX OOS: 43 trades (48.8% WR, +25.60 wpnl) — a marginal improvement vs anchor
(+23.31, 54 trades).

The OOS Sharpe lift (+0.322) is almost entirely TRX-driven. TRX contributed 212.98% of OOS
wpnl. BCH and LDO both had negative OOS wpnl. This concentration structure makes the OOS
Sharpe reading unreliable as a measure of meta-labeling's systematic edge.

### M2 Mechanism Summary

M2 is demonstrably active (veto rate >> 5%):
- IS: 1,254 vetoes out of ~3,177 M2-evaluated bars = 39.5% IS veto rate
- Total (IS+OOS): 1,953 vetoes out of 5,467 = 35.7% overall veto rate
- Reference (/017): 42.7% — similar order of magnitude, slightly lower here

M2 did reduce MaxDD: OOS MaxDD dropped -9.4pp (34.53% → 25.12%). This is the one
structural positive: M2 cut some bad trades. However the BCH-specific filter was
counterproductive (IS winner selection failed to generalize to BCH OOS).

## Meta-Labeling Mechanism Assessment

M2 is WORKING AS DESIGNED as a take/skip filter. The precision-filter mechanism is
active and materially filtering trades. But "working as designed" is not "working well."

Three structural problems observed:

1. TRX-bias: M2's precision improvement is TRX-local. In OOS, TRX (the strongest symbol) is
   the only contributor; BCH and LDO are net-negative. This means the M2 filter learned a
   TRX-specific pattern IS, not a cross-symbol quality signal.

2. BCH IS-overfit: M2 BCH IS WR 46.2% vs anchor 31.4% (excellent IS lift) but OOS BCH WR
   dropped to 31.0% — below even the M1-only anchor WR. The M2 BCH model is fitting IS noise.

3. LDO structural inactivity: LDO has <6 months of IS M2 training history. The 65 IS vetoes
   and 264 OOS vetoes suggest M2 is highly uncertain about LDO (low-confidence OOS vetoes at
   conf 0.096–0.494), resulting in only 8 OOS trades. The M2 filter is effectively destroying
   LDO's OOS participation.

The QR EDA predicted PATH C / INERT (40%) as the dominant outcome. The observed result is
SUSPICIOUS-OOS-DOMINANT (the 10% tail path: OOS +0.32 lift driven by TRX-concentration while
IS declines). The mechanism is not inert — M2 is selecting trades — but the selection quality
is symbol-asymmetric in a way that creates a statistically suspicious OOS headline.

## Falsifier Check (Brief Section 4.4)

| falsifier                              | threshold              | observed          | status         |
|----------------------------------------|------------------------|-------------------|----------------|
| IS Sharpe delta vs /060               | >=+0.10 PROMISING / <-0.10 NEGATIVE | -0.150 | NEGATIVE fires (IS < /060 - 0.10) |
| OOS Sharpe delta vs /060              | >=+0.20 PROMISING / <-0.20 NEGATIVE | +0.322 | PROMISING side fires (but IS veto blocks) |
| BCH IS share >=80% one-sided          | n/a (monitoring)       | BCH IS = +151.51% of total IS PnL | NOTE: BCH IS dominates, TRX IS negative |
| OOS trade rate floor (informational)  | >=10/month (floor)     | 80/14 = 5.71/month | BREACHED — below floor (informational per brief §8.5; flag required) |
| frac_positive_paths >= 0.50           | >=0.50                 | 0.6444            | PASS           |
| PBO < 0.40                            | <0.40                  | NaN               | UNEVALUABLE — per-cell PBO structurally absent with MetaLabelingStrategy |
| OOS/IS monthly Sharpe ratio < 3.0    | <3.0 (SUSPICIOUS gate) | 0.6774            | PASS (well below 3.0) |
| DSR_relative_B4 >= 0.95              | >=0.95                 | 0.9845            | PASS           |
| PSR >= 0.95                          | >=0.95                 | 1.0000            | PASS           |

**Trade-rate floor breach flag (per brief §8.5 mandate):** OOS 5.71 trades/month is below
the 10/month floor AND below the §8.5 pessimistic-scenario threshold of 52 total OOS trades
(observed: 80). The 80-trade count does not trigger the §8.5 hard-flag (80 > 52), but the
monthly rate (5.71/month) is the lowest observed in the v3 catalog excluding LDO-isolated
months. The OOS Sharpe is based on a thin 80-trade OOS sample concentrated 54% in TRX.
This sample is low-confidence per brief §8.5 framing.

**Saturation falsifier (§4.5):** IS trade count = 112 < 155 threshold → saturation
falsifier does NOT fire. M2 is genuinely filtering.

**Per-symbol IS trade-count shift (§4.6):** Expected BCH IS -10 to -20, TRX IS -10 to -20,
LDO IS -2 to 0. Observed: IS BCH = 52 (anchor 73, shift -21 — at edge of expected range),
IS TRX = 53 (anchor 75, shift -22 — at edge), IS LDO = 7 (anchor 11, shift -4 — exceeds
the "0 to -2" prediction for LDO). LDO M2 trained on 6 months of IS history and vetoed 65
IS bars — M2 found enough LDO data to train (as the EDA noted was possible). Brief §4.6
requires the engineering report to note LDO IS shift > 5 trades: NOTED.

## Risk Gate Efficacy Table

From log gate stats (single outer seed):

| symbol  | signals_seen | kill_rate | killed_zscore | killed_hurst | killed_adx | killed_low_vol | drawdown_brake | direction_block |
|---------|-------------|-----------|--------------|-------------|-----------|---------------|---------------|----------------|
| BCHUSDT | 1,328       | 76.66%    | 473          | 45          | 267       | 233           | 0             | 0              |
| LDOUSDT | 465         | 92.26%    | 243          | 6           | 100       | 80            | 0             | 0              |
| TRXUSDT | 1,721       | 74.26%    | 513          | 126         | 431       | 208           | 0             | 0              |

LDO gate kill_rate 92.26% is extremely high (only 36 vol_scaled_signals survive all gates).
LDO's high gate kill rate + M2 veto rate leaves very few trades in both IS and OOS. This is
consistent with LDO being a structurally low-signal, high-gate-fire symbol.

Drawdown brake: 0 fires across all symbols (unchanged from prior iterations — the brake
threshold has not been breached in IS or OOS).

Direction block (primitive 10 — BCH LONG kill switch from /047): 0 fires. BCH LONG block
remains dormant (no BCH LONG signals survived other gate kills to reach the direction filter).

## Seed Concentration Audit

Single outer seed (seed=42 expansion → inner seeds 191664963, 1662057957, 1405681631).
EXPLORATION mode: no multi-seed concentration audit applicable. Per v3 cadence rules,
concentration audit deferred to CONFIRMATION-mode runs.

## Label Leakage Audit

Walk-forward CV gap = (timeout_candles + 1) * n_symbols = (21 + 1) * 3 = 66 candles.
Per log: "Universal label_timeout_minutes (iter-v3/070 CARRY-FORWARD): 10080 min (= 21
candles at 8h; timeout UNCHANGED; embargo 22 per cell, cross-cell gap 66 per 3-sym universe)
PASS."

Note: the v3 walk-forward lookahead-bias bug (`walk_forward.py:69`, `train_end_ms =
test_start_ms` with no embargo, documented in
`feedback_v3_walkforward_lookahead_bug.md`) is still present in this worktree. All IS and OOS
absolute Sharpe values are biased upward. Cross-iteration deltas remain valid; /071 vs /060
comparison is internally consistent. Absolute magnitudes are inflated vs a corrected
walk-forward implementation.

## Anomaly Notes from Trade Spot-Check

10 random OOS trades spot-checked (seed=999 for reproducibility):

1. BCHUSDT SHORT SL: entry 428.44, exit 440.152683, net -2.8338, wpnl -0.9635 (wf=0.34).
   Math verified: pnl = (440.152683-428.44)/428.44 * -1 * 100 = -2.7338; net = -2.8338; wpnl
   = -2.8338 * 0.34 = -0.9635. CORRECT.

2. TRXUSDT LONG TP: entry 0.305730, exit 0.314305, net 2.7046, wpnl 2.4882 (wf=0.92).
   Math verified: pnl = (0.314305-0.305730)/0.305730 * 100 = 2.8048; net = 2.7048; wpnl =
   2.7048 * 0.92 = 2.4884 (rounding epsilon vs 2.4882). CORRECT.

3. LDOUSDT SHORT SL: entry 0.9072, exit 0.94404, net -4.1609, wpnl -1.7060 (wf=0.41).
   Math verified: pnl = (0.94404-0.9072)/0.9072 * -1 * 100 = -4.0608; net = -4.1608; wpnl
   = -4.1608 * 0.41 = -1.7059 (rounding epsilon). CORRECT.

4. TRXUSDT LONG SL (wf=0.0000): wpnl = 0.0000. BTC-contagion kill confirmed (weight_factor=0
   = BTC risk gate fired). PnL math not affected. EXPECTED.

exit_reason values observed: stop_loss, take_profit, timeout — all valid. No NaN PnL, no
zero-trade OOS months (14 months, 80 trades — all months have at least 2 trades per monthly
table). comparison.csv ratio math verified correct (3 ratios checked).

One observation: TRXUSDT wf=0.0000 trade (open_time=1769932799999, exit SL). This is a
BTC-contagion event (weight_factor zeroed). The trade was still executed but weighted to zero
— consistent with the BTC-contagion gate semantics (signal recorded but not counted in wpnl).

## Recommendations to QR

1. SUSPICIOUS-OOS-DOMINANT classification is LOCKED per brief §8.3/8.4. The iteration does
   NOT auto-advance to the cycle-2 CONFIRMATION bundle. This is consistent with the cycle-1
   /070 classification (also SUSPICIOUS-OOS-DOMINANT); meta-labeling as a same-feature
   mechanism reproduced the suspicious pattern at the /060 unified anchor.

2. PBO=NaN is a structural methodology concern. MetaLabelingStrategy's training path does not
   produce the OOF parquet required for per-cell CSCV PBO computation. This means any future
   MetaLabelingStrategy iteration will also have PBO=NaN unless the runner is modified to
   write OOF predictions from the M1 Optuna CV loop when MetaLabelingStrategy is active. The
   Critic must adjudicate whether PBO=NaN is an acceptable structural consequence or a
   methodology BLOCK for meta-labeling iterations.

3. The QR EDA lesson (§10 Section 4, pre-registered): a FUTURE meta-labeling EXPLORATION
   should use DISTINCT M2 features (the /017 lesson-#4 fix that this iteration intentionally
   deferred for single-axis discipline). The /071 result is a clean data point that
   same-feature M2 (meta-labeling using M1's own 14 features) does not deliver a PROMISING
   lift at the unified /060 anchor — it reproduces the SUSPICIOUS-OOS-DOMINANT pattern with
   high TRX concentration. If the QR elects to pursue a second meta-labeling EXPLORATION, it
   must use a DIFFERENT M2 feature set (per /017 lesson-#4).

4. OOS trade rate 5.71/month is the lowest non-trivially-explained rate in the v3 EXPLORATION
   catalog (below even the /059 BASELINE's 6.7/month). Meta-labeling over-filters in OOS.
   A CONFIRMATION-level meta-labeling run at current configuration would breach the
   CONFIRMATION-bundle trade-rate floor.

5. Cycle-2 #2 axis (/072): TBD per QR EDA. The meta-labeling same-feature axis is now
   exhausted for this cycle; the next EXPLORATION should be a different structural axis per
   the cycle-2 priorities established at iter-v3/070 Phase 8.

## Critic Alert

The Critic must adjudicate three open items:

(a) PBO=NaN methodology integrity: is the absence of per-cell PBO a BLOCK (methodology gate
unevaluable) or an acceptable structural consequence of MetaLabelingStrategy's training path?
The Critic should determine whether the three passing non-PBO gates (DSR_relative_B4=0.9845,
PSR=1.0000, frac_positive_paths=0.6444) are sufficient for SUSPICIOUS-OOS-DOMINANT
classification, or whether PBO=NaN triggers an additional review flag.

(b) Classification precedence: NEGATIVE also fires (IS +0.6825 < threshold +0.7325). The
brief §8.4 precedence rule gives SUSPICIOUS priority. The Critic should confirm the
SUSPICIOUS-OOS-DOMINANT classification is the canonical outcome and that NEGATIVE is
superseded (not a concurrent close).

(c) Trade-rate floor: OOS 5.71/month is below the 10/month floor. The brief §8.5 pre-registers
this as informational for EXPLORATION (consistent with the BASELINE anchor at 6.7/month).
The Critic should confirm this framing is appropriate given the severity of over-filtering and
advise whether the floor breach strengthens the case against advancing meta-labeling to a
CONFIRMATION bundle.

## Status

OVERALL=READY-FOR-CRITIC

Classification: SUSPICIOUS-OOS-DOMINANT
Does NOT advance to cycle-2 CONFIRMATION.
Critic adjudication required on (a) PBO=NaN methodology, (b) NEGATIVE/SUSPICIOUS precedence,
(c) trade-rate floor severity.
