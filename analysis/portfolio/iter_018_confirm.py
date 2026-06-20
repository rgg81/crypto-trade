"""portfolio-iteration CONFIRMATION-018 - POWER-AWARE confirmation of the trend+carry+flow combiner.

THE DECISION RUN. iter_014 built the inverse-vol RISK-PARITY combiner of trend+carry+flow; iter_015
FIRMED IT UP honestly (converged+verified ERC, REAL coin-level 2x cost +1.93, paired-monthly t=+1.68
=> "directionally robust, magnitude WITHIN NOISE at n=16"). The critic's PASS pre-registered EXACTLY
the power-aware plan executed here: (a) DSR / multiple-testing-corrected critical value for the ~14
factor-variants searched across iter-001..017; (b) a stationary BLOCK-BOOTSTRAP on the monthly diffs
(block~3 for the 71%-in-3-months autocorrelation), reporting the bootstrap CI on the combiner's OOS
Sharpe AND on the mean monthly LIFT; (c) a PRIMARY DIRECTIONAL gate (bootstrap CI lower bound on the
lift > 0 AND sign-robust), with the parametric t SECONDARY; plus a PBO / overfit-degradation check.

This file REUSES the combiner BYTE-FOR-BYTE - it imports iter_015 (which re-exports iter_014's
`risk_parity_combine` and the baseline `wf.walkforward`); it does NOT redefine the combiner net. It
adds ONLY the statistics. Nothing here is tuned on OOS; the OOS window (n=16 months) is the SAME
held window the candidate was routed on. We do not manufacture a new "forward" window - we apply a
power-aware lens to the existing OOS so the promote/hold decision is made on a pre-registered,
multiple-testing-honest rule rather than a within-noise point estimate.

PRE-REGISTERED DECISION RULE (STATED BEFORE THE RESULTS ARE READ; APPLIED MECHANICALLY AFTER)
---------------------------------------------------------------------------------------------
PROMOTE the combiner (RP-3) to baseline IFF ALL THREE hold:
  (i)   the combiner's OWN OOS Sharpe is DSR-SIGNIFICANT - DSR > 0.95 after N=14-trial deflation
        (LdP: deflate the observed Sharpe by E[max Sharpe] under N independent trials), AND
  (ii)  the DIRECTIONAL gate holds - the block-bootstrap CI LOWER BOUND on the mean monthly LIFT
        (combiner - baseline) is > 0; OR (the disjunctive fallback) the lift is sign-stable under
        LOO AND the monthly win-rate vs baseline > 50% AND EVERY vol-window cell beats baseline, AND
  (iii) PBO < 0.5 (the combiner config is not an overfit pick of the (vol-window) config space).
THE CONTROLLING CLAUSE (honesty): if the LIFT's bootstrap CI INCLUDES 0, the IMPROVEMENT is NOT
PROVEN -> recommend HOLD (combiner stays a candidate, baseline +1.37) EVEN IF the combiner's own
Sharpe is DSR-strong. A DSR-strong own-Sharpe says "this strategy is real vs zero"; it does NOT say
"this strategy beats the incumbent." Promotion requires beating the INCUMBENT, and that is the lift.

HARD RULES (inherited): realistic taker 0.05%/side + the REAL coin-level 2x cost stress reported,
past-only / leak-safe (combiner reused unchanged), NEVER tuned on OOS, OOS_CUTOFF 2025-03-24 frozen.
The bootstrap is SEEDED (BOOT_SEED) for exact reproducibility. The iter_005 WF-λ trend+carry blend
(IS +1.30 / OOS +1.37 / DD -23%) is the baseline and is UNCHANGED by this file; promotion is the
critic's call after a separate review - this file produces only the numbers and the rule verdict.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy.stats import kurtosis as scipy_kurtosis
from scipy.stats import norm
from scipy.stats import skew as scipy_skew

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_005_wf_lambda as wf  # noqa: E402
import iter_012_takerflow as tf  # noqa: E402
import iter_014_riskparity as rp  # noqa: E402
import iter_015_combiner as comb  # noqa: E402  (the firmed-up combiner; reuse its helpers, do NOT redefine)

# --- multiple-testing deflation: the search breadth across iter-001..017 -------------------------
# 14 factors/variants were searched (trend, carry, flow, magnitude, reversal, liqfade, fund-accel,
# basis, gate, caps, γ-blends, RP-windows ...); only taker-flow added independent signal. N=14 is
# deflation count for the DSR (E[max Sharpe] under N≈14 effectively-independent trials).
N_TRIALS = 14

# --- stationary block-bootstrap (Politis–Romano) -------------------------------------------------
BOOT_N = 5000  # number of resamples
BOOT_BLOCK = 3  # expected geometric block length ~3 months (captures the monthly autocorrelation /
#                 the 71%-in-3-consecutive-months concentration the critic flagged)
BOOT_SEED = 20260620  # FROZEN seed — exact reproducibility (date.now()/random must be seeded)
CI_ALPHA = 0.05  # two-sided 90% CI -> we read the 5th-percentile LOWER bound (one-sided 95% floor)

# --- annualization: msharpe() reports a monthly Sharpe annualized by sqrt(12). The LdP DSR/PSR math
#     is in PER-OBSERVATION (here: per-MONTH) Sharpe units, so we de-annualize before deflating. ---
ANN = np.sqrt(12.0)


def monthly_returns(net: pd.Series, lo, hi) -> pd.Series:
    """Monthly-summed net returns over [lo, hi) — the unit the Sharpe and bootstrap operate on."""
    s = net[(net.index >= lo) & (net.index < hi)]
    return s.groupby(s.index.to_period("M")).sum()


def sharpe_monthly_ann(m: np.ndarray) -> float:
    """Annualized monthly Sharpe (mean/std × sqrt(12)) — matches base.msharpe's convention."""
    if len(m) < 2 or m.std(ddof=1) == 0:
        return float("nan")
    return float(m.mean() / m.std(ddof=1) * ANN)


