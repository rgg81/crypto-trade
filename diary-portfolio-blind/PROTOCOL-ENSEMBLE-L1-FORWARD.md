# PROTOCOL-ENSEMBLE-L1-FORWARD — Pre-registered forward-validation contract for the frozen ENSEMBLE-L1 (protocol v2)

**Status: FROZEN 2026-07-10, before the first forward candle.** This is protocol **v2** — it
**supersedes PROTOCOL-L1-FORWARD (single-phase Wed@00h)**, which is RETIRED (§1). It is the
pre-registered forward contract for the **all-21-phase equal-weight ENSEMBLE-L1** — the /007
construction (PHASE7-007: IS TIER = FAIL on a mis-anchored G-crash gate, adjudicated as a
mis-anchored-gate failure, NOT a crash-defense collapse; the phase-tail is empirically
time-diversifiable, the overlay mechanism is preserved, all IS years positive). Paper trading only —
**no real orders.** The construction is FROZEN: no threshold, no parameter, no aggregation change. Any
change resets the clock to a new T0 and a new protocol version (§5).

**Why this is a forward test at all (honest framing — read first).** ENSEMBLE-L1's ONLY pre-registered
IS gate outcome was **FAIL** (/007 G-crash), because the crash gate was anchored to a single-phase
number (~2.76× the phase-honest level) — a contract defect, not a mechanism failure (crash defense is
intact: IS crash +0.933% > 0, short_px +1.204 > 0, ≈ V0-ENSEMBLE +0.935%). **The IS crash gate for this
construction/window is SPENT** (PHASE7-007 §5b) — no clean IS re-gate is admissible. **This forward test
is therefore the FIRST clean adjudication of the ensemble's crash defense**, on genuinely unseen data,
with a **PRINCIPLE-anchored** crash gate (§4, M-crash). The forward test is not "confirming an IS pass";
it is the primary and only clean validation path, entered on the user-accepted QR recommendation
(PHASE7-007 §5c) that the ensemble is the phase-honest construction with the empirically-clipped tail.

**Quarantines.** IS artifacts only for design; **`CONFIRMATION-005.md` not read**; the burned OOS
window **2025-03-24 → T0 stays quarantined as INPUT-history only** and contributes **no** forward metric
(indicator-history exception, §2). ONE frozen candidate; **n_eff = 1 forward** (§5).

---

## §1 — Supersession record (NEW; the sibling-forward ban made operational)

**PROTOCOL-L1-FORWARD (single-phase Wed@00h L1) is RETIRED effective 2026-07-10, BEFORE its T0.**

- The retired protocol's T0 was 2026-07-15; **zero forward candles accrued** (its §7 activation record:
  "0 forward rows (pre-T0, correct)"). **Retiring it pre-T0 abandons NO in-flight test** — no forward
  data is discarded, no clock is reset on observed data. This is a clean construction switch, not an
  abandonment mid-window.
- **Sibling-forward ban honored: exactly ONE forward book runs — ENSEMBLE-L1.** The single-phase book
  does NOT continue in parallel. Running both (or any other aggregation / phase / control variant) would
  recreate the best-of-k selection problem forward and void the n_eff = 1 property (§5).
- **User authorization: 2026-07-10**, accepting the PHASE7-007 §5(c) QR recommendation to switch the
  forward validation to ENSEMBLE-L1 (replacing single-phase, new T0 / new protocol version). The
  decision was the user's; the recommendation was grounded in the /007 evidence (phase-tail clipped to
  −18.59%, phase luck structurally removed, crash defense intact) with the honest counter-weight
  disclosed (new construction, correlation-regime risk).
- The retired protocol's systemd timer / runner path (`blind-paper-l1.timer`, `paper-l1/run_weekly.sh`,
  `analysis/portfolio/blind_paper_l1.py`) is **RE-TARGETED**, not duplicated (§6): the same weekly
  Wednesday recompute now evaluates the ensemble book. The `paper-l1/` log directory is reused with a
  **protocol-version tag on every row** and a v2 re-init (§3, §6).

---

## §2 — Construction (FROZEN — the exact /007 ENSEMBLE-L1)

Each weekly run rebuilds the full panel (2020-01-01 → now) and computes the ensemble via the
**UNCHANGED** `blind_engine.run_backtest`, reusing `run_l1` / `run_v0` / `trim_panel` from
`blind_paper_l1` (single source of truth — the SAME functions the /007 matrix and the phase sweep used).

**Tranche (each of 21):** the byte-frozen L1 at rebal offset `p ∈ {0..20}`:
- `lowvol_signal(window=12)`, `pit_topn_universe(top_n=20, lookback=30)`,
  `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)`, funding ON, `gross=1.0`,
  `rebal=21`, `weighting="midvol_short"`, `long_frac=0.5`, `short_frac=0.25`;
- **C1** = `short_scalar_series` from the committed `mania_gate` with the **0.5 floor**;
- **C2** = `short_exclude` from trailing-21c return `> +0.30`, `short_exclude_mode="shrink"`;
- **C3/C4/C5 OUT.** Tranche `p` = `run_l1(trim_panel(panel, p))`.

