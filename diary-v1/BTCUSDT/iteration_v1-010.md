# Diary — iter-v1/010 (BTCUSDT) — EXPLORATION — fixed_horizon N9 (3d) let-winners-run, NO gate

**Axis:** SHORTEN iter-009's horizon 21→9 (3d). Same 19-col HYBRID set + let-winners-run execution
(`atr_tp=100` TP non-binding, `atr_sl=1.45`, exec timeout = label horizon = 3d). NO regime gate
(QR ruled out on Sharpe basis: gates lock in the T3 inversion). K=5, n_trials=35, slippage 2.

**Result:** IS Sharpe **+0.3863** / OOS **−1.4762**, WR 43.4%/38.8%, payoff 1.41/1.20,
IS net **+29.65%** (max DD 16.3%, PF 1.14, Sortino +0.45) / OOS net **−32.14%** (max DD 24.7%).
242/98 trades, 5/5 seeds. Exits: timeout 141/51 + stop_loss 101/47 (0 take-profit → winners ran).

**Verdict: NEGATIVE (severe IS/OOS inversion) — but a genuine MILESTONE.**
- **FIRST positive IS Sharpe of the entire campaign (+0.39).** The QR's hit-rate prediction was
  accurate: WR 43.4% ≈ predicted 44.5%. At 43% WR, breakeven payoff ~1.32; IS payoff 1.41 clears it
  → IS net +29.65%, Sharpe +0.39, DD only 16.3%. The IS profile is genuinely good.
- **But OOS collapsed to −1.48 (worst of the campaign).** OOS payoff 1.20 < breakeven 1.58 for 38.8%
  WR → net −32.14%. A severe inversion (ratio −3.82): the OPPOSITE of generalization.

### Diagnosis — the long directional edge overfits IS, vanishes OOS
Long/short PnL split (the decisive evidence):
| | IS trades | IS WR | IS net | OOS trades | OOS WR | OOS net |
|---|---|---|---|---|---|---|
| LONG (+1) | 112 | **45.5%** | **+33.10%** | 48 | **31.2%** | **−22.68%** |
| SHORT (−1) | 130 | 41.5% | −3.45% | 50 | 46.0% | −9.45% |

- **ALL the IS profit is LONG (+33%); shorts are flat (−3.5%).** Not a short-side problem (my
  squeeze-veto hypothesis was wrong — shorts actually held up better OOS).
- **The LONG edge VANISHES OOS:** long WR 45.5%→31.2%, net +33%→−22.7%. The model's long directional
  skill does NOT generalize from IS to the 2025-26 OOS regime.

### Horizon sweep confirms overfitting (shorter = more overfit)
| horizon | IS | OOS | IS/OOS gap | IS trades |
|---|---|---|---|---|
| N21 (7d, /009) | −0.09 | −0.74 | 0.65 | 171 |
| N9 (3d, /010) | +0.39 | −1.48 | **1.87** | 242 |
Shorter horizon → more trades → better IS → MUCH worse OOS. The horizon is a tradeoff axis
(short = +IS/−OOS); **coherence (both-positive) is not reachable on the horizon axis alone.**

### OOS loss structure (overfit + regime mix)
OOS negative in 11/16 months; two big early-OOS losses (2025-04 −6.74, 2025-06 −8.13) = a hostile
post-cutoff regime for a long-biased trend-follower, plus a persistent thin bleed (the overfit long
edge). Mix of regime shift + systematic overfit.

**OOS-vigilance:** QR iter-010 scripts verified IS-only (3 scripts, pre-cutoff filter + leak assert).
QE wiring (iter-009 branch) kept /002-/007 byte-identical; iter-010 changed only the horizon.

**Lessons**
- The let-winners-run mechanism + fixed_horizon label CAN produce a positive IS Sharpe — the signal
  exists IS. The wall is now purely GENERALIZATION (IS→OOS), not signal absence. This is a different,
  more tractable problem than iter-001→008's noise floor.
- IS-proxy optimization (the QR's N9 pick) maximizes the OVERFIT direction. The user's original
  "expand the timeout" instinct (longer horizon) is the generalization-favoring direction — N21's gap
  (0.65) ≪ N9's (1.87). Don't chase the best-IS horizon; chase the smallest IS/OOS gap.
- The binding problem is the model's directional (long) edge not generalizing → attack the
  GENERALIZATION GAP (overfit reduction: more bagging / longer training window / leaner model),
  not the horizon or features.

**Next:** iter-v1/011 — attack the generalization gap at a positive-IS-capable config. Dispatch the
crypto-QR for an IS-only diagnosis: is the long-edge IS→OOS failure reducible (overfit — leaner
model / longer training window spanning more crypto regimes / more bagging) or structural (regime)?
QR recommends the single highest-leverage gap-reduction lever for iter-011 (K=5). Do NOT burn a K=20
confirmation on a config with OOS −1.48 (not coherent — won't merge); conserve it until a K=5 screen
shows a both-positive (coherent) profile.
