# MN4 UNIFIED-01-03 — No-Trade-Band Cost-Discipline Experiment

**User-directed 2026-07-12** (the surgical follow-on after the cadence sweep was falsified).
"Keep daily evaluation but only rebalance a name when its target moves beyond a band — skip
small churn, keep the large re-ranking moves that carry the edge."

## What was built
- **Opt-in engine hook** `trade_band: float | None = None` on `blind_engine.run_backtest`. Applies
  per-name hysteresis on the **alpha-leg** target weights only (post weighting/cap/beta-neut, pre-hedge);
  the **hedge legs (BTC/ETH) adjust every rebal → neutrality preserved**. Default `None` is a clean
  no-op (zero FP ops on the legacy path). **Verified bit-identical: 77 engine+unified tests pass**
  (number-asserting engine tests + the unified replay test). De-risk passes through naturally (a regime
  scalar halving gross creates big moves that exceed the band).
- Core algorithm UNCHANGED — composite signal/universe/scalar/hedge byte-identical; only `trade_band` varies.

## IS sweep (daily rebal preserved; band varies)

| band | turnover | Sh 1× | Sh 2× | maxDD(2×) | annRet(2×) | 2×/1× |
|---|---:|---:|---:|---:|---:|---:|
| None (baseline) | 123× | +1.86 | +1.51 | −32.9% | +45% | 0.82 |
| **0.02** | **105×** | **+1.86** | **+1.55** | **−30.3%** | **+48%** | 0.83 |
| 0.05 | 61× | +1.09 | +1.06 | −37.2% | +27% | 0.97 |
| 0.10 | 15× | +0.79 | +0.77 | −33.2% | +12% | 0.97 |
| 0.15 | 5.8× | −0.13 | −0.16 | −28.6% | −2% | 1.25 |
| 0.20 | 2.9× | +0.00 | −0.02 | −23.5% | −1% | — |
| 0.30 | 1.9× | +0.07 | +0.06 | −20.7% | +0% | 0.87 |

**IS read:** a TIGHT 2% band gives a marginal gain (+0.03 Sh2×, −15% turnover, shallower DD) by trimming
the tiniest noise trades. But there's a **cliff at 5%**: gross Sharpe collapses (+1.86 → +1.09) even though
the 2×/1× ratio jumps to 0.97 (costs nearly eliminated) — the 2–5% moves are carrying real re-ranking edge,
and holding them loses more than the cost saves. At 10%+ the edge is destroyed.

## Holdout reveal of the IS-winner (band=0.02) — the experiment's payoff

| band | turnover | Sh 1× | Sh 2× | maxDD(2×) | annRet(2×) |
|---|---:|---:|---:|---:|---:|
| None | 121× | +1.10 | **+0.81** | **−26.0%** | **+27%** |
| 0.02 | 98× | +1.10 | +0.61 | −29.1% | +17% |

*(warmup=300; absolute baseline differs slightly from the UNIFIED-01-03 diary's +0.951 which used the
engine's native warmup — the band-vs-baseline COMPARISON at constant warmup is what matters.)*

**The IS gain does NOT generalize.** On holdout, band=0.02 HURTS: Sh2× +0.81 → +0.61, maxDD −26% → −29%,
annRet +27% → +17%. The tiny IS improvement was IS-specific noise, not a robust cost saving.

## Verdict — the book is at its cost-efficient frontier
Both cost-discipline levers are now falsified:
- **Cadence** (slowing rebal): hurts IS monotonically — the 60c momentum needs daily re-ranking.
- **Band** (no-trade hysteresis): a tight 2% band gives a marginal IS gain that does NOT survive the
  holdout; looser bands destroy the edge.

**The daily churn is carrying real edge.** At 123× turnover the doubled cost takes only ~18% of the edge
(2×/1× ratio 0.82) — the cost wall is not this book's binding constraint, and there is no hidden cost
saving to extract. **No change to the frozen daily unified book.**

## What's kept
The `trade_band` opt-in engine hook stays (default None, bit-identical, 77 tests green) — a dormant,
verified cost-discipline primitive available for a future faster-turnover book where costs ARE binding.
It cost nothing on the legacy path and the experiment proved it's correctly wired (the 2×/1× ratio
rising to 0.97 at wide bands confirms the band genuinely suppresses cost; the gross-Sharpe collapse
confirms it correctly holds positions).

*— Orchestrator, MN4, 2026-07-12. No-trade-band experiment: falsified (IS-gain doesn't generalize; edge
needs the daily churn). Book at cost-efficient frontier. Engine hook retained (opt-in, bit-identical).
Opus 4.8.*
