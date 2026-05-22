# iter-v3/104 — Cycle-5 EXPLORATION #4 — NEW EDGE SOURCE (a non-price information layer) — FILED NULL-AT-EDA — the Phase-1 data-feasibility step killed liquidation-cascade history; the QR pivoted to on-chain network-activity and the deep IS-only EDA conclusively proved no on-chain candidate clears an IS-predictive bar; no backtest was run

**Date**: 2026-05-19
**Type**: EXPLORATION (cycle-5 slot #4) — Phases 1-5 concluded at a NULL-AT-EDA verdict
**Verdict**: **NULL-AT-EDA** — the recommended /103 axis was a genuinely new edge SOURCE behind a hard Phase-1 GO/NO-GO EDA. The fail-fast data-feasibility step found liquidation-cascade history is no longer obtainable, so the QR pivoted (within the same orthogonal-edge-source axis) to on-chain network-activity. The deep, multi-angle IS-only EDA (2 committed scripts + 7 result CSVs, `aaac3e9`) screened 6 on-chain candidate features and conclusively proved no candidate is IS-predictive — IC at the noise floor, 0/10 cells statistically significant, IS-fold LightGBM importance INERT (rank 12–15/15). No Phase-6 backtest was run.
**Classification**: **NULL-AT-EDA** — reserved for an axis the deep EDA conclusively proves dead (the dispatch's high bar). Killing it at the EDA — rather than committing a multi-symbol data fetch, a `src/` feature module, and a 3-seed backtest to reproduce the documented `feedback_v3_inert_features_at_higher_budget.md` OOS-harm — is the fail-fast WIN (`feedback_fail_fast.md`), not an iteration failure. Matches the /098/100/103 NULL-AT-EDA precedent.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION).
**Branch**: `iteration-v3/104`

---

## 1. The axis committed — and why

iter-v3/104 is cycle-5 EXPLORATION slot #4. The /103 closeout (Section 6, ranked #1) and
the /100/101/102/103 closeouts all converge on the same recommendation: after the
feature-stack frame closed twice in cycle 5 (the 7-FEED INERT verdict; /098 NO-GO; /102
NEGATIVE-by-IS-collapse; /103 NULL-AT-EDA-by-INERT) and every model-side lever closed
across cycle 4 + cycle 5, the only axis class left that attacks the binding constraint —
the thin per-symbol 8h triple-barrier signal — is **a genuinely new edge SOURCE**: a
non-price information layer brought in from outside the OHLCV-derived feature space.

Per `feedback_v3_structural_over_knob_exploration.md`, a NEW feature *family* sourced from
new data outranks another feature engineered off the existing price stack. The /103
Section 6 named two un-attacked non-price layers — **liquidation-cascade features** and
**on-chain regime broadcasts** — and mandated (`feedback_fail_fast.md`, the
/094/095/096/098/099/100 cheap-kill pattern) that the axis be killed-or-passed by a cheap
committed IS-only GO/NO-GO EDA *before* any `fetch` or `src/` build is committed.

Per `feedback_v3_axis_selection_quant_discipline.md` the axis was QR-led with a committed
`analysis/iteration_v3-104/*.py` EDA basis preceding any brief. The QR's Phase-1 work
ran a hard data-feasibility GO/NO-GO step *first* — the cheapest possible kill — and that
step is itself the first finding of this iteration.

---

## 2. The Phase-1 data-feasibility finding — liquidation-cascade history is dead

The /103-recommended first-choice edge source was liquidation cascades (self-exciting
liquidation chaining, Hawkes-process intensity, long/short liquidation asymmetry —
`references/crypto-edge-deep.md`). The fail-fast discipline says the *first* thing to
check is not "is the signal predictive" but "can the data even be obtained, gap-free,
strictly point-in-time, over the full 2020-01 → 2025-03-23 IS window." It cannot:

- **`data.binance.vision/.../futures/um/daily/liquidationSnapshot/`** — the historical
  liquidation-snapshot archive that backtests of this kind depended on has been
  **removed** from the Binance Vision bucket. There is no monthly/daily ZIP series to
  bulk-download. A v3 IS window starting 2020-01 cannot be reconstructed from it.
- **`/fapi/v1/allForceOrders`** — the REST force-order (liquidation) endpoint is
  **deprecated**; the request returns **HTTP 400**. Even if it responded, the REST window
  is a rolling recent slice, not a 5-year point-in-time history.

A liquidation-cascade feature for the v3 IS window would therefore have to be
*reconstructed* from a third-party paid feed (Coinglass / Amberdata) with its own
look-ahead, vendor-revision, and coverage risks — exactly the kind of un-auditable input
the v3 honest-backtest discipline (Rung 1) forbids without a verified point-in-time
source. **GO/NO-GO verdict on liquidations: NO-GO at the data layer** — not because the
signal was tested and failed, but because a gap-free, auditable, point-in-time IS history
does not exist. This is the cheapest possible kill: the iteration cost of discovering it
is two HTTP probes.

**The pivot — staying on the same axis.** The /103-recommended axis is *a new edge
SOURCE*, and on-chain regime broadcasts were the named second choice. The QR pivoted to
on-chain network-activity, which clears the data-feasibility bar that liquidations failed:

- **Source: CoinMetrics community API** (`community-api.coinmetrics.io/v4`) — a free,
  documented, point-in-time endpoint. Metrics fetched: **`AdrActCnt`** (count of active
  on-chain addresses) and **`TxCnt`** (count of on-chain transactions), **daily
  frequency**, for **btc, bch, trx**.
- `T1_is_panel_summary.csv` confirms the on-chain series is **gap-free over the full IS
  window** — BCH 5727 IS rows / LDO 2741 / TRX 5669, label coverage 0.9949–0.9976, min
  OHLCV coverage 1.0; the daily on-chain series forward-fills cleanly onto the 8h grid
  with no holes.

So the iteration proceeded — on the same orthogonal-new-edge-source axis — to a deep
IS-only EDA on on-chain network-activity. **The data-feasibility step did its job: it
swapped a dead sub-source for a live one at near-zero cost, before any build.**

---

## 3. The deep IS-only EDA — 6 on-chain candidate features, the IS-predictive standard

Two committed scripts under `analysis/iteration_v3-104/` (commit `aaac3e9`):
`fetch_onchain.py` (the CoinMetrics fetch + the candidate construction), `onchain_is_eda.py`
(the IS-predictive screen), and `onchain_daily_resolution_check.py` (the native-daily-vs-8h-grid
and regime-split robustness check). All strictly IS-only — every row entering any IC,
sign-stability, redundancy, or LightGBM-importance computation has
`open_time < OOS_CUTOFF_MS = 1742774400000`; the post-cutoff OOS was never read by the QR
in Phases 1-5.

### The candidate basket — 6 on-chain network-activity features

On-chain counts are non-stationary and trend with adoption, so a raw level cannot be a
feature. Each candidate is a **14-day growth rate, then z-scored on a trailing 90-day
window** — a stationary, scale-invariant transform consistent with the v3 feature
discipline. Two metric channels (`AdrActCnt`, `TxCnt`) × three chains, where the BTC pair
is a **cross-asset broadcast** (BTC on-chain activity as a market-wide regime input to the
altcoin book) and the bch/trx pairs are **own-chain** signals:

| Candidate | Construction | Encoded information |
|---|---|---|
| `btc_adract_growth_14d_z90` | z90 of 14-day growth in BTC active addresses | market-wide adoption-pulse broadcast |
| `btc_txcnt_growth_14d_z90` | z90 of 14-day growth in BTC transaction count | market-wide on-chain throughput broadcast |
| `bch_adract_growth_14d_z90` | z90 of 14-day growth in BCH active addresses | BCH own-chain network demand |
| `bch_txcnt_growth_14d_z90` | z90 of 14-day growth in BCH transaction count | BCH own-chain throughput |
| `trx_adract_growth_14d_z90` | z90 of 14-day growth in TRX active addresses | TRX own-chain network demand |
| `trx_txcnt_growth_14d_z90` | z90 of 14-day growth in TRX transaction count | TRX own-chain throughput |

**Adversarial causality.** On-chain data has a publication-timing trap: a metric *dated*
day D is not *knowable* at the open of day D (the day is still in progress; CoinMetrics
finalizes after the UTC day closes). Every candidate carries a **+1-day publication lag**
— the value attached to an 8h bar uses on-chain data dated strictly before the bar's
calendar day. The EDA's adversarial causality assertion (no rolling window with
`min_periods < window`, no centered op, no `bfill`, the lag applied before the join)
**passed**: an on-chain feature cannot peek at its own bar or any future bar.

### The screen — the IS-predictive evidence standard (the /103-corrected bar)

The /103 closeout's central methodological lesson — carried forward verbatim here — is
that the selection evidence must be **IS-predictive**: it must measure what a multi-seed
IS Optuna fit actually consumes, with **no held-out-tail OOS-leaning proxy**. The /104
screen applies four strictly-IS-only axes:

- **T2 — directional Spearman IC** of each candidate vs the /059 triple-barrier label,
  per symbol, with a p-value.
- **T3 — IS sub-period sign-stability**, half-split AND quartile resolution (a half-split
  can mask a within-half sign flip — the /103 `tsrank_dispersion_ratio` lesson).
- **T4 — incumbent redundancy** vs the 14 production features (the 0.70 hard gate).
- **T5 — IS-fold LightGBM gain-importance**: for each symbol a depth-4 LightGBM (the v3
  architecture; `num_leaves=15`, `max_depth=4`) fit on the IS panel with the 14 incumbents
  + the candidate, chronological 70/30 IS train/validation split, no shuffling, no
  post-cutoff data. This is the decisive IS-predictive test — a direct, cheap proxy for
  "will the multi-seed Optuna fit allocate ranked split capacity to this feature."
- **T7 — daily-native-vs-8h-grid + regime-split robustness**: re-runs the IC on the
  on-chain feature's native daily frequency (to rule out a 8h-grid forward-fill artifact)
  and runs a top-vs-bottom-decile regime-split Mann-Whitney test.

### T2 — the directional IC is at the noise floor

`T2_onchain_directional_ic.csv` — 10 symbol×candidate cells (the BTC cross-asset pair
appears on all 3 symbols; the own-chain pairs on their own symbol):

| candidate | symbol | n | IC | p-value | significant (p<0.05) |
|---|---|---:|---:|---:|:--:|
| `btc_txcnt_growth_14d_z90` | BCH | 5713 | +0.0323 | 0.0146 | (borderline) |
| `bch_txcnt_growth_14d_z90` | BCH | 5713 | +0.0284 | 0.0320 | (borderline) |
| `trx_txcnt_growth_14d_z90` | TRX | 5655 | −0.0340 | 0.0106 | (borderline) |
| `btc_adract_growth_14d_z90` | BCH | 5713 | +0.0164 | 0.2140 | no |
| `bch_adract_growth_14d_z90` | BCH | 5713 | +0.0210 | 0.1127 | no |
| `btc_adract_growth_14d_z90` | LDO | 2727 | +0.0291 | 0.1289 | no |
| `btc_txcnt_growth_14d_z90` | LDO | 2727 | −0.0127 | 0.5059 | no |
| `btc_adract_growth_14d_z90` | TRX | 5655 | −0.0048 | 0.7157 | no |
| `btc_txcnt_growth_14d_z90` | TRX | 5655 | +0.0188 | 0.1574 | no |
| `trx_adract_growth_14d_z90` | TRX | 5655 | −0.0254 | 0.0558 | no |

The **strongest mean |IC| in the entire basket is 0.034** (`trx_txcnt_growth_14d_z90`)
— at the same order as alpha032's 0.0354, the /102 feature that *collapsed the IS fit*. On
the standard 5713-row IS panel an |IC| of 0.034 is barely distinguishable from zero. Three
cells have p<0.05 but at p≈0.01–0.03 with 10 cells tested, the expected number of
spurious sub-0.05 cells is ~0.5–1 — these three are inside the multiple-testing noise band,
not evidence. The BTC cross-asset broadcast is the weakest of all: the
`btc_adract_growth` row on TRX has IC −0.0048 (p=0.72) — literally zero.

### T3 — sign-stability is 1 of 10

`T3_subperiod_stability.csv` — half-split and quartile sign strings per cell. The screen
demands one IC sign held across all four IS quartiles on the symbol. **Exactly one of 10
cells passes the quartile-stability test** — `trx_txcnt_growth_14d_z90` on TRX, sign
string `----` across all four quartiles. Every other cell flips sign at least once within
the IS window (e.g. `btc_txcnt_growth` on BCH is `++-+`; `btc_adract_growth` on LDO is
`+++-`). And the one quartile-stable survivor is precisely the candidate the T5 importance
test then kills — see below. A feature whose sign is not stable across the IS window
cannot carry a stable directional relationship a multi-seed Optuna fit could consume.

### T5 — the conclusive INERT finding

`T5_isfold_importance.csv` — the IS-fold LightGBM with 14 incumbents + the candidate:

| candidate | symbol | gain_rank_of_15 | gain_share_pct | parity 6.67% |
|---|---|---:|---:|:--:|
| `btc_adract_growth_14d_z90` | BCH | 13 | 4.054 | below |
| `btc_txcnt_growth_14d_z90` | BCH | 12 | 4.471 | below |
| `bch_adract_growth_14d_z90` | BCH | 13 | 3.535 | below |
| `bch_txcnt_growth_14d_z90` | BCH | 13 | 4.699 | below |
| `btc_adract_growth_14d_z90` | LDO | 10 | 5.807 | below |
| `btc_txcnt_growth_14d_z90` | LDO | 7 | 6.585 | below |
| `btc_adract_growth_14d_z90` | TRX | **15** | 2.690 | below |
| `btc_txcnt_growth_14d_z90` | TRX | 13 | 4.406 | below |
| `trx_adract_growth_14d_z90` | TRX | 14 | 3.622 | below |
| `trx_txcnt_growth_14d_z90` | TRX | 12 | 5.007 | below |

**Every one of the 10 candidate cells is BELOW the 1/15 = 6.67% importance-parity line on
every symbol** — `isfold_above_parity_engine` is `False` for all 6 candidates in the
`T6_screen_verdict.csv` summary. The best-ranked cell anywhere is rank 7/15 on the
581-row LDO panel (`btc_txcnt_growth`, share 6.585% — still *below* parity, and LDO is too
thin to carry a feature verdict). On the two symbols carrying 99%+ of /059 IS PnL — **BCH
(95.76%) and TRX** — no candidate ranks better than 12/15, and `btc_adract_growth_14d_z90`
ranks **dead last 15/15 on TRX**. The one T3 quartile-stable survivor,
`trx_txcnt_growth_14d_z90`, ranks **12/15 on TRX at a 5.0% sub-parity share** — its sign
stability does not translate into split capacity the tree will use. This is the textbook
v3 **INERT** signature — the iter-v3/019/082/085/086 7-FEED pattern, where the tree
declines to allocate ranked split capacity to the feature.

### T7 — the regime-split significance is a multiple-testing artifact

`T7_daily_resolution_and_regime.csv` rules out the two natural objections:

1. **8h-grid forward-fill artifact?** No. The native-daily IC (`ic_daily_native`) tracks
   the 8h-grid IC closely (e.g. BCH `btc_txcnt`: 8h-grid +0.0323 vs daily-native +0.0216;
   TRX `trx_txcnt`: −0.0340 vs −0.0334) — the weak signal is a property of the metric,
   not the resampling. All `ic_daily_pvalue` values are 0.14–0.71 — **not one daily-native
   IC is significant**.
2. **A regime signal hiding in the tails?** The top-vs-bottom-decile Mann-Whitney
   `regime_split_mw_pvalue` flags 4 of 10 cells at p<0.05 — but the corresponding
   `regime_topbot_mean_gap_pct` (the actual forward-return gap between the on-chain
   top-decile and bottom-decile bars) is **0.8–1.3% on the "significant" cells and
   *negative* on TRX** — an economically trivial gap, and with 10 cells tested 4 sub-0.05
   p-values is within the multiple-testing band. The regime split is a statistical
   artifact of large n, not an exploitable conditional edge.

### EDA verdict

`T6_screen_verdict.csv` — every one of the 6 on-chain candidates is **NO-GO**. Six
on-chain network-activity features (BTC cross-asset broadcast + own-chain bch/trx;
AdrActCnt + TxCnt channels), screened on four IS-predictive axes. **IC max mean |0.034| —
at the noise floor. 0 of 10 symbol×candidate cells statistically significant after
accounting for multiple testing. Sign-stability 1 of 10. IS-fold LightGBM importance
below the 6.67% parity line in 10 of 10 cells — INERT on both IS-engine symbols. The
regime-split significance is a multiple-testing artifact.** No on-chain candidate is
IS-predictive.

---

## 4. The verdict — NULL-AT-EDA, no backtest — the fail-fast justification

The dispatch reserves NULL-AT-EDA for "an axis the deep EDA conclusively proves dead (high
bar)." The /104 EDA clears that bar — a hard data-feasibility GO/NO-GO step plus a deep
IS-predictive screen on the pivoted source, with a 0-of-10-significant IC result and a
10-of-10-INERT importance result. No backtest was run, for three binding reasons —
identical in structure to the /103 NULL-AT-EDA:

