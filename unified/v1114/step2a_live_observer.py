#!/usr/bin/env python3
"""v1114 Step 2-A 生きた Center 観察基盤 (案 b-1、v105_memory_readout.run() 直接呼び)

## 観察対象注釈ブロック (実装着手前に明示、Code A 自己強制ハードル)

### 観察対象の本質
- 同じ系内 (Center 単体、Atom なし)
- Step 1b (post-process) を生きた run に置換 + Step 1b で取れなかった 2 軸を本物で取る
- **観察のみ、書き戻しなし** (Web Claude 設計 §6 厳守、§3 自己擦り込みは Taka 判断待ちで保留)

### 過去成功事例との照合 (実機検証済み)
- v918_memory_readout.run() = 物理層正規実装、IntegrationManager なし
- **v105_memory_readout.run() = v918 同一物理層 + IntegrationManager 並走** (line 256 で
  `from v105_integration import IntegrationManagerV105 as IntegrationManager`)
- engine/VirtualLayer 設定は v918 と v105 で完全同一 (実機 grep 確認 2026-06-07)
- 物理層は同一、α/β は IntegrationManager が概念層で並走 (Taka 整理「Integration は物理に触らない」)

### 過去失敗パターン回避
- v1110-v1113 = 異なる系の対応関係発想で 4 連続失敗
- 本実装は Center 単体、cid id は認知 ID (node ID でない)
- monkey-patch は engine.state を読むだけ (完全 read-only ラッパー、Taka 規律 (3-2))

### 残さないもの (Step 1b 継続)
- node ID / 座標 / 不透明 float / 判定数値 (z) / 設計パラメータ / 差・有意差
- 近似値の擦り替え (Taka 規律「すり替えない」)

### 残すフィールド (実機確認済み、Step 1b + 解消 2 軸)
- cid (認知 ID、node ID でない)
- trigger (記号 7 種、独立監視)
- point: n_core / lifespan / lifecycle_phase / formation_relation / pulse_reactivity / C / Q_remaining
- neighborhood: familiarity_n + **familiarity_sizes** (= 周辺の大きさ、生きた run で取得可)

### M1 二重検証 (Taka 規律 (2))
- (i) 物理層: v105 物理が v918 と bit-identical
  - 既存 v918 main run output (per_subject_seed0.csv) と比較
  - 離散構造 (label birth 順 / cid 発番順 / 誕生・死 window / n_core) 完全一致
  - 連続値 (theta) は同一 seed で同一軌跡なら可
- (ii) α/β 層: v105 Integration 出力が v107 source_events と整合
  - 離散構造 (どの cid が どの window で α/β 形成) 一致
  - 形成付随小数差は問わない (Taka 規律 (6))

### Step 2-A 範囲 (Web Claude 設計 §1+§4 のみ、§3 保留)
- 観察のみ、書き戻しなし
- 7 種引き金独立監視 (Step 1b 同じ EWMA+z ロジック)
- lifecycle_phase は cog.born_at 直接 = unknown は生存中のみ
- familiarity_sizes は cog.familiarity[cid].keys() の相手 n_core (取れない相手は飛ばす)

### Fall back 条件 (Taka 規律 (4)(7))
- step_window(500) vs step_window(10)×50 で物理 bit-identity が崩れる場合 → (b-2) v918 に Integration patch
- per-10step 粒度が保てない場合 → 同上、per-window に勝手に変えない
"""
import os, sys
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import json, time
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

REPO = Path('/home/takasan/esde/ESDE-Research')

