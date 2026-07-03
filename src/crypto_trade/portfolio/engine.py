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

# On a Binance rate-limit ban (418 / -1003) the poll waits this long before retrying — re-hitting a
# banned IP ESCALATES the ban, so back off well past a typical ban (minutes), not the 60s poll.
RATE_LIMIT_BACKOFF = 900  # 15 min

# Binance business-logic order errors a retry cannot fix (bad request, not a transient outage) —
# never resend on these. All are NEGATIVE codes, so a "-NNNN" substring can't collide with a digit
# run inside a URL/timestamp/quantity that a 5xx error body may echo.
TERMINAL_ORDER_CODES = ("-1121", "-4164", "-2019", "-1111", "-1013", "-4003", "-1102", "-4061")
# Rate-limit business codes (also negative) — do NOT retry inside a rebalance (hammering a banned IP
# escalates the ban); the poll loop's RATE_LIMIT_BACKOFF handles these higher up. HTTP 418/429 are
# detected via status code, not substring (a bare "429" could match a timestamp in a 5xx body).
RATE_LIMIT_CODES = ("-1003", "-1015")


def _order_error_kind(exc: Exception) -> str:
    """Classify a place_market_order failure: 'terminal' (don't retry), 'ratelimit' (don't retry),
    or 'transient' (retry with position reconcile). Prefers the HTTP status code (httpx) so a bare
    418/429 in a 5xx error body's echoed URL can't cause a misclassification. Unknown / network
    errors default to transient — safe because the retry reconciles to the live position and trades
    only the remaining gap (never double-fills)."""
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status in (418, 429):
        return "ratelimit"
    if status is not None and status >= 500:
        return "transient"  # 5xx gateway/server outage — ambiguous, reconcile makes the retry safe
    if status is not None and 400 <= status < 500:
        # any other 4xx is a Binance business reject (bad param/precision/notional) — a retry can't
        # fix it. Covers codes beyond TERMINAL_ORDER_CODES (e.g. -1100/-4011/-4001) without a list.
        return "terminal"
    msg = repr(exc).lower()
    if any(c in msg for c in RATE_LIMIT_CODES) or "too many requests" in msg:
        return "ratelimit"
    if any(c in msg for c in TERMINAL_ORDER_CODES):  # 4xx Binance reject with a negative code
        return "terminal"
    return "transient"


