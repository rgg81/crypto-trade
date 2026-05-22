# Engineering Report — iter-v3/072

## Headers

- Iteration: iter-v3/072
- Branch: iteration-v3/072
- Commit SHA (impl): `79990bb` (feat: fixed-horizon label_mode + ITERATION_LABEL v3-072)
- Gate SHA: `f2152fd` (docs: phase 5.5 gate PASS)
- Hardware: CPU (WSL2, linux 6.6.114.1)
- Wall-clock time: 0.66h (vs brief estimate 0.6–1.0h — within estimate)

## Configuration Diff vs Baseline (iter-v3/059)

| Parameter | BASELINE_V3.md (/059) | iter-v3/072 | Change |
|---|---|---|---|
| label_mode | `"triple_barrier"` | `"fixed_horizon"` | AXIS VARIABLE |
| ITERATION_LABEL | `"v3-071"` | `"v3-072"` | bumped |
| V3_FEATURE_COLUMNS | 14 features | 14 features (UNCHANGED) | none |
| V3_MODELS | BCH, LDO, TRX | BCH, LDO, TRX (UNCHANGED) | none |
| label_timeout_minutes | 10080 | 10080 (UNCHANGED) | none |
| compute_embargo_candles | 22 | 22 (UNCHANGED) | none |
| REQUIRED_GAP | 66 | 66 (UNCHANGED) | none |
| EXPLORATION_ENSEMBLE_SIZE | 3 | 3 (UNCHANGED) | none |
| n_trials | 35 | 35 (UNCHANGED) | none |
| Risk gates (7 primitives) | as at /059 | UNCHANGED | none |
| BacktestConfig TP/SL/timeout | as at /059 | UNCHANGED | none |

Single-axis discipline: confirmed. The one substantive change is `label_mode="fixed_horizon"` threaded from `run_baseline_v3.py:1506` through `_build_v3_model common_kwargs` into `LightGbmStrategy.__init__` and thence into `label_trades`. The pre-flight assertion at `run_baseline_v3.py:754-760` confirms `_p13_lgbm.label_mode == "fixed_horizon"` before training begins. Trade-exit barriers (`BacktestConfig.stop_loss_pct`, `take_profit_pct`, `timeout_minutes`) are UNCHANGED — only the training label rule changed, not the execution layer.

## Key Metrics Block

### Headline (vs /060 EXPLORATION-MODE anchor)

| Metric | /060 (anchor) | /072 | Δ | Ratio |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | +0.8325 | **-0.3139** | **-1.1464** | — |
| OOS monthly Sharpe | +0.1403 | **-0.6557** | **-0.7960** | — |
| IS daily Sharpe | +1.7115 | -0.7059 | -2.4174 | — |
| OOS daily Sharpe | +0.3659 | -1.9399 | -2.3058 | — |
| OOS/IS monthly Sharpe ratio | 0.169 | **2.089** | — | (both negative — ratio not meaningful as overfitting indicator) |
| IS profit_factor | 1.2806 | **0.9016** | -0.379 | LOSING IS |
| OOS profit_factor | 1.0482 | **0.7856** | -0.263 | LOSING OOS |
| IS win_rate | 31.4465% | 27.5676% | -3.88pp | — |
| OOS win_rate | 39.2157% | 32.5301% | -6.69pp | — |
| IS MaxDD | 30.97% | 44.81% | +13.84pp | — |
| OOS MaxDD | 34.53% | **58.06%** | **+23.53pp** | — |
| IS monthly Calmar | — | -0.4891 | — | — |
| OOS monthly Calmar | — | -0.4466 | — | — |
| IS n_trades | 159 | 185 | +26 | — |
| OOS n_trades | 102 | 83 | -19 | — |
| IS total_pnl | — | -21.91 | — | — |
| OOS total_pnl | — | -25.93 | — | — |
| DSR | 0.0 | 0.0 | — | structural at v3 volume |
| DSR_relative_B4 | n/a | **0.0000** | — | FAIL |
| PBO | 0.1278 | 0.1426 | +0.015 | — |
| PSR | 0.9763 | **0.0000** | -0.976 | FAIL |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | 0.000 | architecture-invariant |
| n_trials | 315 | 315 | 0 | — |
| n_eff | — | 16 | — | — |

