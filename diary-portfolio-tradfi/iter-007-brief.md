# iter-007 BRIEF — Proper portfolio optimization (MVO) vs the naive sector-demean

**Date:** 2026-07-01 · **Track:** portfolio-tradfi · **Cadence:** EXPLORATION (IS-only, `< OOS_CUTOFF 2025-03-24`; **OOS HIDDEN**)
**Working best entering iter-007:** iter-005 (`iter_005_multihorizon.py`) — multi-horizon within-sector momentum blend, naive sector-demean weighting, band δ=0.005, 15%/yr vol-target. IS net **+0.20** / gross **+0.40**, bull +0.38 / bear −0.90 / chop +0.26 (**2/3**), turnover 0.114/day, maxDD −31%.
**Directive (user, 2026-06-30):** escalate the toolkit — replace the naive demean with PROPER PORTFOLIO OPTIMIZATION, test WEEKLY rebalance, ground in market-neutral equity literature.
**Probe (single source of truth for every number):** `analysis/portfolio/tradfi/iter_007_probe.py` (cvxpy MVO + Ledoit-Wolf, IS-only, leak-safe; reproduce `uv run python analysis/portfolio/tradfi/iter_007_probe.py`). **Dep added:** `cvxpy==1.9.2` (`uv add cvxpy`).

---

## Part A — How market-neutral EQUITY books are actually built (research, cited)

**1. MVO with an alpha signal.** The practitioner objective is `max_w  α'w − λ·w'Σw` subject to neutrality + position constraints. But raw MVO is an *error-maximizer*: it over-weights names whose estimated return is too high or whose estimated covariance is too low, so small input errors produce wild weights (Michaud 1989, "The Markowitz Optimization Enigma: Is Optimized Optimal?", *FAJ*; Best & Grauer 1991, *RFS*). The canonical empirical warning: **naive 1/N (here, the demean) frequently beats sample-based MVO out of sample** because estimation error swamps the optimization gain — MVO needs an implausibly long estimation window to win at moderate N (DeMiguel, Garlappi, Uppal 2009, "Optimal Versus Naive Diversification", *RFS* 22(5)).

**2. Covariance at N~40, T~1700.** Sample Σ is the MSE-worst choice in an optimizer even when T≫N, because the optimizer attacks its smallest (noisiest) eigenvalues. **Ledoit-Wolf shrinkage** `Σ̂ = δ·F + (1−δ)·S` (Ledoit & Wolf 2003 *J.Emp.Fin.*; 2004 "Honey, I Shrunk the Sample Covariance Matrix", *JPM*) gives the analytic δ that minimizes MSE. Targets `F`: **identity / constant-variance** (sklearn default, most conservative), **constant-correlation** (often best empirically), **single-factor / market** (Sharpe index model). Practitioner default: "just use Ledoit-Wolf"; start with constant-variance (PyPortfolioOpt risk-models doc). Crucially, **δ→1 (full shrinkage to the diagonal/identity target) collapses MVO back to a signal-proportional book** — this is the hinge of the result below.

**3. Transaction-cost-aware optimization.** Add a turnover penalty `−γ·‖w−w_prev‖₁` (or trade only to the boundary of a *no-trade region*). With proportional costs the optimum is to **trade partially toward the "aim" portfolio**, not all the way (Gârleanu & Pedersen 2013, "Dynamic Trading with Predictable Returns and Transaction Costs", *JF*; Davis-Norman 1990). Turnover penalization is reported as *more effective than covariance shrinkage* for realized performance (DeMiguel et al. 2009, "A Generalized Approach… Constraining Portfolio Norms", *Mgmt.Sci.*). **iter-003's hysteresis band is exactly a no-trade region** — the L1 turnover penalty is its convex-objective analog.

**4. Neutrality + position limits as constraints.** Dollar-neutral `1'w=0`, beta-neutral `β'w=0`, sector-neutral `Σ_sector w=0` (implies dollar-neutral), per-name box `|wᵢ|≤cap`, gross budget `‖w‖₁≤1`. These belong as *optimizer constraints* (project the alpha onto the neutral subspace), which is the correct home for a "risk model" on a directional signal — NOT as a variance term that fights the bet (Grinold & Kahn, *Active Portfolio Management*; Barra/Rosenberg 1974 factor-risk-model lineage).

