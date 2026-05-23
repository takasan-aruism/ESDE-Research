#!/usr/bin/env python3
"""v1105 Step E — 観察 3: 両段の強度マップ (11 数値別レイヤー保持)

設計書 v4 §2.4 案 B 通り、scope × stratum を行、11 数値を別レイヤー列で並列保持。
binary 判定なし、閾値なし、単一スコア化なし (絶対格言 #11 厳密適用)。

11 数値:
  段 4-b (3 数値): ① genesis_lift_C  ② couple_hit_rate_unweighted
                   ③ couple_hit_rate_prob_weighted
  段 4-c trajectory (2 数値): ④ traj_r_stability_vs_maxprob
                              ⑤ traj_r_diffusion_vs_maxprob
  段 4-c density (6 数値): ⑥-⑪ density r (3 density × 2 sim_basis、response=max_prob)

入力 (read-only):
  - unified/v1105/outputs/main/observation_1_terrain_4b.parquet (Step C 出力)
  - unified/v1105/outputs/main/observation_2_terrain_4c.parquet (Step D 出力)
  - unified/v1104a/outputs/main/observation_2_scope_stratified.parquet (Genesis lift_C scope-level)

出力:
  - unified/v1105/outputs/main/observation_3_intensity_map.parquet
    (per stratum で 11 数値別レイヤー)
  - unified/v1105/outputs/v1105_intensity_map.html
    (4 panel heatmap、各 layer 別 colorscale)
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPO_ROOT = Path('/home/takasan/esde/ESDE-Research')
V1104A_MAIN = REPO_ROOT / 'unified/v1104a/outputs/main'
V1105_MAIN = REPO_ROOT / 'unified/v1105/outputs/main'
V1105_OUT = REPO_ROOT / 'unified/v1105/outputs'

STRATA_ORDER = [
    'ESDE_event', 'ESDE_step10', 'ESDE_window', 'ESDE_all',
    'CID_n=2', 'CID_n=3', 'CID_n=4', 'CID_n=5', 'CID_n=6+', 'CID_all',
    'alpha_all', 'beta_all',
]


def main():
    V1105_MAIN.mkdir(parents=True, exist_ok=True)
    V1105_OUT.mkdir(parents=True, exist_ok=True)
    print('=== v1105 Step E 観察 3: 両段の強度マップ (11 数値別レイヤー) ===')
    t0 = time.time()

    o1 = pd.read_parquet(V1105_MAIN / 'observation_1_terrain_4b.parquet')
    o2 = pd.read_parquet(V1105_MAIN / 'observation_2_terrain_4c.parquet')
    gen_strat = pd.read_parquet(V1104A_MAIN / 'observation_2_scope_stratified.parquet')
    print(f'observation_1 (Step C): {len(o1)} rows')
    print(f'observation_2 (Step D): {len(o2)} rows')
    print(f'genesis scope_stratified (v1104a): {len(gen_strat)} rows')

    # --- (1) Genesis lift_C: stratum 別に集約 ---
    # CID 全 self-loop / alpha/beta 部分 self-loop / ESDE 部分 self-loop
    # shuffle_type='C' のみ、is_full_self_loop=False は non-self-loop の代表値、True は self-loop
    g = gen_strat[gen_strat['shuffle_type'] == 'C'].copy()
    # scope-level 集約: CID 全 (self-loop only)、ESDE 3 解像度、alpha/beta 全
    lift_C_map = {}
    # ESDE 3 解像度
    for esde in ['ESDE_event', 'ESDE_step10', 'ESDE_window']:
        sub = g[g['change_scope'] == esde]
        if len(sub) > 0:
            # non-self-loop と self-loop の chain 数加重平均
            w = sub['n_chains']
            lift_C_map[esde] = (sub['lift_mean'] * w).sum() / w.sum() if w.sum() > 0 else np.nan
    # ESDE_all = 3 解像度の chain 数加重平均
    esde_sub = g[g['change_scope'].str.startswith('ESDE')]
    w = esde_sub['n_chains']
    lift_C_map['ESDE_all'] = (esde_sub['lift_mean'] * w).sum() / w.sum() if w.sum() > 0 else np.nan
    # CID 全 (100% self-loop): n_size_bin 別の値
    cid_sub = g[g['change_scope'] == 'CID']
    for n_label in ['CID_n=2', 'CID_n=3', 'CID_n=4', 'CID_n=5+']:
        nb = cid_sub[cid_sub['n_size_bin'] == n_label]
        if len(nb) > 0:
            # CID_n=5+ は v1104a の n_size_bin 名 (Language receiver_bin の CID_n=5 / CID_n=6+ と命名差異)
            key = n_label.replace('CID_n=5+', 'CID_n=5')  # 暫定 mapping、CID_n=6+ は CID_all から取得
            lift_C_map[key] = float(nb['lift_mean'].iloc[0])
    # CID_n=6+ は v1104a n_size_bin が CID_n=5+ に集約されているため CID_n=5+ 値を併用
    if 'CID_n=5+' in cid_sub['n_size_bin'].unique():
        v = float(cid_sub[cid_sub['n_size_bin'] == 'CID_n=5+']['lift_mean'].iloc[0])
        lift_C_map.setdefault('CID_n=5', v)
        lift_C_map['CID_n=6+'] = v  # v1104a 命名差異の架橋: CID_n=5+ → Language CID_n=5/6+ 両方に同値
    # CID_all = CID 全 chain 加重平均
    w = cid_sub['n_chains']
    lift_C_map['CID_all'] = (cid_sub['lift_mean'] * w).sum() / w.sum() if w.sum() > 0 else np.nan
    # alpha/beta scope 集約 (self-loop + non-self-loop 加重平均)
    for sc in ['alpha', 'beta']:
        sub = g[g['change_scope'] == sc]
        w = sub['n_chains']
        lift_C_map[f'{sc}_all'] = (sub['lift_mean'] * w).sum() / w.sum() if w.sum() > 0 else np.nan
    print(f'Genesis lift_C per stratum: {sorted(lift_C_map.keys())}')

    # --- (2) Language couple_hit_rate per stratum ---
    # observation_1_terrain_4b は per (receiver_bin, change_metric_type) で値あり
    # stratum 単位に集約
    couple_uw_map = {}; couple_pw_map = {}
    for esde in ['ESDE_event', 'ESDE_step10', 'ESDE_window']:
        sub = o1[o1['receiver_bin'] == esde]
        couple_uw_map[esde] = sub['language_couple_hit_rate_unweighted'].mean()
        couple_pw_map[esde] = sub['language_couple_hit_rate_prob_weighted'].mean()
    couple_uw_map['ESDE_all'] = o1[o1['scope'] == 'ESDE']['language_couple_hit_rate_unweighted'].mean()
    couple_pw_map['ESDE_all'] = o1[o1['scope'] == 'ESDE']['language_couple_hit_rate_prob_weighted'].mean()
    for cn in ['CID_n=2', 'CID_n=3', 'CID_n=4', 'CID_n=5', 'CID_n=6+']:
        sub = o1[o1['receiver_bin'] == cn]
        couple_uw_map[cn] = sub['language_couple_hit_rate_unweighted'].mean()
        couple_pw_map[cn] = sub['language_couple_hit_rate_prob_weighted'].mean()
    couple_uw_map['CID_all'] = o1[o1['scope'] == 'CID']['language_couple_hit_rate_unweighted'].mean()
    couple_pw_map['CID_all'] = o1[o1['scope'] == 'CID']['language_couple_hit_rate_prob_weighted'].mean()
    couple_uw_map['alpha_all'] = o1[o1['scope'] == 'alpha']['language_couple_hit_rate_unweighted'].mean()
    couple_pw_map['alpha_all'] = o1[o1['scope'] == 'alpha']['language_couple_hit_rate_prob_weighted'].mean()
    couple_uw_map['beta_all'] = o1[o1['scope'] == 'beta']['language_couple_hit_rate_unweighted'].mean()
    couple_pw_map['beta_all'] = o1[o1['scope'] == 'beta']['language_couple_hit_rate_prob_weighted'].mean()

    # --- (3) trajectory r 2 種 + density r 6 種: observation_2_terrain_4c から ---
    # response=max_prob のみ (設計書 §2.4)
    o2_mp = o2[o2['response'] == 'response_max_prob']
    traj_stab_map = {}; traj_diff_map = {}
    density_maps = {f'density_r_{lc}': {} for lc, in [
        ('raw_density_raw',), ('raw_density_norm',),
        ('qweighted_density_raw',), ('qweighted_density_norm',),
        ('const_adjusted_density_raw',), ('const_adjusted_density_norm',),
    ]}
    for stratum in STRATA_ORDER:
        sub = o2_mp[o2_mp['stratum'] == stratum]
        traj_stab_map[stratum] = float(sub[sub['predictor'] == 'traj_stability_mean']['pearson_r'].iloc[0]) \
            if len(sub[sub['predictor'] == 'traj_stability_mean']) > 0 else np.nan
        traj_diff_map[stratum] = float(sub[sub['predictor'] == 'diffusion_ratio_mean']['pearson_r'].iloc[0]) \
            if len(sub[sub['predictor'] == 'diffusion_ratio_mean']) > 0 else np.nan
        for dens_layer in ['raw_density_raw', 'raw_density_norm',
                            'qweighted_density_raw', 'qweighted_density_norm',
                            'const_adjusted_density_raw', 'const_adjusted_density_norm']:
            sub_d = sub[sub['predictor'] == dens_layer]
            density_maps[f'density_r_{dens_layer}'][stratum] = float(sub_d['pearson_r'].iloc[0]) \
                if len(sub_d) > 0 else np.nan

    # --- (4) 統合: 12 stratum × 11 数値別レイヤー ---
    rows = []
    for stratum in STRATA_ORDER:
        rows.append({
            'stratum': stratum,
            # 段 4-b
            'genesis_lift_C': lift_C_map.get(stratum, np.nan),
            'couple_hit_rate_unweighted': couple_uw_map.get(stratum, np.nan),
            'couple_hit_rate_prob_weighted': couple_pw_map.get(stratum, np.nan),
            # 段 4-c trajectory
            'traj_r_stability_vs_maxprob': traj_stab_map.get(stratum, np.nan),
            'traj_r_diffusion_vs_maxprob': traj_diff_map.get(stratum, np.nan),
            # 段 4-c density 6 種
            'density_r_raw_density_raw': density_maps['density_r_raw_density_raw'].get(stratum, np.nan),
            'density_r_raw_density_norm': density_maps['density_r_raw_density_norm'].get(stratum, np.nan),
            'density_r_qweighted_density_raw': density_maps['density_r_qweighted_density_raw'].get(stratum, np.nan),
            'density_r_qweighted_density_norm': density_maps['density_r_qweighted_density_norm'].get(stratum, np.nan),
            'density_r_const_adjusted_density_raw': density_maps['density_r_const_adjusted_density_raw'].get(stratum, np.nan),
            'density_r_const_adjusted_density_norm': density_maps['density_r_const_adjusted_density_norm'].get(stratum, np.nan),
        })
    df = pd.DataFrame(rows)
    out = V1105_MAIN / 'observation_3_intensity_map.parquet'
    df.to_parquet(out, index=False)
    print(f'\nwrote {out.name} ({len(df)} strata × 11 layers + stratum, elapsed {time.time()-t0:.1f}s)')
    print(df.round(3).to_string(index=False))

    # --- (5) heatmap 4 panel + parquet 本体 ---
    layers = [
        ('段 4-b: Genesis lift_C', ['genesis_lift_C'], 'RdBu', 0),
        ('段 4-b: Language couple_hit_rate', ['couple_hit_rate_unweighted',
                                                  'couple_hit_rate_prob_weighted'], 'Viridis', None),
        ('段 4-c: trajectory r (response=max_prob)', ['traj_r_stability_vs_maxprob',
                                                          'traj_r_diffusion_vs_maxprob'], 'RdBu', 0),
        ('段 4-c: density r (6 種、response=max_prob)', [
            'density_r_raw_density_raw', 'density_r_raw_density_norm',
            'density_r_qweighted_density_raw', 'density_r_qweighted_density_norm',
            'density_r_const_adjusted_density_raw', 'density_r_const_adjusted_density_norm',
        ], 'RdBu', 0),
    ]
    fig = make_subplots(rows=4, cols=1,
                        subplot_titles=[lay[0] for lay in layers],
                        vertical_spacing=0.05,
                        row_heights=[0.10, 0.20, 0.20, 0.50])
    for ri, (title, cols, cscale, zmid) in enumerate(layers, start=1):
        z = df[cols].values.T  # rows=cols (layer), columns=stratum
        text = [[f'{v:.3f}' if not np.isnan(v) else 'NaN' for v in row] for row in z]
        kwargs = dict(z=z, x=df['stratum'].tolist(), y=cols,
                       colorscale=cscale, text=text, texttemplate='%{text}',
                       textfont={'size': 10},
                       colorbar=dict(title='r' if ri >= 3 else
                                      ('lift' if ri == 1 else 'rate'),
                                       y={1: 0.93, 2: 0.78, 3: 0.58, 4: 0.25}[ri], len=0.15))
        if zmid is not None:
            kwargs['zmid'] = zmid
            kwargs['zmin'] = -1.0 if ri >= 3 else -0.3
            kwargs['zmax'] = 1.0 if ri >= 3 else 0.3
        fig.add_trace(go.Heatmap(**kwargs), row=ri, col=1)
        fig.update_xaxes(tickangle=-30, row=ri, col=1)

    fig.update_layout(
        height=1600, width=1700,
        title=('v11.0.5 (v1105) Step E 観察 3 強度マップ (11 数値別レイヤー保持、'
                '単一スコア化なし、判定なし)<br>'
                '<sub>段 4-b (Genesis predecessor + Language Couple) と '
                '段 4-c (trajectory + 48 次元密度 6 種) を scope × stratum で並列、'
                'binary 判定なし、scope 別の構造事実を Phase Result で読む</sub>'),
    )
    out_html = V1105_OUT / 'v1105_intensity_map.html'
    fig.write_html(out_html, include_plotlyjs='cdn')
    print(f'\nwrote {out_html.name} ({out_html.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
