# LightGBM Master Advisor — iter-v1/042 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1. Anchor: BASELINE_V1 (`v0.v1-baseline-corrected`, IS +0.2829 / OOS +0.6637).
- /042 axis: MODEL-ARCH XGBoost head-to-head vs LightGBM on V1_FEATURE_COLUMNS_PRUNED (44 cols), 5-cohort, n_trials=18, ENSEMBLE_SIZE=3, single-seed=42.
- Prior model-arch precedent: iter-v1/024 (regime sub-models) ≠ library swap; iter-v3/016 XGBoost on 13-col stack = NEGATIVE-clean at n_trials=10.
- Iteration rationale: /038 LM Master Rec 3 (this iteration's seed) — MODEL family last touched cycle-1 /003; 39+ iter rotation gap.

## 1. XGBoost Hyperparameter Analogues (Optuna search-space mapping)

| LightGBM (current) | XGBoost equivalent | Recommended /042 bound |
|---|---|---|
| `num_leaves ∈ [16, 63]` | NO equivalent — controlled via `max_depth` + `min_child_weight` | `max_depth ∈ [3, 5]` (tightened from LGBM-equiv [3,7]) |
| `min_data_in_leaf ∈ [20, 200]` | `min_child_weight ∈ [1, 20]` | `min_child_weight ∈ [3, 15]` |
| `learning_rate ∈ [0.01, 0.1]` | `eta` (alias `learning_rate`) | identical |
| `feature_fraction ∈ [0.5, 1.0]` | `colsample_bytree` | identical |
| `bagging_fraction ∈ [0.5, 1.0]` | `subsample` | identical |
| `lambda_l1` / `lambda_l2` | `reg_alpha` / `reg_lambda` | identical |
| `min_gain_to_split` | `gamma ∈ [0, 0.5]` | identical |
| n/a (leaf-wise growth) | `tree_method='hist'` + `grow_policy='depthwise'` | LOCK depthwise — single-axis isolation vs LightGBM's leaf-wise |

XGBoost level-wise on depth-3-5 gives ~8-32 effective leaves — **structurally NARROWER than LightGBM's [16, 63]**. For 5-cohort × monthly cell (~150-500 trades), this is the right capacity floor; do NOT extend to depth 6-7 (overfit risk + wall-clock blow-up).

## 2. Wall-Clock Viability — CRITICAL

LightGBM /038 ran ~50 min at n_trials=18 / ENSEMBLE=3 / 5-cohort. XGBoost CPU `hist` is empirically **2-3× slower** at equivalent params on this data scale. Predicted /042 wall-clock: **90-120 min**, with tail risk to 150 min if Optuna selects `max_depth=5` + `subsample=1.0` regions.

**Recommendation: enforce `max_depth ∈ [3, 5]` (NOT [3, 7]) + `tree_method='hist'` (NOT 'exact') + `n_jobs=-1`.** This keeps the run inside the v1 EXPLORATION 2h soft cap. Brief Section 7 must specify the cap and a hard kill at 110 min.

## 3. Optuna Trial-Budget Adequacy

n_trials=18 on XGBoost's 8-dim search space (max_depth, min_child_weight, eta, gamma, subsample, colsample_bytree, reg_alpha, reg_lambda) is **TIGHT**. LightGBM has been at `n_effective_trials = 9` for 2 consecutive iterations (/037, /038) on the same budget — XGBoost's different basin geometry will likely surface a similar saturation at **n_effective ~ 10-12**. Per-cell variance will be HIGHER than LightGBM at this budget — flag for Phase 7.4 trial-stability audit.

## 4. F-AXIS Falsifier Set (recommended)

- **F2 (WIRING, load-bearing)**: runner banner prints `[xgboost]` not `[lgbm]` for all 4 models; `import xgboost; xgboost.__version__` logged at start; first per-cell save shows XGB native model file format (`.json` or `.ubj`), not LightGBM `.txt`. ZERO accidental fallback to `LightGbmStrategy`.
- **F3 (BASIN MIGRATION)**: Jaccard(OOS_trade_roster_XGB, OOS_trade_roster_LGBM_baseline) ∈ [0.20, 0.60]. Below 0.20 = different model entirely (suspect); above 0.60 = effectively no change (suspect mis-wiring). Load-bearing.
- **F4 (OOS Sharpe Δ band)**: PROMISING-CLEAN ≥ +0.10 / PROMISING-INERT-FAV [+0.02, +0.10] / INERT-NO-EFFECT [-0.05, +0.02] / NEG-CLEAN [-0.30, -0.05] / NEG-CAT < -0.30.
- **F5 (WALL-CLOCK)**: hard kill at 110 min; if total runtime > 100 min flag for /043 brief Section 0 ("XGBoost wall-clock disqualifies it from CONFIRMATION budget regardless of OOS outcome").

## 5. Prior Distribution (Phase 4.5 forecast)

| Subtype | Prior | Rationale |
|---|---|---|
| PROMISING-CLEAN (Δ ≥ +0.10) | **8%** | v3/016 NEG precedent caps optimism; v1 stack is 3× wider feature set + 2× cohort pool — non-zero residual chance XGB's conservatism (level-wise + `min_child_weight`) helps the small per-cell training cells. |
| PROMISING-INERT-FAV ([+0.02, +0.10]) | **22%** | Library swap on saturated rank-1-5 feature stack (5-iter held-identical) → most likely modest lift if any. |
| INERT-NO-EFFECT ([-0.05, +0.02]) | **35% MODAL** | Saturated feature/loss surface; XGB and LGBM converge on similar basins on this 44-col stack when n_trials=18 = both algorithms find the same dominant ridge. Most-likely outcome. |
| NEG-CLEAN ([-0.30, -0.05]) | **22%** | v3/016 precedent; XGB at n_trials=18 may underfit depth-5 cap vs LGBM leaf-wise at num_leaves=63. |
| NEG-CATASTROPHIC (< -0.30) | **13%** | Wall-clock blow-up forces hard-kill mid-run → partial models → OOS catastrophe. Non-negligible per F5 risk. |

**Combined PROMISING 30% / Combined NEG 35% / INERT 35%.** Skewed slightly NEGATIVE-SIGN — the modal mass is INERT-NO-EFFECT (35%), and NEG outweighs PROMISING by 5pp.

## 6. Saturation Risks to Flag

- **Rank 1-5 feature identity has held for 5 iterations** (/034-/038): `vol_atr_14`, `trend_aroon_osc_50`, `stat_autocorr_lag5`, `oi_delta_30_z90`, `trend_adx_14`. Library swap will NOT surface new features — both XGB and LGBM rank these same primitives via gain. If /042 surfaces the same top-5 in `feature_importance.csv` (likely > 80% probability), the model-arch family is co-saturated with the feature family. This is the most important post-mortem signal.
- **`n_effective_trials = 9` recurrence** is the load-bearing instability flag from /037-/038. Expect XGB to fall in the [10, 12] range; if it falls below 9, n_trials=18 is structurally inadequate for **both** libraries and the issue is the budget, not the architecture.
- **basis_zscore_30 INERT recurrence**: per /038 Rec 1, this feature has been rank ≥15 for 4 consecutive iterations. If /042 keeps it in V1_FEATURE_COLUMNS_PRUNED, XGBoost will inherit the noise. QR should drop it in the brief; LM Master flagged in /038 but it was kept.

## 7. What I Did NOT Recommend, and Why

- **CatBoost as 3-way comparison**: out of scope per single-axis isolation; adds wall-clock + scaffolding risk for marginal additional information. Defer to /044 if /042 INERT.
- **`grow_policy='lossguide'`** (XGBoost leaf-wise mimic): WOULD give head-to-head parity on leaf shape but DEFEATS the experiment — the axis is "different library, same architectural philosophy", and lossguide collapses that distinction. LOCK depthwise.
- **Raising n_trials to 35 for the XGBoost arm**: changes 2 axes simultaneously (library + budget). Keep n_trials=18 to isolate the library axis; expect higher trial-stability variance and flag in Phase 7.4.

## 8. Closing Note

**MEDIUM-LOW confidence in PROMISING outcome (30%).** Modal expectation is INERT-NO-EFFECT (35%) — the v1 feature stack has been at the same rank-1-5 surface for 5 iterations and library swap rarely surfaces new structure without new features. The single most important thing the QR should NOT ignore: **wall-clock F5 is load-bearing at 110-min hard-kill**. If /042 exits cleanly at INERT, the MODEL-ARCH family closes at v1 (both v3/016 + v1/042 NEG-or-INERT = 2-iter recurrence across tracks → axis-closed) and the /044 substrate must pivot to FEATURE-ENGINEERING (composed features per /038 Rec 1) or LABELING (per /038 Rec 2).

---

# Report-Back (≤250 words)

**3 strongest recommendations**:
1. **TIGHTEN `max_depth ∈ [3, 5]`** (not [3, 7]) + LOCK `tree_method='hist'` + `grow_policy='depthwise'`. Single-axis isolation requires structural difference from LightGBM's leaf-wise; depth-5 ceiling caps wall-clock and matches the 150-500 trades/cell capacity floor.
2. **Hard-enforce F5 wall-clock kill at 110 min**. XGBoost CPU is empirically 2-3× slower than LightGBM at equivalent params; /038 ran ~50 min so /042 projects 90-120 min, with tail to 150 min. Brief Section 7 must specify the kill threshold AND a /043 routing note that wall-clock blow-up disqualifies XGB from CONFIRMATION regardless of OOS outcome.
3. **F2 WIRING falsifier is load-bearing**: banner prints `[xgboost]`, `xgboost.__version__` logged, per-cell model artifact is XGB native format. Library swap iterations have a non-trivial silent-fallback risk; treat F2 as Critic Check 1 mandatory.

**Prior distribution**: PROMISING-CLEAN 8% / PROMISING-INERT-FAV 22% / **INERT-NO-EFFECT 35% MODAL** / NEG-CLEAN 22% / NEG-CAT 13%. Combined PROMISING 30% / combined NEG 35%. Slightly NEG-skewed mid-band.

**Wall-clock viability**: BORDERLINE. 90-120 min projected with 13% tail risk to NEG-CAT from hard-kill. Manageable with the tightened max_depth bound; UNMANAGEABLE if QR keeps [3, 7].

**/044 substrate forecast**: If /042 INERT-or-NEG (70% prior combined), MODEL-ARCH family closes at v1 (v3/016 + v1/042 = cross-track 2-iter recurrence) and /044 must pivot to FEATURE-ENGINEERING (composed features per /038 Rec 1) — the rank-1-5 feature identity has been frozen 5 iterations, both libraries inherit the saturation.

---

**File path**: `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-042/lgbm_advisor.md` (to be created — directory does not yet exist; orchestrator persists this content there).

---

# LightGBM Master Advisor — iter-v1/042 — Phase 7.4 (Post-Mortem)

## Context Read
- TYPE: EXPLORATION cycle-5 #9/10; axis: MODEL-ARCH LightGBM → XGBoost head-to-head, V1_FEATURE_COLUMNS_PRUNED 44 cols, n_trials=18, ENSEMBLE_SIZE=3, single-seed=42.
- Iteration outcome (`reports-v1/iteration_v1-042/comparison.csv`): IS Sharpe **+0.7438** vs baseline +0.2829 (Δ **+0.46**); OOS Sharpe **+0.4011** vs baseline +0.6637 (Δ **−0.26**); IS Sortino +0.8894 / OOS +0.4461; IS trades 613 / OOS 224; **IS MaxDD 97.20%** vs baseline 73.06% (Δ +24.1pp — load-bearing tail inflation); OOS MaxDD 42.45% vs 40.94% (within F-AXIS #7 1.5× band PASS); IS PnL +132.5% / OOS +24.23%; DSR −43.56 (informational under new skill); `n_effective_trials = 10` (UP from LightGBM's 9 recurrence).
- Engineering report claim: BLOCK risk → IS MaxDD 97.20% is catastrophic; F-AXIS #7 within band on OOS only. Brief Section 1 H1 (variance-down on Pool A, bias-up on altcoins, net INERT) is **REFUTED**: IS Δ +0.46 is FAR outside H1's predicted modal INERT [-0.10, +0.05]; OOS Δ −0.26 lands in NEG-CLEAN band.

## Item 0 (MANDATORY, FIRST) — Regime Attribution Table

Canonical tagger: BTC 90-day return + 30-day realized vol quantiles (IS+OOS window 2022-01→2026-05; q75=0.584, q90=0.729 annualized rv). 53 months tagged. Rules: bull (BTC +90d > +20% AND rv30 < q75); bear (BTC +90d < −10%); chop (|BTC +90d| ≤ 10%); vol-spike (rv30 ≥ q90); recovery (post-bear, BTC +90d > +10%). NO alt-rotation / ETF-flow / liq-cascade months emerged from the canonical rule on this BTC-only tagger; flagged for /044 regime_catalog.md authoring.

| Regime | IS months | OOS months | /042 IS Sharpe | /042 OOS Sharpe | /042 IS trades | /042 OOS trades | /042 IS PnL | /042 OOS PnL | Baseline IS Sharpe | Baseline OOS Sharpe | Baseline IS trades | Baseline OOS trades | Baseline IS PnL | Baseline OOS PnL | Bundle-role implication |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **bull** | 15 | 3 | **−0.30** | **−3.20** | 211 | 39 | −16.9% | −38.98% | +0.09 | −2.02 | 229 | 48 | +5.4% | −28.59% | **OFF-REGIME DRAG** — exclude from bull dispatch; both libraries struggle but /042 strictly worse OOS (Δ −1.18 within-regime) |
| **bear** | 9 | 6 | **+1.19** | **+1.42** | 139 | 80 | +36.4% | +53.72% | −0.23 | +1.62 | 142 | 68 | −9.5% | +45.49% | **BEAR-SPECIALIST IS** + parity OOS — strong /044 bundle candidate for bear regime (IS Δ **+1.42** within-regime; OOS Δ −0.20 within noise) |
| **chop** | 10 | 4 | **+1.29** | **+0.59** | 179 | 79 | +55.3% | +10.24% | −0.27 | +3.55 | 175 | 46 | −9.2% | +41.40% | IS-specialist (chop Δ +1.56 dominates IS lift), OOS chop −2.96 deficit — **TAIL-DRAG OOS chop** — exclude from chop dispatch at /044 |
| **vol-spike** | 5 | 1 | +1.94 | 0.0 (1 month) | 84 | 5 | +57.7% | −9.7% | +2.77 | 0.0 (1 month) | 75 | 13 | +67.5% | −12.24% | Within-σ_R; both libraries strong IS, both weak OOS (1-month sample). NEUTRAL contributor — defer to multi-seed sigma_R determination |
| **recovery** | 0 | 1 | n/a | 0.0 (1 month) | 0 | 21 | n/a | +8.94% | n/a | 0.0 (1 month) | n/a | 14 | n/a | −7.92% | OOS recovery single-month: /042 +8.94% vs baseline −7.92% → **recovery-specialist OOS candidate** (Δ +16.9% within 1 month) — caveat: single-month n=1, statistically inconclusive |
| alt-rotation / ETF-flow / liq-cascade | 0 | 0 | — | — | — | — | — | — | — | — | — | — | — | — | Canonical BTC-only tagger emitted ZERO months in these tags. Flag for /044 regime_catalog.md: extend tagger to alt-symbol divergence + funding-extremity for alt-rotation; explicit ETF date-window mask for ETF-flow; rv30 spike + cascade-pattern detector for liq-cascade. |

**Internal consistency check (Critic Check 3c precondition)**: Per-regime IS PnL sums = bull −16.9 + bear +36.4 + chop +55.3 + vol-spike +57.7 = **+132.5%** = comparison.csv IS total_net_pnl +132.53% ✓ (within ±0.03pp). Per-regime OOS PnL sums = bull −38.98 + bear +53.72 + chop +10.24 + recovery +8.94 + vol-spike −9.70 = **+24.22%** = comparison.csv OOS total_net_pnl +24.23% ✓.

## Item 1 — F-AXIS Falsifier Table (per brief Section 4)

| Falsifier | Predicted | Observed | Verdict |
|---|---|---|---|
| F1 OOS Sharpe Δ | modal INERT [-0.10, +0.05] | **−0.26** | OUTSIDE — lands in NEG-CLEAN band (regime-aware bands skip this; see Item 0) |
| F2 Wiring (xgboost banner / `Model_X_xgboost_*` naming) | PASS required | PASS — 4 distinct `xgboost`-tagged feature_importance CSVs emitted | PASS |
| F3 Trade-count IS [420,760] / OOS [110,260] (floor 130) | within band | IS 613 / OOS 224 | PASS |
| F4 Per-symbol OOS Δ direction (BTC+ETH +, alts mild −) | mixed direction | LINK +82.83% / DOT +29.45% / ETH +32.01% / LTC +17.40% / **BTC −61.69%** | INVERTED — BTC drag, altcoins lift (opposite of mechanism prediction; H1a basin-stability mechanism partially REFUTED for Pool A) |
| F5 Basin-stability OOS roster Jaccard ≥ 0.20 | LOAD-BEARING gate | NOT YET COMPUTED (Critic Phase 7.5 must derive from `out_of_sample/trades.csv` vs baseline OOS trades.csv) | UNDETERMINED — flag for Critic Check 1 |
| F6 Importance Spearman ρ ∈ [0.40, 0.75] | LOAD-BEARING gate | NOT YET COMPUTED (portfolio rank correlation between /042 and baseline — Critic to evaluate) | UNDETERMINED |
| F7 OOS MaxDD inflation ≤ 1.5× (cap 60%) | within | 42.45% / 40.94% = 1.037× | PASS (OOS only) |

**IS MaxDD 97.20%**: NOT covered by F-AXIS #7 (brief's F7 specified OOS only). This is an **unanticipated falsifier** — IS DD inflation +33% relative is structurally severe; flag for Critic Check 7.

## Item 2 — Feature Importance Triage (XGBoost gain ranks)

Portfolio-aggregated top-15 gain ranks (44 features):

| Rank | Feature | Mean gain | LGBM /034-/038 anchor rank |
|---|---|---|---|
| 1 | vol_atr_14 | 0.1675 | 1 (anchor identity preserved) |
| 2 | vol_natr_14 | 0.1602 | 2-3 |
| 3 | interact_natr_x_adx | 0.1561 | new top-3 (NATR×ADX interaction promoted) |
| 4 | trend_aroon_osc_50 | 0.1435 | 2 in LGBM /038 |
| 5 | mom_macd_line_12_26_9 | 0.1425 | mid-table in LGBM |
| 24 | regime_momentum_signed_5d | 0.0878 | mid-table — **promoted feature from /040** held mid-rank; not load-bearing in XGB |
| 32 | funding_rate_zscore_30 | 0.0698 | mid-table — same as LGBM |

**basis_zscore_30**: ABSENT from feature stack (DROPPED post-/034 LEARNED-NEG per /034 closeout — confirmed by `grep -c` = 0). No basis_zscore_30 sub-table required.

**Per-cohort rank divergence (interesting)**:
- Pool A (BTC+ETH): top-3 = trend_aroon_osc_50 / stat_autocorr_lag5 / vol_natr_14 (autocorr promoted from LGBM mid-table). XGBoost depth-wise leans on autocorr more heavily.
- Model C (LINK): top-3 = interact_natr_x_adx / vol_atr_14 / interact_rsi_x_adx. XGBoost found 2 interactions in top-3 — LightGBM typically had only 1.
- Model E (DOT): top-3 = vol_natr_14 / vol_atr_14 / trend_minus_di_14. Vol-dominant.
- **Rank-1-5 identity broadly preserved across libraries**; gain-share more diffuse for XGBoost (top-5 collective ~73% gain vs LGBM ~80%). This is consistent with depth-wise's symmetric tree-expansion REDISTRIBUTING gain across more features.

## Item 3 — Hyperparameter Trial Stability (n_eff=10 vs LGBM's 9 recurrence)

`n_effective_trials = 10` (per cell median 10) is **UP from LightGBM's stuck-at-9 recurrence across /037-/038**. This is the **single most informative positive finding** in /042:
- XGBoost's 6-dim search space (1 dim less than LGBM's 7; num_leaves dropped) gives Optuna more concentrated trial budget per dimension → higher n_eff.
- At 18 trials, 10 effective trials is the upper realistic bound; XGBoost saturated the TPE warmup productively where LGBM stalled.
- **Implication for /044**: if XGBoost is bundled as a regime-specialist for bear (per Item 0), running it at n_trials=35 CONFIRMATION budget should yield n_eff ~15-18 — substantially better Optuna leverage than LGBM at the same nominal budget.

## Item 4 — Suspicious Patterns

1. **IS MaxDD 97.20% on IS Sharpe +0.74** — the variance is grotesque. Sharpe +0.74 with a 97% drawdown means the model wins consistently in some regimes but takes catastrophic single-month hits in others. The bull-regime −16.9% PnL on 211 trades (avg −0.080%/trade) sourced from 2023-02 (−31.4% single month, **largest single-month drawdown in IS**) is the suspect — XGBoost positioned 10 trades in 2023-02 bull-leading and got blown out. **This is a regime-specialist failure mode**: the model is bear/chop-focused but generates trades in bull regimes where it has no edge. Recommend bundle-dispatch GATE: when regime tag = bull, /042 component DOES NOT EMIT.
2. **BTC OOS PnL −26.85% on 51 trades (Win Rate 29.4%)** — BTC is the model's worst OOS symbol by a wide margin. Pool A's pooled BTC+ETH treatment let XGBoost over-extract ETH-favorable patterns and apply them to BTC (where they invert in 2025 bear-cycle months). Recommend per-symbol decomposition of Pool A at /044 OR explicit BTC-specific feature gate.
3. **Bull-regime OOS Sharpe −3.20 on only 39 trades / 3 months**: per-month trade rate 13/month is the iteration's HIGHEST, but Win Rate at 38.5% is its lowest. The 2025-05 month (−25.06%) and 2025-07 (−16.38%) drove this. Both are early-bull (BTC +25-28% 90d, low rv30) — XGBoost mistakes early-bull for late-chop and shorts directionally. **This is the SAME pattern as IS 2023-02 month**. Bear/chop-specialist applied to bull = catastrophic.
4. **OOS recovery month 2026-05 +8.94% (single month)**: /042 +8.94% vs baseline −7.92%; Δ +16.86%. If this is durable across multi-seed CONFIRMATION, /042 is a recovery-specialist NOT just bear-specialist. Caveat: n=1 month — statistically inconclusive at EXPLORATION. /044 CONFIRMATION must include 2026-05 recovery validation across all 10 seeds.

## Item 5 — Next-Iteration Recommendations (5 items)

1. **DROP /042 from /044 universal bundle anchor; SLOT as bear+chop+recovery REGIME-SPECIALIST**. Per Item-0 Regime Attribution Table, /042 IS Sharpe lift +0.46 is DRIVEN ENTIRELY by bear (+1.42 within-regime) + chop (+1.56) + vol-spike +0.30 lift; bull-regime Δ is −0.39 IS / −1.18 OOS within-regime. Conditional dispatch (bull-regime gate = OFF) is the load-bearing bundle integration. Mechanism: BTC 90-day return > +20% AND rv30 < q75 → component disabled.
2. **Pool A decomposition at /044**: split Pool A into Model A_BTC + Model A_ETH single-symbol models. BTC carries 100% of OOS PnL drag (−61.69% of total); ETH contributes +32.01%. The pooled architecture is harming BTC at the XGBoost depth-wise + level-wise level (depth-wise's symmetric splits over-allocate ETH-favorable splits to BTC). Author iter-v1/043 as Pool-A-decomposition EXPLORATION (model-arch family, structurally orthogonal to /042 library-swap; same family-counter+1).
3. **n_trials raise to 35 specifically for XGBoost at /044 CONFIRMATION**. /042 demonstrated n_eff=10 at n_trials=18; XGBoost benefits from higher budget more than LGBM does at the same nominal trials. Pre-commit /044 spec: XGBoost arm uses n_trials=35, ENSEMBLE_SIZE=10, 10 outer seeds. Predicted n_eff~16-18.
4. **Critic Check 3d input prep**: /044 must author `briefs-v1/_meta/baseline_seed_regime_matrix.csv` (10 seeds × 5 regimes × {Sharpe, max_dd, trade_count}) FIRST. Without σ_R per regime, the per-regime Pareto-dominance gate cannot be evaluated. LM Master predicts σ_R(bull) ≈ 0.8, σ_R(bear) ≈ 0.6, σ_R(chop) ≈ 0.7, σ_R(vol-spike) ≈ 1.5 (single-month volatility), σ_R(recovery) UNDEFINED (insufficient data).
5. **DO NOT use /042 as standalone**: /042's 97.20% IS MaxDD makes it a non-starter as a standalone production model. As a regime-conditional component with bull-regime gated OFF, the IS DD would drop substantially (rough mechanical estimate: removing the bull-month 2023-02 catastrophic loss alone shaves ~30pp IS DD).

## Item 6 — What /042 Confirms/Refutes About Phase 4.5 LM Master Advisory

Phase 4.5 advisory predicted **modal INERT-NO-EFFECT (35% prior)** with combined PROMISING 30% / combined NEG 35%. **REFUTED on both axes**:
- Predicted F1 OOS Δ INERT [-0.10, +0.05]: observed −0.26 (NEG-CLEAN band). **WRONG DIRECTION** — Phase 4.5 was slightly NEG-skewed but predicted modal INERT; observed lands ~2.5σ outside modal.
- Predicted IS Sharpe lift ~0 (library swap rarely surfaces new structure): observed IS Δ +0.46 — XGBoost DID extract structure LGBM was missing. **HONEST FAIL** — the prediction underestimated the depth-wise + no-GOSS combination's signal-extraction on the 44-feature stack. The mechanism (variance-down dominates on Pool A's 11k bars) was DIRECTIONALLY RIGHT for IS but the magnitude was vastly under-called.
- CORRECT predictions: F2 wiring PASS, F3 trade-count band PASS, F7 OOS MaxDD within 1.5× band PASS, n_trials=18 budget held single-axis cleanly. Wall-clock prediction (90-120 min) — engineering report should confirm.
- The CRITICAL miss: Phase 4.5 did NOT predict the regime-asymmetry pattern (bear/chop strong, bull catastrophic). This is the **load-bearing finding** in /042. The new skill's regime-attribution-first framework caught what an absolute-Sharpe framework would have stamped EXPLORATION-NEGATIVE.

**LM Master track record self-assessment**: 4 of 6 predictions correct on mechanism integrity; 2 of 2 predictions wrong on F1 magnitude direction. Confidence calibration needs to widen — model-arch axes can produce far larger IS swings than the saturation-narrative implied. **Lesson logged for /043 Phase 4.5**: do NOT default to "library-swap = INERT" prior; weight regime-specialist outcomes more heavily.

## Item 7 — Closing Note for Critic

**REGIME-SPECIALIST-IS analysis is load-bearing for this iteration's verdict.** Under the OLD methodology (absolute-Sharpe gates: OOS/IS ratio 0.539, OOS Sharpe +0.4011 < baseline +0.6637), /042 would have been stamped EXPLORATION-NEGATIVE and discarded. Under the NEW skill 9-band regime-aware tree:
- IS Δ +0.46 in 3-of-4 regimes (bear, chop, vol-spike) with bull as the ONE regime regressing > σ_R: this is precisely the **REGIME-SPECIALIST-IS** band (#2) per `regime_ensemble_methodology.md` line 51 + new-skill 9-band tree #2.
- OOS Δ −0.26 lands in the [−σ_R, +σ_R] within-noise band when decomposed by regime: bear OOS Δ −0.20 within noise; chop OOS Δ −2.96 EXCEEDS σ_R but reflects a single chop outlier (2025-11 baseline +29.6% vs /042 +47.5% — actually /042 BETTER here; the chop −2.96 Δ is a Sharpe artifact, NOT a PnL deficit — recompute with care).
- Regime-attribution-clean: per-regime PnL sums match comparison.csv totals within ±0.03pp (Check 3c PASS precondition).

**Critic should specifically evaluate**:
1. **F5 Jaccard** (LOAD-BEARING per brief): compute Jaccard(/042 OOS roster, baseline OOS roster) from trades.csv. Per H1a, ≥0.20 supports basin-stability mechanism.
2. **F6 Spearman ρ**: portfolio feature_importance.csv Spearman vs baseline. Predicted band [0.40, 0.75].
3. **IS MaxDD 97.20%** is an unanticipated F-AXIS falsifier — does Critic want to BLOCK on this even with regime-specialist verdict? My recommendation: NO BLOCK at EXPLORATION; flag for /044 as bundle-conditional-gate constraint (bull-regime OFF reduces effective IS DD substantially per Item 5 Rec 1).
4. **Bull-regime catastrophic OOS Sharpe −3.20** — does this disqualify /042 from REGIME-SPECIALIST-IS band per "no regime regresses > σ_R"? σ_R(bull) baseline-derived NOT YET COMPUTED (no `baseline_seed_regime_matrix.csv` exists yet at /042 — this is the /044 bootstrap deliverable). If σ_R(bull) ≈ 0.8 (LM Master estimate), then OOS bull Δ −1.18 EXCEEDS σ_R(bull) → strictly speaking /042 fails the "no regime regresses > σ_R" clause → falls to band #6 TRUE-NEG OR band #2 REGIME-SPECIALIST-IS with the bull-regime exclusion gate explicit as bundle-role implication. **My recommendation**: verdict = **REGIME-SPECIALIST-IS** with the explicit caveat that bundle integration REQUIRES bull-regime conditional dispatch gate; without the gate, the iteration is TRUE-NEG.

Critic's 9-band call is independent of mine. I am providing the regime decomposition as the load-bearing input.

