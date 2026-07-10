# EXPLORATION-A2 — Engineering Report (QE, Phase 6)

**Date:** 2026-07-10 · **Role:** Quant Engineer · **Track:** baseline-BLIND MARKET-NEUTRAL (MN)
**Contract:** `briefs-portfolio-mn/EXPLORATION-A2.md` (frozen 2026-07-10, 85bbe30f) **plus the
Critic pre-flight conditions C1–C4** (`diary-portfolio-mn/REVIEW-A2-preflight.md`, additive
instrumentation only) — implemented exactly as frozen; no parameter adjusted, no phase selected,
no re-run after seeing results.
**Script:** `analysis/portfolio/mn_exploration_a2.py` (single frozen results pass; matrix run
twice only for the pre-registered bit-identity check). **Engine extension:** `blind_engine.py`
`beta_neutralize` (brief §7, sanctioned; opt-in, inert-default byte-identical).
**Tests:** `tests/test_mn_exploration_a2.py` (13 new; full suite **99 = 55 blind + 21 mn +
10 EXPL-A + 13 new, ALL GREEN**; the DIAG-A funding-sort leak control carries in the EXPL-A
suite). **NOT committed** (per dispatch; `analysis/` is gitignored in this worktree).
**Hardware / wall-clock:** same host as EXPLORATION-A (i9-12900HK, 20 threads, 58 GB) — full
matrix (84 result runs × 2 passes + per-tranche funding/universes/betas recomputed per pass)
≈ **9 min**; targeted G3 localization forensic ≈ 4 min.

**Blinding/IS:** `mn_panel_health()` first (OK; BTC grid T=7147 contiguous; live feeds current).
Panel sliced via `mn_slice_is` (T=6576, C=747, 2020-01-01 → 2025-12-31); `mn_guard_grid` passed
on the IS grid AND on every tranche grid (both passes). Old-track `is_mask`/`OOS_CUTOFF`/
`slice_is` never touched. **No holdout candle touched; `confirmation_reveal` never passed.**
No baseline artifact read. EXPLORATION-A Cell-1/Cell-3 comparators CITED from
`EXPLORATION-A-engineering.md`, never re-run.

**ENGINEER SCOPE:** observed values only. Gate PASS/FAIL, tiers, the §3.1 both-ways
interpretation, and the §5 decision map are the QR's Phase-7 calls. The §3.1 bin is printed as a
MECHANICAL bin (frozen thresholds applied arithmetically), not a verdict. Verdict cells blank.

---

## 1. What was built (work item 1 — the `beta_neutralize` engine extension)

`blind_engine.run_backtest` gained one **opt-in** parameter, `beta_neutralize: (T,C) | None`
(default `None` = byte-identical, no FP op added to the legacy loop), plus the module function
`apply_beta_neutralization(w_raw, beta_row, member_mask, gross)` implementing brief §1.5/§1.6
steps 3–5 exactly:

- **Projection:** on M = universe[k−1] ∩ finite signal[k−1] ∩ valid fill price at open[k] ∩
  finite β[k−1], `w_proj = w_raw − Aᵀ(AAᵀ)⁻¹(A·w_raw)` with `A = [1…1; β_M]`, (AAᵀ) inverted in
  closed form — minimal-L2, zeroes Σw AND Σw·β exactly. **Feasibility (min_members) counts |M|**
  per §1.6 steps 1–2 when the extension is on (legacy predicate untouched when off). Observed
  effect of the predicate change: **nil** — β rows are all-or-nothing finite (0 partial rows),
  and A2-1 / A2-N20 infeasible counts (571 / 352 per 21 tranches) are IDENTICAL to EXPLORATION-A
  Cell-1/Cell-3's revealed counts.
- **Degenerate-β fallback** (see anomaly note b — the frozen inequality is self-referential as
  written; implemented as the numerically-stable equivalent its own required unit test pins):
  keep w_raw, count in `n_beta_degenerate_rebal`.
- **Projection-collapse guard:** Σ|w_proj| < 0.10·g → rebal treated as INFEASIBLE (skip, hold
  previous weights), counted in `n_projection_collapse_rebal`.
- **Rescale to gross** (positive scalar; both constraints preserved), then the frozen
  **per-name cap LAST** (unchanged `apply_weight_cap` code path); the **post-cap target-β
  residual is MEASURED per rebal** (`bn_post_cap_target_beta`), never asserted zero.
- **Forensics** (inert-empty when off): per-rebal `bn_status` (projected/degenerate/collapse),
  `bn_prerescale_gross` (C1), `bn_rho_spearman` + `bn_sign_flips` (projection distortion),
  `bn_post_cap_target_beta`; scalar metrics incl. `bn_postproj_target_beta_max` and
  `bn_dropped_nonmember_gross_max`.

