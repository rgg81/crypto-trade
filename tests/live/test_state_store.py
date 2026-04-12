import pytest

from crypto_trade.live.models import LiveTrade
from crypto_trade.live.state_store import StateStore


@pytest.fixture
def store(tmp_path):
    s = StateStore(tmp_path / "test.db")
    yield s
    s.close()


def _make_trade(**overrides) -> LiveTrade:
    defaults = dict(
        id="t001",
        model_name="A",
        symbol="BTCUSDT",
        direction=1,
        entry_price=60000.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=57600.0,
        take_profit_price=64800.0,
        open_time=1000000,
        timeout_time=2000000,
        signal_time=999000,
        status="open",
        created_at="2026-01-01T00:00:00+00:00",
    )
    defaults.update(overrides)
    return LiveTrade(**defaults)


def test_upsert_and_get(store):
    trade = _make_trade()
    store.upsert_trade(trade)
    got = store.get_trade("t001")
    assert got is not None
    assert got.symbol == "BTCUSDT"
    assert got.direction == 1
    assert got.entry_price == 60000.0
    assert got.status == "open"


def test_get_open_trades(store):
    store.upsert_trade(_make_trade(id="t1", model_name="A", symbol="BTCUSDT"))
    store.upsert_trade(_make_trade(id="t2", model_name="C", symbol="LINKUSDT"))
    store.upsert_trade(_make_trade(id="t3", model_name="A", symbol="ETHUSDT", status="closed"))

    all_open = store.get_open_trades()
    assert len(all_open) == 2

    model_a = store.get_open_trades(model_name="A")
    assert len(model_a) == 1
    assert model_a[0].symbol == "BTCUSDT"

    model_c = store.get_open_trades(model_name="C")
    assert len(model_c) == 1
    assert model_c[0].symbol == "LINKUSDT"


def test_close_trade(store):
    store.upsert_trade(_make_trade())
    store.close_trade("t001", exit_price=64800.0, exit_time=1500000, exit_reason="take_profit")

    trade = store.get_trade("t001")
    assert trade.status == "closed"
    assert trade.exit_price == 64800.0
    assert trade.exit_time == 1500000
    assert trade.exit_reason == "take_profit"


def test_upsert_updates_existing(store):
    trade = _make_trade()
    store.upsert_trade(trade)

    trade.sl_order_id = "order_123"
    store.upsert_trade(trade)

    got = store.get_trade("t001")
    assert got.sl_order_id == "order_123"


def test_engine_state_kv(store):
    assert store.get_state("last_processed_BTCUSDT") is None

    store.set_state("last_processed_BTCUSDT", "1000000")
    assert store.get_state("last_processed_BTCUSDT") == "1000000"

    store.set_state("last_processed_BTCUSDT", "2000000")
    assert store.get_state("last_processed_BTCUSDT") == "2000000"


def test_get_all_trades_ordered(store):
    store.upsert_trade(_make_trade(id="t1", open_time=3000))
    store.upsert_trade(_make_trade(id="t2", open_time=1000))
    store.upsert_trade(_make_trade(id="t3", open_time=2000))

    trades = store.get_all_trades()
    assert [t.id for t in trades] == ["t2", "t3", "t1"]


def test_creates_parent_directories(tmp_path):
    db_path = tmp_path / "deep" / "nested" / "dir" / "test.db"
    store = StateStore(db_path)
    store.set_state("key", "val")
    assert store.get_state("key") == "val"
    store.close()
