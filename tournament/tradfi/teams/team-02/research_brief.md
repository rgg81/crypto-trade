# team-02 research brief — t02-52wk-high-anchor-v1 (52-week-high proximity / anchoring)

Status: PART A (pre-registration) written BEFORE any experiment was run.
PART B (final frozen spec for the QE) is appended only after the pre-registered
experiment ladder completes. Family approved in `registry.jsonl`
(`t02-52wk-high-anchor-v1`, backup-2 assignment after residual-momentum veto).

---

## PART A — PRE-REGISTRATION (written before experiment results)

### A.1 Economic mechanism

George & Hwang (2004): the trailing 52-week high acts as a salient ANCHOR. When good
news pushes a stock near its 52-week high, traders under-bid because "it already looks
expensive relative to the anchor" — the price is slow to break through, then continues
upward once the information is fully absorbed. Symmetrically, names far below their
trailing high have typically absorbed bad news slowly and keep underperforming.
Prediction: cross-sectionally, names NEAR their trailing high outperform names FAR from
it. This is underreaction driven by anchoring — distinct from return momentum: the
signal is a price LEVEL relative to a reference point, not a past-return window, and
empirically survives controlling for 12-1 momentum.

Why it should exist in this universe: ~65 liquid, heavily retail-traded US mega-caps on
perps — salient anchors ("all-time/52-week high" headlines) are exactly the attentional
reference points retail flow anchors on. The signal is slow-moving (a level vs a
trailing max), so daily-cadence turnover is intrinsically low — the 6 bps/side cost
regime favors this family.

### A.2 Signal design space (all pre-registered; nothing outside this space is tested)

Base signal, per name i, day t, computed from the team view panels ONLY:

    PH_i(t) = close_i(t) / rolling_max(high_i, L days, min_periods=M)(t)

- PH in (0, 1]; NaN when close_i(t) is NaN or fewer than M non-NaN highs in the window.
- Cross-sectional transform (row-wise over names with finite PH):
  - T-RANK: centered percentile rank: r = pctrank(PH) − rowmean(pctrank(PH))  [exactly dollar-neutral raw book]
  - T-Z:    winsorized z-score: z = clip(zscore(PH), −3, +3), then row-demeaned
  - T-Q:    quantile book: +1 top-q fraction, −1 bottom-q, 0 middle (q ∈ {1/5, 1/3})
- Sign is FIXED long-near-high / short-far-from-high (the GH direction). A sign flip is
  NOT in the design space — if the GH direction fails, the family is falsified (A.5).
- Optional temporal smoothing of the transformed signal: EWM halflife h ∈ {none, 5, 10, 21}
  days, then re-masked to names with finite PH(t) (no position without a current bar).
- Optional inverse-vol scaling: divide by sigma_i(t) = std of daily close-to-close
  returns over 63 days (min_periods=40); NaN sigma → flat.
- Lookback L ∈ {126, 189, 252, 315, 378}; history floor M ∈ {63, 126, 252} (default M = min(126, L/2)).

Raw weights = transformed (optionally smoothed / vol-scaled) signal, NaN = flat.
The ENGINE owns gross-normalisation, per-name cap 0.10, net cap 0.25, shift(1),
costs, and vol-targeting — the strategy emits raw signed rows only.

### A.3 Experiment ladder (budget: ≤ 8 material experiments of the 40-line cap)

1. exp-001 baseline: L=252, M=126, T-RANK, no smoothing, no vol-scaling; 1× and 2× cost.
2. exp-002 lookback plateau: L ∈ {126, 189, 252, 315, 378}, rest as baseline.
3. exp-003 transform: T-RANK vs T-Z vs T-Q(1/3) vs T-Q(1/5) at the plateau L*.
4. exp-004 smoothing: h ∈ {none, 5, 10, 21} at L*, best transform.
5. exp-005 inverse-vol scaling on/off at the incumbent config.
6. exp-006 history-floor M ∈ {63, 126, 252} sensitivity at the incumbent config.
7. exp-007 final confirmation: chosen config + one-step neighbors (plateau evidence),
   1× and 2×, full regime scorecard. (exp-008 reserve for one contingency only.)

### A.4 Selection rule (pre-registered, applied in order)

1. HARD: median names/side ≥ 5; net IS Sharpe @1× > 0 AND @2× > 0.
2. Plateau over peak: candidate's one-step neighbors on every swept axis must retain
   ≥ 80% of its @1× Sharpe; otherwise prefer the flattest neighborhood.
