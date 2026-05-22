# Iteration iter-v3/021 — Diary

## Decision: EXPLORATION-NEGATIVE (clean)

Universe expansion (V3_MODELS 3 → 5; +HBARUSDT +AVAXUSDT) failed unambiguously. OOS Sharpe **-0.4380** (Δ -0.83 vs iter-v3/018 anchor +0.3869) is the **WORST OOS in v3 catalog history** on the iter-v3/018 anchor basis (prior worst: iter-v3/016 XGBoost at -2.53 was on a different baseline level). Both new symbols are net drag IS+OOS: HBAR -36.5% IS PnL / -10.9% OOS PnL; AVAX -49.2% IS PnL / -12.1% OOS PnL. Together they alone subtract -85.7% IS PnL from the portfolio. The trade-rate floor cleared (144 ≥ 130) but at the cost of edge — the brief's mechanism story ("denominator expansion dilutes concentration without removing edge") was structurally falsified at the symbol-fit layer: the new symbols' per-symbol heads at n_trials=35 split 5 ways did NOT produce non-trivial positive contribution. Saturation falsifier from §4.4 row 5 FIRES (IS trades 311 > 269 upper bound; the axis effect was LARGER than predicted but all excess trades unprofitable). Methodology of the run is clean — all 12 standard methodology checks PASS or PASS-with-Falsifier-fired (Critic FINAL `f5b89a3`).

NOT a CONFIRMATION-bundle candidate. The universe-expansion mechanism with HBAR+AVAX is CLOSED at the catalog level (not the entire universe-expansion axis — different symbol candidates ATOM/FIL/ALGO are deferred to future MEDIUM-priority retest only AFTER higher-priority structural axes are exhausted). Cadence #3 of 10 in the post-bootstrap cycle.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding HBARUSDT + AVAXUSDT to V3_MODELS (universe 3 → 5 symbols; 7-primitive risk gate stack BYTE-IDENTICAL to iter-v3/018 anchor; per-symbol cap DISABLED at first commit per iter-v3/020 PATH C closeout; 13 V3_FEATURE_COLUMNS UNCHANGED) will dilute single-symbol concentration mechanically without removing edge from any incumbent symbol, because the universe-expansion mechanism is denominator expansion. Predicted IS Sharpe band [+0.30, +0.55] median +0.40; predicted OOS Sharpe band [+0.45, +0.70] median +0.55."

**Spec (locked, single-axis variation):**
- V3_MODELS expanded 3 → 5: + ("E (HBARUSDT)", "HBARUSDT") + ("F (AVAXUSDT)", "AVAXUSDT")
- REQUIRED_GAP updated 66 → 110 = (21+1) × 5 (formula-derived; runtime assertion verified at run.log)
- enable_per_symbol_cap = False (revert from iter-v3/020 PATH C closeout; implementation kept in repo at zero revert cost)
- ITERATION_LABEL = "v3-021"
- 13 V3_FEATURE_COLUMNS UNCHANGED (funding absent; tbr_zscore_30 absent; vwap_dev_50 absent)
- 7-primitive risk gate stack byte-identical to iter-v3/018 (zscore=2.0, adx=20.0, btc_pct=15.0, ATR 2.0/1.0)
- Ran in EXPLORATION mode: --exploration --seeds 1 (1 outer × 1 inner × 35 n_trials × 5 symbols = **175 fits per cell**; colsample_bytree=1.0 hardcoded). Second EXPLORATION at the n_trials=35 default per `feedback_v3_exploration_n_trials_35.md`.
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS.

