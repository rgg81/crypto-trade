# Diary — iter-v1/003 (BTCUSDT) — EXPLORATION (feature-only ablation of /002)

**Axis:** SAME 41-col prune as /002, **R2 drawdown brake OFF** (isolation variable). K=3, n_trials=35,
slippage 2bps/side. Decisive test of the /002 Critic finding that R2 (not the prune) caused the OOS drop.

**3-way result (K=3 screens vs K=20 baseline /001):**
| | IS Sharpe | OOS Sharpe | ratio | OOS net | dispersion |
|---|---|---|---|---|---|
| /001 baseline (K=20) | −0.2793 | +0.6401 | −2.29 (inversion) | +9.07 | 49.46 |
| /002 prune+R2 | +0.2058 | +0.1172 | +0.57 | +1.16 | 34.57 |
| **/003 prune-only** | **+0.1694** | **+0.3980** | **+2.35** | **+5.41** | **34.57** |

**Verdict: PROMISING — clean both-positive baseline-beater.**
- **R2 attribution CONFIRMED:** removing R2 recovered OOS +0.12→+0.40 (net +1.16→+5.41), IS ~flat
  (+0.21→+0.17). The Critic's trade-level call (R2 throttled OOS recovery winners) was correct.
- The **feature prune is the real edge**: IS −0.28→+0.17 (net −12→+7.8), dispersion 49.5→34.6, both
  windows positive. Beats the iter-001 inversion on the generalization-coherence gate.
- Caveat: this is K=3 vs the K=20 baseline (not matched-K). The next run is the matched-K decision.

**Next:** K=20 CONFIRMATION of the prune-only config (R2 OFF) — the merge-deciding run that (a) validates
at full bagging and (b) gives the matched-K comparison vs iter-001. If it holds (both-positive, beats
the inversion), it MERGES as the new BASELINE_V1_BTCUSDT. Then iter-004 = orthogonal non-OHLCV feature
families (funding/OI/long-short/basis) on the pruned base to attack the thin price-only edge.
