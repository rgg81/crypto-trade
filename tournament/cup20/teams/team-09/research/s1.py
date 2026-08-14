import itertools, time, pandas as pd, numpy as np
from sweep import run
cfgs=[]
for kind in ("per","perb","lvl","zfl","bigp","perbig","persml"):
    for w in (21,42,90,180):
        for cad in (9,21,42,63):
            for k in (5,6):
                cfgs.append(dict(kinds=(kind,),weights=(1.0,),w=w,purge=("ret","size","liq"),
                                 k=k,cadence=cad,phase=0))
print(len(cfgs),'configs')
t=time.time(); df=run(cfgs,workers=12,out='sweep_s1.csv'); print('%.0fs'%(time.time()-t))
pd.set_option('display.width',260)
cols=['kinds','w','cadence','k','sharpe1','sharpe2','vol','dd2','turn','edge_bps','worst_fold','median_fold','pq2','G','long_gross','short_gross']
print(df.sort_values('G',ascending=False).head(25)[cols].to_string(index=False))
print()
print(df.groupby('kinds')[['sharpe2','G','worst_fold']].mean().sort_values('G',ascending=False).to_string())
