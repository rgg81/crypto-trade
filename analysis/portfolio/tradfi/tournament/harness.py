"""Mechanical leak-proofing harness — the tournament's structural anti-cheat layer.

Five independent checks per strategy, all mandatory (QE runs them pre-freeze; the
leaderboard and the Critic re-run them independently):

1. STATIC SCAN        — AST import whitelist (numeric libs + approved substrate modules only),
                        file-read/exec call ban, and a prohibited-path string denylist.
2. DETERMINISM        — two fresh module loads on identical inputs must emit bit-identical
                        weights (catches unseeded randomness, wall-clock, import-order state).
3. TRUNCATED REPLAY   — re-run on data truncated at N cut dates; emitted weights ≤ cut must be
                        bit-identical to the full-panel run (catches future reads AND
                        full-sample normalisations AND panel-length-derived state).
4. FUTURE CORRUPTION  — mangle every bar strictly AFTER a cut (prices ×7+5, volume ×3+1, VIX
                        ×2+3); weights ≤ cut must be unchanged (catches absolute-index tricks
                        that survive truncation).
5. SAME-BAR           — perturb close[t*] only; weights STRICTLY BEFORE t* must be unchanged
                        (close[t*] is legitimately available to the t* decision).
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from tournament import constants as tc  # noqa: E402
from tournament import engine as te  # noqa: E402
from tournament import protocol as tp  # noqa: E402

# imports a team strategy may use (root package names); team-local modules are added per-scan
ALLOWED_IMPORT_ROOTS = frozenset(
    {
        "numpy",
        "pandas",
        "scipy",
        "math",
        "statistics",
        "itertools",
        "functools",
        "collections",
        "dataclasses",
        "typing",
        "numbers",
        "enum",
        "abc",
        "__future__",
        # approved substrate modules (read-only helpers, no data access)
        "core_tradfi",
        "neutralize",
        "universe_tradfi",
    }
)

BANNED_CALL_NAMES = frozenset({"open", "eval", "exec", "__import__", "compile", "input"})
BANNED_ATTR_PREFIXES = ("read_",)  # pd.read_csv / read_parquet / read_pickle / ...
BANNED_ATTR_NAMES = frozenset({"load", "loadtxt", "genfromtxt", "fromfile", "to_pickle"})

PATH_DENYLIST = (
    "data_live_tradfi",
    "funding_rates",
    "diary-portfolio-tradfi",
    "BASELINE",
    "reports-tradfi",
    "iter_0",
    "splice_loader",
    "reconcile_basis",
    "oos_forensic",
    "live_tradfi",
    "live_weights",
    "holdout",
    "MANIFEST",
)
_DATA_DIR_RE = re.compile(r"(?<![\w./-])data/")  # bare data/ path literal (data_is/ is fine)


@dataclass
class HarnessReport:
    scan_ok: bool = False
    determinism_ok: bool = False
    truncation_ok: bool = False
    corruption_ok: bool = False
    samebar_ok: bool = False
    n_truncations: int = 0
    violations: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.scan_ok
            and self.determinism_ok
            and self.truncation_ok
            and self.corruption_ok
            and self.samebar_ok
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ok"] = self.ok
        return d


# ------------------------------------------------------------------ static scan -----------------
def scan_sources(team_dir: Path) -> list[str]:
    """Return violations for every .py in the team bundle (empty list == clean)."""
    team_dir = Path(team_dir)
    violations: list[str] = []
    py_files = [
        p
        for p in sorted(team_dir.rglob("*.py"))
        if p.relative_to(team_dir).parts[0] not in ("out", "__pycache__")
    ]
    local_roots = {p.stem for p in py_files}
    own_team = team_dir.name
    for p in py_files:
        rel = p.relative_to(team_dir)
        src = p.read_text()
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            violations.append(f"{rel}: syntax error {e}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root not in ALLOWED_IMPORT_ROOTS and root not in local_roots:
                        violations.append(f"{rel}:{node.lineno}: banned import '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # relative import — team-local, fine
                    continue
                root = (node.module or "").split(".")[0]
                if root not in ALLOWED_IMPORT_ROOTS and root not in local_roots:
                    violations.append(f"{rel}:{node.lineno}: banned import 'from {node.module}'")
            elif isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name) and fn.id in BANNED_CALL_NAMES:
                    violations.append(f"{rel}:{node.lineno}: banned call '{fn.id}('")
                elif isinstance(fn, ast.Attribute) and (
                    fn.attr.startswith(BANNED_ATTR_PREFIXES) or fn.attr in BANNED_ATTR_NAMES
                ):
                    violations.append(f"{rel}:{node.lineno}: banned call '.{fn.attr}('")
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                for token in PATH_DENYLIST:
                    if token in s:
                        violations.append(f"{rel}:{node.lineno}: prohibited literal {token!r}")
                if _DATA_DIR_RE.search(s):
                    violations.append(f"{rel}:{node.lineno}: prohibited path literal {s!r}")
                m = re.search(r"teams/(team-\d\d)", s)
                if m and m.group(1) != own_team:
                    violations.append(f"{rel}:{node.lineno}: references other team {m.group(1)}")
    return violations


# ------------------------------------------------------------------ data variants ---------------
def _cut_ms(t: pd.Timestamp) -> int:
    return int(pd.Timestamp(t).value // 1_000_000)


def truncate_coins(coins: dict[str, pd.DataFrame], cut: pd.Timestamp) -> dict[str, pd.DataFrame]:
    ms = _cut_ms(cut)
    return {s: df[df.index <= ms] for s, df in coins.items()}


def corrupt_coins_after(
    coins: dict[str, pd.DataFrame], cut: pd.Timestamp
) -> dict[str, pd.DataFrame]:
    """Mangle every bar STRICTLY AFTER the cut (positive-preserving so math never NaNs out)."""
    ms = _cut_ms(cut)
    out: dict[str, pd.DataFrame] = {}
    for s, df in coins.items():
        d = df.copy()
        mask = d.index > ms
        if s == tc.VIX_SYM:
            d.loc[mask, ["open", "high", "low", "close"]] = (
                d.loc[mask, ["open", "high", "low", "close"]] * 2.0 + 3.0
            )
        else:
            d.loc[mask, ["open", "high", "low", "close"]] = (
                d.loc[mask, ["open", "high", "low", "close"]] * 7.0 + 5.0
            )
        if "volume" in d.columns:
            d.loc[mask, "volume"] = d.loc[mask, "volume"] * 3.0 + 1.0
        out[s] = d
    return out


def perturb_close_at(coins: dict[str, pd.DataFrame], t: pd.Timestamp) -> dict[str, pd.DataFrame]:
    ms = _cut_ms(t)
    out: dict[str, pd.DataFrame] = {}
    for s, df in coins.items():
        d = df.copy()
        if ms in d.index:
            d.loc[ms, "close"] = float(d.loc[ms, "close"]) * 1.001
        out[s] = d
    return out


def pick_cut_dates(index: pd.DatetimeIndex, n: int, seed: int) -> list[pd.Timestamp]:
    """n seeded-random cuts (post-warmup) + fixed adversarial cuts: COVID trough week, the
    panel midpoint, and the last-but-one bar."""
    lo, hi = min(260, len(index) // 3), len(index) - 3
    rng = np.random.default_rng(seed)
    pos = sorted(rng.choice(np.arange(lo, hi), size=min(n, hi - lo), replace=False))
    cuts = {index[p] for p in pos}
    pos_covid = int(index.searchsorted(pd.Timestamp("2020-03-20")))
    if lo < pos_covid < hi:
        cuts.add(index[pos_covid])
    cuts.add(index[len(index) // 2])
    cuts.add(index[-2])
    return sorted(cuts)


# ------------------------------------------------------------------ audit -----------------------
def _run_strategy(team_dir: Path, coins: dict[str, pd.DataFrame]):
    """(conformed raw weights, panel dict) for one FRESH strategy run on one coins variant."""
    pn = te.panels_with_volume(coins)
    view = te.team_view(pn)
    aux = te.make_aux(coins)
    mod = tp.load_strategy(team_dir)
    raw = mod.build_raw_weights(view, aux)
    return te.conform_raw(raw, pn), pn


def _slices_equal(a: pd.DataFrame, b: pd.DataFrame, hi: pd.Timestamp, *, strict: bool) -> bool:
    """Bit-exact equality of the two frames on rows <= hi (or < hi when strict)."""
    am = a[(a.index < hi) if strict else (a.index <= hi)]
    bm = b[(b.index < hi) if strict else (b.index <= hi)]
    try:
        pd.testing.assert_frame_equal(am, bm, check_exact=True)
        return True
    except AssertionError:
        return False


def audit_strategy(
    team_dir: Path,
    snapshot_dir: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    *,
    n_truncations: int = 8,
    n_corruptions: int = 3,
    seed: int = tc.SEED,
    verify: bool = True,
) -> HarnessReport:
    """Run all five checks against the frozen IS snapshot; every check independent."""
    rep = HarnessReport()
    rep.violations = scan_sources(team_dir)
    rep.scan_ok = not rep.violations

    coins = te.load_is_coins(snapshot_dir, manifest_path, verify=verify)
    try:
        raw_full, pn = _run_strategy(team_dir, coins)
        raw_full2, _ = _run_strategy(team_dir, coins)
    except Exception as e:  # noqa: BLE001 — any strategy crash is a report, not a traceback
        rep.violations.append(f"strategy raised on full panel: {e!r}")
        return rep
    try:
        pd.testing.assert_frame_equal(raw_full, raw_full2, check_exact=True)
        rep.determinism_ok = True
    except AssertionError:
        rep.violations.append("determinism: two fresh runs differ")

    idx = pn["open"].index
    cuts = pick_cut_dates(idx, n_truncations, seed)
    rep.n_truncations = len(cuts)

    rep.truncation_ok = True
    for cut in cuts:
        try:
            raw_t, _ = _run_strategy(team_dir, truncate_coins(coins, cut))
        except Exception as e:  # noqa: BLE001
            rep.truncation_ok = False
            rep.violations.append(f"truncation@{cut.date()}: strategy raised {e!r}")
            continue
        if not _slices_equal(raw_t, raw_full, cut, strict=False):
            rep.truncation_ok = False
            rep.violations.append(f"truncation@{cut.date()}: weights <= cut changed")

    rep.corruption_ok = True
    for cut in cuts[:: max(1, len(cuts) // n_corruptions)][:n_corruptions]:
        try:
            raw_c, _ = _run_strategy(team_dir, corrupt_coins_after(coins, cut))
        except Exception as e:  # noqa: BLE001
            rep.corruption_ok = False
            rep.violations.append(f"corruption@{cut.date()}: strategy raised {e!r}")
            continue
        if not _slices_equal(raw_c, raw_full, cut, strict=False):
            rep.corruption_ok = False
            rep.violations.append(f"corruption@{cut.date()}: weights <= cut changed")

    t_star = idx[int(len(idx) * 0.7)]
    try:
        raw_s, _ = _run_strategy(team_dir, perturb_close_at(coins, t_star))
        rep.samebar_ok = _slices_equal(raw_s, raw_full, t_star, strict=True)
        if not rep.samebar_ok:
            rep.violations.append(f"same-bar@{t_star.date()}: weights BEFORE t* changed")
    except Exception as e:  # noqa: BLE001
        rep.violations.append(f"same-bar@{t_star.date()}: strategy raised {e!r}")

    tp.purge_team_modules()
    return rep
