#!/usr/bin/env python3
"""v12 Atomset cid_align — STEP 1 (作り直し): trajectory エンコーダで cid_align 構築

## 作り直しの理由 (Web Claude 2 点指摘 → 実コードで確証)
旧 STEP 1 (m7) は run-end 版 v106_post_process.py のエンコーダを使った誤り。
正しいのは **trajectory 版** (v106_pulse_trajectory / v106_step10_trajectory):
- (1) ontological informational = cumulative_pulse_count (v106_pulse_trajectory.py:213)
      → v107 pulse event を累積で数えれば作れる → ontological 5/5。
- (2) epistemological_vec の入力は R_familiarity (同 L205-207)。v107 R_familiarity_pre と
      v105 pulse_log R_familiarity は完全同レンジ (min-5.787/max20.000) = 同一量。
      v106 も同じ境界 [10,30,60,150] で 99.97% level0 = degenerate だが、それが v106 の挙動。
      verbatim で使うのが v106 一致 (旧「写せない」は run-end の last_familiarity_max=count と
      取り違えた誤り)。
→ trajectory エンコーダ verbatim import で、8 軸フル + experience 2/3 を v107 から構築。

## 観察対象注釈ブロック
### 認識の核 (Taka 2026-06-15, 手放さない)
- Atom も CID も「10軸×下位levels=48」の大枠は共有、下位 level の厳密 1-1 対応は無い
  (両端人為的投影、神経-言語同様)。一致率の絶対値を信じない (本STEPでは測らない)。
### 物理非介入
- v107 source_events を読んで parquet を書くだけ。engine 回さず、θ/S/R/E/phase_sig/label.nodes 非書込。
### 使う軸 (v107 source_events から構築できる範囲, trajectory エンコーダ verbatim)
- temporal(lifespan_so_far) / scale(n_core_member) / epistemological(R_familiarity_pre, verbatim・大半 level0)
- ontological 5/5 (material=Q_remaining_at_window_end/q0, informational=cum_pulse, relational=cum_alpha,
  structural=n_core/7, semantic=C_at_window_end)
- interconnection(cum_alpha) / resonance(C_at_window_end) / lawfulness(pulse_density=cum_pulse/lifespan)
- value_generation 4/4 (functional=q_spent_so_far/q0, aesthetic=cum_ingest, ethical=cum_alpha, sacred=cum_beta)
- experience 2/3 (discovery=cum_ingest, comprehension=cum_pulse; creation=cum_q_spend_events は v107 に
  event 種無く 0)
### 使わない軸 (v107 source_events に field 無し, 別 source で追加可能・flag)
- symmetry: delta_social/stability/spread/familiarity は v105 pulse_log にあり (v107 source_events に無い)。
  join すれば追加可能 (要 Web Claude/Taka 判断)。本 STEP では 0。
### crown 禁止: 「個性化成立」「会話に繋がる」は書かない。
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

REPO = Path('/home/takasan/esde/ESDE-Research')
sys.path.insert(0, str(REPO / 'developmental/v106'))
from v106_pulse_trajectory import (  # noqa: E402  v106 trajectory エンコーダ verbatim
    temporal_vec, scale_vec, epistemological_vec, ontological_vec,
    interconnection_vec, resonance_vec, lawfulness_vec, experience_vec,
    value_generation_vec,
)

SRC_DIR = REPO / 'developmental/v107/outputs/main'
OUT_DIR = REPO / 'unified/v1201/run_step1b'
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_PER_CHUNK = 10
ALPHA = 0.3
MAD_C = 1.4826
Z_CLIP = 4.0
K_MIN = 3

# 48 次元レイアウト (v106 build_step10_cid_vector と同一軸順)
#  temporal7|scale6|epist5|ontol5|intercon5|reson4|symmetry5|lawful4|experience3|valuegen4 = 48
SYM0, SYM_W = 32, 5  # symmetry (本STEPでは0, pulse_log join で追加可能)


def build_vec48(row, seed_max):
    """v106 trajectory エンコーダ verbatim で 48 次元を組む。symmetry(idx32:37)のみ 0。"""
    parts = []
    parts += temporal_vec(row['lifespan_so_far'])                         # 7
    parts += scale_vec(row['n_core_member'])                              # 6
    parts += epistemological_vec(row.get('R_familiarity', 0))            # 5
    parts += ontological_vec(row, seed_max)                              # 5
    parts += interconnection_vec(row.get('cumulative_n_alphas', 0))      # 5
    parts += resonance_vec(row.get('C_at_window_end', 0))                # 4
    parts += [0.0] * SYM_W                                               # 5 symmetry=0 (delta_* 無)
    parts += lawfulness_vec(row.get('pulse_density_so_far', 0))          # 4
    parts += experience_vec(row)                                         # 3 (creation=0)
    parts += value_generation_vec(row, seed_max)                        # 4
    assert len(parts) == 48, len(parts)
    return np.array(parts, dtype=np.float64)


def robust_z_series(vecs):
    rm = np.zeros(vecs.shape[1])
    vals = []
    for t in range(len(vecs)):
        vals.append(np.linalg.norm(vecs[t] - rm) if t > 0 else 0.0)
        rm = rm + (vecs[t] - rm) / (t + 1)
    vals = np.array(vals)
    fs = np.zeros(len(vals))
    for t in range(K_MIN, len(vals)):
        w = vals[:t]
        med = np.median(w)
        mad = np.median(np.abs(w - med)) * MAD_C
        fs[t] = np.clip((vals[t] - med) / max(mad, 1e-3), -Z_CLIP, Z_CLIP)
    return np.abs(fs)


def process_seed(seed):
    df = pd.read_parquet(SRC_DIR / f'source_events_seed{seed}.parquet').sort_values('timestamp')
    df['q_spent_so_far'] = (pd.to_numeric(df['v14_q0'], errors='coerce')
                            - pd.to_numeric(df['Q_remaining_at_window_end'], errors='coerce')).clip(lower=0)
    # seed_max (offline, v107 全ストリームから — live で死んだ run-end 依存を解消)
    tot = df.groupby('source_cid')['event_source_type'].value_counts().unstack(fill_value=0)
    seed_max = {
        'cumulative_pulse_max': float(max(tot.get('pulse', pd.Series([1])).max(), 1)),
        'cumulative_n_alphas_max': float(max(tot.get('alpha_formation', pd.Series([1])).max(), 1)),
        'cumulative_n_betas_max': float(max(tot.get('beta_formation', pd.Series([1])).max(), 1)),
        'cumulative_n_ingestions_max': float(max(tot.get('ingestion', pd.Series([1])).max(), 1)),
        'C_max_seed': float(max(pd.to_numeric(df['C_at_window_end'], errors='coerce').max(), 1)),
    }
    rows = []
    for cid, g in df.groupby('source_cid'):
        g = g.sort_values('timestamp').reset_index(drop=True)
        cnt = {'pulse': 0, 'alpha_formation': 0, 'beta_formation': 0, 'ingestion': 0}
        recs = []
        for _, e in g.iterrows():
            et = e['event_source_type']
            if et in cnt:
                cnt[et] += 1
            ls = float(e['lifespan_so_far']) if not pd.isna(e['lifespan_so_far']) else 1.0
            row = {
                'lifespan_so_far': ls,
                'n_core_member': e['n_core_member'],
                'R_familiarity': e.get('R_familiarity_pre', 0),
                'v14_q0': e.get('v14_q0', 0),
                'Q_remaining_at_window_end': e.get('Q_remaining_at_window_end', 0),
                'C_at_window_end': e.get('C_at_window_end', 0),
                'q_spent_so_far': e.get('q_spent_so_far', 0),
                'cumulative_pulse_count': cnt['pulse'],
                'cumulative_n_alphas': cnt['alpha_formation'],
                'cumulative_n_betas': cnt['beta_formation'],
                'cumulative_n_ingestions': cnt['ingestion'],
                'cumulative_q_spend_events': 0,  # v107 に event 種無し (experience creation=0)
                'pulse_density_so_far': cnt['pulse'] / max(ls, 1.0),
            }
            recs.append((int(e['timestamp']), row,
                         int(e['n_core_member']) if not pd.isna(e['n_core_member']) else 0))
        vecs = np.array([build_vec48(r, seed_max) for _, r, _ in recs])
        fs = robust_z_series(vecs)
        align = vecs[0] / (np.linalg.norm(vecs[0]) + 1e-9)
        for t in range(len(recs)):
            ts, _, ncore = recs[t]
            ev = vecs[t] / (np.linalg.norm(vecs[t]) + 1e-9)
            align = align + ALPHA * fs[t] * ev
            align = align / (np.linalg.norm(align) + 1e-9)
            ch = ts // N_PER_CHUNK
            if rows and rows[-1]['seed'] == seed and rows[-1]['cid'] == int(cid) and rows[-1]['chunk'] == ch:
                rows[-1].update({f'a{j:02d}': float(align[j]) for j in range(48)})
                rows[-1]['n_events'] += 1
            else:
                rec = {'seed': seed, 'cid': int(cid), 'chunk': int(ch), 'gstep': int(ch) * N_PER_CHUNK,
                       'n_events': 1, 'n_core': ncore}
                rec.update({f'a{j:02d}': float(align[j]) for j in range(48)})
                rows.append(rec)
    return rows


def main():
    all_rows = []
    for seed in range(24):
        r = process_seed(seed)
        all_rows.extend(r)
        n_cid = len({(x['seed'], x['cid']) for x in r})
        print(f'seed{seed}: {len(r)} chunk-records, {n_cid} CIDs')
    out = pd.DataFrame(all_rows)
    path = OUT_DIR / 'cid_align_step1b.parquet'
    out.to_parquet(path, index=False)
    print(f'\n=== STEP 1 (作り直し) 完了 ===')
    print(f'保存: {path.relative_to(REPO)}')
    print(f'総 chunk-records: {len(out)} / 総 CID: {out.groupby(["seed","cid"]).ngroups}')
    acols = [f'a{j:02d}' for j in range(48)]
    AX = {'temporal': (0, 7), 'scale': (7, 6), 'epistemological': (13, 5), 'ontological': (18, 5),
          'interconnection': (23, 5), 'resonance': (28, 4), 'symmetry': (32, 5),
          'lawfulness': (37, 4), 'experience': (41, 3), 'value_generation': (44, 4)}
    nz = int((out[acols].abs().sum(axis=0) > 1e-9).sum())
    print(f'非ゼロ次元: {nz}/48')
    for name, (st, w) in AX.items():
        per_dim = [(out[f'a{j:02d}'].abs().sum() > 1e-9) for j in range(st, st + w)]
        print(f'  {name:<16} idx[{st}:{st+w}]: 非ゼロ次元 {sum(per_dim)}/{w}')


if __name__ == '__main__':
    main()