**Tests (13 new):** inert-default byte-identity (×2 weighting modes, alongside cap+min_members;
forensic arrays empty when off); corrupt-future-β positive control (β consumed at [k−1]:
weights[:t0+1] bit-identical, future changed, non-vacuous); projection correctness on synthetic
(|Σw| ≤ 1e-12 AND |Σw·β| ≤ 1e-12 pre- and post-rescale; closed-form reference match at 1e-12;
scalar-rescale preservation); projection correctness on a NON-dollar-neutral input (force-exit
case: both constraints still zeroed); minimal-distortion (w_proj − w_raw ∈ row-space(A),
residual ≤ 1e-12); degenerate fallback (module: constant β → w unchanged bitwise, flag set;
engine: constant-β panel run byte-identical to the plain run with the degenerate counter firing
at every executed rebal); collapse guard (module: w_raw ∈ row-space(A) → collapse, input
unchanged; engine: skip/hold-previous semantics, counter, resume); cap-after-projection ordering
(pre-cap target β ≤ 1e-12; Σw=0 preserved post-cap at every LEG-FEASIBLE rebal; post-cap β
REPORTED nonzero when the cap binds — non-vacuous); **cap leg-infeasibility semantics** (the
frozen cap DROPS excess when a projected leg exceeds its same-leg capacity → Σw≠0; documented,
counted in the run — see anomaly d); engine-level uncapped semantics (Σw=0, Σ|w|=gross,
Σw·β[k−1]=0 at every executed rebal to 1e-12). Pre-existing suites untouched and green.

## 2. Run protocol confirmations (top-of-script hard order)

| Check | Result |
|---|---|
| `mn_panel_health()` first | OK (grid contiguous; feeds current) |
| IS slice + `mn_guard_grid` + last-candle extent | PASS (T=6576, ends 2025-12-31) |
| Sign pin `signal_engine = -build_signal(fund, univ)` | PASS (element-for-element, NaNs incl.) |
| Funding coverage (floored top-40 ever-members) | complete (745/747 direct, 2 non-members missing) |
| Regime occupancy (frozen rules) | CRASH 11.5% / MANIA 15.7% / CHOP 72.7% — matches DIAG-A |
| Leak positive control | corrupt fund[3288:,:] → signal[:3288] bit-identical; future changed |
| β_BTC first all-finite row (derived) | **135**; partially-finite rows: **0** (all-or-nothing) |
| First row ≥ N/2 feasible members (derived) | **N40: 585 (2020-07-14) → first live rebal k=588; N20: 360 → k=378** — see anomaly a |
| Scoring mask | **PINNED to the EXPLORATION-A common mask: first-True=293** (2020-04-07), contiguous [293, 6574], n_common=6282; IDENTICAL across both cells and both cost tiers (asserted per cell/tier); COVID March-2020 outside |
| Members/candle N=40 | before floor 36.6 → after floor 36.1 (min 0, p5 8) — identical to EXPL-A |
| Betas | `rolling_beta` (BTC only) computed per tranche; no ETH-residual chain (dropped with the overlay) |

## 3. Internal reproducibility (brief §7 pins)

| Pin | Result |
|---|---|
| **Bit-identical re-run** (full matrix from scratch incl. funding/universes/betas) | PASS — mapped rets/turnover/funding/per-name P&L + b_model + ALL projection forensics + counters bit-identical |
| **Leg reconciliation** price − tcost − funding ≡ rets, all 84 runs × 2 passes | max **1.11e-16** (≤1e-12) PASS |
| **`beta_neutralize=None` inert control** (p=0 config vs plain engine call) | **BYTE-IDENTICAL** (assert_array_equal on rets/turnover/weights/funding_rets) PASS |
| **IS-guard on every tranche grid** | PASS (both passes) |
| **Ensemble leg reconciliation** (per cell/tier) | ≤1e-12 asserted, PASS |
| **Ground-truth 2× vs analytic twin** (cross-check only, never asserted) | a2_1 max elementwise drift **2.91e-04** (expected ~2.6e-4, stateless); a2_n20 **5.78e-04**; analytic ens 2× Sharpe +1.4618 vs GT +1.4619 (a2_1) |

## 4. TABLE 1 — Headline per cell (1×; pinned common slice [293, 6574]; PPY=1095)

| cell | Sharpe | fundSh (uncosted) | fundSh (costed) | 2×Sh (GROUND TRUTH) | ann vol | maxDD | turn/yr | ann ret | mo win | top-name share |
|---|---|---|---|---|---|---|---|---|---|---|
| **A2-1 (PRIMARY)** | **+1.6784** | +16.280 | +12.488 | **+1.4619** | 18.80% | **−25.57%** | 54.3× | +34.72% | 55.1% | 13.2% (SOL) |
| A2-N20 | +1.5880 | +11.410 | +8.420 | +1.4129 | 25.11% | −31.57% | 58.6× | +44.42% | 58.0% | 11.1% (BNB) |

Turnover cross-check (full-array (1/21)ΣT_p^ann): 52.0× / 56.1× — consistent.
**Informational** — A2-1 on the native fully-live window [608, 6574] (excluding the ~292 flat
pre-live candles BOTH A2 and the revealed Cell-1 share inside the pinned mask): Sharpe
**+1.7307** (n=5967). Headline stays the pinned 293 mask.

## 5. TABLE 2 — Neutrality panel (C5 mechanics) + C3 decomposition

