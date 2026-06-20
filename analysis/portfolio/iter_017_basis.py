"""portfolio-iteration EXPLORATION-017 — PERP-SPOT BASIS factor (leverage-demand premium).

ONE new STRUCTURAL change to the canonical iter_005 baseline (walk-forward-λ trend+carry, honest
IS +1.30 / OOS +1.37 / maxDD -23%). The book already trades the funding LEVEL (CARRY) and a
funding-DYNAMICS slope was rejected (iter_016: orthogonal but no edge). This iteration tests a
DIFFERENT PRICE SERIES, not a funding transform: the PERP-SPOT BASIS — perp_price/spot_price − 1.

CRYPTO-NATIVE RATIONALE (quant-researcher):
  The perpetual trades against a separate spot market with no expiry. When leveraged longs crowd
  the perp, their aggressive bidding pushes the perp ABOVE spot (positive basis) — the *realized*
  leverage premium / over-extension. When shorts dominate or longs capitulate the perp trades BELOW
  spot (negative basis). Funding is the *mechanism* that pulls the two back together (8h
  settlements), but the basis is the market's REALIZED price gap RIGHT NOW — a continuous,
  intra-settlement positioning gauge that funding (a discrete, smoothed, exchange-set rate) does not
  equal. The economic reject-trigger question: is the basis just carry/funding re-skinned? They are
  LINKED (high basis ⇄ funding pressure to push longs out) but NOT identical: funding is
  clamped/clipped by the exchange, settles on a cadence, and the carry signal is its sign over a
  9-candle MEAN; the basis is the raw continuous gap and can diverge from funding's sign on any
  given candle (basis spikes funding hasn't yet repriced; funding caps the basis overshoots). We
  MEASURE the collinearity and REJECT if corr-to-carry is high or the residual collapses.

  DIRECTION — tested BOTH ways, sign picked by MECHANISM + IS (NEVER OOS):
    (A) FADE-THE-LEVERAGE (contrarian): high positive basis == over-leveraged longs == over-
        extension → SHORT the high-basis / LONG the low-basis. sign = -basis_z. This is the economic
        prior (mean-reversion of the leverage premium; same direction as carry, which is exactly why
        the orthogonality gate is the whole ballgame).
    (B) MOMENTUM: high basis == leverage demand confirming an up-move → ride it LONG. sign =
        +basis_z. Builds the literal sign flip and prints BOTH; the IS-better sign is deployed.

SIGNAL CONSTRUCTION (per coin-candle t, ALL inputs known at close[t], PAST-ONLY):
  basis[t]    = perp_close[t] / spot_close[t] − 1.0               (completed candle, known at close)
  basis_sm[t] = basis.rolling(SMOOTH_WIN).mean()                   (de-noise; single prints = noise)
  basis_z[t,c]= cross-sectional z-score of basis_sm across the ELIGIBLE PIT top-20 at t (row-demean
                / row-std, axis=1 SAME-TIME only — no time leak). IDENTICAL transform + lag chain to
                iter_012's flow_z / iter_016's accel_z, so the factor is scale-comparable and sized
                by the z-score itself (no extra /rvol). The weight lag is applied later via
                `.shift(1)` (mirrors trend/carry/flow): a signal built from close[t] trades the
                open[t+1]→open[t+2] return. Held-leg funding accrual is booked `fund.shift(-1)`.

  BOTH a LEVEL form (basis_sm directly) and a DE-MEANED / DEVIATION form (basis_sm − its own
  trailing long mean, so a coin's *structural* basis offset — exchange/listing artifacts — is
  removed and only the deviation from its norm is traded) are built; LEVEL is headline, DEVIATION is
  a robustness cross-check (per-coin structural basis offsets could otherwise dominate the panel).

ALIGNMENT (the one new data hazard — pre-registered sanity check):
  Spot 8h klines are on a SEPARATE file/index (different start, occasional gaps) from the perp. We
  reindex each coin's spot close to the PERP ms index with `method="nearest", tolerance=4h` (half
  the 8h grid) — the same nearest-within-grid pattern iter_004 uses for funding. A coin contributes
  a basis only where it HAS spot within tolerance; missing → NaN → it drops out of that candle's
  cross-section (the z-score row-stats use only coins with a finite basis). A PER-COIN GUARD first
  drops wrong-asset spot files (full-history median |basis| > 2% — ticker reuse / 1000-prefix /
  wrong era; GLMR +94%, RAY −59%, RAD +52%). SANITY GATE on what remains: pooled |median| < 0.20%,
  p99 < 5%. A huge residual basis ⇒ a perp/spot misalignment bug and we HALT.

CONSTRUCTION (mirrors iter_012 / iter_016 EXACTLY; reuses tf._panels for the shared past-only inputs
so the PIT top-20 universe, trend, carry, flow, rvol, elig, ret_fwd, fund_next are BYTE-IDENTICAL to
the canonical book). The standalone basis net flows through the IDENTICAL gross-normalize → lag →
real-funding+taker-cost → per-candle vol-target machinery the other factors use.

NO-CHEATING: the DIRECTION is IS+mechanism-picked (NOT OOS); the smoothing window is robustness-
swept over a fixed grid, NEVER walk-forwarded, NEVER OOS-tuned; taker 0.05%/side both sides + a 2×
cost stress on the standalone (a gross-only / turnover-eaten edge is a REJECT — the gate that killed
funding-acceleration); OOS_CUTOFF=2025-03-24 fixed; carry/flow/trend nets and the baseline WF-λ are
reused byte-for-byte and UNCHANGED.

PRE-REGISTERED REJECT TRIGGERS (the brief's gate, fixed BEFORE seeing OOS):
  - collinear-with-carry: |corr(basis_z, carry)| >= 0.50 (signal) OR |corr(basis net, carry net)|
    >= 0.50 (P&L)  → REJECT as carry-redundant.
  - spanned-by-book: residual OOS Sharpe (basis net regressed on trend+carry+flow nets, IS-fit OLS)
    collapses (<= +0.30 or below raw-OOS − EPS)  → REJECT.
  - cost-fragile: not net-positive IS AND OOS at BOTH 1× AND 2× taker  → REJECT.
  - no-edge / window-fragile: picked-direction standalone not positive IS+OOS, or the sign is not
    stable across the smoothing-window grid  → REJECT.
"""

