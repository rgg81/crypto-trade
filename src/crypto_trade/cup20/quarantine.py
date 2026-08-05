"""Physical custody of the holdout, and the tripwire for the window where custody must end.

Blindness in CUP-20 rests on absence-from-the-team's-data-root, a narrow protocol, namespace rules
and a static source scan. None of those is an operating-system control: every agent runs as the
same account, so a team process that decides to open ``data/cup20/sealed/`` can. This module
converts the strongest part of that story from a rule into a fact for the period it matters most.

**Quarantine (phase 1).** While teams are researching, the sealed snapshot and the un-truncated
acquisition snapshot do not need to be anywhere a team can reach, so they are moved out of the
working tree entirely. During that window blindness is not honour-bound at all -- the bytes are not
on any path a team process can name. :func:`quarantine_holdout` performs the move and writes a
receipt; :func:`restore_holdout` reverses it, but only after verifying that what comes back is
byte-for-byte what went out, measured against the digest the activation record bound before any
team started. A mismatch refuses the restore outright rather than reporting and continuing: a
holdout that was modified while out of the tree is not a holdout, and the tournament has to stop.

**Tripwire (phase 3).** Scoring the finalists requires the sealed data to be present and readable,
so quarantine cannot cover that window. Two detectors do, and both are weaker than quarantine --
stated here rather than discovered later:

* A **canary file** is planted inside the sealed tree before quarantine and stays there for the
  rest of the tournament. It carries a high-entropy token that exists nowhere else in the
  repository, so the token appearing in any team artifact is evidence that the sealed tree's bytes
  were read and carried away. What it proves: a bulk read (``cat``, ``cp -r``, ``tar``, ``grep
  -r``, a directory walk) that persisted its output. What it does NOT prove: absence of a targeted
  read. A process that opens only ``bars.parquet`` never touches the canary and leaves no token.
  The canary is a bulk-read-and-keep detector, not a read detector.
* An **access-time tripwire**. :func:`arm_sealed_access_tripwire` back-dates every sealed file's
  ``atime`` by 48 hours and records the armed value. Under the ``relatime`` mount option -- what
  this repository's filesystem actually uses -- the kernel updates ``atime`` on read only when the
  existing ``atime`` is older than ``mtime``/``ctime`` or older than 24 hours, so an armed file's
  FIRST read always moves it. Arming is what makes ``relatime`` usable at all; unarmed sampling
  would miss a read that follows a recent one. What it does NOT prove: the mount may be
  ``noatime`` (then the control is inert, and :func:`sealed_access_report` says so from
  ``/proc/mounts`` rather than reporting a clean result); a reader may pass ``O_NOATIME``, which
  the file's own owner is allowed to do; anyone able to call ``utime`` can put ``atime`` back; and
  a read of a COPY of the tree made elsewhere leaves the original untouched. It also does not say
  WHO read the file -- only that something did, since arming.

None of the three is complete on its own. Together they cover the tournament's whole timeline:
quarantine makes phase 1 a physical fact, and the two tripwires make phase 3 reviewable.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from crypto_trade.cup20.activation import verify_activation
from crypto_trade.cup20.archive import bundle_digest
from crypto_trade.cup20.journal import append_record, read_records, verify_chain
from crypto_trade.cup20.snapshot import load_snapshot

RECEIPT_SCHEMA_VERSION = "cup20-quarantine-receipt-v1"
BASELINE_SCHEMA_VERSION = "cup20-sealed-access-baseline-v1"

# The canary lives INSIDE the sealed tree, so it travels with it into quarantine and back. It is
# deliberately not a manifest-declared dataset: ``load_snapshot`` digests exactly the five
# ``*.parquet`` files named in ``snapshot._DATASETS``, so planting this file cannot move
# ``manifest_sha256`` and therefore cannot invalidate the activation record that bound it.
# ``quarantine_holdout`` asserts that rather than assuming it.
CANARY_FILENAME = "HOLDOUT-CANARY-DO-NOT-READ.txt"
CANARY_TOKEN_FILENAME = "canary-token.txt"
CANARY_TOKEN_PREFIX = "cup20-holdout-canary:"

QUARANTINE_EVENT = "holdout_quarantined"
RESTORE_EVENT = "holdout_restored"
TRIAL_EVENT = "trial_accepted"

# The two trees that leave the working tree, keyed by the receipt name used for each. The sealed
# snapshot is the holdout itself; the acquisition snapshot is its un-truncated superset and leaks
# exactly the same rows, so quarantining one without the other would be theatre.
SEALED_TREE = "sealed"
ACQUISITION_TREE = "acquisition"
TREE_NAMES: tuple[str, ...] = (SEALED_TREE, ACQUISITION_TREE)

# How far back arming pushes ``atime``. Must exceed the kernel's 24-hour ``relatime`` threshold, or
# arming would leave files whose next read the kernel declines to record.
ARMED_ATIME_LAG_SECONDS = 48 * 3600

_TOKEN_PATTERN = re.compile(r"\A[0-9a-f]{32,128}\Z")


def _digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canary_contents(token: str) -> str:
    """The canary file's exact text. Legible to a human who opens it, greppable for the review."""
    return (
        "CUP-20 SEALED HOLDOUT -- ORGANISER ONLY\n"
        "\n"
        "This file is a tripwire. It sits inside the sealed holdout snapshot, which no team is\n"
        "permitted to open (charter section 5, playbook section 1). The token below appears\n"
        "nowhere else in this repository. If it turns up in a team's workspace, an archive, a\n"
        "notebook, a log or a scratch file, that team read the sealed tree.\n"
        "\n"
        f"{CANARY_TOKEN_PREFIX}{token}\n"
    )


