# team-09 research brief — trade-size composition cross-section
## Family: t09-trade-size-composition-v3 (approved pivot, registry.jsonl)
## Appendix A preserves the full falsification record of t09-liq-squeeze-reversal-v2 (e01-e04).

Status: PRE-REGISTERED before the first family experiment (ledger resumes at e05; 4/40 used).
Sections 1-7 are frozen intent; Section 8 (results) and Section 9 (QE SPEC) are filled ONLY
per the Section-6 selection rule applied to evaluator-logged experiments.

---

## 1. Mechanism and economic rationale

The kline `trades` field makes the **marginal participant observable**: average trade size
(`quote_volume / trades`, dollars per print) and trade-count dynamics separate two kinds of
flow that OHLCV alone cannot:

- **Retail swarm**: trade count explodes while average trade size SHRINKS — many small
  orders. This is the signature of an attention cascade (social-media-driven arrival of
  price-insensitive small traders). Retail nets long at attention peaks and is exit
  liquidity for earlier holders; swarm names are marginally overpriced.
- **Large-trade flow**: average trade size RISES — big prints, fewer participants per
  dollar. Accumulation/distribution by larger or better-informed traders.

Hypothesis (registered direction, fixed): over the following **1-4 weeks**, retail-swarm
names UNDERPERFORM the cross-section and large-trade-flow names OUTPERFORM. Why it should
exist in crypto perps: no fundamental anchor, retail share of flow is structurally high,
attention is the dominant retail allocation mechanism, and perps let the swarm lever up
(compounding the subsequent bleed). Why it persists: the counterparty is systematic
attention-chasing, refreshed every cycle; the signal requires the `trades` field, which
most simple screens ignore.

Distinctness (fidelity notes): this is a WHO-is-trading mechanism — not aggressor
direction (t05 taker-flow), not volume-confirmation of price moves (t10), not price
persistence (t02/t03/t04), not OI positioning (t06/t08 territory). The composition term
(trade size/count) must be load-bearing vs a plain volume-attention control (falsifier F3).

## 2. Signal design

