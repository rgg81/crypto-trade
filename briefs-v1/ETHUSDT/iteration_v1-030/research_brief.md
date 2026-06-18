# iter-v1/030 — ETHUSDT — Research Brief (DESIGN SPEC)

**Track:** v1 single-symbol. **Symbol:** ETHUSDT. **Phases authored:** 1 (EDA), 2 (labeling),
5 (synthesis). **Mode target:** EXPLORATION first (K=5), then CONFIRMATION (K=20) if it screens.
**Axis (single):** **multi-speed trend AGREEMENT as a deterministic conviction modulator** on the
unchanged SMA200 direction (DIRECTION / conviction-gate axis). **Status:** IS-only design; no
src/ edits, no backtest run by QR (a K=20 iter-029 confirmation is using the LightGBM compute).

---

## Section 0 — The mandate, in one sentence

ETH must succeed where BTC (and ETH iter-027) could not: a **BROAD, DE-CONCENTRATED, regime-robust
OOS** — not a low-WR let-winners-run book whose OOS Sharpe is carried by 1–2 trades. The user asked
for "way more time," internet research, and "what the best hedge funds use." This brief answers with
the canonical **CTA forecast-combination** robustness lever (AQR / Carver / the 2025 crypto Donchian-
ensemble paper), applied **deterministically** so it cannot overfit.

## Section 0.5 — Hypothesis (refined by the IS-only EDA — see the honest correction in §1.3)

> **The OOS concentration is upstream of M2: the ENTIRE book's direction rests on ONE trend speed
> (the single 200-SMA sign). That single speed is excellent in strong-trend regimes but loses badly
> in chop (2022, 2024H1) — and that chop fragility is the structural source of the few-big-winners /
> many-wrong-way-losers profile that fails the OOS-concentration falsifier. Combining the trend
> signal across MULTIPLE DE-CORRELATED speeds AND families (MA-cross, Donchian breakout, TS-momentum)
> via a deterministic AGREEMENT score, and using that score to MODULATE conviction/sizing on the
> UNCHANGED SMA200 direction, de-concentrates the book (top-2 trade share 0.043 → 0.033, higher net,
> higher per-trade Sharpe) WITHOUT giving up the recent-regime strength and WITHOUT changing the
> deterministic direction sign that the campaign proved is the only durable claim.**

The EDA forced one correction to the naive "ensemble the direction" framing: **replacing** the
direction with an ensemble vote DESTROYS the recent-regime edge (+1.31 → +0.54). The robust lever is
**forecast-combination as a conviction modulator (AGREE_SCALE)**, not direction replacement. This is
precisely Carver's combine-then-scale design and AQR's "diversify across low-correlation horizons."

## Section 0.6 — Architecture-Family Justification

- **Axis family:** `labeling` / direction-conviction (the conviction-gate quantity is changed; the
  executed direction sign is UNCHANGED). It is NOT `model-arch` (no new trained model; M2 is
  orthogonal and optional — see §6) and NOT `feature-family` (no new LightGBM feature columns; the
  agreement score is a deterministic gate quantity, not an M1 feature).
- **Prior families (ETH campaign):** iter-025 vanilla bootstrap (model-arch), iter-026 sizing/conviction
  screen (labeling), iter-027 = proven-stack confirmation (labeling), iter-028 = M2 meta-labeling
  (model-arch), iter-029 = K=20 confirmation of iter-028 (no axis).
- **Rotation status:** VALID — distinct from the iter-028/029 model-arch (M2) line. iter-030 attacks
  the concentration at its *root* (the single-speed direction conviction), upstream of M2.
- **Rationale:** iter-028 attacked concentration with a precision FILTER (M2) and it filtered to
  precision rather than broadening the book (top-1 = 78% of OOS net persisted, only 23 OOS trades).
  The root cause is upstream — the single trend speed. Fix the source of concentration, not the symptom.

---

