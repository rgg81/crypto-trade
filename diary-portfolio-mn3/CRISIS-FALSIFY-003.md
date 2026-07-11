# CRISIS-FALSIFY-003 — two-layer risk architecture: BOTH shared floors FAIL their frozen bars

**Date:** 2026-07-11. **Role:** QE. **Trigger:** PLAN-AMENDMENT-002 (commit e86d945e, user-ruled —
auth A RATIFIED GAP-only Layer-1 at 4σ/10%; auth B AUTHORIZED the DD-from-peak family). **Machines:**
`analysis/portfolio/mn3_crisis.py` — `gap_only_machine` (§A) + `dd_detector` (§B) added ALONGSIDE the
frozen-as-failed 5-indicator machine (which stays on record, untouched). **Runner:**
`analysis/portfolio/mn3_layer_falsify.py` on the MN3 IS (T=4,929, 2020-01-01 → 2024-06-30, C=747).
Market-data-only; no book; no strategy return; no token; no holdout; `mn3_guard_grid` before any metric.
Both machines are scored against their OWN frozen pre-run bars. **Terminal discipline honored: nothing
was tuned; both fails are reported, not fixed.**

## THE OPEN QUESTION (the headline) — ANSWERED: **YES**

> Does GAP alone catch May-2021 and LUNA at CRISIS 0-LAG?

**YES — GAP-only reaches CRISIS at 0 LAG on all 4/4 primary episodes**, via genuine ≥4σ/10% BTC
candles, with the exact trigger candles:

| Primary | T0 | GAP CRISIS trigger candle | g / r_BTC | Timing |
|---|---|---|---|---|
| COVID | 2020-03-12 | 2020-03-12 00:00Z | 4.58σ / −7.1% | COINCIDENT |
| **May-2021** | 2021-05-19 | **2021-05-12 16:00Z** | **5.17σ / −11.3%** | **LEAD** |
| **LUNA** | 2022-05-11 | **2022-05-05 08:00Z** | **4.61σ / −7.1%** | **LEAD** |
| FTX | 2022-11-09 | 2022-11-08 16:00Z | 4.35σ / −5.2% | COINCIDENT |

May-2021 and LUNA — flagged UNCONFIRMED in DISPOSITION §3 (they were confluence catches in /001) —
are caught by GAP alone on real precursor crash candles (May-2021's −11.3% on 05-12; LUNA's −7.1%
on 05-05). **And the RATIFIED 4σ floor is load-bearing for FTX:** FTX's worst candle is 4.35σ, which
clears 4σ but NOT the /002 5σ/12% floor that killed FTX in CRISIS-FALSIFY-002 — the reversion the
user ratified is exactly what rescues FTX. GAP-only's episode-detection layer is validated: 4/4
primary CRISIS 0-LAG.

## VERDICT

| Machine | Episode bar | Calm budgets | OVERALL |
|---|---|---|---|
| **Layer-1 GAP-only (§A)** | 4/4 primary CRISIS 0-LAG — **PASS** | entries 25>16, off-ep 4.1%>3% — **FAIL** | **FAIL → DEAD** |
| **Layer-B DD-from-peak (§B)** | 4/4 primary CRISIS 0-LAG — PASS; **2/3 secondary — FAIL** | CRISIS 12.5%>8%, S+C 27.6%>25%, off-ep 6.6%>3% — **FAIL** | **FAIL → DEAD (terminal)** |

Both shared floors are DEAD by their own frozen bars. **What is ALIVE going into the field: the
Layer-2 per-construction throttle (§C) ONLY** — the binding invariant every MN3 construction ships
from birth. Per §E, the diagnostic field (DIAG-J first) unblocks regardless; Layer-2 carries crisis
risk per-construction, with no shared floor composing under it.

## 1. Layer-1 GAP-only (§A) — SCORECARD

GAP first defines 2020-01-11 08:00 (31 warmup candles); raw crisis-grade candle occupancy **0.73%**
(near its /001 coverage anchor); scored candles 4,898.

**Episodes:** primary 4/4 CRISIS 0-LAG (table above). Secondaries (reported-only, GAP expected to
miss grinders): 2021-12-04 PASS (−12.6%, 6.62σ), **Celsius/3AC MISS** (worst candle −6.9%/3.27σ —
no ≥4σ candle; the documented slow-bleed blindness, NOT a bar), 2023-08-17 PASS (6.75σ).

