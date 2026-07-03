"""Order-retry guard: a transient MARKET-leg failure retries by RECONCILING to the live position,
so it re-sends only the unfilled gap and can NEVER double-fill.

Motivating incident (2026-07-03 00:00): a 502 Bad Gateway on SELL ADAUSDT left the leg unplaced
(engine skipped it, healed at the next 8h rebalance). This adds an in-rebalance retry that is safe
under the 502's ambiguity (the matching engine may or may not have received the order).
"""

import sys

sys.path.insert(0, "src")

import httpx
import pytest

LEG = {  # SELL ~$35 of ADA; target end-state = -0.06 * 4000 = -$240 notional
    "symbol": "ADAUSDT",
    "side": "SELL",
    "target_w": -0.06,
    "current_w": -0.051,
    "delta_notional_usd": -35.0,
    "price": 1.0,
}
GROSS = 4000.0


def _http_err(status: int, body: str = "") -> httpx.HTTPStatusError:
    # body deliberately echoes a URL with a 13-digit timestamp to prove the classifier keys off the
    # HTTP status, not a bare "429"/"418" substring that a timestamp could accidentally contain.
    req = httpx.Request("POST", "https://testnet.binancefuture.com/fapi/v1/order")
    resp = httpx.Response(status, request=req, text=body)
    url = "http://x/fapi/v1/order?symbol=ADAUSDT&quantity=216.0&timestamp=1783037150782"
    return httpx.HTTPStatusError(
        f"{status} err for POST /fapi/v1/order: {body} {url}", request=req, response=resp
    )


class _FakeAuth:
    def __init__(self, place_effects, notionals, raise_on_positions=False):
        self.place_effects = list(place_effects)  # per place call: None (fill) or Exception
        self.notionals = list(notionals)  # signed $ notional returned per get_positions call
        self.raise_on_positions = raise_on_positions
        self.place_calls = []  # (symbol, side, qty)
        self.pos_calls = 0

    def set_leverage(self, *a, **k):
        pass

    def place_market_order(self, symbol, side, qty, reduce_only=False):
        idx = len(self.place_calls)
        self.place_calls.append((symbol, side, qty))
        eff = self.place_effects[idx] if idx < len(self.place_effects) else None
        if isinstance(eff, Exception):
            raise eff
        return {"status": "FILLED"}

    def get_positions(self, symbol=None):
        if self.raise_on_positions:
            raise httpx.ConnectError("position query boom")
        i = self.pos_calls
        self.pos_calls += 1
        n = self.notionals[i] if i < len(self.notionals) else self.notionals[-1]
        return [
            {"symbol": symbol, "positionAmt": str(n), "markPrice": "1"}
        ]  # mark=1 -> notional=amt


def _engine(tmp_path, monkeypatch, auth):
    from crypto_trade.config import load_settings
    from crypto_trade.portfolio.engine import PortfolioConfig, PortfolioEngine

    cfg = PortfolioConfig(
        dry_run=True, db_path=str(tmp_path / "r.db"), order_max_retries=3, order_retry_wait_s=0
    )
    eng = PortfolioEngine(cfg, load_settings())
    eng.auth = auth
    eng.qty_prec = {"ADAUSDT": 0}
    eng.step_size = {}
    eng.min_notl = {"ADAUSDT": 0.0}  # min-notional floor = cfg.min_notional_usd = $5
    eng._lev_set = {"ADAUSDT"}  # skip leverage call
    monkeypatch.setattr("crypto_trade.portfolio.engine.time.sleep", lambda *_a, **_k: None)
    return eng


def test_transient_then_success_resends_only_gap(tmp_path, monkeypatch):
    """502 then recovery: reconcile shows the order did NOT fill (-205 vs -240 target) -> resend the
    remaining -$35 gap (SELL 35), which succeeds."""
    auth = _FakeAuth(place_effects=[_http_err(502), None], notionals=[-205.0])
    eng = _engine(tmp_path, monkeypatch, auth)
    assert eng._place_leg_with_retry(LEG, GROSS) == "retried"
    assert len(auth.place_calls) == 2
    assert auth.place_calls[1] == ("ADAUSDT", "SELL", 35.0)  # only the unfilled gap
    assert auth.pos_calls == 1


def test_ambiguous_already_filled_does_not_double_fill(tmp_path, monkeypatch):
    """CRITICAL: the 502'd order ACTUALLY landed (position already at -240 target). Reconcile sees
    gap~0 and places NOTHING — no double-fill."""
    auth = _FakeAuth(place_effects=[_http_err(502), None], notionals=[-240.0])
    eng = _engine(tmp_path, monkeypatch, auth)
    assert eng._place_leg_with_retry(LEG, GROSS) == "reconciled"
    assert len(auth.place_calls) == 1  # NO second order
    assert auth.pos_calls == 1


