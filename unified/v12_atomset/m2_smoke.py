#!/usr/bin/env python3
"""v12 Atomset M2 — 誕生時 rank_1 設定 + per-10step 頻度集計 + bonus 育成

## 観察対象注釈ブロック

### 観察対象
- 同じ系内 (Center ESDE 単体、生きた run)
- M1 (label に atomset_seed/bonus key 追加) を extend:
  (a) 誕生時に rank_1 atom を atomset_seed に設定 (簡易 build_cid_vector + atom_centroids cosine)
  (b) per-10step hook で event 種別 (pulse / α / β / c_conv / cid_birth / cid_death) を検出
      各 event 発生 cid の atomset_seed atom への頻度を積算
  (c) atomset_bonus = k * event_count / (event_count + C0) (飽和関数、設計書 §4.1)
- **torque 未接続** (M3 で接続)、bonus を持つだけ、torque_mag には影響しない

### Atomset 設計書 §3 + §4 (v12.0、Web Claude 2026-06-10)
- A 静的素質: 誕生時 rank_1 Atom (本 M2 で実装、簡易 vector)
- B 動的成長: 素質 Atom に頻度積算で bonus 育成 (本 M2)
- 飽和関数: k=0.5, C0=10.0 (smoke 用初期値、判定数値はレコード/summary 外)
- 素質 Atom 一個に積む (合成指標にしない、§4.1 規律)

### M2 出口 (設計書 §7)
- bonus が頻度で育つ (event 発生 cid の bonus > 0)
- torque 未接続なので **baseline (M1 smoke) と bit-identity** が成立
  (= 動学に影響しない、物理 output が一致)

### 規律 (継続)
- 判断基準: CID の個性化を促進するか
- 物理層 frozen、VirtualLayer 内のみ操作
- 判定数値 (event_count, k, C0) はレコード/summary 外
- 人工性留保 (cid_atom_sim_matrix は LLM 判定+手定義投影、本物にならない)
"""
import os, sys, json
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
import time

REPO = Path('/home/takasan/esde/ESDE-Research')
PATHS = [
    REPO / 'primitive/v910', REPO / 'primitive/v911', REPO / 'primitive/v913',
    REPO / 'primitive/v914', REPO / 'primitive/v915', REPO / 'primitive/v917',
    REPO / 'primitive/v918', REPO / 'autonomy/v82',
    REPO / 'cognition/semantic_injection/v4_pipeline/v43',
    REPO / 'cognition/semantic_injection/v4_pipeline/v41',
    REPO / 'ecology/engine',
    REPO / 'developmental/v104', REPO / 'developmental/v105',
    REPO / 'developmental/v106',
]
for p in PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# === 構成 (smoke、M1 と同じ) ===
SEED = 0
MATURATION_WINDOWS = 2
TRACKING_WINDOWS = 3
WINDOW_STEPS = 500
N_PER_CHUNK = 10

# Atomset 設計書 §4.1 (smoke 用、判定数値、レコード/summary 外)
BONUS_K = 0.5      # 飽和上限係数
BONUS_C0 = 10.0    # 飽和速度係数

OUT_DIR = REPO / 'unified/v12_atomset/run_m2_smoke'
OUT_DIR.mkdir(parents=True, exist_ok=True)
V105_OUT_DIR = Path('/tmp/v12_m2_smoke_seed0')
V105_OUT_DIR.mkdir(parents=True, exist_ok=True)

ATOM_CENTROIDS_PATH = REPO / 'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet'

HOOK_STATE = {
    'vl': None, 'cog': None, 'engine': None,
    'integration_mgr': None, 'alpha_mgr': None, 'beta_mgr': None,
    'per_step_counter': 0, 'patch_chunk_count': 0,
    'label_birth_count': 0,
    'theta_diverged': False,
    # M2 event 検出用 (Step 2-A から流用)
    'last_pulse_counts': {},
    'last_alpha_ids': set(),
    'last_beta_ids': set(),
    'last_dead_cids': set(),
    'last_C_values': {},
    'last_known_cids': set(),
    # 観察用
    'rank1_computed_count': 0,
    'rank1_failed_count': 0,
    'event_increment_count': 0,
}

# atom_centroids を 1 回だけ load
ATOM_CENTROIDS_DF = None
ATOM_NAMES = None
ATOM_MATRIX = None


