# BRIEF — iter-v2-002 EXPLORATION: cross-sectional momentum on rank 21–40

**Track:** portfolio-iteration-v2 (L/S rank-21–40 mid-cap perps).
**Type:** EXPLORATION — ONE change. Add a **cross-sectional momentum (XS-mom)** signal to the
rank-21–40 book. OOS is HIDDEN until the single CONFIRMATION reveal (skill §5; audit fix #4).
**Anchor:** iter-v2-001 — trend+carry on rank 21–40, PIT pool + slippage. IS **+1.53** / OOS **+0.01**
(−0.12 under pessimistic slip). Strong-IS / dead-OOS: the recent regime (2024→26) faded directional
mid-cap trend to ~0 while mega-cap trend kept working (v1-honest OOS +1.49).
**The bet of this iteration:** the anchor died because *directional* (time-series) trend on mid-caps
stopped paying — but the *relative* ordering of mid-caps (who is winning vs who is losing **within the
band**) still carries information. XS-mom is a different signal CLASS (dollar-neutral relative
strength), not a re-skin of the trend that just faded. v1 rejected it on the top-20; the v2 thesis is
that it belongs on the dispersed mid-cap cross-section.

---

## 1. Crypto-native rationale — WHY XS-mom on 21–40, and WHY now

The anchor's failure mode is specific and measured (EXPLORATION-001 characterization): per-year Sharpe
`{2021:+1.9, 2022:+2.5, 2023:+2.1, 2024:+0.7, 2025:+0.8, 2026:−0.1}`. The book is FULL (band=20
names/yr), walk-forward λ is honest, so this is **regime non-stationarity of the TIME-SERIES trend
signal**, not overfit and not thinness. Directional "is this coin up over 21/42/84/168 candles?"
stopped generalizing on mid-caps. That is exactly the failure XS-mom is structurally insulated from,
for four crypto-native mechanisms:

1. **Dispersion is the fuel, and the mid-cap band has it.** XS-mom monetizes *relative* return spread,
   not *aggregate* direction. The top-20 is BTC/ETH-dominated and beta-coupled — when BTC moves, the
   whole cohort moves together, so the cross-sectional spread an XS-rank can harvest is small and
   quickly arbitraged (v1's iter_002 rejection). The rank-21–40 cohort (INJ/UNI/AAVE/OP/TIA/SEI/WIF/
   ICP/HBAR/XMR-type names) is precisely where idiosyncratic, narrative-driven dispersion lives: at any
   8h close some mid-caps are pumping on a listing/airdrop/narrative while others bleed. **A
   dollar-neutral long-winners/short-losers book earns the spread regardless of whether the cohort's
   aggregate trend is up, down, or flat** — which is the whole point in a regime where aggregate trend
   pays nothing.

2. **Retail rotation persists at the 1–4 week scale.** Mid-cap crypto flows are retail-and-narrative
   driven: capital chases relative strength (the coin that just outperformed keeps attracting
   rotation-in) on a multi-day-to-few-week horizon before exhausting. This is the canonical
   cross-sectional momentum mechanism (Jegadeesh-Titman ported to crypto; documented in crypto by
   e.g. the 2018–2024 cross-sectional-momentum-in-crypto literature). It is a *relative-strength
   persistence* effect, mechanistically distinct from the *absolute-trend persistence* the anchor
   used — and relative-strength persistence does NOT require an alt-season tide. A short-the-laggard
   leg also directly harvests the mid-cap "bleed" that a long-only or net-long trend book gets hurt by.

3. **Funding / positioning asymmetry favors the dollar-neutral structure.** Mid-cap perps that have run
   hard carry crowded longs and elevated positive funding; laggards often carry crowded shorts /
   negative funding. The anchor's carry leg already tilts toward fading funding extremes, and the
   walk-forward λ leaned to carry (0.25) in 2024–26 yet stayed flat — carry alone didn't rescue it.
   XS-mom is **orthogonal** to that: it ranks on *price* relative strength, and the dollar-neutral
   construction means the funding paid on the crowded-long winners is partly offset by funding earned
   on the crowded-short laggards. The two legs net much of the cohort-wide funding drift, so XS-mom's
   PnL is cleaner relative-strength than the directional book's.

4. **Dollar-neutrality strips the beta the anchor was long.** The anchor is net-directional (trend sign
   can align the book long the whole cohort). In a flat/choppy mid-cap tape that net exposure earns
   noise. XS-mom is **mechanically dollar-neutral** (centered rank, Σw≈0 within the band), so it
   removes the cohort-beta term entirely and isolates the relative signal. **The Sharpe case** (our
   objective — not return) is precisely that removing the dead net-directional bet while keeping the
   relative bet should *raise risk-adjusted* return even if gross return falls.

**Why "now" and not in v1:** v1 tested XS-mom on the top-20 (too few, too efficient, too beta-coupled)
and it failed — the rejection was about the *universe*, not the *factor*. We are not re-running a dead
idea; we are running the factor in the cohort where its mechanism (dispersion + retail relative-strength
rotation) actually operates. The honest risk — which the guardrails below are built to catch — is that
XS-mom *also* turns out to be an alt-season-only effect (mechanism #2's rotation could itself be a
2021–23 phenomenon). The era-split gate is designed to falsify exactly that.

---

## 2. Exact construction

### 2.1 The XS-mom signal (single, pre-registered primary; lookback is the one structural knob)

Within the eligible band (the same `eligibility(coins, rank_lo, rank_hi, season)` mask the anchor
uses), at each candle:

```
mom[c,t]   = close[c,t] / close[c, t - L] - 1.0           # trailing return, lookback L candles
rk[c,t]    = mom.where(elig).rank(axis=1)                 # cross-sectional rank within the band, asc
n[t]       = elig.sum(axis=1)                             # number of names in the band at t
xs[c,t]    = (rk[c,t] - (n[t]+1)/2) / n[t]                # CENTERED, dollar-neutral in [-0.5, +0.5]
             , masked .where(elig)                        # winners > 0, losers < 0, Σ_c xs ≈ 0
```

This is **bit-identical to v1's `iter_002_top20.py` lines 85–89** construction (the reference factor
we are reviving), now computed on the 21–40 band. It is past-only by construction (`close` and `elig`
are past-only; no `.shift(-1)`). The signal is a per-candle centered rank, sign = winner(+)/loser(−),
magnitude ∝ distance from the cohort median.

