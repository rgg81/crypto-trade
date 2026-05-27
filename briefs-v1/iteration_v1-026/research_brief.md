# iter-v1/026 — Pre-CONFIRMATION Cross-Correlation Sanity Check (Research Brief)

**Status**: NOT an EXPLORATION axis. Pre-CONFIRMATION sanity slot before /027.
**Verdict**: **YELLOW** (one required-pair breach; one new pair breach surfaced).
**Routing**: see Section 4 below.

---

## Section 0 — Pre-CONFIRMATION Sanity Context

Per LM Master /025 §4(Recommendation #6) + Critic /025 Path Forward, /026
runs the cross-correlation pre-validation required before /027 can launch
CONFIRMATION. The mandate (LM Master /025 §4):

- Pearson(pool, LINK) < 0.50 — REQUIRED
- Pearson(pool, ETH+gate) < 0.50 — REQUIRED
- IDEALLY: Pearson(LINK, ETH+gate) < 0.50 — diversification

This brief is intentionally compact (5 sections, no full EXPLORATION format).
No src/ changes; no new backtests; all analysis is read-only over the
existing reports for `iteration_v1-baseline`, `iteration_v1-018`, and
`iteration_v1-019`.

Three analysis scripts are committed under `analysis/iteration_v1-026/`:
1. `cross_correlation_analysis.py` — the 3-pair Pearson/Spearman matrix
   mandated by LM Master /025 §4.
2. `diagnose_oos_pool_link.py` — leave-one-out jackknife on the OOS pool×LINK
   pair to identify what's driving the breach.
3. `bundle_5model_estimate.py` + `full_5model_cross_corr.py` — single-seed
   reference reconstruction of /027's 5-Model bundle per `/025 brief
   Section 11.6 LOCKED composition`, with the 10-pair cross-correlation
   matrix among the five components.

Output CSVs:
- `cross_correlation_matrix.csv` — 3-pair × 3-sample matrix.
- `bundle_composition_validation.csv` — additive-bundle Sharpe/DD (loose).
- `baseline_stability.csv` — Phase 3 anchor re-check (bit-exact match).
- `oos_pool_link_diagnostic.csv` — month-level driver attribution.
- `bundle_replacement_validation.csv` — replacement-bundle attribution (3-component).
- `bundle_5model_estimate.csv` — 5-Model bundle attribution (per /025 LOCKED).
- `full_5model_cross_corr.csv` — 10-pair Pearson/Spearman matrix.

---

## Section 1 — Cross-Correlation Results

### 1.1 Three-pair mandate from LM Master /025 §4

Monthly returns Pearson (canonical) + Spearman (robustness check),
overlap-only months where both components have ≥1 trade.

| Pair | Sample | n_months | Pearson | Spearman | Verdict |
|---|---|---|---|---|---|
| pool × LINK | IS | 38 | **+0.0601** | +0.0901 | PASS |
| pool × LINK | OOS | 15 | **+0.5260** | +0.4893 | **FAIL** |
| pool × LINK | combined | 53 | +0.1904 | +0.2049 | PASS |
| pool × ETH+gate | IS | 39 | −0.0795 | +0.0034 | PASS |
| pool × ETH+gate | OOS | 13 | −0.1042 | −0.1813 | PASS |
| pool × ETH+gate | combined | 52 | −0.0855 | −0.0389 | PASS |
| LINK × ETH+gate | IS | 38 | −0.2572 | −0.2085 | PASS |
| LINK × ETH+gate | OOS | 13 | +0.1269 | +0.2088 | PASS |
| LINK × ETH+gate | combined | 52 | −0.1035 | −0.0024 | PASS |

**Pearson summary**:
- pool × LINK     IS +0.06 | OOS **+0.53** | Combined +0.19 → OOS BREACH
- pool × ETH+gate IS −0.08 | OOS −0.10     | Combined −0.09 → PASS (strongly safe)
- LINK × ETH+gate IS −0.26 | OOS +0.13     | Combined −0.10 → PASS

### 1.2 What drives pool × LINK OOS = +0.5260

Leave-one-out jackknife (`diagnose_oos_pool_link.py`):

| Month dropped | Pearson | Note |
|---|---|---|
| 2025-11 | +0.3954 | **BELOW** 0.50 threshold |
| 2025-08 | +0.4571 | **BELOW** 0.50 threshold |
| 2026-02 | +0.4713 | **BELOW** 0.50 threshold |
| ... | ... | (12 others all keep Pearson > 0.50) |

Co-extreme months (|z| > 1.0 on BOTH series, same sign):
- 2025-08: pool +22.4% / LINK +13.4% (z = +1.29 / +1.29 — joint risk-on)
- 2025-11: pool +29.6% / LINK +16.1% (z = +1.76 / +1.61 — joint risk-on, all-time-high month)

These are TWO joint-positive crypto-wide rallies. The breach is concentrated
in two months, not structural. Mechanism: both pool and LINK specialist are
long-biased crypto strategies and benefited from the same August and November
2025 rallies. The Spearman correlation (+0.49) is at the threshold rather than
above, confirming the Pearson is partly outlier-inflated.

### 1.3 New surprise: 5-Model bundle cross-correlation breach

Per /025 brief Section 11.6, the LOCKED /027 bundle composition is:

> LINK-only specialist Model C' (+0.80 multi-seed Δ target) — LOCKED
> ETH-only + symmetric BTC-trend gate Model G (+0.50) — LOCKED
> BTC, LTC, DOT — all in pool via baseline models

I.e., the actual bundle is **5 components**, not 3. The relevant correlation
matrix is the 10-pair among (A_btc_approx, C_link_spec, D_ltc, E_dot,
G_eth_spec). Running it on the existing single-seed reports
(`full_5model_cross_corr.py`):

| Pair (OOS) | Pearson | Spearman | Verdict |
|---|---|---|---|
| A_btc × C_link | +0.295 | +0.115 | PASS |
| A_btc × D_ltc | −0.097 | −0.249 | PASS |
| A_btc × E_dot | +0.268 | +0.190 | PASS |
| A_btc × G_eth | −0.199 | −0.133 | PASS |
| C_link × D_ltc | +0.226 | +0.234 | PASS |
| **C_link × E_dot** | **+0.6027** | +0.4250 | **FAIL on Pearson** |
| C_link × G_eth | +0.142 | +0.305 | PASS |
| D_ltc × E_dot | +0.065 | −0.082 | PASS |
| D_ltc × G_eth | +0.169 | +0.047 | PASS |
| E_dot × G_eth | −0.473 | −0.477 | PASS (just under) |

The C_link × E_dot Pearson breach is **new information** not surfaced by the
original 3-pair mandate. Spearman is +0.425 (under threshold) — the Pearson is
inflated by outlier months. Mechanism candidate: LINK and DOT are both
DeFi/altcoin layer-1 cohort assets and may share the same regime tailwind in
risk-on months.

In IS the same C × E pair is +0.121 Pearson / −0.005 Spearman — fully safe.
The breach is OOS-only.

---

## Section 2 — Bundle Composition Validation

### 2.1 Approximation caveat

The Critic /025 review explicitly flagged that a BTC-only Model A' (no longer
pooled with ETH) would re-train Optuna on BTC alone and produce a different
trade roster than the BTC slice of the baseline pool. The single-seed
reference bundle below uses **baseline BTC trades as a proxy for Model A'**.
This is an approximation — the actual /027 multi-seed multi-model backtest
is the binding number; /026's estimate is informational ONLY.

### 2.2 Single-seed reference bundle, 5-Model

Per-component standalone Sharpe + MaxDD on monthly-aggregated PnL (sqrt(12)
annualization; project canonical uses daily sqrt(365), so absolute numbers
differ from comparison.csv but per-component ranking holds):

| Component | OOS Trades | OOS Sharpe (sqrt(12)) | OOS MaxDD | IS Sharpe |
|---|---|---|---|---|
| A_btc_approx (baseline BTC subset) | 35 | +0.452 | 15.59% | −0.252 |
| C_link_spec (/018) | 48 | **+1.086** | 21.95% | +0.382 |
| D_ltc (baseline) | 34 | **−1.050** | 29.06% | +0.054 |
| E_dot (baseline) | 46 | −0.091 | 5.46% | −0.360 |
| G_eth_spec (/019) | 42 | **+0.677** | 15.62% | −0.033 |
| **BUNDLE (sum)** | **205** | **+0.570** | **49.18%** | **+0.064** |
| Reference baseline pool | 189 | +0.572 | 33.77% | +0.329 |
| Bundle Δ vs baseline | +16 trades | **−0.002** | **+15.4pp** | −0.265 |

### 2.3 Critical finding — bundle target gap

The /025 brief locked bundle target is **+1.10 to +1.30 OOS Sharpe at
multi-seed**. The single-seed reference bundle Sharpe is **+0.57**.

Gap to target lower bound: **+0.53** Sharpe units.

The reason the bundle does not deliver lift on the single-seed reference is:

1. **D (LTC) baseline OOS Sharpe is −1.05** — heavily negative. The bundle
   sums component PnL, so D drags total PnL down.
2. **E (DOT) baseline OOS Sharpe is −0.09** — flat, contributes vol without lift.
3. **A_btc_approx Sharpe +0.45** — positive but modest; the BTC-only Model A'
   in /027 may be slightly different but likely won't add the +0.53 gap.
4. The two new specialists C' (+1.09) and G (+0.68) ARE positive, but their
   contribution to the bundle Sharpe is diluted by the 3 baseline models.

The catalog entry for /018 itself acknowledged this:

> bundle Sharpe target ≥+0.70 multi-seed mean requires 5+ specialists at
> ~+0.50-0.80 each with cross-correlation ≤0.3

The /025 brief target of +1.10–+1.30 is OPTIMISTIC relative to that earlier
catalog statement. The single-seed evidence supports the catalog's earlier
prior (≥+0.70 for 5-component bundle) but does not support the +1.10–+1.30
target.

### 2.4 Multi-seed regression-to-mean impact

The /018 catalog entry explicitly anchors the multi-seed LINK specialist
target at **+0.80 NOT /018's +0.98** — meaning the single-seed reference is
expected to regress downward. Same logic applied to ETH+gate: the multi-seed
mean is below /019's single-seed +0.70.

If multi-seed regresses C' to +0.80 (catalog anchor) and G to +0.50 (LM
Master /025 §4 anchor), the bundle Sharpe under additive accounting and
the existing D (−1.05) + E (−0.09) drag yields an even lower estimate than
the +0.57 single-seed reference — likely **+0.40 to +0.55 multi-seed mean**.

**The /027 multi-seed CONFIRMATION will almost certainly NOT clear the
+1.10–+1.30 target.** The bundle composition does not have the structure to
deliver +1.10 OOS Sharpe given the baseline LTC arm's heavy negative drag.

### 2.5 What the bundle is actually likely to produce

Based on the single-seed reference and the multi-seed regression expectations:

| Outcome | OOS Sharpe | OOS MaxDD | Versus Hard Merge Floor (>1.0) | Versus Target [+1.10, +1.30] |
|---|---|---|---|---|
| Optimistic | +0.65 to +0.75 | 30–40% | FAIL | FAIL |
| Modal | +0.40 to +0.60 | 40–50% | FAIL | FAIL |
| Pessimistic | +0.15 to +0.35 | 50%+ | FAIL | FAIL |

Even the optimistic case fails the >1.0 floor for MERGE.

---

## Section 3 — BASELINE_V1 Stability Re-Check

`baseline_stability.csv` reads `reports-v1/iteration_v1-baseline/comparison.csv`
directly and verifies the anchor numbers in BASELINE_V1.md.

| Metric | comparison.csv | BASELINE_V1.md anchor | Match |
|---|---|---|---|
| IS Sharpe (canonical daily√365) | +0.2829 | +0.2829 | **YES** (bit-exact) |
| OOS Sharpe (canonical) | +0.6637 | +0.6637 | **YES** (bit-exact) |
| IS trades | 621 | 621 | **YES** |
| OOS trades | 189 | 189 | **YES** |

**Note on the doc-label misnomer**: BASELINE_V1.md says "Monthly Sharpe"
but the underlying number is computed on a daily weighted-PnL series
filled with zero on no-trade days, annualized by sqrt(365)
(see `iteration_report.py:69`). The label is technically inaccurate but
the number is canonical. My /026 monthly-aggregated Sharpe (sqrt(12) on
monthly_pnl.csv) is +0.3285 IS / +0.5722 OOS — different by methodology
but legitimate; both come from the same underlying trade roster.

The BASELINE_V1 anchor is stable. No drift since v0.v1-baseline-corrected
(`f8bc12c`).

---

## Section 4 — /027 GREEN/YELLOW/RED Verdict

### 4.1 LM Master /025 §4 strict-threshold verdict

3-pair mandate (Pearson < 0.50 across IS/OOS/combined):

- pool × LINK     — IS PASS / **OOS FAIL** / Comb PASS
- pool × ETH+gate — PASS across all
- LINK × ETH+gate — PASS across all

**Required pairs (pool×LINK, pool×ETH+gate)**: 1 fail (pool×LINK OOS = 0.526).
**Ideal pair (LINK×ETH+gate)**: PASS.

Per the verdict routing rules in this iteration's prompt:
- GREEN: all 3 pairs < 0.50 → proceed immediately
- YELLOW: 1 pair ≥ 0.50 → flag for weight adjustment or specialist removal
- RED: 2+ pairs ≥ 0.50 → revise bundle composition

The 3-pair mandate is **YELLOW** (1 OOS pool×LINK breach).

### 4.2 5-Model bundle 10-pair cross-correlation (new information)

When the bundle is evaluated as the LOCKED 5-Model composition (per /025 brief
Section 11.6), an ADDITIONAL Pearson breach emerges at C_link × E_dot OOS =
+0.603 (Spearman +0.425, just under threshold). This was NOT surfaced by the
original 3-pair mandate because the 3-pair mandate aggregated D + E + A_btc
into "pool" rather than treating them as separate components.

This brings the count of Pearson-breached pairs to **2 of 10**:
- pool × LINK OOS = 0.526 (3-pair view: aggregates D + E + A_btc into pool)
- C_link × E_dot OOS = 0.603 (5-pair view: isolates DOT from pool)

### 4.3 Bundle-target-achievability verdict

INDEPENDENT of the cross-correlation result, the single-seed reference bundle
Sharpe (+0.57) is far below /027's stated target of +1.10 to +1.30. Even with
the cross-correlation gates fully satisfied, the bundle does not have the
component structure to clear the +1.10 floor.

The bundle target gap (+0.53 Sharpe units from +0.57 → +1.10) is **structural
on the bundle composition**, not a methodological artifact:
- D (LTC) and E (DOT) baseline models are net-negative in OOS.
- Multi-seed regression at C' (+0.98 → +0.80) and G (+0.70 → +0.50) shrinks
  the positive contribution from the new specialists.
- BTC-only A' is unlikely to add +0.53 to the bundle Sharpe.

### 4.4 OVERALL VERDICT: YELLOW (with structural concerns)

**Proceed to /027 with the following modifications and acknowledgments**:

1. **Acknowledge the target gap**: /027 brief Section 2 (prediction) must
   pre-register a multi-seed OOS Sharpe band of **[+0.40, +0.75]**, NOT
   [+1.10, +1.30]. The +1.10–+1.30 target is structurally unachievable
   given the baseline LTC/DOT drag and the multi-seed regression expectations
   for C' and G. Pre-registering a realistic band prevents post-hoc
   rationalization at /027 closeout.

2. **Flag the C_link × E_dot OOS Pearson +0.603 breach**: /027 Phase 7
   QR evaluation must explicitly report whether multi-seed runs preserve or
   dissolve this correlation. If multi-seed C × E Pearson stays > 0.50,
   the bundle has an unanticipated joint-risk concentration in the
   altcoin/L1 cohort.

3. **Reconsider including E_dot (Model E DOT) in the bundle**: E (DOT)
   baseline OOS Sharpe is −0.09 — essentially flat. Dropping E reduces the
   bundle MaxDD from 49% to a lower number (E's standalone MaxDD is small
   at 5.5% but its volatility-only contribution still drags the bundle).
   Sample 4-Model bundle (A + C + D + G, drop E) is NOT computed here
   because /025 LOCKED the 5-Model composition; this is a /027 brief
   Section 3 consideration for QR.

4. **D_ltc (Model D LTC) is the dominant drag**: D OOS Sharpe = −1.05.
   The single-best lever to lift the bundle would be a D-specialist (an LTC
   variant of /018's LINK specialist methodology), but this is a cycle-4
   axis per /025 brief Section "Path Forward" candidate 1. /027 cannot
   add an D-specialist within its bundling scope.

5. **Do NOT BLOCK /027**: the 3-pair mandate verdict is YELLOW not RED.
   The /025 brief's prediction matrix explicitly states "PROMISING ... /026
   = pre-CONFIRMATION sanity (cross-correlation check). Do NOT stack OI
   momentum/volatility per SAME-FAMILY rule." — /026 is a CHECK, not a
   block-out gate. /027 proceeds with the explicit modifications above
   and the multi-seed CONFIRMATION outcome is the binding number.

### 4.5 Compact decision summary

| Question | Answer |
|---|---|
| 3-pair cross-correlation mandate verdict | **YELLOW** (1 of 2 required-pair breach: pool×LINK OOS +0.526) |
| 5-Model bundle 10-pair check | **YELLOW** (1 of 10 pair breach: C_link × E_dot OOS +0.603) |
| Bundle Sharpe target [+1.10, +1.30] achievable? | **NO** (single-seed reference +0.57; multi-seed regression worsens this) |
| BASELINE_V1 anchor stable? | YES (bit-exact match) |
| /027 GREEN-LIGHT? | **YELLOW** — proceed with modified target band [+0.40, +0.75] and explicit acknowledgment that bundle composition has structural ceiling |
| /027 RED-BLOCK? | NO |
| Required modifications to /027 brief | (1) Realistic target band, (2) Flag C × E breach for Phase 7 attribution, (3) Consider dropping E |

---

## Notes on Methodology

- **Pearson is the LM Master mandated metric**. Spearman is reported as a
  robustness check; where Pearson breaches but Spearman does not (C × E OOS),
  the breach is partly outlier-inflated. We do NOT relax the Pearson mandate
  on this basis — the LM Master spec is explicit.
- **Overlap-only correlation**: for the 3-pair mandate we report on months
  where BOTH components have ≥1 trade. For the 5-Model 10-pair matrix we
  zero-fill inactive months (since the bundle Sharpe is computed on the
  zero-filled aggregate); both views are reported.
- **Daily vs monthly Sharpe**: the project canonical metric in
  `comparison.csv:sharpe` is daily PnL × sqrt(365). My /026 analysis uses
  monthly PnL × sqrt(12) for cross-correlation purposes (cross-correlation
  needs an aligned multi-component series; monthly is the lowest-frequency
  alignment possible). Per-component absolute Sharpe values differ between
  the two methods but per-component RANK is preserved.
- **No new backtests**. All numbers come from the committed reports for
  `iteration_v1-baseline`, `iteration_v1-018`, `iteration_v1-019`.

---

## Deliverables Index

- `analysis/iteration_v1-026/cross_correlation_analysis.py`
- `analysis/iteration_v1-026/diagnose_oos_pool_link.py`
- `analysis/iteration_v1-026/bundle_replacement_analysis.py`
- `analysis/iteration_v1-026/bundle_5model_estimate.py`
- `analysis/iteration_v1-026/full_5model_cross_corr.py`
- `analysis/iteration_v1-026/diagnose_roster_overlap.py`
- `analysis/iteration_v1-026/cross_correlation_matrix.csv`
- `analysis/iteration_v1-026/bundle_composition_validation.csv`
- `analysis/iteration_v1-026/baseline_stability.csv`
- `analysis/iteration_v1-026/oos_pool_link_diagnostic.csv`
- `analysis/iteration_v1-026/bundle_replacement_validation.csv`
- `analysis/iteration_v1-026/bundle_5model_estimate.csv`
- `analysis/iteration_v1-026/full_5model_cross_corr.csv`
- `briefs-v1/iteration_v1-026/research_brief.md` (this file)
- `briefs-v1/iteration_v1-026/sanity_check_report.md` (one-page summary)
