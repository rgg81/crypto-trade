# Phase 7.5 Critic Review — iter-v1/006 (BTCUSDT) — EXPLORATION screen

## Verdict: NEGATIVE — funding LEVEL z-score is coherently-losing; funding family closed.

### Results (K=5 screen)
| | IS Sharpe | OOS Sharpe | ratio | dispersion | IS net | OOS net | trades | funding rank |
|---|---|---|---|---|---|---|---|---|
| iter-004 prune-only (K=20) | −0.17 | +0.48 | −2.82 (inv) | — | — | — | — | n/a |
| iter-005 prune+spread (K=5) | −0.43 | +0.85 | −1.97 (inv) | 40.05 | −18.37 | +12.13 | 194/83 | 16/42 |
| iter-006 prune+level-z90 (K=5) | **−0.3951** | **−0.4245** | **+1.07 (both neg)** | 40.89 | −18.01 | −5.53 | 200/87 | **29/42** |

### Critic's literal read
The generalization-coherence gate rewards a both-POSITIVE profile. iter-006 is sign-coherent but
both-NEGATIVE — a coherently-losing model, which is not mergeable and not an edge. The funding level
z-score made IS worse than prune-only (−0.40 vs −0.17) and turned OOS outright negative. **NEGATIVE.**

### Methodology PASS on results
- Honest-cost netting verified; IS/OOS split honored; full data; 5/5 seeds trained (287 trades).
- **OOS-vigilance:** iter-006 feature selection (FE `feature_ortho_scan.py`) verified IS-only —
  strict `open_time < OOS_CUTOFF_MS` filter (line 118) + leak-guard assert (line 119), forward
  returns computed post-filter (no OOS peek). Confirmed by reading the committed code, not prose.
- **Verifiability fix (task #130) validated:** importance CSV now 42 rows; `funding_rate_zscore_90`
  visible at rank 29/42. The feature trained — no silent drop. Standalone-probe rank 8 did not transfer.

### Flags
- **K-confound:** K=5 vs K=20 prune anchor; verdict robust to it (IS below anchor AND OOS negative).
- **Fragile-OOS insight:** the positive OOS of the inverted /004//005 configs is regime exposure, not
  edge — one feature flipped it to −0.42. Do not chase inverted-profile OOS numbers.

## Proposed Backtest Changes (mandatory)
1. **iter-v1/007 — NEW family (Open Interest): `btc_oi_delta_5_z30`.** The best non-funding candidate
   by raw dir_acc OOF lift; near-zero univariate IC means a non-linear positioning signal a tree may
   exploit where the linear funding signal failed. Completes the orthogonal sweep. Pre-register the
   both-positive coherence guardrail (NEGATIVE if profile stays neg-IS or both-negative).
2. **Do NOT re-screen `funding_rate_zscore_30`.** It is the same factor as z90 (0.78 corr; FE: "one
   factor"). z90 ranked 29/42 and failed; z30 is low-information to retest. Funding family closed at 2.
3. **If iter-007 (OI) also NEGATIVE → declare the orthogonal-feature axis closed for BTC** (funding×2 +
   OI tested, basis pre-screened degrading, long_short zero-IC, cross-asset dead). iter-008 pivots axis:
   label horizon, a regime gate, OR reconsider whether BTC — at max |IS-IC| 0.028, a noise-floor signal —
   is the right FIRST symbol vs a coin with a coherent IS edge. The FE headline is the real finding.
