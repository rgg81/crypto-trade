# EXPLORATION-A — Engineering Report (QE, Phase 6)

**Date:** 2026-07-10 · **Role:** Quant Engineer · **Track:** baseline-BLIND MARKET-NEUTRAL (MN)
**Contract:** `briefs-portfolio-mn/EXPLORATION-A.md` **including PRE-RUN AMENDMENT 001 (C1–C6)**
— implemented exactly as amended-frozen; no parameter adjusted, no phase selected, no re-run
after seeing results.
**Script:** `analysis/portfolio/mn_exploration_a.py` (single frozen pass; matrix run twice only
for the pre-registered bit-identity check). **Engine extension:** `blind_engine.py` `weight_cap`
+ `min_members` (AMENDMENT C2, sanctioned). **Tests:** `tests/test_mn_exploration_a.py` (10 new;
full suite 86 = 55 blind + 21 mn + 10 new, ALL GREEN).
**NOT committed** (per dispatch). Branch `quant-portfolio-blind`; note `analysis/` is gitignored
in this worktree — the mn_*/blind_* infrastructure files are untracked on disk, unchanged state.
**Hardware / wall-clock:** i9-12900HK, 20 threads, 58 GB — full run (336 tranche backtests =
2 × 168, + betas/funding/universes recomputed per pass) ≈ **9 min** end to end.

**Blinding/IS:** `mn_panel_health()` first (OK; BTC grid T=7147 contiguous; live feeds current).
Panel sliced via `mn_slice_is` (T=6576, C=747, 2020-01-01 → 2025-12-31); `mn_guard_grid` passed
on the IS grid AND on every tranche grid. Old-track `is_mask`/`OOS_CUTOFF`/`slice_is` never
touched. **No holdout candle touched; `confirmation_reveal` never passed.** No baseline
artifact read. Ensemble helpers reused from `blind_exploration_007`/`blind_paper_l1` after
verifying import produces zero execution/stdout (brief §1.4/§7 reuse path).

**ENGINEER SCOPE:** observed values only. Gate PASS/FAIL, tiers, and the §4.5/C4 A2-trigger
decision are the QR's Phase-7 calls. Thresholds are printed alongside every observed value;
verdict cells are deliberately blank. (Brief §7 item 8 asked for "mechanical pass/fail"; the
dispatch instruction "observed values only — gate verdicts are QR/Critic's Phase-7 calls"
supersedes it — noted as a contract deviation resolved in favor of the dispatch.)

---

## 1. What was built (work item 1 — C2 engine extension)

`blind_engine.run_backtest` gained two **opt-in** parameters (defaults `None` = byte-identical,
zero added FP ops on the legacy path):

- `weight_cap: float | None` — per-name `|w_i| <= weight_cap * g` (g = the rebal's applied
  target gross) via new module function `apply_weight_cap`: iterative same-leg pro-rata
  redistribution to a fixed point (clip → redistribute over strictly-under-cap same-leg names →
  re-clip; capped set grows monotonically ⇒ terminates in ≤ n_leg passes). Preserves Σw and
  Σ|w| to ±1e-12 in the feasible case. Applied AFTER the weighting builder **and after the
  engine's invalid-price force-exit**, BEFORE the hedge overlay (so the hedge is sized on the
  capped alpha book, per §1.3/C2). *Implementation note:* the brief is silent on cap-vs-force-exit
  ordering; cap-after-force-exit was chosen so the invariants hold on the book actually held —
  the two orderings coincide at every rebal without a force-exit.
- `min_members: int | None` — the FROZEN C2 infeasibility rule verbatim: at a rebal with
  `m = (universe[k-1] & isfinite(signal[k-1])).sum() < min_members`, the rebal is SKIPPED (hold
  previous weights, no new target, no forced flatten, no turnover) and counted. Applied with
  `min_members = N//2` to ALL cells, both N (rule identical across cells).
- New forensic metrics (always present, inert-zero when off): `n_rebal_executed`,
  `n_infeasible_rebal`, `n_cap_bound_rebal`, `cap_redistributed_total`, `weight_cap_enabled`.

