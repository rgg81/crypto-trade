"""iter-v1/084 — REFORMED symbol-selection EDA (batch: GALA, CHZ, AXS, CRV).

Reform mandate (USER DIRECTIVE 2026-06-09 "option 3"):
  The EMPIRICAL predictor of ML edge headroom is the TRIVIAL TS-MOMENTUM
  BASELINE, computed IS-ONLY (klines strictly before OOS_CUTOFF 2025-03-24).
  A NEGATIVE trivial baseline = ML has room to add edge (DOT/063, AAVE/078).
  A POSITIVE trivial baseline = the symbol already trends cleanly and ML just
  adds noise (the FIL/083 trap: trivial +1.45 -> ML -0.82).

REFORMED SELECTION RULE: prefer the MOST NEGATIVE min-across-horizons trivial
Sharpe with >=4y data.

IS-ONLY DISCIPLINE: only klines with open_time < CUTOFF_MS are read for the
baseline. An explicit assertion guards against OOS leakage.

Methodology (LOCKED downstream): 50 seeds x 30 trials x specialist_mode x
LightGBM x max_depth=5 x num_leaves=31 — not exercised here; this is EDA only.

Reproducible: a colleague running
`python analysis/iteration_v1-084/eda_gala_chz_axs_crv.py` from the worktree
root gets identical numbers.
"""

import csv
import datetime
import math

CUTOFF_MS = datetime.datetime(2025, 3, 24).timestamp() * 1000  # OOS_CUTOFF_DATE
FEE = 0.0005          # 0.05% per side (Binance futures taker)
BARS_PER_DAY = 3      # 8h cadence
ANN = math.sqrt(365.0)  # daily-equivalent annualization

HORIZONS = {"5d": 15, "21d": 63, "50d": 150}  # bars at 8h
BATCH = ["GALAUSDT", "CHZUSDT", "AXSUSDT", "CRVUSDT"]


def load_is(sym):
    with open(f"data/{sym}/8h.csv") as f:
        rows = list(csv.reader(f))[1:]
    is_rows = [r for r in rows if int(r[0]) < CUTOFF_MS]
    assert all(int(r[0]) < CUTOFF_MS for r in is_rows), f"OOS LEAK in {sym}"
    times = [int(r[0]) for r in is_rows]
    closes = [float(r[4]) for r in is_rows]
    highs = [float(r[2]) for r in is_rows]
    lows = [float(r[3]) for r in is_rows]
    return times, closes, highs, lows


def sharpe_from_bar_pnl(pnl):
    daily = [sum(pnl[i:i + BARS_PER_DAY]) for i in range(0, len(pnl), BARS_PER_DAY)]
    if len(daily) < 2:
        return float("nan")
    m = sum(daily) / len(daily)
    v = sum((x - m) ** 2 for x in daily) / (len(daily) - 1)
    sd = math.sqrt(v)
    return (m / sd) * ANN if sd > 0 else 0.0


def trivial_sharpe(closes, N):
    n = len(closes)
    pnl = []
    prev_pos = 0
    for t in range(N, n - 1):
        mom = closes[t] / closes[t - N] - 1
        pos = 1 if mom > 0 else (-1 if mom < 0 else 0)
        fwd = closes[t + 1] / closes[t] - 1
        fee = FEE * abs(pos - prev_pos)
        pnl.append(pos * fwd - fee)
        prev_pos = pos
    return sharpe_from_bar_pnl(pnl)


def natr30_p50(closes, highs, lows):
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]),
                 abs(lows[i] - closes[i - 1]))
        trs.append(tr / closes[i] * 100 if closes[i] > 0 else 0.0)
    win = 30
    natrs = sorted(sum(trs[i - win:i]) / win for i in range(win, len(trs)))
    return natrs[len(natrs) // 2] if natrs else float("nan")


def regime_split_21d(closes):
    N = 63
    n = len(closes)
    reg = {"bull": [], "bear": [], "chop": []}
    prev_pos = 0
    for t in range(N, n - 1):
        mom = closes[t] / closes[t - N] - 1
        pos = 1 if mom > 0 else (-1 if mom < 0 else 0)
        fwd = closes[t + 1] / closes[t] - 1
        fee = FEE * abs(pos - prev_pos)
        p = pos * fwd - fee
        prev_pos = pos
        r = closes[t] / closes[t - N] - 1
        lab = "bull" if r > 0.05 else ("bear" if r < -0.05 else "chop")
        reg[lab].append(p)
    return {k: (sharpe_from_bar_pnl(v), len(v)) for k, v in reg.items()}


def verdict(min_sharpe, data_years):
    if data_years < 4:
        return "NONE"
    if min_sharpe < -0.30:
        return "HIGH"
    if min_sharpe <= 0.20:
        return "MEDIUM"
    if min_sharpe <= 0.80:
        return "LOW"
    return "NONE"  # > +0.80 = strong trivial trend, the FIL trap


def main():
    print("symbol,data_years,IS_years,IS_bars,triv_5d,triv_21d,triv_50d,"
          "min_horizon,natr30_p50,bull_S,bear_S,chop_S,verdict")
    results = {}
    for sym in BATCH:
        with open(f"data/{sym}/8h.csv") as f:
            allrows = list(csv.reader(f))[1:]
        total_years = (int(allrows[-1][0]) - int(allrows[0][0])) / 1000 / 86400 / 365.25
        times, closes, highs, lows = load_is(sym)
        is_years = (times[-1] - times[0]) / 1000 / 86400 / 365.25
        s = {h: trivial_sharpe(closes, N) for h, N in HORIZONS.items()}
        mn = min(s.values())
        p50 = natr30_p50(closes, highs, lows)
        reg = regime_split_21d(closes)
        v = verdict(mn, total_years)
        results[sym] = dict(total_years=total_years, mn=mn, v=v)
        print(f"{sym},{total_years:.2f},{is_years:.2f},{len(closes)},"
              f"{s['5d']:+.3f},{s['21d']:+.3f},{s['50d']:+.3f},{mn:+.3f},"
              f"{p50:.3f},{reg['bull'][0]:+.3f},{reg['bear'][0]:+.3f},"
              f"{reg['chop'][0]:+.3f},{v}")

    eligible = {k: r for k, r in results.items()
                if r["total_years"] >= 4 and r["v"] in ("HIGH", "MEDIUM")}
    pool = eligible if eligible else {k: r for k, r in results.items()
                                      if r["total_years"] >= 4}
    best = min(pool, key=lambda k: pool[k]["mn"])
    print(f"\nBEST={best} min_horizon_sharpe={pool[best]['mn']:+.3f} "
          f"verdict={pool[best]['v']}")


if __name__ == "__main__":
    main()