from __future__ import annotations

import glob
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis/portfolio")
import iter_002_top20 as base  # noqa: E402
import iter_012_takerflow as tf  # noqa: E402
import iter_014_riskparity as rp  # noqa: E402

# --- signal knobs (structural; robustness-checked, NEVER OOS-tuned) ---
SMOOTH_WIN = (
    9  # trailing basis de-noise window (~3d of 8h == iter_004 carry M_FUND; level-vs-level)
)
DEMEAN_WIN = 84  # per-coin structural-offset window for the DEVIATION form (~28d, == base.VOL_WIN)
SPOT_TOL_MS = 4 * 60 * 60 * 1000  # nearest-spot tolerance: half the 8h grid (same idea as iter_004)

# --- robustness grids ---
SMOOTH_WIN_GRID = [3, 9, 21]  # de-noise-window sweep (headline 9 is one cell, not a tuned pick)
EPS = 0.05  # materiality band (same as iter_008/011/012/016)

# --- per-coin alignment guard (drop SPOT files that are NOT the same asset as the perp) ---
# A real-asset perp/spot pair CANNOT durably diverge: funding arbitrages the basis back within days,
# so a coin's MEDIAN |basis| over its whole history is ~0 (a few bp). A large median offset means
# spot file is the WRONG asset (ticker reuse across delisting/relisting, a 1000-prefix mismatch, a
# different listing era) — e.g. GLMR median +94%, RAY −59%, RAD +52%. We DROP any coin whose median
# |basis| exceeds this structural-offset threshold (a contaminated file, NOT a real basis).
MAX_COIN_MEDIAN_ABS_BASIS = 0.02  # 2%: a same-asset perp/spot median basis is always far below this

# --- pooled alignment sanity thresholds (AFTER the per-coin guard; basis is a small premium) ---
# pooled |median basis| must be < 0.20% (a small leverage premium); pooled |basis| p99 < 5%
# (tolerant of real liquidation-spike tails, but not 10×+ misalignment garbage).
MAX_MEDIAN_ABS_BASIS = 0.002
MAX_P99_ABS_BASIS = 0.05


def load_spot_close(coins: dict) -> pd.DataFrame:
    """Read spot 8h closes for the SAME PIT universe and align each to the PERP ms index.

    The spot files (`data/spot/<SYM>/8h.csv`) are on a SEPARATE index from the perp (different
    start, occasional gaps). For each coin we read spot `close` keyed by `open_time` (ms), dedup,
    then reindex to the perp ms index with `method="nearest", tolerance=4h` (half the 8h grid) — the
    iter_004 funding-alignment pattern. A coin with NO spot file, or no spot within tolerance for a
    candle, gets NaN there and drops out of that candle's cross-section. PAST-ONLY: spot close[t] is
    a completed-candle quantity; nothing here looks forward.
    """
    perp_index = (
        pd.DataFrame({s: d["open"] for s, d in coins.items()}).sort_index().index
    )  # ms epoch index of the perp universe (same as base.build)
    by_sym = {p.split("/")[2]: p for p in glob.glob("data/spot/*USDT/8h.csv")}
    cols = {}
    for sym in coins:
        p = by_sym.get(sym)
        if p is None:
            continue  # no spot for this perp — it contributes no basis (handled as missing)
        k = pd.read_csv(p, usecols=["open_time", "close"])
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        sclose = k["close"].astype(float)
        cols[sym] = sclose.reindex(perp_index, method="nearest", tolerance=SPOT_TOL_MS)
    return pd.DataFrame(cols, index=perp_index)


