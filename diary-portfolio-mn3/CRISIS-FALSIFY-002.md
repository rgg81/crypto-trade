# CRISIS-FALSIFY-002 — the re-registered machine FAILS; spec FROZEN AS FAILED (terminal)

**Date:** 2026-07-11. **Role:** QE. **Diagnostic order-1 re-run** after
PLAN-AMENDMENT-001 (commit c7553bd4 — the ONE permitted anchor-family-constrained
re-registration). **Machine spec:** PLAN §2 as amended, implemented FROZEN in
`analysis/portfolio/mn3_crisis.py` (zero deviations from the amendment — every §A/§B/§C item
below is coded verbatim). **Run:** `analysis/portfolio/mn3_crisis_falsify.py` on the MN3 IS
(T=4,929, 2020-01-01 → 2024-06-30, C=747, funding 745/747 direct). `mn3_guard_grid` before any
metric; no book anywhere; no strategy return. **Scored against the UNCHANGED §2.4 bars (§D).**

**This is the SECOND FAIL. Per PLAN-AMENDMENT-001's terminal commitment, the crisis-machine spec
is FROZEN AS FAILED. There is no third machine, no budget move, no rescue. The QR decides
GAP-only vs escalation. Nothing was tuned to make it pass.**

## VERDICT

| Arm | 001 (original) | 002 (amended) | Bar |
|---|---|---|---|
| Primary episodes (CRISIS, 0 LAG) | 3/4 (COVID unscoreable) | **3/4 (FTX MISS)** — FAIL | 4/4 |
| Secondary (≥ STRESS) | 3/3 PASS | 3/3 PASS | 3/3 |
| CRISIS occupancy | 9.07% | **3.35% — PASS** | ≤4% |
| STRESS+CRISIS occupancy | 85.25% | **20.95% — FAIL** | ≤15% |
| Distinct CRISIS entries | 33 | **17 — FAIL** | ≤10 |
| Off-episode CRISIS occ | 5.95% | **2.53% — FAIL** | ≤1.5% |
| **OVERALL** | FAIL | **FAIL (terminal)** | — |

The amendment worked where it aimed (COVID fixed, CRISIS occupancy now passes, all four
per-indicator occupancies collapsed) but broke FTX and left three budgets over bar. **The two
failures are the SAME mechanism pulling in opposite directions** — see §4.

## 1. Episode scorecard (pass window [T0−5d, end of day T0+1])

| Episode | T0 | Req | First hit | Timing | Result | Attribution |
|---|---|---|---|---|---|---|
| **COVID** | 2020-03-12 | CRISIS | 2020-03-12 08:00Z | COINCIDENT | **PASS (fixed)** | GAP=2 alone (all cross-sectional abstain) — the §A abstention fix worked exactly as designed |
| May-2021 | 2021-05-19 | CRISIS | 2021-05-14 00:00Z | LEAD | PASS | already CRISIS at window start (entered 05-12) |
| LUNA | 2022-05-11 | CRISIS | 2022-05-11 16:00Z | COINCIDENT | PASS | FUND=2 BREADTH=2 confluence (GAP=1) |
| **FTX** | 2022-11-09 | CRISIS | never (STRESS only) | MISS | **FAIL (regressed)** | reached STRESS 11-05→11-19 but never the ≥2-crisis confluence; see §4 |
| 2021-12-04 flash | 2021-12-04 | ≥STRESS | 2021-12-04 00:00Z | COINCIDENT | PASS | GAP=2 BREADTH=2 |
| Celsius/3AC | 2022-06-13 | ≥STRESS | 2022-06-11 08:00Z | LEAD | PASS | BREADTH=2 |
| 2023-08-17 delev | 2023-08-17 | ≥STRESS | 2023-08-17 16:00Z | COINCIDENT | PASS | GAP=2 BREADTH=2 XVOL=1 |

## 2. Per-indicator vote occupancy — the load-bearing collapse (QR prediction: HIT)

001 = over forward-filled votes / all scored candles; 002 = among DEFINED candles (abstention).
The crisis-grade collapse is unambiguous under either denominator:

| Indicator | 001 calm/stress/crisis | 002 calm/stress/crisis | crisis Δ |
|---|---|---|---|
| XVOL | 0.861 / 0.057 / **0.082** | 0.967 / 0.031 / **0.0020** | −97% |
| CORR | 0.905 / 0.095 / **0.000** | 0.930 / 0.046 / **0.0238** | 0 → small (as predicted) |
| FUND | 0.860 / 0.048 / **0.092** | 0.962 / 0.023 / **0.0151** | −84% |
| GAP | 0.974 / 0.019 / **0.007** | 0.974 / 0.023 / **0.0031** | −56% (12%/5σ floor) |
| BREADTH | 0.788 / 0.126 / **0.086** | 0.978 / 0.009 / **0.0137** | −84% |

The onset/coincident transforms (§B) did exactly what the amendment predicted: crisis-grade
per-indicator occupancy fell from 8–9% to 0.2–2.4%; CORR moved off its chronic-9.5%-stress /
0%-crisis pathology to 4.6%/2.4%; GAP dropped under the raised floor. **This is why CRISIS
occupancy now passes at 3.35%.**

## 3. Calm budgets

Scored (live, post-warmup) IS candles: 4,898 (warmup now only 31 leading candles — the §A fix:
the machine goes live when GAP first defines 2020-01-11, not when the last cross-sectional
indicator warms 2020-06-22). DEGRADED mid-series candles: 0.

| Budget | 002 | Bound | Result | QR prediction |
|---|---|---|---|---|
| CRISIS occupancy | 3.35% | ≤4% | **PASS** | HIT (predicted ≤4%) |
| STRESS+CRISIS occupancy | 20.95% | ≤15% | FAIL | MISS (predicted 6–15%; flagged primary residual risk) |
| Distinct CRISIS entries | 17 | ≤10 | FAIL | MISS (predicted 6–9; flagged tightest budget) |
| Off-episode CRISIS occ | 2.53% | ≤1.5% | FAIL | MISS (predicted PASS) |

The STRESS layer is still too broad: onset stress-grade votes + BREADTH stress, combined via the
≥2-stress-confluence STRESS-trigger, still fire on ~21% of candles once the 12c de-escalation
tail is applied. 17 distinct CRISIS entries come from ≥2-crisis-confluence events scattered
across the 4.5y (56 non-NORMAL segments; churn-implied whole-book gross turnover 73 units,
~547 bps illustrative). Off-episode CRISIS (2.53%) is the residual of confluence CRISIS entries
that land outside the seven pre-registered episode windows (e.g. 2020-11 mania, 2023-03 SVB
banking week, 2024-04→05 — a 97-candle CRISIS segment).

## 4. The terminal finding — onset detection and FTX are the SAME dial

FTX is the diagnostic key. BTC's FTX crash was a **multi-candle slow bleed**, not one violent
candle: the worst 8h candle in the entire FTX pass window was **−7.2% (g=4.35σ)** (sequence
−3.9%, −5.2%, −6.4%, −7.2%). Consequences under the amended spec:

1. **GAP:** −7.2% / 4.35σ clears the STRESS floor (7% / 3σ) but NOT the raised CRISIS floor
   (12% / 5σ). Under the ORIGINAL floor (10% / 4σ) 4.35σ ≥ 4 → GAP would have voted CRISIS and
   caught FTX on the fast path (as it did in 001). **The §B5 crisis-floor raise — needed to buy
   distinct-entry margin — removed the exact backstop that caught FTX.**