### Comparison.csv values (byte-exact)

From `reports-v3/iteration_v3-072/comparison.csv`:

```
metric,in_sample,out_of_sample,ratio
monthly_sharpe,-0.3139,-0.6557,2.0886
daily_sharpe,-0.7059,-1.9399,2.7481
max_drawdown,44.8080,58.0584,1.2957
profit_factor,0.9016,0.7856,0.8714
win_rate,27.5676,32.5301,1.1800
n_trades,185,83,0.4486
total_pnl,-21.9136,-25.9282,1.1832
monthly_calmar,-0.4891,-0.4466,0.9132
weighted_pnl_total,-21.9136,-25.9282,1.1832
dsr,0.000000,—,—
pbo,0.1426,—,—
psr,0.0000,—,—
n_trials,315,—,—
n_effective_trials,16,—,—
```

Per-symbol OOS section:
```
BCHUSDT,-0.6579,28,35.7,2.54
LDOUSDT,-32.4913,14,21.4,125.31
TRXUSDT,7.2210,41,34.1,-27.85
```

OOS wpnl cross-check: -0.6579 + -32.4913 + 7.2210 = **-25.9282** matches `weighted_pnl_total`. PASS.
IS trade count: BCH 83 + LDO 17 + TRX 85 = **185** matches `n_trades`. PASS.
OOS trade count: BCH 28 + LDO 14 + TRX 41 = **83** matches `n_trades`. PASS.

## Behavioral-Effect Audit (Section 4.5 confirmation)

Brief Section 4.5 predicted the IS trade roster changes by ≥ 15% of trades (≥ 24 of 159 IS trades differ). Observed:

| Symbol | /060 IS trades | /072 IS trades | Delta | Per-symbol within ±3? |
|---|---:|---:|---:|---|
| BCH | 73 | 83 | +10 | NO (10 > 3) |
| LDO | 11 | 17 | +6 | NO (6 > 3) |
| TRX | 75 | 85 | +10 | NO (10 > 3) |
| **Total** | **159** | **185** | **+26** | — |

Total IS trade delta = +26 (+16.4% vs 159). Exceeds the ≥15% behavioral-effect prediction. Saturation falsifier does NOT fire (all three per-symbol deltas exceed ±3, total count delta exceeds ±3, IS Sharpe delta is -1.1464 far beyond ±0.03). The `label_mode="fixed_horizon"` switch took effect and genuinely retrained different models.

## Label Activation Verification

Pre-flight assertion at `run_baseline_v3.py:754-760` confirmed `_p13_lgbm.label_mode == "fixed_horizon"` before the first training call. The assertion would have hard-aborted the runner if the wiring failed — the run completed successfully with 185 IS and 83 OOS trades, which is a material change from /060, consistent with the re-labeling reaching `label_trades`. The saturation falsifier (both Sharpe and trade-count conditions) does not fire, confirming the label switch was active.

## Ensemble Configuration

`ensemble_summary.json` confirms EXPLORATION mode, `ensemble_size=3`, seeds `[191664963, 1662057957, 1405681631]` (outer=42 lineage), matching the brief's specified run mode. n_trials = 315 = 35 × 3 symbols × 3 seeds.

## IS Zero-Trade Month Check

IS monthly_pnl.csv: 37 months, zero zero-trade months (minimum trade count per month = 1). PASS.

## OOS Trade-Rate Floor

