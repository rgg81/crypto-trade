# iter-v1/032 — Research Brief (ETHUSDT): HIGH-VOL-CONDITIONED SHORT-HORIZON REVERSION FADE

**The breadth bet.** A genuinely DIFFERENT, higher-frequency, crypto-native edge for ETH — a
deterministic SHORT-HORIZON MEAN-REVERSION fade conditioned on a HIGH-VOLATILITY regime — designed
to produce MANY INDEPENDENT WINNING EVENTS where the iter-027 slow-trend edge cannot. IS-only design
+ feasibility evidence; **no backtest run yet** (orchestrator launches Phase 6).

- Analysis scripts (committed, IS-only, cutoff-asserted): `analysis/ETHUSDT/iteration_v1-032/`
  - `breadth_edge_screen.py` — head-to-head of edges A (mean-reversion) / B (faster-trend) / C (funding-carry)
  - `winner_robustness.py` — sub-period + crypto-mechanism probes (exposed faster-trend as a lucky spike)
  - `plateau_and_gate.py` — (W,N) plateau detector (faster-trend = noise grid, 2023+2024 negative)
  - `meanrev_deepdive.py` — pure-MR grid (mostly negative net of cost; high-vol conditioning helps)
  - `revvol_plateau.py` — FINAL: year-stability gate → the ONE passing cell
- Leak-safe scaffolding reused verbatim: `analysis/ETHUSDT/iteration_v1-030/_common.py` (cutoff
  `open_time < 1742774400000`, per-horizon `drop_horizon_crossing_oos`, `.shift(1)` primitives).

---

## Section 0 — Hypothesis

**ETH exhibits a tradeable short-horizon REVERSION snapback after a high-volatility price
overextension, and harvesting it at a 2-candle (16h) hold produces 6× more independent winning
events than the iter-027 slow-trend roster — broadening the OOS event base and slashing
single-trade concentration — WITHOUT the IS-edge inversion that killed the 4 de-concentration
levers (/028–/031).** Direction is DETERMINISTIC (fade the stretch: `dir = -sign(price_z)`), so it
cannot be overfit by a freely-learned LightGBM entry (the 2nd /031 finding: ETH's learned entry is
itself overfit). The LightGBM head supplies abstention/sizing only; the SIGN is rule-replaced.

## Section 0.5 — WHY this edge, WHY now (campaign context)

The iter-027 baseline (IS +0.6336 / OOS +0.0560) is a 14d let-winners-run TREND edge: ~82 IS / ~32
OOS trades, OOS carried by 1–2 concentrated trend-captures (top-2 ≈ 438% of weighted net). The
de-concentration campaign PROVED (4 mechanism families, all NEGATIVE — diary /031) that **you cannot
manufacture independent winning events by modifying the slow-trend trade structure.** The root cause:
breadth = MORE INDEPENDENT WINNING EVENTS, intrinsic to a DIFFERENT, higher-frequency edge — not a
re-slice/veto/modulate of the same ~82-event set. This iteration builds that different edge.

## Section 0.6 — Architecture-Family Justification

- **Axis family: `labeling`** (new label horizon + a NEW deterministic DIRECTION primitive —
  reversion-state — replacing the trend-state direction; short-hold fixed_horizon label).
- Prior ETH SPECIALIST families: /028–/029 model-arch (M2 veto), /030 labeling/conviction
  (AGREE_SCALE), /031 execution/exit + feature/entry-supply (multi-signal). 
- **Rotation status: VALID.** A reversion DIRECTION primitive + short-hold label is a distinct
  axis from every prior lever (all of which kept the trend direction + 14d hold and operated on the
  SAME event set). This is the first axis that changes the underlying EDGE, not its packaging.
- Rationale: the campaign's own closeout (diary /031, fork #1) prescribes "a different edge — a new
  strategy family with intrinsically more independent events (shorter-horizon / mean-reversion)."

---

## Section 1 — The deterministic signal + direction primitive (past-only, leak-safe)

**Trigger (overextension):** `price_z[t-1] = (close[t-1] − SMA10(close)[t-1]) / rolling_std10(close)[t-1]`,
fire when `|price_z[t-1]| ≥ 1.5`. (10-candle = ~3.3d short window; std over the same window.)

**Vol-regime gate (crypto mechanism — load-bearing):** fire ONLY when
`natr[t-1] = ATR14[t-1]/close[t-1] ≥ q40` (40th-pct of the past-only IS natr distribution; backtest
uses the per-month past-only quantile). **Reason from crypto mechanism:** reversion snapbacks are
driven by retail-flow exhaustion / liquidation-cascade overshoot / funding-overextension that
RESOLVES — these live in HIGH-volatility regimes. In low-vol drift, a z-extension is a trend
beginning, not an exhaustion (the proxy confirms: removing the vol gate flips the edge negative,
§2). This is the SOTA stat-arb pattern: "a sharp expansion beyond the bands signals exhaustion."

