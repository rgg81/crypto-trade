# Diary — iter-v1/016 (BTCUSDT) — EXPLORATION — STATELESS 200-SMA TREND-STATE DIRECTION — ★ FIRST BOTH-POSITIVE ★

**Axis:** replace the overfit LightGBM *direction* with a stateless, parameter-free **200-SMA
trend-state** sign (`+1 if close[t−1] > SMA200[t−1] else −1`, past-only). V-A: keep the LightGBM
specialist for entry timing/confidence; override only the executed direction. Full stack = iter-015
(19-col HYBRID, fixed_horizon N=42 14d, let-winners-run, R2 brake) + trend-state direction. Single-axis
vs /015. K=5, n_trials=35, slippage 2.

**Result — FIRST both-positive of the campaign (iter-001→016):**
| | IS Sharpe | OOS Sharpe | IS net | OOS net | IS maxDD | OOS maxDD | WR | payoff |
|---|---|---|---|---|---|---|---|---|
| **iter-016** | **+0.6308** | **+0.1120** | +86.0% | +0.52% | 15.3% | 3.93% | 28.6%/26.9% | 3.34/3.14 |
5/5 seeds, 112/52 trades, clean run, trend-state index loaded (FAIL-LOUD guard passed).

**Verdict: PROMISING — first both-positive; beats the baseline on the generalization-coherence gate.**
- **IS +0.63 AND OOS +0.11 — both positive (ratio +0.18, coherent).** vs baseline IS −0.28 / OOS +0.64
  (ratio −2.29, inverted). Per the user's codified gate ("both positives still better than the
  baseline; ratio IS/OOS proves generalization"), iter-016's coherent profile BEATS the inverted
  baseline despite a lower raw OOS — it's a generalizing edge, not a regime artifact.
- **Mechanism confirmed (direction split):** OOS **shorts +25.1% (WR 31%)**, OOS longs −9.2% (WR 23%).
  The trend-state went SHORT below the 200-SMA; OOS opened in a correction → the shorts captured the
  down-moves the overfit model-longs kept losing on (iter-010→015 OOS-bull long inversion). A direction
  rule that CANNOT overfit (zero params) generalized where the learned sign couldn't. This is the
  campaign's core finding materialized: **the direction source was the bug; a stateless trend rule fixes it.**
- R2 brake kept the OOS drawdown tiny (3.93%) — capital-preservation working alongside.

**Honest caveats (→ why K=20 confirmation is needed):**
- OOS Sharpe +0.11 is MARGINAL (barely positive); OOS net +0.52% is thin. A K=5 screen is TENTATIVE
  (lottery risk) — the K=20 confirmation is the arbiter.
- OOS 52 trades / ~15mo ≈ 3.5/mo (thin, below the old 10/mo floor; deprioritized per "don't demand
  perfection," but flagged — the longer 14d horizon trades infrequently).

**Campaign arc (the grind that got here):** features (FE: direction not stable) → label-mode unlock
(fixed_horizon) → horizon (boosts IS, never OOS) → de-lever (failed) → R2 (bounds loss, not Sharpe
sign) → **diagnosis: the DIRECTION SOURCE overfits** → stateless trend-state direction = both-positive.

**Next:** iter-v1/017 — **K=20 CONFIRMATION** of the iter-016 config (verify the both-positive holds
across 20 bagging seeds, not a K=5 lottery). If it holds (IS>0 AND OOS>0, beats baseline on the
coherence gate) → MERGE: update BASELINE_V1_BTCUSDT. The first merge candidate of the redesign.
