# Engineering Report — iter-v3/088

## Headers

- Iteration: iter-v3/088
- Branch: iteration-v3/088
- Commit SHA (code, pre-backtest): 1d3d0a45e778f7871f695a331e7d9b58efbc0ab6
- Hardware: DESKTOP-H1H6T11, 20 logical cores (WSL2)
- Wall-clock time: 0h 22m 23s
- Exit code: 0 (clean)

---

## Configuration Diff vs Baseline

iter-v3/088 is a re-architecture. The baseline (BASELINE_V3.md / tag v0.v3-059) runs N per-symbol
LightGbmStrategy instances on a 3-symbol universe. This iteration replaces that entirely with:

- Model: ONE pooled LGBMRanker(objective="lambdarank") — new module
  `src/crypto_trade/strategies/ml/cross_sectional.py`
- Universe: 22-symbol XS_UNIVERSE (non-v1/v2 Binance-USDT perps, IS-screened)
- Label: cross-sectional forward-return rank {0,1,2} at H=3 bars — replaces triple-barrier
- Position: dollar-neutral tercile long-short, inverse-vol weighting, portfolio vol-targeting
- Feature set: 13 features (14-feature /059 stack minus btc_ret_14d, cross-sectionally rank-normalized)
- CPCV gap: XS_REQUIRED_GAP=88 = (H+1)*N_symbols = (3+1)*22 (distinct from legacy REQUIRED_GAP=66)
- Rebalance cadence: every 8h bar (continuous book)
- Fee: 0.1% per side, turnover-based (charged on absolute position delta per bar)
- Runner: run_cross_sectional_v3.py (new; the per-symbol run_baseline_v3.py is untouched)
- Seeds: 1 (EXPLORATION mode; n_trials=35)

The legacy 7-gate v3 risk stack is intentionally ABSENT from this iteration (Section 3.7 of brief:
re-introducing gates would confound the architecture measurement). Three structural controls replace
them: dollar-neutral construction, inverse-vol weighting + vol-targeting, tercile diversification.

---

## Key Metrics Block

| metric | in_sample | out_of_sample | ratio |
|---|---|---|---|
| monthly_sharpe | -0.6403 | -0.5418 | 0.846 |
| max_drawdown | 34.03% | 20.23% | 0.594 |
| n_trades (bar-symbol rows) | 46,806 | 17,612 | 0.376 |
| total_pnl | -0.7646 | -0.1544 | — |
| OOS rank-IC (mean) | — | +0.0430 | — |
| OOS rank-IC (std) | — | 0.3317 | — |
| OOS rank-IC (n_timestamps) | — | 1,255 | — |
| OOS rank-IC t-stat | — | +4.59 | — |
| frac_positive_paths (CPCV) | 0.000 | — | — |
| n_trials | 35 | — | — |

Total panel rows: 64,418 (46,806 IS + 17,612 OOS).

---

## Sign Diagnostic (the Central Question)

### 1. `build_positions` code trace

The relevant excerpt from `src/crypto_trade/strategies/ml/cross_sectional.py` lines 581-587:

```python
# Sort by score ascending.
order = np.argsort(scores)
sorted_syms = syms[order]

n_leg = max(1, int(np.floor(n * tercile_frac)))
long_syms = set(sorted_syms[:n_leg])  # bottom tercile → LONG
short_syms = set(sorted_syms[-n_leg:])  # top tercile → SHORT
```

`np.argsort(scores)` sorts ascending. `sorted_syms[:n_leg]` = the LOWEST-score symbols → LONG.
`sorted_syms[-n_leg:]` = the HIGHEST-score symbols → SHORT.

The `predict_ranking` docstring (lines 513-515) states:

```
"Higher score = model predicts this symbol will RANK HIGHER (i.e., be
a top-tercile forward-return symbol in the cross-section). Given the
reversal signal (negative IC), higher score → lower forward return →
SHORT candidate; lower score → LONG candidate."
```

### 2. Brief Section 3.4 specification

Brief Section 3.4 (position construction) states:

> "Long the bottom tercile (grade-0 / low-score symbols — **the reversal long: recent cross-section
> under-performers are predicted to bounce**) and short the top tercile."

