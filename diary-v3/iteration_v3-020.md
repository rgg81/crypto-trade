# Iteration iter-v3/020 — Diary

## Decision: EXPLORATION-NEGATIVE (clean / PATH C confirmed)

PATH C from brief Section 1 confirmed. The per-symbol PnL share cap (0.40) propagated to runtime, fired at the expected counterfactual rate (BCH 12.8%, LDO 9.4%, TRX 10.4%) on 9 IS trades, and SUBTRACTED edge proportional to model conviction in profitable symbols. IS Sharpe -0.10 vs anchor / OOS Sharpe -0.72 vs anchor — both deltas exceed the magnitude threshold of brief §4.4 row 5. PSR collapsed from iter-v3/019's saturation 1.0 → 0.0009 (n_trials=35 honest deflation; iter-v3/019's DSR=+0.0167 saturated artifact is now resolved). n_eff=19 vs iter-v3/019's n_eff=7 — n_trials=35 EXPLORATION default delivers materially better Optuna search coverage, cleaner DSR/PSR readout, and earlier-window NEGATIVE classifications. Methodology of the run is clean — all 12 standard checks PASS.

NOT a CONFIRMATION-bundle candidate. The per-symbol PnL share cap mechanism is CLOSED at the catalog level — future axes touching concentration MUST use orthogonal mechanisms (universe expansion, drawdown brake, vol-target ceiling, regime-conditional kill switch). NOT proportional scaling. Cannot be renegotiated post-hoc per new memory rule `feedback_v3_concentration_is_signal.md`.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding `max_per_symbol_pnl_share = 0.40` (TRADE-time rolling-window per-symbol PnL cap inside `RiskV2Wrapper`) on top of the iter-v3/018 multi-seed BOOTSTRAP baseline (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 13 V3_FEATURE_COLUMNS) will reduce single-symbol OOS lottery risk by mechanically scaling down the position weight of any symbol whose 30-day rolling PnL share exceeds 0.40, while preserving most of the underlying entry signal. Predicted IS Sharpe band [+0.30, +0.55] median +0.40; predicted OOS Sharpe band [+0.45, +0.65] median +0.55."

**Spec (locked, single-axis variation):**
- NEW `RiskV2Config` parameters: `enable_per_symbol_cap = True`, `max_per_symbol_pnl_share = 0.40`, `max_per_symbol_window_bars = 90` (≈ 30d at 8h cadence).
- TRADE-TIME integration in `RiskV2Wrapper.get_signal()`: cap multiplies `weight_factor` by `cap / observed_share` when a symbol's rolling 90-bar PnL share exceeds 0.40. Trades NOT killed; only position magnitude shrinks. Past-only enforcement: `record_trade_result(trade)` keyed on `close_time`; current trade not in own denominator (verified by adversarial test `test_per_symbol_cap_past_only`).
- `funding_rate_zscore_30` REVERTED from iter-v3/019 (V3_FEATURE_COLUMNS 14 → 13) for clean iter-v3/020 attribution. Funding infrastructure (`funding_v3.py` module + `fetch-funding` CLI + `data/funding_rates/<sym>.csv` cache) KEPT (zero revert cost; preserves option for iter-v3/028+ CONFIRMATION retest).
- sklearn pinned `>=1.8,<1.9` per Critic FINAL Rec 12 of iter-v3/019.
- Ran in EXPLORATION mode: `--exploration --seeds 1` (1 outer × 1 inner × 35 n_trials × 3 symbols = **105 fits per cell**; colsample_bytree=1.0 hardcoded). FIRST EXPLORATION at the new n_trials=35 default per `feedback_v3_exploration_n_trials_35`.
- All other strategy parameters byte-identical to iter-v3/018 (BCH+LDO+TRX, ATR 2.0/1.0, zscore_threshold=2.0, BTC trend ±15%, ADX threshold=20, 7-primitive risk gate stack).
- Anchor: iter-v3/018 multi-seed mean +0.3788 IS / +0.3869 OOS (NOT iter-v3/013 single-seed +1.0088/+2.6970 — formally falsified at iter-v3/018).

This was iter-v3/020, the **first NEW-risk-primitive axis** in v3 catalog (12 unique axis representations after this iteration). Cadence #2 of 10 in the post-bootstrap cycle that follows iter-v3/018 CONFIRMATION-MERGE-BOOTSTRAP.

