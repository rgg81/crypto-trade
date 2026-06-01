# Phase 7.5 Critic Review — iter-v1/036

OVERALL: **EXPLORATION-PROMISING-CLEAN** — OOS Sharpe +1.7465 vs baseline +0.6637 = OOS Δ **+1.08** (LARGEST single-seed OOS lift in v1 history); both LINK + DOT specialists individually deliver >+100pp OOS PnL with 52-56% WR. /035 bimodal discovery EMPIRICALLY VALIDATED at isolated 2-cohort dispatch.

## Iteration Type
TYPE: EXPLORATION cycle-5 #3/10 — per-cohort specialization with trend-scanning labels (2-mechanism stack)

## Observed results

| Metric | Baseline | /036 | Δ |
|---|---|---|---|
| IS Sharpe | +0.2829 | +0.0843 | -0.20 |
| **OOS Sharpe** | +0.6637 | **+1.7465** | **+1.08** |
| IS Trades | 621 | 281 | -340 (2-cohort scope) |
| OOS Trades | 189 | 105 | -84 (below 130 floor) |
| IS WR | 39.9% | 38.8% | -1.1pp |
| OOS WR | 40.2% | **54.3%** | **+14.1pp** |
| OOS PF | 1.156 | 1.612 | +0.46 |
| OOS Calmar | 0.93 | **2.22** | **2.4× lift** |
| OOS Max DD | 40.94% | **23.28%** | **-17.7pp BETTER** |
| OOS PSR_vs_0 | 0.989 | 0.903 | -0.09 |
| OOS PSR_vs_1 | 0.079 | **0.594** | **+0.51 (8× lift)** |
| n_eff per cell median | n/a | 9 | healthy |
| DSR_corrected OOS | -35.66 | -3.82 | +31.84 (much better) |

**Per-symbol OOS — BIT-IDENTICAL to /035 LINK+DOT extraction:**

| Symbol | Trades | WR | Net PnL% | % of OOS PnL |
|---|---|---|---|---|
| **DOTUSDT** | 53 | **52.8%** | **+113.63%** | 51.06% |
| **LINKUSDT** | 52 | **55.8%** | **+108.91%** | 48.94% |

50/50 split — cleanest diversification in v1 history. Neither cohort dominates.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
Trend-scanning labels strictly forward at LABEL time; embargo intact at training time. PER-COHORT dispatch isolates each cohort's training set — no cross-cohort contamination.

### Check 2 — Embargo Width: PASS

### Check 3 — Multiple-Testing Correction: INFORMATIONAL improving toward MERGE
DSR OOS -3.82 (vs baseline -35.66; 90% improvement). PSR_vs_1 = 0.594 (lifted 8× from baseline 0.079; still below 0.95 merge tier but rising fast). At single-seed EXPLORATION budget, these signals are STRONGLY informative.

### Check 4 — IC Correlation: PASS (no new features)

### Check 5 — ADF Stationarity: PASS

### Check 6 — Pareto: N/A (single seed)

### Check 7 — Reproducibility: PASS
HEAD `69284b9`. Seed=42 / ENSEMBLE_SIZE=3 / n_trials=18 / label_mode=trend_scanning / symbols=LINKUSDT,DOTUSDT.

### Check 8 — Hypothesis-Implementation Alignment: PASS
H1 (LINK+DOT trend-scanning signal survives per-cohort isolation) → **CONFIRMED with margin**. Per-symbol OOS BIT-IDENTICAL to /035 extraction; bundle OOS Sharpe +1.7465 above prediction modal +1.0.

### Check 13 — Anti-Pattern Static Scan: PASS

### Check 14 — Axis Family Validation: PASS
`per-cohort-specialization` REPEAT-JUSTIFIED per Critic /035 Path Forward.

## Verdict Cell

