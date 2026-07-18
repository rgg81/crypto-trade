# team-06 research brief — t06-ls-ratio-contrarian-v1

Family (APPROVED, registry.jsonl): **Fade per-coin long/short-ratio positioning extremes.**
Registered after FCFS collision on primary (residual momentum → team-03). This brief section
(§1–§9) is PRE-REGISTERED before any experiment was run; the QE SPEC (§10) is filled in after
the ledgered experiments select the final parameters, under the §6 selection rule.

## 1. Mechanism & economic rationale

Binance publishes per-symbol positioning ratios for USDT perps (aux panels):

| aux key | Binance metric | who it measures |
|---|---|---|
| `ls_accounts` | global long/short ACCOUNT ratio | all accounts by count — retail-dominated |
| `tt_ls_accounts` | top-trader account ratio | top-20%-margin accounts, by count |
| `tt_ls_positions` | top-trader POSITION ratio | top traders, position-weighted ("smart book") |
| `taker_ls_vol` | taker buy/sell volume ratio | aggressive flow of the bar |

Mechanism: retail perp accounts are the dominant marginal player in alt perps and they
counter-trend by habit — they average down into falling coins and short into rallies. A
per-coin EXTREME in the global account long/short ratio (vs that coin's own norm) therefore
marks a distressed crowd: extreme long-crowding = layers of averaged-down longs with thin
liquidation buffers below (forced-unwind fuel); extreme short-crowding = squeeze fuel.
Warehousing the other side of that crowd earns (a) the positioning-unwind price move and
(b) structurally, the funding the crowd pays — the fade side is typically the
funding-receiving side, so the tournament's native funding P&L is a tailwind, not a drag.

Why it persists: liquidation cascades are mechanical (forced flow), retail flow is
attention-driven and non-adaptive at the weekly horizon, and the capital that could arbitrage
it away must pay funding and warehouse inventory risk to do so.

Note on sign vs momentum: because retail averages down, per-coin ls_accounts extremes often
coincide with recent price DISTRESS; fading the crowd (shorting the dip-bought name) can be
momentum-flavored at the coin level. That is fine — the registered mechanism is the
positioning-crowding unwind, whatever its correlation with price momentum turns out to be.

## 2. Data honesty — coverage window (checked FIRST, e01)

Known constraint accepted at registration: ratio panels are NaN pre-~2020-09 and for dead
names. Sister-team ledgered finding (journaled, shared by orchestrator): OI-panel
cross-sectional breadth is effectively thin until late 2021. The ratio panels ship in the
same Binance metrics files, so **e01 (before any signal work) measures, per candle, the count
of ELIGIBLE names with (a) valid ratio data and (b) a valid W=90 rolling z-score**, for all
four panels.

Pre-registered honest-window rule: `T0` = first candle after which the 30-day rolling median
of eligible names with a valid core-signal z-score stays ≥ 25 (comfortably above the 5/side
breadth floor after L/S splitting). The falsifier (§7) is evaluated on [T0, 2024-06-30].
The OFFICIAL metric (full IS window, 2020-01 →) will include a flat pre-T0 stub; that
dilution is accepted and reported, not hidden.

## 3. Core signal construction (formulas fixed up-front)

For ratio panel `R` (core: `ls_accounts`):

1. `x = log(R)` where `R > 0`, else NaN (ratios are multiplicative; log symmetrizes).
2. Per-coin rolling z: `z[t,i] = (x[t,i] − mean_W(x[:,i])) / std_W(x[:,i])`, rolling window
   `W` candles, `min_periods = W//2`, current bar INCLUDED (aux row t is same-bar info,
   usable at t's close — charter convention). std==0 → NaN.
3. Clip `z` to ±3 (fixed, not tuned).
4. Fade sign: `s = −z`.
5. Optional turnover smoothing: EMA of `s` with span `E` (E=1 means none).
6. Cross-sectional transform (one of two, selected by experiment):
   - `demean`: subtract the cross-sectional mean of `s` over names that are eligible AND
     non-NaN at t;
   - `rank`: centered cross-sectional rank of `s` in [−0.5, +0.5] over the same name set.
7. Names with NaN signal → NaN weight (flat). The engine owns eligibility masking, gross
   normalization, caps, lag, costs, funding, vol-targeting.

Variants (same family — positioning-ratio crowding, aux ratio panels only):
- Panel swap: same pipeline on `tt_ls_accounts`, `tt_ls_positions`, `taker_ls_vol` — ALL
  with fade sign only. Pre-commitment: if `taker_ls_vol` works only with FOLLOW sign, it is
  team-05's taker-flow family — I drop the panel rather than flip the sign. Same discipline
  for `tt_ls_positions`: a follow-sign top-trader signal alone is not my family; top-trader
  panels may enter only as the ANCHOR of the spread below.
- Smart-dumb spread: `s = z_smart − z_retail` where `z_smart = z(tt_ls_positions)`,
  `z_retail = z(ls_accounts)` — fade the retail crowd relative to the smart-money anchor
  (still a positioning-crowding fade; both legs are family panels).

## 4. Expected regime behavior (fixed tags, pre-registered)

- COVID crash (2020-02→03): NO DATA (panels NaN) — flat, honestly excluded.
- 2020-21 bull: modest positive. Retail shorts rallies → we long the squeezing leaders;
  funding collected on shorts of crowded-long names offsets trend headwind.
- May-2021 crash: positive early (crowd was max-long into the top); whipsaw risk at the
  V-bottom where the crowd is briefly right.
- 2021 ATH run: modest positive, same logic as 2020-21 bull.
- 2022 bear: expected STRONGEST — persistent distress names (LUNA cohort etc.) with retail
  averaging down for months; shorts collect the unwind.
- FTX-aftermath chop: positive — range markets favor fading positioning extremes.
- ETF bull: modest positive; risk of underperformance if leadership is broad and untouched
  by retail shorting.
- Post-halving chop: positive, as FTX chop.
A materially different realized pattern (e.g., all P&L from one regime) must be reported
as-is and weighs against submission.

## 5. Parameter plan (plateaus over peaks)

| param | grid | rationale |
|---|---|---|
| W (z window) | {45, 90, 135, 180} candles (15–60 d) | crowding builds over days–weeks; <15d is noise, >60d stale norms |
| E (EMA span) | {1, 3, 6, 12} candles | turnover control at 8h cadence; 12–30 bps round-trip compounds |
| XS transform | {demean, rank} | rank robust to outlier z; demean keeps magnitude info |
| clip | 3.0 FIXED | not tuned |
| min_periods | W//2 FIXED | not tuned |
| panel/variant | core, 3 panel-swaps (fade only), spread | mechanism variants, not free parameters |

Budget: ≤ ~12 ledgered experiments for the whole program (hard cap 40).

## 6. Selection rule (pre-registered)

1. Grid W×E on the core panel with each XS transform; compute net IS Sharpe @1× (official
   window) plus honest-window Sharpe.
2. Identify the connected plateau of configs with Sharpe ≥ 0.8 × grid max. Pick the config
   nearest the plateau center (median W, median E inside the plateau); tie-break: lower
   turnover. NEVER select a config with a negative-Sharpe neighbor (adjacent W or E).
3. Variants/spread may be combined with the core only if standalone-positive on the honest
   window AND the equal-weight combo beats the best single on BOTH cost tiers. No weight
   optimization — equal weight only.
4. Submission gates: 2×-stress Sharpe > 0; breadth median ≥ 5 names/side; positive
   honest-window Sharpe in at least 2 of the 3 regime classes (bull/bear/chop).

## 7. Falsifier (pre-registered — this kills the family)

Over the honest window [T0, 2024-06-30]: if the core retail-fade signal (`ls_accounts`,
every W ∈ {45,90,135,180} × E ∈ {1,3,6,12} × both XS transforms) has net Sharpe ≤ 0 at 1×
costs in EVERY configuration, AND the smart-dumb spread is likewise ≤ 0 across its W grid,
the family is falsified → report plainly, ask orchestrator (pivot or honest DNF).
Secondary kill: if positive-Sharpe configs exist but NONE has 2×-stress Sharpe ≥ 0, the
edge is a cost mirage → same outcome. Structural kill: if coverage never supports the
breadth floor (median ≥5/side unreachable), the family is untestable on this substrate.

## 8. Cost & stress plan

Every candidate is scored at 1× (official) and 2× (cost AND slip doubled) via
`net_series(..., cost_mult=2.0, slip_mult=2.0)`. Turnover and total_cost from
`evaluate()` are reported for the chosen config. Funding attribution (`total_funding_pnl`)
is reported to verify the claimed funding-tailwind property.

## 9. Experiment ledger plan

e01 coverage → e02 core baseline → e03 W sweep → e04 E sweep → e05 XS transform →
e06 panel swaps (fade sign) → e07 smart-dumb spread → e08 combo (only if §6.3 allows) →
e09 chosen-config stress + regime + funding attribution → e10 robustness (min_periods ±,
clip {2,4}, T0 ± 30d start shift, IS first-half vs second-half consistency). Each logged via
`cli.py log-experiment` BEFORE reading its result.

## 10. QE SPEC — FINAL (frozen after e01–e10; selected by the §6 rule)

**One signal, no alternatives, every parameter fixed.** Numbers cited in is_report.md must
come from `team-run` output only.

### 10.1 Interface

`build_raw_weights(pn, aux) -> pd.DataFrame` — index = the panel grid (same index as
`pn["open"]` / all aux panels), columns derived at runtime from `aux["ls_accounts"].columns`
(never hard-coded; widening-safe). NaN cells = flat. The engine owns eligibility masking,
normalization, caps, the decision lag, costs, funding, and vol-targeting — emit the raw
signal as weights, nothing else. Uses ONLY `aux["ls_accounts"]` and `aux["eligibility"]`
(klines untouched). Deterministic, no randomness (`aux["seed"]` unused).

### 10.2 Exact pipeline (pandas semantics load-bearing — replicate calls verbatim)

Fixed parameters: `PANEL="ls_accounts"`, `W=90`, `MIN_PERIODS=45`, `CLIP=3.0`,
`EMA_SPAN=3`, XS transform = centered cross-sectional rank.

```python
R = aux["ls_accounts"]                       # 8h sums of 5-min ratio snapshots
E = aux["eligibility"]                       # bool panel, same grid (organizer, past-only)
x = np.log(R.where(R > 0.0))                 # zeros/negatives -> NaN (e01: 2022 zero plague)
mu = x.rolling(90, min_periods=45).mean()    # current bar INCLUDED (same-bar convention)
sd = x.rolling(90, min_periods=45).std()
z = ((x - mu) / sd.where(sd > 0.0)).clip(-3.0, 3.0)
s = -z                                       # FADE the per-coin positioning extreme
s = s.ewm(span=3, min_periods=1).mean().where(s.notna())
#   ^ pandas defaults: adjust=True, ignore_na=False; the trailing .where(s.notna())
#     re-masks bars whose raw signal is NaN (EMA must not invent values there)
avail = s.where(E)                           # rank only eligible AND non-NaN names
r = avail.rank(axis=1)                       # pandas defaults: ascending, ties -> average
n = avail.notna().sum(axis=1)
w = r.sub((n + 1) / 2.0, axis=0).div(n.where(n > 1), axis=0)   # centered rank in [-0.5, 0.5]
return w
```

Causality notes for the harness/tests: `rolling` and `ewm(adjust=True)` are strictly
trailing; `rank` is per-row; aux row t is same-bar info usable at t (charter §5) — the
engine applies the `.shift(1)`. Future-corruption of `ls_accounts`/`eligibility` rows > t
must leave weights ≤ t unchanged (EMA/rolling guarantee this; team test must assert it).
Pre-2023 the book is structurally flat (NaN coverage) — expected, not a bug.

### 10.3 Frozen expectations (scratch-evaluator values; QE re-derives via team-run)

1× Sharpe ≈ 1.18 (official window) / ≈ 1.60 (honest window 2023-01-13+); 2×-stress ≈ 0.74;
maxDD ≈ −0.33; ann. turnover ≈ 94; median names ≈ 20 long / 20 short; total funding P&L
positive. If team-run departs materially from these (beyond float noise), STOP and debug
the pipeline against §10.2 — do not re-tune.

## 11. Results addendum (running, dated)

### 11.1 e01 coverage finding (2026-07-18) — DATA AMENDMENT to §2/§4

The ratio panels are 8h SUMS of Binance 5-min metric snapshots (values ≈ 96 × mean ratio).
Coverage structure found:
- 2020-09 → 2021-11: exactly ONE eligible name (BTC) has data — cross-sectionally useless.
- Dec-2021: brief 39-name island; **2022-01 → 2022-12: 85–100% of eligible cells are exact
  ZEROS in most months** (missing 5-min archive rows summed to 0; partial sums smear the
  rest). Both panels are zero at the same bars, so ratio-of-sums salvage fails (spread
  coverage 0 in 2022). 2022 is DEAD for every variant of this family.
- 2022-12 (mid) → 2024-06: clean, full 40-name coverage, sane values.

**Honest window per the §2 pre-registered rule: T0 = 2023-01-13 → 2024-06-30**
(~17.6 months). Consequences, stated plainly:
- The 2022-bear expectation in §4 is UNTESTABLE on this substrate; testable regimes are
  FTX-aftermath chop, ETF bull, post-halving chop (bull + 2× chop, bear n/a).
- The official full-IS Sharpe includes ~36 structurally flat months; expected dilution
  factor vs honest-window Sharpe ≈ √(18/54) ≈ 0.58. Accepted and reported, not hidden.
- The falsifier (§7) operates on [2023-01-13, 2024-06-30] as pre-registered.

### 11.2 e02–e10 results & selection (2026-07-18) — FALSIFIER NOT FIRED

All numbers below are scratch-evaluator values (same engine code path as team-run); the
canonical citations for is_report.md will come from `team-run` output.

- **Core retail-fade works across the whole plateau.** W×E grid (ls_accounts, demean):
  {45,90}×{1,3,6} all official-1× ≥ 1.0, honest-window ≥ 1.3; W∈{135,180} weaker but
  positive (hw ≈ 1.1). No sign flips anywhere → §7 primary falsifier not fired. 2×-stress
  positive in every plateau cell (0.47–0.79) → cost-mirage kill not fired.
- **Selection per §6.2** (plateau ≥ 0.8×max = cells {45,90}×{1,3,6}): median W tie →
  lower-turnover tie-break → W=90; median E=3. Transform: rank beats demean on the locked
  Stage-1 metric (1× 1.176 vs 1.116; demean better at 2×: 0.792 vs 0.744 — both pass the
  stress>0 gate); rank also gives balanced 20/20 breadth and is defensively preferable
  given this data source's proven pathologies. **Final: (ls_accounts, W=90, E=3, rank).**
  Note: W45E3-rank had a higher point Sharpe (1.23/1.66) — plateau-center rule prevails
  over the peak, as pre-registered.
- **Panel swaps (e06), fade sign only:** tt_ls_accounts +0.98 (weaker cousin, not used);
  tt_ls_positions −0.56 (smart book must not be faded — consistent with mechanism);
  taker_ls_vol −1.36 (dropped; follow-sign belongs to team-05's family — not flipped).
- **Spread & combos (e07/e08) rejected by the §6.3 gate:** smart-dumb spread standalone
  positive but weaker (hw ≤ 1.17) and loses the funding tailwind (funding P&L −0.02 vs
  +0.07); neither combo beats the single core on both cost tiers.
- **Validation (e09):** plateau neighbors of the final config all positive (1.23 / 0.69 /
  1.01 / 0.96). Honest-window months 12/18 positive. Attribution: price P&L +0.69,
  funding +0.067, cost −0.236 (pre-vol-target units) — funding-tailwind claim confirmed.
- **REGIME CONCENTRATION (honesty flag):** honest-window Sharpe splits bull 4.23 (6
  months) vs chop 0.52 (14 months); H1-2023 (FTX-aftermath chop) is +0.41 @1× but
  **−0.51 @2×**, H2 (ETF bull + post-halving) +2.92/+2.13. The edge is materially
  bull/participation-concentrated on the short honest window; §4's bear expectation is
  untestable (2022 data dead). §6.4 gate passes on the two available regime classes.
  Interpretation (not a claim): positioning signals carry more information when retail
  participation is high; 2023-H1 was the post-FTX participation trough.
- **Robustness (e10):** min_periods {30,45,60} → 1.34/1.18/0.94 all-positive (kept the
  pre-fixed 45); clip {2,3,4} near-invariant under rank (1.20/1.18/1.17); extra 1-candle
  lag degrades to 0.87 @1× but stays positive — slow structure, not timing luck.
- Ledger: 10 of 40 experiments used (e01–e10).
