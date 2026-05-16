# iter-v3/068 — Cycle 1 #9 NEGATIVE / Labeling-timeout doubling failed catastrophically

**Date**: 2026-05-14
**Type**: EXPLORATION (cycle 1 #9 of 10; NON-FEATURE PIVOT; LABELING TIMEOUT axis Path C)
**Axis**: UNIVERSAL `label_timeout_minutes` 10080 → 20160 (21 → 42 candles at 8h) + REVERT /067 inference_threshold_floor
**Verdict**: EXPLORATION-MERGE per Critic FINAL — NEGATIVE certified methodologically clean
**Classification**: NEGATIVE per Section 8.4 disjunctive OR (BOTH gates triggered)
**BASELINE_V3.md**: UNCHANGED (/059 canonical)

## 1. What was done

Per orchestrator autopilot, /068 tested labeling-timeout axis. QR EDA `c16d53c` chose Path C (timeout doubling) per evidence: only Path with predicted IS Δ band centered + non-zero PROMISING upside. REQUIRED_GAP recalculated 66 → 129.

Commit chain: EDA `c16d53c` → setup `06a8cc2` → impl `0e9eb30` → gate `0ac455b` → engineering report `05b8257` → Critic review (this commit). Wall-clock 0.70h.

**Pre-flight blocked once** on data staleness (16.6h > 16h threshold). Orchestrator refreshed klines (2 candles per symbol) and re-launched cleanly.

## 2. Results

| Metric | /060 anchor | /068 (timeout=42) | Δ |
|---|---|---|---|
| IS Sharpe | +0.8325 | +0.4817 | **-0.35** |
| OOS Sharpe | +0.1403 | **-0.3396** | **-0.48** |
| OOS/IS daily ratio | 0.28 | -0.67 | sign-flipped |
| OOS PF | 1.21 | **0.89** | LOSING OOS |
| OOS MaxDD | 34.53% | **62.76%** | **+28pp** |
| IS trades | 159 | 184 | +25 |
| OOS trades | 102 | 102 | 0 |
| frac_positive_paths | 0.6444 | 0.6444 | 0 |
| PSR | 0.9763 | **0.0000** | -0.98 (sign-flip) |

Per-symbol OOS:
- BCH +9.62 (39 tr, 35.9% WR)
- **LDO -38.98 (12 tr, 8.3% WR — 1 win of 12)** — CATASTROPHIC; third consecutive cycle 1 LDO failure
- TRX +14.92 (51 tr, 41.2% WR)

## 3. Mechanism: hypothesis falsified

Brief T3 EDA prediction: "LDO has ZERO timeouts at K=21 — INSENSITIVE to timeout extension. /068 cannot fix LDO via this axis." Observed: LDO got WORSE (8.3% WR vs /060 18.2%, vs /064 7.1%).

**Why LDO collapsed**: with doubled embargo (43 vs 22 candles per cell, CV gap 129 vs 66), training samples reduced ~3-5% per WF month. LDO has lowest absolute trade count (9 IS, 11 OOS at /060). With fewer training labels + larger noise floor, Optuna at n_trials=35 cannot distinguish signal from noise for LDO → degenerate model.

**Why OOS MaxDD doubled**: NOT mechanically explained by longer-held trades (trades remain barrier-bound at /068 — most close 1-7 candles via TP/SL). Optuna re-converged under doubled embargo to a model that picks WORSE OOS trades (lower per-trade quality). 62.76% across 102 trades consistent with the 14-week LDO+TRX bleed period.

## 4. Critic verdict summary

OVERALL=MERGE (NEGATIVE certified clean). 13/13 Checks PASS or PASS-equivalent (Check 3 PSR=0.0 informational at EXPLORATION). §11 Anti-Pattern Scan CLEAN. Foundation Audit: walk-forward fix INTACT, REQUIRED_GAP correctly updated, embargo math verified (embargo_ms > timeout_ms by 1 candle = canonical purge).

Anchor-byte-correctness PASS (no /065-style recurrence). All four adversarial questions resolved:
- OOS MaxDD doubling = legitimate Optuna re-convergence under embargo cost, not bug
- LDO collapse = pure axis-driven (training-sample loss hits low-trade-count symbol hardest)
- PSR=0.0 = mathematically sound (sign-flip in observed_sharpe)
- Anchor values byte-correct vs /060 comparison.csv

## 5. PATH classification

**NEGATIVE** per brief Section 8.4 LOCKED. Both disjunctive-OR gates triggered (IS<-0.20 AND OOS<-0.30). Pre-registered Section 8.5 NEGATIVE-EMBARGO-COUPLED sub-mode FIRED (25% probability mass HIT). Axis CLOSED. Labeling-timeout family CLOSED in both directions (Path A reduction = different mechanism, but pre-registered NEGATIVE; Path C/D extension = embargo-coupled cost dominates label-cleanup benefit).

## 6. Hypothesis check — calibrated probability HIT; magnitude under-quantified

Brief Section 7 4-mode table: INERT 50%, PROMISING 15%, NEGATIVE 25%, SUSPICIOUS-OOS 10%. NEGATIVE HIT.

**Prediction-band miscalibration** (per Critic Finding F1): T4 predicted IS Δ [-0.10, +0.10] / OOS Δ [-0.15, +0.15]. Observed -0.35/-0.48 are 2-3× the lower bound. Section 7 NEGATIVE expected-metrics IS consistent with floor of disjunctive-OR gate (-0.20 IS / -0.30 OOS) but the MAGNITUDE was under-quantified. Future labeling-DURATION axes should pre-register full [-0.50, +0.50] envelope.

## 7. BASELINE_V3.md status

UNCHANGED — /059 stays canonical at `v0.v3-059`.

## 8. Critic Recommendations carried forward

1. **Pre-register magnitude bands wider for labeling-axis EXPLORATIONs** (per F1). Future labeling-DURATION axes use [-0.50, +0.50] envelope.

2. **Address inherited IC violation at /070 CONFIRMATION bundle composition**. vwap_dev_20 × regime_momentum_signed_5d = 0.7642 (composed-feature carve-out from /059 baseline). Document or address in /070 bundle review.

3. **LDO weakness pattern: /060 18.2% / /064 7.1% / /068 8.3% OOS WR demands LDO-targeted axis at /069 or post-/070**. Three consecutive cycle 1 failures. Escalate to feature/model axis (NOT labeling-timeout/SL — closed). Candidates: LDO-only feature_columns variation, LDO-only ATR override, or universe expansion to dilute concentration per `feedback_v3_concentration_is_signal.md`.

## 9. Next Iteration Ideas

Cycle 1 progress: 9/10 EXPLORATIONs done.

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /060 | EXPLORATION-MODE-REFERENCE (anchor) | PROMISING-EXPLORATION |
| #2 | /061 | TRX vol_scale_floor | INERT (closed) |
| #3 | /062 | DSR_relative recalibration | PASSIVE-DIAGNOSTIC |
| #4 | /063 | MASS FEATURE EXPANSION 14→46 | SUSPICIOUS-OOS+IS-COLLAPSE |
| #5 | /064 | Phased +adx_14 | NEGATIVE |
| #6 | /065 | UNIVERSAL labeling Path D (SL=1.5) | **SUSPICIOUS-OOS-DOMINANT** (FIRST /070 candidate) |
| #7 | /066 | UNIVERSAL vol_scale_ceiling=0.8 | INERT (ceiling family CLOSED) |
| #8 | /067 | Confidence threshold floor=0.60 | INERT (Path D non-activation) |
| **#9** | **/068** | **Label timeout 21→42 candles (Path C)** | **NEGATIVE (timeout family CLOSED both directions)** |
| #10 | /069 | TBD per QR EDA + Critic Rec #3 LDO-targeted axis | TBD |
| CONFIRMATION | /070 | Bundle: /065 SL widening + /062 Path B4 | TBD |

**iter-v3/069 axis candidates** (NON-FEATURE per Critic /064 Rec #4; AVOID universal-symmetric-clip per /066 Rec #2; AVOID timeout family per /068; ADDRESS LDO weakness per Critic /068 Rec #3):
- **Universe expansion** (4th symbol; dilutes LDO concentration; denominator-expansion mechanism)
- **LDO-targeted feature_columns variation** (per-symbol feature override; CAREFUL per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` — needs IS-preservation pre-falsifier)
- **PASSIVE-DIAGNOSTIC alternative** (if QR EDA finds no high-confidence axis at single-seed; defer to /070 bundle composition + Path B4 carry-forward refinement)
- /070 bundle: /065 SL widening + /062 Path B4 deferred spec (unchanged through /066-/068 INERT/NEGATIVE)
