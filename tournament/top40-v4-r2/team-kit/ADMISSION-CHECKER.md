# Exact score-blind admission checker

The organizer applies this contract to the complete batch before opening any score data. Start
from `templates/strategy.py`; change the causal signal, horizons, thresholds, sides, and risk
policy without changing its transparent construction pattern.

`admission-call-allowlist.json` is the machine-readable exact authority for the two call sets
printed below; activation tests require it to equal the organizer checker.

Inside `target_weights`, the only admitted direct function calls are:

`abs`, `all`, `any`, `dict`, `float`, `len`, `max`, `min`, `round`, `sorted`, and `sum`.

The only admitted method/attribute calls are:

`abs`, `all`, `any`, `array`, `asarray`, `astype`, `clip`, `copy`, `corr`, `corrcoef`, `cov`,
`diff`, `dropna`, `ewm`, `exp`, `fabs`, `fillna`, `head`, `isfinite`, `isin`, `isna`, `item`,
`log`, `log1p`, `max`, `maximum`, `mean`, `median`, `min`, `minimum`, `nanmean`, `nanmedian`,
`nanstd`, `nlargest`, `notna`, `nsmallest`, `pct_change`, `quantile`, `rank`, `reindex`,
`replace`, `rolling`, `shift`, `sign`, `sort_index`, `sort_values`, `sqrt`, `std`, `sum`, `tail`,
`to_numpy`, and `where`.

Attribute reads and indexing such as `frame.empty`, `frame["close"]`, `series.iloc[-1]`, and
`mapping[symbol]` are admitted. Do not substitute familiar but unlisted calls: in particular,
`Series`, `DataFrame`, `get`, `range`, `set`, `list`, `tuple`, `append`, `extend`, `values`,
`to_dict`, `argsort`, `logical_and`, `div`, `mul`, `gt`, `int`, and `enumerate` are rejected.

The complete syntactic limits in `RULES.md` also apply. Especially:

- exactly one `strategy.py`, one direct strategy class, one `target_weights`, and one factory;
- no helper functions, comprehensions, persistent state, `self` reads, decision-time reads,
  dynamic code, file/data loaders, RNG, module containers, or nonempty literal containers;
- only frozen operational column/option strings; at most 24 numeric literals, each bounded to six
  significant digits; and
- build dynamic dictionaries with an empty `{}` plus direct `mapping[key] = value` assignments.

Before writing the final batch outbox, compare every strategy with the template and search every
call expression against the two allowlists above. The organizer may return a bounded
`feedback/admission-<phase>-<attempt>.json` containing only deterministic score-blind
findings. Repair all findings before finishing; repair never contains scores or trial outcomes.
