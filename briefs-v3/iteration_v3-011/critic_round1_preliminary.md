# Phase 7.5 Critic Review — iter-v3/011 — PRELIMINARY

**Iteration Type**: EXPLORATION (catalog row #4 since last CONFIRMATION; risk-gate axis per Critic FINAL Rec 1 of iter-v3/010)
**Mode**: Round 1 — PRELIMINARY (NO OVERALL verdict yet)
**Code SHA**: `9b4af01` | Brief SHA: `1bd02dc` | Phase 5.5 Gate SHA: `138e861` | Engineering Report SHA: `642cc45` | Analysis SHA: `17d01ab`

Per Section 0.5 TYPE=EXPLORATION cadence rules: methodology axes (look-ahead, embargo, IC, ADF, Pareto, hypothesis-implementation alignment) enforced; edge axis (DSR/PSR) is INFORMATIONAL only.

---

## Per-Check Status (Preliminary)

### Check 1 — Look-Ahead Audit: PASS
ZERO new feature code. Single behavior change is `RiskV2Config.zscore_threshold` 2.5 → 2.0 at `run_baseline_v3.py:873`. The z-score gate at `risk_v2.py:274-286` computes per-symbol mean/std snapshots over the IS window (`risk_v2.py:222-226`, masked by `open_time < OOS_CUTOFF_MS`) then evaluates `np.abs((x - mu) / sd)` on the live row's V2_FEATURE_COLUMNS. The training-window snapshot is NOT recomputed across OOS bars — confirmed at `risk_v2.py:221`. No look-ahead path created by the threshold tightening.

### Check 2 — Embargo Width: PASS
Required gap = `(timeout_candles+1) × n_symbols = (21+1) × 4 = 88`. Engineering report banner confirms PASS. Per-symbol fold gap = 22 rows × 184h. Identical to iter-v3/010.

### Check 3 — Multiple-Testing Correction: METHODOLOGY-PASS / EDGE-INFORMATIONAL
- PBO (per-cell mean) = **0.10770** << 0.40 threshold (identical to iter-v3/010 — methodology stable across gate perturbation).
- PBO `frac_positive_paths=0.600` from 45 paths.
- n_eff (per-cell median) = **7** > 4 minimum.
- n_trials = 40. Matches `--n-trials 10 × 4 symbols` budget.
- `n_high_pbo_cells` (PBO ≥ 0.9) = **6** (BCH/2024-10, MKR/2022-10, MKR/2025-04, MKR/2025-07, TRX/2025-10, TRX/2025-11) vs iter-v3/010's 5. Slightly more outlier cells under tighter gate.
- DSR=0.0, PSR=1.0 — single-seed exploration artifact, INFORMATIONAL per cadence.

Methodology axis: PASS.

### Check 4 — IC Correlation: PASS
Max off-diagonal `|IC_pearson| = 0.660` at (`max_dd_window_50`, `range_realized_vol_50`); ZERO pairs ≥ 0.70 threshold. Identical to iter-v3/010 (same 13 features, same IS data).

### Check 5 — ADF Stationarity: WARN (carry-forward)
2769 (symbol, feature, month) cells; 82.3% stationary. Same per-month low-T artifact as iter-v3/010.

### Check 6 — Pareto Dominance: WAIVED (single-seed exploration)
1 row in `pareto_front.csv`. WAIVED. Note: `max_concentration_pct = 64.94%` (LDO) substantially exceeds the 35% per-symbol cap that would apply at CONFIRMATION; informational under EXPLORATION — see Clarification 2.

### Check 7 — Reproducibility: PASS
Code SHA `9b4af01` stamped; analysis SHA `17d01ab` predates brief; ITERATION_LABEL=v3-011 confirmed; feature_columns explicit. Trade-row spot-check OOS row 1 (MKR SHORT) reproduces `-3.6867%`.

### Check 8 — Hypothesis-Implementation Alignment: PASS
The single change is `zscore_threshold=2.0` at `run_baseline_v3.py:873`. ATR multipliers UNCHANGED (2.0/1.0 inherited), feature count UNCHANGED at 13. Single-axis cadence rule honored.

Falsifiers 1, 2, 3 NOT triggered.

**Calibration miss documented**: IS Sharpe = +0.9566 overshoots predicted band [+0.30, +0.70] by +0.26 in the FAVORABLE direction. SECOND consecutive overshoot in favorable direction (iter-v3/010 also overshot by +0.27). Pattern flag for future calibration; not a methodology defect.

### Check 9 — Symbol Exclusion Enforcement: PASS

### Check 10 — Feature Isolation Enforcement: PASS

### Check 11 — Forming-Candle Audit: PASS (with documented re-fetch)
First launch failed staleness check (19.6h > 16h); re-fetched 2 klines × 5 symbols + regenerated features. Process artifact, not methodology issue.

### Check 12 — Library Version Pinning: PASS
Stack identical to iter-v3/010.

---

## Forensic Observations (Not Check Failures, Surface Areas for Clarification)

**Observation 1 — MKR pattern: 4th consecutive negative, monotonically worsening magnitude.**

| Iteration | OOS MKR weighted PnL | OOS MKR net PnL% | OOS MKR n_trades | OOS MKR WR |
|---|---:|---:|---:|---:|
| iter-v3/007 | -27.84% pct_of_total | -6.49% | 12 | 33.3% |
| iter-v3/009 | -16.06% pct_of_total | -13.10% | 13 | 30.8% |
| iter-v3/010 | -8.88% conc | -10.65% | 17 | 29.4% |
| **iter-v3/011** | **-32.92% conc** | **-25.75%** | 16 | **25.0%** |

Per Critic Disposition on iter-v3/010 Clarification 2: per-symbol-exclusion threshold set at "6-7 consecutive negatives". iter-v3/011 brings the count to 4, with the WORST WR (25.0%) and WORST net PnL (-25.75%) of the v3 history. The IS MKR also degraded (-23.21% net PnL, 33.8% WR). The tightening killed 49.8% of MKR signals (vs ~35% under z=2.5) — the highest of any symbol — yet MKR's per-trade economics WORSENED rather than improved.

**Observation 2 — LDO concentration regression toward iter-v3/009's lottery pattern.**

| Iteration | OOS LDO trades | LDO WR | LDO concentration | LDO net PnL% | Other-3-symbols sum |
|---|---:|---:|---:|---:|---:|
| iter-v3/009 | 12 | 75.0% | 98.61% | +85.51% | -4.86% |
| iter-v3/010 | 16 | 50.0% | 40.66% | +27.41% | broad-based 3/4 positive |
| **iter-v3/011** | **10** | **80.0%** | **86.31%** | **+56.25%** | BCH +28.40% / TRX +14.47% / MKR -48.23% |

The iter-v3/011 OOS pattern returns toward iter-v3/009's lottery character: 10-trade LDO with 80% WR drives 86.31% concentration. Exact-binomial 95% CI on 80% WR over 10 trades is approximately [44.4%, 97.5%] — too wide to claim signal.

**Observation 3 — OOS trade rate moves further from the 10/month floor.**

| Iteration | OOS trades | Trades/month | Distance from 10/month floor |
|---|---:|---:|---:|
| iter-v3/009 | 87 | 6.44 | -3.56 |
| iter-v3/010 | 109 | 8.07 | -1.93 |
| **iter-v3/011** | **101** | **7.48** | **-2.52** |

The pre-committed bundle-level rule holds, but the gate-axis EXPLORATION moves trade rate AWAY from the floor.

**Observation 4 — IS Sharpe calibration band overshoot is now systematic on the favorable side.**
Two consecutive iterations (010, 011) overshot the predicted upper band by +0.26 / +0.27 in the favorable direction.

**Observation 5 — TRX IS PnL sign-flip vs iter-v3/010, MKR IS partial recovery.**
TRX flipped IS-negative under z=2.0 (-19.96% net PnL) vs iter-v3/010's +19.49% IS-positive. MKR IS slightly improved but still IS-negative.

---

## Clarifications Requested from QR

**Clarification 1 — MKR catalog disposition with 4th consecutive negative.**
Per iter-v3/010 review FINAL Clarification 2 disposition: per-symbol-exclusion threshold set at "6-7 consecutive negatives". iter-v3/011 brings MKR to 4/4 negative with WORST WR (25.0%) and WORST net PnL (-25.75%) of v3 history. The tighter z=2.0 gate filtered MKR signals MORE aggressively (49.8% kill rate) yet per-trade MKR economics still WORSENED. This refutes the implicit "more filtering will help MKR" hypothesis.

(a) Should the catalog row note that increased z-gate aggression on MKR did NOT correct the per-symbol pattern (structural MKR underperformance is gate-orthogonal)?
(b) Does the threshold remain at 6-7, OR does the worsening magnitude trajectory compress it to 5?

**Clarification 2 — LDO concentration-vs-coverage trade-off catalog framing.**
iter-v3/011's OOS pattern (LDO 86.31% concentration, 10 trades, 80% WR) structurally resembles iter-v3/009's NEGATIVE-flagged lottery (98.61% LDO, 12 trades, 75% WR). The differentiator that gave iter-v3/010 PROMISING was "3/4 symbols OOS-positive on standalone basis" — iter-v3/011 fails this strictly (only 3/4 net-positive but with extreme LDO concentration). Should the catalog row flag the regression toward iter-v3/009's lottery pattern explicitly, OR does iter-v3/010's PROMISING differentiator still hold?

**Clarification 3 — Trade-rate floor recoverability check explicit at the iter-v3/011 catalog row.**
iter-v3/011 at 7.48/month single-seed implies 22-30 trades/month at 5-seed×ensemble=5 multiplication if the 3-4× factor cited in iter-v3/010 review holds. At 13.5 OOS months, that gives 303-405 OOS bundle trades — well above 130. But the multiplication factor is unverified. Should the catalog row record an explicit "floor-recoverable check" computation?

**Clarification 4 — Data-extent drift from feature regen.**
First launch failed staleness; re-fetched 2 klines + regenerated features. The added 16h is PRE-OOS-cutoff for IS half. Drift is structurally identical to iter-v3/010's own data-extent moment. Should iter-v3/011 vs iter-v3/010 OOS Sharpe delta (-0.187) be partly attributed to additional OOS data, or purely the gate-axis effect?

---

## What This Round 1 Did NOT Resolve

OVERALL verdict held for Round 2 FINAL after QR responds to the four clarifications. The methodology axes ALL clear at PRELIMINARY (Checks 1-12 all PASS / WARN-carry-forward / WAIVED-single-seed; no BLOCK conditions). The remaining decision rests on the catalog-disposition coherence questions: how the four observed patterns are encoded in the iter-v3/011 catalog row so the future CONFIRMATION QR inherits a clean audit trail.
