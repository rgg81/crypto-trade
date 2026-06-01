# v1 Cycle-3 Closeout — 2026-05-26 → 2026-05-28

**Status**: CLOSED without CONFIRMATION verdict (TECHNICAL FAILURE at /027 closing iteration).
**Anchor**: `v0.v1-baseline-corrected` (BASELINE_V1.md commit `f8bc12c`). **UNCHANGED.**
**Tags issued in cycle**: `v0.v1-016`, `v0.v1-017`, `v0.v1-018`, `v0.v1-019`, `v0.v1-020`, `v0.v1-021`, `v0.v1-022`, `v0.v1-023`, `v0.v1-024`, `v0.v1-025`, `v0.v1-026`, `v0.v1-027-technical-failure`. No `v0.v1-027-final` tag.

---

## 1. Cadence

- **10 EXPLORATIONs** (/016 → /025) completing the cadence rule "≥10 EXPLORATION precedents accumulate since the last CONFIRMATION".
- **1 pre-CONFIRMATION sanity slot** (/026 — cross-correlation validation, analysis-only).
- **1 CONFIRMATION TECHNICAL FAILURE** (/027 — runner crashed at hard-assert; no verdict possible).
- **Total**: 12 iteration slots used.

EXPLORATION wall-clock budget: every EXPLORATION cleared the 2h cap (modal 25-90 min). CONFIRMATION wall-clock: /027 breached the 6h cap by 2.2× (13h actual) AND crashed at post-training — cycle-4 must add explicit progress logging at month-boundary granularity to detect rate breach before half-finish.

---

## 2. Verdict Distribution (cycle-3)

| Slot | Verdict | Notes |
|---|---|---|
| /016 | EXPLORATION-NEGATIVE catastrophic | R5 vol kill-switch — risk-primitive family closed |
| /017 | EXPLORATION-NEGATIVE anti-direction-INERT | +SOLUSDT 6-sym universe expansion |
| **/018** | **EXPLORATION-PROMISING-INERT favorable** | **LINK-only specialist, single-seed OOS Δ +0.80** |
| **/019** | **EXPLORATION-PROMISING** | **ETH-only + asymmetric BTC-trend gate, single-seed OOS Δ +0.50** |
| /020 | EXPLORATION-NEGATIVE catastrophic | BTC-only specialist — NEGATIVE prior cohort |
| /021 | EXPLORATION-PROMISING-METHODOLOGY | H1 basin-isolation refuted; H2 basin-substrate refuted; non-compoundable |
| /022 | EXPLORATION-NEGATIVE catastrophic | LTC-only specialist + long-suppress gate — NEGATIVE prior cohort |
| /023 | EXPLORATION-NEGATIVE-LEARNED-clean | funding-rate z30/z90 — feature learned but no edge |
| /024 | EXPLORATION-NEGATIVE clean | regime-conditional 7 sub-models — partition non-specializing |
| /025 | EXPLORATION-NEGATIVE-LEARNED-CATASTROPHIC | OI delta z90 — feature learned but OOS catastrophic |
| /026 | GREEN-WITH-FIX (sanity) | replacement-pool Pearson +0.4935 / -0.1412 — both PASS; C×E +0.6027 breach flagged for cycle-4 |
| /027 | **CONFIRMATION-TECHNICAL-FAILURE** | runner crashed at hard-assert; no verdict; cycle closes here |

**Summary**: 2 PROMISING + 1 PROMISING-METHODOLOGY (non-compoundable) + 7 NEGATIVE + 1 sanity + 1 TECHNICAL FAILURE = **0 edge ingredients merged.**

---

## 3. Structural Findings (DURABLE; carry forward to cycle-4+)

### Finding 3.1 — Per-cohort isolation only works with INDEPENDENT positive prior OR orthogonal mechanism

Cycle-3's per-cohort axis family was the dominant axis (5 of 10 EXPLORATIONs: /018, /019, /020, /022 and indirectly /024 via the regime-partition variant). The empirical pattern across the four direct per-cohort EXPLORATIONs is unambiguous:

