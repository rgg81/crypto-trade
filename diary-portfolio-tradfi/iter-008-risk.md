# iter-008 RISK NOTE — VIX brake + drawdown stop (two leak-safe exposure overlays)

**Date:** 2026-07-01 · **Track:** portfolio-tradfi · **Role:** Risk Engineer
**Cadence:** EXPLORATION (IS-only, `< OOS_CUTOFF 2025-03-24`; **OOS HIDDEN** — no `--confirm`, no OOS number computed)
**Working best entering iter-008:** iter-006 crash-gate — net **+0.43** / bull **+0.60** / **bear −1.23** / chop **+0.56** (2/3) / maxDD **−25.5%** / turn 0.0962 / 2× cost +0.27.
**Source of truth (every number below):** `analysis/portfolio/tradfi/iter_008_vix_stop.py` (IS-only). Reproduce: `uv run python analysis/portfolio/tradfi/iter_008_vix_stop.py`.

---

## 1. Mechanism — two OUTER scalars on the vol-targeted net

iter-006's net is **already 63d portfolio vol-targeted** inside `banded_net`. The iter-006 note proved any de-lever applied **inside** the vol-target (Barroso constant-vol, raw-book drawdown brake) is **re-levered away**. Same trap kills a VIX scale on the raw weights (gross-norm re-normalizes it). So **both overlays multiply the final vol-targeted net** — the only place a de-lever survives. The book runs at target vol in calm tape, **below** target (de-risked) in stress. Each overlay is a per-bar scalar on the *whole* book, so sector-/dollar-neutrality and the unit-gross rebalance schedule (turnover) are **untouched** — only EXPOSURE moves.

```
net6     = iter-006 net (UNCHANGED — signal/gate/band/cost untouched)
net_vix  = net6 * s_vix                       # exogenous VIX brake
net_stop = dd_brake(net6)                      # endogenous drawdown stop
net_comb = dd_brake(net6 * s_vix)              # VIX outer de-lever, then stop on the deployed book
```

## 2. Pre-registered thresholds (theory-pinned / worst-quintile RULE; NOT max-net)

