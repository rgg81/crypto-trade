# Diary — iter-v1/037-039 — STRIP-MODEL PORTABILITY SWEEP (LINK/LTC/DOT) — CLOSEOUT: ETH-specific, NOT track-wide

**Axis:** map whether the iter-034/035 ETH breakthrough (STRIP the overfit LightGBM entry layer → trade
the pure deterministic trend-state core) generalizes across the v1 coins. Generic deterministic-core
directional screen (`deterministic_entry_only=True`, R2 OFF, K=1 model-bypassed) on LINK (037) / LTC (038)
/ DOT (039), to compare against the already-run ETH (034) + BTC (036).

## The full 5-coin strip-model verdict (deterministic core, OOS Sharpe)
| coin | IS Sharpe | OOS Sharpe | verdict |
|---|---|---|---|
| **ETHUSDT** | +0.6481 | **+0.4148** | CLEAN WIN — both-positive, strong → MERGED (BASELINE_V1_ETHUSDT) |
| BTCUSDT | +0.2977 | +0.1153 | both-positive but MODEST; not Pareto-vs iter-020 (no merge) |
| DOTUSDT | +0.3946 | −0.0331 | IS-positive, OOS ≈ 0 (marginal; R2-off — a proper R2 test *might* tip it) |
| LINKUSDT | −0.0365 | −1.0329 | both-NEGATIVE (catastrophic OOS) |
| LTCUSDT | −0.5747 | −0.1714 | both-NEGATIVE |

## Conclusion: STRIP-MODEL IS COIN-SPECIFIC, NOT A TRACK-WIDE DEFAULT (hypothesis FALSIFIED)
- Both-positive on only **2 of 5** coins (ETH strong, BTC modest); IS-positive on 3 of 5 (+DOT); fails
  outright on LINK/LTC.
- **ETH is special:** its 200-SMA trend-state core is exceptionally clean in the 2025-26 OOS regime
  (strong trends the deterministic rule catches). LINK/LTC's OOS regimes are choppy → the deterministic
  trend-state direction WHIPSAWS (both-negative). BTC/DOT are in between.
- The "deterministic core generalizes; the LightGBM entry layer is a track-wide drag" hypothesis is
  FALSIFIED at the track level. The reality: the LightGBM entry layer's overfit-share AND the
  deterministic core's viability are both COIN-REGIME-dependent. On ETH the model was pure overfit drag
  (strip → huge win); on the choppy coins the deterministic core has no edge to begin with (the model,
  or a different approach, is needed there).

## Caveat (R2-OFF confound — honest)
The sweep ran R2 OFF (per-coin R2 not calibrated). This INFLATES the drawdowns (LINK 96%, LTC 103% IS
MaxDD) and depresses Sharpe somewhat. BUT R2 is DD-control and does NOT flip the Sharpe SIGN — LTC IS
−0.57 and LINK OOS −1.03 are clearly negative regardless. DOT (IS +0.39 / OOS −0.03) is the one case where
a proper R2-calibrated test *might* tip OOS positive (marginal). The directional verdict (ETH clean, BTC
modest, others fail) is robust to the confound. A proper baseline for any promising coin would re-test
with calibrated R2.

## Net takeaways
1. **The ETH breakthrough (iter-034/035, OOS +0.41, MERGED) stands as the headline win** — it serves the
   user's mandate (ETH succeeds where BTC couldn't, OOS +0.41 vs BTC +0.09) and is not diminished by the
   sweep. It's a real, deterministic, K-invariant, leak-free edge.
2. **Strip-model is a per-coin TOOL, not a default.** Apply it where the coin's OOS regime is
   trend-favorable (ETH; partially BTC/DOT); the choppy coins (LINK/LTC) need the model or a different edge.
3. **Breadth remains intractable at the single-symbol level** for every coin tried — the path to a broad,
   de-concentrated book is PORTFOLIO-level (a bundle of per-coin baselines = many independent coin edges),
   which is the redesign's original architecture. That requires establishing per-coin baselines (only BTC
   iter-020 + ETH iter-034 exist; LINK/LTC/DOT need model-gated bootstraps since their deterministic core
   fails).

## Next (strategic fork — surfaced to user)
(1) **Portfolio path (real breadth):** bootstrap model-gated baselines for LINK/LTC/DOT (iter-027-style
stack) → assemble a regime-complementary BUNDLE → portfolio-level breadth + de-concentration. The
redesign's original goal; the genuine answer to the breadth mandate. (2) **DOT near-miss:** a proper
R2-calibrated DOT test (IS +0.39 is a real positive edge; OOS −0.03 might tip). (3) **Deepen ETH:** a new
edge class on the strong ETH core. Recommendation: (1) — it both serves breadth AND builds the track.
