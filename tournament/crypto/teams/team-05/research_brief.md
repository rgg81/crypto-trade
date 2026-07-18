# team-05 research brief — cross-sectional taker-flow imbalance (t05-taker-flow-imbalance-v2)

Status: PRE-REGISTERED before any experiment was run. The hypothesis map, parameter grids,
selection rule, and falsifier below were written before reading any IS result. The QE SPEC
section at the bottom is finalized only after the pre-registered selection rule has been
applied to logged experiment output; the selection rule itself is fixed here and may not be
changed after results are seen.

## 1. Mechanism

Every perp trade has a maker and a taker; `taker_buy_quote_volume / quote_volume` measures
what fraction of each candle's dollar volume was initiated by aggressive (spread-crossing)
buyers. Crypto perp flow is retail-dominated and herding-prone: narratives, listings,
influencer attention, and liquidation cascades produce sustained one-sided aggressive flow
that arrives in waves over days, not in one candle. Market makers absorb that flow into
inventory and lean their quotes against it, so price adjusts to persistent demand pressure
with a lag — sustained aggressive buying that has not yet fully moved price predicts
continuation. At long horizons the same measure becomes a crowding proxy: a name that has
been aggressively net-bought for many weeks is attention-saturated, crowded long (typically
with positive funding), and its marginal buyer is exhausted — predicting underperformance.

Why this exists in crypto perp markets specifically: no fundamental anchor, high retail
share, reflexive attention dynamics, and leverage that turns crowded flow into forced
unwinds. The signal is derivable purely from klines (full 2020-01 history, no OI/ratio NaN
cliff), is naturally cross-sectional and two-sided (breadth-safe under the organizer caps),
and its smoothing window is a direct turnover throttle at 8h cadence.

## 2. Pre-registered hypothesis map (direction × horizon)

Let TBR_W(i,t) = [Σ over last W candles of taker_buy_quote_volume] /
[Σ over last W candles of quote_volume] — the volume-weighted aggressive-buy share.

- **H1 — herding continuation (PRIMARY): sign = +1, W ∈ {6, 12, 21, 42} candles (2–14 days).**
  Long the names with the highest smoothed aggressive-buy share, short the lowest. Rationale:
  multi-day herding waves + lagged absorption of demand pressure. This is the band I expect
  to trade.
- **H2 — exhaustion fade (SECONDARY): sign = −1, W ∈ {63, 90, 126, 180, 270} candles
  (3 weeks – 3 months).** Short the names the crowd has been aggressively buying for months,
  long the neglected/sold names. Rationale: attention saturation + crowded-long unwind; this
  band should also COLLECT funding (crowded-long names have positive funding).

Discipline: each band's direction is FIXED here. Flipping the sign of a band after seeing
results is prohibited and would be an overfit laundering move; a band that only works with
the wrong sign counts as a FAILED band. The two bands are disjoint in W by construction
(boundary between 42 and 63 chosen a priori as ~2–3 weeks, where equity-retail literature
and crypto attention dynamics suggest continuation decays into reversal).

## 3. Expected behavior per regime tag (pre-registered)

For H1 (continuation): strongest in flow-rich trending regimes — 2020-21 bull, 2021 ATH run,
ETF bull; positive in the sustained 2022 bear (persistent aggressive selling of the weakest
names → short side works); weakest/negative in chop (FTX-aftermath, post-halving) and at
V-reversals (May-2021 snapback, COVID rebound) where the herd flips. Funding P&L expected
NEGATIVE (long crowded-buy names pays funding) — price alpha must exceed the drag.

For H2 (fade): strongest in chop and post-crash normalization; collects funding; worst in
sustained manias (late-2020/early-2021) where crowded buying stays right for months.

## 4. Falsifier (pre-registered)

Plateau definition (fixed): within a band, a run of ≥3 ADJACENT grid windows whose net IS
Sharpe @1× (full costs + funding, evaluator `net_series`/`evaluate`) is > 0.5 AND whose
2×-stress Sharpe (cost_mult=2, slip_mult=2) is > 0.

- A band QUALIFIES iff it contains a plateau in its pre-registered direction.
- **THE FAMILY IS DEAD (falsifier fires) iff NEITHER band qualifies.** In that case I report
  the negative result plainly and either request the one documented pivot or take best
  honest book / DNF — no sign flips, no post-hoc horizon bands, no rescue variants.

## 5. Signal construction (fixed a priori)

1. `tbr = taker_buy_quote_volume.rolling(W, min_periods=ceil(0.75·W)).sum() /
   quote_volume.rolling(W, min_periods=ceil(0.75·W)).sum()` — NaN where the denominator has
   insufficient history or is ≤ 0.
