# LightGBM Master Advisory — iter-v1/092 (XRP ADX-kill) — RECOMMEND PIVOT

SPECIALIST EXPLORATION on XRP/088 (IS +0.3783/OOS +0.4966). Axis as briefed: opt-in post-aggregator ADX-kill `trend_adx_14 < 22.0 → NO_SIGNAL`. Default OFF. LOCK 50×30×depth-5×24mo; no multi-seed. I ran the crux OOS forensic (84 OOS trades × trend_adx_14, advisory-only — did NOT change the IS-calibrated threshold).

## CRUX (#2) — the OOS OFF stretch is TREND-WRONG-WAY, not chop → ADX-kill does NOT fix BLOCKER 1
Forensic (84-trade join):
| Window | n | net% | WR | ADX median | <22 KILLED (n/net) | ≥22 KEPT (n/net) |
|---|--:|--:|--:|--:|--|--|
| pre-Nov OFF | 44 | **−42.77** | 29.5% | **26.28** | 14 / −4.17 | 30 / **−38.61** |
| post-Nov ON | 40 | +72.04 | 57.5% | 21.54 | 21 / +37.11 | 19 / +34.92 |
The pre-Nov OFF losses live in the ADX≥22 KEPT bucket (30/44 trades, −38.61% of −42.77%, at ADX 26-66 = strongly TRENDING but wrong-direction, 27% WR). The ADX-kill removes only −4.17% (14 chop trades). Simulated F4: pre-Nov −42.77→−38.61, months-positive 3/8→3/8 UNCHANGED → **F4 DID-NOT-FIX**. ADX = trend STRENGTH not direction → a chop filter cannot fix wrong-direction-in-trend, which IS the OOS OFF failure mode. Perverse: the gate kills 52% of the WINNING post-Nov trades.

## 1 — mechanics
No look-ahead (reads decision-candle trend_adx_14, past-only, already a model feature at /088 rank 2; /091 R-CONV wiring precedent). But OOS ADX runs HOTTER than IS (OOS median 25.95 vs IS 25.45): thr=22 kills 42% OOS (not the IS-calibrated 37%) — fires LESS where needed, MORE where not.

## 3 — R3/R5 interaction
Orthogonal to R3 (OOD candles are high-vol/high-ADX, opposite end from chop; low overlap). R5 vol-estimate sample unchanged (reads candle series not roster), but ADX∝vol so killing low-ADX preferentially removes low-vol entries → survivors slightly higher-vol → R5 sizes them down (PnL effect not a clean subtraction).

## 4 — selection bias
IS chop bucket genuinely net-LOSING (−64.55%, not just low-return). BUT ADX∝vol; part of "chop no-edge" is "low-vol thin-edge" (LOVOL +11.2%/sharpe 0.17, weakly positive). The cleaner IS discriminator is **BTC_UP regime** (IS n=57, net −36.71%, sharpe −0.79) — directional/contextual, closer to the trend-wrong-way OOS failure than ADX-chop.

## 5 — trade-rate floor — F3 BORDERLINE-FAIL
thr=22 leaves **49 OOS survivors** (35/84 killed) — ONE below the ≥50 floor (the 30-49 band needs 7-seed validation, foreclosed by the no-multi-seed lock). Survivor net **−3.69%** (vs full +29.26%) — the gate DESTROYS the standalone OOS edge by killing post-Nov winners.

## 6 — MODAL VERDICT: NEGATIVE-DID-NOT-FIX (HIGH confidence)
The IS-ADX-regime split is real but does NOT transfer; the OOS OFF stretch is trend-wrong-way (high-ADX, wrong-direction). F4 fails, F3 borderline-fails, the gate kills winning trades. **RECOMMEND PIVOT before spending compute.**

## RECOMMENDED PIVOT (for the QR revision)
Pivot the OFF-regime detector from ADX-chop to a **BTC-trend-directional gate** — suppress XRP entries when the specialist's `_final_signed` OPPOSES the BTC trend sign, OR suppress in the BTC_UP regime where XRP's directional calls lose. **IS-CALIBRATABLE** (XRP IS BTC_UP n=57, net −36.71%, sharpe −0.79 — the IS evidence stands on its own; the OOS forensic just confirms it generalizes, so this is NOT OOS-tuning). This attacks trend-wrong-way head-on; ADX-strength is orthogonal to direction. Re-pre-register F4 (regime-breadth) + F3 (verify the BTC-trend gate doesn't over-kill below 50 OOS).

## Closing / QE+QR asks
- The single most important number: the pre-Nov OFF drag is in the ADX≥22 KEPT bucket (−38.61% of −42.77%) — any "F1 IS lift = gate works" read that ignores the pre-Nov KEPT-bucket PnL is reading the wrong number.
- Backtest-mode decision_log sink is mandatory or F2 is unreconstructable (the /091 no-op finding).
- F3 at ~49 is borderline-FAIL — do NOT renegotiate the floor post-hoc.
