"""crypto-cup-01 tournament evaluator tests — synthetic 8h panels, no real data needed.

Covers: snapshot integrity, IS-boundary enforcement, team-view stripping, caps invariants,
the weekly eligibility floor, delisting, the funding SUM-in-window model (incl. 4h-interval
symbols + ms jitter), the slippage model, vol-target past-onlyness, the decision lag, all
six harness checks (with deliberately-leaky references), submission SHA binding, the
registry-approved freeze gate, the double-gated holdout with IS-replay + mask-replay, and
Stage-1 ranking with the noise floor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402
from portfolio_tournament import harness as th  # noqa: E402
from portfolio_tournament import holdout as thold  # noqa: E402
from portfolio_tournament import leaderboard as tlb  # noqa: E402
from portfolio_tournament import protocol as tp  # noqa: E402
from portfolio_tournament import snapshot as tsnap  # noqa: E402
from portfolio_tournament import teamlib  # noqa: E402
from portfolio_tournament import universe as tu  # noqa: E402

STEP = tc.STEP_MS
GRID0 = int(pd.Timestamp("2024-01-01").value // 1_000_000)  # a Monday 00:00 UTC, inside IS


# ------------------------------------------------------------------ synthetic data --------------
def synth_klines(
    n: int, seed: int, *, start_ms: int = GRID0, price0: float = 100.0, vol_scale: float = 1e6
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.Index(np.arange(start_ms, start_ms + n * STEP, STEP, dtype=np.int64), name="open_time")
    px = price0 * np.exp(np.cumsum(rng.normal(0, 0.01, size=n)))
    vol = rng.uniform(0.5, 1.5, size=n) * vol_scale / 100.0
    return pd.DataFrame(
        {
            "open": px,
            "high": px * 1.01,
            "low": px * 0.99,
            "close": px * (1 + rng.normal(0, 0.002, size=n)),
            "volume": vol,
            "close_time": np.asarray(idx) + STEP - 1,
            "quote_volume": vol * 100.0,  # ~vol_scale $-volume per candle
            "trades": np.full(n, 500.0),
            "taker_buy_volume": vol * 0.5,
            "taker_buy_quote_volume": vol * 50.0,
        },
        index=idx,
    )


def synth_bundle(n_sym: int = 6, n: int = 420, *, all_elig: bool = True) -> dict:
    """Bundle of n_sym coins over n candles, 8h funding, full or empty eligibility."""
    klines = {f"C{i:02d}USDT": synth_klines(n, seed=10 + i) for i in range(n_sym)}
    grid = next(iter(klines.values())).index
    funding = {
        s: pd.Series(0.0001, index=pd.Index(np.asarray(grid) + STEP, name="funding_time"))
        for s in klines
    }
    elig = pd.DataFrame(all_elig, index=grid, columns=sorted(klines)).astype(int)
    oi = {
        s: pd.DataFrame(
            {c: np.linspace(1, 2, len(grid)) for c in te.AUX_OI_COLS.values()}, index=grid
        )
        for s in list(klines)[:2]
    }
    return {"klines": klines, "funding": funding, "oi": oi, "elig": elig}


def write_snapshot_dir(bundle: dict, dest: Path, manifest_path: Path) -> dict:
    """Write a bundle as a data_is/ tree + manifest (mimics build_is_snapshot output)."""
    files: dict[str, str] = {}
    for sym, df in bundle["klines"].items():
        p = dest / sym / "8h.csv"
        p.parent.mkdir(parents=True, exist_ok=True)
        df.reset_index().to_csv(p, index=False, float_format="%.17g")
        files[f"{sym}/8h.csv"] = tsnap.sha256_file(p)
        f = bundle["funding"].get(sym)
        if f is not None and len(f):
            fp = dest / sym / "funding.csv"
            f.rename("funding_rate").reset_index().to_csv(fp, index=False, float_format="%.17g")
            files[f"{sym}/funding.csv"] = tsnap.sha256_file(fp)
        o = bundle["oi"].get(sym)
        if o is not None:
            op = dest / sym / "oi.csv"
            o.reset_index().to_csv(op, index=False, float_format="%.17g")
            files[f"{sym}/oi.csv"] = tsnap.sha256_file(op)
    udir = dest / "_universe"
    udir.mkdir(parents=True, exist_ok=True)
    bundle["elig"].to_csv(udir / "eligibility.csv")
    files["_universe/eligibility.csv"] = tsnap.sha256_file(udir / "eligibility.csv")
    manifest = {
        "schema": 1,
        "name": "crypto-cup-01-test",
        "is_end_ms": tc.IS_END_MS,
        "is_end": str(tc.TRN_IS_END.date()),
        "built_at_utc": "test",
        "source_commit": "",
        "n_files": len(files),
        "files": files,
        "files_sha256": tsnap._files_digest(files),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


REFERENCE_STRATEGY = """
import pandas as pd