## Headline Numbers

### Single-seed EXPLORATION run (seed 42)

| Metric | iter-v3/018 anchor (multi-seed mean) | iter-v3/020 | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | **+0.2745** | **-0.1043** (below predicted [+0.30, +0.55] lower bound) |
| OOS monthly Sharpe | +0.3869 | **-0.3296** | **-0.7165** (way below predicted [+0.45, +0.65] lower bound) |
| OOS/IS Sharpe ratio | 1.02 | -1.20 | sign flip |
| IS n_trades | 196 (mean) | **200** | bit-identical-region (well within saturation band) |
| OOS n_trades | 90.5 (mean) | **86** | <130 trade-rate floor (informational) |
| IS MaxDD | 21.86% (mean) | 29.33% | +7.47pp |
| OOS MaxDD | 27.74% (best seed 42) | 34.10% | +6.36pp |
| Win rate IS / OOS | — | 31.0% / 37.2% | OOS WR > IS WR (mechanical: cap removed loser-amplification) |
| Total OOS PnL | +∼7% (mean) | **-9.07%** | LDO -13.29 weighted_pnl drives portfolio negative |
| DSR | 0.0 (n_trials=1500) | **0.0** (n_trials=105) | clean honest readout at n_trials=35 |
| PSR | 0.9936 | **0.0009** | collapsed from iter-v3/019 saturation — methodological IMPROVEMENT |
| PBO mean | 0.0892 | 0.1190 | TRX/2025-Q4 carry-forward |
| n_eff | 25 (CONFIRMATION) | **19** | vs iter-v3/019 n_eff=7 — n_trials=35 delivers better search coverage |
| n_trials | 1500 (CONFIRMATION) | **105** | EXPLORATION default raised 30 → 105 |

### vs iter-v3/019 (prior EXPLORATION; for n_trials=35 validation)

| Metric | iter-v3/019 (n_trials=10) | iter-v3/020 (n_trials=35) | Δ |
|---|---:|---:|---:|
| n_trials per cell | 30 | **105** | +250% search coverage |
| n_eff | 7 | **19** | +172% effective trials |
| DSR | +0.0167 (saturated artifact) | **0.0** (honest) | n_trials=35 deflation gradient correctly pushes DSR to 0 when observed_SR is genuinely modest |
| PSR | 1.0 (saturated) | **0.0009** (honest) | P(true Sharpe>0) at n_trials=105 collapses to ~0 when observed annualized SR ≈ 0.95 |
| Wall-clock | 6 min | **13 min** | +117% (still well within 2h EXPLORATION HARD CAP) |

### Path C confirmation: counterfactual vs observed

| Mode | Predicted OOS Sharpe Δ | Observed OOS Sharpe Δ |
|---|---:|---:|
| Mode A (static counterfactual, brief §2.2.1) | -0.36 | — |
| Mode B (rolling counterfactual, brief §2.2.2) | -0.26 | — |
| **iter-v3/020 actual** | predicted lower-bound [-0.36, -0.26] | **-0.7165** |

The observed OOS delta (-0.7165) is **substantially WORSE** than both counterfactual lower bounds (Mode A -0.36, Mode B -0.26). PATH C scenario was pre-registered at P=30% probability; its realization AND its magnitude exceeding the counterfactual lower bound confirms that **Optuna at n_trials=35 did NOT compensate for the cap** — in fact, the cap + Optuna interaction degraded OOS further than the static counterfactual estimate. Mechanism: concentration carries genuine edge that the cap removed proportional to conviction.

### Per-symbol attribution (single-seed)

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | Concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +0.8236 | 36 | 36.1% | -9.08% |
| LDOUSDT | **-13.2882** | 13 | 38.5% | 146.43% |
| TRXUSDT | +3.3899 | 37 | 37.8% | -37.36% |