**A2-1 (PRIMARY):**
- rolling-270 β_BTC: **within |β|≤0.10 on 97.0%** of 6148 defined candles; **max |β| = 0.1813**
  [G1a: ≥95% AND max ≤0.20 (H)] — vs Cell-1 revealed 96.0% / 0.1769
- rolling-270 β_ETH: within 100.0%; max 0.0957 [G1b (H)] — vs Cell-1 100.0% / 0.1016
- full-slice OLS: β_BTC = −0.0133 (se 0.0041); β_ETH = −0.0116 (se 0.0031); mean rolling β_BTC = −0.0218
- **CRASH n=658: β_BTC = +0.0088 (se 0.0087)** [G2 (H)] — mean +1.13 bps/cd (+1.027%/mo), t = +0.54, P&L share +4.1%
- MANIA n=999: β_BTC = −0.0153 (se 0.0098) [G2 (H)] — mean +4.53 bps/cd (+4.133%/mo), t = +2.22, share +25.0%
- CHOP n=4625: β_BTC = −0.0212 (se 0.0053) — mean +2.78 bps/cd (+2.534%/mo), t = +3.40, **share +70.9%** [G5 ≤60% (S)]
- worst-bucket t = **+0.54** (CRASH) [G4: t > −1.0 (H)]

**A2-N20 (robustness, informational):** β_BTC within 94.3%, max 0.2087; β_ETH within 99.4%, max
0.1675; CRASH β −0.0098; MANIA β −0.0147; CHOP share 85.8%; worst t +0.49.

**C3 decomposition of the realized rolling β_BTC (Critic condition; A2-1):**
- (a) projection-target component: max |post-projection pre-cap target β| = **4.30e-15** (zero by construction).
- (b) cap-residual proper (post-cap target Σw·β at rebal, in-window): mean|·| **0.0000**, max|·| **0.0058**.
- (b′) rolling-270 mean of the model-implied held-book β (cap-residual + intra-hold drift): mean +0.0014, max|·| 0.0160.
- (c) estimation residual (realized − model): mean −0.0232, max|·| **0.1782**.
- At the G1a max-|realized-β| candle (2025-09-21): realized **−0.1813 = model −0.0032 +
  estimation −0.1781** — the realized-β excursions are ~entirely **trailing-β-estimation error**,
  not cap residual (the thin-G1a adjudication input the Critic asked for).

## 6. TABLE 3 — G3 + projection / cap / floor / infeasibility forensics (1× runs)

| cell | G3 REBAL-row max | G3 executed-target max | G3 ALL-candle max | % candles >0.10 | cap bind | capDrop | degen | collapse | n_infeasible | infeas % | live rebals min/mean | names |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A2-1** | **0.0699** | **2.96e-15** | **0.2624** | 0.41% | 1.3% | **0** | 0 | 0 | 571 | 8.7% | 285/285 | 352 |
| A2-N20 | **0.1111** | **1.11e-01** | 0.6014 | 1.42% | **78.2%** | **14** | 0 | 0 | 352 | 5.4% | 295/296 | 255 |

- A2-1 post-cap target-β residual in-window: mean|·| 0.0000 / max|·| 0.0058; dropped-nonmember
  gross ≡ 0. A2-N20: mean|·| 0.0044 / **max|·| 0.1467** (cap binds 78.2% of rebals at N20).
- Comparators (revealed, cited): Cell-1 G3 0.2365 (hedge leg), Cell-3 G3 0.1080 (fresh-target
  force-exit). A2-1 G3reb 0.0699 = **0.30× Cell-1, 0.65× Cell-3.**

**TABLE 3b — C2 p=0 G3 forensic (A2-1, 1×), THE §5 discriminator:**
- Executed rebal rows in-window: 286; **max |Σw_target| = 2.03e-15** — the projection makes the
  REBAL-TARGET dollar-neutral to FP precision at every executed rebal ("Σw_target ≡ 0 at rebal"
  verified).
- Skipped rebal rows in-window with a live book (p=0): 0.
- ALL-candle |Σw|/gross (n=5987): p50 0.0104, p90 0.0366, p99 0.0764, **max 0.2220**, frac>0.10
  = 0.33%.
- Top-5 |Σw|/gross candles: ALL type **mid-hold**, ALL with force-exit component
  **fxComp = −0.0000** and **drift = the entire net** (2025-05-05 +0.2177, 2025-04-30 +0.2207,
  2025-05-03 +0.2235, 2025-05-01 +0.2238, 2025-05-05 +0.2158; gross ≈ 0.98–1.02). The all-candle
  transient is **intra-hold P&L drift of fixed shares** (longs up / shorts down inside a winning
  week), NOT delisting force-exits and NOT a hedge leg — see anomaly c.
