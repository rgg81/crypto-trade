"""The activation freeze is the tournament's root of trust -- test it like one.

Every authority bound by the record must be provably capable of detecting its own change, and the
snapshot bindings must detect a data swap that leaves the snapshot's own manifest untouched. A
freeze that only re-reads a manifest's self-declared digest would notarise nothing.
"""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.cup20.activation import build_activation_record, verify_activation
from crypto_trade.cup20.snapshot import write_split_snapshots

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_CONFIG = REPO_ROOT / "tournament" / "cup20" / "config.toml"

# Every authority the record binds, paired with the substring ``verify_activation`` must name when
# that authority changes, and a callable that makes a MATERIAL change to it on disk. Driving the
# detection test from this table (rather than hand-writing one case) is the point: adding a new
# authority to ``activation.py`` without adding it here leaves the coverage assertion below
# failing, so an unverified binding cannot be introduced silently.
_CUTOFF = pd.Timestamp("2021-06-01T00:00:00Z")
_SEALED_END = pd.Timestamp("2022-01-01T00:00:00Z")


def _panels(symbols=("AUSDT", "BUSDT"), seed=11):
    """Small but structurally real snapshot panels spanning both sides of the cutoff."""
    times = pd.date_range("2021-01-01T00:00:00Z", periods=1200, freq="8h")
    rng = np.random.default_rng(seed)
    bar_frames = []
    prices: dict[str, np.ndarray] = {}
    for symbol in symbols:
        price = 100.0 * np.cumprod(1.0 + rng.normal(0.0002, 0.01, len(times)))
        prices[symbol] = price
        bar_frames.append(
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
    bars = pd.concat(bar_frames, ignore_index=True)
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


def _fixture(tmp_path):
    """A complete, genuinely valid set of authorities: the real CUP-20 machine contract, a charter,
    two real on-disk snapshots written by ``write_split_snapshots``, an implementation tree, a
    pure-crypto audit report, a lock file and a test log.
    """
    config = tmp_path / "config.toml"
    shutil.copy(REAL_CONFIG, config)
    charter = tmp_path / "CHARTER.md"
    charter.write_text("# charter\n")
    is_root = tmp_path / "is"
    sealed_root = tmp_path / "sealed"
    write_split_snapshots(
        *_panels(),
        is_root=is_root,
        sealed_root=sealed_root,
        is_end=_CUTOFF,
        sealed_end=_SEALED_END,
    )
    implementation = tmp_path / "implementation"
    implementation.mkdir(exist_ok=True)
    (implementation / "runner.py").write_text("TARGET = 1\n")
    audit = tmp_path / "pure-crypto-audit.json"
    audit.write_text(json.dumps({"status": "PURE_CRYPTO_UNIVERSE_VERIFIED"}, indent=2) + "\n")
    lock = tmp_path / "uv.lock"
    lock.write_text("# lock\n")
    tests = tmp_path / "tests.out"
    tests.write_text("42 passed\n")
    return config, charter, is_root, sealed_root, tests, lock, implementation, audit


def _build(tmp_path):
    return build_activation_record(*_fixture(tmp_path))


def _freeze(tmp_path):
    """Build the record and write it where ``verify_activation`` will read it."""
    record = _build(tmp_path)
    path = tmp_path / "activation-freeze.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record, path


_AUTHORITY_KEYS = (
    "config_sha256",
    "charter_sha256",
    "implementation_sha256",
    "is_manifest_sha256",
    "sealed_manifest_sha256",
    "pure_crypto_audit_sha256",
    "dependency_lock_sha256",
    "test_output_sha256",
)


def _mutate_config(tmp_path):
    """A real, semantically valid edit: flip a free parameter the frozen contract does not pin."""
    path = tmp_path / "config.toml"
    path.write_text(
        path.read_text().replace("bootstrap_samples = 2000", "bootstrap_samples = 4000")
    )


def _mutate_charter(tmp_path):
    (tmp_path / "CHARTER.md").write_text("# charter changed\n")


def _mutate_lock(tmp_path):
    (tmp_path / "uv.lock").write_text("# lock changed\n")


def _mutate_tests(tmp_path):
    (tmp_path / "tests.out").write_text("41 passed, 1 failed\n")


def _mutate_implementation(tmp_path):
    (tmp_path / "implementation" / "runner.py").write_text("TARGET = 2\n")


def _mutate_audit(tmp_path):
    (tmp_path / "pure-crypto-audit.json").write_text(json.dumps({"status": "changed"}) + "\n")


def _reissue_snapshot(root: Path, seed: int) -> None:
    """Rewrite a snapshot root end-to-end -- new bars AND a correspondingly new manifest.

    The honest form of a data swap: an organiser who rebuilt the snapshot after activation would
    produce exactly this, with a self-consistent manifest. Detection therefore cannot come from
    internal consistency; it has to come from the frozen record.
    """
    scratch = root.parent / f"{root.name}-scratch"
    write_split_snapshots(
        *_panels(seed=seed),
        is_root=scratch / "is",
        sealed_root=scratch / "sealed",
        is_end=_CUTOFF,
        sealed_end=_SEALED_END,
    )
    source = scratch / ("is" if root.name == "is" else "sealed")
    for item in source.iterdir():
        shutil.copy(item, root / item.name)
    shutil.rmtree(scratch)


def _mutate_is_snapshot(tmp_path):
    _reissue_snapshot(tmp_path / "is", seed=77)


def _mutate_sealed_snapshot(tmp_path):
    _reissue_snapshot(tmp_path / "sealed", seed=78)


# (authority key, message substring, mutation) -- one row per bound authority.
_MUTATIONS = (
    ("config_sha256", "config", _mutate_config),
    ("charter_sha256", "charter", _mutate_charter),
    ("implementation_sha256", "implementation", _mutate_implementation),
    ("dependency_lock_sha256", "dependency lock", _mutate_lock),
    ("test_output_sha256", "test output", _mutate_tests),
    ("pure_crypto_audit_sha256", "pure-crypto audit", _mutate_audit),
    ("is_manifest_sha256", "IS snapshot", _mutate_is_snapshot),
    ("sealed_manifest_sha256", "sealed snapshot", _mutate_sealed_snapshot),
)


def test_activation_record_binds_every_authority(tmp_path):
    record = _build(tmp_path)
    for key in _AUTHORITY_KEYS:
        assert len(record[key]) == 64, key
        assert set(record[key]) <= set("0123456789abcdef"), key


def test_every_bound_authority_has_a_detection_case():
    """The table above must cover the module's own authority list exactly.

    Without this, adding a seventh authority to ``activation.py`` would silently ship untested:
    the parametrised detection test only exercises rows that exist here.
    """
    assert {key for key, _, _ in _MUTATIONS} == set(_AUTHORITY_KEYS)


def test_the_two_snapshot_digests_are_not_the_same_value(tmp_path):
    """Guards the detection test below against a vacuous pass: if the IS and sealed snapshots
    happened to hash identically, mutating one would appear to mutate both and the per-authority
    attribution assertions would prove nothing.
    """
    record = _build(tmp_path)
    assert record["is_manifest_sha256"] != record["sealed_manifest_sha256"]


def test_is_and_sealed_manifests_must_differ(tmp_path):
    """A single snapshot pointed at twice is not a split -- it is the sealed window handed to the
    teams, or the IS window handed to the holdout. Either way the tournament is void, so the record
    refuses to be built rather than notarising it.
    """
    authorities = _fixture(tmp_path)
    is_root, sealed_root = authorities[2], authorities[3]
    for item in is_root.iterdir():
        shutil.copy(item, sealed_root / item.name)
    with pytest.raises(ValueError, match="distinct"):
        build_activation_record(*authorities)


def test_verify_activation_round_trips_an_untouched_freeze(tmp_path):
    record, path = _freeze(tmp_path)
    assert verify_activation(path) == record


def test_build_activation_record_is_deterministic(tmp_path):
    """Two builds over identical inputs must be byte-identical -- the record is a freeze, so it
    must not carry a timestamp or any other value that drifts between runs.
    """
    assert _build(tmp_path) == _build(tmp_path)


@pytest.mark.parametrize(
    ("key", "message", "mutate"), _MUTATIONS, ids=[key for key, _, _ in _MUTATIONS]
)
def test_verify_activation_detects_a_changed_authority(tmp_path, key, message, mutate):
    record, path = _freeze(tmp_path)
    mutate(tmp_path)
    with pytest.raises(ValueError, match=message) as error:
        verify_activation(path)
    # Attribution, not just detection: the raised message must name the authority that actually
    # changed, so an operator is not left bisecting six files by hand.
    for other_key, other_message, _ in _MUTATIONS:
        if other_key != key:
            assert other_message not in str(error.value), (
                f"changing {key} was reported as {other_message}"
            )


def test_verify_activation_detects_snapshot_data_swapped_under_a_stale_manifest(tmp_path):
    """The fail-open this module exists to close.

    ``manifest.json`` carries the snapshot's own claim about its contents. Binding that claim alone
    notarises a promise, not the data: replacing ``bars.parquet`` while leaving ``manifest.json``
    untouched leaves the claim -- and therefore any digest-of-the-claim -- completely unchanged.
    The record must bind the RECOMPUTED file digests, so this swap is detected even though nothing
    the naive implementation reads has changed at all.
    """
    record, path = _freeze(tmp_path)
    manifest_before = (tmp_path / "is" / "manifest.json").read_bytes()
    bars = pd.read_parquet(tmp_path / "is" / "bars.parquet")
    bars.loc[bars.index[0], "close"] = float(bars["close"].iloc[0]) * 2.0
    bars.to_parquet(tmp_path / "is" / "bars.parquet", index=False)
    assert (tmp_path / "is" / "manifest.json").read_bytes() == manifest_before, (
        "the fixture must leave the manifest untouched, or this test proves nothing"
    )
    assert json.loads(manifest_before)["manifest_sha256"] == record["is_manifest_sha256"]
    with pytest.raises(ValueError, match="IS snapshot"):
        verify_activation(path)


def test_build_activation_record_rejects_an_invalid_machine_contract(tmp_path):
    """The config is bound as an AUTHORITY, so it must be a valid CUP-20 contract at freeze time.
    Hashing an unparsed or drifted config would freeze the drift instead of catching it.
    """
    authorities = _fixture(tmp_path)
    config = authorities[0]
    config.write_text(config.read_text().replace("target_size = 20", "target_size = 40"))
    with pytest.raises(ValueError, match="frozen contract"):
        build_activation_record(*authorities)


def test_build_activation_record_names_a_missing_authority(tmp_path):
    authorities = _fixture(tmp_path)
    authorities[1].unlink()
    with pytest.raises(FileNotFoundError, match="CHARTER.md"):
        build_activation_record(*authorities)


def test_build_activation_record_rejects_a_missing_implementation_root(tmp_path):
    """``bundle_digest`` over a non-existent tree returns the digest of nothing rather than
    raising, so a mistyped or unmounted implementation path would freeze cleanly while binding no
    code at all. Both halves of that fail-open are closed and both are exercised: a root that does
    not exist, and a root that exists but is empty.
    """
    authorities = list(_fixture(tmp_path))
    authorities[6] = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError, match="does-not-exist"):
        build_activation_record(*authorities)