**Ensemble aggregation (FROZEN):**
- Map each tranche's per-candle return onto the ORIGINAL grid by `grid_ms` (trimmed index `j` ↔ original
  `p+j`); **common warmup=63 slice** begins at the first candle where all 21 tranches are warm+finite
  (IS: original index 83; forward: the running analog).
- **`ensemble_ret[t] = (1/21)·Σ_p mapped_tranche_ret_p[t]`** — equal 1/21 weights, mean-of-returns.
  Equity compounds on the ensemble return. Effective behavior: the book rebalances 1/21 of itself every
  8h candle.
- **Disclosed cost biases (carried from /007 §2/§4, unchanged):** (i) **each tranche pays its own
  turnover — no cross-tranche netting** → COST-CONSERVATIVE (a real book nets internal crossings; real
  turnover ≤ ~50x, so all cost-bearing metrics are a pessimistic lower bound); (ii) constant equal 1/21
  weights assume **costless cross-tranche weight maintenance** — a small OPTIMISTIC idealization. Both
  tiny (tranches were ~52% correlated IS); net direction likely conservative.

**IS parity anchors (for the runtime ABORT-guard, §6):** ensemble Sharpe **+1.2826** (common [83:]
slice), maxDD **−18.59%**, turnover **50.3x**; single-phase tranche p=0 **+1.1638** (ties to /006 +
the sweep). Both are asserted every run.

**T0 — MECHANICAL, phase-neutral.** The ensemble holds all 21 phases and rebalances 1/21 every candle,
so it is **phase-symmetric: any weekly boundary is an equivalent start** — there is NO phase-luck in T0
selection (unlike the retired single-phase protocol, which had to justify Wed@00h out of 21; that
concern is structurally eliminated here). Wednesday 00:00 UTC is retained purely for **runner-cadence /
monthly-reporting continuity.**

> **T0 rule (pre-registered, so the date is mechanical, not chosen):**
> **T0 = the first Wednesday 00:00 UTC candle ≥ operational-readiness** (operational-readiness = the QE
> v2 re-init of the runner + logs is committed and a clean proof run has fired, §6).

Both candidate T0s are pre-registered NOW (§4.5): **T0-A = 2026-07-15 00:00 UTC** (if the QE re-init
lands first) or **T0-B = 2026-07-22 00:00 UTC** (the next Wednesday). Whichever the mechanical rule
selects is the frozen T0; the horizon dates for both are tabled in §4.5. Per the T0-decoupling clause
(carried from the /007 brief §5.3): **T0 timing must not pressure anything — verdict/readiness quality
takes precedence; missing T0-A simply lands the test at T0-B.**

Only the **post-T0 slice** is the forward evaluation. The engine's proven **append-invariance** (leak
positive-controls) guarantees past decisions never change as candles append; **every run ASSERTS
bit-identity** of all pre-existing ensemble rows against the prior run (proves no forward leak + catches
upstream kline revisions). Same recompute architecture, burned-window guard `[OOS_CUTOFF=2025-03-24,
T0)`, integrity pinning, and weekly Wednesday runs as the retired protocol.

---

## §3 — Data / cost / funding / state accounting (inherit v1 §3 by reference; essentials restated)

Identical to PROTOCOL-L1-FORWARD §3 except the evaluated book is the ensemble:

- **Costs:** taker 5 bps + slippage 2.5 bps on one-way turnover at fills (recorded kline **open = fill
  price**), **per tranche**, funding = `blind_funding` bucket-sum on each tranche's held weights; equity
  compounds multiplicatively; fixed-share drift between rebals. Cost biases per §2.
- **Funding:** ON, identical to the backtest, per tranche then averaged into the ensemble return.
- **State / logs:** `paper-l1/` at worktree root, **re-initialized for v2** (the retired protocol's logs
  are pre-T0 empty — headers only, zero forward rows — so re-init loses nothing). **Every row carries a
  `protocol` tag = `ENSEMBLE-L1-v2`.** New/extended schema (§6): an **ensemble aggregate** equity row
  (ensemble equity, ensemble per-candle return, ensemble gross) + a decisions row (aggregate turnover,
  cost, funding; C1-fired tranche count this candle; C2 excluded-name count this candle) + the **forward
  `rho_bar`** (weekly) + the **V0-ENSEMBLE reference series** (forward V0-ensemble Sharpe / crash / mania
  for the relative gates). Append-only, committed weekly (docs-style commits → tamper-evident audit
  trail).
- **Integrity:** SHA256 of `blind_engine.py` / `blind_risk_calib_006.py` / `blind_mania_rule.py` /
  `blind_paper_l1.py` (the ensemble construction + runner) pinned at T0 (§7); every run re-hashes +
  alerts on drift (drift ⇒ construction moved ⇒ clock-reset per §5).
- **Cadence:** weekly, Wednesday ~00:10 UTC, after a data refresh (fetch 8h klines all perps + funding);
  staleness/completeness guard: retry up to 3× over 6h, then proceed with a **DEGRADED** flag (engine
  force-exits invalid prices, same as backtest). Same systemd timer as v1, re-targeted.
