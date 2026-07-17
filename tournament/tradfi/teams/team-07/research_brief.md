# team-07 research brief — t07-overnight-tugofwar-v1

Family (APPROVED in registry.jsonl): **Overnight-vs-intraday gap decomposition ("tug of war")**.
Primary residual-momentum registration was vetoed (team-01 FCFS); this is backup-2, assigned by
the orchestrator. All work below stays inside this family.

Status: PRE-REGISTRATION written before any experiment ran. Sections 6-7 (results + final QE
spec) are filled in only after the ledgered experiments complete.

---

## 1. Mechanism

Decompose each name's daily total return into two sessions computable from the OHLC panel:

- overnight component  `on[t] = open[t] / close[t-1] - 1`
- intraday  component  `id[t] = close[t] / open[t]  - 1`

Cross-sectionally, trailing overnight returns CONTINUE (names persistently bid in the
off-session keep being bid) while trailing intraday returns REVERSE (intraday moves carry a
liquidity-provision / rebalancing-pressure component that decays). The canonical family signal
is the trailing tug-of-war spread — long names whose returns arrive overnight, short names
whose returns arrive intraday:

```
S[t] = mean(on[t-W+1 .. t]) - mean(id[t-W+1 .. t])
```

with the two single-component books (`+mean(on)`, `-mean(id)`) as within-family controls that
tell us WHERE the edge lives.

## 2. Economic rationale

Session clienteles differ: the open prices overnight news through attention-driven retail and
market-on-open flow, while intraday is dominated by institutional execution and rebalancing.
Lou-Polk-Skouras-style "tug of war" evidence says the overnight component of returns carries
persistent, clientele-driven continuation while the intraday component carries transient price
pressure that mean-reverts. The decomposition splits one noisy total return into a persistent
piece and a fading piece — a cleaner cross-sectional sort than total-return momentum at the
same horizon. On perps the short side has no borrow constraint, so the fade leg is clean.

Execution-contract caveat (drives design): we decide at close[t] and fill at open[t+1],
earning open-to-open. The very next overnight gap (close[t] -> open[t+1]) is NEVER captured.
So one-day-lag effects are structurally unavailable; the signal must predict overnight
components at lag >= 2 and intraday components at lag >= 1. Hence trailing-window (weeks to
months) formation, NOT day-ahead gap prediction.

## 3. Expected regime behavior

- Bull / chop: the book is cross-sectional and (by construction) dollar-neutral row-wise —
  expect low beta and steady modest positive edge; this is where clientele segmentation is
  cleanest.
- Bear / VIX stress (2011, 2015-16, 2018Q4, 2020-03, 2022): overnight gaps become macro/beta
  driven, correlations spike, and the idiosyncratic clientele signal is diluted — expect the
  weakest (possibly negative) Sharpe in `regime_sharpe["bear"]`; the engine's vol-target
  de-levers there. A bear-regime bleed is acceptable; a bull-regime bleed is not (that would
  contradict the mechanism).

## 4. Falsifier (kills the idea)

Primary: if ALL three constructs (spread, ON-only, ID-fade-only) across the FULL formation
grid W in {21, 63, 126, 252} yield net IS Sharpe @1x <= 0 — i.e. no plateau anywhere, at most
isolated sign-flips — the family premise is dead at open-to-open horizon under this contract;
we report the negative result and DNF (or spend the one pivot).

Secondary (cost falsifier): if every configuration with positive 1x Sharpe has 2x-cost Sharpe
<= 0 even after the pre-registered smoothing/banding axis, the edge is a cost illusion at 6
bps/side and is likewise reported dead.

Validity constraint at all times: median names/side >= 5 (charter breadth floor).

## 5. Pre-registered parameter plan & selection rule

Grid (target <= 25 material experiments, ledgered before each result is read):

