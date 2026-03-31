# Iteration 097 Diary — 2026-03-31

## Merge Decision: NO-MERGE (EARLY STOP)

**Trigger**: Year 2025 OOS PnL=-67.5%, WR=35.4%. IS was positive (+0.78) but OOS collapsed to -1.07.

**OOS cutoff**: 2025-03-24

## Hypothesis

Sample uniqueness weighting (AFML Ch. 4) would fix overlapping label bias by down-weighting crowded periods. Expected: improved OOS/IS ratio.

## Results

| Metric | Iter 097 | Baseline (093) |
|--------|----------|----------------|
| IS Sharpe | +0.78 | +0.73 |
| IS WR | 43.5% | 42.8% |
| IS MaxDD | 87.6% | 92.9% |
| OOS Sharpe | **-1.07** | +1.01 |
| OOS WR | 35.6% | 42.1% |
| OOS MaxDD | 76.2% | 46.6% |

## Gap Quantification

OOS WR is 35.6%, break-even is 33.3%, gap is +2.3 pp (barely above break-even). But PF 0.80 means losses dominate. Baseline OOS WR was 42.1%. Uniqueness weighting caused a **6.5 pp WR collapse** in OOS while IS WR slightly improved.

## What Failed

1. **Uniformly low uniqueness values destroyed |PnL| weighting.** With 7-day timeout and 8h candles, every sample overlaps ~21 others. Uniqueness ≈ 1/21 ≈ 0.046 for all samples. Multiplying |PnL| weights by 0.046 essentially makes all weights equal (range [0.05, 1.68] vs baseline [1, 10]). The |PnL|-based weighting — which gives the model information about trade conviction — was critical for OOS performance.

2. **IS improved, OOS collapsed — classic researcher overfitting.** The uniqueness weighting changed which samples the model emphasizes during training. This happened to help IS (+0.05 Sharpe, +0.7 pp WR) but hurt OOS (-2.08 Sharpe). The change didn't generalize.

3. **AFML's uniqueness assumes sparse labeling.** The technique was designed for event-driven sampling where only a fraction of candles are labeled. In our setup, ALL candles are labeled, creating near-uniform overlap. The technique has no discriminating power when applied to dense labeling.

## Research Checklist Completed

- **A**: Feature analysis (185 features confirmed essential, no changes)
- **C**: Labeling analysis — 78.3% of trades have overlap, 18% flip rate, labels are stable
- **E**: Trade patterns — model excels in volatile markets, fails in choppy periods
- **F**: Statistical rigor — WR 42.8% [37.6%, 48.0%] CI, significantly above break-even

## Exploration/Exploitation Tracker

Last 10 (iters 088-097): [X, E, E, E, X, E, X, E, X, **E**]
Exploration rate: 6/10 = 60%
Type: **EXPLORATION** (sample uniqueness weighting — AFML Ch. 4)

## Lessons Learned

1. **AFML sample uniqueness doesn't apply to dense labeling.** When ALL candles are labeled with overlapping windows, uniqueness is uniformly ~1/N_overlap for all samples. The technique provides no discrimination — it just scales all weights down equally.

2. **|PnL| weighting is a valuable signal, not noise.** The baseline's |PnL| weights (range [1,10]) give higher weight to trades with larger outcomes. This is effectively an implicit bet-sizing signal. Removing it (as uniqueness weighting did) degrades OOS.

3. **IS improvement doesn't predict OOS improvement.** Iter 097 had better IS than baseline but much worse OOS. The OOS/IS Sharpe ratio went from +1.38 to -1.38 — a sign of overfitting.

## Next Iteration Ideas

1. **EXPLORATION: Time decay weighting only (no uniqueness).** Instead of uniqueness, add exponential time decay: recent samples weight ~1.0, oldest weight ~0.25. Half-life = 12 months. This preserves the |PnL| weighting while adding recency bias. Mathematically: `weight = |PnL| * exp(-lambda * age)`.

2. **EXPLORATION: Per-symbol models.** BTC and ETH have fundamentally different OOS dynamics (BTC 33.3% WR vs ETH 50.0%). Separate models with own Optuna optimization.

3. **EXPLORATION: Event-driven sampling.** Instead of labeling ALL candles, only label high-volatility events (range_spike > threshold). This naturally creates sparse labels where uniqueness weighting would actually work. Combined with the existing range_spike filter.