**Tests (10 new, `tests/test_mn_exploration_a.py`):** inert-default byte-identity across 3
weighting modes (`assert_array_equal` on weights/turnover/equity/rets/funding_rets) + a
non-binding-parameterization byte-identity (cap=1.0, min_members=0 exercise the new paths and
change nothing); binding-cap engine semantics (Σw=0, Σ|w|=gross ±1e-12, max|w| ≤ cap+1e-12,
non-vacuous); hand-computed multi-pass fixed point ([0.50,0.28,0.12,0.10] @ cap 0.30 →
[0.30, 0.30, 16.8/77, 14/77], redistributed notional exact); same-leg preservation (short leg
bitwise untouched, zeros stay zero, no sign flips); min-members skip-rebal (turnover 0, held
name-set carries, counter exact, rebals resume); **hedge-sized-on-capped-book ordering**
(h_btc == −(w_capped_alpha @ β[k−1]) at every rebal, ±1e-12); DIAG-A funding-sort signal
corrupt-future leak positive control (past bit-identical, future changed, non-vacuous).
Pre-existing suites untouched and green (55 blind + 21 mn).

## 2. Run protocol confirmations (top-of-script hard order + C3)

| Check | Result |
|---|---|
| `mn_panel_health()` first | OK (grid contiguous; BTC+top40 live current) |
| IS slice + `mn_guard_grid` + last-candle extent | PASS (T=6576, ends 2025-12-31) |
| Sign pin `signal_engine = -build_signal(fund, univ)` | PASS (element-for-element, NaNs incl.) |
| Funding coverage (floored top-40 ever-members) | complete (745/747 direct, 2 non-members missing) |
| Regime occupancy (frozen rules) | CRASH 11.5% / MANIA 15.7% / CHOP 72.7% — matches DIAG-A |
| C3 warmup, derived programmatically | β_eth_resid first all-finite row = **269** → first fully-hedged rebal k = **273** — asserted ==273 |
| Common mask first-True | **293** (2020-04-07) — asserted ==293; contiguous [293, 6574]; n_common=6282; **IDENTICAL mask for all 4 cells and both cost tiers** (asserted per cell/tier) |
| COVID disclosure (C3) | metric window starts 2020-04-07 → March-2020 crash OUTSIDE the window |
| Betas | computed **per tranche** (the brief's unconditional path; no trim-invariance assert needed) |
| Members/candle N=40 | before floor 36.6 → after floor 36.1 (min 0, p5 = 8 — the floor bites hard early-era) |
| Members/candle N=20 | 18.9 → 18.8 |
| Leak positive control (script, spot) | corrupt fund[3288:,:] → signal[:3288] bit-identical; future changed (non-vacuous) — PASS |

## 3. Internal reproducibility (brief §7 pins — no parity anchor exists)

| Pin | Result |
|---|---|
| **Bit-identical re-run** (full matrix recomputed from scratch, incl. funding/universes/betas) | PASS — all mapped rets/turnover/funding-income/per-name-P&L arrays + counters bit-identical across passes |
| **Leg reconciliation** price − tcost − funding ≡ rets, ALL 168 runs | max **1.11e-16** (≤1e-12) PASS |
| **Hedge-inert control** (Cell-3 p=0, `hedge_overlay=None` vs all-zero-beta overlay) | max Δrets = **0.00e+00** (≤1e-12) PASS |
| **IS-guard on every tranche grid** | PASS (mn_guard_grid per tranche, both passes) |
| **Ensemble leg reconciliation** (per cell/tier) | ≤1e-12 asserted, PASS |

## 4. TABLE 1 — Headline per cell (1×; common slice [293, 6574]; PPY=1095)

| cell | Sharpe | fundSh (uncosted) | fundSh (costed) | 2×Sh (GROUND TRUTH) | ann vol | maxDD | turn/yr | ann ret | mo win | top-name share |
|---|---|---|---|---|---|---|---|---|---|---|
| **cell1 (PRIMARY)** | **+1.7753** | +16.340 | +12.560 | **+1.5616** | 19.28% | **−24.68%** | 54.9× | +38.24% | 55.1% | 12.7% (SOL) |
| cell2 (no floor/cap) | +1.7605 | +16.508 | +12.598 | +1.5424 | 19.35% | −25.55% | 56.3× | +37.98% | 55.1% | 12.8% (SOL) |
| cell3 (unhedged) | +1.7195 | +16.597 | +12.922 | +1.5138 | 19.42% | −26.28% | 53.3× | +37.04% | 58.0% | 13.0% (SOL) |
| cell1-N20 | +1.7388 | +11.618 | +8.662 | +1.5660 | 25.98% | −26.26% | 59.8× | +51.93% | 60.9% | 10.7% (BNB) |

Thresholds alongside: G-sharpe-floor ≥ +0.35 (H) · target ≥ +0.90 (S) · G-durable fundSh ≥
+0.25 AND ≥5/6 yrs > 0 (H) · G-2xcost > 0 AND ≥ 0.5×(1× Sharpe) (H) · target ≥ +0.60 (S) ·
G-maxdd ≥ −25% (H) · target ≥ −15% (S) · G-turnover ≤ 250×/yr (H).
Turnover cross-check (full-array (1/21)ΣT_p^ann): 52.5× / 53.8× / 51.0× / 57.3× — consistent
with the C3 common-slice primary (54.9× / 56.3× / 53.3× / 59.8×).

## 5. TABLE 2 — Neutrality panel (C5 mechanics: BTC/ETH HOLD-return regressor open→open; rolling 270/135; RETURN-candle labels; n<30 → N/A-FAIL; no bucket thin)

**Cell 1 (HEDGED, PRIMARY):**
- rolling-270 β_BTC: **within |β|≤0.10 on 96.0%** of 6148 defined candles; **max |β| = 0.1769** [G1a: ≥95% AND max ≤0.20 (H)]
- rolling-270 β_ETH: within 100.0%; max 0.1016 [G1b: ≥95% |β|≤0.15 AND max ≤0.25 (H)]
- full-slice OLS: β_BTC = −0.0120 (se 0.0042); β_ETH = −0.0132 (se 0.0032); mean rolling β_BTC = −0.0208
- **CRASH n=658: β_BTC = +0.0103 (se 0.0089)** [G2 |β|≤0.15 (H)] — mean +0.54 bps/cd (+0.495%/mo), t = +0.26, P&L share +1.8%
- MANIA n=999: β_BTC = −0.0113 (se 0.0103) [G2] — mean +5.62 bps/cd (+5.128%/mo), t = +2.63, share +28.6%
- CHOP n=4625: β_BTC = −0.0213 (se 0.0054) — mean +2.96 bps/cd (+2.697%/mo), t = +3.55, **share +69.6%** [G5 ≤60% (S)]
- worst-bucket t = **+0.26** (CRASH) [G4: t > −1.0 (H)]

**Cell 3 (UNHEDGED reference):**
- rolling-270 β_BTC: within 87.9%; max 0.2031 · β_ETH within 100.0%; max 0.1221
- full OLS β_BTC = −0.0221 (se 0.0042) · CRASH β_BTC = +0.0178 (se 0.0089) · MANIA −0.0328 · CHOP −0.0329
- buckets: CRASH +0.58 bps/cd t +0.27 · MANIA +4.63 bps/cd t +2.16 · CHOP +3.06 bps/cd t +3.64 (share 73.8%)

**Hedge crash-beta contribution (Cell3 − Cell1 CRASH β_BTC): +0.0075** — the §5.2 headline
delta. The overlay also lifts full-window within-bound from 87.9% → 96.0% and max|β| 0.2031 →
0.1769, and adds MANIA share +4.4pp of P&L (hedge was net-long BTC; see §9a).

## 6. TABLE 3 — G3 + hedge / cap / floor / infeasibility forensics (1× runs)

| cell | G3 max \|Σw\|/gross | cap bind-rate | mean redistributed | n_infeasible | infeas % | ETH-armed % (common rebals) | hedge skips | hedge turn share | live rebals min/mean | names traded |
|---|---|---|---|---|---|---|---|---|---|---|
| cell1 | **0.2365** | **0.0%** | n/a | 571 | 8.7% | 2.0% | 0 | 3.9% | 285/285 | 352 (350 ex-hedge) |
| cell2 | 0.2363 | 0.0% | n/a | 405 | 6.2% | 2.0% | 0 | 3.9% | 293/293 | 353 |
| cell3 | 0.1080 | 0.0% | n/a | 571 | 8.7% | — | — | — | 285/285 | 352 (350 ex-hedge) |
| cell1-N20 | 0.2395 | **22.3%** | 0.0269 | 352 | 5.4% | 6.0% | 0 | 6.0% | 295/296 | 255 |

Thresholds: G3 |Σw| ≤ 0.10×gross at every rebal (H). G-sample ≥200 live rebals/tranche AND ≥40
names (H). Infeasible-fraction flag threshold 10% (C2) — no cell exceeds it; all infeasible
skips fall in the early era BEFORE the common metric window (verified: 0 in-window skips on the
p=0 forensic, and live-rebal counts equal the full common-window rebal count in every tranche).

## 7. TABLE 4 — Per-year, Cell 1 (2020 partial, from Apr; G-durable stream = UNCOSTED −funding_rets)

| year | n | total Sharpe | funding Sharpe | funding income sum | sign |
|---|---|---|---|---|---|
| 2020 | 805 | +3.737 | +20.826 | +0.0901 | + |
| 2021 | 1095 | +4.303 | +18.960 | +0.1606 | + |
| 2022 | 1095 | **−0.165** | +23.492 | +0.1604 | + |
| 2023 | 1095 | +1.369 | +17.355 | +0.2473 | + |
| 2024 | 1098 | +1.735 | +15.821 | +0.0873 | + |
| 2025 | 1094 | +0.421 | +16.318 | +0.2704 | + |

Funding income positive **6/6** years (G-durable needs ≥5/6). Min per-year TOTAL Sharpe =
−0.165 (2022, not the predicted 2024; 2024 was +1.735).

## 8. TABLES 5–8 — monthly, attribution, contamination, phase dispersion (Cell 1)

- **Monthly (69 months):** win rate 55.1%. Worst-10: 2023-12 −10.63%, 2020-11 −6.23%, 2024-03
  −6.12%, 2025-09 −5.30%, 2022-11 −5.22%, 2022-07 −5.10%, 2025-06 −4.90%, 2022-02 −4.65%,
  2024-05 −4.53%, 2022-10 −3.75%. In 9 of the worst 10, net_fund is POSITIVE while a price leg
  bleeds (full monthly table in the run log / script output, reproducible bit-identically).
- **Funding-vs-price attribution (arithmetic sums, common slice):** Cell 1 cum total +1.9641 =
  price +1.1842 + funding income +1.0161 − tcost 0.2362. Funding +1.62 bps/cd, price +1.89
  bps/cd. Same split within ±1% across cells 2/3; N20 price component much larger (+2.92 bps/cd).
- **Floor+cap P&L cost (Cell1 − Cell2): ΔSharpe = +0.0148** — the floor/cap costs ~nothing at
  N=40 and slightly HELPS. ALPACA appears in Cell 2/3 top-5 name concentration (+5.7%/+5.8%)
  and is REMOVED from Cell 1's top-5 by the floor. Top-5 shares (Cell 1): SOL +12.7%, BNB +8.0%,
  THETA +7.4%, BTC +6.2% (hedge leg), AVAX +6.0%. N20: BNB +10.7%, SOL +9.7%, ALPACA +6.7%,
  **LUNA −6.4%**, BTC +6.1%.
- **Contamination twin (Cell 1):** full-IS Sharpe +1.7753 | **ex-2025-03→2025-12 Sharpe
  +2.1353** (ratio 1.20; G-contam S needs ≥0.7) — stronger ex-window, consistent with DIAG-A.
  Bucket means ex-window: **CRASH −0.01 bps/cd (n=580)** vs full +0.54 (n=658); MANIA +5.79;
  CHOP +3.43.
- **Phase dispersion (21 tranche common-slice Sharpes, Cell 1):** min +0.939 / p25 +1.208 /
  med +1.460 / p75 +1.710 / max +1.937; **positive 21/21**; ensemble +1.7753 (above the best
  single phase's neighborhood via diversification, selects nothing).

## 9. ANOMALY / FORENSIC NOTES (surprising numbers REPORTED, not resolved)

**a. G3 breach is the hedge's own mechanical net exposure (THE structural surprise).**
Observed Cell-1 G3 max = 0.2365 vs frozen bound 0.10 and amendment band [0.02, 0.12].
Forensic re-extraction of tranche p=0 (same frozen construction; bit-identity already proven;
no parameter touched): at every one of the worst rebals **alpha_net ≡ 0.0000 exactly** and the
entire net = the BTC hedge leg — `hedge_btc` = **+0.2155 (2025-04-23)**, +0.1882 (2024-11-20),
+0.1792 (2024-03-06), +0.1631 (2025-04-30), +0.1598 (2025-07-23); hedge_eth 0 at those rebals.
p50 ratio 0.031, p90 0.083, p99 0.142; **5.9% of common-window rebals exceed 0.10**; zero
in-window infeasibility skips. The alpha book carries NEGATIVE BTC beta (long structurally
negative-funding majors vs short high-beta memes), so the overlay goes net-LONG BTC to cancel
it — |book β| reaches ~0.22 in 2024-25, so the §1.7 premise "hedge legs add net exposure ≈
−book_beta (small)" does not hold in that era. Cell 3 (unhedged) max 0.1080 comes from a
different, minor mechanism: invalid-price force-exits of held names at rebal (delisting era;
e.g. 2022-02-16 net +0.046 with gross 0.954). The tension between the frozen G3 wording
(|Σw| ≤ 0.10×gross post-hedge INCLUDING hedge legs) and the hedge overlay design is a
Phase-7/QR read — reported here, not resolved.

**b. Analytic-2× drift exceeded the ≤1e-3 sanity on exactly the two cells with ETH-arm flips.**
cell1 2.40e-03 (arm-count deltas 1×vs2× = 2), cell1-N20 1.35e-03 (deltas = 5); cells with zero
flips show pure fixed-share drift ~2.6e-4. Mechanism: the ETH arming regression consumes the
book's OWN past net rets, which are cost-dependent → at 2× costs a few arming decisions flip →
weights genuinely differ. This is a SECOND, larger invalidation channel of the analytic
identity beyond /007's equity-renormalization drift — C1's ground-truth re-runs are the
authoritative 2× numbers (ensemble-Sharpe impact of the drift is negligible: +1.5619 analytic
vs +1.5616 ground truth on Cell 1). Reported per the amendment; never asserted.

**c. The 0.10 cap is STRUCTURALLY INERT at N=40 given the min-members rule.** Rank-neutral max
weight at m members ≈ ((m−1)/2)/Σ|demeaned ranks| ≤ 0.10 for all m ≥ 19; min_members = 20
skips every rebal that could have violated it → bind-rate 0.0%, mean redistributed n/a. The
Critic's F2 binding premise (post-floor membership ≤18 ⇒ max weight >10%) is exactly the
region the frozen C2 skip-rule excludes. The cap DOES bind at N=20 (m ∈ [10,20)): bind-rate
22.3%, mean redistributed 0.0269 per binding rebal. Both engine paths are exercised and
unit-tested regardless.

**d. Funding-only (uncosted) Sharpe +16.3** — far above the §3 band [+0.3, +1.2]. The uncosted
income stream of a ~dollar-neutral book is a near-deterministic drip (mean +1.62 bps/cd, tiny
σ). The prediction appears to have been scaled for a total-return-like vol; the COSTED honesty
line is +12.56 (income minus the turnover cost needed to hold the positions). Observed only;
prediction scoring is Phase 7.

**e. Turnover 54.9×/yr — BELOW the predicted band [90×, 200×]** (DIAG-A decile book: 145×).
Rank weights mutate far less at weekly cadence than decile membership swaps. Cost-favorable;
reported as a prediction miss on the conservative side.

**f. maxDD −24.68% vs the −25% HARD floor — 0.32pp of margin.** Razor-thin; single-phase
tranches range wider (Cell 3 ensemble −26.28% would sit below the floor). Phase-7 read.

**g. CRASH-bucket profitability is concentrated in the revealed 2025 window:** full-IS CRASH
mean +0.54 bps/cd → **−0.01 bps/cd ex-window** (n=580). The crash-bucket BETA result (G2 crux)
is unaffected (β is a slope, not a mean), but the "crash bucket earns money" reading depends
on the burned window; ex-window it is exactly flat. Disclosed per charter §5.4.

**h. The DIAG-A crash-beta problem largely did not translate to the engine book:** DIAG-A's
static-residual CRASH β was +0.172; the engine rank book measures CRASH β = +0.0178 UNHEDGED
(Cell 3) and +0.0103 hedged (Cell 1). The rank-weighted, capped, floored engine book is a
different object from the equal-weight decile probe; the overlay's crash-beta contribution is
small (+0.0075) because there was little left to remove. The §3 prediction (+0.08, band
straddling 0.15) was pessimistic on this axis.

**i. G1a margins are not wide:** 96.0% within-bound vs the 95% requirement, max|β| 0.1769 vs
0.20 cap. The max-|β| episodes coincide with the 2024-25 negative-book-beta era of note (a).

**j. Min per-year Sharpe −0.165 landed in 2022, not the predicted 2024** (2024: +1.735). 2025
is the second-weakest (+0.421).

**k. ETH arm fraction 2.0% of common rebals — below the [5%, 50%] band**; hedge skips = 0
everywhere; hedge turnover share 3.9% (N40) / 6.0% (N20).

## 10. §3 predictions vs observed (verbatim; hit/miss scoring = Phase 7)

| quantity | point | band | observed |
|---|---|---|---|
| Net ensemble Sharpe | +0.9 | [+0.4, +1.6] | **+1.7753** |
| Funding-only Sharpe (uncosted) | +0.7 | [+0.3, +1.2] | **+16.34** |
| Net vol (ann) | 12% | [7%, 20%] | 19.3% |
| maxDD | −15% | [−8%, −28%] | −24.68% |
| 2×-cost net Sharpe (ground truth) | +0.7 | [+0.2, +1.4] | +1.5616 |
| Turnover (ann one-way) | 140× | [90×, 200×] | **54.9×** |
| Rolling 270 β_BTC (full OLS) | +0.02 | [−0.05, +0.08] | −0.0120 |
| CRASH β_BTC after hedge (G2 crux) | +0.08 | [−0.05, +0.20] | **+0.0103** |
| CRASH-bucket net t (G4 crux) | ~0 | [−1.2, +0.6] | +0.26 |
| MANIA-bucket net mean (/mo) | +0.8% | [+0.2%, +1.6%] | **+5.13%** |
| Min per-year Sharpe | +0.1 | (2024 weakest) | −0.165 (2022) |
| Cap bind-rate | 8% | [2%, 25%] | **0.0%** (N40; N20: 22.3%) |
| ETH-armed rebal fraction | 20% | [5%, 50%] | 2.0% |
| G3 max \|Σw\|/gross (amendment) | 0.05 | [0.02, 0.12] | **0.2365** |

## 11. Gate scorecard — observed vs frozen threshold (VERDICTS BLANK — Phase 7)

| gate | observed (Cell 1) | frozen threshold | verdict |
|---|---|---|---|
| G1a (H) | within 96.0%, max 0.1769 | ≥95% \|β_BTC\|≤0.10 AND max ≤0.20 | [ ] |
| G1b (H) | within 100.0%, max 0.1016 | ≥95% \|β_ETH\|≤0.15 AND max ≤0.25 | [ ] |
| G2-CRASH (H) | β +0.0103 (n=658) | \|β\| ≤ 0.15 | [ ] |
| G2-MANIA (H) | β −0.0113 (n=999) | \|β\| ≤ 0.15 | [ ] |
| G3 (H) | max \|Σw\|/gross 0.2365 | ≤ 0.10 at every rebal | [ ] |
| G4 (H) | worst-bucket t +0.26 (CRASH) | t > −1.0 | [ ] |
| G5 (S) | max bucket share 69.6% (CHOP) | no bucket > 60% | [ ] |
| G-sharpe-floor (H) | +1.7753 | ≥ +0.35 | [ ] |
| G-sharpe-target (S) | +1.7753 | ≥ +0.90 | [ ] |
| G-durable (H) | fund Sharpe +16.34, 6/6 yrs > 0 | ≥ +0.25 AND ≥5/6 yrs | [ ] |
| G-2xcost (H) | +1.5616 (0.88 of 1×) | > 0 AND ≥ 0.5 × 1× | [ ] |
| G-2xcost-target (S) | +1.5616 | ≥ +0.60 | [ ] |
| G-maxdd (H) | −24.68% | ≥ −25% | [ ] |
| G-maxdd-target (S) | −24.68% | ≥ −15% | [ ] |
| G-turnover (H) | 54.9× | ≤ 250×/yr | [ ] |
| G-sample (H) | ≥285 live rebals/tranche; 352 names (350 ex-hedge) | ≥200 AND ≥40 | [ ] |
| G-contam (S) | ex-window +2.1353 = 1.20 × full | ≥ 0.7 × full-IS | [ ] |

---

## Status

Implemented as amended-frozen; single results-bearing pass; all internal-reproducibility pins
green (bit-identical re-run, leg recon 1.11e-16, hedge-inert 0.00e+00, IS-guard everywhere,
sign pin, leak controls); anomalies reported, none resolved by improvisation; no verdicts.

**READY-FOR-PHASE-7.** Hand to QR for IS evaluation against §4 gates, §4.5/C4 A2-trigger rule,
and the §5 decision map. The holdout remains SEALED.

*— QE, MN track, 2026-07-10.*

---

## Appendix A — Cell 1 (PRIMARY) full monthly table (1×, common slice; ret compounded, legs summed)

```
month       n      ret   long_px  short_px  net_fund    tcost
-------------------------------------------------------------
2020-04    70   +0.00%   +0.0000   +0.0000   +0.0000   0.0000
2020-05    93   +0.00%   +0.0000   +0.0000   +0.0000   0.0000
2020-06    90   +0.00%   +0.0000   +0.0000   +0.0000   0.0000
2020-07    93   +4.10%   +0.0665   -0.0296   +0.0055   0.0019
2020-08    93   +7.38%   +0.1366   -0.0752   +0.0148   0.0036
2020-09    90   +8.25%   -0.0279   +0.0888   +0.0227   0.0030
2020-10    93   +5.15%   -0.0031   +0.0363   +0.0201   0.0025
2020-11    90   -6.23%   +0.1612   -0.2340   +0.0140   0.0033
2020-12    93  +21.52%   +0.1430   +0.0438   +0.0131   0.0034
2021-01    93  +12.08%   +0.3641   -0.2739   +0.0310   0.0031
2021-02    84  +20.29%   +0.3555   -0.1866   +0.0236   0.0038
2021-03    93  +14.67%   +0.2656   -0.1402   +0.0171   0.0033
2021-04    90  +10.55%   +0.2570   -0.1648   +0.0143   0.0038
2021-05    93  +11.99%   -0.0393   +0.1478   +0.0109   0.0039
2021-06    90   +1.73%   -0.0994   +0.1147   +0.0057   0.0032
2021-07    93  +13.17%   +0.1590   -0.0415   +0.0129   0.0034
2021-08    93   +7.51%   +0.2206   -0.1483   +0.0052   0.0037
2021-09    90   +3.05%   -0.0087   +0.0423   +0.0020   0.0038
2021-10    93   +6.98%   +0.1661   -0.1028   +0.0086   0.0034
2021-11    90   -1.45%   +0.0019   -0.0310   +0.0197   0.0035
2021-12    93   -0.18%   -0.0926   +0.0856   +0.0095   0.0037
2022-01    93   +1.74%   -0.1329   +0.1458   +0.0082   0.0034
2022-02    84   -4.65%   -0.0174   -0.0333   +0.0065   0.0029
2022-03    93  +10.01%   +0.1582   -0.0668   +0.0091   0.0036
2022-04    90   -0.06%   -0.2073   +0.2033   +0.0070   0.0030
2022-05    93   -2.92%   -0.1816   +0.1400   +0.0168   0.0029
2022-06    90   +6.59%   -0.1352   +0.1870   +0.0177   0.0032
2022-07    93   -5.10%   +0.1003   -0.1591   +0.0107   0.0034
2022-08    93   -1.30%   -0.0975   +0.0802   +0.0084   0.0032
2022-09    90   -2.03%   -0.0485   +0.0186   +0.0141   0.0030
2022-10    93   -3.75%   -0.0091   -0.0327   +0.0075   0.0029
2022-11    90   -5.22%   -0.1298   +0.0516   +0.0297   0.0035
2022-12    93   +3.88%   -0.1043   +0.1216   +0.0247   0.0035
2023-01    93   +7.69%   +0.3171   -0.2514   +0.0134   0.0038
2023-02    84   -3.41%   -0.0396   +0.0034   +0.0060   0.0034
2023-03    93   +4.15%   +0.0205   +0.0171   +0.0076   0.0037
2023-04    90   +2.46%   -0.0211   +0.0372   +0.0121   0.0033
2023-05    93   +3.87%   +0.0078   +0.0249   +0.0105   0.0035
2023-06    90   -2.95%   -0.0470   +0.0127   +0.0088   0.0036
2023-07    93   -2.87%   -0.0276   -0.0120   +0.0147   0.0037
2023-08    93   +9.00%   -0.0605   +0.0980   +0.0530   0.0035
2023-09    90  +17.13%   +0.0998   -0.0294   +0.0937   0.0036
2023-10    93   +1.13%   +0.0887   -0.0824   +0.0097   0.0042
2023-11    90   -1.97%   +0.0313   -0.0551   +0.0081   0.0037
2023-12    93  -10.63%   +0.0902   -0.2064   +0.0098   0.0042
2024-01    93   -1.28%   -0.0456   +0.0324   +0.0051   0.0033
2024-02    87   -0.09%   +0.1552   -0.1593   +0.0076   0.0036
2024-03    93   -6.12%   +0.1372   -0.1985   +0.0062   0.0038
2024-04    90   +7.00%   -0.1731   +0.2386   +0.0069   0.0038
2024-05    93   -4.53%   +0.0679   -0.1129   +0.0033   0.0042
2024-06    90   +3.20%   -0.1101   +0.1443   +0.0017   0.0039
2024-07    93   -0.87%   -0.0207   +0.0095   +0.0069   0.0038
2024-08    93   -0.67%   -0.1044   +0.0952   +0.0071   0.0038
2024-09    90   +4.58%   +0.1674   -0.1230   +0.0056   0.0040
2024-10    93   +1.39%   -0.0253   +0.0301   +0.0139   0.0038
2024-11    90  +16.44%   +0.3411   -0.1852   +0.0034   0.0039
2024-12    93  +14.13%   -0.0237   +0.1418   +0.0195   0.0037
2025-01    93   +4.28%   -0.0263   +0.0528   +0.0205   0.0035
2025-02    84   -3.03%   -0.1652   +0.1275   +0.0111   0.0033
2025-03    93   -0.31%   -0.1328   +0.1091   +0.0267   0.0042
2025-04    90  +10.36%   +0.1372   -0.0502   +0.0239   0.0043
2025-05    93   -0.38%   +0.0058   -0.0101   +0.0060   0.0044
2025-06    90   -4.90%   -0.0999   +0.0365   +0.0177   0.0039
2025-07    93   +3.68%   +0.0953   -0.0586   +0.0069   0.0044
2025-08    93   -2.51%   -0.0266   -0.0172   +0.0235   0.0040
2025-09    90   -5.30%   -0.0266   -0.0397   +0.0172   0.0038
2025-10    93   +1.90%   -0.0927   +0.1079   +0.0090   0.0040
2025-11    90   +2.19%   -0.1868   +0.1571   +0.0595   0.0037
2025-12    92   +2.49%   -0.0591   +0.0435   +0.0484   0.0038
```
