"""CARRY ENHANCEMENT — shared harness (EXPLORATION; IS-only by construction here).

A single generalized broad-carry book builder that all carry_enh_* prototypes call. It is a strict
superset of broad_carry.build_book: same realistic conventions (signal <= close[t], fill open[t+1],
hold candle t+1, real 8h funding, 0.07%/side cost), same eligibility, same dollar-neutral equal-leg
construction — but with PLUGGABLE per-row scoring + per-row short-leg gating so each enhancement is
ONE orthogonal change vs the baseline.

  - rank_signal: the cross-sectional score each row is ranked by (default: trailing-mean funding,
    EXACTLY the baseline). short = top-FRAC (highest score), long = bottom-FRAC (lowest score).
  - short_guard: an optional per-(row,coin) boolean MASK of squeeze-prone names to DROP from the
    SHORT-leg candidate pool only (long leg untouched) — the squeeze-avoidance axis.
  - short_demote_score / short_keep_frac: alternatively, re-rank the short-leg pool by a SECOND
    signal and keep only the safest keep_frac of the top-FRAC pool (soft squeeze avoidance).

EVERYTHING past-only. The short-leg drag (-53.5% IS price) is the target; the long leg (+309% IS)
must be preserved, so guards/re-ranks touch ONLY the short candidate set.

Decomposition helper splits net into LONG-leg vs SHORT-leg price + funding so every claim is backed.
All selection/scoring is IS-ONLY by gauntlet rule; OOS is revealed only at CONFIRMATION.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
M_FUND = 9
FRAC = 0.25
MIN_HISTORY = 1095   # the most-picked walk-forward combo (~1y point-in-time listing age)


def panels(coins: dict) -> dict[str, pd.DataFrame]:
    """All the per-coin aligned panels the enhancements need (open/funding/quote_vol/taker)."""
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).sort_index()
    idx = opens.index

    def panel(col: str) -> pd.DataFrame:
        df = pd.DataFrame({s: d[col] for s, d in coins.items() if col in d}).reindex(idx)
        return df.apply(pd.to_numeric, errors="coerce")

    return {
        "open": opens.apply(pd.to_numeric, errors="coerce"),
        "high": panel("high"),
        "low": panel("low"),
        "close": panel("close"),
        "funding": panel("funding_rate"),
        "quote_volume": panel("quote_volume"),
        "taker_buy_quote": panel("taker_buy_quote_volume"),
    }


def base_eligibility(pan: dict, m_fund: int, min_history: int | None) -> tuple:
    """Returns (ftrail, ret, fund_earn, elig) — the baseline eligibility EXACTLY as broad_carry."""
    opens, funds = pan["open"], pan["funding"]
    ftrail = funds.rolling(m_fund).mean()              # signal <= t (past-only)
    ret = opens.shift(-2) / opens.shift(-1) - 1.0      # hold candle t+1 (future of decision)
    fund_earn = funds.shift(-1)                         # funding settled over candle t+1
    elig = ftrail.notna() & ret.notna() & fund_earn.notna()
    if min_history is not None:
        hist = opens.notna().cumsum().shift(1)
        elig = elig & (hist >= min_history)
    return ftrail, ret, fund_earn, elig


def build_enh(
    coins: dict,
    pan: dict | None = None,
    m_fund: int = M_FUND,
    frac: float = FRAC,
    min_history: int | None = MIN_HISTORY,
    cost_side: float = pe.COST_SIDE,
    rank_signal: pd.DataFrame | None = None,
    short_guard: pd.DataFrame | None = None,
    short_demote_score: pd.DataFrame | None = None,
    short_keep_frac: float = 1.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generalized realistic broad carry. Returns (book, weights). book has the standard net/price/
    funding/cost PLUS long_price/short_price/long_funding/short_funding leg decomposition columns.

    rank_signal: cross-sectional score to rank by (default = trailing-mean funding = baseline).
    short_guard: True at (row,coin) => DROP that coin from the SHORT pool (long leg untouched).
    short_demote_score: re-rank the top-FRAC short pool by this score (ascending = safest first),
        keep only the safest short_keep_frac of it -> soft squeeze avoidance (long untouched).
    """
    if pan is None:
        pan = panels(coins)
    opens = pan["open"]
    ftrail, ret, fund_earn, elig = base_eligibility(pan, m_fund, min_history)
    score = ftrail if rank_signal is None else rank_signal.reindex_like(ftrail)

    sc_np = score.to_numpy(dtype=float)
    el_np = (elig & score.notna()).to_numpy()
    guard_np = short_guard.reindex_like(ftrail).to_numpy() if short_guard is not None else None
    demote_np = (short_demote_score.reindex_like(ftrail).to_numpy()
                 if short_demote_score is not None else None)

    n_rows, n_cols = sc_np.shape
    w = np.zeros_like(sc_np)
    ls = np.zeros((n_rows, n_cols))   # +1 long / -1 short membership for leg decomposition
    for i in range(n_rows):
        ecols = np.where(el_np[i])[0]
        if len(ecols) < 4:
            continue
        order = ecols[np.argsort(sc_np[i, ecols])]   # ascending score
        k = int(len(ecols) * frac)
        if k < 1:
            continue
        longs = order[:k]
        short_pool = order[-k:]                        # highest-score names = baseline short pool
        if guard_np is not None:
            keep = ~np.nan_to_num(guard_np[i, short_pool], nan=False).astype(bool)
            short_pool = short_pool[keep]
        if demote_np is not None and len(short_pool) > 0 and short_keep_frac < 1.0:
            safe_order = short_pool[np.argsort(demote_np[i, short_pool])]  # ascending = safest
            n_keep = max(1, int(len(safe_order) * short_keep_frac))
            short_pool = safe_order[:n_keep]
        if len(longs) < 1 or len(short_pool) < 1:
            continue
        w[i, longs] = 1.0 / len(longs)
        w[i, short_pool] = -1.0 / len(short_pool)
        ls[i, longs] = 1.0
        ls[i, short_pool] = -1.0

    wdf = pd.DataFrame(w, index=opens.index, columns=opens.columns)
    ret_np = ret.to_numpy(dtype=float)
    fe_np = fund_earn.to_numpy(dtype=float)
    price = (w * np.nan_to_num(ret_np)).sum(axis=1)
    funding = -(w * np.nan_to_num(fe_np)).sum(axis=1)
    cost = cost_side * np.abs(w - np.vstack([np.zeros(n_cols), w[:-1]])).sum(axis=1)

    long_mask = (ls > 0)
    short_mask = (ls < 0)
    long_price = (np.where(long_mask, w, 0) * np.nan_to_num(ret_np)).sum(axis=1)
    short_price = (np.where(short_mask, w, 0) * np.nan_to_num(ret_np)).sum(axis=1)
    long_funding = -(np.where(long_mask, w, 0) * np.nan_to_num(fe_np)).sum(axis=1)
    short_funding = -(np.where(short_mask, w, 0) * np.nan_to_num(fe_np)).sum(axis=1)

    idx = pd.to_datetime(opens.index, unit="ms")
    book = pd.DataFrame(
        {"net": price + funding - cost, "price": price, "funding": funding, "cost": cost,
         "long_price": long_price, "short_price": short_price,
         "long_funding": long_funding, "short_funding": short_funding},
        index=idx,
    )
    wdf.index = idx
    # keep zero-weight rows as net=0 (matches broad_carry's monthly-Sharpe denominator exactly);
    # only drop rows where the realized PnL itself is undefined (NaN ret/funding outside positions).
    return book.dropna(subset=["net"]), wdf.loc[book.dropna(subset=["net"]).index]