The brief explicitly specifies: long the low-score (bottom-tercile) symbols, short the high-score
(top-tercile) symbols. The code implements this exactly.

### 3. Verdict: 3b — Brief Design Issue (NOT an implementation bug)

The `build_positions` code is correctly aligned with the brief's Section 3.4 specification.
The brief itself contains the erroneous assumption that drives the sign problem. The
design issue is:

**The label `label_cross_sectional_rank` assigns grade {0,1,2} based on FORWARD return rank:**
- Grade 0 = bottom-third of forward returns = future underperformers
- Grade 2 = top-third of forward returns = future outperformers

The `LGBMRanker` with `lambdarank`, trained on these grades, learns: **high predicted score →
high label grade → high FUTURE return**. Confirmed by pooled IS Spearman:
`Spearman(predicted_score, label_grade) = +0.0328` (p=1.2e-12).

The brief's position logic assumed that a "reversal signal" (the EDA's negative rank-IC between
PAST returns and FUTURE returns) would somehow cause the LGBMRanker to assign low scores to
future winners. It does not. The model learns the FORWARD mapping: high score = high future return.
Therefore:

- `long_syms = sorted_syms[:n_leg]` = low-score symbols = **predicted future losers** → the book
  LONGS symbols expected to underperform.
- `short_syms = sorted_syms[-n_leg:]` = high-score symbols = **predicted future winners** → the
  book SHORTS symbols expected to outperform.

The reversal logic was grounded in the EDA's PAST-return predictor, where high past return → low
future return (negative rank-IC). But the LGBMRanker is trained on the FORWARD return label, so it
learns the opposite mapping — high score = high future return — and the brief's position sign is
inverted relative to what the model actually produces.

The `predict_ranking` docstring attempted to patch this with "given the reversal signal (negative
IC), higher score → lower forward return," but this reasoning is wrong: the IS Spearman computed
above (+0.033) confirms the model's high scores DO correctly predict high forward returns.

**Summary:** The position construction in both the brief and the code longs the predicted future
losers and shorts the predicted future winners. This is a brief design issue (3b), not an
implementation bug — the code faithfully implements what the brief specified.

---

## Per-Leg PnL Evidence

Computed from `in_sample/trades.csv` and `out_of_sample/trades.csv`:

| leg | IS gross | IS fee | IS net | OOS gross | OOS fee | OOS net |
|---|---|---|---|---|---|---|
| Long (position > 0) | −0.3764 | 0.3503 | −0.7268 | −0.0122 | 0.0853 | −0.0974 |
| Short (position < 0) | +0.2985 | 0.3363 | −0.0378 | +0.0096 | 0.0666 | −0.0570 |
| Book total | −0.0780 | 0.6866 | −0.7646 | −0.0026 | 0.1518 | −0.1544 |

The long leg has NEGATIVE gross PnL (longing symbols that actually underperform → consistent with
the sign issue) and the short leg has POSITIVE gross PnL (shorting symbols that actually
outperform → correct direction, generating positive gross from the shorts). Both legs are net
negative because the fee drag (IS: 0.69, OOS: 0.15) overwhelms the gross signal.

OOS mean predicted score: long leg = −0.252 (longs low-score = predicted losers), short leg =
+0.141 (shorts high-score = predicted winners). This mirrors IS and confirms the structural issue.

---

## Flipped IS Sharpe (Diagnostic)

Under a position-sign flip (`position → −position`, `gross_pnl → −gross_pnl`, fee unchanged):

- Flipped IS gross monthly Sharpe: **+0.0670** (vs original −0.0670)
- Flipped IS net monthly Sharpe: **−0.4308** (vs original −0.6403)

The flipped gross IS Sharpe is trivially positive (+0.067), confirming the sign issue is real but
small. Critically, the flipped net IS Sharpe is still deeply negative (−0.43), because the fee
drag (IS total fees = 0.6866 vs IS gross = −0.0780) overwhelms even the correctly-oriented gross
signal. The sign inversion is a real design flaw but it is NOT the primary failure driver — the
turnover cost is.

This means that fixing the sign alone (flip positions) would produce IS gross monthly Sharpe
≈ +0.07, still far below the floor needed for net profitability after 0.1% × 2 × every-8h-bar
fees. The architecture's core problem is that the 8h rebalance cadence generates turnover that
overwhelms the weak +0.04 OOS rank-IC signal.

