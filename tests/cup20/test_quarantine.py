"""Physical custody of the holdout, and the tripwires for the window custody cannot cover.

Two mutations dominate this file.

The first is a restore that does not actually verify: an implementation that moves the trees back
and *then* checks, or that compares the tree against the receipt it wrote itself rather than
against the digest activation bound before any team started, would pass a naive round-trip test and
fail the only case that matters. Every corruption case below therefore asserts BOTH halves --
that the restore raised, and that nothing moved.

The second is a control that reports clean because it is inert. The access-time tripwire is
worthless on a ``noatime`` mount, and the test for that reads a synthetic ``/proc/mounts`` rather
than trusting the developer's own filesystem to be representative.
"""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20 import quarantine as q
from crypto_trade.cup20.activation import build_activation_record, verify_activation
from crypto_trade.cup20.archive import FORBIDDEN_PATTERNS, bundle_digest
from crypto_trade.cup20.journal import append_record
from crypto_trade.cup20.snapshot import load_snapshot, write_split_snapshots

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_CONFIG = REPO_ROOT / "tournament" / "cup20" / "config.toml"

_CUTOFF = pd.Timestamp("2021-06-01T00:00:00Z")
_SEALED_END = pd.Timestamp("2022-01-01T00:00:00Z")
_TOKEN = "a" * 64


def _panels(symbols=("AUSDT", "BUSDT"), seed=11):
    times = pd.date_range("2021-01-01T00:00:00Z", periods=1200, freq="8h")
    rng = np.random.default_rng(seed)
    frames = []
    prices: dict[str, np.ndarray] = {}
    for symbol in symbols:
        price = 100.0 * np.cumprod(1.0 + rng.normal(0.0002, 0.01, len(times)))
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
    boundaries = pd.date_range("2021-01-04T00:00:00Z", _SEALED_END, freq="7D", inclusive="left")
    membership = pd.DataFrame(
        {
            "reconstitution_time": np.repeat(boundaries, len(symbols)),
            "symbol": list(symbols) * len(boundaries),
            "liquidity_rank": list(range(1, len(symbols) + 1)) * len(boundaries),
            "trailing_quote_volume": 1e9,
        }
    )
    metadata = pd.DataFrame(
        {
            "symbol": list(symbols),
            "contract_type": "PERPETUAL",
            "quote_asset": "USDT",
            "margin_asset": "USDT",
            "is_crypto": True,
            "onboard_date": pd.Timestamp("2020-01-01T00:00:00Z"),
            "delivery_date": pd.Timestamp("2100-12-25T08:00:00Z"),
            "underlying_type": "COIN",
            "metadata_source": "current_exchangeInfo",
        }
    )
    return bars, funding, marks, membership, metadata


class Tree:
    """A complete working tree with a frozen activation record, plus a quarantine destination."""

    def __init__(self, tmp_path: Path) -> None:
        self.root = tmp_path / "repo"
        self.quarantine = tmp_path / "quarantine"
        data = self.root / "data" / "cup20"
        data.mkdir(parents=True)
        self.is_root = data / "is"
        self.sealed_root = data / "sealed"
        self.acquisition_root = data / "acquisition"
        write_split_snapshots(
            *_panels(),
            is_root=self.is_root,
            sealed_root=self.sealed_root,
            is_end=_CUTOFF,
            sealed_end=_SEALED_END,
        )
        # The acquisition snapshot is the un-truncated superset: it has no manifest of its own,
        # which is exactly why the receipt's bundle digest has to cover it.
        self.acquisition_root.mkdir()
        shutil.copy(self.sealed_root / "bars.parquet", self.acquisition_root / "bars.parquet")
        (self.acquisition_root / "coverage.json").write_text('{"symbols": 2}\n')

        self.config = self.root / "config.toml"
        shutil.copy(REAL_CONFIG, self.config)
        self.charter = self.root / "CHARTER.md"
        self.charter.write_text("# charter\n")
        implementation = self.root / "implementation"
        implementation.mkdir()
        (implementation / "runner.py").write_text("TARGET = 1\n")
        audit = self.root / "audit.json"
        audit.write_text(json.dumps({"status": "PURE_CRYPTO_UNIVERSE_VERIFIED"}) + "\n")
        lock = self.root / "uv.lock"
        lock.write_text("# lock\n")
        tests = self.root / "tests.out"
        tests.write_text("42 passed\n")

        record = build_activation_record(
            self.config,
            self.charter,
            self.is_root,
            self.sealed_root,
            tests,
            lock,
            implementation,
            audit,
        )
        self.tournament = self.root / "tournament" / "cup20"
        self.tournament.mkdir(parents=True)
        self.activation = self.tournament / "activation-freeze.json"
        self.activation.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        self.receipt = self.tournament / "quarantine-receipt.json"
        self.freeze = self.tournament / "selection-freeze.json"
        self.stamp = self.tournament / "quarantine-restore.json"
        self.baseline = self.tournament / "sealed-access-baseline.json"
        self.journal = self.tournament / "research-journal.jsonl"
        self.record = record

    def quarantine_now(self, **overrides):
        kwargs = dict(
            quarantine_root=self.quarantine,
            activation_record=self.activation,
            receipt_path=self.receipt,
            acquisition_root=self.acquisition_root,
            repo_root=self.root,
            token=_TOKEN,
        )
        kwargs.update(overrides)
        return q.quarantine_holdout(**kwargs)

    def close_the_field(self) -> None:
        self.freeze.write_text('{"advancing": ["team-01"]}\n')

    def restore_now(self, **overrides):
        kwargs = dict(
            receipt_path=self.receipt,
            selection_freeze_path=self.freeze,
            restore_stamp_path=self.stamp,
            baseline_path=self.baseline,
        )
        kwargs.update(overrides)
        return q.restore_holdout(**kwargs)