def is_msharpe(s: pd.Series) -> float:
    return pe.monthly_sharpe(s, LO0, pe.OOS_CUTOFF)


def is_total(s: pd.Series) -> float:
    return float(s[s.index < pe.OOS_CUTOFF].sum())


def is_maxdd(net: pd.Series) -> float:
    x = net[net.index < pe.OOS_CUTOFF]
    eq = (1 + x).cumprod()
    return float((eq / eq.cummax() - 1).min())


def is_funding_t(book: pd.DataFrame) -> float:
    """Non-overlapping monthly funding-income t-stat (gauntlet check 3), IS-only."""
    f = book["funding"]
    f = f[f.index < pe.OOS_CUTOFF]
    g = f.groupby(f.index.to_period("M")).sum()
    return float(g.mean() / (g.std() / np.sqrt(len(g)))) if len(g) > 1 else float("nan")


def is_report(label: str, book: pd.DataFrame, w: pd.DataFrame) -> dict:
    """IS-ONLY summary + the load-bearing leg decomposition. NEVER touches OOS."""
    net = book["net"]
    r = {
        "label": label,
        "is_net_sh": is_msharpe(net),
        "is_net_total": is_total(net),
        "is_maxdd": is_maxdd(net),
        "is_fund_sh": is_msharpe(book["funding"]),
        "is_fund_t": is_funding_t(book),
        "is_long_price": is_total(book["long_price"]),
        "is_short_price": is_total(book["short_price"]),
        "is_long_fund": is_total(book["long_funding"]),
        "is_short_fund": is_total(book["short_funding"]),
        "is_turnover": float(w[w.index < pe.OOS_CUTOFF].diff().abs().sum(axis=1).mean()),
        "n_is": int((net.index < pe.OOS_CUTOFF).sum()),
    }
    return r