def _resolve(path: str | Path) -> Path:
    return Path(path).resolve()


def _require_directory(path: Path, label: str) -> None:
    if not path.is_dir():
        raise FileNotFoundError(f"{label} is not a directory: {path}")


def _tree_paths(
    sealed_root: Path, acquisition_root: Path, quarantine_root: Path
) -> dict[str, tuple[Path, Path]]:
    """Working-tree source and quarantine destination for each tree, keyed by receipt name."""
    return {
        SEALED_TREE: (sealed_root, quarantine_root / SEALED_TREE),
        ACQUISITION_TREE: (acquisition_root, quarantine_root / ACQUISITION_TREE),
    }


def quarantine_holdout(
    *,
    quarantine_root: str | Path,
    activation_record: str | Path = "tournament/cup20/activation-freeze.json",
    receipt_path: str | Path = "tournament/cup20/quarantine-receipt.json",
    acquisition_root: str | Path = "data/cup20/acquisition",
    journal_path: str | Path | None = None,
    repo_root: str | Path = ".",
    token: str | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Move the sealed and acquisition snapshots out of the working tree. Run before team 01 starts.

    Every precondition is checked before anything moves, because a half-quarantined tournament is
    worse than an unquarantined one: the activation record must still verify (quarantining a
    tournament that has already drifted would freeze the drift out of reach), no receipt may exist
    yet (quarantine happens once), and the destination must be outside the working tree (a
    destination inside it would move the bytes without moving them out of a team's reach).

    Returns the receipt, which is also written to ``receipt_path`` and is meant to be committed:
    it is the working tree's only durable evidence that quarantine happened, and the only place
    the expected restore digests are recorded.
    """
    receipt_file = Path(receipt_path)
    if receipt_file.exists():
        raise FileExistsError(
            f"a quarantine receipt already exists at {receipt_file}; quarantine happens once per "
            "tournament, and re-running it would overwrite the digests restore verifies against"
        )

    # Verify BEFORE moving. An activation record that already disagrees with the tree is a fact
    # about the tournament that has to be resolved in the open, not carried into quarantine.
    record = verify_activation(activation_record)

    destination = _resolve(quarantine_root)
    working_root = _resolve(repo_root)
    if destination == working_root or destination.is_relative_to(working_root):
        raise ValueError(
            f"quarantine root {destination} is inside the working tree {working_root}; the point "
            "of quarantine is that the bytes leave every path a team process can reach"
        )
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"quarantine root {destination} exists and is not empty")

    sealed_root = Path(record["sealed_root"])
    acquisition = Path(acquisition_root)
    _require_directory(sealed_root, "sealed root")
    _require_directory(acquisition, "acquisition root")

    trees = _tree_paths(sealed_root, acquisition, destination)
    canary_token = secrets.token_hex(32) if token is None else token
    if not _TOKEN_PATTERN.match(canary_token):
        raise ValueError(
            "canary token must be 32-128 lowercase hex characters so it cannot collide with "
            "ordinary text and cannot be mistaken for a legitimate identifier"
        )

    canary_file = sealed_root / CANARY_FILENAME
    if canary_file.exists():
        raise FileExistsError(f"a canary is already planted at {canary_file}")
    canary_text = canary_contents(canary_token)
    canary_file.write_text(canary_text)

    # The canary must not disturb the authority the activation record bound. Asserted, not assumed:
    # if a future change ever made the manifest cover every file in the tree, planting the canary
    # would silently invalidate the sealed snapshot for the rest of the tournament.
    replanted = load_snapshot(sealed_root).manifest_sha256
    if replanted != record["sealed_manifest_sha256"]:
        canary_file.unlink()
        raise ValueError(
            "planting the canary changed the sealed snapshot's manifest digest "
            f"({record['sealed_manifest_sha256']} -> {replanted}); the canary has been removed "
            "and nothing was quarantined"
        )

    before = {name: bundle_digest(source) for name, (source, _) in trees.items()}

    destination.mkdir(parents=True, exist_ok=True)
    token_file = destination / CANARY_TOKEN_FILENAME
    token_file.write_text(canary_token + "\n")
    os.chmod(token_file, 0o600)

    for name, (source, target) in trees.items():
        shutil.move(str(source), str(target))
        moved = bundle_digest(target)
        if moved != before[name]:
            raise ValueError(
                f"the {name} tree changed while being moved to quarantine "
                f"({before[name]} -> {moved}); it is now at {target} and MUST NOT be restored "
                "until the difference is explained"
            )
        if source.exists():
            raise ValueError(f"the {name} tree is still present at {source} after the move")

    stamped = time.time() if now is None else now
    receipt: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "quarantined_at_epoch": float(stamped),
        "quarantine_root": str(destination),
        "activation_record_path": str(activation_record),
        "sealed_manifest_sha256": record["sealed_manifest_sha256"],
        "canary_relative_path": f"{SEALED_TREE}/{CANARY_FILENAME}",
        "canary_file_sha256": _digest_bytes(canary_text.encode("utf-8")),
        "canary_token_sha256": _digest_bytes(canary_token.encode("utf-8")),
        "trees": {
            name: {
                "working_path": str(source),
                "quarantine_path": str(target),
                "bundle_sha256": before[name],
            }
            for name, (source, target) in trees.items()
        },
    }
    receipt_file.parent.mkdir(parents=True, exist_ok=True)
    receipt_file.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    if journal_path is not None:
        append_record(
            journal_path,
            QUARANTINE_EVENT,
            {
                "quarantine_root": str(destination),
                "sealed_manifest_sha256": record["sealed_manifest_sha256"],
                "canary_token_sha256": receipt["canary_token_sha256"],
            },
        )
    return receipt


def load_receipt(receipt_path: str | Path) -> dict[str, Any]:
    """Parse a quarantine receipt, rejecting any shape a later check would have to guess at."""
    path = Path(receipt_path)
    payload: Any = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"quarantine receipt {path} must be a JSON object")
    if payload.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        raise ValueError(
            f"quarantine receipt {path} has schema_version "
            f"{payload.get('schema_version')!r}, expected {RECEIPT_SCHEMA_VERSION!r}"
        )
    trees = payload.get("trees")
    if not isinstance(trees, Mapping) or set(trees) != set(TREE_NAMES):
        raise ValueError(
            f"quarantine receipt {path} must describe exactly the trees {list(TREE_NAMES)}"
        )
    for name, entry in trees.items():
        if not isinstance(entry, Mapping):
            raise ValueError(f"quarantine receipt {path} tree {name} is not an object")
        for field in ("working_path", "quarantine_path", "bundle_sha256"):
            if not isinstance(entry.get(field), str):
                raise ValueError(f"quarantine receipt {path} tree {name} is missing {field}")
    for field in (
        "quarantine_root",
        "activation_record_path",
        "sealed_manifest_sha256",
        "canary_relative_path",
        "canary_file_sha256",
        "canary_token_sha256",
    ):
        if not isinstance(payload.get(field), str):
            raise ValueError(f"quarantine receipt {path} is missing {field}")
    return payload


def verify_quarantine_in_effect(
    *, receipt_path: str | Path = "tournament/cup20/quarantine-receipt.json"
) -> dict[str, Any]:
    """Assert, right now, that neither quarantined tree is reachable from the working tree.

    Raises rather than returning a verdict: an organiser calls this in the middle of the research
    phase precisely to be told loudly if the answer is no.
    """
    receipt = load_receipt(receipt_path)
    present = [
        name for name, entry in receipt["trees"].items() if Path(entry["working_path"]).exists()
    ]
    if present:
        raise ValueError(
            f"quarantine is NOT in effect: {sorted(present)} are present in the working tree at "
            f"{[receipt['trees'][name]['working_path'] for name in sorted(present)]}"
        )
    missing = [
        name
        for name, entry in receipt["trees"].items()
        if not Path(entry["quarantine_path"]).is_dir()
    ]
    if missing:
        raise ValueError(
            f"quarantine is not verifiable: {sorted(missing)} are absent from the quarantine root "
            f"{receipt['quarantine_root']}"
        )
    return receipt


def verify_quarantine_covered_research(
    *,
    journal_path: str | Path,
    receipt_path: str | Path = "tournament/cup20/quarantine-receipt.json",
) -> dict[str, Any]:
    """Prove from the hash chain that quarantine bracketed every accepted trial.

    A wall-clock timestamp in the receipt proves nothing on its own -- it is a number someone
    typed. The journal is append-only and hash-chained, so the ORDER of records is evidence: if
    ``holdout_quarantined`` sits at a lower sequence number than every ``trial_accepted``, then no
    trial was accepted while the holdout was in the working tree, and re-ordering that to look
    otherwise breaks the chain. If a ``holdout_restored`` record exists, it must sit above every
    trial for the same reason.

    Fails closed on a journal with no accepted trials: this check certifies coverage of the
    research phase, and a journal that records no research is a sign the review is pointed at the
    wrong file, not evidence of a clean tournament.
    """
    verify_chain(journal_path)
    receipt = load_receipt(receipt_path)
    records = read_records(journal_path)
    quarantines = [r for r in records if r.get("event_type") == QUARANTINE_EVENT]
    restores = [r for r in records if r.get("event_type") == RESTORE_EVENT]
    trials = [r for r in records if r.get("event_type") == TRIAL_EVENT]
    if len(quarantines) != 1:
        raise ValueError(
            f"expected exactly one {QUARANTINE_EVENT} record in {journal_path}, "
            f"found {len(quarantines)}"
        )
    if len(restores) > 1:
        raise ValueError(
            f"expected at most one {RESTORE_EVENT} record in {journal_path}, found {len(restores)}"
        )
    if not trials:
        raise ValueError(
            f"{journal_path} records no {TRIAL_EVENT} events; there is no research phase for "
            "quarantine to have covered, so this journal is not the one the review needs"
        )
    quarantine_sequence = int(quarantines[0]["sequence"])
    trial_sequences = [int(record["sequence"]) for record in trials]
    if quarantine_sequence > min(trial_sequences):
        raise ValueError(
            f"{QUARANTINE_EVENT} is at sequence {quarantine_sequence}, after the first accepted "
            f"trial at sequence {min(trial_sequences)}: the holdout was in the working tree while "
            "research was already running"
        )
    restore_sequence = int(restores[0]["sequence"]) if restores else None
    if restore_sequence is not None and restore_sequence < max(trial_sequences):
        raise ValueError(
            f"{RESTORE_EVENT} is at sequence {restore_sequence}, before the last accepted trial "
            f"at sequence {max(trial_sequences)}: the holdout was back in the working tree while "
            "research was still running"
        )
    if quarantines[0]["payload"].get("canary_token_sha256") != receipt["canary_token_sha256"]:
        raise ValueError(
            "the journalled quarantine event and the receipt describe different canary tokens"
        )
    return {
        "quarantine_sequence": quarantine_sequence,
        "restore_sequence": restore_sequence,
        "first_trial_sequence": min(trial_sequences),
        "last_trial_sequence": max(trial_sequences),
        "trials_covered": len(trial_sequences),
    }


def restore_holdout(
    *,
    receipt_path: str | Path = "tournament/cup20/quarantine-receipt.json",
    selection_freeze_path: str | Path = "tournament/cup20/selection-freeze.json",
    restore_stamp_path: str | Path = "tournament/cup20/quarantine-restore.json",
    baseline_path: str | Path = "tournament/cup20/sealed-access-baseline.json",
    journal_path: str | Path | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Bring both trees back, but only after proving they are byte-identical to what went out.

    Verification happens at the QUARANTINE location, before anything moves. A tampered tree that
    was verified after landing in the working tree would already be in a team's reach by the time
    the check failed; verifying first means a tree that fails never re-enters the tree at all.

    Three independent things must agree, and any one of them failing refuses the restore:

    1. each tree's bundle digest equals the receipt's -- this covers the acquisition snapshot,
       which has no manifest of its own, and covers files ADDED to or REMOVED from either tree
       (including the canary), which a manifest digest over five named parquet files cannot see;
    2. the full activation record still verifies with the sealed root read from quarantine, so the
       sealed snapshot's own manifest digest is checked against the value bound before any team
       started -- not against the receipt, which was written later;
    3. after the move, the activation record verifies again with no override, so the tree that is
       now back in place is the one that was checked.

    ``selection_freeze_path`` must already exist. The holdout may not come back while a team could
    still act on it, and the selection freeze is the artifact that says the field is closed.
    """
    receipt = load_receipt(receipt_path)
    stamp_file = Path(restore_stamp_path)
    if stamp_file.exists():
        raise FileExistsError(
            f"a restore stamp already exists at {stamp_file}; the holdout has already been restored"
        )
    freeze = Path(selection_freeze_path)
    if not freeze.is_file():
        raise FileNotFoundError(
            f"refusing to restore the holdout: the selection freeze {freeze} does not exist yet, "
            "so the field is not closed and a team could still act on the sealed rows"
        )

    for name, entry in sorted(receipt["trees"].items()):
        target = Path(entry["working_path"])
        if target.exists():
            raise FileExistsError(
                f"the {name} tree is already present at {target}; restore would overwrite it"
            )
        source = Path(entry["quarantine_path"])
        _require_directory(source, f"quarantined {name} tree")
        observed = bundle_digest(source)
        if observed != entry["bundle_sha256"]:
            raise ValueError(
                f"REFUSING TO RESTORE: the quarantined {name} tree at {source} does not match the "
                f"digest recorded when it was quarantined (expected {entry['bundle_sha256']}, "
                f"found {observed}). The holdout was modified while out of the working tree. "
                "Nothing has been moved. Do not score anything against it."
            )

    activation_record = receipt["activation_record_path"]
    verify_activation(
        activation_record,
        sealed_root_override=Path(receipt["trees"][SEALED_TREE]["quarantine_path"]),
    )

    for name, entry in sorted(receipt["trees"].items()):
        source = Path(entry["quarantine_path"])
        target = Path(entry["working_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        landed = bundle_digest(target)
        if landed != entry["bundle_sha256"]:
            raise ValueError(
                f"the {name} tree changed while being restored to {target} "
                f"(expected {entry['bundle_sha256']}, found {landed})"
            )

    verify_activation(activation_record)

    sealed_working = Path(receipt["trees"][SEALED_TREE]["working_path"])
    canary_file = sealed_working / CANARY_FILENAME
    if not canary_file.is_file():
        raise ValueError(f"the canary is missing from the restored sealed tree at {canary_file}")
    canary_digest = _digest_bytes(canary_file.read_bytes())
    if canary_digest != receipt["canary_file_sha256"]:
        raise ValueError(
            f"the restored canary at {canary_file} does not match the receipt "
            f"(expected {receipt['canary_file_sha256']}, found {canary_digest})"
        )

    baseline = arm_sealed_access_tripwire(sealed_working, baseline_path=baseline_path, now=now)

    stamped = time.time() if now is None else now
    payload: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "restored_at_epoch": float(stamped),
        "receipt_path": str(receipt_path),
        "selection_freeze_path": str(freeze),
        "sealed_manifest_sha256": receipt["sealed_manifest_sha256"],
        "access_baseline_path": str(baseline_path),
        "armed_files": sorted(baseline["files"]),
    }
    stamp_file.parent.mkdir(parents=True, exist_ok=True)
    stamp_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    if journal_path is not None:
        append_record(
            journal_path,
            RESTORE_EVENT,
            {
                "sealed_manifest_sha256": receipt["sealed_manifest_sha256"],
                "selection_freeze_path": str(freeze),
            },
        )
    return payload


def read_canary_token(
    *,
    quarantine_root: str | Path | None = None,
    receipt_path: str | Path = "tournament/cup20/quarantine-receipt.json",
) -> str:
    """The planted token, read from the quarantine root and checked against the receipt's digest.

    The token itself is never committed -- the receipt carries only its SHA-256 -- because a token
    in the repository is a token a team can grep for and avoid. Checking the digest here is what
    makes the value usable as evidence: a reviewer who scans for the wrong string proves nothing.
    """
    receipt = load_receipt(receipt_path)
    root = Path(receipt["quarantine_root"] if quarantine_root is None else quarantine_root)
    token = (root / CANARY_TOKEN_FILENAME).read_text().strip()
    if _digest_bytes(token.encode("utf-8")) != receipt["canary_token_sha256"]:
        raise ValueError(
            f"the token at {root / CANARY_TOKEN_FILENAME} does not match the receipt's "
            "canary_token_sha256; scanning for it would prove nothing"
        )
    return token


def _sealed_files(sealed_root: Path) -> list[Path]:
    return sorted(path for path in sealed_root.rglob("*") if path.is_file())


def mount_options(path: str | Path, *, mounts_path: str | Path = "/proc/mounts") -> tuple[str, ...]:
    """Mount options governing ``path``, or ``()`` when they cannot be determined.

    Read rather than assumed, because whether the access-time tripwire works at all is a property
    of the mount: ``noatime`` makes it silently inert, and a control that is inert must say so
    instead of reporting a clean result.
    """
    try:
        lines = Path(mounts_path).read_text().splitlines()
    except OSError:
        return ()
    target = _resolve(path)
    best: tuple[int, tuple[str, ...]] = (-1, ())
    for line in lines:
        fields = line.split()
        if len(fields) < 4:
            continue
        mount_point = Path(fields[1].replace("\\040", " "))
        if target == mount_point or target.is_relative_to(mount_point):
            depth = len(mount_point.parts)
            if depth > best[0]:
                best = (depth, tuple(fields[3].split(",")))
    return best[1]


def arm_sealed_access_tripwire(
    sealed_root: str | Path,
    *,
    baseline_path: str | Path = "tournament/cup20/sealed-access-baseline.json",
    now: float | None = None,
) -> dict[str, Any]:
    """Back-date every sealed file's ``atime`` and record the armed value.

    Back-dating is the whole mechanism. Under ``relatime`` the kernel records a read only when the
    stored ``atime`` is already older than ``mtime``/``ctime`` or older than 24 hours; a file whose
    ``atime`` is recent absorbs any number of reads without moving. Pushing ``atime`` 48 hours into
    the past guarantees the next read is recorded, which converts ``relatime`` from "unreliable"
    into "reliable exactly once per arming". ``mtime`` is preserved untouched -- moving it would
    change what a later reader believes about when the data was written.
    """
    root = Path(sealed_root)
    _require_directory(root, "sealed root")
    stamped = time.time() if now is None else now
    armed_atime = float(stamped) - ARMED_ATIME_LAG_SECONDS
    files: dict[str, int] = {}
    for path in _sealed_files(root):
        stat = path.stat()
        os.utime(path, ns=(int(armed_atime * 1_000_000_000), stat.st_mtime_ns))
        files[path.relative_to(root).as_posix()] = path.stat().st_atime_ns
    baseline: dict[str, Any] = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "armed_at_epoch": float(stamped),
        "sealed_root": str(root),
        "mount_options": list(mount_options(root)),
        "files": files,
    }
    destination = Path(baseline_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
    return baseline


def sealed_access_report(
    sealed_root: str | Path,
    *,
    baseline_path: str | Path = "tournament/cup20/sealed-access-baseline.json",
    mounts_path: str | Path = "/proc/mounts",
) -> dict[str, Any]:
    """Which sealed files have been read since arming, and whether the answer means anything.

    ``atime_is_recorded`` is the honest qualifier on everything else in the report. When the mount
    carries ``noatime`` the kernel never updates access times at all, so ``accessed`` would be
    empty no matter what any process did; the flag is false in that case and an empty ``accessed``
    list must be read as "this control told us nothing", not as "nobody read the holdout".

    ``appeared`` and ``vanished`` are reported separately from ``accessed`` because a file added to
    or removed from the sealed tree after arming is a different and more serious finding than one
    that was read.
    """
    root = Path(sealed_root)
    baseline: Any = json.loads(Path(baseline_path).read_text())
    if not isinstance(baseline, dict) or baseline.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise ValueError(
            f"access baseline {baseline_path} has schema_version "
            f"{baseline.get('schema_version') if isinstance(baseline, dict) else None!r}, "
            f"expected {BASELINE_SCHEMA_VERSION!r}"
        )
    if not isinstance(baseline.get("files"), Mapping) or "armed_at_epoch" not in baseline:
        raise ValueError(
            f"access baseline {baseline_path} is missing its files table or armed_at_epoch; "
            "an unreadable baseline cannot be reported as a clean tripwire"
        )
    recorded: Mapping[str, Any] = baseline["files"]
    current = {
        path.relative_to(root).as_posix(): path.stat().st_atime_ns for path in _sealed_files(root)
    }
    accessed = sorted(
        name for name, armed in recorded.items() if name in current and current[name] != int(armed)
    )
    options = mount_options(root, mounts_path=mounts_path)
    return {
        "sealed_root": str(root),
        "armed_at_epoch": baseline["armed_at_epoch"],
        "mount_options": list(options),
        "atime_is_recorded": "noatime" not in options,
        "accessed": accessed,
        "appeared": sorted(set(current) - set(recorded)),
        "vanished": sorted(set(recorded) - set(current)),
    }
