# Regime-Ensemble Methodology — Cross-Agent Memo

**Date:** 2026-05-31
**Status:** MANDATORY READ for QR, QE, LightGBM Master, Critic at next dispatch
**Source:** user directive 2026-05-31 (verbatim, anchor):
> "Our framework is a walkforward timeseries implementation. Every month we train and predict. So the IS we talking about here is just the data the QR has to run his analysis to define better configuration, is not the traditional IS when we train the model... The whole idea is to create different models, features, and risk models that each one has its strength, that performs under a specific regime better than the others and in the end, after stacking them together we will have a regime free unified model... Don't want this kind of behaviour rejecting models that perform great in IS and not so great in OOS."

---

## 1. What This Framework Actually Is

v1 is a **walk-forward time-series pipeline**. Every calendar month, for every `(model, symbol)` cell:

1. Train a fresh LightGBM on the last `training_months = 24` months of klines + features.
2. Predict signals for the upcoming month.
3. Trade them through the risk gates.
4. Slide the window forward by one month, repeat.

Both the IS window (pre-2025-03-24) and the OOS window (post-2025-03-24) undergo the **same monthly train-predict mechanic**. The embargo (`walk_forward.py:113`: `train_end_ms = test_start_ms - embargo_ms`) is applied at every fold boundary, IS-internal and OOS-internal. OOS is **not** a held-out test set in the classical sense.

## 2. What IS/OOS Actually Means

- **IS = the researcher's data.** It is what the QR reads, analyzes, EDAs, and designs against. The QR is forbidden from viewing OOS during Phases 1–5. The barrier exists to prevent **researcher overfitting**, not model leakage.
- **OOS = the researcher-honesty window.** The QR sees it for the first time in Phase 7. It is one realization of a future regime mix — not a generalization oracle.
- **The walk-forward + embargo is the model-leakage defense.** It is structural and applies equally to IS and OOS months.

## 3. The End-Goal Is a Regime-Ensemble Bundle

We are not building a single universal predictor. We are building a **bundle of complementary regime specialists** — N component models, each strong in some regime (bull, alt-rotation, chop, bear, vol-spike, liquidation-cascade, ETF-flow, etc.), combined into a regime-balanced portfolio.

The bundle is the product. Components are evaluated as bundle contributors, not as standalone universals.

## 4. Operating Consequences

### 4.1 Stop calling IS-strong / OOS-weak "overfit" by default

IS spans ~5 years and ~6 regimes. OOS spans ~7 months and 1–2 regimes. A model that crushes 2020-bull + 2021-alt + 2023-chop (IS) but only matches 2025-Q2-Q3 recovery (OOS) is a **regime specialist** — a bundle candidate, not a reject.

True overfit signature still exists: importance-INERT mechanism + OOS catastrophic + no regime explanation. Use the F-AXIS load-bearing falsifiers (importance rank, wiring proof, mechanism congruence) to distinguish:

| Signature | Verdict |
|---|---|
| IS lift via basin lottery, importance INERT, OOS catastrophic, mechanism falsified | **OVERFIT-BY-MECHANISM-FAILURE** — discard |
| IS lift mechanically attributable to a signal-bearing feature, importance load-bearing, OOS weakness explained by regime mismatch | **REGIME-SPECIALIST-IS** — preserve for /044+ bundle |

### 4.2 Use the 5-band verdict, not binary PROMISING / NEGATIVE

| Band | IS Δ | OOS Δ | Regime attribution | Bundle role |
|---|---|---|---|---|
| `UNIVERSAL` | ≥ +0.05 | ≥ +0.05 | broad across regimes | Anchor candidate |
| `REGIME-SPECIALIST-IS` | ≥ +0.10 | ≤ +0.05 (≥ −0.20) | concentrated in IS-only regimes | Bundle candidate for IS-only regimes |
| `REGIME-SPECIALIST-OOS` | ≤ +0.05 (≥ −0.20) | ≥ +0.10 | concentrated in OOS regimes | Bundle candidate for OOS-recurring regimes |
| `TAIL-CONTROL` | any | any | DD reduction ≥ 20% | Risk overlay (evaluated on tail, not Sharpe) |
| `TRUE-NEG` / `EXPLORATION-NEGATIVE` | ≤ 0 | ≤ 0 | no regime gives lift; mechanism falsified | Discard / dead-paths catalog |
| `WALK-FORWARD-LEAKAGE` | n/a | n/a | actual leakage (gap=0, look-ahead) | BLOCK — methodology integrity failure |

### 4.3 `OOS / IS ≥ 0.5` is a BUNDLE-level gate, not a component gate

This single line in the v1 skill (line 158, 255) was systematically killing regime specialists. It is retained as a gate for **bundle CONFIRMATIONs** only — when claiming a unified regime-free predictor. For **component EXPLORATIONs**, the replacement is **regime-attribution analysis** + within-regime Sharpe.

### 4.4 CONFIRMATION is portfolio composition, not single-model validation

A CONFIRMATION is the act of combining N component models (each from prior EXPLORATIONs) into a unified prediction — via stacking, regime-conditional dispatch, ensemble averaging, or weighted blend. Components are evaluated for their bundle contribution (regime coverage + composition lift), not as standalone universal predictors.

## 5. What Each Role Must Do Differently

**QR (Phase 1–5, 7, 8):**
- Brief Section 4 falsifier must be **target-regime-aware** ("if target-regime IS Sharpe < X" — NOT "if OOS Sharpe < X" alone, because OOS may not contain the target regime).
- New brief Section 10 — Regime Attribution Plan (declare target regime, off-regime expectation, bundle role).
- Phase 7 / Phase 8 closeout language: replace "OVERFIT" with "IS-REGIME-SPECIALIST candidate" when criteria met.

**LightGBM Master (Phase 4.5, 7.4):**
- Phase 7.4 deliverable adds a **mandatory Regime Attribution Table** (item 0, FIRST) — IS and OOS months tagged by regime, per-regime Sharpe + trade count for this iter and BASELINE_V1, bundle-role implication proposed.

**Quant Engineer (Phase 5.5, 6):**
- Phase 5.5 gate verifies brief Section 10 (Regime Attribution Plan) is present and Section 4 falsifier is regime-aware.
- Phase 6 runner emits a regime-tagged daily PnL artifact (`reports-v1/iteration_v1-NNN/regime_attribution.csv`) for downstream LM Master + Critic consumption.

**Quant Critic (Phase 6.0, 7.5):**
- Phase 7.5 Check 3 splits into 3a (DSR/PSR), 3b (PBO), 3c (Regime attribution clarity — component candidate gate), 3d (Bundle-level OOS/IS — BUNDLE-CONFIRMATION only).
- New Check 14 (axis family validation) unchanged; existing.
- Verdict-band map updates to include `REGIME-SPECIALIST-IS`, `REGIME-SPECIALIST-OOS`, `TAIL-CONTROL`, `UNIVERSAL`, `WALK-FORWARD-LEAKAGE`.

## 6. Single Most Load-Bearing Sentence

**The walk-forward is the leakage defense; the IS/OOS split is the researcher-honesty defense; the bundle is the product.**

Memorize that line. Everything else in this memo follows from it.

---

**Established:** 2026-05-31 by user directive during cycle-5 EXPLORATION /041 backtest review.
**Supersedes:** the implicit "IS-strong / OOS-weak = overfit" framing across Phase 7.5 closeouts.
**See also:** `feedback_is_oos_divergence_is_regime_not_overfit.md` (memory), `skill_walkforward_reframe_critique.md` (full audit).
