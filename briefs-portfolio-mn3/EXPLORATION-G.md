# EXPLORATION-G — Family-G flagship, turnover-suppressed reformulation (horizon-matched slow label; MN3; IS-only; pre-registered)

**Track:** MN3 (two-year-holdout market-neutral). **Date:** 2026-07-11. **Author role:** Quant
Researcher. **Stage:** Stage-1 IS design-validation. **IS window:** 2020-01-01 → 2024-06-30
(`mn3_split` cutoff `MN3_IS_CUTOFF_MS = 2024-07-01`). **Holdout (2024-07-01 → 2026-06-30) is SEALED
and untouched** — this brief neither reveals nor references any holdout metric; family-G's
one-forever token `MN3-G` is NOT spent by this EXPLORATION (Stage-1 is IS-only by construction;
`reveal_token=None`; `REVEAL-LEDGER.md` stays at zero spends).

> **MODEL-NOTE (charter deviation, disclosed).** The MN3 charter mandates ALL AGENTS ON FABLE. The
> Fable mandate is **user-suspended for this phase** (Fable-5 rate limit; user direction: "continue
> on Opus"). This brief was authored on **Opus 4.8**, not Fable. Pre-registration integrity is
> unaffected: the construction, gates, throttle, cost stress, falsification arms, decision map, and
> ledger are FROZEN in this document BEFORE any EXPLORATION-G backtest runs; nothing has been
> revealed; the holdout is sealed. Same posture as DIAG-G / EXPLORATION-S4. This brief goes to a
> Critic pre-flight next, then a QE re-run (Lever B retrain) + a QR/QE scored engine run.

**Freeze statement.** Every construction detail, gate, threshold, throttle constant, suppression
constant, cost-stress arm, falsification arm, and decision-map tier below is FROZEN as of this
document. Any change after the Critic pre-flight requires a dated `EXPLORATION-G-AMENDMENT-NNN`
section recorded BEFORE the scored run — never an in-place edit, never a post-hoc re-gate. A fired
gate is final.

**Provenance.** DIAG-G scored family-G's LightGBM cross-sectional residual-alpha flagship and killed
it on **kill (d) — economics ONLY** (`DIAG-G.md`): the signal is the **strongest, most stable, most
crash-robust the MN/MN3 effort has measured** — pooled OOF cross-sectional IC **+0.0369** (config
**c1**), positive in **all 3 OOF years and all 5 seeds**, CRASH-bucket quintile-spread **t +3.21**
(significantly RIGHT-signed) — but its weekly top/bottom-**quintile** book churns **156.6×/yr
(~3.0 Σ|dw| per rebal — MORE than a full flip each week)** and its phase-agnostic 2×-cost net spread
is **−5.3%/yr**. Kills (a)/(b)/(c)/(e) all PASS; only (d) fired. The signal is real; the **trade** is
not — the 24h-label ranking re-forms faster than the weekly book can pay to chase it. DIAG-G §5
explicitly deferred the turnover-suppressed reformulation to the orchestrator/user as a **NEW
pre-registered construction** that "shares family G's one-forever holdout token, requires its own
EXPLORATION brief, Critic pre-flight, and frozen decision map." **The user chose this reformulation
as the highest within-dataset prior.** This brief is that construction. It invokes family-G's ONE
permitted revision round (PLAN §3.1 cap-16 clause), now user-authorized.

---

## Section 0 — Contamination / governance disclosure (§1.3 verbatim; family-G row)

**Family-G row (PLAN §1.3), verbatim:** *"G ML residual alpha — univariate ICs of constituent
feature classes (funding/taker/OI/resid-mom) were measured here as MN-v2 IS (DIAG-A/C/D/E1) [W1–W2];
same + vol_low book P&L revealed (different, closed mechanism) [W2]; never evaluated [holdout].
**Sealed-as-achievable.** Feature-class univariate-IC knowledge over W1–W2 is in-head and shaped the
§3.1 feature list; disclosed. No G book has ever touched any of it."*

**Reformulation-specific read (the honest, narrow truth):**

1. **This is a re-parameterization of family G — it shares `MN3-G` FOREVER (PLAN §6.1 anti-gaming).**
   It earns NO new token. A future Stage-2 reveal of this construction spends `MN3-G` and burns
   family G's entire holdout budget (§7). **This EXPLORATION spends NO token** (IS-only; guard fires
   with `reveal_token=None`).
2. **The 24-feature list, the 8-config grid, the 5 seeds, and config c1 are all INHERITED
   VERBATIM from DIAG-G** (Critic-ratified, frozen). No feature is added, dropped, or re-selected.
   The only change to the SIGNAL is the **label horizon** (§0.5, §1). The feature-class knowledge
   from W1–W2 that shaped the list is already-disclosed in-head IS knowledge; it is unchanged here.
3. **Regime-composition leak (disclosed, confronted).** As QR I hold in-head knowledge that the
   holdout is 2025-11→2026-06 crash-heavy, 2026-H1 mania-free (§1.3 self-disclosure). G is
   crash-ROBUST (CRASH t +3.21), so a naive reader could suspect I am steering a crash-hardened book
   at a known crash-heavy holdout. The four §1.3 defenses neutralize this and are pre-registered
   below: **(i)** market-only regime bucketing (frozen `mn3_regimes`); **(ii)** the §6 decision map
   pre-commits its interpretation before any reveal; **(iii)** every threshold is
   principle/relative-anchored, NEVER fitted to G's revealed IS economics (esp. the suppression
   constant — §0.5 — anchored on horizon-matching, NOT on G's −5.3% cost wall); **(iv)** the
   all-weather EDGE read is the arbiter (§4 G-crash-preserve), and — the load-bearing addition here —
   **a slow book that clears cost by ABANDONING G's crash edge is a FAIL, not a win.** G's
   crash-positivity was measured IS-only in DIAG-G and is PREDICTED a-priori by the mechanism (the
   crowding-syndrome features flag the squeeze side hardest when liquidity is scarcest), not
   reverse-engineered from holdout knowledge.
