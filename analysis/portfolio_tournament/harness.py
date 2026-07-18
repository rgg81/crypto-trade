"""Mechanical leak-proofing harness — the tournament's structural anti-cheat layer.

Six independent checks per strategy, all mandatory (QE runs them pre-freeze; the
leaderboard freeze and the Critic re-run them independently):

1. STATIC SCAN        — AST import whitelist (numpy/pandas/scipy/stdlib + ``teamlib`` only),
                        file-read/exec call ban, and a prohibited-path string denylist.
2. DETERMINISM        — two fresh module loads on identical inputs must emit bit-identical
                        weights (catches unseeded randomness, wall-clock, import-order state).
3. TRUNCATED REPLAY   — re-run on data truncated at N cut dates; emitted weights ≤ cut must be
                        bit-identical to the full-panel run (catches future reads AND
                        full-sample normalisations AND panel-length-derived state).
                        Truncation covers klines AND funding AND OI AND the eligibility mask.
4. FUTURE CORRUPTION  — mangle every row strictly AFTER a cut (prices ×7+5, volumes ×3+1,
                        funding ×3+1e-4, OI ×3+1, eligibility inverted); weights ≤ cut must be
                        unchanged (catches absolute-index tricks that survive truncation).
5. SAME-BAR           — perturb close[t*] + the funding/OI cells of candle t* only; weights
                        STRICTLY BEFORE t* must be unchanged (candle-t* info is legitimately
                        available to the t* decision — the same-bar convention).
6. WIDENING           — re-run with extra synthetic never-eligible columns appended (the
                        holdout panel WILL contain coins the IS panel didn't); the strategy
                        must not crash and must return a weights DataFrame.

Truncation semantics for funding: the aux row of candle t sums events in (open[t], open[t+1]],
knowable at candle t's close — so a cut at candle t keeps funding events with
ts <= cut + STEP_MS (everything belonging to candles ≤ t) and klines/OI rows with
open_time <= cut.
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

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import engine as te  # noqa: E402
from portfolio_tournament import protocol as tp  # noqa: E402

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
        # the ONLY approved substrate module (pure metric helpers, no data access)
        "teamlib",
    }
)

BANNED_CALL_NAMES = frozenset({"open", "eval", "exec", "__import__", "compile", "input"})
BANNED_ATTR_PREFIXES = ("read_",)  # pd.read_csv / read_parquet / read_pickle / ...
BANNED_ATTR_NAMES = frozenset({"load", "loadtxt", "genfromtxt", "fromfile", "to_pickle"})

PATH_DENYLIST = (
    "pf_data",
    "funding_rates",
    "open_interest",
    "data_live",
    "diary-portfolio",
    "briefs-",
    "reports-",
    "BASELINE_",
    "iter_0",
    "iter_v",
    "portfolio_v2",
    "analysis/portfolio",
    "crypto_trade",
    "holdout",
    "MANIFEST",
    "fapi.",
    "binance.com",
    "binance.vision",
    "http://",
    "https://",
    ".env",
    "testnet",
)
_DATA_DIR_RE = re.compile(r"(?<![\w./-])data/")  # bare data/ path literal (data_is/ is fine)


@dataclass
class HarnessReport:
    scan_ok: bool = False
    determinism_ok: bool = False
    truncation_ok: bool = False
    corruption_ok: bool = False
    samebar_ok: bool = False
    widening_ok: bool = False
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
            and self.widening_ok
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
def _cut_ms(t) -> int:
    return int(pd.Timestamp(t).value // 1_000_000)


_VOLUME_COLS = ("volume", "quote_volume", "trades", "taker_buy_volume", "taker_buy_quote_volume")
_OHLC = ("open", "high", "low", "close")


def truncate_bundle(bundle: dict, cut) -> dict:
    """Every source truncated at what is knowable at the CLOSE of the cut candle."""
    ms = _cut_ms(cut)
    return {
        "klines": {s: df[df.index <= ms] for s, df in bundle["klines"].items()},
        "funding": {s: f[f.index <= ms + tc.STEP_MS] for s, f in bundle["funding"].items()},
        "oi": {s: df[df.index <= ms] for s, df in bundle["oi"].items()},
        "elig": bundle["elig"][bundle["elig"].index <= ms],
    }


def corrupt_bundle_after(bundle: dict, cut) -> dict:
    """Mangle everything STRICTLY AFTER the cut (positive-preserving so math never NaNs out)."""
    ms = _cut_ms(cut)
    klines: dict[str, pd.DataFrame] = {}
    for s, df in bundle["klines"].items():
        d = df.astype(float)  # float-cast: int columns (trades) must accept mangled values;
        m = d.index > ms  # build_panels float-casts everything anyway, so this is invisible
        d.loc[m, list(_OHLC)] = d.loc[m, list(_OHLC)] * 7.0 + 5.0
        vc = [c for c in _VOLUME_COLS if c in d.columns]
        d.loc[m, vc] = d.loc[m, vc] * 3.0 + 1.0
        klines[s] = d
    funding: dict[str, pd.Series] = {}
    for s, f in bundle["funding"].items():
        g = f.copy()
        m = g.index > ms + tc.STEP_MS
        g[m] = g[m] * 3.0 + 1e-4
        funding[s] = g
    oi: dict[str, pd.DataFrame] = {}
    for s, df in bundle["oi"].items():
        d = df.astype(float)
        m = d.index > ms
        d.loc[m] = d.loc[m] * 3.0 + 1.0
        oi[s] = d
    elig = bundle["elig"].copy()
    m = elig.index > ms
    elig.loc[m] = 1 - elig.loc[m]
    return {"klines": klines, "funding": funding, "oi": oi, "elig": elig}


def perturb_samebar(bundle: dict, t) -> dict:
    """Perturb ONLY candle t*'s same-bar info: close[t*], funding events of candle t*, OI[t*]."""
    ms = _cut_ms(t)
    klines: dict[str, pd.DataFrame] = {}
    for s, df in bundle["klines"].items():
        d = df.copy()
        if ms in d.index:
            d.loc[ms, "close"] = float(d.loc[ms, "close"]) * 1.001
        klines[s] = d
    funding: dict[str, pd.Series] = {}
    for s, f in bundle["funding"].items():
        g = f.copy()
        m = (g.index > ms) & (g.index <= ms + tc.STEP_MS)
        g[m] = g[m] + 1e-4
        funding[s] = g
    oi: dict[str, pd.DataFrame] = {}
    for s, df in bundle["oi"].items():
        d = df.astype(float)  # float-cast: ×1.001 must not hit int64 columns (pandas 3 raises)
        if ms in d.index:
            d.loc[ms] = d.loc[ms] * 1.001
        oi[s] = d
    return {"klines": klines, "funding": funding, "oi": oi, "elig": bundle["elig"]}


