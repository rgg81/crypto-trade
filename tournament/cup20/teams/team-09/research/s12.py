import pandas as pd, numpy as np
from sweep import run
PG=("ret","size","liq")
rows=[]
for kinds in (("bigp","imbsml"),("bigp","imbsmlm")):
  for strict in (False,True):
    cfgs=[dict(kinds=kinds,weights=(1.,1.),purge=PG,cadence=1,phase=0,w=w,nb=nb,hold=h,k=k,strict=strict)
          for (w,nb,h,k) in [(81,126,72,4),(72,126,72,4),(90,126,72,4),(81,108,72,4),(81,144,72,4),
                             (81,126,60,4),(81,126,84,4),(81,126,72,3),(81,126,72,5)]]
    df=run(cfgs,workers=9)
    df['nom']=['NOMINEE']+['pt']*8
    med={c:float(df[c].median()) for c in ['sharpe1','sharpe2','sharpe3','ann1','vol','dd1','dd2','turn','edge_bps','worst_fold','median_fold','pq2','calmar2','short_gross','long_gross','trades']}
    C=lambda x: min(1.,max(0.,x))
    G=(30*C((med['worst_fold']+.25)/1.)+20*C((med['median_fold']-.25)/.75)+20*C((.20-med['dd2'])/.15)
       +15*C(med['calmar2']/1.5)+8*C((med['pq2']-.5)/.375))
    n=df.iloc[0]
    rows.append(dict(kinds='+'.join(kinds),strict=strict,G_med=round(G,2),
      posfrac=float(((df.ann1>0)&(df.sharpe2>0)).mean()),nom_S1=round(n.sharpe1,3),nom_S2=round(n.sharpe2,3),
      nom_wf=round(n.worst_fold,3),nom_G=round(n.G,2),**{('m_'+k):round(v,4) for k,v in med.items()}))
pd.set_option('display.width',300); print(pd.DataFrame(rows).to_string(index=False))
