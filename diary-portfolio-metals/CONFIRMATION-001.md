# CONFIRMATION-001 — OOS reveal + full gauntlet → BASELINE_METALS bootstrap

**Date:** 2026-06-25. User authorized the OOS reveal ("the end"). **Verdict:** CONFIRMATION-**BOOTSTRAP**
(Critic) — establish **BASELINE_METALS = L2 (anchor + dispersion)**. NO re-tuning (only the
Critic-pre-registered COT lag 6→7, strictly more conservative).

## Layered OOS reveal (IS = →2025-03-24; OOS = 2025-03-24→2026-06)
| Layer | IS_SR | OOS_SR | IS_DD | OOS_DD | turn/c | beats gold | beats basket |
|---|---|---|---|---|---|---|---|
| L1 anchor | 0.40 | 1.70 | −24% | −16% | 0.009 | ✓ | ✓ |
| **L2 +dispersion (BASELINE)** | **0.51** | **1.71** | −26% | −18% | 0.007 | ✓ | **✓** |
| L3 +COT (robust, no ptpd) | 0.56 | 1.57 | −25% | −19% | 0.017 | ✓ | ✗ (1.57<1.58) |
| L4 +ptpd (full 4-sleeve) | 0.59 | 1.63 | −25% | −19% | 0.026 | ✓ | ✓ |
Benchmarks (VT 15%): buy-hold gold OOS 1.45; equal-weight basket OOS 1.58. Cost-stress 2×: L2 1.70,
L3 1.54, L4 1.57. DSR (N_eff=72, E[max|null]≈1.23): all clear. Leak re-audit PASS. Tests 18/18.

## The honest read (the OOS did not disappoint, but it is regime-flattered)
OOS Sharpe (1.57–1.71) is ~3× IS (0.40–0.59) because **2025–26 was a strong metals bull** (L2 2025
OOS net +61%). The naive long benchmarks reached ~1.5 in the same window → the book's edge OVER
buy-and-hold is THIN and is ~entirely the directional anchor riding the melt-up. The market-neutral
overlays add ≤+0.06 OOS each; **only dispersion confirms OOS** (+0.010 marginal).

## Critic adjudication (full review)
- **Baseline = L2.** The only layer where every added sleeve's OOS marginal lift is non-negative;
  highest OOS Sharpe of the clean layers; beats both benchmarks; lowest turnover; 2×-cost-robust.
- **L3/L4 rejected as baseline:** L3 carries the full-COT sleeve whose OOS marginal lift is NEGATIVE
  (−0.137); L4's benchmark-beat leans on pt/pd (`PROMOTABLE=False`, thin-n).
- **COT disposition:** confirmed GOLD/SILVER-ONLY (+0.044 OOS); full-4-metal OOS-falsified (−0.137)
  — the falsifier did exactly its job (palladium/thin pt/pd-COT reliance). NOT promoted as wired.
- **Verdict: BOOTSTRAP** not full-PASS — single benign-bull OOS regime + thin B&H-beat. First metals
  baseline deserves recording with the caveats as outstanding constraints.
- Methodology PASS: leak/parity clean (`net_from_raw` shift(1), COT +7d causal, benchmark vol-target
  past-only = fair comparison), no re-tuning, DSR honest/informational. One reporting defect flagged
  (summary named L3 as baseline) → FIXED to L2 + added an L2 cost-stress row.

## Next confirmation's burden (Critic Path Forward — regime/deployment, NOT signal-hunting)
1. **Metals-BEAR OOS test** — the binding open question (anchor long-bias vulnerability).
2. **`L2 + GS-only-COT` as an explicit headline OOS layer** (currently an inferred cell).
3. **Live-parity reconcile harness** before capital.

See `BASELINE_METALS.md` for the recorded baseline + caveats. The in-scope signal frontier is CLOSED
(iter-005/006). `analysis/portfolio/metals/confirm_metals.py` reproduces this gauntlet.