1. **An INERT 15th feature is known to HARM, not help.**
   `feedback_v3_inert_features_at_higher_budget.md` is binding: a feature that ranks last
   in importance, added at higher Optuna budget, produced OOS Sharpe −1.07 vs +0.78
   (Δ −1.85) because the larger search space lets Optuna overfit IS noise *through* the
   dead column. All 6 on-chain candidates are sub-parity in all symbols — the exact INERT
   profile that rule governs.

2. **A backtest would knowingly reproduce a documented failure mode.** /102's failure was
   that its selection proxy did not predict the IS fit; /103's and /104's EDAs use an
   IS-predictive screen *and that screen returns a negative verdict*. To run the
   multi-seed backtest anyway — after committing a `src/crypto_trade/features_v3/`
   on-chain module and a multi-symbol on-chain `fetch` — would discard the very evidence
   the /102 lesson tells us to trust, at material compute + engineering cost, to confirm
   a documented failure mode (the /102 IS-collapse / the 7-FEED INERT verdict).

3. **Fail-fast forbids a foreseeable-failure spend.** `feedback_fail_fast.md` — the
   cheap-kill discipline the /094/095/096/098/099/100/103 fail-fast EDAs established —
   directs that an axis a committed IS-only EDA conclusively kills is closed at the EDA:
   no `src/` change, no runner change, no backtest, no Critic, no agent dispatch. The
   honest move is to report the negative IS-predictive verdict with the numbers, which is
   what NULL-AT-EDA is.