**Direction (DETERMINISTIC):** `dir = −sign(price_z[t-1])` — short the up-stretch, long the
down-stretch. Parameter-free; cannot overfit. NEW primitive `_compute_reversion_state` in `lgbm.py`,
structurally identical to `_compute_trend_state` (searchsorted past-only `close[t-1]`, SMA10/std10
over the window ending at `t-1`; returns None on warmup → conservative fall-back to model sign).

**Holding horizon:** N=2 candles (16h) — `fixed_horizon` label N=2, execution timeout 16h. Short
hold is essential: it caps cost-bleed and prevents the position drifting back into trend
continuation (§2 shows N≥3 weakens — pre-registered as the primary falsifier).

## Section 2 — IS-ONLY feasibility evidence (net of fee 0.1% + slippage 2bps/side = 0.24% round-trip)

**Head-to-head of the three candidate edges (best config per family, IS, net of cost):**

| edge | best config | events | trades/mo | win | per-trade Sharpe (ann) | top-2 gross share | verdict |
|---|---|---|---|---|---|---|---|
| baseline | iter-027 trend (14d) | 82 | 1.31 | 34% | (daily +0.63 series) | IS 0.073 / **OOS 0.44** | anchor |
| B faster-trend | trendSMA100_N6 | 818 | 13.0 | 49% | +0.63 | 0.020 | **lucky spike — REJECT** |
| C funding-carry | fade fz30 (any k,N) | 257–691 | 4–11 | 47–49% | **−0.16 … −0.47** | — | **dead — REJECT** |
| **A reversion (final)** | **pricez\|natr≥q40\|k1.5\|N2** | **485** | **7.7** | **53.8%** | **+0.43** | **0.028** | **breadth candidate** |

**Why B and C are rejected (honest):**
- **B (faster-trend)** posts a headline +0.63 at W=100/N=6, but the (W,N) joint grid is a NOISE
  FIELD — neighbors range −0.06…+0.24 (`plateau_and_gate.py`), the best 3×3-neighborhood-min is only
  +0.20, and EVERY robust variant is **negative in 2023 AND 2024** (the two years adjacent to the
  2025 OOS wall). It is a 2-parameter lucky spike that would very likely die OOS exactly like the
  de-concentration levers. REJECTED.
- **C (funding-carry)** is uniformly NEGATIVE on ETH IS — neither FADE nor FOLLOW nor funding-CONFIRM
  beats cost at any threshold (`winner_robustness.py` §4–5). Crypto reading: ETH funding gets extreme
  BECAUSE a strong directional move is underway → it is a (weak) continuation signal, not a clean
  reversion trigger, and the noise swamps the 0.24% cost. REJECTED.

**Edge A passes the decisive year-stability gate (the breadth premise check):**

`pricez|natr≥q40|k1.5|N2` is the ONLY high-frequency cell that is positive AND non-negative across
all OOS-adjacent recent years:

| metric | value | vs baseline / target |
|---|---|---|
| IS events | **485** | **5.9× the 82 trend roster** (target ≥ 2× = 164 → CLEARED 3×) |
| trades/month | 7.7 | vs 1.31 (intrinsically high-frequency) |
| win rate | 53.8% | a real >50% directional edge (vs 34% trend) |
| per-trade Sharpe (ann) | +0.43 | net of 0.24% round-trip |
| top-2 gross share | **0.028** | vs iter-027 IS 0.073 / **OOS 0.44** → ~16× de-concentrated |
| 2022 / 2023 / 2024 Sharpe | **+0.08 / +2.00 / +0.13** | all ≥ 0 (incl. the 2024 chop year that killed B & pure-MR) |
| active months | 63/63 | every IS month fires (mean 7.7/mo) |

**Crypto-native conditioning evidence (`meanrev_deepdive.py` §3):** removing the vol gate makes pure
z-fade NEGATIVE everywhere (best −0.07); gating on `natr≥q60` lifts it to +0.26 (2023:+5.19). The
vol gate is the mechanism, not a cosmetic filter — it isolates the exhaustion regime from trend
beginnings.

**Independence:** events fire across all 63 IS months (not clustered); top-2 gross 0.028 means NO
single trade dominates — the structural opposite of the iter-027 OOS (top-2 0.44). This is the
breadth the user mandated.

## Section 2.5 — HIGH-RISK Axis Declaration

