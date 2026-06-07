# iter-v1/076 — OOS Evaluation Memo

**Verdict**: SPECIALIST-NEGATIVE (1st strike for AAVE seat)
**Iteration type**: NEW SYMBOL universe-extension (AAVEUSDT specialist) at LOCKED methodology
**Anchor**: implicit single-coin dispatch baseline (no prior AAVE baseline)
**BUNDLE-001 status**: UNCHANGED (DOT/063 + ETH/064 + BTC/065 at v0.v1-071 stand)

---

## 1. Headline Metrics

| Metric | IS | OOS | Ratio |
|---|---|---|---|
| Sharpe | **−0.6943** | **+0.6234** | −0.898 |
| Sortino | −0.6199 | +1.4152 | −2.283 |
| Max DD | 55.33% | 24.43% | 0.442 |
| Win rate | 35.4% | 40.5% | 1.142 |
| Profit factor | 0.8026 | 1.1797 | 1.470 |
| Total trades | 158 | 84 | 0.532 |
| Calmar | 0.786 | 0.665 | 0.847 |
| DSR (info only at EXPLORATION) | −33.03 | −47.08 | 1.425 |
| Net PnL % | −43.48% | +16.26% | −0.374 |
| Specialist dispersion (mean) | 32.95 (highest in roster) | — | — |

**F-AXIS adjudication** (pre-registered in brief Section 4, frozen at brief SHA):
- F-AXIS #1 IS Sharpe: −0.6943 < +0.20 → **SPECIALIST-NEGATIVE FIRES** (1.19 below PROMISING-VALIDATED +0.50; 0.89 below PROMISING-TENTATIVE +0.20).
- IS trade-count floor: 158 ≥ 50 → CLEARED.
- F-AXIS #2 specialist_dispersion_mean: 32.95 > 30 → basin-lottery fingerprint METHODOLOGY-NEGATIVE.
- F-AXIS #3 OOS Sharpe: +0.6234 ≥ +0.40 with IS Δ = −1.32 (≫ +0.10 ceiling) → "Suspicious OOS-dominant lift" band — flags long-bias / regime-coincidence diagnostic per LM 7.4.
- Falsifier #1 per-direction Sharpe balance: SHORT 71 / LONG 87 IS (45% / 55% — balanced); SHORT 40 / LONG 44 OOS (48% / 52% — balanced). Neither direction dominates >70% — F-AXIS #1 verdict stands at face value (NOT a long-only mirage).

The verdict adjudication is mechanical. IS Sharpe missed the SPECIALIST-NEGATIVE band by 0.89; the falsifier ladder cleared without rescuing.

---

## 2. IS vs OOS Divergence — −0.69 IS vs +0.62 OOS (Δ = +1.32)

This is the largest IS/OOS divergence in the v1 catalog. It is **not** a sign-flip artefact — both numbers are mechanically computed on the same locked methodology, same 48-col `V1_FEATURE_COLUMNS_PRUNED`, same Model A wrapper. The sign reversal is **regime-driven**, not methodology-driven.

### 2.1 Per-direction × per-year decomposition (IS)

From `reports-v1/iteration_v1-076/in_sample/trades.csv`:

| Year | Dir | n | WR | Sum PnL% |
|---|---|---|---|---|
| 2022 (Q4) | SHORT | 8 | 37.5% | +0.66 |
| 2022 (Q4) | LONG | 9 | 22.2% | **−38.59** |
| 2023 | SHORT | 31 | 25.8% | **−42.99** |
| 2023 | LONG | 47 | 40.4% | +16.01 |
| 2024 | SHORT | 31 | 35.5% | −24.65 |
| 2024 | LONG | 25 | 40.0% | +2.68 |
| 2025 (Q1) | SHORT | 1 | 0.0% | −5.17 |
| 2025 (Q1) | LONG | 6 | 50.0% | +0.24 |

**IS totals**: SHORT 71 trades, WR 31.0%, sum **−72.15**; LONG 87 trades, WR 39.1%, sum **−19.65**.
Both directions lose in IS. Shorts are the dominant loser; longs bleed slowly. This is the fingerprint of a model that has **no clean direction** and which the dispersion 32.95 confirms — 50 inner seeds disagreed throughout.

### 2.2 Per-direction × per-year decomposition (OOS)