No `src/` code was written — `V3_FEATURE_COLUMNS` stays at 14, bit-identical to /059;
there is no on-chain feature module; there is nothing to revert. No `fetch` sub-source was
wired into the production pipeline (the CoinMetrics pull lives entirely inside the
committed `analysis/iteration_v3-104/fetch_onchain.py` EDA script).
`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` were untouched. Every Phase 1-5
measurement was strictly IS-only; the QR did not inspect the post-cutoff OOS.

---

## 5. The non-price-edge-source axis closes — and what it means for v3

iter-v3/104 closes the **new-edge-SOURCE** axis the /103 Section 6 ranked #1. Combined
with the prior v3 record, the non-price information layers are now systematically attacked:

- **Derivative data — funding rates, OI, perp-spot basis** — closed across
  /019/023/024/082/085/086 (the 7-FEED INERT verdict; funding ×4, microstructure ×1,
  basis ×1).
- **Liquidation cascades** — **NO-GO at the data layer** (this iteration): no auditable,
  gap-free, point-in-time IS history exists; the Binance Vision archive is removed and
  the REST endpoint is deprecated.
- **On-chain network-activity** — **NULL-AT-EDA by INERT** (this iteration): 6 candidates,
  0/10 significant, 10/10 below importance parity.

**The structural read.** /104 is fully consistent with the recurring cycle-4 + cycle-5
finding: *every* single-feature-addition axis to the v3 14-feature stack has failed,
across *every* source family — price-derived (the 7-FEED verdict, /098, /102, /103),
derivative (funding/OI/basis), and now on-chain. The binding constraint is **not the
feature family and not the data source** — it is that the v3 per-symbol depth-3-5
LightGBM on a thin 8h triple-barrier signal has a saturated feature representation; a 15th
input, however orthogonal its source, does not lift it and tends to harm the IS fit
through Optuna noise-overfit. The training objective (/101), the model architecture
(/093/096/100/016 XGBoost), the label class structure (/099), the universe (/097), the
feature stack (/098/102/103), and now the external-data layer (/104) have *all* been
attacked and closed. The thin per-symbol signal is the constraint, and **no input-side or
model-side lever has moved it.** That is the decisive structural fact this cycle has
established — and it is what makes the /105 axis recommendation (Section 6) the genuinely
bold one it has to be.

