import sys; sys.path.insert(0, "tournament/cup20/teams/team-07/research")
import numpy as np, pandas as pd
from strat import data
from sim2 import simulate, reference_scalars, metrics, dec

p = data(); g=p["grid"]; fr=p["funding"]; op=p["open"]; ok=p["ok"]; r8 = op.pct_change()
CACHE={}

def build(cl, rl, ns, cad, lam=0.0, kl=63, sym=False, ph=0):
    key=(cl,rl,ns,cad,lam,kl,sym,ph)
    if key in CACHE: return CACHE[key]
    C = fr.rolling(cl, min_periods=max(2,cl//2)).mean().shift(1).where(ok).to_numpy()
    Rk = r8.rolling(rl, min_periods=max(4,rl//2)).std().shift(1).where(ok).to_numpy()
    K = fr.gt(1e-4).rolling(kl, min_periods=max(2,kl//2)).mean().shift(1).where(ok).to_numpy()
    OK = ok.to_numpy(); n=C.shape[1]; out=[]
    for i in range(len(g)):
        if (i % cad) != (ph % cad): out.append(None); continue
        c, r, k, o = C[i], Rk[i], K[i], OK[i]
        v = o & np.isfinite(c) & np.isfinite(r) & (r>0) & np.isfinite(k)
        if int(v.sum()) < 2*ns+2: out.append(None); continue
        idx = np.where(v)[0]
        sc = (c[idx]-np.median(c[idx]))/r[idx]
        desc = idx[np.argsort(-sc)]
        ss = desc[:ns]; ls = desc[::-1][:ns]
        w = np.zeros(n)
        w[ls] = 1.0/r[ls]; w[ss] = -1.0/r[ss]
        if lam > 0:
            w[ss] *= np.clip(1.0 - lam*k[ss], 0.0, 1.0)
            if sym: w[ls] *= np.clip(1.0 - lam*(1.0-k[ls]), 0.0, 1.0)
        pos=w>0; neg=w<0
        if not pos.any() or not neg.any(): out.append(None); continue
        w[pos]/=w[pos].sum(); w[neg]/=-w[neg].sum()
        out.append(w)
    CACHE[key]=out; return out

def one(cl,rl,ns,cad,**kw):
    tl=build(cl,rl,ns,cad,**kw)
    ref,_=simulate(tl,p["fwd_price"],p["fwd_fund"],1.0)
    sc=reference_scalars(ref,g)
    r1,tr=simulate(tl,p["fwd_price"],p["fwd_fund"],1.0,sc)
    r2,_=simulate(tl,p["fwd_price"],p["fwd_fund"],2.0,sc)
    m1,m2=metrics(r1,tr),metrics(r2,tr)
    return {"wf":m2["worst_fold"],"mf":m2["median_fold"],"dd":m2["maxdd"],"cal":m2["calmar"],
            "pq":m2["pos_q"],"sh1":m1["sharpe"],"sh2":m2["sharpe"],"vol":m1["vol"],
            "turn":m1["turn_ann"],"trades":tr,"ret1":m1["ann_ret"],
            "gedge":r1["gross"].sum()/r1["turnover"].sum()*1e4,
            "pos": 1.0 if (m1["ann_ret"]>0 and m2["sharpe"]>0) else 0.0}

def Gof(m):
    return (30*dec((m["wf"]+0.25)/1.0)+20*dec((m["mf"]-0.25)/0.75)+20*dec((0.20-m["dd"])/0.15)
            +15*dec(m["cal"]/1.5)+8*dec((m["pq"]-0.50)/0.375))

def nbhd(cl,rl,ns,cad,**kw):
    pts=[(cl,rl,ns),(cl-15,rl,ns),(cl+21,rl,ns),(cl,rl-15,ns),(cl,rl+21,ns),(cl,rl,ns-1),(cl,rl,ns+1)]
    res=[one(a,b,c,cad,**kw) for a,b,c in pts]
    med={k:float(np.median([r[k] for r in res])) for k in res[0]}
    med["G"]=Gof(med); med["posfrac"]=float(np.mean([r["pos"] for r in res]))
    return med,res

print("continuous crowding penalty on the SHORT sleeve: w *= (1 - lam * premium_duration)")
print(f"{'cad':>4} {'lam':>5} {'Gmed':>6} {'Gnom':>6} {'wf':>6} {'mf':>6} {'dd':>6} {'sh1':>5} {'sh2':>5} "
      f"{'vol':>6} {'turn':>6} {'gedge':>6} {'trades':>7} {'pos%':>5}")
for cad in (1,3,6):
    for lam in (0.0,0.2,0.4,0.5,0.6,0.8,1.0):
        med,res=nbhd(63,63,7,cad,lam=lam)
        print(f"{cad:>4} {lam:5.2f} {med['G']:6.1f} {Gof(res[0]):6.1f} {med['wf']:+6.2f} {med['mf']:+6.2f} "
              f"{med['dd']:6.1%} {med['sh1']:+5.2f} {med['sh2']:+5.2f} {med['vol']:6.1%} {med['turn']:6.1f} "
              f"{med['gedge']:6.1f} {int(med['trades']):7d} {med['posfrac']:5.2f}")
    print()
print("symmetric penalty (also on the long sleeve), cadence 3:")
for lam in (0.0,0.4,0.6,0.8):
    med,res=nbhd(63,63,7,3,lam=lam,sym=True)
    print(f"  lam={lam:4.2f} Gmed={med['G']:6.1f} wf={med['wf']:+.2f} mf={med['mf']:+.2f} dd={med['dd']:.1%} sh1={med['sh1']:+.2f}")
print("\ncrowd lookback sensitivity at cadence 3, lam=0.6:")
for kl in (21,42,63,90,126,189):
    med,res=nbhd(63,63,7,3,lam=0.6,kl=kl)
    print(f"  crowd_lb={kl:4d} Gmed={med['G']:6.1f} wf={med['wf']:+.2f} mf={med['mf']:+.2f} dd={med['dd']:.1%} sh1={med['sh1']:+.2f}")

print("\n=== phase dispersion of the NEIGHBOURHOOD MEDIAN (lam=0.6) ===")
for cad in (2,3,4,6):
    gs=[]
    for ph in range(cad):
        med,res=nbhd(63,63,7,cad,lam=0.6,ph=ph)
        gs.append(med["G"])
    print(f"cad={cad}: Gmed by phase = " + " ".join(f"{x:6.1f}" for x in gs) +
          f"   mean={np.mean(gs):6.1f} sd={np.std(gs):5.1f} min={min(gs):6.1f}")

print("\n=== 9-point neighbourhood (adds CROWDING_PENALTY +-0.2) ===")
def nbhd9(cl,rl,ns,cad,lam,kl=63,ph=0):
    pts=[(cl,rl,ns,lam),(cl-15,rl,ns,lam),(cl+21,rl,ns,lam),(cl,rl-15,ns,lam),(cl,rl+21,ns,lam),
         (cl,rl,ns-1,lam),(cl,rl,ns+1,lam),(cl,rl,ns,lam-0.2),(cl,rl,ns,lam+0.2)]
    res=[one(a,b,c,cad,lam=d,kl=kl,ph=ph) for a,b,c,d in pts]
    med={k:float(np.median([r[k] for r in res])) for k in res[0]}
    med["G"]=Gof(med); med["posfrac"]=float(np.mean([r["pos"] for r in res]))
    return med,res
for cad in (1,3,6):
    for lam in (0.4,0.6,0.8):
        med,res=nbhd9(63,63,7,cad,lam)
        print(f"cad={cad} lam={lam}: Gmed={med['G']:6.1f} Gnom={Gof(res[0]):6.1f} wf={med['wf']:+.2f} "
              f"mf={med['mf']:+.2f} dd={med['dd']:.1%} cal={med['cal']:+.2f} pq={med['pq']:.2f} "
              f"sh1={med['sh1']:+.2f} sh2={med['sh2']:+.2f} vol={med['vol']:.1%} turn={med['turn']:.1f} "
              f"trades={int(med['trades'])} pos%={med['posfrac']:.2f}")

print("\n=== 9-point neighbourhood median by cadence AND phase (lam=0.6) ===")
for cad in (1,2,3,4,6):
    row=[]
    for ph in range(cad):
        med,res=nbhd9(63,63,7,cad,0.6,ph=ph)
        row.append((med["G"], med["wf"], med["sh1"], med["turn"], med["gedge"], int(med["trades"]), med["vol"]))
    gs=[r[0] for r in row]
    print(f"cad={cad}: Gmed by phase = " + " ".join(f"{x:6.1f}" for x in gs) +
          f"  mean={np.mean(gs):6.1f} sd={np.std(gs):5.1f} min={min(gs):6.1f} | "
          f"wf={np.mean([r[1] for r in row]):+.2f} sh1={np.mean([r[2] for r in row]):+.2f} "
          f"turn={np.mean([r[3] for r in row]):.1f} gedge={np.mean([r[4] for r in row]):.1f} "
          f"trades={int(np.mean([r[5] for r in row]))} vol={np.mean([r[6] for r in row]):.1%}")