@dataclasses.dataclass(frozen=True)
class PortfolioConfig:
    equity_usd: float = 10_000.0
    leverage: float = 1.0
    delta: float = strategy.DELTA  # hysteresis band (SNAP)
    interval: str = "8h"
    ref_symbol: str = "BTCUSDT"  # candle-close trigger reference
    min_notional_usd: float = 5.0  # skip dust legs (Binance min-notional is ~5 USDT)
    poll_interval_seconds: int = 60
    data_dir: str = "data"
    db_path: str = "data/portfolio_dry_run.db"
    dry_run: bool = True
    testnet: bool = False
    # Panel-completeness guard: at an 8h boundary some symbols' new candle can lag / their fetch
    # can transiently error (production API load at 00/08/16:00). Rebalancing on that incomplete
    # cross-section ranks marginal names differently and carries a slightly-off book until the next
    # 8h rebalance. So require >= this fraction of the universe to fetch OK before rebalancing;
    # otherwise wait panel_retry_wait_s and re-fetch, up to panel_max_retries, then proceed anyway.
    min_panel_ok_fraction: float = 0.95  # steady-state is ~2/513 skipped (0.4%); 40 skipped = 7.8%
    panel_retry_wait_s: int = 20
    panel_max_retries: int = 6  # ~2min max wait — bounded so the loop never hangs
    # Order-retry guard: a MARKET leg can fail on a transient venue error (502 / timeout / 5xx) the
    # matching engine may or may not have received. Rather than blindly resend (which double-fills
    # if the failed order actually landed), the retry RECONCILES against the live position, trading
    # only the remaining gap to target — idempotent by construction. Terminal errors
    # (-1121/-4164/-2019/-1111/-1013) and rate-limits (418/429/-1003) are NOT retried.
    order_max_retries: int = 3
    order_retry_wait_s: int = 2


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
        self.step_size: dict[str, float] = {}  # LOT_SIZE stepSize per symbol (qty multiple)
        self.min_notl: dict[str, float] = {}  # MIN_NOTIONAL filter per symbol ($ floor; -4164)
        self._lev_set: set[str] = set()  # symbols whose leverage we've already set
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
        gross_dollar = self.cfg.equity_usd  # notional base; leverage only affects margin

        all_syms = set(tgt) | set(cur)
        legs = []
        new_held = {}
        for s in sorted(all_syms):
            t = float(tgt.get(s, 0.0))  # backtest deployed weight for the upcoming candle
            c = float(cur.get(s, 0.0))  # what we actually hold now
            trade_w = t - c
            delta_notional = trade_w * gross_dollar
            # include EVERY target coin in the book (held_w) — even ones this venue can't trade yet;
            # those are PAPERED at execution (testnet) so the book stays the full strategy target.
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

    def refresh_data(self) -> tuple[int, int]:
        """Refresh klines + funding for the full candidate universe (PIT + carry parity).

        Per-symbol tolerant: a coin delisted from production fapi (400 on /klines) keeps its on-disk
        CSV (parity with the backtest view) and is skipped — one dead symbol must not abort the run.
        Returns (ok, skipped) so the caller can gate rebalancing on panel completeness.
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
                skipped += 1  # delisted / unavailable on production fapi
        print(f"[portfolio] klines refreshed: {ok} ok, {skipped} skipped (delisted)")
        funding.refresh_funding(syms, self.cfg.data_dir)
        return ok, skipped

    def refresh_data_complete(self) -> tuple[int, int]:
        """refresh_data + panel-completeness guard: retry the refresh while too many symbols fail,
        so lagging boundary candles / transient fetch errors have time to clear before we rebalance
        on a degraded cross-section. Bounded by panel_max_retries so the poll loop never hangs; on
        exhaustion it proceeds on the best panel obtained (logged) — next 8h rebalance corrects."""
        ok, skipped = self.refresh_data()
        total = ok + skipped
        if total == 0:
            return ok, skipped
        for attempt in range(1, self.cfg.panel_max_retries + 1):
            if ok >= self.cfg.min_panel_ok_fraction * total:
                return ok, skipped
            print(
                f"[portfolio] DEGRADED PANEL: {ok}/{total} ok ({skipped} skipped, "
                f">{(1 - self.cfg.min_panel_ok_fraction) * 100:.0f}% missing) — waiting "
                f"{self.cfg.panel_retry_wait_s}s for candles to post (retry {attempt}/"
                f"{self.cfg.panel_max_retries}) before rebalancing"
            )
            time.sleep(self.cfg.panel_retry_wait_s)
            ok, skipped = self.refresh_data()
            total = ok + skipped
        if ok < self.cfg.min_panel_ok_fraction * total:
            print(
                f"[portfolio] WARNING: panel still degraded after {self.cfg.panel_max_retries} "
                f"retries ({ok}/{total} ok) — rebalancing on best available; next 8h corrects"
            )
        return ok, skipped

    # ---- live execution plumbing (reuses the proven AuthenticatedBinanceClient) ----
    def setup_exchange(self) -> None:
        """Load quantityPrecision + stepSize + MIN_NOTIONAL (exchangeInfo) for valid orders.
        ONLY status=='TRADING' symbols are registered — a listed-but-not-yet-trading symbol
        (PENDING_TRADING / SETTLING / PRE_TRADING / BREAK) is rejected by the order endpoint with
        -1121 'Invalid symbol'. The production universe can include such a coin while this venue
        (testnet) hasn't opened it yet; it's skipped at plan + execution time via _tradable()."""
        if self.auth is None:
            return
        skipped = 0
        info = self.auth.get_exchange_info()
        for si in info.get("symbols", []):
            if si.get("status") != "TRADING":
                skipped += 1
                continue
            sym = si["symbol"]
            self.qty_prec[sym] = int(si["quantityPrecision"])
            for f in si.get("filters", []):
                ft = f.get("filterType")
                if ft in ("LOT_SIZE", "MARKET_LOT_SIZE") and sym not in self.step_size:
                    self.step_size[sym] = float(f["stepSize"])  # qty must be a multiple of this
                elif ft == "MIN_NOTIONAL":
                    self.min_notl[sym] = float(f.get("notional") or f.get("minNotional") or 0.0)
        print(
            f"[portfolio] loaded {len(self.qty_prec)} TRADING symbols "
            f"(precision/stepSize/MIN_NOTIONAL); {skipped} non-TRADING skipped"
        )

    def _tradable(self, symbol: str) -> bool:
        """True if the symbol is in TRADING status on the venue (registered in setup_exchange).
        With no exchange info loaded (paper / backtest), everything is tradable."""
        return (not self.qty_prec) or (symbol in self.qty_prec)

    def _min_notional(self, symbol: str) -> float:
        """Largest of the configured floor and the symbol's Binance MIN_NOTIONAL filter. Legs below
        this can't be placed (-4164 BTC=$50 etc.), so they're skipped (held at current — bounded by
        one filter-notional off target, inside parity tolerance, self-corrects next rebalance)."""
        return max(self.cfg.min_notional_usd, self.min_notl.get(symbol, 0.0))

    def _ensure_leverage(self, symbol: str) -> None:
        """Set leverage on a symbol once (lazily, before its first order)."""
        if self.auth is None or symbol in self._lev_set:
            return
        try:
            self.auth.set_leverage(symbol, max(1, int(round(self.cfg.leverage))))
            self._lev_set.add(symbol)  # only cache on success — a failed set stays retryable
        except Exception as exc:
            print(f"[portfolio] set_leverage {symbol} failed: {exc}")

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

    def _live_notional(self, symbol: str) -> float:
        """Signed USD notional currently held for symbol (positionAmt * markPrice), 0 if flat.
        Used by the order-retry reconcile to measure what actually filled after a failed leg."""
        for p in self.auth.get_positions(symbol):
            if p.get("symbol") != symbol:
                continue
            amt = float(p.get("positionAmt", 0) or 0)
            return amt * float(p.get("markPrice", 0) or 0)
        return 0.0

    def _place_leg_with_retry(self, leg: dict, gross_dollar: float) -> str:
        """Place one MARKET leg with a RECONCILE-based retry. Returns 'placed' | 'retried' |
        'reconciled' | 'error'.

        Idempotency: a transient venue failure (502 / timeout / 5xx) is ambiguous — the matching
        engine may or may not have received the order. So we NEVER blindly resend; on each retry we
        re-read the LIVE position and trade only the remaining gap to this symbol's target notional
        (target_w * gross_dollar). If the failed order actually landed, the gap is ~0 and we place
        nothing — no double-fill. Terminal errors + rate-limits are not retried (won't clear)."""
        s = leg["symbol"]
        px = float(leg["price"])  # forming-open (close-proxy) the leg was sized at
        target_notional = float(leg["target_w"]) * gross_dollar
        side = leg["side"]
        qty = self._round_qty(s, abs(leg["delta_notional_usd"]) / px)
        self._ensure_leverage(s)
        for attempt in range(self.cfg.order_max_retries + 1):  # 1 initial + N retries
            try:
                self.auth.place_market_order(s, side, qty)
                return "placed" if attempt == 0 else "retried"
            except Exception as exc:  # noqa: BLE001
                kind = _order_error_kind(exc)
                print(
                    f"[portfolio] order {side} {s} x{qty} failed (attempt "
                    f"{attempt + 1}/{self.cfg.order_max_retries + 1}, {kind}): {repr(exc)[:120]}"
                )
                if kind != "transient" or attempt >= self.cfg.order_max_retries:
                    return "error"
                time.sleep(self.cfg.order_retry_wait_s)
                # RECONCILE: recompute the remaining gap from the LIVE position (idempotent).
                try:
                    remaining = target_notional - self._live_notional(s)
                except Exception as rexc:  # noqa: BLE001 — can't verify fill; do NOT resend (double-fill risk)
                    print(
                        f"[portfolio] reconcile query for {s} failed ({repr(rexc)[:80]}) — "
                        "not resending; next 8h rebalance heals"
                    )
                    return "error"
                if abs(remaining) < self._min_notional(s):
                    print(
                        f"[portfolio] {s} reconciled to target (gap ${remaining:+.2f} "
                        f"< min-notional) after transient error — no resend"
                    )
                    return "reconciled"
                side = "BUY" if remaining > 0 else "SELL"
                qty = self._round_qty(s, abs(remaining) / px)
                if qty <= 0:
                    # gap >= min-notional but below stepSize resolution — can't place it; surface as
                    # error (not a false "reconciled" success). Sub-step residue heals if the target
                    # later moves enough to clear one stepSize.
                    print(f"[portfolio] {s} gap ${remaining:+.2f} below stepSize — cannot resize")
                    return "error"
        return "error"

    def execute(self, plan: dict) -> dict:
        """Place a MARKET order per rebalance leg on the (testnet) exchange. Returns summary.
        Transient per-leg failures are retried with a live-position reconcile (see
        _place_leg_with_retry) so a 502/timeout re-sends only the UNFILLED gap, no double-fill."""
        if self.auth is None:
            return {
                "placed": 0,
                "papered": 0,
                "skipped": len(plan["legs"]),
                "errors": 0,
                "retried": 0,
            }
        gross_dollar = float(plan.get("gross_dollar", self.cfg.equity_usd))
        placed = errors = skipped = papered = retried = 0
        for leg in plan["legs"]:
            s = leg["symbol"]
            if not self._tradable(s):
                # untradable on this venue (PENDING_TRADING etc. -> -1121). TESTNET: PAPER it — keep
                # in the book (held_w), place no order, so the book stays the full strategy target.
                # LIVE: production lists every target coin, so this is unexpected; skip defensively.
                if self.cfg.testnet:
                    papered += 1
                else:
                    skipped += 1
                continue
            px = float(leg["price"])  # forming-open (close-proxy) the leg sized at
            qty = self._round_qty(s, abs(leg["delta_notional_usd"]) / px)
            # POST-FLOOR min-notional guard: flooring qty to stepSize can drop the order below the
            # symbol's MIN_NOTIONAL filter (-4164; BTC=$50). Skip these dust legs (held at current).
            if qty <= 0 or qty * px < self._min_notional(s):
                skipped += 1
                continue
            outcome = self._place_leg_with_retry(leg, gross_dollar)
            if outcome == "placed":
                placed += 1
            elif outcome in ("retried", "reconciled"):
                placed += 1
                retried += 1  # recovered after a transient failure (retry or reconcile-to-target)
            else:
                errors += 1
        return {
            "placed": placed,
            "papered": papered,
            "skipped": skipped,
            "errors": errors,
            "retried": retried,
        }

    def run_once(self, refresh: bool = True) -> dict:
        """One evaluation: refresh data, compute the plan, log it; place orders unless dry-run."""
        if refresh:
            self.refresh_data_complete()  # guard: no rebalance on a partial/degraded kline fetch
        # forming candle via close-proxy (built in compute_plan); current book from positions
        current = None if self.cfg.dry_run else self._actual_weights()
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
            res = self.execute(plan)
            print(
                f"[portfolio:{mode}] orders placed={res['placed']} "
                f"papered={res.get('papered', 0)} skipped={res['skipped']} "
                f"errors={res['errors']} retried={res.get('retried', 0)}"
            )
            self._save_held(plan["_new_held"])
        return plan

    def run(self) -> None:
        """Poll loop: act once per new 8h candle close on the reference symbol."""
        mode = "DRY-RUN" if self.cfg.dry_run else ("TESTNET" if self.cfg.testnet else "LIVE")
        print(
            f"[portfolio:{mode}] entering poll loop (every {self.cfg.poll_interval_seconds}s); "
            f"equity=${self.cfg.equity_usd} lev={self.cfg.leverage}x band={self.cfg.delta}"
        )
        if not self.cfg.dry_run:
            self.setup_exchange()  # load quantityPrecision; leverage set lazily per leg
        last_key = f"portfolio_last_candle_{self.cfg.ref_symbol}"
        while True:
            # RESILIENT poll: a transient API error (418 rate-limit ban / 429 / network / 5xx) must
            # NOT crash the engine. The candle key only advances after a CLEAN run_once, so a failed
            # poll re-attempts the same candle. CRITICAL: on a RATE-LIMIT error (418/429/-1003) back
            # off HARD (RATE_LIMIT_BACKOFF) instead of re-hitting every poll — pounding a banned IP
            # ESCALATES the ban (extended on each request), so a 60s retry would perpetuate it.
            # Backing off lets the ban lapse, then the next poll rebalances.
            sleep_s = self.cfg.poll_interval_seconds
            try:
                last = self.store.get_state(last_key)
                last_ms = int(last) if last else None
                candle = data_pipeline.detect_new_candle(
                    self.read_client, self.cfg.ref_symbol, self.cfg.interval, last_ms
                )
                if candle is not None:
                    self.run_once(refresh=True)
                    self.store.set_state(last_key, str(candle.open_time))
            except Exception as exc:
                msg = repr(exc)
                rate_limited = any(t in msg for t in ("418", "429", "-1003", "too many requests"))
                sleep_s = RATE_LIMIT_BACKOFF if rate_limited else max(120, sleep_s)
                print(f"[portfolio] poll error (backoff {sleep_s}s, retry): {msg[:180]}")
            time.sleep(sleep_s)
