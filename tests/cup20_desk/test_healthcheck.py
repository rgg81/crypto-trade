"""The operational shell: the healthcheck, the digest and the runner's engine lock.

Three different kinds of claim are tested here, and they are tested differently.

**The healthcheck names what is wrong.** Every check is exercised by reinstating the exact defect
it exists to catch -- a mutated artifact, a ledger truncated behind the desk's back, a CSV that no
longer renders its ledger, a changed authority digest, a moved pin, a boundary the engine never
reached, a mutated cache file, an engine that is not running -- and asserting the named failure
class appears and the exit status is non-zero. A check nobody has seen fail is a check nobody has
seen work.

The CSV/ledger cross-check needs care to be worth anything. Every artifact is also bound by size,
row count and SHA-256 in ``integrity.json``, so a casually edited CSV is caught by the binding
before the cross-check ever runs. The test therefore edits the CSV *and re-binds it*, which is
exactly the failure the cross-check is for: a desk that rendered its CSV from something other than
its ledger and bound the result faithfully. The ledger is the record; the CSV is a rendering; a
rendering that disagrees is drift no matter how well it is bound.

**The digest reports, it does not judge.** It is a test result. The assertions are that bridge rows
are excluded from every statistic and reported separately as a count, and that a window shorter
than ninety official bars is labelled ``INSUFFICIENT`` and says what it is insufficient for.

**The runner cannot double-tick, sign, or compute an execution number.** The lock is tested against
a real second process, because a lock that only excludes a second call in the same process is not
the property the desk needs. The paper-only and no-duplicated-execution claims are static scans of
the runner's own source, mirroring ``tests/cup20_desk/test_tick.py``.
"""

import ast
import dataclasses
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from crypto_trade.cup20.activation import verify_activation
from crypto_trade.cup20_desk.authority import current_desk_authority
from crypto_trade.cup20_desk.live_data import PublicMarketDataClient, conform_frame
from crypto_trade.cup20_desk.tick import (
    BRIDGE,
    FORWARD_RETURN_SCHEMA,
    OFFICIAL,
    persist_tick,
    run_tick,
)
from tests.cup20_desk.test_live_data import _StubBinance
from tests.cup20_desk.test_tick import (
    AFTER_OFFICIAL_TICK,
    BRIDGE_TICK,
    INTERVAL,
    LAST_CACHED_BAR,
    OFFICIAL_TICK,
    PANEL_START,
    Desk,
    _bars,
    _build_desk,
    _funding,
    _marks,
    _metadata,
    _recorded_membership,
    _steps,
)
from tests.cup20_desk.test_tick import SEAM as FIXTURE_SEAM

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO_ROOT / "run_cup20_paper.py"
HEALTHCHECK_PATH = REPO_ROOT / "scripts" / "cup20_paper_healthcheck.py"
DIGEST_PATH = REPO_ROOT / "scripts" / "cup20_paper_digest.py"
WATCHDOG_PATH = REPO_ROOT / "scripts" / "cup20_paper_watchdog.sh"

LAST_TICK = AFTER_OFFICIAL_TICK + INTERVAL
"""One boundary past ``test_tick``'s last, so the record carries more than one settled row on each
side of the phase change and a statistic over the official rows is not a single number."""

FRESH = LAST_TICK + pd.Timedelta(hours=8, minutes=40)
"""A wall clock at which ``LAST_TICK`` is the newest boundary the desk could have published: the
bar opening at ``LAST_TICK`` closed eight hours later, and the publication lag has since passed."""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = _load(RUNNER_PATH, "cup20_paper_runner")
healthcheck = _load(HEALTHCHECK_PATH, "cup20_paper_healthcheck")
digest = _load(DIGEST_PATH, "cup20_paper_digest")


# --------------------------------------------------------------------------------------------
# a desk that has really ticked
# --------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def authority():
    return current_desk_authority()


