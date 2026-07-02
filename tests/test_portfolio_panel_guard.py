"""Panel-completeness guard: the engine must not rebalance on a degraded kline fetch.

At an 8h boundary some symbols' new candle can lag or their fetch can transiently error (production
API load at 00/08/16:00). Rebalancing on that incomplete cross-section ranks marginal names wrong
and carries a slightly-off book until the next 8h rebalance (observed 2026-07-02 00:00: 475/513 ok,
40 skipped, which kept 2 marginal names). refresh_data_complete retries the fetch while too many
symbols are missing, bounded so the loop never hangs.
"""

import sys

sys.path.insert(0, "src")

import pytest


def _engine(tmp_path, **cfg_overrides):
    from crypto_trade.config import load_settings
    from crypto_trade.portfolio.engine import PortfolioConfig, PortfolioEngine

    cfg = PortfolioConfig(
        dry_run=True,
        db_path=str(tmp_path / "guard.db"),
        panel_retry_wait_s=0,  # no real waiting in tests
        panel_max_retries=6,
        min_panel_ok_fraction=0.95,
        **cfg_overrides,
    )
    return PortfolioEngine(cfg, load_settings())


def _stub_refresh(eng, monkeypatch, sequence):
    """Make refresh_data yield successive (ok, skipped) tuples; count sleeps."""
    calls = {"refresh": 0, "sleep": 0}
    seq = list(sequence)

    def fake_refresh():
        i = min(calls["refresh"], len(seq) - 1)
        calls["refresh"] += 1
        return seq[i]

    monkeypatch.setattr(eng, "refresh_data", fake_refresh)
    monkeypatch.setattr(
        "crypto_trade.portfolio.engine.time.sleep",
        lambda *_a, **_k: calls.__setitem__("sleep", calls["sleep"] + 1),
    )
    return calls


def test_clean_panel_no_retry(tmp_path, monkeypatch):
    """A complete fetch (2/513 skipped) rebalances immediately — no wait, no re-fetch."""
    eng = _engine(tmp_path)
    calls = _stub_refresh(eng, monkeypatch, [(511, 2)])
    ok, skipped = eng.refresh_data_complete()
    assert (ok, skipped) == (511, 2)
    assert calls["refresh"] == 1  # fetched once
    assert calls["sleep"] == 0  # never waited


def test_degraded_then_recovers(tmp_path, monkeypatch):
    """A degraded fetch (40 skipped = 7.8%) waits + re-fetches; once complete it proceeds."""
    eng = _engine(tmp_path)
    calls = _stub_refresh(eng, monkeypatch, [(473, 40), (511, 2)])
    ok, skipped = eng.refresh_data_complete()
    assert (ok, skipped) == (511, 2)  # returns the RECOVERED panel
    assert calls["refresh"] == 2  # initial + one retry
    assert calls["sleep"] == 1  # waited once between


def test_persistent_degradation_bounded(tmp_path, monkeypatch):
    """If the panel never recovers, retries are bounded (never hangs) and it proceeds anyway."""
    eng = _engine(tmp_path)
    calls = _stub_refresh(eng, monkeypatch, [(473, 40)])  # always degraded
    ok, skipped = eng.refresh_data_complete()
    assert (ok, skipped) == (473, 40)
    # initial fetch + panel_max_retries re-fetches; sleeps == panel_max_retries
    assert calls["refresh"] == 1 + eng.cfg.panel_max_retries
    assert calls["sleep"] == eng.cfg.panel_max_retries


def test_steady_state_two_skipped_passes(tmp_path, monkeypatch):
    """The normal 2/513 delisted floor is under the 5% threshold — must NOT trigger a retry."""
    eng = _engine(tmp_path)
    calls = _stub_refresh(eng, monkeypatch, [(511, 2)])
    eng.refresh_data_complete()
    assert calls["refresh"] == 1 and calls["sleep"] == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
