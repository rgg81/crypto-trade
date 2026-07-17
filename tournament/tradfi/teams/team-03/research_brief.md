# team-03 research brief — stress-gated sector-residual reversal

Family: `t03-sector-residual-reversal-v1` (approved, registry pass-1).
Status: DESIGN COMPLETE — spec FROZEN for QE implementation. 13 material experiments
(exp-002 … exp-014 in `experiments.jsonl`), budget cap 40, target 25.

## 1. Mechanism & economic rationale

Sector-relative short-horizon mean reversion, exposure-gated to market stress states.

Core mechanism (unchanged from registration): large idiosyncratic single-name moves against
the sector basket are dominated by price-pressure flows and overshoot; they revert as
liquidity providers replenish inventory. We long idiosyncratic losers / short idiosyncratic
winners vs their sector, at a 5-day horizon.

What the IS data added (exp-002 … exp-007): in this 69-name US mega-cap universe, 2010-2024,
the UNGATED premium is real but tiny (gross Sharpe <= 0.4 at any horizon) and lives in the
small-dislocation band (tails anti-revert — news drift; exp-005), so it cannot fund 6 bps/side
at daily cadence — best ungated net was −0.53. The registered expected_regime_behavior
anticipated exactly where the premium concentrates: "earns best in choppy and high-dispersion
tapes and in post-stress snapback windows (elevated VIX episodes create forced flows and wider
overshoots)". Conditioning exposure on that pre-registered state flips the book decisively
positive (exp-008/009): liquidity provision pays only when liquidity is scarce; in calm tape
the premium is arbitraged below cost.

Family-fidelity note (for the Critic): the cross-sectional mechanism is the registered one —
a single sector-residual reversal book. VIX enters ONLY as a scalar 0/1 exposure switch, an
in-family risk overlay implementing the registration's own expected-regime clause. This is
NOT menu family #7 (VIX-conditional regime books = switching between DIFFERENT cross-sectional
mechanisms by state), which remains unclaimed by any team. No pivot was used.

## 2. FROZEN SPECIFICATION (QE implements exactly this — zero research freedom)

`build_raw_weights(pn, aux)` — pure, deterministic; uses ONLY `pn['close']`, `aux['vix']`,
`aux['sector_map']`. `aux['seed']` unused (no randomness). Tickers = `pn['close'].columns`
at runtime, never hard-coded. No file I/O, no network, no subprocess.

Reference implementation the QE must transcribe: `scratch_lib.build_raw` called with EXACTLY
`L=5, skip=0, vol_std=True, vol_win=63, transform="blend", winsor=3.0, ema_span=5, z_in=0.0,
exhaust=False, vix_mode="pct", vix_thr=0.85, sector_demean=False, inv_vol=False, peers_min=2,
min_hist=63` (see `scratch_run.py` exp-014 invocation). Step by step:

1. **Returns** `close = pn['close']`; `r = close/close.shift(1) − 1`.
2. **Active mask** `hist = r.notna().rolling(126, min_periods=1).sum()`;
   `active = close.notna() & (hist >= 63)`.
3. **Sector residual** `rA = r.where(active)`. Per sector `sec` (group tickers by
   `aux['sector_map']`, missing ticker → group "Unknown"), per day and name i:
   `peer_mean_i` = mean of non-NaN `rA` over the sector's OTHER names;
   `peer_cnt_i` = that count; `uni_mean_i` = same over ALL other panel names.
   `basket_i = peer_mean_i if peer_cnt_i >= 2 else uni_mean_i` (denominators guarded
   with max(cnt,1)). `e = rA − basket` (NaN where `rA` NaN).
   Exact vectorized recipe: `scratch_lib.sector_residual` — transcribe it.
4. **Signal core** `R = e.fillna(0).rolling(5, min_periods=1).sum().where(active)`;
   `sigma = e.rolling(63, min_periods=40).std()`; `core = R / (sigma * sqrt(5))`;
   `s = −core`.
5. **Cross-sectional transform (fixed 50/50 blend, no tuning)** on `s.where(active)`:
   `z = ((s − rowmean)/rowstd).clip(−3, 3)` (pandas skipna mean/std, ddof=1);
   `pct = s.rank(axis=1, pct=True)` (pandas default average method, NaN excluded);
   `w0 = 0.5*(z/3) + 0.5*((pct − 0.5)*2)`.
6. **Stress gate (BEFORE smoothing — order is load-bearing)**
   `v = aux['vix'].reindex(close.index).ffill(limit=5)`;
   `pctile = v.rolling(252, min_periods=126).rank(pct=True)`;
   `g = (pctile > 0.85)` as float, `NaN → 0`; `w1 = w0.mul(g, axis=0)`.
7. **Smoothing** `w2 = w1.ewm(span=5, min_periods=1).mean()`.
8. **Mask & emit** `return w2.where(active)` — NaN = flat; engine owns gross-norm,
   caps, shift(1), costs, vol-target.

