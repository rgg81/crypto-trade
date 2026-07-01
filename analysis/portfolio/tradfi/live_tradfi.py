"""TradFi PAPER-TRADING engine — the confirmed iter-016 book, run continuously as a paper desk with
a DUAL P&L (backtest-parity + live-perp-with-funding).

Mirrors the metals paper engine (analysis/portfolio/metals/live_metals.py) but for DAILY US
trading-day bars and with a two-track P&L. Each new SETTLED daily bar:

  refresh Yahoo inputs + perp klines/funding  →  recompute the deployed iter-016 book from full
  history (the parity mechanism — same `iter_016.deployed_weights` the backtest uses)  →  book two
  equity tracks (PARITY = the Yahoo-TR backtest net; LIVE = perp-return − funding − turnover on the
  actual tradeable perps)  →  persist state + snapshot equity  →  log. No real orders.

TWO EQUITY TRACKS — SIGNAL vs EXECUTED
--------------------------------------
  * PARITY = THE SIGNAL (backtest book of record): ``net`` from
    ``live_weights_tradfi.deployed_book`` compounded since launch, on the CONTINUOUS ideal weights.
    All 69 names, Yahoo total-return, realistic cost (``ct.COST_SIDE`` = taker + slippage). This is
    the reference that must match the backtest bit-for-bit — quantization is NOT a signal error and
    must NEVER drift it. ``tradfi_held_w`` stays the continuous ideal book for the same reason (the
    monitor's PARITY check compares to it).
  * LIVE = THE REAL TRADE (executed paper P&L): the deployed weight panel QUANTIZED to the official
    Binance perp filters (lot-step rounding + sub-min-notional drops) at each day's perp price,
    scored on Binance TradFi-perp returns MINUS funding (on the quantized legs) MINUS turnover cost
    at the SAME ``ct.COST_SIDE`` the backtest owns (slippage is already in it — NOT double-counted;
    an optional ``live_extra_slippage_side`` stress knob defaults to 0). Coverage-aware — a name
    with no perp bar / no funding on a day contributes 0 (ragged onboarding, 34→100 % cover).

  ``basis_gap = equity_live − equity_parity`` bundles the full REAL-vs-SIGNAL gap:
  perp-vs-underlying basis + funding + quantization (lot rounding + dropped sub-min-notional legs).
  Slippage is in BOTH tracks via ``ct.COST_SIDE`` so it does NOT appear in the gap. Expected
  non-zero and growing — that is the desk's honesty. Phase-2b measured the basis+funding part at
  ≈ −85 bps at the whole-book level.

PAYP EXCLUSION
--------------
``LIVE_EXCLUDED = {PAYPUSDT}`` — the Phase-2b broken PayPal perp (perp ~$14 vs PayPal ~$43, corr
0.19: a perp-venue decoupling / ticker mismap). Dropped from the LIVE tradeable book. **NOT
re-normalized** — every other name keeps its exact backtest weight (parity-preserving); the tiny
gross/neutrality drift from the dropped leg is the documented cost of the exclusion.

FUNDING SIGN (reused from reconcile_basis_tradfi, NOT re-implemented)
--------------------------------------------------------------------
Per-leg funding P&L = ``−w·f`` (Binance f>0 ⇒ longs pay). The ms-resolution funding-binning + perp
open-to-open forward-return helpers are IMPORTED from ``reconcile_basis_tradfi`` (its 9 tests guard
the ms DatetimeIndex edge cast — casting to ``datetime64[ms]`` so funding rows do not silently read
as zero). This engine only adds the portfolio netting on top of those helper outputs.

WEIGHT-LAG ALIGNMENT (parity ⇔ live)
------------------------------------
``deployed_w`` is ALREADY one-bar lagged — ``iter_015.banded_book_freq`` ends in ``held.shift(1)``.
The backtest ``net[t] = Σ deployed_w[t]·ret_fwd[t] − cost`` aligns the lagged weight against the
open-to-open forward return on the SAME index t. The LIVE track uses the IDENTICAL alignment:
``live[t] = Σ deployed_w[t]·perp_rf[t] − Σ deployed_w[t]·f_daily[t] − cost`` (perp_rf on the same
index t, NO extra shift) — bit-for-bit the ``reconcile_basis_tradfi.book_level`` convention.

Settled-bar discipline (the daily analog of the metals forming-8h-candle drop): the book is
recomputed on bars whose UTC date < today, so today's unsettled bar never enters signal or P&L.

State (SQLite ``data/tradfi_paper.db`` via the crypto ``StateStore``): ``tradfi_held_w`` (JSON),
``tradfi_last_candle`` (ms of last processed settled bar), ``tradfi_launch_candle``,
``tradfi_equity_parity``, ``tradfi_equity_live``, ``tradfi_funding_cum``. Equity snapshots append to
``data/tradfi_equity.csv``.

Run:  PYTHONUNBUFFERED=1 uv run python run_tradfi_paper.py > logs/tradfi_paper.log 2>&1 &
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
for _p in (str(_HERE), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import core_tradfi as ct  # noqa: E402
import iter_016_bear_gated_tsmom as champ  # noqa: E402  — the confirmed tradfi baseline
import live_weights_tradfi as lw  # noqa: E402  — parity bridge (deployed_book / deployed_target_weights)
import perp_map_tradfi as pm  # noqa: E402
import reconcile_basis_tradfi as rc  # noqa: E402  — REUSE funding-binning + perp fwd-return helpers
import sizing_min_notional as sizing  # noqa: E402  — REUSE its filter fetch + quantize_weight rule
import universe_tradfi as ut  # noqa: E402

from crypto_trade.storage import csv_path, read_last_open_time  # noqa: E402

# The broken PayPal perp (Phase-2b): perp ~$14 vs PayPal ~$43, corr 0.19. Excluded from the LIVE
# tradeable book; NOT re-normalized (every other name keeps its exact backtest weight).
LIVE_EXCLUDED = frozenset({"PAYPUSDT"})

# Uniform Binance TradFi-perp filter fallback (verified 2026-07-01: all 69 perps share these). Used
# only when the live exchangeInfo fetch fails at engine init, so a brief outage never kills the desk
# (the quantizer keeps running on the uniform default).
_DEFAULT_FILT = {"min_notional": 5.0, "step": 0.01, "min_qty": 0.01}


@dataclasses.dataclass(frozen=True)
class TradfiPaperConfig:
    equity_usd: float = 10_000.0  # real starting budget; $10k trades the book cleanly
    # (~1% lot-quant shortfall, 66/68 legs clear the $5 min-notional) — see sizing_min_notional.py.
    data_dir: str = str(_ROOT / "data")  # Yahoo underlying bars (backtest source of truth)
    live_data_dir: str = str(_ROOT / "data_live_tradfi")  # Binance perp daily klines
    funding_dir: str = str(_ROOT / "data")  # funding under <funding_dir>/funding_rates/<SYM>.csv
    db_path: str = str(_ROOT / "data" / "tradfi_paper.db")
    equity_csv: str = str(_ROOT / "data" / "tradfi_equity.csv")
    poll_interval_seconds: int = 60
    # ── LIVE-track execution realism (PARITY track is untouched — it stays the ideal signal) ──
    # quantize_live: quantize the LIVE deployed weights to the official Binance perp filters
    #   (lot-step rounding + sub-min-notional drops) at each day's perp price. Quantization is a
    #   REAL execution effect, NOT a signal error — it must NEVER touch parity / ``tradfi_held_w``.
    quantize_live: bool = True
    # LIVE-track cost = ``ct.COST_SIDE`` (the SAME taker+slippage the backtest/parity already own:
    #   core_tradfi.COST_SIDE = 0.0006 = 6 bps/side taker + slippage) charged on the QUANTIZED
    #   turnover. Slippage is a real cost OWNED BY THE BACKTEST and lives in BOTH parity and live,
    #   so it is NOT re-added here (that would double-count it). The only cost difference vs parity
    #   is that quantized turnover ≠ continuous turnover — a small, correct quantization effect.
    #   ``live_extra_slippage_side`` is a STARTING-ASSUMPTION stress knob: extra slippage ABOVE the
    #   backtest's built-in assumption (to be refined from observed fills). Default 0.0 ⇒ live and
    #   parity are cost-consistent, so basis_gap = perp basis + funding + quantization ONLY.
    live_extra_slippage_side: float = 0.0


class TradfiPaperEngine:
    """Paper desk for the confirmed iter-016 book with a dual (parity + live-perp) P&L."""

    def __init__(self, cfg: TradfiPaperConfig) -> None:
        self.cfg = cfg
        # Lazy import so a StateStore-free unit test (synthetic frames) never opens the DB.
        from crypto_trade.live.state_store import StateStore

        Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.store = StateStore(Path(cfg.db_path))
        # Official Binance perp filters, fetched ONCE at init and cached for the LIVE quantizer.
        self._perp_filters = self._load_perp_filters()

    @staticmethod
    def _load_perp_filters() -> dict[str, dict]:
        """``{perp_symbol: {min_notional, step, min_qty}}`` from LIVE exchangeInfo (reuses sizing's
        ``_filters``), fetched once. On ANY fetch failure return ``{}`` — every lookup then resolves
        to the verified-uniform ``_DEFAULT_FILT`` — so a brief exchangeInfo outage never kills the
        desk (the quantizer keeps running on the uniform default)."""
        try:
            return sizing._filters()
        except Exception as e:  # noqa: BLE001 — exchangeInfo hiccup must not kill the engine
            print(
                f"  [filters] live exchangeInfo fetch failed ({e}); using uniform default filter",
                flush=True,
            )
            return {}

    # ── data refresh (Yahoo inputs + perp klines/funding; tolerant like the metals engine) ──
    def refresh_data(self) -> None:
        # (a) Yahoo underlying + VIX — incremental idempotent overwrite; yfinance hiccups tolerated
        try:
            import ingest_yahoo as iy

            syms = sorted(ut.SECTOR_MAP)
            end = str((pd.Timestamp.now("UTC") + pd.Timedelta(days=1)).date())
            n_ok = 0
            for sym in syms:
                try:
                    df = iy.download_daily(iy.yahoo_ticker(sym), "2010-01-01", end)
                    if df is None or df.empty:
                        continue
                    daily = iy._to_daily_frame(df)
                    if not daily.empty:
                        iy.write_daily_csv(sym, daily, self.cfg.data_dir)
                        n_ok += 1
                except Exception as e:  # noqa: BLE001 — per-name tolerance
                    print(f"  [data] yahoo {sym}: {e}", flush=True)
            try:
                vdf = iy.download_daily(iy.VIX_YAHOO, "2010-01-01", end)
                if vdf is not None and not vdf.empty:
                    iy.write_daily_csv(iy.VIX_DIRNAME, iy._to_daily_frame(vdf), self.cfg.data_dir)
            except Exception as e:  # noqa: BLE001
                print(f"  [data] yahoo VIX: {e}", flush=True)
            print(f"  [data] yahoo refreshed {n_ok}/{len(syms)} names", flush=True)
        except Exception as e:  # noqa: BLE001 — a broken yahoo refresh must not kill the loop
            print(f"  [data] yahoo refresh skipped ({e})", flush=True)

        # (b) perp klines + funding — via the dedicated ingest module (tolerant)
        try:
            import ingest_perp_tradfi as ip

            ip.ingest()
        except Exception as e:  # noqa: BLE001 — a source hiccup must not kill the loop
            print(f"  [data] perp/funding refresh skipped ({e})", flush=True)

    # ── settled panel + deployed book (same machinery as lw.deployed_book, truncated to settled) ──
    def _settled_book(self) -> tuple[pd.Series | None, pd.DataFrame | None, pd.Timestamp | None]:
        """Recompute ``(net, deployed_w, as_of)`` on the SETTLED panel (bars with UTC date < today).

        Identical mechanism to ``live_weights_tradfi.deployed_book`` (``champ.deployed_weights``) —
        parity by construction — but the panel is first truncated to bars whose date < today UTC, so
        today's not-yet-settled bar never enters. ``as_of`` = the newest settled bar (the book to
        hold now). Returns ``(None, None, None)`` if there is no settled data yet.
        """
        coins = ct.load_tradfi(lw._universe(self.cfg.data_dir), self.cfg.data_dir)
        today_ms = self._today_ms()
        coins = {s: d[d.index < today_ms] for s, d in coins.items() if len(d[d.index < today_ms])}
        if not coins:
            return None, None, None
        pn = ct.panels(coins)
        net, deployed_w = champ.deployed_weights(pn, data_dir=self.cfg.data_dir)
        return net, deployed_w, deployed_w.index[-1]

    @staticmethod
    def _drop_excluded(weights: dict[str, float]) -> dict[str, float]:
        """Drop ``LIVE_EXCLUDED`` names with NO re-normalization — every surviving leg keeps its
        exact backtest weight (parity-preserving; the dropped leg's small gross drift is the
        documented cost of the PAYP exclusion)."""
        return {k: v for k, v in weights.items() if k not in LIVE_EXCLUDED}

    # ── live-perp track: coverage-aware perp+funding netting on the SAME lagged deployed_w ──
    def _live_returns(self, deployed_w: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """``(live_ret, funding_ret)`` daily series from the perp+funding book (PAYP already gone).

        Reuses ``reconcile_basis_tradfi`` for the load-bearing math: ``load_perp_opens`` +
        ``fwd_ret`` (perp open-to-open forward return on the Yahoo trading-day grid) and
        ``daily_funding`` (ms-binned holding-window funding). This engine adds only the portfolio
        netting, matching ``book_level`` bit-for-bit:

            live_ret[t]    = Σ w·perp_rf − Σ w·f_daily − COST·Σ|Δw|  (w = deployed_w[t], no re-lag)
            funding_ret[t] = −Σ w·f_daily                            (funding P&L; long pays if f>0)

        Coverage-aware: names with no perp bar / no funding on a day are masked to weight 0 (they do
        not NaN-poison the sum). Weight lag = whatever ``deployed_w`` already carries (band ends in
        ``.shift(1)``) — the SAME alignment the parity ``net`` uses against ``ret_fwd``.
        """
        perp_map = {
            k: v for k, v in pm.perp_symbol_map(live=False).items() if k in deployed_w.columns
        }
        idx = deployed_w.index
        perp_opens = rc.load_perp_opens(perp_map, idx, live_dir=Path(self.cfg.live_data_dir))
        perp_rf = rc.fwd_ret(perp_opens)
        fdaily = rc.daily_funding(
            perp_map, idx, funding_dir=Path(self.cfg.funding_dir) / "funding_rates"
        )

        names = [c for c in deployed_w.columns if c in perp_rf.columns]
        w = deployed_w[names]
        prf = perp_rf.reindex(columns=names)
        fd = fdaily.reindex(columns=names)
        avail = prf.notna() & fd.notna()  # tradeable-live mask per (day, name)
        w_live = w.where(avail, 0.0)  # coverage-aware: absent leg → 0 (no NaN poison)

        perp_pnl = (w_live * prf.fillna(0.0)).sum(axis=1)
        funding_ret = -(w_live * fd.fillna(0.0)).sum(axis=1)  # −Σ w·f : long pays when f>0
        cost = ct.COST_SIDE * (w_live - w_live.shift(1)).abs().sum(axis=1)
        live_ret = perp_pnl + funding_ret - cost
        return live_ret, funding_ret

    # ── quantize a CONTINUOUS weight panel to the per-perp lot/min-notional filters (LIVE only) ──
    def _quantize_book(self, w: pd.DataFrame, opens: pd.DataFrame) -> pd.DataFrame:
        """Quantize each continuous deployed weight to its official Binance perp filter at that
        day's perp OPEN price. Returns a ``q_w`` panel (same index/columns as ``w``): sub-min-
        notional or sub-lot legs drop to 0 (their gross is simply not deployable live), the rest
        round to the lot step. Reuses the scalar ``sizing.quantize_weight`` (ONE rule, shared with
        the backtest-feasibility script) on the perp-available cells only — a cell with no perp open
        (NaN / ≤ 0) or zero weight stays 0. Quantization is a LIVE-execution effect ONLY; it never
        touches the parity track or ``tradfi_held_w`` (those stay the continuous ideal signal)."""
        equity = self.cfg.equity_usd
        q = pd.DataFrame(0.0, index=w.index, columns=w.columns)
        for name in w.columns:
            filt = self._perp_filters.get(name, _DEFAULT_FILT)
            prices = opens[name].to_numpy(dtype=float)
            weights = w[name].to_numpy(dtype=float)
            out = np.zeros(len(weights))
            live_cells = np.flatnonzero(np.isfinite(prices) & (prices > 0.0) & (weights != 0.0))
            for r in live_cells:
                rw, ok = sizing.quantize_weight(float(weights[r]), float(prices[r]), filt, equity)
                if ok:
                    out[r] = rw
            q[name] = out
        return q

    # ── live-perp track, EXECUTED: quantized fills + funding on the quantized legs + COST_SIDE ──
    def _live_returns_quantized(self, deployed_w: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """``(live_ret, funding_ret)`` for the REAL executed book — same coverage-aware perp+funding
        netting as ``_live_returns`` but on the QUANTIZED weight panel.

            q_w[t]         = quantize(deployed_w[t], perp_open[t], filter)   (drop sub-min-notional)
            live_ret[t]    = Σ q_w·perp_rf − Σ q_w·f_daily − COST·Σ|Δq_w|
            funding_ret[t] = −Σ q_w·f_daily                       (funding on the quantized legs)

        Cost per side = ``ct.COST_SIDE + live_extra_slippage_side``. With the default stress knob
        0.0 this is EXACTLY the backtest/parity cost (``ct.COST_SIDE`` = taker + slippage) — so
        slippage is NOT double-counted; the only cost difference vs parity is quantized vs
        continuous turnover. Parity + ``tradfi_held_w`` are computed elsewhere and stay CONTINUOUS
        (the ideal signal)."""
        perp_map = {
            k: v for k, v in pm.perp_symbol_map(live=False).items() if k in deployed_w.columns
        }
        idx = deployed_w.index
        perp_opens = rc.load_perp_opens(perp_map, idx, live_dir=Path(self.cfg.live_data_dir))
        perp_rf = rc.fwd_ret(perp_opens)
        fdaily = rc.daily_funding(
            perp_map, idx, funding_dir=Path(self.cfg.funding_dir) / "funding_rates"
        )

        names = [c for c in deployed_w.columns if c in perp_rf.columns]
        w = deployed_w[names]
        prf = perp_rf.reindex(columns=names)
        fd = fdaily.reindex(columns=names)
        opens = perp_opens.reindex(columns=names)

        q_w = self._quantize_book(w, opens) if self.cfg.quantize_live else w
        avail = prf.notna() & fd.notna()  # tradeable-live mask per (day, name)
        q_live = q_w.where(avail, 0.0)  # coverage-aware: absent leg → 0 (no NaN poison)

        perp_pnl = (q_live * prf.fillna(0.0)).sum(axis=1)
        funding_ret = -(q_live * fd.fillna(0.0)).sum(axis=1)  # −Σ q_w·f on the quantized legs
        cost_side = ct.COST_SIDE + self.cfg.live_extra_slippage_side
        cost = cost_side * (q_live - q_live.shift(1)).abs().sum(axis=1)
        live_ret = perp_pnl + funding_ret - cost
        return live_ret, funding_ret

    # ── one tick: refresh → detect new settled bar → recompute book → book dual P&L → persist ──
    def run_once(self, *, refresh: bool = True) -> dict | None:
        if refresh:
            self.refresh_data()

        net, deployed_w, as_of = self._settled_book()
        if net is None:
            print("  [tick] no settled tradfi data yet", flush=True)
            return None
        as_of_ms = int(as_of.value // 1_000_000)

        last_seen = self.store.get_state("tradfi_last_candle")
        if last_seen is not None and as_of_ms <= int(last_seen):
            return None  # no new settled bar since the last rebalance

        # launch = go-forward flat on first run (metals convention); smoke back-dates it in the DB
        if self.store.get_state("tradfi_launch_candle") is None:
            self.store.set_state("tradfi_launch_candle", str(as_of_ms))
        launch_ts = pd.Timestamp(int(self.store.get_state("tradfi_launch_candle")), unit="ms")

        # 1. held book (parity by construction with deployed_w's frontier) — drop PAYP, no renorm
        tgt = lw.deployed_target_weights(as_of, self.cfg.data_dir)
        meta = tgt.pop("_meta")
        for ex in sorted(LIVE_EXCLUDED):
            if abs(tgt.get(ex, 0.0)) > 0.0:
                print(
                    f"  [exclude] dropped {ex} leg w={tgt[ex]:+.4f} (NOT renormalized)", flush=True
                )
        held = self._drop_excluded({s: float(w) for s, w in tgt.items()})

        # Both tracks compound over REALIZED daily bars only: index < as_of. The as_of bar is the
        # book we now hold INTO the next open — its forward return has not settled, so it is dropped
        # (its live-track weight would also coverage-mask to 0 → a spurious full-unwind cost). This
        # is the daily analog of the metals "start flat at launch" convention.
        realized = net.index[net.index < as_of]

        # 2. PARITY track — backtest book of record (all names, Yahoo TR), compounded since launch
        net_since = net[(net.index >= launch_ts) & (net.index < as_of)]
        equity_parity = (
            self.cfg.equity_usd * float((1.0 + net_since).prod())
            if len(net_since)
            else self.cfg.equity_usd
        )

        # 3. LIVE track — the REAL executed book: perp+funding on the QUANTIZED lagged weights (lot
        #    rounding + sub-min-notional drops at each day's perp price), PAYP dropped, coverage
        #    aware. Cost = ct.COST_SIDE (same taker+slippage as parity) on quantized turnover — no
        #    double-count. Parity + held (below) stay CONTINUOUS: quantization is execution.
        dw_live = deployed_w.drop(columns=list(LIVE_EXCLUDED & set(deployed_w.columns)))
        live_ret, funding_ret = self._live_returns_quantized(dw_live)
        live_ret = live_ret.reindex(realized).fillna(
            0.0
        )  # realized bars only (drops warmup+frontier)
        funding_ret = funding_ret.reindex(realized).fillna(0.0)

        live_since = live_ret[live_ret.index >= launch_ts]
        equity_live = (
            self.cfg.equity_usd * float((1.0 + live_since).prod())
            if len(live_since)
            else self.cfg.equity_usd
        )
        # 4. cumulative + day funding P&L (return units × equity0). funding_ret is realized-only, so
        #    its last entry is the funding of the last COMPLETED holding window (as_of−1 → as_of).
        fund_since = funding_ret[funding_ret.index >= launch_ts]
        funding_cum = self.cfg.equity_usd * float(fund_since.sum())
        day_funding = self.cfg.equity_usd * float(funding_ret.iloc[-1]) if len(funding_ret) else 0.0
        basis_gap = equity_live - equity_parity

        # 5. persist state (6 keys)
        prev = self._load_held()
        n_legs = sum(
            1 for s in set(held) | set(prev) if abs(held.get(s, 0.0) - prev.get(s, 0.0)) > 1e-9
        )
        self._save_held(held)
        self.store.set_state("tradfi_last_candle", str(as_of_ms))
        self.store.set_state("tradfi_equity_parity", f"{equity_parity:.2f}")
        self.store.set_state("tradfi_equity_live", f"{equity_live:.2f}")
        self.store.set_state("tradfi_funding_cum", f"{funding_cum:.4f}")

        # 6. snapshot
        self._snapshot(as_of, equity_parity, equity_live, day_funding, funding_cum, basis_gap)

        # 7. one [rebal] line
        gross = sum(abs(w) for w in held.values())
        bps = basis_gap / self.cfg.equity_usd * 1e4
        print(
            f"  [rebal] as_of={as_of.date()}  gross={gross:.3f}  n_pos={len(held)}  legs={n_legs}  "
            f"eq_parity=${equity_parity:,.0f}  eq_live=${equity_live:,.0f}  "
            f"basis_gap=${basis_gap:,.0f} ({bps:+.0f}bps, incl quant+basis+funding)  "
            f"day_fund=${day_funding:,.2f}  cum_fund=${funding_cum:,.2f}  "
            f"(meta gross={meta['gross']:.3f})",
            flush=True,
        )
        return {
            "as_of": str(as_of.date()),
            "held": held,
            "equity_parity": equity_parity,
            "equity_live": equity_live,
            "basis_gap": basis_gap,
            "day_funding": day_funding,
            "funding_cum": funding_cum,
            "legs": n_legs,
        }

    def run(self) -> None:
        print(
            f"[tradfi-paper] start  equity=${self.cfg.equity_usd:,.0f}  "
            f"data={self.cfg.data_dir}  live={self.cfg.live_data_dir}  db={self.cfg.db_path}",
            flush=True,
        )
        while True:
            try:
                if self._new_candle_due():  # cheap gate — only work on a new settled daily bar
                    self.run_once()
            except KeyboardInterrupt:
                print("[tradfi-paper] stopped", flush=True)
                return
            except Exception as e:  # noqa: BLE001 — a tick error must not kill the desk
                print(f"[tradfi-paper] tick error: {e}", flush=True)
            time.sleep(self.cfg.poll_interval_seconds)

    # ── clock gate: has a NEW settled Yahoo daily bar appeared since the last rebalance? ──
    @staticmethod
    def _today_ms() -> int:
        return int(pd.Timestamp.now(tz="UTC").normalize().tz_localize(None).value // 1_000_000)

    def _latest_settled_ms(self) -> int | None:
        """Newest bar (UTC date < today) present as a universe CSV's last row — cheap tail read."""
        today_ms = self._today_ms()
        base = Path(self.cfg.data_dir)
        best: int | None = None
        for key in ut.SECTOR_MAP:
            ot = read_last_open_time(csv_path(base, key, "1d"))
            if ot is not None and ot < today_ms and (best is None or ot > best):
                best = ot
        return best

    def _new_candle_due(self) -> bool:
        last = self.store.get_state("tradfi_last_candle")
        if last is None:
            return True  # first run — seed + rebalance
        settled = self._latest_settled_ms()
        if settled is None:
            return False
        return settled > int(last)

    # ── persistence helpers ──
    def _load_held(self) -> dict:
        raw = self.store.get_state("tradfi_held_w")
        return json.loads(raw) if raw else {}

    def _save_held(self, held: dict) -> None:
        self.store.set_state("tradfi_held_w", json.dumps(held))

    def _snapshot(
        self,
        as_of: pd.Timestamp,
        equity_parity: float,
        equity_live: float,
        day_funding: float,
        funding_cum: float,
        basis_gap: float,
    ) -> None:
        path = Path(self.cfg.equity_csv)
        path.parent.mkdir(parents=True, exist_ok=True)
        new = not path.exists()
        with open(path, "a") as f:
            if new:
                f.write(
                    "ts_utc,bar_date,equity_parity,equity_live,day_funding_pnl,"
                    "funding_cum,basis_gap\n"
                )
            f.write(
                f"{dt.datetime.now(dt.UTC).isoformat()},{as_of.date()},{equity_parity:.2f},"
                f"{equity_live:.2f},{day_funding:.4f},{funding_cum:.4f},{basis_gap:.4f}\n"
            )
