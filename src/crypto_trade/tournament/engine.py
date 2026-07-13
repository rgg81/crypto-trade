"""Strategy-neutral, next-open Binance perpetual portfolio evaluator."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.data import eligible_at
from crypto_trade.tournament.protocol import (
    REBALANCE_INSTRUCTION_COLUMN,
    DecisionContext,
    TargetStrategy,
)


@dataclasses.dataclass(frozen=True)
class EvaluatorConfig:
    interval_hours: int = 8
    initial_equity: float = 100_000.0
    taker_fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.5
    max_gross_exposure: float = 1.0
    max_abs_net_exposure: float = 0.25
    max_symbol_exposure: float = 0.10
    max_bar_participation: float = 0.001

    def validate(self) -> None:
        if self.interval_hours < 1 or self.initial_equity <= 0:
            raise ValueError("interval_hours and initial_equity must be positive")
        if self.taker_fee_bps_per_side < 0 or self.slippage_bps_per_side < 0:
            raise ValueError("costs cannot be negative")
        if not 0 < self.max_gross_exposure <= 1.0:
            raise ValueError("gross exposure must be in (0, 1] for the unlevered evaluator")
        if not 0 <= self.max_abs_net_exposure <= self.max_gross_exposure:
            raise ValueError("invalid net-exposure cap")
        if not 0 < self.max_symbol_exposure <= self.max_gross_exposure:
            raise ValueError("invalid symbol-exposure cap")
        if not 0 < self.max_bar_participation <= 1:
            raise ValueError("max_bar_participation must be in (0, 1]")


@dataclasses.dataclass(frozen=True)
class EvaluationResult:
    returns: pd.DataFrame
    positions: pd.DataFrame
    events: pd.DataFrame


def generate_targets(
    strategy: TargetStrategy,
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    decision_times: Sequence[pd.Timestamp],
    *,
    seed: int,
    interval_hours: int = 8,
    auxiliary: Mapping[str, pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Call a team strategy with a freshly truncated past-only context at every decision.

    Every requested decision remains present on the returned audit grid. The reserved Boolean
    instruction column distinguishes an explicit target mapping from ``None`` (hold quantities).
    """
    frame = _normalise_bars(bars)
    if frame["symbol"].astype(str).eq(REBALANCE_INSTRUCTION_COLUMN).any():
        raise ValueError("market data contains the reserved rebalance instruction symbol")
    funding_frame = _normalise_funding(funding)
    interval = pd.Timedelta(hours=interval_hours)
    symbol_frames = {
        symbol: group.reset_index(drop=True)
        for symbol, group in frame.groupby("symbol", observed=True, sort=False)
    }
    symbol_close_times = {
        symbol: pd.DatetimeIndex(group["open_time"] + interval)
        for symbol, group in symbol_frames.items()
    }
    symbols_with_open = {
        pd.Timestamp(open_time): frozenset(group["symbol"])
        for open_time, group in frame.groupby("open_time", observed=True, sort=False)
    }
    funding_times = pd.DatetimeIndex(funding_frame["funding_time"])
    outputs: list[pd.Series] = []
    for raw_time in sorted(pd.to_datetime(list(decision_times), utc=True)):
        decision_time = pd.Timestamp(raw_time)
        # Weekly membership can outlive a mid-week suspension or delisting. A strategy may only
        # target members for which the evaluator has an executable open at this decision. The
        # open price itself remains hidden; only fillability is exposed.
        available = symbols_with_open.get(decision_time, frozenset())
        eligible = tuple(
            symbol for symbol in eligible_at(membership, decision_time) if symbol in available
        )
        by_symbol: dict[str, pd.DataFrame] = {}
        for symbol in eligible:
            group = symbol_frames.get(symbol)
            if group is None:
                continue
            stop = symbol_close_times[symbol].searchsorted(decision_time, side="right")
            # The context is explicitly read-only. A shallow slice avoids repeatedly copying the
            # complete multi-year history while still preventing any future row from being seen.
            by_symbol[symbol] = group.iloc[:stop].copy(deep=False)
        funding_stop = funding_times.searchsorted(decision_time, side="left")
        past_funding = funding_frame.iloc[:funding_stop]
        if eligible:
            past_funding = past_funding[past_funding["symbol"].isin(eligible)]
        else:
            past_funding = past_funding.iloc[0:0]
        past_auxiliary: dict[str, pd.DataFrame] = {}
        for name, auxiliary_frame in (auxiliary or {}).items():
            if "timestamp" not in auxiliary_frame.columns:
                raise ValueError(f"auxiliary dataset {name} requires a timestamp column")
            timestamps = pd.to_datetime(auxiliary_frame["timestamp"], utc=True)
            past_auxiliary[name] = auxiliary_frame.loc[timestamps < decision_time].copy(deep=False)
        context = DecisionContext(
            decision_time=decision_time,
            bars=by_symbol,
            funding=past_funding,
            auxiliary=past_auxiliary,
            eligible_symbols=eligible,
        )
        weights = strategy.target_weights(context, seed=seed)
        if weights is None:
            row_values: dict[str, float | bool] = {REBALANCE_INSTRUCTION_COLUMN: False}
        else:
            if not isinstance(weights, Mapping):
                raise TypeError("target_weights() must return a weight mapping or None")
            row_values = {}
            for symbol, raw_weight in weights.items():
                weight = float(raw_weight)
                if not math.isfinite(weight):
                    raise ValueError("target_weights() returned a non-finite target weight")
                row_values[str(symbol)] = weight
            if REBALANCE_INSTRUCTION_COLUMN in row_values:
                raise ValueError("target_weights() returned the reserved instruction column")
            row_values[REBALANCE_INSTRUCTION_COLUMN] = True
        row = pd.Series(row_values)
        row.name = decision_time
        outputs.append(row)
    if not outputs:
        return pd.DataFrame()
    result = pd.DataFrame(outputs).fillna(0.0).sort_index()
    result[REBALANCE_INSTRUCTION_COLUMN] = result[REBALANCE_INSTRUCTION_COLUMN].astype(bool)
    return result


