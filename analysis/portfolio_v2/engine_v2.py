"""engine_v2 — consolidated, parametrized port of the v1 portfolio backtest engine.

Reproduces the deployed v1 book EXACTLY in v1-compat mode (rank band (0,20], season=None, slip=0):

    iter_004 signals (trend + carry, real funding P&L)
      -> iter_005 walk-forward λ stitch (best past monthly Sharpe, 24m train, 3-candle gap)
      -> iter_020 hysteresis band (δ=0.010 SNAP) + iter_021 eligibility-exit (K=2)
      -> gross renorm to baseline -> vol-target (84-candle, target 0.01, max-lev 3).

Two parametrizations on top:
  1. eligibility from universe_v2.eligibility(rank_lo, rank_hi, season) — replaces the hardcoded
     `rank <= TOP_N` mask everywhere (per-λ book construction AND the eligibility-exit mask).
  2. liquidity-scaled slippage added to the taker cost:
        cost[t] = Σ_c |Δw[c,t]| · (COST_SIDE + slip_side[c,t])
        slip_side[c,t] = slip_bps_fn(dvol_M[c,t]) / 1e4,   dvol_M = liq · 3 / 1e6   (past-only)
     slip_bps_fn=None (or zero_slip) reduces cost to v1's COST_SIDE·Σ|Δw| bit-for-bit.

Canonical configs (used by the run scripts / parity_check):
  PARITY     : load_pool_v1compat(), rank_lo=0,  rank_hi=20, season=None, slip=0   == iter_021 K=2
  v1-honest  : load_pool_pit(),      rank_lo=0,  rank_hi=20, season=168, slip=default
  v2-anchor  : load_pool_pit(),      rank_lo=20, rank_hi=40, season=168, slip=default
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from . import universe_v2 as uv

# ---- v1 constants (must match for parity) --------------------------------------------------
OOS_CUTOFF = pd.Timestamp("2025-03-24")
LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
COST_SIDE = 0.0005
HORIZONS = uv.HORIZONS
VOL_WIN = uv.VOL_WIN
LIQ_WIN = uv.LIQ_WIN
TOP_N = uv.TOP_N
PORT_VOL_WIN = 84
TARGET_VOL = 0.01
MAX_LEV = 3.0
M_FUND = 9
TRAIN_MONTHS = 24
GAP_CANDLES = 3
LAM_GRID = [0.0, 0.1, 0.25, 0.4]
DELTA = 0.010
K_EXIT = 2
MODE = "snap"
STEP_MS = 8 * 60 * 60 * 1000

# ---- default slippage model (config-overridable, monotone, liquidity-scaled) ----------------
SLIP_A = 1.0
SLIP_B = 20.0
SLIP_FLOOR = 1.0
SLIP_CAP = 10.0

SlipFn = Callable[[float | np.ndarray | pd.Series], float | np.ndarray | pd.Series]


def default_slip_bps(dvol_m):
    """Per-side slippage in BPS as a function of daily $-volume in millions (dvol_m).

        slip_side_bps = clip(SLIP_A + SLIP_B / max(dvol_m, 1e-6), SLIP_FLOOR, SLIP_CAP)

    ~1.1bp @ $200M, ~1.5bp @ $40M (rank 21-40 median), ~5bp @ $5M. Monotone decreasing in dvol_m;
    thinner coins pay strictly more, floored/capped. Works on scalars, arrays, and DataFrames.
    """
    if isinstance(dvol_m, pd.DataFrame | pd.Series):
        d = dvol_m.clip(lower=1e-6)
        return (SLIP_A + SLIP_B / d).clip(lower=SLIP_FLOOR, upper=SLIP_CAP)
    arr = np.asarray(dvol_m, dtype=float)
    arr = np.where(arr < 1e-6, 1e-6, arr)
    out = np.clip(SLIP_A + SLIP_B / arr, SLIP_FLOOR, SLIP_CAP)
    return float(out) if np.isscalar(dvol_m) else out


def zero_slip(dvol_m):
    """No slippage — reduces the cost term to v1's pure taker cost. Returns 0 in the same shape."""
    if isinstance(dvol_m, pd.DataFrame | pd.Series):
        return dvol_m * 0.0
    arr = np.asarray(dvol_m, dtype=float) * 0.0
    return float(arr) if np.isscalar(dvol_m) else arr


