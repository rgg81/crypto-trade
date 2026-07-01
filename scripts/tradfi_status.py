"""TradFi paper-engine STATUS — the per-tick alert check (health + parity + candle integrity).

READ-ONLY. Test-integrity checks for the tradfi paper desk (iter-016 BEAR-GATED TSMOM champion on
68 Binance single-stock TradFi perps ex-PAYP, DAILY US-trading-day rebalance):

  STATUS  : (a) engine alive (`ps` contains a real `python … run_tradfi_paper.py`), (b) no Traceback
            in the last ~400 log lines, (c) MISSED rebalance — a NEW SETTLED Yahoo daily bar exists
            on disk (date < today UTC) but `tradfi_last_candle` has not advanced to it.
  PARITY  : recompute the iter-016 DEPLOYED target book at the bar the held book was built for
            (`tradfi_last_candle`), DROP `LIVE_EXCLUDED` (PAYP), compare per-name to the held book.
            DRIFT = the paper book no longer matches what the strategy says to hold.
  CANDLE  : (a) no forming/unsettled bar leaked into the book (look-ahead) — `tradfi_last_candle`
            must be strictly < today UTC; (b) data-staleness FLAG (freshest settled bar too old on a
            trading day) — informational, benign over weekends/holidays.

Per the HANDS-OFF mandate these are the ONLY alert sources (test-integrity). Dual P&L / drawdown /
basis / funding are OBSERVATIONAL (printed as a FUNDING/BASIS line here, detailed in tradfi_digest).

The MISSED / settled-bar rule is ON-DISK-DATA-FRESHNESS, not wall-clock: it reuses the engine's OWN
`_latest_settled_ms()` / `_today_ms()` helpers so the two never disagree. A weekend / US holiday
produces NO new settled Yahoo bar, so `settled == last_candle` and MISSED cannot false-fire.

Exit 0 = all OK; exit 1 = an alert fired.

Run:  uv run python scripts/tradfi_status.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT / "src"), str(_ROOT / "analysis" / "portfolio" / "tradfi")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import live_weights_tradfi as lw  # noqa: E402  — parity bridge (recompute the deployed target book)
from live_tradfi import LIVE_EXCLUDED, TradfiPaperConfig, TradfiPaperEngine  # noqa: E402

from crypto_trade.live.state_store import StateStore  # noqa: E402

DB = _ROOT / "data" / "tradfi_paper.db"
LOG = _ROOT / "logs" / "tradfi_paper.log"
DATA_DIR = str(_ROOT / "data")
PARITY_TOL = 1e-6  # held vs recomputed target — paper fills are exact so steady-state parity ≈ 0
STALE_DAYS = 5  # freshest-settled-bar age (days) above which we FLAG on a weekday (else benign)
DAY_MS = 86_400_000

# ps-line substrings that MENTION the runner but are NOT the runner process (avoid false "up").
_BAD = ("grep", "pgrep", "bash -c", "/bin/sh", "tradfi_status", "tradfi_digest")


def _is_runner_line(ln: str) -> bool:
    """True iff a `ps -eo args` line is the ACTUAL python runner (not a grep/monitor/shell line)."""
    return "run_tradfi_paper.py" in ln and "python" in ln and not any(b in ln for b in _BAD)


def _engine_up_from_ps(ps_stdout: str) -> bool:
    """Pure string test — does any ps line look like the real runner process? (unit-testable)."""
    return any(_is_runner_line(ln) for ln in ps_stdout.splitlines())


def _engine_up() -> bool:
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    return _engine_up_from_ps(out)


def _log_scan() -> tuple[bool, str]:
    """(traceback_present, last_[rebal]_line). A missing log is not a traceback (engine down)."""
    if not LOG.exists():
        return False, ""
    tail = LOG.read_text(errors="ignore").splitlines()[-400:]
    tb = any("Traceback" in line for line in tail)
    rebal = next((line for line in reversed(tail) if "[rebal]" in line), "")
    return tb, rebal.strip()


def _missed_rebalance(last_candle: int | None, settled_ms: int | None) -> bool:
    """MISSED iff a settled Yahoo bar strictly newer than the last processed one exists ON DISK.

    On-disk-data-freshness rule (not wall-clock): a new SETTLED bar is at least a trading day ahead
    of `tradfi_last_candle`. Weekends/holidays produce NO new settled bar (settled == last) so this
    stays False — no false MISSED. `last_candle is None` = first run (nothing missed yet).
    """
    if last_candle is None or settled_ms is None:
        return False
    return int(settled_ms) > int(last_candle)


def _parity_drift(
    held: dict,
    target: dict,
    excluded: frozenset[str] = LIVE_EXCLUDED,
    tol: float = PARITY_TOL,
) -> list[str]:
    """Per-name |held − target| drift list, AFTER dropping `_meta` + `excluded` (PAYP) from target.

    The exclusion is the load-bearing bit: the LIVE held book never carries PAYP, so a raw target
    that still contains PAYP must have it dropped before the compare or PAYP false-DRIFTs.

    PARITY IS A SIGNAL-FIDELITY CHECK — deliberately PRE-QUANTIZATION. Both `held` (`tradfi_held_w`)
    and the recomputed `target` are the CONTINUOUS ideal weights, so lot-quantization / sub-min-
    notional drops (a LIVE-execution effect that lives only in the eq_live track, never in the held
    book) can NEVER make this drift. A DRIFT here means the SIGNAL itself diverged from the
    backtest, which is a real correctness bug; quantization is not, by construction.
    """
    tgt = {k: v for k, v in target.items() if k != "_meta" and k not in excluded}
    out = []
    for s in sorted(set(held) | set(tgt)):
        h, t = float(held.get(s, 0.0)), float(tgt.get(s, 0.0))
        if abs(h - t) > tol:
            out.append(f"{s}: held {h:+.4f} vs target {t:+.4f}")
    return out


def main() -> int:
    alerts: list[str] = []
    flags: list[str] = []

    up = _engine_up()
    if not up:
        alerts.append("engine DOWN (run_tradfi_paper.py not running)")
    tb, last_rebal = _log_scan()
    if tb:
        alerts.append("TRACEBACK in logs/tradfi_paper.log")

    held: dict = {}
    last_candle: int | None = None
    eq_parity = eq_live = fund_cum = None
    parity = candle = "n/a"
    settled_ms: int | None = None

    if not DB.exists():
        flags.append("no DB yet (engine never launched)")
    else:
        st = StateStore(DB)
        raw = st.get_state("tradfi_held_w")
        held = json.loads(raw) if raw else {}
        lc = st.get_state("tradfi_last_candle")
        last_candle = int(lc) if lc is not None else None
        eq_parity = st.get_state("tradfi_equity_parity")
        eq_live = st.get_state("tradfi_equity_live")
        fund_cum = st.get_state("tradfi_funding_cum")

        # Reuse the engine's OWN settled-bar detection so the two rules never diverge.
        eng = TradfiPaperEngine(TradfiPaperConfig())
        today_ms = eng._today_ms()
        settled_ms = eng._latest_settled_ms()

        # (c) MISSED rebalance — on-disk settled bar ahead of the last processed one.
        if _missed_rebalance(last_candle, settled_ms):
            alerts.append(
                f"MISSED rebalance: settled bar {pd.Timestamp(int(settled_ms), unit='ms').date()} "
                f"on disk but last_candle stuck at "
                f"{pd.Timestamp(int(last_candle), unit='ms').date()}"
            )

        # CANDLE (a) — look-ahead: a forming/unsettled bar must never have entered the book.
        if last_candle is not None and last_candle >= today_ms:
            alerts.append(
                f"CANDLE=BAD look-ahead: last_candle "
                f"{pd.Timestamp(int(last_candle), unit='ms').date()} >= today "
                f"{pd.Timestamp(today_ms, unit='ms').date()}"
            )
            candle = "BAD"
        else:
            candle = "OK"

        # CANDLE (b) — staleness FLAG (informational; benign over weekends/holidays).
        now = pd.Timestamp.now(tz="UTC")
        if settled_ms is None:
            flags.append("no settled tradfi bar on disk yet")
        else:
            age_days = (today_ms - int(settled_ms)) / DAY_MS
            if now.weekday() < 5 and age_days > STALE_DAYS:
                flags.append(
                    f"data stale: freshest settled bar "
                    f"{pd.Timestamp(int(settled_ms), unit='ms').date()} is {age_days:.0f}d old "
                    f"(>{STALE_DAYS}d on a weekday)"
                )
                if candle == "OK":
                    candle = f"OK (stale {age_days:.0f}d)"

        # PARITY — recompute the deployed target at the bar the held book was built for, drop PAYP.
        if held and last_candle is not None:
            as_of = pd.Timestamp(int(last_candle), unit="ms")
            try:
                tgt = lw.deployed_target_weights(as_of, DATA_DIR)
                drift = _parity_drift(held, tgt)
                parity = "OK" if not drift else "DRIFT"
                if drift:
                    alerts.append("PARITY=DRIFT: " + "; ".join(drift[:6]))
            except Exception as e:  # noqa: BLE001 — a recompute hiccup is a flag, not a silent pass
                parity = "ERR"
                flags.append(f"parity recompute failed: {e}")

    # ── FUNDING / BASIS — OBSERVATIONAL (never an alert): perp-vs-underlying tracking + carry ──
    equity0 = TradfiPaperConfig().equity_usd
    basis_line = "FUNDING/BASIS: n/a (no equity state yet)"
    if eq_parity is not None and eq_live is not None:
        p, live_ = float(eq_parity), float(eq_live)
        basis_gap = live_ - p
        bps = basis_gap / equity0 * 1e4
        fc = float(fund_cum) if fund_cum is not None else float("nan")
        basis_line = (
            f"FUNDING/BASIS: eq_parity=${p:,.0f}  eq_live=${live_:,.0f}  "
            f"basis_gap=${basis_gap:,.0f} ({bps:+.0f}bps)  funding_cum=${fc:,.2f}"
        )

    status = "ALERT" if alerts else "OK"
    ep = f"${float(eq_parity):,.0f}" if eq_parity is not None else "n/a"
    el = f"${float(eq_live):,.0f}" if eq_live is not None else "n/a"
    print(
        f"STATUS: {status}  (engine={'up' if up else 'DOWN'}, eq_parity={ep}, eq_live={el}, "
        f"held={len(held)} names, parity={parity}, candle={candle})"
    )
    if last_candle is not None:
        line = f"  last settled bar processed: {pd.Timestamp(int(last_candle), unit='ms').date()}"
        if settled_ms is not None:
            line += f"   freshest on disk: {pd.Timestamp(int(settled_ms), unit='ms').date()}"
        print(line)
    if last_rebal:
        print(f"  last rebal: {last_rebal}")
    print(f"  {basis_line}")
    for a in alerts:
        print(f"  ALERT: {a}")
    for f in flags:
        print(f"  flag: {f}")
    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