| Cohort | Prior signal in BASELINE_V1 pool | /018-/022 per-cohort outcome |
|---|---|---|
| LINK | + +34.23% OOS net PnL (positive prior) | **PROMISING** (/018 OOS Δ +0.80) |
| ETH | + 11.08% / -26.87% IS-OOS rotation (mixed) | **PROMISING with asymmetric gate** (/019 OOS Δ +0.50) |
| BTC | + +33.17% OOS / -73.11% IS (rotation prior) | **NEGATIVE catastrophic** (/020 OOS Δ -0.86) |
| LTC | -47.25% OOS / +6.42% IS (negative prior + gate) | **NEGATIVE catastrophic** (/022 OOS Δ -1.17) |

**Read**: per-cohort isolation does NOT generally lift; it only lifts when the cohort either (a) has an independent positive prior pre-isolation (LINK), OR (b) the isolation comes with an orthogonal mechanism (ETH + BTC-trend gate) that constrains the basin draw. Cohorts with rotation priors (BTC) or negative priors (LTC) regress catastrophically because isolation removes whatever pool-level regularization was holding the noisier basin in check.

**Forward-binding**: cycle-4 per-cohort EXPLORATIONs MUST declare in brief Section 2 whether the candidate cohort has (a) an independent positive prior in pool baseline, OR (b) brings an orthogonal mechanism. Bare per-cohort isolation on a NEGATIVE-prior cohort is now a dead path until new evidence.

### Finding 3.2 — Pool A + NEW feature family at single-seed = LEARNED-NEGATIVE (n=2 confirmation)

| iter | NEW feature family | Pool A learning evidence | OOS outcome |
|---|---|---|---|
| /023 | funding rate z30 + z90 (Binance funding endpoints) | F-AXIS #1 DUAL GATE 4/4 PROMISING; feature LEARNED uniformly | F1 OOS Δ -0.20 (NEGATIVE LEARNED-clean) |
| /025 | OI delta z90 | F-AXIS #1 DUAL GATE 4/4 PROMISING; feature LEARNED uniformly | F1 OOS Δ -1.40 (NEGATIVE LEARNED-CATASTROPHIC) |

**Read**: at single-seed EXPLORATION budget under the existing Pool-A-pooled architecture, NEW feature families that the model LEARNS via uniform F-AXIS gain-share gates STILL produce OOS-negative outcomes. The model is acquiring NEW signal mechanically; that signal is OOS-suboptimal. This is the v3-style "INERT features at higher Optuna budget actively HARM OOS" pattern surfacing in v1 too. **Adding NEW feature families to the existing Pool A architecture at single-seed EXPLORATION is now a dead path until a NEW substrate is introduced first** (NEW model architecture, NEW labeling, OR multi-seed validation before feature-addition commits).

**Forward-binding**: cycle-4 NEW feature family EXPLORATIONs must EITHER (a) be tested on top of a NEW substrate (e.g., XGBoost head-to-head, OR sample-weighted training), NOT bare Pool A; OR (b) be deferred to a multi-seed CONFIRMATION precondition test before single-seed feature-family EXPLORATION fires.

### Finding 3.3 — Regime-conditional sub-models do NOT specialize at single-seed

/024 partitioned each cohort into 2 regime sub-models on `|funding_z30| > 1.5`. F-AXIS #1 dispatch PASS (sub-models built); F-AXIS #5 gain-share recurrence FAIL on 2/3 cohorts (the partition mechanically engaged but did not produce regime-specialized signal). F3 IS catastrophic at -0.86.

**Read**: regime-conditional partitioning at single-seed EXPLORATION under the existing Pool A + 4-cohort architecture is dispatch-correct but signal-INERT. The basin-aggregation across 7 sub-models with single-seed=42 does not produce regime-specialized signal — the sub-models converge to similar loss surfaces. This generalizes Cycle-2's "single-axis-INERT" pattern: model architecture changes at single-seed are subject to the same basin-aggregation effect as feature additions.

**Forward-binding**: NEW model architectures (e.g., XGBoost, NEW ensemble compositions, regime-conditional variants) at cycle-4 should be tested with multi-seed FROM THE START (mandatory 2-seed minimum even at EXPLORATION budget), NOT single-seed EXPLORATION first.

### Finding 3.4 — Methodology validation question (/027) remained UNANSWERED

