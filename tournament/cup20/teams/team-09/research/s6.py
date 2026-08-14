import time, pandas as pd, numpy as np
from sweep import run
purges=[(),("ret",),("size",),("liq",),("size","liq"),("ret","size"),("ret","size","liq")]
cfgs=[]
for kind in ("bigp","lvl","per"):
    for pg in purges:
        for hold in (42,63,90):
            for k in (5,6):
                cfgs.append(dict(kinds=(kind,),weights=(1.0,),w=90,purge=pg,k=k,hold=hold,cadence=1,phase=0))
print(len(cfgs)); t=time.time(); df=run(cfgs,workers=16,out='sweep_ablate.csv'); print('%.0fs'%(time.time()-t))
pd.set_option('display.width',270)
df['pg']=df['purge'].astype(str)
print(df.groupby(['kinds','pg'])[['sharpe1','sharpe2','G','worst_fold','f1','f2','f3','f4','dd2','turn','short_gross']].mean().round(3).to_string())
