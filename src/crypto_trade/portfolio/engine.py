"""PortfolioEngine — live executor for baseline-v2 (trend+carry+hysteresis), DRY-RUN first.

Every 8h candle close: refresh klines + funding for the full candidate universe -> compute the
upcoming-candle target weights via the SAME backtest code (strategy.next_target_weights) -> diff vs
current holdings -> apply the hysteresis band (delta=0.010) vs ACTUAL held weights -> produce a
rebalance plan. In DRY-RUN the plan is LOGGED (no orders) and treated as filled (held_w persisted),
so we can verify live decisions track the backtest before any order is placed.

Parity contract:
- target weights come from strategy.next_target_weights (machine-precision parity with iter_020).
- act on candle CLOSE[t] (detect_new_candle on a reference symbol) -> rebalance at next open.
- gross dollar = sum |target_w| * equity * leverage; the weights already carry the vol-target scale.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

from crypto_trade.client import BinanceClient
from crypto_trade.live import data_pipeline
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
        # klines always from production (parity with backtest data source)
        self.kline_client = BinanceClient(base_url=settings.base_url)
        self.store = StateStore(Path(config.db_path))

    # ---- held-weight persistence (the hysteresis band's path-dependent state) ----
    def _load_held(self) -> dict:
        raw = self.store.get_state(_held_key(self.cfg))
        return json.loads(raw) if raw else {}

    def _save_held(self, held: dict) -> None:
        self.store.set_state(_held_key(self.cfg), json.dumps(held))

    # ---- the core: compute the rebalance plan for the upcoming candle ----
    def compute_plan(self, current_weights: dict | None = None) -> dict:
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
        tgt = strategy.next_target_weights(coins, delta=self.cfg.delta)
        meta = tgt.pop("_meta")
        cur = dict(current_weights if current_weights is not None else self._load_held())
        gross_dollar = self.cfg.equity_usd * self.cfg.leverage

        all_syms = set(tgt) | set(cur)
        legs = []
        new_held = {}
        for s in sorted(all_syms):
            t = float(tgt.get(s, 0.0))            # backtest deployed weight for the upcoming candle
            c = float(cur.get(s, 0.0))            # what we actually hold now
            trade_w = t - c
            delta_notional = trade_w * gross_dollar
            if abs(delta_notional) >= self.cfg.min_notional_usd:
                legs.append({
                    "symbol": s,
                    "side": "BUY" if trade_w > 0 else "SELL",
                    "target_w": round(t, 6),
                    "current_w": round(c, 6),
                    "delta_notional_usd": round(delta_notional, 2),
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
            "vol_target_scale": round(meta["vol_target_scale"], 4),
            "target_gross": round(meta["gross"], 4),
            "n_target_positions": meta["n_positions"],
            "gross_dollar": round(gross_dollar, 2),
            "n_rebalance_legs": len(legs),
            "rebalance_notional_usd": round(sum(abs(x["delta_notional_usd"]) for x in legs), 2),
            "legs": legs,
            "_new_held": new_held,
        }

    def refresh_data(self) -> None:
        """Refresh klines + funding for the full candidate universe (PIT + carry parity)."""
        syms = strategy.candidate_symbols()
        data_pipeline.refresh_klines(self.kline_client, syms, self.cfg.interval, self.cfg.data_dir)
        funding.refresh_funding(syms, self.cfg.data_dir)

    def run_once(self, refresh: bool = True) -> dict:
        """One evaluation: optionally refresh data, compute + log the plan. No orders in dry-run."""
        if refresh:
            self.refresh_data()
        plan = self.compute_plan()
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
        return plan

    def run(self) -> None:
        """Poll loop: act once per new 8h candle close on the reference symbol."""
        mode = "DRY-RUN" if self.cfg.dry_run else ("TESTNET" if self.cfg.testnet else "LIVE")
        print(f"[portfolio:{mode}] entering poll loop (every {self.cfg.poll_interval_seconds}s); "
              f"equity=${self.cfg.equity_usd} lev={self.cfg.leverage}x band={self.cfg.delta}")
        last_key = f"portfolio_last_candle_{self.cfg.ref_symbol}"
        while True:
            last = self.store.get_state(last_key)
            last_ms = int(last) if last else None
            candle = data_pipeline.detect_new_candle(
                self.kline_client, self.cfg.ref_symbol, self.cfg.interval, last_ms)
            if candle is not None:
                self.run_once(refresh=True)
                self.store.set_state(last_key, str(candle.open_time))
            time.sleep(self.cfg.poll_interval_seconds)
