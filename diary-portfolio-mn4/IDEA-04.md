# IDEA-04 — Slow ML Factor (cost-engineered) — Diary

**Track:** MN4 blind tournament. **Idea:** 04 (Slow ML Factor). **Role:** QR+QE pair.
**Model:** Opus 4.8 (Fable user-suspended this phase — charter deviation, disclosed; the charter mandates ALL AGENTS ON FABLE but the user directed "continue on Opus 4.8" for this session. Construction byte-frozen BEFORE any metric read; IS-only throughout; zero holdout reads).
**Construction module:** `analysis/portfolio/mn4_idea04_construction.py` (frozen).
**OOF manifest:** `data/mn4_idea04/oof_manifest.json` (wall 20.2 min, 30 months × 8 configs × 5 seeds = 1200 fits).
**Scorecard log:** `logs/mn4_idea04_score.log`.

---

## Decision: IS-GATE PASS — BANKED FOR REVEAL

The construction clears every principle-anchored IS gate. The 2×-GT Sharpe is positive (+0.844), the OOF IC is overwhelming (+0.0509, t=+13.57), the CRASH regime is positive (+33.2%), and the leak battery is clean. This is banked for the Phase-B reveal — one holdout look.

---

## 1. Construction one-liner

LightGBM walk-forward (monthly, 24mo window, 8×5 grid, purge=21) predicting the 21-candle forward residual total return from 24 crypto-native features; continuous demeaned-rank weights + BTC minimal-L2 beta projection; weekly rebal=21 phase 0; dd_brake crisis throttle (−15%/flat/−7.5%); honest 5+2.5bps + funding + 2×-GT twin.

## 2. IS headline (the numbers that matter)

| metric | value |
|---|---|
| **OOF pooled rank-IC** | **+0.0509** (t=+13.57, n=2715) |
| **Sharpe 1× cost** | **+1.017** |
| **Sharpe 2×-GT** | **+0.844** |
| **maxDD (1×)** | **−50.4%** ← the honest risk |
| **turnover** | 27.3× annualized (one-way) |
| **b_BTC** (full / CRASH / MANIA) | **+0.0071 / +0.0161 / +0.0040** |
| **CRASH regime** | +33.2% (t=+1.74) |
| phase-agnostic mean Sharpe | +0.557 (17/21 positive) |
| leak battery | ALL PASS (purge 30/30, corrupt-future BIT-IDENTICAL) |

## 3. What worked

1. **The edge is real and strong.** OOF rank-IC +0.051 at t=+13.57 over 2715 scored candles is not noise. The 21-candle (weekly) residual-total label captures a slower, more persistent alpha than the 3-candle (24h) MN3-G fast label — exactly the "slow ML factor" hypothesis. The per-config IC band (+0.046 to +0.050 across 8 configs) is remarkably tight, confirming the edge is NOT an HP-overfit artifact.