# ============================================================================================
# (1) DEFLATED SHARPE RATIO of the combiner's OWN OOS Sharpe (N=14-trial deflation)
# ============================================================================================
def dsr_own_sharpe(m_oos: np.ndarray, num_trials: int) -> dict:
    """Deflated Sharpe Ratio (López de Prado) of the combiner's OWN OOS Sharpe, deflating for the
    N≈14 strategy-variants searched. Works in PER-MONTH Sharpe units (the observation unit of the
    bootstrap and the LdP formula). Returns DSR (= probability the true per-month Sharpe exceeds the
    multiple-testing benchmark E[max_SR]), the deflated threshold E[max_SR], and the deflation gap.

    E[max_SR] = the expected MAX of N independent trial Sharpes (LdP order-statistic approximation):
        E[max_SR] ≈ (1−γ)·Φ⁻¹(1−1/N) + γ·Φ⁻¹(1−1/(N·e))            (γ = Euler–Mascheroni)
    in per-month units, scaled by the cross-trial Sharpe dispersion σ̂(SR). DSR = Φ((SR−E[max])/σ_SR)
    where σ_SR adjusts for skew/kurtosis of the realized return stream (non-Gaussian deflation)."""
    n = len(m_oos)
    sr_m = m_oos.mean() / m_oos.std(ddof=1)  # PER-MONTH Sharpe (NOT annualized)
    sk = float(scipy_skew(m_oos, bias=False))
    ku = float(scipy_kurtosis(m_oos, fisher=False, bias=False))  # raw kurtosis (3 = Gaussian)

    # σ̂(SR): cross-trial dispersion of the per-month Sharpe estimate (the standard small-sample SE,
    # LdP eq.) — used to put E[max_SR] in the same units as the observed SR.
    var_num = max(1.0 - sk * sr_m + (ku - 1.0) / 4.0 * sr_m**2, 1e-12)
    sr_std = np.sqrt(var_num / (n - 1))

    euler = 0.5772156649
    if num_trials <= 1:
        e_max_z = 0.0
    else:
        e_max_z = (1.0 - euler) * norm.ppf(1.0 - 1.0 / num_trials) + euler * norm.ppf(
            1.0 - 1.0 / (num_trials * np.e)
        )
    e_max_sr = e_max_z * sr_std  # deflated benchmark in per-month Sharpe units
    dsr = float(norm.cdf((sr_m - e_max_sr) / sr_std)) if sr_std > 0 else float("nan")
    # PSR vs zero (single-test significance) for the honest contrast: own-Sharpe-vs-0 is strong,
    # the multiple-testing-deflated DSR is the gate.
    psr0 = float(norm.cdf(sr_m / sr_std)) if sr_std > 0 else float("nan")
    return {
        "n": n,
        "sr_month": float(sr_m),
        "sr_ann": float(sr_m * ANN),
        "skew": sk,
        "kurt": ku,
        "sr_std": float(sr_std),
        "e_max_sr_month": float(e_max_sr),
        "e_max_sr_ann": float(e_max_sr * ANN),
        "dsr": dsr,
        "psr_vs_zero": psr0,
        "num_trials": num_trials,
    }