@pytest.fixture
def tree(tmp_path):
    return Tree(tmp_path)


# --- the fixture itself, without which every assertion below is vacuous ------------------------


def test_the_fixture_activates_cleanly_before_anything_is_quarantined(tree):
    assert verify_activation(tree.activation) == tree.record
    assert tree.sealed_root.is_dir()
    assert tree.acquisition_root.is_dir()


# --- quarantine ---------------------------------------------------------------------------------


def test_quarantine_moves_both_trees_out_of_the_working_tree(tree):
    receipt = tree.quarantine_now()
    assert not tree.sealed_root.exists()
    assert not tree.acquisition_root.exists()
    assert (tree.quarantine / "sealed" / "bars.parquet").is_file()
    assert (tree.quarantine / "acquisition" / "coverage.json").is_file()
    assert receipt["sealed_manifest_sha256"] == tree.record["sealed_manifest_sha256"]
    assert json.loads(tree.receipt.read_text()) == receipt


def test_quarantine_leaves_the_in_sample_snapshot_alone(tree):
    # The teams' own data root must survive quarantine untouched, or the research phase cannot run.
    before = bundle_digest(tree.is_root)
    tree.quarantine_now()
    assert tree.is_root.is_dir()
    assert bundle_digest(tree.is_root) == before


def test_planting_the_canary_does_not_move_the_bound_sealed_manifest_digest(tree):
    # The load-bearing assumption behind the whole tripwire: the manifest digest covers the five
    # named parquet files, so a sixth file can be added without invalidating the activation record.
    # If this ever stopped holding, the canary would silently break the tournament.
    tree.quarantine_now()
    quarantined = tree.quarantine / "sealed"
    assert (quarantined / q.CANARY_FILENAME).is_file()
    assert load_snapshot(quarantined).manifest_sha256 == tree.record["sealed_manifest_sha256"]


def test_the_canary_carries_the_token_and_the_token_is_never_written_to_the_receipt(tree):
    receipt = tree.quarantine_now()
    text = (tree.quarantine / "sealed" / q.CANARY_FILENAME).read_text()
    assert _TOKEN in text
    assert _TOKEN not in tree.receipt.read_text()
    assert receipt["canary_token_sha256"] != _TOKEN


def test_the_canary_filename_is_a_forbidden_pattern():
    # Cross-module coupling made self-detecting: the scan cannot catch a copied canary by name
    # unless archive.FORBIDDEN_PATTERNS still matches quarantine.CANARY_FILENAME.
    import re

    assert any(re.search(pattern, q.CANARY_FILENAME) for pattern in FORBIDDEN_PATTERNS)


def test_quarantine_refuses_when_a_receipt_already_exists(tree):
    tree.quarantine_now()
    with pytest.raises(FileExistsError, match="quarantine receipt already exists"):
        tree.quarantine_now()


def test_quarantine_refuses_a_destination_inside_the_working_tree(tree):
    with pytest.raises(ValueError, match="inside the working tree"):
        tree.quarantine_now(quarantine_root=tree.root / "elsewhere")
    assert tree.sealed_root.is_dir()
    assert not tree.receipt.exists()


def test_quarantine_refuses_a_destination_that_is_the_working_tree_itself(tree):
    with pytest.raises(ValueError, match="inside the working tree"):
        tree.quarantine_now(quarantine_root=tree.root)


def test_quarantine_refuses_a_destination_that_is_not_empty(tree):
    tree.quarantine.mkdir()
    (tree.quarantine / "stray.txt").write_text("x\n")
    with pytest.raises(FileExistsError, match="not empty"):
        tree.quarantine_now()
    assert tree.sealed_root.is_dir()


def test_quarantine_refuses_a_tournament_whose_activation_has_already_drifted(tree):
    tree.charter.write_text("# a different charter\n")
    with pytest.raises(ValueError, match="activation authority changed: charter"):
        tree.quarantine_now()
    assert tree.sealed_root.is_dir()


def test_quarantine_refuses_a_missing_acquisition_root(tree):
    shutil.rmtree(tree.acquisition_root)
    with pytest.raises(FileNotFoundError, match="acquisition root"):
        tree.quarantine_now()
    assert tree.sealed_root.is_dir()


def test_quarantine_refuses_a_canary_that_is_already_planted(tree):
    (tree.sealed_root / q.CANARY_FILENAME).write_text("stale\n")
    with pytest.raises(FileExistsError, match="canary is already planted"):
        tree.quarantine_now()


