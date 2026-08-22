"""The desks cannot trade, and that is enforced rather than promised.

The monitor skill tells a future operator "there is nothing to disable and no key in use". That
sentence is worth exactly as much as the test behind it. These assert the property by inspection of
the runner's actual import graph, so the claim fails loudly if anyone ever adds a signed client, an
order path, or a credential read -- including someone who edits the skill to say otherwise.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "run_cup50v2_paper.py"

# Anything that could sign a request, place an order, or read a credential.
FORBIDDEN_NAMES = (
    "BinanceClient",
    "AuthClient",
    "auth_client",
    "place_market_order",
    "place_algo_stop_market_order",
    "place_algo_take_profit_market_order",
    "cancel_order",
    "set_leverage",
    "get_positions",
    "hmac",
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
)
FORBIDDEN_ENDPOINTS = ("/fapi/v1/order", "/fapi/v1/algoOrder", "/fapi/v2/account", "listenKey")


def _desk_sources() -> list[Path]:
    package = ROOT / "src" / "crypto_trade" / "cup50v2_desk"
    return [RUNNER, *sorted(package.glob("*.py"))]


@pytest.mark.parametrize("path", _desk_sources(), ids=lambda p: p.name)
def test_no_desk_source_can_sign_or_place_an_order(path: Path) -> None:
    source = path.read_text()
    for name in FORBIDDEN_NAMES:
        assert name not in source, f"{path.name} mentions {name}"
    for endpoint in FORBIDDEN_ENDPOINTS:
        assert endpoint not in source, f"{path.name} mentions {endpoint}"


def test_the_runner_imports_only_the_public_client() -> None:
    """The one network client in the runner's own imports is the public, allowlisted one."""
    tree = ast.parse(RUNNER.read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imported.add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    clients = {name for name in imported if "Client" in name}
    assert clients == {"crypto_trade.cup50v2_desk.live_data.PublicMarketDataClient"}, clients


def test_the_public_client_refuses_any_endpoint_outside_its_allowlist() -> None:
    """The allowlist is the thing that makes 'paper only' structural rather than a convention."""
    from crypto_trade.cup50v2_desk import wire

    assert wire.PUBLIC_ENDPOINTS == {
        wire.KLINES_ENDPOINT,
        wire.MARK_PRICE_KLINES_ENDPOINT,
        wire.FUNDING_RATE_ENDPOINT,
        wire.EXCHANGE_INFO_ENDPOINT,
    }
    assert not any(path.startswith("/fapi/v1/order") for path in wire.PUBLIC_ENDPOINTS)

    client = wire.PublicMarketDataClient()
    try:
        # Match the real arity. The first draft passed an extra argument and caught the resulting
        # TypeError, which is a test that would have gone green against a client with no allowlist
        # at all -- the message assertion is the only reason that was noticed.
        with pytest.raises(ValueError, match="/fapi/v1/order"):
            client.get_json("/fapi/v1/order")
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


def test_the_desk_package_imports_no_other_edition() -> None:
    """A desk importing a live edition inherits every edit made to keep that desk alive."""
    package = ROOT / "src" / "crypto_trade" / "cup50v2_desk"
    for path in sorted(package.glob("*.py")):
        source = path.read_text()
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            assert "cup20_desk" not in stripped, f"{path.name}: {stripped}"
            assert "cup50_desk" not in stripped, f"{path.name}: {stripped}"


def test_every_desk_module_imports() -> None:
    import crypto_trade.cup50v2_desk as package

    for info in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"crypto_trade.cup50v2_desk.{info.name}")


@pytest.mark.parametrize("path", _desk_sources(), ids=lambda p: p.name)
def test_no_desk_source_reaches_into_another_edition_s_data(path: Path) -> None:
    """Paths built from string segments survive an import-level namespace rewrite.

    Forking cup50_desk rewrote every `from crypto_trade.cup50.` import, and left five
    `root / "data" / "cup50" / ...` literals untouched. They are invisible to an import rewrite,
    invisible to lint, and invisible to every test that does not actually build a snapshot -- the
    first paper tick found them by trying to open another edition's manifest. This asserts the
    property directly instead of relying on a rewrite having been thorough.
    """
    source = path.read_text()
    for edition in ("cup50", "cup20", "top40"):
        for segment in (f'"{edition}"', f"'{edition}'", f"/{edition}/"):
            assert segment not in source, f"{path.name} names another edition: {segment}"
