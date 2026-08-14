"""Extract each sleeve's EXACT unit-gross weight matrix by running the real candidate code
through the organiser's generate_targets with cadence 1 and the combination switched off.
Scores nothing; opens only the IS snapshot the team is given."""
from __future__ import annotations
import hashlib, importlib.util, re, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, "tournament/cup20/teams/team-12/research")
from panel import Panel
from crypto_trade.tournament.engine_v2 import generate_targets
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN

TPL = Path("tournament/cup20/teams/team-12/research/_template/strategy.py")
CACHE = Path("tournament/cup20/teams/team-12/research/_sleeves")
CACHE.mkdir(exist_ok=True)
SLEEVES = ("carry", "trend", "lowrisk", "flow")


def render(overrides: dict[str, int]) -> str:
    text = TPL.read_text()
    for name, value in overrides.items():
        text, k = re.subn(rf"^{name} = -?\d+", f"{name} = {value}", text, flags=re.M)
        assert k == 1, name
    return text


def load_module(source: str):
    path = CACHE / "_tmp_strategy.py"
    path.write_text(source)
    spec = importlib.util.spec_from_file_location("tmpstrat_" + hashlib.sha256(
        source.encode()).hexdigest()[:12], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sleeve_matrix(panel, sleeve: str, params: dict[str, int]) -> np.ndarray:
    key = sleeve + "_" + "_".join(f"{k}{v}" for k, v in sorted(params.items()))
    out = CACHE / f"{key}.npy"
    if out.exists():
        return np.load(out)
    ov = {f"USE_{s.upper()}": (1 if s == sleeve else 0) for s in SLEEVES}
    ov.update({"EQUAL_NOTIONAL": 1, "REBALANCE_CADENCE": 1, "REBALANCE_PHASE": 0})
    ov.update(params)
    mod = load_module(render(ov))
    t = time.time()
    tg = generate_targets(mod.build_strategy(), panel.snapshot.bars, panel.snapshot.funding,
                          panel.snapshot.membership, list(panel.times), seed=20200817,
                          interval_hours=8)
    W = tg.reindex(columns=panel.symbols).fillna(0.0).to_numpy(dtype=float)
    g = np.abs(W).sum(axis=1)
    W = W / np.where(g > 0, g, 1.0)[:, None]
    np.save(out, W)
    print(f"  built {key} in {time.time()-t:.0f}s", flush=True)
    return W


if __name__ == "__main__":
    p = Panel()
    for s in SLEEVES:
        sleeve_matrix(p, s, {})
