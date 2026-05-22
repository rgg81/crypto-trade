"""Catch-up safety regression tests.

Property: regardless of dry_run/testnet/live mode, _catch_up_model must never
place real Binance orders. The first real order happens only after catch-up
returns and the live tick loop opens a position via OrderManager.open_trade.
"""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

from crypto_trade.live.engine import LiveEngine
from crypto_trade.live.models import COMBINED_MODELS, LiveConfig


def test_catch_up_never_calls_signed_endpoints(tmp_path):
    """_catch_up_model in dry_run=False mode must not place Binance orders.

    We patch the data-refresh helpers in _initial_setup so the test is fast
    (no network kline fetch, no feature-pipeline rebuild) and uses
    catch_up_lookback_days=0 so the replay loop exits before any model
    training would be triggered. The assertion still holds regardless of
    how many candles were replayed — the property under test is "no signed
    order placement before the live tick loop runs," which is a structural
    invariant of _catch_up_model's body (see the source-anchor test below).
    """
    cfg = LiveConfig(
        models=COMBINED_MODELS,
        dry_run=False,  # live mode
        db_path=tmp_path / "safety.db",
        data_dir=Path("data"),
        catch_up_lookback_days=0,  # short window — even an empty replay must not call _auth
    )
    engine = LiveEngine(cfg)
    auth_mock = MagicMock()
    engine._auth_client = auth_mock
    engine._order_mgr._auth = auth_mock

    # _initial_setup runs network kline fetch + feature regen + warmup, which
    # take many minutes for COMBINED_MODELS. The catch-up safety property is
    # independent of those. Stub _initial_setup out — we still hit
    # _reconcile, _rebuild_vt_history, _rebuild_risk_state, _catch_up.
    with patch.object(LiveEngine, "_initial_setup", lambda self: None):
        engine.catch_up_only()

    auth_mock.place_market_order.assert_not_called()
    auth_mock.place_algo_stop_market_order.assert_not_called()
    auth_mock.place_algo_take_profit_market_order.assert_not_called()


def test_catch_up_source_has_no_auth_reference():
    """Drift guard: _catch_up_model body must not reference self._auth.

    Source-anchor regex check. Catch-up creates CATCHUP-* paper rows
    directly via state.upsert_trade; real order placement is the live
    tick's job. Any future refactor that pipes self._auth into catch-up
    fails this test before it can land.
    """
    src = Path("src/crypto_trade/live/engine.py").read_text()
    # Match `def _catch_up_model(...)` body up to the next top-level def or
    # a clear section delimiter (`def _tick(`).
    match = re.search(
        r"def _catch_up_model\(self.*?\n    def (?:_tick|_shutdown)\(",
        src,
        flags=re.DOTALL,
    )
    assert match is not None, "Could not locate _catch_up_model in engine.py"
    body = match.group(0)
    assert "self._auth" not in body, (
        "_catch_up_model body must not reference self._auth. "
        "Catch-up creates CATCHUP-* paper rows directly via state.upsert_trade. "
        "Real order placement is the live tick's job (OrderManager.open_trade)."
    )


def test_catch_up_open_guard_sees_real_binance_trades():
    """Drift guard: _catch_up_model's step (b) open-guard must skip symbols
    that have an existing real Binance trade in the DB, not just paper rows.

    Background (the bug this prevents): the engine's two open-guards looked
    at different worlds —
      • live tick (engine.py:_tick) hits the DB and sees ALL open trades
      • catch-up (engine.py:_catch_up_model) loaded a paper-only dict that
        explicitly skipped `if not is_paper_trade(seeded): continue`,
        so the open-guard `sym not in open_trades` was blind to real trades

    Result: after a SIGTERM/relaunch, catch-up replayed candles past the
    candle that opened the real trade and created CATCHUP- duplicates for
    every subsequent same-direction signal — duplicates the live tick had
    correctly skipped via `position_open` while running.

    Fix: a parallel `real_open_syms: set[str]` is populated from real
    (non-paper) trades and checked alongside `open_trades` in step (b).
    Step (a)'s `check_order` still operates only on `open_trades` (paper
    only) so it never fakes an exit on a real Binance position.

    This regex anchor fails if either piece is removed.
    """
    src = Path("src/crypto_trade/live/engine.py").read_text()
    match = re.search(
        r"def _catch_up_model\(self.*?\n    def (?:_tick|_shutdown)\(",
        src,
        flags=re.DOTALL,
    )
    assert match is not None, "Could not locate _catch_up_model in engine.py"
    body = match.group(0)

    # Population: real_open_syms must be filled from non-paper trades.
    assert "real_open_syms" in body, (
        "_catch_up_model must maintain a `real_open_syms` set tracking "
        "symbols held by real (non-paper) Binance trades."
    )
    pop = re.search(
        r"if\s+not\s+is_paper_trade\(seeded\)\s*:\s*\n\s*real_open_syms\.add\(seeded\.symbol\)",
        body,
    )
    assert pop is not None, (
        "real_open_syms must be populated from `not is_paper_trade(seeded)` "
        "branch — paper-only entries belong in open_trades."
    )

    # Open-guard: step (b) must skip when sym is in real_open_syms.
    assert "sym not in real_open_syms" in body, (
        "Step (b)'s open-guard must include `sym not in real_open_syms` "
        "alongside `sym not in open_trades`. Without it, catch-up replays "
        "subsequent same-direction signals on a symbol whose real Binance "
        "position the live tick had already opened — producing CATCHUP- "
        "duplicates that diverge from live-tick behavior."
    )


def test_tick_uses_inner_strategy_for_current_month():
    """Drift guard: _tick must read _current_month off runner.inner_strategy,
    not runner.strategy. For v2 models runner.strategy is a RiskV2Wrapper
    that does not expose _current_month — accessing it raises AttributeError
    and breaks the per-tick same-month/new-month branch.
    """
    src = Path("src/crypto_trade/live/engine.py").read_text()
    match = re.search(
        r"def _tick\(self\).*?(?=\n    def |\Z)",
        src,
        flags=re.DOTALL,
    )
    assert match is not None, "Could not locate _tick in engine.py"
    body = match.group(0)
    # Any access of _current_month inside _tick must go through inner_strategy.
    # If you need to access it via another path, update this assertion AND
    # ensure the new path also works for RiskV2Wrapper-wrapped runners.
    bad = re.search(r"runner\.strategy\._current_month", body)
    assert bad is None, (
        "_tick must use runner.inner_strategy._current_month, not "
        "runner.strategy._current_month. RiskV2Wrapper does not expose "
        "_current_month, so the wrapped path raises AttributeError for v2 models."
    )
    # Positive assertion: the inner_strategy access must actually be present.
    assert "inner_strategy._current_month" in body, (
        "_tick must read _current_month from runner.inner_strategy."
    )
