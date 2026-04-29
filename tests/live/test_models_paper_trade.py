"""Tests for is_paper_trade() — classifies trade origin via entry_order_id prefix."""

from __future__ import annotations

import pytest

from crypto_trade.live.models import LiveTrade, is_paper_trade


def _trade(entry_order_id: str | None) -> LiveTrade:
    return LiveTrade(
        id="t",
        model_name="A",
        symbol="BTCUSDT",
        direction=1,
        entry_price=60000.0,
        amount_usd=1000.0,
        weight_factor=1.0,
        stop_loss_price=57600.0,
        take_profit_price=64800.0,
        open_time=1,
        timeout_time=2,
        signal_time=0,
        entry_order_id=entry_order_id,
    )


@pytest.mark.parametrize("oid", [None, "SEEDED", "DRY-abc12345", "CATCHUP-deadbeef"])
def test_paper_trade_prefixes(oid):
    assert is_paper_trade(_trade(oid)) is True


@pytest.mark.parametrize("oid", ["1234567890", "999", "0"])
def test_real_numeric_order_id_is_not_paper(oid):
    assert is_paper_trade(_trade(oid)) is False


def test_empty_string_is_real():
    """Empty entry_order_id can only arise from a Binance API anomaly during real-mode
    placement (`str(entry_resp.get("orderId", ""))` at order_manager.py:127). Treating
    it as 'real' keeps the failure mode loud (the next reconcile will surface it)
    rather than silently classifying it as paper."""
    assert is_paper_trade(_trade("")) is False