- **Declaration: HIGH-RISK.** It changes Optuna's training-objective domain on TWO axes: (1) a NEW
  deterministic DIRECTION primitive (reversion-state replaces trend-state), and (2) a NEW short-hold
  label (fixed_horizon N=2 replaces N=42). This is a fresh edge, not a knob.
- **Reason:** entirely different label + direction → the learned head, gate calibration, and R-stack
  all see a new objective.
- **Mitigation:** N-sensitivity is the known fragility (the IS proxy's +0.43 is sharp at N=2; N≥3
  weakens). Pre-registered falsifier (§ below) on it. Run **single-seed EXPLORATION first** (v1 OPT-IN
  rule); if both-positive survives, the CONFIRMATION does the K=20 bagging validation. Honest cost
  model + consistent training_days + sacred constants intact.

## Section 3 — Design spec for iter-032 (the exact config to backtest)

Maps to `run_baseline_v1.py` single-symbol machinery via the `_spec_*` overrides; ONE new primitive
for the QE to implement in `lgbm.py` (analogous to `_compute_trend_state`).

**Label (NEW):**
- `label_mode = "fixed_horizon"`, `use_atr_labeling = False`
- `label_timeout_minutes = 960` (N=2 candles × 8h = 16h), `execution_timeout_minutes = 960`

**Direction primitive (NEW — QE implements):**
- `enable_reversion_state_dir = True` (new flag, mirrors `enable_trend_state_dir`)
- `_compute_reversion_state(open_time)`: past-only `price_z = (close[t-1] − SMA10[t-1]) / std10[t-1]`;
  return `−1 if price_z > 0 else +1` (fade); return `None` on warmup (<10 closes) → conservative
  fall-back to model sign. Built with the SAME searchsorted past-only lookup + leak-safety contract
  as `_compute_trend_state` (close_time ≤ candle_open_time selects candle t-1). Add a
  `reversion_state_window = 10` param. Wire the override at the same site as the trend-state override
  (`lgbm.py` ~line 2971), logging `kind="reversion_state_override"` for Phase 7.4 attribution.
