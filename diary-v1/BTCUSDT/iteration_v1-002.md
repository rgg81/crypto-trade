# Diary — iter-v1/002 (BTCUSDT) — EXPLORATION

**Axis:** PRIMARY = 41-col feature prune (`V1_BTC_PRUNED_ITER002`, strict subset of 193); SUPPORTING
= R2 drawdown brake (8/0.5/18). K=3 screen, n_trials=35, slippage 2 bps/side, honest costs.

**Result (vs iter-001 baseline IS −0.2793 / OOS +0.6401, dispersion 49.46):**
IS Sharpe **+0.2058** / OOS **+0.1172**, OOS/IS ratio **+0.57**, dispersion **34.57**, 191/73 trades,
IS net −12.02→+8.43, OOS net +9.07→+1.16. Clean run, 0 seed failures.

**Verdict: NEGATIVE as-bundled → feature prune PROMISING (redirect).**
- The prune did exactly what was predicted: **IS crossed positive (−0.28→+0.21), dispersion dropped
  ~30% (49.5→34.6).** The 193-col dump was ~86% redundant; cutting it strengthened signal consensus.
- **OOS fell +0.64→+0.12** — but the Critic's trade-level evidence pins this on **R2** (size scaled
  down through drawdown, `weight_factor` 0.33→0.18 OOS, throttling the recovery winners), NOT the
  prune. The brief's pre-registered attribution caveat materialized.
- **Generalization reframe (user, 2026-06-16):** iter-002's both-positive profile (ratio +0.57) is
  MORE trustworthy than iter-001's inversion (IS −0.28 / OOS +0.64, ratio −2.29 = regime artifact).
  The "beat +0.64 OOS" guardrail was the wrong bar. Codified into the skill merge gate
  (generalization-coherence first; don't reward sign-inverted baselines on raw OOS).

**Lessons**
- Don't bundle a size-altering risk brake with the primary feature axis in a screen (the R2 confound
  was predictable + predicted). Feature-only screens isolate cleanly.
- The prune is the real edge; R2 is the OOS drag to remove.

**Next:** iter-v1/003 = feature-only ablation (41-col prune, R2 OFF), K=3 — LAUNCHED. Expected:
both-positive with OOS recovered → K=20 confirmation candidate (new BASELINE_V1_BTCUSDT). Then
iter-004 = orthogonal non-OHLCV feature families (funding/OI/long-short/basis) per FE, to attack the
thin price-only edge.