**Lookback L — the ONE structural knob (robustness sweep, NOT a per-month fit, NOT OOS-tuned).**
- **Primary, pre-registered: `L = 84` candles (= 28 days at 8h).** This matches v1's xsec_mom lookback
  exactly and sits inside the anchor's own `HORIZONS=[21,42,84,168]`, so it is *not* a degree of
  freedom we invented to fit this cohort.
- **Robustness sweep (must all be reported, judged on IS + walk-forward only):**
  `L ∈ {42, 84, 126, 168}` (= 14, 28, 42, 56 days). The pre-registration is: L=84 is the deploy
  candidate; the sweep exists to prove the result is **not a knife-edge in L** — the MERGE decision in
  §4 requires the *neighbors* (L=42 and L=126) to agree in sign with L=84, not to be individually
  re-optimized. We do NOT pick the best L on OOS. If the sign of the IS lift is positive only at one
  isolated L and flips at its neighbors, the factor is a fit artifact and is killed.

> Rationale for not adding a short-term-reversal lookback here: short-term reversal is a *separate*
> pre-registered EXPLORATION on the v2 roadmap (skill §Roadmap item 3). This iteration changes ONE
> thing — XS-mom. Keep it clean.

### 2.2 STANDALONE vs BLENDED — run BOTH; deploy the BLEND, parity via γ

We test two configurations, in this order:

- **(A) STANDALONE XS-mom** — replace the directional signal entirely with `xs`, keep everything else
  (inverse-vol size, gross-norm, lag, band, eligexit, vol-target) identical. This is the cleanest read
  of "does relative strength carry information on this cohort, independent of the faded trend?" It is a
  diagnostic, not the deploy candidate.

- **(B) BLENDED trend+carry+XS-mom** — add `xs` as a THIRD term in the existing signal blend with its
  own weight **γ**, exactly analogous to how carry enters via λ. This is the **deploy candidate**: it
  preserves the anchor's surviving trend+carry structure and *adds* the relative bet, so a positive
  result compounds with the baseline rather than replacing a still-partially-working signal.

**The blend, parity-preserving (this is the non-negotiable spec for the engineer).** Today
`fixed_lambda_book` builds the pre-size numerator as:

```
raw = (((1 - lam) * trend + lam * carry) / rvol).where(elig)        # current anchor
```

