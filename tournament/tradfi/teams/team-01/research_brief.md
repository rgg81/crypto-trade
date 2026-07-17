# team-01 research brief — t01-residual-momentum-v1 (FINAL SPEC, frozen for QE)

Family (approved in registry.jsonl): **residual (beta-stripped) momentum**.
This brief is the complete, unambiguous specification. The QE implements EXACTLY this in
`strategy.py` and makes NO research choices. Every parameter is fixed. Section 3 is the
normative pipeline; `scratch_common.py::build()` with the exp-013 config is the working
reference implementation the output must match.

## 1. Mechanism & economic rationale

Underreaction to firm-specific news persists after stripping the market and sector return
components. Raw momentum's tail risk comes from time-varying systematic exposure (beta
crashes when the market whipsaws), not from the stock-specific signal. Ranking names on
idiosyncratic (market- and sector-residual) trailing returns keeps the behavioral
underreaction premium while removing the crash channel — the right construction for a
capped, vol-targeted, net-capped book of ~65 single-stock perps.

IS evidence for the mechanism (evaluator, monthly √12 Sharpe, 1× cost):
raw 12-1 momentum bear-regime Sharpe **−1.27** → market-residual **−0.48** → market+sector
residual **−0.06..−0.24** (scaling-dependent), at comparable overall Sharpe. The
residualization does exactly what the family thesis claims.

## 2. Final parameters (all FIXED)

| Parameter | Value | Provenance |
|---|---|---|
| Residualization | market, then sector (self-excluded) | exp-007: +0.02 Sharpe, bear −0.48→−0.06 |
| Beta/gamma window `B` | 63 trading days, min_periods=63 | exp-006: monotone 63>126>252; substrate-canonical |
| Formation `form` | 252 trading days | exp-005: flat plateau, 252 best edge; canonical 12-1 |
| Skip `skip` | 21 trading days | exp-005: skip 10 vs 21 inside noise; canonical reversal-zone skip |
| Momentum window `L` | form − skip = 231 | derived |
| Rolling min_periods `mp` | round(0.9 × 231) = **208** | exp-012: 0.8/0.9/1.0 spread 0.028 = robust |
| Scaling | **blend**: 50/50 pct-rank(IR) + pct-rank(sum) | exp-008/009; decision note in exp-010 ledger line |
| Cross-section | rank → dollar-neutral (demean) | exp-011: quantile books non-monotone = noise peak |
| Smoothing | EMA halflife **10**, min_periods=1, on 0-filled weights | exp-010: hl 5–10 plateau, 10 = centroid |
| Randomness | none (aux['seed'] unused) | deterministic by construction |

## 3. Normative pipeline (exact order; pandas semantics as stated)

Inputs: `pn` dict of dates×tickers DataFrames `{'open','high','low','close','volume'}`;
`aux = {'vix', 'sector_map', 'seed'}`. Use ONLY `pn['close']` and `aux['sector_map']`.
Tickers = `pn['close'].columns` at runtime (never hard-coded). No file reads, no network,
no subprocesses. Allowed imports: numpy, pandas, stdlib-math, and `neutralize`
(approved substrate; use `dollar_neutralize`).

1. **Returns**: `ret = close / close.shift(1) - 1` (simple daily; NaN propagates).
2. **EW market**: `mkt = ret.mean(axis=1)` (pandas skipna row mean over listed names).
3. **Market residual**: per column c:
   `beta_c = ret[c].rolling(63, min_periods=63).cov(mkt) / mkt.rolling(63, min_periods=63).var()`
   then `e = ret - beta.mul(mkt, axis=0)`. (No alpha subtraction — idiosyncratic drift IS
   the signal. Windows end at the current bar: past-only, engine applies the decision lag.)