PATHS = [
    REPO / 'primitive/v910',
    REPO / 'primitive/v911',
    REPO / 'primitive/v913',
    REPO / 'primitive/v914',
    REPO / 'primitive/v915',
    REPO / 'primitive/v917',
    REPO / 'primitive/v918',
    REPO / 'autonomy/v82',
    REPO / 'cognition/semantic_injection/v4_pipeline/v43',
    REPO / 'cognition/semantic_injection/v4_pipeline/v41',
    REPO / 'ecology/engine',
    REPO / 'developmental/v104',
    REPO / 'developmental/v105',
]
for p in PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# === 構成 (smoke/main 出力 dir 分離、Taka 指示 2026-06-08 上書き事故防止) ===
SEED = 0
IS_SMOKE = os.environ.get('STEP2A_SMOKE') == '1'
if IS_SMOKE:
    MATURATION_WINDOWS = 2
    TRACKING_WINDOWS = 3
    OUT_DIR = REPO / 'unified/v1114/run_step2a_smoke'
    V105_OUT_DIR = Path('/tmp/v105_step2a_seed0_smoke')
else:
    MATURATION_WINDOWS = 20
    TRACKING_WINDOWS = 50
    OUT_DIR = REPO / 'unified/v1114/run_step2a'
    V105_OUT_DIR = Path('/tmp/v105_step2a_seed0_main')
WINDOW_STEPS = 500
N_PER_CHUNK = 10  # per-10step 観察
EWMA_ALPHA = 0.2
Z_NOTICE = 2.0
Z_ANOMALY = 3.0
WARMUP_CHUNKS = 10

OUT_DIR.mkdir(parents=True, exist_ok=True)
V105_OUT_DIR.mkdir(parents=True, exist_ok=True)

TRIGGER_TYPES = ['pulse', 'ingestion', 'alpha_formation', 'beta_formation',
                 'c_conversion', 'cid_birth', 'cid_death']


# === Global hook state (engine.state を読むだけ、書き戻し禁止) ===
HOOK_STATE = {
    'cog': None,
    'integration_mgr': None,
    'alpha_mgr': None,
    'beta_mgr': None,
    'engine': None,
    'global_step': 0,
    'records': [],
    'order': 0,
    'running_stats': {et: {'mean': 0.0, 'var': 1.0, 'count': 0} for et in TRIGGER_TYPES},
    # event 検出用 prev state
    'last_cids': set(),
    'last_dead_cids': set(),
    'last_alpha_ids': set(),
    'last_beta_ids': set(),
    'last_pulse_counts': {},  # cid -> count
    'last_C_values': {},      # cid -> C value
    'last_ingestion_count': 0,
    'patch_chunk_count': 0,  # patch 経由 chunk 数 (検証用)
    'patch_remainder_count': 0,  # 余り step 数 (検証用)
    # === Task 223 残課題 2: reap で pop される前に capture (Taka 指示 2026-06-08) ===
    'captured_born_at': {},      # cid -> birth_window (alive 中に capture)
    'captured_host_lost_at': {},  # cid -> host_lost_window (死亡確定時に capture)
}


def safe_int(v, default=0):
    if v is None:
        return default
    try:
        if isinstance(v, float) and np.isnan(v):
            return default
        return int(v)
    except (ValueError, TypeError):
        return default


def ewma_update(stat, value, alpha=EWMA_ALPHA):
    """Step 1b と同じ EWMA + z-score (内部のみ、レコードに z 残さない)"""
    stat['count'] += 1
    if stat['count'] <= WARMUP_CHUNKS:
        n = stat['count']
        stat['mean'] = (stat['mean'] * (n - 1) + value) / n
        stat['var'] = max(stat['var'], 0.1)
        return 0.0
    delta = value - stat['mean']
    stat['mean'] += alpha * delta
    stat['var'] = (1 - alpha) * (stat['var'] + alpha * delta ** 2)
    std = np.sqrt(stat['var'])
    return delta / std if std > 1e-9 else 0.0