**VIX brake (continuous, exogenous):** `s_vix[t] = clip(VIX_BASE / VIX_close[t−1], VIX_FLOOR, 1)`
- **VIX_BASE = 20.0** — canonical calm/elevated VIX line (~ long-run median; IS median = 18.0). Brake **inert at VIX ≤ 20** (clipped to 1). A conventional fixed level, *pre-registered before reading any net* — NOT tuned to flip a window.
- **VIX_FLOOR = 0.50** — never cut below half gross (binds only at VIX ≥ 40, ~1.9% of IS days). Round, conservative cap.
- `.shift(1)` (yesterday's close) + past-only ffill onto the trading-day grid = strictly causal.
- VIX is **EXOGENOUS** (spiked ~82 in COVID, elevated through 2022): it de-risks our two IS bears *without being fit to them* — the forward-looking analog of the Barroso-Santa-Clara momentum-crash vol brake, de-levering on the high-vol days that are the worst momentum days (vol clustering).

**Drawdown stop (portfolio-level, endogenous):** metals iter-007 hysteresis.
- **D_TRIP = 15.1%** = 80th percentile of the iter-006 IS daily drawdown-depth distribution (the book sits deeper than this on its worst ~20% of IS days). A pre-registered **worst-quintile RULE**, NOT a max-net fit.
- **DD_FLOOR = 0.50** (floor > 0 → the de-levered equity keeps moving and can recover to re-arm; no self-lock).
- Re-arm at **−D_TRIP/2 = −7.6%** (hysteresis dead-band kills trip/re-arm chatter).
- Form choice: portfolio-level, **not** per-name. A per-name stop zeroing a blowing-up IPO (COIN/MSTR/RIVN) would break the per-sector dollar-neutrality the book is built on; a scalar de-lever preserves neutrality exactly and composes with VIX.

## 3. Simulated IS effect (overlays don't change the book → turnover identical 0.0962)

| build | net | bull | bear | chop | (n/3) | maxDD |
|---|---|---|---|---|---|---|
| **iter-006 (baseline)** | **+0.43** | **+0.60** | **−1.23** | **+0.56** | 2/3 | **−25.5%** |
| VIX brake ALONE | +0.41 | +0.52 | **−0.88** | +0.35 | 2/3 | −25.9% |
| DD stop ALONE | +0.34 | +0.44 | −1.07 | **+0.56** | 2/3 | **−20.6%** |
| **COMBINED (VIX+stop)** | +0.31 | +0.36 | **−0.48** | +0.35 | 2/3 | **−20.8%** |

Exposure (IS): VIX scalar mean 0.92 / min 0.50 / active 38% of days; DD scalar mean 0.80 / active 40%; combined mean 0.74 / min 0.25.

**BEAR specifically (the target).** Aggregate bear **−1.23 → −0.48 (Δ+0.76)** in the combined; VIX-alone **−0.88 (Δ+0.35)**.
- **2022 grind (the sustained momentum crash):** Sh −0.38/−3% → **+0.26/+1%** — fixed.
- **COVID V-crash:** dollar loss **−11% → −4%** (cut 60%). The sub-window *Sharpe* prints −3.65 → −7.89, but that is computed on only ~1.5 months (≈2 monthly points) and is unreliable — the meaningful number is the dollar/maxDD reduction. A trend-lagged book still loses into a 2-month V-crash; the brakes bound the magnitude.

**Tail (combined):** worst MONTH −13.15% → **−11.78%**, worst DAY −5.77% → **−5.58%**, maxDD −25.5% → **−20.8%**.

**Sensitivity (reported; pinned cell starred; we did NOT pick max-net).** Continuous VIX base×floor: gentler `base=25/fl=0.50` → net +0.45 but bear only −1.13; pinned `base=20/fl=0.50` → +0.41 / bear −0.88. There is a genuine **more-bear-fix ⇒ more-bull/chop-cost** trade across the whole grid. The **step variant is knife-edge** (thr=25 → bear −0.35, thr=30 → bear −1.24) — a cautionary example of exactly the IS-fitting the Critic blocked; the continuous brake (no threshold to flip) is the defensible construction.

## 4. Leak safety (HARD rule)

- VIX: past-only ffill onto the trading grid + `.shift(1)` → `s_vix[t]` reads only `VIX[<t]` (no bfill, no forward read). dd_brake is a forward sequential scan: `scale[t]` depends only on braked returns **before** t.
- **Future-bar leak self-check PASS** (corrupt panel + VIX + forward returns after a cutoff → COMBINED IS net before the cutoff bit-identical). 6 new tests green (2 identities, VIX past-only, DD past-only, DD floor/no-self-lock, **combined future-bar no-leak**). Suite **44 passed, 2 skipped**.
- IDENTITIES (pre-registered): VIX_BASE→∞ → s_vix≡1 → net_vix==net6; D_TRIP→∞ → stop never trips → net_stop==net6. Both PASS.
- **OOS HIDDEN**: every metric on the IS slice only; no `--confirm` path exists here.

## 5. Honest read & handoff (N=2-bear caveat)

The mechanisms work and are clean, but this is a **risk/return TRADE, not a Pareto win**: all three overlays buy bear-Sharpe + maxDD by **denting the strong regimes**. The COMBINED fixes bear (Δ+0.76) and maxDD (−4.7pp) but **dents bull (+0.60→+0.36) AND chop (+0.56→+0.35)** and lowers net (+0.43→+0.31). Under the strict task test (*fix bear WITHOUT killing bull/chop*) and the track's regime-Pareto merge gate (worse on **2 of 3** regimes), the COMBINED is a **borderline WASH → NO baseline-promote**. 2× cost: combined **+0.10** (vs iter-006 +0.27) — cost-fragile when stacked.

**N=2-bear caveat (load-bearing).** We have only **COVID + 2022** in-sample. The **bear-fix magnitude is SUGGESTIVE, not robustly estimated** — it rests on two episodes, one of which (COVID) the Sharpe can't even measure. The **bull/chop COST is the reliably-estimated number** (long, many-month windows). So we are confident the overlays *cost* bull/chop; we are only *hopeful* they fix bear out-of-sample.

**Recommendation to Quant Research (adopt/modify/reject is QR's call):**
1. **VIX brake ALONE is the cleanest single overlay** — best bear-fix/cost ratio (bear −1.23→−0.88 at net +0.41 ≈ unchanged, maxDD ~flat). Adopt it as exogenous COVID-class crash insurance *if* the catastrophic-bear tail is the binding survival risk; it is theory-pinned, leak-safe, deterministic (seed-stable at CONFIRMATION).
2. **DD stop ALONE is maxDD insurance** that *preserves chop* (−25.5%→−20.6%, chop +0.56 held) but does **not** fix bear-Sharpe (confirming the iter-006 prediction). Treat as an optional drawdown cap, not a bear fix.
3. **Do NOT stack both for a baseline-promote** — the combined over-de-risks (net +0.31, both strong regimes dented, cost-fragile at 2×). If QR wants the strongest bear/maxDD bound and accepts the bull/chop cost as a deliberate Sharpe-first drawdown trade, the combined is the lever; otherwise keep iter-006 and run VIX-alone as a deployable risk overlay.
