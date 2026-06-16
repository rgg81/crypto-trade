# Diary — iter-v1/011 (BTCUSDT) — DIAGNOSIS (research-only, no backtest) — STRUCTURAL

**Axis:** crypto-QR IS-only diagnosis of the iter-010 IS→OOS generalization gap (first positive IS
+0.39 / OOS −1.48). Question: is the long-edge collapse REDUCIBLE OVERFIT (fixable via training
window / leaner model / regularization) or STRUCTURAL REGIME dependence? No backtest — output is a
strategic finding + the iter-012 direction.

**Finding: STRUCTURAL regime dependence, not reducible overfit. No IS-selectable model/feature/window
lever closes the gap. The edge is REAL but bull-regime-bound.**

### IS-only evidence (unifying metric = cross-IS-sub-period stability of the let-winners-run LONG edge)
- **Seed-deterministic, not a lottery:** the long edge is positive in exactly 6/9 IS sub-periods and
  negative in the SAME 3 (2022-H1, 2022-H2, 2025-Q1) for ALL 5 seeds.
- **Regime-explained:** LONG Sharpe **+2.47 in BULL** (200-SMA up) vs **+0.11 (dead) in BEAR**. The
  let-winners-run long book is a trend-persistence / reflexivity bet that structurally pays only in an
  up-trend — a crypto-native truth, not a bug.
- **The OOS −1.48 was PRE-PRINTED IS-side:** the most-recent IS sub-period (2025-Q1, nearest OOS) is
  one of the 3 negative regimes; OOS then opened in a correction. The OOS failure is an honest regime
  artifact (OOS began in a down-trend), NOT overfit.
- **Every fix lever ruled out ON IS:** TRAIN-WINDOW (longer ≠ more stable; 730d is WORST, frac_pos
  0.571) · LEANER/reg (frac_pos INVARIANT 0.667; the negative sub-periods stay negative) · BULL GATE
  (lifts headline via bull beta but DEGRADES every stability axis; reproduces the T3 inversion). The
  3 negative sub-periods cannot be removed by any IS-selectable model property.

### Strategic read (the campaign has turned)
The wall is no longer "BTC has no signal" (iter-001→008 noise floor) — it is "BTC's let-winners-run
LONG edge is real (+2.47 Sharpe in bull) but **unhedged in down-trends**." This is a RISK/SIZING
problem, not a signal problem. The model finds the long trend; it just shouldn't be at full size when
the trend is down.

### iter-012 direction (QR forward rec — a RISK ENGINEER primitive)
The only honest path to a smaller IS/OOS gap: a **regime-aware, vol-scaled long-bias SIZING primitive**
that **de-levers in down-trends** (e.g. scale position by 200-SMA-slope / trend-strength state, or a
trend-overlay on the existing R5 vol-target) — capturing the +2.47 bull edge while cutting exposure in
the bear/correction regimes where it bleeds. NOT a binary regime gate (ruled out §3.3 — fragile,
T3-inverts). NOT a model/feature/window change (ruled out §1–§2). Calibrated IS-only (the regime
signal is stateless: SMA slope sign / magnitude). This is the Risk Engineer's domain — the redesign's
explicit investment area.

**Note on the QR's literal iter-011 rec:** the QR suggested "re-run iter-010 byte-identical at K=5,"
premised on iter-010 being K=3. iter-010 ALREADY ran at K=5 (EXPLORATION cadence), IS +0.39 — so that
re-run is a no-op and is SKIPPED. The substantive output is the STRUCTURAL finding + the sizing path.

**OOS-vigilance:** all 3 QR scripts verified IS-only (strict pre-cutoff filter + leak-guard assert;
embargo ≥ horizon). The OOS −1.48 was used ONLY as the motivating fact; the diagnosis + iter-012 lever
are chosen entirely on IS sub-period stability — nothing fit/selected against OOS.

**Files:** `analysis/BTCUSDT/iteration_v1-011/{longedge_stability,regime_structural_test,regime_gate_subperiod_n9}.py`
(+ 7 CSVs), `briefs-v1/BTCUSDT/iteration_v1-011/research_brief.md`. QR commit `fd257476`.

**Next:** iter-v1/012 — Risk Engineer designs the regime-aware vol-scaled long-bias sizing primitive
(de-lever in down-trends), IS-only calibrated, on the iter-010 N9 let-winners-run config. Then K=5
screen. This is the first iteration with a genuine both-positive coherence SHOT — capture the bull
edge, survive the bear.
