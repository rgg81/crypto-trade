import pandas as pd, numpy as np
from sweep import run
PG=("ret","size","liq")
PTS=[(81,126,72,4),(72,126,72,4),(90,126,72,4),(81,108,72,4),(81,144,72,4),(81,126,60,4),(81,126,84,4),(81,126,72,3),(81,126,72,5)]
def med_of(kinds,strict,wts=None):
    wts=wts or tuple(1.0 for _ in kinds)
    cfgs=[dict(kinds=kinds,weights=wts,purge=PG,cadence=1,phase=0,w=w,nb=nb,hold=h,k=k,strict=strict) for w,nb,h,k in PTS]
    df=run(cfgs,workers=9)
    m={c:float(df[c].median()) for c in ['sharpe1','sharpe2','ann1','vol','dd1','dd2','turn','edge_bps','worst_fold','median_fold','pq2','calmar2','short_gross','trades']}
    C=lambda x:min(1.,max(0.,x))
    G=(30*C((m['worst_fold']+.25)/1.)+20*C((m['median_fold']-.25)/.75)+20*C((.20-m['dd2'])/.15)+15*C(m['calmar2']/1.5)+8*C((m['pq2']-.5)/.375))
    return dict(kinds='+'.join(kinds),strict=strict,G=round(G,2),posfrac=float(((df.ann1>0)&(df.sharpe2>0)).mean()),
                **{k:round(v,4) for k,v in m.items()})
rows=[]
for kinds in (("bigp","imbsml"),("bigp","imbsml0"),("bigp","imbsmlm"),("bigp",),("imbsml0",),("imbsmlm",)):
    for st in ((False,True) if len(kinds)>1 else (False,)):
        rows.append(med_of(kinds,st))
pd.set_option('display.width',300); print(pd.DataFrame(rows).to_string(index=False))
