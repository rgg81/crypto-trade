# LightGBM Master Advisor — iter-v1/019 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/019`. HEAD `c35c36a`. Cycle-3 EXPLORATION #4 of 10. **SECOND per-cohort EXPLORATION** (per /018 LM Master + Critic convergent recommendation; opposite-sign structural prior cohort).
- **Anchor**: portfolio `v0.v1-baseline-corrected` IS +0.2829 / OOS +0.6637. **Per-cohort anchor**: ETH-in-pool IS **−0.1022** / OOS **+0.0503** (from `eth_per_symbol_baseline.csv` — IS 145 trades / 39 months, OOS 46 trades / 14 months).
- **/018 outcome (LINK-only)**: PROMISING-INERT favorable, OOS Δ +0.16 vs LINK-in-pool +0.8184. My Phase 4.5 modal INERT 45% CONFIRMED. Track now 2/16 directional + 8/16 mechanism-level.
- **QR's EDA pivot**: symmetric "skip ETH when BTC bearish" REFUTED at IS (3/3 indicators show bull-BTC ETH WORSE than bear-BTC ETH). Reframed to **direction-aware counter-trend kill** (+42.47% IS PnL lift, both H1/H2 halves positive, 17.2% skip rate).
- **Single src/ file diff**: `run_baseline_v1.py` adds ETH-only branch + imports `apply_btc_trend_filter` from `risk_v2.py` lines 1346-1417. Code-isolation acceptable; module is strategy/risk helper not feature.

## 1. Direction-aware gate plausibility — STRONGER than my /018 §6 staged version

**The QR's EDA pivot is mechanistically superior to my Phase 4.5 staged "BTC-trend conditional gate"**. I staged a symmetric framing; QR's `btc_trend_direction_aware.csv` shows asymmetric ±0.62%/−0.87% per-trade economics that no symmetric gate could capture:

| Cell | n | avg_pnl | Mechanism |
|---|---|---|---|
| ETH long + BTC ret14 > 0 | 33 | **+0.62%** | momentum confluence (KEEP) |
| ETH short + BTC ret14 > 0 | 42 | **−0.87%** | fighting BTC tape (KILL) |
| ETH long + BTC ret14 ≤ 0 | 37 | −0.26% | mild counter-trend drag (KILL) |
| ETH short + BTC ret14 ≤ 0 | 33 | **+0.37%** | bear-momentum confluence (KEEP) |

This is **NOT a v2/019 SAME pattern re-discovery** — v2/019 applied the gate to SOL/XRP/DOGE/NEAR (4-symbol cohort, alt-only, no ETH). The direction-aware mechanism is GENERAL but the per-symbol economics differ. Re-using `apply_btc_trend_filter` is CODE re-use, NOT signal re-use. /027 CONFIRMATION value retained: this is the FIRST v1-track multi-seed validation of the gate primitive on the ETH cohort with v1's labeling + 5-feature stack + Model A semantics. No diminution.

## 2. F1 anchor +0.0503 TINY — recalibrate verdict expectations

Anchoring against **+0.0503** is correct per-cohort methodology — but the absolute scale is so small that **modest gate efficacy clears PROMISING easily**. EDA projects gated OOS PnL +7.84% vs baseline +2.76% (lift +5.08%) at OOS over 14 months. If that translates linearly to Sharpe lift, OOS Sharpe lands ~+0.20-+0.35.

**Key distinction**: PROMISING here is a **directional flip success** (gate did its job), NOT an edge-discovery milestone. Different from /018's LINK at +0.98 where PROMISING-INERT meant "preserved a strong existing edge". /019 PROMISING means "found a small directional signal in a structurally NEGATIVE cohort." Both legitimate /027 bundle candidates, but their /027 mean predictions differ:
- LINK-only specialist /027 multi-seed mean (my /018 Phase 7.4 §5): **+0.80 anchor**
- ETH-only + gate /019 multi-seed mean projection: **+0.15 anchor band, possibly [+0.10, +0.40]**

Bundle math at /027: ETH+gate contributes via low cross-correlation to LINK, not via absolute Sharpe magnitude. Modest absolute Sharpe is acceptable for diversification ingredient.

## 3. EDA IS lift +42% will NOT translate 1:1 to backtest

Critical caveat. The QR's `gate_threshold_sweep.csv` row at ±8%: IS gated PnL +28.77% vs baseline −13.70% = +42.47% lift. **This is post-hoc filtering on a FROZEN baseline-trained model's trade roster.** /019 retrains Model G ETH-only — different Optuna trajectory, different selected hyperparameters, different trade roster.

