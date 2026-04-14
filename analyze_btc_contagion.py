"""Post-hoc BTC contagion circuit breaker feasibility (iter-v2/015).

Response to iter-v2/014's drawdown brake lineage closure. This
primitive bypasses XRP dominance because it fires symmetrically on
a cross-asset signal (BTC crash) rather than differentially on
per-symbol DD.

Loads iter-v2/005's OOS trade stream and BTC 8h klines. Computes
BTC rolling returns, flags contagion events, builds a kill-window
mask, and filters trades whose open_time falls in a kill window.
Reports aggregate and per-symbol metrics for each config.

Usage:
    uv run python analyze_btc_contagion.py

Outputs:
    reports-v2/iteration_v2-015_btc_contagion/
        summary.json           — per-config aggregate + per-symbol
        btc_rolling.csv        — BTC returns and trigger flags
        trigger_events.csv     — flagged events per config
        per_config_trades.csv  — braked trade stream per config
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

V2_REPORT = Path("reports-v2/iteration_v2-005")
BTC_DATA = Path("data/BTCUSDT/8h.csv")
OUT_DIR = Path("reports-v2/iteration_v2-015_btc_contagion")
EIGHT_HOURS_MS = 8 * 60 * 60 * 1000


@dataclass(frozen=True)
class ContagionConfig:
    name: str
    thresh_1bar_pct: float  # kill if 1-bar BTC return < this (e.g., -4.0)
    thresh_3bar_pct: float  # kill if 3-bar BTC return < this (e.g., -10.0)
    kill_bars: int  # kill window length in 8h bars following the trigger


CONFIGS: tuple[ContagionConfig, ...] = (
    ContagionConfig("none", thresh_1bar_pct=-9999.0, thresh_3bar_pct=-9999.0, kill_bars=0),
    ContagionConfig("A_tight_3_8_1d", thresh_1bar_pct=-3.0, thresh_3bar_pct=-8.0, kill_bars=3),
    ContagionConfig("B_mid_4_10_1d", thresh_1bar_pct=-4.0, thresh_3bar_pct=-10.0, kill_bars=3),
    ContagionConfig("C_loose_5_12_2d", thresh_1bar_pct=-5.0, thresh_3bar_pct=-12.0, kill_bars=6),
    ContagionConfig("D_mid_4_10_3d", thresh_1bar_pct=-4.0, thresh_3bar_pct=-10.0, kill_bars=9),
)


def _load_btc_klines() -> pd.DataFrame:
    """Load BTC 8h klines, compute 1-bar and 3-bar returns."""
    btc = pd.read_csv(BTC_DATA)
    btc = btc.sort_values("open_time").reset_index(drop=True)
    btc["ret_1bar_pct"] = (btc["close"] / btc["open"] - 1.0) * 100.0
    # 3-bar cumulative return: product of (1 + r_1bar) over 3 bars minus 1
    btc["ret_3bar_pct"] = (
        (1.0 + btc["ret_1bar_pct"] / 100.0).rolling(3).apply(lambda x: x.prod(), raw=True) - 1.0
    ) * 100.0
    return btc


def _build_kill_windows(btc: pd.DataFrame, cfg: ContagionConfig) -> tuple[np.ndarray, list[dict]]:
    """Return a boolean mask over BTC bars marking kill windows plus an event log.

    A contagion event fires on any bar where ret_1bar < thresh_1bar OR
    ret_3bar < thresh_3bar. The kill window covers that bar plus the
    next (kill_bars - 1) bars. Overlapping events extend the window.
    """
    n = len(btc)
    mask = np.zeros(n, dtype=bool)
    events: list[dict] = []
    if cfg.kill_bars <= 0:
        return mask, events

    for i in range(n):
        r1 = btc.iloc[i]["ret_1bar_pct"]
        r3 = btc.iloc[i]["ret_3bar_pct"]
        triggered_by = None
        if pd.notna(r1) and r1 < cfg.thresh_1bar_pct:
            triggered_by = "1bar"
        elif pd.notna(r3) and r3 < cfg.thresh_3bar_pct:
            triggered_by = "3bar"
        if triggered_by is None:
            continue
        end = min(i + cfg.kill_bars, n)
        mask[i:end] = True
        events.append(
            {
                "config": cfg.name,
                "trigger_bar_idx": i,
                "trigger_open_time": int(btc.iloc[i]["open_time"]),
                "trigger_date": pd.to_datetime(btc.iloc[i]["open_time"], unit="ms")
                .date()
                .isoformat(),
                "triggered_by": triggered_by,
                "ret_1bar_pct": round(float(r1) if pd.notna(r1) else 0.0, 3),
                "ret_3bar_pct": round(float(r3) if pd.notna(r3) else 0.0, 3),
                "kill_from_idx": i,
                "kill_to_idx": end - 1,
            }
        )
    return mask, events


def _apply_brake(trades: pd.DataFrame, btc: pd.DataFrame, mask: np.ndarray) -> pd.DataFrame:
    """Apply the kill mask to the trade stream.

    For each trade, find the BTC bar whose open_time is <= trade's
    open_time (the most recent BTC bar at trade entry). If that bar
    is in a kill window, zero out the trade's weighted_pnl and
    weight_factor.
    """
    trades = trades.sort_values("open_time").reset_index(drop=True).copy()
    btc_times = btc["open_time"].to_numpy(dtype=np.int64)

    killed = np.zeros(len(trades), dtype=bool)
    for i, t in trades.iterrows():
        # Locate the BTC bar active at or before trade open_time
        idx = int(np.searchsorted(btc_times, t["open_time"], side="right") - 1)
        if 0 <= idx < len(btc) and mask[idx]:
            killed[i] = True

    trades["is_killed"] = killed
    trades["effective_weighted_pnl"] = np.where(killed, 0.0, trades["weighted_pnl"])
    trades["effective_weight_factor"] = np.where(killed, 0.0, trades["weight_factor"])
    return trades


def _trade_level_sharpe(pnl: pd.Series) -> float:
    if len(pnl) < 2 or pnl.std() == 0:
        return 0.0
    return float(pnl.mean() / pnl.std() * np.sqrt(len(pnl)))


def _annualize_daily(daily_pnl: pd.Series, periods: int = 365) -> float:
    if len(daily_pnl) < 2 or daily_pnl.std() == 0:
        return 0.0
    return float(daily_pnl.mean() / daily_pnl.std() * np.sqrt(periods))


def _max_drawdown(equity: pd.Series) -> float:
    if len(equity) == 0:
        return 0.0
    rolling_max = equity.cummax()
    dd = (equity - rolling_max) / rolling_max.replace(0, np.nan)
    return float(dd.min() or 0.0)


def _summarize(trades: pd.DataFrame, pnl_col: str, label: str) -> dict:
    if len(trades) == 0:
        return {"label": label, "n": 0}

    trades = trades.copy()
    trades["date"] = pd.to_datetime(trades["close_time"], unit="ms").dt.date
    daily = trades.groupby("date")[pnl_col].sum()

    sharpe_daily = _annualize_daily(daily / 100.0)
    sharpe_trade = _trade_level_sharpe(trades[pnl_col])
    equity = (1.0 + daily / 100.0).cumprod()
    max_dd = _max_drawdown(equity)
    pnl = trades[pnl_col]
    wins = pnl[pnl > 0].sum()
    losses = abs(pnl[pnl < 0].sum() or 1)
    pf = float(wins / losses)
    total_pnl = float(pnl.sum())
    total_return = float((1.0 + daily / 100.0).prod() - 1.0)
    calmar = float(total_return / abs(max_dd)) if max_dd != 0 else 0.0

    # Per-symbol breakdown
    per_sym = trades.groupby("symbol")[pnl_col].sum().sort_values(ascending=False).to_dict()
    total = sum(per_sym.values())
    per_sym_pct = {
        sym: round(float(pnl / total * 100) if total != 0 else 0.0, 2)
        for sym, pnl in per_sym.items()
    }

    return {
        "label": label,
        "n_trades": int(len(trades)),
        "n_killed": int((trades[pnl_col] == 0).sum()) if pnl_col != "weighted_pnl" else 0,
        "win_rate": round(float((pnl > 0).mean() * 100), 2),
        "pf": round(pf, 4),
        "sharpe_trade": round(float(sharpe_trade), 4),
        "sharpe_daily_annualized": round(float(sharpe_daily), 4),
        "max_dd_pct": round(float(max_dd * 100), 2),
        "total_pnl_pct": round(total_pnl, 2),
        "calmar": round(calmar, 2),
        "per_sym_pnl": {k: round(float(v), 2) for k, v in per_sym.items()},
        "per_sym_share_pct": per_sym_pct,
    }


def main() -> None:
    print("=" * 70)
    print("BTC CONTAGION BRAKE FEASIBILITY — iter-v2/015")
    print("=" * 70)

    oos_path = V2_REPORT / "out_of_sample/trades.csv"
    if not oos_path.exists():
        print(f"ERROR: {oos_path} not found")
        return

    trades = pd.read_csv(oos_path)
    btc = _load_btc_klines()
    print(f"\nLoaded {len(trades)} v2 OOS trades")
    print(f"Loaded {len(btc)} BTC 8h klines")
    print(
        f"BTC date range: {pd.to_datetime(btc['open_time'].min(), unit='ms').date()} "
        f"→ {pd.to_datetime(btc['open_time'].max(), unit='ms').date()}"
    )
    print()

    # Slice BTC to trade-relevant window
    v2_start = int(trades["open_time"].min()) - 3 * EIGHT_HOURS_MS
    v2_end = int(trades["close_time"].max()) + EIGHT_HOURS_MS
    btc_oos = btc[(btc["open_time"] >= v2_start) & (btc["open_time"] <= v2_end)].reset_index(
        drop=True
    )
    print(f"BTC OOS-window slice: {len(btc_oos)} bars")
    print(
        f"BTC OOS 1-bar return stats: min={btc_oos['ret_1bar_pct'].min():.2f}% "
        f"max={btc_oos['ret_1bar_pct'].max():.2f}% "
        f"mean={btc_oos['ret_1bar_pct'].mean():.3f}% "
        f"std={btc_oos['ret_1bar_pct'].std():.3f}%"
    )
    print(
        f"BTC OOS 3-bar return stats: min={btc_oos['ret_3bar_pct'].min():.2f}% "
        f"max={btc_oos['ret_3bar_pct'].max():.2f}%"
    )
    print()
    # How many bars exceed each threshold?
    for thresh in (-3.0, -4.0, -5.0, -6.0, -8.0):
        n1 = int((btc_oos["ret_1bar_pct"] < thresh).sum())
        print(f"  Bars with 1-bar return < {thresh:+.1f}%: {n1}")
    for thresh in (-8.0, -10.0, -12.0, -15.0):
        n3 = int((btc_oos["ret_3bar_pct"] < thresh).sum())
        print(f"  Bars with 3-bar return < {thresh:+.1f}%: {n3}")
    print()

    summaries: dict[str, dict] = {}
    all_events: list[dict] = []
    per_config_trades: dict[str, pd.DataFrame] = {}

    for cfg in CONFIGS:
        mask, events = _build_kill_windows(btc_oos, cfg)
        all_events.extend(events)
        braked = _apply_brake(trades, btc_oos, mask)
        summary = _summarize(braked, "effective_weighted_pnl", cfg.name)
        summary["config"] = {
            "thresh_1bar_pct": cfg.thresh_1bar_pct if cfg.thresh_1bar_pct > -100 else None,
            "thresh_3bar_pct": cfg.thresh_3bar_pct if cfg.thresh_3bar_pct > -100 else None,
            "kill_bars": cfg.kill_bars,
        }
        summary["n_trigger_events"] = len(events)
        summary["n_killed_trades"] = int(braked["is_killed"].sum())
        summaries[cfg.name] = summary
        per_config_trades[cfg.name] = braked

    # Headline table
    print("=" * 90)
    print("HEADLINE METRICS")
    print("=" * 90)
    header = (
        f"{'config':<18} {'1bar':>5} {'3bar':>5} {'kill':>5} "
        f"{'evts':>5} {'kills':>5} {'Sharpe':>8} {'MaxDD%':>8} "
        f"{'Calmar':>7} {'PnL%':>7} {'XRPshr%':>8}"
    )
    print(header)
    print("-" * len(header))
    for name, s in summaries.items():
        cfg = s["config"]
        t1 = f"{cfg['thresh_1bar_pct']}" if cfg["thresh_1bar_pct"] else "—"
        t3 = f"{cfg['thresh_3bar_pct']}" if cfg["thresh_3bar_pct"] else "—"
        kb = f"{cfg['kill_bars']}" if cfg["kill_bars"] else "—"
        xrp_share = s.get("per_sym_share_pct", {}).get("XRPUSDT", 0.0)
        print(
            f"{name:<18} {t1:>5} {t3:>5} {kb:>5} "
            f"{s['n_trigger_events']:>5} {s['n_killed_trades']:>5} "
            f"{s['sharpe_trade']:>+8.4f} "
            f"{s['max_dd_pct']:>+8.2f} "
            f"{s['calmar']:>+7.2f} "
            f"{s['total_pnl_pct']:>+7.2f} "
            f"{xrp_share:>+8.2f}"
        )

    # Decision criteria
    print()
    print("=" * 90)
    print("DECISION CRITERIA: MaxDD reduction ≥15% AND Sharpe drag ≤5% AND conc change ≤5 pp")
    print("=" * 90)
    baseline = summaries["none"]
    base_sharpe = baseline["sharpe_trade"]
    base_mdd = baseline["max_dd_pct"]
    base_xrp = baseline["per_sym_share_pct"].get("XRPUSDT", 0.0)
    for name, s in summaries.items():
        if name == "none":
            continue
        mdd_reduction = (abs(base_mdd) - abs(s["max_dd_pct"])) / abs(base_mdd) * 100
        sharpe_drag = (s["sharpe_trade"] - base_sharpe) / base_sharpe * 100
        conc_change = s["per_sym_share_pct"].get("XRPUSDT", 0.0) - base_xrp
        mdd_ok = mdd_reduction >= 15.0
        sharpe_ok = sharpe_drag >= -5.0
        conc_ok = abs(conc_change) <= 5.0
        verdict = "PASS" if (mdd_ok and sharpe_ok and conc_ok) else "FAIL"
        print(
            f"  {name}: MaxDD red={mdd_reduction:+.1f}% ({'ok' if mdd_ok else 'BAD'}) | "
            f"Sharpe drag={sharpe_drag:+.1f}% ({'ok' if sharpe_ok else 'BAD'}) | "
            f"ConcΔ={conc_change:+.2f}pp ({'ok' if conc_ok else 'BAD'}) "
            f"→ {verdict}"
        )

    # Per-symbol breakdown for the winner (or C as default)
    print()
    print("=" * 90)
    print("PER-SYMBOL SHARE (XRP / SOL / DOGE / NEAR)")
    print("=" * 90)
    for name, s in summaries.items():
        shares = s["per_sym_share_pct"]
        print(
            f"  {name}: XRP={shares.get('XRPUSDT', 0):6.2f}%  "
            f"SOL={shares.get('SOLUSDT', 0):6.2f}%  "
            f"DOGE={shares.get('DOGEUSDT', 0):6.2f}%  "
            f"NEAR={shares.get('NEARUSDT', 0):6.2f}%  "
            f"(total PnL={s['total_pnl_pct']:+.2f}%)"
        )

    # Sample of trigger events
    if all_events:
        print()
        print("=" * 90)
        print("FIRST 15 TRIGGER EVENTS (across all configs)")
        print("=" * 90)
        edf = pd.DataFrame(all_events)
        edf = edf.sort_values(["config", "trigger_bar_idx"])
        print(edf.head(15).to_string(index=False))

    # Persist
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summaries, indent=2, default=str))
    btc_oos.to_csv(OUT_DIR / "btc_rolling.csv", index=False)
    if all_events:
        pd.DataFrame(all_events).to_csv(OUT_DIR / "trigger_events.csv", index=False)
    all_frames = []
    for name, df in per_config_trades.items():
        df = df.copy()
        df["brake_config"] = name
        all_frames.append(df)
    pd.concat(all_frames, ignore_index=True).to_csv(OUT_DIR / "per_config_trades.csv", index=False)
    print(f"\nArtifacts written to {OUT_DIR}")


if __name__ == "__main__":
    main()
