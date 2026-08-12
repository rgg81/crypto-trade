import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np
exec(open("tournament/cup20/teams/team-07/research/exp14.py").read().split("print(\"continuous")[0])
print("7-point neighbourhood median (carry_lb, risk_lb, n_side vary; lam FIXED) by cadence x lam")
for cad in (1,2,3,6):
    row=[]
    for lam in (0.0,0.2,0.4,0.6,0.8,1.0):
        gs=[]
        for ph in range(cad):
            med,res=nbhd(63,63,7,cad,lam=lam,ph=ph)
            gs.append(med["G"])
        row.append((lam, np.mean(gs), np.std(gs)))
    print(f"cad={cad}: " + "  ".join(f"lam{l:.1f}:{m:5.1f}(sd{s:4.1f})" for l,m,s in row))