- The TRIGGER `|price_z| ≥ 1.5` AND vol-gate `natr ≥ q40` are entry GATES (abstain when not met),
  implemented as a RULE-layer abstention gate analogous to the trend-strength gate
  (`enable_reversion_trigger_gate = True`, `reversion_z_threshold = 1.5`,
  `reversion_natr_quantile = 0.40`, both past-only per-month quantile / fixed-z). Where the gate
  quantity is NaN (warmup) → CONSERVATIVE: abstain (no trade), since a reversion edge with no valid
  z is undefined (DIFFERENT from trend-state's conservative-FIRE — record this in the QE note).

**Features:** existing V1 19-col HYBRID set (`V1_BTC_ITER009_FEATURES`) — the head only does
abstention/sizing; the direction is rule-supplied, so features need not change for the first cut.
(If the QE prefers, a short-window reversion subset is a follow-up axis, not this iteration.)

**Execution / TP-SL:** `atr_tp = 100.0` (non-binding; the 16h timeout binds — a reversion edge exits
on time, not on a profit target), `atr_sl = 1.45` (keep the ETH-calibrated stop; a reversion trade
against a continuing move must be cut). Conviction gate from iter-027 (`enable_trend_strength_gate`)
**OFF** — replaced by the reversion trigger gate.

**Risk stack:** R2 drawdown brake ON, ETH-calibrated (trigger 4.07 / anchor 16.27 / floor 0.20) —
unchanged from iter-027. R3 OOD ON (0.70). R5 vol-target ON (0.3). R1 OFF. TREND-SCALE OFF,
funding-readmit OFF.

**Costs / constants:** fee 0.1% + slippage 2.0 bps/side. `OOS_CUTOFF=2025-03-24`,
`training_months=24`, embargo intact.

**Run (EXPLORATION, single-seed):**
```
run_baseline_v1.py --exploration --iteration 32 --symbols ETHUSDT --n-trials 18 --slippage-bps 2
```
(K=1 bagging for EXPLORATION; if both-positive, CONFIRMATION re-runs at K=20.)

## Section 4 — Pre-registered falsifiers + breadth target (PASS/FAIL, set BEFORE backtest)

**Breadth target (the point of the iteration):**
- OOS events **≥ 64** (≈ 2× the iter-027 OOS roster of 32; the IS proxy implies ~7.7/mo → OOS span
  ~7.5 mo → ~58 raw, the head's abstention will trim; ≥64 is the breadth bar). 
- OOS **top-2 trade share < 0.30** of OOS net (vs iter-027 OOS 0.44) — the de-concentration claim.

**Both-positive coherence (the merge PRIMARY):**
- IS Sharpe > 0 AND OOS Sharpe > 0 (the durable claim; magnitude anchored modestly, NOT chased —
  per BASELINE caveat #1 the K=5→K=20 lesson).

**Falsifiers (any TRUE → NEGATIVE, honest closeout, NO retune):**
1. **N-fragility realized:** if OOS Sharpe < 0 while IS > 0, the N=2 spike was a proxy artifact —
   the head/cost interaction at backtest fidelity broke it. (Primary risk per §2.5.)
2. **Vol gate doesn't transfer:** if the reversion-override trades show no win-rate edge in the
   high-vol regime OOS (Phase 7.4 attribution: override win rate ≤ 50%), the mechanism didn't hold.
3. **Concentration not improved:** OOS top-2 share ≥ 0.44 (no better than the trend baseline) → the
   breadth premise failed even if Sharpe is positive.
4. **Edge inverts (the /030 trap):** IS Sharpe < 0 → the reversion direction is wrong-signed at
   backtest fidelity (the proxy's +0.43 was non-representative). Immediate NEGATIVE.

**Expected OOS impact (honest, distribution not point):** modest positive OOS Sharpe (~+0.1 to +0.4
band) with a BROAD base (≥64 events, top-2 < 0.30). The win is a DE-CONCENTRATED both-positive OOS,
NOT a higher absolute return than the trend edge. If it lands both-positive with breadth, it is a
CONFIRMATION candidate and a template for other coins; if Sharpe is positive but thin, it still
demonstrates the different-edge thesis and informs the next axis.

## Section 5 — Risk Mitigation

- **R2 (DD brake)** ETH-calibrated, ON — the principal protection against a reversion-fade regime
  where ETH trends hard against the fade (the 2024-style risk); it scales size down as cumulative DD
  builds. IS-calibrated (iter-026 maxDD 62.6 → trigger 4.07 / anchor 16.27), simulated effect:
  cut IS DD 62.6%→23.8% on the trend stack; re-validated on this label in Phase 6.
- **Short 16h hold + ATR SL 1.45** is itself the first-line risk control — a reversion trade that is
  wrong is closed within 2 candles or stopped, never held into a 14d trend loss.
- **Vol-gate abstention** removes the low-vol-drift regime where reversion fails (the loss regime,
  per §2) — a structural risk filter, not just an alpha filter.
- **R3 OOD (0.70)** + **R5 vol-target (0.3)** unchanged.
- **Kill-switch:** abandon mid-flight if Phase 6 IS Sharpe < 0 (falsifier 4 — the proxy was wrong).

## Section 6 — SOTA / crypto-native grounding

Short-horizon mean-reversion is the canonical statistical-arbitrage regime ("broadly diversified,
held for short periods, seconds to days," contrarian mean-reversion principle; "mean reversion works
at shorter horizons — intraday to a few days") — the N=2 (16h) hold sits squarely in it. The z-score
±1.5–2 / Bollinger-overextension trigger is the canonical contrarian signal, and "a sharp expansion
beyond the bands signals exhaustion" — exactly the high-vol-conditioned z-fade. The mechanism is
crypto-specific: 2024–25 saw repeated liquidation-cascade overshoots (Dec-2024 7% flash crash, $400M
long liquidations; Q3-2025 record single-day liquidations, ETH > BTC, leverage to 125×) that produce
the overextension-then-snapback this edge harvests. The literature's calibration discipline is
respected: a 1.4–1.5 Sharpe is "good," >3 "should make you suspicious" — our IS proxy per-trade
+0.43 ann. is plausible, not suspicious, and we anchor OOS expectations modestly.

Sources:
- [Statistical arbitrage — Wikipedia](https://en.wikipedia.org/wiki/Statistical_arbitrage)
- [Statistical Arbitrage in Crypto Algorithmic Trading — WindfallCapital](https://www.linkedin.com/pulse/statistical-arbitrage-crypto-algorithmic-trading-windfallcapital-tosxf)
- [A 2+ Sharpe Market-Neutral Statistical Arbitrage Strategy in Cryptocurrency — R. Lui](https://medium.com/@luitingronald.us/a-2-sharpe-market-neutral-statistical-arbitrage-strategy-in-cryptocurrency-0f0b7728cf1e)
- [Perpetual Momentum: How Q3 2025 Redefined Crypto Derivatives — AMINA Bank](https://aminagroup.com/research/perpetual-momentum-how-q3-2025-redefined-crypto-derivatives/)
- [Bitcoin's $2B Reckoning: November's Liquidation Cascade — Coinchange](https://www.coinchange.io/blog/bitcoins-2-billion-reckoning-how-novembers-liquidations-cascade-exposed-cryptos-structural-fragilities)
- [Explainable Patterns in Cryptocurrency Microstructure — arXiv 2602.00776](https://arxiv.org/html/2602.00776v1)