Cycle-3 was designed to close with a CONFIRMATION methodology validation: does the per-cohort architecture (/018 LINK + /019 ETH+gate) hold at multi-seed under the LOCKED 5-model replacement bundle? The /027 TECHNICAL FAILURE leaves this question open. The per-cohort architecture status is held at "two single-seed PROMISING EXPLORATIONs + multi-seed unanswered" entering cycle-4.

**Forward-binding**: if and only if cycle-4 EXPLORATIONs (or their cycle-4 CONFIRMATION) re-surface per-cohort specialization as the natural bundling candidate, the cycle-4 CONFIRMATION must re-answer this question. Otherwise the question stays open as a cycle-3 inheritance.

### Finding 3.5 — LM Master cycle-3 track record

- **Methodology track**: **6/6 PERFECT** across the cycle. Every methodology recommendation that landed on a methodology axis (basin diagnostic /021, n_eff calibration sweep /014-/015, hard-assert MANDATE form at /027) was empirically validated for the methodology it asserted. The /027 form was right; the INTEGRATION test was missing.
- **Directional (verdict-class magnitude) track**: **2/8 = 25%** across the cycle. Modal priors hit on /018 + /019 (PROMISING band predictions correct). Missed on /016/017/020/022/023/024/025 (magnitude band predictions wrong by at least one band). Cycle-3 directional track was WEAKER than cycle-2's directional track despite the cycle-2 PROMISING-METHODOLOGY /008 substrate.

**Forward-binding**: cycle-4 should preserve LM Master methodology recommendations as ADOPTED-VERBATIM (mechanism-deterministic; integration-test-mandate added per /027 lesson) but treat directional priors as INFORMATIONAL ONLY (the 2/8 cycle-3 track does not warrant load-bearing reliance on magnitude band predictions yet).

---

## 4. Cycle-4 Staging — MANDATORY axis candidates

### 4.1 Cycle-4 first or second EXPLORATION: D-specialist MANDATORY

The LTC drag (OOS Sharpe -1.05; OOS net PnL -47.25% — worst cohort contributor) is unaddressed at cycle-3 close. /022 LTC NEGATIVE catastrophic at single-seed leaves Model D in BASELINE_V1.md unchanged. Cycle-4 must address this with EITHER:
- A D-specialist axis with a NEW orthogonal mechanism (e.g., explicit LTC volatility-regime gate; LTC-only sample weighting; LTC universe removal with 4-symbol pool), OR
- A universe contraction to 4 symbols (BTC/ETH/LINK/DOT) with explicit baseline re-anchoring required.

The bare LTC-only isolation is CLOSED (per /022 dead path). New evidence required.

### 4.2 Cycle-4 second or third EXPLORATION: C×E altcoin de-concentration required

/026 5-model cross-correlation surfaced C_link × E_dot OOS Pearson +0.6027 (Spearman +0.425). LM Master /027 §2 predicted this is signal-level co-movement (NOT basin lottery) and **WILL NOT dissolve at multi-seed**. Cycle-4 must address altcoin-cohort concentration explicitly with one of:
- Per-cohort drawdown brake (loss-stop semantics; NOT proportional caps — per-symbol PnL caps CLOSED at v1 catalog per /020 closeout reasoning carried over from v3)
- Vol-target ceiling on altcoin cohort exposure
- Regime-conditional kill switch on the altcoin pair under coordinated drawdown

Per-symbol proportional caps remain CLOSED.

### 4.3 Cycle-4 NEW-UNUSED-axis candidates

- **Sample-weighting** (NEVER tried in v1): López de Prado AFML Ch. 4 uniqueness weighting; OR hard-negative oversampling on cohort-specific OOS-losing trades. ORTHOGONAL to all cycle-3 axes. Recommended cycle-4 EXPLORATION #3-5.
- **XGBoost head-to-head against LightGBM** (NEVER tried in v1; was tried in v3 with NEGATIVE outcome). v1 substrate's LightGBM-specific basin may respond differently. Recommended cycle-4 EXPLORATION #4-6.

### 4.4 Cycle-4 first CONFIRMATION

Subject to which axis families surface as PROMISING in cycle-4 EXPLORATIONs. If per-cohort axis re-emerges, it MUST re-answer /027's UNANSWERED methodology question (multi-seed validation of the bundle). If cycle-4 produces a NEW PROMISING axis family, the first CONFIRMATION bundles THAT axis instead — /027's per-cohort bundle is held in cold storage.