def load_atom_centroids():
    global ATOM_CENTROIDS_DF, ATOM_NAMES, ATOM_MATRIX
    ATOM_CENTROIDS_DF = pd.read_parquet(ATOM_CENTROIDS_PATH)
    ATOM_NAMES = ATOM_CENTROIDS_DF['atom'].tolist()
    cols = [c for c in ATOM_CENTROIDS_DF.columns if c not in ('atom', 'n_words')]
    ATOM_MATRIX = ATOM_CENTROIDS_DF[cols].values.astype(np.float32)
    # 正規化 (cosine 用)
    norms = np.linalg.norm(ATOM_MATRIX, axis=1, keepdims=True)
    norms[norms < 1e-9] = 1.0
    ATOM_MATRIX = ATOM_MATRIX / norms
    print(f'  atom_centroids loaded: {ATOM_MATRIX.shape} (= {len(ATOM_NAMES)} atoms × 48 dims)')


def compute_rank_1_atom(label, state):
    """誕生時の簡易 cid_vector → atom_centroids cosine → rank_1 atom

    設計書 §3.1: 「rank_1 は方向であってラベルの完全一致ではない」
    誕生時に取れる情報のみで簡易 vector を構築 (主に scale 軸 + phase)
    v106 build_cid_vector の完全な fields は誕生時に揃わないため、近似版を使う
    """
    try:
        n_core = len(label['nodes'])
        phase_sig = label['phase_sig']

        # 簡易 48 次元 vector: scale_vector のみで埋め、他軸は等比初期値
        # v106 scale_vector(n_core) は 6 levels (= 48 中の 6 次元)
        # 残り 42 次元は 0 → cosine の denominator は scale 軸のみで決まる
        vec = np.zeros(48, dtype=np.float32)
        # scale 軸 (6 levels)、v106 scale_vector ロジック流用
        # cumulative position: 7 (temporal) ... 13 (scale 終了)
        scale_start = 7  # temporal 7 levels の後
        n = int(round(n_core))
        if n <= 2:
            vec[scale_start + 0] = 1.0
        elif n == 3:
            vec[scale_start + 1] = 1.0
        elif n == 4:
            vec[scale_start + 2] = 1.0
        elif n == 5:
            vec[scale_start + 3] = 1.0
        elif n == 6:
            vec[scale_start + 4] = 1.0
        else:
            vec[scale_start + 5] = 1.0

        # phase_sig を temporal 軸 (誕生時近接、暫定的に temporal[0]=emergence にマップ)
        # phase_sig は -π..π、|phase_sig| 大 = transformation 寄り、小 = emergence 寄り
        norm_phase = abs(phase_sig) / np.pi  # 0..1
        # temporal 7 levels に分配
        for i, lo in enumerate([0, 1/7, 2/7, 3/7, 4/7, 5/7, 6/7]):
            if norm_phase >= lo and norm_phase < (lo + 1/7):
                vec[i] = 1.0
                break
        else:
            vec[6] = 1.0  # 上限

        # 正規化
        norm = np.linalg.norm(vec)
        if norm < 1e-9:
            return None
        vec_unit = vec / norm

        # atom_centroids との cosine sim → rank_1
        sims = ATOM_MATRIX @ vec_unit  # (326,)
        rank_1_idx = int(np.argmax(sims))
        return ATOM_NAMES[rank_1_idx]
    except Exception as e:
        return None


def patch_virtual_layer_step():
    """VirtualLayer.step を wrap して新規 label に atomset_seed (rank_1) / atomset_bonus を装飾"""
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
    _orig_step = VirtualLayerV9.step

    def _hooked_step(self, state, window_count, islands=None, substrate=None):
        stats = _orig_step(self, state, window_count, islands, substrate)
        for lid, label in list(self.labels.items()):
            if 'atomset_seed' not in label:
                # M2: 誕生時に rank_1 を計算
                rank_1 = compute_rank_1_atom(label, state)
                if rank_1 is not None:
                    label['atomset_seed'] = rank_1
                    HOOK_STATE['rank1_computed_count'] += 1
                else:
                    label['atomset_seed'] = None
                    HOOK_STATE['rank1_failed_count'] += 1
                label['atomset_bonus'] = 0.0
                label['atomset_event_count'] = 0
                HOOK_STATE['label_birth_count'] += 1
        theta = state.theta
        if np.any(np.isnan(theta)) or np.any(np.abs(theta) > 100):
            HOOK_STATE['theta_diverged'] = True
        HOOK_STATE['vl'] = self
        return stats

    VirtualLayerV9.step = _hooked_step
    print(f'  [hook] VirtualLayer.step wrapped (誕生時 rank_1 + bonus 0)')