---

## frac_positive_paths Interpretation

`frac_positive_paths = 0.000` — all 45 CPCV paths have negative net PnL. Given the deeply
negative net Sharpe (IS −0.64, OOS −0.54), this is consistent and unsurprising. It would be
equally 0.000 with the sign flipped (flipped net IS Sharpe = −0.43, still negative across all
paths). The CPCV label-proxy is meaningful here as a confirmation that the book never generates
positive returns on any path subset, not as a standalone gate.

---

## Seed Concentration Audit

Single seed (seed=42, EXPLORATION mode). Per-symbol IS concentration (`per_symbol.csv`):
max IS concentration = TRXUSDT at 16.1% of IS book PnL. No symbol exceeds 17%. 22-symbol
universe is structurally diversified as designed (tercile: ~7 names per leg).

OOS per-symbol: max OOS concentration = FILUSDT at 10.5% and CRVUSDT at 14.3%. No symbol
exceeds 15% OOS. The brief's F5 falsifier (no single symbol > 50% OOS book PnL) is PASS.

---

## Label Leakage Audit

Walk-forward uses `train_end_ms = test_start_ms − embargo_ms`, where:
- `embargo_ms = XS_REQUIRED_GAP * interval_ms = 88 * (8 * 3600 * 1000)`
- `XS_REQUIRED_GAP = (H + 1) * N_symbols = (3 + 1) * 22 = 88`

The embargo removes, on both sides of every test boundary, enough pooled panel rows so that no
training label's H=3 forward window overlaps a test row. The e149e9d walk-forward fix (carry-over
from the per-symbol path) is confirmed active in `_generate_xs_monthly_splits` at
`cross_sectional.py:951`. No lookahead bias.

---

## Gate Efficacy Table

The legacy 7-gate v3 risk stack is intentionally absent (brief Section 3.7). The three structural
controls are:

| Control | Mechanism | IS status |
|---|---|---|
| Dollar-neutral long-short | Both legs always present; gross long = gross short notional | Active; confirmed by symmetric IS n_trades (23,403 long / 23,403 short) |
| Inverse-vol weighting + vol-target | Per-symbol 1/σ weights + portfolio vol scaling | Active; max IS symbol concentration 16.1%, structurally capped |
| Tercile diversification | ~7 names per leg | Active; 22-symbol universe across full IS |

---

## Anomaly Notes

Random spot-check (10 rows sampled from `out_of_sample/trades.csv`): entry/exit math is consistent
(gross_pnl = position × next_1bar_return; net_pnl = gross_pnl − fee; fee = |pos − prev_pos| ×
0.001). Rows with label_grade=None (last H bars before data end) carry valid PnL and are correctly
excluded from rank-IC computation.

OOS per-symbol monthly_pnl has no zero-trade months in a pathological sense — the cross-sectional
book always has ≥22 active symbols in the cross-section at each bar, so every OOS month has
thousands of bar-symbol rows. The EOSUSDT IS row count (2,135) vs OOS (135) reflects the 60-day
burn-in applied per-symbol, which correctly restricts EOSUSDT to its listed history window; this
is expected and documented in the brief.

---

## Status

OVERALL=READY-FOR-CRITIC

### Sign Diagnostic Verdict: **3b — BRIEF DESIGN ISSUE**

The code correctly implements what the brief specified. The brief incorrectly assumed that a
LGBMRanker trained on FORWARD-return grades would exhibit an inverted score-to-return mapping
(because the EDA found a past-return reversal). In fact the model learns the correct FORWARD
mapping (high score → high future return), and the brief's "long the bottom-tercile / low-score"
construction therefore longs predicted future losers.

The dominant failure mode is **turnover-cost drag**, not the sign inversion alone. IS total fees
(0.69) are 8.8× the IS gross PnL magnitude (0.078). Even with positions flipped, the flipped
net IS Sharpe is still −0.43. The 8h-rebalance cadence at 0.1% per-side fee is incompatible with
an OOS rank-IC of +0.043 — the signal is too weak to overcome that friction. Both the sign issue
and the turnover cost must be addressed in any follow-on iteration.
