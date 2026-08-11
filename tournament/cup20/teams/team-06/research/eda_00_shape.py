"""Team 06 EDA step 0 -- what is actually in the in-sample snapshot."""

from __future__ import annotations

import pandas as pd

ROOT = "data/cup20/is"

bars = pd.read_parquet(f"{ROOT}/bars.parquet")
funding = pd.read_parquet(f"{ROOT}/funding.parquet")
membership = pd.read_parquet(f"{ROOT}/membership.parquet")
marks = pd.read_parquet(f"{ROOT}/mark_prices.parquet")
meta = pd.read_parquet(f"{ROOT}/contract_metadata.parquet")

for name, frame in [
    ("bars", bars),
    ("funding", funding),
    ("membership", membership),
    ("marks", marks),
    ("meta", meta),
]:
    print(f"=== {name}: {frame.shape} ===")
    print(frame.dtypes.to_string())
    print(frame.head(3).to_string())
    print()

print("bars symbols:", bars["symbol"].nunique())
tcol = "open_time" if "open_time" in bars.columns else bars.columns[0]
print("bars time span:", bars[tcol].min(), bars[tcol].max())
print("membership cols:", list(membership.columns))
print(membership.head(25).to_string())
print("membership boundaries:", membership.iloc[:, 0].nunique())
print("distinct members:", membership["symbol"].nunique() if "symbol" in membership else "n/a")
