# Diary — iter-v1/019 (BTCUSDT) — EXPLORATION — conviction gate q=0.40 — BOTH-POSITIVE (K=5, marginal)

**Axis:** trend-strength conviction gate q=0.50 → 0.40 (QR pre-registered trade-rate fallback). Single
knob vs /018; rest bit-identical (iter-016 stack + gate). K=5, n_trials=35, slippage 2.

**Result — BOTH-POSITIVE at K=5:**
| | IS Sharpe | OOS Sharpe | IS net | OOS net | trades (IS/OOS) |
|---|---|---|---|---|---|
| iter-018 (q=0.50) | +0.8563 | **−0.1647** | +100% | −1.0% | 56/36 |
| **iter-019 (q=0.40)** | **+0.5370** | **+0.0602** | +65.2% | +22.2% | 67/36 |
WR 28.4%/33.3%, payoff 3.63/2.67. OOS dir −1 (short) +22.3% (WR 41%), dir +1 (long) −0.1% (flat). 5/5 seeds.

**Verdict: PROMISING — first conviction-gate BOTH-POSITIVE (IS +0.54 / OOS +0.06), but the OOS is
marginal/noise-around-zero. K=20 confirmation MANDATORY before any merge claim.**
- Both-positive (ratio +0.11, coherent) — on the relative gate beats the inverted baseline (IS −0.28 /
  OOS +0.64, ratio −2.29). The user's explicit goal (both positive) is met AT K=5.
- **⚠️ The OOS is knob-sensitive noise:** q=0.50 → 0.40 FLIPPED OOS −0.16 → +0.06. A robust edge would
  not change sign on a small quantile change. Strong signal the conviction-gate OOS is ≈0 (flat),
  landing barely positive on the favorable side of the noise at q=0.40.
- **Still thin:** 36 OOS trades (~2.4/mo) — q=0.40 added IS trades (56→67) but NOT OOS trades (36→36).
  OOS +0.06 is within noise on 36 trades.
- **Basin-lottery live:** iter-016 K=5 OOS +0.11 collapsed to K=20 −1.15. A K=5 both-positive is TENTATIVE.

**Honest framing:** the conviction-gate mechanism (iter-018/019) achieves strong IS (+0.5..+0.9) and
dragged OOS from −1.15 (iter-017) up to ~0 (flat, −0.16 to +0.06 depending on the knob). That is the
campaign's best OOS — but it is FLAT, not a robust positive edge. Whether it lands ≥0 at honest K=20
is the open question.

**Next:** iter-v1/020 — **K=20 CONFIRMATION of iter-019 (q=0.40)**. Methodology-mandated for a PROMISING
both-positive; the backtest is the only arbiter (no offline projection-based skip despite the
knob-sensitivity concern). If OOS holds ≥0 with IS>0 across 20 seeds → MERGE (first both-positive
baseline of the redesign, beats the inverted iter-001 on coherence). If it collapses (like iter-016)
→ the conviction-gate OOS is confirmed noise-around-zero; consolidate + surface to the user (strong IS,
OOS-flat is the ceiling — needs a genuinely new OOS-edge source, not more gate tuning).