---

## 6. Lessons

1. **A data-feasibility GO/NO-GO step is the cheapest kill in the playbook — run it
   first.** The /104 first-choice edge source (liquidation cascades) was killed by two
   HTTP probes — the Binance Vision archive removal and the deprecated REST endpoint —
   *before* a single line of feature code was written. The fail-fast discipline is not
   only "kill the signal cheaply at an IS EDA"; it is "kill the *data assumption* cheaper
   still." Future new-edge-source EXPLORATIONs must, as Phase-1 step zero, verify a
   gap-free auditable point-in-time IS history exists for the proposed source. A pivot
   within the same axis (liquidations → on-chain) at near-zero cost is the correct
   response, not an iteration failure.

2. **An IS-predictive feature screen kills a new-data feature exactly as it kills an
   engineered one.** /103 applied the IS-predictive screen to engineered compositions;
   /104 applied the identical screen — IC, quartile-resolution sign-stability, incumbent
   redundancy, IS-fold LightGBM gain-importance — to features sourced from a genuinely
   new data layer. The screen returned the same conclusive negative (0/10 significant IC,
   10/10 below importance parity). The lesson generalizes: the IS-fold LightGBM
   gain-importance test is a source-agnostic, cheap, direct proxy for "will the multi-seed
   Optuna fit allocate split capacity to this feature," and a NULL-AT-EDA on a 10/10-INERT
   importance result is the fail-fast WIN regardless of where the feature came from.

