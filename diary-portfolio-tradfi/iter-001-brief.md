# iter-001 EXPLORATION brief — Dollar-neutral XS-momentum anchor

**Track:** portfolio-tradfi (market-neutral L/S Binance `TRADIFI_PERPETUAL` single-company stock perps)
**Cadence:** EXPLORATION — **IS-ONLY** (`--confirm` NOT passed; `OOS_CUTOFF = 2025-03-24` HIDDEN)
**Role:** quant-researcher design brief (the anchor). Author of record: QR. Implementation/run: QE. Review: Critic.
**One change:** establish the anchor — dollar-neutral cross-sectional 12m-1m momentum, inverse-vol scaled.
**Objective:** **Sharpe** (risk-adjusted, net of cost). NOT absolute return, NOT beating buy-and-hold.

---

## 1. Hypothesis

A dollar-neutral long/short book that goes **long recent winners / short recent losers** on a **12-month-minus-1-month** formation, inverse-vol scaled and vol-targeted to 15%/yr, nets a **positive IS Sharpe** on this TradFi stock cross-section after ~6 bps/side daily-rebalance cost.

Equity-native rationale (this is the most-replicated anomaly in all of asset pricing, not a crypto reflexivity story):
- **Cross-sectional momentum is pervasive and persistent.** Jegadeesh-Titman (1993); Asness-Moskowitz-Pedersen, *Value and Momentum Everywhere* (2013) document it across 40+ years, 8 markets, and 6 asset classes. The premium is paid for **underreaction to gradual information diffusion** (Hong-Stein) plus behavioral frictions (disposition effect, anchoring, herding) — structural, not arbitraged away on a daily-rebalanced single-name book.
- **12-1 is the canonical specification.** Formation over trailing 252 trading days, **skipping the most recent 21 days** to avoid contamination by the well-documented 1-month short-term reversal (Jegadeesh 1990). The anchor's `close.shift(21)/close.shift(252) - 1` is exactly this.
- **Why it survives 6 bps/side daily cost:** 12-1 is a **slow** signal. The weight vector drifts only as the trailing-year ranking drifts, so daily turnover is low and the cost drag is small relative to the long-short winner-loser spread. This is the crux — momentum nets because it is low-turnover, not because it is high-Sharpe gross.
- **Native-short perp = clean edge over cash-equity L/S.** We pay no borrow/locate on the short leg. In cash equities the momentum short leg (prior losers, often hard-to-borrow) is where a large slice of the paper premium is eaten by rebate costs; here it is free. This structurally favors the short leg of the book.
- **Inverse-vol scaling (`mom/rvol`) raises Sharpe** by risk-parity-ing the book (no single high-vol name dominates portfolio risk) and partially harvesting the low-vol anomaly — an additive, Sharpe-positive overlay, not a bug.
- **Dollar-neutral removes the market's first-order drift**, isolating the cross-sectional spread → lower vol → higher Sharpe than a long-only book, and a first step toward the all-weather target (beta/sector neutrality follow in iter-002/003).

**Honest counter-force (pre-registered, not hidden): momentum crashes.** Daniel-Moskowitz, *Momentum Crashes* (2016): in panic-rebound rallies the short leg (prior losers, high-beta) snaps back violently and momentum's residual net-short-beta tilt gets run over. A dollar-neutral book is **not** beta-neutral, so the rebound onsets (notably the April-2020 COVID snapback, possibly Jan-2023 / Nov-2023) are the expected fragility. This is precisely the crash channel iter-002 (beta-neutral) and iter-003 (sector-neutral) target — so iter-001's all-weather bar is **survivability (bounded DD)** through those windows, not peak Sharpe.

---

## 2. Exact signal spec — CONFIRM the anchor as-is (no parameter change for iter-001)

Production signal (`analysis/portfolio/tradfi/iter_001_xsmom.py::xsmom_raw`), run through the leak-safe core (`core_tradfi.net_from_raw`):

```
mom  = close.shift(21) / close.shift(252) - 1.0          # 12m-1m formation, all past
rvol = close.pct_change().rolling(63).std()              # 3m realized vol (VOL_WIN=63)
raw  = nz.dollar_neutralize( mom / rvol )                # inverse-vol THEN cross-sectional demean
# net_from_raw: gross-normalize to 1 -> .shift(1) lag -> Σ w·ret_fwd -> 6bps·|Δw| cost -> vol-target 15%/yr, ≤5x
```