def setup_cog_integration_patches():
    """SubjectLayer + IntegrationManager + V82Engine を捕捉 (Step 2-A 経路)"""
    import v105_memory_readout as v105mr
    SubjectLayer = v105mr.SubjectLayer
    IntegrationManager = v105mr.IntegrationManager
    from esde_v82_engine import V82Engine

    _orig_subject_init = SubjectLayer.__init__
    def _captured_subject_init(self, *args, **kwargs):
        _orig_subject_init(self, *args, **kwargs)
        HOOK_STATE['cog'] = self
    SubjectLayer.__init__ = _captured_subject_init

    _orig_im_init = IntegrationManager.__init__
    def _captured_im_init(self, *args, **kwargs):
        _orig_im_init(self, *args, **kwargs)
        HOOK_STATE['integration_mgr'] = self
        HOOK_STATE['alpha_mgr'] = getattr(self, 'alpha', None)
        HOOK_STATE['beta_mgr'] = getattr(self, 'beta', None)
    IntegrationManager.__init__ = _captured_im_init

    _orig_engine_init = V82Engine.__init__
    def _captured_engine_init(self, *args, **kwargs):
        _orig_engine_init(self, *args, **kwargs)
        HOOK_STATE['engine'] = self
        if hasattr(self, 'realizer') and self.realizer is not None:
            _orig_realizer_step = self.realizer.step
            _engine_ref = self
            def _hooked_realizer_step(state):
                _orig_realizer_step(state)
                HOOK_STATE['per_step_counter'] += 1
                if HOOK_STATE['per_step_counter'] % N_PER_CHUNK == 0:
                    HOOK_STATE['patch_chunk_count'] += 1
                    per_chunk_observe()
            self.realizer.step = _hooked_realizer_step
    V82Engine.__init__ = _captured_engine_init


def per_chunk_observe():
    """per-10step hook: event 検出 + 該当 cid の atomset_seed atom に頻度積算 + bonus 育成

    Step 2-A の引き金検出経路を流用、ただし alert 判定は不要 (頻度を積むだけ)
    """
    cog = HOOK_STATE['cog']
    vl = HOOK_STATE['vl']
    if cog is None or vl is None:
        return

    # event 検出 (Step 2-A と同じ delta 検出)
    born_at = getattr(cog, 'born_at', {})
    current_cids = set(born_at.keys())
    new_births = current_cids - HOOK_STATE['last_known_cids']
    HOOK_STATE['last_known_cids'] = current_cids

    host_lost_at = getattr(cog, 'host_lost_at', {})
    current_dead = set(c for c, v in host_lost_at.items() if v is not None)
    new_deaths = current_dead - HOOK_STATE['last_dead_cids']
    HOOK_STATE['last_dead_cids'] = current_dead

    alpha_mgr = HOOK_STATE.get('alpha_mgr')
    new_alpha_cids = set()
    if alpha_mgr is not None:
        current_alphas = set(getattr(alpha_mgr, 'alphas', {}).keys())
        new_alpha_ids = current_alphas - HOOK_STATE['last_alpha_ids']
        for aid in new_alpha_ids:
            ai = alpha_mgr.alphas.get(aid)
            if ai is not None:
                new_alpha_cids.update(getattr(ai, 'member_cids', set()))
        HOOK_STATE['last_alpha_ids'] = current_alphas

    beta_mgr = HOOK_STATE.get('beta_mgr')
    new_beta_cids = set()
    if beta_mgr is not None:
        current_betas = set(getattr(beta_mgr, 'betas', {}).keys())
        new_beta_ids = current_betas - HOOK_STATE['last_beta_ids']
        for bid in new_beta_ids:
            bi = beta_mgr.betas.get(bid)
            if bi is not None:
                new_beta_cids.update(getattr(bi, 'member_cids', set()))
        HOOK_STATE['last_beta_ids'] = current_betas

    # pulse
    new_pulse_cids = set()
    current_pulse = getattr(cog, 'v10_pulse_count', {})
    if isinstance(current_pulse, dict):
        for cid, pc in current_pulse.items():
            prev = HOOK_STATE['last_pulse_counts'].get(cid, 0)
            if pc > prev:
                new_pulse_cids.add(cid)
        HOOK_STATE['last_pulse_counts'] = dict(current_pulse)

    # c_conversion
    new_c_cids = set()
    current_C = getattr(cog, 'C', {})
    if isinstance(current_C, dict):
        for cid, cv in current_C.items():
            prev = HOOK_STATE['last_C_values'].get(cid, 0)
            if cv > prev:
                new_c_cids.add(cid)
        HOOK_STATE['last_C_values'] = dict(current_C)

    # 該当 cid 全集合 (event 発生 cid)
    event_cids = new_births | new_deaths | new_alpha_cids | new_beta_cids | new_pulse_cids | new_c_cids
    if not event_cids:
        return

    # cid → lid → label の経路で atomset_seed atom に頻度積算
    cid_of_lid = getattr(cog, 'current_lid', {})  # cid -> lid (M1 で確認、cog.current_lid)
    for cid in event_cids:
        lid = cid_of_lid.get(cid)
        if lid is None:
            continue
        label = vl.labels.get(lid)
        if label is None or label.get('atomset_seed') is None:
            continue
        # 頻度積算 (素質 Atom 一個に積む、合成指標にしない、設計書 §4.1)
        label['atomset_event_count'] = label.get('atomset_event_count', 0) + 1
        # bonus 飽和関数 (設計書 §4.1: bonus = k * event_count / (event_count + C0))
        ec = label['atomset_event_count']
        label['atomset_bonus'] = BONUS_K * ec / (ec + BONUS_C0)
        HOOK_STATE['event_increment_count'] += 1