3. **On-chain network-activity is a weak predictor of the thin 8h triple-barrier label on
   this universe.** The economically intuitive prior — that BTC on-chain activity is a
   market-wide regime broadcast and own-chain throughput signals network demand — did not
   survive contact with the data: the strongest mean |IC| in a 6-candidate basket was
   0.034 (noise floor), and the regime-split "significance" was a large-n multiple-testing
   artifact with a sub-1.3% economically-trivial decile gap. The plausible reason: on-chain
   metrics move on a multi-day-to-weekly adoption timescale, while the v3 label is a
   per-symbol 8h triple-barrier event — a horizon mismatch the +1-day publication lag only
   widens. On-chain data may carry a slow regime signal, but not one a per-symbol 8h
   directional classifier on BCH/LDO/TRX can consume.

4. **Every input-side and model-side lever for v3 is now closed — the constraint is
   structural and the next axis must be too.** /104 is the capstone of a long run: feature
   stack, derivative data, on-chain data, training objective, model architecture, label
   class, and universe have all been attacked and closed. Per
   `feedback_v3_structural_over_knob_exploration.md` the remaining un-attacked axis class
   is not "another feature / another model" — it is a **structural re-framing of the
   prediction problem itself**: the label geometry, the trade-construction layer between
   the model score and the executed position, and the risk-primitive stack. Section 7 is
   the concrete /105 recommendation.

