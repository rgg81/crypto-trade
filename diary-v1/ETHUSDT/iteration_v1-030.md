# Diary — iter-v1/030 (ETHUSDT) — EXPLORATION — AGREE_SCALE conviction modulator — NEGATIVE (IS inverted; EDA proxy did not transfer)

**Axis:** AGREE_SCALE — the DETERMINISTIC de-concentration lever (SOTA forecast-combination; AQR
TSMOM / Carver / Zarattini-2025). Keep the iter-027 SMA-200 trend-state DIRECTION byte-identical;
MULTIPLY the conviction-gate quantity `|close−SMA200|/ATR14` by a past-only AGREEMENT fraction over
panel P3 {ema_cross(50,200), donchian(55), tsmom(42)} vs the anchor sign. Single axis vs iter-027.
K=5 EXPLORATION, n_trials=35. (Promoted to PRIMARY de-concentration path after iter-029 killed the
learned-M2 alternative.)

**Result (K=5):** IS Sharpe **−0.0866** / OOS **+0.2372** (ratio −2.74). 79 IS / 29 OOS trades (≈ iter-027
82/32 — trade count preserved, F4 PASS). IS top-2 conc 272% / OOS top-2 **139%**; OOS winners 10/29,
MaxDD 4.64%.

## Verdict: EXPLORATION-NEGATIVE. Fails the both-positive PRIMARY gate (IS −0.09 < 0); fires pre-registered K2 (IS regresses >0.05 below iter-027 +0.6336 — it regressed −0.72).

The IS-only EDA predicted IS Sharpe +0.44→**+0.56**; the real backtest delivered **−0.09**. The proxy did
NOT transfer — a −0.65 miss. iter-027 (IS +0.6336/OOS +0.0560) REMAINS BASELINE_V1_ETHUSDT.

## Forensic — WHY the EDA inverted (the load-bearing lesson)
iter-027 and iter-030 differ ONLY in the agreement modulation of `conv` (same model, same trend-state
direction, same R-stack, same trade count ≈80 IS). Yet IS flipped **+0.63 → −0.09** while OOS rose
**+0.056 → +0.24**. Decomposition:
- The EDA proxy trades EVERY conv-gated candle with the deterministic SMA200 direction × signless 14d
  forward return. The real backtest only trades candles the **LightGBM model signals** (entry timing),
  then applies the trend-state direction + the (now modulated) gate. The proxy cannot model the
  model's entry selection — that is the whole gap.
- **AGREE_SCALE removes the model's LOW-agreement, IS-WINNING entries.** The LightGBM has learned IS
  setups, some in low-agreement (chop) regimes where it found IS edge; AGREE_SCALE shrinks their
  conviction below the gate and drops them, keeping high-agreement entries that are IS-UNprofitable.
  So the modulator FIGHTS the model's learned IS edge → IS inverts negative.
- In OOS the model's learned edge does NOT generalize (the founding campaign problem). Removing it and
  keeping only high-agreement (multi-speed-confirmed) entries HELPS — OOS rises to +0.24 AND
  de-concentrates (top-2 438%→139%). **AGREE_SCALE behaves as a REGULARIZER that de-correlates from
  the model's overfit IS edge** — IS−/OOS+ by construction.

This is a genuine regime effect, NOT a bug: the OOS coherence + strength rule out randomness, and the
look-ahead suite (9 tests) + the real-parquet byte-identity proof rule out a wiring leak.

## What's REAL vs not
- REAL/intriguing: OOS +0.24 is the **campaign-best ETH OOS** AND the most de-concentrated (top-2 139%
  vs iter-027 438% / iter-028-K5 135% / iter-029-K20 186%). The multi-speed AGREEMENT primitive does
  carry OOS signal and DOES de-concentrate — the de-concentration HYPOTHESIS is partly vindicated.
- FAIL: it gets there by sacrificing the IS (−0.09). Under the generalization-first gate, both-positive
  is PRIMARY and IS<0 is a hard fail. The OOS +0.24 must NOT be chased (cardinal rule — never overfit
  OOS; an IS−/OOS+ config is the inverse overfit, not a generalizing edge).

## Engine note (defect found + FIXED)
The run exited code 1 on `UnboundLocalError: results_a030` at L12392 — a post-report m2_passed
annotation block keyed on `iteration_label == "v1-030"` but NOT universe-guarded, so the single-symbol
ETH path (no M2 / no results_a030) crashed it. FIXED: added `and set(symbols) ==
set(V1_BASELINE_UNIVERSE)` guard (the legacy 5-symbol M2 path's own condition). The crash was AFTER
comparison.csv + IS/OOS reports were written → headline metrics are valid; only the post-report
m2_passed annotation + methodology rows (DSR/PSR/ADF/IC, not needed for an EXPLORATION screen) were
skipped. No re-run needed (IS<0 verdict is determined by the valid headline metrics).

**OOS-vigilance:** axis + panel were chosen from IS-only EDA (cutoff-asserted, leak-guarded, Critic 6.0
PASS); OOS seen for the first time in this Phase-7 eval. The NEGATIVE verdict is on the IS Sharpe sign,
NOT an OOS fit.

**Next:** Critic Phase 7.5 (EXPLORATION-NEGATIVE + Path Forward). De-concentration mandate continues —
the AGREE_SCALE forensic says entry-side conviction reordering trades IS for OOS; the next lever should
de-concentrate WITHOUT inverting IS. Leading candidate (Critic's iter-027 next-step #1): an EXIT-side
de-concentrator (partial-profit / second let-winners-run band) — convert the one big 14d trend-capture
into several realized sub-trades — orthogonal to the entry-side AGREE_SCALE and to the model's IS edge.
