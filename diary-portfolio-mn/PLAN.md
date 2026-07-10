# MN Track — PLAN.md (track-opening, 2026-07-10)

**Track:** baseline-blind MARKET-NEUTRAL portfolio (MN). Charter: `ORCHESTRATOR_BRIEF_MN.md`
(binding, read in full). Predecessor methodology: `diary-portfolio-blind/TRACK-CONCLUSION-2026-07-10.md`
(read for METHODOLOGY only). Infrastructure inspected: `analysis/portfolio/blind_engine.py`,
`blind_universe.py`, `blind_funding.py`, `blind_paper_l1.py` (recompute architecture),
`blind_regime.py` / `blind_mania_rule.py` (market-only bucket-rule discipline),
`tests/test_blind_engine.py` (55-test leak/parity suite), `src/crypto_trade/main.py` (`fetch-oi`).

**NOT read, per blinding:** `BASELINE_PORTFOLIO.md`, `analysis/portfolio/iter_*.py`,
`diary-portfolio-top20/`, `CONFIRMATION-005.md`, sibling worktrees. The vol_low / mid-vol
cross-sectional family is CLOSED — nothing below reuses it as a signal. Lead-lag diffusion and
low-beta/BAB tilts are excluded per charter.

**Status of this document:** pre-registration. Every kill criterion, grid, threshold, and bucket
rule below is FROZEN as of this commit, before any diagnostic script runs. Amendments require a
dated `PLAN-AMENDMENT-NNN` section appended (never edited in place) and are allowed only BEFORE
the affected diagnostic is scored.

---

## 1. Mission + neutrality doctrine

### 1.1 What "market-neutral, all-conditions" means operationally

The predecessor's books were **dollar-neutral with realized crash/mania beta** — sum(w)=0 on
paper, long-beta in practice, so crashes set the P&L. That is the failure mode this track exists
to engineer away. Operationally:

1. **Beta-neutral, measured, not assumed.** Neutrality is a property of the REALIZED return
   stream, verified by regression against BTC and ETH — never inferred from sum(w)=0 or from the
   construction ("we hedged, therefore we're neutral" is banned). Every book reports rolling and
   bucket-conditional realized betas as first-class metrics next to Sharpe.
2. **Bounded net exposure at every rebal**, including hedge legs.
3. **Per-regime-bucket evaluation from day one.** Every diagnostic and every backtest reports its
   core metric split by market-rule-defined crash / mania / chop buckets. A book that earns its
   whole Sharpe in one bucket is a regime bet wearing a neutral costume.
4. **The counterparty must exist in all regimes.** Each construction must articulate WHO pays us
   in crash, in mania, and in chop — if the mechanism's payer disappears in one regime, that is a
   disclosed structural hole, not a surprise.

### 1.2 Regime buckets (FROZEN market rules — no strategy inputs, ever)

Inherited discipline from the old track (blind_mania_rule.py lesson): bucket rules must be
market-only and frozen a-priori; membership must never track strategy P&L. For this track the
rules are deliberately simpler than the old C1 gate (which was gate-anchored):

- **CRASH:** trailing 90-candle (30d) BTC close-to-close return ≤ −15%.
- **MANIA:** trailing 90-candle BTC return ≥ +25%.
- **CHOP:** everything else.

Asymmetric thresholds because BTC drifts up over the IS window; both are round numbers chosen
a-priori, not fitted. Trailing windows only, so the same rule is live-computable. **Occupancy
sanity check** (run once, before DIAG-A is scored): each bucket must cover ≥5% of IS candles.
If it fails, ONE re-registration of thresholds is permitted via PLAN-AMENDMENT-001, before any
diagnostic result is looked at. After that the rules are immutable for the track's lifetime.

### 1.3 THE NEUTRALITY GATE (every construction is held to this)

Applied on IS at EXPLORATION (phase-agnostic mean where cadence > 1 candle), re-applied verbatim
on the holdout at CONFIRMATION and on forward paper-trade. All betas are OLS of the book's net
return stream on BTC (and ETH) 8h returns.

