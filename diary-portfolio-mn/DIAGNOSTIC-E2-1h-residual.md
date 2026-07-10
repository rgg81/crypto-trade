# DIAGNOSTIC-E Stage 2 — 1h Residualized Short-Horizon Cross-Section (MN track)

**Date:** 2026-07-10 · **Role:** QR · **Script:** `analysis/portfolio/mn_diag_e2_residrev_1h.py`
(committed spec = PLAN.md §2 Sketch E′ Stage 2, run exactly as frozen; trial ledger: 16 grid
cells, opened and closed here). Raw scored log: `diary-portfolio-mn/DIAGNOSTIC-E2-run.log`.
**Data hygiene:** `mn_panel_health()` → 8h grid OK (DEGRADED = live-feed staleness only,
irrelevant for IS-only); own 1h coverage check: BTC 1h IS grid T=52,608, 0 gaps, guard-passed
(`mn_guard_grid`, step=1h); 361-symbol §4.3 scope fully fetched, 303/361 gap-free.
**Blinding/IS:** 1h grid strictly < 2026-01-01; 8h panel via `mn_split.mn_slice_is`;
`mn_guard_grid` passed on both grids. Old-track `is_mask`/`OOS_CUTOFF` never touched.
**Verification:** DIAG-D's vectorized Spearman imported (not forked), re-cross-checked vs
`scipy.stats.spearmanr` on 300 random candles (max abs diff 1.11e-16); full re-run reproduced
the scored output bit-identically (modulo timing lines).

## VERDICT — pre-registered kill criterion (PLAN §2 Sketch E′, verbatim, per stage)

> "KILL the stage if no cell has |IC| ≥ 0.02 with same-sign stability across IS halves AND
> 2×-cost coverage at the cell's natural cadence."

| Arm | Measured | Verdict |
|---|---|---|
| \|IC\| ≥ 0.02 + same-sign halves | **13 of 16 cells eligible** (max \|IC\| = 0.0433 at L=4,h=1, t = −42.2 — ALL 16 cells REVERSAL, 16/16 same-sign halves) | passes broadly |
| 2×-cost coverage at natural cadence, evaluated PER CELL (Stage-2 registered scope) | ALL 13 eligible cells FAIL — best net2x_ann = **−229.6%** (L=4,h=24); champion L=4,h=1 = **−2338.5%** | **FAILS 13/13** |

**STAGE 2 IS KILLED.** With Stage 1 dead (2026-07-10), **Sketch E′ is DEAD** per the
registered rule ("both dead ⇒ sketch dead"). The kill is not marginal: the single
positive-gross cell (+90.6%/yr at L=4,h=1) sits behind a 16,072×/yr turnover wall
(≈ 1,206%/yr at 1× costs). The PLAN's pre-registered arithmetic — "15bps round-trip per unit
turnover means only cells with forward moves ≥ ~30bps net of beta survive" — was exactly
right: the measured forward move per candle at the champion is **~1 bp** vs a 15 bp
round-trip. No post-hoc re-gating (PLAN §5.7). Stage-2 lookbacks/thresholds die with the
sketch (PLAN §6).

---

## 0. Construction (as registered + implementation decisions on record)

- **Grid:** BTC 1h IS grid (52,608 candles, 2020-01-01 → 2025-12-31, 0 gaps). 8h panel used
  only for universe/regimes/health machinery.
- **Universe:** PIT top-40 built ON THE 8H PANEL (DIAG-A/D/E1 builder imported verbatim:
  trailing 30-candle mean $-vol, ex-stables, ≥270-candle history), membership mapped to each
  1h decision candle via the **last CLOSED 8h candle** (DIAG-B's live-computable mapping).
  Decision on record: the track has ONE universe definition and the §4.3 fetch scope was
  generated from exactly this object; a 1h-native re-reading of "trailing 30-candle" would
  be a different universe and was NOT run. Mean 36.6 members/candle on the 1h grid (matches
  the 8h diagnostics); ever-members = 361 = the fetched scope exactly. Top-20 = robustness.
- **Residualization FIRST:** r̃[t] = r[t] − β[t−1]·r_BTC[t], β = `mn_beta.rolling_beta`
  imported VERBATIM with frozen defaults (window=270, min_periods=135, λ=0.33, clip [0,3])
  on the NATIVE 1h grid, [k−1] lag. Reading on record: the PLAN registers the beta window in
  CANDLES ("rolling 270-candle past-only OLS beta"), so at 1h the window is 270 hours
  (~11.3d); the fixed-wall-clock alternative (2160 candles = 90d) was NOT run (it would be an
  unledgered second beta spec). Warmup = 135 all-NaN rows, excluded; residual coverage over
  member-candles = 100.0%; median prior-filled names/candle = 201 (young/thin names get the
  cross-sectional shrinkage prior — mostly non-members).
- **Signal:** Signal_L[t] = trailing L-candle MEAN of residual returns, min obs L//2+1 (the
  DIAG-A/D/E1 majority convention, carried for cross-stage comparability), L ∈ {4,12,24,48}.
