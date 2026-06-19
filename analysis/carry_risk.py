"""CARRY ITERATION — EXPLORATION-002: cut the -37% maxDD of the WALK-FORWARD carry baseline.

The bias-free walk-forward baseline (carry_walkforward.walkforward_book) is net IS=+1.15,
OOS=+0.96, fullDD=-37%, oosDD=-33%, positive every year. The DD is the short-SQUEEZE PRICE tail:
the short leg of high-funding coins squeezing UP. Funding-only is smooth (DD ~0); the price leg
causes the tail. This module designs IS-calibrated, PAST-ONLY, walk-forward-compatible DD controls,
applies them to the ACTUAL baseline book (weights + price/funding/cost decomposition stitched
per-month by the walk-forward), and reports IS/OOS Sharpe + full/OOS maxDD for each.

PRIOR DD FINDINGS (analysis/carry_dd.py) — built on, not repeated:
  - VOL-TARGET (continuous target/trailing_vol scaling): USELESS — squeezes are NOT vol-predictable.
  - DD-BRAKE (de-lever after drawdown): MODEST (-32% -> -26%); tuned here.
  - NO-MAGNETS (exclude extreme-funding coins): BACKFIRES — extreme funding IS the edge. NOT used.
  - WIDER FRAC: helps OOS DD; already in the walk-forward combo grid -> absorbed in the baseline.

OVERLAY FAMILIES (all PAST-ONLY; weight-level overlays REBUILD net from re-weighted legs so price,
funding AND cost all reflect the new exposures):
  (a) PER-COIN WEIGHT CAP — clip |w_i| at a per-name ceiling, renormalize each leg back to gross
      neutrality. Directly limits any single short from blowing up the book in a squeeze.
  (b) INVERSE-VOL (risk-parity-ish) SIZING — within each leg, weight coins by 1/trailing_vol (vol
      <= t-1). Crowded-funding names that are ALSO high-vol (squeeze-prone) get less weight.
  (c) DD-BRAKE — scalar exposure cut to a floor while running drawdown (realized <= t-1) exceeds a
      threshold; IS-grid-tuned (thresh x floor).
  (d) BETA-HEDGE the residual short-leg beta to BTC/ETH — past-only rolling beta of book net to a
      50/50 BTC/ETH market return; subtract beta*market each candle (hedge return net of its own
      cost). Tests the alt-season / market-beta hypothesis for the squeezes.
  (e) GROSS-VOL CEILING — scale exposure DOWN only when trailing book vol (vol <= t-1) exceeds an
      IS-calibrated ceiling (a one-sided cap, not the symmetric vol-target that failed); never
      levers up. Distinct from (c): vol-trigger vs drawdown-trigger.

All thresholds/targets are calibrated on IS rows only (index < pe.OOS_CUTOFF). OOS is revealed once.
Leak-safe: every overlay's exposure/weight at candle t uses data strictly <= t-1 (or, for weight
caps / inverse-vol, the SAME past-only signal the book already used at t -> no new look-ahead).
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "analysis")
import broad_carry as bc  # noqa: E402
import carry_walkforward as cw  # noqa: E402
import pair_engine as pe  # noqa: E402

LO0 = pd.Timestamp("2000-01-01")
HI1 = pd.Timestamp("2100-01-01")
COST_SIDE = pe.COST_SIDE


# --------------------------------------------------------------------------------------------------
# stats / reporting
# --------------------------------------------------------------------------------------------------
def stats(net: pd.Series) -> dict:
    net = net.dropna()
    eq = (1 + net).cumprod()
    is_net = net[net.index < pe.OOS_CUTOFF]
    oos_net = net[net.index >= pe.OOS_CUTOFF]
    is_eq = (1 + is_net).cumprod()
    oos_eq = (1 + oos_net).cumprod()
    return {
        "is_sh": pe.monthly_sharpe(net, LO0, pe.OOS_CUTOFF),
        "oos_sh": pe.monthly_sharpe(net, pe.OOS_CUTOFF, HI1),
        "dd": float((eq / eq.cummax() - 1).min()),
        "is_dd": float((is_eq / is_eq.cummax() - 1).min()) if len(is_eq) else float("nan"),
        "oos_dd": float((oos_eq / oos_eq.cummax() - 1).min()) if len(oos_eq) else float("nan"),
    }


def line(name: str, net: pd.Series) -> dict:
    s = stats(net)
    print(f"  {name:34} IS={s['is_sh']:+.2f} OOS={s['oos_sh']:+.2f} | "
          f"maxDD full={s['dd']*100:5.0f}% IS={s['is_dd']*100:5.0f}% OOS={s['oos_dd']*100:5.0f}%")
    return s


# --------------------------------------------------------------------------------------------------
# market (BTC/ETH) hold-candle return on the realistic grid — for beta-hedge
# --------------------------------------------------------------------------------------------------
def market_return(coins: dict, index: pd.DatetimeIndex) -> pd.Series:
    """50/50 BTC/ETH next-bar-open hold return aligned to the book's HOLD-candle index.

    The book's row at hold-candle t+1 (open_time t+1) earns price return open[t+2]/open[t+1]-1. We
    build the same quantity for a 50/50 BTC/ETH portfolio so a rolling beta can hedge it out. All
    past-only relative to its own row (it is the SAME hold candle as the book leg)."""
    mkt = {}
    for s in ("BTCUSDT", "ETHUSDT"):
        d = coins.get(s)
        if d is None:
            continue
        o = d["open"]
        # SAME convention as build_book: row at open_time T holds open[T+2]/open[T+1]-1, labelled T.
        r = o.shift(-2) / o.shift(-1) - 1.0
        r.index = pd.to_datetime(o.index, unit="ms")
        mkt[s] = r
    out = pd.DataFrame(mkt).mean(axis=1)
    return out.reindex(index)


# --------------------------------------------------------------------------------------------------
# (c) DD-BRAKE — scalar exposure cut after drawdown (past-only, realized equity <= t-1)
# --------------------------------------------------------------------------------------------------
def dd_brake(net: pd.Series, dd_thresh: float = 0.15, floor: float = 0.3) -> pd.Series:
    vals = net.to_numpy()
    exp = np.ones(len(vals))
    eq = 1.0
    peak = 1.0
    for t in range(len(vals)):
        dd = eq / peak - 1.0 if peak > 0 else 0.0
        exp[t] = floor if dd < -dd_thresh else 1.0
        eq *= (1.0 + exp[t] * vals[t])
        peak = max(peak, eq)
    return pd.Series(exp * vals, index=net.index)


# --------------------------------------------------------------------------------------------------
# (e) GROSS-VOL CEILING — one-sided de-lever when trailing book vol exceeds an IS ceiling
# --------------------------------------------------------------------------------------------------
def vol_ceiling(net: pd.Series, win: int = 90, pctl: float = 0.75,
                floor: float = 0.4) -> pd.Series:
    """Scale exposure to ceiling/trailing_vol, clipped to [floor, 1] — NEVER levers above 1 (unlike
    the symmetric vol-target that failed). ceiling = IS pctl of trailing vol; past-only."""
    rv = net.rolling(win).std().shift(1)
    ceil = rv[net.index < pe.OOS_CUTOFF].quantile(pctl)        # IS-only ceiling
    exposure = (ceil / rv).clip(floor, 1.0).fillna(1.0)
    return exposure * net


# --------------------------------------------------------------------------------------------------
# weight-level overlays — rebuild net from re-weighted legs (price/funding/cost all change)
# --------------------------------------------------------------------------------------------------
def _net_from_weights(coins: dict, w: pd.DataFrame, cost_side: float = COST_SIDE) -> pd.Series:
    """Rebuild the realistic net (price + funding - cost) from an arbitrary weight matrix w whose
    index is HOLD-candle open_time and columns are coins. Mirrors broad_carry.build_book exactly:
    price = sum_i w_i * ret_i ; funding = -sum_i w_i * fund_earn_i ; cost = cost_side * |Δw|.

    ret_i / fund_earn_i are rebuilt on the FULL coin grid then aligned to w's index, so this works
    for ANY re-weighting (caps, inverse-vol, hedged book)."""
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).sort_index()
    funds = pd.DataFrame({s: d["funding_rate"] for s, d in coins.items()}).reindex(opens.index)
    ret = opens.shift(-2) / opens.shift(-1) - 1.0
    fund_earn = funds.shift(-1)
    ret.index = pd.to_datetime(opens.index, unit="ms")
    fund_earn.index = pd.to_datetime(opens.index, unit="ms")
    ret = ret.reindex(w.index)[w.columns]
    fund_earn = fund_earn.reindex(w.index)[w.columns]
    price = (w * ret).sum(axis=1)
    funding = -(w * fund_earn).sum(axis=1)
    cost = cost_side * (w - w.shift(1)).abs().sum(axis=1)
    return (price + funding - cost).rename("net")


def cap_weights(w: pd.DataFrame, cap: float) -> pd.DataFrame:
    """(a) Per-coin weight cap: clip |w_i| to `cap`, then renormalize EACH leg to gross 1 so the
    book stays dollar-neutral with the same gross. Past-only (operates on the book's own weights, no
    new data). If a leg's gross is already under the cap the clip is inert; otherwise mass moves off
    the largest names onto the rest of that leg — squeeze concentration is bounded by `cap`."""
    wv = w.to_numpy().copy()
    out = np.zeros_like(wv)
    for i in range(wv.shape[0]):
        row = wv[i]
        longs = np.where(row > 0)[0]
        shorts = np.where(row < 0)[0]
        for leg, sign in ((longs, 1.0), (shorts, -1.0)):
            if len(leg) == 0:
                continue
            mag = np.abs(row[leg])
            gross = mag.sum()
            if gross <= 0:
                continue
            target = mag / gross                          # normalized leg weights (sum 1)
            # iterative water-filling: cap then redistribute the spill to uncapped names
            for _ in range(20):
                over = target > cap
                if not over.any():
                    break
                spill = (target[over] - cap).sum()
                target[over] = cap
                room = ~over
                if not room.any() or target[room].sum() <= 0:
                    break
                target[room] += spill * target[room] / target[room].sum()
            out[i, leg] = sign * target
    return pd.DataFrame(out, index=w.index, columns=w.columns)


def inverse_vol_weights(coins: dict, w: pd.DataFrame, win: int = 30) -> pd.DataFrame:
    """(b) Inverse-vol sizing WITHIN each leg: keep the book's long/short SET (the carry signal) but
    weight each name by 1/trailing_vol (vol over `win` 8h candles, <= t-1 so past-only),
    renormalized to gross 1 per leg. Down-weights squeeze-prone (high-vol) names; keeps dir."""
    opens = pd.DataFrame({s: d["open"] for s, d in coins.items()}).sort_index()
    ret = opens / opens.shift(1) - 1.0
    vol = ret.rolling(win).std().shift(1)                 # vol <= t-1
    vol.index = pd.to_datetime(opens.index, unit="ms")
    vol = vol.reindex(w.index)[w.columns]
    inv = 1.0 / vol.replace(0.0, np.nan)
    wv = w.to_numpy()
    iv = inv.to_numpy()
    out = np.zeros_like(wv)
    for i in range(wv.shape[0]):
        row = wv[i]
        ivr = iv[i]
        for sign in (1.0, -1.0):
            leg = np.where(np.sign(row) == sign)[0]
            if len(leg) == 0:
                continue
            wgt = ivr[leg]
            # fall back to equal-weight where vol is missing
            bad = ~np.isfinite(wgt) | (wgt <= 0)
            if bad.all():
                wgt = np.ones(len(leg))
            else:
                wgt = np.where(bad, np.nanmedian(wgt[~bad]), wgt)
            wgt = wgt / wgt.sum()
            out[i, leg] = sign * wgt
    return pd.DataFrame(out, index=w.index, columns=w.columns)


def beta_hedge(net: pd.Series, mkt: pd.Series, win: int = 90,
               cost_side: float = COST_SIDE) -> pd.Series:
    """(d) Hedge the book's residual market beta to a 50/50 BTC/ETH return. beta_t = rolling cov/var
    over `win` candles using returns <= t-1 (past-only). Hedge return = -beta_t * mkt_t; charge a
    cost on the CHANGE in hedge notional |Δbeta| * mkt-leg turnover (one extra leg per beta change).
    If the squeezes are an alt-season/market-beta effect, neutralizing beta should clip the tail."""
    df = pd.DataFrame({"net": net, "mkt": mkt}).dropna()
    cov = df["net"].rolling(win).cov(df["mkt"]).shift(1)
    var = df["mkt"].rolling(win).var().shift(1)
    beta = (cov / var).clip(-2.0, 2.0).fillna(0.0)
    hedge_ret = -beta * df["mkt"]
    hedge_cost = cost_side * beta.diff().abs().fillna(0.0)
    hedged = df["net"] + hedge_ret - hedge_cost
    return hedged.reindex(net.index)


# --------------------------------------------------------------------------------------------------
# IS-only grid tuning helpers (calibrate -> then reveal OOS once)
# --------------------------------------------------------------------------------------------------
def _is_score(net: pd.Series) -> tuple[float, float]:
    """IS Sharpe and IS maxDD (for grid selection — OOS NEVER touched here)."""
    is_net = net[net.index < pe.OOS_CUTOFF].dropna()
    if len(is_net) < 30:
        return float("-inf"), 0.0
    eq = (1 + is_net).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    return pe.monthly_sharpe(is_net, LO0, pe.OOS_CUTOFF), dd


def tune_dd_brake(net: pd.Series) -> tuple[float, float]:
    """Pick (thresh, floor) maximizing IS Sharpe/|IS DD| ratio (DD-efficiency) on IS rows only."""
    best, best_key = float("-inf"), (0.15, 0.3)
    for thr in (0.08, 0.10, 0.12, 0.15, 0.20):
        for fl in (0.0, 0.2, 0.3, 0.5):
            sh, dd = _is_score(dd_brake(net, thr, fl))
            score = sh / abs(dd) if dd < 0 else sh
            if score > best:
                best, best_key = score, (thr, fl)
    return best_key


def tune_cap(coins: dict, w: pd.DataFrame) -> float:
    """Pick the per-coin cap maximizing IS Sharpe/|IS DD| on IS rows only."""
    best, best_cap = float("-inf"), 0.10
    for cap in (0.04, 0.06, 0.08, 0.10, 0.15, 0.20):
        net = _net_from_weights(coins, cap_weights(w, cap))
        sh, dd = _is_score(net)
        score = sh / abs(dd) if dd < 0 else sh
        if score > best:
            best, best_cap = score, cap
    return best_cap


# --------------------------------------------------------------------------------------------------
def main() -> None:
    print("Loading universe + building the WALK-FORWARD baseline book (this takes a minute)...")
    coins = bc.load_universe()
    base, parts = cw.walkforward_book(coins)
    w = parts["weights"]
    mkt = market_return(coins, base.index)

    print("\n=== EXPLORATION-002: DD controls on the WALK-FORWARD carry baseline ===")
    print("(weight-level overlays rebuild net from re-weighted legs; cost tracks new exposures)\n")
    results: dict[str, dict] = {}
    results["baseline (walk-forward)"] = line("baseline (walk-forward)", base)

    # sanity: rebuilding net from the baseline weights must reproduce base (no hidden leak/bug)
    recon = _net_from_weights(coins, w)
    rec_diff = float((recon.reindex(base.index) - base).abs().max())
    print(f"  [sanity] net rebuilt from baseline weights: maxdiff vs baseline = {rec_diff:.2e}\n")

    # (a) per-coin weight cap — IS-tuned
    cap = tune_cap(coins, w)
    cap_net = _net_from_weights(coins, cap_weights(w, cap))
    results[f"(a) per-coin cap={cap:.2f}"] = line(f"(a) per-coin cap (IS-tuned={cap:.2f})", cap_net)

    # (b) inverse-vol sizing within each leg
    iv_net = _net_from_weights(coins, inverse_vol_weights(coins, w, win=30))
    results["(b) inverse-vol (win=30)"] = line("(b) inverse-vol sizing (win=30)", iv_net)

    # (c) dd-brake — IS-tuned
    thr, fl = tune_dd_brake(base)
    brake_net = dd_brake(base, thr, fl)
    results[f"(c) dd-brake t={thr:.2f},f={fl:.1f}"] = line(
        f"(c) dd-brake (IS-tuned {thr:.0%}/floor{fl:.1f})", brake_net)

    # (d) beta-hedge to BTC/ETH
    hedge_net = beta_hedge(base, mkt, win=90)
    results["(d) beta-hedge BTC/ETH"] = line("(d) beta-hedge BTC/ETH (win=90)", hedge_net)

    # (e) gross-vol ceiling — IS-calibrated one-sided cap
    vc_net = vol_ceiling(base, win=90, pctl=0.75, floor=0.4)
    results["(e) vol-ceiling (p75)"] = line("(e) vol-ceiling (IS p75, floor0.4)", vc_net)

    # --- COMPOSITES: the mechanism-aligned stack (cap the single-name tail + brake the book) ---
    print("\n  --- composites (compose the past-only overlays) ---")
    cap_w = cap_weights(w, cap)
    cap_brake = dd_brake(_net_from_weights(coins, cap_w), thr, fl)
    results[f"cap{cap:.2f}+brake"] = line(f"(a)+(c) cap{cap:.2f} + dd-brake", cap_brake)

    iv_cap_w = cap_weights(inverse_vol_weights(coins, w, win=30), cap)
    iv_cap = _net_from_weights(coins, iv_cap_w)
    results["invvol+cap"] = line("(b)+(a) inverse-vol + cap", iv_cap)

    iv_cap_brake = dd_brake(iv_cap, thr, fl)
    results["invvol+cap+brake"] = line("(b)+(a)+(c) inverse-vol + cap + brake", iv_cap_brake)

    cap_hedge = beta_hedge(_net_from_weights(coins, cap_w), mkt, win=90)
    results["cap+beta-hedge"] = line("(a)+(d) cap + beta-hedge", cap_hedge)

    # --- recommendation: best DD reduction that KEEPS OOS Sharpe clearly positive ---
    print("\n=== RECOMMENDATION ===")
    b = results["baseline (walk-forward)"]
    cand = [(k, v) for k, v in results.items()
            if k != "baseline (walk-forward)" and v["oos_sh"] > 0.5
            and v["dd"] > b["dd"]]                          # less negative DD than baseline
    if cand:
        # rank by DD improvement, tie-break on OOS Sharpe retention
        cand.sort(key=lambda kv: (kv[1]["dd"], kv[1]["oos_sh"]), reverse=True)
        name, v = cand[0]
        print(f"  BEST: {name}")
        print(f"    fullDD {b['dd']*100:.0f}% -> {v['dd']*100:.0f}%  "
              f"(OOS DD {b['oos_dd']*100:.0f}% -> {v['oos_dd']*100:.0f}%)")
        print(f"    OOS Sharpe {b['oos_sh']:+.2f} -> {v['oos_sh']:+.2f}  "
              f"(IS {b['is_sh']:+.2f} -> {v['is_sh']:+.2f})")
    else:
        print("  No overlay cut DD while keeping OOS Sharpe > 0.5 — baseline stands.")


if __name__ == "__main__":
    main()
