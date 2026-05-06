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

---

## Last CONFIRMATION

(none — iter-v3/008 was aborted at 4h 15min on 2026-05-06; the cadence discipline was established AFTER that abort)

## Count of EXPLORATIONS since last CONFIRMATION

**1** of **10 required**. iter-v3/008 onwards needs **9 more EXPLORATIONS** before any CONFIRMATION can launch.
