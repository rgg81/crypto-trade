"""Metals PAPER-TRADING engine — live signals BIT-IDENTICAL to the backtest, paper fills.

Runs the FROZEN iter-008 sleeve-aware regime book continuously as a paper desk. Each new 8h candle:
refresh data → recompute the target positions from FULL history (the parity mechanism — same
functions as the backtest) → "fill" the plan at the candle open (paper, zero slippage) → persist the
held book + equity → log. No real orders, no Binance testnet.

PARITY BY CONSTRUCTION: signals come from `live_weights.next_target_weights_metals` (the deployed
position book of `iter_008_allweather.regime_book`) computed on the SAME Dukascopy data the backtest
uses — the only data deep enough for the SMA-450 regime gate (Binance metal perps are ~5mo old). The
paper PnL is `live_weights.regime_net` compounded — the backtest net itself. The Binance metal-perp
BASIS is tracked separately (monitor) for the eventual real-money cutover.

State (SQLite `engine_state`, reused crypto `StateStore`): `metals_held_w` (JSON {ticker: weight}),
`metals_last_candle` (ms open_time of the last processed COMPLETE candle), `metals_launch_candle`,
`metals_equity`. An equity snapshot is appended to `<data_dir>/../metals_equity.csv` each rebalance.

Run:  PYTHONUNBUFFERED=1 uv run python run_metals_paper.py > logs/metals_paper.log 2>&1
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
for p in (str(_HERE), str(_ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import ingest_dukascopy as ing  # noqa: E402
import live_weights as lw  # noqa: E402
import universe_metals as um  # noqa: E402

from crypto_trade.live.state_store import StateStore  # noqa: E402
from crypto_trade.storage import csv_path, read_last_open_time, write_klines  # noqa: E402

STEP_MS = 8 * 60 * 60 * 1000


@dataclasses.dataclass(frozen=True)
class MetalsPaperConfig:
    equity_usd: float = 10_000.0
    data_dir: str = str(_ROOT / "data_live_metals")  # dedicated live Dukascopy store
    db_path: str = str(_ROOT / "data" / "metals_paper.db")
    equity_csv: str = str(_ROOT / "data" / "metals_equity.csv")
    poll_interval_seconds: int = 60
    refresh_lookback_days: int = 21  # incremental Dukascopy pull window each tick
    seed_start: str = "2005-06-01"  # first-run deep history (warmup for SMA450)


class MetalsPaperEngine:
    """Paper desk for the iter-008 metals regime book (parity-by-construction)."""

    def __init__(self, cfg: MetalsPaperConfig) -> None:
        self.cfg = cfg
        Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.store = StateStore(Path(cfg.db_path))
        self._instr = dict(ing.INSTRUMENTS)  # {ticker: (dukascopy_id, start)}

    # ── data refresh (incremental Dukascopy — the backtest's source, for exact signal parity) ──
    def _refresh_one(self, ticker: str, instrument: str) -> int:
        out = csv_path(Path(self.cfg.data_dir), ticker, "8h")
        last = read_last_open_time(out)
        start = (
            self.cfg.seed_start
            if last is None
            else (
                pd.Timestamp(last, unit="ms") - pd.Timedelta(days=self.cfg.refresh_lookback_days)
            ).strftime("%Y-%m-%d")
        )
        end = (dt.datetime.now(dt.UTC).date() + dt.timedelta(days=1)).isoformat()
        with tempfile.TemporaryDirectory(prefix="mlive_") as tmp:
            h1 = ing.fetch_h1(instrument, start, end, tmp)
        eight = ing.resample_8h(h1)
        klines = [k for k in ing.to_klines(eight) if last is None or k.open_time > last]
        return write_klines(out, klines, append=(last is not None))

    def refresh_data(self) -> None:
        for ticker, (instrument, _start) in self._instr.items():
            try:
                n = self._refresh_one(ticker, instrument)
                if n:
                    print(f"  [data] {ticker}: +{n} 8h candle(s)", flush=True)
            except Exception as e:  # noqa: BLE001 — tolerate a transient source hiccup
                print(f"  [data] {ticker}: refresh failed ({e})", flush=True)
        self._refresh_cot()

    def _refresh_cot(self) -> None:
        """Incremental CFTC COT refresh for the iter-012 ensemble sleeve (tolerant; weekly cadence).

        The COT only changes on Friday releases; refreshing each tick is harmless (idempotent).
        A failed fetch is non-fatal — the engine keeps the cached COT (the sleeve uses release-
        lagged warmup-clean values, so a few-day-stale COT just defers the newest week, never leaks)."""
        try:
            import ingest_cot
            import iter_012_cot_ensemble as champ

            ingest_cot.refresh_recent()
            champ.clear_cot_cache()
            print("  [data] COT refreshed", flush=True)
        except Exception as e:  # noqa: BLE001 — tolerate CFTC network hiccups; keep cached COT
            print(f"  [data] COT refresh skipped ({e})", flush=True)

    # ── forming-candle proxy (open ≈ last close; the live target is for the just-opened candle) ──
    @staticmethod
    def _append_forming(coins: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        if not coins:
            return coins
        glast = max(int(d.index[-1]) for d in coins.values() if len(d))
        out: dict[str, pd.DataFrame] = {}
        for s, d in coins.items():
            if len(d) and int(d.index[-1]) == glast:
                px = float(d["close"].iloc[-1])
                row = pd.DataFrame(
                    {"open": [px], "high": [px], "low": [px], "close": [px], "volume": [0.0]},
                    index=[glast + STEP_MS],
                )
                out[s] = pd.concat([d, row])
            else:
                out[s] = d
        return out

    def _new_candle_due(self) -> bool:
        """Clock gate: has a new COMPLETE 8h candle (00/08/16 UTC) opened since the last rebalance?

        Keeps the expensive Dukascopy refresh to ~once per 8h instead of every 60s poll. The latest
        complete candle's open = (now floored to the 8h grid) − 8h (forming candle is the floor).
        """
        last = self.store.get_state("metals_last_candle")
        if last is None:
            return True  # first run — seed + rebalance
        now_ms = int(time.time() * 1000)
        latest_complete_open = (now_ms // STEP_MS) * STEP_MS - STEP_MS
        return latest_complete_open > int(last)

    # ── one tick: refresh → detect new candle → recompute target → paper-fill → persist ──
    def run_once(self) -> dict | None:
        self.refresh_data()
        coins = um.load_metals(Path(self.cfg.data_dir))
        if not coins:
            print("  [tick] no data yet", flush=True)
            return None
        latest = max(int(d.index[-1]) for d in coins.values() if len(d))
        last_seen = self.store.get_state("metals_last_candle")
        if last_seen is not None and latest <= int(last_seen):
            return None  # no new COMPLETE candle since last rebalance

        if self.store.get_state("metals_launch_candle") is None:
            self.store.set_state("metals_launch_candle", str(latest))

        # target positions for the just-opened (forming) candle — the parity bridge
        tgt = lw.next_target_weights_metals(self._append_forming(coins))
        meta = tgt.pop("_meta")
        held = {s: float(w) for s, w in tgt.items()}

        # realised paper equity = equity0 × Π(1+net) since launch (regime_net = the backtest net)
        net = lw.regime_net(coins)
        launch = pd.Timestamp(int(self.store.get_state("metals_launch_candle")), unit="ms")
        live_net = net[net.index >= launch]
        equity = (
            self.cfg.equity_usd * float((1.0 + live_net).prod())
            if len(live_net)
            else (self.cfg.equity_usd)
        )

        prev = self._load_held()
        n_legs = sum(
            1 for s in set(held) | set(prev) if abs(held.get(s, 0.0) - prev.get(s, 0.0)) > 1e-9
        )

        self._save_held(held)
        self.store.set_state("metals_last_candle", str(latest))
        self.store.set_state("metals_equity", f"{equity:.2f}")
        self._snapshot_equity(latest, equity, meta)

        as_of = pd.Timestamp(latest, unit="ms")
        print(
            f"  [rebal] as_of={as_of}  breadth={meta['breadth']:.2f}  "
            f"gross={meta['gross']:.3f}  n_pos={meta['n_positions']}  legs={n_legs}  "
            f"equity=${equity:,.0f}  positions={ {s: round(w, 4) for s, w in held.items()} }",
            flush=True,
        )
        return {"as_of": str(as_of), "held": held, "equity": equity, "meta": meta, "legs": n_legs}

    def run(self) -> None:
        print(
            f"[metals-paper] start  equity=${self.cfg.equity_usd:,.0f}  data={self.cfg.data_dir}  "
            f"db={self.cfg.db_path}",
            flush=True,
        )
        while True:
            try:
                if self._new_candle_due():  # clock gate — only refresh/rebalance on a new 8h candle
                    self.run_once()
            except KeyboardInterrupt:
                print("[metals-paper] stopped", flush=True)
                return
            except Exception as e:  # noqa: BLE001
                print(f"[metals-paper] tick error: {e}", flush=True)
            time.sleep(self.cfg.poll_interval_seconds)

    # ── persistence helpers ──
    def _load_held(self) -> dict:
        raw = self.store.get_state("metals_held_w")
        return json.loads(raw) if raw else {}

    def _save_held(self, held: dict) -> None:
        self.store.set_state("metals_held_w", json.dumps(held))

    def _snapshot_equity(self, candle_ms: int, equity: float, meta: dict) -> None:
        path = Path(self.cfg.equity_csv)
        path.parent.mkdir(parents=True, exist_ok=True)
        new = not path.exists()
        with open(path, "a") as f:
            if new:
                f.write("ts_utc,candle_open_ms,equity_usd,gross,breadth,n_positions\n")
            f.write(
                f"{dt.datetime.now(dt.UTC).isoformat()},{candle_ms},{equity:.2f},"
                f"{meta['gross']:.4f},{meta['breadth']:.4f},{meta['n_positions']}\n"
            )
