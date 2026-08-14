import time, pandas as pd, numpy as np
from sweep import run
top=[("bigp",90,42,6),("perb",90,42,6),("perb",90,42,5),("per",90,42,5),("per",90,42,6),
     ("perbig",180,42,5),("bigp",90,21,6),("per",90,21,5),("bigp",90,9,5),("persml",21,42,5),
     ("lvl",180,42,5),("zfl",90,42,5)]
cfgs=[]
for kind,w,cad,k in top:
    for ph in range(cad):
        cfgs.append(dict(kinds=(kind,),weights=(1.0,),w=w,purge=("ret","size","liq"),
                         k=k,cadence=cad,phase=ph))
print(len(cfgs),'configs'); t=time.time()
df=run(cfgs,workers=14,out='sweep_phase.csv'); print('%.0fs'%(time.time()-t))
g=df.groupby(['kinds','w','cadence','k']).agg(
  S2_mean=('sharpe2','mean'),S2_min=('sharpe2','min'),S2_max=('sharpe2','max'),
  G_mean=('G','mean'),G_min=('G','min'),G_max=('G','max'),
  wf_mean=('worst_fold','mean'),turn=('turn','mean'),dd2=('dd2','mean'),vol=('vol','mean'),
  edge=('edge_bps','mean'),n=('G','size')).reset_index().sort_values('G_mean',ascending=False)
pd.set_option('display.width',260); print(g.to_string(index=False))
