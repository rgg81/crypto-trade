"""team-07 — cointegration convergence, discovery baseline.

Rolling pairwise Engle-Granger cointegration on log close prices, a preregistered
half-life, and the three-part stop described in section 4 of lane/scouting/THESIS.md.

Every constant below is a Tier-0 fixture, a Tier-1 declared centre, or a Tier-2
declared default from the preregistered parameter surface. Nothing here has been
moved in response to a result, because no result exists yet.

State: none. Every quantity is recomputed from the past-only window at each decision,
including the "position", which is reconstructed from the residual path rather than
remembered (commitment C4).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

# --- Tier 0: fixed by preregistration, never searched -------------------------------
# price transform          log(close)
# method                   Engle-Granger, log P_dep ~ 1 + log P_ind, ADF on residual
# z basis                  in-window residual mean/sd, past-only, no embargo
# excursion clock          bars since the residual last crossed its in-window mean
# leg sizing               beta-weighted, pair gross normalised
# volatility targeting     none (engine-owned)

# --- Tier 1: declared centre --------------------------------------------------------
HALF_LIFE = 15  # H, preregistered half-life in 8h bars (5 days)
K_AGE = 2  # k, excursion-age stop, in half-lives
Z_IN = 2.0  # entry threshold, in formation-window sigma
Z_STOP = 3.5  # divergence stop, in formation-window sigma
N_PAIRS = 20  # pairs held

# --- Tier 2: declared defaults ------------------------------------------------------
WINDOW = 180  # W, formation window in 8h bars (60 days); satisfies W >= 6H
ADF_TAU = -3.0  # residual ADF t-statistic screen
Z_OUT = 0.25  # take-profit band
M_PARTNERS = 5  # correlation-ranked partners tested per symbol
M_MAX = 2  # max pairs a single symbol may appear in
EVENT_E = 8.0  # idiosyncratic-event veto, in trailing leg dispersion
BETA_DRIFT = 0.50  # beta-drift invalidation band (stop S2)
LIQ_FLOOR = 0.25  # universe filter, cross-sectional quote-volume percentile
FUNDING_VETO = True

# --- Implementation fixtures (not knobs; the simplest admissible value) -------------
ADF_LAGS = 1  # augmenting lags in the residual Dickey-Fuller regression
GROSS = 1.0  # book gross before caps; the engine owns the risk unit
MAX_WEIGHT = 0.10
MAX_NET = 0.25
MIN_SYMBOLS = 3
EPS = 1e-12


def _build_panel(
    bars: Mapping[str, pd.DataFrame], symbols: Sequence[str], window: int
) -> pd.DataFrame | None:
    """Close-price panel aligned on ``open_time``, not on the positional index.

    Symbols whose own last ``window`` bars do not land exactly on the panel grid are
    dropped rather than forward-filled: a gap means the spread was not observable.
    """
    cols: dict[str, pd.Series] = {}
    for sym in symbols:
        frame = bars.get(sym)
        if frame is None or len(frame) < window:
            continue
        if "open_time" not in frame.columns or "close" not in frame.columns:
            continue
        tail = frame.iloc[-window:]
        stamps = tail["open_time"]
        if stamps.duplicated().any() or stamps.isna().any():
            continue
        cols[sym] = pd.Series(tail["close"].to_numpy(dtype=float), index=stamps.to_numpy())
    if len(cols) < MIN_SYMBOLS:
        return None

    panel = pd.concat(cols, axis=1).sort_index()
    if panel.shape[0] < window:
        return None
    panel = panel.iloc[-window:].dropna(axis=1, how="any")
    if panel.shape[1] < MIN_SYMBOLS:
        return None
    panel = panel.loc[:, (panel > 0.0).all(axis=0).to_numpy()]
    return panel if panel.shape[1] >= MIN_SYMBOLS else None


def _median_quote_volume(
    bars: Mapping[str, pd.DataFrame], symbols: Sequence[str], window: int
) -> np.ndarray:
    out = np.zeros(len(symbols), dtype=float)
    for pos, sym in enumerate(symbols):
        frame = bars.get(sym)
        if frame is None or "quote_volume" not in frame.columns:
            continue
        vol = frame["quote_volume"].iloc[-window:].to_numpy(dtype=float)
        if vol.size:
            med = np.nanmedian(vol)
            out[pos] = med if np.isfinite(med) else 0.0
    return out


def _mean_funding(funding: pd.DataFrame, symbols: Sequence[str], since) -> np.ndarray:
    """Trailing mean 8h funding rate per symbol over the formation window's span.

    Returns zeros when the funding frame is unusable, which makes the funding veto
    inert rather than silently wrong. That shows up as an unchanged cost share.
    """
    zeros = np.zeros(len(symbols), dtype=float)
    if funding is None or len(funding) == 0:
        return zeros
    needed = {"symbol", "funding_rate", "funding_time"}
    if not needed.issubset(set(funding.columns)):
        return zeros
    stamps = funding["funding_time"]
    # ``since`` comes from the bar panel's own ``open_time``; only compare the two
    # clocks when they are the same kind of clock. Otherwise leave the veto inert.
    if pd.api.types.is_datetime64_any_dtype(stamps) != isinstance(
        since, (pd.Timestamp, np.datetime64)
    ):
        return zeros
    recent = funding.loc[stamps.to_numpy() >= since, ["symbol", "funding_rate"]]
    if recent.empty:
        return zeros
    per_symbol = recent.groupby("symbol")["funding_rate"].mean()
    return np.array([float(per_symbol.get(sym, 0.0)) for sym in symbols], dtype=float)


def _robust_scale(values: np.ndarray) -> np.ndarray:
    """Column-wise MAD scale, normalised to be a standard deviation under normality.

    The event veto has to measure a jump against a dispersion the jump did not itself
    inflate. With 179 returns in the window, a genuine 8-sigma bar raises the ordinary
    standard deviation by ~17%, so an ``e * std`` rule would need a ~10-sigma move to
    fire and would sit inert. The median absolute deviation does not move.
    """
    centre = np.median(values, axis=0)
    return 1.4826 * np.median(np.abs(values - centre), axis=0)


def _ols_beta(dep: np.ndarray, ind: np.ndarray) -> np.ndarray:
    """Slope of a batched univariate regression with intercept, column-wise."""
    dep_c = dep - dep.mean(axis=0)
    ind_c = ind - ind.mean(axis=0)
    denom = (ind_c * ind_c).sum(axis=0)
    return np.where(denom > EPS, (dep_c * ind_c).sum(axis=0) / np.where(denom > EPS, denom, 1.0), np.nan)


def _df_tstat(resid: np.ndarray, lags: int) -> np.ndarray:
    """Dickey-Fuller t-statistic on each column of ``resid``.

    The Engle-Granger residual is mean-zero by construction, so the test regression
    carries no intercept: d u_t = rho * u_{t-1} + sum_l phi_l * d u_{t-l} + e_t.
    Only ``lags == 1`` is used; the branchless algebra below is the 2x2 solve.
    """
    du = np.diff(resid, axis=0)
    resp = du[lags:]
    ylag = resid[lags:-1]
    if lags == 0:
        s11 = (ylag * ylag).sum(axis=0)
        rho = np.where(s11 > EPS, (ylag * resp).sum(axis=0) / np.where(s11 > EPS, s11, 1.0), np.nan)
        err = resp - rho * ylag
        dof = max(resp.shape[0] - 1, 1)
        sigma2 = (err * err).sum(axis=0) / dof
        var_rho = np.where(s11 > EPS, sigma2 / np.where(s11 > EPS, s11, 1.0), np.nan)
    else:
        dlag = du[:-lags]
        s11 = (ylag * ylag).sum(axis=0)
        s12 = (ylag * dlag).sum(axis=0)
        s22 = (dlag * dlag).sum(axis=0)
        b1 = (ylag * resp).sum(axis=0)
        b2 = (dlag * resp).sum(axis=0)
        det = s11 * s22 - s12 * s12
        safe = np.where(np.abs(det) > EPS, det, np.nan)
        rho = (b1 * s22 - b2 * s12) / safe
        phi = (s11 * b2 - s12 * b1) / safe
        err = resp - rho * ylag - phi * dlag
        dof = max(resp.shape[0] - 2, 1)
        sigma2 = (err * err).sum(axis=0) / dof
        var_rho = sigma2 * s22 / safe
    return rho / np.sqrt(np.where(var_rho > EPS, var_rho, np.nan))


def _excursion(resid: np.ndarray) -> np.ndarray:
    """First row index of the residual's current excursion, per column.

    The excursion begins at the bar after the residual last crossed its in-window
    mean. If it never crossed, the excursion is the whole window, which the
    excursion-age stop will then reject.
    """
    positive = resid > 0.0
    changed = positive[1:] != positive[:-1]
    last = (changed.shape[0] - 1) - np.argmax(changed[::-1], axis=0)
    return np.where(changed.any(axis=0), last + 1, 0)


def _masked_from(values: np.ndarray, start: np.ndarray, fill: float) -> np.ndarray:
    rows = np.arange(values.shape[0])[:, None]
    return np.where(rows >= start[None, :], values, fill)


def _apply_caps(weights: dict[str, float]) -> dict[str, float]:
    """Gross <= 1.0, |w| <= 0.10, |net| <= 0.25 -- in that order, reductions only."""
    if not weights:
        return {}
    names = list(weights)
    vec = np.array([weights[n] for n in names], dtype=float)
    vec = np.where(np.isfinite(vec), vec, 0.0)

    gross = np.abs(vec).sum()
    if gross <= EPS:
        return {}
    vec = vec * (GROSS / gross)
    vec = np.clip(vec, -MAX_WEIGHT, MAX_WEIGHT)

    net = vec.sum()
    if abs(net) > MAX_NET:
        longs = vec[vec > 0].sum()
        shorts = -vec[vec < 0].sum()
        if net > 0.0 and longs > EPS:
            vec = np.where(vec > 0, vec * ((shorts + MAX_NET) / longs), vec)
        elif net < 0.0 and shorts > EPS:
            vec = np.where(vec < 0, vec * ((longs + MAX_NET) / shorts), vec)

    return {n: float(w) for n, w in zip(names, vec) if abs(w) > 1e-6}


class CointegrationConvergence:
    """Hold a book of beta-hedged pairs whose residual is far from its in-window mean."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed  # no randomness is used anywhere in this strategy

        eligible = list(context.eligible_symbols)
        if len(eligible) < MIN_SYMBOLS:
            return {}
        panel = _build_panel(context.bars, eligible, WINDOW)
        if panel is None:
            return {}

        symbols = [str(c) for c in panel.columns]
        logp = np.log(panel.to_numpy(dtype=float))

        # --- universe filter: drop the thinnest LIQ_FLOOR of the cross-section -------
        med_qv = _median_quote_volume(context.bars, symbols, WINDOW)
        rets = np.diff(logp, axis=0)
        disp = rets.std(axis=0)
        keep = (disp > EPS) & np.isfinite(disp)
        if LIQ_FLOOR > 0.0 and keep.sum() >= MIN_SYMBOLS:
            floor = np.quantile(med_qv[keep], LIQ_FLOOR)
            keep &= med_qv >= floor
        if keep.sum() < MIN_SYMBOLS:
            return {}
        idx = np.flatnonzero(keep)
        symbols = [symbols[i] for i in idx]
        logp = logp[:, idx]
        rets = rets[:, idx]
        disp = disp[idx]
        n_sym = len(symbols)

        # --- C6: bounded candidate generation, top-m return-correlated partners ------
        centred = rets - rets.mean(axis=0)
        corr = (centred.T @ centred) / (rets.shape[0] * np.outer(disp, disp))
        np.fill_diagonal(corr, -np.inf)
        m_use = min(M_PARTNERS, n_sym - 1)
        partners = np.argsort(-corr, axis=1, kind="stable")[:, :m_use]
        candidates = set()
        for i in range(n_sym):
            for j in partners[i]:
                jj = int(j)
                if not np.isfinite(corr[i, jj]) or corr[i, jj] <= 0.0:
                    continue
                candidates.add((i, jj) if i < jj else (jj, i))
        if not candidates:
            return {}
        pair_list = sorted(candidates)
        left = np.array([a for a, _ in pair_list])
        right = np.array([b for _, b in pair_list])

        # The higher-return-variance leg is the regressand. This is symmetric under
        # renaming and under price rescaling, and avoids testing both directions and
        # keeping the better one, which would be a second selection channel.
        swap = disp[left] < disp[right]
        dep_i = np.where(swap, right, left)
        ind_i = np.where(swap, left, right)

        # --- Engle-Granger on log levels --------------------------------------------
        y = logp[:, dep_i]
        x = logp[:, ind_i]
        beta = _ols_beta(y, x)
        resid = (y - y.mean(axis=0)) - beta * (x - x.mean(axis=0))
        sigma = resid.std(axis=0)

        tstat = _df_tstat(resid, ADF_LAGS)

        half = WINDOW // 2
        beta_recent = _ols_beta(y[-half:], x[-half:])
        drift = np.abs(beta_recent - beta) / np.maximum(np.abs(beta), EPS)

        with np.errstate(invalid="ignore", divide="ignore"):
            zpath = resid / np.where(sigma > EPS, sigma, np.nan)
        z_now = zpath[-1]

        start = _excursion(resid)
        age = (WINDOW - 1) - start
        peak = _masked_from(np.abs(zpath), start, -1.0).max(axis=0)

        # --- idiosyncratic-event veto: news is a break, not an excursion -------------
        scale = _robust_scale(rets)
        scale = np.where(scale > EPS, scale, disp)
        jumped = np.abs(rets) > (EVENT_E * scale[None, :])
        pair_jump = jumped[:, dep_i] | jumped[:, ind_i]
        news = _masked_from(pair_jump.astype(float), np.maximum(start - 1, 0), 0.0).max(axis=0) > 0.0

        # --- screen and the three stops ---------------------------------------------
        ok = np.isfinite(tstat) & np.isfinite(beta) & (sigma > EPS)
        ok &= tstat <= ADF_TAU  # cointegration screen
        ok &= beta > 0.0  # a negative hedge ratio doubles the common trend
        ok &= drift <= BETA_DRIFT  # S2, relationship invalidation
        ok &= ~news  # idiosyncratic-event veto
        ok &= np.isfinite(z_now)

        side = -np.sign(z_now)  # +1 means long the dependent leg
        active = (
            ok
            & (peak >= Z_IN)  # the excursion did reach the entry band ...
            & (peak < Z_STOP)  # ... and was not stopped out on divergence (S3)
            & (np.abs(z_now) >= Z_OUT)  # ... and has not yet taken profit
            & (age <= K_AGE * HALF_LIFE)  # S1, excursion-age / model invalidation
            & (side != 0.0)
        )

        # --- funding veto: carry that swallows the convergence it is waiting for -----
        if FUNDING_VETO:
            fund = _mean_funding(context.funding, symbols, panel.index[0])
            # legs are w_dep = side*size, w_ind = -side*beta*size; a long pays f, so
            # funding P&L per bar per unit size is -(w_dep f_dep + w_ind f_ind)/size.
            carry = -side * (fund[dep_i] - beta * fund[ind_i])
            gain = np.abs(z_now) * sigma  # convergence to zero, per unit size
            active &= ~((carry < 0.0) & (HALF_LIFE * np.abs(carry) > gain))

        chosen = np.flatnonzero(active)
        if chosen.size == 0:
            return {}

        # --- rank by strength of cointegration, cap reuse of any single symbol -------
        chosen = chosen[np.argsort(tstat[chosen], kind="stable")]
        used: dict[int, int] = {}
        held = []
        for p in chosen:
            a, b = int(dep_i[p]), int(ind_i[p])
            if used.get(a, 0) >= M_MAX or used.get(b, 0) >= M_MAX:
                continue
            used[a] = used.get(a, 0) + 1
            used[b] = used.get(b, 0) + 1
            held.append(int(p))
            if len(held) >= N_PAIRS:
                break
        if not held:
            return {}

        # --- equal gross per pair, beta-weighted legs --------------------------------
        per_pair = GROSS / len(held)
        raw: dict[str, float] = {}
        for p in held:
            b = float(beta[p])
            size = per_pair / (1.0 + b)
            s = float(side[p])
            dep_sym = symbols[int(dep_i[p])]
            ind_sym = symbols[int(ind_i[p])]
            raw[dep_sym] = raw.get(dep_sym, 0.0) + s * size
            raw[ind_sym] = raw.get(ind_sym, 0.0) - s * size * b

        return _apply_caps(raw)


def build_strategy() -> CointegrationConvergence:
    return CointegrationConvergence()
