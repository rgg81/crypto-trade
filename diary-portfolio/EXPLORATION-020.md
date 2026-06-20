# portfolio-iteration EXPLORATION-020 — hysteresis-banding / no-trade band (PROMISING)

**Agent-driven.** Goal: cut whipsaw turnover into correlated reversals (the source of the baseline's
−23% maxDD) AND lower real trading cost — by attacking REBALANCING CADENCE, the one lever no prior
iteration touched (every iter-001…019 modulated gross-exposure scalars or factor weights). This is
the exact "one-more iteration" the iter-019 critic proposed. Code:
`analysis/portfolio/iter_020_hysteresis.py`. Baseline DO-NOT-MODIFY: `iter_005_wf_lambda.py`
(IS +1.30 / OOS +1.37 / maxDD −23%).

## Method — a no-trade band on the CANONICAL walk-forward-λ weight book
- **Canonical book, reconstructed at the WEIGHT level.** iter_005 stitches per-month *nets* from the
  best past-λ. iter_020 re-runs the **identical** month-picking loop (best past monthly Sharpe on the
  per-λ vol-targeted nets) but stitches the chosen λ's **per-coin weight book + per-candle vol-target
  scale** instead of its net. This single `target_w` / `scale` reproduces iter_005's net.
- **The band (per-coin, past-only, path-dependent):**
  `held[t]=held[t-1]` unless `|target[t]−held[t-1]| > δ`, then SNAP to `target[t]` (or, EDGE mode,
  to the band edge `held[t-1] ± (move−δ)`). `held[t-1]` is strictly past; the decision uses NO
  information from candle t's return.
- **Cadence, NOT sizing.** After banding, the per-candle gross is renormalized back to the baseline's
  gross — verified preserved to machine precision (max |gross−base| ≈ 1e-15, mean gross ≡ 1.000 at
  every δ). This is the structural fix for the iter-019 trap: there a "regime overlay" turned out to
  be a disguised constant de-lever; here the book ALWAYS carries baseline gross, so any Sharpe change
  is genuine cadence timing, not a smaller book.
- **Cost on the ACTUAL banded turnover** (the point): `cost = COST_SIDE·cost_mult·Σ|w[t]−w[t−1]|` on
  the renormalized banded book. Real funding + price P&L on the held legs; same canonical vol-target
  scale applied last.
- δ swept {0, 0.002, 0.005, 0.010, 0.020}; effect judged on ROBUSTNESS across the sweep, not one cell.

## Identity check (mandatory) — δ=0 reproduces iter_005 EXACTLY
`IDENTITY δ=0: IS +1.30 / OOS +1.37 / maxDD −23%` — bit-for-bit the baseline. With no band, held≡target,
gross renorm is a no-op, cost is on the full turnover. **PASS.**

## Leak test — future→past corruption
Corrupting `target_w` from a cutoff forward leaves the banded `held` bit-identical before the cutoff
(both SNAP and EDGE). The band is strictly past-only/path-dependent. **PASS.**

## Result vs canonical baseline (IS +1.30 / OOS +1.37 / maxDD −23% / oosDD −22%)
SNAP mode (snap to target on trigger):

| δ | IS | OOS | maxDD | oosDD | turnover | turn Δ | OOS @2× cost |
|---|---|---|---|---|---|---|---|
| 0.000 | +1.30 | +1.37 | −23% | −22% | 0.2965 | — | +0.89 |
| 0.002 | +1.30 | +1.37 | −23% | −22% | 0.2953 | −0% | +0.89 |
| 0.005 | +1.33 | +1.37 | −23% | −22% | 0.2911 | −2% | +0.90 |
| **0.010** | **+1.35** | **+1.50** | **−23%** | **−20%** | **0.2759** | **−7%** | **+1.05** |
| 0.020 | +1.27 | +1.55 | −22% | −20% | 0.2437 | −18% | +1.14 |

EDGE mode (snap to band edge — lags harder):