- **Cross-tranche G3reb localization** (targeted re-extraction, all 21 tranches): the A2-1
  rebal-row max 0.0699 occurs at **2021-02-16, tranche p=20, a min_members-SKIPPED rebal**
  (bn_status=0; decision row 1237 is one of the 6 post-go-live feasibility-dip rows) where the
  gate measures the HELD drifted book. In-window skipped rebal rows with a live book across ALL
  tranches: **6** (ratios 0.0131–0.0699; dips cluster 2021-01-16→02-16 and 2022-03-11). Executed
  rebal rows everywhere ≤ 3e-15. A2-N20's 0.1111 is DIFFERENT: an **executed** rebal
  (2020-05-07, p=3) with net = −0.100 / gross = 0.900 — the cap leg-infeasibility drop
  (anomaly d), not a skip and not drift.

**TABLE 3c — C1 projection-health panel (in-window executed projection rebals):**

| cell | n rebals | pre-rescale Σ\|w_proj\|: min/p5/med/max | amp max | amp>2× flags | ρ(w_proj,w_raw) mean/med/min | sign flips mean/max |
|---|---|---|---|---|---|---|
| A2-1 | 5983 | 0.478 / 0.862 / 0.985 / 1.047 | 2.09× | **2 (0.03%)** — 2022-04-02, 2022-02-28 | +0.975 / +0.989 / +0.695 | 1.24 / 10 |
| A2-N20 | 6202 | 0.404 / 0.777 / 0.972 / 1.081 | 2.48× | **6 (0.10%)** — 2022:4, 2024:2 | +0.955 / +0.979 / +0.490 | 0.86 / 7 |

Per-era (A2-1): ρ mean by year 2020 +0.973 / 2021 +0.983 / 2022 +0.981 / 2023 +0.981 /
**2024 +0.955 (min +0.695, flips 1.94/rebal — the most distorted year)** / 2025 +0.975. All
amp>2× flags land in the 2022 LUNA/Feb-war era, NOT the 2024-25 high-|book-β| era the pre-flight
flagged; the collapse-guard zone was never approached (min pre-rescale gross 0.478 ≫ 0.10).

## 7. TABLE 4 — Per-year, A2-1 (2020 partial from Apr; G-durable stream = UNCOSTED −funding_rets)

| year | n | total Sharpe | funding Sharpe | funding income sum | sign |
|---|---|---|---|---|---|
| 2020 | 805 | +2.854 | +20.871 | +0.0879 | + |
| 2021 | 1095 | +4.527 | +19.101 | +0.1604 | + |
| 2022 | 1095 | **−0.084** | +28.716 | +0.1516 | + |
| 2023 | 1095 | +1.224 | +17.022 | +0.2448 | + |
| 2024 | 1098 | +1.461 | +16.660 | +0.0922 | + |
| 2025 | 1094 | +0.306 | +15.811 | +0.2637 | + |

Funding income positive **6/6** years (G-durable years criterion; the +16.28 full-window funding
"Sharpe" is the known income-drip artifact, reported but informational per PHASE7-A §4.2).
Min per-year TOTAL Sharpe = −0.084 (2022 — the year the brief predicted thin).

## 8. TABLES 5–8 — monthly, attribution, contamination, phase dispersion (A2-1)

- **Monthly (69 months, full table in Appendix A):** win rate 55.1%. Worst-10: 2023-12 −11.23%,
  2020-11 −7.94%, 2025-09 −6.38%, 2025-06 −6.14%, 2022-07 −5.24%, 2022-11 −4.86%, 2024-05
  −4.05%, 2022-10 −3.81%, 2023-07 −3.49%, 2023-02 −3.24%. net_fund is positive in ALL 10.
- **Funding-vs-price attribution (common slice):** A2-1 cum total +1.8107 = price +1.0438 +
  funding income +1.0007 − tcost 0.2338. Funding **+1.59 bps/cd** (Cell-1 revealed +1.62) vs
  price **+1.66 bps/cd** (Cell-1 +1.89): the neutralization tax lands almost entirely on the
  **price leg**; the funding-carry income is preserved. Top-5 names (A2-1): SOL +13.2%, THETA
  +7.8%, BNB +7.8%, AVAX +7.4%, AXS +6.3% — no BTC hedge leg in the book; ALPACA absent (floor).
  N20: BNB +11.1%, SOL +10.4%, ALPACA +7.8%, FIL +6.7%, ETC +6.4%.
- **Contamination twin:** full-IS +1.6784 | ex-2025-03→12 **+2.0652** (ratio 1.23; G-contam S
  ≥0.7). Bucket means ex-window: CRASH **+0.94** bps/cd (n=580) vs full +1.13; MANIA +4.64;
  CHOP +3.27. (Note: A2's crash bucket stays ~+1 bps/cd ex-window — unlike Cell-1's exact flat
  −0.01; observed only, magnitude small, t not re-derived ex-window.)
- **Phase dispersion (21 tranche Sharpes):** min +0.849 / p25 +1.115 / med +1.390 / p75 +1.628 /
  max +1.821; **positive 21/21**; ensemble +1.6784.

## 9. TABLE 9 — A2-1 vs the REVEALED comparators (C4: both ways; cited, not re-run)

