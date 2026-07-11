# DIAGNOSTIC-C — OI/Leverage-Crowding Fade Probe (MN track)

**Date:** 2026-07-11 · **Role:** QR · **Script:** `analysis/portfolio/mn_diag_c_crowding.py`
(committed spec = PLAN.md §2 Sketch C, run exactly as frozen; trial ledger: 3 horizon cells)
**Data hygiene:** `mn_panel_health()` → BTC grid OK (T=7147 contiguous); DEGRADED = live-feed
staleness only, irrelevant to an IS-only probe. OI-coverage guard (own assertion, per dispatch):
core-20 first-OI-bar dates all match OI-BACKFILL-REPORT §4 (no regression); OI loaded for
360/361 top-40 ever-members; scored-member breadth ≥20/candle on 99.9% of candles from 2022-02.
**Blinding/IS:** panel sliced via `mn_split.mn_slice_is` before any computation; `mn_guard_grid`
passed on the panel grid AND explicitly on the OI-aligned grid (raw OI CSVs extend into 2026 —
every holdout row is dropped by the reindex before any feature is computed). Old-track
`is_mask`/`OOS_CUTOFF` never touched. The pinned OI `.shift(1)` (decision at t consumes OI rows
≤ t−1) is asserted by an in-script corrupt-future positive control: corrupting `oi[t0:]` leaves
`z_dOI[:t0+1]` bit-identical — PASSED (t0=3945).

## VERDICT — pre-registered kill criteria (PLAN §2 Sketch C, verbatim)

| # | Criterion (frozen) | Measured | Verdict |
|---|---|---|---|
| (a) | \|IC\| < 0.02 at ALL of the three horizons | IC = **−0.0068 / −0.0027 / −0.0002** at h=1/3/9 — max \|IC\| = 0.0068, a third of the bar | **KILLED** |
| (b) | event-study forward move at best horizon < 2× round-trip cost (30 bps; RT = 15 bps single-leg, decision D8) | fade move at h=1 = **−3.1 bps** — not merely below cost, the WRONG SIGN | **KILLED** |
| (c) | event rate < 5/month | 300.4/month (14,572 onsets / 48.5 months) | SURVIVES |
| (d) | IC sign flips between IS halves at best horizon | half1 −0.0070 / half2 −0.0068 — same sign | SURVIVES |

**SKETCH C IS DEAD.** Two criteria fired independently and decisively. Per PLAN §5.7 the sketch
dies as registered; no post-hoc re-gating; the crowding-score composition, windows, and event
definitions die with it (PLAN §6: no knob inheritance without explicit re-registration).

**Track consequence:** family C was the last open diagnostic. The ENSEMBLE capstone's trigger
condition (ORCHESTRATOR_BRIEF_MN.md addendum: ≥2 families with BANKED candidates) does **NOT**
fire. **A3-1 stands alone.**

---

## 0. Construction (as frozen + implementation decisions on record)

Frozen (PLAN §2 Sketch C): c = rank-sum of { z(ΔOI, 90-candle), funding-extremity z,
taker-imbalance z }, signs aligned so high c = crowded-LONG; Spearman IC of c vs forward
{1, 3, 9}-candle residual return (mechanism predicts NEGATIVE); top-decile |c| event study with
1–30-candle forward residual paths; PIT top-40 universe (top-20 robustness), `rolling_beta`
residualization at [k−1], 7.5 bps/side costs + funding + 2×-twin, contamination disclosure.

Implementation decisions recorded in the script header BEFORE the run (D-numbers cited):
- **I1** OI input = `sum_open_interest` — a SNAPSHOT (last 5-min reading in the bar, despite the
  name; verified in `main.py:1426`). The stub-poisoned flow SUM columns (OI-BACKFILL-REPORT
  §5.2) are NOT consumed; had they been, `sum_*/count_*` normalization would be mandatory.
- **I2** Pinned shift: ΔOI[t] = oi[t−1]/oi[t−2] − 1 (pct change of the LAGGED snapshot); the
  corrupt-future positive control pins the convention at runtime.
- **D3** z windows: 90-candle per-name trailing z, min 45 obs, for ALL three components (window
  pinned in the PLAN for ΔOI; adopted for the other two; TI z = DIAG-D's frozen construction
  verbatim). Per-name time-series z, not cross-sectional z — "extremity vs the name's own
  history" is the mechanism, and a cross-sectional z would collapse to the raw-level rank
  under the rank-sum.