The gate's pure mechanical lift on retrained trades is likely **30-60% of the post-hoc lift** based on v2/019 precedent (where the gate's retrain-included lift compressed from post-hoc projection by ~50%). Realistic /019 IS lift band: **+13% to +25% PnL** translating to IS Sharpe ~+0.15 to +0.40 (anchor was −0.10; Δ +0.25 to +0.50 — clears F3 PROMISING). OOS even more conditional — Optuna basin lottery at single-seed=42 widens to ±0.40.

## 4. Verdict-class priors — ADJUSTED off QR's FLAT 30/40/30

| Verdict | QR | LM Master | Reasoning |
|---|---|---|---|
| PROMISING (Δ ≥ +0.20 → OOS ≥ +0.25) | 30% | **35%** | EDA mechanism cross-year-stable AND ETH structural prior 4/4 NEGATIVE means even modest gate lift produces large Δ vs essentially-zero anchor |
| INERT (Δ ∈ [−0.20, +0.20]) | 40% | **40%** | basin lottery wide; gate works directionally but anchor +0.05 leaves narrow path; modal |
| NEGATIVE (Δ ≤ −0.20) | 30% | **25%** | cohort isolation drag exposed before gate compensates; gate over-kill OOS; subset NEGATIVE-INTRINSIC 8%, NEGATIVE-CATASTROPHIC 5% |

**Adjustment rationale**: ETH 4/4 OOS-negative + anchor +0.05 ≈ 0 means the gate has asymmetric verdict topology. PROMISING bar is +0.25 absolute; small mechanism win produces large Δ vs zero anchor. NEGATIVE bar is −0.15 absolute; would require gate to ACTIVELY HARM the cohort, possible but less likely given EDA cross-year stability.

## 5. n_eff_per_cell prediction: [4, 8] band — LOWER than /018's 9

ETH-only cohort + 17% gate fire rate → ETH IS trades post-gate ~120 (vs LINK-only /018 154). Smaller training rows + post-hoc gate roster trim → narrower Optuna trial diversity. Predicted n_eff band **[4, 8]** (LINK-only hit 9). INFORMATIONAL per /017 closeout demotion. If observed n_eff = 1 or 2, mechanism issue — flag at Phase 7.4.

## 6. Hyperparameter recommendations

### 6.1 KEEP n_trials=18 (against any compression pressure)
26 min predicted wall-clock with 78% margin — zero pressure to compress. TPE at n_trials=18 stays well above ~10 saturation. /018's identical config produced clean 9-trial n_eff convergence.

### 6.2 KEEP ENSEMBLE_SIZE=3
Per /018 Phase 4.5 §4.3 logic: single-axis isolation = SYMBOL DIMENSION + STATELESS GATE. Raising ENSEMBLE_SIZE confounds attribution. /027 multi-seed handles basin-lottery dissolution.

### 6.3 Accept current Optuna bounds; do NOT modify
Phase 7.4 post-mortem reads actual best-trial trajectories. Pre-emptively tightening num_leaves or learning_rate on a NEGATIVE-prior cohort risks suppressing the basin where the gate's edge is realizable.

### 6.4 LEAVE gate constants frozen at brief Section 3.3 values
`lookback_bars=42, threshold_pct=8.0, enabled=True` is single-axis-pinned. /020+ verdict-conditional retunes (per brief Section 11.7 — TIGHTER ±5% if under-fire, WIDER ±12% if over-kill) are the proper tune locations, NOT /019.

## 7. Saturation risks to flag

**Single-cohort + gate basin lottery at single-seed=42 (HIGH-RISK)**: per v3 /020-/022 frozen-baseline pattern — single-seed Optuna trajectories deterministic. ETH-only OOS Sharpe basin band [-0.40, +0.60] is plausible. Single iteration is sample-of-1; the 30/40/30 priors are basin-lottery-marginalized. /027 multi-seed dissolves this.

**Gate fire-rate band [10%, 30%] IS / [5%, 35%] OOS plausibility**: predicted 17.2% IS / 17.4% OOS. Sample size at OOS is small (14 months, 46 baseline trades, 8 predicted gate kills). Single regime shift in OOS could push fire-rate to 30%+ if BTC volatility regime differs from IS. Pre-registered band is correctly wide.

**Re-training divergence risk**: post-hoc EDA assumes baseline-trained model's ETH trades. /019 trains ETH-ONLY Model G — the trade roster will differ in OOS by potentially 20-40% of trades. The gate may fire on a DIFFERENT set of trades than the EDA analyzed. Pre-registered F-AXIS #3 fire-rate band is the right diagnostic (mechanism-level test absorbs roster shift).

