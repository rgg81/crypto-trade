# team-08 — research brief

Two families researched. Family 1 (`t08-short-horizon-reversal-v2`) was falsified honestly —
its full pre-registration and negative result are preserved verbatim in PART B below.
Family 2 (`t08-oi-price-confirmation-v3`) is the ACTIVE family: team-08's one documented
pivot, registry-approved.

---

# PART A (ACTIVE) — t08-oi-price-confirmation-v3

> §A1–A6 are PRE-REGISTERED: written after the pivot approval and BEFORE any e04+ experiment
> was logged or run. The ledger continues at e04 (3/40 used by the falsified family).
> §A7 (results) and §A8 (QE SPEC) are appended after the ledgered experiments.

## A1. Economic mechanism

In perp markets every price move carries an observable **commitment signature** in open
interest — the market's positioning ledger, which spot markets do not have:

- **Price up + OI up** — new longs initiating against sellers; fresh capital committed above
  the old price. Reflexive continuation: the move attracts entrants who defend their basis.
- **Price down + OI up** — new shorts pressing; committed bearish capital. Continuation down.
- **Price up + OI down** — short-covering rally: forced buy-backs close positions; nobody new
  is long. No follow-through once covering exhausts.
- **Price down + OI down** — long-liquidation / deleveraging dump: positions closing, sellers
  self-exhausting. No committed follow-through.

My ledgered e01–e03 experiments (PART B) measured robust 8h–3d cross-sectional CONTINUATION
in this exact universe (fading it: gross −0.7…−2.5). This family rides that persistence ONLY
where the positioning ledger says the move is committed — the OI conditioning is the
load-bearing element, enforced by the integrity falsifier (A3-V2).

Funding expectation (pre-registered, testable): the e01 mirror implies the continuation book
COLLECTED funding in IS (the fade book paid −0.03…−0.08 cumulative unlevered) — plausibly a
short-squeeze artifact (recent winners with still-negative funding). Expect roughly neutral
to slightly positive funding P&L; report actual.

## A2. Data, coverage handicap, and the active window (ON THE RECORD)

- Primary panel: `aux["oi"]` (units). `aux["oi_value"]` NOT used (its Δlog confounds
  positioning change with price change).
- OI ≤ 0 → NaN. NaN-tolerance everywhere; names without OI history are flat, never errors.
- **Coverage handicap (declared at pivot):** OI breadth is honest only from ~Dec-2021. The
  Stage-1 board metric is the FULL 54-month IS Sharpe; flat early months dilute it (estimated
  ×~0.7 vs active-window Sharpe). `is_report.md` MUST carry BOTH numbers (full-window and
  active-window) — orchestrator requirement, on the record.
- **Active window (fixed by census e04, then frozen):** active_lo = first candle at which the
  trailing 84-candle median count of names with valid signal inputs (eligible ∧ OI valid ∧
  z-ΔOI computable at M=9) ≥ 10. All falsifier verdicts use [active_lo, IS_HI); the board
  number stays full-window.
- **OI-artifact rule (census-decided BEFORE any Sharpe is read):** oi.csv bar rows aggregate
  5-min metrics; variable snapshot counts per bar would fake ΔOI spikes. Census e04 measures
  the fraction of one-bar |Δlog OI| > 0.5 among valid observations. If > 0.5%, ALL subsequent
  experiments use OI := 3-candle rolling median of the raw panel; otherwise raw. Decided
  once, applied uniformly, never revisited.

## A3. Falsifier (pre-registered kill criteria; registered one-liner made precise)

All measured on the ACTIVE window at the evaluator unless stated.

- **V1 — no plateau:** Stage-B L×H grid has no connected region (adjacency ±1 grid step in L
  or H) of ≥3 configs with net@1x Sharpe ≥ 0.5 → dead.
- **V2 — integrity (conditioned-minus-unconditioned):** at the selected config, the
  OI-conditioned book must beat its price-only analog — same pipeline with the gate forced to
  1 (for S2: z-displacement alone), restricted to the SAME valid-OI name-candle set. If
  Sharpe_cond − Sharpe_uncond ≤ 0 @1x, the commitment signature is not load-bearing → dead.
- **V3 — stress:** selected config net@2x ≤ 0 → dead.
- **V4 — breadth:** active-window median names per side < 5 at the selected config, not
  fixable inside the pre-registered grid → dead.