3. Among candidates within 0.10 Sharpe of the best plateau candidate, take the LOWEST
   annual turnover.
4. Regime sanity (informational tiebreak): prefer no regime bucket (bull/bear/chop)
   below −0.5 Sharpe.

### A.5 Falsifier (kills the family)

If no configuration in the A.2 space reaches net IS Sharpe @1× ≥ 0.30 with the breadth
floor satisfied and @2× > 0, the family is dead: I report the negative result with full
precision and do not launder a peak. (Registration falsifier restated for this family.)

### A.6 Expected regime behavior (prediction BEFORE results)

- Bull: best bucket — near-high names keep grinding up (anchored underreaction resolves upward).
- Bear: mildly positive-to-flat — far-from-high names fall further (short leg carries);
  but sharp panic sell-offs compress everything toward lows, hurting the long leg.
- Chop / V-recoveries (2012, 2016, 2019, post-2020-04): WORST bucket — junk rallies:
  beaten-down far-from-high names bounce hardest (short-leg squeeze). This is the
  family's known crash mode (analogous to momentum's 2009).
- Expected annual turnover: LOW for this class (signal is a slow level ratio) — one of
  the reasons this family was chosen for a 6 bps/side daily book.

---

## PART B — RESULT: FAMILY FALSIFIED (A.5 tripped)

Written after exp-001…exp-006 (ledger `experiments.jsonl`; raw evaluator JSON in
`out/scratch_exp-00*.json`). All numbers are `tournament.engine.run_is` output.

### B.1 Evidence

Sign-fixed GH direction (long near-high / short far-from-high), net IS Sharpe @1×:

| Axis swept | Configs | Sharpe @1× range |
|---|---|---|
| Lookback L (exp-002) | 126 / 189 / 252 / 315 / 378 | −0.72 … −0.77 (flat plateau, wrong sign) |
| Transform (exp-003) | rank / z / tercile / quintile | −0.56 … −0.76 |
| Smoothing (exp-004) | h = none / 5 / 10 / 21 | −0.76 … −0.49 (turnover 40→4.4×/yr; cost was never the problem) |
| Inv-vol scaling (exp-005) | on | +0.23 — ARTIFACT, see B.2 |

Best legitimate config: −0.49. Falsifier bar was ≥ +0.30 → **family dead in the
registered direction.** exp-006/007 slots of the original ladder (M-sensitivity, final
confirmation) are moot — M only shifts entry dates, it cannot flip a sign that is flat
across every other axis.

### B.2 The inv-vol "+0.23" is beta leakage, not anchoring

Dividing centered ranks by per-name vol inflates the low-vol near-high long leg:
mean_net = +0.21 (pinned at the 0.25 net cap), regime Sharpe bull +0.42 / bear −1.37.
That is a net-long low-vol beta book (another team's family, and below the falsifier
bar regardless). Rejected on mechanism fidelity.

### B.3 What the data actually says (exp-006 diagnostic, pivot-request evidence)

The REVERSED book — long names at a deep discount to their trailing high, short names
at/near it — is robustly positive on a wide plateau:

| Config (rank, reversed sign) | Sharpe @1× | Sharpe @2× | maxDD | ann. turnover | breadth L/S |
|---|---|---|---|---|---|
| L=252, h=21 | **+0.43** | **+0.40** | −0.39 | 4.4×/yr | 22 / 26 |
| L=252, h=10 | +0.40 | +0.35 | −0.40 | 6.6×/yr | 22 / 26 |
| L=189, h=10 | +0.36 | +0.31 | −0.37 | 7.2×/yr | 23 / 26 |
| L=315, h=10 | +0.39 | +0.34 | −0.41 | 6.2×/yr | 23 / 25 |
| L=252, h=5 | +0.38 | +0.31 | −0.40 | 9.5×/yr | 23 / 25 |
| L=252, unsmoothed | +0.17 | −0.13 | −0.40 | 40×/yr | 24 / 24 |

Regime scorecard (L=252, h=21): bull +0.57, chop +0.17, bear −0.46 — economically
coherent: beaten-down names keep falling during crashes, then get bought hard in
recoveries. Monthly t-stat ≈ 0.43 × √14.5 ≈ 1.6 at the point; the claim rests on the
PLATEAU (every smoothed config on every lookback positive at both cost tiers), not the peak.