| # | Gate | Bound | Kind |
|---|------|-------|------|
| G1a | Rolling 270-candle (90d) β vs BTC | abs ≤ 0.10 on ≥95% of post-warmup candles; max abs ≤ 0.20 | HARD |
| G1b | Rolling 270-candle β vs ETH | abs ≤ 0.15 on ≥95%; max abs ≤ 0.25 | HARD |
| G2 | Bucket-conditional β vs BTC, CRASH bucket and MANIA bucket separately | abs ≤ 0.15 each | HARD |
| G3 | Net exposure at every rebal, post-hedge, hedge legs included | abs(Σw) ≤ 0.10 × gross | HARD |
| G4 | Worst-bucket performance | worst bucket's mean net return t-stat > −1.0 | HARD |
| G5 | Bucket P&L concentration | no bucket > 60% of total P&L | SOFT (report + Critic discussion) |

G2 is the anti-predecessor gate: it is exactly the axis on which dollar-neutrality failed.
G4 operationalizes "all-conditions": we do not demand positive Sharpe in every bucket at
EXPLORATION (sample sizes in CRASH are small), but a book SIGNIFICANTLY losing in any bucket
fails. G5 is soft because a carry book legitimately earns more in chop; it exists to force the
discussion, not to auto-kill.

Any G-hard failure ⇒ the construction does not proceed to CONFIRMATION, regardless of Sharpe.

---

## 2. Construction sketches

Five sketches: A–D from the charter menu, E′ merges menu item E with this plan's single new
angle (beta-residualization + a full horizon×sign map, rather than a point bet on one horizon).
Menu item F (dispersion-conditional gross scaling) is deferred by charter design ("later") — it
is a meta-layer on top of whatever survives, not a construction.

Common conventions for all sketches:
- **Universe:** PIT top-40 by trailing 30-candle mean $-volume, ex-stablecoins, ≥90d history
  (via `pit_topn_universe`, N=40). Primary view top-40 (an MN cross-section needs breadth);
  top-20 reported as a robustness column. Both pre-registered here — no other N will be tried
  at diagnostic stage.
- **Residual return** r̃_i = r_i − β_i·r_BTC with β_i a rolling 270-candle past-only OLS beta,
  shrunk toward the cross-sectional mean (λ=0.33), min_periods=135, clipped to [0, 3]. All IC
  probes below use residual returns so the measured edge is the MN-compatible component.
- **Costs:** taker 5bps + slip 2.5bps per side on every leg (hedge legs included), funding on
  every perp leg, 2×-cost twin always. Diagnostics that report spreads must report cost coverage
  at the construction's natural cadence — an IC with no cost-coverage line is not a result.
- **IS only:** 2020-01-01 → 2025-12-31. Every diagnostic also reports its headline metric
  EXCLUDING the 2025-03→2025-12 sub-window (contamination disclosure, §5).

### Sketch A — Funding-carry beta-neutral basket (menu A)

**Mechanism — who pays us, in all regimes:** funding is the perp's price-anchoring tax on the
crowded side. Leveraged directional traders — predominantly retail — pay it for leverage access
in BOTH directions: in mania the crowded longs pay (we are short the extreme-positive-funding
names, collecting), in crash panic the crowded shorts pay (funding flips negative on panicked
names, we are long them, collecting). The CROSS-SECTIONAL form (long low/negative-funding vs
short high-funding, beta-hedged) isolates RELATIVE crowding and is insensitive to the aggregate
funding level — the payer exists in every regime because leverage demand never goes to zero, it
just migrates. Secondary mechanism: extreme funding marks positioning crowding that
mean-reverts (BIS WP 1087: carry shocks precede liquidation waves — the price leg of the
unwinding pays the fader). Known risks: funding cross-section concentration in meme perps
(liquidity floor + per-name cap needed at construction stage), and chop-regime compression of
the funding spread (G5 will surface it).

**Data:** READY. Funding CSVs for 779 symbols (BTC from 2019-09); `blind_funding.load_funding`
is bucket-sum exact for any settlement cadence; `assert_funding_coverage` guards silent-zero.
8h panel ready.

**Frequency:** 8h native (funding settles on the 8h grid for most names; the loader handles
4h/1h-settling names exactly). Candidate rebal cadences: every candle with weight banding, daily
(rebal=3), weekly (rebal=21) — the diagnostic's persistence measurement decides which are viable;
weekly and daily REQUIRE the phase sweep (§5). Sample: ~6,570 IS candles × 40 names.

**Diagnostic DIAG-A (IS-only, <1 day, no engine required):**
1. *Persistence:* per-name and pooled autocorrelation of 8h funding at lags 1–90; half-life of
   the funding z-score. Carry is harvestable only if the sort outlives the 1-candle decision lag.
