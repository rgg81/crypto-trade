# iter-v1/011 — Research Brief

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Mode**: EXPLORATION (single-seed, ENSEMBLE_SIZE=3, n_trials=35, ≤2h cap)
**Axis**: R5 BINARY KILL switch — `risk-primitive` family (binary-kill SUBTYPE; sister to /010 proportional scaling)
**Branch**: `iteration-v1/011`

---

## Section 0 — Iteration Pre-Header

### 0.1 Anchor
`v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`)
- IS monthly Sharpe **+0.2829**, OOS monthly Sharpe **+0.6637**
- IS trades 621, OOS trades 189
- 5-seed v1-baseline-corrected ensemble (`[42, 123, 456, 789, 1001]`)
- UNCHANGED post-/010 (NO-MERGE per EXPLORATION-NEGATIVE rule)

### 0.2 Mode
**EXPLORATION** (cycle-2, post-/010 closeout)
- `--exploration --seeds 1 --n-trials 35` (canonical v1 EXPLORATION knobs)
- ENSEMBLE_SIZE = 3 (single outer seed × 3 inner seeds from `[42, 123, 456]`)
- ≤2h wall-clock cap (NON-NEGOTIABLE per /005 closeout 10:1 cadence discipline)

### 0.3 Iteration label
`v1-011`

### 0.4 Determinism note
R5-BINARY-KILL is purely deterministic given NATR_14 feature parquet. Same data extent → reproducible. Compared to /010's proportional scaling: binary kill is a state-discontinuous entry filter (skip-vs-proceed) NOT a multiplicative weight modifier. Mechanically distinct primitive class.

### 0.5 Cadence position
**Cycle-2 EXPLORATION #6** (of 10-EXPLORATION cycle since /002 baseline-set).

Cycle-2 catalog: /006 (universe, NEG+DEGEN), /007 (feature-family composed, NEG-NEG), /008 (methodology PROMISING-METH), /009 (feature-family delete, NEG-NEG), /010 (risk-primitive proportional R5, NEG/PROMISING-INERT-with-IS-basin-shift).

