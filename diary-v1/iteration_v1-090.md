# iter-v1/090 — Phase 8 Diary (W-DECAY time-decay sample weighting)

**Date**: 2026-06-11
**Track**: v1 (refactored)
**Branch**: `iteration-v1/090`
**TYPE**: SPECIALIST — machinery EXPLORATION (FIRST sample-weighting axis of cycle-7). W-DECAY = new `sample_weight_mode="abs_pnl_timedecay"` (abs_pnl × exp(−ln2/12·age), half-life 12mo). Tested on the ETH/064 seat (single cell). fail-fast=2.0 ON.
**Cycle**: 7, machinery axis (the "alternate" after BNB/XRP)
**Author**: QR (autopilot)
**Tag**: `v0.v1-090`

---

## Headline

**SPECIALIST-NEGATIVE (INVERSE-EDGE) — BLOCKED-FAIL-FAST. W-DECAY drove ETH's first-2yr IS from the +0.2383 baseline to −2.02 Sharpe (weighted_pnl −17.17, net −27.9%, 143 trades). The LM Phase 4.5 §5.1 inverse-edge risk (pre-registered ~25-30%) MATERIALIZED: ETH's IS edge is in OLDER data (2022-23); recency-weighting discarded it.**

The decisive nuance: **the mechanism ENGAGED (F2 ✓) but the result is deeply NEGATIVE (F1 ✗).** W-DECAY did exactly what it was designed to — Optuna's `training_days` median rose to 280d (folds<120d 14%, vs TRB's 50% collapse) — proving the recency-gradient suppressed the window-truncation incentive. But emphasizing recent ETH data is the WRONG move: ETH's edge lives in 2022-23, so the recency-weighted model lost money. This is NOT NEGATIVE-INERT (the mechanism worked); it is NEGATIVE via inverse-edge.

---

## Result (fail_fast_report.csv)

| Metric | Value |
|---|---:|
| verdict | **BLOCKED-FAIL-FAST** |
| first-2.0yr IS weighted_pnl | **−17.1722** (≤0 → block) |
| first-2.0yr IS net PnL | −27.91% |
| first-2.0yr IS Sharpe (approx) | **−2.0193** |
| IS trades (2.0yr window) | 143 |
| baseline ETH/064 IS | +0.2383 (Δ ≈ −2.26) |
| wall-clock to abort | 13,468s (~3.7h vs ~7-8h full; ~3.5-4h saved) |

**F2 (mechanism) ENGAGED**: training_days median **280d** (vs XRP/088 prior 250d, LM-predicted ~220-240d), folds<120d 14%. **§1c attribution**: decay.mean 0.544, decay.min 0.254 (matches 12mo/24mo math), weight_sum halved (reg-loosening channel present), kish 0.87 (ESS shrink MILD — the negative is genuine inverse-edge, NOT an ESS/reg artifact).

---

## Decision: SPECIALIST-NEGATIVE (INVERSE-EDGE) — NO MERGE

- W-DECAY-on-ETH-at-12mo is NEGATIVE (deeply). The ETH seat is unchanged (baseline ETH/064 stays as the bundle component).
- **BUNDLE-002 (`v0.v1-082`) UNCHANGED.**
- fail-fast VALIDATED a 3rd time (BNB/087 block, XRP/088 pass, W-DECAY-ETH block) — it correctly caught the inverse-edge at the 2yr mark.

---

## Key finding: recency-weighting is COIN-SPECIFIC, not universally good

This is the genuinely valuable learning (connects directly to the user's principle-2 discussion "recent matters more"):
- **XRP/088's edge is RECENT** (post-Nov-2025 regime; the OFF→ON transition).
- **ETH/064's edge is OLD** (2022-23; recency-weighting destroys it).
- → **There is NO universal "recent matters more" weighting.** W-DECAY as a BUNDLE-WIDE recency lever (apply to all seats) is REFUTED — it would hurt old-edge seats. It could only work as a PER-SEAT opt-in matched to each coin's temporal-edge profile, which is more complex and less clearly worth it.
- The LM 4.5 reframing was correct: decay COMPOSES with training_days (not substitutes) → F2 second-order (the 280d shift is modest, as predicted, not cap-ward); and the §1c log was the right attribution instrument (it confirmed reg-loosening was present but did NOT rescue the inverse-edge negative).

---

## W-DECAY axis disposition

- **CLOSED for ETH at 12mo** (inverse-edge — deeply negative).
- **NOT fully closed for the axis**: a recent-edge coin (XRP-like) or a shorter/longer half-life could differ — but the bundle-wide application is refuted (mixed temporal profiles), and per-seat recency-matching is a complex, lower-priority lane. Recommend NOT pursuing W-DECAY further on the current bundle seats; if revisited, only on a coin with a confirmed RECENT edge, and as a per-seat opt-in.

---

## Next Iteration Ideas

1. The other machinery axes from the earlier menu remain: **R-CONV** (ensemble-conviction trade gate — only trade when ≥X of 50 seeds agree; pure SNR filter, bundle-wide, no temporal-profile dependence) and **GATE-INV** (cross-regime sign-invariance feature-admission gate). R-CONV is the cleaner next machinery axis — it doesn't depend on a coin's temporal-edge profile the way W-DECAY does.
2. Sharpen-XRP axes (autocorr-persistence feature head; regime-conditional kill primitive) — XRP's recent edge is the one confirmed recent-edge profile, and a regime-kill suppressing its OFF stretch is the natural follow-up.
3. Continue alternating machinery with coin-mining per the user directive.

NO multi-seed CONFIRMATION (permanently dropped).

---

## Catalog

iter-v1/090 → `sample-weighting` axis (W-DECAY, abs_pnl_timedecay 12mo; FIRST machinery axis of cycle-7; rotation satisfied) | tested on ETH/064 seat | **SPECIALIST-NEGATIVE (INVERSE-EDGE), BLOCKED-FAIL-FAST** — first-2.0yr IS weighted_pnl −17.17 / Sharpe −2.02 (baseline ETH +0.2383; Δ −2.26) | **F2 ENGAGED** (training_days 280d ↑, folds<120d 14%) but **F1 deeply NEGATIVE** = mechanism worked, recency WRONG for ETH (edge in 2022-23 old data) | §1c: decay.mean 0.544, kish 0.87 (mild — genuine inverse-edge not artifact) | KEY: recency-weighting is COIN-SPECIFIC (XRP recent / ETH old) → bundle-wide W-DECAY REFUTED | fail-fast 3rd validation (~3.5-4h saved) | BUNDLE-002 (`v0.v1-082`) UNCHANGED. Tag `v0.v1-090`.
