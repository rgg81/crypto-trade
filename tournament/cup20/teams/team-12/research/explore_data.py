"""IS snapshot shape: what is actually in the data root."""
import pandas as pd
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start

snap = load_snapshot("data/cup20/is")
print("manifest", snap.manifest_sha256[:16])
for name in ("bars", "funding", "mark_prices", "membership", "contract_metadata"):
    f = getattr(snap, name)
    print(f"\n== {name} == rows={len(f)}")
    print(list(f.columns))
    print(f.head(2).to_string())
is_start = resolve_is_start(snap.membership)
print("\nIS_START:", is_start)
b = snap.bars
b["open_time"] = pd.to_datetime(b["open_time"], utc=True)
print("bars span", b.open_time.min(), b.open_time.max(), "symbols", b.symbol.nunique())
m = snap.membership
m["reconstitution_time"] = pd.to_datetime(m["reconstitution_time"], utc=True)
print("membership boundaries", m.reconstitution_time.nunique(),
      m.reconstitution_time.min(), m.reconstitution_time.max())
print("distinct members ever", m.symbol.nunique())
print(sorted(m.symbol.unique()))
f = snap.funding
f["funding_time"] = pd.to_datetime(f["funding_time"], utc=True)
print("funding span", f.funding_time.min(), f.funding_time.max(), "syms", f.symbol.nunique())
print("funding interval hours value counts:")
print(f["funding_interval_hours"].value_counts() if "funding_interval_hours" in f else "n/a")
