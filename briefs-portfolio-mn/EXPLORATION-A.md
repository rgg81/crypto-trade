# EXPLORATION-A — Funding-Carry Beta-Neutral Basket (engine backtest; IS-only; pre-registered)

## Section 0 — Provenance & scope (pre-registration)

- **Frozen:** 2026-07-10, BEFORE any engine backtest runs. This brief is the frozen contract; the QE
  runs the matrix ONCE and the results are scored against the gates below. **No post-hoc tuning** —
  any change to construction, variants, gates, predictions, decision map, or reveal logic after the
  run invalidates the pre-registration and must be recorded as a new EXPLORATION.
- **Track:** baseline-BLIND MARKET-NEUTRAL portfolio (worktree `quant-portfolio-blind`). Charter
  `ORCHESTRATOR_BRIEF_MN.md`; PLAN `diary-portfolio-mn/PLAN.md` §2 Sketch A (binding); predecessor
  DIAGNOSTIC `diary-portfolio-mn/DIAGNOSTIC-A-funding-carry.md` (committed 584295a4 — SURVIVES on
  all three kill criteria).
- **BASELINE-BLINDING intact.** Designed against `mn_*` / `blind_*` infrastructure + DIAG-A only.
  **No baseline artifact read** (`BASELINE_PORTFOLIO.md`, `analysis/portfolio/iter_*.py`,
  `diary-portfolio-top20/`, `CONFIRMATION-005.md`, sibling worktrees — none touched). The old
  vol_low / mid-vol family is CLOSED; no signal is inherited from it. `briefs-portfolio-blind/
  EXPLORATION-006/007` were read for FORMAT/METHODOLOGY only (staggered-rebal ensemble, honesty
  section, gate/decision-map structure) — never for signals.
- **MN SPLIT — this is an IS-ONLY phase end to end. There is NO holdout reveal in EXPLORATION-A.**
  `MN_IS_CUTOFF = 2026-01-01` (`mn_split.py`) is SEALED; every number is computed on candles
  `open_time < MN_IS_CUTOFF` via `mn_slice_is`. `mn_guard_grid` is asserted at the top of the QE
  script (raises on any holdout overlap). The old-track `blind_universe.is_mask` / `OOS_CUTOFF =
  2025-03-24` / `blind_sanity_lowvol.slice_is` are the WRONG split and MUST NOT be used. Verdict
  semantics below are **IS design-validation only**, explicitly NOT a deployability claim.
- **Backtests run by this QR: ZERO.** The QE runs the frozen matrix; no side-probes.
- **Contamination disclosure (charter §5, PLAN §5.4):** every headline is reported WITH and WITHOUT
  the 2025-03→2025-12 IS sub-window. DIAG-A's edge was STRONGER ex-window (net higher at all
  cadences); a result that only exists in the revealed sub-window is discounted.

### 0.1 Design thesis (one paragraph)

DIAG-A established, IS-only, that a cross-sectional funding sort has a genuine, persistent,
cost-surviving edge: decile IC −0.0194 (t −7.59), near-monotone deciles, D1−D10 net spread +164%
(rebal=3) / +131% (rebal=21) annualized after honest costs, funding-leg positive in ALL six IS
years, no aggregate price giveback (−54.6%), and — critically — it did NOT die on the crash-loss
falsifier (CRASH mean −9.43 bps, t −0.58, insignificant). What DIAG-A did NOT establish, and what
this exploration tests, are the three things that decide whether a *tradeable market-neutral book*
exists: (1) does the edge survive translation from an equal-weight decile PROBE into the engine's
rank-weighted, dollar-neutral, per-name-capped, liquidity-floored, BTC/ETH-hedged, staggered-weekly
BOOK, net of the hedge's own cost+funding drag; (2) does the engine hedge overlay drive realized
beta inside the charter neutrality gate — **especially the crash-conditional β_BTC, which DIAG-A's
static per-name residualization left at +0.172, ABOVE the G2 bound of 0.15** (the anti-predecessor
gate, and the pre-registered expected failure point); (3) does the book stand on the DURABLE
component — the funding leg alone — rather than on the 2020-21 price pop that has decayed to
negative in the recent era. The construction below is the funding-carry basket built as an engine
book; the variants isolate the hedge's contribution, the floor/cap's P&L cost, and the funding-only
durability base case; the gates bind on neutrality and durability, not on a headline Sharpe level.

---

## Section 1 — Construction (FROZEN)

