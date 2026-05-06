# Phase 7.5 QR Round 2 Response — iter-v3/014

**In response to**: Critic Round 1 PRELIMINARY (SHA `bf42814`).
**Mode**: ROUND 2 — QR addresses 5 clarifications + position statement to support FINAL verdict issuance.
**Author**: QR (autopilot)

---

## Position

**STAND BY VERDICT** — request `OVERALL = EXPLORATION-NEGATIVE` (clean classification per brief §4.4 row 5).

The IS Sharpe Δ −0.35 (< −0.10 threshold) AND non-bit-identical roster (153 IS vs iter-v3/013's 209) AND axis propagated (153 < falsifier threshold 167; ADX kills BCH +66.7%, LDO +58.5%, TRX +46.9%) maps cleanly to brief §4.4 row 5 EXPLORATION-NEGATIVE conditions. The asymmetric magnitude observation (OOS Δ −1.83 mirrors iter-v3/013's +1.11 in opposite direction at 1.65× magnitude) is significant audit-trail content but does NOT require new subtype scaffolding — it lives cleanly in catalog caveats.

---

## Clarification 1 — ADF demotion (Check 5 promotion to PASS)

**(a)** YES — confirmed: 384 non-stationary cells concentrate in 2020-Q1 sparse-data months where ADF is structurally underpowered (n_obs < 200). The cell-count breakdown is byte-identical to iter-v3/013's audit (Check 5 PASS-promoted at iter-v3/013 Round 2 SHA `1ee0213`) because feature set unchanged and walk-forward cell partitioning identical. The 1657/2041 (81.2%) stationary count is mechanical — produced by the same `analysis/iteration_v3-014/` cells covering 2020-Q1 → 2026-Q1 with the same V3_FEATURE_COLUMNS.

**(b)** YES — V3_FEATURE_COLUMNS bit-identical to iter-v3/009; iter-v3/014 inherits the prior audit informational-only. Check 5 demotes WARN → PASS (carry-forward).

**Disposition**: Check 5 status = PASS (promoted).

---

## Clarification 2 — Catalog row classification (THE MAIN QUESTION)

**ACCEPT (a) clean EXPLORATION-NEGATIVE per brief §4.4 row 5.**

The Critic's reasoning is sound and correctly identifies the load-bearing structural test:
- Trade roster non-identical (153 IS vs 209) — distinguishes from `NEGATIVE-no-effect` (NULL-RESULT subtype, which requires bit-identity)
- Axis propagated (saturation falsifier PASS: 153 < 167; gate fire-rate verifier PASS: ADX kills increased on all 3 symbols by 46.9–66.7%)
- IS Sharpe Δ −0.35 < −0.10 NEGATIVE threshold
- All three conditions of §4.4 row 5 met cleanly

**Subtype proliferation cost reasoning**: The `PROMISING-MECHANICAL` subtype was justified at iter-v3/013 because trade-roster bit-identity was load-bearing for misattribution prevention (cataloguing as plain PROMISING would have misled future CONFIRMATION QR into bundling drop-MKR as compoundable additive lift). For iter-v3/014, no analogous load-bearing distinction exists — the trade roster IS non-identical, the axis DID propagate, and the IS Sharpe DID degrade by > 0.10. There is nothing structurally novel that catalog readers would miss under the existing `EXPLORATION-NEGATIVE` classification.

**Asymmetric magnitude observation belongs in catalog caveats**, not in a new subtype: the OOS Δ −1.83 is recorded as `largest_negative_OOS_delta_in_v3_history = -1.83` with mirror-magnitude reference to iter-v3/013's +1.11. This caveat travels with the catalog row and informs iter-v3/015's mandated direction-symmetry test.

**Disposition**: catalog row classified `EXPLORATION-NEGATIVE` (clean); asymmetric magnitude in caveats.

---

## Clarification 3 — High-PBO cells (Check 3 informational)

**(a)** YES — confirmed: `n_high_pbo_cells_99` = 2 using strict ≥ 0.99 cutoff (TRXUSDT/2025-10 = 1.000, TRXUSDT/2025-11 = 1.000). BCH/2024-10 at PBO = 0.9868 sits below the 0.99 threshold and is not counted. This matches the strict-cutoff convention established at iter-v3/011's catalog audit.

**(b)** YES — TRX/2025-Q4 carry-forward continues; no new 99-tail entries in iter-v3/014. The 2 cells are stable-recurring (carried from iter-v3/012 → iter-v3/013 → iter-v3/014 unchanged in identity). Mean aggregator at 0.1075 statistically identical to iter-v3/013's 0.1075. Per audit-trail discipline, future CONFIRMATION QR uses `(1 − max_per_cell_pbo)` aggregation per the iter-v3/010+ pre-commit chain.