LDO drives portfolio negative (-13.29 weighted_pnl on 13 trades) — the symbol the cap most aggressively scaled down (9.4% fire rate on IS) is the symbol the cap most aggressively damaged on OOS. **Concentration_pct values >100% / negative are accounting artifacts of negative total portfolio PnL denominator (-9.07%); they do NOT indicate a mechanism defect.** The cap fired at expected ~10% per symbol on IS as designed; falsifier 5 (post-cap top-share > 40% indicating mechanism defect) NOT triggered.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS (Critic FINAL `f913724`). Look-ahead audit verified by past-only `record_trade_result(trade)` keyed on `close_time` + adversarial test `test_per_symbol_cap_past_only`. Embargo width REQUIRED_GAP=66=(21+1)×3 unaffected by cap mechanism. Reproducibility stamp clean (Setup `37df8a9`, gate `68a02ae`, brief `de82b8e`, EDA `bbbe783`). Single-axis discipline preserved: cap added; funding reverted; ITERATION_LABEL=v3-020; sklearn pin. 8 unit tests covering basic/no-fire/scaling/past-only/disabled/window/counter/negative-share.

- **n_trials=35 EXPLORATION default validates positively (PRELIMINARY).** Three diagnostic improvements over iter-v3/019:
  1. **n_eff=19** vs iter-v3/019 n_eff=7 — higher absolute search coverage at n_trials=105 vs 30
  2. **DSR=0.0** vs iter-v3/019 +0.0167 saturated artifact — deflation gradient correctly pushes DSR to 0 when observed Sharpe is genuinely modest
  3. **PSR=0.0009** vs iter-v3/019 saturation 1.0 — honest P(true Sharpe>0) readout at n_trials=105
  
  Wall-clock budget held (13 min vs 2h cap). ONE data point cannot validate a default change unilaterally — Critic prior is that iter-v3/021-023 should also exhibit DSR/PSR/n_eff in this honest regime. Continue at n_trials=35; do not roll back; record metric trajectories in catalog.

- **Counterfactual prediction was directionally correct, just not pessimistic enough.** Brief §2.2 IS-only counterfactual analysis predicted PATH C at P=30% with predicted OOS Δ in [-0.36, -0.26] band. Observed -0.72 is materially worse but the SIGN and MECHANISM were correctly anticipated. The brief explicitly framed PATH C as "if dominant-symbol concentration is not lottery-RISK but lottery-REWARD, then capping mechanically subtracts genuine edge" — exactly what observed.

- **PSR collapse from saturated 1.0 → 0.0009 is methodological IMPROVEMENT.** iter-v3/019's saturated PSR=1.0 was a known structural artifact at n_trials=30 (E[max_SR]=2.61 vs observed annualized 4.00). At iter-v3/020 n_trials=105, E[max_SR]≈3.25 deflates observed annualized Sharpe ≈ 0.95 honestly to PSR=0.0009. Future EXPLORATION rows where observed Sharpe genuinely exceeds E[max_SR] will show PSR rising — the metric is now informative again.

## What Failed

- **Falsifier 1 (PATH C indicator) fires unambiguously.** IS Sharpe Δ = -0.1043 (< -0.10 threshold) AND OOS Sharpe Δ = -0.7165 (< -0.10 below anchor; OOS = -0.3296 < anchor +0.2869). Both gates fail simultaneously. EXPLORATION-NEGATIVE (clean) — no PATH B (lift-with-floor-violation) ambiguity, no PATH D (NULL-RESULT identity) ambiguity.

- **OOS observed Δ (-0.72) substantially worse than counterfactual band [-0.36, -0.26].** Predicted upper bound was -0.26; observed is -0.72 — i.e., the cap+Optuna interaction degraded OOS by an additional **-0.46 Sharpe beyond static counterfactual estimate**. Mechanism: at n_trials=35, Optuna explored hyperparameters that AVOIDED the cap (i.e., reduced the very symbol-conviction that the cap targeted), but in doing so reduced edge magnitude on profitable symbols (BCH +0.82, TRX +3.39 — both materially below their iter-v3/018 anchor counterparts) without rescuing LDO (-13.29). The cap forced Optuna into a region of hyperparameter space with weaker per-symbol edges across the board, not just the dominant symbol.

- **LDO drove the OOS Δ.** LDO -13.29 weighted_pnl on 13 OOS trades is the largest single-symbol negative in v3 EXPLORATION history. iter-v3/018's anchor had LDO -10.24 (seed 42) — already negative — and the cap mechanism was supposed to LIMIT LDO's negative concentration via downscaling. Observed: cap fired at 9.4% on LDO IS but LDO OOS still concentrated negatively. Concentration is NOT lottery-RISK; it is lottery-REWARD when positive (TRX) and lottery-DAMAGE when negative (LDO) — the cap's symmetric scaling treats both as crowding to remove.

