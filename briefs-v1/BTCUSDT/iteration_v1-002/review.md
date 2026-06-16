# Phase 7.5 Critic Review — iter-v1/002 (BTCUSDT) — EXPLORATION screen

## Verdict: NEGATIVE **as bundled** — but the feature prune is PROMISING; redirect, don't abandon.

### Results (K=3 screen) vs iter-001 baseline (K=20)
| | IS Sharpe | OOS Sharpe | OOS/IS ratio | dispersion | IS net | OOS net |
|---|---|---|---|---|---|---|
| iter-001 baseline | −0.2793 | +0.6401 | **−2.29 (inversion)** | 49.46 | −12.02 | +9.07 |
| iter-002 (prune+R2) | **+0.2058** | +0.1172 | **+0.57 (coherent)** | 34.57 | +8.43 | +1.16 |

### Critic's literal read
The brief's pre-registered guardrail ("OOS must not collapse below +0.64") fired: OOS fell +0.64→+0.12 (−82%). Per the conjunctive PROMISING test, that routes the **bundled config** to NEGATIVE — advancing it to a K=20 confirmation as-is would burn budget on a config that breaches its own guardrail.

### Attribution (load-bearing — from trade-level evidence, not speculation)
**R2, not the prune, caused the OOS drop.** iter-002 OOS `weight_factor` decays monotonically 0.33→0.18 as drawdown deepens (vs iter-001 pinned at the 0.33 VT floor), shrinking exactly the late-2025/2026 recovery take-profits (+6–7% trades multiplied by ~0.18–0.26). Monthly: 2025-08 +5.11→+0.49, 2025-10 +4.55→−0.94. The RE's "R2 fires rarely OOS" assumption was falsified — the OOS path stayed in drawdown enough to keep R2 armed. **The prune itself lifted IS −0.28→+0.21 (net −12→+8) and dropped dispersion ~30%** — it looks good in isolation; R2 rode along and destroyed OOS.

### Flags
- **K-mismatch** (screen K=3 vs baseline K=20): dispersion + Sharpe comparisons are directionally indicative only, not quantitatively attributable until matched-K. (Fine for a screen.)
- **dsr reporting defect:** `comparison.csv` dsr (−60.2) disagrees with `dsr.json` (0.0) — clean up before any confirmation.
- Methodology PASS on results: honest-cost netting verified (net = pnl − fee − slippage, slippage 0.04% round-trip), IS/OOS split at cutoff honored, no leakage signature (IS-worse-than-OOS is the opposite of leakage), training_days searched.

## QR reframe (user directive 2026-06-16) — the prune is the WIN
The literal "beat +0.64 OOS" guardrail was the WRONG bar: iter-001's +0.64 OOS sits on a **negative IS (inversion, ratio −2.29)** — a regime artifact, not a generalizing edge. iter-002's **both-positive profile (IS +0.21 / OOS +0.12, ratio +0.57)** is the more trustworthy, generalizing model. Codified into the skill merge gate (generalization-coherence FIRST: don't reward sign-inverted baselines on their raw OOS number). **The prune is PROMISING.** Combined with the R2-attribution finding, the OOS +0.12 is a *throttled* number — feature-only (R2 OFF) should be both-positive with OOS recovered → strictly better on every frame.

## Proposed Backtest Changes (mandatory)
1. **iter-v1/003 — feature-only re-screen (41-col prune, R2 OFF), K=3.** The decisive isolator: confirm the prune keeps the both-positive coherence with OOS recovered toward +0.64. → if so, it earns a K=20 confirmation as the baseline-beater. **(LAUNCHED.)**
2. Gentler R2 (10/0.5/25) on the pruned base — only if a brake is wanted after #1; pre-register the OOS-coherence guardrail.
3. iter-v1/004 axis (FE-flagged): add orthogonal non-OHLCV families (funding / OI / long-short / basis) on the pruned base, R2 OFF — attacks the diagnosed thin single-factor (price-only) edge.