4. **Sector residual**: group columns by `aux['sector_map']` (missing ticker → its own
   "Unknown" bucket handling is inherited from aux; buckets with <3 member columns are
   left untouched). For each sector block `block = e[cols]` (the ORIGINAL market-residual
   block — members are processed independently, not sequentially):
   - `n = block.notna().sum(axis=1)`; `s_sum = block.sum(axis=1)` (skipna),
   - per member c: `n_ex = (n - block[c].notna().astype(int)).replace(0, NaN)`;
     `s_ex = (s_sum - block[c].fillna(0.0)) / n_ex`,
   - `g = block[c].rolling(63, min_periods=63).cov(s_ex) / s_ex.rolling(63, min_periods=63).var()`,
   - `e2[c] = block[c] - g * s_ex`.
   Fallback everywhere: `e2 = e2.where(e2.notna(), e)` (sector stage undefined → keep
   market-only residual).
5. **Momentum** (L=231, mp=208, windows shifted past the reversal zone):
   - `S = e2.rolling(231, min_periods=208).sum().shift(21)`
   - `V = e2.rolling(231, min_periods=208).std().shift(21)` (pandas default ddof=1)
   - `m_ir = S / (V * sqrt(231))`; `m_sum = S`.
6. **Blend**: `mom = 0.5 * m_ir.rank(axis=1, pct=True) + 0.5 * m_sum.rank(axis=1, pct=True)`
   (pandas rank: method='average', ascending, pct=True; NaN stays NaN).
7. **Cross-sectional weights**: `r = mom.rank(axis=1, pct=True)`;
   `w = dollar_neutralize(r)` (subtract row mean over non-NaN — net-zero book; NaN = flat).
8. **Smoothing**: `w = w.fillna(0.0).ewm(halflife=10, min_periods=1).mean()`.
9. **Return `w`** — raw signed weights on the full panel grid. The engine owns
   gross-normalisation, |w_i|≤0.10, |net|≤0.25, shift(1), costs, vol-targeting.

Missing data / ragged starts: handled entirely by NaN propagation + min_periods — a name
becomes eligible ≈ 63+231 trading days after listing; before that it is flat (0 after the
fillna in step 8). Delisted/gap days: NaN returns propagate NaN into rolling windows until
min_periods is again satisfied; no forward-fill anywhere.

Leak-safety notes for the harness: every operator is causal (rolling windows end at t,
ewm is forward-recursive, ranks/means are row-wise). Truncated-replay equivalence holds
because the panel head is frozen and nothing looks forward. Future-bar corruption cannot
reach weights at ≤ t.

## 4. Expected IS metrics (evaluator `te.run_is`, exp-013; QE must reproduce via team-run)

| Metric | 1× cost | 2× cost |
|---|---|---|
| Net Sharpe (monthly, √12) | **+0.455** | **+0.418** |
| Max drawdown | −0.283 | −0.288 |
| Ann. turnover (gross) | 4.03 | 4.03 |
| Total return | +1.205 | +1.041 |
| Months | 174 | 174 |
| Regime Sharpe bull / bear / chop | +0.44 / −0.24 / +0.73 | +0.41 / −0.29 / +0.70 |
| Median names long / short | 24 / 24 | 24 / 24 |
| Mean gross / net | 1.0 / ~0 | 1.0 / ~0 |

Breadth floor (≥5/side): passed ~5× over. Cost robustness: 1×→2× Sharpe Δ = 0.037.

## 5. Falsifier status (pre-registered at registration)

- "Net Sharpe @1× ≤ 0 across the plateau" — NOT triggered (+0.28..+0.48 everywhere tested).
- "Edge exists only in raw momentum form" — NOT triggered: residual variants match raw
  Sharpe within noise (0.455 vs 0.485) with the bear channel collapsed (−0.24 vs −1.27).
- "Breadth floor forces cost-fatal turnover" — NOT triggered (24/24 at 4×/yr).

## 6. Expected regime behavior (for the record, per registration)

Bull: modest positive (+0.44 IS). Bear: near-flat, mildly negative (−0.24 IS) — the
family's improvement axis vs raw momentum. Chop: strongest (+0.73 IS). No holdout
inference of any kind is made.

## 7. Experiment ledger summary

reg-001 + exp-002 (EDA) + exp-003..exp-013 (11 material batches) = 13 lines, ≤40 budget.
Decision notes for judgment calls (blend adoption, plateau centroids) are recorded inside
the ledger lines of the experiment FOLLOWING the read (exp-010, exp-011, exp-012, exp-013).