def get_familiarity_sizes(cog, cid):
    """生きた run: cog.familiarity[cid].keys() で相手 cid 集合 → 各 n_core
    Taka 規律: 取れない相手 (ghost/reaped) は正直に飛ばす (偽値で埋めない)
    """
    fam_dict = getattr(cog, 'familiarity', {}).get(cid, {})
    if not isinstance(fam_dict, dict):
        return []
    partner_cids = list(fam_dict.keys())
    sizes = []
    v11_m_c = getattr(cog, 'v11_m_c', {})
    for pcid in partner_cids:
        mc = v11_m_c.get(pcid)
        if mc is not None and isinstance(mc, dict) and 'n_core' in mc:
            sizes.append(int(mc['n_core']))
        # 取れない相手は飛ばす (規律遵守、近似で埋めない)
    return sizes


def get_lifecycle_phase(cog, cid, current_global_step):
    """生きた run: cog.born_at / host_lost_at 直接 (Step 1b の time scale ズレ問題なし)

    Task 223 残課題 2 (Taka 指示 2026-06-08): cog.born_at[cid] が reap で pop される
    可能性があるため、HOOK_STATE['captured_born_at'] / ['captured_host_lost_at'] (alive
    中に capture したもの) を優先参照する。
    """
    # 1. captured cache を優先参照 (reap 前に保存されたもの)
    captured_born = HOOK_STATE['captured_born_at'].get(cid)
    captured_host_lost = HOOK_STATE['captured_host_lost_at'].get(cid)

    # 2. 現在の cog 状態 (fallback)
    born_at_dict = getattr(cog, 'born_at', {})
    host_lost_at_dict = getattr(cog, 'host_lost_at', {})
    cur_born = born_at_dict.get(cid)
    cur_host_lost = host_lost_at_dict.get(cid)

    # birth_window 決定 (capture 優先、なければ現在 cog)
    birth_window = captured_born if captured_born is not None else cur_born
    if birth_window is None:
        return 'unknown'  # 誕生情報なし
    birth_step = int(birth_window) * WINDOW_STEPS

    # host_lost_window 決定 (capture 優先、なければ現在 cog)
    host_lost_window = captured_host_lost
    if host_lost_window is None and cur_host_lost is not None:
        host_lost_window = cur_host_lost
    if host_lost_window is None:
        return 'unknown'  # 生存中 (censored)
    death_step = int(host_lost_window) * WINDOW_STEPS

    total = death_step - birth_step
    if total <= 0:
        return 'unknown'
    age = current_global_step - birth_step
    if age < 0 or age > total:
        return 'unknown'
    return round(age / total, 3)


def get_n_core(cog, cid):
    """cog.v11_m_c[cid]['n_core'] から取得、なければ unknown"""
    v11_m_c = getattr(cog, 'v11_m_c', {})
    mc = v11_m_c.get(cid)
    if mc is not None and isinstance(mc, dict) and 'n_core' in mc:
        return int(mc['n_core'])
    return 'unknown'


def get_C_Q(cog, cid):
    """C, Q_remaining を cog から取得"""
    C_dict = getattr(cog, 'C', {})
    C_val = C_dict.get(cid, 'unknown') if isinstance(C_dict, dict) else 'unknown'
    if C_val != 'unknown':
        try:
            C_val = int(C_val)
        except (ValueError, TypeError):
            C_val = 'unknown'
    # Q_remaining: v915_buffers から (buf.Q_remaining)
    v915_buffers = getattr(cog, 'v915_buffers', {})
    buf = v915_buffers.get(cid) if isinstance(v915_buffers, dict) else None
    if buf is not None and hasattr(buf, 'Q_remaining'):
        Q_val = int(buf.Q_remaining) if buf.Q_remaining is not None else 'unknown'
    else:
        Q_val = 'unknown'
    return C_val, Q_val