**Decision: confirm verbatim. Change no parameter.** Reasons, all IS-only / no OOS peek:
- **252 / 21 / 63 are canonical, not tuned.** 252-day formation, 21-day skip, 63-day vol window are the textbook UMD/risk-parity defaults. Changing any of them at iter-001 would mean the anchor is hindsight-picked, which the gauntlet (rule 3: structural params proven by robustness sweep, never hindsight-picked) forbids. I have zero IS evidence yet and cannot look at OOS, so the principled choice is the literature default.
- **Continuous `mom/rvol`, NOT rank-terciles.** The anchor uses the continuous inverse-vol score, dollar-neutralized — it uses the full cross-section and avoids arbitrary tercile cutoffs. (Note: the existing `EXPLORATION-001.md` prose says "long top-tercile / short bottom-tercile" — that is stale; the code and `tests` are continuous. The QE/Critic should treat **continuous `mom/rvol`** as the real spec and correct the prose.) Rank-decile vs continuous is a legitimate future EXPLORATION — **not** iter-001 (one change per iteration).
- **Order of operations matters and the anchor's is correct.** Production does `dollar_neutralize(mom/rvol)` (inverse-vol → demean), which guarantees exact Σw=0 on the *scaled* signal. The test helper `_xsmom_raw` uses the opposite order `(mom - mean)/rvol`, which is **not** zero-sum — see §6, this is a leak-test gap, not a spec change.
- **Dollar-neutral ONLY.** Beta-neutral = iter-002, sector-neutral = iter-003. Out of scope here by design.

**Robustness sweep (evaluation aid, NOT a parameter change):** alongside the headline at canonical 252/21/63, QE reports a small neighborhood — lookback ∈ {126, 252}, skip ∈ {10, 21, 42}, vol_win ∈ {21, 63, 126}. **Decision rule, pre-registered: the anchor STAYS at 252/21/63 regardless of which cell scores highest** (cherry-picking the best cell is hindsight). The sweep's only job is to confirm the canonical point sits inside a **positive-Sharpe plateau** (majority of neighbors IS-positive), i.e. the anchor is not a knife-edge. If the canonical point is positive but most neighbors are negative, that is a fragility flag for the diary, not a reason to switch cells.

---

## 3. IS-only success criteria (RELATIVE — this is the FIRST anchor)

The bar is honest and relative: iter-001 only needs to be a **real positive starting point** that subsequent neutrality layers improve upon — not perfect. Concrete tiers on **IS monthly Sharpe (√12-annualized, net of 6bps/side cost)**:

| Verdict | IS net Sharpe | maxDD (IS slice) | All-weather |
|---|---|---|---|
| **Healthy anchor** | ≥ +0.50 | better than -25% | ≥2 of 3 regimes ≥ 0; worst regime bounded |
| **Promotable-direction anchor (default)** | +0.30 to +0.50 | better than -35% | no regime catastrophic (see §4) |
| **Marginal / keep-but-flag** | +0.10 to +0.30 | better than -40% | thin edge; iter-002/003 MUST lift it |
| **REJECT direction-as-specified** | ≤ +0.10 or negative | — | pivot formation/weighting (do NOT quit) |
| **RED FLAG — assume leak** | > +1.0 | — | standalone 12-1 momentum does not net >1.0 Sharpe; treat as a bug until Critic clears both leak tests |

**Calibration note (load-bearing):** standalone XS 12-1 momentum is a **modest** standalone factor — gross annualized Sharpe ~0.4-0.7 in the literature (it shines *combined* with value, not alone). A vol-targeted-15% book at IS net Sharpe ~0.4-0.6 → ~6-9%/yr net is the realistic *expected* outcome and a perfectly good anchor. **A net IS Sharpe above ~1.0 is a red flag for leak, not a triumph** — per the skill's "if a result looks too good, assume a bug until the Critic clears it."

Promotion: a verdict of Promotable-or-better **+ Critic PASS** tags iter-001 CANDIDATE ANCHOR and authorizes CONFIRMATION-001 (which alone reveals OOS via `--confirm`). EXPLORATION never reveals OOS.

---

## 4. All-weather expectation (per-regime, IS-only)

Regimes are the fixed tags in `core_tradfi._REGIMES`. Effective data start is ~mid-2019 (252-day formation warm-up on ~2018 Dukascopy depth), so the pre-COVID bull is thin; the meat is **2022 bear + 2022-23 chop + 2020.04-2022 and 2023.06-2025.03 bull**.