def evaluate_targets(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    mark_prices: pd.DataFrame,
    config: EvaluatorConfig | None = None,
    cost_multiplier: float = 1.0,
) -> EvaluationResult:
    """Convert target weights to fills, costs, funding cashflows, and open-to-open returns.

    A target indexed at time ``t`` was decided from candles closed by ``t`` and fills at the open
    timestamped ``t``. Target quantities and exposure controls use the exact boundary mark while
    fills, participation, and costs use the transaction open. Exposure earns the following bar's
    open-to-open transaction return. Funding is applied from actual published rows in
    ``[t, next_t)``; no fixed funding schedule is assumed. A false reserved rebalance instruction
    holds current quantities, but never disables membership exits or central risk reductions.
    """
    cfg = config or EvaluatorConfig()
    cfg.validate()
    if cost_multiplier <= 0:
        raise ValueError("cost_multiplier must be positive")
    frame = _normalise_bars(bars)
    funding_frame = _normalise_funding(funding)
    mark_frame = _normalise_mark_prices(mark_prices)
    if len(targets.index) == 0:
        return EvaluationResult(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

    target_frame = targets.copy()
    target_frame.index = pd.to_datetime(target_frame.index, utc=True)
    target_frame = target_frame.sort_index()
    if target_frame.index.duplicated().any():
        raise ValueError("target frame contains duplicate timestamps")
    if target_frame.columns.duplicated().any():
        raise ValueError("target frame contains duplicate columns")
    if REBALANCE_INSTRUCTION_COLUMN in target_frame.columns:
        rebalance_instructions = target_frame.pop(REBALANCE_INSTRUCTION_COLUMN)
        if rebalance_instructions.isna().any() or not pd.api.types.is_bool_dtype(
            rebalance_instructions.dtype
        ):
            raise ValueError("rebalance instruction column must contain only Boolean values")
        rebalance_instructions = rebalance_instructions.astype(bool)
    else:
        # Focused evaluator callers predating sparse instructions remain explicit-rebalance rows.
        rebalance_instructions = pd.Series(True, index=target_frame.index, dtype=bool)
    target_frame = target_frame.apply(pd.to_numeric, errors="raise").astype(float)
    if not np.isfinite(target_frame.to_numpy()).all():
        raise ValueError("target frame contains non-finite target weights")
    if frame["symbol"].astype(str).eq(REBALANCE_INSTRUCTION_COLUMN).any():
        raise ValueError("market data contains the reserved rebalance instruction symbol")
    symbols = sorted(set(frame["symbol"]) | set(target_frame.columns))
    opens = frame.pivot(index="open_time", columns="symbol", values="open").sort_index()
    closes = frame.pivot(index="open_time", columns="symbol", values="close").sort_index()
    quote_volume = frame.pivot(
        index="open_time", columns="symbol", values="quote_volume"
    ).sort_index()
    boundary_marks = mark_frame.pivot(
        index="mark_time", columns="symbol", values="mark_price"
    ).sort_index()
    unmatched_targets = target_frame.index.difference(opens.index)
    if len(unmatched_targets):
        raise ValueError(f"target timestamps without matching bar opens: {list(unmatched_targets)}")
    evaluation_times = opens.index[
        (opens.index >= target_frame.index.min()) & (opens.index <= target_frame.index.max())
    ]
    if len(evaluation_times) < 2:
        raise ValueError("at least two base bars within the target span are required")

    quantities = pd.Series(0.0, index=symbols)
    equity = cfg.initial_equity
    return_rows: list[dict[str, object]] = []
    position_rows: list[pd.Series] = []
    event_rows: list[dict[str, object]] = []
    for index, fill_time in enumerate(evaluation_times):
        terminal_bar = index == len(evaluation_times) - 1
        next_time = (
            fill_time + pd.Timedelta(hours=cfg.interval_hours)
            if terminal_bar
            else evaluation_times[index + 1]
        )
        equity_at_start = equity
        quantities_before_trade = quantities.copy()
        current_open = opens.loc[fill_time].reindex(symbols)
        current_mark = (
            boundary_marks.loc[fill_time].reindex(symbols)
            if fill_time in boundary_marks.index
            else pd.Series(np.nan, index=symbols)
        )
        next_open = (
            pd.Series(np.nan, index=symbols)
            if terminal_bar
            else opens.loc[next_time].reindex(symbols)
        )
        current_close = closes.loc[fill_time].reindex(symbols)
        missing_held_open = quantities.ne(0.0) & current_open.isna()
        if missing_held_open.any():
            raise ValueError(
                "missing current open for held symbols: "
                f"{sorted(quantities[missing_held_open].index)}"
            )
        missing_held_mark = quantities.ne(0.0) & current_mark.isna()
        if missing_held_mark.any():
            raise ValueError(
                "missing current mark for held symbols: "
                f"{sorted(quantities[missing_held_mark].index)}"
            )

        # Funding on the exact boundary belongs to the carried position, before the rebalance.
        at_fill = funding_frame[funding_frame["settlement_time"] == fill_time]
        funding_at_fill_usd = _funding_cashflow_usd(at_fill, quantities_before_trade)
        event_rows.extend(
            _funding_event_rows(at_fill, quantities_before_trade, phase="before_rebalance")
        )
        equity_after_boundary_funding = equity + funding_at_fill_usd
        if equity_after_boundary_funding <= 0:
            raise ValueError(f"portfolio insolvent after funding at {fill_time}")

        # Intersect the weekly universe with the actually executable cross-section. This mirrors
        # ``generate_targets`` and prevents a stale weekly member from being reopened after its
        # last bar. Any position carried into a missing next open is closed below at the last
        # executable close, with normal fees and slippage.
        fillable = set(current_open[current_open.notna()].index)
        eligible = set(eligible_at(membership, fill_time)) & fillable
        missing_eligible_mark = current_mark.loc[list(eligible)].isna()
        if missing_eligible_mark.any():
            raise ValueError(
                "missing current mark for eligible symbols: "
                f"{sorted(missing_eligible_mark[missing_eligible_mark].index)}"
            )
        requested_quantity_by_symbol = pd.Series(0.0, index=symbols)
        if fill_time in target_frame.index and bool(rebalance_instructions.loc[fill_time]):
            desired = pd.Series(0.0, index=symbols)
            supplied = target_frame.loc[fill_time].reindex(symbols).fillna(0.0).astype(float)
            if not np.isfinite(supplied.to_numpy()).all():
                raise ValueError(f"non-finite target at {fill_time}")
            ineligible_nonzero = supplied[(supplied.abs() > 1e-12) & ~supplied.index.isin(eligible)]
            if not ineligible_nonzero.empty:
                raise ValueError(
                    f"ineligible target symbols at {fill_time}: {sorted(ineligible_nonzero.index)}"
                )
            active_symbols = list(eligible & set(symbols))
            desired.loc[active_symbols] = supplied.loc[active_symbols]
            _validate_weight_limits(desired, cfg, fill_time)
            desired_mark_notional = desired * equity_after_boundary_funding
            desired_quantities = desired_mark_notional.div(current_mark).fillna(0.0)
            requested_quantity_by_symbol = desired_quantities - quantities
        else:
            # A sparse strategy holds quantities between decisions. Membership exits remain
            # mandatory, and the central exposure-cap pass below still runs on every bar.
            no_longer_eligible = ~quantities.index.isin(eligible)
            requested_quantity_by_symbol.loc[no_longer_eligible] = -quantities.loc[
                no_longer_eligible
            ]

        # Target and risk weights are mark-notional quantities. Orders, participation, and costs
        # remain transaction-price quantities so a mark/open basis cannot manufacture liquidity.
        requested_notional_by_symbol = requested_quantity_by_symbol.mul(current_open).fillna(0.0)

        history_volume = quote_volume.loc[quote_volume.index < fill_time].tail(
            max(1, math.ceil(24 / cfg.interval_hours))
        )
        available = history_volume.sum(axis=0).reindex(symbols).fillna(0.0)
        cap_notional = available * cfg.max_bar_participation
        filled_notional = requested_notional_by_symbol.clip(lower=-cap_notional, upper=cap_notional)
        missing_trade_price = filled_notional.ne(0.0) & current_open.isna()
        if missing_trade_price.any():
            raise ValueError(
                "missing trade price for target symbols: "
                f"{sorted(filled_notional[missing_trade_price].index)}"
            )
        quantities = quantities + filled_notional.div(current_open).fillna(0.0)
        requested_notional = float(requested_notional_by_symbol.abs().sum())
        executed_notional = float(filled_notional.abs().sum())
        unfilled_notional = float((requested_notional_by_symbol - filled_notional).abs().sum())
        execution_cost_rate = (
            (cfg.taker_fee_bps_per_side + cfg.slippage_bps_per_side) / 10_000 * cost_multiplier
        )
        equity_after_strategy_costs = equity_after_boundary_funding - (
            executed_notional * execution_cost_rate
        )
        if equity_after_strategy_costs <= 0:
            raise ValueError(f"portfolio insolvent after execution costs at {fill_time}")
        risk_scale = _cost_aware_risk_reduction_scale(
            quantities,
            current_mark,
            current_open,
            equity_after_strategy_costs,
            cfg,
            execution_cost_rate,
        )
        risk_requested_notional = pd.Series(0.0, index=symbols)
        risk_reduction_notional = pd.Series(0.0, index=symbols)
        if risk_scale < 1.0:
            # Central exposure caps override strategy cadence. De-risking is an emergency market
            # action, charged normal costs, and is never treated as alpha or a free rebalance.
            risk_requested_quantity = quantities * (risk_scale - 1.0)
            risk_requested_notional = risk_requested_quantity.mul(current_open).fillna(0.0)
            remaining_cap = (cap_notional - filled_notional.abs()).clip(lower=0.0)
            risk_reduction_notional = risk_requested_notional.clip(
                lower=-remaining_cap, upper=remaining_cap
            )
            quantities = quantities + risk_reduction_notional.div(current_open).fillna(0.0)
            risk_executed = float(risk_reduction_notional.abs().sum())
            executed_notional += risk_executed
            requested_notional += float(risk_requested_notional.abs().sum())
            unfilled_notional += float(
                (risk_requested_notional - risk_reduction_notional).abs().sum()
            )
        entry_fee_usd = executed_notional * cfg.taker_fee_bps_per_side / 10_000 * cost_multiplier
        entry_slippage_usd = (
            executed_notional * cfg.slippage_bps_per_side / 10_000 * cost_multiplier
        )
        for symbol in filled_notional[filled_notional.ne(0.0)].index:
            symbol_notional = float(filled_notional[symbol])
            event_rows.append(
                {
                    "timestamp": fill_time,
                    "symbol": symbol,
                    "event_type": "trade",
                    "phase": "rebalance",
                    "quantity": float(symbol_notional / current_open[symbol]),
                    "price": float(current_open[symbol]),
                    "notional": symbol_notional,
                    "funding_rate": 0.0,
                    "cashflow": 0.0,
                    "fee": abs(symbol_notional)
                    * cfg.taker_fee_bps_per_side
                    / 10_000
                    * cost_multiplier,
                    "slippage": abs(symbol_notional)
                    * cfg.slippage_bps_per_side
                    / 10_000
                    * cost_multiplier,
                }
            )
        for symbol in risk_reduction_notional[risk_reduction_notional.ne(0.0)].index:
            symbol_notional = float(risk_reduction_notional[symbol])
            event_rows.append(
                {
                    "timestamp": fill_time,
                    "symbol": symbol,
                    "event_type": "risk_reduction",
                    "phase": "exposure_cap",
                    "quantity": float(symbol_notional / current_open[symbol]),
                    "price": float(current_open[symbol]),
                    "notional": symbol_notional,
                    "funding_rate": 0.0,
                    "cashflow": 0.0,
                    "fee": abs(symbol_notional)
                    * cfg.taker_fee_bps_per_side
                    / 10_000
                    * cost_multiplier,
                    "slippage": abs(symbol_notional)
                    * cfg.slippage_bps_per_side
                    / 10_000
                    * cost_multiplier,
                }
            )

        price_change = next_open.sub(current_open)
        forced_mask = (
            quantities.ne(0.0) & price_change.isna() & current_open.notna() & current_close.notna()
        )
        if terminal_bar:
            forced_mask = quantities.ne(0.0) & current_open.notna() & current_close.notna()
        price_change.loc[forced_mask] = current_close.loc[forced_mask].sub(
            current_open.loc[forced_mask]
        )
        unavailable = quantities.ne(0.0) & price_change.isna()
        if unavailable.any():
            raise ValueError(
                "missing executable price for held symbols: "
                f"{sorted(quantities[unavailable].index)}"
            )

        # Funding at the right boundary belongs to the position carried into that boundary and
        # precedes a forced close or settlement.  Charge only quantities that disappear here.
        # Surviving quantities are intentionally left for the next loop's ``at_fill`` pass, which
        # prevents a shared boundary event from being counted twice.  On the terminal bar every
        # held quantity is forced, so this also closes the otherwise-open right endpoint.
        at_forced_exit_boundary = funding_frame[funding_frame["settlement_time"] == next_time]
        forced_exit_boundary_quantities = quantities.where(forced_mask, 0.0)
        funding_at_forced_exit_usd = _funding_cashflow_usd(
            at_forced_exit_boundary, forced_exit_boundary_quantities
        )
        event_rows.extend(
            _funding_event_rows(
                at_forced_exit_boundary,
                forced_exit_boundary_quantities,
                phase="before_forced_exit",
            )
        )
        price_pnl_by_symbol = quantities * price_change.fillna(0.0)
        price_pnl_usd = float(price_pnl_by_symbol.sum())
        long_price_pnl_usd = float(price_pnl_by_symbol.loc[quantities > 0.0].sum())
        short_price_pnl_usd = float(price_pnl_by_symbol.loc[quantities < 0.0].sum())
        for symbol in quantities[quantities.ne(0.0)].index:
            event_price = next_open[symbol]
            if pd.isna(event_price):
                event_price = current_close[symbol]
            event_rows.append(
                {
                    "timestamp": next_time,
                    "symbol": symbol,
                    "event_type": "mark_to_market",
                    "phase": "bar",
                    "quantity": float(quantities[symbol]),
                    "price": float(event_price),
                    "notional": float(quantities[symbol] * current_open[symbol]),
                    "funding_rate": 0.0,
                    "cashflow": float(quantities[symbol] * price_change[symbol]),
                    "fee": 0.0,
                    "slippage": 0.0,
                }
            )

        after_fill = funding_frame[
            (funding_frame["settlement_time"] > fill_time)
            & (funding_frame["settlement_time"] < next_time)
        ]
        funding_after_fill_usd = _funding_cashflow_usd(after_fill, quantities)
        event_rows.extend(_funding_event_rows(after_fill, quantities, phase="holding"))
        long_funding_usd = (
            _funding_cashflow_usd(
                at_fill, quantities_before_trade.where(quantities_before_trade > 0.0, 0.0)
            )
            + _funding_cashflow_usd(after_fill, quantities.where(quantities > 0.0, 0.0))
            + _funding_cashflow_usd(
                at_forced_exit_boundary,
                forced_exit_boundary_quantities.where(forced_exit_boundary_quantities > 0.0, 0.0),
            )
        )
        short_funding_usd = (
            _funding_cashflow_usd(
                at_fill, quantities_before_trade.where(quantities_before_trade < 0.0, 0.0)
            )
            + _funding_cashflow_usd(after_fill, quantities.where(quantities < 0.0, 0.0))
            + _funding_cashflow_usd(
                at_forced_exit_boundary,
                forced_exit_boundary_quantities.where(forced_exit_boundary_quantities < 0.0, 0.0),
            )
        )

        # A last close is a price observation, not evidence of unlimited executable liquidity.
        # Close orders therefore share the realized bar's participation allowance with orders
        # already executed at its open.  A delisted residual has no later executable observation:
        # settle it with an explicit, symmetric adverse 100% reference-notional haircut (longs
        # behave as if settled at zero; shorts as if settled at twice the last close).  At the
        # arbitrary terminal horizon, retain mark-to-market PnL and report any unexecuted residual
        # instead of applying the delisting haircut.
        forced_exit_requested = (-quantities * current_close).where(forced_mask, 0.0).fillna(0.0)
        close_participation_cap = (
            quote_volume.loc[fill_time].reindex(symbols).fillna(0.0) * cfg.max_bar_participation
        )
        current_bar_executed = filled_notional.abs() + risk_reduction_notional.abs()
        forced_exit_cap = (close_participation_cap - current_bar_executed).clip(lower=0.0)
        forced_exit_filled = forced_exit_requested.clip(
            lower=-forced_exit_cap, upper=forced_exit_cap
        )
        forced_exit_quantity = forced_exit_filled.div(current_close).fillna(0.0)
        residual_quantity = (quantities + forced_exit_quantity).where(forced_mask, 0.0)
        residual_quantity = residual_quantity.mask(residual_quantity.abs() < 1e-12, 0.0)
        delisting_residual = residual_quantity.where(forced_mask & (not terminal_bar), 0.0)
        terminal_residual = residual_quantity.where(forced_mask & terminal_bar, 0.0)

        forced_exit_requested_notional = float(forced_exit_requested.abs().sum())
        forced_exit_notional = float(forced_exit_filled.abs().sum())
        forced_exit_unfilled_notional = float(
            (forced_exit_requested - forced_exit_filled).abs().sum()
        )
        conservative_settlement_notional = float((delisting_residual.abs() * current_close).sum())
        conservative_long_settlement = float(
            (delisting_residual.where(delisting_residual > 0.0, 0.0) * current_close).sum()
        )
        conservative_short_settlement = float(
            (-delisting_residual.where(delisting_residual < 0.0, 0.0) * current_close).sum()
        )
        terminal_unresolved_notional = float((terminal_residual.abs() * current_close).sum())
        requested_notional += forced_exit_requested_notional
        unfilled_notional += forced_exit_unfilled_notional
        forced_fee_usd = (
            forced_exit_notional * cfg.taker_fee_bps_per_side / 10_000 * cost_multiplier
        )
        forced_slippage_usd = (
            forced_exit_notional * cfg.slippage_bps_per_side / 10_000 * cost_multiplier
        )
        for symbol in forced_exit_filled[forced_exit_filled.ne(0.0)].index:
            notional = float(forced_exit_filled[symbol])
            event_rows.append(
                {
                    "timestamp": next_time,
                    "symbol": symbol,
                    "event_type": "forced_exit",
                    "phase": "terminal" if terminal_bar else "delisting",
                    "quantity": float(forced_exit_quantity[symbol]),
                    "price": float(current_close[symbol]),
                    "notional": notional,
                    "funding_rate": 0.0,
                    "cashflow": 0.0,
                    "fee": abs(notional) * cfg.taker_fee_bps_per_side / 10_000 * cost_multiplier,
                    "slippage": abs(notional)
                    * cfg.slippage_bps_per_side
                    / 10_000
                    * cost_multiplier,
                }
            )
        for symbol in delisting_residual[delisting_residual.ne(0.0)].index:
            reference_notional = float(abs(delisting_residual[symbol] * current_close[symbol]))
            event_rows.append(
                {
                    "timestamp": next_time,
                    "symbol": symbol,
                    "event_type": "conservative_settlement",
                    "phase": "delisting_residual_100pct_haircut",
                    "quantity": float(-delisting_residual[symbol]),
                    "price": float(current_close[symbol]),
                    "notional": float(-delisting_residual[symbol] * current_close[symbol]),
                    "funding_rate": 0.0,
                    "cashflow": -reference_notional,
                    "fee": 0.0,
                    "slippage": 0.0,
                }
            )
        for symbol in terminal_residual[terminal_residual.ne(0.0)].index:
            event_rows.append(
                {
                    "timestamp": next_time,
                    "symbol": symbol,
                    "event_type": "unresolved_residual",
                    "phase": "terminal",
                    "quantity": float(terminal_residual[symbol]),
                    "price": float(current_close[symbol]),
                    "notional": float(terminal_residual[symbol] * current_close[symbol]),
                    "funding_rate": 0.0,
                    "cashflow": 0.0,
                    "fee": 0.0,
                    "slippage": 0.0,
                }
            )
        fee_usd = entry_fee_usd + forced_fee_usd
        slippage_usd = entry_slippage_usd + forced_slippage_usd
        price_pnl_usd -= conservative_settlement_notional
        long_price_pnl_usd -= conservative_long_settlement
        short_price_pnl_usd -= conservative_short_settlement
        net_change_usd = (
            funding_at_fill_usd
            + price_pnl_usd
            + funding_after_fill_usd
            + funding_at_forced_exit_usd
            - fee_usd
            - slippage_usd
        )
        net_return = net_change_usd / equity_at_start
        equity = equity_at_start + net_change_usd
        if equity <= 0:
            raise ValueError(f"portfolio insolvent at {fill_time}")

        equity_after_execution_costs = (
            equity_after_boundary_funding - entry_fee_usd - entry_slippage_usd
        )
        if equity_after_execution_costs <= 0:
            raise ValueError(f"portfolio insolvent after execution costs at {fill_time}")
        held_weights = quantities.mul(current_mark).div(equity_after_execution_costs)
        risk_breach_scale = _risk_reduction_scale(held_weights, cfg)
        position = held_weights.copy()
        position.name = fill_time
        position_rows.append(position)
        quantities.loc[forced_mask] = 0.0
        total_turnover = (executed_notional + forced_exit_notional) / equity_at_start
        return_rows.append(
            {
                "timestamp": fill_time,
                "price_pnl": price_pnl_usd / equity_at_start,
                "long_price_pnl": long_price_pnl_usd / equity_at_start,
                "short_price_pnl": short_price_pnl_usd / equity_at_start,
                "funding_pnl": (
                    funding_at_fill_usd + funding_after_fill_usd + funding_at_forced_exit_usd
                )
                / equity_at_start,
                "long_funding_pnl": long_funding_usd / equity_at_start,
                "short_funding_pnl": short_funding_usd / equity_at_start,
                "forced_exit_boundary_funding_pnl": funding_at_forced_exit_usd / equity_at_start,
                "fees": fee_usd / equity_at_start,
                "slippage": slippage_usd / equity_at_start,
                "net_return": net_return,
                "turnover": total_turnover,
                "gross_exposure": float(held_weights.abs().sum()),
                "net_exposure": float(held_weights.sum()),
                "long_exposure": float(held_weights.clip(lower=0.0).sum()),
                "short_exposure": float(-held_weights.clip(upper=0.0).sum()),
                "requested_notional": requested_notional,
                "unfilled_notional": unfilled_notional,
                "forced_exit_requested_notional": forced_exit_requested_notional,
                "forced_exit_unfilled_notional": forced_exit_unfilled_notional,
                "forced_exit_turnover": forced_exit_notional / equity_at_start,
                "conservative_settlement_notional": conservative_settlement_notional,
                "conservative_settlement_loss": conservative_settlement_notional / equity_at_start,
                "terminal_unresolved_notional": terminal_unresolved_notional,
                "risk_reduction_turnover": float(risk_reduction_notional.abs().sum())
                / equity_at_start,
                "risk_cap_breach": risk_breach_scale < 1.0 - 1e-12,
                "risk_cap_required_scale": risk_breach_scale,
                "equity": equity,
            }
        )
    returns = pd.DataFrame(return_rows).set_index("timestamp")
    positions = pd.DataFrame(position_rows).fillna(0.0)
    events = pd.DataFrame(event_rows)
    return EvaluationResult(returns=returns, positions=positions, events=events)


def evaluate_base_and_double_cost(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    mark_prices: pd.DataFrame,
    config: EvaluatorConfig | None = None,
) -> tuple[EvaluationResult, EvaluationResult]:
    """Perform two independent evaluator runs; the stress result is not an analytic shortcut."""
    base = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=mark_prices,
        config=config,
        cost_multiplier=1.0,
    )
    stressed = evaluate_targets(
        bars,
        funding,
        membership,
        targets,
        mark_prices=mark_prices,
        config=config,
        cost_multiplier=2.0,
    )
    return base, stressed


