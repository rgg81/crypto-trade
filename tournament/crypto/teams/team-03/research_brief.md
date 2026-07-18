# team-03 — Research Brief: BTC-beta-residual cross-sectional momentum

Family: `t03-btc-residual-momentum-v1` (APPROVED in registry.jsonl).
Status: PRE-REGISTERED before any experiment was run. Sections 1–8 were written before the
first `log-experiment` line; Section 9 (results) and Section 10 (QE SPEC, final parameters)
were filled in afterwards, following the selection rule of Section 7 verbatim.

---

## 1. Mechanism

Crypto alt returns are dominated by a single market factor (BTC/majors). The residual — the
component of each coin's return orthogonal to its rolling market beta — reflects coin-specific
narrative flow: sector rotations (DeFi summer, L1 season, memes, AI), listings and unlocks,
ecosystem health or death spirals. Retail flow chases these narratives reflexively: coins with
alt-specific strength attract more aggressive taker buying, social attention, and follow-on
listings; coins with alt-specific weakness (dying ecosystems, unlock overhangs) keep bleeding.
So residual strength/weakness PERSISTS at horizons of days-to-weeks.

We rank the weekly top-40 on trailing residual momentum and go long persistent residual
winners / short persistent residual losers, dollar-neutral by construction.

Why residualize (vs plain momentum): (a) most of the danger in crypto momentum is the market
factor — violent common crashes and V-bottoms whipsaw plain momentum; the residual book is
near-market-neutral and survives them structurally; (b) the engine's net cap (|Σw| ≤ 0.25) and
vol-targeting reward a book whose P&L is not a disguised market bet; (c) beta dispersion in the
top-40 is wide (majors ~1, small alts 1.2–2), so plain cross-sectional momentum ranks are
contaminated by beta × market-trend, which reverses at regime turns.

Why it is not arbitraged away: the marginal trader in top-40 alt perps is retail/flow-driven,
shorting alts costs carry and borrow attention, and institutional stat-arb capacity in these
names is thin; the effect is a crowd-herding phenomenon, not a latent risk premium that a
single desk can drain.

## 2. Expected behavior per regime tag (pre-registered)

Engine scorecard buckets: bull / bear / chop (fixed windows in `constants._REGIMES`).

- COVID crash (bear, 2020-02-14→03-13): roughly neutral. The crash is mostly the market
  factor, which we strip; expect small loss at the V-bottom whipsaw, not a wipeout.
- 2020-21 bull (03-13→2021-04-14): strongly positive — DeFi/L1 rotation persistence is the
  archetype of the mechanism.
- May-2021 crash (bear): drawdown risk — momentum-crash dynamics; beaten-down high-beta names
  bounce hardest. Residualization mitigates but does not eliminate. Expect negative-to-flat.
- Run to 69k ATH (bull): positive.
- 2022 macro bear (Fed/LUNA/3AC/FTX): positive — residual losers (dying ecosystems) kept
  dying; the short side also collects.
- FTX-aftermath chop (2022-11→2023-10): weak/flat — fast rotation chop is the mechanism's
  worst weather. Expect ~0, small negative acceptable.
- ETF bull (2023-10→2024-03): positive (AI/meme narrative persistence).
- Post-halving chop (2024-03→07): weak/flat.

Aggregate expectation: bull bucket clearly > 0; bear bucket ≥ 0 (2022 offsets May-2021); chop
bucket ~0. The strategy should NOT be a one-regime pony; if it is, the falsifier fires.

Funding expectation: momentum longs skew toward high-funding names (crowded longs pay), so
`total_funding_pnl` is expected mildly negative — an accepted headwind, monitored. If funding
drag alone flips the sign of net P&L, that is a kill condition (see falsifier).

## 3. Falsifier (pre-registered — this kills the family)

F1. Plateau failure: at baseline settings (Section 6), the MEDIAN net IS Sharpe @1× across the
    formation-lookback plateau L ∈ {42, 63, 126, 168} candles (2–8 weeks) is ≤ 0.
F2. One-regime pony: for the selected spec, recomputing the monthly Sharpe with the
    2020-03-13→2021-04-14 bull window EXCLUDED gives ≤ 0 (all profit was the 2020-21 bull).
F3. Cost fragility: the selected spec's net IS Sharpe ≤ 0 at the 2×-stress tier.
F4. Funding domination: the selected spec is profitable only with funding off (i.e. net
    Sharpe @1× funding-on ≤ 0 while funding-off > 0) — the price signal would be an illusion
    financed by carry we do not collect.

Any of F1–F4 → report honestly, then either invoke the one documented pivot (ask orchestrator)
or submit the best honest book / DNF.

