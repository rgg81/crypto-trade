"""crypto-cup-01 winner paper desk — team-02 breakout-channel via the tournament evaluator.

PARITY BY CONSTRUCTION with Stage-2 Run B: the live target book is computed by the SAME
`portfolio_tournament.engine` pipeline the sealed holdout used — full-pool weekly top-40
eligibility mask -> frozen team-02 `build_raw_weights` -> normalize_and_cap (0.10/0.25) ->
shift(1) -> vol-target scale — recomputed from FULL history each tick, so a mid-week start
reproduces the mask week and the vol-scale chain from data.

INTEGRITY: `check_submission_shas(team-02)` runs at import AND inside every
`next_target_weights` call — any post-freeze mutation of the frozen bundle halts the desk.

Engine seam: exposes the same surface as `strategy.py` / `strategy_v2.py`
(`load_universe`, `candidate_symbols`, `forming_from_close`, `append_forming`,
`next_target_weights`). `delta`/`mode` kwargs are accepted and ignored (the tournament book
has no hysteresis band — the organizer pipeline IS the deployed rule).

Weight convention: the returned weights are the tournament book × vol-target scale for the
candle being HELD (the just-opened candle H). `coins` must end at H (forming close-proxy
row appended by the engine) because scale[H] consumes raw_net[H-1] which needs open[H].
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ANALYSIS = _REPO_ROOT / "analysis"
if str(_ANALYSIS) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS))

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402
from portfolio_tournament import protocol as tp  # noqa: E402
from portfolio_tournament import universe as tu  # noqa: E402

WINNER_TEAM = "team-02"
WINNER_FAMILY = "t02-breakout-channel-v2"
TEAM_DIR = tc.team_dir(WINNER_TEAM)

# Live data store (shared main-repo store; the engine refreshes it each tick).
DATA_DIR = Path(os.environ.get("TOURNAMENT_DESK_DATA_DIR", str(tc.MAIN_DATA_DIR)))

# One JSON line per weekly ranking boundary this desk has ever seen, so a future signal-parity
# audit (scripts/tournament_paper_signal_parity.py) has ground truth instead of having to infer
# whether a live-vs-backtest divergence traces to data that changed on disk after the fact (see
# the 2026-08-24/25 investigation: the shared data/ store's "closed candles are immutable"
# assumption does not hold in practice). Lives in this worktree, not the shared data store.
_SNAPSHOT_PATH = _REPO_ROOT / "logs" / "tournament_universe_weekly_snapshots.jsonl"

# Verify the frozen bundle at import — the desk refuses to start on a mutated submission.
tp.check_submission_shas(TEAM_DIR)


# ---------------------------------------------------------------- data loading ------------------
def candidate_symbols() -> list[str]:
    """Symbols the engine refreshes each tick: the full pure-crypto USDT pool on disk."""
    return tu.pool_symbols(DATA_DIR)


def load_universe() -> dict:
    """{sym: df(open, close, quote_volume; ms open_time index)} for the full crypto pool."""
    coins: dict = {}
    for sym in candidate_symbols():
        p = DATA_DIR / sym / "8h.csv"
        try:
            k = pd.read_csv(p, usecols=["open_time", "open", "close", "quote_volume"])
        except Exception:  # noqa: BLE001 — per-symbol tolerant (delisted/partial files)
            continue
        k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
        if len(k):
            coins[sym] = k
    return coins


def forming_from_close(coins: dict) -> dict:
    """Forming (hold) candle open via the NON-RAGGED close-proxy: open[H] ~= close[H-1]."""
    out = {}
    for s, d in coins.items():
        if not len(d):
            continue
        last_ot = int(d.index[-1])
        out[s] = (last_ot + tc.STEP_MS, float(d["close"].iloc[-1]))
    return out


def append_forming(coins: dict, forming_opens: dict) -> dict:
    out = {}
    for s, d in coins.items():
        fo = forming_opens.get(s)
        if fo is None:
            out[s] = d
            continue
        ot, px = int(fo[0]), float(fo[1])
        if len(d) and ot <= int(d.index[-1]):
            out[s] = d
            continue
        last_qv = float(d["quote_volume"].iloc[-1]) if len(d) else 0.0
        row = pd.DataFrame({"open": [px], "close": [px], "quote_volume": [last_qv]}, index=[ot])
        out[s] = pd.concat([d, row])
    return out


# ---------------------------------------------------------------- book construction -------------
def _panels(coins: dict) -> tuple[dict, dict, pd.DataFrame]:
    """(pn, scoring, elig) on the aligned 8h grid — the tournament engine's semantics with the
    minimal panel set the winner's book needs (open/close/quote_volume; funding from disk)."""
    cols = sorted(coins)
    nonempty = [coins[s] for s in cols if len(coins[s])]
    lo = max(min(int(d.index.min()) for d in nonempty), int(tc.TRN_IS_START.value // 10**6))
    hi = max(int(d.index.max()) for d in nonempty)
    grid_ms = pd.Index(pd.RangeIndex(lo, hi + tc.STEP_MS, tc.STEP_MS), name="open_time")
    dt = pd.to_datetime(grid_ms, unit="ms")

    pn: dict = {}
    for f in ("open", "close", "quote_volume"):
        panel = pd.DataFrame({s: coins[s][f] for s in cols}).astype(float).reindex(grid_ms)
        panel.index = dt
        pn[f] = panel
    pn["ret_fwd"] = pn["open"].shift(-1) / pn["open"] - 1.0

    qv_ms = pn["quote_volume"].copy()
    qv_ms.index = grid_ms
    mask = tu.weekly_topn_mask(qv_ms)
    elig = mask.reindex(index=grid_ms, columns=cols).fillna(False).astype(bool)
    elig.index = dt

    funding: dict = {}
    fdir = DATA_DIR / "funding_rates"
    for s in cols:
        p = fdir / f"{s}.csv"
        if not p.exists():
            continue
        f = pd.read_csv(p).drop_duplicates(subset="funding_time", keep="last")
        funding[s] = f.set_index("funding_time")["funding_rate"].astype(float).sort_index()
    fund_win = te.funding_candle_panel(funding, grid_ms, cols)
    fund_win.index = dt

    scoring = {
        "fund_win": fund_win,
        "slip_side": te.slip_side_panel(pn["quote_volume"]),
        "elig": elig,
    }
    return pn, scoring, elig


def _snapshot_weekly_ranking(qv: pd.DataFrame) -> None:
    """Append the trailing-liquidity ranking used for the LATEST weekly refresh boundary, once
    per boundary ever seen (idempotent on refresh_ms) — best-effort, never blocks trading.
    `qv` is DatetimeIndex-ed (pn["quote_volume"] from _panels), NOT raw epoch-ms."""
    try:
        liq = qv.rolling(tc.DVOL_WIN, min_periods=tc.DVOL_MIN_PERIODS).mean().shift(1)
        refresh_rows = qv.index[(qv.index.weekday == tc.REFRESH_WEEKDAY) & (qv.index.hour == 0)]
        if not len(refresh_rows):
            return
        refresh_at = refresh_rows[-1]
        refresh_ms = int(refresh_at.value // 10**6)

        seen = set()
        if _SNAPSHOT_PATH.exists():
            for line in _SNAPSHOT_PATH.read_text().splitlines():
                if line.strip():
                    seen.add(json.loads(line)["refresh_ms"])
        if refresh_ms in seen:
            return  # this week's boundary is already recorded (first observer wins)

        row = liq.loc[refresh_at]
        rank = row.rank(ascending=False, method="min")
        record = {
            "refresh_ms": refresh_ms,
            "refresh_at": str(refresh_at),
            "liq": {s: round(float(v), 2) for s, v in row.items() if pd.notna(v)},
            "top40": sorted(s for s in row.index if pd.notna(rank[s]) and rank[s] <= tc.TOP_N),
        }
        _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _SNAPSHOT_PATH.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:  # noqa: BLE001 — instrumentation must never break a live decision
        pass


def position_weight_book(coins: dict) -> pd.DataFrame:
    """Full per-candle deployed book: row t = tournament weights held during candle t × scale[t]."""
    tp.check_submission_shas(TEAM_DIR)  # SHA-recheck on EVERY recompute
    pn, scoring, elig = _panels(coins)
    _snapshot_weekly_ranking(pn["quote_volume"])
    mod = tp.load_strategy(TEAM_DIR)
    view = {k: pn[k].copy() for k in ("open", "close", "quote_volume")}
    aux = {"eligibility": elig.copy(), "seed": tc.SEED}
    raw = te.conform_raw(mod.build_raw_weights(view, aux), pn)
    tp.purge_team_modules()
    _net, w, parts = te.net_series(raw, pn, scoring)
    return w.mul(parts["scale"], axis=0)


def next_target_weights(coins: dict, delta: float | None = None, mode: str | None = None) -> dict:
    """Deployed weights to HOLD during the LATEST candle in `coins` (engine seam entry)."""
    book = position_weight_book(coins)
    last = book.iloc[-1]
    pos = last[last.abs() > 1e-9]
    out = {s: float(v) for s, v in pos.items()}
    n_long = int((last > 1e-9).sum())
    n_short = int((last < -1e-9).sum())
    out["_meta"] = {
        "as_of": str(book.index[-1]),
        "lambda_pick": None,  # v1-era engine meta key (compat; no walk-forward lambda here)
        "team": WINNER_TEAM,
        "family": WINNER_FAMILY,
        "gross": float(last.abs().sum()),
        "n_positions": int(len(pos)),
        "n_long": n_long,
        "n_short": n_short,
        "vol_scale": float(np.nan_to_num(last.abs().sum())),
    }
    return out