@pytest.fixture(scope="module")
def ticked(tmp_path_factory, authority) -> Desk:
    """A desk carried across the phase change on the synthetic universe ``test_tick`` builds.

    Module scoped: every tick is a full-window replay through the tournament's evaluator, and the
    tests below that only READ the result would otherwise pay for it many times over. Every test
    that damages a desk copies this one first.
    """
    bars = _bars(_steps(PANEL_START, LAST_CACHED_BAR + INTERVAL))
    marks = _marks(bars)
    metadata = _metadata()
    panel = {
        "bars": bars,
        "mark_prices": marks,
        "funding": _funding(bars),
        "contract_metadata": metadata,
        "membership": conform_frame("membership", _recorded_membership(bars, marks, metadata)),
    }
    desk = _build_desk(tmp_path_factory.mktemp("healthy") / "desk", panel)
    for boundary in (BRIDGE_TICK, OFFICIAL_TICK, AFTER_OFFICIAL_TICK, LAST_TICK):
        result = run_tick(boundary, authority=authority, **desk.kwargs)
        persist_tick(result, desk.root)
    _arm_engine_lock(desk.root)
    return desk


def _arm_engine_lock(root: Path) -> None:
    """Leave a held engine lock behind, so the liveness check has something to find."""
    handle = (root / "engine.lock").open("a+", encoding="utf-8")
    runner.fcntl.flock(handle.fileno(), runner.fcntl.LOCK_EX | runner.fcntl.LOCK_NB)
    handle.seek(0)
    handle.truncate()
    handle.write(f"{os.getpid()}\n")
    handle.flush()
    # Deliberately leaked for the lifetime of the module: closing it drops the lock.
    _HELD.append(handle)


_HELD: list[Any] = []


@pytest.fixture
def desk(tmp_path: Path, ticked: Desk) -> Desk:
    """A private copy of the ticked desk, for the tests that damage one."""
    root = tmp_path / "desk"
    shutil.copytree(ticked.root, root)
    return Desk(root=root, is_root=root / "is", sealed_root=root / "sealed")


def _check(root: Path, **overrides):
    # ``seam`` is the fixture universe's own seam; production defaults to the tournament's
    # ``SEALED_END``, which the synthetic panel deliberately does not use.
    arguments: dict[str, object] = {"now": FRESH, "check_process": False, "seam": FIXTURE_SEAM}
    arguments.update(overrides)
    return healthcheck.check_desk(root, **arguments)


def _classes(report) -> set[str]:
    return {alert.split(":", 1)[0] for alert in report.alerts}


def _integrity(root: Path) -> dict[str, Any]:
    return json.loads((root / "integrity.json").read_text())