| metric | A2-1 | Cell-1 (hedged) | ratio | delta | Cell-3 (unhedged) | ratio | delta |
|---|---|---|---|---|---|---|---|
| net Sharpe | +1.6784 | +1.7753 | 0.945 | −0.0969 | +1.7195 | 0.976 | −0.0411 |
| 2×-GT Sharpe | +1.4619 | +1.5616 | 0.936 | −0.0997 | +1.5138 | 0.966 | −0.0519 |
| maxDD | −25.57% | −24.68% | 1.036 | −0.89pp | −26.28% | 0.973 | +0.71pp |
| turnover /yr | 54.3× | 54.9× | 0.990 | −0.6 | 53.3× | 1.019 | +1.0 |
| G2-CRASH β | +0.0088 | +0.0103 | 0.850 | −0.0015 | +0.0178 | 0.492 | −0.0090 |
| G3 max (rebal rows) | 0.0699 | 0.2365 | 0.296 | −0.1666 | 0.1080 | 0.647 | −0.0381 |
| funding years + | 6/6 | 6/6 | — | — | n/a | — | — |
| G1a within / max | 97.0% / 0.181 | 96.0% / 0.177 | — | — | 87.9% / 0.203 | — | — |

**§3.1 MECHANICAL bin (frozen thresholds applied arithmetically — NOT a verdict):** A2 Sharpe
+1.6784 ≥ 1.30 AND ratio 0.945 → **SURVIVE-≈INTACT**. C4 sharper comparator: A2/Cell-3 ratio
**0.976** (delta −0.0411) — the projection costs ~4 Sharpe-points vs the raw unhedged book,
~5.5 vs the hedged book.

## 10. §3 predictions vs observed (verbatim; hit/miss scoring = Phase 7)

| quantity | point | band | observed |
|---|---|---|---|
| Net ensemble Sharpe (headline) | +1.45 | [+0.9, +1.75] | **+1.6784** |
| Sharpe ratio A2 / Cell-1 | 0.82 | [0.51, 0.99] | **0.945** |
| Spearman ρ(w_proj, w_raw) | +0.90 | [0.75, 0.97] | **+0.975** (med +0.989) |
| Realized G3 max \|Σw\|/gross | +0.10 | [+0.05, +0.15] | **rebal-row 0.0699 / all-candle 0.2624** |
| Crash-conditional β_BTC | +0.02 | [−0.03, +0.08] | +0.0088 |
| Full-slice OLS β_BTC | +0.00 | [−0.03, +0.03] | −0.0133 |
| Rolling-270 β_ETH within (G1b) | 99% | [95%, 100%] | 100.0% |
| Post-cap target-β residual | 0.01 | [0.00, 0.04] | mean 0.0000, max 0.0058 |
| maxDD | −20% | [−12%, −28%] | **−25.57%** |
| 2×-cost net Sharpe (ground truth) | +1.25 | [+0.7, +1.55] | +1.4619 |
| Turnover (ann one-way) | 60× | [45×, 90×] | 54.3× |
| MANIA-bucket net mean (/mo) | +3.0% | [+1.0%, +5.0%] | +4.133% |
| Min per-year Sharpe (2022 thin) | 0.0 | (no band) | −0.084 (2022) |
| Beta-degenerate rebal fraction | <1% | [0%, 3%] | 0.00% (0 of 5984) |
| Warmup k / common first-True | 273/293 | (§7 pin) | **588/293** (mask pinned; anomaly a) |

## 11. Gate scorecard — observed vs frozen threshold (VERDICTS BLANK — Phase 7)

| gate | observed (A2-1) | frozen threshold | verdict |
|---|---|---|---|
| G1a (H) | within 97.0%, max 0.1813 | ≥95% \|β_BTC\|≤0.10 AND max ≤0.20 | [ ] |
| G1b (H) | within 100.0%, max 0.0957 | ≥95% \|β_ETH\|≤0.15 AND max ≤0.25 | [ ] |
| G2-CRASH (H) | β +0.0088 (n=658) | \|β\| ≤ 0.15 | [ ] |
| G2-MANIA (H) | β −0.0153 (n=999) | \|β\| ≤ 0.15 | [ ] |
| G3 (H) | rebal-row max 0.0699 (all-candle 0.2624 — see anomaly c) | ≤ 0.10 at every rebal | [ ] |
| G4 (H) | worst-bucket t +0.54 (CRASH) | t > −1.0 | [ ] |
| G5 (S) | max bucket share 70.9% (CHOP) | no bucket > 60% | [ ] |
| G-sharpe-floor (H) | +1.6784 | ≥ +0.35 | [ ] |
| G-sharpe-target (S) | +1.6784 | ≥ +0.90 | [ ] |
| G-durable (H) | 6/6 yrs > 0 (fund Sharpe +16.28, drip artifact, informational) | ≥ 5/6 years positive | [ ] |
| G-2xcost (H) | +1.4619 (0.87× of 1×) — GROUND TRUTH | > 0 AND ≥ 0.5×(1×) | [ ] |
| G-2xcost-target (S) | +1.4619 | ≥ +0.60 | [ ] |
| G-maxdd (H) | **−25.57%** | ≥ −25% | [ ] |
| G-maxdd-target (S) | −25.57% | ≥ −15% | [ ] |
| G-turnover (H) | 54.3× | ≤ 250×/yr | [ ] |
| G-sample (H) | live rebals min 285/tranche; 352 names | ≥200 AND ≥40 | [ ] |
| G-contam (S) | ex-window +2.0652 = 1.23× full | ≥ 0.7× full-IS | [ ] |

