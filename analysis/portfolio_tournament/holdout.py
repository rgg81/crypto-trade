"""Stage-2 sealed-holdout evaluator — orchestrator-only, doubly gated, journaled.

GATE: refuses to run unless BOTH ``confirm=True`` (the --confirm-holdout flag) AND the
``CRYPTO_TOURNAMENT_ALLOW_HOLDOUT=1`` env var are set. Every invocation appends a
``holdout_run`` line to the tournament journal BEFORE computing — an indelible trace.

DATA: Binance klines are immutable, so no vendor-rebasing splice is needed — the frozen IS
snapshot is CANON and the fresh store simply appends the tail. TWO runs per finalist:

  RUN A (causality check, canonical config only): panel = the frozen IS-union columns,
    frozen IS rows verbatim + fresh tail rows. The IS rows of this run's net series must be
    bit-identical to the team's frozen ``out/net_is.csv`` (strategies are causal, data is
    canon ⇒ free cheat check). Mismatch ⇒ ``ReplayMismatchError`` — an integrity finding.
    The LAST frozen row is excluded: its ``ret_fwd`` and boundary funding were truncated by
    construction in the snapshot.

  RUN B (the score): panel = the FULL holdout universe (every symbol ever in the recomputed
    full-pool weekly top-40 through 2026-06-30) loaded fresh — the honest deployment
    reality: coins list and enter the top-40 that the IS panel never contained. Metrics are
    evaluated on the holdout window only. Sensitivities (no-funding / 2×cost / 2×slip) run
    RUN B only.

MASK REPLAY: the eligibility mask is recomputed full-pool from the fresh store and its IS
rows (sliced to the frozen columns) must equal the frozen ``_universe/eligibility.csv``
bit-for-bit — any drift means the store's IS klines changed and is an integrity stop.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402
from portfolio_tournament import protocol as tp  # noqa: E402
from portfolio_tournament import snapshot as tsnap  # noqa: E402
from portfolio_tournament import universe as tu  # noqa: E402


class HoldoutSealedError(RuntimeError):
    """Holdout evaluation attempted without the double orchestrator gate."""


class ReplayMismatchError(RuntimeError):
    """IS rows of the holdout run diverged from the frozen stage-1 net (causality break)."""


class MaskReplayError(RuntimeError):
    """Recomputed eligibility mask's IS rows diverged from the frozen snapshot mask."""


def _gate(confirm: bool) -> None:
    if not confirm:
        raise HoldoutSealedError("holdout is sealed: pass confirm=True (--confirm-holdout)")
    if os.environ.get(tc.HOLDOUT_ENV_FLAG) != "1":
        raise HoldoutSealedError(f"holdout is sealed: env {tc.HOLDOUT_ENV_FLAG}=1 not set")