---

## 5. Process Lessons (Forward-binding cycle-4+)

### 5.1 Defensive runtime checks must be unit-tested against real instances

/027 lesson. When a defensive assert references an object attribute, the unit test suite must include a test that constructs the object via the production code path and confirms the assert reads every referenced attribute. Adding to Phase 6.0 pre-flight check list at cycle-4 startup.

### 5.2 CONFIRMATION wall-clock observability needs month-boundary granularity

/027 wall-clock 13h vs 6h CAP = 2.2× breach with no early kill. Cycle-4 first CONFIRMATION must add explicit progress logging at month-boundary granularity (one log line per walk-forward month; median wall-clock per month tracked; projected total = current_month × median_per_month × remaining_months / 24). Kill-switch fires when projected total > 1.3× cap.

### 5.3 LM Master directional priors are INFORMATIONAL ONLY at cycle-4 start

Track record 2/8 in cycle-3. Methodology recommendations stay ADOPTED-VERBATIM (track 6/6) but verdict-class magnitude predictions do not carry forward as load-bearing decision inputs. The "directional track strengthens to 6/8 + cycle-4 starts citing as load-bearing" is the threshold to re-elevate.

### 5.4 Multi-seed mandate carries from cycle-3 to cycle-4

Cumulative ≥1σ negative count reached 5 in cycle-3 (/016, /020, /022, /024-IS, /025). The multi-seed mandate already TRIPPED prior to /027 per `feedback_v1_seed_count_non_negotiable.md`. Cycle-4 inherits the active multi-seed mandate: any HIGH-RISK axis must declare and execute multi-seed validation (≥2 outer seeds × ENSEMBLE_SIZE=3 inner minimum) from the EXPLORATION run, NOT defer to a future CONFIRMATION.

---

## 6. Catalog Updates

- `briefs-v1/exploration_catalog.md` — 12 new rows added during cycle-3 (/016 through /027). Last row is /027 = `CONFIRMATION-TECHNICAL-FAILURE`.
- `BASELINE_V1.md` — UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). Cycle-3 closes with NO baseline update.

---

## 7. Cycle Inheritance to Cycle-4

| Item | Cycle-3 outcome | Cycle-4 starting position |
|---|---|---|
| BASELINE_V1.md anchor | UNCHANGED | `v0.v1-baseline-corrected` (`f8bc12c`) |
| Per-cohort architecture | 2 PROMISING single-seed (/018 LINK, /019 ETH+gate); multi-seed unanswered (/027 TECHNICAL FAILURE) | Re-test if axis re-emerges; otherwise held in cold storage |
| Pool A + NEW feature family axis | 2 NEGATIVE LEARNED outcomes (/023, /025) | DEAD path under single-seed bare Pool A; resurrect under NEW substrate or multi-seed precondition |
| Regime-conditional sub-models | 1 NEGATIVE (partition non-specializing) (/024) | DEAD path at single-seed; resurrect under multi-seed |
| Per-symbol proportional caps | inherited DEAD from v3 catalog | Cycle-4 cannot retry; must use orthogonal mechanisms |
| LTC drag | UNADDRESSED | MANDATORY cycle-4 axis (D-specialist or 4-sym universe) |
| C×E altcoin concentration | FLAGGED at /026; predicted to persist at multi-seed | MANDATORY cycle-4 axis (drawdown brake, vol-target ceiling, OR regime kill-switch) |
| Multi-seed mandate | TRIPPED (cumulative 5 ≥1σ negatives) | CARRIES FORWARD — all HIGH-RISK cycle-4 axes must multi-seed |
| LM Master directional priors | 2/8 cycle-3 | INFORMATIONAL only at cycle-4 start; re-elevate at 6/8 cumulative |
| LM Master methodology priors | 6/6 cycle-3 | ADOPTED-VERBATIM continues; integration-test mandate ADDED |
| Phase 6.0 pre-flight checks | adequate for static patterns; missed /027 integration defect | NEW check item: "integration smoke test for every NEW defensive runtime assert" |
| CONFIRMATION wall-clock observability | 2.2× breach uncaught | NEW: month-boundary logging + 1.3× projected cap kill |

---

**End of cycle-3 closeout. Cycle-4 starts at iter-v1/028.**