2. *Decile capture:* sort by trailing 9-candle (3d) mean funding z; D1−D10 spread of next-candle
   TOTAL residual return (price + funding), decomposed into funding component vs price component
   (the giveback), split by regime bucket.
3. *Cost coverage:* implied one-way turnover of the sort at rebal ∈ {1, 3, 21}; net spread after
   costs at each cadence, and under the 2×-cost twin.

**Kill criterion (pre-registered):** KILL sketch A if ANY of:
(a) net-of-cost D1−D10 residual total-return spread ≤ 0 annualized at BOTH rebal=3 and rebal=21;
(b) price-leg giveback ≥ 100% of funding collected on full-IS aggregate (carry fully arbitraged);
(c) CRASH-bucket mean spread return < 0 with t < −2 — the mechanism predicts carry WINS in
crashes (short the crowded longs); a significant crash loss falsifies the mechanism itself, not
just the parameters.

### Sketch B — Cointegration pairs/basket stat-arb at 1h (menu B)

**Mechanism:** related perps (shared sector, shared holder base, shared market-maker inventory)
are pushed apart by idiosyncratic liquidity shocks — single-name liquidation cascades, listing
hype, narrative rotation — and relative-value correction pays the provider of that liquidity.
The payer is the noise trader / forced liquidator demanding immediacy in ONE name of a
cointegrated set. Regime-symmetric: relative dislocations occur in bull and bear alike, and the
spread position is beta-neutral by construction (hedge ratio from the cointegrating vector,
verified by G1/G2 regardless). The known killer is STRUCTURAL BREAKS — narratives decouple pairs
permanently; per charter, the kill-switch design IS the research content of this sketch.

**Data:** NEEDS 1h fetch (worktree has 8h only). ~top-40 names, 2020→now (§4.3). 8h gives too
few observations per formation window for half-lives of hours.

**Frequency:** 1h. Cost reality check drives the design: a pair round-trip is 4 crossings
(2 legs × entry+exit) ≈ 30bps + funding, so tradeable spreads must open ≥ 2σ with σ_spread big
enough that 2σ→0 convergence clears ~45bps (1.5× margin). The diagnostic measures whether such
spreads exist at all.

**Diagnostic DIAG-B (IS-only, ~1 day once 1h data lands):**
1. *Census:* top-30 by IS mean $-vol → 435 pairs; rolling 90d formation windows stepped
   quarterly through IS; Engle-Granger ADF p<0.05 AND OU half-life ∈ [6h, 7d] ⇒ "qualifying".
2. *Persistence (the killer, measured directly):* of pairs qualifying in window w, the fraction
   still qualifying in w+1, vs the unconditional base rate.
3. *Walk-forward convergence:* enter |z|>2 / exit z=0 / hard stop |z|>4 in the window AFTER
   formation, 4-crossing costs + funding on both legs; P&L per trade, by regime bucket.

**Kill criterion:** KILL sketch B if ANY of: (a) persistence ≤ 1.5× base rate (cointegration is
window noise); (b) walk-forward post-cost convergence P&L ≤ 0; (c) median qualifying-pair count
per window < 8 (a basket cannot be diversified — single-pair books die by structural break).

### Sketch C — OI/leverage-crowding fade (menu C)

**Mechanism:** when open interest builds rapidly WITH extreme funding AND one-sided taker flow,
the marginal trader on the crowded side is late, leveraged, and clustered — liquidation prices
stack. The forward distribution is asymmetric against the crowd (cascade risk), so fading the
crowded side cross-sectionally collects a cascade-risk premium from late momentum entrants.
Regime-symmetric by construction: in mania the crowded side is long (we fade short), in crash
capitulation the crowded side is short (we fade long); the payer — the late leveraged entrant —
exists in every regime. Per charter: standalone cascade alpha is cost-marginal, so the edge must
come from the CROSS-SECTIONAL portfolio form (many small fades, beta-hedged), not event sniping.

**Data:** GATED on fetch-oi backfill. `fetch-oi` exists (`main.py`, iter-v3/093): daily
metrics ZIPs from data.binance.vision, 5-min granularity resampled to 8h, schema includes
`sum_open_interest`, `sum_open_interest_value`, top-trader and global long/short ratios, taker
L/S vol ratio — richer than raw OI. Cache (`data/open_interest/`) is currently EMPTY except two
empty dirs. Backfill scope specced in §4.2. The docstring claims BTC coverage from 2020-09-01;
treat as a claim the QE verifies empirically — archive start dates bound the usable IS window
for this sketch and must be reported per symbol.

