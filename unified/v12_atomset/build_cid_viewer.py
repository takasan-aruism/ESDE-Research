#!/usr/bin/env python3
"""v12 M5 — 全 CID 探索ビューア生成 (Taka: 集約も判定もしない、全データを掘れる形に)
全 n_core/全 CID/全 window/全指標(drift/exc/degree/n_partner/n_core/atom/生存)/全条件(A/C/F)。
同一 CID を条件跨ぎ(C/F/A 重ね)で。出力: 全 CID parquet + 自己完結 HTML viewer。
結論は出さない。Taka が自分の目で掘る。
"""
import pandas as pd, numpy as np, json
from pathlib import Path

R = Path('unified/v12_atomset/run_m5_core_long')   # Long(tracking50) A/C/F × seed0-7
OUT = Path('unified/v12_atomset/viewer'); OUT.mkdir(exist_ok=True)
SEEDS = range(8); CONDS = ['A', 'C', 'F']
METRICS = ['drift', 'exc', 'degree', 'n_partner', 'n_core']  # drift=phase_sig移動量
COLMAP = {'drift': 'atom_rate', 'exc': 'exc', 'degree': 'degree',
          'n_partner': 'n_partner_cids', 'n_core': 'n_core'}


def load(cond, s):
    return pd.read_parquet(R / f'core_st1/{cond}/seed{s}/records.parquet')


# 1) 全 CID 長形式データ (parquet/csv、Taka が pandas/excel で掘れる)
allrows = []
for cond in CONDS:
    for s in SEEDS:
        d = load(cond, s)
        for r in d.itertuples():
            allrows.append(dict(cond=cond, seed=int(s), cid=int(r.cid), window=int(r.window),
                                drift=float(r.atom_rate), exc=float(r.exc), degree=int(r.degree),
                                n_partner=int(r.n_partner_cids), n_core=int(r.n_core), atom=r.atom))
df = pd.DataFrame(allrows)
df.to_parquet(OUT / 'all_cids_long.parquet')
df.to_csv(OUT / 'all_cids_long.csv', index=False)
ng = df.groupby(['seed', 'cid']).ngroups
print(f'全データ: {len(df)} 行, {ng} 個の (seed,cid), 保存: viewer/all_cids_long.parquet+csv')

# 2) 同一 CID を C/F/A 重ねられる per-(seed,cid) trajectory JSON
traj = {}; index = []
for (s, cid), g0 in df.groupby(['seed', 'cid']):
    key = f's{s}_c{cid}'
    entry = {'seed': int(s), 'cid': int(cid)}
    nc = int(g0.n_core.median())
    entry['n_core'] = nc
    for cond in CONDS:
        gc = g0[g0.cond == cond].sort_values('window')
        if len(gc):
            entry[cond] = {'w': gc.window.tolist(),
                           **{m: gc[m].round(3).tolist() for m in METRICS}}
        else:
            entry[cond] = {'w': []}
    # 並べ替え用メタ
    lifeC = len(entry['C']['w']); lifeF = len(entry['F']['w']); lifeA = len(entry['A']['w'])
    mdC = max(entry['C'].get('drift', [0]) or [0]); mdF = max(entry['F'].get('drift', [0]) or [0])
    atomC = (g0[g0.cond == 'C'].atom.iloc[0] if lifeC else (g0.atom.iloc[0] if len(g0) else ''))
    entry['meta'] = {'life_A': lifeA, 'life_C': lifeC, 'life_F': lifeF,
                     'maxdrift_C': round(mdC, 3), 'maxdrift_F': round(mdF, 3), 'atom': atomC}
    traj[key] = entry
    index.append({'key': key, 'seed': int(s), 'cid': int(cid), 'n_core': nc,
                  'life_C': lifeC, 'life_F': lifeF, 'life_A': lifeA,
                  'maxdrift_C': round(mdC, 3), 'maxdrift_F': round(mdF, 3), 'atom': atomC})