2. **Onset indicators:** at the FTX peak (11-09 16:00) only BREADTH reached crisis-grade
   (0.775 ≥ 0.60); FUND onset reached z=2.67 (stress, <3), XVOL z=1.48 and CORR z=1.03 (both
   calm). n_crisis = 1 → the ≥2-crisis-confluence CRISIS-trigger never assembled → STRESS only.
   **Why the onset forms were muted at FTX:** FTX arrived after the LUNA→FTX autumn of sustained
   elevated vol and high funding, so V_long / F_long were already high → the short/long ratios
   ln(V_short/V_long), ln(F_short/F_long) stayed modest. **This is the very property that fixed
   the calm budget** (onset doesn't fire in sustained regimes) — and it is exactly why FTX,
   which arrived *inside* a sustained-elevated regime, is not seen as an onset.

**The tension is structural, not a threshold.** The amendment's §E predicted "FTX's textbook
4-indicator confluence should survive (onset forms fire harder at true onsets than level forms)."
It did not: FTX was not a clean onset — it was a crash *within* an already-stressed regime. You
cannot simultaneously have (a) onset transforms that stay quiet through a months-long elevated
regime (required to pass STRESS+CRISIS ≤15%) and (b) crisis detection of a crash that occurs
*inside* such a regime (required to pass FTX) — the same short/long-ratio dial governs both.
And the GAP fast-path that could have bridged the gap was tightened (§B5) to protect the
entry-count budget. The three failing budgets and the FTX miss are one coupled system.

## 5. QR pre-registered expectations (§E) — scored hit/miss

| Prediction (§E) | Outcome | Hit/Miss |
|---|---|---|
| COVID PASS via GAP by ~candle 30 | COINCIDENT via GAP-alone at T0 | **HIT** |
| May-2021/LUNA/FTX 0-LAG preserved; **FTX 4-indicator confluence survives** | May-2021/LUNA PASS; **FTX MISS** | **MISS** |
| Secondaries ≥STRESS; Celsius re-hits COINCIDENT | 3/3 PASS (Celsius LEAD 06-11) | **HIT** |
| Per-indicator crisis occ 8–9%→0.5–2%; CORR crisis 0→~1%; GAP ~unchanged | XVOL 0.20% / FUND 1.51% / BREADTH 1.37% / CORR 2.38% / GAP 0.31% | **HIT** |
| CRISIS occupancy ≤4% | 3.35% | **HIT** |
| STRESS+CRISIS ≤15% (range 6–15%; flagged residual risk) | 20.95% | **MISS** (self-flagged) |
| Distinct CRISIS entries 6–9 (flagged tightest; >10 = FAIL) | 17 | **MISS** (self-flagged) |
| Off-episode CRISIS ≤1.5% | 2.53% | **MISS** |
| Disclosed residual: onset misses a slow-building crisis (claimed "no IS primary is of that type") | FTX was exactly that type (slow multi-candle bleed in a sustained regime) | the disclosed hole fired |

The QR's occupancy-collapse thesis was correct and precise; its episode-preservation thesis was
wrong for FTX, and the disclosed "slow-building crisis" hole — asserted absent from the IS
primaries — was in fact FTX.

## 6. State of the machine (terminal)

- Spec FROZEN AS FAILED (PLAN-AMENDMENT-001 §terminal). No third amendment.
- The QR's two documented options: **(a) GAP-only** — the one proven event-arrival component
  (well-behaved 97.4%/2.3%/0.31% occupancy; caught COVID, 2021-12-04, 2023-08-17 outright; a
  degraded but honest one-indicator machine) — noting GAP-alone would ALSO miss FTX under the
  12%/5σ crisis floor (FTX's worst candle was 7.2%/4.35σ), so GAP-only needs its own crisis-floor
  decision; or **(b) escalate the design question to the user.** This is the QR's call, not the
  QE's.
- Engineering note for whichever path: FTX is caught by EITHER the old GAP crisis floor (10%/4σ)
  OR a multi-candle/cumulative gap detector — the current single-candle GAP + raised floor is the
  specific combination that misses it. Reporting this as a fact, not proposing a change.

## 7. Coverage / datacheck (unchanged from CRISIS-FALSIFY-001, re-verified this run)

Panel health: BTC grid OK, MN3 IS extent covered (live check DEGRADED only from the post-fetch
freshest candle — irrelevant to an IS run). Regime occupancy PASS (CRASH 13.16% / MANIA 18.85% /
CHOP 67.99%). 1h gate 219 COMPLETE. OI broad start 2021-12-01. Full detail in CRISIS-FALSIFY-001 §6.

## 8. Artifacts

- Amended module: `analysis/portfolio/mn3_crisis.py` (PLAN-AMENDMENT-001 §A/§B/§C verbatim).
- Runner: `analysis/portfolio/mn3_crisis_falsify.py` (deterministic; reproduce:
  `uv run python analysis/portfolio/mn3_crisis_falsify.py`).
- Tests: `tests/test_mn3_crisis.py` (24, updated to the amended spec — abstention replaces
  forward-fill; §C timings; raised GAP floor) + `tests/test_mn3_infra.py` (20). Full track
  suite 149/149 green; ruff clean.
- Token ledger: `diary-portfolio-mn3/REVEAL-LEDGER.md` (no spends).

*— QE, MN3 track. The amended machine was built exactly as frozen and reported exactly as it
behaved. A second FAIL is a reportable terminal result, not a problem to fix silently.*