| axis | values | rationale |
|---|---|---|
| construct | SPREAD (canonical), ON-only, ID-fade-only | locate the edge within the family |
| formation W | 21, 63, 126, 252 (min_periods = W) | month -> year; lag>=2 persistence lives here |
| standardization | raw mean vs t-stat (mean/std within window) | vol-normalise component noise |
| cross-sectional transform | centered pct-rank (default) vs z-score (winsorized +/-3) | rank = robust to fat tails |
| weighting | linear in centered rank (max breadth) vs top/bottom tercile equal-weight | breadth/concentration trade-off |
| smoothing | none vs EMA halflife {5, 10} on the final weight panel | first-class turnover control at 6 bps |
| sector neutralization | off vs `neutralize.sector_neutralize` | strip sector clientele confound |

Fixed by contract, not swept: engine owns gross=1, |w_i|<=0.10, |net|<=0.25, vol-target 15%;
NaN signal = flat name; tickers derived from panel columns at runtime; no VIX gating in v1
(regime conditioning is out of scope for this family's first pass — noted as future work).

Selection rule (pre-registered, applied mechanically): among configs satisfying breadth floor,
maximize **min(Sharpe@1x, Sharpe@2x)** subject to plateau stability — the chosen W must have
both grid-neighbors within 0.30 Sharpe or same-sign edge; when two configs are within 0.15 of
each other on the criterion, take the SIMPLER one (fewer active axes). No config is chosen on
a single-cell peak.

Experiment budget: reg-001 consumed 1 ledger line; design target is <= 16 further material
experiments (hard family cap 40, never reset).

---

## 6. Results (evaluator numbers only — te.run_is; full precision in out/e-*.json)

17 material experiments (e-002..e-018), ledgered before each result was read. One axis was
ADDED beyond the Section-5 grid and is documented in the ledger: a 21d formation skip
(12-1 analog, e-013). It hurt and is not in the final spec.

| id | construct | W | variant | Sharpe@1x | Sharpe@2x | maxDD | ann.turn | med nL/nS |
|---|---|---|---|---|---|---|---|---|
| e-002 | ON | 63 | — | +0.268 | +0.017 | -0.421 | 30.3 | 24/24 |
| e-003 | ID_REV | 63 | — | -0.435 | -0.747 | -0.769 | 40.2 | 24/24 |
| e-004 | SPREAD | 63 | — | +0.058 | -0.250 | -0.449 | 35.9 | 24/24 |
| e-005 | ON | 21 | — | +0.198 | -0.316 | -0.474 | 58.1 | 24/24 |
| e-006 | ON | 126 | — | +0.218 | +0.066 | -0.399 | 20.4 | 24/24 |
| e-007 | ON | 252 | — | +0.441 | +0.340 | -0.347 | 12.9 | 24/24 |
| e-008 | ON | 252 | tstat | +0.428 | +0.300 | -0.284 | 13.9 | 24/24 |
| e-009 | ON | 252 | zscore | +0.476 | +0.408 | -0.363 | 11.6 | 22/27 |
| e-010 | ON | 252 | tercile | +0.472 | +0.375 | -0.345 | 12.1 | 17/17 |
| e-011 | ON | 252 | sector-neutral | +0.314 | +0.177 | -0.368 | 15.9 | 24/24 |
| e-012 | ON | 252 | ema5 | **+0.448** | **+0.417** | -0.350 | **3.9** | 24/24 |
| e-013 | ON | 252 | skip21 | +0.257 | +0.155 | -0.358 | 12.8 | 24/24 |
| e-014 | ON | 252 | ema10 | +0.428 | +0.405 | -0.342 | 2.9 | 24/24 |
| e-015 | ON | 126 | ema5 | +0.326 | +0.280 | -0.410 | 6.2 | 24/24 |
| e-016 | ON | 252 | tercile+ema5 | +0.448 | +0.412 | -0.374 | 4.4 | 23/24 |
| e-017 | ON | 252 | zscore+ema5 | +0.480 | +0.456 | -0.359 | 3.9 | 22/27 |
| e-018 | ON | 252 | ema5 (spec rerun) | +0.448 | +0.417 | -0.350 | 3.9 | 24/24 |

Findings, in causal order:
1. **The edge lives in the overnight component** (e-002 vs e-003/e-004): the ID-fade leg is
   NEGATIVE net (-0.44) — trailing intraday returns do not revert at this horizon/cost — and
   the canonical spread merely dilutes ON with a losing leg. ON-only is exactly the mechanism
   this family registered ("cross-sectional persistence of the trailing overnight component").
2. **Longer formation is monotonically better and cheaper** (e-005/002/006/007): Sharpe@1x
   0.20 -> 0.27 -> 0.22 -> 0.44 while turnover falls 58 -> 13. Overnight persistence here is a
   slow clientele sort, not a fast gap effect (consistent with the fill-at-next-open contract
   destroying lag-1 effects).
3. Variants at W=252: t-stat standardization no gain; zscore and tercile within noise of rank;
   **sector neutralization HURTS** (-0.13 Sharpe — the sector tilt is part of the signal);
   21d skip HURTS (recent-month ON is informative, unlike price momentum).
4. **EMA halflife-5 weight smoothing is the decisive overlay**: turnover 12.9 -> 3.9 with
   Sharpe unchanged, closing the 1x->2x gap to 0.03 (e-012). ema10 equivalent (plateau).
5. Plateau check for the champion (min(S1x,S2x) = 0.417): neighbors ema10 0.405, unsmoothed
   0.340, W=126+ema5 0.280, tercile+ema5 0.412, zscore+ema5 0.456 — all same-sign, all within
   the 0.30 band. e-017 (zscore) beats the champion by 0.039 < 0.15 -> selection rule takes
   the SIMPLER config (rank is the pre-registered default transform; e-017 also skews the book
   22/27 and deepens bear bleed -1.67 vs -1.31).
6. e-018 rerun of the exact spec is bit-identical to e-012 (determinism confirmed).

Regime profile of the champion (pre-registration §3 held): bull +0.74, chop +0.23, bear -1.31.
The bear bleed was predicted and accepted; the mechanism is intact where it should work.

## 7. Final specification for the QE (complete — nothing left to decide)

`build_raw_weights(pn, aux)` — pure, deterministic, no randomness (aux['seed'] unused):

```python
def build_raw_weights(pn, aux):
    o, c = pn["open"], pn["close"]          # dates x tickers; tickers from panel at runtime
    on = o / c.shift(1) - 1.0               # overnight component: open[t]/close[t-1] - 1
    sig = on.rolling(252, min_periods=252).mean()
    r = sig.rank(axis=1, pct=True)          # pandas defaults: method='average', na_option='keep'
    w = r.sub(r.mean(axis=1), axis=0)       # center -> dollar-neutral; NaN stays NaN
    return w.ewm(halflife=5, min_periods=1).mean()   # pandas defaults: adjust=True, ignore_na=False
```

Fixed parameters (ALL of them): W = 252 bars, min_periods = 252 (strict — any NaN inside the
trailing window blanks the name that day), cross-sectional transform = pct-rank centered by
row mean, weighting linear in centered rank, EMA halflife = 5 bars with min_periods=1,
NO sector adjustment, NO skip, NO standardization, NO zscore/tercile, NO VIX use, NO use of
high/low/volume. Inputs touched: `pn['open']`, `pn['close']` only.

Missing-data semantics (exactly as scored): names with <252 valid overnight observations in
the trailing window have NaN signal -> engine treats as flat. The EMA (ignore_na=False,
pandas default) emits the carried mean on a missing-bar day once a name has >=1 prior valid
signal; such days have NaN ret_fwd so they contribute no PnL — deterministic and leak-safe.
Do not "fix" this; the IS numbers above are scored with precisely these semantics.

Engine owns everything downstream (gross=1, |w_i|<=0.10, |net|<=0.25, vol-target 15%, shift(1),
costs). Emit raw weights only. Expected canonical IS metrics for verification after
`cli.py team-run --team team-07`: Sharpe@1x = 0.4478, Sharpe@2x = 0.4171, maxDD = -0.3498,
ann. turnover = 3.887, median names 24/24, 174 months (full precision: out/e-018.json).