The new blend nests the existing trend+carry combo and tilts a γ-fraction toward XS-mom:

```
tc       = (1 - lam) * trend + lam * carry                          # unchanged anchor combo
combined = (1 - xs_gamma) * tc + xs_gamma * xs                      # NEW: γ-tilt to XS-mom
raw      = (combined / rvol).where(elig)
```

**Parity contract (HARD — Critic will verify bit-for-bit):**
- `xs_gamma == 0.0` ⇒ `combined = (1-0)*tc + 0*xs = tc` **algebraically identical** to today's line.
  The engineer MUST guard so that at γ=0 the `xs` panel is never even multiplied in a way that could
  perturb NaN/dtype (e.g. `if xs_gamma == 0.0: combined = tc` early-return, OR ensure `xs` is `0.0`
  where the band is eligible and `tc` is finite so `0.0 * xs` contributes exactly `0.0`). The existing
  `parity_check.py` (v1-compat == iter_021 K=2, max|Δ| target <1e-9) and `tests/test_portfolio_v2.py`
  must stay green with **max|Δ| unchanged at ~1e-16**. Add a new unit test
  `test_xsmom_gamma_zero_parity`: `run_book(..., xs_gamma=0.0)` net == current `run_book(...)` net
  bit-for-bit (max|Δ| == 0.0, not just <1e-9).
- The XS-mom term must flow through the SAME downstream pipeline (inverse-vol `/rvol`, gross-norm, lag
  `.shift(1)`, band, eligexit, renorm, vol-target) and the SAME slippage cost — so the cost of XS-mom's
  higher turnover is charged honestly, not bolted on.
- γ enters BOTH the per-λ book (so walk-forward λ-selection sees the XS-augmented nets) AND the final
  banded net — identical treatment to how λ and slippage already enter both, per the engine docstring.

**γ — structural knob, robustness sweep (NOT OOS-tuned, NOT walk-forward-selected in this iteration).**
- Pre-registered sweep: **`γ ∈ {0.0, 0.15, 0.25, 0.40, 0.60, 1.0}`** where γ=0.0 is the parity anchor
  and γ=1.0 is effectively config (A) standalone-with-trend-residual. Mirror the carry grid's scale
  (`LAM_GRID=[0.0,0.1,0.25,0.4]`) so γ is a sibling, not a new magnitude regime.
- **In this EXPLORATION γ is FIXED across the sweep, not walk-forward-selected.** Reason: we are
  measuring whether the factor has signal, with a robustness sweep, before granting it the right to a
  walk-forward weight. Walk-forwarding γ (analogous to λ) is a *follow-up* iteration that only earns
  its place if a fixed γ clears the gates here. (Skill §4: a param earns per-month tuning ONLY if
  proven non-stationary; we have not proven that yet.)
- Deploy candidate to carry into CONFIRMATION = the single γ that maximizes the **IS + walk-forward
  metric** (OOS hidden), provided its neighbors agree in sign (robustness, not knife-edge).

### 2.3 The dispersion / min-names gate (critic-mandated guardrail, pre-registered)

XS-mom is meaningless when the band is thin or undispersed (ranking 3 names, or ranking names whose
returns are nearly identical, manufactures noise positions and pure turnover cost). Gate the **XS-mom
contribution** off (fall back to pure trend+carry, i.e. force the γ-term to 0 for that candle) when
EITHER condition holds, both computed **past-only** (`.shift(1)`, on the band's eligible members as of
the prior close):

```
GATE OFF the xs term at candle t  iff
   (n[t] < N_MIN)                                   # too few names to rank meaningfully
   OR (disp[t] < DISP_MIN)                          # cross-sectional return spread too compressed
where
   n[t]    = elig.sum(axis=1)                       # band size at t (already computed)
   disp[t] = cross-sectional std of mom[c,t] over the eligible band at t   (past-only L-return spread)
```

When gated off, `combined` reverts to `tc` for that candle (the book = pure anchor), so the gate can
NEVER make the book *worse than the anchor* on gated candles — it is fail-safe toward the baseline.

**Pre-registered thresholds (calibrated on IS dispersion distribution ONLY, frozen before OOS reveal):**
- **`N_MIN = 8`** names. The band targets 20 (rank 21–40) and EXPLORATION-001 confirms band=20 in
  2021–26; only the thin 2020 tail (band≈14.8, and near-empty early) and any future delisting-driven
  thinning would trip it. N_MIN=8 ⇒ at least 4 longs / 4 shorts, the minimum for a non-degenerate
  dollar-neutral cross-section. (Pre-registered; if the IS band-size histogram shows a natural floor
  elsewhere, the engineer reports it but N_MIN stays 8 unless re-registered with rationale.)