- **IC:** per-candle Spearman of Signal_L vs forward h-candle residual-return sum (strict
  all-finite), h ∈ {1,4,12,24}, min 20 members — the frozen 4×4 = 16-cell grid.
- **Cost machinery:** DIAG-D harness imported — held-weights decile book (gross 2.0), funding
  on every held leg (1h bucket-sum via `blind_funding` on the 1h grid — settlements land in
  the exact hold-hour; coverage complete, 361/361 direct), 7.5 bps/side × Σ|Δw|, 2×-twin,
  natural cadence rebal=h with FULL phase sweep (phase-agnostic headline, PLAN §5.5). Per the
  Stage-2 registered text ("the map reports cost coverage per cell"), coverage was computed
  for ALL 16 cells, so the kill conjunction is evaluated per cell — no champion shortcut.
  Annualization at CPY=8,760 (local `agg_cadence_1h`; DIAG-D's 8h constant must not leak).
- t_adj = t/√h for overlapping forward windows; the kill floor is on |IC| level, unaffected.

## 1. Hole-policy disclosure (charter §4; DIAG-B precedent adopted)

- Interior gaps: 58/361 syms, 7,970 missing hours (0.087% of the finite panel). Dominant
  cause: the two upstream archive holes **2022-02-26→28 (72h)** and **2022-04-01→02 (48h)**
  (1H-FETCH-REPORT §4). Three halt/rebrand gaps exceed the fill limit: TLM 708h, ICP 626h,
  BNX 518h.
- **Policy (fixed a-priori, = DIAG-B's):** interior forward-fill ≤96h, FLAGGED
  (`ffill_interior` imported verbatim); never past a symbol's last raw-finite candle; 6,406
  candle-values fabricated (0.070%). **Decisions EXCLUDED on hole-filled hours** (Signal_L
  NaN-masked where the name's own decision price is fabricated — 1,782 member-hours
  excluded); **positions hold through** holes in the cadence sim. The ffill makes multi-hour
  residual sums approximately correct across a hole (−β·r_BTC accrues during the freeze, the
  full jump lands at resume). Gaps >96h stay NaN past the limit; those names drop from the
  cross-section there via the strict all-finite machinery. Deviation from E1's strict-NaN
  convention is deliberate and disclosed: an IC probe can drop rows, but a HELD book must not
  silently delete cross-hole moves; DIAG-B is the track's 1h precedent.

## 2. THE MAP — 16 cells: rank IC AND decile tails AND cost coverage (top-40, full IS)

IC + IC-oriented decile-tail spread (bps per h candles; the DIAG-D/E1 two-layer columns):

| cell | mean IC | t (t_adj) | sign | tail mean | median | %pos | t(sp) |
|---|---|---|---|---|---|---|---|
| **L=4, h=1** | **−0.0433** | −42.2 (−42.2) | REV | **+1.03** | +5.23 | 52.4% | +1.50 |
| L=4, h=4 | −0.0350 | −34.2 (−17.1) | REV | −1.17 | +6.33 | 51.4% | −0.89 |
| L=4, h=12 | −0.0209 | −20.8 (−6.0) | REV | −8.06 | +5.91 | 50.8% | −3.90 |
| L=4, h=24 | −0.0110 | −10.9 (−2.2) | REV | −11.12 | +0.64 | 50.1% | −3.93 |
| L=12, h=1 | −0.0343 | −33.2 (−33.2) | REV | −0.91 | +2.04 | 50.9% | −1.30 |
| L=12, h=4 | −0.0312 | −30.1 (−15.0) | REV | −6.45 | +1.56 | 50.4% | −4.88 |
| L=12, h=12 | −0.0229 | −22.1 (−6.4) | REV | −20.32 | −2.82 | 49.6% | −9.61 |
| L=12, h=24 | −0.0150 | −14.4 (−2.9) | REV | −20.74 | −0.80 | 49.9% | −7.08 |
| L=24, h=1 | −0.0301 | −28.8 (−28.8) | REV | −0.38 | +2.47 | 51.1% | −0.56 |
| L=24, h=4 | −0.0291 | −27.2 (−13.6) | REV | −5.15 | +1.95 | 50.4% | −3.91 |
| L=24, h=12 | −0.0229 | −21.5 (−6.2) | REV | −16.15 | −0.70 | 49.9% | −7.34 |
| L=24, h=24 | −0.0156 | −14.7 (−3.0) | REV | −24.14 | −5.67 | 49.5% | −7.92 |
| L=48, h=1 | −0.0211 | −20.2 (−20.2) | REV | −1.61 | +1.03 | 50.4% | −2.28 |
| L=48, h=4 | −0.0227 | −21.2 (−10.6) | REV | −7.31 | −0.79 | 49.8% | −5.28 |
| L=48, h=12 | −0.0238 | −22.1 (−6.4) | REV | −16.27 | −0.98 | 49.9% | −7.08 |
| L=48, h=24 | −0.0231 | −21.6 (−4.4) | REV | −23.57 | −9.52 | 49.2% | −7.46 |

Cost coverage per cell at natural cadence rebal=h (phase-agnostic; net = residual price leg
+ funding − 7.5bps/side × turnover; the registered decider):

| cell | gross_ann | fund_ann | NET (1×) | NET (2×) | turnover/yr | Sharpe | phases+ | exW NET |
|---|---|---|---|---|---|---|---|---|
| L=4, h=1 | **+90.6%** | −18.3% | −1133.1% | −2338.5% | 16,072× | −7.90 | 0/1 | −1089.0% |
| L=4, h=4 | −25.4% | −11.6% | −579.7% | −1122.4% | 7,236× | −4.22 | 0/4 | −563.7% |
| L=4, h=12 | −59.8% | −5.8% | −248.1% | −430.7% | 2,434× | −1.90 | 0/12 | −241.3% |
| L=4, h=24 | −40.0% | −5.5% | −137.5% | −229.6% | 1,228× | −1.10 | 1/24 | −120.0% |
| L=12, h=1 | −79.4% | −17.1% | −839.5% | −1582.4% | 9,906× | −5.79 | 0/1 | −803.5% |
| L=12, h=4 | −141.0% | −13.8% | −493.2% | −831.7% | 4,513× | −3.54 | 0/4 | −497.5% |
| L=12, h=12 | −149.3% | −11.4% | −341.8% | −523.0% | 2,416× | −2.57 | 0/12 | −331.7% |
| L=12, h=24 | −76.6% | −10.7% | −178.5% | −269.8% | 1,217× | −1.39 | 0/24 | −160.2% |
| L=24, h=1 | −33.4% | −24.1% | −604.0% | −1150.5% | 7,287× | −4.21 | 0/1 | −530.3% |
| L=24, h=4 | −113.0% | −23.0% | −385.9% | −635.7% | 3,332× | −2.77 | 0/4 | −329.9% |
| L=24, h=12 | −118.9% | −18.9% | −273.4% | −409.1% | 1,808× | −2.02 | 0/12 | −234.0% |
| L=24, h=24 | −89.3% | −15.6% | −195.6% | −286.3% | 1,209× | −1.47 | 0/24 | −173.8% |
| L=48, h=1 | −140.7% | −35.9% | −569.9% | −963.2% | 5,244× | −3.88 | 0/1 | −562.5% |
| L=48, h=4 | −160.0% | −32.7% | −375.8% | −559.0% | 2,442× | −2.62 | 0/4 | −379.4% |
| L=48, h=12 | −120.5% | −28.7% | −250.5% | −351.7% | 1,350× | −1.79 | 0/12 | −257.1% |
| L=48, h=24 | −85.8% | −24.7% | −179.6% | −248.7% | 921× | −1.32 | 0/24 | −192.2% |

**Shape of the map — does 1h change the 8h object?** Partly, and instructively:

1. **Rank layer: reversal EVERYWHERE, and far stronger than at 8h.** 16/16 cells REV
   (8h: 19/20), t-stats to −42 (8h max −14.9) — mechanically boosted by 8× the observations,
   but the IC LEVEL at the short corner (−0.043) also matches the strongest 8h cells. IC
   decays monotonically with horizon (h=1 → h=24 roughly halves to quarters it) and, at
   short horizons, with lookback: the freshest 4h of residual flow predicts the next hour
   best. **The 8h map's momentum island (L=3,h=21) has NO 1h analogue** — the map is purely
   reversal; menu E's premise (short-horizon reversal exists at 1h) is rank-confirmed.
2. **Tail layer: the two-layer structure persists but INVERTS at the shortest horizon.** At
   L=4,h=1 the reversal-oriented tail spread is POSITIVE (+1.03 mean, +5.23 median, and D1
   bounces +1.10 bps while D10 continues only +0.11) — the **first cell in the entire MN
   diagnostic series (D, E1, E2) where the IC-oriented decile book has positive gross**. At
   1h/1h the liquidity-provision bounce dominates even the extreme deciles; the squeeze-
   continuation tails need hours to run. By h=12–24 the 8h pathology fully reasserts: tail
   means −16 to −24 bps against positive-to-flat medians — mid-rank reversal + episodic
   extreme-tail continuation, third independent confirmation.
3. **Era decay (the discount that matters):** all 16 cells same-sign across halves, but
   half1 ≈ 2× half2 at the short corner (champion −0.0585 → −0.0299), and per-year champion
   IC decays monotonically 2020 −0.067 → 2025 −0.023 while the SPREAD decays through zero:
   2020 +7.05 bps (t +4.87), 2021 +4.58 (t +2.57), then 2022–2025 ≤ +0.29 with 2025 at
   **−2.21** (t −1.21). The tradeable component of 1h cross-sectional reversal has been
   competed away over the sample — the rank signal survives (market-makers still fade flow;
   we would be paying them, not being them), but the decile-book edge is a 2020–21 artifact.
4. **Buckets:** reversal IC is strongest in MANIA at 1h (champion −0.0591, t −21.8) —
   opposite of 8h where CRASH led. CRASH IC fades to insignificance at h=24 (−0.004 to
   −0.006): liquidation flow at 1h keeps running within the day (cascades persist), while
   mania chases revert within the hour. The champion spread earns ONLY in MANIA (+5.67
   bps/1c, t +3.39; CHOP −0.04, dead; CRASH +1.98, t +0.62) — a mania-fade, not an
   all-conditions book (G4/G5 would object even before costs).

## 3. Champion cell L=4,h=1 — full characterization (the only positive-gross cell)

- Deciles (bps fwd-1c residual, D1 = lowest past-resid): D1 **+1.10**, D2 +0.36, D3 +0.31,
  D4 −0.19, D5 −0.21, D6 −0.52, D7 −0.76, D8 −0.50, D9 −0.65, D10 **+0.11**. Monotone-ish
  through D7 — a real gradient, unlike the 8h U-shape; only D10 still continues.
- Oriented spread: +1.03 bps/1c mean, +5.23 median, 52.4% pos, t +1.50 — **not significant
  even gross**, ≈ +90.6%/yr gross, entirely 2020–21 + MANIA (above).
- Contamination twin (fwd window fully before 2025-03): spread +1.59 bps (t +2.20), IC
  −0.0467 — the kill does not depend on the burned sub-window (it is even friendlier there);
  exW NET −1089%/yr.
- **Cost coverage at rebal=1:** turnover 16,072×/yr × 7.5 bps/side ≈ **1,205%/yr in
  fees+slip** vs +90.6% gross and −18.3% funding — cost-to-gross ≈ 13×.
  NET −1133%/yr, net2x −2339%/yr, net Sharpe −7.9. An L=4 sort re-deals its extreme deciles
  essentially every hour; nothing survives that.
- **Funding drag is negative on ALL 16 cells** (−5.5% to −35.9%/yr): the reversal
  orientation is anti-carry at 1h too — long recent losers still paying positive funding,
  short squeeze names whose funding is negative. E1's lesson replicated on the 1h grid.
- Beta before/after residualization (measured, not assumed): RAW +0.0903 / RESID **+0.0702**
  (β_ETH +0.072) — return-space residualization barely moves realized spread beta, third
  independent confirmation. Bucket-conditional β_BTC of the residual stream: **CRASH +0.3402
  (se 0.036)**, MANIA +0.0009. The conditional-beta asymmetry of recent losers (E1 §5,
  DIAG-A) replicates at 1h: the reversal book is structurally LONG crash beta (+0.34 ≫ the
  G2 bound 0.15), and the trailing estimator cannot see it by construction.
- Top-20 twin: IC −0.0437 (t −32.6), spread +0.32 bps mean / +6.37 median, NET −1239%/yr —
  same structure, worse net. Not a top-40 artifact.

## 4. What dies with the stage, and what the finding is worth elsewhere

1. **Dead as registered:** all 16 Stage-2 cells as 1h decile books, both orientations (the
   momentum flip has no eligible cell and negative-gross tails at h≥4), and with Stage 1
   dead ⇒ **Sketch E′ (residualized past-return horizon map) is DEAD as a family.** Menu E's
   1h reversal exists in rank space and fails as a book — killed by turnover arithmetic that
   was pre-registered, not discovered.
2. **Transferable observations (recorded, not acted on):**
   - **The cost wall is the binding constraint on ANY 1h cross-sectional decile book in this
     universe:** natural-cadence turnover ranges 921–16,072×/yr → 69–1,206%/yr at 1× costs.
     Any future intraday MN idea must be born with turnover suppression (banding, mid-rank
     books, event-conditioning) or die here; a rank-IC of 0.04 with t=−42 bought nothing.
   - **Two-layer structure now confirmed on three independent sorts** (taker-flow 8h,
     past-return 8h, past-return 1h) with a new boundary datum: at 1h/h=1 the bounce briefly
     dominates the tails; continuation needs hours. Squeeze/cascade tails are an
     hours-to-days phenomenon, not minutes-to-an-hour.
   - **Crash-beta asymmetry of loser-long books replicates at 1h** (+0.34 conditional on
     CRASH after residualization) — third confirmation that measurement-level rolling-beta
     residualization does NOT deliver crash-conditional neutrality; the §4.1 hedge overlay's
     G2-CRASH test remains the binding test for every future book.
   - **1h reversal is era-decaying** (per-year IC −0.067 → −0.023, spread +7 bps → −2.2 bps):
     evidence of competed-away intraday liquidity provision. Discount any future revisit's
     2020–21 sub-sample accordingly.
   - MANIA-bucket 1h chase-fade (+5.67 bps/1c, t +3.39 at the champion) is the one live
     texture — but it is bucket-conditional gross on a book whose all-in cost is ~13× its
     gross; any revisit is a NEW registration with its trial count carried into n_eff.
3. **Process note:** the first launch crashed at section [6] on a mechanical numpy
   read-only-buffer error (pandas rolling output), BEFORE any IC/kill metric was computed or
   printed; the one-line fix (`np.array(...)` buffer ownership) was made and the script
   relaunched. No scored number existed pre-fix; not a re-gate. A full post-score re-run
   reproduced the scored output bit-identically (modulo timing lines).
4. n_eff ledger for family E after this diagnostic: Stage-1 = 20 cells (dead 2026-07-10),
   Stage-2 = 16 cells (dead here), no other knobs tried, no amendments, coverage scored once
   per cell as registered. **Family E′ ledger CLOSED at 36 trials, 0 survivors.**

## 5. Track state after this entry

Family A banked (terminal); **D dead, E1 dead, B dead, E2 dead (⇒ Sketch E′ dead)**;
C = the last open diagnostic (OI-gated; backfill per OI-BACKFILL-REPORT). E2 was the last
data-ready diagnostic — the §3 diagnostic queue is now exhausted except C.

*— QR, MN track, 2026-07-10. Probe run exactly as pre-registered: the |IC|/stability arm
passed on 13/16 cells (the strongest rank signal any MN diagnostic has measured), and the
2×-cost coverage arm killed every one of them — the sole positive-gross cell carries a ~13×
cost-to-gross ratio; every other cell is negative before a basis point of cost. A clean kill
with the cost wall measured precisely is the process working. Not committed (per dispatch).*