**Frequency:** 8h native (matches the resampled cache; 5-min granularity remains available for
a later intraday refinement if the 8h form survives).

**Diagnostic DIAG-C (IS-only, <1 day once backfill lands):**
1. *Crowding score:* c = rank-sum of { z(ΔOI, 90-candle), funding-extremity z, taker-imbalance
   z } with signs aligned so high c = crowded-LONG. The exact composition (rank-sum, the three
   inputs, the windows) is FROZEN here — the diagnostic script implements this and nothing else.
2. *IC:* Spearman IC of c vs next 1/3/9-candle residual return (mechanism predicts NEGATIVE IC —
   fade the crowd), by regime bucket, both IS halves (2020-22 / 2023-25).
3. *Event study:* top-decile |c| events; forward residual return path 1–30 candles; event
   rate/month; implied cost coverage at the best horizon.

**Kill criterion:** KILL sketch C if ANY of: (a) |IC| < 0.02 at ALL of the three horizons;
(b) event-study forward move at the best horizon < 2× round-trip cost; (c) event rate < 5/month
(book cannot be diversified); (d) IC sign flips between IS halves at the best horizon.

### Sketch D — Taker-flow cross-section (menu D)

**Mechanism:** `taker_buy_volume / volume` measures which side is paying the spread + impact —
aggression. At short horizons, aggressive flow is either informed (continuation) or uninformed
retail chasing (reversal once impact decays); either way there is a harvestable premium on the
other side of impatience: the payer is the taker who crossed the spread. The 8h cross-section of
taker-imbalance is genuinely untouched in this repo's portfolio work (charter: "already in the
panel, never used by the old track"), and the sign (momentum vs reversal, per horizon) is an
empirical question the diagnostic answers rather than assumes.

**Data:** READY — `taker_buy_volume` is a first-class panel column.

**Frequency:** 8h first (free); 1h extension only if the 8h map shows the signal decaying inside
one candle (then it rides the §4.3 fetch).

**Diagnostic DIAG-D (IS-only, <1 day):**
1. TI = taker_buy/volume z-scored per name over trailing 90 candles; Spearman IC of TI-z
   aggregated over lookbacks {1, 3, 9, 21, 63} candles vs forward {1, 3} candle residual
   returns — a 5×2 pre-registered grid, counted as 10 trials in the family's n_eff ledger.
2. Sign map by horizon + regime buckets + IS halves.
3. Decile spread with implied turnover and cost coverage at rebal 1 and 3 for the best cell.

**Kill criterion:** KILL sketch D if ANY of: (a) max |IC| < 0.015 over the grid; (b) the best
cell's decile spread fails 2×-cost coverage at its natural cadence; (c) best-cell IC sign flips
between IS halves.

### Sketch E′ — Residualized past-return horizon map (menu E + this plan's one new angle)

**New angle (the only one, per charter):** instead of menu E's point bet ("short-horizon
reversal at 1h–4h"), residualize returns against beta FIRST and map the ENTIRE horizon×sign
structure of the residual cross-section — from 1h reversal to multi-week idiosyncratic momentum
— in one pre-registered pass. Rationale: raw cross-sectional past-return sorts in crypto are
beta bets in disguise (high-beta names top every raw momentum sort in manias — exactly what G2
exists to kill); the residual component is the only MN-compatible part. In equities, residual
momentum carries higher Sharpe with far smaller crashes than raw momentum (Blitz, Huij &
Martens, 2011, J. Empirical Finance) — crypto's retail herding gives the prior a
mechanism: underreaction/herding in SINGLE names, net of the market factor.

**Mechanism:** short end — the payer is the impatient liquidity demander whose single-name
impact mean-reverts (liquidity-provision premium, regime-agnostic because forced flow happens in
all regimes). Long end — the payer is the herding retail chaser who underreacts to
name-specific developments (listings, unlocks, narratives) and corrects slowly. Both ends are
idiosyncratic by construction after residualization, so neutrality is structural and G1/G2
verify it.

**Data:** Stage 1 (8h) READY; Stage 2 (1h) rides the §4.3 fetch. The old track's 8h finding
("reversal long-side-only") is from the CLOSED family and is BANNED as a design input — the map
is measured fresh, neutralized.