def get_formation_relation(cog, cid, current_global_step):
    """alpha 形成時刻 vs 注意時刻 で判定。alpha_mgr から取得。

    Task 222 残課題 1 (Taka 指示 2026-06-08): cid_to_alphas が空のままだった (ghost で
    pop される等) ため、alphas[aid].member_cids + member_history を直接 lookup する。
    """
    alpha_mgr = HOOK_STATE.get('alpha_mgr')
    if alpha_mgr is None:
        return 'no_alpha'
    alphas = getattr(alpha_mgr, 'alphas', {})
    # この cid が member (現在) or member_history (過去) だった alpha を直接探す
    earliest_global_step = None
    for aid, ai in alphas.items():
        members = getattr(ai, 'member_cids', set())
        history = getattr(ai, 'member_history', set())
        if cid not in members and cid not in history:
            continue
        # alpha 形成時刻: born_global_step or born_window
        gs = getattr(ai, 'born_global_step', None)
        if gs is None:
            bw = getattr(ai, 'born_window', None)
            if bw is not None:
                gs = int(bw) * WINDOW_STEPS
        if gs is not None:
            if earliest_global_step is None or gs < earliest_global_step:
                earliest_global_step = gs
    if earliest_global_step is None:
        return 'no_alpha'
    delta = current_global_step - earliest_global_step
    if delta < 0:
        return 'before'
    elif delta <= 100:
        return 'after_0_100'
    else:
        return 'after_100plus'


def get_pulse_reactivity(cog, cid):
    """cog.v10_pulse_count[cid] (本物)"""
    return safe_int(getattr(cog, 'v10_pulse_count', {}).get(cid, 0))


def get_lifespan(cog, cid, current_global_step):
    """current_global_step - birth_step (= 現時点での年齢)"""
    born_at = getattr(cog, 'born_at', {})
    if cid not in born_at:
        return 0
    birth_step = int(born_at[cid]) * WINDOW_STEPS
    return max(0, current_global_step - birth_step)


def build_record(cog, cid, trigger, current_global_step):
    """percept レコード生成 (記号 + 構造のみ、判定数値・座標・差なし)

    Taka 判断 (2026-06-08): formation_relation と lifecycle_phase は v105 hook で
    100% 退化 (no_alpha / unknown) するため落とす (取れないなら落とす規律)。
    残す軸: n_core / lifespan / pulse_reactivity / C / Q_remaining / familiarity_n / familiarity_sizes
    """
    point = {
        'n_core': get_n_core(cog, cid),
        'lifespan': get_lifespan(cog, cid, current_global_step),
        'pulse_reactivity': get_pulse_reactivity(cog, cid),
    }
    C_val, Q_val = get_C_Q(cog, cid)
    point['C'] = C_val
    point['Q_remaining'] = Q_val
    neighborhood = {
        'familiarity_n': len(getattr(cog, 'familiarity', {}).get(cid, {})),
        'familiarity_sizes': get_familiarity_sizes(cog, cid),  # 本物の相手 n_core list (Step 1b で取れず、本実装の成果)
    }
    return {
        'order': HOOK_STATE['order'],
        'cid': int(cid),
        'trigger': trigger,
        'point': point,
        'neighborhood': neighborhood,
    }


