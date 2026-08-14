import pandas as pd, numpy as np
from sweep import run
PG=("ret","size","liq"); K=("bigp","imbsml0"); W=(1.,1.)
def nb_points(w,nb,h,k,dw,dn,dh):
    return [(w,nb,h,k),(w-dw,nb,h,k),(w+dw,nb,h,k),(w,nb-dn,h,k),(w,nb+dn,h,k),
            (w,nb,h-dh,k),(w,nb,h+dh,k),(w,nb,h,k-1),(w,nb,h,k+1)]
def ev(nom,dw,dn,dh):
    P=nb_points(*nom,dw,dn,dh)
    cfgs=[dict(kinds=K,weights=W,purge=PG,cadence=1,phase=0,w=a,nb=b,hold=c,k=d,strict=True) for a,b,c,d in P]
    df=run(cfgs,workers=9)
    m={c:float(df[c].median()) for c in ['sharpe1','sharpe2','sharpe3','ann1','ann2','vol','dd1','dd2','turn','edge_bps','cost_share','worst_fold','median_fold','pq2','calmar2','short_gross','long_gross','trades']}
    C=lambda x:min(1.,max(0.,x))
    G=(30*C((m['worst_fold']+.25)/1.)+20*C((m['median_fold']-.25)/.75)+20*C((.20-m['dd2'])/.15)+15*C(m['calmar2']/1.5)+8*C((m['pq2']-.5)/.375))
    n=df.iloc[0]
    return dict(nom=nom,d=(dw,dn,dh),G=round(G,2),posfrac=float(((df.ann1>0)&(df.sharpe2>0)).mean()),
                worstpt_S2=round(df.sharpe2.min(),3),nomS1=round(n.sharpe1,3),nomS2=round(n.sharpe2,3),nom_wf=round(n.worst_fold,3),
                **{k:round(v,4) for k,v in m.items()})
CAND=[((81,126,72,4),9,18,12),((81,126,84,4),9,18,12),((90,126,72,4),9,18,12),((81,126,60,4),9,18,12),
      ((72,126,72,4),9,18,12),((81,108,72,4),9,18,12),((81,126,72,5),9,18,12),((90,126,84,4),9,18,12),
      ((81,126,72,4),12,24,18),((81,135,78,4),9,18,12)]
rows=[ev(*c) for c in CAND]
pd.set_option('display.width',300); print(pd.DataFrame(rows).sort_values('G',ascending=False).to_string(index=False))