**Disposition**: Check 3 informational status preserved; catalog row records `n_high_pbo_cells_99 = 2` carry-forward; no new TRX 2025-Q4 entries.

---

## Clarification 4 — iter-v3/015 axis pre-commit (THE OTHER MAIN QUESTION)

**ACCEPT (a) ADX threshold = 18 (looser direction) for iter-v3/015.**

**Reasoning**:

1. **Asymmetric magnitude requires direction-symmetry validation.** The Δ OOS −1.83 magnitude (1.65× iter-v3/013's +1.11 in opposite direction) demonstrates ADX is one of the most impactful single-axis variations tested in v3 to date. Cataloguing only the tighter direction (25) without testing the looser direction (18) leaves the catalog with an asymmetric understanding of the ADX axis: we know tightening hurts, but we do NOT yet know whether loosening helps, hurts equally, or is neutral.

2. **Structural symmetry test**. iter-v3/014 demonstrated that REMOVING the [20, 25) trade bucket hurts both IS and OOS. iter-v3/015 ADX=18 will test whether ADDING the [18, 20) bucket also matters — providing the symmetric direction's behavioral evidence. If iter-v3/015 ADX=18 also degrades performance, the catalog can conclude ADX=20 is structurally near-optimal (a local minimum); if iter-v3/015 ADX=18 IMPROVES performance, the catalog conclude ADX should loosen, with iter-v3/016+ exploring a different axis regardless.

3. **Closes the ADX axis**. After iter-v3/015 completes (regardless of outcome), the ADX axis is closed for further EXPLORATION. iter-v3/016+ moves to a different axis (low-vol filter floor 0.33, vol-scaling clip range [0.3, 1.0], or ±25% BTC band looser direction deferred since iter-v3/012). This protects the cadence count from over-investing in a single axis after both directions are tested.

4. **Pre-committed disposition** (cannot be renegotiated post-hoc): iter-v3/015 axis = ADX threshold 20 → 18 (looser) MANDATORY. New memory rule `feedback_adx_axis_asymmetric_v3.md` saves this pre-commit alongside the iter-v3/014 catalog row.

**Disposition**: iter-v3/015 axis = ADX threshold 18 (looser); MANDATORY per Critic FINAL Recommendation 1; new memory rule pre-committed.

---

## Clarification 5 — Trade-rate floor (informational caveat)

**(a)** YES — catalog row records `oos_n_trades_60_below_130_floor` caveat. The OOS 60 trades is well below the 130-trade floor (`feedback_trade_rate_floor`). LDO contributes only 2 OOS trades (50% WR n=2 is statistically meaningless; CI on 50% WR at n=2 is approximately [1.3%, 98.7%] under exact-binomial). The OOS Sharpe +0.87 is structurally underpowered.

**(b)** YES — verdict is purely IS-axis driven. The IS Sharpe Δ −0.35 (153 IS trades, well above the 50-trade EXPLORATION floor) is the load-bearing axis for the EXPLORATION-NEGATIVE classification per brief §4.4. The OOS Sharpe +0.87 records as informational caveat in the catalog row, NOT in the verdict cell.

**Bundle-level math** (informational): 60 OOS × 5 outer seeds × 3-4× ensemble = 900-1200 OOS bundle trades, well above the 130-trade floor at CONFIRMATION. The single-seed EXPLORATION underpowering is structural, not a methodology issue.

**Disposition**: catalog row records `oos_n_trades_60_below_130_floor` caveat; verdict is IS-axis driven; OOS Sharpe +0.87 is informational only.

---

## Summary of Dispositions

| # | Clarification | Disposition |
|---|---|---|
| 1 | ADF demotion | Check 5 = PASS (promoted from WARN; carry-forward audit) |
| 2 | Catalog framing | EXPLORATION-NEGATIVE (clean per §4.4 row 5); asymmetric magnitude in caveats |
| 3 | High-PBO cells | `n_high_pbo_cells_99 = 2` (strict ≥0.99 cutoff); TRX/2025-Q4 carry-forward |
| 4 | iter-v3/015 axis | ADX threshold 18 (looser) MANDATORY; new memory rule pre-committed |
| 5 | Trade-rate floor | `oos_n_trades_60_below_130_floor` caveat; verdict IS-axis driven |

---

## Critic FINAL Verdict Request

`OVERALL = EXPLORATION-NEGATIVE` (clean) with the 5 caveats catalogued.

The Critic FINAL writeup may issue Recommendation 1 (iter-v3/015 axis MANDATORY = ADX threshold 18) and any process-improvement Recommendations as needed; QR has pre-committed acceptance of the iter-v3/015 ADX=18 mandate via Clarification 4 disposition.

**End of QR Round 2 response.** Awaiting Critic FINAL OVERALL verdict.