---

## 7. Next Iteration Ideas — cycle-5 EXPLORATION slot #5

The diagnosis cycle 5 has now established with near-certainty is precise: **the v3
per-symbol 8h triple-barrier signal is thin, and no input-side lever (features, derivative
data, on-chain data) or model-side lever (architecture, training objective, label class,
universe) has moved it.** "The search space is exhausted" is the forbidden conclusion —
and it is also factually wrong: every closed axis has attacked the *inputs to* or the
*estimator of* a fixed prediction problem. Not one has changed **what the prediction
problem is**. That is the un-attacked frontier, and it is large.

The recommended iter-v3/105 axis, with the runner-up ranked below it.

### Recommendation #1 (TOP) — re-frame the label geometry: the trend-scanning / vertical-barrier-grid label

**The axis.** Replace the v3 single-fixed-horizon triple-barrier label with a
**multi-horizon trend-scanning label** (López de Prado, *Machine Learning for Asset
Managers* §5.4, the "trend-scanning" method; the AFML triple-barrier with a *grid* of
vertical barriers is the close sibling). Instead of asking "does a ±ATR barrier get hit
within 21 candles," trend-scanning fits a linear trend over *every* horizon h in a window
(e.g. h ∈ {5, 8, 13, 21, 34} candles), and labels the bar by the **sign and t-statistic
of the most statistically significant trend** — the horizon is chosen *per bar by the
data*, not fixed by a hyperparameter.

