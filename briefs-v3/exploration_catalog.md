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
| iter-v3/010 | 2026-05-06 | Labeling → ATR multipliers (2.9, 1.45) → (2.0, 1.0) | IS Sharpe Δ +0.488 (vs iter-v3/009 +0.0802) | +1.8122 | EXPLORATION-PROMISING | YES — strong candidate for next CONFIRMATION bundle |

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

## Caveats — iter-v3/010 EXPLORATION-PROMISING flags

The +1.8122 OOS Sharpe and +0.5683 IS Sharpe in iter-v3/010 are the highest in v3 track history. Unlike iter-v3/009, iter-v3/010's headline metrics co-direct (IS lift broad-based across 3 of 4 symbols) and ALL pre-registered falsifiers were NOT triggered, so the verdict is genuinely PROMISING. The following caveats are catalogued for audit-trail discipline so the future CONFIRMATION-bundling QR inherits the rule set without re-deriving any of them under post-hoc pressure:

- **Mechanism cited**: (c) tighter labels reduce label noise so features find real momentum more cleanly. NOT (a) "edge was always there but masked" (would predict neutral/worse PBO; actual PBO improved 0.1145 → 0.1077). NOT (b) regime-specific tuning (lift is broad-based, not symbol-specific).
- **MKR_OOS = -10.6%**: 3rd consecutive negative across iter-v3/007 (MKR -14.03%), iter-v3/009 (MKR -13.1%/-17.61%), iter-v3/010 (MKR -10.65%). Per QR Clarification 2 disposition: revisit at 6-7 consecutive negatives with a per-symbol-diagnostic EXPLORATION (drop MKR as a single-axis universe variation); until then, audit-trail-only.
- **n_high_pbo_cells = 5/175**: TRX/2025-10, TRX/2025-11, MKR/2024-10, MKR/2025-04, MKR/2025-07. Mean PBO aggregator dilutes these to a clean 0.1077; future CONFIRMATION QRs may use `(1 - max_per_cell_pbo)` for a more conservative weighting alongside or instead of `(1 - mean_pbo)`.
- **OOS_trade_rate = 8.07/month < 10/month floor** (`feedback_trade_rate_floor`): informational at EXPLORATION; **floor applies at the BUNDLE level at CONFIRMATION** per the new memory rule `feedback_trade_rate_floor_bundle_level` (added per Critic Rec #3, pre-committed in this catalog row before any CONFIRMATION outcome is known to prevent post-hoc rationalization).
- **OOS_concentration = 57.17%** (BCH-driven): above the 35% per-symbol cap that would apply at CONFIRMATION. Informational under EXPLORATION per brief Section 6.3 — the labeling change may shift concentration in either direction at higher seed counts.
- **Calibration miss**: IS Sharpe overshoots predicted [+0.10, +0.30] band (P4 at 50%) by +0.27 in the FAVORABLE direction. Combined with iter-v3/009's unfavorable undershoot (P4 at 60%, [+0.18, +0.28]; reality +0.0802), labeling-axis EXPLORATION priors should widen the PROMISING band to roughly [+0.05, +0.60] to capture the higher-than-expected variance under colsample=1.0 + n_trials=10.

The five caveats above are NOT disqualifying for catalog inclusion — they are explicit pre-commitments that travel with the catalog row to the future CONFIRMATION-bundling QR. iter-v3/010 IS a strong candidate for next CONFIRMATION bundling.

---

## Last CONFIRMATION

(none — iter-v3/008 was aborted at 4h 15min on 2026-05-06; the cadence discipline was established AFTER that abort)

## Count of EXPLORATIONS since last CONFIRMATION

**3** of **10 required**. iter-v3/011 onwards needs **7 more EXPLORATIONS** before any CONFIRMATION can launch.

Per Critic FINAL Recommendation 1 (iter-v3/010 review.md SHA `f6f4ef7`), iter-v3/011 should test ANOTHER non-features axis to maximize catalog axis diversity before CONFIRMATION bundling. Suggested: **risk-gate axis — z-score OOD threshold 2.5 → 2.0 (tighter) or 3.0 (looser)** as single-axis variation. After iter-v3/011 the catalog will have axis coverage of features × 2, labeling × 1, risk-gate × 1 — meaningful diversity for the eventual CONFIRMATION bundle.
