# CONFIRMATION-005 — the OOS reveal for EXPLORATION-005 (track's first MERGE candidate)

**Date:** 2026-07-10. **One-time OOS reveal. Construction FROZEN (no post-hoc tuning).** Script: `blind_confirm_005.py`.
OOS window: 2025-03-24 → ~2026-07-08 (1.21 yr, 1322 8h periods). Evaluated against the frozen map (PHASE7-005).

## Result
| | IS (parity) | OOS |
|---|--:|--:|
| Sharpe | +0.921 (≈ +0.91 ✓) | **+0.219** |
| ann return | — | +2.4% |
| maxDD | −33% | **−73.0%** |
| turnover | 55x | 49x |
| net funding | −208bps (2021 income) | **+860bps (a COST)** |
| per-year | all positive | 2025 +0.35, **2026 −0.16** |

## FROZEN-MAP VERDICT: **FAIL**
Triggered independently by TWO frozen conditions:
1. OOS Sharpe +0.219 < +0.30 (the FAIL threshold).
2. OOS maxDD −73.0% < −60% (the FAIL threshold).
(Also: 2026 per-year −0.16 < 0, breaking the all-years-positive regime test — though not < −1.0.)

## Diagnosis — why the IS +0.91 didn't survive
The IS was overfit. Decomposition of the IS→OOS collapse (+0.91 → +0.22):
- **Multiple-testing / cadence-scan inflation:** the +0.91 was the IS-max-adjacent point of a scan that followed 4 prior NO-MERGE explorations (n_eff≈10–15). The Critic's deflated-Sharpe expectation was +0.65–0.80; actual OOS +0.22 — the overfit was *worse* than the (honest, tempered) expectation. The cross-sectional vol_low edge is real but too weak net-of-cost at 8h to clear deployable OOS.
- **Funding dodge failed OOS:** IS-2021 delivered −208bps NET INCOME (shorts received > longs paid); OOS delivered +860bps NET COST. The near-neutrality funding benefit was IS-regime-specific (2021 mania's extreme positive funding) and did not generalize to the 2025–26 funding regime.
- **Intra-rebal drift materialized (REVIEW-005 F1):** the −73% OOS maxDD (vs IS −33%) is the weekly cadence's intra-rebal concentration risk (ORDIUSDT-style squeezes) blowing up out-of-sample — exactly the unsystematic risk the Critic flagged and tempored the OOS maxDD expectation for.
- **Regime shift:** 2026 per-year −0.16; the OOS regime differs from the IS regime that produced +0.91.

## What this means for the track
Per the frozen map + pre-registration discipline: **FAIL → not deployable; NO post-hoc tuning** (no "try rebal=42" — that's mining; no bolting on hysteresis — that's a rescue, permitted only for PARTIAL not FAIL). The honest conclusion: **EXPLORATION-005 is not a deployable book.** The IS +0.91 was overfit; the OHLCV-8h vol_low cross-sectional edge — even at the optimal cadence, with the tail-capped neutral construction, funding-modeled honestly — does not survive out-of-sample.

## The track's net result (5 explorations + diagnostics + CONFIRMATION)
A thorough, honestly-executed characterization that produced **no deployable book**. What WAS produced (real, reusable value):
- A leak-safe, realistic-cost portfolio backtest foundation (blind_engine/universe/funding, 33 leak tests) — reusable for any future strategy.
- A verified methodological lesson: **rank-IC ≠ L/S P&L for skewed crypto cross-sections**; **cadence is a first-order lever** (the rebal=6 anchor capped 4 explorations); **funding is a first-order cost** (net-long pays ~12%/yr); **shorts are universally toxic at 8h** (lottery squeezes); **the OHLCV-8h cross-section on the volume-top-20 is too weak net-of-cost to deploy** (+0.22 OOS).
- Validated defensive primitives (regime-gate, leg-decoupling, tail-capped shorts, BTC-drawdown scalar) — transferable to a stronger alpha source if one is found.
- A clean demonstration of pre-registration discipline working under pressure (the frozen map prevented rationalizing the OOS failure).

Per user direction ("both substrate levers, then conclude") + the FAIL verdict: **the track concludes here.** A genuinely different pivot (OI universe / non-OHLCV mechanism / different frequency) would be a fresh line of inquiry, not a rescue of /005 — available if the user wants to continue, but the honest read is that the OHLCV-8h-cross-section edge is insufficient.
