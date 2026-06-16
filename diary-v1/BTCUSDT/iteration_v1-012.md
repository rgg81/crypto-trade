# Diary — iter-v1/012 (BTCUSDT) — EXPLORATION — trend-scale de-lever sizing primitive

**Axis:** RE-designed regime-aware, vol-scaled, LONG-bias de-lever SIZING primitive on the iter-010
config (19-col HYBRID, fixed_horizon N=9 (3d), let-winners-run execution). trend_scale ∈ [0.25, 1.0]
driven by past-only 200-SMA-slope z (floor 0.25, z_lo −0.5, z_hi 0.0). Single-axis vs iter-010. K=5.

**Result:** IS Sharpe **+0.2464** / OOS **−1.6065** (vs iter-010 IS +0.3863 / OOS −1.4762). Trade set
IDENTICAL to iter-010 (sizing changes weight, not which trades fire). The de-lever made BOTH IS and
OOS Sharpe WORSE. Fire counter: IS fire-rate 0.5625 / avg long-mult 0.625; OOS fire-rate 0.396 /
avg long-mult 0.721. 5/5 seeds. **Verdict: NEGATIVE — the designed structural fix did not transfer.**

### Why the de-lever failed (decisive — the campaign-turning diagnosis)
A regime split of the OOS trades by BTC 200-SMA-slope regime overturns the iter-011 "real-in-bull /
dead-in-bear" hypothesis:

| regime | IS LONG net (WR) | OOS LONG net (WR) |
|---|---|---|
| **BULL (200-SMA up)** | **+31.2% (43%)** | **−22.0% (24%)** |
| BEAR/CHOP | +1.9% (48%) | −0.7% (42%) |

- **The IS-bull longs (+31%, the ENTIRE edge) INVERT to −22% (WR 24%) in OOS-bull — the SAME trend
  regime.** The edge is NOT regime-conditional. It is **overfit to the specific 2023-24 IS-bull
  microstructure and does not generalize to the 2025-26 OOS-bull.**
- **This is why the de-lever failed:** it keeps FULL size in up-trends (where it expected the edge)
  and cuts size in down-trends. But the OOS losses are IN the up-trends → the de-lever protected
  nothing in OOS and instead cut the (modest, +1.9% IS) bear/chop longs → IS Sharpe down, OOS unchanged.
  The 200-SMA regime signal is the wrong discriminator: the OOS failure is WITHIN the favorable regime.
- **Not a seed lottery (so K=20 won't fix it):** iter-011 showed the negative IS sub-periods are
  deterministic across all 5 seeds. The IS→OOS-bull inversion is a structural distribution shift, not
  estimation variance — more bagging averages variance, not a systematic shift.
- **Proxy-vs-backtest gap (4th occurrence):** the RE's pooled-per-trade Sharpe proxy predicted a +0.17
  IS lift; the real bagged-specialist time-series Sharpe (with R5 interaction) fell −0.14. Offline
  proxies (FE funding-importance, FE label, QR N9, RE de-lever) have ALL overpredicted vs the backtest.

**OOS-vigilance:** the regime-split here is an OOS EVALUATION (Phase 7), not design — no fix was tuned
on it. The RE's primitive was calibrated IS-only (verified). backtest.py wiring byte-identical when
disabled (93 backtest/lookahead tests pass).

## CAMPAIGN SYNTHESIS (iter-005 → 012) — the honest terminal read for the directional model
- **Features (005-007):** orthogonal non-OHLCV families (funding ×2, OI) all NEGATIVE, bottom-third
  importance. BTC price signal at the noise floor (max |IS-IC| 0.028). Axis closed.
- **Label mode (008-009):** the unlock — fixed_horizon + let-winners-run lifted IS −0.4 → near 0.
- **Horizon (010):** N9 (3d) gave the FIRST positive IS (+0.39) but OOS −1.48 (overfit; shorter = worse OOS).
- **Generalization diagnosis (011):** the long edge is seed-deterministic, structurally regime-shaped.
- **Sizing fix (012):** the de-lever doesn't transfer — and the regime split reveals WHY: the edge
  inverts IS-bull → OOS-bull. **The directional model overfits IS-within-regime and does not
  generalize to OOS, deterministically.** No overlay (gate ruled out /011, sizing failed /012) can fix
  a within-favorable-regime inversion.

**Conclusion:** the let-winners-run + fixed_horizon mechanism extracts a genuine IS edge, but the
LightGBM directional signal on BTC 8h is overfit to IS-bull microstructure that did not repeat in
OOS-bull. The directional-prediction approach has been thoroughly explored (8 screens, FE+RE+QR all
engaged, every lever — feature/label/horizon/gate/sizing — tried) and hits a structural OOS
generalization wall that is not an overlay-fixable problem.

**Next (strategic fork — surfaced to user):** the within-regime IS→OOS inversion means more
directional-model tweaks are likely futile. Honest options: (A) rethink the modeling approach for
OOS-robustness (different target/architecture — e.g. non-directional, volatility/breakout, or an
ensemble built explicitly for distribution-shift robustness), or (B) accept BTC 8h directional as the
overfit-prone limit it appears to be. This is a genuine strategic decision — paused for user steer.
