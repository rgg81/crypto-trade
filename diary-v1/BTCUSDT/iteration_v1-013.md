# Diary — iter-v1/013 (BTCUSDT) — EXPLORATION — LENGTHEN horizon 3d→14d (N=42)

**Axis:** lengthen the fixed_horizon let-winners-run hold 9→42 candles (3d→14d). Same 19-col HYBRID +
let-winners-run execution (atr_tp=100 non-binding, atr_sl=1.45), NO trend_scale. K=5, n_trials=35,
slippage 2. The user's "expand the timeout" instinct, targeting OOS recovery.

**Result (scored RELATIVE to baseline iter-001 IS −0.28 / OOS +0.64):**
IS Sharpe **+0.8767** (net +137%, Sortino +1.36, PF 1.68, max DD 31.8%) / OOS **−1.1814** (net −35.6%,
DD 31.8%). WR 25.8%/21.8%, payoff **4.26**/2.54. 120/55 trades. 5/5 seeds.

**Verdict: best IS of the campaign; OOS still negative → not both-positive yet, but a strong base.**
- **IS +0.88 is the highest of iter-001→013** (vs baseline −0.28; vs N9 +0.39). The 14d let-winners-run
  captures big multi-week crypto moves — low WR (26%) × huge payoff (4.26) = +137% IS net. The IS edge
  is now genuinely strong.
- **OOS −1.18 (net −35.6%).** OOS longs still lose (dir+1 WR 22%, net −23.6%); shorts also lose.

**Horizon sweep (non-monotonic — IS climbs with horizon, OOS stays negative):**
| horizon | IS | OOS | IS net | OOS net | trades |
|---|---|---|---|---|---|
| N9 (3d) | +0.39 | −1.48 | +29.6% | −32% | 242/98 |
| N21 (7d) | −0.09 | −0.74 | — | — | 171/78 |
| **N42 (14d)** | **+0.88** | **−1.18** | **+137%** | −35.6% | 120/55 |

Lengthening the horizon BOOSTS IS (captures bigger moves) but does NOT fix OOS — the OOS directional
edge is absent at every horizon. **Horizon alone cannot reach both-positive; the problem is now purely
OOS (the IS side is solved).**

**Trade-rate note:** OOS 55 trades / ~15mo ≈ 3.7/mo (thin at 14d; below the old 10/mo floor — flagged,
deprioritized per the "don't demand perfection" steer). R2 (sizing) won't change count.

**Next (queued iter-015):** apply the **R2 drawdown brake** (RE-validated, regime-agnostic) on THIS
N42 base — it's the strongest IS base (+0.88) and has a 31.8% OOS max-DD that R2 is built to bound.
R2 de-levers during drawdowns → should cut the OOS −35.6% bleed toward 0 while LIFTING the strong IS
(RE IS proxy +0.71, DD −61%). This is the clearest both-positive shot: strong IS already in hand +
R2-bounded OOS. If R2 brings OOS near/above 0 with IS strongly positive → both-positive (or clearly
beats the baseline).