Expected / required profile:
- **Bear (dominated by 2022):** I expect momentum to be **strong** here — in 2022 the prior losers (long-duration tech, unprofitable growth) kept losing and prior winners (energy, value, defensives) kept winning, the ideal momentum tape. **Require bear Sharpe ≥ 0** (and would not be surprised by the *best* regime here). A negative 2022 bear would be a real concern.
- **Chop (2022.10-2023.06):** the expected **weak spot** — choppy reversals are momentum's worst friend. **Require survivable: Sharpe ≥ -0.30 and bounded DD**, not necessarily positive.
- **Bull (the long stretches):** **require positive** — momentum's home regime in trending up-markets. If bull is the *only* positive regime and it is carrying the whole book while bear/chop are deeply negative, that is the single-regime-artifact failure (§8.3).
- **Crash watch:** the coarse regime tags blur the momentum-crash window (the April-2020 COVID *rebound* falls inside the "bull 2020.04+" tag, not the "bear" tag). So per-regime Sharpe alone will not isolate it — QE must additionally report the **worst single monthly return and its date**; if it clusters at a rebound onset (Apr-2020, Jan/Nov-2023) and the DD is bounded, that is the expected, survivable momentum-crash signature and a direct motivation to fast-track iter-002.

**All-weather pass = survivable in every regime (no catastrophic regime), positive in ≥2 of 3.** Peak Sharpe in one regime does not excuse a blow-up in another.

---

## 5. Breadth / trade-rate sanity

- **Point-in-time / ragged starts (already handled, must be verified):** a name's `mom` is NaN until it has 252 days of history; `net_from_raw` gross-normalizes and `.fillna(0.0)` → **a name with insufficient history carries exactly 0 weight**. Recent IPOs (HOOD, RIVN, PLTR, COIN, CRWV, CRCL, ASTS…) enter only from their real listing date — never back-fabricated. Survivorship-safe by construction; the universe is on-disk-ingested names ∩ `SECTOR_MAP`, with no future-data filter.
- **Minimum cross-section for a real market-neutral book:** I require **median active N ≥ 20** (≈10 per side) over the IS window; ideally 30+ in the mature sample. The early window (2019, before most IPOs have 252d) will be thin (~25-40 mega/large caps) and ramp toward ~69 mapped names. QE must report the **N_active time series (min / median / first-active date)** and flag any stretch with N < 20 — those months are not a credible L/S book and should be discounted when reading the regime Sharpes.
- **Concentration sanity:** `mom/rvol` can blow up a single ultra-low-vol name's weight (small rvol denominator). Require **max single-name |weight| ≤ ~15% of gross**; >25% is a concentration pathology (§8.4) motivating rvol-winsorization / per-name cap in a later iteration. Measure and report; do not fix in iter-001.
- **Turnover/cost as the survival metric:** 12-1 should be low-turnover. Expect mean daily Σ|Δw| in the low single-digit-% range; the **net-minus-gross Sharpe gap (the cost drag) should be < ~0.3 Sharpe** for the anchor to be cost-robust. A larger gap means inverse-vol/rank churn is eating the edge → a smoothing/banding EXPLORATION, not a quit.

---

## 6. Leak-check plan (what the Critic MUST verify)

Mandatory dual leak discipline — **future-bar AND same-bar** (same-bar is the exact class that cost the metals track a withdrawn iteration):

1. **Existing tests must pass** (`tests/test_portfolio_tradfi_foundation.py`): `test_future_bar_corruption_does_not_change_past_net`, `test_same_bar_close_cannot_affect_its_own_return`, `test_net_from_raw_dollar_accounting_and_shape`, `test_dollar_neutral_rows_sum_to_zero`, `test_perf_line_hides_oos_by_default`, `test_iter001_build_is_dollar_neutral_and_leak_safe`.
2. **GAP TO CLOSE (Critic action item):** the future-bar and same-bar leak tests (lines 91-126) run against a **local proxy** `_xsmom_raw` that uses a *different* operation order than production — proxy is `(mom - mean)/rvol`; production `xsmom_raw` is `dollar_neutralize(mom/rvol)`. The leak guards therefore do **not** exercise the real signal. **Critic must require the leak tests be extended to call `iter_001_xsmom.xsmom_raw` / `.build` directly**, asserting future-bar and same-bar bit-identity on the production path. Until that exists, the leak proof is on a stand-in, not the shipped code.
3. **Lag is load-bearing — verify it exists.** The only thing between `raw[t]` (which legitimately uses `close[t]` via `rvol`) and the fill is the **`.shift(1)`** in `net_from_raw` paired with a **forward** `ret_fwd[t]=open[t+1]/open[t]`. Confirm: `w[t]=raw[t-1]` (decided from `close[t-1]`), applied to `open[t]→open[t+1]`. Decision strictly precedes fill; corrupting `close[t]`/`high[t]`/`low[t]` must leave `w[s]`,`net[s]` bit-identical for all `s ≤ t`. The metals withdrawal was exactly a missing/insufficient lag here.
4. **No time-series full-sample stats.** Confirm `dollar_neutralize` demeans **cross-sectionally** (`axis=1`, contemporaneous — legitimate), not across time; `rvol` is **rolling** (past), not full-sample; no full-sample z-score / mean / std anywhere in the signal.
5. **Cost realism + net reporting.** Cost = `COST_SIDE·|Δw|` subtracted from PnL **before** vol-target (so cost scales with leverage — correct). Confirm the reported Sharpe is **net**, and that QE also emits **gross** so the cost drag is bounded (§7.2).
6. **OOS gate (mechanical).** The EXPLORATION run (`--confirm` absent) must emit **no** OOS number; `perf_line(reveal_oos=False)` must compute maxDD/netTot over the IS-only slice. Confirm `is_only()` uses strict `< OOS_CUTOFF`.
7. **PIT / survivorship.** No name selected/excluded on full-sample performance; ragged NaN → 0 weight; universe derived from ingested ∩ SECTOR_MAP only.

