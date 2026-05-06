# Phase 7.5 Critic Review — iter-v3/014 — PRELIMINARY

**Mode**: ROUND 1 PRELIMINARY (no OVERALL verdict; awaiting QR clarifications).
**Scope discipline**: Per Section 0.5 TYPE=EXPLORATION, methodology axes 1, 2, 4, 5, 6, 8 enforced; edge axis (DSR/PSR Check 3) INFORMATIONAL only.

---

## Per-Check Preliminary Status

### Check 1 — Look-Ahead Audit: PASS
V3_FEATURE_COLUMNS unchanged (13). The single-axis variation (`adx_threshold` 20 → 25) touches gate logic only, not feature pipeline. ADX is computed via 14-period Wilder rolling on past-only OHLC. No look-ahead.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 confirmed at runtime. CPCV n_paths=45. Symmetric purge gap=66 with embargo=27. **Stale `= 88` docstrings REMOVED** per Critic FINAL Rec 3 — `grep -nE '= 88' run_baseline_v3.py` returns 0 matches. Hygiene fix landed.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (per EXPLORATION protocol)
DSR=0.0, PSR=1.0, n_trials=30, n_eff=7, PBO=0.1075 (stable). `n_high_pbo_cells_99` = 2 (TRX/2025-10, TRX/2025-11) — same TRX 2025-Q4 carry-forward as iter-v3/013. BCH/2024-10 at PBO=0.9868 below the 0.99 cutoff, not counted.

### Check 4 — IC Correlation: PASS
Max off-diagonal |IC|=0.6847 (range_realized_vol_50 × max_dd_window_50); below 0.70.

### Check 5 — ADF Stationarity: WARN (carry-forward, demotion contingent on Clarification 1)
1657/2041 (81.2%) cells stationary. 384 non-stationary concentrate in early walk-forward.

### Check 6 — Pareto Dominance: PASS (vacuous, single-seed --exploration)

### Check 7 — Reproducibility: PASS
Code SHA `bdcce5d` stamped. ITERATION_LABEL=v3-014. RiskV2Config(zscore_threshold=2.0, adx_threshold=25.0).

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-FAILED-HYPOTHESIS
Implementation matches single-axis change. Single-axis discipline holds. **Hypothesis NOT SUPPORTED**: IS Sharpe +0.6593 = Δ −0.35 vs iter-v3/013's +1.0088. Per brief §4.4 row 5 (`EXPLORATION-NEGATIVE`): "IS Sharpe down > 0.10 AND non-bit-identical roster" — observed Δ −0.35 < −0.10, roster non-identical (153 vs 209). Saturation falsifier (IS trades 153 < derived 167) PASS — gate fire-rate verifier confirms axis propagated. NOT a NULL-RESULT (distinguishing from iter-v3/012). The gate change took effect; the gate change just hurt the model.

### Checks 9-12: PASS

---

## EXPLORATION-Specific Methodology Notes

**LDO trade collapse 10 → 2 (-80%) is dominant OOS Sharpe collapse driver**. LDO ADX kills increased +58.5% (largest proportional). 2-trade sample (1W/1L) is statistically meaningless (CI on 50% WR at n=2 is essentially [1.3%, 98.7%]). The OOS Sharpe Δ -1.83 attributes primarily to LDO's near-disappearance.

**Largest negative OOS delta in v3 history (Δ -1.83)**. Mirrors iter-v3/013's Δ +1.11 in opposite direction and 1.65× magnitude. Brief §2.1 OOS_caveat correctly pre-registered: "the OOS [20, 25) bucket carried 61.48% of iter-v3/013 OOS PnL". P6 of brief §7 (20% probability) materialized.

**OOS MaxDD doubled (12.47% → 25.15%, +12.68pp)**. Meaningful downside-profile deterioration. WR degraded on 3/3 symbols (BCH 41.9% → 35.0%, LDO 80.0% → 50.0% n=2 noise, TRX 43.2% → 42.1%).