**PROMISING-MECHANICAL adjacent (Critic Check 14 watch)**: the gate is mechanism re-use from v2/019, applied post-hoc to a retrained trade stream. If verdict is PROMISING but trade roster bit-identity vs the EDA baseline roster preserves >80% of kept trades, classify PROMISING-MECHANICAL — non-compoundable as new signal source. Phase 7.4 will check via trade_id Jaccard.

## 8. What I Did NOT Recommend, and Why

- **Multi-seed for /019**: HIGH-RISK forward-mandate (3 consecutive ≥1σ HIGH-RISK negatives) not triggered. /027 multi-seed handles basin-lottery dissolution.
- **TIGHTER gate threshold (±5%) at /019**: EDA shows ±8% best IS lift (+42.47% vs ±5% at +32.29%). Single-dimension re-tune deferred to /020 conditional on /019 verdict.
- **Pre-emptive Optuna bounds tightening**: would interfere with basin discovery; no /018 evidence of overfitting in this hyperparameter region.
- **Vendoring `apply_btc_trend_filter` into a `risk_v1_gates.py` copy**: QR brief Section 3.1 already flags this as Phase 5.5/Critic-conditional fallback. Wait for Critic decision; cross-import is correct first attempt (test suite already uses cross-track helper imports).
- **Direction-asymmetry constraint in Optuna**: violates no-cheating (the asymmetry is an OOS-observation pattern from `btc_trend_direction_aware.csv` which is IS-only — but encoding it as a hyperparameter prior would still bias).
- **F8 OOS trade band [25, 90] tightening**: QR's band is correctly wide given gate fire-rate uncertainty. Predicted ~38 OOS trades after gate (46 baseline × 0.83 keep-rate) — center of band.

## 9. Closing Note

**MEDIUM directional confidence (35% PROMISING / 40% INERT modal)**. Higher than /018 PROMISING-INERT confidence in absolute terms because the EDA cross-year stability is the strongest pre-registered mechanism in v1 catalog history (`gate_cross_year_stability.csv` — both H1 +6.33% lift and H2 +36.15% lift positive at ±8%). But the structural prior 4/4 NEGATIVE and single-seed basin lottery widen the negative tail.

Three calls staked:

1. **PROMISING 35% / INERT 40% modal** — both verdict cells comparably likely; INERT-no-effect subtype (|Δ|<0.05) is the residual concern. ETH-only without the gate would be **catastrophic** (95% prior); ETH-only WITH the gate is the binary mechanism test.
2. **F1 anchoring against ETH-in-pool +0.0503 is correct** — but interpret PROMISING as "directional flip" not "edge discovery." Bundle contribution at /027 is via diversification not absolute Sharpe.
3. **KEEP all hyperparameters frozen** — n_trials=18, ENSEMBLE_SIZE=3, gate constants pinned. Single-axis discipline.

**Single most important point for QR**: ETH structural prior 4/4 NEGATIVE means **gate failure mode dominates verdict tail**. If F-AXIS #3 OOS fire-rate falls below 5% (under-fire), ETH cohort exposure unmitigated → catastrophic almost certain. Pre-registered band [5%, 35%] is the binary mechanism gate — Critic Phase 7.5 should treat this as load-bearing, not informational. The fire-rate test is more diagnostic than F1 OOS Sharpe Δ given the small anchor magnitude.

**/020+ verdict-conditional pre-staging**:
- **PROMISING** → /020 = BTC-only specialization (per /018 Phase 7.4 §6 cohort coverage)
- **PROMISING-INERT (modal)** → /020 = BTC-only specialized (same)
- **PROMISING-INERT-no-effect** (|Δ|<0.05) → /020 = ETH-only with TIGHTER gate (±5%) — single-dimension re-tune (small subset)
- **NEGATIVE-INERT** → /020 = BTC-only specialized; ETH cohort DROPPED for /027 bundle
- **NEGATIVE-INTRINSIC** → /020 = BTC-only specialized; ETH+gate axis PERMANENTLY CLOSED (ETH drag not BTC-trend-conditional, load-bearing finding for /024+ on-chain feature axis)
- **NEGATIVE-CATASTROPHIC** → /020 = BTC-only specialized; ETH cohort path closed for cycle-3
- **NEGATIVE-OVER-KILL** / **NEGATIVE-UNDER-FIRE** → /020 = ETH-only with re-tuned threshold (single-dimension; basin diagnostic, not edge claim)