| Year | Dir | n | WR | Sum PnL% |
|---|---|---|---|---|
| 2025 (Q2–Q4) | SHORT | 26 | 38.5% | +2.24 |
| 2025 (Q2–Q4) | LONG | 26 | 34.6% | +5.01 |
| 2026 (Q1–Q2) | SHORT | 14 | **64.3%** | **+53.26** |
| 2026 (Q1–Q2) | LONG | 18 | 33.3% | −11.24 |

**OOS totals**: SHORT 40 trades, WR 47.5%, sum **+55.50**; LONG 44 trades, WR 34.1%, sum **−6.23**.
The OOS edge is **entirely concentrated in 2026Q1–Q2 shorts** (14 trades, 64.3% WR, +53.26% sum) — i.e. **17% of OOS trades carry essentially all of the OOS PnL**. The remaining 70 OOS trades net roughly flat.

### 2.3 Raw price regime per quarter (re-derived from `data/AAVEUSDT/8h.csv`)

**IS — whipsaw mean-reversion regime**: 2022Q4 −31.2% / 2023Q1 +43.8% / 2023Q2–Q3 ±5% / 2023Q4 +57.7% / 2024Q1 +17% / 2024Q2 −22.3% / 2024Q3 +60.0% / 2024Q4 +88.2% / 2025Q1 −40.3%.
Net IS close-to-close: 75.52 → 187.22 (+148%) — but the path is **4 alternating mean-reversion V-shape regimes**, not a single bull trend.

**OOS — terminal bear with one rally**: 2025Q1 −14.8% / 2025Q2 +65.7% / 2025Q3 +1.2% / 2025Q4 −46.4% / 2026Q1 −32.8% / 2026Q2 −24.1%.
Net OOS: 187.22 → 76.06 (−59.4%) — **secular downtrend after the single Q2 rally**, 5 of last 6 quarters monotone bear.

### 2.4 Mechanism — "chop-IS / trend-OOS, wrong-direction-bias rescued by accident"

- The model's IS feature stack leans on **vol-regime confirmation features** (`vol_atr_14` 9.84% gain, `interact_natr_x_adx` 5.53%, `trend_adx_14` 4.18%, `stat_kurtosis_20` 4.24% = combined 23.79% of split-budget) and **slow trend confirmations** (`trend_aroon_osc_50` 6.96%, `mom_macd_line_12_26_9` 5.29% = combined 12.25%). These features tell the model **WHEN volatility is high**, not which direction AAVE is going. In a high-vol asset (118% IS ann.), high-vol signals fire on nearly every candle → degenerate to noise.
- IS losses concentrate in **whipsaw quarters where the wrong-direction-bias was punished by mean-reversion** (2022Q4 longs −38.6 on the −31% drop; 2023 shorts −42.99 against secular up; 2024 mixed).
- OOS 2026Q1–Q2 is the first **monotone trend** in AAVE's history within the data window. The same wrong-direction-bias became right by coincidence: the model keeps shorting because it reads "high-vol, downtrending Aroon"; in 2026 that direction was actually correct because the bear was persistent.
- Net effect: IS −0.69 reflects the price regime (chop), not signal absence; OOS +0.62 reflects regime-tailwind, not signal presence.

The OOS lift is **regime-accidental, not signal-driven**. Per `feedback_v1_oos_inflation_empirically_confirmed.md` (HARD methodology lock established at /046), the IS-first gate is non-negotiable. The OOS edge being statistically real (σ_SR ≈ 0.155 at N=84 → +0.62 is ≈ 4σ above zero) does not promote a NEGATIVE-IS iteration to bundle-eligible.

---

## 3. Per-Regime Breakdown

`reports-v1/iteration_v1-076/in_sample/per_regime.csv` and `out_of_sample/per_regime.csv` both contain a single row with `regime="unknown"`:

| Window | regime | trades | wins | win_rate | net_pnl_pct | avg_pnl_pct | sharpe |
|---|---|---|---|---|---|---|---|
| IS | unknown | 158 | 56 | 35.4% | −91.80 | −0.581 | −0.077 |
| OOS | unknown | 84 | 34 | 40.5% | +49.27 | +0.587 | +0.075 |