The book is a **rank-weighted, dollar-neutral, BTC/ETH-hedged funding-carry basket**, run through
the UNCHANGED `blind_engine.run_backtest` (the leak-proven engine; the HedgeOverlay is already
implemented per PLAN §4.1 and is byte-identical-inert when `hedge_overlay=None`). All parameters
below are frozen.

**1.1 Signal (single source of truth = DIAG-A).**
- Import `build_signal` from `mn_diag_a_funding` verbatim: `S[t,i]` = trailing 9-candle (3d) mean of
  the cross-sectional funding z-score over current universe members (min 5 of 9 finite), known at
  `close[t]`. **This is the committed DIAG-A signal; do not reimplement.**
- **Engine sign:** `blind_engine.target_weights` longs the HIGHEST signal. DIAG-A's sort longs the
  LOWEST funding (D1). Therefore pass **`signal_engine = -S`** so high engine-signal ⇔ low/negative
  funding ⇔ LONG (collect from crowded shorts); low engine-signal ⇔ high funding ⇔ SHORT (collect
  from crowded longs). The QE asserts `signal_engine = -build_signal(...)` (one line, pinned).

**1.2 Universe (PIT top-N + liquidity floor).**
- Base: `build_universe(panel, top_n=N)` from `mn_diag_a_funding` — PIT top-N by trailing 30-candle
  mean $-volume, ex-stablecoins, with the ≥90d-history (270-candle) filter (NaN-mask a name's first
  270 candles of quote-volume before ranking — the DIAG-A machinery, reused verbatim).
- **N = 40 PRIMARY** (an MN cross-section needs breadth); **N = 20 robustness column** (both
  pre-registered in DIAG-A/PLAN — no other N is tried).
- **Liquidity floor (FROZEN, principle-anchored — NOT DIAG-A-fitted):** a universe member must ALSO
  have trailing 30-candle mean $-volume ≥ **$3,000,000 per 8h candle**. Rationale: below ~$3M/8h a
  rank-weighted leg cannot be filled at the assumed 2.5bps slippage — this is an execution-realism
  floor, disclosed as a principle bound, not tuned to any result. Implemented in the universe
  builder as a boolean AND on the trailing-$-vol array (same array `pit_topn_universe` already
  computes); the QE reports mean members/candle before and after the floor.

**1.3 Weighting + per-name cap.**
- `weighting="rank_neutral"`, `gross=1.0` (sum|w_alpha|=1, sum(w_alpha)=0). Rank weighting is
  robust to funding-magnitude outliers by construction (ranks, not raw z) — this alone reduces the
  DIAG-A equal-weight-decile ALPACA concentration (15.3% of decile P&L) to a rank-bounded ~5%/name
  at N=40.
- **Per-name weight cap (FROZEN):** `|w_alpha,i| ≤ 0.10 × gross`; any excess is redistributed
  pro-rata across the SAME leg's remaining names (preserves sum(w)=0 and sum|w|=gross). Rationale:
  no single name may carry >10% of gross in a book that claims all-conditions neutrality — an
  ALPACA-class delisting squeeze must never become 15% of P&L. At N=40 the cap binds rarely (rank
  max ~5%); at N=20 it binds more — measured, not assumed. Implemented as a post-process on
  `target_weights` output applied at each rebal BEFORE the hedge overlay (so the hedge is sized on
  the capped alpha book). The QE reports the cap's bind-rate (fraction of rebals where any name was
  clipped) and the mean redistributed notional.

**1.4 Cadence — WEEKLY as a 21-phase TRANCHE ENSEMBLE (charter §6; single-phase headlines BANNED).**
- `rebal = 21` (weekly on 8h candles). DIAG-A persistence (sort AR(1) ρ=0.988, half-life 56 candles
  ≈ 18.7 days) makes weekly signal-compatible, and weekly minimizes turnover/cost (DIAG-A rebal=21
  decile turnover 145×/yr vs 478× at rebal=3).
- **Ensemble:** for `p in range(21)`, run the full pipeline on `trim_panel(pis, p)` (front-trim p
  candles — phase offset), map each tranche's per-candle `rets` / `turnover` / `funding_rets` /
  hedge series onto the ORIGINAL IS grid by `grid_ms` (via `map_to_grid`), and take the
  **equal-weight (1/21) mean return stream on the common warmup slice** (`common_metric_mask`).
  The headline IS the phase-agnostic mean — equal-weight over all 21 phases is the one aggregation
  that selects nothing (no phase is chosen). Machinery: reuse the pure aggregation helpers
  `map_to_grid`, `common_metric_mask`, `ensemble_result`, `ann_vol`, `dd_path`,
  `ensemble_monthly_table` from `blind_exploration_007` (signal-agnostic math) and `trim_panel` from
  `blind_paper_l1` (pure front-trim) — **but the IS slice is `mn_slice_is`, NOT `slice_is`.** If any
  of those helpers transitively imports old-track signal code at module load, the QE re-implements
  the ~10-line helper locally rather than import it (blinding takes precedence over reuse).