**Calm budgets (2-state; STRESS+CRISIS inapplicable — no STRESS state, documented not deleted):**

| Budget | Measured | Derived bar (§A) | Result |
|---|---|---|---|
| CRISIS occupancy | 5.33% | ≤6% | **PASS** |
| Distinct CRISIS entries | **25** | ≤16 | **FAIL** |
| Off-episode CRISIS occ | **4.10%** | ≤3% | **FAIL** |

**Why it fails (attribution):** 25 distinct ≥4σ/10% BTC candles over 4.5y vs the QR's derived ~11
(range 8–14). 17 of 25 entries are OFF-episode — and they are GENUINE ≥4σ/10% candles the labeled
list doesn't enumerate, **many of them violent UP candles** (short squeezes): +14.0% (2021-01-29),
+10.8% (2021-02-08), +6.9% (2020-07-27), +6.5%/+6.9% (2023-02/01), alongside real down candles
(−10.5% 2021-01-11, −11.6% 2021-09-07). The derivation assumed ~2–4 crisis candles per clustered
event; the reality is looser — most entries are ISOLATED single ≥4σ candles (19 of 25 segments are
exactly the 9-candle dwell minimum). The interrupt is sparse (5.33% occupancy, PASS) but fires on
more distinct violent candles than the entry-count ceiling allows, and on real off-episode ones
beyond the 3% off-episode bar. **Design note for the QR (fact, not a change): GAP fires on |r|, so a
symmetric ≥4σ move flattens the book on a large BTC UP-squeeze — arguably not "the model is lost"
for a market-neutral book; 7 of the 17 off-episode entries are up-candles.** Per §A terminal rule,
a violent-candle interrupt that is not sparse ENOUGH (entries/off-episode) is dead — Layer-1 DEAD.

## 2. Layer-B DD-from-peak (§B) — SCORECARD

DD first defines 2020-01-30 16:00 (89 warmup candles, the 90c peak window); blue-chip-core used on
68.0% of live candles, BTC-DD fallback on the rest (COVID/2020 pre-core era); scored candles 4,840.

**Primary episodes: 4/4 CRISIS 0-LAG — PASS.**

| Primary | First CRISIS | Timing | DD at hit | Source |
|---|---|---|---|---|
| COVID | 2020-03-12 08:00 | COINCIDENT | −41.0% | BTC-DD (core under-defined — the fallback's purpose) |
| May-2021 | 2021-05-19 00:00 | COINCIDENT | −31.5% | BTC-DD |
| LUNA | 2022-05-06 00:00 | LEAD | −30.8% | BCDD |
| FTX | 2022-11-09 16:00 | COINCIDENT | −33.3% | BCDD |

**FTX cleared the −30% CRISIS line at −33.3%** — the QR's flagged secondary risk (FTX borderline at
−27 to −33%) did NOT bite; the blue-chip-median (not BTC-alone) choice paid off, as alts drew down
harder than BTC.