@pytest.mark.parametrize("bad", ["", "short", "NOTHEX" * 8, "a" * 200, "a" * 32 + " b" * 16])
def test_quarantine_refuses_a_token_that_is_not_high_entropy_hex(tree, bad):
    with pytest.raises(ValueError, match="canary token must be"):
        tree.quarantine_now(token=bad)
    assert not (tree.sealed_root / q.CANARY_FILENAME).exists()


def test_quarantine_generates_its_own_token_when_none_is_given(tree):
    receipt = tree.quarantine_now(token=None)
    token = q.read_canary_token(receipt_path=tree.receipt)
    assert len(token) == 64
    assert token in (tree.quarantine / "sealed" / q.CANARY_FILENAME).read_text()
    assert receipt["canary_token_sha256"] == q._digest_bytes(token.encode("utf-8"))


# --- verify_quarantine_in_effect ----------------------------------------------------------------


def test_verify_quarantine_in_effect_passes_while_the_trees_are_away(tree):
    tree.quarantine_now()
    assert q.verify_quarantine_in_effect(receipt_path=tree.receipt)["quarantine_root"] == str(
        tree.quarantine.resolve()
    )


def test_verify_quarantine_in_effect_raises_when_a_tree_reappears(tree):
    tree.quarantine_now()
    tree.sealed_root.mkdir(parents=True)
    with pytest.raises(ValueError, match="quarantine is NOT in effect"):
        q.verify_quarantine_in_effect(receipt_path=tree.receipt)


def test_verify_quarantine_in_effect_raises_when_the_quarantined_tree_vanished(tree):
    tree.quarantine_now()
    shutil.rmtree(tree.quarantine / "acquisition")
    with pytest.raises(ValueError, match="not verifiable"):
        q.verify_quarantine_in_effect(receipt_path=tree.receipt)


# --- verify_quarantine_integrity ------------------------------------------------------------------
#
# The defect this section exists for: the integrity review told the organiser that the live
# quarantine check "verifies the same digest at the quarantine location". It did not -- it checked
# only that the trees were absent from the working tree, so a byte appended to a quarantined file
# passed silently. Every case below therefore pairs the tamper with an assertion about which layer
# catches it, and the first one asserts explicitly that the absence-only check does NOT.


def _tampered_sealed_bar(tree) -> Path:
    """Append one null byte to a quarantined sealed file -- the reported failure, verbatim."""
    target = tree.quarantine / "sealed" / "bars.parquet"
    target.write_bytes(target.read_bytes() + b"\x00")
    return target


def test_integrity_verify_passes_on_an_untouched_quarantine(tree):
    # Paired with every tamper case below; on its own an exit-0 proves nothing at all.
    receipt = tree.quarantine_now()
    report = q.verify_quarantine_integrity(receipt_path=tree.receipt)
    assert report["bundle_sha256"] == {
        name: entry["bundle_sha256"] for name, entry in receipt["trees"].items()
    }
    assert report["sealed_manifest_sha256"] == tree.record["sealed_manifest_sha256"]
    assert report["canary_token_length"] == len(_TOKEN)


