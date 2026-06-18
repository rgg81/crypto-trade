# Diary — iter-v1/028 (ETHUSDT) — EXPLORATION — META-LABELING (M1 trend + M2 veto) — PROMISING (coherence win, partial de-concentration)

**Axis:** SOTA meta-labeling (López de Prado) — M1 = iter-027 trend-state stack (primary/side); M2 =
LGBMClassifier on a 15-col crypto-native positioning set, VETO when P(win)<0.45 (size/filter). Built to
DE-CONCENTRATE the OOS (user mandate: ETH must succeed where BTC's thin/concentrated OOS failed). M2
look-ahead-tested (trains only on past resolved M1 outcomes, embargo = full 14d horizon; 10/10 PASS).
K=5, n_trials=35 (M1) / n_trials_m2=18.

**Result (vs ETH baseline iter-027 IS +0.63 / OOS +0.06, top-2=438%):**
| | IS | OOS | ratio | OOS top-2 conc | OOS trades/winners | OOS DD |
|---|---|---|---|---|---|---|
| iter-028 | +0.2705 | +0.2097 | **+0.78** | 135% | 23 / 8 | 4.10% |
WR 31%/35%, 67/23 trades. 5/5 seeds.

**Verdict: PROMISING — meta-labeling IMPROVED generalization, but the de-concentration is PARTIAL.**
- **Most COHERENT both-positive of the campaign:** IS +0.27 / OOS +0.21, ratio +0.78 (vs every prior
  config's near-zero/inverted ratio). OOS lifted +0.06→+0.21; OOS DD a tiny 4.1%. M2 raised precision
  (the win is generalization coherence, not raw IS — IS dropped +0.63→+0.27 as M2 filtered trades).
- **Partial de-concentration:** OOS top-2 438%→135% (much better) but STILL FAILS the strict <40% check
  (top-1 trade = 78% of net, 8 winners). M2 FILTERED trades (23 OOS, fewer) rather than BROADENING the
  book. The IS-proxy de-concentration (top-2 0.064) did NOT fully transfer to OOS (135%) — proxy gap.

**Caveats (→ K=20 arbiter):**
- K=5: the OOS +0.21 is still ~one big trade (top-1 78%) — fragile. K=20 is the arbiter.
- M2 is a LEARNED layer (which trades it keeps varies per seed) → adds seed-variance → the K=5 OOS
  could regress at K=20 (like iter-026 +0.97→+0.06, iter-022 collapse). The K=20 tests robustness.

**Next:** iter-v1/029 — **K=20 CONFIRMATION of iter-028** (the arbiter). If the coherent both-positive
(IS +0.27/OOS +0.21) HOLDS → it's a genuinely better, more-coherent ETH baseline than iter-027 (bank
it). If it regresses → the meta-labeling's K=5 OOS was seed-variance; pursue BREADTH instead.
**The full broad-OOS win still needs BREADTH** (the user's explicit target): M2 filtered but didn't
broaden. Next-tier per QR: ENSEMBLE M1 over SMA 100/200/300 (more diverse trend signals → more reliable
trades → broader OOS) + meta-label each. That's the path to a truly de-concentrated OOS.