def per_chunk_observe(engine):
    """per-N-step hook: engine.state を読むだけ、書き戻し禁止
    Web Claude view 確認項目: engine.state へ書き込まないこと
    """
    cog = HOOK_STATE['cog']
    if cog is None:
        return
    current_global_step = HOOK_STATE['global_step']

    # === 引き金 7 種 event 検出 (delta) ===
    # cid_birth
    born_at = getattr(cog, 'born_at', {})
    current_cids = set(born_at.keys())
    new_births = current_cids - HOOK_STATE['last_cids']
    HOOK_STATE['last_cids'] = current_cids

    # === Task 223: alive 中に born_at を capture (reap で pop される前) ===
    for cid in current_cids:
        if cid not in HOOK_STATE['captured_born_at']:
            HOOK_STATE['captured_born_at'][cid] = born_at[cid]

    # cid_death
    host_lost_at = getattr(cog, 'host_lost_at', {})
    current_dead = set(c for c, v in host_lost_at.items() if v is not None)
    new_deaths = current_dead - HOOK_STATE['last_dead_cids']
    HOOK_STATE['last_dead_cids'] = current_dead

    # === Task 223: 死亡確定検出時に host_lost_at も capture ===
    for cid in current_dead:
        if cid not in HOOK_STATE['captured_host_lost_at']:
            HOOK_STATE['captured_host_lost_at'][cid] = host_lost_at[cid]

    # alpha_formation
    alpha_mgr = HOOK_STATE.get('alpha_mgr')
    new_alpha_cids = set()
    if alpha_mgr is not None:
        current_alphas = set(getattr(alpha_mgr, 'alphas', {}).keys())
        new_alpha_ids = current_alphas - HOOK_STATE['last_alpha_ids']
        for aid in new_alpha_ids:
            ai = alpha_mgr.alphas.get(aid)
            if ai is not None:
                members = getattr(ai, 'member_cids', set())
                new_alpha_cids.update(members)
        HOOK_STATE['last_alpha_ids'] = current_alphas

    # beta_formation
    beta_mgr = HOOK_STATE.get('beta_mgr')
    new_beta_cids = set()
    if beta_mgr is not None:
        current_betas = set(getattr(beta_mgr, 'betas', {}).keys())
        new_beta_ids = current_betas - HOOK_STATE['last_beta_ids']
        for bid in new_beta_ids:
            bi = beta_mgr.betas.get(bid)
            if bi is not None:
                members = getattr(bi, 'member_cids', set())
                new_beta_cids.update(members)
        HOOK_STATE['last_beta_ids'] = current_betas

    # pulse (cog.v10_pulse_count の delta)
    new_pulse_cids = set()
    current_pulse = getattr(cog, 'v10_pulse_count', {})
    if isinstance(current_pulse, dict):
        for cid, pc in current_pulse.items():
            prev = HOOK_STATE['last_pulse_counts'].get(cid, 0)
            if pc > prev:
                new_pulse_cids.add(cid)
        HOOK_STATE['last_pulse_counts'] = dict(current_pulse)

    # c_conversion (cog.C の delta、C が増えた cid)
    new_c_cids = set()
    current_C = getattr(cog, 'C', {})
    if isinstance(current_C, dict):
        for cid, cv in current_C.items():
            prev = HOOK_STATE['last_C_values'].get(cid, 0)
            if cv > prev:
                new_c_cids.add(cid)
        HOOK_STATE['last_C_values'] = dict(current_C)

    # ingestion (cog.death_pool の long-living 系の摂食、要詳細実装。
    #            まずは count を per_chunk で増加検出)
    new_ingestion_count = 0
    death_pool_log = getattr(cog, '_death_pool_log', [])
    if isinstance(death_pool_log, list):
        new_ingestion_count = max(0, len(death_pool_log) - HOOK_STATE['last_ingestion_count'])
        HOOK_STATE['last_ingestion_count'] = len(death_pool_log)

    # === 7 種で独立 running 統計 + alert 判定 (判定数値はレコード外) ===
    event_counts = {
        'cid_birth': len(new_births),
        'cid_death': len(new_deaths),
        'alpha_formation': len(new_alpha_cids),
        'beta_formation': len(new_beta_cids),
        'pulse': len(new_pulse_cids),
        'c_conversion': len(new_c_cids),
        'ingestion': new_ingestion_count,
    }

    alerted_triggers = set()
    for trig in TRIGGER_TYPES:
        cnt = event_counts.get(trig, 0)
        z = ewma_update(HOOK_STATE['running_stats'][trig], float(cnt))
        if abs(z) > Z_NOTICE:
            alerted_triggers.add(trig)

    # === alert 時に代表 CID 選んでレコード生成 ===
    trigger_to_cids = {
        'cid_birth': new_births,
        'cid_death': new_deaths,
        'alpha_formation': new_alpha_cids,
        'beta_formation': new_beta_cids,
        'pulse': new_pulse_cids,
        'c_conversion': new_c_cids,
        # ingestion はカウントのみ、代表 cid 不明 → 飛ばす (Taka 規律「すり替えない」)
    }
    for trig in alerted_triggers:
        cids = trigger_to_cids.get(trig, set())
        if not cids:
            continue  # 代表 cid が取れない場合はレコードしない
        # 代表 = 最小 cid (Step 1b と同じ「最初の event」相当)
        rep_cid = min(cids)
        record = build_record(cog, rep_cid, trig, current_global_step)
        HOOK_STATE['records'].append(record)
        HOOK_STATE['order'] += 1