def test_integrity_verify_catches_a_byte_appended_to_a_quarantined_sealed_file(tree):
    # The mutation: a `verify` that tests absence and calls it integrity. The absence-only check is
    # asserted to pass here, so this test fails the moment the two are conflated again.
    tree.quarantine_now()
    _tampered_sealed_bar(tree)

    assert q.verify_quarantine_in_effect(receipt_path=tree.receipt)["quarantine_root"]

    with pytest.raises(ValueError, match="QUARANTINE INTEGRITY FAILURE: the quarantined sealed"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_a_modified_acquisition_file(tree):
    # The mutation: checking the sealed snapshot's manifest and stopping there. The acquisition
    # tree has no manifest at all, so only the receipt's bundle digest can see this.
    tree.quarantine_now()
    (tree.quarantine / "acquisition" / "coverage.json").write_text('{"symbols": 3}\n')
    with pytest.raises(
        ValueError, match="QUARANTINE INTEGRITY FAILURE: the quarantined acquisition"
    ):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_a_file_added_to_the_quarantined_sealed_tree(tree):
    # The mutation: verifying load_snapshot's manifest digest instead of the whole-tree bundle. The
    # manifest covers five named parquet files and is blind to a sixth.
    tree.quarantine_now()
    (tree.quarantine / "sealed" / "extra.parquet").write_bytes(b"\x00\x01")
    assert (
        load_snapshot(tree.quarantine / "sealed").manifest_sha256
        == tree.record["sealed_manifest_sha256"]
    )
    with pytest.raises(ValueError, match="QUARANTINE INTEGRITY FAILURE"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_the_canary_deleted_from_the_quarantined_sealed_tree(tree):
    # Same mutation, removal direction -- and the load_snapshot assertion proves the manifest layer
    # genuinely cannot see it, so this case is carried by the bundle digest alone.
    tree.quarantine_now()
    (tree.quarantine / "sealed" / q.CANARY_FILENAME).unlink()
    assert (
        load_snapshot(tree.quarantine / "sealed").manifest_sha256
        == tree.record["sealed_manifest_sha256"]
    )
    with pytest.raises(ValueError, match="QUARANTINE INTEGRITY FAILURE"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_a_tree_that_came_back_into_the_working_tree(tree):
    # The mutation: dropping the absence layer once the digest layers were added. A pristine copy in
    # quarantine hashes clean while a second copy sits back in every team's reach.
    tree.quarantine_now()
    shutil.copytree(tree.quarantine / "sealed", tree.sealed_root)
    with pytest.raises(ValueError, match="quarantine is NOT in effect"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_a_quarantined_tree_that_vanished(tree):
    # The mutation: treating a missing tree as nothing to compare and passing -- a fail-open that
    # would report the strongest possible verdict over an empty directory.
    tree.quarantine_now()
    shutil.rmtree(tree.quarantine / "acquisition")
    with pytest.raises(ValueError, match="not verifiable"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_an_emptied_quarantined_tree(tree):
    # A directory that still exists but holds nothing: the absence layer is satisfied, so only the
    # bundle digest stands between an empty tree and a clean verdict.
    tree.quarantine_now()
    for path in (tree.quarantine / "acquisition").iterdir():
        path.unlink()
    with pytest.raises(ValueError, match="QUARANTINE INTEGRITY FAILURE"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_an_authority_that_drifted_while_the_holdout_was_away(tree):
    # The mutation: comparing bundle digests only. The charter is in NEITHER tree, so no digest in
    # the receipt covers it -- only re-verifying the whole activation record does.
    tree.quarantine_now()
    tree.charter.write_text("# rewritten while the holdout was away\n")
    with pytest.raises(ValueError, match="activation authority changed: charter"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_a_swapped_sealed_snapshot_at_the_quarantine_location(tree):
    # The layer the review's check 1 provides and the receipt cannot: the sealed manifest is
    # compared against the value activation bound before any team started. Rewriting the receipt to
    # match a swapped tree does not help, because the record is the authority here.
    tree.quarantine_now()
    target = tree.quarantine / "sealed" / "bars.parquet"
    target.write_bytes(target.read_bytes() + b"\x00")
    payload = json.loads(tree.receipt.read_text())
    payload["trees"]["sealed"]["bundle_sha256"] = bundle_digest(tree.quarantine / "sealed")
    tree.receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="sealed snapshot at .* does not match its own manifest"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_a_receipt_that_names_a_different_sealed_manifest(tree):
    # The mutation: trusting the receipt's own claim about which holdout it describes. Both bundle
    # digests still match and the activation record still verifies, so only the cross-comparison
    # between the two artifacts can fire.
    tree.quarantine_now()
    payload = json.loads(tree.receipt.read_text())
    payload["sealed_manifest_sha256"] = "0" * 64
    tree.receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="two different holdouts"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_an_edited_canary_token_file(tree):
    # The mutation: relying on the two bundle digests. The token file sits at the quarantine ROOT,
    # inside neither tree, so both digests still match -- asserted here -- while the review would go
    # on to scan every team workspace for a string that was never planted.
    receipt = tree.quarantine_now()
    (tree.quarantine / q.CANARY_TOKEN_FILENAME).write_text("b" * 64 + "\n")
    for name, entry in receipt["trees"].items():
        assert bundle_digest(entry["quarantine_path"]) == entry["bundle_sha256"], name
    with pytest.raises(ValueError, match="does not match the receipt"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_catches_a_deleted_canary_token_file(tree):
    tree.quarantine_now()
    (tree.quarantine / q.CANARY_TOKEN_FILENAME).unlink()
    with pytest.raises(FileNotFoundError):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)


def test_integrity_verify_reads_but_never_writes(tree):
    # The mutation: an implementation that "repairs" a mismatch, or that moves a tree while
    # checking it. Both the clean and the failing path must leave every byte and every path alone.
    receipt = tree.quarantine_now()
    before = {name: bundle_digest(e["quarantine_path"]) for name, e in receipt["trees"].items()}
    q.verify_quarantine_integrity(receipt_path=tree.receipt)
    _tampered_sealed_bar(tree)
    tampered = bundle_digest(tree.quarantine / "sealed")
    with pytest.raises(ValueError, match="QUARANTINE INTEGRITY FAILURE"):
        q.verify_quarantine_integrity(receipt_path=tree.receipt)
    assert bundle_digest(tree.quarantine / "acquisition") == before["acquisition"]
    assert bundle_digest(tree.quarantine / "sealed") == tampered
    assert not tree.sealed_root.exists()
    assert not tree.acquisition_root.exists()


def test_the_fast_disclaimer_names_what_the_absence_check_cannot_see():
    # Not a wording test: the --fast branch is the one path that still reports a clean quarantine
    # without reading a byte, and the sentence shown next to that result is the only thing standing
    # between it and the exact misreading this section was written to fix.
    text = q.FAST_VERIFY_DISCLAIMER.lower()
    assert "not checked" in text
    assert "--fast" in text
    for missed in ("modified", "deleted", "canary token"):
        assert missed in text, missed


# --- the command an organiser actually types ------------------------------------------------------
#
# The library function being right is not the fix. The integrity review names a COMMAND, and the
# defect was that the command ran the weaker function. These drive scripts/cup20_quarantine.py so a
# future change of default is caught here rather than by someone reading the runbook in month four.


def _cli():
    import importlib.util

    path = REPO_ROOT / "scripts" / "cup20_quarantine.py"
    spec = importlib.util.spec_from_file_location("cup20_quarantine_cli", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_cli(module, tree, monkeypatch, *argv):
    monkeypatch.setattr(
        module,
        "_paths",
        lambda: {
            "activation": str(tree.activation),
            "journal": str(tree.journal),
            "selection_freeze": str(tree.freeze),
            "sealed_root": str(tree.sealed_root),
            "receipt": str(tree.receipt),
            "restore_stamp": str(tree.stamp),
            "baseline": str(tree.baseline),
        },
    )
    monkeypatch.setattr("sys.argv", ["cup20_quarantine.py", *argv])
    module.main()


def test_the_verify_command_reads_the_quarantined_bytes_by_default(tree, monkeypatch, capsys):
    receipt = tree.quarantine_now()
    _run_cli(_cli(), tree, monkeypatch, "verify")
    out = capsys.readouterr().out
    assert "quarantine VERIFIED" in out
    for entry in receipt["trees"].values():
        assert entry["bundle_sha256"] in out
    assert tree.record["sealed_manifest_sha256"] in out


def test_the_verify_command_fails_loudly_on_a_tampered_quarantine(tree, monkeypatch):
    # The exact reported failure, driven through the command the runbook names: one null byte
    # appended to a quarantined sealed file used to leave `verify` printing success and exiting 0.
    tree.quarantine_now()
    _tampered_sealed_bar(tree)
    with pytest.raises(ValueError, match="QUARANTINE INTEGRITY FAILURE"):
        _run_cli(_cli(), tree, monkeypatch, "verify")


def test_the_fast_flag_passes_on_a_tampered_quarantine_and_says_it_did_not_look(
    tree, monkeypatch, capsys
):
    # --fast keeps the old behaviour on purpose, so this asserts the honest half: it still reports
    # the tampered quarantine as "in effect", and the disclaimer that this proves nothing about the
    # bytes is printed with it. Remove the disclaimer and this test fails.
    tree.quarantine_now()
    _tampered_sealed_bar(tree)
    _run_cli(_cli(), tree, monkeypatch, "verify", "--fast")
    out = capsys.readouterr().out
    assert "quarantine IS in effect" in out
    assert q.FAST_VERIFY_DISCLAIMER in out
    assert "VERIFIED" not in out


# --- the receipt's own shape --------------------------------------------------------------------


def test_load_receipt_rejects_a_json_array(tree, tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text("[]\n")
    with pytest.raises(ValueError, match="must be a JSON object"):
        q.load_receipt(path)


def test_load_receipt_rejects_an_unknown_schema_version(tree):
    tree.quarantine_now()
    payload = json.loads(tree.receipt.read_text())
    payload["schema_version"] = "cup20-quarantine-receipt-v99"
    tree.receipt.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="schema_version"):
        q.load_receipt(tree.receipt)


def test_load_receipt_rejects_a_receipt_that_forgets_a_tree(tree):
    tree.quarantine_now()
    payload = json.loads(tree.receipt.read_text())
    del payload["trees"]["acquisition"]
    tree.receipt.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="exactly the trees"):
        q.load_receipt(tree.receipt)


def test_load_receipt_rejects_a_tree_entry_that_is_not_an_object(tree):
    tree.quarantine_now()
    payload = json.loads(tree.receipt.read_text())
    payload["trees"]["sealed"] = "somewhere"
    tree.receipt.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="tree sealed is not an object"):
        q.load_receipt(tree.receipt)


def test_load_receipt_rejects_a_tree_entry_missing_its_digest(tree):
    tree.quarantine_now()
    payload = json.loads(tree.receipt.read_text())
    del payload["trees"]["sealed"]["bundle_sha256"]
    tree.receipt.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="missing bundle_sha256"):
        q.load_receipt(tree.receipt)


@pytest.mark.parametrize(
    "field",
    [
        "quarantine_root",
        "activation_record_path",
        "sealed_manifest_sha256",
        "canary_relative_path",
        "canary_file_sha256",
        "canary_token_sha256",
    ],
)
def test_load_receipt_rejects_a_missing_top_level_field(tree, field):
    tree.quarantine_now()
    payload = json.loads(tree.receipt.read_text())
    del payload[field]
    tree.receipt.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match=f"missing {field}"):
        q.load_receipt(tree.receipt)


# --- restore ------------------------------------------------------------------------------------


def test_restore_round_trips_both_trees_and_re_verifies_activation(tree):
    receipt = tree.quarantine_now()
    tree.close_the_field()
    stamp = tree.restore_now()
    assert tree.sealed_root.is_dir()
    assert tree.acquisition_root.is_dir()
    assert not (tree.quarantine / "sealed").exists()
    for name, entry in receipt["trees"].items():
        assert bundle_digest(entry["working_path"]) == entry["bundle_sha256"], name
    assert verify_activation(tree.activation) == tree.record
    assert json.loads(tree.stamp.read_text()) == stamp
    assert tree.baseline.is_file()
    assert (tree.sealed_root / q.CANARY_FILENAME).is_file()


def test_restore_refuses_a_modified_sealed_file(tree):
    """The single most important assertion here: a tampered holdout does not come back."""
    tree.quarantine_now()
    tree.close_the_field()
    target = tree.quarantine / "sealed" / "bars.parquet"
    payload = bytearray(target.read_bytes())
    payload[len(payload) // 2] ^= 0xFF
    target.write_bytes(bytes(payload))

    with pytest.raises(ValueError, match="REFUSING TO RESTORE: the quarantined sealed tree"):
        tree.restore_now()
    # Nothing moved -- the tampered tree never entered the working tree at all.
    assert not tree.sealed_root.exists()
    assert not tree.acquisition_root.exists()
    assert not tree.stamp.exists()


def test_restore_refuses_a_modified_acquisition_file(tree):
    # The acquisition tree has NO manifest, so the only thing that can catch this is the receipt's
    # bundle digest. A restore that verified the sealed manifest alone would pass.
    tree.quarantine_now()
    tree.close_the_field()
    (tree.quarantine / "acquisition" / "coverage.json").write_text('{"symbols": 3}\n')
    with pytest.raises(ValueError, match="quarantined acquisition tree"):
        tree.restore_now()
    assert not tree.acquisition_root.exists()


def test_restore_refuses_a_sealed_tree_with_the_canary_deleted(tree):
    # A file REMOVED from the tree leaves all five manifest-declared parquet files intact, so the
    # snapshot's own manifest still verifies. Only the whole-tree bundle digest sees it.
    tree.quarantine_now()
    tree.close_the_field()
    (tree.quarantine / "sealed" / q.CANARY_FILENAME).unlink()
    assert (
        load_snapshot(tree.quarantine / "sealed").manifest_sha256
        == (tree.record["sealed_manifest_sha256"])
    )
    with pytest.raises(ValueError, match="REFUSING TO RESTORE"):
        tree.restore_now()


def test_restore_refuses_a_sealed_tree_with_a_file_added(tree):
    tree.quarantine_now()
    tree.close_the_field()
    (tree.quarantine / "sealed" / "extra.parquet").write_bytes(b"\x00\x01")
    with pytest.raises(ValueError, match="REFUSING TO RESTORE"):
        tree.restore_now()


def test_restore_refuses_when_the_selection_freeze_does_not_exist(tree):
    tree.quarantine_now()
    with pytest.raises(FileNotFoundError, match="the field is not closed"):
        tree.restore_now()
    assert not tree.sealed_root.exists()


def test_restore_refuses_when_a_restore_stamp_already_exists(tree):
    tree.quarantine_now()
    tree.close_the_field()
    tree.restore_now()
    with pytest.raises(FileExistsError, match="already been restored"):
        tree.restore_now()


def test_restore_refuses_when_the_working_tree_already_holds_a_tree(tree):
    tree.quarantine_now()
    tree.close_the_field()
    tree.sealed_root.mkdir(parents=True)
    with pytest.raises(FileExistsError, match="already present"):
        tree.restore_now()


def test_restore_refuses_when_a_quarantined_tree_is_absent(tree):
    tree.quarantine_now()
    tree.close_the_field()
    shutil.rmtree(tree.quarantine / "sealed")
    with pytest.raises(FileNotFoundError, match="quarantined sealed tree"):
        tree.restore_now()
    assert not tree.acquisition_root.exists()


def test_restore_refuses_when_another_authority_drifted_while_quarantined(tree):
    # Independent of the bundle digests: the charter is in neither tree, so only the second layer
    # -- verify_activation against the quarantined sealed root -- can catch this.
    tree.quarantine_now()
    tree.close_the_field()
    tree.charter.write_text("# rewritten while the holdout was away\n")
    with pytest.raises(ValueError, match="activation authority changed: charter"):
        tree.restore_now()
    assert not tree.sealed_root.exists()


def test_restore_refuses_a_canary_whose_contents_were_edited_in_place(tree):
    tree.quarantine_now()
    tree.close_the_field()
    canary = tree.quarantine / "sealed" / q.CANARY_FILENAME
    canary.write_text(q.canary_contents("b" * 64))
    with pytest.raises(ValueError, match="REFUSING TO RESTORE"):
        tree.restore_now()


# --- reading the token back ---------------------------------------------------------------------


def test_read_canary_token_returns_the_planted_token(tree):
    tree.quarantine_now()
    assert q.read_canary_token(receipt_path=tree.receipt) == _TOKEN


def test_read_canary_token_refuses_a_token_that_does_not_match_the_receipt(tree):
    tree.quarantine_now()
    (tree.quarantine / q.CANARY_TOKEN_FILENAME).write_text("b" * 64 + "\n")
    with pytest.raises(ValueError, match="does not match the receipt"):
        q.read_canary_token(receipt_path=tree.receipt)


# --- the journal is what proves quarantine covered the research phase ----------------------------


def _journal(tree, *, quarantine_first=True, restore=True, trials=3):
    receipt = tree.quarantine_now(journal_path=tree.journal if quarantine_first else None)
    if not quarantine_first:
        for index in range(trials):
            append_record(tree.journal, "trial_accepted", {"team_id": f"team-0{index + 1}"})
        append_record(
            tree.journal,
            q.QUARANTINE_EVENT,
            {"canary_token_sha256": receipt["canary_token_sha256"]},
        )
        return receipt
    for index in range(trials):
        append_record(tree.journal, "trial_accepted", {"team_id": f"team-0{index + 1}"})
    if restore:
        tree.close_the_field()
        tree.restore_now(journal_path=tree.journal)
    return receipt


def test_the_journal_proves_quarantine_bracketed_every_accepted_trial(tree):
    _journal(tree)
    report = q.verify_quarantine_covered_research(
        journal_path=tree.journal, receipt_path=tree.receipt
    )
    assert report["quarantine_sequence"] == 1
    assert report["first_trial_sequence"] == 2
    assert report["last_trial_sequence"] == 4
    assert report["restore_sequence"] == 5
    assert report["trials_covered"] == 3


def test_a_restore_that_never_happened_is_allowed_mid_tournament(tree):
    _journal(tree, restore=False)
    report = q.verify_quarantine_covered_research(
        journal_path=tree.journal, receipt_path=tree.receipt
    )
    assert report["restore_sequence"] is None


def test_quarantine_after_the_first_trial_is_caught(tree):
    _journal(tree, quarantine_first=False)
    with pytest.raises(ValueError, match="after the first accepted trial"):
        q.verify_quarantine_covered_research(journal_path=tree.journal, receipt_path=tree.receipt)


def test_a_restore_before_the_last_trial_is_caught(tree):
    tree.quarantine_now(journal_path=tree.journal)
    append_record(tree.journal, "trial_accepted", {"team_id": "team-01"})
    tree.close_the_field()
    tree.restore_now(journal_path=tree.journal)
    append_record(tree.journal, "trial_accepted", {"team_id": "team-02"})
    with pytest.raises(ValueError, match="before the last accepted trial"):
        q.verify_quarantine_covered_research(journal_path=tree.journal, receipt_path=tree.receipt)


def test_a_journal_with_no_quarantine_event_is_caught(tree):
    tree.quarantine_now()
    append_record(tree.journal, "trial_accepted", {"team_id": "team-01"})
    with pytest.raises(ValueError, match="exactly one holdout_quarantined"):
        q.verify_quarantine_covered_research(journal_path=tree.journal, receipt_path=tree.receipt)


def test_two_quarantine_events_are_caught(tree):
    _journal(tree, restore=False)
    append_record(tree.journal, q.QUARANTINE_EVENT, {"canary_token_sha256": "x"})
    with pytest.raises(ValueError, match="exactly one holdout_quarantined"):
        q.verify_quarantine_covered_research(journal_path=tree.journal, receipt_path=tree.receipt)


def test_two_restore_events_are_caught(tree):
    _journal(tree)
    append_record(tree.journal, q.RESTORE_EVENT, {})
    with pytest.raises(ValueError, match="at most one holdout_restored"):
        q.verify_quarantine_covered_research(journal_path=tree.journal, receipt_path=tree.receipt)


def test_a_journal_with_no_accepted_trials_is_refused_rather_than_passing_vacuously(tree):
    tree.quarantine_now(journal_path=tree.journal)
    with pytest.raises(ValueError, match="records no trial_accepted"):
        q.verify_quarantine_covered_research(journal_path=tree.journal, receipt_path=tree.receipt)


def test_a_journal_describing_a_different_canary_is_caught(tree):
    # Ordered correctly, so the sequence checks all pass and only the token comparison can fail:
    # this is the case where the receipt in the repository and the event in the chain describe two
    # different quarantines.
    tree.quarantine_now()
    append_record(tree.journal, q.QUARANTINE_EVENT, {"canary_token_sha256": "f" * 64})
    append_record(tree.journal, "trial_accepted", {"team_id": "team-01"})
    with pytest.raises(ValueError, match="different canary tokens"):
        q.verify_quarantine_covered_research(journal_path=tree.journal, receipt_path=tree.receipt)


def test_a_broken_chain_is_caught_before_any_ordering_question(tree):
    _journal(tree)
    lines = tree.journal.read_text().splitlines()
    tree.journal.write_text("\n".join(lines[:1] + lines[2:]) + "\n")
    with pytest.raises(ValueError, match="journal sequence break"):
        q.verify_quarantine_covered_research(journal_path=tree.journal, receipt_path=tree.receipt)


# --- the access-time tripwire --------------------------------------------------------------------


def _restored(tree):
    tree.quarantine_now()
    tree.close_the_field()
    tree.restore_now()
    return tree


def test_arming_back_dates_every_sealed_file_far_enough_for_relatime(tree):
    _restored(tree)
    baseline = json.loads(tree.baseline.read_text())
    for name, armed in baseline["files"].items():
        stat = (tree.sealed_root / name).stat()
        assert stat.st_atime_ns == armed, name
        # Older than the kernel's 24-hour relatime threshold, or the next read is not recorded.
        assert baseline["armed_at_epoch"] - armed / 1e9 > 24 * 3600


def test_arming_does_not_disturb_modification_times_or_contents(tree):
    tree.quarantine_now()
    tree.close_the_field()
    before = {
        path.name: (path.stat().st_mtime_ns, path.read_bytes())
        for path in (tree.quarantine / "sealed").iterdir()
    }
    tree.restore_now()
    for path in tree.sealed_root.iterdir():
        mtime, payload = before[path.name]
        assert path.stat().st_mtime_ns == mtime, path.name
        assert path.read_bytes() == payload, path.name


def test_reading_an_armed_sealed_file_is_reported_as_access(tree):
    _restored(tree)
    (tree.sealed_root / "bars.parquet").read_bytes()
    report = q.sealed_access_report(tree.sealed_root, baseline_path=tree.baseline)
    if not report["atime_is_recorded"]:  # pragma: no cover - depends on the mount
        pytest.skip("this filesystem is mounted noatime; the tripwire is inert here")
    assert "bars.parquet" in report["accessed"]
    assert "membership.parquet" not in report["accessed"]


def test_an_untouched_sealed_tree_reports_no_access(tree):
    _restored(tree)
    report = q.sealed_access_report(tree.sealed_root, baseline_path=tree.baseline)
    assert report["accessed"] == []
    assert report["appeared"] == []
    assert report["vanished"] == []


def test_a_noatime_mount_is_reported_as_inert_rather_than_clean(tmp_path, tree):
    # The mutation this catches: reporting `accessed: []` on a mount where the kernel never records
    # an access at all, which reads as "nobody touched the holdout" and means nothing of the sort.
    _restored(tree)
    mounts = tmp_path / "mounts"
    mounts.write_text(f"/dev/sda1 {tree.root} ext4 rw,noatime 0 0\n")
    report = q.sealed_access_report(
        tree.sealed_root, baseline_path=tree.baseline, mounts_path=mounts
    )
    assert report["atime_is_recorded"] is False
    assert report["mount_options"] == ["rw", "noatime"]


def test_the_deepest_matching_mount_point_wins(tmp_path, tree):
    mounts = tmp_path / "mounts"
    mounts.write_text(
        f"/dev/sda1 / ext4 rw,relatime 0 0\n/dev/sdb1 {tree.root} ext4 rw,noatime 0 0\n"
    )
    assert q.mount_options(tree.sealed_root, mounts_path=mounts) == ("rw", "noatime")


def test_unknown_mount_options_are_empty_rather_than_guessed(tmp_path):
    assert q.mount_options(tmp_path, mounts_path=tmp_path / "absent") == ()


def test_a_file_added_to_the_sealed_tree_after_arming_is_reported_separately(tree):
    _restored(tree)
    (tree.sealed_root / "planted.txt").write_text("x\n")
    report = q.sealed_access_report(tree.sealed_root, baseline_path=tree.baseline)
    assert report["appeared"] == ["planted.txt"]
    assert report["vanished"] == []


def test_a_file_removed_from_the_sealed_tree_after_arming_is_reported_separately(tree):
    _restored(tree)
    (tree.sealed_root / q.CANARY_FILENAME).unlink()
    report = q.sealed_access_report(tree.sealed_root, baseline_path=tree.baseline)
    assert report["vanished"] == [q.CANARY_FILENAME]


def test_the_access_report_refuses_a_baseline_of_the_wrong_schema(tree, tmp_path):
    _restored(tree)
    bad = tmp_path / "baseline.json"
    bad.write_text(json.dumps({"schema_version": "v0", "files": {}}) + "\n")
    with pytest.raises(ValueError, match="schema_version"):
        q.sealed_access_report(tree.sealed_root, baseline_path=bad)


def test_the_access_report_refuses_a_baseline_with_no_files_table(tree, tmp_path):
    # Right schema version, nothing to compare against: reporting `accessed: []` off this would be
    # a clean-looking verdict computed from an empty baseline.
    _restored(tree)
    bad = tmp_path / "baseline.json"
    bad.write_text(json.dumps({"schema_version": q.BASELINE_SCHEMA_VERSION}) + "\n")
    with pytest.raises(ValueError, match="missing its files table"):
        q.sealed_access_report(tree.sealed_root, baseline_path=bad)


def test_the_access_report_refuses_a_baseline_with_no_armed_timestamp(tree, tmp_path):
    _restored(tree)
    bad = tmp_path / "baseline.json"
    bad.write_text(json.dumps({"schema_version": q.BASELINE_SCHEMA_VERSION, "files": {}}) + "\n")
    with pytest.raises(ValueError, match="armed_at_epoch"):
        q.sealed_access_report(tree.sealed_root, baseline_path=bad)


def test_arming_refuses_a_sealed_root_that_is_not_there(tmp_path):
    with pytest.raises(FileNotFoundError, match="sealed root"):
        q.arm_sealed_access_tripwire(tmp_path / "absent", baseline_path=tmp_path / "b.json")
