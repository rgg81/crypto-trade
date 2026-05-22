# iter-v3/095 — Phase-1 GO/NO-GO EDA closeout note — VERDICT: **NO-GO**

**Date**: 2026-05-18
**Axis**: crypto cointegration / relative-value statistical arbitrage — a
walk-forward cointegration pairs strategy (the user-chosen iter-v3/095
direction; cycle-4 prep-memo Candidate B).
**Outcome**: **NO-GO** at the Phase-1 fail-fast checkpoint. No 10-section
research brief written; no cointegration runner built; no backtest run. The
axis is killed for the cost of two committed IS-only EDA scripts.
**Classification**: **NULL-AT-EDA** — crypto cointegration on v3's actual IS
data does not clear the persistence / tradeability bar for a walk-forward pairs
strategy. Killing it cheaply at the EDA is the fail-fast WIN
(`feedback_fail_fast.md`), not an iteration failure.

---

## 1. What was tested and why this was a hard GO/NO-GO

Everything v3 has tried — per-symbol directional triple-barrier prediction
(/082-087), cross-sectional ranking (/088-092), derivatives-microstructure
regime overlays and order-flow alpha (/093-094) — extracts edge from
*forecasting direction*. Cointegration pairs trading is a genuinely different
STRATEGY CLASS: it extracts edge from the market-neutral *mean-reversion of a
stationary spread* between cointegrated symbols.