def print_report(r: dict) -> None:
    print(f"  [{r['label']}]")
    print(f"    IS net Sharpe={r['is_net_sh']:+.2f}  IS net total={r['is_net_total']*100:+.0f}%  "
          f"IS maxDD={r['is_maxdd']*100:.0f}%")
    print(f"    IS funding Sharpe={r['is_fund_sh']:+.2f} (monthly t={r['is_fund_t']:+.2f})  "
          f"turnover={r['is_turnover']:.2f}")
    print(f"    IS price decomp:  LONG={r['is_long_price']*100:+.0f}%  "
          f"SHORT={r['is_short_price']*100:+.0f}%   "
          f"fund decomp: LONG={r['is_long_fund']*100:+.0f}% SHORT={r['is_short_fund']*100:+.0f}%")


def signal_funding_z(pan: dict, m_fund: int = M_FUND, z_win: int = 90) -> pd.DataFrame:
    """Funding z-score: (trailing-mean funding - its rolling mean) / rolling std. Past-only.
    High z = funding ELEVATED vs the coin's own recent history (acute crowding spike)."""
    ftrail = pan["funding"].rolling(m_fund).mean()
    mu = ftrail.rolling(z_win).mean()
    sd = ftrail.rolling(z_win).std()
    return (ftrail - mu) / sd


def signal_funding_persistence(pan: dict, m_fund: int = M_FUND, win: int = 90) -> pd.DataFrame:
    """Funding PERSISTENCE = (trailing-mean funding) * (fraction of past `win` candles funding had
    the SAME sign as the trailing mean). Past-only. Rewards stable, durable crowding over spikes."""
    funds = pan["funding"]
    ftrail = funds.rolling(m_fund).mean()
    same_sign = (np.sign(funds) == np.sign(ftrail)).astype(float)
    frac_same = same_sign.rolling(win).mean()
    return ftrail * frac_same


def signal_squeeze_momentum(pan: dict, win: int = 9) -> pd.DataFrame:
    """Recent realized price momentum over `win` candles (~3d at win=9), past-only via close[t].
    HIGH = the coin is already running up = squeeze-in-progress = dangerous to short."""
    close = pan["close"]
    return close / close.shift(win) - 1.0


def signal_taker_imbalance(pan: dict, win: int = 9) -> pd.DataFrame:
    """Trailing taker-BUY share = taker_buy_quote / quote_volume, smoothed over `win`. Past-only.
    HIGH = aggressive buyers dominating = late crowded longs piling in = short-squeeze fuel."""
    tb = pan["taker_buy_quote"]
    qv = pan["quote_volume"]
    share = (tb / qv).clip(0, 1)
    return share.rolling(win).mean()
