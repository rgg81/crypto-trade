# iter-v3/054 — Candidate axes ranking

**Source**: `analysis/iteration_v3-054/cycle4_axis_ranking_eda.py` (this script)

## Final pick

**A1: Per-symbol drawdown brake** (NEW risk primitive)

- Implementation cost: ~1.5h (RiskV2Config field + RiskV2Wrapper state machine + GateStats counter + 5 adversarial tests).
- Backtest wall-clock: ~1.25h (same as /053; no feature regen needed).
- Total: ~2.75h (split: QR EDA done; QE implementation ~1.5h; QR Phase 5.5 ~0.25h).

## EDA evidence basis

### A1 — LDO drag is structural, BCH+TRX healthy

From `/053` IS trade roster (in_sample/trades.csv, 180 trades):

| Symbol | N | Final wpnl | Max wpnl peak | Max drawdown norm |
|---|---:|---:|---:|---:|
| BCH | 86 | +56.46 | +60.51 | 0.07 |
| LDO |  9 | -16.09 | +3.78 | 5.26 |
| TRX | 85 | -18.27 |  +3.94 | 5.64 |

Wait — the absolute-peak normalization makes LDO and TRX look identical because both
barely peak. Use the RUNNING_PEAK with FINAL_PEAK_OF_BCH = 60.51 as the cross-symbol
normalizer to get a meaningful 'this symbol's drawdown in BCH-units' view.

**Conclusion**: LDO and TRX both have running-peak ~+3-4 absolute wpnl units and then
go strictly negative. Per-symbol drawdown brake at threshold 0.5-1.0 (in symbol-self
units) would skip ~50-80% of post-peak LDO trades AND ~50-80% of post-peak TRX trades.

**Refined threshold**: Use absolute weighted_pnl drawdown (NOT normalized) at 5.0 wpnl
units — captures LDO and TRX descent without over-firing on BCH's intra-trade swings.

### A2 — DSR variants at /053

Current V1: at n_eff=19, E[max_SR] ≈ 4.00; observed annualized 4.95 daily / 1.65 monthly.
DSR_v1 = norm.cdf(1.65 - 4.00) ≈ 0.0094. Clamps to 0.0 numerically.

V3 (cap n_eff at 5): E[max_SR] ≈ 2.32; DSR_v3 = norm.cdf(1.65 - 2.32) ≈ 0.252. Still below 0.95.

V4 (PSR-only): PSR = 1.0 at all iterations from /028 → PASS. But PSR doesn't capture
multiple-testing penalty.

**Conclusion**: A2 is genuine methodology improvement (DSR=0 mechanically inevitable at
current architecture), but it's DEFERRED. /054 axis = A1.

### A3 — CatBoost cost

Full impl 7-10h; spike only 1.5-2h. Fails 2h cap.

### A4 — Base-stack importance

/053 portfolio importance ranking shows `regime_momentum_signed_5d` at rank 15/15 (despite being the proven edge ingredient — Optuna draw at /053 prioritized hurst_drift_50_200). The marginal candidate is unclear without fresh orthogonality EDA.

## Behavioral effect predictor (A1)

Predicted behavioral effects at threshold = 5.0 absolute wpnl drawdown:
- LDO trades skipped: 6-9 of 9 IS trades (the late-IS losses), 11-14 of 16 OOS
- TRX trades skipped: 30-50 of 85 IS, 15-30 of 44 OOS
- BCH trades skipped: 0-5 of 86 IS (drawdown stays well under 5.0 wpnl), 0-3 of 36 OOS

Predicted aggregate IS Sharpe delta: +0.05 to +0.20 (LDO+TRX drag removal).
Predicted aggregate OOS Sharpe delta: -0.10 to +0.20 (TRX is OOS contributor at /053;
skipping its drawdown trades may also skip recovery trades).

**PATH probability distribution prediction**:
- PATH A (PROMISING-clean): 20% — IS Δ +0.05 to +0.20 AND OOS Δ ≥ -0.20 AND ratio in band
- PATH B (PROMISING-INERT): not applicable (no new feature)
- PATH C-clean (NEGATIVE-clean): 25% — TRX drawdown brake over-fires and removes recovery
- PATH C-suspicious: 15% — same Sharpe but ratio shifts out of band
- PATH D (NULL-RESULT): 35% — brake fires rarely; IS Δ in (-0.10, +0.05)
- PATH E (CPCV-INVARIANT NULL): 5% — unexpected; ~20% trade volume reduction SHOULD shift CPCV