- **D4** Taker-imbalance input = panel `taker_buy_volume/volume` (complete, never
  stub-poisoned); the metrics-file taker L/S alternative was NOT scored (no extra trials).
- **D6** Rank-sum: per candle, over top-N members with ALL THREE z finite (strict); each
  component cross-sectionally ranked (average ties), normalized to [0,1]; c ∈ [0,3]; dev = c−1.5.
- **D7** Events = ONSETS of the per-candle top decile by |dev| (k = n//10); fade = −sign(dev).
- **D8** Kill-(b) threshold: RT = single alt-leg entry+exit = 15 bps → 2×RT = 30 bps, scored on
  the FADE-signed move (the registered trade); hedge-inclusive 60 bps twin disclosed, not scored
  (moot — the move is negative).
- **D10** Decile book in the REGISTERED fade orientation (long D1 lowest-c / short D10), not
  re-oriented by measured IC sign.

**Window disclosure (mandatory):** OI archive-policy start is 2021-12-01 for every non-BTC name
(OI-BACKFILL-REPORT §3). First scored candle = **2021-12-16**; usable window = 4,425 of 6,576 IS
candles (**67% of IS**). The registered IS halves (split 2023-01-01) are ASYMMETRIC under this
window: half1 = 1,139 scored candles (~2021-12→2022-12) vs half2 = 3,286. Median scored members
= 40/40 (breadth is not the problem).

## 1. Component ICs vs the combined score — the score is diluted by its own components

Spearman IC vs forward-h residual return, top-40, all components on the SAME scored set:

| signal | h=1 | h=3 | h=9 |
|---|---|---|---|
| **c (combined, frozen)** | **−0.0068 (t −2.51)** | −0.0027 (t −1.00) | −0.0002 (t −0.07) |
| z_ΔOI | **+0.0075 (t +2.81)** | +0.0086 (t +3.24) | **+0.0107 (t +4.11)** |
| z_fund | −0.0061 (t −2.20) | −0.0025 (t −0.89) | −0.0041 (t −1.46) |
| z_TI | **−0.0133 (t −4.76)** | −0.0108 (t −3.87) | −0.0068 (t −2.48) |

The headline structural finding: **the ΔOI component has the WRONG SIGN for the mechanism.**
z_ΔOI is a *continuation* signal at every horizon (IC +0.011 at h=9, t +4.1, strengthening with
horizon) — at 8h, OI build predicts positive relative residual return. Rising OI marks capital
inflow / trend confirmation, not late-crowd fragility. The registered rank-sum therefore ADDS a
momentum component to two weak reversal components (funding, TI), and they cancel: the combined
score (max |IC| 0.0068) is WEAKER than its own TI component alone (0.0133). No component
individually clears the 0.02 bar either — and the strongest one (TI) is family D's signal,
already dead on cost coverage (DIAG-D kill (b): −214%/yr net2x).

**Which component carries it: z_TI carries what little exists; z_ΔOI actively fights it;
z_fund is a faint echo of family A's carry.** The frozen composition is internally contradictory
as measured.

## 2. Rank IC and decile tails, side by side (the D/E1/E2 lesson)

Best horizon h=1, per-decile mean forward residual return (bps, D1 = lowest c / crowded-SHORT):

| D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
|---|---|---|---|---|---|---|---|---|---|
| −9.71 | −5.28 | +0.99 | −0.23 | −1.17 | −6.76 | −6.98 | −3.14 | −3.82 | −1.51 |

- Not monotone, and BOTH tails sit below the mid-ranks' mild dip: D1 (crowded-short) keeps
  FALLING hardest (−9.7 bps/candle) — capitulation continues, fading it catches the knife;
  D10 (crowded-long) out-performs the row mean (−1.5 vs −3.8 avg).
- Registered FADE spread (long D1 / short D10): mean **−9.10 bps/candle (t −1.95),
  ≈ −100%/yr gross** — the fade orientation loses before a single basis point of cost.
  Median −3.23 bps, 49.0% of candles positive: mean-driven, tail-episode-dominated, exactly the
  DIAG-D signature.
- Note the whole decile row is negative-mean (unconditional top-40 residual bleed ≈ −3.8
  bps/candle over this window) — relevant to §3's event interpretation.

Top-20 robustness column: IC −0.0023 / +0.0028 / +0.0066 at h=1/3/9 — the combined score's IC
**flips sign across breadth** at two of three horizons. There is no hidden edge in the tighter
cross-section (fade spread −18.7 bps, t −2.77, i.e. loses MORE).

## 3. Event study (registered step 3) — tails continue, and the "moves" are mostly alt-bleed

14,572 onsets / 48.5 months = 300.4/month (crowded-LONG 7,595 / crowded-SHORT 6,977). Mean
fade-signed cumulative residual path (bps):

| h | 1 | 2 | 3 | 6 | 9 | 15 | 21 | 30 |
|---|---|---|---|---|---|---|---|---|
| all events | −3.1 | −3.7 | −3.5 | −5.2 | −3.2 | +2.2 | −1.2 | +11.4 |
| t | −0.79 | −0.77 | −0.64 | −0.68 | −0.37 | +0.21 | −0.10 | +0.84 |
| crowded-LONG (fade short) | +1.4 | +6.0 | +8.5 | +22.4 | +41.4 | +74.8 | +97.0 | +148.4 |
| crowded-SHORT (fade long) | −8.1 | −14.3 | −16.6 | −35.3 | −51.7 | −76.9 | −108.2 | −137.9 |

- Aggregate fade move at h=1 (the kill-(b) input): **−3.1 bps vs the 30 bps threshold** — and at
  no horizon on the 1–30 path does the aggregate reach even 1× RT (max +11.4 bps at h=30,
  t +0.84).
- The side split looks dramatic (+148 / −138 bps at h=30) but decomposes honestly: the scored
  cross-section's unconditional residual drift is ≈ −3.76 bps/candle ≈ **−113 bps over 30
  candles**. Both event classes are followed by residual DECLINE of ~138–148 bps — i.e. only
  **−36 bps (crowded-LONG) and −25 bps (crowded-SHORT) of event-specific excess** beyond the
  alt-bleed baseline, over 10 days. The two sides' declines cancel in any long/short book (the
  cross-sectional form nets out the common drift — that is what it is FOR), leaving the ~flat
  aggregate path. What remains per side is thin against 15 bps RT, clustered in time
  (event-level t-stats overstate independence), and one-sided-short-alts in structure — the
  predecessor's directional-costume failure mode.