def test_build_activation_record_rejects_an_empty_implementation_root(tmp_path):
    authorities = list(_fixture(tmp_path))
    empty = tmp_path / "empty-implementation"
    empty.mkdir()
    authorities[6] = empty
    with pytest.raises(ValueError, match="contains no files"):
        build_activation_record(*authorities)


@pytest.mark.parametrize("missing", [*_AUTHORITY_KEYS, "config_path", "is_root"])
def test_verify_activation_rejects_a_record_missing_a_field(tmp_path, missing):
    """A truncated or hand-edited freeze must fail closed with a named field, never a bare
    ``KeyError`` from deep inside the comparison loop.
    """
    record, path = _freeze(tmp_path)
    del record[missing]
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match=missing):
        verify_activation(path)


def test_verify_activation_rejects_a_record_that_is_not_an_object(tmp_path):
    path = tmp_path / "activation-freeze.json"
    path.write_text(json.dumps(["not", "a", "record"]))
    with pytest.raises(ValueError, match="JSON object"):
        verify_activation(path)


def test_verify_activation_rejects_a_non_string_field(tmp_path):
    """Every field is a path or a digest; a number or null in either position means the record was
    machine-mangled, and coercing it would hide that.
    """
    record, path = _freeze(tmp_path)
    record["charter_sha256"] = 12345
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="charter_sha256"):
        verify_activation(path)


