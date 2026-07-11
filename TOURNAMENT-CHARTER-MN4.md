# TOURNAMENT CHARTER — MN4: the 10-idea blind parallel tournament

**Authorized by user 2026-07-11.** Full restart, blind again. Supersedes MN3 (concluded: 5
families + 1 spinout + 1 revision + 1 holdout reveal → zero deployable candidates; the one
holdout reveal MN3-G FAILED and that construction is now holdout-contaminated + closed — but the
2-year holdout DATA remains pristine for genuinely-new constructions). This tournament does NOT
re-mine the dead MN3 families; it sweeps the **untried mechanism/technique space**.

## MANDATE (the target is the same)
Find a strategy that **GENERALIZES**: high Sharpe, a **winner in EVERY market condition** (bull /
bear / chop / crash / mania), very controlled risk. **Market-neutral is the default doctrine**
(measured beta, not assumed); a small number of ideas pursue a different object (directional trend
or managed-variance) if it is genuinely all-weather — these are **labeled** below, and neutrality
is still MEASURED and reported for every book so the Critic can judge. When "the model is lost"
(black-swan / crisis), the construction must **de-risk toward the blue-chip core** (BTC / ETH /
top-liquidity majors), not blow up.

## SPLITS (unchanged, SACRED)
- **IS = 2020-01-01 → 2024-06-30** (4.5 yr: COVID, 2021 mania, 2022 collapse, 2023 chop, 2024-H1 mania).
- **HOLDOUT = 2024-07-01 → 2026-06-30 (2 years, SEALED).** ONE reveal per construction, EVER.
- **Stage-3 = post-2026-06-30** (forward paper-trade arbiter; accrues untouched).

## METHODOLOGY (load-bearing — non-negotiable for every pair)
1. **Honest engine from BIRTH.** NO diagnostic-only scoring. Every construction runs through
   `blind_engine.run_backtest` with: next-bar (open-to-open) fills; delisting names force-exited at
   an honest fill (no phantom returns from un-tradable names); honest per-side cost **5 + 2.5 bps +
   funding**; a GROUND-TRUTH 2×-cost twin (re-run, not analytic). *Prior lesson (S4): a diagnostic
   sleeve's Sharpe is NOT an executable book — close-to-close scoring overstates tradability by
   capturing bid-ask bounce + delisting artifacts + gross leverage. Do not repeat it.*
2. **IS-only.** Everything through the `mn3_split` guard (IS cutoff epoch 1719792000000 = 2024-07-01).
   ZERO reads of the holdout or Stage-3 — not even coverage stats. The guard is reused as-is.
3. **Leak battery on every construction:** corrupt-future positive control, decision-lag [k−1], PIT
   cross-sectional membership (no survivorship backfill), append-invariance where applicable.
4. **Cost-realism + slow-favored.** Cost-survival has been the binding constraint on this dataset.
   Favor low-turnover (weekly / daily) constructions. If you build a high-IC but fast book, expect
   it to die on cost and **engineer turnover suppression from the start** (continuous weights,
   no-trade bands, slower labels — principle-anchored, not fitted).
5. **Principle-anchored gates.** Any IS pass/fail threshold must be charter/structural
   (economic-relevance floors, sign tests, neutrality bounds) — NOT fitted to your IS result. You
   will be revealed on unseen data; a gate fitted to IS is worthless OOS.
6. **Neutrality MEASURED.** Report realized rolling β_BTC, β_ETH, and CRASH/MANIA-bucket β for
   every book, neutral-by-design or not.
7. **Crisis de-risk.** Every construction carries a pre-registered crisis/de-risk primitive (gross
   throttle toward the blue-chip core, or flat, in acute stress). Both shared crisis "floors" are
   dead (CRISIS-FALSIFY-003: detection is easy, calm-time occupancy is the killer) → use a
   **per-construction Layer-2 throttle** (constants principle-anchored) or a regime-gate, NOT a
   shared machine.

## PROCESS (the tournament)
- **Phase A — parallel development (QR+QE pairs, NO Critic):** 10 ideas, 10 pairs, fully parallel.
  Each pair: design → implement (`analysis/portfolio/mn4_ideaNN_*`) → IS engine backtest → leak
  checks → **freeze the construction byte-exact** + write brief (`briefs-portfolio-mn4/IDEA-NN.md`)
  + diary (`diary-portfolio-mn4/IDEA-NN.md`) with the full IS scorecard. **NO holdout. NO Critic**
  (the Critic comes after, by user direction).
- **Phase B — reveal ALL 10:** every construction scored on the sealed 2-year holdout, ONE look
  each, against its frozen gates. Tokens MN4-01..10 spent (REVEAL-LEDGER). Terminal per
  construction: PASS → candidate / FAIL → closed.