**The regime tagger is structurally inactive for single-symbol cohort SPECIALIST runs** — cross-asset regime context cannot be computed when the dispatch universe is a single coin. This is a known limitation of the SPECIALIST architecture, not a /076 implementation defect. Per-regime decomposition for AAVE at this iteration is therefore reconstructed from raw price quarters (see Section 2.3 above) and per-direction × per-year trade aggregation (Sections 2.1 + 2.2).

The implicit per-regime story from quarterly tagging:
- **IS chop-whipsaw quarters (5 of 9 quarters)** — model bleeds in both directions. Net: shorts −72.15, longs −19.65.
- **IS trend-up quarters (2024Q3–Q4)** — partial recovery; longs +2.68 in 2024 net.
- **OOS chop-rally quarters (2025Q1–Q3)** — net roughly flat (shorts +2.24, longs +5.01 across 52 trades).
- **OOS monotone-bear quarters (2025Q4 → 2026Q2)** — shorts win by trend-coincidence (+53.26 on 14 trades, 64.3% WR).

---

## 4. Per-Month Breakdown

From `reports-v1/iteration_v1-076/in_sample/monthly_pnl.csv` and `out_of_sample/monthly_pnl.csv`:

### IS monthly PnL (28 months, Oct-2022 → Mar-2025)
- **Worst months**: 2022-10 (−18.04, 6 trades), 2024-04 (−12.10, 6 trades), 2023-01 (−10.16, 7 trades), 2025-02 (−10.23, 3 trades), 2023-10 (−8.53, 6 trades), 2024-09 (−8.09, 4 trades).
- **Best months**: 2023-11 (+15.13, 6 trades), 2024-07 (+8.52, 4 trades), 2024-10 (+8.19, 6 trades), 2024-11 (+6.78, 2 trades).
- **Monthly hit-rate**: 12 of 28 months profitable (43%). Median monthly PnL = −2.04%.
- **Trade-count distribution**: 5.6 trades/month mean, range [2, 9]. Consistent specialist cadence; no chunking.
- **No single month dominates IS losses** — the −43.48% IS net PnL is broadly distributed across 16 negative months. This is the loss footprint of a model **without clean direction**, not a model with a single catastrophic blow-up.

### OOS monthly PnL (15 months, Mar-2025 → Jun-2026)
- **Worst months**: 2025-05 (−11.39, 5 trades), 2025-04 (−6.54, 5 trades), 2025-09 (−4.74, 6 trades), 2025-07 (−4.73, 8 trades).
- **Best months**: 2025-12 (+10.51, 3 trades), 2025-08 (+7.80, 5 trades), 2026-05 (+6.65, 5 trades), 2026-06 (+6.52, 2 trades), 2026-04 (+4.13, 7 trades), 2026-03 (+3.18, 5 trades).
- **Monthly hit-rate**: 9 of 15 months profitable (60%). Median monthly PnL = +1.01%.
- **OOS lift concentration**: 2025-08 / 2025-12 / 2026-03 / 2026-04 / 2026-05 / 2026-06 = six months collectively +38.79 of the +16.26 net (i.e. the rest net −22.5). The lift is **plurality-spread**, not single-month, but six months of the 2026 secular bear carry it.

The OOS monthly hit-rate (60%) exceeds the IS monthly hit-rate (43%) by 17 percentage points — consistent with **a regime-tailwind rather than a stable edge**. A stable specialist would not show that much spread.

---

## 5. Hypothesis — AAVE as Regime-Specialist for the 2026Q1–Q2 Trend Regime?

The prompt poses the question: **is AAVE a regime-specialist for the current 2025–2026 regime, with IS evidence failing to validate?**

The answer per the v1 methodology lock is **NO — IS evidence does not validate the hypothesis**, and there is no path under the current per-symbol regime-specialist mandate that allows /076 to advance based on OOS evidence alone. Three independent reasons:

### 5.1 IS does NOT support the OOS hypothesis even as a directional precedent

If AAVE were a "monotone-bear-trend specialist", we would expect IS to show **strong short performance in IS bear quarters** (2022Q4 = −31% close; 2024Q2 = −22% close; 2025Q1 = −40% close). Actual IS data:
- 2022Q4 SHORT: 8 trades, WR 37.5%, sum **+0.66** — barely positive on a quarter where shorts should have feasted on a −31% drop.
- 2024Q2 + 2025Q1 SHORT: combined ~5 trades, sum negative.
- Even the directionally-correct IS quarters (where shorts should win) produce **flat-to-negative** short PnL.

