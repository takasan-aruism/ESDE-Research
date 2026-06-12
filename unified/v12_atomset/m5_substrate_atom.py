#!/usr/bin/env python3
"""v12 Atomset M5 — per-Atom 主体 + 別チャネル(torque_factor) substrate（筋3）

## 設計 (Taka 筋3 確定 + 二指摘、2026-06-12)
干渉(CID 物理が経験の state.E を撹拌)を解くため、主体を CID→AtomID に移し、物理値を
書かず torque_factor(係数)に乗せる。
- ① 主体=AtomID: 経験を per-Atom で積む(rate[atom])。CID は器。
- ② 別チャネル: label["torque_factor"]=g(rate[atomset_seed])。state.E/L/θ の値は書かない。
- ③ CID 間共有: 同 atomset_seed の CID は同じ rate[atom] を共有((i)厳密共有、(ii)伝播は後段)。
- ④ センサー地続き: 橋(入力 Atom)が rate[atom] を更新→その Atom を担う全 CID の torque に乗る。
- v9.7 guard: torque_factor は v9.7 の口 → slight + shuffle 対照維持。

## Taka 二指摘
(1) torque は θ の口=v9.7 のねじれ + 入力 E/L と通貨違い → corr≤0 なら CHANNEL=lambda(知覚側)へ。
(2) 係数でも torque は最終 θ を駆動し flow/gravity/Kuramoto と混ざる→θ で再混合の筋が残る。
    corr が正に転じるか=関門。やってみないと分からない(要検証)。

## 関門: 干渉検査やり直し
C(経験on,入力なし) vs A(baseline) で corr(rate[atom]-1, |Δexc|) が正に転じれば scramble されてない。
"""
import os, sys, json, math
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['MKL_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'
from pathlib import Path
from collections import deque, defaultdict
import numpy as np
import pandas as pd
import time

REPO = Path('/home/takasan/esde/ESDE-Research')
for p in ['primitive/v910','primitive/v911','primitive/v913','primitive/v914','primitive/v915',
          'primitive/v917','primitive/v918','autonomy/v82',
          'cognition/semantic_injection/v4_pipeline/v43','cognition/semantic_injection/v4_pipeline/v41',
          'ecology/engine','developmental/v104','developmental/v105','developmental/v106']:
    pp = str(REPO / p)
    if pp not in sys.path: sys.path.insert(0, pp)

MATURATION_WINDOWS = 2; WINDOW_STEPS = 500
# argv: CONDITION [SEED] [TRACKING] [CHANNEL]
CONDITION = sys.argv[1] if len(sys.argv) > 1 else 'A'
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 0
TRACKING_WINDOWS = int(sys.argv[3]) if len(sys.argv) > 3 else 15
# CHANNEL: 全部並行で撃つ (Taka)。torque/lambda/link/perception/gravity/multi
CHANNEL = sys.argv[4] if len(sys.argv) > 4 else 'torque'
# STRENGTH: over-drive 倍率 (Taka: cid 特異性が出始める閾値を探す)。1=slight 起点
STRENGTH = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0

# 入力なしで gate を測る: A=baseline, C=経験real, F=経験shuffle対照。B/D/E は入力込み(④用)。
COND_MAP = {'A': (False, 'off'), 'B': (True, 'off'), 'C': (False, 'on'),
            'D': (True, 'on'), 'E': (True, 'shuffle'), 'F': (False, 'shuffle')}
INPUT_ON, EXP_MODE = COND_MAP[CONDITION]

# 経験パラメータ (per-cid-axis robust_z は流用、主体だけ atom へ集約)
Z_CLIP = 4.0; MAD_C = 1.4826; FLOOR_REL = 10.0; DECAY_LAM = 0.97; ALPHA_EXP = 0.5
BUF = 50; K_MIN = 3
# per-Atom rate 集約 (additive standing, 有界)
ALPHA_ATOM = 0.5; DECAY_ATOM = 0.9
# torque_factor 別チャネル (slight 限定: tanh で graded saturate、hard clip だと飽和して
# 経験→効果の勾配が消え関門が判定不能になる)
G_TORQUE = 0.1; TF_HI = 1.6
# 各チャネルの gain (slight 限定)
G_LAMBDA = 0.5      # lambda: 出力励起を per-atom 注意で重み (θ 非経由)
G_LINK = 0.004; L_CAP = 0.01   # link: 他者との latent L (絞る、E2 結合の口)
G_PERC = 0.3        # perception: cog.attention を per-atom でスケール (受け取り方→dynamics)
G_GRAV = 0.3        # gravity: vl._gravity_factors を per-atom で (torque 同系・別係数)
TF_HI_MULTI = 1.3   # multi: torque を弱めに
G_FIELD = 1.0       # field: 文化が育った Atom 領域へ入力 addressing 重みを偏らせる (個体に書かない)

SELF_AXES = ['lifespan', 'n_core', 'C']
OTHER_AXES = ['fam_mean', 'n_partners', 'att_entropy']
AXES = SELF_AXES + OTHER_AXES

ATOM_CENTROIDS_PATH = REPO / 'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet'
CHTAG = f'{CHANNEL}_st{STRENGTH:g}'
OUT_DIR = REPO / 'unified/v12_atomset/run_m5_atom' / CHTAG / CONDITION / f'seed{SEED}'
OUT_DIR.mkdir(parents=True, exist_ok=True)
V105_OUT = Path(f'/tmp/v12_m5_atom_{CHTAG}_{CONDITION}_seed{SEED}'); V105_OUT.mkdir(parents=True, exist_ok=True)

H = {'vl': None, 'cog': None, 'engine': None, 'window': 0, 'last_input_window': -999,
     'theta_diverged': False,
     'buf': defaultdict(lambda: defaultdict(lambda: deque(maxlen=BUF))),
     'runmean': defaultdict(lambda: defaultdict(float)),
     'rate': defaultdict(lambda: defaultdict(lambda: 1.0)),   # cid->axis->rate (boost 計算用)
     'seen': defaultdict(lambda: defaultdict(int)),
     'atom_rate': defaultdict(lambda: 1.0),                   # ① 主体: atom->rate (per-Atom 文化)
     'cid_atom': {},                                          # cid->atomset_seed
     'records': [], 'monitor': [], 'input_events': [],
     'rng': np.random.default_rng(12345 + SEED), 'born_window': {}}

ATOM_PHASE = None; ATOM_NAMES = None; ATOM_MATRIX = None


def load_atoms():
    """atom_centroids → phase(addressing placeholder) と 48d matrix(rank_1 用)。"""
    global ATOM_PHASE, ATOM_NAMES, ATOM_MATRIX
    df = pd.read_parquet(ATOM_CENTROIDS_PATH)
    ATOM_NAMES = df['atom'].tolist()
    cols = [c for c in df.columns if c not in ('atom', 'n_words')]
    M = df[cols].values.astype(np.float64)
    norms = np.linalg.norm(M, axis=1, keepdims=True); norms[norms < 1e-9] = 1.0
    ATOM_MATRIX = (M / norms).astype(np.float32)
    Mc = M - M.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(Mc, full_matrices=False)
    pc = Mc @ Vt[:2].T
    ATOM_PHASE = {a: float(math.atan2(pc[i, 1], pc[i, 0]) % (2*math.pi)) for i, a in enumerate(ATOM_NAMES)}
    print(f'  atoms: {len(ATOM_NAMES)} (phase placeholder + 48d for rank_1)')


def rank1_atom(label):
    """誕生時 rank_1 Atom (M2 compute_rank_1_atom 流用: n_core + phase_sig の簡易 vector)。"""
    try:
        n = int(round(len(label.get('nodes', []))))
        ps = label.get('phase_sig', 0.0)
        vec = np.zeros(48, dtype=np.float32)
        sidx = 7 + min(max(n - 2, 0), 5)
        vec[sidx] = 1.0
        npn = abs(ps) / math.pi
        ti = min(int(npn * 7), 6); vec[ti] = 1.0
        nv = np.linalg.norm(vec)
        if nv < 1e-9: return None
        sims = ATOM_MATRIX @ (vec / nv)
        return ATOM_NAMES[int(np.argmax(sims))]
    except Exception:
        return None


def cdist(a, b):
    d = abs(a - b) % (2*math.pi); return min(d, 2*math.pi - d)


def lam_dyn(vl):
    macro = set(getattr(vl, 'macro_nodes', set()))
    ps = [l['phase_sig'] for lid, l in vl.labels.items() if lid not in macro]
    if len(ps) < 2: return 1.0
    cm = float(np.mean([math.cos(p) for p in ps])); sm = float(np.mean([math.sin(p) for p in ps]))
    r = math.sqrt(cm**2 + sm**2)
    cs = math.pi if r < 1e-9 else math.sqrt(-2*math.log(max(r, 1e-9)))
    return 1.0 / (cs + 1e-9)


def bridge_inject(atom_id):
    vl = H['vl']; eng = H['engine']
    if vl is None or eng is None or atom_id not in ATOM_PHASE: return {}
    theme = ATOM_PHASE[atom_id]; lam = lam_dyn(vl)
    macro = set(getattr(vl, 'macro_nodes', set()))
    # field channel: 文化が育った Atom 領域へ addressing 重みを偏らせる (個体に書かない)
    field_on = (CHANNEL == 'field' and EXP_MODE in ('on', 'shuffle'))
    lid2cid = {}
    if field_on:
        for c, l in getattr(H['cog'], 'current_lid', {}).items():
            if l is not None: lid2cid[l] = c
    cae = H.get('cid_atom_eff', {})
    w = {}
    for lid, lab in vl.labels.items():
        if lid in macro: continue
        base = math.exp(-lam * cdist(lab['phase_sig'], theme))
        if field_on:
            c = lid2cid.get(lid); a = cae.get(c) if c is not None else None
            ar = H['atom_rate'].get(a, 1.0) if a is not None else 1.0
            base *= max(0.0, 1.0 + G_FIELD * STRENGTH * (ar - 1.0))  # 文化が育った領域に降りやすい
        w[lid] = (base, list(lab['nodes']))
    if not w: return {}
    cands = []
    for lid in sorted(w, key=lambda l: -w[l][0])[:5]:
        cands += [n for n in w[lid][1] if n in eng.state.alive_n]
    cands = list(set(cands))[:50]
    if not cands: return {}
    E0 = {n: eng.state.E.get(n, 0.0) for n in cands}
    eng.physics.inject(eng.state, target_nodes=cands)
    n2c = H['cid_lid_node']; inj = defaultdict(float)
    for n in cands:
        c = n2c.get(n)
        if c is not None: inj[c] += eng.state.E.get(n, 0.0) - E0[n]
    return inj


def current_phase_avg(nodes, theta):
    th = [float(theta[n]) for n in nodes]
    if not th: return None
    return math.atan2(sum(math.sin(t) for t in th)/len(th), sum(math.cos(t) for t in th)/len(th)) % (2*math.pi)


def cid_axis_values(cid, label, cog):
    lifespan = max(0, H['window'] - H['born_window'].get(cid, H['window']))
    n_core = len(label.get('nodes', []))
    C = float(getattr(cog, 'C', {}).get(cid, 0))
    try: fam = float(cog.get_familiarity_mean(cid))
    except Exception: fam = 0.0
    try: npart = float(cog.get_n_partners(cid))
    except Exception: npart = 0.0
    try: ent = float(cog.get_attention_entropy(cid))
    except Exception: ent = 0.0
    return {'lifespan': lifespan, 'n_core': n_core, 'C': C, 'fam_mean': fam, 'n_partners': npart, 'att_entropy': ent}


def cid_boost(cid, vals):
    """per-cid-axis robust_z → combined boost (この CID の経験強度)。"""
    for a in AXES:
        v = vals[a]; rm = H['runmean'][cid][a]; n = H['seen'][cid][a]
        value = abs(v - rm) if n > 0 else 0.0
        buf = H['buf'][cid][a]
        if len(buf) >= K_MIN:
            arr = np.array(buf); med = np.median(arr); mad = np.median(np.abs(arr - med)) * MAD_C
            f = float(np.clip((value - med) / max(FLOOR_REL * mad, 1e-3), -Z_CLIP, Z_CLIP))
        else:
            f = 0.0
        r = H['rate'][cid][a]; r = 1.0 + (r - 1.0) * DECAY_LAM; r = max(0.1, r * (1.0 + ALPHA_EXP * f))
        H['rate'][cid][a] = r
        buf.append(value); H['seen'][cid][a] = n + 1; H['runmean'][cid][a] = rm + (v - rm) / (n + 1)
    return max(0.0, float(np.mean([H['rate'][cid][a] - 1.0 for a in AXES])))


def per_atom_experience_and_apply():
    """① per-cid boost → atom 集約 (atom_rate) → ② torque_factor/λ に乗せる (物理値は書かない)。
    EXP off は計算のみ・適用なし。shuffle は cid→atom を入替。返り値: per-cid の applied 量台帳。"""
    vl = H['vl']; cog = H['cog']
    applied = {}  # cid -> (atom_rate_used, tf)
    if vl is None or cog is None: return applied
    cid_of_lid = getattr(cog, 'current_lid', {})
    living = []
    node2cid = {}
    for cid, lid in cid_of_lid.items():
        if lid is None: continue
        lab = vl.labels.get(lid)
        if lab is None: continue
        if cid not in H['born_window']: H['born_window'][cid] = H['window']
        if cid not in H['cid_atom']:
            H['cid_atom'][cid] = rank1_atom(lab)
        for n in lab.get('nodes', []): node2cid[n] = cid
        living.append((cid, lid, lab))
    H['cid_lid_node'] = node2cid
    # per-cid boost
    boost = {}
    for cid, lid, lab in living:
        boost[cid] = cid_boost(cid, cid_axis_values(cid, lab, cog))
    # ① atom 集約: atom -> mean boost of その atom の cid 群、standing 更新
    atom_boost = defaultdict(list)
    for cid, _, _ in living:
        a = H['cid_atom'].get(cid)
        if a is not None: atom_boost[a].append(boost[cid])
    for a, bs in atom_boost.items():
        agg = float(np.mean(bs))
        H['atom_rate'][a] = 1.0 + DECAY_ATOM * (H['atom_rate'][a] - 1.0) + ALPHA_ATOM * agg
    # ② 適用 (EXP on/shuffle)。物理値は書かない、torque_factor/λ 係数だけ
    if EXP_MODE in ('on', 'shuffle'):
        cid_atom = dict(H['cid_atom'])
        if EXP_MODE == 'shuffle':  # cid→atom を入替 (cid 対応を壊す、rate 集合は同じ)
            cids = [c for c, _, _ in living]; atoms = [cid_atom.get(c) for c in cids]
            perm = list(atoms); H['rng'].shuffle(perm)
            cid_atom = {c: p for c, p in zip(cids, perm)}
        H['cid_atom_eff'] = cid_atom   # field/bridge が使う (shuffle 反映)
        eng = H['engine']; cog = H['cog']; vl = H['vl']
        for cid, lid, lab in living:
            a = cid_atom.get(cid)
            ar = H['atom_rate'].get(a, 1.0) if a is not None else 1.0
            e = ar - 1.0  # 経験の超過分
            if CHANNEL == 'field':
                # field: 個体には一切書かない。bridge_inject が世界(入力地形)を偏らせる
                applied[cid] = (ar, 1.0); continue
            tf_g = lambda hi, g: float(1.0 + (hi - 1.0) * math.tanh(g * e))  # graded saturate
            app = 1.0
            nodes = [n for n in lab.get('nodes', []) if n in eng.state.alive_n]
            if CHANNEL == 'torque':                    # (A) 力学: torque 係数 (θ via torque)
                # over-drive: STRENGTH で最大効果を拡大 (閾値探索)
                app = float(1.0 + STRENGTH * (TF_HI - 1.0) * math.tanh(G_TORQUE * e)); lab['torque_factor'] = app
            elif CHANNEL == 'lambda':                  # (B) 出力スケール (θ 非経由・読取)
                app = 1.0 + G_LAMBDA * e; lab['atom_attn'] = app
            elif CHANNEL == 'link':                    # (E2) 結合: 他者との latent L (値側)
                dL = min(STRENGTH * G_LINK * e, STRENGTH * L_CAP)
                for n in nodes:
                    for nb in list(eng.state.neighbors(n))[:2]:
                        eng.state.set_latent(n, nb, eng.state.get_latent(n, nb) + dL)
                app = 1.0 + dL
            elif CHANNEL == 'perception':              # (う) 受け取り方: cog.attention をスケール
                att = getattr(cog, 'attention', {}).get(cid)
                if att:
                    sc = 1.0 + G_PERC * math.tanh(e)
                    for k in list(att.keys()): att[k] *= sc
                    app = sc
            elif CHANNEL == 'gravity':                 # (E3) gravity_factor (torque 同系・別係数)
                gf = getattr(vl, '_gravity_factors', None)
                if gf is not None:
                    app = tf_g(TF_HI, G_GRAV); gf[lid] = gf.get(lid, 1.0) * app
            elif CHANNEL == 'multi':                   # (E1) 合成: torque 弱 + link 弱
                app = tf_g(TF_HI_MULTI, G_TORQUE); lab['torque_factor'] = app
                for n in nodes:
                    for nb in list(eng.state.neighbors(n))[:2]:
                        eng.state.set_latent(n, nb, eng.state.get_latent(n, nb) + min(0.5 * G_LINK * e, L_CAP))
            applied[cid] = (ar, app)
    else:
        H['cid_atom_eff'] = dict(H['cid_atom'])
        for cid, lid, lab in living:
            a = H['cid_atom'].get(cid)
            applied[cid] = (H['atom_rate'].get(a, 1.0) if a is not None else 1.0, 1.0)
    return applied


def patch_vl():
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
    _orig = VirtualLayerV9.step

    def hooked(self, state, window_count, islands=None, substrate=None):
        H['vl'] = self; H['window'] = int(window_count)
        # ② 経験→torque_factor を _orig(torque 適用) の前に設定 (係数なので毎 step 効く)
        applied = per_atom_experience_and_apply()
        stats = _orig(self, state, window_count, islands, substrate)
        # 橋 INPUT
        input_E = defaultdict(float)
        if INPUT_ON and window_count in INPUT_WINDOWS and H['engine'] is not None:
            atom = INPUT_ATOMS[INPUT_WINDOWS.index(window_count) % len(INPUT_ATOMS)]
            # 橋も rate[atom] を更新 (④ 入力 Atom が文化を育てる)
            H['atom_rate'][atom] = 1.0 + DECAY_ATOM * (H['atom_rate'][atom] - 1.0) + ALPHA_ATOM * 1.0
            input_E = bridge_inject(atom)
            H['last_input_window'] = int(window_count)
            H['input_events'].append({'window': int(window_count), 'atom': atom, 'n_cid': len(input_E)})
        # 出力読取 (current_phase_avg、λ channel は atom_attn で重み)
        eng = H['engine']
        if eng is not None:
            theta = eng.state.theta; lam = lam_dyn(self)
            alive = list(eng.state.alive_n)
            ta = np.array([float(theta[n]) for n in alive]) if alive else np.array([0.0])
            Ea = np.array([eng.state.E.get(n, 0.0) for n in alive]) if alive else np.array([0.0])
            cid_of_lid = getattr(H['cog'], 'current_lid', {}) if H['cog'] else {}
            lag = int(window_count) - H['last_input_window'] if H['last_input_window'] >= 0 else 999
            TWO = 2*math.pi
            # node→cid map (接続相手 cid 特定用)
            node2cid_out = {}
            for _c, _l in cid_of_lid.items():
                if _l is None: continue
                _lab = self.labels.get(_l)
                if _lab is None: continue
                for _n in _lab.get('nodes', []): node2cid_out[_n] = _c
            for cid, lid in cid_of_lid.items():
                if lid is None: continue
                lab = self.labels.get(lid)
                if lab is None: continue
                nodes = [n for n in lab.get('nodes', []) if n in eng.state.alive_n]
                if not nodes: continue
                cpa = current_phase_avg(nodes, theta)
                if cpa is None: continue
                d0 = np.abs(cpa - ta) % TWO; d = np.minimum(d0, TWO - d0)
                exc = float(np.sum(Ea * np.exp(-lam * d)))
                if CHANNEL == 'lambda':
                    exc *= lab.get('atom_attn', 1.0)   # λ channel: 注意係数で出力を重み (θ 非経由)
                # 接続グラフ metric (#4 Taka: link は誰と繋がるか): cid の次数 + 接続相手 cid 数
                deg = 0; partner_cids = set()
                for n in nodes:
                    for nb in eng.state.neighbors(n):
                        if nb in eng.state.alive_n:
                            deg += 1; pc = node2cid_out.get(nb)
                            if pc is not None and pc != cid: partner_cids.add(pc)
                ar, app = applied.get(cid, (1.0, 1.0))
                H['records'].append({
                    'condition': CONDITION, 'channel': CHANNEL, 'window': int(window_count), 'cid': int(cid),
                    'atom': H['cid_atom'].get(cid), 'exc': exc, 'atom_rate': float(ar), 'applied': float(app),
                    'input_E': float(input_E.get(cid, 0.0)), 'n_core': len(lab.get('nodes', [])),
                    'degree': int(deg), 'n_partner_cids': int(len(partner_cids)),
                    'lag_since_input': lag, 'is_reflex_window': int(0 <= lag <= 1)})
            nan = bool(np.any(~np.isfinite(ta))) or (len(ta) and np.max(np.abs(ta)) > 1e6)
            if nan: H['theta_diverged'] = True
            H['monitor'].append({'window': int(window_count), 'links': len(eng.state.alive_l),
                                 'alive': len(eng.state.alive_n), 'theta_nan': int(nan)})
        return stats
    VirtualLayerV9.step = hooked


def setup_capture():
    import v105_memory_readout as v105mr
    SubjectLayer = v105mr.SubjectLayer; IntegrationManager = v105mr.IntegrationManager
    from esde_v82_engine import V82Engine
    _os = SubjectLayer.__init__
    def cs(self, *a, **k): _os(self, *a, **k); H['cog'] = self
    SubjectLayer.__init__ = cs
    _oe = V82Engine.__init__
    def ce(self, *a, **k): _oe(self, *a, **k); H['engine'] = self
    V82Engine.__init__ = ce


# 入力を tracking 中盤〜後半に分散 (field は文化が育ってから入力が降る必要がある、立ち上がり対策)
INPUT_WINDOWS = [MATURATION_WINDOWS + k for k in (3, 6, 9, 12)]
INPUT_ATOMS = ['PRP.new', 'PER.hear']


def main():
    print(f'=== M5 per-Atom substrate — COND={CONDITION} seed{SEED} track{TRACKING_WINDOWS} CHANNEL={CHANNEL} ===')
    print(f'  ① 主体=AtomID(rate[atom]) ② 別チャネル={CHANNEL}(物理値書かない) ③ 厳密共有 ④ 橋 atom 更新')
    load_atoms(); setup_capture(); patch_vl()
    import v105_memory_readout as v105mr
    cwd = Path.cwd(); os.chdir(V105_OUT); t0 = time.time()
    try:
        v105mr.run(seed=SEED, maturation_windows=MATURATION_WINDOWS, tracking_windows=TRACKING_WINDOWS,
                   window_steps=WINDOW_STEPS, tag=f'v12_m5_atom_{CONDITION}_s{SEED}')
    finally:
        os.chdir(cwd)
    dt = time.time() - t0
    rec = pd.DataFrame(H['records']); mon = pd.DataFrame(H['monitor'])
    rec.to_parquet(OUT_DIR / 'records.parquet'); mon.to_parquet(OUT_DIR / 'monitor.parquet')
    dl = da = 0.0
    if len(mon) >= 2:
        dl = (mon['links'].iloc[-1] - mon['links'].iloc[0]) / max(mon['links'].iloc[0], 1) * 100
        da = (mon['alive'].iloc[-1] - mon['alive'].iloc[0]) / max(mon['alive'].iloc[0], 1) * 100
    summ = {'condition': CONDITION, 'channel': CHANNEL, 'seed': SEED, 'tracking': TRACKING_WINDOWS,
            'input_on': INPUT_ON, 'exp_mode': EXP_MODE, 'duration_sec': round(dt, 1),
            'n_records': len(rec), 'n_cids': int(rec['cid'].nunique()) if len(rec) else 0,
            'n_atoms': int(rec['atom'].nunique()) if len(rec) else 0,
            'theta_diverged': H['theta_diverged'],
            'atom_rate_max': float(max(H['atom_rate'].values())) if H['atom_rate'] else 1.0,
            'exc_std_across_cid': float(rec.groupby('cid')['exc'].mean().std()) if len(rec) else 0.0,
            'delta_links_pct': round(dl, 2), 'delta_alive_pct': round(da, 2)}
    (OUT_DIR / 'summary.json').write_text(json.dumps(summ, indent=2, ensure_ascii=False))
    print(f'\n=== {CONDITION} s{SEED} 完了 ({dt:.1f}s) θ_div={H["theta_diverged"]} ===')
    print(f'  records={len(rec)} cids={summ["n_cids"]} atoms={summ["n_atoms"]} atom_rate_max={summ["atom_rate_max"]:.3f}')
    print(f'  exc_std={summ["exc_std_across_cid"]:.3f}  Δlinks={dl:.1f}% Δalive={da:.1f}% θ_nan={"✗" if H["theta_diverged"] else "✓0"}')
    if H['theta_diverged']: sys.exit(1)


if __name__ == '__main__':
    main()