**Secondary episodes: 2/3 ≥STRESS — FAIL.** 2021-12-04 PASS (LEAD, later reached deeper), Celsius/3AC
PASS (−43.0% BCDD), **2023-08-17 deleveraging MISS** — trough DD only −17.2%, above the −20% STRESS
line. That episode was a sharp one-candle deleveraging with no sustained drawdown, which a
drawdown-from-peak detector structurally cannot see (the mirror image of GAP's slow-bleed blindness).

**Calm budgets:**

| Budget | Measured | Derived bar (§B) | Result |
|---|---|---|---|
| CRISIS occupancy | **12.48%** | ≤8% | **FAIL** |
| STRESS+CRISIS occupancy | **27.62%** | ≤25% | **FAIL** |
| Distinct CRISIS entries | 9 | ≤10 | **PASS** |
| Off-episode CRISIS occ | **6.58%** | ≤3% | **FAIL** |

**Why it fails (the QR's #1 pre-stated risk fired): the level-persistence trap partially won.** The
30d self-resetting window helped (segments DO terminate — the detector is not pinned to a 2021
all-time high) but not enough: the 2022 bear produced multi-hundred-candle CRISIS segments
(2021-11-26→2022-02-14 = 242c; 2022-04-26→2022-07-14 = 238c) as the blue-chip median sat below its
own decaying 30d peak for months. CRISIS occupancy 12.48% (vs ≤8%) and STRESS+CRISIS 27.62% (vs the
deliberately-generous ≤25%) both exceed — the detector is elevated through genuine-but-ordinary bear
grind, which is precisely the ≤25% falsifier's target. Off-episode CRISIS 6.58% (vs ≤3%) is the same
mechanism outside the 7 labeled windows. Entries (9) pass — the events are few but LONG. Per §B
terminal no-retry, Layer-B is DEAD; its slow-bleed coverage falls to Layer-2.

## 3. §D composition — implemented + leak-tested (for whichever layers survive)

`compose_gross_scalars` (elementwise min), `compose_universe_tightest` (FULL<TOP20<BLUECHIP_CORE<FLAT),
and `binding_layer` (forensic precedence GAP>DD>construction) are implemented and pass the full leak
battery (`tests/test_mn3_layers.py`): min-composition determinism + order-independence; tightest-universe;
inert-default byte-identity (all-ones composed scalar ⇒ engine bit-for-bit); decision-lag ([k−1]
consumption — a composed flat at k−1 flattens the book at k, the same-candle decoy ignored); corrupt-future
on the COMPOSED scalar (min of two past-only machines is past-only). With both shared floors dead, the
composition currently reduces to `min(s_con)` = the Layer-2 per-construction throttle alone, but the
plumbing is ready and leak-proven for the moment a shared floor is revived under a future amendment.

## 4. Composed architecture — what is ALIVE

```
  Layer-2 per-construction throttle (binding invariant, ALWAYS present)
  Layer-1 GAP-only  = FAIL (DEAD)
  Layer-B DD-peak   = FAIL (DEAD, terminal no-retry)
```

Going into the field: **Layer-2 ONLY.** Every MN3 construction ships its own pre-registered,
sustained-regime-aware gross throttle (the A3/SCUD precedent) with its own falsification arm; there is
no shared crisis floor composing under the constructions. Per §E this does NOT block the diagnostic
field — DIAG-J proceeds. Honest facts for the QR's disposition (reported, not acted on):
- **GAP-only is one clustering-assumption away from passing** — it caught 4/4 primaries at 0-LAG and
  passed CRISIS occupancy (5.33%≤6%); it died only on entry-count (25 vs 16) and off-episode (4.1% vs
  3%), largely from symmetric firing on violent UP candles. A directional (down-only) or
  entry-debounced variant is a plausible future design question — NOT a re-registration I may make.
- **Layer-B's occupancy overshoot is modest** (27.6% vs 25%; 12.5% vs 8%) and its 4/4 primary +
  FTX-at-−33.3% catch is genuinely strong; its death is the sustained-bear occupancy the QR
  pre-registered as its most-likely failure mode. The trap won, as flagged.
- Both are terminal per AMENDMENT-002; neither is re-registerable. The disposition (revive a variant
  under a future amendment vs Layer-2-only) is the QR's / user's call.

## 5. Coverage / datacheck

Panel health: BTC grid OK, MN3 IS extent covered (live DEGRADED only from the post-fetch freshest
candle — irrelevant to an IS run). Regime occupancy PASS, 1h gate 219 COMPLETE, OI broad start
2021-12-01 — unchanged, detail in CRISIS-FALSIFY-001 §6.

## 6. Artifacts

- Machines: `analysis/portfolio/mn3_crisis.py` — `gap_only_machine`, `dd_detector`, `dd_signal`,
  `name_drawdown`, `run_dd_state_machine`, `compose_gross_scalars`, `compose_universe_tightest`,
  `binding_layer`, `classify_episode_series`, `occupancy_series`, `state_segments` (the 5-indicator
  machine + PLAN-AMENDMENT-001 code above them is untouched, FROZEN AS FAILED).
- Runner: `analysis/portfolio/mn3_layer_falsify.py` (deterministic; reproduce:
  `uv run python analysis/portfolio/mn3_layer_falsify.py`).
- Tests: `tests/test_mn3_layers.py` (20 — both machines' mechanics + full §2.5 leak battery + §D
  composition leak tests). Full track suite **169/169 green** (105 original + 20 infra + 24 crisis +
  20 layers); ruff clean.
- Token ledger: `diary-portfolio-mn3/REVEAL-LEDGER.md` (no spends).

*— QE, MN3 track. Both machines built exactly as frozen and reported exactly as they behaved. Two
honest terminal fails; the field proceeds Layer-2-only. Nothing tuned; holdout untouched.*
