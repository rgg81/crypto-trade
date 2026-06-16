# Phase 7.5 Critic Review — iter-v1/009 (BTCUSDT) — EXPLORATION screen

## Verdict: NEGATIVE on the coherence gate — but the mechanism is validated; this is the most informative screen of the campaign.

### Results (K=5 screen)
| | IS Sharpe | OOS Sharpe | win rate | payoff | IS net | OOS net | exits |
|---|---|---|---|---|---|---|---|
| prior screens (/005–/007) | −0.40 to −0.47 | mixed | — | — | neg | neg | TP+SL+timeout |
| **iter-009 fixed_horizon let-run** | **−0.0878** | **−0.7442** | 32.7%/33.3% | **2.08/1.75** | **+4.43%** | **−15.94%** | **0 TP**, SL+timeout |

### Critic's literal read
Both Sharpe negative → NEGATIVE on the generalization-coherence gate. Not advanceable to a K=20
confirmation as-is. BUT this is not a dead screen: it isolates the mechanism and the binding constraint.

### What the result proves (Sharpe-lens, per user directive — NOT a return-vs-B&H judgment)
1. **Execution-consistency fix worked:** 0 take-profit exits → winners ran to the 7d timeout; the QE's
   `atr_tp=100` non-binding + `atr_sl=1.45` design behaved exactly as intended in the live backtest.
2. **Payoff asymmetry is real:** IS payoff 2.08 (win +6.46% / loss −3.11%). This is the correct
   crypto-native trend-capture structure.
3. **Binding constraint = hit rate / regime.** At ~33% WR, breakeven payoff = 2.0. IS clears it (2.08 →
   net +4.43%); OOS slips below (1.75 → net −15.94%). The OOS loss is entirely the payoff dropping under
   breakeven — a trade-SELECTION problem, not a label or feature problem.
4. **Best IS of the campaign** (−0.09 vs prior −0.17 best). The label-mode pivot improved learnability.

### Methodology flags
- **FE proxy overprediction (recurring):** IS Sharpe proxy +1.28 → backtest −0.09. Offline purged-CV
  proxies ignore SL truncation, costs, R3/R5 gates, confidence-threshold filtering, and K-bagging.
  Treat FE/QR offline Sharpe/importance proxies as DIRECTION-ONLY; never as magnitude. (Cf. funding
  importance rank 8→29.)
- OOS-vigilance PASS: FE scripts IS-only (verified). QE kept /002–/007 byte-identical.
- K=5 single-pass: IS→OOS drop (−0.09→−0.74) is partly small-K lottery + regime mismatch; a coherent
  candidate would need K=20 confirmation before any merge claim.

## Proposed Backtest Changes (mandatory)
1. **iter-v1/010 — KEEP fixed_horizon let-winners-run; ADD a regime gate.** Trade only when crypto
   trend-persistence favors the asymmetric payoff (a stateless trend/vol-state gate). This directly
   raises the hit rate / payoff toward clearing breakeven and executes the user's Sharpe-lens
   re-examination of the iter-008 regimes. Crypto-QR designs IS-only: which regime, threshold,
   retained trade count (≥~10/mo OOS). Pre-register the both-positive coherence falsifier.
2. **Reserve — fixed_horizon N9 (3d).** The FE's highest proxy; a shorter horizon trades payoff for a
   higher hit rate. Screen if the regime gate fails. (Do not trust the +1.80 proxy magnitude.)
3. **Confidence-threshold sensitivity** as a tertiary lever: raising the gate trades count for hit
   rate — but only after the regime gate, since regime selection is the more structural fix.