def widen_bundle(bundle: dict, *, n_extra: int = 5, seed: int = tc.SEED) -> dict:
    """Append deterministic synthetic never-eligible symbols (holdout-panel realism check)."""
    rng = np.random.default_rng(seed)
    any_df = next(iter(bundle["klines"].values()))
    ref = bundle["klines"].get("BTCUSDT", any_df)
    idx = ref.index[len(ref) // 2 :]  # lists mid-panel: NaN-before behaviour included
    klines = dict(bundle["klines"])
    for i in range(n_extra):
        px = 10.0 * np.exp(np.cumsum(rng.normal(0, 0.01, size=len(idx))))
        vol = rng.uniform(1e3, 1e5, size=len(idx))
        df = pd.DataFrame(
            {
                "open": px,
                "high": px * 1.01,
                "low": px * 0.99,
                "close": px * (1 + rng.normal(0, 0.001, size=len(idx))),
                "volume": vol,
                "close_time": np.asarray(idx, dtype=np.int64) + tc.STEP_MS - 1,
                "quote_volume": vol * px,
                "trades": np.full(len(idx), 100.0),
                "taker_buy_volume": vol * 0.5,
                "taker_buy_quote_volume": vol * px * 0.5,
            },
            index=idx,
        )
        klines[f"ZZWIDE{i:02d}USDT"] = df
    return {**bundle, "klines": klines}


def pick_cut_dates(index: pd.DatetimeIndex, n: int, seed: int) -> list[pd.Timestamp]:
    """n seeded-random cuts (post-warmup) + fixed adversarial cuts: the COVID crash low, the
    May-2021 crash, the FTX collapse, the panel midpoint, and the last-but-one candle."""
    lo, hi = min(750, len(index) // 3), len(index) - 3
    rng = np.random.default_rng(seed)
    pos = sorted(rng.choice(np.arange(lo, hi), size=min(n, hi - lo), replace=False))
    cuts = {index[p] for p in pos}
    for adversarial in ("2020-03-13", "2021-05-19", "2022-11-09"):
        p = int(index.searchsorted(pd.Timestamp(adversarial)))
        if lo < p < hi:
            cuts.add(index[p])
    cuts.add(index[len(index) // 2])
    cuts.add(index[-2])
    return sorted(cuts)


# ------------------------------------------------------------------ audit -----------------------
def _run_strategy(team_dir: Path, bundle: dict):
    """(conformed raw weights, panel dict) for one FRESH strategy run on one bundle variant."""
    pn, aux, _scoring = te.build_panels(bundle)
    view = te.team_view(pn)
    team_aux = te.make_team_aux(aux)
    mod = tp.load_strategy(team_dir)
    raw = mod.build_raw_weights(view, team_aux)
    return te.conform_raw(raw, pn), pn


def _slices_equal(a: pd.DataFrame, b: pd.DataFrame, hi: pd.Timestamp, *, strict: bool) -> bool:
    """Bit-exact equality of the two frames on shared columns, rows <= hi (< hi when strict)."""
    cols = [c for c in b.columns if c in a.columns]
    am = a[(a.index < hi) if strict else (a.index <= hi)][cols]
    bm = b[(b.index < hi) if strict else (b.index <= hi)][cols]
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
    bundle: dict | None = None,
) -> HarnessReport:
    """Run all six checks against the frozen IS snapshot; every check independent."""
    rep = HarnessReport()
    rep.violations = scan_sources(team_dir)
    rep.scan_ok = not rep.violations

    if bundle is None:
        bundle = te.load_is_bundle(snapshot_dir, manifest_path, verify=verify)
    try:
        raw_full, pn = _run_strategy(team_dir, bundle)
        raw_full2, _ = _run_strategy(team_dir, bundle)
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
            raw_t, _ = _run_strategy(team_dir, truncate_bundle(bundle, cut))
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
            raw_c, _ = _run_strategy(team_dir, corrupt_bundle_after(bundle, cut))
        except Exception as e:  # noqa: BLE001
            rep.corruption_ok = False
            rep.violations.append(f"corruption@{cut.date()}: strategy raised {e!r}")
            continue
        if not _slices_equal(raw_c, raw_full, cut, strict=False):
            rep.corruption_ok = False
            rep.violations.append(f"corruption@{cut.date()}: weights <= cut changed")

    t_star = idx[int(len(idx) * 0.7)]
    try:
        raw_s, _ = _run_strategy(team_dir, perturb_samebar(bundle, t_star))
        rep.samebar_ok = _slices_equal(raw_s, raw_full, t_star, strict=True)
        if not rep.samebar_ok:
            rep.violations.append(f"same-bar@{t_star.date()}: weights BEFORE t* changed")
    except Exception as e:  # noqa: BLE001
        rep.violations.append(f"same-bar@{t_star.date()}: strategy raised {e!r}")

    try:
        raw_w, _ = _run_strategy(team_dir, widen_bundle(bundle, seed=seed))
        rep.widening_ok = isinstance(raw_w, pd.DataFrame)
        if not rep.widening_ok:
            rep.violations.append("widening: strategy did not return a DataFrame")
    except Exception as e:  # noqa: BLE001
        rep.violations.append(f"widening: strategy raised on extra columns {e!r}")

    tp.purge_team_modules()
    return rep