- Regime honesty (report, not kill): per-bucket Sharpe over the covered tags (2022 bear, FTX
  chop, ETF bull, post-halving chop; earlier tags are outside OI coverage). Single-bucket
  concentration is reported prominently in `is_report.md`.
- Funding thesis (report, not kill): sign and size of funding P&L vs the A1 expectation.

## A4. Signal pipeline (order fixed) and parameter grid

Pipeline: OI clean (A2 rule) → ΔOI + displacement → structure score → eligibility mask →
cross-sectional transform → abs-sum normalization → EMA smoothing → raw weights.

Definitions:
- `r1 = close/close.shift(1) − 1`; `σ = r1.rolling(42, min_periods=21).std()`
- `retL = close/close.shift(L) − 1`; `zret = clip(retL/(σ·√L), ±3)`
- `doi_M = log(OI) − log(OI.shift(M))`;
  `zdoi = clip(doi_M / doi_M.rolling(90, min_periods=45).std(), ±3)`
- Rank transform: rank among valid ∧ eligible names, centered at (n+1)/2, abs-sum-normalized.

Structures (Stage A axis):
- **S1γ0 (confirm-only):** score = centered-rank(disp) × 1{doi_M > 0}; unconfirmed flat.
- **S1γ−1 (four-quadrant):** score = centered-rank(disp) × sign(doi_M); unconfirmed faded.
- **S2 (product):** score = zret × zdoi, row-demeaned over valid ∧ eligible,
  abs-sum-normalized (no rank — magnitude-sensitive by design).

| Axis | Grid | Rationale |
|---|---|---|
| Structure | {S1γ0, S1γ−1, S2} | Quadrant logic coarse→continuous; is the fade side additive or noise? |
| Displacement | {retL raw, zret σ-scaled} | Ledgered e02 showed σ-scaling strongly helps the continuation direction (the fade got worse: −0.7→−2.1 at L=3). |
| L (candles) | {6, 9, 18, 27} (2d–9d) | e01–e03 located continuation at 8h–3d; longer L trades slower (cost stack); OI-confirmation operates over days–weeks. |
| M (ΔOI window) | {L, max(3, round(L/3))} | Matched vs recent commitment; tested LAST (Stage C), default M=L. |
| H (EMA halflife) | {0, 2, 4, 8} | Turnover control; continuation is slow so smoothing is near-free. |

Fixed (no axis): rank kernel for S1 (ledgered e03 showed kernel choice second-order), vol
window 42/21, zdoi window 90/45, clips ±3.

## A5. Experiment plan (ledger e04+; aim ≤22 total incl. the 3 spent)

- **e04 — coverage census + artifact scan (no Sharpe read):** quarterly counts of eligible /
  OI-valid / signal-valid names; fixes active_lo; decides the A2 median-filter rule; checks
  oi vs oi_value availability equivalence. Feasibility gate: if the active window is < 24
  months, report to the orchestrator before proceeding.
- **e05 — Stage A structure selection:** 6 configs = {S1γ0, S1γ−1, S2} × {raw, σ-scaled} at
  fixed L=9, M=9, H=2. Choose best active net@1x.
- **e06 — Stage B plateau grid:** chosen structure; L × H (4×4), M=L. Plateau + selection
  rule (A6). V1/V3/V4 evaluated here.
- **e07 — Stage C ΔOI-window check:** M ∈ {L, max(3, round(L/3))} at the selected (L, H);
  switch only if Δ(net@1x) > 0.15.
- **e08 — Stage D verdict diagnostics:** V2 integrity criterion, regime table, funding/cost
  decomposition, full-window vs active-window dilution decomposition, breadth. Final
  falsifier verdict.

## A6. Selection rule (pre-registered)

1. Stage A picks structure+displacement by active net@1x (single decision, 6 candidates).
2. Stage B: plateau = maximal connected region with active net@1x ≥ 0.5, size ≥ 3 (else V1).
   Select within plateau: max net@2x; ties → lower ann. turnover → smaller L → smaller H.
3. Stage C may switch M only on Δ > 0.15 Sharpe.
4. No grid re-opening after results are seen. `is_report.md` numbers come ONLY from
   `team-run` on the final `strategy.py`.

