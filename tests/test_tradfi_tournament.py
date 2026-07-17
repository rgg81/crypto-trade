"""tradfi-cup-01 tournament machinery — synthetic-data tests (no real data needed).

Covers: IS snapshot truncation + tamper detection + loader boundary enforcement (T1-T3),
the team view contract (T4), organizer-owned caps (T5), bit-identity to the proven
``core_tradfi.net_from_raw`` when caps are slack (T6), the leak harness (T7-T11, T17),
submission freeze / reproduction (T15), the holdout gate + funding + window slicing
(T12-T14), and stage-1 ranking (T16).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_TRADFI = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "tradfi"
if str(_TRADFI) not in sys.path:
    sys.path.insert(0, str(_TRADFI))

import core_tradfi as ct  # noqa: E402
from tournament import constants as tc  # noqa: E402
from tournament import engine as te  # noqa: E402
from tournament import harness as th  # noqa: E402
from tournament import holdout as thold  # noqa: E402
from tournament import leaderboard as tlb  # noqa: E402
from tournament import protocol as tp  # noqa: E402
from tournament import snapshot as ts  # noqa: E402

SYMS = ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT", "EEEUSDT", "FFFUSDT"]


# ------------------------------------------------------------------ synthetic data --------------
def _ms(index: pd.DatetimeIndex) -> np.ndarray:
    # resolution-robust true-epoch ms (bdate_range may be ns OR us depending on pandas version)
    return index.astype("datetime64[ms]").astype("int64")


def _write_sym(root: Path, sym: str, start: str, end: str, seed: int) -> None:
    dates = pd.bdate_range(start, end)
    rng = np.random.default_rng(seed)
    level = 100.0 * np.cumprod(1 + rng.normal(0.0002, 0.015, len(dates)))
    df = pd.DataFrame(
        {
            "open_time": _ms(dates),
            "open": level * (1 + rng.normal(0, 0.002, len(dates))),
            "high": level * 1.01,
            "low": level * 0.99,
            "close": level,
            "volume": rng.integers(1_000, 90_000, len(dates)).astype("int64"),
        }
    )
    p = root / sym / "1d.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def make_full_data(root: Path, *, end: str = "2026-06-30") -> Path:
    """Full synthetic store: 6 names + VIX, 2019 -> end (spans the IS boundary)."""
    src = root / "data_full"
    for i, sym in enumerate(SYMS):
        _write_sym(src, sym, "2019-01-02", end, seed=100 + i)
    _write_sym(src, tc.VIX_SYM, "2019-01-02", end, seed=999)
    return src


@pytest.fixture()
def snap(tmp_path):
    """(snapshot_dir, manifest_path, src_dir) with a built + verified IS snapshot."""
    src = make_full_data(tmp_path)
    dest = tmp_path / "data_is"
    manifest = tmp_path / "MANIFEST.sha256.json"
    ts.build_is_snapshot(src, dest, manifest, symbols=SYMS + [tc.VIX_SYM])
    return dest, manifest, src


def _load(snap):
    dest, manifest, _src = snap
    return te.load_is_panels(dest, manifest)


# ------------------------------------------------------------------ T1-T3 snapshot --------------
def test_snapshot_truncation_no_rows_past_is_end(snap):
    dest, _manifest, _src = snap
    files = sorted(dest.rglob("1d.csv"))
    assert len(files) == len(SYMS) + 1  # 6 names + VIX
    for p in files:
        assert pd.read_csv(p)["open_time"].max() <= tc.IS_END_MS, p


def test_snapshot_manifest_tamper_detection(snap):
    dest, manifest, _src = snap
    ts.verify_manifest(dest, manifest)  # clean passes
    victim = dest / SYMS[0] / "1d.csv"
    victim.write_bytes(victim.read_bytes().replace(b"1", b"2", 1))
    with pytest.raises(ts.SnapshotTamperedError):
        ts.verify_manifest(dest, manifest)


def test_snapshot_extra_file_detected(snap):
    dest, manifest, _src = snap
    (dest / "sneaky.csv").write_text("open_time,close\n1,1\n")
    with pytest.raises(ts.SnapshotTamperedError, match="extra"):
        ts.verify_manifest(dest, manifest)


def test_load_is_panels_hard_fails_on_post_is_rows(snap, tmp_path):
    dest, manifest, _src = snap
    # plant a 2025 bar AND recompute its manifest hash — verify passes, boundary check must trip
    victim = dest / SYMS[1] / "1d.csv"
    df = pd.read_csv(victim)
    row = df.iloc[[-1]].copy()
    row["open_time"] = int(pd.Timestamp("2025-02-03").value // 1_000_000)
    pd.concat([df, row]).to_csv(victim, index=False)
    m = ts.read_manifest(manifest)
    m["files"][f"{SYMS[1]}/1d.csv"] = ts.sha256_file(victim)
    m["files_sha256"] = ts._files_digest(m["files"])
    import json

    manifest.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
    with pytest.raises(te.ISBoundaryError):
        te.load_is_panels(dest, manifest)


# ------------------------------------------------------------------ T4 team view ----------------
def test_team_view_has_no_ret_fwd_and_has_volume(snap):
    pn, aux = _load(snap)
    view = te.team_view(pn)
    assert set(view) == {"open", "high", "low", "close", "volume"}
    assert "ret_fwd" not in view
    assert list(view["volume"].columns) == list(view["open"].columns)
    assert isinstance(view["close"].index, pd.DatetimeIndex)
    assert aux["vix"] is not None and isinstance(aux["vix"].index, pd.DatetimeIndex)
    assert set(aux["sector_map"]) == set(SYMS)
    # views are copies — mutating them cannot poison the scoring panels
    view["close"].iloc[:, :] = -1.0
    assert not (pn["close"] == -1.0).all().all()


# ------------------------------------------------------------------ T5 caps ---------------------
def test_caps_invariants_and_zero_rows():
    idx = pd.bdate_range("2020-01-01", periods=40)
    rng = np.random.default_rng(7)
    raw = pd.DataFrame(rng.normal(0, 1, (40, 8)), index=idx, columns=list("ABCDEFGH"))
    raw.iloc[3] = 0.0  # all-zero row
    raw.iloc[5, 2] = np.inf
    raw.iloc[6, 3] = np.nan
    raw.iloc[10] = [1, 1, 1, 1, 1, 1, 1, 1]  # pure directional book
    w = te.normalize_and_cap(raw)
    eps = 1e-12
    assert (w.abs() <= tc.PER_NAME_CAP + eps).all().all()
    assert (w.sum(axis=1).abs() <= tc.NET_CAP + eps).all()
    assert (w.abs().sum(axis=1) <= 1.0 + eps).all()
    assert (w.iloc[3] == 0.0).all()
    assert np.isfinite(w.to_numpy()).all()
    # pure-long row collapses to the net cap (docstring behavior)
    assert w.iloc[10].sum() == pytest.approx(tc.NET_CAP, abs=1e-9)


def test_caps_identity_on_compliant_book():
    idx = pd.bdate_range("2020-01-01", periods=30)
    cols = [f"S{i}" for i in range(14)]
    rng = np.random.default_rng(11)
    mag = rng.uniform(0.9, 1.1, (30, 14))
    signs = np.array([1] * 7 + [-1] * 7)
    raw = pd.DataFrame(mag * signs, index=idx, columns=cols)
    w = te.normalize_and_cap(raw)
    # book is compliant after one gross-normalisation -> output IS that normalisation, bit-exact
    gross = raw.abs().sum(axis=1)
    expected = raw.div(gross, axis=0)
    pd.testing.assert_frame_equal(w, expected, check_exact=True)
    # and idempotent
    pd.testing.assert_frame_equal(te.normalize_and_cap(w), w, check_exact=True)


# ------------------------------------------------------------------ T6 core anchor --------------
def test_engine_reduces_to_core_when_caps_slack(snap):
    pn, _aux = _load(snap)
    idx, cols = pn["open"].index, list(pn["open"].columns)
    # 6 names is too few for slack caps -> widen synthetically by splitting each name in two
    rng = np.random.default_rng(3)
    wide = [f"{c}#{k}" for c in cols for k in range(3)]  # 18 pseudo-names
    mag = rng.uniform(0.9, 1.1, (len(idx), len(wide)))
    signs = np.tile(np.array([1, -1, 1, -1, 1, -1] * 3), (len(idx), 1))
    raw = pd.DataFrame(mag * signs, index=idx, columns=wide)
    ret_fwd = pd.DataFrame(rng.normal(0, 0.01, (len(idx), len(wide))), index=idx, columns=wide)
    net_engine, w_engine = te.net_series(raw, ret_fwd)
    net_core, w_core = ct.net_from_raw(raw, ret_fwd)
    assert (raw.div(raw.abs().sum(axis=1), axis=0).abs() <= tc.PER_NAME_CAP).all().all()
    pd.testing.assert_frame_equal(w_engine, w_core, check_exact=True)
    pd.testing.assert_series_equal(net_engine, net_core, check_exact=True)


# ------------------------------------------------------------------ T7-T11 harness --------------
REFERENCE_STRATEGY = '''\
"""Leak-safe reference: 12-1 cross-sectional momentum, row-wise demeaned."""


def build_raw_weights(pn, aux):
    c = pn["close"]
    mom = c.shift(21) / c.shift(252) - 1.0
    return mom.sub(mom.mean(axis=1), axis=0)
'''

LOOKAHEAD_STRATEGY = """\
def build_raw_weights(pn, aux):
    c = pn["close"]
    fut = c.shift(-1) / c - 1.0  # future return — leak
    return fut.sub(fut.mean(axis=1), axis=0)