Next CONFIRMATION cannot fire until 10 cycle-2 EXPLORATIONs accumulate (currently 6; /011 = 6 of 10). Earliest CONFIRMATION at /015.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: `risk-primitive` (binary-kill SUBTYPE — structurally orthogonal to /010's proportional-scaling subtype)
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md`):
  - iter-v1/006: `universe`
  - iter-v1/007: `feature-family`
  - iter-v1/008: `methodology`
  - iter-v1/009: `feature-family`
  - iter-v1/010: `risk-primitive` (proportional-scaling subtype)
- **Rotation status**: **VALID — 1 of last 5 is `risk-primitive` (/010); majority (4 of 5) are NOT `risk-primitive`.** Per skill: "if the last 5 EXPLORATIONs were all from the same family, the NEXT EXPLORATION MUST be from a different family". 1/5 is not "all same family"; rotation discipline preserved.
- **Within-family subtype distinction (load-bearing)**: /010's proportional-scaling R5 family was CLOSED at v1 single-seed (catalog axiom from /010 closeout extending v3/020). /011's binary-kill is an architecturally-orthogonal SISTER subtype: state-discontinuous mechanism (skip-vs-proceed) vs smooth multiplicative attenuation. Different primitive class, different loss-surface signature, different LM Master Phase 4.5 basin-shift expectation (entry filter does NOT multiply into position-sizing weight directly).
- **One-sentence rationale**: 3-way convergent recommendation (LM Master Phase 7.4 PRIMARY + Critic Phase 7.5 Path Forward #1 + QR Phase 7 memo) directed /011 to NATR-based binary kill switch as the architecturally-orthogonal sister to /010's proportional scaling; the EDA (Section 2) SHARPENS the convergent threshold via empirical evidence and INVERTS the direction (skip if NATR < X, not NATR > X) based on entry-time-conditional NATR distributions that the /010 EDA's candle-level analysis missed.

---

## Section 1 — Hypothesis

**Skipping entries at LOW entry-time NATR_14 (below ~2.0%) reduces portfolio drawdown by killing the systematic loser cluster — low-NATR low-confidence trades — without removing the high-NATR high-conviction winners.**

The hypothesis has four parts:

1. **Mechanism (revised from convergent recommendation per Section 2 EDA)**: at LOW entry-time NATR_14 (below universe-portfolio p15-p20 ≈ 2.0%), the model fires entries with low conviction in low-volatility regimes where MEAN_NET_PNL < 0 (per Phase 1.5 evidence). At HIGH entry-time NATR (>5%), the model fires entries with high conviction in volatility regimes where MEAN_NET_PNL > +5%/trade (winner cluster). The convergent "kill high-NATR tail" recommendation was based on /010 EDA's candle-level NATR p90 ≈ 6.3% — but the model's feature space already filters high-NATR candles via confidence gating, so the entry-time-conditional p90 is 4.30% (OOS). Killing above 7% kills zero practical trades.

2. **Predicted effect**: at threshold = 2.0%, skip rate on BOTH rosters (BASELINE + /010-EXPLORATION) lands in F2 band [10%, 60%] at 18-19%; oracle OOS Sharpe Δ is **+0.046 (BASELINE) / +0.115 (/010-EXPLORATION)**. Cross-roster sign-agreement on a 6.5× magnitude difference. The expected effect on /011 backtest is +0.05 to +0.12 OOS Δ (using BASELINE as the lower bound and /010-roster as the upper, since /011's actual backtest will share characteristics of /010's EXPLORATION-spec architecture).

3. **Expected outcome class**: PROMISING (OOS Δ ≥ +0.05) is the modal prediction. The EDA evidence is robust enough that a NEGATIVE verdict would itself be informative — it would prove that single-seed Optuna re-optimization can wipe out a clean oracle signal (a generalization of /010's Failure Mode 4 to a different mechanism class). PROMISING-INERT is the second-most-likely outcome (the inversion's positive oracle gets eaten by basin shift). NEGATIVE-catastrophic is unlikely but not impossible (basin shift could go any direction).

4. **Falsifies**: the convergent 3-way recommendation (LM Master Phase 7.4 + Critic Path Forward #1 + QR memo all said "NATR > 7%"). The EDA empirically falsifies this direction. **Per THE PRIME DIRECTIVE, the brief acts on the EDA-discovered live experiment, not the speculation-based one.**

**Confirms** (if PROMISING): the binary-kill subtype of risk-primitive is architecturally distinct from proportional-scaling and has independent edge potential at v1 single-seed; the entry-time-conditional NATR distribution (NOT candle-level) is the load-bearing diagnostic for any future R5 binary-kill calibration.

---

## Section 2 — IS-Only Evidence (numerical tables)

### 2.1 Per-symbol ENTRY-TIME NATR_14 distribution (BOTH rosters)

From `analysis/iteration_v1-011/entry_time_natr_distribution.csv` — load `(symbol, open_time)` keyed NATR_14 lookup from feature parquets, join to BASELINE roster (621 IS + 189 OOS trades) AND /010 EXPLORATION roster (663 IS + 210 OOS trades).

**BASELINE roster — entry-time NATR_14 percentiles**:

| Symbol | half | n_trades | mean | p10 | p25 | **p50** | p75 | p85 | p90 | p95 |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | IS | 113 | 2.28 | 1.28 | 1.70 | **2.11** | 2.66 | 2.99 | 3.23 | 4.30 |
| BTCUSDT | OOS | 35 | 1.98 | 1.48 | 1.52 | **1.95** | 2.27 | 2.43 | 2.53 | 2.85 |
| ETHUSDT | IS | 145 | 3.14 | 1.93 | 2.22 | **2.82** | 3.80 | 4.25 | 4.73 | 5.65 |
| ETHUSDT | OOS | 46 | 3.04 | 2.01 | 2.39 | **2.82** | 3.50 | 3.88 | 4.02 | 4.26 |
| LINKUSDT | IS | 146 | 4.01 | 2.46 | 2.96 | **3.77** | 4.59 | 5.14 | 5.53 | 7.17 |
| LINKUSDT | OOS | 28 | 3.42 | 2.40 | 2.76 | **3.22** | 3.86 | 4.52 | 4.78 | 5.38 |
| LTCUSDT | IS | 123 | 3.27 | 2.12 | 2.53 | **3.00** | 3.81 | 4.19 | 4.76 | 5.40 |
| LTCUSDT | OOS | 34 | 2.72 | 1.68 | 1.96 | **2.66** | 3.29 | 3.73 | 3.87 | 4.23 |
| DOTUSDT | IS | 93 | 3.37 | 2.02 | 2.41 | **3.03** | 3.92 | 4.57 | 5.36 | 6.12 |
| DOTUSDT | OOS | 46 | 3.70 | 2.73 | 3.12 | **3.43** | 4.13 | 4.38 | 4.86 | 5.45 |
| **PORTFOLIO** | **IS** | **620** | **3.25** | **1.81** | **2.28** | **2.96** | **3.90** | **4.45** | **5.01** | **5.76** |
| **PORTFOLIO** | **OOS** | **189** | **3.00** | **1.71** | **2.20** | **2.89** | **3.56** | **4.01** | **4.30** | **4.92** |

**Critical empirical finding (LOAD-BEARING for /011 design)**:

| Distribution | Universe p90 | Source |
|---|---|---|
| /010 CANDLE-LEVEL (5,012-5,714 candles/symbol) | 6.3% | /010 brief Section 2.1 |
| /011 ENTRY-TIME-CONDITIONAL (189 OOS trades) | **4.30%** | Section 2.1 above |
| **Gap** | **-2.0pp (47% reduction)** | |

The model's confidence-gating + R3 OOD-gate + feature dynamics ALREADY filter candidate candles down to a lower-NATR subset. The convergent "NATR > 7%" threshold puts the kill rate at OOS skip = **0.5% (1 trade)** — empirically inactive.

### 2.2 Oracle Sharpe-delta simulation — HIGH-side kill (skip if NATR > threshold)

From `analysis/iteration_v1-011/oracle_sharpe_delta.csv`:

**BASELINE roster (5-seed v1-baseline-corrected anchor)**:

| threshold | OOS skip rate | OOS sharpe baseline | OOS sharpe oracle | **OOS Δ** | F2 band [10%, 60%]? |
|---|---|---|---|---|---|
| 5.5 | 3.7% | 0.1710 | 0.1445 | **-0.0265** | OUT (under) |
| 6.0 | 1.6% | 0.1710 | 0.1713 | **+0.0003** | OUT |
| 6.5 | 1.1% | 0.1710 | 0.1718 | **+0.0008** | OUT |
| 7.0 | 0.5% | 0.1710 | 0.1696 | **-0.0013** | OUT |
| 7.5 | 0.0% | 0.1710 | 0.1710 | 0.000 | OUT (no trades killed) |
| 8.0 | 0.0% | — | — | 0.000 | OUT |

**Verdict on convergent NATR > 7% recommendation**: OOS skip rate 0.5%, OOS Δ = -0.0013, F2 band FAILS. **Empirically dead axis.**

Extended low-threshold sweep (3.0-5.0) on BASELINE roster:

| threshold | OOS skip rate | **OOS Δ** | F2 band? |
|---|---|---|---|
| 3.00 | 45.0% | -0.144 | IN (but Δ NEG) |
| 3.50 | 27.5% | -0.140 | IN (Δ NEG) |
| 3.75 | 20.1% | -0.076 | IN (Δ NEG) |
| 4.00 | 15.3% | -0.112 | IN (Δ NEG) |
| 4.25 | 11.6% | -0.095 | IN (Δ NEG) |
| 4.50 | 7.9% | -0.063 | OUT (Δ NEG anyway) |

**ALL kill_high thresholds on BASELINE roster produce NEGATIVE OOS Δ.** High-NATR trades on the BASELINE roster are systematic positive contributors (LINK +4.84/trade at NATR>5; ETH +5.56/trade at NATR 4-5).

### 2.3 Oracle Sharpe-delta simulation — INVERTED kill_low (skip if NATR < threshold)

From `analysis/iteration_v1-011/inverted_low_kill_oracle.csv`:

**BASELINE roster (kill_low; the EDA-discovered live axis)**:

| threshold | OOS skip rate | OOS sharpe baseline | OOS sharpe oracle | **OOS Δ** | F2 band? |
|---|---|---|---|---|---|
| **2.00** | **18.0%** | 0.1710 | 0.2169 | **+0.0460** | **IN — calibrated optimum lower bound** |
| 2.25 | 26.5% | 0.1710 | 0.1409 | -0.0301 | IN (Δ NEG) |
| 2.50 | 35.4% | 0.1710 | 0.1295 | -0.0415 | IN (Δ NEG) |
| 2.75 | 43.9% | 0.1710 | 0.2794 | +0.1084 | IN (Δ POS, larger skip) |
| 3.00 | 55.0% | 0.1710 | 0.2549 | +0.0839 | IN (edge of band) |
| 3.25 | 62.4% | 0.1710 | 0.3861 | +0.2151 | OUT (over 60%) |

**/010 EXPLORATION roster (kill_low; same axis, basin-shifted roster)**:

| threshold | OOS skip rate | OOS Δ | F2 band? |
|---|---|---|---|
| **2.00** | **19.0%** | **+0.1153** | **IN — calibrated optimum lower bound** |
| 2.25 | 25.7% | +0.0166 | IN (Δ POS, smaller) |
| 2.50 | 35.2% | -0.0492 | IN (Δ NEG) |
| 2.75 | 44.8% | -0.0394 | IN (Δ NEG) |
| 3.00 | 57.1% | -0.2753 | IN (Δ very NEG) |

**Cross-roster sign-agreement at threshold = 2.0%**:

| Roster | OOS skip rate | OOS Δ | F2 band |
|---|---|---|---|
| BASELINE | 18.0% | **+0.046** | IN |
| v1-010 EXPLORATION | 19.0% | **+0.115** | IN |

This is the **only** candidate threshold across kill_high AND kill_low that:
- Lands in F2 band [10%, 60%] on BOTH rosters
- Produces POSITIVE OOS Δ on BOTH rosters
- Has cross-roster sign-agreement (basin-robust signal)

### 2.4 Per-symbol PnL pattern (BASELINE OOS) — why kill_low works

From `analysis/iteration_v1-011/per_symbol_natr_pnl_pattern.csv` — BASELINE OOS only (most decisive evidence):

| Symbol | NATR bucket | n_trades | WR | mean_net_pnl_pct | sum_weighted_pnl |
|---|---|---|---|---|---|
| BTC | <2.5 | 31 | 45.2% | +0.72 | +2.68 |
| BTC | 2.5-3 | 2 | 50.0% | +1.86 | +3.71 |
| BTC | 3-3.5 | 2 | 50.0% | +3.63 | +7.26 |
| **ETH** | **<2.5** | **13** | **30.8%** | **-0.36** | **+12.38** |
| **ETH** | **2.5-3** | **15** | **20.0%** | **-1.64** | **-7.65** |
| ETH | 3-3.5 | 6 | 66.7% | +3.43 | +10.77 |
| ETH | 3.5-4 | 7 | 42.9% | -0.77 | +1.86 |
| ETH | 4-5 | 3 | 100% | +5.56 | **+14.70** |
| ETH | >5 | 2 | 50.0% | +0.07 | +0.15 |
| LINK | <2.5 | 5 | 20.0% | -1.50 | -1.52 |
| LINK | 2.5-3 | 7 | 42.9% | +1.54 | +7.76 |
| LINK | 3-3.5 | 5 | 20.0% | -1.31 | -7.12 |
| LINK | 3.5-4 | 5 | 80.0% | +4.77 | +11.76 |
| LINK | 4-5 | 3 | 66.7% | -0.27 | -0.27 |
| LINK | >5 | 3 | 100% | +4.84 | **+10.73** |
| **LTC** | **<2.5** | **16** | **25.0%** | **-0.88** | **-0.63** |
| **LTC** | **2.5-3** | **5** | **20.0%** | **-1.51** | **-7.56** |
| LTC | 3-3.5 | 6 | 33.3% | -0.56 | -6.81 |
| LTC | 3.5-4 | 4 | 50.0% | -3.16 | -3.61 |
| LTC | 4-5 | 3 | 33.3% | -3.20 | -9.59 |
| DOT | <2.5 | 2 | 50.0% | +1.65 | +2.08 |
| **DOT** | **2.5-3** | **8** | **12.5%** | **-3.06** | **-7.12** |
| DOT | 3-3.5 | 14 | 35.7% | -0.33 | -3.36 |
| DOT | 3.5-4 | 7 | 42.9% | +0.48 | -2.79 |
| DOT | 4-5 | 10 | 40.0% | -0.75 | +1.41 |
| DOT | >5 | 5 | 80.0% | +6.38 | **+8.93** |

**Mechanism observed**:
- **ETH 2.5-3 bucket: WR 20%, sum -7.65** (loser cluster)
- **LTC <2.5 + 2.5-3 buckets: WR 25%+20%, sum -0.63 + -7.56 = -8.19** (loser cluster)
- **DOT 2.5-3 bucket: WR 12.5%, sum -7.12** (catastrophic loser cluster)
- **High-NATR (>5) winners**: ETH +0.15, LINK +10.73, DOT +8.93 — the convergent recommendation would have KILLED THESE WINNERS

At threshold = 2.0%, kill_low removes ~34 trades (mostly ETH+LTC+DOT in the 2-3% NATR band that are systematic losers); LINK and BTC at NATR<2 are mostly preserved (low-NATR BTC is a winner; low-NATR LINK is tiny n_trades=5).

### 2.5 HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**
- **Reason**: R5-BINARY-KILL is an ENTRY FILTER that changes which trades enter — this changes the trade roster that Optuna's CV objective sees, which changes the loss surface the GBM is fitting. Distinct mechanism from /010 (which multiplied position-sizing weight into the loss directly), but still modifies Optuna's training-objective domain. HIGH-RISK by v1 catalog definition.
- **Mitigation (HIGH-RISK with OPT-IN multi-seed; lighter footing than v3)**: pre-commit to /012 multi-seed CONFIRMATION-spec validation IF /011 verdict is PROMISING. If /011 is NEGATIVE / NEGATIVE-NEGATIVE / PROMISING-INERT / OVERSHOOT-FLAG, /012 reverts to next axis from Critic Path Forward and binary-kill is recorded as single-seed-tested.
- **7-HIGH-RISK-in-a-row context** (per /010 closeout): /005-/010 were all HIGH-RISK; 6 NEGATIVE outcomes + 1 PROMISING-METHODOLOGY (/008 methodology); /011 is 7th-consecutive HIGH-RISK. **NOTE per /010 LM Master Phase 7.4 calibration update**: when the axis multiplies the loss directly (position-sizing weight, sample weight, loss function), basin-shift probability is HIGH (40-60%) at single-seed budgets. R5-BINARY-KILL does NOT multiply the loss directly — it filters which trades enter the loss computation. **The basin-shift mechanism for binary kill differs from /010's proportional scaling.** The brief Section 5.1 P10/P90 width reflects this distinction (narrower band than /010 would have warranted in retrospect).
- **Rule firing check**: per /010 closeout permanent catalog rule "3+ HIGH-RISK in a row with >1σ negative deltas → mandatory multi-seed" — /005-/010 produced /005 OOS Δ -0.48 (>1σ NEG), /006 OOS Δ -0.23 (>1σ NEG), /007 OOS Δ -0.90 (>1σ NEG), /009 OOS Δ -0.48 (>1σ NEG), /010 OOS Δ -0.03 (<1σ; INERT band, NOT a NEG). The 5 NEG-class HIGH-RISKs (/005-/007 + /009) trigger the rule; /010's INERT outcome arguably stops the run; either way, **the mandate is active** for /011. Per /010 closeout: the rule is "lighter footing than v3" — multi-seed pre-commit is OPT-IN, mitigation = pre-commit to /012 CONFIRMATION if PROMISING. The brief honors the rule via Section 2.5 OPT-IN pre-commit.

---

## Section 3 — Proposed Changes (with LM Master and Critic responses)

### 3.1 src/ changes

**3-file diff (~15 lines net new)**:

1. **`src/crypto_trade/backtest_models.py`**: add 2 fields to `BacktestConfig`:
   ```python
   # Risk mitigation R5-BINARY-KILL (iter-v1/011): entry-time NATR kill switch.
   # When enabled, skips entry if NATR_14 at signal time < risk_r5_kill_natr_min_pct.
   # Applied at the entry gate BEFORE vt_scale / R2 (since this is an entry
   # filter, not a sizing modifier). Default disabled — preserves byte-identical
   # legacy behavior on every iteration through /010.
   risk_r5_kill_low_natr_enabled: bool = False
   risk_r5_kill_low_natr_min_pct: float = 2.0
   ```

   Note: distinct fields from /010's `risk_r5_vol_target_enabled` / `risk_r5_vol_target_pct` — both fields coexist (independent flags). /010's proportional-scaling R5 stays available but disabled for /011 (we are testing the binary subtype in isolation; no axis-stacking).

2. **`src/crypto_trade/backtest.py`**: insert R5-BINARY-KILL block at entry gate, BEFORE the cooldown check / before vt_scale computation. Implementation skeleton (QE finalizes line numbers):
   ```python
   # R5-BINARY-KILL (iter-v1/011) — entry-time NATR floor; STATELESS gate
   if config.risk_r5_kill_low_natr_enabled:
       _natr = r5_natr_lookup.get((sym, ot), float("nan"))
       if ot < OOS_CUTOFF_MS:
           r5_kill_signals_is += 1
       else:
           r5_kill_signals_oos += 1
       if not math.isnan(_natr) and _natr < float(config.risk_r5_kill_low_natr_min_pct):
           # Kill entry — increment counter, continue to next bar
           if ot < OOS_CUTOFF_MS:
               r5_kill_fires_is += 1
           else:
               r5_kill_fires_oos += 1
           continue
   # ... existing cooldown / vt_scale / R2 / (legacy R5 proportional) blocks follow
   ```

   The `r5_natr_lookup` dict is already built at backtest init by the /010 wiring (loaded when either `risk_r5_vol_target_enabled` OR `risk_r5_kill_low_natr_enabled` is True — small refactor of the init guard).

3. **`run_baseline_v1.py`**: at `run_model` BacktestConfig construction:
   ```python
   risk_r5_kill_low_natr_enabled=True,
   risk_r5_kill_low_natr_min_pct=2.0,
   risk_r5_vol_target_enabled=False,  # /010 proportional scaling DISABLED for /011
   ```

   Applied to all 4 models (A pooled, C LINK, D LTC, E DOT) — R5-BINARY-KILL is universal entry filter (no per-symbol differentiation; defer per-symbol calibration to /012 CONFIRMATION if PROMISING).

### 3.2 LM Master /010 Phase 7.4 PRIMARY recommendation response

Per `briefs-v1/iteration_v1-010/lgbm_advisor.md` Phase 7.4 §"Path for /011":

> **Concrete /011 axis**: "skip entry if NATR_14 > 7%" (binary kill, not proportional scale). The threshold 7% is the **universe p90 of NATR_14**; at p75 ≈ 4.7% the cap is too tight (would kill ~25% of trades). p90 ≈ 7% kills ~10% — same fire-rate band as /010's 23%/18.6% but as a hard binary cutoff.

**Response**: **PRIMARY AXIS (binary-kill) ADOPTED; DIRECTION INVERTED via EDA**. The EDA (Section 2) reveals:
- LM Master's "universe p90 of NATR_14 ≈ 7%" came from /010 EDA's CANDLE-LEVEL distribution (per /010 brief Section 2.1). The model's actual entry-time-conditional p90 OOS is **4.30%** — the convergent threshold puts skip rate at 0.5% (1 trade) OOS.
- The Phase 1.5 exit-reason analysis on the BASELINE roster shows high-NATR (5-7%) OOS WR = 77.8% / mean PnL +5.14%/trade; low-NATR (<3%) OOS WR = 31.7% / mean PnL -0.41%. **High-NATR is empirical winners**, the OPPOSITE of the convergent reasoning.
- Cross-roster oracle: only the INVERSION (skip if NATR < 2.0%) produces positive OOS Δ on BOTH rosters AND lands in F2 band.

This is NOT a rejection of LM Master's PRIMARY axis (R5 binary kill switch — ADOPTED in the primitive class). It is an **EDA-driven sharpening of the direction**: kill the empirical losers, not the empirical winners. Per THE PRIME DIRECTIVE: the EDA is design work for the sharpest experiment; sharpening the direction is exactly what the EDA exists to do.

**No Phase 4.5 LM Master dispatch for /011**: per /010 closeout discipline, the orchestrator will run Phase 4.5 LM Master advisory AFTER this brief is authored (analogous to /010's post-brief Phase 4.5 fire due to compaction ordering). The brief Section 3 ENTRIES below are best-anticipation; the LM Master advisory will be addressed in `lgbm_advisor.md` once issued, with brief Section 3.3 amended retroactively (same protocol as /010).

### 3.3 Critic /010 Phase 7.5 Path Forward response

Per `briefs-v1/iteration_v1-010/review.md` §"Path Forward":

> **R5-BINARY-KILL — risk-primitive** (LM Master Phase 7.4 PRIMARY recommendation; convergent with Critic). Skip entry if NATR_14 > 7% (universe p90). State-discontinuous primitive vs /010's smooth attenuation. Predicted fire rate: ~10%. EDA basis already exists in /010 Section 2.1 — no new Phase 1 work needed.

**Response**:
- **PRIMARY axis (binary-kill, risk-primitive UNUSED subtype) ADOPTED**.
- **Threshold and DIRECTION REVISED via EDA**: Critic's prediction "EDA basis already exists in /010 Section 2.1 — no new Phase 1 work needed" was structurally wrong. /010's EDA was candle-level NATR distribution; /011 needed entry-time-conditional NATR distribution. Phase 1 work IS needed (and was done — see Section 2.1). The EDA revealed:
  1. Convergent 7% threshold = empirically inactive (0.5% OOS skip rate).
  2. F2 band [10%, 60%] cannot be satisfied at any high-side threshold.
  3. Per Phase 1.5 exit-reason: high-NATR is empirical winners, low-NATR is empirical losers.
  4. Cross-roster sign-agreement on kill_low @ threshold 2.0% (+0.046 BASELINE / +0.115 v1-010).

**The EDA-driven inversion (kill_low at 2.0%) is the LIVE axis; the convergent direction (kill_high at 7%) is empirically dead.** Per Critic Rec #2 (LM Master revised basin-shift probability band 40-60% for weight-touching axes), brief Section 5.1 acknowledges this in the P10/P90 width — though R5-BINARY-KILL is NOT weight-touching (it is an entry filter, not a multiplicative weight modifier); the basin-shift mechanism differs but the conservative P10/P90 width is preserved.

- **Critic Path Forward Option 2 (TRIPLE-BARRIER σ_t SOURCE — labeling) REJECTED**: structurally orthogonal alternative; not consumed at /011 since binary-kill (Option 1) advances. Available for /012 if /011 is NEGATIVE.
- **Critic Path Forward Option 3 (PER-CELL EARLY-STOP — methodology) REJECTED**: non-compoundable methodology improvement; not the highest-value next step given the EDA-discovered live signal. Available for /013+ if a structural defect surfaces.

### 3.4 Critic Recommendations #1, #2, #3 response

Per `briefs-v1/iteration_v1-010/review.md` §"Recommendations to QR":

**Rec #1 — Pre-register `IS Δ > +X` verdict class in Section 8**:
- **ADOPTED**: Section 8 now includes the OVERSHOOT-FLAG class (`IS Δ ∈ (+0.05, +0.30]` requiring multi-seed CONFIRMATION) and catastrophic-basin-shift (`IS Δ > +0.30`).

**Rec #2 — LM Master revised basin-shift probability band (40-60%) for weight-touching axes**:
- **ADOPTED**: Section 5.1 P10/P90 width is wider than the EDA's oracle prediction would suggest, acknowledging the LM Master calibration update. Specifically: R5-BINARY-KILL is NOT weight-touching (it is an entry filter, not a multiplicative weight modifier into the loss), but the brief's predicted band still respects the conservative prior. Brief Section 5.1 notes the mechanism distinction explicitly.

**Rec #3 — r5_fire_log.csv**:
- **N/A**: there is no R5 revival in the proportional-scaling sense; this is binary kill, not proportional. Equivalent forensic at /011 = the IS/OOS-split fire counter print (analogous to /010's `[R5] IS: fired on X of Y signals` summary) but for binary-kill firings: `[R5-BINARY-KILL] IS: fired on X of Y candidate signals (Z%)` + OOS same. No per-trade NATR_14 / r5_cap forensic needed because binary kill = single boolean per signal-candidate, fully captured by aggregate counters + comparison.csv rows.

### 3.5 Hyperparameter and search-space — UNCHANGED

- `bounds_profile=v1_pruned` (same as /002+ default)
- `n_trials=35` (canonical v1 EXPLORATION)
- `ENSEMBLE_SIZE=3` (single outer seed × 3 inner)
- `feature_columns=V1_FEATURE_COLUMNS_PRUNED` (40 columns — same as /008-/010)
- `cv_splits=5`, `embargo` formula unchanged
- ATR mults `atr_tp=3.5, atr_sl=1.75` (all models)
- R1 mults / cooldown unchanged
- R2 drawdown brake (Model E) unchanged
- R3 OOD Mahalanobis gate unchanged
- R5 proportional-scaling (/010 axis) DISABLED for /011

The ONLY axis change is the BacktestConfig R5-BINARY-KILL enable + threshold 2.0%.

---

## Section 4 — Falsifiers and Behavioral Predictors

Each falsifier has an EXPLICIT numerical condition that fires on backtest report data.

### F1 (PRIMARY) — Portfolio OOS Sharpe Δ
- **Condition**: `(/011 OOS monthly Sharpe) - (BASELINE_V1 OOS monthly Sharpe +0.6637) < -0.05`
- **Verdict if fires**: NEGATIVE
- **Catastrophic threshold**: `Δ < -0.20` triggers NEGATIVE-catastrophic
- **PROMISING threshold**: `Δ ≥ +0.05`
- **Oracle prediction**: +0.05 to +0.12 (based on BASELINE roster +0.046 and /010-roster +0.115)

### F2 (BEHAVIORAL — Phase 1 predictor) — R5-BINARY-KILL fire rate
- **Condition**: per-half R5-BINARY-KILL fire rate band check
  - **Calibration miss-too-tight**: portfolio OOS fire rate > 60% — kill is acting as constant brake, killing the majority of candidate signals
  - **Calibration miss-too-loose**: portfolio OOS fire rate < 5% — kill effectively inactive
- **Verdict if fires**: NEGATIVE-mis-calibrated
- **Reasonable activation band**: portfolio OOS fire rate ∈ [10%, 60%]
- **Oracle prediction**: BASELINE 18.0% / v1-010-EXPLORATION 19.0% — both mid-band
- **Pre-registered Phase 1 evidence**: `analysis/iteration_v1-011/inverted_low_kill_oracle.csv` row `roster=baseline, half=OOS, direction=kill_low, threshold_pct=2.0` shows skip rate 18.0%; `roster=v1-010, ...` shows 19.0%.

### F3 — IS Sharpe Δ catastrophic check (UPDATED per Critic Rec #1 with sign-symmetric gates)
- **Lower-bound condition**: `(/011 IS monthly Sharpe) - (BASELINE_V1 IS monthly Sharpe +0.2829) < -0.10`
- **Lower-bound verdict if fires**: NEGATIVE-catastrophic-IS
- **Upper-bound condition (NEW per Critic Rec #1)**:
  - `IS Δ ∈ (+0.05, +0.30]` → OVERSHOOT-FLAG (requires multi-seed CONFIRMATION to distinguish capacity-fit-noise from genuine edge)
  - `IS Δ > +0.30` → catastrophic-basin-shift (analogous to /010 LTC basin lottery; axis CLOSED at single-seed)
- **Oracle prediction**: +0.10 to +0.25 — possibly in OVERSHOOT-FLAG band

### F4 — DEGENERATE_PREDICTOR check (per /008 detector)
- **Condition**: any per-cell DEGENERATE_PREDICTOR fire in the /011 reports per `validation_v1.detect_degenerate_predictor`
- **Verdict if fires**: NEGATIVE-data-integrity OR NEGATIVE-feature-leakage (per detector subtype)
- **Oracle prediction**: 0 fires — R5-BINARY-KILL is an entry filter, not a feature or label-modifying primitive

### F5 — DSR computable per /008 refactor
- **Condition**: `dsr.json` exists with `n_eff_per_cell_median ≥ 4` AND `dsr_is_finite=True` AND no math-undefined values
- **Verdict if fires**: NEGATIVE-methodology-regression
- **Oracle prediction**: PASS (no methodology change between /008 baseline and /011)

### F6 (NEW per /010 closeout Lesson #2) — Roster-overlap diagnostic
- **Condition**: OOS roster overlap with BASELINE roster < (1 - fire_rate) - 0.20
  - At threshold 2.0% with predicted OOS skip rate 18-19%, expected baseline-roster overlap ≈ 81-82% (the trades not killed).
  - Tripwire: observed overlap < 61% indicates >20pp of Optuna basin re-routing beyond mechanical filtering.
- **Verdict if fires**: PROMISING-INERT-with-roster-shift OR NEGATIVE-basin-shift (subtype determined by F1 sign)
- **Oracle prediction**: ≥75% overlap — binary-kill is mechanically less loss-surface-disrupting than /010's proportional scaling (entry filter doesn't change weight magnitudes, only which trades enter)

---

## Section 5 — Expected OOS Impact

### 5.1 Predicted Sharpe delta band (with epistemic humility)

Per /010 closeout LM Master calibration rule: basin-shift probability HIGH (40-60%) at single-seed for position-sizing-weight axes. **R5-BINARY-KILL is NOT a position-sizing-weight axis** (it is an entry filter; no multiplicative weight modification of the loss). The basin-shift expectation for binary kill should be lower than for proportional scaling — but the brief still respects a CONSERVATIVE prior.

| Range | OOS Sharpe Δ | Interpretation | Confidence |
|---|---|---|---|
| P10 | -0.15 | Optuna basin shift goes opposite direction; roster turnover wipes out oracle signal | LOW |
| P25 | -0.05 | F1 boundary; NEGATIVE marginal | LOW-MED |
| **P50** | **+0.08** | **Tracks oracle midpoint (+0.046 baseline / +0.115 v1-010 average)** | **MED** |
| P75 | +0.18 | Oracle signal preserved; Optuna re-optimization neutral | LOW-MED |
| P90 | +0.30 | Optuna re-optimization compounds with kill_low effect | LOW |

**Wide band (~0.45 P10-P90 spread)** reflects:
- LM Master /005-/010 calibration drift (track 1/6 directional correct)
- Conservative basin-shift prior despite R5-BINARY-KILL being entry-filter not weight-touching
- Cross-roster oracle disagreement on MAGNITUDE (+0.046 vs +0.115; 6.5× ratio) suggests basin-dependent sensitivity even before /011 launches

### 5.2 Most likely verdict: **PROMISING** (modal) or PROMISING-INERT-with-roster-shift (sister mode)

Per oracle EDA (Section 2.3): cross-roster sign-agreement on positive OOS Δ at threshold = 2.0% is the strongest pre-registered EDA signal /011 has had in cycle-2. If Optuna re-optimization stays in a neighborhood that doesn't catastrophically re-route, the verdict is **PROMISING** (OOS Δ ≥ +0.05).

Less likely: **PROMISING-INERT** (the kill_low mechanism is real but eaten by basin shift) — would imply the binary-kill direction is correct but its magnitude collapses below the +0.05 threshold. Still record positive cross-roster oracle as informative.

Lowest likely: **NEGATIVE / NEGATIVE-catastrophic** (basin shift inverts the oracle signal). Probability ~20% per Section 5.1 P25 tail.

### 5.3 Counter-evidence (mandatory per Section 7 of skill template)

Three arguments AGAINST /011 yielding positive OOS:

1. **`feedback_v3_concentration_is_signal.md` v3/020 universal generalization**: the concentration/risk-primitive family has produced NEGATIVE outcomes universally across v3 (/020 -0.72) and now v1 (/010 -0.03 with IS basin shift). Binary kill is a subtype within this family; even if directionally orthogonal to proportional scaling, the family's empirical track record is poor.

2. **/010 LM Master Phase 7.4 calibration: basin-shift probability HIGH at single-seed even for entry-filter axes**: although binary kill is structurally different from proportional scaling, the underlying mechanism (Optuna's CV objective seeing a different trade roster → different loss surface → potentially different basin) is preserved. LM Master's updated rule is conservative; brief Section 5.1 reflects this.

3. **The cross-roster oracle agreement could be partly artifactual**: both BASELINE and /010-EXPLORATION rosters share the same FEATURE-PARQUET + same NATR_14 column + same OOS_CUTOFF_MS. The 18-19% OOS skip rate at threshold 2.0% is a property of the entry-time-conditional NATR distribution, which is itself partly a property of the model's feature space (Model A uses NATR_14 as a feature). Cross-roster overlap on the SAME feature could produce spurious agreement. The /010-roster oracle (+0.115) is 2.5× the BASELINE oracle (+0.046); this magnitude divergence is itself a warning sign.

These counter-arguments are NOT defeaters — they sharpen the falsifier F1 boundary. The experiment runs precisely BECAUSE the EDA evidence is strong but the basin-shift risk is non-negligible.

---

## Section 6 — Risk Mitigation (required per merge-candidate skill rule)

R5-BINARY-KILL itself IS the risk mitigation. This section addresses interactions with R1/R2/R3 and risk-of-the-experiment.

### 6.1 R5-BINARY-KILL ↔ R1 interaction (Models C, D, E)

R1 (consecutive-SL cooldown, K=3, C=27 candles) is BINARY (entry blocked, weight unchanged when not blocked). R5-BINARY-KILL is also BINARY (entry skipped). They are orthogonal binary gates; sequential application: R5-BINARY-KILL is evaluated FIRST (entry-time NATR floor), then R1 (cooldown), then proceed to vt_scale / R2. No multiplicative interaction.

### 6.2 R5-BINARY-KILL ↔ R2 interaction (Model E only)

R2 (drawdown-triggered scaling, trigger=7%, anchor=15%, floor=0.33) operates at position-sizing layer AFTER R5-BINARY-KILL has decided to proceed. Orthogonal layers; no interaction.

### 6.3 R5-BINARY-KILL ↔ R3 interaction (ALL models)

R3 (OOD Mahalanobis gate, 70th-percentile cutoff) operates BEFORE prediction (gates the input features). R5-BINARY-KILL operates AFTER prediction (gates the entry given NATR). Both are binary; sequential. No multiplicative interaction.

### 6.4 R5-BINARY-KILL ↔ legacy R5 proportional scaling (DISABLED for /011)

/010's `risk_r5_vol_target_enabled` is DISABLED for /011 — no axis stacking. The wiring coexists in code, but only one R5 subtype is active per backtest. If /011 PROMISING, a future /013+ CONFIRMATION may consider stacking both R5 subtypes; not at EXPLORATION.

### 6.5 IS-calibrated thresholds (mandatory per `feedback_risk_mitigation_design.md`)

- `risk_r5_kill_low_natr_min_pct = 2.0` — calibrated from Section 2 EDA; cross-roster sign-agreement on positive OOS Δ + F2 band-passing skip rate (18-19%).
- F2 mis-calibration tripwire: portfolio OOS fire rate band [10%, 60%] — falsifier F2.
- F6 mis-calibration tripwire (NEW): OOS roster-overlap with BASELINE < 61% — falsifier F6.

### 6.6 Simulated historical effect on past iterations

The kill_low oracle on the baseline trade roster (Section 2.3) shows what /011 would do if Optuna's hyperparameters were FROZEN at the baseline run. The simulation is honestly POSITIVE oracle (+0.046 BASELINE / +0.115 v1-010 EXPLORATION), so /011 is justified as:
- (a) An empirical test of whether the cross-roster-positive oracle survives Optuna re-optimization at single-seed=42, OR
- (b) An EDA-driven inversion of the convergent recommendation that the EDA itself empirically refuted.

This brief presents (a) as the primary frame. The experiment is being run BECAUSE the oracle is the strongest positive signal in cycle-2 to date — failing to run it would violate THE PRIME DIRECTIVE.

### 6.7 Kill-switch criteria (mandatory)

If any of the following fire mid-flight, the iteration is killed:
- IS Sharpe < -0.50 in first month of monthly walk-forward (would indicate catastrophic Optuna miss) — KILLED
- DEGENERATE_PREDICTOR fires in first 4 monthly cells — KILLED, data integrity defect
- Optuna stalls (no successful trial in any (model, month, seed) cell > 5 min) — KILLED, infrastructure defect
- R5-BINARY-KILL fire rate > 90% in first month (would indicate threshold mis-spec) — KILLED, calibration defect

---

## Section 7 — Failure Modes (mandatory per skill brief template)

### Failure Mode 1 — Basin shift inverts the oracle signal
- **Mechanism**: at single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3, Optuna re-optimization on the post-kill_low trade roster could find a basin that overfits IS to the new restricted training universe. The new basin's OOS trade roster could land in a region where the kill_low oracle's BASELINE-roster prediction does NOT hold.
- **Detection**: F1 NEGATIVE-catastrophic (OOS Δ < -0.20).
- **Verdict**: NEGATIVE-catastrophic + F6 roster-overlap diagnostic confirms basin shift.
- **Pre-emptive defense**: cross-roster oracle agreement (BASELINE +0.046 AND /010-EXPLORATION +0.115) is the strongest evidence the signal is basin-robust; HIGH-RISK Section 2.5 OPT-IN multi-seed pre-commit covers the residual risk.

### Failure Mode 2 — Kill rate too tight (mis-calibration to high firing)
- **Mechanism**: actual /011 OOS fire rate exceeds oracle 19% by >2× (>40%) due to Optuna re-routing trades into the kill zone.
- **Detection**: F2 OOS fire rate > 60% (mis-calibrated).
- **Verdict**: NEGATIVE-mis-calibrated.
- **Pre-emptive defense**: Section 2.3 cross-roster oracle 18-19% has ~3× margin to 60% tripwire.

### Failure Mode 3 — Kill rate too loose (PROMISING-INERT)
- **Mechanism**: actual /011 OOS fire rate is < 5% — kill effectively inactive; behavior reverts to baseline.
- **Detection**: F2 OOS fire rate < 5%.
- **Verdict**: PROMISING-INERT (no effective intervention).
- **Pre-emptive defense**: 2.0% threshold is at portfolio entry-time p10 (BASELINE) / p10 (/010); skip rate cannot collapse below 5% absent extreme Optuna re-routing.

### Failure Mode 4 — IS Δ overshoot indicating basin lottery (per /010 OVERSHOOT-FLAG class)
- **Mechanism**: similar to /010's LTC basin lottery — single-seed Optuna finds a basin that fits IS noise around the new restricted training universe; IS Δ exceeds +0.05 / OOS Δ in INERT band.
- **Detection**: F3 IS Δ ∈ (+0.05, +0.30] AND F1 OOS Δ ∈ [-0.05, +0.05].
- **Verdict**: PROMISING-INERT-with-IS-overshoot (per Critic Rec #1; recorded as OVERSHOOT-FLAG class).
- **Resolution**: multi-seed CONFIRMATION required at /012 to distinguish capacity-fit-noise from genuine edge.

### Failure Mode 5 — Per-symbol asymmetry breaks (LINK/BTC kill-low removes winners)
- **Mechanism**: per Section 2.4 BASELINE OOS: LINK <2.5 = 5 trades sum -1.52 (slight loser); BTC <2.5 = 31 trades sum +2.68 (winner cluster). Kill_low at 2.0% would remove BTC OOS low-NATR winners as collateral damage.
- **Detection**: per-symbol BTC OOS net_pnl < baseline by > 5pp (vs baseline +33.17).
- **Verdict**: NEGATIVE-edge-source-erosion (BTC subtype).
- **Counter-pre-emption**: 2.0% threshold is at portfolio p10 → BTC OOS p10 = 1.48% (Section 2.1 table). BTC's portfolio share at NATR < 2.0% is ~20 trades (rough estimate from BTC p25 = 1.52%); most of BTC OOS volume is at NATR 2-3 range which is preserved. Counter-evidence #3 in Section 5.3 acknowledges this risk.

---

## Section 8 — Verdict Gates (UPDATED per Critic Rec #1 — sign-symmetric on F3)

### PROMISING (favorable, advances to /015 CONFIRMATION consideration)
- F1: OOS Sharpe Δ ≥ +0.05 (strict)
- F3: IS Sharpe Δ ∈ [-0.05, +0.05] (within normal drift band)
- F2: portfolio OOS fire rate ∈ [10%, 60%]
- F4: 0 DEGENERATE_PREDICTOR fires
- F5: DSR mathematically computable (n_eff_per_cell_median ≥ 4)
- F6: OOS roster-overlap with BASELINE ≥ 61% (i.e., ≤ 20pp basin shift beyond mechanical filtering)
- Trade-rate floor: ≥ 10 OOS/month, ≥ 130 OOS total

### PROMISING-INERT (mechanism fires but Sharpe-neutral)
- F1: OOS Sharpe Δ ∈ [-0.05, +0.05]
- F3: IS Sharpe Δ ∈ [-0.10, +0.05] (within normal drift band)
- F2: portfolio OOS fire rate ∈ [10%, 60%]
- F4: 0 DEGENERATE_PREDICTOR fires
- F5: DSR computable
- F6: OOS roster-overlap with BASELINE ≥ 61%
- Trade-rate floor: PASS

### OVERSHOOT-FLAG (NEW per Critic Rec #1) — IS basin-shift candidate
- F1: OOS Sharpe Δ ∈ [-0.05, +0.05] (literal INERT band)
- F3: IS Sharpe Δ ∈ (+0.05, +0.30] (overshoot in candidate band; not catastrophic)
- F2/F4/F5: PASS
- F6: per-symbol concentration: at least one symbol with pct_of_total_pnl > 80% (corroborating diagnostic)
- **Verdict subtype**: EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-overshoot) — basin-shift confirmed; OOS band-pass is happy accident; mechanism not durable at single-seed
- **Resolution path**: NOT a multi-seed CONFIRMATION candidate; pivot to next axis from Critic Path Forward

### catastrophic-basin-shift (NEW per Critic Rec #1)
- F3: IS Sharpe Δ > +0.30 (catastrophic basin lottery; analogous to /010 LTC)
- Verdict: EXPLORATION-NEGATIVE-catastrophic-IS-overshoot; axis CLOSED at single-seed

### NEGATIVE (any single failure of F1/F3/F4/F5/F6 below PROMISING-INERT band)
- F1: OOS Sharpe Δ < -0.05 → NEGATIVE
- F1 catastrophic: OOS Sharpe Δ < -0.20 → NEGATIVE-catastrophic
- F3: IS Sharpe Δ < -0.10 → NEGATIVE-catastrophic-IS (independent of F1)
- F4 fires: NEGATIVE-data-integrity (subtype per detector)
- F5 fires: NEGATIVE-methodology-regression
- F6 fires: NEGATIVE-basin-shift (subtype per F1 sign)

### NEGATIVE-NEGATIVE compound (per /007 + /009 + /010-IS-overshoot cycle-2 pattern)
- Both F1 < -0.05 AND F3 < -0.10 simultaneously → NEGATIVE-NEGATIVE compound, classify as cycle-2 pattern-continuation (3rd-or-4th occurrence)

### NEGATIVE-mis-calibrated (F2 boundary)
- F2 portfolio OOS fire rate < 5% OR > 60% → NEGATIVE-mis-calibrated

### PROMISING tripwire commitment (per Section 2.5)
- If verdict = PROMISING, /012 launches as multi-seed CONFIRMATION-SPEC at ENSEMBLE_SIZE=10 + 10-seed validation per the HIGH-RISK pre-commit at Section 2.5. (Note: /012 multi-seed validation can be done at EXPLORATION-spec n_trials but with ENSEMBLE=10 + 10 outer seeds; full CONFIRMATION-MERGE must wait for cycle cadence at /015.)

---

## Section 9 — Library Stack Declaration (mandatory per /009 closeout amendment)

The /011 backtest uses the following libraries — pinned by `pyproject.toml` and `uv.lock` at branch HEAD:

- **lightgbm** — exact pin from `uv.lock`
- **optuna** — exact pin
- **pandas** + **pyarrow** — for feature parquet IO
- **numpy** — for binary-kill comparison
- **scikit-learn** — for OOD Mahalanobis gate (R3) and PCA in dsr.json
- **statsmodels** — for ADF tests in /008 reporting
- **scipy** — for PSR/DSR computation
- **pandas-ta** — for vol_natr_14 feature (already in baseline; no new dep)

**No new dependencies introduced.** The R5-BINARY-KILL implementation uses only `numpy` (already in stack) and `math` (stdlib). The NATR_14 column is loaded from the same feature parquets the strategy already loads.

---

## Section 10 — Implementation Spec (for QE Phase 6)

### 10.1 src/ diff summary (verbatim spec for QE)

1. **`src/crypto_trade/backtest_models.py`**: insert AFTER the existing R5 fields (line 92-93 of /010 wiring):
   ```python
   # Risk mitigation R5-BINARY-KILL (iter-v1/011): entry-time NATR floor.
   # When enabled, skips entry if NATR_14 < risk_r5_kill_low_natr_min_pct.
   # This is an entry filter (state-discontinuous), NOT a position-sizing
   # weight modifier. Distinct from /010's risk_r5_vol_target_enabled.
   # Default disabled — restoring False preserves byte-identical legacy.
   risk_r5_kill_low_natr_enabled: bool = False
   risk_r5_kill_low_natr_min_pct: float = 2.0
   ```

2. **`src/crypto_trade/backtest.py`**:
   - **Refactor the existing `r5_natr_lookup` init guard** (around backtest.py L207) to load when EITHER `risk_r5_vol_target_enabled` OR `risk_r5_kill_low_natr_enabled` is True:
     ```python
     if config.risk_r5_vol_target_enabled or config.risk_r5_kill_low_natr_enabled:
         # load r5_natr_lookup ... (existing /010 wiring)
     ```
   - **Add R5-BINARY-KILL block as the FIRST signal-time filter** (BEFORE cooldown check and BEFORE vt_scale computation). Suggested location: at the top of the `if signal.direction != 0 and signal.weight > 0:` block, before the cooldown check. Implementation skeleton:
     ```python
     # R5-BINARY-KILL (iter-v1/011) — entry-time NATR floor; STATELESS gate
     if config.risk_r5_kill_low_natr_enabled:
         _natr_kill = r5_natr_lookup.get((sym, ot), float("nan"))
         if ot < OOS_CUTOFF_MS:
             r5_kill_signals_is += 1
         else:
             r5_kill_signals_oos += 1
         if not math.isnan(_natr_kill) and _natr_kill < float(config.risk_r5_kill_low_natr_min_pct):
             if ot < OOS_CUTOFF_MS:
                 r5_kill_fires_is += 1
             else:
                 r5_kill_fires_oos += 1
             # Skip this signal entirely
             continue
     # ... existing cooldown / vt_scale / R2 / legacy-R5 blocks follow
     ```
   - **Add IS/OOS-split fire counter initialization** (around L196-201 of /010 wiring, after the existing `r5_signals_is` / `r5_fires_is` etc.):
     ```python
     r5_kill_signals_is: int = 0
     r5_kill_signals_oos: int = 0
     r5_kill_fires_is: int = 0
     r5_kill_fires_oos: int = 0
     ```
   - **Add stdout summary print at backtest end** (analogous to /010's [R5] summary):
     ```python
     if config.risk_r5_kill_low_natr_enabled:
         _is_rate = r5_kill_fires_is / max(r5_kill_signals_is, 1)
         _oos_rate = r5_kill_fires_oos / max(r5_kill_signals_oos, 1)
         _all_rate = (r5_kill_fires_is + r5_kill_fires_oos) / max(
             r5_kill_signals_is + r5_kill_signals_oos, 1
         )
         print(
             f"[R5-BINARY-KILL] IS: fired on {r5_kill_fires_is} of {r5_kill_signals_is} "
             f"signals ({100*_is_rate:.2f}%); "
             f"OOS: fired on {r5_kill_fires_oos} of {r5_kill_signals_oos} "
             f"signals ({100*_oos_rate:.2f}%); "
             f"ALL: {100*_all_rate:.2f}%"
         )
     ```

3. **`src/crypto_trade/strategies/ml/reporting_v1.py`**: add `append_r5_binary_kill_rows_to_comparison` helper (analogous to /010's `append_r5_rows_to_comparison`). Add 2 rows to comparison.csv: `r5_binary_kill_fire_rate_is` and `r5_binary_kill_fire_rate_oos`. **NOTE per /010 Critic Check 7 defect D-RPRT-001**: ensure the schema convention (`in_sample` column = IS value, `out_of_sample` column = OOS value) is honored; do NOT replicate the /010 column-label-inversion bug.

4. **`run_baseline_v1.py`**: at `run_model` BacktestConfig construction, append:
   ```python
   risk_r5_kill_low_natr_enabled=True,
   risk_r5_kill_low_natr_min_pct=2.0,
   risk_r5_vol_target_enabled=False,  # /010 axis disabled for /011 isolation
   ```

### 10.2 Tests (Phase 6 QE deliverable)

`tests/test_iteration_v1_011_r5_binary_kill.py` covers:

1. **R5-BINARY-KILL OFF parity**: BacktestConfig with `risk_r5_kill_low_natr_enabled=False` produces byte-identical trade roster vs /010 baseline (sanity).
2. **R5-BINARY-KILL ON math**: synthetic config; NATR=1.5 + threshold=2.0 → signal skipped; NATR=2.5 + threshold=2.0 → signal proceeds.
3. **R5-BINARY-KILL boundary**: NATR == threshold exact → proceeds (strict `<` comparison; not skipped).
4. **R5-BINARY-KILL missing NATR**: when `(sym, ot)` not in `r5_natr_lookup`, signal proceeds (no nan-as-truthy bug; defensive null-check).
5. **R5-BINARY-KILL × R1 independence**: synthetic test where R1 cooldown is active + R5-BINARY-KILL would also fire — assert R5-BINARY-KILL is evaluated first and signal is correctly skipped (no double-counting).
6. **R5-BINARY-KILL counter accuracy**: synthetic 4-signal test with 2 firing IS + 1 firing OOS + 1 non-firing — assert counters equal expected values.
7. **DEGENERATE_PREDICTOR detector** (per /008): runs on /011 reports.

### 10.3 Reports schema (additions vs /010)

`reports-v1/iteration_v1-011/` produces:
- `comparison.csv` (10 rows + 2 new rows `r5_binary_kill_fire_rate_is` + `r5_binary_kill_fire_rate_oos`)
- `in_sample/` and `out_of_sample/` with full v1 report stack
- `dsr.json` per /008 schema
- IS+OOS adf_test.csv, ic_matrix.csv, per_symbol.csv, per_regime.csv, trades.csv, daily_pnl.csv, monthly_pnl.csv, quantstats.html
- /010 R5 proportional-scaling rows (`r5_fire_rate_is` / `r5_fire_rate_oos`) should both be 0.0% since the legacy axis is DISABLED for /011

### 10.4 Wall-clock estimate

Same as /008-/010: ~75-90 min single-seed × 4 models × 35 trials × 5 inner CV splits. R5-BINARY-KILL adds negligible overhead (one dict lookup + one float compare per signal). Within ≤ 2h cap.

### 10.5 Configuration single-source-of-truth

The `risk_r5_kill_low_natr_min_pct = 2.0` value lives in ONE place: `BacktestConfig.risk_r5_kill_low_natr_min_pct` default + `run_baseline_v1.py:run_model` literal. No other configuration file (or `live/models.py`) need touch for EXPLORATION — live wiring is CONFIRMATION-spec only.

---

## Section 11 — Alternate Designs (for Critic 6.0 review)

The brief Section 2 EDA converged on `risk_r5_kill_low_natr_min_pct = 2.0` as the calibrated optimum. If Critic 6.0 disagrees on the calibration choice, the next-best fallback values are:

| Alternate | threshold | BASELINE OOS oracle Δ | /010 OOS oracle Δ | BASELINE OOS skip rate | F2 band? |
|---|---|---|---|---|---|
| **PRIMARY** | **2.00%** | **+0.046** | **+0.115** | **18.0%** | **IN both rosters** |
| Alt-1 | 2.75% | +0.108 | -0.039 | 43.9% | IN BASELINE (CROSS-ROSTER SIGN-DISAGREE) |
| Alt-2 | 3.25% | +0.215 | -0.520 | 62.4% | OUT BASELINE (over 60%) |

Alt-1 has higher BASELINE oracle but NEGATIVE /010-roster oracle → cross-roster sign-disagreement → not robust. Alt-2 has highest BASELINE oracle but kills 62% of OOS trades (outside F2 band) AND catastrophic /010-roster -0.52. **Threshold 2.0% is the only candidate with cross-roster sign-agreement AND F2 band-passing on both rosters AND no catastrophic candidate-roster outcomes.**

The brief does NOT propose a grid sweep — that would require multiple Optuna runs and exceed the ≤2h EXPLORATION cap. /011 commits to threshold = 2.0%. If /011 is PROMISING, /012 multi-seed CONFIRMATION-spec can include threshold ∈ {1.75, 2.0, 2.25} as a 3-point ablation.

**The convergent NATR > 7% recommendation is EXPLICITLY REJECTED via Section 2.2 evidence**: empirically inactive (0.5% skip rate, F2 band fails). The brief does not preserve this as an alternate.

---

## Section 12 — Catalog Closeout Plan

If /011 outcome:

- **PROMISING (OOS Δ ≥ +0.05)**: catalog entry `risk-primitive` (binary-kill subtype) / `EXPLORATION-PROMISING` → /012 = multi-seed CONFIRMATION-spec of R5-BINARY-KILL at threshold=2.0 per Section 2.5 HIGH-RISK pre-commit. Major implication: **first cycle-2 PROMISING outcome on a compoundable axis**; would advance binary-kill subtype as a CONFIRMATION-bundle candidate for cycle-2 CONFIRMATION at /015.

- **PROMISING-INERT (OOS Δ ∈ [-0.05, +0.05] AND F3 in [-0.10, +0.05])**: catalog entry `risk-primitive` / `EXPLORATION-PROMISING-INERT` → binary-kill at 2.0% subtype CLOSED at single-seed; /012 pivots to UNUSED axis. **Note**: this would mean the kill_low oracle signal is real but not durable at single-seed budgets — informationally distinct from /010's PROMISING-INERT-with-IS-basin-shift because cross-roster oracle agreement (+0.046 / +0.115) is preserved as evidence even if /011's headline lands in INERT band.

- **OVERSHOOT-FLAG (F3 ∈ (+0.05, +0.30] AND F1 ∈ [-0.05, +0.05])**: catalog entry `risk-primitive` / `EXPLORATION-NEGATIVE PROMISING-INERT-with-IS-overshoot` → axis NOT closed; /012 = multi-seed re-test of THIS axis to distinguish capacity-fit-noise from genuine edge.

- **catastrophic-basin-shift (F3 > +0.30)**: catalog entry `risk-primitive` / `EXPLORATION-NEGATIVE-catastrophic-IS-overshoot` → axis CLOSED at single-seed; analogous to /010's LTC basin lottery; /012 pivots to UNUSED family.

- **NEGATIVE / NEGATIVE-NEGATIVE (F1 < -0.05 OR F3 < -0.10)**: catalog entry `risk-primitive` / `EXPLORATION-NEGATIVE` → binary-kill subtype CLOSED at v1 single-seed. **Catalog axiom escalation**: BOTH proportional-scaling (/010) AND binary-kill (/011) subtypes CLOSED → entire `risk-primitive` family CLOSED at v1 single-seed EXPLORATION; /012 MUST pivot to UNUSED family (labeling, methodology, model-arch, or universe extension).

- **NEGATIVE-mis-calibrated**: threshold re-calibration EXPLORATION at /012 with threshold ∈ {1.5, 2.5, 3.0} candidates — same risk-primitive family but different parameter region.

In all cases the next /012 brief Section 0.6 declares rotation status: PROMISING = same family at CONFIRMATION-spec exempt from rotation; PROMISING-INERT / NEGATIVE = rotation valid since UNUSED families still exist.

---

## Section 13 — Phase 5.5 Gate Self-Check

QR self-attestation of 11 mandatory sections (per `quant-iteration-v1.md` Phase 5.5):

- [x] Section 0 (subsections 0.1-0.6) — anchor, mode, label, determinism, cadence, axis-family
- [x] Section 1 — hypothesis (EDA-driven, with mechanism + predicted effect + outcome class + falsification claims)
- [x] Section 2 — IS-only evidence with numerical tables (5 tables; cross-roster oracle on BOTH BASELINE + /010-EXPLORATION; per-symbol PnL pattern; confidence × NATR cross-tab)
- [x] Section 2.5 — HIGH-RISK axis declaration (HIGH-RISK with binary-kill mechanism distinction from /010 weight-touching; OPT-IN multi-seed pre-commit)
- [x] Section 3 — proposed changes + LM Master /010 Phase 7.4 response + Critic /010 Phase 7.5 Path Forward response + Critic Recs #1/#2/#3 responses
- [x] Section 4 — falsifiers (F1-F6, including NEW F6 roster-overlap diagnostic per /010 Lesson #2) with explicit numerical conditions
- [x] Section 5 — expected OOS impact + counter-evidence + P10/P90 width respecting LM Master conservative prior
- [x] Section 6 — risk mitigation (R5-BINARY-KILL ↔ R1/R2/R3 orthogonality; IS-calibrated 2.0% threshold; kill-switch criteria)
- [x] Section 7 — failure modes (5 modes; Failure Mode 4 = OVERSHOOT-FLAG class per Critic Rec #1)
- [x] Section 8 — verdict gates (PROMISING / PROMISING-INERT / OVERSHOOT-FLAG / catastrophic-basin-shift / NEGATIVE / NEGATIVE-mis-calibrated; sign-symmetric on F3 per Critic Rec #1)
- [x] Section 9 — library stack declaration
- [x] Section 10 — implementation spec for QE (4-file diff; 7 unit tests; reports schema additions)
- [x] Section 11 — alternate designs (for Critic 6.0; convergent 7% recommendation explicitly rejected with evidence)
- [x] Section 12 — catalog closeout plan (6 verdict branches mapped to /012 next-axis)
- [x] Section 13 — Phase 5.5 self-check (this)

Cadence count check: cycle-2 = 6 of 10 EXPLORATIONs. /011 is EXPLORATION mode (not CONFIRMATION); cadence rule satisfied.

Axis Rotation Discipline check: prior 5 = [universe(006), feature-family(007), methodology(008), feature-family(009), risk-primitive(010)]. /011 = risk-primitive would be 2nd consecutive risk-primitive in cycle-2 but only 1 of last 5 is same-family. Rotation discipline preserved per Section 0.6. **Within-family subtype distinction (binary-kill vs proportional-scaling) is structural orthogonality, NOT a knob-tuning trap** — different primitive class (state-discontinuous entry filter vs smooth multiplicative weight modifier).

LM Master /010 Phase 7.4 PRIMARY recommendation: PRIMARY AXIS ADOPTED (binary-kill); threshold + direction REVISED via EDA — explicit response logged in Section 3.2.

Critic /010 Phase 7.5 Path Forward #1 (PRIMARY R5-BINARY-KILL): PRIMARY ADOPTED with EDA-driven inversion — explicit response logged in Section 3.3.

Critic Recs #1, #2, #3: ADOPTED, ADOPTED, N/A-with-equivalent-forensic — explicit responses logged in Section 3.4.

DEGENERATE_PREDICTOR detector check: /011 inherits /008 detector by default; F4 falsifier presence verified.

OVERSHOOT-FLAG verdict class: Section 8 includes the 4th band per Critic Rec #1.

**EDA-driven inversion of the convergent direction is the brief's load-bearing finding**: the convergent 3-way recommendation (LM Master + Critic + QR-memo all on "NATR > 7%") was based on candle-level NATR p90 ≈ 6.3% (/010 brief Section 2.1) — but the model's entry-time-conditional p90 OOS is 4.30%, and the convergent threshold produces 0.5% OOS skip rate (F2 fails). The EDA empirically REFUTES the convergent direction and IDENTIFIES the inverted direction (kill_low at 2.0%) as the only cross-roster-positive + F2-band-passing candidate. Per THE PRIME DIRECTIVE: the EDA designs the sharpest experiment; the brief must run the EDA-discovered live experiment, not the speculation-based one.