_HOLD_HI_MS = int(tc.TRN_HOLD_HI.value // 1_000_000)
_LOAD_HI_MS = _HOLD_HI_MS + tc.STEP_MS  # one extra candle so the last holdout ret_fwd exists


def _read_kline(p: Path, hi_ms: int) -> pd.DataFrame:
    k = pd.read_csv(p)
    k = k.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
    return k[k.index <= hi_ms]


def _read_funding(p: Path, hi_ms: int) -> pd.Series:
    f = pd.read_csv(p).drop_duplicates(subset="funding_time", keep="last")
    s = f.set_index("funding_time")["funding_rate"].astype(float).sort_index()
    return s[s.index <= hi_ms + 60_000]  # jitter margin on the boundary event


def _read_oi(p: Path, hi_ms: int) -> pd.DataFrame:
    o = pd.read_csv(p)
    o = o.drop_duplicates(subset="open_time", keep="last").set_index("open_time").sort_index()
    return o[o.index <= hi_ms]


def recompute_mask(src: Path) -> pd.DataFrame:
    """Fresh full-pool weekly top-40 mask over the whole store (ms-indexed bool)."""
    qv = tu.load_qv_panel(Path(src))
    return tu.weekly_topn_mask(qv)


def check_mask_replay(mask: pd.DataFrame, snapshot_dir: Path = tc.SNAPSHOT_DIR) -> None:
    frozen = pd.read_csv(snapshot_dir / "_universe" / "eligibility.csv", index_col="open_time")
    cols = list(frozen.columns)
    got = mask.loc[mask.index <= tc.IS_END_MS, :].reindex(columns=cols).fillna(False)
    got = got[got.index.isin(frozen.index)]
    if len(got) != len(frozen) or not (got.to_numpy().astype(int) == frozen.to_numpy()).all():
        raise MaskReplayError(
            "recomputed eligibility mask IS rows do not reproduce the frozen snapshot mask "
            "— the store's IS klines drifted (integrity stop)"
        )


def load_replay_bundle(src: Path, snapshot_dir: Path, manifest_path: Path, mask: pd.DataFrame):
    """RUN-A bundle: frozen IS-union columns, frozen IS rows verbatim + fresh tail."""
    tsnap.verify_manifest(snapshot_dir, manifest_path)
    manifest = tsnap.read_manifest(manifest_path)
    symbols = tsnap.manifest_symbols(manifest)
    frozen = te.load_is_bundle(snapshot_dir, manifest_path, verify=False)
    src = Path(src)
    klines, funding, oi = {}, {}, {}
    for sym in symbols:
        fk = frozen["klines"][sym]
        fresh = _read_kline(src / sym / "8h.csv", _LOAD_HI_MS)
        klines[sym] = pd.concat([fk, fresh[fresh.index > tc.IS_END_MS]]).sort_index()
        ff = frozen["funding"].get(sym, pd.Series(dtype=float))
        fp = src / "funding_rates" / f"{sym}.csv"
        if fp.exists():
            tail = _read_funding(fp, _HOLD_HI_MS)
            funding[sym] = pd.concat([ff, tail[tail.index > tc.IS_END_MS]]).sort_index()
        elif len(ff):
            funding[sym] = ff
        fo = frozen["oi"].get(sym)
        op = src / "open_interest" / sym / "8h.csv"
        if op.exists():
            tail_o = _read_oi(op, _HOLD_HI_MS)
            oi[sym] = (
                pd.concat([fo, tail_o[tail_o.index > tc.IS_END_MS]]).sort_index()
                if fo is not None
                else tail_o
            )
        elif fo is not None:
            oi[sym] = fo
    elig = mask.reindex(columns=symbols).fillna(False)
    return {"klines": klines, "funding": funding, "oi": oi, "elig": elig}


def load_score_bundle(src: Path, mask: pd.DataFrame):
    """RUN-B bundle: the full holdout universe, loaded fresh (the deployment reality)."""
    src = Path(src)
    in_window = mask[mask.index < _HOLD_HI_MS]
    symbols = sorted(c for c in mask.columns if in_window[c].any())
    klines, funding, oi = {}, {}, {}
    for sym in symbols:
        p = src / sym / "8h.csv"
        if not p.exists():
            continue
        klines[sym] = _read_kline(p, _LOAD_HI_MS)
        fp = src / "funding_rates" / f"{sym}.csv"
        if fp.exists():
            funding[sym] = _read_funding(fp, _HOLD_HI_MS)
        op = src / "open_interest" / sym / "8h.csv"
        if op.exists():
            oi[sym] = _read_oi(op, _HOLD_HI_MS)
    elig = mask.reindex(columns=sorted(klines)).fillna(False)
    return {"klines": klines, "funding": funding, "oi": oi, "elig": elig}


def _check_is_replay(team_dir: Path, net: pd.Series) -> bool:
    """Bit-compare the RUN-A net's IS rows against the frozen stage-1 net (last row excluded)."""
    csv = Path(team_dir) / "out" / "net_is.csv"
    if not csv.exists():
        raise ReplayMismatchError(f"{Path(team_dir).name}: out/net_is.csv missing")
    frozen = pd.read_csv(csv, index_col="date", parse_dates=["date"], float_precision="round_trip")[
        "net"
    ].iloc[:-1]
    frozen.index = frozen.index.astype(net.index.dtype)
    got = net.reindex(frozen.index)
    return bool(got.notna().all() and (got.to_numpy() == frozen.to_numpy()).all())


def _run_on_bundle(team_dir: Path, bundle: dict, **net_kwargs):
    pn, aux, scoring = te.build_panels(bundle)
    mod = tp.load_strategy(team_dir)
    raw = te.conform_raw(mod.build_raw_weights(te.team_view(pn), te.make_team_aux(aux)), pn)
    tp.purge_team_modules()
    return te.net_series(raw, pn, scoring, **net_kwargs)


def evaluate_holdout(
    team_id: str,
    *,
    confirm: bool = False,
    apply_funding: bool = True,
    cost_mult: float = 1.0,
    slip_mult: float = 1.0,
    label: str = "canonical",
    teams_dir: Path = tc.TEAMS_DIR,
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    src_data_dir: Path = tc.MAIN_DATA_DIR,
    results_dir: Path | None = None,
    journal_path: Path = tc.JOURNAL_PATH,
    _mask_cache: dict | None = None,
) -> tuple[dict, pd.Series]:
    """Run one frozen submission over the sealed holdout window; returns (result, run-B net)."""
    _gate(confirm)
    tc.journal(
        "holdout_run",
        journal_path,
        team_id=team_id,
        label=label,
        apply_funding=apply_funding,
        cost_mult=cost_mult,
        slip_mult=slip_mult,
    )
    td = tc.team_dir(team_id, teams_dir)
    tp.check_submission_shas(td)

    if _mask_cache is not None and "mask" in _mask_cache:
        mask = _mask_cache["mask"]
    else:
        mask = recompute_mask(src_data_dir)
        check_mask_replay(mask, snapshot_dir)
        if _mask_cache is not None:
            _mask_cache["mask"] = mask

    is_replay = None
    if label == "canonical":
        # AMENDMENT #2 (charter §13, journaled 2026-07-18): the causality bit-compare scores
        # the REPLAY RUN'S WEIGHTS through the IS-LENGTH scoring path. Scoring the extended
        # panel directly diverges from the frozen net by 1 ULP on most rows — numpy's
        # reduction blocking changes with frame length — which false-failed all four
        # finalists while their raw weights were bit-identical. Team causality is exactly
        # "weights on IS rows unchanged when data extends"; organizer-side summation order
        # carries no integrity information, so both sides of the compare now score
        # identical-length frames over the frozen snapshot's own panels.
        bundle_a = load_replay_bundle(src_data_dir, snapshot_dir, manifest_path, mask)
        pn_a, aux_a, _sc_a = te.build_panels(bundle_a)
        mod = tp.load_strategy(td)
        raw_a = te.conform_raw(
            mod.build_raw_weights(te.team_view(pn_a), te.make_team_aux(aux_a)), pn_a
        )
        tp.purge_team_modules()
        pn_is, _aux_is, sc_is = te.load_is_panels(snapshot_dir, manifest_path, verify=False)
        raw_a_is = raw_a.reindex(index=pn_is["open"].index, columns=pn_is["open"].columns)
        net_a, _w_a, _parts_a = te.net_series(raw_a_is, pn_is, sc_is)
        is_replay = _check_is_replay(td, net_a)
        if not is_replay:
            raise ReplayMismatchError(
                f"{team_id}: IS-row weights of the holdout run do not reproduce the frozen "
                "stage-1 net — causality break or tampered artifacts (integrity finding)"
            )

    bundle_b = load_score_bundle(src_data_dir, mask)
    net, w, parts = _run_on_bundle(
        td, bundle_b, apply_funding=apply_funding, cost_mult=cost_mult, slip_mult=slip_mult
    )
    m = te.evaluate(net, w, parts, lo=tc.TRN_HOLD_START, hi=tc.TRN_HOLD_HI)
    result = {
        "schema": 1,
        "team_id": team_id,
        "label": label,
        "config": {
            "apply_funding": apply_funding,
            "cost_mult": cost_mult,
            "slip_mult": slip_mult,
        },
        "window": {
            "lo": str(tc.TRN_HOLD_START.date()),
            "hi_exclusive": str(tc.TRN_HOLD_HI.date()),
        },
        "n_universe_symbols": len(bundle_b["klines"]),
        "metrics": m.to_dict(),
        "is_replay_identical": is_replay,
    }
    if results_dir is not None:
        results_dir = Path(results_dir)
        results_dir.mkdir(parents=True, exist_ok=True)
        suffix = "" if label == "canonical" else f"_{label}"
        (results_dir / f"holdout_{team_id}{suffix}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
    tc.journal(
        "holdout_result",
        journal_path,
        team_id=team_id,
        label=label,
        sharpe=result["metrics"]["sharpe"],
        maxdd=result["metrics"]["maxdd"],
        is_replay_identical=is_replay,
    )
    return result, net
