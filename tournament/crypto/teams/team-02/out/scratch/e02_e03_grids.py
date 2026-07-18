"""e02/e03 — engine grids: form A and form B over L, 1x and 2x cost tiers, k=1."""

from common import form_A, form_B, line, panels, score

pn, aux, scoring = panels()

for name, fn in (("A", lambda L: form_A(pn, aux, L, 0.6)), ("B", lambda L: form_B(pn, aux, L))):
    print(f"== form {name} (k=1) ==")
    for L in (3, 6, 9, 21, 42):
        sig = fn(L).fillna(0.0)
        _, _, _, m1 = score(sig)
        _, _, _, m2 = score(sig, cost_mult=2.0, slip_mult=2.0)
        print(line(f"{name} L={L:2d} @1x", m1))
        print(f"{'':34s} S2x={m2.sharpe:+.3f}")
