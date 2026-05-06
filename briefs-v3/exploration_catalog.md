# v3 EXPLORATION Catalog

Running ledger of EXPLORATION iterations. Each EXPLORATION's Phase 8 diary appends one row here. The next CONFIRMATION QR reads this to bundle the best variations.

**Schema**: `iter-v3/NNN | YYYY-MM-DD | axis varied | IS Sharpe Δ | OOS Sharpe (informational) | verdict | confirmation candidate?`

**Constraints**:
- CONFIRMATION cannot launch with fewer than 10 EXPLORATION rows since the last CONFIRMATION
- Only CONFIRMATION-MERGE updates BASELINE_V3.md
- No calendar/daily limit — 10:1 ratio is the only cadence constraint

---

## Catalog (newest at bottom)

| iter-v3/NNN | Date | Axis varied | IS Sharpe Δ | OOS Sharpe | Verdict | Confirmation candidate? |
| ----------- | ---- | ----------- | ----------- | ---------- | ------- | ----------------------- |
| iter-v3/007 | 2026-05-06 | Features → top-14 by importance (drop bottom-20) | +0.2987 (vs iter-v3/003 baseline -0.0746) | +0.0622 (single-seed) | EXPLORATION-PROMISING | YES — top-14 minus vwap_dev_50 redundancy → top-13 candidate |
| iter-v3/009 | 2026-05-06 | Features → top-13 (drop vwap_dev_50) | IS Sharpe Δ -0.144 (vs iter-v3/007 +0.2241) | +1.1223 (INFORMATIONAL — see caveats below) | EXPLORATION-NEGATIVE | NO — Falsifier 1 activated; OOS lift is LDO-concentrated 12-trade lottery; N=87 OOS < 130 floor |

---

## Caveats — iter-v3/009 INFORMATIONAL OOS flags

The +1.1223 OOS Sharpe in iter-v3/009 must NOT be read as evidence of edge by any future CONFIRMATION-bundling QR. The following caveats are catalogued for audit-trail discipline (`feedback_trade_rate_floor` operative across iterations):

- **OOS_concentration = 98.61%** (LDO-driven). LDOUSDT contributed +70.77% weighted_pnl out of +53.22% total OOS PnL — the other three symbols sum to -17.5% across 75 trades.
- **LDO 12 trades, 75% WR, exact-binomial 95% CI [42.8%, 94.5%]**. CI width is too wide to claim signal; the 75% WR is consistent with a lucky 12-flip sequence on a fair coin within 95% confidence.
- **MKR_OOS regression**: iter-v3/007's MKR weighted_pnl was -6.5% on the matching window-equivalent → iter-v3/009's MKR is -13.1% on a comparable trade count, arguing against any "redundancy drop helps" reading at the per-symbol level.
- **OOS_trades = 87 < 130 trade-rate floor** (`feedback_trade_rate_floor`). Sharpe from <130 trades is structurally underpowered (`σ_SR ≈ √(1/T)` makes the t-test unreliable below this floor).
- **DSR = 0.0, PSR = 1.0**: single-seed exploration artifact (DSR collapses, PSR saturates at N=1). NOT evidence of edge significance.

The +1.12 OOS Sharpe is the highest in v3 track history, but the four caveats above mean it is NOT eligible for downstream bundling without independent multi-seed validation that explicitly pre-registers an OOS-axis falsifier.

---

## Last CONFIRMATION

(none — iter-v3/008 was aborted at 4h 15min on 2026-05-06; the cadence discipline was established AFTER that abort)

## Count of EXPLORATIONS since last CONFIRMATION

**2** of **10 required**. iter-v3/010 onwards needs **8 more EXPLORATIONS** before any CONFIRMATION can launch.

Per Critic FINAL Recommendation 1 (iter-v3/009 review.md SHA `1bc828f`), iter-v3/010 should vary along a NON-features axis (e.g., labeling parameters, risk-gate thresholds, BTC trend filter band) to maximize axis diversity for downstream CONFIRMATION bundling. Two consecutive features-axis EXPLORATION rows (iter-v3/007 top-14, iter-v3/009 top-13) leave the catalog under-diverse — the 10-EXPLORATION quota is a diversity requirement, not just a count requirement.