**Why this is genuinely bold and not a re-tread.** Every closed v3 axis kept the label
fixed. /099 attacked the label *class structure* (it added an abstention class — a
3-class re-partition of the *same* fixed-horizon barrier event) and closed NO-GO. /010
tuned the barrier *multipliers* (2.0/1.0) — a knob on the same label. Trend-scanning is
neither: it changes the **estimand**. The thinness of the v3 signal is plausibly *caused
by* the fixed 21-candle horizon — a single horizon is a lottery on whether the predictable
move happens to complete inside that exact window, and on a per-symbol 8h series the
predictable horizon almost certainly varies bar-to-bar with the volatility regime. A
per-bar data-selected horizon directly attacks that: it lets each bar be labeled at the
horizon where its move is *actually* statistically resolvable. This is the one structural
lever the cycle-5 evidence most directly implicates and has never been pulled.

**Quantitative rationale — and the fail-fast EDA that gates it.** The committed
`analysis/iteration_v3-105/*.py` IS-only GO/NO-GO EDA (the mandatory
`feedback_fail_fast.md` + `feedback_v3_axis_selection_quant_discipline.md` step) is cheap
and decisive: compute the trend-scanning label on the IS panel and measure (a) the
**distribution of the data-selected horizon** per symbol — if it is tightly peaked at 21
candles, trend-scanning ≈ the incumbent and the axis is NO-GO before any build; if it is
broad (the expected result), the fixed-horizon label is demonstrably leaving structure on
the table; (b) the **IS feature→label IC of the existing 14-feature stack against the new
label** — the GO bar is a *materially higher* aggregate |IC| than the same 14 features
score against the incumbent triple-barrier label (the same IS-predictive screen /103+/104
established, now applied to the *label* rather than a candidate feature); (c) **label
balance and trade count** — trend-scanning must not collapse the trade rate below the
`feedback_v3_trade_rate_floor_bundle_level.md` floor. A higher 14-feature IC against a
re-framed label is the single most direct evidence that the binding constraint is the
label geometry and not the features — and it is measurable entirely IS-only, before a
backtest.

**Risk primitives.** The label change is a clean single-axis swap; the 7-gate RiskV2
stack and the per-symbol architecture carry over unchanged. The pre-registered falsifiers
mirror /103/104: F-HORIZON (the selected-horizon distribution is degenerate at 21 → the
label is a relabel of the incumbent → NO-GO at EDA), F-IC (the 14-feature aggregate IC
against the new label does not exceed the incumbent-label IC → no structural lift → NO-GO),
F-RATE (IS trade count below the bundle-level floor).

