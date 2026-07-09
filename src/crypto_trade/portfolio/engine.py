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
import re
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
    delta: float = strategy.DELTA  # hysteresis band (SNAP)
    interval: str = "8h"
    ref_symbol: str = "BTCUSDT"  # candle-close trigger reference
    min_notional_usd: float = 5.0  # skip dust legs (Binance min-notional is ~5 USDT)
    # BUFFER on the post-floor min-notional guard: a leg sized at the close-proxy price just ABOVE
    # the MIN_NOTIONAL floor can still be REJECTED (-4164) if the price drifts down before the
    # staggered order executes (the notional is re-evaluated at execution). Skip legs within this
    # multiple of the floor so a normal ~15-min price move can't push them below it. 1.0 = off.
    min_notional_buffer: float = 1.20
    poll_interval_seconds: int = 60
    data_dir: str = "data"
    db_path: str = "data/portfolio_dry_run.db"
    dry_run: bool = True
    testnet: bool = False
    # PAPER-FALLBACK: when a real order fails with a testnet-untradeable code (symbol not listed /
    # not openable / thin-book PERCENT_PRICE on testnet), track that symbol as a PAPER position
    # instead of dropping the leg — so the live book stays faithful to the strategy target (no MISSING
    # drift, no net tilt from un-placed legs). TESTNET-ONLY convenience; OFF by default (v1 + production
    # place real orders only). On production the strategy should hold real positions, not paper.
    paper_untradeable: bool = False
    # DATA-INTEGRITY GUARD: min ACTIVE coins (at the latest candle) required to rebalance. A partial
    # or stale kline refresh (a Binance 418 rate-limit ban mid-refresh) collapses the universe
    # to a handful -> the rank book degenerates into a few oversized, non-neutral positions. Below
    # this floor the engine REFUSES to rebalance (raises -> poll loop logs + retries) rather than
    # trade a corrupted book. Normal is hundreds; a collapse is tens. 0 disables.
    min_active_universe: int = 100
    # PRIMARY data-integrity guard (load-bearing): min FRACTION of the candidate universe that must
    # refresh OK to rebalance. A 418 ban mid-refresh drops most coins (logged "skipped"); even when
    # the active count stays > min_active_universe, the partial fetch leaves GAPS in trailing candles
    # that break per-bar SEASONING -> the eligible rank set collapses -> degenerate book. If ok/total
    # is below this fraction the engine REFUSES to rebalance (raises -> retries). Normal ~99% ok.
    # 0 disables; the v2 runner sets 0.80. Real/testnet only.
    min_refresh_fraction: float = 0.0
    # STAGGER: seconds to delay the rebalance PAST the candle close, so this engine's kline refresh
    # doesn't collide with the other engines all refreshing at the 8h boundary (the cause of the 418
    # rate-limit contention). Parity-safe (same just-closed-candle signal, executed later). 0 = fire
    # at the boundary (default). The v2 runner sets 900 (15 min).
    rebalance_lag_seconds: int = 0


# PERMANENT untradeability — paper on the FIRST failure (retrying can't help here): -1121 invalid
# symbol, -4141 symbol closed/not-listed (e.g. TLM: prod-listed, absent on testnet), -4140 invalid
# status for opening, -4411 TradFi agreement, -4061/-4046 position-side/leverage quirks.
_PERMANENT_UNTRADEABLE = {"-1121", "-4140", "-4411", "-4061", "-4046", "-4141"}
# TRANSIENT — a MOMENTARY thin-book rejection, NOT permanent: -4131 PERCENT_PRICE (implied price
# exceeded the band because the book was thin THAT tick). Retried; papered only after PAPER_STRIKE_N
# consecutive failures, so a one-off doesn't permanently freeze a liquid symbol (LINK/HEI were
# wrongly papered forever on a single -4131 before v20).
_TRANSIENT_UNTRADEABLE = {"-4131"}
PAPER_STRIKE_N = 3
# Subset surfacing at set_leverage that means the SYMBOL genuinely can't be traded (all PERMANENT).
# EXCLUDES -4046/-4061 (from set_leverage they're benign "leverage already set" quirks — must fall
# through to the order, not paper a tradeable symbol).
_LEVERAGE_UNTRADEABLE = {"-4141", "-1121", "-4140"}


def _held_key(cfg: PortfolioConfig) -> str:
    return "portfolio_held_w"