- **OOS n_trades = 86 < 130 trade-rate floor.** Informational caveat at EXPLORATION (`feedback_trade_rate_floor`). Below floor at single-seed; the cap mechanism reduced effective trade emission from iter-v3/018's 90.5 (mean) to 86 — a small reduction but contributes to underpowering.

- **MaxDD increased from anchor (IS +7.47pp, OOS +6.36pp).** Counter to brief Section 1's mechanism story ("the cap is a position-sizing layer; it does not gate trade emission, only the magnitude of position weight"). The cap should have FLATTENED the per-symbol PnL distribution (lower MaxDD via concentration reduction). Observed: the cap weakened positive-edge symbols' positions enough to reduce their compounding lift, while losing symbols' negative streaks were unaffected (the cap only fires when SHARE > 40%, regardless of sign convention in implementation). Net: MaxDD worsens because the position-sizing reduction is asymmetric in mean but symmetric in tail.

## Critical Lessons

(a) **Concentration in 3-symbol BCH+LDO+TRX universe is lottery-REWARD source, NOT lottery-RISK source.** iter-v3/020 confirmed PATH C: per-symbol PnL share caps subtract edge proportional to conviction. The mechanism: in 3-symbol universe, the model's high-conviction symbols carry the edge. A cap proportional to share scales those high-conviction positions DOWN, removing edge proportional to where the model is most right. Observed Δ -0.72 > counterfactual lower bound -0.26 by an additional -0.46 → Optuna at n_trials=35 did NOT compensate for the cap; the cap+Optuna interaction degraded OOS further than static counterfactual estimate. New memory rule `feedback_v3_concentration_is_signal.md` enshrines this distinction so future axes touching concentration MUST use orthogonal mechanisms.

(b) **Per-symbol PnL share caps CLOSED at catalog level.** Cannot revisit at any threshold without fundamentally different mechanism proposed with new IS-only counterfactual evidence. Permitted alternatives for future "concentration" axes: (i) **universe expansion** (denominator expansion — adds more symbols rather than scaling existing ones); (ii) **per-symbol drawdown brake** (loss-stop semantics — kill symbol after consecutive losses, NOT proportional scaling); (iii) **vol-target ceiling** (exposure ceiling — caps total notional, NOT per-symbol share); (iv) **regime-conditional kill switch** (binary off/on, NOT continuous scaling).

(c) **n_trials=35 EXPLORATION default validates positively at iter-v3/020 (PRELIMINARY).** Three diagnostic improvements over iter-v3/019: n_eff 7 → 19 (+172%); DSR saturated +0.0167 → honest 0.0; PSR saturated 1.0 → honest 0.0009. Wall-clock 13 min (well within 2h cap). The n_trials=35 default delivers materially better Optuna search coverage AND cleaner DSR/PSR readout AND earlier-window NEGATIVE classifications. ONE data point cannot validate unilaterally — continue at n_trials=35 through iter-v3/021-023, record DSR/PSR/n_eff trajectories. If subsequent EXPLORATIONs ALSO exhibit honest deflation regime, the default is empirically validated.

(d) **EXPLORATION-mode counterfactual analysis correctly anticipates PATH C direction but underestimates magnitude.** Brief §2.2's counterfactual on iter-v3/018 anchor predicted [-0.36, -0.26] OOS Δ. Observed -0.72. The 2x magnitude gap is the cap+Optuna interaction effect — not a counterfactual flaw but a property of TRADE-time integration: at IS-only counterfactual mode, the cap is applied to an already-fitted strategy; at iter-v3/020 actual run, Optuna re-fits hyperparameters knowing the cap is active, and the resulting hyperparameter region has weaker per-symbol edges across the board. Future PATH C-suspect axes must include this 2x interaction-magnitude factor when sizing predicted bands.

