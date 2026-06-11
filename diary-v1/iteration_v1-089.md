# iter-v1/089 — Phase 8 Diary (BUNDLE-003 ASSEMBLY)

**Date**: 2026-06-11
**Track**: v1 (refactored)
**Branch**: `iteration-v1/089`
**TYPE**: BUNDLE assembly (CONFIRMATION-PORTFOLIO) — {DOT/063, ETH/064, BTC/065, AAVE/078, XRP/088}. Composition of 5 existing specialist trade streams (no new training).
**Cycle**: 7, bundle assembly
**Author**: QR (autopilot)
**Tag**: `v0.v1-089`

---

## Headline

**NO-MERGE — BUNDLE-003 {DOT,ETH,BTC,AAVE,XRP} does NOT Pareto-dominate BUNDLE-002 under the relative-regime-Pareto merge rule. It raises headline OOS Sharpe (+1.001 → +1.058) and fixes BUNDLE-002's concentration breach (BTC 37.5% → 29.46%), but no regime improves beyond σ_R and XRP's OOS edge is entirely post-Nov-2025 (the regime-conditionality falsifier fires). BUNDLE-002 (`v0.v1-082`) stays the live baseline. XRP held as a PROMISING diversifier for re-assessment as more OOS accrues.**

XRP earned its seat candidacy (SPECIALIST-PROMISING + trade-corr gate 0.30 < 0.5 = genuine diversifier), and the assembly is non-regressive (Pareto-≥ on every regime). But the merge rule requires STRICT improvement on ≥1 regime beyond its sampling noise (σ_R), and none of the three OOS regimes clears it — the σ_R band (~1.0, driven by 12-15 month sub-samples) swamps every per-regime delta. The one materially-positive regime (BTC_DOWN +0.446) is the same Nov-2025 XRP window the regime-conditionality falsifier flags. The methodology held: a genuine diversifier with a regime-contingent, noise-band-thin edge is not sufficient to change the live baseline.

---

## BUNDLE-003 vs BUNDLE-002 (equal-weight, IS-only weights, consistent pipeline)

| Metric | BUNDLE-002 (4) | BUNDLE-003 (5) | Δ |
|---|---:|---:|---:|
| IS Sharpe | 0.717 | 0.691 | −0.026 |
| OOS Sharpe | 1.001 | **1.058** | +0.057 |
| OOS DSR (N_eff=1) | 0.863 | 0.896 | +0.033 |
| OOS top-symbol conc. | BTC **37.47%** (breach) | BTC **29.46%** | ✅ fixes breach |
| OOS MaxDD | 59.4% | **92.0%** | +32.6 (worse) |
| IS / OOS trades | 690 / 324 | 908 / 409 | +218 / +85 |
| Per-specialist OOS floor | — | all ≥50 (DOT 63/ETH 82/BTC 88/AAVE 91/XRP 85) | OK |

Per-regime OOS (BTC-trend tag): BTC_UP +0.033, BTC_FLAT +0.003, BTC_DOWN +0.446 — all Pareto-≥, ALL within σ_R (~1.0). No strict improvement.

---

## Decision: NO-MERGE (BUNDLE-002 stays)

**Verdict** (Phase 7.5 Critic review, commit pending): `NO-MERGE`.

- **BUNDLE-002 (`v0.v1-082`; DOT+ETH+BTC+AAVE; IS +0.72 / OOS +1.00) remains the live v1 baseline.** BASELINE_V1.md unchanged.
- **XRP/088 held as a PROMISING (single-outer-seed-TENTATIVE) diversifier** — NOT discarded. First non-negative fresh mine; genuine diversifier vs DOT/ETH/BTC (trade-corr 0.30); fixes concentration. Re-assess for BUNDLE-003 when more OOS accrues past the Nov-2025 inflection.