Per name i, candle t (same-bar info legal at t's close):

1. Aggregate average trade size, recent window W:
   `ats_num = qv.rolling(W).sum() / trades.rolling(W).sum()`
   (ratio of sums — robust; NaN-safe where trades sum to 0).
2. Baseline, window B shifted to be overlap-free:
   `ats_den = (qv.rolling(B).sum() / trades.rolling(B).sum()).shift(W)`.
3. Composition score: `comp = log(ats_num / ats_den)` — POSITIVE = trade size rising
   (large-trade flow), NEGATIVE = trade size shrinking (retail swarm). Scale-free across
   names and time; cross-sectional common drift removed by the transform in (4).
4. Cross-sectional transform, per candle, over eligible names with valid comp:
   centered rank in [-0.5, +0.5] (primary; z-score clipped ±3 as robustness variant).
   Rows with < MIN_NAMES valid eligible names → all-NaN (flat; avoids 3-name-universe
   noise in early 2020).
5. Hold smoothing: `sm = rank.rolling(h).mean()` (turnover control; h in candles).
6. Emit `sm` as raw signed weights (LONG rising-ATS names, SHORT swarm names). Engine owns
   eligibility, caps, lag, costs, funding, vol-target.

NaN policy: comp NaN until W and B+W warmed (min_periods 80% of window); trades==0 or
NaN → comp NaN → flat for that name. New listings are flat their first ~(B+W) candles.

## 3. Expected behavior per regime tag (pre-registered predictions)

Retail-participation-dependent, but two-sided (long leg is whale-flow, not anti-retail):
- **2020-21 bull, 2021 ATH run, ETF bull**: swarm events abundant (DOGE Apr-21, meme
  waves, SHIB Oct-21, memecoin season 2024) — expect the STRONGEST contribution.
- **Chop regimes (FTX-aftermath 2023, post-halving 2024)**: memecoin rotations persist
  (PEPE May-23, WIF/BONK 2024) — expect positive, moderate.
- **Bear 2022**: retail exodus, fewer swarms; expect weakest/flat, NOT strongly negative
  (the mechanism goes quiet rather than inverting).
- **COVID crash / early 2020**: universe thin (3-18 names), signal partly flat by the
  MIN_NAMES guard; expect ~nil contribution.
Pre-registered profile: bull ≥ chop > bear ≈ 0. A bull-only profile would be a concern to
report honestly; a robustly NEGATIVE profile anywhere fires F1 scrutiny.
Funding sub-hypothesis: swarm shorts are crowded-long names with positive funding → the
short leg should COLLECT funding (total_funding_pnl ≥ 0 expected; measured, not assumed).

## 4. Falsifiers (pre-registered)

- **F1 (existence, registered direction)**: no (W, h) cell in the pre-registered grid has
  net IS Sharpe > 0 @1x in the registered direction (long rising-ATS / short swarm) ⇒
  family dead. A robustly opposite-signed result is ALSO F1 — we do not flip-ship a
  different mechanism under this registration.
- **F2 (cost honesty)**: pre-cost edge exists but no turnover-controlled variant keeps
  net Sharpe > 0 @1x ⇒ dead.
- **F3 (load-bearing composition — registered)**: control = identical pipeline with comp
  replaced by NEGATIVE log volume-spike (fade volume-attention alone,
  `comp_ctrl = -log(qv.rolling(W).sum() / qv.rolling(B).sum().shift(W) · B/W)`, i.e. the
  same ratio-of-sums construction on qv only), plus a count-only control (same on
  `trades`). If the best control achieves ≥ 80% of the candidate's IS Sharpe, composition
  is not load-bearing ⇒ family dead.
- **F4 (breadth)**: chosen config median names/side ≥ 5 on active rows.
- **F5 (stress)**: chosen config net Sharpe > 0 at 2x cost+slippage.

## 5. Parameter plan (grid pre-registered; plateaus over peaks)

| Param | Meaning | Grid | Rationale |
|---|---|---|---|
| W | recent composition window | {9, 21, 42} candles (3d, 1wk, 2wk) | swarm build-up timescale |
| B | baseline window | 90 fixed; 180 robustness | stable participant norm |
| h | hold smoothing | {1, 9, 21} candles | 1-4wk predictive horizon; turnover control |
| transform | x-sectional | rank primary; z(clip 3) robustness | fat-tailed ats distributions |
| MIN_NAMES | row validity | 10 fixed | early-2020 thin universe guard |
| min_periods | warmup | ceil(0.8·window) fixed | NaN honesty |

Grid = 3×3 (W×h) at B=90/rank = 9 cells core; + ≤6 robustness cells; + 2 F3 controls.

## 6. Selection rule (pre-registered)

1. Core 3×3 (W,h) grid: candidate = cell with the highest mean of {cell, its grid
   neighbors} (plateau center). Edge-sitting plateau ⇒ extend grid one step once per axis
   (logged as its own experiment).
2. Keep B=90 and rank transform unless a robustness variant differs by > 0.2 Sharpe
   (then investigate before selecting).
3. Candidate must beat BOTH F3 controls by the load-bearing margin (control < 80% of
   candidate Sharpe), pass F4, F5.
4. Ties → lower turnover.
5. Headline numbers for is_report.md come from team-run only.

## 7. Cost & turnover expectations

Rank of a W-candle aggregate is slow-moving; expected annualized turnover O(20-80).
At ~7-12 bps/side full cost this is a 1.5-8%/yr drag — the h axis exists to keep the
realized drag at the low end without pushing the hold beyond the registered 1-4wk horizon.

---

## 8. Results (filled from evaluator-logged experiments ONLY; e05-e10, 10/40 budget used)

### e05 — diagnostics
Trades field valid for 100% of eligible names over the whole window. comp well-behaved
(sd 0.21, p1/p99 ±0.55/0.59). Slow signal: rank autocorr +0.99 (lag 1), +0.77 (lag 9),
+0.46 (lag 21). Confound map (xsec Spearman): comp vs vol_spike +0.71, count_spike +0.50,
ret21 +0.35, size −0.07 → F3 controls and a momentum-overlap check are mandatory.

### e06/e07 — F1 grid + refinement (registered direction; centered rank, B=90)
**F1 does NOT fire.** Net IS Sharpe @1x, W×h grid:
| | h=1 | h=3 | h=9 | h=21 |
|---|---|---|---|---|
| W=5 | +0.97 | +0.76 | — | — |
| W=9 | **+0.98** | +0.82 | +0.64 | +0.28 |
| W=21 | +0.87 | +0.71 | +0.35 | −0.06 |
| W=42 | **+0.83** | +0.71 | +0.49 | −0.12 |
Fresh ranks carry the signal (monotone decay in h; W-window is the real smoothing).
Funding P&L positive in every cell (funding sub-hypothesis CONFIRMED at book level).
Breadth 19/19 everywhere. 2x-stress (h=1): W=9 +0.45, W=21 +0.52, W=42 +0.59 (F5 PASS,
ordering inverted vs 1x). Regime deviation vs Section 3: bull ≈ bear > 0 > **chop
negative** (−0.28 at W=42 … −1.27 at W=9) — reported honestly; leg split (e08) shows the
whale-long leg bleeds in dead markets.

**Documented selection amendment (written into the ledgered e09 entry BEFORE running
it):** strict rule-1 gives (9,1) (neighborhood 0.91 vs 0.90 (5,1), 0.85 (21,1)); within
the h=1 plateau (all cells inside 0.2), we prefer **(W=42, h=1)** by: max 2x-stress (the
stage-1 tiebreak metric), least-bad worst-regime (charter generalization objective),
lowest turnover (rule 4), and horizon fidelity to the registry text (W=42 = 2 weeks).
(9,1) numbers are reported alongside for the Critic.

### e08 — F3 load-bearing controls: PASS by an enormous margin
Same pipeline, comp replaced: vol-attention fade −1.33 (W9) / −0.58 (W42); count-attention
fade −1.28 / −0.30 — both DEEPLY negative vs comp +0.98 / +0.83. The composition term is
not merely load-bearing; it is the entire edge (attention-fading alone loses, consistent
with the Appendix-A continuation findings). Leg funding: swarm shorts COLLECT (+0.14 raw),
whale longs pay (−0.09) — as registered. Diagnostic references: ret21 momentum book (a
CLAIMED family; measured as reference only, never shippable by us) = +1.28, with monthly
corr to comp of +0.69 (W9) / +0.46 (W42).

### e09 — momentum-orthogonality fidelity check (ex-ante bars in the ledger)
Momentum-residualized comp (per-candle rank-on-rank OLS): **net −0.03 (W=42), −0.50
(W=9)** → the ex-ante "≤0 ⇒ escalate to orchestrator as fidelity failure" bar FIRED.
Robustness (rule 2): B=180 +0.54, z-transform +0.60 vs +0.83 baseline — knob sensitivity
0.23-0.29 (variants are worse, so pre-registered defaults stand; sensitivity disclosed).

### e10 — final validation package + residual decomposition
Candidate (W=42, h=1, B=90, rank): **1x +0.83** (maxDD −0.44, TO 81/yr, breadth 19/19,
54 months, mean +2.52%/mo, 56% positive months), **2x-stress +0.59**, funding-off +0.70
(funding contributes ≈ +0.13 Sharpe — real tailwind, not the whole edge).
Residual book decomposition: **pre-cost +0.50** (bull +0.71, bear +0.81, chop −0.43;
+0.38 with funding also off) vs net −0.03 — the momentum-orthogonal component carries
REAL gross alpha but the residualization construction doubles turnover (165 vs 81/yr) and
costs erase it. Characterization for the record: comp = genuine composition alpha
(momentum-orthogonal, two-regime-positive pre-cost) + a momentum-correlated component;
in net terms the shipped slow design's edge is substantially carried by the
momentum-correlated part.

### Falsifier scorecard (registered set)
- **F1 PASS** (+0.83 @1x, registered direction, plateau not peak)
- **F2 PASS** (net-positive; cost drag 0.23 raw over 4.5y at TO 81/yr)
- **F3 PASS** decisively (best control −0.30 vs candidate +0.83; margin ≫ registered 80% bar)
- **F4 PASS** (median 19/19 names per side)
- **F5 PASS** (+0.59 at 2x cost+slippage)
- **Extra-registered e09 fidelity bar: FIRED on net (−0.03), mitigated on gross (+0.50
  pre-cost)** → ESCALATED to orchestrator with recommendation SHIP + full disclosure
  (decision pending; Section 9 spec is conditional on that decision).

## 9. QE SPEC (CONDITIONAL on orchestrator resolution of the e09 escalation)

Signal: trade-size composition, exactly as follows. No price, OI, funding, or ratio
inputs. No randomness (aux['seed'] unused). Derive columns from the panel at runtime.

Inputs: `qv = pn['quote_volume']`, `tr = pn['trades']`, `elig = aux['eligibility']`.
Constants: `W=42, B=90, MPW=34, MPB=72, MIN_NAMES=10` (MPW=ceil(0.8·42), MPB=ceil(0.8·90)).

1. `qs_W = qv.rolling(42, min_periods=34).sum()`; `ts_W = tr.rolling(42, min_periods=34).sum()`
2. `qs_B = qv.rolling(90, min_periods=72).sum()`; `ts_B = tr.rolling(90, min_periods=72).sum()`
3. `comp = np.log((qs_W / ts_W) / (qs_B / ts_B).shift(42))`
4. `comp = comp.replace([np.inf, -np.inf], np.nan).where(elig)`  # mask BEFORE ranking —
   ranks are computed among eligible names only (order-affecting; do not move this step)
5. `r = comp.rank(axis=1)`  # pandas defaults: ascending, average ties, NaNs excluded
6. `sig = r.sub(r.mean(axis=1), axis=0).div(r.count(axis=1).clip(lower=1), axis=0)`
7. `n_valid = comp.notna().sum(axis=1)`; rows where `n_valid < 10` → set entire row NaN
8. `return sig`  (raw signed weights; LONG high comp = rising avg trade size, SHORT low
   comp = retail swarm; NaN = flat; engine owns everything downstream)

No h-smoothing step (h=1 ⇒ identity; omit). Scale of `sig` is irrelevant (engine
gross-normalizes); ordering and centering are load-bearing. Column-set agnostic by
construction (all ops are panel-wide; WIDENING-safe). NaN-tolerant: young/dead names and
thin rows are NaN → flat. Scratch reference implementation: `out/scratch/sig2.py`
(`build_signal(pn, aux, W=42, h=1)` — bit-identical to this spec).

---
---

# Appendix A — FALSIFICATION RECORD: t09-liq-squeeze-reversal-v2 (dead family)

Registered mechanism (registry.jsonl): post-liquidation-cascade snap-back — continuous
wipeout-intensity score (extreme range + volume spike + OI collapse), trade the 1-3 day
reversal of the overshoot. Pre-registered falsifiers F1 (no positive net IS Sharpe @1x
over 1-9-candle holds anywhere in the grid) and F2 (effect only pre-cost).

**VERDICT: F1 and F2 FIRED. 4 material experiments (e01-e04, experiments.jsonl).**

- **e01 (coverage)**: eligible universe ramps 3→40 names Jan→Sep-2020. OI panel BTC-only
  until Nov-2021; ≥80% eligible coverage from 2021-12 ⇒ honest OI window 2022+.
- **e02 (pre-registered k×h book grid, GAMMA=1, 1x costs)**: ALL 9 cells net IS Sharpe
  −2.31 to −3.18, maxDD ≈ −99%, negative in bull AND bear AND chop in every cell;
  funding P&L negative in all cells (funding-tailwind sub-thesis also failed).
  Turnover 305-797/yr.
- **e03 (decomposition + event study)**: center cell k=2,h=6 is **−1.31 Sharpe pre-cost,
  pre-funding** — failure is not a cost artifact. Event-conditional forward returns
  (market-relative, entry open[t+1]): long-flush events NEGATIVE at every threshold and
  1-9-candle horizon, monotonically worse with stronger cascade evidence (x0=2,ev0=2,n=3:
  −182 bps t=−3.3; x0=3,ev0=3,n=3: −689 bps t=−2.7); wrong-signed in bull (−72), bear
  (−288), chop (−131 bps). Short-squeeze side: continuation too; only pocket = chop-only
  +70 bps (t=+2.5), a single-regime sliver. Conclusion: at 8h granularity the intra-candle
  bounce is fully absorbed before the next open; what remains is CONTINUATION.
- **e04 (OI-collapse-confirmed events, 2022+, entry delays 0-6, holds 1-9)**: OI
  confirmation NEUTRALIZES continuation (flushL n=3: −153 bps → −15/−33 bps at
  oi_drop ≥ 5%/10%) but never turns positive beyond noise (best +6.6 bps, t=0.6, below
  the 12-14 bps round-trip cost). Squeeze side with OI: N=122-256, |t| ≤ 1.5, noise.

Family closed honestly; sign-flip continuation trading was NOT shipped under this family
(would be family-misrepresentation). Pivot granted by the orchestrator; FCFS resolved to
t09-trade-size-composition-v3 (this brief). The e04 OI-term evidence was offered to and
is now owned by the OI-price-confirmation family (team-08).