4. **Killed-at-mechanism families stay closed:** vol_low, pairs-persistence, taker-standalone,
   resid-mom-standalone, OI-fade. The DIAG-G §4 honest note (`range9_xz` rhymes with closed vol_low
   direction) is carried forward: the S3-C4 flag on `rvratio_xz`/`rv_ownpctl` was NEGATIVE in DIAG-G
   (both near the bottom of model loading); the reformulation changes nothing about the feature set,
   so the S3-C4 disposition is UNCHANGED (re-reported, not re-litigated). The R1 `mkt_fund_agg`
   level-z definition remains locked-immutable as ratified.

---

## Section 0.5 — THE LEVER DECISION: Lever B (horizon-matched slow-label retrain) + non-mining justification

The mandate is to pick ONE primary turnover-suppression lever and freeze it. **I choose Lever B —
the slower-label retrain — and DECLINE the Lever-A no-trade band, even as a secondary arm.** The
reasoning is a root-cause argument, not a preference:

**DIAG-G's failure is a HORIZON-MISMATCH failure, not a signal failure.** The model is trained to
forecast a **3-candle (24h) forward return**, but the book **holds for 21 candles (1 week)**. By
day 2–3 of the hold, the 24h-ahead forecast that put the position on is stale, so every weekly rebal
re-ranks on a fresh, near-independent 24h forecast → **~3.0 Σ|dw| per rebal (>full flip), 156×/yr.**
The turnover is the mechanical shadow of a forecast horizon far shorter than the holding period.

- **Lever A (no-trade band on the frozen fast c1 signal) treats the symptom while fighting the
  disease.** A band cuts turnover only by HOLDING positions past the point the fast model still
  endorses them — i.e. holding stale, decayed alpha. And DIAG-G's own number forecloses it: the
  target re-forms **more than fully each week** (Σ|dw| ≈ 3.0 > 2.0). A band on a target that
  fully re-forms weekly has **no sweet spot** — small band ⇒ names still cross it (moves are large)
  ⇒ little turnover cut; large band ⇒ grossly stale positions ⇒ alpha destruction. This is exactly
  the risk the mandate names ("band-holding a fast 24h-horizon target may hold stale positions
  against a fast-decaying signal → lose alpha"), and DIAG-G's >full-flip churn is direct evidence the
  band is the WRONG tool for THIS failure mode. Lever A is DECLINED as primary.

- **Lever B fixes the disease at its root.** Retrain the SAME 24-feature model + config c1 on a
  **21-candle (weekly) forward residual label**. A 21-candle forward return is an intrinsically
  slower-moving, smoother target (it integrates over the week, averaging out the high-frequency noise
  the 3-candle target chases), so its cross-section re-orders far more slowly week-to-week — turnover
  falls at the root — AND, decisively, **the alpha now persists over the hold because the forecast
  horizon IS the holding period.** No stale-alpha problem: the position is put on to harvest the very
  return it is held to collect.

**The ONE principle-anchored suppression constant, and its anchor.** The suppression is the label
horizon **H = 21 candles**, anchored on the **horizon-matching principle** (Grinold–Kahn: the IC that
pays is the IC over the *holding period*; the forecast horizon must equal the rebalance/hold
horizon). H is set **equal to the book's pre-existing weekly cadence** (rebal = 21 = 7 days × 3
candles/day at 8h — itself the crypto-native weekly cadence, three funding cycles/day × a 7-day
week). **H is NOT fitted to G's economics:** it is derived entirely from the book's own inherited
weekly hold; a band width or cadence chosen to "just clear the −5.3% cost wall" would be mining, and
H=21 is provably not that — it is the hold, full stop. DIAG-G rebalanced weekly (21) on a 3-candle
label (mismatch); the reformulation makes label = hold = 21 (matched). That is the whole
construction.

**Secondary arm DECLINED (DOF discipline).** I register NO Lever-A band as a secondary arm. A band on
TOP of the slow-label book would be a second turnover-suppression DOF, and choosing band-on vs
band-off by whichever clears cost is cadence/mechanism-selection-by-outcome — banned mining
(PLAN §3.1). The slow label is the root fix: if it works, no band is needed; if it fails the cost
wall, a band on an already-slow signal is a within-scope tweak for a FUTURE iteration, not a
pre-registered arm here. **One construction, one suppression constant (H=21).**

**QE cost of Lever B:** a ~12-minute OOF re-run (§9.1). Disclosed and specified precisely.

---

## Section 1 — Frozen construction (engine-level; `blind_engine.run_backtest`, NOT diagnostic scoring)

### 1.1 Signal source — retrained family-G, horizon-matched (FROZEN)

Everything is DIAG-G's frozen spec EXCEPT the two horizon-linked constants (`LABEL_FWD_K`,
`MN3_G_PURGE_CANDLES`) and the winsor cap (√-horizon-scaled). No feature, no HP, no seed, no config,
no window changes.

| Element | Frozen value | vs DIAG-G |
|---|---|---|
| **Model** | LightGBM, 24 pinned features `MN3_G_FEATURE_COLUMNS` (position-pinned), fixed params (lr=0.05, n_est=300 no early stop, feature_fraction=0.8, bagging 0.8/freq1, deterministic) | **IDENTICAL** |
| **Config** | **c1** (num_leaves=15, min_data_in_leaf=200, lambda_l2=10) — DIAG-G's selected winner, **PINNED A-PRIORI** (not re-selected on the slow label; see §8) | **IDENTICAL config; not re-searched** |
| **Seeds** | {42, 123, 456, 789, 1001}; prediction = **seed-ensemble mean** | **IDENTICAL** |
| **Label** | forward **21-candle** (weekly) residual TOTAL return (price + funding), winsorized at **±0.53** (= ±0.20·√(21/3)) | **CHANGED: horizon 3→21; winsor √-horizon-scaled** |
| **Purge** | **21-candle** purge at every train/OOF boundary (= label horizon, standard convention) | **CHANGED: 3→21** |
| **Walk-forward** | monthly retrain, trailing **24-month** window (house sacred constant); first OOF 2022-01; OOF span 2022-01 → 2024-06 (last 21 candles unlabeled) ≈ **30 months / ~2.5 yr** | **IDENTICAL window; span −21c tail** |