## A7. Results (ledger e04–e08; scratch artifacts `out/scratch/results_e0{4..8}.json`)

**e04 census:** OI coverage is binary — exactly 1 valid name pre-Dec-2021, ~39–40 from
2022Q1. active_lo = **2022-01-01 08:00 UTC** (frozen; rule hit exactly). Active window =
30 months. Artifact fraction |ΔlogOI| > 0.5 = 0.078% < 0.5% → **no median filter** (worst
spikes are LUNA/SRM death events — real signal). `oi`/`oi_value` availability identical.

**e05 Stage A (L=9, M=9, H=2):** S1γ0+z wins (act@1x +0.879); S1γ0+raw +0.808;
S2 +0.555; S1γ−1 ≈ 0 — **the fade quadrants hurt**, consistent with e01–e03 (covering/
liquidation moves do not revert at 8h granularity; standing aside is correct). Funding P&L
positive (+0.08 cumulative unlevered), as the A1 expectation predicted.

**e06 Stage B (S1γ0+z, M=L), active net@1x / net@2x:**

| L\H | 0 | 2 | 4 | 8 |
|---|---|---|---|---|
| 6 | −0.710 / −2.117 | +0.092 / −0.512 | +0.251 / −0.193 | +0.210 / −0.121 |
| 9 | +0.446 / −0.834 | +0.879 / +0.283 | +0.919 / +0.494 | +0.741 / +0.436 |
| 18 | +0.629 / −0.138 | **+0.939 / +0.578** | +0.853 / +0.570 | +0.545 / +0.337 |
| 27 | +0.437 / −0.247 | +0.804 / +0.476 | +0.624 / +0.368 | +0.367 / +0.159 |

Plateau (act@1x ≥ 0.5, connected): 9 configs {(9,2),(9,4),(9,8),(18,0),(18,2),(18,4),(18,8),
(27,2),(27,4)} → **V1 PASS**. Selection (max act@2x): **(L=18, H=2)**, runner-up (18,4) at
0.570 — a plateau, not a spike.

**e07 Stage C:** M=6 degrades badly (+0.238 vs +0.939) → **M=18 stands** (matched window).

**e08 Stage D (integrity + diagnostics), selected config S1γ0, z, L=18, M=18, H=2:**
- **V2 conditioned-minus-unconditioned:** Δact@1x = **+0.035** (formal PASS; noise-level — 30
  monthly points have Sharpe SE ≈ ±0.4); Δact@2x = **+0.179**; maxDD −0.289 vs −0.385
  (conditioned better); chop bucket +0.07 vs −0.29. Neighbor (18,4): Δ@1x −0.044, Δ@2x
  +0.093. Inner-plateau (9,4): **Δ@1x +0.320, Δ@2x +0.493** — the commitment gate is
  strongly load-bearing at fresher displacement, marginal-at-1x for stale displacement.
  Reported plainly: the gate's value at the SELECTED config is primarily in stress-cost
  robustness, drawdown, and chop behavior, not in 1x mean.
- Regime (active window, @1x): bull +2.55, bear +0.75, chop +0.07 — positive in all three
  covered buckets, clearly bull-loaded (ETF-bull tag dominates). Reported prominently per A3.
- **Dilution decomposition (ON THE RECORD):** active +0.939 → full-window +0.460 @1x,
  factor ≈ 0.49 — WORSE than the ~0.7 declared at pivot (24 structurally-flat months out of
  54 hit both mean and the monthly-count). The board metric carries the full handicap.
- Funding thesis: CONFIRMED in sign — +0.086 cumulative unlevered funding collected at the
  selected config (registration expectation was neutral-to-slightly-positive).
- Breadth: 24 long / 15 short medians → **V4 PASS**. act@2x +0.578 > 0 → **V3 PASS**.

**Falsifier verdict: NO KILL — V1/V2/V3/V4 all pass** (V2 with the thin-margin caveat above,
disclosed for the Critic). Family proceeds to build. Ledger: 8/40 used.

## A8. QE SPEC — final, zero ambiguity

`strategy.py` must implement exactly this. One config, no options, no tuning left.

