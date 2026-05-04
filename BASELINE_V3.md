# BASELINE_V3 — Crypto-Trade v3 Track

**Sibling to:** `BASELINE.md` (v1) and `BASELINE_V2.md` (v2). All three coexist.

**Last updated:** pre-iter-v3/001 (placeholder)

## Current Baseline

**TBD by iter-v3/001 — universe and metrics to be determined.**

There is NO virtual `iter-v3/000`. v3 starts genuinely fresh with iter-v3/001's brief, which selects the v3 symbol universe AND ships the methodology stack (CPCV, PBO, PSR, meta-labeling, ADF-tested fracdiff, Critic workflow).

After iter-v3/001 completes (assuming MERGE), this section will be populated with:

- Iteration ID and tag (`v0.v3-001`)
- Date merged
- Symbol universe (4 symbols selected from outside `V3_EXCLUDED_SYMBOLS`)
- IS metrics: monthly Sharpe, daily Sharpe, MaxDD, profit factor, win rate, n_trades, total PnL, monthly Calmar, weighted PnL total
- OOS metrics: same set
- IS/OOS ratios
- DSR, PBO, PSR (v3-mandatory)
- n_trials, n_effective_trials
- Per-symbol breakdown (weighted PnL, n_trades, concentration)
- Risk gate fire rates (vol scaling, ADX, Hurst, z-score OOD, BTC trend filter, plus any v3-specific gates)
- 10-seed pre-MERGE validation summary

## Sacred Constants

```
OOS_CUTOFF_DATE = 2025-03-24       # IMMUTABLE
training_months = 24                # IMMUTABLE
ensemble_seeds = [42, 123, 456, 789, 1001]   # 5-seed inner ensemble
```

Plus v3-specific hard thresholds:

```
DSR_threshold = 0.95     # Deflated Sharpe Ratio (probability true Sharpe > 0)
PBO_threshold = 0.40     # Probability of Backtest Overfitting (LOWER is better)
PSR_threshold = 0.95     # Probabilistic Sharpe Ratio
IC_threshold  = 0.70     # |IC_pearson| between feature families (LOWER is better)
ADF_threshold = 0.05     # ADF p-value (LOWER is better — rejects unit root)
```

Inherited project-level merge gates:

- IS monthly Sharpe > 1.0
- OOS monthly Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- ≥10 trades/month OOS, ≥130 OOS total trades
- Top symbol concentration ≤ 30% of OOS PnL (or explicit exception)
- 10-seed pre-MERGE validation: mean Sharpe > 0, ≥7/10 profitable

**Any single gate failure = NO-MERGE.**

## Forbidden Symbols (V3_EXCLUDED_SYMBOLS)

v3 cannot trade any symbol already traded by v1 or v2. The runner enforces this at startup:

```python
V3_EXCLUDED_SYMBOLS = (
    # v1 traded
    "BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT",
    # historical v1-v2 reservation
    "BNBUSDT",
    # v2 traded
    "SOLUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT",
)

assert set(cfg.symbols).isdisjoint(V3_EXCLUDED_SYMBOLS), \
    f"v3 cannot trade v1/v2 symbols: {set(cfg.symbols) & set(V3_EXCLUDED_SYMBOLS)}"
```

iter-v3/001's Phase 3 (Symbol Selection) produces Gate 1–2 evidence (data quality, futures availability, liquidity) for 4 candidate symbols from outside this exclusion list. Universe selection is part of iter-v3/001's scope.

## Dead Ideas

(Empty — populated as v3 iterations fail.)

When iterations fail and produce dead-paths lessons, they get cataloged here so future iterations don't retry without explicit new evidence. v2's dead-paths catalog (in `BASELINE_V2.md`) inspires the format. Examples to expect over time:

- Symbol failures: "[SYMBOL] — OOS [metric], iter-v3/NNN, see diary"
- Feature additions failing IC threshold
- Gate configurations failing Pareto check
- Architectural changes failing Critic Check 8 (hypothesis-implementation alignment)

## Measurement Discipline

(Inherited from `BASELINE_V2.md`.)

### Data Extent Rule

Every kline CSV in `data/<SYMBOL>/8h.csv` must have `close_time` within 16 hours of the measurement time. Stale data silently corrupts feature computations and label horizons. The Engineer's Phase 6 pre-flight check verifies this before running any backtest.

### Forming-Candle Filter

`fetcher.py` filter: `if k.close_time < now_ms` drops forming candles. iter-v2/059 lost 50 days of OOS data due to a forming-candle bug; the v3 fix is non-negotiable.

### Re-Fetch Protocol

If freshness check fails, the Engineer re-fetches the affected symbols via:

```bash
uv run crypto-trade fetch --interval 8h --symbols <comma-separated>
```

The re-fetch is documented in the engineering report, and the backtest is re-run from the fresh data.

### Reproducibility

Every iteration's engineering report stamps:
- Git commit SHA (must exist in `git rev-parse <SHA>`)
- Hardware (CPU model, RAM)
- Wall-clock time
- Library versions (per brief Section 9)

The Critic's Check 7 verifies reproducibility properties — explicit `feature_columns`, ensemble seeds literal, trade-row PnL spot-check.

## Relationship to v1 and v2

`BASELINE_V3` is independent of `BASELINE.md` (v1) and `BASELINE_V2.md` (v2). The three tracks evolve independently:

- v1 tagged at `v0.NNN` after MERGE
- v2 tagged at `v0.v2-NNN` after MERGE
- v3 tagged at `v0.v3-NNN` after MERGE

The combined-portfolio runner (future work) weights all three tracks. v3 is expected to contribute to combined-portfolio diversification because its symbol universe excludes v1+v2 traded symbols by hard rule.

## See Also

- `ITERATION_PLAN_8H_V3.md` — workflow doc for v3
- `.claude/commands/quant-iteration-v3.md` — the v3 skill
- `.claude/agents/quant-engineer.md` — Engineer subagent
- `.claude/agents/quant-critic.md` — Critic subagent
- `BASELINE_V2.md` — sibling baseline (v2)
- `BASELINE.md` — sibling baseline (v1)
