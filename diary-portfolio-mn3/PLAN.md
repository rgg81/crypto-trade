# MN3 Track — PLAN.md (track-opening, 2026-07-11)

**Track:** baseline-blind MARKET-NEUTRAL portfolio, v3 — the TWO-YEAR-HOLDOUT restart.
Charter: `ORCHESTRATOR_BRIEF_MN3.md` (binding, read in full). Methodology sources read:
`diary-portfolio-mn/SURVEY-001-CLOSEOUT.md`, `diary-portfolio-mn/PHASE7-CONFIRMATION-A.md`,
`diary-portfolio-mn/PLAN.md` (format + lessons ONLY; its constructions are NOT templates),
`ORCHESTRATOR_BRIEF_MN.md` (superseded v2 charter). Infrastructure inspected:
`analysis/portfolio/{blind_engine,blind_universe,blind_funding,blind_paper_l1,mn_split,
mn_regimes,mn_beta,mn_scud,mn_datacheck}.py`, `tests/test_{blind_engine,mn_infra,
mn_exploration_a*,}.py` (102 tests), `diary-portfolio-mn/{OI-BACKFILL-REPORT,1H-FETCH-REPORT}.md`
(data-extent facts only).

**NOT read, per blinding:** `BASELINE_PORTFOLIO.md`, `analysis/portfolio/iter_*.py`,
`diary-portfolio-top20/`, `CONFIRMATION-005.md`, sibling worktrees. Closed-at-mechanism
families — vol_low, pairs-cointegration-persistence, taker-standalone, resid-mom-standalone,
OI-fade — are NOT reused as signals anywhere below.

**Status of this document: PRE-REGISTRATION.** Every indicator construction, threshold, state
rule, grid, kill criterion, and budget below is FROZEN as of this commit, before any MN3
diagnostic script exists or runs. Amendments only via dated `PLAN-AMENDMENT-NNN` sections
appended at the end (never in-place edits), and only BEFORE the affected artifact is scored.

---

## 1. Mission, lifecycle, splits, contamination

### 1.1 The methodology (user directive — verbatim-encoded lifecycle)

1. **Stage 1 — IS development:** diagnostics + explorations, pre-registered, IS-only.
2. **Stage 2 — the TWO-YEAR sealed holdout:** one reveal per family, ever, against a frozen
   decision map. **A model must GENERALIZE ACROSS TWO YEARS before anything else happens.**
3. **Stage 3 — six-month forward paper-trade** (recompute architecture; pre-registered gates).
4. **Stage 4 — live real money** (user decision; small size first).

**No stage may be skipped or shortened; failing any stage terminates the family (no rescue).**
The v2 lesson IS this charter: a 6-month holdout (n=572 candles, SE(Sharpe) ≈ 1.38) cannot even
contain the regimes needed to judge an all-weather book — CONFIRMATION-A's reveal window held
CRASH 28.5% / MANIA 0.0% and was structurally non-informative on edge. A 2-year window
(~2,193 candles, SE(Sharpe) ≈ 0.7 annualized) halves the noise AND — decisively — spans
multiple regime buckets, so "the earner bucket was absent" cannot recur as an excuse or as
a verdict-destroyer.

### 1.2 Splits (new; enforced in code before anything else runs)

- **IS = 2020-01-01 → 2024-06-30** (4.5 yr, ~4,929 8h candles). Contains COVID (2020-03),
  the 2021 mania + May-2021 crash, the 2021-12 flash crash, LUNA (2022-05), Celsius/3AC
  (2022-06), FTX (2022-11), the 2023 chop + 2023-08 deleveraging day, and the 2024-H1 mania.
  All regime buckets and four+ genuine crisis episodes are present — the IS is rich enough to
  both develop AND falsify the crisis machine without touching the holdout.
- **HOLDOUT = 2024-07-01 → 2026-06-30 (2 years), SEALED.** One family-token reveal, ever,
  per family (§6). Millisecond pins: `MN3_IS_CUTOFF_MS = 1719792000000` (2024-07-01 00:00 UTC),
  `MN3_HOLDOUT_END_MS = 1782864000000` (2026-07-01 00:00 UTC).
- **Data after 2026-06-30 accrues for Stage-3 paper trading.** It is neither IS nor holdout;
  no backtest metric is ever computed on it outside the Stage-3 recompute architecture.
- New split module `mn3_split.py` (§5.1). The v2 `mn_split` (cutoff 2026-01-01) and the old
  track's `blind_universe.is_mask` (2025-03-24) must be structurally unusable in mn3 code —
  distinct constant names, import bans enforced by test.

### 1.3 Contamination map — per family (disclosed here; reproduced in every MN3 brief §0)

No virgin 2-year window exists in this dataset. The holdout is sealed in the only sense
achievable: **never evaluated for the mechanism under test.** The map, per charter, refined
per family below. Windows: W1 = 2024-07→2025-03 (old-track IS tail + MN-v2 IS),
W2 = 2025-03→2025-12 (old-track REVEALED for vol_low books + MN-v2 IS),
W3 = 2026-01→2026-06 (MN-v2 REVEALED for funding-carry, A3-1).

| Family | W1 (24-07→25-03) | W2 (25-03→25-12) | W3 (26-01→26-06) | Net status |
|---|---|---|---|---|
| **G** ML residual alpha | univariate ICs of constituent feature classes (funding/taker/OI/resid-mom) were measured here as MN-v2 IS (DIAG-A/C/D/E1) | same + vol_low book P&L revealed (different, closed mechanism) | never evaluated | **Sealed-as-achievable.** Feature-class univariate-IC knowledge over W1–W2 is in-head and shaped the §3.1 feature list; disclosed. No G book has ever touched any of it. |
| **H** born-ensemble | as G, per sleeve | as G | never evaluated | **Sealed-as-achievable** with two flags: S1 (carry sleeve) inherits family-A signal knowledge; S2's continuation SIGN comes from MN-v2 DIAG-C measured over W1–W2. Disclosed. |
| **I** funding-carry v2 | **A-family parameter development window** (MN-v2 IS) | same | **FULLY REVEALED** — A3-1 book P&L, monthly attribution, funding/price decomposition all known (PHASE7-CONFIRMATION-A) | **Compromised end-to-end.** W1+W2 are parameter-contaminated; W3 is book-revealed. Family I CANNOT earn a clean Stage-2 pass on this holdout — flagged; §3.3 defines the discounted structure and shifts evidential weight to Stage 3. |
| **J** funding term-dynamics | funding AUTOCORRELATION/half-life stats (DIAG-A lags 1–90) measured here | same | funding-LEVEL book revealed (family I's, not J's) | **Mildly contaminated.** Persistence summary stats are known over W1–W2; the funding-MOMENTUM cross-sectional IC — J's object — was never measured anywhere. |
| **K** event-conditioned | unconditional 1h residual-reversal ICs (DIAG-E2) measured over MN-v2 IS incl. W1–W2 | same | never evaluated | **Mild-moderate.** Unconditional-IC knowledge exists; the event-CONDITIONED object was never measured. K's kill criterion (d) explicitly requires conditioning to beat the unconditional baseline, so the contamination is turned into a falsifier. |