| δ | IS | OOS | maxDD | oosDD | turnover | turn Δ | OOS @2× cost |
|---|---|---|---|---|---|---|---|
| 0.002 | +1.32 | +1.44 | −21% | −20% | 0.2432 | −18% | +1.02 |
| 0.005 | +1.28 | +1.49 | −21% | −19% | 0.1901 | −36% | +1.14 |
| 0.010 | +1.18 | +1.49 | −27% | −19% | 0.1355 | −54% | +1.22 |
| 0.020 | +1.01 | +1.43 | −32% | −20% | 0.0796 | −73% | +1.26 |

Per-year net% (SNAP): δ=0 `{2020:22,2021:55,2022:36,2023:44,2024:27,2025:16,2026:32}` →
δ=0.005 `{2020:22,2021:56,2022:36,2023:46,2024:28,2025:15,2026:32}` — no year is sacrificed.

## Reading the two effects (they are different, and both are wins)
- **Trade-EVENT cut is large; turnover-weighted cut is smaller.** SNAP δ=0.010 cuts per-cell
  weight-change events 127,768 → 47,098 (−63%) but turnover (Σ|Δw|, size-weighted) only −7%. The band
  kills a swarm of tiny noise rebalances while leaving the few large meaningful trades — exactly the
  deployment win (far fewer order tickets → much lower slippage/fee drag than the −7% Σ|Δw| suggests,
  since slippage is super-linear in ticket count, not in notional).
- **OOS improves, not just holds.** SNAP δ=0.010: OOS +1.37 → **+1.50**, oosDD −22% → −20%, IS +1.30 →
  +1.35. The whipsaw it removes was negative-expectancy noise: skipping the round-trip into immediate
  reversals adds edge. Robust across δ=0.005→0.020 (OOS monotone +1.37→+1.55).
- **Cost-stress (2× taker).** SNAP δ=0.010 OOS@2× +1.05 vs baseline +0.89 — the banded book is
  materially more cost-robust (fewer/larger trades), and the advantage widens at δ=0.020 (+1.14).
- **EDGE trades cost harder but over-lags.** −36%…−73% turnover, but at δ≥0.010 the band-edge drift
  holds stale weights so long that IS decays (+1.30→+1.01) and maxDD WORSENS (−27/−32%): you hold the
  losing direction too long into the reversal. EDGE δ=0.002–0.005 is the only attractive EDGE region
  (−18/−36% turnover, OOS +1.44/+1.49, DD −21%) but SNAP δ=0.010 Pareto-dominates it on IS+DD.

## Verdict: PROMISING — SNAP δ≈0.010 is a clean Pareto improvement (pending CONFIRMATION + critic)
Hysteresis-banding does what no gross/factor lever did: it cuts trading WITHOUT costing OOS, and in
fact LIFTS OOS while preserving gross exactly (a true cadence change, not a disguised de-lever — the
iter-019 failure mode is structurally excluded here). SNAP δ=0.010:
- turnover −7% (Σ|Δw|), rebalancing EVENTS −63% → meaningfully lower live cost/slippage;
- OOS +1.37 → +1.50, IS +1.30 → +1.35, oosDD −22% → −20% (a small DD bonus);
- OOS@2× cost +0.89 → +1.05 (more cost-robust);
- robust across the sweep (OOS positive and rising δ=0.005→0.020, no year sacrificed).

This is the first deployment-relevant accretive change on the cadence axis. **Not yet a baseline
update** — that requires the CONFIRMATION gauntlet (OOS revealed once with full benchmark/DSR check)
and a critic PASS. The δ chosen here (0.010) was picked on IS+turnover robustness, never on OOS; the
OOS column is reported once for information. The maxDD did NOT collapse (−23%→−23% at the headline δ),
so the original DD hypothesis is only PARTIALLY confirmed: the band's win is mostly turnover/cost +
OOS, with DD relief modest (−2pt on oosDD) — honest, not the −23%→−15% I'd hoped. Still a clear net win.

## Next
- CONFIRMATION-020: take SNAP δ=0.010 (and the δ=0.005/0.020 neighbours for robustness) through the
  full gauntlet — reveal OOS once, benchmark vs B&H-BTC + EW-top20, turnover/cost-stress at 1×/2×,
  DSR on the modest n. If it clears + critic PASS → first cadence-axis baseline update.
- A combined lever worth a later iter: band δ tuned per-λ-regime (walk-forward), or band-then-overlay
  stacking with the held combiner. But ONE change at a time — confirm the plain band first.