**Frequency:** stage-dependent. Stage-2 candidates at 1h face the same cost wall as B — 15bps
round-trip per unit turnover means only cells with forward moves ≥ ~30bps net of beta survive;
the map reports cost coverage per cell.

**Diagnostic DIAG-E (two stages, each <1 day, IS-only):**
- Stage 1 (8h): IC of trailing residual return over lookbacks {3, 9, 21, 63, 189} candles vs
  forward {1, 3, 9, 21} candles — a 5×4 grid (20 trials in the ledger), by regime bucket and IS
  halves; decile-spread cost coverage for the best momentum cell and best reversal cell.
- Stage 2 (1h): lookbacks {4h, 12h, 24h, 48h} vs forward {1h, 4h, 12h, 24h} (16 trials),
  same reporting.

**Kill criterion (per stage, independently):** KILL the stage if no cell has |IC| ≥ 0.02 with
same-sign stability across IS halves AND 2×-cost coverage at the cell's natural cadence.
Stage-1 death does not kill Stage 2 (different microstructure), but both dead ⇒ sketch dead.

---

## 3. Diagnostic order

Ranking rule: prior strength × data readiness × falsification cheapness.

| Order | Diagnostic | Why here |
|-------|-----------|----------|
| 1 | **DIAG-A** (funding-carry) | Data 100% ready; strongest prior (a paid-in-all-regimes structural flow, industry MN books demonstrably run it); probe is half a day; also forces the residualization harness (rolling betas) to be built and validated first — the same harness every later diagnostic and the beta-hedge builder reuse. |
| 2 | **DIAG-D** (taker-flow) | Data already in the panel and never used; reuses the DIAG-A harness verbatim; second-cheapest falsification. |
| 3 | **DIAG-E Stage 1** (residual horizon map, 8h) | Data ready, harness shared; the map also produces the residual-return infrastructure DIAG-C consumes. |
| 4 | **DIAG-C** (OI-crowding) | GATED on the fetch-oi backfill (§4.2) — QE task dispatched at track open, runs in parallel with diagnostics 1–3; DIAG-C is scored when the backfill completeness report is in. |
| 5 | **DIAG-B** (cointegration pairs) + **DIAG-E Stage 2** | Both gated on the 1h fetch (§4.3); B is last because it is the most research-heavy per unit of falsification (the kill-switch design only matters if the census + persistence probe survives). |

Parallelism: the two QE data tasks (§4.2, §4.3) start immediately so the gates are open by the
time diagnostics 1–3 are scored. No diagnostic result influences whether the data tasks run.

---

## 4. Track infrastructure asks for the QE (specs — do not implement in this plan)

### 4.1 Beta-hedge overlay in the engine (the load-bearing ask)

**Chosen semantics: explicit BTC/ETH HEDGE-LEG OVERLAY, not cross-sectional beta-neutralization
of the alt weights.** Justification, on the record:

1. *Signal preservation:* an overlay leaves the alpha weights untouched, so alpha-book vs
   hedge-book attribution stays separable (the engine's `funding_rets` split already supports
   per-leg attribution; hedge P&L must be equally separable).
2. *Cost efficiency:* the hedge trades the two most liquid perps on the venue; cross-sectional
   re-weighting smears hedge turnover across 40 less-liquid names at worse realized slippage.
3. *Conditioning:* per-name betas to BTC and to ETH are heavily collinear across alts; a
   two-factor per-name weight projection is ill-conditioned and churns window-to-window. One
   aggregate book-beta per factor is a single well-estimated number.
4. *Auditability:* the hedge notional is an explicit reported time series; the neutrality gate
   then MEASURES realized book beta including the hedge — measured, never assumed (charter §7).

**Mechanics to implement:**
- `analysis/portfolio/mn_beta.py`: `rolling_beta(panel, ref="BTCUSDT", window=270,
  min_periods=135, shrink_lambda=0.33, clip=(0.0, 3.0))` → (T, C) past-only per-name betas from
  8h close-to-close returns; consumed at the standard `[k-1]` decision lag.