def make_slip_fn(slip_bps_fn: SlipFn | None, slip_mult: float) -> SlipFn:
    """Resolve the slip bps callable. None -> zero_slip (v1-compat); slip_mult stresses it."""
    base = zero_slip if slip_bps_fn is None else slip_bps_fn
    if slip_mult == 1.0:
        return base

    def _scaled(dvol_m):
        return base(dvol_m) * slip_mult

    return _scaled


# ---- panel construction --------------------------------------------------------------------
def msharpe(net: pd.Series, lo, hi) -> float:
    """Monthly-annualized Sharpe over [lo, hi). Identical to iter_002.msharpe."""
    s = net[(net.index >= lo) & (net.index < hi)]
    g = s.groupby(s.index.to_period("M")).sum()
    return g.mean() / g.std() * np.sqrt(12) if len(g) > 1 and g.std() > 0 else float("nan")


def vol_target(net: pd.Series) -> pd.Series:
    """Past-only per-candle vol-target. Identical to iter_002.vol_target."""
    rv = net.rolling(PORT_VOL_WIN).std().shift(1)
    scale = (TARGET_VOL / rv).clip(upper=MAX_LEV).fillna(0.0)
    return net * scale


def _load_funding(index_ms, syms) -> pd.DataFrame:
    """Funding panel, nearest-match within 4h (iter_004.load_funding fix), reading from pf_data/."""
    import os

    cols = {}
    for s in syms:
        p = f"pf_data/funding_rates/{s}.csv"
        if not os.path.exists(p):
            cols[s] = pd.Series(0.0, index=index_ms)
            continue
        f = pd.read_csv(p).drop_duplicates(subset="funding_time", keep="last")
        f = f.set_index("funding_time")["funding_rate"].astype(float).sort_index()
        cols[s] = f.reindex(index_ms, method="nearest", tolerance=14_400_000).fillna(0.0)
    return pd.DataFrame(cols)


def build_panel(coins: dict, liq_win: int = LIQ_WIN) -> dict:
    """Build the datetime-indexed opens/close/qv/fund/liq panels shared by all λ (iter_004 layout).

    Funding is read from pf_data/funding_rates/<SYM>.csv if present, else a synthetic `funding`
    column on each coin frame is used (tests), else 0. liq is the past-only trailing $-volume
    (qv.rolling(liq_win).mean().shift(1)) used for the slippage dvol; `liq_win` defaults to the v1
    parity constant LIQ_WIN and is overridden only by the fast unit tests on short panels.
    """
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).astype(float).sort_index()
    close = (
        pd.DataFrame({s: d["close"] for s, d in coins.items()}).astype(float).reindex(opens.index)
    )
    qv = (
        pd.DataFrame({s: d["quote_volume"] for s, d in coins.items()})
        .astype(float)
        .reindex(opens.index)
    )

    # funding: prefer per-coin synthetic `funding` column (tests); else load from disk.
    if all("funding" in d.columns for d in coins.values()):
        fund = (
            pd.DataFrame({s: d["funding"] for s, d in coins.items()})
            .astype(float)
            .reindex(opens.index)
        )
    else:
        fund = _load_funding(opens.index, list(coins.keys())).reindex(opens.index)

    dt = pd.to_datetime(opens.index, unit="ms")
    cols = list(coins.keys())
    for df in (opens, close, qv, fund):
        df.index = dt
    opens, close, qv, fund = (df[cols] for df in (opens, close, qv, fund))

    liq = qv.rolling(liq_win).mean().shift(1)
    return {
        "opens": opens,
        "close": close,
        "qv": qv,
        "fund": fund,
        "liq": liq,
        "cols": cols,
    }


def _slip_side_panel(liq: pd.DataFrame, slip_fn: SlipFn) -> pd.DataFrame:
    """Per-coin per-candle slip fraction: slip_bps_fn(dvol_M) / 1e4, dvol_M = liq · 3 / 1e6.

    liq is the trailing-mean per-candle $-volume (past-only). ·3 converts an 8h candle's $-vol to a
    daily figure; /1e6 -> millions. NaN liq (un-warmed / un-listed) -> 0 slip (no spurious cost).
    """
    dvol_m = liq * 3.0 / 1e6
    slip_bps = slip_fn(dvol_m)
    slip_bps = slip_bps.where(dvol_m.notna(), 0.0)
    return (slip_bps / 1e4).fillna(0.0)