- **`DISP_MIN`**: pre-register as the **20th percentile of the IS-period cross-sectional `disp[t]`
  distribution** (computed once, IS-only, in the analysis script, and printed as a fixed number in the
  diary so it is frozen). Gating the bottom-quintile-dispersion candles removes the regime where ranking
  is noise. This is a distributional pre-registration, NOT a value tuned to maximize Sharpe — the
  engineer reports the resolved number and never sweeps it for performance.
- **Robustness check on the gate (not a tune):** report results at `N_MIN ∈ {6, 8, 10}` and
  `DISP_MIN ∈ {p10, p20, p30}` to show the gate's effect is monotone/stable, not a single magic cell.
- **Run WITH and WITHOUT the gate** (critic mandate) so its marginal effect is measured, not assumed.

---

## 3. Critic-mandated guardrails (from EXPLORATION-001) — how each is honored

1. **Dispersion / min-names gate** — §2.3, pre-registered `N_MIN=8`, `DISP_MIN=IS-p20`, run with AND
   without, fail-safe to the anchor on gated candles.
2. **Judge on the 2×/pessimistic-slip OOS.** XS-mom turns over MORE than directional trend (rank
   ordering churns every candle as relative returns jostle), so it is structurally more cost-exposed.
   The **deploy / MERGE decision is made on the slippage-inclusive net**, and the headline comparison
   is reported at default slip, 2× slip, 2× taker, AND the `diag_v2_001.slip_pessimistic` model
   (cap=25bp, B=40) — exactly the model under which the anchor reads OOS −0.12. **Turnover must be
   reported alongside Sharpe for every config** so the cost story is explicit. A config that wins at
   default slip but dies at pessimistic slip is NOT a merge candidate (the anchor already sits at ~0
   there; we must clear it under the same pessimistic lens).
3. **ERA-SPLIT — the central falsifier.** An edge that lives only in 2021–23 alt-season is the regime
   effect in a new costume. Report per-year Sharpe AND an explicit two-era split:
   **EARLY = 2021–2023** (alt-season) vs **LATE = 2024-01-01 → OOS_CUTOFF** (the faded IS tail), both
   IN-SAMPLE, plus the hidden-until-reveal OOS sub-windows (2025-03..12, 2026). The pre-registered
   requirement (§4): **XS-mom must lift the LATE (2024→cutoff) in-sample sub-window**, not just the
   EARLY era. If the entire lift is concentrated in 2021–23 and LATE is flat-or-worse, the factor is
   alt-season beta in disguise → KILL, regardless of full-sample IS.

---

## 4. Pre-registered MERGE / falsifier criteria (numeric, OOS hidden until ONE reveal)

**Comparison anchors:** v2-anchor OOS **+0.01** (default slip) / **−0.12** (pessimistic slip); the
v1-honest top-20 OOS **+1.49** is the aspirational reference but is a DIFFERENT universe — the binding
bar is **beat the rank-21–40 anchor on a risk-adjusted basis under honest cost.** Objective = SHARPE,
not return; a lower-return / higher-Sharpe (dollar-neutral, lower-DD) book is a WIN.

**Cost basis for all gate evaluations: slippage-inclusive net.** Default `default_slip_bps` is the
headline; the pessimistic model is the stress that the candidate must also survive.

### EXPLORATION-stage gates (OOS HIDDEN — judged on IS + walk-forward metric only)
A config is **PROMISING** (carried to CONFIRMATION) iff ALL hold:
- **G1 — IS lift:** blended deploy candidate IS Sharpe ≥ anchor IS (+1.53) **− 0.10** AND ideally
  ≥ +1.53 (XS-mom should not *cost* IS; a small give-back is tolerable only if LATE-era improves).
- **G2 — LATE-era IS lift (the anti-regime gate):** LATE (2024-01-01→cutoff) in-sample Sharpe of the
  blended candidate **> LATE Sharpe of the anchor** by ≥ +0.15. This is the load-bearing gate — it is
  what distinguishes "real relative-strength edge" from "more 2021–23 alt-season beta."
