"""Every check that must pass before a single team is allowed to start.

A leak test is never adjusted to make it pass. If one of these fails, the assembled pipeline (or
the module it exercises) is wrong -- stop and fix the implementation, never the assertion.
"""

import ast
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import crypto_trade.cup20 as cup20
from crypto_trade.cup20.runner import decision_grid, run_candidate
from crypto_trade.cup20.snapshot import Snapshot, load_snapshot, write_split_snapshots
from crypto_trade.tournament.engine_v2 import EvaluatorConfig

# EvaluatorConfig's own defaults (max_abs_net_exposure=0.25, max_symbol_exposure=0.10) are
# tighter than CUP-20 policy, so every CUP-20 caller must build the config explicitly (see
# crypto_trade.cup20.runner.evaluator_config) rather than relying on the bare dataclass defaults.
# max_symbol_exposure=0.30 here, not the production 0.20: MomentumProbe below splits unit gross
# evenly across every eligible symbol, and this fixture has only 4 symbols (0.25 each magnitude)
# versus production's 20-symbol book (0.05 each) -- 0.20 would put the fixture's own equal-weight
# book above its own cap, and the evaluator's `_validate_weight_limits` is a hard RAISE, never a
# silent scale-down. 0.30 stays strictly above the fixture's 0.25 and strictly below
# max_gross_exposure=1.0, so the symbol cap remains capable of binding (not algebraically inert)
# without spuriously rejecting this fixture's own honest equal-weight book.
CONFIG = EvaluatorConfig(max_gross_exposure=1.0, max_abs_net_exposure=1.0, max_symbol_exposure=0.30)
RISK_UNIT = {"target_annualized_volatility": 0.10, "lookback_days": 90}


class MomentumProbe:
    """A realistic causal strategy: sign of the trailing 30-bar return, equal weight."""

    def target_weights(self, context, *, seed):
        weights = {}
        for symbol, frame in context.bars.items():
            if len(frame) < 31:
                continue
            closes = frame["close"].to_numpy(dtype=float)
            weights[symbol] = 1.0 if closes[-1] > closes[-31] else -1.0
        if not weights:
            return {}
        scale = 1.0 / len(weights)
        return {symbol: value * scale for symbol, value in weights.items()}


def _synthetic(seed=3, symbols=("AUSDT", "BUSDT", "CUSDT", "DUSDT")):
    times = pd.date_range("2021-01-01T00:00:00Z", periods=900, freq="8h")
    rng = np.random.default_rng(seed)
    frames = []
    # NOTE: the evaluator's `_normalise_funding` (crypto_trade.tournament.engine_v2) requires a
    # `mark_price` column on the funding frame -- used to price funding cashflows -- in addition
    # to `funding_time`/`symbol`/`funding_rate`. tests/cup20/test_runner.py's own fixture carries
    # the identical note. `prices` is kept so the funding frame can reuse each symbol's own price
    # series, pricing funding cashflows consistently with the bars.
    prices: dict[str, np.ndarray] = {}
    for symbol in symbols:
        price = 100.0 * np.cumprod(1.0 + rng.normal(0.0002, 0.012, len(times)))
        prices[symbol] = price
        frames.append(
            pd.DataFrame(
                {
                    "open_time": times,
                    "symbol": symbol,
                    "open": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price,
                    "volume": 1e6,
                    "quote_volume": 1e9,
                }
            )
        )
    bars = pd.concat(frames, ignore_index=True)
    funding = pd.DataFrame(
        {
            "funding_time": np.tile(times, len(symbols)),
            "symbol": np.repeat(list(symbols), len(times)),
            "funding_rate": 0.0001,
            "mark_price": np.concatenate([prices[symbol] for symbol in symbols]),
        }
    )
    marks = bars[["open_time", "symbol", "open"]].rename(
        columns={"open_time": "mark_time", "open": "mark_price"}
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": [times[0]] * len(symbols),
            "symbol": list(symbols),
            "liquidity_rank": list(range(1, len(symbols) + 1)),
            "trailing_quote_volume": [1e9] * len(symbols),
        }
    )
    metadata = pd.DataFrame({"symbol": list(symbols), "contract_type": "PERPETUAL"})
    return Snapshot(bars, funding, marks, membership, metadata, manifest_sha256="synthetic")


def _run(snapshot, grid, seed=42):
    return run_candidate(
        MomentumProbe(),
        snapshot,
        decision_times=grid,
        seed=seed,
        config=CONFIG,
        risk_unit=RISK_UNIT,
    )