**1.5 Hedge overlay (ARMED — the §4.1 BTC/ETH HedgeOverlay, exact engine semantics).**
- `beta_btc = mn_beta.rolling_beta(panel)` frozen defaults (window=270, min_periods=135, shrink
  λ=0.33, clip [0,3], BTC self-beta identity-pinned to 1). `beta_eth_resid =
  mn_beta.rolling_residual_beta(panel, ref="ETHUSDT", base="BTCUSDT")` frozen defaults.
- `HedgeOverlay(beta_btc=…, beta_eth_resid=…, eth_arm_threshold=0.10, eth_beta_window=270)`.
  Engine semantics (cited from `blind_engine._hedge_target_row` / `_eth_arming`, verbatim): at each
  rebal k, after the capped alpha weights `w` are built, `h_eth = -Σ w_i·βᵉᵗʰ_i[k-1]` is added ONLY
  when the ETH arming rule fires — the trailing 270-candle realized OLS beta of the book's OWN net
  returns on ETH hold-returns exceeds 0.10 in |·| (≥135 finite pairs required); then
  `h_btc = -(Σ w_i·βᴮᵀᶜ_i[k-1] + h_eth·βᴮᵀᶜ_ETH[k-1])` cancels total BTC-factor exposure INCLUDING
  the ETH leg's own BTC beta (β_BTC,BTC≡1). Any non-finite beta or invalid hedge fill price makes
  that leg INERT for the rebal (never NaN); counts land in `metrics["n_hedge_skipped_rebal"]` /
  `metrics["n_eth_armed_rebal"]`. Hedge legs pay taker+slip on their turnover and funding like any
  position; `weights`/`gross_leverage`/`turnover`/`funding_rets` INCLUDE them (so G3 measures the
  post-hedge book). Betas are consumed at [k-1] (the engine's standard decision lag).
- **Beta arrays per tranche:** compute `rolling_beta` / `rolling_residual_beta` on `trim_panel(pis,
  p)` for each tranche (shape (T-p, C)). The QE MAY instead compute betas once on the full IS panel
  and front-trim-align IF it first asserts trim-invariance on the common slice (bit-identical betas
  for a spot phase p>0 vs untrimmed on overlapping grid_ms); otherwise compute per-tranche.

**1.6 Costs.** `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)`; funding =
`blind_funding.load_funding(panel)` on every perp leg (alpha AND hedge). **2×-cost twin** on every
cell: `CostModel(10.0, 5.0, True)`. Because `rank_neutral` uses no vol-target / dd-brake / gross
scalar, target weights are cost-invariant, so the 2× twin is the exact analytic
`rets_2x[t] = rets_1x[t] − turnover[t]·cost_side` (verified elementwise ≤1e-12 on one spot tranche
against a real `CostModel(10,5,True)` re-run, per the /007 identity) — no extra full re-runs needed.

**1.7 Net/gross budgets.** Alpha book is dollar-neutral (Σw_alpha=0, gross=1.0). Hedge legs add
net exposure ≈ −book_beta (small); total gross and net EXPOSURE are reported post-hedge and gated by
G3. No leverage beyond the hedge legs; `max_lev` left at engine default (hedge notional is small
relative to gross).

---

## Section 2 — Variants (FROZEN list — a small one-factor-at-a-time star, each cell justified)

The PRIMARY candidate is **Cell 1**. Cells 2 and 3 each change exactly ONE axis from Cell 1, so each
axis's contribution is isolated cleanly (a full 2×2 would add a fourth cell that answers no
additional question). All cells are the 21-phase weekly ensemble at N=40 unless noted.

| Cell | Hedge | Floor+Cap | N | Purpose |
|---|---|---|---|---|
| **1 (PRIMARY)** | ARMED (BTC + ETH-arm) | ON | 40 | the candidate market-neutral carry book |
| **2** | ARMED | **OFF** | 40 | measures the liquidity-floor + per-name-cap P&L COST (how much edge lives in the illiquid/tail names) |
| **3** | **OFF** (`hedge_overlay=None`) | ON | 40 | measures the hedge's cost drag AND its neutrality contribution (unhedged realized beta vs Cell 1) |
| **1-N20** | ARMED | ON | 20 | pre-registered robustness column on the PRIMARY (DIAG-A both-N mandate) |

