# Phase 7.5 Critic Review — iter-v1/010 (BTCUSDT) — EXPLORATION screen

## Verdict: NEGATIVE (severe IS/OOS inversion) — but the first positive IS; the wall moved from "no signal" to "no generalization."

### Results (K=5 screen)
| | IS Sharpe | OOS Sharpe | WR | payoff | IS net | OOS net |
|---|---|---|---|---|---|---|
| N21 (7d, /009) | −0.09 | −0.74 | 33% | 2.08 | +4.43% | −15.94% |
| **N9 (3d, /010)** | **+0.3863** | **−1.4762** | 43.4%/38.8% | 1.41/1.20 | **+29.65%** | **−32.14%** |

### Critic's literal read
Both windows must be positive (generalization-coherence). iter-010 has a strong positive IS (+0.39)
and a deeply negative OOS (−1.48) — a severe inversion (ratio −3.82). NEGATIVE; not a merge candidate.
Do NOT spend a K=20 confirmation on it: OOS −1.48 is not coherence-passable, and K=20 reduces variance,
not regime mismatch.

### What's genuinely new (Sharpe-lens, not return-lens)
- **First positive IS Sharpe in 10 iterations.** The fixed_horizon + let-winners-run mechanism + the
  shorter horizon's higher hit rate (WR 43.4%, QR predicted 44.5%) produce a real IS edge (net +29.65%,
  DD 16.3%). The signal EXISTS in-sample.
- **The failure is now pure generalization.** Long/short split: IS profit is entirely LONG (+33%; shorts
  −3.5%), and the LONG edge collapses OOS (WR 45.5%→31.2%, +33%→−22.7%). The model's long directional
  skill does not survive into the 2025-26 OOS regime.
- **Overfit signature:** shorter horizon → more trades → better IS, worse OOS (gap 0.65 at N21 → 1.87 at
  N9). Coherence is unreachable on the horizon axis alone.

### Methodology
- OOS-vigilance PASS (QR scripts IS-only, verified). /002–/007 byte-identical.
- K=5 single-pass: the +0.39 IS has lottery variance; but the OOS −1.48 + the long-edge-collapse
  diagnosis are structural enough that the verdict (non-coherent) is robust to K.

## Proposed Backtest Changes (mandatory)
1. **iter-v1/011 — attack the GENERALIZATION GAP, not the horizon.** Crypto-QR diagnoses IS-only whether
   the long-edge IS→OOS collapse is reducible overfit vs structural regime, and recommends the single
   highest-leverage gap-reduction lever: (a) longer training window (span more crypto regimes → robust
   edge; the diagnosis is "edge fit to a narrow recent IS window"), (b) leaner/more-regularized model
   (fewer features — drop FE-flagged inert mom_rsi_9/vol_cmf_10/ent_shannon_10; tighter bounds), or (c)
   more bagging. Pick ONE axis (single-axis screen discipline). Keep N9 (positive-IS) OR test a middle
   horizon if the QR finds the gap shrinks with horizon.
2. **Conserve K=20.** Only confirm once a K=5 screen shows a both-positive (coherent) profile. iter-010
   is not it.
3. **Reserve — long-bias / regime-conditional sizing** if overfit reduction stalls: IS edge is long-only,
   so a long-tilt or vol-scaled sizing (NOT the ruled-out binary regime gate) may improve OOS robustness.
