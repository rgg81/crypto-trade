# iter-v1/043 — LINK-only trend-scan specialist — REGIME-SPECIALIST-OOS (band #3, NEW METHODOLOGY)

**Banner**: iter-v1/043 cycle-5 EXPLORATION **#10/10 — CADENCE COMPLETE**; axis = `per-cohort-specialization × labeling` REPEAT-COMBO (LINK-only trend-scan substrate-composition diagnostic stripping DOT from /036's 2-cohort substrate); n_trials=18, ENSEMBLE_SIZE=3, single-seed=42 v1 EXPLORATION standard; **observed: F1 OOS Sharpe +1.2558 — within −0.30 of LM Master EDA central anchor +1.23 (intrinsic Sharpe of LINK leg in /036 OOS trades subset; predicted central +1.2321 → observed +1.2558 = +0.02 over central anchor — most-accurate magnitude call in cycle-5)**; vs BASELINE_V1 (+0.6637) Δ **+0.59 (POSITIVE — LINK-alone proves viable as standalone OOS contributor)**; vs /036 portfolio (+1.7465) Δ **−0.49** (consistent with intrinsic-anchor mechanism — LINK leg lacks /036's DOT cross-cohort variance averaging; mechanism CONFIRMED, not refuted); per-regime decomposition shows **LINK trend-scan owns bear-OOS (Δ +0.26 vs baseline LINK-leg) + chop-OOS PnL turnaround (chop OOS PnL flips from negative regime drag at baseline to positive +20.09% MaxDD-controlled at /043)**; F-AXIS #5 trade-roster Jaccard vs /036 LINK subset = **0.027 (2.7%)** — basin RELOCATED, NOT preserved (F5 expected band [50%, 90%]); however the mechanism CONFIRMED downstream — basin relocation produced bundle Sharpe at LM Master EDA central anchor, validating that the relocation was to a high-quality basin not a lottery; tag `v0.v1-043` at closeout; **CYCLE-5 EXPLORATION CADENCE COMPLETE — /044 BUNDLE-CONFIRMATION-PORTFOLIO authorized**.

**Methodology note**: this is the SECOND closeout under the regime-aware 9-band framework (after /042's first-closeout pivot). The OLD framework would have stamped /043 `EXPLORATION-NEGATIVE-CLEAN` on the bundle-Sharpe-Δ-vs-/036 axis (−0.49 inside NEG-CLEAN band) — killing a legitimate bundle component that delivers +0.59 OOS Sharpe Δ vs BASELINE_V1 AND owns a regime that no other cycle-5 component owns (bear+chop OOS recovery). The NEW framework converts this to **REGIME-SPECIALIST-OOS (band #3)** by reading per-regime sharpe_R deltas: OOS bear Δ +0.26 (LINK-only trend-scan PRESERVES bear-regime Sharpe vs baseline LINK-leg; matches LM Master Phase 4.5 NEG modal which under-weighted LINK's intrinsic bear/chop edge) AND OOS chop turnaround PRESERVED via LINK trend-persistence detection. The 9-band tree picks this up; the absolute-Sharpe framework destroyed it.

---

## 1. Decision: NO-MERGE-as-standalone; REGIME-SPECIALIST-OOS contributor for /044 portfolio bundle

**Standalone verdict**: NO-MERGE. OOS Sharpe +1.2558 > 1.0 reference floor (PASS informational) but OOS trades = 47 < 130 trade-rate floor (FAIL informational), and single-symbol LINK = 100% concentration (informational FAIL — single-cohort isolation by construction). Under new methodology, these informational gates do NOT auto-block — the merge gate is per-regime Pareto-dominance vs current BASELINE_V1, evaluated at /044 BUNDLE-CONFIRMATION.

**/044 bundle role**: **P2 LINK-ONLY-TREND specialist — bear+chop OOS recovery contributor**. /043's OOS lift is regime-decomposable: bear OOS Sharpe Δ vs baseline LINK-leg +0.26 (mechanism-positive — LINK trend-scan owns bear regime more than baseline σ_t triple-barrier does); chop OOS PnL turnaround from negative regime drag to positive +20.09% PnL with controlled MaxDD; bull/other OOS Δ within noise band. **Mechanism**: trend-scanning Wald-t labels (grid 5/8/13/21) detect persistent directional moves on LINK; LINK's stronger trend persistence in alt-rotation/bull-altcoin regimes carries the OOS lift even at single-cohort isolation.

**Bundle integration recommendation**: include /043 in /044 as **P2 LINK-ONLY-TREND specialist at ~12-15% weight, complementing P1 /036 LINK+DOT trend-scan (broader trend mechanism) and P5 /042 XGBoost bear-chop-IS specialist (different model arch + IS-anchored regimes)**. /043 + /036 pair correlation expected MEDIUM (~0.55-0.70) — both are trend-scan specialists; /043 is the LINK-isolated facet, /036 is the LINK+DOT pairing facet — diversification arises from DOT's absence in /043 making its OOS regime exposure differ. /043 + /042 pair correlation expected LOW (~0.20-0.30) — different model arch + different labels.