**Winsor √-horizon anchor (the one derived constant, principle-anchored NOT fitted).** DIAG-G's ±0.20
was "an a-priori L2 sanity cap on fat tails" for a 3-candle return. A 21-candle residual return has
≈√7 ≈ 2.65× the typical magnitude, so a fixed ±0.20 would clip a large fraction of *legitimate*
weekly moves — precisely the fat tails where the crash edge lives — and would DAMAGE the
crash-preservation the reformulation must protect. Scaling by √-horizon (±0.20·√(21/3) ≈ ±0.53)
preserves the SAME distributional clip-fraction as the fast label. This is a √-time vol-scaling
anchor, disclosed, not a scanned/fitted DOF.

### 1.2 Weighting — continuous IC-proportional, dollar-neutral, BTC-only minimal-L2 projected (FROZEN)

This is the reformulation's book form. It is BOTH the Grinold-optimal linear-IC weighting AND
turnover-reducing vs DIAG-G's quintile-extreme sort (a smooth cross-section instead of a hard 8-vs-8
boundary whose names flip 0↔full). It is directly the existing engine's default builder — **no code
change**.

1. **Continuous rank-demeaned weights** — feed the **continuous** c1-slow seed-ensemble prediction as
   `signal` to `blind_engine.run_backtest(weighting="rank_neutral", ...)`, which calls
   `target_weights` (`blind_engine.py:141`): per candle, cross-sectional rank of the prediction over
   live members, **demean the ranks** (→ dollar-neutral), normalize to Σ|w| = gross. This is the
   full-cross-section IC-proportional book (contrast DIAG-G, which fed a quintile STEP signal ⇒
   extreme 8-vs-8 equal-weight; here the continuous prediction ⇒ graded weights across all ~40 names,
   the lower-turnover Grinold weighting).
2. **Beta neutralization (weight-level, BTC-only minimal-L2)** — `apply_beta_neutralization`
   (`blind_engine.py:420`), rolling BTC β from `mn_beta.rolling_beta` (ref=BTCUSDT, window 270,
   min_periods 135, shrink λ=0.33, clip [0,3]), consumed at **[k−1]**; degenerate-β + collapse
   guards (frozen). Passed via the engine's `beta_neutralize=` hook. This is the EXACT S4 R1 pattern.
   *(Note — no double-neutralization: the residual LABEL shapes what the model LEARNS [idiosyncratic
   alpha]; the weight projection ensures the EXECUTED book's realized β ≈ 0. Complementary, exactly as
   S4 did — label residual + weights BTC-projected.)*
3. **Per-name cap** `|w_i| ≤ 0.10·gross`, iterative same-leg pro-rata (`apply_weight_cap`) — safety
   rail; a binding cap signals a universe/projection anomaly to report.
