# QR Response to Critic — iter-v3/009

## Clarifications

### Clarification 1 — Falsifier 1 disposition

QR endorses the **mechanical reading → EXPLORATION-NEGATIVE** with the OOS observation catalogued as INFORMATIONAL only. Falsifier 1 was pre-registered at IS<+0.10 and the observed IS=+0.0802 mechanically activates it — per the project memory "no cheating" rule, we never override pre-registered measurement criteria on un-pre-registered evidence (here, the OOS jump). This is the FIRST iteration testing the EXPLORATION/CONFIRMATION cadence rules, and overriding Falsifier 1 on OOS in the very first activation would erode pre-registration discipline for every future iteration; the catalog row is recorded as `EXPLORATION-NEGATIVE` with note `OOS=+1.12 informational, LDO-concentrated 75% WR on 12 trades, NOT a confirmation candidate without bootstrap validation`.

### Clarification 2 — LDO concentration interpretation

The OOS lift is **a 12-trade LDO lottery, not a robust 13-feature edge** — exact-binomial 95% CI on 75% WR with N=12 is [42.8%, 94.5%], too wide to claim signal, and 12 trades is well below the 130-OOS-trade floor. The "BCH dominated iter-v3/007 OOS / LDO dominated iter-v3/009 OOS" pattern is consistent with single-seed exploration being structurally concentration-fragile rather than evidence of any per-symbol edge — the dominant symbol changed but the 84%→98.61% concentration pattern persisted, and MKR got WORSE (-6.5%→-13.1%) which argues against a uniform "vwap_dev_50 was overfit-friendly" reading. Useful catalog data point: confirms exploration-mode IS noisy AND OOS concentration-prone, validating the cadence rule of bundling ≥10 explorations before any CONFIRMATION promotion.

### Clarification 3 — Stale docstring

ITER-V3/010 CLEANUP. Cosmetic-only — `_verify_feature_columns()` lineage attribution to iter-v3/008 is technically correct (the feature drop landed in setup commit `56b8f8b`), but the docstring should track the active brief, not the originating SHA. Add to a "process improvements" running list (parametrize docstring banner against active `ITERATION_LABEL`, same fix-pattern that was deferred from iter-v3/007 Clarification 4) and clean up in iter-v3/010's first commit; not blocking the v3-009 verdict.

### Clarification 4 — Sample-size caveat

YES, record the trade-rate-floor caveat. Catalog row will include `OOS_trades=87 (< 130 trade-rate floor; OOS metrics informational only)` to prevent future CONFIRMATION QRs from over-weighting the +1.12 OOS Sharpe when bundling exploration evidence. This is mechanically the project memory feedback rule (`feedback_trade_rate_floor`: ≥10 trades/month and ≥130 OOS total for trustworthy Sharpe) applied at catalog-write time — explicit caveat is the audit-trail mechanism that keeps the rule operative across iterations.

## Position

**STAND BY VERDICT** with request that Round 2 final verdict resolve to `EXPLORATION-NEGATIVE` with informational OOS notation.

QR accepts all of Critic's preliminary findings (Checks 1-12 PASS / WARN-carry-forward / WAIVED-single-seed) and asks Round 2 to honor the mechanical Falsifier 1 activation per Clarification 1 — the pre-registration discipline value of recording NEGATIVE on the FIRST falsifier-trip exceeds any informational gain from over-promoting an LDO-concentrated 12-trade OOS lottery to PROMISING.
