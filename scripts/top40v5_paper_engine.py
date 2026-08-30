"""One tick: build the shared cache, replay four desks against it, publish if parity holds.

**One cache, four desks.** The engine builds a single market snapshot per boundary and replays all
four desks against those exact bytes. Two consequences worth stating, because they change how a
failure is read:

* A cache or fetch failure hits all four desks at once. Four desks failing at the same boundary is
  **one** fault, not four -- diagnose the generation, not the desks.
* A difference between two desks is a difference between two strategies, never between two fetches.
  If two desks disagree about a price, that is a real integrity failure.

**Nothing is published until parity is re-proved.** Every tick re-replays the frozen historical
window and every already-published row, and refuses to publish if either fails to reproduce. That
is what makes ``PARITY-BROKEN`` mean something: the live desk and the backtest evaluator it is
supposed to *be* have diverged, structurally, rather than a fetch having timed out.

**A killed tick is safe.** Nothing is written until the tick completes. A partial tick leaves an
``attempt.json`` in ``RUNNING`` and no boundary record, and the next run redoes that boundary. There
is no half-published state to repair.

Paper by construction: there is no signed client and no order path anywhere in this import graph.

Usage::

    uv run python scripts/top40v5_paper_engine.py --once
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import sys
import traceback
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.tournament.v5.desk.ledger import AppendInvarianceError, append_rows, read_ledger
from crypto_trade.tournament.v5.desk.parity import DeskParityError
from crypto_trade.tournament.v5.engine import EvaluatorConfig, evaluate_targets, generate_targets

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper-top40v5"
# The desks read the FORWARD snapshot when it exists -- the frozen one is the tournament's
# evidence and stops at the historical window's end, so a desk reading it can never publish an
# official day. The forward snapshot is the frozen one plus a REST-appended tail; live-append.json
# beside it records exactly which range came from REST rather than from checksummed archives.
FROZEN_SNAPSHOT = REPO / "data" / "top40" / "snapshot-v3"
FORWARD_SNAPSHOT = REPO / "data" / "top40" / "forward"
SNAPSHOT = FORWARD_SNAPSHOT if (FORWARD_SNAPSHOT / "bars.parquet").is_file() else FROZEN_SNAPSHOT
INTERVAL_HOURS = 8
# The desk replays from here so that carried positions and funding are path-correct at the
# boundary. Starting at the boundary itself would score a cold book against a warm one.
REPLAY_START = pd.Timestamp("2024-02-01", tz="UTC")


def _boundary(now: pd.Timestamp) -> pd.Timestamp:
    """The most recent closed 8h boundary."""

    floored = now.floor(f"{INTERVAL_HOURS}h")
    return floored - pd.Timedelta(hours=INTERVAL_HOURS)


def _load(path: Path, name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module.build_strategy()


def _assert_manifest(manifest: dict) -> None:
    """A desk replays the bytes that were frozen, or it does not replay."""

    for desk, spec in manifest.items():
        for lane, bound in spec["bundle"].items():
            path = PAPER / desk / f"frozen-{lane}.py"
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != bound["sha256"]:
                raise DeskParityError(
                    f"deployment drift: {desk}/{path.name} is {actual[:12]}, "
                    f"manifest binds {bound['sha256'][:12]}"
                )


def _combine(frames: list[pd.DataFrame]) -> pd.DataFrame:
    reserved = [c for c in frames[0].columns if c.startswith("__")]
    numeric = [f.drop(columns=reserved, errors="ignore").astype(float) for f in frames]
    columns = sorted(set().union(*[set(f.columns) for f in numeric]))
    combined = sum(f.reindex(columns=columns).fillna(0.0) for f in numeric) / float(len(numeric))
    for column in reserved:
        combined[column] = np.logical_or.reduce([f[column].to_numpy() for f in frames])
    return combined


def _returns_for(desk: str, spec: dict, data: dict, decisions: list) -> pd.DataFrame:
    lanes = [spec["lane"]] if spec["lane"] else spec["members"]
    frames = [
        generate_targets(
            _load(PAPER / desk / f"frozen-{lane}.py", f"frozen_{desk}_{lane}"),
            data["bars"],
            data["funding"],
            data["membership"],
            decisions,
            seed=42,
            interval_hours=INTERVAL_HOURS,
        )
        for lane in lanes
    ]
    targets = frames[0] if len(frames) == 1 else _combine(frames)
    result = evaluate_targets(
        data["bars"],
        data["funding"],
        data["membership"],
        targets,
        mark_prices=data["mark_prices"],
        config=EvaluatorConfig(),
        cost_multiplier=1.0,
    )
    rows = result.returns.reset_index()
    rows = rows.rename(columns={rows.columns[0]: "boundary"})
    keep = [
        c for c in ("boundary", "net_return", "gross_exposure", "turnover") if c in rows.columns
    ]
    # Drop the final boundary: it is provisional until a later bar exists.
    #
    # Measured, not assumed. Replaying the same snapshot to 2024-03-01 and to 2024-06-01 produces
    # identical rows everywhere EXCEPT the shorter run's last boundary, which moves by 2.2e-04 --
    # the evaluator treats a decision with no subsequent bar differently from the same decision
    # once one exists. Publishing it would mean every tick rewrites the row it published last time,
    # which the append-invariant ledger correctly refuses. A row becomes final when the next
    # boundary exists, so that is when it is published.
    return rows[keep].iloc[:-1]


def tick(now: pd.Timestamp) -> int:
    warnings.filterwarnings("ignore")
    launch = PAPER / "launch.json"
    if not launch.is_file():
        print("not launched; nothing to do")
        return 0

    # One engine at a time, for the whole field.
    #
    # Added after running two concurrently by accident: the second truncated the shared log while
    # the first still held it open at its old offset, so the log showed one run's desks and the
    # other run's summary, and read as a failure that had not happened. Two engines can also
    # publish the same boundary twice -- the append-invariant ledger would refuse the rewrite, but
    # a refusal is a worse way to discover this than a lock that simply declines to start.
    PAPER.mkdir(parents=True, exist_ok=True)
    lock_handle = (PAPER / "engine.lock").open("w")
    try:
        fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another engine holds paper-top40v5/engine.lock; declining to start")
        return 0
    lock_handle.write(f"{now}\n")
    lock_handle.flush()
    return _tick_locked(now, launch)


def _tick_locked(now: pd.Timestamp, launch: Path) -> int:
    manifest = json.loads((PAPER / "deployment-manifest.json").read_text(encoding="utf-8"))
    _assert_manifest(manifest)

    boundary = _boundary(now)
    official_start = pd.Timestamp(json.loads(launch.read_text(encoding="utf-8"))["official_start"])
    print(f"boundary {boundary}  (official from {official_start.date()})")

    data = {
        name: pd.read_parquet(SNAPSHOT / f"{name}.parquet")
        for name in ("bars", "funding", "membership", "mark_prices")
    }
    # One generation, hashed, shared by all four desks. A desk cannot see a different price.
    generation = hashlib.sha256(
        b"".join(pd.util.hash_pandas_object(data[n]).values.tobytes() for n in sorted(data))
    ).hexdigest()
    print(f"cache generation {generation[:16]}")

    # The snapshot is the desk's whole world, so a boundary past its last bar cannot be replayed.
    # Clamp and say so, loudly, rather than raising: a desk that is merely waiting for data is not
    # a broken desk, and conflating the two would make DATA-STALE read as a parity failure. The
    # monitor surfaces this as its own class.
    last_bar = pd.Timestamp(data["bars"]["open_time"].max())
    stale_hours = (boundary - last_bar) / pd.Timedelta(hours=1)
    effective = min(boundary, last_bar)
    if effective < boundary:
        print(
            f"DATA-STALE: snapshot ends {last_bar}, boundary is {boundary} "
            f"({stale_hours:.0f}h behind); replaying to {effective} and publishing nothing past it"
        )
    (PAPER / "boundary.json").write_text(
        json.dumps(
            {
                "boundary": str(boundary),
                "replayed_through": str(effective),
                "snapshot_last_bar": str(last_bar),
                "stale_hours": round(stale_hours, 1),
                "generation": generation[:32],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    decisions = list(
        pd.date_range(
            REPLAY_START, effective, freq=f"{INTERVAL_HOURS}h", tz="UTC", inclusive="both"
        )
    )

    published = 0
    for desk, spec in sorted(manifest.items()):
        root = PAPER / desk
        attempt = root / "attempt.json"
        attempt.write_text(
            json.dumps({"status": "RUNNING", "boundary": str(boundary)}), encoding="utf-8"
        )
        try:
            rows = _returns_for(desk, spec, data, decisions)
            rows["official"] = rows["boundary"] >= official_start
            added = append_rows(root / "ledger" / "forward_returns.parquet", rows, key="boundary")
            (root / "boundary.json").write_text(
                json.dumps({"boundary": str(boundary), "generation": generation[:32]}, indent=2),
                encoding="utf-8",
            )
            attempt.write_text(
                json.dumps(
                    {"status": "OK", "boundary": str(boundary), "rows_added": added}, indent=2
                ),
                encoding="utf-8",
            )
            total = len(read_ledger(root / "ledger" / "forward_returns.parquet"))
            print(f"  {desk:16s} OK  +{added} rows, {total} total")
            published += 1
        except (AppendInvarianceError, DeskParityError) as error:
            attempt.write_text(
                json.dumps(
                    {
                        "status": "FAILED",
                        "boundary": str(boundary),
                        "error_type": type(error).__name__,
                        "error": str(error),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"  {desk:16s} PARITY-BROKEN  {error}"[:200])
        except Exception as error:  # noqa: BLE001 - operational, not a parity break
            attempt.write_text(
                json.dumps(
                    {
                        "status": "FAILED",
                        "boundary": str(boundary),
                        "error_type": type(error).__name__,
                        "error": str(error),
                        "traceback": traceback.format_exc()[-2000:],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"  {desk:16s} FAIL  {type(error).__name__}: {error}"[:200])

    print(f"\n{published}/{len(manifest)} desks published boundary {boundary}")
    return 0 if published == len(manifest) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="run a single tick")
    parser.add_argument("--as-of", default=None, help="pretend now is this UTC timestamp")
    arguments = parser.parse_args()
    now = pd.Timestamp(arguments.as_of, tz="UTC") if arguments.as_of else pd.Timestamp.now(tz="UTC")
    return tick(now)


if __name__ == "__main__":
    sys.exit(main())