4. **min_members = 20** (skip a rebal when finite-signal members < 20 — DIAG-G's `MIN_MEMBERS`).
5. **gross = 1.0** (Σ|w| = 1.0 → 0.5 long + 0.5 short, the unit dollar-neutral MN book). **Net Sharpe
   is invariant to gross** (a positive scalar on both return and cost); the −25% maxDD gate is a
   per-unit-gross bound at gross=1.0. No vol-targeting (fixed-gross, track convention; avoids a DOF).

### 1.3 Cadence, costs, phase sweep (FROZEN — horizon-matched)

| Element | Frozen value |
|---|---|
| **Rebal** | weekly = **21 candles** (= the label horizon H — the horizon-match, §0.5) |
| **Phase sweep** | full **21-phase** equal-weight tranche ensemble; **phase-agnostic mean is the ONLY headline** (single-phase numbers never load-bearing — the /005 phase-luck lesson) |
| **Costs (1×)** | `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)` — 7.5 bps/side on Σ|dw| + funding on every leg |
| **Costs (2× GT twin)** | `CostModel(10.0, 5.0, funding_enable=True)` — **full engine re-run** (GROUND-TRUTH, not analytic; the throttle/projection make the book non-stateless) |
| **Universe** | PIT top-40 by trailing 30c mean quote-$-volume, ex-stablecoins, ≥270c history (the DIAG-G universe the OOF was generated on) |
| **Signal source** | the FROZEN retrained parquet `data/mn3_g_slow/oof_predictions.parquet`, config c1 seed-ensemble mean (§9.1) |

### 1.4 Engine wiring (the S4 harness pattern, VERBATIM — no engine core change)

Per-phase tranche (`run_tranche` pattern of `mn3_exploration_s4.py`), front-trim + slice, then:
```
run_backtest(panel_is, signal=pred_c1_slow, universe, cost=COST_1X,
             gross=1.0, rebal=21, weighting="rank_neutral",
             weight_cap=0.10, min_members=20,
             beta_neutralize=rolling_beta(panel_is),      # [k-1] internally
             funding=load_funding(panel_is),
             gross_scalar_series=<LCDD-z scalar | None>)   # §2
```
21-phase equal-weight tranche ensemble on the common all-tranches-finite scored mask; phase-agnostic
mean = headline. GT 2× twin = identical call with `COST_2X`. Reproducibility assert (S4 §1.2(5)
analog): the engine book's realized β must be ≈ 0 (G1a/G2 verify) — the residual-alpha intent
executed honestly.

---

## Section 2 — Crisis defense: Layer-2 per-construction throttle (AMENDMENT-002 §C; FROZEN)

### 2.0 Why Layer-2 only + the crash-robust disposition

Per `CRISIS-FALSIFY-003` + AMENDMENT-002 §C/§D: **both shared crisis floors are DEAD by their own
frozen bars** (Layer-1 GAP-only: 25>16 entries, off-episode 4.1%>3%; Layer-B DD-from-peak: 12.5%>8%,
S+C 27.6%>25%). The binding doctrine is the **§C per-construction Layer-2 throttle ONLY** (no
`s_gap`, no `s_dd`; effective scalar = `min` degenerates to `s_con`). §C is a TRACK INVARIANT: every
construction pre-registers a throttle + thresholds + falsification arm. This brief does so — **but G
is crash-ROBUST (CRASH t +3.21)**, so, exactly as the S4 precedent established, a downside throttle
will very likely fire in G's PROFITABLE crashes. The throttle is therefore pre-registered WITH a MECE
disposition that lets the data decide, and — diverging from S4's C1, justified below — a
THROTTLE-HURTS result ships throttle-off and **remains SUCCESS-eligible** because G defends via
*measured crash-robustness*, not via the throttle.

### 2.1 The G-LCDD-z throttle — SCUD structural mirror, re-pointed to G's exposed cohort (FROZEN)

The exact structural mirror of the sanctioned A3 SCUD primitive (`mn_scud`), re-pointed to G's
exposed leg. G's book longs the top-predicted names; its adverse tail is a systemic dump of the
cohort it is most-long. At each candle t:
1. **Exposed cohort** `L_t` = live members whose **c1-slow prediction** is in the **top q=0.33
   fraction** (the names G longs most). Require `|L_t| ≥ m_min = 5`; else forward-fill last valid
   indicator (throttle = 1.0 over warmup where the book is flat).
2. **Trailing return** per cohort name `rᵢ = close_i[t]/close_i[t−h] − 1`, `h = 9` (3 days). Past-only.
3. **Downside-dispersion** `D[t] = −P25{rᵢ : i∈L_t}` (robust lower-tail; higher D = the long cohort
   selling off harder).
4. **Z-score** over `W = 90` (min_periods 45): `LCDD_z[t] = (D[t] − mean_W)/std_W`, clip [−5, +5].

**Ramp (reuse `mn_scud.scud_ramp`, constants VERBATIM):** `τ_lo = +0.85` (≈80th pct, no throttle
below), `τ_hi = +1.65` (≈95th pct, full de-risk at/above), floor **φ = 0.50** (halve gross in the
worst dump — keep the book ON; G earns in crashes). `scalar(z) = 1 − (1−φ)·clip((z−τ_lo)/(τ_hi−τ_lo),
0, 1)`. Release automatic/continuous; consumed at [k−1].

**Constant provenance (INHERITED with disclosure, NOT refit).** Every constant (`q=0.33`, `m_min=5`,
`h=9`, `W=90`, `min_periods=45`, clip ±5, `τ_lo=0.85`, `τ_hi=1.65`, `φ=0.50`) is carried VERBATIM
from the sanctioned A3 SCUD spec. **The ONLY changes from SCUD are the leg (top-0.33 by G's
prediction — G's exposed long cohort) and the tail (P25 downside).** τ are standard-normal percentile
anchors that transfer distribution-agnostically to any z-series. Report-don't-tune rule inherited: a
gross coverage mismatch (scalar<1 on >40%, or mean scalar <0.80) is REPORTED, never tuned.

**Neutrality preserved by construction.** A positive scalar `s∈[φ,1]` on a dollar/beta-neutral book:
`Σ(s·w)=0`, `Σ(s·w)·β=0` EXACTLY. The throttle can only scale gross, never break neutrality.

### 2.2 Disposition — MECE priority partition (C2 form) + the crash-positivity divergence from S4-C1

Sign convention (C2): **Δmaxdd = (un-throttled depth) − (throttled depth)** (>0 = throttle made DD
shallower); **s = Sharpe(throttled)/Sharpe(un-throttled)**. Evaluate in this order (first match wins;
exhaustive, non-overlapping):
1. **THROTTLE-HURTS** if `Δmaxdd < 0` **OR** `s < 0.90` → **as-shipped book = throttle-OFF.**
2. else **THROTTLE-HELPS** if `Δmaxdd ≥ +2pp` **AND** `s ≥ 0.90` → as-shipped = throttled.
3. else **THROTTLE-NEUTRAL** (residual: `Δmaxdd ∈ [0,+2pp)` AND `s ≥ 0.90`) → as-shipped = throttled.

**The as-shipped book (one, per this partition) is the object ALL §4 gates and §5 controls score.**

**DELIBERATE, JUSTIFIED DIVERGENCE from S4's C1 (flagged for the Critic).** In S4, THROTTLE-HURTS
capped the tier at MARGINAL, because S4's tier was about whether a *marginal-edge liquidity book*
could be a clean candidate, and a throttle that hurt signaled its tail-risk-shaping was unsolved. **G
is different: G is crash-ROBUST (measured t +3.21), and its risk defense is that measured
crash-positivity, gated directly (G-crash-preserve, G4, G-maxdd) — NOT the throttle.** The §C throttle
for G is a *required falsification* of "could a downside throttle improve G's tail?", and the
a-priori + S4-empirical answer is "no — a downside throttle HURTS crash-positive books." That is a
CONFIRMATORY finding (the crash edge is real and must not be throttled), not a primitive failure.
Therefore for G a **THROTTLE-HURTS → throttle-off as-shipped book REMAINS SUCCESS-eligible**; the
throttle disposition does NOT independently cap the tier. §C is satisfied by pre-registration +
falsification of the throttle; MECE is preserved because there is exactly ONE as-shipped book and the
tier is a pure function of the gates/controls on it (§6). **Pre-registered PREDICTION: THROTTLE-HURTS
→ ship throttle-off** (G crash-robust; S4's identical LCDD-z came back HURTS on a *less* crash-positive
book).

### 2.3 Throttle falsification arm (§C requirement; leak battery + IS behavior)
- **Leak battery:** corrupt-future positive control on `LCDD_z` (rows ≥ t corrupted ⇒ `LCDD_z[<t]`
  bit-identical); decision-lag [k−1]; append-invariance; inert-default byte-identity (scalar None ≡
  ones ⇒ engine bit-identical). Reuse the `mn_scud` corrupt-future harness.
- **IS coverage (report, coverage-anchored):** fraction scalar<1 (~15–25% at τ_lo=80th), fraction =φ
  (~3–8% at τ_hi=95th), mean scalar (~0.90–0.96). Gross departure (>40% / mean<0.80) ⇒ REPORT.
- **HELPS/NEUTRAL/HURTS forensic:** within-run throttled-vs-unthrottled Δmaxdd, s, and a
  throttle-active-window mean-return read (are throttle-active windows G's LOSING windows [good] or
  WINNING/crash windows [bad — the a-priori-predicted HURTS mechanism]?).

---

## Section 3 — Honest cost stress (FROZEN)

G's book is a **full-cross-section continuous book across the liquid top-40**, NOT a thin-cohort
liquidity book (contrast S4). So the honest primary cost object is the **symmetric GT 2× twin**, and
the S4-style asymmetric thin-name stress is INFORMATIONAL unless the book measurably tilts illiquid.

### 3.1 CS-2× — symmetric GT twin (load-bearing) — HARD (= G-2xcost, §4)
Full engine re-run at 10+5 bps/side both legs + funding. **This is THE gate DIAG-G's quintile book
FAILED (net2× −5.3%/yr).** Pass bar in §4.

### 3.2 CS-3× — symmetric over-stress (corroboration) — SOFT
Full re-run at 15+7.5 bps/side. Report: net Sharpe > 0. Cost-robustness margin.

### 3.3 Thin-name tilt diagnostic + CS-A (informational; ledger-neutral)
Report the **mean `dvol_rank` of the long leg minus the short leg** (weighted by |w|; 0–1 rank scale).
G's continuous demeaned-rank book is balanced by construction, so a large illiquid-long tilt is NOT
expected. **Pre-registered materiality threshold: if |long−short leg mean dvol_rank tilt| > 0.25**
(the long leg systematically thinner), then the **CS-A asymmetric arm** (long leg 3× = 22.5 bps/side,
short leg 1× = 7.5 bps/side, full GT re-run) net-2× annualized return > 0 is CONSULTED as a **disclosed
MARGINAL-consideration** in the diary (S4's thin-name lesson honored), NOT a mechanical HARD gate —
because G is not a structurally-thin book. If the tilt is ≤ 0.25, the symmetric 2× twin is the honest
cost object and CS-A is reported for completeness only. Ledger-neutral (no design choice keys off it).

---

## Section 4 — Full HARD gate set (adapted from S4's 13-HARD; economics + all-weather load-bearing)

Evaluated on the **as-shipped book** (§2.2). Neutrality via `mn3_regimes` frozen buckets (trailing-90c
BTC return; CRASH ≤ −15%, MANIA ≥ +25%, else CHOP; any bucket n<30 ⇒ loud N/A-FAIL). β by OLS of book
net return on BTC/ETH 8h returns. **Every threshold is principle/relative-anchored — NONE fitted to
G's revealed IS economics.**

| # | Gate | Threshold | Class | Falsifier (what a FAIL means) |
|---|---|---|---|---|
| **G1a** | rolling-270 \|β_BTC\| | ≤0.10 on ≥95% post-warmup **AND** max ≤0.20 | NEUT-HARD | the weight projection doesn't neutralize BTC β, or the "edge" is BTC beta |
| **G1b** | rolling-270 \|β_ETH\| | ≤0.15 on ≥95% **AND** max ≤0.25 | NEUT-HARD | BTC-only projection leaves material ETH exposure |
| **G2-CRASH** | bucket \|β_BTC\| in CRASH | ≤0.15 | NEUT-HARD | G's +3.21 CRASH edge is directional beta, not neutral alpha — the doctrine's central crash falsifier |
| **G2-MANIA** | bucket \|β_BTC\| in MANIA | ≤0.15 | NEUT-HARD | book takes beta in mania → not all-weather neutral |
| **G3** | \|Σw\| at every rebal (post-projection+cap) | ≤0.10·gross | NEUT-HARD | dollar-neutrality broken by cap/projection interaction |
| **G4** | worst-bucket mean net-return t (CRASH/MANIA/CHOP) | t > −1.0 | NEUT-HARD | a regime loses significantly → not all-weather |
| **G-signal-IC** | slow-c1 pooled OOF cross-sectional IC **> 0** AND right-signed in ≥2/3 OOF years | >0 / ≥2yr | **SIGNAL-HARD** | the slow label destroyed the signal (a degenerate reformulation) — weaker than DIAG-G's 0.02 bar because the 21c target is intrinsically noisier; sign-preservation is the principled floor |
| **G-crash-preserve** | (i) CRASH-bucket mean net return **> 0** AND (ii) fresh CRASH quintile-spread of the slow-c1 prediction **t > 0** (right-signed) | both right-signed | **ALL-WEATHER-HARD** | **the reformulation ABANDONED G's crash edge** — a slow book that clears cost by losing the crash-robust all-weather property is a FAIL, not a win (the mandate's load-bearing gate). Sign-preservation anchor (NOT G's +3.21 — that would be fitting the fast-label number) |
| **G-2xcost** | net-2× Sharpe **> 0 AND ≥ 0.5×(1× Sharpe)** AND net-2× annualized return **> 0** | >0 & ratio & >0 | **ECON-HARD** | **the DIAG-G killer gate.** Its −5.3%/yr net2× is what the reformulation exists to fix; still-negative ⇒ the horizon-match didn't clear the cost wall |
| **G-turnover** | ann one-way turnover | **≤ 104×/yr** | **ECON-HARD** | 104 = 52 weekly rebals × 2.0 Σ|dw| (**one full flip per week — the max sensible weekly turnover**), pure geometry. DIAG-G's 156× BLEW THROUGH it; a fail ⇒ the slow label did NOT actually slow the book |
| **G-sharpe-floor** | net Sharpe (1× cost), as-shipped | ≥ **+0.35** | **ECON-HARD** | economic-relevance floor (v2/S4 template VERBATIM — NOT G's number); below it the neutralization machinery isn't justified |
| **G-maxdd** | as-shipped maxDD (gross=1.0) | ≥ **−25%** | **ECON-HARD** | draws like an equity bet → fails the all-weather MN mandate (charter/S4 verbatim) |
| **G-durable** | sign-stable IS halves: H1 net > 0 **AND** H2 net > 0 (H1=2020→2022-03, H2=2022-04→2024-06; scored over the OOF overlap) | both >0 | **ECON-HARD** | a one-half artifact, not durable |
| **G-sample** | span ≥ **2.0yr** AND ≥ **100 weekly rebals/phase** AND ≥ **20 names/rebal** mean AND all 3 OOF years (2022/23/24-H1) present | — | **ECON-HARD** | book scored on a truncated window (Rung-4 floor sized to the OOF cadence; 2.0yr/100-rebal are the post-warmup structural minima; ≥20 = MIN_MEMBERS) |

**14 HARD** = 6 NEUT {G1a,G1b,G2-CRASH,G2-MANIA,G3,G4} + 1 SIGNAL {G-signal-IC} + 1 ALL-WEATHER
{G-crash-preserve} + 6 ECON {G-2xcost, G-turnover, G-sharpe-floor, G-maxdd, G-durable, G-sample}.

| SOFT gate | Threshold | Note |
|---|---|---|
| G-crash-strong | fresh CRASH quintile-spread t > +1.5 | meaningfully (not just barely) right-signed — echoes G's crash-robustness without demanding the fast-label +3.21 |
| G-sharpe-target | net Sharpe ≥ +0.90 | the "clean candidate" level vs the +0.35 floor |
| G5 | no regime bucket > 60% of total P&L | one-regime concentration |
| G-3xcost | net Sharpe under CS-3× > 0 | corroborating cost-robustness (§3.2) |
| G-concentration | single-name gross ≤ 10% | structurally satisfied by the 0.10 cap; a violation = cap/universe bug |

---

## Section 5 — Falsification arms (pre-registered NEGATIVE controls; kill-only; ledger-neutral)

### 5.1 The suppression must cut COST, not add SIGNAL (un-suppressed comparison) — HARD control
Run the SAME continuous rank_neutral book + SAME projection + SAME cost + SAME 21-rebal on **DIAG-G's
FROZEN fast c1 (3-candle) prediction** (the un-suppressed twin). Report gross/turnover/net for BOTH.
**PASS requires: turnover(slow) < 0.5 × turnover(fast)** (the mechanism — the label actually slowed
the book) **AND the slow book's NET win over the fast book is COST-driven** (gross(slow) not ≫
gross(fast): specifically `gross(slow) ≤ 1.25 × gross(fast)`). **FALSIFIER:** if the slow book wins on
NET primarily via HIGHER GROSS (gross(slow) > 1.25×gross(fast)), the label change smuggled a *new/better
alpha* rather than suppressing turnover → the registered mechanism ("cut cost not signal") is falsified
→ **FAIL** (a different, un-registered claim; disclose, do not re-gate).

### 5.2 The plumbing must NOT be the edge (shuffled-signal placebo, on GROSS — C4-fixed) — HARD control
Run the SAME continuous book + SAME projection + SAME cost on a **cross-sectionally shuffled slow-c1
signal** (ranks permuted within each candle's live universe; ≥20 pre-registered shuffle seeds,
disclosed). The placebo must be **(i) beta-neutral** (G1a/G1b/G2 pass — neutrality is a projection
property) **AND (ii) zero GROSS-edge** (GROSS-Sharpe 95% CI over the ≥20 seeds INCLUDES 0, **two-sided**).
**C4 methodology fix baked in from birth:** the null is on **GROSS** Sharpe (or the real−placebo
gross-Sharpe differential), **NOT net-of-cost** — because the S4 field proved a two-sided null on a
net-of-cost Sharpe is structurally failed by ANY costed random book (it centers at −cost, not 0)
(FIELD-CLOSEOUT §"Methodology bug"). Also report the **real−placebo gross-Sharpe differential** (must
be reliably > 0 — the signal carries information over the random null). **FALSIFIER:** a reliably-nonzero
GROSS placebo (either sign) ⇒ the edge is projection/universe/weighting plumbing, not the signal → **FAIL.**

### 5.3 Direction integrity (frozen-sign control) — HARD control
G's direction is a-priori **+1** (the model forecasts the label; LONG top-predicted / SHORT
bottom-predicted). Report the reversed book (LONG bottom / SHORT top). It MUST underperform frozen.
**FALSIFIER:** reversed ≥ frozen ⇒ mechanism falsified → **FAIL**; and per S3-C2/D10, the frozen
direction is NEVER re-oriented to chase the reversed sign.

### 5.4 Throttle-is-not-the-alpha (informational, folds into §2.2)
The as-shipped book is throttle-off under the predicted HURTS, so the alpha is in the slow-label sort
by construction. Reported via the §2.2 forensic (throttled vs un-throttled). If the disposition
surprisingly returns HELPS with the throttle carrying the edge, disclose — but the un-throttled book
independently gates the alpha floors (G-sharpe-floor, G-2xcost), so a throttle-manufactured edge cannot
reach SUCCESS.

---

## Section 6 — Frozen decision map (IS design-validation only; NO holdout reveal; MECE, mechanical)

The as-shipped book (§2.2) is the single scored object. Tiers are a pure function of the §4 gates +
§5 controls on it. No post-hoc re-gating.

| Tier | Condition (mechanical) | Consequence |
|---|---|---|
| **FAIL** | ANY of: a NEUT-HARD fails (G1a/G1b/G2-CRASH/G2-MANIA/G3/G4) — OR **G-signal-IC fails** (slow label killed the signal) — OR **G-crash-preserve fails** (the reformulation abandoned G's crash edge) — OR a §5 control fails (§5.1 win is signal-driven not cost-driven / §5.2 GROSS placebo non-null / §5.3 direction flips) | The mechanism, its neutralization, its all-weather property, or its provenance is falsified. Localize, document, NOT revealed. |
| **MARGINAL** | ALL NEUT-HARD **AND** G-signal-IC **AND** G-crash-preserve **AND** all §5 controls pass, **BUT** a pure-ECON-HARD fails (G-2xcost / G-turnover / G-sharpe-floor / G-maxdd / G-durable / G-sample) | Genuinely neutral, all-weather-preserving, clean-signal — but the economics don't yet clear. The specific failed gate names the next iteration (e.g. G-2xcost still <0 ⇒ the horizon-match slowed the book [G-turnover pass] but not enough to pay ⇒ a slower cadence or a band becomes the next axis; G-turnover fail ⇒ the slow label did NOT slow the book, revisit the label). NOT revealed. |
| **SUCCESS** | ALL 14 HARD pass on the as-shipped book (incl. G-2xcost, G-turnover, G-crash-preserve) **AND** all §5 controls clear | An **IS-design-validated, turnover-suppressed, all-weather, cost-surviving market-neutral candidate** — the DIAG-G signal (crash-robust, all-year, all-seed) now executed at a turnover that clears the honest 2× cost wall, with the crash edge PRESERVED. Becomes the candidate for the family-G (`MN3-G`) holdout reveal (a FUTURE Stage-2 CONFIRMATION). **NOT a deployment, NOT a reveal — spends no token.** |

**Note (the discriminating gate).** G-2xcost is DIAG-G's killer. Its pass/fail is the reformulation's
whole thesis: SUCCESS ⇔ the horizon-match fixed the −5.3% economics while preserving the crash edge;
MARGINAL ⇔ neutral+clean+crash-preserving but the economics still don't clear. The throttle disposition
does NOT create a separate tier (§2.2 divergence-from-C1, justified).

---

## Section 7 — Holdout governance (shared `MN3-G` token; Stage-3 arbiter; ensemble-capstone status)

- **Shared token.** Per PLAN §6.1 anti-gaming, this construction is a **re-parameterization of family
  G** and **shares family G's one-forever token `MN3-G`.** A future Stage-2 reveal consumes `MN3-G`
  and burns family G's entire holdout budget. There is exactly one `MN3-G` reveal, ever.
- **This EXPLORATION spends NO token.** Stage-1, IS-only; `mn3_guard(reveal_token=None)` fires and MUST
  raise on any holdout-window overlap; `REVEAL-LEDGER.md` stays at zero spends.
- **Stage-3 is the real arbiter.** Even a clean Stage-2 `MN3-G` reveal is followed by a six-month
  forward paper-trade (recompute architecture, pre-registered gates) on genuinely-unseen post-2026-06
  data — that forward test, not the IS gates here, is the deployment arbiter.
- **Ensemble-capstone status (updated — G is now the ONLY live family).** The MN3 field is closed
  otherwise: S4 FAIL, H DEAD, I closed, J DEAD (fold into I), K DEAD (FIELD-CLOSEOUT). **If this
  reformulation banks, G is the SOLE standalone candidate — there is NO second family to ensemble
  with** (the born-ensemble / cross-family capstone path is dormant with no second survivor). A
  Stage-2 reveal would therefore be G STANDALONE (burns `MN3-G` only), not an ensemble. The C6
  ensemble-orthogonality flag (Amihud `amihud30_xz` shared with the dead S4) is moot (S4 failed).

---

## Section 8 — Multiple-testing budget / ledger (minimize DOF)

- **Family-G ledger opened at 8** (DIAG-G HP grid; one feature list, one label; the config-selection
  rule spent no extra trial). DIAG-G declined the revision round (cap-16) because kill (d) was a real
  economic result, not a fixable defect. **The user has now authorized that ONE revision round for
  this reformulation** (PLAN §3.1: "at most ONE pre-registered revision round … ledger 8→16; hard cap
  16 for the family's entire IS life").
- **This EXPLORATION-G spends +2 → ledger 10 (cap 16, headroom 6):**
  - **+1 — the slow-label retrain.** The label horizon (3→21) is the ONE new design DOF; the purge and
    winsor are horizon-*linked* (not free). **Config c1 is PINNED A-PRIORI (N=1, not best-of-8):** I do
    NOT re-select on the slow label — that would spend the full 8-trial round AND confound the
    label-horizon experiment. Pinning c1 is (a) justified by DIAG-G's proven HP-insensitivity (all 8
    configs in a tight +0.031…+0.037 band) and (b) a clean single-variable experiment (change ONLY the
    label; hold config, features, seeds, window fixed). The harness computes all 8 slow-label configs;
    the other 7 pooled ICs are REPORTED as an HP-insensitivity cross-check (ledger-neutral, no
    selection keys off them).
  - **+1 — the G-LCDD-z throttle** (§2.1): one construction, constants fully inherited from SCUD; the
    only free choices (leg = top-predicted cohort, tail = P25 downside) are structurally determined by
    the book, bundled into this one DOF and carrying its own falsifier (§2.3).
- **Ledger-neutral (kill-only) — spend 0:** the un-suppressed comparison (§5.1), the GROSS placebo
  (§5.2), the reversed-direction control (§5.3), the CS-3×/CS-A/thin-tilt arms (§3), and the
  un-throttled twin (§5.4). No design choice may key off any of them; if one ever conditions a design
  choice it converts to a registered trial retroactively.

---

## Section 9 — QE asks + pre-registered expectations

### 9.1 QE ASK — the slow-label OOF retrain (Lever B; the ONE code-adjacent change; ~12 min)

Clone `analysis/portfolio/mn3_g_oof.py` → `mn3_g_oof_slow.py` (or parametrize), changing EXACTLY three
horizon-linked constants and the output path; everything else (24 features, 8-config grid, 5 seeds,
monthly WF, 24-month window, deterministic params) BIT-IDENTICAL:
1. **Label horizon** `LABEL_FWD_K = 3 → 21` (`mn3_features.py` / passed into `build_g_label` /
   `forward_total_residual`) — forward 21-candle residual TOTAL return.
2. **Winsor** `LABEL_WINSOR = 0.20 → 0.53` (= 0.20·√(21/3); the √-horizon anchor, §1.1).
3. **Purge** `MN3_G_PURGE_CANDLES = 3 → 21` AND the inline purge in the WF loop
   (`mn3_g_oof.py:143` `t_idx_arr <= b_idx - 3 - 1` → `b_idx - 21 - 1`) — purge = label horizon.
4. **Output** → `data/mn3_g_slow/oof_predictions.parquet` + manifest (do NOT overwrite the frozen fast
   parquet `data/mn3_g/oof_predictions.parquet`).
5. **Guards unchanged:** `mn3_panel_health` first, `mn3_guard_grid` BEFORE any compute, IS-slice only,
   feature-column pin assert (24), determinism. OOF span 2022-01 → 2024-06 (last 21c unlabeled).

### 9.2 QE ASK — the engine scored run (the S4 harness pattern; NO engine core change)

Clone `mn3_exploration_s4.py` structure. Differences: signal source = `data/mn3_g_slow` c1
seed-ensemble mean (continuous, NOT a quintile step); `weighting="rank_neutral"` fed the CONTINUOUS
prediction (⇒ continuous demeaned-rank weights); `gross=1.0`, `rebal=21`, `weight_cap=0.10`,
`min_members=20`, `beta_neutralize=rolling_beta`, `funding=load_funding`; 21-phase tranche ensemble;
GT 2× (`COST_2X`) full re-run; the G-LCDD-z throttle (`mn3_scud_g.py` or an `mn_scud` extension: cohort
= **top** q=0.33 by c1-slow prediction, dispersion = P25 downside, SCUD constants verbatim) →
past-only `gross_scalar_series`. Report blocks: headline (Sharpe 1×/2×, ann ret/vol, maxDD, turnover,
21-phase positive count + distribution), neutrality (rolling β_BTC/β_ETH + max, bucket β_BTC + C5 β_ETH
CRASH/MANIA, G3), all-weather (CRASH/MANIA/CHOP means+t, fresh CRASH quintile-spread t), signal
(slow-c1 pooled OOF IC + per-year + per-seed + the 7-config HP-insensitivity cross-check), IS-halves,
throttle (coverage, mean scalar, HELPS/NEUTRAL/HURTS forensic), controls (§5.1 gross/turnover/net
fast-vs-slow, §5.2 GROSS placebo CI + real−placebo differential, §5.3 reversed), cost (CS-3×, thin-tilt
+ CS-A if material). Leak battery: corrupt-future on LCDD-z + composed scalar; decision-lag [k−1];
inert-default byte-identity; `mn3_guard(reveal_token=None)` before any metric; `mn3_datacheck` first.

### 9.3 Pre-registered expectations (honest ranges; what falsifies) — informational, NOT gates

| Quantity | Point | Range | Basis / what falsifies |
|---|---|---|---|
| slow-c1 pooled OOF IC | +0.022 | [+0.010, +0.037] | DIAG-G fast IC +0.037; a 21c target is noisier (accumulated idiosyncratic noise) ⇒ lower but positive. ≤0 ⇒ G-signal-IC FAIL |
| turnover (as-shipped) | ~45×/yr | [25×, 90×] | horizon-matched slow signal + continuous (vs quintile) weighting; DIAG-G 156×. >104× ⇒ G-turnover FAIL (label didn't slow the book) |
| net-2× Sharpe | +0.5 | [−0.1, +1.1] | the discriminating gate; lower turnover pays the DIAG-G gross down less. ≤0 ⇒ G-2xcost FAIL (the horizon-match didn't clear the wall) |
| net Sharpe (1×, as-shipped) | +0.8 | [+0.3, +1.4] | slower book harvests weekly IC; < +0.35 ⇒ G-sharpe-floor FAIL |
| CRASH-bucket edge (preserve) | right-signed, t ~ +2 | t ∈ [0, +3.5] | DIAG-G CRASH t +3.21; the slow label should retain the crowding-syndrome crash edge. t ≤ 0 ⇒ **G-crash-preserve FAIL** (abandoned the all-weather property) |
| maxDD (gross=1.0) | −14% | [−8%, −25%] | crash-positive + low turnover ⇒ shallow. < −25% ⇒ G-maxdd FAIL |
| CRASH \|β_BTC\| | +0.05 | [−0.05, +0.15] | weight projection neutralizes; the +3.21 CRASH edge is premium not beta. >0.15 ⇒ G2-CRASH FAIL |
| §5.1 gross(slow)/gross(fast) | ~0.9 | [0.6, 1.25] | suppression cuts cost not signal; >1.25 ⇒ §5.1 FAIL (smuggled new alpha) |
| GROSS placebo Sharpe | ~0 | CI ∋ 0 | neutrality is a projection property, edge is the signal; reliably ≠0 ⇒ §5.2 FAIL |
| throttle disposition | **HURTS** → ship-off | — | G crash-robust; a downside throttle fires in G's profitable crashes (S4 precedent). HELPS would be a bonus |

**Modal outcome I expect:** G-turnover PASSES decisively (the horizon-match is a real turnover fix);
the two DISCRIMINATING unknowns are **(a) G-2xcost** — does the lower turnover let G's now-slower gross
clear the 2× wall (the whole thesis) — and **(b) G-crash-preserve** — does the 21c label RETAIN the
crowding-syndrome crash edge that the 3c label captured (the noisier target could dilute it). The
throttle is a-priori-predicted HURTS (ship-off). Neutrality (G1a/G2) should transfer (same projection
as S4's R1-pass), and G-signal-IC should pass (positive but lower IC).

---

*— Quant Researcher (Opus 4.8, Fable-suspended phase disclosed), MN3 track, 2026-07-11.
EXPLORATION-G pre-registration — the turnover-suppressed, horizon-matched reformulation of the
family-G flagship. Everything frozen before the run; holdout sealed; `MN3-G` token unspent; nothing
committed to git. Next: Critic pre-flight, then the QE slow-label retrain (§9.1) + the scored engine
run (§9.2).*