def _normalise_bars(bars: pd.DataFrame) -> pd.DataFrame:
    required = {"open_time", "symbol", "open", "close", "quote_volume"}
    missing = required - set(bars.columns)
    if missing:
        raise ValueError(f"bars missing columns: {sorted(missing)}")
    frame = bars.copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True)
    if frame["open_time"].isna().any():
        raise ValueError("bars contain invalid timestamps")
    for column in ("open", "close", "quote_volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if not np.isfinite(frame[column].to_numpy()).all():
            raise ValueError(f"bars contain non-finite {column}")
    if (frame[["open", "close"]] <= 0).any().any():
        raise ValueError("bar prices must be positive")
    if (frame["quote_volume"] < 0).any():
        raise ValueError("quote_volume cannot be negative")
    for column in ("high", "low", "volume", "trade_count", "taker_buy_quote_volume"):
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
            if not np.isfinite(frame[column].to_numpy()).all():
                raise ValueError(f"bars contain non-finite {column}")
    if frame.duplicated(["open_time", "symbol"]).any():
        raise ValueError("duplicate (open_time, symbol) bars")
    return frame.sort_values(["open_time", "symbol"]).reset_index(drop=True)


def _normalise_funding(funding: pd.DataFrame) -> pd.DataFrame:
    required = {"funding_time", "symbol", "funding_rate", "mark_price"}
    missing = required - set(funding.columns)
    if missing:
        raise ValueError(f"funding missing columns: {sorted(missing)}")
    frame = funding.loc[:, sorted(required)].copy()
    frame["funding_time"] = pd.to_datetime(frame["funding_time"], utc=True)
    if frame["funding_time"].isna().any():
        raise ValueError("funding contains invalid timestamps")
    frame["settlement_time"] = frame["funding_time"].dt.floor("h")
    jitter = frame["funding_time"] - frame["settlement_time"]
    if (jitter >= pd.Timedelta(seconds=1)).any():
        raise ValueError("funding timestamps must be at an hourly boundary with sub-second jitter")
    for column in ("funding_rate", "mark_price"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if not np.isfinite(frame[column].to_numpy()).all():
            raise ValueError(f"funding contains non-finite {column}")
    if (frame["mark_price"] <= 0).any():
        raise ValueError("funding mark_price must be positive")
    if frame.duplicated(["funding_time", "symbol"]).any():
        raise ValueError("duplicate (funding_time, symbol) rows")
    if frame.duplicated(["settlement_time", "symbol"]).any():
        raise ValueError("duplicate (settlement_time, symbol) funding rows")
    return frame.sort_values(["settlement_time", "funding_time", "symbol"]).reset_index(drop=True)


def _normalise_mark_prices(mark_prices: pd.DataFrame) -> pd.DataFrame:
    required = {"mark_time", "symbol", "mark_price"}
    missing = required - set(mark_prices.columns)
    if missing:
        raise ValueError(f"mark_prices missing columns: {sorted(missing)}")
    frame = mark_prices.loc[:, ["mark_time", "symbol", "mark_price"]].copy()
    frame["mark_time"] = pd.to_datetime(frame["mark_time"], utc=True)
    if frame["mark_time"].isna().any():
        raise ValueError("mark_prices contain invalid timestamps")
    frame["mark_price"] = pd.to_numeric(frame["mark_price"], errors="raise")
    if not np.isfinite(frame["mark_price"].to_numpy()).all():
        raise ValueError("mark_prices contain non-finite prices")
    if (frame["mark_price"] <= 0).any():
        raise ValueError("mark_prices must be positive")
    if frame.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("duplicate (mark_time, symbol) rows")
    return frame.sort_values(["mark_time", "symbol"]).reset_index(drop=True)


def _funding_cashflow_usd(events: pd.DataFrame, quantities: pd.Series) -> float:
    if events.empty:
        return 0.0
    event_quantities = events["symbol"].map(quantities).fillna(0.0)
    return -float((event_quantities * events["mark_price"] * events["funding_rate"]).sum())


def _funding_event_rows(
    events: pd.DataFrame, quantities: pd.Series, *, phase: str
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in events.itertuples(index=False):
        quantity = float(quantities.get(event.symbol, 0.0))
        if quantity == 0.0:
            continue
        cashflow = -quantity * float(event.mark_price) * float(event.funding_rate)
        rows.append(
            {
                "timestamp": event.funding_time,
                "symbol": event.symbol,
                "event_type": "funding",
                "phase": phase,
                "quantity": quantity,
                "price": float(event.mark_price),
                "notional": quantity * float(event.mark_price),
                "funding_rate": float(event.funding_rate),
                "cashflow": cashflow,
                "fee": 0.0,
                "slippage": 0.0,
            }
        )
    return rows


def _validate_weight_limits(
    weights: pd.Series, config: EvaluatorConfig, timestamp: pd.Timestamp
) -> None:
    gross = float(weights.abs().sum())
    net = float(abs(weights.sum()))
    largest = float(weights.abs().max()) if len(weights) else 0.0
    tolerance = 1e-10
    if gross > config.max_gross_exposure + tolerance:
        raise ValueError(f"gross exposure {gross:.6f} exceeds cap at {timestamp}")
    if net > config.max_abs_net_exposure + tolerance:
        raise ValueError(f"net exposure {net:.6f} exceeds cap at {timestamp}")
    if largest > config.max_symbol_exposure + tolerance:
        raise ValueError(f"symbol exposure {largest:.6f} exceeds cap at {timestamp}")


def _risk_reduction_scale(weights: pd.Series, config: EvaluatorConfig) -> float:
    gross = float(weights.abs().sum())
    net = float(abs(weights.sum()))
    largest = float(weights.abs().max()) if len(weights) else 0.0
    scales = [1.0]
    if gross > config.max_gross_exposure:
        scales.append(config.max_gross_exposure / gross)
    if net > config.max_abs_net_exposure and net > 0.0:
        scales.append(config.max_abs_net_exposure / net)
    if largest > config.max_symbol_exposure:
        scales.append(config.max_symbol_exposure / largest)
    return max(0.0, min(scales))


def _cost_aware_risk_reduction_scale(
    quantities: pd.Series,
    mark_prices: pd.Series,
    transaction_prices: pd.Series,
    equity: float,
    config: EvaluatorConfig,
    execution_cost_rate: float,
) -> float:
    """Find the largest uniformly scaled book that remains capped after its own exit costs."""

    marked_notional = quantities.mul(mark_prices).fillna(0.0)
    if _risk_reduction_scale(marked_notional / equity, config) >= 1.0 - 1e-12:
        return 1.0
    liquidation_notional = float(
        quantities.mul(transaction_prices).abs().replace([np.inf, -np.inf], np.nan).sum()
    )

    def feasible(scale: float) -> bool:
        post_cost_equity = equity - execution_cost_rate * liquidation_notional * (1.0 - scale)
        if post_cost_equity <= 0.0:
            return False
        weights = marked_notional * scale / post_cost_equity
        return _risk_reduction_scale(weights, config) >= 1.0 - 1e-12

    if not feasible(0.0):
        raise ValueError("portfolio cannot be de-risked without execution-cost insolvency")
    low, high = 0.0, 1.0
    for _ in range(80):
        midpoint = (low + high) / 2.0
        if feasible(midpoint):
            low = midpoint
        else:
            high = midpoint
    return low
