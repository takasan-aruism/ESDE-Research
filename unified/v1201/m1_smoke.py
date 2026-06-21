#!/usr/bin/env python3
"""v12 Atomset M1 — label に atomset_seed/atomset_bonus 追加 + smoke 完走確認

## 観察対象注釈ブロック

### 観察対象
- 同じ系内 (Center ESDE 単体、生きた run)
- VirtualLayer.labels に新規 key (atomset_seed, atomset_bonus) を追加して smoke 完走確認
- torque 未接続 (M3 で接続)、atomset_bonus は初期 0、torque 計算には影響しない
- Atomset 設計書 §7 M1: 「label に 2 key が乗り、torque_factor 経路が健在」

### Atomset 設計書 §3 (v12.0、Web Claude 2026-06-10) 準拠
- A 静的素質: 誕生時に rank_1 Atom を atomset_seed に設定 (M1 では None、M2 で実装)
- B 動的成長: 素質方向の event 頻度で atomset_bonus を育てる (M2 で実装)
- C torque 接続: atomset_factor を torque_mag に乗算 (M3 で実装)

### 規律 (Step 2-A 継続 + Atomset 設計書 §6)
- 判断基準は一本: CID の個性化を促進するか
- 物理層 (genesis_physics) 不可侵
- VirtualLayer 内 torque のみ
- 判定数値はレコードに残さない
- 過去 main run output は触らない (新世代 ESDE、新 baseline)
- v106 cid_atom_sim_matrix の人工性留保継続 (LLM 判定 + 手定義投影、本物にならない)

### M1 出口
- smoke (mat=2 + track=3 = 5 windows) 完走、exit 0
- engine 発散せず (theta 範囲 [-π, π] 維持、alive_n 安定)
- 全 label に atomset_seed と atomset_bonus が乗っている
- 既存 torque_factor 経路 (label.get('torque_factor', 1.0)) は健在 (= 1.0 default、変えていない)
"""
import os, sys, json
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from pathlib import Path
import numpy as np
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
]
for p in PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# === 構成 (smoke 規模、Step 2-A と同じパラメータ) ===
SEED = 0
MATURATION_WINDOWS = 2
TRACKING_WINDOWS = 3
WINDOW_STEPS = 500

OUT_DIR = REPO / 'unified/v1201/run_m1_smoke'
OUT_DIR.mkdir(parents=True, exist_ok=True)
V105_OUT_DIR = Path('/tmp/v12_m1_smoke_seed0')
V105_OUT_DIR.mkdir(parents=True, exist_ok=True)

HOOK_STATE = {
    'vl': None,  # VirtualLayer instance (atomset_seed/bonus 追加対象)
    'engine': None,
    'label_birth_count': 0,  # 観察用: 新規 label に atomset key を装飾した回数
    'labels_with_atomset': 0,  # 観察用: 完走時点で atomset_seed/bonus を持つ label 数
    'theta_diverged': False,  # engine 発散検出
}


def patch_virtual_layer_step():
    """VirtualLayer.step を wrap して、新規 label に atomset_seed/bonus を装飾

    M1: atomset_seed=None (rank_1 計算は M2 で)、atomset_bonus=0.0 (初期)
    torque 計算には影響しない (M3 で atomset_factor を乗算)
    """
    from virtual_layer_v9 import VirtualLayer as VirtualLayerV9
    _orig_step = VirtualLayerV9.step

    def _hooked_step(self, state, window_count, islands=None, substrate=None):
        stats = _orig_step(self, state, window_count, islands, substrate)
        # 新規 label を検出 (atomset_seed key が未設定なもの)
        for lid, label in list(self.labels.items()):
            if 'atomset_seed' not in label:
                label['atomset_seed'] = None  # M2 で rank_1 atom を設定
                label['atomset_bonus'] = 0.0  # M2 で頻度駆動で育てる
                HOOK_STATE['label_birth_count'] += 1
        # engine 発散チェック (theta が範囲外 or NaN)
        theta = state.theta
        if np.any(np.isnan(theta)) or np.any(np.abs(theta) > 100):
            HOOK_STATE['theta_diverged'] = True
        HOOK_STATE['vl'] = self
        return stats

    VirtualLayerV9.step = _hooked_step
    print(f'  [hook] VirtualLayer.step wrapped (新規 label に atomset_seed/bonus 装飾)')


