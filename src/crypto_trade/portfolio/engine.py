"""PortfolioEngine — live executor for baseline-v2 (trend+carry+hysteresis), DRY-RUN first.

Every 8h candle close: refresh klines + funding for the full candidate universe -> compute the
upcoming-candle target weights via the SAME backtest code (strategy.next_target_weights) -> diff vs
current holdings -> apply the hysteresis band (delta=0.010) vs ACTUAL held weights -> produce a
rebalance plan. In DRY-RUN the plan is LOGGED (no orders) and treated as filled (held_w persisted),
so we can verify live decisions track the backtest before any order is placed.

Parity contract:
- target weights come from strategy.next_target_weights (machine-precision parity with iter_020).
- act on candle CLOSE[t] (detect_new_candle on a reference symbol) -> rebalance at next open.
- notional = weight * equity (the weights already carry the vol-target scale ~0.70 gross). LEVERAGE
  only reduces required MARGIN (notional/leverage); it does NOT scale the notional.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

from crypto_trade.client import BinanceClient
from crypto_trade.live import data_pipeline
from crypto_trade.live.auth_client import AuthenticatedBinanceClient
from crypto_trade.live.state_store import StateStore
from crypto_trade.portfolio import funding, strategy


@dataclasses.dataclass(frozen=True)
class PortfolioConfig:
    equity_usd: float = 10_000.0
    leverage: float = 1.0
    delta: float = strategy.DELTA          # hysteresis band (SNAP)
    interval: str = "8h"
    ref_symbol: str = "BTCUSDT"            # candle-close trigger reference
    min_notional_usd: float = 5.0          # skip dust legs (Binance min-notional is ~5 USDT)
    poll_interval_seconds: int = 60
    data_dir: str = "data"
    db_path: str = "data/portfolio_dry_run.db"
    dry_run: bool = True
    testnet: bool = False


def _held_key(cfg: PortfolioConfig) -> str:
    return "portfolio_held_w"


class PortfolioEngine:
    def __init__(self, config: PortfolioConfig, settings):
        self.cfg = config
        self.settings = settings
        # klines always from production (parity with backtest data source). kline_client (bulk
        # incremental refresh) vs read_client (limit=2 for candle-detect + forming-open polls).
        self.kline_client = BinanceClient(base_url=settings.base_url)
        self.read_client = BinanceClient(base_url=settings.base_url, limit=2)
        self.store = StateStore(Path(config.db_path))
        # signed client (orders/positions/leverage) — testnet routing via auth_base_url; only when
        # we will actually trade. klines stay on production base_url for full history (parity).
        self.auth: AuthenticatedBinanceClient | None = None
        self.qty_prec: dict[str, int] = {}
        self.step_size: dict[str, float] = {}     # LOT_SIZE stepSize per symbol (qty multiple)
        self._lev_set: set[str] = set()           # symbols whose leverage we've already set
        if not config.dry_run and settings.binance_api_key:
            auth_url = settings.auth_base_url or settings.base_url
            self.auth = AuthenticatedBinanceClient(
                api_key=settings.binance_api_key,
                api_secret=settings.binance_api_secret,
                base_url=auth_url,
            )
            mode = "TESTNET" if config.testnet else "LIVE"
            print(f"[portfolio:{mode}] AUTH endpoint: {auth_url}")

    # ---- held-weight persistence (the hysteresis band's path-dependent state) ----
    def _load_held(self) -> dict:
        raw = self.store.get_state(_held_key(self.cfg))
        return json.loads(raw) if raw else {}

    def _save_held(self, held: dict) -> None:
        self.store.set_state(_held_key(self.cfg), json.dumps(held))

    # ---- the core: compute the rebalance plan for the upcoming candle ----
    def compute_plan(self, current_weights: dict | None = None,
                     forming_opens: dict | None = None) -> dict:
        """Return the rebalance plan: per-coin target weight, current weight, delta-notional, side.

        PARITY: target = strategy.next_target_weights = the backtest's deployed book for the held
        candle (the hysteresis band is ALREADY baked in there, on the pre-vol-target weights). The
        engine does NOT re-band — it TRACKS that book: trade = target - actual_held. The only
        execution filter is min_notional (skip dust legs Binance rejects). Because the target is
        recomputed from FULL history every tick, a mid-month start is handled automatically: the
        month's walk-forward lambda and the path-dependent band chain are reproduced from data, not
        from when we started. current_weights = actual positions (live) / persisted paper (dry-run);
        an empty book => cold-start full entry falls out naturally.
        """
        coins = strategy.load_universe()
        # forming (hold) candle via NON-RAGGED close-proxy (every active coin) unless an override is
        # given. A partial network fetch ragged-collapses the book (the XLM-0.40 bug); close[last]
        # is a < 0.01% proxy for open[H] -> relative weights bit-exact, gross off < 0.1%.
        if forming_opens is None:
            forming_opens = strategy.forming_from_close(coins)
        prices = {s: float(px) for s, (_, px) in forming_opens.items()}
        coins = strategy.append_forming(coins, forming_opens)
        tgt = strategy.next_target_weights(coins, delta=self.cfg.delta)
        meta = tgt.pop("_meta")
        cur = dict(current_weights if current_weights is not None else self._load_held())
        gross_dollar = self.cfg.equity_usd        # notional base; leverage only affects margin

        all_syms = set(tgt) | set(cur)
        legs = []
        new_held = {}
        for s in sorted(all_syms):
            t = float(tgt.get(s, 0.0))            # backtest deployed weight for the upcoming candle
            c = float(cur.get(s, 0.0))            # what we actually hold now
            trade_w = t - c
            delta_notional = trade_w * gross_dollar
            if abs(delta_notional) >= self.cfg.min_notional_usd and s in prices:
                legs.append({
                    "symbol": s,
                    "side": "BUY" if trade_w > 0 else "SELL",
                    "target_w": round(t, 6),
                    "current_w": round(c, 6),
                    "delta_notional_usd": round(delta_notional, 2),
                    "price": prices[s],
                })
                held_w = t                        # traded to target
            else:
                held_w = c                        # below min-notional: can't trade, keep current
            if abs(held_w) > 1e-9:
                new_held[s] = held_w
        return {
            "as_of": meta["as_of"],
            "cold_start": len(cur) == 0,
            "lambda_pick": meta["lambda_pick"],
            "target_gross": round(meta["gross"], 4),
            "n_target_positions": meta["n_positions"],
            "gross_dollar": round(gross_dollar, 2),
            "n_rebalance_legs": len(legs),
            "rebalance_notional_usd": round(sum(abs(x["delta_notional_usd"]) for x in legs), 2),
            "legs": legs,
            "_new_held": new_held,
        }

    def refresh_data(self) -> None:
        """Refresh klines + funding for the full candidate universe (PIT + carry parity).

        Per-symbol tolerant: a coin delisted from production fapi (400 on /klines) keeps its on-disk
        CSV (parity with the backtest view) and is skipped — one dead symbol must not abort the run.
        """
        from crypto_trade.fetcher import fetch_symbol_interval
        data_dir = Path(self.cfg.data_dir)
        syms = strategy.candidate_symbols()
        ok = skipped = 0
        for s in syms:
            try:
                fetch_symbol_interval(self.kline_client, data_dir, s, self.cfg.interval)
                ok += 1
            except Exception:
                skipped += 1                   # delisted / unavailable on production fapi
        print(f"[portfolio] klines refreshed: {ok} ok, {skipped} skipped (delisted)")
        funding.refresh_funding(syms, self.cfg.data_dir)

    # ---- live execution plumbing (reuses the proven AuthenticatedBinanceClient) ----
    def setup_exchange(self) -> None:
        """Load quantityPrecision + LOT_SIZE stepSize (exchangeInfo) for valid order qtys."""
        if self.auth is None:
            return
        info = self.auth.get_exchange_info()
        for si in info.get("symbols", []):
            sym = si["symbol"]
            self.qty_prec[sym] = int(si["quantityPrecision"])
            for f in si.get("filters", []):
                if f.get("filterType") in ("LOT_SIZE", "MARKET_LOT_SIZE"):
                    self.step_size[sym] = float(f["stepSize"])    # qty must be a multiple of this
                    break
        print(f"[portfolio] loaded quantityPrecision + stepSize for {len(self.qty_prec)} symbols")

    def _ensure_leverage(self, symbol: str) -> None:
        """Set leverage on a symbol once (lazily, before its first order)."""
        if self.auth is None or symbol in self._lev_set:
            return
        try:
            self.auth.set_leverage(symbol, max(1, int(round(self.cfg.leverage))))
        except Exception as exc:
            print(f"[portfolio] set_leverage {symbol} failed: {exc}")
        self._lev_set.add(symbol)

    def _actual_weights(self) -> dict:
        """Current per-coin weight from positions: positionAmt*markPrice / (equity*leverage)."""
        if self.auth is None:
            return self._load_held()
        gross_dollar = self.cfg.equity_usd        # notional base (matches compute_plan)
        cur: dict = {}
        for p in self.auth.get_positions():
            amt = float(p.get("positionAmt", 0) or 0)
            if amt == 0:
                continue
            mark = float(p.get("markPrice", 0) or 0)
            cur[p["symbol"]] = amt * mark / gross_dollar
        return cur

    def _round_qty(self, symbol: str, qty: float) -> float:
        """Snap qty DOWN to the LOT_SIZE stepSize multiple, then to precision (Binance-valid).

        is coarser than 10^-precision (e.g. ONDO step=1, prec=1). floor-to-step is the rule.
        is coarser than 10^-precision (e.g. ONDO). floor-to-step is the correct Binance rule.
        """
        prec = self.qty_prec.get(symbol, 3)
        step = self.step_size.get(symbol)
        if step and step > 0:
            qty = (qty // step) * step            # floor to a stepSize multiple
        return round(qty, prec)                    # clean float artifacts to the allowed precision

    def execute(self, plan: dict) -> dict:
        """Place a MARKET order per rebalance leg on the (testnet) exchange. Returns summary."""
        if self.auth is None:
            return {"placed": 0, "skipped": len(plan["legs"]), "errors": 0}
        placed = errors = skipped = 0
        for leg in plan["legs"]:
            s = leg["symbol"]
            px = float(leg["price"])             # forming-open (close-proxy) the leg sized at
            qty = self._round_qty(s, abs(leg["delta_notional_usd"]) / px)
            # POST-FLOOR min-notional guard: flooring qty to stepSize can drop the order below
            # Binance's $5 min-notional (-4164). Skip these dust legs (position stays <$5 off target).
            if qty <= 0 or qty * px < self.cfg.min_notional_usd:
                skipped += 1
                continue
            try:
                self._ensure_leverage(s)
                self.auth.place_market_order(s, leg["side"], qty)
                placed += 1
            except Exception as exc:
                errors += 1
                print(f"[portfolio] order {leg['side']} {s} x{qty} failed: {exc}")
        return {"placed": placed, "skipped": skipped, "errors": errors}

    def run_once(self, refresh: bool = True) -> dict:
        """One evaluation: refresh data, compute the plan, log it; place orders unless dry-run."""
        if refresh:
            self.refresh_data()
        # forming candle via close-proxy (built in compute_plan); current book from positions
        current = None if self.cfg.dry_run else self._actual_weights()
        plan = self.compute_plan(current_weights=current)
        mode = "DRY-RUN" if self.cfg.dry_run else ("TESTNET" if self.cfg.testnet else "LIVE")
        print(f"[portfolio:{mode}] rebalance plan as_of={plan['as_of']} "
              f"gross=${plan['gross_dollar']} target_gross={plan['target_gross']} "
              f"legs={plan['n_rebalance_legs']} rebal=${plan['rebalance_notional_usd']}")
        for leg in plan["legs"]:
            print(f"    {leg['side']:4} {leg['symbol']:14} "
                  f"w {leg['current_w']:+.4f}->{leg['target_w']:+.4f} "
                  f"${leg['delta_notional_usd']:+.2f}")
        if self.cfg.dry_run:
            self._save_held(plan["_new_held"])   # treat plan as filled (paper book)
        else:
            res = self.execute(plan)
            print(f"[portfolio:{mode}] orders placed={res['placed']} "
                  f"skipped={res['skipped']} errors={res['errors']}")
            self._save_held(plan["_new_held"])
        return plan

    def run(self) -> None:
        """Poll loop: act once per new 8h candle close on the reference symbol."""
        mode = "DRY-RUN" if self.cfg.dry_run else ("TESTNET" if self.cfg.testnet else "LIVE")
        print(f"[portfolio:{mode}] entering poll loop (every {self.cfg.poll_interval_seconds}s); "
              f"equity=${self.cfg.equity_usd} lev={self.cfg.leverage}x band={self.cfg.delta}")
        if not self.cfg.dry_run:
            self.setup_exchange()             # load quantityPrecision; leverage set lazily per leg
        last_key = f"portfolio_last_candle_{self.cfg.ref_symbol}"
        while True:
            last = self.store.get_state(last_key)
            last_ms = int(last) if last else None
            candle = data_pipeline.detect_new_candle(
                self.read_client, self.cfg.ref_symbol, self.cfg.interval, last_ms)
            if candle is not None:
                self.run_once(refresh=True)
                self.store.set_state(last_key, str(candle.open_time))
            time.sleep(self.cfg.poll_interval_seconds)
