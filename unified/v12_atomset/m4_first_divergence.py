#!/usr/bin/env python3
"""v12 M4 — first-divergence 計装 re-run (現 seed 0 で機構監査)

M3 と同一の torque 接続 (atomset_factor=1.0+GAIN*bonus を label["torque_factor"] へ)。
追加で実験側 audit を取る (CID 公式レコードには入れない、すべて run_m4/<cond>/ へ):
  1. theta_checksums.csv — per realizer-step の θ md5 (off vs small を後で diff → 最初に θ が
     分岐する step を確定)
  2. label_window_snapshot.json — vl.step ごとの {lid, cid, factor, share, nodes}
     (torque が読む factor とその label の territory。first-divergence link の node が
      bonus 対象 territory に属すか確認するため)
  3. cid_bonus_tags.csv — per cid の {atomset_seed, event_count, bonus, final_factor,
     is_bonus_target} (死んだ CID も含めるため per_chunk で逐次蓄積)

usage: python m4_first_divergence.py {off|small}
"""
import os, sys, json, hashlib
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from pathlib import Path
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

SEED = 0
MATURATION_WINDOWS = 2
TRACKING_WINDOWS = 3
WINDOW_STEPS = 500
N_PER_CHUNK = 10
BONUS_K = 0.5
BONUS_C0 = 10.0
GAIN_CONDITIONS = {'off': 0.0, 'small': 0.5, 'medium': 1.0}

CONDITION = sys.argv[1] if len(sys.argv) > 1 else 'off'
if CONDITION not in GAIN_CONDITIONS:
    print(f'ERROR: condition は {list(GAIN_CONDITIONS)} (受領: {CONDITION!r})')
    sys.exit(2)
TORQUE_GAIN = GAIN_CONDITIONS[CONDITION]

OUT_DIR = REPO / 'unified/v12_atomset/run_m4' / CONDITION
OUT_DIR.mkdir(parents=True, exist_ok=True)
V105_OUT_DIR = Path(f'/tmp/v12_m4_{CONDITION}_seed0')
V105_OUT_DIR.mkdir(parents=True, exist_ok=True)
ATOM_CENTROIDS_PATH = REPO / 'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet'

HOOK_STATE = {
    'vl': None, 'cog': None, 'engine': None,
    'alpha_mgr': None, 'beta_mgr': None,
    'per_step_counter': 0,
    'last_pulse_counts': {}, 'last_alpha_ids': set(), 'last_beta_ids': set(),
    'last_dead_cids': set(), 'last_C_values': {}, 'last_known_cids': set(),
    'theta_diverged': False,
    'theta_checksums': [],      # (step_counter, md5)
    'label_window_snapshot': {},  # window_count -> [ {lid,cid,factor,share,nodes} ]
    'cid_tags': {},             # cid -> {seed,event_count,bonus,factor}
}

ATOM_NAMES = None
ATOM_MATRIX = None


def load_atom_centroids():
    global ATOM_NAMES, ATOM_MATRIX
    df = pd.read_parquet(ATOM_CENTROIDS_PATH)
    ATOM_NAMES = df['atom'].tolist()
    cols = [c for c in df.columns if c not in ('atom', 'n_words')]
    m = df[cols].values.astype(np.float32)
    norms = np.linalg.norm(m, axis=1, keepdims=True); norms[norms < 1e-9] = 1.0
    ATOM_MATRIX = m / norms


def compute_rank_1_atom(label, state):
    try:
        n_core = len(label['nodes']); phase_sig = label['phase_sig']
        vec = np.zeros(48, dtype=np.float32); scale_start = 7
        n = int(round(n_core))
        idx = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4}.get(n, 5 if n > 6 else 0)
        if n <= 2: idx = 0
        vec[scale_start + idx] = 1.0
        norm_phase = abs(phase_sig) / np.pi
        for i, lo in enumerate([0, 1/7, 2/7, 3/7, 4/7, 5/7, 6/7]):
            if lo <= norm_phase < lo + 1/7:
                vec[i] = 1.0; break
        else:
            vec[6] = 1.0
        norm = np.linalg.norm(vec)
        if norm < 1e-9: return None
        sims = ATOM_MATRIX @ (vec / norm)
        return ATOM_NAMES[int(np.argmax(sims))]
    except Exception:
        return None