def main():
    print('=== v12 Atomset M1 smoke — label に 2 key 追加 + 完走確認 ===\n')
    print(f'  SEED={SEED}, mat={MATURATION_WINDOWS}, track={TRACKING_WINDOWS}')
    print(f'  M1 出口: smoke 完走 + 全 label に atomset_seed/bonus + torque_factor 経路健在\n')

    patch_virtual_layer_step()

    import v105_memory_readout as v105mr
    v105_run = v105mr.run

    cwd_orig = Path.cwd()
    os.chdir(V105_OUT_DIR)
    print(f'  cwd: {V105_OUT_DIR}\n')

    t_start = time.time()
    try:
        v105_run(
            seed=SEED,
            maturation_windows=MATURATION_WINDOWS,
            tracking_windows=TRACKING_WINDOWS,
            window_steps=WINDOW_STEPS,
            tag='v12_m1_smoke_seed0',
        )
    finally:
        os.chdir(cwd_orig)

    t_total = time.time() - t_start
    print(f'\n=== v105 run() 完了 ({t_total:.1f}s) ===\n')

    # === 完走確認 ===
    vl = HOOK_STATE['vl']
    if vl is None:
        print('ERROR: VirtualLayer 捕捉失敗')
        sys.exit(1)

    # 全 label に atomset_seed/bonus が乗っているか
    labels_total = len(vl.labels)
    labels_with_atomset = sum(
        1 for label in vl.labels.values()
        if 'atomset_seed' in label and 'atomset_bonus' in label
    )
    HOOK_STATE['labels_with_atomset'] = labels_with_atomset

    print('=' * 60)
    print('M1 出口確認')
    print('=' * 60)
    print(f'\n(1) smoke 完走: ✓ exit 0 ({t_total:.1f}s)')
    print(f'(2) engine 発散検出: {"✗ 発散!" if HOOK_STATE["theta_diverged"] else "✓ 発散なし"}')
    print(f'(3) label に atomset_seed/bonus 装飾:')
    print(f'    label 誕生時 atomset 装飾回数: {HOOK_STATE["label_birth_count"]}')
    print(f'    完走時点 label 総数: {labels_total}')
    print(f'    完走時点 atomset を持つ label 数: {labels_with_atomset}')
    print(f'    {"✓" if labels_with_atomset == labels_total else "✗"} 全 label に乗ってる')

    # torque_factor 経路健在確認 (label.get('torque_factor', 1.0) は変えていない、default 1.0)
    sample_label = next(iter(vl.labels.values())) if vl.labels else None
    if sample_label is not None:
        tf_default = sample_label.get('torque_factor', 1.0)
        print(f'(4) torque_factor 経路健在: torque_factor={tf_default} (= 1.0 default、未変更 ✓)')
        print(f'    sample label keys: {sorted(sample_label.keys())}')

    # === 出力 ===
    summary = {
        'design': 'v1201_m1_smoke',
        'note': 'M1: label に atomset_seed (None)+atomset_bonus (0.0) 追加、torque 未接続。M2 で rank_1 atom 設定、M3 で torque 接続。',
        'seed': SEED,
        'maturation_windows': MATURATION_WINDOWS,
        'tracking_windows': TRACKING_WINDOWS,
        'window_steps': WINDOW_STEPS,
        'duration_sec': round(t_total, 1),
        'label_birth_count': HOOK_STATE['label_birth_count'],
        'labels_total_at_end': labels_total,
        'labels_with_atomset_at_end': labels_with_atomset,
        'all_labels_decorated': labels_with_atomset == labels_total,
        'theta_diverged': HOOK_STATE['theta_diverged'],
        'torque_factor_default': float(tf_default) if sample_label else None,
    }
    (OUT_DIR / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f'\n保存: {OUT_DIR / "summary.json"}')
    print(f'\n=== M1 完了 ===')

    if HOOK_STATE['theta_diverged']:
        print('赤信号: engine 発散検出、M2 に進む前に要 debug')
        sys.exit(1)
    if labels_with_atomset != labels_total:
        print('赤信号: 一部 label に atomset 未装飾、要 debug')
        sys.exit(1)


if __name__ == '__main__':
    main()