- **G3 — L-robustness:** sign of the IS+LATE lift is preserved at the lookback NEIGHBORS of the deploy
  L (L=42 and L=126 both agree in sign with L=84). No knife-edge.
- **G4 — γ-robustness:** the IS+LATE lift is positive across at least the contiguous γ-neighborhood of
  the deploy γ (not a single isolated γ cell).
- **G5 — cost survival:** the IS+LATE lift survives at 2× slip AND under `slip_pessimistic`
  (LATE-era Sharpe still > anchor LATE under pessimistic slip). Turnover increase vs anchor reported;
  if turnover more than ~2× the anchor's (anchor turn≈0.297) the cost story must still clear.
- **G6 — trade/structure sanity:** book stays dollar-neutral within the band when γ→1 (Σw≈0 check);
  avgPos and band names/yr unchanged from anchor (the gate must not silently thin the book).

### CONFIRMATION-stage gates (ONE OOS reveal; full gauntlet)
Promote XS-mom to the v2 baseline iff, on the slippage-inclusive net:
- **M1 — OOS beats the anchor:** blended deploy candidate **OOS Sharpe > +0.01 by a margin** —
  pre-register **OOS ≥ +0.30** (default slip) AND **OOS ≥ 0.00 under `slip_pessimistic`** (clear the
  −0.12 the anchor sits at). A merely-positive +0.05 is NOT enough given multiple-testing exposure.
- **M2 — OOS not a single-window mirage:** BOTH OOS sub-windows (2025-03..12 and 2026) are ≥ the
  anchor's in that window; the LATE/OOS improvement is not one lucky quarter.