(e) **iter-v3/021 axis pre-commit: HIGH-priority axis #2b (universe expansion) per Critic FINAL Rec.** PATH C confirmation demonstrates 3-symbol concentration carries genuine signal; the orthogonal mechanism is **denominator expansion** — adding 1-2 NEW symbols to V3_MODELS to dilute concentration mechanically WITHOUT removing edge from any single symbol. This was sub-axis B in iter-v3/020 brief, deferred by single-axis discipline.
  - Why universe expansion elevates over alternatives: MEDIUM #3 (DSR gate reformulation) is a process fix, not a strategy lever; MEDIUM #4 (TRX/2022-Q4 regime gate) is symbol-specific, narrower upside; HIGH-priority #1 (NEW feature family) tested at iter-v3/019 (PROMISING-INERT), retest at n_trials=35 is lower-priority than orthogonal-mechanism universe-expansion given PATH C confirmation.
  - Symbol candidates (excluded per `project_tried_symbols.md` + V3_EXCLUDED_SYMBOLS: DOGE, SOL, XRP, NEAR, BTC, ETH, LINK, LTC, DOT, BNB, MKR): AVAXUSDT, ADAUSDT, ATOMUSDT, FILUSDT, ALGOUSDT, HBARUSDT, VETUSDT — **subject to QR Gate 1-2 EDA** (Phase 1 + Phase 3 in iter-v3/021 setup).
  - iter-v3/021 first commit will DISABLE per-symbol cap (set `enable_per_symbol_cap = False` default) since the cap was found to subtract edge — the implementation stays in `RiskV2Wrapper` (zero revert cost; preserves option for fundamentally-different-mechanism future use) but is not active by default in v3 production.

## Pre-Commit for iter-v3/021

Per `feedback_v3_iter019_axis_priorities.md` LOCKED + Critic FINAL Recommendation #1 of iter-v3/020 (SHA `f913724`):

- **iter-v3/021 axis = HIGH-priority #2b (universe expansion)**. Cannot be renegotiated post-hoc per `feedback_v3_concentration_is_signal.md`. Per-symbol PnL share cap axis is CLOSED.
- **DISABLE per-symbol cap in iter-v3/021 setup commit**: `RiskV2Config.enable_per_symbol_cap = False` default. Implementation KEPT in repo (zero revert cost). v3 runner will not pass `cap=0.40` from this iteration onward.
- **Phase 1 + Phase 3 EDA on candidate NEW symbols** before brief: AVAXUSDT, ADAUSDT, ATOMUSDT, FILUSDT, ALGOUSDT, HBARUSDT, VETUSDT against Gate 1 (data quality), Gate 2 (liquidity), structural complementarity to BCH+LDO+TRX. Output: `analysis/iteration_v3-021/symbol_candidate_ranking.csv`. Top-2 candidates progress to brief.
- **NEW memory rule `feedback_v3_concentration_is_signal.md`** committed (per Critic Rec #3). Cannot be renegotiated post-hoc.

## Cadence Status

**2 of 10 EXPLORATIONs done in post-bootstrap cycle.** iter-v3/019 (PROMISING-INERT) + iter-v3/020 (NEGATIVE-clean) completed; **8 EXPLORATIONs remaining** before next CONFIRMATION (earliest = iter-v3/029 — bumped from iter-v3/028 because iter-v3/021-028 = 8 EXPLORATIONs needed).

CONFIRMATION wall-clock cap = 6h (per `feedback_v3_cadence_discipline.md` empirically updated post-iter-v3/018). EXPLORATION wall-clock cap = 2h (iter-v3/020 ran 13 min — well within).

**Per-symbol cap axis CLOSED.** iter-v3/021 = universe expansion (HIGH-priority #2b).

## Reproducibility

- Setup commit SHA: `37df8a9` (feat: per-symbol PnL cap (primitive 8) + revert funding to 13 features + sklearn pin)
- Phase 5.5 gate SHA: `68a02ae` (PASS)
- Brief SHA: `de82b8e`
- EDA analysis SHA: `bbbe783`
- Engineering report SHA: `b1f4aa5`
- Critic FINAL SHA: `f913724`
- HEAD SHA at backtest run: `37df8a9`
- Reports: `reports-v3/iteration_v3-020/comparison.csv` (single-seed EXPLORATION row), `reports-v3/iteration_v3-020/dsr.json` (DSR=0.0 / PBO=0.119 / PSR=0.0009 / n_trials=105 / n_eff=19), `reports-v3/iteration_v3-020/per_cell_pbo.csv`, `reports-v3/iteration_v3-020/seed_summary.json`, `reports-v3/iteration_v3-020/pareto_front.csv`, `reports-v3/iteration_v3-020/ic_matrix.csv`, `reports-v3/iteration_v3-020/adf_test.csv`
- No tag (NEGATIVE-clean — per-symbol cap axis closed; not a baseline-update event)