- DIAG-D's transferable observation is CONFIRMED in the crowding-conditioned form it predicted:
  the crowded-SHORT tail continues (cascades persist — fade-long loses monotonically to −138
  bps), while the crowded-LONG tail decays only slowly. Conditioning taker tails on OI build +
  funding did NOT convert continuation into a harvestable fade.
- Regime buckets of events: CRASH +0.1 bps (t +0.01, n=1,555), MANIA −9.5 (t −0.80), CHOP −2.8
  (t −0.62) at h=1 — no regime refuge. Per-year: 2022 −8.8 / 2023 −0.0 / 2024 −4.3 / 2025 −0.6 —
  no year positive.

## 4. Regime buckets, halves, per-year (best horizon, IC and fade spread)

| bucket | n | fade spread (bps/1c) | t | IC |
|---|---|---|---|---|
| CRASH | 492 | +0.93 | +0.07 | +0.0039 |
| MANIA | 402 | −18.52 | −1.43 | −0.0036 |
| CHOP | 3,530 | −9.43 | −1.76 | −0.0087 |

The (weak) rank-fade is a CHOP phenomenon; CRASH is flat with a POSITIVE-sign IC — the
mechanism's "capitulation pays the fader in crashes" leg is absent exactly where an
all-conditions book needs it (same hole DIAG-D found).

| year | n | fade spread (bps/1c) | t | IC |
|---|---|---|---|---|
| 2021 (Dec 16–31 sliver) | 47 | +48.17 | +1.31 | −0.0300 |
| 2022 | 1,092 | −15.45 | −1.02 | −0.0060 |
| 2023 | 1,095 | −7.15 | −1.41 | −0.0057 |
| 2024 | 1,096 | −3.19 | −0.49 | −0.0094 |
| 2025 | 1,094 | −13.10 | −1.72 | −0.0054 |

No full year positive on the spread; IC hugs zero everywhere. Halves at h=1: −0.0070 / −0.0068
(same sign, criterion (d) survives — on a disclosed 1,139-vs-3,286 asymmetric split). h=9 flips
(−0.0019/+0.0004), immaterial at these magnitudes. Contamination twin (forward window fully
before 2025-03): fade spread −8.94 bps (t −1.64), IC −0.0074 (n=3,506) — **the kill does not
depend on the burned sub-window.**

## 5. Cost coverage at the registered cadences (fade decile book, phase-agnostic)