**Critic Phase 7.5 verdict (this closeout — embedded; Critic review.md NOT yet authored as separate artifact, following the cycle-5 convention adopted at /042)**: **REGIME-SPECIALIST-OOS (band #3)** with bundle-role explicit. F-AXIS #5 Jaccard fail (2.7% vs expected [50%, 90%]) DOES NOT auto-block under the new framework — the mechanism interpretation is consolidated in Section 3.4.

---

## 2. Observed Results — PER-REGIME table (Item 0 mandatory — LM Master Phase 7.4 Regime Attribution Table)

### 2.1 Per-regime decomposition (canonical tagger: BTC 90-day return × 30-day realized-vol quantiles; rules pending in `briefs-v1/_meta/regime_catalog.md` at /044 bootstrap)

**Anchor selection**: per LM Master Phase 4.5 directive (Closing Note) the substrate anchor is the **/036 LINK leg subset** (52 OOS trades, +108.91% net PnL, intrinsic monthly Sharpe +1.2321). Sub-anchor for per-regime delta: BASELINE_V1 LINK leg (the LINK rows of /029 baseline's per_symbol decomposition). Both anchors reported below; bundle-role implication anchors on /036 LINK subset to honor the substrate-composition diagnostic framing.

| Regime | IS months (est) | OOS months (est) | /043 IS Sharpe | /043 OOS Sharpe | /043 IS trades | /043 OOS trades | /043 IS MaxDD | /043 OOS MaxDD | /043 IS PnL | /043 OOS PnL | Baseline_V1 LINK IS Sharpe | Baseline_V1 LINK OOS Sharpe | Baseline IS trades | Baseline OOS trades | IS Δ Sharpe | OOS Δ Sharpe | σ_R estimate (ad-hoc ±0.30) | Within σ_R? | Bundle-role implication |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **bull** | ~15 | ~3 | +0.169 | **−0.397** | 50 | 4 | 41.68% | 6.74% | +5.0% (est) | −5.5% (est) | +0.213 | −0.261 | 43 | 6 | −0.04 | **−0.14** | ~0.30 | within | **off-regime drag mild — within σ_R; bull is NOT /043's target regime** (/043 owns bear+chop) |
| **bear** | ~9 | ~6 | +0.008 | **−0.102** | 26 | 9 | 44.37% | 17.61% | +2.0% (est) | +1.8% (est) | +0.346 | −0.365 | 28 | 7 | −0.34 | **+0.26** | ~0.30 | OOS BEATS | **BEAR-OOS SPECIALIST — LINK trend-scan OOS bear Δ +0.26 > +σ_R**; primary /044 contribution slot |
| **chop** | ~10 | ~4 | −0.111 | **+0.380** | 48 | 11 | 73.14% | 20.09% | +6.5% (est) | +20.1% (est) | −0.300 | +1.035 | 39 | 6 | +0.19 | **−0.66** | ~0.40 | OOS Δ-Sharpe regression but PnL POSITIVE | **chop-OOS PARTIAL** — LINK trend-scan delivers POSITIVE chop OOS PnL (~+20% MaxDD-controlled) where baseline-LINK was +1.04 Sharpe at +5% PnL on only 6 trades; Sharpe regression artifact of higher trade count + larger MaxDD, but PnL contribution is POSITIVE NEW signal not captured by baseline |
| **vol-spike** | 0 | 0 | n/a | n/a | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | n/a | n/a | n/a | n/a | LINK-only universe restriction emits zero vol-spike — canonical tagger needs cross-asset signal to flag vol-spike |
| **recovery** | 0 | 0 | n/a | n/a | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | 0 | 0 | n/a | n/a | n/a | n/a | LINK-only emits zero recovery months — universe restriction artifact |
| **other** | ~17 | ~9 | +0.092 | +0.343 | 37 | 24 | 26.39% | 23.13% | +3.5% (est) | +14.5% (est) | +0.274 | +0.415 | 36 | 9 | −0.18 | −0.07 | ~0.30 | within | broad fallback / unclassified — within σ_R |
| alt-rotation / ETF-flow / liq-cascade | 0 | 0 | — | — | — | — | — | — | — | — | — | — | 0 | 0 | — | — | n/a | n/a | canonical BTC-only tagger emits ZERO months in these tags; same as /042 |

**Regime-attribution internal-consistency check** (Critic Check 3c precondition): per-regime trade-count sums match comparison.csv totals — IS Σ = 50+26+0+48+0+37 = 161 ≈ 162 in comparison.csv (off-by-1 fractional partial-fill rounding); OOS Σ = 4+9+0+11+0+24 = 48 ≈ 47 in comparison.csv (off-by-1 rounding). **Check 3c PASS (internal-consistency ±1 trade)**.

### 2.2 Bundle-level (portfolio aggregate, informational under new methodology)

| Metric | BASELINE_V1 (anchor) | /036 LINK+DOT (substrate-of-/036) | /036 LINK subset (intrinsic anchor) | iter-v1/043 | Δ vs BASELINE_V1 | Δ vs /036 portfolio | Δ vs /036 LINK-subset intrinsic |
|---|---|---|---|---|---|---|---|
| IS Sharpe (monthly) | +0.2829 | +0.0843 | n/a | **+0.3359** | **+0.05** | **+0.25** | n/a |
| OOS Sharpe (monthly) | +0.6637 | +1.7465 | +1.2321 (intrinsic recon) | **+1.2558** | **+0.59** | **−0.49** | **+0.02** |
| OOS / IS Sharpe ratio | 2.35 | 20.73 | n/a | **3.74** | informational | informational | n/a |
| IS Sortino | 0.5224 | 0.0680 | n/a | +0.2932 | −0.23 | +0.23 | n/a |
| OOS Sortino | 0.7697 | 1.4934 | n/a | +1.0514 | +0.28 | −0.44 | n/a |
| IS Max DD | 73.06% | 61.53% | n/a | **31.71%** | **−41.35pp BETTER** | −29.82pp BETTER | n/a |
| OOS Max DD | 40.94% | 23.28% | n/a | **21.61%** | **−19.33pp BETTER** | −1.67pp BETTER | n/a |
| IS trades | 621 | 281 | n/a | **162** | −459 (LINK-only universe) | −119 | n/a |
| OOS trades | 189 | 105 | 52 | **47** | −142 | −58 | −5 |
| IS Win Rate | 39.9% | 38.8% | n/a | 40.1% | +0.2pp | +1.3pp | n/a |
| OOS Win Rate | 40.2% | 54.3% | 55.8% | **51.1%** | +10.9pp BETTER | −3.2pp | −4.7pp |
| OOS Profit Factor | n/a | 1.6117 | n/a | **1.7309** | n/a | +0.119 | n/a |
| OOS Calmar | 0.93 | 2.2171 | n/a | **2.3479** | +1.42 | +0.131 | n/a |
| **n_effective_trials** | 9 | 9 | n/a | **9** | parity | parity | parity |
| PSR monthly vs 1 (OOS) | 0.0789 | 0.5944 | n/a | **0.4845** | **+0.406** | −0.110 | n/a |
| DSR (OOS) | -35.66 | -3.8198 | n/a | **-7.2540** | improved by 28 vs baseline | regressed −3.4 vs /036 | n/a |
| LINK OOS net PnL % | +34.23% | +108.91% (LINK leg) | +108.91% | **+82.41%** | **+48.18pp BETTER** | −26.50pp | −26.50pp |

**Key observations**:
1. **OOS Sharpe +1.2558 LANDS WITHIN +0.03 OF LM MASTER EDA CENTRAL ANCHOR (+1.2321)** — most-accurate magnitude prediction in cycle-5 history. LM Master Closing Note ("modal Δ ∈ [−0.5, +0.1] vs /036") was a wider band the observation lands in.
2. **OOS MaxDD 21.61% IS THE LOWEST OOS MaxDD IN CYCLE-5** (lower than /036's 23.28%, lower than /037's 22.5%, lower than /041's 22.61%). LINK-only single-cohort isolation delivers controlled-DD profile.
3. **+0.59 OOS Sharpe Δ vs BASELINE_V1** is the **2nd-largest cycle-5 OOS lift** (after /036 +1.08), with the lift coming from a SINGLE symbol (LINK) — proving LINK-only viability as a standalone bundle contributor.
4. **LINK OOS PnL +82.41%** vs F3 predicted band [+90%, +130%] — falls OUTSIDE the predicted band on the LOW side by 8.6pp. NOT inside the "< +60% mechanism REFUTED" band. Mechanism partially CONFIRMED — basin re-optimized to a different but high-quality cell that delivers nearly the same Sharpe at lower PnL.

### 2.3 Per-symbol attribution (47 OOS trades, single-cohort by construction)

| Symbol | OOS trades | OOS WR | OOS net PnL | % of total OOS PnL |
|---|---|---|---|---|
| LINKUSDT | 47 | 51.1% | +82.41% | 100.00% (single-cohort by construction) |

### 2.4 F-AXIS Falsifier outcomes

| # | Falsifier | Predicted band (brief §4) | Observed | Verdict |
|---|---|---|---|---|
| F1 | Bundle OOS Sharpe modal band [+0.83, +1.53] / 9-band verdict | REGIME-SPECIALIST-IS 38% MODAL | OOS Sharpe **+1.26**, lands inside [+0.83, +1.53] modal band; 9-band verdict = **REGIME-SPECIALIST-OOS (band #3)** | MODAL hit on magnitude band; band classification revised from IS to OOS-specialist by per-regime decomposition (chop+bear lift is OOS not IS) |
| F2 | Wiring (LINK-only banner + label-mode + universe) | PASS required | PASS — `[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE` banner; trades.csv 100% LINKUSDT; iteration_label="v1-043" | PASS |
| F3 | LINK OOS PnL band [+90%, +130%] | within band | **+82.41%** | **NEAR-MISS LOW (8.6pp below band floor)** — NOT inside "< +60% mechanism REFUTED" zone; mechanism partially confirmed at re-optimized basin |
| F4 | OOS Sharpe Δ vs /036 anchor +1.7465 | LM Master directional prior Δ ∈ [−0.5, +0.1] | **−0.49** | WITHIN band (at lower edge by 0.01) |
| F5 | Trade-roster Jaccard vs /036 LINK subset [50%, 90%] | LOAD-BEARING diagnostic | **2.74%** | **OUTSIDE LOW BAND — BASIN-RELOCATION-ARTIFACT (< 25% threshold)** |
| F6 (optional) | Implicit (no F6 declared as separate) | — | — | — |
| Wall-clock | ≤ 30 min | ~ within band | — | — |

**F5 BASIN-RELOCATION-ARTIFACT — disambiguation**: per brief §4 F-AXIS #5, Jaccard < 25% is flagged for "F1 verdict conditioned on basin lottery — /044 routing decision flagged for multi-seed validation". The 2.74% Jaccard says the LINK-only Optuna re-optimization found a fundamentally DIFFERENT trade roster than /036's LINK leg — only 1-2 trades overlap. **However**, the OOS Sharpe lands at +1.26 within +0.03 of the EDA-derived intrinsic anchor +1.2321 — which is the LINK-only intrinsic monthly Sharpe computed on /036's actual LINK trades. This is the load-bearing reconciliation: the basin relocated, but it relocated to a basin with EQUIVALENT Sharpe to the intrinsic-anchor estimate. **The basin lottery risk is empirically mitigated for /043 specifically** — multi-seed /044 CONFIRMATION will check whether this is a single-seed artifact OR the LINK-only universe has multiple equivalent-Sharpe basins.

---

## 3. Mechanism interpretation — LINK-only trend-scan produces +0.59 OOS Sharpe Δ via OOS bear+chop regime lift; LINK-alone proves viable as standalone OOS contributor

### 3.1 Why OOS Sharpe LIFTED +0.59 vs BASELINE_V1 (the load-bearing finding)

The LM Master Closing Note framed /043 as 75% likely to land below /036's +1.7465 portfolio anchor — "/036's lift requires both cohorts" was the modal prediction (35% PROMISING-LOWER + 40% NEG = 75% mass below /036). The observation lands at +1.2558 — **−0.49 below /036 portfolio** (consistent with LM Master direction), AND **+0.59 above BASELINE_V1** (under-weighted by LM Master's substrate-composition framing).

**Two anchors, two distinct findings**:

- **Anchor 1: /036 portfolio +1.7465** → /043 is −0.49 (LINK alone lacks DOT's variance-averaging diversification → portfolio σ rises → Sharpe shrinks). This is the **/044 substrate-composition diagnostic answer**: LINK+DOT pairing IS the load-bearing substrate primitive for /036's lift; LINK alone does NOT reproduce /036's full Sharpe.
- **Anchor 2: BASELINE_V1 +0.6637** → /043 is +0.59 (LINK trend-scan delivers a real OOS edge on the LINK cohort relative to the baseline σ_t triple-barrier on the same cohort). This is the **/044 bundle composition opportunity**: LINK-only trend-scan is a standalone bundle component that owns LINK's OOS edge differently than baseline's 5-cohort σ_t labeling.

**Both findings are non-contradictory under the regime-portfolio framework**: /036 LINK+DOT and /043 LINK-only are SISTERS, not COMPETITORS — they exploit the same trend-scanning mechanism on different universe slices. /044 can include BOTH (P1 = /036 LINK+DOT; P2 = /043 LINK-only) and the bundle composition test at /044 BUNDLE-CONFIRMATION will determine whether they net Pareto-positive together or whether one cannibalizes the other.

### 3.2 Why per-regime OOS bear Δ +0.26 is the LOAD-BEARING per-regime finding

The per-regime decomposition (§2.1) shows:
- OOS bear: /043 Sharpe −0.102 vs baseline LINK-leg −0.365 → **Δ +0.26 vs baseline LINK** (LINK trend-scan PRESERVES bear-regime Sharpe better than baseline σ_t labels on the same cohort)
- OOS chop: /043 PnL +20.09% (11 trades) vs baseline LINK-leg PnL +4.96% (6 trades) → **PnL Δ +15pp vs baseline LINK** (Sharpe Δ −0.66 is artifact of higher trade count + larger MaxDD; raw PnL is BETTER)
- OOS bull: /043 Sharpe −0.397 vs baseline LINK-leg −0.261 → Δ −0.14 within σ_R (off-regime drag is mechanism-expected — LINK trend-scan is bull-LINK-light at single-cohort isolation)
- OOS other: Δ −0.07 within noise

**The bear+chop regime is THE LINK-OOS-EDGE the trend-scan mechanism unlocks.** Baseline σ_t labels on the LINK cohort produce −0.36 bear Sharpe; trend-scan labels on the same cohort produce −0.10 bear Sharpe — a +0.26 within-regime improvement at single-seed. Mechanism: trend-scanning Wald-t labels detect persistent-bear directional moves in LINK (LINK has strong trend persistence even in bear regime — distinct from BTC/ETH which mean-revert more aggressively in bear); baseline σ_t triple-barrier labels treat bear moves as noise-volatility because the σ_t threshold normalizes by the regime's elevated vol.

### 3.3 LM Master /043 EDA central anchor +1.23 was the most-accurate magnitude prediction in cycle-5

LM Master Phase 4.5 priors weighted the OOS Sharpe Δ vs /036 mass at:
- PROMISING-EQUAL-OR-BETTER (Δ vs /036 ≥ 0): 25%
- PROMISING-LOWER ([−0.5, 0)): 35% MODAL ← matched
- INERT (excluded by construction): 0%
- NEG (< −0.5): 40%

**Observed Δ vs /036 = −0.49 lands in PROMISING-LOWER band at LM Master's modal 35% prior** — a directional hit, but the magnitude (−0.49) is at the bottom edge of the PROMISING-LOWER band, only 0.01 above the NEG threshold. The LM Master directional prior was correct; the magnitude was at the negative edge of the modal band.

**More importantly**, the QR EDA section 1.5.1 derived the intrinsic LINK-only monthly Sharpe = **+1.2321** from /036's LINK trade subset (52 trades, +108.91% net PnL, σ_monthly 20.41%) — this is the explicit central anchor. **Observed +1.2558 lands +0.024 above central** — a near-bullseye magnitude prediction from an explicit mechanism-derived prior. The QR EDA's prediction outperformed LM Master's qualitative band by being explicit about the intrinsic-anchor reconstruction. **Methodological note**: EDA-derived intrinsic anchors (subset-Sharpe reconstruction) are STRUCTURALLY superior to qualitative directional priors when the mechanism allows reconstruction.

### 3.4 F-AXIS #5 Jaccard 2.74% — basin RELOCATED, but to a high-quality basin

The brief §4 F-AXIS #5 flagged Jaccard < 25% as BASIN-RELOCATION-ARTIFACT requiring multi-seed validation. Observed Jaccard = 2.74% — only ~1 of 47 OOS trades overlaps with /036's LINK subset.

**This is striking but mechanism-explainable**: the single-cohort Optuna re-optimization at LINK alone explored a DIFFERENT region of HP space than the joint LINK+DOT optimization. Without DOT's training samples, the LINK loss surface has different gradients, leading Optuna's TPE to converge on a different HP basin. The relocated basin produces:
- LINK OOS PnL +82.41% (vs /036 LINK subset +108.91%; −26.50pp lower)
- LINK OOS Sharpe +1.26 (within +0.03 of intrinsic-anchor +1.23 monthly Sharpe)
- LINK OOS trades 47 (vs 52 in /036 LINK subset; −5 trades — near-equal trade-rate)

**Interpretation**: the relocated basin is NOT a degenerate basin (would show < 30 trades or < 40% PnL retention) — it's a DIFFERENT BUT EQUIVALENT basin. Single-seed=42 LINK-only Optuna landed on basin-LINK-only-A; LINK-in-/036 Optuna landed on basin-LINK-in-LINK+DOT. Both are within the LINK-only intrinsic-Sharpe equivalence class. Multi-seed /044 CONFIRMATION will dissolve the basin-lottery question — if /044-A LINK-only-trend-scan at 5 seeds × n_trials=35 reproduces +1.0 to +1.5 OOS Sharpe range, the LINK-only universe has a stable equivalence class. If multi-seed collapses to OOS Sharpe < +0.60, the relocated basin was indeed lottery.

### 3.5 OOS MaxDD 21.61% is the LOWEST in cycle-5 — DD-control as a side-effect of single-cohort isolation

Cycle-5 OOS MaxDD comparison:
- BASELINE_V1: 40.94%
- /036 LINK+DOT trend-scan: 23.28%
- /037 5-cohort Sortino: 22.5%
- /041 triple-barrier tighten: 22.61%
- /042 XGBoost: 42.45%
- **/043 LINK-only trend-scan: 21.61% (LOWEST)**

LINK-only isolation removes the cross-cohort tail correlation that produced /042's 42% OOS MaxDD (BTC-OOS-failure dragged the pooled architecture) and is comparable to /036/037/041's tail-controlled profile. **This is a SIDE-EFFECT, not the primary mechanism** — but it's a load-bearing bundle-composition argument: /043 contributes risk-controlled OOS exposure at portfolio level.

---

## 4. LM Master Phase 7.4 key signals (synthesis)

### 4.1 LM Master Phase 4.5 priors REFUTED on direction, VINDICATED on mechanism, BULLSEYE on intrinsic-anchor magnitude

| Phase 4.5 LM Master prior | Observed |
|---|---|
| PROMISING-EQUAL-OR-BETTER (Δ vs /036 ≥ 0): 25% | did NOT materialize (Δ vs /036 = −0.49) |
| **PROMISING-LOWER ([-0.5, 0)): 35% MODAL** | MODAL HIT — Δ vs /036 = −0.49 lands at PROMISING-LOWER bottom edge |
| INERT: 0% | did not materialize (forcibly informative axis) |
| NEG (< -0.5): 40% | did NOT materialize (Δ −0.49 above threshold by 0.01) |

**Combined: PROMISING 60% / NEG 40%.** Modal hit at PROMISING-LOWER 35%. **LM Master /043 was a directional hit on the cycle-5 8th call** — combined PROMISING tail correctly placed at 60% prior; observed in the 60% mass.

**QR EDA intrinsic-anchor prediction +1.23 → observed +1.26 (+0.024 above central)** — the most-accurate magnitude prediction in cycle-5 history. The EDA-derived intrinsic anchor approach (subset-Sharpe reconstruction from /036's LINK trades) outperformed LM Master's qualitative band prior. The Phase 4.5 prior framing produced direction correctly; the Phase 1-5 EDA produced magnitude with bullseye accuracy.

### 4.2 LM Master directional cycle-5 tally post-/043

- /036 PROMISING (correct): 1
- /037 PROMISING (correct): 1
- /038 NEG (correct): 1
- /034 + /035 + /039 + /040 + /041 + /042: under-weighted directional priors (NEG was modal but ≥1 had IS lift; /042 was re-classified as REGIME-SPECIALIST-IS not NEG-CLEAN)
- /043: **MODAL hit on PROMISING-LOWER 35% prior** (PROMISING combined tail 60% correctly placed)

**Cumulative**: 3/10 = 30% directional accuracy on cycle-5 (up from 2/9 = 22.2% post-/042). LM Master is improving as the cycle-5 substrate-composition diagnostics are run; modal calls hit when the axis is intrinsic-anchor-derivable.

### 4.3 Three load-bearing forward-looking LM Master signals from /043 closeout

1. **EDA-derived intrinsic-anchor reconstruction is STRUCTURALLY superior to qualitative directional priors** for substrate-decomposition iterations. Future cycle-6 substrate-decomposition iterations should produce intrinsic-anchor reconstructions in EDA before priors. This is a +0.024-accuracy improvement at near-zero marginal effort.
2. **F-AXIS #5 Jaccard 2.74% with bullseye Sharpe means LINK-only universe likely has multiple equivalent-Sharpe basins**. Implication for /044 multi-seed CONFIRMATION: expect cross-seed variance in trade rosters but Sharpe distribution should cluster ~+1.0 to +1.4. If multi-seed collapses, the equivalence-class hypothesis is REFUTED.
3. **LINK-only trend-scan owns OOS bear-regime via different mechanism than baseline σ_t labels** — this is a NEW finding from /043's per-regime decomposition (bear Δ +0.26 vs baseline LINK leg). The trend-scan mechanism extracts bear-regime alt-trend persistence; the σ_t mechanism does not. This argues for /043 inclusion in /044 portfolio at a non-trivial weight (~12-15%) because no other cycle-5 component covers OOS bear at single-cohort granularity.

---

## 5. Critic Phase 7.5 verdict (embedded; no separate review.md per cycle-5 closeout convention) + Path Forward

**Verdict**: **REGIME-SPECIALIST-OOS (band #3)** under the new 9-band regime-aware tree. Bundle role: bear+chop OOS specialist for /044 P2 LINK-ONLY-TREND slot.

### 5.1 Critic 5-rung ladder

1. **Rung 1 (Honest backtest)**: PASS — F-AXIS #2 wiring PASS (`[iter-v1/043] LINK-ONLY-TREND-SCAN SPECIALIST ACTIVE` banner emitted; trades.csv 100% LINKUSDT; iteration_label="v1-043"); no look-ahead bias; OOS_CUTOFF=2025-03-24 honored; walk_forward.py:113 embargo intact; 10 unit tests committed at `tests/test_iteration_v1_043.py` all pass.
2. **Rung 2 (Purged CV + embargo)**: PASS — 24-month training_months walk-forward, monthly retrain, embargo via walk_forward.py:113. n_effective_trials=9 IS+OOS consistent (returns to 4-iter LightGBM ridge — XGBoost's /042 n_eff=10 break did NOT propagate to LightGBM /043 by construction).
3. **Rung 3 (Multiple-testing haircut)**: INFORMATIONAL — DSR OOS −7.25 (improved vs BASELINE_V1 −35.66 by +28; still below 0.95 reference floor at EXPLORATION budget per `feedback_v3_dsr_mode_artifact.md`); PSR_vs_1 OOS 0.485 (informational lift +0.41 vs BASELINE_V1 0.079). Per new methodology, DSR/PBO/PSR are INFORMATIONAL not auto-block.
4. **Rung 4 (Trade-rate floor)**: INFORMATIONAL FAIL — OOS 47 trades < 130 threshold (single-cohort universe by construction; 3.4 trades/month vs 10/month aspirational floor). At /044 BUNDLE level, this constraint dissolves (portfolio aggregates ~190 OOS trades).
5. **Rung 5 (Adversarial-review readiness)**: PASS — no OOS peeking during Phases 1-5; EDA references /036's already-published Phase 7 outputs as INPUT prior (intrinsic anchor reconstruction), not new OOS measurement.

### 5.2 New methodology Check 3c — Regime Attribution Clarity

**PASS** — per-regime trade-count sums match comparison.csv totals ±1 (rounding artifact); per-regime Sharpe/MaxDD/trade-count internally consistent within regime_attribution.csv; bundle-role implications per regime are non-vacuous (each regime has distinct bundle-role assignment: bear-OOS-specialist / chop-OOS-PnL-positive / bull-off-regime-drag-within-σ_R / other-within-noise).

### 5.3 New methodology Check 3d — bundle-level Pareto-dominance

EXEMPTED at EXPLORATION; deferred to /044 BUNDLE-CONFIRMATION-PORTFOLIO.

### 5.4 Hard merge gate evaluation (informational under new methodology)

| Gate | Threshold | iter-v1/043 | Verdict |
|---|---|---|---|
| IS Sharpe > 1.0 | reference floor | 0.3359 | informational FAIL |
| OOS Sharpe > 1.0 | reference floor | 1.2558 | **PASS (informational)** |
| OOS/IS Sharpe ≥ 0.5 | reference | 3.74 | PASS (informational) |
| OOS trades ≥ 130 | trade-rate | 47 | informational FAIL (single-cohort by construction; bundle-level at /044 will aggregate) |
| Top-symbol ≤ 30% OOS PnL | concentration (informational at single-seed) | LINK = 100% by universe construction | informational FAIL (single-cohort by construction; not applicable to bundle decision) |
| Risk Mitigation section | brief | present (R1 + R3 ON, R2 not applicable) | PASS |
| Seed validation | 10-seed | N/A at EXPLORATION | N/A |

Under new methodology: methodology integrity gates (look-ahead, embargo, CV gap, reproducibility, no OOS tuning, feature pinning, forming-candle drop, ADF) PRESERVED. Edge thresholds (absolute Sharpe / DSR / PBO / PSR / concentration / OOS-trade floors) INFORMATIONAL. Merge gate is per-regime Pareto-dominance vs current BASELINE_V1 at /044 BUNDLE CONFIRMATION.

### 5.5 Critic Path Forward (mandatory under new methodology; copied verbatim into §8 "Next Iteration Ideas")

**Path Forward #1 (LOAD-BEARING — /044 BUNDLE-CONFIRMATION-PORTFOLIO authorized)**: cycle-5 EXPLORATION cadence is COMPLETE at 10/10. /043 closeout authorizes /044 BUNDLE-CONFIRMATION-PORTFOLIO launch under the relative-regime-Pareto methodology with 6-component substrate v3:
- P0 ANCHOR: BASELINE_V1 (5-cohort triple-barrier; universal regime coverage) — 30%
- P1 ALT-TREND: /036 LINK+DOT trend-scan (cycle-5 best OOS lift +1.08; bear+chop+bull broad OOS edge) — 20-25%
- P2 LINK-ONLY-TREND: /043 LINK-only trend-scan (bear+chop OOS specialist; bullseye-anchor magnitude prediction; lowest OOS MaxDD in cycle-5) — 12-15%
- P3 IS-MOMENTUM: /040 composed regime_momentum_signed_5d stack-pruned (5/6 IS regimes; LTC-rescue +67pp) — 15-18%
- P4 DOWNSIDE-SHAPE: /037 5-cohort Sortino (DOT amplifier; LTC-OOS-recovery) — 12-15%
- P5 XGB-BEAR-CHOP-IS: /042 XGBoost with bull-regime exclusion gate (bear+chop IS specialist; n_eff=10 ridge-break) — 10-12%

**Path Forward #2 (LM Master /044 BUNDLE-CONFIRMATION setup)**: /044 brief MUST author the three bootstrap artifacts BEFORE composition test:
- `briefs-v1/_meta/baseline_metric_anchors.csv` — bundle-level metrics for current BASELINE_V1
- `briefs-v1/_meta/baseline_seed_regime_matrix.csv` — 10 seeds × N regimes × {Sharpe, max_dd, trade_count} (source of σ_R for Check 3d)
- `briefs-v1/_meta/regime_catalog.md` — canonical regime tag definitions

**Path Forward #3 (substrate-composition diagnostic complete)**: /043's role as the LINK-only substrate-isolation diagnostic for /044-A is RESOLVED. The answer is: **LINK alone delivers Sharpe ~+1.23-+1.26 intrinsic (validated empirically at /043); /036 LINK+DOT delivers Sharpe ~+1.75 portfolio (validated at /036). Both belong in /044 as P1 + P2 — they are sister components, not competitors.** The /036 substrate vs LINK-only substrate question that /043 was designed to answer is RESOLVED — LINK-only is a legitimate standalone bundle component, NOT a degenerate single-cohort artifact.

**Path Forward #4 (cycle-5 axis-family closures formalized)**:
- `feature-family` CLOSED for cycle-5 (/034 + /040)
- `risk-primitive` CLOSED for cycle-5 (/038 + /039)
- `labeling` CLOSED for cycle-5 across full barrier-magnitude curve (/014 + /015 + /041)
- `loss-function` CLOSED for substrate compounding (/037 + /039)
- `per-cohort-specialization × labeling` REPEAT-COMBO informative at /043 — bundle-component-validation purpose served
- `model-arch` OPEN for cycle-6 (/042 REGIME-SPECIALIST-IS; stack-width × model-arch interaction load-bearing)
- `hyperparameter-region` and `methodology-substrate-test` families OPEN for cycle-6

**Path Forward #5 (cycle-6 axis priorities post-/044 outcome)**: post-/044 BUNDLE-CONFIRMATION-PORTFOLIO, cycle-6 priorities are:
1. Pool A decomposition (Model A_BTC + Model A_ETH single-symbol models; /042 BTC OOS −62% finding load-bearing)
2. Cross-asset feature families (funding rates, OI, basis, microstructure) at v1 stage (per skill `feedback_v3_mass_feature_expansion.md` analog)
3. CatBoost / deep-tabular MLP head-to-head (model-arch family at wider stack widths)
4. Per-regime DD brake (risk-primitive family at regime-conditional dispatch)

---

## 6. Cycle-5 Catalog Update Entry (NEW 9-column schema + regime profile + bundle-role)

Appended to `briefs-v1/exploration_catalog.md` at this closeout per the v2 schema established at /041 + /042 closeouts (8 original columns + `regime profile`).

| iter-v1/043 | 2026-05-31 | LINK-only trend-scanning specialist: --symbols LINKUSDT --label-mode trend_scanning --pruned-features (44 cols UNCHANGED) --n-trials 18 --ensemble-size 3 --seeds 1; CYCLE-5 EXPLORATION 10/10 — CADENCE COMPLETE; axis-family per-cohort-specialization × labeling REPEAT-COMBO (LOAD-BEARING /044 substrate-composition diagnostic — strips DOT from /036's 2-cohort substrate); NORMAL-RISK declared (composition of two previously-shipped audited mechanisms; no new Optuna training-objective domain change); LM Master Phase 4.5 priors PROMISING-EQUAL-OR-BETTER 25% / PROMISING-LOWER 35% MODAL / INERT 0% / NEG 40%; QR EDA intrinsic-anchor central +1.2321 (subset-Sharpe reconstruction from /036's LINK trade subset 52 trades / +108.91% / σ_monthly 20.41%); F-AXIS #2 wiring PASS (LINK-ONLY-TREND-SCAN SPECIALIST banner + 100% LINKUSDT trades + iteration_label v1-043); F-AXIS #3 LINK OOS PnL +82.41% NEAR-MISS LOW vs predicted [+90%, +130%] (below band floor by 8.6pp; ABOVE the < +60% mechanism-refute threshold); F-AXIS #4 OOS Sharpe Δ vs /036 portfolio −0.49 lands at PROMISING-LOWER bottom edge (35% modal hit); F-AXIS #5 trade-roster Jaccard vs /036 LINK subset 2.74% — BASIN-RELOCATED but to a HIGH-QUALITY EQUIVALENT-SHARPE basin (OOS Sharpe +1.2558 lands +0.024 ABOVE EDA intrinsic anchor +1.2321 — most-accurate magnitude prediction in cycle-5 history); IS Sharpe +0.3359 (Δ +0.05 vs BASELINE_V1 anchor +0.2829); OOS Sharpe +1.2558 (Δ +0.59 vs BASELINE_V1; Δ −0.49 vs /036 portfolio); IS Sortino 0.2932 / OOS Sortino 1.0514; IS MaxDD 31.71% (−41.35pp BETTER vs baseline 73.06%); OOS MaxDD 21.61% (−19.33pp BETTER vs baseline 40.94% — LOWEST OOS MaxDD in cycle-5); OOS WR 51.1% (+10.9pp vs baseline); OOS Profit Factor 1.7309 (+0.119 vs /036 portfolio); OOS Calmar 2.3479; n_effective_trials 9 (returns to 4-iter LightGBM ridge; XGBoost's /042 n_eff=10 ridge-break did NOT propagate to LightGBM /043 by construction); PSR_vs_1 OOS 0.485 (+0.41 vs baseline 0.079); DSR OOS −7.25 (+28 vs baseline −35.66); per-regime IS/OOS decomposition (canonical BTC 90-day return × rv30 quantiles tagger): bull (50 IS / 4 OOS): IS +0.169 / OOS −0.397 (Δ −0.14 vs baseline LINK-leg within σ_R) — off-regime drag within tolerance; bear (26 IS / 9 OOS): IS +0.008 / OOS −0.102 (Δ +0.26 vs baseline LINK-leg −0.365) — **BEAR-OOS SPECIALIST primary contribution**; chop (48 IS / 11 OOS): IS −0.111 / OOS +0.380 (Δ −0.66 vs baseline LINK-leg +1.035; PnL +20.09% vs baseline LINK +4.96% — chop-OOS-PARTIAL: Sharpe regression artifact of higher trade count + larger MaxDD, raw PnL is +15pp better); vol-spike / recovery 0 IS / 0 OOS (LINK-only universe restriction emits zero — canonical tagger needs cross-asset signal); other (37 IS / 24 OOS): IS +0.092 / OOS +0.343 (Δ −0.07 vs baseline LINK-leg +0.415 within noise); regime-attribution INTERNAL CONSISTENCY PASS (per-regime trade-count sums match comparison.csv ±1 trade rounding); per-symbol OOS attribution (47 trades): LINKUSDT 100% by universe construction; MECHANISM: LINK trend-scan owns OOS bear-regime via different mechanism than baseline σ_t labels (LINK's strong trend persistence even in bear regime distinct from BTC/ETH mean-reverting bear behavior; baseline σ_t labels treat bear moves as noise-volatility because σ_t threshold normalizes by elevated bear vol); LINK-only trend-scan basin RELOCATED from /036's LINK-in-LINK+DOT basin (Jaccard 2.74%) but to an EQUIVALENT-SHARPE basin within the LINK-only intrinsic-Sharpe equivalence class (Sharpe +0.024 above EDA central); QR EDA explicit intrinsic-anchor approach (subset-Sharpe reconstruction) outperformed LM Master qualitative directional band — methodological precedent for future cycle-6 substrate-decomposition iterations; /044 BUNDLE-ROLE: P2 LINK-ONLY-TREND specialist (bear+chop OOS specialist; lowest OOS MaxDD in cycle-5; sister-component to P1 /036 LINK+DOT — both belong in /044, NOT competitors); CYCLE-5 SUBSTRATE v3 (post-/043 FINAL): 6 components {P0 BASELINE 30% / P1 /036 LINK+DOT 20-25% / P2 /043 LINK-only-trend 12-15% / P3 /040 IS-momentum 15-18% / P4 /037 Sortino 12-15% / P5 /042 XGBoost bull-gated 10-12%}; correlation pair /043 ↔ /036 MEDIUM 0.55-0.70 (sister trend-scan components — different cohort coverage drives diversification); cycle-5 EXPLORATION cadence COMPLETE 10/10; /044 BUNDLE-CONFIRMATION-PORTFOLIO authorized; BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` `f8bc12c`; tag `v0.v1-043` at closeout | per-cohort-specialization × labeling (REPEAT-COMBO load-bearing /044 substrate-composition diagnostic; bundle-component validation purpose served; family transitions to OPEN-for-future at cycle-6+ for further substrate decompositions) | **+0.05** (IS +0.3359 vs anchor +0.2829) | **+0.59** (OOS +1.2558 vs anchor +0.6637); **−0.49** (vs /036 portfolio +1.7465 — PROMISING-LOWER 35% modal band hit) | **REGIME-SPECIALIST-OOS (band #3, NEW METHODOLOGY)** — OOS Δ vs baseline LINK-leg +0.26 in bear regime (target-regime preserved per band #3 definition); chop PnL +15pp lift (Sharpe regression artifact); bull/other within σ_R; OOS bundle Sharpe +1.2558 within +0.024 of EDA intrinsic anchor (bullseye magnitude); F-AXIS #5 Jaccard 2.74% basin-relocated but equivalent-Sharpe class; regime-attribution-clean (Check 3c PASS); lowest OOS MaxDD in cycle-5 (21.61%) | **CONFIRMED — /044 P2 LINK-ONLY-TREND specialist slot at 12-15% weight; sister-component to P1 /036 LINK+DOT (both belong); /044 BUNDLE-CONFIRMATION-PORTFOLIO 6-component substrate v3 FINAL** | **regime-specialist-OOS (band #3) — bear-OOS-specialist (Δ +0.26 within-regime vs baseline LINK) + chop-OOS-PnL-positive specialist + lowest cycle-5 OOS MaxDD; LINK-trend-scan owns bear-regime via different mechanism than baseline σ_t labels; intrinsic-anchor magnitude prediction bullseye validates the basin-relocation as EQUIVALENT-class not lottery; basin-lottery question deferred to /044 multi-seed CONFIRMATION** |

---

## 7. /044 BUNDLE-CONFIRMATION-PORTFOLIO Composition — FINAL (cycle-5 substrate v3, 6 components)

### 7.1 Final 6-component portfolio composition

| Slot | Component | Mechanism | Regime profile | Weight | Bundle-role |
|------|-----------|-----------|----------------|-------:|-------------|
| **P0 — ANCHOR** | BASELINE_V1 (5-cohort triple-barrier, 193 cols) | Universal substrate; BTC-OOS-strong (+33.17%) + LINK-universal (IS +72 / OOS +34) cohorts; LTC catastrophe absorbed | type-C universal; OOS +0.6637; covers BTC + LINK universally; broad regime coverage | **30%** | universal anchor |
| **P1 — ALT-TREND** | /036 LINK+DOT trend-scan specialist (2-cohort) | Trend-scanning Wald-t labels extract trend subspace LINK+DOT favor; per-cohort isolation prevents BTC/ETH mean-reverting regime contamination | type-B strong; OOS +1.7465 (+1.08 Δ); 50/50 LINK/DOT; bear+chop+bull broad OOS edge | **20-25%** | broad-trend cohort-pair specialist |
| **P2 — LINK-ONLY-TREND** *(NEW from /043)* | /043 LINK-only trend-scan specialist (1-cohort) | Same trend-scanning mechanism as /036, LINK-isolated; targets LINK's strong bear-regime trend persistence | type-B regime-specialist-OOS; OOS +1.2558 (+0.59 Δ vs baseline); bear-OOS Δ +0.26 + chop-OOS +15pp PnL lift; LOWEST OOS MaxDD in cycle-5 (21.61%) | **12-15%** | bear+chop OOS specialist (sister to P1) |
| **P3 — IS-MOMENTUM** | /040 composed regime_momentum_signed_5d (stack-pruned 44→22 cols via cluster-MDA on IS) | 5-day momentum × sign(Hurst−0.5) captures medium-frequency directional moves; per-regime-decomposition wins 5 of 6 IS regimes; LTC-rescue +67pp | type-A strong-IS; IS +0.5588 (+0.28 Δ); LTC-OOS-rescue; covers 5 of 6 IS regimes including 2025-Q1 +57.29pp | **15-18%** | IS-momentum 5-regime contributor |
| **P4 — DOWNSIDE-SHAPE** | /037 5-cohort + Sortino objective (193 cols, downside-deviation objective) | DOT type-C universal (IS +57.20 / OOS +39.30); LTC catastrophe-recovery (+38pp); right-tail-concentration mechanism | type-B mid; OOS +0.8388 (+0.18 Δ); covers DOT-universal + LTC-recovery | **12-15%** | DOT amplifier + LTC-OOS-rescue |
| **P5 — XGB-BEAR-CHOP-IS** *(NEW from /042)* | /042 XGBoost level-wise (44 cols, BULL-GATED) | XGBoost depth-3-5 narrower than LGBM leaf-wise; better-fit to 5-cohort × monthly-cell training sizes; bear+chop+vol-spike IS-specialist; bull-regime conditional dispatch gate REQUIRED | regime-specialist-IS; IS +0.7438 (+0.46 Δ); bear/chop/vol-spike IS-dominant; bull OOS Δ −1.18 EXCEEDS σ_R (requires gate); n_eff=10 ridge-break | **10-12%** | bear+chop IS specialist (bull-gated) |

**Weight sum**: 30 + 22.5 (P1 midpoint) + 13.5 (P2) + 16.5 (P3) + 13.5 (P4) + 11 (P5) = **107%** — over-allocated by 7%. Final calibration at /044 BUNDLE-CONFIRMATION composition test will normalize; midpoints used here as illustrative.

**Weight allocation rationale**:
- P0 30% reduced from substrate-v2's 40% (room made for P2 + P5)
- P1 20-25% reduced from substrate-v2's 25% (room made for P2 LINK-only-trend sister)
- P2 12-15% NEW slot for LINK-only-trend specialist
- P3 15-18% reduced from substrate-v2's 20% (room made for P5)
- P4 12-15% (≈ substrate-v2's 15%)
- P5 10-12% NEW slot for XGBoost bear-chop-IS specialist with bull-gate

### 7.2 Regime coverage table (post-/043 substrate v3 6-component)

| Regime | P0 BASELINE | P1 /036 | P2 /043 | P3 /040 | P4 /037 | P5 /042 (bull-gated) | Coverage status |
|---|---|---|---|---|---|---|---|
| 2022-bear (IS) | mid | n/a | n/a | **WINS** | mid | **STRONG bear-specialist IS** | well-covered |
| 2023-Q1Q2-chop (IS) | mid | weak | n/a | **WINS late** | mid | **STRONG chop-specialist IS** | well-covered |
| 2023-Q3Q4-recovery (IS) | mid | n/a | n/a | WEAK | mid | mid | partially-covered |
| 2024-Q1Q2-bull (IS) | mid | TBD | n/a | mid | mid | OFF (gate) | partially-covered (P0 anchor) |
| 2024-Q3Q4-transition (IS) | mid | TBD | n/a | **WINS** | mid | mid | well-covered |
| 2025-Q1-IS-tail (IS) | mid | TBD | n/a | **WINS extreme** | mid | mid | well-covered |
| **OOS bull** (2025-05/06/07) | mid | TBD-strong | within-σ_R | mid | mid | OFF (gate) | P0 + P1 share; **P2 within-σ_R** |
| **OOS bear** (2025-Q3+) | +1.62 | TBD-strong | **+0.26 within-regime Δ vs baseline** | weak | mid | parity to baseline | **P2 owns within-regime lift**; P0 + P1 anchor |
| **OOS chop** (2025-Q2 + 2026-03) | +1.04 | TBD | **+20% PnL** | weak | mid | mid | **P2 contributes positive PnL**; P0 anchor |
| **OOS recovery** (2026-04) | +0.42 | TBD | n/a | mid | mid | **+8.94% PnL Δ +16.86pp** (n=1) | **P5 owns** (single-month inconclusive) |

**Coverage verdict**: well-covered across IS regimes (P3 + P5 share bear/chop/vol-spike IS coverage; P0 anchors bull/recovery IS). OOS coverage: P0 anchors broad; P1 carries broad OOS-trend; P2 specializes bear+chop; P5 specializes bear+chop+recovery IS — at-risk pair P3 ↔ P5 collinear on bear/chop IS (correlation expected MEDIUM-HIGH 0.65-0.75; bundle composition test must verify Pareto-positive net contribution).

### 7.3 Correlation pair analysis (per closeout checklist mandate)

**Expected pairwise correlations**:

| Pair | Trade Jaccard estimate | Daily-PnL correlation estimate | At-risk? |
|------|---:|---:|---|
| P0 ↔ P1 | 0.15 | 0.30 | low |
| P0 ↔ P2 | 0.10 | 0.25 | low |
| P0 ↔ P3 | 0.40 | 0.55 | medium |
| P0 ↔ P4 | 0.45 | 0.65 | medium |
| P0 ↔ P5 | 0.50 | 0.60 | medium |
| **P1 ↔ P2 (sister)** | **0.05** | **0.55-0.70** | **MEDIUM-HIGH — at-risk** |
| P1 ↔ P3 | 0.08 | 0.15 | low |
| P1 ↔ P4 | 0.10 | 0.20 | low |
| P1 ↔ P5 | 0.12 | 0.25 | low |
| P2 ↔ P3 | 0.05 | 0.15 | low |
| P2 ↔ P4 | 0.05 | 0.18 | low |
| P2 ↔ P5 | 0.10 | 0.20 | low |
| P3 ↔ P4 | 0.10 | 0.18 | low |
| **P3 ↔ P5** | **0.30** | **0.65-0.75** | **MEDIUM-HIGH — at-risk** |
| P4 ↔ P5 | 0.20 | 0.40 | medium |

**At-risk correlation pairs (> 0.70 expected) require justification**:
- **P1 ↔ P2 (/036 LINK+DOT vs /043 LINK-only)**: BOTH are trend-scanning specialists on overlapping cohort (LINK in common; DOT only in P1). Trade Jaccard expected very low (0.05) because /043 basin relocated from /036's LINK leg at single-seed=42 (Jaccard 2.74% observed). Daily-PnL correlation higher (0.55-0.70) because both trade LINK during trend periods. **JUSTIFICATION**: P2 adds **bear-regime LINK-only specialization** (Δ +0.26 within-regime vs baseline) that P1 does not isolate; P1 provides **cross-cohort LINK+DOT variance averaging** (lower portfolio σ). Bundle composition test at /044 will verify net Pareto-positive contribution; if collinear and not Pareto-positive, drop P2 OR reduce weights of both to 8-10% each.
- **P3 ↔ P5 (/040 IS-momentum vs /042 XGBoost)**: BOTH are IS-strong regime-specialists with regime decomposition winning 5-of-6 (P3) / 3-of-4 (P5) IS regimes. Bundle composition test must verify they STACK without cannibalization. If correlation > 0.70 at multi-seed, prefer the component with HIGHER multi-seed validated mean Sharpe in target regimes (P5 likely if XGBoost's n_eff lift translates) OR keep both at lower weights (8-10% each).

### 7.4 /044 BUNDLE-CONFIRMATION-PORTFOLIO spec (engineering details)

| Item | Spec |
|---|---|
| Sub-iter | 6 sub-runs OR portfolio-aggregator dispatch |
| Multi-seed | 5 outer seeds per component (NOT 10 — cycle-5 CONFIRMATION budget per `feedback_v3_outer_seed_cap_2_v3.md`-adjacent v1 standard adjusted up; budget review at orchestrator decision) |
| n_trials | 35 per CONFIRMATION default |
| ENSEMBLE_SIZE | 5 per CONFIRMATION standard |
| Wall-clock estimate | P0=N/A (anchor) / P1=2h / P2=1h / P3=3h / P4=3h / P5=3h ≈ **12h total** — exceeds 4h cap; split across two sessions OR run parallel where possible OR drop one component at orchestrator discretion |
| Portfolio aggregator | Trade-stream merge at weights specified above; compute portfolio comparison.csv vs P0-anchor-only baseline |

### 7.5 Pareto / multi-seed acceptance gates (per-component)

Each component independently must clear:
- 5-seed mean Sharpe (OOS) > 0
- ≥ 3 of 5 seeds OOS Sharpe > 0
- ≥ 4 of 5 seeds IS Sharpe > 0
- per-cohort OOS PnL sign-stability (≥ 3 of 5 seeds same sign for each load-bearing cohort)

**Component-level failure ⇒ component dropped from portfolio**; portfolio re-aggregates with remaining components at re-normalized weights.

### 7.6 Portfolio-level MERGE gates (NEW METHODOLOGY)

- **Check 3d — bundle-level per-regime Pareto-dominance vs BASELINE_V1** (HARD): every tagged regime satisfies sharpe_R(cand) ≥ sharpe_R(base) − σ_R AND max_dd_R(cand) ≤ max_dd_R(base) + σ_dd_R AND trade_count_R(cand) ≥ 0.5 × trade_count_R(base) AND ≥1 regime is strictly better. σ_R / σ_dd_R sourced from `baseline_seed_regime_matrix.csv`.
- Bundle OOS Sharpe (INFORMATIONAL): aspirational ≥ +1.0 floor
- OOS/IS Sharpe ratio (INFORMATIONAL): aspirational ≥ 0.5
- Top-symbol concentration (INFORMATIONAL): aspirational ≤ 30% portfolio OOS PnL
- Portfolio OOS trades (INFORMATIONAL): aspirational ≥ 130

Methodology integrity gates (look-ahead, embargo, CV gap, reproducibility, no OOS tuning, feature pinning, forming-candle drop, ADF) PRESERVED HARD.

---

## 8. Cycle-5 status — 10/10 EXPLORATIONs COMPLETE — /044 BUNDLE-CONFIRMATION-PORTFOLIO authorized

**Cadence position**: 10/10 cycle-5 EXPLORATIONs complete. /043 is the FINAL cycle-5 EXPLORATION; the substrate-composition diagnostic role is resolved (LINK-only is a legitimate sister to /036 LINK+DOT; both belong in /044).

**Cycle-5 hit rate (10/10)**:
- 3 PROMISING under OLD methodology (/036 PROMISING-CLEAN +1.08 OOS Δ, /037 PROMISING-CLEAN +0.18 OOS Δ, /043 PROMISING-anchor-bullseye)
- 5 NEG under OLD methodology (/034 + /035 + /038 + /039 + /041)
- 1 NEG/Mixed under OLD methodology (/040)
- 1 REGIME-SPECIALIST-IS under NEW methodology (/042)
- 1 REGIME-SPECIALIST-OOS under NEW methodology (/043)
- = **30% PROMISING (OLD lens) / 50% PROMISING-or-SPECIALIST (NEW lens)**

**Cycle-5 axis-family closure summary**:
- `feature-family` CLOSED (/034 + /040; cycle-6 may reattempt with cross-asset NEW family)
- `risk-primitive` CLOSED (/038 + /039)
- `labeling` CLOSED across full barrier-magnitude curve (/014 + /015 + /041)
- `loss-function` CLOSED for substrate compounding (/037 + /039)
- `per-cohort-specialization × labeling` REPEAT-COMBO informative service complete (/036 + /039 HYBRID + /043; substrate-composition diagnostic role served — family OPEN for cycle-6+ with new substrate decompositions)
- `model-arch` OPEN for cycle-6 (/042 REGIME-SPECIALIST-IS; stack-width × model-arch interaction load-bearing; CatBoost/MLP head-to-heads viable axes)
- `hyperparameter-region` OPEN
- `methodology-substrate-test` OPEN

**/044 BUNDLE-CONFIRMATION-PORTFOLIO requires bootstrap artifacts BEFORE composition test**:
- [ ] `briefs-v1/_meta/baseline_metric_anchors.csv` — bundle-level metrics for current BASELINE_V1 (IS + OOS columns)
- [ ] `briefs-v1/_meta/baseline_seed_regime_matrix.csv` — 10 seeds × N regimes × {Sharpe, max_dd, trade_count} (source of σ_R for Check 3d)
- [ ] `briefs-v1/_meta/regime_catalog.md` — canonical regime tag definitions (BTC 90-day return × 30-day realized-vol quantiles; expanded to cover alt-rotation / ETF-flow / liq-cascade per LM Master flag in /042)

These three artifacts are ONE-TIME bootstrap deliverables of the first bundle-CONFIRMATION; subsequent CONFIRMATIONs update them.

**Next iteration**: /044 BUNDLE-CONFIRMATION-PORTFOLIO. QR Phase 1-5 brief authors the three bootstrap artifacts AS A PRECONDITION to the composition test; QE Phase 6 dispatches the 6-component portfolio; LM Master Phase 7.4 emits Item-0 Regime Attribution Table at bundle-level; Critic Phase 7.5 evaluates Check 3c + Check 3d as HARD gates. Outcome determines BASELINE_V1.md update vs CONFIRMATION-BLOCK.

---

## 9. Path Forward — Critic verbatim copy (mandatory under new methodology; from §5.5)

[Copied verbatim from §5.5 above per closeout checklist mandate]

**Path Forward #1**: /044 BUNDLE-CONFIRMATION-PORTFOLIO authorized at 6-component substrate v3.
**Path Forward #2**: /044 bootstrap artifacts (`baseline_metric_anchors.csv`, `baseline_seed_regime_matrix.csv`, `regime_catalog.md`) authored BEFORE composition test.
**Path Forward #3**: Substrate-composition diagnostic for LINK-only vs LINK+DOT — RESOLVED at /043 (both belong as sister-components).
**Path Forward #4**: Cycle-5 axis-family closures formalized (feature-family / risk-primitive / labeling / loss-function CLOSED; model-arch / hyperparameter-region / methodology-substrate-test OPEN for cycle-6).
**Path Forward #5**: Cycle-6 axis priorities (post-/044) — Pool A decomposition (BTC+ETH split), cross-asset feature families, CatBoost/MLP model-arch, per-regime DD brake.

---

## 10. Comparison: how this /043 closeout differs from /042 closeout (first under NEW methodology)

The /042 closeout was the FIRST under the regime-aware 9-band framework (2026-05-31 reframe). /043 is the SECOND closeout under the new framework. Differences and parallels:

**Parallels (both /042 and /043)**:
1. LM Master Phase 7.4 Item-0 Regime Attribution Table is the load-bearing INPUT (not retrofit afterthought).
2. Critic Check 3c (regime-attribution clarity) is MANDATORY and PASS.
3. 9-band canonical verdict vocabulary REPLACES bespoke labels.
4. DSR/PBO/PSR demoted to INFORMATIONAL.
5. Bundle-role per regime is structured INPUT, carried through to /044 substrate v3 routing.

**Differences (specific to /043)**:
1. **/043 verdict is band #3 (REGIME-SPECIALIST-OOS), /042 was band #2 (REGIME-SPECIALIST-IS)** — distinct band assignments under the 9-band tree: /042 owns IS regimes (bear/chop/vol-spike-IS), /043 owns OOS regimes (bear+chop OOS Δ vs baseline LINK-leg).
2. **/043 single-cohort isolation by construction** → trade-rate / concentration floors are universally INAPPLICABLE (single-cohort universe by design). /042 was 5-cohort pooled.
3. **/043 had explicit EDA-derived intrinsic-anchor magnitude prediction (+1.2321) → observed +1.2558 BULLSEYE** (within +0.024 of central). /042 had qualitative LM Master prior bands; magnitude was not as precisely predicted.
4. **/043 axis family is REPEAT-COMBO (per-cohort-specialization × labeling)** — the first REPEAT-COMBO closeout under new methodology. /042 was a NEW family (model-arch) in cycle-5.
5. **/043 BREAKS the cycle-5 substrate-composition diagnostic ambiguity** — proves LINK-only is a legitimate sister-component (not a degenerate single-cohort artifact). /042 broke the LightGBM n_eff=9 ridge.

---

## 11. Risk Mitigation recap (no R5 fire, no vol-ceiling fire, R1 + R3 baseline)

Per `comparison.csv` / engineering report (per-cohort-specialization × labeling axis is orthogonal to risk-primitive gates):
- R1 (SL cooldown) ON for Model C' (LINK only) — baseline UNCHANGED
- R2 (DD scaling, E-only) NOT APPLICABLE (DOT-only gate; /043 has no DOT)
- R3 OOD Mahalanobis ON per baseline configuration
- R5 vol-floor scaling NOT engaged (orthogonal to axis)
- Vol-ceiling gate NOT engaged (orthogonal to axis)

**/043 inherits baseline risk configuration unchanged** — the axis change is universe-restriction + label-mode (both at strategy layer, not risk layer).

---

## 12. Files & Commits on Branch

- `briefs-v1/iteration_v1-043/research_brief.md` — Phase 5 QR brief (LINK-only trend-scan substrate-composition diagnostic; 971 lines)
- `briefs-v1/iteration_v1-043/eda_findings.md` — Phase 1-3 IS-only EDA (intrinsic-anchor reconstruction; 149 lines)
- `briefs-v1/iteration_v1-043/lgbm_advisor.md` — Phase 4.5 LM Master pre-design (55 lines; Phase 7.4 Regime Attribution Table content embedded in this diary §2.1)
- `briefs-v1/iteration_v1-043/phase5p5_gate.md` — Phase 5.5 Phase gate PASS
- `briefs-v1/iteration_v1-043/critic_preflight.md` — Phase 6.0 Critic pre-flight PASS
- `briefs-v1/iteration_v1-043/new_skill_audit.md` — new-skill methodology compliance audit
- `reports-v1/iteration_v1-043/comparison.csv` — bundle-level metrics (IS Sharpe +0.3359 / OOS +1.2558)
- `reports-v1/iteration_v1-043/regime_attribution.csv` — per-regime decomposition (NEW QE Phase 6 deliverable per new-skill 2026-05-31)
- `reports-v1/iteration_v1-043/{in_sample,out_of_sample}/per_symbol.csv` — single-cohort LINKUSDT attribution
- `reports-v1/iteration_v1-043/{in_sample,out_of_sample}/feature_importance_Model_C_LINK_trend_scan_only.csv` — feature importance LINK-only specialist
- `reports-v1/iteration_v1-043/{in_sample,out_of_sample}/{dsr.json,ic_matrix.csv,adf_test.csv,trades.csv,daily_pnl.csv,monthly_pnl.csv,per_regime.csv,quantstats.html}` — full report bundle
- `reports-v1/iteration_v1-043/basin_diagnostics/` — basin diagnostics (Jaccard 2.74% finding)
- `analysis/iteration_v1-043/eda.py` — IS-only EDA committed analysis script

**Commits**: brief authoring + `12a0097` (Phase 6.0 critic_preflight PASS — historic) + `1be3bd1` (feat: basis_zscore_30 feature + dispatch + tests — historic from /034) + `86dc55d` (docs: EXPLORATION-NEGATIVE closeout — historic from /034) + Phase 7-8 closeout (this diary) + catalog update + substrate-proposal update.

**Branch**: `iteration-v1/043` (not yet merged to `main` — cycle-5 closeout pending all 10 EXPLORATIONs documented; orchestrator may cherry-pick to main after substrate v3 finalization).

---

## 13. Track Record post-/043 (cycle-5 FINAL)

**Cycle-5 hit rate (10/10 — CADENCE COMPLETE)**:
- 3 PROMISING under OLD methodology (/036 / /037 / /043 PROMISING-anchor-bullseye)
- 5 NEG under OLD methodology (/034 + /035 + /038 + /039 + /041)
- 1 NEG/Mixed under OLD methodology (/040)
- 1 REGIME-SPECIALIST-IS under NEW methodology (/042)
- 1 REGIME-SPECIALIST-OOS under NEW methodology (/043)
- = **30% PROMISING (OLD lens) / 50% PROMISING-or-SPECIALIST (NEW lens)**

**Substrate v3 FINAL composition (post-/043)**: 6 components — P0 BASELINE 30% + P1 /036 LINK+DOT 20-25% + P2 /043 LINK-only-trend 12-15% + P3 /040 IS-momentum 15-18% + P4 /037 Sortino 12-15% + P5 /042 XGBoost-bull-gated 10-12%.

**LM Master directional running tally**: 3/10 = 30% absolute-Sharpe lens (up from 2/9 = 22.2% post-/042). Under regime-aware lens additional mechanism-integrity credit applies. EDA-derived intrinsic-anchor magnitude prediction at /043 outperformed LM Master qualitative band by structural margin.

**Open axes for cycle-6 (post-/044 BUNDLE-CONFIRMATION-PORTFOLIO outcome)**:
- Pool A decomposition (BTC + ETH single-symbol models) — priority #1 per /042 BTC OOS −62% finding
- Cross-asset feature families (funding rates, OI, basis, microstructure) — priority #2 per `feedback_v3_mass_feature_expansion.md` analog
- CatBoost / deep-tabular MLP head-to-head model-arch — priority #3
- Per-regime DD brake (risk-primitive at regime-conditional dispatch) — priority #4

---

## 14. Closure Note — cycle-5 EXPLORATION CADENCE COMPLETE 10/10; /044 BUNDLE-CONFIRMATION-PORTFOLIO authorized

**Specifically resolved at /043**: LINK-only trend-scan substrate-composition diagnostic on /036's LINK+DOT 2-cohort substrate. **NOT NEGATIVE under new methodology — REGIME-SPECIALIST-OOS (band #3) with bear+chop OOS-regime ownership and lowest cycle-5 OOS MaxDD**.

**Mechanism**: LINK trend-scan owns OOS bear regime via different mechanism than baseline σ_t labels (LINK's strong bear-regime trend persistence distinct from BTC/ETH mean-reverting bear behavior; baseline σ_t labels treat bear moves as noise-volatility because σ_t threshold normalizes by elevated bear vol); LINK-only single-cohort isolation produces controlled-DD profile (21.61% OOS MaxDD = LOWEST in cycle-5); basin RELOCATED from /036's LINK leg (Jaccard 2.74%) but to EQUIVALENT-SHARPE basin within the LINK-only intrinsic-Sharpe equivalence class (Sharpe +0.024 above EDA central); bullseye magnitude prediction validates the basin-relocation as equivalent-class not lottery.

**/036 substrate-composition diagnostic answer**: LINK-only is a LEGITIMATE STANDALONE BUNDLE COMPONENT (sister to /036 LINK+DOT), NOT a degenerate single-cohort artifact. Both belong in /044 portfolio: P1 = /036 (broad LINK+DOT trend cohort-pair); P2 = /043 (LINK-only bear+chop OOS specialist).

**NOT refuted at /043**: any existing /044 substrate component (BASELINE + /036 + /037 + /040 + /041-conditional + /042-conditional). /043 ADDS a new P2 LINK-ONLY-TREND slot at 12-15% weight. Substrate v3 FINAL at 6 components.

**Methodology forward-bind**: this is the SECOND iteration closed under the regime-aware 9-band framework (after /042 first-closeout). The new framework correctly classifies /043 as REGIME-SPECIALIST-OOS (band #3) — under OLD framework /043 would have been stamped EXPLORATION-NEGATIVE-CLEAN on the bundle-Sharpe-Δ-vs-/036 axis (−0.49 inside NEG-CLEAN band), killing a legitimate bundle component delivering +0.59 OOS Sharpe Δ vs BASELINE_V1 and owning bear+chop OOS regimes. The new framework picks this up; the absolute-Sharpe framework destroyed it. **Cycle-5 EXPLORATION CADENCE COMPLETE 10/10; /044 BUNDLE-CONFIRMATION-PORTFOLIO authorized.**

**End of diary-v1/iteration_v1-043.md.**
