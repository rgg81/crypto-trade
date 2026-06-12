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

## Phase 7.4 — Post-mortem (corrected run)

### Context read
- Outcome (comparison.csv, 09:30): GATED IS daily-Sharpe **0.3007** / OOS **0.5952**, ratio 1.98; ungated /088 IS 0.3783 / OOS 0.5158. Gate removed **40 net IS trades** (219→179, 18.3%) and 9 OOS (84→75). IS MaxDD **worsened** 26.29%→41.82%.
- Eng-report headline: projection (+0.81 IS) falsified by the real backtest (−0.078 IS); root cause = sequential slot-freeing cascade. Confirmed and extended below.
- Brief F1 (IS≥+0.578, Δ≥+0.20): **FAILS HARD** — actual 0.3007 is below both the floor and the ungated 0.3783.

### (1) Why IS Sharpe FELL when the gate removed net-losing entries
The EDA was numerically correct in isolation — the 57 IS BTC_UP entries are genuinely net-losing (−36.71%, WR ~0.35). The error was treating a sequential single-symbol backtest as a *static set* you can subtract from. Two mechanisms broke the projection:

- **Slot-freeing replacement.** When the gate suppresses a BTC_UP entry at candle T, the position slot is freed, so the walk-forward enters on a *later* candle that was previously blocked by the open T-position. The engineer's `projection_divergence.py` counts **25 IS replacement trades** at **WR 0.280** (below the gated mean 0.447) contributing **−24.33 wpnl** — strictly worse than the −17.10 removed. Net IS wpnl moved **−7.23** vs the **+5.21** projected: a **−12.44 projection error**.
- **Suppression cascade.** Gross removed was **65, not 57** — replacements freed by earlier BTC_UP suppressions *also* landed in BTC_UP and got re-suppressed, a multi-round cascade the static filter could not see.

The mechanism is purely accounting/path-dependence, not a model change. The reshuffled 179-trade roster is a *different, net-worse* roster than "088 minus 57 losers." MaxDD blowing out to 41.82% is the tell: removing 65 entries and inserting 25 low-WR replacements re-clustered the loss path and removed the diversifying winners that were previously dampening the equity curve. **Generalizable and now load-bearing: an entry gate's effect on a sequential backtest is NEVER the subtraction of the gated entries' PnL — the slot reallocation must be simulated by the backtest itself. "Zero concurrent overlaps" justifies nothing; the binding condition is "suppressing an entry never frees a slot," which is unsatisfiable in a single-position model.** This vindicates the no-side-scripts directive at the mechanism level, not just as policy.