2. **Cost-survival by construction.** The 2×-GT twin delivers +0.844 Sharpe — the charter names cost as the binding constraint on this dataset, and this construction clears it. The slow label + continuous demeaned-rank weights + weekly rebal suppress turnover to 27.3× annual (vs MN3-G-SLOW's 63× on holdout). The cost-coverage spread (1×−2× = +0.173) is modest.

3. **BTC beta projection works.** Realized β_BTC = +0.0071 full-sample, +0.0161 in CRASH, +0.0040 in MANIA. `post_cap_target_beta_mean=0.0000` — the minimal-L2 projection fires cleanly at every rebal (0 degenerate, 0 collapse, 130/130 projected). This is the structural difference vs MN3-G-SLOW (which had no beta overlay), and it shows.

4. **All-weather.** CRASH +33.2% (t=+1.74), CHOP +13.9% (t=+1.97), MANIA −7.4% (t=−0.70). Positive in CRASH is the property the charter demands ("a winner in EVERY market condition"). The crisis throttle fired 31 times and the book STILL delivered +33.2% in crashes — the alpha survives de-risking.

5. **Phase robustness.** 17/21 phases positive. Phase 0 (+1.017) is above the phase-agnostic mean (+0.557) but the edge is NOT phase-dependent (cf. the rebal-phase feedback: /005's +0.91 was 3/21 phase luck — here 17/21 positive).

## 4. What failed / honest risks

1. **maxDD = −50.4% is high.** This is the main OOS risk. The dd_brake (−15% trigger, flatten, −7.5% release) fires 31 times but the DD is the intra-week PATH risk — the brake only acts at weekly rebals, so a fast crash deepens the DD before the next flatten. Disclosed honestly; NOT tightened (a −10% trigger would be IS-fit). The CRASH regime is +33.2%, so the book is NOT blowing up in crashes — it's the path, not the regime.

2. **Phase 12 is negative (−0.557).** One of 21 phases is notably negative; 3 others are low-positive. The phase-agnostic mean (+0.557) is the honest headline for OOS expectations, not phase 0's +1.017.

3. **MANIA regime is slightly negative (−7.4%, t=−0.70).** The market-neutral book doesn't capture mania upside. This is EXPECTED and acceptable for a neutral factor, but it means the book underperforms in pure-mania holdout windows.

4. **Shared DNA with MN3-G-SLOW.** This construction uses the same 24 features + 21c label + purge=21 + 8-config grid as the failed MN3-G-SLOW holdout reveal (net2x −0.28, maxDD −35.9%, crash_net_t −1.59 on holdout). The structural differences (BTC beta overlay, full ensemble, engine rank_neutral weights, dd_brake, weight_cap) are meaningful, and MN3-G-SLOW's failure mode (crash blowup) is exactly what the dd_brake + beta projection address. But the honest prior is that the underlying alpha is partially shared — the holdout will decide whether the structural additions convert it to a generalizer.

## 5. Leak battery (charter mandate — proportionate, ALL PASS)

| check | result | evidence |
|---|---|---|
| purge assert (21c horizon) | PASS | 30/30 months, max overlap 0 candles; `assert_no_label_overlap` |
| corrupt-future (fit loop) | PASS | BIT-IDENTICAL (max abs diff 0.00e+00); corrupting features at grid ≥ mid-IS leaves prior-month predictions unchanged |
| corrupt-future (label) | PASS | rows < t0−21 bit-identical after future corruption (unit-tested) |
| decision-lag [k−1] | structural PASS | OOF signal[t] trained on data ≤ t−22; engine consumes signal[k−1] |
| injected-leak positive control | PASS | label vs label_raw IC = +1.0000 (harness detects leakage) |
| PIT cross-sectional membership | PASS | `pit_topn_universe` (no survivorship backfill) |
| OI consumed at .shift(1) | PASS | asserted in mn3_features, inherited |

The purge=21 is the load-bearing leak-safety check. The charter text says "3-candle purge" (copy-paste from MN3-G fast); the charter's MANDATORY leak battery says "verify NO train/OOF label overlap at the 21c horizon" — the leak battery wins. A 3-candle purge with a 21-candle label would leak 18 candles/month. purge=21 eliminates the overlap exactly (unit-tested: purge=3 produces overlap for ALL 30 months; purge=21 produces zero).

## 6. Why this generalizes (the OOS prior)

- **The IC is t=+13.57**, not t=+2.5. Even with a 5× haircut for tournament multiplicity (10 ideas), the edge survives.
- **HP-insensitive** (8-config IC spread 0.0036). Not a knob-tuning artifact.
- **Seed-stable** (5-seed IC spread 0.009). Not a basin-lottery hit.
- **Cost-surviving at 2×** (+0.844). The binding constraint on this dataset is cleared.
- **All-weather** (positive in CRASH and CHOP, the two most populous buckets).
- **BTC-neutral by measurement** (β=0.007), not by assumption.

## 7. Why this might NOT generalize (the honest counter-priors)

- **MN3-G-SLOW failed on this exact holdout** with the same features + label. The structural additions (beta overlay, dd_brake, full ensemble) are genuine but untested on holdout.
- **maxDD −50.4%** on IS. If the holdout has a fast crash that the weekly brake can't catch, the DD could be worse OOS.
- **The feature set is 4-year-old crypto structure** (funding/OI/taker). If the 2024-2026 holdout regime is structurally different (e.g., ETF-driven institutional flow diluting retail-driven funding/taker signals), the IC may decay.

## 8. Next iteration ideas (if revealed FAIL)

1. **Daily rebal (rebal=3) with the same 21c label** — contains the maxDD by acting faster, at the cost of higher turnover (the 2×-GT twin decides if it survives).
2. **Meta-label** (the charter seed's "optional meta-label") — a binary classifier on top of the regression signal to filter low-conviction weeks; could lift the win rate and contain the DD.
3. **Tighter dd_brake (−10% trigger)** — would contain maxDD but costs alpha in the recovery; measure the tradeoff IS-side as a diagnostic, NOT a gate.
4. **Feature-set refresh** — add on-chain / ETF-flow features if the 2024-2026 regime shift is the failure mode.

## 9. Process notes

- **Zero holdout reads.** Everything through `mn3_slice_is` + `mn3_guard_grid`. The 2-year holdout [2024-07-01, 2026-07-01) is pristine and sealed.
- **No git commit** (orchestrator commits centrally).
- **No shared files touched.** All artifacts in `mn4_idea04_*` / `data/mn4_idea04/` / `briefs-portfolio-mn4/IDEA-04.md` / `diary-portfolio-mn4/IDEA-04.md` / `tests/test_mn4_idea04_*`.
- **Tests:** 11/11 pass (`tests/test_mn4_idea04_construction.py`). Ruff: all 4 files clean.
- **Compute:** OOF generation 20.2 min (1200 LightGBM fits); scorecard ~3 min (21 phase sweeps + leak battery).

---

**Bottom line:** banked for reveal. The IS edge is strong, cost-surviving, all-weather, and leak-clean. The maxDD is the honest risk. One holdout look will decide whether the structural additions (beta overlay + crisis throttle + full ensemble) converted the MN3-G-SLOW alpha into a generalizer — or whether the shared DNA dooms it. Either way, this is the methodology working.