**In-head contamination (QR self-disclosure, carried into every brief):** I have read
PHASE7-CONFIRMATION-A and therefore know A3-1's holdout behavior on W3 (funding leg
+8.75 bps/cd in crash windows, price-leg inversion in MANIA-free chop, SCUD 3/3 coincident).
I also hold regime-composition knowledge of the whole holdout: 2024-H2 chop/rally, 2025
trends, **2025-11→2026-06 crash-heavy, 2026-H1 MANIA-free**. Defenses, pre-registered:
(i) market-only regime bucketing (frozen rules, §5.3) so composition is scored mechanically,
never narratively; (ii) every Stage-2 decision map pre-commits its interpretation across
bucket compositions BEFORE the reveal (the CONFIRMATION-A map's proven design); (iii) all
thresholds below are coverage- or principle-anchored, never fitted to any revealed draw;
(iv) the crisis doctrine is falsified on IS episodes only — a book that merely survives
crashes but earns nothing still fails its holdout map on the edge read, so crash-hardening
cannot game the known crash-heavy holdout tail.

**Killed-at-mechanism families stay closed:** vol_low, pairs-persistence, taker-standalone,
resid-mom-standalone, OI-fade. Where a construction below walks NEAR a closed family
(H's S3 vol-structure sleeve vs vol_low; K vs resid-reversal-standalone), the distinction is
stated explicitly and the Critic pre-flight must ratify or kill it before any run.

### 1.4 Neutrality doctrine (inherited verbatim from MN v2 — it transferred OOS)

Beta-neutral, measured never assumed. The v2 §1.3 neutrality gate is inherited unchanged for
IS EXPLORATIONs (all OLS of book net returns on BTC/ETH 8h returns):

| # | Gate | Bound | Kind |
|---|------|-------|------|
| G1a | Rolling 270c β vs BTC | abs ≤ 0.10 on ≥95% of post-warmup candles; max abs ≤ 0.20 | HARD |
| G1b | Rolling 270c β vs ETH | abs ≤ 0.15 on ≥95%; max abs ≤ 0.25 | HARD |
| G2 | Bucket-conditional β vs BTC (CRASH and MANIA separately) | abs ≤ 0.15 each | HARD |
| G3 | Net exposure at every rebal, hedge/projection included | abs(Σw) ≤ 0.10 × gross | HARD |
| G4 | Worst-bucket mean net return | t > −1.0 | HARD |
| G5 | Bucket P&L concentration | no bucket > 60% of total P&L | SOFT |

Every construction must articulate WHO pays it in crash, mania, and chop (§3). Stage-2 maps
re-freeze holdout-scale neutrality bounds at CONFIRMATION-brief time (full-window OLS form,
CONFIRMATION-A precedent). Residualization harness: reuse `mn_beta.rolling_beta` as-is
(270c window, shrink λ=0.33, clip [0,3], min_periods 135 — all a-priori constants, leak-tested,
transferred OOS at ρ(w_proj, w_raw) = 0.976).

---

## 2. THE CRISIS MACHINE (shared infrastructure — every family integrates it from birth)

A three-state risk regime machine — **NORMAL / STRESS / CRISIS** — driven by PAST-ONLY
crypto-native indicators, pre-registered here once and consumed by every construction. It is
the charter's "the model is lost" doctrine made mechanical: no alt exposure survives a black
swan. **Calibration is coverage- and principle-anchored ONLY; the falsification harness never
computes a strategy return** (no Sharpe scans, ever — the machine is falsified against known
IS crisis episodes and a calm-period coverage budget, nothing else).

### 2.1 Indicator suite (exact constructions; all past-only; all on the 8h BTC-aligned grid)

Common conventions: indicator universe = PIT top-40 by trailing 30-candle mean dollar-volume,
ex-stablecoins, ≥90d history (`pit_topn_universe`, N=40 — the v2 convention); cross-sectional
indicators require ≥15 members with finite inputs, else the indicator is UNDEFINED at t and
its vote forward-fills (§2.5). Robust z convention:
`z[t] = (x[t] − median_270(x)) / (1.4826 · MAD_270(x))`, trailing 270 candles (90d),
min_periods = 135, clipped to ±8. Robust location/scale because crisis windows are exactly
where means and stds explode — a plain z de-sensitizes itself during the event it must detect.
min_periods = 135 (45d) makes COVID (IS candle ~215) scoreable. Vote grammar: each indicator
emits v ∈ {0 calm, 1 stress-grade, 2 crisis-grade} per candle.

**C1 — XVOL: cross-sectional realized-vol index z.**
Per-name RV_i[t] = std of 8h log returns over trailing 30 candles (min 20 finite);
V[t] = cross-sectional MEDIAN of RV_i over the indicator universe; z_XVOL[t] = robust z of V.
Votes: stress at z ≥ +2.0, crisis at z ≥ +3.0 (standard-normal 97.7th / 99.87th percentile
coverage anchors — the SCUD anchoring style, shifted rarer because this is insurance, not a
throttle). Median-of-names so one meme perp cannot fire a systemic indicator.

**C2 — CORR: median pairwise correlation spike ("correlation-to-one = systemic").**
Pairwise Pearson correlation of 8h returns over trailing 90 candles across the PIT top-20
(190 pairs; majors give the cleaner systemic read and cap compute); ρ̄[t] = median pairwise.
Votes on ABSOLUTE level: stress at ρ̄ ≥ 0.75, crisis at ρ̄ ≥ 0.85. Principle anchor, not
z-scored: correlation is bounded on [0,1] with intrinsic meaning, and a trailing z would go
numb during an extended systemic regime exactly when the vote must stay up. 0.75/0.85 are
a-priori round numbers on the natural scale ("three-quarters of the way to one" / "close to
one"); the falsification harness (§2.4) verifies their IS coverage and episode behavior.

**C3 — FUND: aggregate |funding| dislocation.**
F[t] = EQUAL-WEIGHT cross-sectional mean of |funding_i[t]| (bps/8h; `blind_funding` loader,
bucket-sum exact) over indicator-universe members with funding data; z_FUND[t] = robust z of F.
Votes: stress at z ≥ +2.0, crisis at z ≥ +3.0. Equal-weight, not dollar-weight: dollar
weighting concentrates in BTC/ETH whose funding is clamp-tame; dislocation lives in the breadth
of the cross-section. Disclosed limitation: per-name funding clamps (±0.75%/8h typical)
compress the extreme tail — C3 is a confirming indicator, never the sole trigger.

**C4 — GAP: BTC single-candle gap detector (the fast trigger).**
σ[t] = EWMA std of BTC 8h log returns, half-life 30 candles, computed on returns through t−1
(the shock candle never inflates its own denominator); g[t] = |r_BTC[t]| / σ[t].
Votes: stress at g ≥ 3 OR |r_BTC[t]| ≥ 7%; crisis at g ≥ 4 OR |r_BTC[t]| ≥ 10%.
The absolute floors are the vol-numbness guard: after a month of elevated σ (LUNA→FTX autumn),
a pure vol-relative detector under-fires; a 10% BTC candle in 8h is a systemic event
unconditionally. 4σ / 10% are principle anchors (fat-tail-aware "impossible under calm"
magnitudes), not fitted.

**C5 — BREADTH: breadth collapse.**
B[t] = fraction of indicator-universe members (finite trailing 9-candle return) with trailing
9-candle (3d) return < 0. Votes: stress at B ≥ 0.85, crisis at B ≥ 0.95. Absolute anchors on
a bounded [0,1] quantity with natural meaning (≥95% of the liquid universe down over 3 days =
synchronized liquidation, no rotation); a z of breadth is unstable when the trailing window is
itself a mania. Round numbers a-priori; coverage verified by harness.

### 2.2 State machine — transitions and hysteresis

Score at t: the vote vector (v1..v5). Triggers:
- **CRISIS-trigger:** (≥2 indicators at crisis-grade) OR (C4-GAP at crisis-grade alone).
  GAP is the single-sufficient fast path: a 4σ/10% BTC candle IS the event; the other four
  indicators use 30–90-candle windows and confirm rather than lead. Multi-indicator
  confirmation everywhere else prevents one noisy series from flattening the book.
- **STRESS-trigger:** (≥1 indicator at crisis-grade) OR (≥2 indicators at stress-grade).

Transition rules:
1. **Escalation is immediate and may jump states** (NORMAL→CRISIS direct on a CRISIS-trigger).
   State is decided at close[t] from indicator values at t and consumed by the book at the
   open[t+1] fill — the engine's standard [k−1] decision-lag convention; no intra-candle exits
   (an honest 8h reaction lag, disclosed).
2. **Minimum dwell:** CRISIS ≥ 9 candles (3d); STRESS ≥ 6 candles (2d). A flash wick that
   fires GAP costs a 3-day de-risk — that is the price of insurance; the calm-period coverage
   budget (§2.4) bounds how often it is paid.
3. **De-escalation is slow and steps one state at a time:**
   - CRISIS→STRESS: no CRISIS-trigger for 9 consecutive candles (3d) AND dwell met.
   - STRESS→NORMAL: no STRESS-trigger and no CRISIS-trigger for 21 consecutive candles (7d)
     AND dwell met.
   Asymmetry rationale (crypto-native): liquidation cascades self-excite (Hawkes signature;
   median cascade 2–6h, aftershocks cluster for days) — entries must be fast because the 8h
   bar is already slow versus the cascade timescale; exits must be slow because aftershocks
   arrive into thin, one-sided books.
4. **Warmup:** state = NORMAL while any required indicator is in min_periods warmup, flagged
   `WARMUP` and excluded from falsification scoring (§2.4) and from occupancy fractions.

### 2.3 What each state does to a book (+ the blue-chip core)

| State | Gross scalar | Universe | Notes |
|---|---|---|---|
| NORMAL | 1.0 | the construction's full pre-registered universe | full book |
| STRESS | 0.5 | intersection of the construction's universe with PIT top-20 by trailing 270c mean dollar-volume | contraction toward the blue-chip core; dropped names close at the next rebal fill |
| CRISIS | **0.0 — FLAT (default)** | — | see fallback decision below |

Scalars 1 / ½ / 0 are principle anchors (full / half / none — the SCUD φ=0.50 precedent for
the half), never scanned. Composition with any construction-specific throttle (e.g., a
SCUD-style gross throttle): **effective scalar = min(machine scalar, construction scalar)** —
the more conservative wins; multiplicative stacking would double-count. Plumbing: the machine
emits a past-only `gross_scalar_series` + state series consumed via the engine's existing
sanctioned opt-in pattern (`book_scalar_series` forensics already exist in `BacktestResult`).

**The crisis fallback decision — FLAT, with a narrow pre-registered carve-out.**
Charter offers blue-chip-only minimal neutral core OR flat. **Default for ALL families: FLAT.**
Justification: (1) CRISIS means "the model is lost" — any position derived from a fitted signal
is unjustified by the machine's own premise, and correlation-to-one destroys exactly the
cross-sectional dispersion these books trade; (2) flat has zero parameters to falsify and zero
leak surface; (3) our 2.5bps slippage assumption is least trustworthy inside a cascade — the
honest-cost doctrine says don't trade where the cost model is known-wrong; (4) the re-entry
cost of a false CRISIS is bounded, measurable, and charged by the falsification harness's
episode ledger. **Carve-out (pre-registered per construction at its brief, frozen before any
run, never toggled post-hoc):** a family whose mechanism has an articulated all-regime payer
that SURVIVES correlation-to-one AND whose signal is directly observable (not model-fitted) may
register the blue-chip-minimal-core fallback instead: the construction's own signal restricted
to the blue-chip core, gross 0.25, beta-projected. Family I is the canonical (and currently
only) qualifying case: crash funding flows are the single most reliable crisis payer in this
dataset (A3-1's funding leg paid 3–6× its IS rate in a 28.5%-crash window; BIS WP 1087's
carry-shock→liquidation mechanism), and the funding print is an observable, not a model output.

**Blue-chip core — mechanical, frozen rule (not a frozen list):**
- Eligible(t) = perps with ≥540 days of listed history at t.
- Core(t) = top-5 of Eligible by trailing 270-candle (90d) mean dollar-volume, all past-only.
- Evaluated at rebal candles only. Anti-churn hysteresis: a name ENTERS the core after
  appearing in the top-5 on 2 consecutive evaluations; it EXITS after falling below rank 7 on
  2 consecutive evaluations (5/7 band). This mechanically yields BTC, ETH + the reigning
  majors (BNB/SOL/XRP/DOGE, era-dependent) with no hand-curated list. 540d/top-5/rank-7 are
  a-priori structural constants.

### 2.4 IS falsification protocol (the machine's ONLY calibration check — no Sharpe anywhere)

Run once on IS (2020-01-01→2024-06-30) with the §2.1–2.2 spec frozen. The harness consumes
market data and episode timestamps ONLY; it never sees a book.

**Primary episodes — machine must reach CRISIS with LEAD or COINCIDENT timing (0 LAG allowed):**

| Episode | T0 (pre-registered defining date, UTC) | Pass window for first CRISIS candle |
|---|---|---|
| COVID | 2020-03-12 | [T0 − 5d, T0 + 1d] |
| May-2021 crash | 2021-05-19 | [T0 − 5d, T0 + 1d] |
| LUNA/UST spiral | 2022-05-11 | [T0 − 5d, T0 + 1d] |
| FTX collapse | 2022-11-09 | [T0 − 5d, T0 + 1d] |

LEAD = first CRISIS before T0 (within window); COINCIDENT = on T0 or T0+1d; anything later =
LAG = **FAIL for that episode**. Pass bar: **4/4 primary episodes at CRISIS, 0 LAG.** A machine
that fires at the trough is worthless (the v2 SCUD standard: 0 LAG across all fired months).

**Secondary episodes — machine must reach ≥ STRESS in the same window shape:**
2021-12-04 (flash crash), 2022-06-13→18 (Celsius/3AC, T0 = 2022-06-13), 2023-08-17
(deleveraging day). Pass bar: 3/3 at ≥ STRESS. (Secondary episodes reaching CRISIS is
acceptable, not required.)

**Calm-period coverage budget (a-priori insurance budgets; over defined non-WARMUP IS):**
- CRISIS occupancy ≤ 4% of candles; STRESS+CRISIS occupancy ≤ 15%.
- Distinct CRISIS entries ≤ 10 over the 4.5-yr IS (≈ ≤2.2/yr).
- Outside the pre-registered episode windows (each episode ± 15 days), CRISIS occupancy
  ≤ 1.5% of candles.
An insurance policy that is "on" 20% of the time is not insurance; a machine that never
de-escalates would trivially pass the episode test — the budget is the other jaw of the vise.

**Failure protocol (mn_regimes occupancy-check precedent):** if the frozen machine misses an
episode or blows the calm budget, ONE re-registration is permitted via PLAN-AMENDMENT —
thresholds may move only along their pre-declared anchor families (e.g., a z anchor 2.0→1.65,
both standard-normal coverage points; a breadth anchor 0.95→0.90, both round numbers), never
toward any book metric — documented BEFORE any book-level backtest consumes the machine. After
that, the machine is immutable for the track's lifetime. The harness's full output (episode
table with per-indicator vote traces, state timeline, occupancy report, episode ledger of
entry/exit costs implied by state churn) is committed as `CRISIS-FALSIFY.md`.

### 2.5 Leak-safety and degraded-data semantics (the SCUD/stateful-gate lessons, mandatory)

- **Corrupt-future positive control:** corrupting all inputs at rows ≥ t leaves states < t
  bit-identical (per indicator AND on the composed state series).
- **Forward-replay determinism / append-invariance:** running the machine on growing data
  prefixes yields identical state prefixes (the stateful-gate deadlock/rewrite class killer;
  same property `blind_paper_l1` asserts weekly).
- **Decision-lag test:** the state consumed at fill k uses only data ≤ close[k−1].
- **Vote forward-fill (SCUD C2 pattern):** an UNDEFINED indicator at t forward-fills its last
  defined VOTE (initialized 0). If ALL cross-sectional indicators are undefined (data outage),
  the machine HOLDS state (never silently de-escalates on missing data) and flags DEGRADED.
- **No-book-input test:** `mn3_crisis` module imports market-data loaders only; a unit test
  asserts its public functions accept no strategy artifacts (the `mn_regimes` signature
  discipline).

---

## 3. Construction sketches (all five charter menu items G/H/I/J/K carried)

All five are kept: G is the mandated flagship; H is the user's ensemble directive as a
construction; I is the only proven-durable mechanism (kept despite its compromised holdout —
§3.3 restructures its evidence); J is the cheapest genuinely-unprobed axis; K is the only
intraday and only event-conditioned axis and its falsifier is nearly free on already-fetched
1h data. Nothing added: the menu's residual surface is already wider than one wave can clear.

Common conventions: universe = PIT top-40 (§2.1 convention; top-20 robustness column);
residual return r̃ = r − β·r_BTC via `mn_beta` (§1.4); costs 5+2.5 bps per side on every leg
+ funding on every perp leg; 2×-cost twin always (ground-truth twins for stateful
constructions, analytic twins only for stateless — charter); phase sweeps mandatory for any
cadence > 1 candle (21-phase tranche ensemble; headline = phase-agnostic mean); every
diagnostic reports by regime bucket (§5.3) and by IS halves (H1 = 2020-01→2022-03,
H2 = 2022-04→2024-06); all diagnostics import `mn3_guard` and run on the NEW IS ONLY.
Multiple-testing ledger convention (v2-inherited): a REGISTERED TRIAL = a scored variant;
a-priori design constants are disclosed as design DOF, not trials; each family's n_eff ledger
opens at the counts below and is carried into every exploration verdict and reveal-time
discount.

### 3.1 Sketch G — ML cross-sectional residual alpha (flagship)

**Mechanism — who pays us, in all regimes.** LightGBM predicts beta-RESIDUALIZED forward
returns from neutralized features. ML's role is NOT to discover a new payer — it is to combine
the known structural payers CONDITIONALLY: (a) leveraged retail directional flow, visible in
funding/OI/positioning-ratio features, pays via funding and via the predictable unwind of
crowding; (b) impatient liquidity demanders, visible in taker-imbalance features, pay the
impact-reversion premium; (c) slow herding flow, visible in residual-momentum features, pays
the underreaction premium on name-specific news. The tree model's edge over the linear sleeves
(H) is the interaction surface — e.g., funding extremity should matter MORE when OI is
stretched and taker flow is one-sided (the crowding syndrome, not its symptoms separately).
In crash the crowding features flag the squeeze side; in mania dispersion is rich and funding
extremes are most informative; in chop carry-like features dominate. The "model is lost" tail
is the crisis machine's job, not the model's.

**Data:** all ready. 8h OHLCV+taker (747 perps), funding (779), OI archive (599 symbols; BTC
from 2020-09-01, broad coverage from ~2021-12 — per-name NaN before archive start, LightGBM
handles missing natively). Era-proxy risk disclosed: OI availability is era-correlated; the
per-year IC stability kill (b) is the falsifier.

**Pre-registered feature list — EXACTLY these 24, immutable once DIAG-G runs** (all past-only,
consumed at [k−1]; "xz" = cross-sectional z at t; "own-pctl" = percentile in own trailing 270c
history):

- Funding (5): `fund_lvl_xz` (9c mean funding), `fund_lvl_ownpctl`, `fund_mom21_xz`
  (9c-mean now − 9c-mean 21c ago), `fund_mom63_xz` (same, 63c), `fund_abs_xz` (9c mean |funding|).
- OI (5): `oi_chg9_xz` (Δlog sum_open_interest, 9c), `oi_chg90_xz` (90c),
  `oi_per_dvol_xz` (OI value / 30c mean dollar-volume), `toptrader_ls_xz` (3c mean),
  `taker_ls_oi_xz` (taker L/S vol ratio from OI archive, 9c mean).
- Taker (3): `ti3_xz`, `ti9_xz`, `ti21_xz` (taker_buy/volume, 3/9/21c means).
- Vol structure (3): `rvratio_xz` (RV9/RV90), `range9_xz` ((high−low)/close, 9c mean),
  `rv_ownpctl` (RV30 own-history percentile). **Deliberate exclusion:** NO cross-sectional
  vol-LEVEL feature — that would let the model reconstruct the CLOSED vol_low family.
- Residual momentum (3): `resmom21_xz`, `resmom63_xz`, `resmom189_xz` (trailing residual returns).
- Liquidity (2): `amihud30_xz` (mean |ret|/dollar-vol, 30c), `dvol_rank` (30c dollar-vol rank).
- Market context (3, identical across names at t — interaction fuel): `mkt_regime`
  (§5.3 label as −1/0/+1), `mkt_corr` (C2's ρ̄[t]), `mkt_fund_agg` (C3's z[t]).

Design provenance disclosed: the CLASSES were informed by MN-v2 univariate diagnostics
measured over windows overlapping W1–W2 of the new holdout (§1.3) — that knowledge selected
which families of features to include; no G model has ever seen any holdout data.

**Label:** forward 3-candle (24h) residual TOTAL return (price + funding), winsorized at ±20%
(a-priori sanity cap for L2 on fat tails). Single pre-registered horizon, not a scan:
1-candle labels are cost-dominated at 8h; long labels shrink the effective sample; 24h matches
the weekly-tranche book's decision density. Overlapping labels disclosed (uniqueness ≈ 1/3);
train/OOF boundaries purged by 3 candles (the label horizon) — the standard purge convention.

**Walk-forward + HP region + seed policy (the v1/v3-track discipline, cited and applied):**
- Monthly retrain, trailing 24-month training window (`training_months = 24`, the house
  sacred constant), predict the next month out-of-fold. First OOF month 2022-01 (24mo warmup;
  coincides with broad OI coverage). OOF span 2022-01→2024-06 = 30 months.
- **Explicit feature columns ALWAYS:** `feature_columns=list(MN3_G_FEATURE_COLUMNS)` — the
  position-pinned tuple (LightGBM's colsample samples by position; the
  feedback_explicit_feature_columns rule).
- **HP region = a fixed 8-config grid, ZERO Optuna** (stricter than v3's n_trials=35 cap):
  num_leaves ∈ {15, 31} × min_data_in_leaf ∈ {200, 500} × lambda_l2 ∈ {1, 10}; fixed
  lr=0.05, n_estimators=300 (no early stopping — deterministic), feature_fraction=0.8,
  bagging_fraction=0.8/freq=1, `deterministic=true`.
- **Seed ensemble:** 5 seeds {42, 123, 456, 789, 1001} (house convention), prediction = mean.
- **Config selection rule (pre-registered):** highest pooled OOF Spearman IC over the 30 OOF
  months; ties → fewer leaves, then larger min_data_in_leaf (simpler model wins).

**Frequency + cost:** weekly rebal (21c) with 21-phase tranche ensemble; a rank book on a 24h
label implies roughly 30–50% one-way weekly turnover — must clear 15bps round-trip; DIAG-G
reports the implied turnover and cost coverage of the quintile book.

**DIAG-G (cheapest-to-falsify: an OOF-IC harness, NOT a backtest).** Walk-forward OOF
predictions scored on IS only. Kill criteria — G dies if ANY of:
(a) best-config pooled OOF Spearman IC < 0.02 (an ML combiner that cannot beat the univariate
    IC bars of its own inputs does not earn its surface);
(b) calendar-year instability: IC ≤ 0 in ≥2 of the 3 OOF years (2022, 2023, 2024-H1);
(c) seed instability: ANY of the 5 seeds has pooled IC ≤ 0 at the selected config;
(d) economics: top-minus-bottom QUINTILE net spread at weekly cadence (21-phase mean) fails
    2×-cost coverage;
(e) all-weather: CRASH-bucket quintile-spread mean return t < −2 (significantly wrong-signed
    where the doctrine demands survival).

**Multiple-testing budget (family G):** ledger opens at **8 registered trials** (the HP grid;
one feature list, one label — counted as design DOF with provenance disclosed). If DIAG-G
fails on a specific diagnosable defect, at most ONE pre-registered revision round is permitted
(PLAN-AMENDMENT before rerun; ledger 8→16); **hard cap 16 trials for the family's entire IS
life.** No per-run tuning, no feature add/drop iteration, no post-diagnostic label changes —
feature-selection-by-iteration is the classic mining vector and is banned.

### 3.2 Sketch H — Born-ensemble multi-sleeve MN composite

**Mechanism.** The user's ensemble directive as a construction: 3–4 weak orthogonal sleeves
combined at equal-risk FROM BIRTH — diversification as the design, not a capstone afterthought.
Who pays, per sleeve (charter's sleeve list, each ONE fixed construction, no grids):

- **S1 carry-flow:** cross-sectional rank of trailing 9c mean funding; long bottom quintile /
  short top. Payer: leveraged directional traders on the crowded side, both directions, all
  regimes (the proven durable flow). [Contamination: the A-family signal core — disclosed.]
- **S2 OI-structure (continuation sign):** cross-sectional z of Δlog OI over 90c; long high /
  short low. Payer: later-arriving leveraged entrants — capital-inflow persistence at 8h (the
  MN-v2 DIAG-C finding, sign disclosed as contaminated-window-derived; the CLOSED family is
  OI-FADE — this is the opposite sign, a different mechanism: flow persistence, not fragility).
- **S3 vol-structure (term-structure slope, NOT level):** per-name RV9/RV90 ratio,
  cross-sectional rank; LONG low-ratio / SHORT high-ratio (fade the currently-exciting names —
  lottery-demand overpricing of recent action). **Flag for Critic pre-flight:** this rhymes
  with the CLOSED vol_low family; the object is the OWN-HISTORY-normalized slope, not the
  cross-sectional vol level — Critic must ratify the distinction or the sleeve is dropped
  pre-run (H proceeds with 3 sleeves).
- **S4 liquidity-provision proxy:** Amihud (mean |ret|/dollar-vol, 30c) cross-sectional rank
  among the top-40; LONG high-Amihud / SHORT low-Amihud. Payer: immediacy demanders in the
  thinner half of the liquid set. Cost warning disclosed: the long side is structurally more
  expensive to trade — the 2×-cost twin is load-bearing here.

Each sleeve: quintile L/S on the top-40, beta-projected (`mn_beta`), weekly rebal, 21-phase
tranche. Composite: equal-RISK weights = inverse trailing 90d realized sleeve vol (a-priori;
an IS-Sharpe-optimized weighting is mining and is banned — capstone doctrine §1). The
falsifiable composite claim (capstone doctrine §4): composite Sharpe ≥ best sleeve's AND
composite maxDD shallower than every sleeve's, via measured decorrelation; sleeves too
correlated to add anything = a FINDING (mechanism overlap), not a tuning failure.

**Data:** all ready; S2 starts when ≥25 universe members carry OI (report the actual date;
~2021-12 expected).

**DIAG-H (per-sleeve IC/spread + sleeve correlation matrix; <1 day).** Kill criteria:
(a) FAMILY dies if <2 sleeves pass their sleeve gate: net 2×-cost quintile spread > 0 at
    weekly cadence (phase-agnostic mean) AND sign-stable across IS halves;
(b) FAMILY dies if the median pairwise correlation of PASSING sleeves' weekly returns ≥ 0.5
    (nothing orthogonal to combine);
(c) surviving sleeves (≥2) proceed to EXPLORATION-H as the composite — sleeve selection is
    mechanical (all survivors enter), never discretionary.

**Multiple-testing budget (family H):** 4 registered trials (one per sleeve; the composite is
arithmetic, not a trial). Sleeve spin-outs are re-parameterizations of H — they share H's
holdout token forever (anti-gaming rule, §6.1). Cap 8 (one amendment round max).

### 3.3 Sketch I — Funding-carry v2 (contamination-disclosed re-instantiation)

**Mechanism.** Proven durable: funding is the perp's price-anchoring tax on the crowded side;
leveraged directional traders pay it in both directions — crowded longs in mania, panicked
shorts in crash (A3-1's funding leg: 6/6 IS years positive, then +8.75 bps/cd, 7/7 months
positive, on genuinely unseen crash-heavy data — the one mechanistically-confirmed
all-regime payer in this dataset). Construction: long low/negative-funding vs short
high-funding, projection-based beta-neutralization (hedge-free — A3's transferred choice),
construction throttle inherited (SCUD-style; its constants are coverage/principle-anchored —
τ at standard-normal 80th/95th, W=90, q=0.33 structural — and therefore inheritable with
disclosure, not refitting), **crisis machine on top with the §2.3 blue-chip-core carve-out**
(the canonical qualifying family: the payer survives correlation-to-one and the signal is an
observable print, not a model output). CRISIS book = the same funding sort restricted to the
blue-chip core, gross 0.25, beta-projected.

**The honest evidential structure (family-defining flag).** Per §1.3, family I's holdout is
compromised end-to-end: W1+W2 were the A-family's development IS; W3 is book-revealed. So:
- The construction is RE-ANCHORED on the NEW IS only (2020→2024-06): every constant that was
  data-derived in v2 is re-derived here; principle-anchored constants carry with disclosure.
- Any family-I Stage-2 reveal scores W1+W2 as its PRIMARY read (parameter-contaminated but
  never book-evaluated for the new construction — discounted once) and reports W3 SEPARATELY
  AT ZERO EVIDENTIAL WEIGHT (fully revealed for this family; can never count as evidence —
  charter). The Critic's reveal verdict must apply this discount explicitly.
- Consequently **family I's real arbiter is Stage 3** (the forward paper-trade on genuinely
  unseen post-2026-06 data). Its Stage-2 pass, if any, is structurally weaker and is flagged
  as such in advance — no post-hoc surprise.

**Data:** ready (funding 779 symbols, loader bucket-sum exact).

**DIAG-I (re-anchoring harness on the new IS; <half day — the mn_diag_a_funding pattern).**
Decile capture of next-candle residual TOTAL return by trailing-9c-mean-funding sort,
funding/price decomposition, regime buckets, cost coverage at rebal ∈ {3, 21} (2 cells).
Kill criteria (the v2 DIAG-A structure, re-scored on the new window):
(a) net-of-cost D1−D10 residual total-return spread ≤ 0 annualized at BOTH rebal 3 and 21;
(b) price-leg giveback ≥ 100% of funding collected on full-IS aggregate;
(c) CRASH-bucket mean spread return < 0 with t < −2 (the mechanism predicts carry WINS in
    crashes; a significant crash loss falsifies the mechanism, not the parameters).

**Multiple-testing budget (family I):** the ledger INHERITS the A-family's terminal n_eff 9
(the mechanism family's cumulative mining does not reset with a rebrand) + 2 new cells =
**opens at 11**. Cap 15.

### 3.4 Sketch J — Funding term-dynamics (the funding SURFACE as signal)

**Mechanism.** Funding is a lagged, clamped controller tracking the perp–spot basis; its
DYNAMICS (not its level) encode where positioning is BUILDING vs UNWINDING. Rising funding =
leverage building — the late entrant on the crowding side pays once the build saturates;
falling-from-extreme = unwinding in progress — the forced unwinder pays the fader of panicked
funding. In crash, the panicked-short funding plunge marks capitulation (mean-reversion pays
the long); in mania, the funding ramp marks late leverage (fade pays); in chop, funding
oscillation around zero marks rotating mini-crowds. **The delta vs family I is conditioning on
the CHANGE, not the LEVEL — and that distinction is measured, not asserted:** every J read is
reported both raw and LEVEL-CONTROLLED (cross-sectional rank-regression of the momentum signal
on the level signal; IC of the residual). If the level explains it, J is I in disguise and
dies as a separate family (kill c).

**Contamination note (§1.3):** funding AUTOCORRELATION stats are known over W1–W2 (MN-v2
DIAG-A); the cross-sectional funding-MOMENTUM IC — J's object — has never been measured
anywhere. Genuinely new axis, mild disclosure.

**Data:** ready. **Frequency:** 8h native; candidate cadences rebal ∈ {3, 21} for the best
cell (cost coverage decides).

**DIAG-J (<half day; the funding harness + one partial-correlation step).** Pre-registered
grid: signal = per-name funding-momentum ΔL = (9c-mean funding at t) − (9c-mean funding at
t−L), L ∈ {9, 21, 63}; cross-sectional rank; forward 3c residual total return; each L scored
raw AND level-controlled → **6 registered cells**. By bucket + IS halves; decile spread with
turnover and 2×-cost coverage at rebal 3 and 21 for the best level-controlled cell.
Kill criteria — J dies if ANY of:
(a) no L with level-controlled |IC| ≥ 0.015 sign-stable across IS halves;
(b) best cell's decile spread fails 2×-cost coverage at both rebal 3 and 21;
(c) level-controlled IC < 50% of raw IC at EVERY L (it's all the level → fold into family I;
    no J token is spent, and no J construction ever runs).
Aggregate funding-momentum as a standalone TIMING overlay is banned (directional risk);
only the cross-sectional form is in scope.

**Multiple-testing budget (family J):** opens at 6. Cap 12 (one amendment round).

### 3.5 Sketch K — Event-conditioned books (dispersion-gated 1h liquidity provision)

**Mechanism.** Trade ONLY inside high-dispersion windows. After a market-wide shock, forced
flow (liquidations, stop-outs, margin calls) dominates the tape and the immediacy premium is
at its richest; a short-lived cross-sectional reversal book provides liquidity exactly when a
payer demonstrably just paid, and is FLAT otherwise. The payer in crash = liquidated longs'
stops crossing the spread; in mania = FOMO chasers and squeezed shorts; in chop = single-name
event flow (unlocks, hacks, listings) spilling into correlated names. Turnover suppression is
BORN-IN (the E2 lesson: unconditional 1h reversal died behind a 10× cost wall; conditioning
concentrates the same gross into the ~5% of hours where per-trade edge can clear costs).
**Family distinctness (Critic to ratify):** resid-mom/reversal-STANDALONE is closed as an
unconditional cross-section; K is event-GATED liquidity provision — different trade count,
different payer concentration, and kill (d) forces the conditioning to prove it adds.

**Data:** 1h klines for ~361 symbols already fetched (core 35 verified complete; the full-set
completeness gate is a QE ask, §5.5 — DIAG-K is gated on it). **Frequency:** 1h; cost
reality: 15 bps round trip per unit turnover; the book trades ~once per event with a 4h hold.

**Event definition (pre-registered, coverage-anchored):** market-wide dispersion event at hour
h when the cross-sectional std of trailing-4h returns across the PIT top-30 exceeds its own
trailing 720h (30d) 95th percentile (fires ≈5% of hours by construction — a coverage anchor,
not a fitted threshold); re-arm: no new event within 12h of the last (cluster de-dup).
**Book (ONE fixed construction):** at the event hour's close, form quintiles on trailing-4h
RESIDUAL returns across the top-30; long losers / short winners; enter at the next 1h open;
hold 4h; exit. Beta-projected. **Doctrine interaction (pre-registered):** K may trade in
machine-STRESS at the 0.5 gross; machine-CRISIS flat is non-negotiable — shared doctrine wins
over the construction's appetite; kill (c) tests whether that leaves K anything to eat.

**DIAG-K (<1 day once the 1h completeness gate passes; needs the crisis machine's state
series → gated on CRISIS-FALSIFY).** Event census (rate/month, clustering), per-event net
quintile spread distribution, bucket + IS-half splits, machine-state overlap of event P&L,
conditional-vs-unconditional IC comparison. Sample floor: ≥150 events over IS, else the
verdict is INSUFFICIENT-DATA (not pass). Kill criteria — K dies if ANY of:
(a) median event rate < 4/month (cannot diversify a book across events);
(b) net-of-2×-cost per-event quintile spread ≤ 0, or sign-unstable across IS halves;
(c) >50% of aggregate event P&L falls inside machine-CRISIS candles (doctrine-incompatible:
    the edge lives exactly where the book must be flat);
(d) post-event IC < 2× the unconditional 1h reversal IC measured on the SAME window and
    universe (conditioning adds nothing → K reduces to the closed unconditional family → dead).

**Multiple-testing budget (family K):** opens at **1 registered trial** (one event rule × one
book; the four a-priori constants — 95th pct, 30d window, 12h re-arm, 4h formation/hold — are
disclosed design DOF). Cap 4.

---

## 4. Diagnostic order

Ranking rule (v2-inherited): prior strength × data readiness × falsification cheapness —
plus, new in MN3, crisis-machine dependency. Infrastructure gates in [brackets].

| Order | Item | Gated by | Why here |
|---|---|---|---|
| 0 | `mn3_split` + `mn3_regimes` occupancy check + `mn3_datacheck` | — | The split guard blocks EVERYTHING — no MN3 number exists before it; occupancy check is the regime rules' one escape hatch and must fire before any diagnostic is scored. |
| 1 | **CRISIS-FALSIFY** (§2.4) | [mn3_split, mn3_crisis] | Market-data-only, ZERO mining risk (no book anywhere), and every EXPLORATION consumes the machine — build and falsify the shared insurance first. Also forces the blue-chip-core builder into existence. DIAG-K consumes its state series. |
| 2 | **DIAG-J** | [funding harness] | Cheapest genuinely-NEW high-prior axis; data 100% ready; the level-control machinery it builds is reused by DIAG-I and H's S1. |
| 3 | **DIAG-H** | [mn_beta reuse; OI loader] | Four fixed sleeves, no grids, <1 day; its sleeve-correlation matrix is the first empirical read on whether the ensemble doctrine has anything orthogonal to combine — informs G expectations too. |
| 4 | **DIAG-G** | [mn3_features builder + leak tests] | The flagship carries the heaviest infrastructure (feature matrix, walk-forward OOF harness, 5-seed × 8-config compute ~hours); the builder is dispatched at track open (§5.4) and lands while 1–3 score. |
| 5 | **DIAG-I** | [funding harness] | High prior but LOW information gain (a re-anchoring of a proven mechanism on a subset of what v2 measured) and its Stage-2 is structurally weak regardless — it should not consume early slots. Runs while G trains. |
| 6 | **DIAG-K** | [1h completeness gate + CRISIS-FALSIFY] | Double-gated; last by dependency, not by prior. |

Parallel QE dispatches at track open (no diagnostic result influences whether they run):
`mn3_split` (first, blocks all), `mn3_crisis`, `mn3_features`, the 1h completeness re-check.
Every diagnostic script is committed BEFORE its first scored run (`analysis/portfolio/
mn3_diag_*.py`); one diary entry per diagnostic regardless of outcome — kills documented with
the same rigor as survivals.

---

## 5. QE infrastructure asks (specs — nothing implemented in this plan)

### 5.1 `analysis/portfolio/mn3_split.py` — THE FIRST TASK; blocks everything

- Constants: `MN3_IS_START_MS = 1577836800000` (2020-01-01), `MN3_IS_CUTOFF_MS =
  1719792000000` (2024-07-01 00:00 UTC), `MN3_HOLDOUT_END_MS = 1782864000000`
  (2026-07-01 00:00 UTC). Import-time literal asserts on all three (the mn_split pattern —
  a silent constant edit trips before any script computes a number).
- `mn3_is_mask(panel)`; **structurally distinct from every prior cutoff:** deliberately
  self-contained, `MN3_*` names only; a unit test asserts no mn3 module imports
  `mn_split.mn_is_mask` or `blind_universe.is_mask` (grep-based import-ban test), so the
  2026-01-01 / 2025-03-24 boundaries cannot be silently swapped in.
- **Sealed-holdout guard with FAMILY TOKENS:** `mn3_guard(grid_ms, windows, *,
  reveal_token=None)` raises `Mn3HoldoutError` on any metric window overlapping
  [MN3_IS_CUTOFF_MS, MN3_HOLDOUT_END_MS) unless a sanctioned reveal: `reveal_token ∈
  {"MN3-G","MN3-H","MN3-I","MN3-J","MN3-K","MN3-ENSEMBLE"}`, single-use FOREVER — the guard
  reads/writes `diary-portfolio-mn3/REVEAL-LEDGER.md` and hard-refuses a token already
  recorded (loud, auditable banner with UTC timestamp on the one sanctioned use; the
  CONFIRMATION-A audit-banner precedent). `MN3-ENSEMBLE` consumption atomically records ALL
  member-family tokens (§6.3). Post-2026-06-30 data is likewise guarded (Stage-3 territory;
  only `mn3_paper_*` may touch it).
- Every mn3 diagnostic/exploration script imports and calls the guard BEFORE computing or
  printing any metric.

### 5.2 `analysis/portfolio/mn3_crisis.py` — the §2 machine, verbatim

- The five indicator constructions (§2.1) with their frozen constants as module-level pins
  (the mn_scud style: constants are NOT function parameters — the freeze is structural).
- The state machine (§2.2): triggers, dwell minimums, one-step de-escalation, warmup + DEGRADED
  semantics, vote forward-fill.
- The blue-chip-core builder (§2.3): eligibility, top-5 rule, 5/7 hysteresis band, past-only;
  unit test: membership series is prefix-stable (append-invariant).
- The falsification harness (§2.4): episode table with per-indicator vote traces,
  LEAD/COINCIDENT/LAG classification against the pre-registered T0 dates, occupancy + distinct-
  entry counts, calm-window budget check, state-churn episode ledger. **No strategy returns
  anywhere in the module** — enforced by the no-book-input test (§2.5).
- Full §2.5 leak-test suite in `tests/test_mn3_crisis.py` (corrupt-future per indicator AND on
  the composed state; forward-replay/append-invariance; decision-lag; forward-fill semantics;
  DEGRADED hold-state).
- Engine integration via the sanctioned opt-in pattern only: emit a past-only
  `gross_scalar_series` + state array; `min()`-composition with construction throttles;
  inert-default byte-identity test (machine off ⇒ every existing mode bit-identical).

### 5.3 `analysis/portfolio/mn3_regimes.py` — bucket rules (REUSE, my call, justified)

- **Decision: reuse `mn_regimes`' frozen rules unchanged** (trailing 90-candle BTC return;
  CRASH ≤ −15%, MANIA ≥ +25%, else CHOP; market-only, WARMUP semantics). Justification:
  (1) the constants are a-priori round numbers, never fitted, and they worked — the v2
  bucket machinery scored CONFIRMATION-A's composition mechanically; (2) re-deriving regime
  boundaries per track is itself a tuning vector — freezing them ACROSS tracks is the
  stronger discipline; (3) single source of truth: `mn3_regimes.py` is a thin wrapper
  importing the constants + `mn_regime_labels` from `mn_regimes` (this import is sanctioned;
  the §5.1 import ban covers SPLIT modules only), adding an MN3 occupancy function on
  `mn3_is_mask`.
- **Occupancy sanity check on the NEW IS (2020-01→2024-06), run once before any diagnostic is
  scored:** each bucket ≥5% of defined IS candles. If it fails, ONE re-registration via
  PLAN-AMENDMENT-NNN before any diagnostic result is looked at; then immutable. (The new IS
  is proportionally richer in 2020–22 crash/mania than v2's, so a pass is expected — but the
  check is the rule, not the expectation.)

### 5.4 `analysis/portfolio/mn3_features.py` — sketch G's feature-matrix builder

- The 24-feature matrix (§3.1) EXACTLY; exported position-pinned tuple
  `MN3_G_FEATURE_COLUMNS` (len 24; order frozen; the explicit-feature-columns house rule).
- Past-only construction throughout; consumed at [k−1]; NaN policy = LightGBM-native missing,
  NO forward-fill across gaps; per-name OI features NaN before archive start.
- **OI `.shift(1)` convention asserted in code AND pinned by unit test** (the resampler's
  bar-T-aggregates-own-rows lesson from the v2 OI backfill — carried verbatim).
- Leak tests per feature block: corrupt-future positive control (corrupt rows ≥ t; features
  < t bit-identical), cross-sectional-z at t uses only names live at t (no survivorship
  backfill into the z denominator).
- Walk-forward OOF harness: monthly retrain, trailing 24-month window, 3-candle purge at every
  train/OOF boundary, 8-config grid × 5 seeds, OOF predictions persisted to disk so DIAG-G
  scoring is a pure read (re-scoring never retrains).

### 5.5 `mn3_datacheck` + 1h completeness gate + data-extent verification

- Clone/extend the `mn_datacheck` pattern (BTC grid integrity HARD; live-coverage SOFT) onto
  the MN3 grid extent.
- **1h completeness gate for DIAG-K:** re-run `klines_1h_coverage_check.py` logic over the
  full ~361-symbol scope (the 1H-FETCH-REPORT verified core-35 only; the remainder was
  in-flight) — per-symbol row counts vs expected grid, loud gap report, and the DIAG-K
  universe restricted to verified-complete symbols. No 1h diagnostic runs before this gate.
- **OI per-symbol archive-start report on the new IS** (the mn_oi_report pattern): per-name
  usable start dates; the date at which ≥25 of the PIT top-40 carry OI (H's S2 sleeve start;
  G's OI-feature coverage disclosure).
- Funding coverage assertion (`assert_funding_coverage`) wired into every funding-consuming
  diagnostic — the silent-zero guard.

### 5.6 Later (specs deferred, named now so nothing is invented ad-hoc)

- `mn3_paper_*.py` — Stage-3 clone of the `blind_paper_l1` recompute architecture per
  surviving family (frozen params, weekly append-invariant recompute, dual parity pins,
  tamper-evident commits, `_guard_window` quarantine, no exchange orders). Spec'd at Stage-2
  pass time, per family.
- Engine extension for STRESS universe contraction (close-at-next-rebal semantics) — opt-in,
  inert-default byte-identity + full leak tests, only when the first EXPLORATION needs it.

---

## 6. Anti-leak protocol (concrete, MN3)

1. **One holdout reveal per family, EVER — enforced by family tokens in code.** Family =
   mechanism family (G/H/I/J/K). A re-parameterization of a revealed family NEVER earns a
   second token. H's sleeves have no individual tokens; a sleeve spun out as a "new"
   standalone family shares H's token forever (pre-registered anti-gaming rule). If J dies
   as I-in-disguise (kill c), no J token is spent and none becomes available by rebranding.
   The reveal ledger (`REVEAL-LEDGER.md`) is committed, append-only, and checked by the guard
   itself (§5.1).
2. **Stage gates are sequential and unskippable (§1.1).** Stage-2 reveal requires: IS
   robustness documented (phase sweep, 2×-cost twin, regime buckets, seed/window stability as
   applicable), a FROZEN decision map committed before the reveal (CONFIRMATION-A pattern:
   pre-committed reads, thresholds, tier definitions, and §5-style pre-committed consequences
   — including the interpretation under every regime composition), Critic pre-flight, and the
   single-use token. Stage-3 (6-month forward paper) gates are pre-registered per family AT
   Stage-2-pass time, BEFORE the paper window opens: neutrality gates verbatim, a maxDD bound,
   mechanism-attribution reads (e.g., funding-leg sign for I), and an edge read that is honest
   about 6-month power (SE(Sharpe) ≈ 1.4 — the v2 lesson: high-power reads carry the verdict;
   a 6-month Sharpe point estimate alone never does). Stage-4 is the user's decision, small
   size first. **Failing any stage terminates the family — no rescue, no second look, no
   "the window was adverse so discount it"** (the CONFIRMATION-A §5 discipline, now
   track-law).
3. **Ensemble capstone reveal rule (pre-registered now):** when ≥2 families hold banked
   candidates, EXPLORATION-ENSEMBLE registers the cross-family combination — a-priori weights
   only (equal-risk from member vol stats or plain equal-weight, picked at registration;
   IS-Sharpe-optimized weights are mining and banned), members byte-frozen, combined-book
   neutrality measured never assumed. **An ensemble holdout reveal consumes EVERY member
   family's token simultaneously** (`MN3-ENSEMBLE` records them all, atomically). The
   efficient budget path is therefore likely ONE ensemble reveal instead of per-family
   reveals — that choice is the USER's, made after the field survey, never the QR's.
4. **Pre-registration cadence:** this PLAN freezes the crisis machine, all five diagnostics,
   their grids and kill criteria, and the family ledgers (G:8, H:4, I:11-inherited, J:6, K:1)
   BEFORE any mn3 code exists. Each subsequent EXPLORATION gets its own brief
   (`briefs-portfolio-mn3/`) pre-registering construction params, falsification arms, and a
   frozen decision map BEFORE its backtest; adversarial Critic pre-flight before every run and
   review after. Diagnostic scripts committed before first scored run. Amendments dated,
   append-only, and only before the affected artifact is scored. A fired kill criterion is
   final — arguing with it is a process violation, not a research move.
5. **Disclosure duty for contaminated families:** every brief for a construction touching a
   contaminated family reproduces the §1.3 row VERBATIM plus the in-head disclosure, and the
   Critic's verdict must explicitly state the applied discount. Family I additionally carries
   its flag — W3 at zero evidential weight, W1+W2 discounted, Stage-3-decides — in every
   document it appears in, including this one.
6. **No number touches the holdout outside a token reveal.** Every mn3 script calls
   `mn3_guard` before computing anything; the falsification harness, all diagnostics, and all
   explorations run on IS 2020-01→2024-06 only; post-2026-06 data is Stage-3 territory
   reachable only by `mn3_paper_*`. Costs honest from candle one; phase sweeps mandatory;
   market-only buckets; sample floors sized to frequency (8h weekly books: ≥120 IS rebal
   events; K: ≥150 events). All agents on Fable.

---

## 7. Cadence

- Order-0 infrastructure (§5.1–5.3, §5.5) dispatched to QE immediately, in parallel;
  CRISIS-FALSIFY scored first (order-1); diagnostics 2–6 at ~1 day each as their gates open.
- EXPLORATION only after a diagnostic survives its kill criteria — full engine backtest of ONE
  construction with the neutrality gate (§1.4) + the crisis machine integrated from birth.
- CONFIRMATION (Stage-2 reveal) is rare and terminal-budgeted (§6); no reveal happens in this
  wave without the user's go on token spend.
- No knob inheritance from dead sketches; any reuse re-registers in the inheriting family's
  brief with ledger carry.
- One diary entry per diagnostic/exploration regardless of outcome, in `diary-portfolio-mn3/`.

*— QR, MN3 track, 2026-07-11. This document is the pre-registration record; amendments only
via dated PLAN-AMENDMENT sections, never in-place edits. Nothing has been run; no code exists;
the holdout has never been touched.*

---

# PLAN-AMENDMENT-001 — the ONE crisis-machine re-registration (2026-07-11)

**Trigger:** `CRISIS-FALSIFY-001.md` (commit 9672d8ff) — the frozen §2 machine FAILED IS
falsification: primary episodes 3/4 (COVID unscoreable), secondary 3/3 PASS, calm budgets 0/4
(STRESS+CRISIS occupancy 85.25% vs ≤15%). Read in full.

**Scope & authority:** this is the SINGLE anchor-family-constrained re-registration §2.4 permits,
authored BEFORE any book-level backtest consumes the machine, honoring my own frozen constraints:
changes stay within the pre-registered anchor families (normal-coverage-z / round-number-abs on
bounded quantities / fat-tail magnitude), the same five indicator concepts, and the same
three-state fast-in/slow-out grammar. It supersedes ONLY the named items in §2.1–§2.2; everything
else in §2 (blue-chip core §2.3, FLAT fallback + carve-out §2.3, the falsification protocol
targets §2.4, leak-safety §2.5) stands unchanged. **The four calm budgets and the episode pass
bars in §2.4 are NOT touched — they are the falsifier (see §D below).**

**This is the last re-registration.** If the machine below FAILS falsification, the crisis-machine
spec is FROZEN AS FAILED and the track proceeds with GAP-only (the sole component that passed) or
I escalate to the user. There is no second amendment.

**Root-cause summary (from CRISIS-FALSIFY-001 §2–§3, adopted):** two independent defects.
(1) COVID: at T0 only 24 perps existed, none with ≥270c history, so the four cross-sectional
indicators were in warmup; GAP was DEFINED and voted crisis-grade at T0 but §2.2 rule-4 global
warmup forced NORMAL and suppressed it. Not reachable by any threshold — a semantics defect.
(2) Calm blowout: robust-z with standard-normal anchors on regime-PERSISTENT series (median-RV,
mean-|funding|) and abs-level on chronically-high crypto correlation / bear-market breadth measure
regime MEMBERSHIP, not event ARRIVAL — each fires 8–9% of candles; a lone crisis vote trips STRESS
and the 21c-clean de-escalation multiplies every hit into ≥7 days. GAP alone was well-behaved
(1.9%/0.7%, near its anchors) — the only event-arrival construction in the suite.

## A. Warmup semantics + scoring-ambiguity resolution (fixes COVID; adopts guidance (a))

**A1 — per-indicator abstention replaces global-warmup NORMAL forcing.** §2.2 rule 4 is superseded:
an indicator in warmup/undefined at t ABSTAINS — it contributes NO vote and is excluded from the
confluence counts (it is NOT counted as a calm 0-vote). The state is decided from the DEFINED
indicators' votes via the §C grammar. Because GAP defines from ~candle 30 (BTC exists at candle 0;
GAP needs only its EWMA-σ warmup) and GAP-at-crisis-grade is a single-sufficient CRISIS-trigger,
the machine can reach CRISIS on GAP alone before any cross-sectional indicator warms — exactly the
COVID case. A candle where ALL indicators abstain (the first ~30 candles of 2020-01, or a full data
outage) HOLDS state (DEGRADED, initialized NORMAL) — never a forced NORMAL, never a silent
de-escalation on missing data (the §2.5 DEGRADED-hold rule, now the ONLY warmup rule).

**A2 — the §2.2/§2.4 ambiguity is resolved explicitly (adopting the QE's suggested reading).**
An episode is SCOREABLE iff ≥1 indicator is defined within its pass window. Under A1 every primary
is now scoreable (COVID on GAP). The pass bar is therefore the STRICT, unchanged **4/4 primary at
CRISIS with 0 LAG** — I am not lowering the bar to a lenient 3/3; I am fixing the machine so COVID
is genuinely scoreable and must pass on its own merits. Secondary bar unchanged: **3/3 at ≥STRESS**.
"WARMUP excluded from scoring" (old §2.2) is retired; abstention (A1) is the sole mechanism.

## B. Indicator transforms — LEVEL → EVENT-ARRIVAL (adopts guidance (b))

The four regime-persistent indicators are converted from level reads to onset reads of the SAME
underlying quantity, keeping each within a pre-registered anchor family. GAP (the one that worked)
keeps its construction; only its crisis floor is nudged for entry-budget margin. All past-only;
consumed at [k−1]; robust-z convention unchanged (median/MAD, trailing 270c, min_periods 135,
clip ±8); indicator universe unchanged (PIT top-40; CORR on PIT top-20; ≥15-member floor).

**B1 — XVOL: cross-sectional realized-vol ONSET (was: median-RV level-z).**
RV_i,short = std of 8h log returns over trailing 9c (min 6 finite); RV_i,long = over trailing 90c
(min 45). V_short = cross-sectional MEDIAN of RV_i,short; V_long = MEDIAN of RV_i,long.
R_XVOL = ln(V_short / V_long) (guard V_long>0). **z_XVOL = robust z of R_XVOL.** Votes: stress z≥2.0,
crisis z≥3.0 (normal-coverage family, unchanged anchors). Property: after a vol jump, V_long catches
up within ~90c so the ratio decays toward 0 — the indicator fires on ACCELERATION, and a multi-month
high-vol regime no longer pins it (the §3.1 pathology).

**B2 — FUND: aggregate |funding| ONSET (was: mean-|funding| level-z).**
fund_short_i = 9c mean |funding_i|; fund_long_i = 90c mean |funding_i|. F_short = EW cross-sectional
mean of fund_short_i; F_long = EW mean of fund_long_i. R_FUND = ln(F_short / F_long) (guard F_long>0).
**z_FUND = robust z of R_FUND.** Votes: stress z≥2.0, crisis z≥3.0. Fires when funding suddenly
dislocates in EITHER direction (a mania leverage-ramp OR a crash funding-plunge both spike |funding|
short-term); a slow leverage grind (F_long tracks F_short) no longer chronically fires. Clamp
limitation (§2.1) still disclosed — confirming indicator, never sole trigger.

**B3 — CORR: median-pairwise-correlation ONSET (was: abs level 0.75/0.85).**
ρ̄[t] unchanged (median pairwise Pearson of 8h returns, trailing 90c, PIT top-20, 190 pairs).
**z_CORR = robust z of ρ̄** over trailing 270c. Votes: stress z≥2.0, crisis z≥3.0 (moves CORR into
the normal-coverage-z family already used by XVOL/FUND — a pre-registered family in the suite, and
exactly the LEVEL→onset conversion guidance (b) names). Rationale: crypto majors are CHRONICALLY
correlated (median pairwise 0.6–0.8 in calm), so the abs 0.75 anchor was a normal-market level
(9.5% chronic stress, 0% crisis — useless as a crisis signal). The systemic event is correlation
SPIKING ABOVE its already-high baseline; z detects that. My original "z goes numb in an extended
systemic regime" objection is retired: the §C slow de-escalation HOLDS the state up after CORR's
onset spike fades, so CORR is now a confluence CONFIRMER, not a persistence-carrier.

**B4 — BREADTH: coincident-sharp-decline (was: fraction down over 3d, abs 0.85/0.95).**
Per name, standardize the CURRENT 8h return by the name's own trailing-90c return σ (past-only,
min 45 finite): s_i[t] = r_i[t] / σ_i[t]. breadth_tail[t] = fraction of universe members (finite
s_i) with s_i ≤ −2.0. Votes: **stress ≥ 0.40, crisis ≥ 0.60** (round-number-fraction family on a
[0,1]-bounded quantity — same family, new anchors). Fires when a large fraction of the universe
SIMULTANEOUSLY prints a ≥2σ-down 8h candle = a synchronized liquidation event; a slow bear grind
(individual 8h moves within normal σ) no longer chronically fires (the §3.1 pathology). The per-name
σ denominator self-normalizes across regimes (a −2σ move requires a bigger absolute move in
sustained high vol).

**B5 — GAP: unchanged construction; crisis floor raised for entry-budget margin.**
σ[t] = EWMA std of BTC 8h log returns (HL 30c, through t−1); g[t] = |r_BTC[t]| / σ[t].
Stress-grade UNCHANGED: g ≥ 3 OR |r_BTC| ≥ 7%. **Crisis-grade RAISED: g ≥ 5 OR |r_BTC| ≥ 12%**
(was g≥4 OR 10%) — within the fat-tail "impossible-under-calm magnitude" family. Rationale: GAP is
the single-sufficient CRISIS-trigger (COVID's fast path) and the direct driver of distinct-CRISIS
entries; tightening its crisis floor to the most extreme moves buys margin under the ≤10-entry
budget (§D) while every IS primary still clears it (COVID −27%/8h; May-2021/LUNA/FTX all had ≥12%
8h candles), and the ≥2-crisis-confluence path (§C) is the redundant safety net for any primary
whose peak candle were sub-12%.

## C. State grammar — kill the multiplication (adopts guidance (c); keeps fast-in/slow-out)

Votes are ordinal per DEFINED indicator (crisis-grade v=2 implies ≥ stress-grade); abstaining
indicators are excluded from all counts (A1).

- **CRISIS-trigger:** (≥2 defined indicators at crisis-grade) OR (GAP at crisis-grade). *[unchanged;
  GAP fast path preserved — COVID-critical]*
- **STRESS-trigger:** (≥2 defined indicators at ≥ stress-grade) OR (≥1 defined indicator at
  crisis-grade). *[the ≥2-CONFLUENCE clause is the change: a lone stress-grade vote no longer
  triggers anything. A lone CRISIS-grade vote still triggers STRESS — justified because the B1–B4
  onset transforms collapse per-indicator crisis-vote occupancy from 8–9% to ~1%, so this path is
  no longer chronic; the §3.1 "single crisis vote is a STRESS-trigger" pathology was a symptom of
  the LEVEL construction, now fixed at the source.]*
- **Escalation:** immediate, may jump states (NORMAL→CRISIS direct), decided at close[t], consumed
  at the open[t+1] fill ([k−1] convention). *[unchanged]*
- **Dwell:** CRISIS ≥ 9c (3d), STRESS ≥ 6c (2d). *[unchanged — CRISIS is now rare, its dwell costs
  negligible occupancy, and 3-day-flat in a genuine "model is lost" event is prudent]*
- **De-escalation:** CRISIS→STRESS after 9c with no CRISIS-trigger (unchanged); **STRESS→NORMAL
  after 12c (4d) with no STRESS- and no CRISIS-trigger** *[REDUCED from 21c/7d — the §3.3-identified
  primary occupancy multiplier]*. Fast-in/slow-out is preserved: same-candle escalation vs up-to-6-day
  full exit (9c crisis tail + 12c stress tail), still ≥12× slower out than in; median cascade 2–6h
  with aftershocks over days is amply covered by a 4-day stress tail.

## D. Budgets FROZEN — the falsifier is untouched (guidance (d))

The four §2.4 calm budgets — CRISIS ≤ 4%, STRESS+CRISIS ≤ 15%, distinct CRISIS entries ≤ 10,
off-episode CRISIS ≤ 1.5% — and the episode pass bars (4/4 primary CRISIS 0-LAG, 3/3 secondary
≥STRESS, per-episode windows [T0−5d, T0+1d], T0 dates unchanged) are **unchanged**. Moving them
would be tuning-to-pass and would void the entire point of the exercise: the budget is the OTHER
jaw of the vise that the episode test cannot supply. The re-registration changes only the
indicator constructions and the state grammar — the pass/fail bars stay exactly where they were
frozen before any number existed.

## E. Pre-registered expectations for CRISIS-FALSIFY-002 (predictions, honest ranges, residual risks)

Committed BEFORE the re-run. I cannot run this; these are falsifiable predictions, not results.

**Episodes (expect strict 4/4 primary + 3/3 secondary):**
- COVID: GAP defined by ~candle 30; COVID's ≫12% 8h candles → GAP crisis-grade → NORMAL→CRISIS at
  or before T0. Expect PASS (LEAD/COINCIDENT). This is the whole COVID fix.
- May-2021 / LUNA / FTX: genuine sharp onsets; expect onset transforms (B1–B4) to fire crisis-grade
  in confluence AND GAP crisis-grade — timing 0-LAG PRESERVED. FTX's textbook 4-indicator confluence
  should survive (onset forms fire harder at true onsets than level forms).
- Secondaries: expect ≥STRESS via ≥2-confluence. Possible timing shift: Celsius's prior 5-day LEAD
  came from a lone CORR=1 vote (now insufficient under §C ≥2-confluence) — expect it to re-hit
  COINCIDENT on genuine mid-June confluence, still PASS. 2021-12-04 (GAP+coincident-BREADTH) and
  2023-08-17 (GAP stress + BREADTH) expected PASS.

**Per-indicator vote occupancy (the load-bearing fix):** expect crisis-grade occupancy to fall from
8–9% (XVOL/FUND) and 8.6% (BREADTH) to ≈ 0.5–2% each under the onset/coincident transforms; CORR
crisis-grade to rise from 0% to a small non-zero (~0.5–1.5%) and its chronic stress to fall from
9.5% to ≈ 2–4%; GAP essentially unchanged (crisis-grade slightly lower under the 5σ/12% floor).

**Calm budgets:**
- CRISIS occupancy: expect ≤ 4% (rare confluence + rare GAP-crisis, × 9c dwell).
- STRESS+CRISIS occupancy: expect ≤ 15%, honest range 6–15%. **Primary residual risk** — if onset
  transforms retain more persistence than expected or confluence co-fires broadly across minor
  wobbles, the 12c de-escalation multiplier could still push this over 15%.
- Distinct CRISIS entries: expect 6–9. **TIGHTEST budget / second residual risk** — genuine
  ≥12%-BTC-8h events plus ≥2-crisis-confluence events over 4.5y could plausibly reach 10–11; the
  5σ/12% GAP floor is the margin lever. If entries > 10, that is a FAIL.
- Off-episode CRISIS ≤ 1.5%: expect PASS (≥12% BTC 8h moves outside the pre-registered episode
  windows are rare).

**Disclosed residual limitation (acceptable):** onset transforms could miss a hypothetical
SLOW-BUILDING crisis with no sharp onset; no IS primary is of that type (all four are sharp onsets),
and GAP + confluence provide redundancy, so this is an acceptable, disclosed hole rather than a
falsification risk on the pre-registered episodes.

**Terminal commitment (restated):** CRISIS-FALSIFY-002 is scored against the UNCHANGED §2.4 bars.
If it PASSES, the machine is frozen as the shared infrastructure and the field proceeds (DIAG-J
first, §4). If it FAILS on ANY arm, the crisis-machine spec is FROZEN AS FAILED; the track either
runs GAP-only (the proven event-arrival component — a degraded but honest one-indicator machine) or
I escalate the design question to the user. No third machine, no budget move, no rescue.

*— QR, MN3 track, 2026-07-11. PLAN-AMENDMENT-001. This is the one permitted re-registration;
appended, not edited; frozen before CRISIS-FALSIFY-002 runs; the holdout remains untouched.*