---

## 7. Numbers the QE run must output (IS evaluation)

All over the IS slice (`< 2025-03-24`); no OOS. Headline first:

1. **IS net monthly Sharpe** (√12) — the verdict number.
2. **IS gross Sharpe** (cost off) → cost drag = gross − net (must be < ~0.3 Sharpe).
3. **maxDD** over IS slice **+ worst single monthly return and its date** (crash-watch, §4).
4. **Per-regime Sharpe** bull / bear / chop **with monthly-bucket counts per regime** (so a thin 1-2-bucket Sharpe is not over-read; COVID-only-bear is tiny).
5. **Per-year Sharpe** (≈2019 … 2025-Q1) — consistency, not just regime buckets.
6. **Turnover:** mean daily Σ|Δw| + annualized one-way + implied annual cost drag (%).
7. **Breadth:** N_active time series — min / median / first-active date; flag stretches N < 20.
8. **Neutrality + leverage:** mean |Σw| net-dollar (≈0 check) and realized gross-leverage (vol-target multiplier) distribution — flag if pinned at 5× cap.
9. **Concentration:** max single-name |weight| distribution / max.
10. **Robustness sweep table** (§2) — IS Sharpe across the lookback/skip/vol_win neighborhood (plateau check; anchor does NOT move).
11. Net total return over IS — **informational only**, never the objective.

---

## 8. Pre-registered failure modes (what makes this NEGATIVE / reject)

1. **Flat/negative edge:** IS net Sharpe ≤ +0.10 → momentum-as-specified does not net on this cross-section. Next EXPLORATION pivots the **formation (lookback/skip)** or **weighting (rank vs continuous, equal-vol vs inverse-vol)** — narrow the search, do not quit the direction.
2. **Cost eats the edge:** gross Sharpe positive but net ≤ 0 with high turnover → signal too fast / inverse-vol churn. Next EXPLORATION = signal smoothing / rebalance banding / lower-frequency rebalance. Diagnostic, not a quit.
3. **Single-regime artifact:** total IS Sharpe positive **only** because one regime (likely the long 2023-25 bull) carries it, while another is catastrophic (regime Sharpe < -0.5 **or** regime DD < -40% in bear or chop). Fails all-weather → fast-track iter-002 beta-neutral (the crash channel).
4. **Concentration / leverage pathology:** a single name > 25% of gross, **or** realized leverage pinned at the 5× cap for most of the sample (vol-target failing) → inverse-vol blow-up. Fix via rvol-winsorization / per-name cap (later iter).
5. **Breadth failure:** median N_active < 20 → book too thin to be a credible market-neutral portfolio. Defer momentum on the early window / widen universe / revisit the 252d history requirement.
6. **Too-good red flag:** IS net Sharpe > 1.0 for standalone 12-1 momentum → **assume a leak** until the Critic clears future-bar **and** same-bar on the *production* signal (§6.2).
7. **Any leak-test failure** (future-bar or same-bar not bit-identical on the production path) → automatic NEGATIVE / withdraw, regardless of Sharpe. No exceptions.

---

## 9. Dependencies / handoff notes

- **Blocked on ingest.** Only 3 of ~69 SECTOR_MAP names (AAPL, JPM, MSFT) are ingested. QE must complete `ingest_dukascopy_stocks.py` for the full mapped universe before the IS run is meaningful; breadth numbers (§7.7) are the readiness gate.
- **Stale-prose cleanup:** correct `EXPLORATION-001.md` to describe the **continuous `mom/rvol`** spec (not terciles) when its numbers are filled in.
- **Next on PASS:** CANDIDATE ANCHOR → CONFIRMATION-001 (reveals OOS, full gauntlet, benchmarks, 1×/2× cost stress) → on Critic PASS, promote to `BASELINE_TRADFI.md`. Then iter-002 = beta-neutral overlay.