2. Same-bar eligibility gate: signal considered only where `aux['eligibility']` is True at t
   (organizer past-only mask; engine re-masks anyway — ranking inside the mask keeps ranks
   undistorted by dead/ineligible names).
3. Cross-sectional transform: percentile rank across eligible non-NaN names at each candle,
   then subtract the row mean → sum-zero weights in ≈[−0.5, +0.5]. Rank (not z-score) is
   pre-registered: robust to thin-name ratio outliers.
4. `raw = sign × demeaned_rank`; NaN/ineligible → 0 (flat). Engine owns caps, lag, costs,
   funding, vol-targeting.

## 6. Parameter plan & selection rule (fixed a priori)

Grid, e01 (the hypothesis map): sign ∈ {+1 on H1 band, −1 on H2 band}, W as in §2, linear
demeaned-rank weights, no extra smoothing. Both cost tiers computed for every cell.

Selection rule (mechanical):
1. Apply the plateau test per band. If neither qualifies → falsifier fires (§4).
2. If one band qualifies → select it. If both qualify → select the band with the higher
   MINIMUM 1×-Sharpe over its best plateau run (ties: higher minimum 2×-stress Sharpe).
3. Selected W = the MIDDLE window (grid order; left-middle if even length) of the best
   qualifying run — plateau center, never the peak.
4. Refinements (each a logged experiment, each optional and adopted ONLY if it improves
   BOTH 1× and 2×-stress Sharpe at the selected W AND the same variant helps at the two
   adjacent grid windows in the same direction (no single-cell spikes), AND breadth stays
   ≥ floor):
   a. weight sharpening: top/bottom-quantile q ∈ {25%, 33%} vs linear ranks;
   b. turnover smoothing: EMA halflife h ∈ {3, 6, 12} candles on the final weight panel.
   Default if no variant qualifies: linear ranks, no smoothing.
5. Final config is then FROZEN into the QE SPEC. Robustness diagnostics (split-half IS,
   per-regime table, funding decomposition) are reported but do NOT feed back into
   parameter choice.

Budget intent: ≤ ~8 logged experiments for the whole program (map, densify, 2 refinements,
robustness, final confirmation), hard ceiling 40 per charter.

## 7. Known risks (pre-registered)

- Turnover: 8h cadence × ~6–11 bps/side at 1× (doubled at stress). Short-W continuation may
  be gross-alpha-positive but net-negative; the 2×-stress term in the plateau test is the
  guard. I will not select a config whose edge exists only at the 1× tier.
- Funding drag on H1 (long crowded-buy names pays funding) — monitored via
  `total_funding_pnl`; a band whose price alpha is fully consumed by funding will show it
  in the net numbers, which is what the plateau test sees.
- Universe churn: rank-based, mask-gated construction re-ranks each candle over whichever
  names are eligible — no per-name state, so entering/leaving coins are handled naturally.
- Breadth: ranking the full eligible set keeps ~20 names per side; floor risk only under
  quantile sharpening — checked at adoption time.

## 8. Results & selection log (written AFTER experiments e01–e06; scratch-evaluator numbers,
## see out/scratch/results_e0*.csv — is_report.md numbers will come ONLY from team-run)

- **e01 (hypothesis map):** H1 continuation qualified across its ENTIRE band — 1× Sharpe
  {W=6: 1.313, W=12: 1.473, W=21: 1.501, W=42: 1.427}, 2×-stress {0.285, 0.839, 1.049,
  1.126}, all cells pass (1× > 0.5, 2× > 0). H2 fade FAILED decisively: 1× Sharpe −1.81 to
  −1.00 across {63, 90, 126, 180, 270} — continuation persists even at 3-month horizons; no
  exhaustion reversal inside IS. Per §2 discipline H2's sign is not flippable; H2 is dead
  and reported as a negative result. **Falsifier (§4) did NOT fire** (H1 qualified).
- **Selection-rule application (§6.2–6.3):** qualifying runs in H1: {6,12,21}, {12,21,42},
  {6,12,21,42} with minimum 1× Sharpe 1.313 / 1.427 / 1.313 → best run = {12,21,42} →
  selected W = middle = **21** (7 days). Surprise vs §3: funding P&L of the continuation
  book is POSITIVE (+0.37 raw cumulative at W=21), not a drag — high taker-buy-share names
  do not carry the highest funding; the book collects net funding.