# 3) 自己完結 HTML viewer (データ埋め込み、plotly CDN、CID選択で C/F/A 重ね、ソート/フィルタ)
html = '''<!doctype html><html><head><meta charset="utf-8">
<title>v12 Atomset CID Viewer (全CID 個別軌跡 A/C/F)</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
 body{font-family:monospace;margin:0;display:flex;height:100vh}
 #list{width:340px;overflow:auto;border-right:1px solid #ccc;padding:6px;font-size:12px}
 #plots{flex:1;overflow:auto;padding:8px}
 .row{cursor:pointer;padding:2px 4px;border-bottom:1px solid #eee;white-space:nowrap}
 .row:hover{background:#eef} .row.sel{background:#cdf}
 #ctrl{padding:4px;font-size:12px} .panel{height:230px}
 th{cursor:pointer;position:sticky;top:0;background:#ddd}
 table{border-collapse:collapse;width:100%} td,th{padding:1px 4px;text-align:right}
 td:first-child,th:first-child{text-align:left}
</style></head><body>
<div id="list">
 <div id="ctrl">
  n_core: <select id="fnc"><option value="">all</option><option>2</option><option>3</option><option>4</option><option>5</option></select>
  sort: <select id="srt">
   <option value="maxdrift_C">maxdrift_C</option><option value="life_C">life_C</option>
   <option value="life_F">life_F</option><option value="n_core">n_core</option>
   <option value="dlife">life_C-life_F</option><option value="seed">seed</option></select>
  <button id="dir">↓</button>
 </div>
 <table id="tbl"><thead><tr><th>seed/cid</th><th>nc</th><th>lifeC</th><th>lifeF</th><th>lifeA</th><th>mdC</th><th>mdF</th><th>atom</th></tr></thead><tbody></tbody></table>
</div>
<div id="plots"><h3 style="margin:4px">CID を左から選択 → A(灰)/C(青=自分の経験で核drift)/F(赤=他人の) を重ねて表示</h3>
 <div id="p_drift" class="panel"></div><div id="p_exc" class="panel"></div>
 <div id="p_degree" class="panel"></div><div id="p_n_partner" class="panel"></div><div id="p_n_core" class="panel"></div>
</div>
<script>
const TRAJ=__TRAJ__; const IDX=__IDX__;
const METRICS=["drift","exc","degree","n_partner","n_core"];
const COL={A:"#999",C:"#15c",F:"#e33"};
let asc=false;
function render(){
 const nc=document.getElementById('fnc').value, srt=document.getElementById('srt').value;
 let rows=IDX.filter(r=>!nc||r.n_core==nc);
 rows.sort((a,b)=>{let av,bv; if(srt=='dlife'){av=a.life_C-a.life_F;bv=b.life_C-b.life_F}else{av=a[srt];bv=b[srt]} return (av-bv)*(asc?1:-1)});
 const tb=document.querySelector('#tbl tbody'); tb.innerHTML='';
 rows.forEach(r=>{const tr=document.createElement('tr');tr.className='row';
  tr.innerHTML=`<td>s${r.seed}c${r.cid}</td><td>${r.n_core}</td><td>${r.life_C}</td><td>${r.life_F}</td><td>${r.life_A}</td><td>${r.maxdrift_C}</td><td>${r.maxdrift_F}</td><td>${r.atom}</td>`;
  tr.onclick=()=>{document.querySelectorAll('.row').forEach(x=>x.classList.remove('sel'));tr.classList.add('sel');show(r.key)};tb.appendChild(tr)});
}
function show(key){const e=TRAJ[key];
 METRICS.forEach(m=>{const tr=[];['A','C','F'].forEach(c=>{const d=e[c];if(d&&d.w&&d.w.length)tr.push({x:d.w,y:d[m],name:c,mode:'lines+markers',line:{color:COL[c]},marker:{size:4}})});
  Plotly.newPlot('p_'+m,tr,{title:`CID s${e.seed}c${e.cid} n_core=${e.n_core} ${e.meta.atom} : ${m}`,margin:{t:28,b:24,l:40,r:8},showlegend:true,height:225},{displayModeBar:false})});
}
document.getElementById('fnc').onchange=render;
document.getElementById('srt').onchange=render;
document.getElementById('dir').onclick=()=>{asc=!asc;document.getElementById('dir').textContent=asc?'↑':'↓';render()};
render();
</script></body></html>'''
html = html.replace('__TRAJ__', json.dumps(traj, separators=(',', ':')))
html = html.replace('__IDX__', json.dumps(index, separators=(',', ':')))
(OUT / 'cid_viewer.html').write_text(html)
sz = (OUT / 'cid_viewer.html').stat().st_size / 1e6
print(f'viewer: viewer/cid_viewer.html ({sz:.1f}MB, {len(index)} CID, ブラウザで開く)')
print('  使い方: 左で n_core フィルタ/ソート → CID クリック → A灰/C青/F赤 の軌跡が drift/exc/degree/n_partner/n_core で重なる')
