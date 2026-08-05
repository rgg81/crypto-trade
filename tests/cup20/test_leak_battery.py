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
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

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


class PeekingProbe:
    """Trades nothing; records the latest bar open_time visible to every decision.

    A direct visibility check, independent of the corrupt-and-diff mechanism below. This battery
    is the pre-tournament gate and must not rely on tests/cup20/test_runner.py's own
    ``PeekingStrategy`` for its tightest causality property -- a forming-candle leak (a strategy
    seeing the bar that opens exactly AT its own decision time, one bar early) sits in a gap the
    corruption fixture below never reaches: the only extra bar such a leak would expose lies in a
    span the corruption never touches (see ``test_future_corruption_does_not_change_any_target``'s
    docstring and the task-14 fix-round-1 report for how this was found).
    """

    def __init__(self):
        self.observations: list[tuple[pd.Timestamp, pd.Timestamp | None]] = []

    def target_weights(self, context, *, seed):
        latest = max(
            (frame["open_time"].max() for frame in context.bars.values() if len(frame)),
            default=None,
        )
        self.observations.append((context.decision_time, latest))
        return None


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
    membership = pd.concat(
        [
            pd.DataFrame(
                {
                    "reconstitution_time": [times[0]] * len(symbols),
                    "symbol": list(symbols),
                    "liquidity_rank": list(range(1, len(symbols) + 1)),
                    "trailing_quote_volume": [1e9] * len(symbols),
                }
            ),
            pd.DataFrame(
                {
                    # A second reconstitution, re-affirming the identical universe -- inert for
                    # every test that only depends on eligibility -- placed after
                    # test_is_snapshot_written_to_disk_contains_no_sealed_row's IS cutoff
                    # (2021-06-01) so that test's sealed-side membership assertions have a genuine
                    # row to exercise. A single reconstitution event, by construction, can never
                    # appear on the sealed side of any split -- found the hard way, as a real
                    # AssertionError, during fix-round 1.
                    "reconstitution_time": [pd.Timestamp("2021-07-01T00:00:00Z")] * len(symbols),
                    "symbol": list(symbols),
                    "liquidity_rank": list(range(1, len(symbols) + 1)),
                    "trailing_quote_volume": [1e9] * len(symbols),
                }
            ),
        ],
        ignore_index=True,
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


# A mirror transform for the corrupted region below: x -> _CORRUPTION_MIRROR - x. Chosen larger
# than any price this fixture's random walk can plausibly produce (empirically, its max OHLC
# value is ~230; verified directly as part of fix-round 1) so every mirrored value stays
# comfortably positive and finite.
_CORRUPTION_MIRROR = 1_000_000.0


def test_future_corruption_does_not_change_any_target():
    """The single most important test in the build: past decisions are blind to the future.

    The corrupted region is mirrored (``x -> _CORRUPTION_MIRROR - x``), not scaled
    (``x -> x * 1000``, this test's original form). A pure scale is a MONOTONE transform: for any
    positive k, ``a * k > b * k`` iff ``a > b``, so a probe whose entire signal is a sign
    comparison of two values -- like MomentumProbe's ``closes[-1] > closes[-31]`` -- cannot tell a
    scaled comparison from an unscaled one whenever BOTH compared points land inside the corrupted
    region. That blind spot is real and was found empirically during fix-round 1: a "delete
    truncation entirely" mutation collapsed every decision's context to the dataset's final bar,
    which pulled the momentum window entirely inside the corrupted region on both ends and the
    signal never flipped despite the strategy genuinely seeing 1000+ forbidden bars. The mirror
    transform has no such blind spot: for ANY a, b drawn from the corrupted region,
    ``a > b`` iff ``_CORRUPTION_MIRROR - a < _CORRUPTION_MIRROR - b`` -- the comparison is
    provably INVERTED, never merely rescaled, so this corruption cannot hide behind any
    monotone-invariant signal the way the original multiplicative form could.
    """
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    cutoff = grid[len(grid) // 2]
    half = grid[: len(grid) // 2]
    baseline = _run(snapshot, half)
    # Not vacuous: assert_frame_equal on two empty (or all-zero) frames would also "pass" without
    # ever exercising the property under test.
    assert len(baseline.targets) == len(half)
    assert baseline.targets.drop(columns=[REBALANCE_INSTRUCTION_COLUMN]).abs().sum().sum() > 0.0

    corrupted_bars = snapshot.bars.copy()
    mask = corrupted_bars["open_time"] >= cutoff
    for column in ("open", "high", "low", "close"):
        corrupted_bars.loc[mask, column] = _CORRUPTION_MIRROR - corrupted_bars.loc[mask, column]
    corrupted = Snapshot(
        corrupted_bars,
        snapshot.funding,
        snapshot.mark_prices,
        snapshot.membership,
        snapshot.contract_metadata,
        manifest_sha256="corrupted",
    )
    after = _run(corrupted, half)
    pd.testing.assert_frame_equal(baseline.targets, after.targets)


def test_no_symbol_context_ever_reaches_or_passes_its_own_decision_boundary():
    """Direct visibility check: no symbol's bar history ever reaches its own decision time.

    Complements ``test_future_corruption_does_not_change_any_target`` above with a mechanism that
    cannot be fooled by any probe's own math (see that test's docstring): this one inspects
    exactly what ``context.bars`` contains at every decision, rather than inferring it indirectly
    from whether corrupting unseen rows changes an output.
    """
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    probe = PeekingProbe()
    run_candidate(probe, snapshot, decision_times=grid, seed=1, config=CONFIG, risk_unit=RISK_UNIT)
    # Not vacuous: an empty or all-None observation list would make the loop below pass having
    # checked nothing.
    assert len(probe.observations) == len(grid)
    assert any(latest is not None for _, latest in probe.observations)
    for decision_time, latest_open in probe.observations:
        if latest_open is not None:
            # A bar opening at `latest_open` closes at `latest_open + 8h` and may equal the
            # decision exactly (DecisionContext's own contract: "bars contains rows whose close
            # time is no later than decision_time"). It must never close AFTER the decision.
            assert latest_open + pd.Timedelta(hours=8) <= decision_time


def test_evaluation_is_bit_reproducible():
    """Two same-seed, same-process runs must be bit-identical, not merely close.

    ``check_exact=True`` on both calls: pandas' default (``check_exact=False``) tolerates roughly
    a 1e-5 relative difference (empirically probed as part of fix-round 1 -- 1e-6 through 1e-9 are
    silently absorbed as "equal", 1e-5 and above reliably raise), which comfortably covers every
    realistic nondeterminism source in this pipeline: summation-order drift, BLAS thread-count
    variance, and dict-iteration accumulation all land at 1e-12 to 1e-15. The property this test's
    name claims is bit reproducibility, not "close enough".
    """
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    first = _run(snapshot, grid)
    second = _run(snapshot, grid)
    # Not vacuous: two empty frames/series would also compare bit-identical.
    assert not first.results[1].returns.empty
    assert not first.risk_scalars.empty
    pd.testing.assert_frame_equal(
        first.results[1].returns, second.results[1].returns, check_exact=True
    )
    pd.testing.assert_series_equal(first.risk_scalars, second.risk_scalars, check_exact=True)


def test_risk_unit_scales_realised_volatility_to_within_a_band_of_the_common_target():
    """A structural guarantee (scaled must differ from unscaled) PLUS a tight band on the ratio to
    target -- neither alone is enough.

    The band alone is not a guaranteed catch: ``scaled_vol ~= target / sqrt(bars_per_year)``, so
    ``ratio ~= sqrt(1095 / B)`` for whatever ``bars_per_year=B`` the implementation actually uses
    -- independent of this fixture's data entirely. Fix-round 1 shipped ``[0.5, 2.0]``, which
    admits any ``B`` in (273.75, 4380): ``B=365`` (annualising 8h bars as if they were daily -- the
    single most plausible mistake) lands at ratio ~1.75, comfortably inside that band. Tightened
    here to ``[0.85, 1.20]``: the real, correctly-scaled pipeline measures ~1.016 (empirically
    probed as part of fix-round 2), keeping ~18% headroom while rejecting ``B=365`` (~1.75),
    ``B=252`` (~2.05), an inert risk unit (~2.01), and a risk unit pinned to ``minimum_scale``
    (~0.40) -- see the fix-round-2 report for the exact reproduction.

    The structural assertion exists because no band, however tight, is a GUARANTEED catch on its
    own: a coincidentally in-range ratio is still possible for some wrong ``B``, and fix-round 1's
    own ``[0.5, 2.0]`` band let the single most realistic wiring bug (an inert risk unit --
    ``run_candidate`` passing unscaled ``targets`` instead of ``scaled_targets``, or
    ``apply_risk_scalars`` degenerating into a no-op) through with only a 0.6% margin. When that
    mutation is present, ``run.results[1]`` and ``run.unscaled`` are evaluated from IDENTICAL
    target weights at the SAME 1x cost multiplier and are therefore bit-identical -- a fact true
    regardless of the fixture's volatility, the target, or any band. ``run.unscaled`` was otherwise
    referenced nowhere in this file.
    """
    snapshot = _synthetic()
    grid = decision_grid(snapshot.bars["open_time"].min(), snapshot.bars["open_time"].max())
    run = _run(snapshot, grid)
    scaled = run.results[1].returns["net_return"]
    unscaled = run.unscaled.returns["net_return"]
    target = 0.10 / np.sqrt(1095)
    tail = slice(300, None)
    # Not vacuous: std() of an empty/all-NaN slice is NaN, and every comparison with NaN is False
    # -- the band assertion below already fails closed on that, but an explicit check here reports
    # the actual cause instead of a bare "assert False".
    assert len(scaled.iloc[tail]) > 0

    # Guaranteed catch, independent of the band: the scaled and unscaled books must not be the
    # same evaluation wearing two names.
    assert not scaled.equals(unscaled)

    ratio = scaled.iloc[tail].std() / target
    assert 0.85 <= ratio <= 1.20


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


# Every dataset write_split_snapshots partitions by time, paired with its time column
# (crypto_trade/cup20/snapshot.py's own _TIME_COLUMN mapping). contract_metadata is timeless and
# is not part of this list -- it carries no time column to leak across the boundary in the first
# place. A future mark-price series or a future top-20 composition (membership) shipped inside the
# IS snapshot handed to teams is exactly as severe a leak as a future bar or funding row, and
# fix-round 1 shipped with neither asserted -- this loop is what closes that gap for every
# time-keyed dataset at once, present and future.
_TIME_KEYED_DATASETS = (
    ("bars", "open_time"),
    ("funding", "funding_time"),
    ("mark_prices", "mark_time"),
    ("membership", "reconstitution_time"),
)


def test_is_snapshot_written_to_disk_contains_no_sealed_row(tmp_path):
    """Blindness is enforced by absence: the IS snapshot on disk must contain no row at or after
    the IS cutoff, in ANY time-keyed dataset -- and the sealed snapshot must contain no row before
    it either.

    ``.max() < cutoff`` / ``.min() >= cutoff``, backed by an explicit non-empty assertion, not
    ``(series < cutoff).all()``: ``.all()`` on an EMPTY boolean series is vacuously ``True`` in
    pandas (verified directly as part of fix-round 1), so a ``_slice`` regression that dropped
    every IS row for one dataset would have passed this test silently. ``.max()`` on an empty
    series is ``NaT``, and every comparison with ``NaT`` is ``False``, so that form fails closed
    even without the explicit guard -- the guard exists so a vacuous case reports its actual cause
    (an empty frame) rather than a bare, confusing comparison failure.
    """
    snapshot = _synthetic()
    cutoff = pd.Timestamp("2021-06-01T00:00:00Z")
    sealed_end = pd.Timestamp("2022-01-01T00:00:00Z")
    is_paths, sealed_paths = write_split_snapshots(
        snapshot.bars,
        snapshot.funding,
        snapshot.mark_prices,
        snapshot.membership,
        snapshot.contract_metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=cutoff,
        sealed_end=sealed_end,
    )
    is_snapshot = load_snapshot(is_paths.root)
    sealed_snapshot = load_snapshot(sealed_paths.root)

    for name, column in _TIME_KEYED_DATASETS:
        is_frame = getattr(is_snapshot, name)
        sealed_frame = getattr(sealed_snapshot, name)
        assert len(is_frame) > 0, f"IS {name} is empty -- fixture or split regressed"
        assert len(sealed_frame) > 0, f"sealed {name} is empty -- fixture or split regressed"
        assert is_frame[column].max() < cutoff, f"IS {name} contains a row at/after the IS cutoff"
        assert sealed_frame[column].min() >= cutoff, (
            f"sealed {name} contains a row before the IS cutoff"
        )


def test_is_snapshot_censors_future_contract_metadata(tmp_path):
    """``contract_metadata`` is timeless (``crypto_trade/cup20/snapshot.py``'s own
    ``_TIME_COLUMN`` mapping) and would otherwise ship WHOLE, unfiltered, into the IS snapshot --
    but ``onboard_date`` and ``delivery_date`` are themselves future universe composition: exactly
    the leak class this battery treats as CRITICAL for ``membership.reconstitution_time``, just
    carried by columns instead of rows. Found live in prior-tournament metadata during fix-round 2
    (147 of 667 symbols carry a genuine delist date; 112 of those fall inside the sealed window),
    not merely as an unasserted test gap.

    A symbol that delists inside the sealed window, and a symbol that isn't even listed until
    inside the sealed window, must both reveal nothing of that in the IS snapshot; the sealed
    snapshot must still carry the truth.
    """
    snapshot = _synthetic()
    cutoff = pd.Timestamp("2021-06-01T00:00:00Z")
    sealed_end = pd.Timestamp("2022-01-01T00:00:00Z")
    # Binance's own real convention for "no delivery date scheduled" -- used here only to build a
    # realistic fixture. write_split_snapshots derives this value from the data itself rather than
    # trusting this literal (see snapshot.py's _perpetual_delivery_sentinel).
    perpetual_sentinel = pd.Timestamp("2100-12-25T08:00:00Z")
    delisting_date = pd.Timestamp("2021-09-01T00:00:00Z")  # inside the sealed window
    onboard_date = pd.Timestamp("2021-08-01T00:00:00Z")  # also inside the sealed window

    existing_symbols = list(snapshot.contract_metadata["symbol"])
    delisting_symbol = existing_symbols[0]
    not_yet_listed_symbol = "EUSDT"
    metadata = pd.DataFrame(
        {
            "symbol": [*existing_symbols, not_yet_listed_symbol],
            "contract_type": "PERPETUAL",
            "onboard_date": [pd.Timestamp("2020-01-01T00:00:00Z")] * len(existing_symbols)
            + [onboard_date],
            "delivery_date": [perpetual_sentinel] * (len(existing_symbols) + 1),
        }
    )
    metadata.loc[metadata["symbol"] == delisting_symbol, "delivery_date"] = delisting_date

    is_paths, sealed_paths = write_split_snapshots(
        snapshot.bars,
        snapshot.funding,
        snapshot.mark_prices,
        snapshot.membership,
        metadata,
        is_root=tmp_path / "is",
        sealed_root=tmp_path / "sealed",
        is_end=cutoff,
        sealed_end=sealed_end,
    )
    is_metadata = load_snapshot(is_paths.root).contract_metadata
    sealed_metadata = load_snapshot(sealed_paths.root).contract_metadata

    # The not-yet-onboarded symbol is entirely absent from the IS snapshot -- its presence alone
    # would leak that it exists before it does -- but present in the sealed one.
    assert not_yet_listed_symbol not in set(is_metadata["symbol"])
    assert not_yet_listed_symbol in set(sealed_metadata["symbol"])

    # The delisting symbol's real future date never appears in the IS snapshot -- censored to the
    # perpetual sentinel, indistinguishable from a genuinely-perpetual contract -- but the sealed
    # snapshot still carries the truth.
    is_row = is_metadata.loc[is_metadata["symbol"] == delisting_symbol]
    assert len(is_row) == 1, "the delisting symbol itself must still be present pre-cutoff"
    assert pd.Timestamp(is_row["delivery_date"].iloc[0]) == perpetual_sentinel
    sealed_row = sealed_metadata.loc[sealed_metadata["symbol"] == delisting_symbol]
    assert len(sealed_row) == 1
    assert pd.Timestamp(sealed_row["delivery_date"].iloc[0]) == delisting_date

    # No row in the IS snapshot carries a real (non-sentinel) date at or after the cutoff.
    is_delivery = pd.to_datetime(is_metadata["delivery_date"], utc=True)
    assert ((is_delivery < cutoff) | (is_delivery == perpetual_sentinel)).all()


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