- **M3 — Deflated:** N_eff-deflated OOS Sharpe (cluster/PCA the cross-config OOS return matrix over the
  γ×L sweep grid, per audit fix #3) stays > 0 after deflation for the program-wide trial count. Report
  N_eff, not the raw grid size.
- **M4 — risk-adjusted dominance, not return:** OOS maxDD ≤ anchor OOS DD (−30%) — the dollar-neutral
  structure should REDUCE drawdown; if DD worsens while Sharpe barely moves, NO-MERGE.
- **M5 — methodology intact:** parity (γ=0 bit-for-bit), leak (future-perturbation green), survivorship
  (PIT, candidate count grows), all unit tests green.

### KILL conditions (any ⇒ NO-MERGE this iteration, log the dead path)
- **K1 (regime costume):** the full-sample IS lift is entirely EARLY-era (2021–23) and **G2 fails**
  (LATE-era not improved) → XS-mom is alt-season beta; KILL even if full-IS looks great.
- **K2 (cost death):** lift exists at default slip but vanishes/negates under 2× or pessimistic slip
  → turnover eats the edge; KILL (and note the turnover figure).
- **K3 (knife-edge):** lift is a single isolated (γ, L) cell with neighbors flipping sign → fit
  artifact; KILL.
- **K4 (OOS reveal):** at CONFIRMATION, M1 or M2 fails → NO-MERGE; record the honest OOS number and the
  era-split, no retune, no second OOS peek.

**No OOS-tuning. No per-month fitting of γ/L/gate in this iteration.** Structural params get the
robustness sweeps above; OOS is consulted exactly once, at CONFIRMATION, and only to PASS/FAIL the
pre-registered M-gates.

---

## 5. What the engineer must implement + run

### 5.1 Engine change (`analysis/portfolio_v2/engine_v2.py`)
1. **`_signals`**: add `xs` to the returned dict. Compute per the §2.1 construction. It needs the
   eligibility mask and a lookback L → either pass `elig` + `L` into `_signals`, or (cleaner) compute
   `xs` inside `fixed_lambda_book` after `elig` is built (preferred — `elig` already lives there). The
   centered-rank `xs` must be `0.0`-filled where ineligible so it never injects NaN into `combined`.
2. **`fixed_lambda_book`**: add params `xs_gamma: float = 0.0`, `xs_lookback: int = 84`,
   `xs_nmin: int = 8`, `xs_disp_min: float | None = None`. Build `xs`; apply the §2.3 gate (force the
   xs-term to 0 on candles failing `n<N_MIN or disp<DISP_MIN`); form
   `combined = (1-xs_gamma)*tc + xs_gamma*xs` with the **hard γ=0 early-return parity guard**; feed
   `combined/rvol` into the existing `.where(elig)` line. NOTHING else in the pipeline changes.
3. **`run_book`**: thread the four new params through to every `fixed_lambda_book` call in the λ grid
   AND keep them consistent in the final banded net (they only affect signal construction inside the
   per-λ book, so threading through the books dict is sufficient — verify the canonical-book stitch is
   untouched).
4. **`DISP_MIN` resolution**: if `xs_disp_min is None`, the run script computes the IS-only p20 of
   `disp[t]` once and passes the frozen number in (never auto-recompute per config — freeze it so all
   configs share one pre-registered threshold).

### 5.2 Tests (keep the foundation green + add parity-at-γ=0)
- `tests/test_portfolio_v2.py`: add `test_xsmom_gamma_zero_parity` (γ=0 net == current net, max|Δ|==0).
- Add `test_xsmom_dollar_neutral` (with γ=1 and no gating, Σ of the pre-size `xs` over the band ≈ 0).
- Re-run `parity_check.py` — v1-compat must STILL hit max|Δ| ≤ 1e-9 vs iter_021 K=2 (unchanged).
- `uv run pytest tests/test_portfolio_v2.py -q` → all green (was 9/9).

### 5.3 Configs to run (new script `analysis/portfolio_v2/iter_v2_002_xsmom.py`)
All on `load_pool_pit()`, `rank_lo=20, rank_hi=40, season=168`, `slip_bps_fn=default_slip_bps` unless
noted. **Suppress OOS in the EXPLORATION diary** (print IS + LATE-era + walk-forward metric; keep OOS
computed but hidden behind a `--reveal` flag used only at CONFIRMATION).

1. **Parity guard:** `xs_gamma=0` → assert net == anchor net (printed max|Δ|).
2. **Standalone (A):** `xs_gamma=1.0`, L=84, no gate — diagnostic read of raw XS-mom signal.
3. **Blended γ-sweep (B):** `xs_gamma ∈ {0.15, 0.25, 0.40, 0.60}`, L=84, gate ON — the deploy search.
4. **L-robustness:** at the best γ, `L ∈ {42, 84, 126, 168}`.
5. **Gate on/off + gate-robustness:** best (γ,L) with gate OFF vs gate ON; then
   `N_MIN ∈ {6,8,10} × DISP_MIN ∈ {p10,p20,p30}` (report grid, don't tune).
6. **Cost stress:** best (γ,L,gate) at `slip_mult=2.0`, `cost_mult=2.0`, and `slip_bps_fn=slip_pessimistic`.

### 5.4 Diagnostics to report (extend `diag_v2_001` style)
For every config above, print:
- **IS Sharpe** and the **EARLY (2021–23) vs LATE (2024→cutoff) in-sample split** (the central table).
- **Per-year Sharpe** (reuse `per_year_sharpe`) — show the 2024/2025 IS years move, not just 2021–23.
- **OOS + OOS sub-windows** — COMPUTED but printed ONLY under `--reveal` (CONFIRMATION).
- **Turnover, tickets, avgPos, band names/yr** — the cost + structure story (vs anchor turn≈0.297).
- **Pessimistic-slip IS/LATE** for the deploy candidate (the −0.12-equivalent stress).
- **Dollar-neutrality check** (Σw within band per candle) and the **gate-fire rate** (% candles gated).
- **The frozen `DISP_MIN` value** (IS p20) printed once, for the record.
- **A single deploy-candidate row** (γ*, L*, gate) carried into CONFIRMATION, with IS + LATE only.

### 5.5 Run commands
```
export PATH="$HOME/.local/bin:$PATH"
uv run pytest tests/test_portfolio_v2.py -q                    # foundation + new parity tests green
uv run python analysis/portfolio_v2/parity_check.py            # v1-compat parity unchanged (<1e-9)
uv run python analysis/portfolio_v2/iter_v2_002_xsmom.py       # EXPLORATION (OOS hidden)
# CONFIRMATION (separate, later, ONE reveal):
uv run python analysis/portfolio_v2/iter_v2_002_xsmom.py --reveal
```

---

## 6. One-line thesis for the critic
Add a dollar-neutral cross-sectional-momentum tilt (γ on a centered within-band return-rank, L=84) to
the rank-21–40 trend+carry book, parity-preserving at γ=0; it should lift the **LATE-era / OOS**
risk-adjusted Sharpe the directional anchor lost — and if the entire lift sits in 2021–23 alt-season or
dies under pessimistic slip, the era-split and cost gates KILL it. Objective is Sharpe, not return.