**5. Rebalance frequency for 12-1m momentum.** Cross-sectional momentum is conventionally **monthly**-rebalanced precisely to bound turnover; daily adds cost that is silently booked as return unless netted (Novy-Marx & Velikov 2016 "A Taxonomy of Anomalies and Their Trading Costs", *RFS*; 2023). The tradeoff is alpha-decay (favours frequent) vs cost (favours infrequent) — an empirical question per signal.

**6. Momentum crash control lives in the risk model as VOL-SCALING, not MVO.** The fix for momentum's left tail is constant-volatility / dynamic-volatility scaling (Barroso & Santa-Clara 2015 "Momentum has its moments", *JFE*; Daniel & Moskowitz 2016 "Momentum Crashes", *JFE*), or idiosyncratic/residual momentum (Blitz-Huij-Martens 2011). The practitioner stack = **Barra factor risk model (for neutralization + crash-scaling) + MVO + tcost** — but for a *pure directional momentum* alpha the variance-minimization role of Σ is the part that hurts.

**Takeaway worth adopting here at N~40:** keep Σ in the *constraints* (neutralization — already done via sector-demean) and in *crash control* (vol-target + a bear brake), and be skeptical that a variance-penalty MVO with a sample/shrunk Σ will beat the demean — DeMiguel et al. predict it won't at this N. The probe tests exactly that.

## Part B — Prototype IS numbers (probe, IS-only, leak-safe)

Identical alpha (iter-005 `mh_raw` blend), identical downstream (`net_from_raw`: gross-norm → `.shift(1)` lag → taker cost → 15% vol-target). Only the **alpha→weight map** changes. Σ = rolling 252d Ledoit-Wolf, past-only (window strictly `< t`). **Leak check PASS** (corrupting alpha after a cutoff leaves all earlier weights bit-identical). The optimizer is solved only on IS dates; OOS never computed.

| config (banded δ=0.005 unless noted) | net | gross | bull / bear / chop | (n/3) | turn/day | maxDD | Δ net vs naive |
|---|---|---|---|---|---|---|---|
| **iter-005 naive demean, DAILY** (ref) | **+0.20** | **+0.40** | +0.38 / −0.90 / +0.26 | 2/3 | 0.114 | −31% | — |
| naive demean, **WEEKLY** (hold 5d) | +0.12 | +0.22 | +0.23 / −1.13 / +0.49 | 2/3 | 0.061 | −33% | **−0.08** |
| naive demean, biweekly (hold 10d) | +0.03 | +0.11 | +0.06 / −1.02 / +0.72 | 2/3 | 0.045 | −32% | −0.17 |
| MVO λ=200, cap .15, dollar-N, DAILY (best *plain* MVO) | +0.05 | +0.31 | +0.27 / −0.75 / −0.41 | 1/3 | 0.193 | −45% | −0.15 |
| MVO λ=10, cap .15, **+beta-N**, WEEKLY (best MVO net) | **+0.07** | +0.17 | −0.05 / −0.33 / **+1.95** | 1/3 | 0.096 | −41% | **−0.13** |
| MVO λ=10, cap .15, +beta-N, DAILY | +0.06 | +0.31 | +0.30 / −1.60 / **+1.05** | 2/3 | 0.241 | −53% | −0.14 |
| MVO λ=0 (pure-alpha-at-caps, no Σ), DAILY | −0.02 | +0.17 | +0.22 / −1.31 / +0.26 | 2/3 | 0.216 | −56% | −0.22 |
| MVO λ=1e4 (≈min-variance tilt), DAILY | −0.13 | +0.15 | −0.05 / −0.85 / +0.18 | 1/3 | 0.133 | −45% | −0.33 |
| MVO +turnover-penalty γ=2e-2, DAILY | +0.00 | +0.03 | +0.16 / −0.78 / +0.14 | 2/3 | 0.027 | −42% | −0.20 |

Full λ∈{0,10,50,200,1e3,1e4} × cap∈{.05,.08,.15,.25} × {daily,weekly} × {dollar/beta/sector-N} sweep in the probe — **the single best of 21 optimizer configs is +0.07; none clears +0.20.**

## Part C — Does optimization beat the naive demean here? **NO** — and why (the iter-007 verdict)

**Decisive, structural reason (not a tuning artifact):** the best MVO **gross** Sharpe is **+0.31** (λ=200), *below* the naive gross **+0.40**. Gross is the no-cost ceiling — so no turnover penalty, band, or weekly hold can rescue the optimizer; **the covariance penalty is discarding momentum signal, not merely adding cost.** This is textbook error-maximization at N~40 on a 62%-Semi/Tech-correlated universe (DeMiguel-Garlappi-Uppal; Michaud), and it is monotone in the wrong direction: every step *away* from the diagonal target (λ↑ toward the sample/shrunk Σ) loses net.

