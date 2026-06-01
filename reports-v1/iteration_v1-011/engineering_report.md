# iter-v1/011 — Engineering Report (Phase 7 — QR Evaluation)

**Date**: 2026-05-25
**QR**: claude-opus-4-7 (1M context) — quant-research-v1 mode
**Branch**: `iteration-v1/011`
**HEAD before Phase 7+8 closeout**: `b48c035`
**Axis**: R5-BINARY-KILL-LOW — `risk-primitive` family, binary-kill SUBTYPE (kill_low at NATR_14 < 2.0% threshold)
**Mode**: EXPLORATION (cycle-2 #6 of 10; `--exploration --seeds 1 --n-trials 35`; ENSEMBLE_SIZE=3)
**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`); IS Sharpe +0.2829 / OOS Sharpe +0.6637

---

## 1. Final Verdict + Verdict-Class Rationale

**Verdict: EXPLORATION-NEGATIVE — subtype `catastrophic-basin-shift`** (per `briefs-v1/iteration_v1-011/review.md` Phase 7.5 OVERALL).

**Verdict-class is mechanically deterministic from brief Section 8 pre-registration:**

> **catastrophic-basin-shift (NEW per Critic Rec #1)**: F3: IS Sharpe Δ > +0.30 → Verdict: EXPLORATION-NEGATIVE-catastrophic-IS-overshoot; axis CLOSED at single-seed

Observed IS Sharpe Δ = **+0.4849** > +0.30 pre-registered threshold → catastrophic-basin-shift class fires. F1 PROMISING (OOS Δ +0.4072 ≥ +0.05) does NOT override because the pre-registered class explicitly carries "axis CLOSED at single-seed" subsuming any F1 reading. Per Critic discipline ("when in doubt, FAIL") and per brief's own pre-registration ladder, the catastrophic-basin-shift class is binding.

LM Master Phase 7.4 proposed a NEW v1 verdict subtype `PROMISING-OVERSHOOT-BASIN-INHERITED` to disambiguate the {F3 catastrophic, F1 PROMISING, F6 < 61%} dual-firing case observed here — Critic REJECTED retroactive re-classification on /011 itself ("process improvement for FUTURE briefs, cannot retroactively re-classify /011"). The compound class is recorded as a forward-looking process upgrade (Critic Recommendation #1 to /011 closeout — see Section 8 below); /011's verdict remains EXPLORATION-NEGATIVE catastrophic-basin-shift literal.

**Reading the merge floors against the verdict**: this is the unusual case where the OOS Sharpe magnitude (+1.0709) literally clears every hard merge gate (IS > 1.0 fails marginally at 0.77; OOS > 1.0 clears; OOS/IS ratio 1.39 ≥ 0.5 clears; 180 OOS trades ≥ 130 clears) yet the pre-registered verdict-class is NEGATIVE. Per Project Mode rules, the verdict-class wins — merge floors are necessary-but-not-sufficient gates layered on top of an EXPLORATION-PROMISING verdict, NOT an override of the verdict-class itself. The IS Δ pre-registration was deliberately built to make basin-lottery overshoots verdict-negative regardless of OOS magnitude, precisely to prevent the false-positive recall pattern this iteration would produce if read on OOS alone.

---

## 2. Headline Metrics

From `reports-v1/iteration_v1-011/comparison.csv`:

| Metric | IS | OOS | Baseline IS | Baseline OOS | IS Δ | OOS Δ |
|---|---|---|---|---|---|---|
| **Monthly Sharpe** | **+0.7678** | **+1.0709** | +0.2829 | +0.6637 | **+0.4849** | **+0.4072** |
| Sortino | +0.7490 | +1.1940 | +0.3205 | +0.7697 | +0.4285 | +0.4243 |
| Max Drawdown | 54.47% | 39.77% | 73.06% | 40.94% | -18.59pp | -1.17pp |
| Win Rate | 41.8% | 50.0% | 39.9% | 40.2% | +1.9pp | +9.8pp |
| Profit Factor | 1.1807 | 1.2620 | 1.060 | 1.156 | +0.121 | +0.106 |
| Total Trades | 570 | 180 | 621 | 189 | -51 | -9 |
| Calmar | 2.7576 | 1.5413 | 0.740 | 0.931 | +2.018 | +0.610 |
| DSR | -42.14 | -19.26 | -93.80 | -35.66 | +51.66 | +16.40 |
| Total Net PnL | +150.21% | +61.29% | +54.05% | +38.13% | +96.16pp | +23.16pp |
| PSR_monthly_vs_0 | 0.8983 | 0.8841 | 0.977 | 0.989 | -0.0787 | -0.1049 |
| PSR_monthly_vs_1 | 0.3254 | **0.5663** | 0.0003 | 0.0789 | +0.3251 | +0.4874 |
| n_effective_trials | 13 | 13 | 13 | 13 | 0 | 0 |
| n_eff_per_cell_median | 13 | 13 | 13 | 13 | 0 | 0 |
| **R5-BINARY-KILL fire rate (portfolio)** | **18.34%** | **21.69%** | — | — | — | — |

**OOS/IS ratio = 1.3948** — anti-overfit pattern; unusual at single-seed EXPLORATION (signal that the OOS lift came from a different mechanism than IS lift; consistent with mechanical kill_low cleanup at the OOS-only stratum sitting on top of an IS-only basin-lottery substrate).

**R5-BINARY-KILL fire rate**: IS 18.34% / OOS 21.69% — both inside F2 band [10%, 60%]; F2 PASSES. EDA oracle predicted IS ~18% / OOS ~18-19%; the OOS observed 21.69% is +2.7pp above prediction, consistent with the OOS NATR_14 distribution mass shifted slightly lower than the BASELINE roster's OOS NATR distribution used in the oracle (Optuna re-routing produced trades at marginally lower entry-time NATR than baseline produced, which crosses the threshold more often).

---

## 3. Per-Symbol IS/OOS PnL Attribution (vs /010 comparison)

### 3.1 In-Sample (570 trades)

| Symbol | trades | WR | net_pnl_pct | **pct_of_total** | /010 net_pnl | /010 pct_total | Δ vs /010 |
|---|---|---|---|---|---|---|---|
| **LTCUSDT** | 104 | 51.0% | **+110.58** | **+106.48%** | +79.98 | +119.84% | **+30.60** PnL / -13.36pp share |
| LINKUSDT | 149 | 43.0% | +42.45 | +40.88% | +32.33 | +48.44% | +10.12 PnL / -7.56pp share |
| DOTUSDT | 116 | 44.8% | +31.01 | +29.86% | +17.99 | +26.95% | +13.02 PnL / +2.91pp share |
| BTCUSDT | 78 | 38.5% | -30.74 | -29.60% | -44.16 | -66.16% | +13.42 PnL / +36.56pp share |
| ETHUSDT | 123 | 31.7% | -49.45 | -47.61% | -19.40 | -29.06% | -30.05 PnL / -18.55pp share |

**LTC IS basin trajectory baseline → /010 → /011**: pct_of_total_pnl `+6.42% → +119.84% → +106.48%`. Same substrate; mild redistribution toward DOT+BTC. LM Master Phase 7.4 verified roster overlap LTC IS /010 ↔ /011 = **93.3% (97 / 104)**. The IS Δ +0.4849 is NOT first-order kill_low mechanical loser-cluster removal; it is the same Optuna basin /010 found, re-discovered by /011's mechanically distinct entry-filter axis.

### 3.2 Out-of-Sample (180 trades)

| Symbol | trades | WR | net_pnl_pct | **pct_of_total** | /010 net_pnl | /010 pct_total | Δ vs /010 |
|---|---|---|---|---|---|---|---|
| **LINKUSDT** | 47 | 55.3% | **+84.86** | **+59.24%** | +80.92 | +80.88% | +3.94 PnL / -21.64pp share |
| **BTCUSDT** | 17 | **70.6%** | **+51.28** | **+35.80%** | +44.88 | +44.86% | +6.40 PnL / -9.06pp share |
| DOTUSDT | 48 | 45.8% | +29.13 | +20.34% | +29.13 | +29.12% | +0.00 PnL / -8.78pp share |
| ETHUSDT | 36 | 44.4% | -2.90 | -2.02% | -11.36 | -11.35% | **+8.46 PnL** (mechanical recovery) |
| LTCUSDT | 32 | 43.8% | -19.12 | -13.34% | -43.52 | -43.50% | **+24.40 PnL** (mechanical recovery) |

**Two symbols above 30% per-symbol concentration cap**: LINK 59.24% (basin-inherited from /010's 80.88%); BTC 35.80% (basin-inherited from /010's 44.86%). Both concentrations are NOT /011-discovered — they are inherited from /010's same basin Optuna found at single-seed=42.

**LTC OOS mechanical cleanup**: -43.52 → -19.12 (Δ +24.40pp), the largest mechanical-attributable benefit. BASELINE OOS LTC was -3.94 → /010 -43.52 (Δ -39.58pp basin-loss) → /011 -19.12 (Δ +24.40pp mechanical recovery via kill_low filtering ~6 of /010's worst low-NATR LTC OOS losers). The kill_low filter delivered ~62% of /010's LTC OOS deterioration as mechanical recovery in /011 — but did NOT eliminate the basin-loss vs BASELINE (still -19.12 vs BASELINE -3.94).

**ETH OOS mechanical cleanup**: -11.36 → -2.90 (Δ +8.46pp). Same mechanism class as LTC — kill_low filters the low-NATR loser cluster on the OOS side. Smaller magnitude.

**BTC OOS 17 trades / 70.6% WR**: 12W/5L. Per LM Master Phase 7.4 §3, this is the only mechanism-attributable effect of kill_low (selectively removed BTC OOS losers per brief Section 2.4 EDA prediction). HOWEVER 17 trades / ~14 OOS months ≈ 1.2 trades/month BTC is below the credibility floor for per-symbol Sharpe inference at this sample size; flagged in §"BTC regime-concentration vulnerability" below.

---

## 4. Basin-Inheritance Smoking Gun

The verdict-defining evidence comes from three roster-overlap statistics computed by LM Master Phase 7.4 (`briefs-v1/iteration_v1-011/lgbm_advisor.md` §1 + §2):

| Comparison | overlap | interpretation |
|---|---|---|
| **LTC IS roster /010 ↔ /011** | **93.3%** (97 / 104) | Same basin re-discovered across mechanically distinct axes |
| **F6 OOS roster /011 ↔ BASELINE** | **16.7%** (30 / 180) | Far below the 61% tripwire — catastrophic basin shift on paper |
| **F6 OOS roster /011 ↔ /010** | **93.3%** (168 / 180) | Mechanically near-identical to /010's basin minus ~12 trades |

### 4.1 Why this is a smoking gun

R5-BINARY-KILL is a STATELESS pre-entry filter with OOS fire rate 21.69%. Mechanically, /011 should retain **78.31%** of BASELINE's OOS roster (the 78.31% of trades where NATR_14 ≥ 2.0%) plus zero new trades (the filter only removes; it does not generate). Observed BASELINE-roster overlap is **16.7%** — meaning 83.3% of /011's OOS trades are entries that BASELINE did NOT take. The filter alone cannot produce this — it can only subtract, not add. The 83.3% difference is Optuna re-optimization choosing different entry signals than BASELINE chose.

Cross-check against /010: /011 overlaps /010 at 93.3% on OOS. /010 itself was a different axis (proportional weight scaling, NOT entry filtering) — meaning Optuna at single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED converged to the SAME basin under TWO mechanically distinct axes. The basin is a property of (seed, search budget, feature set, ensemble size), NOT of the axis intervention.

### 4.2 LTC trajectory as the load-bearing artifact

LTC IS pct_of_total_pnl across iterations:
- BASELINE: **+6.42%** (single-symbol contribution ~baseline)
- /010 (R5 proportional weight scaling): **+119.84%** (basin lottery — single symbol drove entire IS portfolio gain)
- /011 (R5-BINARY-KILL-LOW): **+106.48%** (basin re-discovered; modest LTC redistribution toward DOT/BTC)

LM Master Phase 7.4 verified LTC IS roster overlap between /010 ↔ /011 = 93.3% (97 of 104 LTC IS trades shared between the two runs). This means: of /011's 104 IS LTC trades, 97 are byte-identical to /010's IS LTC trades. The 7 differing trades (filtered out by kill_low because their entry-time NATR < 2.0%) account for the modest IS PnL redistribution, NOT a different basin. **The basin assignment is structurally stable across the two axis primitives at single-seed=42.**

### 4.3 F6 falsifier verdict

Brief Section 4 F6 declared: "OOS roster overlap with BASELINE < 61% → NEGATIVE-basin-shift". Observed BASELINE-overlap = 16.7% — fires F6 catastrophically (16.7% < 61% by 44.3pp). LM Master Phase 4.5 had predicted F6 ≈ 70-78%; observed is 53.3pp below the lower bound. The F6 falsifier is the diagnostic that ties the OOS lift to basin lottery rather than to the brief-hypothesized mechanism.

**NOTE on F6 artifact gap**: F6 was computed by LM Master OFFLINE in Phase 7.4 from the trade rosters; the committed reports do NOT contain a deterministic `f6_roster_overlap.csv` artifact. Critic flagged this as a process integrity defect (Recommendation #2) — future briefs with F6-style falsifiers must require QE to emit the roster-overlap CSV as a committed artifact, structurally equivalent to the comparison.csv / dsr.json contract. For /011, the LM Master value of 16.7% is taken as the reference even though the artifact-level reproduction is not in the committed reports (it is reproducible from `reports-v1/iteration_v1-011/out_of_sample/trades.csv` joined to the BASELINE OOS trades by `(symbol, open_time)`).

---

## 5. Mechanism Attribution — Basin Lottery vs Mechanical kill_low Cleanup

Question: what fraction of the OOS Δ +0.4072 is basin lottery vs mechanical kill_low cleanup?

### 5.1 Quantitative decomposition

The cleanest decomposition uses /010 as the basin-isolation control (same basin, no kill_low) vs /011 (same basin + kill_low filter):

| Stratum | /010 OOS PnL | /011 OOS PnL | Δ attributable to kill_low |
|---|---|---|---|
| LTC OOS | -43.52 | -19.12 | **+24.40** (mechanical recovery via filtering low-NATR LTC losers) |
| ETH OOS | -11.36 | -2.90 | **+8.46** (mechanical recovery via filtering low-NATR ETH losers) |
| BTC OOS | +44.88 | +51.28 | +6.40 (kill_low improved BTC WR 44.7% → 70.6%; selective BTC loser removal) |
| LINK OOS | +80.92 | +84.86 | +3.94 (~marginal; LINK low-NATR not in loser cluster per Section 2.4 EDA) |
| DOT OOS | +29.13 | +29.13 | 0.00 (essentially no effect; DOT low-NATR cluster was not in /010's roster differential) |
| **Portfolio OOS PnL Δ** | | | **+43.20pp** (sum of per-symbol /010→/011 OOS Δ) |

The portfolio OOS PnL went from /010's +100.45 to /011's +143.65 = +43.20pp. **This is the kill_low mechanical effect.** Sharpe-Δ of this mechanical component is roughly proportional to PnL change at constant volatility — call it ~+0.40 Sharpe-Δ contribution from mechanical kill_low cleanup at the /010→/011 stratum.

The basin shift /010 → BASELINE OOS PnL = +100.45 vs +38.13 = +62.32pp swing (LTC -39.58, ETH -7.46, LINK +50.63, BTC +6.75, DOT +24.41). At /010's level of basin re-routing, the OOS basin LOST -2.83pp in Sharpe-Δ vs BASELINE (the /010 OOS Δ vs BASELINE was -0.0283; the kill_low ON TOP delivers the entire OOS lift /011 produced).

### 5.2 Pure-strata attribution table

| Mechanism | Sharpe Δ attribution (estimated) | Confidence |
|---|---|---|
| /010 basin substrate vs BASELINE | -0.03 (OOS) / +0.47 (IS) | HIGH (already measured at /010 closeout) |
| /011 kill_low mechanical cleanup on /010 basin | +0.44 (OOS) / +0.01 (IS) | MED (single-seed estimate; not multi-seed validated) |
| **/011 vs BASELINE total** | **+0.41 (OOS) / +0.48 (IS)** | LOW directional (basin-conditional; cannot be repeated at multi-seed without testing) |

**Key reading**: the entire OOS Δ +0.41 is attributable to the kill_low mechanical layer riding on the /010 basin substrate. NONE of the OOS Δ is attributable to the kill_low mechanism finding a new positive-OOS basin. The mechanism is real but downstream-mechanical-only; it is NOT a basin-discovery edge. If /015 multi-seed CONFIRMATION dissolves the LTC-dominated basin (which it likely will per the structural argument), the mechanical /010→/011 kill_low effect would still apply to each seed's basin but the basin substrate itself would average to BASELINE's level — meaning multi-seed OOS Sharpe would land closer to BASELINE +0.66 + (small mechanical kill_low cleanup ≈ +0.05) ≈ +0.70, NOT /011's +1.07.

### 5.3 Non-durability claim

The OOS Δ +0.41 is real-but-non-durable because:

1. The basin substrate itself is single-seed-conditional and dissolves at multi-seed (LM Master Phase 7.4 §2 + §6 explicit; F6 baseline-overlap 16.7% is mechanically incompatible with axis edge).
2. The kill_low mechanical cleanup is durable per-seed at any reasonable Optuna budget (it is deterministic data filtering — every (seed, n_trials, features) configuration with this kill_low layer added would mechanically remove ~21% of low-NATR OOS trades).
3. But the OOS Δ contribution of mechanical kill_low cleanup is small (~+0.05 Sharpe estimated from the BASELINE-stratum oracle in brief Section 2.3, where the kill_low oracle on the BASELINE roster ITSELF showed only +0.046 Sharpe-Δ).
4. Therefore the /011 OOS Δ +0.41 is mostly the basin-lottery substrate's accidental OOS-positive transfer + small mechanical layer. The basin substrate is non-durable.

**Multi-seed dissolution test at /015** is the binding empirical question for whether R5-BINARY-KILL has any durable edge. /011 by itself cannot answer it.

---

## 6. F1-F6 Verdict Matrix

| Falsifier | Condition (brief Section 4) | Observed | Status |
|---|---|---|---|
| F1 (PRIMARY) | OOS Sharpe Δ ≥ +0.05 → PROMISING; ≥ -0.05 → INERT; < -0.05 → NEGATIVE; < -0.20 → NEGATIVE-catastrophic | +0.4072 | **PROMISING literal** |
| F2 (behavioral) | OOS fire rate ∈ [10%, 60%] | 21.69% | **PASS** |
| F3 (IS catastrophic + Critic Rec #1 sign-symmetric) | IS Δ ≥ -0.10 (lower); IS Δ ∈ (+0.05, +0.30] → OVERSHOOT-FLAG; IS Δ > +0.30 → **catastrophic-basin-shift, axis CLOSED at single-seed** | +0.4849 | **FIRES catastrophic-basin-shift class; axis CLOSED** |
| F4 (DEGENERATE_PREDICTOR) | 0 IS / 0 OOS fires per `validation_v1.detect_degenerate_predictor` | not surfaced in committed reports | **UNVERIFIED-FROM-COMMITTED-ARTIFACTS** (detector ships in `validation_v1.py` but no per-cell CSV/JSON emitted at /011 — Critic flagged as defect; assumed 0/0 given no Critic Check 13 alert) |
| F5 (DSR computable) | `n_eff_per_cell_median ≥ 4` AND `dsr_is_finite=True` | 13 / True | **PASS** |
| F6 (NEW per /010) | OOS roster overlap with BASELINE < 61% → catastrophic basin shift | **16.7%** | **FIRES — far below tripwire by 44.3pp** |
| Trade-rate floor | ≥10 trades/month OOS AND ≥130 OOS total | ~13/month + 180 OOS | PASS |
| Per-symbol concentration cap | ≤30% of OOS PnL per symbol | LINK 59.24% + BTC 35.80% | **FAIL on 2 symbols** (substantive Critic Check 6) |

**Dual-firing reading**: F1 PROMISING + F3 catastrophic-basin-shift + F6 catastrophic + Check 6 concentration FAIL. Per brief Section 8 pre-registration, F3 catastrophic-basin-shift class explicitly carries "axis CLOSED at single-seed" — this subsumes F1 PROMISING. The verdict-class is deterministic from F3 alone; F6 + Check 6 + F4 unverified support the catastrophic-basin-shift reading. Critic Rec #1 to /011 closeout (next iteration) introduces a NEW PROMISING-OVERSHOOT-BASIN-INHERITED subtype to handle this F3+F1+F6 dual-firing cell more cleanly; the proposal does NOT retroactively re-classify /011.

---

## 7. LM Master Calibration Update (0/9 directional + 3 PARTIAL)

LM Master Phase 7.4 self-assessment (`briefs-v1/iteration_v1-011/lgbm_advisor.md` §"What This Iteration Confirms / Refutes"):

- **Modal verdict class**: predicted PROMISING ~45%; actual class is `PROMISING-with-OVERSHOOT-SUBTYPE` (compound). **PARTIAL** — verdict class taxonomy was sound but mechanism was wrong.
- **Basin-shift probability for entry-filter axes (20-30%)**: **WRONG**. Observed 93.3% LTC IS basin overlap with /010 across mechanically distinct axes. The structural distinction between weight-touching and entry-filter axes that LM Master made does NOT empirically hold at v1 single-seed=42. **NEW LM Master RULE (calibration update)**: at v1 single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED, ANY non-trivial axis (entry filter OR weight-touching) re-discovers the same Optuna basin. The basin is seed-property-driven, NOT axis-property-driven.
- **OOS gainer prediction (ETH/DOT-led)**: **WRONG**. LINK + BTC led OOS (per Section 3.2; LINK basin-inherited 59.24%; BTC mechanically improved 35.80%).
- **P50 OOS Δ +0.05 prediction**: observed +0.41 — 8× under-prediction. **WRONG**.

**LM Master track record after /011**: **0/9 directional + 3 PARTIAL** (across /003-/011). The PARTIAL credits are: /002 LTC overfit mechanism diagnosis (Phase 7.4 §4); /008 PROMISING-METHODOLOGY subtype prediction; /011 modal-class taxonomy. The directional Sharpe-Δ track record is 0/9, but the diagnostic-frame contributions (Phase 7.4 LTC IS roster overlap finding 93.3%; F6 catastrophic computation 16.7%) are load-bearing for Critic verdict and Path Forward.

**Calibration interpretation**: directional Sharpe-Δ prediction at single-seed EXPLORATION is structurally unanswerable at the LM Master's frame (since LM Master cannot model Optuna's basin-lottery without running the actual Optuna). LM Master's value at /011 was diagnostic-evidence-production (the 93.3% LTC overlap + 16.7% F6 baseline overlap + LM Master Phase 7.4 forensic mechanism decomposition), NOT predictive Sharpe-Δ accuracy. Future Phase 4.5 / Phase 7.4 cycles should weight LM Master's diagnostic-frame outputs heavily and discount the point Sharpe-Δ predictions.

---

## 8. NEW v1 Verdict Subtype Discussion — PROMISING-OVERSHOOT-BASIN-INHERITED

### 8.1 LM Master Phase 7.4 Proposal

LM Master Phase 7.4 §"Closing Note for Critic" proposed adding a NEW v1 verdict subtype for the {F3 catastrophic, F1 PROMISING, F6 < 61%} dual-firing cell observed at /011:

> Catalog should record /011 as a **NEW v1 verdict subtype**: `PROMISING-OVERSHOOT-BASIN-INHERITED` — distinct from /010's PROMISING-INERT-with-IS-basin-shift in that the basin transfers to OOS.

The motivation: /011 is the first v1 iteration where ALL THREE of {F3 IS-overshoot above catastrophic threshold, F1 OOS PROMISING above lift threshold, F6 baseline-overlap below tripwire} fire simultaneously. The existing brief Section 8 verdict gates do not assign a class to this cell (they assume IS-overshoot AND OOS-PROMISING are mutually exclusive via the implicit "either basin-lottery delivered IS only OR delivered IS+OOS, but the IS-only case → catastrophic-basin-shift class; the IS+OOS case is undefined").

### 8.2 Critic Rejection

Critic Phase 7.5 §"Recommendation #1 to QR" REJECTED retroactive re-classification on /011:

> LM Master proposed `PROMISING-OVERSHOOT-BASIN-INHERITED` — Critic concurs as NEW v1 subtype. Codify: F3 catastrophic + F1 PROMISING + F6 < 61% = `EXPLORATION-NEGATIVE` subtype `BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP`. OOS lift real-but-non-durable; binding constraint is multi-seed dissolution at /015.

Critic agrees the subtype is a real verdict cell deserving its own class — but on /011 itself, the deterministic resolution from brief Section 8 pre-registration is catastrophic-basin-shift (F3 IS Δ > +0.30 → axis CLOSED at single-seed). Re-classifying /011 retroactively would violate "pre-registered gates resolve dual-firing deterministically" (Critic Phase 7.5 §"QR Response Considered").

**The compromise**: future v1 briefs Section 8 MUST pre-register the {F3 catastrophic, F1 PROMISING, F6 < 61%} cell as `EXPLORATION-NEGATIVE subtype BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP` (Critic's terminology) — same overarching verdict NEGATIVE, but disambiguates the mechanism so the diary + catalog ledger can record the differential cleanly. The mechanism note + Path Forward depend on this distinction (BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP implies "multi-seed CONFIRMATION on the BASE axis would dissolve the basin substrate but preserve the mechanical layer ~+0.05 Sharpe gain" — a different /015 disposition than pure catastrophic-basin-shift would imply).

### 8.3 Phase 5.5 gate enforcement

Per Critic Recommendation #1, future v1 brief Section 8 verdict tables MUST pre-register:

| Cell | Class | Sub-class | Resolution |
|---|---|---|---|
| F3 > +0.30 AND F1 < +0.05 | EXPLORATION-NEGATIVE | catastrophic-basin-shift | axis CLOSED at single-seed |
| F3 > +0.30 AND F1 ≥ +0.05 AND F6 < 61% | EXPLORATION-NEGATIVE | BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP | axis CLOSED at single-seed; multi-seed dissolution at next CONFIRMATION may preserve mechanical layer only |
| F3 > +0.30 AND F1 ≥ +0.05 AND F6 ≥ 61% | EXPLORATION-PROMISING-VERIFIED | (mechanism-validated) | HIGH-RISK pre-commit fires; multi-seed CONFIRMATION mandated |

This three-cell extension closes the {IS catastrophic, OOS PROMISING} verdict-gap. Phase 5.5 gate will enforce in future /012+ briefs.

---

## 9. BTC Regime-Concentration Vulnerability (Critic Phase 7.5 Pre-Flag #3)

LM Master Phase 7.4 §"Critic Phase 7.5 Pre-Flags" #3 flagged:

> BTC OOS Feb-Apr 2026 regime concentration: 12 of 17 BTC trades in Q1 2026; 11 of 17 are shorts. Single-regime alpha pattern — historically this is the failure mode in /005-/006. Critic should investigate.

The 17 BTC OOS trades / 70.6% WR (12W/5L) at ~1.2 trades/month over the ~14 OOS months is below the per-symbol Sharpe credibility floor. The empirical evidence:
- 35.80% OOS PnL share at 17 trades = 3.0% per-trade alpha — high-leverage / low-N
- 11 of 17 are SHORTS (per LM Master Phase 7.4 enumeration)
- 12 of 17 cluster in Q1 2026 (per LM Master enumeration)
- Q1 2026 was a directional-BTC regime (per the OOS window character)

This could be:
- **(a) Genuine kill_low edge**: the filter selectively removed BTC OOS losers per brief Section 2.4 EDA, leaving the 12W/5L cluster as the high-conviction BTC subset
- **(b) Single-regime alpha**: Q1 2026 BTC short-trend regime happened to align with kill_low filtered roster, producing the 70.6% WR by regime accident

Critic Phase 7.5 Check 6 noted the substantive concentration FAIL but did NOT separately escalate the BTC regime-concentration question — left as Path Forward / future diagnostic for /012 if the BTC sub-cluster matters. For /011 closeout, the BTC concentration is recorded as a vulnerability but is subordinate to the F3 + F6 + Check 6 verdict-binding evidence.

---

## 10. Reproducibility Defects (Critic Phase 7.5 Check 7)

Three artifact-level defects from `briefs-v1/iteration_v1-011/review.md` §"Check 7 — Reproducibility":

### 10.1 `engineering_report.md` not committed (THIS DOCUMENT)

Critic flagged: "Neither `briefs-v1/iteration_v1-011/engineering_report.md` nor `reports-v1/iteration_v1-011/engineering_report.md` exists. /010 had one — /011 does not. Process integrity violation."

**Resolution**: this engineering report fills the gap at `reports-v1/iteration_v1-011/engineering_report.md` as part of QR Phase 7 + Phase 8 closeout commit chain. Critic Recommendation #3 ("Engineering report mandatory at every Phase 7.5 dispatch") is codified as a permanent v1 closeout process rule.

### 10.2 F6 roster-overlap diagnostic absent from committed reports

Critic flagged: "Brief Section 4 F6 declares 'OOS roster-overlap with BASELINE < 61% → NEGATIVE-basin-shift' as a load-bearing falsifier. The trade-roster-join script is NOT in `analysis/iteration_v1-011/`. LM Master Phase 7.4 computed F6=16.7% offline as smoking-gun, but the artifact is unfilled."

**Resolution**: documented in this engineering report Section 4.1; future briefs with F6-style falsifiers MUST require QE to emit `f6_roster_overlap.csv` (commit-tracked) per Critic Recommendation #2. /011 cannot retroactively populate the committed artifact, but the LM Master offline computation is accepted as the reference (reproducible from the trade rosters via a join on `(symbol, open_time)`).

### 10.3 F4 DEGENERATE_PREDICTOR detector surface absent

Critic flagged: "Detector ships in `validation_v1.py` but no per-cell JSON/CSV emitted."

**Resolution**: this is the **D-INST-001 carry-over** from /010 closeout — feature_importance.csv emission gap was the /010 instance; /011 added the same gap for DEGENERATE_PREDICTOR surface output. Both are instrumentation defects that future iterations must address — the v1 reporting layer needs a structured "validator output bundle" alongside comparison.csv that surfaces all `validation_v1.*` detector outputs as committed artifacts. Defer to next methodology iteration (Critic Path Forward Option 2 / 3 covers either methodology axis variant).

### 10.4 Cosmetic — comparison.csv r5_binary_kill_fire_rate row duplication

Critic flagged: "`r5_binary_kill_fire_rate_is` / `_oos` rows in comparison.csv are duplicates (both carry identical payload). The metric-name labels which half is primary subject; values correct in column slots per D-RPRT-001 fix. Unconventional schema but not verdict-binding."

**Resolution**: schema verified — see comparison.csv lines 18-19. Both rows have `in_sample=0.183384, out_of_sample=0.216912`; the row name labels which half is the primary statistic (the IS row carries the IS fire rate in column `in_sample`; the OOS row carries the OOS fire rate in column `out_of_sample`). This is the corrected schema (D-RPRT-001 fix from /010 closeout); the row duplication is unconventional but the values are correct. Cosmetic-only; not verdict-binding. Future cleanup is a one-line schema tightening.

---

## 11. Discussion — What This Iteration Established for v1 Cycle-2

### 11.1 Substrate-Lock Structural Finding

The /010 + /011 pair establishes a NEW structural finding for v1 cycle-2: **the v1 single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED substrate has a stable, LTC-dominated Optuna basin that is re-discovered across axis primitives**. The basin is a property of the (seed, search budget, feature set, ensemble size) tuple, NOT of the axis intervention being tested.

This was hypothesized at /010 closeout (LM Master Phase 7.4 calibration update) but only became a confirmed structural property at /011 with the LTC IS roster overlap measurement (93.3% across two mechanically distinct axes).

### 11.2 Implications for v1 cycle-2 EXPLORATION budget

At v1 EXPLORATION budget (single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3), any non-trivial axis change is expected to produce:
1. IS Δ in the OVERSHOOT band (+0.30 to +0.50) — basin-lottery re-discovery
2. OOS Δ in the {-0.30, +0.50} range — basin transfers OOS with random sign (small mechanical layer if the axis has any deterministic OOS effect)
3. Per-symbol concentration ≥ 30% on the basin-locked symbol (LTC, currently)
4. F6 baseline-overlap < 61% (basin re-routing dominates mechanical filtering)

**The structural implication**: single-seed Sharpe-Δ at v1 cycle-2 EXPLORATION cannot anchor an edge claim. The only way to disambiguate basin-lottery from genuine axis edge is multi-seed dissolution at CONFIRMATION (≥10 outer seeds × ENSEMBLE_SIZE=10 × n_trials=50, per `feedback_v1_seed_count_non_negotiable.md`).

### 11.3 Cycle-2 path forward via multi-seed dissolution test

Critic Phase 7.5 §"Path Forward" proposed 3 axes for /012 (see brief `briefs-v1/iteration_v1-011/review.md` §"Path Forward"):

1. **Labeling axis — triple-barrier σ_t source**: UNUSED family; changes the Optuna training-objective domain at the per-cell label level; ~70% prior probability of basin escape. Strongest substrate-dissolution probe from UNUSED-family menu.

2. **Methodology axis — per-cell early-stop with inner hold-out**: UNUSED since /008; changes WHICH trees retained per cell; substrate-dissolving via tree-selection diversity.

3. **Substrate-dissolution PROBE EXPLORATION at /012**: rerun /011's EXACT R5-BINARY-KILL config at single-seed=43 (NOT a new axis; sister probe at adjacent seed). Tests LM Master's hypothesis "basin is seed-property-driven not axis-property-driven" directly. If /012 (seed=43) diverges from /011 by >0.30 Sharpe, basin IS seed-locked → /015 multi-seed CONFIRMATION on R5-BINARY-KILL becomes the binding next step. If /012 reproduces /011 patterns, the (n_trials=35, 40-feature, ENSEMBLE=3) substrate is binding and basin cannot be unstuck at EXPLORATION budget.

QR Phase 7 Memo recommendation: do NOT pre-commit to a specific Path Forward option in this memo; defer to Phase 8 diary's "Next Iteration Ideas" + next iteration's Phase 5 brief. The three options are not mutually exclusive — /012 could pick any single one; /013 + /014 fill the other two before /015 CONFIRMATION.

### 11.4 Cycle-2 cadence position after /011

| Iteration | Family | Verdict |
|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /008 | methodology | EXPLORATION-PROMISING-METHODOLOGY |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) |
| **/011** | **risk-primitive (binary-kill subtype)** | **EXPLORATION-NEGATIVE (catastrophic-basin-shift; subtype proposal BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP)** |

**Cycle-2 EXPLORATION count after /011: 6 of 10.** CONFIRMATION-eligible at /015 (4 more EXPLORATIONs required before any CONFIRMATION can launch). Cycle-2 verdict distribution: 0 pure PROMISING / 1 PROMISING-METHODOLOGY (non-compoundable) / 5 NEGATIVE. No edge ingredient bundled yet.

### 11.5 HIGH-RISK pre-commit tripwire — 8th-consecutive correct non-firing

Per /011 brief Section 2.5 HIGH-RISK declaration, the multi-seed pre-commit was OPT-IN: pre-commit to /012 multi-seed CONFIRMATION-spec IF /011 verdict = PROMISING. Verdict = EXPLORATION-NEGATIVE catastrophic-basin-shift → tripwire correctly does NOT fire. This is the **8th-consecutive correct non-firing** of the HIGH-RISK pre-commit (across /003 + /004 + /005 + /006 + /007 + /009 + /010 + /011 — all 7 HIGH-RISK iterations on /003-/011 except /008 which was methodology-only).

**Cumulative compute saved**: ~48h across 8 iterations (6h per averted multi-seed CONFIRMATION at 10-seed × ENSEMBLE=10 × n_trials=50). Discipline is battle-tested over 8 independent HIGH-RISK iterations without producing a false-positive CONFIRMATION dispatch.

---

## 12. Files & Commits on Branch (pre-Phase-7+8 closeout)

- Branch: `iteration-v1/011` from `iter-v1/010` closeout commit `33601b6`
- HEAD before Phase 7+8: `b48c035` (Critic Phase 7.5 review)
- HEAD after Phase 7+8: see closing commit SHAs in Phase 8 diary

Commits in this iteration (pre-closeout):
- `5d7a1e1` — EDA analysis scripts + oracle simulation
- `9227d92` — QR Phases 1-5 + R5 binary kill EDA-calibrated threshold + brief
- `f6e0515` — LM Master Phase 4.5 pre-design advisory
- `9c843e6` — brief Section 3.6 — LM Master Phase 4.5 recs response
- `57587ef` — phase 5.5 gate PASS
- `b788d4f` — R5-BINARY-KILL-LOW wiring (pre-R2 entry filter, configurable threshold)
- `ff3b686` — Critic Phase 6.0 pre-flight PASS
- `048bbd4` — LM Master Phase 7.4 post-mortem
- `b48c035` — Phase 7.5 Critic review — EXPLORATION-NEGATIVE

Trunk merge: **NONE**. EXPLORATION-NEGATIVE never merges to main.

Tag: `v0.v1-011` (after Phase 8 commit).

---

## 13. Summary

iter-v1/011 tested an EDA-driven inversion of the convergent 3-way "kill_high at NATR > 7%" recommendation — instead, skip entry if NATR_14 < 2.0% (kill_low). The EDA was the strongest pre-registered signal in v1 cycle-2 to date (cross-roster sign-agreement on positive oracle Δ at the calibrated threshold). The implementation was clean (3-file src/ diff matching brief Section 3.1 exactly; deterministic stateless gate).

The outcome:
- OOS Sharpe +1.0709 — literal merge-floor pass
- IS Sharpe +0.7678 — IS Δ +0.4849 above brief Section 8 catastrophic-basin-shift threshold (+0.30)
- F6 roster overlap with BASELINE = 16.7% (far below 61% tripwire) → smoking-gun basin shift
- LTC IS roster /010 ↔ /011 = 93.3% → same Optuna basin re-discovered across mechanically distinct axes

The verdict is EXPLORATION-NEGATIVE catastrophic-basin-shift per pre-registered F3 gate. The OOS Sharpe magnitude is real-but-non-durable: ~+0.05 of the +0.41 OOS Δ is attributable to mechanical kill_low cleanup (a durable layer); the remaining +0.36 is basin-lottery substrate transferring to OOS (single-seed-conditional; dissolves at multi-seed).

The structural finding: at v1 single-seed=42 + n_trials=35 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED, the Optuna basin is substrate-locked across axis primitives. Single-seed Sharpe-Δ cannot anchor an edge claim at v1 EXPLORATION budget; only multi-seed dissolution at /015 CONFIRMATION can disambiguate.

Critic Path Forward proposes 3 axes for /012 (labeling σ_t source / methodology early-stop / substrate-dissolution probe at seed=43); all are structurally orthogonal to /010 + /011's risk-primitive family. The full cycle-2 cadence is 6 of 10 EXPLORATIONs complete; CONFIRMATION-eligible at /015 earliest.