**Funding-leg-only base case (within-run attribution, NOT a separate backtest).** The engine reports
`funding_rets` separately, so each cell yields two P&L lenses on the SAME positions: (i) TOTAL return
(price + funding − cost), and (ii) the **funding-only return stream** (`funding_rets` alone, same
weights). The funding-only lens operationalizes DIAG-A's "durable component" recommendation — it is
the conservative sizing base case (credit zero price mean-reversion). It is reported for every cell
and it drives the durability sub-gate G-durable (§4). No extra runs.

**Compute footprint:** 4 constructions × 21 tranche runs = **84 backtests** + analytic 2× twins
(post-processing). All on the IS slice — fast; no long-run flag. (Cell 1-N20 shares nothing with the
N=40 cells' warmup, so it is a full 21-tranche run of its own.)

---

## Section 3 — Pre-registered predictions (point + bands; scored after the run)

Derived from DIAG-A where a number exists; **WIDE bands on the genuine unknowns** (the decile-probe →
rank-book translation, the hedge's cost/funding drag, the cap/floor haircut) — the /007 `rho_bar`
lesson: honest bands, not false precision. All refer to Cell 1 (PRIMARY, hedged, floor+cap, N=40,
weekly ensemble, honest cost) unless noted.

| Quantity | Point | Band | Reasoning |
|---|---:|---|---|
| **Net ensemble Sharpe (headline)** | +0.9 | **[+0.4, +1.6]** | DIAG-A decile gross ann-Sharpe ≈1.5; rank-weighting spreads bets (lower), hedge+cost drag subtracts, floor/cap ambiguous → wide |
| **Funding-only Sharpe (durable base)** | +0.7 | [+0.3, +1.2] | funding leg positive all 6 IS years; lower vol than total → Sharpe can exceed total's lower band |
| **Net vol (annualized)** | 12% | [7%, 20%] | rank+cap book far tamer than the 409bps/candle decile probe (equal-weight squeeze exposure removed) |
| **maxDD** | −15% | **[−8%, −28%]** | hedge removes crash-beta drag; cap removes single-name blowups; but CRASH price-leg bleed persists |
| **2×-cost net Sharpe** | +0.7 | [+0.2, +1.4] | weekly turnover low; same per-doubling drag as 1× |
| **Turnover (ann one-way, ensemble)** | 140× | [90×, 200×] | DIAG-A rebal=21 decile 145×; rank book similar-or-lower; hedge adds a little |
| **Rolling 270 β_BTC (G1a)** | +0.02 | [−0.05, +0.08] | DIAG-A raw full-sample β −0.055, residual +0.006; hedge tightens → G1a likely PASS |
| **CRASH-conditional β_BTC after hedge (G2 crux)** | +0.08 | **[−0.05, +0.20]** | DIAG-A static-residual CRASH β +0.172 > 0.15; engine hedge uses the SAME trailing beta (under-estimates crash beta) → band STRADDLES the 0.15 bound. G2-CRASH is a coin-flip-to-likely-fail |
| **CRASH-bucket net mean (G4 crux)** | ≈0 | t ∈ [−1.2, +0.6] | DIAG-A decile CRASH −9.4 bps t−0.58; hedge lifts it (removes +crash-beta drag) but price-leg bleed persists → G4 (t>−1.0) is the second risk |
| **MANIA-bucket net mean** | +0.8%/mo | [+0.2%, +1.6%] | DIAG-A decile MANIA +37.6 bps/candle t+3.36 (strongest bucket); rank-scaled down |
| **Min per-year Sharpe** | +0.1 | 2024 the thin/negative year | DIAG-A 2024 decile −37% (funding compression); may be the one sub-zero year |
| **Cap bind-rate (fraction of rebals)** | 8% | [2%, 25%] | rank max ~5% at N=40 → binds rarely; N=20 higher |
| **ETH-armed rebal fraction** | 20% | [5%, 50%] | ETH residual exposure is intermittent; arms only when book ETH-beta >0.10 |

**Modal outcome I expect:** the performance floors (Sharpe/2×-cost/turnover/maxDD) PASS; the
discriminating risks are the two NEUTRALITY gates — **G2-CRASH** (crash β may stay >0.15) and **G4**
(CRASH-bucket t may fall below −1.0). The information in this exploration is whether the engine hedge
overlay converts DIAG-A's +0.172 crash residual-beta into a gate-passing realized crash beta. The
funding-only durability sub-gate is expected to pass (funding leg had no losing IS year).

---

## Section 4 — Pre-registered GATES (frozen thresholds, IS-only, common warmup slice)

Evaluated on **Cell 1 (PRIMARY)** unless a gate names another cell. G1–G5 are the charter neutrality
gate (PLAN §1.3) VERBATIM. Performance floors are principle-anchored (NO absolute floor derived from
a single DIAG-A draw — the /007 G-crash lesson); a passing floor certifies "the mechanism survived
engine+hedge+cost translation," NOT a discovery. **HARD = fail ⇒ candidate does NOT proceed to the
family-A holdout reveal. SOFT = report + set SUCCESS/PARTIAL tier.**

| # | Gate | Metric | Threshold | H/S |
|---|---|---|---|---|
| **G1a** | rolling 270-candle β vs BTC (book net returns) | \|β\| ≤ 0.10 on ≥95% of post-warmup candles **AND** max \|β\| ≤ 0.20 | **HARD** |
| **G1b** | rolling 270-candle β vs ETH | \|β\| ≤ 0.15 on ≥95% **AND** max \|β\| ≤ 0.25 | **HARD** |
| **G2** | bucket-conditional β vs BTC, **CRASH** and **MANIA** separately (OLS of book net return on BTC 8h return within each `mn_regimes` bucket) | \|β\| ≤ 0.15 **each** | **HARD** |
| **G3** | net exposure at every rebal, post-hedge (hedge legs included) | \|Σw\| ≤ 0.10 × gross at every rebal | **HARD** |
| **G4** | worst-bucket mean net return t-stat (CRASH/MANIA/CHOP) | t > **−1.0** | **HARD** |
| **G5** | bucket P&L concentration | no bucket > 60% of total P&L | SOFT |
| **G-sharpe-floor** | net ensemble Sharpe | ≥ **+0.35** | **HARD** |
| G-sharpe-target | net ensemble Sharpe | ≥ +0.90 | SOFT |
| **G-durable** | funding-only ensemble Sharpe (Cell 1) **AND** funding-only positive in ≥5 of 6 IS years | Sharpe ≥ **+0.25 AND ≥5/6 yrs > 0** | **HARD** |
| **G-2xcost** | 2×-cost net ensemble Sharpe | > **0 AND ≥ 0.5 × (1× Sharpe)** | **HARD** |
| G-2xcost-target | 2×-cost net Sharpe | ≥ +0.60 | SOFT |
| **G-maxdd** | ensemble maxDD | ≥ **−25%** | **HARD** |
| G-maxdd-target | ensemble maxDD | ≥ −15% | SOFT |
| **G-turnover** | ensemble turnover (ann one-way) | ≤ **250×/yr** | **HARD** |
| **G-sample** | rebals with a live book (per tranche) **AND** distinct names ever traded | ≥ 200 rebals AND ≥ 40 names | **HARD** |
| G-contam | net Sharpe EXCLUDING 2025-03→2025-12 | ≥ 0.7 × full-IS Sharpe (report; if the edge collapses ex-window, discount) | SOFT |

**11 HARD** = {G1a, G1b, G2, G3, G4, G-sharpe-floor, G-durable, G-2xcost, G-maxdd, G-turnover,
G-sample}; **5 SOFT** = {G5, G-sharpe-target, G-2xcost-target, G-maxdd-target, G-contam}.

**Floor rationale (principle, not DIAG-A-fitted):** G-sharpe-floor +0.35 and G-durable +0.25 are set
where they catch "the carry mechanism did NOT survive engine translation" (an MN book below ~0.35
net Sharpe after honest cost does not justify the neutrality machinery over a simpler book), NOT
where DIAG-A's decile number sits — passing them is not a discovery. G-maxdd −25% encodes "an
all-conditions MN book must not draw down like an equity bet." G-turnover 250× is a cost-fragility
ceiling. These bands are disclosed as principle-anchored; the realized numbers are predicted with
WIDE bands in §3 precisely because they are genuine unknowns.

**Reference note for G2/G4:** report the CRASH/MANIA/CHOP breakdown for BOTH Cell 1 (hedged) and
Cell 3 (unhedged) so the hedge's neutrality contribution is attributable (Cell 3 crash β − Cell 1
crash β = the overlay's crash-beta reduction). The `mn_regimes` buckets are FROZEN (occupancy
already validated in DIAG-A: CRASH 11.5% / MANIA 15.7% / CHOP 72.7%) — never redefined here.

---

## Section 4.5 — G2-CRASH CONTINGENCY (pre-registered — the coordinator's explicit ask)

DIAG-A left crash-conditional residual β_BTC at **+0.172 > 0.15**; §3 predicts the engine-hedged
crash β at +0.08 with band [−0.05, +0.20] — **G2-CRASH is the expected failure point.** The
disposition is frozen NOW so it is not tailored to the outcome:

1. **If Cell 1 PASSES G2-CRASH (and all other HARD):** SUCCESS/PARTIAL per §5 — proceed toward the
   family-A holdout reveal.
2. **If Cell 1 FAILS G2-CRASH (crash \|β_BTC\| > 0.15) but the mechanism is otherwise intact**
   (G-sharpe-floor, G-durable, G-2xcost pass; the edge is real, only the NEUTRALIZATION failed):
   this is **NOT a family kill** — the funding-carry MECHANISM survived DIAG-A; the failure is in
   the hedge ENGINEERING, a named, bounded problem. It triggers **exactly ONE** named follow-up,
   **EXPLORATION-A2**, which pre-registers (BEFORE seeing its result) a SPECIFIC richer neutralizer
   targeting crash beta — the candidate remedy is a **crash-conditional / downside beta** (a
   shorter-window or downside-only `rolling_beta` engaged in the CRASH bucket, since trailing
   270-candle shrunk betas under-estimate the crash-state beta that leaks the +0.172), with
   crash-β reduction as the pre-registered falsification arm. A2 is a HEDGE (risk-primitive) change
   only — the SIGNAL, universe, cap, floor, and cadence stay byte-frozen from this brief, so A2 is
   not alpha-mining and does not re-open selection. A2 counts +1 in the family-A n_eff ledger.
3. **If A2 ALSO fails G2-CRASH:** the funding-carry family is declared **NOT market-neutralizable by
   static/simple overlays** — a genuine, documented NEGATIVE finding. The family-A holdout reveal is
   **NOT spent**; the sketch is shelved for the MN mandate (it may earn carry but cannot meet the
   anti-predecessor neutrality bar, which is the whole point of this track). **This bounds the hedge
   search to ONE retry** — no infinite hedge-tuning loop. NO third attempt without a new,
   independently-motivated mechanism (not a re-parameterization).
4. **If Cell 1 fails G2-CRASH AND the mechanism is also weak** (G-sharpe-floor or G-durable fails):
   no A2 — the construction simply FAILS; localize and document (§5).

**No post-hoc re-gating (charter §5, PLAN §5.7):** re-tuning the SIGNAL/universe/cap after seeing any
gate is a process violation. A2 is the ONLY sanctioned response to a G2-CRASH failure, it changes
ONLY the risk-primitive, and it is bounded to one attempt.

---

## Section 5 — Frozen decision map (IS design-validation only; NO holdout reveal)

**Discriminating axis = NEUTRALITY (G1–G4), not the Sharpe level** (the level is a genuine unknown
with a wide §3 band, floored only to catch non-survival). The performance SOFT targets are
prediction-scoring lines, not tier-determining.

| Outcome | Condition | Interpretation |
|---|---|---|
| **SUCCESS** | ALL 11 HARD pass on Cell 1 (incl. G2-CRASH, G4, G-durable) | The funding-carry basket is an **IS-design-validated market-neutral candidate** — realized beta inside the charter gate in every regime incl. crash, edge durable on the funding leg, cost-robust. Becomes the **candidate for the family-A holdout reveal** (a FUTURE CONFIRMATION, after §5.1 robustness is documented). **NOT a deployment decision.** |
| **PARTIAL** | ALL neutrality HARD (G1a,G1b,G2,G3,G4) pass **BUT** a performance HARD (G-sharpe-floor / G-durable / G-2xcost / G-maxdd / G-turnover / G-sample) fails | The book is genuinely neutral but not yet a clean candidate (edge too thin, cost-fragile, or too concentrated after the cap). Documented; the specific failed floor names the next iteration's target (e.g., faster cadence for durability, tighter floor for liquidity). NOT revealed. |
| **FAIL — G2-CRASH** | G2-CRASH fails | → §4.5 contingency (A2, ONE retry) if mechanism intact; else localize. NOT revealed. |
| **FAIL — other neutrality HARD** | G1a/G1b/G3/G4 fails (not G2-CRASH) | The overlay does not neutralize as designed (full-sample or ETH beta, net exposure, or a bucket loses significantly). Localize; document; NOT revealed; no automatic A2. |

**5.1 What SUCCESS means (IS-scoped) + reveal protocol.** SUCCESS makes Cell 1 the family-A
holdout-reveal candidate — an IS design verdict, NOT deployability. **The holdout stays SEALED in
this exploration.** The reveal is spent ONCE per family, ever (PLAN §5.2), only at a future
CONFIRMATION-A, and only after IS robustness is documented: phase-offset distribution (all 21, the
headline is the mean — already built as the ensemble), 2×-cost twin (built here), regime buckets
(built here), the contamination twin (built here), and a window/seed-stability check as applicable.
The reveal, when sanctioned, is the single call `mn_guard_holdout(lo, hi,
confirmation_reveal="funding-carry")` — the loud audit banner is the record; a second reveal for
family A is a violation. **This brief does NOT authorize any reveal; the QE script never passes
`confirmation_reveal`.**

**5.2 Cross-cutting.** Regardless of tier, the Cell 1 vs Cell 3 (hedged vs unhedged) crash-beta
delta and the funding-only-vs-total decomposition are the two most informative new numbers for the
track — they quantify, IS-only, how much neutrality the overlay buys and how much of the edge is the
durable carry vs the decaying price pop.

---

## Section 6 — Multiple-testing honesty (family-A n_eff ledger)

- DIAG-A booked **3 cadence cells** (rebal ∈ {1,3,21}) — no best-of-k selection (all reported, kill
  criteria pre-registered).
- This exploration adds **3 pre-committed construction cells** (Cell 1/2/3; the PRIMARY is
  pre-DESIGNATED as hedged+floor/cap, NOT chosen as best-of-3) + the N=20 robustness column (a
  robustness check, not a selection) + **1 researcher-DOF** (decide to build the engine book +
  fix the floor/cap/cadence constants). No parameter is tuned; no phase is selected (equal-weight
  ensemble selects nothing). **Family-A running n_eff ≈ 3 + 3 + 1 ≈ 7.**
- The §4.5 contingency A2, if triggered, adds **+1** (a single pre-committed risk-primitive retry),
  → n_eff ≈ 8.
- **Critic haircut instruction:** apply a DSR/deflation consistent with family-A n_eff ≈ 7 to any
  Sharpe reported. **BUT** this is IS-only with NO holdout reveal, so per the track's EXPLORATION-mode
  convention the deflation is **informational only** — it sizes expectations for the future
  CONFIRMATION-A, it does not gate the IS design-validation verdict.

---

## Section 7 — QE deliverables spec

**Script:** `analysis/portfolio/mn_exploration_a.py`. **No verdicts — tables + mechanical pass/fail
only** (verdict rendering is the QR's Phase-7 job).

**Reuse VERBATIM (single source of truth, no reimplementation):** `build_signal`, `build_universe`,
`TOP_N_PRIMARY`, `TOP_N_ROBUST` from `mn_diag_a_funding`; `rolling_beta`, `rolling_residual_beta`
from `mn_beta`; `load_funding` from `blind_funding`; `mn_regime_labels`, `regime_occupancy` from
`mn_regimes`; `run_backtest`, `CostModel`, `HedgeOverlay`, `target_weights`, `_metrics`,
`PERIODS_PER_YEAR` from `blind_engine`; `load_panel`, `Panel` from `blind_universe`;
`mn_slice_is`, `mn_guard_grid`, `MN_IS_CUTOFF_MS`, `MN_STEP_MS` from `mn_split`;
`mn_panel_health`, `MnDataError` from `mn_datacheck`; the pure ensemble helpers (`map_to_grid`,
`common_metric_mask`, `ensemble_result`, `ann_vol`, `dd_path`, `ensemble_monthly_table`) from
`blind_exploration_007` and `trim_panel` from `blind_paper_l1` **IF they import cleanly without
executing old-track signal code — otherwise re-implement locally** (blinding > reuse).

**Top-of-script hard order (ABORT on any failure):**
1. `mn_panel_health()` FIRST (charter §4); abort on `MnDataError`.
2. `pis = mn_slice_is(load_panel())`; `mn_guard_grid(pis.grid_ms)`; assert
   `int(pis.grid_ms[-1]) + MN_STEP_MS <= MN_IS_CUTOFF_MS`. **Never** import/call
   `blind_universe.is_mask`, `OOS_CUTOFF*`, or `blind_sanity_lowvol.slice_is` (wrong split).
3. Assert `signal_engine = -build_signal(fund, univ)` element-for-element (the sign pin, §1.1).

**Per-name cap + liquidity floor:** implement as specified (§1.2/§1.3); assert sum(w)=0 and
sum|w|=gross (±1e-12) after capping+redistribution; report cap bind-rate and floor's members/candle
before/after.

**Ensemble build (frozen, exact):** for each of the 4 constructions, run 21 front-trimmed tranches,
map by `grid_ms` (assert exact alignment via `map_to_grid`'s built-in assert), take the 1/21
equal-weight return + leg + funding streams on the common warmup slice, wrap via `ensemble_result`
and metric via `_metrics`. Warmup = the beta warmup (betas start ~candle 135; the residual-ETH beta
starts later ~2×min_periods) — set the common-slice warmup so ALL tranches AND all betas are valid;
assert the common mask's first-True index is stable and report it.

**2×-cost twin (analytic, exact):** `rets_2x[t] = rets_1x[t] − turnover[t]·cost_side` per tranche,
then ensemble identically. **Assert** the analytic 2× reproduces one real `CostModel(10,5,True)`
re-run on tranche 0 (Cell 1) — elementwise ≤1e-12 on per-candle rets, ~1e-12 on recompounded Sharpe.
(Valid because `rank_neutral` has no cost-dependent controls → weights cost-invariant.)

**Internal reproducibility asserts (no parity anchor exists for this construction — pin these
instead):**
- **Bit-identical re-run:** running the full matrix twice yields byte-identical headline metrics
  (the DIAG-A script already reproduced bit-identically — same determinism expected here).
- **Leg reconciliation:** per tranche, `funding_rets` + price P&L − tcost ≡ `rets` to ≤1e-12
  (the engine's own attribution identity); assert on every tranche.
- **Hedge-inert control:** Cell 3 with `hedge_overlay=None` must equal a run with an all-zero-beta
  HedgeOverlay to ≤1e-12 on rets (the overlay's documented inert-default byte-identity) — a spot
  check on one tranche is enough.
- **IS-guard:** `mn_guard_grid` on every tranche's grid (front-trim only touches the front; the
  holdout boundary is never crossed).

**Leak test for the funding-sort signal (corrupt-future positive control, house style):** on a spot
tranche, corrupt `fund[t:, :]` (set to ±large) and assert `signal_engine[:t]` is bit-identical to
the uncorrupted build (the 3d-mean funding-z at candle s<t uses only fund ≤ s). Pin as an assert in
the script (the `mn_beta` corrupt-future control already exists for betas; this adds the signal
series). Report PASS.

**Required tables (observations only):**
1. **Headline block per cell** (1, 2, 3, 1-N20): net ensemble Sharpe (honest cost), funding-only
   Sharpe, 2×-cost Sharpe, ann vol, maxDD, turnover (ann one-way), ann return, monthly win rate,
   top-name P&L concentration share.
2. **Neutrality block (Cell 1 AND Cell 3):** rolling-270 β_BTC / β_ETH — fraction of candles inside
   the G1a/G1b bounds + max |β|; bucket-conditional β_BTC for CRASH / MANIA / CHOP (with n and se);
   G3 max |Σw|/gross over rebals; `n_hedge_skipped_rebal`, `n_eth_armed_rebal`, ETH-armed fraction.
3. **Regime buckets (Cell 1 AND Cell 3):** CRASH/MANIA/CHOP mean net monthly return + t-stat + leg
   split (long_px / short_px / net_fund), and each bucket's share of total P&L (G5).
4. **Per-year ensemble Sharpe** {2020…2025} for Cell 1, TOTAL and funding-only (G-durable).
5. **Monthly table + worst-10 months** (Cell 1).
6. **Cap/floor cost:** Cell 1 vs Cell 2 headline delta (the floor+cap P&L cost) + Cell 1 cap
   bind-rate + members/candle before/after floor + the single-name concentration under each.
7. **Contamination twin:** Cell 1 net Sharpe + bucket means WITH and WITHOUT 2025-03→2025-12.
8. **Gate scorecard:** all 16 gate lines (§4), each HARD/SOFT with mechanical pass/fail, plus the
   §3 prediction hit/miss for each predicted quantity. (No tier verdict — that is the QR.)

**Do NOT:** touch the holdout / pass `confirmation_reveal`; read any baseline/CONFIRMATION artifact
or sibling worktree; use the old-track split (`is_mask`/`OOS_CUTOFF`/`slice_is`); change any FROZEN
signal/universe/cap/floor/cadence/hedge parameter; select or weight any phase unequally; re-run or
re-tune after seeing results. Hand the report to the QR for Phase-7 IS evaluation. **There is no
holdout reveal in this phase.**

---

**FROZEN.** Construction (§1), variant list (§2), predictions (§3), gate thresholds (§4), the
G2-CRASH contingency (§4.5), the decision map + reveal protocol (§5), and the n_eff ledger (§6) are
locked as of 2026-07-10, pre-run. Any deviation is a new EXPLORATION.

*— QR, MN track, 2026-07-10.*