# --- freezing while the holdout is quarantined -------------------------------------------------
#
# An amendment can land after ``quarantine.quarantine_holdout`` has moved the sealed tree out of
# the working tree, and re-freezing then must neither restore the holdout nor write the quarantine
# location into the record. ``build_activation_record``'s ``sealed_root_override`` is the third
# option: hash the tree where it is, record the path the contract names.


def _quarantine(tmp_path: Path) -> Path:
    """Move the fixture's sealed tree aside, the way ``quarantine_holdout`` does for real."""
    moved = tmp_path / "quarantined-sealed"
    shutil.move(str(tmp_path / "sealed"), str(moved))
    return moved


def test_build_activation_record_can_hash_a_quarantined_sealed_tree(tmp_path):
    """The override changes WHERE the tree is read from, never what it hashes to, and never the
    path the record carries.

    Mutation this catches: passing the quarantine path as ``sealed_root`` instead of as the
    override. That produces the same digest, so only the recorded path tells the two apart -- and a
    record naming the quarantine root stops verifying the moment the holdout is restored.
    """
    authorities = _fixture(tmp_path)
    in_place = build_activation_record(*authorities)
    moved = _quarantine(tmp_path)

    overridden = build_activation_record(*authorities, sealed_root_override=moved)
    assert overridden == in_place
    assert overridden["sealed_root"] == str(authorities[3])
    assert str(moved) not in json.dumps(overridden)