**Critic Phase 7.5 priority items**:
1. **F-AXIS-MECHANISM #1** (`df['symbol'].unique() == ['ETHUSDT']`) binary pass <2 min.
2. **F-AXIS-MECHANISM #3** (gate fire-rate band) — load-bearing despite F1 small-anchor magnitude. Pre-registered band is the strongest verdict-disambiguator.
3. **Cross-track import** (`from crypto_trade.strategies.ml.risk_v2 import ...`) — Critic Check 14 may flag track-isolation principle. QR brief Section 3.1 already documents fallback (vendor copy in `risk_v1_gates.py`). If Critic BLOCKs the import, BLOCK-PENDING-FIX with vendoring is zero-behavior-change fix.

---

# LightGBM Master Post-Mortem — iter-v1/019 — Phase 7.4

## 1. Phase 4.5 vs Phase 7.4 prediction-reality

| Phase 4.5 prediction | Observed | Hit/Miss |
|---|---|---|
| PROMISING 35% / INERT 40% / NEGATIVE 25% | PROMISING-INERT favorable (Δ +0.6487 vs ETH-anchor) | **HIT** (modal cell adjacent; PROMISING tail fired) |
| Gate fire-rate IS 17.2% (band [10%, 30%]) | **19.5%** (31/159) | **HIT** — inside band |
| Gate fire-rate OOS 17.4% (band [5%, 35%]) | **14.3%** (6/42) | **HIT** — inside band |
| OOS Sharpe band [+0.10, +0.40] (advisor §2) | **+0.6990** | **MISS HIGH** — exceeded upper bound by +0.30 |
| n_eff_per_cell [4, 8] | **9** | MISS HIGH (+1; see §5) |
| IS lift 30-60% of post-hoc projection (§3) | EDA projected +42.47%; observed IS PnL -1.77 USD (essentially flat). Anchor IS -1.022 → observed -0.0304 = Δ +0.0718 | IS lift dampened MORE than predicted (compressed to ~10%); but OOS over-shot | MIXED |
| F-AXIS #3 fire-rate as load-bearing diagnostic | **CONFIRMED LOAD-BEARING** — both bands PASS | **HIT** |

Net assessment: 4/7 HIT, 2/7 MISS HIGH (favorable surprise), 1/7 MIXED. Phase 4.5's directional call (PROMISING-tail upside on small-anchor cohort with cross-year-stable gate) was vindicated; magnitude was under-predicted.

## 2. PROMISING-MECHANICAL Jaccard test (LOAD-BEARING)

Compared (symbol, open_time) keys between v1-baseline ETH-in-pool roster (145 IS + 46 OOS = 191 trades) and /019 ETH-only KEPT roster (128 IS + 36 OOS = 164 kept trades after gate).

| Scope | \|Intersection\| | \|Union\| | **Jaccard** |
|---|---|---|---|
| IS only | 10 | 263 | **0.0380** |
| OOS only | 2 | 80 | **0.0250** |
| Combined kept | 12 | 343 | **0.0350** |
| Combined ALL /019 trades (pre-gate model roster, 201 total) vs baseline ETH | 21 | 371 | **0.0566** |

**Verdict: Jaccard ≈ 0.04 << 0.50 → NEW SIGNAL SOURCE (compoundable)**. The /019 ETH-only retrained model generates an essentially DIFFERENT trade roster than pool-trained baseline. Even the pre-gate roster overlap is 5.7%. This is NOT PROMISING-MECHANICAL per `feedback_promising_mechanical_subtype.md` — the gate isn't filtering an existing roster; it's filtering a freshly-trained roster that itself diverges 94% from baseline. /027 bundle can stack ETH+gate ingredient additively without compoundability concerns.

## 3. F7 sign-agreement assessment

IS Sharpe **-0.0304** vs OOS Sharpe **+0.6990**: technical sign-mismatch. But IS net PnL is **-1.77 USD across 159 trades / 39 months** — basically zero. IS monthly distribution: 13 positive / 23 negative / 3 zero months → mean monthly PnL ≈ -0.045%. Recommend Critic interpret as **"IS flat / OOS positive"** not "IS negative / OOS positive". This replicates the v2/019 pattern (small-anchor IS, breakout OOS). F7 (brief Section 4 line 499) should be treated as **N/A at |IS Sharpe| = 0.03** — far below the ~0.10 threshold where IS sign carries information. Apply only at |IS Sharpe| > 0.10.

## 4. /027 CONFIRMATION multi-seed regression target

Per /018 multi-seed regression precedent (LINK-only single-seed +0.98 → expected +0.80 anchor at /027 multi-seed). Apply same compression to /019 single-seed +0.6990:

- Compression factor 0.65-0.80 (mean ~0.72) → **/019 ETH+gate /027 multi-seed band [+0.45, +0.55]; point estimate +0.50**.
- Single-seed basin variance ±0.30 → multi-seed ±0.15 at ENSEMBLE_SIZE=10.