This was iter-v3/021, the **first universe-expansion EXPLORATION** in v3 catalog (13 unique axis representations after this iteration; cadence #3 of 10 in the post-bootstrap cycle).

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor (multi-seed mean) | iter-v3/021 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | **+0.3183** | **-0.0605** (within predicted [+0.30, +0.55] lower bound) |
| OOS monthly Sharpe | +0.3869 | **-0.4380** | **-0.8249** (below predicted [+0.45, +0.70] entire band; **worst OOS Δ in v3 anchor-basis history**) |
| OOS/IS Sharpe ratio | 1.02 | **-1.376** | sign flip |
| IS n_trades | 172 (mean) | **311** | +139 (above brief §2.3 predicted 269 upper bound — **saturation falsifier FIRES**) |
| OOS n_trades | 90.5 (mean) | **144** | +53.5 (clears 130 trade-rate floor) |
| IS MaxDD | 21.86% (mean) | **42.62%** | +20.76pp |
| OOS MaxDD | 27.74% (best seed 42) | **37.34%** | +9.60pp |
| Win rate IS / OOS | — | 30.55% / 34.03% | OOS WR > IS WR |
| Total OOS PnL | +∼7% (mean) | **-15.14%** | HBAR + AVAX drag drives portfolio negative |
| DSR | 0.0 (n_trials=1500) | **0.0** | clean honest readout at n_trials=175 |
| PSR | 0.9936 | **0.0001** | collapsed (consistent with negative observed Sharpe at n_trials=175) |
| PBO mean | 0.0892 | 0.1074 | TRX/2025-Q4 + HBAR/AVAX cell carry-forward; mean aggregator clean < 0.40 |
| n_eff | 25 (CONFIRMATION) | **19** | maintained from iter-v3/020 (validates n_trials=35 default; consistent regime) |
| n_trials | 1500 (CONFIRMATION) | **175** | EXPLORATION default (5 sym × 35 trials = 175) |

### Per-symbol attribution

| Symbol | IS weighted_pnl | IS PnL contribution | OOS weighted_pnl | OOS n_trades | OOS WR | Concentration_pct |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | (positive) | +38.4% | -10.4651 | 36 | 36.1% | 69.10% |
| LDOUSDT | (positive) | +41.9% | **-13.2373** | 13 | 38.5% | 87.41% |
| TRXUSDT | (negative) | -19.3% | +5.7235 | 37 | 37.8% | -37.79% |
| **HBARUSDT** | (negative) | **-36.5%** | +4.4733 | 27 | 29.6% | -29.54% |
| **AVAXUSDT** | (negative) | **-49.2%** | -1.6386 | 31 | 29.0% | 10.82% |

**HBAR + AVAX subtract -85.7% IS PnL together.** They are the dominant IS drag — the brief's prediction that the n_trials=35 budget split 5 ways would still produce non-negative per-symbol contribution was structurally wrong. On OOS the dominant negative source is LDO (-13.24 weighted_pnl on 13 trades) — same lottery flag carried forward from prior iterations. BCH OOS turned negative for the first time in the v3 catalog at -10.47 weighted_pnl; the brief did not predict this would happen as a side effect of universe expansion.

### Saturation falsifier verification (per `feedback_axis_saturation_predictor.md`)

| Predictor | Lower bound | Upper bound | Observed | Triggered? |
|---|---:|---:|---:|---|
| IS trade band (brief §2.3) | 186 | 269 | **311** | FIRES (over upper) |

The axis effect was LARGER than the QR's behavioral-effect predictor suggested. The brief assumed proportional scaling (3 sym × 100 trades + 2 sym × 65 trades ≈ 230) with ±18% saturation band. Observed +42 trades over upper bound means the new symbols emit MORE trade volume than the proxy ratio predicted, but **all excess trades are unprofitable**. This is symmetric to iter-v3/014's ADX-axis falsifier: the axis propagated cleanly, but the propagation direction was wrong.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS (Critic FINAL `f5b89a3`). Look-ahead audit verified by past-only feature regeneration through `features_v3` module + funding fetcher writing per-symbol cache. Embargo width REQUIRED_GAP = 110 = (21+1) × 5 correctly scaled with universe expansion (sub-fix 2 propagated to validation_v3.py + runtime assertion). Reproducibility stamp clean (Setup `6446d5d`, gate `61f1b35`, brief `6b84934`, EDA `a360251`). Single-axis discipline preserved: V3_MODELS expanded; cap disabled (revert from iter-v3/020); ITERATION_LABEL=v3-021; 13 V3_FEATURE_COLUMNS unchanged. {BCH, LDO, TRX, HBAR, AVAX} ∩ V3_EXCLUDED_SYMBOLS = ∅.

- **n_trials=35 EXPLORATION default validates positively at iter-v3/021 (PRELIMINARY-VALIDATED through iteration #2).** n_eff=19 maintained from iter-v3/020 — consistent regime across 2 EXPLORATIONs. PSR=0.0001 collapses honestly when observed Sharpe is materially negative; the metric is now informative rather than saturated. DSR=0.0 reflects honest deflation. Wall-clock 23 min (well within 2h cap). Two data points confirm n_trials=35 default operates in the honest deflation regime; iter-v3/022-023 will continue to record the trajectory before the default is empirically validated.

- **Trade-rate floor mechanics validated.** OOS bundle = 144 ≥ 130 floor — the QR's pre-commit reasoning ("2-symbol expansion brings bundle to ~198 — comfortable cushion") was directionally correct on volume but fundamentally wrong on edge. The floor was satisfiable but at the cost of edge.

## What Failed

- **Falsifier 1 (NEGATIVE indicator) fires unambiguously** per brief §4.4 row 5: IS Sharpe Δ -0.06 within predicted band BUT OOS Sharpe -0.4380 < anchor -0.10 threshold (anchor +0.2869); roster non-identity (5 sym ≠ 3 sym); saturation falsifier FIRES at 311 IS trades > 269 upper bound. Three §4.4 row 5 conditions met cleanly. Verdict triggers via OOS collapse condition (worst-in-v3-catalog at -0.83 vs anchor) + roster non-identity. Clean EXPLORATION-NEGATIVE — no NULL-RESULT (which would require bit-identical roster, distinguishing from iter-v3/012); no PROMISING-MECHANICAL (which would require bit-identical roster on retained symbols).

- **HBAR + AVAX both deeply negative IS+OOS.** HBAR weighted_pnl IS -36.5% / OOS -10.9%; AVAX weighted_pnl IS -49.2% / OOS -12.1%. EDA's **"lowest mean |corr|" metric (HBAR 0.41, AVAX 0.50) captured price-level return diversity, NOT signal diversity in the 13-feature statistical-moments space.** The 13-feature stack identified existing-symbol patterns; HBAR and AVAX have different mid-cap altcoin return regimes that LightGBM at n_trials=35 split 5 ways cannot fit. Mechanism: the per-symbol heads for HBAR/AVAX were UNDERFIT relative to BCH/LDO/TRX whose patterns the 13-feature set was designed against (via iter-v3/007-013 evolution).

- **OOS Sharpe Δ -0.83 is the worst in v3 anchor-basis history.** Brief §1 predicted [+0.45, +0.70] OOS Sharpe band — observed -0.4380 missed the entire band by -0.89 from the lower bound. The QR's reasoning that "the new symbols add their own model fits which are independently learned by per-symbol LightGBM heads" was structurally correct (per-symbol architecture preserved) but ignored the budget-per-symbol arithmetic: 175 fits per cell ÷ 5 symbols = 35 fits/symbol on the new entries vs 1500 fits per cell ÷ 3 = 500 fits/symbol on incumbents in BOOTSTRAP CONFIRMATION.

- **BCH OOS turned negative for the first time** (weighted_pnl -10.47). Brief §1 implicitly assumed incumbent symbols' per-symbol contribution would be preserved by per-symbol architecture. Observed: BCH was the strongest IS contributor (+38.4% PnL) but reverted to NEGATIVE OOS. The 5-symbol training context shifted Optuna's hyperparameter selection toward regions that overfit BCH's IS pattern — a side effect of the broader cell-level Optuna search at n_trials=35 with a lower budget per symbol.

- **OOS MaxDD increased +9.60pp** from 27.74% (anchor seed 42 best) to 37.34%. Brief §5 predicted concentration dilution would FLATTEN the per-symbol PnL distribution (lower MaxDD via concentration reduction). Observed: dilution failed; new symbols added their own losses without compensating gain.

- **EDA composite scoring methodology was flawed.** EDA composite formula = 0.30 × complementarity (1 − mean_abs_corr_baseline) + 0.30 × data_quality + 0.25 × liquidity + 0.15 × trade_rate_proxy. The 30% weight on complementarity was based on the assumption that low return correlation implies signal complementarity — which is decorrelated from feature-space signal complementarity in the 13-feature statistical-moments space. The EDA composite ranking was directionally misleading: HBAR (rank 1, composite 0.756) had the worst IS contribution (-36.5%) and AVAX (rank 2, composite 0.740) had the second-worst IS contribution (-49.2%).

## Critical Lessons

(a) **EDA correlation ranking is necessary but not sufficient for symbol selection.** Mean-absolute-correlation against incumbents captures price-level return diversity — orthogonal to signal diversity in the 13-feature statistical-moments space. Future symbol-candidate EDAs MUST include either (i) per-symbol IS feature-mean / std comparison vs incumbents at the V3_FEATURE_COLUMNS level, OR (ii) per-symbol trial-Optuna importance vector cross-correlation, OR (iii) prior multi-seed performance evidence on a comparable stack. Pure return-correlation ranking is structurally insufficient for justifying universe expansion. New memory rule `feedback_v3_universe_expansion_eda_insufficient.md` enshrines this.

(b) **Universe expansion at n_trials=35 split N ways is over-stretched.** Per-symbol budget arithmetic: at n_trials=35 with 1 outer × 1 inner × N symbols = 35N trials; per-symbol budget is ~35 fits at single-seed EXPLORATION, vs ~500 fits/symbol at iter-v3/018 BOOTSTRAP CONFIRMATION (--seeds 2 --n-trials 50 --ensemble-size 5). Adding new symbols at EXPLORATION budget halves the effective per-symbol Optuna search compared to incumbent symbols' iter-v3/018 fit. Future universe-expansion EXPLORATIONs should either (i) be deferred to CONFIRMATION budget where per-symbol fit quality is non-degraded, OR (ii) test 1-symbol expansion at a time to isolate per-symbol contribution. The 2-symbol pre-decision in the brief Section 0.5 ("trade-rate floor argument") was the wrong call — the floor was satisfied but at the cost of edge.

(c) **HBAR + AVAX axis CLOSED at catalog level for current 10-EXPLORATION cycle.** Cannot revisit HBAR/AVAX without fundamentally different mechanism proposed (e.g., dedicated multi-seed CONFIRMATION budget for the 5-symbol universe; or new feature family designed against HBAR/AVAX-specific microstructure). The catalog row records the negative result; iter-v3/022+ axis MUST advance to a different axis entirely. Other symbol candidates (ATOM/FIL/ALGO) are deferred to future LOW-priority retest only AFTER higher-priority structural axes are exhausted.

(d) **iter-v3/022 axis pre-commit: TRX/2022-Q4 regime gate (MEDIUM #4 ELEVATED per Critic FINAL Rec #1).** Per Critic FINAL `f5b89a3`: iter-v3/022 = surgical structural fix addressing BASELINE_V3.md outstanding constraint #5 (PBO max=1.0 on TRX/2022-10 + TRX/2023-01 — FTX/LUNA crash regime). A regime-aware kill switch (kill TRX trades when BTC_drawdown_30d > 30% OR BTC_volatility_zscore > 2.5) is a SURGICAL fix targeting the highest-PBO cells in iter-v3/018. Per `feedback_v3_concentration_is_signal.md`, regime-conditional kill switch is one of 4 permitted orthogonal mechanisms (binary off/on) for future structural-architecture EXPLORATION.

## Pre-Commit for iter-v3/022

Per Critic FINAL Recommendation #1 of iter-v3/021 (SHA `f5b89a3`) + `feedback_v3_iter019_axis_priorities.md` LOCKED + diary lessons (a)-(d):

- **iter-v3/022 axis = MEDIUM-priority #4 (TRX/2022-Q4 regime gate)**. ELEVATED from MEDIUM to HIGH within the post-bootstrap cycle priority order, given iter-v3/021's NEGATIVE outcome and the catalog discipline that all BASELINE_V3.md outstanding-constraint axes should be tested before any retesting of speculative axes.
- **Implementation**: regime-conditional kill switch for TRX position-taking when (a) BTC_drawdown_30d > 30% over 30 days, OR (b) BTC_volatility_zscore > 2.5. Past-only enforcement: BTC drawdown / vol z-score computed from BTC 8h kline data with strict timestamp < t discipline. NEW gate primitive added to `RiskV2Wrapper` as primitive 9 (sister to primitive 8 per-symbol cap).
- **REVERT V3_MODELS 5 → 3** (drop HBARUSDT + AVAXUSDT). REQUIRED_GAP back 110 → 66 = (21+1) × 3.
- **KEEP** funding_v3 + per-symbol cap infrastructure (cap stays disabled; zero revert cost — preserves option for future re-test under fundamentally different mechanism).
- **ITERATION_LABEL = "v3-022"**.
- **Test for past-only discipline on regime gate**: adversarial test confirming BTC drawdown / vol z-score cannot peek at current bar.
- **NEW memory rule `feedback_v3_universe_expansion_eda_insufficient.md`** committed (per lesson (a)).

## Cadence Status

**3 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 (PROMISING-INERT) + iter-v3/020 (NEGATIVE-clean / PATH C) + iter-v3/021 (NEGATIVE-clean) completed; **7 EXPLORATIONs remaining** before next CONFIRMATION (earliest = iter-v3/029).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/021 ran 23 min — well within).

**HBAR + AVAX axis CLOSED.** iter-v3/022 = TRX/2022-Q4 regime gate (MEDIUM #4 ELEVATED).

## Reproducibility

- Setup commit SHA: `6446d5d` (feat: V3_MODELS 3→5, REQUIRED_GAP 66→110, cap disabled, ITERATION_LABEL=v3-021)
- Phase 5.5 gate SHA: `61f1b35` (PASS)
- Brief SHA: `6b84934`
- EDA analysis SHA: `a360251`
- Engineering report SHA: `bc66596`
- Critic FINAL SHA: `f5b89a3`
- HEAD SHA at backtest run: `6446d5d`
- Reports: `reports-v3/iteration_v3-021/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-021/dsr.json` (DSR=0.0 / PBO=0.1074 / PSR=0.0001 / n_trials=175 / n_eff=19), `reports-v3/iteration_v3-021/per_cell_pbo.csv`, `reports-v3/iteration_v3-021/seed_summary.json`, `reports-v3/iteration_v3-021/pareto_front.csv`, `reports-v3/iteration_v3-021/ic_matrix.csv`, `reports-v3/iteration_v3-021/adf_test.csv`
- No tag (NEGATIVE-clean — universe expansion HBAR+AVAX axis closed at catalog level; not a baseline-update event)