The OOS short-trend lift in 2026Q1–Q2 is **not the same mechanism IS could have validated**. IS shorts lose −72.15 cumulative; OOS shorts win +55.50 cumulative. If the model had learned an actual "short-the-monotone-bear" rule, we would see at least directional consistency in IS bear quarters. We do not.

### 5.2 The OOS lift is concentration-fragile (LdP / Carver lens)

17% of OOS trades carry essentially all of OOS PnL (14 of 84 trades = +53.26 on shorts in 2026Q1–Q2). The remaining 70 trades net roughly flat. By the trade-rate-floor and concentration lenses:
- σ_SR at N=14 ≈ √(2/13) ≈ 0.39 → +0.6234 OOS Sharpe headline is mechanically ≤ 2σ from zero **when stripped to the load-bearing subset**.
- A single regime transition (2026Q3 chop resumption, or 2026Q3 bear reversal to rally) flips this from +0.62 to roughly 0.
- This is the **OOS-dominant-divergence-suspicious** signature of `feedback_v3_promising_mechanical_subtype` translated to v1 SPECIALIST: a one-regime tailwind, not a multi-regime edge.

### 5.3 Methodology lock per `feedback_v1_oos_inflation_empirically_confirmed`

Established at /046 from the /045 ALT_1 IS-only re-solve falsification: **OOS-aware composite scoring is empirically falsified**; any v1 partition-solve MUST use IS-only scoring. There is no exception path for "the OOS Sharpe is statistically meaningful" or "the regime might continue." The IS-first gate is HARD.

**Conclusion**: The "AAVE as 2025–2026 regime specialist" hypothesis is **plausible as a narrative** but **not validated by IS evidence** and **methodologically barred from advancing on OOS evidence alone**. The hypothesis remains structurally testable only via a per-symbol methodology-bit change at /AAVE-2 (see Path Forward in the diary).

---

## 6. What This Iteration Confirms About v1 SPECIALIST Architecture

1. **NEW SYMBOL universe-extension at LOCKED methodology can produce sharp IS failures** even on symbols that pass the NEGATIVE-pooled-baseline mine-phase gate (AAVE TS-mom IS Sharpe was negative — the structural DOT/063 precondition). The 48-col `V1_FEATURE_COLUMNS_PRUNED` stack inherited from DOT/063 is **not symbol-portable**.
2. **Specialist dispersion mean is a real-time canary**: AAVE dispersion 32.95 is the highest in roster (DOT/063 ~25, BTC/065 ~28). When dispersion stays > 30 for 60%+ of walk-forward observations (per `feedback_v1_basin_lottery_vigilance`), the IS Sharpe estimate is structurally noisy — even if it had landed in the PROMISING band, the 1σ downgrade would have been mandated.
3. **Direction-asymmetric LM 7.4 diagnostics are essential**: per-direction × per-year Sharpe tables (Sections 2.1 + 2.2) carry diagnostic information that the headline Sharpe + headline DD cannot express. Future NEW SYMBOL closeouts should make this table mandatory in the eval memo, not optional.
4. **IS/OOS sign reversal does NOT imply look-ahead leakage**. Check 1 (Look-Ahead Audit) PASS in Phase 7.5 review (`briefs-v1/iteration_v1-076/review.md` lines 13-14) — foundation `walk_forward.py:113` carries the embargo subtraction; no /076 commits touched the foundation. The sign reversal is regime-coincidence, not contamination.

---

## 7. Cross-Reference

- Critic review verdict + 14-check status: `briefs-v1/iteration_v1-076/review.md`
- LM Master Phase 7.4 post-mortem (full mechanism diagnosis): `briefs-v1/iteration_v1-076/lgbm_advisor.md` (Phase 7.4 appendix, lines 156-311)
- LM Master Phase 4.5 pre-design (calibration record): `briefs-v1/iteration_v1-076/lgbm_advisor.md` (lines 1-153)
- Per-trade rosters: `reports-v1/iteration_v1-076/in_sample/trades.csv` (158 rows), `out_of_sample/trades.csv` (84 rows)
- Feature importance: `reports-v1/iteration_v1-076/in_sample/feature_importance_Model_A_AAVE_specialist_076.csv`
- Specialist dispersion timeseries: `reports-v1/iteration_v1-076/in_sample/specialist_dispersion.csv`
