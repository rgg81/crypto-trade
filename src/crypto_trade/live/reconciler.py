"""Startup reconciliation: compare local DB state with exchange positions/orders.

Runs once before the poll loop begins. Detects trades that were closed
(SL/TP hit) or orders that expired while the bot was offline.
"""

from __future__ import annotations

import time

from crypto_trade.live.auth_client import AuthenticatedBinanceClient
from crypto_trade.live.models import is_paper_trade
from crypto_trade.live.state_store import StateStore


def reconcile(
    state: StateStore,
    auth_client: AuthenticatedBinanceClient | None,
    dry_run: bool,
) -> list[str]:
    """Reconcile open trades in DB with exchange state.

    Paper trades (None / SEEDED / CATCHUP-* / DRY-* entry_order_id) are
    skipped — they have no Binance counterpart. Touching them would corrupt
    seeded state (e.g. close a SEEDED trade as 'reconciled' before catch-up
    can replay its scripted exit).
    """
    messages: list[str] = []
    open_trades = state.get_open_trades()

    if not open_trades:
        messages.append("[reconcile] No open trades in DB.")
        return messages

    messages.append(f"[reconcile] Found {len(open_trades)} open trade(s) in DB.")

    if dry_run or auth_client is None:
        messages.append("[reconcile] Dry-run mode — skipping exchange reconciliation.")
        return messages

    paper_trades = [t for t in open_trades if is_paper_trade(t)]
    real_trades = [t for t in open_trades if not is_paper_trade(t)]

    if paper_trades:
        messages.append(
            f"[reconcile] Skipped {len(paper_trades)} paper trade(s) "
            f"(SEEDED / CATCHUP- / DRY- / None) — no exchange counterpart."
        )

    now_ms = int(time.time() * 1000)

    for trade in real_trades:
        try:
            resolved = _reconcile_trade(trade, auth_client, state, now_ms)
            if resolved:
                messages.append(resolved)
        except Exception as exc:
            messages.append(
                f"[reconcile] Error checking {trade.model_name}:{trade.symbol} "
                f"(trade {trade.id}): {exc}"
            )

    return messages


def _reconcile_trade(trade, auth_client, state, now_ms) -> str | None:
    """Check one trade against exchange. Returns log message if resolved."""
    symbol = trade.symbol
    trade_id = trade.id

    # Check SL order
    if trade.sl_order_id:
        try:
            sl_status = auth_client.get_order(symbol, trade.sl_order_id)
            if sl_status.get("status") == "FILLED":
                fill_price = float(sl_status.get("avgPrice", trade.stop_loss_price))
                fill_time = int(sl_status.get("updateTime", now_ms))
                state.close_trade(trade_id, fill_price, fill_time, "stop_loss")
                # Cancel TP order
                if trade.tp_order_id:
                    try:
                        auth_client.cancel_order(symbol, trade.tp_order_id)
                    except Exception:
                        pass
                return (
                    f"[reconcile] {trade.model_name}:{symbol} — "
                    f"SL filled @ {fill_price:.2f} while offline"
                )
        except Exception:
            pass

    # Check TP order
    if trade.tp_order_id:
        try:
            tp_status = auth_client.get_order(symbol, trade.tp_order_id)
            if tp_status.get("status") == "FILLED":
                fill_price = float(tp_status.get("avgPrice", trade.take_profit_price))
                fill_time = int(tp_status.get("updateTime", now_ms))
                state.close_trade(trade_id, fill_price, fill_time, "take_profit")
                # Cancel SL order
                if trade.sl_order_id:
                    try:
                        auth_client.cancel_order(symbol, trade.sl_order_id)
                    except Exception:
                        pass
                return (
                    f"[reconcile] {trade.model_name}:{symbol} — "
                    f"TP filled @ {fill_price:.2f} while offline"
                )
        except Exception:
            pass

    # Check if position still exists
    try:
        positions = auth_client.get_positions(symbol)
        has_position = any(float(p.get("positionAmt", 0)) != 0 for p in positions)
        if not has_position:
            # Position gone but no SL/TP fill detected — mark as reconciled
            state.close_trade(trade_id, trade.entry_price, now_ms, "reconciled")
            return (
                f"[reconcile] {trade.model_name}:{symbol} — "
                f"no exchange position found, marked reconciled"
            )
    except Exception:
        pass

    return None