# ---- signals -------------------------------------------------------------------------------
def _signals(panel: dict) -> dict:
    """trend / carry / rvol / ret_fwd / fund_next — past-only, identical to iter_004/iter_005."""
    close = panel["close"]
    opens = panel["opens"]
    fund = panel["fund"]
    ret_fwd = opens.shift(-1) / opens - 1.0
    rvol = close.pct_change().rolling(VOL_WIN).std()
    trend = sum(np.sign(close / close.shift(h) - 1.0) for h in HORIZONS) / len(HORIZONS)
    carry = -np.sign(fund.rolling(M_FUND).mean())
    fund_next = fund.shift(-1)
    return {
        "trend": trend,
        "carry": carry,
        "rvol": rvol,
        "ret_fwd": ret_fwd,
        "fund_next": fund_next,
    }


# ---- iter-v2-002: cross-sectional momentum (XS-mom) -----------------------------------------
XS_GAMMA = 0.0
XS_LOOKBACK = 84
XS_NMIN = 8


def _xsmom(
    close: pd.DataFrame, elig: pd.DataFrame, lookback: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Centered within-band return-rank XS-mom signal + its past-only L-return panel `mom`.

    Bit-identical to v1's iter_002_top20.build('xsec_mom') lines 85-89 (lookback L=84), revived on
    the rank-21-40 band here:

        mom = close / close.shift(L) - 1.0                # trailing L-return, past-only
        rk  = mom.where(elig).rank(axis=1)                # cross-sectional rank in the band, asc
        n   = elig.sum(axis=1)                            # number of names in the band at t
        xs  = (rk - (n+1)/2) / n , masked .where(elig)    # CENTERED, dollar-neutral in [-0.5, +0.5]

    `xs` is `0.0`-filled where ineligible (never NaN) so it can be blended into `combined` without
    injecting NaN: at γ=0 the engine early-returns to `tc` and never touches `xs`; at γ>0 the
    0.0-fill contributes exactly 0.0 outside the band (masked off by `.where(elig)` downstream).
    Returns (xs, mom) — `mom` is reused for the dispersion gate.
    """
    mom = close / close.shift(lookback) - 1.0
    rk = mom.where(elig).rank(axis=1)
    n = elig.sum(axis=1)
    xs = rk.sub(n.add(1) / 2.0, axis=0).div(n, axis=0).where(elig).fillna(0.0)
    return xs, mom


def _xs_gate_mask(
    mom: pd.DataFrame,
    elig: pd.DataFrame,
    n_min: int,
    disp_min: float | None,
) -> pd.Series:
    """Past-only dispersion / min-names gate. Returns a per-candle bool Series: True => the XS-mom
    term is GATED OFF for that candle (blend reverts to pure trend+carry `tc`, fail-safe to anchor).

    Both conditions are computed on the band's eligible members as of the PRIOR close (`.shift(1)`):
        n[t]    = elig.sum(axis=1)                          # band size at t
        disp[t] = cross-sectional std of mom over the eligible band at t   (L-return spread)
    GATE OFF iff  (n[t] < n_min)  OR  (disp[t] < disp_min).  disp_min=None disables dispersion leg.
    """
    n_prev = elig.sum(axis=1).shift(1)
    disp_prev = mom.where(elig).std(axis=1).shift(1)
    gate = (n_prev < n_min).fillna(True)
    if disp_min is not None:
        gate = gate | (disp_prev < disp_min).fillna(True)
    return gate


# ---- per-λ book (the small-panel-safe building block) --------------------------------------
def fixed_lambda_book(
    coins: dict,
    *,
    lam: float,
    rank_lo: float = 0,
    rank_hi: float = TOP_N,
    season: int | None = None,
    slip_bps_fn: SlipFn | None = None,
    cost_mult: float = 1.0,
    slip_mult: float = 1.0,
    liq_win: int = LIQ_WIN,
    xs_gamma: float = XS_GAMMA,
    xs_lookback: int = XS_LOOKBACK,
    xs_nmin: int = XS_NMIN,
    xs_disp_min: float | None = None,
) -> dict:
    """One λ's canonical pre-band book: lagged gross-normalized weights `w` + the vol-targeted net.

    This is iter_004/iter_005's exact per-λ construction, parametrized by the (rank band + season)
    eligibility and the slippage cost term. Returns w / pnl / fpnl / cost / raw_net / scale / net.
    With slip=0 + v1-compat eligibility (lo=0, hi=20, season=None) the cost and net are the v1 ones
    bit-for-bit. Small-panel safe (no walk-forward) — the leak/cost unit tests call this directly.

    iter-v2-002 — XS-mom blend (parity-preserving at γ=0):
        tc       = (1 - lam) * trend + lam * carry                  # unchanged anchor combo
        combined = (1 - xs_gamma) * tc + xs_gamma * xs              # γ-tilt to XS-mom
        raw      = (combined / rvol).where(elig)
    HARD γ=0 parity guard: `xs_gamma == 0.0` early-returns `combined = tc` — the `xs` panel is
    never even built/multiplied, so the numerator is `tc` bit-for-bit (no NaN/dtype perturb). §2.3
    dispersion/min-names gate forces the xs-term to 0 on gated candles (combined reverts to `tc`,
    fail-safe to the anchor). The XS term flows through the SAME /rvol, gross-norm, lag, slippage,
    band, eligexit, vol-target pipeline — its higher-turnover cost is charged honestly.
    """
    panel = build_panel(coins, liq_win=liq_win)
    sig = _signals(panel)
    elig = (
        uv.eligibility(coins, rank_lo, rank_hi, season, liq_win=liq_win)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )

    tc = (1 - lam) * sig["trend"] + lam * sig["carry"]
    if xs_gamma == 0.0:
        # HARD γ=0 parity guard: never touch `xs`; combined IS tc, bit-for-bit with the anchor line.
        combined = tc
    else:
        xs, mom = _xsmom(panel["close"], elig, xs_lookback)
        gate = _xs_gate_mask(mom, elig, xs_nmin, xs_disp_min)
        # gate OFF (True) => force the xs-term to 0 that candle (combined reverts to tc).
        gamma_t = pd.Series(xs_gamma, index=tc.index).where(~gate, 0.0)
        combined = tc.mul(1.0 - gamma_t, axis=0) + xs.mul(gamma_t, axis=0)

    raw = (combined / sig["rvol"]).where(elig)
    w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)

    slip_fn = make_slip_fn(slip_bps_fn, slip_mult)
    slip_side = (
        _slip_side_panel(panel["liq"], slip_fn)
        .reindex(index=w.index, columns=w.columns)
        .fillna(0.0)
    )

    dw = (w - w.shift(1)).abs()
    pnl = (w * sig["ret_fwd"].reindex(columns=w.columns)).sum(axis=1)
    fpnl = -(w * sig["fund_next"].reindex(columns=w.columns)).sum(axis=1)
    cost = (dw * (COST_SIDE * cost_mult + slip_side)).sum(axis=1)
    raw_net = (pnl + fpnl - cost).dropna()

    rv = raw_net.rolling(PORT_VOL_WIN).std().shift(1)
    scale = (TARGET_VOL / rv).clip(upper=MAX_LEV).fillna(0.0)
    return {
        "w": w,
        "pnl": pnl,
        "fpnl": fpnl,
        "cost": cost,
        "raw_net": raw_net,
        "scale": scale,
        "net": raw_net * scale,
        "ret_fwd": sig["ret_fwd"].reindex(columns=w.columns),
        "fund_next": sig["fund_next"].reindex(columns=w.columns),
        "slip_side": slip_side,
        "elig": elig,
    }


# ---- walk-forward λ stitch (iter_005 / iter_020 canonical_book) -----------------------------
def _canonical_book(books: dict) -> dict:
    """Stitch the walk-forward-λ choice into a single per-candle canonical target book.

    Identical month loop to iter_005.walkforward / iter_020.canonical_book: best past monthly
    Sharpe on the vol-targeted per-λ nets, 24m train, 3-candle gap, >=200 train candles. Stitches
    the chosen λ's WEIGHTS + per-candle scale (reproduces the stitched net exactly).
    """
    panel = pd.DataFrame({lam: books[lam]["net"] for lam in books}).sort_index()
    months = pd.PeriodIndex(panel.index, freq="M").unique().sort_values()
    any_w = next(iter(books.values()))["w"]
    cols = any_w.columns
    target_w = pd.DataFrame(0.0, index=any_w.index, columns=cols)
    scale = pd.Series(0.0, index=any_w.index)
    covered = pd.Series(False, index=any_w.index)
    picks = []
    for ms in months:
        m0 = ms.to_timestamp()
        lo = m0 - pd.DateOffset(months=TRAIN_MONTHS)
        hi = m0 - pd.Timedelta(milliseconds=GAP_CANDLES * STEP_MS)
        test_hi = (ms + 1).to_timestamp()
        train = panel[(panel.index >= lo) & (panel.index < hi)]
        test_mask = (panel.index >= m0) & (panel.index < test_hi)
        if len(train) < 200 or not test_mask.any():
            continue
        tsh = train.apply(lambda s: msharpe(s, LO0, HI1))
        if not np.isfinite(tsh.max()):
            continue
        best = tsh.idxmax()
        picks.append((m0.year, best))
        idx = panel.index[test_mask]
        target_w.loc[idx, cols] = books[best]["w"].reindex(index=idx, columns=cols).to_numpy()
        scale.loc[idx] = books[best]["scale"].reindex(idx).to_numpy()
        covered.loc[idx] = True
    target_w = target_w.loc[covered]
    scale = scale.loc[covered]
    ret_fwd = next(iter(books.values()))["ret_fwd"].reindex(index=target_w.index, columns=cols)
    fund_next = next(iter(books.values()))["fund_next"].reindex(index=target_w.index, columns=cols)
    slip_side = (
        next(iter(books.values()))["slip_side"]
        .reindex(index=target_w.index, columns=cols)
        .fillna(0.0)
    )
    return {
        "target_w": target_w,
        "scale": scale,
        "ret_fwd": ret_fwd,
        "fund_next": fund_next,
        "slip_side": slip_side,
        "picks": picks,
    }


# ---- band + eligibility-exit overlay (iter_020 / iter_021) ----------------------------------
def _apply_band_eligexit(
    target_w: pd.DataFrame,
    elig: pd.DataFrame,
    delta: float,
    k_exit: float,
    mode: str = "snap",
) -> pd.DataFrame:
    """iter_021.apply_band_eligexit, bit-for-bit. Band SNAP/EDGE step + force-close coins ineligible
    for >= k_exit consecutive candles (overriding the band). k_exit=inf disables the overlay ->
    iter_020.apply_band. The forced zero is written into `prev` -> propagates (path dependence)."""
    tw = target_w.to_numpy()
    el = elig.to_numpy()
    n, m = tw.shape
    held = np.empty_like(tw)
    streak = np.zeros(m, dtype=np.int64)

    def _force_exit(row_idx: int, cur: np.ndarray) -> np.ndarray:
        elig_row = el[row_idx]
        streak[elig_row] = 0
        streak[~elig_row] += 1
        if np.isfinite(k_exit):
            cur = cur.copy()
            cur[streak >= k_exit] = 0.0
        return cur

    held[0] = _force_exit(0, tw[0].copy())
    prev = held[0].copy()
    no_band = delta <= 0.0
    for t in range(1, n):
        tgt = tw[t]
        if no_band:
            cur = tgt.copy()
        else:
            move = tgt - prev
            cur = prev.copy()
            trig = np.abs(move) > delta
            if mode == "edge":
                cur[trig] = prev[trig] + np.sign(move[trig]) * (np.abs(move[trig]) - delta)
            else:
                cur[trig] = tgt[trig]
        cur = _force_exit(t, cur)
        held[t] = cur
        prev = cur
    return pd.DataFrame(held, index=target_w.index, columns=target_w.columns)


def _renorm(target_w: pd.DataFrame, held: pd.DataFrame) -> pd.DataFrame:
    """Renorm the post-overlay held gross back to the baseline per-candle gross (iter_020 step)."""
    base_gross = target_w.abs().sum(axis=1)
    held_gross = held.abs().sum(axis=1).replace(0, np.nan)
    return held.mul((base_gross / held_gross).fillna(0.0), axis=0)


# ---- top-level driver ----------------------------------------------------------------------
def run_book_from_signal(
    coins: dict,
    signal_panel: pd.DataFrame,
    *,
    rank_lo: float = 0,
    rank_hi: float = TOP_N,
    season: int | None = None,
    slip_bps_fn: SlipFn | None = None,
    delta: float = DELTA,
    k_exit: float = K_EXIT,
    mode: str = MODE,
    cost_mult: float = 1.0,
    slip_mult: float = 1.0,
    liq_win: int = LIQ_WIN,
) -> dict:
    """Full v2 pipeline driven by a PRECOMPUTED per-(coin, candle) `signal_panel` — the ML path.

    `signal_panel` is a candle-indexed, coin-columned DataFrame holding the (already centered /
    dollar-neutral, on the same scale as the other signals) target signal at each candle. It plays
    the role the trend+carry blend plays inside `fixed_lambda_book`: the engine runs the EXACT SAME
    downstream pipeline on it, with NO walk-forward λ selection (the signal IS the target, λ is a
    trend+carry concept):

        raw = (signal_panel / rvol).where(elig)              # inverse-vol size, band-masked
          -> gross-norm (Σ|raw| = 1 per candle)
          -> .shift(1) lag (decisions act on the next candle)            == target_w
          -> _apply_band_eligexit (δ SNAP/EDGE band + K-exit force-close)
          -> _renorm (back to the pre-band gross)
          -> net = pnl + funding - cost (taker + liquidity slippage)
          -> vol-target (84-candle, target 0.01, max-lev 3).

    Reuses build_panel / _signals (for rvol/ret_fwd/fund_next) / eligibility / _slip_side_panel /
    _apply_band_eligexit / _renorm — the IDENTICAL code paths `run_book` uses, so it cannot perturb
    `run_book` (this is a brand-new entry point; parity_check stays green). Returns the SAME dict
    shape as `run_book` (net, target_w, held_w, turnover, avg_positions, tickets, scale, IS, OOS).

    `signal_panel` is reindexed onto the opens grid + coin columns and NaN-filled to 0.0 before the
    /rvol step, so a missing-coin / missing-candle cell contributes exactly 0.0 (the `.where(elig)`
    masks it off anyway). A constant or all-zero signal yields a degenerate (zero-gross) book
    without error (the gross-norm divides by NaN where the gross is 0 and `.fillna(0.0)` flattens).
    """
    panel = build_panel(coins, liq_win=liq_win)
    sig = _signals(panel)
    elig = (
        uv.eligibility(coins, rank_lo, rank_hi, season, liq_win=liq_win)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )

    # Align the supplied signal onto the engine grid; missing cells -> 0.0 (masked off by elig).
    signal = (
        signal_panel.reindex(index=panel["opens"].index, columns=panel["cols"])
        .astype(float)
        .fillna(0.0)
    )

    # raw -> gross-norm -> lag : SAME construction as fixed_lambda_book, signal in place of `tc`.
    raw = (signal / sig["rvol"]).where(elig)
    target_w = raw.div(raw.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0).shift(1)

    # band + eligibility-exit overlay + renorm (UNCHANGED helpers).
    held = _apply_band_eligexit(target_w, elig, delta, k_exit, mode)
    w = _renorm(target_w, held)

    slip_fn = make_slip_fn(slip_bps_fn, slip_mult)
    slip_side = (
        _slip_side_panel(panel["liq"], slip_fn)
        .reindex(index=w.index, columns=w.columns)
        .fillna(0.0)
    )
    ret_fwd = sig["ret_fwd"].reindex(columns=w.columns)
    fund_next = sig["fund_next"].reindex(columns=w.columns)

    dw = (w - w.shift(1)).abs()
    pnl = (w * ret_fwd).sum(axis=1)
    fpnl = -(w * fund_next).sum(axis=1)
    cost = (dw * (COST_SIDE * cost_mult + slip_side)).sum(axis=1)
    raw_net = (pnl + fpnl - cost).dropna()

    rv = raw_net.rolling(PORT_VOL_WIN).std().shift(1)
    scale = (TARGET_VOL / rv).clip(upper=MAX_LEV).fillna(0.0)
    net = (raw_net * scale.reindex(raw_net.index)).dropna()

    turnover = float(dw.sum(axis=1).iloc[1:].mean()) if len(dw) > 1 else float("nan")
    tickets = float((dw > 1e-6).sum(axis=1).iloc[1:].mean()) if len(dw) > 1 else float("nan")
    avg_positions = float((w.abs() > 1e-9).sum(axis=1).mean())

    return {
        "net": net,
        "raw_net": raw_net,
        "target_w": target_w,
        "held_w": w,
        "picks": [],
        "turnover": turnover,
        "avg_positions": avg_positions,
        "tickets": tickets,
        "scale": scale,
        "ret_fwd": ret_fwd,
        "fund_next": fund_next,
        "elig": elig,
        "IS": msharpe(net, LO0, OOS_CUTOFF),
        "OOS": msharpe(net, OOS_CUTOFF, HI1),
    }


def run_book(
    coins: dict,
    *,
    rank_lo: float = 0,
    rank_hi: float = TOP_N,
    season: int | None = None,
    slip_bps_fn: SlipFn | None = None,
    delta: float = DELTA,
    k_exit: float = K_EXIT,
    mode: str = MODE,
    cost_mult: float = 1.0,
    slip_mult: float = 1.0,
    liq_win: int = LIQ_WIN,
    xs_gamma: float = XS_GAMMA,
    xs_lookback: int = XS_LOOKBACK,
    xs_nmin: int = XS_NMIN,
    xs_disp_min: float | None = None,
) -> dict:
    """Full v2 pipeline -> dict(net, target_w, picks, turnover, avg_positions, tickets, ...).

    v1-compat (rank_lo=0, rank_hi=20, season=None, slip_bps_fn=None/zero, delta=0.010, k_exit=2)
    reproduces iter_021 K=2 bit-for-bit. The slippage + (rank band, season) parametrizations enter
    BOTH the per-λ book (so λ-selection is slippage-aware) and the final banded net.

    iter-v2-002: the XS-mom params (xs_gamma/xs_lookback/xs_nmin/xs_disp_min) enter the per-λ books
    ONLY — they reshape the signal numerator inside each `fixed_lambda_book`, so the walk-forward
    λ-selection sees the XS-augmented nets AND the final banded net is stitched from those books'
    weights. The canonical-book stitch / band / eligexit / renorm / vol-target are UNCHANGED. At
    xs_gamma=0.0 every book early-returns to `tc`, so the whole pipeline is bit-for-bit the anchor.
    """
    books = {
        lam: fixed_lambda_book(
            coins,
            lam=lam,
            rank_lo=rank_lo,
            rank_hi=rank_hi,
            season=season,
            slip_bps_fn=slip_bps_fn,
            cost_mult=cost_mult,
            slip_mult=slip_mult,
            liq_win=liq_win,
            xs_gamma=xs_gamma,
            xs_lookback=xs_lookback,
            xs_nmin=xs_nmin,
            xs_disp_min=xs_disp_min,
        )
        for lam in LAM_GRID
    }
    book = _canonical_book(books)
    target_w = book["target_w"]

    elig = (
        uv.eligibility(coins, rank_lo, rank_hi, season, liq_win=liq_win)
        .reindex(index=target_w.index, columns=target_w.columns)
        .fillna(False)
    )

    held = _apply_band_eligexit(target_w, elig, delta, k_exit, mode)
    w = _renorm(target_w, held)

    slip_side = book["slip_side"].reindex(index=w.index, columns=w.columns).fillna(0.0)
    dw = (w - w.shift(1)).abs()
    pnl = (w * book["ret_fwd"]).sum(axis=1)
    fpnl = -(w * book["fund_next"]).sum(axis=1)
    cost = (dw * (COST_SIDE * cost_mult + slip_side)).sum(axis=1)
    raw_net = (pnl + fpnl - cost).dropna()
    net = (raw_net * book["scale"].reindex(raw_net.index)).dropna()

    turnover = float(dw.sum(axis=1).iloc[1:].mean()) if len(dw) > 1 else float("nan")
    tickets = float((dw > 1e-6).sum(axis=1).iloc[1:].mean()) if len(dw) > 1 else float("nan")
    avg_positions = float((w.abs() > 1e-9).sum(axis=1).mean())

    return {
        "net": net,
        "target_w": target_w,
        "held_w": w,
        "picks": book["picks"],
        "turnover": turnover,
        "avg_positions": avg_positions,
        "tickets": tickets,
        "scale": book["scale"],
        "ret_fwd": book["ret_fwd"],
        "fund_next": book["fund_next"],
        "elig": elig,
        "IS": msharpe(net, LO0, OOS_CUTOFF),
        "OOS": msharpe(net, OOS_CUTOFF, HI1),
    }
