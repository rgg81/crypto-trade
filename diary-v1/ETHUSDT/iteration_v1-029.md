# Diary — iter-v1/029 (ETHUSDT) — CONFIRMATION (K=20) — NO-MERGE (meta-labeling K=5 OOS was a basin-lottery)

**Axis:** K=20 confirmation of the iter-028 meta-labeling (config bit-identical: iter-027 M1 trend-state
stack + M2 LGBMClassifier veto<0.45 on the 15-col positioning set). The arbiter of whether the iter-028
K=5 coherent both-positive (IS +0.27 / OOS +0.21, ratio +0.78) was REAL or seed-variance.

**Result (K=20, 20 bagging studies):** IS Sharpe **+0.2613** / OOS **+0.0369** (ratio 0.14).
68 IS / 27 OOS trades, WR 29.4%/29.6%, PF 1.247/1.019, OOS MaxDD 6.58%. (iter-028 K=5 was +0.27/+0.21.)

## Verdict: CONFIRMATION-NO-MERGE. The iter-028 OOS +0.21 was a K=5 BASIN-LOTTERY — collapsed to +0.04 at K=20.

Three findings, all decisive:

1. **The coherence was seed-variance, not edge.** OOS swung **+0.2097 (K=5) → +0.0369 (K=20)** and the
   ratio **+0.78 → +0.14** from the seed count alone. M2 is a LEARNED layer — which entries it vetoes
   varies per seed — so its K=5 OOS gain rode the seed-varying selection that K=20 averages out. The IS
   held (+0.27 → +0.26, M2 is stable IS) but the OOS coherence did not. **4th confirmation of the
   recurring campaign lesson** (iter-016/021/022/029): any mechanism whose OOS edge depends on the
   model's seed-varying timing/selection is a K=5 lottery that collapses at K=20; only DETERMINISTIC
   parts generalize.

2. **Pareto-dominated by the iter-027 baseline** (IS +0.6336 / OOS +0.0560). iter-029 is WORSE on IS
   (+0.26 ≪ +0.63 — the M2 veto cut trades 82→68 IS and roughly halved IS Sharpe) AND slightly worse on
   OOS (+0.037 < +0.056). It is strictly dominated on both regimes → fails the generalization-first
   merge gate (candidate must be Pareto-better-or-equal on every regime + strictly better on ≥1).
   **iter-027 REMAINS BASELINE_V1_ETHUSDT.** (iter-029 is technically both-positive in absolute terms
   — IS +0.26>0, OOS +0.037>0 — but both-positive vs nothing is not a merge; it must beat the incumbent.)

3. **De-concentration FAILED at K=20 — the opposite of the iter-028 thesis.** OOS top-1 trade = **107%**
   of net, top-2 = **186%** (27 trades, 8 winners) — MORE concentrated than the iter-028 K=5 read
   (top-1 78% / top-2 135%). The M2 veto filtered the book to even-higher single-trade dependence
   rather than broadening it. The de-concentration goal (the user's mandate) is not served by
   meta-labeling at the honest K=20 budget.

**Meta-labeling concluded NEGATIVE for ETH:** at K=20 it neither improves the iter-027 baseline NOR
de-concentrates the OOS. The iter-028 PROMISING tag was a K=5 artifact. (DSR −56/−59 are the known
small-N EXPLORATION-mode artifacts, n_eff=2 — informational only, not the basis for the verdict.)

## This REINFORCES the iter-030 deterministic-lever bet (already prepared + Critic-PASS)
The de-concentration mandate needs a DETERMINISTIC mechanism (the only kind that generalizes — see
finding #1, now 4×). That is exactly **iter-030 = AGREE_SCALE** (committed 198a42ec, Critic 6.0 PASS,
launch-ready): keep the iter-027 SMA-200 direction byte-identical, MULTIPLY the conviction quantity by
a deterministic past-only AGREEMENT fraction over panel P3 {ema_cross(50,200), donchian(55), tsmom(42)}.
The iter-030 brief §6 PRE-REGISTERED this fork: *"If iter-029 REGRESSES M2 (coherence was a K=5
artifact): AGREE_SCALE stands alone as the de-concentration mechanism on the proven iter-027 stack —
the safer, more fundamental fix (deterministic, can't overfit) and becomes the primary path."* It now is.

**Next:** LAUNCH iter-030 (compute freed): `run_baseline_v1.py --exploration --iteration 30 --symbols
ETHUSDT --n-trials 35 --slippage-bps 2 --no-engineering-report`. Evaluate vs pre-registered falsifiers
F1-F4/K1-K4 (brief §4): de-concentration (OOS top-2 below iter-027), IS Sharpe ≥ +0.58, recent-regime
edge ≥ +1.10, trade count ≥ 0.85×. If both-positive AND de-concentrated → K=20 confirm.

**Methodology working:** 4th K=5 false-positive caught at K=20. The K=20 arbiter + the
deterministic-vs-seed-varying distinction protected the baseline from a lottery merge again.

(Engine note: the run exited code 1 on a post-report `engineering_report.md`-not-found guard — a
mid-pipeline-orchestration artifact, NOT a computation failure. All reports wrote successfully;
metrics above are from the completed comparison.csv. iter-030 launches with `--no-engineering-report`.)
