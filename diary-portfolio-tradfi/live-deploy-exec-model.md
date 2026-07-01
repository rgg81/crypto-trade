# Live deploy — LIVE-track execution model (lot quantization + funding on quantized legs)

**Date:** 2026-07-01 · **Status:** DONE — LIVE track now models REAL execution; PARITY track unchanged (still the ideal signal).
**Files:** `analysis/portfolio/tradfi/live_tradfi.py` (engine), `analysis/portfolio/tradfi/sizing_min_notional.py`
(one importable `quantize_weight` helper), `scripts/tradfi_digest.py`, `scripts/tradfi_status.py` (comment),
`tests/test_tradfi_exec_model.py` (new).

## Conceptual model (as specified)
- **PARITY = THE SIGNAL.** Continuous ideal book (Yahoo-TR, `ct.COST_SIDE` = taker+slippage) compounded since
  launch. Must match the backtest bit-for-bit. `tradfi_held_w` stays the CONTINUOUS ideal book — quantization
  is an execution effect, NOT a signal error, so it can NEVER drift the monitor's PARITY check. **Left unchanged.**
- **LIVE = THE REAL TRADE.** Each day the deployed weights are QUANTIZED to the official Binance perp filters
  (lot-step rounding + sub-min-notional drops) at that day's perp OPEN price, marked on perp returns, funding
  booked on the QUANTIZED legs, turnover charged at `ct.COST_SIDE` on quantized turnover.
- **`basis_gap = eq_live − eq_parity`** = perp-vs-underlying basis + funding + quantization. Expected non-zero
  and growing — the desk's honesty.

## Cost-model correction (applied)
`core_tradfi.COST_SIDE = 0.0006` is ALREADY "6 bps/side taker + slippage" and is in BOTH parity and live.
Slippage is therefore NOT re-added as a live-only cost (that would double-count it). Live turnover cost =
`ct.COST_SIDE + live_extra_slippage_side`, with the stress knob **defaulting to 0.0** ⇒ live and parity are
cost-consistent, and `basis_gap` bundles perp basis + funding + **quantization only** (slippage is in both
tracks, so it does NOT appear in the gap). `quantize_live=True` default; `live_extra_slippage_side=0.0` default,
documented as a starting-assumption stress knob to refine from observed fills.

## Implementation
- New `TradfiPaperEngine._quantize_book(w, opens)` builds the quantized weight panel by reusing the scalar
  `sizing.quantize_weight` on the perp-available cells only (one quantization rule shared with the sizing
  feasibility script — no copy-paste). New `_live_returns_quantized(deployed_w)` mirrors the old
  `_live_returns` coverage-aware netting but on `q_w` (funding on quantized legs, cost on quantized turnover).
  `run_once` now books the LIVE track via `_live_returns_quantized`; PARITY + held computation untouched.
- Filters fetched ONCE at init (`sizing._filters()` live exchangeInfo, 69 perps) and cached; on any fetch
  failure the cache is `{}` and every lookup falls back to the verified-uniform `_DEFAULT_FILT`
  (`min_notional=5.0, step=0.01, min_qty=0.01`) — a brief outage never kills the desk.
- `_live_returns` (the continuous method) is deliberately KEPT unchanged (it's the pre-change reference and is
  guarded by the existing engine tests).

## Smoke ($10k, real on-disk data, TEMP scratch db — live DB untouched)
`[rebal] as_of=2026-06-30  gross=0.690  n_pos=68  legs=68  eq_parity=$12,040  eq_live=$10,881  basis_gap=$-1,159 (-1159bps, incl quant+basis+funding)  day_fund=$-0.52  cum_fund=$-31.05  (meta gross=0.691)`

| window | eq_parity | basis_gap CONTINUOUS (pre-change) | basis_gap QUANTIZED (new) | quantization drag |
|--------|-----------|-----------------------------------|---------------------------|-------------------|
| full perp window (launch 2026-01-28) | $12,040 | −1153.4 bps | **−1158.6 bps** | **−5.1 bps** |
| recent 20-bar (launch 2026-06-01) | $10,629 | −75.8 bps (≈ live −81bps snapshot) | **−78.5 bps** | **−2.7 bps** |

- Both eq tracks populate; the QUANTIZED basis_gap is MORE negative than the continuous one in both windows
  (quantization adds drag), and the recent-window continuous number (−75.8 bps) matches the live engine's
  ~−81 bps short-window snapshot. Quantization at $10k costs ~2–5 bps (window-dependent; it compounds).
- `tradfi_held_w` written = **68 continuous ideal weights** (PAYP excluded upstream, NOT re-normalized, NOT
  lot-rounded — e.g. SNDK +0.05704, PLTR −0.04086). PARITY/held CANNOT drift on quantization by construction.

## Digest / status
- `tradfi_digest.py`: adds "PARITY = signal (ideal book, must match backtest — the correctness check)" and
  "LIVE = executed (quantized fills + funding + basis on real perps, same realistic cost)", labels basis_gap
  "real execution gap (perp basis + funding + quantization; slippage is in BOTH tracks, not here)", and shows
  N legs quantized / dropped at $10k for the current book (reuses `quantize_weight`). READ-ONLY.
- `tradfi_status.py`: PARITY alert check UNCHANGED; added a comment that PARITY is a signal-fidelity check,
  deliberately pre-quantization, so lot-quantization can never make it drift.

## Tests / lint
`tests/test_tradfi_exec_model.py` (5 behaviors): (1) LIVE quantized but parity/held continuous; (2) sub-$5 leg
dropped from live yet present in held (no parity drift); (3) cost on quantized turnover at `ct.COST_SIDE` by
default (slippage not double-counted) + stress knob; (4) funding booked on quantized legs, correct sign;
(5) filter-fetch failure falls back to uniform default without raising. `uv run pytest
test_tradfi_exec_model + test_tradfi_paper_engine + test_tradfi_monitor + test_tradfi_basis_reconcile` = 30
passed (121 across all tradfi files). `ruff check` clean on every touched file.