Missing data / ragged starts: names enter the book only via the active mask (>= 63 returns in
trailing 126 days); a missing bar day contributes 0 to the rolling residual sum and NaN weight
that day (engine flats it); VIX gaps are forward-filled at most 5 days, unresolvable gate NaN
means gate OFF (flat book). Never forward-fill prices.

## 3. Parameter provenance & plateau evidence (all numbers from `te.run_is` scratch evaluator)

| Axis | Chosen | Pre-registered neighborhood tested | Net Sharpe @1x across neighborhood |
|---|---|---|---|
| Residual horizon L | 5d | 3,4,5,6,7 (exp-010/012/013) | 0.38 – 0.62 (gated variants) |
| EMA span | 5 | 3,4,5,6,8 (exp-010/013) | 0.40 – 0.62 |
| Gate percentile | 0.85 | 0.80, 0.825, 0.85, 0.875, 0.90 (exp-009/012/013) | 0.42 – 0.80 |
| Transform | blend 50/50 | z (0.457), rank (0.617), blend (0.568) — all with vol_std | all positive |
| Vol standardisation | on | on/off at multiple cells (exp-011/012/013) | +0.03 … +0.06 lift |

Not chosen (documented negatives): tail-thresholding z_in (hurts — tails anti-revert, breadth
floor breach; exp-005), exhaustion gate (exp-007), inverse-vol sizing (−0.60; exp-011),
sector-demean of weights (−0.07; exp-011), skip-day (−0.36; exp-011), level-VIX gate
(knife-edge at 24/25; exp-009), L>=10 (negative; exp-003/010).

Selection rule (pre-registered in exp-012/exp-013 lines, applied verbatim): among plateau
members — cost-robust Sharpe, all sub-periods positive, bear regime not deeply negative.
Blend chosen over pure rank: gives up 0.049 Sharpe @1x (0.617 → 0.568) to improve bear-regime
Sharpe from −0.46 to −0.15; rank's bear was −0.22 … −0.95 across its plateau. Gate 0.85 kept
over the locally-better 0.825 (0.804) — plateau center over peak, per discipline.

## 4. Expected IS metrics (exp-014, exact frozen spec; QE's team-run must reproduce)

| Metric | @1x | @2x |
|---|---|---|
| Net Sharpe (monthly, √12) | 0.568 | 0.439 |
| Max drawdown | −0.325 | −0.370 |
| Ann. turnover | 15.5 | 15.5 |
| Median names L/S | 25 / 23 | — |
| Total return / months | +202.5% / 174 | — |
| Regime Sharpe bull/bear/chop | 0.50 / −0.15 / 1.17 | — |
| Sub-periods 2010-14 / 15-19 / 20-24H1 / 15-24H1 | 0.431 / 0.772 / 0.525 / 0.631 | — |

Breadth floor: PASS (25/23 >> 5). Cost sensitivity: 2x retains 77% of Sharpe (turnover 15.5/yr
is the design's cost armor). Book is ON ~15% of days (top-VIX-percentile states), flat
otherwise; median-breadth statistic is computed over active days by the engine.

## 5. Falsifier disposition & risks

Registered falsifier: net IS Sharpe < 0.3 @1x across the L 2-7 / smoothing 2-5 plateau, OR
2015-2024 sub-window <= 0, OR breadth floor unmeetable. Outcome: NOT triggered for the gated
family (plateau 0.38-0.62; 2015-2024 = 0.631; breadth 25/23). The UNGATED family corner IS
dead (best −0.53) and is reported as such in is_report.md — the deployable edge exists only
inside stress states, which the registration pre-declared as the edge's habitat.

Honest risks for the final report: (1) gate ON-fraction ~15% → effective sample ~26 active
months-equivalent; Sharpe noise floor is material. (2) bear-regime Sharpe mildly negative
(−0.15): in a sustained crash the book bleeds slowly; it earns in the chop/correction states
around it (+1.17). (3) holdout VIX distribution may differ from IS; percentile gate (not
level) is the defense against secular vol-regime drift.

## 6. QE checklist

- Transcribe `scratch_lib.build_raw` at the frozen params into `strategy.py:build_raw_weights`;
  simplify away dead branches (z_in/exhaust/sector_demean/inv_vol/skip/level-gate) but do NOT
  alter numerics or step order (gate before EMA; masks as specified).
- `test_strategy.py`: determinism, future-corruption self-check (corrupt bars after day T,
  assert weights <= T unchanged), no-hardcoded-tickers, NaN-handling on ragged starts.
- `cli.py team-run --team team-03` → `out/is_metrics.json` must match §4 (bit-identical to
  exp-014 if transcription is exact); then `cli.py audit --team team-03`.
- No re-tuning of ANY parameter. Deviations = escalate back to QR, never improvise.