def test_future_corruption_does_not_change_any_target():
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    cutoff = grid[len(grid) // 2]
    baseline = _run(snapshot, grid[: len(grid) // 2])

    corrupted_bars = snapshot.bars.copy()
    mask = corrupted_bars["open_time"] >= cutoff
    for column in ("open", "high", "low", "close"):
        corrupted_bars.loc[mask, column] *= 1000.0
    corrupted = Snapshot(
        corrupted_bars,
        snapshot.funding,
        snapshot.mark_prices,
        snapshot.membership,
        snapshot.contract_metadata,
        manifest_sha256="corrupted",
    )
    after = _run(corrupted, grid[: len(grid) // 2])
    pd.testing.assert_frame_equal(baseline.targets, after.targets)


def test_evaluation_is_bit_reproducible():
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    first = _run(snapshot, grid)
    second = _run(snapshot, grid)
    pd.testing.assert_frame_equal(first.results[1].returns, second.results[1].returns)
    pd.testing.assert_series_equal(first.risk_scalars, second.risk_scalars)


def test_risk_unit_moves_realised_volatility_toward_the_common_target():
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = _run(snapshot, grid)
    scaled = run.results[1].returns["net_return"]
    unscaled = run.unscaled.returns["net_return"]
    tail = slice(300, None)
    assert abs(scaled.iloc[tail].std() - 0.10 / np.sqrt(1095)) < abs(
        unscaled.iloc[tail].std() - 0.10 / np.sqrt(1095)
    )


def test_costs_are_strictly_monotone_in_the_multiplier():
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = _run(snapshot, grid)
    costs = {
        multiplier: float(result.returns["fees"].sum() + result.returns["slippage"].sum())
        for multiplier, result in run.results.items()
    }
    assert costs[1] < costs[2] < costs[3]


def test_a_flat_strategy_earns_no_funding_and_no_costs():
    class Flat:
        def target_weights(self, context, *, seed):
            return {}

    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = run_candidate(
        Flat(), snapshot, decision_times=grid, seed=1, config=CONFIG, risk_unit=RISK_UNIT
    )
    frame = run.results[1].returns
    assert float(frame["funding_pnl"].abs().sum()) == pytest.approx(0.0, abs=1e-12)
    assert float(frame["fees"].sum() + frame["slippage"].sum()) == pytest.approx(0.0, abs=1e-12)


def test_is_snapshot_written_to_disk_contains_no_sealed_row(tmp_path):
    snapshot = _synthetic()
    cutoff = pd.Timestamp("2021-06-01T00:00:00Z")
    is_paths, sealed_paths = write_split_snapshots(
        snapshot.bars,
        snapshot.funding,
        snapshot.mark_prices,
        snapshot.membership,
        snapshot.contract_metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=cutoff,
        sealed_end=pd.Timestamp("2022-01-01T00:00:00Z"),
    )
    reloaded = load_snapshot(is_paths.root)
    assert (reloaded.bars["open_time"] < cutoff).all()
    assert (reloaded.funding["funding_time"] < cutoff).all()
    assert load_snapshot(sealed_paths.root).bars["open_time"].min() >= cutoff


# --- Public-surface completeness -----------------------------------------------------------
#
# The brief's own hardcoded __all__ list predates several functions added to cup20 modules during
# their individual review rounds (metrics.sharpe, metrics.max_drawdown,
# archive.verify_neighbourhood_coordinates) and would have silently under-exported the package had
# it been transcribed as-is -- exactly the failure mode this pair of tests exists to make
# permanently self-detecting. A future module addition must now be a conscious export-or-excuse
# decision, never a name nobody remembered to wire up.

_CUP20_ROOT = Path(cup20.__file__).parent

# Module-level names that are genuinely public (no leading underscore) but are internal tuning
# constants or type aliases, never meant to be part of the package's callable surface. Verified by
# direct reading of every cup20/*.py file as part of this task.
_INTENTIONALLY_UNEXPORTED: dict[str, frozenset[str]] = {
    "archive.py": frozenset({"FORBIDDEN_PATTERNS"}),
    "journal.py": frozenset({"SCHEMA_VERSION"}),
    "metrics.py": frozenset(
        {
            "DAYS_PER_YEAR",
            "Fold",
            "UNDEFINED_CALMAR",
            "UNDEFINED_COST_SHARE",
            "MINIMUM_IS_WINDOW",
            "MINIMUM_HOLDOUT_WINDOW",
        }
    ),
    "universe.py": frozenset({"MEMBERSHIP_COLUMNS"}),
}


def _module_level_public_names(path: Path) -> set[str]:
    """Every module-level def/class/assignment name in ``path`` that doesn't start with ``_``.

    AST-based, not live-namespace introspection: a name reaching a submodule's namespace only via
    ``from other_module import name`` (there are many -- every cup20 module imports helpers from
    its neighbours and from crypto_trade.tournament) must never be mistaken for something that
    module itself defines and should export. ``ast.parse`` only sees genuine ``FunctionDef`` /
    ``ClassDef`` / ``Assign`` / ``AnnAssign`` nodes; ``Import`` / ``ImportFrom`` are distinct,
    excluded node types, so this sidesteps that ambiguity entirely rather than trying to resolve
    it via ``__module__`` (which plain constants such as tuples don't even carry).
    """
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if not node.target.id.startswith("_"):
                names.add(node.target.id)
    return names


def test_every_module_level_public_definition_is_exported_or_explicitly_excused():
    for path in sorted(_CUP20_ROOT.glob("*.py")):
        if path.name == "__init__.py":
            continue
        defined = _module_level_public_names(path)
        excused = _INTENTIONALLY_UNEXPORTED.get(path.name, frozenset())
        unexported = defined - excused - set(cup20.__all__)
        assert not unexported, (
            f"{path.name} defines {sorted(unexported)} at module level without exporting or "
            "explicitly excusing it in _INTENTIONALLY_UNEXPORTED"
        )


def test_all_exports_are_importable_and_the_package_namespace_has_nothing_extra():
    for name in cup20.__all__:
        assert hasattr(cup20, name), f"{name!r} is declared in __all__ but not importable"
    assert len(cup20.__all__) == len(set(cup20.__all__)), "__all__ contains a duplicate name"

    # Everything __init__.py actually bound into the package namespace, minus dunders and the
    # submodule objects that Python's import system binds onto a package as a side effect of
    # `from crypto_trade.cup20.X import ...` (crypto_trade.cup20.archive, .bootstrap, ... become
    # real, harmless attributes of the package this way -- just never part of the declared public
    # API, so they must not be counted as if they were).
    exposed = {
        name
        for name, value in vars(cup20).items()
        if not name.startswith("_") and not isinstance(value, types.ModuleType)
    }
    assert exposed == set(cup20.__all__)