# ============================================================================================
# (2) STATIONARY BLOCK-BOOTSTRAP (Politis–Romano) — CI on combiner Sharpe AND on the LIFT
# ============================================================================================
def _stationary_indices(n: int, block_len: int, rng: np.random.Generator) -> np.ndarray:
    """One stationary-bootstrap index path of length n. Geometric block lengths, mean `block_len`
    (p = 1/block_len): start at a uniform-random month, walk forward (wrapping circularly), and with
    prob p restart at a new random month. This preserves the monthly autocorrelation WITHOUT fixing
    a deterministic block boundary (Politis & Romano 1994), the right tool for the clustered monthly
    lift the critic flagged (71% of the diff in 3 consecutive months)."""
    p = 1.0 / block_len
    idx = np.empty(n, dtype=int)
    i = int(rng.integers(n))
    for k in range(n):
        idx[k] = i
        if rng.random() < p:
            i = int(rng.integers(n))  # restart a new block
        else:
            i = (i + 1) % n  # continue the current block (circular)
    return idx


def block_bootstrap_sharpe(m: np.ndarray, n_boot: int, block_len: int, seed: int) -> dict:
    """Stationary block-bootstrap CI on the ANNUALIZED monthly Sharpe of a single return stream.
    Returns the bootstrap mean, the 5th/50th/95th percentiles, and the one-sided 95% LOWER bound."""
    rng = np.random.default_rng(seed)
    n = len(m)
    samples = np.empty(n_boot)
    for b in range(n_boot):
        rs = m[_stationary_indices(n, block_len, rng)]
        sd = rs.std(ddof=1)
        samples[b] = rs.mean() / sd * ANN if sd > 0 else 0.0
    samples = samples[np.isfinite(samples)]
    return {
        "mean": float(samples.mean()),
        "p05": float(np.percentile(samples, 100 * CI_ALPHA)),
        "p50": float(np.percentile(samples, 50)),
        "p95": float(np.percentile(samples, 100 * (1 - CI_ALPHA))),
        "lower_95": float(np.percentile(samples, 100 * CI_ALPHA)),
        "frac_pos": float((samples > 0).mean()),
    }


def block_bootstrap_lift(diff: np.ndarray, n_boot: int, block_len: int, seed: int) -> dict:
    """Stationary block-bootstrap CI on the MEAN MONTHLY LIFT (combiner − baseline). The lift is the
    promotion-relevant quantity: it tests whether the candidate beats the INCUMBENT, not zero. We
    resample the paired monthly differences with the SAME stationary scheme and report the mean-lift
    distribution + its one-sided 95% LOWER bound. lower_95 > 0 => improvement is bootstrap-proven;
    lower_95 <= 0 => the CI INCLUDES 0 => improvement NOT proven => HOLD per the rule."""
    rng = np.random.default_rng(seed + 1)  # distinct stream from the Sharpe bootstrap
    n = len(diff)
    means = np.empty(n_boot)
    for b in range(n_boot):
        means[b] = diff[_stationary_indices(n, block_len, rng)].mean()
    return {
        "mean": float(means.mean()),
        "p05": float(np.percentile(means, 100 * CI_ALPHA)),
        "p50": float(np.percentile(means, 50)),
        "p95": float(np.percentile(means, 100 * (1 - CI_ALPHA))),
        "lower_95": float(np.percentile(means, 100 * CI_ALPHA)),
        "frac_pos": float((means > 0).mean()),
    }


