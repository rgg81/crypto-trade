"""Live weight engine for BASELINE_PORTFOLIO_V2 — PARITY BY CONSTRUCTION.

Drop-in for the PortfolioEngine's strategy interface (mirrors v1 `portfolio/strategy.py`). The live
executor and the v2 backtest compute target weights from the SAME code: this module imports the
validated `analysis/portfolio_v2` engine and exposes the v1-shaped surface:

- candidate_symbols()           -> ex-stable ascii USDT-perp symbols from the live data dir.
- load_universe()               -> universe_v2.load_pool_pit() (survivorship-safe PIT pool).
- forming_from_close(coins)     -> next-open close-proxy per active coin (8h step), like v1.
- append_forming(coins, opens)  -> append the forming (hold) candle's open per coin, like v1.
- next_target_weights(coins)    -> the DEPLOYED book's last row (held_w × scale, risk layer ON).

The v2 baseline (BASELINE_PORTFOLIO_V2.md):
  signal = equal-weight ensemble over L∈{42,63,84,126,168} of unit-L1-normalized
           _xsmom(close, elig, L), re-normalized to unit-L1.  rank_lo=20, rank_hi=40, season=168.
  build  = run_book_from_signal(... slip=default_slip_bps ...) with the FROZEN risk layer
           (TARGET_VOL=0.006, MAX_LEV=2.0, dd_brake OFF) -> deployed weight = held_w × scale.

The analysis modules use CWD-relative globs + bare sibling imports, so we put `analysis/` on the
path and run the data ops with CWD = repo root (mirrors v1 strategy._in_root). The DATA_GLOB /
FUNDING_DIR module consts are flipped to the LIVE `data/` dir at import so the live process reads
fresh klines + funding while the parity gates keep their `pf_data/` defaults.
"""

from __future__ import annotations

import contextlib
import glob
import os
import os.path
import sys

import numpy as np
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_ANALYSIS = os.path.join(_ROOT, "analysis")
if _ANALYSIS not in sys.path:
    sys.path.insert(0, _ANALYSIS)

from portfolio_v2 import engine_v2 as _e2  # noqa: E402
from portfolio_v2 import universe_v2 as _uv  # noqa: E402

# ---- live data-dir override (parity gates keep the pf_data/ defaults) -----------------------
# Flip the analysis-module data globs to the live `data/` dir for the live process ONLY. The
# parity gates import these modules fresh and reset the consts themselves (pf_data/), so this
# import-time flip cannot perturb parity_check. LIVE_DATA_DIR can be overridden (e.g. the dry
# smoke points it back at pf_data) by setting PORTFOLIO_V2_DATA_DIR before import.
LIVE_DATA_DIR = os.environ.get("PORTFOLIO_V2_DATA_DIR", "data")
_uv.DATA_GLOB = f"{LIVE_DATA_DIR}/*USDT/8h.csv"
_e2.FUNDING_DIR = f"{LIVE_DATA_DIR}/funding_rates"

# ---- v2 deployed config (BASELINE_PORTFOLIO_V2.md, frozen) -----------------------------------
DELTA = 0.010  # hysteresis band (SNAP) — same as v1
MODE = "snap"
K_EXIT = 2  # eligibility-exit: force-close after K candles out of band
RANK_LO = 20
RANK_HI = 40
SEASON = 168
ENSEMBLE_LOOKBACKS = (42, 63, 84, 126, 168)  # the frozen 5-way ensemble
TARGET_VOL = 0.006  # FROZEN risk layer (iter-007)
MAX_LEV = 2.0
SLIP_FN = _e2.default_slip_bps

STABLE = _uv.STABLE  # ex-stable regex (shared with the universe loader)


@contextlib.contextmanager
def _in_root():
    """Run the analysis data ops with CWD = repo root so their relative globs resolve."""
    cwd = os.getcwd()
    os.chdir(_ROOT)
    try:
        yield
    finally:
        os.chdir(cwd)


def candidate_symbols() -> list[str]:
    """Candidate-universe symbols (ex-stable, ascii) WITHOUT loading every CSV — for kline refresh.

    Mirrors universe_v2.load_pool_pit's symbol filter (the per-bar seasoning cut is applied later by
    eligibility). Used to know which symbols' klines + funding the live tick must keep fresh so the
    PIT rank-21-40 selection matches the backtest (which scans the full candidate set).
    """
    syms = []
    for p in sorted(glob.glob(os.path.join(_ROOT, LIVE_DATA_DIR, "*USDT", "8h.csv"))):
        sym = os.path.basename(os.path.dirname(p))
        if not sym.endswith("USDT") or STABLE.search(sym) or not sym.isascii():
            continue
        syms.append(sym)
    return syms


def load_universe() -> dict:
    """PIT candidate universe (live <data>/<SYM>/8h.csv, ex-stable, survivorship-safe). CWD-safe."""
    with _in_root():
        return _uv.load_pool_pit()


def forming_from_close(coins: dict) -> dict:
    """Build the forming (hold) candle's open per ACTIVE coin from its last close — non-ragged.

    Identical to v1 strategy.forming_from_close: the next candle's open ~= the prior close (gap
    < 0.01%), so close[last] is a near-exact proxy for open[H]. Using it for EVERY active coin (last
    candle == the global latest) avoids the ragged-panel bug a partial fetch causes. Returns
    {sym: (next_open_time_ms, close[last])}. 8h candle assumed.
    """
    if not coins:
        return {}
    step = 8 * 60 * 60 * 1000
    global_last = max(int(d.index[-1]) for d in coins.values() if len(d))
    out = {}
    for s, d in coins.items():
        if len(d) and int(d.index[-1]) == global_last:
            out[s] = (global_last + step, float(d["close"].iloc[-1]))
    return out


