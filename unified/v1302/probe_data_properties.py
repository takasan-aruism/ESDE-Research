#!/usr/bin/env python3
"""v1302 設計監査 §2 — coherence 駆動性質 + structural-strength 分散の read-only データ点検（stdout のみ・ファイル非生成）。

【観察対象注釈ブロック / 同系・異系宣言】
- 同系内: 親 seed0 CID の縮小子系を想定した点検。異系対応でない。
- 読=frozen: per_subject_seed0 / v18_window_trajectory（v918 main）。書込なし（stdout のみ）。
- これは smoke でも実験 run でもない: child を1体も走らせない。既存 frozen データの分布を見るだけ。
- 親 physics/inject/ledger/state 非書込。
"""
import pandas as pd, numpy as np
REPO='/home/takasan/esde/ESDE-Research'
t=pd.read_csv(f'{REPO}/primitive/v918/diag_v918_main/selfread/v18_window_trajectory_seed0.csv')
b=pd.read_csv(f'{REPO}/primitive/v918/diag_v918_main/subjects/per_subject_seed0.csv')
b['cognitive_id']=pd.to_numeric(b['cognitive_id'],errors='coerce')
nc_map={int(k):str(v) for k,v in zip(b['cognitive_id'].dropna(),b['v11_m_c_n_core'])}
col='v18_v_unified_concentration_at_window_end'
t[col]=pd.to_numeric(t[col],errors='coerce')
t=t.dropna(subset=[col])
t['nc']=t['cid_id'].map(nc_map)

print('=== §2-1 coherence driver 性質 (seed0, v18_window_trajectory) ===')
print('rows', len(t), 'CIDs', t.cid_id.nunique())
g_all=t.groupby('cid_id').size()
print('per-CID 点数 min/med/max:', int(g_all.min()), int(g_all.median()), int(g_all.max()))
for nc in ['2','4','5']:
    sub=t[t.nc==nc]
    if len(sub)==0:
        print(f'  n{nc}: なし'); continue
    g=sub.groupby('cid_id')
    npts=g.size(); std=g[col].std().fillna(0)
    arc=((npts>=3)&(std>1e-3))
    print(f'  n{nc}: CID={sub.cid_id.nunique()} 点数med={int(npts.median())} 点数max={int(npts.max())} '
          f'弧あり(>=3pts&std>1e-3)={int(arc.sum())}/{len(npts)} ({round(100*arc.mean())}%)')

print()
print('=== §2-2 同 n_core 内分散 CV=std/|mean| (一意性が割れるか) ===')
def cv(s, col):
    x=pd.to_numeric(s[col],errors='coerce')
    return round(float(x.std()/(abs(x.mean())+1e-9)),3)
for nc in ['2','4','5']:
    s=b[b['v11_m_c_n_core']==nc]
    print(f'  n{nc}(N={len(s)}): B_gen_CV={cv(s,"v11_b_gen")} '
          f's_avg_CV={cv(s,"v11_m_c_s_avg")} r_core_CV={cv(s,"v11_m_c_r_core")} '
          f'conc_final_CV={cv(s,"v18_v_unified_concentration_final")} k_final_CV={cv(s,"v18_v_unified_k_final")}')
print('  注: B_gen_CV が小さく member 系(s_avg/r_core/conc)CV が大きいほど structural-strength の一意性が立つ')
