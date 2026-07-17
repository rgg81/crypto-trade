"""Stage-2 sealed-holdout evaluator — orchestrator-only, doubly gated, journaled.

GATE: refuses to run unless BOTH ``confirm=True`` (the --confirm-holdout flag) AND the
``TRADFI_TOURNAMENT_ALLOW_HOLDOUT=1`` env var are set. Every invocation appends a
``holdout_run`` line to the tournament journal BEFORE computing — an indelible trace.

DATA: the frozen IS snapshot is CANON. Yahoo total-return series re-base retroactively when
new dividends occur, so a fresh fetch's IS rows need not bit-match the snapshot teams
researched on. ``_extend_frozen`` therefore return-chains the fresh series onto the frozen
one at the IS boundary (the proven splice_one math, anchored at the LAST frozen bar):
    extended[t] = frozen[t]                        for t <= D   (bit-identical to snapshot)
    extended[t] = fresh[t] * frozen[D] / fresh[D]  for t >  D   (pure fresh returns)
The fresh series is itself ``load_tradfi_spliced`` output, so the 2026 tail already rides
the Binance perp (the traded instrument). Funding (−w·f on the held book, zero before each
perp's inception) is charged when ``apply_funding`` — "use funding when available".

CAUSALITY CROSS-CHECK: for the canonical run the IS rows of the holdout net series must be
bit-identical to the team's frozen ``out/net_is.csv`` (strategies are causal, data is canon
=> free cheat check). A mismatch raises ``ReplayMismatchError`` — an integrity finding.
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

import core_tradfi as ct  # noqa: E402
import perp_map_tradfi as pm  # noqa: E402
import reconcile_basis_tradfi as rb  # noqa: E402
import splice_loader as sl  # noqa: E402
from tournament import constants as tc  # noqa: E402
from tournament import engine as te  # noqa: E402
from tournament import protocol as tp  # noqa: E402
from tournament import snapshot as tsnap  # noqa: E402

_OHLC = ("open", "high", "low", "close")


class HoldoutSealedError(RuntimeError):
    """Holdout evaluation attempted without the double orchestrator gate."""


class ReplayMismatchError(RuntimeError):
    """IS rows of the holdout run diverged from the frozen stage-1 net (causality break)."""


def _gate(confirm: bool) -> None:
    if not confirm:
        raise HoldoutSealedError("holdout is sealed: pass confirm=True (--confirm-holdout)")
    if os.environ.get(tc.HOLDOUT_ENV_FLAG) != "1":
        raise HoldoutSealedError(f"holdout is sealed: env {tc.HOLDOUT_ENV_FLAG}=1 not set")


def _extend_frozen(frozen: pd.DataFrame, fresh: pd.DataFrame | None) -> pd.DataFrame:
    """Frozen IS bars verbatim; fresh bars AFTER the boundary re-based to the frozen level."""
    if fresh is None or not len(fresh):
        return frozen.copy()
    d = int(frozen.index.max())
    if d not in fresh.index:
        return frozen.copy()
    tail_idx = fresh.index[fresh.index > d]
    if not len(tail_idx):
        return frozen.copy()
    tail = fresh.loc[tail_idx].copy()
    for f in _OHLC:
        tail[f] = tail[f].astype(float) * (float(frozen.at[d, f]) / float(fresh.at[d, f]))
    return pd.concat([frozen, tail]).sort_index()


def load_holdout_coins(
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    data_dir: Path | str | None = None,
    live_data_dir: Path | str | None = None,
) -> dict[str, pd.DataFrame]:
    """Frozen-IS-canon coins dict spanning IS + holdout for the manifest universe + VIX."""
    tsnap.verify_manifest(snapshot_dir, manifest_path)
    manifest = tsnap.read_manifest(manifest_path)
    symbols = sorted({Path(rel).parts[0] for rel in manifest["files"]})
    frozen = ct.load_tradfi(symbols, snapshot_dir)
    tradable = [s for s in symbols if s != tc.VIX_SYM]
    fresh = sl.load_tradfi_spliced(tradable, data_dir, live_data_dir)
    fresh.update(ct.load_tradfi([tc.VIX_SYM], data_dir))
    return {sym: _extend_frozen(frozen[sym], fresh.get(sym)) for sym in symbols}


def _check_is_replay(team_dir: Path, net: pd.Series) -> bool:
    """Bit-compare the holdout net's IS rows against the frozen stage-1 net.

    The LAST frozen row is excluded: its pnl was truncated by construction (the snapshot has
    no next open, so ``ret_fwd`` is all-NaN there and sums to 0.0), while the holdout run sees
    the true first-holdout-open return. Every earlier row must match bit-for-bit.
    """
    csv = Path(team_dir) / "out" / "net_is.csv"
    if not csv.exists():
        raise ReplayMismatchError(f"{Path(team_dir).name}: out/net_is.csv missing")
    frozen = pd.read_csv(csv, index_col="date", parse_dates=["date"], float_precision="round_trip")[
        "net"
    ].iloc[:-1]
    frozen.index = frozen.index.astype(net.index.dtype)
    got = net.reindex(frozen.index)
    return bool(got.notna().all() and (got.to_numpy() == frozen.to_numpy()).all())


def evaluate_holdout(
    team_id: str,
    *,
    confirm: bool = False,
    apply_funding: bool = True,
    cost_mult: float = 1.0,
    exclude: tuple[str, ...] = (),
    label: str = "canonical",
    teams_dir: Path = tc.TEAMS_DIR,
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    data_dir: Path | str | None = None,
    live_data_dir: Path | str | None = None,
    funding_dir: Path | None = None,
    results_dir: Path | None = None,
    journal_path: Path = tc.JOURNAL_PATH,
) -> tuple[dict, pd.Series]:
    """Run one frozen submission over the sealed holdout window; returns (result, net)."""
    _gate(confirm)
    tc.journal(
        "holdout_run",
        journal_path,
        team_id=team_id,
        label=label,
        apply_funding=apply_funding,
        cost_mult=cost_mult,
        exclude=list(exclude),
    )
    td = tc.team_dir(team_id, teams_dir)
    tp.check_submission_shas(td)

    coins = load_holdout_coins(snapshot_dir, manifest_path, data_dir, live_data_dir)
    pn = te.panels_with_volume(coins)
    aux = te.make_aux(coins)
    mod = tp.load_strategy(td)
    raw = te.conform_raw(mod.build_raw_weights(te.team_view(pn), aux), pn)
    tp.purge_team_modules()
    for sym in exclude:
        if sym in raw.columns:
            raw[sym] = 0.0

    funding = None
    if apply_funding:
        tradable = list(pn["open"].columns)
        perp_map = {t: pm.PERP_SYMBOL_MAP.get(t, t) for t in tradable}
        kwargs = {} if funding_dir is None else {"funding_dir": Path(funding_dir)}
        funding = rb.daily_funding(perp_map, pn["open"].index, **kwargs)

    net, w = te.net_series(raw, pn["ret_fwd"], cost_mult=cost_mult, funding=funding)

    is_replay = None
    if cost_mult == 1.0 and not exclude:
        is_replay = _check_is_replay(td, net)
        if not is_replay:
            raise ReplayMismatchError(
                f"{team_id}: IS rows of the holdout run do not reproduce out/net_is.csv "
                "— causality break or tampered artifacts (integrity finding)"
            )

    m = te.evaluate(net, w, lo=tc.TRN_HOLD_START, hi=tc.TRN_HOLD_HI)
    result = {
        "schema": 1,
        "team_id": team_id,
        "label": label,
        "config": {
            "apply_funding": apply_funding,
            "cost_mult": cost_mult,
            "exclude": list(exclude),
        },
        "window": {
            "lo": str(tc.TRN_HOLD_START.date()),
            "hi_exclusive": str(tc.TRN_HOLD_HI.date()),
        },
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
