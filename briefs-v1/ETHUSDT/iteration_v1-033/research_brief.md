# iter-v1/033 (ETHUSDT) — Research Brief: TREND × REVERSION regime-complementary ENSEMBLE — IS-only feasibility → **NEGATIVE** (contingency RESOLVED AGAINST building)

**Type:** IS-only feasibility + architecture-design screen (NO backtest run by this iteration; NO `src/` edits).
**Axis family:** model-arch (signal-combination / regime-router ensemble).
**Verdict: NEGATIVE.** The TREND × REVERSION ensemble premise is FALSIFIED at the IS-proxy level under
production-faithful wiring, AND independently confirmed-falsified by iter-032's just-completed backtest
(IS −0.6131 / OOS −0.8699). The reversion leg has **no real edge to contribute**; combining it with the
trend edge reproduces the iter-031-B crowding/dilution failure. **Do NOT build iter-033.**

---

## Section 0 — Hypothesis (pre-registered)
Two STRONG, de-correlated deterministic edges — TREND (iter-027, SMA200 trend-state + conviction, 14d hold)
and REVERSION (iter-032 IS PASS cell, SMA10 z-fade + high-vol gate, 16h hold) — fire and win in DIFFERENT
crypto regimes (trends persist via funding/momentum reflexivity; mean-reversion snaps back in high-vol
liquidation exhaustion). A deterministic regime-ROUTER making only one edge eligible per candle (no overlap,
no crowding) should ADD independent reversion events to the regimes where the trend edge stands aside →
breadth (more independent winning events) + de-concentration WITHOUT diluting IS Sharpe (avoiding the
iter-031-B failure where weak added signals crowded out the trend's high-conviction entries).

## Section 0.5 — The single load-bearing finding that kills the hypothesis
**The reversion edge does not exist under production wiring.** iter-032's IS screen reported the PASS cell
`pricez|natr>=q40|k1.5|N2` at per-trade Sharpe **+0.426** — but that screen computed the z-score with
`rolling(10).std(ddof=0)`. The PRODUCTION code (`lgbm.py::_reversion_price_z`, docstring confirmed at lines
369 / 2742 / 2752) uses **`ddof=1`**. Re-running the IDENTICAL cell with the production-faithful `ddof=1`:

| std basis | events | IS per-trade Sharpe | net% | source |
|---|---|---|---|---|
| ddof=0 (iter-032 screen) | 485 | **+0.426** | +84.4 | proxy MISMATCH with backtest |
| **ddof=1 (production wiring)** | 432 | **+0.269** | +51.9 | what the backtest actually runs |
| ddof=1, non-overlap re-entry + horizon-cross-drop (this screen) | 452 | **−0.039** | −7.8 | feasibility-faithful |

And the production-faithful ddof=1 reversion is **negative/breakeven in 4 of 5 IS years**, carried entirely
by a single 23-event year:

| year | events | net% | mean/trade |
|---|---|---|---|
| 2020 | 102 | −1.8 | −0.018% |
| 2021 | 135 | +3.6 | +0.026% (≈ breakeven) |
| 2022 | 109 | **−14.4** | −0.133% |
| **2023** | **23** | **+18.7** | +0.814% (the ONLY positive year) |
| 2024 (OOS-adjacent) | 59 | **−34.1** | −0.579% |

**iter-032's +0.426 was a ddof=0 proxy artifact inflating a regime-fragile, mostly-negative signal.** This is
the AGREE_SCALE lesson (iter-030: IS proxy PASSED, backtest INVERTED) recurring — and I pre-registered it as
the contingency.

## Section 0.6 — CONTINGENCY RESOLVED: iter-032's backtest (completed mid-screen) confirms the NEGATIVE
The brief was pre-registered as contingent on iter-032's backtest confirming the reversion edge transfers
from IS proxy to backtest. **It does NOT.** iter-032 completed at 07:37 (`reports-v1/ETHUSDT/iteration_v1-032/comparison.csv`):

| metric | IS | OOS |
|---|---|---|
| monthly Sharpe | **−0.6131** | **−0.8699** |
| profit factor | 0.6913 | 0.6340 |
| total net PnL | −15.29 | −3.69 |
| total trades | 104 | 39 |

The reversion edge collapsed from an apparent +0.426 IS proxy to **−0.61 IS in the real backtest** (ddof=1 +
LightGBM per-month confidence gate + R2/R3/R5 risk layers). My production-faithful IS screen (−0.039, 4-of-5
years negative) correctly anticipated direction; the backtest is even worse. The reversion leg is not a weak
edge — under production wiring **it is a losing book**. There is nothing net-additive to route to.

---

## Section 1 — Regime-complementarity: the de-correlation premise HOLDS, the both-profitable premise FAILS
(`analysis/ETHUSDT/iteration_v1-033/ensemble_screen.py` [2]–[3], cutoff-asserted, leak-guarded, horizon-cross-dropped)

- **Event-timing de-correlation HOLDS** (the iter-031-B parallel): candle-level Jaccard(trend-open, rev-open)
  = **0.0393** (21 of 535 union) — the two triggers fire on different candles, exactly like iter-031-B's
  Donchian/TSMOM (0.02–0.03). The de-correlation premise is true.
- **Regime SEPARATION is WEAK, not clean.** Median ADX14 at trend events = 24.1 vs reversion events = 26.6
  (nearly identical); median convATR 5.01 vs 4.66; median natr 3.25 vs 3.82. The reversion book sits in
  *slightly* higher vol but NOT in a distinct "high-vol chop" regime — its ADX-tertile occupancy is 29% low /
  39% high, i.e. it fires MORE in high-ADX (trending) candles than in low-ADX chop. The crypto-native story
  ("reversion lives in high-vol liquidation exhaustion") is not cleanly separable from the trend regime on ETH
  8h. (`hurst_100` was UNUSABLE as a regime proxy — median 1.02, range 0.77–1.11, not a standard [0,1] Hurst.)
- **Both-profitable FAILS** (the decisive break vs the hypothesis): trend standalone +0.402, reversion
  standalone **−0.039** (production-faithful). One strong edge + one breakeven-to-negative edge ≠ two strong
  de-correlated edges. The premise that we have "TWO STRONG edges" is false under production wiring.
- **The single-position crowding surface is enormous:** 366 of 452 reversion opens (81.0%) fall INSIDE a 14d
  trend hold. On a single-position book a concurrent two-sleeve design is impossible; routing is mandatory.

## Section 2 — Combination architecture: REGIME-ROUTER (i) is the only parity-clean option, but it cannot rescue a non-edge
**Architecture (ii) two-sleeve concurrent book is INFEASIBLE.** `src/crypto_trade/backtest.py` holds ONE
position per (model, symbol); `strategy.get_signal` returns ONE `Signal` per (symbol, open_time). A concurrent
trend-sleeve + reversion-sleeve book would require a backtest-engine rewrite AND would violate the HARD
backtest-live parity requirement (engine `_tick` is single-position) — out of scope and not justified by the
evidence. **Architecture (i) regime-router is the parity-clean choice** (a deterministic per-candle switch
that picks which existing override is eligible; both overrides — `enable_trend_state_dir` and
`enable_reversion_dir` — are ALREADY wired in `lgbm.py`). I evaluated two router classifiers:

| router | events (T / R) | IS Sharpe | top2 | recent yrs (22/23/24) | reversion marginal vs trend-only-under-router |
|---|---|---|---|---|---|
| trend-alone (reference) | 104 (104/0) | +0.402 | 0.710 | −0.29 / −0.41 / −0.17 | — |
| **R-ADX** (ADX14 ≥ median) | 230 (85/145) | **−0.086** | n/a | +0.03 / **−1.39** / −0.58 | Δshrp **−0.342 → DILUTIVE** |
| **R-CONV** (convATR ≥ trend-gate q) | 199 (109/90) | +0.464 | 0.541 | **−0.63** / −0.04 / −0.11 | Δshrp **+0.036 → trivially additive** |

**The CONTROL (trend-only under the SAME router, reversion disabled) is the decisive diagnostic:**
- R-ADX: reversion events (145 of them) crater Sharpe from +0.256 (trend-only) to −0.086 — **the iter-031-B
  crowding failure exactly: a high-count weak/negative stream wins the race to open and destroys the book.**
- R-CONV: trend-only-under-router already = +0.428; adding the 90 reversion events moves it to +0.464 — a
  **+0.036 marginal, within noise.** R-CONV's apparent strength is the *trend subset the conviction-router
  selects* (re-discovering the iter-027 conviction gate), NOT the reversion leg. The reversion events add
  essentially nothing — and they drag 2022 to −0.63.

## Section 3 — Combined-book IS screen vs the pre-registered PASS criteria
Pre-registered PASS (vs trend-alone, for the recommended router): (a) MORE events, (b) LOWER top-2 share,
(c) IS Sharpe ≥ trend-alone, (d) recent (2022/2023/2024) all non-negative.

| criterion | R-ADX | R-CONV |
|---|---|---|
| (a) more events | ✅ 230 > 104 | ✅ 199 > 104 |
| (b) lower top-2 | ❌ (negative net) | ✅ 0.541 < 0.710 |
| (c) Sharpe ≥ trend | ❌ −0.086 < +0.402 | ✅ +0.464 ≥ +0.402 |
| (d) recent non-neg | ❌ 2023 −1.39 | ❌ 2022 −0.63 |
| **verdict** | **NEGATIVE** | **NEGATIVE** |

Neither router PASSES. R-CONV clears (a)(b)(c) but FAILS (d) — and the control proves its (c) pass is a
trend-subset artifact, not a reversion contribution. The reversion leg is **dilutive-to-trivial**, never
net-additive. This is the iter-031-B failure mode (weak added signal de-concentrates the book but does not
add edge) — confirmed for a fourth-and-fifth combination mechanism.

## Section 4 — iter-033 architecture (DESIGNED, but NOT recommended for build)
For completeness (the design was the deliverable), the regime-router would have wired as a post-aggregator
RULE-layer selector analogous to the existing `_compute_trend_state` / `_compute_reversion_state` primitives:
- a deterministic past-only `_compute_regime(open_time)` returning TREND or CHOP (R-CONV form: `trend_conv[t-1]
  ≥ per-month q-quantile`, reusing the already-built trend-strength index);
- in `get_signal`, if regime==TREND apply the trend-state direction + conviction gate (existing path); if
  regime==CHOP apply the reversion direction + |z|/natr gate (existing path); mutually exclusive, single
  position; both branches already parity-safe (searchsorted past-only, FAIL-LOUD on missing parquet);
- `run_baseline_v1.py` ETH cell adds `enable_regime_router=True` plus the existing trend + reversion params.
- Backtest-live parity: identical to iter-027/032 (both override primitives already fire identically in
  backtest + `engine.py::_tick`); the router is a deterministic per-candle switch over them → parity-clean.

**This design is sound but should NOT be built**, because the reversion branch it routes to is a losing book
(Section 0.5 / 0.6). Routing a non-edge into the trend's stand-aside regimes adds turnover and drag, not breadth.

## Section 5 — Honest conclusion + path forward
- **PASS/NEGATIVE: NEGATIVE.** The two edges are de-correlated in timing (Jaccard 0.039) — the ONE premise
  that held — but they are NOT both profitable (reversion = −0.039 IS proxy, −0.61 IS backtest) and NOT
  cleanly regime-separable (ADX/conv medians nearly identical). The regime-router adds independent events and
  de-concentrates (R-CONV top2 0.71→0.54) but does so by routing in a **negative** book → DILUTIVE (R-ADX) or
  trivially-additive-then-2022-dragging (R-CONV). This is the iter-031-B crowding failure recurring.
- **The ETH breadth campaign is now exhausted across FIVE combination mechanisms** (iter-031's four —
  veto / modulate / re-slice / add-weak-trend-signals — plus iter-033's regime-routed different-edge). The
  recurring root cause is unchanged and now strengthened: **ETH has only ONE robust deterministic edge (the
  SMA200 trend-state, iter-027). The short-horizon reversion edge is a ddof-sensitive, single-year mirage that
  does not survive production wiring.** iter-027 (IS +0.6336 / OOS +0.0560) STANDS as the ETH breadth ceiling.
- **Methodology win:** this IS-only screen + the ddof reconciliation correctly PREDICTED iter-032's backtest
  failure (−0.61 IS) before reading it, and it kills the iter-033 backtest pre-emptively (~1.5–2h compute
  saved). The ddof=0/ddof=1 proxy-fidelity discrepancy is a generalizable lesson: **IS-design proxies must
  match the production std/ewm contract exactly, or they manufacture phantom edges** (append to the dead-paths
  catalog alongside the AGREE_SCALE inversion).
- **Recommended next axis (NOT another ETH breadth attempt):** adopt BASELINE_V1_ETHUSDT's own Critic
  next-steps — (2) direction-robustness K=5 swap of the ONE primitive the edge rests on (trend_state_symbol →
  BTC cross-asset regime, or SMA 100/300), and (3) genuine multi-outer-seed validation of iter-027 (the basin
  diagnostic is vacuous at outer-seeds=1). These harden the edge we HAVE rather than chasing a breadth that is
  structurally unavailable to the trend family. Alternatively, consolidate iter-027 as the ETH ceiling
  (parallel to BTC iter-020) and move to the next coin.

---

### Pre-registered falsifiers (all FIRED — recorded for the dead-paths catalog)
- **Both-profitable falsifier:** reversion standalone IS Sharpe ≤ 0 under production wiring → **FIRED** (−0.039
  proxy, −0.61 backtest).
- **Net-additive falsifier:** reversion marginal Δshrp (full router − trend-only-under-router) ≤ 0 → **FIRED**
  for R-ADX (−0.342); trivial (+0.036, within noise + 2022 drag) for R-CONV.
- **Recent-stability falsifier:** any of 2022/2023/2024 < −0.10 for the recommended router → **FIRED** (R-ADX
  2023 −1.39; R-CONV 2022 −0.63).
- **Contingency falsifier:** iter-032 backtest does not confirm the reversion edge transfers → **FIRED**
  (IS −0.6131 / OOS −0.8699).

### Leak guards / honesty
All statistics IS-only: `open_time < 1742774400000` asserted in `_common.load_*`; every entry's exit candle
forced strictly inside IS (`drop_horizon_crossing_oos` / per-config `otf < OOS_CUTOFF`); vol/conviction
quantile thresholds calibrated on IS rows only. No OOS price enters any reported number. Reversion direction
uses production-faithful `ddof=1`. Proxy-fidelity caveat honored: the per-candle non-overlap proxy does not
model the LightGBM per-month confidence gate or risk layers — but here the IS-proxy NEGATIVE is *corroborated*
by iter-032's full backtest, so the conclusion is robust to proxy fidelity.

Artifacts: `analysis/ETHUSDT/iteration_v1-033/{ensemble_screen.py, ensemble_screen.csv, ensemble_screen_output.txt, _common.py}`.