- **INDICATOR-HISTORY EXCEPTION (explicit):** the z365 / universe-lookback / vol warmup necessarily
  consumes pre-T0 history INCLUDING the burned OOS window. That history is **INPUT only**. No pre-T0
  candle contributes to any forward metric — every §4 gate is on fills at candles with open_time ≥ T0.

---

## §4 — Pre-registered gates + horizon (QR design — FRESH, principle/relative-anchored)

**Anchoring discipline (the /007 lesson, load-bearing).** No gate is anchored to a revealed IS ensemble
number in a way that guarantees a pass. Two clean patterns are used throughout: **principle-anchoring**
(directional/sign conditions: mean > 0, short_px > 0, correlations must not blow out) and
**relative-anchoring vs the forward V0-ENSEMBLE** (the no-overlay 21-phase ensemble, computed by the
runner on the SAME forward window — apples-to-apples, un-gameable by any IS number). The fail-fast risk
floors are stress ceilings anchored to a PRINCIPLE ("diversification evaporated" / "month-diversification
broke"), not to the ensemble's own passing IS level.

### 4.0 Statistical-power framing (why the Sharpe gate is deliberately deflated)

Forward horizon = 12 months ≈ 1092 8h candles ≈ 52 weekly rebals. iid asymptotic SE (Lo 2002)
**SE(SR̂) ≈ √(1/T_years)**:

| horizon | T_years | SE(SR̂) |
|---|---|---|
| 6 months | 0.50 | ≈ **1.41** |
| 12 months | 1.00 | ≈ **1.00** |
| 18 months (extension) | 1.50 | ≈ **0.82** |

A 12-month Sharpe gate has SE ≈ 1.0 — LOW-POWER (crypto fat tails / autocorrelation only widen the true
SE). **The Sharpe gate is a deflated screen; the risk-containment (fail-fast) and mechanism gates carry
the decision weight** — and for the ensemble those mechanism gates are STRONGER than for the single-phase
book (the tail is empirically clipped, and the crash / mania / correlation mechanisms are all directly
testable against the forward V0-ENSEMBLE).

**Honest forward Sharpe band (REVIEW-007 caveat 5): ≈ +0.70–0.95, central ~+0.80** — above the retired
single-phase L1 band (+0.55–0.80), because phase luck is structurally removed AND there is a structural
~1.35× vol-reduction (the /007 diversification discovery) whose decorrelation mechanism is regime-general;
well below the IS +1.28 (base-edge deflation + transfer uncertainty; forward tranche correlation could
rise in stress — the M-rho risk, §4.1).

### 4.1 Gate table (FROZEN)

Sign convention: maxDD and returns negative; "breach" = worse than the floor. All forward metrics on
fills at candles with open_time ≥ T0. **V0-ENSEMBLE** = the 21-phase equal-weight ensemble of the
no-overlay /005 base, computed by the runner on the SAME forward window.

| Gate | Type | Metric | Threshold | Evaluated | Anchor |
|---|---|---|---|---|---|
| **FF-1 maxDD** | HARD fail-fast | forward ensemble equity peak-to-trough DD since T0 | **< −28% → FAIL** | every run | PRINCIPLE: −28% ≈ the single-phase Wed@00h maxDD (−28.58%) = the level at which the ensemble's tail has degraded back to a single lucky phase, i.e. the diversification benefit has evaporated; ~1.5× the ensemble IS maxDD (−18.59%). Tighter & more informative than the retired −35% (which was single-phase-phase-fragility-calibrated / undeployable). |
| **FF-2 worst-month** | HARD fail-fast | any completed forward calendar-month return | **< −12% → FAIL** | every run (on month close) | PRINCIPLE: −12% ≈ just below the single-phase L1 IS worst month (−12.72%) and ~1.5× the ensemble IS worst (−8.17%). A forward month worse than the single-phase book's worst IS month ⇒ the ensemble's month-level squeeze-diversification (which clipped the 35pp phase dispersion) broke. |
| **FF-3 slow-bleed** | HARD fail-fast | trailing-26wk ann. Sharpe **AND** trailing-26wk cum. return | **Sharpe < −1.0 AND return < −12% → FAIL** | every run, once ≥26 fwd weeks | return threshold tightened −15% → −12% for the ensemble's LOWER vol (~0.20 vs single-phase ~0.27): −1.0 Sharpe over 26wk at 0.20 vol ≈ −14% return, so the −12% AND aligns both conditions. Catches a low-vol persistent bleed FF-1 misses. |
| **CP6 fail-early** | fail-early only | cumulative forward Sharpe since T0 | **< −1.0 → FAIL-EARLY** (+ re-affirm FF-1/2/3) | 6-mo checkpoint (T0+26wk) | one-sided; only a clear half-year bleed. **No SUCCESS/PARTIAL at 6mo.** |
| **P-Sharpe** | PRIMARY (tiered) | cumulative forward Sharpe since T0 | **≥ +0.60 → SUCCESS-tier · −0.25…+0.60 → PARTIAL · < −0.25 → FAIL** | 12-mo (T0+52wk) | deflated screen 0.10 below the +0.70 band floor; raised from the retired +0.50 to reflect the higher ensemble expectation while staying low-power (§4.3). |
| **P-turnover** | HARD sanity | forward annualized one-way turnover | **≤ 100x** (else FAIL) | 12-mo | structural (ensemble IS = 50.3x; >100x = universe/data breakdown). |
| **P-risk-held** | HARD (SUCCESS precondition) | FF-1/FF-2/FF-3 never breached in-window | must hold for SUCCESS | 12-mo | HIGH. |
| **M-crash** ★ | mechanism (conditional) — **THE /007 lesson** | forward crash-bucket (frozen rule `btc_ret<−15% OR btc_dd_end(540)>25%`) mean, short_px, and vs forward V0-ENSEMBLE crash | **PASS iff** ensemble crash mean **> 0** AND crash **short_px > 0** AND ensemble crash **≥ forward V0-ENSEMBLE crash − 0.25pp** (PRESERVE-not-improve tolerance band). CONTRADICTION if any fails. | 12-mo if **≥2** fwd crash months, else **N/A** (extension trigger, §4.4a) | **PRINCIPLE + relative** — NOT anchored to any revealed IS number (the /007 defect corrected). Tests "does the overlay PRESERVE crash defense?" — C1/C2 were never designed to IMPROVE crash (IS: overlay is crash-NEUTRAL, ENS-L1 +0.933% ≈ V0-ENS +0.935%), so a strict `≥` would spuriously CONTRADICT a faithfully-neutral overlay ~50% of the time; the −0.25pp band tests preservation, not improvement. |
| **M-mania** | mechanism (conditional) | forward mania-bucket (frozen `blind_mania_rule` ≥40% coverage) mean, short_px, vs forward V0-ENSEMBLE mania | **PASS iff** ensemble mania mean **≥ forward V0-ENSEMBLE mania** AND ensemble mania **short_px ≥ V0-ENSEMBLE mania short_px** (short leg less squeezed). CONTRADICTION otherwise. | 12-mo if **≥2** fwd mania months, else **N/A** | relative (vs forward V0-ENSEMBLE). |
| **M-C1** | mechanism (conditional) | short-leg P&L in C1-fired weeks vs unflagged weeks, **pooled across all 21 tranches** | fired-week (un-scaled) short leg **more negative** than unflagged → C1 fired on real squeezes → PASS; opposite → CONTRADICTION | 12-mo if ≥8 pooled fired tranche-weeks, else **N/A** | PRINCIPLE (directional). |
| **M-C2** | mechanism (conditional) | counterfactual short P&L of C2-excluded names over their exclusion windows, **pooled across all 21 tranches** | excluded names were **bad shorts** (counterfactual short P&L < 0) → PASS; > 0 → CONTRADICTION. **Broken out mania-month vs non-mania-month** (caveat-5 non-2024-11 stress). | 12-mo if ≥1 pooled exclusion, else **N/A** | PRINCIPLE (directional). |
| **M-rho** ★ | mechanism (conditional, one-sided) — **NEW /007 discovery** | forward `rho_bar` (mean pairwise Pearson of the 21 tranche forward-return streams, full window) **AND** forward ensemble ann. vol | **CONTRADICTION iff** forward `rho_bar > 0.75` **AND** forward ensemble vol **> 0.26**. `rho_bar` staying low grants NOTHING (the expected/good case). | 12-mo if ≥26 fwd weeks, else **N/A**; **logged weekly, INFORMATIONAL until the primary** | PRINCIPLE — the diversification mechanism (the ensemble's load-bearing novelty) failing forward. |
| **M-overlay** | mechanism (one-sided) — ensemble-level replacement for the retired M-phase | forward ensemble-L1 Sharpe − forward V0-ENSEMBLE Sharpe | ensemble-L1 Sharpe **≥** V0-ENSEMBLE Sharpe → PASS; **[V0-ENSEMBLE Sharpe − 0.25, V0-ENSEMBLE Sharpe) → CONCERN** (dead-zone buffer; blocks SUCCESS → routes to PARTIAL, §4.2, C3); **< V0-ENSEMBLE Sharpe − 0.25 → CONTRADICTION**. Positive overlay grants nothing beyond PASS (SUCCESS still needs P-Sharpe ≥ +0.60). | 12-mo, if ≥26 fwd weeks, else **N/A** | relative (tests the F10 21/21-positive-overlay claim forward, aggregated). |

★ = the two gates that encode the specific /007 findings (M-crash = the mis-anchored-gate lesson;
M-rho = the diversification-mechanism discovery + its correlation-regime risk).

### 4.1a — Weekly INFORMATIONAL logs

The runner already computes all 21 L1 + 21 V0 tranche books each run. It logs (in `gates.csv`, tagged
`ENSEMBLE-L1-v2`): the **ensemble** forward Sharpe/maxDD/turnover, the **V0-ENSEMBLE** forward
Sharpe/crash/mania (relative-gate references), the weekly **forward `rho_bar`**, and the per-phase
overlay delta (context). These are INFORMATIONAL — the binding gates evaluate the **ensemble aggregate**.
**No mid-window action derives from the logs except the pre-registered fail-fast gates.** The
phase-selection ban is **moot** here (the ensemble uses all 21 phases equally; nothing is ever selected).

### 4.2 Verdict integration at the 12-month PRIMARY

- **FAIL** if ANY of: a fail-fast gate (FF-1/2/3) breached at any point in-window; **or** P-Sharpe < −0.25;
  **or** P-turnover > 100x; **or** any EVALUABLE mechanism gate returns a **CONTRADICTION** (M-crash:
  crash defense lost or overlay hurt crash vs V0-ENS / M-mania: overlay failed to help mania vs V0-ENS /
  M-C1: C1 fired but worsened / M-C2: excluded names were good shorts / M-rho: correlations rose AND vol
  blew out / M-overlay: overlay materially negative). A mechanism CONTRADICTION overrides a merely-noisy
  positive Sharpe — the "edge" was luck.
- **SUCCESS** if ALL of: P-Sharpe ≥ +0.60 **AND** P-risk-held (no fail-fast breach) **AND** P-turnover
  ≤ 100x **AND M-crash is PASS (not N/A)** **AND** every OTHER evaluable mechanism gate is PASS (no
  CONTRADICTION and no CONCERN; N/A is acceptable for the non-M-crash gates). **M-crash N/A is NOT
  eligible for full SUCCESS** — it routes to the §4.4a extension (12mo) or the QUALIFIED verdict (18mo).
- **PARTIAL** (→ the ONE 6-month extension, §4.4/§4.4a) if not FAIL and not SUCCESS — e.g. −0.25 ≤
  P-Sharpe < +0.60 with risk contained and no contradiction; **or** an M-overlay **CONCERN**
  (dead-zone [V0-ENS−0.25, V0-ENS), C3) which blocks SUCCESS; **or** M-crash **N/A** at 12mo (§4.4a(a)).
- **QUALIFIED ("SUCCESS-except-crash-not-forward-tested")** — ONLY at the 18-month terminus (§4.4a(b)):
  a SUCCESS-grade result (P-Sharpe ≥ +0.60, P-risk-held, P-turnover ≤ 100x, every OTHER evaluable
  mechanism gate PASS) but with **M-crash STILL N/A** (< 2 forward crash months over the full 18mo).
  Full SUCCESS is withheld; the /007 crash question stays open and travels as a deployment caveat.

The mechanism gates are load-bearing precisely because the Sharpe is low-power. **M-crash is the
decisive one:** it is the properly-anchored version of the gate the ensemble FAILED IS — a forward PASS
on M-crash is the specific evidence the /007 FAIL could not clean, and its N/A is why the QUALIFIED
tier exists (a hollow SUCCESS with the crash question untested is not permitted).

### 4.3 Error rates for the SUCCESS Sharpe bar (+0.60) — honest, quoted (SE ≈ 1.0 at 12mo)

- **P(false PASS | true SR = 0) = P(SR̂ ≥ +0.60) ≈ 27%** — Sharpe-gate ALONE. SUCCESS additionally
  requires P-risk-held **and** no mechanism contradiction, driving the JOINT false-positive far below 27%
  (a true-zero book must also survive a year with no −28% DD / no −12% month AND pass M-crash / M-C1 /
  M-C2 / M-rho / M-overlay — jointly unlikely by luck).
- **P(miss | true SR = +0.80 central) = P(SR̂ < +0.60) ≈ 42%** — of which only **≈15%** is an outright
  FAIL (P(SR̂ < −0.25 | +0.80) ≈ 15%); the remaining **≈27%** routes to **PARTIAL → the one extension**.
- Across the honest band: P(miss) at floor +0.70 ≈ **46%**, at top +0.95 ≈ **36%**; the
  outright-hard-FAIL portion runs **≈12–17%** across the band.
- **Decision rationale (FINAL — this is the last moment the tiers can move).** I set SUCCESS at **+0.60**,
  raised from the retired single-phase +0.50, because the ensemble's honest expectation is higher
  (+0.70–0.95 vs +0.55–0.80); +0.60 stays a deflated screen 0.10 below the band floor (I did NOT set it
  at the +0.70 floor, which would make ~half of central-expectation books miss SUCCESS — too punitive for
  SE≈1.0). The confidence rests on the strengthened risk + mechanism gates (empirically-clipped tail;
  M-crash / M-rho / M-overlay). The **−0.25 FAIL floor is band-independent** ("a clearly-negative forward
  year") and stays put.
- **Calibration-honesty disclosure (Critic C4).** The +0.60 bar is set AFTER observing the IS ensemble
  numbers (+1.28 Sharpe, +0.947 phase mean), so it is a **post-IS-observation calibration** — disclosed
  as such. Three reasons it is NOT outcome-anchoring / tuned-to-pass: (i) **the gated quantity — the
  FORWARD Sharpe — is genuinely UNSEEN** (no forward candle has been observed; the burned window
  contributes no metric), so the bar cannot be fitted to the outcome it screens; (ii) **the calibration
  moved in the CONSERVATIVE direction** (raised the bar +0.50 → +0.60 to reflect the higher ensemble
  expectation, making SUCCESS HARDER, not easier); (iii) it is a **deflated screen sitting 0.20 BELOW the
  ~+0.80 central expectation with a quoted 42% miss rate** at that expectation — a bar tuned-to-pass would
  sit at or below the noise floor, not a fifth of an SE below the central forecast with a
  4-in-10 chance of missing. The decision weight remains on the risk + mechanism gates, not this screen.

### 4.4 Extension rule (pre-registered, once)

**PARTIAL at 12 months → exactly ONE 6-month extension** (to T0 + 78 weeks). At the 18-month terminus,
re-evaluate the SAME gate structure over the FULL 18-month window (SE ≈ 0.82):

- **SUCCESS** if P-Sharpe(18mo) ≥ +0.60 AND P-risk-held AND P-turnover ≤ 100x AND **M-crash PASS** AND
  no other mechanism contradiction/CONCERN. **QUALIFIED** if that SUCCESS grade holds in every respect
  EXCEPT M-crash is still N/A (< 2 crash months over 18mo — §4.4a(b)). **FAIL** otherwise. **No second
  extension.**
- Error rates at 18mo for the +0.60 bar: **P(false PASS | SR=0) ≈ 23%**, **P(miss | SR=+0.80) ≈ 40%**.
  The extension buys only modest power; it resolves a genuinely ambiguous 12-month outcome, not
  manufactures significance.

### 4.4a M-crash N/A completeness — the decisive gate must not be silently skipped (Critic C2)

M-crash is the phase's raison d'être (the properly-anchored version of the gate the ensemble FAILED
IS). Crash months **cluster** (bimodal in time), so a bull 12-month forward window plausibly (~20–40%)
yields **< 2 forward crash months → M-crash is N/A**. Without this rule, §4.2's "PASS-or-N/A" would
declare a **HOLLOW full SUCCESS** with the crash question — the entire /007 lesson — never forward-tested.

- **(a) M-crash N/A at the 12-month primary → extend once (6 months)** to seek ≥2 forward crash months.
  This is a **second, independent trigger for the SAME single extension** as the PARTIAL-Sharpe trigger
  (§4.4). **Interaction (explicit): there is EXACTLY ONE 6-month extension total.** Whichever trigger
  fires first (or if both fire at 12mo) invokes it; the window extends to T0+78wk and the full 18-month
  window is re-evaluated once. **No second extension under any combination of triggers.**
- **(b) M-crash STILL N/A at the 18-month terminus** (fewer than 2 crash months over the full 18mo) →
  the verdict is **QUALIFIED: "SUCCESS-except-crash-not-forward-tested"** — **NOT full SUCCESS.** Even if
  P-Sharpe(18mo) ≥ +0.60 with risk held and every OTHER evaluable mechanism gate PASS, the ensemble's
  crash defense was never adjudicated forward, so the /007 crash question **remains open.** Any
  deployment consideration under a QUALIFIED verdict carries the **explicit caveat that the crash-defense
  question the IS gate could not clean is still untested on unseen data** — a materially weaker basis
  than a full SUCCESS with an M-crash PASS.
- **N/A handling for the OTHER conditional mechanism gates** (M-mania, M-C1, M-C2, M-overlay) is
  unchanged — their N/A does NOT trigger an extension or a QUALIFIED verdict (none is the phase's
  decisive gate); only M-crash carries this completeness rule.

### 4.5 Horizon dates (FROZEN for BOTH candidate T0s; the mechanical T0 rule selects one)

**If T0-A = 2026-07-15 00:00 UTC (Wednesday):**

| milestone | offset | date (UTC, Wed) | fwd candles |
|---|---|---|---|
| **T0-A** | 0 | **2026-07-15 00:00** | 0 |
| 6-mo checkpoint (fail-early only) | +26wk | **2027-01-13 00:00** | ≈ 546 |
| **12-mo PRIMARY** | +52wk | **2027-07-14 00:00** | ≈ 1092 |
| 18-mo extension terminus (if PARTIAL) | +78wk | **2028-01-12 00:00** | ≈ 1638 |

**If T0-B = 2026-07-22 00:00 UTC (Wednesday):**

| milestone | offset | date (UTC, Wed) | fwd candles |
|---|---|---|---|
| **T0-B** | 0 | **2026-07-22 00:00** | 0 |
| 6-mo checkpoint (fail-early only) | +26wk | **2027-01-20 00:00** | ≈ 546 |
| **12-mo PRIMARY** | +52wk | **2027-07-21 00:00** | ≈ 1092 |
| 18-mo extension terminus (if PARTIAL) | +78wk | **2028-01-19 00:00** | ≈ 1638 |

---

## §5 — Frozen interpretation map + multiple-testing

### 5.1 Interpretation map

| 12-mo (or 18-mo) verdict | action |
|---|---|
| **SUCCESS** | Candidate for **small-size REAL deployment consideration** — a NEW decision made WITH the user, **not automatic**. Requires, in particular, an **M-crash PASS** — the properly-anchored crash gate the /007 IS test could not clean. (M-crash N/A does NOT qualify → see QUALIFIED.) |
| **QUALIFIED** ("SUCCESS-except-crash-not-forward-tested") | Only at the 18-month terminus with M-crash STILL N/A (§4.4a(b)). A SUCCESS-grade Sharpe/risk/mechanism result, but the crash question is UNTESTED forward. Deployment consideration is permitted ONLY with the **explicit caveat that the /007 crash-defense question remains open** — a materially weaker basis than full SUCCESS; the user must weigh deploying with the decisive gate untested. |
| **PARTIAL** (12-mo only) | **The ONE 6-month extension**, once (§4.4/§4.4a) — triggered by a PARTIAL Sharpe/overlay result **or** by M-crash N/A at 12mo, whichever fires first (one extension total). A PARTIAL (Sharpe/overlay) at the 18-month terminus is a FAIL; an M-crash-N/A-only case at 18mo is QUALIFIED, not FAIL. No second extension. |
| **FAIL** | **Track concludes on the ensemble book. ENSEMBLE-L1 is archived. NO rescue tuning** — no re-weighting of tranches, no phase subset, no threshold nudge, no control swap, no crash-gate re-anchor. A failed forward test is a result, not a starting point. |

**Clock-reset rule.** ANY change to the construction, the aggregation (equal 1/21 mean-of-returns), or
any tranche C1/C2/base parameter during the window **resets the clock to a new T0 and a new protocol
version** (`PROTOCOL-ENSEMBLE-L1-FORWARD-v3`). The thing being tested does not move.

**No-sibling-forward ban (restated).** Exactly ONE forward book runs: ENSEMBLE-L1. No single-phase book
(retired, §1), no C1-only / C1+C2+C3, no different Q, no unequal tranche weighting, no phase subset in
parallel — any of those recreates best-of-k forward and voids n_eff = 1.

**No mid-window peeking-based action** other than the pre-registered fail-fast gates (FF-1/2/3) and the
6-month fail-early checkpoint. The weekly logs are an audit trail, not a decision surface.

**T0-decoupling clause (carried from /007 brief §5.3).** T0 timing must not pressure readiness or
verdict quality: if the QE v2 re-init is not clean by T0-A, the mechanical rule lands the test at T0-B
with no penalty. Readiness/verdict quality takes absolute precedence over any candidate date.

### 5.2 Multiple-testing note

- **This is ONE pre-registered forward test of ONE frozen candidate → n_eff = 1 forward.** The Sharpe
  bar is deflated (+0.60, below the +0.70–0.95 band floor) precisely because the IS-side cumulative
  selection surface already inflated IS Sharpes; the forward test must not re-spend that budget.
- **IS-side cumulative ledger (documented, carried from /007 §6):** the ensemble added **zero best-of-k
  inflation** (selection-free, equal-weight all-21) + **1 researcher-DOF** (the decision to build the
  ensemble) → **cumulative IS-side n_eff ≈ 17–23**. The ensemble Sharpe is already **phase-deflated by
  construction** (it realizes the phase-agnostic level, not the single-phase lucky draw).
- **The switch decision, counted honestly.** Choosing the ensemble over single-phase for the forward book
  is a construction CHOICE (a researcher-DOF), made by the user on the QR /007 recommendation. It is NOT
  a new search over constructions — the ensemble +1 DOF is already booked, and the single-phase book is
  RETIRED (not run in parallel), so no best-of-2-forward inflation is created. **Forward n_eff = 1.**
- **The IS gate outcome was FAIL.** This forward test is NOT confirming an IS pass — the ensemble's IS
  crash gate is SPENT (failed, mis-anchored). The forward M-crash gate is the FIRST clean, properly-
  anchored crash adjudication, on genuinely unseen data. A forward SUCCESS is evidence for a deployment
  *decision*, not proof of a specific live Sharpe; the honest live expectation is the deflated band
  (~+0.70–0.95), never the IS +1.28.
- **Forward maxDD honest expectation:** the ensemble IS maxDD is −18.59% (tail empirically clipped), but
  forward tranche correlation could rise in stress (M-rho); a forward maxDD toward −25% … −28% is within
  the plausible working-book distribution, and FF-1 stops at −28% (the diversification-evaporated level) —
  a breach FAILS regardless of cause (a drawdown that deep is undeployable), with the concurrent `rho_bar`
  logged at any breach for attribution (rising rho_bar + deep DD = the M-rho risk materialized).

---

## §6 — Engineer handoff spec (what the QE must change in `blind_paper_l1.py`)

The runner already computes all 21 L1 + 21 V0 tranches weekly for the phase diagnostic — retarget the
gate evaluation from the single-phase Wed@00h book to the ensemble aggregate. Reuse `run_l1` / `run_v0`
/ `trim_panel` VERBATIM (single source of truth). No engine or tranche-construction change.

1. **Gates book = ENSEMBLE.** Build `ensemble_ret[t] = (1/21)·Σ_p mapped_tranche_ret_p[t]` on the common
   warmup=63 slice (the /007 alignment: map by `grid_ms`, common region first-True = warmup + max_p; IS
   index 83, forward analog). All §4 gates evaluate the ensemble equity/return; the single-phase book is
   no longer gate-bearing.
2. **Parity ABORT-guard = BOTH:** ensemble IS Sharpe **+1.2826 ± 0.005** (common slice) **AND** tranche
   p=0 IS Sharpe **+1.1638 ± 0.005** (+ V0 p0 +0.9134, ensemble maxDD −18.59% ±1pp, ensemble turnover
   50.3x ±2). Both assert every run — ties the runner to /007 AND the sweep. Also assert the full 21-row
   sweep reproduction (≤1e-6) and per-tranche + ensemble leg reconciliation (≤1e-12).
3. **V0-ENSEMBLE reference series (NEW):** compute the forward V0-ENSEMBLE (mean of the 21 V0 tranches)
   crash mean / mania mean / Sharpe on the forward window, for the relative gates (M-crash, M-mania,
   M-overlay). The runner already runs the 21 V0 tranches — aggregate them.
4. **Forward `rho_bar` (NEW):** each run, the mean pairwise Pearson correlation of the 21 tranche
   forward-return streams over `[T0, now)`, logged weekly (M-rho monitoring). Also log forward ensemble
   ann. vol (M-rho's second condition).
5. **Log schema (v2) + protocol tag:** every row carries `protocol = ENSEMBLE-L1-v2`. Add: ensemble
   aggregate equity row (ensemble equity / return / gross); ensemble decisions row (aggregate turnover /
   cost / funding; **C1-fired tranche count this candle**; **C2 excluded-name count this candle**, with
   names); the V0-ENSEMBLE reference series; forward `rho_bar` + ensemble vol. **Re-init `paper-l1/` logs
   for v2** (the retired protocol's logs are pre-T0 empty — zero forward rows — so re-init loses nothing;
   preserve the retired `runs.log`/`cron_runs.log` history as an audit trail, start fresh
   `equity.csv`/`decisions.csv`/`gates.csv` under the v2 schema).
6. **Append-invariance:** extend the bit-identity assert to the ensemble aggregate rows + the V0-ENS
   reference (a revised historical kline flips a past ensemble decision → trips the assert → ABORT, no
   append). Burned-window guard `[OOS_CUTOFF, T0)` extended to the ensemble path.
7. **Mechanism-gate counting (spec, per §4.1):** M-C1 / M-C2 are computed **per tranche then pooled
   across all 21 tranches** (each tranche contributes its own C1-fired weeks / C2 exclusions, weighted
   1/21); M-crash / M-mania / M-overlay use the ensemble vs the forward V0-ENSEMBLE on the same window;
   M-rho uses the tranche-return correlation matrix.
8. **Integrity re-pin (§7):** SHA256 of `blind_engine.py`, `blind_risk_calib_006.py`,
   `blind_mania_rule.py`, `blind_paper_l1.py` (now the ensemble construction + runner). Re-hash every run.
9. **Tests:** carry the /007 ensemble-alignment / common-mask + analytic-2x tests; ADD forward-row
   extraction for the ensemble aggregate, V0-ENSEMBLE reference computation, forward `rho_bar`
   computation, and append-invariance on the ensemble rows. All green + ruff clean before the proof run.
10. **Proof run + activation:** a clean end-to-end proof run via the scheduled path (parity PASS on BOTH
    anchors, append-invariance OK, 0 forward rows pre-T0, burned window sealed) establishes
    operational-readiness → the mechanical T0 rule (§2) fixes T0-A or T0-B. The systemd timer
    (`blind-paper-l1.timer`, Wed 00:10 UTC) is re-targeted, not duplicated.

---

## §7 — Integrity pins (populated by the QE at T0, before the first forward run)

```
blind_engine.py         SHA256: <pinned at T0>
blind_risk_calib_006.py SHA256: <pinned at T0>
blind_mania_rule.py     SHA256: <pinned at T0>
blind_paper_l1.py       SHA256: <pinned at T0>   (ensemble construction + runner)
T0 selected             : <T0-A 2026-07-15 or T0-B 2026-07-22, per the mechanical rule>
T0 panel extent         : <max grid_ms at T0 build>
```

Every subsequent weekly run re-hashes and alerts on drift (hash change ⇒ construction moved ⇒
clock-reset per §5). The append-invariance assert (§2/§6) covers the data side.

---

**FROZEN 2026-07-10.** The construction (equal-weight all-21-phase ENSEMBLE-L1), gates, thresholds,
horizon dates (both candidate T0s), the interpretation map, the extension rule, and the
principle/relative anchoring of every gate are locked before the first forward candle. This protocol
SUPERSEDES PROTOCOL-L1-FORWARD (retired pre-T0, zero forward data). No OOS was read; the burned window is
INPUT-history only; no backtest was run to author this contract. Any deviation is a new protocol version
with a new T0.
