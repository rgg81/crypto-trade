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
import time
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
for p in (str(_HERE), str(_ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import live_weights as lw  # noqa: E402
import metals_funding as mf  # noqa: E402
import universe_metals as um  # noqa: E402

from crypto_trade.client import BinanceClient  # noqa: E402
from crypto_trade.fetcher import fetch_symbol_interval  # noqa: E402
from crypto_trade.live.state_store import StateStore  # noqa: E402

STEP_MS = 8 * 60 * 60 * 1000


@dataclasses.dataclass(frozen=True)
class MetalsPaperConfig:
    equity_usd: float = 10_000.0
    # Merged 8h store: Dukascopy deep-history backfill (frozen) + Binance live tail. Built once by
    # build_merged_data.py; the engine only ever APPENDS the Binance tail (fetch_symbol_interval).
    data_dir: str = str(_ROOT / "data_live_metals")
    db_path: str = str(_ROOT / "data" / "metals_paper.db")
    equity_csv: str = str(_ROOT / "data" / "metals_equity.csv")
    poll_interval_seconds: int = 60


class MetalsPaperEngine:
    """Paper desk for the iter-008 metals regime book (parity-by-construction)."""

    def __init__(self, cfg: MetalsPaperConfig) -> None:
        self.cfg = cfg
        Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.store = StateStore(Path(cfg.db_path))
        self._instr = list(um.UNIVERSE)  # the 4 Binance metal-perp tickers
        self._client = BinanceClient()  # production fapi klines — the reliable live source

    # ── data refresh (incremental BINANCE klines — reliable live source; Dukascopy is a one-time
    #    historical backfill merged in by build_merged_data.py, never re-fetched live) ──
    def _refresh_one(self, ticker: str) -> int:
        # fetch_symbol_interval resumes from the CSV's last open_time, drops the still-forming
        # candle (close_time > now — a look-ahead guard), and appends to data_dir/<SYM>/8h.csv —
        # the same store the Dukascopy backfill wrote, so signals stay bit-parity with the backtest.
        return fetch_symbol_interval(self._client, Path(self.cfg.data_dir), ticker, "8h")

    def refresh_data(self) -> None:
        for ticker in self._instr:
            try:
                n = self._refresh_one(ticker)
                if n:
                    print(f"  [data] {ticker}: +{n} 8h candle(s)", flush=True)
            except Exception as e:  # noqa: BLE001 — tolerate a transient source hiccup
                print(f"  [data] {ticker}: refresh failed ({e})", flush=True)

    def _refresh_cot(self) -> None:
        """Incremental CFTC COT refresh for the iter-012 ensemble sleeve (tolerant; weekly cadence).

        The COT only changes on Friday releases; refreshing each tick is harmless (idempotent).
        A failed fetch is non-fatal — the engine keeps the cached COT (the sleeve uses release-
        lagged warmup-clean values, so a few-day-stale COT just defers the newest week)."""
        try:
            import ingest_cot
            import iter_012_cot_ensemble as champ

            ingest_cot.refresh_recent()
            champ.clear_cot_cache()
            print("  [data] COT refreshed", flush=True)
        except Exception as e:  # noqa: BLE001 — tolerate CFTC network hiccups; keep cached COT
            print(f"  [data] COT refresh skipped ({e})", flush=True)

    def _refresh_funding(self) -> None:
        """Incremental Binance funding refresh for realistic paper PnL (real 4h metal-perp rates).

        Refreshed ONLY here — at an actual rebalance — so the equity we persist and the funding it
        was computed on stay in sync. Funding NEVER touches the strategy signals (held book is
        identical with/without it); it is a post-decision paper-accounting leg only. Tolerant: a
        failed fetch keeps cached rates (funding is tiny; a stale tail just defers new rows)."""
        try:
            from crypto_trade.portfolio.funding import refresh_funding

            refresh_funding(list(self._instr), data_dir=self.cfg.data_dir)
            print("  [data] funding refreshed", flush=True)
        except Exception as e:  # noqa: BLE001 — tolerate Binance hiccups; keep cached funding
            print(f"  [data] funding refresh skipped ({e})", flush=True)

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
        # Rebalance only on the latest candle EVERY coin has — never max-of-coins. Dukascopy can
        # recover unevenly (one metal's candle lands before another's); rebalancing on that
        # misaligned data feeds the strategy stale/NaN legs → a book that diverges from the backtest
        # (which always sees aligned data). Using MIN makes a lagging coin defer the whole rebalance
        # until all four align — matches the backtest, so parity is preserved.
        latests = {s: int(d.index[-1]) for s, d in coins.items() if len(d)}
        latest = min(latests.values())
        last_seen = self.store.get_state("metals_last_candle")
        if last_seen is not None and latest <= int(last_seen):
            if len(set(latests.values())) > 1:  # some coin(s) ahead — defer for the laggard(s)
                lag = pd.Timestamp(latest, unit="ms")
                print(f"  [tick] coins misaligned (aligned-latest={lag}); deferring rebalance",
                      flush=True)
            return None  # no new COMPLETE candle that ALL coins have

        if self.store.get_state("metals_launch_candle") is None:
            self.store.set_state("metals_launch_candle", str(latest))

        # Refresh COT + funding ONLY here — at an actual rebalance — so the persisted held_w/equity
        # and the data they were computed on stay in sync (a per-tick refresh desyncs them).
        self._refresh_cot()
        self._refresh_funding()

        # target positions for the just-opened (forming) candle — the parity bridge
        tgt = lw.next_target_weights_metals(self._append_forming(coins))
        meta = tgt.pop("_meta")
        held = {s: float(w) for s, w in tgt.items()}

        # realised paper equity since launch = equity0 × Π(1 + price_net + funding_net).
        #   PRICE leg  = regime_net (the backtest net, ×leverage) — the strategy edge.
        #   FUNDING leg = real Binance 4h funding on the DEPLOYED book — paper-only realism.
        #     Causal: only COMPLETE candles are loaded, so candle t's {t, t+4h} funding is settled;
        #     it rides the same price_net.index as the cost leg (lockstep) and NEVER touches the
        #     held book, so backtest↔live parity is preserved.
        price_net = lw.regime_net(coins)
        deployed, _ = lw.deployed_weight_book(coins)
        funding = mf.load_funding(self.cfg.data_dir, list(self._instr))
        fnet = mf.funding_net_8h(deployed, funding).reindex(price_net.index).fillna(0.0)
        launch = pd.Timestamp(int(self.store.get_state("metals_launch_candle")), unit="ms")
        live = price_net.index >= launch
        live_net = (price_net + fnet)[live]
        live_price = price_net[live]
        equity = (
            self.cfg.equity_usd * float((1.0 + live_net).prod())
            if len(live_net)
            else self.cfg.equity_usd
        )
        equity_price_only = (
            self.cfg.equity_usd * float((1.0 + live_price).prod())
            if len(live_price)
            else self.cfg.equity_usd
        )
        funding_pnl = equity - equity_price_only  # $ funding contribution since launch

        prev = self._load_held()
        n_legs = sum(
            1 for s in set(held) | set(prev) if abs(held.get(s, 0.0) - prev.get(s, 0.0)) > 1e-9
        )

        self._save_held(held)
        self.store.set_state("metals_last_candle", str(latest))
        self.store.set_state("metals_equity", f"{equity:.2f}")
        self.store.set_state("metals_funding_pnl", f"{funding_pnl:.4f}")
        self._snapshot_equity(latest, equity, meta)

        as_of = pd.Timestamp(latest, unit="ms")
        print(
            f"  [rebal] as_of={as_of}  breadth={meta['breadth']:.2f}  "
            f"gross={meta['gross']:.3f}  n_pos={meta['n_positions']}  legs={n_legs}  "
            f"equity=${equity:,.0f} (funding ${funding_pnl:+.2f})  "
            f"positions={ {s: round(w, 4) for s, w in held.items()} }",
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