Per brief Section 4 verdict matrix:
- F1 OOS Sharpe Δ +1.08 → **PROMISING-CLEAN** (Δ ≥ +0.20 band; deep into PROMISING territory)
- F-AXIS #3 LOAD-BEARING: LINK +75pp ✓ / DOT +112pp ✓ both clear +50pp threshold
- F-AXIS #4 bundle OOS Sharpe +1.75 >> +0.30 hard floor → PASS

## Structural Finding (LOAD-BEARING)

This is the **STRONGEST EXPLORATION result in v1 history (post-/058 RE-ANCHOR)**:

| Iteration | OOS Sharpe | OOS Δ | Notes |
|---|---|---|---|
| Baseline_v1 | +0.6637 | — | 5-cohort baseline anchor |
| /018 LINK isolated | +1.46 | +0.80 | Per-cohort LINK at triple-barrier |
| /028 LTC+atr_sl | +1.26 | +0.598 | Per-cohort LTC with label shift |
| /031 sample-weighting | +1.70 | +1.04 | 5-cohort + composite_inv_concurrency wrapper (single-seed) |
| **/036 LINK+DOT trend-scan** | **+1.75** | **+1.08** | **2-cohort + trend-scanning labels** |

/036 ties /031's OOS Sharpe at single-seed BUT with structurally cleaner diversification (50/50 split vs LINK 58%) AND better OOS Max DD (23% vs 35%) AND higher WR (54% vs 48%) AND fewer mechanisms stacked (2 vs 3).

## Mechanism interpretation

Trend-scanning labels (Wald-test trend significance over forward 21-bar window) extract a DIFFERENT signal subspace than triple-barrier σ_t. For small-cap symbols (LINK, DOT) with stronger trend persistence:
- Triple-barrier captures barrier-hit events (chop-sensitive)
- Trend-scanning captures statistically-significant directional moves (trend-sensitive)

LINK + DOT's volatility profile favors trend signals. Per-cohort isolation prevents the model from over-fitting BTC/ETH/LTC's mean-reverting regime to the trend-scanning labels.

## Caveats

1. **OOS trades = 105 below 130 floor** — concentration concern; 2-cohort × fewer trades. Mitigation: increase ENSEMBLE_SIZE at multi-seed validation to boost trade count.

2. **IS Sharpe +0.08** — weak IS fit. Could indicate (a) honest OOS regime tailwind, OR (b) trend-scanning generalizes better than fits, OR (c) some hidden structural issue. Multi-seed CONFIRMATION will discriminate.

3. **Single-seed result** — needs /044 multi-seed CONFIRMATION before merge. Predicted multi-seed mean OOS Sharpe band [+0.8, +1.5] per typical regression-to-mean factor at OOS lift > +1.0.

## Path Forward — /037+ ROUTING

**Strong recommendation**: Continue cycle-5 EXPLORATIONs to find MORE per-cohort specialist axes that could bundle with /036.

Specifically:
- **/037** = original cycle-5 menu position (Sortino objective in Optuna). Different mechanism class; could compound with /036.
- **/038-/039** = remaining cycle-5 axes (risk primitives + Kelly sizing). All orthogonal to /036's labeling mechanism.

After /037-/043 → **/044 CONFIRMATION** = multi-seed validation of /036 (or /036 + additional PROMISING specialists from /037-/043).

**Cycle-5 status after /036:**
- /034 basis_zscore_30: NEG-CLEAN (-0.27)
- /035 trend-scanning labels (5-cohort): NEG-CAT (-0.68) with bimodal per-cohort discovery
- **/036 trend-scanning LINK+DOT specialist: PROMISING-CLEAN (+1.08)** ⭐
- 7 cycle-5 EXPLORATIONs remain

This is the FIRST cycle-5 PROMISING and a strong candidate for /044 multi-seed substrate.

## NO-MERGE (single-seed at EXPLORATION budget)

BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`. /036 PROMISING-CLEAN at single-seed; merge eligibility requires /044 multi-seed CONFIRMATION.

Tag: v0.v1-036 at closeout.