def test_terminal_error_not_retried(tmp_path, monkeypatch):
    """A -4164 MIN_NOTIONAL reject (HTTP 400 + neg code) is terminal: no retry, no reconcile."""
    auth = _FakeAuth(
        place_effects=[_http_err(400, '{"code":-4164,"msg":"min notional"}')], notionals=[-205.0]
    )
    eng = _engine(tmp_path, monkeypatch, auth)
    assert eng._place_leg_with_retry(LEG, GROSS) == "error"
    assert len(auth.place_calls) == 1 and auth.pos_calls == 0


def test_rate_limit_not_retried(tmp_path, monkeypatch):
    """HTTP 429 is a rate-limit: do NOT retry inside the rebalance (would escalate a ban)."""
    auth = _FakeAuth(place_effects=[_http_err(429, "too many requests")], notionals=[-205.0])
    eng = _engine(tmp_path, monkeypatch, auth)
    assert eng._place_leg_with_retry(LEG, GROSS) == "error"
    assert len(auth.place_calls) == 1 and auth.pos_calls == 0


def test_persistent_transient_bounded(tmp_path, monkeypatch):
    """502 every attempt, never fills: bounded to 1 + order_max_retries placements, then error."""
    auth = _FakeAuth(place_effects=[_http_err(502)] * 6, notionals=[-205.0])
    eng = _engine(tmp_path, monkeypatch, auth)
    assert eng._place_leg_with_retry(LEG, GROSS) == "error"
    assert len(auth.place_calls) == 1 + eng.cfg.order_max_retries  # 4 attempts
    assert auth.pos_calls == eng.cfg.order_max_retries  # reconcile after each retryable fail


def test_reconcile_query_failure_does_not_resend(tmp_path, monkeypatch):
    """If the post-failure position query itself fails, we can't verify the fill -> do NOT resend
    (double-fill risk); return error and let the next 8h rebalance heal."""
    auth = _FakeAuth(
        place_effects=[_http_err(502), None], notionals=[-205.0], raise_on_positions=True
    )
    eng = _engine(tmp_path, monkeypatch, auth)
    assert eng._place_leg_with_retry(LEG, GROSS) == "error"
    assert len(auth.place_calls) == 1  # never resent blind


def test_execute_tally_counts_retries(tmp_path, monkeypatch):
    """execute() reports retried>0 and still counts a recovered leg as placed."""
    auth = _FakeAuth(place_effects=[_http_err(502), None], notionals=[-205.0])
    eng = _engine(tmp_path, monkeypatch, auth)
    eng.cfg = eng.cfg.__class__(**{**eng.cfg.__dict__, "testnet": True})
    plan = {"gross_dollar": GROSS, "legs": [LEG]}
    res = eng.execute(plan)
    assert res["placed"] == 1 and res["retried"] == 1 and res["errors"] == 0


def test_unlisted_4xx_is_terminal_not_retried(tmp_path, monkeypatch):
    """A 4xx Binance reject with a code NOT in TERMINAL_ORDER_CODES (e.g. -1100) is still terminal —
    a retry can't fix a bad-param 400. No wasted resends, no reconcile."""
    auth = _FakeAuth(
        place_effects=[_http_err(400, '{"code":-1100,"msg":"illegal chars"}')], notionals=[-205.0]
    )
    eng = _engine(tmp_path, monkeypatch, auth)
    assert eng._place_leg_with_retry(LEG, GROSS) == "error"
    assert len(auth.place_calls) == 1 and auth.pos_calls == 0


def test_sub_stepsize_gap_returns_error_not_false_success(tmp_path, monkeypatch):
    """After a transient fail, reconcile finds a real gap (>= min-notional) that rounds to qty 0
    under stepSize — must return 'error' (surfaced), not a false 'reconciled'."""
    leg = {
        "symbol": "ADAUSDT",
        "side": "SELL",
        "target_w": -0.06,
        "current_w": -0.045,
        "delta_notional_usd": -60.0,
        "price": 10.0,
    }  # target notional -240
    auth = _FakeAuth(place_effects=[_http_err(502)], notionals=[-246.0])  # gap = -240-(-246) = +6
    eng = _engine(tmp_path, monkeypatch, auth)
    eng.step_size = {"ADAUSDT": 1.0}  # 6/10 = 0.6 -> floor to step 1 -> qty 0, but $6 >= $5 min
    assert eng._place_leg_with_retry(leg, GROSS) == "error"
    assert len(auth.place_calls) == 1  # only the failed initial; no bogus resend


def test_classifier_502_body_with_timestamp_is_transient(tmp_path, monkeypatch):
    """Robustness: a 5xx whose body echoes a URL w/ a timestamp classifies by status (transient),
    never misread a digit run as a 418/429 rate-limit."""
    from crypto_trade.portfolio.engine import _order_error_kind

    assert _order_error_kind(_http_err(502, "timestamp=1783037150429")) == "transient"
    assert _order_error_kind(_http_err(429)) == "ratelimit"
    assert _order_error_kind(_http_err(400, '{"code":-1121}')) == "terminal"
    assert _order_error_kind(_http_err(400, '{"code":-1100}')) == "terminal"  # unlisted 4xx
    assert _order_error_kind(httpx.ReadTimeout("timed out")) == "transient"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