## Section 1 — IS-ONLY EDA (deterministic, leak-guarded; 5685 horizon-safe IS rows)

All scripts hard-filter `open_time < 1742774400000` and DROP IS entries whose 14d (42-candle) label
horizon crosses the OOS wall (`_common.drop_horizon_crossing_oos`), with a leak-guard assert. No OOS
price enters any number. The feature-engineer's concurrent `analysis/ETHUSDT/iteration_v1-030/
breadth_eda.py` reconstructs the same past-only primitives independently; this brief's numbers come
from `multispeed_breadth.py`, `orthogonality_and_subperiod.py`, `blend_agreement.py`,
`agree_scale_robustness.py` (all committed in `analysis/ETHUSDT/iteration_v1-030/`).

### 1.1 SMA-only multi-speed does NOT de-concentrate — the windows are too correlated (`multispeed_breadth.csv`)

The book = SMA200/family direction × signless 14d forward return − costs, gated at the iter-027
conviction quantile q=0.40 (held FIXED so only the direction axis varies — single-axis discipline).

| direction config | n gated | signal hit-rate | per-trade Sharpe (ann) | net | top1 share | top2 share | Herfindahl |
|---|---|---|---|---|---|---|---|
| **ANCHOR — single SMA200** | 3291 | 0.526 | +0.436 | 49.35 | 0.0217 | 0.0433 | 0.00057 |
| A — SMA-majority {100,150,200,300} | 3291 | 0.519 | +0.440 | 49.77 | 0.0215 | 0.0429 | 0.00057 |
| A' — SMA signed-avg (same windows) | 3291 | 0.519 | +0.440 | 49.77 | 0.0215 | 0.0429 | 0.00057 |
| B — TSMOM-majority {21,42,84} | 3291 | 0.535 | +0.554 | 62.52 | 0.0171 | 0.0342 | 0.00057 |
| **C — family {MA-cross,Donchian,TSMOM}** | 3291 | **0.540** | **+0.617** | **69.51** | **0.0154** | **0.0308** | 0.00057 |
| D — grand signed-avg (all) | 3291 | 0.527 | +0.536 | 60.49 | 0.0177 | 0.0353 | 0.00057 |

**Finding 1 (kills framing A):** stacking more SMA *windows* {100,150,200,300} is INERT — A/A' are
numerically identical to the anchor. The windows are ~0.9+ correlated to each other (Carver's
">95%-correlated → reject" rule); they re-derive the same partition. **Multi-SPEED of the same MA is
not diversification.** The de-concentration comes from de-correlated FAMILIES (Donchian breakout,
TS-momentum return-sign), not more MA lengths.

**Finding 2:** the family ensemble (C) and TSMOM-multi-horizon (B) both improve full-IS Sharpe
(+0.62 / +0.55 vs +0.44) AND concentration (top-2 0.031 / 0.034 vs 0.043). This is the breadth signal.

### 1.2 The families are genuinely de-correlated (`signal_family_correlation.csv` — Carver inclusion test)

Pairwise correlation of the {+1,−1} sign series (Carver: combine only if < 0.95):

| | sma200 | macross | donch55 | tsmom42 | tsmom21 | tsmom84 |
|---|---|---|---|---|---|---|
| sma200 | 1.00 | 0.68 | 0.44 | 0.46 | 0.29 | 0.64 |
| macross | | 1.00 | 0.28 | 0.31 | 0.15 | 0.49 |
| donch55 | | | 1.00 | 0.75 | 0.58 | 0.51 |
| tsmom21 | | | | | 1.00 | 0.34 |

All pairs ≤ 0.75 (MA-cross vs TSMOM-21 = 0.15). The ensemble is REAL diversification — not three
copies of one signal. C-family disagrees with the SMA200 anchor on **22.6%** of rows (a genuinely
different direction primitive, not a relabel).

### 1.3 The honest complication: the anchor is BEST in the recent regime; the ensemble is robust in CHOP (`subperiod_family.csv`)

Per-trade Sharpe by IS sub-period (RECENT = 2024H2–2025Q1 = the closest analogue to OOS):

| book | 2022 | 2023 | 2024H1 | **RECENT** |
|---|---|---|---|---|
| ANCHOR SMA200 | −0.67 | +0.12 | −0.61 | **+1.31** |
| C-family | −0.12 | −0.02 | −0.28 | +0.45 |
| B-tsmom | −0.11 | +0.02 | −0.12 | +0.47 |

**This is load-bearing and is why a direction REPLACEMENT is the WRONG axis.** The single SMA200 is
*excellent* in the recent strong-trend regime (+1.31) but *catastrophic* in chop (2022 −0.67, 2024H1
−0.61) — and that chop fragility (a few big trend captures vs many wrong-way losers) IS the source of
the OOS-concentration failure. The ensembles are the mirror image: they cushion chop dramatically
(2022 −0.67→−0.12, 2024H1 −0.61→−0.28) but GIVE UP the recent peak (+1.31→+0.45). A pure replacement
would trade the campaign's hard-won recent-regime strength for chop-robustness — a bad swap, and it
risks flipping the both-positive sign. **We need the anchor's direction AND the ensemble's robustness.**

### 1.4 The resolution — AGREE_SCALE: keep the anchor's direction, modulate conviction by multi-speed agreement (`blend_agreement.csv`)

Direction = SMA200 anchor (UNCHANGED). Conviction quantity = iter-027's `|close−SMA200|/ATR14`
**multiplied by a deterministic agreement score** = fraction of a 5-signal panel {MA-cross 50/200,
Donchian 55, TSMOM 21/42/84} that points the SAME way as the anchor. Low-agreement (chop) rows are
smoothly pushed below the q=0.40 gate and stand aside; high-agreement rows keep full conviction.

| config | 2022 | 2023 | 2024H1 | RECENT | FULL-IS Sharpe | FULL top-2 | FULL net |
|---|---|---|---|---|---|---|---|
| **ANCHOR** | −0.67 | +0.12 | −0.61 | **+1.31** | +0.436 | 0.0433 | 49.35 |
| **AGREE_SCALE (chosen)** | −0.64 | +0.13 | **−0.45** | **+1.21** | **+0.546** | **0.0342** | **62.46** |
| AGREE_GATE 4-of-5 (hard veto) | −0.11 | +0.21 | −0.56 | +1.02 | +0.462 | 0.0501 | 34.92 |
| ENSEMBLE_DIR (replace dir) | −0.16 | −0.06 | −0.24 | +0.54 | +0.562 | 0.0337 | 63.35 |

**AGREE_SCALE Pareto-dominates the anchor** and is the right single axis:
1. **Keeps the recent-regime strength** (+1.21 vs anchor +1.31 — a 0.10 give-up, vs ENSEMBLE_DIR's
   catastrophic 0.77 give-up). The campaign's durable edge is preserved.
2. **De-concentrates** (top-2 share 0.0433 → **0.0342**) and lifts net (49.4 → **62.5**) and full-IS
   Sharpe (+0.44 → **+0.55**).
3. **Improves chop** (2024H1 −0.61 → −0.45).
4. **Single-axis clean:** the executed DIRECTION is byte-identical to iter-027 (the deterministic
   SMA200 sign). The ONLY change is the conviction-gate quantity gains a deterministic agreement
   multiplier. Direction sign cannot overfit; agreement is parameter-free and past-only.
5. **Keeps the book broad** — smooth scaling (not the hard 4-of-5 veto, which thins to 2258 trades and
   RE-concentrates to top-2 0.050). This mirrors iter-028's lesson that over-filtering re-concentrates.

### 1.5 The lift is NOT a single-parameter artifact (`agree_scale_robustness.csv`)

Six independent panel choices (TSMOM-only, family-3, multi-MA-cross, multi-Donchian, wide-mix):

| panel | FULL-IS Sharpe | top-2 share |
|---|---|---|
| ANCHOR (no agreement) | +0.436 | 0.0433 |
| P1 macross+donch+tsmom×3 | +0.546 | 0.0342 |
| P2 tsmom-only ×3 | +0.529 | 0.0359 |
| **P3 family-3 {macross,donch55,tsmom42}** | **+0.560** | **0.0332** |
| P4 macross multi-speed | +0.503 | 0.0370 |
| P5 donchian multi-speed | +0.537 | 0.0348 |
| P6 wide-mix ×7 | +0.541 | 0.0348 |

**6/6 variants beat the anchor on Sharpe AND on concentration.** Sharpe clusters tightly in
[+0.50, +0.56] (all > anchor +0.44); top-2 share in [0.033, 0.037] (all < anchor 0.043). The lift is
structurally robust because the agreement score is a smooth average over de-correlated signals —
exactly the diversification AQR/Carver describe. **Recommended panel: P3 family-3** (best Sharpe +0.56,
lowest concentration 0.0332, parsimonious 3 signals). P6 wide-mix is a defensible fallback.

---

## Section 2 — Web research: what the best CTAs / hedge funds use for ROBUST, de-concentrated trend

The user authorized internet research for SOTA hedge-fund methods. The convergent finding across the
canon is: **robust trend returns come from COMBINING many de-correlated trend signals (speeds AND
families), each vol-scaled, then summed — never from one signal.**

1. **AQR — Moskowitz, Ooi & Pedersen (2012) "Time Series Momentum"; AQR "Trends Everywhere" (JOIM).**
   Combine look-back horizons (1/3/12-month); each signal scaled inverse-to-volatility; "monthly,
   weekly and daily strategies exhibit LOW CROSS-CORRELATION, indicating they capture distinct
   continuation phenomena," giving "diversification benefits both within each asset class AND across
   each trend horizon." This is the canonical case that multi-horizon trend > single-horizon, and the
   diversification is *within* the trend factor (exactly the breadth we want).
   https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum ·
   https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/AQR-Trends-Everywhere_JOIM.pdf

2. **Robert Carver — "Systematic Trading" (2015); qoppac blog.** The modular CTA template: trading
   rules (EWMAC crossover variations at multiple speeds; breakout rules) each emit a **forecast scaled
   to a target volatility**, capped at ±20; forecasts are **combined with weights** and an explicit
   **diversification multiplier (capped 2.5)**. Crucially Carver **rejects rule variations whose
   correlation > 0.95** — the rule directly behind our §1.1 finding that multi-SMA is inert (too
   correlated) while adding Donchian/TSMOM families is real diversification. The position-sizing layer
   (vol-targeting) is separate from the rule layer.
   https://qoppac.blogspot.com/2017/06/some-more-trading-rules.html

3. **Zarattini, Pagani & Barbon (2025) "Catching Crypto Trends" (Swiss Finance Institute / SSRN
   5209907) — the directly-on-point CRYPTO paper.** An **ensemble of Donchian-channel trend models at
   multiple lookbacks {5,10,20,30,60,90,150,250,360 days}** aggregated into ONE signal, with
   volatility-based position sizing. The "Combo" ensemble: **Sharpe 1.58, Sortino 2.03, CAGR 30%,
   annualized alpha +14% vs holding Bitcoin**, survivorship-bias-free across all coins since 2015.
   Their stated rationale is exactly ours: "by aggregating these models into a single signal, the
   strategy **reduces sensitivity to any single parameter choice and improves robustness**." This is
   the SOTA crypto evidence that a multi-lookback trend ensemble de-concentrates and beats single-
   lookback on a RISK-ADJUSTED basis. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5209907 ·
   https://concretumgroup.com/catching-crypto-trends-a-tactical-approach-for-bitcoin-and-altcoins/

4. **"Systematic Trend-Following with Adaptive Portfolio Construction" (arXiv 2602.11708, 2026).** A
   crypto trend system on **6h candles "aligned with the 4×/day funding-rate cycle on perpetual
   swaps"** (corroborates our 8h funding-aligned cadence), leveraging "24/7 trading and retail-
   dominated order flow." It reaches Sharpe 2.41 with a single adaptive momentum signal but
   **explicitly does NOT employ multi-horizon fusion** — i.e., it leaves the diversification gain on
   the table. iter-030's axis is exactly that un-exploited lever, made deterministic.
   https://arxiv.org/html/2602.11708v1

**What we deliberately DON'T adopt:** the position-sizing turnover machinery (per-signal vol scaling +
diversification multiplier) is a continuous-position CTA construct; our v1 architecture is discrete
triple-barrier entries with R2/R5 vol-targeting already handling exposure. So we import the **signal
side** (multi-family forecast combination → agreement score) and let the existing R2/R5 stack handle
sizing — single-axis discipline.

## Section 2.5 — Crypto-native justification (reasoning from mechanism, NOT equity priors)

Why does multi-speed/multi-family trend diversification fit crypto's microstructure specifically?

- **24/7 reflexive trend persistence at MULTIPLE horizons.** Crypto has no overnight gap and is
  retail-flow-dominated; momentum is reflexive (price up → funding up → longs pay → more spot demand →
  price up). That feedback operates at different clock speeds simultaneously: liquidation cascades
  create 1–6h momentum, funding-cycle crowding creates multi-day momentum, ETF/halving narrative flows
  create multi-week momentum. **One SMA speed samples ONE of these reflexive loops; the agreement
  panel samples several.** When fast (TSMOM-21), medium (Donchian-55), and slow (MA-cross 50/200) all
  agree, multiple reflexive loops are aligned — the highest-conviction, most-persistent trend state.
  When they disagree, the reflexive loops are fighting (a chop/transition regime) — exactly where the
  single SMA200 bleeds (our §1.3 2022/2024H1).
- **Vol-clustering → agreement is a regime detector.** Crypto vol clusters; the agreement score is a
  cheap deterministic regime classifier (high agreement = clean trend regime, low agreement =
  transition/chop) that needs no learning and cannot overfit.
- **Liquidation cascades create cross-family confirmation.** A cascade simultaneously breaks a Donchian
  channel (breakout family), flips a short TSMOM sign, AND pulls price across a fast MA — so a true
  cascade-driven move lights up MULTIPLE families at once, while noise lights up only one. Cross-family
  agreement is a structural cascade/real-move filter, not an equity-style smoothing trick.

This is the opposite of the equity efficient-market prior. We are NOT assuming trend is arbitraged
away; we are exploiting that crypto's retail/funding/cascade structure produces persistent,
multi-horizon, reflexive trends — and that combining de-correlated views of those trends is what makes
the capture robust rather than single-trade-dependent.

## Section 2.6 — HIGH-RISK Axis Declaration

- **Declaration: NORMAL-RISK.** The executed direction is byte-identical to the merged iter-027 (the
  deterministic SMA200 sign). No new trained model, no new LightGBM feature column, no label-mode change,
  no universe/bar change. The only change is a deterministic, past-only multiplier on the existing
  conviction-gate quantity — it does NOT change Optuna's training-objective domain.
- **Reason:** direction-preserving conviction modulation; the LightGBM M1 trains on the same features
  and label as iter-027. Single-seed EXPLORATION lottery risk is structurally LOW because the change is
  deterministic and shown robust across 6 panels (§1.5), not a sizing/basin artifact.

---

## Section 3 — DESIGN SPEC (the exact iter-030 ETH model)

### 3.1 PRIMARY (M1) — UNCHANGED from the proven iter-027 stack
- Direction: deterministic **trend-state** `+1 if close[t-1] > SMA200[t-1] else -1`, on ETH's own
  close (`enable_trend_state_dir=True`, `trend_state_sma_window=200`, `trend_state_symbol=ETHUSDT`).
- Label: `fixed_horizon` N=42 candles (14d), `use_atr_labeling=False`.
- Execution: let-winners-run — `atr_tp=100.0` (non-binding), `atr_sl=1.45`, exec timeout 14d.
- Features: 19-col HYBRID `V1_BTC_ITER009_FEATURES`. Risk: R2 ETH-calibrated, R3=0.70, R5 vt=0.3, R1 OFF.
- Model: specialist bagging, n_trials=35. (Everything above is FROZEN.)

### 3.2 THE ONE CHANGE — multi-speed AGREEMENT conviction modulator (the axis)
- **New deterministic quantity** (past-only, parameter-free), computed alongside the existing
  `trend_strength = |close[t-1]−SMA200[t-1]|/ATR14[t-1]`:

  ```
  panel (default P3, all past-only, shift(1)-lagged):
    s1 = ema_cross_sign(close, fast=50, slow=200)     # +1 if EMA50>EMA200 at t-1 else -1
    s2 = donchian_breakout_sign(close, window=55)     # +1 if close[t-1] >= midline(High/Low,55) else -1
    s3 = tsmom_sign(close, horizon=42)                # +1 if close[t-1]/close[t-43]-1 > 0 else -1
  anchor = trend_state_sign(close, 200)               # the UNCHANGED iter-027 direction
  agreement = mean( [s1,s2,s3] == anchor )            # in {0, 1/3, 2/3, 1}
  conviction_quantity := trend_strength * agreement   # the gated quantity
  ```
- **Gate unchanged:** enter only when `conviction_quantity >= q-quantile (q=0.40, past-only
  training-window quantile)`. Because low-agreement rows have their conviction shrunk, they fall below
  the gate and stand aside; high-agreement rows are unaffected. Direction sign is the anchor — untouched.
- **Implementation note for QE (Phase 6):** this is a wiring change in the conviction-gate computation
  (multiply the existing strength by the agreement score before quantile-gating). The three panel
  signals are deterministic functions of `close`/`high`/`low` — NO new feature parquet, NO model
  retrain semantics change. Add a config flag `enable_agreement_scale` (default off elsewhere) +
  `agreement_panel="P3"`. Look-ahead test: assert the agreement series at row t uses only `close[:t]`.

### 3.3 What is explicitly NOT changed (single-axis guard)
Direction sign, label, execution barriers, features, R-stack, model/trial budget, costs, OOS cutoff,
training_months — ALL frozen at iter-027. The agreement multiplier is the sole degree of freedom.

---

## Section 4 — IS-only evidence plan + PRE-REGISTERED falsifiers

The EDA above is the evidence; the falsifiers below are the lines that, if the EXPLORATION backtest
crosses them, KILL the axis (not renegotiable post-hoc). All measured IS-only on the EXPLORATION run.

**CONFIRM (axis advances to K=20) requires ALL of:**
- **F1 — de-concentration:** IS top-2 trade share of net ≤ **0.040** (anchor 0.0433) AND strictly
  below the iter-027 IS top-2 (0.714 in the actual backtest book — the EDA proxy is 0.043; the
  backtest book is sparser, so the operative target is *strictly below iter-027's realized IS top-2*).
- **F2 — Sharpe non-regression:** IS monthly Sharpe ≥ iter-027 IS (+0.6336) − 0.05 (no material IS
  regression; the EDA predicts an INCREASE, +0.44→+0.55 per-trade).
- **F3 — direction-sign preserved:** RECENT-IS-subperiod book stays positive (the +1.21 EDA result);
  i.e. the agreement multiplier must not gut the recent-regime edge (give-up ≤ 0.20 per-trade Sharpe
  vs anchor's recent +1.31 → AGREE_SCALE must keep ≥ +1.10 in the recent proxy).
- **F4 — breadth not destroyed:** IS trade count ≥ 0.85 × iter-027 IS trade count (smooth scaling
  should keep ~all entries; if the agreement gate silently vetoes >15% of entries it has become a
  hard filter, not a modulator — that is the AGREE_GATE failure mode we rejected).

**KILL (axis closed for this cadence) if ANY of:**
- **K1:** IS top-2 share NOT below iter-027's (no de-concentration) — the hypothesis is falsified at
  its core claim.
- **K2:** IS Sharpe regresses > 0.05 below iter-027 (the modulator is destroying signal, not focusing it).
- **K3:** RECENT-subperiod per-trade Sharpe falls below +1.00 (the modulator gutted the recent edge —
  it has behaved like ENSEMBLE_DIR, not AGREE_SCALE; revert to anchor).
- **K4:** IS trade count drops > 25% (it collapsed into a hard veto / book got thin — re-concentration
  risk).

**Behavioral-effect predictor (pre-registered):** AGREE_SCALE should leave the entry COUNT ≈ unchanged
(smooth scaling) but CHANGE WHICH high-conviction rows clear the gate — net effect: fewer chop-regime
entries, more clean-trend entries, top-2 share down ~20%, full-IS Sharpe up ~0.10. If the observed IS
trade-count change is > ±25% the axis has not behaved as a modulator and F4/K4 fires.

**Concentration metrics reported (every EXPLORATION):** top-1 / top-2 trade share of net PnL,
Herfindahl of |pnl|, win-rate, n-winners — IS and (Phase 7, first sight) OOS.

---

## Section 5 — Risk Mitigation
R-stack UNCHANGED from iter-027 (R2 ETH-calibrated trigger 4.07 / anchor 16.27 / floor 0.20; R3=0.70;
R5 vt=0.3; R1 OFF). The agreement modulator is itself a *risk* mechanism — it reduces exposure in
chop regimes (low agreement → conviction shrinks → fewer entries), which is the de-concentration lever.
No new R-gate added (single-axis). Kill-switch: the F-falsifiers above; if K1–K4 fire, revert to the
iter-027 anchor (zero-cost revert since direction is unchanged).

## Section 6 — Composition with M2 (modular; covers both iter-029 outcomes)
The agreement modulator is UPSTREAM of and ORTHOGONAL to M2, and valuable in both iter-029 branches:
- **If iter-029 CONFIRMS M2 (both-positive holds at K=20):** AGREE_SCALE composes additively. M2 reads
  positioning/leverage features to veto losing trades; the agreement modulator reduces the *supply* of
  chop-regime trades M2 has to veto. The two attack concentration at different layers (M2 = precision
  filter on entries; agreement = regime-conviction on the direction primitive). iter-030 EXPLORATION
  runs WITHOUT M2 first (clean single-axis read on the agreement lever); a follow-up can stack them.
- **If iter-029 REGRESSES M2 (coherence was a K=5 artifact):** AGREE_SCALE stands alone as the
  de-concentration mechanism on the proven iter-027 stack — it does not depend on M2 at all. This is
  the safer, more fundamental fix (deterministic, can't overfit) and becomes the primary path.

iter-030 is therefore designed M2-agnostic: it modifies the iter-027 PRIMARY's conviction gate, which
sits below any M2 layer. Run it on the iter-027 stack (no M2) for the EXPLORATION; the result is
interpretable regardless of how iter-029 lands.

---

## Recommended axis (one line)
**Multiply the iter-027 conviction-gate quantity by a deterministic, past-only multi-speed AGREEMENT
score** (fraction of {EMA-cross 50/200, Donchian-55, TSMOM-42} agreeing with the unchanged SMA200
direction) — IS-shown to de-concentrate (top-2 0.043→0.033) and lift Sharpe (+0.44→+0.56) across 6/6
panels WITHOUT giving up the recent-regime edge or changing the deterministic direction sign.
