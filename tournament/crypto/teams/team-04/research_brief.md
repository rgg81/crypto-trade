# team-04 research brief — t04-ts-trend-v2 (per-name multi-horizon time-series trend)

Status: PRE-REGISTERED (sections 1-7 written before experiment e01 was run; the QE SPEC in
section 8 is filled in after the experiment program concludes and is flagged as such).

## 1. Mechanism & economic rationale

Crypto perp trends are reflexively self-reinforcing. Rising prices attract retail flow (which
executes as aggressive taker buying), leveraged longs accumulate with the move, and funding/OI
build alongside. Adverse moves force margin liquidations that cascade in the direction of the
move, extending rather than ending it. There is no cash-flow anchor pulling price back to
"fair value" — narrative and flow ARE the fundamentals. Consequently multi-week price
direction persists per name, in both directions: pumping names keep pumping (flow chases),
bleeding names keep bleeding (post-pump exit queues, ecosystem collapses like LUNA/FTT,
delisting spirals).

This is a TIME-SERIES mechanism: each name's signal is computed from its OWN price history
only — direction (sign of multi-horizon trend) and conviction (trend size relative to the
name's own volatility). There is NO cross-sectional ranking, demeaning, residualization, or
peer comparison anywhere in the signal (that is team-03's family; family integrity is a hard
constraint). Cross-sectional interaction enters only through the organizer's book
construction (gross normalization + caps), which is outside the signal.

Why it can survive the net-capped book: the organizer caps |Σw| at 0.25 and per-name at 0.10.
A unanimous-direction book collapses to gross = net = 0.25 and gets re-levered ≤3x by the
vol-target — throttled but not dead. More importantly, the weekly top-40 by dollar volume is
NOT a unanimous universe: volume ranking pulls in crashing names (dump volume) alongside
pumping ones, so a per-name trend book naturally carries both sides most of the time. The
two-sided component of the book passes the caps at full gross. Whether the residual breadth
satisfies the median>=5/side floor is an EMPIRICAL question measured explicitly in e01 before
anything else is tuned.

## 2. Expected behavior per regime tag (pre-registered predictions)

| Regime tag | Expectation | Why |
|---|---|---|
| pre-COVID grind-up (bull) | mildly positive | short warmup history available (panel starts 2020-01; long lookbacks NaN) — possibly flat/inactive early |
| COVID crash (bear) | weak/negative | 1-month crash is faster than multi-week lookbacks; trend arrives late; warmup may leave book thin |
| 2020-21 bull | positive | strongest trend regime in the sample; longs persist for months |
| May-2021 crash (bear) | mixed | sharp reversal whipsaws slow lookbacks; shorter horizons should flip and recover the back half |
| run to 69k ATH (bull) | positive | trending |
| 2022 bear | positive | 13-month grind-down; shorts persist (LUNA, FTX collapses are trend-friendly); NOTE: shorts likely PAY funding here (crowded shorts, negative rates) — parts.fpnl will quantify |
| FTX-aftermath chop | flat/negative | rangebound = trend's known bleed regime; expected worst tag |
| ETF bull | positive | trending |
| post-halving chop (2024) | flat/negative | rangebound bleed |

Honest summary: I expect the bull and bear tags to pay and the two chop tags to bleed. The
strategy is deployable if the trend harvest across ~7 directional periods dominates the chop
bleed, net of costs, and the aggregate is not a disguised long-only bull bet.

## 3. Falsifier (pre-registered, matches the approved registration)

If, across the pre-registered multi-horizon lookback plateau (~21-126 candles), net IS Sharpe
at 1x costs is <= 0, OR all positive P&L sits in the 2020-21 bull tag while the 2022 bear and
both chop tags are jointly strongly negative (i.e., it is a long-only bull artifact, not
trend), the family is dead. Additionally (structural validity, not falsifier): if the
median>=5-names-per-side floor cannot be met by any configuration in the pre-registered
parameter space, the strategy is invalid as submitted and I will report that plainly.

## 4. Signal space (pre-registered parameter plan)

Core signal, per name i, per candle t (all inputs past-or-same-bar; close[t] usable at t):

- r_t = ln(close_t / close_{t-1})  (per-name 8h log return; NaN across listing gaps)
- vol_t(i) = rolling std of r over V candles, min_periods = V//2 (per-name own volatility)
- For horizon L: score_L(i,t) = ln(close_t / close_{t-L}) / (vol_t(i) * sqrt(L))
  (vol-normalized trend "t-stat"; NaN if close_{t-L} missing → that horizon abstains)
- blended(i,t) = mean over available horizons in H of clip(score_L, -Z, +Z); NaN only if ALL
  horizons NaN → flat
- raw weight w_raw(i,t) = blended(i,t) [optionally / vol_t(i), axis A3]
- optional smoothing (axis A4): EMA of w_raw with span E
- Emit w_raw full-width; engine masks eligibility, normalizes, caps, lags, costs, vol-targets.

Axes and ranges (rationale in parentheses):

- A1 horizon set H: singles {21, 63, 126, 252} and blends {21,63,126}, {63,126,252},
  {21,63,126,252} (candles; = 7d, 21d, 42d, 84d — the documented crypto trend band; shorter
  = cost-toxic at 8h cadence, longer = too few independent bets in 54 months)
- A2 clip Z: {1, 2, 3} plus pure sign(score) (conviction saturation vs binary; sign is the
  classic robust choice, clipped-z keeps mild conviction info)
- A3 inverse-vol sizing: {on, off} (risk parity across names vs signal-only; per-name cap 0.10
  already limits concentration)
- A4 signal EMA span E: {1 (none), 3, 6, 12} (turnover control; 8h costs are 6-15 bps/side)
- A5 vol window V: {42, 63, 126} (robustness check only; 63 = 21d default)
- NaN/newcomer rule: no history → NaN → flat (engine sanitizes NaN to 0). No imputation ever.

Budget plan: ~8-12 material experiments, each a logged sweep along ONE axis holding the rest
at defaults (defaults: H = {21,63,126,252}, Z = 2, inv-vol on, E = 1, V = 63). Then one final
confirmation run of the chosen spec (+ 2x stress + funding-off informational).

## 5. Selection rule (pre-registered — plateaus over peaks)

1. Validity gates first: median_names_long >= 5 AND median_names_short >= 5 over IS;
   ann_turnover sanity (< ~150/yr); NaN-safe.
2. Among valid configs, prefer the config whose one-step neighbors on every swept axis stay
   within 0.25 Sharpe of it (a plateau member), maximizing the MINIMUM of (Sharpe@1x,
   Sharpe@2x-stress + 0.5). Never select an argmax whose neighbors collapse.
3. Ties broken toward: fewer parameters away from defaults, lower turnover, better worst
   regime-tag Sharpe.
4. The 2x-stress tier must remain > 0 for the chosen config, else choose the nearest plateau
   config that satisfies it; if none exists the falsifier discussion in section 3 applies.

## 6. Experiment ledger plan

All experiments logged via `cli.py log-experiment --team team-04` BEFORE reading results;
one line per material sweep; ids e01, e02, ... Target <= 20, hard budget 40.

- e01: baseline defaults + full diagnostics (Sharpe 1x/2x, regime table, breadth time-series,
  net-exposure distribution, turnover, funding P&L split). GO/NO-GO on breadth structure.
- e02: A1 horizon sweep. e03: A2 transform sweep. e04: A3 sizing. e05: A4 smoothing.
- e06: A5 vol-window robustness. e07+: only if e01-e06 expose a structural problem
  (e.g., breadth rescue via wider flat-band, chop-bleed diagnosis).
- final: confirmation of chosen spec (fresh eval + stress + funding-off informational).

## 7. Cost & funding accounting expectations (pre-registered)

- Costs: ann_turnover T on the capped book costs ~ T * (5 + slip) bps/yr pre-vol-target;
  slow multi-week trend should land T in the 20-80 range — measured, not assumed.
- Funding: trend is LONG crowded names in bulls (pays positive funding) and SHORT crowded
  shorts in bears (pays negative funding) — I expect funding to be a structural DRAG on this
  family, unlike carry. parts.fpnl quantifies it; if the drag exceeds the price-trend alpha
  the falsifier fires honestly.

## 8. QE SPEC — FINAL (filled after experiments e01-e11; ledger-backed)

Chosen configuration (selection documented in section 9 and the e10/e11 ledger entries):
**H = (21, 63, 126, 252), transform = clip with Z = 2, inverse-vol sizing ON, EMA span E = 3,
vol window V = 126.**

The QE implements `build_raw_weights(pn, aux) -> pd.DataFrame` EXACTLY as below.
Imports allowed: numpy, pandas, teamlib only. No file access, no network, no randomness.

Inputs: `pn["close"]` ONLY. `aux` must be accepted but is UNUSED (do not read any aux panel;
do not apply eligibility — the engine masks; `aux["seed"]` intentionally unused — the
strategy has no randomness). Derive symbols from `pn["close"].columns` at runtime; never
hard-code names or counts (harness WIDENING check).

Exact steps, in order (pandas defaults everywhere: rolling std ddof=1; ewm adjust=True,
ignore_na=False):

1. `C  = pn["close"].astype(float)`          # DatetimeIndex x symbol columns
2. `lp = np.log(C)`                           # NaN where C is NaN; NEVER ffill/impute
3. `r  = lp.diff(1)`                          # 8h log returns; NaN across listing gaps
4. `vol = r.rolling(126, min_periods=63).std()`
5. `vol = vol.where(vol > 1e-6)`              # degenerate/stale series -> NaN (flat)
6. For each L in (21, 63, 126, 252):
       `s_L = ((lp - lp.shift(L)) / (vol * np.sqrt(L))).clip(-2.0, 2.0)`
   (young listing / gap -> s_L NaN -> that horizon abstains for that cell)
7. NaN-skipping blend — REQUIRED implementation shape:
       `num = Σ_L s_L.fillna(0.0)` ; `cnt = Σ_L s_L.notna()` ;
       `sig = num / cnt.replace(0, np.nan)`
   (cell NaN only if ALL four horizons are NaN; a plain (a+b+c+d)/4 is WRONG — it would
   flatten young names that have only the short horizons)
8. `w = sig / vol`                            # inverse-vol sizing
9. `w = w.ewm(span=3, min_periods=1).mean()`  # turnover smoothing, pandas defaults
10. `w = w.where(sig.notna())`                # EMA must not resurrect flat/NaN cells
11. `return w`  — same index and columns as `pn["close"]`. Do NOT normalize, cap, lag,
    mask, fillna(0), or scale — all engine-owned. NaN = flat is the contract.

Single-sentence NaN rule: any NaN input propagates to NaN output for that cell (with
horizon-level abstention in step 7 as the only NaN-tolerant aggregation), and the engine
treats NaN as flat — no imputation, no forward-fill, anywhere.

Sanity anchors from the e10 scratch run of this EXACT spec through the evaluator
(official numbers must come from `team-run`; a large deviation from these = wiring bug):
Sharpe@1x = 1.624, Sharpe@2x-stress = 1.336, maxDD = -0.371, ann_turnover = 125.7,
median names L/S = 18/17, mean gross = 0.81, regime Sharpe bull/bear/chop =
2.54 / 1.12 / +0.01, total funding P&L = +0.0591, total cost = 0.3570.

> **ADJUDICATION NOTE (post-team-run; ledger e12; orchestrator-ruled).** The frozen
> `strategy.py` transcribed step 7's `cnt = Σ_L s_L.notna()` as iterated `+` over BOOL
> frames; pandas bool addition is logical OR, so `cnt` saturates at 1 and the implemented
> `sig` is the **SUM over available horizons**, not the NaN-skipping MEAN written above.
> Verified bit-exactly in scratch (sum-semantics rebuild == strategy.py output; scoring it
> reproduces the official +1.609/+1.316 exactly). The engine's gross-normalization absorbs
> the per-cell count factor wherever it is uniform across the row, so the deviation only
> mildly tilts mixed rows toward full-history names: official +1.609/+1.316 vs the
> intended-mean +1.624/+1.336 (e10) — both members of the same plateau, difference far
> inside the noise floor. RULING: the frozen implementation's sum semantics is CANONICAL;
> this note records the deviation; nothing was tuned in response. The step-7 text above is
> preserved as the pre-freeze record of intent.

test_strategy.py minimum contents: (a) future-corruption self-check — corrupt
close[t+k], k>=1, assert weights at and before t bit-unchanged; (b) widening — append a
synthetic all-NaN column and a synthetic constant-price column, assert no crash and
existing columns' weights unchanged; (c) determinism — two calls on copies are bit-equal;
(d) NaN-tolerance — inject an interior NaN run into one column, assert no exception, NaN
cells flat, other columns unchanged; (e) same-bar honesty — weights at t must change if
close[t] changes (documents the same-bar convention the engine lags by one candle).

## 9. Post-experiment addendum (results annotations — pre-registered sections above are
untouched; numbers here are scratch-evaluator readings, official ones come from team-run)