def _write_integrity(root: Path, payload: dict[str, Any]) -> None:
    (root / "integrity.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _rebind(root: Path, name: str) -> None:
    """Re-bind one artifact to its current bytes, the way a tick would have bound them.

    Used only by the CSV/ledger test: without it the size/row/digest binding fires first and the
    cross-check is never reached, which would let the cross-check rot undetected.
    """
    payload = _integrity(root)
    binding = payload["artifacts"][name]
    path = root / binding["path"]
    binding["size"] = path.stat().st_size
    binding["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    binding["rows"] = max(len(lines) - 1, 0)
    _write_integrity(root, payload)


# --------------------------------------------------------------------------------------------
# the healthy case
# --------------------------------------------------------------------------------------------


def test_a_healthy_desk_reports_status_ok(ticked: Desk):
    report = _check(ticked.root)
    assert report.alerts == (), report.render()
    assert report.ok
    assert report.render().startswith("STATUS OK")


def test_the_liveness_check_finds_the_held_engine_lock(ticked: Desk):
    report = _check(ticked.root, check_process=True)
    assert healthcheck.ENGINE_DOWN not in _classes(report), report.render()


def test_the_healthcheck_exits_zero_on_a_healthy_desk(ticked: Desk, monkeypatch):
    monkeypatch.setattr(healthcheck, "SEALED_END", FIXTURE_SEAM)
    assert (
        healthcheck.main(
            ["--desk-dir", str(ticked.root), "--now", FRESH.isoformat(), "--skip-process"]
        )
        == 0
    )


# --------------------------------------------------------------------------------------------
# the failure classes
# --------------------------------------------------------------------------------------------


def test_a_mutated_artifact_is_named(desk: Desk):
    path = desk.root / "latest-boundary.json"
    payload = json.loads(path.read_text())
    payload["risk_scalar"] = 0.5
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    report = _check(desk.root)
    assert healthcheck.ARTIFACT_DRIFT in _classes(report), report.render()
    assert not report.ok


def test_a_truncated_ledger_is_an_append_invariance_abort(desk: Desk):
    path = desk.root / "ledger" / "forward_returns.parquet"
    ledger = pd.read_parquet(path)
    ledger.iloc[:-2].to_parquet(path, index=False)
    report = _check(desk.root)
    assert healthcheck.APPEND_INVARIANCE_ABORT in _classes(report), report.render()


def test_a_csv_that_disagrees_with_its_ledger_is_drift(desk: Desk):
    """Re-bound, so the size/row/digest binding passes and only the cross-check can catch it."""
    path = desk.root / "forward_returns.csv"
    rendered = pd.read_csv(path)
    rendered.loc[0, "net_return"] = 0.123456
    path.write_text(rendered.to_csv(index=False))
    _rebind(desk.root, "forward_returns")
    report = _check(desk.root)
    assert healthcheck.LEDGER_CSV_MISMATCH in _classes(report), report.render()


def test_an_authority_digest_change_is_named(desk: Desk):
    payload = _integrity(desk.root)
    payload["strategy_sha256"] = "0" * 64
    _write_integrity(desk.root, payload)
    report = _check(desk.root)
    assert healthcheck.AUTHORITY_DRIFT in _classes(report), report.render()
    assert any("strategy_sha256" in alert for alert in report.alerts)


@pytest.mark.parametrize("field", ["is_start", "seam", "official_start"])
def test_a_moved_pin_is_named(desk: Desk, field: str):
    payload = _integrity(desk.root)
    payload[field] = (pd.Timestamp(payload[field]) + pd.Timedelta(days=7)).isoformat()
    _write_integrity(desk.root, payload)
    report = _check(desk.root)
    assert healthcheck.PIN_DRIFT in _classes(report), report.render()
    assert any(field in alert for alert in report.alerts)


def test_a_stale_boundary_is_named(ticked: Desk):
    report = _check(ticked.root, now=FRESH + pd.Timedelta(days=3))
    assert healthcheck.STALE_BOUNDARY in _classes(report), report.render()


def test_a_mutated_cache_file_is_named(desk: Desk):
    path = desk.root / "cache" / "mark_prices.parquet"
    marks = pd.read_parquet(path)
    marks.loc[0, "mark_price"] = 1.0
    marks.to_parquet(path, index=False)
    report = _check(desk.root)
    assert healthcheck.CACHE_DRIFT in _classes(report), report.render()


def test_a_missing_engine_is_named(desk: Desk):
    (desk.root / "engine.lock").unlink(missing_ok=True)
    report = _check(desk.root, check_process=True)
    assert healthcheck.ENGINE_DOWN in _classes(report), report.render()


def test_an_unheld_engine_lock_is_a_missing_engine(desk: Desk):
    (desk.root / "engine.lock").write_text("999999\n")
    report = _check(desk.root, check_process=True)
    assert healthcheck.ENGINE_DOWN in _classes(report), report.render()


def test_a_failed_attempt_marker_is_reported(desk: Desk):
    (desk.root / "attempt.json").write_text(
        json.dumps(
            {
                "status": "FAIL",
                "boundary": LAST_TICK.isoformat(),
                "started_at": FRESH.isoformat(),
                "error": "BinancePublicDataError: barred",
            }
        )
    )
    report = _check(desk.root)
    assert healthcheck.TICK_FAILED in _classes(report), report.render()


def test_missing_artifacts_are_named(tmp_path: Path):
    report = _check(tmp_path / "empty")
    assert healthcheck.ARTIFACTS_MISSING in _classes(report), report.render()


def test_the_healthcheck_exits_non_zero_on_a_failure(desk: Desk):
    (desk.root / "forward_returns.csv").write_text("nonsense\n")
    assert (
        healthcheck.main(
            ["--desk-dir", str(desk.root), "--now", FRESH.isoformat(), "--skip-process"]
        )
        == 1
    )


def test_every_named_failure_class_is_reachable_from_the_module():
    for name in healthcheck.FAILURE_CLASSES:
        assert isinstance(name, str) and name == name.upper()
    for required in (
        "AUTHORITY DRIFT",
        "PIN DRIFT",
        "APPEND-INVARIANCE ABORT",
        "CACHE DRIFT",
        "STALE BOUNDARY",
        "LEDGER/CSV MISMATCH",
        "ENGINE DOWN",
    ):
        assert required in healthcheck.FAILURE_CLASSES


# --------------------------------------------------------------------------------------------
# the digest
# --------------------------------------------------------------------------------------------


def _ledger(root: Path, phases: list[str], *, offset: int = 0) -> Path:
    """A forward ledger of ``phases``, one row per 8h boundary, in the tick's own schema.

    Every value is a function of the row's ABSOLUTE step, so two ledgers whose official rows land
    on the same boundaries carry identical official values however many bridge rows precede them.
    That is what lets the exclusion test compare two summaries field by field.
    """
    rows = []
    for index, phase in enumerate(phases):
        step = offset + index
        row: dict[str, Any] = {"timestamp": PANEL_START + step * INTERVAL, "phase": phase}
        for column in FORWARD_RETURN_SCHEMA.columns:
            if column in row:
                continue
            if column == "risk_cap_breach":
                row[column] = False
            elif column in ("risk_policy_id", "risk_policy_reasons"):
                row[column] = ""
            else:
                row[column] = 0.0
        # The bridge rows carry a large, distinctive value in every statistic-bearing column, so a
        # statistic that failed to exclude them could not accidentally agree with one that did.
        magnitude = 1.0 if phase == BRIDGE else 0.01
        row["net_return"] = magnitude * (1.0 if step % 2 else -1.0)
        row["turnover"] = magnitude
        row["gross_exposure"] = magnitude
        row["net_exposure"] = magnitude
        row["long_exposure"] = magnitude
        row["short_exposure"] = magnitude
        row["fees"] = magnitude
        row["slippage"] = magnitude
        rows.append(row)
    frame = conform_frame(FORWARD_RETURN_SCHEMA, pd.DataFrame(rows))
    ledger = root / "ledger"
    ledger.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(ledger / "forward_returns.parquet", index=False)
    return ledger / "forward_returns.parquet"


def test_the_digest_excludes_bridge_rows_from_every_statistic(tmp_path: Path):
    only_official = tmp_path / "official"
    mixed = tmp_path / "mixed"
    _ledger(only_official, [OFFICIAL] * 120, offset=30)
    _ledger(mixed, [BRIDGE] * 30 + [OFFICIAL] * 120)
    clean = digest.summarise(only_official)
    contaminated = digest.summarise(mixed)
    assert contaminated.bridge_bars == 30
    assert clean.bridge_bars == 0
    assert contaminated.official_bars == clean.official_bars == 120
    for field in dataclasses.fields(digest.Digest):
        if field.name in ("bridge_bars", "bridge_fills"):
            continue
        assert getattr(contaminated, field.name) == getattr(clean, field.name), field.name


def test_the_digest_reports_the_bridge_row_count_separately(tmp_path: Path):
    _ledger(tmp_path, [BRIDGE] * 7 + [OFFICIAL] * 95)
    summary = digest.summarise(tmp_path)
    assert summary.bridge_bars == 7
    assert "bridge" in summary.render().lower()
    assert "7" in summary.render()


def test_fewer_than_ninety_official_bars_is_insufficient(tmp_path: Path):
    _ledger(tmp_path, [BRIDGE] * 200 + [OFFICIAL] * 89)
    summary = digest.summarise(tmp_path)
    assert not summary.sufficient
    rendered = summary.render()
    assert "INSUFFICIENT" in rendered
    assert str(digest.MINIMUM_OFFICIAL_BARS) in rendered
    assert "insufficient for" in rendered.lower()


def test_ninety_official_bars_is_sufficient(tmp_path: Path):
    _ledger(tmp_path, [OFFICIAL] * digest.MINIMUM_OFFICIAL_BARS)
    summary = digest.summarise(tmp_path)
    assert summary.sufficient
    assert "INSUFFICIENT" not in summary.render()


def test_a_desk_with_no_official_rows_summarises_rather_than_raising(tmp_path: Path):
    """The two states every desk passes through before its first official bar must both report.

    A desk that has never ticked has no ledger at all; a desk inside the unscored bridge has one
    holding only bridge rows. Neither can be handed to the tournament's `window_metrics` -- an
    empty window's daily index is not tz-aware and the quarterly grouping raises on it -- and both
    are ordinary states the monitor reads routinely, so the digest must render them.
    """
    never_ticked = tmp_path / "never-ticked"
    never_ticked.mkdir()
    bridge_only = tmp_path / "bridge-only"
    _ledger(bridge_only, [BRIDGE] * 12)

    for root in (never_ticked, bridge_only):
        summary = digest.summarise(root)
        assert summary.official_bars == 0
        assert summary.official_days == 0
        assert not summary.sufficient
        assert "INSUFFICIENT" in summary.render()
    assert digest.summarise(bridge_only).bridge_bars == 12


def test_the_digest_states_no_verdict(tmp_path: Path):
    _ledger(tmp_path, [OFFICIAL] * 120)
    rendered = digest.summarise(tmp_path).render().lower()
    for verdict in ("good", "bad", "pass", "fail", "alert", "warning", "target", "threshold"):
        assert verdict not in rendered, verdict


def test_the_digest_runs_against_a_real_desk(ticked: Desk):
    summary = digest.summarise(ticked.root)
    assert summary.bridge_bars > 0
    assert summary.official_bars > 0
    assert not summary.sufficient
    assert digest.main(["--desk-dir", str(ticked.root)]) == 0


# --------------------------------------------------------------------------------------------
# the runner
# --------------------------------------------------------------------------------------------


_LOCK_PROBE = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("probe_runner", {runner!r})
module = importlib.util.module_from_spec(spec)
sys.modules["probe_runner"] = module
spec.loader.exec_module(module)
try:
    with module.single_engine_lock({root!r}):
        print("ACQUIRED")
except module.EngineLockError as exc:
    print("REFUSED")
"""


def _probe(root: Path) -> str:
    script = _LOCK_PROBE.format(runner=str(RUNNER_PATH), root=str(root))
    finished = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )
    assert finished.returncode == 0, finished.stderr
    return finished.stdout.strip()


def test_the_engine_lock_excludes_a_second_process(tmp_path: Path):
    root = tmp_path / "desk"
    assert _probe(root) == "ACQUIRED", "a free lock must be acquirable"
    with runner.single_engine_lock(root):
        assert _probe(root) == "REFUSED"
    assert _probe(root) == "ACQUIRED", "the lock must be released when the holder exits"


def test_the_engine_lock_records_the_live_holder(tmp_path: Path):
    root = tmp_path / "desk"
    (root).mkdir(parents=True)
    (root / "engine.lock").write_text("123456\n")
    with runner.single_engine_lock(root):
        assert (root / "engine.lock").read_text().strip() == str(os.getpid())


def test_the_publication_lag_never_ticks_an_unclosed_bar():
    """A boundary is ready only once its own bar has closed AND the lag has elapsed.

    The evaluator reads the fill bar's own quote volume for the participation cap and its close for
    the mark-to-market, so a boundary whose bar is still forming would produce fills that change on
    the next tick -- an append-invariance abort every single tick, forever.
    """
    lag = runner.DEFAULT_LAG_SECONDS
    boundary = pd.Timestamp("2026-08-14T08:00:00Z")
    closed = boundary + INTERVAL
    assert runner.ready_boundary(closed - pd.Timedelta(seconds=1), lag) < boundary
    assert runner.ready_boundary(closed + pd.Timedelta(seconds=lag - 1), lag) < boundary
    assert runner.ready_boundary(closed + pd.Timedelta(seconds=lag), lag) == boundary
    assert runner.ready_boundary(closed + pd.Timedelta(hours=7), lag) == boundary


def test_the_symbol_universe_is_the_eligible_cross_section():
    payload = {
        "symbols": [
            _info("BTCUSDT"),
            _info("ETHUSDT"),
            _info("DELISTEDUSDT", status="SETTLING"),
            _info("BTCUSDC", quoteAsset="USDC"),
            _info("BTCUSD_PERP", marginAsset="BTC"),
            _info("ETHUSDT_240329", contractType="CURRENT_QUARTER"),
            _info("SP500USDT", underlyingType="INDEX"),
        ]
    }
    assert runner.tradable_symbols(payload) == ("BTCUSDT", "ETHUSDT")


def _info(symbol: str, **overrides: str) -> dict[str, str]:
    record = {
        "symbol": symbol,
        "status": "TRADING",
        "contractType": "PERPETUAL",
        "quoteAsset": "USDT",
        "marginAsset": "USDT",
        "underlyingType": "COIN",
    }
    record.update(overrides)
    return record


def test_the_cache_records_no_funding_the_tournament_already_sealed(tmp_path: Path):
    """Bars and marks reach back a full lookback; funding starts at the seam and not before.

    The two sources answer different questions about ``funding_interval_hours`` -- the archives
    publish the contractual schedule, the REST endpoint publishes nothing and the desk derives the
    observed spacing -- so where the venue skips a settlement they disagree honestly, and
    ``snapshot_forward._stack`` refuses any disagreement. Measured against the real venue: 2 of 2098
    overlapping rows, from a settlement ``HYPEUSDT`` missed on 2026-06-24.
    """
    seam = pd.Timestamp("2026-07-15T00:00:00Z")
    boundary = pd.Timestamp("2026-07-20T00:00:00Z")
    stub = _StubBinance()
    with PublicMarketDataClient(transport=stub.transport(), sleep=lambda _s: None) as client:
        runner.refresh_cache(tmp_path, boundary, client=client, lookback_days=-11, seam=seam)
    funding = pd.read_parquet(tmp_path / "cache" / "funding.parquet")
    bars = pd.read_parquet(tmp_path / "cache" / "bars.parquet")
    marks = pd.read_parquet(tmp_path / "cache" / "mark_prices.parquet")
    assert not funding.empty and not bars.empty
    assert funding["funding_time"].min() >= seam
    assert bars["open_time"].min() < seam, "the wide history must reach back past the seam"
    assert marks["mark_time"].min() < seam


def test_the_history_window_covers_a_complete_liquidity_lookback():
    boundary = pd.Timestamp("2026-08-14T08:00:00Z")
    start = runner.history_start(boundary, lookback_days=180)
    assert boundary - start >= pd.Timedelta(days=180)
    assert start == start.floor("8h")


ARITHMETIC = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)

FORBIDDEN_IN_ARITHMETIC = re.compile(
    r"price|fee|slipp|notional|quantity|weight|equity|pnl|turnover|scalar"
)
"""The quantities execution owns. Lowercase and case sensitive, exactly as ``test_tick`` does it:
a reference to one of these numbers is written ``row["price"]``, while an ALL-CAPS constant naming
a file or a schema is not a reference to a number."""


def test_the_runner_computes_no_execution_arithmetic():
    tree = ast.parse(RUNNER_PATH.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp | ast.AugAssign) and isinstance(node.op, ARITHMETIC):
            rendered = ast.unparse(node)
            assert not FORBIDDEN_IN_ARITHMETIC.search(rendered), rendered


def test_the_runner_cannot_sign_or_place_an_order():
    source = RUNNER_PATH.read_text()
    for forbidden in (
        "hmac",
        "api_key",
        "api_secret",
        "signature",
        "X-MBX-APIKEY",
        "place_market_order",
        "place_order",
        "create_order",
        "/fapi/v1/order",
        "BinanceClient",
        "AuthClient",
    ):
        assert forbidden not in source, forbidden


def test_the_watchdog_refuses_to_start_a_second_engine():
    source = WATCHDOG_PATH.read_text()
    assert os.access(WATCHDOG_PATH, os.X_OK), "the watchdog must be executable"
    assert "flock" in source
    assert "engine.lock" in source
    assert "run_cup20_paper.py" in source
    assert "PYTHONUNBUFFERED=1" in source


def test_the_watchdog_starts_the_runner_when_the_lock_is_free(tmp_path: Path):
    """Run the real script against a stand-in runner, and read what it did out of its own log."""
    root = tmp_path / "worktree"
    (root / "scripts").mkdir(parents=True)
    (root / "logs").mkdir()
    shutil.copy(WATCHDOG_PATH, root / "scripts" / WATCHDOG_PATH.name)
    # A stand-in engine that takes the real lock the watchdog probes, and holds it.
    (root / "run_cup20_paper.py").write_text(
        "import fcntl, pathlib, time\n"
        "path = pathlib.Path(__file__).parent / 'paper-cup20' / 'engine.lock'\n"
        "path.parent.mkdir(parents=True, exist_ok=True)\n"
        "handle = path.open('a+')\n"
        "fcntl.flock(handle.fileno(), fcntl.LOCK_EX)\n"
        "time.sleep(60)\n"
    )
    script = (root / "scripts" / WATCHDOG_PATH.name).read_text()
    script = script.replace(
        "ROOT=/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top20-low-dd",
        f"ROOT={root}",
    ).replace("UV=/home/roberto/.local/bin/uv", f"UV={sys.executable}")
    script = script.replace('"$UV" run python run_cup20_paper.py', '"$UV" run_cup20_paper.py')
    (root / "scripts" / WATCHDOG_PATH.name).write_text(script)
    os.chmod(root / "scripts" / WATCHDOG_PATH.name, 0o755)

    first = subprocess.run(
        [str(root / "scripts" / WATCHDOG_PATH.name)], capture_output=True, text=True, timeout=120
    )
    assert first.returncode == 0, first.stderr
    log = root / "logs" / "cup20_paper_watchdog.log"
    engine_lock = root / "paper-cup20" / "engine.lock"
    deadline = time.time() + 30
    while time.time() < deadline and not _lock_held(engine_lock):
        time.sleep(0.2)
    assert "started" in log.read_text(), log.read_text()
    assert _lock_held(engine_lock), "the started engine never took the lock"

    try:
        second = subprocess.run(
            [str(root / "scripts" / WATCHDOG_PATH.name)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert second.returncode == 0, second.stderr
        assert "already running" in log.read_text(), log.read_text()
        assert log.read_text().count("started") == 1, log.read_text()
    finally:
        subprocess.run(["pkill", "-f", str(root / "run_cup20_paper.py")], check=False)


def _lock_held(path: Path) -> bool:
    if not path.is_file():
        return False
    return subprocess.run(["flock", "-n", str(path), "-c", "true"]).returncode != 0


def test_activation_freeze_still_verifies(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    verify_activation("tournament/cup20/activation-freeze.json")