## 12. ANOMALY / FORENSIC NOTES (surprising values REPORTED, not resolved)

**a. Warmup-derivation prediction MISSED — the mask pin held (comparability intact).** The brief
§7 predicted the programmatic warmup lands at k=273 / first-True 293 with the universe
270-history filter binding at ~index 270. OBSERVED: β_BTC all-finite at row 135, but the first
row with ≥20 feasible members is **585 (2020-07-14)** → first live rebal **k=588** (N20: 360 →
378). The binding constraint is **panel population + the $3M floor** — the pre-floor top-40
universe holds only 3–24 names through mid-2020 (≥20 pre-floor members first at row 413; the
floor pushes it to 585). RECONCILIATION with the revealed EXPLORATION-A: identical physics —
its 571/21 ≈ 27 infeasible skips/tranche are every rebal through row ~567, its 285 live
rebals/tranche is exactly a first live rebal at 588, and its Appendix-A monthly table shows
+0.00% for 2020-04/05/06. **Cell-1's +1.7753 was therefore scored on a mask CONTAINING ~292
flat candles**, so scoring A2 on the IDENTICAL 293 mask keeps the comparison candle-for-candle
(both books flat over the same span); the 273/293 mask is a COMPARABILITY pin, not a
construction-minimum. Informational native fully-live-window Sharpe: +1.7307. Also corrects the
EXPLORATION-A engineering wording "all infeasible skips fall before the common metric window" —
they fall before the book's first LIVE rebal (row 588), which is INSIDE the metric window.

**b. The frozen degenerate-β guard inequality is SELF-REFERENTIAL as written.** Brief §1.6:
`det(AAᵀ) < 1e-12 · |M| · Σ(β−β̄)²`. But det(AAᵀ) ≡ |M|·Σ(β−β̄)² identically, so the literal
inequality reads x < 1e-12·x (never true except FP-rounding coin flips at β≈constant).
Implemented as the numerically-stable equivalent that the brief's OWN required unit test
(constant β ⇒ fallback fires, w unchanged) uniquely pins: `Σ(β−β̄)² ≤ 1e-12 · Σβ²` (β constant
to ~1e-6 relative sd ⇒ rank-deficient). **All candidate readings coincide on real data** — the
guard requires a near-constant β cross-section, which never occurs across 20–40 real alts:
observed `n_beta_degenerate_rebal = 0` and `n_projection_collapse_rebal = 0` in all 84 runs
(min pre-rescale gross 0.478 vs the 0.10 collapse floor). Reported for QR ratification; zero
effect on any observed number under any reading.

**c. G3 structure (THE modal-outcome question): the frozen rebal-row gate number is 0.0699 —
UNDER the 0.10 bound — and the predicted "force-exit floor" did NOT materialize as force-exit.**
Three layers, fully localized:
  (i) **Executed rebal targets:** |Σw_target| ≤ 2.96e-15 everywhere (the projection delivers
  Σw≡0 at every executed rebal, cap-preserved; capDrop=0 at N40).
  (ii) **The rebal-row max 0.0699** (the gate-convention number, vs Cell-1 0.2365 / Cell-3
  0.1080) comes from **6 in-window min_members-SKIPPED rebals with a live held book** (max:
  2021-02-16, tranche p=20; the others 2021-01-16→18 and 2022-03-11 — post-go-live feasibility
  dips where the decision row briefly held <20 members), where the gate measures the drifted
  held book. Not a hedge leg; not a projection artifact.
  (iii) **The all-candle max 0.2624** (0.41% of candles >0.10) is **intra-hold P&L drift on
  fixed shares** — the p=0 top-5 transient candles (2025-04-30→05-05, ratio ~0.22) have
  force-exit component ≡ −0.0000 and drift = the entire net (a week where longs rallied and
  shorts fell). The brief's §1.6/§3 story attributed this floor to mid-hold FORCE-EXITS
  (Cell-3's 0.1080 mechanism); observed: at rebal rows the projection absorbs fresh-target
  force-exits entirely, and the mid-hold transient is DRIFT, not force-exit. Which measurement
  ("at every rebal" verbatim vs all-candle) the frozen G3 gate scores is a Phase-7/QR read —
  both are reported side by side everywhere.

**d. NEW mechanism at N20 — projection-induced cap leg-infeasibility (robustness cell only).**
The projection can unbalance the long/short leg counts; at N20's small member counts (m ∈
[10,20]) a leg can end up with fewer names than `leg_gross / (0.10·g)` requires, and the FROZEN
EXPL-A cap semantics then DROP the residual excess → Σw ≠ 0 at an EXECUTED rebal target.
Observed: **14 capDrop rebals** across 21 tranches, max |Σw_target| = 0.100 → **A2-N20 G3
rebal-row max = 0.1111** (2020-05-07, p=3, net −0.100 / gross 0.900) — a breach-shaped number by
a mechanism that is neither a hedge leg nor a force-exit. N20's cap bind rate is **78.2%** (vs
22.3% in EXPL-A N20 — the projection+rescale pushes many weights above 0.10 at small m), and its
post-cap target-β residual reaches **0.1467**. The PRIMARY cell is untouched (capDrop=0, bind
1.3%, residual max 0.0058). Unit-tested as documented frozen-cap semantics; reading is Phase-7
scope.