def patch_virtual_layer_step():
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
    _orig_step = VirtualLayerV9.step

    def _hooked_step(self, state, window_count, islands=None, substrate=None):
        # torque が読む factor + territory を snapshot (この window の torque 直前の状態)
        cog = HOOK_STATE['cog']
        snap = []
        for lid, label in self.labels.items():
            if lid in getattr(self, 'macro_nodes', {}):
                continue
            cid = cog.cid_for_lid(lid) if cog is not None else None
            snap.append({
                'lid': int(lid), 'cid': (int(cid) if cid is not None else None),
                'factor': float(label.get('torque_factor', 1.0)),
                'share': float(label.get('share', 0.0)),
                'nodes': sorted(int(n) for n in label['nodes']),
            })
        HOOK_STATE['label_window_snapshot'][int(window_count)] = snap

        stats = _orig_step(self, state, window_count, islands, substrate)

        for lid, label in list(self.labels.items()):
            if 'atomset_seed' not in label:
                rank_1 = compute_rank_1_atom(label, state)
                label['atomset_seed'] = rank_1
                label['atomset_bonus'] = 0.0
                label['atomset_event_count'] = 0
                label['torque_factor'] = 1.0
        theta = state.theta
        if np.any(np.isnan(theta)) or np.any(np.abs(theta) > 100):
            HOOK_STATE['theta_diverged'] = True
        HOOK_STATE['vl'] = self
        return stats

    VirtualLayerV9.step = _hooked_step


def setup_cog_integration_patches():
    import v105_memory_readout as v105mr
    SubjectLayer = v105mr.SubjectLayer
    IntegrationManager = v105mr.IntegrationManager
    from esde_v82_engine import V82Engine

    _orig_subject_init = SubjectLayer.__init__
    def _captured_subject_init(self, *a, **k):
        _orig_subject_init(self, *a, **k); HOOK_STATE['cog'] = self
    SubjectLayer.__init__ = _captured_subject_init

    _orig_im_init = IntegrationManager.__init__
    def _captured_im_init(self, *a, **k):
        _orig_im_init(self, *a, **k)
        HOOK_STATE['alpha_mgr'] = getattr(self, 'alpha', None)
        HOOK_STATE['beta_mgr'] = getattr(self, 'beta', None)
    IntegrationManager.__init__ = _captured_im_init

    _orig_engine_init = V82Engine.__init__
    def _captured_engine_init(self, *a, **k):
        _orig_engine_init(self, *a, **k)
        HOOK_STATE['engine'] = self
        if getattr(self, 'realizer', None) is not None:
            _orig_realizer_step = self.realizer.step
            def _hooked_realizer_step(state):
                _orig_realizer_step(state)
                HOOK_STATE['per_step_counter'] += 1
                c = HOOK_STATE['per_step_counter']
                # per-step θ md5 (off vs small を後で diff)
                md5 = hashlib.md5(np.ascontiguousarray(state.theta).tobytes()).hexdigest()
                HOOK_STATE['theta_checksums'].append((c, md5))
                if c % N_PER_CHUNK == 0:
                    per_chunk_observe()
            self.realizer.step = _hooked_realizer_step
    V82Engine.__init__ = _captured_engine_init