def test_build_activation_record_without_the_override_fails_on_a_quarantined_tree(tmp_path):
    """The negative control for the override: it must be doing real work.

    Without it the build cannot read the sealed snapshot at all, so a passing override test could
    not be explained by the tree still being reachable at the contract path.
    """
    authorities = _fixture(tmp_path)
    _quarantine(tmp_path)
    with pytest.raises((FileNotFoundError, ValueError)):
        build_activation_record(*authorities)


def test_the_override_still_fails_on_a_tampered_quarantined_tree(tmp_path):
    """It cannot weaken the freeze. A sealed tree altered while out of the working tree must fail
    verification just as loudly as one altered in place.

    Mutation this catches: an override that skips the sealed digest entirely (for example copying
    the frozen value through when the tree is absent), which would notarise anything.
    """
    record, path = _freeze(tmp_path)
    moved = _quarantine(tmp_path)
    assert verify_activation(path, sealed_root_override=moved) == record

    _reissue_snapshot(moved, seed=79)
    with pytest.raises(ValueError, match="sealed snapshot"):
        verify_activation(path, sealed_root_override=moved)


def test_verify_activation_without_the_override_cannot_read_a_quarantined_tree(tmp_path):
    """Pairs with the test above: the override is the only thing that makes the check available
    during the research phase, which is exactly when the organiser most needs to run it."""
    _, path = _freeze(tmp_path)
    _quarantine(tmp_path)
    with pytest.raises((FileNotFoundError, ValueError)):
        verify_activation(path)