**e. maxDD −25.57% vs the −25% HARD floor — a 0.57pp breach-shaped number on the PRIMARY
cell.** Consistent with the revealed geometry: Cell-1 passed at −24.68% only via the hedge
(PHASE7-A §4.3 flagged it fragile), and unhedged Cell-3 was −26.28%; A2 (no hedge leg, β folded
into weights) lands between. Prediction band [−12%, −28%] covered it; the frozen gate line
prints −25.57% vs ≥−25%.

**f. C3: realized-β excursions are ~entirely trailing-β-ESTIMATION error.** The projection
zeroes the pre-cap target exactly (4.3e-15); the cap residual is negligible at N40 (max 0.0058);
the rolling model-implied held-book β stays within ±0.016; yet the realized rolling β reaches
−0.1813 (2025-09-21), of which **−0.1781 is the estimation residual**. The G1a within-bound
fraction actually IMPROVED vs the hedged Cell-1 (97.0% vs 96.0%) while max|β| is fractionally
worse (0.1813 vs 0.1769).

**g. C1: the pre-flight's amplification concern mostly did NOT materialize.** Only 2 rebals
(0.03%) at N40 exceeded 2× amplification (max 2.09×, both 2022-02-28/2022-04-02 — the
LUNA/Feb-2022 era, NOT the 2024-25 high-|book-β| era the Critic predicted); pre-rescale gross
never fell below 0.478 (collapse floor 0.10). Projection distortion is small and era-dependent:
ρ(w_proj, w_raw) mean +0.975 (above the [0.75, 0.97] band top), worst year 2024 (mean +0.955,
min +0.695, 1.94 sign-flips/rebal of ~40 members).

**h. The neutralization tax lands on the PRICE leg, not the funding leg.** Funding income
+1.59 bps/cd (Cell-1 +1.62) vs price +1.66 bps/cd (Cell-1 +1.89): the projection preserves the
carry harvest and gives up ~0.23 bps/cd of price P&L — the −0.0969 Sharpe delta vs Cell-1.

**i. Analytic-2× drift 2.91e-4 (N40) / 5.78e-4 (N20)** vs the ~2.6e-4 stateless expectation —
slightly above at N20 (larger per-tranche turnover share), both well under the 1e-3 sanity and
the ensemble-Sharpe impact is 1e-4 (analytic +1.4618 vs GT +1.4619). Ground truth is
authoritative per the catalog rule; reported, never asserted.

**j. MANIA share fell as the brief's relabel §0.2 anticipated:** MANIA P&L share 25.0% (Cell-1
28.6%), CHOP 70.9% (69.6%) — shrinking the high-β short-meme leg shifts share toward CHOP; G5
soft-fail expected and disclosed. CRASH share +4.1% with mean +1.13 bps/cd full / +0.94
ex-window (n=580).

---

## Status

Implemented as frozen (+C1–C4 additive instrumentation); single results-bearing pass; all
internal-reproducibility pins green (bit-identical re-run, leg recon 1.11e-16, inert control
byte-identical, IS-guard everywhere, sign pin, leak controls); anomalies reported, none resolved
by improvisation; no verdicts; §3.1 bin printed mechanically only.

**READY-FOR-PHASE-7.** Hand to QR for IS evaluation against the frozen §4 gates and the §5
decision map. The holdout remains SEALED.

*— QE, MN track, 2026-07-10.*

---

## Appendix A — A2-1 (PRIMARY) full monthly table (1×, pinned common slice; ret compounded, legs summed)