def build_basis(coins: dict, spot_close: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Per-coin raw basis = perp_close / spot_close − 1.0, on the shared ms index, PAST-ONLY.

    Uses the perp CLOSE (the completed-candle perp price, the same column the trend/carry signals
    read) over the nearest-aligned spot CLOSE. Returns (basis_df, dropped_coins). NaN where the coin
    has no aligned spot (it then drops out of the cross-section).

    PER-COIN ALIGNMENT GUARD (a data-provenance filter, NOT a tradeable signal): a same-asset perp/
    spot pair has a MEDIAN |basis| of a few bp (funding arbitrages any durable gap away in days). A
    coin whose full-history median |basis| exceeds MAX_COIN_MEDIAN_ABS_BASIS (2%) has a WRONG spot
    file — ticker reuse across a delisting/relisting, a 1000-prefix mismatch, or a different listing
    era (GLMR median +94%, RAY −59%, RAD +52%). Such a coin is DROPPED (its basis column zeroed to
    NaN). This is leak-safe: a fixed data-provenance call about which spot FILE is the right asset
    (like the universe MIN_HISTORY length filter), not a return-conditioned or time-varying signal —
    the same coins are dropped whether evaluated on IS or OOS.
    """
    perp_close = pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float).sort_index()
    sp = spot_close.reindex(index=perp_close.index, columns=perp_close.columns)
    basis = perp_close / sp.replace(0.0, np.nan) - 1.0
    coin_med_abs = basis.abs().median(axis=0)  # full-history median |basis| per coin (provenance)
    dropped = sorted(coin_med_abs[coin_med_abs > MAX_COIN_MEDIAN_ABS_BASIS].dropna().index.tolist())
    if dropped:
        basis[dropped] = np.nan  # zero out the wrong-asset spot files
    return basis, dropped


def build_basis_z(
    basis: pd.DataFrame,
    elig: pd.DataFrame,
    smooth_win: int,
    direction: int = 1,
    demean: bool = False,
) -> pd.DataFrame:
    """Cross-sectional z-score of the trailing-smoothed basis, PAST-ONLY.

    basis_sm[t]  = basis.rolling(smooth_win).mean()                  (completed candle t, trailing)
    [LEVEL form]  use basis_sm directly.
    [DEVIATION]   basis_sm − basis_sm.rolling(DEMEAN_WIN).mean()      (remove the coin's OWN
                  structural basis offset — listing/exchange artifacts — trade only the deviation).
    basis_z[t,c] = (x − rowmean) / rowstd over the ELIGIBLE cross-section at t (axis=1 same-time).
    direction = +1 momentum (long high-basis), −1 fade-leverage (short high-basis; both printed).

    The weight lag is applied later via `.shift(1)`; nothing here uses future data (z-score rowstats
    are same-row cross-section, the smoothing and the per-coin demean are strictly trailing).
    """
    basis_sm = basis.rolling(smooth_win).mean()
    x = basis_sm - basis_sm.rolling(DEMEAN_WIN).mean() if demean else basis_sm
    sm = x.where(elig)  # restrict the cross-section to eligible coins for the row-stats
    row_mean = sm.mean(axis=1)
    row_std = sm.std(axis=1)
    z = sm.sub(row_mean, axis=0).div(row_std.replace(0, np.nan), axis=0)
    return (direction * z).where(elig)


def basis_diagnostics(basis: pd.DataFrame, elig: pd.DataFrame) -> dict:
    """Alignment sanity diagnostics over the ELIGIBLE cells: median / p99 of |basis|, basis mean,
    coin coverage. A SMALL basis (|median| < 0.05%, p99 < 2%) confirms perp≈spot (correct align);
    a huge basis flags a misalignment bug (wrong index, decimal scale, 1000-prefix mismatch)."""
    b = basis.where(elig)
    vals = b.to_numpy().ravel()
    vals = vals[np.isfinite(vals)]
    n_coins_with_spot = int(basis.notna().any(axis=0).sum())
    return {
        "n_cells": int(vals.size),
        "n_coins_with_spot": n_coins_with_spot,
        "mean": float(np.mean(vals)) if vals.size else float("nan"),
        "median_abs": float(np.median(np.abs(vals))) if vals.size else float("nan"),
        "p99_abs": float(np.quantile(np.abs(vals), 0.99)) if vals.size else float("nan"),
        "max_abs": float(np.max(np.abs(vals))) if vals.size else float("nan"),
    }


def _panels(coins: dict) -> dict:
    """Shared past-only inputs — reuse tf._panels (trend/carry/flow/rvol/elig/ret_fwd/fund_next on
    the BYTE-IDENTICAL PIT top-20 universe) and ADD the perp-spot basis signals (LEVEL + DEVIATION).
    Spot is loaded fresh from disk and aligned to the perp ms index (tf._panels already converted
    _opens.index to datetime64[ms]; `.astype("int64")` recovers the ORIGINAL ms epoch the spot
    loader needs — identical recovery to iter_016's funding re-load).
    """
    p = tf._panels(coins)
    opens = p["_opens"]
    spot_close = load_spot_close(
        coins
    )  # on the ORIGINAL ms epoch index (== base.build's perp index)
    basis, dropped = build_basis(coins, spot_close)
    # align onto the shared dt index tf._panels uses
    basis.index = pd.to_datetime(basis.index, unit="ms")
    basis = basis.reindex(index=opens.index, columns=opens.columns)
    elig = p["elig"]
    p["_basis"] = basis
    p["_dropped_coins"] = dropped
    p["basis_z"] = build_basis_z(basis, elig, SMOOTH_WIN, direction=1, demean=False)
    p["basis_z_dev"] = build_basis_z(basis, elig, SMOOTH_WIN, direction=1, demean=True)
    return p


def standalone(p: dict, cost_mult: float, direction: int = 1, key: str = "basis_z") -> dict:
    """Build the basis signal as a self-contained cross-sectional factor (z-score, gross-normalized,
    lagged, real funding + taker cost at cost_mult×, per-candle vol-targeted) — directly comparable
    to the baseline and the other factors. direction flips the sign (momentum vs fade-leverage).
    """
    z = p[key].fillna(0.0)
    sig = z if direction == 1 else -z
    raw = sig.where(p["elig"])
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    w = raw.div(gross, axis=0).fillna(0.0).shift(1)
    pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = cost_mult * base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    net = base.vol_target((pnl + fpnl - cost).dropna())
    gross_net = base.vol_target((pnl + fpnl).dropna())  # pre-cost (cost honesty diagnostic)
    s = rp.stats(net)
    s["turn"] = float((w - w.shift(1)).abs().sum(axis=1).mean())
    s["gross_is"] = base.msharpe(gross_net, base.LO0, base.OOS_CUTOFF)
    s["gross_oos"] = base.msharpe(gross_net, base.OOS_CUTOFF, base.HI1)
    return s


def standalone_net(p: dict, direction: int = 1, key: str = "basis_z") -> pd.Series:
    """The standalone basis NET return series (1× taker, real funding, NOT vol-targeted) — used by
    the residual-orthogonality diagnostic so it shares the other factors' raw-return space.
    """
    z = p[key].fillna(0.0)
    sig = z if direction == 1 else -z
    raw = sig.where(p["elig"])
    w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)
    pnl = (w * p["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * p["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = base.COST_SIDE * (w - w.shift(1)).abs().sum(axis=1)
    return (pnl + fpnl - cost).dropna()


def orthogonality(p: dict, other_key: str, basis_key: str = "basis_z") -> float:
    """Pooled cross-coin Pearson corr(basis_z, <other signal>) over IS ELIGIBLE cells. THE key
    number for `carry`: if |corr to carry| is high the basis is the funding LEVEL re-skinned
    (REDUNDANT, gate threshold |corr| < 0.50). `other_key` is a per-coin signal panel (trend/carry/
    flow_z/basis_z_dev); for the dense trend/carry panels it is masked to eligible cells.
    """
    fl = p[basis_key]
    ot = p[other_key].where(p["elig"])
    is_mask = fl.index < base.OOS_CUTOFF
    a = fl[is_mask].to_numpy().ravel()
    b = ot[is_mask].to_numpy().ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 100 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return float("nan")
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def net_correlations(p: dict, basis_net: pd.Series) -> dict:
    """Correlation of the basis standalone NET series to the trend / carry / flow factor NETS (over
    IS, common dates). The orthogonality the combiner cares about is at the NET level (does the
    factor's P&L stream co-move with the book's), complementing the per-cell signal corr above.
    """
    nets = rp.factor_nets(
        p
    )  # trend, carry, flow standalone vol-targeted nets (byte-identical book)
    out = {}
    bv = base.vol_target(basis_net)  # put basis on the same vol-target footing as the factor nets
    for n in ["trend", "carry", "flow"]:
        df = pd.DataFrame({"a": bv, "b": nets[n]}).dropna()
        df = df[df.index < base.OOS_CUTOFF]
        out[n] = float(df["a"].corr(df["b"])) if len(df) > 2 else float("nan")
    return out


def residual_orthogonality(p: dict, direction: int) -> dict:
    """Regress the standalone basis net on the trend, carry AND flow factor nets jointly (IS-fit
    OLS, applied to the whole series) and report the RESIDUAL OOS Sharpe. If the basis were spanned
    by the existing 3-factor book — especially by carry (the funding LEVEL it is economically linked
    to) — its net would be explained away and the residual would collapse. A residual that stays
    materially positive OOS proves the factor is INDEPENDENTLY additive, NOT carry/trend/flow stack.

    Betas fit on IS ONLY (no OOS peek); the same IS-fit betas applied to the OOS residual.
    """
    basis = standalone_net(p, direction=direction)
    nets = rp.factor_nets(p)
    df = pd.DataFrame(
        {"basis": basis, "trend": nets["trend"], "carry": nets["carry"], "flow": nets["flow"]}
    ).dropna()
    is_df = df[df.index < base.OOS_CUTOFF]
    y = is_df["basis"].to_numpy()
    x = is_df[["trend", "carry", "flow"]].to_numpy()
    x1 = np.column_stack([np.ones(len(x)), x])  # intercept + 3 factor nets
    beta, *_ = np.linalg.lstsq(x1, y, rcond=None)  # IS-fit OLS
    xall = df[["trend", "carry", "flow"]].to_numpy()
    pred = beta[0] + xall @ beta[1:]
    resid = pd.Series(df["basis"].to_numpy() - pred, index=df.index)
    # carry-only beta (the single most important redundancy check)
    yc, cc = is_df["basis"], is_df["carry"]
    var_c = float((cc**2).mean() - cc.mean() ** 2)
    cov_c = float((yc * cc).mean() - yc.mean() * cc.mean())
    beta_carry_only = cov_c / var_c if var_c > 0 else 0.0
    return {
        "beta_trend": float(beta[1]),
        "beta_carry": float(beta[2]),
        "beta_flow": float(beta[3]),
        "beta_carry_only": beta_carry_only,
        "raw_is": base.msharpe(df["basis"], base.LO0, base.OOS_CUTOFF),
        "raw_oos": base.msharpe(df["basis"], base.OOS_CUTOFF, base.HI1),
        "resid_is": base.msharpe(resid, base.LO0, base.OOS_CUTOFF),
        "resid_oos": base.msharpe(resid, base.OOS_CUTOFF, base.HI1),
    }


def coverage(p: dict) -> dict:
    """Coverage diagnostic for the basis factor: fraction of eligible cells carrying a finite
    basis_z (after the SMOOTH_WIN warmup AND only where the coin has aligned spot), IS vs OOS, +
    median active coins/candle. UNLIKE the dense funding/flow factors this one is naturally SPARSER
    (a coin drops out where it has no spot) — quantifies how much of the top-20 carries a basis.
    """
    finite = p["basis_z"].notna() & p["elig"]
    elig = p["elig"]
    is_m = elig.index < base.OOS_CUTOFF
    oos_m = elig.index >= base.OOS_CUTOFF
    is_cov = finite[is_m].sum().sum() / max(int(elig[is_m].sum().sum()), 1)
    oos_cov = finite[oos_m].sum().sum() / max(int(elig[oos_m].sum().sum()), 1)
    active = finite.sum(axis=1)
    med_active = float(active[active > 0].median()) if (active > 0).any() else 0.0
    return {"is_cov": is_cov, "oos_cov": oos_cov, "med_active": med_active}


def window_sweep(p: dict, direction: int) -> list:
    """De-noise-window robustness: rebuild basis_z per SMOOTH_WIN and report standalone IS/OOS +
    corr-to-carry. If only one cell has an edge and the others are flat/negative or the sign flips,
    the headline is a tuned cell → downgrade. Reuses the fixed elig / basis panels (only the window
    changes).
    """
    rows = []
    for win in SMOOTH_WIN_GRID:
        bz = build_basis_z(p["_basis"], p["elig"], win, direction=direction, demean=False)
        pv = {**p, "basis_z": bz}
        corr_ca = orthogonality(pv, "carry")
        sa = standalone(pv, 1.0, direction=direction)
        rows.append({"win": win, "corr_carry": corr_ca, **sa})
    return rows


def main() -> None:
    coins = base.load_universe()
    print(f"EXPLORATION-017: PERP-SPOT BASIS factor (leverage-demand premium) — {len(coins)} coins")
    print(
        f"  signal: basis_z = xsec z-score of (perp/spot − 1).rolling({SMOOTH_WIN}).mean(); "
        f"tested BOTH dirs (fade-leverage vs momentum)\n"
    )

    p = _panels(coins)

    # --- HARD SANITY: perp ≈ spot (the basis is a SMALL leverage premium). A huge basis ⇒ a perp/
    # spot alignment bug (wrong index, decimal scale, 1000-prefix mismatch). If the median or p99
    # |basis| is large, HALT — every basis number would be on a mis-aligned price series.
    diag = basis_diagnostics(p["_basis"], p["elig"])
    align_ok = (
        np.isfinite(diag["median_abs"])
        and diag["median_abs"] < MAX_MEDIAN_ABS_BASIS
        and diag["p99_abs"] < MAX_P99_ABS_BASIS
    )
    dropped = p["_dropped_coins"]
    print("  --- ALIGNMENT SANITY (perp ≈ spot; basis is a small premium) ---")
    print(
        f"  per-coin guard: DROPPED {len(dropped)} wrong-asset spot files "
        f"(median|basis|>{MAX_COIN_MEDIAN_ABS_BASIS * 100:.0f}%): {dropped}"
    )
    print(
        f"  valid spot={diag['n_coins_with_spot']}/{len(coins)}  cells={diag['n_cells']}  "
        f"mean={diag['mean'] * 100:+.4f}%  |median|={diag['median_abs'] * 100:.4f}%  "
        f"p99|·|={diag['p99_abs'] * 100:.3f}%  max|·|={diag['max_abs'] * 100:.2f}%"
    )
    align_tag = (
        "PASS (basis small — perp≈spot)"
        if align_ok
        else "FAIL (basis too large — likely a misalignment bug)"
    )
    print(f"  -> alignment {align_tag}")
    if not align_ok:
        print("\n  HALT: basis too large — refusing to read any basis result (fix the alignment).")
        return

    # --- coverage (sparser than funding/flow: a coin drops out where it has no aligned spot) ---
    cv = coverage(p)
    print(
        f"\n  COVERAGE: IS finite-basis_z fraction of eligible={cv['is_cov']:.2f}  "
        f"OOS={cv['oos_cov']:.2f}  median active coins/candle={cv['med_active']:.0f}\n"
    )

    # --- mechanism / orthogonality: is the basis just the funding LEVEL (carry) re-skinned? ---
    corr_ca = orthogonality(p, "carry")
    corr_tr = orthogonality(p, "trend")
    corr_fl = orthogonality(p, "flow_z")
    corr_dev = orthogonality(p, "basis_z_dev")  # LEVEL vs DEVIATION form agreement
    carry_ok = np.isfinite(corr_ca) and abs(corr_ca) < 0.50
    print("  --- MECHANISM / ORTHOGONALITY (IS signal-level, eligible cells) ---")
    carry_sig_tag = (
        "PASS (|corr|<0.50, distinct from LEVEL)" if carry_ok else "FAIL (>=0.50, carry re-skin)"
    )
    print(f"  corr(basis_z, CARRY) = {corr_ca:+.3f}  -> {carry_sig_tag}")
    print(f"  corr(basis_z, trend) = {corr_tr:+.3f}   corr(basis_z, flow) = {corr_fl:+.3f}")
    print(f"  corr(basis_z LEVEL, basis_z DEVIATION form) = {corr_dev:+.3f}  (form agreement)\n")

    # --- STANDALONE both directions + cost honesty (1× and 2× taker) ---
    print("  --- STANDALONE basis_z cross-sectional factor (BOTH directions, cost honesty) ---")
    print(f"  {'':24}{'IS':>7}{'OOS':>7}{'maxDD':>7}{'netTot':>8}{'turn':>7}")
    sa_mom1 = standalone(p, 1.0, direction=1)
    sa_mom2 = standalone(p, 2.0, direction=1)
    sa_fade1 = standalone(p, 1.0, direction=-1)
    sa_fade2 = standalone(p, 2.0, direction=-1)
    print(
        f"  {'MOMENTUM(+basis) 1x':24}{sa_mom1['is']:>+7.2f}{sa_mom1['oos']:>+7.2f}"
        f"{sa_mom1['dd'] * 100:>6.0f}%{sa_mom1['tot']:>+7.0f}%{sa_mom1['turn']:>7.3f}"
    )
    print(
        f"  {'MOMENTUM(+basis) 2x':24}{sa_mom2['is']:>+7.2f}{sa_mom2['oos']:>+7.2f}"
        f"{sa_mom2['dd'] * 100:>6.0f}%{sa_mom2['tot']:>+7.0f}%{sa_mom2['turn']:>7.3f}"
    )
    print(
        f"  {'FADE-LEVERAGE(-basis) 1x':24}{sa_fade1['is']:>+7.2f}{sa_fade1['oos']:>+7.2f}"
        f"{sa_fade1['dd'] * 100:>6.0f}%{sa_fade1['tot']:>+7.0f}%{sa_fade1['turn']:>7.3f}"
    )
    print(
        f"  {'FADE-LEVERAGE(-basis) 2x':24}{sa_fade2['is']:>+7.2f}{sa_fade2['oos']:>+7.2f}"
        f"{sa_fade2['dd'] * 100:>6.0f}%{sa_fade2['tot']:>+7.0f}%{sa_fade2['turn']:>7.3f}"
    )
    # DEVIATION-form cross-check (headline direction picked just below)
    mom_dir = sa_mom1["is"] >= sa_fade1["is"]  # direction the data picks (IS, NOT OOS)
    direction = 1 if mom_dir else -1
    pv_dev = {**p, "basis_z": p["basis_z_dev"]}
    sa_dev = standalone(pv_dev, 1.0, direction=direction, key="basis_z")
    print(
        f"  {'DEVIATION-form 1x(picked)':24}{sa_dev['is']:>+7.2f}{sa_dev['oos']:>+7.2f}"
        f"{sa_dev['dd'] * 100:>6.0f}%{sa_dev['tot']:>+7.0f}%{sa_dev['turn']:>7.3f}"
    )
    picked = sa_mom1 if mom_dir else sa_fade1
    print(f"     picked net%/yr={picked['yr']}")
    dir_label = (
        "MOMENTUM (+basis, long high-basis)"
        if mom_dir
        else "FADE-LEVERAGE (−basis, short high-basis)"
    )
    print(f"     direction picked by data (IS): {dir_label}\n")

    # --- NET-level correlation of the picked direction to trend / carry / flow NETS ---
    basis_net = standalone_net(p, direction=direction)
    ncorr = net_correlations(p, basis_net)
    print("  --- NET-RETURN correlation of basis factor to the book's factor NETS (IS) ---")
    print(
        f"  corr(basis net, trend net)={ncorr['trend']:+.2f}  "
        f"corr(basis net, CARRY net)={ncorr['carry']:+.2f}  "
        f"corr(basis net, flow net)={ncorr['flow']:+.2f}"
    )
    net_carry_ok = np.isfinite(ncorr["carry"]) and abs(ncorr["carry"]) < 0.50
    net_carry_tag = (
        "< 0.50 (P&L stream distinct from the carry leg)"
        if net_carry_ok
        else ">= 0.50 (P&L co-moves with carry — REDUNDANT)"
    )
    print(f"  -> NET corr to CARRY {net_carry_tag}\n")

    # --- residual orthogonality vs the existing 3 factors (carry is the redundancy risk) ---
    ro = residual_orthogonality(p, direction)
    resid_ok = ro["resid_oos"] > 0.30 and ro["resid_oos"] >= ro["raw_oos"] - EPS
    resid_tag = (
        "independently additive (NOT spanned by trend/carry/flow)"
        if resid_ok
        else "spanned by the existing book (redundant)"
    )
    print("  --- RESIDUAL ORTHOGONALITY (basis net regressed on trend+carry+flow nets; IS OLS) ---")
    print(
        f"  betas: trend={ro['beta_trend']:+.2f} carry={ro['beta_carry']:+.2f} "
        f"flow={ro['beta_flow']:+.2f}  (carry-only beta={ro['beta_carry_only']:+.2f})"
    )
    print(
        f"  raw basis IS/OOS={ro['raw_is']:+.2f}/{ro['raw_oos']:+.2f}  "
        f"-> RESIDUAL IS/OOS={ro['resid_is']:+.2f}/{ro['resid_oos']:+.2f}"
    )
    print(f"     {resid_tag}\n")

    # --- de-noise-window robustness (prove the headline 9 is not a tuned cell) ---
    print("  --- DE-NOISE-WINDOW ROBUSTNESS (picked direction; standalone + corr-to-carry) ---")
    print(f"  {'win':>4} {'corrCarry':>9} {'sa_IS':>7} {'sa_OOS':>7} {'maxDD':>7} {'turn':>7}")
    sweep = window_sweep(p, direction)
    for r in sweep:
        print(
            f"  {r['win']:>4d} {r['corr_carry']:>+9.3f} {r['is']:>+7.2f} {r['oos']:>+7.2f} "
            f"{r['dd'] * 100:>6.0f}% {r['turn']:>7.3f}"
        )
    sweep_pos = all(r["is"] > 0 and r["oos"] > 0 for r in sweep)
    sweep_carry_ok = all(abs(r["corr_carry"]) < 0.50 for r in sweep if np.isfinite(r["corr_carry"]))
    print()

    # --- baseline anchor for context (UNCHANGED) ---
    base_wf, _ = tf.wf.walkforward(tf.wf.lam_nets(coins))
    b = rp.stats(base_wf)
    oos_net = base_wf[base_wf.index >= base.OOS_CUTOFF]
    n_oos_mo = oos_net.groupby(oos_net.index.to_period("M")).sum().shape[0]
    print(
        f"  CANONICAL baseline (iter_005 WF-λ, UNCHANGED): IS={b['is']:+.2f} OOS={b['oos']:+.2f} "
        f"maxDD={b['dd'] * 100:.0f}%  (n={n_oos_mo} OOS months)\n"
    )

    # --- carry standalone (the factor basis must be distinct FROM), for the comparison table ---
    carry_s = rp.stats(rp.factor_nets(p)["carry"])
    print(
        f"  CARRY standalone (the funding-LEVEL factor in the book): IS={carry_s['is']:+.2f} "
        f"OOS={carry_s['oos']:+.2f} maxDD={carry_s['dd'] * 100:.0f}%  (basis must be DISTINCT)\n"
    )

    # --- PRE-REGISTERED FALSIFIER VERDICT ---
    cost_ok = (
        picked["is"] > 0
        and picked["oos"] > 0
        and (
            sa_mom2["is"] > 0 and sa_mom2["oos"] > 0
            if mom_dir
            else sa_fade2["is"] > 0 and sa_fade2["oos"] > 0
        )
    )
    standalone_edge = picked["is"] > 0 and picked["oos"] > 0
    edge_material = picked["oos"] >= 0.30  # a real standalone factor, not noise around zero

    print(f"  === PRE-REGISTERED FALSIFIER VERDICT (n={n_oos_mo} OOS months) ===")
    print(
        f"  [1] standalone net-positive IS AND OOS (picked dir): "
        f"IS={picked['is']:+.2f} OOS={picked['oos']:+.2f} -> "
        f"{'PASS' if standalone_edge else 'FAIL'}"
    )
    print(
        f"  [2] standalone OOS >= +0.30 (a real factor, above the n={n_oos_mo}mo noise floor): "
        f"{picked['oos']:+.2f} -> {'PASS' if edge_material else 'FAIL'}"
    )
    print(
        f"  [3] cost-honest: net-positive at 1× AND 2× taker (not gross-only/turnover-eaten): "
        f"{'PASS' if cost_ok else 'FAIL'}"
    )
    print(
        f"  [4] DISTINCT from CARRY: |corr(basis_z, carry)| < 0.50 (signal) AND "
        f"|corr(basis net, carry net)| < 0.50 (P&L): "
        f"sig={corr_ca:+.3f} net={ncorr['carry']:+.2f} -> "
        f"{'PASS' if (carry_ok and net_carry_ok) else 'FAIL (redundant with the funding LEVEL)'}"
    )
    print(
        f"  [5] residual-additive vs trend+carry+flow (resid OOS > +0.30 AND not collapsed): "
        f"resid OOS={ro['resid_oos']:+.2f} -> {'PASS' if resid_ok else 'FAIL'}"
    )
    print(
        f"  [6] robust across the de-noise window (every cell IS+OOS>0 AND |corr-carry|<0.50): "
        f"-> {'PASS' if (sweep_pos and sweep_carry_ok) else 'FAIL'}"
    )

    distinct_from_carry = carry_ok and net_carry_ok
    real_edge = standalone_edge and edge_material and cost_ok
    orthogonal_additive = distinct_from_carry and resid_ok
    print()
    if real_edge and orthogonal_additive and sweep_pos and sweep_carry_ok:
        print(
            "  VERDICT: ORTHOGONAL CANDIDATE FACTOR — perp-spot basis is a real standalone edge\n"
            "  (positive IS+OOS, cost-honest at 2×), DISTINCT from the funding-LEVEL carry (low\n"
            "  signal AND net corr to carry), residual-additive vs the trend+carry+flow book. The\n"
            "  realized leverage premium carries positioning signal funding can't fully express.\n"
            "  Recommend PROMOTE to a walk-forward / held-OOS CONFIRMATION before the combiner.\n"
            "  Baseline UNCHANGED (iter_005 WF-λ, IS +1.30 / OOS +1.37 / -23%)."
        )
    elif real_edge and not distinct_from_carry:
        print(
            "  VERDICT: REJECT — CARRY-REDUNDANT. The basis HAS a standalone edge, but it is\n"
            "  COLLINEAR with the funding LEVEL in the book (|corr to carry| >= 0.50). Realized\n"
            "  price gap and the funding rate carry the SAME positioning information on this\n"
            "  universe — it would double-count the carry leg's risk, not add a new factor.\n"
            "  Baseline UNCHANGED."
        )
    elif real_edge and distinct_from_carry and not resid_ok:
        print(
            "  VERDICT: REJECT — SPANNED BY THE BOOK. Low pairwise corr to carry, but basis net\n"
            "  is explained away by the JOINT trend+carry+flow regression (resid collapses). Not\n"
            "  independently additive — no new info for the combiner. Baseline UNCHANGED."
        )
    else:
        print(
            "  VERDICT: REJECT — NO STANDALONE EDGE (or cost-eaten / window-fragile). Perp-spot\n"
            "  basis does not carry a usable factor on this universe at realistic taker cost.\n"
            "  Baseline UNCHANGED (iter_005 WF-λ, IS +1.30 / OOS +1.37 / -23%)."
        )


if __name__ == "__main__":
    main()