```
build_raw_weights(pn, aux) -> pd.DataFrame          # index = pn["close"].index, columns = pn["close"].columns

Constants: L = 18; M = 18; H = 2.0; MIN_NAMES = 10; VOL_WIN = 42; VOL_MINP = 21; CLIP = 3.0

1  close = pn["close"]                              # derive symbol set from THIS panel only
2  elig  = aux["eligibility"].reindex(index=close.index, columns=close.columns).fillna(False).astype(bool)
3  oi_r  = aux["oi"].reindex(index=close.index, columns=close.columns)
4  oi    = oi_r.where(oi_r > 0)                     # non-positive/missing OI -> NaN
5  r1    = close / close.shift(1) - 1.0
6  sig   = r1.rolling(VOL_WIN, min_periods=VOL_MINP).std()
7  retL  = close / close.shift(L) - 1.0
8  zret  = (retL / (sig * sqrt(L))).clip(-CLIP, CLIP)        # sqrt(L) = sqrt(18)
9  doi   = log(oi) - log(oi).shift(M)                        # np.log; NaN propagates
10 s     = zret.where(elig & doi.notna())                    # candidate set
11 rk    = s.rank(axis=1)                                    # pandas default (average) ranks
12 n     = rk.count(axis=1)
13 c     = rk.sub((n + 1) / 2.0, axis=0)                     # centered rank
14 gate  = (doi > 0).astype(float)                           # NaN -> False -> 0.0
15 score = c * gate
16 score = score.where(n >= MIN_NAMES broadcast row-wise)    # thin rows -> all-NaN (flat)
17 den   = score.abs().sum(axis=1).replace(0.0, nan)
18 w     = score.div(den, axis=0).fillna(0.0)
19 w     = w.ewm(halflife=H, adjust=True).mean()             # over the 0-filled panel
20 return w
```

Rules bound to the implementation:
- Imports: numpy, pandas (± math). `teamlib` optional. NOTHING else. No file/network access,
  no randomness (`aux["seed"]` unused), no ret_fwd, no hard-coded symbols or column counts.
- NaN semantics: every NaN anywhere → the name is simply flat at that candle. Row 16
  implements the A2 count-guard (also auto-flattens the 1-name pre-2022 era).
- Same-bar legality: close[t], oi[t], eligibility[t] are all same-bar inputs; the engine owns
  the decision lag. No additional shifting inside the strategy.
- Widening safety: reindex aux panels onto close's index/columns (steps 2–3); synthetic extra
  columns get False/NaN and stay flat.