- Falsifier status: DOES NOT FIRE. Plateau-wide Sharpe@1x is +0.7..+1.7 (never <= 0);
  bear-tag Sharpe +1.12 and 2022 calendar year +0.46 with chop +0.01 — not a long-only
  bull artifact.
- e01 surprises vs pre-registration: (i) turnover was ~209/yr at defaults, far above the
  pre-registered 20-80 guess — EMA span 3 brings the final book to ~126/yr; (ii) funding
  was a mild net CREDIT (+0.059 pre-vol-target, collected mostly in chop/bear), not the
  expected drag; funding-off Sharpe 1.577 vs 1.624 — funding is not load-bearing.
- Breadth: median 18L/17S over IS — the volume-ranked top-40 keeps both sides populated
  (crash volume pulls bleeding names into the universe); floor passed with margin.
- Selection: rule-2 min(S1x, S2x+0.5) produced a cluster of statistical ties spanning
  H3/H4 x Z{1,2} x V{126,189} x E{3,6} (spread ~0.11 Sharpe << the 54-month noise floor
  ~0.5). Pre-registered tie-breakers applied over the cluster: fewest changes from
  defaults -> H4-Z2-V126-E3, which is also the cluster's best on worst-regime Sharpe
  (chop +0.01), maxDD (-0.371), and near-best turnover. e11 then verified the choice is
  NOT a 2020-21 artifact: it has the best recent-half (2022-04..2024-06) Sharpe of the
  cluster (+0.76).
- HONEST CAVEAT for the record: the edge is front-loaded family-wide. Split-half Sharpe
  is +2.69 (2020-01..2022-03) vs +0.76 (2022-04..2024-06); calendar 2024 H1 is -0.29.
  Trend was simply stronger in 2020-21 than in 2022-24 across the entire parameter space.
  A realistic forward expectation is nearer the recent-half level (~+0.7) than the
  aggregate (+1.62). No second-half-targeted tuning was attempted (that would be
  overfitting to recency); the plateau, not the peak, was submitted.
- Ledger: e01-e12 (12 of 40 used; e12 = post-team-run adjudication forensics, no tuning).
  No pivot. No holdout contact of any kind.