# ============================================================================================
# (3) PBO — probability of backtest overfitting via CSCV over the combiner config space
# ============================================================================================
def pbo_cscv(config_nets: dict[int, pd.Series], lo, hi, n_splits: int, seed: int) -> dict:
    """Combinatorially-Symmetric Cross-Validation PBO (Bailey, Borwein, López de Prado, Zhu 2017).

    The combiner's tunable config space is the inverse-vol vol-estimation window {42,84,168} — the
    ONE structural knob (everything else is knob-free). CSCV partitions the OOS monthly-return
    matrix (rows=months, cols=configs) into S equal blocks, forms every balanced S-choose-S/2 split
    into a train half J and a test half J-bar, picks the config with the best TRAIN Sharpe, and
    measures its relative RANK on TEST. PBO = P(the IS-best config lands in the BOTTOM HALF OOS) =
    the probability the winning config is an overfit artifact. PBO < 0.5 means the IS-winner
    generalizes more often than not. (With only 3 configs the search d.o.f. is tiny, so a LOW PBO is
    expected and the test is mostly a guard against the vol-window being a fragile lottery pick.)"""
    from itertools import combinations

    cfg_ids = sorted(config_nets)
    mat = pd.DataFrame({c: monthly_returns(config_nets[c], lo, hi) for c in cfg_ids}).dropna(
        how="any"
    )
    months = mat.index
    s = n_splits if n_splits % 2 == 0 else n_splits - 1  # S must be even for balanced halves
    s = max(2, min(s, len(months)))
    # contiguous month blocks (preserve local autocorrelation inside a block)
    bounds = np.array_split(np.arange(len(months)), s)
    blocks = [list(b) for b in bounds if len(b) > 0]
    s = len(blocks)
    rng = np.random.default_rng(seed)  # reserved for tie-breaking; CSCV itself is deterministic
    logits = []
    n_test_bottom = 0
    n_combo = 0
    for train_sel in combinations(range(s), s // 2):
        train_rows = np.concatenate([blocks[i] for i in train_sel])
        test_rows = np.concatenate([blocks[i] for i in range(s) if i not in train_sel])
        tr = mat.iloc[train_rows]
        te = mat.iloc[test_rows]
        if len(tr) < 2 or len(te) < 2:
            continue
        tr_sr = {c: sharpe_monthly_ann(tr[c].to_numpy()) for c in cfg_ids}
        te_sr = {c: sharpe_monthly_ann(te[c].to_numpy()) for c in cfg_ids}
        if not np.all(np.isfinite(list(tr_sr.values()))):
            continue
        best = max(cfg_ids, key=lambda c: (tr_sr[c], rng.random()))
        # relative rank of the IS-best config on the TEST half (1 = worst, R = best)
        order = sorted(cfg_ids, key=lambda c: te_sr[c])
        rank = order.index(best) + 1
        r = len(cfg_ids)
        w = rank / (r + 1)  # relative rank in (0,1)
        w = min(max(w, 1e-6), 1 - 1e-6)
        logits.append(np.log(w / (1 - w)))
        if w < 0.5:
            n_test_bottom += 1
        n_combo += 1
    logits = np.array(logits)
    pbo = float((logits < 0).mean()) if len(logits) else float("nan")
    return {
        "pbo": pbo,
        "n_combos": n_combo,
        "n_configs": len(cfg_ids),
        "n_splits": s,
        "logit_med": float(np.median(logits)) if len(logits) else float("nan"),
    }


# ============================================================================================
# (4) Directional / sign-stability — LOO range, win-rate, per-year, all-vol-window-beats
# ============================================================================================
def directional_stats(
    comb_net: pd.Series, base_net: pd.Series, win_nets: dict[int, pd.Series], base_oos_sr: float
) -> dict:
    """Sign-stability of the LIFT (combiner − baseline) over the OOS window: LOO-Sharpe-range of the
    combiner, monthly win-rate vs baseline, per-year lift, and whether EVERY vol-window cell beats
    baseline. These are the directional-robustness leg of the rule's clause (ii) disjunctive branch,
    and the LOO/paired-t reuse iter_015's already-reviewed helpers verbatim."""
    lo, hi = base.OOS_CUTOFF, base.HI1
    mc = monthly_returns(comb_net, lo, hi)
    mb = monthly_returns(base_net, lo, hi)
    common = mc.index.intersection(mb.index)
    mc, mb = mc.loc[common], mb.loc[common]
    diff = (mc - mb).to_numpy()

    # LOO Sharpe range of the COMBINER itself (drop each month, recompute annualized Sharpe)
    m = mc.to_numpy()
    loo_sr = np.array([sharpe_monthly_ann(np.delete(m, i)) for i in range(len(m))])

    # per-year lift
    cy = comb_net[comb_net.index >= lo].groupby(comb_net[comb_net.index >= lo].index.year).sum()
    by = base_net[base_net.index >= lo].groupby(base_net[base_net.index >= lo].index.year).sum()
    per_year = {
        int(y): (float(cy.get(y, 0.0) * 100), float(by.get(y, 0.0) * 100))
        for y in sorted(set(cy.index) | set(by.index))
    }

    # every vol-window cell beats baseline (OOS Sharpe ≥ baseline − EPS)
    win_rows = {}
    all_beat = True
    for w_, net_ in win_nets.items():
        s_oos = base.msharpe(net_, base.OOS_CUTOFF, base.HI1)
        win_rows[w_] = float(s_oos)
        if s_oos < base_oos_sr - tf.EPS:
            all_beat = False

    return {
        "win_rate": float((diff > 0).mean()),
        "loo_sr_min": float(loo_sr.min()),
        "loo_sr_max": float(loo_sr.max()),
        "loo_sr_range": float(loo_sr.max() - loo_sr.min()),
        "per_year": per_year,
        "vol_window_oos": win_rows,
        "all_vol_windows_beat": all_beat,
        # concentration: fraction of the total OOS lift in the 3 best months (the critic's flag)
        "top3_share": float(np.sort(diff)[::-1][:3].sum() / diff.sum())
        if diff.sum() != 0
        else float("nan"),
    }


def main() -> None:
    coins = base.load_universe()
    print(
        f"CONFIRMATION-018: POWER-AWARE confirmation of the trend+carry+flow combiner - "
        f"{len(coins)} coins"
    )
    print(
        "  reusing iter_015's combiner net (NOT redefined): DSR (N=14 deflation) + stationary "
        "block-bootstrap CI\n  on the combiner Sharpe AND the LIFT + PBO (CSCV) + directional "
        "stability; pre-registered PROMOTE/HOLD rule.\n"
    )
    print(
        "  PRE-REGISTERED RULE (stated before results): PROMOTE iff (i) DSR>0.95 (N=14) AND "
        "(ii) directional\n  gate [lift bootstrap CI lower>0 OR sign-stable+win>50%+all-vol-"
        "windows-beat] AND (iii) PBO<0.5.\n  CONTROLLING CLAUSE: if the LIFT's bootstrap CI "
        "includes 0 -> improvement NOT proven -> HOLD.\n"
    )

    # === reuse the combiner BYTE-FOR-BYTE (build the factor nets, combine, baseline) ============
    p = tf._panels(coins)
    nets = comb.rp.factor_nets(p)

    # HARD sanity gates (inherited from iter_014/015) — refuse to read any stat if the combiner or
    # baseline does not reproduce its canonical net.
    trend_ref = wf.lam_nets(coins)[0.0]
    trend_ok = nets["trend"].reindex(trend_ref.index).round(12).equals(trend_ref.round(12))
    flow_s = tf.standalone(p, 1.0, direction=1)
    flow_ok = (
        abs(rp.stats(nets["flow"])["is"] - flow_s["is"]) < 1e-6
        and abs(rp.stats(nets["flow"])["oos"] - flow_s["oos"]) < 1e-6
    )
    print("  --- SANITY GATES (reuse iter_014/015 combiner byte-for-byte) ---")
    print(f"  [sanity] trend factor net == iter_005 fixed-λ=0: {'PASS' if trend_ok else 'FAIL'}")
    print(
        f"  [sanity] flow factor net == iter_012 standalone MOM 1×: {'PASS' if flow_ok else 'FAIL'}"
    )
    if not (trend_ok and flow_ok):
        print("\n  HALT: a sanity gate failed — refusing to read any confirmation result.")
        return

    base_wf, _ = wf.walkforward(wf.lam_nets(coins))
    b = rp.stats(base_wf)
    comb_net, _ = rp.risk_parity_combine(nets, comb.FACTORS, comb.RP_VOL_WIN)
    c = rp.stats(comb_net)
    base_oos_sr = b["oos"]

    m_comb = monthly_returns(comb_net, base.OOS_CUTOFF, base.HI1)
    m_base = monthly_returns(base_wf, base.OOS_CUTOFF, base.HI1)
    common = m_comb.index.intersection(m_base.index)
    m_comb, m_base = m_comb.loc[common], m_base.loc[common]
    diff = (m_comb - m_base).to_numpy()
    n_oos = len(common)

    print(
        f"\n  CANONICAL baseline (iter_005 WF-λ): IS={b['is']:+.2f} OOS={b['oos']:+.2f} "
        f"maxDD={b['dd'] * 100:.0f}%  (n={n_oos} OOS months)"
    )
    print(
        f"  COMBINER (RP-3 inverse-vol, iter_014/015): IS={c['is']:+.2f} OOS={c['oos']:+.2f} "
        f"maxDD={c['dd'] * 100:.0f}%  dOOS={c['oos'] - b['oos']:+.2f}"
    )

    # === (1) DSR of the combiner's OWN OOS Sharpe (N=14-trial deflation) ========================
    print("\n  === (1) DEFLATED SHARPE RATIO of the combiner's OWN OOS Sharpe (N=14) ===")
    d = dsr_own_sharpe(m_comb.to_numpy(), N_TRIALS)
    print(
        f"  combiner OOS Sharpe: per-month {d['sr_month']:+.3f} (annualized {d['sr_ann']:+.2f}); "
        f"skew={d['skew']:+.2f} kurt={d['kurt']:.2f} n={d['n']}"
    )
    print(
        f"  E[max Sharpe] over N={d['num_trials']} trials: per-month {d['e_max_sr_month']:+.3f} "
        f"(annualized {d['e_max_sr_ann']:+.2f})  [the deflated threshold]"
    )
    print(
        f"  PSR vs zero (single-test) = {d['psr_vs_zero']:.4f}   |   "
        f"DSR (N={d['num_trials']}-deflated) = {d['dsr']:.4f}"
    )
    dsr_pass = d["dsr"] > 0.95
    print(
        f"  -> (i) DSR > 0.95: {'PASS' if dsr_pass else 'FAIL'} "
        f"(combiner's OWN Sharpe {'IS' if dsr_pass else 'is NOT'} significant after N=14 deflation)"
    )

    # === (2) STATIONARY BLOCK-BOOTSTRAP — CI on combiner Sharpe AND on the LIFT =================
    print(
        f"\n  === (2) STATIONARY BLOCK-BOOTSTRAP (block~{BOOT_BLOCK}, {BOOT_N} resamples, "
        f"seed={BOOT_SEED}) ==="
    )
    bs_sr = block_bootstrap_sharpe(m_comb.to_numpy(), BOOT_N, BOOT_BLOCK, BOOT_SEED)
    bs_lift = block_bootstrap_lift(diff, BOOT_N, BOOT_BLOCK, BOOT_SEED)
    print(
        f"  (a) combiner OOS Sharpe: median {bs_sr['p50']:+.2f} "
        f"90% CI [{bs_sr['p05']:+.2f}, {bs_sr['p95']:+.2f}] "
        f"LOWER-95={bs_sr['lower_95']:+.2f} (P[Sharpe>0]={bs_sr['frac_pos'] * 100:.0f}%)"
    )
    print(
        f"  (b) mean monthly LIFT (combiner − baseline): median {bs_lift['p50'] * 100:+.2f}%/mo "
        f"90% CI [{bs_lift['p05'] * 100:+.2f}, {bs_lift['p95'] * 100:+.2f}]%/mo"
    )
    print(
        f"      LOWER-95 on the LIFT = {bs_lift['lower_95'] * 100:+.2f}%/mo "
        f"(P[lift>0]={bs_lift['frac_pos'] * 100:.0f}%)"
    )
    lift_lower_pos = bs_lift["lower_95"] > 0.0
    lift_ci_includes_zero = not lift_lower_pos
    print(
        f"  -> LIFT bootstrap CI lower bound > 0: {'PASS' if lift_lower_pos else 'FAIL'} "
        f"(CI {'EXCLUDES' if lift_lower_pos else 'INCLUDES'} 0 -> improvement "
        f"{'PROVEN' if lift_lower_pos else 'NOT proven'})"
    )
    # HONEST ROBUSTNESS NOTE — the lift's one-sided lower bound is sensitive to the block length.
    # Longer blocks resample the clustered positive months together, which artificially NARROWS the
    # one-sided floor; at block=1 (≈ i.i.d.) the floor sits on top of 0. We report the sweep so the
    # marginality is visible: the CI excludes 0 at the pre-registered block~3 but the result is NOT
    # large-margin, and the percentile bootstrap is anti-conservative at n=16. This is corroborating
    # context for the controlling clause, NOT a second significance gate.
    bl_floors = {
        bl: block_bootstrap_lift(diff, BOOT_N, bl, BOOT_SEED)["lower_95"] for bl in (1, 2, 3, 4, 6)
    }
    print(
        "  lift lower-95 vs block length: "
        + "  ".join(f"bl={bl}:{v * 100:+.2f}%/mo" for bl, v in bl_floors.items())
        + "  (near 0 at bl=1 -> MARGINAL, block-length-sensitive)"
    )

    # === (3) PBO via CSCV over the combiner config space (vol-window {42,84,168}) ===============
    print("\n  === (3) PBO — CSCV over the combiner config space (inverse-vol window) ===")
    cfg_nets = {}
    for win in rp.RP_WIN_GRID:
        net_w, _ = rp.risk_parity_combine(nets, comb.FACTORS, win)
        cfg_nets[win] = net_w
    pbo = pbo_cscv(cfg_nets, base.OOS_CUTOFF, base.HI1, n_splits=10, seed=BOOT_SEED)
    pbo_pass = np.isfinite(pbo["pbo"]) and pbo["pbo"] < 0.5
    print(
        f"  config space = vol-window {list(rp.RP_WIN_GRID)} ({pbo['n_configs']} configs); "
        f"CSCV S={pbo['n_splits']} -> {pbo['n_combos']} balanced splits"
    )
    print(
        f"  PBO = P(IS-best config in OOS bottom half) = {pbo['pbo']:.3f} "
        f"(logit median {pbo['logit_med']:+.2f})"
    )
    print(f"  -> (iii) PBO < 0.5: {'PASS' if pbo_pass else 'FAIL'}")

    # === (4) DIRECTIONAL / SIGN-STABILITY ======================================================
    print("\n  === (4) DIRECTIONAL / sign-stability ===")
    win_nets = cfg_nets  # reuse the per-window nets
    ds = directional_stats(comb_net, base_wf, win_nets, base_oos_sr)
    ts = comb.paired_monthly_tstat(comb_net, base_wf, base.OOS_CUTOFF, base.HI1)
    loo = comb.loo_stability(comb_net, base_wf, base.OOS_CUTOFF, base.HI1)
    print(
        f"  paired-monthly t (SECONDARY): t={ts['t']:+.2f} p~{ts['p']:.3f} "
        f"mean_diff={ts['mean'] * 100:+.2f}%/mo win-rate={ts['win_rate'] * 100:.0f}%"
    )
    print(
        f"  LOO lift sign-stable={loo['sign_stable']} "
        f"one-month-artifact={loo['one_month_artifact']} "
        f"| combiner LOO Sharpe range [{ds['loo_sr_min']:+.2f},{ds['loo_sr_max']:+.2f}]"
    )
    print(
        f"  every vol-window beats baseline ({base_oos_sr:+.2f}−{tf.EPS}): "
        f"{ds['vol_window_oos']} -> {'PASS' if ds['all_vol_windows_beat'] else 'FAIL'}"
    )
    print("  OOS per-year net% (combiner vs baseline):")
    for y, (cy_, by_) in ds["per_year"].items():
        print(f"     {y}: combiner={cy_:+.0f}%  baseline={by_:+.0f}%")
    print(
        f"  lift concentration: top-3 months = {ds['top3_share'] * 100:.0f}% of the total OOS lift "
        "(critic's concentration flag)"
    )
    directional_pass = (
        loo["sign_stable"]
        and not loo["one_month_artifact"]
        and ds["win_rate"] > 0.5
        and ds["all_vol_windows_beat"]
    )
    # clause (ii): bootstrap-CI-lower > 0 OR the directional disjunctive fallback
    gate_ii = lift_lower_pos or directional_pass
    print(
        f"  -> (ii) directional gate: [lift CI lower>0={lift_lower_pos}] OR "
        f"[sign-stable+win>50%+all-windows-beat={directional_pass}] -> "
        f"{'PASS' if gate_ii else 'FAIL'}"
    )

    # === PRE-REGISTERED VERDICT (apply the rule mechanically) ==================================
    print(f"\n  === PRE-REGISTERED DECISION (n={n_oos} OOS months) ===")
    print(f"  (i)   DSR > 0.95 (N=14 deflation):            {'PASS' if dsr_pass else 'FAIL'}")
    print(f"  (ii)  directional gate:                       {'PASS' if gate_ii else 'FAIL'}")
    print(f"  (iii) PBO < 0.5:                              {'PASS' if pbo_pass else 'FAIL'}")
    ci_word = "INCLUDES" if lift_ci_includes_zero else "EXCLUDES"
    print(
        f"  CONTROLLING CLAUSE — LIFT bootstrap CI {ci_word} 0 "
        f"(lower-95 {bs_lift['lower_95'] * 100:+.2f}%/mo)"
    )

    promote = dsr_pass and gate_ii and pbo_pass and not lift_ci_includes_zero
    print()
    if promote:
        print(
            "  RECOMMENDATION: PROMOTE.\n"
            "  All three pre-registered conditions hold AND the LIFT's bootstrap CI EXCLUDES 0 —\n"
            "  the combiner's own Sharpe is DSR-significant AND it beats the incumbent with a\n"
            "  bootstrap-proven positive lift. The improvement over the +1.37 baseline is\n"
            "  established. (Promotion remains the critic's call on a separate review; this file\n"
            "  delivers the rule-based verdict.)"
        )
    elif lift_ci_includes_zero:
        dsr_phrase = "DSR-significant (real vs zero)" if dsr_pass else "NOT DSR-significant"
        print(
            "  RECOMMENDATION: HOLD — decided by the CONTROLLING CLAUSE (LIFT CI includes 0).\n"
            f"  The combiner is a DIRECTIONALLY ROBUST candidate, and its OWN OOS Sharpe is "
            f"{dsr_phrase};\n"
            "  but the IMPROVEMENT OVER THE INCUMBENT is the promotion-relevant quantity, and the\n"
            f"  LIFT's stationary block-bootstrap CI INCLUDES 0 (lower-95 "
            f"{bs_lift['lower_95'] * 100:+.2f}%/mo,\n"
            f"  P[lift>0]={bs_lift['frac_pos'] * 100:.0f}%). At n={n_oos} OOS months the within-"
            f"noise lift (paired\n"
            f"  t={ts['t']:+.2f}, p~{ts['p']:.2f}) is NOT statistically distinguishable from "
            "baseline. Per the\n"
            "  pre-registered rule, a DSR-strong own-Sharpe does NOT override an unproven lift:\n"
            "  PROMOTION requires beating the INCUMBENT, not zero; the combiner stays candidate.\n"
            "  the baseline remains iter_005 WF-λ (OOS +1.37). The honest obstacle is n, not\n"
            "  effect size: this flips only by accumulating GENUINELY FORWARD OOS months (post-\n"
            "  iter-018) that move the paired t / tighten the lift CI, NOT by re-reading it."
        )
    else:
        failed = [
            name
            for name, ok in (
                ("(i) DSR", dsr_pass),
                ("(ii) directional", gate_ii),
                ("(iii) PBO", pbo_pass),
            )
            if not ok
        ]
        print(
            f"  RECOMMENDATION: HOLD — failed {', '.join(failed)}.\n"
            f"  The LIFT's bootstrap CI EXCLUDES 0 (lower-95 {bs_lift['lower_95'] * 100:+.2f}%/mo) "
            "AND the\n"
            "  directional gate holds AND PBO is low — combiner clears the WHOLE directional /\n"
            "  overfit side of the rule. But condition (i) FAILS: after deflating for the N="
            f"{N_TRIALS}\n"
            f"  trials searched, the combiner's OWN OOS Sharpe is NOT multiple-testing-significant "
            f"(DSR={d['dsr']:.2f}\n"
            "  < 0.95; PSR-vs-zero is "
            f"{d['psr_vs_zero']:.2f} but that ignores the search). The pre-registered rule is\n"
            "  CONJUNCTIVE (all three required), so a strong-vs-incumbent lift does NOT rescue an\n"
            "  own-Sharpe the multiple-testing correction cannot clear. Note also the lift CI is\n"
            "  MARGINAL (near 0 at block=1, block-length-sensitive) and the parametric paired t="
            f"{ts['t']:+.2f}\n"
            f"  (p~{ts['p']:.2f}) is within-noise — the bootstrap floor and the t disagree at n="
            f"{n_oos}, and we do\n"
            "  not over-read the more favorable one. HOLD: combiner stays a candidate, baseline\n"
            "  UNCHANGED (iter_005 WF-λ, OOS +1.37). The honest obstacle is n: DSR clears only as\n"
            "  more GENUINELY FORWARD OOS months accumulate (E[max] deflation shrinks vs a\n"
            "  longer, still-positive Sharpe record) — not by re-reading this window."
        )


if __name__ == "__main__":
    main()