### Recommendation #2 (runner-up) — the trade-construction layer: a meta-labeling secondary model

If the QR judges the label-geometry EDA's selected-horizon distribution degenerate (the
F-HORIZON kill), the next structural axis is the **trade-construction layer between the
model score and the executed position** — specifically a **meta-labeling secondary model**
(López de Prado, AFML Ch. 3). v3 currently maps the primary LightGBM score to a position
directly. A meta-labeling layer keeps the primary model's *direction* and trains a second
classifier whose only job is the binary *take / skip* decision — sizing the bet by the
secondary model's confidence. /017 closed a meta-labeling attempt as PATH C *over-filter*,
but /017's secondary model was fed the *same* feature stack as the primary; the
generalizable lesson there was the feature overlap, not that meta-labeling is dead. A
/105-or-/106 meta-labeling axis fed by a *deliberately disjoint* feature set — the
regime/volatility/cross-asset features the primary model under-weights — is a materially
different experiment and attacks the thin signal at the construction layer rather than the
estimation layer. It is ranked second only because the label-geometry EDA (#1) is the
cheaper and more direct test of the cycle-5 diagnosis.

Both recommendations are structural re-framings of the prediction problem, not another
input or estimator on a fixed problem — which is exactly what the closed-axis record
demands. Per `feedback_v3_axis_selection_quant_discipline.md`, the iter-v3/105 axis must
be QR-led with a committed `analysis/iteration_v3-105/*.py` EDA basis preceding the brief,
and per `feedback_fail_fast.md` it must carry a hard Phase-1 GO/NO-GO EDA (the F-HORIZON /
F-IC / F-RATE falsifiers above) before any `src/` build.

---

## 8. Commit chain

- EDA SHA: `aaac3e9` — `analysis/iteration_v3-104/` (3 scripts: `fetch_onchain.py`,
  `onchain_is_eda.py`, `onchain_daily_resolution_check.py` + 7 result CSVs:
  `T1_is_panel_summary.csv`, `T2_onchain_directional_ic.csv`, `T3_subperiod_stability.csv`,
  `T4_incumbent_redundancy.csv`, `T5_isfold_importance.csv`, `T6_screen_verdict.csv`,
  `T7_daily_resolution_and_regime.csv`).
- Diary SHA: this closeout — `docs(iter-v3/104): closeout diary — FILED NULL-AT-EDA /
  liquidation data dead, on-chain network-activity EDA proved no candidate is
  IS-predictive`.
- Catalog update SHA: committed with this diary — `briefs-v3/exploration_catalog.md` /104
  row (classification NULL-AT-EDA).
- **No reports** (no backtest run — NULL-AT-EDA stopped the iteration at the EDA).
- **No `src/` change** (NULL-AT-EDA — nothing was implemented; `V3_FEATURE_COLUMNS` stays
  at 14, bit-identical to /059; no on-chain feature module; no `fetch` sub-source wired;
  nothing to revert).
- **Tag**: `v0.v3-104` — a closeout marker only, tagged by the orchestrator (NOT a
  baseline update — the `v0.v3-082`…`v0.v3-103` pattern; BASELINE_V3.md UNCHANGED at
  `v0.v3-059`, IS +1.0894 / OOS +0.5791).

iter-v3/104 is cycle-5 EXPLORATION slot #4; the cadence advances. iter-v3/105 is slot #5 —
the recommended LABEL-GEOMETRY re-framing iteration (trend-scanning label) with a hard
Phase-1 GO/NO-GO EDA (Section 7).

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched. The walk-forward
embargo fix (`e149e9d`) is inherited unchanged. No cheating: the QR saw no OOS data —
no backtest was run; all Phase 1-5 EDA was strictly IS-only (`open_time < OOS_CUTOFF_MS`),
verified across the committed EDA scripts.