def setup_monkey_patches():
    """v105 module を import + patch (cog/IntegrationManager 捕捉、realizer.step per-N-step hook)

    修正 (2026-06-07): tracking loop は per-step realizer.step を直接呼ぶため、
    step_window patch では maturation 中のみ hook されていた。
    realizer.step を patch して maturation と tracking の両方で per-10step hook を効かす。
    """
    from esde_v82_engine import V82Engine
    import v105_memory_readout as v105mr
    # 修正 (2026-06-07): v105 は独自の class SubjectLayer (line 443) を持つ。
    # v918 の SubjectLayer ではなく v105 のものを patch する。
    SubjectLayer = v105mr.SubjectLayer
    IntegrationManager = v105mr.IntegrationManager

    # === SubjectLayer.__init__ patch (cog 捕捉) ===
    _orig_subject_init = SubjectLayer.__init__
    def _captured_subject_init(self, *args, **kwargs):
        _orig_subject_init(self, *args, **kwargs)
        HOOK_STATE['cog'] = self
        print(f'  [hook] cog captured (SubjectLayer instance)')
    SubjectLayer.__init__ = _captured_subject_init

    # === IntegrationManager.__init__ patch (α/β 捕捉) ===
    _orig_im_init = IntegrationManager.__init__
    def _captured_im_init(self, *args, **kwargs):
        _orig_im_init(self, *args, **kwargs)
        HOOK_STATE['integration_mgr'] = self
        HOOK_STATE['alpha_mgr'] = getattr(self, 'alpha', None)
        HOOK_STATE['beta_mgr'] = getattr(self, 'beta', None)
        print(f'  [hook] IntegrationManager captured (alpha={HOOK_STATE["alpha_mgr"] is not None}, '
              f'beta={HOOK_STATE["beta_mgr"] is not None})')
    IntegrationManager.__init__ = _captured_im_init

    # === V82Engine.__init__ patch (engine + realizer.step を per-step hook 経路として捕捉) ===
    _orig_engine_init = V82Engine.__init__
    def _captured_engine_init(self, *args, **kwargs):
        _orig_engine_init(self, *args, **kwargs)
        HOOK_STATE['engine'] = self
        # realizer.step を instance-level で wrap (完全 read-only ラッパー)
        if hasattr(self, 'realizer') and self.realizer is not None:
            _orig_realizer_step = self.realizer.step
            _engine_ref = self
            def _hooked_realizer_step(state):
                _orig_realizer_step(state)  # 元の per-step physics を実行 (動学不変)
                HOOK_STATE['per_step_counter'] = HOOK_STATE.get('per_step_counter', 0) + 1
                if HOOK_STATE['per_step_counter'] % N_PER_CHUNK == 0:
                    HOOK_STATE['global_step'] += N_PER_CHUNK
                    HOOK_STATE['patch_chunk_count'] += 1
                    per_chunk_observe(_engine_ref)  # read-only 観察 (engine.state を読むだけ)
            self.realizer.step = _hooked_realizer_step
            print(f'  [hook] engine captured + realizer.step wrapped (per-{N_PER_CHUNK}step hook)')
    V82Engine.__init__ = _captured_engine_init

    return v105mr


