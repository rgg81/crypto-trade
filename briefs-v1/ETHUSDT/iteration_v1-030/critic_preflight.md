# Phase 6.0 Critic Pre-Flight — iter-v1/030 (ETHUSDT)

OVERALL: PASS

Track: v1 single-symbol. Axis: AGREE_SCALE — multi-speed AGREEMENT conviction modulator on the
UNCHANGED iter-027 SMA-200 trend-state direction. Setup committed at 31ede2c8. Static / read-only
review; the iter-029 K=20 confirmation was not touched.

## Check 1 — LOOK-AHEAD (load-bearing kill criterion): PASS

Audited the AGREE_SCALE build block in lgbm.py L944-966 (inside the trend-strength index-build,
gated on `if self._enable_agreement_scale:`). EVERY panel member and the anchor are past-only,
built in the SAME `.shift(1)` style as the existing |dist_atr| build, on the open_time-keyed ETH
parquet:
- anchor (L950): `np.where(_cp > _sma, 1, -1)` where `_cp = close.shift(1)`, `_sma =
  close.rolling(200).mean().shift(1)`. = close[t-1] vs SMA200[t-1]. Past-only.
- s1 ema_cross(50,200): `close.ewm(span=50,adjust=False).mean().shift(1)` vs `span=200 .shift(1)`.
- s2 donchian(55): `high.shift(1).rolling(55).max()`, `low.shift(1).rolling(55).min()`, midline,
  compared to `_cp` (close[t-1]). Window spans [t-55..t-1]. Past-only.
- s3 tsmom(42): `_cp / _cp.shift(42) - 1` = close[t-1]/close[t-43]-1. Past-only.
- agreement (L965): `np.mean(_panel == _anchor_sign, axis=0)` in {0,1/3,2/3,1}.
- modulation (L966): `_abs_dist = _abs_dist * _agreement`; NaN (SMA/ATR warmup) stays NaN → gate
  falls back to conservative fire exactly as iter-027.

Modulation applied to the |dist_atr| SERIES at build time → BOTH the per-month q=0.40 threshold AND
the per-candle gated value derive from the modulated series (consistent). The lookup
`_compute_trend_strength` selects the row with `open_time == candle_open_time` exactly, reading the
pre-built row-t value — appending future candles cannot change a past row; the decision candle's own
bar is never used. The regression test exercises the append-future-candles invariant for the slowest
binding member (SMA-200/Donchian-55) at rel/abs 1e-12. 9 new tests + 33 pre-existing look-ahead =
42 passed, no regression.

## Check 2 — HYPOTHESIS-IMPLEMENTATION ALIGNMENT: PASS

Implements AGREE_SCALE (conviction MODULATOR — `_abs_dist *= _agreement`, direction sign UNCHANGED),
NOT the FE report's rejected direction-replacement. Panel math matches the QR's committed primitives
EXACTLY: ema_cross(50,200) == multispeed_breadth.py `ma_cross_sign`; donchian(55) ==
`donchian_breakout_sign`; tsmom(42) == `tsmom_sign`; anchor == `sma_sign(200)`; agreement formula ==
blend_agreement.py `np.mean(panel_arr == anchor, axis=0)`; `_abs_dist*_agreement` == `conv *
agree_with_anchor`; panel = P3 == agree_scale_robustness.py `P3_family_3` (the QR's recommended
panel, best Sharpe +0.56 / lowest top-2 0.0332). No SMA/EMA swap, no wrong horizon, no formula drift
— the IS evidence transfers.

## Check 3 — BYTE-IDENTITY (default-off): PASS

`enable_agreement_scale=False` default in the constructor, run_model, run_meta_model, and
`_spec_enable_agreement_scale=False`. Modulation strictly gated behind `if
self._enable_agreement_scale:`; when off, `_abs_dist` is the raw `np.abs(_dist_atr)` stored
unchanged. QE's real-parquet proof (off ⇒ bit-identical to raw |dist_atr|, 6873/7073 finite; on ⇒
2916 modulated, ON ≤ OFF everywhere, NaN positions identical) is consistent with the gating. Every
iter-016→029 run and v2/v3 stay bit-identical.

## Check 4 — SINGLE-AXIS DISCIPLINE: PASS

The iter-030 keyed branch clones the iter-027 M1 stack and changes ONLY the conviction multiplier:
direction (SMA-200 sign, ETH own close), label (fixed_horizon N=42, use_atr_labeling=False), exec
(atr_tp=100/sl=1.45, timeout 20160min), features (19-col HYBRID, asserted ==19), R-stack (R2
4.07/16.27/0.20, R3=0.70, R5 vt=0.3), M2 OFF — all FROZEN == /027. The gate still measures magnitude
vs SMA-200 (strength index built with sma_window=200, NOT ensemble distance). Panel windows
hardcoded (50/200, 55, 42), NOT Optuna-searched. Sole degree of freedom:
`_spec_enable_agreement_scale=True`. Single axis, clean.

## Check 5 — OOS-VIGILANCE: PASS

All four analysis scripts hard-filter `open_time < OOS_CUTOFF_MS (1742774400000)` with a leak-guard
assert and drop horizon-crossing IS entries (`drop_horizon_crossing_oos` + `assert
df["open_time"].max() < OOS_CUTOFF_MS, "LEAK GUARD FAILED"`). Forward returns computed on the full
frame but the leak guard is enforced at the ENTRY level — late-IS entries whose 42-candle label
window crosses the wall are dropped, so no OOS price enters any reported statistic.

## Check 6 — NAMESPACE / ROUTING: PASS

Single-symbol-ETH AGREE_SCALE branch (`iteration_label=="v1-030" and len(symbols)==1 and
symbols[0]=="ETHUSDT"`) and the pre-existing 5-symbol M2 branch (`set(symbols)==BASELINE_UNIVERSE`)
are mutually exclusive. The `V1_ITER030_*_M2_*` constants belong to the rejected M2 plan, documented
do-not-delete, never read on the single-ETH path. Universal single-symbol guard takes precedence
over legacy `set(symbols)==UNIVERSE` branches; with `_spec_enable_metalabel=False` the v1-030 ETH
cell takes the generic `run_model` dispatch, which threads `enable_agreement_scale`. Cohort isolation
asserted. M2 off → generic path.

## Check 13 — Anti-Pattern Static Scan (foundation): PASS

- A1 (train/test boundary lookahead): walk_forward.py L113 carries `train_end_ms = test_start_ms -
  embargo_ms` — no regression from the iter-v3/057 fix; iter-030 does not touch walk_forward.py.
- A2 (labeling-window σ_t lookahead): no forward-window in labeling.py; the σ path is past-only
  (`.shift(1)`) and NOT exercised by iter-030 (`use_atr_labeling=False`, fixed_horizon). Not modified.
- A3 (scaler fit on combined): no StandardScaler/fit introduced; LightGBM scale-invariant; the
  agreement primitives are pure shift/rolling, no fit.
- Change is purely additive (+286, 0 deletions), gated default-off; no foundation regression.

---

## Path Forward
OVERALL = PASS — backtest cleared to launch. (Path Forward mandatory only on BLOCK.)

## Launch note (advisory, not blocking)
Launch with `--n-trials 35` (per engineering report) so the ONLY delta vs iter-027 is the agreement
modulator (18 would confound the axis with a trial-budget change). Pre-registered falsifiers F1-F4 /
K1-K4 (brief §4) are well-formed and measurable IS-only on the EXPLORATION; F4/K4 (trade-count ≥
0.85× / drop ≤ 25%) correctly guards against the modulator degenerating into a hard veto (the
AGREE_GATE failure mode the QR rejected).
