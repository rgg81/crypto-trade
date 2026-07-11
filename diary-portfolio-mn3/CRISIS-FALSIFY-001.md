# CRISIS-FALSIFY-001 — the frozen §2 machine FAILS its IS falsification

**Date:** 2026-07-11. **Role:** QE. **Diagnostic order-1 (PLAN §4).**
**Machine spec:** PLAN §2.1–§2.5, implemented FROZEN in `analysis/portfolio/mn3_crisis.py`
(constants are module-level pins; zero deviations from the pre-registration).
**Run:** `analysis/portfolio/mn3_crisis_falsify.py` on the MN3 IS panel
(T=4,929 8h candles, 2020-01-01 → 2024-06-30, C=747 perps, funding 745/747 direct-resolved).
`mn3_guard_grid` called before any metric; no book anywhere in the harness; no strategy
return computed. **This is a reportable FAIL, not a problem that was fixed silently.
Nothing was tuned.** Per §2.4 the ONE permitted anchor-family-constrained re-registration
is the QR's call.

## VERDICT

| Arm | Result |
|---|---|
| Primary episodes (CRISIS, 0 LAG) | **3/4 — FAIL** (COVID unscoreable: machine in WARMUP at T0) |
| Secondary episodes (≥ STRESS) | **3/3 — PASS** |
| Calm budgets (all four) | **0/4 — FAIL** (STRESS+CRISIS occupancy 85.25% vs ≤15% budget) |
| **OVERALL** | **FAIL** |

## 1. Episode scorecard (pass window = [T0−5d, end of day T0+1])

| Episode | T0 | Required | First hit | Timing | Result | Vote attribution at hit |
|---|---|---|---|---|---|---|
| COVID | 2020-03-12 | CRISIS | never (in WARMUP) | MISS | **FAIL** | GAP=2 (defined, voted crisis at T0); XVOL/CORR/FUND/BREADTH all UNDEFINED at T0 |
| May-2021 | 2021-05-19 | CRISIS | 2021-05-14T00:00Z | LEAD | PASS | already in CRISIS at window start (entered 2021-05-12 via multi-indicator confluence) |
| LUNA | 2022-05-11 | CRISIS | 2022-05-06T00:00Z | LEAD | PASS | XVOL=2 at hit (segment entered 2022-04-26) |
| FTX | 2022-11-09 | CRISIS | 2022-11-08T16:00Z | LEAD | PASS | XVOL=2 FUND=2 GAP=2 BREADTH=2 — textbook 4-indicator confluence |
| 2021-12-04 flash | 2021-12-04 | ≥STRESS | 2021-12-04T00:00Z | COINCIDENT | PASS | GAP=2 BREADTH=2 (reached CRISIS) |
| Celsius/3AC | 2022-06-13 | ≥STRESS | 2022-06-08T00:00Z | LEAD | PASS | CORR=1 at hit |
| 2023-08-17 delev | 2023-08-17 | ≥STRESS | 2023-08-12T00:00Z | LEAD | PASS | in-STRESS at window start |

**The detection layer works.** Every episode the machine could legally score was caught at the
required state with LEAD or COINCIDENT timing — 0 LAG anywhere, FTX with all-but-one indicator
at crisis grade on the entry candle.

## 2. The COVID failure — structural, not threshold-related

- The on-disk 8h panel **starts 2020-01-01** (fetch-config start; Binance USDT-perps also barely
  existed earlier — 11 perps listed by 2020-02-01, 24 by 2020-03-12).
- §2.1's indicator universe requires **≥90d (270-candle) history**: at COVID T0 **zero** names
  qualify. First defined votes: CORR/BREADTH 2020-05-09, XVOL/FUND 2020-06-22 (robust-z needs
  135 finite inputs on top of the universe). Machine WARMUP ends **2020-06-22** (521 candles);
  COVID sits 3.4 months inside it → §2.2 rule 4 forces NORMAL → MISS.
