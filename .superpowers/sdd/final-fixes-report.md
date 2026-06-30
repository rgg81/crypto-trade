# Final Fixes Report — portfolio-tradfi branch

## FIX A — OOS leak in `perf_line` (`analysis/portfolio/tradfi/core_tradfi.py`)

### Before
```python
def perf_line(label: str, net: pd.Series, *, reveal_oos: bool = False) -> str:
    """One-line IS performance summary. OOS hidden unless reveal_oos=True (CONFIRMATION)."""
    eq = (1 + net).cumprod()
    parts = [
        f"  {label:18} IS_Sharpe={msharpe(net, LO0, OOS_CUTOFF):+.2f}",
        f"maxDD={maxdd(net) * 100:5.1f}%",
        f"netTot={(eq.iloc[-1] - 1) * 100:+.0f}%",
    ]
    if reveal_oos:
        parts.insert(2, f"OOS_Sharpe={msharpe(net, OOS_CUTOFF, HI1):+.2f}")
    return "  ".join(parts)
```
`maxDD` and `netTot` were computed over the FULL net series, leaking OOS information when `reveal_oos=False`.

### After
```python
def perf_line(label: str, net: pd.Series, *, reveal_oos: bool = False) -> str:
    """One-line IS performance summary. OOS hidden unless reveal_oos=True (CONFIRMATION).

    When reveal_oos is False, maxDD and netTot are computed over the IS-only slice too —
    not just IS_Sharpe — so an EXPLORATION run leaks NO OOS information.
    """
    src = net if reveal_oos else is_only(net)
    eq = (1 + src).cumprod()
    parts = [
        f"  {label:18} IS_Sharpe={msharpe(net, LO0, OOS_CUTOFF):+.2f}",
        f"maxDD={maxdd(src) * 100:5.1f}%",
        f"netTot={(eq.iloc[-1] - 1) * 100:+.0f}%",
    ]
    if reveal_oos:
        parts.insert(2, f"OOS_Sharpe={msharpe(net, OOS_CUTOFF, HI1):+.2f}")
    return "  ".join(parts)
```
`src = is_only(net)` when `reveal_oos=False`; both `maxDD` and `netTot` now computed IS-only.

---

## FIX B — New test locks the gate

Test appended to `tests/test_portfolio_tradfi_foundation.py`:

```python
def test_perf_line_hides_oos_by_default():
    idx = pd.date_range("2024-06-01", periods=500, freq="B")  # crosses 2025-03-24
    net = pd.Series(0.001, index=idx)  # steady positive so IS total < full total
    line = ct.perf_line("x", net)
    assert "OOS_Sharpe" not in line
    is_net = net[net.index < ct.OOS_CUTOFF]
    is_tot = ((1 + is_net).cumprod().iloc[-1] - 1) * 100
    full_tot = ((1 + net).cumprod().iloc[-1] - 1) * 100
    assert is_tot < full_tot  # proves OOS rows are excluded from the IS total
    assert f"netTot={is_tot:+.0f}%" in line
    assert "OOS_Sharpe" in ct.perf_line("x", net, reveal_oos=True)
```

### RED (without fix): `assert f"netTot={is_tot:+.0f}%" in line` fails because the old code uses the full series total (higher than IS-only total).
### GREEN (with fix): all 13 tests pass in 0.38s.

---

## FIX C — ruff E501 in `ingest_dukascopy_stocks.py:71`

### Before (111 chars)
```python
    vol_series = g["volume"].sum() if "volume" in h1.columns else pd.Series(0.0, index=g["open"].first().index)
```

### After (reflowed to ≤100 chars)
```python
    if "volume" in h1.columns:
        vol_series = g["volume"].sum()
    else:
        vol_series = pd.Series(0.0, index=g["open"].first().index)
```

### Ruff result
```
All checks passed!
```

---

## FIX D — Doc honesty: "2010" → "~2018+"

### `.claude/commands/portfolio-tradfi.md`
- Line ~31: `IS spans 2010+` → `IS spans ~2018+ (Dukascopy US-stock depth starts ~2018)`
- Line ~56: `The 2010+ IS therefore comes from` → `The ~2018+ IS therefore comes from`
- Lines ~59-60: `Backtest (2010+)` → `Backtest (~2018+)` + clarified note about Dukascopy depth
- Line ~114: `IS window = 2010+` → `IS window = ~2018+ (Dukascopy US-stock depth; covers 2020 COVID + 2022 bear)`

### `diary-portfolio-tradfi/EXPLORATION-001.md`
- Line ~14: `across 2010–2025-03` → `across ~2018-01 to 2025-03-23 (Dukascopy US-stock depth starts ~2018)`
- Line ~39: `IS (2010–2025-03-23)` → `IS (~2018-01 to 2025-03-23)`
- Line ~52: `Bull (2010–2019) | 2010-01 → 2019-12` → `Bull (2018–2019) | 2018-01 → 2019-12`

All-weather framing preserved: docs note that 2020 COVID crash and 2022 bear are still covered.

---

## Pytest result

```
.............                                                            [100%]
13 passed in 0.38s
```

---

## Commit SHA

(see git log after commit)