def main():
    print('=== v12 Atomset M2 smoke — 誕生時 rank_1 + 頻度集計 + bonus 育成 ===\n')
    print(f'  SEED={SEED}, mat={MATURATION_WINDOWS}, track={TRACKING_WINDOWS}')
    print(f'  飽和関数: bonus = {BONUS_K} * event_count / (event_count + {BONUS_C0})')
    print(f'  M2 出口: bonus が頻度で育つ + torque 未接続で baseline 動学不変\n')

    load_atom_centroids()
    setup_cog_integration_patches()
    patch_virtual_layer_step()

    import v105_memory_readout as v105mr
    v105_run = v105mr.run

    cwd_orig = Path.cwd()
    os.chdir(V105_OUT_DIR)

    t_start = time.time()
    try:
        v105_run(
            seed=SEED,
            maturation_windows=MATURATION_WINDOWS,
            tracking_windows=TRACKING_WINDOWS,
            window_steps=WINDOW_STEPS,
            tag='v12_m2_smoke_seed0',
        )
    finally:
        os.chdir(cwd_orig)

    t_total = time.time() - t_start

    print(f'\n=== v105 run() 完了 ({t_total:.1f}s) ===\n')

    vl = HOOK_STATE['vl']
    if vl is None:
        print('ERROR: VirtualLayer 捕捉失敗')
        sys.exit(1)

    # === M2 出口確認 ===
    labels_total = len(vl.labels)
    labels_with_atomset = sum(1 for l in vl.labels.values() if 'atomset_seed' in l)
    labels_with_seed = sum(1 for l in vl.labels.values() if l.get('atomset_seed') is not None)
    bonus_values = [l.get('atomset_bonus', 0.0) for l in vl.labels.values()]
    bonus_grown = sum(1 for b in bonus_values if b > 0)
    event_counts = [l.get('atomset_event_count', 0) for l in vl.labels.values()]

    # rank_1 atom 分布
    rank1_dist = Counter(l.get('atomset_seed') for l in vl.labels.values() if l.get('atomset_seed') is not None)

    print('=' * 60)
    print('M2 出口確認')
    print('=' * 60)
    print(f'\n(1) smoke 完走: ✓ exit 0 ({t_total:.1f}s)')
    print(f'(2) engine 発散: {"✗ 発散" if HOOK_STATE["theta_diverged"] else "✓ なし"}')
    print(f'(3) label 装飾:')
    print(f'    label 総数: {labels_total}')
    print(f'    atomset_seed 計算成功: {HOOK_STATE["rank1_computed_count"]} / 失敗: {HOOK_STATE["rank1_failed_count"]}')
    print(f'    完走時 atomset_seed not None: {labels_with_seed}/{labels_total}')
    print(f'(4) bonus 育成 (M2 核心):')
    print(f'    event 積算回数: {HOOK_STATE["event_increment_count"]}')
    print(f'    bonus > 0 の label: {bonus_grown}/{labels_total}')
    if bonus_values:
        print(f'    bonus 値: min={min(bonus_values):.4f}, max={max(bonus_values):.4f}, mean={np.mean(bonus_values):.4f}')
    if event_counts:
        print(f'    event_count: min={min(event_counts)}, max={max(event_counts)}, sum={sum(event_counts)}')
    print(f'(5) rank_1 atom 分布 (上位 5):')
    for atom, cnt in rank1_dist.most_common(5):
        print(f'    {atom}: {cnt}')

    # === bit-identity 検証 (M1 smoke と output 比較) ===
    print(f'\n(6) bit-identity 検証 (M1 smoke と subjects/per_subject_seed0.csv 比較):')
    m1_subj_path = Path('/tmp/v12_m1_smoke_seed0/diag_v105_v12_m1_smoke_seed0/subjects/per_subject_seed0.csv')
    m2_subj_path = V105_OUT_DIR / 'diag_v105_v12_m2_smoke_seed0/subjects/per_subject_seed0.csv'
    if m1_subj_path.exists() and m2_subj_path.exists():
        m1_df = pd.read_csv(m1_subj_path)
        m2_df = pd.read_csv(m2_subj_path)
        # 主要 cols で完全一致確認
        key_cols = ['cognitive_id', 'birth_window', 'host_lost_window',
                    'final_state', 'original_phase_sig']
        common = [c for c in key_cols if c in m1_df.columns and c in m2_df.columns]
        if len(m1_df) == len(m2_df):
            print(f'    M1: {len(m1_df)} CIDs, M2: {len(m2_df)} CIDs ← 一致')
            mismatched = 0
            for c in common:
                if c in ('original_phase_sig',):
                    eq = (m1_df[c].round(6).values == m2_df[c].round(6).values).sum()
                else:
                    eq = (m1_df[c].astype(str).values == m2_df[c].astype(str).values).sum()
                mismatch = len(m1_df) - eq
                mismatched += mismatch
                marker = '✓' if mismatch == 0 else '✗'
                print(f'    {c}: {eq}/{len(m1_df)} 一致 {marker}')
            print(f'    {"✓ bit-identity 成立" if mismatched == 0 else f"✗ {mismatched} fields mismatch"}')
        else:
            print(f'    ✗ CID 数が違う: M1 {len(m1_df)} vs M2 {len(m2_df)}')
    else:
        print(f'    M1 smoke output 不在、bit-identity 検証 skip')
        print(f'    M1: {m1_subj_path.exists()}, M2: {m2_subj_path.exists()}')

    # === 出力 ===
    summary = {
        'design': 'v12_atomset_m2_smoke',
        'note': 'M2: 誕生時 rank_1 + per-10step 頻度集計 + bonus 育成、torque 未接続で baseline と bit-identity',
        'seed': SEED,
        'maturation_windows': MATURATION_WINDOWS,
        'tracking_windows': TRACKING_WINDOWS,
        'window_steps': WINDOW_STEPS,
        'duration_sec': round(t_total, 1),
        'label_birth_count': HOOK_STATE['label_birth_count'],
        'labels_total': labels_total,
        'labels_with_seed': labels_with_seed,
        'rank1_computed_count': HOOK_STATE['rank1_computed_count'],
        'rank1_failed_count': HOOK_STATE['rank1_failed_count'],
        'event_increment_count': HOOK_STATE['event_increment_count'],
        'labels_with_bonus_grown': bonus_grown,
        'rank1_top5': rank1_dist.most_common(5),
        'theta_diverged': HOOK_STATE['theta_diverged'],
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n保存: {OUT_DIR / "summary.json"}')
    print(f'\n=== M2 完了 ===')


if __name__ == '__main__':
    main()
