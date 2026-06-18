# Diary — iter-v1/032 (ETHUSDT) — EXPLORATION — short-horizon MEAN-REVERSION edge — NEGATIVE (+ iter-033 ensemble NEGATIVE) → PIVOT to pure-deterministic trend

**Axis:** a genuinely DIFFERENT edge for breadth (after the trend family's de-concentration was exhausted,
4 mechanisms): deterministic SMA10 z-fade direction (`dir=−sign((close[t-1]−SMA10[t-1])/std10[t-1])`) +
high-vol z-gate (|z|≥1.5 AND natr≥q40), N=2 (16h) hold. IS screen had looked strong (485 events, +0.43,
WR 53.8%, positive all years).

**Backtest result (K=5): IS Sharpe −0.6131 / OOS −0.8699** — deeply NEGATIVE both. WR 51.9%/61.5% but
PF 0.69/0.63 (wins small, losses big: atr_sl=1.45 cuts losses tight while the 16h timeout caps wins —
bad reversion risk/reward). 104 IS / 39 OOS trades. DECISIVELY DEAD.

## Root cause — a ddof PROXY ARTIFACT (dead-paths-catalog lesson)
The iter-032 IS screen computed the z-score std with `rolling(10).std(ddof=0)` (population), giving the
cited +0.426. The PRODUCTION primitive `lgbm.py::_reversion_price_z` uses pandas default **`ddof=1`**
(sample). Production-faithful, the reversion edge is IS Sharpe **−0.039** — negative/breakeven in 4 of 5
IS years (2022 −14%, 2024 −34%), carried entirely by a single 23-event 2023. **The +0.426 was a ddof
artifact inflating a regime-fragile mirage; the backtest (ddof=1 + the LightGBM head + gate) is −0.61.**
**LESSON: IS-design proxies MUST match the production std/ewm contract (ddof) EXACTLY, or they
manufacture phantom edges.** This is the 3rd IS-proxy-didn't-transfer event (iter-030 AGREE_SCALE,
iter-032) — IS screens are necessary-not-sufficient; the backtest is the only arbiter.

## iter-033 — TREND × REVERSION regime-complementary ensemble — NEGATIVE (committed 25c7e13d)
The creative "combine two STRONG de-correlated edges" idea (vs iter-031-B's weak signals). NEGATIVE:
(a) the reversion edge isn't actually profitable (ddof, above); (b) regimes are NOT separable on ETH 8h
(median ADX14 at trend vs reversion events 24.1 vs 26.6 — nearly identical; reversion fires MORE in
high-ADX trending candles, not chop — the "liquidation-exhaustion" story doesn't hold at 8h); (c) the
regime-router CONTROL (trend-only) shows reversion events DILUTE the book (R-ADX Sharpe +0.256→−0.086,
the iter-031-B crowding failure again). Two-sleeve concurrent book infeasible (engine is single-position
— HARD parity). NEGATIVE.

## ETH single-symbol breadth — now exhausted across SIX mechanisms
M2 meta-labeling veto (/028-029) · AGREE_SCALE conviction modulation (/030) · exit-ladder (/031-A) ·
multi-signal entry (/031-B) · mean-reversion different-edge (/032) · trend×reversion ensemble (/033).
**Empirical conclusion: ETH's only robust 8h alpha is the slow concentrated trend (iter-027). Neither
de-concentrating it nor adding a higher-frequency edge works at 8h.** iter-027 (IS +0.6336/OOS +0.0560)
remains BASELINE_V1_ETHUSDT.

## NEXT (not giving up — creative pivot, campaign-thesis-grounded): iter-034 = PURE-DETERMINISTIC TREND
The campaign's core thesis: DETERMINISTIC parts generalize, LEARNED parts overfit. iter-030's forensic
proved the LightGBM ENTRY-TIMING layer is overfit (de-correlating from it lifted OOS to +0.24). The
deterministic core (200-SMA trend-state direction + conviction gate q=0.40) is what merged at iter-020/027.
**Hypothesis:** STRIP the LightGBM entry layer and trade the PURE deterministic rule — enter EVERY
conviction-gated candle in the trend-state direction, 14d hold, R-stack. This (a) BROADENS (many more
events than the model-gated ~32 OOS → de-concentration), (b) REMOVES the overfit entry selection (iter-030
showed it hurts OOS), (c) is fully deterministic (no lottery, no model). Directly tests "does the
LightGBM add value over the deterministic core, or just overfit?" — informative + bold either way.
Implement a `deterministic_entry_only` mode (model→bypassed; enter on all gated candles) + launch K=5.