- **GAP was live and voted crisis at T0** (BTC −27%/8h class candles; the single-sufficient fast
  path would have fired NORMAL→CRISIS) — warmup semantics suppressed it.
- The §2.1 rationale "min_periods=135 makes COVID (IS candle ~215) scoreable" rested on a false
  premise: it counted robust-z warmup only, not the 270-candle universe-history requirement, and
  assumed panel data pre-dating 2020-01-01. Under the frozen spec, **COVID is unscoreable by
  construction on this dataset** — no threshold value changes that.
- Ambiguity flagged for QR adjudication (not resolved in the machine's favor here): §2.2 says
  WARMUP candles are "excluded from falsification scoring", §2.4 says "4/4 primary at CRISIS".
  Strict reading (used for the verdict): COVID = FAIL. Lenient reading: COVID = UNSCOREABLE,
  pass bar effectively 3/3 on scoreable episodes. The QR owns this call.

## 3. Calm-budget failure — the machine is "on" most of the time

Scored (defined, non-WARMUP) IS candles: 4,408.

| Budget | Measured | Bound | Result |
|---|---|---|---|
| CRISIS occupancy | **9.07%** | ≤ 4% | FAIL (2.3×) |
| STRESS+CRISIS occupancy | **85.25%** | ≤ 15% | FAIL (5.7×) |
| Distinct CRISIS entries | **33** | ≤ 10 | FAIL (3.3×) |
| CRISIS outside episodes ±15d | **5.95%** | ≤ 1.5% | FAIL (4×) |

Per-indicator vote occupancy over scored IS (the attribution):

| Indicator | calm | stress | crisis | note |
|---|---|---|---|---|
| XVOL (robust-z 2.0/3.0) | 86.1% | 5.7% | **8.2%** | tail occupancy ~60× the 0.13% normal-coverage anchor |
| CORR (abs 0.75/0.85) | 90.5% | 9.5% | 0.0% | stress-grade chronic; crisis never |
| FUND (robust-z 2.0/3.0) | 86.0% | 4.8% | **9.2%** | same pathology as XVOL |
| GAP (4σ / 10%) | 97.4% | 1.9% | 0.7% | **well-behaved** — the only indicator near its coverage anchor |
| BREADTH (abs 0.85/0.95) | 78.8% | **12.6%** | **8.6%** | synchronized 3d drawdowns are chronic in crypto |

Mechanism of the blowout (diagnosis, not a fix):
1. **Standard-normal coverage anchors are wrong for regime-persistent series.** The robust z of
   median-RV and of mean-|funding| is right-skewed and persistent: elevated-vol regimes last
   months (2020-H2, all of 2021, the 2022 bear, 2023-H1 — see the churn ledger), so z≥3
   occupancy is 8–9%, not 0.13%. A z-threshold on a persistent series measures regime
   membership, not event arrival.
2. **A single crisis-grade vote is a STRESS-trigger** (§2.2). XVOL, FUND, BREADTH each carry
   8–9% crisis-vote occupancy and they co-move → ≥1 crisis vote on ~20%+ of candles.
3. **The 21-clean-candle de-escalation multiplies raw trigger occupancy** — every isolated
   trigger costs ≥7 days of ≥STRESS. Correct design for aftershocks; explosive when combined
   with (1)+(2).
4. CRISIS entries (33): ≥2 simultaneous crisis votes among the three saturated indicators occur
   in every extended risk regime, incl. 2020-11→2021-03 (a 328-candle mania-era segment at
   peak CRISIS) and most of 2023 — periods that are volatile but not "the model is lost".
5. State churn: 42 non-NORMAL segments; implied whole-book gross turnover from state changes
   alone = 75 gross units over 4.5y (~562 bps at 7.5 bps/side, illustrative) — an insurance
   premium far above what a real book could carry.

## 4. What passed (worth preserving in any re-registration)

- GAP's construction (lagged EWMA σ + absolute floors) is near its coverage anchors AND caught
  2021-12-04 and FTX — the fast path works as designed.
- Episode timing: 0 LAG on everything scoreable; the escalate-fast machinery is sound.
- The hysteresis/dwell mechanics, forward-fill, DEGRADED-hold, and the [k−1] engine hookup all
  passed their full leak suite (24 machine tests: corrupt-future per indicator + composite,
  append-invariance, decision-lag byte-identity, no-book-input; `tests/test_mn3_crisis.py`).

## 5. Failure protocol

§2.4 permits ONE re-registration via PLAN-AMENDMENT, thresholds moving only along their
pre-declared anchor families, never toward any book metric, documented BEFORE any book-level
backtest consumes the machine. **That decision is the QR's, not the QE's.** Notes the QR will
need: (a) the COVID miss is a warmup/universe-coverage issue — it is NOT reachable by any
threshold move within the declared anchor families; (b) the calm-budget blowout is
anchor-reachable in principle for CORR/BREADTH (round-number family) and XVOL/FUND (normal
coverage-point family), but the z-on-persistent-series pathology in §3.1 is structural to the
indicator construction, not to the threshold value.

## 6. Datacheck / coverage note (PLAN §5.5 gates, run this session)

- **Panel health:** BTC grid OK (T=7,149 contiguous, 2020-01-01 → 2026-07-10); MN3 IS extent
  fully covered. Live-feed check DEGRADED only because the freshest candle (2026-07-11 00:00)
  post-dates the last fetch — irrelevant to an IS-only run.
- **Regime occupancy (PLAN §5.3, run BEFORE any diagnostic is scored):** IS 2020-01→2024-06,
  4,839 defined candles: CRASH 13.16% / MANIA 18.85% / CHOP 67.99% — **all ≥5%, PASS**, no
  re-registration needed. Bucket rules confirmed immutable.
- **1h completeness gate (full 361-symbol scope; DIAG-K blocker):** **219 COMPLETE** (≥99.9%
  coverage of own listed overlap with the MN3 IS), 53 GAPPY (worst: BNXUSDT 96.8%, TLMUSDT
  97.3%, ICPUSDT 97.7%; a cluster shares a 72h gap ≈ a common 3-day outage window), 89
  NO-IS-OVERLAP (listed after 2024-06-30 — the MN3 IS ends earlier than the v2 window), 0
  missing files. **DIAG-K universe = the 219 verified-complete list**
  (`mn3_datacheck.run_1h_completeness_gate`).
- **OI archive starts on the MN3 IS:** BTCUSDT usable from 2020-09-01; the archive has a hard
  broad start at **2021-12-01**, where the PIT top-40 jumps from <10 to 40/40 members with
  usable OI (thresholds ≥10 through ≥40 all cross on that date). Confirms PLAN §3.1/§3.2:
  family-H S2 sleeve start ≈ 2021-12; family-G OI features are NaN before per-name archive
  start with era-correlation disclosed. Latest-listing members of the IS-end top-40: TONUSDT
  2024-03-01, BOMEUSDT 2024-03-16. 599 OI archive dirs total. The `.shift(1)` usable-start
  convention is enforced in `mn3_datacheck.oi_usable_start_ms` and unit-tested.

## 7. Artifacts

- Modules: `analysis/portfolio/{mn3_split,mn3_crisis,mn3_regimes,mn3_datacheck,mn3_crisis_falsify}.py`
- Tests: `tests/test_mn3_infra.py` (20) + `tests/test_mn3_crisis.py` (24); full track suite
  149/149 green (105 pre-existing + 44 new); ruff clean.
- Token ledger initialized (no spends): `diary-portfolio-mn3/REVEAL-LEDGER.md`.
- Full run log: scratchpad `crisis_falsify_run.log` (reproduce:
  `uv run python analysis/portfolio/mn3_crisis_falsify.py`; deterministic).

*— QE, MN3 track. The machine was built exactly as frozen and reported exactly as it behaved.*