Economic reading: this 65-name universe is liquid retail-favorite US mega-caps,
2010–2024 — a regime dominated by buy-the-dip flow, index inflows, and V-recoveries.
The GH anchor's known crash mode (junk rallies, pre-registered in A.6 as our worst
bucket) is the DOMINANT mode here. Distance below the trailing-high anchor behaves as
a DISCOUNT that closes, not an underreaction that continues.

---

## PART C — PROPOSED PIVOT (pre-registration, pending orchestrator approval)

**Proposed family: `t02-anchor-discount-contrarian-v1`** — long-horizon contrarian on
the 52-week-high anchor: long names trading at a deep discount to their trailing
252-day high, short names at/near the anchor. Mechanism: overreaction + systematic
dip-buying flow in retail-heavy mega-caps (De Bondt–Thaler long-horizon reversal,
anchored on the trailing high rather than a past-return window).

Distinctness: t03 owns SECTOR-RELATIVE SHORT-horizon reversion (mine: plain
cross-sectional, multi-month, own-anchor); t08 owns 1–5d reversal (mine: months);
t04 owns 12-1 momentum (correlated cousin, different variable and opposite trade);
t05 owns low-vol/BAB (my book stays inverse-vol-UNscaled and dollar-balanced
precisely to avoid that overlap). Not the reserved bear-gated TSMOM.

HONESTY NOTE: this family was reached by falsifying the registered GH direction; the
sign is an empirical IS finding (B.3 plateau), not an a-priori prediction. The pivot
burns team-02's single allowed pivot. Baseline config imported from exp-006 evidence:
L=252, M=126, centered pct-rank, reversed sign, EWM halflife 21.

Pre-registered REMAINING design space (nothing else will be tested post-approval):
- halflife h ∈ {21, 42, 63} (exp-004/006 showed monotone improvement up to the tested edge)
- anchor window L ∈ {252, 378, 504} at the chosen h
- transform: rank vs tercile(1/3) at the chosen (L, h)
- skip window: PH computed on close lagged {0, 21} days (recent-crash contamination check)
- history floor M ∈ {63, 126, 252} sensitivity
Budget: ≤ 6 further material experiments. Selection rule: unchanged from A.4.
Falsifier for the pivoted family: if the chosen config's one-step neighbors do not all
hold Sharpe @1× ≥ 0.30 and @2× > 0.25 with breadth ≥ 5/side, report negative and DNF
(no second pivot exists).

*(Pivot APPROVED in registry.jsonl — `t02-anchor-discount-contrarian-v1`; PART C
ladder executed as exp-007…exp-012; final spec follows in PART D.)*

---

## PART D — FINAL SPECIFICATION FOR THE QE (frozen; no research choices remain)

Family: `t02-anchor-discount-contrarian-v1`. The QE implements EXACTLY this in
`strategy.py :: build_raw_weights(pn, aux)` and makes no research decisions.

### D.1 Inputs used (and explicitly NOT used)

- USED: `pn['close']`, `pn['high']` (dates × tickers, ragged starts, never ffilled).
- NOT USED: `pn['open']`, `pn['low']`, `pn['volume']`, `aux['vix']`,
  `aux['sector_map']`, `aux['seed']` (strategy is deterministic pure pandas — no RNG;
  the unused-seed fact must be stated in a code comment for the Critic).
- Ticker set: taken from the panel columns at runtime. Never hard-coded.

### D.2 Signal pipeline (exact order; all ops per this spec, pandas defaults unless stated)

Let `close`, `high` be the input panels. Parameters: L=252, M=126, SKIP=21, H=42.

1. Anchor:      `anchor = high.rolling(window=252, min_periods=126).max()`
                (rolling max ignores NaN bars; needs ≥126 non-NaN highs in the window)
2. Proximity:   `ph0 = (close / anchor).where(close.notna())`
3. Skip:        `ph = ph0.shift(21).where(close.notna())`
                (21 PANEL ROWS = 21 US trading days; month-old anchor distance, but
                never a signal for a name without a current bar)
4. Rank:        `r = ph.rank(axis=1, pct=True)`   (ties: pandas default 'average';
                NaN PH → NaN rank)
