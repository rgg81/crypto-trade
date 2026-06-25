# EXPLORATION-001 — Metals directional TREND ANCHOR

**Track:** metals portfolio (parallel to crypto `portfolio-iteration`). **Date:** 2026-06-25.
**Verdict:** ✅ **PASS** (Critic) — kept as the iter-001 directional anchor; advance to iter-002.
**OOS:** hidden (OOS_CUTOFF 2025-03-24). All numbers below are **IN-SAMPLE only**.

## The one change
First iteration: establish a directional time-series trend anchor on the 4 Binance precious-metal
perps (XAU/XAG/XPT/XPD). Net long exposure allowed (the anchor; iter-002 strips the beta).

**Mechanism (from QR diagnostics):** a naive symmetric multi-horizon sign-trend scores IS Sharpe
**−0.60 / maxDD −70%** — and the loss is entirely the SHORT leg (LONG +0.18 / SHORT −0.71).
Precious metals carry a secular long drift (gold $1050→$5500, central-bank buying, real-rates/USD
hedge); shorting a 28–56d downswing fights that drift and gets whipsawed in the 2015–2020 chop.

**Design:** long-biased trend filter — each metal carries a base-load long `FLOOR=0.5`, stepped up
to 1.0 while `EMA(84) > EMA(189)` (confirmed uptrend), cut back to the floor in downtrends —
**never shorts**. Inverse-vol sized (auto-tilts to gold = lowest rvol, cleanest trender), then fed
to the leak-safe core `net_from_raw` (gross-norm → `.shift(1)` lag → taker cost → ~15% vol-target,
≤5× lev). Implementation: `analysis/portfolio/metals/iter_001_trend.py:build()`.

Pre-registered tunables (no per-month tuning): `EMA_FAST=84, EMA_SLOW=189, FLOOR=0.5`.

## Results (IS-only)
| Config | IS Sharpe | maxDD | netTot | turnover/candle |
|---|---|---|---|---|
| **CENTER** (EMA84/189, FLOOR=0.5) | **+0.40** | −23.7% | +154% | 0.0086 |
| Reference: always-long inverse-vol (FLOOR=1.0) | +0.36 | −25.9% | +136% | 0.0053 |
| Drop-gold (center, ex-XAU) | +0.18 | −30.0% | +69% | 0.0039 |

- **Robustness sweep** (FAST{63,84}×SLOW{168,189,210}×FLOOR{0.25,0.5,0.75}, 18 cells): all in
  **[+0.37, +0.45]**, 100% > 0, 100% > +0.20 — a genuine ridge, center mid-plateau (not a spike).
- **Cost stress (IS):** 1× (6bps) +0.40 → 2× (12bps) +0.37 → 3× (18bps) +0.35. Low-turnover anchor
  is highly cost-robust (matches the tight-spread, low-slippage premise).
- Per-year IS net%: {2015:−20.7, 2016:13.2, 2017:8.7, 2018:−2.6, 2019:21.4, 2020:27.7, 2021:−4.6,
  2022:1.5, 2023:−2.4, 2024:12.6, 2025:11.2}.

**Pre-registered criteria — 5/5 PASS:** center IS Sharpe ≥+0.30 (✓+0.40); maxDD shallower than
−30% (✓−23.7%); ≥80% of 18 cells >+0.20 and 100% >0 (✓100%/100%); drop-gold ≥+0.15 (✓+0.18);
center beats always-long reference on Sharpe AND maxDD (✓ both).

## Leak check (MANDATORY) — PASS
Corrupted ALL OHLC inputs from 2022-06-01 forward, rebuilt `build()`: all 6125 pre-cutoff IS net
candles + deployed weights **bit-identical** (max abs diff 0.00e+00). The EMA `ewm(adjust=False)`
recursion, the `.shift(1)` lag, vol-target `.shift(1)`, and ragged-start `.where(elig)` are all
past-only. Now a permanent regression: `tests/test_portfolio_metals_foundation.py::test_build_ema_path_is_past_only`
(+ `test_iter001_is_long_only`). Foundation suite 13/13 green.

## Critic note (CONSTRUCTIVE, read-only)
**PASS.** No blocking defect. Confirmed: leak-safe (incl. EMA recursion), honest sweep (no best-cell
selection, 3 tunables pre-registered), costs correctly applied on deployed-book turnover, long-only
`raw ≥ 0` mathematically guaranteed.
- **Watch hardest at CONFIRMATION (§4):** +0.40 is thin (n≈122 monthly, SE ≈ ±0.30 — not
  statistically distinguishable from the +0.36 reference or 0) and **regime-concentrated** (5/11 IS
  years negative/flat; bull years 2019/2020/2024/2025 supply ~half of netTot). Expected for a
  beta-carrying anchor — but a metals-bull OOS window must not be mistaken for edge. iter-002's MN
  overlay does the real diversification work.
- Non-blocking: bid-only Dukascopy pricing is a one-signed (conservative) bias on the long entry leg
  — partly absorbed by COST_SIDE; size it before live. Dukascopy(spot/CFD)-vs-Binance(perp) basis is
  a deploy-time concern, out of scope for IS math.
- Hygiene done this iter: EMA-path leak regression test committed (C1).

## Path forward → iter-002 (market-neutral relative-value overlay)
Highest value (Critic + roadmap): a **dollar-neutral cross-sectional book** summed into the same
`net_from_raw` accounting, to strip the anchor's metals-beta and add regime-orthogonal Sharpe in the
flat/bear years (2015/2018/2021/2023) where the anchor bleeds:
1. **Gold/silver ratio (XAU/XAG) mean-reversion** — the canonical metals RV trade; neutrality
   plumbing already tested.
2. **Precious-vs-industrial** (XAU/XAG vs XPT/XPD) — note: 2022+ only (size conviction; report as a
   sub-window, not a 10yr stat).
3. (anchor refinement) continuous trend-strength gate to trim the 2015 whipsaw drawdown.

## Files
- `analysis/portfolio/metals/iter_001_trend.py` (iteration)
- `analysis/portfolio/metals/universe_metals.py` (foundation), `ingest_dukascopy.py` (data)
- `tests/test_portfolio_metals_foundation.py` (13 tests incl. EMA leak + long-only)