def main():
    print('=== v1114 Step 2-A 生きた Center 観察基盤 (案 b-1) ===\n')
    print(f'  SEED={SEED}, MATURATION_WINDOWS={MATURATION_WINDOWS}, TRACKING_WINDOWS={TRACKING_WINDOWS}')
    print(f'  WINDOW_STEPS={WINDOW_STEPS}, N_PER_CHUNK={N_PER_CHUNK}')
    print(f'  v105_memory_readout.run() 直接呼び + monkey-patch')
    print(f'  Taka 規律: 観察のみ、書き戻しなし、§3 自己擦り込みは保留\n')

    # === monkey-patch setup ===
    v105mr = setup_monkey_patches()
    v105_run = v105mr.run

    # === v105 run() の出力 dir を /tmp に逃がす ===
    cwd_orig = Path.cwd()
    os.chdir(V105_OUT_DIR)
    print(f'  cwd: {V105_OUT_DIR} (v105 run() 出力先)\n')

    t_start = time.time()
    try:
        # v105 run() を呼ぶ (patch 経由で hook が動く)
        v105_run(
            seed=SEED,
            maturation_windows=MATURATION_WINDOWS,
            tracking_windows=TRACKING_WINDOWS,
            window_steps=WINDOW_STEPS,
            tag='step2a_seed0',
        )
    finally:
        os.chdir(cwd_orig)

    t_total = time.time() - t_start
    print(f'\n=== v105 run() 完了 (total {t_total:.1f}s) ===\n')

    # === 報告 (Taka 規律: 溜まったか + 多様か + unknown 率 + familiarity_sizes 取れたか) ===
    records = HOOK_STATE['records']
    print('=' * 60)
    print('Step 2-A 観察 (Taka 念押し: 溜まったか + 多様か、差は測らない)')
    print('=' * 60)
    print(f'\nレコード数: {len(records)}')
    print(f'  patch 経由 chunk 数: {HOOK_STATE["patch_chunk_count"]}')
    print(f'  patch 経由 remainder 数: {HOOK_STATE["patch_remainder_count"]}')
    print(f'  最終 global_step: {HOOK_STATE["global_step"]}')

    if len(records) == 0:
        print('\n→ レコード溜まらず (要 debug)')
        # debug: running_stats の最終状態をダンプ
        print('\n=== debug: running_stats 最終状態 ===')
        for trig, stat in HOOK_STATE['running_stats'].items():
            print(f'  {trig}: count={stat["count"]}, mean={stat["mean"]:.3f}, var={stat["var"]:.3f}')
        print(f'\n=== debug: last_cids 集合サイズ ===')
        print(f'  last_cids: {len(HOOK_STATE["last_cids"])}')
        print(f'  last_dead_cids: {len(HOOK_STATE["last_dead_cids"])}')
        print(f'  last_alpha_ids: {len(HOOK_STATE["last_alpha_ids"])}')
        print(f'  last_beta_ids: {len(HOOK_STATE["last_beta_ids"])}')
        print(f'  last_pulse_counts: {len(HOOK_STATE["last_pulse_counts"])} CIDs tracked')
        print(f'  last_C_values: {len(HOOK_STATE["last_C_values"])} CIDs tracked')
        (OUT_DIR / 'summary.json').write_text(json.dumps({
            'design': 'v1114_step2a_live_observer',
            'records_total': 0,
            'note': 'records_empty',
            'debug_running_stats': {trig: {'count': stat['count'], 'mean': stat['mean'], 'var': stat['var']}
                                    for trig, stat in HOOK_STATE['running_stats'].items()},
            'debug_last_sizes': {
                'last_cids': len(HOOK_STATE['last_cids']),
                'last_dead_cids': len(HOOK_STATE['last_dead_cids']),
                'last_alpha_ids': len(HOOK_STATE['last_alpha_ids']),
                'last_beta_ids': len(HOOK_STATE['last_beta_ids']),
            },
            'final_global_step': HOOK_STATE['global_step'],
            'patch_chunk_count': HOOK_STATE['patch_chunk_count'],
        }, indent=2, ensure_ascii=False))
        return

    # 引き金 7 種分布
    trigger_dist = Counter(r['trigger'] for r in records)
    print(f'\n引き金 (記号、7 種、独立監視) の分布:')
    for trig in TRIGGER_TYPES:
        cnt = trigger_dist.get(trig, 0)
        marker = ' ★' if trig in ('cid_birth', 'cid_death') else ''
        print(f'  {trig}: {cnt}{marker}')

    # n_core 分布
    n_core_dist = Counter(str(r['point']['n_core']) for r in records)
    print(f'\n点の n_core 分布:')
    for nc in sorted(n_core_dist.keys(), key=lambda x: (x == 'unknown', x)):
        cnt = n_core_dist[nc]
        marker = ''
        try:
            ncv = int(nc)
            if ncv == 2: marker = ' ← bulk'
            elif ncv >= 4: marker = ' ← hub'
        except ValueError:
            pass
        print(f'  n_core={nc}: {cnt}{marker}')

    # formation_relation / lifecycle_phase は Taka 判断 (2026-06-08) で落とした
    # (v105 hook で 100% 退化、取れないなら落とす規律遵守、Step 1b 既知バグとして保留)

    # familiarity_sizes 取得率
    fs_has = sum(1 for r in records if r['neighborhood']['familiarity_sizes'])
    fs_total_partners = sum(len(r['neighborhood']['familiarity_sizes']) for r in records)
    print(f'\nfamiliarity_sizes: {fs_has}/{len(records)} レコードで取得 ({fs_has/len(records)*100:.1f}%)')
    print(f'  全相手 n_core サンプル数: {fs_total_partners}')
    if fs_has > 0:
        all_sizes = []
        for r in records:
            all_sizes.extend(r['neighborhood']['familiarity_sizes'])
        size_dist = Counter(all_sizes)
        print(f'  相手 n_core 分布:')
        for sz, cnt in sorted(size_dist.items()):
            print(f'    n_core={sz}: {cnt}')

    # 引き金 × n_core 二次元
    print(f'\n引き金 × n_core 二次元:')
    cross = defaultdict(lambda: defaultdict(int))
    for r in records:
        cross[r['trigger']][str(r['point']['n_core'])] += 1
    n_cores_sorted = sorted({nc for ncs in cross.values() for nc in ncs},
                            key=lambda x: (x == 'unknown', x))
    header = '  trigger\\\\n_core ' + ' '.join(f'{nc:>5}' for nc in n_cores_sorted)
    print(header)
    for trig in TRIGGER_TYPES:
        row = f'  {trig:<18}' + ' '.join(f'{cross[trig].get(nc, 0):>5}' for nc in n_cores_sorted)
        print(row)

    # === ファイル出力 ===
    (OUT_DIR / 'attention_records.json').write_text(
        json.dumps(records, indent=2, ensure_ascii=False))
    summary = {
        'design': 'v1114_step2a_live_observer',
        'note': 'formation_relation/lifecycle_phase を落とした (Taka 判断 2026-06-08、v105 hook で 100% 退化、Step 1b 既知バグとして保留)',
        'seed': SEED,
        'maturation_windows': MATURATION_WINDOWS,
        'tracking_windows': TRACKING_WINDOWS,
        'window_steps': WINDOW_STEPS,
        'n_per_chunk': N_PER_CHUNK,
        'patch_chunk_count': HOOK_STATE['patch_chunk_count'],
        'patch_remainder_count': HOOK_STATE['patch_remainder_count'],
        'final_global_step': HOOK_STATE['global_step'],
        'records_total': len(records),
        'trigger_distribution': dict(trigger_dist),
        'n_core_distribution': {str(k): v for k, v in n_core_dist.items()},
        'familiarity_sizes_has_count': fs_has,
        'familiarity_sizes_total_partners': fs_total_partners,
        'v105_output_dir': str(V105_OUT_DIR),
    }
    (OUT_DIR / 'summary.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n保存: attention_records.json + summary.json')
    print(f'v105 run() output: {V105_OUT_DIR} (M1 検証用、per_subject_seed0.csv 等)')
    print(f'\n=== Step 2-A 完了 ===')


if __name__ == '__main__':
    main()
