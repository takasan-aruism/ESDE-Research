#!/usr/bin/env python3
"""v12 Atomset M3 — 育った atomset_bonus を torque に接続 (Frozenset cog_factor の口)

## 観察対象注釈ブロック

### 観察対象
- 同じ系内 (Center ESDE 単体、生きた run)
- M2 (誕生時 rank_1 + per-10step 頻度集計 + bonus 育成) を extend:
  育った atomset_bonus を atomset_factor = 1.0 + GAIN * bonus として
  label["torque_factor"] に乗せ、torque_mag に接続する。
- 接続点: virtual_layer_v9.py の step()/apply_torque_only() の
      cog_factor = label.get("torque_factor", 1.0)
      torque_mag = energy * rigidity_factor * self._torque_multiplier * cog_factor
  この cog_factor の口に atomset_factor を流す (設計書 §3.3、Frozenset の cog_factor 経路)。
  v105 の NOTE 通り、torque_factor を設定しなければ v9.6 と同一挙動 = M2 baseline。

### 飽和係数 (GAIN) を 0→小→中 で段階的に (発散チェック)
- off    GAIN=0.0  → atomset_factor=1.0 → M2 baseline と bit-identity (制御群、配線が gated)
- small  GAIN=0.5  → atomset_factor=1.0+0.5*bonus (bonus 由来の torque 増 ~半分)
- medium GAIN=1.0  → atomset_factor=1.0+1.0*bonus (設計書 nominal 1.0+bonus)
- bonus 飽和関数は M2 と同一 (k=0.5, C0=10.0)。bonus 値そのものは M2 で物理無害を
  証明済なので、ここで出る diff は torque 接続 (cog_factor 経由) のみに由来する。

### M3 smoke 出口 (設計書 §7)
- (1) engine 発散しない (theta 範囲維持、run 完走)、GAIN を上げても発散しない
- (2) bonus が torque に実際に乗る (cog_factor>1 が torque 計算で使われる)
      → GAIN=0 では baseline と bit-identity、GAIN>0 では diff が出る
      → この diff = torque 由来 (M2 で bit 一致＝無害が確定済なので切り分け可能)

### 規律 (継続)
- 判断基準: CID の個性化を促進するか
- 物理層 (genesis_physics、イベント発生) は不可侵、VirtualLayer 内 torque のみ操作
- 判定数値 (GAIN, k, C0, event_count) は CID の観察レコード (per_subject / label parquet)
  に残さない。GAIN は実験条件 (experiment knob) として summary に条件名で記す。
- 24 seeds main は本 smoke が健全と確認してから。
- 人工性留保 (cid_atom_sim_matrix は LLM 判定+手定義投影、本物にならない) 継続。

usage: python m3_smoke.py {off|small|medium}
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

# === 構成 (smoke、M1/M2 と同じ) ===
SEED = 0
MATURATION_WINDOWS = 2
TRACKING_WINDOWS = 3
WINDOW_STEPS = 500
N_PER_CHUNK = 10

# bonus 飽和関数 (M2 と同一、判定数値、CID レコード外)
BONUS_K = 0.5      # 飽和上限係数
BONUS_C0 = 10.0    # 飽和速度係数

# M3 torque 接続係数 (飽和係数 GAIN、0→小→中 で発散チェック、CID レコード外)
GAIN_CONDITIONS = {'off': 0.0, 'small': 0.5, 'medium': 1.0}

# === 実験条件選択 (argv) ===
CONDITION = sys.argv[1] if len(sys.argv) > 1 else 'off'
if CONDITION not in GAIN_CONDITIONS:
    print(f'ERROR: condition は {list(GAIN_CONDITIONS)} のいずれか (受領: {CONDITION!r})')
    sys.exit(2)
TORQUE_GAIN = GAIN_CONDITIONS[CONDITION]

OUT_DIR = REPO / 'unified/v1201/run_m3_smoke' / CONDITION
OUT_DIR.mkdir(parents=True, exist_ok=True)
V105_OUT_DIR = Path(f'/tmp/v12_m3_smoke_{CONDITION}_seed0')
V105_OUT_DIR.mkdir(parents=True, exist_ok=True)

ATOM_CENTROIDS_PATH = REPO / 'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet'

HOOK_STATE = {
    'vl': None, 'cog': None, 'engine': None,
    'integration_mgr': None, 'alpha_mgr': None, 'beta_mgr': None,
    'per_step_counter': 0, 'patch_chunk_count': 0,
    'label_birth_count': 0,
    'theta_diverged': False,
    # event 検出用 (M2 から流用)
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
    # M3: torque 接続の instrumentation
    'factor_set_count': 0,        # torque_factor を設定した回数
    'max_factor_ever': 1.0,       # 観測した最大 atomset_factor
    'window_torque_log': [],      # per-window: (window_count, n_factor_gt1, max_factor, torque_total, torque_events)
}

ATOM_CENTROIDS_DF = None
ATOM_NAMES = None
ATOM_MATRIX = None


def load_atom_centroids():
    global ATOM_CENTROIDS_DF, ATOM_NAMES, ATOM_MATRIX
    ATOM_CENTROIDS_DF = pd.read_parquet(ATOM_CENTROIDS_PATH)
    ATOM_NAMES = ATOM_CENTROIDS_DF['atom'].tolist()
    cols = [c for c in ATOM_CENTROIDS_DF.columns if c not in ('atom', 'n_words')]
    ATOM_MATRIX = ATOM_CENTROIDS_DF[cols].values.astype(np.float32)
    norms = np.linalg.norm(ATOM_MATRIX, axis=1, keepdims=True)
    norms[norms < 1e-9] = 1.0
    ATOM_MATRIX = ATOM_MATRIX / norms
    print(f'  atom_centroids loaded: {ATOM_MATRIX.shape} (= {len(ATOM_NAMES)} atoms × 48 dims)')


def compute_rank_1_atom(label, state):
    """誕生時の簡易 cid_vector → atom_centroids cosine → rank_1 atom (M2 と同一)"""
    try:
        n_core = len(label['nodes'])
        phase_sig = label['phase_sig']
        vec = np.zeros(48, dtype=np.float32)
        scale_start = 7
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
        norm_phase = abs(phase_sig) / np.pi
        for i, lo in enumerate([0, 1/7, 2/7, 3/7, 4/7, 5/7, 6/7]):
            if norm_phase >= lo and norm_phase < (lo + 1/7):
                vec[i] = 1.0
                break
        else:
            vec[6] = 1.0
        norm = np.linalg.norm(vec)
        if norm < 1e-9:
            return None
        vec_unit = vec / norm
        sims = ATOM_MATRIX @ vec_unit
        rank_1_idx = int(np.argmax(sims))
        return ATOM_NAMES[rank_1_idx]
    except Exception:
        return None


def patch_virtual_layer_step():
    """VirtualLayer.step を wrap。

    M3: torque は _orig_step 内で label.get("torque_factor", 1.0) を読んで適用される。
    その口に流す atomset_factor は per_chunk_observe() で bonus 更新時に label に書き込む。
    ここでは _orig_step の前に「今 torque が使う factor 分布」を snapshot して instrument し、
    _orig_step 後に新規 label を装飾する。
    """
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
    _orig_step = VirtualLayerV9.step

    def _hooked_step(self, state, window_count, islands=None, substrate=None):
        # _orig_step が torque に使う factor を事前 snapshot (この window の torque が読む値)
        factors = [lbl.get('torque_factor', 1.0) for lbl in self.labels.values()]
        n_gt1 = sum(1 for f in factors if f > 1.0)
        max_f = max(factors) if factors else 1.0

        stats = _orig_step(self, state, window_count, islands, substrate)

        HOOK_STATE['window_torque_log'].append((
            int(window_count), int(n_gt1), float(max_f),
            float(stats.get('torque_total', 0.0)),
            int(stats.get('torque_events', 0)),
        ))

        # 新規 label を装飾 (M2 と同一: 誕生時 rank_1 + bonus 0)
        for lid, label in list(self.labels.items()):
            if 'atomset_seed' not in label:
                rank_1 = compute_rank_1_atom(label, state)
                if rank_1 is not None:
                    label['atomset_seed'] = rank_1
                    HOOK_STATE['rank1_computed_count'] += 1
                else:
                    label['atomset_seed'] = None
                    HOOK_STATE['rank1_failed_count'] += 1
                label['atomset_bonus'] = 0.0
                label['atomset_event_count'] = 0
                # 誕生時 factor = 1.0 (bonus 0) — 制御群 off と同値、torque 無影響
                label['torque_factor'] = 1.0
                HOOK_STATE['label_birth_count'] += 1
        theta = state.theta
        if np.any(np.isnan(theta)) or np.any(np.abs(theta) > 100):
            HOOK_STATE['theta_diverged'] = True
        HOOK_STATE['vl'] = self
        return stats

    VirtualLayerV9.step = _hooked_step
    print(f'  [hook] VirtualLayer.step wrapped (誕生時 rank_1 + torque_factor 接続)')


def setup_cog_integration_patches():
    """SubjectLayer + IntegrationManager + V82Engine を捕捉 (M2 と同一)"""
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
            def _hooked_realizer_step(state):
                _orig_realizer_step(state)
                HOOK_STATE['per_step_counter'] += 1
                if HOOK_STATE['per_step_counter'] % N_PER_CHUNK == 0:
                    HOOK_STATE['patch_chunk_count'] += 1
                    per_chunk_observe()
            self.realizer.step = _hooked_realizer_step
    V82Engine.__init__ = _captured_engine_init


def per_chunk_observe():
    """per-10step hook: event 検出 + 頻度積算 + bonus 育成 + torque_factor 接続 (M3 核心)

    M2 と同一の event 検出・bonus 育成に加え、
    育った bonus を atomset_factor = 1.0 + TORQUE_GAIN * bonus として
    label["torque_factor"] に書き込む (= 次 vl.step の torque がこの factor を読む)。
    """
    cog = HOOK_STATE['cog']
    vl = HOOK_STATE['vl']
    if cog is None or vl is None:
        return

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

    new_pulse_cids = set()
    current_pulse = getattr(cog, 'v10_pulse_count', {})
    if isinstance(current_pulse, dict):
        for cid, pc in current_pulse.items():
            prev = HOOK_STATE['last_pulse_counts'].get(cid, 0)
            if pc > prev:
                new_pulse_cids.add(cid)
        HOOK_STATE['last_pulse_counts'] = dict(current_pulse)

    new_c_cids = set()
    current_C = getattr(cog, 'C', {})
    if isinstance(current_C, dict):
        for cid, cv in current_C.items():
            prev = HOOK_STATE['last_C_values'].get(cid, 0)
            if cv > prev:
                new_c_cids.add(cid)
        HOOK_STATE['last_C_values'] = dict(current_C)

    event_cids = new_births | new_deaths | new_alpha_cids | new_beta_cids | new_pulse_cids | new_c_cids
    if not event_cids:
        return

    cid_of_lid = getattr(cog, 'current_lid', {})  # cid -> lid
    for cid in event_cids:
        lid = cid_of_lid.get(cid)
        if lid is None:
            continue
        label = vl.labels.get(lid)
        if label is None or label.get('atomset_seed') is None:
            continue
        # 頻度積算 (素質 Atom 一個に積む、M2 と同一)
        label['atomset_event_count'] = label.get('atomset_event_count', 0) + 1
        ec = label['atomset_event_count']
        bonus = BONUS_K * ec / (ec + BONUS_C0)
        label['atomset_bonus'] = bonus
        HOOK_STATE['event_increment_count'] += 1
        # === M3 核心: bonus を torque へ接続 ===
        # atomset_factor = 1.0 + GAIN * bonus を cog_factor の口 (torque_factor) に流す
        factor = 1.0 + TORQUE_GAIN * bonus
        label['torque_factor'] = factor
        HOOK_STATE['factor_set_count'] += 1
        if factor > HOOK_STATE['max_factor_ever']:
            HOOK_STATE['max_factor_ever'] = factor


def main():
    print('=== v12 Atomset M3 smoke — bonus を torque に接続 (cog_factor の口) ===\n')
    print(f'  CONDITION={CONDITION}, TORQUE_GAIN={TORQUE_GAIN}')
    print(f'  SEED={SEED}, mat={MATURATION_WINDOWS}, track={TRACKING_WINDOWS}')
    print(f'  bonus 飽和: bonus = {BONUS_K} * ec / (ec + {BONUS_C0})  (M2 と同一)')
    print(f'  torque 接続: atomset_factor = 1.0 + {TORQUE_GAIN} * bonus → label["torque_factor"]')
    print(f'  発散チェック: GAIN 0→小→中 段階、theta_diverged を監視\n')

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
            tag=f'v12_m3_smoke_{CONDITION}_seed0',
        )
    finally:
        os.chdir(cwd_orig)

    t_total = time.time() - t_start
    print(f'\n=== v105 run() 完了 ({t_total:.1f}s) ===\n')

    vl = HOOK_STATE['vl']
    if vl is None:
        print('ERROR: VirtualLayer 捕捉失敗')
        sys.exit(1)

    labels_total = len(vl.labels)
    labels_with_seed = sum(1 for l in vl.labels.values() if l.get('atomset_seed') is not None)
    bonus_values = [l.get('atomset_bonus', 0.0) for l in vl.labels.values()]
    bonus_grown = sum(1 for b in bonus_values if b > 0)
    factor_values = [l.get('torque_factor', 1.0) for l in vl.labels.values()]
    factor_gt1 = sum(1 for f in factor_values if f > 1.0)
    rank1_dist = Counter(l.get('atomset_seed') for l in vl.labels.values() if l.get('atomset_seed') is not None)

    # torque log 集計
    wlog = HOOK_STATE['window_torque_log']
    windows_with_active_factor = sum(1 for (_, n_gt1, _, _, _) in wlog if n_gt1 > 0)
    torque_total_sum = sum(tt for (_, _, _, tt, _) in wlog)

    print('=' * 60)
    print(f'M3 出口確認 (CONDITION={CONDITION}, GAIN={TORQUE_GAIN})')
    print('=' * 60)
    print(f'\n(1) smoke 完走: ✓ exit 0 ({t_total:.1f}s)')
    print(f'(2) engine 発散: {"✗ 発散" if HOOK_STATE["theta_diverged"] else "✓ なし"}')
    print(f'(3) label / bonus:')
    print(f'    label 総数: {labels_total}, atomset_seed not None: {labels_with_seed}')
    print(f'    bonus > 0: {bonus_grown}/{labels_total}, event 積算: {HOOK_STATE["event_increment_count"]}')
    if bonus_values:
        print(f'    bonus: min={min(bonus_values):.4f}, max={max(bonus_values):.4f}, mean={np.mean(bonus_values):.4f}')
    print(f'(4) torque 接続 (M3 核心):')
    print(f'    torque_factor 設定回数: {HOOK_STATE["factor_set_count"]}')
    print(f'    factor > 1.0 の label (完走時): {factor_gt1}/{labels_total}')
    print(f'    観測最大 atomset_factor: {HOOK_STATE["max_factor_ever"]:.4f}')
    print(f'    factor>1 が torque に乗った window 数: {windows_with_active_factor}/{len(wlog)}')
    print(f'    Σ torque_total (全 window): {torque_total_sum:.4f}')
    print(f'(5) per-window torque log (window, n_factor>1, max_factor, torque_total, events):')
    for row in wlog:
        print(f'    w={row[0]}: n_gt1={row[1]}, max_f={row[2]:.4f}, torque_total={row[3]:.4f}, events={row[4]}')
    print(f'(6) rank_1 atom 分布 (上位 5):')
    for atom, cnt in rank1_dist.most_common(5):
        print(f'    {atom}: {cnt}')

    summary = {
        'design': 'v1201_m3_smoke',
        'note': ('M3: 育った atomset_bonus を atomset_factor=1.0+GAIN*bonus として '
                 'label["torque_factor"] (cog_factor の口) に接続し torque_mag に乗せる。'
                 'GAIN=0 (off) は M2 baseline と bit-identity (制御群)、GAIN>0 で torque 由来の diff。'),
        'condition': CONDITION,          # experiment knob (CID レコード外)
        'torque_gain': TORQUE_GAIN,      # experiment knob (CID レコード外)
        'seed': SEED,
        'maturation_windows': MATURATION_WINDOWS,
        'tracking_windows': TRACKING_WINDOWS,
        'window_steps': WINDOW_STEPS,
        'duration_sec': round(t_total, 1),
        'label_birth_count': HOOK_STATE['label_birth_count'],
        'labels_total': labels_total,
        'labels_with_seed': labels_with_seed,
        'event_increment_count': HOOK_STATE['event_increment_count'],
        'labels_with_bonus_grown': bonus_grown,
        'bonus_max': round(max(bonus_values), 4) if bonus_values else 0.0,
        'factor_set_count': HOOK_STATE['factor_set_count'],
        'labels_factor_gt1': factor_gt1,
        'max_atomset_factor': round(HOOK_STATE['max_factor_ever'], 4),
        'windows_with_active_factor': windows_with_active_factor,
        'torque_total_sum': round(torque_total_sum, 4),
        'window_torque_log': wlog,
        'rank1_top5': rank1_dist.most_common(5),
        'theta_diverged': HOOK_STATE['theta_diverged'],
        'v105_out_dir': str(V105_OUT_DIR),
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n保存: {OUT_DIR / "summary.json"}')
    print(f'\n=== M3 smoke ({CONDITION}) 完了 ===')

    if HOOK_STATE['theta_diverged']:
        print('赤信号: engine 発散検出、GAIN を上げる前に要 debug')
        sys.exit(1)


if __name__ == '__main__':
    main()
