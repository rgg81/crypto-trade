# Diary — iter-v1/018 (BTCUSDT) — EXPLORATION — TREND-STRENGTH CONVICTION GATE — PROMISING (closest to both-positive)

**Axis:** add a trend-CONVICTION entry gate to the iter-016 stack — trade the trend-state direction
only when `|close[t−1] − SMA200[t−1]| / ATR14[t−1] ≥ past-only median` (q=0.50); skip weak-trend chop.
Single-axis vs /016. K=5, n_trials=35, slippage 2. (QR iter-018: the OOS short-bias was a curve-fit
NULL on IS; this gate is the IS-sub-period-stable mechanism that surfaced instead.)

**Result:**
| | IS Sharpe | OOS Sharpe | IS net | OOS net | trades (IS/OOS) | IS DD | OOS DD |
|---|---|---|---|---|---|---|---|
| iter-017 K=20 (no gate) | +0.25 | −1.15 | — | — | 120/58 | 13.9% | 6.3% |
| **iter-018 K=5 (+ gate)** | **+0.8563** | **−0.1647** | +100.2% | −1.03% | 56/36 | 11.3% | 5.2% |
PF 2.70/0.92, Sortino 1.07/−0.10, WR 33.9%/30.6%, payoff 3.70/2.65. 5/5 seeds.

**Verdict: PROMISING — closest to both-positive yet; mechanism sound; NOT both-positive (OOS −0.16).**
- **IS +0.86 = strongest of the campaign** (gate removes net-negative weak-trend chop; PF 2.70, DD 11.3%).
- **The gate FIXED the OOS-long bleed:** OOS longs −14% (iter-017 K=20) → **−0.3% (~flat)** here. Overall
  OOS dragged from −1.15 up to **−0.16** — essentially flat. The conviction gate is the right mechanism:
  it skips the weak-trend chop where direction is noise (crypto-native; trends pay only when convincing).
- **Direction split (IS-only edge is LONG, confirming the iter-018 QR finding):** IS longs +91.2% (WR 39%),
  IS shorts +9.0%. OOS longs −0.3% (gate cleaned them), OOS shorts +11.9%.

**Caveats (→ next step):**
- OOS −0.16 is a HAIR below zero — within noise on only **36 OOS trades (~2.4/mo)**. Not both-positive.
- **Thin trade rate triggers the QR's pre-registered q=0.40 fallback** (the gate at q=0.50 cut trades
  ~49%). A K=5 result is TENTATIVE (basin-lottery live — iter-016 K=5 +0.11 → K=20 −1.15).

**Campaign trajectory (converging):** iter-016 K=5 +0.63/+0.11 (lottery) → iter-017 K=20 +0.25/−1.15
(honest, OOS-long bleed) → **iter-018 +0.86/−0.16 (gate fixes the bleed, OOS ~flat).** The OOS has
climbed −1.15 → −0.16 as the mechanism improved. One more push could cross zero.

**Next:** iter-v1/019 — **q=0.40 fallback** (less aggressive gate → ~thicker trade rate, more robust OOS
estimate; QR pre-registered as IS-stable). If q=0.40 gives OOS ≥ 0 with a thicker trade count → K=20
CONFIRM (mandatory given the live basin-lottery). If q=0.40 OOS stays negative → the gate cleans but
doesn't cross zero; consolidate + surface options to the user.