- `test_strategy.py` (team-owned) must include at minimum: (a) future-corruption self-check —
  corrupt the LAST k rows of close/oi/eligibility and assert weights strictly before those
  rows are bit-identical; (b) determinism (two calls, identical output); (c) widening (add a
  synthetic column, no crash, original columns' weights unchanged); (d) all-NaN-OI tolerance
  (weights all zero, no exception).
- Scratch cross-check for the QE: `team-run` metrics must match, up to evaluator rounding,
  scratch row `["S1g0","z",18,18,2]` in `out/scratch/results_e06.json`
  (full-window @1x ≈ +0.460; active-window numbers per §A7).
- `is_report.md` MUST include: full-window AND active-window (lo = 2022-01-01 08:00 UTC)
  Sharpe at 1x and 2x, the dilution factor, the regime table with the bull-concentration
  caveat, breadth, turnover, funding P&L (thesis-confirmed note), and the V2 thin-margin
  disclosure. Numbers exclusively from `team-run` output artifacts.

---

# PART B (ARCHIVE) — t08-short-horizon-reversal-v2 — FALSIFIED

Family 1 (registry-approved, then falsified): **short-horizon cross-sectional overreaction
fade** — long recent extreme losers, short recent extreme winners, 1–3 day horizon, weekly
top-40 USDT-perp universe, 8h bars.

> Sections 1–5 were PRE-REGISTERED: written before any experiment was logged or run.
> Section 6 (results) was appended after the ledgered experiments.

## 1. Economic mechanism

Short-horizon crypto moves systematically overshoot because a large share of 8h–3d price
displacement is **forced flow, not information**:

- **Liquidation cascades** — perp leverage is recycled by liquidation engines; a move that
  breaches a cluster of liquidation prices generates mechanical market orders in the SAME
  direction, pushing price beyond any information-consistent level.
- **Margin stops and deleveraging** — discretionary leveraged traders are forced out at the
  worst prints; their exits are price-insensitive.
- **Retail chase** — aggressive taker flow follows a pump with hours-scale latency (social
  feeds), buying tops and selling bottoms.

The reversion agents are market-maker inventory mean-reversion and slower dip-buyer /
profit-taker flow, operating over the following 1–3 days. The effect should be strongest
exactly where trend-family signals break: high-volatility, cascade-rich regimes.

**Funding alignment (registered thesis, directly testable here):** recent winners tend to
carry positive funding (crowd is long them) and recent losers negative funding (crowd is
short). The reversal book — short winners, long losers — therefore tends to COLLECT funding
on both legs under the evaluator's native funding P&L (`−w·f`). This is a structural cushion
against this family's main adversary: turnover costs.

## 2. Expected behavior per regime tag

Engine scorecard buckets the fixed tags into {bull, bear, chop}. Expectations, pre-registered:

| Bucket | Tags | Expectation |
|---|---|---|
| bear | COVID crash, May-2021 crash, 2022 bear | **Strongest.** Cascades and capitulation overshoots are abundant; fade pays. |
| chop | FTX-aftermath, post-halving | **Good.** Range-bound cross-section mean-reverts; funding collection adds carry. |
| bull | 2020-21 bull, ATH run, ETF bull | **Weakest.** Shorting winners in reflexive melt-ups bleeds price P&L; partially cushioned by large positive funding collected on the short-winners leg. Near-zero to modestly positive acceptable. |

Prediction to check honestly: net Sharpe positive in ≥2 of 3 buckets, with bull the weakest.

## 3. Falsifier (pre-registered kill criteria)

- **F1 — no gross edge:** max GROSS Sharpe (cost_mult=0, slip_mult=0, funding OFF; pure price
  reversal) over the pre-registered L grid (rank kernel, no smoothing) **< 0.8** → family dead.
- **F2 — cost-kill:** F1 passes but NO config in the pre-registered grid (Section 4) reaches
  **net Sharpe @1x ≥ 0.5** → family dead. This is the gross-vs-net decomposition criterion:
  an edge that exists gross but cannot clear 1x costs after the best pre-registered smoothing
  is a documented negative — NOT an invitation to smooth beyond the registered horizon.
- **F3 — no plateau:** no connected region of **≥3 adjacent configs** in the final L×H grid
  with net@1x ≥ 0.5 (adjacency = ±1 grid step in L or H) → dead (isolated peak = overfit).
- **F4 — stress fragility:** the selected config has **net Sharpe @2x-stress ≤ 0** → dead.
- **F5 — regime concentration:** at the selected config, only ONE of {bull, bear, chop} has
  positive Sharpe AND the summed net P&L of the other two buckets is ≤ 0 → the registered
  "regime-agnostic" claim is false → dead (or documented pivot request).
- **F6 — breadth:** median active names per side < 5 at the selected config and no
  pre-registered kernel fixes it → invalid book → dead.

Informational (not a kill, but reported): the funding thesis — `total_funding_pnl > 0`
expected at the selected config; if negative, the registration's funding-alignment claim is
reported as falsified even if the strategy otherwise passes.

## 4. Parameter plan (ranges + rationale) — the complete pre-registered grid

Signal pipeline (order fixed): past-return → optional vol-normalization → eligibility mask →
cross-sectional kernel → weight normalization → optional EMA smoothing.

| Axis | Grid | Rationale |
|---|---|---|
| Lookback L (candles) | {1, 2, 3, 6, 9} | Registered horizon is 1–3 days = 3–9 candles; 1–2 probe the 8h–16h boundary where the effect should be strongest but turnover worst. |
| Vol-normalization | {none, σ-scaled} | σ-scaled = retL / (σ₁ · √L), σ₁ = rolling std of 1-candle returns, window 42 candles (14d), min_periods 21, same-bar. Overshoot is a sigma-unit phenomenon; scaling stops perennially-wild names from monopolizing the tails. |
| XS kernel | {centered-rank, winsorized-z (clip ±3), rank-cubed taper} | Rank is fat-tail robust; z preserves magnitude; rank-cubed emphasizes the extremes (where the overreaction lives) while staying continuous and breadth-safe. |
| EMA halflife H (candles) | {0, 1, 2, 4, 8} | Turnover control. Reversal alpha decays over ~3–9 candles, so H ≤ 8 (≈2.7d) preserves the family horizon. H > 8 is PROHIBITED (would drift the family toward medium-horizon reversal — over-smoothing guard). |

Exploration is staged (each stage fixes the previous stage's winner; full L×H grid re-run at
the end on the chosen kernel): existence → vol-norm → kernel → smoothing → final plateau grid.
Budgeted at ~6 ledgered experiments.

## 5. Selection rule (pre-registered)

1. On the chosen kernel/vol-norm (picked by net@1x in the staged runs), compute the FULL L×H
   grid at 1x and 2x.
2. Identify the maximal connected plateau with net@1x ≥ 0.5 (adjacency ±1 step in L or H).
   Plateau size must be ≥ 3 (else F3 fires).
3. Within the plateau, select the config **maximizing net@2x-stress Sharpe**; ties → lower
   annualized turnover; remaining ties → smaller L, then smaller H.
4. No selection on the regime table (it is an honesty check only). No re-opening of the grid
   after seeing results ("the grid is the grid").

Numbers cited in `is_report.md` will come only from `team-run` output on the final
`strategy.py`.

---

*Sections below appended after the pre-registered experiments were run and ledgered.*

## 6. Results — FALSIFIER FIRED (family dead)

Three ledgered experiments (e01–e03, evaluator-stamped 2026-07-18; scratch artifacts
`out/scratch/results_e0{1,2,3}.json`). All numbers are IS 2020-01-01→2024-06-30, evaluator
`net_series`/`evaluate` (monthly Sharpe, √12).

**e01 — existence grid (rank kernel, raw returns, H=0):**

| L (candles) | gross (no cost, no funding) | net @1x | net @2x | ann. turnover |
|---|---|---|---|---|
| 1 | **+0.348** | −3.146 | −6.204 | 1435 |
| 2 | −1.460 | −4.181 | −6.754 | 1002 |
| 3 | −0.711 | −3.115 | −5.321 | 824 |
| 6 | −1.386 | −3.055 | −4.567 | 591 |
| 9 | −2.245 | −3.576 | −4.765 | 486 |

**e02 — vol-normalized variant:** strictly worse everywhere (gross −0.78 … −2.48).

**e03 — tail-emphasis kernels at L=1:** zclip gross +0.245, rank3 gross +0.163 — both below
the linear rank's +0.348. The extremes do not revert more than the middle.

**Falsifier evaluation (pre-registered §3):**
- **F1 FIRED**: max gross Sharpe over the pre-registered L grid (rank, H=0) = **+0.348 < 0.8**.
  The pre-registered rescue axes (σ-normalization, tail kernels) were completed and both made
  it worse, not better. There is no gross short-horizon reversal edge in this universe/window.
- F2–F6: moot (nothing is nettable; cumulative cost 1.4–4.6 on the unlevered book dwarfs any
  gross edge; smoothing stages e04/e05 NOT run — smoothing reduces cost but cannot flip a
  negative-gross signal, and running them would be budget waste).
- **Funding-alignment thesis (registration): ALSO FALSIFIED.** The fade book's total funding
  P&L is slightly NEGATIVE in every config (−0.03 … −0.11 cumulative unlevered over 4.5y) —
  small in magnitude, but the sign contradicts the registered claim that the short-winners /
  long-losers book collects funding.

**Mechanism post-mortem (honest reading, not a re-registration):** the finding is not "noise,
no effect" — it is a strong OPPOSITE effect. The 8h–3d cross-section of the weekly top-40
exhibited robust CONTINUATION over IS (fading it loses −0.7 … −2.5 gross Sharpe at L ≥ 2,
in all three regime buckets). A coherent explanation: reversal-after-forced-flow is real in
crypto but concentrates in (a) the illiquid tail, and (b) minutes-to-hours horizons. In the
top-40 — by construction the MOST liquid slice — liquidation overshoots are arbitraged well
inside a single 8h bar, so by the first close the overshoot is gone and what remains at bar
granularity is flow-persistence. The mechanism I registered lives below this data's time
resolution and outside this universe's liquidity tier.

**Verdict: negative result, documented. The family is dead as registered. No QE SPEC is
issued for this family. Pivot decision escalated to the orchestrator (one documented pivot
available per charter §6).**
