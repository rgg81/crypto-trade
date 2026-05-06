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
| iter-v3/011 | 2026-05-06 | Risk-gate → z-score OOD 2.5 → 2.0 (tighter) | IS Sharpe Δ +0.39 (vs iter-v3/010 +0.5683) | +1.6251 | EXPLORATION-PROMISING (lottery/concentration caveats) | YES — strong IS lift broad-based, but flag LDO 86% concentration for CONFIRMATION QR |

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

## Caveats — iter-v3/011 EXPLORATION-PROMISING (with lottery/concentration caveats) flags

The +1.6251 OOS Sharpe and +0.9566 IS Sharpe in iter-v3/011 are the second-highest OOS and **highest IS** in v3 track history. The IS axis is broad-based 286 trades (NOT lottery-driven) but the OOS axis carries an LDO 86.31% lottery concentration. Verdict is PROMISING-with-caveats because the falsifier-grade IS axis cleared with substantial margin (+0.56 above the +0.40 PROMISING threshold) on a broad-based sample, while the OOS lottery-flag is informational only under EXPLORATION. The five caveats below are catalogued for audit-trail discipline so the future CONFIRMATION-bundling QR inherits the rule set without re-deriving any of them under post-hoc pressure:

- **Gate-orthogonal MKR** (4th consecutive OOS-negative; threshold compressed 6-7 → 5; next negative = mandatory per-symbol-diagnostic axis): MKR -25.75% OOS net PnL at 25.0% WR — both worst-yet in the trajectory (-6.5% → -13.1% → -10.6% → -25.75%; WR 33.3% → 30.8% → 29.4% → 25.0%). Tighter z-gate INCREASED MKR kill-rate by ~15pp (35.0% → 49.8% — the LARGEST of any symbol) yet WORSENED per-trade economics. **MKR pattern is gate-orthogonal**: tightening doesn't fix it. Per Critic FINAL Recommendation 3, the per-symbol-exclusion threshold is compressed from 6-7 (per iter-v3/010) → 5 consecutive negatives. If iter-v3/012+ records MKR's 5th consecutive negative, the NEXT EXPLORATION must be a per-symbol-diagnostic axis (e.g., drop-MKR universe-change exploration as single axis). Pre-committed via new memory rule `feedback_mkr_threshold_compression.md` to prevent post-hoc rationalization. Rule cannot be renegotiated post-hoc by future Engineer or QR.
- **LDO 86.31% OOS concentration (lottery-flag)**: 10 trades, 8 wins (80% WR), exact-binomial 95% CI **[44.4%, 97.5%]** — CI width too wide to claim signal-from-noise distinction; the 80% WR is consistent with a lucky 10-flip sequence within 95% confidence. Without LDO's 8 wins, OOS Sharpe collapses materially. Future CONFIRMATION QR must scope ex-LDO basket fragility before bundling iter-v3/011 risk-gate component.
- **IS broad-based confirmation** (286 trades, 36.4% WR, +0.96 Sharpe — NOT lottery-driven): IS axis attribution is BCH 100 trades / +86.82% PnL + LDO 21 / +52.90% + TRX 88 / -19.96% + MKR 77 / -23.21%. 121 of 286 IS trades (42%) on the two positive-PnL symbols. The IS-axis broad-based-ness is what justifies the PROMISING verdict alongside the OOS lottery-flag — it forecloses any "the entire iteration is lottery-driven" reading.
- **Floor-recoverable bundle math**: iter-v3/011 single-seed = 101 OOS trades; predicted bundle at CONFIRMATION = 5 outer seeds × 3-4× ensemble = **303-404 OOS bundle trades** (well above the 130-trade floor with margin). Factor 3-4× **inherited from iter-v3/010 review, UNVERIFIED at iter-v3/011's tighter gate setting** — the gate may shift the multiplication factor. A future CONFIRMATION QR must validate the multiplier empirically before claiming the floor clears at bundle level.
- **Data-regen audit note**: First launch failed staleness check (19.6h > 16h threshold per `feedback_data_staleness_per_worktree`); re-fetched 2 klines × 5 symbols + regenerated features (~3 min of the 8 min wall-clock). 0.5% data-extent drift on a 13.5-month OOS window is **NOT attributed to the −0.187 OOS Sharpe metric delta vs iter-v3/010** — gate-axis kill-rate shifts (+15-18pp across all 4 symbols) are the dominant driver. Per-spec staleness guard functioning correctly. Audit-noted but not a methodology issue.

The five caveats above are NOT disqualifying for catalog inclusion. iter-v3/011 IS a strong candidate for next CONFIRMATION bundling, conditional on the future bundling QR addressing the LDO lottery-flag and ex-LDO basket fragility explicitly.

---

## Last CONFIRMATION

(none — iter-v3/008 was aborted at 4h 15min on 2026-05-06; the cadence discipline was established AFTER that abort)

## Count of EXPLORATIONS since last CONFIRMATION

**4** of **10 required**. iter-v3/012 onwards needs **6 more EXPLORATIONS** before any CONFIRMATION can launch.

Axis coverage after iter-v3/011: **features × 2** (007, 009), **labeling × 1** (010), **gate × 1** (011). Per Critic FINAL Recommendation 1 (iter-v3/011 review.md SHA `b9ebbb2`), iter-v3/012 should test ANOTHER non-features-non-labeling-non-gate-zscore axis. Suggested: **BTC trend filter band ±20% (currently) → ±15% (stricter) or ±25% (looser)** as single-axis variation. After iter-v3/012 the catalog will have axis coverage features × 2, labeling × 1, gate-zscore × 1, gate-btc-trend × 1 — substantially diverse for the eventual CONFIRMATION bundle. Alternative axes: ADX threshold (currently 20), low-vol filter floor (0.33), or vol-scaling clip range ([0.3, 1.0]).