def append_forming(coins: dict, forming_opens: dict) -> dict:
    """Append the just-opened (forming) candle's OPEN per coin so the deployed book covers the HOLD
    candle. Identical to v1 strategy.append_forming: bit-exact parity needs open[H] (the vol-target
    scale[H] uses it); close[H]/qv[H] do NOT affect deployed[H], so we placeholder them.
    forming_opens = {sym: (open_time_ms, open_px)}.
    """
    out = {}
    for s, d in coins.items():
        fo = forming_opens.get(s)
        if fo is None:
            out[s] = d
            continue
        ot, px = int(fo[0]), float(fo[1])
        if len(d) and ot <= int(d.index[-1]):
            out[s] = d  # forming candle already closed / in data
            continue
        last_qv = float(d["quote_volume"].iloc[-1]) if len(d) else 0.0
        row = pd.DataFrame({"open": [px], "close": [px], "quote_volume": [last_qv]}, index=[ot])
        out[s] = pd.concat([d, row])
    return out


def _norm(sig: pd.DataFrame) -> pd.DataFrame:
    """Unit-L1 normalize per candle (Σ_c |sig| = 1), 0.0 where the gross is 0 (degenerate row)."""
    return sig.div(sig.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def _ensemble_signal(coins: dict) -> pd.DataFrame:
    """The frozen 5-way XS-mom ensemble signal panel (BASELINE_PORTFOLIO_V2.md, == iter_v2_008).

        elig = eligibility(rank 21-40, season 168)
        for L in {42,63,84,126,168}: xs_L = unit-L1-normalized _xsmom(close, elig, L)
        signal = unit-L1-normalized( mean_L xs_L )

    Computed on the SAME panel/elig the engine rebuilds internally, so the signal aligns onto the
    engine grid 1:1 (run_book_from_signal reindexes + 0.0-fills any residual mismatch).
    """
    panel = _e2.build_panel(coins)
    elig = (
        _uv.eligibility(coins, RANK_LO, RANK_HI, SEASON)
        .reindex(index=panel["opens"].index, columns=panel["cols"])
        .fillna(False)
    )

    def _xs(lb: int) -> pd.DataFrame:
        s, _ = _e2._xsmom(panel["close"], elig, lb)
        return _norm(s)

    mean = sum(_xs(lb) for lb in ENSEMBLE_LOOKBACKS) / len(ENSEMBLE_LOOKBACKS)
    return _norm(mean)


def position_weight_book(coins: dict, delta: float = DELTA) -> pd.DataFrame:
    """Full per-candle DEPLOYED position-weight matrix (held_w × scale), risk layer ON.

    Row t is the weight HELD during candle t (decided at close[t-1]) — the v2 backtest's traded,
    vol-targeted book. PARITY-CRITICAL: set engine_v2.TARGET_VOL/MAX_LEV to the frozen risk layer
    BEFORE the run so `scale` carries the de-lever, then deployed = held_w × scale.
    """
    with _in_root():
        signal = _ensemble_signal(coins)
        # set the frozen risk layer as module globals so run_book_from_signal's inline
        # scale = (TARGET_VOL / rv).clip(upper=MAX_LEV) reproduces retarget(0.006, 2.0) exactly.
        prev_tv, prev_ml = _e2.TARGET_VOL, _e2.MAX_LEV
        _e2.TARGET_VOL, _e2.MAX_LEV = TARGET_VOL, MAX_LEV
        try:
            res = _e2.run_book_from_signal(
                coins,
                signal,
                rank_lo=RANK_LO,
                rank_hi=RANK_HI,
                season=SEASON,
                slip_bps_fn=SLIP_FN,
                delta=delta,
                k_exit=K_EXIT,
                mode=MODE,
            )
        finally:
            _e2.TARGET_VOL, _e2.MAX_LEV = prev_tv, prev_ml
    return res["held_w"].mul(res["scale"], axis=0)


def next_target_weights(coins: dict, delta: float = DELTA) -> dict:
    """Deployed position weights to HOLD during the LATEST candle in `coins` — the live target.

    BIT-EXACT DEFINITION (parity_live_check): the deployed weight for the candle being held = the
    LAST ROW of the full deployed book (held_w × scale, risk layer ON). The vol scale for candle H
    depends on open[H], so the CALLER must feed `coins` ending at the HOLD candle (include the
    just-opened candle's open via the close-proxy) — exactly like v1.

    Because the book is recomputed from FULL history each tick, the path-dependent band / eligexit /
    vol-target chain is reproduced from data, so a mid-stream start is handled automatically.
    Returns {symbol: signed_weight} for non-trivial holds (gross ≈ scale ≈ 0.3-0.6 after the
    de-lever), plus a "_meta" block.
    """
    deployed = position_weight_book(coins, delta)  # full per-candle deployed book
    last = deployed.iloc[-1]  # weight held during the latest candle
    pos = last[last.abs() > 1e-9]
    out = {s: float(v) for s, v in pos.items()}
    out["_meta"] = {
        "as_of": str(deployed.index[-1]),
        "lambda_pick": None,  # v2 has no walk-forward λ (the ensemble IS the target)
        "gross": float(last.abs().sum()),
        "n_positions": int(len(pos)),
    }
    return out