```
month       n      ret   long_px  short_px  net_fund    tcost
-------------------------------------------------------------
2020-04    70   +0.00%   +0.0000   +0.0000   +0.0000   0.0000
2020-05    93   +0.00%   +0.0000   +0.0000   +0.0000   0.0000
2020-06    90   +0.00%   +0.0000   +0.0000   +0.0000   0.0000
2020-07    93   +4.24%   +0.0668   -0.0287   +0.0056   0.0019
2020-08    93   +6.57%   +0.1306   -0.0766   +0.0145   0.0036
2020-09    90   +7.22%   -0.0356   +0.0881   +0.0216   0.0032
2020-10    93   +3.06%   -0.0229   +0.0382   +0.0181   0.0027
2020-11    90   -7.94%   +0.1560   -0.2475   +0.0146   0.0032
2020-12    93  +18.50%   +0.1324   +0.0289   +0.0135   0.0034
2021-01    93  +14.64%   +0.3698   -0.2556   +0.0293   0.0031
2021-02    84  +21.07%   +0.3531   -0.1785   +0.0244   0.0038
2021-03    93  +14.09%   +0.2628   -0.1427   +0.0173   0.0033
2021-04    90   +9.95%   +0.2521   -0.1657   +0.0146   0.0038
2021-05    93  +11.81%   -0.0422   +0.1503   +0.0097   0.0038
2021-06    90   +3.15%   -0.0959   +0.1251   +0.0056   0.0032
2021-07    93  +13.99%   +0.1676   -0.0431   +0.0136   0.0035
2021-08    93   +8.24%   +0.2317   -0.1523   +0.0050   0.0038
2021-09    90   +4.79%   +0.0005   +0.0497   +0.0021   0.0039
2021-10    93   +4.62%   +0.1508   -0.1099   +0.0087   0.0035
2021-11    90   -2.05%   +0.0000   -0.0357   +0.0201   0.0035
2021-12    93   +0.88%   -0.0814   +0.0847   +0.0098   0.0037
2022-01    93   +2.09%   -0.1321   +0.1484   +0.0082   0.0034
2022-02    84   -2.89%   -0.0052   -0.0270   +0.0063   0.0030
2022-03    93  +10.79%   +0.1580   -0.0597   +0.0093   0.0036
2022-04    90   -1.63%   -0.2206   +0.2006   +0.0073   0.0031
2022-05    93   -1.14%   -0.1638   +0.1402   +0.0169   0.0029
2022-06    90   +5.57%   -0.1416   +0.1827   +0.0180   0.0032
2022-07    93   -5.24%   +0.1000   -0.1609   +0.0109   0.0033
2022-08    93   -0.65%   -0.0970   +0.0861   +0.0085   0.0032
2022-09    90   -2.11%   -0.0500   +0.0191   +0.0144   0.0030
2022-10    93   -3.81%   -0.0072   -0.0352   +0.0076   0.0029
2022-11    90   -4.86%   -0.1190   +0.0520   +0.0218   0.0033
2022-12    93   +2.44%   -0.1137   +0.1193   +0.0223   0.0034
2023-01    93   +6.19%   +0.2953   -0.2431   +0.0124   0.0036
2023-02    84   -3.24%   -0.0392   +0.0045   +0.0060   0.0033
2023-03    93   +5.24%   +0.0158   +0.0321   +0.0074   0.0035
2023-04    90   +1.92%   -0.0246   +0.0348   +0.0127   0.0033
2023-05    93   +4.29%   +0.0104   +0.0258   +0.0110   0.0034
2023-06    90   -3.06%   -0.0489   +0.0133   +0.0088   0.0036
2023-07    93   -3.49%   -0.0293   -0.0169   +0.0149   0.0036
2023-08    93   +9.41%   -0.0574   +0.0981   +0.0536   0.0035
2023-09    90  +17.92%   +0.1040   -0.0289   +0.0956   0.0035
2023-10    93   -0.48%   +0.0778   -0.0834   +0.0057   0.0042
2023-11    90   -2.12%   +0.0299   -0.0555   +0.0086   0.0038
2023-12    93  -11.23%   +0.0824   -0.2037   +0.0081   0.0042
2024-01    93   -1.36%   -0.0496   +0.0352   +0.0051   0.0033
2024-02    87   -1.50%   +0.1360   -0.1546   +0.0078   0.0036
2024-03    93   -2.07%   +0.1325   -0.1531   +0.0072   0.0040
2024-04    90   +6.89%   -0.1654   +0.2295   +0.0071   0.0037
2024-05    93   -4.05%   +0.0683   -0.1086   +0.0034   0.0040
2024-06    90   +0.86%   -0.1188   +0.1295   +0.0021   0.0039
2024-07    93   -1.19%   -0.0273   +0.0124   +0.0073   0.0037
2024-08    93   -2.02%   -0.1080   +0.0842   +0.0076   0.0036
2024-09    90   +6.89%   +0.1727   -0.1069   +0.0061   0.0040
2024-10    93   +1.24%   -0.0301   +0.0328   +0.0142   0.0037
2024-11    90   +7.11%   +0.2995   -0.2295   +0.0043   0.0040
2024-12    93  +13.86%   -0.0192   +0.1343   +0.0199   0.0036
2025-01    93   +2.59%   -0.0266   +0.0381   +0.0187   0.0034
2025-02    84   -0.92%   -0.1545   +0.1380   +0.0111   0.0032
2025-03    93   -1.91%   -0.1378   +0.0989   +0.0254   0.0040
2025-04    90  +13.84%   +0.1407   -0.0207   +0.0217   0.0041
2025-05    93   -0.54%   +0.0009   -0.0064   +0.0057   0.0045
2025-06    90   -6.14%   -0.1062   +0.0297   +0.0176   0.0039
2025-07    93   +4.63%   +0.0879   -0.0428   +0.0075   0.0043
2025-08    93   -2.50%   -0.0301   -0.0138   +0.0233   0.0038
2025-09    90   -6.38%   -0.0328   -0.0476   +0.0199   0.0038
2025-10    93   +0.45%   -0.0938   +0.0961   +0.0076   0.0039
2025-11    90   +1.09%   -0.1855   +0.1427   +0.0612   0.0035
2025-12    92   +1.82%   -0.0575   +0.0398   +0.0439   0.0037
```
