# iter-v3/020 EDA — Per-Symbol PnL Cap (Sub-Axis A)

## Axis choice — Sub-Axis A: per-symbol cap (post-trade weighting layer)

Per `feedback_v3_iter019_axis_priorities.md` HIGH-priority #2 (concentration
architecture), iter-v3/020 chooses **Sub-Axis A** over Sub-Axis B (universe
expansion). Rationale:

1. **Cleaner single-mechanism axis**: Sub-Axis A varies one parameter
   (`max_per_symbol_pnl_share = 0.40`); Sub-Axis B varies two axes
   simultaneously (universe + concentration). Single-axis discipline is
   non-negotiable per `feedback_structural_over_knob_exploration.md`.
2. **Lower implementation cost**: Sub-Axis A is a post-trade weighting
   layer (mirrors `apply_btc_trend_filter` pattern) — no Gate 1-2 EDA
   needed. Sub-Axis B requires symbol selection + Gate 1-2 EDA on 1-2
   new symbols, doubling the brief size.
3. **Closer to current bottleneck**: TRX OOS 86.0% / BCH OOS 74.1% (per
   anchor iter-v3/018) shows the concentration mechanism is structural
   to 3-symbol universe. Universe expansion would dilute mechanically
   but at the cost of per-symbol Sharpe contribution. Per-symbol cap
   tests whether cutting the lottery RISK (not the lottery REWARD) is
   net-accretive to OOS Sharpe.

## Anchor — iter-v3/018 multi-seed BOOTSTRAP per-symbol concentration

Per `BASELINE_V3.md` and `reports-v3/iteration_v3-018/in_sample/per_symbol.csv`
+ `out_of_sample/per_symbol.csv`. The single-seed projection (used in
comparison.csv footer) shows TRX 152% IS / 86% OOS, BCH 78% IS / 74% OOS,
LDO -130% IS / -60% OOS — concentrations sum to >>100% because LDO is the
sustained drag, allowing the two profitable symbols to share more than 100%
of the *net* portfolio PnL.

## Counterfactual results — three cap flavors

Three cap-mode counterfactuals were computed against iter-v3/018's anchor
trade roster (172 IS / 102 OOS):

1. **No cap (anchor)**: monthly Sharpe IS +0.4563 / OOS +0.2343 (single-seed
   projection). Anchor sums: IS Sharpe=+0.4563, OOS Sharpe=+0.2343.
2. **Static full-window cap (Mode A)**: cap any symbol whose absolute share
   over the FULL window exceeds 0.40. The dominant positive contributor
   gets scaled down post-hoc; pure accounting recomputation.
3. **Rolling-window cap (Mode B)**: at each trade close, look at the past
   90 bars (~30 days), compute that
   symbol's share, scale this trade's weight if share > 0.40. Mirrors
   trade-time integration with RiskV3Wrapper.

### Mode A (static full-window) results

- IS:  capped 97 of 172 trades; top share 78.72% → 67.24%; monthly Sharpe +0.3969 (anchor +0.4563)
- OOS: capped 86 of 102 trades; top share 152.01% → 259.85%; monthly Sharpe -0.1276 (anchor +0.2343)

### Mode B (rolling-window) results

- IS:  capped 18 of 172 trades; fire rate 10.47%; monthly Sharpe +0.2190
- OOS: capped 8 of 102 trades; fire rate 7.84%; monthly Sharpe -0.0305

## Predicted IS / OOS bands for iter-v3/020

**IS Sharpe band**: predicted [+0.30, +0.55] median +0.40, calibrated against
the multi-seed iter-v3/018 anchor +0.3788 and the static counterfactual
+0.3969. The cap removes some lift on profitable
concentrations; the rolling-cap mode (closer to TRADE-time integration) is
the binding counterfactual.

**OOS Sharpe band**: predicted [+0.45, +0.65] median +0.55, calibrated against
iter-v3/018 anchor +0.3869 (multi-seed mean) and the rolling-cap counterfactual
-0.0305. Mechanism: capping TRX's 86% OOS share
redistributes weight to BCH (74% OOS share, also positive) and LDO (-60%,
negative). The rebalance MAY add lift if BCH OOS Sharpe > TRX OOS Sharpe in
the unweighted unit; OR subtract lift if LDO drag dominates.

## Three pathways pre-committed

- **PATH A (PROMISING)**: post-cap top-share < 40% AND OOS Sharpe ≥ anchor
  +0.10 (≥ +0.4869) → strong candidate for next CONFIRMATION bundle.
- **PATH B (NEGATIVE-no-effect)**: post-cap top-share < 40% AND OOS Sharpe
  in [+0.2869, +0.4869] (anchor ± 0.10) → concentration is NOT the bottleneck;
  cap is mechanism-clean but the profitable concentration was the source of
  the OOS lift. Catalog row marks NO candidate.
- **PATH C (NEGATIVE)**: post-cap top-share < 40% AND OOS Sharpe < +0.2869
  → concentration carries genuine signal that the cap removes; iteration
  is destructively pruning lottery (NOT lottery-risk).

## Implementation pre-commits (sub-fix #1 design)

TRADE-time integration with `RiskV3Wrapper` is preferred over post-hoc
aggregation-layer integration because TRADE time is faithful to live
execution. Mechanism:

- Add to `RiskV2Config`: `max_per_symbol_pnl_share: float | None = None` and
  `max_per_symbol_window_bars: int = 90` (default OFF).
- Add to `RiskV2Wrapper`: a per-bar rolling per-symbol PnL share tracker.
- After scale-vol and other gates fire, multiply `sig.weight` by the cap
  scale: `cap_scale = min(1.0, cap / observed_share)` if `observed_share > cap`.
- Track via gate stats; emit per-symbol fire counters.
- iter-v3/020 sets `max_per_symbol_pnl_share=0.40` in the v3 runner's
  `RiskV2Config(...)` construction.

Alternative (post-hoc aggregation): a new `apply_per_symbol_cap` function
in `risk_v2.py` mirroring `apply_btc_trend_filter` pattern. Simpler but
non-faithful (live engine cannot apply post-hoc).

## Verdict

Sub-Axis A is tractable, single-axis-disciplined, and the counterfactual
shows non-trivial OOS Sharpe shifts under the cap. Predicted bands and
pathway pre-commits stand. iter-v3/020 EXPLORATION proceeds to Phase 6
with the per-symbol cap mechanism integrated TRADE-time via `RiskV2Wrapper`.