def per_chunk_observe():
    cog = HOOK_STATE['cog']; vl = HOOK_STATE['vl']
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
    alpha_mgr = HOOK_STATE.get('alpha_mgr'); new_alpha_cids = set()
    if alpha_mgr is not None:
        cur = set(getattr(alpha_mgr, 'alphas', {}).keys())
        for aid in cur - HOOK_STATE['last_alpha_ids']:
            ai = alpha_mgr.alphas.get(aid)
            if ai is not None: new_alpha_cids.update(getattr(ai, 'member_cids', set()))
        HOOK_STATE['last_alpha_ids'] = cur
    beta_mgr = HOOK_STATE.get('beta_mgr'); new_beta_cids = set()
    if beta_mgr is not None:
        cur = set(getattr(beta_mgr, 'betas', {}).keys())
        for bid in cur - HOOK_STATE['last_beta_ids']:
            bi = beta_mgr.betas.get(bid)
            if bi is not None: new_beta_cids.update(getattr(bi, 'member_cids', set()))
        HOOK_STATE['last_beta_ids'] = cur
    new_pulse_cids = set()
    cur_pulse = getattr(cog, 'v10_pulse_count', {})
    if isinstance(cur_pulse, dict):
        for cid, pc in cur_pulse.items():
            if pc > HOOK_STATE['last_pulse_counts'].get(cid, 0): new_pulse_cids.add(cid)
        HOOK_STATE['last_pulse_counts'] = dict(cur_pulse)
    new_c_cids = set()
    cur_C = getattr(cog, 'C', {})
    if isinstance(cur_C, dict):
        for cid, cv in cur_C.items():
            if cv > HOOK_STATE['last_C_values'].get(cid, 0): new_c_cids.add(cid)
        HOOK_STATE['last_C_values'] = dict(cur_C)
    event_cids = new_births | new_deaths | new_alpha_cids | new_beta_cids | new_pulse_cids | new_c_cids
    if not event_cids:
        return
    cid_of_lid = getattr(cog, 'current_lid', {})
    for cid in event_cids:
        lid = cid_of_lid.get(cid)
        if lid is None: continue
        label = vl.labels.get(lid)
        if label is None or label.get('atomset_seed') is None: continue
        label['atomset_event_count'] = label.get('atomset_event_count', 0) + 1
        ec = label['atomset_event_count']
        bonus = BONUS_K * ec / (ec + BONUS_C0)
        label['atomset_bonus'] = bonus
        factor = 1.0 + TORQUE_GAIN * bonus
        label['torque_factor'] = factor
        # per-cid tag を逐次蓄積 (死んだ CID も残す)
        HOOK_STATE['cid_tags'][int(cid)] = {
            'cid': int(cid), 'atomset_seed': label.get('atomset_seed'),
            'event_count': int(ec), 'bonus': round(float(bonus), 6),
            'final_factor': round(float(factor), 6), 'is_bonus_target': True,
        }


def main():
    print(f'=== v12 M4 first-divergence 計装 ({CONDITION}, GAIN={TORQUE_GAIN}) ===')
    load_atom_centroids()
    setup_cog_integration_patches()
    patch_virtual_layer_step()
    import v105_memory_readout as v105mr
    cwd = Path.cwd(); os.chdir(V105_OUT_DIR)
    t0 = time.time()
    try:
        v105mr.run(seed=SEED, maturation_windows=MATURATION_WINDOWS,
                   tracking_windows=TRACKING_WINDOWS, window_steps=WINDOW_STEPS,
                   tag=f'v12_m4_{CONDITION}_seed0')
    finally:
        os.chdir(cwd)
    dt = time.time() - t0
    print(f'run 完了 ({dt:.1f}s), 発散={HOOK_STATE["theta_diverged"]}, '
          f'θ checksum {len(HOOK_STATE["theta_checksums"])} steps, '
          f'bonus 対象 cid {len(HOOK_STATE["cid_tags"])}')

    # dump
    pd.DataFrame(HOOK_STATE['theta_checksums'], columns=['step', 'theta_md5']).to_csv(
        OUT_DIR / 'theta_checksums.csv', index=False)
    (OUT_DIR / 'label_window_snapshot.json').write_text(
        json.dumps(HOOK_STATE['label_window_snapshot'], ensure_ascii=False, indent=1))
    tags = list(HOOK_STATE['cid_tags'].values())
    pd.DataFrame(tags).to_csv(OUT_DIR / 'cid_bonus_tags.csv', index=False)
    print(f'保存: {OUT_DIR}/ (theta_checksums.csv, label_window_snapshot.json, cid_bonus_tags.csv)')


if __name__ == '__main__':
    main()
