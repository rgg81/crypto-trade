# iter-v1/088 — Phase 8 Diary (XRPUSDT SPECIALIST)

**Date**: 2026-06-11
**Track**: v1 (refactored)
**Branch**: `iteration-v1/088`
**TYPE**: SPECIALIST — XRPUSDT single-coin cohort (un-reserved; cross-track v2 overlap accepted); STOCK 48-col stack, NO new features; fail-fast=2.0 gate (PASSED).
**Cycle**: 7, universe expansion
**Author**: QR (autopilot)
**Tag**: `v0.v1-088`

---

## Headline

**SPECIALIST-PROMISING — the FIRST non-negative fresh mine of the entire campaign (0/7 before). IS Sharpe +0.3783 / OOS +0.4966. XRP passed the fail-fast (first-2yr IS +16.88, where BNB was BLOCKED), and the OOS is a genuine regime-conditional edge (not noise). A legitimate BUNDLE-003 candidate — decided by a bundle-assembly backtest, not a standalone re-run.**

After ATOM/075, ICP/077, FIL/083, CRV/084, UNI/085, TRB/086, BNB/087 all NEGATIVE or BLOCKED (0/7), XRP is the first fresh symbol to clear the fail-fast and deliver a positive standalone. IS +0.38 is the TOP of the bundle's standalone-IS cohort (ETH +0.24, AAVE +0.34, BTC +0.07). The verdict is PROMISING-TENTATIVE (single outer seed), not a merge — neither window clears +1.0, and the bundle-fit (trade-level correlation vs the cohort) is the load-bearing unchecked quantity.

---

## Results

| Metric | IS | OOS |
|---|---:|---:|
| Sharpe | **+0.3783** | **+0.4966** |
| Trades | 219 | 84 |
| WR | 42.5% | 42.9% |
| PF | 1.13 | 1.14 |
| MaxDD | 26.3% | 18.9% |
| DSR (N_eff-corr) | 0.8027 | 0.7469 |
| PSR(vs1) | 0.176 | 0.301 |
| OOS/IS ratio | — | 1.31 |

Fail-fast: first-2.0yr IS weighted_pnl **+16.88 → PASSED** (BNB/087 was −9.69 → BLOCKED). Inner-seed dispersion 41.1 (50 seeds genuinely differ; aggregation sound).

---

## Key findings

1. **First non-negative fresh mine.** Campaign 0/7 → XRP positive in both windows. The fail-fast worked as a discriminator: it BLOCKED BNB (negative first 2yr) and PASSED XRP (positive first 2yr), and XRP's full run confirmed the positive read.

2. **The OOS is a REGIME-CONDITIONAL edge, not noise** (LM 7.4 + Critic 7.5 concur, correcting the engineering "single lucky month" framing): pre-Nov-2025 (8mo) −17.24% / 1-of-8-pos (edge OFF); 2025-11 +11.75% (inflection); post-Nov (7mo) **+15.15% / 6-of-7-pos, largest +4.05% (broad-based, NOT outlier-driven)** — the strongest, most stable OOS stretch. XRP's trend/autocorr edge "turned ON" in late 2025. Honest residual danger: the regime can turn OFF as abruptly; and a degenerate-Optuna tell (8/54 months best_trial=1, 7 in OOS era) means part of "edge on" is served by a budget-thin generic config.

3. **IS +0.38 is in-fold-validated, not a basin artifact** — 54/54 per-month Optuna objectives positive (NOT the /086 TRB in-fold/realized inversion); inner-seed dispersion healthy (41.1). Single-outer-seed-TENTATIVE (basin-lottery DOWNGRADE triggers unmeasurable at one outer seed), NOT active basin-lottery.

4. **Coherent trend/autocorr edge, but partly shared-basis.** Feature importance: vol_atr_14, trend_adx_14, stat_autocorr_lag5, trend_aroon_osc_50, mom_macd_line, interact_natr_x_adx. `stat_autocorr_lag5` (rank 3) is the ONLY structural differentiator from the bundle's existing trend members — XRP largely re-learns the shared trend basis (lighter than TRB's DIVERSIFIER-DEGENERATE, but not strongly orthogonal). **Trade-level correlation vs the cohort is the load-bearing unchecked quantity** (the IC matrix is feature-level only).

---

## Decision: SPECIALIST-PROMISING (TENTATIVE) — NO MERGE (forward-pointer)

**Verdict** (Phase 7.5 Critic review, commit `0146d9e0`): `SPECIALIST-PROMISING`, single-outer-seed-TENTATIVE.

- XRP is a **BUNDLE-003 CANDIDATE** — the first the campaign has produced.
- Neither window clears +1.0; bundle-merge floors apply at BUNDLE-003 assembly, not here.
- **BUNDLE-002 (`v0.v1-082`; DOT+ETH+BTC+AAVE) UNCHANGED** until a BUNDLE-003 assembly clears its gates.
- The fail-fast mechanism is validated as a discriminator (BNB BLOCK vs XRP PASS).

---

## Next Iteration Ideas — the decisive next step is a BUNDLE-003 assembly backtest with XRP

Per LM 7.4 + Critic 7.5 (and "the backtest is the proof"): the bundle backtest, not a standalone re-run, decides whether XRP earns a seat.

1. **/089 = BUNDLE-003 assembly backtest including XRP** (DOT+ETH+BTC+AAVE+XRP). Pre-register: (a) does XRP raise bundle OOS Sharpe; (b) **per-symbol TRADE-level correlation** (XRP vs ETH/AAVE/BTC trade returns, overlapping windows) with a pre-committed **<0.5 "earned seat" threshold** (>0.5 → DIVERSIFIER-DEGENERATE, no seat); (c) **cross-track parity/netting audit** (combined v1+v2 XRP notional; v1 bundle XRP decisions independent of v2 live); (d) **regime-conditionality falsifier** (if XRP's incremental bundle OOS is itself concentrated in the post-Nov window, temporal-complementarity is unsupported).
2. If the bundle trial REJECTS XRP — fresh-mine axes from families NOT used in the prior 5 (all universe): autocorr-persistence feature-family head (engineer XRP's only orthogonal differentiator); regime-conditional kill primitive (suppress the OFF regime); longer-horizon labeling head (match the lag-5 persistence timescale).
3. Machinery axes (W-DECAY etc.) remain available per "alternate."

NO multi-seed CONFIRMATION (permanently dropped).

---

## Catalog

iter-v1/088 → `per-cohort-specialization-XRP` (universe; STOCK 48-col; fail-fast=2.0 PASSED) | **SPECIALIST-PROMISING (TENTATIVE)** | IS +0.3783 / OOS +0.4966 (OOS regime-conditional: post-Nov-2025 +15.15%/6-of-7-pos) | FIRST non-negative fresh mine (campaign 0/7 → 1) | BUNDLE-003 candidate (trade-corr <0.5 check pending) | cross-track v2 overlap flagged | DSR 0.75-0.80 informational | BUNDLE-002 (`v0.v1-082`) UNCHANGED. Tag `v0.v1-088`.