- `blind_engine.run_backtest(..., hedge_overlay=...)` opt-in extension: at each rebal, after
  `w_tgt` is built, compute book beta b = Σ w_i·β_i[k−1] and set the BTC hedge leg to −b
  (β_BTC,BTC ≡ 1). ETH leg: OFF by default; auto-armed per the pre-registered trigger — when the
  trailing 270-candle realized β_ETH of the BTC-hedged book exceeds 0.10 in absolute value, add
  an ETH leg sized against a rolling ETH-residual beta. Hedge legs pay taker+slip on turnover
  and funding like any weight — no free hedge. Alpha gross target unchanged; total gross and net
  exposure reported INCLUDING hedge legs (G3 measures the post-hedge book).
- Result plumbing: `hedge_weights` (T, 2) and hedge-leg P&L/funding series in `BacktestResult`.

**Leak tests required (extend the 55-test suite, same house style):**
- inert-default byte-identity: `hedge_overlay=None` reproduces every existing mode bit-for-bit;
- corrupt-future positive control on `rolling_beta` (the blind_regime.py test-5 pattern):
  corrupting `close[t:, :]` leaves `beta[:t]` bit-identical;
- decision-lag test: hedge sizing at rebal k uses only data ≤ close[k−1];
- cost accounting: hedge-leg turnover is charged, funding applied, and appears in `turnover`;
- NaN-beta handling: names with <135 candles of history get the shrinkage prior (cross-sectional
  mean), never silent zero and never silent exclusion — logged count per rebal.

### 4.2 fetch-oi backfill (gates DIAG-C)

- Scope: the union of all names EVER in the PIT top-60 by trailing $-vol over IS, plus BTCUSDT
  and ETHUSDT (top-60 not top-40: universe churn means today's top-40 is not 2021's; the union
  is the point-in-time-safe superset). QE emits the symbol list from `pit_topn_universe` (N=60)
  before fetching.
- Range: earliest archive date per symbol → now. **Verify the actual archive start empirically**
  (the `fetch-oi` docstring claims BTC from 2020-09-01 — treat as unverified) and report the
  per-symbol usable start date; DIAG-C's effective IS window is bounded by it and must be
  disclosed in the diagnostic.
- Deliverable: `data/open_interest/<SYM>/8h.csv` + a completeness report (days fetched vs days
  expected per symbol, gap list — the panel-starvation lesson demands a loud report, charter §4).
- Leak note carried from the resampler docstring: cached bar T aggregates bar-T's own 5-min
  rows, so ALL consumers must `.shift(1)` before feature construction. The DIAG-C script asserts
  this convention; a unit test pins it.

### 4.3 1h kline fetch (gates DIAG-B and DIAG-E Stage 2)

- Scope: union of PIT top-40 members over IS (same union logic as §4.2, N=40), via
  `bulk --intervals 1h` + `--api-backfill` for the current month; 2020-01-01 → now.
- Loader: extend `blind_universe.load_panel` with an `interval` parameter (currently hardcoded
  `8h.csv`) as `mn` namespace usage; same BTC-grid alignment on the 1h grid.
- Completeness guard: per-symbol row count vs expected grid length, loud gap report BEFORE any
  1h diagnostic runs (charter §4 — the starvation bug class).
- Leak tests: grid-alignment test on 1h (no forward-fill across gaps into the future), and
  panel-parity spot check 1h→8h aggregation vs the 8h panel for 3 symbols.

### 4.4 New IS/HOLDOUT split module (blocks EVERYTHING — first QE task)

- `analysis/portfolio/mn_split.py`: `IS_END_MS = 2026-01-01 00:00 UTC`; `mn_is_mask(panel)`
  analogous to `blind_universe.is_mask` but on the NEW boundary. **Do not reuse
  `blind_universe.is_mask`** — its `OOS_CUTOFF = 2025-03-24` is the OLD track's split.
- Sealed-holdout guard: a `_guard_window`-style assertion (pattern exists in
  `blind_paper_l1.py`) that raises if any mn_* script computes or prints a metric overlapping
  2026-01-01→now outside a sanctioned CONFIRMATION reveal. Every diagnostic script imports it.

### 4.5 Regime bucket module

- `analysis/portfolio/mn_regimes.py`: the §1.2 rules exactly (90-candle trailing BTC return,
  −15% / +25%), returning a (T,) label array + an occupancy report function. Unit test: the
  function signature takes ONLY market data (panel), no strategy artifacts — enforced by test.

---

## 5. Anti-leak protocol (concrete, this track)