### (2) Did the model itself change? NO — confirmed
`diff feature_importance_*_092.csv feature_importance_*_088.csv` is **byte-identical** (48 rows, `vol_atr_14` rank 1 @ 9531.10 gain, `trend_adx_14` rank 2, `stat_autocorr_lag5` rank 3, identical down to `eth_vs_btc_ret_ratio_30` @ 0.0 rank 48). This is exactly as designed: the BTC-regime kill is a **post-aggregator RULE gate** — it filters the *signal stream* after `get_signal`, so the per-month LightGBM fits, Optuna trajectories, and gain ledger are gate-independent. The model trained on identical data both runs; only the realized trade roster differs. So nothing here is an ML-overfit story — it is 100% a position-accounting story. (Side note for the record: `btc_funding_spread_30_90` is an in-model feature at rank 9, and BTC-context is already partially priced into the model's signal — the external gate is redundant with information the tree already has, which is part of why it adds noise rather than edge.)

### (3) Is XRP's regime-conditional edge harvestable by a BTC-trend kill?
**No — not by entry suppression, on this evidence.** The IS BTC_UP discriminator is real (the split exists and is directional, which is why I steered /092 here from the failed ADX-chop axis in the Phase 4.5 advisory). But "real on a static IS split" ≠ "harvestable by a sequential gate," because:

- The harvest mechanism (suppress-the-loser) is defeated by slot-freeing: you don't get the counterfactual "those candles flat," you get "those candles replaced by worse entries."
- The IS bucket that *actually* drags is not chop and not cleanly BTC_UP — it overlaps the high-ADX wrong-direction-in-trend bucket I flagged at Phase 4.5 (pre-Nov OFF losses lived in the ADX≥22 KEPT bucket at 27% WR). A coarse binary BTC-trend kill can't separate "wrong-direction-in-BTC_UP" from "right-direction-in-BTC_UP" — and XRP has winning BTC_UP trades too, which the gate also kills.

The edge, if any, is **directional-conditional** (does XRP's signed call agree with BTC's trend?), not **regime-binary** (is BTC up?). A binary kill throws away the winning half of the regime. **My read: the BTC-regime-binary-kill axis for XRP is CLOSED** (concurs with the disposition). What is NOT closed is encoding the BTC interaction *inside the model* as a feature so the tree can split winners from losers within BTC_UP, instead of an all-or-nothing external veto.

### (4) Forward ideas — feature families NOT touched in the last 5 XRP-adjacent iterations
The last 5 XRP-adjacent iters (/088 base, /091 R-CONV, /092 ADX-kill→BTC-kill, plus the two prior gate axes) all ran the **same frozen 48-feature model** and only bolted on post-aggregator RULE gates. Zero feature-engineering has touched the XRP head. Three concrete model-side directions, in priority order:

1. **`btc_trend_interaction_signed` (composed, in-model).** `stat_return_5 × sign(btc_ret_42 − 0.067)` — the *exact* discriminator the gate tried to apply externally, but as a feature so the tree can carve winners from losers *within* BTC_UP at a single split instead of vetoing the whole regime. Per the proven-engineered-features finding, composed sign-interactions encode exactly what depth-5 trees can't compose. Expect |IC|~0.3–0.5 with `stat_return_5` (use the Category-2 importance≥30 carve-out, not the strict |IC|<0.5 gate). Predicted IS importance rank 8–15; this is the cleanest "do it inside the model" answer to (3).
2. **Cross-sectional XRP-vs-BTC relative strength, return-space (not OHLCV-level).** `xrp_ret_42 − btc_ret_42` z-scored, and `xrp/btc` realized-vol ratio. NOTE: the v3 cross-asset *OHLCV-derived* axis is CLOSED after 6 failures — but those were price-level ETH/BTC primitives in a BTC-excluded universe. v1 INCLUDES BTC, and a *return-difference relative-strength* feature is a different object (it directly encodes the "XRP decoupling from BTC" structure that the regime split is a crude proxy for). Gate this on the rolling-window T5 importance test; drop after one verdict if rank 14/14.
3. **Funding/OI microstructure already half-present — extend it.** `funding_rate_zscore_30` (rank 20) and `oi_delta_30_z90` (rank 7) are *already in the model and oi_delta is top-7*. XRP has historically funding-sensitive squeezes. Add `funding_rate_zscore_30 × sign(oi_delta_30_z90)` (a crowding-direction composite) — this is a feature family (OI×funding interaction) genuinely unused, and it builds on a rank-7 feature already proven informative for this head rather than importing a cold cross-asset primitive.

### What this iteration confirms / refutes about prior LM Master advisory
The Phase 4.5 advisory's **pivot recommendation was right to abandon ADX-chop** (ADX is strength not direction) and right that the IS BTC_UP split was the cleaner discriminator. But it **under-weighted the harvest-mechanism risk**: I recommended the BTC-regime gate as IS-calibratable and "attacks trend-wrong-way head-on," and it does target the right bucket — yet I did not flag that a *binary entry-suppression* gate cannot harvest a directional edge in a sequential backtest (slot-freeing + winners-in-regime both defeat it). Honest scorecard: **axis-redirection correct, harvest-mechanism prediction wrong.** The lesson I carry forward: when I recommend an entry gate, I must state whether the edge is harvestable by *suppression* vs only by *in-model feature encoding* — and for directional/regime edges with winners-in-regime, default to feature encoding (idea #1), not a veto gate.

### Closing note for Critic (Phase 7.5)
- **Verdict is uncontested NEGATIVE; no ML anomaly to chase.** Model is byte-identical to /088 (Check on feature_importance will show no training change) — this is purely a roster/accounting outcome, so the usual overfit/leakage checks have no surface here.
- One thing worth a glance: IS MaxDD **worsened** 26.29%→41.82% while OOS MaxDD improved — confirm the IS DD blowout is the reshuffled-roster loss-clustering (it is, per the monthly_pnl path: 2024-03 −16.00% and 2025-01 −16.12% concentrate the new loss path), not a sizing/R5 artifact (R5 fire-rate is 0.0 both windows per comparison.csv, so R5 is not involved).
- The pre-registered F2 band (20–45% suppressed) came in **below** at 18.3% IS — that is itself evidence the suppression was less subtractive than modeled (cascade replacements net the count *up* toward 179). No renegotiation; F1 already fails. Recommend closing the BTC-regime-binary-kill axis for XRP and routing the next XRP iter to feature-engineering (idea #1) per the per-symbol regime-specialist feature-MODAL mandate.
