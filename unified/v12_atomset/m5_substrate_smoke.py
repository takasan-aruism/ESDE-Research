#!/usr/bin/env python3
"""v12 Atomset M5 — 並行試行 substrate（橋 + 真ん中、E/L で噛み合わせ、混線見分け付き）

## 設計（Taka + GPT/Gemini 両監査、2026-06-12）
両方やる: (ろ)橋 言語→Atom→inject(E/L) ＋ (い)真ん中 経験を E/L に載せる（M-split-conn）。
同じ E/L 通貨で橋(入力)と真ん中(経験)が出会う。両方やるので E-crosstalk を見分ける計装を必須に。

### 二つの穴を塞ぐ（両監査指摘）
- (Gemini) 出力励起を固定 phase_sig でなく **current_phase_avg**（CID が今示す平均位相）で読む
  ＝経験で育てた個性が出口で消えるのを防ぐ。
- (GPT) E 混線は直接加算でなく二次誘導(INPUT→E増→活動増→EXP増)。タグだけでは不十分。
  → **2×2+shuffle 対照** A/B/C/D/E ＋ **lag 解析**（INPUT 直後 K window 除外、lag2+ で shuffle に
    消えれば経験寄与）。input_E/exp_E をタグ台帳で分離。

### 条件 (argv): (INPUT, EXP)
  A off/off (baseline) | B on/off (橋だけ=反射) | C off/on (経験単独) |
  D on/on (両方) | E on/shuffle (両方だが経験の cid 割当を入替)
対比: D−B=入力に経験が足した分 / C−A=経験単独 / D−E=cid 対応が本物 / B−A=橋だけの反射

### 口（M-split-conn、本命）: SELF経験→E（自分の存続）、OTHER経験→L（他者との結合、cliff 側で強く絞る）
### atom→theme_phase = addressing placeholder（意味でなく形式。「意味投影」と呼ばない）
### slight 監視: Δlinks<±5% Δalive<±10% θ_nan/inf=0 E/L 加算上限
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

SEED = 0; MATURATION_WINDOWS = 2; TRACKING_WINDOWS = 3; WINDOW_STEPS = 500; N_PER_CHUNK = 10

# 条件 (INPUT_ON, EXP_MODE)
COND_MAP = {'A': (False, 'off'), 'B': (True, 'off'), 'C': (False, 'on'),
            'D': (True, 'on'), 'E': (True, 'shuffle')}
CONDITION = sys.argv[1] if len(sys.argv) > 1 else 'A'
INPUT_ON, EXP_MODE = COND_MAP[CONDITION]

# 経験パラメータ (post-process 確定)
Z_CLIP = 4.0; MAD_C = 1.4826; FLOOR_REL = 10.0; DECAY_LAM = 0.97; ALPHA_EXP = 0.5
BUF = 50; K_MIN = 3
# 口の gain (slight 限定。OTHER→L は cliff 側で強く絞る)
G_E = 0.02; E_CAP = 0.05      # SELF→E
G_L = 0.004; L_CAP = 0.01     # OTHER→L (絞る)
LAG_EXCLUDE = 1               # INPUT 直後 K window は反射として除外フラグ

SELF_AXES = ['lifespan', 'n_core', 'C']
OTHER_AXES = ['fam_mean', 'n_partners', 'att_entropy']
AXES = SELF_AXES + OTHER_AXES

ATOM_CENTROIDS_PATH = REPO / 'unified/v1103/outputs/main/atom_centroids_48d_normalized.parquet'
OUT_DIR = REPO / 'unified/v12_atomset/run_m5_substrate' / CONDITION
OUT_DIR.mkdir(parents=True, exist_ok=True)
V105_OUT = Path(f'/tmp/v12_m5_sub_{CONDITION}_seed0'); V105_OUT.mkdir(parents=True, exist_ok=True)

H = {'vl': None, 'cog': None, 'engine': None, 'alpha_mgr': None, 'beta_mgr': None,
     'per_step': 0, 'window': 0, 'last_input_window': -999,
     'theta_diverged': False,
     # 経験 state
     'buf': defaultdict(lambda: defaultdict(lambda: deque(maxlen=BUF))),  # cid->axis->deque
     'runmean': defaultdict(lambda: defaultdict(float)),                  # cid->axis->mean
     'rate': defaultdict(lambda: defaultdict(lambda: 1.0)),              # cid->axis->rate
     'seen_count': defaultdict(lambda: defaultdict(int)),
     # 台帳 (per window per cid)
     'records': [],
     'monitor': [],  # per window: links, alive, theta_nan
     'input_events': [],
     'rng': np.random.default_rng(12345),
     'born_window': {},
     }

ATOM_PHASE = None  # addressing placeholder


def build_atom_phase():
    """atom 48d → 主成分 2 軸 → atan2 → phase。addressing placeholder（意味でなく形式）。"""
    global ATOM_PHASE
    df = pd.read_parquet(ATOM_CENTROIDS_PATH)
    cols = [c for c in df.columns if c not in ('atom', 'n_words')]
    M = df[cols].values.astype(np.float64)
    M = M - M.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(M, full_matrices=False)
    pc = M @ Vt[:2].T  # (n_atom, 2)
    ATOM_PHASE = {atom: float(math.atan2(pc[i, 1], pc[i, 0]) % (2 * math.pi))
                  for i, atom in enumerate(df['atom'].tolist())}
    print(f'  atom_phase (addressing placeholder): {len(ATOM_PHASE)} atoms')


# ---- addressing (v1111c 流用) ----
def cdist(a, b):
    d = abs(a - b) % (2 * math.pi)
    return min(d, 2 * math.pi - d)


def lam_dyn(vl):
    macro = set(getattr(vl, 'macro_nodes', set()))
    ps = [l['phase_sig'] for lid, l in vl.labels.items() if lid not in macro]
    if len(ps) < 2: return 1.0
    cm = float(np.mean([math.cos(p) for p in ps])); sm = float(np.mean([math.sin(p) for p in ps]))
    r = math.sqrt(cm**2 + sm**2)
    cs_std = math.pi if r < 1e-9 else math.sqrt(-2 * math.log(max(r, 1e-9)))
    return 1.0 / (cs_std + 1e-9)


def bridge_inject(atom_id):
    """橋: atom → theme_phase → label_weights(phase_sig) → targets → inject(E,L)。tag=INPUT。"""
    vl = H['vl']; eng = H['engine']
    if vl is None or eng is None or atom_id not in ATOM_PHASE: return {}
    theme = ATOM_PHASE[atom_id]; lam = lam_dyn(vl)
    macro = set(getattr(vl, 'macro_nodes', set()))
    w = {}
    for lid, lab in vl.labels.items():
        if lid in macro: continue
        w[lid] = (math.exp(-lam * cdist(lab['phase_sig'], theme)), list(lab['nodes']))
    if not w: return {}
    slids = sorted(w, key=lambda l: -w[l][0])[:5]
    cands = []
    for lid in slids:
        for n in w[lid][1]:
            if n in eng.state.alive_n: cands.append(n)
    cands = list(set(cands))[:50]
    if not cands: return {}
    E0 = {n: eng.state.E.get(n, 0.0) for n in cands}
    eng.physics.inject(eng.state, target_nodes=cands)
    # tag: 注入で増えた E を cid へ帰属
    inj = defaultdict(float)
    node2cid = H['node2cid']
    for n in cands:
        dE = eng.state.E.get(n, 0.0) - E0[n]
        c = node2cid.get(n)
        if c is not None: inj[c] += dE
    return inj


def current_phase_avg(nodes, theta):
    th = [float(theta[n]) for n in nodes]
    if not th: return None
    return math.atan2(sum(math.sin(t) for t in th) / len(th),
                      sum(math.cos(t) for t in th) / len(th)) % (2 * math.pi)


# ---- 経験計算 (live, robust_z + 種類分け + 衰退 + floor) ----
def axis_values(cid, label, cog):
    """live で reduced cid_vec の各軸の生値。"""
    lifespan = max(0, H['window'] - H['born_window'].get(cid, H['window']))
    n_core = len(label.get('nodes', []))
    C = float(getattr(cog, 'C', {}).get(cid, 0))
    try: fam_mean = float(cog.get_familiarity_mean(cid))
    except Exception: fam_mean = 0.0
    try: n_partners = float(cog.get_n_partners(cid))
    except Exception: n_partners = 0.0
    try: att_entropy = float(cog.get_attention_entropy(cid))
    except Exception: att_entropy = 0.0
    return {'lifespan': lifespan, 'n_core': n_core, 'C': C,
            'fam_mean': fam_mean, 'n_partners': n_partners, 'att_entropy': att_entropy}


def update_experience(cid, vals):
    """各軸: value=|v-runmean| → pre-event robust_z f → rate を decay+(1+αf)。"""
    for a in AXES:
        v = vals[a]
        rm = H['runmean'][cid][a]; n = H['seen_count'][cid][a]
        value = abs(v - rm) if n > 0 else 0.0
        buf = H['buf'][cid][a]
        # pre-event 統計 (現 value を入れる前の buffer)。floor = max(FLOOR_REL×MAD, 絶対floor)
        # = post-process と同じ per-axis 相対 floor (典型は f≈0、外れだけ動く＝slight・graded)
        if len(buf) >= K_MIN:
            arr = np.array(buf)
            med = np.median(arr); mad = np.median(np.abs(arr - med)) * MAD_C
            scale = max(FLOOR_REL * mad, 1e-3)
            f = float(np.clip((value - med) / scale, -Z_CLIP, Z_CLIP))
        else:
            f = 0.0
        # rate 更新 (decay then surprise)
        r = H['rate'][cid][a]
        r = 1.0 + (r - 1.0) * DECAY_LAM
        r = max(0.1, r * (1.0 + ALPHA_EXP * f))
        H['rate'][cid][a] = r
        # buffer/runmean 更新
        buf.append(value)
        H['seen_count'][cid][a] = n + 1
        H['runmean'][cid][a] = rm + (v - rm) / (n + 1)
    self_boost = max(0.0, float(np.mean([H['rate'][cid][a] - 1.0 for a in SELF_AXES])))
    other_boost = max(0.0, float(np.mean([H['rate'][cid][a] - 1.0 for a in OTHER_AXES])))
    return self_boost, other_boost


def per_window_experience():
    """per-window で経験を更新+適用 (cog state は per-window 更新なので per-window が正しい粒度。
    per-chunk だと同一値を 50×更新して rate が爆発する)。返り値: exp_E, exp_L の per-cid 台帳。"""
    vl = H['vl']; cog = H['cog']; eng = H['engine']
    exp_E = defaultdict(float); exp_L = defaultdict(float)
    if vl is None or cog is None or eng is None: return exp_E, exp_L
    cid_of_lid = getattr(cog, 'current_lid', {})
    # node→cid map (今 window 分)
    node2cid = {}
    living = []
    for cid, lid in cid_of_lid.items():
        if lid is None: continue
        lab = vl.labels.get(lid)
        if lab is None: continue
        if cid not in H['born_window']: H['born_window'][cid] = H['window']
        for n in lab.get('nodes', []): node2cid[n] = cid
        living.append((cid, lab))
    H['node2cid'] = node2cid
    # 経験計算
    boosts = {}
    for cid, lab in living:
        vals = axis_values(cid, lab, cog)
        sb, ob = update_experience(cid, vals)
        boosts[cid] = (sb, ob)
    # shuffle: cid→boost 割当を入替 (橋入力は別、経験のみ)
    if EXP_MODE == 'shuffle' and boosts:
        cids = list(boosts.keys()); perm = list(cids)
        H['rng'].shuffle(perm)
        boosts = {c: boosts[p] for c, p in zip(cids, perm)}
    # 適用 (EXP on/shuffle のみ)
    if EXP_MODE in ('on', 'shuffle'):
        for cid, lab in living:
            sb, ob = boosts[cid]
            nodes = [n for n in lab.get('nodes', []) if n in eng.state.alive_n]
            # SELF→E
            dE_total = 0.0
            for n in nodes:
                dE = min(G_E * sb, E_CAP)
                eng.state.E[n] = min(1.0, eng.state.E.get(n, 0.0) + dE); dE_total += dE
            # OTHER→L (絞る)
            dL_total = 0.0
            for n in nodes:
                for nb in list(eng.state.neighbors(n))[:2]:
                    dL = min(G_L * ob, L_CAP)
                    eng.state.set_latent(n, nb, eng.state.get_latent(n, nb) + dL); dL_total += dL
            exp_E[cid] += dE_total
            exp_L[cid] += dL_total
    return exp_E, exp_L


def patch_vl():
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
    _orig = VirtualLayerV9.step

    def hooked(self, state, window_count, islands=None, substrate=None):
        H['vl'] = self; H['window'] = int(window_count)
        stats = _orig(self, state, window_count, islands, substrate)
        # 経験を per-window で更新+適用 (SELF→E, OTHER→L)。台帳 exp_E/exp_L を受ける
        exp_E, exp_L = per_window_experience()
        H['chunk_exp_E'] = exp_E; H['chunk_exp_L'] = exp_L
        # 橋 INPUT (window 境界で、INPUT_ON かつ 所定 window)
        input_E = defaultdict(float)
        if INPUT_ON and window_count in INPUT_WINDOWS and H['engine'] is not None:
            atom = INPUT_ATOMS[INPUT_WINDOWS.index(window_count) % len(INPUT_ATOMS)]
            input_E = bridge_inject(atom)
            H['last_input_window'] = int(window_count)
            H['input_events'].append({'window': int(window_count), 'atom': atom,
                                      'n_cid': len(input_E)})
        # 出力読取 (current_phase_avg)
        eng = H['engine']
        if eng is not None:
            theta = eng.state.theta; lam = lam_dyn(self)
            alive = list(eng.state.alive_n)
            E = eng.state.E
            TWO_PI = 2 * math.pi
            theta_arr = np.array([float(theta[n]) for n in alive]) if alive else np.array([0.0])
            E_arr = np.array([E.get(n, 0.0) for n in alive]) if alive else np.array([0.0])
            cid_of_lid = getattr(H['cog'], 'current_lid', {}) if H['cog'] else {}
            lag = int(window_count) - H['last_input_window'] if H['last_input_window'] >= 0 else 999
            for cid, lid in cid_of_lid.items():
                if lid is None: continue
                lab = self.labels.get(lid)
                if lab is None: continue
                nodes = [n for n in lab.get('nodes', []) if n in eng.state.alive_n]
                if not nodes: continue
                cpa = current_phase_avg(nodes, theta)
                if cpa is None: continue
                d0 = np.abs(cpa - theta_arr) % TWO_PI
                d = np.minimum(d0, TWO_PI - d0)
                exc = float(np.sum(E_arr * np.exp(-lam * d)))
                H['records'].append({
                    'condition': CONDITION, 'window': int(window_count), 'cid': int(cid),
                    'exc': float(exc), 'cpa': float(cpa), 'n_core': len(lab.get('nodes', [])),
                    'input_E': float(input_E.get(cid, 0.0)),
                    'exp_E': float(H['chunk_exp_E'].get(cid, 0.0)),
                    'exp_L': float(H['chunk_exp_L'].get(cid, 0.0)),
                    'self_boost': float(np.mean([H['rate'][cid][a] - 1 for a in SELF_AXES])),
                    'other_boost': float(np.mean([H['rate'][cid][a] - 1 for a in OTHER_AXES])),
                    'lag_since_input': lag, 'is_reflex_window': int(0 <= lag <= LAG_EXCLUDE),
                })
            # slight 監視
            th = np.array([float(theta[n]) for n in alive]) if alive else np.array([0.0])
            nan = bool(np.any(~np.isfinite(th)))
            if nan or (alive and np.max(np.abs(th)) > 1e6): H['theta_diverged'] = True
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
    _oi = IntegrationManager.__init__
    def ci(self, *a, **k):
        _oi(self, *a, **k); H['alpha_mgr'] = getattr(self, 'alpha', None); H['beta_mgr'] = getattr(self, 'beta', None)
    IntegrationManager.__init__ = ci
    _oe = V82Engine.__init__
    def ce(self, *a, **k):
        _oe(self, *a, **k); H['engine'] = self
    V82Engine.__init__ = ce


# 橋の入力スケジュール (maturation 後の tracking window で Atom を順に inject)
INPUT_WINDOWS = [MATURATION_WINDOWS, MATURATION_WINDOWS + 1]  # = window 2,3
INPUT_ATOMS = ['PRP.new', 'PER.hear']  # 代理入力 (人間語の placeholder)


def main():
    print(f'=== M5 substrate smoke — COND={CONDITION} (INPUT={INPUT_ON}, EXP={EXP_MODE}) ===')
    print(f'  口: SELF→E (G_E={G_E}), OTHER→L (G_L={G_L} 絞る)、出力=current_phase_avg')
    print(f'  橋 INPUT window={INPUT_WINDOWS} atoms={INPUT_ATOMS} (addressing placeholder)\n')
    build_atom_phase(); setup_capture(); patch_vl()
    H['chunk_exp_E'] = defaultdict(float); H['chunk_exp_L'] = defaultdict(float)
    import v105_memory_readout as v105mr
    cwd = Path.cwd(); os.chdir(V105_OUT)
    t0 = time.time()
    try:
        v105mr.run(seed=SEED, maturation_windows=MATURATION_WINDOWS, tracking_windows=TRACKING_WINDOWS,
                   window_steps=WINDOW_STEPS, tag=f'v12_m5_sub_{CONDITION}_seed0')
    finally:
        os.chdir(cwd)
    dt = time.time() - t0
    rec = pd.DataFrame(H['records']); mon = pd.DataFrame(H['monitor'])
    rec.to_parquet(OUT_DIR / 'records.parquet'); mon.to_parquet(OUT_DIR / 'monitor.parquet')
    # slight 監視判定
    d_links = d_alive = 0.0
    if len(mon) >= 2:
        l0, l1 = mon['links'].iloc[0], mon['links'].iloc[-1]
        a0, a1 = mon['alive'].iloc[0], mon['alive'].iloc[-1]
        d_links = (l1 - l0) / max(l0, 1) * 100; d_alive = (a1 - a0) / max(a0, 1) * 100
    summary = {
        'condition': CONDITION, 'input_on': INPUT_ON, 'exp_mode': EXP_MODE, 'duration_sec': round(dt, 1),
        'n_records': len(rec), 'n_cids': int(rec['cid'].nunique()) if len(rec) else 0,
        'theta_diverged': H['theta_diverged'],
        'sum_input_E': float(rec['input_E'].sum()) if len(rec) else 0.0,
        'sum_exp_E': float(rec['exp_E'].sum()) if len(rec) else 0.0,
        'sum_exp_L': float(rec['exp_L'].sum()) if len(rec) else 0.0,
        'exc_mean': float(rec['exc'].mean()) if len(rec) else 0.0,
        'exc_std_across_cid': float(rec.groupby('cid')['exc'].mean().std()) if len(rec) else 0.0,
        'delta_links_pct': round(d_links, 2), 'delta_alive_pct': round(d_alive, 2),
        'input_events': H['input_events'],
    }
    (OUT_DIR / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n=== COND {CONDITION} 完了 ({dt:.1f}s) ===')
    print(f'  records={len(rec)}, cids={summary["n_cids"]}, θ発散={H["theta_diverged"]}')
    print(f'  Σinput_E={summary["sum_input_E"]:.3f}, Σexp_E={summary["sum_exp_E"]:.3f}, Σexp_L={summary["sum_exp_L"]:.4f}')
    print(f'  exc_mean={summary["exc_mean"]:.3f}, exc_std_across_cid={summary["exc_std_across_cid"]:.3f}')
    print(f'  slight 監視: Δlinks={d_links:.1f}% Δalive={d_alive:.1f}% θ_nan={"✗" if H["theta_diverged"] else "✓0"}')
    print(f'  保存: {OUT_DIR}')
    if H['theta_diverged']:
        print('  赤信号: θ 発散'); sys.exit(1)


if __name__ == '__main__':
    main()