5. Center:      `c = r.sub(r.mean(axis=1), axis=0)`   (exact dollar-neutral raw rows)
6. REVERSED SIGN: `s = -1.0 * c`   (long deep-discount, short near-anchor — the
                pivoted family's defining direction)
7. Smooth:      `s = s.ewm(halflife=42, adjust=True, ignore_na=False, min_periods=1).mean()`
                (per-name over time, on the panel as-is)
8. Final mask:  `raw = s.where(ph.notna())`   (flat whenever step-3 PH is NaN)
9. Return `raw` (DataFrame, same index/columns as `pn['close']`). NaN = flat.

The ENGINE owns everything downstream (gross=1 normalisation, |w_i|≤0.10, |net|≤0.25,
`.shift(1)` decision lag, 6 bps/side on |Δw|, 15% vol-target): emit raw rows only,
do NOT normalise, cap, lag, or scale.

### D.3 Missing-data / ragged-start rules (complete)

- A name with < 126 non-NaN highs in the trailing 252 rows → anchor NaN → flat.
- A name with no bar at t (close NaN) → flat at t (enforced at steps 2, 3 and 8 —
  the EWM never bridges a missing current bar into a live position).
- No forward-filling anywhere; no minimum-breadth logic in the strategy (the book
  runs 22/26 median names/side, comfortably above the floor).
- First ~6 months of 2010 are structurally flat (anchor warm-up); the evaluator
  scores them as zero-return days. Expected and accepted.

### D.4 Chosen parameters + plateau evidence (evaluator output, exp-007…exp-012)

Chosen: **L=252, M=126, rank transform, SKIP=21, H=42, sign=−1.**

| Config | Sharpe @1× | Sharpe @2× | maxDD | turn ×/yr | vs chosen @1× |
|---|---|---|---|---|---|
| **CHOSEN** | **0.4921** | **0.4695** | **−0.391** | **3.07** | 100% |
| L=189 | 0.4243 | 0.4004 | −0.387 | 3.39 | 86% |
| L=315 | 0.4878 | 0.4662 | −0.402 | 2.87 | 99% |
| H=21 | 0.4507 | 0.4180 | −0.360 | 4.40 | 92% |
| H=63 | 0.4926 | 0.4745 | −0.418 | 2.49 | 100% |
| SKIP=0 | 0.4701 | 0.4482 | −0.400 | 3.09 | 96% |
| M=63 | 0.3762 | 0.3520 | −0.409 | 3.17 | 76% |
| M=252 | 0.3888 | 0.3656 | −0.432 | 3.09 | 79% |

Pivot falsifier: NOT tripped — every neighbor ≥ 0.30 @1× and > 0.25 @2×, breadth
22/26 everywhere.

Documented selection tensions (A.4 applied honestly):
- H axis: H=63 scores +0.0005 @1× (noise) with lower turnover, but it is the UNTESTED
  EDGE of the pre-registered range, its bear bucket breaches −0.5 (−0.538) and chop
  goes negative (−0.044). exp-007's ledger line pre-committed to the plateau midpoint
  under exactly this pattern (flattening gain + bear degradation). H=42 is the
  interior point with a two-sided verified plateau and an all-weather profile.
- M axis: least flat (neighbors 76% / 79%, below the 80% plateau preference though
  above the falsifier bands). M=126 was the incumbent default carried from the
  exp-006 baseline — NOT chosen by the sweep; both alternatives are worse and the
  axis gates only ragged-start entry timing, not signal shape.

### D.5 Expected IS metrics (evaluator `run_is`; QE must reproduce via `cli.py team-run`)

@1×: Sharpe 0.4921, maxDD −0.3909, ann_turnover 3.07, total_return 1.927,
n_months 174, regime {bull +0.679, bear −0.358, chop +0.037},
median names long/short 22/26, mean_gross 1.0, mean_net 0.0069.
@2×: Sharpe 0.4695.
Tolerance: `team-run` must match these to float noise (same evaluator, same panels);
any visible drift means an implementation divergence from D.2 — stop and reconcile
against `scratch_explore.py` (`build_raw`, grid `exp-012[0]`) before freezing.

### D.6 Team-owned test expectations (QE writes `test_strategy.py`)

Minimum: (a) future-bar corruption self-check (corrupt bars after a cut date; weights
before the cut must be bit-identical); (b) determinism (two calls → identical frame);
(c) NaN-close day forces zero/NaN weight for that name (no EWM bridging);
(d) output index/columns == `pn['close']` index/columns; (e) unused-aux honesty
(runs with `aux['vix']=None`).
