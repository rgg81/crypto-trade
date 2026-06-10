# iter-v1/087 — Phase 8 Diary (BNBUSDT SPECIALIST + FAIL-FAST mechanism)

**Date**: 2026-06-10
**Track**: v1 (refactored)
**Branch**: `iteration-v1/087`
**TYPE**: SPECIALIST — BNBUSDT single-coin cohort (un-reserved); STOCK 48-col stack, NO new features. ALSO: first implementation + first production firing of the in-backtest **FAIL-FAST** mechanism.
**Cycle**: 7, universe expansion + infra
**Author**: QR (autopilot)
**Tag**: `v0.v1-087`

---

## Headline

**BLOCKED-FAIL-FAST — the new fail-fast mechanism fired on its first production run. BNB's first 2.0 years of IS walk-forward lost money (cumulative weighted_pnl −9.6937, net −32.82%, IS Sharpe ≈ −1.06 over 155 trades), so the backtest blocked it and aborted at ~3.1h (vs ~6-8h full), saving ~3-5h of compute.**

This iteration delivered the user's 2026-06-10 directive: retire the side-script GATE-2 probes; build a fail-fast INTO the real backtest ("if the coin doesn't have positive result in the first two years, we block it; the backtest is the proof"); and un-reserve BNB ("a very popular coin" must be testable). The mechanism worked exactly as designed — opt-in (default OFF), fired once at the 2-year IS checkpoint, clean exit (code 0), wrote `fail_fast_report.csv`.

---

## Result (fail_fast_report.csv)

| Metric | Value |
|---|---:|
| verdict | **BLOCKED-FAIL-FAST** |
| first-2.0yr IS cumulative weighted_pnl | **−9.6937** (≤ 0 → block) |
| first-2.0yr IS net PnL | −32.82% |
| first-2.0yr IS Sharpe (approx) | −1.0555 |
| IS trades in the 2.0yr window | 155 |
| window | first 733 days from the first IS test trade |
| wall-clock to abort | 11,267s (~3.1h) vs ~6-8h full |

No full IS/OOS reports (aborted before the reporting stage — that is the point of fail-fast).

---

## Decision: BLOCKED-FAIL-FAST — NO MERGE

- The BNB stock-48-col specialist is BLOCKED (first 2 years not positive). Not a bundle candidate.
- **BNB remains UN-RESERVED** (dropped from V1_EXCLUDED_SYMBOLS) — it is a first-class v1 symbol now and can be re-mined later with different features / risk / labeling. The block is on THIS config, not the symbol.
- **BUNDLE-002 (`v0.v1-082`; DOT+ETH+BTC+AAVE) UNCHANGED.**

---

## Methodology: fail-fast mechanism validated in production

The fail-fast (commit `6eada415`, Critic 6.0 PASS `bfc15fa9`) is now proven:
- **Opt-in, default OFF** (`fail_fast_is_years: float | None = None`) — foundation + all prior iterations byte-unchanged (Critic 6.0 verified the hot-loop is fully gated; embargo `walk_forward.py:113` untouched).
- **No look-ahead** — sums ONLY IS test trades (close_time < OOS_CUTOFF) over the first 2.0yr (730d) from the first IS test trade; purely post-hoc early TERMINATION (emitted trades byte-identical to the un-terminated prefix).
- **Semantics**: cumulative IS weighted_pnl ≤ 0 at the 2-year checkpoint → BLOCKED-FAIL-FAST + clean exit; > 0 → run to completion.
- **First firing**: BNB, −9.69 over 2yr → blocked, ~3-5h saved. Not a spurious/borderline abort — a clear, large structural negative (155 real trades, −32.82% net).

This REPLACES the retired side-script GATE-2 probe ([[feedback_v1_backtest_fail_fast]]). The backtest is the proof; the diversification/trivial-baseline analysis is informational only (BNB's GATE 0 corr 0.676 + GATE 1 trivial +0.0755 did NOT block it — the real backtest did).

---

## Next Iteration Ideas (per user "alternate" + universe directives)

1. **XRPUSDT specialist (/088)** — the second universe-expansion symbol (user Option-3: into v1, cross-track v2 overlap accepted). Run with fail-fast=2.0 (cheap downside — aborts early if first-2yr negative). Carries the XRP double-exposure flag at any future bundle/deploy step.
2. **Machinery axes (alternate)** — W-DECAY (time-decay sample weighting — directly removes the short-window noise-exploitation channel the /086 LM post-mortem found), R5-LWG (listing-window-guard primitive), R-CONV (ensemble-conviction trade gate). Bundle-wide, lift existing seats.
3. Re-mine BNB later with a NEW feature family or risk primitive (it's un-reserved; the stock-stack config is blocked, not the symbol).

---

## Catalog

iter-v1/087 → `per-cohort-specialization-BNB` + fail-fast infra | BLOCKED-FAIL-FAST | first-2.0yr IS weighted_pnl −9.69 / net −32.82% / Sharpe −1.06 (155 trades) | fail-fast fired (first production firing; ~3-5h saved) | BNB un-reserved (re-mineable) | BUNDLE-002 unchanged. Tag `v0.v1-087`.