**Why NO-MERGE** (σ_R adjudication, Critic): "strictly better on ≥1 regime" = Δ > σ_R (a coherent rule can't use σ_R to reject noise on the better-or-equal leg while accepting Δ>0 noise on the strictly-better leg). Under Δ > σ_R, no regime clears. The one materially-positive regime (BTC_DOWN +0.446) = Nov-2025 XRP trades = the falsifier window. Regime-conditionality falsifier FIRES: XRP incremental OOS +0.057 full / **−0.421 ex-post-Nov** (XRP OOS pre-Nov −48%, post-Nov +81%). Integrity all clean (Checks 15/16/17 PASS).

---

## Bundle integrity (HARD) — all PASS
- **Check 15 parity**: pure union of 5 streams, no post-hoc netting, equal-weight (mirrors /082).
- **Check 16 pairwise-disjoint**: DOT/ETH/BTC/AAVE/XRP own distinct coins. Forensic flag: trade-corr seat gate passes on AVERAGE (0.30) but XRP↔AAVE IS co-trade = 0.67 (>0.5) — XRP diversifies vs DOT/ETH/BTC, partially duplicates AAVE (zerofill drops all to ≤0.22). Cross-track v2-overlap (XRP notional 20%) = deploy-parity audit item, not an assembly blocker.
- **Check 17 weights IS-only**: weight_calibration.py reads only in_sample/trades.csv.

## Process notes (Critic recs)
- Concentration provenance: 37.47%→29.46% is the consistent compose-pipeline basis; ≠ BASELINE_V1's 33.96% (different denominator). State the basis when comparing.
- The concentration fix is denominator expansion (N=4→5 mechanical); the worse OOS MaxDD (59→92%, streams' drawdowns stack) roughly cancels it on the risk ledger.
- /089 had no formal brief (pre-registration lived in the /088 diary) — logged as a process exception, not a blocker.

---

## Campaign outcome (BNB/XRP universe expansion + fail-fast)

The 2026-06-10/11 universe-expansion + fail-fast campaign closes:
- **fail-fast mechanism** implemented + validated in production (BNB BLOCK vs XRP PASS).
- **BNB/087** BLOCKED-FAIL-FAST (first-2yr IS −9.69).
- **XRP/088** SPECIALIST-PROMISING (first non-negative fresh mine; IS +0.38/OOS +0.50), cleared the trade-corr seat gate.
- **BUNDLE-003 /089** NO-MERGE (regime-contingent edge, no strict per-regime improvement).
- **BUNDLE-002 (`v0.v1-082`) remains the live baseline** — unchanged through the entire campaign.

Net: a genuine PROMISING diversifier (XRP) discovered and held, the fail-fast infra built + validated, but no baseline change. The methodology held under a borderline merge candidate.

---

## Next Iteration Ideas

1. **Hold XRP; re-assess BUNDLE-003 when more OOS accrues** — if XRP's post-Nov-2025 strength persists another 6+ months at the next assembly, the "strictly better on ≥1 regime" leg may clear (the σ_R band shrinks as the OOS sub-samples grow).
2. **Sharpen XRP** (axes from families NOT used in the prior 5 universe mines): (a) autocorr-persistence feature head (engineer XRP's stat_autocorr_lag5 differentiator; reduce the AAVE overlap); (b) regime-conditional kill primitive (suppress XRP's OFF regime → harvest the post-Nov edge without the pre-Nov −48% drag); (c) longer-horizon labeling matched to the lag-5 persistence timescale.
3. **Machinery axes** (W-DECAY etc.) per "alternate" — lift the existing BUNDLE-002 seats.

NO multi-seed CONFIRMATION (permanently dropped).

---

## Catalog

iter-v1/089 → BUNDLE-003 assembly {DOT,ETH,BTC,AAVE,XRP} (equal-weight, IS-only weights) | **NO-MERGE** (Critic, relative-regime-Pareto rule) | OOS Sharpe 1.001→1.058 (+0.057, within σ_R) + DSR 0.863→0.896 + concentration 37.47%→29.46% (fixes breach) BUT OOS MaxDD 59→92% + no strict per-regime improvement + regime-conditionality falsifier FIRES (XRP OOS −0.42 ex-post-Nov) | BUNDLE-002 (`v0.v1-082`) UNCHANGED | XRP held PROMISING diversifier (re-assess as OOS accrues). Tag `v0.v1-089`.