| rebal | gross ann | funding ann | NET ann (1×) | NET ann (2×) | turnover/yr | net Sharpe | ex-2025-03+ NET | phases >0 |
|---|---|---|---|---|---|---|---|---|
| 1 | −99.7% | **+19.1%** | −354.5% | −628.3% | 3,652× | −3.45 | −362.2% | — |
| 3 | −15.8% | +15.4% | −94.2% | −188.1% | 1,252× | −1.08 | −95.0% | 0/3 |
| 9 | −8.1% | +9.3% | −30.9% | −63.0% | 428× | −0.43 | −37.0% | 2/9 |

- **Turnover realism is fatal on its own:** a rank-sum of three fast 90-candle z's reshuffles
  the extreme deciles nearly every candle — 3,652×/yr at rebal=1 (274%/yr burned at 1× costs),
  still 428×/yr at rebal=9 (32%/yr at 1×, 64% at 2×). Even a correctly-signed IC of the measured
  magnitude could never clear this hurdle (the DIAG-D cost story, replayed).
- **The funding leg is a TAILWIND (+9 to +19%/yr):** the fade book shorts high-funding names and
  longs negative-funding names, so it passively collects carry — family A's mechanism wearing
  C's clothes. The OI/TI price legs then lose more than the carry collects. The one profitable
  ingredient in this book is already banked, in clean form, as A3-1.

## 6. Beta before/after neutralization (fade-spread stream, h=1)

| stream | β_BTC | (se) | β_ETH | (se) |
|---|---|---|---|---|
| RAW (before residualization) | −0.0573 | 0.0311 | −0.0188 | 0.0232 |
| RESID (after) | −0.0436 | 0.0309 | −0.0103 | 0.0231 |

Bucket-conditional β_BTC of the residual stream: **CRASH +0.086 (se 0.063)**, MANIA −0.071
(se 0.089). Near-flat unconditionally, but the crash-bucket sign is positive — the fade book's
loser-long leg (long capitulating, crowded-short names) is exactly the +0.34-crash-beta lesson's
budget line, here in miniature. Academic interest only, since there is no edge to neutralize.

## 7. What dies with the sketch, and what the finding is worth elsewhere

1. **Dead as registered:** the OI/leverage-crowding fade, the rank-sum composition, its 90-candle
   windows, the top-decile |c| event definition, and the fade decile book at every registered
   cadence. Criteria (a) and (b) fired independently — this is not a marginal kill.
2. **No adjust-and-re-register case.** The strongest component (TI, |IC| 0.0133) belongs to dead
   family D and fails C's own bar; the novel component (ΔOI) is continuation-signed, so no
   re-weighting of a FADE score can be rescued by it; turnover economics are hopeless at any
   registered cadence. A hypothetical "OI-build continuation" sort would be a NEW family
   (opposite mechanism, fresh registration per PLAN §6) — and at max |IC| ≈ 0.011 with the same
   churn profile and the D-lesson tails risk, it does not merit one on this evidence.
3. **Transferable observations (recorded, not acted on):**
   - z_ΔOI at 8h is mildly CONTINUATION-signed cross-sectionally (t +4.1 at h=9, monotone in
     horizon): OI build = inflow confirmation. Any future OI axis should start from that sign.
   - Crowding-conditioned event tails reproduce DIAG-D's asymmetry: crowded-SHORT names keep
     falling (cascade persistence), crowded-LONG names decay slowly; both sides' 30-candle
     "moves" are ~75–80% unconditional alt residual bleed (−113 bps/30c baseline), which any
     cross-sectional L/S form correctly nets out.
   - The fade book passively collects +9–19%/yr funding — confirmation that the funding
     cross-section (family A, banked) is the real payer in this corner of the panel.
4. **n_eff ledger for family C:** 3 registered horizon cells scored; component ICs are
   attribution of the frozen composition, not selection trials; no amendments; no post-hoc
   re-orientation scored. One implementation-decision set (I1–D11), recorded pre-run.
5. **Track state:** families B/C/D/E1/E2 all dead by pre-registered criteria; family A banked
   (A3-1). The pre-registered cross-family ENSEMBLE capstone trigger (≥2 banked families) does
   not fire. A3-1 stands alone as the MN track's sole candidate book.

*— QR, MN track, 2026-07-11. Probe run exactly as pre-registered; kill criteria (a) and (b)
fired; sketch C dead as registered. The last open diagnostic closes with a clean kill — the
process working, and the funding-carry family's uniqueness confirmed from a second angle.*