- **e02 (densify, diagnostic):** plateau smooth — 1× {W=15: 1.584, 18: 1.642, 21: 1.501,
  27: 1.300, 33: 1.322}, 2× {1.019, 1.141, 1.049, 0.911, 0.968}. W=18's higher point was
  NOT adopted (plateau-center discipline; e02 pre-declared non-selecting).
- **e03 (sharpening):** REJECTED by rule §6.4a — q=0.25 at W=21: 1× 1.500 (not an
  improvement over 1.501); q=0.33 worse on both tiers. Linear ranks retained (also better
  bear Sharpe and 2× the breadth).
- **e04 (EMA smoothing):** REJECTED by rule §6.4b — at W=21 no halflife improves BOTH tiers
  (hl=3: 1× 1.431 < 1.501 despite 2× 1.196 > 1.049); cross-window direction inconsistent
  (helps W=12, hurts W=42).
- **e05 (robustness diagnostics):** min_periods 0.5W vs 0.75W indistinguishable (1.499 vs
  1.501) — not load-bearing. Base-volume TBR equivalent (1.558/1.111) — quote version kept
  as pre-registered. Eligibility-gated ranking IS load-bearing in the right direction:
  ungated ranks degrade to 1.178/0.794 with a +0.18 net-long tilt and lopsided breadth —
  confirms the pre-registered gate. Informational: mean XS corr(flow rank, 21-candle
  momentum rank) = 0.44 — flow is related to but not a disguise of price momentum.
- **e06 (frozen-config confirmation):** 1× Sharpe 1.501, 2×-stress 1.049, maxDD −0.430,
  ann. turnover 173, breadth 20/20 (floor 5), mean net 0.0, total funding P&L +0.369 (raw),
  regime Sharpe bull 1.86 / bear 1.63 / chop 0.33, split-half 2.289 (2020-01→2022-03) vs
  0.722 (2022-04→2024-06), yearly msharpe 2020: 1.43, 2021: 3.50, 2022: 1.32, 2023: 0.88,
  2024-H1: 0.22. Honest read: the edge decays through time and is weakest in chop — every
  year positive, but the recent-regime expectation is ~0.2–0.9, not 1.5.

## 9. QE SPEC — FROZEN (zero ambiguity; implement exactly)

`build_raw_weights(pn, aux) -> pd.DataFrame`, pure, deterministic, past-only, column-set
agnostic (derive symbols from panel columns at runtime; never hard-code names or counts).
No randomness is used (`aux["seed"]` intentionally unused). Constants: `W = 21`,
`MIN_PERIODS = 16` (= ceil(0.75·21)). Exact transform order:

```python
tb  = pn["taker_buy_quote_volume"]          # candle × symbol, float
qv  = pn["quote_volume"]
num = tb.rolling(window=21, min_periods=16).sum()      # trailing sums, past-only,
den = qv.rolling(window=21, min_periods=16).sum()      # NaNs skipped by rolling.sum
sig = num / den.where(den > 0) - 0.5                   # NaN if den<=0 or <16 non-NaN candles

elig = (aux["eligibility"]
        .reindex(index=sig.index, columns=sig.columns)  # widening-safe alignment
        .fillna(False).astype(bool))                    # unknown/synthetic cols -> False
masked = sig.where(elig)                                # ineligible or NaN -> NaN

r = masked.rank(axis=1, pct=True)          # pandas defaults: ascending, average ties,
                                           # NaN excluded from the rank
w = r.sub(r.mean(axis=1), axis=0)          # row-demeaned -> sum-zero long/short book
return w.fillna(0.0)                       # NaN = flat (sign is +1: NO negation anywhere)
```

Fixed decisions the QE must NOT revisit: quote-volume TBR (not base-volume); rolling-sums
ratio (not mean of per-candle ratios); the −0.5 centering (cosmetic after demeaning — keep
for interpretability); eligibility-gated ranking (load-bearing, e05); linear demeaned
percentile ranks (no quantile sharpening, no rank powers — e03 rejected); no EMA/other
smoothing of weights (e04 rejected); no per-name state, no NaN forward-fills, no clipping.
Rows with <2 eligible non-NaN names or insufficient history come out all-zero (flat) —
correct behavior, do not "fix". The engine owns eligibility re-masking, gross normalisation,
caps, the decision lag, costs, funding, and vol-targeting.

Team tests should assert: determinism (two calls bit-equal); past-only (corrupting klines
AND aux after candle T leaves rows ≤ T bit-identical); widening (extra synthetic columns in
pn/aux neither crash nor change existing columns' weights); all-NaN and empty-eligibility
rows produce flat rows; output index/columns equal `pn["open"]`'s.
