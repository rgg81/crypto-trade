# Phase 7.5 Critic Review — iter-v1/089 — BUNDLE-003 ASSEMBLY

OVERALL: NO-MERGE — strictly-better-on-≥1-regime is unmet (the σ_R reading is correct AND the only positive-Δ regime, BTC_DOWN, is the same Nov-2025 XRP window the regime-conditionality falsifier fires on). Methodology integrity intact (Checks 1/2/15/16/17 PASS); BUNDLE-002 (`v0.v1-082`) stays. XRP held as PROMISING specialist.

## The Decisive Question — σ_R Interpretation
**"Strictly better on ≥1 regime" = Δ > σ_R (NOT Δ > 0). NO-MERGE follows.** The "(within σ_R)" tolerance makes the "better-or-equal" leg accept `Δ ≥ −σ_R`; a coherent rule cannot use σ_R to reject noise on one leg and accept noise (`Δ > 0`) on the other (a +0.0003 BTC_FLAT Δ would otherwise "qualify"). Applying Δ > σ_R:

| Regime | B2 | B3 | Δ | σ_R | Verdict |
|---|---:|---:|---:|---:|---|
| BTC_UP | 0.300 | 0.333 | +0.033 | ~0.98 | within (noise) |
| BTC_FLAT | 1.104 | 1.107 | +0.003 | ~1.04 | within (noise) |
| BTC_DOWN | 0.194 | 0.640 | +0.446 | ~1.01 | within (noise) |

No regime strictly better; σ_R (~1.0, driven by 12-15 month sub-samples) swamps every Δ. `pareto_dominates_bundle_002 = false` (QR summary). The BTC_DOWN +0.446 — the largest Δ — is dominated by Nov-2025 XRP trades (the falsifier's window). **NO-MERGE under the correct reading.**

## Per-Check Status
- **Check 1 Look-Ahead: PASS.** Composition (no new training). New BTC-trend regime tagger uses `bisect_left(close_time, open_time)−1` (last BTC candle closed strictly before entry; lagged 30×8h) — clean. IS/OOS re-split on strict close-day rule, symmetric across all 5 components (explains composed XRP 85 OOS vs standalone 84). Foundation embargo inherited.
- **Check 2 Embargo: PASS** (inherited; no new boundary).
- **Check 3 Multiple-Testing: FAIL (informational).** Bundle OOS DSR 0.896 / IS 0.908 (<0.95); XRP N_eff=1 single-outer-seed. Operative gate is the relative-regime-Pareto rule, not edge axes. Flagged; compounds the single-seed concern.
- **Checks 4/5 INFORMATIONAL.** XRP's stat_autocorr_lag5 (rank 3) is the only structural differentiator; otherwise re-learns shared trend basis (signal-orthogonality thinner than the trade-corr number suggests).
- **Check 6 Pareto Dominance: FAIL** (decisive). B3 Pareto-≥ on all 3 regimes (non-regressive) but strictly-better (Δ>σ_R) on ZERO. The one materially-positive regime (BTC_DOWN +0.446) = Nov-2025 XRP trades = the falsifier window. Does not dominate.
- **Check 7 Reproducibility: PASS.** Deterministic from git-tracked trade artifacts; pairwise-disjoint assertion load-bearing; sources unambiguous.
- **Check 8 Alignment: PASS.** Implements the /088 diary's pre-registered /089 step (OOS-Sharpe, trade-corr gate, cross-track audit, regime falsifier). No scope creep, no OOS leak into weights, no post-hoc filtering.

## Bundle Integrity (HARD)
- **Check 15 Parity: PASS.** Pure union of 5 streams, no post-hoc netting; equal-weight (w=1.0 all five, mirrors /082).
- **Check 16 Pairwise-Disjoint: PASS** (DOT/ETH/BTC/AAVE/XRP own distinct coins). Caveat: XRPUSDT also v2-live (notional 20%) → deploy-parity audit item (not a v1-assembly blocker). Forensic flag: trade-corr seat gate PASSES on average (0.299<0.5) but XRP↔AAVE IS co-trade = 0.6716 (>0.5) — XRP diversifies vs DOT/ETH/BTC but partially duplicates AAVE; zerofill drops all pairs to ≤0.22 (supports diversifier; not escalated to FAIL).
- **Check 17 Weights IS-Only: PASS.** weight_calibration.py reads only in_sample/trades.csv; no out_of_sample path; equal-weight PRIMARY (RP is robustness companion).

## Concentration fix vs MaxDD
37.47%→29.46% (consistent pipeline; ≠ BASELINE_V1's 33.96% which used /082's pipeline — provenance must be stated). Crossing 30% is real but is denominator expansion (N=4→5 mechanical, expected). OOS MaxDD widens 59→92% (streams' drawdowns stack, not offset). **The concentration improvement and MaxDD deterioration roughly cancel on the risk ledger** — neither decides; the regime-Pareto rule does.

## Regime-Conditionality Falsifier — the substantive heart
FIRES (`regime_contingent: true`): XRP incremental OOS Sharpe +0.057 full / **−0.421 ex-post-Nov-2025**; XRP OOS pre-Nov 44 trades −48.28%, post-Nov 41 trades +81.50%. "Regime-conditional edge that turned ON 7 months before data ends, at a single outer seed, N_eff=1" is exactly the profile that does NOT support a baseline-changing merge. Genuine diversification (low trade-corr vs DOT/ETH/BTC) is necessary but NOT sufficient — the diversifier must also deliver above-noise incremental edge across >1 regime-window, and it does not.

## Recommendations to QR
1. Author /089 brief artifacts retroactively OR log the process exception (pre-registration lives in the /088 diary — hence Recommendation not BLOCK).
2. Fix concentration-figure provenance in the diary (37.47%→29.46% consistent-pipeline; ≠ BASELINE_V1 33.96%).
3. XRP↔AAVE 0.67 is a future-bundle hazard: report per-member correlations (not only the average) at any BUNDLE-004; flag any single pair > 0.5.

## Path Forward
XRP/088 held as PROMISING (single-outer-seed-TENTATIVE); BUNDLE-002 (`v0.v1-082`) stays. **Do NOT discard XRP** — first non-negative fresh mine + genuine diversifier vs DOT/ETH/BTC. **Re-assess for BUNDLE-003 when more OOS accrues** (if post-Nov strength persists another 6+ months at the next assembly, the "strictly better on ≥1 regime" leg may clear). Alt axes from families NOT in the prior 5 (all universe mines): (1) autocorr-persistence feature head (engineer XRP's stat_autocorr_lag5 differentiator; reduce the AAVE overlap); (2) regime-conditional kill primitive (suppress XRP's OFF regime → harvest the post-Nov edge without the pre-Nov −48% drag); (3) longer-horizon labeling matched to the lag-5 persistence timescale. NO multi-seed CONFIRMATION (permanently dropped).

OVERALL=NO-MERGE