"""

FULLSAMPLE_STRATEGY = """\
def build_raw_weights(pn, aux):
    c = pn["close"]
    r = c.pct_change()
    z = (r - r.mean()) / r.std()  # full-sample stats — leak
    return -z
"""

NONDET_STRATEGY = """\
import numpy as np
import pandas as pd


def build_raw_weights(pn, aux):
    rng = np.random.default_rng()  # unseeded
    c = pn["close"]
    return pd.DataFrame(rng.normal(size=c.shape), index=c.index, columns=c.columns)
"""

SCAN_BAD_STRATEGY = """\
import requests


def build_raw_weights(pn, aux):
    x = open("data/AAAUSDT/1d.csv").read()
    y = "data_live_tradfi"
    return None
"""


def _team(tmp_path: Path, source: str, name: str = "team-01") -> Path:
    d = tmp_path / "teams" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "strategy.py").write_text(source)
    return d


def test_harness_passes_leak_safe_reference(snap, tmp_path):
    dest, manifest, _src = snap
    td = _team(tmp_path, REFERENCE_STRATEGY)
    rep = th.audit_strategy(td, dest, manifest, n_truncations=3)
    assert rep.ok, rep.violations
    assert rep.n_truncations >= 3


def test_harness_catches_lookahead_strategy(snap, tmp_path):
    dest, manifest, _src = snap
    td = _team(tmp_path, LOOKAHEAD_STRATEGY)
    rep = th.audit_strategy(td, dest, manifest, n_truncations=3)
    assert not rep.truncation_ok
    assert not rep.corruption_ok
    assert not rep.ok


def test_harness_catches_fullsample_normalization(snap, tmp_path):
    dest, manifest, _src = snap
    td = _team(tmp_path, FULLSAMPLE_STRATEGY)
    rep = th.audit_strategy(td, dest, manifest, n_truncations=3)
    assert not rep.truncation_ok
    assert not rep.ok


def test_harness_catches_nondeterminism(snap, tmp_path):
    dest, manifest, _src = snap
    td = _team(tmp_path, NONDET_STRATEGY)
    rep = th.audit_strategy(td, dest, manifest, n_truncations=3)
    assert not rep.determinism_ok
    assert not rep.ok


def test_import_scan_blocks_network_file_reads_and_paths(tmp_path):
    td = _team(tmp_path, SCAN_BAD_STRATEGY)
    violations = th.scan_sources(td)
    joined = "\n".join(violations)
    assert "banned import 'requests'" in joined
    assert "banned call 'open('" in joined
    assert "data_live_tradfi" in joined
    assert "data/AAAUSDT" in joined
    rep = th.HarnessReport()
    rep.violations = violations
    assert not rep.ok


# ------------------------------------------------------------------ T15 freeze / SHAs -----------
def test_submission_sha_binding_blocks_post_freeze_mutation(tmp_path):
    td = _team(tmp_path, REFERENCE_STRATEGY)
    (td / "helpers.py").write_text("def two():\n    return 2\n")
    tp.write_submission(
        td,
        family_id="t01-xsmom-v1",
        reported={"sharpe_1x": 1.0},
        net_is_csv_sha256="x",
        harness="PASS",
    )
    assert tp.check_submission_shas(td)["team_id"] == "team-01"
    (td / "helpers.py").write_text("def two():\n    return 3\n")
    with pytest.raises(tp.SubmissionError, match="post-freeze mutation"):
        tp.check_submission_shas(td)


# ------------------------------------------------------------------ T17 same-bar via engine -----
def test_samebar_close_perturbation_through_engine(snap, tmp_path):
    dest, manifest, _src = snap
    td = _team(tmp_path, REFERENCE_STRATEGY)
    coins = te.load_is_coins(dest, manifest)
    raw_a, pn_a = th._run_strategy(td, coins)
    idx = pn_a["open"].index
    t_star = idx[int(len(idx) * 0.7)]
    raw_b, pn_b = th._run_strategy(td, th.perturb_close_at(coins, t_star))
    net_a, _ = te.net_series(raw_a, pn_a["ret_fwd"])
    net_b, _ = te.net_series(raw_b, pn_b["ret_fwd"])
    pd.testing.assert_series_equal(
        net_a[net_a.index <= t_star], net_b[net_b.index <= t_star], check_exact=True
    )


# ------------------------------------------------------------------ T12-T14 holdout -------------
def _frozen_team(snap, tmp_path) -> Path:
    """Reference team with team-run artifacts + a written submission (freeze without audit)."""
    dest, manifest, _src = snap
    td = _team(tmp_path, REFERENCE_STRATEGY)
    payload, net1 = tlb.run_team(td, dest, manifest)
    tlb.write_team_artifacts(td, payload, net1)
    tp.write_submission(
        td,
        family_id="t01-xsmom-v1",
        reported=payload["metrics"],
        net_is_csv_sha256=tp._sha256_bytes((td / "out" / "net_is.csv").read_bytes()),
        harness="PASS",
    )
    return td


def _holdout_kwargs(snap, tmp_path, data_dir=None):
    dest, manifest, src = snap
    return dict(
        teams_dir=tmp_path / "teams",
        snapshot_dir=dest,
        manifest_path=manifest,
        data_dir=data_dir if data_dir is not None else src,
        live_data_dir=tmp_path / "no_live_store",
        funding_dir=tmp_path / "no_funding",
        results_dir=tmp_path / "results",
        journal_path=tmp_path / "journal.jsonl",
    )


def test_holdout_gate_requires_flag_and_env(snap, tmp_path, monkeypatch):
    _frozen_team(snap, tmp_path)
    monkeypatch.delenv(tc.HOLDOUT_ENV_FLAG, raising=False)
    with pytest.raises(thold.HoldoutSealedError):
        thold.evaluate_holdout("team-01", confirm=False, **_holdout_kwargs(snap, tmp_path))
    with pytest.raises(thold.HoldoutSealedError):
        thold.evaluate_holdout("team-01", confirm=True, **_holdout_kwargs(snap, tmp_path))
    assert not (tmp_path / "journal.jsonl").exists()  # sealed attempts leave no partial state
    monkeypatch.setenv(tc.HOLDOUT_ENV_FLAG, "1")
    result, net = thold.evaluate_holdout("team-01", confirm=True, **_holdout_kwargs(snap, tmp_path))
    assert result["is_replay_identical"] is True
    assert (tmp_path / "results" / "holdout_team-01.json").exists()
    assert (tmp_path / "journal.jsonl").read_text().count("holdout_") >= 2


def test_holdout_window_slice_exact_24_months(snap, tmp_path, monkeypatch):
    _frozen_team(snap, tmp_path)
    monkeypatch.setenv(tc.HOLDOUT_ENV_FLAG, "1")
    result, net = thold.evaluate_holdout("team-01", confirm=True, **_holdout_kwargs(snap, tmp_path))
    # synthetic store runs 2019 -> 2026-06-30: the scored slice must be exactly 24 months
    assert result["metrics"]["n_months"] == 24
    assert result["window"] == {"lo": "2024-07-01", "hi_exclusive": "2026-07-01"}
    # net spans IS too (needed for the replay check) but metrics ignore everything < 2024-07
    assert net.index.min() < tc.TRN_HOLD_START


def test_holdout_immune_to_vendor_readjustment(snap, tmp_path, monkeypatch):
    """A retroactive total-return re-base of the fresh store must not move stage-2 results:
    the frozen IS snapshot is canon and fresh tails are return-chained onto it."""
    dest, manifest, src = snap
    _frozen_team(snap, tmp_path)
    monkeypatch.setenv(tc.HOLDOUT_ENV_FLAG, "1")
    r_base, _ = thold.evaluate_holdout("team-01", confirm=True, **_holdout_kwargs(snap, tmp_path))

    src2 = tmp_path / "data_readjusted"
    for p in Path(src).rglob("1d.csv"):
        df = pd.read_csv(p)
        for col in ("open", "high", "low", "close"):
            df[col] = df[col] * 0.93  # vendor re-based the whole adjusted series
        out = src2 / p.relative_to(src)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
    r_adj, _ = thold.evaluate_holdout(
        "team-01", confirm=True, **_holdout_kwargs(snap, tmp_path, data_dir=src2)
    )
    assert r_adj["is_replay_identical"] is True
    assert r_adj["metrics"]["sharpe"] == pytest.approx(r_base["metrics"]["sharpe"], abs=1e-9)
    assert r_adj["metrics"]["total_return"] == pytest.approx(
        r_base["metrics"]["total_return"], abs=1e-9
    )


def test_funding_sign_and_application_exact():
    idx = pd.bdate_range("2026-01-05", periods=90)
    cols = list("ABCD")
    raw = pd.DataFrame(0.0, index=idx, columns=cols)
    raw["A"], raw["B"] = 1.0, -1.0
    ret_fwd = pd.DataFrame(0.0, index=idx, columns=cols)
    f = pd.DataFrame(0.0, index=idx, columns=cols)
    f["A"] = 0.001  # positive funding on the LONG leg -> longs pay

    net_f, w = te.net_series(raw, ret_fwd, cost_mult=0.0, funding=f)
    expected_raw = (-(w * f).sum(axis=1)).dropna()
    pd.testing.assert_series_equal(net_f, ct.vol_target(expected_raw), check_exact=True)

    net_none, _ = te.net_series(raw, ret_fwd, cost_mult=0.0, funding=None)
    net_zero, _ = te.net_series(
        raw, ret_fwd, cost_mult=0.0, funding=pd.DataFrame(0.0, index=idx, columns=cols)
    )
    pd.testing.assert_series_equal(net_none, net_zero, check_exact=True)
    assert net_f.sum() < net_none.sum()  # funding on the long leg is a drag


# ------------------------------------------------------------------ T16 ranking -----------------
def test_stage1_ranking_tiebreakers():
    entries = [
        {"team_id": "A", "sharpe_1x": 1.2, "sharpe_2x": 0.8, "maxdd": -0.2},
        {"team_id": "B", "sharpe_1x": 1.2, "sharpe_2x": 0.9, "maxdd": -0.3},
        {"team_id": "C", "sharpe_1x": 1.2, "sharpe_2x": 0.9, "maxdd": -0.1},
        {"team_id": "D", "sharpe_1x": 2.0, "sharpe_2x": 0.1, "maxdd": -0.5},
        {"team_id": "E", "sharpe_1x": float("nan"), "sharpe_2x": 5.0, "maxdd": -0.01},
    ]
    ranked = tlb.stage1_rank(entries)
    assert [e["team_id"] for e in ranked] == ["D", "C", "B", "A", "E"]
    assert [e["rank"] for e in ranked] == [1, 2, 3, 4, 5]