OOS n_trades = 83. The Section 8.5 thin-sample flag fires if OOS count falls below 52 (50% of /060's 102). 83 ≥ 52: PASS (informational — the iteration is NEGATIVE regardless; this flag was not needed).

## Per-symbol Forensic

### IS per-symbol detail

| Symbol | /060 trades | /072 trades | /060 WR | /072 WR | /060 net_pnl | /072 net_pnl |
|---|---:|---:|---:|---:|---:|---:|
| BCH | 73 | 83 | 45.2% | 38.6% | +79.45% | +11.78% |
| LDO | 11 | 17 | 27.3% | 23.5% | -11.44% | -35.58% |
| TRX | 75 | 85 | 29.3% | 32.9% | -23.04% | -14.84% |

BCH IS net_pnl collapsed from +79.45% to +11.78% (Δ = -67.67pp, a 85% reduction). Section 4.7 pre-registered the BCH sensitivity check: "if BCH IS net_pnl falls > 30% vs /060's +79.45% while LDO/TRX are flat, the headline IS Sharpe will likely collapse." BCH fell 85%; the /063/064 pattern repeated. The IS Sharpe collapse is dominated by the BCH IS implosion.

LDO IS net_pnl regressed from -11.44% to -35.58% (Δ = -24.14pp). Section 4.6 pre-registered a per-symbol falsifier: "if LDO IS net_pnl REGRESSES (falls below /060's -11.44%) while BCH/TRX are roughly flat, the core hypothesis is falsified for LDO specifically." LDO IS regressed — and BCH/TRX are not flat (both also regressed). The LDO falsifier fires.

TRX IS net_pnl improved from -23.04% to -14.84% (+8.20pp). TRX is the only IS improvement, but it is insufficient to offset BCH and LDO collapses. TRX WR improved from 29.3% to 32.9% (+3.6pp).

### OOS per-symbol detail

| Symbol | /060 wpnl | /072 wpnl | /060 WR | /072 WR | /060 trades | /072 trades |
|---|---:|---:|---:|---:|---:|---:|
| BCH | +1.91 | -0.66 | 32.4% | 35.7% | 37 | 28 |
| LDO | -19.72 | **-32.49** | 18.2% | 21.4% | 11 | 14 |
| TRX | +23.31 | +7.22 | 48.1% | 34.1% | 54 | 41 |

LDO OOS: -32.49 wpnl at 21.4% WR, 125.31% concentration — CATASTROPHIC. The axis was intended to rescue LDO (Section 1, Section 2.5), but LDO went from a mild OOS drag to a catastrophic OOS loss. The fixed-horizon label materially worsened LDO's OOS performance.

TRX OOS: +7.22 (positive), but down from +23.31 at /060. TRX WR collapsed from 48.1% to 34.1% (-14.0pp). TRX is the one surviving positive contributor but it lost the dominant portion of its /060 edge.

BCH OOS: -0.66 (near-flat negative), down from +1.91.

## Root Cause — Label-Execution Mismatch

The fixed-horizon label trains the M1 LightGBM to predict "is the 21-candle realized forward return positive?" The backtest execution STILL exits trades at TP/SL/timeout barriers (`BacktestConfig.stop_loss_pct=4.0`, `take_profit_pct=8.0`, `timeout_minutes=10080`). These are two independent mechanisms.

A trade can have a POSITIVE 21-candle net forward return yet hit the SL barrier before the 21st candle. The model predicts `+1` (label is positive) → takes a LONG position → price touches SL at candle 3 → trade closes at a loss. The model was trained to predict the net 21-candle outcome; the execution realized a SL exit on candle 3.

The triple-barrier label, by contrast, labels a candle by which barrier is touched FIRST: TP, SL, or timeout. A candle where the SL is touched first before the TP gets label `−1` (or the fwd-return sign at timeout if neither TP/SL is hit). This label is CONSISTENT with the execution — both the label and the execution use the same barrier-first-hit mechanism. The model trained on triple-barrier labels has learned to predict the SAME outcome the backtest execution will realize.

This is the fundamental mismatch: fixed-horizon training target ≠ execution barrier reward. The EDA showed the FH-21 label is "cleaner" in label-space (larger directional spread, higher persistence). But label-space quality is only relevant if the label target is the same as the execution reward. It is not.

The Section 3.2 disambiguation ("the training label and the execution rule are independent degrees of freedom") was accurate as stated but it contained the critical assumption — "the hypothesis is that a cleaner training label produces a better direction model" — that this EXPLORATION tested and DISPROVED. Cleaner IS NOT sufficient if the label target is decoupled from the execution reward function.

This is the QR's pre-registered Section 7 NEGATIVE failure mode: "a candle whose forward path hit the stop first is genuinely a worse long setup, and the 2:1 TP:SL asymmetry tells the model 'only label LONG the setups where a 2×ATR move precedes a 1×ATR move'... If the path information was load-bearing, the M1 model trained on the fixed-horizon label will be WORSE at distinguishing tradeable setups." Confirmed. The path information IS load-bearing because the execution is barrier-based, not fixed-horizon.

## Hypothesis Falsification

QR hypothesis (Section 1): "replacing the ATR triple-barrier label with a fixed-horizon return-sign label lifts both IS and OOS monthly Sharpe vs the /060 anchor by giving the M1 LightGBM a directionally cleaner training target."

EDA rationale: FH-21 separates forward drift 30–50% more sharply at the matched 21-candle horizon. Label persistence higher (0.788 vs 0.727). LDO's triple-barrier label 69% SL-saturated and 41% already effectively fixed-horizon.

Observed outcome: IS Sharpe -0.3139 (Δ -1.1464), OOS Sharpe -0.6557 (Δ -0.7960). Both IS and OOS went NEGATIVE. IS PF = 0.90 (losing). OOS PF = 0.79 (losing). OOS MaxDD = 58.06% (+23.5pp).

The EDA's directional-spread improvement in LABEL SPACE did not translate to better trading because the label target is decoupled from the execution reward. Sharper label separation ≠ better model when the training objective and the execution objective are measuring different quantities.

QR predicted NEGATIVE with 35% probability. The NEGATIVE outcome is confirmed. The magnitude is catastrophic (IS Δ = -1.15 far exceeds the -0.10 threshold; OOS Δ = -0.80 far exceeds the -0.20 threshold). The 35% probability bucket was correctly the most-likely single outcome.

LDO-specific falsifier (Section 4.6): LDO IS net_pnl regressed from -11.44% to -35.58% — FIRES. The axis that was designed to rescue LDO's SL-saturated label made LDO substantially worse in both IS (-35.58%) and OOS (-32.49 wpnl). The fundamental error: the SL-saturation diagnostic showed a LABEL QUALITY problem, but the fix (fixed-horizon label) broke the training-execution alignment. LDO's SL saturation is a structural feature of LDO's volatility profile under the execution barriers, not a problem fixable by changing the training label while keeping the same execution barriers.

BCH IS sensitivity (Section 4.7): BCH IS net_pnl fell from +79.45% to +11.78% (−67.67pp, 85% reduction). The pre-registered flag was "fall > 30% vs /060's +79.45%." A 85% reduction is far above the flag threshold. The /063//064 BCH-collapse pattern repeated.

## Section 4.4 Falsifier Check (per brief)

| Falsifier | Threshold | Observed | Status |
|---|---|---|---:|
| IS Sharpe shift | > -0.20 | -1.1464 | FAILS — catastrophic |
| OOS Sharpe shift | > -0.20 (brief 8.2) | -0.7960 | FAILS — catastrophic |
| PSR | > 0.95 | 0.0000 | FAILS |
| DSR_relative_B4 | > 0.95 | 0.0000 | FAILS |
| frac_positive_paths | ≥ 0.50 | 0.6444 | PASS (architecture-invariant) |
| OOS/IS ratio | < 3.0 | 2.089 | PASS (both negative — ratio is not meaningful as overfitting indicator here) |

Note on the OOS/IS ratio: the ratio 2.089 is below 3.0 so the pre-registered SUSPICIOUS gate (Section 8.4) does NOT fire. Both IS and OOS are negative, so the "SUSPICIOUS-OOS-DOMINANT" sub-mode (IS Δ < 0 AND OOS Δ ≥ +0.20) also does not fire (OOS Δ = -0.80, not ≥ +0.20). Classification is cleanly NEGATIVE under Section 8.2 (both IS and OOS gates fire independently).

Classification precedence (Section 8.4): SUSPICIOUS > NEGATIVE > INERT. SUSPICIOUS requires ratio > 3.0 or SUSPICIOUS-OOS-DOMINANT. Neither fires. Classification = NEGATIVE.

## MaxDD Watch (Section 5 pre-registration)

Section 5 pre-registered: "if OOS MaxDD widens > 5pp vs /060's 35.78% AND the OOS Sharpe does not clear the PROMISING band, the Engineering report flags the labeling change as having traded drawdown control for nothing."

OOS MaxDD widened by +23.53pp (34.53% → 58.06%). OOS Sharpe did not clear the PROMISING band (it went negative). The flag FIRES: the fixed-horizon label traded away drawdown control for a 23.5pp MaxDD widening without any OOS Sharpe improvement. As hypothesized in Section 5, the fixed-horizon label may select setups with deeper interim drawdowns (trades that get stopped before the net-positive horizon completes), consistent with the IS PF = 0.90 and OOS PF = 0.79 (more stopped-out trades from setups admitted by the label that the execution barriers close at a loss).

## Seed Concentration Audit

EXPLORATION mode: 3 seeds (ensemble_size=3), single outer run. No multi-seed dispersion audit applies (that is a CONFIRMATION-mode requirement). The trade roster and metrics above are from the single 3-seed EXPLORATION pass.

## Label Leakage Audit

The fixed-horizon label scans 21 candles forward from the candidate candle to assign a training label. The walk-forward embargo = `compute_embargo_candles(10080, 480) = 22` candles ≥ 21-candle label horizon. Training candles are purged by 22 candles from the test window boundary (`train_end_ms = test_start_ms - embargo_ms`). The 22-candle embargo strictly covers the 21-candle label horizon — no training candle's fixed-horizon label can reach into the test window. This is byte-identical to the triple-barrier embargo (same timeout, same embargo math). No label leakage risk introduced by the label mode change.

## Gate Efficacy Table

All 7 risk primitives are UNCHANGED from /060. The per-primitive fire rates are not separately tabulated here (only the gate configuration changed — re-trained models under a different label will produce different signal confidences, changing gate hit rates). The `per_regime.csv` output consolidates all regime information: IS regime "unknown" (185 trades, 34.6% WR, -38.64% net_pnl, Sharpe -0.043); OOS regime "unknown" (83 trades, 32.5% WR, -42.88% net_pnl, Sharpe -0.129). No gate configuration changed.

## Anomaly Notes

The LDO OOS wpnl of -32.4913 against a 125.31% concentration flag is the largest per-symbol OOS loss in v3 EXPLORATION history. The OOS MaxDD of 58.06% is the largest in v3 EXPLORATION history. Both are a direct consequence of the label-execution mismatch. No data integrity anomalies were found — trade counts are consistent (IS 83+17+85=185, OOS 28+14+41=83), wpnl sums cross-check (-0.6579-32.4913+7.2210=-25.9282). The results are internally consistent; they are catastrophically bad, not corrupted.

No spot-check anomalies: the IS monthly PnL series shows no zero-trade months. The direction of the effect (lower WR, lower PF, higher MaxDD) is mechanically consistent with the label-execution mismatch hypothesis (model admits more setups that get stopped before the 21-candle horizon completes).

## Methodology Lesson for QR

Alternative-labeling axes must verify the label target is CONSISTENT with the backtest execution barrier structure. The EDA showed the fixed-horizon label is directionally cleaner in LABEL SPACE. But "cleaner in label space" is only actionable if the label space matches the execution reward space.

If a future iteration wants fixed-horizon execution, it would ALSO need to change the backtest execution to fixed-horizon exits (exit at candle 21 regardless of TP/SL). That is a 2-axis change, which violates single-axis discipline. The viable design is: triple-barrier label + triple-barrier execution (current baseline) OR fixed-horizon label + fixed-horizon execution (a future multi-axis iteration that would require a separate brief). The hybrid (fixed-horizon label + triple-barrier execution) tested here is structurally incoherent as a training-execution pair.

## Classification

**NEGATIVE (catastrophic)**

Per brief Section 8.2 (disjunctive OR): IS Δ = -1.1464 < -0.10 (FIRES) AND OOS Δ = -0.7960 < -0.20 (FIRES). Both gates fire independently. SUSPICIOUS gate does NOT fire (OOS/IS ratio 2.089 < 3.0; SUSPICIOUS-OOS-DOMINANT requires OOS Δ ≥ +0.20 which is not met). Classification = NEGATIVE under Section 8.2.

Axis CLOSED: fixed-horizon return-sign labeling (21-candle horizon). The axis family "label-execution decoupled" is structurally invalid for the current ATR-barrier execution layer. The brief Section 8.2 closing condition fires.

## Status

OVERALL=READY-FOR-CRITIC
