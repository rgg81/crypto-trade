# team-02 — Research Brief: OI-Crowding Fade (`t02-oi-crowding-fade-v1`)

Status: PRE-REGISTRATION written 2026-07-18 BEFORE any experiment was run (ledger `e01+`
timestamps postdate this file's creation). The final "QE SPEC" section (§9) is appended after
the experiment program completes; §1-§8 are frozen at pre-registration and not edited
afterward.

## 1. Mechanism

When open interest builds up sharply while price stagnates or makes little progress, leverage
is stacking without the directional conviction being resolved. Every new contract adds a
liquidation trigger to a dense band around the entry zone. Liquidation engines are mechanical
and non-discretionary: once price moves against the crowded side, forced-flow cascades convert
small adverse moves into large ones. Positioning AGAINST the direction the crowd pressed
(shorting names where OI built as price drifted up = crowded longs; longing names where OI
built as price drifted down = crowded shorts) harvests the unwind premium before/into the
cascade.

## 2. Why it exists and persists in crypto perp markets

- Perp leverage demand is retail-driven, inelastic, and herding — build-ups are observable in
  the aux `oi` panel while most of the flow that creates them does not condition on it.
- Liquidations are forced, mechanical flow with predictable direction once crowding is
  measurable; the counterparty earning the premium must warehouse inventory risk into
  potential cascades, so the premium is compensation, not free money.
- On Binance perps, the arbitrage capital that would lean against crowded builds early is
  balance-sheet constrained and mostly delta-hedges funding, not OI, so the OI dimension of
  crowding is less arbitraged than the funding dimension.
- Distinct from adjacent registered families: NOT funding-level carry (team-01; funding is
  never a signal input here), NOT post-wipeout snap-back (team-09; we position on the BUILD
  before/into the unwind, not on the flush candle's aftermath).

## 3. Data & known limitations (accepted at registration)

- `aux['oi']` (= `sum_open_interest`, sum of 5-min OI snapshots over the 8h candle) is NaN
  before ~2020-09 and for dead/delisted names' missing history. The strategy is FLAT wherever
  the signal is not computable; the months 2020-01 → ~2020-09 therefore contribute ~0 monthly
  returns and DILUTE the objective Sharpe (~8-9 of 54 monthly points near zero). Accepted
  honestly; no fallback signal is allowed (it would be a second mechanism family).
- `sum_open_interest` is a SUM of 5-min samples: exchange data gaps within a candle create
  fake OI collapses. Mitigation: cross-sectional RANK transforms (bounded influence), and no
  raw-level thresholds.
- `oi_value` mixes price into the level; the contract-count panel `oi` is the build measure.
- COVID-crash regime (2020-02/03) is NOT testable for this family. Pre-registered statement:
  the regime scorecard's "bear" bucket will be dominated by May-2021 + 2022; we claim nothing
  about COVID behavior.

## 4. Signal candidates (pre-registered formulas)

Notation, per candle t: eligible set E_t = {i : eligibility[t,i] AND oi[t,i]>0 AND
oi[t−L,i]>0, both finite}. For i ∈ E_t:

- build:      b_i = log(oi[t,i]) − log(oi[t−L,i])
- move:       r_i = log(close[t,i]) − log(close[t−L,i])
- crank_t(x): cross-sectional rank of x among E_t (average ties), scaled (rank−0.5)/N_t ∈ (0,1)
- σ_i:        rolling std of 1-candle log close returns, window 42, min_periods 30 (form C only)

Forms (raw signal s_i; names outside E_t get s_i = NaN → 0 after fill):

- **Form A — build-gated sign fade**: g_i = max(0, (crank(b_i) − q)/(1 − q)), gate q = 0.6;
  s_i = −g_i · sign(r_i). Fades only above-quantile builds; direction = concurrent drift.
- **Form B — symmetric double-rank**: s_i = −(2·crank(b_i) − 1) · (2·crank(r_i) − 1).
  High build fades the move; OI collapse FOLLOWS the move (cascade/squeeze-follow leg).
- **Form C — stagnation-weighted A**: s_i = −g_i · sign(r_i) · (1 − crank(|r_i| / σ_i)).
  Emphasizes builds absorbed with little price progress (leverage stacking w/o resolution).

Post-transform: fill NaN → 0.0, then per-column EMA smoothing `ewm(span=k).mean()`
(k = 1 means no smoothing). Emitted raw weights = smoothed panel (engine owns eligibility
mask, gross-norm, caps, lag, costs, funding, vol-target).

## 5. Parameter plan (pre-registered grid)

- Lookback L ∈ {3, 6, 9, 21, 42} candles (1, 2, 3, 7, 14 days) — cascade-relevant build
  horizons; below 1d is noise + turnover, above 14d is stale positioning.
- Gate q ∈ {0.5, 0.6, 0.75} (forms A/C only; 0.6 is the default, others robustness).
- Smoothing k ∈ {1, 3, 6, 9} candles.
- Core grid for the FALSIFIER: forms A and B × L grid at q = 0.6, k = 1.

## 6. Pre-registered falsifier

**The family is DEAD if, over the core grid (A, B × L ∈ {3,6,9,21,42}, q=0.6, k=1, evaluated
by the tournament evaluator at 1× costs, funding on, full IS window incl. the flat pre-
coverage months), no form has a contiguous plateau of ≥ 2 adjacent L values with net IS
Sharpe > 0.** Smoothing (k) may be applied to the plateau check only if k=1 turnover costs
are the sole reason for failure (cost-, not signal-failure — reported honestly either way).

Additional SPEC-kill criteria (kill the candidate spec, force re-selection inside the family
or an honest negative report): 2×-stress Sharpe ≤ 0; breadth median < 5 names/side; > 90% of
cumulative P&L from a single regime bucket while another bucket is materially negative
(< −0.5 Sharpe).

## 7. Expected behavior per regime window (pre-registered)

| Window | Tag | Expectation |
|---|---|---|
| 2020-01→2020-02-14 pre-COVID bull | bull | FLAT (OI NaN — no claim) |
| 2020-02-14→03-13 COVID crash | bear | FLAT (OI NaN — no claim) |
| 2020-03-13→2021-04-14 bull | bull | Live from ~2020-09. Modest/mixed: leverage waves build & flush (Jan/Feb-2021); fading crowded longs bleeds in the steepest ramps |
| 2021-04-14→07-20 May-2021 crash | bear | SIGNATURE window: record OI + stagnating price into April, cascade in May. Expect clearly positive; a loss here challenges the mechanism |
| 2021-07-20→11-10 run to ATH | bull | Mixed; Sept-2021 flush positive, ramp weeks negative |
| 2021-11-10→2022-11-21 macro bear | bear | Positive-to-flat: repeated cascade legs (LUNA, 3AC, FTX); symmetric form may also catch short-squeeze legs (Jul-2022) |
| 2022-11-21→2023-10-16 FTX-aftermath chop | chop | Positive: range-bound positioning builds mean-revert; crowding fades pay in chop |
| 2023-10-16→2024-03-14 ETF bull | bull | Weakest window expected: persistent leverage build with trending price; drawdown risk concentrated here |
| 2024-03-14→07-01 post-halving chop | chop | Positive: repeated leverage flushes (Apr-2024) in a range |

Aggregate: bear + chop strong, bull flat-to-negative; the balanced long/short book plus
breadth should keep bull bleed bounded. If instead bull is strongly positive and bear/chop
negative, the mechanism story is wrong (report as such).

## 8. Selection rule (pre-registered — plateaus over peaks)

1. **Form choice (A vs B):** higher MEDIAN net IS Sharpe @1× across the L grid (k=1, q=0.6).
2. **L choice:** center of the widest contiguous plateau with Sharpe ≥ 0.8 × (form's grid
   max); tie → larger L (lower turnover).
3. **Smoothing k:** maximize min(Sharpe@1×, Sharpe@2×-stress) over k ∈ {1,3,6,9}; tie →
   smaller k.
4. **Refinements (form C stagnation weight; q ∈ {0.5, 0.75}; symmetric-vs-build-only):**
   accepted ONLY if BOTH 1× and 2× Sharpe improve by ≥ 0.10 over the incumbent; otherwise
   keep the simpler incumbent.
5. Final spec must satisfy: Sharpe@1× > 0, Sharpe@2× > 0, breadth median ≥ 5/side, no
   single-regime concentration (§6).

Experiment ledger plan (≤ ~12 material experiments; budget 40): e01 EDA/coverage/IC; e02 grid
A×L; e03 grid B×L; e04 smoothing on winner; e05 refinements C/q; e06 build-only vs symmetric
decomposition; e07 robustness (2×, funding-off part attribution, breadth, regime table);
e08 final-spec confirmation via team-run (numbers for is_report.md). IDs beyond e08 only if a
result forces a documented follow-up.

## 9. RESULTS & VERDICT (appended after experiments e01-e06 — §1-§8 above are unedited)

### 9.1 Data amendment (post-e01, documented — supersedes the §3 coverage assumption)

The chartered "OI NaN before ~2020-09" materially understates the gap. Measured coverage of
eligible names with finite `oi` (mean names/candle): **0-1 until 2021Q3, 13.8 in 2021Q4,
~38-40 from 2022Q1**. Real breadth starts ~Dec-2021 (Binance futures-metrics archive start).
Consequences: the active window is ~30 of 54 IS months; the §7 "signature" May-2021 window is
NOT testable (0-1 names); the bear bucket reduces to the 2022 legs. With < 2 covered names
the pre-registered forms are automatically flat (rank of a singleton = 0.5 ⇒ s = 0).

Also documented (e01 → e01b): an IC scan of signal[t] vs `ret_fwd[t]` is same-candle
contaminated (`ret_fwd[t]` spans candle t, overlapping the signal's own r_L window); the
engine-true horizon is `ret_fwd[t+1]`. e01's −0.21 "continuation IC" was this artifact; all
conclusions below use the corrected horizon or the evaluator itself.

### 9.2 Falsifier verdict: **FIRED — family dead on this substrate**

Core grid (§6: forms A, B × L ∈ {3,6,9,21,42}, q=0.6, k=1, evaluator, 1× costs, funding on,
full IS window): **all 10 cells negative** — A: −1.45..−1.66, B: −0.80..−2.15. No plateau,
no positive cell. The smoothing/cost clause does NOT apply: gross (cost-free, funding-off)
Sharpe is negative in every decomposed config (e04: −0.25..−0.94), i.e. signal-failure, not
cost-failure. Losses concentrate in the LONG leg (longing "crowded-short" OI-builds with
falling price = catching 2022 cascade knives; −0.7..−1.3 cumulative, mostly 2022) while the
short leg wins 2022 and gives it back in 2023 — both fully-covered years are negative.

Pre-registered refinements fare no better (e05, e06):
- Form C (stagnation-weighted — the registry one-liner's purest expression): gross
  −0.42..−1.23, net −1.49..−2.06 across L × q ∈ {0.6, 0.75}.
- Inverse-vol risk-normalization (diagnosis-driven rescue): 11/12 cells gross-negative;
  best cell ivB L=42 gross +0.10, net −0.66.
- Equal-weight sign-only tercile fade: gross −0.99, net −1.69.
- DIAGNOSTIC reverse sign (OI-confirmation continuation — NOT in-family): gross only
  +0.25..+0.27 and net −0.65/−0.34 @1× — no tradable edge of either sign at these costs.
- Active-window-only (2022-01→2024-06) Sharpe of the least-bad fade: −1.09 (worse than the
  −0.80 full-window figure) — the flat-month dilution masks nothing.

Economic reading: at the 8h horizon on top-40 perps, OI expansion accompanying a move is
participation/confirmation — extreme OI-backed moves CONTINUE over the next candle
(held-candle mean of top-build-quintile down-moves: −21 bps) — and quiet builds resolve with,
not against, their drift. The unwind alpha this family hunts lives at event scale (the flush
itself) or requires positioning-direction panels (funding / LS-ratios) that belong to other
teams' registered families. Within the registered fade mechanism there is no honest positive
configuration; continuing to mine variants here would be exactly the laundering this charter
bans.

### 9.3 Status

**No QE SPEC is issued from this family.** Per the charter (§6, one documented pivot) and
the orchestrator's process note, a pivot request with a concrete replacement family
pre-proposal has been submitted to the orchestrator; this brief remains as the documented
negative result for `t02-oi-crowding-fade-v1` (experiments e01-e06, evaluator-stamped).
The pivot to `t02-breakout-channel-v2` was APPROVED and journaled; Part II below.

---

# PART II — Breakout / Channel (`t02-breakout-channel-v2`) — PIVOT FAMILY

Status: PRE-REGISTRATION of §II.1-§II.6 written BEFORE the first breakout experiment (ledger
continues at e07; the evaluator-stamped e07 timestamp postdates this edit). §II.7 (results)
and §II.8 (QE SPEC) are appended after the experiment program; §II.1-§II.6 are frozen now.

## II.1 Mechanism

Crypto trends ignite reflexively: a range escape (price clearing its own N-candle channel
extreme) forces short-covering / liquidates the opposing side, triggers stop and breakout
flow from systematic and retail participants, and draws momentum-chasing retail in — with no
cash-flow anchor to lean against, the move persists until exhaustion. Congestion (price
inside its channel) carries no signal. The tradable structure is a per-name STATE: long
after an upside channel escape, short after a downside one, held with a hysteresis exit
(opposite shorter channel) so the position survives noise but dies when the trend structure
breaks. This is per-name ANCHORING to the coin's own range — distinct from t04's continuous
multi-horizon trend sign/magnitude (menu #10) and from t03's cross-sectional residual
momentum (#9); no volume/participation conditioning is used anywhere (t10's family, #14).

## II.2 Why it persists in crypto perp markets

Stops and liquidations cluster just beyond range extremes (mechanically observable in every
cascade); breakout flow is partly FORCED (liquidations of the trapped side), partly herding
(retail chases confirmed moves). The counterparty warehousing this risk must fade confirmed
escapes in an asset class with fat trend tails — expensive — so the premium survives. The
known cost is whipsaw bleed in chop; the edge is long-vol-like convexity in trends.

## II.3 Signal forms (pre-registered formulas; price-only, per-name)

Let close[t,i] be the 8h close panel. All windows use PRIOR data only or same-bar close[t]
(charter same-bar convention). NaN close (unlisted/dead) ⇒ signal NaN ⇒ 0 after fill.

- **Form D — Donchian state with hysteresis (M = round(N/3), fixed ratio):**
  entry_hi[t] = max(close[t−N .. t−1]), entry_lo[t] = min(close[t−N .. t−1]) (strict
  min_periods = N; NaN until warmed). exit_lo[t] = min(close[t−M .. t−1]),
  exit_hi[t] = max(close[t−M .. t−1]) (min_periods = M).
  State machine per name, state ∈ {−1, 0, +1}, start 0:
  0→+1 when close[t] > entry_hi[t]; 0→−1 when close[t] < entry_lo[t];
  +1→0 when close[t] < exit_lo[t]; −1→0 when close[t] > exit_hi[t];
  re-entry allowed same candle a state is exited if the opposite entry also triggers
  (evaluation order: exit first, then entry). Raw signal s = state.
- **Form E — channel position with deadband:**
  hi_N[t] = max(close[t−N+1 .. t]), lo_N[t] = min(close[t−N+1 .. t]) (min_periods = N,
  window INCLUDES t). c = 2·(close − lo_N)/(hi_N − lo_N) − 1 ∈ [−1, +1] (0 where
  hi_N = lo_N). Deadband d: s = sign(c)·max(0, |c| − d)/(1 − d). Default d = 0.25.

Optional transforms (refinement axis, not core): per-name inverse-vol sizing
w = s / max(σ, floor) with σ = rolling std of 1-candle log close returns, window 42,
min_periods 30, floor = cross-sectional 20th percentile of σ at t; EMA smoothing
`ewm(span=k)` on the final panel, k ∈ {1, 3, 6}. NaN→0 fill BEFORE smoothing.

## II.4 Parameter plan (pre-registered)

- N ∈ {30, 60, 90, 180} candles (10, 20, 30, 60 days) — crypto swing-to-position trend
  horizons (55-daily-candle classic ≈ 165 8h candles ≈ the 180 cell).
- Form D: M = round(N/3) fixed (single hysteresis dof, no separate M sweep).
- Form E: d = 0.25 in the core grid; d ∈ {0, 0.5} as refinement.
- Core grid for the FALSIFIER: forms D and E × N ∈ {30, 60, 90, 180}, raw sizing, k = 1.

## II.5 Pre-registered falsifier & expected regime behavior

**Family dead if, over the core grid (evaluator, 1× costs, funding on, full IS window), no
form has a contiguous plateau of ≥ 2 adjacent N with net IS Sharpe > 0.** Spec-kill (not
family-kill): 2×-stress ≤ 0; breadth median < 5/side; single-regime concentration (> 90% of
cumulative P&L from one regime bucket while another is < −0.5 Sharpe).

Expected per regime window: COVID crash + (shorts trigger; V-bottom whipsaw caps it);
2020-21 bull strongly + (longs); May-2021 crash + then whipsaw at the bounce; 2021 H2 bull
+; 2022 bear + (persistent breakdown shorts; mild funding drag when shorts pay negative
rates); FTX-aftermath chop − (whipsaw bleed — the family's known cost; target small, not
catastrophic); ETF bull +; post-halving chop mildly −. Aggregate: bull + bear positive, chop
negative-but-bounded. If instead chop is the ONLY positive bucket, the mechanism story is
wrong (report as such). Breadth risk is form D's state sparsity (few shorts in bulls) —
form E's continuous channel position is the structural mitigation; the floor is checked on
every grid cell.

## II.6 Selection rule (pre-registered — plateaus over peaks)

1. Form (D vs E): higher MEDIAN net IS Sharpe @1× across its N grid (raw, k=1) — BUT a form
   failing the breadth floor at its plateau cells is disqualified regardless of Sharpe.
2. N: widest contiguous plateau with Sharpe ≥ 0.8 × form's grid max; tie → larger N.
3. Inverse-vol sizing: adopt ONLY if it improves BOTH 1× and 2× Sharpe by ≥ 0.10.
4. Deadband d and smoothing k: maximize min(S@1×, S@2×); ties → d = 0.25, k = 1 defaults.
5. Final gates: S@1× > 0, S@2× > 0, breadth median ≥ 5/side, no single-regime concentration.

Experiment plan (ledger continues at e07; aim ≤ 25 total): e07 core grid form D; e08 core
grid form E; e09 inverse-vol on the winning plateau; e10 d/k refinement; e11 robustness +
decomposition (regime, funding, breadth, yearly); e12 final-spec confirmation. Follow-ups
only if a result forces one, documented in the ledger.

## II.7 RESULTS (appended after e07-e12; all numbers from the tournament evaluator)

### Falsifier status: NOT FIRED — wide positive plateau on the core grid

Core grid @1× (gross Sharpe in parens): form D — N=30 +1.56 (+1.74), N=60 +1.79 (+1.86),
N=90 +1.78 (+1.68), N=180 +1.23 (+1.23); form E — N=30 +1.57 (+2.10), N=60 +1.97 (+2.15),
N=90 +1.93 (+1.96), N=180 +1.16 (+1.20). Every cell of both forms positive, gross and net,
at both cost tiers.

### Selection audit trail (rules II.6, applied mechanically)

1. **Form:** D's plateau cells (N=60/90/180) have median shorts = 4 → breadth-floor DQ
   (exactly the pre-registered risk). E passes everywhere (10/14) AND has the higher grid
   median (+1.75 vs +1.67) → **form E**.
2. **N:** plateau ≥ 0.8×max(1.965)=1.572 → contiguous {30, 60, 90}; center → **N=60**.
   (Interaction check e11: at final d/k, N=90 scores +2.20 vs N=60 +2.07 — documented as
   plateau evidence; the pre-registered rule selects N=60 and was not post-hoc overridden.)
3. **Inverse-vol sizing (e09): REJECTED** — N=60 −0.08 @1×; N=90 +0.08 < +0.10 threshold.
4. **d × k (e10):** argmax min(S@1×, S@2×) = d=0.25, k=6 (min +1.821; turnover 268→124).
   Boundary check (e11): k=9 min +1.914, k=12 min +1.904 — a gentle plateau, not an
   edge-peak; selection stays inside the pre-registered grid at **k=6**.

### Final spec confirmation (e12, fresh end-to-end implementation)

| Metric (evaluator, full IS 2020-01→2024-06) | @1× | @2×-stress |
|---|---|---|
| Net Sharpe (monthly, √12) | **+2.0687** | **+1.8214** |
| MaxDD | −0.2884 | −0.3105 |
| Ann. turnover | 123.9 | — |
| Breadth median long/short | 17.0 / 18.0 | — |
| Mean gross / mean net | 0.830 / −0.007 | — |
| Regime Sharpe bull / bear / chop | +3.02 / +1.49 / +0.31 | — |
| Total funding P&L / total cost | +0.026 / 0.350 | — |
| Months | 54 | — |

Robustness (e11): half-samples +3.17 (2020-01→2022-03) / +1.14 (2022-04→2024-06) — both
positive, recent half weaker (honest expectation for the chop-heavier holdout era is nearer
the H2 figure than the full-window one). Yearly net: 2020 +1.33, 2021 +1.04, 2022 +0.19,
2023 +0.83, 2024H1 −0.09. Funding-off Sharpe +2.044 — the edge is price, not funding
harvest. Worst months: −13.8% (2022-02), −13.3% (2023-02), −11.6% (2020-05). All §II.5/§II.6
gates pass: S@1×>0, S@2×>0, breadth ≥5/side, no bucket <0, no single-regime concentration
(bull-heaviest, but bear +1.49 and chop +0.31 are both positive).

## II.8 QE SPEC — FINAL (zero ambiguity; the e12 reference implementation is normative)

**Family:** `t02-breakout-channel-v2` — per-name 60-candle channel position with deadband,
EMA-smoothed. Signal only; the engine owns eligibility, caps, lag, costs, funding,
vol-target.

**Constants (all fixed, no free parameters):** `N = 60`, `D = 0.25`, `K = 6`.

**`build_raw_weights(pn, aux)` — exact steps, in order (copy the function body from
`out/scratch/e12_final.py` verbatim into `strategy.py`):**

```python
N, D, K = 60, 0.25, 6
close = pn["close"]                                   # columns derived at runtime
hi  = close.rolling(N, min_periods=N).max()           # window INCLUDES row t (same-bar close)
lo  = close.rolling(N, min_periods=N).min()
rng = hi - lo
c   = (2.0 * (close - lo) / rng - 1.0).where(rng > 0, 0.0)   # channel position in [-1, 1]
s   = np.sign(c) * (c.abs() - D).clip(lower=0.0) / (1.0 - D) # deadband
s   = s.fillna(0.0)                                   # NaN (dead/unlisted close) -> flat
return s.ewm(span=K, adjust=True).mean()              # per-column causal EMA; adjust=True
```

Semantics the QE must preserve exactly:
- `.where(rng > 0, 0.0)` sets c = 0 where rng is 0 **or NaN** (unwarmed names: first N−1
  candles of any listing are flat). NaN `close` propagates to NaN c → caught by
  `fillna(0.0)` AFTER the deadband, BEFORE the EMA (a dying name decays to 0 via the EMA).
- No eligibility pre-mask, no aux usage at all (`aux` accepted, unused; no randomness, so
  `aux['seed']` unused). No cross-sectional transform — the signal is purely per-name.
- Column-set agnostic (everything from `pn["close"]` columns — WIDENING-safe); pure,
  deterministic, past-only (rolling windows end at t; `adjust=True` EMA is causal and
  prefix-stable, so truncated-replay and future-corruption harness checks pass by
  construction). Imports: numpy + pandas only (`teamlib` optional, not required).
- Emitted values are raw signed weights in [−1, 1] per name; NaN never emitted (0 = flat).

**Verification targets for `team-run` (must reproduce to the printed precision):**
sharpe@1× = +2.0687, maxdd@1× = −0.2884, ann_turnover = 123.9, months = 54,
median names long/short = 17/18, sharpe@2×-stress = +1.8214.

**test_strategy.py must include (team-owned):** determinism (two calls, identical output);
future-corruption self-check (corrupt rows > T in close/funding/oi/eligibility copies →
output rows ≤ T bit-identical); widening (add synthetic columns → no crash, original
columns' output unchanged); flat-warmup (first N−1 rows of a fresh column are 0); NaN-close
handling (a column going NaN decays to 0).
