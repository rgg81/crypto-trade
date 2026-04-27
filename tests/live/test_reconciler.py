import httpx
import pytest

from crypto_trade.live.auth_client import AuthenticatedBinanceClient
from crypto_trade.live.models import LiveTrade
from crypto_trade.live.reconciler import reconcile
from crypto_trade.live.state_store import StateStore


@pytest.fixture
def state(tmp_path):
    s = StateStore(tmp_path / "test.db")
    yield s
    s.close()


def _open_trade(**overrides) -> LiveTrade:
    defaults = dict(
        id="t1",
        model_name="A",
        symbol="BTCUSDT",
        direction=1,
        entry_price=60000.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=57600.0,
        take_profit_price=64800.0,
        open_time=1000000,
        timeout_time=99999999,
        signal_time=999000,
        status="open",
        entry_order_id="entry_1",
        sl_order_id="sl_1",
        tp_order_id="tp_1",
    )
    defaults.update(overrides)
    return LiveTrade(**defaults)


def _mock_client(order_statuses: dict[str, dict], positions: list[dict] | None = None):
    """Create a mock auth client that returns specific order statuses."""

    def handler(request):
        path = str(request.url.path)
        params = dict(request.url.params)

        if "/fapi/v1/order" in path and request.method == "GET":
            oid = params.get("orderId", "")
            if oid in order_statuses:
                return httpx.Response(200, json=order_statuses[oid])
            return httpx.Response(200, json={"status": "NEW"})

        if "/fapi/v3/positionRisk" in path:
            return httpx.Response(200, json=positions or [])

        if request.method == "DELETE":
            return httpx.Response(200, json={"orderId": params.get("orderId", "")})

        return httpx.Response(200, json={})

    return AuthenticatedBinanceClient(
        api_key="test",
        api_secret="test",
        transport=httpx.MockTransport(handler),
    )


def test_no_open_trades(state):
    msgs = reconcile(state, None, dry_run=True)
    assert any("No open trades" in m for m in msgs)


def test_dry_run_skips_exchange(state):
    state.upsert_trade(_open_trade())
    msgs = reconcile(state, None, dry_run=True)
    assert any("Dry-run" in m for m in msgs)
    assert state.get_trade("t1").status == "open"


def test_sl_filled_while_offline(state):
    state.upsert_trade(_open_trade())
    client = _mock_client(
        order_statuses={
            "sl_1": {"status": "FILLED", "avgPrice": "57600.0", "updateTime": 2000000},
        },
        positions=[{"positionAmt": "0.001"}],
    )

    msgs = reconcile(state, client, dry_run=False)
    trade = state.get_trade("t1")
    assert trade.status == "closed"
    assert trade.exit_reason == "stop_loss"
    assert trade.exit_price == 57600.0
    assert any("SL filled" in m for m in msgs)


def test_tp_filled_while_offline(state):
    state.upsert_trade(_open_trade())
    client = _mock_client(
        order_statuses={
            "sl_1": {"status": "NEW"},
            "tp_1": {"status": "FILLED", "avgPrice": "64800.0", "updateTime": 2000000},
        },
    )

    reconcile(state, client, dry_run=False)
    trade = state.get_trade("t1")
    assert trade.status == "closed"
    assert trade.exit_reason == "take_profit"


def test_position_gone_marked_reconciled(state):
    state.upsert_trade(_open_trade())
    client = _mock_client(
        order_statuses={},  # SL/TP both show as NEW
        positions=[{"positionAmt": "0"}],  # No position
    )

    reconcile(state, client, dry_run=False)
    trade = state.get_trade("t1")
    assert trade.status == "closed"
    assert trade.exit_reason == "reconciled"


def test_position_still_open(state):
    state.upsert_trade(_open_trade())
    client = _mock_client(
        order_statuses={},
        positions=[{"positionAmt": "0.016"}],  # Position still exists
    )

    reconcile(state, client, dry_run=False)
    trade = state.get_trade("t1")
    assert trade.status == "open"


def test_seeded_trade_is_skipped_not_corrupted(state):
    """A SEEDED open trade must not be touched by reconciler — its DB state
    (entry_price + None SL/TP IDs) would otherwise be destroyed by close_trade."""
    state.upsert_trade(
        _open_trade(
            id="seeded-1",
            entry_order_id="SEEDED",
            sl_order_id=None,
            tp_order_id=None,
        )
    )
    # Mock client returns "no position" — would normally trigger close_trade("reconciled")
    client = _mock_client(order_statuses={}, positions=[{"positionAmt": "0"}])

    msgs = reconcile(state, client, dry_run=False)

    trade = state.get_trade("seeded-1")
    assert trade.status == "open"
    assert trade.entry_order_id == "SEEDED"
    assert any("paper" in m.lower() and "skip" in m.lower() for m in msgs)


def test_catchup_trade_is_skipped(state):
    state.upsert_trade(
        _open_trade(
            id="catchup-1",
            entry_order_id="CATCHUP-deadbeef",
            sl_order_id="CATCHUP-feedface",
            tp_order_id="CATCHUP-12345678",
        )
    )
    client = _mock_client(order_statuses={}, positions=[{"positionAmt": "0"}])
    reconcile(state, client, dry_run=False)
    assert state.get_trade("catchup-1").status == "open"


def test_dry_prefix_trade_is_skipped(state):
    """Paper trade left over from a prior --dry-run session must not be reconciled."""
    state.upsert_trade(
        _open_trade(
            id="dry-1",
            entry_order_id="DRY-abc12345",
            sl_order_id="DRY-deadbeef",
            tp_order_id="DRY-feedface",
        )
    )
    client = _mock_client(order_statuses={}, positions=[{"positionAmt": "0"}])
    reconcile(state, client, dry_run=False)
    assert state.get_trade("dry-1").status == "open"


def test_real_numeric_id_still_reconciled(state):
    """Regression — pre-existing reconciler behavior preserved for real trades."""
    state.upsert_trade(_open_trade(entry_order_id="9876543210"))
    client = _mock_client(
        order_statuses={"sl_1": {"status": "FILLED", "avgPrice": "57600.0", "updateTime": 2000000}},
    )
    reconcile(state, client, dry_run=False)
    trade = state.get_trade("t1")
    assert trade.status == "closed"
    assert trade.exit_reason == "stop_loss"


def test_paper_skip_count_in_messages(state):
    state.upsert_trade(_open_trade(id="seed-a", entry_order_id="SEEDED"))
    state.upsert_trade(_open_trade(id="seed-b", entry_order_id="CATCHUP-aaaa1111"))
    state.upsert_trade(_open_trade(id="real-1", entry_order_id="9876543210"))
    client = _mock_client(order_statuses={}, positions=[{"positionAmt": "0.001"}])

    msgs = reconcile(state, client, dry_run=False)
    assert any("Skipped 2 paper" in m for m in msgs)