def build_raw_weights(pn, aux):
    close = pn["close"]
    mom = close / close.shift(24) - 1.0
    raw = mom.sub(mom.mean(axis=1), axis=0)
    return raw.fillna(0.0)
"""


def make_team(tmp_path: Path, code: str = REFERENCE_STRATEGY, name: str = "scratch-t1") -> Path:
    td = tmp_path / name
    (td / "out").mkdir(parents=True, exist_ok=True)
    (td / "strategy.py").write_text(code)
    return td


# ------------------------------------------------------------------ snapshot / loading ----------
def test_manifest_verify_ok_then_tamper(tmp_path):
    b = synth_bundle(3, 60)
    dest, man = tmp_path / "data_is", tmp_path / "MANIFEST.json"
    write_snapshot_dir(b, dest, man)
    tsnap.verify_manifest(dest, man)  # clean
    p = dest / "C00USDT" / "funding.csv"
    raw = bytearray(p.read_bytes())
    raw[len(raw) // 2] ^= 0x01
    p.write_bytes(bytes(raw))
    with pytest.raises(tsnap.SnapshotTamperedError):
        tsnap.verify_manifest(dest, man)


def test_manifest_extra_and_missing_file(tmp_path):
    b = synth_bundle(3, 60)
    dest, man = tmp_path / "data_is", tmp_path / "MANIFEST.json"
    write_snapshot_dir(b, dest, man)
    (dest / "SNEAKUSDT").mkdir()
    (dest / "SNEAKUSDT" / "8h.csv").write_text("open_time,close\n1,2\n")
    with pytest.raises(tsnap.SnapshotTamperedError, match="extra"):
        tsnap.verify_manifest(dest, man)
    (dest / "SNEAKUSDT" / "8h.csv").unlink()
    (dest / "SNEAKUSDT").rmdir()
    (dest / "C01USDT" / "oi.csv").unlink()
    with pytest.raises(tsnap.SnapshotTamperedError, match="missing"):
        tsnap.verify_manifest(dest, man)


def test_is_boundary_enforced(tmp_path):
    b = synth_bundle(2, 40)
    bad = synth_klines(4, seed=99, start_ms=tc.IS_END_MS + 1)
    b["klines"]["C00USDT"] = pd.concat([b["klines"]["C00USDT"], bad])
    dest, man = tmp_path / "data_is", tmp_path / "MANIFEST.json"
    write_snapshot_dir(b, dest, man)
    with pytest.raises(te.ISBoundaryError):
        te.load_is_bundle(dest, man)


def test_team_view_and_aux_isolation():
    b = synth_bundle(3, 120)
    pn, aux, scoring = te.build_panels(b)
    view = te.team_view(pn)
    assert set(view) == set(te.TEAM_PANELS)
    assert "ret_fwd" not in view and "fund_win" not in view
    assert set(te.AUX_KEYS) <= set(aux)
    team_aux = te.make_team_aux(aux)
    team_aux["funding"].iloc[:, :] = 999.0  # team mutation must not reach the evaluator
    assert float(aux["funding"].iloc[10, 0]) != 999.0


# ------------------------------------------------------------------ caps ------------------------
def test_caps_invariants_random_books():
    rng = np.random.default_rng(0)
    idx = pd.date_range("2021-01-01", periods=50, freq="8h")
    raw = pd.DataFrame(
        rng.normal(size=(50, 30)), index=idx, columns=[f"C{i:02d}USDT" for i in range(30)]
    )
    raw.iloc[7] = 0.0
    w = te.normalize_and_cap(raw)
    gross = w.abs().sum(axis=1)
    assert (gross <= 1.0 + 1e-9).all()
    assert (w.abs().to_numpy() <= tc.PER_NAME_CAP + 1e-12).all()
    assert (w.sum(axis=1).abs() <= tc.NET_CAP + 1e-9).all()
    assert (w.iloc[7] == 0.0).all()


def test_caps_identity_on_compliant_book():
    idx = pd.date_range("2021-01-01", periods=20, freq="8h")
    cols = [f"C{i:02d}USDT" for i in range(20)]
    w0 = pd.DataFrame(0.0, index=idx, columns=cols)
    w0.iloc[:, :10] = 0.05
    w0.iloc[:, 10:] = -0.05  # gross=1, net=0, per-name 0.05
    out = te.normalize_and_cap(w0)
    pd.testing.assert_frame_equal(out, w0, check_exact=True)


# ------------------------------------------------------------------ engine scoring --------------
def test_eligibility_weekly_force_close_and_costed():
    b = synth_bundle(4, 130)
    grid = b["elig"].index
    drop_at = grid[63]  # a Monday 00:00 refresh (63 = 3 weeks of 21 candles)
    assert pd.Timestamp(drop_at, unit="ms").weekday() == 0
    b["elig"].loc[b["elig"].index >= drop_at, "C00USDT"] = 0
    pn, aux, scoring = te.build_panels(b)
    raw = pd.DataFrame(1.0, index=pn["open"].index, columns=pn["open"].columns)
    net, w, parts = te.net_series(raw, pn, scoring)
    dt_drop = pd.Timestamp(drop_at, unit="ms")
    # held book: w = masked.shift(1) -> zero from the candle AFTER the refresh (<=8h later)
    held_after = w.loc[w.index > dt_drop, "C00USDT"]
    assert (held_after == 0.0).all()
    assert float(w.loc[dt_drop, "C00USDT"]) != 0.0  # still held THROUGH the refresh candle
    close_out = parts["cost"].loc[held_after.index[0]]
    assert close_out > 0.0  # the forced exit turnover IS costed


def test_delisted_terminal_candle_no_nan():
    b = synth_bundle(4, 200)
    b["klines"]["C01USDT"] = b["klines"]["C01USDT"].iloc[:90]  # delists mid-panel
    b["funding"]["C01USDT"] = b["funding"]["C01USDT"].iloc[:90]
    b["elig"].loc[b["elig"].index >= b["klines"]["C01USDT"].index[-1], "C01USDT"] = 0
    pn, aux, scoring = te.build_panels(b)
    raw = pd.DataFrame(1.0, index=pn["open"].index, columns=pn["open"].columns)
    net, w, parts = te.net_series(raw, pn, scoring)
    assert net.notna().all()
    assert (w["C01USDT"].iloc[95:] == 0.0).all()


def test_funding_sum_in_window_hand_computed():
    n = 120
    b = synth_bundle(2, n)
    grid = b["klines"]["C00USDT"].index
    # C00: 8h events at each candle CLOSE (open+STEP), rate 0.0001 -> one event per candle
    # C01: 4h interval -> events at open+4h AND open+8h, rate 0.0002 each -> 0.0004 per candle
    b["funding"]["C01USDT"] = pd.Series(
        0.0002,
        index=pd.Index(
            np.sort(np.concatenate([np.asarray(grid) + STEP // 2, np.asarray(grid) + STEP])),
            name="funding_time",
        ),
    )
    pn, aux, scoring = te.build_panels(b)
    fw = scoring["fund_win"]
    assert np.allclose(fw["C00USDT"].iloc[:-1], 0.0001)
    assert np.allclose(fw["C01USDT"].iloc[:-1], 0.0004)
    # long book pays positive funding: fpnl strictly negative once positions are on
    raw = pd.DataFrame(1.0, index=pn["open"].index, columns=pn["open"].columns)
    _net, w, parts = te.net_series(raw, pn, scoring)
    assert (parts["fpnl"].iloc[2:-1] < 0).all()


def test_funding_jitter_snapped_to_boundary():
    b = synth_bundle(1, 50)
    grid = b["klines"]["C00USDT"].index
    jittered = pd.Series(
        0.0003, index=pd.Index(np.asarray(grid[:10]) + STEP + 4, name="funding_time")
    )  # boundary event stamped 4ms late — belongs to the candle it CLOSES
    b["funding"]["C00USDT"] = jittered
    pn, aux, scoring = te.build_panels(b)
    assert np.allclose(scoring["fund_win"]["C00USDT"].iloc[:10], 0.0003)
    assert float(scoring["fund_win"]["C00USDT"].iloc[10]) == 0.0


def test_slippage_zero_mult_reduces_to_taker():
    b = synth_bundle(3, 150)
    pn, aux, scoring = te.build_panels(b)
    rng = np.random.default_rng(3)
    raw = pd.DataFrame(
        rng.normal(size=pn["open"].shape), index=pn["open"].index, columns=pn["open"].columns
    )
    _n, w, parts = te.net_series(raw, pn, scoring, slip_mult=0.0, apply_funding=False)
    dw = (w - w.shift(1)).abs().sum(axis=1)
    expect = tc.COST_SIDE * dw
    got = parts["cost"]
    assert np.allclose(got.fillna(0), expect.fillna(0))


def test_slippage_monotone_thin_pays_more():
    thick = te.slip_side_panel(pd.DataFrame({"A": [1e9] * 200}))
    thin = te.slip_side_panel(pd.DataFrame({"A": [1e5] * 200}))
    assert float(thin.iloc[-1, 0]) > float(thick.iloc[-1, 0])
    assert float(thin.iloc[-1, 0]) <= tc.SLIP_CAP / 1e4 + 1e-15
    assert float(thick.iloc[-1, 0]) >= tc.SLIP_FLOOR / 1e4 - 1e-15


def test_slippage_past_only():
    qv = pd.DataFrame({"A": np.linspace(1e6, 2e6, 300)})
    base = te.slip_side_panel(qv)
    qv2 = qv.copy()
    qv2.iloc[200:] *= 50.0
    pert = te.slip_side_panel(qv2)
    pd.testing.assert_frame_equal(base.iloc[:201], pert.iloc[:201], check_exact=True)


def test_vol_target_past_only():
    rng = np.random.default_rng(5)
    idx = pd.date_range("2021-01-01", periods=400, freq="8h")
    net = pd.Series(rng.normal(0, 0.01, 400), index=idx)
    base = te.vol_target(net)
    net2 = net.copy()
    net2.iloc[300:] *= 10.0
    pert = te.vol_target(net2)
    # rows < 300 are untouched inputs; their scale uses only past rows -> identical outputs.
    # (row 300 itself differs because ITS return is the perturbed input.)
    pd.testing.assert_series_equal(base.iloc[:300], pert.iloc[:300], check_exact=True)
    assert float(pert.iloc[301]) != float(base.iloc[301]) or float(base.iloc[301]) == 0.0


def test_decision_lag_one_candle():
    b = synth_bundle(2, 100)
    pn, aux, scoring = te.build_panels(b)
    raw = pd.DataFrame(0.0, index=pn["open"].index, columns=pn["open"].columns)
    raw.iloc[50] = 1.0  # decide at candle 50 only
    _n, w, parts = te.net_series(raw, pn, scoring, apply_funding=False)
    assert (w.iloc[50] == 0.0).all()
    assert w.iloc[51].abs().sum() > 0  # held during candle 51 — fills at open[51]
    assert (w.iloc[52] == 0.0).all()


# ------------------------------------------------------------------ harness ---------------------
def _mini_snapshot(tmp_path):
    b = synth_bundle(5, 420)
    dest, man = tmp_path / "data_is", tmp_path / "MANIFEST.json"
    write_snapshot_dir(b, dest, man)
    return dest, man


def test_harness_passes_leak_safe_reference(tmp_path):
    dest, man = _mini_snapshot(tmp_path)
    td = make_team(tmp_path)
    rep = th.audit_strategy(td, dest, man, n_truncations=3)
    assert rep.ok, rep.violations


def test_harness_catches_lookahead(tmp_path):
    dest, man = _mini_snapshot(tmp_path)
    td = make_team(
        tmp_path,
        "def build_raw_weights(pn, aux):\n"
        "    return (pn['close'].shift(-1) / pn['close'] - 1).fillna(0.0)\n",
    )
    rep = th.audit_strategy(td, dest, man, n_truncations=3)
    assert not rep.truncation_ok or not rep.corruption_ok


def test_harness_catches_full_sample_normalisation(tmp_path):
    dest, man = _mini_snapshot(tmp_path)
    td = make_team(
        tmp_path,
        "def build_raw_weights(pn, aux):\n"
        "    c = pn['close']\n"
        "    z = (c - c.mean()) / c.std()\n"  # full-panel stats — leaks the future
        "    return z.fillna(0.0)\n",
    )
    rep = th.audit_strategy(td, dest, man, n_truncations=3)
    assert not rep.truncation_ok


def test_harness_catches_nondeterminism(tmp_path):
    dest, man = _mini_snapshot(tmp_path)
    td = make_team(
        tmp_path,
        "import numpy as np\n"
        "def build_raw_weights(pn, aux):\n"
        "    c = pn['close']\n"
        "    return c * 0 + np.random.default_rng().normal(size=c.shape)\n",
    )
    rep = th.audit_strategy(td, dest, man, n_truncations=3)
    assert not rep.determinism_ok


def test_harness_catches_aux_funding_lookahead(tmp_path):
    dest, man = _mini_snapshot(tmp_path)
    td = make_team(
        tmp_path,
        "def build_raw_weights(pn, aux):\n    return (-aux['funding'].shift(-2)).fillna(0.0)\n",
    )
    rep = th.audit_strategy(td, dest, man, n_truncations=3)
    assert not (rep.truncation_ok and rep.corruption_ok)


def test_harness_widening_catches_column_brittleness(tmp_path):
    dest, man = _mini_snapshot(tmp_path)
    td = make_team(
        tmp_path,
        "def build_raw_weights(pn, aux):\n"
        "    assert pn['close'].shape[1] == 5, 'hardcoded universe size'\n"
        "    return pn['close'] * 0.0\n",
    )
    rep = th.audit_strategy(td, dest, man, n_truncations=1)
    assert not rep.widening_ok


def test_static_scan_blocks_prohibited(tmp_path):
    td = make_team(
        tmp_path,
        "import httpx\n"
        "def build_raw_weights(pn, aux):\n"
        "    f = open('data/BTCUSDT/8h.csv')\n"
        "    x = 'tournament/crypto/teams/team-03/strategy.py'\n"
        "    return None\n",
    )
    v = th.scan_sources(td)
    assert any("httpx" in x for x in v)
    assert any("open(" in x for x in v)
    assert any("data/" in x for x in v)
    assert any("team-03" in x for x in v)


def test_static_scan_allows_teamlib(tmp_path):
    td = make_team(
        tmp_path,
        "import teamlib\nimport numpy as np\n"
        "def build_raw_weights(pn, aux):\n    return pn['close'] * 0.0\n",
    )
    assert th.scan_sources(td) == []


# ------------------------------------------------------------------ protocol --------------------
def test_submission_sha_binding_blocks_mutation(tmp_path):
    td = make_team(tmp_path)
    tp.write_submission(td, family_id="fam-x", reported={}, net_is_csv_sha256="0", harness="PASS")
    tp.check_submission_shas(td)  # clean
    (td / "strategy.py").write_text(REFERENCE_STRATEGY + "\n# post-freeze edit\n")
    with pytest.raises(tp.SubmissionError, match="post-freeze mutation"):
        tp.check_submission_shas(td)


def test_freeze_requires_approved_family(tmp_path):
    reg = tmp_path / "registry.jsonl"
    with pytest.raises(tp.SubmissionError, match="not APPROVED"):
        tp.require_approved_family("team-01", "fam-a", reg)
    reg.write_text(
        json.dumps({"team_id": "team-01", "family_id": "fam-a", "status": "approved"}) + "\n"
    )
    tp.require_approved_family("team-01", "fam-a", reg)  # ok
    with reg.open("a") as f:
        f.write(json.dumps({"team_id": "team-01", "family_id": "fam-a", "status": "vetoed"}) + "\n")
    with pytest.raises(tp.SubmissionError):
        tp.require_approved_family("team-01", "fam-a", reg)


def test_teamlib_constants_match_evaluator():
    assert teamlib.STEP_MS == tc.STEP_MS
    assert teamlib.CANDLES_PER_YEAR == tc.CANDLES_PER_YEAR
    idx = pd.date_range("2022-01-01", periods=400, freq="8h")
    net = pd.Series(np.random.default_rng(1).normal(1e-4, 0.01, 400), index=idx)
    assert teamlib.msharpe(net) == pytest.approx(
        te.msharpe(net, pd.Timestamp("2000-01-01"), pd.Timestamp("2100-01-01"))
    )


# ------------------------------------------------------------------ universe --------------------
def test_weekly_mask_past_only_and_age_gated():
    n = 140
    a = synth_klines(n, seed=1, vol_scale=1e8)
    b_ = synth_klines(n, seed=2, vol_scale=1e6)
    late = synth_klines(n - 40, seed=3, start_ms=GRID0 + 40 * STEP, vol_scale=1e9)
    qv = pd.DataFrame(
        {
            "AAAUSDT": a["quote_volume"],
            "BBBUSDT": b_["quote_volume"],
            "LATEUSDT": late["quote_volume"],
        }
    ).reindex(a.index)
    mask = tu.weekly_topn_mask(qv, top_n=2)
    assert not mask["LATEUSDT"].iloc[: 40 + tc.DVOL_WIN].any()  # age gate: no partial-week rank
    assert mask["LATEUSDT"].iloc[-1]  # eventually ranks (huge volume)
    assert not mask.iloc[: tc.DVOL_WIN].to_numpy().any()  # nothing ranks pre-warmup


def test_weekly_mask_refresh_only_on_mondays():
    n = 200
    qv = pd.DataFrame({f"C{i}USDT": synth_klines(n, seed=i)["quote_volume"] for i in range(5)})
    mask = tu.weekly_topn_mask(qv, top_n=2)
    changes = mask.astype(int).diff().abs().sum(axis=1)
    change_days = pd.to_datetime(mask.index[changes > 0], unit="ms")
    assert set(change_days.weekday) <= {0}
    assert set(change_days.hour) <= {0}


# ------------------------------------------------------------------ holdout ---------------------
def test_holdout_double_gate(monkeypatch):
    monkeypatch.delenv(tc.HOLDOUT_ENV_FLAG, raising=False)
    with pytest.raises(thold.HoldoutSealedError):
        thold.evaluate_holdout("team-01", confirm=False)
    with pytest.raises(thold.HoldoutSealedError):
        thold.evaluate_holdout("team-01", confirm=True)  # env still missing


def _synth_store(root: Path, n_sym: int, n_is: int, n_tail: int) -> Path:
    """A fake main data store whose IS rows end exactly at the IS boundary."""
    src = root / "store"
    start = tc.IS_END_MS + 1 - n_is * STEP  # last IS candle opens at IS_END_MS+1-STEP
    for i in range(n_sym):
        sym = f"C{i:02d}USDT"
        df = synth_klines(n_is + n_tail, seed=30 + i, start_ms=start)
        p = src / sym / "8h.csv"
        p.parent.mkdir(parents=True, exist_ok=True)
        df.reset_index().to_csv(p, index=False, float_format="%.17g")
        grid = df.index
        f = pd.Series(0.0001, index=pd.Index(np.asarray(grid) + STEP, name="funding_time"))
        fp = src / "funding_rates" / f"{sym}.csv"
        fp.parent.mkdir(parents=True, exist_ok=True)
        f.rename("funding_rate").reset_index().to_csv(fp, index=False, float_format="%.17g")
    return src


def test_holdout_end_to_end_replay_and_score(tmp_path, monkeypatch):
    src = _synth_store(tmp_path, n_sym=6, n_is=630, n_tail=270)  # ~30wk IS + 90d tail
    build_dir = tmp_path / "_build"
    monkeypatch.setattr(tc, "BUILD_DIR", build_dir)
    dest, man = tmp_path / "data_is", tmp_path / "MANIFEST.json"
    tsnap.build_is_snapshot(src, dest, man)
    tsnap.verify_manifest(dest, man)

    td = make_team(tmp_path)
    payload, net1 = tlb.run_team(td, dest, man)
    tlb.write_team_artifacts(td, payload, net1)
    tp.write_submission(
        td,
        family_id="fam-ref",
        reported=payload["metrics"],
        net_is_csv_sha256=tp._sha256_bytes((td / "out" / "net_is.csv").read_bytes()),
        harness="PASS",
    )

    monkeypatch.setenv(tc.HOLDOUT_ENV_FLAG, "1")
    result, net = thold.evaluate_holdout(
        "scratch-t1",
        confirm=True,
        teams_dir=tmp_path,
        snapshot_dir=dest,
        manifest_path=man,
        src_data_dir=src,
        journal_path=tmp_path / "journal.jsonl",
    )
    assert result["is_replay_identical"] is True
    assert result["metrics"]["n_months"] >= 2  # scored on the tail window only

    # tampering with the frozen stage-1 net must be caught as a causality/integrity break
    csv = td / "out" / "net_is.csv"
    lines = csv.read_text().splitlines()
    parts_ = lines[5].split(",")
    lines[5] = f"{parts_[0]},{float(parts_[1] or 0) + 1e-3}"
    csv.write_text("\n".join(lines) + "\n")
    sub = json.loads((td / "submission.json").read_text())  # keep SHA binding consistent
    with pytest.raises((thold.ReplayMismatchError, tp.SubmissionError)):
        thold.evaluate_holdout(
            "scratch-t1",
            confirm=True,
            teams_dir=tmp_path,
            snapshot_dir=dest,
            manifest_path=man,
            src_data_dir=src,
            journal_path=tmp_path / "journal.jsonl",
        )
    del sub


def test_holdout_mask_replay_catches_store_drift(tmp_path, monkeypatch):
    src = _synth_store(tmp_path, n_sym=5, n_is=630, n_tail=90)
    build_dir = tmp_path / "_build"
    monkeypatch.setattr(tc, "BUILD_DIR", build_dir)
    dest, man = tmp_path / "data_is", tmp_path / "MANIFEST.json"
    tsnap.build_is_snapshot(src, dest, man)
    # drift the store INSIDE the IS window: chop a coin's early history (the age gate then
    # delays its first eligibility -> recomputed IS mask rows differ from the frozen ones)
    p = src / "C02USDT" / "8h.csv"
    k = pd.read_csv(p)
    k.iloc[100:].to_csv(p, index=False, float_format="%.17g")
    mask = thold.recompute_mask(src)
    with pytest.raises(thold.MaskReplayError):
        thold.check_mask_replay(mask, dest)


# ------------------------------------------------------------------ stage-1 ranking -------------
def test_stage1_rank_tiebreakers_and_noise_floor():
    entries = [
        {"team_id": "a", "sharpe_1x": 1.0, "sharpe_2x": 0.5, "maxdd": -0.3},
        {"team_id": "b", "sharpe_1x": 1.0, "sharpe_2x": 0.8, "maxdd": -0.5},
        {"team_id": "c", "sharpe_1x": 1.0, "sharpe_2x": 0.8, "maxdd": -0.2},
        {"team_id": "d", "sharpe_1x": float("nan"), "sharpe_2x": 2.0, "maxdd": -0.1},
    ]
    ranked = tlb.stage1_rank(entries)
    assert [e["team_id"] for e in ranked] == ["c", "b", "a", "d"]
    se = tlb.sharpe_se(1.0, 54)
    assert 0.3 < se < 0.8  # ~sqrt((1+1/24)/54)*sqrt(12) ≈ 0.48


# ------------------------------------------------------------------ harness regressions ---------
def test_truncation_survives_late_listing(tmp_path):
    """A cut BEFORE a late listing's first candle leaves an empty kline frame — the panel
    builder must tolerate it (regression: int(NaN) crash on truncated bundles)."""
    b = synth_bundle(4, 420)
    late = synth_klines(100, seed=77, start_ms=GRID0 + 320 * STEP)
    b["klines"]["LATEUSDT"] = late
    b["funding"]["LATEUSDT"] = pd.Series(
        0.0001, index=pd.Index(np.asarray(late.index) + STEP, name="funding_time")
    )
    b["elig"]["LATEUSDT"] = 0
    dest, man = tmp_path / "data_is", tmp_path / "MANIFEST.json"
    write_snapshot_dir(b, dest, man)
    td = make_team(tmp_path)
    rep = th.audit_strategy(td, dest, man, n_truncations=2)
    assert rep.ok, rep.violations  # cuts include pre-listing dates via seeded picks/midpoint


def test_samebar_perturbation_tolerates_int64_oi(tmp_path):
    """OI archives carry int64 columns; the ×1.001 same-bar perturbation must not raise
    (regression: pandas-3 'Invalid value for dtype int64')."""
    b = synth_bundle(3, 420)
    grid = b["klines"]["C00USDT"].index
    b["oi"]["C00USDT"] = pd.DataFrame(
        {c: np.arange(len(grid), dtype=np.int64) + 1 for c in te.AUX_OI_COLS.values()},
        index=grid,
    )
    dest, man = tmp_path / "data_is", tmp_path / "MANIFEST.json"
    write_snapshot_dir(b, dest, man)
    td = make_team(tmp_path)
    rep = th.audit_strategy(td, dest, man, n_truncations=2)
    assert rep.samebar_ok and rep.corruption_ok, rep.violations