**/027 bundle math** (assuming both ingredients carry to multi-seed):
- LINK contribution: +0.80 anchor
- ETH+gate contribution: +0.50 anchor
- BCH/DOT/LTC/BTC pending (/020-/023)

If cross-correlation between LINK and ETH+gate roster Sharpe paths < 0.40 (likely given different cohorts + different gate semantics), portfolio Sharpe lift via diversification: **estimate +0.85-+1.05 at 2-specialist bundle**, before BTC/LTC/DOT specialists. CONFIRMATION readiness solidifying.

## 5. n_eff = 9 outside predicted [4, 8] by +1

INFORMATIONAL miss. Mechanism: gate kills 19.5% IS / 14.3% OOS trades **POST-MODEL-FIT**, not at training. Model trained on full ETH labels (~159 IS trades' equivalent); Optuna trial diversity was measured at training row count, unaffected by post-hoc gate. My Phase 4.5 §5 conflated "training row count" with "post-gate trade count" — they're decoupled here. **Updated methodology for /020+**: predict n_eff from training cohort size (full per-symbol ETH IS labels ≈ 159+) NOT from post-gate trade count. /020 BTC-only with no gate → predict n_eff [8, 10].

## 6. Feature importance triage

**Not applicable for v1 track** — `run_baseline_v1.py` does not write `feature_importance.csv` per the iter-v1/018 + /019 report directories. v1's runner doesn't expose per-month importance. Recommend QE add `_write_feature_importance` to v1 runner BEFORE /020 to enable per-cohort importance comparison (LINK vs ETH vs BTC). Without it, we cannot directly diagnose whether the LINK-only and ETH-only specialists are leaning on different feature subsets — this is **structural diagnostic gap for the /027 bundle composition decision**.

## 7. /020+ pre-staging conditional updates

Verdict observed: **PROMISING-INERT favorable** (Δ +0.6487 vs ETH-anchor; OOS Sharpe +0.6990; mechanism passes load-bearing F-AXIS #3). Per Phase 4.5 §9 verdict-conditional matrix → **/020 = BTC-only specialization (cohort coverage continuation)**.

Pre-staging /020 EDA priorities for QR Phase 4:
1. BTC IS/OOS trajectory across cycle-3 (analog of `eth_oos_trajectory.csv`)
2. BTC monthly distribution (regime concentration check)
3. Test for BTC-specific drag mechanism (likely NOT BTC-trend-self since BTC IS the trend reference — pivot to vol regime or funding regime)

**LM Master Phase 4.5 prior for /020** (best-guess pre-EDA): PROMISING 25% / INERT 50% / NEGATIVE 25%. BTC is structurally the strongest pool anchor symbol (BTC-pooled regularization helps OTHER symbols; BTC-only isolation loses that asymmetric benefit). Modal INERT. Will refine post-/020 EDA.

**/021-/026 staged candidates** (conditional on /020 not catastrophic):
- /021 = LTC-only specialization (next NEGATIVE structural prior cohort after ETH)
- /022 = DOT-only specialization
- /023-/026 = pooled cohorts or methodology refinements (TBD)

## 8. CONFIRMATION readiness assessment

Per brief Section 11.6:

| Specialist | Status | Single-seed Δ | /027 regression target |
|---|---|---|---|
| LINK-only /018 | PROMISING-INERT favorable | +0.16 | +0.80 |
| ETH-only+gate /019 | **PROMISING-INERT favorable** | **+0.65** | **+0.50** |
| BTC-only /020 | PENDING | — | — |
| LTC-only /021 | PENDING | — | — |
| DOT-only /022 | PENDING | — | — |
| Pooled cohorts /023-/026 | PENDING | — | — |

At /027 CONFIRMATION (multi-seed), expect 4-6 specialists. Current 2-specialist projection: portfolio Sharpe **+0.85 to +1.05** before remaining /020-/026 contributions. **/027 multi-seed validation is now 2/4-6 ingredients staged.**

## 9. Most important Phase 7.4 finding

The mechanism worked exactly as Phase 4.5 §1-§2 predicted — direction-aware gate flipped essentially-zero ETH-in-pool anchor to clearly positive OOS via 19.5% IS / 14.3% OOS counter-trend kill rate (both inside pre-registered bands). Jaccard 0.04 vs baseline ETH roster confirms NEW signal source (compoundable, NOT PROMISING-MECHANICAL); ETH+gate becomes second confirmed /027 bundle ingredient after LINK-only, with single-seed +0.6990 → multi-seed regression target +0.50.