- **Phase C — Critic tournament review:** the Critic reviews all 10 revealed results **together**,
  applies **multiple-testing correction across the tournament**, and confirms whether the WINNER is
  a genuine generalizer (not a multiplicity artifact). The Critic's verdict is final for who (if
  anyone) proceeds to Stage-3 paper trade.

## THE 10 IDEAS (orchestrator-curated for diversity; each pair has full latitude within its seed
to choose techniques, features, and parameters — the seed only guarantees coverage + non-collision)

| # | Name | Mechanism (1-line) | Obj | Key advanced technique | Freq |
|---|---|---|---|---|---|
| 01 | **TS-Momentum (blue-chip)** | time-series trend on BTC/ETH/top-5, beta-hedged into a basket | neutral | vol-scaled trend signal (risk-equalized) | weekly |
| 02 | **Meta-Labeled Breakout** | primary breakout/donchian + a meta-classifier filtering false breaks | neutral | López de Prado meta-labeling (LightGBM) | daily |
| 03 | **Regime-Adaptive Allocator** | detect regime (trend/chop/stress) → switch gross + universe (full→blue-chip in stress) | neutral | HMM or vol/corr regime detector; the user's "interrupt-in-crisis, stick to blue chips" mandate | daily |
| 04 | **Slow ML Factor** | residual-alpha ML signal at DAILY cadence, weekly hold, turnover-suppressed | neutral | LightGBM walk-forward + meta-label + continuous weights (the cost-engineered ML factor) | daily |
| 05 | **Kalman Stat-Arb** | cointegration/stat-arb on major pairs, adaptive hedge ratios | neutral | Kalman-filtered hedge + structural-break kill-switch | daily |
| 06 | **Funding-Rate Prediction** | predict next funding from microstructure; trade the predicted-vs-implied convergence | neutral | model the RATE (not its level); regression on OI/taker/basis proxies | daily |
| 07 | **XS Reversal (dispersion-gated)** | fade extreme short-horizon winners cross-sectionally, ONLY in high-dispersion windows | neutral | dispersion conditioning (concentrate gross where the edge is richest) | daily |
| 08 | **Vol-Targeted Risk-Parity** | managed-variance across blue-chips: scale gross inverse-vol, hard crisis de-risk | **directional** | vol-targeting (CTA standard) + crisis overlay | daily |
| 09 | **Calendar / Seasonality Tilt** | exploit crypto weekend/monthly seasonality on majors | **directional** | calendar effect; ultra-low turnover (cost-immune) | weekly |
| 10 | **Born-Diverse Ensemble** | 3-4 genuinely-orthogonal slow signals combined at inverse-vol from birth | neutral | diversification as the PRIMARY design (the user's ensemble directive) | weekly |

**Why these ten:** the dead MN3/H/J/I/K families were all cross-sectional carry / crowding /
liquidity / residual-alpha at 8h-1h. The strongest all-weather priors in quantitative finance —
**time-series momentum, statistical arbitrage, meta-labeling, regime-adaptive allocation,
volatility-targeting, calendar effects, born-diverse ensembles** — were NEVER tried in this track.
This tournament sweeps exactly that untried space. Trend-following and stat-arb in particular are
the canonical Sharpe-positive-all-regimes strategies; excluding them (as prior tracks did) leaves
the best generalization priors on the table.

## NAMESPACES & RULES (10 pairs share ONE worktree — collisions break everything)
- **Files:** `analysis/portfolio/mn4_ideaNN_*.py`, `data/mn4_ideaNN/`, `tests/test_mn4_ideaNN_*.py`,
  `briefs-portfolio-mn4/IDEA-NN.md`, `diary-portfolio-mn4/IDEA-NN.md`. **STRICT namespacing** —
  every file you create carries your `mn4_ideaNN` prefix; never touch another pair's files.
- **Reuse (read-only / tested, do NOT modify):** `blind_engine.py`, `mn3_split.py`,
  `mn3_regimes.py`, `mn_beta`, the funding/OI loaders, `mn3_features` helpers where useful.
- **Do NOT git commit** — the orchestrator commits centrally.
- **Model:** Opus 4.8 (Fable rate-limited this session; user-directed). Disclose in your diary.

## HONEST PRIOR (set expectations)
Four prior baseline-blind tracks concluded NULL on this dataset (no cost-surviving all-weather
edge via cross-sectional mechanisms at 8h/1h; every "crash-robust" signal was an IS artifact).
This tournament mines a genuinely different space, so the prior is more open — but expect **most
of the 10 to fail**. The value is the breadth + the tournament-Critic design giving the best shot
at a real generalizer. A clean null across 10 diverse untried ideas would itself be a strong,
final structural result. **A FAIL on the holdout is the methodology working, not a disappointment.**

*— Orchestrator, MN4 tournament, 2026-07-11. Ten parallel pairs; reveal-all; Critic ranks. The
2-year holdout is sacred and pristine for these constructions.*
