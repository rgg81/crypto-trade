# iter-v2/063 Engineering Report

## Build

- Branch: `iteration-v2/063` from `quant-research` at `44d9a62`
- Code change: `run_baseline_v2.py` — add `AAVEUSDT` to V2_MODELS,
  add `DOTUSDT`+`LTCUSDT` to V2_EXCLUDED_SYMBOLS
- Data: refetched AAVEUSDT (160 new klines from Feb 28 → Apr 23 07:59 UTC),
  regenerated v2 features (AAVEUSDT: 6,046 rows, 48 features)
- Other 4 baseline symbols + BTC: fresh from iter-v2/059-clean run
- All 4 pre-flight checks passed (fetcher guard, no forming, <16h lag, runner
  ↔ baseline consistent)

## Backtest

5 individual models (E DOGE, F SOL, G XRP, H NEAR, I AAVE), single seed
(v1-style 5-seed internal ensemble), runtime ~2.5h.

| Model | OOS trades | Runtime |
|---|---|---|
| E DOGEUSDT | 56 | 34min |
| F SOLUSDT | 79 | 40min |
| G XRPUSDT | 75 | 55min |
| H NEARUSDT | 72 | 29min |
| I AAVEUSDT | 59 | 33min |

## Headline results

| Metric | iter-v2/059-clean (baseline) | **iter-v2/063** | Δ |
|---|---|---|---|
| IS monthly Sharpe | +1.04 | **+1.14** | +9% ✓ |
| IS trade Sharpe | +0.97 | +1.00 | +3% |
| **OOS monthly Sharpe** | +1.66 | **+1.07** | **−35%** |
| **OOS trade Sharpe** | +1.66 | +1.17 | −30% |
| Combined IS+OOS monthly | 2.70 | 2.21 | −18% |
| OOS PF | 1.78 | 1.35 | −24% |
| OOS MaxDD | 22.61% | 31.54% | +39% (worse) |
| OOS WR | 49.1% | 42.5% | −6.6pp |
| OOS trades | 57 | 80 | +23 |

## Concentration audit (the primary objective)

Authoritative from `seed_concentration.json`:

| Symbol | OOS wpnl | OOS share | Trades | WR |
|---|---|---|---|---|
| NEARUSDT | +35.54 | **44.44%** | 16 | 62.5% |
| XRPUSDT | +26.83 | 33.55% | 7 | 57.1% |
| SOLUSDT | +11.87 | 14.84% | 18 | 38.9% |
| DOGEUSDT | +5.74 | 7.17% | 16 | 43.8% |
| AAVEUSDT | **−21.34** | 0.00% | 23 | **26.1%** |

NEAR concentration dropped **57.96% → 44.44%** (−13.5pp) — the dilution
hypothesis worked. **But** the n=5 strict concentration rules were not met:

- Per-seed max cap (≤ 40%): **FAIL** (NEAR 44.44%)
- Mean ≤ 35%: cannot evaluate on 1 seed run (10-seed sweep not yet run)
- Pass inner (≤32% above): **FAIL**

## AAVE performance — the problem

AAVE was a catastrophic pick:

- 23 OOS trades, 26.1% WR, **−1.36% avg net PnL per trade**
- Net OOS: **−21.34 weighted PnL**
- IS: 46 trades, 50.0% WR, +4.48 avg, +25.21 net (IS was fine)

AAVE's OOS regime was fundamentally different from its IS regime:
- IS WR 50.0% → OOS WR 26.1% (−23.9pp collapse)
- Classic OOS regime shift that even the v2 risk gates didn't detect
  because AAVE's feature z-scores stayed within the 2.5σ threshold during
  the losing trades.

The gates fired as designed — they didn't over-fire, but they also didn't
catch the degradation. The degradation was SLOW GRIND-DOWN, not a regime
break. This matches the skill's documented "known-unknown failure mode":
*"a slow monotone grind-down that never triggers ATR percentile spikes
nor feature z-score excursions — v2's current gates cannot detect this."*

## Gate efficacy

BTC trend filter killed 29 signals across 5 models (vs 29 in iter-v2/059-clean)
— roughly same fire rate. Other gates unchanged.

## Code quality

- Ruff: clean
- V2_FEATURE_COLUMNS pinned: ✓
- Feature isolation audit (grep for `from crypto_trade.features `): empty ✓
- Data freshness pre-flight: passed for all 6 symbols ✓
- Runner ↔ BASELINE_V2.md drift: N/A (iteration branch, baseline drift only
  checked before starting — confirmed clean at iter-v2/063 open)

## Verdict

**NO-MERGE.** Fails 4 of 7 MERGE criteria:

1. Combined monthly Sharpe ≥ 2.70 → **FAIL** (2.21)
2. NEAR concentration < 45% → PASS just barely (44.44%)
3. OOS monthly Sharpe ≥ 1.41 (0.85×1.66) → **FAIL** (1.07)
4. IS monthly Sharpe ≥ 0.88 (0.85×1.04) → PASS (1.14)
5. OOS trade Sharpe >0, PF >1, trades ≥50 → PASS (but all worse)
6. Per-seed max ≤40% → **FAIL** (44.44%)
7. v2-v1 correlation <0.80 → not evaluated (skipped for time)