**The naive demean IS the optimizer's own answer.** `max α'w − λ‖w‖² s.t. 1'w=0` solves to `w ∝ α − mean(α)` = the sector-demeaned alpha — i.e. **iter-005 ≡ MVO with Σ = identity = maximal Ledoit-Wolf shrinkage (δ→1).** The probe empirically locates the optimal shrinkage at **δ→1** on this universe: conviction-proportional sizing beats any reweighting toward the estimated covariance. Pushing to caps/corners (λ=0 quantile book, gross +0.17) is *worse still* — the smooth proportional book is the edge.

**Weekly also loses on net (+0.12 vs +0.20).** It halves turnover (0.061 vs 0.114) and cost drag, and *helps chop* (+0.49 vs +0.26), but the staleness costs bull-regime momentum freshness (+0.23 vs +0.38) — net falls. For this slow-but-not-that-slow blend, **daily is the better frequency.** (Monthly-momentum convention assumes a 12-1m-only signal; our blend includes a 3-1m sleeve that decays faster, so it wants fresher rebalancing.)

### Recommended iter-007 — implement verbatim
**REJECT the MVO + weekly escalation. KEEP iter-005 (naive sector-demean, DAILY, band δ=0.005, 15% vol-target) as the working best — UNCHANGED.** No production weight-construction change. Concretely for the QE:
1. **Do NOT** swap the weight map; iter-005's `mh_raw → gross_norm → banded_net(δ=0.005)` stays the book.
2. **Retain** `iter_007_probe.py` as committed evidence (cvxpy optimizer infra, dormant). If anyone re-opens MVO, the *only* config worth re-running is `Σ = 252d Ledoit-Wolf` with the shrinkage target forced to **identity (δ=1)** — which provably reproduces the naive book — and it should be revisited **only when the universe grows to N≳80–100**, where T/N shrinks enough that the off-diagonal covariance becomes informative (DeMiguel et al.'s break-even N).
3. The genuinely interesting orthogonal finding to hand forward (NOT for iter-007): **beta-neutral as a hard constraint transforms CHOP** (chop +0.26 → +1.05 daily / +1.95 weekly) — but wrecks bear (−1.60) and is net-negative overall, so it is a *future conditional-in-chop* candidate, not now.

### Pre-registered IS criteria (unchanged across the arc) + this iteration's verdict
- net ≥ **+0.30** = promotable; +0.50 = healthy. **Best optimizer +0.07 — FAILS.**
- all-weather = positive in ≥**2/3** regimes, no catastrophic regime. Best-net MVO is 1/3; bear is negative in **100%** of configs.
- net > **+1.0** = **assume-leak**. (Nothing is near it; leak check independently PASS.)
- **Pre-registered decisive falsifier (met):** if `best-MVO gross < naive gross (+0.40)`, the optimizer is rejected regardless of cost engineering — **+0.31 < +0.40 → REJECT.**
- **Verdict: NEGATIVE-FALSIFIED EXPLORATION.** The "escalate to covariance-aware MVO" hypothesis is falsified at N~40; iter-005 remains the working best.

### Pre-registered FAILURE MODE (honest, why it failed, what would change the call)
The optimizer failed for a *structural* reason, not a search-budget one: at N~40 on a high-correlation universe, the variance term and the per-name caps both fight a directional momentum bet whose edge lives in **smooth conviction sizing**, so the optimizer's no-cost ceiling (gross +0.31) sits below the demean's (+0.40). The verdict would FLIP only if a future run shows MVO **gross > +0.40** — most plausibly at much larger N, or with Σ used purely for *neutralization constraints* (not a variance penalty). **The binding regime is BEAR (negative everywhere), confirming EXPLORATION-005's plan that the next real lever is iter-006's momentum-crash bear brake — a risk-model crash-scaler — NOT portfolio optimization.**

### Concern
The probe is a clean falsification of the optimizer at current N, but it does NOT escalate net (the directive's hope). Real upside remains on the BEAR axis (crash control), not the weight-construction axis. Caveat on the optimizer mechanics: `net_from_raw` re-gross-normalizes each row, so per-name caps are enforced pre-normalization and become soft post-norm; this does not affect the verdict (the decisive comparison is gross-Sharpe shape, scale-invariant), but a production MVO would enforce gross=1 inside the solver.