## 4. Signal construction (formulas fixed BEFORE experiments)

All series are past-only; the decision at candle t uses data at or before t (same-bar close[t]
and aux row t are allowed by charter). No randomness. Column-set agnostic: symbols = panel
columns at runtime; eligibility reindexed to panel columns with `fill_value=False`.

1. Returns: `r = log(close).diff()` per symbol (log returns; NaN where close missing).
2. Market factor `m_t`: cross-sectional mean of `r_t` over symbols ELIGIBLE at t
   (aux['eligibility'] row t), requiring ≥ 5 eligible names with valid returns, else NaN.
   Variant DVW: weighted mean with weights ∝ trailing 21-candle mean quote_volume, shift(1),
   renormalized over the same eligible+valid set (BTC/ETH-dominated ⇒ closest to "BTC beta").
3. Rolling beta (window W_beta, min_periods MP_beta = W_beta // 2):
   `beta_i = r_i.rolling(W_beta, MP_beta).cov(m) / m.rolling(W_beta, MP_beta).var()`,
   then `beta = beta.clip(0.0, 3.0)` (fixed, not tuned — guards thin-history blowups).
4. Residual: `e_i,t = r_i,t − beta_i,t · m_t` (NaN if any input NaN).
5. Formation score over L candles with skip-gap g (skip the most recent g candles to avoid
   short-horizon reversal contamination):
   - raw-sum variant:  `S = e.rolling(L, mp_L).sum().shift(g)`
   - t-stat variant:   `S = (e.rolling(L, mp_L).mean() / e.rolling(L, mp_L).std()).shift(g)`
   with `mp_L = ceil(0.8·L)`.
6. Cross-sectional transform: mask S to eligible names (row t); centered percentile rank:
   `w_raw = S.rank(axis=1, pct=True)`, then subtract the row-mean of the ranks (exactly
   dollar-neutral raw book, full breadth ~20/side). NaN → flat (0).
7. Turnover smoothing: `w = w_raw.fillna(0).ewm(span=K, adjust=True).mean()` (K=1 ⇒ none).
8. Emit w as raw weights. Engine owns eligibility zeroing, gross=1, caps, shift(1), costs,
   funding, vol-target.

## 5. Data notes / NaN discipline

Kline-only signal — full IS coverage from 2020-01 (no OI/ratio NaN cliff). Dead/delisted names
have NaN closes after death → NaN returns → NaN scores → flat; the eligibility mask removes
them from the ranking cross-section. New listings need max(W_beta·MP-frac, L) candles of
history before entering the book — acceptable, the top-40 always contains seasoned names.

## 6. Parameter plan (ranges + rationale; baseline in bold)

| Param | Range | Rationale |
|---|---|---|
| L (formation) | {42, 63, **126**, 168, 252} candles (2–12 wk; plateau target 2–8 wk) | narrative persistence horizon; equity lit uses 6–12 mo, crypto rotations are ~5–10× faster |
| g (skip gap) | {0, **3**, 6} candles (0–2 days) | 1–3 day reversal contamination |
| W_beta | {180, **270**, 540} candles (60/90/180 d) | beta stability vs adaptivity |
| market factor | {**EW**, DVW} | EW = broad alt factor; DVW ≈ BTC/ETH factor |
| scaling | {raw-sum, **t-stat**} | t-stat normalizes residual vol across names (Blitz-style residual momentum) |
| K (EMA span) | {**1**, 3, 6, 9} candles | turnover control vs signal lag |
| weighting | {**centered rank**, top/bottom-12 equal-weight} | rank = breadth + low turnover; quantile = concentration |
| beta clip | fixed [0, 3] | not tuned |
| mp fractions | fixed (W_beta//2, 0.8·L) | not tuned |

## 7. Selection rule (pre-registered — applied verbatim, plateaus over peaks)

1. e01/e02 context anchors (plain XS momentum; residual baseline). No selection from these.
2. Scaling (raw-sum vs t-stat): the variant with the higher MEDIAN Sharpe across the L sweep
   at baseline settings wins.
3. L*: center of the widest contiguous run of L values with Sharpe ≥ max(0.8·best, best−0.3);
   ties → the L whose ±1-step neighbors have the higher minimum.
4. W_beta / market factor: keep baseline (270, EW) unless an alternative beats it by > 0.3 at
   the plateau MINIMUM across L* and its neighbors (parsimony bias, pre-registered).
5. g: keep 3 unless an alternative beats it by > 0.3 at L*.
6. K: smallest K with 1× Sharpe within 0.1 of the best K; tiebreak = higher 2×-stress Sharpe.
7. Weighting: centered rank unless top/bottom-12 beats it by > 0.3 at BOTH 1× and 2×.
8. Final spec must pass: 2×-stress Sharpe > 0, median names/side ≥ 5, F2 bull-exclusion > 0.

Budget: ≤ 14 logged experiments (each sweep = one logged experiment); hard cap 40.

## 8. Risk register

- Momentum crash at regime turns (May-2021 type): structural; mitigated by residualization +
  the engine vol-target; accepted.
- Funding drag on crowded-long winners: monitored via `total_funding_pnl`; kill condition F4.
- Turnover: rank book at multi-week L expected ~30–80×/yr annualized; K sweep controls; the
  2×-stress tier is the honesty check.
- Universe churn: rank-based cross-section recomputed each candle over the CURRENT eligible
  set; a coin ejected from the top-40 is force-closed by the engine (costed) — no action.
- Selection overfit: small pre-registered grid, plateau-median rules, parsimony bias.

---

## 9. Results (scratch-evaluator numbers — same engine code path as `team-run`
## (`conform_raw` → `net_series` → `evaluate`); `is_report.md` will cite ONLY `team-run` output)

Experiments e01–e10 (10 of 40 budget), ledger: `experiments.jsonl` (evaluator-stamped).

Anchors (e01/e02): plain XS momentum 0.885 @1×; residual version 1.136 — residualization
adds +0.25 Sharpe, doubles the bear bucket (1.22 vs 0.50), lifts ex-bull-2021 (0.69 vs 0.51).
Mechanism confirmed: the improvement is exactly where the theory says (regime turns).

Falsifier status — NONE fired:
- F1 plateau median over L∈{42,63,126,168}: ≈ 1.05 (tstat), ≈ 1.05 (sum) — PASS (≫ 0).
- F2 ex-bull-2021 Sharpe of final spec: 0.904 — PASS.
- F3 2×-stress Sharpe of final spec: 0.927 — PASS.
- F4 funding-on 1.304 ≥ funding-off 1.178 — PASS (funding is a small tailwind:
  cumulative funding P&L +0.111 on the unlevered book; no carry-drag illusion).

Selection-rule application (verbatim, Section 7):
- Rule 2 scaling: tstat (median 0.960 vs 0.930 over full L sweep).
- Rule 3 L*: threshold max(0.8·1.282, 1.282−0.3) = 1.026 → runs {63},{168} tie at width 1;
  neighbor-min tiebreak 0.859 vs 0.838 → **L* = 63**.
- Rule 4: (270, EW) retained — best alternative min over {42,63,126} was 0.891 ((540,DVW))
  vs baseline 0.859: +0.03 ≪ 0.3.
- Rule 5: g=3 retained — g=0 scored 1.287 vs 1.136: +0.15 < 0.3. (Noted honestly: g=0 also
  wins at the final K=3 point, 1.49 vs 1.30; the pre-registered rule keeps g=3 and we do NOT
  post-hoc switch to the peak.)
- Rule 6: K=3 (best 1× = 1.304 at K=3; K=1 is 0.168 out of band; smallest in-band K = 3).
- Rule 7: centered rank retained (tb12: 1.303/0.872 — no > 0.3 edge, worse at 2×).
- Rule 8 gates: all pass (see falsifier status; breadth 19/19 median names per side).

Final spec headline (e09):

| metric | value |
|---|---|
| net IS Sharpe @1× | **1.304** |
| net IS Sharpe @2×-stress | **0.927** |
| maxDD (vol-targeted net) | −0.367 |
| ann. turnover | 118.6× |
| median names long/short | 19 / 19 |
| regime Sharpe bull / bear / chop | 1.93 / 1.33 / −0.21 |
| total funding P&L / total cost (unlevered) | +0.111 / −0.337 |
| ex-bull-2021 Sharpe | 0.904 |
| positive months | 30/54; worst month −13.4% (2023-03) |
| yearly Sharpe 2020..2024H1 | +2.08, +2.04, +0.91, −0.11, +1.02 |

Plateau confirmation (e10) — one-step perturbations around the final spec, 1× / 2×:
L=42: 1.12/0.68 · L=126: 1.10/0.87 · w_beta=180: 1.25/0.87 · w_beta=540: 1.24/0.88 ·
g=0: 1.49/1.11 · g=6: 0.97/0.61 · K=2: 1.27/0.81 · K=4: 1.30/0.97 · DVW: 1.22/0.86.
All nine neighbors ≥ 0.97 @1× and > 0.6 @2× — a plateau, not a peak.

Known weakness (reported with the same precision as the strengths): the chop bucket is
−0.21 and calendar-2023 is −0.11 — narrative-rotation chop is this mechanism's worst weather,
exactly as pre-registered in Section 2. No chop-specific patch was added (that would be
in-sample regime-fitting).

## 10. QE SPEC (final — zero ambiguity; implement WITHOUT importing the evaluator)

`strategy.py` exposes `build_raw_weights(pn, aux) -> pd.DataFrame`. Imports allowed:
numpy, pandas (plus stdlib-math/teamlib if needed). No file I/O, no network, no subprocess,
no randomness (`aux['seed']` is NOT used — the strategy is deterministic by construction).
No hard-coded symbol names or column counts anywhere.

Fixed parameters (FINAL — no free parameters left):
`W_BETA = 270` (candles), `MP_BETA = 135`, `L = 63`, `MP_L = 51`, `G = 3`, `K_EMA = 3`,
`BETA_CLIP = (0.0, 3.0)`, `MIN_FACTOR_NAMES = 5`.

Exact computation (pandas semantics; order of operations is normative):

```python
def build_raw_weights(pn, aux):
    close = pn["close"]                                   # DatetimeIndex × symbols
    elig = (aux["eligibility"]
            .reindex(index=close.index, columns=close.columns)
            .fillna(False).astype(bool))                  # widening-safe: unknown cols False
    r = np.log(close.where(close > 0)).diff()             # log returns; NaN-tolerant
    valid = r.notna() & elig
    m = r.where(valid).mean(axis=1)                       # EW eligible-mean factor
    m = m.where(valid.sum(axis=1) >= 5)                   # MIN_FACTOR_NAMES
    cov = r.rolling(270, min_periods=135).cov(m)          # column-wise rolling cov vs m
    var = m.rolling(270, min_periods=135).var()
    beta = cov.div(var, axis=0).clip(0.0, 3.0)
    e = r.sub(beta.mul(m, axis=0))                        # residual; NaN if any input NaN
    s = e.rolling(63, min_periods=51).mean() / e.rolling(63, min_periods=51).std()
    s = s.replace([np.inf, -np.inf], np.nan)              # guard sd==0 degenerate rows
    s = s.shift(3)                                        # skip-gap G (shift BEFORE masking)
    s = s.where(elig)                                     # rank only the CURRENT top-40
    rk = s.rank(axis=1, pct=True)                         # method='average', NaN kept
    w = rk.sub(rk.mean(axis=1), axis=0)                   # centered rank ⇒ exact zero-sum
    w = w.fillna(0.0)                                     # NaN = flat
    w = w.ewm(span=3, adjust=True).mean()                 # turnover smoothing K_EMA
    return w                                              # raw signed weights; engine owns rest
```

Normative details:
1. Symbol set = `pn["close"].columns` at runtime. Never enumerate names. The eligibility
   reindex (index AND columns, `fillna(False)`) makes synthetic/widened columns permanently
   ineligible → score NaN → weight 0 → no crash (harness WIDENING).
2. All rolling ops use pandas defaults beyond the stated `window`/`min_periods` (ddof=1 for
   var/std/cov). `rank(axis=1, pct=True)` uses default `method='average'`,
   `na_option='keep'`. Row-mean of ranks uses default skipna.
3. Causality: every row-t output depends only on data ≤ t (close[t] and aux row t are
   same-bar-usable per charter). No `shift(-…)`, no reversed windows, no global stats.
   `ewm(adjust=True)` is causal and truncated-replay-safe (head of panel is never cut).
4. NaN rules (already encoded above): close ≤ 0 or missing → NaN return; NaN propagates
   through beta/residual/score; all-NaN rows produce an all-zero weight row after
   `fillna(0.0)`. NO other imputation of any kind.
5. Emit the FULL panel-index DataFrame (warm-up rows are zero rows). The engine applies
   eligibility zeroing, gross normalization, caps, `shift(1)`, costs, funding, vol-target.
6. `aux` usage: ONLY `aux["eligibility"]`. Funding/OI/ratio panels are deliberately unused.

Validation targets for the QE (scratch-evaluator reference, must reproduce via `team-run`
to rounding): Sharpe@1× 1.304, Sharpe@2× 0.927, ann_turnover 118.6, maxDD −0.367,
total_return 4.020, median names 19/19, regime bull/bear/chop 1.93/1.33/−0.21,
total_funding_pnl +0.1106, total_cost 0.3369. Any mismatch = investigate wiring, NEVER tune.

`test_strategy.py` (QE-owned) must at minimum assert: (a) future corruption of klines /
funding / OI / eligibility rows > t leaves weights at rows ≤ t bit-identical; (b) determinism
across two calls; (c) widening with junk synthetic columns neither crashes nor changes
original columns' weights; (d) an all-NaN close row yields an all-zero weight row; (e) output
index/columns equal `pn["close"]`'s.
