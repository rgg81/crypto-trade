# iter-v3/087 — Research Brief — WHOLESALE universe-breadth EXPANSION 3→6 (cycle-3 EXPLORATION #6)

**Date**: 2026-05-17
**Branch**: `iteration-v3/087` (off the /086 closeout `3d05740`)
**Author**: QR (autopilot)
**Cycle**: 3, EXPLORATION slot #6 of 10 (`briefs-v3/cycle3_plan.md`). Cycle 3 is 0/5 clean PROMISING — /082 SUSPICIOUS, /083 NEGATIVE, /084 REFERENCE-REANCHOR, /085 SUSPICIOUS, /086 INERT.

---

## Section 0 — Data Split Declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are IMMUTABLE and untouched. All Phase 1-5 research — literature survey, candidate-symbol screening, EDA, axis selection — used **IS data only** (`open_time < 2025-03-24`). The committed EDA `analysis/iteration_v3-087/wholesale_breadth_expansion_eda.py` (SHA `1a117b2`) filters every candidate frame to `open_time < OOS_CUTOFF_MS` before any model is trained or any metric computed. No expansion symbol — no symbol set, no book size — was selected on any OOS metric. The QR sees OOS for the first time in Phase 7. Section 10 audits the no-cheating discipline explicitly.

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION** (cycle-3 EXPLORATION #6 of 10). **Single-axis**: a **WHOLESALE symbol-universe EXPANSION** — `V3_MODELS` grows from 3 symbols (BCH/LDO/TRX) to **6** by adding **GALAUSDT, MANAUSDT, SANDUSDT** in one step. This is **denominator expansion** — the Grinold-Kahn breadth lever (`IR = IC·√breadth`) — and is structurally distinct from the CLOSED swap-by-replacement family (/078 swapped LDO→ADA at constant count). Every incumbent is kept; 3 symbols are added; each added symbol gets one independent per-symbol LightGBM with the identical 14-feature stack, the identical `(2.0,1.0)`-ATR triple-barrier labeling, and the identical 7-gate risk stack — a fully **universal** addition (`feedback_v3_per_symbol_lifts_oos_breaks_is.md` satisfied: no per-symbol features, no per-symbol ATR, no per-symbol gates). EXPLORATION-mode 3-seed, `run_baseline_v3.py --exploration --n-trials 35`. Per `feedback_v3_dsr_mode_artifact.md`, Check-3 DSR/PSR are informational for an EXPLORATION; only per-cell PBO and CPCV `frac_positive_paths` are evaluated against thresholds.

**Two MANDATORY non-axis baseline-restore actions** accompany the setup (they are **not** a second axis — they restore the /059 anchor per Critic /086 Rec #3): (a) **drop the 3 perp-spot basis features** (`basis_zscore_30`, `basis_momentum_3`, `basis_extreme_flag`) — revert `V3_FEATURE_COLUMNS_TOP_N` from the 17-feature /086 stack to the 14-feature /059 anchor; (b) add those 3 basis names to the runner's pre-flight ABSENT-assertion list (the established `funding_regime_momentum_5d` pattern), so a future iteration cannot silently re-inherit them. The `fetch-spot` subcommand, `basis_v3.py`, and `data/spot/` cache are RETAINED as reusable infrastructure — only the 3 feature columns are dropped, per `feedback_v3_inert_features_at_higher_budget.md`.

## Section 1 — Hypothesis

**v3's 3-symbol universe makes the portfolio a near-single-symbol bet; a wholesale breadth expansion to 6 symbols raises the aggregate IS Sharpe — not by adding stronger symbols, but because the breadth/diversification benefit (`√N`) genuinely offsets the per-symbol weakness, since the per-symbol strategy-PnL streams are weakly correlated.**

Two cycles + five cycle-3 EXPLORATIONs have established that the conservative axes are exhausted (gate knobs, risk primitives, single-symbol swaps, labeling tweaks, instrumentation) and — the /086 7-FEED STRUCTURAL VERDICT — that the v3 per-symbol depth-3-5 LightGBM does not allocate split capacity to crypto-native feature families regardless of the feed (funding /019/023/024/082/085, microstructure /015, basis /086 — 7 families, all INERT). The remaining structural levers are **Direction 2 (breadth)** and **Direction 3 (a non-naive pooled model)**. This iteration is Direction 2.

**The Fundamental Law.** Grinold & Kahn (*Active Portfolio Management*, 1999): `IR = IC · √breadth`. Breadth — the number of independent forecasts per period — is a lever v3 has **never pulled at scale**: it has been locked to 3 symbols for the entirety of cycles 1-2 (20+ iterations) and all of cycle 3. The /078 finding quantifies the fragility: BCH dominates ~77% of IS wpnl; the 3-symbol portfolio is effectively a single-symbol bet, and any positive-edge change to a non-BCH symbol washes against BCH dominance. A 6-symbol book doubles the breadth and structurally dilutes the concentration.

**Why this is NOT /083.** /083 added ONE weak symbol (FILUSDT) and the aggregate IS Sharpe collapsed −0.9156. The /083 root error was **methodological**: it selected FIL on a per-symbol IS-edge screen and ignored the **diversification term**. A single-symbol add to a pooled book has no meaningful diversification offset — with N going 3→4, the variance-reduction `√(N/(1+(N−1)ρ̄))` barely moves, so one weak symbol's bad monthly-PnL stream drags the pooled monthly Sharpe almost one-for-one. A genuine WHOLESALE expansion (3 symbols at once, N going 3→6) is a different operation: it doubles breadth, and the correlation drag is governed by the **strategy-PnL correlation** — which EDA Section 2 shows is far lower than the price-return correlation that /021/069 wrongly measured.

## Section 2 — IS-Only Numerical Evidence

All tables from the committed EDA `analysis/iteration_v3-087/wholesale_breadth_expansion_eda.py` + `robustness_check.py` (EDA SHA `1a117b2`), IS-only, current data. The EDA builds a faithful per-symbol v3-style IS model — the 14-feature v3 stack from raw OHLCV, REAL v3 triple-barrier labels (`label_trades`, ATR(2.0,1.0), 21-candle timeout), a confidence-gated (0.45) IS-only expanding 24-month walk-forward LightGBM — for every incumbent and every candidate, and aggregates the per-symbol rosters into a pooled book exactly as v3 does.

**SCREEN SCOPE — LOAD-BEARING DISCLOSURE.** This is a **relative-ranking** screen, not a /059 reproduction. Every symbol runs through ONE identical un-tuned (fixed-LGBM-param) pipeline with NO Optuna and NO 7-gate risk stack. Its absolute Sharpe numbers therefore differ from the production v3 baseline (Optuna-tuned + risk-gated): the screen's incumbent-3 aggregate IS monthly Sharpe is −0.0761 against the production /084 reference of +0.83. Per the /083 closeout's hard lesson (the /083 screen under-predicted the realized IS damage ~24×), **the screen's aggregate-Sharpe Δ is a DIRECTION-ONLY signal, NOT an absolute-magnitude predictor.** The load-bearing outputs are: the **SIGN** of the aggregate-Sharpe Δ, the **CROSS-SYMBOL ranking**, and the **correlation structure** (T4). The Section 4 falsifier bands are set wide accordingly.

### 2.1 — T1: candidate pool screen (data depth, liquidity, listing)

The candidate pool is 16 deep-history liquid Binance-futures alts NOT in `V3_EXCLUDED_SYMBOLS` and NOT closed (HBAR/AVAX CLOSED at /021; ADA CLOSED at /078; FIL CLOSED at /083 — all four explicitly excluded). All 16 PASS the T1 screen (≥2200 IS bars post-60-day-burn-in; ≥$20M median daily quote volume): ATOM, ALGO, ETC, XLM, EOS, VET, XTZ, AAVE, UNI, CRV, FTM, RUNE, SAND, GALA, MANA, THETA. The chosen-3 detail:

| Symbol | First listing | IS bars (post burn-in) | Median daily quote vol |
|---|---|---:|---:|
| GALAUSDT | 2021-09-18 | 3669 | $131.3M |
| MANAUSDT | 2021-03-15 | 4215 | $51.9M |
| SANDUSDT | 2021-01-25 | 4362 | $96.5M |

All three are liquid large/mid-cap perps with full 24-month-training + multi-year IS-evaluation depth.

### 2.2 — T2: per-symbol IS edge — the chosen 3 carry positive standalone screen Sharpe

| Symbol | Role | IS trades | IS WR | IS monthly Sharpe (screen) | mean dur (candles) |
|---|---|---:|---:|---:|---:|
| BCHUSDT | incumbent | 2163 | 0.325 | **−0.3522** | 6.79 |
| LDOUSDT | incumbent | 237 | 0.464 | **+0.6137** | 6.54 |
| TRXUSDT | incumbent | 2151 | 0.364 | **+0.1564** | 6.82 |
| GALAUSDT | candidate | 913 | 0.400 | **+0.3024** | 6.94 |
| MANAUSDT | candidate | 1499 | 0.389 | **+0.3114** | 6.97 |
| SANDUSDT | candidate | 1485 | 0.352 | **+0.1289** | 6.62 |

The chosen 3 all have **positive standalone screen Sharpe** — and GALA (+0.302) / MANA (+0.311) screen *better* than two of the three incumbents (BCH −0.352, TRX +0.156). This is the explicit /083 contrast: /083's FIL had a **negative** standalone screen Sharpe (−0.137 in the /083 screen) and a far-more-negative production edge (−32% IS net PnL). GALA/MANA/SAND are not the FIL pattern. (12 of the 16 pool candidates had negative standalone Sharpe — confirming the chosen 3 are not a low bar; they are the genuine positive-edge tail.)

### 2.3 — T3: THE LOAD-BEARING TEST — aggregate book IS monthly Sharpe

v3 pools every per-symbol roster into ONE book; the headline IS monthly Sharpe is the Sharpe of the union roster's per-calendar-month PnL series. T3 measures it for the 3-symbol incumbent book and wholesale-expanded books, and decomposes it via the Bailey-LdP identity `SR_portfolio = mean_S · √(N / (1 + (N−1)·ρ̄))`:

| Book | Symbols | N | Aggregate IS monthly Sharpe | mean per-symbol Sharpe | mean pairwise PnL-corr ρ̄ | Δ vs incumbent-3 |
|---|---|---:|---:|---:|---:|---:|
| **incumbent-3** | BCH+LDO+TRX | 3 | **−0.0761** | +0.1393 | −0.1137 | 0.0 |
| wholesale-5 | +GALA+MANA | 5 | **+0.1475** | +0.2063 | +0.0563 | **+0.2235** |
| **wholesale-6** | **+GALA+MANA+SAND** | **6** | **+0.1610** | +0.1934 | +0.0869 | **+0.2371** |
| wholesale-7 | +GALA+MANA+SAND+EOS | 7 | +0.1242 | +0.1613 | +0.1260 | +0.2003 |
| wholesale-8 | +GALA+MANA+SAND+EOS+UNI | 8 | +0.1096 | +0.1341 | +0.0997 | +0.1856 |

**The result is decisive and the /083-drag-avoidance argument is direct.** The 3-symbol incumbent book has a *negative* aggregate IS monthly Sharpe (−0.0761) on the screen even though its mean per-symbol Sharpe is *positive* (+0.139) — because at N=3 with ρ̄=−0.11 the pooled-PnL volatility is high and one weak symbol (BCH −0.35) drags the union. Every wholesale book LIFTS the aggregate; the lift **peaks at N=6** (+0.2371). The greedy-marginal and own-Sharpe constructions converge on the *same* size-6 set (GALA+MANA+SAND) — robust. Beyond N=6 the marginal candidates (EOS +0.004, UNI −0.003) are essentially neutral and the aggregate plateaus then slowly declines as the correlation drag accumulates. **N=6 is the EDA-peak — it is the EDA-driven book size, not a wall-clock compromise.**

### 2.4 — T3b: per-candidate marginal aggregate-Sharpe lift (the genuine indifference-curve test)

Each candidate's marginal lift to the incumbent-3 aggregate Sharpe when added alone:

| Candidate | Marginal aggregate-Sharpe lift | | Candidate | Marginal lift |
|---|---:|---|---|---:|
| GALAUSDT | **+0.1530** | | THETAUSDT | −0.0621 |
| MANAUSDT | **+0.1407** | | CRVUSDT | −0.0743 |
| SANDUSDT | **+0.0670** | | VETUSDT | −0.1170 |
| EOSUSDT | +0.0037 | | ETCUSDT | −0.1731 |
| UNIUSDT | −0.0029 | | RUNEUSDT | −0.1890 |
| ALGOUSDT | −0.0091 | | FTMUSDT | −0.2633 |
| XLMUSDT | −0.0196 | | ATOMUSDT | −0.3405 |
| AAVEUSDT | −0.0539 | | | |

GALA/MANA/SAND are the **only 3 candidates with a clearly positive marginal lift** (EOS is borderline-neutral at +0.004). The cutoff is clean — there is a visible gap between SAND (+0.067) and EOS (+0.004). This is the genuine indifference-curve test: a candidate is worth adding when its marginal contribution to the *aggregate* Sharpe is positive — which depends on both its own edge AND its correlation to the existing book. The 13 negative-marginal candidates are exactly the symbols a per-symbol-Sharpe-only screen (the /083 error) would have wrongly cleared had they had decent standalone numbers.

### 2.5 — T4: the two correlations — why this is structurally NOT /083/021/069

The /021 (HBAR+AVAX) and /069 (ADA) expansions failed in part because they screened on **price-return correlation** — price diversity, not signal diversity. The correlation that governs the indifference curve is the correlation of the per-symbol **strategy monthly-PnL streams**:

| Correlation metric | Mean |·| across the universe |
|---|---:|
| Price-return correlation (the /021/069 metric — WRONG one) | **0.6066** |
| Strategy monthly-PnL correlation (the indifference-curve metric) | **0.2003** |

**A 3× gap.** The price returns of these alts move together (~0.61) — but the v3 triple-barrier classifier trades them at different times, in different directions, for different durations, so the per-symbol *strategy* PnL streams are only ~0.20 correlated. This is precisely why the breadth lever works: in `SR_portfolio = mean_S · √(N/(1+(N−1)·ρ̄))`, the correlation drag at the chosen-6 book is ρ̄ = +0.087 (T3) — small enough that `√(6/(1+5·0.087)) = √4.18 = 2.04×` breadth multiplier dominates. /021/069 measured 0.61, concluded "too correlated, no diversification," and either rejected good candidates or accepted bad ones — they measured the wrong thing. **The /083-drag-avoidance argument in one line: /083 dragged because a single weak symbol at N=4 has no diversification offset; a wholesale N=6 expansion at ρ̄(PnL)=+0.087 has a 2.04× breadth multiplier that the EDA shows genuinely lifts the aggregate Sharpe +0.2371.**

### 2.6 — Robustness: leave-one-out + per-month decomposition (from `robustness_check.py`)

**Leave-one-out** on the wholesale-6 book — drop any one symbol, recompute the 5-symbol aggregate Sharpe:

| Dropped | 5-symbol aggregate Sharpe |
|---|---:|
| BCHUSDT | +0.3171 |
| LDOUSDT | +0.1173 |
| TRXUSDT | +0.1168 |
| GALAUSDT | +0.0960 |
| MANAUSDT | +0.1061 |
| SANDUSDT | +0.1475 |

**Every 5-symbol subset stays positive (+0.096 … +0.317).** The size-6 lift is not driven by any single symbol — dropping the screen's worst performer (BCH) actually *raises* the aggregate, confirming the diversification mechanism is genuine and not a one-symbol artifact.

**Per-month decomposition (honest texture).** Over 37 common IS months, the 6-book monthly PnL exceeds the 3-book in 14/37 months. The Sharpe lift comes through the **mean**, not through beating most months: 6-book mean monthly PnL +36.81 (std 228.61) vs 3-book mean −8.07 (std 106.05). **The 6-book is a bigger book with bigger monthly swings — both the mean AND the std rise; the mean rises proportionally more, which is what lifts the Sharpe.** This is a screen-grade signal and is flagged honestly: the lift is a genuine mean improvement, not a variance collapse.

### 2.7 — T5: holding-time / roster-composition predictor

`feedback_v3_is_oos_regime_divergence.md` mandate — a book whose added symbols are duration-loaded relative to the incumbents loads the v3 IS/OOS regime factor. The incumbent pooled-roster mean trade duration is 6.79 candles. The chosen-3 added-symbol duration gaps:

| Added symbol | Mean duration (candles) | Gap vs incumbent pool |
|---|---:|---:|
| GALAUSDT | 6.94 | **+0.149** |
| MANAUSDT | 6.97 | **+0.181** |
| SANDUSDT | 6.62 | **−0.171** |

All three gaps are **well inside ±0.2 candles** — far below the +1.0 trade-selection-sub-channel trigger and the regime-loading concern threshold. The added symbols hold trades for essentially the same duration as the incumbents. This axis does NOT load the regime factor via roster duration. (For context, /078's SUSPICIOUS swap had a +2.23-candle gap.)

### 2.8 — Concentration: the structural target is hit

BCH IS trade-count share drops from **47.5%** (3-symbol book) to **25.6%** (6-symbol book) — the wholesale expansion genuinely dilutes the BCH concentration, which is the standing cycle-3 constraint #2 and the aspirational ≤30% top-symbol gate. (Trade-count share is the stable concentration proxy on the un-tuned screen; the production OOS PnL concentration is measured in Phase 7.)

## Section 3 — Proposed Changes (the single axis + the two baseline-restore actions + the data-fetch plan)

### 3.1 — The single axis: `V3_MODELS` 3 → 6

```python
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
    ("E (GALAUSDT)", "GALAUSDT"),   # <- /087 wholesale expansion
    ("F (MANAUSDT)", "MANAUSDT"),   # <- /087 wholesale expansion
    ("G (SANDUSDT)", "SANDUSDT"),   # <- /087 wholesale expansion
)
```

Each added symbol gets one independent per-symbol LightGBM, identical 14-feature stack, identical `(2.0,1.0)`-ATR triple-barrier, identical 7-gate risk stack — fully universal. No labeling change, no feature change beyond the basis-revert, no risk-gate change, no model-architecture change, no seed change.

### 3.2 — REQUIRED_GAP recompute: 66 → 132

The pooled-CPCV purge gap `REQUIRED_GAP = (timeout_candles+1) × n_symbols = (21+1) × 6 = 132`. Changes in `src/crypto_trade/strategies/ml/validation_v3.py:65` (`REQUIRED_GAP = (21 + 1) * 6`) and the runner's `_canonical_v059` config-accretion table (`run_baseline_v3.py:980`, expected value 66 → 132). The runner's `_verify_label_leakage_gap` computes `(21+1)×len(V3_MODELS)` dynamically and asserts equality — it auto-tracks the 6-symbol universe. The **per-cell** `PER_CELL_GAP` stays **22** — it operates on a single-symbol `(symbol, month)` cell, so the `×n_symbols` factor does NOT apply (the /084 methodology fix; `PER_CELL_GAP` is unchanged).

### 3.3 — The two MANDATORY non-axis baseline-restore actions (Critic /086 Rec #3)

1. **Drop the 3 perp-spot basis features.** `V3_FEATURE_COLUMNS_TOP_N` in `src/crypto_trade/features_v3/__init__.py` reverts from the 17-feature /086 stack to the **14-feature /059 anchor** (`basis_zscore_30`, `basis_momentum_3`, `basis_extreme_flag` removed). /086 was INERT — the 3 basis features ranked 15/16/17 of 17; per `feedback_v3_inert_features_at_higher_budget.md` an INERT feature is not carried forward and not retested at a higher Optuna budget.
2. **Add the runner ABSENT-assertion ban.** The 3 basis names join the runner pre-flight ABSENT-assertion list (`run_baseline_v3.py` `_verify_feature_columns`), the established `funding_regime_momentum_5d` pattern — a future iteration cannot silently re-inherit them.

The `fetch-spot` subcommand, `basis_v3.py`, and `data/spot/` cache are NOT removed — RETAINED as reusable infrastructure; only the 3 feature columns are dropped.

### 3.4 — The data-fetch plan (Phase 6 engineering cost)

The 3 added symbols need fresh 8h klines + v3 feature parquets. GALA/MANA/SAND klines currently extend to 2026-02-28; the incumbents extend to 2026-05-16 — Phase 6 must refresh all 6 to a common extent. The Engineer's Phase-6 pre-flight:

```bash
uv run crypto-trade fetch --interval 8h --symbols BCHUSDT,LDOUSDT,TRXUSDT,GALAUSDT,MANAUSDT,SANDUSDT
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,GALAUSDT,MANAUSDT,SANDUSDT --interval 8h --track v3 --format parquet --workers 4
```

This is a real, legitimate engineering cost — the structural investment a breadth expansion requires. The v3 feature pipeline is symbol-agnostic (verified: the existing `VETUSDT_8h_features.parquet` carries all 14 V3 features), so feature generation is a known-good operation for the 3 new symbols.

### 3.5 — Config-accretion pre-flight update

`run_baseline_v3.py` `_canonical_v059`: the `V3_MODELS symbols` knob expected value updates `("BCHUSDT","LDOUSDT","TRXUSDT")` → `("BCHUSDT","LDOUSDT","TRXUSDT","GALAUSDT","MANAUSDT","SANDUSDT")`, and `REQUIRED_GAP` expected 66 → 132. These are the *declared* /087 axis deltas — they are documented here as deliberate and the check is updated, exactly the procedure the check's docstring prescribes. All other knobs stay /059-canonical (single-axis discipline). `ITERATION_LABEL` → `"v3-087"`.

## Section 4 — Expected OOS Impact (TWO-ANCHOR statement + falsifier + /083-drag argument)

### 4.1 — The TWO anchors (MANDATORY per Critic /084 Rec #2)

- **ANCHOR 1 — the cycle-3 EXPLORATION-MODE-REFERENCE: iter-v3/084, IS +0.8325 / OOS +0.3322** (3-seed EXPLORATION-mode, current data). /087 runs 3-seed EXPLORATION-mode — it is classified against this 3-seed reference. **All intra-cycle Δ classification in Section 8 uses ANCHOR 1.**
- **ANCHOR 2 — the /059 CONFIRMATION baseline: IS +1.0894 / OOS +0.5791** (10-seed CONFIRMATION-mode, tag `v0.v3-059`). RESERVED for the iter-v3/092 CONFIRMATION. /087 is NOT compared against ANCHOR 2.

Mixing the two — comparing a 3-seed EXPLORATION number against the 10-seed CONFIRMATION number — is the /082-/083 reference-architecture error the /084 closeout corrected. /087 uses ANCHOR 1 only.

### 4.2 — Predicted Δ vs ANCHOR 1 (/084)

The EDA's screen-grade aggregate-Sharpe Δ of **+0.2371** is a **DIRECTION-ONLY** signal — per the /083 closeout, the screen is NOT an absolute-magnitude predictor (the /083 screen under-predicted ~24×). The honest forecast: a wholesale expansion that the EDA shows LIFTS the screen aggregate Sharpe by a clearly positive, robust margin (+0.2371, leave-one-out all positive) **should** produce a production result that is at minimum **not a NEGATIVE-class IS collapse** and plausibly an IS lift. The central forecast: **IS Δ in [−0.10, +0.30] vs /084** (an honest band — the diversification math supports a lift, but the production Optuna + 7-gate stack can compress or amplify it). OOS is genuinely uncertain — a 6-symbol book has 2× the breadth, which *should* dampen the OOS single-symbol fragility, but the screen does not predict OOS magnitude.

### 4.3 — The LOCKED falsifier band (pre-registered, single-axis universe-expansion)

| # | Falsifier | Trigger | Classification implied |
|---|---|---|---|
| F1 | **Aggregate IS collapse** — the /083 / /021 failure mode reproduced | IS monthly Sharpe Δ vs /084 **< −0.20** | NEGATIVE |
| F2 | **OOS-DOMINANT regime-loading** | IS Δ < 0 **AND** OOS Δ vs /084 ≥ +0.20 | SUSPICIOUS |
| F3 | **OOS/IS ratio gate** | OOS/IS monthly Sharpe ratio **> 3.0** | SUSPICIOUS |
| F4 | **Trade-selection sub-channel** (the /076 channel) | added-vs-removed OOS-roster mean-duration gap **> +1.0 candle** | SUSPICIOUS |

F1 is the direct /083-failure-mode falsifier. If F1 fires, the wholesale expansion dragged the aggregate exactly as /083's single-symbol add did, and the breadth thesis is falsified for this symbol set. F2/F3/F4 are the standing SUSPICIOUS gates (`feedback_v3_oos_is_ratio_gate.md`; `feedback_v3_is_oos_regime_divergence.md`). **These are LOCKED numeric gates — `feedback_v3_per_symbol_target_axis_falsifier.md`: predictions are estimates, falsifiers are gates; a firing falsifier cannot be downgraded by a mechanism argument.**

### 4.4 — Pre-registered roster-composition / holding-time predictor

Per `feedback_v3_is_oos_regime_divergence.md` and `feedback_v3_per_symbol_target_axis_falsifier.md` — for a universe axis, pre-register the target-axis falsifier band, not just the non-target. **Target-axis prediction: the 3 added symbols (GALA/MANA/SAND) collectively contribute an OOS-roster mean trade duration within ±1.0 candle of the incumbent pooled-roster mean duration.** EDA T5 measured the IS added-symbol duration gaps at +0.149 / +0.181 / −0.171 — all inside ±0.2; the production OOS prediction is the same order. The pre-registered **target-axis falsifier**: if the added-symbol OOS-roster mean duration is > +1.0 candle longer than the incumbent pooled roster, the expansion loaded the regime factor via the added symbols' roster → SUSPICIOUS (this is F4 above, evaluated on the added-symbol subset in Phase 8).

### 4.5 — The /083-drag-avoidance argument (explicit, the load-bearing Section-4 claim)

/083 dragged the aggregate IS Sharpe −0.9156 because: (a) it added ONE symbol — N going 3→4 — so the diversification offset `√(N/(1+(N−1)ρ̄))` barely moved; (b) FIL had a genuinely negative production edge; (c) it screened FIL on per-symbol Sharpe alone, ignoring the correlation/diversification term. /087 differs on **all three**: (a) it is a WHOLESALE expansion — N going 3→6, a 2.04× breadth multiplier at the chosen book's ρ̄(PnL)=+0.087; (b) the 3 added symbols all have *positive* standalone screen Sharpe (GALA +0.302, MANA +0.311, SAND +0.129 — two of them beating incumbents), explicitly NOT the FIL pattern; (c) the symbols were selected on the **aggregate-book Sharpe** under the Bailey-LdP indifference-curve framework, with the strategy-PnL correlation (0.20) — not the price-return correlation (0.61) /021/069 wrongly used — as the governing correlation. The EDA's load-bearing T3 result is that the broader book's aggregate IS Sharpe is **preserved AND lifted** (+0.2371, leave-one-out all positive), which is the explicit precondition the orchestrator's directive set for running a wholesale expansion. **If the production run nonetheless shows F1 (aggregate IS collapse), the honest reading is that the production Optuna+gate stack does not transfer the screen's diversification benefit — and the wholesale-expansion axis is closed for this symbol set, recorded in Dead Ideas.**

## Section 5 — Risk Mitigation

The axis is itself a risk-mitigation: a 6-symbol book structurally **reduces** the BCH single-symbol concentration risk (47.5%→25.6% IS trade-count share on the screen) — concentration is the standing cycle-3 constraint #2. The 7-gate risk stack (BTC-trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate-disabled) is applied **unchanged and universally** to all 6 symbols — every added symbol inherits the identical, IS-calibrated risk gates with no per-symbol tuning. No new risk primitive is introduced (a new risk primitive would be a second axis). The R-layer simulated-historical-effect requirement is satisfied by the gate stack being /059-canonical and unchanged: its IS-calibrated thresholds and historical behavior are the /059-validated ones, applied to a larger universe.

## Section 6 — Risk Management Design

No new risk gate, no new kill-switch, no new drawdown brake — the single axis is the universe expansion; introducing a risk primitive would violate single-axis discipline. The existing 7-gate stack (RiskV3, /059-canonical) handles all 6 symbols. The config-accretion pre-flight (`_canonical_v059`, 11 knobs) asserts every RiskV3 knob equals /059-canonical at runtime — the only declared deltas are `V3_MODELS symbols` (3→6) and `REQUIRED_GAP` (66→132), both documented in Section 3.5 as the deliberate /087 axis. Any other knob drift raises at runtime.

## Section 7 — Pre-Registered Failure-Mode Prediction (honest)

v3 is 0/5 clean PROMISING in cycle 3 and 1-edge-ingredient across 3 cycles + 26 EXPLORATIONs. Universe expansion as an axis has a 3-failure track record (/021 HBAR+AVAX NEGATIVE, /069 ADA, /083 FIL NEGATIVE) — although all three were *single-or-double* symbol adds screened on the wrong metric, which this iteration corrects. The honest pre-registered distribution:

- **≈40% — PROMISING-or-INERT-mild.** The EDA's +0.2371 screen lift + the all-positive leave-one-out + the clean correlation structure are the strongest pre-backtest case any cycle-3 EXPLORATION has had for a structural lift. But "PROMISING at EXPLORATION" requires both IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /084; the production Optuna+gate stack can compress the screen lift. The most likely *favorable* outcome is a modest IS lift that lands PROMISING or just short of it (INERT-mild — IS Δ inside [0, +0.10]).
- **≈30% — NEGATIVE (F1).** The /083 / /021 failure mode: the production multi-symbol Optuna+gate stack does not transfer the screen's diversification benefit, and the aggregate IS Sharpe regresses. The screen is a relative-ranking tool — the /083 closeout proved it can under-predict the production damage by ~24×. A wholesale 3-symbol add is 3× the integration surface of /083's single add; if the added symbols' production-tuned models behave worse than the screen implied, the aggregate collapses. This is the single most-likely *failure* path and is named as such.
- **≈25% — SUSPICIOUS (F2 / F3 / F4).** The persistent cycle-3 pattern (3 of 5 cycle-3 EXPLORATIONs were SUSPICIOUS-or-SUSPICIOUS-flavored). A wholesale expansion changes the pooled book substantially — the OOS roster can shift toward longer-held trades (F4) or the OOS can soar on a flat/negative IS (F2, the /082/078 signature). Universe changes have a documented history of loading the OOS regime factor (/078). Given the cycle-3 base rate, SUSPICIOUS gets a non-tail weight — F4 in particular is not a tail (the /085/086 closeouts both flagged it).
- **≈5% — NULL-RESULT.** Adding 3 symbols changes the pooled book and `REQUIRED_GAP` — the /087 roster cannot be bit-identical to /084's. Listed for taxonomy completeness only.

**Calibration note.** The central forecast leans PROMISING-or-INERT-mild (≈40%) because the EDA evidence is genuinely the strongest structural case in cycle 3 — but NEGATIVE (≈30%) is given a deliberately heavy weight because universe expansion has failed 3×, the screen is a known under-predictor, and a wholesale add is a large integration surface. The brief does NOT float PROMISING above what the evidence supports: the screen lift is direction-only, the production transfer is uncertain, and the honest modal outcome is "modest lift OR collapse."

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED classification taxonomy)

EXPLORATION — does NOT merge regardless; an EXPLORATION cannot update BASELINE_V3.md. The taxonomy classifies the result for the cycle-3 catalog and the /092 CONFIRMATION-bundle decision. **Disjunctive precedence, first match canonical: SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL-RESULT.** All Δ vs **ANCHOR 1 (/084, IS +0.8325 / OOS +0.3322)**.

### 8.1 — PROMISING
IS monthly Sharpe Δ vs /084 **≥ +0.10** AND OOS monthly Sharpe Δ vs /084 **≥ +0.20** AND CPCV `frac_positive_paths` **≥ 0.55** AND NOT SUSPICIOUS. (A PROMISING universe-expansion advances to the /092 CONFIRMATION bundle as the candidate 6-symbol universe.)

### 8.2 — NEGATIVE
IS monthly Sharpe Δ vs /084 **< −0.10** OR OOS monthly Sharpe Δ vs /084 **< −0.20** (and NOT SUSPICIOUS). F1 (IS Δ < −0.20) is the strong-form NEGATIVE — the /083 failure mode.

### 8.3 — SUSPICIOUS (evaluated FIRST). Fires on ANY of four sub-channels:
- **(a) OOS/IS monthly Sharpe ratio > 3.0** (F3).
- **(b) OOS-DOMINANT sub-mode** — IS Δ < 0 AND OOS Δ ≥ +0.20 (F2).
- **(c) the /076 trade-selection sub-channel** — on the /084-anchor OOS roster diff, the added-vs-removed OOS-roster mean trade-duration gap **> +1.0 candle** (F4; robust across ≥2 of the 3 trade-identity keys).
- **(d) the added-symbol target-axis sub-channel** — the GALA+MANA+SAND OOS-roster mean trade duration is **> +1.0 candle** longer than the incumbent (BCH/LDO/TRX) OOS pooled-roster mean duration (the Section 4.4 pre-registered target-axis falsifier).

### 8.4 — INERT
IS monthly Sharpe Δ vs /084 **∈ [−0.10, +0.10]** AND OOS Δ does not clear the +0.20 PROMISING leg, AND NOT SUSPICIOUS. (A universe expansion that neither lifts nor collapses the aggregate — the breadth benefit did not transfer but did no harm.)

### 8.5 — NULL-RESULT
The /087 OOS roster is bit-identical to /084's. Mechanically impossible here (3 symbols added, `REQUIRED_GAP` changed) — listed for taxonomy completeness.

**Phase-8 roster-diff requirement.** Sub-channels (c) and (d) require the Phase-8 OOS roster-diff (`analysis/iteration_v3-087/roster_diff_oos.py`, the /085/086 method precedent) — the /086 and /084 OOS rosters compared by trade-identity key, with the added-vs-removed duration gap and the added-symbol-subset duration gap computed. The QR runs this in Phase 8 before finalizing the Section-8 classification.

## Section 9 — Library Stack Declaration

No new libraries. The axis is a `V3_MODELS` tuple change + a `REQUIRED_GAP` constant + a feature-list revert; the EDA uses only `numpy`, `pandas`, `lightgbm` (already pinned). Pinned stack unchanged: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1.

## Section 10 — QR Audit Trail (literature-research path + axis selection)

### 10.1 — The orchestrator's lead steer and the QR call

The orchestrator's dispatch named **Direction 2 — wholesale universe-breadth expansion** as the lead candidate (and Direction 3 — a non-naive pooled model — as the alternative). Per `feedback_v3_axis_selection_quant_discipline.md` the QR makes the final call with committed EDA backing. The QR committed Direction 2 — the wholesale expansion — backed by the committed EDA `analysis/iteration_v3-087/wholesale_breadth_expansion_eda.py` (SHA `1a117b2`). The decisive EDA evidence: the wholesale-6 book's aggregate IS monthly Sharpe lifts +0.2371 over the 3-symbol book, robust under leave-one-out, with the strategy-PnL correlation structure (ρ̄ = +0.087) confirming the breadth benefit genuinely offsets the per-symbol weakness — the explicit precondition the orchestrator set for running a wholesale expansion. Direction 3 (a non-naive pooled model) was NOT selected: the naive pooled model was EDA-falsified at /085, and the EDA budget was spent on the breadth axis where the orchestrator's lead steer and the cycle-3-plan HIGH-priority directions both point. The QR's axis call is the wholesale expansion; this is not a superseded-orchestrator-pick case (the QR adopted the lead steer after the EDA confirmed it), so no rewrite/revert was needed.

### 10.2 — Literature-research path (genuine WebSearch/WebFetch, Phases 1-4)

| # | Source | Finding it contributes |
|---|---|---|
| 1 | **Grinold & Kahn, *Active Portfolio Management* (1999)** — the Fundamental Law. (Robeco 2018 explainer; analystprep CFA-L2 notes; OMSCS-notes ML4T module — all WebSearch-surfaced.) | `IR = IC · √breadth`. Breadth — independent forecasts per period — is the lever; the Sharpe ratio grows as `√breadth`. v3 has never pulled it: 3 symbols for 26 EXPLORATIONs. A 3→6 expansion doubles breadth. This is the iteration's core thesis. |
| 2 | **Bailey, López de Prado & del Pozo, "The Strategy Approval Decision: A Sharpe Ratio Indifference Curve Approach" (2012/2013, SSRN 2003638; *Algorithmic Finance* af018; davidhbailey.com PDF).** | The Strategy Approval Theorem: a new return stream RAISES the portfolio Sharpe when its average pairwise correlation to the approved set is low enough — *even at a below-average or negative own Sharpe*. There is no fixed SR threshold; there is an indifference curve over (own Sharpe, correlation-to-book). This is the framework the /083 per-symbol-Sharpe screen ignored — and the EDA's T3 (Bailey-LdP decomposition) and T3b (per-candidate marginal lift) operationalize it directly. |
| 3 | **Crypto cross-sectional / portfolio-size literature** (arXiv 2505.24831 "Optimising cryptocurrency portfolios through stable...", 2024-2025; the multi-crypto-portfolio survey set — all WebSearch-surfaced). | Empirical finding: crypto portfolios of **~10 assets** delivered better risk-adjusted returns than 5 or 15; "medium portfolios kept better Sharpe ratios than both smaller and institutional accounts." Crypto factors sorted by size/momentum diversify genuinely. This bounds the expansion: more breadth than 3 helps, but the benefit is not unbounded — consistent with the EDA's N=6 peak (the aggregate Sharpe plateaus then declines past 6 as the correlation drag accumulates). |
| 4 | **Multi-task gradient boosting literature** (ScienceDirect S0957417425043118 "Robust multi-task gradient boosting"; the pooled-vs-per-asset crypto-ML comparison set — WebSearch-surfaced). | Pooled ("data pooling") treats all assets as identical; single-task ignores cross-asset synergy; multi-task GBM is the middle ground. Asset-specific volatility means a naive pool can be sub-optimal. This is why /087 keeps the **per-symbol model architecture** (one independent LightGBM per symbol — the v3 single-task design) for the wholesale expansion, rather than coupling the expansion with a pooled model (Direction 3). It also confirms the /085 EDA's falsification of the *naive* pool — a sound future axis would be multi-task, not naive pooling. |

The research path: WebSearch on the Fundamental Law established the breadth thesis (source 1); WebSearch on crypto cross-sectional portfolios surfaced the Bailey-LdP indifference curve as the rigorous tool for *which* symbols to add (source 2) and the empirical ~10-asset portfolio-size finding (source 3); WebSearch on pooled-panel ML (source 4) confirmed the per-symbol architecture is the right vehicle for the breadth axis (the pooled model is a separate, future axis). The EDA then operationalized the indifference-curve framework on v3's own IS data: T3 measures the aggregate-book Sharpe via the Bailey-LdP identity, T3b the per-candidate marginal lift, T4 the load-bearing strategy-PnL correlation (vs the price-return correlation /021/069 wrongly used). The axis — wholesale 3→6 expansion with GALA/MANA/SAND — is the EDA-derived answer to "does the breadth benefit genuinely outweigh the per-symbol-weakness drag," and the EDA says yes (+0.2371, leave-one-out all positive).

### 10.3 — No-cheating audit

- `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` — IMMUTABLE, untouched.
- The EDA filters every candidate frame to `open_time < OOS_CUTOFF_MS` before training or scoring — every T1/T2/T3/T4/T5/T6 number is IS-only.
- No expansion symbol, no book size, no design parameter was selected on any OOS metric. The book size (6) is the EDA's IS aggregate-Sharpe peak; the symbol set (GALA/MANA/SAND) is the EDA's IS marginal-lift top-3.
- `CONF_THRESHOLD = 0.45` and `NEUTRAL_EDGE_PCT = 0.5` in the EDA are data-free a-priori choices (not tuned on IS or OOS) — the screen's selectivity analogue of the 7-gate stack.
- The QR sees OOS for the first time in Phase 7.

## Section 11 — Reproducibility Stamp (backfilled at setup)

- EDA SHA: `1a117b2` (`analysis/iteration_v3-087/wholesale_breadth_expansion_eda.py` + `robustness_check.py` + the T1-T6 CSVs)
- Brief SHA: (this commit)
- Setup SHA: (backfilled by the setup commit)
- Phase 5.5 gate SHA: (backfilled)
- ITERATION_LABEL: `v3-087`
- Run command: `uv run python run_baseline_v3.py --exploration --n-trials 35` (3-seed EXPLORATION-mode, 6-symbol universe)
- Estimated wall-clock: ~1.6h (linear-in-trials extrapolation from /084 3-symbol 0.70h / 315 trials and /083 4-symbol 1.00h / 420 trials; /087 is 6 symbols × 3 seeds × 35 = 630 trials → ~1.6h base, ~1.9h with 6-symbol CPCV/per-cell-PBO/report headroom — within the 2h EXPLORATION cap). Book size 6 (not 8) is the EDA-peak AND keeps the run within the cap.
- Hardware: x86_64, 60 GB RAM, WSL2 / Linux 6.6.114.1
- Library stack pinned: lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1