def _err_code(exc: Exception) -> str | None:
    m = re.search(r'"code":(-?\d+)', str(exc))
    return m.group(1) if m else None


class PortfolioEngine:
    def __init__(self, config: PortfolioConfig, settings, strategy_module=None):
        self.cfg = config
        self.settings = settings
        # Dependency-injected weight engine (the strategy interface the engine calls). Default = the
        # v1 `strategy` module -> v1 behavior is bit-identical when the param is omitted. The v2
        # live executor passes `crypto_trade.portfolio_v2.strategy_v2` (drop-in, same surface).
        self.strat = strategy_module if strategy_module is not None else strategy
        # klines always from production (parity with backtest data source). kline_client (bulk
        # incremental refresh) vs read_client (limit=2 for candle-detect + forming-open polls).
        self.kline_client = BinanceClient(base_url=settings.base_url)
        self.read_client = BinanceClient(base_url=settings.base_url, limit=2)
        self.store = StateStore(Path(config.db_path))
        # signed client (orders/positions/leverage) — testnet routing via auth_base_url; only when
        # we will actually trade. klines stay on production base_url for full history (parity).
        self.auth: AuthenticatedBinanceClient | None = None
        self.qty_prec: dict[str, int] = {}
        self.step_size: dict[str, float] = {}  # LOT_SIZE stepSize per symbol (qty multiple)
        self.min_notl: dict[str, float] = {}  # MIN_NOTIONAL filter per symbol ($ floor; -4164)
        self._lev_set: set[str] = set()  # symbols whose leverage we've already set
        self._paper_strikes: dict[
            str, int
        ] = {}  # per-symbol consecutive transient (-4131) failures
        if not config.dry_run and settings.binance_api_key:
            auth_url = settings.auth_base_url or settings.base_url
            self.auth = AuthenticatedBinanceClient(
                api_key=settings.binance_api_key,
                api_secret=settings.binance_api_secret,
                base_url=auth_url,
            )
            mode = "TESTNET" if config.testnet else "LIVE"
            print(f"[portfolio:{mode}] AUTH endpoint: {auth_url}")
            if config.paper_untradeable and not config.testnet:
                print(
                    "[portfolio] SAFETY: paper_untradeable=True ignored on PRODUCTION (real money) — "
                    "the paper-fallback is testnet-only; every leg trades for real here."
                )
            elif config.paper_untradeable:
                print(
                    "[portfolio] paper-fallback ON (testnet): untradeable symbols tracked as paper"
                )

    # ---- held-weight persistence (the hysteresis band's path-dependent state) ----
    def _load_held(self) -> dict:
        raw = self.store.get_state(_held_key(self.cfg))
        return json.loads(raw) if raw else {}

    def _save_held(self, held: dict) -> None:
        self.store.set_state(_held_key(self.cfg), json.dumps(held))

    # ---- paper-fallback state (testnet-untradeable symbols tracked as paper, not on the exchange) --
    def _load_paper(self) -> tuple[set, dict]:
        """(paper_symbols, paper_held_weights). Symbols that failed to trade on testnet → papered, so
        the strategy holds its full intended book; their weights are tracked here, not on the venue."""
        raw = self.store.get_state("portfolio_paper")
        d = json.loads(raw) if raw else {}
        return set(d.get("syms", [])), d.get("held", {})

    def _save_paper(self, syms: set, held: dict) -> None:
        self.store.set_state("portfolio_paper", json.dumps({"syms": sorted(syms), "held": held}))

    def _reconcile_paper_vs_positions(self) -> None:
        """Startup reconcile: a symbol must NOT be both papered AND holding a real position. If a
        papered symbol has a live position on the venue it IS tradeable (e.g. wrongly papered on a
        transient -4131 before v20 — LINK/HEI/SIREN were frozen this way), so UN-STICK it: drop it
        from the paper set so the next rebalance manages that real position back toward target.
        Genuinely-untradeable papered symbols (no real position, e.g. TLM) are left papered."""
        if not self._paper_enabled() or self.auth is None:
            return
        syms, held = self._load_paper()
        if not syms:
            return
        real = {
            p["symbol"]
            for p in self.auth.get_positions()
            if float(p.get("positionAmt", 0) or 0) != 0
        }
        stuck = syms & real
        if not stuck:
            return
        syms -= stuck
        held = {s: w for s, w in held.items() if s not in stuck}
        for s in stuck:
            self._paper_strikes.pop(s, None)
        self._save_paper(syms, held)
        print(
            f"[portfolio] paper reconcile: un-stuck {len(stuck)} papered sym(s) holding a live "
            f"position (now strategy-managed again): {', '.join(sorted(stuck))}"
        )

    def _paper_enabled(self) -> bool:
        """The paper-fallback is allowed ONLY on TESTNET (and only when explicitly opted in, live mode).
        HARD SAFETY: never on production (real money) — papering a position you don't actually hold
        would fabricate P&L. `testnet` is the load-bearing guard; `paper_untradeable` is the opt-in."""
        return self.cfg.paper_untradeable and self.cfg.testnet and not self.cfg.dry_run

    # ---- the core: compute the rebalance plan for the upcoming candle ----
    def compute_plan(
        self, current_weights: dict | None = None, forming_opens: dict | None = None
    ) -> dict:
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
        coins = self.strat.load_universe()
        # forming (hold) candle via NON-RAGGED close-proxy (every active coin) unless an override is
        # given. A partial network fetch ragged-collapses the book (the XLM-0.40 bug); close[last]
        # is a < 0.01% proxy for open[H] -> relative weights bit-exact, gross off < 0.1%.
        if forming_opens is None:
            forming_opens = self.strat.forming_from_close(coins)
        # GUARD: refuse to rebalance on a collapsed active universe (partial/stale refresh -> ragged
        # panel -> degenerate book). The raise is caught by the poll loop (logged as a tick error,
        # last_candle NOT advanced) so the rebalance retries next tick on complete data.
        n_active = len(forming_opens)
        if (
            not self.cfg.dry_run
            and self.cfg.min_active_universe
            and n_active < self.cfg.min_active_universe
        ):
            raise RuntimeError(
                f"active universe collapsed to {n_active} coins "
                f"(< {self.cfg.min_active_universe}); refusing to rebalance on a ragged panel"
            )
        prices = {s: float(px) for s, (_, px) in forming_opens.items()}
        coins = self.strat.append_forming(coins, forming_opens)
        tgt = self.strat.next_target_weights(coins, delta=self.cfg.delta)
        meta = tgt.pop("_meta")
        cur = dict(current_weights if current_weights is not None else self._load_held())
        gross_dollar = self.cfg.equity_usd  # notional base; leverage only affects margin

        all_syms = set(tgt) | set(cur)
        legs = []
        new_held = {}
        for s in sorted(all_syms):
            t = float(tgt.get(s, 0.0))  # backtest deployed weight for the upcoming candle
            c = float(cur.get(s, 0.0))  # what we actually hold now
            trade_w = t - c
            delta_notional = trade_w * gross_dollar
            if abs(delta_notional) >= self._min_notional(s) and s in prices:
                legs.append(
                    {
                        "symbol": s,
                        "side": "BUY" if trade_w > 0 else "SELL",
                        "target_w": round(t, 6),
                        "current_w": round(c, 6),
                        "delta_notional_usd": round(delta_notional, 2),
                        "price": prices[s],
                    }
                )
                held_w = t  # traded to target
            else:
                held_w = c  # below min-notional: can't trade, keep current
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
        syms = self.strat.candidate_symbols()
        ok = skipped = 0
        for s in syms:
            try:
                fetch_symbol_interval(self.kline_client, data_dir, s, self.cfg.interval)
                ok += 1
            except Exception:
                skipped += 1  # delisted / unavailable on production fapi
        print(f"[portfolio] klines refreshed: {ok} ok, {skipped} skipped (delisted)")
        # expose refresh completeness for the run_once data-integrity guard. NOTE: a transient fetch
        # failure (Binance 418 rate-limit ban) is caught above as "skipped" too, so a low ok-count is
        # the direct signal of a PARTIAL refresh (not just genuine delistings).
        self._last_refresh_ok = ok
        self._last_refresh_total = len(syms)
        funding.refresh_funding(syms, self.cfg.data_dir)

    # ---- live execution plumbing (reuses the proven AuthenticatedBinanceClient) ----
    def setup_exchange(self) -> None:
        """Load quantityPrecision + stepSize + MIN_NOTIONAL (exchangeInfo) for valid orders."""
        if self.auth is None:
            return
        info = self.auth.get_exchange_info()
        for si in info.get("symbols", []):
            sym = si["symbol"]
            self.qty_prec[sym] = int(si["quantityPrecision"])
            for f in si.get("filters", []):
                ft = f.get("filterType")
                if ft in ("LOT_SIZE", "MARKET_LOT_SIZE") and sym not in self.step_size:
                    self.step_size[sym] = float(f["stepSize"])  # qty must be a multiple of this
                elif ft == "MIN_NOTIONAL":
                    self.min_notl[sym] = float(f.get("notional") or f.get("minNotional") or 0.0)
        print(
            f"[portfolio] loaded quantityPrecision + stepSize + MIN_NOTIONAL "
            f"for {len(self.qty_prec)} symbols"
        )

    def _min_notional(self, symbol: str) -> float:
        """Largest of the configured floor and the symbol's Binance MIN_NOTIONAL filter. Legs below
        this can't be placed (-4164 BTC=$50 etc.), so they're skipped (held at current — bounded by
        one filter-notional off target, inside parity tolerance, self-corrects next rebalance)."""
        return max(self.cfg.min_notional_usd, self.min_notl.get(symbol, 0.0))

    def _ensure_leverage(self, symbol: str) -> bool:
        """Set leverage on a symbol once (lazily, before its first order). Returns False if the
        symbol is UNTRADEABLE on the venue — set_leverage returned a code in _LEVERAGE_UNTRADEABLE
        (e.g. -4141 'Symbol is closed' for a prod-listed name absent from testnet). The caller then
        papers/skips it, rather than proceeding to an order that fails downstream with a -1111
        precision cascade. Benign leverage quirks (already-set, etc.) still return True."""
        if self.auth is None or symbol in self._lev_set:
            return True
        try:
            self.auth.set_leverage(symbol, max(1, int(round(self.cfg.leverage))))
        except Exception as exc:
            print(f"[portfolio] set_leverage {symbol} failed: {exc}")
            if _err_code(exc) in _LEVERAGE_UNTRADEABLE:
                return (
                    False  # symbol can't be traded here — do NOT mark _lev_set; caller handles it
                )
        self._lev_set.add(symbol)
        return True

    def _actual_weights(self) -> dict:
        """Current per-coin weight from positions: positionAmt*markPrice / (equity*leverage)."""
        if self.auth is None:
            return self._load_held()
        gross_dollar = self.cfg.equity_usd  # notional base (matches compute_plan)
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
            qty = (qty // step) * step  # floor to a stepSize multiple
        return round(qty, prec)  # clean float artifacts to the allowed precision

    def execute(
        self, plan: dict, paper_syms: set | None = None, strikes: dict | None = None
    ) -> dict:
        """Place a MARKET order per rebalance leg on the (testnet) exchange. Returns summary.

        Legs whose symbol is already a known paper symbol are NOT sent (papered). When the
        paper-fallback is on, a leg that FAILS with a PERMANENT untradeable code is papered
        immediately; a TRANSIENT code (-4131 thin-book) is RETRIED and papered only after
        PAPER_STRIKE_N consecutive failures, so a one-off doesn't freeze a liquid symbol.
        `strikes` (per-symbol transient-failure counts) is mutated in place; a fill clears it.
        """
        if self.auth is None:
            return {
                "placed": 0,
                "skipped": len(plan["legs"]),
                "errors": 0,
                "papered": 0,
                "retrying": 0,
                "new_paper": set(),
            }
        paper_syms = paper_syms or set()
        strikes = strikes if strikes is not None else {}
        placed = errors = skipped = papered = retrying = 0
        new_paper: set = set()
        for leg in plan["legs"]:
            s = leg["symbol"]
            if s in paper_syms:  # already a paper symbol — track, don't send
                papered += 1
                continue
            px = float(leg["price"])  # forming-open (close-proxy) the leg sized at
            qty = self._round_qty(s, abs(leg["delta_notional_usd"]) / px)
            # POST-FLOOR min-notional guard: flooring qty to stepSize can drop the order below the
            # symbol's MIN_NOTIONAL filter (-4164; BTC=$50). Skip these dust legs (held at current).
            # The BUFFER absorbs price drift between the close-proxy sizing and the staggered
            # execution (a leg just above the floor at plan time can be re-evaluated below it and
            # rejected -4164). Skipped legs are bounded by one filter-notional off target — inside
            # parity tolerance, self-correct next rebalance.
            if qty <= 0 or qty * px < self._min_notional(s) * self.cfg.min_notional_buffer:
                skipped += 1
                continue
            try:
                if not self._ensure_leverage(s):
                    # untradeable at set_leverage (PERMANENT, e.g. -4141 not-listed). Paper it on
                    # testnet so the book keeps its weight; on production skip as an error leg
                    # (papering a real position would fabricate P&L).
                    if self._paper_enabled():
                        new_paper.add(s)
                        papered += 1
                        strikes.pop(s, None)
                        print(
                            f"[portfolio] PAPER-FALLBACK {s} (untradeable at set_leverage) — paper"
                        )
                    else:
                        errors += 1
                        print(f"[portfolio] {s} untradeable on venue (set_leverage) — leg skipped")
                    continue
                self.auth.place_market_order(s, leg["side"], qty)
                placed += 1
                strikes.pop(s, None)  # a fill clears any transient strike streak
            except Exception as exc:
                code = _err_code(exc)
                if self._paper_enabled() and code in _PERMANENT_UNTRADEABLE:
                    new_paper.add(s)
                    papered += 1
                    strikes.pop(s, None)
                    print(f"[portfolio] PAPER-FALLBACK {s} (permanent {code}) — paper")
                elif self._paper_enabled() and code in _TRANSIENT_UNTRADEABLE:
                    strikes[s] = strikes.get(s, 0) + 1
                    if strikes[s] >= PAPER_STRIKE_N:
                        new_paper.add(s)
                        papered += 1
                        strikes.pop(s, None)
                        print(
                            f"[portfolio] PAPER-FALLBACK {s} (transient {code} x{PAPER_STRIKE_N} "
                            f"consecutive) — tracking as paper"
                        )
                    else:
                        retrying += 1
                        print(
                            f"[portfolio] {leg['side']} {s} transient {code} "
                            f"(strike {strikes[s]}/{PAPER_STRIKE_N}) — retry next rebalance"
                        )
                else:
                    errors += 1
                    print(f"[portfolio] order {leg['side']} {s} x{qty} failed: {exc}")
        return {
            "placed": placed,
            "skipped": skipped,
            "errors": errors,
            "papered": papered,
            "retrying": retrying,
            "new_paper": new_paper,
        }

    def run_once(self, refresh: bool = True) -> dict:
        """One evaluation: refresh data, compute the plan, log it; place orders unless dry-run."""
        if refresh:
            self.refresh_data()
            # GUARD: refuse to rebalance on a PARTIAL refresh (a 418 rate-limit ban dropped most coins
            # -> ragged panel -> broken seasoning -> degenerate book). The raise is caught by the poll
            # loop (last_candle NOT advanced) so it retries next tick once the contention clears.
            ok, total = self._last_refresh_ok, self._last_refresh_total
            if (
                not self.cfg.dry_run
                and self.cfg.min_refresh_fraction
                and total
                and ok < self.cfg.min_refresh_fraction * total
            ):
                raise RuntimeError(
                    f"refresh incomplete: {ok}/{total} coins ok "
                    f"(< {self.cfg.min_refresh_fraction:.0%}); rate-limit/partial fetch — "
                    f"refusing to rebalance on a ragged panel"
                )
        # paper-fallback state (testnet-untradeable symbols we track as paper, not on the venue)
        paper_on = self._paper_enabled()
        paper_syms, paper_held = self._load_paper() if paper_on else (set(), {})
        # forming candle via close-proxy (built in compute_plan); current book from positions, with
        # the paper symbols merged in at their tracked weight so the strategy holds its FULL book.
        if self.cfg.dry_run:
            current = None
        else:
            current = self._actual_weights()
            if paper_on:
                current = {**current, **paper_held}
        plan = self.compute_plan(current_weights=current)
        mode = "DRY-RUN" if self.cfg.dry_run else ("TESTNET" if self.cfg.testnet else "LIVE")
        print(
            f"[portfolio:{mode}] rebalance plan as_of={plan['as_of']} "
            f"gross=${plan['gross_dollar']} target_gross={plan['target_gross']} "
            f"legs={plan['n_rebalance_legs']} rebal=${plan['rebalance_notional_usd']}"
        )
        for leg in plan["legs"]:
            print(
                f"    {leg['side']:4} {leg['symbol']:14} "
                f"w {leg['current_w']:+.4f}->{leg['target_w']:+.4f} "
                f"${leg['delta_notional_usd']:+.2f}"
            )
        if self.cfg.dry_run:
            self._save_held(plan["_new_held"])  # treat plan as filled (paper book)
        else:
            res = self.execute(plan, paper_syms=paper_syms, strikes=self._paper_strikes)
            extra = f" retrying={res['retrying']} papered={res['papered']}" if paper_on else ""
            print(
                f"[portfolio:{mode}] orders placed={res['placed']} "
                f"skipped={res['skipped']} errors={res['errors']}{extra}"
            )
            self._save_held(plan["_new_held"])
            if paper_on:
                paper_syms = paper_syms | res["new_paper"]
                # the paper symbols' intended (target) weights, from the plan's would-be held book
                paper_held = {
                    s: plan["_new_held"].get(s, 0.0)
                    for s in paper_syms
                    if abs(plan["_new_held"].get(s, 0.0)) > 1e-9
                }
                self._save_paper(paper_syms, paper_held)
        return plan

    def _interval_ms(self) -> int:
        """Candle interval in ms, parsed from cfg.interval (e.g. '8h' -> 28_800_000)."""
        s = self.cfg.interval
        return int(s[:-1]) * {"m": 60, "h": 3600, "d": 86400}[s[-1]] * 1000

    def run(self) -> None:
        """Poll loop: act once per new 8h candle close on the reference symbol."""
        mode = "DRY-RUN" if self.cfg.dry_run else ("TESTNET" if self.cfg.testnet else "LIVE")
        print(
            f"[portfolio:{mode}] entering poll loop (every {self.cfg.poll_interval_seconds}s); "
            f"equity=${self.cfg.equity_usd} lev={self.cfg.leverage}x band={self.cfg.delta}"
        )
        if not self.cfg.dry_run:
            self.setup_exchange()  # load quantityPrecision; leverage set lazily per leg
            try:
                self._reconcile_paper_vs_positions()  # un-stick papered symbols that hold real legs
            except Exception as exc:  # never let a reconcile hiccup block startup
                print(f"[portfolio] paper reconcile skipped: {type(exc).__name__}: {exc}")
        last_key = f"portfolio_last_candle_{self.cfg.ref_symbol}"
        consecutive_errors = 0
        announced_lag_for = None  # candle open_time we've already logged a "staggered" notice for
        while True:
            try:
                last = self.store.get_state(last_key)
                last_ms = int(last) if last else None
                candle = data_pipeline.detect_new_candle(
                    self.read_client, self.cfg.ref_symbol, self.cfg.interval, last_ms
                )
                if candle is not None:
                    # STAGGER: hold the rebalance until `rebalance_lag_seconds` PAST the candle close,
                    # so the kline refresh doesn't collide with the other engines all refreshing at the
                    # 8h boundary (the Binance 418 rate-limit contention). Parity-safe: the rebalance
                    # still uses THIS just-closed candle's signal — same target, just executed later.
                    # Non-blocking: keep polling; last_candle only advances after the rebalance fires.
                    due_ms = (
                        candle.open_time
                        + self._interval_ms()
                        + self.cfg.rebalance_lag_seconds * 1000
                    )
                    if int(time.time() * 1000) >= due_ms:
                        self.run_once(refresh=True)
                        self.store.set_state(last_key, str(candle.open_time))
                        announced_lag_for = None
                    elif announced_lag_for != candle.open_time:
                        wait_min = (due_ms - int(time.time() * 1000)) / 60000
                        print(
                            f"[portfolio:{mode}] new candle closed; staggering rebalance "
                            f"~{wait_min:.0f}min (lag={self.cfg.rebalance_lag_seconds}s) to avoid "
                            f"boundary kline-refresh contention"
                        )
                        announced_lag_for = candle.open_time
                consecutive_errors = 0
            except Exception as exc:
                # RESILIENCE: a transient error (network reset, API hiccup, kline fetch failure)
                # must NOT kill the long-running engine. Log a ONE-LINER (no stack trace, so the
                # monitor's `Traceback` alarm stays reserved for genuine bugs) and retry next poll.
                # last_key only advances after a SUCCESSFUL run_once, so a missed candle is simply
                # re-detected and the rebalance retried on the next tick — no rebalance is lost.
                consecutive_errors += 1
                print(
                    f"[portfolio:{mode}] tick error #{consecutive_errors} "
                    f"({type(exc).__name__}: {exc}); retrying in {self.cfg.poll_interval_seconds}s"
                )
            time.sleep(self.cfg.poll_interval_seconds)
