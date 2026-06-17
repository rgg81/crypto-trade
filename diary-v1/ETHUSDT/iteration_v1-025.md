# Diary — iter-v1/025 (ETHUSDT) — CONFIRMATION (K=20) — BOOTSTRAP (establishes BASELINE_V1_ETHUSDT)

**First ETH run of the single-symbol redesign.** Vanilla config (same as BTC iter-001): full 193-col
V1_FEATURE_COLUMNS, triple_barrier (ATR tp 2.9/sl 1.45, 7d), R3/R5 ON, R2 OFF, model-learned direction.
K=20, n_trials=35, slippage 2. Features regenerated 2026-06-17 to klines 2026-06-15 (cross-coin-
comparable to BTC). Purpose: establish the honest ETH baseline, then improve (user: "same idea — run a
confirmation first to generate the baseline then start improving").

**Result: IS Sharpe −0.4787 / OOS −0.9589 — BOTH NEGATIVE.** 215/81 trades, max DD 50.8%/26.2%, PSR low,
dispersion 47.67 (high). Clean run, 20/20 seeds.

**Verdict: BOOTSTRAP — establishes BASELINE_V1_ETHUSDT (weak, both-negative).** The vanilla directional
LightGBM has no edge on ETH (loses both windows; weaker than BTC's iter-001 which was at least
OOS-positive). This is the honest ETH bar; the improvement phase does the work.

**Next:** iter-v1/026 — apply the PROVEN BTC iter-020 stack to ETH (stateless 200-SMA trend-state
direction + conviction gate q=0.40 + fixed_horizon N=42 14d let-winners-run + R2 brake + R3/R5). The
highest-prior first improvement — it produced BTC's both-positive, and ETH's less-correction-dominated
2025-26 OOS may give the both-positive coherence a fairer test than BTC's. K=5 screen → K=20 confirm.