The known, documented risk is INSTABILITY — pairs cointegrated in one window
decohere in the next (the cycle-4 prep memo's Candidate-B caveat: "altcoin-universe
instability + turnover drag"; `briefs-v3/cycle4_prep_memo.md` line 145). Per
`feedback_fail_fast.md`, Phase 1 of /095 is an explicit GO/NO-GO that tests
exactly this BEFORE any expensive build.

**Universe**: the 22-symbol cross-sectional `XS_UNIVERSE` (`cross_sectional.py:61`)
— non-v1/v2 liquid Binance-USDT perps. The `V3_EXCLUDED_SYMBOLS` check passes by
construction (XS_UNIVERSE was built to exclude every v1/v2 symbol; the EDA
asserts the empty intersection at load). C(22,2) = 231 candidate pairs — genuine
breadth, vs the 3-pair BCH/LDO/TRX `V3_MODELS` set which is far too thin for
cointegration.

**Method**: two committed IS-only, walk-forward-faithful EDA scripts
(`feedback_v3_eda_walkforward_faithful.md`) — a 24-month formation window
(`training_months=24`), a 1-month trading window, stepping monthly; 39 windows
inside the IS span `open_time < OOS_CUTOFF_MS = 2025-03-24`. Cointegration
(Engle-Granger) tested on the formation window only; tradeability measured on
the SUBSEQUENT out-of-formation 1-month window. `cointegration_go_nogo_eda.py`
(prevalence/persistence/half-life/pair-window tradeability) and
`cointegration_stress_test.py` (the faithful walk-forward BOOK + the decisive
out-of-formation spread-ADF diagnostic).

---

## 2. The decisive numbers — three independent FAIL gates

### 2.1 Out-of-formation cointegration SURVIVAL — the binding failure

For every pair selected as cointegrated in the 24-month formation window
(Engle-Granger p<0.05, tradeable formation half-life), the stress test
ADF-tests the spread on the *next* 1-month trading window using the FORMATION
hedge ratio:

| Metric | Value |
|---|---|
| Out-of-formation spread ADF — **median p-value** | **0.4524** |
| Fraction of selected pairs still cointegrated out-of-formation (ADF p<0.10) | **0.1477** |

**Only ~15% of in-formation-cointegrated spreads are still cointegrated the
very next month.** The formation-window cointegration does NOT survive into the
window where it would actually be traded. This is the cycle-4 prep-memo
Candidate-B caveat, quantified: crypto altcoin cointegration decoheres faster
than a monthly walk-forward can re-select. A pairs strategy that selects on
in-formation cointegration is, ~85% of the time, trading a spread that is no
longer mean-reverting.

### 2.2 The faithful walk-forward BOOK does not clear cost

The stress test runs the actual strategy a v3 cointegration runner would deploy
— per-window pick the TOP-10 pairs by formation Engle-Granger p-value (filtered
to a tradeable 2-60-bar formation half-life), trade the spread z-score
market-neutral on the subsequent month, charge 0.20% per round-trip (4 leg-fills
× 0.05% Binance-futures taker), aggregate into ONE monthly book PnL series.
Two GENEROUSLY-chosen entry thresholds:

| Book variant | Trades/month | NET monthly Sharpe | GROSS monthly Sharpe | Frac months NET+ |
|---|---:|---:|---:|---:|
| STRICT (z-entry 2.0) | 2.5 | **-0.0770** | -0.0681 | 0.4103 |
| LOOSE (z-entry 1.5) | 3.7 | **-0.0236** | -0.0127 | 0.5128 |

The book is **NET-negative in both variants and GROSS-negative too** — the
problem is not merely the two-leg turnover cost; the spreads do not mean-revert
profitably out-of-formation at all (consistent with §2.1). v3's /059 baseline is
OOS monthly Sharpe +0.58 and the merge floor is +1.0; a new strategy class that
cannot clear an IS NET monthly Sharpe of even +0.30 — generously parameterized,
IS-only, before any OOS haircut — has no realistic path to the merge bar, and a
NEGATIVE OOS is foreseeable.

### 2.3 Trade-rate floor failed by a wide margin

The project hard gate is ≥10 trades/month OOS (≥130 total;
`feedback_trade_rate_floor.md`). The faithful book fires **2.5-3.7 trades/month**
— spreads with a median half-life of ~60 bars (20 days) get only ~1.5
mean-reversion cycles inside a 90-bar monthly window, so 2/3 of selected
pair-windows never complete a round-trip. Even the LOOSE z-entry=1.5 variant is
3.7×/month, ~3× below the floor.

---

## 3. Why the first-pass EDA's "70% persistence" was an artifact

`cointegration_go_nogo_eda.py` initially returned a fragile GO: mean persistence
rate 0.7045, "lift over random" +0.5724. The stress test exposes this as an
**in-sample-overlap artifact**:

- Persistence was measured as `|coint(N) ∩ coint(N+1)| / |coint(N)|` using the
  Engle-Granger p-value on the *formation* windows.
- Adjacent 24-month formation windows share **23 of 24 months — ~96% identical
  data**. A statistic computed on 96%-overlapping samples is mechanically
  autocorrelated; the Engle-Granger p-value "persisting" across two near-identical
  windows is expected and is **NOT evidence the spread is tradeable next month.**
- The honest test is the out-of-formation spread ADF (§2.1) — measured on the
  genuinely non-overlapping trading window. It returns **14.77% survival**, not
  70%. The cointegration relation does not survive into the trading window.

This is a recorded methodology lesson: cointegration "persistence" measured on
overlapping formation windows is an in-sample-overlap artifact; the load-bearing
metric is out-of-formation spread stationarity.

Prevalence itself (T1) was also wildly non-stationary — 0.013 to 0.41 across the
39 windows — a second instability flag.

---

## 4. Pre-registered GO/NO-GO criteria and the verdict

The stress test pre-registered three GO gates (ALL required):

| Gate | Threshold | Observed (best variant) | Result |
|---|---|---|---|
| (Sharpe) best faithful book NET monthly Sharpe | ≥ +0.30 | -0.0236 | **FAIL** |
| (Trade rate) round-trips per month | ≥ 10 | 3.7 | **FAIL** |
| (OOF survival) frac selected pairs still cointegrated out-of-formation | ≥ 0.50 | 0.1477 | **FAIL** |

**All three FAIL. VERDICT: NO-GO.** This is not a borderline call — the book is
net-negative AND gross-negative, the trade rate is ~3× below floor, and the
cointegration relation survives into the trading window only ~15% of the time.

---

## 5. NO-GO closeout — fail-fast applied as designed

Per `feedback_fail_fast.md`: the failure of a crypto-cointegration walk-forward
pairs strategy was foreseeable from the documented altcoin-instability caveat,
and the Phase-1 EDA confirmed it for the cost of **two committed IS-only EDA
scripts — no `fetch`, no new runner, no backtest, no Critic, no agent
dispatch.** This is the fail-fast WIN: a non-viable axis killed cheaply so
compute flows to a genuine high-EV test.

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched; every
measurement is strictly IS-only (`open_time < OOS_CUTOFF_MS`); OOS was never
touched and is first seen in Phase 7 of a future iteration.

---

## 6. Next-axis recommendation

The cycle-4 derivatives-microstructure line is closed in both roles (/093 regime
overlay BLOCKED + low-ceiling; /094 order-flow alpha NO-GO). Cointegration
stat-arb (/095) is now also NO-GO. The honest structural pattern across
/082-095: crypto-native non-OHLCV feeds and now a market-neutral spread strategy
have not delivered a transferable, cost-viable edge on v3's data.

**Recommended iter-v3/096 axis — a genuine NEW MODEL-ARCHITECTURE axis: a
non-tree sequence learner (a shallow temporal MLP, or a small attention-pooled
sequence model) on the existing validated 14-feature price-derived stack
(`V3_FEATURE_COLUMNS_TOP_N`), per-symbol BCH/LDO/TRX, predicting the /059
triple-barrier label.** Rationale, per `feedback_v3_axis_selection_quant_discipline.md`
(the iter-v3/096 QR must still produce a committed EDA-driven quantitative basis
before the brief):

- It attacks the actual recurring structural limitation v3 has never addressed:
  the depth-3-5 LightGBM cannot compose feature interactions across time — every
  v3 architecture has been a tree on a flat feature vector. The /094 closeout
  explicitly names this as the un-tried axis.
- It needs ZERO new data and ZERO new feature family — it runs on the existing
  on-disk OHLCV-derived 14-feature stack, so the fail-fast cheap-precondition
  (does the data exist) is already cleared.
- It is a true re-architecture, not a knob/feed variant — distinct from the
  /082/086 crypto-native-feed dead ends and the /015/016 model-arch axis (which
  closed only LightGBM↔XGBoost head-to-head at n_trials=10, NOT non-tree
  learners).

Fallback if the iter-v3/096 model-architecture EDA also comes back at the
price-myopic ceiling: regime-switching TSMOM (cycle-4 prep-memo Candidate C) —
recorded but lowest-ambition.

---

## 7. Committed artifacts

- `analysis/iteration_v3-095/cointegration_go_nogo_eda.py` — prevalence /
  persistence / half-life / pair-window tradeability EDA (IS-only,
  walk-forward-faithful).
- `analysis/iteration_v3-095/cointegration_stress_test.py` — the decisive
  faithful walk-forward BOOK + out-of-formation spread-ADF diagnostic.
- `analysis/iteration_v3-095/T1_coint_prevalence.csv` — cointegration prevalence
  per formation window (non-stationary: 0.013-0.41).
- `analysis/iteration_v3-095/T2_persistence.csv` — formation-window persistence
  (the in-sample-overlap artifact; mean 0.70 — NOT a valid tradeability signal).
- `analysis/iteration_v3-095/T3_halflife.csv` — spread half-life distribution
  (median ~60 bars / 20 days — too slow for a 1-month book).
- `analysis/iteration_v3-095/T4_tradeability.csv` — pair-window-level
  out-of-formation tradeability (thin: 231 trades / 38 months).
- `analysis/iteration_v3-095/NO_GO_NOTE.md` — this note.