1. **Pre-registration timing.** This PLAN freezes: bucket rules, neutrality gate bounds, all
   five diagnostic designs, their grids (trial counts: A≈3 cadence cells, C=3 horizons, D=10
   cells, E1=20, E2=16 — the family n_eff ledger starts at these numbers), and all kill
   criteria — BEFORE any diagnostic code runs. Each EXPLORATION (post-diagnostic) gets its own
   brief pre-registering construction params, falsification arms, and a frozen decision map
   BEFORE its backtest; adversarial Critic pre-flight before the run and review after
   (predecessor evidence: this combination caught every major error — TRACK-CONCLUSION §3).
2. **IS/HOLDOUT.** IS = 2020-01-01→2025-12-31. HOLDOUT = 2026-01-01→present, SEALED, enforced
   in code (§4.4). **One holdout reveal per candidate FAMILY, ever** (family = mechanism family
   A/B/C/D/E′; a re-parameterization of a revealed family does NOT get a second reveal).
3. **Forward paper-trade is the final arbiter.** The recompute architecture exists and is
   reusable: `blind_paper_l1.py` — weekly full-panel recompute through the UNCHANGED engine with
   frozen params, append-invariance assertion (ABORT on mismatch), dual parity pins to committed
   IS numbers, tamper-evident weekly commits, `_guard_window` quarantine. An MN survivor gets an
   `mn_paper_*.py` clone of this pattern with its own parity pins; no exchange-order code.
4. **Contamination map (charter, carried verbatim):** "2020→2025-03 heavily mined by prior
   tracks (new mechanism families OK); 2025-03→2026-07 was REVEALED for the old vol_low-family
   books (BURNED-REVEAL-2026-07-10.md) — regime knowledge exists (2025-11→2026-07 was
   crash-heavy); new-family evaluation there is discounted, not forbidden." Operationally: every
   diagnostic and brief reports its headline with AND without the 2025-03→2025-12 IS sub-window;
   a result that only exists in the revealed sub-window is treated as discounted evidence.
5. **Phase sweeps mandatory.** Any rebal cadence > 1 candle reports the FULL phase-offset
   distribution; the headline is the phase-agnostic mean (or tranche ensemble); single-phase
   numbers are never load-bearing. (The predecessor's 21/21-positive-delta standard is the
   reference bar for claiming a cadence-level improvement.)
6. **Costs honest from candle one.** 5+2.5 bps per side on every leg including hedges, funding
   on every perp leg, 2×-cost twin on every backtest, trade-rate/sample floors sized to each
   construction's frequency (a 1h book needs proportionally more trades than an 8h book for the
   same evidential weight).
7. **No post-hoc re-gating, ever.** A kill criterion fires ⇒ the sketch dies as registered.
   Arguing with a fired criterion is a process violation, not a research move.

---

## 6. Cadence

- **Diagnostics: ~1 day each**, in the §3 order; data tasks (§4.2, §4.3) dispatched to the QE
  immediately and run in parallel. Diagnostic scripts live at `analysis/portfolio/mn_diag_*.py`,
  committed BEFORE their first scored run.
- **EXPLORATION only after a diagnostic survives its kill criterion.** An EXPLORATION is a full
  engine backtest of ONE construction with the neutrality gate applied, cheap and falsifiable;
  CONFIRMATION (holdout reveal) is rare — one per family, ever — and only after IS robustness
  (phase sweep, cost twin, regime buckets, seed/window stability as applicable) is documented.
- **No knob inheritance from dead sketches.** If a sketch dies, its lookbacks, thresholds, and
  universe tweaks die with it; any reuse in a live sketch requires explicit re-registration in
  that sketch's EXPLORATION brief (with the trial-count carried into n_eff).
- **All agents on Fable** (charter §3); briefs in `briefs-portfolio-mn/`, diary entries in
  `diary-portfolio-mn/`, one diary entry per diagnostic/exploration regardless of outcome —
  kills are documented with the same rigor as survivals.
- Deferred by design: menu item F (dispersion-conditional gross scaling) is revisited only when
  at least one construction has survived EXPLORATION — it scales gross on an existing book, so
  it needs a book first.
- Noted for later, not now: `fetch-spot` exists in `main.py` (the charter lists spot as
  unavailable — the command's actual coverage is unverified). If a future wave wants perp−spot
  basis constructions, the QE verifies spot fetchability first; NO sketch in this wave depends
  on it.

*— QR, MN track, 2026-07-10. This document is the pre-registration record; amendments only via
dated PLAN-AMENDMENT sections, never in-place edits.*