**Saturation predictor parametrization PASSED** (Critic FINAL Rec 3 worked). Predicted counterfactual_n_trades=139; observed IS=153; threshold ceil(1.2×139)=167.

**3rd-consecutive-overshoot pattern broken**. Brief widened band [+0.50, +1.30] median +0.90 per Critic Rec 4. Observed +0.6593 lands BELOW median, breaking the favorable-overshoot trend (010, 011, 013).

---

## Clarifications Requested from QR

### Clarification 1 — ADF non-stationary cells (Check 5 demotion)
(a) Confirm 384 non-stationary cells concentrate in early walk-forward (2020-Q1 sparse-data months with empty `adf_statistic`)? Quick test: `count(rows where adf_statistic == "")`.
(b) Confirm V3_FEATURE_COLUMNS unchanged from iter-v3/009; this Check 5 inherits prior audit, informational-only?

### Clarification 2 — Catalog row classification (THE MAIN QUESTION)

Pre-registered §4.4 outcome table is unambiguous: IS Sharpe Δ −0.35 < −0.10 NEGATIVE threshold + non-bit-identical roster + gate axis propagated → **EXPLORATION-NEGATIVE** per row 5.

Two options:
(a) Catalog as **EXPLORATION-NEGATIVE** (clean): "Tighter ADX over-restricted; [20, 25) trades carried valuable model signal." Per brief §4.4 row 5. iter-v3/015 explores DIFFERENT axis OR tests ADX=18 (looser direction) for disambiguation.
(b) Catalog as **EXPLORATION-NEGATIVE-ASYMMETRIC** (NEW subtype): preserves audit trail that ADX is HIGH-IMPACT axis (Δ OOS magnitude 1.83 mirrors iter-v3/013's +1.11 but exceeds 1.65×) but adverse direction.

**Critic strong prior: (a) clean NEGATIVE classification.** Subtype proliferation has cost; PROMISING-MECHANICAL was justified at iter-v3/013 because trade-roster bit-identity was load-bearing for misattribution prevention. Here, trade roster non-identical and axis propagated — no load-bearing distinction needing new subtype. The "asymmetric magnitude" observation belongs in catalog caveats.

### Clarification 3 — High-PBO cells (Check 3 informational)

(a) Confirm `n_high_pbo_cells_99` for iter-v3/014 = 2 (TRX/2025-10, TRX/2025-11) using strict ≥0.99 cutoff, NOT 3 (BCH/2024-10 at 0.9868 below threshold)?
(b) Catalog row pre-commit: TRX/2025-Q4 carry-forward continues; no new 99-tail entry?

### Clarification 4 — iter-v3/015 axis pre-commit

(a) Confirm iter-v3/015 axis = ADX threshold 18 (looser direction) for disambiguation? Structurally important test: iter-v3/014 demonstrates REMOVING [20,25) hurts both IS and OOS; iter-v3/015 ADX=18 would test whether ADDING the [18,20) bucket also matters (axis-symmetry validation).
(b) OR confirm iter-v3/015 axis = different axis (low-vol floor 0.33, vol-scaling clip, ±25% BTC band)?

**Critic prior: (a) ADX=18 mandated for iter-v3/015.** The asymmetric Δ −1.83 magnitude argues ADX is one of the most impactful axes; catalog needs both directions for honest CONFIRMATION QR bundling decisions.

### Clarification 5 — Trade-rate floor (informational)

(a) Confirm catalog row records caveat that iter-v3/014 OOS Sharpe is from N=60 trades (well below 130 floor; LDO contributes only 2)?
(b) Verdict is purely IS-axis driven; OOS Sharpe +0.87 records as informational caveat, not in verdict cell?

---

**End of PRELIMINARY review.** Awaiting QR `qr_response.md` addressing Clarifications 1–5 before issuing FINAL OVERALL verdict in Round 2.
